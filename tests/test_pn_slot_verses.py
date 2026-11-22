#!/usr/bin/env python3
"""Locked test — name-form verse lists: one entry per verse, and the bridged
book rail (TODO small fixes, 11/21).

Two defects, both on numberless names (`PN:<form>` keys and the 6 bridged numbers
like Galilee G1056, whose ABP rows carry no number):

  1. The lists were one entry per HIT, so a verse naming the person twice showed
     two rows with the same key. Fix: one entry per verse carrying every slot in
     `positions` (the field lane (f) gives Hebrew xref rows; the page already reads it).
  2. /api/lexicon/books had no bridge branch, so for a bridged number the ABP
     book list (and the no-corpus default) came back EMPTY — clicking a rendering
     chip silently showed the unnarrowed list. Fix: count the name's own slots,
     the same rows the verses endpoint serves.

KNOWN POSITIVE FIRST: Mat 4:23 names Galilee twice (slots 4 and 9) — on the old
code it came back as two entries; the bridged book list came back empty.

Pure stdlib + on-disk temp SQLite (the routes open core.DB). Run:
  python tests/test_pn_slot_verses.py
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GAL = "Γαλιλαία"


def _make_db(path):
    c = sqlite3.connect(path)
    c.executescript(f"""
        CREATE TABLE books (abbrev TEXT, name TEXT, sort_order INT, id INT);
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT,
                             verse INT, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            english TEXT, english_head TEXT, strongs_base TEXT,
                            strongs TEXT, is_pn INT, italic INT DEFAULT 0);
        CREATE TABLE lexicon (strongs TEXT, strongs_g TEXT, lemma TEXT, lemma_plain TEXT,
                              translit TEXT, kjv_def TEXT, derivation TEXT,
                              strongs_def TEXT);
        CREATE TABLE pn_greek_identity (
            verse_id INT, position INT, greek_strongs TEXT, greek_lemma TEXT,
            source TEXT, hebrew_base TEXT, PRIMARY KEY (verse_id, position));

        INSERT INTO books VALUES ('Jos','Joshua',6,6), ('Mat','Matthew',40,40);
        INSERT INTO verses VALUES
            (1,'Mat',4,15,'land of Zebulun ... Galilee'),
            (2,'Mat',4,23,'Jesus went about all Galilee ... in Galilee'),
            (3,'Jos',20,7,'Kedesh in Galilee');
        -- the starred Galilee slots: ABP's printed English, no number
        INSERT INTO words (id, verse_id, position, english, english_head,
                           strongs_base, strongs, is_pn) VALUES
            (1, 1, 5, 'Galilee', 'Galilee', NULL, '*', 1),
            (2, 2, 9, 'Galilee', 'Galilee', NULL, '*', 1),
            (3, 2, 4, 'Galilee', 'Galilee', NULL, '*', 1),
            (4, 2, 6, 'went', 'went', 'G4013', '4013', 0),
            (5, 3, 2, 'Galilee', 'Galilee', NULL, '*', 1);
        INSERT INTO pn_greek_identity VALUES
            (1, 5, NULL, '{GAL}', 'surface', NULL),
            (2, 9, NULL, '{GAL}', 'surface', NULL),
            (2, 4, NULL, '{GAL}', 'surface', NULL),
            (3, 2, NULL, '{GAL}', 'surface', NULL);
        INSERT INTO lexicon VALUES
            ('1056','G1056','{GAL}','γαλιλαια','galilaia','Galilee','','Galilee');
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
    dbp = os.path.join(tmp, "pn_slot_verses.db")
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

    def keys(vs):
        return [(v.get("book"), v["chapter"], v["verse"], v.get("positions")) for v in vs]

    want_all = [("Jos", 20, 7, [2]), ("Mat", 4, 15, [5]), ("Mat", 4, 23, [4, 9])]
    want_mat = [(None, 4, 15, [5]), (None, 4, 23, [4, 9])]

    old_db = core.DB
    core.DB = dbp
    try:
        # ---- defect 1: one entry per verse ----
        d = get(f"/api/lexicon/verses/PN:{GAL}/all")
        check("POSITIVE: PN: list — the twice-named verse is ONE entry with both slots",
              keys(d.get("verses", [])), want_all)
        d = get(f"/api/lexicon/verses/PN:{GAL}/Mat")
        check("PN: one book — same", [(v["chapter"], v["verse"], v.get("positions"))
                                       for v in d.get("verses", [])],
              [(4, 15, [5]), (4, 23, [4, 9])])
        d = get(f"/api/lexicon/profile/PN:{GAL}")
        check("PN: profile default list — same", keys(d.get("default_verses", [])), want_all)
        check("PN: profile total still counts HITS (4), like a numbered word",
              d.get("total"), 4)
        check("PN: profile book counts still count hits",
              {b["book"]: b["count"] for b in d.get("books", [])}, {"Mat": 3, "Jos": 1})

        d = get("/api/lexicon/verses/G1056/all?corpus=abp")
        check("bridged All-books list — same", keys(d.get("verses", [])), want_all)
        d = get("/api/lexicon/verses/G1056/all?corpus=abp&gloss=galilee")
        check("bridged rendering chip — same", keys(d.get("verses", [])), want_all)
        d = get("/api/lexicon/verses/G1056/Mat?corpus=abp")
        check("bridged one book — same", keys(d.get("verses", [])), want_mat)
        # (the numbered profile's default list is this same _all_books_verses call)
        d = get("/api/lexicon/verses/G1056/all?corpus=abp")
        check("no entry carries the old single `position`",
              any("position" in v for v in d.get("verses", [])), False)

        # ---- defect 2: the bridged book rail ----
        want_books = {"Mat": 3, "Jos": 1}
        d = get("/api/lexicon/books/G1056?corpus=abp")
        check("POSITIVE: bridged book list is no longer empty (ABP)",
              {b["book"]: b["count"] for b in d.get("books", [])}, want_books)
        d = get("/api/lexicon/books/G1056")
        check("bridged book list, no-corpus default",
              {b["book"]: b["count"] for b in d.get("books", [])}, want_books)
        d = get("/api/lexicon/books/G1056?corpus=abp&gloss=galilee")
        check("bridged book list narrowed by its rendering",
              {b["book"]: b["count"] for b in d.get("books", [])}, want_books)
        d = get("/api/lexicon/books/G1056?corpus=abp&gloss=zzz")
        check("an unattested rendering narrows to nothing", d.get("books"), [])
        d = get("/api/lexicon/books/G4013?corpus=abp")
        check("a numbered word is untouched (its own words rows)",
              {b["book"]: b["count"] for b in d.get("books", [])}, {"Mat": 1})
    finally:
        core.DB = old_db

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll name-form slot-list checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
