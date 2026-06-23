#!/usr/bin/env python3
"""LSJ / BDB lexicon-entry routes.

Liddell-Scott-Jones Greek entries (with abp_ext + Strong's fallbacks), the
Haiku-backed LSJ sense summary, and Brown-Driver-Briggs Hebrew entries.

_lsj_concept_lookup and _format_lsj_context are used by the AI blueprint (its
LSJ-context step), so they live here with the other LSJ helpers and the AI module
imports them.
"""
import json
import re

from flask import Blueprint, jsonify, request

from core import db, db_ro, _anthropic, limiter, log, _strip_accents, ai_fingerprint
from views_lexicon import _greek_cognates

bp = Blueprint("lsj", __name__)


# The prompt is SOURCE-BOUND, not a blacklist (the standing "reframe, don't blacklist"
# rule — see project_synthesis_no_parse + project_ai_synthesis_quality). Haiku was
# pulling NT theology from its own training even when the entry didn't carry it — G1577
# ἐκκλησία came back "the Church as a body of Christians or the building where they meet"
# though the LSJ entry says no such thing (2026-06-23). Two levers fix it:
#   - source-binding: summarize ONLY what THIS entry states; anything not in the entry is
#     left out. That alone drops the invented "church/building" sense.
#   - plain meaning over loaded label: keep the attested sense, never recast a plain
#     definition as a doctrinal/institutional term (feedback_plain_meaning_not_tradition).
# Runs on Sonnet now (claude-sonnet-4-6), same as xref/chapter-summary/ask-corpus — Haiku
# over-asserts on loaded words. We do NOT name classical authors (naming them primed the
# leak) and the reader already SEES the headword + gloss, so no need to re-announce it.
_LSJ_SYNTHESIS_SYSTEM = """\
You are helping someone reading the Greek Bible understand a Greek word by summarizing \
the dictionary entry shown below. Work ONLY from that entry: in plain modern English, \
give the meaning and the range of senses the entry itself states. Do not add meanings, \
nuances, or usage from your own knowledge of the word — if the entry does not say it, \
leave it out. Keep to the plain, attested sense; do not recast a plain definition as a \
theological, doctrinal, or institutional term the entry never uses. Work from a Berean \
approach: the text speaks first; follow where the entry leads, with no imported \
systematic theology and no denominational assumptions. Write in plain prose — no \
markdown, no headers, no bullet points. Do not state the word's grammatical parsing \
(part of speech, case, number, tense, voice, mood); that is shown separately. Focus \
only on meaning and semantic range.\
"""

# The two user-message asks, kept as named constants so the synthesis fingerprint below
# covers their wording (editing either auto-refreshes the cached summaries).
_LSJ_ASK_CTX = (
    "From this entry, identify the sense of the word active in the verse above and explain "
    "it in plain prose. 2-3 sentences, 60 words max. Let the entry dictate the length — do "
    "not pad. No markdown, no headers, no bullet points."
)
_LSJ_ASK_GEN = (
    "Summarize what this entry shows the word means and its main range of senses. 2-3 "
    "sentences, 60 words max. Let the entry dictate the length — do not pad. No markdown, "
    "no headers, no bullet points."
)

# Synthesis fingerprint — same self-healing scheme as the ai_search_cache entries. It's
# stamped into each stored summary (summary_json["_synth_ver"]); when the prompt above
# changes, the stamp no longer matches and the old summary is dropped + regenerated on
# next view. No manual cache-clear script needed.
_LSJ_SYNTH_VER = ai_fingerprint("lsj", _LSJ_SYNTHESIS_SYSTEM, _LSJ_ASK_CTX, _LSJ_ASK_GEN)

# keyed on LSJ key; persists for server lifetime. Capped so a long-running worker
# can't grow it without bound — context-keyed entries are many distinct keys.
_lsj_summary_cache: dict = {}
_LSJ_SUMMARY_CACHE_MAX = 500


def _cache_lsj_summary(key: str, payload: dict) -> dict:
    """Store a summary payload, bounding the in-memory cache size. Returns payload."""
    if len(_lsj_summary_cache) < _LSJ_SUMMARY_CACHE_MAX:
        _lsj_summary_cache[key] = payload
    return payload

_LSJ_TERM_LIMIT = 4  # max LSJ entries per extracted search term


