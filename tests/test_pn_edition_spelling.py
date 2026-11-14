#!/usr/bin/env python3
"""
test_pn_edition_spelling.py — locks the edition respelling list in backfill_pn_surface.py
(DESIGN 9.115): bh_scrape.db labels names in the OLD edition's spelling, so a respelled name
(Jabish -> Jabesh) no longer finds its printed Greek. scripts/pn_edition_spelling.tsv names, per
verse, the old token(s) an edition token is printed under; the backfill uses it ONLY for slots its
normal rules refused, and keeps the result only if no normally paired slot changes.

Ruled cases: direct match still wins · a mapped miss resolves · an unmapped miss still refuses.
Plus: ordered multi-token row (Gen 4:18 shape) · count mismatch leaves the row unused · a mapped
slot joins an existing group (Num 26:39 shape) · the no-change guard keeps the first pass ·
a listed slot whose old token has no row stays refused · shape 2, a possessive label in a shifted
slot (Est 5:9) · shape 3, a different English word (Num 36:5) · the bridge path, a name only in a
glued cell (Gen 5:25) · a malformed list stops the run, table untouched · the committed list loads.
Fixture shapes copy tests/test_pn_surface_backfill.py (the real builders' CREATE TABLEs).
"""
import os
import sqlite3
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "backfill_pn_surface.py")
_ENV = dict(os.environ, PYTHONIOENCODING="utf-8")

LIST_HEADER = "book\tchapter\tverse\tedition_token\tscrape_tokens\tnote\n"
LIST_ROWS = [
    ("Mat", 1, 1, "jabesh", "jabish"),            # A: direct match exists -> not needed
    ("Mat", 2, 1, "joram", "jehoram"),            # B: mapped miss resolves
    ("Mat", 4, 1, "mathusala", "methusael,methusaela"),  # D: ordered, one per refused slot
    ("Mat", 5, 1, "mathusala", "methusael,methusaela"),  # E: 2 tokens, 1 refused slot -> unused
    ("Mat", 6, 1, "hupham", "shupham"),           # F: joins the shupham group
    ("Mat", 7, 1, "adm", "adam"),                 # G: would un-pair the blank slot -> conflict
    ("Mat", 9, 9, "nobody", "noone"),             # verse has no name slot -> no slot
    ("Mat", 8, 1, "silvanus", "silouanos"),       # H: listed, but the scrape has no such row
    ("Mat", 10, 1, "hamans", "haman"),            # S2: shape 2, possessive label (Est 5:9 shape, slot shifted)
    ("Mat", 11, 1, "joseph", "israel"),           # S3: shape 3, a different English word (Num 36:5 shape)
    ("Mat", 12, 1, "mathusala", "methuselah"),    # S4: bridge path - name only in a glued cell (Gen 5:25 shape)
]


