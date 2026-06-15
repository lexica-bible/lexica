#!/usr/bin/env python3
"""Berean Standard Bible (BSB) routes.

BSB is a reading + plain-text-search corpus only — no word-level / Strong's
data (ABP and KJV already carry that). One table, bsb_verses, mirroring
kjv_verses on the same 1-66 book-id numbering (core._KJV_BOOK_ID).

Two endpoints:
  GET /api/bsb/chapter/<book>/<chapter>  — verses for a chapter (+ pericope headings)
  GET /api/bsb/search?q=&mode=&book=     — eSword-style plain-text find

If bsb_verses hasn't been loaded yet (scripts/load_bsb.py), both endpoints
return empty rather than erroring, so deploying the code before the data is safe.
"""
import sqlite3

from flask import Blueprint, jsonify, request

from core import db_ro, _KJV_BOOK_ID, _USFM_BOOK, usfm_titlecase

bp = Blueprint("bsb", __name__)

# openbible.com hosts the public-domain (CC0) BSB narration. Plain narrator
# (Souer), one mp3 per chapter at a fixed pattern:
#   https://openbible.com/audio/souer/BSB_<NN>_<Abbr>_<CCC>.mp3
# NN = 01-66 book number, Abbr = title-cased USFM code (Gen, Jdg, Mrk, Jhn...),
# CCC = zero-padded chapter. No key, freely streamable, so we just hand the
# browser the URL to play in an <audio> tag.
_BSB_AUDIO_BASE = "https://openbible.com/audio/souer"


@bp.route("/api/bsb/chapter/<book>/<int:chapter>")
def bsb_chapter(book, chapter):
    """A chapter of BSB. Returns each verse with both its plain text (for prose /
    reading) AND a per-word breakdown with Strong's (for chip mode / word study),
    mirroring /api/kjv/chapter. If bsb_words hasn't been loaded yet
    (scripts/load_bsb_words.py), it falls back to text-only with an empty words
    list, so deploying the code before the data is safe."""
    book_id = _KJV_BOOK_ID.get(book)
    if book_id is None:
        return jsonify([])
    conn = db_ro()
    try:
        pericope_rows = conn.execute(
            "SELECT verse, heading FROM pericopes WHERE book = ? AND chapter = ?",
            (book, chapter),
        ).fetchall()
        try:
            word_rows = conn.execute("""
                SELECT bw.verse_num, bw.word_id, bw.verse_pos, bw.word, bw.italic, bw.punc,
                       GROUP_CONCAT(bs.strongs_id) AS strongs_ids,
                       bv.verse_text,
                       MAX(COALESCE(bdb.lemma, lex.lemma))   AS lemma,
                       MAX(COALESCE(bdb.xlit, lex.translit)) AS xlit
                FROM bsb_words bw
                LEFT JOIN bsb_strongs bs ON bs.word_id = bw.word_id
                LEFT JOIN bsb_verses bv ON bv.book_id = bw.book_id
                    AND bv.chapter = bw.chapter AND bv.verse_num = bw.verse_num
                LEFT JOIN bdb ON bdb.strongs_id = bs.strongs_id AND bs.strongs_id LIKE 'H%'
                LEFT JOIN lexicon lex ON lex.strongs_g = bs.strongs_id
                WHERE bw.book_id = ? AND bw.chapter = ?
                GROUP BY bw.word_id, bw.verse_num, bw.verse_pos, bw.word, bw.italic, bw.punc, bv.verse_text
                ORDER BY bw.verse_num, bw.verse_pos
            """, (book_id, chapter)).fetchall()
        except sqlite3.OperationalError:
            word_rows = []           # bsb_words/bsb_strongs not loaded yet
        verse_rows = []
        if not word_rows:
            verse_rows = conn.execute(
                "SELECT verse_num, verse_text FROM bsb_verses "
                "WHERE book_id = ? AND chapter = ? ORDER BY verse_num",
                (book_id, chapter),
            ).fetchall()
    except sqlite3.OperationalError:
        return jsonify([])           # bsb_verses not loaded yet either
    finally:
        conn.close()
    headings = {r["verse"]: r["heading"] for r in pericope_rows}
    if not word_rows:
        return jsonify([
            {
                "verse": r["verse_num"],
                "verse_text": r["verse_text"],
                "heading": headings.get(r["verse_num"]),
                "words": [],
            }
            for r in verse_rows
        ])
    verses: dict[int, dict] = {}
    order: list[int] = []
    for r in word_rows:
        vn = r["verse_num"]
        if vn not in verses:
            verses[vn] = {"verse": vn, "words": [], "verse_text": r["verse_text"], "heading": headings.get(vn)}
            order.append(vn)
        sids = [s.strip() for s in (r["strongs_ids"] or "").split(",") if s.strip()]
        verses[vn]["words"].append({
            "word_id":   r["word_id"],
            "verse_pos": r["verse_pos"],
            "word":      r["word"],
            "italic":    bool(r["italic"]),
            "punc":      r["punc"] or "",
            "strongs_ids": sids,
            "lemma":     r["lemma"] or "",
            "xlit":      r["xlit"] or "",
        })
    return jsonify([verses[v] for v in order])


