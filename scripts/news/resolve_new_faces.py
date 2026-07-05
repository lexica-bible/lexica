#!/usr/bin/env python3
"""resolve_new_faces.py — forward-fill face URL resolution at ingest.

Runs as the last step of the nightly news pipeline (after group_news). For each
cluster face that is a Google News wrapper, still unresolved, AND recently
ingested, resolve it once and cache the real URL in items.resolved_url — so new
stories arrive already resolved and Copy shortlist is instant, with no crawl of
the archive.

Reuses EXACTLY what's already built:
  - views_news._group / _pick_face  -> the same face the copy emits
  - gnews_resolve.resolve           -> the same batchexecute resolver
  - backfill_face_urls._resolve_with_backoff -> the same polite throttle

Pick rule (all three must hold):
  1. face url is a Google News wrapper
  2. resolved_url IS NULL (never redoes cached rows; DOES retry last night's
     failures — they're still NULL and still in the window)
  3. face row's PUBLISHED date is within the recency window (default 50h)

The window is on the article's OWN publish date, NOT first_seen (our pull time).
That matters: adding a new source freshly pulls thousands of YEARS-old articles,
all stamped with today's first_seen — gating on first_seen would forward-fill the
whole backlog. Gating on published only sweeps genuinely recent stories; an old
article we just discovered gets resolve-on-copy if it's ever copied.

The NULL guard does the real work; the window is only a floor on how far back to
look. 50h (not 26h) so a single missed/late cron night still gets swept next run.

Off the survival path: the whole run is wrapped — any error logs and exits 0,
never blocks or partial-corrupts ingest. On a resolve failure the row is left
NULL (resolve-on-copy catches it later).

  python3 scripts/news/resolve_new_faces.py [--db /path/news.db] [--since-hours 50]

PARKED (not built): a permanently-unresolvable face retries every night forever
(NULL + in-window). Harmless at low volume. If a persistent nightly-failure
pattern ever appears, add a resolve_attempts counter / resolve_failed marker to
stop after N tries. Noted, not implemented.
"""
import os
import sys
import time
import sqlite3
import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")

sys.path.insert(0, REPO_ROOT)
from views_news import _group, _pick_face                              # noqa: E402
from scripts.news.gnews_resolve import is_wrapper                      # noqa: E402
from scripts.news.backfill_face_urls import _resolve_with_backoff, BASE_SLEEP  # noqa: E402

DEFAULT_SINCE_HOURS = 50


def _arg(flag, default=None):
    if flag in sys.argv:
        try:
            return sys.argv[sys.argv.index(flag) + 1]
        except IndexError:
            pass
    return default


def _has_col(conn, table, col):
    return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})"))


def _faces(conn, has_event):
    """Every cluster's face row (same pick the live serializer uses)."""
    cols = "i.id, i.url, i.title, i.source, i.published, i.score, i.ai_thread"
    if has_event:
        cols += ", i.event"
    rows = conn.execute(
        f"SELECT {cols} FROM items i WHERE i.score IS NOT NULL "
        f"ORDER BY i.score DESC, i.published DESC").fetchall()
    faces, seen = [], set()
    for c in _group(rows, has_event):
        arts = c["arts"]
        newest = max((a["published"] or "" for a in arts), default="")
        face = _pick_face(arts, newest)
        if face["id"] not in seen:
            seen.add(face["id"])
            faces.append(face)
    return faces


def run():
    db = _arg("--db", DEFAULT_DB)
    try:
        since_hours = int(_arg("--since-hours", DEFAULT_SINCE_HOURS))
    except (TypeError, ValueError):
        since_hours = DEFAULT_SINCE_HOURS
    cutoff = (datetime.datetime.now(datetime.timezone.utc)
              - datetime.timedelta(hours=since_hours)).isoformat()

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")   # NFS-safe, not WAL (2026-07-05 corruption)
    conn.execute("PRAGMA busy_timeout=5000")
    if not _has_col(conn, "items", "resolved_url"):
        conn.close()
        print("resolve_new_faces: items.resolved_url missing — run the ALTER first. Skipping.")
        return
    has_event = _has_col(conn, "items", "event")

    faces = _faces(conn, has_event)
    todo = []
    for f in faces:
        pub = f["published"] or ""
        if not is_wrapper(f["url"]):
            continue
        if pub < cutoff:                    # article published outside the window (or undated)
            continue
        cur = conn.execute("SELECT resolved_url FROM items WHERE id = ?",
                           (f["id"],)).fetchone()
        if cur and cur["resolved_url"]:     # already cached
            continue
        todo.append(f)

    print(f"resolve_new_faces: window {since_hours}h  "
          f"faces {len(faces)}  new unresolved wrapper-faces {len(todo)}")

    ok = fail = 0
    for f in todo:
        clean = _resolve_with_backoff(f["url"])
        if clean:
            conn.execute("UPDATE items SET resolved_url = ? WHERE url = ?",
                         (clean, f["url"]))   # caches every row sharing this url
            conn.commit()
            ok += 1
        else:
            fail += 1                          # leave NULL — resolve-on-copy retries
        time.sleep(BASE_SLEEP)
    print(f"resolve_new_faces: resolved {ok}  failed {fail} (left NULL)")
    conn.close()


def main():
    # off the survival path: never let a resolution error fail the nightly run
    try:
        run()
    except Exception as e:
        print(f"resolve_new_faces: skipped on error ({e})")


if __name__ == "__main__":
    main()
