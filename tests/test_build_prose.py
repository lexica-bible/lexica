"""Locked tests for scripts/build_prose_from_app.py — derivation B (verses.text from the app
feed; DESIGN_q2_build.md §9.3, §9.7, §9.8, §9.48–§9.57). Synthetic feed + synthetic abp_texts
lines + temp sqlite copies only (reuses test_app_transplant's Env). No real bible.db.

Run:  python tests/test_build_prose.py
"""
import collections
import csv
import hashlib
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import build_prose_from_app as BP                     # noqa: E402
from abp_app_feed import FeedError                    # noqa: E402
from test_app_transplant import Env                   # noqa: E402

GEN, GEN2, GEN3 = ("Gen", 1, 1), ("Gen", 1, 2), ("Gen", 1, 3)
SRC = {
    GEN: "AndG2532 [3brought forthG1806 1theG3588 2waters]G5204",
    GEN2: "AndG2532 thatG3754",
    GEN3: "AndG2532 typeG1085",
}
FEED = {
    GEN: [("2532", "And"), ("1806", "[3brought forth"), ("3588", "1the"), ("5204", "2seas]")],
    GEN2: [("3754", "that"), ("2532", "and")],                       # swap -> ineligible in A
    GEN3: [("2532", "And"), ("1085", "type -")],                     # end dash -> " --"
}


