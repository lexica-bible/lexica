"""Locked tests for gate_greek_header.py --declared (CHARTER_edition_upgrade.md
§4.5; Q8 ruled 2026-10-30 "land --declared before the rebuild, own checkpoint";
the four checkpoints ruled 10/30: tight key book+chapter+verse+name, gate before
step 9, fixture committed, test lands with the change).

Four cases. The ruled three (10/30) are 1-3; CASE 4 EXTENDS THEM by the
2026-10-31 ruling ("a declared row with no actual delta = FAIL naming the row"):
  1. no flag        = today's behaviour — proven against the sibling
                      tests/test_gate_greek_header.py fixture and ITS expectation
                      lines (not a new baseline), plus today's gate-A wording on a
                      pn_binding delta, and no DECLARED/declared text anywhere.
  2. declared match = gate A PASS, on the COMMITTED worked example
                      tests/fixtures/rebuild_trap/declared_deltas_20261025.json
                      (its pn_binding member rows drive the pass; only the
                      words/verses counts are re-pointed at the six-row fixture,
                      since 626,309 rows cannot live in a test db).
  3. one undeclared differing row  = gate A FAIL, today's wording
                      ("CHANGED — automatic stop"), the row named.
  4. a declared row with no delta  = gate A FAIL naming the row ("NO DELTA").

Runs the REAL gate script on tiny synthetic files (no bible.db). Asserts the
gate-A lines, not the exit code (gate C legitimately fails on synthetic data).
render/hot/tier values on the synthetic Michaiah rows are placeholders — the
real values are unchanged either side and are not recorded in the repo.

Run:  python tests/test_gate_declared.py
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import test_gate_greek_header as sib          # the sibling fixture + its expectations

GATE = os.path.join(ROOT, "scripts", "gate_greek_header.py")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "rebuild_trap",
                       "declared_deltas_20261025.json")

# pn_binding rows: (book, chapter, verse, name, entity_uniq, kind, rule, render, hot, tier)
# The 3 Michaiah binds as LIVE read them before the 10/25 swap (kind/rule from
# charter §9.4 (g); entity from pn_hand_rulings.tsv) + 1 unrelated row that must
# stay untouched (and is the undeclared mover in case 3).
LIVE_BIND = [
    (12, 22, 12, "michaiah", "Micaiah@2Ki.22.12-2Ch", "ruled", "spelling-equiv", 1, 0, 1),
    (14, 17, 7,  "michaiah", "Micaiah@2Ch.17.7",      "ruled", "spelling-equiv", 1, 0, 1),
    (16, 12, 41, "michaiah", "Micaiah@Neh.12.41",     "ruled", "spelling-equiv", 1, 0, 1),
    (1,  1,  1,  "david",    "David@1Sa.16.13",       "exact", "",               1, 0, 1),
]


def after_swap(rows, which):
    """The post-10/25 shape: kind ruled -> fuzzy, rule spelling-equiv -> ''."""
    out = []
    for r in rows:
        if r[3] == "michaiah" and (r[0], r[1], r[2]) in which:
            r = r[:5] + ("fuzzy", "") + r[7:]
        out.append(r)
    return out


ALL3 = {(12, 22, 12), (14, 17, 7), (16, 12, 41)}


def build(path, ident, binds):
    sib.build_db(path, ident)
    conn = sqlite3.connect(path)
    conn.executemany("INSERT INTO pn_binding VALUES (?,?,?,?,?,?,?,?,?,?)", binds)
    conn.commit()
    conn.close()


def run_gate(live, scr, declared=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    cmd = [sys.executable, GATE, live, scr]
    if declared:
        cmd += ["--declared", declared]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          cwd=ROOT, env=env).stdout


class TestGateDeclared(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.live = os.path.join(cls.tmp, "live.db")
        build(cls.live, sib.LIVE_IDENT, LIVE_BIND)
        # identity table identical to live (keys and values): the declaration
        # says pn_greek_identity keys do not move, and gate A is what is under test.
        cls.scr_match = os.path.join(cls.tmp, "scr_match.db")
        build(cls.scr_match, sib.LIVE_IDENT, after_swap(LIVE_BIND, ALL3))
        cls.scr_extra = os.path.join(cls.tmp, "scr_extra.db")
        extra = after_swap(LIVE_BIND, ALL3)
        extra[3] = extra[3][:5] + ("fuzzy", "") + extra[3][7:]      # david moves, undeclared
        build(cls.scr_extra, sib.LIVE_IDENT, extra)
        cls.scr_short = os.path.join(cls.tmp, "scr_short.db")
        build(cls.scr_short, sib.LIVE_IDENT, after_swap(LIVE_BIND, ALL3 - {(16, 12, 41)}))

        # the COMMITTED worked example, counts re-pointed at this six-row fixture
        with open(FIXTURE, encoding="utf-8") as fh:
            decl = json.load(fh)
        cls.fixture_rows = decl["pn_binding"]["changed_rows"]
        decl["words"]["scratch_count"] = len(sib.WORDS)
        decl["verses"]["scratch_count"] = len(sib.VERSES)
        cls.decl_path = os.path.join(cls.tmp, "declared.json")
        with open(cls.decl_path, "w", encoding="utf-8") as fh:
            json.dump(decl, fh)

    # ── case 1: no flag = today's behaviour ──────────────────────────────────
    def test_case1_no_flag_is_todays_gate_on_the_sibling_fixture(self):
        live, scr = os.path.join(self.tmp, "sib_live.db"), os.path.join(self.tmp, "sib_scr.db")
        sib.build_db(live, sib.LIVE_IDENT)
        sib.build_db(scr, sib.SCR_IDENT)
        out = run_gate(live, scr)
        ctrl = run_gate(live, live)
        probs = [l for l in out.splitlines() if "problem:" in l]
        # the sibling's own expectation lines, unchanged
        self.assertIn("glued cure (blanked) 1", out)
        self.assertIn("gentilic drop 1", out)
        self.assertIn("pinned ruled loss 1", out)
        self.assertTrue(any("Σαμουήλ" in l and "outside the ruled classes" in l for l in probs))
        self.assertTrue(any("'PIN'" in l for l in probs))
        self.assertIn("gate B: PASS", ctrl)
        # today's gate-A wording, and no declaration vocabulary without the flag
        self.assertIn("gate A: PASS — identity layer untouched", out)
        for text in (out, ctrl):
            self.assertNotIn("DECLARED", text)
            self.assertNotIn("declared", text)

    def test_case1_no_flag_pn_binding_delta_is_todays_fail(self):
        out = run_gate(self.live, self.scr_match)
        self.assertIn("gate A: pn_binding      4 vs 4 rows — DIFFER", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)
        self.assertNotIn("declared", out)

    # ── case 2: declared match = PASS ────────────────────────────────────────
    def test_case2_declared_match_passes_gate_a(self):
        self.assertEqual(len(self.fixture_rows), 3, "the committed example declares 3 rows")
        out = run_gate(self.live, self.scr_match, self.decl_path)
        self.assertIn("DECLARED deltas: lane=", out)
        self.assertIn("gate A: pn_binding      4 vs 4 rows — 3 row(s) differ; declared 3 → MATCH", out)
        self.assertIn("gate A: PASS — identity layer as declared", out)
        self.assertNotIn("problem: undeclared", out)
        self.assertNotIn("NO DELTA", out)

    # ── case 3: one undeclared row = FAIL, today's wording ───────────────────
    def test_case3_undeclared_row_fails_naming_it(self):
        out = run_gate(self.live, self.scr_extra, self.decl_path)
        self.assertIn("4 row(s) differ; declared 3 → MISMATCH", out)
        self.assertIn("problem: undeclared row (1, 1, 1, 'david'): DIFFER", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)

    # ── case 4: declared row with no delta = FAIL naming the row (10/31) ─────
    def test_case4_declared_row_without_delta_fails_naming_it(self):
        out = run_gate(self.live, self.scr_short, self.decl_path)
        self.assertIn("2 row(s) differ; declared 3 → MISMATCH", out)
        self.assertIn("problem: declared row (16, 12, 41, 'michaiah'): NO DELTA", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)


if __name__ == "__main__":
    unittest.main()
