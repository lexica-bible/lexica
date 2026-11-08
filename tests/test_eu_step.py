"""Tests for scripts/eu_step.py (edition upgrade: the shared pre / prep / delta / same / check steps),
on made-up databases only. The dry run is the real step-11 builder (build_rendering_norm) on the
throwaway copy, so the chain below is the step-11 block in miniature.

  1. pre: guards pass on a clean repo at REF and make the run folder; STOP on: folder exists,
     unknown REF, REF not an ancestor, scripts/ differ from REF, uncommitted scripts/ change,
     -journal beside a db, a trigger, a missing rollback copy
  2. prep: state + before.db + dry.db; the dry copy = built by digest, row ids kept (a table
     without an id column too); STOP on a missing table / column, or a second prep
  3. dry run on the copy -> delta built -> dry: only english_head_norm changes, every row named,
     kjv/bsb word_norm 0; the delta file's sha is stable; --zero and --expect-sha gate it
  4. same: OK while built is untouched; STOP after any write
  5. check: OK after the same builder runs on built; FAIL on an extra write to an unwritten
     table, on a written table that differs from the dry run (row-level file written), on a
     -journal, and on a dirty scripts/ folder
  6. delta details: a duplicated row and a case-only change in a NOCASE column are differences;
     added / removed rows under a natural key

Run:  python tests/test_eu_step.py
"""
import contextlib
import io
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)
import eu_step  # noqa: E402
import build_rendering_norm  # noqa: E402

TAG = "T11"


