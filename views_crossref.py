#!/usr/bin/env python3
"""Cross-reference (TSK) routes.

Torrey's Treasury of Scripture Knowledge cross-references for a verse, plus the
AI endpoint that curates them (Haiku picks the 8–10 strongest) and writes a short
synthesis (Sonnet, anchored in ABP vocabulary). Cross-ref payloads are cached in
core._ai_cache (in-memory) and in the ai_search_cache table with ver_key=_XREF_VER —
the unified prompt fingerprint (core.ai_fingerprint over the two xref system prompts).
Editing either prompt auto-refreshes this cache and nothing else.
"""
import json
import re

from flask import Blueprint, jsonify

from core import (
    db_ro, _anthropic, limiter, log, _ai_cache,
    _KJV_BOOK_ID, _KJV_BOOK_ID_REV,
    ai_fingerprint, ai_cache_get, ai_cache_put, ai_cache_prune,
)

bp = Blueprint("crossref", __name__)


_XREF_SYNTHESIS_SYSTEM = """\
You are a textual scholar with a Berean approach: the text speaks first. Working only \
from the passages in front of you, show what they reveal when read together. The reader is \
already looking at the verse they clicked, so do not restate or retell it — open at the \
connection itself and let the cross-referenced passages carry the substance. Write from \
inside the text — in terms of what the verses actually say and the people, places, and \
events in them — naming a specific passage when it carries the point, rather than \
describing the set from the outside. Bring in no systematic theology and no outside \
doctrinal framework — follow where the words lead.

Write for a reader who knows no Greek or Hebrew. Keep it plain and concrete, never \
academic. One idea per sentence, short sentences, and never pack several parallels into a \
run-on. Let the length follow the connection: a simple link needs a sentence or two, a \
rich one a few more — up to about 100 words. Do not pad, and do not cram.

Be selective — name the strongest link or two, not every parallel. Describe the \
connection the passages themselves make. Do not settle contested questions, moralize, or \
add application. Where a reading is genuinely debated, lay out what each passage says and \
stop there — let the openness show by where you end, not by a closing line that announces \
the matter is unsettled. Report the plain sense, including anything supernatural, as the \
text gives it — never rationalize it or soften it into a natural explanation.

If you cite a Greek or Hebrew word, give a readable transliteration and a short English \
gloss once — for example, tov, "good" — never the original script, and never the same \
gloss twice. Do not name any app, database, source, or translation. Open straight into \
the first sentence — no heading, no label, no throat-clearing about the passages \
themselves — and vary how you begin.

Here is one example of the right voice (the reader has clicked the wilderness manna verse,
so it is not retold — the writing opens straight at the connection):
The same bread keeps surfacing long after the wilderness: a jar of it set before the \
covenant as a keepsake, and a warning that the fathers ate it and still died. Each return \
turns on provision no one earned, and how quickly it was forgotten. A psalm calls it grain \
of heaven, yet the people it fed kept rebelling. The jar stays by the covenant as a sign of \
both — the gift, and the forgetting.\
"""

_XREF_CURATION_SYSTEM = """\
You are a biblical scholar evaluating cross-references from Torrey's Treasury of \
Scripture Knowledge. Given a source verse and a numbered list of candidate passages, \
select the 8 to 10 with the strongest connection to the source — prioritizing direct \
quotations, shared key terms in the Greek or Hebrew, thematic parallels, and \
canonical echoes. Exclude weak matches that share only common vocabulary with no \
deeper connection. Return ONLY a JSON array of the selected 1-based numbers, \
e.g. [1,3,7,12]. No prose, no explanation — only the array.\
"""

# One fingerprint for both xref endpoints (they share a category). Editing either
# system prompt above changes it, so cached synthesis/curation lazily refreshes. The
# trailing salt is a manual bump for non-prompt changes to the synthesis MESSAGE —
# e.g. feeding the cross-refs in ABP instead of KJV — so those cached rows refresh too.
_XREF_VER = ai_fingerprint(
    "xref", _XREF_CURATION_SYSTEM, _XREF_SYNTHESIS_SYSTEM, "msg:abp-refs-2"
)


def _abp_text(conn, abbr, chapter, verse):
    """ABP English prose for one verse (verses.text — the clean, correctly-ordered
    line the reader's prose mode shows). None when ABP has no matching verse
    (versification can differ from the KJV reference) so the caller can fall back to
    KJV. Do NOT rebuild from `words` by position — that's raw Greek order and scrambles
    ABP's bracket-reordered English (2026-06-20)."""
    row = conn.execute(
        "SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
        (abbr, chapter, verse),
    ).fetchone()
    if not row:
        return None
    txt = (row["text"] or "").strip()
    return txt or None


def prune_cache() -> int:
    """Startup: drop xref rows tagged with an older prompt fingerprint."""
    return ai_cache_prune("xref", _XREF_VER)


