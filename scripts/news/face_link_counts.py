#!/usr/bin/env python3
"""face_link_counts.py — READ-ONLY. How many story-card FACES point at a Google
News wrapper vs a real (native) article link.

It builds the cards exactly the way the live feed does (reuses views_news._group
and _pick_face), then for each card's face article reports:
  - wrapper  : the face url is still a news.google.com wrapper
  - native   : the face url is already a real article link
  - of the wrapper ones, how many ALSO have a cached resolved_url (so a copy is
    instant) vs none yet (copy resolves it live on the spot).

Nothing is written. Run on PA:
  ~/.virtualenvs/bible-env/bin/python ~/bible-db/scripts/news/face_link_counts.py
"""
import os
import sqlite3
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from views_news import _group, _pick_face  # noqa: E402
from scripts.news.gnews_resolve import is_wrapper  # noqa: E402

DB = os.path.join(REPO_ROOT, "news.db")


def _has_col(conn, table, col):
    return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})"))


def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    has_event = _has_col(conn, "items", "event")
    has_resolved = _has_col(conn, "items", "resolved_url")

    cols = "id, url, title, source, published, score, ai_thread, ai_why"
    if has_event:
        cols += ", event"
    rows = conn.execute(
        f"SELECT {cols} FROM items WHERE score IS NOT NULL "
        f"ORDER BY score DESC, published DESC"
    ).fetchall()

    # cache of url -> has a cached resolved_url?
    resolved_urls = set()
    if has_resolved:
        for r in conn.execute(
            "SELECT url FROM items WHERE resolved_url IS NOT NULL AND resolved_url != ''"
        ):
            resolved_urls.add(r["url"])

    total = wrapper = native = wrap_cached = wrap_uncached = 0
    for c in _group(rows, has_event):
        arts = sorted(c["arts"], key=lambda a: a["published"] or "", reverse=True)
        newest = arts[0]["published"] if arts else ""
        face = _pick_face(arts, newest)
        url = face["url"] or ""
        total += 1
        if is_wrapper(url):
            wrapper += 1
            if url in resolved_urls:
                wrap_cached += 1
            else:
                wrap_uncached += 1
        else:
            native += 1

    print(f"total story cards : {total}")
    print(f"  native face link: {native}")
    print(f"  google wrapper  : {wrapper}")
    if has_resolved:
        print(f"      already resolved (instant copy): {wrap_cached}")
        print(f"      not yet resolved (copy does it live): {wrap_uncached}")


if __name__ == "__main__":
    main()
