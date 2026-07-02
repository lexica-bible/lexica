#!/usr/bin/env python3
"""News watch — admin-only review tab for the end-times news gatherer.

The data is gathered + AI-scored OFFLINE by scripts/news/ (gather_news.py +
score_news.py) into news.db. This blueprint just SERVES that file to the in-app
tab, admin-gated (404 to everyone else, exactly like visitor stats):

  GET  /api/news/meta             → {owner, available, labels, reviewer}
  GET  /api/news/counts?...       → window-scoped inbox/kept/dismissed card tallies
  GET  /api/news/list?...         → stories (near-duplicates grouped into one card)
  POST /api/news/status           → mark a story keep / dismiss / new

Read-mostly: the only write is flipping an article's review status. It never
gathers or scores (that's the offline scripts' job) and never touches bible.db.
"""
import datetime
import hashlib
import hmac
import json
import math
import os
import re
import sqlite3
from collections import Counter

from flask import Blueprint, jsonify, request

from core import news_db, NEWS_DB, limiter, notes_db
from views_notes import is_admin, ai_caller

bp = Blueprint("news", __name__)

# Display names for the gatherer's 13 threads. KEEP IN SYNC with the THREADS keys
# in scripts/news/queries.py (small + static, so duplicated here rather than
# importing across the scripts/ boundary). "new" = the AI flagged a fresh angle.
THREAD_LABELS = {
    "papacy_moral_authority": "Papacy as moral authority",
    "american_pope": "Vatican–US relations",
    "encyclical_political": "Encyclicals / doctrine going political",
    "ai_moralized": "Economic/tech control",
    "legislating_morality": "Legislating worship/morality",
    "ecumenism": "Ecumenism (Protestant–Catholic)",
    "ecumenism_orthodox": "Catholic–Orthodox reunion",
    "protestant_collapse": "Protestant / Evangelical collapse",
    "alien_agenda": "Alien / UFO disclosure",
    "culture_shaping": "Culture shaping",
    "signs_wonders": "Signs & wonders / miracles",
    "political_realignment": "Political realignment",
    "sabbath_sunday": "Sabbath / Sunday law",
    "new": "New angle",
}

# keep/dismiss write a row; "clear" DELETES the reviewer's row so the card is simply
# unreviewed again (absence = inbox — no sentinel to special-case in the counts). "new"
# kept for back-compat (an old client still un-keeps with it; COALESCE treats it as inbox).
_VALID_STATUS = {"new", "keep", "dismiss", "clear"}

# Optional "share link" for a no-login READER (e.g. Tudor). Set NEWS_SHARE_KEY in the
# WSGI env; then /?news=<key> lets someone browse the tab read-only without an account.
# Empty/unset = sharing off (admin only). Writes (keep/dismiss) ALWAYS stay admin-only.
NEWS_SHARE_KEY = os.environ.get("NEWS_SHARE_KEY", "").strip()


def _shared_key_ok():
    if not NEWS_SHARE_KEY:
        return False
    given = (request.args.get("key") or request.headers.get("X-News-Key") or "").strip()
    return bool(given) and hmac.compare_digest(given, NEWS_SHARE_KEY)


def _can_read():
    """Admins always; a valid share-key holder gets read-only access too."""
    return is_admin() or _shared_key_ok()


# Per-reviewer review state. One row per (article, reviewer); the reviewer id is a
# STABLE identity — 'u<user_id>' for an admin, 'k<keytag>' for a share-key holder —
# never a human name, so a future second reviewer can't collide on a literal tag. The
# display name is resolved separately (_reviewer_label), purely for rendering. Kept
# beside items in news.db; items.status stays for back-compat (not migrated).
_REVIEWS_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
  item_id  INTEGER NOT NULL,
  reviewer TEXT NOT NULL,
  status   TEXT NOT NULL,
  updated  TEXT NOT NULL,
  PRIMARY KEY (item_id, reviewer)
);
"""


def _ensure_reviews(conn):
    conn.executescript(_REVIEWS_SCHEMA)


def _key_tag(key):
    """Short stable fingerprint of a share key, so the reviewer id doesn't store the
    secret and a second key gets a different id."""
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _reviewer():
    """Who is reviewing, and may they write.
      admin     -> ('u<user_id>', True)
      share-key -> ('k<keytag>',  True)
      otherwise -> (None, False)
    Admin wins over share-key (branch order) so an admin holding the key still records
    under their own id. Writes are scoped to the returned id, so an admin can never
    write a share-key holder's rows and vice versa — the separation is structural."""
    role, uid = ai_caller()
    if role == "admin" and uid:
        return f"u{uid}", True
    if _shared_key_ok():
        return f"k{_key_tag(NEWS_SHARE_KEY)}", True
    return None, False


