#!/usr/bin/env python3
"""R-2 stage 3 flip #1 (G2) locked test: Word study answers for Greek identities
behind READER_GREEK_FLIPS.

Drives the REAL lexicon routes (views_lexicon profile / books / verses) over a
fixture db whose pn_greek_identity and step_lexicon mirror the builders' actual
CREATE TABLE shapes (receipt-2 lesson). Locks:

  * switch OFF          -> a G9xxx profile 404s exactly as before (the OFF-proof)
  * switch OFF vs ON    -> a normal Greek word's profile payload byte-identical
                           (the union adds no rows for a word with no tipnr
                           identity rows)
  * switch ON, G9xxx    -> profile 200: lemma/translit/gloss from step_lexicon,
                           step flag true, corpus stays "abp" (tab-fallback fix:
                           never demoted to an empty KJV tab), ABP total = the
                           tipnr identity rows, verse list lists their verses
  * no-double-count     -> reviewer condition 2, tested not asserted: a planted
                           pathological word reachable BOTH ways (native
                           strongs_base = the G-number AND a tipnr identity row
                           at the same verse+position) counts ONCE
  * Hebrew branch       -> untouched: an H-number profile byte-identical OFF vs ON

Pure stdlib + on-disk temp SQLite (the routes open core.DB). Run:
  python tests/test_ws_greek_flips.py
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
                            strongs TEXT, is_pn INT, italic INT DEFAULT 0);
        CREATE TABLE lexicon (strongs TEXT, strongs_g TEXT, lemma TEXT,
                              translit TEXT, kjv_def TEXT, derivation TEXT,
                              strongs_def TEXT);
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

        INSERT INTO books VALUES ('Gen','Genesis',1,1), ('1Sa','1 Samuel',9,9),
                                 ('Mat','Matthew',40,40);
        INSERT INTO verses VALUES
            (1,'1Sa',15,8,'And he seized Agag king of Amalek alive.'),
            (2,'1Sa',15,9,'And Saul spared Agag.'),
            (3,'Mat',1,6,'And Jesse begot David the king.'),
            (4,'Gen',11,26,'And Terah lived seventy years.');
        -- G9826 (Agag, STEP-extended): two tipnr-backfilled words, Hebrew-keyed
        INSERT INTO words (id, verse_id, position, english, english_head,
                           strongs_base, strongs, is_pn) VALUES
            (1,1,3,'Agag','Agag','H90','*',1),
            (2,2,4,'Agag','Agag','H90','*',1),
        -- G1138 (David): one NATIVE Greek word (Mat) + one tipnr Hebrew word (Gen slot
        -- reused as a stand-in OT occurrence)
            (3,3,5,'David','David','G1138','1138',1),
            (4,4,2,'Terah','Terah','H8646','*',1),
        -- normal Greek word, no identity anywhere
            (5,1,5,'seized','seized','G4815','4815',0);
        INSERT INTO lexicon VALUES
            ('1138','G1138','Δαυίδ','dauid','David','','David the king'),
            ('4815','G4815','συλλαμβάνω','sullambanō','seize','','to seize');
        INSERT INTO bdb VALUES ('H90','אֲגַג','Agag','Agag, king of Amalek');
        INSERT INTO step_lexicon VALUES ('G9826G', 9826, 'Ἀγάγ', 'agag', 'Agag');
        INSERT INTO pn_greek_identity VALUES
            (1, 3, 'G9826', NULL, 'tipnr', 'H90'),
            (2, 4, 'G9826', NULL, 'tipnr', 'H90'),
        -- David: the Mat word is ALSO given a pathological tipnr row (reviewer
        -- condition 2: reachable both ways must count ONCE), plus a genuine
        -- tipnr row on the Hebrew-keyed Gen word.
            (3, 5, 'G1138', NULL, 'tipnr', 'H1732'),
            (4, 2, 'G1138', NULL, 'tipnr', 'H1732');
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
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(views_lexicon.bp)
    client = app.test_client()

    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "ws_flips.db")
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

        # ---- switch OFF (the OFF-proof contract) ----
        core.READER_GREEK_FLIPS = False
        r = client.get("/api/lexicon/profile/G9826")
        check("OFF: G9xxx profile 404s as before", r.status_code, 404)
        off_norm = client.get("/api/lexicon/profile/G4815").get_data(as_text=True)
        off_heb = client.get("/api/lexicon/profile/H90").get_data(as_text=True)

        # ---- switch ON ----
        core.READER_GREEK_FLIPS = True
        check("ON: normal Greek word byte-identical to OFF",
              client.get("/api/lexicon/profile/G4815").get_data(as_text=True), off_norm)
        check("ON: Hebrew branch byte-identical to OFF",
              client.get("/api/lexicon/profile/H90").get_data(as_text=True), off_heb)

        r = client.get("/api/lexicon/profile/G9826")
        check("ON: G9xxx profile answers", r.status_code, 200)
        p = json.loads(r.get_data(as_text=True))
        check("ON: lemma from step_lexicon", p.get("lemma"), "Ἀγάγ")
        check("ON: translit from step_lexicon", p.get("translit"), "agag")
        check("ON: gloss from step_lexicon", p.get("definition"), "Agag")
        check("ON: STEP flag set", p.get("step"), True)
        check("ON: corpus stays abp (tab-fallback fix)", p.get("corpus"), "abp")
        check("ON: ABP total = the tipnr identity rows", p.get("total"), 2)
        check("ON: has_abp true via the union", p.get("has_abp"), True)
        check("ON: renders-as from the identity words (folded lowercase)",
              [g["gloss"] for g in p.get("abp_glosses", [])], ["agag"])
        check("ON: default verse list = the identity verses",
              [(v["book"], v["chapter"], v["verse"]) for v in p.get("default_verses", [])],
              [("1Sa", 15, 8), ("1Sa", 15, 9)])

        # no-double-count (reviewer condition 2): David reachable both ways at
        # Mat 1:6 (native G1138 word + planted tipnr row) counts ONCE there;
        # total = 1 native + 1 genuine tipnr = 2, never 3.
        p = json.loads(client.get("/api/lexicon/profile/G1138").get_data(as_text=True))
        check("ON: both-routes word counts once (total 2, not 3)", p.get("total"), 2)
        check("ON: native word not STEP-tagged (field absent)", "step" in p, False)
        check("ON: native lemma still from main lexicon", p.get("lemma"), "Δαυίδ")

        # books endpoint rides the same union
        b = json.loads(client.get("/api/lexicon/books/G9826?corpus=abp").get_data(as_text=True))
        check("ON: books endpoint sees the identity rows",
              {x["book"]: x["count"] for x in b.get("books", [])} if isinstance(b, dict) else b,
              {"1Sa": 2})

        # per-book verse list rides the same union
        r = client.get("/api/lexicon/verses/G9826/1Sa?corpus=abp")
        check("ON: per-book verse list answers", r.status_code, 200)
        v = json.loads(r.get_data(as_text=True))
        vl = v.get("verses", v) if isinstance(v, dict) else v
        check("ON: per-book verse list count", len(vl), 2)
    finally:
        core.DB, core.READER_GREEK_FLIPS = old_db, old_flag

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll Word-study greek-flips checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
