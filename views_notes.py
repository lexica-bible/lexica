#!/usr/bin/env python3
"""Study-notes sync — the ONLY visitor-write path on the site.

Notes are browser-local first (static/src/12-notes-store.jsx). Sync is opt-in:
a visitor turns it on, which mints a random "sync code". That code is the only
identity — anyone holding it can read/write that bucket of notes, so it must be
long + unguessable (the client makes a 20+ char code). No login, no email, no
recovery if the code is lost. This is the deliberate "light" option; full email
accounts are a future upgrade (a code can later be claimed by an email).

Storage: notes.db (core.notes_db), kept OUT of bible.db. One row per note:
  (code, id) primary key, json blob, updated (ISO), deleted flag.

Endpoint: POST /api/notes/sync  {code, notes:[...]}  ->  {notes:[...]}
Two-way last-write-wins merge: incoming notes fold into the bucket (newer
`updated` wins, deletes carry a tombstone), then the whole bucket comes back so
the client folds it in too. Caps + the AI-tier rate limit guard against abuse.
"""
import json
import re
import sqlite3
import time

from flask import Blueprint, jsonify, request

from core import notes_db, limiter

bp = Blueprint("notes", __name__)

_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{12,64}$")   # client mints ~20 chars
_MAX_NOTES = 5000            # per code — a generous personal ceiling
_MAX_NOTE_BYTES = 8000       # one note's JSON
_MAX_BODY_BYTES = 4_000_000  # whole request


def _ensure_table():
    conn = notes_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            " code TEXT NOT NULL, id TEXT NOT NULL, json TEXT NOT NULL,"
            " updated TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,"
            " PRIMARY KEY (code, id))"
        )
        conn.commit()
    finally:
        conn.close()


@bp.route("/api/notes/sync", methods=["POST"])
@limiter.limit("120 per hour")
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

    code = body.get("code")
    if not isinstance(code, str) or not _CODE_RE.match(code):
        return jsonify({"error": "bad code"}), 400

    incoming = body.get("notes") or []
    if not isinstance(incoming, list) or len(incoming) > _MAX_NOTES:
        return jsonify({"error": "bad notes"}), 400

    _ensure_table()
    conn = notes_db()
    try:
        # Fold each incoming note in: newer `updated` wins (a tombstone is just a
        # note carrying deleted=true, so deletes propagate like any other edit).
        existing = {
            r["id"]: r["updated"]
            for r in conn.execute("SELECT id, updated FROM notes WHERE code = ?", (code,))
        }
        for n in incoming:
            if not isinstance(n, dict):
                continue
            nid = n.get("id")
            upd = n.get("updated") or ""
            if not isinstance(nid, str) or not nid or not isinstance(upd, str):
                continue
            blob = json.dumps(n, separators=(",", ":"))
            if len(blob) > _MAX_NOTE_BYTES:
                continue
            if nid not in existing or upd > existing[nid]:
                conn.execute(
                    "INSERT OR REPLACE INTO notes (code, id, json, updated, deleted)"
                    " VALUES (?,?,?,?,?)",
                    (code, nid, blob, upd, 1 if n.get("deleted") else 0),
                )
                existing[nid] = upd
        # Enforce the per-code ceiling (after merge), trimming oldest if somehow over.
        count = conn.execute("SELECT count(*) FROM notes WHERE code = ?", (code,)).fetchone()[0]
        if count > _MAX_NOTES:
            conn.execute(
                "DELETE FROM notes WHERE code = ? AND id IN ("
                " SELECT id FROM notes WHERE code = ? ORDER BY updated ASC LIMIT ?)",
                (code, code, count - _MAX_NOTES),
            )
        conn.commit()
        rows = conn.execute("SELECT json FROM notes WHERE code = ?", (code,)).fetchall()
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
