#!/usr/bin/env python3
"""build_pn_greek_identity.py — R-2 stage 1: Greek identity ADDED ALONGSIDE Hebrew.

For every ABP proper-noun word (is_pn=1) computes a GREEK identity per the ruled design
(docs/DESIGN_greek_name_identity.md), layered:
  abp-tag    the word's own strongs_base is already a G-number (mostly NT names)
  tipnr      the word's TIPNR entity carries a Greek number (renderable via step_lexicon)
  lemma-only no Greek number in any scheme; the word's own Greek lemma is the identity
             and the card will show the honest no-number state (Q3)

Stage-1 contract: writes ONLY its own table `pn_greek_identity` keyed (verse_id,
position); words/verses untouched; Hebrew strongs_base stays authoritative and is
snapshotted per word as the future cross-reference (Q2 side-table ruling). No live
code reads the table until the stage-2 flip.

Entity resolution reuses the PRODUCTION paths: pn_binding rows (the binder's verdicts)
first, then import_tipnr's parsed lookup for unbound words — never a re-implementation.

Usage (PA):
  python3 scripts/build_pn_greek_identity.py ~/bible-db/bible_test.db          # dry-run
  python3 scripts/build_pn_greek_identity.py ~/bible-db/bible_test.db --apply
"""
import os
import re
import sqlite3
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))
import import_tipnr                      # parse_tipnr (the loader-fixed roster)
import entity_resolution as er           # norm_name (the binder's normalizer)

from build_abp_surface import ABBREV_TO_SLUG   # the ONE ABP-abbrev -> scrape-slug map

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          os.path.expanduser("~/bible-db/bible.db"))
APPLY = "--apply" in sys.argv
BH = next((sys.argv[i + 1] for i, a in enumerate(sys.argv)
           if a == "--bh" and i + 1 < len(sys.argv)),
          os.path.expanduser("~/bible-db/bh_scrape.db"))


def _name_token(s):
    """A word's name label reduced to a bare lowercase token ('of Raamah,' -> 'raamah')."""
    s = re.sub(r"[^a-z' -]", " ", (s or "").lower())
    toks = [t for t in s.split() if t not in
            ("of", "the", "and", "to", "in", "for", "with", "a", "an", "o")]
    return toks[-1] if toks else ""


