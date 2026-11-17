"""Locked tests for the step-4 A dry-run output (edition upgrade DESIGN §9.139 (1), §9.142 (4)):
build_words_from_abp.py AppTransplant(record_cells=True) / `--cells` — one row per changed
english / english_head / greek_pos / bracket_id cell, bracket_id as eu_words_delta's per-verse rank.

  * the output changes NOTHING A writes: rows and tallies identical with it on and off; on the real
    feed (when present locally) the whole no-db dry run's four files + printout are byte-identical
    on / off, the only additions being cells_<date>.tsv and its printed lines
  * the members: each changed cell listed once, before = OLD, after = composed, repr() values
  * bracket_id by rank: a renumbered but same grouping is NOT a member; a regrouping is, with ranks
  * the self-checks: english verses = "english changed"; greek_pos/bracket verses vs the raw tally,
    the counted-not-listed verses named
  * guards: composed positions differing from OLD's -> FeedError; --cells without a dry run refused

Run:  python tests/test_app_cells.py
"""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import build_words_from_abp as B  # noqa: E402
import abp_app_feed as F  # noqa: E402
from test_app_transplant import Env, run_verse, GEN, GEN_SRC, GEN_FEED  # noqa: E402

K2 = ("Gen", 1, 2)
K2_SRC = "AndG2532 itG1473"
K2_FEED = [("2532", "And"), ("1473", "it")]          # same English -> no cell


def _row(pos, eng, head=None, gpos=None, bid=None):
    return (pos, eng, head, "3756", "G3756", gpos, bid, 0, "", "", None, None)


