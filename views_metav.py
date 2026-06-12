#!/usr/bin/env python3
"""MetaV person/place sidebar + proper-noun/strongs counts.

Routes for the person/place metadata sidebar (metav_* tables) plus the two small
count endpoints the frontend uses to decide what to show. Looked up by NAME, not
strongs. Depends only on core (DB + the Anthropic client) — a true leaf domain.
"""
from flask import Blueprint, jsonify

from core import (
    db, db_ro, _anthropic, log,
    ai_fingerprint, ai_cache_get, ai_cache_put, ai_cache_prune,
)

bp = Blueprint("metav", __name__)

# AI person/place blurb (the 'pn' cache). Prompts kept as named constants so the
# fingerprint below covers them — editing either auto-refreshes only this cache.
_PN_SYSTEM = (
    "You are a concise biblical reference. Answer in 1-2 sentences only. "
    "State who the person is, their role, key relationships, and main passages. "
    "No speculation, no theology — text first. No markdown."
)
_PN_USER_TMPL = "Describe {name} in the Bible in 1-2 sentences — person, place, or group."
_PN_VER = ai_fingerprint("pn", _PN_SYSTEM, _PN_USER_TMPL)


def prune_cache() -> int:
    """Startup: drop pn rows tagged with an older prompt fingerprint."""
    return ai_cache_prune("pn", _PN_VER)


@bp.route("/api/pn-count/<path:name>")
def pn_count(name):
    conn = db_ro()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM words WHERE english_head = ? COLLATE NOCASE AND strongs_base = '*'",
            (name.lower(),)
        ).fetchone()
    finally:
        conn.close()
    return jsonify({"count": row["cnt"] if row else 0})


@bp.route("/api/metav/person/<path:name>")
def metav_person(name):
    conn = db_ro()
    try:
        # Look up by name or alias — prefer entries with more biographical data
        row = conn.execute("""
            SELECT * FROM (
                SELECT p.person_id, p.name, p.surname, p.gender,
                       p.birth_year, p.death_year, p.birth_place, p.death_place
                FROM metav_people p
                WHERE p.name = ? COLLATE NOCASE
                UNION
                SELECT p.person_id, p.name, p.surname, p.gender,
                       p.birth_year, p.death_year, p.birth_place, p.death_place
                FROM metav_people p
                JOIN metav_people_aliases a ON a.person_id = p.person_id
                WHERE a.alias = ? COLLATE NOCASE
            )
            ORDER BY (birth_year IS NOT NULL) DESC,
                     (death_year IS NOT NULL) DESC
            LIMIT 1
        """, (name, name)).fetchone()
        # Fallback: fuzzy prefix match for Greek vowel suffixes on Hebrew names
        # e.g. "Methusaela" → matches "Methusael" (length ±2, first 5+ chars match)
        if not row and len(name) >= 5:
            prefix = name[:max(5, len(name) - 2)]
            row = conn.execute("""
                SELECT * FROM (
                    SELECT p.person_id, p.name, p.surname, p.gender,
                           p.birth_year, p.death_year, p.birth_place, p.death_place
                    FROM metav_people p
                    WHERE p.name LIKE ? COLLATE NOCASE
                      AND length(p.name) BETWEEN ? AND ?
                    UNION
                    SELECT p.person_id, p.name, p.surname, p.gender,
                           p.birth_year, p.death_year, p.birth_place, p.death_place
                    FROM metav_people p
                    JOIN metav_people_aliases a ON a.person_id = p.person_id
                    WHERE a.alias LIKE ? COLLATE NOCASE
                      AND length(a.alias) BETWEEN ? AND ?
                )
                ORDER BY (birth_year IS NOT NULL) DESC,
                         (death_year IS NOT NULL) DESC
                LIMIT 1
            """, (f"{prefix}%", len(name) - 2, len(name) + 2,
                  f"{prefix}%", len(name) - 2, len(name) + 2)).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404

        pid = row["person_id"]

        # Groups (tribe, genealogy)
        groups = [r["group_name"] for r in conn.execute(
            "SELECT group_name FROM metav_people_groups WHERE person_id = ?", (pid,)
        ).fetchall()]

        # Key relationships
        rels = conn.execute("""
            SELECT r.rel_type, p.name, p.surname, p.person_id
            FROM metav_people_relationships r
            JOIN metav_people p ON p.person_id = r.related_to
            WHERE r.person_id = ?
            ORDER BY CASE r.rel_type
                WHEN 'father' THEN 1
                WHEN 'mother' THEN 2
                WHEN 'spouseOrConcubine' THEN 3
                WHEN 'child' THEN 4
                WHEN 'sibling' THEN 5
                ELSE 6
            END
        """, (pid,)).fetchall()

        relationships = [{"type": r["rel_type"], "name": r["name"] + (" " + r["surname"] if r["surname"] else ""), "id": r["person_id"]} for r in rels]

    finally:
        conn.close()

    full_name = row["name"] + (" " + row["surname"] if row["surname"] else "")
    return jsonify({
        "person_id":   pid,
        "name":        full_name,
        "gender":      row["gender"] or "",
        "birth_year":  row["birth_year"] or "",
        "death_year":  row["death_year"] or "",
        "birth_place": row["birth_place"] or "",
        "death_place": row["death_place"] or "",
        "groups":      groups,
        "relationships": relationships,
    })


@bp.route("/api/metav/ai-description/<path:name>")
def metav_ai_description(name):
    """Generate a brief AI description for a biblical person or place with no metaV data."""
    if not _anthropic:
        return jsonify({"error": "AI not available"}), 503

    cache_key = f"pn:{name.lower()}"
    cached = ai_cache_get(cache_key, _PN_VER)
    if cached is not None:
        return jsonify(cached)

    try:
        msg = _anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            temperature=0,
            system=_PN_SYSTEM,
            messages=[{"role": "user", "content": _PN_USER_TMPL.format(name=name)}],
        )
        description = msg.content[0].text.strip() if msg.content else ""
    except Exception as e:
        log.error("AI description failed for %s: %s", name, e)
        return jsonify({"error": "AI unavailable"}), 500

    payload = {"name": name, "description": description}
    ai_cache_put(cache_key, payload, _PN_VER)
    return jsonify(payload)


@bp.route("/api/metav/place/<path:name>")
def metav_place(name):
    conn = db_ro()
    try:
        row = conn.execute("""
            SELECT p.place_id, p.name, p.comment, p.lat, p.lon, p.strongs_g
            FROM metav_places p
            WHERE p.name = ? COLLATE NOCASE
            UNION
            SELECT p.place_id, p.name, p.comment, p.lat, p.lon, p.strongs_g
            FROM metav_places p
            JOIN metav_place_aliases a ON a.place_id = p.place_id
            WHERE a.alias = ? COLLATE NOCASE
            LIMIT 1
        """, (name, name)).fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "not found"}), 404

    return jsonify({
        "place_id": row["place_id"],
        "name":     row["name"],
        "comment":  row["comment"] or "",
        "lat":      row["lat"],
        "lon":      row["lon"],
        "strongs_g": row["strongs_g"] or "",
    })


@bp.route("/api/strongs-count/<strongs_base>")
def strongs_count_route(strongs_base):
    if strongs_base == "*":
        return jsonify({"count": None})
    conn = db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM words WHERE strongs = ?"
            " AND english IS NOT NULL AND english != ''",
            (strongs_base,),
        ).fetchone()
    finally:
        conn.close()
    return jsonify({"count": row["cnt"] if row else 0})
