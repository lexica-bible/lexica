#!/usr/bin/env python3
"""NIV — PERSONAL, owner-only reading text (server-enforced gate).

The NIV is Biblica/Zondervan-copyrighted, so it is NOT a public corpus like
KJV/BSB. The owner owns NIV copies and uses it for his OWN study only — personal
use, not publishing. EVERY route here checks the caller's login token against the
owner's email (the shared site-owner gate, OWNER_EMAIL in the WSGI env) and
returns 404 to everyone else. Hiding the toggle is NOT the protection — the
address itself must not work for anyone but the owner, and that's enforced here.

Text lives in its OWN file, niv.db (core.niv_db), loaded on PA by
scripts/load_niv.py — never in bible.db, never in git (*.db is gitignored).

This mirrors views_esv.py but is TEXT-ONLY: there is no NIV audio route, because
NIV audio is commercially licensed and isn't in FCBH's openly-available filesets.
If an NIV fileset ever turns up, copy the /api/esv/audio route here.

Endpoints (all owner-gated):
  GET /api/niv/status                    -> {owner: bool}   (turns the toggle on)
  GET /api/niv/chapter/<book>/<chapter>  -> [{verse, verse_text, heading}]
All require Authorization: Bearer <token> whose account == the owner.
"""
import sqlite3

from flask import Blueprint, jsonify

from core import db_ro, niv_db, _KJV_BOOK_ID
from views_notes import is_berean as _can_niv   # NIV reading text = berean+ (trusted friends)

bp = Blueprint("niv", __name__)


@bp.route("/api/niv/status")
def niv_status():
    """The frontend asks this to decide whether to show the NIV toggle. It's just
    a yes/no — the owner's email never leaves the server."""
    return jsonify({"owner": _can_niv()})


@bp.route("/api/niv/chapter/<book>/<int:chapter>")
def niv_chapter(book, chapter):
    if not _can_niv():
        return jsonify({"error": "not found"}), 404      # opaque to non-owners
    book_id = _KJV_BOOK_ID.get(book)
    if book_id is None:
        return jsonify([])
    # NIV text from niv.db; section headings (shared) from bible.db's pericopes.
    try:
        conn = niv_db()
    except sqlite3.OperationalError:
        return jsonify([])                                # niv.db not loaded yet
    try:
        rows = conn.execute(
            "SELECT verse_num, verse_text FROM niv_verses"
            " WHERE book_id = ? AND chapter = ? ORDER BY verse_num",
            (book_id, chapter),
        ).fetchall()
    except sqlite3.OperationalError:
        return jsonify([])                                # niv_verses table missing
    finally:
        conn.close()

    headings = {}
    try:
        bconn = db_ro()
        try:
            for r in bconn.execute(
                "SELECT verse, heading FROM pericopes WHERE book = ? AND chapter = ?",
                (book, chapter),
            ):
                headings[r["verse"]] = r["heading"]
        finally:
            bconn.close()
    except sqlite3.OperationalError:
        pass

    return jsonify([
        {
            "verse": r["verse_num"],
            "verse_text": r["verse_text"],
            "heading": headings.get(r["verse_num"]),
        }
        for r in rows
    ])