def _make_bible(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT,
                             verse INT, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            english TEXT, english_head TEXT, strongs_base TEXT,
                            strongs TEXT, is_pn INT, italic INT DEFAULT 0,
                            italic_words TEXT, greek_pos TEXT, bracket_id INT,
                            morph TEXT, smcap_words TEXT, lemma TEXT);
        CREATE TABLE abp_surface (
          verse_id INTEGER, position INTEGER, form TEXT, translit TEXT,
          PRIMARY KEY (verse_id, position));
        INSERT INTO verses VALUES (1,'Mat',1,1,'...'), (2,'Mat',2,1,'...'), (3,'Mat',3,1,'...'),
                                  (4,'Mat',4,1,'...'), (5,'Mat',5,1,'...'), (6,'Mat',6,1,'...'),
                                  (7,'Mat',7,1,'...'), (8,'Mat',8,1,'...'), (10,'Mat',10,1,'...'),
                                  (11,'Mat',11,1,'...'), (12,'Mat',12,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn) VALUES
          (1,2,'Jabesh','Jabesh','*','*',1),        -- A
          (2,4,'of Joram','Joram','*','*',1),       -- B
          (3,1,'Silvanus,','Silvanus','*','*',1),   -- C: unmapped miss
          (4,14,'Mathusala;','Mathusala','*','*',1),-- D
          (4,16,'Mathusala','Mathusala','*','*',1),
          (5,3,'Mathusala','Mathusala','*','*',1),  -- E
          (6,1,'Shupham,','Shupham','*','*',1),     -- F
          (6,6,'Hupham,','Hupham','*','*',1),
          (7,3,NULL,NULL,'*','*',1),                -- G: blank slot, paired by the blank path
          (7,7,'Adm','Adm','*','*',1),
          (8,2,'Silvanus','Silvanus','*','*',1),     -- H
          (10,2,'Haman','Haman','*','*',1),          -- S2: direct match
          (10,12,'Haman''s','Haman''s','*','*',1),   --     possessive label -> token hamans, refused
          (11,5,'of Israel,','Israel','*','*',1),    -- S3: ambiguous alone (two Israel rows)
          (11,13,'of Joseph,','Joseph','*','*',1),   --     the old edition printed 'Israel' here
          (12,1,'Mathusala','Mathusala','*','*',1);  -- S4: bridge-fail alone (the book attests Methuselah)
    """)
    c.commit()
    c.close()


def _make_scrape(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE bh_words (
            id INTEGER PRIMARY KEY, book TEXT NOT NULL, chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL, position INTEGER NOT NULL, strongs TEXT,
            greek TEXT, english TEXT, italic_words TEXT NOT NULL DEFAULT '',
            smcap_words TEXT NOT NULL DEFAULT '', greek_pos INTEGER);
        INSERT INTO bh_words (book,chapter,verse,position,strongs,greek,english) VALUES
          ('matthew',1,1,1,NULL,'ΙΑΒΕΣ','Jabesh'),     -- A: the direct row
          ('matthew',1,1,2,NULL,'ΙΑΒΙΣ','Jabish'),     --    the listed old token's row (must NOT win)
          ('matthew',2,1,1,NULL,'Ιωράμ','of Jehoram'), -- B
          ('matthew',3,1,1,NULL,'Σιλουανός','Silas'),  -- C
          ('matthew',4,1,1,NULL,'ΜΑΘΑ','Methusael'),   -- D
          ('matthew',4,1,2,NULL,'ΜΑΘΒ','Methusaela'),
          ('matthew',5,1,1,NULL,'ΜΑΘΓ','Methusael'),   -- E
          ('matthew',6,1,1,NULL,'Σωφάν','Shupham'),    -- F: two rows, same old token
          ('matthew',6,1,2,NULL,'Οφάμ','Shupham'),
          ('matthew',7,1,1,'2036-*','είπεν Αδάμ','said Adam'),  -- G: its token is 'adam'
          ('matthew',8,1,1,NULL,'Σιλάς','Silas'),      -- H: the listed old token has no row
          ('matthew',10,1,1,NULL,'Αμάν','Haman'),      -- S2: one Haman row
          ('matthew',11,1,1,NULL,'Ισραήλ','of Israel'),-- S3: two rows labelled Israel in the old edition
          ('matthew',11,1,2,NULL,'Ιωσήφ','of Israel'),
          ('matthew',12,1,1,'2198-*','έζησε Μαθουσαλά','Methuselah lived'),  -- S4: glued cell, token 'lived'
          ('matthew',13,1,1,NULL,'Μαθουσαλά','Methuselah');  -- same-book standalone cell (no words rows)
    """)
    c.commit()
    c.close()


def _write_list(path, rows, header=LIST_HEADER):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# test list\n" + header)
        for book, ch, vs, tok, olds in rows:
            f.write(f"{book}\t{ch}\t{vs}\t{tok}\t{olds}\ttest\n")


