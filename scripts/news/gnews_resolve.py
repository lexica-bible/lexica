#!/usr/bin/env python3
"""gnews_resolve.py — the ONE home for Google News wrapper-URL knowledge.

A Google News RSS link (news.google.com/rss/articles/<token>) hides the real
article URL. The AU_yqL "opaque" tokens can't be decoded locally — they need a
batchexecute round-trip to Google. We lean on the version-pinned PyPI package
`googlenewsdecoder` for that handshake so all the format-specific fragility
lives behind this one function.

Contract:
  - resolve(url, timeout=8.0) -> clean URL string, or None.
  - NEVER raises. A 429, a timeout, a parse failure, an unknown format, a
    non-wrapper URL that slips in — all return None. The caller keeps the
    original wrapper on None (fail soft), so a Google format change breaks
    exactly this function and nothing downstream.

If Google changes the token format, only resolve() breaks and it fails to None.
Re-pin / patch here; nothing else needs to know.
"""

WRAPPER_MARK = "news.google.com/rss/articles/"


def is_wrapper(url):
    """True if this is a Google News RSS wrapper that needs resolving."""
    return bool(url) and WRAPPER_MARK in url


def resolve(url, timeout=8.0):
    """Resolve one Google News wrapper to its real article URL, or None.

    Never raises — every failure path returns None so copy/backfill can fall
    back to the wrapper untouched.
    """
    if not is_wrapper(url):
        return None
    try:
        from googlenewsdecoder import gnewsdecoder
    except Exception:
        # library missing / import error — fail soft, caller keeps the wrapper
        return None
    try:
        # `interval` is the library's polite inter-request delay; `timeout` caps
        # the network wait. Both are passed defensively — older builds ignore
        # unknown kwargs via the TypeError retry below.
        try:
            res = gnewsdecoder(url, interval=1, timeout=timeout)
        except TypeError:
            res = gnewsdecoder(url, interval=1)
    except Exception:
        return None
    # the library returns {"status": bool, "decoded_url": str} on success,
    # {"status": False, "message": ...} on failure. Be defensive about shape.
    if isinstance(res, dict) and res.get("status") and res.get("decoded_url"):
        return res["decoded_url"]
    return None
