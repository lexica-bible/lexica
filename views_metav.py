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
    h_abp_predicate,
)
from entity_resolution import book_num, norm_name, is_people_group

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
    "You are a concise biblical reference note. You are given a name, the verse where it "
    "occurs, and the exact text of that verse in the translation the reader is viewing. "
    "Explain ONLY the specific person, place, or group this name refers to AS IT APPEARS "
    "IN THAT VERSE, fixed by its own context — the book, the era, the surrounding names. "
    "The name IS present in the verse as shown; describe what it denotes there. Do NOT say "
    "the term is absent or wrong, and do NOT fact-check the shown text against Hebrew, "
    "English, or other translations — this translation may render or transliterate a name "
    "differently (for example a Greek/Septuagint form such as 'Antilebanon' for the "
    "Anti-Lebanon range), and that rendering is correct for this reader. Many names are "
    "shared by several unrelated figures; describe only the one meant here and do not blend "
    "them. If genuinely unsure which one, say so briefly. 1-2 sentences. No theology, no "
    "speculation, no markdown."
)
# With the displayed verse (the normal path):
_PN_USER_TMPL = (
    'In {translation}, {ref} reads:\n"{verse}"\n\n'
    'Who or what is "{name}" as it appears in this verse? Describe only the one meant there.'
)
# Fallback when the verse text can't be fetched (keeps a single system prompt):
_PN_USER_TMPL_NOVERSE = 'Who or what is "{name}" at {ref}? Describe only the one meant there.'
_PN_VER = ai_fingerprint("pn", _PN_SYSTEM, _PN_USER_TMPL, _PN_USER_TMPL_NOVERSE)

# translation code -> (full name for the prompt, verse-table + columns keyed by book-NUMBER;
# ABP is keyed by book ABBREV in `verses`). heb/unknown fall back to ABP (the anchor text).
_TXT_META = {
    "kjv": ("the King James Version", "kjv_verses", "verse_text"),
    "bsb": ("the Berean Standard Bible", "bsb_verses", "verse_text"),
}


def _displayed_verse(conn, translation, book, ch, vs):
    """The verse text the reader is looking at + that translation's full name, so the AI
    note explains a name AS RENDERED (e.g. ABP's Greek 'Antilebanon') instead of fact-
    checking it against Hebrew/English. Falls back to the ABP text; ('', '') if not found."""
    t = (translation or "abp").lower()
    try:
        if t in _TXT_META:
            full, tbl, col = _TXT_META[t]
            bk = book_num(book)
            if bk:
                r = conn.execute(
                    f"SELECT {col} AS txt FROM {tbl} WHERE book_id=? AND chapter=? AND verse_num=?",
                    (bk, int(ch), int(vs))).fetchone()
                if r and r["txt"]:
                    return r["txt"], full
        # ABP (default / heb / anything else): the anchor Greek text, keyed by abbrev
        r = conn.execute(
            "SELECT text AS txt FROM verses WHERE book=? AND chapter=? AND verse=?",
            (book, int(ch), int(vs))).fetchone()
        if r and r["txt"]:
            return r["txt"], "the Apostolic Bible Polyglot (a Greek text following the Septuagint)"
    except Exception:
        pass
    return "", ""


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


def _person_card(conn, pid):
    """The rich person payload (bio + groups + relationships) for a metav_people
    person_id. Shared by the name path (/api/metav/person) and the verse-bound link
    path (/api/metav/entity), so the two renders can never drift. Returns None if the
    person_id has no row."""
    row = conn.execute(
        "SELECT person_id, name, surname, gender, birth_year, death_year, "
        "birth_place, death_place FROM metav_people WHERE person_id = ?", (pid,)
    ).fetchone()
    if not row:
        return None

    groups = [r["group_name"] for r in conn.execute(
        "SELECT group_name FROM metav_people_groups WHERE person_id = ?", (pid,)
    ).fetchall()]

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
    relationships = [{"type": r["rel_type"],
                      "name": r["name"] + (" " + r["surname"] if r["surname"] else ""),
                      "id": r["person_id"]} for r in rels]

    full_name = row["name"] + (" " + row["surname"] if row["surname"] else "")
    return {
        "person_id":   pid,
        "name":        full_name,
        "gender":      row["gender"] or "",
        "birth_year":  row["birth_year"] or "",
        "death_year":  row["death_year"] or "",
        "birth_place": row["birth_place"] or "",
        "death_place": row["death_place"] or "",
        "groups":      groups,
        "relationships": relationships,
    }


