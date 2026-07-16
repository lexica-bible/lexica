#!/usr/bin/env python3
"""
import_tipnr.py — Import STEPBible TIPNR proper noun data into bible.db

Phase 1: Create tipnr lookup table, populate from TIPNR file
Phase 2: Match words.strongs_base='*' against tipnr names
         → update strongs_base to real H/G number, set is_pn=1
Phase 3: Mark remaining unmatched * words as is_pn=1 (metaV still works by name)

Usage:
  python3 scripts/import_tipnr.py bible.db --dry-run   # preview matches
  python3 scripts/import_tipnr.py bible.db              # apply changes
"""

import os
import re
import sys
import sqlite3
import urllib.request
from collections import defaultdict

DB       = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "bible.db"
DRY_RUN  = "--dry-run" in sys.argv

# Session 5 pin: default to the vendored, hash-pinned copy (cert_manifest.json).
# The live download stays only behind --download-tipnr, for drift checks.
TIPNR_PINNED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "tipnr", "TIPNR.txt")

# What a harvested alternate spelling must look like (blocks urls/refs/junk).
_NAME_SHAPE = re.compile(r"[A-Za-z][A-Za-z'\- ]*")

try:
    # Hand-checked KJV/LXX variant -> canonical roster key (2026-07-16 batch; every
    # entry's verdict + reason in docs/tickets/alias_decisions.txt). Consulted at
    # ladder step 7; the inline ALIASES map wins on any overlap.
    from tipnr_alias_variants import VARIANT_ALIASES
except ImportError:
    VARIANT_ALIASES = {}
DOWNLOAD_TIPNR = "--download-tipnr" in sys.argv

TIPNR_URL = (
    "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/"
    "Proper%20Nouns/TIPNR%20-%20Translators%20Individualised%20Proper%20Names"
    "%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt"
)

NT_BOOKS = {
    "Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal",
    "Eph","Php","Col","1Th","2Th","1Ti","2Ti","Tit","Phm",
    "Heb","Jas","1Pe","2Pe","1Jo","2Jo","3Jo","Jud","Rev",
}

def norm_strongs(s):
    """H0175A -> H175, G0002 -> G2. Returns None if not parseable."""
    if not s:
        return None
    m = re.match(r"^([GH])0*(\d+)[A-Za-z]?$", s.strip())
    if m:
        return f"{m.group(1)}{int(m.group(2))}"
    return None

def extract_strongs_from_field(field):
    """Extract eStrong from 'dStrong«eStrong=Hebrew' format."""
    if "«" not in field:
        return None
    after = field.split("«", 1)[1]
    estrong = after.split("=")[0].strip()
    return norm_strongs(estrong)

