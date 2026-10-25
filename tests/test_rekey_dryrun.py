"""Locked tests for scripts/dryrun_rekey_fill.py (rebuild-trap re-key dry run,
CHARTER_rebuild_trap_fix.md §6).

What must hold (feedback_audit_tools_must_fail — every outcome fires on a planted case):
  * the live-path gate REFUSES (a file named bible.db, the live path by another spelling,
    the same file twice, a .db report path) and writes no report;
  * each reason fires on its planted verse: placed-and-moved, 7 key conflict, 6 key 1 none,
    6 key 1 several, 1 key 2 none; an uncovered class is placed without the witness;
  * the C1 identity control STOPS the run when a fill verse has a duplicate position;
  * no database file changes (bytes identical before and after).

Run:  python tests/test_rekey_dryrun.py
"""
import contextlib
import csv
import hashlib
import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dryrun_rekey_fill as dr   # noqa: E402

VERSES = [(i, "Gen", 1, i) for i in range(1, 7)]
OLD_WORDS = [
    (1, 1, "3588", "the", 0), (1, 2, "3056", "word", 0), (1, 3, "2316", "of God", 0),
    (2, 1, "2316", "God", 0), (2, 2, "2316", "God,", 0),
    (3, 1, "3056", "word", 0),
    (4, 1, "3056", "word", 0),
    (5, 1, "2532", "and", 0), (5, 2, "2532", "and", 0),
    (6, 1, "3588", "the", 0),
]
BUILT_WORDS = [
    (1, 1, "2532", "and", 0), (1, 2, "3588", "the", 0), (1, 3, "3056", "word", 0),
    (1, 4, "2316", "of God", 0),                       # a slot added in front: everything moves
    (2, 1, "2316", "God,", 0), (2, 2, "2316", "God", 0),   # English swapped: keys disagree
    (3, 1, "3056", "saying", 0),                       # English changed: key 1 finds none
    (4, 1, "3057", "word", 0),                         # number changed: key 2 finds none
    (5, 1, "2532", "and", 0), (5, 2, "2532", "and", 0),    # repeated English: key 1 several
    (6, 1, "3588", "the", 0),
]
# fill rows: (verse_id, position, form, cls, action, old_form)
FILL = [
    (1, 2, "λόγου", "fill_resolved", "insert", ""),
    (2, 2, "θεοῦ", "fill_resolved", "insert", ""),
    (3, 1, "λόγου", "fill_resolved", "insert", ""),
    (4, 1, "λόγου", "fill_resolved", "insert", ""),
    (5, 2, "και", "fill_resolved", "insert", ""),
    (6, 1, "τοῦ", "normalize_only", "update", "τω"),
]
LEXICON = [("3056", "λόγος", "λόγου"), ("2316", "θεός", "θεοῦ"),
           ("2532", "καί", "και"), ("3588", "ὁ", "τοῦ")]


