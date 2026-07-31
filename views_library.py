#!/usr/bin/env python3
"""Library (ABP interlinear) reading routes.

The ABP primary text: per-verse plain text, per-verse word list (interlinear
stack), the book list with chapter counts, and the full chapter render (with
pericope headings + proper-noun typing). Word dicts are built via the shared
core._serialize_word_core so chapter_text / verse_words can't drift.
"""
import re

from flask import Blueprint, jsonify

import core as _core
from core import (db, _serialize_word_core, _FUNCTION_STRONGS, word_gloss_cols,
                  step_lemma_cols, pn_xref_parts)
from entity_resolution import norm_name as er_norm_name, book_num as er_book_num

bp = Blueprint("library", __name__)


def _greek_flip_parts(conn):
    """R-2 stage 3 flip #2 (docs/PLAN_r2_stage3.md): with READER_GREEK_FLIPS on
    AND the stage-1 identity table present, each ABP word row carries its served
    Greek identity so the reader's Strong's tags can key Greek for backfilled
    proper nouns. Switch off (or table missing) -> empty strings and the feed
    payload is byte-identical to today (the G1 OFF-proof gate)."""
    if not _core.READER_GREEK_FLIPS:
        return "", ""
    has_gid = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pn_greek_identity'"
    ).fetchone() is not None
    if not has_gid:
        return "", ""
    return (", g.greek_strongs AS g_strongs, g.source AS g_src",
            "LEFT JOIN pn_greek_identity g ON g.verse_id = w.verse_id AND g.position = w.position")


def _gid_field(r, enabled):
    """The per-word identity field, present ONLY when a real identity was served
    (source != 'none'); 'strongs' is the Greek number or empty for a lemma-only
    word (the tag hides rather than fabricate a number — Q3)."""
    if not enabled:
        return {}
    src = r["g_src"]
    if not src or src == "none":
        return {}
    return {"g_id": {"strongs": r["g_strongs"] or "", "src": src}}


@bp.route("/api/verse/<book>/<int:chapter>/<int:verse>")
def verse_text(book, chapter, verse):
    conn = db()
    try:
        # verses.text is the clean, correctly-ordered English prose (the same column
        # the reader's prose mode + the SEO pages use). Do NOT rebuild from `words`
        # joined by position — that's raw Greek order, so ABP's bracket-reordered
        # English comes out scrambled (the TSK-panel garble, 2026-06-20).
        row = conn.execute(
            "SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
            (book, chapter, verse),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "verse not found"}), 404

    return jsonify({"text": row["text"] or ""})


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
        # Corrected headword for ABP dotted Strong's (scripts/build_dotted_lexicon.py);
        # join only if that side table exists, else fall back to the base lexicon lemma.
        has_dotted = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'"
        ).fetchone() is not None
        lem_expr = "COALESCE(dl.lemma, l.lemma)"       if has_dotted else "l.lemma"
        tr_expr  = "COALESCE(dl.translit, l.translit)" if has_dotted else "l.translit"
        dl_join = ("LEFT JOIN dotted_lexicon dl ON dl.strongs = 'G' || w.strongs"
                   if has_dotted else "")
        # Plain-meaning lemma gloss (scripts/build_word_gloss.py); replaces the KJV-ized
        # l.kjv_def. Falls back to l.kjv_def until that table is built (deploy-safe).
        gloss_sel, wg_join = word_gloss_cols(conn, dotted_alias=("dl" if has_dotted else None))
        # Candidate-3 dormant repoints (core.py block comment): STEP lemma fallback
        # for post-retirement G9xxx bases + the tipnr type-badge join through the
        # cross-ref home. Pre-rebuild both return today's SQL untouched.
        lem_expr, tr_expr, gloss_sel, sl_join = step_lemma_cols(conn, lem_expr, tr_expr, gloss_sel)
        lem_sel = f"{lem_expr} AS lemma"
        tr_sel  = f"{tr_expr} AS translit"
        xr_join, t_key = pn_xref_parts(conn)
        gid_sel, gid_join = _greek_flip_parts(conn)
        wrows = conn.execute(
            f"""SELECT w.position, w.english, w.english_head, w.greek_pos, w.bracket_id, w.italic,
                      COALESCE(w.italic_words, '') AS italic_words,
                      w.strongs_base, w.strongs, w.is_pn, w.morph,
                      {lem_sel}, {tr_sel}, {gloss_sel} AS kjv_def, l.strongs_def, l.derivation,
                      t.entity_type AS pn_type, t.entity_types AS pn_types{gid_sel}
               FROM words w
               LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
               {dl_join} {wg_join} {sl_join} {xr_join}
               LEFT JOIN tipnr t ON t.strongs = {t_key}
               {gid_join}
               WHERE w.verse_id = ?
               ORDER BY w.position""",
            (row["id"],),
        ).fetchall()
        # Chip-merge signal (JP-approved 2026-07-31): two ADJACENT proper-noun words
        # whose recorded binds resolve to the SAME entity (Ezion+Geber, Ramoth+Gilead)
        # render as ONE chip. Display-only marker derived from pn_binding — the source
        # of truth — at read time; binds don't move, the partner slot's data is
        # untouched (Mary-class rule). Trigger is exact: both names bound, same
        # entity key, positions consecutive. Absent table -> no markers (deploy-safe).
        merge_pos = set()
        if any(w["is_pn"] for w in wrows) and conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pn_binding'"
        ).fetchone():
            # pn_binding keys book by NUMBER (the 2026-07-31 inert-feature bug:
            # the abbrev matched nothing, so the flag never fired anywhere).
            bmap = {r["name"]: r["entity_uniq"] for r in conn.execute(
                "SELECT name, entity_uniq FROM pn_binding "
                "WHERE book=? AND chapter=? AND verse=? AND render=1",
                (er_book_num(book), chapter, verse))}
            if bmap:
                prev = None
                for w in wrows:
                    ent = None
                    if w["is_pn"]:
                        ent = bmap.get(er_norm_name(w["english_head"] or w["english"] or ""))
                    if ent and prev and prev["ent"] == ent and w["position"] == prev["pos"] + 1:
                        merge_pos.add(w["position"])
                    prev = {"pos": w["position"], "ent": ent} if ent else None
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
                "pn_types":    w["pn_types"],
                "is_content":  w["strongs_base"] not in _FUNCTION_STRONGS,
                **({"pn_merge": True} if w["position"] in merge_pos else {}),
                **_gid_field(w, bool(gid_sel)),
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


