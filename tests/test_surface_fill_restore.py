"""Locked tests for the rebuild-trap fix (CHARTER_rebuild_trap_fix.md G1-G3):
scripts/snapshot_surface_fill.py, scripts/restore_surface_fill.py, the health_check floor.

What must hold (feedback_audit_tools_must_fail — every outcome fires on a planted case):
  * snapshot: refuses a file named bible.db and an existing frozen file; G0 stops on a wrong diff;
    the file is byte-identical on a second run; its .sha256 verifies; ordinals are right;
  * restore dry run: places every slot on a same-layout build (agree-weak listed), writes nothing;
  * restore --apply: G1 count exact, forms + new-slot translit written, other rows untouched;
    a second run reads ALREADY RESTORED; a half-restored table FAILS;
  * re-key across a moved layout writes at the NEW positions;
  * reasons 3 / 4 / 6 fire and block the write (database bytes unchanged);
  * G1a stops on a wrong builder total; G1b stops when the builder table != the pre-fill copy;
  * a tampered snapshot is refused (checksum);
  * the health floor: 395,002 rows WARN shortfall 1, 395,003 rows OK.

Run:  python tests/test_surface_fill_restore.py
"""
import contextlib
import csv
import hashlib
import io
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dryrun_rekey_fill as dr            # noqa: E402
import restore_surface_fill as rs         # noqa: E402
import snapshot_surface_fill as sn        # noqa: E402
from build_abp_translit import romanize   # noqa: E402

VERSES = [(1, "Gen", 1, 1), (2, "Gen", 1, 2), (3, "Gen", 1, 3)]
LEMMA = {"G3588": "ὁ", "G3056": "λόγος", "G2316": "θεός", "G2532": "καί", "G1473": "ἐγώ"}
# (verse_id, position, strongs, english)
OLD_WORDS = [(1, 1, "3588", "the"), (1, 2, "3056", "word"), (1, 3, "2316", "of God"),
             (2, 1, "2532", "and"), (2, 2, "2532", "and"),
             (3, 1, "1473", "I")]
BASE = [(1, 1, "τοῦ")]                                     # a builder row, not part of the fill
# fill: (verse_id, position, form, cls, action, old_form)
FILL = [(1, 2, "λόγου", "fill_resolved", "insert", ""),
        (1, 3, "θεοῦ", "normalize_only", "update", "θεου"),
        (2, 2, "και", "fill_resolved", "insert", ""),
        (3, 1, "εγώ", "normalize_only", "insert", "")]
LEXICON = [("3056", "λόγος", "λόγου"), ("2316", "θεός", "θεοῦ"), ("2532", "καί", "και")]


def lem(sb):
    return LEMMA.get(sb, "")


