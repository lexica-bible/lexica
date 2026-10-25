#!/usr/bin/env python3
"""Same-article merge for news.db (scripts/news/dedupe.py + merge_dups.py).

Runs the REAL merge code against an in-memory sqlite copy of the items/reviews shape — not a
re-implementation. Covers:
  - canonical_url: tracking junk / www / AMP tail / trailing slash collapse; a real ?id= kept;
    a Google redirect has no key (never merged unresolved)
  - the known positive: two Google rows, different redirect links, same resolved article
    (shaped on the NewsNation "Catholic AI task force" pair) -> ONE set, page-verified row kept
  - title-only matches are NEVER merged (same outlet + same headline, different articles)
  - apply: removed row lands in items_merged, reviews move, a review clash keeps the later
    mark and saves the other, keeper blanks filled, nothing left to merge after
  - nightly mode is a no-op until items_merged exists
  - ingest skip list (merged_urls) reads items_merged, empty before it exists
"""
import io
import os
import sqlite3
import sys
from contextlib import redirect_stdout

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

from scripts.news.dedupe import canonical_url, plan_merges, merged_urls, title_key  # noqa: E402
from scripts.news import merge_dups  # noqa: E402
import views_news  # noqa: E402

G1 = "https://news.google.com/rss/articles/CBMiAAA?oc=5"
G2 = "https://news.google.com/rss/articles/CBMiBBB?oc=5"
REAL = "https://www.newsnationnow.com/business/tech/ai/catholic-ai-task-force/"


def _check(fails, label, got, want):
    if got != want:
        fails.append(f"{label}: got {got!r}, want {want!r}")


def _db():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript("""
      CREATE TABLE items (id INTEGER PRIMARY KEY, url TEXT UNIQUE, title TEXT, source TEXT,
        published TEXT, summary TEXT, thread TEXT, query TEXT, first_seen TEXT, score INTEGER,
        ai_thread TEXT, ai_why TEXT, ai_new_flag INTEGER, status TEXT DEFAULT 'new',
        event TEXT, resolved_url TEXT, published_page TEXT, published_src TEXT,
        date_flag INTEGER DEFAULT 0);
    """)
    c.executescript(views_news._REVIEWS_SCHEMA)
    return c


def _add(c, id_, url, title="Catholic AI task force announced by US bishops - NewsNation",
         source="NewsNation", resolved=None, src="google", flag=0, score=7, event="",
         query="catholic ai", summary=""):
    c.execute("INSERT INTO items (id, url, title, source, published, summary, query, first_seen,"
              " score, ai_thread, ai_why, event, resolved_url, published_src, date_flag)"
              " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (id_, url, title, source, "2026-10-21T00:00:00+00:00", summary, query,
               "2026-10-21", score, "ai_moralized", "why", event, resolved, src, flag))


def _rows(c):
    return merge_dups.load_rows(c)


def check_canonical(fails):
    base = "newsnationnow.com/business/tech/ai/catholic-ai-task-force"
    for u in (REAL,
              "http://newsnationnow.com/business/tech/ai/catholic-ai-task-force",
              REAL + "?utm_source=google&utm_medium=rss#comments",
              REAL + "amp/",
              REAL + "?amp=1",
              "https://WWW.NewsNationNow.com/business/tech/ai/catholic-ai-task-force/"):
        _check(fails, f"canonical {u}", canonical_url(u), base)
    _check(fails, "real ?id kept", canonical_url("https://x.com/story.php?id=12&utm_x=1"),
           "x.com/story.php?id=12")
    _check(fails, "different ids differ",
           canonical_url("https://x.com/a.php?id=1") == canonical_url("https://x.com/a.php?id=2"),
           False)
    _check(fails, "google redirect has no key", canonical_url(G1), "")
    _check(fails, "empty has no key", canonical_url(None), "")
    _check(fails, "title key strips outlet",
           title_key("Catholic AI task force announced - NewsNation", "NewsNation"),
           ("newsnation", "catholic ai task force announced"))


def check_known_positive_pair(fails):
    """Two redirect links, same real article -> one set, page-verified row survives."""
    c = _db()
    _add(c, 100, G1, resolved=REAL, src="google", flag=1, event="US Bishops AI Task Force")
    _add(c, 200, G2, resolved=REAL + "?utm_source=gn", src="page", flag=0,
         event="USCCB Catholic AI Task Force 2026")
    plans = plan_merges(_rows(c))
    _check(fails, "pair -> one set", len(plans), 1)
    if plans:
        _k, keep, losers = plans[0]
        _check(fails, "page-verified row kept", keep["id"], 200)
        _check(fails, "other row merged", [r["id"] for r in losers], [100])


def check_title_only_never_merges(fails):
    c = _db()
    _add(c, 1, "https://outlet.com/2026/10/weekly-roundup", title="Weekly Roundup - Outlet",
         source="Outlet")
    _add(c, 2, "https://outlet.com/2026/10/weekly-roundup-2", title="Weekly Roundup - Outlet",
         source="Outlet")
    _add(c, 3, G1, title="Weekly Roundup - Outlet", source="Outlet")      # unresolved
    rows = _rows(c)
    plans = plan_merges(rows)
    _check(fails, "title-only: no merge", len(plans), 0)
    diff, unknown = merge_dups.title_report(rows, plans)
    _check(fails, "title-only reported (unknown address)", len(unknown), 1)


