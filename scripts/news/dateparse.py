#!/usr/bin/env python3
"""dateparse.py — ONE tolerant publish-date parser for both ingest paths.

gather_news.py (Google News XML) and pull_rss.py (feedparser) each had their own
date handling with a silent ''-on-junk fallback. This is the shared home so the
two can't drift: give it whatever date string a feed offered and it returns a
UTC ISO timestamp, or '' when the string is genuinely unreadable.

'' is meaningful downstream: an empty published date is the "we don't know when
this ran" marker (the feed shows it as an estimated ~first-seen date), so this
must NEVER guess a date from junk — better an honest '' than a wrong day.

Formats tried, in order:
  1. RFC 822 (the RSS standard: 'Sat, 17 May 2026 04:12:00 GMT') including the
     common malformed variants email.utils tolerates (missing weekday, odd tz).
  2. ISO 8601 ('2026-05-17T04:12:00Z' / '+00:00' / date-only) — Atom `updated`
     and Dublin Core `dc:date` use this.
  3. A few loose real-world shapes seen in the wild: '17 May 2026',
     'May 17, 2026', '2026/05/17' (with or without a time tacked on).
A parsed date with no timezone is taken as UTC (the least-wrong default).
"""
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Loose fallback shapes (date part only; any trailing time is retried with %H:%M[:%S]).
_LOOSE = ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%m/%d/%Y")


def _utc_iso(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def to_iso(raw):
    """Best-effort UTC ISO timestamp from a feed date string; '' on junk."""
    s = (raw or "").strip()
    if not s:
        return ""
    # 1. RFC 822 and its tolerated malformations
    try:
        return _utc_iso(parsedate_to_datetime(s))
    except Exception:
        pass
    # 2. ISO 8601 (fromisoformat won't take a trailing 'Z' before 3.11 — normalize it)
    try:
        return _utc_iso(datetime.fromisoformat(s.replace("Z", "+00:00")))
    except Exception:
        pass
    # 3. Loose shapes — try the whole string, then date-part + common time tails
    cleaned = re.sub(r"\s+", " ", s)
    for fmt in _LOOSE:
        for full in (fmt, fmt + " %H:%M:%S", fmt + " %H:%M"):
            try:
                return _utc_iso(datetime.strptime(cleaned, full))
            except ValueError:
                continue
    return ""