# Non-canonical texts (Didache, etc.) each live in their OWN two tables,
# `<book>_words` / `<book>_verses`, created by scripts/didache_proof/load_extra.py.
# They are walled off from the Bible's words/verses and from search + lexicon counts.
_EXTRA_BOOK_RE = re.compile(r"^[a-z0-9_]+$")   # table-name safe; blocks anything odd


@bp.route("/api/extra/<book>/chapter/<int:chapter>")
def extra_chapter(book, chapter):
    """Serve one chapter of a non-canonical text in the shape the Library reader
    consumes, plus a readable-English line per verse. Degrades quietly (empty
    list) if the text's tables haven't been loaded on PA yet."""
    if not _EXTRA_BOOK_RE.match(book):
        return jsonify([])
    wtable, vtable = f"{book}_words", f"{book}_verses"
    conn = db()
    try:
        have = {r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?)",
            (wtable, vtable)
        ).fetchall()}
        if wtable not in have:
            return jsonify([])
        # join the lexicon for the transliteration (same key the Bible uses:
        # lexicon.strongs_g = 'G####'); the Didache words carry that G-number.
        wrows = conn.execute(
            f"""SELECT w.verse, w.position, w.greek, w.lemma, w.strongs, w.gloss, l.translit
                FROM {wtable} w
                LEFT JOIN lexicon l ON l.strongs_g = w.strongs
                WHERE w.chapter=? ORDER BY w.verse, w.position""", (chapter,)
        ).fetchall()
        # `heading` was added later — only select it if the table has it, so an
        # older (pre-headings) load still serves cleanly until the next reload.
        has_heading = vtable in have and any(
            c["name"] == "heading" for c in conn.execute(f"PRAGMA table_info({vtable})")
        )
        vsel = "verse, english, heading" if has_heading else "verse, english"
        vrows = conn.execute(
            f"SELECT {vsel} FROM {vtable} WHERE chapter=? ORDER BY verse",
            (chapter,)
        ).fetchall() if vtable in have else []
    finally:
        conn.close()
    english = {r["verse"]: r["english"] for r in vrows}
    headings = {r["verse"]: r["heading"] for r in vrows} if has_heading else {}
    verses: dict[int, list] = {}
    for r in wrows:
        sg = r["strongs"] or ""                          # "G1322" or ""
        verses.setdefault(r["verse"], []).append({
            "position":     r["position"],
            "english":      r["gloss"],                  # per-word gloss (interlinear)
            "english_head": None,
            "lemma":        r["lemma"],                  # Greek dictionary form
            "translit":     r["translit"],               # romanized form (from lexicon)
            "greek":        r["greek"],                  # inflected form as printed
            "strongs_base": sg or None,                 # G-number → drives word-study click
            "strongs":      sg[1:] if sg else None,      # bare, frontend renders G{strongs}
            "greek_pos":    None,
            "bracket_id":   None,
            "italic":       0,
            "is_pn":        0,
            "morph":        None,
        })
    # Verse list = every verse that has Greek words OR readable English, so an
    # English-only text (no words loaded, e.g. 1 Enoch) still serves prose + headings.
    all_vns = sorted(set(verses) | set(english))
    return jsonify([
        {"verse": v, "heading": headings.get(v), "english": english.get(v, ""), "words": verses.get(v, [])}
        for v in all_vns
    ])


@bp.route("/api/extra/<book>/strongs-count/<strongs>")
def extra_strongs_count(book, strongs):
    """How many times a Strong's number appears within one non-canonical text
    (e.g. the Didache). `strongs` is the G-prefixed form, matching the stored value."""
    if not _EXTRA_BOOK_RE.match(book):
        return jsonify({"count": 0})
    wtable = f"{book}_words"
    conn = db()
    try:
        if not conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (wtable,)
        ).fetchone():
            return jsonify({"count": 0})
        n = conn.execute(
            f"SELECT count(*) FROM {wtable} WHERE strongs=?", (strongs,)
        ).fetchone()[0]
    finally:
        conn.close()
    return jsonify({"count": n})


