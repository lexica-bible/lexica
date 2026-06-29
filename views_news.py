#!/usr/bin/env python3
"""News watch — admin-only review tab for the end-times news gatherer.

The data is gathered + AI-scored OFFLINE by scripts/news/ (gather_news.py +
score_news.py) into news.db. This blueprint just SERVES that file to the in-app
tab, admin-gated (404 to everyone else, exactly like visitor stats):

  GET  /api/news/meta             → {owner, available, labels, counts}
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
        "count": len(arts),
        "sources": sources[:12],
        "status": face["status"] or "new",
    }


# Recency-weighted DEFAULT sort. The feed ranks story cards by PEAK score, which floats
# an old-but-high cluster above fresher coverage. We dock a small staleness penalty keyed
# off the cluster's NEWEST sibling: GRACE days free, then RATE/day, capped at CAP. So a
# story breaking today still tops a 3-week-old 9 (a 20-day-old 9 -> ~7.2 vs a fresh 8 ->
# 8.0), but the cap means recency can NEVER overturn more than a CAP-point real gap — it's
# a weight, not a score override. A long-running real story keeps a fresh face because the
# penalty reads its NEWEST article, so continued coverage = age 0 = no dock. Steepen RATE
# to 0.15 only if an old-but-high card keeps holding the top slot (watch card #1 a few days).
_FEED_GRACE_DAYS = 2
_FEED_RATE = 0.1
_FEED_CAP = 2.0


def _staleness_penalty(published):
    """Days-old dock for a cluster, from its newest article's date ('YYYY-MM-DD')."""
    d = (published or "")[:10]
    if not d:
        return 0.0
    try:
        today = datetime.datetime.now(datetime.timezone.utc).date()
        age = (today - datetime.date.fromisoformat(d)).days
    except ValueError:
        return 0.0
    return min(_FEED_CAP, max(0.0, (age - _FEED_GRACE_DAYS) * _FEED_RATE))


def _count_view_clusters(conn, rid, status_value, has_event):
    """How many CARDS (clusters) this reviewer has in a status — counted the SAME way the
    list renders: existing + scored items only, scoped to rid, grouped into cards. So the
    tab badge can't disagree with the feed (an orphaned review row whose item churned away
    has no scored item to join, so it drops out), and the number is CARDS not articles
    (5 kept articles that group into 3 cards count as 3). No min/since/thread floor — the
    Kept/Dismissed views don't apply one either."""
    sql = (f"SELECT i.id, i.title, i.ai_thread{', i.event' if has_event else ''} "
           f"FROM items i LEFT JOIN reviews r "
           f"  ON r.item_id = i.id AND r.reviewer = ? "
           f"WHERE i.score IS NOT NULL AND COALESCE(r.status, 'new') = ? "
           f"ORDER BY i.score DESC, i.published DESC")
    rows = conn.execute(sql, [rid, status_value]).fetchall()
    return len(_group(rows, has_event)) if rows else 0


@bp.route("/api/news/meta", methods=["GET"])
def meta():
    """Drives the tab: is the viewer admin, is news.db loaded, the thread names, and
    how many stories sit in each review bucket. Yes/no to everyone; data only to admin."""
    admin = is_admin()
    reader = (not admin) and _shared_key_ok()
    if not (admin or reader):
        return jsonify({"owner": False, "reader": False, "available": False})
    if not _available():
        return jsonify({"owner": admin, "reader": reader, "available": False, "labels": THREAD_LABELS})
    rid, can_write = _reviewer()
    conn = news_db()
    try:
        _ensure_reviews(conn)
        def n(sql, args=()):
            r = conn.execute(sql, args).fetchone()
            return (r[0] or 0) if r else 0
        has_event = "event" in [c[1] for c in conn.execute("PRAGMA table_info(items)")]
        counts = {
            "scored": n("SELECT count(*) FROM items WHERE score IS NOT NULL"),
            "total": n("SELECT count(*) FROM items"),
            # CARDS (clusters), counted the same way the list renders — see _count_view_clusters.
            "kept": _count_view_clusters(conn, rid, "keep", has_event),
            "dismissed": _count_view_clusters(conn, rid, "dismiss", has_event),
        }
    except sqlite3.Error:
        counts = {}
    finally:
        conn.close()
    return jsonify({"owner": admin, "reader": reader, "available": True,
                    "labels": THREAD_LABELS, "counts": counts, "can_write": can_write,
                    "reviewer": rid, "reviewer_name": _reviewer_label(rid)})


@bp.route("/api/news/list", methods=["GET"])
@limiter.limit("240 per hour")
def list_news():
    if not _can_read():
        return jsonify({"error": "not found"}), 404
    if not _available():
        return jsonify({"stories": [], "available": False})

    since = (request.args.get("since") or "").strip()        # 'YYYY-MM-DD' or empty
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
        # Default: recency-weighted score (see _staleness_penalty). Published stays the
        # tie-break so equal effective scores still favor the fresher card.
        stories.sort(key=lambda s: (s["score"] - _staleness_penalty(s["published"]),
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
    where = ["score IS NOT NULL"]
    args = []
    if since:
        where.append("published >= ? AND published != ''")
        args.append(since)
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
