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
    # Google's AMP viewer (seen on The Hill, 2026-10-25 report)
    "amp_gsa", "amp_js_v", "usqp",
    # MSN page-rendering switches (seen 2026-10-25: the same ar-/gm- page with and without them)
    "uxmode", "apiversion", "batchservertelemetry", "domshim", "noservercache",
    "noservertelemetry", "renderwebcomponents", "wcseo",
}
# Parameters that are tracking only with one specific value (Substack's ?action=share).
_TRACKING_VALUE = {("action", "share")}

# Second names for the same site, each seen serving the identical article path (2026-10-25
# report): cnn.com / edition.cnn.com, bbc.com / bbc.co.uk, philstar.com / qa.philstar.com.
_HOST_ALIAS = {"edition.cnn.com": "cnn.com", "bbc.co.uk": "bbc.com",
               "qa.philstar.com": "philstar.com"}

# MSN names a page by its id (ar-AA25Dyd0, gm-GM66ED0EE4); the words before it change when
# MSN edits the headline ("didnt" -> "didn-t") but it's the same page.
_MSN_ID = re.compile(r"^(ar|gm|vi|ss|cg)-[A-Za-z0-9]+$")


def _is_tracking(key, value=""):
    k = key.lower()
    return (k in _TRACKING or k.startswith("utm_")
            or (k, (value or "").lower()) in _TRACKING_VALUE)


def canonical_url(url):
    """A cleaned-up form of an article address, for "same article?" comparison only (never
    shown or stored). Lowercases the host (and maps a site's known second name to its main one),
    drops http/https and a leading "www.", the #part, click-tracking parameters, an "amp" path
    piece, a front-door "index.php/" piece, a ".html"/".htm" ending, and a trailing slash. Keeps
    every other parameter (some sites name the article with ?id=...), sorted. MSN pages key on
    their own id. '' for no address or a Google redirect (a redirect says nothing about the
    article until it's resolved). Every rule here was seen on real duplicate pairs; add a rule
    only from a real pair, never a guess."""
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
    host = _HOST_ALIAS.get(host, host)
    segs = [s for s in (p.path or "").split("/") if s]
    if host == "msn.com" and len(segs) >= 2 and _MSN_ID.match(segs[-1]):
        return f"msn.com/{segs[0].lower()}/{segs[-1]}"
    segs = [s for i, s in enumerate(segs)
            if s.lower() != "amp" and not (s.lower() == "index.php" and i < len(segs) - 1)]
    if segs:
        segs[-1] = re.sub(r"\.html?$", "", segs[-1], flags=re.I) or segs[-1]
    path = "/" + "/".join(segs)
    params = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
              if not _is_tracking(k, v)]
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
    """Outlet + headline, loosened. REPORT ONLY — never a merge key (see the module note).
    Drops only Google's own " - <outlet>" ending (not any " - ..." part: "The Friday Pillar
    Post - June 26" and "- July 3" are different issues), then case and punctuation. The outlet
    is loosened too, so a feed name and Google's name for one outlet line up ("EWTN News (CNA)"
    / "ewtnnews.com", "Vatican News" / "vaticannews.va")."""
    src = (source or "").strip()
    t = (title or "").strip()
    if src and t.lower().endswith(" - " + src.lower()):
        t = t[:-(len(src) + 3)]
    t = " ".join(re.findall(r"[a-z0-9]+", t.lower()))
    return (outlet_key(src), t)


def outlet_key(source):
    """An outlet name loosened for comparison: case, a "(...)" part, www., a web-address ending,
    spaces and punctuation."""
    s = re.sub(r"\(.*?\)", "", (source or "").lower()).strip()
    if " " not in s:
        s = re.sub(r"^www\.", "", s)
        s = re.sub(r"\.[a-z]{2,4}(\.[a-z]{2})?$", "", s)
    return re.sub(r"[^0-9a-zа-яё]+", "", s)


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


def score_rank(row, keeper_id):
    """Which row's AI reading (score, thread, reason, new-angle flag, event label) the survivor
    carries: the HIGHEST score, ties to the survivor itself. So merging only removes the
    duplicate — it never pulls an article below the score floor. (2026-10-25 report: keeping
    the RSS copy's own score would have dropped 21 articles out of the 5+ Inbox, e.g. the
    Vatican News death-penalty piece, RSS copy 3 / Google copy 7.)"""
    sc = row["score"]
    return (sc is not None, sc or 0, row["id"] == keeper_id)


def plan_merges(rows, key=None):
    """Group rows that share an article_key (or `key(row)` when given — merge_dups.py passes one
    that also honors the page's own main-address tag). Returns a list of (key, keeper, [losers])
    for every key with 2+ rows, keeper picked by keeper_rank. Rows with no key are left alone."""
    key = key or article_key
    by_key = {}
    for r in rows:
        k = key(r)
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
