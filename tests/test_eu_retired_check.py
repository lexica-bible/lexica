"""Locked tests for scripts/eu_retired_check.py — the §9.61 / §9.63 retired-row check (§9.81).
Synthetic temp sqlite copies + a stub feed_text only. No real bible.db, no real feed.

Run:  python tests/test_eu_retired_check.py
"""
import io
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import eu_retired_check as R                          # noqa: E402

FEED_OK = {5: ("Mar", 16, 17)}                        # one named prose row in the synthetic set
FEED = {("Mar", 16, 17): "signs shall follow -- in my name"}   # B's text, before the em-dash swap


class Retired(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "built.db"

    def make(self, verses, words, corrections):
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT)")
        con.execute("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT, greek_pos INT)")
        con.execute("CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, "
                    "position INT, field TEXT, source_value TEXT, corrected_value TEXT, ledger_ref TEXT, "
                    "status TEXT, applied_at TEXT)")
        for vid, (b, c, v, t) in enumerate(verses, 1):
            con.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (vid, b, c, v, t))
        for vid, pos, eng, gp in words:
            con.execute("INSERT INTO words (verse_id, position, english, greek_pos) VALUES (?,?,?,?)", (vid, pos, eng, gp))
        for row in corrections:
            con.execute("INSERT INTO abp_corrections VALUES (?,?,?,?,?,?,?,?,?,?,'ingest')", row)
        con.commit()
        con.close()

    def base(self, prose_named="signs shall follow — in my name", prose_other="fixed text", gp=5):
        verses = [("Mar", 16, 17, prose_named), ("Job", 24, 18, prose_other), ("Exo", 32, 3, "x")]
        words = [(3, 0, "the", gp)]
        corr = [
            (5, "Mar", 16, 17, -1, "verses.text", "old", "corrected named", "S9-f", "retired"),
            (6, "Job", 24, 18, -1, "verses.text", "old", "fixed text", "S9-f", "retired"),
            (7, "Exo", 32, 3, 0, "greek_pos", "4", "5", "BD-1", "retired"),
            (8, "Exo", 32, 3, 0, "english", "a", "b", "L9", "active"),          # active rows are not checked
        ]
        self.make(verses, words, corr)

    def run_check(self, expected=3, feed_ok=FEED_OK):
        calls = []

        def ft(key):
            calls.append(key)
            return FEED[key]
        results, failures = R.check(str(self.db), ft, expected=expected, feed_ok=feed_ok)
        return results, failures, calls

    def test_pass_named_row_on_feed_text_others_on_corrected(self):
        self.base()
        results, failures, calls = self.run_check()
        self.assertEqual(failures, [])
        self.assertEqual([r["outcome"] for r in results], ["feed text", "corrected_value", "corrected_value"])
        self.assertEqual(calls, [("Mar", 16, 17)])          # feed text derived only for the named row
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = R.report(str(self.db), results, failures, expected=3)
        self.assertEqual(rc, 0)
        self.assertIn("RETIRED-ROW CHECK: PASS 3/3 HOLD (corrected_value 2 - feed text 1)", buf.getvalue())

    def test_named_row_on_corrected_value_also_passes(self):
        self.base(prose_named="corrected named")
        _, failures, _ = self.run_check()
        self.assertEqual(failures, [])

    def test_feed_text_is_compared_after_the_emdash_swap(self):
        self.base(prose_named="signs shall follow -- in my name")     # the un-swapped form = a miss
        _, failures, _ = self.run_check()
        self.assertEqual([f["id"] for f in failures], [5])

    def test_unnamed_prose_row_equal_to_nothing_fails_with_full_text(self):
        self.base(prose_other="something else entirely")
        results, failures, _ = self.run_check()
        self.assertEqual([f["id"] for f in failures], [6])
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = R.report(str(self.db), results, failures, expected=3)
        out = buf.getvalue()
        self.assertEqual(rc, 1)
        self.assertIn("RETIRED-ROW CHECK: FAIL 1 of 3", out)
        for txt in ("'old'", "'fixed text'", "'something else entirely'"):
            self.assertIn(txt, out)

    def test_feed_text_carveout_refuses_a_sixth_row(self):
        # id 6 matches B's feed text but is not a named row -> still a FAIL
        self.base(prose_other="signs shall follow — in my name")
        _, failures, calls = self.run_check()
        self.assertEqual([f["id"] for f in failures], [6])
        self.assertEqual(calls, [("Mar", 16, 17)])

    def test_number_cell_matches_text_corrected_value(self):
        self.base(gp=5)
        _, failures, _ = self.run_check()
        self.assertEqual(failures, [])
        self.tmp.cleanup()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "built.db"
        self.base(gp=4)
        _, failures, _ = self.run_check()
        self.assertEqual([f["id"] for f in failures], [7])

    def test_wrong_retired_count_stops(self):
        self.base()
        with self.assertRaisesRegex(R.Stop, "3 retired row"):
            self.run_check(expected=23)

    def test_named_id_not_matching_its_verse_stops(self):
        self.base()
        with self.assertRaisesRegex(R.Stop, "feed-text id 5"):
            self.run_check(feed_ok={5: ("2Sa", 16, 18)})

    def test_missing_cell_fails(self):
        self.base()
        con = sqlite3.connect(self.db)
        con.execute("DELETE FROM words")
        con.commit()
        con.close()
        _, failures, _ = self.run_check()
        self.assertEqual([f["id"] for f in failures], [7])

    def test_target_checks_and_read_only(self):
        with self.assertRaisesRegex(R.Stop, "required"):
            R.check_target("")
        with self.assertRaisesRegex(R.Stop, "not found"):
            R.check_target(str(Path(self.tmp.name) / "nope.db"))
        self.base()
        orig = R.BP.LIVE_DB
        R.BP.LIVE_DB = self.db
        try:
            with self.assertRaisesRegex(R.Stop, "LIVE"):
                R.check_target(str(self.db))
        finally:
            R.BP.LIVE_DB = orig
        before = self.db.read_bytes()
        self.run_check()
        self.assertEqual(before, self.db.read_bytes())

    def test_frozen_carveout_is_the_ruled_five(self):
        self.assertEqual(R.EXPECTED_RETIRED, 23)
        self.assertEqual(R.FEED_OK, {51: ("2Sa", 16, 18), 25: ("1Ch", 22, 15), 27: ("Job", 24, 19),
                                     24: ("Mat", 21, 19), 45: ("Mar", 16, 17)})


if __name__ == "__main__":
    unittest.main()
