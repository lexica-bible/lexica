#!/usr/bin/env python3
"""Tests for scripts/eu_words_delta.py (edition upgrade step 4 raw delta, DESIGN 9.138 (2) / 9.139).

Made-up databases only. Covered: identical copies -> every count 0; a changed cell is listed with
before/after; a bracket renumbered with the same grouping is NOT a difference, a regrouping IS; a
whole-row swap of two words pairs both ways; an identity that occurs twice among the candidates is
left UNPAIRED (never forced); a word only on one side is listed and paired when its identity is
unique; verses.text and a verse on one side only are listed; neither database is written; --out
must exist and be empty; the same file on both sides is refused.
"""
import contextlib
import hashlib
import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import eu_words_delta as D  # noqa: E402

VERSES = [(1, "Gen", 1, 1, "In the beginning God made"), (2, "Gen", 1, 2, "And the earth was")]
# (verse_id, position, english, strongs, morph, lemma, bracket_id)
WORDS = [
    (1, 1, "In", "1722", "P", "en", None),
    (1, 2, "the beginning", "746", "N", "arche", 7),
    (1, 3, "God", "2316", "N", "theos", 7),
    (1, 4, "made", "4160", "V", "poieo", None),
    (2, 1, "And", "2532", "C", "kai", None),
    (2, 2, "the earth", "1093", "N", "ge", None),
    (2, 3, "was", "1510", "V", "eimi", None),
]