def parse_tipnr(lines, _audit=None):
    """
    Returns:
      lookup    : {lower_name -> {"h": str|None, "g": str|None, "type": str}}
      tipnr_rows: [(strongs, primary_name, entity_type, entity_types), ...]
                  entity_type  = single primary type (person>place>other) — legacy
                  entity_types = full comma-joined SET (e.g. 'person,place'), so a
                                 strongs shared by a person AND a place keeps BOTH
                                 (the PK collision fix — backlog #5).
    """
    lookup = {}   # lower(name) -> entry dict
    agg    = {}   # strongs -> {"name": str, "types": set()}  (one entry per strongs)
    # EVERY sub-record spelling (alternate names AND per-version display forms) is
    # QUEUED here, never saved directly: TIPNR lists other entities' names as
    # alternates ("Jesus" under Barabbas via "Jesus Barabbas") and the file is
    # alphabetical, so a first-writer save let an earlier entity STEAL a later
    # entity's key (2026-07-16: 79 hijacked names — jesus→G912, judah→H1938,
    # simon→G4074…). Queued keys resolve AFTER every record is read: a main-record
    # name always wins, and a spelling claimed by entities with different numbers
    # is dropped (wrong number > missing number).
    _disp_pending = {}   # queued spelling -> set of (h, g) owners (ambiguity check)
    _disp_vals    = {}   # queued spelling -> first owner's type

    section   = "other"   # current $=== section
    mixed_hdr = False     # F1: current block header names BOTH person AND place
    cur       = None      # current main record

    records = []  # finished main records, in file order (phase A resolves from these)

    def save(cur):
        if not cur:
            return
        records.append(cur)
        for s in filter(None, [cur["h"], cur["g"]]):
            a = agg.setdefault(s, {"name": cur["name"], "types": set()})
            a["types"].add(cur["type"])

    for line in lines:
        # Section delimiter
        if line.startswith("$=========="):
            save(cur); cur = None
            low = line.lower()
            has_p, has_pl = "person" in low, "place" in low
            mixed_hdr = has_p and has_pl          # PERSON+PLACE header: type MUST come from the row
            section = "person" if has_p else "place" if has_pl else "other"
            continue

        if not line.strip():
            continue

        # Skip pure header / comment lines. NOTE: en-dash lines are NOT comments —
        # they are the sub-records (alternate spellings, per-version forms, gentilic
        # Group rows). Skipping them here silently discarded 10,127 of TIPNR's
        # 10,223 sub-record lines since the import was written (found 2026-07-16 —
        # the roster-gap root cause; 'Elias' itself was missing and only survived
        # via the hand ALIASES map).
        stripped = line.lstrip()
        if stripped[0] in ("=", "‖", "#", "*") or stripped.startswith("UnifiedName"):
            continue

        is_sub = line[0] in (" ", "\t") or line.startswith("–")
        parts  = line.split("\t")

        if not is_sub:
            # ── Main record ──────────────────────────────────────────
            save(cur); cur = None
            f0 = parts[0].strip()
            if "@" not in f0:
                continue
            name = f0.split("@")[0].strip()
            if not name:
                continue

            # uStrong comes after the last "=" in field 0
            primary = norm_strongs(f0.rsplit("=", 1)[-1]) if "=" in f0 else None

            # F1 (mirrors entity_resolution.parse_tipnr lines 315-326): the entity's OWN
            # row type (col 8) beats the block header. A PERSON+PLACE header names both, so
            # header-first typed every place under it as 'person' (the twin bug). Recognized
            # set is IDENTICAL to entity_resolution's: {Place, Male, Female}. Fall back to the
            # header ONLY for a single-type block; an unrecognized type inside a mixed block is
            # unresolvable -> STOP the build (same loud fail entity_resolution raises).
            col8 = parts[8].strip() if len(parts) > 8 else ""
            if col8 == "Place":
                row_section = "place"
            elif col8 in ("Male", "Female"):
                row_section = "person"
            elif mixed_hdr:
                raise ValueError(
                    "import_tipnr.parse_tipnr: entity %r under a PERSON+PLACE header has "
                    "unrecognized type %r -- cannot resolve person/place. Fix the TIPNR "
                    "source or extend the type map before building." % (name, col8))
            else:
                row_section = section
            if _audit is not None and row_section != section:   # audit hook (dry-run only)
                _audit.append((name, section, row_section, mixed_hdr, col8))
            cur = {
                "name":  name,
                "names": {name},
                "type":  row_section,
                "h":     primary if primary and primary[0] == "H" else None,
                "g":     primary if primary and primary[0] == "G" else None,
            }

            # Also check the dStrong«eStrong column in main record (index 11)
            for col in parts[9:14]:
                s = extract_strongs_from_field(col.strip())
                if s:
                    if s[0] == "H" and not cur["h"]:
                        cur["h"] = s
                    elif s[0] == "G" and not cur["g"]:
                        cur["g"] = s
            # Snapshot the MAIN-LINE numbers before sub-records enrich h/g: phase A
            # claims duplicate main-name keys with these first, so 'judah' keeps
            # resolving to the record it always did under the old loader.
            cur["h0"], cur["g0"] = cur["h"], cur["g"]

        else:
            # ── Sub-record ───────────────────────────────────────────
            if not cur or len(parts) < 3:
                continue

            # Real sub-records start "– <significance>\t..." (en-dash, no leading
            # tab), so the significance is in COLUMN 0 and every data column sits
            # one LEFT of what the old whitespace-indented map assumed. The
            # whitespace form is kept for the handful of legacy lines.
            if line.startswith("–"):
                significance = parts[0].lstrip("–").strip()
                base = 0
            else:
                significance = parts[1].strip() if len(parts) > 1 else ""
                base = 1
            if significance.lower().startswith("total"):
                continue

            # Grab the sub-record's OWN strongs (the « column). Group rows
            # (gentilics) carry their own number — 'Christian' is G5546, not the
            # parent Jesus entry's G2424 — so remember it for the display forms.
            row_s = None
            for col in parts[base + 1: base + 4]:
                s = extract_strongs_from_field(col.strip())
                if s:
                    row_s = s
                    if s[0] == "H" and not cur["h"]:
                        cur["h"] = s
                    elif s[0] == "G" and not cur["g"]:
                        cur["g"] = s
                    break

            # Collect alternate name spellings for better matching.
            # "Greek" captures LXX forms of OT names (e.g. Elias for Elijah)
            # which the ABP uses throughout since it's LXX-based; "Group" rows
            # are gentilics (Christian, Tyrians) with their own numbers.
            if significance in ("Named", "Spelled", "Spelled combined",
                                 "Name combined", "Aramaic", "Greek",
                                 "(same form as previous)", "Group",
                                 "(same ref[s] with Variant)", "LXX addition"):
                # The row's own number (Group rows: Christian=G5546) wins over the
                # entity's; both go into the owner pair the ambiguity check keys on.
                hg = (row_s if row_s and row_s[0] == "H" else cur["h"],
                      row_s if row_s and row_s[0] == "G" else cur["g"])

                def _queue(spelling):
                    k = spelling.lower()
                    _disp_pending.setdefault(k, set()).add(hg)
                    _disp_vals.setdefault(k, {"type": cur["type"]})

                # Alternate-name spelling ("Elias" under Elijah) — QUEUED, never a
                # direct save (see the queue comment up top: direct first-writer
                # saves let Barabbas steal 'jesus').
                unique = parts[base + 1].strip() if len(parts) > base + 1 else ""
                alt = unique.split("|")[0].split("@")[0].strip()
                if alt and alt != cur["name"] and _NAME_SHAPE.fullmatch(alt):
                    _queue(alt)
                # Per-version display forms ("Ashkenaz =ESV,NIV; Ashchenaz =KJV"):
                # TIPNR's own attested spellings, incl. the KJV forms ABP-adjacent
                # English uses. Same queue, same ambiguity rule.
                disp = parts[base + 3].strip() if len(parts) > base + 3 else ""
                if disp and not disp.startswith("http") and "«" not in disp:
                    for piece in disp.split(";"):
                        a2 = piece.split("=")[0].strip()
                        if (a2 and a2 != cur["name"] and len(a2) > 1
                                and _NAME_SHAPE.fullmatch(a2)):
                            _queue(a2)

    save(cur)

    # Phase A — main-record names, two passes over the finished records.
    # Pass 1 claims each key with the record's own MAIN-LINE numbers — byte-
    # compatible with the old loader, so duplicate main names ('Judah' ×n) keep
    # resolving to the record they always did. Pass 2 fills still-empty slots with
    # the sub-record-enriched numbers — the entities-gain-numbers win of the loader
    # fix, without letting an earlier record's sub-rows steal a later record's key.
    for rec in records:
        for nm in rec["names"]:
            key = nm.lower()
            if key not in lookup:
                lookup[key] = {"h": None, "g": None, "type": rec["type"]}
            e = lookup[key]
            if rec["h0"] and not e["h"]:
                e["h"] = rec["h0"]
            if rec["g0"] and not e["g"]:
                e["g"] = rec["g0"]
    for rec in records:
        for nm in rec["names"]:
            e = lookup[nm.lower()]
            if rec["h"] and not e["h"]:
                e["h"] = rec["h"]
            if rec["g"] and not e["g"]:
                e["g"] = rec["g"]

    # Resolve the queued sub-record spellings: a MAIN-record name always wins (the
    # key is skipped — zero regression to existing resolution), a spelling whose
    # owners carry different numbers is DROPPED (wrong number > missing number),
    # and only a single-owner spelling is added. Owner pairs with no number at all
    # carry no claim and are ignored. The dropped list is exposed for the audit
    # record (docs/tickets/alias_ambiguous_dropped.txt).
    dropped = []
    for k in sorted(_disp_pending):
        if k in lookup:
            continue
        owners = {p for p in _disp_pending[k] if p != (None, None)}
        if not owners:
            continue
        if len(owners) > 1:
            dropped.append((k, sorted(x for pair in owners for x in pair if x)))
            continue
        h, g = next(iter(owners))
        lookup[k] = {"h": h, "g": g, "type": _disp_vals[k]["type"]}
    parse_tipnr.dropped_ambiguous = dropped

    def _primary(types):
        for t in ("person", "place", "other"):
            if t in types:
                return t
        return "other"

    tipnr_rows = [
        (s, a["name"], _primary(a["types"]), ",".join(sorted(a["types"])))
        for s, a in agg.items()
    ]
    return lookup, tipnr_rows


