#!/usr/bin/env python3
"""date_pass.py — check Google-path article dates against the article's own page.

Ruling (2026-10-24): on the Google News path, `published` is Google's discovery/crawl date,
not the article's, so every Google row's date is untrusted until checked against the page.
RSS rows are never touched — the feed's own pubDate stays authoritative for them.

Three columns on items (added by ensure_columns, additive):
  published_page  TEXT     the page's own date ('YYYY-MM-DD', or 'YYYY-MM' from a URL segment)
  published_src   TEXT     'rss' | 'page' | 'google' — where `published` came from
  date_flag       INTEGER  1 = the shown date is unverified, or the page and Google disagree by
                           more than 30 days; 0 otherwise
`published` stays the display column.

One row's outcome (decide):
  page day found     -> published = page day, published_page = it, src 'page';
                        flag 1 when it differs from Google's date by more than 30 days
  page month only    -> published_page = 'YYYY-MM', src 'page'. If Google's date is in that
                        same month, Google's exact day is kept (flag 0); otherwise published =
                        the 1st of that month and flag 1 — the card shows it with "~" because
                        the day is not known
  no page date       -> published untouched, src stays 'google', flag 1 (unverified, not "wrong").
                        Includes a page that contradicts itself (pagedate: 'conflict') and a page
                        date later than the day we pulled the article ('after-pull').
  no real link       -> nothing written; the next run tries again (a Google redirect that
                        couldn't be resolved tonight is a Google-side failure, not a finding)
  timed out          -> nothing written; the next run tries again (a network step that ran past
                        its hard stop — see RESOLVE_DEADLINE / PAGE_DEADLINE)

Candidates = Google-path rows, score >= 5 (the ones that can reach a card), never checked
(src 'google' and flag 0, no published_page), first pulled since `since`. A row that has been
checked once is never fetched again.

Shared by the nightly face-fill job (scripts/news/resolve_new_faces.py, recent pulls only) and
the one-shot backfill (scripts/backfill_page_dates.py, last 60 days, dry-run first).
"""
import time
import datetime
import threading

try:
    from pagedate import page_date_detail            # run from scripts/news/
except ImportError:
    from scripts.news.pagedate import page_date_detail

MIN_SCORE = 5
DISAGREE_DAYS = 30
NEW_COLS = ("published_page", "published_src", "date_flag")

# Hard wall-clock stops per network step. Needed because the Google-redirect library on PA
# (googlenewsdecoder 0.1.7) takes no timeout and makes requests calls with NONE — one silent
# connection hung the first full backfill dry run for 1h45m (2026-10-25). The page fetch has its
# own 10s socket limit, but nothing covers a stalled name lookup, so it gets a stop too. A step
# that runs past its stop is abandoned (left running in the background, harmless) and the row is
# skipped untouched, to be tried again next run.
RESOLVE_DEADLINE = 90       # the lookup retries twice with 5s + 15s waits of its own
PAGE_DEADLINE = 45
TIMED_OUT = object()


def with_deadline(fn, *args, secs):
    """fn(*args), or TIMED_OUT if it hasn't returned within `secs` seconds. An exception
    inside fn counts as None (both callers already treat None as 'nothing found')."""
    box = {}

    def run():
        try:
            box["v"] = fn(*args)
        except Exception:
            box["v"] = None

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(secs)
    return TIMED_OUT if t.is_alive() else box.get("v")


def has_columns(conn):
    have = {r[1] for r in conn.execute("PRAGMA table_info(items)")}
    return all(c in have for c in NEW_COLS)


def ensure_columns(conn):
    """Add the three columns if missing, and stamp published_src on any row that has none
    ('rss' for rss:* pulls, 'google' otherwise). Running it again only stamps new rows."""
    have = {r[1] for r in conn.execute("PRAGMA table_info(items)")}
    if "published_page" not in have:
        conn.execute("ALTER TABLE items ADD COLUMN published_page TEXT")
    if "published_src" not in have:
        conn.execute("ALTER TABLE items ADD COLUMN published_src TEXT")
    if "date_flag" not in have:
        conn.execute("ALTER TABLE items ADD COLUMN date_flag INTEGER DEFAULT 0")
    conn.execute("UPDATE items SET published_src = CASE WHEN query LIKE 'rss:%' "
                 "THEN 'rss' ELSE 'google' END WHERE published_src IS NULL")
    conn.execute("UPDATE items SET date_flag = 0 WHERE date_flag IS NULL")
    conn.commit()


def candidates(conn, since):
    """Unchecked Google-path rows scored >= 5, first pulled on/after `since` (ISO string).
    Works before the columns exist (then every Google row counts as unchecked) so a dry run
    never needs to change the database."""
    where = ["score IS NOT NULL", "score >= ?",
             "(query IS NULL OR query NOT LIKE 'rss:%')", "first_seen >= ?"]
    if has_columns(conn):
        where += ["COALESCE(published_src, 'google') = 'google'",
                  "COALESCE(date_flag, 0) = 0", "published_page IS NULL"]
    have = {r[1] for r in conn.execute("PRAGMA table_info(items)")}
    rcol = "resolved_url" if "resolved_url" in have else "NULL AS resolved_url"
    return conn.execute(
        f"SELECT id, url, {rcol}, published, first_seen, source, score, title FROM items "
        f"WHERE {' AND '.join(where)} ORDER BY id", (MIN_SCORE, since)).fetchall()