def _reviewer_label(rid):
    """Display alias for a reviewer id (rendering only; identity stays the id)."""
    if not rid:
        return ""
    if rid.startswith("u"):
        try:
            conn = notes_db()
            row = conn.execute("SELECT name, email FROM users WHERE id = ?",
                               (int(rid[1:]),)).fetchone()
            conn.close()
            if row:
                return row["name"] or row["email"] or rid
        except (sqlite3.Error, ValueError):
            pass
        return rid
    if rid.startswith("k"):
        return os.environ.get("NEWS_SHARE_NAME", "Reviewer").strip() or "Reviewer"
    return rid

# Words too common to help tell two headlines apart when grouping near-duplicates.
_STOP = set((
    "the a an of to in on for and or with at by from as is are was were be been "
    "his her its their our your s it that this these those new over amid into "
    "after before about out up down off than then but not no will would can could"
).split())


def _available():
    return os.path.exists(NEWS_DB)


def _sig_tokens(title):
    """Significant words of a headline, used to spot duplicate stories. Drops the
    trailing ' - Outlet', lowercases, keeps words of 3+ letters that aren't filler."""
    t = (title or "").lower()
    t = re.sub(r"\s+-\s+[^-]+$", "", t)          # strip the " - Source Name" suffix
    words = re.findall(r"[a-z0-9]+", t)
    return {w for w in words if len(w) >= 3 and w not in _STOP}


_GROUP_SIM = 0.45    # share at least this much of the smaller headline's "rare-word
                     # weight" to count as the SAME story (0..1)
_GROUP_MIN_SHARED = 2   # ...and the headlines must share at least this many significant
                        # words, so one coincidental rare word can't fuse two stories


def _cluster(rows):
    """Group articles that are the SAME story (one encyclical reported by 20 outlets)
    into one card. Headlines get paraphrased, so we don't match word-for-word: each
    title becomes a bag of significant words WEIGHTED by how rare they are across this
    batch (idf), and two headlines merge when the rare words they share make up most of
    the smaller one's weight — so 'Pope Leo urges AI disarmament' joins 'Pope Leo XIV
    urges AI disarmament in landmark encyclical' on disarmament/encyclical, while shared
    filler like pope/leo/ai barely counts. Two guards keep it from over-merging:
      • each headline is matched only against a group's REPRESENTATIVE (the first, i.e.
        highest-scoring, article) — groups don't accumulate words, so they can't snowball
        and swallow the whole feed;
      • a merge needs at least _GROUP_MIN_SHARED shared significant words, so a lone
        coincidental term (two unrelated 'Pentagon' stories) can't fuse them.
    Greedy and strongest-first, so the top-scoring article represents each group."""
    toks_list = [_sig_tokens(r["title"]) for r in rows]
    n = len(rows) or 1
    df = Counter()
    for toks in toks_list:
        for t in toks:
            df[t] += 1

    def weight(t):
        return math.log((n + 1.0) / (df[t] + 0.5))     # rarer word -> bigger weight

    def total(toks):
        return sum(weight(t) for t in toks) or 1.0     # the headline's whole weight

    clusters = []
    for r, toks in zip(rows, toks_list):
        a_sum = total(toks)
        best, best_sim = None, 0.0
        for c in clusters:
            shared = toks & c["tokens"]
            if len(shared) < _GROUP_MIN_SHARED:
                continue
            sim = sum(weight(t) for t in shared) / min(a_sum, c["sum"])
            if sim > best_sim:
                best_sim, best = sim, c
        if best and best_sim >= _GROUP_SIM:
            best["arts"].append(r)
        else:
            clusters.append({"rep": r, "tokens": set(toks), "arts": [r], "sum": a_sum})
    return clusters


# Within ONE event label, how big a gap (days) between consecutive article dates starts a
# new card. An event's own coverage arc is dense (days apart); a too-broad phenomenon label
# ("Weeping Icons") spans months/years, so its distinct happenings sit far apart and split.
# 14 holds one event's arc together while breaking multi-month spans. Picked from real PA
# before/after (Pope-Leo-AI stays ~merged, weeping-icons shatters); change only against fresh
# preview counts, never blind. Keys on PUBLISHED (real article date), never first_seen.
WINDOW_DAYS = 14


