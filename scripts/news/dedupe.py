#!/usr/bin/env python3
"""dedupe.py — the ONE home for "are these two rows the same article?" in news.db.

Why it exists (2026-10-25): Google News hands out a NEW redirect link
(news.google.com/rss/articles/<token>) for the same article on different pulls, so the
url-is-unique check at ingest never matches and the same article lands twice. Two rows of one
article can get two different event labels (the labeler is run per night, see TODO.md) and then
show as two cards — e.g. NewsNation "Catholic AI task force announced by US bishops".

THE KEY: the article's real address, cleaned up (canonical_url). For a Google row that's its
resolved_url (looked up by the nightly face/page-date step); for an RSS row it's its own url.
Two rows with the same cleaned address are the same article — merged by merge_dups.py.

NOT a key, on purpose: title + outlet (+ date). Same outlet + same headline can be two different
articles (recurring column titles), and Google's dates are unreliable (a known pair carries
2024-11-21 vs 2021-02-18). merge_dups.py only REPORTS title matches, so a gap in the address
clean-up shows up there instead of being papered over.

Pure functions only (no network, no database writes) — merge_dups.py and the tests share them.
"""
import re
import urllib.parse

WRAPPER_MARK = "news.google.com/"

# Query parameters that only track where a click came from — never part of which page it is.
# Kept to names that are unambiguous: dropping a parameter that DID name the article would merge
# two different articles (destructive), while missing one only leaves a duplicate visible (and
# merge_dups.py's title report shows it). So generic names like "id", "ref" or "src" stay.
_TRACKING = {
    "fbclid", "gclid", "dclid", "msclkid", "ocid", "oc", "cmpid", "cmp", "smid", "smtyp",
    "mc_cid", "mc_eid", "ito", "taid", "ncid", "guccounter", "guce_referrer",
    "guce_referrer_sig", "sr_share", "soc_src", "soc_trk", "amp", "outputtype",
    "ref_src", "at_medium", "at_campaign",
}


def _is_tracking(key):
    k = key.lower()
    return k in _TRACKING or k.startswith("utm_")


def canonical_url(url):
    """A cleaned-up form of an article address, for "same article?" comparison only (never
    shown or stored). Lowercases the host, drops http/https and a leading "www.", the #part,
    click-tracking parameters, an AMP tail ("/amp" path end), and a trailing slash. Keeps every
    other parameter (some sites name the article with ?id=...), sorted. '' for no address or a
    Google redirect (a redirect says nothing about the article until it's resolved)."""
    u = (url or "").strip()
    if not u or WRAPPER_MARK in u:
        return ""
    try:
        p = urllib.parse.urlsplit(u)
    except ValueError:
        return ""
    if p.scheme.lower() not in ("http", "https") or not p.hostname:
        return ""
    host = p.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path or "/"
    path = re.sub(r"/amp/?$", "/", path, flags=re.I)
    if len(path) > 1:
        path = path.rstrip("/") or "/"
    params = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
              if not _is_tracking(k)]
    q = urllib.parse.urlencode(sorted(params))
    return host + path + ("?" + q if q else "")


def article_key(row):
    """The same-article key for one items row: its resolved address if it has one, else its own
    url when that's already a direct article link (RSS rows). '' = unknown (an unresolved Google
    redirect) — such a row is never merged."""
    keys = row.keys() if hasattr(row, "keys") else row
    ru = row["resolved_url"] if "resolved_url" in keys else None
    return canonical_url(ru) or canonical_url(row["url"])


def title_key(title, source):
    """Outlet + headline, loosened (case, punctuation, a trailing " - Outlet"). REPORT ONLY —
    never a merge key (see the module note)."""
    t = (title or "").lower()
    t = re.sub(r"\s+[-–—|]\s+[^-–—|]+$", "", t)
    t = " ".join(re.findall(r"[a-z0-9]+", t))
    return ((source or "").strip().lower(), t)


def is_rss(row):
    return (row["query"] or "").startswith("rss:")


def keeper_rank(row):
    """Which row of a duplicate set survives (highest wins):
      1. an RSS row — the outlet's own feed date is authoritative;
      2. a page-verified date (published_src 'page', no flag), then any page date;
      3. scored, then labeled (keeps the AI work already paid for);
      4. the earliest-pulled (lowest id) — stable tie-break."""
    keys = row.keys()
    src = row["published_src"] if "published_src" in keys else None
    flag = row["date_flag"] if "date_flag" in keys else None
    ev = row["event"] if "event" in keys else None
    return (is_rss(row),
            src == "page" and not flag,
            src == "page",
            row["score"] is not None,
            bool((ev or "").strip()),
            -row["id"])


def plan_merges(rows):
    """Group rows that share an article_key. Returns a list of (keeper, [losers]) for every
    key with 2+ rows, keeper picked by keeper_rank. Rows with no key are left alone."""
    by_key = {}
    for r in rows:
        k = article_key(r)
        if k:
            by_key.setdefault(k, []).append(r)
    plans = []
    for k, grp in by_key.items():
        if len(grp) < 2:
            continue
        grp = sorted(grp, key=keeper_rank, reverse=True)
        plans.append((k, grp[0], grp[1:]))
    plans.sort(key=lambda p: p[1]["id"])
    return plans


MERGED_TABLE = "items_merged"


def merged_urls(conn):
    """Every url already merged away (merge_dups.py keeps the removed row in items_merged).
    Ingest skips these so a merged-away link that turns up again isn't stored and paid to
    score a second time. Empty set when the table doesn't exist yet."""
    try:
        return {r[0] for r in conn.execute(f"SELECT url FROM {MERGED_TABLE}") if r[0]}
    except Exception:
        return set()
