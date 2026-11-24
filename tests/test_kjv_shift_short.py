"""The KJV short-verse and Psa 7:1 writes (DESIGN 9.259, 9.260). Own throwaway db, built from the row
files' own before-values; never touches bible.db.

Run:  python tests/test_kjv_shift_short.py
"""
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_kjv_shift_20261123 as K            # noqa: E402
import apply_kjv_shift_short_20261124 as S      # noqa: E402


class Write(unittest.TestCase):
    def build(self, batch):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, "t.db").replace(os.sep, "/")
        self.plan = S.load_plan(batch)
        c = sqlite3.connect(self.db)
        c.executescript("""CREATE TABLE words (a); CREATE TABLE verses (a);
            CREATE TABLE kjv_words (word_id INTEGER PRIMARY KEY, book_id INT, chapter INT, verse_num INT, verse_pos INT, word TEXT);
            CREATE TABLE kjv_strongs (word_id INT, strongs_id TEXT);""")
        for p in self.plan:
            c.execute("INSERT INTO kjv_words VALUES (?,?,?,?,?,?)", (p["id"], *p["key"], p["id"], p["word"]))
            c.executemany("INSERT INTO kjv_strongs VALUES (?,?)", [(p["id"], t) for t in p["before"]])
        c.execute("INSERT INTO kjv_words VALUES (1, 1, 1, 1, 1, 'other')")
        c.execute("INSERT INTO kjv_strongs VALUES (1, 'H7225')")
        c.commit()
        c.close()
        for x in (mock.patch.object(K, "WORDS", 0), mock.patch.object(K, "VERSES", 0), mock.patch.object(K, "in_window", lambda: False)):
            x.start()
            self.addCleanup(x.stop)

    def tags(self):
        c = sqlite3.connect(self.db)
        out = sorted(c.execute("SELECT word_id, strongs_id FROM kjv_strongs").fetchall())
        c.close()
        return out

    def quiet(self, fn, *a, **k):
        with redirect_stdout(io.StringIO()) as o:
            fn(*a, **k)
        return o.getvalue()

    def test_the_plans(self):
        self.assertEqual(len(S.load_plan("short")), 107)
        self.assertEqual(len({p["key"] for p in S.load_plan("short")}), 31)
        psa = S.load_plan("psa")
        self.assertEqual(len(psa), 6)
        self.assertEqual({p["key"] for p in psa}, {(19, 7, 1)})

    def test_round_trip_both_batches(self):
        for batch in ("short", "psa"):
            with self.subTest(batch):
                self.build(batch)
                start = self.tags()
                self.quiet(S.do_read, self.db, batch, "before", scan=False)
                self.quiet(S.do_write, self.db, batch, True)
                self.quiet(S.do_read, self.db, batch, "after", scan=False)
                self.assertNotEqual(self.tags(), start)
                self.assertIn((1, "H7225"), self.tags())
                self.quiet(S.do_write, self.db, batch, False)
                self.assertEqual(self.tags(), start)

    def test_a_differing_before_value_stops_with_nothing_saved(self):
        self.build("short")
        c = sqlite3.connect(self.db)
        c.execute("UPDATE kjv_strongs SET strongs_id='G9999' WHERE word_id=?", (next(p["id"] for p in self.plan if p["before"]),))
        c.commit()
        c.close()
        start = self.tags()
        with self.assertRaises(K.Stop):
            self.quiet(S.do_read, self.db, "short", "before", scan=False)
        with self.assertRaises(K.Stop):
            self.quiet(S.do_write, self.db, "short", True)
        self.assertEqual(self.tags(), start)

    def test_applying_twice_stops(self):
        self.build("short")
        self.quiet(S.do_write, self.db, "short", True)
        once = self.tags()
        with self.assertRaises(K.Stop):
            self.quiet(S.do_write, self.db, "short", True)
        self.assertEqual(self.tags(), once)

    def test_the_detector_can_only_name_a_verse_never_stop_a_clean_run(self):
        self.build("psa")
        self.quiet(S.do_write, self.db, "psa", True)
        with mock.patch.object(S, "flagged", lambda conn, plan: ["Psa 7:1"]):
            out = self.quiet(S.do_read, self.db, "psa", "after")
        self.assertIn("for information only", out)
        self.assertIn("AFTER DONE", out)

    def test_a_failed_detector_scan_does_not_stop_a_clean_run(self):
        self.build("psa")
        self.quiet(S.do_write, self.db, "psa", True)
        def boom(conn, plan):
            raise sqlite3.OperationalError("database is locked")
        with mock.patch.object(S, "flagged", boom):
            out = self.quiet(S.do_read, self.db, "psa", "after")
        self.assertIn("did not run", out)
        self.assertIn("AFTER DONE", out)

    def test_refuses_the_nightly_window(self):
        self.build("short")
        with mock.patch.object(K, "in_window", lambda: True):
            with self.assertRaises(K.Stop):
                self.quiet(S.do_write, self.db, "short", True)


if __name__ == "__main__":
    unittest.main()