def _split_by_window(arts, days=WINDOW_DAYS):
    """Split one event-label bucket into per-moment cards: walk its articles in date order and
    start a fresh card whenever the gap to the previous article exceeds `days`. A real saga's
    dense coverage stays one card; a phenomenon label spanning months/years breaks into its
    separate happenings. Undated articles can't be placed in time, so each becomes its OWN card
    rather than fusing into or skewing a dated cluster (mirrors _peak_in_window, which drops an
    undated cluster the moment a date edge is set). Keys on published, never first_seen."""
    dated, undated = [], []
    for a in arts:
        try:
            dated.append((datetime.date.fromisoformat((a["published"] or "")[:10]), a))
        except ValueError:
            undated.append(a)
    dated.sort(key=lambda x: x[0])
    groups, run, prev = [], [], None
    for dt, a in dated:
        if prev is not None and (dt - prev).days > days:
            groups.append([x[1] for x in run]); run = []
        run.append((dt, a)); prev = dt
    if run:
        groups.append([x[1] for x in run])
    groups += [[a] for a in undated]      # each undated article = its own card
    return groups


def _group(rows, has_event):
    """Group into story cards. Prefer the AI's event label (scripts/news/group_news.py
    tags each article with the real-world event it covers, so wildly different headlines
    about one encyclical share a label) — collapse by exact label, THEN date-split each
    label into per-moment cards (a label can span years; _split_by_window breaks a >14-day
    gap). Anything not yet labeled falls back to the lexical word-overlap clustering above."""
    if not has_event:
        return _cluster(rows)
    by_event, ungrouped = {}, []
    for r in rows:
        ev = (r["event"] or "").strip() if r["event"] is not None else ""
        if ev:
            by_event.setdefault(ev, []).append(r)
        else:
            ungrouped.append(r)
    clusters = []
    for arts in by_event.values():
        for sub in _split_by_window(arts):
            # strongest in the sub-card represents it (rows arrived score-desc, but the
            # date sort above reorders, so re-pick rather than trust position)
            rep = max(sub, key=lambda a: ((a["score"] or 0), (a["published"] or "")))
            clusters.append({"rep": rep, "arts": sub})
    clusters += _cluster(ungrouped)
    return clusters


# How fresh a sibling must be (days before the cluster's newest article) to be eligible
# for the card HEADLINE. Picked from real before/after on PA (W=14: 7 real de-staling wins,
# drift acceptable). Loosen/tighten only against fresh before/after data, never blind.
FACE_WINDOW = 14


def _pick_face(arts, newest):
    """Choose the article whose HEADLINE fronts the card: the strongest article among
    those published within FACE_WINDOW days of the cluster's newest. So an old high-scorer
    stops holding the headline once fresher coverage exists, while a cluster with NO fresh
    sibling keeps its (correctly old) face — there is nothing newer to promote.

    SCOPE BOUNDARY — face only, never sort. This swaps the visible headline; it does NOT
    change the cluster's score or its feed position. The cluster still ranks on its PEAK
    score (see _serialize). The old-but-high clusters that peak-sort floats up are a
    separate, deferred SORT question — do NOT reach for a sort change here."""
    pool = arts
    nd = (newest or "")[:10]
    if nd:
        try:
            cutoff = (datetime.date.fromisoformat(nd)
                      - datetime.timedelta(days=FACE_WINDOW)).isoformat()
            recent = [a for a in arts if (a["published"] or "")[:10] >= cutoff]
            if recent:
                pool = recent
        except ValueError:
            pass
    # strongest in the pool; ties broken toward the newer article
    return max(pool, key=lambda a: ((a["score"] or 0), (a["published"] or "")))


def _peak_date(arts):
    """The day the cluster peaked — the publish day carrying the most coverage. We age the
    cluster from its BURST, not from its newest straggler, so trickle tail-coverage of an old
    event can't keep it permanently fresh. A lone new article adds 1 to a late day; it can't
    out-count the original burst, so the peak (and the age) barely move. Ties break toward the
    EARLIER day (a late tie is tail coverage, not a genuine re-peak)."""
    by_day = {}
    for a in arts:
        d = (a["published"] or "")[:10]
        if not d:
            continue
        c, ssum = by_day.get(d, (0, 0))
        by_day[d] = (c + 1, ssum + (a["score"] or 0))
    best = None
    for d in sorted(by_day):                 # ascending date -> earliest of any tie wins
        c, ssum = by_day[d]
        if best is None or (c, ssum) > (best[1], best[2]):
            best = (d, c, ssum)
    return best[0] if best else ""