def _lsj_concept_lookup(terms: list[str]) -> list[dict]:
    """Search LSJ + lexicon for English terms; return matched Strong's + semantic snippets."""
    if not terms:
        return []
    conn = db()
    seen: set[str] = set()
    results: list[dict] = []
    try:
        for term in terms[:5]:
            pattern = f"%{term.lower()}%"
            rows = conn.execute(
                """SELECT l.strongs, l.lemma, l.translit, l.derivation, lsj.summary_json, lsj.def_html
                   FROM lexicon l
                   JOIN lsj ON lsj.plain = lower(strip_accents(l.lemma))
                   WHERE lower(lsj.def_html) LIKE ?
                   ORDER BY length(lsj.def_html)
                   LIMIT ?""",
                (pattern, _LSJ_TERM_LIMIT),
            ).fetchall()
            for row in rows:
                if row["strongs"] in seen:
                    continue
                seen.add(row["strongs"])
                semantic = ""
                if row["summary_json"]:
                    try:
                        sj = json.loads(row["summary_json"])
                        semantic = " ".join(
                            s["text"] for s in sj.get("sections", [])
                        )[:300]
                    except Exception:
                        pass
                if not semantic:
                    semantic = re.sub(r"<[^>]+>", " ", row["def_html"] or "")[:300].strip()
                # Fetch dotted variants present in the corpus for this base
                variants = [
                    v["strongs"] for v in conn.execute(
                        "SELECT DISTINCT strongs FROM words WHERE strongs LIKE ? AND strongs != ?",
                        (f"{row['strongs']}.%", row["strongs"]),
                    ).fetchall()
                ]
                # Same-root family from the lexicon's own etymology, so the AI can SEE
                # related forms it would otherwise never search — e.g. σαββατισμός
                # (G4520) hanging off σάββατον (G4521). Greek-only (the etymology data
                # lives in the Greek derivation text); a hiccup must never sink the lookup.
                cognates = []
                try:
                    for c in _greek_cognates(conn, row["strongs"], row["derivation"]):
                        cbase = c["strongs"].lstrip("Gg")
                        if cbase in seen:
                            continue
                        seen.add(cbase)
                        cognates.append(c)
                except Exception as e:
                    log.warning("cognate expansion failed for G%s: %s", row["strongs"], e)
                results.append({
                    "strongs":         row["strongs"],
                    "lemma":           row["lemma"],
                    "translit":        row["translit"],
                    "semantic":        semantic,
                    "dotted_variants": variants,
                    "cognates":        cognates,
                })
    except Exception as e:
        log.warning("LSJ concept lookup failed: %s", e)
    finally:
        conn.close()
    return results


_LSJ_XREF_RE = re.compile(r'\bv\.\s*<i>([^<]+)</i>')

def _is_lsj_stub(def_html: str) -> bool:
    text = re.sub(r'<[^>]+>', '', def_html or '').strip()
    return len(text) <= 150 and bool(_LSJ_XREF_RE.search(def_html or ''))

def _resolve_lsj_xref(conn, def_html: str, columns: str = "key, translit, def_html"):
    """If def_html is a bare cross-reference stub (v. <i>word</i>), fetch the referenced entry."""
    if not def_html:
        return None
    if len(re.sub(r'<[^>]+>', '', def_html).strip()) > 150:
        return None
    m = _LSJ_XREF_RE.search(def_html)
    if not m:
        return None
    # Don't follow if xref points to multiple sub-entries like "(A) and (B)" — ambiguous sense
    after = def_html[m.end():].lstrip()
    if after.startswith('('):
        return None
    ref = m.group(1).strip()
    ref_plain = _strip_accents(ref).lower().replace('-', '')
    row = conn.execute(f"SELECT {columns} FROM lsj WHERE key = ?", (ref,)).fetchone()
    if not row:
        row = conn.execute(
            f"SELECT {columns} FROM lsj WHERE replace(plain,'-','') = ?",
            (ref_plain,),
        ).fetchone()
    return row


def _format_lsj_context(entries: list[dict]) -> str:
    if not entries:
        return ""
    lines = ["LSJ LEXICAL CONTEXT — use these Strong's numbers in SQL WHERE clauses:"]
    for e in entries:
        line = f"  G{e['strongs']} {e['lemma']} ({e['translit']}): {e['semantic']}"
        variants = e.get("dotted_variants", [])
        if variants:
            vlist = ", ".join(f"G{v}" for v in sorted(variants))
            line += f" [corpus dotted variants: {vlist} — use w.strongs='...' to target specifically]"
        lines.append(line)
        cognates = e.get("cognates", [])
        if cognates:
            clist = "; ".join(
                f"{c['strongs']} {c['lemma']} ({c['translit']})"
                + (f" — {c['gloss']}" if c.get("gloss") else "")
                for c in cognates
            )
            lines.append(
                f"      related same-root forms (include in SQL + key_strongs when they "
                f"fit the concept): {clist}"
            )
    return "\n".join(lines)