def check_rss_beats_google(fails):
    c = _db()
    _add(c, 10, G1, resolved="https://www.ncregister.com/news/leo-death-penalty", src="page")
    _add(c, 20, "https://www.ncregister.com/news/leo-death-penalty?utm_source=rss",
         src="rss", query="rss:National Catholic Register", source="National Catholic Register")
    plans = plan_merges(_rows(c))
    _check(fails, "rss+google -> one set", len(plans), 1)
    if plans:
        _check(fails, "RSS row kept", plans[0][1]["id"], 20)


def check_apply(fails):
    c = _db()
    _add(c, 100, G1, resolved=REAL, src="google", flag=1, event="Old Label",
         summary="blurb from the old row")
    _add(c, 200, G2, resolved=REAL, src="page", flag=0, event="New Label", summary="")
    _add(c, 300, "https://elsewhere.com/other-story", title="Other story", source="Elsewhere")
    c.executemany("INSERT INTO reviews (item_id, reviewer, status, updated) VALUES (?,?,?,?)", [
        (100, "u1", "keep", "2026-10-22T10:00"),      # only on the removed row -> moves
        (100, "k1", "dismiss", "2026-10-23T10:00"),   # clash, later -> wins
        (200, "k1", "keep", "2026-10-22T09:00"),      # clash, earlier -> saved in backup
    ])
    c.commit()
    plans = plan_merges(_rows(c))
    removed, clashes = merge_dups.apply_plans(c, plans)
    _check(fails, "apply removed", removed, 1)
    _check(fails, "apply clashes", clashes, 1)
    ids = [r[0] for r in c.execute("SELECT id FROM items ORDER BY id")]
    _check(fails, "items left", ids, [200, 300])
    m = c.execute("SELECT id, url, merged_into, reviews_json FROM items_merged").fetchall()
    _check(fails, "backup row", [(r["id"], r["url"], r["merged_into"]) for r in m],
           [(100, G1, 200)])
    _check(fails, "clash saved", '"status": "keep"' in (m[0]["reviews_json"] or ""), True)
    rv = {(r["reviewer"]): r["status"] for r in
          c.execute("SELECT reviewer, status FROM reviews WHERE item_id = 200")}
    _check(fails, "reviews on survivor", rv, {"u1": "keep", "k1": "dismiss"})
    _check(fails, "no reviews left on removed row",
           c.execute("SELECT COUNT(*) FROM reviews WHERE item_id = 100").fetchone()[0], 0)
    keep = c.execute("SELECT event, summary FROM items WHERE id = 200").fetchone()
    _check(fails, "survivor keeps its label", keep["event"], "New Label")
    _check(fails, "blank summary filled", keep["summary"], "blurb from the old row")
    _check(fails, "nothing left to merge", len(plan_merges(_rows(c))), 0)
    _check(fails, "ingest skip list", merged_urls(c), {G1})


def check_nightly_waits(fails, tmpdir):
    path = os.path.join(tmpdir, "news_nightly_test.db")
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    c.close()
    c = _db()
    _add(c, 100, G1, resolved=REAL)
    _add(c, 200, G2, resolved=REAL)
    c.commit()
    disk = sqlite3.connect(path)
    c.backup(disk)
    disk.close()
    old = sys.argv
    try:
        sys.argv = ["merge_dups.py", "--apply", "--nightly", "--db", path]
        buf = io.StringIO()
        with redirect_stdout(buf):
            merge_dups.main()
        d = sqlite3.connect(path)
        _check(fails, "nightly before first apply: untouched",
               d.execute("SELECT COUNT(*) FROM items").fetchone()[0], 2)
        _check(fails, "nightly says it waits", "waiting for the first" in buf.getvalue(), True)
        d.execute("CREATE TABLE items_merged AS SELECT * FROM items WHERE 0")
        d.commit()
        d.close()
        with redirect_stdout(io.StringIO()):
            merge_dups.main()
        d = sqlite3.connect(path)
        _check(fails, "nightly after first apply: merged",
               d.execute("SELECT COUNT(*) FROM items").fetchone()[0], 1)
        d.close()
    finally:
        sys.argv = old
        try:
            os.remove(path)
        except OSError:
            pass


def check_merged_urls_absent(fails):
    _check(fails, "no items_merged -> empty skip list", merged_urls(_db()), set())


def main():
    import tempfile
    fails = []
    check_canonical(fails)
    check_known_positive_pair(fails)
    check_title_only_never_merges(fails)
    check_rss_beats_google(fails)
    check_apply(fails)
    check_nightly_waits(fails, tempfile.gettempdir())
    check_merged_urls_absent(fails)
    if fails:
        print("FAIL test_news_dedupe:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK test_news_dedupe")


if __name__ == "__main__":
    main()
