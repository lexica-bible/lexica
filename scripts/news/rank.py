#!/usr/bin/env python3
"""rank.py — per-outlet score normalization for the News Inbox ORDER, DOWNWARD ONLY
(ruling 2026-10-24, Item 2 layer 2, reissued).

Why: some outlets score themselves high on almost everything (Advent Messenger: 35% of its
last-30-day articles at 8+, 28 of 31 on cards no other outlet shares). A raw 8 from an outlet
that is always 8-9 says less than a raw 8 from one that ranges 1-9, so the default Inbox order
reads it lower.

  outlet stats  = n, mean, standard deviation of score over the trailing 90 days of scored rows
                  (score present, first pulled within 90 days), one GROUP BY for all outlets
  normalized    = 5 + 1.5 * (score - mean) / sd, clamped to 0-10, 1 decimal — only when the
                  outlet has n >= 20 and sd > 0; otherwise the raw score
  rank_score    = min(score, normalized)

DOWNWARD ONLY. The first version (rank_score = normalized) failed its PA check: the big RSS
feeds that are mostly off-topic average 1-2, so any on-topic story they run looked
"exceptional" and a raw 6-7 jumped to 9.5-10.0, filling the top 20. With min(), nothing ever
ranks above its own raw score: a high self-scorer's 9 comes down (6.7), a low-mean feed's 7
stays 7.

ORDER ONLY. `score` is never modified; the floor-5 gate, the card's number, clustering and the
scorer all stay on the raw score. The sd is the population sd (every row in the window).
"""
import math
import datetime

WINDOW_DAYS = 90
MIN_N = 20


def outlet_stats(conn, now=None):
    """{source: (n, mean, sd)} over the trailing WINDOW_DAYS of scored rows — ONE query."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    cutoff = (now - datetime.timedelta(days=WINDOW_DAYS)).isoformat()
    out = {}
    for src, n, mean, msq in conn.execute(
            "SELECT source, COUNT(*), AVG(score), AVG(score * score) FROM items "
            "WHERE score IS NOT NULL AND first_seen >= ? GROUP BY source", (cutoff,)):
        var = max(0.0, (msq or 0.0) - (mean or 0.0) ** 2)
        out[src or ""] = (n, mean, math.sqrt(var))
    return out


def normalized(score, st):
    """The score re-read against its outlet's own 90-day curve (5 + 1.5z, clamped 0-10,
    1 decimal), or the raw score when the outlet is too small (n < 20), flat (sd 0) or unknown."""
    if score is None or not st:
        return score
    n, mean, sd = st
    if n < MIN_N or sd <= 1e-9:          # 1e-9: a flat outlet's float sd is 0, not "tiny"
        return score
    z = (score - mean) / sd
    return round(min(10.0, max(0.0, 5.0 + 1.5 * z)), 1)


def rank_score(score, st):
    """min(score, normalized): an outlet's typical story can come DOWN, nothing goes up."""
    if score is None:
        return None
    return min(score, normalized(score, st))