@bp.route("/api/lsj/<path:lemma>")
def lsj_lookup(lemma):
    strongs_param = request.args.get("strongs", "")
    conn = db()
    try:
        if "." in strongs_param:
            snum = strongs_param.lstrip("Gg")
            try:
                abp_row = conn.execute(
                    "SELECT def_html FROM abp_ext WHERE trim(strongs) = ? OR trim(strongs) = ?",
                    (snum, "G" + snum),
                ).fetchone()
            except Exception as e:
                log.warning("abp_ext lookup failed: %s", e)
                abp_row = None
        else:
            snum = strongs_param
            abp_row = None
        plain = _strip_accents(lemma).lower().replace('-', '')
        row = conn.execute(
            "SELECT key, translit, def_html FROM lsj WHERE key = ?", (lemma,)
        ).fetchone()
        if not row and plain:
            row = conn.execute(
                "SELECT key, translit, def_html FROM lsj"
                " WHERE lower(strip_accents(replace(key,'-',''))) = ?"
                "   AND key NOT LIKE '-%'", (plain,)        # don't match suffix headwords (-σε, -θεν…)
            ).fetchone()
        if row and not abp_row:
            xref = _resolve_lsj_xref(conn, row["def_html"])
            if xref:
                row = xref
            elif _is_lsj_stub(row["def_html"]):
                row = None
        lex_row = None
        if not row and not abp_row:
            lex_row = conn.execute(
                "SELECT strongs_def, kjv_def, derivation, translit FROM lexicon WHERE lemma = ?", (lemma,)
            ).fetchone()
            if not lex_row and snum:
                lex_row = conn.execute(
                    "SELECT strongs_def, kjv_def, derivation, translit FROM lexicon WHERE strongs = ?",
                    (snum.lstrip("Gg"),),
                ).fetchone()
    finally:
        conn.close()
    def _trim_br(html):
        import re as _re
        return _re.sub(r'(\s*<br\s*/?>\s*)+$', '', html or '', flags=_re.IGNORECASE)

    if abp_row:
        return jsonify({
            "key":      snum,
            "translit": "",
            "def_html": _trim_br(abp_row["def_html"]),
            "source":   "abp_ext",
        })
    if lex_row:
        # Strong's fallback (no LSJ / abp_ext entry). Lead with the KJV rendering, then
        # the derivation — concrete, text-first data — rather than Strong's own
        # interpretive paraphrase (strongs_def), which can carry imported doctrine:
        # e.g. G5020 ταρταρόω reads "to incarcerate in eternal torment", where the text
        # itself only says "cast down to hell" (from Tartarus). strongs_def is the last
        # resort, used only when there's nothing more concrete.
        strongs_body = (
            (lex_row["kjv_def"] or "").strip()
            or (lex_row["derivation"] or "").strip()
            or (lex_row["strongs_def"] or "").strip()
        )
        if strongs_body:
            return jsonify({
                "key":      lemma,
                "translit": lex_row["translit"] or "",
                "def_html": f"<p>{strongs_body}</p>",
                "source":   "strongs",
            })
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "key":      row["key"],
        "translit": row["translit"],
        "def_html": _trim_br(row["def_html"]),
    })


