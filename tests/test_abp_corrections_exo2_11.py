"""The Exo 2:11 write (scripts/apply_abp_corrections_exo2_11_20261124.py, DESIGN 9.266), on a throwaway
database built from the cleared before-values plus the REAL 403-row member list. Proves: it writes exactly the
three cleared cells, the head word's finder key, and three correction rows; the active list after it is the new pinned member file; any
differing before-value writes nothing; a second apply writes nothing; it refuses the nightly window; undo puts
every table back byte for byte. Never touches bible.db.

Run:  python tests/test_abp_corrections_exo2_11.py
"""
import contextlib
import hashlib
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_abp_corrections_exo2_11_20261124 as E   # noqa: E402
import apply_bible_text_batch_20261122 as B          # noqa: E402

TABLES = {"verses": "id, book, chapter, verse, text", "words": "verse_id, position, english, english_head, english_head_norm",
          "abp_corrections": "book, chapter, verse, position, field, source_value, corrected_value, reason, ledger_ref, "
                             "applied_at, status, created"}


class Exo211(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, "t.db")
        self.plan = E.load_plan()
        c = sqlite3.connect(self.db)
        c.executescript("""
            CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
            CREATE TABLE words (verse_id INT, position INT, english TEXT, english_head TEXT, english_head_norm TEXT);
            CREATE TABLE kjv_strongs (word_id INT, strongs_id TEXT);
            CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, book TEXT NOT NULL, chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL, position INTEGER NOT NULL, field TEXT NOT NULL, source_value TEXT,
                corrected_value TEXT, reason TEXT NOT NULL, ledger_ref TEXT, applied_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active', created TEXT NOT NULL);
        """)
        vid = c.execute("INSERT INTO verses (book, chapter, verse, text) VALUES ('Exo', 2, 11, ?)",
                        (self.plan["prose"]["before"],)).lastrowid
        other = c.execute("INSERT INTO verses (book, chapter, verse, text) VALUES ('Exo', 2, 12, 'old er')").lastrowid
        c.execute("INSERT INTO words VALUES (?, 8, 'old er', 'er', 'er')", (vid,))
        c.execute("INSERT INTO words VALUES (?, 9, 'old er', 'er', 'er')", (vid,))      # same text, another slot
        c.execute("INSERT INTO words VALUES (?, 8, 'old er', 'er', 'er')", (other,))    # same slot, another verse
        ins = """INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value, reason,
                 ledger_ref, applied_at, status, created) VALUES (?,?,?,?,?,'a','b','filler',?,'ingest','active','2026-11-22')"""
        for line in Path(E.ACTIVE_OLD).read_text(encoding="utf-8").splitlines():
            bk, ch, vs, pos, fld, led = line.split("\t")
            c.execute(ins, (bk, int(ch), int(vs), int(pos), fld, led))
        c.execute("""INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value, reason,
                     ledger_ref, applied_at, status, created) VALUES ('Gen',1,1,0,'english','x','y','retired','R','ingest',
                     'retired','2026-01-01')""")                                  # not active: never counted
        c.commit()
        c.close()
        for obj, name, value in ((B, "WORDS", 3), (B, "VERSES", 2), (E, "check_feed", lambda plan: None),
                                 (E, "_gates", lambda db, plan: None), (E, "run_cert", lambda db: None),
                                 (B, "in_window", lambda now=None: False)):
            p = mock.patch.object(obj, name, value)
            p.start()
            self.addCleanup(p.stop)

    def run_mode(self, mode):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = E.main([mode, "--db", self.db])
        return rc, out.getvalue()

    def digest(self):
        c = sqlite3.connect(self.db)
        h = hashlib.sha256()
        for t, cols in TABLES.items():
            for r in c.execute(f"SELECT {cols} FROM {t} ORDER BY {cols}"):
                h.update(repr(r).encode("utf-8"))
        c.close()
        return h.hexdigest()

    def q(self, sql, *a):
        c = sqlite3.connect(self.db)
        r = c.execute(sql, a).fetchall()
        c.close()
        return r

    def test_plan_is_rows_1_to_3(self):
        self.assertEqual(self.plan["prose"]["after"].count("older"), 1)
        self.assertEqual([(w["field"], w["before"], w["after"]) for w in self.plan["words"]],
                         [("english", "old er", "older"), ("english_head", "er", "older"),
                          ("english_head_norm", "er", "older")])
        rows = E.new_rows(self.plan)
        self.assertEqual(len(rows), E.ACTIVE_AFTER - E.ACTIVE_BEFORE)
        self.assertNotIn("english_head_norm", [r[4] for r in rows])     # recomputed at rebuild, no correction row

    def test_member_files(self):
        old = Path(E.ACTIVE_OLD).read_text(encoding="utf-8").splitlines()
        new = Path(E.ACTIVE_NEW).read_text(encoding="utf-8").splitlines()
        self.assertEqual((len(old), len(new)), (403, 406))
        self.assertEqual(sorted(set(new) - set(old)), sorted(f"Exo\t2\t11\t{p}\t{f}\tEU-Exo2:11" for p, f in
                                                             ((-1, "verses.text"), (8, "english"), (8, "english_head"))))
        self.assertEqual(B.sha(E.ACTIVE_NEW), E.ACTIVE_NEW_SHA)
        self.assertEqual(B.sha(E.ACTIVE_OLD), E.ACTIVE_OLD_SHA)

    def test_check_apply_after_then_undo(self):
        start = self.digest()
        rc, out = self.run_mode("check")
        self.assertEqual(rc, 0, out)
        rc, out = self.run_mode("apply")
        self.assertEqual(rc, 0, out)
        self.assertIn("written: 7 changes", out)
        rc, out = self.run_mode("after")
        self.assertEqual(rc, 0, out)
        self.assertIn(f"NEW PIN abp_corrections_active: 406, member list sha {E.ACTIVE_NEW_SHA}", out)
        self.assertEqual(self.q("SELECT english, english_head, english_head_norm FROM words ORDER BY verse_id, position"),
                         [("older", "older", "older"), ("old er", "er", "er"), ("old er", "er", "er")])
        self.assertEqual(self.q("SELECT text FROM verses WHERE verse=12"), [("old er",)])
        rc, out = self.run_mode("undo")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.digest(), start)

    def test_a_differing_before_value_saves_nothing(self):
        c = sqlite3.connect(self.db)
        c.execute("UPDATE words SET english_head='old' WHERE position=8 AND verse_id=1")
        c.commit()
        c.close()
        start = self.digest()
        for mode in ("check", "apply"):
            rc, out = self.run_mode(mode)
            self.assertEqual(rc, 1, out)
            self.assertIn("RESULT: STOP", out)
        self.assertEqual(self.digest(), start)

    def test_applying_twice_saves_nothing_more(self):
        self.run_mode("apply")
        once = self.digest()
        rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.digest(), once)

    def test_a_stale_finder_key_saves_nothing(self):
        c = sqlite3.connect(self.db)
        c.execute("UPDATE words SET english_head_norm=NULL WHERE position=8 AND verse_id=1")
        c.commit()
        c.close()
        start = self.digest()
        rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1, out)
        self.assertIn("english_head_norm", out)
        self.assertEqual(self.digest(), start)

    def test_refuses_the_nightly_window(self):
        start = self.digest()
        with mock.patch.object(B, "in_window", lambda now=None: True):
            rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1, out)
        self.assertIn("13:00-14:30 UTC", out)
        self.assertEqual(self.digest(), start)


if __name__ == "__main__":
    unittest.main()
