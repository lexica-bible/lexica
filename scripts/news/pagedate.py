#!/usr/bin/env python3
"""pagedate.py — an article's OWN publish date, read off its page.

Why: on the Google News path, the date Google hands us is a discovery/crawl date, not the
article's (spzh.eu check 2026-10-24: five of six "recent" stamps were 2-5 years late). The
page itself says when it ran. This file reads that, and nothing else.

page_date(url) tries, in order, and returns the FIRST hit:
  1. JSON-LD  datePublished            (an Article-type object preferred over any other)
  2. <meta>   og:article:published_time / article:published_time
  3. <time datetime="...">             inside <article> when the page has one, else the page
  4. the URL  a YYYY-MM-DD segment, /YYYY/MM/DD/, or /YYYY/MM/
It returns 'YYYY-MM-DD', or 'YYYY-MM' when only a /YYYY/MM/ URL segment was found, or None.
Two guards (2026-10-25, from the first full dry run): the page's own date sources must AGREE
within 30 days or no date is returned (a page that contradicts itself is not a witness), and a
<time> tag only counts when the article area carries exactly one date. See page_date_detail.

The day is the page's OWN calendar day as written (the date part of '2021-12-01T00:51+02:00'
is 2021-12-01 — what the byline prints), not a UTC conversion that could slide it a day.

Network: ONE GET, 10s timeout. Every failure (timeout, HTTP error, junk HTML) returns None —
this never raises. Pass `html=` to read a page you already have (the tests do).
"""
import json
import re
import html as _html
import urllib.request
from datetime import date

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
TIMEOUT = 10
MAX_BYTES = 3_000_000          # a news page is far smaller; this only stops a runaway body

_ARTICLE_TYPES = {"article", "newsarticle", "blogposting", "reportagenewsarticle",
                  "analysisnewsarticle", "opinionnewsarticle", "backgroundnewsarticle",
                  "reviewnewsarticle", "scholarlyarticle", "techarticle", "report",
                  "liveblogposting"}
_META_KEYS = {"og:article:published_time", "article:published_time"}

_LD = re.compile(r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                 re.I | re.S)
_LD_LOOSE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"')
_META = re.compile(r"<meta\b[^>]*>", re.I)
_ATTR = re.compile(r'([\w:.-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')')
_ARTICLE = re.compile(r"<article\b.*?</article>", re.I | re.S)
_LEAD_DAY = re.compile(r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)")   # 2014-07-01 and 2014-7-1
_NUMERIC = re.compile(r"(?<!\d)(\d{1,2})[/.](\d{1,2})[/.](\d{4})(?!\d)")
_WEEKDAY = re.compile(r"^\s*(mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+", re.I)
# a <time> tag with its attributes AND its printed text (the text is a second witness)
_TIME_FULL = re.compile(r"<time\b([^>]*)>([^<]*)", re.I)

# URL segments, most specific first
_URL_ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
_URL_YMD = re.compile(r"/(\d{4})/(\d{2})/(\d{2})(?=/|$)")
_URL_YM = re.compile(r"/(\d{4})/(\d{2})(?=/|$)")


def _ok_year(y):
    return 1990 <= y <= date.today().year + 1


def _day(y, m, d):
    """'YYYY-MM-DD' if it's a real calendar day in range, else None."""
    try:
        y, m, d = int(y), int(m), int(d)
        date(y, m, d)
    except (TypeError, ValueError):
        return None
    return f"{y:04d}-{m:02d}-{d:02d}" if _ok_year(y) else None


