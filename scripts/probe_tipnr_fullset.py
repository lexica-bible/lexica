#!/usr/bin/env python3
"""
probe_tipnr_fullset.py — READ-ONLY. The full-ambiguous-set feasibility numbers
for Issue 2, reporting THREE rates separately (they fail independently):

  RATE 1  verse -> TIPNR-entity bind  (the identity number; decides the rebuild —
          it's what kills the AI-blurb verse-fabrication class). Matched by verse
          across ALL entities, linked by name-spelling OR base Strong's, so a
          surface word filed under a different headword (Cushi -> the "Cush"
          place's "Cushite" group) still lands. Misses split into:
            soft  = versification/locality (a candidate entity has refs in the
                    SAME book+chapter; an offset, not truly unbound)
            hard  = no linked entity anywhere in that book.
  RATE 2  TIPNR person -> metaV person bridge  (relationship-keyed).
  RATE 3  TIPNR place  -> metaV place  bridge  (name-only; expected poor — we
          just report how many places even have a usable map row).

Why split: TIPNR carries its own bio/refs/descriptions, so identity+content come
from TIPNR (rate 1). metaV is only needed for coords/dates (rates 2/3), and a
place that can't bridge still binds and renders fine — it just gets no pin, which
Fix A already handles. Rate 1 is the one that matters.

Runs over the whole 724-name ambiguous set, then dumps Cushi/Eden/Judah/Joseph.
Opens bible.db read-only; only SELECTs.

Usage (on PythonAnywhere):
    python3 scripts/probe_tipnr_fullset.py
    python3 scripts/probe_tipnr_fullset.py bible.db /path/to/tipnr.txt
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

_BOOK_VARIANTS = [
    (1, "gen"), (2, "exo exod"), (3, "lev"), (4, "num"), (5, "deu deut"),
    (6, "jos josh"), (7, "jdg judg"), (8, "rth rut ruth"), (9, "1sa 1sam"),
    (10, "2sa 2sam"), (11, "1ki 1kgs"), (12, "2ki 2kgs"), (13, "1ch 1chr"),
    (14, "2ch 2chr"), (15, "ezr ezra"), (16, "neh"), (17, "est esth"), (18, "job"),
    (19, "psa psalm pss"), (20, "pro prov"), (21, "ecc eccl"), (22, "son sng sos song"),
    (23, "isa"), (24, "jer"), (25, "lam"), (26, "eze ezk ezek"), (27, "dan"),
    (28, "hos"), (29, "joe jol joel"), (30, "amo amos"), (31, "oba obad"),
    (32, "jon jonah"), (33, "mic"), (34, "nah nam nahum"), (35, "hab"), (36, "zep zeph"),
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


def norm_base(s):
    m = re.match(r"^([GH])0*(\d+)", (s or "").strip())
    return f"{m.group(1)}{int(m.group(2))}" if m else ""


def parse_ref(tok):
    tok = re.sub(r"^LXX\s*", "", tok.strip())
    if not tok:
        return None
    parts = tok.split(".")
    if len(parts) < 3:
        return None
    book = BOOKNUM.get(parts[0].strip().lower())
    if book is None:
        return None
    cm = re.match(r"\d+", parts[1].strip())
    vm = re.match(r"\d+", parts[2].strip())
    if not cm or not vm:
        return None
    return (book, int(cm.group()), int(vm.group()))


def parse_tipnr(lines):
    """Each entity keeps: headword name, ALL spellings (headword + sub UniqueNames
    + ESV/KJV/NIV translated-name tokens), ALL base Strong's, section, parents/
    offspring names, and the exhaustive reference set."""
    ents = []
    section = "other"
    cur = None

    def close(c):
        if c:
            ents.append(c)

    for line in lines:
        if line.startswith("$=========="):
            close(cur); cur = None
            low = line.lower()
            section = "person" if "person" in low else "place" if "place" in low else "other"
            continue
        if not line.strip():
            continue
        stripped = line.lstrip()
        if stripped[:1] in ("=", "‖", "#", "*", "@") or stripped.startswith("UnifiedName") \
                or stripped.startswith("UniqueName"):
            continue
        is_sub = line[0] in (" ", "\t") or stripped.startswith("–")
        parts = line.split("\t")

        if not is_sub:
            close(cur); cur = None
            f0 = parts[0].strip()
            if "@" not in f0:
                continue
            head = norm_name(f0.split("@")[0])
            if not head:
                continue
            cur = {
                "head": head, "uniq": f0.split("=")[0].strip(), "section": section,
                "spellings": {head}, "bases": set(), "refs": set(),
                "parents": parts[2].strip() if len(parts) > 2 else "",
                "offspring": parts[5].strip() if len(parts) > 5 else "",
            }
            b = norm_base(f0.split("=", 1)[1]) if "=" in f0 else ""
            if b:
                cur["bases"].add(b)
        else:
            if not cur:
                continue
            # sub-record: col1 = UniqueName (AltName@..), col2 = dStrong«eStrong,
            # col3 = translated name (ESV,KJV,NIV). Mine spellings + base + refs.
            if len(parts) > 1 and "@" in parts[1]:
                cur["spellings"].add(norm_name(parts[1].split("@")[0]))
            if len(parts) > 2 and "«" in parts[2]:
                b = norm_base(parts[2].split("«")[0])
                if b:
                    cur["bases"].add(b)
            if len(parts) > 3 and parts[3].strip():
                for tok in re.split(r"[,/()]", parts[3]):
                    w = norm_name(tok)
                    if w and re.match(r"^[a-z][a-z' -]+$", w):
                        cur["spellings"].add(w)
            ref_blob = None
            for i, f in enumerate(parts):
                if "reference=" in f:
                    ref_blob = parts[i + 1] if i + 1 < len(parts) else f.split("reference=", 1)[1]
                    break
            if ref_blob:
                for tok in ref_blob.split(";"):
                    r = parse_ref(tok)
                    if r:
                        cur["refs"].add(r)
    close(cur)
    return ents


def main():
    print(f"READ-ONLY TIPNR full-set probe -> {DB}\n")
    if TIPNR_LOCAL:
        lines = open(TIPNR_LOCAL, encoding="utf-8-sig").read().splitlines()
        print(f"TIPNR: {TIPNR_LOCAL} ({len(lines):,} lines)")
    else:
        print("Downloading TIPNR...")
        with urllib.request.urlopen(TIPNR_URL) as r:
            lines = r.read().decode("utf-8-sig").splitlines()
        print(f"  {len(lines):,} lines")

    ents = parse_tipnr(lines)
    name_idx = defaultdict(set)     # spelling -> {entity idx}
    base_idx = defaultdict(set)     # base strongs -> {entity idx}
    chap_idx = defaultdict(set)     # entity idx -> {(book,chap)}  for soft check
    for i, e in enumerate(ents):
        for s in e["spellings"]:
            name_idx[s].add(i)
        for b in e["bases"]:
            base_idx[b].add(i)
        chap_idx[i] = {(bk, ch) for (bk, ch, _v) in e["refs"]}
    print(f"Parsed {len(ents):,} entities\n")

    def classify(name, bk, ch, vs, base):
        """-> one of clean / variant / strongs / soft / hard."""
        V = (bk, ch, vs)
        name_cands = name_idx.get(name, set())
        base_cands = base_idx.get(base, set()) if base else set()
        # bound by NAME (verse in a same-name entity)
        nm_hit = [i for i in name_cands if V in ents[i]["refs"]]
        if nm_hit:
            return "clean" if any(ents[i]["head"] == name for i in nm_hit) else "variant"
        # bound by base STRONG'S across headwords (the Cushi->Cush case)
        if any(V in ents[i]["refs"] for i in base_cands):
            return "strongs"
        # soft: a candidate entity has refs in the same book+chapter (offset)
        if any((bk, ch) in chap_idx[i] for i in (name_cands | base_cands)):
            return "soft"
        return "hard"

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # ── Ambiguous name set (mirrors audit_entity_resolution: >1 person, >1 place,
    #    or both), intersected with names that occur in the text ────────────────
    place_ids, person_ids = defaultdict(set), defaultdict(set)
    for r in conn.execute("SELECT place_id, name FROM metav_places WHERE name IS NOT NULL"):
        place_ids[norm_name(r["name"])].add(r["place_id"])
    for r in conn.execute("SELECT place_id, alias FROM metav_place_aliases WHERE alias IS NOT NULL"):
        place_ids[norm_name(r["alias"])].add(r["place_id"])
    for r in conn.execute("SELECT person_id, name FROM metav_people WHERE name IS NOT NULL"):
        person_ids[norm_name(r["name"])].add(r["person_id"])
    for r in conn.execute("SELECT person_id, alias FROM metav_people_aliases WHERE alias IS NOT NULL"):
        person_ids[norm_name(r["alias"])].add(r["person_id"])
    place_ids.pop("", None); person_ids.pop("", None)
    ambiguous = ({n for n, ids in place_ids.items() if len(ids) > 1}
                 | {n for n, ids in person_ids.items() if len(ids) > 1}
                 | {n for n in place_ids if n in person_ids})

    has_pn = "is_pn" in {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    pn_where = "w.is_pn = 1" if has_pn else "w.strongs_base = '*'"
    occ_rows = conn.execute(f"""
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               w.strongs_base AS base
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE {pn_where}
          AND COALESCE(NULLIF(w.english_head,''), w.english) IS NOT NULL
          AND COALESCE(NULLIF(w.english_head,''), w.english) != ''
    """).fetchall()

    # ── RATE 1 over the whole ambiguous set ─────────────────────────────────
    buckets = defaultdict(int)
    per_name = defaultdict(lambda: defaultdict(int))
    occ_set_names = set()
    for r in occ_rows:
        nm = norm_name(r["label"])
        if nm not in ambiguous:
            continue
        occ_set_names.add(nm)
        bk = BOOKNUM.get((r["book"] or "").lower())
        if bk is None:
            buckets["hard"] += 1; per_name[nm]["hard"] += 1; continue
        b = norm_base(r["base"])
        cat = classify(nm, bk, r["ch"], r["vs"], b)
        buckets[cat] += 1
        per_name[nm][cat] += 1

    total = sum(buckets.values())
    bound = buckets["clean"] + buckets["variant"] + buckets["strongs"]
    print("=" * 72)
    print(f"RATE 1 — verse -> TIPNR-entity BIND, over the ambiguous set")
    print(f"  ambiguous names total (metaV)        : {len(ambiguous):,}")
    print(f"  ambiguous names occurring in text     : {len(occ_set_names):,}")
    print(f"  occurrences on an ambiguous name      : {total:,}")
    if total:
        print(f"  BOUND                                 : {bound:,}  ({100*bound/total:.1f}%)")
        print(f"     clean   (headword name+verse)      : {buckets['clean']:,}")
        print(f"     variant (other spelling+verse)     : {buckets['variant']:,}")
        print(f"     strongs (across headword, by #)    : {buckets['strongs']:,}  <- headword-artifact catches")
        print(f"  soft miss (versification/locality)    : {buckets['soft']:,}  ({100*buckets['soft']/total:.1f}%)")
        print(f"  HARD unbindable                       : {buckets['hard']:,}  ({100*buckets['hard']/total:.1f}%)")

    # ── RATE 2 — people bridge (relationship-keyed) over ambiguous persons ───
    def rel_names(pid):
        return {(x["name"] or "").lower() for x in conn.execute(
            "SELECT p.name FROM metav_people_relationships r "
            "JOIN metav_people p ON p.person_id=r.related_to WHERE r.person_id=?", (pid,))}

    amb_person_ents = [e for e in ents if e["section"] == "person" and e["head"] in ambiguous]
    p_unique = p_norel = p_nomatch = p_multi = 0
    for e in amb_person_ents:
        R = set()
        for blob in (e["parents"], e["offspring"]):
            for tok in re.split(r"[,+]", blob):
                nm = norm_name(tok.split("@")[0])
                if nm:
                    R.add(nm)
        if not R:
            p_norel += 1; continue
        rows = conn.execute("SELECT person_id FROM metav_people WHERE name=? COLLATE NOCASE",
                            (e["head"],)).fetchall()
        hits = [r["person_id"] for r in rows if R & rel_names(r["person_id"])]
        if len(hits) == 1:
            p_unique += 1
        elif len(hits) == 0:
            p_nomatch += 1
        else:
            p_multi += 1
    npe = len(amb_person_ents) or 1
    print("\n" + "=" * 72)
    print(f"RATE 2 — TIPNR person -> metaV person bridge (relationship-keyed)")
    print(f"  ambiguous-set TIPNR person entities   : {len(amb_person_ents):,}")
    print(f"  bridged to a UNIQUE metaV row         : {p_unique:,}  ({100*p_unique/npe:.1f}%)")
    print(f"  could not bridge — entity has no kin  : {p_norel:,}")
    print(f"  could not bridge — no metaV match     : {p_nomatch:,}")
    print(f"  ambiguous bridge (>1 metaV row)       : {p_multi:,}")

    # ── RATE 3 — places: do they even have a usable metaV map row? ───────────
    amb_place_names = {e["head"] for e in ents if e["section"] == "place" and e["head"] in ambiguous}
    pl_withmap = pl_rowonly = pl_none = 0
    for nm in amb_place_names:
        rows = conn.execute("""
            SELECT lat, lon FROM metav_places WHERE name=? COLLATE NOCASE
            UNION SELECT p.lat, p.lon FROM metav_places p
              JOIN metav_place_aliases a ON a.place_id=p.place_id WHERE a.alias=? COLLATE NOCASE
        """, (nm, nm)).fetchall()
        if not rows:
            pl_none += 1
        elif any(r["lat"] is not None and r["lon"] is not None for r in rows):
            pl_withmap += 1
        else:
            pl_rowonly += 1
    npl = len(amb_place_names) or 1
    print("\n" + "=" * 72)
    print(f"RATE 3 — TIPNR place -> metaV place (name-only; coords coverage)")
    print(f"  ambiguous-set TIPNR place names       : {len(amb_place_names):,}")
    print(f"  have a metaV place row WITH coords    : {pl_withmap:,}  ({100*pl_withmap/npl:.1f}%)")
    print(f"  metaV row exists but NO coords        : {pl_rowonly:,}")
    print(f"  no metaV place row at all             : {pl_none:,}")

    # ── 4-name dump ─────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("FOUR-NAME DUMP (bucket split + bridges)")
    for nm in PROBE_NAMES:
        d = per_name.get(nm, {})
        tot = sum(d.values())
        print(f"\n  {nm}  (occurrences={tot})")
        print(f"     clean={d.get('clean',0)} variant={d.get('variant',0)} "
              f"strongs/headword-catch={d.get('strongs',0)} "
              f"versification(soft)={d.get('soft',0)} hard={d.get('hard',0)}")

    conn.close()
    print("\nDone. (read-only — nothing was changed)")


if __name__ == "__main__":
    main()
