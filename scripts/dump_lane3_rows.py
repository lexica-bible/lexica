#!/usr/bin/env python3
"""dump_lane3_rows.py — READ-ONLY dump of the live words rows for the lane-3
hand-repair verses (69 repair-candidate verses from LANE3_b2_dispositions.md
+ Mat 27:26). Prints verses.text plus every word row, tab-separated, so the
repair patch can be built byte-exact from the LIVE table.

Usage (PA):
  PYTHONIOENCODING=utf-8 python3 scripts/dump_lane3_rows.py ~/bible-db/bible.db > ~/lane3_rows.txt
"""
import sqlite3
import sys

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"

VERSES = [
    # MERGE-gentilic (21 verses / 22 rows)
    "Act 2:10", "Act 14:2", "Mar 12:18", "Mat 9:11", "Mat 12:41",
    "2Ch 14:12", "2Ki 7:15", "2Sa 14:4", "Est 9:6", "Est 9:12",
    "Isa 19:2", "Isa 30:31", "Jer 24:5", "Jer 50:16", "Jer 51:1",
    "Jer 51:24", "Job 1:15", "Lev 24:10", "Num 25:8", "Num 25:14",
    "Num 25:15",
    # MERGE-name (40 verses / 41 rows)
    "Luk 1:12", "Luk 1:18", "1Ch 1:50", "1Ki 15:8", "2Ch 18:13",
    "2Ch 18:16", "2Ch 18:18", "2Ch 18:24", "2Ch 18:27", "2Ch 34:15",
    "2Ch 34:22", "2Ki 22:9", "2Sa 3:15", "2Sa 10:16", "Est 4:12",
    "Exo 36:1", "Exo 37:1", "Eze 23:5", "Eze 26:2", "Ezr 2:63",
    "Gen 5:9", "Gen 5:10", "Gen 5:15", "Gen 5:16", "Gen 11:14",
    "Gen 11:15", "Jer 20:1", "Jer 20:3", "Jer 22:28", "Jer 26:21",
    "Jer 38:8", "Jer 38:11", "Jer 49:1", "Jer 49:3", "Jer 51:41",
    "Jos 5:15", "Jdg 1:6", "Jdg 1:7", "Neh 3:21", "Neh 7:65",
    # MERGE-possessive (8 verses)
    "Heb 11:24", "Luk 17:32", "1Ch 21:9", "1Sa 14:50", "1Sa 24:5",
    "Gen 46:26", "Gen 50:23", "Job 42:10",
    # Mat 27:26 (class-A flagship, same hand lane)
    "Mat 27:26",
]

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

missing = 0
for ref in VERSES:
    book, rest = ref.rsplit(" ", 1)
    ch, vs = rest.split(":")
    v = conn.execute(
        "SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?",
        (book, int(ch), int(vs))).fetchone()
    if v is None:
        print(f"=== {ref} === VERSE NOT FOUND")
        missing += 1
        continue
    print(f"=== {ref} === (verse_id {v['id']})")
    print(f"TEXT\t{v['text']}")
    for w in conn.execute(
            "SELECT position, greek, english, english_head, strongs, strongs_base,"
            " greek_pos, bracket_id, is_pn FROM words WHERE verse_id=?"
            " ORDER BY position", (v["id"],)):
        print("\t".join(str(w[c]) if w[c] is not None else ""
                        for c in ("position", "greek", "english", "english_head",
                                  "strongs", "strongs_base", "greek_pos",
                                  "bracket_id", "is_pn")))
    print()

conn.close()
print(f"# {len(VERSES)} verses requested, {missing} missing")