def _run(dbp, bhp, *extra):
    return subprocess.run([sys.executable, SCRIPT, dbp, "--bh", bhp, *extra],
                          capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=_ENV)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")   # failure lines carry Greek; the Windows console is cp1252
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    tmp = tempfile.mkdtemp()
    dbp, bhp = os.path.join(tmp, "bible.db"), os.path.join(tmp, "bh.db")
    lp, dump = os.path.join(tmp, "list.tsv"), os.path.join(tmp, "dump.tsv")
    _make_bible(dbp)
    _make_scrape(bhp)
    _write_list(lp, LIST_ROWS)

    # without the list (an empty one): the respellings all refuse, as on 11/14
    empty = os.path.join(tmp, "empty.tsv")
    _write_list(empty, [])
    r = _run(dbp, bhp, "--spelling-list", empty, "--apply")
    check("empty list: exit 0", r.returncode, 0)
    c = sqlite3.connect(dbp)
    base = dict(((v, p), f) for v, p, f, _t in c.execute("SELECT * FROM abp_surface"))
    c.execute("DELETE FROM abp_surface")
    c.commit()
    c.close()
    check("empty list: B, D, F's hupham, S2's Haman's, S3 refuse; A, G's blank slot, S2's Haman pair",
          sorted(base), [(1, 2), (7, 3), (10, 2)])

    r = _run(dbp, bhp, "--spelling-list", lp, "--apply", "--dump-list", dump)
    check("list: exit 0", r.returncode, 0)
    out = r.stdout
    c = sqlite3.connect(dbp)
    rows = dict(((v, p), f) for v, p, f, _t in c.execute("SELECT * FROM abp_surface"))
    c.close()
    check("A direct match still wins (Jabesh row, not the listed Jabish row)", rows.get((1, 2)), "ΙΑΒΕΣ")
    check("B mapped miss resolves (Joram -> the Jehoram row)", rows.get((2, 4)), "Ιωράμ")
    check("C unmapped miss still refuses", (3, 1) in rows, False)
    check("D ordered row: k-th refused slot -> k-th old token",
          (rows.get((4, 14)), rows.get((4, 16))), ("ΜΑΘΑ", "ΜΑΘΒ"))
    check("E count differs: row unused, slot refused", (5, 3) in rows, False)
    check("F mapped slot joins the group: both paired in order",
          (rows.get((6, 1)), rows.get((6, 6))), ("Σωφάν", "Οφάμ"))
    check("G no-change guard: the blank slot keeps its pairing", rows.get((7, 3)), "Αδάμ")
    check("G no-change guard: the listed slot stays refused", (7, 7) in rows, False)
    check("S2 shape 2: the possessive slot gets Haman's Greek; the direct Haman slot unchanged",
          (rows.get((10, 2)), rows.get((10, 12))), ("Αμάν", "Αμάν"))
    check("S3 shape 3: Joseph gets the row the old edition labelled Israel, Israel its own (in order)",
          (rows.get((11, 5)), rows.get((11, 13))), ("Ισραήλ", "Ιωσήφ"))
    check("S4 bridge path: the respelled slot takes the glued cell's name word via the old token",
          rows.get((12, 1)), "Μαθουσαλά")
    check("rows = 3 base + 9 from the list (B 1, D 2, F 2, S2 1, S3 2, S4 1)", len(rows), 12)
    check("report: adds line", "respelling-list adds      : 9 " in out, True)
    check("report: tried / paired / still refused / paired along",
          "slots tried 8 - paired 7 - still refused 1; other slots paired along with them "
          "(their group could resolve once the listed slot joined it) 2" in out, True)
    check("report: A not needed", "Mat 1:1 jabesh -> jabish : not needed (direct match)" in out, True)
    check("report: E count differs",
          "Mat 5:1 mathusala -> methusael,methusaela : count differs (1 refused slot(s), 2 tokens)" in out, True)
    check("report: G conflict", "Mat 7:1 adm -> adam : conflict (would change a normally paired slot) - not used"
          in out, True)
    check("report: no slot", "Mat 9:9 nobody -> noone : no slot with this token" in out, True)
    check("H listed but still refused: no row, reported",
          ((8, 2) in rows, "Mat 8:1 silvanus -> silouanos : tried, still refused (1 slot(s): the old token "
                           "did not pair either)" in out), (False, True))
    check("arithmetic closes", "= 16 (must equal 16)" in out.replace(",", ""), True)
    with open(dump, encoding="utf-8") as f:
        d = [ln.rstrip("\n").split("\t") for ln in f]
    check("dump: the 9 paired slots, each with its position, old token and form",
          sorted((x[0], x[2], x[4], x[6], x[7]) for x in d if x[0].startswith("paired")),
          sorted([("paired", "2", "4", "jehoram", "Ιωράμ"), ("paired", "4", "14", "methusael", "ΜΑΘΑ"),
                  ("paired", "4", "16", "methusaela", "ΜΑΘΒ"), ("paired along", "6", "1", "", "Σωφάν"),
                  ("paired", "6", "6", "shupham", "Οφάμ"), ("paired", "10", "12", "haman", "Αμάν"),
                  ("paired", "11", "13", "israel", "Ιωσήφ"), ("paired along", "11", "5", "", "Ισραήλ"),
                  ("paired", "12", "1", "methuselah", "Μαθουσαλά")]))
    check("dump: 9 paired + 5 rows not used", (sum(x[0].startswith("paired") for x in d),
                                               sum(x[0] == "row not used" for x in d)), (9, 5))

    # a malformed list stops the run before anything is read or written
    for name, body in (("self-map", [("Mat", 2, 1, "joram", "joram")]),
                       ("bad book", [("Xyz", 2, 1, "joram", "jehoram")]),
                       ("twice", [("Mat", 2, 1, "joram", "jehoram"), ("Mat", 2, 1, "joram", "x")]),
                       ("capital", [("Mat", 2, 1, "Joram", "jehoram")])):
        bad = os.path.join(tmp, "bad.tsv")
        _write_list(bad, body)
        c = sqlite3.connect(dbp)
        before = sorted(c.execute("SELECT * FROM abp_surface"))
        c.close()
        r = _run(dbp, bhp, "--spelling-list", bad, "--apply")
        c = sqlite3.connect(dbp)
        after = sorted(c.execute("SELECT * FROM abp_surface"))
        c.close()
        check(f"malformed list ({name}) stops the run, table untouched",
              (r.returncode != 0, "respelling list unusable" in r.stderr, after == before), (True, True, True))
    _write_list(os.path.join(tmp, "nohead.tsv"), [], header="")
    r = _run(dbp, bhp, "--spelling-list", os.path.join(tmp, "nohead.tsv"))
    check("list with no header stops the run", r.returncode != 0, True)

    # the committed list loads and every row is well formed
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import backfill_pn_surface as b
    listed, n = b.load_spelling_list(b.SPELLING_LIST)
    check("committed list: 149 rows", n, 149)
    check("committed list: Gen 4:18 keeps both old spellings in slot order",
          listed[("Gen", 4, 18)]["mathusala"], ["methusael", "methusaela"])

    if fails:
        print("\n".join(fails))
        return 1
    print("\nAll edition-respelling checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