def make(path, verses=VERSES, words=WORDS):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT,
                            strongs TEXT, morph TEXT, lemma TEXT, bracket_id INT);""")
    c.executemany("INSERT INTO verses VALUES (?,?,?,?,?)", verses)
    c.executemany("INSERT INTO words (verse_id, position, english, strongs, morph, lemma, bracket_id) "
                  "VALUES (?,?,?,?,?,?,?)", words)
    c.commit()
    c.close()


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()[1:]


class Delta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="euwd_")
        self.a = os.path.join(self.tmp, "a.db")
        self.b = os.path.join(self.tmp, "b.db")
        self.out = os.path.join(self.tmp, "out")
        os.mkdir(self.out)
        make(self.a)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_delta(self, out=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = D.main(["--a", self.a, "--b", self.b, "--out", out or self.out])
        return rc, buf.getvalue()

    def f(self, name):
        return lines(os.path.join(self.out, name))

    def test_identical_copies_have_no_difference(self):
        make(self.b)
        rc, out = self.run_delta()
        self.assertEqual(rc, 0, out)
        self.assertIn("RESULT: DELTA WRITTEN", out)
        for n in ("words_cells.tsv", "words_only.tsv", "words_moved.tsv", "words_unpaired.tsv",
                  "verses_cells.tsv", "verses_only.tsv"):
            self.assertEqual(self.f(n), [], n)
        self.assertIn("words.english                0", out)

    def test_changed_cell_is_listed(self):
        w = [r if r[:2] != (1, 4) else (1, 4, "created", "4160", "V", "poieo", None) for r in WORDS]
        make(self.b, words=w)
        rc, out = self.run_delta()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.f("words_cells.tsv"), ["Gen\t1\t1\t4\tenglish\t'made'\t'created'\tno"])
        self.assertIn("words.english                1", out)

    def test_bracket_number_is_compared_as_a_rank(self):
        w = [r if r[6] != 7 else r[:6] + (99,) for r in WORDS]              # same grouping, new number
        make(self.b, words=w)
        self.run_delta()
        self.assertEqual(self.f("words_cells.tsv"), [])
        shutil.rmtree(self.out)
        os.mkdir(self.out)
        os.remove(self.b)
        w = [r if r[:2] != (1, 3) else r[:6] + (None,) for r in WORDS]     # God leaves the bracket
        make(self.b, words=w)
        self.run_delta()
        self.assertEqual(self.f("words_cells.tsv"), ["Gen\t1\t1\t3\tbracket_id\t1\tNone\tno"])

    def test_a_swap_pairs_both_ways(self):
        w = list(WORDS)
        w[4], w[5] = (2, 1, "the earth", "1093", "N", "ge", None), (2, 2, "And", "2532", "C", "kai", None)
        make(self.b, words=w)
        rc, out = self.run_delta()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.f("words_moved.tsv"), [
            "Gen\t1\t2\t1\t2\t('2532', 'C', 'kai')\t''", "Gen\t1\t2\t2\t1\t('1093', 'N', 'ge')\t''"])
        self.assertEqual(self.f("words_unpaired.tsv"), [])
        cells = self.f("words_cells.tsv")
        self.assertTrue(cells and all(c.endswith("\tyes") for c in cells), cells)

    def test_a_repeated_identity_is_never_forced_into_a_pair(self):
        # verse 2 on b: positions 1 and 3 both carry kai; a has kai at 1 only -> b's two kai candidates
        w = [r for r in WORDS if r[0] == 1] + [(2, 1, "the earth", "1093", "N", "ge", None),
                                               (2, 2, "And", "2532", "C", "kai", None),
                                               (2, 3, "and", "2532", "C", "kai", None)]
        make(self.b, words=w)
        self.run_delta()
        moved = self.f("words_moved.tsv")
        unpaired = self.f("words_unpaired.tsv")
        self.assertNotIn("2532", "".join(moved))                          # kai: 1 on a, 2 on b -> unpaired
        self.assertIn("a\tGen\t1\t2\t1\t('2532', 'C', 'kai')", unpaired)
        self.assertIn("b\tGen\t1\t2\t2\t('2532', 'C', 'kai')", unpaired)
        self.assertIn("b\tGen\t1\t2\t3\t('2532', 'C', 'kai')", unpaired)

    def test_word_on_one_side_is_listed_and_paired_only_when_unique(self):
        w = [r for r in WORDS if r[:2] != (1, 4)] + [(1, 5, "made", "4160", "V", "poieo", None)]
        make(self.b, words=w)
        self.run_delta()
        only = self.f("words_only.tsv")
        self.assertEqual([x.split("\t")[:5] for x in only], [["a", "Gen", "1", "1", "4"], ["b", "Gen", "1", "1", "5"]])
        self.assertEqual(self.f("words_moved.tsv"), ["Gen\t1\t1\t4\t5\t('4160', 'V', 'poieo')\t''"])

    def test_verse_text_and_verse_on_one_side(self):
        v = [VERSES[0][:4] + ("In the beginning God created",)]
        make(self.b, verses=v, words=[r for r in WORDS if r[0] == 1])
        self.run_delta()
        self.assertEqual(self.f("verses_cells.tsv"),
                         ["Gen\t1\t1\ttext\t'In the beginning God made'\t'In the beginning God created'"])
        self.assertEqual([x.split("\t")[:4] for x in self.f("verses_only.tsv")], [["a", "Gen", "1", "2"]])
        self.assertEqual(len(self.f("words_only.tsv")), 3)

    def test_neither_database_is_written(self):
        make(self.b, words=WORDS[:-1])
        before = (sha(self.a), sha(self.b), os.path.getmtime(self.a), os.path.getmtime(self.b))
        rc, _ = self.run_delta()
        self.assertEqual(rc, 0)
        self.assertEqual((sha(self.a), sha(self.b), os.path.getmtime(self.a), os.path.getmtime(self.b)), before)
        self.assertFalse(os.path.exists(self.a + "-journal") or os.path.exists(self.b + "-journal"))

    def test_out_must_exist_and_be_empty(self):
        make(self.b)
        rc, out = self.run_delta(out=os.path.join(self.tmp, "nope"))
        self.assertEqual(rc, 1)
        self.assertIn("must be an existing folder", out)
        open(os.path.join(self.out, "x"), "w").close()
        rc, out = self.run_delta()
        self.assertEqual(rc, 1)
        self.assertIn("must be empty", out)

    def test_a_type_difference_is_a_difference(self):
        # an untyped strongs column on b keeps the int 4160 as an int (a TEXT column would store '4160')
        w = [r if r[:2] != (1, 4) else (1, 4, "made", 4160, "V", "poieo", None) for r in WORDS]
        c = sqlite3.connect(self.b)
        c.executescript("""
            CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
            CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT,
                                strongs, morph TEXT, lemma TEXT, bracket_id INT);""")
        c.executemany("INSERT INTO verses VALUES (?,?,?,?,?)", VERSES)
        c.executemany("INSERT INTO words (verse_id, position, english, strongs, morph, lemma, bracket_id) "
                      "VALUES (?,?,?,?,?,?,?)", w)
        c.commit()
        c.close()
        self.run_delta()
        self.assertEqual(self.f("words_cells.tsv"), ["Gen\t1\t1\t4\tstrongs\t'4160'\t4160\tno"])

    def test_equal_comparing_values_of_another_type_are_a_difference(self):
        # 1 == 1.0 in Python; only the type check sees it (untyped strongs column on both sides)
        def untyped(path, words):
            c = sqlite3.connect(path)
            c.executescript("""
                CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
                CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT,
                                    strongs, morph TEXT, lemma TEXT, bracket_id INT);""")
            c.executemany("INSERT INTO verses VALUES (?,?,?,?,?)", VERSES)
            c.executemany("INSERT INTO words (verse_id, position, english, strongs, morph, lemma, bracket_id) "
                          "VALUES (?,?,?,?,?,?,?)", words)
            c.commit()
            c.close()
        os.remove(self.a)
        untyped(self.a, [r if r[:2] != (1, 4) else (1, 4, "made", 4160, "V", "poieo", None) for r in WORDS])
        untyped(self.b, [r if r[:2] != (1, 4) else (1, 4, "made", 4160.0, "V", "poieo", None) for r in WORDS])
        self.run_delta()
        self.assertEqual(self.f("words_cells.tsv"), ["Gen\t1\t1\t4\tstrongs\t4160\t4160.0\tno"])

    def test_a_column_on_one_side_only_is_named_and_not_compared(self):
        make(self.b)
        c = sqlite3.connect(self.b)
        c.execute("ALTER TABLE words ADD COLUMN extra TEXT")
        c.execute("UPDATE words SET extra = 'x'")
        c.commit()
        c.close()
        rc, out = self.run_delta()
        self.assertEqual(rc, 0, out)
        self.assertIn("words columns on one side only: a none - b ['extra']", out)
        self.assertEqual(self.f("words_cells.tsv"), [])

    def test_summary_file_holds_the_printed_summary(self):
        make(self.b)
        rc, out = self.run_delta()
        with open(os.path.join(self.out, "summary.txt"), encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(text, out)
        self.assertIn("words_cells.tsv             0 lines + header  sha256 ", text)

    def test_a_word_with_no_verse_row_stops(self):
        make(self.b, words=WORDS + [(3, 1, "x", "1", "X", "x", None)])
        rc, out = self.run_delta()
        self.assertEqual(rc, 1)
        self.assertIn("names verse_id 3, which has no verses row", out)

    def test_a_duplicate_word_key_stops(self):
        make(self.b, words=WORDS + [(1, 4, "made", "4160", "V", "poieo", None)])
        rc, out = self.run_delta()
        self.assertEqual(rc, 1)
        self.assertIn("position 4 appears twice", out)

    def test_same_file_both_sides_refused(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = D.main(["--a", self.a, "--b", self.a, "--out", self.out])
        self.assertEqual(rc, 1)
        self.assertIn("same file", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
