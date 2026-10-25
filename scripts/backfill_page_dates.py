#!/usr/bin/env python3
"""backfill_page_dates.py — one-shot: check recent Google-path article dates against the
article's own page (rule + columns: scripts/news/date_pass.py).

Covers Google-path rows scored >= 5 and first pulled in the last 60 days that have never
been checked. 1 request per second (resolving a Google redirect and fetching a page each
count as one). The nightly face-fill job keeps new pulls checked after this has run once.

Run on PA, from ~/bible-db:
  DRY RUN (default — writes NOTHING, not even a resolved link; still fetches the pages):
      ~/.virtualenvs/bible-env/bin/python scripts/backfill_page_dates.py
      ... --limit 25          only the first 25 rows (a quick look)
  WRITE (only after the dry run has been pasted and approved):
      ~/.virtualenvs/bible-env/bin/python scripts/backfill_page_dates.py --apply
  Options: --db PATH (default ~/bible-db/news.db), --days N (default 60)

Each line: id, Google's date, the page's date, gap in days, where the page date came from
[jsonld | meta | time | url], and what --apply would write. Safe to stop and re-run: a row
that has been checked is skipped next time.
"""
import os
import sys
import sqlite3
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.news.date_pass import run_pass                        # noqa: E402
from scripts.news.backfill_face_urls import _resolve_with_backoff  # noqa: E402


def _arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def main():
    # write each row as soon as it's checked (not in hidden batches) so a long run's progress is
    # visible with `tail` / `grep -c` while it's going
    sys.stdout.reconfigure(line_buffering=True)
    apply = "--apply" in sys.argv
    db = _arg("--db", os.path.join(ROOT, "news.db"))
    days = int(_arg("--days", 60))
    limit = int(_arg("--limit", 0)) or None
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()

    if apply:
        conn = sqlite3.connect(db)
        conn.execute("PRAGMA journal_mode=DELETE")   # NFS-safe, never WAL (2026-07-05)
        conn.execute("PRAGMA busy_timeout=5000")
    else:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)   # dry run: read-only open
    conn.row_factory = sqlite3.Row

    print(f"{'APPLY' if apply else 'DRY RUN (writes nothing)'} — Google-path rows, score >= 5, "
          f"first pulled since {since}{f', first {limit}' if limit else ''}")
    print(f"  {'id':>6}  {'google':17}  {'page':15}  {'delta':>11}  [source] action")
    t = run_pass(conn, since, apply=apply, resolve=_resolve_with_backoff, sleep=1.0, limit=limit)
    conn.close()
    print(f"\n{'wrote' if apply else 'would write'}: {t['rows']} rows checked — "
          f"page date {t['page']} ({t['page_flagged']} more than 30 days off Google), "
          f"month-only {t['month_only']}, no page date {t['no_page_date']} (flag unverified), "
          f"no real link {t['no_link']} (skipped, retried next run), "
          f"timed out {t['timed_out']} (skipped, retried next run)")


if __name__ == "__main__":
    main()
