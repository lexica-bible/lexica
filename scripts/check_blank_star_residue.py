#!/usr/bin/env python3
"""
check_blank_star_residue.py — gate-2/gate-5 reconciliation for the head-word rebuild.

Read-only. Compares the db's CURRENT blank star rows (no English on a strongs='*'
row) against the reviewer-approved baseline piles in
docs/tickets/blank_star_classes.md (CAP 148 / MID 64 / NOCAP 40 / EMPTY 225 = 477).

Reports, itemized:
  - CAP rows STILL blank          (on the rebuilt copy this must be 0 — RC-2 fixed them;
                                   on the live db this is the CONTROL: all 148 fire)
  - blank rows NOT in any pile    (must be 0 everywhere — a new blank shape = STOP)
  - pile rows NO LONGER blank     (MID/NOCAP/EMPTY are expected untouched; on the live
                                   db CAP is also untouched)

Usage: python3 scripts/check_blank_star_residue.py <db>
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "docs" / "tickets" / "blank_star_classes.md"


def load_piles():
    piles = {}
    pile = None
    in_block = False
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            pile = line[3:].split(" ")[0].strip()
            piles.setdefault(pile, set())
            in_block = False
        elif line.strip() == "```":
            in_block = not in_block
        elif in_block and pile and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            piles[pile].add((parts[0], int(parts[1])))
    return piles


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    db_path = sys.argv[1]
    piles = load_piles()
    expected_sizes = {"CAP": 148, "MID": 64, "NOCAP": 40, "EMPTY": 225}
    for name, size in expected_sizes.items():
        if len(piles.get(name, ())) != size:
            print(f"BASELINE PARSE ERROR: pile {name} read {len(piles.get(name, ()))} "
                  f"entries, expected {size}. Fix the parser/baseline before trusting "
                  f"anything below.")
            sys.exit(2)

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    blank = {
        (f"{b} {c}:{v}", pos)
        for b, c, v, pos in con.execute(
            "SELECT v.book, v.chapter, v.verse, w.position "
            "FROM words w JOIN verses v ON v.id = w.verse_id "
            "WHERE w.strongs = '*' AND (w.english IS NULL OR trim(w.english) = '')"
        )
    }
    con.close()

    all_pile = set().union(*piles.values())
    cap_still_blank = sorted(piles["CAP"] & blank)
    unexpected = sorted(blank - all_pile)
    print(f"db: {db_path}")
    print(f"blank star rows now: {len(blank)}")
    print(f"\nCAP rows STILL blank: {len(cap_still_blank)} "
          f"(rebuilt copy expects 0; live control expects 148)")
    for ref, pos in cap_still_blank:
        print(f"  {ref} | {pos}")
    print(f"\nblank rows NOT in any baseline pile: {len(unexpected)} (must be 0)")
    for ref, pos in unexpected:
        print(f"  {ref} | {pos}")
    for name in ("MID", "NOCAP", "EMPTY", "CAP"):
        gone = sorted(piles[name] - blank)
        if name == "CAP":
            # On the rebuilt copy every CAP row SHOULD be gone; only list a count.
            print(f"\n{name} rows no longer blank: {len(gone)}")
        else:
            print(f"\n{name} rows no longer blank: {len(gone)} (expected 0)")
            for ref, pos in gone:
                print(f"  {ref} | {pos}")


if __name__ == "__main__":
    main()
