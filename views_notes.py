#!/usr/bin/env python3
"""Study-notes accounts + sync — the only visitor-write path on the site.

Notes are browser-local first (static/src/12-notes-store.jsx). Sync is opt-in:
a visitor signs up / logs in with an email + password, and their notes sync to
that account on every device they log into. The app stays fully usable with no
account (browse + local notes), exactly as before.

Auth: email + password (password stored ONE-WAY hashed via werkzeug — never
readable). Stay-logged-in is a random bearer token kept in the browser; the
server keeps a table of valid tokens (logout deletes the token). NO email
verification and NO "forgot password" yet — password reset needs the site to
send email (SMTP), which isn't configured on PA. Add it later (a reset token
mailed to the address). Until then a lost password = no self-serve recovery.

Storage: notes.db (core.notes_db), kept OUT of bible.db (corpus gets rebuilt;
user data must survive that). Tables: users, tokens, notes (one row per note,
keyed by owner = "u<user_id>").

Endpoints:
  POST /api/auth/signup  {email, password} -> {token, email}
  POST /api/auth/login   {email, password} -> {token, email}
  POST /api/auth/logout                     -> {ok}
  GET  /api/auth/me                          -> {email} | 401
  POST /api/notes/sync   {notes:[...]}       -> {notes:[...]}   (Authorization: Bearer <token>)
Two-way last-write-wins merge by note id; deletes carry a tombstone.
"""
import json
import os
import re
import secrets
import sqlite3
import time

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

from core import notes_db, limiter

bp = Blueprint("notes", __name__)

# Optional "Sign in with Google" — only turns on when the Client ID is in the
# environment AND the google-auth library is installed. Both checked lazily so a
# code deploy before `pip install` (or before the env var is set) never breaks
# the site; the Google button just stays hidden until it's ready.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")


def _google_ready():
    if not GOOGLE_CLIENT_ID:
        return False
    try:
        import google.oauth2.id_token  # noqa: F401
        return True
    except Exception:
        return False

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_NOTES = 5000            # per account
_MAX_NOTE_BYTES = 8000       # one anchored note's JSON
_MAX_JOURNAL_BYTES = 64000   # one free-form journal page's JSON (long essays)
_MAX_BODY_BYTES = 4_000_000  # whole request
_MIN_PASSWORD = 8


def _ensure_tables():
    conn = notes_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,"
            " pass_hash TEXT NOT NULL, created TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS tokens ("
            " token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            " code TEXT NOT NULL, id TEXT NOT NULL, json TEXT NOT NULL,"
            " updated TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,"
            " PRIMARY KEY (code, id))"
        )
        # Chronological reading-plan progress — one small blob per account
        # ({text: {day, streak, last, done}}). Synced by /api/plan/sync.
        conn.execute(
            "CREATE TABLE IF NOT EXISTS plan ("
            " code TEXT PRIMARY KEY, json TEXT NOT NULL, updated TEXT NOT NULL)"
        )
        # Role tier per account (added 2026-06-11). Older dbs predate the column.
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "role" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        conn.commit()
    finally:
        conn.close()


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _user_for_token(conn):
    """Return the user_id for the request's bearer token, or None."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    row = conn.execute("SELECT user_id FROM tokens WHERE token = ?", (token,)).fetchone()
    return row["user_id"] if row else None


# The site OWNER — one person (you), identified by email in the WSGI env. Used to
# gate owner-only features (visitor stats, the ESV reading text). Falls back to the
# older ESV_OWNER_EMAIL so a single var (OWNER_EMAIL) can cover both. Unset -> no one
# is the owner (features stay off), so a deploy before setup is safe.
OWNER_EMAIL = (os.environ.get("OWNER_EMAIL") or os.environ.get("ESV_OWNER_EMAIL") or "").strip().lower()


# Account tiers (lowest → highest). A signed-out visitor is "nologin" (not stored).
#   user   — any signed-in account (the default for a new signup)
#   berean — trusted friends; unlocks the gated reading texts (ESV / NIV)
#   admin  — full control incl. visitor stats + role management (that's you)
# The OWNER_EMAIL account is ALWAYS admin (bootstrap — you can't lock yourself out),
# whatever its stored role says.
_ROLES = ("user", "berean", "admin")


def role_for_token():
    """The caller's tier: 'admin' / 'berean' / 'user' when signed in, else 'nologin'."""
    conn = notes_db()
    try:
        uid = _user_for_token(conn)
        if uid is None:
            return "nologin"
        row = conn.execute("SELECT email FROM users WHERE id = ?", (uid,)).fetchone()
        if not row:
            return "nologin"
        # Owner email is always admin (bootstrap) — true even before the role column exists.
        if OWNER_EMAIL and (row["email"] or "").strip().lower() == OWNER_EMAIL:
            return "admin"
        try:
            rr = conn.execute("SELECT role FROM users WHERE id = ?", (uid,)).fetchone()
            role = (rr["role"] or "user").strip().lower() if rr else "user"
        except sqlite3.Error:
            role = "user"          # role column not migrated yet -> default tier
        return role if role in _ROLES else "user"
    except sqlite3.Error:
        return "nologin"
    finally:
        conn.close()


