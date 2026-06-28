#!/usr/bin/env python3
"""
probe_tipnr_binding.py — READ-ONLY feasibility probe for Issue 2 (B vs C).

Decides whether occurrence-level binding is feasible by answering three questions
for the worst-offender names (Cushi, Eden, Judah, Joseph). It re-parses TIPNR
KEEPING each entity's @reference id, disambiguated Strong's, relationships, and
exhaustive reference list (import_tipnr.py throws all of that away), then checks
it against bible.db and the metaV tables. It only ever SELECTs.

Per name it prints:
  (1) JOIN KEY  — which field, other than the name string, maps a TIPNR entity to
                  a metav_people / metav_places row. Name-only = fail.
  (2) CARDINALITY — TIPNR entity count vs metaV row count. Mismatch = lossy.
  (3) UNBINDABLE — text occurrences whose verse is in no entity's reference list
                  (the residual that the rebuild can't bind -> stays on Fix A).

Usage (on PythonAnywhere):
    python3 scripts/probe_tipnr_binding.py
    python3 scripts/probe_tipnr_binding.py /home/appssanding720/bible-db/bible.db
    python3 scripts/probe_tipnr_binding.py bible.db /path/to/tipnr.txt   # reuse a local copy
"""

import re
import sys
import sqlite3
import urllib.request
from collections import defaultdict

DB = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else \
    "/home/appssanding720/bible-db/bible.db"
TIPNR_LOCAL = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None

TIPNR_URL = (
    "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/"
    "Proper%20Nouns/TIPNR%20-%20Translators%20Individualised%20Proper%20Names"
    "%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt"
)

PROBE_NAMES = ["cushi", "eden", "judah", "joseph"]

# Canonical book number for EVERY abbreviation we might see — ABP's (verses.book:
# Eze/Joe/Mar/Joh/Son/Rth) AND TIPNR's (Ezk/Jol/Mrk/Jhn/Sng/Rut). Compare by number
# so an Ezekiel ref never looks "unbindable" just because the two files spell it
# differently. Anything unmapped is reported, never silently counted.
_BOOK_VARIANTS = [
    (1, "gen"), (2, "exo exod"), (3, "lev"), (4, "num"), (5, "deu deut"),
    (6, "jos josh"), (7, "jdg judg"), (8, "rth rut ruth"), (9, "1sa 1sam"),
    (10, "2sa 2sam"), (11, "1ki 1kgs"), (12, "2ki 2kgs"), (13, "1ch 1chr"),
    (14, "2ch 2chr"), (15, "ezr ezra"), (16, "neh"), (17, "est esth"), (18, "job"),
    (19, "psa psalm pss"), (20, "pro prov"), (21, "ecc eccl"), (22, "son sng sos song"),
    (23, "isa"), (24, "jer"), (25, "lam"), (26, "eze ezk ezek"), (27, "dan"),
    (28, "hos"), (29, "joe jol joel"), (30, "amo amos"), (31, "oba obad"),
    (32, "jon jonah"), (33, "mic"), (34, "nah"), (35, "hab"), (36, "zep zeph"),
    (37, "hag"), (38, "zec zech"), (39, "mal"), (40, "mat matt"), (41, "mar mrk mark"),
    (42, "luk luke"), (43, "joh jhn john"), (44, "act acts"), (45, "rom"),
    (46, "1co 1cor"), (47, "2co 2cor"), (48, "gal"), (49, "eph"), (50, "php phil"),
    (51, "col"), (52, "1th 1thess"), (53, "2th 2thess"), (54, "1ti 1tim"),
    (55, "2ti 2tim"), (56, "tit titus"), (57, "phm phlm"), (58, "heb"),
    (59, "jas james"), (60, "1pe 1pet"), (61, "2pe 2pet"), (62, "1jn 1jo 1john"),
    (63, "2jn 2jo"), (64, "3jn 3jo"), (65, "jud jude"), (66, "rev"),
]
BOOKNUM = {}
for _n, _abbrs in _BOOK_VARIANTS:
    for _a in _abbrs.split():
        BOOKNUM[_a] = _n