def main():
    print(f"{'[APPLY] ' if APPLY else '[DRY-RUN] '}build_pn_greek_identity -> {DB}\n")

    tipnr_lines = open(os.path.join(_HERE, "..", "tipnr", "TIPNR.txt"),
                       encoding="utf-8-sig").read().splitlines()
    lookup, _ = import_tipnr.parse_tipnr(tipnr_lines)

    # Entity -> its own Greek number, from the binder's parse (sub-records included —
    # import_tipnr's lookup deliberately carries main-line numbers only, which misses
    # the Greek sub-record numbers OT names carry, incl. the STEP-extended ones).
    # Rule: exactly ONE Greek base on the entity -> that's its Greek identity; two or
    # more -> no guess (wrong > missing), the word falls to the lemma-only state.
    ents = er.parse_tipnr(tipnr_lines)
    ent_g, multi_g = {}, 0
    for e in ents:
        gs = sorted(b for b in e["bases"] if b.startswith("G"))
        if len(gs) == 1:
            ent_g[e["uniq"]] = gs[0]
        elif len(gs) > 1:
            multi_g += 1
    print(f"entities with exactly one Greek number: {len(ent_g):,} "
          f"(multi-Greek entities, no guess: {multi_g:,})")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=10000")

    have_binding = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE name='pn_binding'").fetchone()[0]
    binds = {}
    if have_binding:
        # keyed exactly like the binder keys its rows: (book#, ch, vs, norm name);
        # value = the bound entity's uniq (the key into ent_g above).
        for r in conn.execute("SELECT book, chapter, verse, name, entity_uniq "
                              "FROM pn_binding WHERE render=1"):
            binds[(r["book"], r["chapter"], r["verse"], r["name"])] = r["entity_uniq"]
    print(f"pn_binding render rows loaded: {len(binds):,}"
          + ("" if have_binding else "  (table absent — layer 'tipnr' via lookup only)"))

    # The printed-Greek side table is the lemma fallback for name words — words.lemma
    # is mostly blank on proper nouns (the dry-run control that caught this: 26,867
    # 'none' rows on the first pass, 2026-07-24).
    have_surface = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE name='abp_surface'").fetchone()[0]
    surf_join = ("LEFT JOIN abp_surface s ON s.verse_id = w.verse_id "
                 "AND s.position = w.position") if have_surface else ""
    surf_col = "s.form" if have_surface else "NULL"
    words = conn.execute(f"""
        SELECT w.verse_id, w.position, w.strongs_base, w.lemma,
               {surf_col} AS surface_form,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               v.book, v.chapter, v.verse
        FROM words w JOIN verses v ON v.id = w.verse_id
        {surf_join}
        WHERE w.is_pn = 1
    """).fetchall()
    print(f"proper-noun words: {len(words):,}\n")

    # Printed-Greek source for name slots: the scrape (bh_words), where a NAME row has
    # a blank number and the Greek form in `greek` (abp_surface skips name slots — the
    # documented 30,126-slot gap; second dry-run control catch, 2026-07-24). Pairing is
    # by the NAME within the verse, never by position (the build splits slots, so
    # positions drift): exactly one name-slot row whose English carries the word's name
    # token, else REFUSE and count.
    scrape = {}
    if os.path.isfile(BH):
        bh = sqlite3.connect(f"file:{BH}?mode=ro", uri=True)
        for b, c, v, greek, english in bh.execute(
                "SELECT book, chapter, verse, greek, english FROM bh_words "
                "WHERE (strongs IS NULL OR strongs='') AND greek IS NOT NULL AND greek != ''"):
            scrape.setdefault((b, c, v), []).append((_name_token(english), greek))
        bh.close()
        print(f"scrape name-slot rows loaded: {sum(len(v) for v in scrape.values()):,} "
              f"across {len(scrape):,} verses")
    else:
        print(f"NOTE: scrape db not found at {BH} — lemma layer limited to words.lemma/abp_surface")

    def scrape_greek(book, ch, vs, label):
        tok = _name_token(label)
        if not tok:
            return None
        slug = ABBREV_TO_SLUG.get(book)
        if not slug:
            return None
        hits = [g for (t, g) in scrape.get((slug, ch, vs), []) if t == tok]
        return hits[0] if len(hits) == 1 else None     # multi or none -> refuse

    rows, split = [], {"abp-tag": 0, "tipnr": 0, "lemma-only": 0, "none": 0}
    scrape_used = scrape_refused = 0
    for w in words:
        base = w["strongs_base"] or ""
        heb = base if base.startswith("H") else None
        greek, source = None, None
        lemma = w["lemma"] or w["surface_form"]   # dictionary form, else printed Greek
        if base.startswith("G"):
            greek, source = base, "abp-tag"
        else:
            nm = er.norm_name(w["label"] or "")
            bk = er.book_num(w["book"])
            uniq = binds.get((bk, w["chapter"], w["verse"], nm)) if bk is not None else None
            if uniq and uniq in ent_g:
                greek, source = ent_g[uniq], "tipnr"
            else:
                ent = lookup.get(nm) if nm else None    # unbound word: the roster itself
                if ent and ent.get("g"):
                    greek, source = ent["g"], "tipnr"
                else:
                    if not lemma:
                        lemma = scrape_greek(w["book"], w["chapter"], w["verse"], w["label"])
                        if lemma:
                            scrape_used += 1
                        else:
                            scrape_refused += 1
                    if lemma:
                        source = "lemma-only"
                    else:
                        source = "none"       # no number, no lemma — counted, not hidden
        split[source] += 1
        rows.append((w["verse_id"], w["position"], greek, lemma, source, heb))

    print("identity split:")
    for k in ("abp-tag", "tipnr", "lemma-only", "none"):
        print(f"  {k:10} {split[k]:,}")
    print(f"  (lemma via scrape: {scrape_used:,} matched; {scrape_refused:,} refused "
          f"— no clean one-to-one name match in the verse; refused rows are the "
          f"'none' bucket's residue, visible, not guessed)")
    print()

    if not APPLY:
        print("Dry-run only — nothing written. Re-run with --apply.")
        return

    conn.execute("DROP TABLE IF EXISTS pn_greek_identity")
    conn.execute("""
        CREATE TABLE pn_greek_identity (
            verse_id      INTEGER NOT NULL,
            position      INTEGER NOT NULL,
            greek_strongs TEXT,      -- 'G1138' / 'G9827' / NULL (lemma-only or none)
            greek_lemma   TEXT,
            source        TEXT NOT NULL,  -- abp-tag | tipnr | lemma-only | none
            hebrew_base   TEXT,      -- the stage-1 stopgap number, frozen as cross-ref
            PRIMARY KEY (verse_id, position)
        )
    """)
    conn.executemany(
        "INSERT INTO pn_greek_identity VALUES (?,?,?,?,?,?)", rows)
    conn.execute("CREATE INDEX idx_pngi_greek ON pn_greek_identity(greek_strongs)")
    conn.execute("CREATE INDEX idx_pngi_heb ON pn_greek_identity(hebrew_base)")
    conn.commit()
    n = conn.execute("SELECT count(*) FROM pn_greek_identity").fetchone()[0]
    print(f"Wrote pn_greek_identity: {n:,} rows.")


if __name__ == "__main__":
    main()
