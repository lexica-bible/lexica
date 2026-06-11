#!/usr/bin/env python3
"""Visitor stats — private, owner-only, in-house (no third party).

A tiny page-view counter kept in notes.db. The browser pings /api/stats/hit once
per page load; we store the day, a one-way DAILY hash of IP+browser (so the same
person on the same day counts as one "unique", and the hash can't be linked across
days or turned back into an IP), and the referring site. The owner's OWN visits are
skipped. /api/stats returns the summary and is owner-gated (404 to everyone else).

Privacy: no cookies, no raw IPs, no PII. Just counts.
"""
import hashlib
import sqlite3
import time
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, request

from core import notes_db, limiter
from views_notes import is_owner

bp = Blueprint("stats", __name__)

_PEPPER = "lexica-visit-v1"   # makes the daily visitor hash not trivially reversible


def _ensure():
    conn = notes_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS visits ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL, ts INTEGER NOT NULL,"
            " visitor TEXT NOT NULL, ref TEXT)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS ix_visits_day ON visits(day)")
        conn.commit()
    finally:
        conn.close()


def _client_ip():
    # PythonAnywhere sits behind a proxy, so the real client IP is the first entry
    # in X-Forwarded-For; fall back to remote_addr.
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or ""


def _ref_host(raw):
    """The referring site's host (where the visitor came from), or 'direct'. Our own
    host counts as direct (in-site navigation isn't an external referrer)."""
    if not raw or not isinstance(raw, str):
        return "direct"
    try:
        host = urlsplit(raw).netloc.lower()
        own = urlsplit(request.host_url).netloc.lower()
    except Exception:
        return "direct"
    if not host or host == own:
        return "direct"
    if host.startswith("www."):
        host = host[4:]
    return host[:100]


@bp.route("/api/stats/hit", methods=["POST"])
@limiter.limit("120 per hour")
def hit():
    if is_owner():
        return jsonify({"ok": True})          # don't count your own visits/refreshes
    _ensure()
    day = time.strftime("%Y-%m-%d", time.gmtime())
    raw = _client_ip() + "|" + request.headers.get("User-Agent", "") + "|" + day + "|" + _PEPPER
    visitor = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    body = request.get_json(silent=True) or {}
    ref = _ref_host(body.get("ref") if isinstance(body, dict) else None)
    conn = notes_db()
    try:
        conn.execute(
            "INSERT INTO visits (day, ts, visitor, ref) VALUES (?,?,?,?)",
            (day, int(time.time()), visitor, ref),
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()
    return jsonify({"ok": True})


@bp.route("/api/stats/owner", methods=["GET"])
def owner():
    # Tells the frontend whether to show the Stats tab. Just a yes/no.
    return jsonify({"owner": is_owner()})


@bp.route("/api/stats", methods=["GET"])
def stats():
    if not is_owner():
        return jsonify({"error": "not found"}), 404
    _ensure()
    conn = notes_db()
    try:
        def one(sql, args=()):
            r = conn.execute(sql, args).fetchone()
            return (r[0] or 0) if r else 0
        today = time.strftime("%Y-%m-%d", time.gmtime())
        d7 = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 6 * 86400))
        d30 = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 29 * 86400))
        total = one("SELECT count(*) FROM visits")
        uniq = one("SELECT count(DISTINCT visitor) FROM visits")
        v_today = one("SELECT count(*) FROM visits WHERE day = ?", (today,))
        v7 = one("SELECT count(*) FROM visits WHERE day >= ?", (d7,))
        v30 = one("SELECT count(*) FROM visits WHERE day >= ?", (d30,))
        by_day = [
            {"day": r["day"], "views": r["v"], "uniques": r["u"]}
            for r in conn.execute(
                "SELECT day, count(*) AS v, count(DISTINCT visitor) AS u FROM visits"
                " WHERE day >= ? GROUP BY day ORDER BY day", (d30,))
        ]
        top_ref = [
            {"ref": r["ref"], "n": r["n"]}
            for r in conn.execute(
                "SELECT ref, count(*) AS n FROM visits GROUP BY ref ORDER BY n DESC LIMIT 8")
        ]
        # Registered accounts (notes.db users table, created by views_notes). last_seen
        # is the newest still-valid login token for that account, or None. Guarded in
        # case no one has signed up yet and the table doesn't exist.
        try:
            accounts = [
                {"email": r["email"], "created": r["created"], "last_seen": r["last_seen"]}
                for r in conn.execute(
                    "SELECT u.email AS email, u.created AS created,"
                    " (SELECT max(created) FROM tokens t WHERE t.user_id = u.id) AS last_seen"
                    " FROM users u ORDER BY u.created DESC")
            ]
        except sqlite3.Error:
            accounts = []
    finally:
        conn.close()
    return jsonify({
        "total_views": total, "unique_visitors": uniq,
        "today": v_today, "last7": v7, "last30": v30,
        "by_day": by_day, "top_ref": top_ref,
        "accounts": accounts,
    })
