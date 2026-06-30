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

# Display names for the gatherer's 10 threads. KEEP IN SYNC with the THREADS keys
# in scripts/news/queries.py (small + static, so duplicated here rather than
# importing across the scripts/ boundary). "new" = the AI flagged a fresh angle.
THREAD_LABELS = {
    "papacy_moral_authority": "Papacy as moral authority",
    "american_pope": "Vatican–US relations",
    "encyclical_political": "Encyclicals / doctrine going political",
    "ai_moralized": "Economic/tech control",
    "legislating_morality": "Legislating worship/morality",
    "ecumenism": "Ecumenism under Rome",
    "alien_agenda": "Alien / UFO disclosure",
    "culture_shaping": "Culture shaping",
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


def _group(rows, has_event):
    """Group into story cards. Prefer the AI's event label (scripts/news/group_news.py
    tags each article with the real-world event it covers, so wildly different headlines
    about one encyclical share a label) — collapse by exact label. Anything not yet
    labeled falls back to the lexical word-overlap clustering above. Rows arrive
    strongest-first, so each group's first article is its representative."""
    if not has_event:
        return _cluster(rows)
    by_event, ungrouped = {}, []
    for r in rows:
        ev = (r["event"] or "").strip() if r["event"] is not None else ""
        if ev:
            by_event.setdefault(ev, []).append(r)
        else:
            ungrouped.append(r)
    clusters = [{"rep": arts[0], "arts": arts} for arts in by_event.values()]
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


def _count_view_clusters(conn, rid, status_value, has_event, since=None, min_score=0,
                         thread=None, until=None):
    """How many CARDS (clusters) this reviewer has in a status — counted the SAME way the
    list renders: existing + scored items only, scoped to rid, grouped into cards. So the
    tab badge can't disagree with the feed (an orphaned review row whose item churned away
    has no scored item to join, so it drops out), and the number is CARDS not articles
    (5 kept articles that group into 3 cards count as 3).

    When since/min_score are given they apply the SAME date+score window the feed uses, so
    the three tab badges describe the in-window population (Inbox+Kept+Dismissed add up to
    the in-window total, and Inbox reads as a remainder). When a thread is given it narrows
    too, so the badges still match the feed once a thread is picked. Called with NO date
    window (but the same thread) for the all-time totals behind the '+N outside' footer."""
    where = ["i.score IS NOT NULL", "COALESCE(r.status, 'new') = ?"]
    args = [rid, status_value]
    if min_score:
        where.append("i.score >= ?")
        args.append(min_score)
    if since:
        where.append("i.published >= ? AND i.published != ''")
        args.append(since)
    if until:
        # published is a full timestamp; compare the DATE part so the whole end-day counts.
        where.append("substr(i.published, 1, 10) <= ? AND i.published != ''")
        args.append(until)
    if thread:
        where.append("i.ai_thread = ?")
        args.append(thread)
    sql = (f"SELECT i.id, i.title, i.ai_thread{', i.event' if has_event else ''} "
           f"FROM items i LEFT JOIN reviews r "
           f"  ON r.item_id = i.id AND r.reviewer = ? "
           f"WHERE {' AND '.join(where)} "
           f"ORDER BY i.score DESC, i.published DESC")
    rows = conn.execute(sql, args).fetchall()
    return len(_group(rows, has_event)) if rows else 0


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
    Counted by CARD the same way the feed groups them (see _count_view_clusters). Honors the
    active thread when one is set, so the badges keep matching the feed once a thread is
    picked; the all-time totals stay thread-scoped too (so '+N outside' means outside the
    DATE window, within the same thread)."""
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
        # '+N outside' = before since OR after until).
        def c(status, sc=False):
            return _count_view_clusters(conn, rid, status, has_event,
                                        since=since if sc else None,
                                        min_score=min_score if sc else 0,
                                        until=until if sc else None,
                                        thread=thread or None)
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
    status_expr = "COALESCE(r.status, 'new')"   # this viewer's call, default unreviewed

    where = ["i.score IS NOT NULL", "i.score >= ?"]
    args = [min_score]
    if since:
        # published is full ISO; comparing against a 'YYYY-MM-DD' floor works as text.
        # Empty published (unknown date) is excluded once a since-floor is set.
        where.append("i.published >= ? AND i.published != ''")
        args.append(since)
    if until:
        # upper bound: compare the DATE part so the whole end-day is included.
        where.append("substr(i.published, 1, 10) <= ? AND i.published != ''")
        args.append(until)
    if thread:
        where.append("i.ai_thread = ?")
        args.append(thread)
    if view == "inbox":
        where.append(f"{status_expr} = 'new'")
    elif view == "kept":
        where.append(f"{status_expr} = 'keep'")
    elif view == "dismissed":
        where.append(f"{status_expr} = 'dismiss'")

    conn = news_db()
    try:
        _ensure_reviews(conn)
        cols = [c[1] for c in conn.execute("PRAGMA table_info(items)")]
        has_event = "event" in cols                      # set once group_news.py runs
        sql = (f"SELECT i.id, i.url, i.title, i.source, i.published, i.score, "
               f"i.ai_thread, i.ai_why, {status_expr} AS status"
               f"{', i.event' if has_event else ''} "
               f"FROM items i LEFT JOIN reviews r "
               f"  ON r.item_id = i.id AND r.reviewer = ? "
               f"WHERE {' AND '.join(where)} "
               f"ORDER BY i.score DESC, i.published DESC")
        rows = conn.execute(sql, [rid, *args]).fetchall()
    finally:
        conn.close()

    clusters = _group(rows, has_event)
    stories = [_serialize(c) for c in clusters]
    if order == "date":
        stories.sort(key=lambda s: (s["published"], s["score"]), reverse=True)
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
    where = ["score IS NOT NULL"]
    args = []
    if since:
        where.append("published >= ? AND published != ''")
        args.append(since)
    if until:
        where.append("substr(published, 1, 10) <= ? AND published != ''")
        args.append(until)
    w = " AND ".join(where)

    conn = news_db()
    try:
        cols = [c[1] for c in conn.execute("PRAGMA table_info(items)")]
        has_event = "event" in cols
        has_newflag = "ai_new_flag" in cols
        # surfaced (score>=6) vs buried (<6) + new-angle flags — booleans sum to counts.
        tot = conn.execute(
            f"SELECT SUM(score >= 6) AS surfaced, SUM(score < 6) AS buried, COUNT(*) AS total"
            f"{', SUM(ai_new_flag = 1) AS new_angles' if has_newflag else ''} "
            f"FROM items WHERE {w}", args).fetchone()
        threads = [
            {"thread": r["ai_thread"],
             "label": THREAD_LABELS.get(r["ai_thread"], r["ai_thread"] or "?"),
             "surfaced": r["surfaced"] or 0, "scored": r["scored"] or 0}
            for r in conn.execute(
                f"SELECT ai_thread, SUM(score >= 6) AS surfaced, COUNT(*) AS scored "
                f"FROM items WHERE {w} GROUP BY ai_thread "
                f"ORDER BY surfaced DESC, scored DESC", args)]
        clusters = []
        if has_event:
            clusters = [
                {"event": r["event"], "n": r["n"], "hi": r["hi"] or 0}
                for r in conn.execute(
                    f"SELECT event, COUNT(*) AS n, MAX(score) AS hi "
                    f"FROM items WHERE {w} AND event IS NOT NULL AND event != '' "
                    f"GROUP BY event ORDER BY n DESC LIMIT 5", args)]
    except sqlite3.Error:
        return jsonify({"available": True, "surfaced": 0, "buried": 0, "total": 0,
                        "new_angles": 0, "threads": [], "clusters": []})
    finally:
        conn.close()
    return jsonify({
        "available": True,
        "surfaced": (tot["surfaced"] or 0) if tot else 0,
        "buried": (tot["buried"] or 0) if tot else 0,
        "total": (tot["total"] or 0) if tot else 0,
        "new_angles": (tot["new_angles"] or 0) if (tot and has_newflag) else 0,
        "threads": threads, "clusters": clusters,
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