def _serialize(cluster):
    arts = sorted(cluster["arts"], key=lambda a: a["published"] or "", reverse=True)
    newest = arts[0]["published"] if arts else ""
    peak = max((a["score"] or 0 for a in arts), default=0)   # cluster strength = SORT key (unchanged)
    face = _pick_face(arts, newest)                          # fresh-coverage HEADLINE only
    sources, seen = [], set()
    for a in arts:
        s = a["source"] or "?"
        if s in seen:
            continue
        seen.add(s)
        sources.append({"source": s, "url": a["url"], "published": (a["published"] or "")[:10]})
    return {
        "ids": [a["id"] for a in cluster["arts"]],
        "title": face["title"],
        "url": face["url"],
        # real article link when known (decoded/cached), else "" — the click prefers it over the
        # wrapper `url`, matching copy. Guarded so it's deploy-safe before the column exists.
        "resolved_url": (face["resolved_url"] if "resolved_url" in face.keys() else None) or "",
        "summary": face["summary"] or "",
        "score": peak,
        "thread": face["ai_thread"],
        "thread_label": THREAD_LABELS.get(face["ai_thread"], face["ai_thread"] or "?"),
        "why": face["ai_why"] or "",
        "published": (newest or "")[:10],
        "peak_date": _peak_date(arts),
        "count": len(arts),
        "sources": sources[:12],
        "status": face["status"] or "new",
    }


def _peak_in_window(peak_date, since, until):
    """The ONE date test shared by list / counts / shape: is a cluster's PEAK day inside
    [since, until]? Empty since/until = open on that side (since='' is the Max preset). A
    cluster with no datable article (empty peak) is dropped the moment a window edge is set —
    mirrors the old SQL, which excluded undated articles as soon as a date floor was applied.
    Filtering on the PEAK (not on each article) is the whole fix: a roving date window can no
    longer split one event into a bulk card here and an orphan straggler card there."""
    d = (peak_date or "")[:10]
    if not since and not until:
        return True
    if not d:
        return False
    if since and d < since:
        return False
    if until and d > until:
        return False
    return True


def _window_clusters(conn, rid, has_event, *, status=None, thread=None,
                     min_score=0, since=None, until=None, has_newflag=False):
    """Pull the FULL scored set (NO date floor in SQL — that's the structural fix), cluster it,
    then keep whole clusters whose PEAK day is in [since, until] AND whose PEAK score >= min_score.
    One event in or out as a unit, dated + counted by peak.

    status/thread narrow the ROWS that cluster (a view legitimately clusters a different
    population): status=None = every status (shape's whole-feed readout); 'new'/'keep'/'dismiss'
    = that bucket (list + counts). The date AND score window are applied to the ASSEMBLED cluster,
    never to the raw articles, so the cluster's identity (peak, count, sources) is the same no
    matter which date window is looking at it. The score floor moves here too: peak = the highest
    member score, so 'peak >= floor' selects the exact same CARDS as the old per-article floor —
    only the count changes, from 'members above the floor' to the whole event."""
    status_expr = "COALESCE(r.status, 'new')"
    where = ["i.score IS NOT NULL"]
    args = []
    if status:
        where.append(f"{status_expr} = ?")
        args.append(status)
    if thread:
        where.append("i.ai_thread = ?")
        args.append(thread)
    sql = (f"SELECT i.id, i.url, i.title, i.source, i.published, i.score, "
           f"i.summary, i.ai_thread, i.ai_why, {status_expr} AS status"
           f"{', i.event' if has_event else ''}"
           f"{', i.ai_new_flag' if has_newflag else ''} "
           f"FROM items i LEFT JOIN reviews r "
           f"  ON r.item_id = i.id AND r.reviewer = ? "
           f"WHERE {' AND '.join(where)} "
           f"ORDER BY i.score DESC, i.published DESC")
    rows = conn.execute(sql, [rid, *args]).fetchall()
    if not rows:
        return []
    out = []
    for c in _group(rows, has_event):
        arts = c["arts"]
        peak_score = max((a["score"] or 0 for a in arts), default=0)
        if min_score and peak_score < min_score:
            continue
        if not _peak_in_window(_peak_date(arts), since, until):
            continue
        out.append(c)
    return out


# Recency-weighted DEFAULT sort. The feed ranks story cards by PEAK score, which floats
# an old-but-high cluster above fresher coverage. We dock a small staleness penalty keyed
# off the cluster's PEAK DAY (the day most outlets covered it): GRACE days free, then
# RATE/day, capped at CAP. So a story breaking today still tops a 3-week-old 9 (a 20-day-old
# 9 -> ~7.2 vs a fresh 8 -> 8.0), but the cap means recency can NEVER overturn more than a
# CAP-point real gap — it's a weight, not a score override. Keying off the PEAK (not the
# newest article) is deliberate: a month-old event that keeps picking up trickle coverage
# would read as permanently fresh if we aged it from its newest straggler. A genuinely
# ongoing story re-peaks and stays fresh on its own. Steepen RATE to 0.15 only if an
# old-but-high card keeps holding the top slot (watch card #1 a few days).
_FEED_GRACE_DAYS = 2
_FEED_RATE = 0.1
_FEED_CAP = 2.0