def main():
    print(f"{'[DRY RUN] ' if DRY_RUN else ''}import_tipnr.py → {DB}\n")

    # ── Load TIPNR (pinned copy by default) ──────────────────────────
    if not DOWNLOAD_TIPNR and os.path.isfile(TIPNR_PINNED):
        print(f"TIPNR: pinned copy {TIPNR_PINNED}")
        lines = open(TIPNR_PINNED, encoding="utf-8-sig").read().splitlines()
    else:
        print("Downloading TIPNR (LIVE upstream — unpinned; drift checks only)...")
        with urllib.request.urlopen(TIPNR_URL) as r:
            lines = r.read().decode("utf-8-sig").splitlines()
    print(f"  {len(lines)} lines\n")

    # ── Parse ─────────────────────────────────────────────────────────
    print("Parsing...")
    lookup, tipnr_rows = parse_tipnr(lines)
    print(f"  {len(lookup):,} name entries (incl. alternates)")
    print(f"  {len(tipnr_rows):,} strongs entries for tipnr table")
    collisions = sum(1 for r in tipnr_rows if "," in (r[3] or ""))
    print(f"  {collisions:,} strongs are MULTI-type (e.g. person+place) — both now preserved\n")

    # Spot-check key names + known problematic ones
    checks = ["Jesus","Israel","Edom","Abraham","Jerusalem","Moses",
               "Elijah","David","Mary","Judah","Ephraim","Aaron",
               "Zion","Abram","Levi","Pharisee","Canaan","Heth",
               "Assyria","Chaldea","Hivite","Amorite","Moab","Ammon"]
    print("Spot checks:")
    for nm in checks:
        print(f"  {nm:12} → {lookup.get(nm.lower())}")
    print()

    # ── DB work ───────────────────────────────────────────────────────
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    # Schema: add is_pn column
    if not DRY_RUN:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(words)").fetchall()}
        if "is_pn" not in cols:
            print("Adding is_pn column to words...")
            conn.execute("ALTER TABLE words ADD COLUMN is_pn INTEGER DEFAULT 0")

        print("Creating tipnr table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tipnr (
                strongs      TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                entity_type  TEXT,
                entity_types TEXT
            )
        """)
        # A pre-existing tipnr table won't get entity_types from CREATE IF NOT
        # EXISTS — add it (mirrors the idempotent _migrate_db ALTER). Backlog #5:
        # entity_types holds the full type SET so a strongs shared by a person AND
        # a place (e.g. Adam H121) keeps BOTH; entity_type stays one primary token.
        tcols = {r[1] for r in conn.execute("PRAGMA table_info(tipnr)").fetchall()}
        if "entity_types" not in tcols:
            conn.execute("ALTER TABLE tipnr ADD COLUMN entity_types TEXT")
        conn.execute("DELETE FROM tipnr")
        conn.executemany(
            "INSERT OR REPLACE INTO tipnr(strongs,name,entity_type,entity_types) VALUES(?,?,?,?)",
            tipnr_rows,
        )
        conn.commit()
        print(f"  Inserted {len(tipnr_rows):,} rows\n")

    # ── Match words ───────────────────────────────────────────────────
    print("Matching words.strongs_base='*'...")
    word_rows = conn.execute("""
        SELECT w.rowid AS word_id, w.english, v.book
        FROM words w
        JOIN verses v ON v.id = w.verse_id
        WHERE w.strongs_base = '*'
          AND w.english IS NOT NULL AND w.english != ''
    """).fetchall()
    print(f"  {len(word_rows):,} words to match\n")

    matched        = []   # (new_strongs, rowid)
    unmatched_cnt  = defaultdict(int)

    # Direct Strong's for entries missing from parsed TIPNR (confirmed numbers)
    DIRECT = {
        "zion":          "H6726",  "abram":        "H87",
        "sarai":         "H8297",  "hivite":       "H2340",
        "hivites":       "H2340",  "amorite":      "H567",
        "amorites":      "H567",   "jebusite":     "H2983",
        "jebusites":     "H2983",  "perizzite":    "H6522",
        "perizzites":    "H6522",  "girgashite":   "H1622",
        "girgashites":   "H1622",  "hermon":       "H2768",
        "shushan":       "H7800",  "necho":        "H5224",
        "neco":          "H5224",  "meshach":      "H4336",
        "shadrach":      "H7714",  "abednego":     "H5665",
        "syrian":        "H761",   "syrians":      "H761",
        # Additional missing entries
        "horeb":         "H2722",  "iscariot":     "G2469",
        "ishbosheth":    "H378",   "arphaxad":     "H775",
        "caesar":        "G2541",  "magdalene":    "G3094",
        "hinnom":        "H2011",  "tishbite":     "H8664",
        "bethhoron":     "H1032",  "edomite":      "H130",
        "edomites":      "H130",   "nethinim":     "H5411",
        "ezion":         "H6100",  "helkiah":      "H2518",
        "hilkiah":       "H2518",  "jabesh":       "H3003",
        "jabish":        "H3003",   "hor":          "H2023",
        "aholiab":       "H171",    "nazarene":     "G3480",
        "hormah":        "H2767",   "jaalam":       "H3281",
        "josedech":      "H3087",   "jehozadak":    "H3087",
        "hadarezer":     "H1928",   "pashur":       "H6583",
        "netophah":      "H5199",   "jerubbaal":    "H3378",
        "cana":          "G2580",   "barnea":       "H1251",
        "jeconiah":      "H3204",   "jechoniah":    "H3204",
        "anakim":        "H6062",   "anak":         "H6062",
        "shethar":       "H8370",   "melchisedek":  "H4442",
        "hodijah":       "H1941",   "aholibamah":   "H173",
        "bama":          "H1117",   "hagarite":     "H1905",
        "hagarites":    "H1905",   "rabbah":       "H7237",
        "cherethite":   "H3746",   "cherethites":  "H3746",
        "pelethite":    "H6432",   "pelethites":   "H6432",
        "pelonite":     "H6397",   "hushathite":   "H2364",
        "kenite":       "H7017",   "kenites":      "H7017",
        "shilonite":    "H8024",   "beerothite":   "H881",
        "abijam":       "H38",     "ivah":         "H5755",
        "ziglag":       "H6860",
        # ── Recurring unmatched batch (2026-06-03), verified H/G ──────────
        "adonai":        "H136",   # divine title (Adonai)
        # LXX/Greek-OT place spellings
        "sor":           "H6865",  # Tyre (LXX Σορ)
        "gai":           "H5857",  # Ai (LXX Γαι)
        "sephela":       "H8219",  # Shephelah
        "negev":         "H5045",
        "gerizim":       "H1630",
        "tanis":         "H6814",  # Zoan
        "artaxerxes":    "H783",   "artasastha":  "H783",
        # Gentilics (Hebrew)
        "gergesite":     "H1622",  "gergesites":  "H1622",  # Girgashite
        "gibeonite":     "H1393",  "gibeonites":  "H1393",
        "hararite":      "H2043",  "temanite":    "H8489",
        "ammonitess":    "H5985",  "moabitess":   "H4125",
        "canaanitess":   "H3669",  "jezreelitess":"H3159",
        "ishmaelites":   "H3459",  "ziphites":    "H2130",
        "zarhites":      "H2227",  "hezronites":  "H2697",
        "arvadite":      "H721",   "sinite":      "H5513",
        "zemarite":      "H6786",  "horite":      "H2752",
        "buzite":        "H940",   "antothite":   "H6069",
        "archite":       "H757",   "adullamite":  "H5726",
        "ahohite":       "H266",   "harodite":    "H2733",
        "pirathonite":   "H6553",  "ithrite":     "H3505",
        "shuhite":       "H7747",  "shunammite":  "H7767",
        "zebulunite":    "H2075",  "horonite":    "H2772",
        "geshurites":    "H1651",  "chittim":     "H3794",  # Kittim
        # Variant name spellings (Hebrew)
        "aholah":        "H170",   "aholibah":    "H172",
        "astaroth":      "H6252",  "milcom":      "H4445",
        "eloth":         "H359",   "ephratah":    "H672",
        "ephrath":       "H672",   "eshbaal":     "H792",
        "meribbaal":     "H4807",  "adonizedec":  "H139",
        "adoniram":      "H141",   "hanameel":    "H2601",
        "jehonadab":     "H3082",  "jehoshabeath":"H3090",
        "belteshazzar":  "H1095",  "shetharboznai":"H8370",
        "malchishua":    "H4444",  "shophach":    "H7780",
        "shechaniah":    "H7935",  "sibbechai":   "H5444",
        "azareel":       "H5832",  "elipheleh":   "H466",
        "elzaphan":      "H469",   "ajah":        "H345",
        "ajalon":        "H357",   "almon":       "H5960",
        "asahiah":       "H6222",  "hashub":      "H2815",
        "hatach":        "H2047",  "phichol":     "H6369",
        "phurah":        "H6513",  "tatnai":      "H8674",
        "tou":           "H8583",  "zechri":      "H2147",
        "zithri":        "H5644",  "maacha":      "H4601",
        "bethmaacah":    "H1038",  "kirjatharba": "H7153",
        "kirjathjearim": "H7157",  "kirjathaim":  "H7156",
        "libna":         "H3841",  "jebus":       "H2982",
        "remmon":        "H7417",  "bashemath":   "H1315",
        "timnath":       "H8553",  "shochoh":     "H7755",
        "achor":         "H5911",  "engedi":      "H5872",
        "tophet":        "H8612",  "harosheth":   "H2800",
        "jabok":         "H2999",  "jiphthahel":  "H3317",
        "abarim":        "H5682",  "zared":       "H2218",
        "perazim":       "H6559",  "raphaim":     "H7497",
        "pochereth":     "H6380",  "dalaiah":     "H1806",
        "hananeel":      "H2606",  "araunah":     "H728",
        "abishalom":     "H53",    "ocran":       "H5918",
        "michah":        "H4318",  "micha":       "H4318",
        "rogel":         "H5883",  "ramathaim":   "H7436",
        "coniah":        "H3659",  "salem":       "H8004",
        # NT names / places (Greek)
        "cretan":        "G2912",  "cretans":     "G2912",
        "crete":         "G2914",  "galilean":    "G1057",
        "galileans":     "G1057",  "samaritan":   "G4541",
        "samaritans":    "G4541",  "hellenists":  "G1675",
        "cyrenian":      "G2956",  "cyrenians":   "G2956",
        "macedonian":    "G3110",  "lydda":       "G3069",
        "sardis":        "G4554",  "sarepta":     "G4558",
        "cenchrea":      "G2747",  "arimathea":   "G707",
        "tiberias":      "G5085",  "beelzebul":   "G954",
        "beelzeboul":    "G954",   "gehenna":     "G1067",
        "didymus":       "G1322",  "dorcas":      "G1393",
        "hymeneus":      "G5211",  "pontius":     "G4194",
        "bosor":         "G1007",
        # Stragglers (2026-06-03 follow-up)
        "gaber":         "H1398",  # Geber
        "ishuah":        "H3438",  # Ishvah
        "baalpeor":      "H1187",  # Baal-peor
        "en gedi":       "H5872",  # En-gedi (spaced form)
    }

    # Gentilics and common variants not stored under their ABP form in TIPNR
    ALIASES = {
        # Demonyms → root place/person in TIPNR
        "levite":      "levi",       "levites":     "levi",
        "jew":         "judah",      "jews":        "judah",
        "egyptian":    "egypt",      "egyptians":   "egypt",
        "assyrian":    "assyria",    "assyrians":   "assyria",
        "chaldean":    "chaldea",    "chaldeans":   "chaldea",
        "canaanite":   "canaan",     "canaanites":  "canaan",
        "hittite":     "heth",       "hittites":    "heth",
        "hivite":      "hivite",     "hivites":     "hivite",
        "amorite":     "amorite",    "amorites":    "amorite",
        "moabite":     "moab",       "moabites":    "moab",
        "ammonite":    "ammon",      "ammonites":   "ammon",
        "philistine":  "philistia",  "philistines": "philistia",
        "israelite":   "israel",     "israelites":  "israel",
        "pharisee":      "pharisee",   "pharisees":     "pharisee",
        "sadducee":      "sadducee",   "sadducees":     "sadducee",
        "persian":       "persia",     "persians":      "persia",
        "gileadite":     "gilead",     "gileadites":    "gilead",
        "elamite":       "elam",       "elamites":      "elam",
        "cushite":       "cush",       "cushites":      "cush",
        "midianite":     "midian",     "midianites":    "midian",
        "edomite":       "edom",       "edomites":      "edom",
        "baalim":        "baal",
        # Spelling variants (ABP/LXX vs ESV/Hebrew forms)
        "michaiah":      "micaiah",    "nabuzaradan":   "nebuzaradan",
        "nabuzar-adan":  "nebuzaradan","jabish":        "jabesh",
        "helkiah":       "hilkiah",    "pharez":        "perez",
        "zarah":         "zerah",      "bezaleel":      "bezalel",
        "urijah":        "uriah",      "neriah":        "neriah",
        "maachah":       "maacah",     "josedech":      "jehozadak",
        "tizrah":        "tirzah",     "baldad":        "bildad",
        "nethaneel":     "nethanel",   "netophathite":  "netophah",
        "netophathites": "netophah",   "hadarezer":     "hadadezer",
        "nazarene":      "nazareth",   "elias":         "elijah",
        "elisaios":      "elisha",     "esaias":        "isaiah",
        "jeremias":      "jeremiah",   "ezechias":      "hezekiah",
        "ozias":         "uzziah",     "josias":        "josiah",
        "jechonias":     "jehoiachin", "joatham":       "jotham",
        "ethiopia":      "cush",       "ethiopian":     "cush",
        "ethiopians":    "cush",       "sidonian":      "sidon",
        "sidonians":     "sidon",      "mede":          "media",
        "medes":         "media",      "median":        "media",
        "gittite":       "gath",       "gittites":      "gath",
        "carmelite":     "carmel",     "carmelites":    "carmel",
        "maachathite":   "maacah",     "maachathites":  "maacah",
        "kirjathjearim": "kiriath-jearim",
        "melchisedek":   "melchizedek", "abijam":     "abijah",
        "gadite":        "gad",         "gadites":    "gad",
        "jezreelite":    "jezreel",     "jezreelites":"jezreel",
        "ashdodite":     "ashdod",      "ashdodites": "ashdod",
        "arabian":       "arabia",      "arabians":   "arabia",
        "ziglag":        "ziklag",      "shilonite":  "shiloh",
        # ── Recurring batch (2026-06-03): NT/LXX name variants → canonical ──
        "juda":          "judah",       "esrom":      "hezron",
        "zara":          "zerah",       "enos":       "enosh",
        "sophar":        "zophar",      "rama":       "ramah",
        "aminadab":      "amminadab",   "naasson":    "nahshon",
        "salathiel":     "shealtiel",   "babylonians":"babylon",
        "mizraim":       "egypt",       "maachah":    "maacah",
        "nabuzar-ardan": "nebuzaradan", "nabuzarardan":"nebuzaradan",
        "zachariah":     "zechariah",   "zacharias":  "zechariah",
    }

    def find_entry(english):
        """Try progressively looser matches against the TIPNR lookup."""
        # Normalise once: strip trailing punct + dashes, strip leading particles
        def _strip_trail(s):
            return re.sub(r"[\s,.:;!?'\"–\-]+$", "", s).strip()

        def _strip_lead(s):
            for prefix in ("land of the ", "land of ", "of the ", "of ", "to ",
                           "in the ", "in ", "for ", "both ", "and ", "this ",
                           "was ", "with ", "the ", "an ", "a ", "O ", "o "):
                if s.lower().startswith(prefix):
                    return s[len(prefix):]
            return s

        def _no_hyphen(s):
            return s.replace("-", "")

        # 1. Exact
        e = lookup.get(english.lower());
        if e: return e
        # 2. Strip trailing punctuation/dashes
        clean = _strip_trail(english)
        e = lookup.get(clean.lower())
        if e: return e
        # 3. Strip leading particle from cleaned
        bare = _strip_lead(clean)
        if bare != clean:
            e = lookup.get(bare.lower())
            if e: return e
        # 4. Remove hyphens: 'Beth-el' -> 'Bethel'
        e = lookup.get(_no_hyphen(bare).lower())
        if e: return e
        # 5. Strip particle from original then clean trailing
        bare2 = _strip_trail(_strip_lead(english))
        e = lookup.get(bare2.lower())
        if e: return e
        # 6. Try singular (strip trailing 's'): 'Pharisees' -> 'Pharisee'
        for candidate in (bare, bare2, clean):
            if candidate.endswith("s"):
                e = lookup.get(candidate[:-1].lower())
                if e: return e
        # 7. Manual alias table for gentilics and name variants, then the
        #    hand-checked variant batch (ALIASES wins on overlap)
        for candidate in (bare.lower(), bare2.lower(), clean.lower(), english.lower()):
            mapped = ALIASES.get(candidate) or VARIANT_ALIASES.get(candidate)
            if mapped:
                e = lookup.get(mapped)
                if e: return e
        # 8. Direct Strong's map for entries missing from parsed TIPNR
        # Also try no-hyphen variant for compound names like 'Abed-nego', 'Beth-horon'
        candidates_direct = {bare.lower(), bare2.lower(), clean.lower(), english.lower(),
                              _no_hyphen(bare).lower(), _no_hyphen(clean).lower()}
        for candidate in candidates_direct:
            s = DIRECT.get(candidate)
            if s:
                return {"h": s if s[0] == "H" else None,
                        "g": s if s[0] == "G" else None,
                        "type": "place"}
        return None

    # ── Validate DIRECT Strong's exist in bdb (H) / lexicon (G) — catch typos ──
    missing = []
    for nm, s in sorted(DIRECT.items()):
        if s.startswith("H"):
            ok = conn.execute("SELECT 1 FROM bdb WHERE strongs_id=?", (s,)).fetchone()
        else:
            ok = conn.execute("SELECT 1 FROM lexicon WHERE strongs=?", (s[1:],)).fetchone()
        if not ok:
            missing.append((nm, s))
    if missing:
        print(f"⚠️  {len(missing)} DIRECT entries have NO bdb/lexicon row (VERIFY before applying):")
        for nm, s in missing:
            print(f"     {nm} -> {s}")
        print()
    else:
        print(f"DIRECT validation: all {len(DIRECT)} entries resolve in bdb/lexicon ✓\n")

    for row in word_rows:
        english = row["english"].strip()
        book    = row["book"]
        entry   = find_entry(english)

        if not entry:
            unmatched_cnt[english] += 1
            continue

        is_nt   = book in NT_BOOKS
        strongs = entry["g"] if is_nt else entry["h"]

        # Fallback: if preferred side missing, use whatever exists
        if not strongs:
            strongs = entry["g"] or entry["h"]

        if strongs:
            matched.append((strongs, row["word_id"]))
        else:
            unmatched_cnt[english] += 1

    total_unmatched = sum(unmatched_cnt.values())
    print(f"  Matched  : {len(matched):,}")
    print(f"  Unmatched: {total_unmatched:,} words  ({len(unmatched_cnt):,} distinct names)\n")

    top = sorted(unmatched_cnt.items(), key=lambda x: -x[1])[:25]
    print("Top unmatched (may need aliases or stay as *):")
    for nm, cnt in top:
        print(f"  {nm!r:30}  {cnt}")
    print()

    # Dump full unmatched list (recurring first) for triage when doing a dry-run
    if DRY_RUN:
        dump = sorted(unmatched_cnt.items(), key=lambda x: (-x[1], x[0].lower()))
        with open("unmatched_pn.txt", "w", encoding="utf-8") as fh:
            for nm, cnt in dump:
                fh.write(f"{cnt}\t{nm}\n")
        recurring = [x for x in dump if x[1] >= 2]
        print(f"Wrote unmatched_pn.txt ({len(dump):,} distinct). "
              f"Recurring (count>=2): {len(recurring):,} names, "
              f"{sum(c for _,c in recurring):,} occurrences.")
        print()

    if DRY_RUN:
        print("── Sample matches ──────────────────────────────────────")
        for new_s, rowid in matched[:30]:
            r = conn.execute("""
                SELECT w.english, v.book, v.chapter, v.verse
                FROM words w JOIN verses v ON v.id=w.verse_id
                WHERE w.rowid=?
            """, (rowid,)).fetchone()
            print(f"  {r['english']:20} {r['book']} {r['chapter']}:{r['verse']:3}  →  {new_s}")
        print("\n[DRY RUN] No changes written.")
        conn.close()
        return

    # ── Apply ─────────────────────────────────────────────────────────
    print(f"Applying {len(matched):,} strongs updates...")
    conn.executemany(
        "UPDATE words SET strongs_base=?, is_pn=1 WHERE rowid=?",
        matched,
    )

    # Mark remaining * words as is_pn=1 even without a match
    conn.execute("UPDATE words SET is_pn=1 WHERE strongs_base='*'")

    remaining = conn.execute(
        "SELECT COUNT(*) FROM words WHERE strongs_base='*'"
    ).fetchone()[0]

    conn.commit()

    # ── p2wl:v2 GUARD FIXTURE DRIFT CHECK (JP-ruled 2026-07-14) ────────────────────────────────
    # Chained in HERE because this script is the VERIFIED sole writer of is_pn=1 (the two UPDATEs
    # above); the build CLEARS is_pn and everything else only reads it. So this is the one event
    # that can move the marking the probe-2 test fixture claims — and it fires whether we ran from
    # finish_rebuild.sh's tail or standalone. No hand-run step, no memory dependency.
    # Runs AFTER commit: the rebuild work is saved and complete before anything can be reported.
    # SEVERITY (JP-ruled): drift NEVER fails or aborts the rebuild — the rebuild is not wrong, the
    # FIXTURE is stale. The nonzero exit is a VERDICT, not an abort: finish_rebuild.sh collects it
    # and refuses to print "done", so the flag cannot scroll past. See DESIGN_p2_guard_drift_check.md.
    from check_p2_guard_fixture import check_guard_fixture
    fixture_ok, fixture_lines = check_guard_fixture(conn)
    conn.close()

    print(f"  {remaining:,} words still strongs_base='*' (unmatched — metaV by name still works)")
    for line in fixture_lines:
        print(line)
    print("\nDone." if fixture_ok else "\nDone — proper nouns imported, but SEE THE FIXTURE DRIFT "
                                       "FLAG ABOVE before swapping.")
    if not fixture_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