def run(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = eu_step.main(list(argv))
    return rc, buf.getvalue()


def make_built(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT,
                            english_head TEXT, strongs TEXT, english_head_norm TEXT);
        CREATE INDEX idx_words_ehnorm ON words(english_head_norm COLLATE NOCASE);
        CREATE TABLE kjv_words (word_id INTEGER PRIMARY KEY, word TEXT, word_norm TEXT);
        CREATE TABLE bsb_words (word_id INTEGER PRIMARY KEY, word TEXT, word_norm TEXT);
        CREATE TABLE pn_binding (book INT, chapter INT, verse INT, name TEXT COLLATE NOCASE, render INT);
        CREATE VIRTUAL TABLE verses_fts USING fts5(text);
    """)
    c.executemany("INSERT INTO verses VALUES (?,?,?,?,?)",
                  [(1, "Gen", 1, 1, "In the beginning"), (2, "Gen", 1, 2, "And the earth")])
    rows = [(10, 1, 0, "in", "in"), (11, 1, 1, "the beginning", "beginning"), (12, 1, 2, "sons", "sons"),
            (13, 2, 0, "and", "and"), (14, 2, 1, "", ""), (15, 2, 2, None, None), (16, 2, 3, "lands", "lands")]
    c.executemany("INSERT INTO words (id, verse_id, position, english, english_head, strongs) VALUES (?,?,?,?,?,'G1')", rows)
    # kjv/bsb already normed, as on a copy of live (a rebuild never touches them)
    for t in ("kjv_words", "bsb_words"):
        c.executemany("INSERT INTO %s (word_id, word) VALUES (?,?)" % t, [(1, "sons"), (2, "Lands"), (3, "the")])
    c.executemany("INSERT INTO pn_binding VALUES (?,?,?,?,?)", [(1, 1, 1, "adam", 1), (1, 1, 2, "eve", 0)])
    c.execute("INSERT INTO verses_fts (text) VALUES ('In the beginning')")
    c.commit()
    build_rendering_norm.recompute_norms(c, only="kjv_words", log=lambda *_: None)
    build_rendering_norm.recompute_norms(c, only="bsb_words", log=lambda *_: None)
    c.commit()
    c.close()


def step11(path):
    c = sqlite3.connect(path)
    build_rendering_norm.recompute_norms(c, log=lambda *_: None)
    c.commit()
    c.close()


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t"] + list(args),
                          capture_output=True, text=True, check=True).stdout.strip()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.d = self.tmp.name
        self.repo = os.path.join(self.d, "repo")
        os.makedirs(os.path.join(self.repo, "scripts"))
        os.makedirs(os.path.join(self.repo, "tests"))
        with open(os.path.join(self.repo, "scripts", "x.py"), "w", newline="\n") as f:
            f.write("x = 1\n")
        with open(os.path.join(self.repo, "tests", "y.py"), "w", newline="\n") as f:
            f.write("y = 1\n")
        git(self.repo, "init", "-q")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "one")
        self.ref = git(self.repo, "rev-parse", "--short", "HEAD")
        self.built = os.path.join(self.d, "built.db")
        make_built(self.built)
        self.keep = os.path.join(self.d, "pre.db")
        with open(self.keep, "wb") as f:
            f.write(b"x")
        self.runs = os.path.join(self.d, "runs")
        os.makedirs(self.runs)
        self.run_dir = os.path.join(self.runs, "step11")

    def tearDown(self):
        self.tmp.cleanup()

    def pre(self, *extra, dir_=None):
        return run("pre", "--tag", TAG, "--repo", self.repo, "--ref", self.ref, "--dir", dir_ or self.run_dir,
                   "--db", self.built, "--keep", self.keep, *extra)

    def prep(self):
        return run("prep", "--tag", TAG, "--repo", self.repo, "--built", self.built, "--dir", self.run_dir,
                   "--copy", "words,kjv_words,bsb_words", "--save", "words:english_head_norm",
                   "--save", "kjv_words:word_norm", "--save", "bsb_words:word_norm", "--save", "pn_binding")

    def dry(self):
        return os.path.join(self.run_dir, "dry.db")

    def delta(self, out, *extra, a=None, b=None, tables=("words", "kjv_words", "bsb_words")):
        args = ["delta", "--tag", TAG, "--a", a or self.built, "--b", b or self.dry(), "--out", os.path.join(self.d, out)]
        for t in tables:
            args += ["--table", t]
        return run(*args, *extra)

    def check(self):
        return run("check", "--tag", TAG, "--repo", self.repo, "--built", self.built, "--dir", self.run_dir,
                   "--written", "words,kjv_words,bsb_words")


class Pre(Base):
    def test_ok_then_folder_exists(self):
        rc, out = self.pre()
        self.assertEqual(rc, 0, out)
        self.assertTrue(out.rstrip().endswith("T11 PRE: OK"))
        self.assertTrue(os.path.isdir(self.run_dir))
        rc, out = self.pre()
        self.assertEqual(rc, 1)
        self.assertIn("run folder already exists", out)

    def test_unknown_ref(self):
        self.ref = "0123abcd"
        rc, out = self.pre()
        self.assertEqual(rc, 1)
        self.assertIn("has not pulled 0123abcd", out)
        self.assertFalse(os.path.exists(self.run_dir))

    def test_ref_not_ancestor(self):
        git(self.repo, "checkout", "-q", "-b", "side")
        with open(os.path.join(self.repo, "README"), "w") as f:
            f.write("side\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "side")
        side = git(self.repo, "rev-parse", "--short", "HEAD")
        git(self.repo, "checkout", "-q", "-")
        self.ref = side
        rc, out = self.pre()
        self.assertEqual(rc, 1)
        self.assertIn("is not an ancestor of HEAD", out)

    def test_scripts_differ_from_ref(self):
        with open(os.path.join(self.repo, "scripts", "x.py"), "w", newline="\n") as f:
            f.write("x = 2\n")
        git(self.repo, "commit", "-q", "-am", "two")
        rc, out = self.pre()
        self.assertEqual(rc, 1)
        self.assertIn("scripts/tests differ from", out)

    def test_uncommitted(self):
        with open(os.path.join(self.repo, "tests", "y.py"), "w", newline="\n") as f:
            f.write("y = 2\n")
        rc, out = self.pre()
        self.assertEqual(rc, 1)
        self.assertIn("uncommitted changes", out)

    def test_journal(self):
        open(self.built + "-journal", "wb").close()
        rc, out = self.pre()
        self.assertEqual(rc, 1)
        self.assertIn("-journal present", out)

    def test_trigger(self):
        c = sqlite3.connect(self.built)
        c.execute("CREATE TRIGGER tr AFTER INSERT ON verses BEGIN SELECT 1; END")
        c.commit()
        c.close()
        rc, out = self.pre()
        self.assertEqual(rc, 1)
        self.assertIn("1 trigger(s)", out)

    def test_missing_keep(self):
        os.remove(self.keep)
        rc, out = self.pre()
        self.assertEqual(rc, 1)
        self.assertIn("rollback copy missing", out)


class Chain(Base):
    def setUp(self):
        super().setUp()
        rc, out = self.pre()
        self.assertEqual(rc, 0, out)

    def test_prep(self):
        rc, out = self.prep()
        self.assertEqual(rc, 0, out)
        self.assertIn("dry.db words: 7 rows", out)
        self.assertIn("virtual tables skipped (their shadow tables are digested): verses_fts", out)
        self.assertNotIn("= built's: NO", out)
        b = sqlite3.connect(os.path.join(self.run_dir, "before.db"))
        self.assertEqual(b.execute("SELECT _rowid, english_head_norm FROM words ORDER BY 1").fetchall()[0], (10, None))
        self.assertEqual(b.execute("SELECT count(*) FROM pn_binding").fetchone()[0], 2)
        b.close()
        d = sqlite3.connect(self.dry())
        self.assertEqual(sorted(r[0] for r in d.execute("SELECT name FROM sqlite_master WHERE type='index'")),
                         ["idx_bsbwords_norm", "idx_kjvwords_norm", "idx_words_ehnorm"])
        self.assertEqual([r[0] for r in d.execute("SELECT id FROM words ORDER BY id")], [10, 11, 12, 13, 14, 15, 16])
        d.close()
        rc, out = self.prep()
        self.assertEqual(rc, 1)
        self.assertIn("already exists", out)

    def test_prep_missing_table_or_column(self):
        rc, out = run("prep", "--tag", TAG, "--built", self.built, "--dir", self.run_dir, "--copy", "words,nope")
        self.assertEqual(rc, 1)
        self.assertIn("built has no table nope", out)
        rc, out = run("prep", "--tag", TAG, "--built", self.built, "--dir", self.run_dir, "--copy", "words",
                      "--save", "words:nope_norm")
        self.assertEqual(rc, 1)
        self.assertIn("no column(s) ['nope_norm']", out)

    def test_dry_delta_same_check(self):
        self.assertEqual(self.prep()[0], 0)
        step11(self.dry())
        rc, out = self.delta("d1.tsv")
        self.assertEqual(rc, 0, out)
        self.assertIn("words (key id): rows 7 -> 7 - changed 5, added 0, removed 0", out)
        self.assertIn("kjv_words (key word_id): rows 3 -> 3 - changed 0", out)
        self.assertIn("bsb_words (key word_id): rows 3 -> 3 - changed 0", out)
        self.assertIn("by class: changed english_head_norm 5", out)
        self.assertIn("by class: english_head_norm: NULL -> value 5", out)
        with open(os.path.join(self.d, "d1.tsv"), encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertEqual(len(lines), 6)
        self.assertEqual(sorted(l.split("\t")[2] for l in lines[1:]), ["(10,)", "(11,)", "(12,)", "(13,)", "(16,)"])
        sha = out.split("sha256 ")[1].split()[0]
        rc, out2 = self.delta("d2.tsv", "--expect-sha", sha)
        self.assertEqual(rc, 0, out2)
        rc, out3 = self.delta("d3.tsv", "--expect-sha", "0" * 64)
        self.assertEqual(rc, 1)
        self.assertIn("delta file sha256", out3)
        rc, out4 = self.delta("d4.tsv", "--zero")
        self.assertEqual(rc, 1)
        self.assertIn("5 difference(s), expected 0", out4)
        # built untouched by all of the above
        rc, out = run("same", "--tag", TAG, "--built", self.built, "--dir", self.run_dir)
        self.assertEqual(rc, 0, out)
        self.assertIn("differences 0 (expect 0)", out)
        # the apply
        step11(self.built)
        rc, out = self.check()
        self.assertEqual(rc, 0, out)
        self.assertIn("written table words: built 7 rows", out)
        self.assertIn("= the dry run: yes", out)
        self.assertTrue(out.rstrip().endswith("T11 CHECK: OK"))
        # same now STOPs: built changed since prep
        rc, out = run("same", "--tag", TAG, "--built", self.built, "--dir", self.run_dir)
        self.assertEqual(rc, 1)
        self.assertIn("table words:", out)

    def test_check_catches(self):
        self.assertEqual(self.prep()[0], 0)
        step11(self.dry())
        step11(self.built)
        c = sqlite3.connect(self.built)
        c.execute("UPDATE verses SET text='x' WHERE id=2")
        c.execute("UPDATE words SET english_head_norm='zzz' WHERE id=12")
        c.commit()
        c.close()
        rc, out = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("table verses:", out)
        self.assertIn("words on built differs from the dry run", out)
        self.assertIn("words CHANGED (12,) [english_head_norm]: ('son',) -> ('zzz',)", out)
        self.assertTrue(os.path.isfile(os.path.join(self.run_dir, "check_delta_words.tsv")))
        self.assertIn("T11 CHECK: FAIL", out)

    def test_check_journal_and_dirty(self):
        self.assertEqual(self.prep()[0], 0)
        step11(self.dry())
        step11(self.built)
        with open(os.path.join(self.repo, "scripts", "x.py"), "w", newline="\n") as f:
            f.write("x = 3\n")
        rc, out = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("scripts/tests dirty", out)
        git(self.repo, "checkout", "--", "scripts")
        open(self.built + "-journal", "wb").close()
        rc, out = self.check()
        self.assertEqual(rc, 1)

    def test_delta_natural_key(self):
        self.assertEqual(self.prep()[0], 0)
        other = os.path.join(self.d, "other.db")
        make_built(other)
        c = sqlite3.connect(other)
        c.execute("INSERT INTO pn_binding VALUES (1,1,1,'adam',1)")      # a duplicated row
        c.execute("UPDATE pn_binding SET name='Eve' WHERE name='eve'")    # case-only, NOCASE column
        c.execute("INSERT INTO pn_binding VALUES (2,1,1,'cain',1)")       # added
        c.commit()
        c.close()
        rc, out = self.delta("n1.tsv", a=self.built, b=other, tables=("pn_binding:book+chapter+verse",))
        self.assertEqual(rc, 0, out)
        self.assertIn("pn_binding (key book+chapter+verse): rows 2 -> 4 - changed 2, added 1, removed 0", out)
        self.assertIn("changed _n 1", out)
        self.assertIn("changed name 1", out)
        rc, out = self.delta("n2.tsv", a=other, b=self.built, tables=("pn_binding",))
        self.assertEqual(rc, 0, out)
        self.assertIn("pn_binding (key _rowid)", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
