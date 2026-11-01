#!/usr/bin/env python3
"""Visitor stats — private, owner-only, in-house (no third party).

A tiny page-view counter kept in notes.db. The browser pings /api/stats/hit once
per page load; we store the day, a one-way DAILY hash of IP+browser (so the same
person on the same day counts as one "unique", and the hash can't be linked across
days or turned back into an IP), the referring site, where the load landed (app
tab + a cleaned address), mobile/desktop, whether it was a signed-in load, and
how many days since this browser's last visit (the browser works that out itself).
The owner's OWN visits are skipped. /api/stats returns the summary and is
owner-gated (404 to everyone else). Finished days are frozen into visits_daily
and raw rows are dropped after 90 days — see stats_rollup.py.

Privacy: no cookies, no raw IPs, no browser strings, no PII. Just counts.
"""
import hashlib
import sqlite3
import time
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, request

import stats_rollup as sr
from core import notes_db, limiter
from views_notes import is_owner, _user_for_token, _ensure_tables, OWNER_EMAIL

bp = Blueprint("stats", __name__)

_PEPPER = "lexica-visit-v1"   # makes the daily visitor hash not trivially reversible
_ready = False                # tables checked once per worker


def _ensure():
    global _ready
    if _ready:
        return
    conn = notes_db()
    try:
        sr.ensure(conn)
    finally:
        conn.close()
    _ready = True


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
    ua_raw = request.headers.get("User-Agent", "")
    raw = _client_ip() + "|" + ua_raw + "|" + day + "|" + _PEPPER
    visitor = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        body = {}
    ref = _ref_host(body.get("ref"))
    surface = sr.clean_surface(body.get("surface"))
    path = sr.clean_path(body.get("path"))
    gap = sr.clean_gap(body.get("gap"))
    conn = notes_db()
    try:
        uid = _user_for_token(conn)
        conn.execute(
            "INSERT INTO visits (day, ts, visitor, ref, surface, path, ua, acct, gap)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (day, int(time.time()), visitor, ref, surface, path,
             sr.ua_family(ua_raw), 1 if uid else 0, gap),
        )
        if uid:
            try:
                conn.execute(
                    "UPDATE users SET last_seen = ? WHERE id = ?"
                    " AND (last_seen IS NULL OR last_seen < ?)", (day, uid, day))
            except sqlite3.Error:
                pass                          # column not added yet — next admin read adds it
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


def _accounts(conn):
    """Every account with signup day + last-seen day (a signed-in visit or a sign-in,
    whichever is later). Empty if no one has signed up yet."""
    try:
        rows = conn.execute(
            "SELECT u.email AS email, u.created AS created, u.last_seen AS seen,"
            " (SELECT max(created) FROM tokens t WHERE t.user_id = u.id) AS login"
            " FROM users u").fetchall()
    except sqlite3.Error:
        return []
    out = []
    for r in rows:
        seen = max((r["seen"] or "")[:10], (r["login"] or "")[:10]) or None
        email = r["email"] or ""
        out.append({"email": email, "created": (r["created"] or "")[:10] or None,
                    "last_seen": seen,
                    "owner": bool(OWNER_EMAIL) and email.strip().lower() == OWNER_EMAIL})
    return out


@bp.route("/api/stats", methods=["GET"])
def stats():
    if not is_owner():
        return jsonify({"error": "not found"}), 404
    _ensure()
    _ensure_tables()                          # adds users.last_seen on an older db
    range_key = request.args.get("range", "30d")
    if range_key not in sr.RANGES:
        range_key = "30d"
    today = time.strftime("%Y-%m-%d", time.gmtime())
    conn = notes_db()
    try:
        try:
            sr.rollup(conn, today)
        except sqlite3.Error:
            pass                              # busy — load_days counts unfrozen days live
        days = sr.load_days(conn, today, sr.load_lo(today, range_key))
        accounts = _accounts(conn)
    finally:
        conn.close()
    return jsonify(sr.summarize(days, today, range_key, accounts))
