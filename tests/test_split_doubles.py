"""The split double rows write (scripts/apply_split_doubles_20261126.py, DESIGN 9.280), on a throwaway database
built from the rows file's own before-values. Proves: it changes exactly the planned number cells, correction
rows and printed forms and nothing else; undo puts every table back byte for byte; a differing before-value, a
second apply, the nightly window, an existing correction on a written row, and a kept row that already holds a
form where one is to move each save nothing. Never touches bible.db. The word-order, phrase-gloss and cert
gates read the real corpus and are not run here (check / after on PA run them).

Run:  python tests/test_split_doubles.py
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
import apply_split_doubles_20261126 as A             # noqa: E402
from build_abp_corrections import SCHEMA             # noqa: E402
from build_abp_translit import romanize              # noqa: E402

PLAN = A.load_plan()
REAL_SURFACE = (A.SURFACE_BEFORE, A.SURFACE_AFTER)      # before setUp patches them


class SplitDoubles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, "t.db")
        n_surface, n_words, n_verses = self.make()
        for obj, name, value in ((A, "SURFACE_BEFORE", n_surface),
                                 (A, "SURFACE_AFTER", n_surface - A.SURFACE_N[0] + A.SURFACE_N[1]),
                                 (B, "WORDS", n_words), (B, "VERSES", n_verses),
                                 (A, "in_window", lambda now=None: False),
                                 (A, "_gates", lambda db: None), (A, "run_cert", lambda db: None)):
            p = mock.patch.object(obj, name, value)
            p.start()
            self.addCleanup(p.stop)
        # fill_note reads the 11/26 frozen fill against restore_surface_fill's pin. That pin moved to the 11/27
        # re-freeze after the live write (DESIGN 9.289), and the note was information for the pre-write check
        # only, so it is stood in here (the fill is git-ignored ABP text anyway: absent on CI).
        p = mock.patch.object(A, "fill_note", lambda conn, plan: print("frozen fill: note stood in (pin moved 11/28)"))
        p.start()
        self.addCleanup(p.stop)

    def make(self):
        """verses / words / abp_surface / abp_corrections / lexicon shaped like live's, holding only the plan's
        rows, one untouched word and form per verse, and the 406 active corrections of the pinned member list."""
        c = sqlite3.connect(self.db)
        c.executescript("""CREATE TABLE verses (id INTEGER PRIMARY KEY, book, chapter INT, verse INT, text);
            CREATE TABLE words (verse_id INT, position INT, english, english_head, strongs, strongs_base,
                                greek_pos INT, bracket_id INT);
            CREATE TABLE lexicon (strongs_g, lemma);
            CREATE TABLE abp_surface (verse_id INT, position INT, form TEXT, translit TEXT,
                                      PRIMARY KEY (verse_id, position));""")
        c.executescript(SCHEMA)
        vid = {}
        for w in PLAN:
            if w["key3"] not in vid:
                vid[w["key3"]] = c.execute("INSERT INTO verses (book, chapter, verse) VALUES (?,?,?)", w["key3"]).lastrowid
                c.execute("INSERT INTO words VALUES (?, 999, 'other', 'other', '2532', 'G2532', NULL, NULL)",
                          (vid[w["key3"]],))
                c.execute("INSERT INTO abp_surface VALUES (?, 999, 'και', ?)", (vid[w["key3"]], romanize("και", "")))
            v, num = vid[w["key3"]], w["number"]
            base = "G" + num.split(".")[0]
            c.execute("INSERT INTO words VALUES (?,?,?,?,?,?,1,1)", (v, w["keep"], w["keep_eng"], w["keep_eng"], num, base))
            if not w["move"]:
                f = next((s["form"] for s in w["strip"] if s["form"]), None)
                if f:
                    c.execute("INSERT INTO abp_surface VALUES (?,?,?,?)", (v, w["keep"], f, romanize(f, "")))
            for s in w["strip"]:
                c.execute("INSERT INTO words VALUES (?,?,?,?,?,?,2,1)", (v, s["pos"], s["eng"], s["eng"], num, base))
                if s["form"]:
                    c.execute("INSERT INTO abp_surface VALUES (?,?,?,?)", (v, s["pos"], s["form"], romanize(s["form"], "")))
        for line in A.ACTIVE_OLD.read_text(encoding="utf-8").splitlines():
            b, ch, vs, pos, fld, led = line.split("\t")
            c.execute("""INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value,
                         reason, ledger_ref, applied_at, status, created) VALUES (?,?,?,?,?,'a','b','r',?,'ingest','active','x')""",
                      (b, int(ch), int(vs), int(pos), fld, led))
        c.commit()
        counts = [c.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("abp_surface", "words", "verses")]
        c.close()
        return counts

    def run_mode(self, mode):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = A.main([mode, "--db", self.db])
        return rc, out.getvalue()

    def tables(self):
        c = sqlite3.connect(self.db)
        t = {name: sorted(c.execute(f"SELECT * FROM {name}"), key=repr)
             for name in ("words", "abp_surface")}
        t["abp_corrections"] = sorted(c.execute("SELECT book, chapter, verse, position, field, source_value, "
                                                "corrected_value, ledger_ref, status FROM abp_corrections"), key=repr)
        c.close()
        return t

    def digest(self):
        return hashlib.sha256(repr(self.tables()).encode()).hexdigest()

    def test_the_plan(self):
        self.assertEqual(len(PLAN), 506)
        self.assertEqual(sum(len(w["strip"]) for w in PLAN), 512)
        self.assertEqual(len(A.new_rows(PLAN)), 1024)
        self.assertEqual(A.changes(PLAN), 512 + 1024 + 482 + 17)
        self.assertEqual(REAL_SURFACE, (395018, 394553))

    def test_the_member_list_is_the_old_one_plus_the_new_rows(self):
        old = [tuple(l.split("\t")) for l in A.ACTIVE_OLD.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(A.member_lines(old, PLAN), A.ACTIVE_NEW.read_text(encoding="utf-8"))
        self.assertEqual(B.sha(A.ACTIVE_NEW), A.ACTIVE_NEW_SHA)

    def test_check_apply_after_then_undo(self):
        start, t0 = self.digest(), self.tables()
        outs = {}
        for mode in ("check", "apply", "after"):
            rc, outs[mode] = self.run_mode(mode)
            self.assertEqual(rc, 0, outs[mode][-3000:])
        self.assertIn("written: 2,035 changes".replace(",", ""), outs["apply"].replace(",", ""))
        self.assertIn("2Sa 3:35 @5", outs["check"])
        self.assertIn("active corrections on a written (verse, position): 0", outs["check"])
        t1 = self.tables()
        w0, w1 = set(t0["words"]), set(t1["words"])
        self.assertEqual(len(w0 - w1), 512)
        self.assertTrue(all(r[4] == "" and r[5] == "" for r in w1 - w0))
        self.assertEqual({r[:4] + r[6:] for r in w0 - w1}, {r[:4] + r[6:] for r in w1 - w0})   # english, order kept
        s0, s1 = set(t0["abp_surface"]), set(t1["abp_surface"])
        self.assertEqual((len(s0 - s1), len(s1 - s0)), (482, 17))
        self.assertEqual(len(t1["abp_corrections"]) - len(t0["abp_corrections"]), 1024)
        rc, out = self.run_mode("undo")
        self.assertEqual(rc, 0, out[-3000:])
        self.assertEqual(self.digest(), start)

    def test_a_differing_before_value_saves_nothing(self):
        c = sqlite3.connect(self.db)
        w = PLAN[100]
        c.execute("UPDATE words SET english='changed' WHERE position=? AND verse_id=(SELECT id FROM verses "
                  "WHERE book=? AND chapter=? AND verse=?)", (w["strip"][0]["pos"], *w["key3"]))
        c.commit()
        c.close()
        start = self.digest()
        for mode in ("check", "apply"):
            rc, out = self.run_mode(mode)
            self.assertEqual(rc, 1, out[-2000:])
            self.assertIn("RESULT: STOP", out)
        self.assertEqual(self.digest(), start)

    def test_applying_twice_saves_nothing_more(self):
        self.assertEqual(self.run_mode("apply")[0], 0)
        once = self.digest()
        rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1, out[-2000:])
        self.assertEqual(self.digest(), once)

    def test_refuses_the_nightly_window(self):
        start = self.digest()
        with mock.patch.object(A, "in_window", lambda now=None: True):
            rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1)
        self.assertIn("12:30-14:30 UTC", out)
        self.assertEqual(self.digest(), start)

    def test_an_existing_correction_on_a_written_row_stops_the_check(self):
        c = sqlite3.connect(self.db)
        w = PLAN[0]
        c.execute("""INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value,
                     reason, ledger_ref, applied_at, status, created) VALUES (?,?,?,?,'english','a','b','r','T','read','active','x')""",
                  (*w["key3"], w["keep"]))
        c.commit()
        c.close()
        rc, out = self.run_mode("check")
        self.assertEqual(rc, 1)
        self.assertIn("already carries a correction", out)

    def test_a_kept_row_that_already_holds_a_form_stops(self):
        w = next(w for w in PLAN if w["move"])
        c = sqlite3.connect(self.db)
        v = c.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?", w["key3"]).fetchone()[0]
        c.execute("INSERT INTO abp_surface VALUES (?,?,?,?)", (v, w["keep"], w["move"][1], "x"))
        c.commit()
        c.close()
        with mock.patch.object(A, "SURFACE_BEFORE", A.SURFACE_BEFORE + 1):
            start = self.digest()
            rc, out = self.run_mode("apply")
        self.assertEqual(rc, 1, out[-2000:])
        self.assertIn("kept row form", out)
        self.assertEqual(self.digest(), start)


if __name__ == "__main__":
    unittest.main()