@bp.route("/api/lsj-summary/<path:lemma>")
@limiter.limit("200 per hour")
def lsj_summary(lemma):
    strongs_param = request.args.get("strongs", "")
    book    = request.args.get("book", "").strip()
    chapter = request.args.get("chapter", "").strip()
    verse_n = request.args.get("verse", "").strip()
    has_ctx = bool(book and chapter and verse_n)

    base_key = f"abp:{strongs_param}" if ("." in strongs_param) else lemma
    mem_key  = (f"ctx:{base_key}:{book}.{chapter}.{verse_n}"
                if has_ctx else f"gen:{base_key}")

    if mem_key in _lsj_summary_cache:
        return jsonify(_lsj_summary_cache[mem_key])
    if not _anthropic:
        return jsonify({"error": "AI unavailable"}), 503

    conn = db()
    exact_key = None
    abp_strongs = None
    row = None
    try:
        if "." in strongs_param:
            snum = strongs_param.lstrip("Gg")
            try:
                abp_row = conn.execute(
                    "SELECT def_html, summary_json FROM abp_ext WHERE trim(strongs) = ? OR trim(strongs) = ?",
                    (snum, "G" + snum),
                ).fetchone()
            except Exception as e:
                log.warning("abp_ext summary lookup failed: %s", e)
                abp_row = None
            if abp_row:
                row = {"def_html": abp_row["def_html"], "summary_json": abp_row["summary_json"]}
                abp_strongs = snum
            else:
                row = None
        else:
            plain = _strip_accents(lemma).lower().replace('-', '')
            row = conn.execute(
                "SELECT key, def_html, summary_json FROM lsj WHERE key = ?", (lemma,)
            ).fetchone()
            if not row and plain:
                row = conn.execute(
                    "SELECT key, def_html, summary_json FROM lsj"
                    " WHERE lower(strip_accents(replace(key,'-',''))) = ?"
                    "   AND key NOT LIKE '-%'", (plain,)     # don't match suffix headwords (-σε, -θεν…)
                ).fetchone()
            if row:
                xref = _resolve_lsj_xref(conn, row["def_html"], "key, def_html, summary_json")
                if xref:
                    row = xref
                elif _is_lsj_stub(row["def_html"]):
                    row = None
            if row:
                exact_key = row["key"]
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404

    # Parse existing summary_json — may contain sections, general, context
    sj: dict = {}
    if row["summary_json"]:
        try:
            sj = json.loads(row["summary_json"])
        except Exception:
            sj = {}

    # Auto-refresh on prompt change: the AI-written parts (general + per-verse context)
    # carry the synthesis fingerprint. If the prompt has changed since they were written,
    # drop them so they regenerate below — same self-healing as the ai_search_cache rows.
    # The parsed `sections` are not AI-written, so they're kept.
    if sj.get("_synth_ver") != _LSJ_SYNTH_VER:
        sj.pop("general", None)
        sj.pop("context", None)

    # Check DB cache for the requested synthesis type
    ctx_db_key = f"{book}.{chapter}.{verse_n}"
    if has_ctx and sj.get("context", {}).get(ctx_db_key):
        payload = {"summary": sj["context"][ctx_db_key], "contextual": True}
        return jsonify(_cache_lsj_summary(mem_key, payload))
    if not has_ctx and sj.get("general"):
        payload = {"summary": sj["general"], "contextual": False}
        return jsonify(_cache_lsj_summary(mem_key, payload))

    # Fetch verse text for contextual summary
    plain_def = re.sub(r"<[^>]+>", " ", row["def_html"] or "").strip()
    actual_ctx = has_ctx
    verse_text = ""
    if has_ctx:
        try:
            vconn = db_ro()
            try:
                vrow = vconn.execute(
                    "SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                    (book, int(chapter), int(verse_n)),
                ).fetchone()
                if vrow:
                    verse_text = vrow["text"]
            finally:
                vconn.close()
        except Exception:
            pass
        if not verse_text:
            actual_ctx = False  # fall back to general if verse not found

    if actual_ctx:
        user_content = (
            f"Verse: {book} {chapter}:{verse_n} — {verse_text}\n\n"
            f"LSJ entry for {lemma}:\n{plain_def[:2000]}\n\n"
            + _LSJ_ASK_CTX
        )
    else:
        user_content = (
            f"LSJ entry for {lemma}:\n{plain_def[:2000]}\n\n"
            + _LSJ_ASK_GEN
        )

    try:
        synth_msg = _anthropic.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            temperature=0,
            system=_LSJ_SYNTHESIS_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
        synthesis = synth_msg.content[0].text.strip()
    except Exception as exc:
        log.warning("LSJ synthesis failed: %s", exc)
        return jsonify({"error": "synthesis failed"}), 500

    # Store synthesis back into summary_json alongside sections, stamped with the current
    # prompt fingerprint so a later prompt change drops + regenerates it (see load above).
    if actual_ctx:
        sj.setdefault("context", {})[ctx_db_key] = synthesis
    else:
        sj["general"] = synthesis
    sj["_synth_ver"] = _LSJ_SYNTH_VER

    conn = db()
    try:
        sj_str = json.dumps(sj, ensure_ascii=False)
        if exact_key:
            conn.execute("UPDATE lsj SET summary_json = ? WHERE key = ?", (sj_str, exact_key))
        elif abp_strongs:
            conn.execute(
                "UPDATE abp_ext SET summary_json = ? WHERE trim(strongs) = ? OR trim(strongs) = ?",
                (sj_str, abp_strongs, "G" + abp_strongs),
            )
        conn.commit()
    finally:
        conn.close()

    payload = {"summary": synthesis, "contextual": actual_ctx}
    return jsonify(_cache_lsj_summary(mem_key, payload))


@bp.route("/api/bdb/<path:strongs_id>")
def bdb_lookup(strongs_id):
    conn = db_ro()
    try:
        row = conn.execute(
            "SELECT strongs_id, lemma, xlit, pronounce, description, part_of_speech FROM bdb WHERE strongs_id = ?",
            (strongs_id.upper(),)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "strongs_id":     row["strongs_id"],
        "lemma":          row["lemma"] or "",
        "xlit":           row["xlit"] or "",
        "pronounce":      row["pronounce"] or "",
        "description":    row["description"] or "",
        "part_of_speech": row["part_of_speech"] or "",
    })
