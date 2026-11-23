"""The KJV long-shift write (DESIGN 9.257, 9.258). Own throwaway db, built from the row files' own
before-values; never touches bible.db.

Run:  python tests/test_kjv_shift_apply.py
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
import apply_kjv_shift_20261123 as K    # noqa: E402


class Write(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = os.path.join(self.tmp.name, "t.db").replace(os.sep, "/")
        self.plan = K.load_plan()
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

    def tearDown(self):
        self.tmp.cleanup()

    def tags(self):
        c = sqlite3.connect(self.db)
        out = sorted(c.execute("SELECT word_id, strongs_id FROM kjv_strongs").fetchall())
        c.close()
        return out

    def quiet(self, fn, *a, **k):
        with redirect_stdout(io.StringIO()) as o:
            fn(*a, **k)
        return o.getvalue()

    def test_the_plan(self):
        self.assertEqual(len(self.plan), 405)
        self.assertEqual(len({p["key"] for p in self.plan}), 21)

    def test_act_26_12_reads_the_pair_on_whereupon(self):
        by = {p["word"]: p for p in self.plan if p["key"] == (44, 26, 12)}
        self.assertEqual(by["Whereupon"]["after"], ["G1722", "G3739"])
        self.assertEqual(by["as"]["after"], [])

    def test_round_trip(self):
        start = self.tags()
        self.quiet(K.do_check, self.db, scan=False)
        self.quiet(K.do_write, self.db, True)
        self.quiet(K.do_after, self.db, scan=False)
        self.assertNotEqual(self.tags(), start)
        self.assertIn((1, "H7225"), self.tags())
        self.quiet(K.do_write, self.db, False)
        self.assertEqual(self.tags(), start)

    def test_a_differing_before_value_stops_with_nothing_saved(self):
        c = sqlite3.connect(self.db)
        c.execute("UPDATE kjv_strongs SET strongs_id='G9999' WHERE word_id=?", (next(p["id"] for p in self.plan if p["before"]),))
        c.commit()
        c.close()
        start = self.tags()
        with self.assertRaises(K.Stop):
            self.quiet(K.do_check, self.db, scan=False)
        with self.assertRaises(K.Stop):
            self.quiet(K.do_write, self.db, True)
        self.assertEqual(self.tags(), start)

    def test_applying_twice_stops(self):
        self.quiet(K.do_write, self.db, True)
        once = self.tags()
        with self.assertRaises(K.Stop):
            self.quiet(K.do_write, self.db, True)
        self.assertEqual(self.tags(), once)

    def test_refuses_the_nightly_window(self):
        with mock.patch.object(K, "in_window", lambda: True):
            with self.assertRaises(K.Stop):
                self.quiet(K.do_write, self.db, True)

    def test_a_changed_row_file_stops(self):
        with mock.patch.object(K, "CLEARED_SHA", "0" * 64):
            with self.assertRaises(K.Stop):
                K.load_plan()


if __name__ == "__main__":
    unittest.main()
