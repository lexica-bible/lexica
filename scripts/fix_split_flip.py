#!/usr/bin/env python3
"""
fix_split_flip.py — repair the "LORD the" word-order flip in the LIVE words table:
a determiner (the/a/an/his/their/...) left stranded AFTER its noun by the build's
_split_compounds step, which fronted the spread-out words in Greek slot order instead
of source-phrase order (Psa 42:8 "LORD the" -> "the LORD").

WHAT IT DOES. For every flip found by scripts/audit_split_flip.find_flips (the SAME
detection the audit counts, imported here so the two can't drift), it swaps the two
slots' POSITION values so the determiner reads just before its noun — nothing else
changes. The english + Strong's stay welded to their own slots, so each word keeps its
correct number; only the reading order is corrected, to match the clean verses.text.

WHY a position swap (not an english swap): swapping english would move "the" onto the
noun's Greek number and the noun onto the article's — wrong tags. Swapping position
keeps every word with its own number and just reorders. Non-bracketed slots only; their
greek_pos is blank, so there is nothing else to move.

MATCHES THE BUILD FIX. The corrected _split_compounds fronts the spread words in
source-phrase order, i.e. the order they appear in verses.text. This fixer reorders the
flagged pair to that same order. Both therefore target verses.text, so a future full
rebuild lands the identical order. The shared gate is the audit: it must read 0 after
EITHER path. (Prove byte-identical on PA: copy the DB twice, run this fixer on one and a
corrected full rebuild on the other, then compare with scripts/compare_words.py.)

Re-runnable: detection re-checks each verse, so an already-fixed pair is skipped.

AFTER --apply, on PA, re-run (positions moved):
  python3 scripts/build_abp_surface.py bible.db --bh bh_scrape.db
  python3 scripts/build_abp_translit.py bible.db
  python3 scripts/audit_split_flip.py bible.db        # must read 0

Usage:
  python3 scripts/fix_split_flip.py bible.db            # dry run (default)
  python3 scripts/fix_split_flip.py bible.db --apply    # write the swaps
"""
import argparse
import os
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_split_flip import find_flips


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write the swaps (default = dry run)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    flips = find_flips(conn)

    by_pair = defaultdict(int)
    for f in flips:
        by_pair[(f["det"], f["noun"])] += 1

    print(f"split-flip fixer -> {args.db}")
    print(f"  flips to repair: {len(flips)}  across {len(set(f['ref'] for f in flips))} verses\n")
    for f in sorted(flips, key=lambda f: f["ref"]):
        print(f'  {f["ref"]:<14} pos {f["noun_pos"]}<->{f["det_pos"]}  '
              f'"{f["stored"]}"  ->  "{f["clean_has"]}"')

    if args.apply:
        # Each swap moves a stranded determiner ONE slot left (past its noun). In a list
        # ("the A the B the C") several articles are stranded in a row, so it converges in
        # a few passes — like one bubble-sort pass each. A swap only ever fires toward the
        # clean verses.text order, so this is monotonic (no oscillation). Loop until stable.
        cur = conn.cursor()
        total = passes = 0
        while True:
            batch = find_flips(conn)
            if not batch:
                break
            for f in batch:
                # swap the two slots' position values via a scratch position so the unique
                # (verse, position) pairing never collides mid-swap.
                cur.execute("UPDATE words SET position=-1 WHERE verse_id=? AND position=?",
                            (f["vid"], f["noun_pos"]))
                cur.execute("UPDATE words SET position=? WHERE verse_id=? AND position=?",
                            (f["noun_pos"], f["vid"], f["det_pos"]))
                cur.execute("UPDATE words SET position=? WHERE verse_id=? AND position=-1",
                            (f["det_pos"], f["vid"]))
            conn.commit()
            total += len(batch)
            passes += 1
            if passes > 50:
                print("  !! still flipped after 50 passes — stopping, investigate."); break
        print(f"\nApplied: {total} swap(s) over {passes} pass(es). Re-run audit_split_flip.py "
              f"(must read 0), then build_abp_surface.py + build_abp_translit.py (positions moved).")
    else:
        print("\nDRY RUN — nothing written. Re-run with --apply once the swaps look right.")
    conn.close()


if __name__ == "__main__":
    main()
