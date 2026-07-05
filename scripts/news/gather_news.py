#!/usr/bin/env python3
"""
gather_news.py — pull the watch-list searches into news.db.

WHAT IT DOES
  - Reads the search list in queries.py (the 10 threads).
  - Runs each search against Google News, which returns a feed for ANY query.
  - Saves each article into news.db (its own file, like notes.db/esv.db — kept out
    of bible.db and out of git). One row per article, deduped by its web address.
  - Touches nothing else. It never opens or changes bible.db.

The AI scoring + the review tab are SEPARATE steps. This file just fills the
shelf with raw articles so we can eyeball what the searches actually surface
before spending a cent on AI.

USAGE
  python3 scripts/news/gather_news.py            # fetch + save
  python3 scripts/news/gather_news.py --dry-run  # fetch + report, save NOTHING
  python3 scripts/news/gather_news.py --limit 5  # at most 5 articles per search
  python3 scripts/news/gather_news.py --db /path/news.db

Built with Python's own tools only — no extra packages to install on PA.
"""
import os
import re
import sys
import html
import time
import sqlite3
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from queries import all_searches  # noqa: E402

# news.db lives at the repo root, beside notes.db/esv.db/study.db (all gitignored,
# PA-only). This file sits in scripts/news/, so go two levels up for the root.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")

DRY_RUN = "--dry-run" in sys.argv
LIMIT = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--limit=")), None)
if LIMIT is None and "--limit" in sys.argv:
    i = sys.argv.index("--limit")
    if i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])
DB_PATH = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--db=")), DEFAULT_DB)

GOOGLE_NEWS = "https://news.google.com/rss/search"
UA = "Mozilla/5.0 (compatible; LexicaNewsWatch/1.0; +https://www.lexica.bible)"

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id          INTEGER PRIMARY KEY,
  url         TEXT UNIQUE,        -- the article link (dedupe key)
  title       TEXT,
  source      TEXT,              -- publisher name, e.g. "Reuters"
  published   TEXT,              -- article date, ISO 8601
  summary     TEXT,              -- short blurb, HTML stripped
  thread      TEXT,              -- which watch-list thread's search found it
  query       TEXT,              -- the exact search string that found it
  first_seen  TEXT,              -- when WE first pulled it (ISO 8601)
  -- filled later by the AI scorer (step 2); empty for now:
  score       INTEGER,           -- 0-10 relevance to the worldview
  ai_thread   TEXT,              -- thread the AI assigns (may differ)
  ai_why      TEXT,              -- one-line reason
  ai_new_flag INTEGER,           -- 1 = AI thinks it's a new angle, not on our list
  -- review state set in the tab (step 3):
  status      TEXT DEFAULT 'new' -- new / keep / dismiss
);
CREATE INDEX IF NOT EXISTS ix_items_thread ON items(thread);
CREATE INDEX IF NOT EXISTS ix_items_published ON items(published);
"""

_TAG = re.compile(r"<[^>]+>")


def clean(text):
    """Strip HTML tags + collapse whitespace from a feed blurb."""
    if not text:
        return ""
    text = _TAG.sub(" ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def iso(pubdate):
    """Turn an RSS date string into plain ISO; fall back to empty on junk."""
    if not pubdate:
        return ""
    try:
        dt = parsedate_to_datetime(pubdate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return ""


def fetch(search):
    """Fetch one search's feed and return a list of article dicts."""
    params = {"q": search, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    url = GOOGLE_NEWS + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    root = ET.fromstring(raw)
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not link:
            continue
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None else ""
        items.append({
            "title": clean(title),
            "url": link,
            "source": source,
            "published": iso(it.findtext("pubDate")),
            "summary": clean(it.findtext("description")),
        })
    return items


def main():
    searches = all_searches()
    print(f"{'DRY RUN — ' if DRY_RUN else ''}gathering {len(searches)} searches "
          f"into {DB_PATH}" + (f"  (max {LIMIT}/search)" if LIMIT else ""))

    conn = None
    if not DRY_RUN:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=DELETE")   # NFS-safe, not WAL (2026-07-05 corruption)
        conn.execute("PRAGMA busy_timeout=5000")
        conn.executescript(SCHEMA)

    now = datetime.now(timezone.utc).isoformat()
    total_seen = 0
    total_new = 0
    errors = 0

    for thread, search in searches:
        try:
            articles = fetch(search)
        except Exception as e:
            errors += 1
            print(f"  ERR  [{thread}] {search!r}: {str(e)[:70]}")
            continue
        if LIMIT:
            articles = articles[:LIMIT]
        new_here = 0
        for a in articles:
            total_seen += 1
            if DRY_RUN:
                continue
            cur = conn.execute(
                """INSERT OR IGNORE INTO items
                   (url, title, source, published, summary, thread, query, first_seen)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (a["url"], a["title"], a["source"], a["published"],
                 a["summary"], thread, search, now))
            if cur.rowcount:
                new_here += 1
        total_new += new_here
        tag = f"+{new_here} new" if not DRY_RUN else f"{len(articles)} found"
        print(f"  OK   [{thread:26s}] {tag:12s} {search!r}")
        time.sleep(1)  # be polite to the feed

    if conn:
        conn.commit()
        conn.close()

    print(f"\n{'(dry run) ' if DRY_RUN else ''}saw {total_seen} articles, "
          f"{total_new} new, {errors} search errors")


if __name__ == "__main__":
    main()