@bp.route("/api/bsb/verse/<book>/<int:chapter>/<int:verse_num>")
def bsb_verse_text(book, chapter, verse_num):
    book_id = _KJV_BOOK_ID.get(book)
    if book_id is None:
        return jsonify({"error": "not found"}), 404
    conn = db_ro()
    try:
        row = conn.execute(
            "SELECT verse_text FROM bsb_verses WHERE book_id = ? AND chapter = ? AND verse_num = ?",
            (book_id, chapter, verse_num),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"text": row["verse_text"]})


@bp.route("/api/bsb/verse_words/<book>/<int:chapter>/<int:verse_num>")
def bsb_verse_words(book, chapter, verse_num):
    book_id = _KJV_BOOK_ID.get(book)
    if book_id is None:
        return jsonify([])
    conn = db_ro()
    try:
        rows = conn.execute("""
            SELECT bw.word_id, bw.verse_pos, bw.word, bw.italic, bw.punc,
                   GROUP_CONCAT(bs.strongs_id) AS strongs_ids,
                   MAX(COALESCE(bdb.lemma, lex.lemma))   AS lemma,
                   MAX(COALESCE(bdb.xlit, lex.translit)) AS xlit
            FROM bsb_words bw
            LEFT JOIN bsb_strongs bs ON bs.word_id = bw.word_id
            LEFT JOIN bdb ON bdb.strongs_id = bs.strongs_id AND bs.strongs_id LIKE 'H%'
            LEFT JOIN lexicon lex ON lex.strongs_g = bs.strongs_id
            WHERE bw.book_id = ? AND bw.chapter = ? AND bw.verse_num = ?
            GROUP BY bw.word_id, bw.verse_pos, bw.word, bw.italic, bw.punc
            ORDER BY bw.verse_pos
        """, (book_id, chapter, verse_num)).fetchall()
    except sqlite3.OperationalError:
        return jsonify([])
    finally:
        conn.close()
    words = []
    for r in rows:
        sids = [s.strip() for s in (r["strongs_ids"] or "").split(",") if s.strip()]
        words.append({
            "word_id":    r["word_id"],
            "word":       r["word"],
            "italic":     bool(r["italic"]),
            "punc":       r["punc"] or "",
            "strongs_ids": sids,
            "lemma":      r["lemma"] or "",
            "xlit":       r["xlit"] or "",
        })
    return jsonify(words)


@bp.route("/api/bsb/strongs-count/<strongs_id>")
def bsb_strongs_count(strongs_id):
    conn = db_ro()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM bsb_strongs WHERE strongs_id = ?",
            (strongs_id.upper(),),
        ).fetchone()
    except sqlite3.OperationalError:
        return jsonify({"count": 0})
    finally:
        conn.close()
    return jsonify({"count": row["cnt"] if row else 0})

@bp.route("/api/bsb/audio/<book>/<int:chapter>")
def bsb_audio(book, chapter):
    """Public-domain BSB chapter narration URL (openbible.com). Returns {url}; no
    key, no gate — BSB is public. {url: None} if the book isn't recognized."""
    book_id = _KJV_BOOK_ID.get(book)
    usfm = _USFM_BOOK.get(book)
    if book_id is None or not usfm:
        return jsonify({"url": None})
    fname = f"BSB_{book_id:02d}_{usfm_titlecase(usfm)}_{chapter:03d}.mp3"
    return jsonify({"url": f"{_BSB_AUDIO_BASE}/{fname}"})


# NOTE: plain-text BSB search lives in views_search.py's generic /api/text-search
# (corpus=bsb), which also covers KJV and ABP. No BSB-specific search route here.
