#!/usr/bin/env python3
"""R-2 candidate 3 (Hebrew retirement) — locked test for the DORMANT serving
repoints (docs/PLAN_r2_stage3.md, candidate-3 charter, code-first run shape).

Two phases over one fixture db whose tables mirror the builders' real CREATE
shapes (the receipt-2 lesson):

  PHASE 1 — pn_hebrew_xref ABSENT (today's live state):
    * every candidate-3 helper returns today's exact SQL (byte-level dormancy)
    * a G9xxx /word-study profile still 404s with the flip switch off
    * the reader verse feed serves the pre-retirement Hebrew-keyed word

  PHASE 2 — retirement simulated (xref table created + words rewritten per the
  charter's row-class table: tipnr → Greek number, lemma-only → '*',
  none → Hebrew KEPT):
    * reader feed: G9826 word gets lemma/translit/gloss from step_lexicon and
      KEEPS its person badge (tipnr join through the cross-ref home)
    * 'none'-class word: badge unchanged (direct Hebrew key still matches)
    * H-keyed ABP counts (metav strongs-count?by=base + the Word-study H
      profile's ABP corpus) find the moved rows via the xref union — the
      S2-Q4 unfindability bar; 'none' rows reachable both ways count ONCE
    * G9xxx Word-study profile answers even with READER_GREEK_FLIPS OFF (the
      G5 switch-semantics change: post-retirement, OFF no longer means
      Hebrew-everywhere)
    * SEO _word_profile serves /word/G9826 from step_lexicon (C3-Q3)

Pure stdlib + on-disk temp SQLite. Run:  python tests/test_c3_dormant.py
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE books (abbrev TEXT, name TEXT, sort_order INT, id INT);
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT,
                             verse INT, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            english TEXT, english_head TEXT, strongs_base TEXT,
                            strongs TEXT, is_pn INT, italic INT DEFAULT 0,
                            italic_words TEXT, greek_pos TEXT, bracket_id INT,
                            morph TEXT, smcap_words TEXT);
        CREATE TABLE lexicon (strongs TEXT, strongs_g TEXT, lemma TEXT,
                              translit TEXT, kjv_def TEXT, derivation TEXT,
                              strongs_def TEXT);
        CREATE TABLE tipnr (strongs TEXT, entity_type TEXT, entity_types TEXT);
        CREATE TABLE kjv_strongs (strongs_id TEXT, word_id INT);
        CREATE TABLE kjv_words (word_id INT, book_id INT, chapter INT,
                                verse_num INT, word TEXT);
        CREATE TABLE bdb (strongs_id TEXT, lemma TEXT, xlit TEXT, description TEXT);
        -- REAL shapes (import_step_lexicon.py / build_pn_greek_identity.py):
        CREATE TABLE step_lexicon (estrong TEXT PRIMARY KEY, base INTEGER,
                                   lemma TEXT, translit TEXT, gloss TEXT);
        CREATE TABLE pn_greek_identity (
            verse_id      INTEGER NOT NULL,
            position      INTEGER NOT NULL,
            greek_strongs TEXT,
            greek_lemma   TEXT,
            source        TEXT NOT NULL,
            hebrew_base   TEXT,
            PRIMARY KEY (verse_id, position)
        );

        INSERT INTO books VALUES ('1Sa','1 Samuel',9,9), ('Mat','Matthew',40,40);
        INSERT INTO verses VALUES
            (1,'1Sa',15,8,'And he seized Agag king of Amalek alive.'),
            (2,'1Sa',15,7,'And Saul struck from Havilah unto Shur.'),
            (3,'1Sa',15,6,'And Saul said to the Kenite, Depart.'),
            (4,'Mat',1,6,'And Jesse begot David the king.');
        -- Pre-retirement state (today's live rows):
        --   Agag    tipnr class      H90   -> becomes G9826
        --   Havilah lemma-only class H2341 -> becomes '*'
        --   Kenite  none class       H7017 -> KEPT (C3-Q1 exception)
        --   David   native NT Greek  G1138 -> untouched
        INSERT INTO words (id, verse_id, position, english, english_head,
                           strongs_base, strongs, is_pn) VALUES
            (1,1,3,'Agag','Agag','H90','*',1),
            (2,2,4,'Havilah','Havilah','H2341','*',1),
            (3,3,5,'Kenite','Kenite','H7017','*',1),
            (4,4,5,'David','David','G1138','1138',1),
            (5,1,5,'seized','seized','G4815','4815',0);
        INSERT INTO lexicon VALUES
            ('1138','G1138','Δαυίδ','dauid','David','','David the king'),
            ('4815','G4815','συλλαμβάνω','sullambanō','seize','','to seize');
        INSERT INTO tipnr VALUES ('H90','person','person'),
                                 ('H2341','place','place'),
                                 ('H7017','person','person');
        INSERT INTO bdb VALUES ('H90','אֲגַג','Agag','Agag, king of Amalek');
        INSERT INTO step_lexicon VALUES ('G9826G', 9826, 'Ἀγάγ', 'agag', 'Agag');
        INSERT INTO pn_greek_identity VALUES
            (1, 3, 'G9826', NULL,      'tipnr',      'H90'),
            (2, 4, NULL,    'Εὐιλάτ',  'lemma-only', 'H2341'),
            (3, 5, NULL,    NULL,      'none',       'H7017');
    """)
    c.commit()
    c.close()


