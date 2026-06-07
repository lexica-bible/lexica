#!/usr/bin/env python3
"""Library (ABP interlinear) reading routes (Phase 3 of REDESIGN_PLAN.md).

The ABP primary text: per-verse plain text, per-verse word list (interlinear
stack), the book list with chapter counts, and the full chapter render (with
pericope headings + proper-noun typing). Word dicts are built via the shared
core._serialize_word_core so chapter_text / verse_words can't drift.
"""
from flask import Blueprint, jsonify

from core import db, _serialize_word_core, _FUNCTION_STRONGS

bp = Blueprint("library", __name__)


@bp.route("/api/verse/<book>/<int:chapter>/<int:verse>")
def verse_text(book, chapter, verse):
    conn = db()
    try:
        row = conn.execute(
            "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
            (book, chapter, verse),
        ).fetchone()

        if not row:
            return jsonify({"error": "verse not found"}), 404

        words = conn.execute(
            "SELECT english FROM words WHERE verse_id=? AND english IS NOT NULL ORDER BY position",
            (row["id"],),
        ).fetchall()
    finally:
        conn.close()

    return jsonify({"text": " ".join(w["english"] for w in words)})


@bp.route("/api/verse-words/<book>/<int:chapter>/<int:verse>")
def verse_words(book, chapter, verse):
    conn = db()
    try:
        row = conn.execute(
            "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
            (book, chapter, verse),
        ).fetchone()
        if not row:
            return jsonify({"error": "verse not found"}), 404
        wrows = conn.execute(
            """SELECT w.position, w.english, w.english_head, w.greek_pos, w.bracket_id, w.italic,
                      COALESCE(w.italic_words, '') AS italic_words,
                      w.strongs_base, w.strongs, w.is_pn, w.morph,
                      l.lemma, l.translit, l.kjv_def, l.strongs_def, l.derivation,
                      t.entity_type AS pn_type
               FROM words w
               LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
               LEFT JOIN tipnr t ON t.strongs = w.strongs_base
               WHERE w.verse_id = ?
               ORDER BY w.position""",
            (row["id"],),
        ).fetchall()
    finally:
        conn.close()
    return jsonify({
        "words": [
            {
                **_serialize_word_core(w),
                "position":    w["position"],
                "italic":      bool(w["italic"]),
                "morph":       w["morph"],
                "strongs_def": (w["strongs_def"] or "").strip(),
                "derivation":  (w["derivation"] or "").strip(),
                "pn_type":     w["pn_type"],
                "is_content":  w["strongs_base"] not in _FUNCTION_STRONGS,
            }
            for w in wrows
        ]
    })


@bp.route("/api/books")
def books_list():
    conn = db()
    try:
        rows = conn.execute("""
            SELECT b.abbrev, b.name, MAX(v.chapter) AS chapters
            FROM books b
            JOIN verses v ON v.book = b.abbrev
            GROUP BY b.abbrev, b.name
            ORDER BY COALESCE(b.sort_order, b.id)
        """).fetchall()
    finally:
        conn.close()
    return jsonify([{"abbrev": r["abbrev"], "name": r["name"], "chapters": r["chapters"]} for r in rows])


@bp.route("/api/chapter/<book>/<int:chapter>")
def chapter_text(book, chapter):
    conn = db()
    try:
        rows = conn.execute(
            """SELECT v.verse, v.text AS prose, w.position, w.english, w.english_head, w.strongs_base, w.strongs,
                      l.lemma, l.translit, l.kjv_def, w.greek_pos, w.bracket_id, w.italic, w.is_pn, w.morph,
                      COALESCE(w.italic_words, '') AS italic_words,
                      COALESCE(w.smcap_words,  '') AS smcap_words,
                      t.entity_type AS pn_type,
                      p.heading
               FROM verses v
               JOIN words w ON w.verse_id = v.id
               LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
               LEFT JOIN tipnr t ON t.strongs = w.strongs_base
               LEFT JOIN pericopes p ON p.book = v.book AND p.chapter = v.chapter AND p.verse = v.verse
               WHERE v.book = ? AND v.chapter = ?
               ORDER BY v.verse, w.position""",
            (book, chapter),
        ).fetchall()
    finally:
        conn.close()
    verses: dict[int, dict] = {}
    order: list[int] = []
    for r in rows:
        vn = r["verse"]
        if vn not in verses:
            verses[vn] = {"words": [], "heading": r["heading"], "prose": r["prose"]}
            order.append(vn)
        verses[vn]["words"].append({
            **_serialize_word_core(r),
            "position":     r["position"],
            "italic":       r["italic"],
            "morph":        r["morph"],
            "smcap_words":  r["smcap_words"],
            "pn_type":      r["pn_type"],
        })
    return jsonify([
        {
            "verse": v,
            "heading": verses[v]["heading"],
            "prose": verses[v]["prose"],
            "words": verses[v]["words"],
        }
        for v in order
    ])
