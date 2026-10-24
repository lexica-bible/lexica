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
_TIME = re.compile(r"<time\b[^>]*\bdatetime\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", re.I)
_LEAD_DAY = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})")

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
    try:
        from dateparse import to_iso           # run as a script from scripts/news/
    except ImportError:
        from scripts.news.dateparse import to_iso
    iso = to_iso(s)
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
    m = _ARTICLE.search(doc)
    region = m.group(0) if m else doc
    for a, b in _TIME.findall(region):
        d = _from_raw(a or b)
        if d:
            return d
    return None


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
    """(date, how) — how is 'jsonld' | 'meta' | 'time' | 'url' | None. Never raises."""
    try:
        doc = html if html is not None else _fetch(url, timeout)
        if doc:
            for how, fn in (("jsonld", _from_jsonld), ("meta", _from_meta), ("time", _from_time)):
                d = fn(doc)
                if d:
                    return d, how
        d = _from_url(url)
        return (d, "url") if d else (None, None)
    except Exception:
        return None, None


def page_date(url, html=None, timeout=TIMEOUT):
    """The article's own date ('YYYY-MM-DD', or 'YYYY-MM' from a /YYYY/MM/ URL), or None."""
    return page_date_detail(url, html, timeout)[0]
