#!/usr/bin/env python3
"""dump_wordpos_lane.py — READ-ONLY evidence dump for the word-position binding
lane prereg fill (DESIGN_wordpos_binding.md section 4; reviewer-ratified design,
codicils C1-C3). Reads the FROZEN census member list
(docs/tickets/wordpos_census_20260807.txt) and, for every lane verse plus the
Ezr 10:25 variant-spelling appendix, prints:
  - the verse prose (verses.text — the clean ordered English),
  - every words row: position, english_head, english, strongs_base, bracket_id,
    is_pn, italic (bracket_id is the bracket-adjacency input for control (c)),
  - the TIPNR candidate entities for each group name (uniq, section, descr,
    parents, offspring) — the pool the per-slot proposals draw from (C1: the
    parent/offspring line here is the load-bearing identity evidence).
Never writes anything. Usage (PA):
  cd ~/bible-db && PYTHONIOENCODING=utf-8 python3 scripts/dump_wordpos_lane.py bible.db
"""
import sys, os, re, sqlite3

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
HERE = os.path.dirname(os.path.abspath(__file__))
CENSUS = os.path.join(HERE, "..", "docs", "tickets", "wordpos_census_20260807.txt")

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

LINE = re.compile(r"^(\w{3})\s+(\d+):(\d+)\s+(\w+)\s+p\[([\d,\s]+)\]")
groups = []
for ln in open(CENSUS, encoding="utf-8"):
    m = LINE.match(ln.strip())
    if m:
        bk, ch, vs, name, ps = m.groups()
        groups.append((bk, int(ch), int(vs), name,
                       [int(p) for p in ps.split(",")]))
# appendix pair (bucket C, flagged member per R4/rider 1)
groups.append(("Ezr", 10, 25, "malchiah/malchijah", [10, 16]))

compact = lambda s: re.sub(r"[^a-z]", "", (s or "").lower())

def tipnr_candidates(name):
    out = []
    for want in name.split("/"):
        cw = compact(want)
        for r in conn.execute(
                "SELECT uniq, section, descr, parents, offspring "
                "FROM tipnr_entities"):
            if compact(r["uniq"].split("@")[0]) == cw:
                out.append(r)
    return out

for bk, ch, vs, name, ps in groups:
    print("=" * 78)
    print(f"GROUP  {bk} {ch}:{vs}  {name}  slots {ps}")
    v = conn.execute(
        "SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?",
        (bk, ch, vs)).fetchone()
    if not v:
        print("  !! verse row MISSING")
        continue
    print(f"  PROSE: {v['text']}")
    print("  pos  head            english                        strongs_base  bid  pn it")
    for w in conn.execute(
            "SELECT position, english_head, english, strongs_base, bracket_id, "
            "is_pn, italic FROM words WHERE verse_id=? ORDER BY position",
            (v["id"],)):
        mark = " <== lane slot" if w["position"] in ps else ""
        print(f"  {w['position']:>3}  {(w['english_head'] or ''):<14}  "
              f"{(w['english'] or ''):<29}  {(w['strongs_base'] or ''):<12}  "
              f"{str(w['bracket_id'] if w['bracket_id'] is not None else '-'):>3}  "
              f"{w['is_pn']}  {w['italic']}{mark}")
    cands = tipnr_candidates(name)
    print(f"  TIPNR candidates under this name: {len(cands)}")
    for c in cands:
        print(f"    {c['uniq']}  [{c['section'] or '?'}]")
        if c["descr"]:
            print(f"      descr:     {c['descr']}")
        if c["parents"]:
            print(f"      parents:   {c['parents']}")
        if c["offspring"]:
            print(f"      offspring: {c['offspring']}")
conn.close()
