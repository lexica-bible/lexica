"""The 10 printed-form cells write (scripts/apply_surface_formcells_20261126.py, DESIGN 9.266 / 9.269), on a
throwaway database built from the cleared before-values. Proves: it writes exactly the 10 slots and nothing
else; undo puts the table back byte for byte; any differing before-value, a second apply, the nightly window,
a spelling that is not the rule's, a pre-fill table that is not as recorded, and an amendment file that does
not match the write each save nothing. Never touches bible.db.

Run:  python tests/test_surface_formcells.py
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
import apply_bible_text_batch_20261122 as B          # noqa: E402
import apply_surface_formcells_20261126 as F         # noqa: E402

LEX = {"G3588": "ὁ", "G3739": "ὅς", "G2532": "καί", "G3754": "ὅτι", "G1510": "εἰμί", "G3140": "μαρτυρέω",
       "G1093": "γῆ"}


class FormCells(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, "t.db")
        self.pre = os.path.join(self.tmp.name, "prefill.db")
        self.plan = F.load_plan()
        self.make(self.db, {p["key"]: p["before"] for p in self.plan})
        self.make(self.pre, {k: (f, "x") for k, f in F.PREFILL_AT.items()})
        for obj, name, value in ((F, "SURFACE_BEFORE", 3 + 4), (F, "SURFACE_AFTER", 3 + 8),
                                 (B, "WORDS", len(F.STRONGS) + 1), (B, "VERSES", 6),
                                 (B, "in_window", lambda now=None: False)):
            p = mock.patch.object(obj, name, value)
            p.start()
            self.addCleanup(p.stop)

    def make(self, path, cells):
        c = sqlite3.connect(path)
        c.executescript("""CREATE TABLE verses (id INTEGER PRIMARY KEY, book, chapter INT, verse INT);
            CREATE TABLE words (verse_id INT, position INT, strongs, strongs_base);
            CREATE TABLE lexicon (strongs_g, lemma);
            CREATE TABLE abp_surface (verse_id INT, position INT, form TEXT, translit TEXT, PRIMARY KEY (verse_id, position));""")
        c.executemany("INSERT INTO lexicon VALUES (?,?)", LEX.items())
        vid = {}
        for key, s in F.STRONGS.items():
            v = vid.get(key[:3]) or c.execute("INSERT INTO verses (book, chapter, verse) VALUES (?,?,?)", key[:3]).lastrowid
            vid[key[:3]] = v
            c.execute("INSERT INTO words VALUES (?,?,?,?)", (v, key[3], s, "G" + s.split(".")[0]))
            if cells.get(key):
                c.execute("INSERT INTO abp_surface VALUES (?,?,?,?)", (v, key[3], *cells[key]))
        c.execute("INSERT INTO words VALUES (1, 99, '3588', 'G3588')")                  # an untouched slot
        for pos, f in ((99, "τον"), (98, "των"), (97, "τοις")):                             # three other rows
            from build_abp_translit import romanize
            c.execute("INSERT INTO abp_surface VALUES (1, ?, ?, ?)", (pos, f, romanize(f, "ὁ")))
        c.commit()
        c.close()

    def run_mode(self, mode):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = F.main([mode, "--db", self.db, "--prefill", self.pre])
        return rc, out.getvalue()

    def digest(self):
        c = sqlite3.connect(self.db)
        h = hashlib.sha256(repr(sorted(c.execute("SELECT * FROM abp_surface"))).encode()).hexdigest()
        c.close()
        return h

    def table(self):
        c = sqlite3.connect(self.db)
        t = {(v, p): (f, tl) for v, p, f, tl in c.execute("SELECT * FROM abp_surface")}
        c.close()
        return t

    def test_the_plan(self):
        kinds = sorted((bool(p["before"]), bool(p["after"])) for p in self.plan)
        self.assertEqual(kinds.count((False, True)), 6)
        self.assertEqual(kinds.count((True, True)), 2)
        self.assertEqual(kinds.count((True, False)), 2)

    def test_check_apply_after_then_undo(self):
        start, t0 = self.digest(), self.table()
        outs = {}
        for mode in ("check", "apply", "after"):
            rc, outs[mode] = self.run_mode(mode)
            self.assertEqual(rc, 0, outs[mode])
        self.assertIn("written: 10 changes, every result read back, every other row unchanged", outs["apply"])
        self.assertIn("after-values: all 10 slots as cleared", outs["after"])
        t1 = self.table()
        changed = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
        self.assertEqual(len(changed), 10)
        self.assertEqual({k: t1[k] for k in t1 if k[1] in (97, 98, 99)}, {k: t0[k] for k in t0 if k[1] in (97, 98, 99)})
        rc, out = self.run_mode("undo")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.digest(), start)

    def test_a_differing_before_value_saves_nothing(self):
        c = sqlite3.connect(self.db)
        c.execute("UPDATE abp_surface SET translit='psu' WHERE form='ψου'")
        c.commit()
        c.close()
        start = self.digest()
        for mode in ("check", "apply"):
            rc, out = self.run_mode(mode)
            self.assertEqual(rc, 1, out)
            self.assertIn("RESULT: STOP", out)
        self.assertEqual(self.digest(), start)

    def test_applying_twice_saves_nothing_more(self):
        self.assertEqual(self.run_mode("apply")[0], 0)
        once = self.digest()
        rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.digest(), once)

    def test_refuses_the_nightly_window(self):
        start = self.digest()
        with mock.patch.object(B, "in_window", lambda now=None: True):
            rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1)
        self.assertIn("13:00-14:30 UTC", out)
        self.assertEqual(self.digest(), start)

    def test_a_spelling_that_is_not_the_rule_stops(self):
        c = sqlite3.connect(self.db)
        c.execute("UPDATE lexicon SET lemma='ο' WHERE strongs_g='G3588'")      # no rough breathing: οι -> oi, not hoi
        c.commit()
        c.close()
        rc, out = self.run_mode("check")
        self.assertEqual(rc, 1)
        self.assertIn("cleared spelling", out)

    def test_a_prefill_table_not_as_recorded_stops(self):
        c = sqlite3.connect(self.pre)
        c.execute("UPDATE abp_surface SET form='και' WHERE form='ανδ'")
        c.commit()
        c.close()
        rc, out = self.run_mode("check")
        self.assertEqual(rc, 1)
        self.assertIn("pre-fill holds", out)

    def test_an_amendment_file_not_matching_the_write_stops(self):
        text = F.AMEND.read_text(encoding="utf-8").replace("\tγης\t", "\tγη\t")
        p = Path(self.tmp.name) / "amend.tsv"
        p.write_bytes(text.encode("utf-8"))
        with mock.patch.object(F, "AMEND", p), mock.patch.object(F, "AMEND_SHA", B.sha(p)):
            start = self.digest()
            rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1)
        self.assertIn("does not fit", out)
        self.assertEqual(self.digest(), start)


if __name__ == "__main__":
    unittest.main()
