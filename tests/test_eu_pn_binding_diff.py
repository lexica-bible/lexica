"""Locked test for scripts/eu_pn_binding_diff.py (DESIGN sec 9.92 G1).

Synthetic 3-row fixture: one CHANGED row (Gen 2:8 eden, kind moves, the slot's
strongs_base moves H -> G), one ONLY-SRC row (Mat 1:12 zerubbabel) and one
ONLY-BUILT row (Mat 1:12 zorobabel). Runs the REAL script; asserts every row is
listed, sorted by (book, chapter, verse, name), with both copies' values, the
slot's strongs AND strongs_base on both copies, the H/G key column, and the
summary line. Plus: same file twice = STOP, exit 2.

Run:  python tests/test_eu_pn_binding_diff.py
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "eu_pn_binding_diff.py")

SCHEMA = """
CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
CREATE TABLE words(verse_id INT, position INT, english TEXT, english_head TEXT,
                   is_pn INT, strongs TEXT, strongs_base TEXT);
CREATE TABLE pn_binding(book INTEGER, chapter INTEGER, verse INTEGER, name TEXT,
                        entity_uniq TEXT, kind TEXT, rule TEXT, render INTEGER,
                        hot INTEGER, tier INTEGER);
"""
VERSES = [(1, "Gen", 2, 8), (2, "Mat", 1, 12)]
SRC_WORDS = [(1, 4, "Eden", "", 1, "*", "H5731"),
             (2, 9, "Zerubbabel,", "", 1, "*", "H2216")]
BUILT_WORDS = [(1, 4, "Eden", "", 1, "*", "G2068"),
               (2, 9, "Zorobabel,", "", 1, "*", "H2216")]
SRC_BIND = [(1, 2, 8, "eden", "Eden@Gen.2.8", "exact", "", 1, 0, 1),
            (40, 1, 12, "zerubbabel", "Zerubbabel@1Ch.3.19", "exact", "", 1, 0, 1)]
BUILT_BIND = [(1, 2, 8, "eden", "Eden@Gen.2.8", "fuzzy", "", 1, 0, 1),
              (40, 1, 12, "zorobabel", "Zerubbabel@1Ch.3.19", "fuzzy", "", 1, 0, 1)]


def build(path, words, binds):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO verses VALUES (?,?,?,?)", VERSES)
    conn.executemany("INSERT INTO words VALUES (?,?,?,?,?,?,?)", words)
    conn.executemany("INSERT INTO pn_binding VALUES (?,?,?,?,?,?,?,?,?,?)", binds)
    conn.commit()
    conn.close()


def run(a, b):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.run([sys.executable, SCRIPT, a, b], capture_output=True,
                          text=True, encoding="utf-8", cwd=ROOT, env=env)


class TestPnBindingDiff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.src = os.path.join(cls.tmp, "src.db")
        cls.blt = os.path.join(cls.tmp, "built.db")
        build(cls.src, SRC_WORDS, SRC_BIND)
        build(cls.blt, BUILT_WORDS, BUILT_BIND)
        cls.res = run(cls.src, cls.blt)
        cls.out = cls.res.stdout

    def test_exit_and_summary(self):
        self.assertEqual(self.res.returncode, 0, self.res.stderr)
        self.assertIn("PN-BINDING DIFF: READ - differing 3 - changed 1 - only-src 1 - "
                      "only-built 1", self.out)

    def test_every_row_listed_in_key_order(self):
        heads = [l for l in self.out.splitlines()
                 if l.startswith(("CHANGED", "ONLY-SRC", "ONLY-BUILT"))]
        self.assertEqual(len(heads), 3)
        self.assertTrue(heads[0].startswith("CHANGED  Gen 2:8 [book 1] name='eden'"))
        self.assertTrue(heads[1].startswith("ONLY-SRC  Mat 1:12 [book 40] name='zerubbabel'"))
        self.assertTrue(heads[2].startswith("ONLY-BUILT  Mat 1:12 [book 40] name='zorobabel'"))

    def test_changed_row_values_slots_and_key(self):
        self.assertIn("key src H / built G  cols changed: kind", self.out)
        self.assertIn("src  : entity_uniq='Eden@Gen.2.8' kind='exact'", self.out)
        self.assertIn("built: entity_uniq='Eden@Gen.2.8' kind='fuzzy'", self.out)
        self.assertIn("slots src  : pos 4 strongs='*' strongs_base='H5731' key=H", self.out)
        self.assertIn("slots built: pos 4 strongs='*' strongs_base='G2068' key=G", self.out)

    def test_one_sided_rows_show_the_missing_side(self):
        block = self.out.split("ONLY-SRC", 1)[1].split("ONLY-BUILT", 1)[0]
        self.assertIn("built: (no row)", block)
        self.assertIn("slots src  : pos 9 strongs='*' strongs_base='H2216' key=H", block)
        self.assertIn("slots built: (no slot)", block)      # built's label is Zorobabel
        block = self.out.split("ONLY-BUILT", 1)[1]
        self.assertIn("src  : (no row)", block)
        self.assertIn("slots built: pos 9 strongs='*' strongs_base='H2216' key=H", block)

    def test_same_file_stops(self):
        r = run(self.src, self.src)
        self.assertEqual(r.returncode, 2)
        self.assertIn("PN-BINDING DIFF: STOP - src and built are the same file", r.stdout)


if __name__ == "__main__":
    unittest.main()