def _from_raw(raw):
    """A page-written date string -> its own calendar day. ISO-shaped strings keep the day
    exactly as written (no timezone shift); anything else goes through the shared tolerant
    parser (dateparse.to_iso), whose UTC day is the best we can do for a non-ISO string."""
    s = _html.unescape((raw or "").strip())
    if not s:
        return None
    m = _LEAD_DAY.match(s)
    if m:
        return _day(*m.groups())
    # Numeric day/month dates ("01/07/2026", "01.07.2026"): the order is only certain when one
    # number is over 12. Both 12 or under (and different) = US vs European is a GUESS -> None.
    # (middle-east-online 26995, 2026-10-25: "Wednesday 01/07/2026" was 1 July — Vance's Fox
    # remarks of Tue 30 June — not 7 January; both dates were Wednesdays.)
    m = _NUMERIC.search(s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), m.group(3)
        if a > 12 and b <= 12:
            return _day(y, b, a)                    # day first
        if b > 12 and a <= 12:
            return _day(y, a, b)                    # month first
        if a == b:
            return _day(y, a, b)
        return None
    try:
        from dateparse import to_iso           # run as a script from scripts/news/
    except ImportError:
        from scripts.news.dateparse import to_iso
    iso = to_iso(s) or to_iso(_WEEKDAY.sub("", s))   # "Sun, 16 May 2021" -> "16 May 2021"
    m = _LEAD_DAY.match(iso or "")
    return _day(*m.groups()) if m else None


def _walk_ld(node, out):
    """Collect (is_article, datePublished) from every object in a JSON-LD tree, in order."""
    if isinstance(node, list):
        for x in node:
            _walk_ld(x, out)
    elif isinstance(node, dict):
        dp = node.get("datePublished")
        if isinstance(dp, str) and dp.strip():
            t = node.get("@type")
            types = t if isinstance(t, list) else [t]
            is_art = any(isinstance(x, str) and x.lower() in _ARTICLE_TYPES for x in types)
            out.append((is_art, dp))
        for v in node.values():
            if isinstance(v, (dict, list)):
                _walk_ld(v, out)


def _from_jsonld(doc):
    found = []
    for block in _LD.findall(doc):
        try:
            _walk_ld(json.loads(block.strip(), strict=False), found)
        except ValueError:
            # malformed JSON-LD (trailing commas etc.) — still read a plain datePublished
            found += [(False, v) for v in _LD_LOOSE.findall(block)]
    # an Article-type object's date beats a WebPage/Organization date on the same page
    ordered = [raw for is_art, raw in found if is_art] + [raw for is_art, raw in found if not is_art]
    for raw in ordered:
        d = _from_raw(raw)
        if d:
            return d
    return None


def _from_meta(doc):
    for tag in _META.findall(doc):
        attrs = {k.lower(): (a if a is not None and a != "" else b)
                 for k, a, b in _ATTR.findall(tag)}
        key = (attrs.get("property") or attrs.get("name") or "").strip().lower()
        if key in _META_KEYS:
            d = _from_raw(attrs.get("content"))
            if d:
                return d
    return None


def _from_time(doc):
    """The one date in the article's <time datetime> tags — ONLY when it is unambiguous. The
    region is the page's single <article> when it has exactly one, else the whole page; if that
    region carries more than one distinct day it's a list of stories (a "latest" box, related
    links), not a byline, and nothing is returned. (nssmag 18052, 2026-10-25: two <article>s,
    six dates; the first was a sidebar story's Oct 17.)"""
    arts = _ARTICLE.findall(doc)
    region = arts[0] if len(arts) == 1 else doc
    days = set()
    for attr_s, text in _TIME_FULL.findall(region):
        days |= _time_days(attr_s, text)
    return days.pop() if len(days) == 1 else None


def _attrs(s):
    return {k.lower(): (a if a is not None and a != "" else b) for k, a, b in _ATTR.findall(s)}


def _time_days(attr_s, text):
    """The days ONE <time> tag claims: its datetime attribute AND its printed text, when the text
    is a readable full date. Two witnesses on one tag — they must agree like any others.
    (gdnonline 20987, 2026-10-25: datetime="2017-12-05..." printed "Sun, 16 May 2021" — the
    site's tag is broken; the printed day, matching the Kerry/COP26 Vatican visit, is right.)"""
    out = set()
    for raw in ((_attrs(attr_s).get("datetime") or ""), text):
        d = _from_raw(raw)
        if d:
            out.add(d)
    return out


