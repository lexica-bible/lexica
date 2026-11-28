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
        # the other 374 rows = the REAL pinned member list, so the list-sha reads below are real
        for line in Path(B.ACTIVE_OLD).read_text(encoding="utf-8").splitlines():
            bk, ch, vs, pos, fld, led = line.split("\t")
            if (bk, int(ch), int(vs), int(pos), fld) != (*B.EXISTING_PROSE, -1, "verses.text"):
                c.execute(ins, (bk, int(ch), int(vs), int(pos), fld, "a", "b", "filler", led))
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
        rows = self.q("SELECT source_value, corrected_value FROM abp_corrections WHERE book='2Ki' AND chapter=14 AND verse=28 AND position=-1")
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

    def _members(self, db, frozen):
        after = Path(frozen) == B.PUNCT_NEW
        return {"word-order": [], "content-other": [] if after else ["Job 3:3"], "dup-gloss": [], "gone": [],
                "new": [], "changed": [], "same": B.PUNCT_AFTER if after else B.PUNCT_BEFORE, "declared_row": None}

    def test_whole_path_check_apply_after(self):
        """The three steps the block runs, in order, with the real member-list shas."""
        with mock.patch.object(B, "check_fill", lambda p: None), \
             mock.patch.object(B, "member_read", self._members), \
             mock.patch.object(B, "phrase_gloss", lambda db: 700), \
             mock.patch.object(B, "run_cert", lambda db: None):
            rc, out = self.run_mode("check")
            self.assertEqual(rc, 0, out)
            self.assertIn("= 76 changes", out)
            self.assertEqual(self.run_mode("apply")[0], 0)
            rc, out = self.run_mode("after")
            self.assertEqual(rc, 0, out)
            self.assertIn(f"NEW PIN abp_corrections_active: 403, member list sha {B.ACTIVE_NEW_SHA}", out)
            self.assertIn("NEW FROZEN punct list: 601", out)
            self.assertEqual(self.run_mode("check")[0], 1, "check must refuse once the write is in")

    def test_after_refuses_before_the_write(self):
        with mock.patch.object(B, "check_fill", lambda p: None), \
             mock.patch.object(B, "member_read", self._members), \
             mock.patch.object(B, "phrase_gloss", lambda db: 700), \
             mock.patch.object(B, "run_cert", lambda db: None):
            self.assertEqual(self.run_mode("after")[0], 1)

    def test_cert_reads_at_403_and_puts_the_pin_back(self):
        import cert_invariants as C
        pin = C.PINS["abp_corrections_active"]     # 403 after this batch (DESIGN 9.251); 406 since Exo 2:11 (9.268); 1,430 since the split doubles (9.289)
        with mock.patch.dict(C.PINS, {"abp_corrections_active": B.ACTIVE_BEFORE}):
            seen = []
            with mock.patch.object(C, "run_suite", lambda db: seen.append(C.PINS["abp_corrections_active"]) or 0):
                B.run_cert(self.db)
            self.assertEqual(seen, [B.ACTIVE_AFTER])
            self.assertEqual(C.PINS["abp_corrections_active"], B.ACTIVE_BEFORE)
            with mock.patch.object(C, "run_suite", lambda db: 1):
                with self.assertRaises(B.Stop):
                    B.run_cert(self.db)
            self.assertEqual(C.PINS["abp_corrections_active"], B.ACTIVE_BEFORE)
        import apply_split_doubles_20261126 as S    # since 11/28 (DESIGN 9.289): 406 + 1,024 = 1,430
        self.assertEqual(pin, S.ACTIVE_BEFORE + 2 * S.ROWS_N)       # the latest write that moved the pin

    def _audit_db(self, name, control=True, lsj=True):
        p = os.path.join(self.tmp.name, name)
        c = sqlite3.connect(p)
        c.executescript("""
            CREATE TABLE lexicon (strongs TEXT, lemma TEXT, kjv_def TEXT, strongs_def TEXT);
            CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
            CREATE TABLE words (verse_id INT, position INT, english TEXT, strongs_base TEXT);
            INSERT INTO lexicon VALUES ('264', 'x', 'sin', ''), ('3361', 'y', 'not', '');
        """)
        if lsj:
            c.execute("CREATE TABLE lsj (plain TEXT, def_html TEXT)")
        c.execute("INSERT INTO verses VALUES (1, ?, ?, 1)", ("Psa", 39) if control else ("Gen", 1))
        c.execute("INSERT INTO words VALUES (1, 0, 'to not sin', 'G3361')")
        c.execute("INSERT INTO words VALUES (1, 1, '', 'G264')")
        c.commit()
        c.close()
        return p

    def test_phrase_gloss_reads_the_real_audit(self):
        """Runs the PRODUCTION audit: this is the read that stopped the 11/22 re-run."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            n = B.phrase_gloss(self._audit_db("a.db"))
        self.assertEqual(n, 1)
        self.assertIn("control fired", out.getvalue())

    def test_phrase_gloss_stops_when_its_control_misses(self):
        with self.assertRaises(B.Stop) as e:
            B.phrase_gloss(self._audit_db("b.db", control=False))
        self.assertIn("CONTROL Psa 39:1: MISSED", str(e.exception))

    def test_phrase_gloss_stops_when_an_input_is_missing(self):
        with self.assertRaises(B.Stop) as e:
            B.phrase_gloss(self._audit_db("c.db", lsj=False))
        self.assertIn("without a required input", str(e.exception))

    def test_phrase_gloss_stops_above_the_gate(self):
        with mock.patch.object(B, "PHRASE_GATE", 0), self.assertRaises(B.Stop) as e:
            B.phrase_gloss(self._audit_db("d.db"))
        self.assertIn("above the gate", str(e.exception))

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
