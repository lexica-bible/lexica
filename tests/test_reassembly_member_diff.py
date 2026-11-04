"""Locked tests for audit_reassembly_diff.py's V2 member diff vs a frozen punct-position file
(DESIGN_q2_build.md §2, §9.52; run mode approved §9.82). Synthetic temp sqlite + temp files only.

Run:  python tests/test_reassembly_member_diff.py
"""
import io
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "audit_reassembly_diff.py"
sys.path.insert(0, str(ROOT / "scripts"))
import audit_reassembly_diff as A                     # noqa: E402

CLEAN = ("And", "God", "made"), "And God made"
PUNCT = ("And", "Lot", "up,", "went"), "And Lot, up went"
PUNCT_OPS = "replace: rows[Lot up,] -> text[Lot, up]"
ORDER = ("the", "spirit", "holy,"), "the holy spirit,"
CONTENT = ("And", "foo"), "And bar"
DUP = ("of", "the", "the", "forces"), "of the forces"


class MemberDiff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)

    def db(self, verses):
        """verses: {(book, ch, vs): (english_rows, text)}"""
        p = self.d / "built.db"
        if p.exists():
            p.unlink()
        con = sqlite3.connect(p)
        con.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT)")
        con.execute("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT, "
                    "bracket_id INT, greek_pos INT)")
        for vid, ((b, c, v), (rows, text)) in enumerate(verses.items(), 1):
            con.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (vid, b, c, v, text))
            for i, e in enumerate(rows):
                con.execute("INSERT INTO words (verse_id, position, english) VALUES (?,?,?)", (vid, i, e))
        con.commit()
        con.close()
        return p

    def frozen(self, members):
        p = self.d / "punct.txt"
        p.write_text("".join(f"     [{'punct-position':<13}] {r:<12} {o}\n" for r, o in members), encoding="utf-8")
        return p

    def eligible(self, rows):
        p = self.d / "eligible.tsv"
        p.write_text("book\tchapter\tverse\teligible\treason\n"
                     + "".join(f"{b}\t{c}\t{v}\t{e}\t{'' if e else 'swap'}\n" for (b, c, v), e in rows.items()),
                     encoding="utf-8")
        return p

    def run_mode(self, db, frozen, elig):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.run_member_diff_v2(str(db), str(frozen), str(elig))
        return rc, buf.getvalue()

    def test_frozen_file_line_format_round_trips(self):
        real = ROOT / "tests" / "fixtures" / "reassembly" / "punct_members_live_20261030.txt"
        m = A.load_punct_members(real)
        self.assertEqual(len(m), 241)
        self.assertEqual(m["Gen 2:19"], "delete: rows[—] -> text[] ; insert: rows[] -> text[—]")

    def test_unchanged_member_and_clean_verse_pass(self):
        db = self.db({("Gen", 1, 1): PUNCT, ("Gen", 1, 2): CLEAN})
        rc, out = self.run_mode(db, self.frozen([("Gen 1:1", PUNCT_OPS)]),
                                self.eligible({("Gen", 1, 1): 1, ("Gen", 1, 2): 1}))
        self.assertEqual(rc, 0)
        self.assertIn("V2 MEMBER DIFF: NO FAIL - word-order 0 - content-other 0 - dup-gloss 0 - "
                      "Joh 14:26 clean - new on non-eligible 0 | to ruling: gone 0 - new on eligible 0 - "
                      "changed ops 0 - unchanged 1", out)

    def test_gone_new_eligible_changed_ops_are_listed_not_failed(self):
        db = self.db({("Gen", 1, 1): PUNCT, ("Gen", 1, 2): PUNCT, ("Gen", 1, 3): CLEAN})
        frozen = self.frozen([("Gen 1:1", "replace: rows[x] -> text[x,]"), ("Gen 1:3", PUNCT_OPS)])
        rc, out = self.run_mode(db, frozen, self.eligible({("Gen", 1, 1): 1, ("Gen", 1, 2): 1, ("Gen", 1, 3): 1}))
        self.assertEqual(rc, 0)
        self.assertIn("[gone         ] Gen 1:3", out)
        self.assertIn("[new-eligible ] Gen 1:2", out)
        self.assertIn("[changed-ops  ] Gen 1:1", out)
        self.assertIn("to ruling: gone 1 - new on eligible 1 - changed ops 1 - unchanged 0", out)

    def test_new_member_on_non_eligible_or_unlisted_verse_fails(self):
        db = self.db({("Gen", 1, 1): PUNCT, ("Gen", 1, 2): PUNCT})
        rc, out = self.run_mode(db, self.frozen([("Gen 9:9", PUNCT_OPS)]),
                                self.eligible({("Gen", 1, 1): 0}))       # 1:1 ineligible, 1:2 not listed
        self.assertEqual(rc, 1)
        self.assertIn("[new-NOT-elig ] Gen 1:1", out)
        self.assertIn("[new-NOT-elig ] Gen 1:2", out)
        self.assertIn("V2 MEMBER DIFF: FAIL", out)

    def test_each_hard_class_fails(self):
        for case, klass in ((ORDER, "word-order"), (CONTENT, "content-other"), (DUP, "dup-gloss")):
            with self.subTest(klass=klass):
                db = self.db({("Gen", 1, 1): case})
                rc, out = self.run_mode(db, self.frozen([("Gen 9:9", PUNCT_OPS)]),
                                        self.eligible({("Gen", 1, 1): 1}))
                self.assertEqual(rc, 1)
                self.assertIn(f"[{klass:<13}] Gen 1:1", out)
                self.assertIn("V2 MEMBER DIFF: FAIL", out)

    def test_declared_row_hit_fails_and_is_named(self):
        db = self.db({("Joh", 14, 26): ORDER})
        rc, out = self.run_mode(db, self.frozen([("Gen 9:9", PUNCT_OPS)]), self.eligible({("Joh", 14, 26): 1}))
        self.assertEqual(rc, 1)
        self.assertIn("Joh 14:26 (charter 4.10 declared row): HIT word-order", out)

    def test_malformed_frozen_file_refused(self):
        bad = self.d / "bad.txt"
        for text, msg in (("     [word-order   ] Gen 1:1      x\n", "not a punct-position"),
                          ("garbage\n", "not a punct-position"),
                          (f"     [punct-position] Gen 1:1      a\n     [punct-position] Gen 1:1      b\n", "twice"),
                          ("", "no members")):
            with self.subTest(msg=msg):
                bad.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, msg):
                    A.load_punct_members(bad)

    def test_cli_member_mode_and_argument_checks(self):
        db = self.db({("Gen", 1, 1): PUNCT})
        frozen, elig = self.frozen([("Gen 1:1", PUNCT_OPS)]), self.eligible({("Gen", 1, 1): 1})
        for argv in ([str(db), "--v2", "--punct-members", str(frozen), "--eligible", str(elig)],
                     ["--v2", "--punct-members", str(frozen), "--eligible", str(elig), str(db)]):
            r = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("V2 MEMBER DIFF: NO FAIL", r.stdout)
        for argv in ([str(db), "--punct-members", str(frozen), "--eligible", str(elig)],        # no --v2
                     ["--v2", "--punct-members", str(frozen), "--eligible", str(elig)],         # no db
                     [str(db), "--v2", "--punct-members", str(frozen)]):                        # no eligible
            r = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 2, argv)
        r = subprocess.run([sys.executable, str(SCRIPT), str(self.d / "nope.db"), "--v2", "--punct-members",
                            str(frozen), "--eligible", str(elig)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)
        self.assertIn("V2 MEMBER DIFF: STOP", r.stdout)

    def test_default_v2_report_unchanged(self):
        """The plain --v2 report keeps its exact output (pinned on this synthetic db)."""
        db = self.db({("Gen", 1, 1): PUNCT, ("Gen", 1, 2): CLEAN})
        buf = io.StringIO()
        with redirect_stdout(buf):
            n = A.run_report_v2(str(db), list_all=True)
        self.assertEqual(n, 1)
        self.assertEqual(buf.getvalue(), (
            f"== reassembly-diff V2 (order-aware) on {db} (READ-ONLY) ==\n"
            "   verses scanned : 2\n"
            "   total hits     : 1\n\n"
            "   by class:\n"
            "     dup-gloss            0\n"
            "     content-other        0\n"
            "     word-order           0\n"
            "     punct-position       1\n\n"
            "   by book (all, canonical-ish by count):\n"
            "     Gen         1\n\n"
            "   every hit:\n"
            f"     [punct-position] Gen 1:1      {PUNCT_OPS}\n"))


if __name__ == "__main__":
    unittest.main()