def _byline_days(doc):
    """Days the page marks as its PUBLISH date outside the data block: a <time> whose class says
    'published' (WordPress 'entry-date published') — both its datetime and its printed text — or
    any tag with itemprop="datePublished". Used only to cross-check the other sources (see
    page_date_detail)."""
    out = set()
    for attr_s, text in _TIME_FULL.findall(doc):
        a = _attrs(attr_s)
        cls = (a.get("class") or "").lower().split()
        if "published" in cls or (a.get("itemprop") or "").strip().lower() == "datepublished":
            out |= _time_days(attr_s, text)
    for tag in re.findall(r"<(?:meta|span|div|p)\b[^>]*>", doc, re.I):
        a = _attrs(tag)
        if (a.get("itemprop") or "").strip().lower() == "datepublished":
            d = _from_raw(a.get("datetime") or a.get("content"))
            if d:
                out.add(d)
    return out


def _spread_days(days):
    """Largest gap in days among full 'YYYY-MM-DD' strings (0 for fewer than two)."""
    ds = sorted(date.fromisoformat(d) for d in days if len(d) == 10)
    return (ds[-1] - ds[0]).days if len(ds) > 1 else 0


AGREE_DAYS = 30   # the page's own date sources must agree within this many days, or it's unverified


def _from_url(url):
    u = (url or "").split("?", 1)[0].split("#", 1)[0]
    for rx in (_URL_ISO, _URL_YMD):
        for g in rx.findall(u):
            d = _day(*g)
            if d:
                return d
    for y, m in _URL_YM.findall(u):
        if _ok_year(int(y)) and 1 <= int(m) <= 12:
            return f"{int(y):04d}-{int(m):02d}"
    return None


def _fetch(url, timeout=TIMEOUT):
    """One GET; the decoded body, or None on any failure."""
    if not (url or "").lower().startswith(("http://", "https://")):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "text/html,*/*;q=0.8"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_BYTES)
            charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")
    except Exception:
        return None


def page_date_detail(url, html=None, timeout=TIMEOUT):
    """(date, how) — how is 'jsonld' | 'meta' | 'time' | 'url', or (None, 'conflict') when the
    page contradicts itself, or (None, None). Never raises.

    CROSS-CHECK: every date the page offers as its publish date — JSON-LD, the published_time
    meta, a byline marked 'published', and a full date in the URL — must agree within
    AGREE_DAYS. If they don't, the page is not a trustworthy witness and NO date is returned
    (the row stays unverified). Picking one side would be guessing. (ipi.media 18094,
    2026-10-25: JSON-LD + meta said 2021-12-17 — a repost/migration date — while the printed
    byline said July 13, 2017, which is right.) When they agree, the ruled order picks."""
    try:
        doc = html if html is not None else _fetch(url, timeout)
        u = _from_url(url)
        if doc:
            j, m = _from_jsonld(doc), _from_meta(doc)
            byline = _byline_days(doc)
            witnesses = {d for d in (j, m) if d} | byline | ({u} if u and len(u) == 10 else set())
            if _spread_days(witnesses) > AGREE_DAYS:
                return None, "conflict"
            if j:
                return j, "jsonld"
            if m:
                return m, "meta"
            if len(byline) == 1:
                return next(iter(byline)), "time"
            t = _from_time(doc)
            if t:
                if u and len(u) == 10 and _spread_days({t, u}) > AGREE_DAYS:
                    return None, "conflict"
                return t, "time"
        return (u, "url") if u else (None, None)
    except Exception:
        return None, None


def page_date(url, html=None, timeout=TIMEOUT):
    """The article's own date ('YYYY-MM-DD', or 'YYYY-MM' from a /YYYY/MM/ URL), or None."""
    return page_date_detail(url, html, timeout)[0]
