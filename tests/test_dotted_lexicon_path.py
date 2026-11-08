"""build_dotted_lexicon.py opens ONLY the db path it is given (ruling 2026-11-07).

The old script hard-wired ~/bible-db/bible.db (LIVE) and ignored any path argument, so a
"run it on the copy" command wrote live. These tests plant a decoy "live" bible.db at that
old default (under a temp HOME/USERPROFILE) AND in the working folder, run the real script
as a subprocess, and assert by mtime + sha256 that the decoys are never opened or written:
  1. given a copy + --apply: the copy gets dotted_lexicon, the decoys are byte- and
     time-identical;
  2. no path: refuses (exit 2), decoys untouched;
  3. a path that does not exist: refuses (exit 2), and no empty file is created.
"""
import hashlib
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(ROOT, "scripts", "build_dotted_lexicon.py")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_dotted_lexicon as bdl  # noqa: E402


def _mkdb(path, with_table_row=False):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE words (strongs TEXT, strongs_base TEXT)")
    conn.execute("CREATE TABLE lexicon (strongs_g TEXT, lemma TEXT)")
    conn.execute("CREATE TABLE abp_ext (strongs TEXT, def_html TEXT)")
    conn.executemany("INSERT INTO words VALUES (?,?)", [
        ("1390.1", "G1390"), ("1390.1", "G1390"), ("303.1", "G303"), ("2316", "G2316"),
    ])
    conn.executemany("INSERT INTO lexicon VALUES (?,?)", [("G1390", "δόμα"), ("G303", "ἀνά")])
    if with_table_row:
        conn.execute("CREATE TABLE dotted_lexicon (strongs TEXT PRIMARY KEY, lemma TEXT, translit TEXT)")
        conn.execute("INSERT INTO dotted_lexicon VALUES ('G9999.9', 'decoy', 'decoy')")
    conn.commit()
    conn.close()


def _stamp(path):
    with open(path, "rb") as f:
        return os.stat(path).st_mtime_ns, hashlib.sha256(f.read()).hexdigest()


class DottedLexiconPath(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.home = os.path.join(t, "home")
        os.makedirs(os.path.join(self.home, "bible-db"))
        self.cwd = os.path.join(t, "work")
        os.makedirs(self.cwd)
        # Decoy "live" files: the old hard-wired default, and a bible.db in the working folder.
        self.decoys = [os.path.join(self.home, "bible-db", "bible.db"),
                       os.path.join(self.cwd, "bible.db")]
        for d in self.decoys:
            _mkdb(d, with_table_row=True)
        self.before = {d: _stamp(d) for d in self.decoys}
        self.copy = os.path.join(t, "copy", "bible_test.db")
        os.makedirs(os.path.dirname(self.copy))
        _mkdb(self.copy)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, *args):
        # PYTHONIOENCODING is for the CHILD only: its dry-run/--diff output prints Greek, which a
        # Windows cp1252 console can't encode (PA's console is UTF-8). The test runner itself is
        # untouched, so a real crash still fails loudly.
        env = dict(os.environ, HOME=self.home, USERPROFILE=self.home, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=self.cwd, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def _assert_decoys_untouched(self):
        for d in self.decoys:
            self.assertEqual(_stamp(d), self.before[d], f"decoy live db was touched: {d}")

    def test_apply_on_copy_never_touches_live(self):
        r = self._run(self.copy, "--apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        conn = sqlite3.connect(self.copy)
        got = {row[0] for row in conn.execute("SELECT strongs FROM dotted_lexicon")}
        conn.close()
        want = {"G" + n for n in (*bdl.NUMERAL_OVERRIDES, *bdl.PHRASE_OVERRIDES, *bdl.HAND_OVERRIDES)}
        self.assertEqual(got, want)
        self.assertIn(self.copy, r.stdout)
        self._assert_decoys_untouched()

    def test_diff_on_copy_never_touches_live(self):
        conn = sqlite3.connect(self.copy)
        conn.execute("CREATE TABLE dotted_lexicon (strongs TEXT PRIMARY KEY, lemma TEXT, translit TEXT)")
        conn.commit()
        conn.close()
        before_copy = _stamp(self.copy)
        r = self._run(self.copy, "--diff")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(_stamp(self.copy), before_copy, "--diff wrote the copy")
        self._assert_decoys_untouched()

    def test_no_path_refuses(self):
        r = self._run("--apply")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("required", r.stdout)
        self._assert_decoys_untouched()

    def test_missing_path_refuses_and_creates_nothing(self):
        ghost = os.path.join(self.tmp.name, "no_such.db")
        r = self._run(ghost, "--apply")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse(os.path.exists(ghost), "refusal created an empty db file")
        self._assert_decoys_untouched()

    def test_db_arg(self):
        self.assertIsNone(bdl.db_arg(["x", "--apply"]))
        self.assertEqual(bdl.db_arg(["x", "--diff", "a.db"]), "a.db")


if __name__ == "__main__":
    unittest.main()