def norm_name(s):
    if not s:
        return ""
    return re.sub(r"[\s,.:;!?'\"–\-]+$", "", s.strip()).lower()


def parse_ref(tok):
    """'Ezk.31.18a' -> (booknum, chap, verse) or None. Strips LXX/letters/ranges."""
    tok = tok.strip()
    if not tok:
        return None
    tok = re.sub(r"^LXX\s*", "", tok)
    parts = tok.split(".")
    if len(parts) < 3:
        return None
    book = BOOKNUM.get(parts[0].strip().lower())
    if book is None:
        return ("UNMAPPED", parts[0].strip(), tok)
    cm = re.match(r"\d+", parts[1].strip())
    vm = re.match(r"\d+", parts[2].strip())   # 'a'/'b' suffix and ranges -> start
    if not cm or not vm:
        return None
    return (book, int(cm.group()), int(vm.group()))


def parse_tipnr(lines):
    """Returns entities: list of dicts keyed-able by name. Each entity keeps its
    @reference id, disambiguated + base Strong's, type, parents/offspring, and the
    full set of reference triples gathered from every sub-record."""
    ents = []
    section = "other"
    cur = None

    def close(cur):
        if cur:
            ents.append(cur)

    for line in lines:
        if line.startswith("$=========="):
            close(cur); cur = None
            low = line.lower()
            section = "person" if "person" in low else "place" if "place" in low else "other"
            continue
        if not line.strip():
            continue
        stripped = line.lstrip()
        if stripped[:1] in ("=", "‖", "#", "*") or stripped.startswith("UnifiedName") \
                or stripped.startswith("UniqueName") or stripped.startswith("–") \
                or stripped.startswith("@"):
            # NB: sub-records start with "– "; we still mine refs from them below,
            # so handle the "– " case BEFORE this guard.
            if not (stripped.startswith("– ") or stripped.startswith("–\t")):
                continue

        is_sub = line[0] in (" ", "\t") or stripped.startswith("–")
        parts = line.split("\t")

        if not is_sub:
            close(cur); cur = None
            f0 = parts[0].strip()
            if "@" not in f0:
                continue
            name = f0.split("@")[0].strip()
            uniq = f0.split("=")[0].strip()            # Name@FirstRef
            dstrong = f0.split("=", 1)[1].strip() if "=" in f0 else ""
            base = ""
            m = re.match(r"^([GH])0*(\d+)", dstrong)
            if m:
                base = f"{m.group(1)}{int(m.group(2))}"
            # Type is the last non-empty tab field; parents=col2, offspring=col5
            typ = ""
            for p in reversed(parts):
                if p.strip():
                    typ = p.strip(); break
            cur = {
                "name": name, "uniq": uniq, "dstrong": dstrong, "base": base,
                "section": section, "type": typ,
                "parents": parts[2].strip() if len(parts) > 2 else "",
                "offspring": parts[5].strip() if len(parts) > 5 else "",
                "refs": set(), "unmapped": set(),
            }
        else:
            if not cur:
                continue
            m = re.search(r"reference=([^\t]*)", line)
            if m:
                for tok in m.group(1).split(";"):
                    r = parse_ref(tok)
                    if r and r[0] == "UNMAPPED":
                        cur["unmapped"].add(r[1])
                    elif r:
                        cur["refs"].add(r)
    close(cur)
    return ents


