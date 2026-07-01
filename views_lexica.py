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
from structural import structural_entry
from views_notes import is_admin

bp = Blueprint("lexica", __name__)

# Rollout gate: Lexica entries render for ADMINS ONLY until the feature is proven. The build
# script keeps writing rows regardless — this controls only WHO can read them, so we can build out
# the fork list + loaded terms and view them in the real card without any public user seeing a
# half-tested entry. ONE global flag — flip to False to go public (a single milestone, not a
# per-word rollout). If we later promote entries individually, a `public` column on lexica_def is
# the clean add. Mirrors views_heb's "gate VISIBILITY during rollout".
LEXICA_ADMIN_ONLY = False   # PUBLIC 2026-06-25 — rollout over; served to everyone, incl. logged-out

# Structural / function-word cards (eimi, …) have their OWN rollout gate, independent of the
# verse-grounded dictionary above. PUBLIC — live for all users, incl. logged-out (JP's call
# 2026-06-25; no admin gating going forward). Flip back to True only to re-gate. (See structural.py.)
STRUCTURAL_ADMIN_ONLY = False


def _has_lexica(conn):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='lexica_def'"
    ).fetchone() is not None


@bp.route("/api/lexica/seams")
def lexica_seams():
    """The SEAM INDEX — every Lexica entry that carries a contested-word `fork`, the words
    where the plain meaning is settled but the READING diverges. Pure read over the stored
    fork data (built by scripts/build_lexica_def.py's CONTESTED register); no engine touch.
    Returns one row per seam: lemma + short gloss + the two authored axes (divergence_type,
    lead_flip) + the full fork (core + priors) for the both-priors card. Deploy-safe: table
    not built → empty list; a word with no fork (e.g. the psyche control) is dropped."""
    if LEXICA_ADMIN_ONLY and not is_admin():
        return jsonify({"seams": []})
    conn = db_ro()
    seams = []
    try:
        if _has_lexica(conn):
            rows = conn.execute("SELECT strongs, def_json FROM lexica_def").fetchall()
            for r in rows:
                if not r["def_json"]:
                    continue
                try:
                    entry = json.loads(r["def_json"])
                except Exception:
                    continue
                fork = entry.get("fork")
                if not fork:
                    continue      # not a contested word (psyche control, ordinary entries) — drop
                seams.append({
                    "strongs": entry.get("strongs") or r["strongs"],
                    "lemma": entry.get("lemma"),
                    "translit": entry.get("translit"),
                    "gloss": fork.get("gloss"),
                    "divergence_type": fork.get("divergence_type"),
                    "lead_flip": bool(fork.get("lead_flip")),
                    "graph_ref": fork.get("graph_ref"),
                    "fork": fork,
                })
    except Exception as e:
        log.warning("seam index lookup failed: %s", e)
        return jsonify({"seams": []})
    finally:
        conn.close()
    # Different-lead seams first, then alphabetically by lemma — a stable, meaningful order.
    seams.sort(key=lambda s: (not s["lead_flip"], (s["lemma"] or "").lower()))
    return jsonify({"seams": seams})


@bp.route("/api/lexica/<strongs>")
def lexica_def(strongs):
    """The Lexica entry for a Strong's number — first a hand-authored STRUCTURAL/function card
    (eimi etc.), else the stored verse-grounded entry — or 404 (word has none / table not built /
    viewer isn't an admin during rollout), which makes the card fall back to LSJ."""
    sid = (strongs or "").strip().upper()
    if sid[:1] not in ("G", "H"):
        sid = "G" + sid
    # Structural / function-word card: a different entry TYPE (the word's grammatical function, not
    # a verse-grounded sense list). Hand-authored + served straight from structural.py — no table,
    # so no PA data build. A dotted conjugate (G1510.2.3) resolves to its lemma's one entry and
    # carries its own parse stamp. Its OWN rollout gate so eimi can be proven before going public.
    se = structural_entry(sid)
    if se is not None:
        if STRUCTURAL_ADMIN_ONLY and not is_admin():
            return jsonify({"error": "not found"}), 404
        return jsonify(se)
    if LEXICA_ADMIN_ONLY and not is_admin():
        return jsonify({"error": "not found"}), 404      # admin-only rollout — non-admins fall through to LSJ
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