def make_db(path, words, surface):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
        CREATE TABLE words(id INTEGER PRIMARY KEY, verse_id INT, position INT, strongs TEXT,
                           english TEXT, is_pn INT);
        CREATE TABLE abp_surface(verse_id INT, position INT, form TEXT, translit TEXT,
                                 PRIMARY KEY (verse_id, position));""")
    c.executemany("INSERT INTO verses VALUES (?,?,?,?)", VERSES)
    c.executemany("INSERT INTO words (verse_id, position, strongs, english, is_pn) "
                  "VALUES (?,?,?,?,?)", words)
    c.executemany("INSERT INTO abp_surface VALUES (?,?,?,?)", surface)
    c.commit()
    c.close()


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class RekeyDryRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        p = lambda n: os.path.join(self.tmp, n)
        self.old, self.pre, self.built = p("old.sqlite"), p("prefill.sqlite"), p("built.sqlite")
        self.csv, self.lex, self.out = p("fill.csv"), p("lexicon.tsv"), p("report.tsv")
        self.live = p("live_stand_in.sqlite")
        base = [(1, 1, "τοῦ", "")]                     # a non-fill row, same on both sides
        prefill_rows = base + [(6, 1, "τω", "")]
        old_rows = base + [(v, pos, form, "") for v, pos, form, *_ in FILL]
        make_db(self.old, OLD_WORDS, old_rows)
        make_db(self.pre, OLD_WORDS, prefill_rows)
        make_db(self.built, BUILT_WORDS, prefill_rows)    # step 9 not run: stale table, unread
        make_db(self.live, OLD_WORDS, old_rows)
        with open(self.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["book", "chapter", "verse", "position", "number", "cls", "action",
                        "old_form", "new_form"])
            for v, pos, form, cls, action, old_form in FILL:
                w.writerow(["Gen", 1, v, pos, "", cls, action, old_form, form])
            w.writerow(["Gen", 1, 1, 3, "", "fill_resolved", "hold", "", ""])  # holds ignored
        with open(self.lex, "w", encoding="utf-8", newline="") as f:
            f.write("ab_number\tlemma\tform\n")
            for row in LEXICON:
                f.write("\t".join(row) + "\n")
        self._saved = (dr.EXPECT_DIFF_NEW, dr.EXPECT_DIFF_OLD, dr.N_INSERT, dr.N_UPDATE)
        dr.EXPECT_DIFF_NEW, dr.EXPECT_DIFF_OLD, dr.N_INSERT, dr.N_UPDATE = 6, 1, 5, 1

    def tearDown(self):
        dr.EXPECT_DIFF_NEW, dr.EXPECT_DIFF_OLD, dr.N_INSERT, dr.N_UPDATE = self._saved

    def run_dr(self, **over):
        args = dict(old=self.old, prefill=self.pre, built=self.built, csv=self.csv,
                    lexicon=self.lex, out=self.out)
        args.update(over)
        argv = sum(([f"--{k}", v] for k, v in args.items()), [])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = dr.main(argv, live=self.live)
        return rc, buf.getvalue()

    # ── the live-path gate ──
    def test_refuses_a_file_named_bible_db(self):
        named = os.path.join(self.tmp, "bible.db")
        shutil.copyfile(self.old, named)
        rc, out = self.run_dr(old=named)
        self.assertEqual(rc, 1)
        self.assertIn("is the live database", out)
        self.assertFalse(os.path.exists(self.out))

    def test_refuses_the_live_path_by_another_spelling(self):
        sneaky = os.path.join(self.tmp, "sub", "..", "live_stand_in.sqlite")
        os.makedirs(os.path.join(self.tmp, "sub"))
        rc, out = self.run_dr(built=sneaky)
        self.assertEqual(rc, 1)
        self.assertIn("is the live database", out)
        self.assertFalse(os.path.exists(self.out))

    def test_refuses_the_same_file_twice(self):
        rc, out = self.run_dr(built=self.old)
        self.assertEqual(rc, 1)
        self.assertIn("three different files", out)

    def test_refuses_a_db_report_path(self):
        rc, out = self.run_dr(out=os.path.join(self.tmp, "report.db"))
        self.assertEqual(rc, 1)
        self.assertIn("must be a new report file", out)

    # ── every outcome fires ──
    def test_reasons_fire_and_nothing_is_written(self):
        before = [digest(x) for x in (self.old, self.pre, self.built)]
        rc, out = self.run_dr()
        self.assertEqual(rc, 0, out)
        self.assertEqual(before, [digest(x) for x in (self.old, self.pre, self.built)])
        for line in ("C1  identity control", "C2  witness negative control",
                     "placed 2 · unplaced 4 · total 6",
                     "reason 1: key 2 none, key 1 none", "reason 6: key 1 none",
                     "reason 6: key 1 several, incl. key 2's slot",
                     "reason 7: both one slot, different",
                     "placed rows whose position moved: 1",
                     "Lexicon-UNCOVERED group (all 4,411, by class): 1",
                     "RESULT: DRY RUN COMPLETE"):
            self.assertIn(line, out)
        with open(self.out, encoding="utf-8") as f:
            rows = {(r["verse"], r["old_position"]): r
                    for r in csv.DictReader(f, delimiter="\t")}
        self.assertEqual((rows[("1", "2")]["reason"], rows[("1", "2")]["new_position"]),
                         ("placed", "3"))
        self.assertEqual(rows[("1", "2")]["lexicon"], "pass")
        self.assertEqual(rows[("2", "2")]["reason"], "7")
        self.assertEqual(rows[("3", "1")]["reason"], "6")
        self.assertEqual(rows[("4", "1")]["reason"], "1")
        self.assertEqual(rows[("5", "2")]["reason"], "6")
        self.assertEqual((rows[("6", "1")]["reason"], rows[("6", "1")]["lexicon"]),
                         ("placed", "uncovered"))

    def test_g0_stops_when_the_diff_is_not_the_fill(self):
        dr.EXPECT_DIFF_NEW = 7
        rc, out = self.run_dr()
        self.assertEqual(rc, 1)
        self.assertIn("G0 diff counts are not the fill's", out)
        self.assertFalse(os.path.exists(self.out))

    def test_c1_stops_on_a_duplicate_position(self):
        c = sqlite3.connect(self.old)
        c.execute("INSERT INTO words (verse_id, position, strongs, english, is_pn) "
                  "VALUES (1, 2, '3056', 'word', 0)")
        c.commit()
        c.close()
        rc, out = self.run_dr()
        self.assertEqual(rc, 1)
        self.assertIn("C1 identity control failed", out)
        self.assertFalse(os.path.exists(self.out))


if __name__ == "__main__":
    unittest.main()