def _person_has_bio(card):
    """A linked person card only EARNS the rich frame when it adds real biography over
    the thin TIPNR facts (born/died, or 2+ relationships). Below that bar the caller
    falls back to the thin card — the rich → TIPNR → Strong's chain — never an empty
    rich frame. Mirrors the name-path's own personOk quality gate."""
    return bool(card and (card["birth_year"] or card["death_year"]
                          or len(card["relationships"]) >= 2))


def _name_is_multi_referent(conn, name):
    """A bare surface name borne by MORE THAN ONE biblical man. An UNBOUND click (no
    verse to say which one) then has no basis to serve a single person's bio — so the
    name path declines the card and the reader gets Strong's + occurrences (the honest
    'the app doesn't know which one' card), never one man's family asserted as fact
    (Gen 36:37's Edomite 'Saul' was being served King Saul's kin). Two signals, EITHER
    sufficient (mirrors the link-build's own multi-candidate test):
      1. several metav_people candidates for the name — INCLUDING aliases, since ABP
         renders a name one way and MetaV another (ABP 'Saul' == MetaV 'Shaul').
      2. several TIPNR person entities under the surface name.
    Signal 1 (metaV + aliases) is the PRIMARY catch — it carried Saul (3 candidates:
    King Saul + the two 'Shaul' alias records). Signal 2 matches TIPNR's SURFACE key, so
    it only counts entities keyed under the name's Latin form and is a secondary confirmer
    (under-counts a name TIPNR keys unlike its ABP surface). The verse-BOUND path is
    UNAFFECTED: a bind already fixes which man, so its rich card (and the seven
    per-referent pharaohs) still serve. Deploy-safe: TIPNR check skipped if table absent."""
    n_metav = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT person_id FROM metav_people         WHERE name  = ? COLLATE NOCASE
            UNION
            SELECT person_id FROM metav_people_aliases  WHERE alias = ? COLLATE NOCASE
        )""", (name, name)).fetchone()[0]
    if n_metav > 1:
        return True
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='tipnr_entities'").fetchone():
        n_tipnr = conn.execute(
            "SELECT COUNT(*) FROM tipnr_entities WHERE section='person' "
            "AND (head = ? COLLATE NOCASE OR uniq LIKE ?)",
            (name, name + "@%")).fetchone()[0]
        if n_tipnr > 1:
            return True
    return False


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
        # Sole-referent label (TICKET_pn_label_confidence): an EXACT name/alias hit that
        # clears the multi-referent guard below is, by construction, the only person of
        # this name in our records (metaV + TIPNR) — the card may say so confidently.
        # A FUZZY hit never earns it: the served person's own name isn't the clicked
        # name (Archite -> Archippus), so "only person of this name" would be false.
        exact_hit = row is not None
        guard_name = name
        # Hyphen-blind fallback (lane-1/3 fix 2026-07-29): ABP word cells store names
        # unhyphenated ("bethhoron") while metaV spells them "Beth-horon" (and the
        # reverse: clicked "Bath-sheba" vs metaV "Bathsheba"). Same-name-different-
        # spelling, so it ranks WITH the exact tier — the multi-referent guard and the
        # sole-referent label then run on the MATCHED canonical spelling. Mirrors the
        # hyphen-blind retry /api/metav/entity has done since the Beth-el fix.
        if not row:
            cn = name.replace("-", "").replace(" ", "")
            if cn:
                row = conn.execute("""
                    SELECT * FROM (
                        SELECT p.person_id, p.name, p.surname, p.gender,
                               p.birth_year, p.death_year, p.birth_place, p.death_place
                        FROM metav_people p
                        WHERE REPLACE(REPLACE(p.name,'-',''),' ','') = ? COLLATE NOCASE
                        UNION
                        SELECT p.person_id, p.name, p.surname, p.gender,
                               p.birth_year, p.death_year, p.birth_place, p.death_place
                        FROM metav_people p
                        JOIN metav_people_aliases a ON a.person_id = p.person_id
                        WHERE REPLACE(REPLACE(a.alias,'-',''),' ','') = ? COLLATE NOCASE
                    )
                    ORDER BY (birth_year IS NOT NULL) DESC,
                             (death_year IS NOT NULL) DESC
                    LIMIT 1
                """, (cn, cn)).fetchone()
                if row:
                    exact_hit = True
                    guard_name = row["name"]
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

        # Referent-multiplicity guard: this endpoint is the UNBOUND path (the frontend
        # only calls it when no verse-bind owns the card). If several men share the
        # name, decline to serve any single bio — the frontend then shows Strong's +
        # occurrences (+ its verse-scoped AI note), the honest card. A single-referent
        # name (David) is unaffected and still serves its rich card here.
        if _name_is_multi_referent(conn, guard_name):
            return jsonify({"ambiguous": True}), 200

        card = _person_card(conn, row["person_id"])
        # TIPNR one-liner for the slim card (Part 1 diagnosis 2026-07-29): attached
        # only when EXACTLY ONE TIPNR person entity carries this name — the top-20
        # probe proved most are absent from the imported table (not a keying bug),
        # so this genuinely reaches Paul-class names that have one, nothing more.
        if card and conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                 "AND name='tipnr_entities'").fetchone():
            trow = conn.execute(
                "SELECT COUNT(*), MIN(descr) FROM tipnr_entities WHERE section='person' "
                "AND (head = ? COLLATE NOCASE OR uniq LIKE ?)",
                (guard_name, guard_name + "@%")).fetchone()
            if trow[0] == 1 and trow[1]:
                card["tipnr_desc"] = trow[1].replace("(?)", "").split("=")[0].strip()
    finally:
        conn.close()

    if not card:
        return jsonify({"error": "not found"}), 404
    card["sole_referent"] = exact_hit
    return jsonify(card)


@bp.route("/api/metav/ai-description/<path:name>")
def metav_ai_description(name):
    """Brief AI blurb for a biblical person/place with no metaV row.

    SCOPED to the clicked occurrence (book/chapter/verse query params) so a shared
    name resolves to the figure at THAT reference, not a same-named one in another
    testament (the Cushi-in-Zephaniah -> Acts bug). Cached PER reference for the same
    reason. Still ungrounded model prose — the frontend labels it "claims not verified
    against the verse text" (reworded 2026-07-30; verse-check cert lane =
    docs/tickets/TICKET_blurb_verse_check.md)."""
    if not _anthropic:
        return jsonify({"error": "AI not available"}), 503

    book = (request.args.get("book") or "").strip()
    ch   = (request.args.get("chapter") or "").strip()
    vs   = (request.args.get("verse") or "").strip()
    translation = (request.args.get("translation") or "abp").strip().lower()
    verse_text, txt_full = "", ""
    if book and ch and vs:
        ref = f"{_BOOK_FULL.get(book, book)} {ch}:{vs}"
        # feed the verse the reader is actually looking at, so the note explains the name
        # AS RENDERED there (ABP's Greek 'Antilebanon') instead of fact-checking it
        conn = db_ro()
        try:
            verse_text, txt_full = _displayed_verse(conn, translation, book, ch, vs)
        finally:
            conn.close()
        cache_key = f"pn:{name.lower()}:{book}{ch}:{vs}:{translation}"
    else:
        ref = "the Bible"
        cache_key = f"pn:{name.lower()}"

    cached = ai_cache_get(cache_key, _PN_VER)
    if cached is not None:
        return jsonify(cached)

    if verse_text:
        user = _PN_USER_TMPL.format(name=name, ref=ref, translation=txt_full, verse=verse_text)
    else:
        user = _PN_USER_TMPL_NOVERSE.format(name=name, ref=ref)
    try:
        msg = _anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=160,
            temperature=0,
            system=_PN_SYSTEM,
            messages=[{"role": "user", "content": user}],
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
        # Hyphen-blind fallback (lane-1/3 fix 2026-07-29, same shape as the person
        # endpoint): "Bethhoron" click finds the "Beth-horon" place row. Exact tier
        # missed entirely, so the compact match IS the match; the sole/TIPNR checks
        # below then run on the matched canonical spelling.
        tipnr_name = name
        if not rows:
            cn = name.replace("-", "").replace(" ", "")
            if cn:
                rows = conn.execute("""
                    SELECT p.place_id, p.name, p.comment, p.lat, p.lon, p.strongs_g
                    FROM metav_places p
                    WHERE REPLACE(REPLACE(p.name,'-',''),' ','') = ? COLLATE NOCASE
                    UNION
                    SELECT p.place_id, p.name, p.comment, p.lat, p.lon, p.strongs_g
                    FROM metav_places p
                    JOIN metav_place_aliases a ON a.place_id = p.place_id
                    WHERE REPLACE(REPLACE(a.alias,'-',''),' ','') = ? COLLATE NOCASE
                """, (cn, cn)).fetchall()
                if rows:
                    tipnr_name = rows[0]["name"]
        # Sole-referent label (TICKET_pn_label_confidence): confident only when exactly
        # one place carries this name in BOTH sources we hold — one metav_places
        # referent, and no second TIPNR place entity under the surface name (mirrors the
        # person guard's TIPNR leg; table-existence-gated like it).
        sole = len({r["place_id"] for r in rows}) == 1
        if sole and conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                 "AND name='tipnr_entities'").fetchone():
            n_tipnr = conn.execute(
                "SELECT COUNT(*) FROM tipnr_entities WHERE section='place' "
                "AND (head = ? COLLATE NOCASE OR uniq LIKE ?)",
                (tipnr_name, tipnr_name + "@%")).fetchone()[0]
            if n_tipnr > 1:
                sole = False
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
        "sole_referent": sole,
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
    pos = (request.args.get("pos") or "").strip()
    bk = book_num(book)
    if not (bk and ch.isdigit() and vs.isdigit()):
        return jsonify({"error": "need book/chapter/verse"}), 400

    conn = db_ro()
    try:
        have = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
            "('pn_binding','tipnr_entities','tipnr_entity_refs','tipnr_metav_link',"
            "'pn_slot_binding')")}
        if {"pn_binding", "tipnr_entities"} - have:
            return jsonify({"error": "not found"}), 404
        nm = norm_name(name)
        # Word-position slot bind FIRST (the wordpos lane, design ratified
        # 2026-08-07): a ruled slot at this exact word position serves its own
        # per-slot entity — the only path that can tell two same-named people
        # (or a person from a place) apart inside one verse. Name must still
        # compact-match (staleness tripwire mirrors the landing guard). No
        # pos / no table / no row -> the verse-grain lookup below, byte-same.
        b = None
        if pos.isdigit() and "pn_slot_binding" in have:
            compact = lambda s: (s or "").lower().replace("-", "").replace(" ", "")
            sb = conn.execute(
                "SELECT name, entity_uniq, kind FROM pn_slot_binding "
                "WHERE book=? AND chapter=? AND verse=? AND position=? "
                "AND render=1 LIMIT 1",
                (bk, int(ch), int(vs), int(pos))).fetchone()
            if sb and compact(sb["name"]) == compact(nm):
                b = {"entity_uniq": sb["entity_uniq"], "kind": sb["kind"],
                     "rule": "slot-ruled", "tier": None}
        if b is None:
            b = conn.execute(
                "SELECT entity_uniq, kind, rule, tier FROM pn_binding "
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
                "SELECT entity_uniq, kind, rule, tier, name FROM pn_binding "
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

        # Rich MetaV enrichment for a bound PERSON: one join to tipnr_metav_link
        # (the pre-vetted metaV person_id), then the SAME rich card the name path
        # serves — so the panel shows David-style badges/born-died/kin while TIPNR
        # stays the identity spine. HARD People/Clan gate: a gentilic click (Jews ->
        # Judah) or a plural-people entity NEVER borrows the ancestor's individual
        # bio — it must keep the People/Clan card. is_people_group is the SAME shared
        # predicate the card path uses (never a second copy). Below-bio links fall
        # back to the thin TIPNR facts (_person_has_bio); table-absence -> no metav.
        metav = None
        if ((e["section"] or "") == "person"
                and not is_people_group(name) and not is_people_group(disp)
                and "tipnr_metav_link" in have):
            lk = conn.execute(
                "SELECT metav_id FROM tipnr_metav_link "
                "WHERE uniq = ? AND kind = 'person' LIMIT 1", (e["uniq"],)).fetchone()
            if lk and lk["metav_id"] is not None:
                card = _person_card(conn, lk["metav_id"])
                if _person_has_bio(card):
                    metav = card
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
        # C: the CLICKED word is a people-group (gentilic) -> the card renders "People /
        # Clan" and drops the ancestor's individual kin. head_is_people = the bound
        # entity's OWN name is itself a plural people (Jebusites), so a "descended from"
        # line would read circular and is suppressed.
        "people_group":   is_people_group(name),
        "head_is_people": is_people_group(disp),
        "kind":      b["kind"] or "",
        # rule = the evidence class within the kind (witness: 'sole-entity' Lane A
        # vs 'context-run' Lane C) — the card sentence keys off it.
        "rule":      b["rule"] or "",
        "tier":      b["tier"],
        # Rich MetaV person card when the bound person is cross-linked and adds real
        # bio (else null -> the frontend keeps the thin TIPNR facts). Gated above by
        # the same People/Clan predicate as the card path.
        "metav":     metav,
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
        if col == "strongs_base" and strongs_base.startswith("H"):
            # Candidate-3 dormant repoint (core.py block comment): post-retirement
            # a backfilled PN's Hebrew number lives in pn_hebrew_xref, not
            # strongs_base — the helper unions it back in; pre-rebuild it returns
            # the plain match and this is today's count exactly.
            pred, params = h_abp_predicate(conn, strongs_base)
            row = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM words w WHERE {pred}"
                " AND w.english IS NOT NULL AND w.english != ''",
                params,
            ).fetchone()
        else:
            row = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM words WHERE {col} = ?"
                " AND english IS NOT NULL AND english != ''",
                (strongs_base,),
            ).fetchone()
    finally:
        conn.close()
    return jsonify({"count": row["cnt"] if row else 0})


# ---------------------------------------------------------------------------
# R-2 stage 2: per-click Greek identity for an ABP proper-noun card
# (docs/PLAN_r2_stage2.md). Served from the stage-1 side tables only —
# pn_greek_identity + step_lexicon; the words table is never touched. Gated by
# core.READER_GREEK_IDENTITY: with the switch OFF every call answers 404 and the
# frontend renders today's card unchanged (the OFF-proof gate). Per-click by
# reviewer ruling (receipt 0): the chapter feed stays byte-identical.
# ---------------------------------------------------------------------------

def _greek_identity_payload(conn, verse_id, position):
    """Identity + counts for ONE proper-noun word. Returns None when there is
    nothing to serve: no row, tables absent, or the 'none' bucket (control C4 —
    those cards must not change). Pure function of the connection so the locked
    test (tests/test_pn_greek_identity.py) drives it on a fixture db."""
    have = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
        "('pn_greek_identity','step_lexicon','lexicon','words')")}
    if "pn_greek_identity" not in have:
        return None
    r = conn.execute(
        "SELECT greek_strongs, greek_lemma, source, hebrew_base "
        "FROM pn_greek_identity WHERE verse_id = ? AND position = ?",
        (verse_id, position)).fetchone()
    if not r or r["source"] == "none":
        return None
    gs = r["greek_strongs"]
    lemma = r["greek_lemma"] or ""
    translit = ""
    step = False
    if gs:
        # Lemma/translit resolve: main lexicon first, else step_lexicon — the
        # STEP flag marks an extended number our lexicon doesn't carry (S2-Q2:
        # the card shows a quiet "STEP" source tag beside it).
        lex = conn.execute(
            "SELECT lemma, translit FROM lexicon WHERE strongs_g = ?",
            (gs,)).fetchone() if "lexicon" in have else None
        if lex and lex["lemma"]:
            lemma, translit = lex["lemma"], lex["translit"] or ""
        elif "step_lexicon" in have:
            # step_lexicon keys: estrong = padded TBESG text ('G0007G'), base =
            # plain NUMBER (7) — the indexed join key. The identity number is
            # unpadded text ('G9827'), so join on the number, never the text
            # (receipt-2 catch: a text join here never matched anything).
            digits = "".join(ch for ch in gs[1:] if ch.isdigit())
            sl = conn.execute(
                "SELECT lemma, translit FROM step_lexicon WHERE base = ? "
                "ORDER BY estrong LIMIT 1",
                (int(digits),)).fetchone() if digits else None
            if sl and sl["lemma"]:
                lemma, translit, step = sl["lemma"], sl["translit"] or "", True
        # S2-Q4: a numbered identity counts by its Greek number — over the
        # identity table, the same derivation the stage-1 audit certified.
        count = conn.execute(
            "SELECT count(*) FROM pn_greek_identity WHERE greek_strongs = ?",
            (gs,)).fetchone()[0]
    else:
        # lemma-only (Q3): no number in any scheme — count by the stored form.
        count = conn.execute(
            "SELECT count(*) FROM pn_greek_identity "
            "WHERE greek_lemma = ? AND greek_strongs IS NULL",
            (lemma,)).fetchone()[0] if lemma else 0
    heb_count = None
    if r["hebrew_base"] and "words" in have:
        # The cross-ref line carries its OWN count (S2-Q4: nothing findable
        # before becomes unfindable) — same shape as /api/strongs-count?by=base.
        # Candidate-3 dormant repoint: h_abp_predicate unions pn_hebrew_xref in
        # once the retirement lands (this count would silently zero otherwise —
        # the §6 collision); pre-rebuild it's the plain match, today's number.
        _hpred, _hparams = h_abp_predicate(conn, r["hebrew_base"])
        heb_count = conn.execute(
            f"SELECT count(*) FROM words w WHERE {_hpred} "
            "AND w.english IS NOT NULL AND w.english != ''",
            _hparams).fetchone()[0]
    return {
        "greek_strongs": gs,
        "lemma": lemma,
        "translit": translit,
        "step": step,
        "source": r["source"],
        "greek_count": count,
        "hebrew_base": r["hebrew_base"],
        "hebrew_count": heb_count,
    }


@bp.route("/api/pn/greek-identity")
def pn_greek_identity_route():
    import core as _core
    if not _core.READER_GREEK_IDENTITY:
        return jsonify({"error": "not found"}), 404
    book = (request.args.get("book") or "").strip()
    ch = (request.args.get("chapter") or "").strip()
    vs = (request.args.get("verse") or "").strip()
    pos = (request.args.get("pos") or "").strip()
    if not (book and ch.isdigit() and vs.isdigit() and pos.isdigit()):
        return jsonify({"error": "need book/chapter/verse/pos"}), 400
    conn = db_ro()
    try:
        vrow = conn.execute(
            "SELECT id FROM verses WHERE book = ? AND chapter = ? AND verse = ?",
            (book, int(ch), int(vs))).fetchone()
        payload = _greek_identity_payload(conn, vrow["id"], int(pos)) if vrow else None
    finally:
        conn.close()
    if not payload:
        return jsonify({"error": "not found"}), 404
    return jsonify(payload)
