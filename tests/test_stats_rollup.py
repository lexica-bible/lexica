#!/usr/bin/env python3
"""Tests for stats_rollup.py — the visitor-stats data layer. Builds its own
in-memory notes.db; never touches a real one.

Locks: finished days freeze once and never re-count; raw rows are only dropped
for frozen days; today is counted live; every dimension's uniques are exact per
day; secrets in the landing address are never stored; search-engine sorting on
stress hosts; returning / spike / delta math.

Run:  python tests/test_stats_rollup.py
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stats_rollup as sr

TODAY = "2026-11-01"


def _db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    sr.ensure(conn)
    return conn


def _hit(conn, day, visitor, ref="direct", surface="library", path="/", ua="desktop",
         acct=0, gap=None):
    conn.execute(
        "INSERT INTO visits (day, ts, visitor, ref, surface, path, ua, acct, gap)"
        " VALUES (?,?,?,?,?,?,?,?,?)", (day, 0, visitor, ref, surface, path, ua, acct, gap))
    conn.commit()


def _old_hit(conn, day, visitor, ref="direct"):
    # A row from before the new columns existed.
    conn.execute("INSERT INTO visits (day, ts, visitor, ref) VALUES (?,?,?,?)",
                 (day, 0, visitor, ref))
    conn.commit()


def _raw_count(conn, day=None):
    if day:
        return conn.execute("SELECT count(*) FROM visits WHERE day=?", (day,)).fetchone()[0]
    return conn.execute("SELECT count(*) FROM visits").fetchone()[0]


# ── tables ───────────────────────────────────────────────────────────────────
def test_ensure_adds_columns_to_an_old_visits_table():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE visits (id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL,"
                 " ts INTEGER NOT NULL, visitor TEXT NOT NULL, ref TEXT)")
    conn.execute("INSERT INTO visits (day, ts, visitor, ref) VALUES ('2026-10-01',0,'a','direct')")
    conn.commit()
    sr.ensure(conn)
    sr.ensure(conn)                                    # second run: no error
    cols = {r[1] for r in conn.execute("PRAGMA table_info(visits)")}
    assert {"surface", "path", "ua", "acct", "gap"} <= cols
    assert conn.execute("SELECT count(*) FROM visits").fetchone()[0] == 1


# ── freezing ─────────────────────────────────────────────────────────────────
def test_rollup_freezes_finished_days_only_and_is_safe_to_rerun():
    conn = _db()
    _hit(conn, "2026-10-30", "a"); _hit(conn, "2026-10-30", "a"); _hit(conn, "2026-10-30", "b")
    _hit(conn, TODAY, "c")
    assert sr.rollup(conn, TODAY) == 1
    frozen = {r[0] for r in conn.execute("SELECT DISTINCT day FROM visits_daily")}
    assert frozen == {"2026-10-30"}                    # today stays live
    before = conn.execute("SELECT * FROM visits_daily ORDER BY day, dim, key").fetchall()
    # A late row for a frozen day must NOT change its frozen numbers on re-run.
    _hit(conn, "2026-10-30", "z")
    assert sr.rollup(conn, TODAY) == 0
    after = conn.execute("SELECT * FROM visits_daily ORDER BY day, dim, key").fetchall()
    assert [tuple(r) for r in before] == [tuple(r) for r in after]
    t = conn.execute("SELECT views, uniques FROM visits_daily WHERE day='2026-10-30'"
                     " AND dim='total'").fetchone()
    assert tuple(t) == (3, 2)


def test_prune_drops_only_old_frozen_days():
    conn = _db()
    old = sr.day_add(TODAY, -(sr.RAW_KEEP_DAYS + 5))
    keep = sr.day_add(TODAY, -(sr.RAW_KEEP_DAYS - 1))
    _hit(conn, old, "a"); _hit(conn, keep, "b"); _hit(conn, TODAY, "c")
    sr.rollup(conn, TODAY)
    assert _raw_count(conn, old) == 0                  # frozen + old -> dropped
    assert _raw_count(conn, keep) == 1                 # inside 90 days -> kept
    assert _raw_count(conn, TODAY) == 1
    # Its numbers survive in the frozen table.
    days = sr.load_days(conn, TODAY)
    assert days[old]["total"][""] == (1, 1)


def test_prune_never_drops_an_unfrozen_day():
    # Simulate a day that is old but somehow not frozen (rollup must freeze first).
    conn = _db()
    old = sr.day_add(TODAY, -200)
    _hit(conn, old, "a")
    sr.rollup(conn, TODAY)
    assert conn.execute("SELECT count(*) FROM visits_daily WHERE day=? AND dim='total'",
                        (old,)).fetchone()[0] == 1
    # Control: a DELETE without the frozen-day guard would have dropped a day that
    # had no frozen row. Prove the guard is what protects it.
    conn2 = _db()
    _hit(conn2, old, "a")
    conn2.execute("DELETE FROM visits WHERE day < ? AND day IN"
                  " (SELECT day FROM visits_daily WHERE dim='total')", (sr.day_add(TODAY, -90),))
    assert _raw_count(conn2, old) == 1


def test_load_days_counts_today_and_unfrozen_days_live():
    conn = _db()
    _hit(conn, "2026-10-31", "a")
    _hit(conn, TODAY, "b"); _hit(conn, TODAY, "b")
    days = sr.load_days(conn, TODAY)                   # no rollup run at all
    assert days["2026-10-31"]["total"][""] == (1, 1)
    assert days[TODAY]["total"][""] == (2, 1)


def test_uniques_are_exact_per_dimension():
    # One visitor lands twice in a day with two different referrers. The day has
    # ONE unique; summing the finer (ref) cells would say two.
    conn = _db()
    _hit(conn, TODAY, "a", ref="direct")
    _hit(conn, TODAY, "a", ref="google.com")
    days = sr.load_days(conn, TODAY)
    assert days[TODAY]["total"][""] == (2, 1)
    assert days[TODAY]["surface"]["library"] == (2, 1)
    # Control: the cell-summing shortcut is wrong here.
    assert sum(u for _v, u in days[TODAY]["ref"].values()) == 2


def test_old_rows_roll_up_as_unknown_and_are_left_out_of_tables():
    conn = _db()
    _old_hit(conn, "2026-10-20", "a", ref="bing.com")
    _hit(conn, TODAY, "b", surface="lexicon", path="/?lex=G25", ua="mobile")
    sr.rollup(conn, TODAY)
    days = sr.load_days(conn, TODAY)
    assert days["2026-10-20"]["surface"] == {sr.UNKNOWN: (1, 1)}
    s = sr.summarize(days, TODAY, "30d", [])
    assert s["kpi"]["views"]["v"] == 2                 # old row still counts as a view
    assert s["pages_total"] == 1                       # but not in the page table
    assert [p["surface"] for p in s["pages"]] == ["lexicon"]
    assert s["pages_since"] == TODAY and s["devices"]["since"] == TODAY
    assert s["refs"]["search"][0]["name"] == "Bing"    # referrers have full history


# ── cleaning ─────────────────────────────────────────────────────────────────
def test_clean_path_never_keeps_secrets():
    assert sr.clean_path("/?news=SECRETKEY123") == "/?news"
    assert sr.clean_path("/?reset=tok_abc") == "/?reset"
    assert "SECRET" not in sr.clean_path("/?b=Jhn&news=SECRET")   # news wins, value gone
    assert sr.clean_path("/?b=Jhn&c=3&t=ABP&x=evil") == "/?b=Jhn&c=3&t=abp"
    assert sr.clean_path("/?lex=g25") == "/?lex=G25"
    assert sr.clean_path("/?lex=G1246.2") == "/?lex=G1246.2"
    assert sr.clean_path("/?lex=<script>") == "/"
    assert sr.clean_path("/?b=Jhn&c=9999") == "/?b=Jhn"
    assert sr.clean_path("/?b=../../etc") == "/"
    assert sr.clean_path("/" + "a" * 100) == "/"
    assert sr.clean_path(None) == "/" and sr.clean_path(42) == "/"
    assert sr.clean_path("/") == "/"


def test_clean_surface_and_gap():
    assert sr.clean_surface("lexicon") == "lexicon"
    assert sr.clean_surface("admin'--") == sr.UNKNOWN
    assert sr.clean_gap(-1) == -1 and sr.clean_gap(3) == 3
    assert sr.clean_gap(0) is None and sr.clean_gap(True) is None
    assert sr.clean_gap("3") is None and sr.clean_gap(99999) is None


def test_ua_family():
    iphone = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit Mobile/15E148"
    android_tab = "Mozilla/5.0 (Linux; Android 13; SM-X700) AppleWebKit Chrome/120 Safari"
    win = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    assert sr.ua_family(iphone) == "mobile"
    assert sr.ua_family(android_tab) == "mobile"       # tablets fold into mobile
    assert sr.ua_family(win) == "desktop"
    assert sr.ua_family("") == "desktop"


def test_classify_ref_stress_hosts():
    assert sr.classify_ref("google.com") == ("search", "Google")
    assert sr.classify_ref("google.co.uk") == ("search", "Google")
    assert sr.classify_ref("google.com.au") == ("search", "Google")
    assert sr.classify_ref("com.google.android.googlequicksearchbox") == ("search", "Google (Android)")
    assert sr.classify_ref("bing.com") == ("search", "Bing")
    assert sr.classify_ref("cn.bing.com") == ("search", "Bing")
    assert sr.classify_ref("duckduckgo.com") == ("search", "DuckDuckGo")
    assert sr.classify_ref("search.yahoo.com") == ("search", "Yahoo")
    assert sr.classify_ref("uk.search.yahoo.com") == ("search", "Yahoo")
    # Not searches:
    assert sr.classify_ref("news.google.com")[0] == "site"
    assert sr.classify_ref("mail.google.com")[0] == "site"
    assert sr.classify_ref("com.google.android.gm")[0] == "site"     # Gmail app
    assert sr.classify_ref("mail.yahoo.com")[0] == "site"
    assert sr.classify_ref("googleblog.com")[0] == "site"
    assert sr.classify_ref("github.com") == ("site", "github.com")


# ── summary math ─────────────────────────────────────────────────────────────
def test_kpi_deltas_compare_equal_length_windows():
    conn = _db()
    for i in range(7):                                 # this week: 2 views/day
        d = sr.day_add(TODAY, -i)
        _hit(conn, d, "a" + d); _hit(conn, d, "b" + d)
    for i in range(7, 14):                             # prior week: 1 view/day
        d = sr.day_add(TODAY, -i)
        _hit(conn, d, "a" + d)
    sr.rollup(conn, TODAY)
    s = sr.summarize(sr.load_days(conn, TODAY), TODAY, "7d", [])
    assert s["kpi"]["views"] == {"v": 14, "prior": 7}
    assert s["kpi"]["uniques"] == {"v": 14, "prior": 7}
    assert s["kpi"]["today"] == {"v": 2, "prior": 2}
    assert s["kpi"]["last7"] == {"v": 14, "prior": 7}
    assert len(s["by_day"]) == 7 and s["start"] == sr.day_add(TODAY, -6)
    s_all = sr.summarize(sr.load_days(conn, TODAY), TODAY, "all", [])
    assert s_all["kpi"]["views"] == {"v": 21, "prior": None}
    assert s_all["start"] == sr.day_add(TODAY, -13)


def test_by_day_fills_empty_days_with_zero():
    conn = _db()
    _hit(conn, sr.day_add(TODAY, -3), "a")
    s = sr.summarize(sr.load_days(conn, TODAY), TODAY, "7d", [])
    assert [r["views"] for r in s["by_day"]] == [0, 0, 0, 1, 0, 0, 0]


def test_returning_counts_only_visits_seen_earlier_in_the_window():
    conn = _db()
    _hit(conn, TODAY, "a", gap=2)      # last here 2 days ago -> inside 7d window
    _hit(conn, TODAY, "b", gap=29)     # last here 29 days ago -> outside 7d, inside 30d
    _hit(conn, TODAY, "e", gap=30)     # 30 days ago -> before the 30d window's first day
    _hit(conn, TODAY, "c", gap=-1)     # first visit
    _hit(conn, TODAY, "d", gap=None)   # browser couldn't say -> not in the share
    s = sr.summarize(sr.load_days(conn, TODAY), TODAY, "7d", [])
    r = s["kpi"]["returning"]
    assert r["v"] == 1 and r["known"] == 4
    assert r["prior"] is None          # tracking started inside this window
    s30 = sr.summarize(sr.load_days(conn, TODAY), TODAY, "30d", [])
    assert s30["kpi"]["returning"]["v"] == 2   # 30 days back is inside 30d


def test_spike_needs_five_times_the_trailing_median():
    conn = _db()
    for i in range(1, 31):
        _hit(conn, sr.day_add(TODAY, -i), "v%d" % i)   # 1 view/day for 30 days
    for j in range(6):
        _hit(conn, TODAY, "s%d" % j, ref="google.com")   # 6 views today
    _hit(conn, TODAY, "x", ref="direct")
    s = sr.summarize(sr.load_days(conn, TODAY), TODAY, "30d", [])
    assert [p["day"] for p in s["spikes"]] == [TODAY]
    assert s["spikes"][0]["views"] == 7 and s["spikes"][0]["top_ref"] == "google.com"
    # Exactly 5x is not a spike.
    conn2 = _db()
    for i in range(1, 31):
        _hit(conn2, sr.day_add(TODAY, -i), "v%d" % i)
    for j in range(5):
        _hit(conn2, TODAY, "s%d" % j)
    assert sr.summarize(sr.load_days(conn2, TODAY), TODAY, "30d", [])["spikes"] == []


def test_pages_group_paths_under_surface_with_14_day_sparkline():
    conn = _db()
    _hit(conn, TODAY, "a", surface="library", path="/?b=Jhn&c=3&t=abp")
    _hit(conn, TODAY, "b", surface="library", path="/")
    _hit(conn, TODAY, "c", surface="library", path="/")
    _hit(conn, sr.day_add(TODAY, -1), "d", surface="lexicon", path="/?lex=G25")
    s = sr.summarize(sr.load_days(conn, TODAY), TODAY, "30d", [])
    lib = s["pages"][0]
    assert lib["surface"] == "library" and lib["views"] == 3
    assert [p["path"] for p in lib["paths"]] == ["/", "/?b=Jhn&c=3&t=abp"]
    assert len(lib["spark"]) == 14 and lib["spark"][-1] == 3
    assert s["pages"][1]["spark"][-2:] == [1, 0]
    assert s["pages_total"] == 4


def test_referrers_split_and_direct_kept_out():
    conn = _db()
    for v, ref in enumerate(["direct", "direct", "google.com", "google.co.uk",
                             "com.google.android.googlequicksearchbox", "github.com"]):
        _hit(conn, TODAY, "v%d" % v, ref=ref)
    _hit(conn, sr.day_add(TODAY, -8), "p", ref="google.com")    # prior 7d window
    s = sr.summarize(sr.load_days(conn, TODAY), TODAY, "7d", [])
    r = s["refs"]
    assert r["direct"] == 2 and r["non_direct"] == 4 and r["views"] == 6
    names = [(g["name"], g["n"], g["prior"]) for g in r["search"]]
    assert names == [("Google", 2, 1), ("Google (Android)", 1, 0)]
    assert [g["name"] for g in r["other"]] == ["github.com"]


def test_accounts_new_active_and_order():
    accts = [
        {"email": "old@x.com", "created": "2026-01-01", "last_seen": "2026-10-30"},
        {"email": "new@x.com", "created": "2026-10-29", "last_seen": None},
        {"email": "gone@x.com", "created": "2026-02-01", "last_seen": "2026-03-01"},
    ]
    s = sr.summarize({}, TODAY, "7d", accts)
    a = s["accounts"]
    assert a["total"] == 3 and a["new"] == 1 and a["active"] == 1
    assert [x["email"] for x in a["list"]] == ["old@x.com", "gone@x.com", "new@x.com"]
    assert s["kpi"]["accounts"] == {"v": 3, "prior": 2}


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except Exception:
            failed += 1
            print(f"  FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