@bp.route("/api/cross-references/<book>/<int:chapter>/<int:verse>")
def cross_references_route(book, chapter, verse):
    book_id = _KJV_BOOK_ID.get(book)
    if book_id is None:
        return jsonify([])
    conn = db_ro()
    try:
        row = conn.execute(
            "SELECT verse_id FROM kjv_verses WHERE book_id=? AND chapter=? AND verse_num=?",
            (book_id, chapter, verse),
        ).fetchone()
        if not row:
            return jsonify([])
        refs = conn.execute(
            """SELECT kv.book_id, kv.chapter, kv.verse_num, kv.verse_text
               FROM cross_references cr
               JOIN kjv_verses kv ON kv.verse_id = cr.verse_ref_id
               WHERE cr.verse_id = ?
               ORDER BY kv.verse_id""",
            (row["verse_id"],),
        ).fetchall()
    finally:
        conn.close()
    result = []
    for r in refs:
        abbrev = _KJV_BOOK_ID_REV.get(r["book_id"])
        if abbrev:
            result.append({
                "book":     abbrev,
                "chapter":  r["chapter"],
                "verse":    r["verse_num"],
                "ref":      f"{abbrev} {r['chapter']}:{r['verse_num']}",
                "kjv_text": r["verse_text"],
            })
    return jsonify(result)


@bp.route("/api/cross-references/curated/<book>/<int:chapter>/<int:verse>")
@limiter.limit("200 per hour")
def cross_refs_curated(book, chapter, verse):
    if not _anthropic:
        return jsonify({"refs": [], "synthesis": None})
    book_id = _KJV_BOOK_ID.get(book)
    if book_id is None:
        return jsonify({"refs": [], "synthesis": None})

    cache_key = f"xref_cur:{book}:{chapter}:{verse}"
    if cache_key in _ai_cache:
        return jsonify(_ai_cache[cache_key])
    cached = ai_cache_get(cache_key, _XREF_VER)
    if cached is not None:
        _ai_cache[cache_key] = cached
        return jsonify(cached)

    conn = db_ro()
    try:
        src = conn.execute(
            "SELECT verse_id, verse_text FROM kjv_verses"
            " WHERE book_id=? AND chapter=? AND verse_num=?",
            (book_id, chapter, verse),
        ).fetchone()
        if not src:
            return jsonify({"refs": [], "synthesis": None})

        all_refs = conn.execute(
            """SELECT kv.verse_id, kv.book_id, kv.chapter, kv.verse_num, kv.verse_text
               FROM cross_references cr
               JOIN kjv_verses kv ON kv.verse_id = cr.verse_ref_id
               WHERE cr.verse_id = ?
               ORDER BY kv.verse_id""",
            (src["verse_id"],),
        ).fetchall()

        # ABP text for the source verse so the synthesis reflects ABP vocabulary.
        abp_text = _abp_text(conn, book, chapter, verse) or ""
    finally:
        conn.close()

    if not all_refs:
        return jsonify({"refs": [], "synthesis": None})

    # Step 1: Haiku selects the 8–10 most relevant cross-refs
    numbered = "\n".join(f"{i+1}. {r['verse_text']}" for i, r in enumerate(all_refs))
    selected_refs = []
    try:
        sel_msg = _anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            temperature=0,
            system=_XREF_CURATION_SYSTEM,
            messages=[{"role": "user", "content": (
                f'Source: "{src["verse_text"]}"\n\nCandidates:\n{numbered}\n\n'
                "Return ONLY a JSON array of selected 1-based numbers."
            )}],
        )
        raw = sel_msg.content[0].text.strip()
        m = re.search(r'\[[\d,\s]+\]', raw)
        if m:
            indices = json.loads(m.group())
            selected_refs = [
                all_refs[i - 1] for i in indices
                if isinstance(i, int) and 1 <= i <= len(all_refs)
            ][:10]
    except Exception as exc:
        log.warning("Cross-ref curation failed: %s", exc)

    if not selected_refs:
        selected_refs = list(all_refs[:8])

    refs = []
    for r in selected_refs:
        abbrev = _KJV_BOOK_ID_REV.get(r["book_id"])
        if abbrev:
            refs.append({
                "book":    abbrev,
                "chapter": r["chapter"],
                "verse":   r["verse_num"],
                "ref":     f"{abbrev} {r['chapter']}:{r['verse_num']}",
                "kjv_text": r["verse_text"],
            })

    # Step 2: Synthesis from the curated set. Feed the cross-refs in ABP (the app's
    # primary text) so the write-up quotes the same wording the panel shows — the TSK
    # list is stored against KJV, which is why it used to come out in "thou/thee".
    # KJV is only a fallback for a verse ABP's versification doesn't carry.
    synthesis = None
    if refs:
        conn = db_ro()
        try:
            ref_block = "\n".join(
                f"- {_abp_text(conn, r['book'], r['chapter'], r['verse']) or r['kjv_text']}"
                for r in refs
            )
        finally:
            conn.close()
        src_line = (
            f'Source (ABP): "{abp_text}"' if abp_text
            else f'Source: "{src["verse_text"]}"'
        )
        try:
            syn_msg = _anthropic.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                temperature=0,
                system=_XREF_SYNTHESIS_SYSTEM,
                messages=[{"role": "user", "content":
                    f'{src_line}\n\nCross-references:\n{ref_block}'}],
            )
            synthesis = re.sub(
                r"^#+\s*[^:\n]*:\s*", "", syn_msg.content[0].text.strip()
            )
        except Exception as exc:
            log.warning("Cross-ref synthesis failed: %s", exc)

    payload = {"refs": refs, "synthesis": synthesis}
    ai_cache_put(cache_key, payload, _XREF_VER)
    _ai_cache[cache_key] = payload
    return jsonify(payload)
