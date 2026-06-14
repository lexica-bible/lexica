#!/usr/bin/env python3
"""Chronological reading-plan daily intro (title + Berean summary).

Powers the "Reading intro" panel in the Library's Chronological view — the ESV-style
card that orients you to a day's reading: a short title (e.g. "David's Psalms") plus a
few sentences on what the day's passages cover and how they connect.

The day -> passages map comes from static/chronological.json (the same file the browser
loads); the verse text is read from bible.db (ABP `verses.text`, prose). One Haiku call
produces both the title and the summary, cached in ai_search_cache:
  query = "chrono_intro:<day>"   ver_key = unified prompt fingerprint (core.ai_fingerprint)
Editing the prompt below auto-refreshes every cached intro (the fingerprint changes).
Rate-limited like the other paid AI routes.
"""
import json
import os
import re

from flask import Blueprint, jsonify

from core import (
    db_ro, _anthropic, limiter, log, _ai_cache,
    ai_fingerprint, ai_cache_get, ai_cache_put, ai_cache_prune,
)

bp = Blueprint("chrono", __name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_CHRONO_JSON = os.path.join(_HERE, "static", "chronological.json")
_MODEL = "claude-haiku-4-5-20251001"

# day number -> day dict, loaded once. (Small static file; reloaded only on restart,
# which is fine — the plan changes only when chronological.json is rebuilt + deployed.)
_DAYS = {}
_PASSAGES = []
try:
    with open(_CHRONO_JSON, encoding="utf-8") as f:
        _data = json.load(f)
    _PASSAGES = _data.get("passages", [])
    _DAYS = {d["day"]: d for d in _data.get("days", [])}
except Exception as exc:   # pragma: no cover - missing file just disables the feature
    log.warning("chrono intro: could not load %s: %s", _CHRONO_JSON, exc)


_SYSTEM = """\
You are a textual scholar working from a Berean approach: the text speaks first. Let the \
actual words of the passages anchor everything you write. Import no systematic theology, no \
denominational framework, and no doctrinal assumptions from outside the text — follow where \
the words lead. You may name a book's well-established author, audience, or setting as ordinary \
background. You may note plain eschatological or messianic themes when the text itself raises \
them, but never impose them and never invent events the text does not contain. Never mention \
any app, database, data source, or translation by name. Write in plain, direct, readable \
language — not academic jargon. Each sentence is one complete thought.\
"""

_PROMPT_TMPL = (
    "This is one day's reading in a chronological journey through the Bible (Reading {day}). "
    "Today's passages, in order:\n{labels}\n\n"
    "Sample of the text:\n{text}\n\n"
    "Write two things:\n"
    "1) A SHORT title for the day — 2 to 5 words capturing its theme, like \"David's Psalms\", "
    "\"The Flood\", or \"Solomon's Proverbs\". No punctuation at the end.\n"
    "2) A single short paragraph (about 60 to 90 words) orienting the reader to what these "
    "passages cover and how they connect, anchored in the text. Do not list the references again "
    "and do not retell verse by verse.\n\n"
    "Format EXACTLY: the title on the first line, then a blank line, then the paragraph. "
    "Do not add any labels, headings, or quotation marks."
)

_VER = ai_fingerprint("chrono", _SYSTEM, _PROMPT_TMPL, _MODEL)


def prune_cache() -> int:
    """Startup: drop intro rows from an OLD prompt version (the fingerprint is the keeper)."""
    return ai_cache_prune("chrono", _VER)


def _passage_text(conn, p, cap=900):
    """Prose text for one passage's verse window (ABP verses.text), capped."""
    rows = conn.execute(
        """SELECT chapter, verse, text FROM verses
           WHERE book = ?
             AND (chapter > ? OR (chapter = ? AND verse >= ?))
             AND (chapter < ? OR (chapter = ? AND verse <= ?))
           ORDER BY chapter, verse""",
        (p["book"], p["start_ch"], p["start_ch"], p["start_v"],
         p["end_ch"], p["end_ch"], p["end_v"]),
    ).fetchall()
    out = " ".join((r["text"] or "").strip() for r in rows if (r["text"] or "").strip())
    return out[:cap]


@bp.route("/api/chrono/intro/<int:day>")
@limiter.limit("200 per hour")
def chrono_intro(day):
    d = _DAYS.get(day)
    if not d:
        return jsonify({"title": None, "summary": None})

    cache_key = f"chrono_intro:{day}"
    if cache_key in _ai_cache:
        return jsonify(_ai_cache[cache_key])
    payload = ai_cache_get(cache_key, _VER)
    if payload is not None:
        _ai_cache[cache_key] = payload
        return jsonify(payload)

    if not _anthropic:
        return jsonify({"title": None, "summary": None})

    # Gather the day's passages (in order) and a capped sample of their text.
    passages = [_PASSAGES[q - 1] for q in d.get("pos", []) if 0 < q <= len(_PASSAGES)]
    labels = "\n".join(f"- {p['label']}" for p in passages) or d.get("label", "")
    conn = db_ro()
    try:
        # Spread the text budget across the passages so a long first one doesn't crowd out the rest.
        per = max(300, int(2400 / max(1, len(passages))))
        text = "\n".join(_passage_text(conn, p, per) for p in passages).strip()
    finally:
        conn.close()
    if not text:
        return jsonify({"title": None, "summary": None})

    try:
        msg = _anthropic.messages.create(
            model=_MODEL,
            max_tokens=320,
            temperature=0,
            system=_SYSTEM,
            messages=[{"role": "user", "content": _PROMPT_TMPL.format(day=day, labels=labels, text=text)}],
        )
        raw = msg.content[0].text.strip()
    except Exception as exc:
        log.warning("chrono intro AI call failed (day %s): %s", day, exc)
        return jsonify({"title": None, "summary": None})

    # First non-empty line = title; the rest = summary.
    parts = [s.strip() for s in raw.split("\n") if s.strip()]
    title = re.sub(r'^["\']|["\']$', "", parts[0]).strip() if parts else None
    summary = " ".join(parts[1:]).strip() if len(parts) > 1 else None
    if title and len(title) > 60:           # a model that ignored the format → no fake title
        summary = raw
        title = None

    payload = {"title": title, "summary": summary}
    if summary:
        ai_cache_put(cache_key, payload, _VER)
        _ai_cache[cache_key] = payload
    return jsonify(payload)
