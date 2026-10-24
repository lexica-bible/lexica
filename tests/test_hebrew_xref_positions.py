#!/usr/bin/env python3
"""Locked test — Hebrew-number ABP rows light from the same filter that listed them
(TODO follow-up (f), JP-approved 2026-10-24: the `positions` field).

The defect: for an H-number, the ABP verse list finds words two ways (the word still
carries the number, OR pn_hebrew_xref links that word slot to it). The verse row then
lit a word only by matching the number on the word itself, so the xref-only words
(stored number '*') were listed but never lit (H1908 Hadad: 45 words listed, 6 lit).

The fix: when the Hebrew cross-ref part of the filter is in use, each verse carries
`positions` — every word slot the SAME filter matched in that verse. Locks:

  * UNLIT CASE FIRST (audit-tools-must-fail): a verse reached ONLY via the xref
    (Gen 25:15 shape) carries its slot.
  * a verse with one numbered word AND one xref-only word (1Ki 11:21 shape) carries BOTH
  * a verse with two xref-only words (1Ki 11:17 shape) carries BOTH — one row, not two
  * a non-hit word in the same verse is never listed (positions come from the filter)
  * the verse LIST itself is unchanged (same verses, same order)
  * both lists: All books (incl. the profile's default list) and one book
  * the rendering chip (?gloss) keeps the positions on the verses it keeps
  * Greek numbers are untouched: no `positions` field on a G list

Pure stdlib + on-disk temp SQLite (the routes open core.DB). Run:
  python tests/test_hebrew_xref_positions.py
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
        -- REAL shape (scripts/retire_hebrew_identity.py DDL):
        CREATE TABLE pn_hebrew_xref (
            verse_id    INTEGER NOT NULL,
            position    INTEGER NOT NULL,
            hebrew_base TEXT,
            class       TEXT NOT NULL,
            PRIMARY KEY (verse_id, position)
        );

        INSERT INTO books VALUES ('Gen','Genesis',1,1), ('1Ki','1 Kings',11,11),
                                 ('Mat','Matthew',40,40);
        INSERT INTO verses VALUES
            (1,'Gen',25,15,'Hadar, and Tema'),
            (2,'1Ki',11,17,'And Hadad fled ... Hadad'),
            (3,'1Ki',11,21,'And Hadad heard ... Hadad'),
            (4,'Mat',4,15,'land of Zebulun ... Galilee');
        INSERT INTO words (id, verse_id, position, english, english_head,
                           strongs_base, strongs, is_pn) VALUES
        -- Gen 25:15: xref-only (retired, lemma-only class) — the UNLIT case
            (1, 1, 1, 'Hadar,', 'Hadar', '*', '*', 1),
            (2, 1, 3, 'Tema', 'Tema', 'G9999', '9999', 1),
        -- 1Ki 11:17: TWO xref-only words in one verse
            (3, 2, 2, 'Hadad,', 'Hadad', '*', '*', 1),
            (4, 2, 19, 'Hadad', 'Hadad', '*', '*', 1),
        -- 1Ki 11:21: one xref-only word + one word still carrying H1908 ('none' class),
        -- plus a non-hit word that must never be listed
            (5, 3, 1, 'Hadad', 'Hadad', '*', '*', 1),
            (6, 3, 5, 'heard', 'heard', 'G191', '191', 0),
            (7, 3, 22, 'Hadad', 'Hadad', 'H1908', '*', 1),
        -- Greek control
            (8, 4, 3, 'Galilee', 'Galilee', 'G1056', '1056', 1);
        INSERT INTO pn_hebrew_xref VALUES
            (1, 1, 'H1908', 'lemma-only'),
            (2, 2, 'H1908', 'lemma-only'),
            (2, 19, 'H1908', 'lemma-only'),
            (3, 1, 'H1908', 'lemma-only'),
            (3, 22, 'H1908', 'none'),
            (1, 3, NULL, 'abp-tag');
        INSERT INTO lexicon VALUES
            ('1056','G1056','Γαλιλαία','galilaia','Galilee','','Galilee');
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
    dbp = os.path.join(tmp, "heb_xref_positions.db")
    _make_db(dbp)

    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    def get(url):
        r = client.get(url)
        if r.status_code != 200:
            return {"_status": r.status_code, "_body": r.get_data(as_text=True)}
        return json.loads(r.get_data(as_text=True))

    def by_key(vs, with_book=True):
        out = {}
        for v in vs:
            k = (v.get("book"), v["chapter"], v["verse"]) if with_book else (v["chapter"], v["verse"])
            out[k] = v.get("positions")
        return out

    old_db = core.DB
    try:
        core.DB = dbp

        # ---- All books (the default word-study list) ----
        d = get("/api/lexicon/verses/H1908/all?corpus=abp")
        vs = d.get("verses", [])
        pos = by_key(vs)
        # UNLIT CASE FIRST: reached only via the xref, must carry its slot
        check("all-books: xref-only verse (Gen 25:15) carries its slot",
              pos.get(("Gen", 25, 15)), [1])
        check("all-books: numbered + xref-only verse (1Ki 11:21) carries BOTH",
              pos.get(("1Ki", 11, 21)), [1, 22])
        check("all-books: two xref-only words (1Ki 11:17) carry BOTH",
              pos.get(("1Ki", 11, 17)), [2, 19])
        check("all-books: verse list unchanged (one row per verse, canonical order)",
              [(v["book"], v["chapter"], v["verse"]) for v in vs],
              [("Gen", 25, 15), ("1Ki", 11, 17), ("1Ki", 11, 21)])
        check("all-books: not truncated", d.get("truncated"), False)

        # rendering chip: Gen's word is 'Hadar' — only the two 1Ki verses stay
        d = get("/api/lexicon/verses/H1908/all?corpus=abp&gloss=hadad")
        check("all-books ?gloss=hadad: keeps the 1Ki verses with their slots",
              by_key(d.get("verses", [])),
              {("1Ki", 11, 17): [2, 19], ("1Ki", 11, 21): [1, 22]})

        # testament filter still narrows (heb-xref rows are OT)
        d = get("/api/lexicon/verses/H1908/all?corpus=abp&testament=nt")
        check("all-books testament=nt: empty", d.get("verses"), [])

        # ---- one book ----
        d = get("/api/lexicon/verses/H1908/Gen?corpus=abp")
        check("one book (Gen): xref-only verse carries its slot",
              by_key(d.get("verses", []), with_book=False), {(25, 15): [1]})
        d = get("/api/lexicon/verses/H1908/1Ki?corpus=abp")
        check("one book (1Ki): both verses carry every slot the filter matched",
              by_key(d.get("verses", []), with_book=False),
              {(11, 17): [2, 19], (11, 21): [1, 22]})
        d = get("/api/lexicon/verses/H1908/1Ki?corpus=abp&gloss=hadad")
        check("one book ?gloss=hadad: slots kept",
              by_key(d.get("verses", []), with_book=False),
              {(11, 17): [2, 19], (11, 21): [1, 22]})

        # ---- Greek numbers untouched: no positions field anywhere ----
        d = get("/api/lexicon/verses/G1056/all?corpus=abp")
        check("Greek all-books: list unchanged",
              [(v["book"], v["chapter"], v["verse"]) for v in d.get("verses", [])],
              [("Mat", 4, 15)])
        check("Greek all-books: no positions field",
              any("positions" in v for v in d.get("verses", [])), False)
        d = get("/api/lexicon/verses/G1056/Mat?corpus=abp")
        check("Greek one book: no positions field",
              any("positions" in v for v in d.get("verses", [])), False)
    finally:
        core.DB = old_db

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll Hebrew-xref positions checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