class Cells(unittest.TestCase):
    def env(self):
        e = Env(src={GEN: GEN_SRC, K2: K2_SRC}, feed={GEN: GEN_FEED, K2: K2_FEED})
        self.addCleanup(e.close)
        return e

    def app(self, e, on):
        return B.AppTransplant(e.src, count_differs=e.cd, record_cells=on, **e.kw)

    def test_on_off_identical_rows_and_tallies(self):
        e = self.env()
        off, on = self.app(e, False), self.app(e, True)
        for k in (GEN, K2):
            r_off, _ = run_verse(off, e.src, k)
            r_on, _ = run_verse(on, e.src, k)
            self.assertEqual(r_off, r_on)
        self.assertEqual(off.tally, on.tally)
        self.assertEqual(off.verdict, on.verdict)
        self.assertEqual(off.cell_members, [])          # off: nothing recorded
        self.assertTrue(on.cell_members)

    def test_members_are_exactly_the_changed_cells(self):
        e = self.env()
        app = self.app(e, True)
        rows, old = run_verse(app, e.src, GEN)
        want = []
        for o, c in zip(map(B._prefix_base, old), map(B._prefix_base, rows)):   # as stored
            for col, i in (("english", 1), ("english_head", 2), ("greek_pos", 5)):
                if o[i] != c[i]:
                    want.append(("Gen", 1, 1, o[0], col, o[i], c[i]))
        got = [m for m in app.cell_members if m[4] != "bracket_id"]
        self.assertEqual(got, want)
        self.assertIn(("Gen", 1, 1, 2, "english", "God made", "God created"), got)
        run_verse(app, e.src, K2)                        # no English change -> no member
        self.assertFalse([m for m in app.cell_members if m[:3] == K2])

    def test_bracket_rank_renumber_is_not_a_member_regroup_is(self):
        app = B.AppTransplant.__new__(B.AppTransplant)
        app.record_cells, app.cell_members, app.F = True, [], F
        old = [_row(0, "a", bid=5), _row(1, "b", bid=5), _row(2, "c", bid=9)]
        same = [_row(0, "a", bid=1), _row(1, "b", bid=1), _row(2, "c", bid=2)]   # renumbered
        app._record_cells(GEN, old, same)
        self.assertEqual(app.cell_members, [])
        regroup = [_row(0, "a", bid=1), _row(1, "b", bid=2), _row(2, "c", bid=2)]
        app._record_cells(GEN, old, regroup)
        # ranks old 1,1,2 -> new 1,2,2: only pos 1's rank moves (the delta counts it the same way)
        self.assertEqual(app.cell_members, [("Gen", 1, 1, 1, "bracket_id", 1, 2)])
        app.cell_members = []
        app._record_cells(GEN, [_row(0, "a"), _row(1, "b")], [_row(0, "a", bid=3), _row(1, "b")])
        self.assertEqual(app.cell_members, [("Gen", 1, 1, 0, "bracket_id", None, 1)])

    def test_rank_matches_eu_words_delta(self):
        # the delta's own ranking over the same rows, via its load_words on a throwaway db
        import sqlite3
        import eu_words_delta as D
        rows = [_row(0, "a", bid=7), _row(1, "b"), _row(2, "c", bid=3), _row(3, "d", bid=7), _row(4, "e", bid=3)]
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, "x.db")
            c = sqlite3.connect(db)
            c.execute("CREATE TABLE words (verse_id INT, position INT, bracket_id INT)")
            c.executemany("INSERT INTO words VALUES (1, ?, ?)", [(r[0], r[6]) for r in rows])
            c.commit()
            got = D.load_words(c, {1: GEN}, ["bracket_id"])
            c.close()
        self.assertEqual({p: v[0] for p, v in got[GEN].items()}, B.AppTransplant._bracket_rank(rows))

    def test_position_mismatch_stops(self):
        app = B.AppTransplant.__new__(B.AppTransplant)
        app.record_cells, app.cell_members, app.F = True, [], F
        with self.assertRaises(F.FeedError):
            app._record_cells(GEN, [_row(0, "a"), _row(1, "b")], [_row(0, "a"), _row(2, "b")])

    def test_written_file_and_checks(self):
        e = self.env()
        app = self.app(e, True)
        for k in (GEN, K2):
            run_verse(app, e.src, k)
        with tempfile.TemporaryDirectory() as d:
            buf = io.StringIO()
            with redirect_stdout(buf):
                app.report(d)
            lines = (Path(d) / "cells_20261031.tsv").read_text(encoding="utf-8").splitlines()
        out = buf.getvalue()
        self.assertEqual(lines[0], "book\tchapter\tverse\tposition\tcolumn\tbefore\tafter")
        self.assertIn("Gen\t1\t1\t2\tenglish\t'God made'\t'God created'", lines)
        self.assertEqual(len(lines) - 1, len(app.cell_members))
        self.assertIn(f"cells list (step 4, sec 9.139 / 9.142): {len(app.cell_members):,} rows", out)
        self.assertIn("cells check: verses with an english cell 1 = english changed 1: yes", out)

    def test_counted_not_listed_verse_is_named(self):
        app = B.AppTransplant.__new__(B.AppTransplant)
        app.record_cells, app.cell_members, app.F = True, [], F
        app.tally = {"english_changed": 0, "greek_pos_or_bracket_changed": 1}
        app.gb_raw_verses = {GEN}                      # raw ids changed, grouping the same
        with tempfile.TemporaryDirectory() as d:
            buf = io.StringIO()
            with redirect_stdout(buf):
                app.write_cells(Path(d) / "c.tsv", {"Gen": 0})
        self.assertIn("counted and not listed (only a bracket number, or a greek_pos the insert blanks, "
                      "changed) 1: Gen 1:1", buf.getvalue())

    def test_listed_not_counted_verse_is_named(self):
        app = B.AppTransplant.__new__(B.AppTransplant)
        app.record_cells, app.F, app.gb_raw_verses = True, F, set()
        app.cell_members = [("Gen", 1, 1, 0, "greek_pos", 1, 2)]
        app.tally = {"english_changed": 0, "greek_pos_or_bracket_changed": 0}
        with tempfile.TemporaryDirectory() as d:
            buf = io.StringIO()
            with redirect_stdout(buf):
                app.write_cells(Path(d) / "c.tsv", {"Gen": 0})
        self.assertIn("listed and not counted 1: Gen 1:1", buf.getvalue())

    def test_compared_as_stored_greek_pos_blanked_without_bracket(self):
        # a no-bracket word whose raw greek_pos differs: the insert (_prefix_base) stores None on
        # both sides, so it is NOT a cell; the same difference inside a bracket IS a cell
        app = B.AppTransplant.__new__(B.AppTransplant)
        app.record_cells, app.cell_members, app.F = True, [], F
        app._record_cells(GEN, [_row(0, "a", gpos=1), _row(1, "b", gpos=3, bid=4)],
                          [_row(0, "a", gpos=2), _row(1, "b", gpos=5, bid=4)])
        self.assertEqual(app.cell_members, [("Gen", 1, 1, 1, "greek_pos", 3, 5)])
        self.assertEqual(B._prefix_base(_row(0, "a", gpos=2))[5], None)    # the rule it follows

    def test_english_check_says_no_on_a_mismatch(self):
        app = B.AppTransplant.__new__(B.AppTransplant)
        app.record_cells, app.F, app.gb_raw_verses = True, F, set()
        app.cell_members = [("Gen", 1, 1, 0, "english", "a", "b")]
        app.tally = {"english_changed": 2, "greek_pos_or_bracket_changed": 0}
        with tempfile.TemporaryDirectory() as d:
            buf = io.StringIO()
            with redirect_stdout(buf):
                app.write_cells(Path(d) / "c.tsv", {"Gen": 0})
        self.assertIn("cells check: verses with an english cell 1 = english changed 2: NO", buf.getvalue())

    def test_cells_without_dry_run_refused(self):
        argv = sys.argv
        sys.argv = ["build_words_from_abp.py", "x.db", "y.db", "--cells"]
        try:
            with self.assertRaises(SystemExit) as cm:
                B.main()
        finally:
            sys.argv = argv
        self.assertIn("--cells works only with --dry-run", str(cm.exception))


@unittest.skipUnless(F.FEED_PATH.is_file(), "real feed TSV not present (gitignored)")
class WholeRunOnOff(unittest.TestCase):
    def test_nodb_dry_run_files_identical_on_and_off(self):
        with tempfile.TemporaryDirectory() as d:
            outs = {}
            for tag, extra in (("off", []), ("on", ["--cells"])):
                o = os.path.join(d, tag)
                p = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_words_from_abp.py"),
                                    "--dry-run-nodb", "--out", o, *extra], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", cwd=str(ROOT))
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                outs[tag] = (o, p.stdout.replace(o, "<OUT>"))
            for f in ("strict_fail", "eligible", "merge_pairs", "edge_splits"):
                a = Path(outs["off"][0], f"{f}_20261031.tsv").read_bytes()
                b = Path(outs["on"][0], f"{f}_20261031.tsv").read_bytes()
                self.assertEqual(a, b, f)
            self.assertFalse(Path(outs["off"][0], "cells_20261031.tsv").exists())
            on_lines = [ln for ln in outs["on"][1].splitlines() if not ln.startswith("  cells ")]
            self.assertEqual(outs["off"][1].splitlines(), on_lines)
            self.assertIn(": yes", outs["on"][1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