def _days_apart(a, b):
    """Whole days between two 'YYYY-MM-DD' strings, or None if either is unreadable."""
    try:
        return abs((datetime.date.fromisoformat(a[:10])
                    - datetime.date.fromisoformat(b[:10])).days)
    except (TypeError, ValueError):
        return None


def decide(google_published, page):
    """The write for one row, given Google's stored `published` and the page's date (or None).
    Returns a dict of the columns to set, plus 'delta' (days, or None) for the report."""
    g = (google_published or "")[:10]
    if not page:
        return {"published_src": "google", "date_flag": 1, "delta": None}
    if len(page) == 10:                                   # a full day off the page
        delta = _days_apart(g, page) if g else None
        return {"published": page + "T00:00:00+00:00", "published_page": page,
                "published_src": "page",
                "date_flag": 1 if (delta is not None and delta > DISAGREE_DAYS) else 0,
                "delta": delta}
    # month only ('YYYY-MM', from a /YYYY/MM/ URL segment)
    if g[:7] == page:                                     # Google's day sits inside that month
        return {"published_page": page, "published_src": "page", "date_flag": 0, "delta": 0}
    first = page + "-01"
    return {"published": first + "T00:00:00+00:00", "published_page": page,
            "published_src": "page", "date_flag": 1,
            "delta": _days_apart(g, first) if g else None}


def run_pass(conn, since, apply, resolve=None, sleep=1.0, limit=None, log=print):
    """Check every candidate row. apply=False writes NOTHING (not even a resolved link) and
    just reports. `resolve` turns a Google redirect into the real link (None on failure);
    `sleep` seconds pass after every network request (1.0 = the ruled 1 req/s).
    Returns a tally dict."""
    if apply:
        ensure_columns(conn)
    rows = candidates(conn, since)
    if limit:
        rows = rows[:limit]
    log(f"  checking {len(rows)} rows")
    tally = {"rows": len(rows), "page": 0, "page_flagged": 0, "month_only": 0,
             "no_page_date": 0, "no_link": 0, "timed_out": 0}
    seen = {}                                   # real link -> (date, how), one fetch per link
    for r in rows:
        link = r["resolved_url"] or ""
        if not link and "news.google.com/" not in (r["url"] or ""):
            link = r["url"] or ""               # already a direct article link
        if not link and resolve is not None:
            got = with_deadline(resolve, r["url"], secs=RESOLVE_DEADLINE)
            time.sleep(sleep)
            if got is TIMED_OUT:
                tally["timed_out"] += 1
                log(f"  {r['id']:>6}  google {(r['published'] or '')[:10]:10}  page {'-':10}  "
                    f"delta {'-':>5}  SKIP link lookup timed out ({RESOLVE_DEADLINE}s) (retried next run)")
                continue
            link = got or ""
            if link and apply:
                conn.execute("UPDATE items SET resolved_url = ? WHERE url = ? "
                             "AND (resolved_url IS NULL OR resolved_url = '')", (link, r["url"]))
        if not link:
            tally["no_link"] += 1
            log(f"  {r['id']:>6}  google {(r['published'] or '')[:10]:10}  "
                f"page {'-':10}  delta {'-':>5}  SKIP no real link (retried next run)")
            continue
        if link in seen:
            page, how = seen[link]
        else:
            got = with_deadline(page_date_detail, link, secs=PAGE_DEADLINE)
            time.sleep(sleep)
            if got is TIMED_OUT:
                # a hang past every socket limit is a stuck connection, not a finding about the
                # page: write nothing, the row stays unchecked and is tried again next run
                tally["timed_out"] += 1
                log(f"  {r['id']:>6}  google {(r['published'] or '')[:10]:10}  page {'-':10}  "
                    f"delta {'-':>5}  SKIP page fetch timed out ({PAGE_DEADLINE}s) (retried next run)")
                log(f"          {link}")
                continue
            page, how = got
            seen[link] = (page, how)
        # A page date AFTER the day we first pulled the article is impossible — the page handed
        # us some other date. Treat it as no page date (unverified), never write it. +1 day of
        # slack for time zones. (nssmag 18052, 2026-10-25: "2026-10-17" on a September pull.)
        pulled = (r["first_seen"] or "")[:10]
        if page and len(page) == 10 and pulled and _days_apart(page, pulled) is not None \
                and page > pulled and _days_apart(page, pulled) > 1:
            page, how = None, "after-pull"
        w = decide(r["published"], page)
        if not page:
            tally["no_page_date"] += 1
            action = "flag unverified (keep Google date)"
        elif len(page) == 7:
            tally["month_only"] += 1
            action = (f"month only -> {'keep Google day' if 'published' not in w else w['published'][:10]}"
                      f"{' FLAG' if w['date_flag'] else ''}")
        else:
            tally["page"] += 1
            tally["page_flagged"] += w["date_flag"]
            action = f"set {page}{' FLAG >30d' if w['date_flag'] else ''}"
        d = w["delta"]
        log(f"  {r['id']:>6}  google {(r['published'] or '')[:10]:10}  page {(page or '-'):10}  "
            f"delta {('-' if d is None else d):>5}  [{how or '-'}] {action}")
        log(f"          {link}")             # the page checked — so any row can be opened by hand
        if apply:
            sets = {k: v for k, v in w.items() if k != "delta"}
            conn.execute(f"UPDATE items SET {', '.join(k + ' = ?' for k in sets)} WHERE id = ?",
                         (*sets.values(), r["id"]))
            conn.commit()
    if apply:
        conn.commit()
    return tally