class Prose(unittest.TestCase):
    def setUp(self):
        self.env = Env(src=SRC, feed=FEED, dash_pin=1, fold_pin=0)
        self.addCleanup(self.env.close)
        self.app = self.env.app()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.elig = self.d / "eligible.tsv"
        self.write_eligible({GEN: "", GEN2: "swap", GEN3: ""})

    def write_eligible(self, verdicts):
        with open(self.elig, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\teligible\treason\n")
            for (b, c, v), r in verdicts.items():
                f.write(f"{b}\t{c}\t{v}\t{0 if r else 1}\t{r}\n")

    def copy_db(self, texts, corrections=()):
        p = self.d / "copy.db"
        con = sqlite3.connect(p)
        con.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT)")
        for (b, c, v), t in texts.items():
            con.execute("INSERT INTO verses (book, chapter, verse, text) VALUES (?,?,?,?)", (b, c, v, t))
        con.execute("CREATE TABLE abp_corrections (book TEXT, chapter INT, verse INT, field TEXT, status TEXT,"
                    " source_value TEXT, ledger_ref TEXT)")
        for (b, c, v), st, *rest in corrections:        # rest = (source_value, ledger_ref), optional
            src_val, ref = (rest + [None, None])[:2]
            con.execute("INSERT INTO abp_corrections VALUES (?,?,?,?,?,?,?)", (b, c, v, "verses.text", st, src_val, ref))
        con.commit()
        con.close()
        return p

    def run_b(self, copy=None, apply=False):
        with redirect_stdout(io.StringIO()):
            return BP.run(self.elig, copy, apply, self.d / "runs", stamp="T", app=self.app, src=SRC)

    def test_local_reorders_brackets_and_counts(self):
        counts, rows = self.run_b()
        self.assertEqual(counts["written"], 2)            # Gen 1:1 seas/waters; Gen 1:3 dash form
        self.assertEqual(counts["kept_old:swap"], 1)
        self.assertEqual(counts["fires:stray_bracket"], 0)
        with open(self.d / "runs" / "prose_T.tsv", encoding="utf-8", newline="") as f:
            got = [(r["verse"], r["outcome"], r["reason"]) for r in csv.DictReader(f, delimiter="\t")]
        self.assertEqual(got, [("1", "written", ""), ("2", "kept_old", "swap"), ("3", "written", "")])

    def test_apply_writes_only_differing_eligible_verses(self):
        copy = self.copy_db({GEN: "And brought forth the waters", GEN2: "OLD 2",
                             GEN3: "And type —"})                    # Gen 1:3 identical after swap
        counts, _ = self.run_b(copy, apply=True)
        self.assertEqual((counts["written"], counts["unchanged"], counts["applied"]), (1, 1, 1))
        con = sqlite3.connect(copy)
        got = dict(((b, c, v), t) for b, c, v, t in con.execute("SELECT book, chapter, verse, text FROM verses"))
        con.close()
        self.assertEqual(got[GEN], "And the seas brought forth")     # [3brought forth 1the 2seas]
        self.assertEqual(got[GEN2], "OLD 2")                          # ineligible: untouched
        self.assertEqual(got[GEN3], "And type —")                 # identical: not rewritten

    def test_dash_written_as_double_hyphen_for_step5(self):
        copy = self.copy_db({GEN: "x", GEN2: "y", GEN3: "And type"})
        self.run_b(copy, apply=True)
        con = sqlite3.connect(copy)
        self.assertEqual(con.execute("SELECT text FROM verses WHERE verse=3").fetchone()[0], "And type --")
        con.close()

    def test_dry_run_writes_nothing(self):
        copy = self.copy_db({GEN: "x", GEN2: "y", GEN3: "z"})
        before = (hashlib.sha256(copy.read_bytes()).hexdigest(), os.path.getmtime(copy))
        counts, _ = self.run_b(copy, apply=False)
        self.assertEqual(counts["written"], 2)
        self.assertNotIn("applied", counts)
        self.assertEqual(before, (hashlib.sha256(copy.read_bytes()).hexdigest(), os.path.getmtime(copy)))

    def test_active_correction_on_written_verse_stops(self):
        copy = self.copy_db({GEN: "x", GEN2: "y", GEN3: "z"}, corrections=[(GEN, "active")])
        with self.assertRaisesRegex(FeedError, "ACTIVE verses.text correction"):
            self.run_b(copy, apply=True)
        con = sqlite3.connect(copy)
        self.assertEqual(con.execute("SELECT text FROM verses WHERE verse=1").fetchone()[0], "x")
        con.close()

    def b_text(self, key):
        """The exact text B writes for an eligible verse (before the em-dash swap)."""
        ka = self.app.pairs[key]
        joined = " ".join(self.app.norm[(ka[0], ka[1], ka[2], s["slot_index"])] for s in self.app.feed[ka])
        return BP.clean_counted(joined, "t", collections.Counter())

    def test_active_row_keyed_to_b_text_is_allowed_and_counted(self):      # §9.79
        copy = self.copy_db({GEN: "x", GEN2: "y", GEN3: "z"},
                            corrections=[(GEN, "active", self.b_text(GEN), "EU-Gen1:1")])
        counts, _ = self.run_b(copy, apply=True)
        self.assertEqual(counts["applied"], 2)
        self.assertEqual((counts["corrections:matched_written"], counts["corrections:matched_written_eu"]), (1, 1))

    def test_active_row_differing_by_whitespace_only_stops(self):          # §9.79: exact, not normalized
        copy = self.copy_db({GEN: "x", GEN2: "y", GEN3: "z"},
                            corrections=[(GEN, "active", self.b_text(GEN) + " ", "EU-Gen1:1")])
        with self.assertRaisesRegex(FeedError, "ACTIVE verses.text correction"):
            self.run_b(copy, apply=True)

    def test_active_row_keyed_to_b_text_on_unwritten_verse_stops(self):    # B must write the verse
        copy = self.copy_db({GEN: BP.emdash(self.b_text(GEN)), GEN2: "y", GEN3: "z"},
                            corrections=[(GEN, "active", self.b_text(GEN), "EU-Gen1:1")])
        with self.assertRaisesRegex(FeedError, "ACTIVE verses.text correction"):
            self.run_b(copy, apply=True)

    def test_retired_correction_does_not_stop(self):
        copy = self.copy_db({GEN: "x", GEN2: "y", GEN3: "z"}, corrections=[(GEN, "retired")])
        counts, _ = self.run_b(copy, apply=True)
        self.assertEqual(counts["applied"], 2)

    def test_eligible_file_disagreeing_with_decide_stops(self):
        self.write_eligible({GEN: "", GEN2: "", GEN3: ""})            # GEN2 is a swap in decide()
        with self.assertRaisesRegex(FeedError, "decide"):
            self.run_b()

    def test_target_checks(self):
        with self.assertRaisesRegex(FeedError, "required"):
            BP.check_target("")
        with self.assertRaisesRegex(FeedError, "not found"):
            BP.check_target(str(self.d / "nope.db"))
        live = BP.LIVE_DB
        if live.is_file():
            with self.assertRaisesRegex(FeedError, "LIVE"):
                BP.check_target(str(live))
        orig = BP.LIVE_DB
        fake_live = self.copy_db({GEN: "x"})
        BP.LIVE_DB = fake_live
        try:
            with self.assertRaisesRegex(FeedError, "LIVE"):
                BP.check_target(str(fake_live))
        finally:
            BP.LIVE_DB = orig

    def test_cleanup_fire_counts(self):
        import collections
        fires = collections.Counter()
        out = BP.clean_counted("And [2let 1us", "t", fires)            # unclosed bracket
        self.assertEqual(fires["stray_bracket"], 1)
        self.assertEqual(fires["leaked_digit"], 1)                   # unreordered digits leak too
        self.assertEqual(out, "And let us")
        fires = collections.Counter()
        BP.clean_counted("And 4dried up", "t", fires)
        self.assertEqual(fires["leaked_digit"], 1)


if __name__ == "__main__":
    unittest.main()
