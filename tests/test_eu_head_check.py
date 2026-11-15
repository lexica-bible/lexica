#!/usr/bin/env python3
"""Tests for scripts/eu_head_check.py (edition upgrade step 4 head-consistency check, DESIGN 9.145 (2)).
Made-up databases only. Covered: the recompute mirrors the build's base rule (plain pick, the italic re-pick,
the star/name re-pick); a stale head on built only with equal inputs is a CANDIDATE (the Joh 19:18 shape);
a row mismatching on both copies is not; a built-only mismatch whose english differs is counted as
'inputs differ', not a candidate; src-only is counted; --show prints a row's detail; neither database is
written; --out must exist and be empty; the same file on both sides is refused.
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
import eu_head_check as H  # noqa: E402

VERSES = [(1, "Joh", 19, 18), (2, "Gen", 1, 1)]
# (verse_id, position, english, english_head, italic_words, strongs)
BASE = [
    (1, 10, "one here on that side,", "here", "on, that, side", "3592"),       # italic re-pick -> 'here'
    (1, 11, "Hezekiah said,", "hezekiah", None, "*"),                            # name re-pick -> 'hezekiah'
    (1, 12, "take favor", "take", "favor", "2983"),                               # italic -> 'take'
    (2, 1, "the beginning", "beginning", None, "746"),                            # plain pick
    (2, 2, "God made", "special", None, "4160"),                                  # a special pass's head: mismatch
]


def make(path, words):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT,
                            english_head TEXT, italic_words TEXT, strongs TEXT);""")
    c.executemany("INSERT INTO verses VALUES (?,?,?,?)", VERSES)
    c.executemany("INSERT INTO words (verse_id, position, english, english_head, italic_words, strongs) "
                  "VALUES (?,?,?,?,?,?)", words)
    c.commit()
    c.close()


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class HeadCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="euhc_")
        self.a, self.b = os.path.join(self.tmp, "a.db"), os.path.join(self.tmp, "b.db")
        self.out = os.path.join(self.tmp, "out")
        os.mkdir(self.out)
        make(self.a, BASE)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def go(self, out=None, show=()):
        argv = ["--a", self.a, "--b", self.b, "--out", out or self.out]
        for s in show:
            argv += ["--show", s]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = H.main(argv)
        return rc, buf.getvalue()

    def lines(self, name):
        with open(os.path.join(self.out, name), encoding="utf-8") as f:
            return f.read().splitlines()[1:]

    def test_recompute_mirrors_the_build_base_rule(self):
        self.assertEqual(H.recompute("one here on that side,", "on, that, side", "3592"), "here")
        self.assertEqual(H.recompute("one h ere on that side,", "on, that, side", "3592"), "ere")
        self.assertEqual(H.recompute("Hezekiah said,", None, "*"), "hezekiah")
        self.assertEqual(H.recompute("Hezekiah said,", None, "1"), "said")
        self.assertEqual(H.recompute("take favor", "favor", "2983"), "take")
        self.assertIsNone(H.recompute(None, None, "1"))

    def test_star_row_with_italics_ends_on_the_italic_pick(self):
        # the full build's last pass (fix_italic_heads re-clean) re-picks with the italic set on every row,
        # star rows included: name pick 'hezekiah' is replaced by the italic pick 'went'
        self.assertEqual(H.recompute("Hezekiah went up", "up", "*"), "went")
        self.assertEqual(H.recompute("Hezekiah went up", None, "*"), "hezekiah")

    def test_both_copies_mismatching_with_different_heads_are_listed(self):
        make(self.b, [r if r[:2] != (2, 2) else r[:3] + ("other",) + r[4:] for r in BASE])
        rc, out = self.go()
        self.assertIn("mismatching on both copies   1 (of which the two stored heads differ: 1", out)
        self.assertEqual(len(self.lines("both_differ.tsv")), 1)
        self.assertEqual(self.lines("candidates.tsv"), [])

    def test_identical_copies_have_no_candidate(self):
        make(self.b, BASE)
        rc, out = self.go()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.lines("candidates.tsv"), [])
        self.assertIn("mismatching on both copies   1", out)                # the special-pass row
        self.assertEqual(len(self.lines("mismatch_a.tsv")), 1)

    def test_stale_head_on_built_with_equal_inputs_is_a_candidate(self):
        make(self.b, [r if r[:2] != (1, 10) else r[:3] + ("ere",) + r[4:] for r in BASE])
        rc, out = self.go(show=["Joh 19:18@10"])
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.lines("candidates.tsv"),
                         ["Joh\t19\t18\t10\t'one here on that side,'\t'here'\t'ere'\t'here'\t'on, that, side'\t'3592'"])
        self.assertIn("on built only                1 = stale-head CANDIDATES 1 + inputs differ 0", out)
        self.assertIn("SHOW Joh 19:18@10 - candidate: yes", out)
        self.assertIn("stored head 'ere'", out)

    def test_built_only_mismatch_with_other_english_is_not_a_candidate(self):
        make(self.b, [r if r[:2] != (2, 1) else (2, 1, "the start", "beginning", None, "746") for r in BASE])
        rc, out = self.go()
        self.assertEqual(self.lines("candidates.tsv"), [])
        self.assertIn("stale-head CANDIDATES 0 + inputs differ 1", out)

    def test_src_only_mismatch_is_counted(self):
        make(self.b, [r if r[:2] != (2, 2) else r[:3] + ("made",) + r[4:] for r in BASE])
        rc, out = self.go()
        self.assertIn("on src only                  1", out)
        self.assertEqual(self.lines("candidates.tsv"), [])

    def test_show_on_a_non_candidate_says_no(self):
        make(self.b, BASE)
        rc, out = self.go(show=["Gen 1:1@2"])
        self.assertIn("SHOW Gen 1:1@2 - candidate: NO", out)
        self.assertIn("MISMATCH", out)

    def test_neither_database_is_written_and_guards(self):
        make(self.b, BASE)
        before = (sha(self.a), sha(self.b), os.path.getmtime(self.a), os.path.getmtime(self.b))
        rc, _ = self.go()
        self.assertEqual(rc, 0)
        self.assertEqual((sha(self.a), sha(self.b), os.path.getmtime(self.a), os.path.getmtime(self.b)), before)
        rc, out = self.go()                                                    # --out no longer empty
        self.assertEqual(rc, 1)
        self.assertIn("must be empty", out)
        o2 = os.path.join(self.tmp, "o2")
        os.mkdir(o2)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = H.main(["--a", self.a, "--b", self.a, "--out", o2])
        self.assertEqual(rc, 1)
        self.assertIn("same file", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