def is_admin():
    """Full-control tier (visitor stats, role management)."""
    return role_for_token() == "admin"


def is_berean():
    """Berean+ — unlocks the gated reading texts (ESV / NIV). Admin counts too."""
    return role_for_token() in ("berean", "admin")


def is_logged_in():
    """Any signed-in account (for login-gated features like AI search)."""
    return role_for_token() != "nologin"


def is_owner():
    """Back-compat alias: 'owner-only' now means admin (the owner email is always
    admin). Keeps the visitor-stats gate working unchanged."""
    return is_admin()


def _read_creds():
    try:
        body = json.loads(request.get_data(cache=False) or b"{}")
    except (ValueError, TypeError):
        return None, None
    if not isinstance(body, dict):
        return None, None
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    return email, password


@bp.route("/api/auth/signup", methods=["POST"])
@limiter.limit("20 per hour")
def signup():
    email, password = _read_creds()
    if not email or not _EMAIL_RE.match(email) or len(email) > 200:
        return jsonify({"error": "Enter a valid email."}), 400
    if not isinstance(password, str) or len(password) < _MIN_PASSWORD:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    _ensure_tables()
    conn = notes_db()
    try:
        try:
            cur = conn.execute(
                "INSERT INTO users (email, pass_hash, created) VALUES (?,?,?)",
                (email, generate_password_hash(password), _now()),
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "That email is already registered."}), 409
        user_id = cur.lastrowid
        token = secrets.token_urlsafe(24)
        conn.execute("INSERT INTO tokens (token, user_id, created) VALUES (?,?,?)", (token, user_id, _now()))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"token": token, "email": email})


@bp.route("/api/auth/login", methods=["POST"])
@limiter.limit("30 per hour")
def login():
    email, password = _read_creds()
    if not email or not password:
        return jsonify({"error": "Email and password required."}), 400
    _ensure_tables()
    conn = notes_db()
    try:
        row = conn.execute("SELECT id, pass_hash FROM users WHERE email = ?", (email,)).fetchone()
        if not row or not check_password_hash(row["pass_hash"], password):
            return jsonify({"error": "Wrong email or password."}), 401
        token = secrets.token_urlsafe(24)
        conn.execute("INSERT INTO tokens (token, user_id, created) VALUES (?,?,?)", (token, row["id"], _now()))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"token": token, "email": email})


@bp.route("/api/auth/logout", methods=["POST"])
def logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        conn = notes_db()
        try:
            conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            conn.close()
    return jsonify({"ok": True})


@bp.route("/api/auth/config", methods=["GET"])
def auth_config():
    # Tells the frontend whether to show the Google button (and which Client ID).
    return jsonify({"google_client_id": GOOGLE_CLIENT_ID if _google_ready() else None})


@bp.route("/api/auth/google", methods=["POST"])
@limiter.limit("60 per hour")
def google_auth():
    if not _google_ready():
        return jsonify({"error": "Google sign-in isn't set up."}), 503
    from google.oauth2 import id_token as g_id_token
    from google.auth.transport import requests as g_requests
    try:
        body = json.loads(request.get_data(cache=False) or b"{}")
    except (ValueError, TypeError):
        return jsonify({"error": "bad request"}), 400
    cred = (body or {}).get("credential")
    if not isinstance(cred, str) or not cred:
        return jsonify({"error": "bad request"}), 400
    try:
        info = g_id_token.verify_oauth2_token(cred, g_requests.Request(), GOOGLE_CLIENT_ID)
    except Exception:
        return jsonify({"error": "Google sign-in failed."}), 401
    email = (info.get("email") or "").strip().lower()
    if not email or not info.get("email_verified"):
        return jsonify({"error": "No verified email on that Google account."}), 401
    _ensure_tables()
    conn = notes_db()
    try:
        # Find-or-create by email — a Google login and an email/password login with
        # the same address are the same account (Google verified they own it).
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            uid = row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO users (email, pass_hash, created) VALUES (?,?,?)",
                # No usable password for a Google-only account; a random hash blocks
                # password login until they set one.
                (email, generate_password_hash(secrets.token_urlsafe(16)), _now()),
            )
            uid = cur.lastrowid
        token = secrets.token_urlsafe(24)
        conn.execute("INSERT INTO tokens (token, user_id, created) VALUES (?,?,?)", (token, uid, _now()))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"token": token, "email": email})


