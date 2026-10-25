#!/usr/bin/env python3
"""merge_dups.py — merge rows in news.db that are the SAME article stored twice.

Cause: Google News gives the same article a new redirect link on a later pull, so the
url-is-unique check at ingest misses it (TODO.md, "Google repeats"); an article pulled from both
an outlet's RSS feed and Google lands twice too. Same article = same real address
(scripts/news/dedupe.py: resolved_url for Google rows, the url itself for RSS rows, cleaned up).
Title + outlet is REPORTED, never used to merge on its own.

USAGE (on PA, from ~/bible-db):
  python3 scripts/news/merge_dups.py                # report only — opens news.db read-only
  python3 scripts/news/merge_dups.py --pages        # also check same-headline pairs whose
                                                    #   addresses differ against each page's
                                                    #   own main-address tag (network, ~1-2 s
                                                    #   a page; still writes nothing)
  python3 scripts/news/merge_dups.py --apply --pages     # do the merge (copy news.db first)
  python3 scripts/news/merge_dups.py --fill-links 300    # look up + SAVE the real link for up to
                                                    #   300 Google rows scored 5+ that don't
                                                    #   have one (newest first). Saves only the
                                                    #   link — the same write the nightly step
                                                    #   makes — and merges nothing.
  python3 scripts/news/merge_dups.py --apply --nightly   # the daily.sh step (see below)
  --db /path/news.db

THE PAGE CHECK (--pages): an outlet sometimes moves an article (EWTN /world/americas/ ->
/world/us/, Crux /uncategorized/ -> /vatican/), so one article sits at two addresses. When a
page's own <link rel="canonical"> tag names ANOTHER row's address (same outlet, same headline),
the two rows merge. A tag pointing anywhere else (a homepage, a section page) is ignored, and a
page that can't be fetched merges nothing.

WHAT A MERGE DOES, per duplicate set:
  - one row survives (dedupe.keeper_rank: RSS row > page-verified date > scored > labeled >
    earliest pulled) — its link, date and headline stay.
  - its AI reading (score, thread, reason, new-angle flag, event label) is taken from the
    HIGHEST-scored row of the set (dedupe.score_rank), so a merge never pulls an article below
    the score floor. Its other empty fields (resolved_url, summary, event) are filled from the
    removed rows.
  - review marks (Keep/Dismiss) on a removed row move to the survivor. If both rows carry a
    mark from the same reviewer, the later one wins and the other is saved in the backup row.
  - each removed row is copied whole into the table items_merged (merged_into = survivor id),
    then deleted from items. items_merged is also what ingest checks, so a merged-away link that
    comes back isn't stored and scored again.

--nightly: does nothing until items_merged exists — i.e. until the first by-hand --apply has
been run after its report was checked. After that it merges each night's new duplicates (the
nightly page-date step looks up tonight's real links first), page-checking only sets that hold a
row pulled in the last 50 hours. Never fails the nightly run.
"""
import os
import sys
import json
import time
import sqlite3
import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")
sys.path.insert(0, REPO_ROOT)

from scripts.news.dedupe import (plan_merges, title_key, article_key, is_rss,   # noqa: E402
                                 canonical_url, score_rank, MERGED_TABLE, WRAPPER_MARK)

FILL_COLS = ("resolved_url", "summary", "event")
SCORE_COLS = ("score", "ai_thread", "ai_why", "ai_new_flag")
PAGE_DEADLINE = 45          # hard stop per page fetch (same as the page-date check)
NIGHTLY_HOURS = 50


