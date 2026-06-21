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
import hmac
import json
import math
import os
import re
import sqlite3
from collections import Counter

from flask import Blueprint, jsonify, request

from core import news_db, NEWS_DB, limiter
from views_notes import is_admin

bp = Blueprint("news", __name__)

# Display names for the gatherer's 12 threads. KEEP IN SYNC with the THREADS keys
# in scripts/news/queries.py (small + static, so duplicated here rather than
# importing across the scripts/ boundary). "new" = the AI flagged a fresh angle.
THREAD_LABELS = {
    "exposure_to_moral_authority": "Exposure → moral authority",
    "papacy_moral_authority": "Papacy as moral authority",
    "american_pope": "The American pope",
    "encyclical_political": "Encyclicals going political",
    "ai_moralized": "AI being moralized",
    "legislating_morality": "Legislating morality",
    "ecumenism": "Ecumenism",
    "jesuits": "Jesuits",
    "trump_vs_leo": "Trump vs. Pope Leo",
    "alien_agenda": "Alien / UFO agenda",
    "protestants_to_rome": "Protestants → Rome",
    "financial_control": "Financial control",
    "new": "New angle",
}

_VALID_STATUS = {"new", "keep", "dismiss"}

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


def _serialize(cluster):
    rep = cluster["rep"]
    arts = sorted(cluster["arts"], key=lambda a: a["published"] or "", reverse=True)
    sources, seen = [], set()
    for a in arts:
        s = a["source"] or "?"
        if s in seen:
            continue
        seen.add(s)
        sources.append({"source": s, "url": a["url"], "published": (a["published"] or "")[:10]})
    return {
        "ids": [a["id"] for a in cluster["arts"]],
        "title": rep["title"],
        "score": rep["score"],
        "thread": rep["ai_thread"],
        "thread_label": THREAD_LABELS.get(rep["ai_thread"], rep["ai_thread"] or "?"),
        "why": rep["ai_why"] or "",
        "published": max((a["published"] or "" for a in arts), default="")[:10],
        "count": len(arts),
        "sources": sources[:12],
        "status": rep["status"] or "new",
    }


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
    conn = news_db()
    try:
        def n(sql, args=()):
            r = conn.execute(sql, args).fetchone()
            return (r[0] or 0) if r else 0
        counts = {
            "scored": n("SELECT count(*) FROM items WHERE score IS NOT NULL"),
            "total": n("SELECT count(*) FROM items"),
            "kept": n("SELECT count(*) FROM items WHERE status='keep'"),
            "dismissed": n("SELECT count(*) FROM items WHERE status='dismiss'"),
        }
    except sqlite3.Error:
        counts = {}
    finally:
        conn.close()
    return jsonify({"owner": True, "available": True, "labels": THREAD_LABELS, "counts": counts})


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

    where = ["score IS NOT NULL", "score >= ?"]
    args = [min_score]
    if since:
        # published is full ISO; comparing against a 'YYYY-MM-DD' floor works as text.
        # Empty published (unknown date) is excluded once a since-floor is set.
        where.append("published >= ? AND published != ''")
        args.append(since)
    if thread:
        where.append("ai_thread = ?")
        args.append(thread)
    if view == "inbox":
        where.append("(status IS NULL OR status = 'new')")
    elif view == "kept":
        where.append("status = 'keep'")
    elif view == "dismissed":
        where.append("status = 'dismiss'")

    conn = news_db()
    try:
        cols = [c[1] for c in conn.execute("PRAGMA table_info(items)")]
        has_event = "event" in cols                      # set once group_news.py runs
        sql = (f"SELECT id, url, title, source, published, score, ai_thread, ai_why, status"
               f"{', event' if has_event else ''} "
               f"FROM items WHERE {' AND '.join(where)} "
               f"ORDER BY score DESC, published DESC")
        rows = conn.execute(sql, args).fetchall()
    finally:
        conn.close()

    clusters = _group(rows, has_event)
    stories = [_serialize(c) for c in clusters]
    if order == "date":
        stories.sort(key=lambda s: (s["published"], s["score"]), reverse=True)
    else:
        stories.sort(key=lambda s: (s["score"], s["published"]), reverse=True)
    return jsonify({"stories": stories[:300], "available": True})


@bp.route("/api/news/status", methods=["POST"])
@limiter.limit("600 per hour")
def set_status():
    if not is_admin():
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
    conn = news_db()
    try:
        marks = ",".join("?" * len(ids))
        conn.execute(f"UPDATE items SET status = ? WHERE id IN ({marks})", [status, *ids])
        conn.commit()
    except sqlite3.Error:
        return jsonify({"ok": False}), 500
    finally:
        conn.close()
    return jsonify({"ok": True, "n": len(ids)})
