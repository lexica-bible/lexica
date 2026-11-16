"""Locked tests for the "spent by lane-3" rule (scripts/lane3_spent.py, DESIGN §9.153, option B)
in BOTH users: scripts/apply_abp_corrections.py (the REAL script, run as a subprocess) and
cert_invariants.check_corrections (the real function). Reads the REAL three lane-3 files.

Each case is built on a throwaway database shaped like Heb 11:24 (EU-Heb11:24 @7 english
"of Pharoah's daughter," -> "of Pharaoh's daughter,"; lane3_star_fixes2.json then splits @7 into
"daughter," and @8 "of Pharaoh's"):

  known positive   after 8b.2a: apply prints "~~ ... spent by lane-3", its own count, exit 0 —
                   never counted as already-applied; cert green with the spent row named
  pre-8b.2a copy   the cell holds the source value: the apply APPLIES it (spent 0); then the REAL
                   lane-3 script splits the cell; then the apply reports it spent
  still red        any one condition missing -> LOUD SKIP (exit 1) and cert red:
                   cell differs · corrected value != the op's old value · slot not in the op's
                   new state · english_head row · a matching row NOT declared · lane-3 file sha
                   changed (rule OFF) · spent count != the declared count

Run:  python tests/test_lane3_spent.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)
from cert_invariants import check_corrections  # noqa: E402
from lane3_spent import Lane3Ops, LANE3_PINS  # noqa: E402

APPLY = os.path.join(SCRIPTS, "apply_abp_corrections.py")
LANE3 = os.path.join(SCRIPTS, "fix_lane3_star_merges.py")

SRC = "of Pharoah's daughter,"
COR = "of Pharaoh's daughter,"
# (position, english, english_head, strongs_base, greek_pos, bracket_id)
BEFORE = [(6, "son", "son", "G5207", None, None), (7, SRC, "daughter", "G2364", None, None),
          (8, None, None, "*", None, None)]
AFTER_STEP7 = [(6, "son", "son", "G5207", None, None), (7, COR, "daughter", "G2364", None, None),
               (8, None, None, "*", None, None)]
AFTER_8B2A = [(6, "son", "son", "G5207", None, None), (7, "daughter,", "daughter", "G2364", 2, 2),
              (8, "of Pharaoh's", "pharaohs", "*", 1, 2)]
TEXT = "By belief Moses, having become great, denied to be called son of Pharaoh's daughter,"


def _fixes2_other_op():
    """A REAL fixes2 op other than Heb 11:24 that has an english old value."""
    with open(os.path.join(SCRIPTS, "lane3_star_fixes2.json"), encoding="utf-8") as f:
        d = json.load(f)
    for verse, spec in d.items():
        if verse in ("_comment", "Heb 11:24"):
            continue
        for op in spec["ops"]:
            if op["old_eng"]:
                return verse, op
    raise AssertionError("no other fixes2 op with an english old value")


class Lane3Spent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "copy.sqlite")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make(self, words, corrections, extra_verses=()):
        c = sqlite3.connect(self.db)
        c.executescript("""
            CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
            CREATE TABLE words(id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT,
                               english_head TEXT, strongs_base TEXT, greek_pos INT, bracket_id INT);
            CREATE TABLE abp_corrections(book TEXT, chapter INT, verse INT, position INT,
                field TEXT, source_value TEXT, corrected_value TEXT, status TEXT,
                applied_at TEXT, ledger_ref TEXT, reason TEXT);""")
        c.execute("INSERT INTO verses VALUES (1,'Heb',11,24,?)", (TEXT,))
        c.executemany("INSERT INTO words (verse_id, position, english, english_head, strongs_base,"
                      " greek_pos, bracket_id) VALUES (1,?,?,?,?,?,?)", words)
        for vid, (book, ch, vs), ws in extra_verses:
            c.execute("INSERT INTO verses VALUES (?,?,?,?,'')", (vid, book, ch, vs))
            c.executemany("INSERT INTO words (verse_id, position, english, english_head,"
                          " strongs_base, greek_pos, bracket_id) VALUES (?,?,?,?,?,?,?)",
                          [(vid,) + w for w in ws])
        c.executemany("INSERT INTO abp_corrections VALUES (?,?,?,?,?,?,?,'active','ingest',?,'t')",
                      corrections)
        c.commit()
        c.close()

    def apply(self, *extra):
        p = subprocess.run([sys.executable, APPLY, self.db, "--only", "words", *extra],
                           capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        return p.returncode, p.stdout + p.stderr

    def cert(self, expected_active=1, expected_spent=1, lane3=None):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        notes = []
        try:
            return check_corrections(c, expected_active=expected_active,
                                     expected_spent=expected_spent, notes=notes,
                                     lane3=lane3), notes
        finally:
            c.close()

    def cell(self, pos=7, col="english"):
        c = sqlite3.connect(self.db)
        try:
            return c.execute(f"SELECT {col} FROM words WHERE verse_id=1 AND position=?",
                             (pos,)).fetchone()[0]
        finally:
            c.close()

    ROW = ("Heb", 11, 24, 7, "english", SRC, COR, "EU-Heb11:24")

    # ── known positive ────────────────────────────────────────────────────────────────────
    def test_known_positive_apply(self):
        self.make(AFTER_8B2A, [self.ROW])
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        self.assertIn("~~ Heb 11:24 pos 7 english: spent by lane-3 8b.2a", out)
        self.assertIn("lane3_star_fixes2.json op pos 7", out)
        self.assertIn("declared DESIGN §9.153", out)
        self.assertIn("would apply 0 · already-applied 0 · spent by lane-3: 1 · LOUD-SKIPPED 0",
                      out)
        for name, sha in LANE3_PINS:
            self.assertIn(f"lane-3 file {name}: sha256 {sha} = pin", out)
        self.assertIn("spent-by-lane-3 rule: ON", out)
        self.assertEqual(self.cell(), "daughter,")          # nothing written

    def test_known_positive_cert(self):
        self.make(AFTER_8B2A, [self.ROW])
        probs, notes = self.cert()
        self.assertEqual(probs, [])
        self.assertIn("spent by lane-3: 1 (declared 1)", notes)
        self.assertTrue(any(n.startswith("Heb 11:24 pos 7 english: spent by lane-3") for n in notes),
                        notes)

    # ── pre-8b.2a copy still applies; then the REAL lane-3 run makes it spent ──────────────────
    def test_pre_8b2a_copy_applies_then_spent(self):
        self.make(BEFORE, [self.ROW])
        rc, out = self.apply("--apply")
        self.assertEqual(rc, 0, out)
        self.assertIn("applied 1 · already-applied 0 · spent by lane-3: 0 · LOUD-SKIPPED 0", out)
        self.assertEqual(self.cell(), COR)
        probs, _ = self.cert(expected_spent=0)               # holds its corrected value
        self.assertEqual(probs, [])
        p = subprocess.run([sys.executable, LANE3, self.db, "--apply", "--fixes",
                            "lane3_star_fixes2.json"], capture_output=True, text=True,
                           encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertIn("=== Heb 11:24 ===", p.stdout, p.stdout + p.stderr)
        self.assertEqual(self.cell(), "daughter,")
        rc, out = self.apply("--apply")
        self.assertEqual(rc, 0, out)
        self.assertIn("applied 0 · already-applied 0 · spent by lane-3: 1 · LOUD-SKIPPED 0", out)
        probs, _ = self.cert()
        self.assertEqual(probs, [])

    def test_after_step7_is_already_applied_not_spent(self):
        self.make(AFTER_STEP7, [self.ROW])
        rc, out = self.apply()
        self.assertEqual(rc, 0, out)
        self.assertIn("would apply 0 · already-applied 1 · spent by lane-3: 0 · LOUD-SKIPPED 0", out)

    # ── anything else still red ───────────────────────────────────────────────────────────
    def assert_red(self, words, row, cert_lane3=None, extra_verses=()):
        self.make(words, [row], extra_verses)
        rc, out = self.apply()
        self.assertEqual(rc, 1, out)
        self.assertIn("!! SKIP", out)
        self.assertIn("spent by lane-3: 0 · LOUD-SKIPPED 1", out)
        probs, _ = self.cert(expected_spent=0, lane3=cert_lane3)
        self.assertEqual(len(probs), 1, probs)
        return out, probs

    def test_red_cell_differs(self):
        w = [r if r[0] != 7 else (7, "daughter", "daughter", "G2364", 2, 2) for r in AFTER_8B2A]
        self.assert_red(w, self.ROW)

    def test_red_corrected_not_the_ops_old_value(self):
        self.assert_red(AFTER_8B2A, ("Heb", 11, 24, 7, "english", SRC, "of Pharaoh's daughter",
                                     "EU-Heb11:24"))

    def test_red_slot_not_in_new_state(self):
        for i, bad in ((4, None), (5, None), (2, "daughters"), (3, "G2365")):
            with self.subTest(column=i):
                r7 = list(AFTER_8B2A[1])
                r7[i] = bad
                w = [AFTER_8B2A[0], tuple(r7), AFTER_8B2A[2]]
                self.assert_red(w, self.ROW)
                self.tearDown()
                self.setUp()

    def test_red_english_head_row_never_spent(self):
        # corrected = the op's old english, slot in the new state: only the field rule stops it
        out, probs = self.assert_red(AFTER_8B2A, ("Heb", 11, 24, 7, "english_head", "x", COR,
                                                  "EU-test"))
        self.assertNotIn("spent-by-lane-3 rule matches", out)   # the RULE refuses, not DECLARED
        self.assertNotIn("spent-by-lane-3 rule matches", probs[0])

    def test_red_two_ops_on_one_cell(self):
        # a copy of fixes2 whose Heb 11:24 entry also sits in a second file -> (a) fails
        import hashlib
        d = os.path.join(self.tmp, "scripts")
        os.mkdir(d)
        with open(os.path.join(SCRIPTS, "lane3_star_fixes2.json"), encoding="utf-8") as f:
            heb = {"Heb 11:24": json.load(f)["Heb 11:24"]}
        files = {"one.json": json.dumps(heb).encode(), "two.json": json.dumps(heb).encode()}
        for n, raw in files.items():
            with open(os.path.join(d, n), "wb") as f:
                f.write(raw)
        pins = tuple((n, hashlib.sha256(raw).hexdigest()) for n, raw in files.items())
        one = Lane3Ops(script_dir=d, pins=pins[:1])
        two = Lane3Ops(script_dir=d, pins=pins)
        self.assertTrue(one.on and two.on)
        self.make(AFTER_8B2A, [self.ROW])
        probs, _ = self.cert(lane3=one)
        self.assertEqual(probs, [])                          # control: one op -> spent
        probs, _ = self.cert(expected_spent=0, lane3=two)
        self.assertEqual(len(probs), 1, probs)               # two ops on the cell -> red
        self.assertIn("Heb 11:24 pos 7 english: reads 'daughter,'", probs[0])

    def test_red_matching_row_not_declared(self):
        verse, op = _fixes2_other_op()
        book, rest = verse.rsplit(" ", 1)
        ch, vs = (int(x) for x in rest.split(":"))
        ws = [(op["pos"], op["new_eng"], op["new_head"], op["sbase"], op["new_gpos"],
               op["new_bid"])]
        row = (book, ch, vs, op["pos"], "english", "anything", op["old_eng"], "EU-test")
        out, probs = self.assert_red(AFTER_8B2A, row, extra_verses=[(2, (book, ch, vs), ws)])
        self.assertIn("NOT declared spent", out)
        self.assertIn("NOT declared spent", probs[0])

    def test_red_lane3_file_changed_turns_rule_off(self):
        d = os.path.join(self.tmp, "scripts")
        os.mkdir(d)
        for name, _ in LANE3_PINS:
            shutil.copy(os.path.join(SCRIPTS, name), d)
        with open(os.path.join(d, "lane3_star_fixes2.json"), "ab") as f:
            f.write(b"\n")
        lane3 = Lane3Ops(script_dir=d)
        self.assertFalse(lane3.on)
        self.assertTrue(any("lane3_star_fixes2.json" in s and "!= pin" in s for s in lane3.lines))
        self.assertTrue(any("rule: OFF" in s for s in lane3.lines))
        self.make(AFTER_8B2A, [self.ROW])
        probs, _ = self.cert(expected_spent=0, lane3=lane3)
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("Heb 11:24 pos 7 english: reads 'daughter,'", probs[0])

    def test_red_lane3_file_changed_apply_prints_off_and_skips(self):
        # the REAL apply + helper copied beside a one-byte-changed fixes2: the apply's own
        # output must show the sha mismatch, the rule OFF, and LOUD-SKIP the row (exit 1)
        d = os.path.join(self.tmp, "scripts")
        os.mkdir(d)
        for name in ("apply_abp_corrections.py", "lane3_spent.py") + tuple(n for n, _ in LANE3_PINS):
            shutil.copy(os.path.join(SCRIPTS, name), d)
        with open(os.path.join(d, "lane3_star_fixes2.json"), "ab") as f:
            f.write(b"\n")
        self.make(AFTER_8B2A, [self.ROW])
        p = subprocess.run([sys.executable, os.path.join(d, "apply_abp_corrections.py"), self.db,
                            "--only", "words"], capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        out = p.stdout + p.stderr
        self.assertEqual(p.returncode, 1, out)
        self.assertIn("lane-3 file lane3_star_fixes2.json: sha256 ", out)
        self.assertIn("!= pin e6a7efc7", out)
        self.assertIn("spent-by-lane-3 rule: OFF", out)
        self.assertIn("!! SKIP Heb 11:24 pos 7 english", out)
        self.assertIn("spent by lane-3: 0 · LOUD-SKIPPED 1", out)

    def test_red_lane3_file_missing_turns_rule_off(self):
        lane3 = Lane3Ops(script_dir=self.tmp)
        self.assertFalse(lane3.on)
        self.assertTrue(any("MISSING" in s for s in lane3.lines))

    def test_red_spent_count_not_the_declared_count(self):
        self.make(AFTER_8B2A, [self.ROW])
        probs, _ = self.cert(expected_spent=0)
        self.assertEqual(probs, ["1 row(s) spent by lane-3, declared 0"])
        self.tearDown()
        self.setUp()
        self.make(AFTER_STEP7, [self.ROW])                   # holds corrected -> 0 spent
        probs, _ = self.cert(expected_spent=1)
        self.assertEqual(probs, ["0 row(s) spent by lane-3, declared 1"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
