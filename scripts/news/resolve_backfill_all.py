#!/usr/bin/env python3
"""resolve_backfill_all.py — one-time parallel backfill of EVERY unresolved
Google News wrapper into items.resolved_url, so Copy shortlist is cache-hit
instant even for big year-spanning shortlists. Resolve-on-copy stays as the
straggler net for anything this misses.

ALL wrapper rows, not just faces: face selection shifts as clusters re-split, so
we resolve every unique wrapper — whichever row becomes a face later is already
cached. Deduped to DISTINCT url (collapses the ~7,200 rows to unique articles);
each write caches every row sharing that url.

Shape:
  - Workers resolve CONCURRENTLY (default 8, --workers N) via gnews_resolve.resolve
    (network-bound, so threads help). Reuses the built resolver — no new logic.
  - Writes are SERIALIZED: only the main thread touches SQLite. Workers hand back
    (url, clean|None); the main thread batches UPDATEs and commits every 50, so a
    crash loses at most a chunk and there's no writer collision.
  - Resumable: targets resolved_url IS NULL. Kill/restart re-sweeps only what's
    left; a second run catches 429 stragglers.
  - Fail soft per URL: a failure leaves NULL, never raises, never stalls the pool.
  - Progress every 100: resolved / failed / remaining.
  - Chunked for the nightly cron: --limit caps how many URLs one run resolves, so
    the archive drains in nightly passes UNDER Google's ~1,300-call clamp point.
  - Stop-on-clamp: after --fail-abort failures in a row, assume we're rate-limited,
    stop dispatching, flush, and exit clean. One success resets the counter.

  python3 scripts/news/resolve_backfill_all.py \
      [--db PATH] [--limit 1000] [--workers 3] [--sleep 1.0] [--fail-abort 50]

PARKED (as before): a permanently-unresolvable wrapper stays NULL and gets
re-tried every run. Add a resolve_attempts marker only if that ever bites.
"""
import os
import sys
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")

sys.path.insert(0, REPO_ROOT)
from scripts.news.gnews_resolve import resolve, is_wrapper       # noqa: E402
from scripts.news.backfill_face_urls import _resolve_with_backoff  # noqa: E402

COMMIT_EVERY = 50
PROGRESS_EVERY = 100


def _arg(flag, default=None):
    if flag in sys.argv:
        try:
            return sys.argv[sys.argv.index(flag) + 1]
        except IndexError:
            pass
    return default


def _has_col(conn, table, col):
    return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})"))


def main():
    db = _arg("--db", DEFAULT_DB)
    workers = int(_arg("--workers", 3))
    sleep = float(_arg("--sleep", 1.0))
    limit = int(_arg("--limit", 1000))
    fail_abort = int(_arg("--fail-abort", 50))

    conn = sqlite3.connect(db, timeout=30)
    conn.row_factory = sqlite3.Row
    # DELETE (plain rollback journal), NOT WAL: news.db is on PA's NFS home, where
    # WAL's shared-memory sidecar + mmap aren't reliable and corrupted the file mid
    # fold-back (2026-07-05). busy_timeout waits-and-retries when the live site reads.
    try:
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA busy_timeout=5000")
    except sqlite3.Error:
        pass

    if not _has_col(conn, "items", "resolved_url"):
        conn.close()
        sys.exit("items.resolved_url missing — run the ALTER first, then re-run.")

    # how many are left overall, then take just this run's chunk
    remaining_all = conn.execute(
        "SELECT COUNT(*) FROM (SELECT DISTINCT url FROM items "
        "WHERE url LIKE '%news.google.com/rss/articles/%' AND resolved_url IS NULL)"
    ).fetchone()[0]
    urls = [r["url"] for r in conn.execute(
        "SELECT DISTINCT url FROM items "
        "WHERE url LIKE '%news.google.com/rss/articles/%' AND resolved_url IS NULL "
        "LIMIT ?", (limit,))]
    total = len(urls)
    print(f"unresolved wrappers: {remaining_all} total, taking {total} this run  "
          f"workers: {workers}  sleep: {sleep}s  fail-abort: {fail_abort}")
    if not total:
        print("nothing to do — archive fully resolved.")
        conn.close()
        return

    def work(u):
        # pace each dispatch, then resolve with the shared per-URL 429 backoff.
        # never raises — returns (url, clean-or-None)
        try:
            if sleep:
                time.sleep(sleep)
            return u, _resolve_with_backoff(u)
        except Exception:
            return u, None

    ok = fail = 0
    consec = 0            # failures in a row -> clamp detector
    aborted = False
    batch = []

    def flush():
        if batch:
            conn.executemany(
                "UPDATE items SET resolved_url = ? WHERE url = ? "
                "AND resolved_url IS NULL", batch)
            conn.commit()
            batch.clear()

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, u) for u in urls]
        for i, fut in enumerate(as_completed(futs), 1):
            u, clean = fut.result()
            if clean:
                batch.append((clean, u))
                ok += 1
                consec = 0
            else:
                fail += 1
                consec += 1
            if len(batch) >= COMMIT_EVERY:
                flush()
            if i % PROGRESS_EVERY == 0:
                print(f"  {i}/{total}  resolved {ok}  failed {fail}  "
                      f"remaining {total - i}", flush=True)
            if consec >= fail_abort:
                # sustained failures — almost certainly Google's rate clamp. Stop
                # dispatching (cancel the not-yet-started ones), flush, bail clean.
                aborted = True
                for f in futs:
                    f.cancel()
                break
    flush()

    left = remaining_all - ok
    if aborted:
        print(f"aborted: sustained failures, likely rate-limited — "
              f"{ok} resolved, {left} remaining. Resumes next run.")
    else:
        print(f"done this chunk. resolved {ok}  failed {fail}  "
              f"{left} remaining across the archive (left NULL — next run sweeps, "
              f"or resolve-on-copy catches them)")
    conn.close()


if __name__ == "__main__":
    main()
