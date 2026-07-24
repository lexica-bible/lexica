#!/usr/bin/env python3
"""R-2 stage 3 flip #2 locked test: Greek-keyed reader tags behind READER_GREEK_FLIPS.

Drives the REAL library feed routes (views_library verse_words + chapter_text) over a
fixture db whose pn_greek_identity mirrors the builder's actual CREATE TABLE
(scripts/build_pn_greek_identity.py:201 — the receipt-2 lesson: fixture = the
importer's shape, never re-derived). Locks:

  * switch OFF (default)      -> both feed payloads BYTE-IDENTICAL with and without
                                 pn_greek_identity present (the G1 OFF-proof contract)
  * switch OFF default state  -> core.READER_GREEK_FLIPS is False when env unset
  * switch ON, backfilled PN  -> word carries g_id {strongs: 'G9826', src} (Agag class)
  * switch ON, real inline G  -> NO g_id override effect target; the word still serves
                                 its own number fields untouched (C2a: never re-derived
                                 — asserted at feed level: g_id present but tag decision
                                 is frontend; feed must still carry strongs/strongs_base
                                 unchanged)
  * switch ON, lemma-only     -> g_id present with strongs '' (frontend hides the tag)
  * switch ON, 'none' bucket  -> NO g_id field (card/tag unchanged)
  * switch ON, table missing  -> behaves exactly as OFF (deploy-safe)

Pure stdlib + on-disk temp SQLite (the routes open core.DB). Run:
  python tests/test_reader_greek_flips.py
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_db(path, with_identity=True):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT,
                             verse INT, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            english TEXT, english_head TEXT, greek_pos TEXT,
                            bracket_id INT, italic INT, italic_words TEXT,
                            smcap_words TEXT, strongs_base TEXT, strongs TEXT,
                            is_pn INT, morph TEXT);
        CREATE TABLE lexicon (strongs_g TEXT PRIMARY KEY, lemma TEXT, translit TEXT,
                              kjv_def TEXT, strongs_def TEXT, derivation TEXT);
        CREATE TABLE tipnr (strongs TEXT PRIMARY KEY, entity_type TEXT, entity_types TEXT);
        CREATE TABLE pericopes (book TEXT, chapter INT, verse INT, heading TEXT);

        INSERT INTO verses VALUES (1,'1Sa',15,8,'And he seized Agag king of Amalek alive.');
        -- pos 2: backfilled PN (strongs='*', Hebrew base) -> Agag class
        -- pos 4: real inline G-number word (C2a: never re-derived)
        -- pos 6: lemma-only PN ('*' base after refusal is NOT this class; this row
        --        keeps its Hebrew base like live lemma-only rows do)
        -- pos 8: 'none'-bucket PN
        INSERT INTO words VALUES
            (1,1,2,'Agag','Agag','','',0,'','','H90','*',1,''),
            (2,1,4,'seized','seized','','',0,'','','G4815','4815',0,'V'),
            (3,1,6,'Hazo','Hazo','','',0,'','','H2375','*',1,''),
            (4,1,8,'Mystery','Mystery','','',0,'','','H9999','*',1,'');
        INSERT INTO lexicon VALUES ('G4815','συλλαμβάνω','sullambanō','seize','','');
    """)
    if with_identity:
        # REAL shape: scripts/build_pn_greek_identity.py CREATE TABLE (verified).
        c.executescript("""
            CREATE TABLE pn_greek_identity (
                verse_id      INTEGER NOT NULL,
                position      INTEGER NOT NULL,
                greek_strongs TEXT,
                greek_lemma   TEXT,
                source        TEXT NOT NULL,
                hebrew_base   TEXT,
                PRIMARY KEY (verse_id, position)
            );
            INSERT INTO pn_greek_identity VALUES
                (1, 2, 'G9826', NULL,      'tipnr',      'H90'),
                (1, 4, 'G4815', NULL,      'abp-tag',    NULL),
                (1, 6, NULL,    'Ἀζαύ',    'lemma-only', 'H2375'),
                (1, 8, NULL,    NULL,      'none',       'H9999');
        """)
    c.commit()
    c.close()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    import core
    import views_library
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(views_library.bp)
    client = app.test_client()

    tmp = tempfile.mkdtemp()
    db_with = os.path.join(tmp, "with_identity.db")
    db_without = os.path.join(tmp, "without_identity.db")
    _make_db(db_with, with_identity=True)
    _make_db(db_without, with_identity=False)

    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    def fetch(path):
        r = client.get(path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        return r.get_data(as_text=True)

    old_db, old_flag = core.DB, core.READER_GREEK_FLIPS
    try:
        # ---- switch OFF (the G1 OFF-proof contract) ----
        core.READER_GREEK_FLIPS = False
        if os.environ.get("READER_GREEK_FLIPS", "") != "1":
            check("switch defaults OFF", core.READER_GREEK_FLIPS, False)

        core.DB = db_with
        off_verse = fetch("/api/verse-words/1Sa/15/8")
        off_chap = fetch("/api/chapter/1Sa/15")
        core.DB = db_without
        check("OFF: verse feed byte-identical with/without identity table",
              off_verse, fetch("/api/verse-words/1Sa/15/8"))
        check("OFF: chapter feed byte-identical with/without identity table",
              off_chap, fetch("/api/chapter/1Sa/15"))
        check("OFF: no g_id anywhere in the payload", "g_id" in off_chap, False)

        # ---- switch ON ----
        core.READER_GREEK_FLIPS = True
        core.DB = db_with
        chap = json.loads(fetch("/api/chapter/1Sa/15"))
        words = {w["position"]: w for w in chap[0]["words"]}

        check("ON: backfilled PN carries Greek identity (Agag class)",
              words[2].get("g_id"), {"strongs": "G9826", "src": "tipnr"})
        check("ON: backfilled PN keeps its stored fields (cross-ref stays findable)",
              (words[2]["strongs_base"], words[2]["strongs"]), ("H90", "*"))
        check("ON: real inline G-number word untouched in its number fields (C2a)",
              (words[4]["strongs_base"], words[4]["strongs"]), ("G4815", "4815"))
        check("ON: lemma-only serves g_id with EMPTY number (tag hides, Q3)",
              words[6].get("g_id"), {"strongs": "", "src": "lemma-only"})
        check("ON: 'none' bucket serves NO g_id (unchanged)",
              "g_id" in words[8], False)

        verse = json.loads(fetch("/api/verse-words/1Sa/15/8"))
        vwords = {w["position"]: w for w in verse["words"]}
        check("ON: verse feed serves the same identity field",
              vwords[2].get("g_id"), {"strongs": "G9826", "src": "tipnr"})

        # ---- switch ON but identity table absent: behaves as OFF (deploy-safe) ----
        core.DB = db_without
        check("ON + table missing: chapter feed byte-identical to OFF",
              fetch("/api/chapter/1Sa/15"), off_chap)
    finally:
        core.DB, core.READER_GREEK_FLIPS = old_db, old_flag

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll reader-greek-flips feed checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
