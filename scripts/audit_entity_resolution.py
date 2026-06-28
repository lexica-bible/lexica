#!/usr/bin/env python3
"""
audit_entity_resolution.py — READ-ONLY blast-radius report for Issue 2
(proper-noun / entity resolution).

WHY: every word card resolves a person/place by NAME STRING at render time
(metav_people/metav_places WHERE name=? LIMIT 1, and the AI blurb gets only the
bare name). No person_id/place_id is ever bound to a word. This script measures
how big the resulting collision problem actually is, so we can decide whether a
light disambiguation or a full occurrence-binding rebuild is warranted.

It opens bible.db READ-ONLY and only ever SELECTs — it cannot change anything.

Usage (on PythonAnywhere):
    python3 scripts/audit_entity_resolution.py
    python3 scripts/audit_entity_resolution.py /home/appssanding720/bible-db/bible.db
"""

import re
import sys
import sqlite3
from collections import defaultdict

DB = sys.argv[1] if len(sys.argv) > 1 else "/home/appssanding720/bible-db/bible.db"

# ABP verses.book is a 3-letter abbreviation. NT set (same as import_tipnr.py).
NT_BOOKS = {
    "Mat", "Mar", "Luk", "Joh", "Act", "Rom", "1Co", "2Co", "Gal",
    "Eph", "Php", "Col", "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm",
    "Heb", "Jas", "1Pe", "2Pe", "1Jo", "2Jo", "3Jo", "Jud", "Rev",
}


def norm(s):
    """Lower + strip trailing punctuation/dashes — a close proxy for the app's
    extractProperName() applied to a clickable proper-noun label."""
    if not s:
        return ""
    s = re.sub(r"[\s,.:;!?'\"–\-]+$", "", s.strip())
    return s.lower()