def main():
    print(f"READ-ONLY TIPNR-binding probe -> {DB}\n")

    if TIPNR_LOCAL:
        with open(TIPNR_LOCAL, encoding="utf-8-sig") as fh:
            lines = fh.read().splitlines()
        print(f"TIPNR: {TIPNR_LOCAL} ({len(lines):,} lines)")
    else:
        print("Downloading TIPNR...")
        with urllib.request.urlopen(TIPNR_URL) as r:
            lines = r.read().decode("utf-8-sig").splitlines()
        print(f"  {len(lines):,} lines")

    ents = parse_tipnr(lines)
    by_name = defaultdict(list)
    for e in ents:
        by_name[norm_name(e["name"])].append(e)
    print(f"Parsed {len(ents):,} TIPNR entities, {len(by_name):,} distinct names\n")

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # Corpus-wide structural fact for the join-key question
    ppl_cols = {r[1] for r in conn.execute("PRAGMA table_info(metav_people)")}
    plc_cols = {r[1] for r in conn.execute("PRAGMA table_info(metav_places)")}
    print("=" * 72)
    print("JOIN-KEY STRUCTURAL FACT (holds for ALL names, not just the 4 below)")
    print("=" * 72)
    print(f"  metav_people columns : {sorted(ppl_cols)}")
    print(f"  -> carries a Strong's number? {'YES' if any('strong' in c for c in ppl_cols) else 'NO'}")
    print(f"  metav_places columns : {sorted(plc_cols)}")
    print(f"  -> carries a Strong's number? {'YES (' + ','.join(c for c in plc_cols if 'strong' in c) + ')' if any('strong' in c for c in plc_cols) else 'NO'}")
    print("  TIPNR entities are keyed by  Name@FirstRef  + a disambiguated Strong's")
    print("  (e.g. H3569H). If metaV has no Strong's, the only shared field is the")
    print("  NAME STRING -> a TIPNR id cannot address a metaV row directly.\n")

    has_pn = "is_pn" in {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    pn_where = "w.is_pn = 1" if has_pn else "w.strongs_base = '*'"

    for name in PROBE_NAMES:
        tents = by_name.get(name, [])
        persons = [e for e in tents if e["section"] == "person"]
        places  = [e for e in tents if e["section"] == "place"]
        others  = [e for e in tents if e["section"] == "other"]

        mp = conn.execute(
            "SELECT * FROM metav_people WHERE name = ? COLLATE NOCASE", (name,)).fetchall()
        mpl = conn.execute(
            "SELECT * FROM metav_places WHERE name = ? COLLATE NOCASE", (name,)).fetchall()

        print("\n" + "#" * 72)
        print(f"#  {name.upper()}")
        print("#" * 72)

        # ── (1) JOIN KEY ───────────────────────────────────────────────────
        print("\n(1) JOIN KEY — TIPNR entity -> metaV row, by what besides the name?")
        print("  TIPNR entities:")
        for e in tents:
            print(f"     {e['uniq']:28} dStrong={e['dstrong']:8} base={e['base']:6}"
                  f" {e['section']:6} refs={len(e['refs'])}"
                  + (f"  parents={e['parents']}" if e['parents'] else "")
                  + (f"  offspring={e['offspring']}" if e['offspring'] else ""))
        print("  metaV people rows:")
        for r in mp:
            rels = conn.execute("""
                SELECT r.rel_type, p.name FROM metav_people_relationships r
                JOIN metav_people p ON p.person_id = r.related_to
                WHERE r.person_id = ?""", (r["person_id"],)).fetchall()
            relstr = ", ".join(f"{x['rel_type']}:{x['name']}" for x in rels) or "—"
            print(f"     person_id={r['person_id']}  surname={r['surname']!r}"
                  f"  born={r['birth_year']} died={r['death_year']}  rels=[{relstr}]")
        print("  metaV place rows:")
        for r in mpl:
            print(f"     place_id={r['place_id']}  name={r['name']!r}"
                  f"  strongs_g={r['strongs_g']!r}  lat/lon={r['lat']},{r['lon']}")
        # Candidate-key tests
        tipnr_bases = {e["base"] for e in tents if e["base"]}
        plc_strongs = {(r["strongs_g"] or "").upper() for r in mpl if r["strongs_g"]}
        key_hit = tipnr_bases & plc_strongs
        print("  TEST strongs match (TIPNR base vs metav_places.strongs_g):"
              f" {sorted(key_hit) if key_hit else 'NONE'}"
              + ("  (people: metav has no strongs column -> impossible)" if mp else ""))
        # Relationship-name bridge (the only non-name hook for people)
        tipnr_relnames = set()
        for e in persons:
            for blob in (e["parents"], e["offspring"]):
                for tok in re.split(r"[,+]", blob):
                    nm = tok.split("@")[0].strip().lower()
                    if nm:
                        tipnr_relnames.add(nm)
        metav_relnames = set()
        for r in mp:
            for x in conn.execute("""
                SELECT p.name FROM metav_people_relationships r
                JOIN metav_people p ON p.person_id = r.related_to
                WHERE r.person_id = ?""", (r["person_id"],)).fetchall():
                metav_relnames.add((x["name"] or "").lower())
        bridge = tipnr_relnames & metav_relnames
        print(f"  TEST relationship-name bridge (people): TIPNR={sorted(tipnr_relnames) or '—'}")
        print(f"                                          metaV={sorted(metav_relnames) or '—'}")
        print(f"                                          overlap={sorted(bridge) or 'NONE'}")

        # ── (2) CARDINALITY ────────────────────────────────────────────────
        print("\n(2) CARDINALITY — TIPNR entities vs metaV rows")
        print(f"     persons: TIPNR {len(persons)}  vs  metaV {len(mp)}"
              + ("   *** MISMATCH ***" if len(persons) != len(mp) else "   ok")
              + (f"   (+{len(others)} 'other'-section TIPNR)" if others else ""))
        print(f"     places : TIPNR {len(places)}  vs  metaV {len(mpl)}"
              + ("   *** MISMATCH ***" if len(places) != len(mpl) else "   ok"))

        # ── (3) UNBINDABLE ─────────────────────────────────────────────────
        all_refs = set()
        for e in tents:
            all_refs |= e["refs"]
        raw_occ = conn.execute(f"""
            SELECT v.book, v.chapter, v.verse, w.english_head, w.english
            FROM words w JOIN verses v ON v.id = w.verse_id
            WHERE {pn_where}
              AND (lower(w.english_head) LIKE ? OR lower(w.english) LIKE ?)
        """, (name + "%", name + "%")).fetchall()
        # Exact normalized match in Python (strips trailing punctuation like "Eden,")
        occ = [r for r in raw_occ
               if norm_name((r["english_head"] or "").strip() or (r["english"] or "")) == name]
        miss = []
        for r in occ:
            bn = BOOKNUM.get((r["book"] or "").lower())
            key = (bn, r["chapter"], r["verse"])
            if bn is None or key not in all_refs:
                miss.append((r["book"], r["chapter"], r["verse"], "book?" if bn is None else "no-ref"))
        print("\n(3) UNBINDABLE — text occurrences with no matching TIPNR reference")
        print(f"     occurrences of '{name}' in text : {len(occ)}")
        print(f"     TIPNR reference triples (union)  : {len(all_refs)}")
        if occ:
            print(f"     unbindable                       : {len(miss)}   ({100*len(miss)/len(occ):.0f}%)")
        else:
            print("     unbindable                       : (no occurrences of this surface name)")
        if miss:
            shown = miss[:15]
            print("       misses: " + ", ".join(f"{b} {c}:{v}[{why}]" for b, c, v, why in shown)
                  + (f"  +{len(miss)-len(shown)} more" if len(miss) > len(shown) else ""))
        unmapped = set()
        for e in tents:
            unmapped |= e["unmapped"]
        if unmapped:
            print(f"     NOTE unmapped TIPNR book tokens: {sorted(unmapped)}")

    conn.close()
    print("\nDone. (read-only — nothing was changed)")


if __name__ == "__main__":
    main()
