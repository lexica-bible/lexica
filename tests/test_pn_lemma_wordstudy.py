#!/usr/bin/env python3
"""Lane #3 locked test: the lemma-keyed Word-study entry for NUMBERLESS
proper-noun identities (the PN:<form> key, TICKET_lemma_word_study.md).

Locks views_lexicon._pn_lemma_rows — the one derivation the PN: profile,
verse list, and book counts are all built from — on a real-shape fixture:

  * PARITY (the closing receipt): the list's length equals the CARD's static
    count for the same form (views_metav._greek_identity_payload, lemma-only
    branch) — two production code paths, one fixture, must agree.
  * a NUMBERED identity spelled the same does NOT leak into the list
  * canonical book order (Gen before Mat regardless of row order)
  * testament filter narrows correctly
  * unknown form -> empty; pn_greek_identity absent -> empty (deploy-safe)

Pure stdlib + in-memory SQLite. Run:  python tests/test_pn_lemma_wordstudy.py
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _fixture() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            strongs_base TEXT, english TEXT);
        CREATE TABLE lexicon (strongs_g TEXT PRIMARY KEY, lemma TEXT, translit TEXT);
        CREATE TABLE step_lexicon (estrong TEXT PRIMARY KEY, base INTEGER,
                                   lemma TEXT, translit TEXT, gloss TEXT);
        CREATE TABLE pn_greek_identity (
            verse_id INT, position INT, greek_strongs TEXT, greek_lemma TEXT,
            source TEXT, hebrew_base TEXT, PRIMARY KEY (verse_id, position));

        -- Row order deliberately NON-canonical (Mat verse first) to prove the
        -- canonical ORDER BY, not insertion order.
        INSERT INTO verses VALUES (1,'Mat',1,2), (2,'Gen',5,12), (3,'Gen',5,13), (4,'1Ch',1,2);
        INSERT INTO pn_greek_identity VALUES
            (1, 4, NULL, 'Καϊναν', 'lemma-only', NULL),
            (2, 1, NULL, 'Καϊναν', 'lemma-only', NULL),
            (3, 1, NULL, 'Καϊναν', 'lemma-only', NULL),
            (4, 2, NULL, 'Καϊναν', 'lemma-only', NULL),
        -- a NUMBERED identity that happens to carry the same stored lemma —
        -- must NOT join the numberless list (it has its own number-keyed page)
            (4, 5, 'G2536', 'Καϊναν', 'tipnr', NULL),
        -- a different form, one occurrence
            (2, 6, NULL, 'Μαλελεήλ', 'lemma-only', NULL);
    """)
    return c


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    from views_lexicon import _pn_lemma_rows
    from views_metav import _greek_identity_payload

    c = _fixture()
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    rows = _pn_lemma_rows(c, "Καϊναν")
    check("numberless occurrences only (numbered same-lemma row excluded)",
          len(rows), 4)
    check("canonical order: Gen rows lead, then 1Ch, then Mat",
          [r["book"] for r in rows], ["Gen", "Gen", "1Ch", "Mat"])

    # PARITY — the closing receipt in test form: the Word-study list length must
    # equal the CARD's static count, both computed by production code.
    card = _greek_identity_payload(c, 2, 1)   # the Gen 5:12 lemma-only slot
    check("card payload is the lemma-only state", card and card["greek_strongs"], None)
    check("PARITY: list length == card count", len(rows), card["greek_count"])

    check("testament filter: OT only", len(_pn_lemma_rows(c, "Καϊναν", "ot")), 3)
    check("testament filter: NT only", len(_pn_lemma_rows(c, "Καϊναν", "nt")), 1)
    check("single-occurrence form", len(_pn_lemma_rows(c, "Μαλελεήλ")), 1)
    check("unknown form -> empty", _pn_lemma_rows(c, "Ζζζ"), [])

    bare = sqlite3.connect(":memory:")
    bare.row_factory = sqlite3.Row
    check("pn_greek_identity absent -> empty (deploy-safe)",
          _pn_lemma_rows(bare, "Καϊναν"), [])

    if fails:
        print("\n".join(fails))
        return 1
    print("\nAll lemma-Word-study checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
