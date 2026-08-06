#!/usr/bin/env python3
"""Lane-② ride instrument: name the split_merges skips and show both states.

fix_split_merges applied 208/237 on the ride copy — 29 verses skipped because
the PN-star pass changed their wording before the patch looked. This names
ALL 29 (not the 10 printed samples) and prints each verse's word cells from
LIVE (patch applied) beside the RIDE copy (pass applied instead), so every
one can be adjudicated by content.

A verse counts as APPLIED when every entry's (new_pos, new_eng) matches the
copy; otherwise it is a skip and both sides print.

Usage: python3 scripts/list_split_merge_skips.py <live-db> <ride-db>
Read-only.
"""
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXES = json.load(open(os.path.join(HERE, "split_merge_fixes.json"),
                       encoding="utf-8"))


def verse_rows(conn, book, ch, vs):
    return conn.execute(
        "SELECT w.position, w.english, w.strongs_base FROM words w "
        "JOIN verses v ON v.id = w.verse_id "
        "WHERE v.book=? AND v.chapter=? AND v.verse=? ORDER BY w.position",
        (book, ch, vs)).fetchall()


def main():
    live, ride = sys.argv[1], sys.argv[2]
    lc = sqlite3.connect("file:%s?mode=ro" % live, uri=True)
    rc = sqlite3.connect("file:%s?mode=ro" % ride, uri=True)

    skips = []
    for key, entries in FIXES.items():
        book, rest = key.split(" ", 1)
        ch, vs = (int(x) for x in rest.split(":"))
        rows = {p: (e or "") for p, e, _s in verse_rows(rc, book, ch, vs)}
        applied = all(
            (en.get("new_eng") or "") == rows.get(en["new_pos"], "\0")
            for en in entries)
        if not applied:
            skips.append((book, ch, vs, entries))

    print(f"skipped verses: {len(skips)} of {len(FIXES)}")
    for book, ch, vs, entries in skips:
        print(f"\n== {book} {ch}:{vs}  (patch wanted: "
              + " | ".join(f"pos{e['new_pos']}={e['new_eng']!r}" for e in entries)
              + ")")
        for tag, conn in (("LIVE", lc), ("RIDE", rc)):
            cells = " · ".join(f"{p}:{e!r}" for p, e, _s in
                               verse_rows(conn, book, ch, vs) if e)
            print(f"  {tag}: {cells}")


if __name__ == "__main__":
    main()
