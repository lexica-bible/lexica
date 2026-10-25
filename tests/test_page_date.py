#!/usr/bin/env python3
"""Locks the page-date finder (scripts/news/pagedate.py) and the write rule that uses it
(scripts/news/date_pass.py decide).

Why: Google's date on the Google News path is a discovery/crawl date. spzh.eu id 26533
("The head of Phanar and Pope Francis hold a joint ecumenical prayer") came in stamped
2026-10-18; its own page says 2022-11-05. The page date wins — this test pins that the
finder reads it off the REAL page markup, and what gets written for each outcome.

Offline: every page is a fixture or an inline string (html= skips the network).
Run from repo root:  python tests/test_page_date.py
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

from scripts.news.pagedate import page_date, page_date_detail   # noqa: E402
from scripts.news.date_pass import decide                       # noqa: E402

SPZH_URL = ("https://spzh.eu/en/news/91616-glava-fanara-i-papa-francisk-proveli-"
            "sovmestnuju-ekumenicheskuju-molitvu.html")

n = 0


def test(name, fn):
    global n
    fn()
    n += 1
    print("ok  " + name)


def _spzh():
    with open(os.path.join(ROOT, "tests", "fixtures", "spzh_91616.html"), encoding="utf-8") as f:
        return f.read()


# --- the four ruled cases -------------------------------------------------------------

def t1():
    d, how = page_date_detail(SPZH_URL, html=_spzh())
    assert d == "2022-11-05", d
    assert how == "jsonld", how                       # read from the page's own data block


def t2():
    html = "<html><body><h1>x</h1><time datetime='2023-07-14T09:30:00+03:00'>14 July</time></body></html>"
    assert page_date("https://example.invalid/news/some-story", html=html) == "2023-07-14"


def t3():
    html = "<html><body><h1>no date anywhere</h1><p>text</p></body></html>"
    assert page_date("https://example.invalid/2024/03/some-story", html=html) == "2024-03"


def t4():
    html = "<html><body><h1>no date anywhere</h1><p>text</p></body></html>"
    assert page_date("https://example.invalid/news/some-story", html=html) is None


test("spzh.eu 26533 page -> 2022-11-05 (not Google's 2026-10-18)", t1)
test("page with only a <time datetime> -> its day", t2)
test("no page date, /2024/03/ in the URL -> 2024-03", t3)
test("no page date, bare URL -> None", t4)


# --- the order and the fail-soft contract --------------------------------------------

def t5():
    # JSON-LD wins over meta and <time>; an Article-type object beats a WebPage one
    html = ("<script type='application/ld+json'>{\"@graph\":["
            "{\"@type\":\"WebPage\",\"datePublished\":\"2020-01-01\"},"
            "{\"@type\":\"NewsArticle\",\"datePublished\":\"2021-12-01T00:51:00+0200\"}]}</script>"
            "<meta property='article:published_time' content='2019-05-05T00:00:00Z'>"
            "<time datetime='2018-01-01'>x</time>")
    # the page's own calendar day, not shifted to UTC (00:51+02:00 is still Dec 1 on the page)
    assert page_date("https://example.invalid/a", html=html) == "2021-12-01"


def t6():
    html = "<meta content=\"2019-05-05T10:00:00Z\" property=\"og:article:published_time\">"
    assert page_date_detail("https://example.invalid/a", html=html) == ("2019-05-05", "meta")


def t7():
    # a <time> inside <article> beats one in a sidebar earlier on the page
    html = ("<aside><time datetime='2017-02-02'>old sidebar</time></aside>"
            "<article><h1>x</h1><time datetime='2022-03-04'>4 March</time></article>")
    assert page_date("https://example.invalid/a", html=html) == "2022-03-04"


def t8():
    # unreachable page: no raise, None (and a bare URL has nothing to fall back on)
    assert page_date("http://127.0.0.1:9/never", timeout=1) is None
    assert page_date("not-a-url") is None


test("JSON-LD first, Article-type preferred, day as written", t5)
test("og:article:published_time meta (attribute order free)", t6)
test("<time> read inside <article> when the page has one", t7)
test("a failed fetch returns None, never raises", t8)


# --- what gets written ------------------------------------------------------------------

def t9():
    w = decide("2026-10-18T12:31:23+00:00", "2022-11-05")
    assert w["published"] == "2022-11-05T00:00:00+00:00"
    assert (w["published_page"], w["published_src"], w["date_flag"]) == ("2022-11-05", "page", 1)
    assert w["delta"] == 1443


def t10():
    w = decide("2025-08-09T07:00:00+00:00", "2025-08-09")     # id 5687: Google was right
    assert (w["published_src"], w["date_flag"], w["delta"]) == ("page", 0, 0)


def t11():
    w = decide("2026-10-18T12:31:23+00:00", None)            # no page date: unverified
    assert w == {"published_src": "google", "date_flag": 1, "delta": None}
    assert "published" not in w                               # Google's date left in place


def t12():
    same = decide("2024-03-19T07:00:00+00:00", "2024-03")     # month agrees -> keep Google's day
    assert "published" not in same and same["date_flag"] == 0 and same["published_src"] == "page"
    off = decide("2026-10-18T07:00:00+00:00", "2024-03")      # month disagrees -> 1st, flagged
    assert off["published"] == "2024-03-01T00:00:00+00:00" and off["date_flag"] == 1


test("page date found, >30 days off Google -> page date written, flagged", t9)


# --- the hard stop (2026-10-25: a no-timeout Google lookup hung the first full dry run) ----

import sqlite3                                                   # noqa: E402
import time                                                      # noqa: E402
import threading                                                 # noqa: E402
import scripts.news.date_pass as dp                              # noqa: E402

_release = threading.Event()                                     # lets the "hung" threads finish


def _hang(*_a):
    _release.wait(30)                                            # a call that never answers
    return "never"


def t_deadline():
    t0 = time.time()
    assert dp.with_deadline(_hang, "x", secs=0.3) is dp.TIMED_OUT
    assert time.time() - t0 < 2
    assert dp.with_deadline(lambda u: "ok", "x", secs=2) == "ok"
    assert dp.with_deadline(lambda u: 1 / 0, "x", secs=2) is None   # an exception = nothing found


def _table():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, url TEXT, resolved_url TEXT, title TEXT, "
              "source TEXT, published TEXT, query TEXT, first_seen TEXT, score INT)")
    c.execute("INSERT INTO items VALUES (1, 'https://news.google.com/rss/articles/A', '', 't', 's', "
              "'2026-10-18T12:31:23+00:00', 'q', '2026-10-20T06:00:00+00:00', 8)")
    c.execute("INSERT INTO items VALUES (2, 'https://news.google.com/rss/articles/B', "
              "'https://b.example/page', 't', 's', '2026-10-18T12:31:23+00:00', 'q', "
              "'2026-10-20T06:00:00+00:00', 8)")
    c.commit()
    return c


def t_hung_steps_skip_untouched():
    saved = (dp.RESOLVE_DEADLINE, dp.PAGE_DEADLINE, dp.page_date_detail)
    dp.RESOLVE_DEADLINE, dp.PAGE_DEADLINE, dp.page_date_detail = 0.3, 0.3, _hang
    try:
        c = _table()
        t0 = time.time()
        t = dp.run_pass(c, "2026-09-01", apply=True, resolve=_hang, sleep=0, log=lambda s: None)
        assert time.time() - t0 < 5, "a hung step must not hold the run"
        assert t["timed_out"] == 2 and t["page"] == 0 and t["no_page_date"] == 0, t
        rows = c.execute("SELECT id, published, published_src, date_flag, published_page "
                         "FROM items ORDER BY id").fetchall()
        # both rows untouched: still Google's date, still unchecked, so the next run retries them
        assert [tuple(r) for r in rows] == [
            (1, "2026-10-18T12:31:23+00:00", "google", 0, None),
            (2, "2026-10-18T12:31:23+00:00", "google", 0, None)], [tuple(r) for r in rows]
        assert len(dp.candidates(c, "2026-09-01")) == 2
    finally:
        dp.RESOLVE_DEADLINE, dp.PAGE_DEADLINE, dp.page_date_detail = saved
        _release.set()


test("a hung network call is cut off at its hard stop", t_deadline)
test("a hung lookup or page fetch skips the row untouched (retried next run)", t_hung_steps_skip_untouched)
test("page date agrees with Google -> page date, not flagged", t10)
test("no page date -> Google date kept, flagged unverified", t11)
test("month-only page date -> keep Google's day if same month, else 1st + flag", t12)

print(f"\n{n} passed")
