#!/usr/bin/env python3
"""Lane-② ride instrument: size the display-order punctuation class.

The 4 adjudicated regressions (Act 4:36 · Act 6:8 · Act 19:24 · Luk 23:13)
share one shape: inside a bracket, a chip that is NOT display-last carries a
trailing comma/semicolon while the display-last chip carries none — so the
rendered text reads "And, Joses". This scans EVERY bracket in the copy for
that shape (display order = greek_pos ascending, the reader's rule) and
prints all members.

A colon/period/question mark mid-bracket can be legitimate clause punctuation;
the comma/semicolon-on-connector shape is the regression class. Both are
listed, tagged, so nothing is silently capped.

Usage: python3 scripts/scan_bracket_punct_order.py <db>
Read-only.
"""
import re
import sqlite3
import sys

TRAIL = re.compile(r"[,;]$")


def main():
    db = sys.argv[1]
    conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    cur = conn.execute(
        "SELECT v.book, v.chapter, v.verse, w.verse_id, w.bracket_id,"
        " w.position, w.english, w.greek_pos FROM words w"
        " JOIN verses v ON v.id = w.verse_id WHERE w.bracket_id IS NOT NULL"
        " ORDER BY w.verse_id, w.bracket_id, w.position")
    groups = {}
    for bk, ch, vs, vid, bid, pos, eng, gp in cur:
        groups.setdefault((vid, bid), []).append((bk, ch, vs, pos, eng, gp))
    conn.close()

    hits = 0
    for (vid, bid), rows in groups.items():
        disp = sorted(rows, key=lambda r: r[5] if r[5] is not None else 999)
        last = disp[-1]
        for r in disp[:-1]:
            if r[4] and TRAIL.search(r[4].strip()) and last[4] and \
                    not re.search(r"[,;:.!?]$", last[4].strip()):
                hits += 1
                bk, ch, vs = r[0], r[1], r[2]
                print("  %s %d:%d bracket %s: %r displays before %r"
                      % (bk, ch, vs, bid, r[4], last[4]))
    print("\ntotal mid-bracket trailing-comma members: %d" % hits)


if __name__ == "__main__":
    main()
