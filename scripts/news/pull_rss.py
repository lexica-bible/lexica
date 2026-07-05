#!/usr/bin/env python3
"""
pull_rss.py — the by-outlet ingestion path (Phase 4), beside gather_news.py.

WHAT IT DOES
  - Reads the outlet feed list in sources.py.
  - Fetches + parses each feed with feedparser.
  - Applies that source's keyword gate (see sources.py): a "hard" source must
    mention a watch term (queries.gate_vocabulary()) or the item is dropped at
    ingest; a "light" source saves everything.
  - Saves each surviving article into news.db (one row, deduped by web address),
    exactly like gather_news.py, with query="rss:<source name>".
  - Touches nothing else; it never opens or changes bible.db.

New rows land with no score, so the existing incremental score_news.py +
group_news.py pick them up on the next run — no extra wiring, no --rescore.

USAGE
  python3 scripts/news/pull_rss.py            # fetch + save
  python3 scripts/news/pull_rss.py --dry-run  # fetch + per-source counts, save NOTHING
  python3 scripts/news/pull_rss.py --limit 5  # at most 5 articles per feed
  python3 scripts/news/pull_rss.py --db /path/news.db

DRY-RUN ACCEPTANCE CHECK
  Per source it reports NEW (would be inserted) vs DUPE (url already on the shelf,
  so INSERT OR IGNORE would skip it) — plus GATED-OUT on hard sources. INSERT OR
  IGNORE drops dupes silently, so the dry run is the one cheap moment to see them:
  new>0 means the feed landed; a surprising dupe count on a FIRST run flags a
  url-normalization quirk making true dupes look distinct (or vice-versa).
"""
import os
import re
import sys
import html
import time
import sqlite3
import calendar
from datetime import datetime, timezone

import feedparser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from queries import gate_vocabulary  # noqa: E402
from sources import SOURCES  # noqa: E402

# news.db lives at the repo root, beside gather_news.py's target. This file sits
# in scripts/news/, so go two levels up for the root.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")

DRY_RUN = "--dry-run" in sys.argv
LIMIT = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--limit=")), None)
if LIMIT is None and "--limit" in sys.argv:
    i = sys.argv.index("--limit")
    if i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])
DB_PATH = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--db=")), DEFAULT_DB)

# A plain browser UA, not a bot tag: some outlet firewalls (e.g. Complicit
# Clergy) return 403 to an obvious bot string but serve the feed to a browser UA.
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

# Same shelf gather_news.py builds; re-declared so a pull that runs before the
# first gather still has somewhere to land. CREATE IF NOT EXISTS = harmless.
SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id          INTEGER PRIMARY KEY,
  url         TEXT UNIQUE,
  title       TEXT,
  source      TEXT,
  published   TEXT,
  summary     TEXT,
  thread      TEXT,
  query       TEXT,
  first_seen  TEXT,
  score       INTEGER,
  ai_thread   TEXT,
  ai_why      TEXT,
  ai_new_flag INTEGER,
  status      TEXT DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS ix_items_thread ON items(thread);
CREATE INDEX IF NOT EXISTS ix_items_published ON items(published);
"""

_TAG = re.compile(r"<[^>]+>")
_TERMS = gate_vocabulary()


def clean(text):
    """Strip HTML tags + collapse whitespace from a feed blurb."""
    if not text:
        return ""
    text = _TAG.sub(" ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def iso_from_entry(e):
    """Best-effort ISO date from a feedparser entry; '' on junk."""
    st = e.get("published_parsed") or e.get("updated_parsed")
    if st:
        try:
            return datetime.fromtimestamp(calendar.timegm(st), tz=timezone.utc).isoformat()
        except Exception:
            pass
    return ""


def passes_gate(level, title, summary):
    """A 'hard' source must mention a watch term; 'light' lets everything through."""
    if level != "hard":
        return True
    blob = (title + " " + summary).lower()
    return any(term in blob for term in _TERMS)


def main():
    print(f"{'DRY RUN — ' if DRY_RUN else ''}pulling {len(SOURCES)} RSS feeds "
          f"into {DB_PATH}" + (f"  (max {LIMIT}/feed)" if LIMIT else ""))

    # Dry run never creates the file; if it already exists we only read it.
    conn = None
    have_table = False
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        have_table = bool(conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
        ).fetchone())
    if not DRY_RUN:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=DELETE")   # NFS-safe, not WAL (2026-07-05 corruption)
        conn.execute("PRAGMA busy_timeout=5000")
        conn.executescript(SCHEMA)
        have_table = True

    def url_seen(u):
        if not have_table:
            return False
        return conn.execute("SELECT 1 FROM items WHERE url=?", (u,)).fetchone() is not None

    now = datetime.now(timezone.utc).isoformat()
    seen_run = set()
    tot_new = tot_dupe = tot_gate = errors = 0

    for s in SOURCES:
        name = s["name"]
        level = s.get("gate_level", "light")
        try:
            feed = feedparser.parse(s["url"], agent=UA)
        except Exception as e:
            errors += 1
            print(f"  ERR  [{name}] {str(e)[:70]}")
            continue
        entries = feed.entries or []
        if not entries and getattr(feed, "bozo", 0):
            errors += 1
            print(f"  ERR  [{name}] parse failed: "
                  f"{str(getattr(feed, 'bozo_exception', ''))[:60]}")
            continue
        if LIMIT:
            entries = entries[:LIMIT]

        new = dupe = gate = 0
        for e in entries:
            link = (e.get("link") or "").strip()
            if not link:
                continue
            title = clean(e.get("title", ""))
            summary = clean(e.get("summary") or e.get("description") or "")
            if not passes_gate(level, title, summary):
                gate += 1
                continue
            if link in seen_run or url_seen(link):
                dupe += 1
                seen_run.add(link)
                continue
            seen_run.add(link)
            if not DRY_RUN:
                conn.execute(
                    """INSERT OR IGNORE INTO items
                       (url, title, source, published, summary, thread, query, first_seen)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (link, title, name, iso_from_entry(e), summary,
                     s.get("thread_hint", ""), f"rss:{name}", now))
            new += 1
        if conn is not None and not DRY_RUN:
            conn.commit()

        tot_new += new
        tot_dupe += dupe
        tot_gate += gate
        gatetxt = f", {gate:3d} gated-out" if level == "hard" else ""
        print(f"  OK   [{name:26s}] {new:3d} new, {dupe:3d} dupe{gatetxt}  ({level})")
        time.sleep(1)  # be polite to the feeds

    if conn is not None:
        if not DRY_RUN:
            conn.commit()
        conn.close()

    print(f"\n{'(dry run) ' if DRY_RUN else ''}{tot_new} new, "
          f"{tot_dupe} dupe (url already on shelf), {tot_gate} gated-out, "
          f"{errors} feed errors")


if __name__ == "__main__":
    main()