def _staleness_penalty(published):
    """Days-old dock for a cluster, from the given date ('YYYY-MM-DD') — the caller passes
    the cluster's PEAK day (see the sort below), not its newest article."""
    d = (published or "")[:10]
    if not d:
        return 0.0
    try:
        today = datetime.datetime.now(datetime.timezone.utc).date()
        age = (today - datetime.date.fromisoformat(d)).days
    except ValueError:
        return 0.0
    return min(_FEED_CAP, max(0.0, (age - _FEED_GRACE_DAYS) * _FEED_RATE))


# ---- one-fetch held set: cluster the whole corpus ONCE, the browser does the rest ----
# The slowness was that every sort/filter/score/date tick re-clustered all ~5k rows
# server-side (counts did it 5x in ONE call). Instead serve the full clustered set once;
# the browser filters/sorts/counts/feed-shapes it with NO further calls. The heavy
# clustering is cached per corpus fingerprint, so it only recomputes when a pull adds
# articles. Status is NOT cached — read fresh per request and attached, so triage stays right.
#
# CACHE BOUNDARY: the fingerprint is (row count, newest id). That busts on a NEW PULL (new
# rows) but NOT on a re-score-in-place (same rows, changed scores). That's fine while the
# scorer is frozen; if you ever re-score existing rows by hand, the cards won't refresh on
# their own — hit the tab's Refresh button (it re-pulls) to clear it. Not a surprise: a
# documented limit, with a one-click force-refresh.
_ALL_CACHE = {"sig": None, "cards": None}


def _corpus_sig(conn):
    r = conn.execute("SELECT COUNT(*) n, COALESCE(MAX(id), 0) mx "
                     "FROM items WHERE score IS NOT NULL").fetchone()
    return (r["n"], r["mx"])


def _all_cards(conn, has_event, has_newflag, has_resolved=False):
    """Every story card, clustered once, status-independent (cached per corpus sig). Each
    card carries a `members` list (per-article score/thread/new-flag + DATE and the article's
    own face fields) so the browser can recompute the whole card over its IN-WINDOW members
    when a date window is active — face, score, date and sources all from the in-window subset,
    so an old burst day can't bury a card that has fresh strong coverage. (See _windowCard in
    84-news.jsx.) Also feeds the feed-shape readout. No extra server call."""
    sig = _corpus_sig(conn)
    if _ALL_CACHE["sig"] == sig and _ALL_CACHE["cards"] is not None:
        return _ALL_CACHE["cards"]
    sel = ("SELECT i.id, i.url, i.title, i.source, i.published, i.score, "
           "i.summary, i.ai_thread, i.ai_why, i.query, 'new' AS status"
           + (", i.resolved_url" if has_resolved else "")
           + (", i.event" if has_event else "")
           + (", i.ai_new_flag" if has_newflag else "") +
           " FROM items i WHERE i.score IS NOT NULL "
           "ORDER BY i.score DESC, i.published DESC")
    rows = conn.execute(sel).fetchall()
    cards = []
    for c in _group(rows, has_event):
        card = _serialize(c)                 # 'status' here is the 'new' placeholder
        card.pop("status", None)             # attached fresh, per request, below
        rep = c["rep"]
        card["event"] = (rep["event"] if has_event and rep["event"] else "")
        # `via` = how WE pulled this article: an RSS-by-outlet feed (query "rss:<name>")
        # or a Google News search. Stored at ingest (the query column) — pure provenance,
        # shown in the why-rail; no scoring involved.
        card["members"] = [{"s": a["score"] or 0, "t": a["ai_thread"],
                            "nf": (a["ai_new_flag"] if has_newflag else 0),
                            "d": (a["published"] or "")[:10],
                            "title": a["title"], "url": a["url"],
                            "resolved": (a["resolved_url"] if has_resolved else "") or "",
                            "summary": a["summary"] or "",
                            "why": a["ai_why"] or "", "src": a["source"] or "?",
                            "via": ("RSS" if (a["query"] or "").startswith("rss:") else "Google News")}
                           for a in c["arts"]]
        cards.append(card)
    _ALL_CACHE["sig"] = sig
    _ALL_CACHE["cards"] = cards
    return cards


