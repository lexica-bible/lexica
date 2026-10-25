#!/usr/bin/env python3
"""inspect_rows.py — READ-ONLY look at the news.db rows whose headline matches some words.
Never changes anything (opens news.db read-only).

Prints, per row: id, how we pulled it (RSS / Google), outlet, date + where the date came from,
score, event label, the night we first pulled it, and the link. With --resolve it also looks up
each Google redirect's real link IN MEMORY (nothing saved) and fetches each real page's own
<link rel="canonical"> address, so two rows can be checked for "same article?" by hand.

USAGE (on PA, from ~/bible-db):
  python3 scripts/news/inspect_rows.py "catholic ai task force"
  python3 scripts/news/inspect_rows.py "catholic ai task force" --resolve
  python3 scripts/news/inspect_rows.py "death penalty" "inadmissible"    # every word must match
  --db /path/news.db
Words match anywhere in the headline or the event label, any case; every word given must appear.
"""
import os
import re
import sys
import sqlite3

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")
sys.path.insert(0, REPO_ROOT)

from scripts.news.dedupe import article_key, canonical_url, WRAPPER_MARK  # noqa: E402

_CANON = re.compile(r"<link\b[^>]*rel\s*=\s*[\"']canonical[\"'][^>]*>", re.I)
_HREF = re.compile(r"href\s*=\s*[\"']([^\"']+)[\"']", re.I)


def page_canonical(url):
    """The page's own <link rel=canonical> address, or '' (any failure)."""
    from scripts.news.pagedate import _fetch
    doc = _fetch(url) or ""
    m = _CANON.search(doc)
    if not m:
        return ""
    h = _HREF.search(m.group(0))
    return h.group(1) if h else ""


def main():
    args = sys.argv[1:]
    db = DEFAULT_DB
    if "--db" in args:
        i = args.index("--db")
        db = args[i + 1]
        del args[i:i + 2]
    resolve = "--resolve" in args
    words = [a.lower() for a in args if not a.startswith("--")]
    if not words:
        sys.exit(__doc__)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    has_event = any(r[1] == "event" for r in conn.execute("PRAGMA table_info(items)"))
    hay = "lower(COALESCE(title, '') || ' ' || COALESCE(event, ''))" if has_event else "lower(title)"
    where = " AND ".join(f"{hay} LIKE ?" for _ in words)
    rows = conn.execute(f"SELECT * FROM items WHERE {where} ORDER BY published, id",
                        [f"%{w}%" for w in words]).fetchall()
    revs = {}
    try:
        for r in conn.execute("SELECT item_id, reviewer, status FROM reviews"):
            revs.setdefault(r["item_id"], []).append(f"{r['reviewer']}={r['status']}")
    except sqlite3.Error:
        pass
    conn.close()
    print(f"{len(rows)} rows match {words}\n")
    for r in rows:
        k = r.keys()
        g = lambda c: r[c] if c in k else None          # noqa: E731
        via = "RSS" if (g("query") or "").startswith("rss:") else "Google"
        print(f"id {r['id']}  {via}  {g('source')}  score {g('score')}")
        print(f"  title     : {g('title')}")
        print(f"  published : {(g('published') or '')[:10]}  date from: {g('published_src')}  "
              f"flag: {g('date_flag')}  page date: {g('published_page')}")
        print(f"  first pull: {(g('first_seen') or '')[:16]}   query: {g('query')}")
        print(f"  label     : {g('event')}")
        print(f"  thread    : {g('ai_thread')}   reviews: {', '.join(revs.get(r['id'], [])) or '-'}")
        print(f"  url       : {g('url')}")
        print(f"  resolved  : {g('resolved_url')}")
        print(f"  match key : {article_key(r) or '(none — no real link yet)'}")
        if resolve:
            real = g("resolved_url") or ""
            if not real and WRAPPER_MARK in (g("url") or ""):
                from scripts.news.gnews_resolve import resolve as gres
                real = gres(g("url")) or ""
                print(f"  looked up : {real or '(lookup failed)'}  -> key {canonical_url(real)}")
            elif not real:
                real = g("url") or ""
            if real:
                pc = page_canonical(real)
                print(f"  page says : {pc or '(no canonical tag / fetch failed)'}"
                      + (f"  -> key {canonical_url(pc)}" if pc else ""))
        print()


if __name__ == "__main__":
    main()