@bp.route("/api/chapter/<book>/<int:chapter>")
def chapter_text(book, chapter):
    conn = db()
    try:
        # The printed-form ("in this verse") side table is built separately by
        # scripts/build_abp_surface.py on PA. Join it only if it exists, so a code
        # deploy BEFORE that build still serves (words just carry no inflected form).
        has_surface = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_surface'"
        ).fetchone() is not None
        surf_sel  = ", s.form AS surface_form, s.translit AS surface_translit" if has_surface else ""
        surf_join = ("LEFT JOIN abp_surface s ON s.verse_id = w.verse_id AND s.position = w.position"
                     if has_surface else "")
        # Corrected headword for the ABP dotted Strong's that are a different word from
        # their base (scripts/build_dotted_lexicon.py). Join only if that side table is
        # built; otherwise fall back to the base lexicon lemma (so a pre-build deploy is fine).
        has_dotted = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'"
        ).fetchone() is not None
        lem_expr = "COALESCE(dl.lemma, l.lemma)"       if has_dotted else "l.lemma"
        tr_expr  = "COALESCE(dl.translit, l.translit)" if has_dotted else "l.translit"
        dl_join = ("LEFT JOIN dotted_lexicon dl ON dl.strongs = 'G' || w.strongs"
                   if has_dotted else "")
        # Plain-meaning lemma gloss over l.kjv_def (deploy-safe; see verse_words).
        gloss_sel, wg_join = word_gloss_cols(conn, dotted_alias=("dl" if has_dotted else None))
        # Candidate-3 dormant repoints — see verse_words / core.py block comment.
        lem_expr, tr_expr, gloss_sel, sl_join = step_lemma_cols(conn, lem_expr, tr_expr, gloss_sel)
        lem_sel = f"{lem_expr} AS lemma"
        tr_sel  = f"{tr_expr} AS translit"
        xr_join, t_key = pn_xref_parts(conn)
        gid_sel, gid_join = _greek_flip_parts(conn)
        rows = conn.execute(
            f"""SELECT v.verse, v.text AS prose, w.position, w.english, w.english_head, w.strongs_base, w.strongs,
                      {lem_sel}, {tr_sel}, {gloss_sel} AS kjv_def, w.greek_pos, w.bracket_id, w.italic, w.is_pn, w.morph,
                      COALESCE(w.italic_words, '') AS italic_words,
                      COALESCE(w.smcap_words,  '') AS smcap_words,
                      t.entity_type AS pn_type, t.entity_types AS pn_types,
                      p.heading{surf_sel}{gid_sel}
               FROM verses v
               JOIN words w ON w.verse_id = v.id
               LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
               {dl_join} {wg_join} {sl_join} {xr_join}
               LEFT JOIN tipnr t ON t.strongs = {t_key}
               LEFT JOIN pericopes p ON p.book = v.book AND p.chapter = v.chapter AND p.verse = v.verse
               {surf_join}
               {gid_join}
               WHERE v.book = ? AND v.chapter = ?
               ORDER BY v.verse, w.position""",
            (book, chapter),
        ).fetchall()
        # Chip-merge signal (JP-approved 2026-07-31) — same marker as verse_words:
        # adjacent same-entity PN pair -> the SECOND word carries pn_merge and the
        # reader folds it into the first chip. Derived from pn_binding at read time;
        # display-only, binds untouched. Absent table -> no markers (deploy-safe).
        brows = conn.execute(
            "SELECT verse, name, entity_uniq FROM pn_binding "
            "WHERE book=? AND chapter=? AND render=1", (er_book_num(book), chapter),
        ).fetchall() if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pn_binding'"
        ).fetchone() else []
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
            "pn_types":     r["pn_types"],
            # Printed ("in this verse") Greek form + its romanization, when the side
            # table is built + this word anchored. Blank otherwise → no extra line.
            "inflected":          (r["surface_form"]     if has_surface else "") or "",
            "inflected_translit": (r["surface_translit"] if has_surface else "") or "",
            **_gid_field(r, bool(gid_sel)),
        })
    if brows:
        bmap: dict[int, dict] = {}
        for b in brows:
            bmap.setdefault(b["verse"], {})[b["name"]] = b["entity_uniq"]
        for vn, vd in verses.items():
            vb = bmap.get(vn)
            if not vb:
                continue
            prev = None
            for w in vd["words"]:
                ent = vb.get(er_norm_name(w["english_head"] or w["english"] or "")) if w.get("is_pn") else None
                if ent and prev and prev["ent"] == ent and w["position"] == prev["pos"] + 1:
                    w["pn_merge"] = True
                prev = {"pos": w["position"], "ent": ent} if ent else None
    return jsonify([
        {
            "verse": v,
            "heading": verses[v]["heading"],
            "prose": verses[v]["prose"],
            "words": verses[v]["words"],
        }
        for v in order
    ])