@bp.route("/api/auth/me", methods=["GET"])
def me():
    _ensure_tables()
    conn = notes_db()
    try:
        uid = _user_for_token(conn)
        if uid is None:
            return jsonify({"error": "not signed in"}), 401
        row = conn.execute("SELECT email FROM users WHERE id = ?", (uid,)).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "not signed in"}), 401
    return jsonify({"email": row["email"], "role": role_for_token()})


@bp.route("/api/admin/users", methods=["GET"])
def admin_users():
    """Admin-only: list accounts + roles for the in-app admin page. 404 otherwise."""
    if not is_admin():
        return jsonify({"error": "not found"}), 404
    _ensure_tables()
    conn = notes_db()
    try:
        rows = conn.execute(
            "SELECT id, email, role, created FROM users ORDER BY created"
        ).fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        is_owner_row = bool(OWNER_EMAIL and (r["email"] or "").strip().lower() == OWNER_EMAIL)
        out.append({
            "id": r["id"],
            "email": r["email"],
            "role": "admin" if is_owner_row else (r["role"] or "user"),
            "owner": is_owner_row,          # the owner-email account — role is locked to admin
            "created": r["created"],
        })
    return jsonify({"users": out})


@bp.route("/api/admin/role", methods=["POST"])
@limiter.limit("60 per hour")
def admin_set_role():
    """Admin-only: set one account's role (user / berean / admin)."""
    if not is_admin():
        return jsonify({"error": "not found"}), 404
    try:
        body = json.loads(request.get_data(cache=False) or b"{}")
    except (ValueError, TypeError):
        return jsonify({"error": "bad request"}), 400
    uid = (body or {}).get("user_id")
    role = ((body or {}).get("role") or "").strip().lower()
    if role not in _ROLES:
        return jsonify({"error": "bad role"}), 400
    _ensure_tables()
    conn = notes_db()
    try:
        row = conn.execute("SELECT email FROM users WHERE id = ?", (uid,)).fetchone()
        if not row:
            return jsonify({"error": "no such user"}), 404
        if OWNER_EMAIL and (row["email"] or "").strip().lower() == OWNER_EMAIL:
            return jsonify({"error": "The owner account is always admin."}), 400
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, uid))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@bp.route("/api/notes/sync", methods=["POST"])
@limiter.limit("200 per hour")
def notes_sync():
    raw = request.get_data(cache=False) or b""
    if len(raw) > _MAX_BODY_BYTES:
        return jsonify({"error": "too large"}), 413
    try:
        body = json.loads(raw or b"{}")
    except (ValueError, TypeError):
        return jsonify({"error": "bad request"}), 400
    if not isinstance(body, dict):
        return jsonify({"error": "bad request"}), 400

    _ensure_tables()
    conn = notes_db()
    try:
        uid = _user_for_token(conn)
        if uid is None:
            return jsonify({"error": "not signed in"}), 401
        owner = "u" + str(uid)

        incoming = body.get("notes") or []
        if not isinstance(incoming, list) or len(incoming) > _MAX_NOTES:
            return jsonify({"error": "bad notes"}), 400

        existing = {
            r["id"]: r["updated"]
            for r in conn.execute("SELECT id, updated FROM notes WHERE code = ?", (owner,))
        }
        for n in incoming:
            if not isinstance(n, dict):
                continue
            nid = n.get("id")
            upd = n.get("updated") or ""
            if not isinstance(nid, str) or not nid or not isinstance(upd, str):
                continue
            blob = json.dumps(n, separators=(",", ":"))
            cap = _MAX_JOURNAL_BYTES if n.get("kind") == "journal" else _MAX_NOTE_BYTES
            if len(blob) > cap:
                continue
            if nid not in existing or upd > existing[nid]:
                conn.execute(
                    "INSERT OR REPLACE INTO notes (code, id, json, updated, deleted)"
                    " VALUES (?,?,?,?,?)",
                    (owner, nid, blob, upd, 1 if n.get("deleted") else 0),
                )
                existing[nid] = upd
        count = conn.execute("SELECT count(*) FROM notes WHERE code = ?", (owner,)).fetchone()[0]
        if count > _MAX_NOTES:
            conn.execute(
                "DELETE FROM notes WHERE code = ? AND id IN ("
                " SELECT id FROM notes WHERE code = ? ORDER BY updated ASC LIMIT ?)",
                (owner, owner, count - _MAX_NOTES),
            )
        conn.commit()
        rows = conn.execute("SELECT json FROM notes WHERE code = ?", (owner,)).fetchall()
    except sqlite3.Error:
        return jsonify({"error": "sync failed"}), 500
    finally:
        conn.close()

    out = []
    for r in rows:
        try:
            out.append(json.loads(r["json"]))
        except (ValueError, TypeError):
            continue
    return jsonify({"notes": out, "server_time": int(time.time())})