@bp.route("/api/news/all", methods=["GET"])
@limiter.limit("240 per hour")
def all_news():
    """The whole clustered feed in one shot — all statuses, no date/score/thread filter.
    The browser holds this and does every sort/filter/score/date/thread/count locally, so
    interactions never hit the server again (refetch only on a fresh pull / reload / the
    tab's Refresh button). See the CACHE BOUNDARY note above _ALL_CACHE for re-score."""
    if not _can_read():
        return jsonify({"error": "not found"}), 404
    if not _available():
        return jsonify({"available": False})
    rid, _ = _reviewer()
    conn = news_db()
    try:
        _ensure_reviews(conn)
        cols = [c[1] for c in conn.execute("PRAGMA table_info(items)")]
        cards = _all_cards(conn, "event" in cols, "ai_new_flag" in cols, "resolved_url" in cols)
        smap = {r["item_id"]: r["status"] for r in
                conn.execute("SELECT item_id, status FROM reviews WHERE reviewer = ?", (rid,))}
        out = []
        for card in cards:
            sts = {smap.get(i, "new") for i in card["ids"]}
            c2 = dict(card)
            c2["status"] = sts.pop() if len(sts) == 1 else "new"
            out.append(c2)
    except sqlite3.Error:
        return jsonify({"available": True, "cards": [], "labels": THREAD_LABELS})
    finally:
        conn.close()
    return jsonify({"available": True, "cards": out, "labels": THREAD_LABELS})


@bp.route("/api/news/meta", methods=["GET"])
def meta():
    """Drives the tab: is the viewer admin, is news.db loaded, the thread names, who's
    reviewing. Yes/no to everyone; data only to admin. The per-tab tallies live in
    /api/news/counts (they're window-scoped and reseed when the date/score changes)."""
    admin = is_admin()
    reader = (not admin) and _shared_key_ok()
    if not (admin or reader):
        return jsonify({"owner": False, "reader": False, "available": False})
    if not _available():
        return jsonify({"owner": admin, "reader": reader, "available": False, "labels": THREAD_LABELS})
    rid, can_write = _reviewer()
    return jsonify({"owner": admin, "reader": reader, "available": True,
                    "labels": THREAD_LABELS, "can_write": can_write,
                    "reviewer": rid, "reviewer_name": _reviewer_label(rid)})


@bp.route("/api/news/counts", methods=["GET"])
@limiter.limit("600 per hour")
def counts():
    """Window-scoped triage tallies for the three tabs: how many CARDS sit in
    inbox / kept / dismissed for the active date+score window — so the three add up to the
    in-window total and Inbox reads as a remainder, not the whole feed. Also returns the
    all-time kept/dismissed totals so the UI can show a quiet '+N outside this window' hint.
    Counted by CARD the same way the feed groups them (through _window_clusters, so the badges
    can't disagree with the list). Honors the active thread when one is set, so the badges keep
    matching the feed once a thread is picked; the all-time totals stay thread-scoped too (so
    '+N outside' means outside the DATE window, within the same thread)."""
    if not _can_read():
        return jsonify({"error": "not found"}), 404
    if not _available():
        return jsonify({"available": False})
    since = (request.args.get("since") or "").strip()
    try:
        min_score = max(0, min(10, int(request.args.get("min", 0))))
    except (TypeError, ValueError):
        min_score = 0
    until = (request.args.get("until") or "").strip()
    thread = (request.args.get("thread") or "").strip()
    rid, _ = _reviewer()
    conn = news_db()
    try:
        _ensure_reviews(conn)
        has_event = "event" in [c[1] for c in conn.execute("PRAGMA table_info(items)")]
        # in-window (sc=True) vs all-time (sc=False) card counts for a status bucket; the
        # thread narrows both (only the DATE window is dropped for the all-time totals, so
        # '+N outside' = before since OR after until). Same _window_clusters the feed uses,
        # so a badge is exactly the card count of its view.
        def c(status, sc=False):
            return len(_window_clusters(conn, rid, has_event, status=status,
                                        thread=thread or None,
                                        since=since if sc else None,
                                        until=until if sc else None,
                                        min_score=min_score if sc else 0))
        out = {
            "available": True,
            "inbox": c("new", True),
            "kept": c("keep", True),
            "dismissed": c("dismiss", True),
            "kept_all": c("keep"),
            "dismissed_all": c("dismiss"),
        }
    except sqlite3.Error:
        out = {"available": True, "inbox": 0, "kept": 0, "dismissed": 0,
               "kept_all": 0, "dismissed_all": 0}
    finally:
        conn.close()
    return jsonify(out)


