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
    # Real pairs from the 2026-10-25 PA report, section B1 — each must now be ONE key.
    same = [
        ("https://www.msn.com/en-us/news/insight/pope-leo-xiv-to-unveil/gm-GM66ED0EE4"
         "?gemSnapshotKey=GM66ED0EE4-snapshot-1&uxmode=ruby",
         "https://www.msn.com/en-us/news/insight/pope-leo-xiv-to-unveil/gm-GM66ED0EE4"
         "?gemSnapshotKey=GM66ED0EE4-snapshot-1"),
        ("https://www.msn.com/en-us/tv/celebrity/usha-vance-therapy-didnt-work/ar-AA25Dyd0",
         "https://www.msn.com/en-us/tv/celebrity/usha-vance-therapy-didn-t-work/ar-AA25Dyd0"
         "?apiversion=v2&noservercache=1&wcseo=1"),
        ("https://www.cnn.com/2026/05/08/politics/ufo-files-pentagon-release-aliens",
         "https://edition.cnn.com/2026/05/08/politics/ufo-files-pentagon-release-aliens"),
        ("https://www.bbc.com/news/articles/c4g2rpn3p9ro",
         "https://www.bbc.co.uk/news/articles/c4g2rpn3p9ro"),
        ("https://www.philstar.com/opinion/2026/06/04/2532617/magnifica-humanitas",
         "https://qa.philstar.com/opinion/2026/06/04/2532617/magnifica-humanitas"),
        ("https://thehill.com/homenews/house/5880943-house-gop-ufo",
         "https://thehill.com/homenews/house/5880943-house-gop-ufo"
         "?amp_gsa=1&amp_js_v=a9&usqp=mq331AQIUAKwASCAAgM%3D"),
        ("https://www.aciafrica.org/index.php/amp/news/22579/catholic-church-leaders",
         "https://www.aciafrica.org/news/22579/catholic-church-leaders"),
        ("https://indiatribune.com/public/index.php/false-charges-to-mob-attacks",
         "https://indiatribune.com/public/false-charges-to-mob-attacks"),
        ("https://spzh.eu/en/news/83531-fanar-poisk-jedinstva",
         "https://spzh.eu/en/news/83531-fanar-poisk-jedinstva.html"),
        ("https://thelettersfromleo.com/p/dialogue-is-a-way-of-life?action=share",
         "https://thelettersfromleo.com/p/dialogue-is-a-way-of-life"),
    ]
    for a, b in same:
        _check(fails, f"same key: {a}", canonical_url(a), canonical_url(b))
    # ...and real different-article pairs from the same report must stay apart.
    apart = [
        ("https://pillarcatholic.com/p/the-friday-pillar-post-june-26-2026",
         "https://pillarcatholic.com/p/the-friday-pillar-post-july-3-2026"),
        ("https://www.lifesitenews.com/episodes/pagan-aztec-war-dance",
         "https://www.lifesitenews.com/news/pagan-aztec-war-dance"),
        ("https://www.msn.com/en-us/news/insight/pope-to-unveil/gm-GMB84A8CA2",
         "https://www.msn.com/en-us/news/insight/pope-to-unveil/gm-GM0926245D"),
        ("https://www.lifesitenews.com/?p=1176239&post_type=acf-field",
         "https://www.lifesitenews.com/?p=1176227&post_type=acf-field"),
        ("https://x.com/story.php?action=view&id=1", "https://x.com/story.php?id=1"),
        ("https://x.com/index.php", "https://x.com/"),
    ]
    for a, b in apart:
        _check(fails, f"apart: {a}", canonical_url(a) == canonical_url(b), False)
    _check(fails, "title key keeps a dated issue",
           title_key("The Friday Pillar Post - June 26, 2026", "The Pillar")
           == title_key("The Friday Pillar Post - July 3, 2026", "The Pillar"), False)
    _check(fails, "title key: feed name = Google name",
           title_key("Pope calls for peace", "EWTN News (CNA)")
           == title_key("Pope calls for peace - ewtnnews.com", "ewtnnews.com"), True)


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
    diff, unknown = merge_dups.title_report(rows, merge_dups.make_key({}))
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


def check_score_carried(fails):
    """The survivor (RSS copy, scored 3) takes the Google copy's 7 + its reasoning + label, so
    the article doesn't drop out of the 5+ Inbox (the 2026-10-25 Vatican News death-penalty
    case: 25161 RSS 3 / 25107 Google 7)."""
    c = _db()
    vn = "https://www.vaticannews.va/en/pope/news/2026-10/pope-leo-death-penalty.html"
    _add(c, 25161, vn, title="Pope Leo XIV rejects death penalty", source="Vatican News",
         src="rss", query="rss:Vatican News", score=3, event="")
    _add(c, 25107, G1, resolved=vn, title="Pope Leo XIV rejects death penalty - Vatican News",
         source="Vatican News", src="page", score=7, event="Pope Leo Death Penalty Statement")
    c.execute("UPDATE items SET ai_why = 'google reason' WHERE id = 25107")
    c.commit()
    plans = plan_merges(_rows(c))
    _check(fails, "carry: one set, RSS kept", [(p[1]["id"]) for p in plans], [25161])
    merge_dups.apply_plans(c, plans)
    r = c.execute("SELECT id, url, score, ai_why, event FROM items").fetchall()
    _check(fails, "carry: survivor row",
           [(x["id"], x["url"], x["score"], x["ai_why"], x["event"]) for x in r],
           [(25161, vn, 7, "google reason", "Pope Leo Death Penalty Statement")])


def check_page_check(fails):
    """An outlet moved an article: two RSS rows, two addresses, same headline. The page's own
    main-address tag names the other row -> merge. A tag pointing elsewhere (homepage) or no
    tag -> no merge."""
    a = "https://www.ewtnnews.com/world/americas/u-s-bishops-demand-justice"
    b = "https://www.ewtnnews.com/world/us/u-s-bishops-demand-justice"

    def rows():
        c = _db()
        for id_, u in ((11374, a), (11566, b)):
            _add(c, id_, u, title="U.S. bishops demand justice", source="EWTN News (CNA)",
                 src="rss", query="rss:EWTN News (CNA)", score=2)
        return _rows(c)

    def run(tag_for):
        rs = rows()
        alias, _tags = merge_dups.page_aliases(merge_dups.title_sets(rs), fetch=tag_for,
                                               log=lambda s: None, sleep=0)
        return plan_merges(rs, merge_dups.make_key(alias))

    p = run(lambda u: b)
    _check(fails, "page check merges a moved article", [(x[1]["id"], [l["id"] for l in x[2]])
                                                        for x in p], [(11374, [11566])])
    _check(fails, "page check ignores a homepage tag",
           len(run(lambda u: "https://www.ewtnnews.com/")), 0)
    _check(fails, "page check: no tag, no merge", len(run(lambda u: None)), 0)


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
    check_score_carried(fails)
    check_page_check(fails)
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