def _merge_plan(stored, incoming):
    """Union the two reading-plan blobs ({text: {day, streak, last, done}}): combine
    the completed-day sets, keep the higher streak, the latest last-read date, and the
    furthest pointer. So reading on two devices never loses a checked day."""
    if not isinstance(stored, dict):
        stored = {}
    if not isinstance(incoming, dict):
        incoming = {}
    out = {}
    for text in set(stored) | set(incoming):
        a = stored.get(text) if isinstance(stored.get(text), dict) else {}
        b = incoming.get(text) if isinstance(incoming.get(text), dict) else {}
        days = set()
        for src in (a.get("done") or [], b.get("done") or []):
            if isinstance(src, list):
                for d in src:
                    if isinstance(d, (int, float)) and 1 <= d <= 400:
                        days.add(int(d))
        out[text] = {
            "day": max(int(a.get("day") or 1), int(b.get("day") or 1)),
            "streak": max(int(a.get("streak") or 0), int(b.get("streak") or 0)),
            "last": (max(a.get("last") or "", b.get("last") or "") or None),
            "done": sorted(days),
        }
    return out


@bp.route("/api/plan/sync", methods=["POST"])
@limiter.limit("200 per hour")
def plan_sync():
    raw = request.get_data(cache=False) or b""
    if len(raw) > 200_000:
        return jsonify({"error": "too large"}), 413
    try:
        body = json.loads(raw or b"{}")
    except (ValueError, TypeError):
        return jsonify({"error": "bad request"}), 400
    if not isinstance(body, dict):
        return jsonify({"error": "bad request"}), 400
    incoming = body.get("plan") or {}
    if not isinstance(incoming, dict) or len(incoming) > 50:
        return jsonify({"error": "bad plan"}), 400

    _ensure_tables()
    conn = notes_db()
    try:
        uid = _user_for_token(conn)
        if uid is None:
            return jsonify({"error": "not signed in"}), 401
        owner = "u" + str(uid)
        row = conn.execute("SELECT json FROM plan WHERE code = ?", (owner,)).fetchone()
        stored = {}
        if row:
            try:
                stored = json.loads(row["json"])
            except (ValueError, TypeError):
                stored = {}
        merged = _merge_plan(stored, incoming)
        blob = json.dumps(merged, separators=(",", ":"))
        if len(blob) <= 200_000:
            conn.execute(
                "INSERT OR REPLACE INTO plan (code, json, updated) VALUES (?,?,?)",
                (owner, blob, _now()),
            )
            conn.commit()
    except sqlite3.Error:
        return jsonify({"error": "sync failed"}), 500
    finally:
        conn.close()
    return jsonify({"plan": merged, "server_time": int(time.time())})


@bp.route("/api/plan/clear", methods=["POST"])
@limiter.limit("200 per hour")
def plan_clear():
    """Clear the account's saved reading-plan progress — one text ({text:"abp"}) or all
    of it ({all:true}). A hard delete on the server, so the union merge won't bring it
    back on the next sync."""
    try:
        body = json.loads(request.get_data(cache=False) or b"{}")
    except (ValueError, TypeError):
        return jsonify({"error": "bad request"}), 400
    if not isinstance(body, dict):
        return jsonify({"error": "bad request"}), 400

    _ensure_tables()
    conn = notes_db()
    try:
        uid = _user_for_token(conn)
        if uid is None:
            return jsonify({"error": "not signed in"}), 401
        owner = "u" + str(uid)
        if body.get("all"):
            conn.execute("DELETE FROM plan WHERE code = ?", (owner,))
            conn.commit()
            return jsonify({"plan": {}})
        text = body.get("text")
        if not isinstance(text, str) or not text:
            return jsonify({"error": "bad request"}), 400
        row = conn.execute("SELECT json FROM plan WHERE code = ?", (owner,)).fetchone()
        stored = {}
        if row:
            try:
                stored = json.loads(row["json"])
            except (ValueError, TypeError):
                stored = {}
        if isinstance(stored, dict):
            stored.pop(text, None)
        else:
            stored = {}
        conn.execute(
            "INSERT OR REPLACE INTO plan (code, json, updated) VALUES (?,?,?)",
            (owner, json.dumps(stored, separators=(",", ":")), _now()),
        )
        conn.commit()
        return jsonify({"plan": stored})
    except sqlite3.Error:
        return jsonify({"error": "clear failed"}), 500
    finally:
        conn.close()
