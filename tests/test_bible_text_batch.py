"""The Bible-text batch write (scripts/apply_bible_text_batch_20261122.py), on a throwaway database built
from the cleared before-values. Proves: it writes exactly the cleared cells; any differing before-value
writes nothing; it refuses the nightly window; undo puts every table back byte for byte.

Run:  python tests/test_bible_text_batch.py
"""
import contextlib
import hashlib
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_bible_text_batch_20261122 as B   # noqa: E402

TABLES = {"verses": "book, chapter, verse, text", "words": "verse_id, position, english",
          "kjv_strongs": "word_id, strongs_id", "kjv_words": "word_id, word",
          "abp_corrections": "book, chapter, verse, position, field, source_value, corrected_value, status, applied_at, ledger_ref"}


def digest(db):
    c = sqlite3.connect(db)
    h = hashlib.sha256()
    for t, cols in TABLES.items():
        for r in c.execute(f"SELECT {cols} FROM {t} ORDER BY {cols}"):
            h.update(repr(r).encode("utf-8"))
    c.close()
    return h.hexdigest()


class Batch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = os.path.join(self.tmp.name, "t.db")
        self.plan = B.load_plan()
        c = sqlite3.connect(self.db)
        c.executescript("""
            CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
            CREATE TABLE words (verse_id INT, position INT, english TEXT);
            CREATE TABLE kjv_words (word_id INT, book_id INT, chapter INT, verse_num INT, word TEXT);
            CREATE TABLE kjv_strongs (word_id INT, strongs_id TEXT);
            CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, book TEXT NOT NULL, chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL, position INTEGER NOT NULL, field TEXT NOT NULL, source_value TEXT,
                corrected_value TEXT, reason TEXT NOT NULL, ledger_ref TEXT, applied_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active', created TEXT NOT NULL);
        """)
        ids = {}
        for r in self.plan["prose"]:
            cur = c.execute("INSERT INTO verses (book, chapter, verse, text) VALUES (?,?,?,?)", (*r["key"], r["before"]))
            ids[r["key"]] = cur.lastrowid
        for r in self.plan["words"]:
            c.execute("INSERT INTO words VALUES (?,?,?)", (ids[r["key"]], r["pos"], r["before"]))
            c.execute("INSERT INTO words VALUES (?,?,?)", (ids[r["key"]], r["pos"] + 500, r["before"]))   # same text, other slot
        for r in self.plan["kjv"]:
            c.execute("INSERT INTO kjv_words VALUES (?,?,?,?,?)", (r["id"], B.KJV_BOOK, B.KJV_CH, B.KJV_VS, r["word"]))
            if r["before"]:
                c.execute("INSERT INTO kjv_strongs VALUES (?,?)", (r["id"], r["before"]))
        c.execute("INSERT INTO kjv_strongs VALUES (999, 'G1056')")                     # a tag on another verse
        ex = next(r for r in self.plan["prose"] if r["key"] == B.EXISTING_PROSE)
        src = ex["before"].replace("—", "--").replace("Jeroboam,", "Jeroboam II,")
        ins = """INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value, reason,
                 ledger_ref, applied_at, status, created) VALUES (?,?,?,?,?,?,?,?,?,'ingest','active','2026-11-02')"""
        c.execute(ins, (*B.EXISTING_PROSE, -1, "verses.text", src, ex["before"], "jeroboam", "EU-2Ki14:28"))
        for i in range(B.ACTIVE_BEFORE - 1):
            c.execute(ins, ("Zzz", 1, i + 1, 1, "english", "a", "b", "filler", "filler"))
        c.commit()
        c.close()
        for name, value in (("WORDS", 2 * len(self.plan["words"])), ("VERSES", len(self.plan["prose"]))):
            p = mock.patch.object(B, name, value)
            p.start()
            self.addCleanup(p.stop)
        for name in ("check_feed",):
            p = mock.patch.object(B, name, lambda *a, **k: None)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.object(B, "in_window", lambda now=None: False)
        self.window = p.start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        self.tmp.cleanup()

    def run_mode(self, mode):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = B.main([mode, "--db", self.db])
        return rc, out.getvalue()

    def q(self, sql, *a):
        c = sqlite3.connect(self.db)
        r = c.execute(sql, a).fetchall()
        c.close()
        return r

    def test_plan_is_the_cleared_rows_plus_him(self):
        self.assertEqual((len(self.plan["prose"]), len(self.plan["words"]), len(self.plan["kjv"])), (15, 14, 21))
        self.assertEqual(len(B.new_rows(self.plan)), B.ACTIVE_AFTER - B.ACTIVE_BEFORE)
        him = next(r for r in self.plan["kjv"] if r["id"] == 680991)
        self.assertEqual((him["before"], him["after"]), ("G615", "G846"))

    def test_apply_writes_exactly_the_cleared_cells(self):
        rc, out = self.run_mode("apply")
        self.assertEqual(rc, 0, out)
        self.assertIn("written: 76 changes", out)
        c = sqlite3.connect(self.db)
        self.assertEqual(B.verify(c, self.plan, "after"), [])
        c.close()
        self.assertEqual(self.q("SELECT strongs_id FROM kjv_strongs WHERE word_id=680977"), [("G1056",)])
        self.assertEqual(self.q("SELECT strongs_id FROM kjv_strongs WHERE word_id=680991"), [("G846",)])
        self.assertEqual(self.q("SELECT count(*) FROM kjv_strongs WHERE strongs_id='G2532'"), [(0,)])
        self.assertEqual(self.q("SELECT count(*) FROM kjv_strongs WHERE word_id=999"), [(1,)])
        self.assertEqual(self.q("SELECT count(*) FROM words WHERE position>=500 AND english LIKE '% )'"), [(9,)])   # other slots untouched

    def test_existing_prose_row_changed_not_doubled(self):
        self.run_mode("apply")
        rows = self.q("SELECT source_value, corrected_value FROM abp_corrections WHERE book='2Ki' AND position=-1")
        self.assertEqual(len(rows), 1)
        self.assertIn("Jeroboam II", rows[0][0])
        self.assertIn("belonging to Judah", rows[0][1])

    def test_dash_rows_keep_the_rebuild_source_form(self):
        self.run_mode("apply")
        for book, ch, vs in (("Luk", 2, 35), ("Jdg", 20, 34)):
            s, cor = self.q("""SELECT source_value, corrected_value FROM abp_corrections WHERE book=? AND chapter=?
                               AND verse=? AND position=-1""", book, ch, vs)[0]
            self.assertIn("--", s)
            self.assertNotIn("—", s)
            self.assertIn("—", cor)
            self.assertNotIn("--", cor)

    def test_a_differing_before_value_writes_nothing(self):
        c = sqlite3.connect(self.db)
        c.execute("UPDATE words SET english='changed' WHERE position=1 AND english='there will be'")
        c.commit()
        c.close()
        d0 = digest(self.db)
        rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1)
        self.assertIn("STOP", out)
        self.assertEqual(digest(self.db), d0)

    def test_a_failure_mid_write_saves_nothing(self):
        d0 = digest(self.db)
        with mock.patch.object(B, "CHANGES", B.CHANGES + 1):
            rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1, out)
        self.assertEqual(digest(self.db), d0)

    def test_second_apply_refuses(self):
        self.assertEqual(self.run_mode("apply")[0], 0)
        d1 = digest(self.db)
        self.assertEqual(self.run_mode("apply")[0], 1)
        self.assertEqual(digest(self.db), d1)

    def test_undo_restores_every_table_exactly(self):
        d0 = digest(self.db)
        self.assertEqual(self.run_mode("apply")[0], 0)
        self.assertNotEqual(digest(self.db), d0)
        rc, out = self.run_mode("undo")
        self.assertEqual(rc, 0, out)
        self.assertIn("put back: 76 changes", out)
        self.assertEqual(digest(self.db), d0)

    def test_undo_refuses_when_nothing_was_applied(self):
        d0 = digest(self.db)
        self.assertEqual(self.run_mode("undo")[0], 1)
        self.assertEqual(digest(self.db), d0)

    def test_window_refused(self):
        mock.patch.stopall()
        for name, value in (("WORDS", 28), ("VERSES", 15)):
            mock.patch.object(B, name, value).start()
        mock.patch.object(B, "check_feed", lambda *a, **k: None).start()
        with mock.patch.object(B, "datetime", wraps=datetime) as _:
            self.assertTrue(B.in_window(datetime(2026, 11, 23, 13, 0, tzinfo=timezone.utc)))
            self.assertTrue(B.in_window(datetime(2026, 11, 23, 14, 29, tzinfo=timezone.utc)))
            self.assertFalse(B.in_window(datetime(2026, 11, 23, 14, 30, tzinfo=timezone.utc)))
            self.assertFalse(B.in_window(datetime(2026, 11, 23, 12, 59, tzinfo=timezone.utc)))
        d0 = digest(self.db)
        with mock.patch.object(B, "in_window", lambda now=None: True):
            rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1)
        self.assertIn("13:00-14:30", out)
        self.assertEqual(digest(self.db), d0)


if __name__ == "__main__":
    unittest.main()