def _arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def _cols(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def _has_table(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def load_rows(conn):
    """Every items row as a plain dict."""
    cur = conn.execute("SELECT * FROM items ORDER BY id")
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def _g(r, k):
    return r[k] if k in r else None


def _line(r):
    via = "RSS   " if is_rss(r) else "Google"
    src = _g(r, "published_src") or "-"
    flag = _g(r, "date_flag")
    date = (_g(r, "published") or "")[:10] or "undated"
    datenote = {"page": "page date", "google": "Google date", "rss": "feed date"}.get(src, src)
    if src == "google" and flag:
        datenote = "Google date, page check found none"
    elif src == "page" and flag:
        datenote = "page date, >30d off Google"
    sc = _g(r, "score")
    return (f"    id {r['id']:>6}  {via}  {(_g(r, 'source') or '?')[:22]:22}  {date} ({datenote})  "
            f"score {('-' if sc is None else sc)!s:>2}  label: {(_g(r, 'event') or '(none)')[:40]}\n"
            f"              {(_g(r, 'title') or '')[:100]}\n"
            f"              first pulled {(_g(r, 'first_seen') or '')[:10]}   "
            f"link: {_g(r, 'resolved_url') or _g(r, 'url') or ''}")


# ---------------------------------------------------------------- same-headline sets

def title_sets(rows):
    """Every same-outlet + same-headline set of 2+ rows (dedupe.title_key)."""
    by_title = {}
    for r in rows:
        tk = title_key(_g(r, "title"), _g(r, "source"))
        if tk[1]:
            by_title.setdefault(tk, []).append(r)
    return [g for g in by_title.values() if len(g) > 1]


def title_report(rows, key):
    """Same-headline sets the merge does NOT fully join, split into 'different addresses' (all
    known, they differ) and 'address unknown' (a Google row with no real link yet). This is the
    check on the merge key: each set here is either different articles, or a gap — read them."""
    diff, unknown = [], []
    for grp in title_sets(rows):
        keys = [key(r) for r in grp]
        if all(keys) and len(set(keys)) == 1:
            continue
        (unknown if not all(keys) else diff).append(grp)
    return diff, unknown


def _page_tag(url):
    from scripts.news.inspect_rows import page_canonical
    return page_canonical(url)


def page_aliases(sets, fetch=None, log=print, sleep=1.0):
    """The page check. For each same-headline set with 2+ different known addresses, fetch each
    member's page; when its main-address tag cleans to ANOTHER member's address, record
    address -> that address. Returns ({address: address}, {address: tag-key or ''})."""
    try:
        from scripts.news.deadline import with_deadline, TIMED_OUT
    except ImportError:
        from deadline import with_deadline, TIMED_OUT
    fetch = fetch or _page_tag
    alias, seen = {}, {}
    todo = [g for g in sets if len({article_key(r) for r in g if article_key(r)}) > 1]
    n = sum(len(g) for g in todo)
    if n:
        log(f"page check: {len(todo)} sets, up to {n} pages...")
    for grp in todo:
        addrs = {article_key(r) for r in grp if article_key(r)}
        for r in grp:
            k = article_key(r)
            if not k:
                continue
            if k not in seen:
                link = _g(r, "resolved_url") or _g(r, "url")
                got = with_deadline(fetch, link, secs=PAGE_DEADLINE)
                if sleep:
                    time.sleep(sleep)
                seen[k] = canonical_url(got) if (got and got is not TIMED_OUT) else ""
            t = seen[k]
            if t and t != k and t in addrs:
                alias[k] = t
    return alias, seen


def make_key(alias):
    """Same-article key honoring the page check: follow address -> address until it settles
    (a loop — two pages naming each other — settles on the smaller address)."""
    def key(r):
        k = article_key(r)
        if not k:
            return ""
        path = [k]
        while k in alias:
            k = alias[k]
            if k in path:
                return min(path[path.index(k):])
            path.append(k)
        return k
    return key


# ---------------------------------------------------------------- the merge

def ensure_merged_table(conn):
    """items_merged = a copy of items' columns + merged_into / merged_at / reviews_json.
    Created on the first --apply; later items columns are added as they appear."""
    if not _has_table(conn, MERGED_TABLE):
        conn.execute(f"CREATE TABLE {MERGED_TABLE} AS SELECT * FROM items WHERE 0")
    have = set(_cols(conn, MERGED_TABLE))
    for c, t in (("merged_into", "INTEGER"), ("merged_at", "TEXT"), ("reviews_json", "TEXT")):
        if c not in have:
            conn.execute(f"ALTER TABLE {MERGED_TABLE} ADD COLUMN {c} {t}")
    for c in _cols(conn, "items"):
        if c not in have:
            conn.execute(f"ALTER TABLE {MERGED_TABLE} ADD COLUMN {c}")


def carry_reading(conn, keeper_id, best_id, item_cols):
    """Give the survivor the AI reading of the set's highest-scored row (score fields, and its
    event label when it has one). Must run before that row is deleted."""
    if best_id == keeper_id:
        return
    sc = [c for c in SCORE_COLS if c in item_cols]
    if sc:
        conn.execute(f"UPDATE items SET ({', '.join(sc)}) = "
                     f"(SELECT {', '.join(sc)} FROM items WHERE id = ?) WHERE id = ?",
                     (best_id, keeper_id))
    if "event" in item_cols:
        conn.execute("UPDATE items SET event = (SELECT event FROM items WHERE id = ?) "
                     "WHERE id = ? AND (SELECT COALESCE(event, '') FROM items WHERE id = ?) != ''",
                     (best_id, keeper_id, best_id))


def merge_one(conn, keeper_id, loser_id, now, item_cols, has_reviews):
    """Fold one removed row into its survivor. Caller commits."""
    for c in FILL_COLS:
        if c in item_cols:
            conn.execute(f"UPDATE items SET {c} = (SELECT {c} FROM items WHERE id = ?) "
                         f"WHERE id = ? AND ({c} IS NULL OR {c} = '')", (loser_id, keeper_id))
    saved = []
    if has_reviews:
        for rv in conn.execute("SELECT reviewer, status, updated FROM reviews WHERE item_id = ?",
                               (loser_id,)).fetchall():
            reviewer, status, updated = rv
            mine = conn.execute("SELECT status, updated FROM reviews WHERE item_id = ? "
                                "AND reviewer = ?", (keeper_id, reviewer)).fetchone()
            if mine is None:
                conn.execute("UPDATE reviews SET item_id = ? WHERE item_id = ? AND reviewer = ?",
                             (keeper_id, loser_id, reviewer))
                continue
            if (updated or "") > (mine[1] or ""):
                saved.append({"reviewer": reviewer, "status": mine[0], "updated": mine[1],
                              "from": keeper_id})
                conn.execute("UPDATE reviews SET status = ?, updated = ? WHERE item_id = ? "
                             "AND reviewer = ?", (status, updated, keeper_id, reviewer))
            else:
                saved.append({"reviewer": reviewer, "status": status, "updated": updated,
                              "from": loser_id})
            conn.execute("DELETE FROM reviews WHERE item_id = ? AND reviewer = ?",
                         (loser_id, reviewer))
    cl = ", ".join(item_cols)
    conn.execute(f"INSERT INTO {MERGED_TABLE} ({cl}, merged_into, merged_at, reviews_json) "
                 f"SELECT {cl}, ?, ?, ? FROM items WHERE id = ?",
                 (keeper_id, now, json.dumps(saved) if saved else None, loser_id))
    conn.execute("DELETE FROM items WHERE id = ?", (loser_id,))
    return saved


def best_of(keep, losers):
    return max([keep] + losers, key=lambda r: score_rank(r, keep["id"]))


def apply_plans(conn, plans):
    """Merge every planned set in one go. Returns (rows removed, review clashes saved)."""
    ensure_merged_table(conn)
    item_cols = _cols(conn, "items")
    has_reviews = _has_table(conn, "reviews")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    removed = clashes = 0
    for _k, keep, losers in plans:
        carry_reading(conn, keep["id"], best_of(keep, losers)["id"], item_cols)
        for lo in losers:
            clashes += len(merge_one(conn, keep["id"], lo["id"], now, item_cols, has_reviews))
            removed += 1
    conn.commit()
    return removed, clashes


# ---------------------------------------------------------------- link fill

def fill_links(conn, n, log=print):
    """Look up and save the real link for up to n Google rows scored 5+ that have none, newest
    first. One at a time, saved after each, so stopping it loses nothing."""
    from scripts.news.backfill_face_urls import _resolve_with_backoff
    rows = conn.execute(
        "SELECT id, url FROM items WHERE url LIKE ? AND (resolved_url IS NULL OR resolved_url = '')"
        " AND score >= 5 ORDER BY published DESC, id DESC LIMIT ?",
        (f"%{WRAPPER_MARK}%", n)).fetchall()
    left = conn.execute(
        "SELECT COUNT(*) FROM items WHERE url LIKE ? AND (resolved_url IS NULL OR "
        "resolved_url = '') AND score >= 5", (f"%{WRAPPER_MARK}%",)).fetchone()[0]
    log(f"fill-links: {left} Google rows scored 5+ have no real link; looking up {len(rows)}")
    ok = 0
    for i, (rid, url) in enumerate(rows, 1):
        got = _resolve_with_backoff(url)
        time.sleep(1.0)
        if got:
            ok += 1
            conn.execute("UPDATE items SET resolved_url = ? WHERE url = ? "
                         "AND (resolved_url IS NULL OR resolved_url = '')", (got, url))
            conn.commit()
        if i % 25 == 0:
            log(f"  {i}/{len(rows)}  found {ok}")
    log(f"fill-links: found {ok}, not found {len(rows) - ok} (left as they were). "
        f"Still without a link: {left - ok}")


# ---------------------------------------------------------------- report

def report(rows, plans, diff, unknown, key, tags, log=print):
    n_lose = sum(len(l) for _k, _keep, l in plans)
    two_labels = sum(1 for _k, keep, l in plans
                     if len({(_g(r, "event") or "") for r in [keep] + l}) > 1)
    by_page = sum(1 for _k, keep, l in plans
                  if len({article_key(r) for r in [keep] + l}) > 1)
    lifted = sum(1 for _k, keep, l in plans if best_of(keep, l)["id"] != keep["id"])
    log(f"\n== A. SAME ARTICLE: {len(plans)} sets, {n_lose} rows to merge away — {two_labels} sets "
        f"carry 2+ different labels (= showing as separate cards); {by_page} matched by the page "
        f"check; {lifted} survivors take a higher AI score from a removed row")
    for k, keep, losers in plans:
        best = best_of(keep, losers)
        page = len({article_key(r) for r in [keep] + losers}) > 1
        log(f"\n  address: {k}" + ("   [PAGE CHECK: a page names another row's address]"
                                    if page else ""))
        log("  KEEP" + (f"   (takes AI score {best['score']} + reading from id {best['id']})"
                        if best["id"] != keep["id"] else ""))
        log(_line(keep))
        log("  MERGE INTO IT")
        for r in losers:
            log(_line(r))
        if page:
            for r in [keep] + losers:
                a = article_key(r)
                log(f"      page tag of {r['id']}: {tags.get(a) or '(none / not fetched)'}")
    log(f"\n== B1. Same outlet + same headline, DIFFERENT real addresses: {len(diff)} sets — "
        f"NOT merged. Each is either different articles, or a gap in the address clean-up.")
    for grp in diff:
        log("")
        for r in grp:
            a = article_key(r)
            log(_line(r) + f"\n              cleaned: {a}"
                + (f"\n              page tag: {tags[a] or '(none / fetch failed)'}" if a in tags else ""))
    log(f"\n== B2. Same outlet + same headline, real address UNKNOWN for at least one: "
        f"{len(unknown)} sets — NOT merged (--fill-links looks the links up)")
    for grp in unknown:
        log("")
        for r in grp:
            log(_line(r))
    g_unres = [r for r in rows if WRAPPER_MARK in (_g(r, "url") or "")
               and not _g(r, "resolved_url")]
    hi = sum(1 for r in g_unres if (_g(r, "score") or 0) >= 5)
    log(f"\n== C. Google rows with no real link yet (can't be matched by address): "
        f"{len(g_unres)} total — {hi} scored 5+, {len(g_unres) - hi} below 5 or unscored")


# ---------------------------------------------------------------- main

def run():
    db = _arg("--db", DEFAULT_DB)
    apply = "--apply" in sys.argv
    nightly = "--nightly" in sys.argv
    pages = "--pages" in sys.argv
    fill = _arg("--fill-links")
    writes = apply or nightly or fill is not None
    if writes:
        conn = sqlite3.connect(db)
        conn.execute("PRAGMA journal_mode=DELETE")   # NFS-safe, not WAL (2026-07-05 corruption)
        conn.execute("PRAGMA busy_timeout=5000")
    else:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        if fill is not None:
            fill_links(conn, int(fill))
            return
        if nightly and not _has_table(conn, MERGED_TABLE):
            print("merge_dups: skipped — waiting for the first by-hand --apply "
                  "(items_merged missing).")
            return
        rows = load_rows(conn)
        alias, tags = {}, {}
        if nightly:
            cutoff = (datetime.datetime.now(datetime.timezone.utc)
                      - datetime.timedelta(hours=NIGHTLY_HOURS)).isoformat()
            fresh = [g for g in title_sets(rows)
                     if any((_g(r, "first_seen") or "") >= cutoff for r in g)]
            alias, tags = page_aliases(fresh, log=lambda s: None)
            plans = plan_merges(rows, make_key(alias))
            removed, clashes = apply_plans(conn, plans) if plans else (0, 0)
            print(f"merge_dups: {len(plans)} duplicate sets, {removed} rows merged away"
                  f"{f', {clashes} review clashes saved' if clashes else ''}")
            return
        if pages:
            alias, tags = page_aliases(title_sets(rows))
        key = make_key(alias)
        plans = plan_merges(rows, key)
        diff, unknown = title_report(rows, key)
        print(f"{'APPLY' if apply else 'REPORT ONLY (nothing written)'} — {db}  ({len(rows)} rows)"
              f"{'  [page check ON]' if pages else '  [page check off — add --pages]'}")
        report(rows, plans, diff, unknown, key, tags)
        if not apply:
            print("\n(report only — nothing was changed)")
            return
        removed, clashes = apply_plans(conn, plans)
        left = plan_merges(load_rows(conn), key)
        kept = conn.execute(f"SELECT COUNT(*) FROM {MERGED_TABLE}").fetchone()[0]
        print(f"\nAPPLIED: {removed} rows merged away into their survivors "
              f"({clashes} review clashes saved in items_merged.reviews_json).")
        print(f"  items_merged now holds {kept} rows.  Duplicate sets left: {len(left)} (expect 0)")
    finally:
        conn.close()


def main():
    if "--nightly" in sys.argv:
        try:
            run()
        except Exception as e:                 # off the survival path
            print(f"merge_dups: skipped on error ({e})")
        return
    run()


if __name__ == "__main__":
    main()
