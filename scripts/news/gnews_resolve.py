#!/usr/bin/env python3
"""gnews_resolve.py — the ONE home for Google News wrapper-URL knowledge.

A Google News RSS link (news.google.com/rss/articles/<token>) hides the real
article URL. The AU_yqL "opaque" tokens can't be decoded locally — they need a
batchexecute round-trip to Google. We lean on the version-pinned PyPI package
`googlenewsdecoder` for that handshake so all the format-specific fragility
lives behind this one function.

Contract:
  - resolve(url, timeout=RESOLVE_LIMIT) -> clean URL string, or None.
  - NEVER raises. A 429, a timeout, a parse failure, an unknown format, a
    non-wrapper URL that slips in — all return None. The caller keeps the
    original wrapper on None (fail soft), so a Google format change breaks
    exactly this function and nothing downstream.
  - NEVER waits longer than `timeout` seconds (hard wall-clock stop). Every caller
    comes through here: the live site's Copy-shortlist resolver
    (views_news.resolve_urls), the nightly headline-link job and the backfills
    (via backfill_face_urls._resolve_with_backoff), and the page-date check.

THE HARD STOP (ruling 2026-10-25): PA has googlenewsdecoder 0.1.7, pinned in
requirements.txt. Its gnewsdecoder(source_url, interval=None, proxy=None) takes no
timeout and makes requests calls with none — one silent Google connection waits
forever (it froze a page-date dry run for 1h45m). Its timeout setting can't be
used (this version silently drops it), so the call runs under
scripts/news/deadline.with_deadline: past the limit we stop waiting and return
None; the abandoned background thread ends whenever its connection gives up.

If Google changes the token format, only resolve() breaks and it fails to None.
Re-pin / patch here; nothing else needs to know.
"""

WRAPPER_MARK = "news.google.com/rss/articles/"
# Hard stop per lookup. A normal decode is two requests plus the library's own 1s pause
# (a few seconds); this only ever fires on a connection that has gone silent.
RESOLVE_LIMIT = 20.0


def is_wrapper(url):
    """True if this is a Google News RSS wrapper that needs resolving."""
    return bool(url) and WRAPPER_MARK in url


def resolve(url, timeout=RESOLVE_LIMIT):
    """Resolve one Google News wrapper to its real article URL, or None.

    Never raises and never waits longer than `timeout` seconds — every failure
    path, a hang included, returns None so copy/backfill can fall back to the
    wrapper untouched.
    """
    if not is_wrapper(url):
        return None
    try:
        from googlenewsdecoder import gnewsdecoder
    except Exception:
        # library missing / import error — fail soft, caller keeps the wrapper
        return None
    try:
        from scripts.news.deadline import with_deadline, TIMED_OUT
    except ImportError:                          # run as a script from scripts/news/
        from deadline import with_deadline, TIMED_OUT
    # `interval` is the library's polite inter-request delay. No timeout kwarg: the
    # pinned version doesn't take one — the hard stop is with_deadline.
    res = with_deadline(lambda u: gnewsdecoder(u, interval=1), url, secs=timeout)
    if res is TIMED_OUT:
        return None
    # the library returns {"status": bool, "decoded_url": str} on success,
    # {"status": False, "message": ...} on failure. Be defensive about shape.
    if isinstance(res, dict) and res.get("status") and res.get("decoded_url"):
        return res["decoded_url"]
    return None
