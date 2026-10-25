"""Locked tests for scripts/lane3_rebuild_step.py's matcher (rebuild step 8b.2a,
CHARTER_rebuild_trap_fix.md G4; JP rulings 2026-10-25). Every rule fires on a planted output, using
the REAL gapfix slots read from scripts/lane3_star_gapfix.json:

  contiguity FAIL from fixes on a gapfix slot, gapfix then PASS   -> pass
  contiguity FAIL from fixes on a non-gapfix slot                 -> fail
  gapfix still FAIL on that verse                                 -> fail
  all three files already applied                                 -> pass
  mixed (8 patched / 1 already)                                   -> fail
  plus: a skip, a render FAIL, fixes2 contiguity FAIL, right position but wrong bracket,
        gapfix never reporting a verse fixes failed, and the live-path refusal.

Run:  python tests/test_lane3_rebuild_step.py
"""
import contextlib
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import lane3_rebuild_step as st   # noqa: E402

GAPS = st.gapfix_slots()
FIXES_VERSES = ["Mat 9:11", "2Ch 14:12", "2Sa 14:4", "Isa 30:31", "Jer 50:16", "Lev 24:10",
                "Num 25:8", "Num 25:14", "Num 25:15"]
GAP_VERSES = ["2Sa 14:4", "Num 25:8", "Num 25:14", "Num 25:15", "2Sa 18:31", "2Sa 18:32"]
FIXES2_VERSES = ["Eze 23:5", "Heb 11:24", "1Ch 21:9", "1Sa 14:50", "1Sa 24:5", "Gen 46:26",
                 "Mat 27:26"]


def block(verse, contig="PASS", render="PASS"):
    return (f"\n=== {verse} === (3 cell edits)\n  BEFORE:\n  AFTER:\n"
            f"  render check: prose unchanged by the edit -> {render}\n"
            f"  contiguity check: {contig}\n")


def run_out(verses, contig=None, render=None, skips=(), patched=None, already=0):
    contig, render = contig or {}, render or {}
    body = "".join(block(v, contig.get(v, "PASS"), render.get(v, "PASS")) for v in verses)
    body += "".join(f"SKIP {v}: english mismatch pos 1  (already fixed, or state changed)\n"
                    for v in skips)
    n = len(verses) if patched is None else patched
    return body + f"\nAPPLIED — {n} verse(s) patched, {already} already applied, " \
                  f"{len(skips)} skipped  [DB: /x/built2.db]\n"


def already_out(verses):
    return "".join(f"ALREADY {v}: already applied (every pinned cell holds its new value)\n"
                   for v in verses) + \
        f"\nAPPLIED — 0 verse(s) patched, {len(verses)} already applied, 0 skipped  [DB: /x]\n"


# The real first-run shape: fixes leaves exactly the gapfix slots open, gapfix closes them.
FIRST_FIXES = {"2Sa 14:4": "FAIL [(1, 4)]", "Num 25:8": "FAIL [(2, 4), (3, 15)]",
               "Num 25:14": "FAIL [(2, 5)]", "Num 25:15": "FAIL [(2, 4)]"}


def first_run(**over):
    outs = {st.FIXES: run_out(FIXES_VERSES, contig=FIRST_FIXES),
            st.GAPFIX: run_out(GAP_VERSES),
            st.FIXES2: run_out(FIXES2_VERSES)}
    outs.update(over)
    return outs


class Lane3Matcher(unittest.TestCase):
    def test_gapfix_slots_read_from_the_real_file(self):
        self.assertEqual(GAPS["Num 25:8"], {(2, 4), (3, 15)})
        self.assertEqual(GAPS["2Sa 14:4"], {(1, 4)})
        self.assertEqual(GAPS["2Sa 18:31"], {(2, 7)})
        self.assertEqual(GAPS["2Sa 18:32"], {(2, 15)})
        self.assertEqual(sorted(GAPS), sorted(GAP_VERSES))

    def test_first_run_with_gapfix_slots_open_then_closed_passes(self):
        ok, probs = st.judge(first_run(), GAPS)
        self.assertTrue(ok, probs)

    def test_contiguity_fail_on_a_non_gapfix_slot_fails(self):
        bad = dict(FIRST_FIXES, **{"Mat 9:11": "FAIL [(2, 2)]"})
        ok, probs = st.judge(first_run(**{st.FIXES: run_out(FIXES_VERSES, contig=bad)}), GAPS)
        self.assertFalse(ok)
        self.assertTrue(any("Mat 9:11 (2, 2) is not a gapfix slot" in p for p in probs), probs)

    def test_right_position_wrong_bracket_fails(self):
        bad = dict(FIRST_FIXES, **{"Num 25:14": "FAIL [(9, 5)]"})
        ok, _ = st.judge(first_run(**{st.FIXES: run_out(FIXES_VERSES, contig=bad)}), GAPS)
        self.assertFalse(ok)

    def test_gapfix_still_fail_fails(self):
        gap = run_out(GAP_VERSES, contig={"Num 25:8": "FAIL [(3, 15)]"})
        ok, probs = st.judge(first_run(**{st.GAPFIX: gap}), GAPS)
        self.assertFalse(ok)
        self.assertTrue(any("Num 25:8 must PASS" in p for p in probs), probs)

    def test_gapfix_not_reporting_a_failed_verse_fails(self):
        gap = run_out(["2Sa 14:4", "Num 25:14", "Num 25:15", "2Sa 18:31", "2Sa 18:32"], patched=6)
        ok, _ = st.judge(first_run(**{st.GAPFIX: gap}), GAPS)
        self.assertFalse(ok)

    def test_all_already_applied_passes(self):
        outs = {st.FIXES: already_out(FIXES_VERSES), st.GAPFIX: already_out(GAP_VERSES),
                st.FIXES2: already_out(FIXES2_VERSES)}
        ok, probs = st.judge(outs, GAPS)
        self.assertTrue(ok, probs)

    def test_mixed_patched_and_already_fails(self):
        mixed = run_out(FIXES_VERSES[:8], contig=FIRST_FIXES, patched=8, already=1) \
            .replace("\nAPPLIED", "ALREADY Num 25:15: already applied\n\nAPPLIED")
        ok, probs = st.judge(first_run(**{st.FIXES: mixed}), GAPS)
        self.assertFalse(ok)
        self.assertTrue(any("a mix fails" in p for p in probs), probs)

    def test_a_skip_fails(self):
        out = run_out(FIXES2_VERSES[:6], skips=["Mat 27:26"], patched=6)
        ok, probs = st.judge(first_run(**{st.FIXES2: out}), GAPS)
        self.assertFalse(ok)
        self.assertTrue(any("skipped" in p for p in probs), probs)

    def test_render_fail_fails(self):
        out = run_out(FIXES2_VERSES, render={"Heb 11:24": "FAIL"})
        ok, _ = st.judge(first_run(**{st.FIXES2: out}), GAPS)
        self.assertFalse(ok)

    def test_fixes2_is_strict(self):
        out = run_out(FIXES2_VERSES, contig={"Gen 46:26": "FAIL [(1, 20)]"})
        ok, probs = st.judge(first_run(**{st.FIXES2: out}), GAPS)
        self.assertFalse(ok)
        self.assertTrue(any("(strict)" in p for p in probs), probs)

    def test_refuses_the_live_path(self):
        named = os.path.join(tempfile.mkdtemp(), "bible.db")
        open(named, "wb").close()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = st.main([named])
        self.assertEqual(rc, 1)
        self.assertIn("LANE-3 STEP: REFUSED", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
