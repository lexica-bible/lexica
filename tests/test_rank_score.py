#!/usr/bin/env python3
"""Locks per-outlet score normalization, DOWNWARD ONLY (scripts/news/rank.py) — ruling
2026-10-24, Item 2 layer 2 reissued: rank_score = min(score, normalized). The Inbox default
ORDER reads rank_score; the raw score is never touched, and nothing ranks above its raw score.

Fixture (in-memory, made-up rows): five outlets —
  A: 30 rows, all 8-9         (mean 8.5, sd 0.5)    always scores itself high
  B: 30 rows, spread 1-9      (mean 5,  sd 2.45)    uses the whole scale
  C: 4 rows at 8                                    too few to normalize
  D: 25 rows, all 7           (sd 0)                big enough, but flat
  E: 30 rows, mostly 1, one 7 (mean 1.27)           a mostly-off-topic feed (low mean)
plus 40 old A rows at score 1 (outside the 90-day window) and one unscored A row.
Run from repo root:  python tests/test_rank_score.py
"""
import os
import sys
import sqlite3
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from scripts.news.rank import outlet_stats, rank_score, normalized   # noqa: E402

NOW = datetime.datetime(2026, 10, 24, 12, 0, tzinfo=datetime.timezone.utc)
RECENT = (NOW - datetime.timedelta(days=3)).isoformat()
OLD = (NOW - datetime.timedelta(days=120)).isoformat()

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, source TEXT, score INTEGER, first_seen TEXT)")
rows = ([("A", 8)] * 15 + [("A", 9)] * 15
        + [("B", s) for s in list(range(1, 10)) * 3] + [("B", 5)] * 3
        + [("C", 8)] * 4
        + [("D", 7)] * 25
        + [("E", 1)] * 27 + [("E", 2)] * 2 + [("E", 7)])
conn.executemany("INSERT INTO items (source, score, first_seen) VALUES (?,?,?)",
                 [(s, sc, RECENT) for s, sc in rows])
conn.executemany("INSERT INTO items (source, score, first_seen) VALUES (?,?,?)",
                 [("A", 1, OLD)] * 40)
conn.execute("INSERT INTO items (source, score, first_seen) VALUES ('A', NULL, ?)", (RECENT,))
conn.commit()
BEFORE = conn.execute("SELECT id, source, score FROM items ORDER BY id").fetchall()

STATS = outlet_stats(conn, now=NOW)


def rs(src, score):
    return rank_score(score, STATS.get(src))


n = 0


def test(name, fn):
    global n
    fn()
    n += 1
    print("ok  " + name)


def t_stats():
    na, ma, sa = STATS["A"]
    assert (na, round(ma, 6), round(sa, 6)) == (30, 8.5, 0.5), STATS["A"]
    nb, mb, sb = STATS["B"]
    assert (nb, round(mb, 6), round(sb, 3)) == (30, 5.0, 2.449), STATS["B"]


def t_a8_below_b8():
    assert rs("A", 8) < rs("B", 8), (rs("A", 8), rs("B", 8))


def t_a9_below_b9():
    # Ruled as "A's 9 ranks below B's 9 and B's 9 keeps rank_score 9". The first half holds.
    # The second half CANNOT under the ruled formula: B's normalized 9 is
    # 5 + 1.5 * (9 - 5) / 2.449 = 7.4, so min(9, 7.4) = 7.4. Pinned at what the rule does;
    # flagged for re-ruling (2026-10-24). B keeps raw only at or below its mean (5).
    assert rs("A", 9) < rs("B", 9), (rs("A", 9), rs("B", 9))
    assert (rs("A", 9), rs("B", 9)) == (6.5, 7.4), (rs("A", 9), rs("B", 9))
    assert rs("B", 5) == 5 and rs("B", 4) == 4


def t_never_above_raw():
    for src in ("A", "B", "C", "D", "E", "Nobody"):
        for s in range(0, 11):
            assert rs(src, s) <= s, (src, s, rs(src, s))


def t_low_mean_outlet():
    assert normalized(7, STATS["E"]) > 7          # the old formula would have lifted it...
    assert rs("E", 7) == 7                         # ...min() keeps it at its raw 7


def t_high_self_scorer_docked():
    assert rs("A", 8) == 3.5 and rs("A", 9) == 6.5, (rs("A", 8), rs("A", 9))   # 5 + 1.5*z


def t_small_outlet():
    assert rs("C", 8) == 8


def t_flat_outlet():
    assert rs("D", 7) == 7


def t_unknown_outlet():
    assert rs("Nobody", 6) == 6


def t_raw_untouched():
    assert conn.execute("SELECT id, source, score FROM items ORDER BY id").fetchall() == BEFORE


test("stats: trailing 90 days of scored rows only (A = 30, mean 8.5, sd 0.5; B mean 5)", t_stats)
test("A's 8 ranks below B's 8", t_a8_below_b8)
test("A's 9 ranks below B's 9 (B's 9 = 7.4 under min(), see note)", t_a9_below_b9)
test("nothing ranks above its raw score, any outlet, any score", t_never_above_raw)
test("a low-mean outlet's 7 keeps 7", t_low_mean_outlet)
test("a high self-scorer comes down: A's 8 -> 3.5, A's 9 -> 6.5", t_high_self_scorer_docked)
test("C (n < 20) keeps rank_score = score", t_small_outlet)
test("D (n >= 20, sd 0) keeps rank_score = score", t_flat_outlet)
test("an outlet with no rows in the window keeps rank_score = score", t_unknown_outlet)
test("raw score column unchanged after the stats query", t_raw_untouched)

print(f"\n{n} passed")
