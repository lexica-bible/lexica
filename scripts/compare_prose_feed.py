#!/usr/bin/env python3
"""
compare_prose_feed.py — READ-ONLY: does live `verses.text` still equal what the pinned
feed (abp_texts/) yields through load_abp_prose today? Edition-upgrade charter §5
("live verses.text vs abp_texts prose agreement"). Opens the db mode=ro, writes no file.

Why: the step-1 census used abp_texts/ as a stand-in for the live English. This proves
(or disproves) that stand-in on the real table, verse by verse, no sampling.

Dash-neutral like verify_prose_leak.py: live went through fix_emdash ('—'), a fresh parse
emits '--'. Both sides are canonicalised to '--' before comparing, so only real wording
differences count. Every difference is printed (ref · live · feed); expected = 0.

Usage (on PA, from ~/bible-db):
  python3 scripts/compare_prose_feed.py ~/bible-db/bible.db
Exit 0 = every verse agrees; 1 = differences (listed); 2 = bad path.
"""
import os
import sqlite3
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
os.chdir(os.path.dirname(_HERE))          # load_abp_prose's ABP_DIRS are repo-relative
from load_abp_prose import ABP_DIRS, parse_file   # the production parser, not a copy


def norm(t):
    return (t or "").replace("—", "--").strip()


def main():
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        sys.exit("usage: compare_prose_feed.py <path to bible.db>  (the path is required)")
    con = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    live = {(b, c, v): norm(t) for b, c, v, t in
            con.execute("SELECT book, chapter, verse, text FROM verses")}
    feed, files = {}, 0
    for d in ABP_DIRS:
        for p in sorted(d.glob("*.txt")):
            files += 1
            for b, c, v, t in parse_file(p):
                feed[(b, c, v)] = norm(t)
    print(f"live verses: {len(live):,} · feed files: {files} · feed verses: {len(feed):,}")
    only_live = sorted(set(live) - set(feed))
    only_feed = sorted(set(feed) - set(live))
    diff = sorted(k for k in set(live) & set(feed) if live[k] != feed[k])
    print(f"only in live: {len(only_live)} · only in feed: {len(only_feed)} · "
          f"text differs: {len(diff)}")
    for k in only_live[:20]:
        print(f"  only-live  {k[0]} {k[1]}:{k[2]}")
    for k in only_feed[:20]:
        print(f"  only-feed  {k[0]} {k[1]}:{k[2]}")
    for k in diff:
        print(f"  DIFF {k[0]} {k[1]}:{k[2]}\n     live: {live[k]}\n     feed: {feed[k]}")
    ok = not (only_live or only_feed or diff)
    print("RESULT:", "AGREE — live verses.text == pinned feed through load_abp_prose"
          if ok else "DIFFER — read every line above before using abp_texts/ as the live stand-in")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
