#!/usr/bin/env python3
"""MetaV person/place sidebar + proper-noun/strongs counts.

Routes for the person/place metadata sidebar (metav_* tables) plus the two small
count endpoints the frontend uses to decide what to show. Looked up by NAME, not
strongs. Depends only on core (DB + the Anthropic client) — a true leaf domain.
"""
from flask import Blueprint, jsonify, request

from core import (
    db, db_ro, _anthropic, log,
    ai_fingerprint, ai_cache_get, ai_cache_put, ai_cache_prune,
)
from entity_resolution import book_num, norm_name

bp = Blueprint("metav", __name__)

# ABP book abbreviation -> full name, for scoping the AI blurb to a real reference
# ("Zephaniah 1:1", not the bare word "Cushi"). Local + self-contained.
_BOOK_FULL = {
    "Gen": "Genesis", "Exo": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
    "Deu": "Deuteronomy", "Jos": "Joshua", "Jdg": "Judges", "Rth": "Ruth",
    "1Sa": "1 Samuel", "2Sa": "2 Samuel", "1Ki": "1 Kings", "2Ki": "2 Kings",
    "1Ch": "1 Chronicles", "2Ch": "2 Chronicles", "Ezr": "Ezra", "Neh": "Nehemiah",
    "Est": "Esther", "Job": "Job", "Psa": "Psalms", "Pro": "Proverbs",
    "Ecc": "Ecclesiastes", "Son": "Song of Songs", "Isa": "Isaiah", "Jer": "Jeremiah",
    "Lam": "Lamentations", "Eze": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea",
    "Joe": "Joel", "Amo": "Amos", "Oba": "Obadiah", "Jon": "Jonah", "Mic": "Micah",
    "Nah": "Nahum", "Hab": "Habakkuk", "Zep": "Zephaniah", "Hag": "Haggai",
    "Zec": "Zechariah", "Mal": "Malachi", "Mat": "Matthew", "Mar": "Mark",
    "Luk": "Luke", "Joh": "John", "Act": "Acts", "Rom": "Romans",
    "1Co": "1 Corinthians", "2Co": "2 Corinthians", "Gal": "Galatians",
    "Eph": "Ephesians", "Php": "Philippians", "Col": "Colossians",
    "1Th": "1 Thessalonians", "2Th": "2 Thessalonians", "1Ti": "1 Timothy",
    "2Ti": "2 Timothy", "Tit": "Titus", "Phm": "Philemon", "Heb": "Hebrews",
    "Jas": "James", "1Pe": "1 Peter", "2Pe": "2 Peter", "1Jo": "1 John",
    "1Jn": "1 John", "2Jo": "2 John", "2Jn": "2 John", "3Jo": "3 John",
    "3Jn": "3 John", "Jud": "Jude", "Rev": "Revelation",
}

# AI person/place blurb (the 'pn' cache). Prompts kept as named constants so the
# fingerprint below covers them — editing either auto-refreshes only this cache.
# The blurb is now SCOPED to the clicked verse: a name shared by several unrelated
# biblical figures (the three Cushis, the several Edens) resolves to the one meant
# at THAT reference instead of wandering across testaments. It is still constrained
# model prose, NOT a verse-checked / citation-gated fact — labelled as such in the UI.
_PN_SYSTEM = (
    "You are a concise biblical reference note. You are given a name and the exact "
    "verse where it occurs. Describe ONLY the specific person, place, or group meant "
    "at THAT verse, fixed by its own context — the book, the era, the surrounding "
    "names. Many biblical names are shared by several unrelated figures; do not "
    "describe a different one and do not blend them. If you are unsure which one the "
    "verse means, say so briefly rather than guess. 1-2 sentences. No theology, no "
    "speculation, no markdown."
)
_PN_USER_TMPL = 'Who or what is "{name}" at {ref}? Describe only the one meant there.'
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
    """Brief AI blurb for a biblical person/place with no metaV row.

    SCOPED to the clicked occurrence (book/chapter/verse query params) so a shared
    name resolves to the figure at THAT reference, not a same-named one in another
    testament (the Cushi-in-Zephaniah -> Acts bug). Cached PER reference for the same
    reason. Still ungrounded model prose — the frontend labels it 'not verse-checked'."""
    if not _anthropic:
        return jsonify({"error": "AI not available"}), 503

    book = (request.args.get("book") or "").strip()
    ch   = (request.args.get("chapter") or "").strip()
    vs   = (request.args.get("verse") or "").strip()
    if book and ch and vs:
        ref = f"{_BOOK_FULL.get(book, book)} {ch}:{vs}"
        cache_key = f"pn:{name.lower()}:{book}{ch}:{vs}"
    else:
        ref = "the Bible"
        cache_key = f"pn:{name.lower()}"

    cached = ai_cache_get(cache_key, _PN_VER)
    if cached is not None:
        return jsonify(cached)

    try:
        msg = _anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=160,
            temperature=0,
            system=_PN_SYSTEM,
            messages=[{"role": "user", "content": _PN_USER_TMPL.format(name=name, ref=ref)}],
        )
        description = msg.content[0].text.strip() if msg.content else ""
    except Exception as e:
        log.error("AI description failed for %s: %s", name, e)
        return jsonify({"error": "AI unavailable"}), 500

    payload = {"name": name, "description": description, "ref": ref, "grounded": False}
    ai_cache_put(cache_key, payload, _PN_VER)
    return jsonify(payload)