def hr(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    print(f"READ-ONLY entity-resolution audit -> {DB}")
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    def tables():
        return {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    T = tables()

    def cols(t):
        if t not in T:
            return set()
        return {r[1] for r in conn.execute(f"PRAGMA table_info({t})")}

    # ── 0. Schema reality check — is any entity id bound anywhere? ──────────
    hr("0. SCHEMA — is a person/place id bound to a word anywhere?")
    print(f"  words columns : {sorted(cols('words'))}")
    print(f"  tipnr columns : {sorted(cols('tipnr'))}")
    print(f"  metav_people  : {sorted(cols('metav_people'))}")
    print(f"  metav_places  : {sorted(cols('metav_places'))}")
    bind = [c for c in cols('words') if 'person' in c or 'place' in c or 'entity' in c]
    print(f"\n  word columns naming a person/place/entity id: {bind or 'NONE'}")
    tbind = [c for c in cols('tipnr') if 'person' in c or 'place' in c or c.endswith('_id')]
    print(f"  tipnr columns linking to a metaV entity id   : {tbind or 'NONE'}")
    print("  -> If both are NONE, EVERY proper-noun occurrence is resolved by"
          " name string; none are bound.")

    # ── Pull the metaV name -> id maps (name + aliases) ────────────────────
    place_ids = defaultdict(set)   # norm(name) -> {place_id}
    for r in conn.execute("SELECT place_id, name FROM metav_places WHERE name IS NOT NULL"):
        place_ids[norm(r["name"])].add(r["place_id"])
    if "metav_place_aliases" in T:
        for r in conn.execute("SELECT place_id, alias FROM metav_place_aliases WHERE alias IS NOT NULL"):
            place_ids[norm(r["alias"])].add(r["place_id"])

    person_ids = defaultdict(set)  # norm(name) -> {person_id}
    for r in conn.execute("SELECT person_id, name FROM metav_people WHERE name IS NOT NULL"):
        person_ids[norm(r["name"])].add(r["person_id"])
    if "metav_people_aliases" in T:
        for r in conn.execute("SELECT person_id, alias FROM metav_people_aliases WHERE alias IS NOT NULL"):
            person_ids[norm(r["alias"])].add(r["person_id"])

    place_ids.pop("", None)
    person_ids.pop("", None)

    place_multi  = {nm: ids for nm, ids in place_ids.items()  if len(ids) > 1}
    person_multi = {nm: ids for nm, ids in person_ids.items() if len(ids) > 1}
    both         = {nm for nm in place_ids if nm in person_ids}

    # ── 1. metaV ambiguity (the resolution TARGETS) ────────────────────────
    hr("1. metaV NAME AMBIGUITY (LIMIT 1 silently picks one of these)")
    print(f"  distinct place names total           : {len(place_ids):,}")
    print(f"  place names mapping to >1 place_id    : {len(place_multi):,}   (Eden class)")
    print(f"  distinct person names total          : {len(person_ids):,}")
    print(f"  person names mapping to >1 person_id  : {len(person_multi):,}   (multi-Cushi class)")
    print(f"  names that are BOTH a person AND place: {len(both):,}   (person-for-place class)")

    # ── 2. Proper-noun occurrences in the text ─────────────────────────────
    hr("2. PROPER-NOUN OCCURRENCES IN THE TEXT (clickable words)")
    has_pn = "is_pn" in cols("words")
    pn_where = "w.is_pn = 1" if has_pn else "w.strongs_base = '*'"
    rows = conn.execute(f"""
        SELECT COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               v.book AS book
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE {pn_where}
          AND COALESCE(NULLIF(w.english_head,''), w.english) IS NOT NULL
          AND COALESCE(NULLIF(w.english_head,''), w.english) != ''
    """).fetchall()

    occ_by_name      = defaultdict(int)   # norm name -> occurrence count
    books_by_name    = defaultdict(set)   # norm name -> {book}
    testaments       = defaultdict(set)   # norm name -> {'OT','NT'}
    for r in rows:
        nm = norm(r["label"])
        if not nm:
            continue
        occ_by_name[nm] += 1
        books_by_name[nm].add(r["book"])
        testaments[nm].add("NT" if r["book"] in NT_BOOKS else "OT")

    total_occ   = sum(occ_by_name.values())
    distinct_nm = len(occ_by_name)
    print(f"  proper-noun occurrences  : {total_occ:,}")
    print(f"  distinct surface names   : {distinct_nm:,}")

    # ── 3. EXPOSURE — occurrences a reader can actually hit wrong ──────────
    hr("3. EXPOSURE (occurrences whose name is ambiguous or has no metaV row)")
    ambiguous_names = set(place_multi) | set(person_multi) | both
    amb_occ  = sum(c for nm, c in occ_by_name.items() if nm in ambiguous_names)
    amb_nm   = sum(1 for nm in occ_by_name if nm in ambiguous_names)
    print(f"  names that are ambiguous AND occur in the text : {amb_nm:,}")
    print(f"  occurrences landing on an ambiguous name       : {amb_occ:,}"
          f"   ({100*amb_occ/total_occ:.1f}% of proper-noun clicks)" if total_occ else "")

    # AI-blurb fallback class: a clickable name with NO person AND NO place row
    no_meta_nm  = [nm for nm in occ_by_name if nm not in person_ids and nm not in place_ids]
    no_meta_occ = sum(occ_by_name[nm] for nm in no_meta_nm)
    print(f"\n  names with NO metaV person AND NO metaV place   : {len(no_meta_nm):,}")
    print(f"  occurrences -> bare-name AI blurb (Cushi class) : {no_meta_occ:,}"
          f"   ({100*no_meta_occ/total_occ:.1f}% of proper-noun clicks)" if total_occ else "")

    # Cross-testament names (a bare-name lookup/AI cannot tell which testament)
    xtest = [nm for nm, ts in testaments.items() if len(ts) > 1]
    xtest_occ = sum(occ_by_name[nm] for nm in xtest)
    print(f"\n  names occurring in BOTH an OT and an NT book    : {len(xtest):,}"
          f"  ({xtest_occ:,} occurrences)")

    # ── 4. Worst offenders (is it a handful or a long tail?) ───────────────
    hr("4. WORST AMBIGUOUS NAMES BY OCCURRENCE COUNT (long-tail check)")
    worst = sorted(((occ_by_name[nm], nm) for nm in occ_by_name if nm in ambiguous_names),
                   reverse=True)[:30]
    print("   occ  name            #person  #place  testaments")
    for c, nm in worst:
        np = len(person_ids.get(nm, ()))
        npl = len(place_ids.get(nm, ()))
        print(f"  {c:5}  {nm:14}  {np:6}  {npl:6}  {','.join(sorted(testaments[nm]))}")

    # ── 5. Concrete spot-checks for the reported symptoms ──────────────────
    hr("5. SPOT-CHECKS — the actual reported symptoms")
    for nm in ["cushi", "eden", "beth-eden", "beth eden"]:
        key = norm(nm)
        print(f"\n  '{nm}'")
        print(f"     occurrences in text : {occ_by_name.get(key, 0)}"
              f"  books={sorted(books_by_name.get(key, []))}")
        pids = sorted(person_ids.get(key, ()))
        plids = sorted(place_ids.get(key, ()))
        print(f"     metav_people ids    : {pids or 'none'}")
        print(f"     metav_places ids    : {plids or 'none'}")
        for pid in plids[:4]:
            p = conn.execute("SELECT name, lat, lon, comment FROM metav_places WHERE place_id=?",
                             (pid,)).fetchone()
            if p:
                cm = (p["comment"] or "")[:60]
                print(f"        place {pid}: {p['name']}  ({p['lat']},{p['lon']})  {cm}")
        # what the app would pick (LIMIT 1, person ordered by birth/death present)
        pick = conn.execute("""
            SELECT name, birth_year, death_year FROM metav_people
            WHERE name = ? COLLATE NOCASE
            ORDER BY (birth_year IS NOT NULL) DESC, (death_year IS NOT NULL) DESC LIMIT 1
        """, (nm,)).fetchone()
        if pick:
            print(f"     app would show PERSON: {pick['name']}"
                  f"  born={pick['birth_year']} died={pick['death_year']}")
        # cached AI blurb, if any
        if "ai_search_cache" in T:
            cr = conn.execute(
                "SELECT result_json FROM ai_search_cache WHERE query=? LIMIT 1",
                (f"pn:{key}",)).fetchone()
            if cr:
                print(f"     cached AI blurb     : {cr['result_json'][:240]}")

    conn.close()
    print("\nDone. (read-only — nothing was changed)")


if __name__ == "__main__":
    main()