def make_db(path, words, surface):
    """surface rows: (verse_id, position, form) — translit = what build_abp_translit writes."""
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
        CREATE TABLE words(id INTEGER PRIMARY KEY, verse_id INT, position INT, strongs TEXT,
                           strongs_base TEXT, english TEXT, english_head TEXT, is_pn INT);
        CREATE TABLE lexicon(strongs_g TEXT, lemma TEXT);
        CREATE TABLE abp_surface(verse_id INT, position INT, form TEXT, translit TEXT,
                                 PRIMARY KEY (verse_id, position));""")
    c.executemany("INSERT INTO verses VALUES (?,?,?,?)", VERSES)
    c.executemany("INSERT INTO words (verse_id, position, strongs, strongs_base, english, "
                  "english_head, is_pn) VALUES (?,?,?,?,?,?,0)",
                  [(v, p, s, "G" + s, e, e) for v, p, s, e in words])
    c.executemany("INSERT INTO lexicon VALUES (?,?)", sorted(LEMMA.items()))
    sb = {(v, p): "G" + s for v, p, s, _ in words}
    c.executemany("INSERT INTO abp_surface VALUES (?,?,?,?)",
                  [(v, p, f, romanize(f, lem(sb.get((v, p))))) for v, p, f in surface])
    c.commit()
    c.close()


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rows_of(path):
    c = sqlite3.connect(path)
    try:
        return set(c.execute("SELECT verse_id, position, form, translit FROM abp_surface"))
    finally:
        c.close()


PREFILL_SURFACE = BASE + [(1, 3, "θεου")]
OLD_SURFACE = BASE + [(v, p, f) for v, p, f, *_ in FILL]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        p = lambda *n: os.path.join(self.tmp, *n)
        self.old, self.pre, self.built = p("old.sqlite"), p("prefill.sqlite"), p("built.sqlite")
        self.csv, self.lex = p("fill.csv"), p("lexicon.tsv")
        self.snap, self.report = p("fix", "snap.tsv"), p("report.tsv")
        self.live = p("live_stand_in.sqlite")
        make_db(self.old, OLD_WORDS, OLD_SURFACE)
        make_db(self.pre, OLD_WORDS, PREFILL_SURFACE)
        make_db(self.live, OLD_WORDS, OLD_SURFACE)
        with open(self.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["book", "chapter", "verse", "position", "number", "cls", "action",
                        "old_form", "new_form"])
            for v, pos, form, cls, action, old_form in FILL:
                w.writerow(["Gen", 1, v, pos, "", cls, action, old_form, form])
        with open(self.lex, "w", encoding="utf-8", newline="") as f:
            f.write("ab_number\tlemma\tform\n")
            for row in LEXICON:
                f.write("\t".join(row) + "\n")
        self._saved = (dr.EXPECT_DIFF_NEW, dr.EXPECT_DIFF_OLD, dr.N_INSERT, dr.N_UPDATE,
                       sn.N_ROWS, rs.ROWS_BASE, rs.ROWS_AFTER, rs.N_ROWS, rs.N_INSERT, rs.N_UPDATE,
                       rs.SNAPSHOT_SHA256)
        rs.SNAPSHOT_SHA256 = None                  # the planted snapshot is not the pinned one
        dr.EXPECT_DIFF_NEW, dr.EXPECT_DIFF_OLD, dr.N_INSERT, dr.N_UPDATE = 4, 1, 3, 1
        sn.N_ROWS = 4
        rs.ROWS_BASE, rs.ROWS_AFTER, rs.N_ROWS, rs.N_INSERT, rs.N_UPDATE = 2, 5, 4, 3, 1

    def tearDown(self):
        (dr.EXPECT_DIFF_NEW, dr.EXPECT_DIFF_OLD, dr.N_INSERT, dr.N_UPDATE, sn.N_ROWS,
         rs.ROWS_BASE, rs.ROWS_AFTER, rs.N_ROWS, rs.N_INSERT, rs.N_UPDATE,
         rs.SNAPSHOT_SHA256) = self._saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def snapshot(self, **over):
        args = dict(src=self.old, prefill=self.pre, csv=self.csv, out=self.snap)
        args.update(over)
        argv = sum(([f"--{k}", v] for k, v in args.items() if v is not True), [])
        argv += [f"--{k}" for k, v in args.items() if v is True]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = sn.main(argv, live=self.live)
        return rc, buf.getvalue()

    def restore(self, db=None, apply=False, prefill=None):
        argv = [db or self.built, "--snapshot", self.snap, "--lexicon", self.lex,
                "--report", self.report]
        if prefill:
            argv += ["--prefill", prefill]
        if apply:
            argv.append("--apply")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = rs.main(argv, live=self.live)
        return rc, buf.getvalue()


class Snapshot(Base):
    def test_writes_a_deterministic_verified_file(self):
        rc, out = self.snapshot()
        self.assertEqual(rc, 0, out)
        self.assertIn("RESULT: SNAPSHOT WRITTEN", out)
        self.assertIn("inserts / updates       3 / 1 | 3 / 1", out)
        rows, hexd = sn.read_snapshot(self.snap)
        self.assertEqual(hexd, digest(self.snap))
        self.assertEqual(len(rows), 4)
        r22 = next(r for r in rows if (r["verse_id"], r["position"]) == (2, 2))
        self.assertEqual((r22["k2_ordinal"], r22["k2_count"], r22["english"]), (1, 2, "and"))
        r13 = next(r for r in rows if (r["verse_id"], r["position"]) == (1, 3))
        self.assertEqual((r13["action"], r13["old_form"], r13["form"]), ("update", "θεου", "θεοῦ"))
        r12 = next(r for r in rows if (r["verse_id"], r["position"]) == (1, 2))
        self.assertIsNone(r12["old_form"])
        second = os.path.join(self.tmp, "fix", "snap2.tsv")
        rc, out = self.snapshot(out=second)
        self.assertEqual(rc, 0, out)
        self.assertEqual(digest(second), digest(self.snap))

    def test_refuses_bible_db_and_an_existing_frozen_file(self):
        named = os.path.join(self.tmp, "bible.db")
        shutil.copyfile(self.old, named)
        rc, out = self.snapshot(src=named)
        self.assertEqual(rc, 1)
        self.assertIn("is the live database", out)
        self.assertFalse(os.path.exists(self.snap))
        self.assertEqual(self.snapshot()[0], 0)
        rc, out = self.snapshot()
        self.assertEqual(rc, 1)
        self.assertIn("already exists", out)

    def test_g0_stops_on_a_wrong_diff(self):
        dr.EXPECT_DIFF_NEW = 5
        rc, out = self.snapshot()
        self.assertEqual(rc, 1)
        self.assertIn("G0 diff counts are not the fill's", out)
        self.assertFalse(os.path.exists(self.snap))


class SnapshotCheck(Base):
    """--check (/rebuild-words step 1a): an existing frozen file is verified against a fresh copy
    of live, never overwritten. The stale-snapshot cases must STOP and leave the file as it was."""
    def setUp(self):
        super().setUp()
        rc, out = self.snapshot()
        assert rc == 0, out
        self.frozen = digest(self.snap)

    def edit_src(self, sql, *args):
        c = sqlite3.connect(self.old)
        c.execute(sql, args)
        c.commit()
        c.close()

    def assert_stale(self, rc, out, *expect):
        self.assertEqual(rc, 1, out)
        self.assertIn("STALE SNAPSHOT", out)
        for e in expect:
            self.assertIn(e, out)
        self.assertNotIn("SNAPSHOT CURRENT", out)
        self.assertEqual(digest(self.snap), self.frozen)            # never overwritten

    def test_matching_source_reads_current_and_writes_nothing(self):
        before = sorted(os.listdir(os.path.dirname(self.snap)))
        rc, out = self.snapshot(check=True)
        self.assertEqual(rc, 0, out)
        self.assertIn("RESULT: SNAPSHOT CURRENT", out)
        self.assertEqual(digest(self.snap), self.frozen)
        self.assertEqual(sorted(os.listdir(os.path.dirname(self.snap))), before)

    def test_matching_source_reads_current_against_the_pin(self):
        rs.SNAPSHOT_SHA256 = self.frozen
        rc, out = self.snapshot(check=True)
        self.assertEqual(rc, 0, out)
        self.assertIn("= the pin in restore_surface_fill.py", out)

    def test_stale_when_the_source_old_word_row_changed(self):
        # surface table untouched (G0 passes) — only the slot's old English moved: bytes differ
        self.edit_src("UPDATE words SET english='Word' WHERE verse_id=1 AND position=2")
        rc, out = self.snapshot(check=True)
        self.assert_stale(rc, out, "slot (1, 2): differs in english")

    def test_stale_when_a_fill_form_changed_on_live(self):
        self.edit_src("UPDATE abp_surface SET form='λογου' WHERE verse_id=1 AND position=2")
        rc, out = self.snapshot(check=True)
        self.assert_stale(rc, out, "no longer yields the frozen fill", "new_form")

    def test_stale_when_the_live_table_gained_a_row(self):
        self.edit_src("INSERT INTO abp_surface VALUES (3, 9, 'x', '')")
        rc, out = self.snapshot(check=True)
        self.assert_stale(rc, out, "G0 diff counts are not the fill's")

    def test_refuses_a_file_that_is_not_the_pinned_one(self):
        rs.SNAPSHOT_SHA256 = "0" * 64
        rc, out = self.snapshot(check=True)
        self.assert_stale(rc, out, "is not the pinned snapshot")

    def test_refuses_missing_file_and_check_with_replace(self):
        rc, out = self.snapshot(check=True, replace=True)
        self.assertEqual(rc, 1)
        self.assertIn("cannot be used together", out)
        self.assertEqual(digest(self.snap), self.frozen)
        rc, out = self.snapshot(check=True, out=os.path.join(self.tmp, "fix", "none.tsv"))
        self.assertEqual(rc, 1)
        self.assertIn("no frozen snapshot", out)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "fix", "none.tsv")))


class Restore(Base):
    def setUp(self):
        super().setUp()
        rc, out = self.snapshot()
        assert rc == 0, out

    def build(self, words=OLD_WORDS, surface=PREFILL_SURFACE):
        make_db(self.built, words, surface)

    def test_dry_run_places_every_slot_and_writes_nothing(self):
        self.build()
        before = digest(self.built)
        rc, out = self.restore(prefill=self.pre)
        self.assertEqual(rc, 0, out)
        self.assertEqual(digest(self.built), before)
        for line in ("placed                    4 | 4   (agree-strong 3 · agree-weak 1)",
                     "unplaced                  0 | 0", "vs pre-fill copy          0 / 0 | 0 / 0",
                     "placed inserts / updates  3 / 1 | 3 / 1", "AGREE-WEAK rows (1)",
                     "Gen 1:2 · pos 2→2 · 'and' · [1, 2]", "every gate PASSES"):
            self.assertIn(line, out)

    def test_apply_restores_exactly_then_reads_already(self):
        self.build()
        rc, out = self.restore(apply=True, prefill=self.pre)
        self.assertEqual(rc, 0, out)
        self.assertIn("G1 table after            5 | 5", out)
        self.assertIn("RESULT: RESTORED, ALL CHECKS PASS", out)
        self.assertEqual(rows_of(self.built), rows_of(self.old))     # = the table with the fill
        before = digest(self.built)
        rc, out = self.restore()
        self.assertEqual(rc, 0, out)
        self.assertIn("ALREADY RESTORED", out)
        self.assertEqual(digest(self.built), before)

    def test_half_restored_table_fails(self):
        self.build(surface=OLD_SURFACE[:-1] + [(3, 1, "εγω")])    # 5 rows, one slot wrong
        rc, out = self.restore()
        self.assertEqual(rc, 1)
        self.assertIn("not every slot holds its form", out)

    def test_moved_layout_writes_at_new_positions(self):
        moved = [(1, 1, "2532", "and")] + [(v, p + 1 if v == 1 else p, s, e)
                                           for v, p, s, e in OLD_WORDS]
        self.build(words=moved, surface=[(1, 2, "τοῦ"), (1, 4, "θεου")])
        rc, out = self.restore(apply=True)
        self.assertEqual(rc, 0, out)
        self.assertIn("placed rows that moved    — | 2", out)
        got = {(v, p): f for v, p, f, _ in rows_of(self.built)}
        self.assertEqual((got[(1, 3)], got[(1, 4)]), ("λόγου", "θεοῦ"))
        self.assertNotIn((1, 5), got)

    def test_reason_3_update_precondition_blocks_the_write(self):
        self.build(surface=BASE + [(1, 3, "θεός")])               # builder now prints another form
        before = digest(self.built)
        rc, out = self.restore(apply=True)
        self.assertEqual(rc, 1)
        self.assertIn("r3 1", out)
        self.assertIn("STOPPED before any write", out)
        self.assertEqual(digest(self.built), before)

    def test_reason_4_insert_target_filled(self):
        rs.ROWS_BASE = 3
        self.build(surface=PREFILL_SURFACE + [(3, 1, "εγω")])
        rc, out = self.restore(apply=True)
        self.assertEqual(rc, 1)
        self.assertIn("r4 1", out)
        self.assertIn("reason 4 slot holds 'εγω'", out)

    def test_reason_6_english_changed(self):
        self.build(words=[w if w[:2] != (3, 1) else (3, 1, "1473", "me") for w in OLD_WORDS])
        rc, out = self.restore()
        self.assertEqual(rc, 1)
        self.assertIn("r6 1", out)
        self.assertIn("a gate FAILS", out)

    def test_g1a_stops_on_a_wrong_builder_total(self):
        self.build(surface=[(1, 3, "θεου")])                      # a backfill row missing
        rc, out = self.restore(apply=True)
        self.assertEqual(rc, 1)
        self.assertIn("abp_surface = 1 rows — expect 2", out)

    def test_g1b_stops_when_builder_table_differs_from_prefill(self):
        self.build(surface=[(1, 1, "τω"), (1, 3, "θεου")])        # same count, one form differs
        before = digest(self.built)
        rc, out = self.restore(apply=True, prefill=self.pre)
        self.assertEqual(rc, 1)
        self.assertIn("vs pre-fill copy          0 / 0 | 1 / 1", out)
        self.assertIn("G1b builder table != pre-fill copy", out)
        self.assertEqual(digest(self.built), before)

    def test_pinned_checksum_refuses_another_snapshot(self):
        self.build()
        rs.SNAPSHOT_SHA256 = "0" * 64
        rc, out = self.restore()
        self.assertEqual(rc, 1)
        self.assertIn("FAIL  checksum = the pinned", out)

    def test_refuses_live_and_a_tampered_snapshot(self):
        named = os.path.join(self.tmp, "bible.db")
        self.build()
        shutil.copyfile(self.built, named)
        rc, out = self.restore(db=named, apply=True)
        self.assertEqual(rc, 1)
        self.assertIn("COPIES only", out)
        with open(self.snap, "ab") as f:
            f.write(b"x")
        rc, out = self.restore()
        self.assertEqual(rc, 1)
        self.assertIn("file changed", out)


class Floor(unittest.TestCase):
    def health(self, n):
        tmp = tempfile.mkdtemp()
        try:
            db = os.path.join(tmp, "copy.sqlite")
            c = sqlite3.connect(db)
            c.execute("CREATE TABLE abp_surface(verse_id INT, position INT, form TEXT, translit TEXT)")
            c.executemany("INSERT INTO abp_surface VALUES (?,1,'x','')", ((i,) for i in range(n)))
            c.commit()
            c.close()
            p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "health_check.py"), db,
                                "--no-backup-check", "--no-disk-check"], capture_output=True,
                               text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            return next(l for l in p.stdout.splitlines() if "abp_surface rows BELOW floor" in l)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_floor_is_395003(self):
        self.assertIn("[WARN] abp_surface rows BELOW floor 395003", self.health(395002))
        self.assertTrue(self.health(395002).split("]: ")[1].startswith("1 "))
        line = self.health(395003)
        self.assertIn("[OK  ] abp_surface rows BELOW floor 395003", line)
        self.assertTrue(line.split("]: ")[1].startswith("0 "))
        self.assertTrue(self.health(391130).split("]: ")[1].startswith("3873 "))


if __name__ == "__main__":
    unittest.main()
