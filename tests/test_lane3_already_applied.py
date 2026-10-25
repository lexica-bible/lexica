"""Locked tests for fix_lane3_star_merges.py's already-applied detection (rebuild chain step 8,
CHARTER_rebuild_trap_fix.md G4). The chain's re-run passes only on the script's own counts, so the
three outcomes must be told apart — and each must fire on a planted case:

  fresh copy        -> "N verse(s) patched, 0 already applied, 0 skipped"
  second run        -> "0 verse(s) patched, N already applied, 0 skipped"
  state drifted     -> "0 verse(s) patched, 0 already applied, 1 skipped"  (never "already")
  dry run           -> writes nothing

Runs the REAL script on a throwaway database (no bible.db needed).
Run:  python tests/test_lane3_already_applied.py
"""
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "fix_lane3_star_merges.py")

# Shape of the real Mat 9:11 entry: a merged cell split onto two blank slots, new 3-slot bracket.
FIX = {"_comment": "test fixture", "Mat 9:11": {"new_bids": [2], "join_bids": [], "ops": [
    {"pos": 1, "sbase": "G1492", "old_eng": "the Pharisees seeing,", "old_gpos": None,
     "old_bid": None, "new_eng": "seeing,", "new_head": "seeing", "new_gpos": 3, "new_bid": 2},
    {"pos": 2, "sbase": "G3588", "old_eng": None, "old_gpos": None, "old_bid": None,
     "new_eng": "the", "new_head": None, "new_gpos": 1, "new_bid": 2},
    {"pos": 3, "sbase": "*", "old_eng": None, "old_gpos": None, "old_bid": None,
     "new_eng": "Pharisees", "new_head": "pharisees", "new_gpos": 2, "new_bid": 2}]}}
WORDS = [(1, 1, "the Pharisees seeing,", "seeing", "G1492", None, None),
         (1, 2, None, None, "G3588", None, None),
         (1, 3, None, None, "*", None, None),
         (1, 4, "said", "said", "G2036", None, None)]


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Lane3AlreadyApplied(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "copy.sqlite")
        self.fixes = os.path.join(self.tmp, "fixes.json")
        with open(self.fixes, "w", encoding="utf-8") as f:
            json.dump(FIX, f, ensure_ascii=False)
        c = sqlite3.connect(self.db)
        c.executescript("""
            CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
            CREATE TABLE words(id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT,
                               english_head TEXT, strongs_base TEXT, greek_pos INT, bracket_id INT);""")
        c.execute("INSERT INTO verses VALUES (1, 'Mat', 9, 11, 'the Pharisees seeing, said')")
        c.executemany("INSERT INTO words (verse_id, position, english, english_head, strongs_base,"
                      " greek_pos, bracket_id) VALUES (?,?,?,?,?,?,?)", WORDS)
        c.commit()
        c.close()

    def run_script(self, *extra):
        p = subprocess.run([sys.executable, SCRIPT, self.db, "--fixes", self.fixes, *extra],
                           capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def test_dry_run_writes_nothing(self):
        before = digest(self.db)
        out = self.run_script()
        self.assertIn("DRY-RUN — 1 verse(s) ready, 0 already applied, 0 skipped", out)
        self.assertEqual(before, digest(self.db))

    def test_apply_then_rerun_is_already_applied(self):
        out = self.run_script("--apply")
        self.assertIn("APPLIED — 1 verse(s) patched, 0 already applied, 0 skipped", out)
        out = self.run_script("--apply")
        self.assertIn("ALREADY Mat 9:11: already applied", out)
        self.assertIn("APPLIED — 0 verse(s) patched, 1 already applied, 0 skipped", out)

    def test_drifted_state_is_a_skip_not_already(self):
        self.run_script("--apply")
        c = sqlite3.connect(self.db)
        c.execute("UPDATE words SET english='seeing' WHERE position=1")   # one cell drifted
        c.commit()
        c.close()
        out = self.run_script("--apply")
        self.assertNotIn("ALREADY", out)
        self.assertIn("SKIP Mat 9:11", out)
        self.assertIn("APPLIED — 0 verse(s) patched, 0 already applied, 1 skipped", out)


if __name__ == "__main__":
    unittest.main()
