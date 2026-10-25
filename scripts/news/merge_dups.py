#!/usr/bin/env python3
"""merge_dups.py — merge rows in news.db that are the SAME article stored twice.

Cause: Google News gives the same article a new redirect link on a later pull, so the
url-is-unique check at ingest misses it (TODO.md, "Google repeats"). Same article = same real
address (scripts/news/dedupe.py: resolved_url for Google rows, the url itself for RSS rows,
cleaned up). Title + outlet is REPORTED, never used to merge.

USAGE (on PA, from ~/bible-db):
  python3 scripts/news/merge_dups.py                # report only — writes NOTHING
  python3 scripts/news/merge_dups.py --resolve      # also look up the real link for same-title
                                                    #   rows that don't have one yet (network;
                                                    #   still writes nothing without --apply)
  python3 scripts/news/merge_dups.py --apply        # do the merge (take a copy of news.db first)
  python3 scripts/news/merge_dups.py --apply --nightly   # the daily.sh step (see below)
  --db /path/news.db

WHAT A MERGE DOES, per duplicate set:
  - one row survives (dedupe.keeper_rank: RSS row > page-verified date > scored > labeled >
    earliest pulled). Its own values stay; only its EMPTY resolved_url / summary / event, or
    an unscored keeper's score fields, are filled from the removed row.
  - review marks (Keep/Dismiss) on the removed row move to the survivor. If both rows carry a
    mark from the same reviewer, the later one wins and the other is saved in the backup row.
  - the removed row is copied whole into the table items_merged (with merged_into = the
    survivor's id), then deleted from items. items_merged is also what ingest checks, so a
    merged-away link that comes back isn't stored and scored again.
  The survivor keeps its event label, so the article's two cards become one.

--nightly: does nothing until items_merged exists — i.e. until the first by-hand --apply has
been run after its report was checked. After that it merges each night's new duplicates (the
nightly page-date step looks up tonight's real links first). Never fails the nightly run.
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
                                 MERGED_TABLE, WRAPPER_MARK)

FILL_COLS = ("resolved_url", "summary", "event")
SCORE_COLS = ("score", "ai_thread", "ai_why", "ai_new_flag")


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
    """Every items row as a plain dict (so --resolve can add a looked-up link in memory)."""
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


def title_report(rows, plans):
    """Same outlet + same headline sets that the address match does NOT merge, split into
    'different addresses' (all known, they differ) and 'address unknown' (a Google row with no
    real link yet). This is the check on the merge key: a set here is either two different
    articles, or a clean-up gap in dedupe.canonical_url — read each one."""
    merged_with = {}
    for k, keep, losers in plans:
        for r in [keep] + losers:
            merged_with[r["id"]] = k
    by_title = {}
    for r in rows:
        tk = title_key(_g(r, "title"), _g(r, "source"))
        if tk[1]:
            by_title.setdefault(tk, []).append(r)
    diff, unknown = [], []
    for tk, grp in by_title.items():
        if len(grp) < 2:
            continue
        keys = [article_key(r) for r in grp]
        # fully explained by one merge set -> nothing to report
        if all(k for k in keys) and len(set(keys)) == 1:
            continue
        if any(not k for k in keys):
            unknown.append(grp)
        else:
            diff.append(grp)
    return diff, unknown


def do_resolve(rows, unknown_sets, apply, conn, log=print):
    """Look up the real link for every Google row in the 'address unknown' sets. Fills the row
    dicts in memory; writes resolved_url only with --apply (same write as the nightly step)."""
    from scripts.news.backfill_face_urls import _resolve_with_backoff
    todo = [r for grp in unknown_sets for r in grp
            if not _g(r, "resolved_url") and WRAPPER_MARK in (_g(r, "url") or "")]
    log(f"--resolve: looking up {len(todo)} real links (about 3-5 s each)...")
    ok = 0
    for r in todo:
        got = _resolve_with_backoff(r["url"])
        time.sleep(1.0)
        if got:
            ok += 1
            r["resolved_url"] = got
            if apply:
                conn.execute("UPDATE items SET resolved_url = ? WHERE url = ? "
                             "AND (resolved_url IS NULL OR resolved_url = '')", (got, r["url"]))
    if apply:
        conn.commit()
    log(f"--resolve: found {ok}, still unknown {len(todo) - ok}")


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


def merge_one(conn, keeper_id, loser_id, now, item_cols, has_reviews):
    """Fold one removed row into its survivor. Caller commits."""
    for c in FILL_COLS:
        if c in item_cols:
            conn.execute(f"UPDATE items SET {c} = (SELECT {c} FROM items WHERE id = ?) "
                         f"WHERE id = ? AND ({c} IS NULL OR {c} = '')", (loser_id, keeper_id))
    sc = [c for c in SCORE_COLS if c in item_cols]
    if sc:
        conn.execute(f"UPDATE items SET ({', '.join(sc)}) = "
                     f"(SELECT {', '.join(sc)} FROM items WHERE id = ?) "
                     f"WHERE id = ? AND score IS NULL", (loser_id, keeper_id))
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


def apply_plans(conn, plans):
    """Merge every planned set in one go. Returns (rows removed, review clashes saved)."""
    ensure_merged_table(conn)
    item_cols = _cols(conn, "items")
    has_reviews = _has_table(conn, "reviews")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    removed = clashes = 0
    for _k, keep, losers in plans:
        for lo in losers:
            clashes += len(merge_one(conn, keep["id"], lo["id"], now, item_cols, has_reviews))
            removed += 1
    conn.commit()
    return removed, clashes


def report(rows, plans, diff, unknown, log=print):
    n_lose = sum(len(l) for _k, _keep, l in plans)
    two_labels = sum(1 for _k, keep, l in plans
                     if len({(_g(r, "event") or "") for r in [keep] + l}) > 1)
    log(f"\n== A. SAME ARTICLE (same real address): {len(plans)} sets, {n_lose} rows to merge away"
        f" — {two_labels} of the sets carry 2+ different labels (= showing as separate cards)")
    for k, keep, losers in plans:
        log(f"\n  address: {k}")
        log("  KEEP")
        log(_line(keep))
        log("  MERGE INTO IT")
        for r in losers:
            log(_line(r))
    log(f"\n== B1. Same outlet + same headline, DIFFERENT real addresses: {len(diff)} sets — "
        f"NOT merged. Each is either two different articles, or a gap in the address clean-up "
        f"(check the two links).")
    for grp in diff:
        log("")
        for r in grp:
            log(_line(r) + f"\n              cleaned: {article_key(r)}")
    log(f"\n== B2. Same outlet + same headline, real address UNKNOWN for at least one: "
        f"{len(unknown)} sets — NOT merged (run with --resolve to look the links up)")
    for grp in unknown:
        log("")
        for r in grp:
            log(_line(r))
    g_unres = [r for r in rows if WRAPPER_MARK in (_g(r, "url") or "")
               and not _g(r, "resolved_url")]
    hi = sum(1 for r in g_unres if (_g(r, "score") or 0) >= 5)
    log(f"\n== C. Google rows with no real link yet (can't be matched by address): "
        f"{len(g_unres)} total — {hi} scored 5+, {len(g_unres) - hi} below 5 or unscored")


def run():
    db = _arg("--db", DEFAULT_DB)
    apply = "--apply" in sys.argv
    nightly = "--nightly" in sys.argv
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA journal_mode=DELETE")   # NFS-safe, not WAL (2026-07-05 corruption)
    conn.execute("PRAGMA busy_timeout=5000")
    if nightly and not _has_table(conn, MERGED_TABLE):
        print("merge_dups: skipped — waiting for the first by-hand --apply (items_merged missing).")
        conn.close()
        return
    rows = load_rows(conn)
    plans = plan_merges(rows)
    if nightly:
        removed, clashes = apply_plans(conn, plans) if plans else (0, 0)
        print(f"merge_dups: {len(plans)} duplicate sets, {removed} rows merged away"
              f"{f', {clashes} review clashes saved' if clashes else ''}")
        conn.close()
        return
    diff, unknown = title_report(rows, plans)
    if "--resolve" in sys.argv and unknown:
        do_resolve(rows, unknown, apply, conn)
        plans = plan_merges(rows)
        diff, unknown = title_report(rows, plans)
    print(f"{'APPLY' if apply else 'REPORT ONLY (nothing written)'} — {db}  ({len(rows)} rows)")
    report(rows, plans, diff, unknown)
    if not apply:
        print("\n(report only — nothing was changed)")
        conn.close()
        return
    removed, clashes = apply_plans(conn, plans)
    left = plan_merges(load_rows(conn))
    kept = conn.execute(f"SELECT COUNT(*) FROM {MERGED_TABLE}").fetchone()[0]
    print(f"\nAPPLIED: {removed} rows merged away into their survivors "
          f"({clashes} review clashes saved in items_merged.reviews_json).")
    print(f"  items_merged now holds {kept} rows.  Duplicate sets left: {len(left)} (expect 0)")
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
