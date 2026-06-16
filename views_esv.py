#!/usr/bin/env python3
"""ESV — PERSONAL, owner-only reading text + audio (server-enforced gate).

The ESV is Crossway-copyrighted, so it is NOT a public corpus like KJV/BSB. The
owner owns ESV copies and uses it for his OWN study only — personal use, not
publishing. EVERY route here checks the caller's login token against the owner's
email (ESV_OWNER_EMAIL, set in the WSGI env like the other secrets) and returns
404 to everyone else. Hiding the toggle is NOT the protection — the address
itself must not work for anyone but the owner, and that's enforced right here.

Text lives in its OWN file, esv.db (core.esv_db), loaded on PA by
scripts/load_esv.py — never in bible.db, never in git (*.db is gitignored).

Audio (optional) prefers Crossway's OWN ESV API (api.esv.org, ESV_API_TOKEN) — the
Max McLean reading of the WHOLE Bible, with an instant self-serve token. It falls
back to Faith Comes By Hearing's Bible Brain (FCBH_API_KEY, NT-only) when only that
key is set. Either way the route fetches a short-lived signed mp3 URL server-side
(the key/token stays in the WSGI env, never reaches the browser) and hands back
just that URL.

Endpoints (all owner-gated):
  GET /api/esv/status                    -> {owner: bool}   (turns the toggle on)
  GET /api/esv/chapter/<book>/<chapter>  -> [{verse, verse_text, heading}]
  GET /api/esv/audio/<book>/<chapter>    -> {url: <mp3>|null}
All require Authorization: Bearer <token> whose account == the owner.
"""
import json
import os
import sqlite3
import urllib.parse
import urllib.request

from flask import Blueprint, jsonify

from core import db_ro, esv_db, _KJV_BOOK_ID, _USFM_BOOK
from views_notes import is_berean as _can_esv   # ESV reading text = berean+ (trusted friends)

bp = Blueprint("esv", __name__)

# Bible Brain (FCBH) audio. Key + filesets in the WSGI env. ENGESVN2DA is
# ENG / ESV / New Testament / multi-voice + background music / audio, so it's
# NT-only; set an OT fileset too if you have one, otherwise OT chapters have no
# audio (the Listen button just won't appear).
FCBH_API_KEY   = os.environ.get("FCBH_API_KEY")
FCBH_API_BASE  = os.environ.get("FCBH_API_BASE", "https://4.dbt.io/api")
ESV_FILESET_NT = os.environ.get("ESV_AUDIO_FILESET_NT", "ENGESVN2DA")
ESV_FILESET_OT = os.environ.get("ESV_AUDIO_FILESET_OT")   # optional

_USFM = _USFM_BOOK   # app book-abbrev -> USFM code (what FCBH expects)