def _pin_from_rows(rows):
    """Pick ONE map pin from possibly-many same-name place rows, or decline. A name like
    'Lebanon' carries several metav_places rows for different referents (the region, Mount
    Hermon, a structure in Jerusalem). Rule: pin the coordinate the MOST rows agree on; a
    defensible pin needs a strict winner (more rows than any other point). A tie between
    referents -> no pin (the Eden -> Beth-eden wrong-pin guard). Failure mode is no-pin,
    never a misplaced pin. Returns (lat, lon, ambiguous).

    INTERIM HEURISTIC: the Lebanon win leans on two rows sharing EXACT coordinates, which is
    coincidental duplication, not meaning. A name whose referents are all distinct points
    gets no pin forever, even though the bound TIPNR entity ('Lebanon@Deu.1.7') already says
    which referent the verse means. The real fix is an entity-level join (TIPNR entity ->
    the matching metav_places row, or OpenBibleInfo's per-referent coordinates) — folds into
    the queued MetaV<->TIPNR cross-link work (places edition). See TODO.md."""
    from collections import Counter
    coords = [(r["lat"], r["lon"]) for r in rows if r["lat"] is not None and r["lon"] is not None]
    multi = len({r["place_id"] for r in rows}) > 1
    if not coords:
        return (None, None, multi)
    ranked = Counter(coords).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return (None, None, True)          # no agreed winner -> withhold the pin
    (lat, lon), _ = ranked[0]
    return (lat, lon, False)               # pinned


def _place_coord_rows(conn, name):
    """metav_places rows (place_id, lat, lon) for a bound place's own NAME. Prefer rows
    whose OWN name matches; fall to alias matches ONLY when there is no name match — so a
    bound entity never borrows coordinates from a DIFFERENT place merely aliased to the
    same word. (Beth-eden near Damascus is aliased 'Eden'; the Genesis Eden has no
    coordinates of its own, so the card must decline, not pin Damascus. The real
    entity->row join is the pending tipnr_metav_link table; this is the interim guard.)"""
    rows = conn.execute(
        "SELECT place_id, lat, lon FROM metav_places WHERE name = ? COLLATE NOCASE",
        (name,)).fetchall()
    if rows:
        return rows
    return conn.execute("""
        SELECT p.place_id, p.lat, p.lon FROM metav_places p
        JOIN metav_place_aliases a ON a.place_id = p.place_id WHERE a.alias = ? COLLATE NOCASE
    """, (name,)).fetchall()


@bp.route("/api/metav/place/<path:name>")
def metav_place(name):
    conn = db_ro()
    try:
        rows = conn.execute("""
            SELECT p.place_id, p.name, p.comment, p.lat, p.lon, p.strongs_g
            FROM metav_places p
            WHERE p.name = ? COLLATE NOCASE
            UNION
            SELECT p.place_id, p.name, p.comment, p.lat, p.lon, p.strongs_g
            FROM metav_places p
            JOIN metav_place_aliases a ON a.place_id = p.place_id
            WHERE a.alias = ? COLLATE NOCASE
        """, (name, name)).fetchall()
    finally:
        conn.close()

    if not rows:
        return jsonify({"error": "not found"}), 404

    # A pin is dropped only when the name is unambiguous AND the matched row has its OWN
    # coordinates (the Eden -> Beth-eden-in-Syria wrong-pin guard, shared via _pin_from_rows).
    # We still show the card (name/comment) when coords are withheld.
    row = rows[0]
    lat, lon, ambiguous = _pin_from_rows(rows)

    return jsonify({
        "place_id":  row["place_id"],
        "name":      row["name"],
        "comment":   row["comment"] or "",
        "lat":       lat,
        "lon":       lon,
        "ambiguous": ambiguous,
        "strongs_g": row["strongs_g"] or "",
    })


def _kin_names(blob, cap=8):
    """TIPNR parents/offspring 'Ham@Gen.5.32-1Ch + , Cush@Gen.10.6' -> ['Ham','Cush'].
    Names sit before '@'; '+' splits father/mother, ',' splits a list."""
    import re as _re
    out = []
    for tok in _re.split(r"[,+]", blob or ""):
        nm = tok.split("@")[0].strip().rstrip("(adf)").strip()
        if nm and "/" not in nm and "http" not in nm.lower() and nm not in out:
            out.append(nm)
    return out[:cap]


