#!/usr/bin/env python3
"""
dump_verse_words.py — READ-ONLY. Print every word slot of one or more verses, in
position order, with the columns that matter for a wrong-slot / dual-ordering fix
(position, bracket id, greek_pos, strongs_base, morph POS, english, english_head).

Never writes — opens the database read-only (mode=ro). Run on PA from the repo root:
  python3 scripts/dump_verse_words.py bible.db "1Co 3:8" "1Ti 6:1"
  python3 scripts/dump_verse_words.py bible.db "1Co 3:8" "1Co 4:12" "1Co 7:4" \\
      "1Co 11:21" "1Co 14:35" "1Co 15:38" "1Ti 3:5" "1Ti 4:2" "1Ti 6:1"
"""
import sqlite3
import sys

ARGS = sys.argv[1:]
if not ARGS:
    sys.exit("usage: dump_verse_words.py <db> \"<Book Ch:V>\" [more refs...]")
DB = ARGS[0]
REFS = ARGS[1:] or ["1Co 3:8"]


def parse_ref(ref):
    """'1Co 3:8' -> ('1Co', 3, 8). Book = everything before the last token."""
    parts = ref.split()
    cv = parts[-1]
    book = " ".join(parts[:-1])
    ch, vs = cv.split(":")
    return book, int(ch), int(vs)


conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

WCOLS = {r[1] for r in conn.execute("PRAGMA table_info(words)")}
GPOS = "greek_pos" if "greek_pos" in WCOLS else "NULL AS greek_pos"
MORPH = "morph" if "morph" in WCOLS else "NULL AS morph"
PN = "is_pn" if "is_pn" in WCOLS else "0 AS is_pn"

print(f"READ-ONLY verse word dump -> {DB}\n")
for ref in REFS:
    book, ch, vs = parse_ref(ref)
    vrow = conn.execute(
        "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
        (book, ch, vs)).fetchone()
    if not vrow:
        print(f"  {ref}: verse not found\n")
        continue
    rows = conn.execute(
        f"SELECT position, bracket_id, {GPOS}, strongs_base, {MORPH}, {PN}, "
        f"       english, english_head "
        f"FROM words WHERE verse_id=? ORDER BY position", (vrow["id"],)).fetchall()
    print(f"  === {ref}  (verse_id={vrow['id']}, {len(rows)} slots) ===")
    print(f"  {'pos':>3} {'bid':>4} {'gpos':>5} {'strongs':>8} {'pos':>3} {'pn':>2}  "
          f"{'english':<26} english_head")
    for r in rows:
        morph = (r["morph"] or "")
        pos = morph.lstrip("-")[:1].upper() if morph else ""
        print(f"  {r['position']:>3} {str(r['bracket_id'] or ''):>4} "
              f"{str(r['greek_pos'] if r['greek_pos'] is not None else ''):>5} "
              f"{(r['strongs_base'] or ''):>8} {pos:>3} {r['is_pn']:>2}  "
              f"{(r['english'] or '')!r:<26} {(r['english_head'] or '')!r}")
    print()
conn.close()
