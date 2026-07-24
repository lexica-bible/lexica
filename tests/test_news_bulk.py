#!/usr/bin/env python3
"""Bulk triage (_apply_bulk) + tolerant publish-date parsing (dateparse/item_date).

Bulk moves run against a REAL in-memory sqlite reviews table — the same
_apply_bulk the /api/news/bulk route calls, not a re-implementation. Covers:
  - the three sanctioned transitions actually move rows
  - idempotency: double-firing the identical call changes 0 the second time
  - stale-state skip: a row another action already moved is skipped, not clobbered
  - per-reviewer isolation: reviewer A's bulk never touches reviewer B's rows
  - changed-count honesty: the return equals the rows that actually moved

Date parsing covers Google News's real pubDate shape (RFC 822), the common
malformed variants, ISO (dc:date / atom:updated), and that junk comes back ''
(the honest "unknown" marker) rather than a guessed date.
"""
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "news"))

import views_news
from dateparse import to_iso
from gather_news import item_date


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(views_news._REVIEWS_SCHEMA)
    return c


def _status(c, rid, item):
    r = c.execute("SELECT status FROM reviews WHERE reviewer=? AND item_id=?",
                  (rid, item)).fetchone()
    return r["status"] if r else "new"


def _check(fails, label, got, want):
    if got != want:
        fails.append(f"{label}: got {got!r}, want {want!r}")


def check_bulk_moves_and_counts(fails):
    """new→keep moves unreviewed rows and reports the true changed count."""
    c = _conn()
    changed = views_news._apply_bulk(c, "u1", [1, 2, 3], "keep", "new")
    _check(fails, "keep-all changed", changed, 3)
    for i in (1, 2, 3):
        _check(fails, f"item {i} kept", _status(c, "u1", i), "keep")


def check_bulk_idempotent(fails):
    """The identical call fired twice: second run finds nothing in 'new' and changes 0."""
    c = _conn()
    views_news._apply_bulk(c, "u1", [1, 2], "dismiss", "new")
    again = views_news._apply_bulk(c, "u1", [1, 2], "dismiss", "new")
    _check(fails, "double-fire changed", again, 0)
    _check(fails, "double-fire state intact", _status(c, "u1", 1), "dismiss")


def check_stale_rows_skipped(fails):
    """A row that moved between page load and the bulk action is skipped, never clobbered:
    Keep All (new→keep) must not drag an already-dismissed row back to keep."""
    c = _conn()
    views_news._apply_bulk(c, "u1", [7], "dismiss", "new")       # someone dismissed it first
    changed = views_news._apply_bulk(c, "u1", [7, 8], "keep", "new")
    _check(fails, "stale-skip changed", changed, 1)              # only the fresh row 8
    _check(fails, "dismissed row untouched", _status(c, "u1", 7), "dismiss")
    _check(fails, "fresh row kept", _status(c, "u1", 8), "keep")


def check_kept_flush(fails):
    """The Kept view's Dismiss All = keep→dismiss, and it ignores rows not in keep."""
    c = _conn()
    views_news._apply_bulk(c, "u1", [1, 2], "keep", "new")
    changed = views_news._apply_bulk(c, "u1", [1, 2, 3], "dismiss", "keep")
    _check(fails, "flush changed", changed, 2)                    # 3 was never kept
    _check(fails, "flushed to dismissed", _status(c, "u1", 1), "dismiss")
    _check(fails, "unkept row stays inbox", _status(c, "u1", 3), "new")


def check_reviewer_isolation(fails):
    """Reviewer A's Dismiss All never touches reviewer B's state on the same items."""
    c = _conn()
    views_news._apply_bulk(c, "kTUDOR", [1, 2], "keep", "new")    # B kept both
    views_news._apply_bulk(c, "u1", [1, 2], "dismiss", "new")     # A dismisses "all"
    _check(fails, "A dismissed own", _status(c, "u1", 1), "dismiss")
    _check(fails, "B's keep survives", _status(c, "kTUDOR", 1), "keep")
    _check(fails, "B's keep survives (2)", _status(c, "kTUDOR", 2), "keep")


def check_transition_table(fails):
    """The route only accepts the three sanctioned moves — dismissed rows have no bulk exit."""
    _check(fails, "sanctioned transitions",
           views_news._BULK_TRANSITIONS,
           {("new", "keep"), ("new", "dismiss"), ("keep", "dismiss")})


def check_date_parser(fails):
    """to_iso: the real Google pubDate shape, the tolerated malformations, ISO, junk→''."""
    cases = [
        # (input, expected ISO date part) — '' expected means "honest unknown"
        ("Sun, 17 May 2026 04:12:00 GMT", "2026-05-17"),      # Google News's actual shape
        ("17 May 2026 04:12:00 GMT", "2026-05-17"),           # missing weekday
        ("Sun, 17 May 2026 04:12:00", "2026-05-17"),          # missing timezone -> UTC
        ("Sun, 17 May 2026 04:12:00 +1200", "2026-05-16"),    # tz offset converts to UTC
        ("2026-05-17T04:12:00Z", "2026-05-17"),               # ISO with Z (atom:updated)
        ("2026-05-17T04:12:00+00:00", "2026-05-17"),          # ISO with offset (dc:date)
        ("2026-05-17", "2026-05-17"),                         # bare ISO date
        ("May 17, 2026", "2026-05-17"),                       # loose US shape
        ("17 May 2026", "2026-05-17"),                        # loose day-first shape
        ("", ""),
        ("last Tuesday", ""),                                 # junk must NOT become a date
        ("nonsense 99/99/9999", ""),
    ]
    for raw, want in cases:
        got = to_iso(raw)[:10]
        _check(fails, f"to_iso({raw!r})", got, want)


def check_item_date_fallbacks(fails):
    """item_date: pubDate first, then dc:date / atom:updated, '' when nothing readable."""
    def item(xml_inner):
        return ET.fromstring(f"<item>{xml_inner}</item>")
    _check(fails, "pubDate wins",
           item_date(item("<pubDate>Sun, 17 May 2026 04:12:00 GMT</pubDate>"))[:10],
           "2026-05-17")
    _check(fails, "dc:date fallback",
           item_date(item('<pubDate>garbage</pubDate>'
                          '<date xmlns="http://purl.org/dc/elements/1.1/">2026-05-17T04:12:00Z</date>'))[:10],
           "2026-05-17")
    _check(fails, "atom:updated fallback",
           item_date(item('<updated xmlns="http://www.w3.org/2005/Atom">2026-05-17</updated>'))[:10],
           "2026-05-17")
    _check(fails, "nothing readable -> ''", item_date(item("<pubDate>???</pubDate>")), "")


def main():
    fails = []
    for check in (check_bulk_moves_and_counts,
                  check_bulk_idempotent,
                  check_stale_rows_skipped,
                  check_kept_flush,
                  check_reviewer_isolation,
                  check_transition_table,
                  check_date_parser,
                  check_item_date_fallbacks):
        check(fails)
        print(f"  ran {check.__name__}")
    if fails:
        print(f"\n{len(fails)} FAILED")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("\nBulk triage holds: sanctioned moves only, idempotent, stale-skip, per-reviewer; "
          "date parser honest on junk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