@bp.route("/api/news/list", methods=["GET"])
@limiter.limit("240 per hour")
def list_news():
    if not _can_read():
        return jsonify({"error": "not found"}), 404
    if not _available():
        return jsonify({"stories": [], "available": False})

    since = (request.args.get("since") or "").strip()        # 'YYYY-MM-DD' or empty
    until = (request.args.get("until") or "").strip()        # 'YYYY-MM-DD' or empty (= now)
    try:
        min_score = max(0, min(10, int(request.args.get("min", 0))))
    except (TypeError, ValueError):
        min_score = 0
    thread = (request.args.get("thread") or "").strip()      # a thread key, or '' = all
    view = (request.args.get("view") or "inbox").strip()     # inbox | kept | dismissed | all
    order = (request.args.get("order") or "score").strip()   # score | date

    rid, _ = _reviewer()
    # inbox/kept/dismissed narrow to one status bucket; "all" leaves status open. The date +
    # score window is applied to the assembled clusters (peak-in-window), NOT the raw articles.
    view_status = {"inbox": "new", "kept": "keep", "dismissed": "dismiss"}.get(view)

    conn = news_db()
    try:
        _ensure_reviews(conn)
        has_event = "event" in [c[1] for c in conn.execute("PRAGMA table_info(items)")]
        clusters = _window_clusters(conn, rid, has_event, status=view_status,
                                    thread=thread or None, min_score=min_score,
                                    since=since or None, until=until or None)
    finally:
        conn.close()

    stories = [_serialize(c) for c in clusters]
    if order == "date":
        # Newest: by the event's PEAK day, not its latest straggler — an event peaking in May
        # with a June trickle is a May story (matches rank + the window + the displayed range).
        stories.sort(key=lambda s: (s["peak_date"], s["score"]), reverse=True)
    elif order == "oldest":
        # Mirror of Newest: oldest peak first; -score keeps the stronger card ahead on a tie.
        stories.sort(key=lambda s: (s["peak_date"], -s["score"]))
    else:
        # Default: recency-weighted score (see _staleness_penalty). The dock keys off the
        # cluster's PEAK day, so a stale event with a fresh straggler can't dodge it. Newest
        # published stays the tie-break so equal effective scores still favor the fresher card.
        stories.sort(key=lambda s: (s["score"] - _staleness_penalty(s["peak_date"]),
                                    s["published"]), reverse=True)
    return jsonify({"stories": stories[:300], "available": True})


@bp.route("/api/news/shape", methods=["GET"])
@limiter.limit("240 per hour")
def shape():
    """Feed-level "why the watch is pointed here today" — computed straight from the
    already-scored rows, NO model call. Honors the Since window (so it's "today's watch");
    deliberately IGNORES the score floor (the whole point is the BURIED count you can't see
    by scrolling) and the thread filter (it's a whole-feed readout). Drives the right
    inspect zone, which now shows this by default instead of a per-card rationale."""
    if not _can_read():
        return jsonify({"error": "not found"}), 404
    if not _available():
        return jsonify({"available": False})
    since = (request.args.get("since") or "").strip()
    until = (request.args.get("until") or "").strip()
    rid, _ = _reviewer()
    conn = news_db()
    try:
        _ensure_reviews(conn)
        cols = [c[1] for c in conn.execute("PRAGMA table_info(items)")]
        has_event = "event" in cols
        has_newflag = "ai_new_flag" in cols
        # Cluster the WHOLE in-window feed once (every status, every thread, NO score floor —
        # the buried count is the point), the SAME way the cards are built, then read every
        # figure off those clusters' member articles. So each shape number matches the cards
        # actually shown for this date window — an event in or out as a unit, by its peak.
        clusters = _window_clusters(conn, rid, has_event, status=None, thread=None,
                                    min_score=0, since=since or None, until=until or None,
                                    has_newflag=has_newflag)
        arts = [a for cl in clusters for a in cl["arts"]]
        surfaced = sum(1 for a in arts if (a["score"] or 0) >= 6)
        buried = sum(1 for a in arts if (a["score"] or 0) < 6)
        total = len(arts)
        new_angles = sum(1 for a in arts if a["ai_new_flag"] == 1) if has_newflag else 0
        # per-thread surfaced (>=6) / scored (all), biggest first
        by_thread = {}
        for a in arts:
            s, sc = by_thread.get(a["ai_thread"], (0, 0))
            by_thread[a["ai_thread"]] = (s + (1 if (a["score"] or 0) >= 6 else 0), sc + 1)
        threads = sorted(
            ({"thread": t, "label": THREAD_LABELS.get(t, t or "?"),
              "surfaced": s, "scored": sc}
             for t, (s, sc) in by_thread.items()),
            key=lambda r: (r["surfaced"], r["scored"]), reverse=True)
        # top events = the biggest in-window cards (each cluster IS one event); label by the
        # cluster's AI event tag when it has one, else its representative headline.
        top = sorted(clusters, key=lambda cl: len(cl["arts"]), reverse=True)[:5]
        topclusters = [
            {"event": ((cl["rep"]["event"] if has_event and cl["rep"]["event"] else None)
                       or cl["rep"]["title"]),
             "n": len(cl["arts"]),
             "hi": max((a["score"] or 0 for a in cl["arts"]), default=0)}
            for cl in top]
    except sqlite3.Error:
        return jsonify({"available": True, "surfaced": 0, "buried": 0, "total": 0,
                        "new_angles": 0, "threads": [], "clusters": []})
    finally:
        conn.close()
    return jsonify({
        "available": True,
        "surfaced": surfaced, "buried": buried, "total": total,
        "new_angles": new_angles,
        "threads": threads, "clusters": topclusters,
    })


