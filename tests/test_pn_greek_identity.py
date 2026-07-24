#!/usr/bin/env python3
"""R-2 stage 2 locked test: the Greek-identity helper behind the reader flip.

Locks the contract of views_metav._greek_identity_payload (the ONE code path the
flipped ABP proper-noun card is fed from) on an in-memory fixture db:

  * numbered identity, lexicon-carried  -> lemma/translit from lexicon, step=False,
    count by the Greek number over pn_greek_identity (S2-Q4)
  * numbered identity, STEP-extended    -> lemma from step_lexicon, step=True (S2-Q2)
  * lemma-only                          -> no number, count by the stored form (S2-Q3/Q4)
  * 'none' bucket                       -> None (control C4: card must not change)
  * tables absent                       -> None (deploy-safe)
  * hebrew_base                         -> carried with its OWN words-table count
  * the switch defaults OFF (READER_GREEK_IDENTITY unset -> False)

Pure stdlib + in-memory SQLite. Run:  python tests/test_pn_greek_identity.py
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
        -- REAL shape (import_step_lexicon.py, verified on PA 2026-07-24): estrong is
        -- the padded TBESG text key, base is a plain NUMBER. The first fixture had
        -- base as text and passed while live never matched — a replica isn't the
        -- mechanism; this fixture must mirror the importer's CREATE TABLE exactly.
        CREATE TABLE step_lexicon (estrong TEXT PRIMARY KEY, base INTEGER,
                                   lemma TEXT, translit TEXT, gloss TEXT);
        CREATE TABLE pn_greek_identity (
            verse_id INT, position INT, greek_strongs TEXT, greek_lemma TEXT,
            source TEXT, hebrew_base TEXT, PRIMARY KEY (verse_id, position));

        INSERT INTO verses VALUES (1,'Mat',1,6), (2,'Gen',11,26), (3,'1Ch',1,1);
        -- David: numbered, lexicon-carried, Hebrew cross-ref H1732 (control C1)
        INSERT INTO lexicon VALUES ('G1138','Δαυίδ','dauid');
        INSERT INTO pn_greek_identity VALUES
            (1, 3, 'G1138', NULL, 'abp-tag', 'H1732'),   -- the clicked word
            (2, 5, 'G1138', NULL, 'tipnr',   'H1732'),   -- second occurrence -> count 2
        -- STEP-extended: number only step_lexicon carries (control C2)
            (2, 7, 'G9901', NULL, 'tipnr',   'H8646'),
        -- lemma-only: printed form, no number in any scheme (control C3)
            (3, 2, NULL, 'Ἰωβήλ', 'lemma-only', NULL),
            (3, 4, NULL, 'Ἰωβήλ', 'lemma-only', NULL),
        -- none bucket (control C4)
            (3, 6, NULL, NULL, 'none', NULL);
        INSERT INTO step_lexicon VALUES ('G9901', 9901, 'Θάρα','thara','Terah');
        -- low padded number: identity 'G2' must reach estrong 'G0002' via base=2
        INSERT INTO step_lexicon VALUES ('G0002', 2, 'Ἀαρών','aarōn','Aaron');
        INSERT INTO pn_greek_identity VALUES (3, 8, 'G2', NULL, 'tipnr', 'H175');
        -- ABP words carrying the Hebrew stopgap number (the cross-ref's own count)
        INSERT INTO words VALUES (1,1,3,'H1732','David'), (2,2,5,'H1732','David'),
                                 (3,2,9,'H1732',''), (4,2,7,'H8646','Terah');
    """)
    return c


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    from views_metav import _greek_identity_payload
    import core

    c = _fixture()
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    # numbered, lexicon-carried (C1 shape)
    p = _greek_identity_payload(c, 1, 3)
    check("numbered: greek number", p["greek_strongs"], "G1138")
    check("numbered: lemma from lexicon", p["lemma"], "Δαυίδ")
    check("numbered: translit from lexicon", p["translit"], "dauid")
    check("numbered: not STEP", p["step"], False)
    check("numbered: count by Greek number (2 rows)", p["greek_count"], 2)
    check("numbered: hebrew cross-ref carried", p["hebrew_base"], "H1732")
    check("numbered: hebrew count skips empty-English rows", p["hebrew_count"], 2)

    # STEP-extended (C2 shape)
    p = _greek_identity_payload(c, 2, 7)
    check("step: greek number", p["greek_strongs"], "G9901")
    check("step: lemma from step_lexicon", p["lemma"], "Θάρα")
    check("step: STEP flag set", p["step"], True)
    check("step: count by Greek number", p["greek_count"], 1)

    # padded low number: the receipt-2 catch — 'G2' must reach estrong 'G0002'
    # through the NUMBER column (a text join never matches the padded key)
    p = _greek_identity_payload(c, 3, 8)
    check("padded: lemma via numeric base join", p["lemma"], "Ἀαρών")
    check("padded: STEP flag set", p["step"], True)

    # lemma-only (C3 shape)
    p = _greek_identity_payload(c, 3, 2)
    check("lemma-only: no number", p["greek_strongs"], None)
    check("lemma-only: stored form", p["lemma"], "Ἰωβήλ")
    check("lemma-only: count by the form (2 rows)", p["greek_count"], 2)
    check("lemma-only: no fabricated STEP tag", p["step"], False)

    # none bucket (C4) + misses
    check("none bucket -> None (card unchanged)", _greek_identity_payload(c, 3, 6), None)
    check("no row -> None", _greek_identity_payload(c, 1, 99), None)

    # tables absent -> None (deploy-safe)
    bare = sqlite3.connect(":memory:")
    bare.row_factory = sqlite3.Row
    bare.executescript("CREATE TABLE verses (id INTEGER PRIMARY KEY);")
    check("identity table absent -> None", _greek_identity_payload(bare, 1, 1), None)

    # the switch defaults OFF (only assert when the env doesn't set it)
    if os.environ.get("READER_GREEK_IDENTITY", "") != "1":
        check("switch defaults OFF", core.READER_GREEK_IDENTITY, False)

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll pn_greek_identity helper checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
