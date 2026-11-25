"""scripts/read_verse_break_forms_20261124.py (DESIGN 9.266 (3)) on a small made-up database and feed: a verse
break the app draws one verse earlier (the 1Jn 5:7/8 shape), a reordered glued cell across a break (the
Gen 1:12/13 shape), a Psalm title (paired through the shift, never moved), and clean verses that stay out.

Run:  python tests/test_verse_break_forms.py
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import read_verse_break_forms_20261124 as R   # noqa: E402

LEX = {"2532": "καί", "5140": "τρεῖς", "1510": "εἰμί", "3588": "ὁ", "3140": "μαρτυρέω", "1909": "ἐπί", "1093": "γῆ",
       "4151": "πνεῦμα", "1492": "εἴδω", "2316": "θεός", "3754": "ὅτι", "2570": "καλός", "1096": "γίνομαι",
       "5568": "ψαλμός", "1722": "ἐν", "746": "ἀρχή"}

# (book, chapter, verse) -> [(strongs, live form)] in live order
LIVE = {
    ("1Jn", 5, 7): [("3754", ""), ("5140", ""), ("1510.2.6", "εισίν")],
    ("1Jn", 5, 8): [("2532", ""), ("5140", ""), ("1510.2.6", ""), ("3588", ""), ("3140", ""), ("1909", ""),
                    ("3588", ""), ("1093", ""), ("3588", "το"), ("4151", "")],
    ("1Jn", 5, 9): [("1722", ""), ("746", "αρχή")],
    ("Gen", 1, 12): [("2532", ""), ("1093", "γη")],
    ("Gen", 1, 13): [("2532", ""), ("2316", ""), ("3588", ""), ("1492", "είδεν"), ("3754", ""), ("2570", "καλόν"),
                     ("2532", ""), ("1096", "εγένετο")],
    ("Psa", 3, 0): [("5568", ""), ("3588", "τω")],
    ("Psa", 3, 1): [("2532", ""), ("1096", "εγένετο")],
}
# feed: (abbrev, chapter, verse) -> [(strongs cell, greek cell)] in app order
FEED = {
    ("1Jn", 5, 7): [("3754", "ότι"), ("5140", "τρεις"), ("1510.2.6", "εισίν"),
                    ("2532", "και"), ("5140", "τρεις"), ("1510.2.6", "εισίν"), ("3588", "οι"), ("3140", "μαρτυρούντες"),
                    ("1909", "επί"), ("3588", "της"), ("1093", "γης")],
    ("1Jn", 5, 8): [("3588", "δαγγερ το"), ("4151", "πνεύμα")],
    ("1Jn", 5, 9): [("1722", "εν"), ("746", "αρχή")],
    ("Gen", 1, 12): [("2532", "και"), ("1093", "γη"), ("2532", "και"), ("1492-3588-2316", "είδεν  ο  θεός"),
                     ("3754", "ότι"), ("2570", "καλόν")],
    ("Gen", 1, 13): [("2532", "και"), ("1096", "εγένετο")],
    ("Psa", 3, 1): [("5568", "ψαλμός"), ("3588", "τω")],
    ("Psa", 3, 2): [("2532", "και"), ("1096", "εγένετο")],
}


class VerseBreak(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, "t.db")
        c = sqlite3.connect(self.db)
        c.executescript("""CREATE TABLE verses (id INTEGER PRIMARY KEY, book, chapter INT, verse INT);
            CREATE TABLE words (verse_id INT, position INT, strongs, strongs_base, is_pn INT);
            CREATE TABLE lexicon (strongs_g, lemma);
            CREATE TABLE abp_surface (verse_id INT, position INT, form, translit);""")
        c.executemany("INSERT INTO lexicon VALUES (?,?)", [("G" + k, v) for k, v in LEX.items()])
        for (b, ch, v), words in LIVE.items():
            vid = c.execute("INSERT INTO verses (book, chapter, verse) VALUES (?,?,?)", (b, ch, v)).lastrowid
            for pos, (s, form) in enumerate(words):
                c.execute("INSERT INTO words VALUES (?,?,?,?,0)", (vid, pos, s, "G" + s.split(".")[0]))
                if form:
                    c.execute("INSERT INTO abp_surface VALUES (?,?,?,'')", (vid, pos, form))
        c.commit()
        c.close()
        self.slots = [{"abbrev": b, "chapter": ch, "verse": v, "slot_index": i, "strongs": s, "greek": g}
                      for (b, ch, v), cells in FEED.items() for i, (s, g) in enumerate(cells)]

    def run_read(self):
        con = sqlite3.connect(f"file:{self.db}?mode=ro", uri=True)
        try:
            n, runs = R.read(con, self.slots, set())
        finally:
            con.close()
        out = os.path.join(self.tmp.name, "out")
        ok = R.write(out, n, runs, set())
        return ok, runs, Path(out, "moved.tsv").read_text(encoding="utf-8").splitlines()[1:]

    def test_finds_both_breaks_and_nothing_else(self):
        ok, runs, moved = self.run_read()
        self.assertTrue(ok)                               # both controls pass
        got = sorted((f"{r['tag'][0][0]} {r['tag'][0][1]}:{r['tag'][1]}", len(r["items"]), r["edge"]) for r in runs)
        self.assertEqual(got, [("1Jn 5:8", 8, True), ("Gen 1:13", 6, True)])
        verdicts = {(m.split("\t")[0], int(m.split("\t")[1])): m.split("\t")[10] for m in moved}
        self.assertEqual([p for (v, p), x in sorted(verdicts.items()) if v == "1Jn 5:8" and x == "DID NOT FOLLOW"],
                         [2, 3, 4, 6, 7])
        self.assertEqual(verdicts[("1Jn 5:8", 0)], "not needed")
        self.assertEqual(verdicts[("Gen 1:13", 3)], "followed")
        self.assertFalse([v for v, _p in verdicts if v.startswith("Psa")])

    def test_the_control_fails_when_the_forms_did_follow(self):
        c = sqlite3.connect(self.db)
        c.execute("INSERT INTO abp_surface SELECT w.verse_id, 3, 'οι', '' FROM words w JOIN verses v ON v.id = w.verse_id "
                  "WHERE v.book='1Jn' AND v.verse=8 AND w.position=3")
        c.commit()
        c.close()
        ok, _runs, _moved = self.run_read()
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