@bp.route("/api/news/status", methods=["POST"])
@limiter.limit("600 per hour")
def set_status():
    rid, can_write = _reviewer()
    if not can_write:
        return jsonify({"error": "not found"}), 404
    try:
        body = json.loads(request.get_data(cache=False) or b"{}")
    except (ValueError, TypeError):
        body = {}
    ids = body.get("ids") or []
    status = body.get("status")
    if status not in _VALID_STATUS or not isinstance(ids, list) or not ids:
        return jsonify({"ok": False}), 400
    ids = [int(i) for i in ids if str(i).isdigit()][:500]
    if not ids:
        return jsonify({"ok": False}), 400
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = news_db()
    try:
        _ensure_reviews(conn)
        # Every write is scoped to THIS caller's id (rid), so a reviewer can only ever
        # touch their OWN rows — admin and share-key never reach each other's. The clear
        # path removes the row entirely (back to inbox); keep/dismiss/new write one.
        if status == "clear":
            qmarks = ",".join("?" for _ in ids)
            conn.execute(
                f"DELETE FROM reviews WHERE reviewer = ? AND item_id IN ({qmarks})",
                [rid, *ids])
        else:
            conn.executemany(
                "INSERT INTO reviews (item_id, reviewer, status, updated) VALUES (?,?,?,?) "
                "ON CONFLICT(item_id, reviewer) DO UPDATE SET status=excluded.status, "
                "updated=excluded.updated",
                [(i, rid, status, now) for i in ids])
        conn.commit()
    except sqlite3.Error:
        return jsonify({"ok": False}), 500
    finally:
        conn.close()
    return jsonify({"ok": True, "n": len(ids)})


@bp.route("/api/news/resolve", methods=["POST"])
@limiter.limit("600 per hour")
def resolve_urls():
    """Resolve-on-copy: turn the shortlist's face wrapper URLs into real article
    URLs, caching each in items.resolved_url so the next copy is instant. Keyed on
    the URL the copy emits (s.url = the face row's url), so we hit exactly the row
    the copy would emit — no way to resolve one row and copy another. The same
    article can sit in several clusters (same url in N rows); UPDATE ... WHERE url
    caches all of them, which is what we want.

    Never raises — an unresolvable wrapper comes back AS the wrapper, so copy
    always succeeds. Body: {urls:[...], dry:bool}. dry=true resolves + returns but
    writes NOTHING (the confirm-the-write-shape variant). Deploy-safe: if the
    resolved_url column isn't there yet, it resolves + returns without caching."""
    if not _can_read():
        return jsonify({"error": "not found"}), 404
    try:
        body = json.loads(request.get_data(cache=False) or b"{}")
    except (ValueError, TypeError):
        body = {}
    urls = body.get("urls") or []
    dry = bool(body.get("dry"))
    if not isinstance(urls, list):
        return jsonify({"ok": False}), 400
    seen, uniq = set(), []
    for u in urls:
        if isinstance(u, str) and u and u not in seen:
            seen.add(u)
            uniq.append(u)
        if len(uniq) >= 300:
            break
    try:
        from scripts.news.gnews_resolve import resolve as _resolve, is_wrapper
    except Exception:
        # resolver unavailable — hand every url back unchanged, copy still works
        return jsonify({"ok": True, "urls": {u: u for u in uniq}, "dry": dry})
    out = {}
    conn = news_db()
    try:
        has_resolved = any(c[1] == "resolved_url"
                           for c in conn.execute("PRAGMA table_info(items)"))
        for u in uniq:
            if not is_wrapper(u):
                out[u] = u
                continue
            if has_resolved:
                row = conn.execute(
                    "SELECT resolved_url FROM items "
                    "WHERE url = ? AND resolved_url IS NOT NULL LIMIT 1", (u,)).fetchone()
                if row and row["resolved_url"]:
                    out[u] = row["resolved_url"]
                    continue
            clean = _resolve(u)              # never raises; None on any failure
            if clean:
                out[u] = clean
                if has_resolved and not dry:
                    conn.execute("UPDATE items SET resolved_url = ? WHERE url = ?",
                                 (clean, u))
                    conn.commit()
            else:
                out[u] = u                   # fail soft: hand back the wrapper
    except sqlite3.Error:
        for u in uniq:
            out.setdefault(u, u)
    finally:
        conn.close()
    return jsonify({"ok": True, "urls": out, "dry": dry})
