"""The split double rows copy-proof tools (scripts/split_doubles_proof_20261126.py, DESIGN 9.281): save copies
abp_surface row for row into a new file and never writes its source; compare counts same / only new / only old
/ differs inside and outside the plan's verses and lists every slot that is not the same; both refuse a file
named bible.db and an existing output. Throwaway databases only.

Run:  python tests/test_split_doubles_proof.py
"""
import contextlib
import csv
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
import apply_split_doubles_20261126 as A               # noqa: E402
import split_doubles_proof_20261126 as P               # noqa: E402

PLAN = A.load_plan()


class Proof(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.copy = self.d / "proof.db"
        c = sqlite3.connect(self.copy)
        c.executescript("""CREATE TABLE verses (id INTEGER PRIMARY KEY, book, chapter INT, verse INT, text);
            CREATE TABLE words (verse_id INT, position INT, english, strongs);
            CREATE TABLE abp_surface (verse_id INTEGER, position INTEGER, form TEXT, translit TEXT,
                                      PRIMARY KEY (verse_id, position));""")
        for key3 in sorted({w["key3"] for w in PLAN}):
            c.execute("INSERT INTO verses (book, chapter, verse) VALUES (?,?,?)", key3)
        self.out_vid = c.execute("INSERT INTO verses (book, chapter, verse) VALUES ('Gen', 1, 1)").lastrowid
        self.in_vid = 1
        for vid in (self.in_vid, self.out_vid):
            for pos in range(4):
                c.execute("INSERT INTO words VALUES (?,?,?,?)", (vid, pos, f"w{pos}", "2532"))
                c.execute("INSERT INTO abp_surface VALUES (?,?,?,?)", (vid, pos, f"f{pos}", f"t{pos}"))
        c.commit()
        c.close()

    def run_tool(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = P.main([str(a) for a in argv])
        return rc, out.getvalue()

    def sha(self, p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    def test_save_copies_the_table_and_leaves_the_source_alone(self):
        before = self.sha(self.copy)
        rc, out = self.run_tool("save", self.copy, self.d / "saved.db")
        self.assertEqual(rc, 0, out)
        self.assertIn("saved abp_surface: 8 rows", out)
        self.assertEqual(self.sha(self.copy), before)
        a = sqlite3.connect(self.copy).execute("SELECT * FROM abp_surface ORDER BY 1, 2").fetchall()
        b = sqlite3.connect(self.d / "saved.db").execute("SELECT * FROM abp_surface ORDER BY 1, 2").fetchall()
        self.assertEqual(a, b)

    def test_compare_counts_inside_and_outside_and_lists_each_difference(self):
        self.assertEqual(self.run_tool("save", self.copy, self.d / "old.db")[0], 0)
        c = sqlite3.connect(self.copy)
        c.execute("DELETE FROM abp_surface WHERE verse_id=? AND position=0", (self.in_vid,))        # only old, inside
        c.execute("UPDATE abp_surface SET form='x' WHERE verse_id=? AND position=1", (self.in_vid,))  # differs, inside
        c.execute("INSERT INTO abp_surface VALUES (?, 9, 'n', 'n')", (self.out_vid,))               # only new, outside
        c.commit()
        c.close()
        self.assertEqual(self.run_tool("save", self.copy, self.d / "new.db")[0], 0)
        before = self.sha(self.copy)
        rc, out = self.run_tool("compare", self.d / "new.db", self.d / "old.db", "--verses", self.copy,
                                "--out", self.d / "list.tsv")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.sha(self.copy), before)
        self.assertIn("inside  the plan's verses: same 2 / only new 0 / only old 1 / differs 1", out)
        self.assertIn("outside the plan's verses: same 4 / only new 1 / only old 0 / differs 0", out)
        with open(self.d / "list.tsv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        self.assertEqual(sorted((r["where"], r["kind"], r["position"]) for r in rows),
                         [("inside", "differs", "1"), ("inside", "only old", "0"), ("outside", "only new", "9")])

    def test_restore_sets_the_pins_for_one_run_and_puts_them_back(self):
        import restore_surface_fill as rs
        before = {k: getattr(rs, k) for k in P.RESTORE_PINS}
        seen = {}

        def fake_main(argv):
            seen.update({k: getattr(rs, k) for k in P.RESTORE_PINS}, argv=argv)
            return 0
        sha = "ab" * 32
        with mock.patch.object(rs, "main", fake_main):
            rc, out = self.run_tool("restore", "--sha", sha, "--counts", "3952,3412,539,1", "--base", "391142",
                                    "--", "copy.db", "--snapshot", "new.tsv", "--apply")
        self.assertEqual(rc, 0, out)
        self.assertEqual((seen["SNAPSHOT_SHA256"], seen["N_ROWS"], seen["N_INSERT"], seen["N_UPDATE"],
                          seen["N_REMOVE"], seen["ROWS_BASE"]), (sha, 3952, 3412, 539, 1, 391142))
        self.assertEqual(seen["argv"], ["copy.db", "--snapshot", "new.tsv", "--apply"])
        self.assertEqual({k: getattr(rs, k) for k in P.RESTORE_PINS}, before)
        self.assertIn("PROOF RESTORE RESULT: DONE", out)

    def test_restore_refuses_bad_counts_a_bad_sha_and_a_base_inside(self):
        import restore_surface_fill as rs
        with mock.patch.object(rs, "main", lambda argv: self.fail("restore must not run")):
            for args in (("--sha", "ab" * 32, "--counts", "3952,3412,539,2", "--base", "1", "--", "c.db"),
                         ("--sha", "xyz", "--counts", "3,1,1,1", "--base", "1", "--", "c.db"),
                         ("--sha", "ab" * 32, "--counts", "3,1,1,1", "--base", "1", "--", "c.db", "--base", "2")):
                rc, out = self.run_tool("restore", *args)
                self.assertEqual(rc, 1, out)
                self.assertIn("RESULT: STOP", out)

    def test_refuses_bible_db_and_an_existing_output(self):
        live_named = self.d / "bible.db"
        live_named.write_bytes(self.copy.read_bytes())
        rc, out = self.run_tool("save", live_named, self.d / "x.db")
        self.assertEqual(rc, 1)
        self.assertIn("named bible.db", out)
        (self.d / "exists.db").write_bytes(b"")
        rc, out = self.run_tool("save", self.copy, self.d / "exists.db")
        self.assertEqual(rc, 1)
        self.assertIn("already exists", out)
        self.assertEqual(os.path.getsize(self.d / "exists.db"), 0)


if __name__ == "__main__":
    unittest.main()
