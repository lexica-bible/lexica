#!/usr/bin/env python3
"""audit_witness_italic.py — READ-ONLY Greek-token completion check for the class-3
witness-divergence reframe (reviewer-required 2026-07-30).

For every slot in docs/tickets/class3_witness_slots.txt (the 392-row census), find
its words row(s) and report the italic flag. italic=0 = the name is a real word of
ABP's text, not a translator addition — the load-bearing evidence that the class is
witness-divergence, not supplied-subject. Any italic=1 row is the hidden true
supplied class and is listed in full.

Usage: python3 scripts/audit_witness_italic.py [bible.db]
"""
import os, sys, sqlite3

DB = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/bible-db/bible.db")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

total = it0 = it1 = nomatch = 0
italic_rows, nomatch_rows = [], []
for ln in open(os.path.join(HERE, "docs", "tickets", "class3_witness_slots.txt"), encoding="utf-8"):
    if ln.startswith("#") or not ln.strip():
        continue
    nm, bk, ch, vs = ln.strip().split("|")
    total += 1
    rows = conn.execute(
        "SELECT w.italic FROM words w JOIN verses v ON v.id=w.verse_id "
        "WHERE w.is_pn=1 AND v.book=? AND v.chapter=? AND v.verse=? "
        "AND (LOWER(COALESCE(NULLIF(w.english_head,''), w.english)) LIKE ? "
        "     OR LOWER(w.english) LIKE ?)",
        (bk, int(ch), int(vs), f"%{nm}%", f"%{nm}%")).fetchall()
    if not rows:
        nomatch += 1
        nomatch_rows.append(f"{nm} {bk} {ch}:{vs}")
    elif any(r[0] == 1 for r in rows):
        it1 += 1
        italic_rows.append(f"{nm} {bk} {ch}:{vs}")
    else:
        it0 += 1

print(f"slots: {total} | italic=0 (attested, witness-divergence confirmed): {it0} "
      f"| italic=1 (TRUE supplied class): {it1} | word row not matched: {nomatch}")
if italic_rows:
    print("\nitalic=1 rows (size before any doctrine ruling):")
    for r in italic_rows:
        print("   ", r)
if nomatch_rows:
    print("\nunmatched rows (name-form mismatch between census and word row — inspect):")
    for r in nomatch_rows[:20]:
        print("   ", r)
