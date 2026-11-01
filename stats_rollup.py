#!/usr/bin/env python3
"""Visitor stats — the data layer behind views_stats.py (no Flask here, so the
tests can drive it with a throwaway in-memory db).

Two tables in notes.db:
  visits        — one row per page load (raw). Kept RAW_KEEP_DAYS days, then dropped,
                  but ONLY for days already frozen into visits_daily.
  visits_daily  — per-day totals: (day, dim, key) -> views, uniques. One row per value
                  of each dimension, so every dimension's uniques are exact for that day
                  (summing finer cells would double-count a visitor who landed twice).
                  dim 'total' (key '') doubles as the "this day is frozen" marker.

A finished day (before today, UTC) is frozen once and never re-counted. Today is
always counted live from the raw rows. Running rollup() again is harmless.

"Unique visitors" over a range = the sum of each day's uniques. The visitor hash
changes every day by design (it can't be linked across days), so a person who
comes on 3 days counts 3 times — same meaning the dashboard has always had.

Privacy: nothing here stores an IP, a cookie, or a raw browser string. `ua` is just
'mobile'/'desktop'; `gap` is "days since this browser's last visit", which the
browser works out itself and sends as a number.
"""
import datetime
import re
from urllib.parse import parse_qs, urlsplit

RAW_KEEP_DAYS = 90
UNKNOWN = "?"          # key for rows from before a dimension was recorded
SURFACES = ("library", "lexicon", "corpus", "notes", "study", "news", "about")
TEXTS = ("abp", "kjv", "bsb", "heb", "esv", "niv")
RANGES = {"7d": 7, "30d": 30, "90d": 90, "all": None}

# dim -> the column (or expression) it groups on. 'path' keys carry their surface
# in front ("library /?b=Jhn&c=3") so the page table can group paths under it.
_DIM_EXPR = {
    "surface": "surface",
    "path": "surface || ' ' || path",
    "ref": "ref",
    "ua": "ua",
    "acct": "acct",
    "gap": "gap",
}
_NEW_COLS = (("surface", "TEXT"), ("path", "TEXT"), ("ua", "TEXT"),
             ("acct", "INTEGER"), ("gap", "INTEGER"))


# ── tables ───────────────────────────────────────────────────────────────────
def ensure(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS visits ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL, ts INTEGER NOT NULL,"
        " visitor TEXT NOT NULL, ref TEXT)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_visits_day ON visits(day)")
    have = {r[1] for r in conn.execute("PRAGMA table_info(visits)")}
    for name, typ in _NEW_COLS:
        if name not in have:
            conn.execute(f"ALTER TABLE visits ADD COLUMN {name} {typ}")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS visits_daily ("
        " day TEXT NOT NULL, dim TEXT NOT NULL, key TEXT NOT NULL,"
        " views INTEGER NOT NULL, uniques INTEGER NOT NULL,"
        " PRIMARY KEY (day, dim, key))")
    conn.commit()


# ── cleaning what the browser sends ──────────────────────────────────────────
_MOBILE_MARKS = ("mobi", "iphone", "ipod", "ipad", "android", "tablet", "silk/",
                 "kindle", "opera mini")


def ua_family(ua):
    """'mobile' (phones + tablets) or 'desktop', from the browser string. Only this
    word is stored, never the string itself."""
    s = (ua or "").lower()
    return "mobile" if any(m in s for m in _MOBILE_MARKS) else "desktop"


_BOOK_RE = re.compile(r"^[A-Za-z0-9]{1,12}$")
_STRONGS_RE = re.compile(r"^[GHgh]\d{1,5}(\.\d{1,2})?[a-zA-Z]?$")
_PATHNAME_RE = re.compile(r"^/[A-Za-z0-9/_.-]{0,60}$")


