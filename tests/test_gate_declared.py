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
import hashlib
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


# ── DESIGN §9.92 G2: pn_binding.renamed_rows (a rename = ONE declared event) ──
OLD = (40, 1, 12, "zerubbabel", "Zerubbabel@1Ch.3.19", "exact", "", 1, 0, 1)
NEW = (40, 1, 12, "zorobabel",  "Zerubbabel@1Ch.3.19", "exact", "", 1, 0, 1)
RENAME = {"book": 40, "chapter": 1, "verse": 12, "old_name": "zerubbabel",
          "new_name": "zorobabel", "changes": {},
          "unchanged": ["entity_uniq", "kind", "rule", "render", "hot", "tier"]}


class TestGateDeclaredRenames(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.live = os.path.join(cls.tmp, "live.db")
        build(cls.live, sib.LIVE_IDENT, LIVE_BIND + [OLD])
        swapped = after_swap(LIVE_BIND, ALL3)
        cls.scr_pass = os.path.join(cls.tmp, "scr_pass.db")
        build(cls.scr_pass, sib.LIVE_IDENT, swapped + [NEW])
        cls.scr_half = os.path.join(cls.tmp, "scr_half.db")      # old gone, new never added
        build(cls.scr_half, sib.LIVE_IDENT, swapped)
        cls.scr_extra = os.path.join(cls.tmp, "scr_extra.db")    # new half moves kind too
        build(cls.scr_extra, sib.LIVE_IDENT, swapped + [NEW[:5] + ("fuzzy",) + NEW[6:]])
        with open(FIXTURE, encoding="utf-8") as fh:
            decl = json.load(fh)
        decl["words"]["scratch_count"] = len(sib.WORDS)
        decl["verses"]["scratch_count"] = len(sib.VERSES)
        decl["pn_binding"]["renamed_rows"] = [RENAME]
        cls.decl_path = os.path.join(cls.tmp, "declared_rename.json")
        with open(cls.decl_path, "w", encoding="utf-8") as fh:
            json.dump(decl, fh)

    def test_rename_pass(self):
        out = run_gate(self.live, self.scr_pass, self.decl_path)
        self.assertIn("5 row(s) differ; declared 3 + 1 rename(s) → MATCH", out)
        self.assertIn("gate A: PASS — identity layer as declared", out)
        self.assertNotIn("problem:", out.split("gate B:")[0])

    def test_rename_missing_half_fails(self):
        out = run_gate(self.live, self.scr_half, self.decl_path)
        self.assertIn("→ MISMATCH", out)
        self.assertIn("problem: renamed row (40, 1, 12) 'zerubbabel' -> 'zorobabel': "
                      "new half missing (needs (40, 1, 12, 'zorobabel') on scratch only)", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)

    def test_rename_extra_diff_fails(self):
        out = run_gate(self.live, self.scr_extra, self.decl_path)
        self.assertIn("problem: renamed row (40, 1, 12) 'zerubbabel' -> 'zorobabel' col kind: "
                      "'exact' -> 'fuzzy' changed but not declared", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)

    def test_unpaired_one_sided_row_still_fails_without_rename(self):
        with open(self.decl_path, encoding="utf-8") as fh:
            decl = json.load(fh)
        del decl["pn_binding"]["renamed_rows"]
        p = os.path.join(self.tmp, "declared_norename.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(decl, fh)
        out = run_gate(self.live, self.scr_pass, p)
        self.assertIn("problem: undeclared row (40, 1, 12, 'zerubbabel'): DIFFER", out)
        self.assertIn("problem: undeclared row (40, 1, 12, 'zorobabel'): DIFFER", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)


# ── DESIGN §9.92 G3: the gate_b block (pins + changed_rows) ──────────────────
# One header row changes in an allowed class (Gen 1:1 'David', glued -> blank =
# glued cure (blanked)); every other identity row is the same on both copies.
SCR_ONE = [sib.SCR_IDENT[0]] + sib.LIVE_IDENT[1:]
CODE_PINS = {"pinned ruled loss": 17, "glued cure (blanked)": 20,
             "glued cure (replaced)": 94, "glued kept as-is": 30}
TRUE_PINS = {"pinned ruled loss": 0, "glued cure (blanked)": 1,
             "glued cure (replaced)": 0, "glued kept as-is": 0}
DAVID = {"book": "Gen", "chapter": 1, "verse": 1, "position": 1, "name": "david"}


class TestGateDeclaredGateB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.live = os.path.join(cls.tmp, "live.db")
        cls.scr = os.path.join(cls.tmp, "scr.db")
        build(cls.live, sib.LIVE_IDENT, LIVE_BIND)
        build(cls.scr, SCR_ONE, LIVE_BIND)

    def gate(self, gate_b):
        decl = {"lane": "test", "declared_by": "test", "receipt": "test",
                "words": {"scratch_count": len(sib.WORDS)},
                "verses": {"scratch_count": len(sib.VERSES)},
                "abp_surface": {"identical": True}, "tipnr_entities": {"identical": True},
                "pn_binding": {"identical": True},
                "pn_greek_identity": {"keys_only_in_live": 0, "keys_only_in_scratch": 0,
                                      "key_moves_file": None}}
        if gate_b is not None:
            decl["gate_b"] = gate_b
        p = os.path.join(self.tmp, "d.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(decl, fh)
        out = run_gate(self.live, self.scr, p)
        self.assertIn("gate A: PASS — identity layer as declared", out)
        return out

    def test_block_absent_keeps_code_pins(self):
        out = self.gate(None)
        self.assertIn("problem: ('PIN', 'glued cure (blanked)', 'expected 20, got 1')", out)
        self.assertNotIn("declared changed_rows", out)
        self.assertIn("gate B: FAIL", out)

    def test_v1_code_pins_and_empty_list_fails_naming_the_row(self):
        out = self.gate({"pins": CODE_PINS, "changed_rows": []})
        self.assertIn("gate B: declared changed_rows 0 · header rows changed 1", out)
        self.assertIn("problem: ((1, 1), 'undeclared', "
                      "'header row changed but not in gate_b.changed_rows')", out)
        self.assertIn("problem: ('PIN', 'glued cure (blanked)', 'expected 20, got 1')", out)
        self.assertIn("gate B: FAIL", out)

    def test_redeclared_pins_with_named_row_pass(self):
        out = self.gate({"pins": TRUE_PINS, "changed_rows": [DAVID]})
        self.assertIn("gate B: declared changed_rows 1 · header rows changed 1", out)
        self.assertIn("gate B: PASS", out)

    def test_declared_row_without_change_fails(self):
        tyre = {"book": "Gen", "chapter": 1, "verse": 4, "position": 1, "name": "tyre"}
        out = self.gate({"pins": TRUE_PINS, "changed_rows": [DAVID, tyre]})
        self.assertIn("problem: ('GATE_B', ('Gen', 1, 4, 1), "
                      "'declared header row: NO DELTA (live == scratch)')", out)
        self.assertIn("gate B: FAIL", out)

    def test_declared_name_must_be_the_slot_label(self):
        out = self.gate({"pins": TRUE_PINS, "changed_rows": [dict(DAVID, name="saul")]})
        self.assertIn("declared name 'saul' != slot label 'David'", out)
        self.assertIn("gate B: FAIL", out)

    def test_pins_must_name_all_four(self):
        out = self.gate({"pins": {"pinned ruled loss": 0}, "changed_rows": [DAVID]})
        self.assertIn("problem: ('PIN', 'gate_b.pins', \"must name exactly", out)
        self.assertIn("gate B: FAIL", out)


# ── DESIGN §9.94 (c) G4: per-table key_moves_file (abp_surface in gate A) ────
LIVE_SURF = [(1, 1, "a", "ta"), (1, 2, "b", "tb"), (2, 5, "c", "tc"), (3, 1, "d", "td")]
SCR_SURF = [(1, 1, "b", "tb"), (1, 2, "a", "ta"), (2, 6, "c", "tc"), (3, 1, "d", "td")]   # swap + single move
MOVES = [(1, 1, 2), (1, 2, 1), (2, 5, 6)]


def build_surf(path, surf, ident=None):
    build(path, ident or sib.LIVE_IDENT, LIVE_BIND)
    conn = sqlite3.connect(path)
    conn.executemany("INSERT INTO abp_surface VALUES (?,?,?,?)", surf)
    conn.commit()
    conn.close()


class TestGateDeclaredKeyMoves(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.live = os.path.join(cls.tmp, "live.db")
        build_surf(cls.live, LIVE_SURF)
        cls.scr = os.path.join(cls.tmp, "scr.db")
        build_surf(cls.scr, SCR_SURF)
        cls.scr_extra = os.path.join(cls.tmp, "scr_extra.db")       # one more form differs
        build_surf(cls.scr_extra, SCR_SURF[:3] + [(3, 1, "dX", "td")])

    def moves_file(self, name, rows):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("verse_id\told_pos\tnew_pos\n")
            for r in rows:
                fh.write("%d\t%d\t%d\n" % r)
        return p

    def gate(self, scr, abp_moves, pgi=None):
        decl = {"lane": "test", "declared_by": "test", "receipt": "test",
                "words": {"scratch_count": len(sib.WORDS)},
                "verses": {"scratch_count": len(sib.VERSES)},
                "abp_surface": {"key_moves_file": abp_moves},
                "tipnr_entities": {"identical": True}, "pn_binding": {"identical": True},
                "pn_greek_identity": pgi or {"keys_only_in_live": 0, "keys_only_in_scratch": 0,
                                             "key_moves_file": None}}
        p = os.path.join(self.tmp, "d.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(decl, fh)
        return run_gate(self.live, scr, p)

    def test_moves_pass(self):
        out = self.gate(self.scr, self.moves_file("m.tsv", MOVES))
        self.assertIn("gate A: abp_surface     4 vs 4 rows — 3 declared key move(s) → MATCH", out)
        self.assertIn("gate A: PASS — identity layer as declared", out)

    def test_moves_missing_source_row_fails(self):
        out = self.gate(self.scr, self.moves_file("m2.tsv", MOVES + [(4, 1, 2)]))
        self.assertIn("problem: declared move (4, 1) -> (4, 2): source row missing on live", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)

    def test_moves_extra_diff_fails(self):
        out = self.gate(self.scr_extra, self.moves_file("m3.tsv", MOVES))
        self.assertIn("→ MISMATCH", out)
        self.assertIn("problem: row (3, 1): live after moves (3, 1, 'd', 'td') vs scratch (3, 1, 'dX', 'td')", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)

    def test_pn_greek_identity_moves_still_read(self):
        # gate B's own moves (shared reader): live slot (1,1) re-keyed to (1,3) on scratch
        moved_ident = [(1, 3) + sib.LIVE_IDENT[0][2:]] + sib.LIVE_IDENT[1:]
        scr = os.path.join(self.tmp, "scr_pgi.db")
        build_surf(scr, LIVE_SURF, ident=moved_ident)
        out = self.gate(scr, self.moves_file("m4.tsv", []),
                        pgi={"keys_only_in_live": 1, "keys_only_in_scratch": 1,
                             "key_moves_file": self.moves_file("pgi.tsv", [(1, 1, 3)])})
        self.assertIn("gate A: abp_surface     4 vs 4 rows — 0 declared key move(s) → MATCH", out)
        self.assertNotIn("KEYSET", out)
        bad = self.gate(scr, self.moves_file("m5.tsv", []),
                        pgi={"keys_only_in_live": 1, "keys_only_in_scratch": 1,
                             "key_moves_file": self.moves_file("pgi2.tsv", [(1, 1, 4)])})
        self.assertIn("declared key moves != actual only-live/only-scratch keys", bad)


# ── G5 (ruled 2026-11-07, DESIGN §9.101): pn_binding.delta_file + sha256 ─────
# src -> built: zerubbabel REMOVED, zorobabel ADDED (one-sided rows, which
# changed_rows cannot declare); everything else the same on both copies.
DF_HEADER = "kind\tbook\tchapter\tverse\tname\tclass\tbefore\tafter\n"
DF_ROWS = [("REMOVED", OLD, None, [OLD]), ("ADDED", NEW, [NEW], None)]


def delta_line(kind, row, before, after):
    """One delta-file line in the 8B3c helper's own format (DRAFT_stageC_outline.md:5303)."""
    if kind == "ADDED":
        before, after = None, [row]
    elif kind == "REMOVED":
        before, after = [row], None
    return "%s\t%s\t%s\t%s\t%s\t%s\t%r\t%r\n" % (kind, row[0], row[1], row[2], row[3],
                                                "x", before, after)


class TestGateDeclaredDeltaFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.live = os.path.join(cls.tmp, "live.db")
        build(cls.live, sib.LIVE_IDENT, LIVE_BIND + [OLD])
        cls.scr = os.path.join(cls.tmp, "scr.db")
        build(cls.scr, sib.LIVE_IDENT, LIVE_BIND + [NEW])
        cls.scr_extra = os.path.join(cls.tmp, "scr_extra.db")       # david moves too, undeclared
        build(cls.scr_extra, sib.LIVE_IDENT,
              LIVE_BIND[:3] + [LIVE_BIND[3][:5] + ("fuzzy",) + LIVE_BIND[3][6:], NEW])

    def delta_file(self, name, lines):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(DF_HEADER + "".join(lines))
        with open(p, "rb") as fh:
            return p, hashlib.sha256(fh.read()).hexdigest()

    def gate(self, scr, path, sha):
        decl = {"lane": "test", "declared_by": "test", "receipt": "test",
                "words": {"scratch_count": len(sib.WORDS)},
                "verses": {"scratch_count": len(sib.VERSES)},
                "abp_surface": {"identical": True}, "tipnr_entities": {"identical": True},
                "pn_binding": {"delta_file": path, "sha256": sha},
                "pn_greek_identity": {"keys_only_in_live": 0, "keys_only_in_scratch": 0,
                                      "key_moves_file": None}}
        p = os.path.join(self.tmp, "d.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(decl, fh)
        return run_gate(self.live, scr, p)

    def good(self):
        return [delta_line("REMOVED", OLD, None, None), delta_line("ADDED", NEW, None, None)]

    def test_g5_pass(self):
        path, sha = self.delta_file("good.tsv", self.good())
        out = self.gate(self.scr, path, sha)
        self.assertIn("gate A: pn_binding      5 vs 5 rows — 2 row(s) differ; delta file 2 row(s) "
                      "(sha256 %s) → MATCH" % sha[:8], out)
        self.assertIn("gate A: PASS — identity layer as declared", out)
        self.assertNotIn("problem:", out.split("gate B:")[0])

    def test_g5_missing_row_fails(self):
        ghost = (1, 1, 2, "saul", "Saul@1Sa.9.2", "exact", "", 1, 0, 1)
        path, sha = self.delta_file("missing.tsv", self.good() + [delta_line("REMOVED", ghost, None, None)])
        out = self.gate(self.scr, path, sha)
        self.assertIn("→ MISMATCH", out)
        self.assertIn("problem: declared row (1, 1, 2, 'saul'): REMOVED in the delta file, NOT SEEN", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)

    def test_g5_extra_difference_fails(self):
        path, sha = self.delta_file("good2.tsv", self.good())
        out = self.gate(self.scr_extra, path, sha)
        self.assertIn("→ MISMATCH", out)
        self.assertIn("problem: undeclared row (1, 1, 1, 'david'): CHANGED", out)
        self.assertIn("(not in the delta file)", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)

    def test_g5_value_differs_fails(self):
        wrong = NEW[:4] + ("Zerubbabel@Ezr.2.2",) + NEW[5:]
        path, sha = self.delta_file("value.tsv", [delta_line("REMOVED", OLD, None, None),
                                                  delta_line("ADDED", wrong, None, None)])
        out = self.gate(self.scr, path, sha)
        self.assertIn("→ MISMATCH", out)
        self.assertIn("problem: row (40, 1, 12, 'zorobabel'): delta file ('ADDED', None, "
                      "[(40, 1, 12, 'zorobabel', 'Zerubbabel@Ezr.2.2'", out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)

    def test_g5_wrong_sha_fails(self):
        path, sha = self.delta_file("sha.tsv", self.good())
        out = self.gate(self.scr, path, "0" * 64)
        self.assertIn("→ MISMATCH", out)
        self.assertIn("problem: delta_file %s: sha256 %s != declared %s" % (path, sha, "0" * 64), out)
        self.assertIn("gate A: FAIL — identity layer CHANGED — automatic stop", out)


if __name__ == "__main__":
    unittest.main()