@bp.route("/api/metav/entity/<path:name>")
def metav_entity(name):
    """The VERSE-BOUND TIPNR entity for a proper-noun click (Issue 2 rebuild). Returns
    the verified entity (the right one for THIS verse) from the pn_binding side table,
    its own grounded description + kin + reference count — so the card states a sourced
    identity instead of a name-guess. 404 -> the frontend falls back to the name-path +
    Fix A blurb. Deploy-safe: if the binding tables aren't built yet, always 404."""
    book = (request.args.get("book") or "").strip()
    ch = (request.args.get("chapter") or "").strip()
    vs = (request.args.get("verse") or "").strip()
    bk = book_num(book)
    if not (bk and ch.isdigit() and vs.isdigit()):
        return jsonify({"error": "need book/chapter/verse"}), 400

    conn = db_ro()
    try:
        have = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
            "('pn_binding','tipnr_entities','tipnr_entity_refs')")}
        if {"pn_binding", "tipnr_entities"} - have:
            return jsonify({"error": "not found"}), 404
        nm = norm_name(name)
        b = conn.execute(
            "SELECT entity_uniq, kind, tier FROM pn_binding "
            "WHERE book=? AND chapter=? AND verse=? AND name=? AND render=1 LIMIT 1",
            (bk, int(ch), int(vs), nm)).fetchone()
        if not b:
            # The reader click can carry the hyphenated surface ("Beth-el") while the
            # binding was keyed on english_head ("bethel") — a surface-form mismatch, not
            # a missing bind. Retry ignoring hyphens/spaces, but only when it resolves to
            # a SINGLE render bind at this verse (never guess between two).
            compact = lambda s: (s or "").replace("-", "").replace(" ", "")
            cn = compact(nm)
            cand = [r for r in conn.execute(
                "SELECT entity_uniq, kind, tier, name FROM pn_binding "
                "WHERE book=? AND chapter=? AND verse=? AND render=1",
                (bk, int(ch), int(vs))) if compact(r["name"]) == cn]
            if len(cand) == 1:
                b = cand[0]
        if not b:
            return jsonify({"error": "not found"}), 404
        e = conn.execute(
            "SELECT uniq, head, section, gender, area, descr, summary, parents, offspring "
            "FROM tipnr_entities WHERE uniq = ?", (b["entity_uniq"],)).fetchone()
        if not e:
            return jsonify({"error": "not found"}), 404
        ref_count = conn.execute(
            "SELECT COUNT(*) FROM tipnr_entity_refs WHERE uniq = ?", (e["uniq"],)
        ).fetchone()[0] if "tipnr_entity_refs" in have else 0
        # display name keeps TIPNR's original casing (uniq = 'Name@FirstRef')
        disp = e["uniq"].split("@")[0].replace("_", " ")
        # Coordinates for a bound PLACE: the map used to ride the name-based metaV place
        # card, which a verse-bind now suppresses (single gate). Read them straight from
        # metav_places under the SAME wrong-pin guard so the bound card can show the map.
        lat = lon = None
        ambiguous = False
        if (e["section"] or "") == "place":
            prows = _place_coord_rows(conn, disp)
            if prows:
                lat, lon, ambiguous = _pin_from_rows(prows)
    finally:
        conn.close()

    return jsonify({
        "bound":     True,
        "uniq":      e["uniq"],
        "name":      disp,
        "section":   e["section"] or "",
        "gender":    e["gender"] or "",
        "area":      e["area"] or "",
        "desc":      e["descr"] or "",
        "summary":   e["summary"] or "",
        "parents":   _kin_names(e["parents"]),
        "offspring": _kin_names(e["offspring"]),
        "ref_count": ref_count,
        "lat":       lat,
        "lon":       lon,
        "ambiguous": ambiguous,
        "kind":      b["kind"] or "",
        "tier":      b["tier"],
    })


@bp.route("/api/strongs-count/<strongs_base>")
def strongs_count_route(strongs_base):
    if strongs_base == "*":
        return jsonify({"count": None})
    # `?by=base` counts on strongs_base instead of the bare `strongs` column. A backfilled
    # proper noun (TIPNR mapped its words onto an H/G number) carries strongs='*' but a real
    # strongs_base (e.g. Eden -> H5731), so its ABP occurrences are only countable by base.
    # Column is a fixed two-way choice, never user text.
    col = "strongs_base" if request.args.get("by") == "base" else "strongs"
    conn = db()
    try:
        row = conn.execute(
            f"SELECT COUNT(*) AS cnt FROM words WHERE {col} = ?"
            " AND english IS NOT NULL AND english != ''",
            (strongs_base,),
        ).fetchone()
    finally:
        conn.close()
    return jsonify({"count": row["cnt"] if row else 0})