def clean_path(raw):
    """The landing address, reduced to the parts worth counting. Only known
    parameters survive; secrets (a News share key, a password-reset token) are
    reduced to a bare flag so they're never stored."""
    if not isinstance(raw, str) or len(raw) > 500:
        return "/"
    try:
        parts = urlsplit(raw)
        q = parse_qs(parts.query, keep_blank_values=True)
    except ValueError:
        return "/"
    pathname = parts.path or "/"
    if not _PATHNAME_RE.match(pathname):
        pathname = "/"
    one = lambda k: (q.get(k) or [""])[0]
    keep = []
    if "news" in q:
        keep.append("news")
    elif "reset" in q:
        keep.append("reset")
    elif one("lex"):
        if _STRONGS_RE.match(one("lex")):
            keep.append("lex=" + one("lex").upper())
    elif one("b"):
        if _BOOK_RE.match(one("b")):
            keep.append("b=" + one("b"))
            c = one("c")
            if c.isdigit() and 0 < int(c) <= 200:
                keep.append("c=" + str(int(c)))
            if one("t").lower() in TEXTS:
                keep.append("t=" + one("t").lower())
    return pathname + ("?" + "&".join(keep) if keep else "")


def clean_surface(raw):
    return raw if raw in SURFACES else UNKNOWN


def clean_gap(raw):
    """-1 = first visit this browser remembers; 1.. = days since its last visit day;
    None = the browser couldn't say (storage blocked)."""
    if isinstance(raw, bool) or not isinstance(raw, int):
        return None
    if raw == -1 or 1 <= raw <= 3650:
        return raw
    return None


# ── referrers ────────────────────────────────────────────────────────────────
# Search engines, matched on the host we store (already lower-cased, "www." removed).
# Only the engine's own search host counts — news.google.com / mail.google.com are
# other sites, not searches.
_SEARCH = (
    (re.compile(r"^com\.google\.android\.googlequicksearchbox$"), "Google (Android)"),
    (re.compile(r"^google(\.[a-z]{2,3}){1,2}$"), "Google"),
    (re.compile(r"^([a-z]{2}\.)?bing\.com$"), "Bing"),
    (re.compile(r"^duckduckgo\.com$"), "DuckDuckGo"),
    (re.compile(r"^([a-z]{2}\.)?search\.yahoo\.com$|^yahoo\.com$"), "Yahoo"),
    (re.compile(r"^yandex(\.[a-z]{2,3}){1,2}$"), "Yandex"),
    (re.compile(r"^ecosia\.org$"), "Ecosia"),
    (re.compile(r"^search\.brave\.com$"), "Brave Search"),
    (re.compile(r"^baidu\.com$"), "Baidu"),
    (re.compile(r"^startpage\.com$"), "Startpage"),
    (re.compile(r"^qwant\.com$"), "Qwant"),
)


def classify_ref(host):
    """('search', engine name) or ('site', host)."""
    for rx, name in _SEARCH:
        if rx.match(host or ""):
            return "search", name
    return "site", host


# ── days ─────────────────────────────────────────────────────────────────────
def day_add(day, n):
    return (datetime.date.fromisoformat(day) + datetime.timedelta(days=n)).isoformat()


def day_span(a, b):
    """Every day from a to b inclusive."""
    out, d = [], a
    while d <= b:
        out.append(d)
        d = day_add(d, 1)
    return out


# ── freezing finished days ───────────────────────────────────────────────────
def aggregate_day(conn, day):
    """One day's counts from the raw rows: [(dim, key, views, uniques), ...]."""
    r = conn.execute("SELECT count(*), count(DISTINCT visitor) FROM visits WHERE day = ?",
                     (day,)).fetchone()
    if not r or not r[0]:
        return []
    out = [("total", "", r[0], r[1])]
    for dim, expr in _DIM_EXPR.items():
        for k, v, u in conn.execute(
                f"SELECT {expr} AS k, count(*), count(DISTINCT visitor) FROM visits"
                " WHERE day = ? GROUP BY k", (day,)):
            out.append((dim, UNKNOWN if k is None else str(k), v, u))
    return out


