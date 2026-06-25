#!/usr/bin/env python3
"""Lexica dictionary serve — the verse-grounded word entry for the word card / Word study tab.

Reads the `lexica_def` side table (built on PA by scripts/build_lexica_def.py; not in git) and
hands the stored entry to the frontend's LexicaBody. DEPLOY-SAFE: if the table isn't built yet,
or the word has no entry, it 404s and the card falls back to the existing LSJ path — a code
deploy before the data step can't break anything. Read-only; the build script is the only writer.
"""
import json

from flask import Blueprint, jsonify

from core import db_ro, log
from views_notes import is_admin

bp = Blueprint("lexica", __name__)

# Rollout gate: Lexica entries render for ADMINS ONLY until the feature is proven. The build
# script keeps writing rows regardless — this controls only WHO can read them, so we can build out
# the fork list + loaded terms and view them in the real card without any public user seeing a
# half-tested entry. ONE global flag — flip to False to go public (a single milestone, not a
# per-word rollout). If we later promote entries individually, a `public` column on lexica_def is
# the clean add. Mirrors views_heb's "gate VISIBILITY during rollout".
LEXICA_ADMIN_ONLY = False   # PUBLIC 2026-06-25 — rollout over; served to everyone, incl. logged-out


def _has_lexica(conn):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='lexica_def'"
    ).fetchone() is not None


@bp.route("/api/lexica/<strongs>")
def lexica_def(strongs):
    """The stored Lexica entry for a Strong's number, or 404 (word has none / table not built /
    viewer isn't an admin during rollout)."""
    if LEXICA_ADMIN_ONLY and not is_admin():
        return jsonify({"error": "not found"}), 404      # admin-only rollout — non-admins fall through to LSJ
    sid = (strongs or "").strip().upper()
    if sid[:1] not in ("G", "H"):
        sid = "G" + sid
    conn = db_ro()
    try:
        if not _has_lexica(conn):
            return jsonify({"error": "not found"}), 404      # table not built yet — fall back to LSJ
        row = conn.execute(
            "SELECT def_json FROM lexica_def WHERE strongs = ?", (sid,)
        ).fetchone()
    except Exception as e:
        log.warning("lexica lookup failed for %s: %s", sid, e)
        return jsonify({"error": "lookup failed"}), 500
    finally:
        conn.close()
    if not row or not row["def_json"]:
        return jsonify({"error": "not found"}), 404
    try:
        entry = json.loads(row["def_json"])
    except Exception:
        return jsonify({"error": "bad data"}), 500
    entry.pop("raw", None)        # the browser uses the split fields, not the full prose blob
    return jsonify(entry)
