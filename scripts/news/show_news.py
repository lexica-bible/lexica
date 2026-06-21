#!/usr/bin/env python3
"""
show_news.py — read-only peek at the scored articles in news.db.

A stopgap until the in-app tab exists: print the strongest hits from the command
line so you can judge whether the filter is reading the watch-list right. Reads
only — never changes anything.

USAGE
  python3 scripts/news/show_news.py                  # top 30, score >= 6
  python3 scripts/news/show_news.py --min 7          # only score 7+
  python3 scripts/news/show_news.py --top 50         # show more
  python3 scripts/news/show_news.py --thread ai_moralized   # one thread only
  python3 scripts/news/show_news.py --new            # only the AI's "new angle" flags
  python3 scripts/news/show_news.py --counts         # just a per-thread tally
"""
import os
import sys
import sqlite3

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")


def _arg(flag, default=None, cast=str):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            return cast(sys.argv[i + 1])
    return default


TOP = _arg("--top", 30, int)
MIN = _arg("--min", 6, int)
THREAD = _arg("--thread")
NEW_ONLY = "--new" in sys.argv
COUNTS = "--counts" in sys.argv
DB_PATH = _arg("--db", DEFAULT_DB)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

scored = conn.execute("SELECT count(*) FROM items WHERE score IS NOT NULL").fetchone()[0]
total = conn.execute("SELECT count(*) FROM items").fetchone()[0]
print(f"news.db: {total} articles, {scored} scored\n")

if COUNTS:
    rows = conn.execute(
        """SELECT ai_thread, count(*) n, round(avg(score),1) avg, max(score) hi
           FROM items WHERE score IS NOT NULL
           GROUP BY ai_thread ORDER BY hi DESC, n DESC""").fetchall()
    print(f"{'thread':30s} {'count':>6s} {'avg':>5s} {'max':>4s}")
    for r in rows:
        print(f"{(r['ai_thread'] or '?'):30s} {r['n']:>6d} {r['avg']:>5} {r['hi']:>4d}")
    sys.exit(0)

where = ["score IS NOT NULL", "score >= ?"]
args = [MIN]
if THREAD:
    where.append("ai_thread = ?")
    args.append(THREAD)
if NEW_ONLY:
    where.append("ai_new_flag = 1")

sql = (f"SELECT score, ai_thread, ai_why, title, source, published, url "
       f"FROM items WHERE {' AND '.join(where)} "
       f"ORDER BY score DESC, published DESC LIMIT {TOP}")
rows = conn.execute(sql, args).fetchall()

if not rows:
    print("nothing matched (try a lower --min, or run the scorer first).")
    sys.exit(0)

for r in rows:
    date = (r["published"] or "")[:10]
    print(f"{r['score']:2d}/10  [{r['ai_thread'] or '?'}]  {r['title']}")
    print(f"        {r['source'] or '?'}  {date}")
    if r["ai_why"]:
        print(f"        → {r['ai_why']}")
    print(f"        {r['url']}")
    print()