def rollup(conn, today):
    """Freeze every finished day that isn't frozen yet, then drop raw rows older
    than RAW_KEEP_DAYS — but only for days that are frozen, so nothing is lost."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        days = [r[0] for r in conn.execute(
            "SELECT DISTINCT day FROM visits WHERE day < ? AND day NOT IN"
            " (SELECT day FROM visits_daily WHERE dim = 'total')", (today,))]
        for d in days:
            conn.executemany(
                "INSERT OR REPLACE INTO visits_daily (day, dim, key, views, uniques)"
                " VALUES (?,?,?,?,?)", [(d,) + row for row in aggregate_day(conn, d)])
        cutoff = day_add(today, -RAW_KEEP_DAYS)
        conn.execute(
            "DELETE FROM visits WHERE day < ? AND day IN"
            " (SELECT day FROM visits_daily WHERE dim = 'total')", (cutoff,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return len(days)


def load_days(conn, today, lo=""):
    """{day: {dim: {key: (views, uniques)}}} for every day >= lo up to today. Frozen
    days come from visits_daily; anything not frozen (today, or a day a failed
    rollup missed) is counted live from the raw rows."""
    out = {}
    for day, dim, key, v, u in conn.execute(
            "SELECT day, dim, key, views, uniques FROM visits_daily WHERE day >= ?", (lo,)):
        out.setdefault(day, {}).setdefault(dim, {})[key] = (v, u)
    live = [r[0] for r in conn.execute(
        "SELECT DISTINCT day FROM visits WHERE day >= ? AND day NOT IN"
        " (SELECT day FROM visits_daily WHERE dim = 'total')", (lo,))]
    for d in live:
        for dim, key, v, u in aggregate_day(conn, d):
            out.setdefault(d, {}).setdefault(dim, {})[key] = (v, u)
    return out


# ── the summary the page shows ───────────────────────────────────────────────
def _median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _first_tracked(days, dim):
    """First day that has real (not UNKNOWN) values for a dimension, or None."""
    for d in sorted(days):
        keys = days[d].get(dim, {})
        if any(k != UNKNOWN for k in keys):
            return d
    return None


def summarize(days, today, range_key, accounts):
    """Everything the Stats page shows, for one range. `days` is load_days() output
    (must reach back far enough for the prior period + 30 days of spike history);
    `accounts` is [{email, created, last_seen, owner}]."""
    n = RANGES.get(range_key, 30)
    first = min(days) if days else today
    if n is None:
        start, prior = min(first, today), None
    else:
        start = day_add(today, -(n - 1))
        prior = (day_add(start, -n), day_add(start, -1))
    rng = day_span(start, today)

    def tot(d, i):
        return days.get(d, {}).get("total", {}).get("", (0, 0))[i]

    def views_in(a, b):
        return sum(tot(d, 0) for d in day_span(a, b))

    def uniq_in(a, b):
        return sum(tot(d, 1) for d in day_span(a, b))

    def dim_sum(dim, a, b):
        acc = {}
        for d in day_span(a, b):
            for k, (v, u) in days.get(d, {}).get(dim, {}).items():
                if k == UNKNOWN:
                    continue
                pv, pu = acc.get(k, (0, 0))
                acc[k] = (pv + v, pu + u)
        return acc

    def kpi(v, p):
        return {"v": v, "prior": p}

    yday = day_add(today, -1)
    k = {
        "uniques": kpi(uniq_in(start, today), uniq_in(*prior) if prior else None),
        "views": kpi(views_in(start, today), views_in(*prior) if prior else None),
        "today": kpi(tot(today, 0), tot(yday, 0)),
        "last7": kpi(views_in(day_add(today, -6), today),
                     views_in(day_add(today, -13), day_add(today, -7))),
        "last30": kpi(views_in(day_add(today, -29), today),
                      views_in(day_add(today, -59), day_add(today, -30))),
    }

    # Returning: a daily visitor whose browser had also been here earlier in the
    # SAME window. Counted per day (like uniques). Share is out of the daily
    # visitors whose browser could say (gap known).
    gap_since = _first_tracked(days, "gap")

    def returning(a, b):
        ret = known = 0
        for d in day_span(a, b):
            for key, (_v, u) in days.get(d, {}).get("gap", {}).items():
                if key == UNKNOWN:
                    continue
                known += u
                g = int(key)
                if g >= 1 and day_add(d, -g) >= a:
                    ret += u
        return ret, known

    r_now, r_known = returning(start, today)
    r_prior = None
    if prior and gap_since and gap_since <= prior[0]:
        r_prior = returning(*prior)[0]
    k["returning"] = {"v": r_now, "prior": r_prior, "known": r_known, "since": gap_since}

    # Accounts: total now vs total at the start of the window.
    created_day = lambda a: (a.get("created") or "")[:10]
    k["accounts"] = kpi(len(accounts),
                        sum(1 for a in accounts if created_day(a) < start) if prior else None)

    # Chart: every day in range (zero-filled), with that day's top referrer.
    def top_ref(d):
        refs = {r: v for r, (v, _u) in days.get(d, {}).get("ref", {}).items() if r != UNKNOWN}
        return max(refs, key=lambda r: (refs[r], r)) if refs else None

    by_day = [{"day": d, "views": tot(d, 0), "uniques": tot(d, 1)} for d in rng]

    # Spikes: a day above 5x the median of the 30 days before it (zero days count).
    # Needs at least 7 days of history; a median under 1 counts as 1.
    spikes = []
    for row in by_day:
        d = row["day"]
        hist = [x for x in day_span(max(first, day_add(d, -30)), day_add(d, -1))]
        if len(hist) < 7:
            continue
        med = max(1, _median([tot(x, 0) for x in hist]))
        if row["views"] > 5 * med:
            spikes.append({"day": d, "views": row["views"], "median": med,
                           "top_ref": top_ref(d)})

    # Devices (views in range).
    ua = dim_sum("ua", start, today)
    devices = {"mobile": ua.get("mobile", (0, 0))[0], "desktop": ua.get("desktop", (0, 0))[0],
               "since": _first_tracked(days, "ua")}

    # Pages: surfaces, each with its paths; 14-day sparkline per row.
    spark_days = day_span(day_add(today, -13), today)

    def spark(dim, key):
        return [days.get(d, {}).get(dim, {}).get(key, (0, 0))[0] for d in spark_days]

    surf = dim_sum("surface", start, today)
    paths = dim_sum("path", start, today)
    pages_total = sum(v for v, _u in surf.values())
    pages = []
    for s, (v, u) in sorted(surf.items(), key=lambda kv: (-kv[1][0], kv[0])):
        plist = []
        for key, (pv, pu) in paths.items():
            sname, _, p = key.partition(" ")
            if sname == s:
                plist.append({"path": p, "views": pv, "uniques": pu, "spark": spark("path", key)})
        plist.sort(key=lambda r: (-r["views"], r["path"]))
        pages.append({"surface": s, "views": v, "uniques": u,
                      "spark": spark("surface", s), "paths": plist[:200]})

    # Referrers: direct on its own line; the rest split into search engines / sites.
    ref_now = dim_sum("ref", start, today)
    ref_prior = dim_sum("ref", *prior) if prior else {}
    direct = ref_now.get("direct", (0, 0))[0]
    groups = {}
    for host in set(ref_now) | set(ref_prior):
        if host == "direct":
            continue
        kind, label = classify_ref(host)
        g = groups.setdefault((kind, label), {"name": label, "n": 0, "prior": 0, "hosts": []})
        g["n"] += ref_now.get(host, (0, 0))[0]
        g["prior"] += ref_prior.get(host, (0, 0))[0]
        g["hosts"].append(host)
    non_direct = sum(g["n"] for g in groups.values())
    order = lambda g: (-g["n"], g["name"])
    refs = {
        "direct": direct, "views": k["views"]["v"], "non_direct": non_direct,
        "has_prior": prior is not None,
        "search": sorted([g for (kind, _), g in groups.items() if kind == "search" and g["n"]], key=order),
        "other": sorted([g for (kind, _), g in groups.items() if kind == "site" and g["n"]], key=order),
    }
    for g in refs["search"] + refs["other"]:
        g["hosts"].sort()

    # Accounts: new = signed up in range; active = seen (a signed-in visit or a
    # sign-in) in range.
    acc_list = sorted(accounts, key=lambda a: (a.get("last_seen") or "", a.get("created") or ""),
                      reverse=True)
    accounts_out = {
        "total": len(accounts),
        "new": sum(1 for a in accounts if created_day(a) >= start),
        "active": sum(1 for a in accounts if (a.get("last_seen") or "") >= start),
        "list": acc_list,
    }

    return {
        "range": range_key if range_key in RANGES else "30d",
        "start": start, "today": today, "prior": list(prior) if prior else None,
        "kpi": k, "by_day": by_day, "spikes": spikes, "devices": devices,
        "pages": pages, "pages_total": pages_total,
        "pages_since": _first_tracked(days, "surface"),
        "refs": refs, "accounts": accounts_out,
    }


def load_lo(today, range_key):
    """How far back summarize() needs data: the prior window plus 30 days of spike
    history, and 60 days for the fixed last-30 tile's prior. '' = everything."""
    n = RANGES.get(range_key, 30)
    if n is None:
        return ""
    return day_add(today, -(2 * n + 30 + 60))