def _retire(path):
    """Simulate the rebuild's write set: create the cross-ref home (the wave's
    reference DDL — the rebuild lane must land this exact shape) and rewrite
    words.strongs_base per the charter's row-class table."""
    c = sqlite3.connect(path)
    c.executescript("""
        -- Q2 cross-ref home (reviewer-ruled shape, JP checkpoint pending at the
        -- rebuild): one row per PN word; hebrew_base NULL (declared, never '')
        -- for always-Greek abp-tag rows; class 'none' IS the machine-visible
        -- kept-Hebrew exception (C3-Q1) — retired by the future
        -- gentilic/people-class Greek backfill candidate.
        CREATE TABLE pn_hebrew_xref (
            verse_id    INTEGER NOT NULL,
            position    INTEGER NOT NULL,
            hebrew_base TEXT,
            class       TEXT NOT NULL,
            PRIMARY KEY (verse_id, position)
        );
        CREATE INDEX idx_pnx_heb ON pn_hebrew_xref(hebrew_base);
        INSERT INTO pn_hebrew_xref VALUES
            (1, 3, 'H90',   'tipnr'),
            (2, 4, 'H2341', 'lemma-only'),
            (3, 5, 'H7017', 'none');
        UPDATE words SET strongs_base = 'G9826' WHERE id = 1;  -- tipnr class
        UPDATE words SET strongs_base = '*'     WHERE id = 2;  -- lemma-only (C3-Q2)
        -- id 3 (none class) keeps H7017; id 4/5 untouched.
    """)
    c.commit()
    c.close()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    import core
    import views_lexicon
    import views_library
    import views_metav
    import views_seo
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(views_lexicon.bp)
    app.register_blueprint(views_library.bp)
    app.register_blueprint(views_metav.bp)
    client = app.test_client()

    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "c3_dormant.db")
    _make_db(dbp)

    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    old_db, old_flag = core.DB, core.READER_GREEK_FLIPS
    try:
        core.DB = dbp
        core.READER_GREEK_FLIPS = False

        conn = sqlite3.connect(dbp)
        # ---- PHASE 1: table absent -> byte-level dormancy ----
        check("P1: pn_xref_ready false", core.pn_xref_ready(conn), False)
        check("P1: step_lemma_cols passes inputs through",
              core.step_lemma_cols(conn, "l.lemma", "l.translit", "g"),
              ("l.lemma", "l.translit", "g", ""))
        check("P1: h_abp_predicate is the plain match",
              core.h_abp_predicate(conn, "H90"),
              ("w.strongs_base = ?", ["H90"]))
        check("P1: pn_xref_parts is no join + today's key",
              core.pn_xref_parts(conn), ("", "w.strongs_base"))
        conn.close()

        r = client.get("/api/lexicon/profile/G9826")
        check("P1: G9xxx profile 404s (flips OFF, no xref)", r.status_code, 404)
        w = json.loads(client.get("/api/verse-words/1Sa/15/8").get_data(as_text=True))
        agag = next(x for x in w["words"] if x["english"] == "Agag")
        check("P1: reader word still Hebrew-keyed", agag["strongs_base"], "H90")
        check("P1: reader badge via direct key", agag["pn_type"], "person")
        n = json.loads(client.get("/api/strongs-count/H90?by=base").get_data(as_text=True))
        check("P1: H count = the pre-retirement row", n["count"], 1)

        # ---- PHASE 2: retirement lands -> every repoint fires ----
        _retire(dbp)

        w = json.loads(client.get("/api/verse-words/1Sa/15/8").get_data(as_text=True))
        agag = next(x for x in w["words"] if x["english"] == "Agag")
        check("P2: reader word Greek-keyed", agag["strongs_base"], "G9826")
        check("P2: lemma from step_lexicon", agag["lemma"], "Ἀγάγ")
        check("P2: translit from step_lexicon", agag["translit"], "agag")
        check("P2: gloss falls through to step_lexicon", agag["kjv_def"], "Agag")
        check("P2: badge survives via the cross-ref home", agag["pn_type"], "person")
        seized = next(x for x in w["words"] if x["english"] == "seized")
        check("P2: normal word untouched", (seized["strongs_base"], seized["lemma"]),
              ("G4815", "συλλαμβάνω"))

        w = json.loads(client.get("/api/verse-words/1Sa/15/6").get_data(as_text=True))
        ken = next(x for x in w["words"] if x["english"] == "Kenite")
        check("P2: 'none' class keeps Hebrew (C3-Q1)", ken["strongs_base"], "H7017")
        check("P2: 'none' badge via direct key", ken["pn_type"], "person")

        n = json.loads(client.get("/api/strongs-count/H90?by=base").get_data(as_text=True))
        check("P2: moved H row found via xref union (S2-Q4)", n["count"], 1)
        n = json.loads(client.get("/api/strongs-count/H7017?by=base").get_data(as_text=True))
        check("P2: both-homes 'none' row counts ONCE", n["count"], 1)

        p = json.loads(client.get("/api/lexicon/profile/H90?corpus=abp").get_data(as_text=True))
        check("P2: H Word-study ABP total via xref union", p.get("total"), 1)

        r = client.get("/api/lexicon/profile/G9826")
        check("P2: G9xxx profile answers with flips OFF (G5 semantics)",
              r.status_code, 200)
        p = json.loads(r.get_data(as_text=True))
        check("P2: G9xxx total = its native rewritten row", p.get("total"), 1)
        check("P2: G9xxx lemma from step_lexicon", p.get("lemma"), "Ἀγάγ")
        core.READER_GREEK_FLIPS = True
        p = json.loads(client.get("/api/lexicon/profile/G9826").get_data(as_text=True))
        check("P2: flips ON, no double count (old G-union retired)", p.get("total"), 1)
        core.READER_GREEK_FLIPS = False

        prof = views_seo._word_profile("G9826")
        check("P2: SEO /word profile serves G9xxx (C3-Q3)",
              (prof or {}).get("lemma"), "Ἀγάγ")
        check("P2: SEO ABP count for G9xxx", (prof or {}).get("total"), 1)
    finally:
        core.DB, core.READER_GREEK_FLIPS = old_db, old_flag

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll candidate-3 dormant-repoint checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