# Crossway's OWN ESV API (api.esv.org) audio — the Max McLean reading, WHOLE Bible
# (not NT-only like the FCBH ESV fileset), and the token is instant self-serve. The
# audio endpoint 302-redirects to a short-lived signed mp3 URL that plays in the
# browser without the token, so we capture that redirect target and hand it back
# (the token stays server-side). Preferred over FCBH whenever ESV_API_TOKEN is set.
ESV_API_TOKEN = os.environ.get("ESV_API_TOKEN")           # api.esv.org token (free)
ESV_API_AUDIO = "https://api.esv.org/v3/passage/audio/"
# Proper English book names for the ?q= passage (e.g. "1 Corinthians 13").
_ESV_BOOK_NAME = {
    1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
    6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
    11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles",
    15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalm",
    20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
    24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel", 28: "Hosea",
    29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah", 33: "Micah", 34: "Nahum",
    35: "Habakkuk", 36: "Zephaniah", 37: "Haggai", 38: "Zechariah", 39: "Malachi",
    40: "Matthew", 41: "Mark", 42: "Luke", 43: "John", 44: "Acts", 45: "Romans",
    46: "1 Corinthians", 47: "2 Corinthians", 48: "Galatians", 49: "Ephesians",
    50: "Philippians", 51: "Colossians", 52: "1 Thessalonians",
    53: "2 Thessalonians", 54: "1 Timothy", 55: "2 Timothy", 56: "Titus",
    57: "Philemon", 58: "Hebrews", 59: "James", 60: "1 Peter", 61: "2 Peter",
    62: "1 John", 63: "2 John", 64: "3 John", 65: "Jude", 66: "Revelation",
}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Stop urllib following Crossway's 302 — we want the redirect TARGET (the signed
    mp3 URL), not the multi-MB mp3 itself."""
    def http_error_302(self, req, fp, code, msg, headers):
        return fp
    http_error_301 = http_error_303 = http_error_307 = http_error_302


_esv_opener = urllib.request.build_opener(_NoRedirect)


def _crossway_audio_url(passage):
    """Return the short-lived signed mp3 URL Crossway redirects to for a passage
    (e.g. 'John 1'), playable in the browser without the token. None on any failure."""
    url = ESV_API_AUDIO + "?q=" + urllib.parse.quote(passage)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Token {ESV_API_TOKEN}",
        "User-Agent": "lexica/1.0",
    })
    try:
        with _esv_opener.open(req, timeout=10) as resp:
            loc = resp.headers.get("Location")
            if loc:
                return loc
            if getattr(resp, "status", None) == 200:   # rare: served the mp3 directly
                return resp.geturl()
    except Exception:
        return None
    return None


@bp.route("/api/esv/status")
def esv_status():
    """The frontend asks this to decide whether to show the ESV toggle. It's just
    a yes/no — the owner's email never leaves the server."""
    return jsonify({"owner": _can_esv()})


@bp.route("/api/esv/chapter/<book>/<int:chapter>")
def esv_chapter(book, chapter):
    if not _can_esv():
        return jsonify({"error": "not found"}), 404      # opaque to non-owners
    book_id = _KJV_BOOK_ID.get(book)
    if book_id is None:
        return jsonify([])
    # ESV text from esv.db; section headings (shared) from bible.db's pericopes.
    try:
        conn = esv_db()
    except sqlite3.OperationalError:
        return jsonify([])                                # esv.db not loaded yet
    try:
        rows = conn.execute(
            "SELECT verse_num, verse_text FROM esv_verses"
            " WHERE book_id = ? AND chapter = ? ORDER BY verse_num",
            (book_id, chapter),
        ).fetchall()
    except sqlite3.OperationalError:
        return jsonify([])                                # esv_verses table missing
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


@bp.route("/api/esv/audio/<book>/<int:chapter>")
def esv_audio(book, chapter):
    if not _can_esv():
        return jsonify({"error": "not found"}), 404
    book_id = _KJV_BOOK_ID.get(book)
    if book_id is None:
        return jsonify({"url": None})

    # Crossway first (whole Bible, instant token). If its token is set, it's the
    # only source we use; FCBH is the fallback when only the FCBH key is present.
    if ESV_API_TOKEN:
        name = _ESV_BOOK_NAME.get(book_id)
        url = _crossway_audio_url(f"{name} {chapter}") if name else None
        return jsonify({"url": url})

    if not FCBH_API_KEY:
        return jsonify({"url": None})                     # audio not configured
    usfm = _USFM.get(book)
    if not usfm:
        return jsonify({"url": None})
    fileset = ESV_FILESET_NT if book_id >= 40 else ESV_FILESET_OT   # 40 = Matthew
    if not fileset:
        return jsonify({"url": None})                     # e.g. OT with no OT fileset

    url = (
        f"{FCBH_API_BASE}/bibles/filesets/{urllib.parse.quote(fileset)}/"
        f"{usfm}/{chapter}?v=4&key={urllib.parse.quote(FCBH_API_KEY)}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "lexica/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return jsonify({"url": None})                     # FCBH down / bad key / no audio

    data = payload.get("data") if isinstance(payload, dict) else None
    path = None
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("path"):
                path = item["path"]
                break
    return jsonify({"url": path})
