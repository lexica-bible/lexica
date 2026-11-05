"""tests for scripts/eu_repair_restore_digits.py (DESIGN §9.88) — the built-copy repair of the
restored rows' bracket digits. Synthetic copies only; nothing here touches a real db."""
import contextlib
import hashlib
import io
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import eu_repair_restore_digits as R  # noqa: E402
from build_words_from_abp import MERGE_PAIR_HEADER, EDGE_SPLIT_HEADER  # noqa: E402

# (position, english, greek_pos, bracket_id, strongs, strongs_base)
LEV = [(0, "your field", 2, 1, "68", "G68"), (1, "You shall not", 1, 1, "3756", "G3756"),
       (2, "sow", None, None, "4687", "G4687"), (3, "and", None, None, "2532", "G2532")]
COR = [(0, "assemblies", 1, 1, "1577", "G1577"), (1, "of", None, None, "3588", "G3588"),
       (2, "Asia!", 3, 1, "*", "*")]
OTHER = [(0, "In", None, None, "1722", "G1722"), (1, "beginning", 1, 2, "746", "G746")]
TEXT = {("Lev", 25, 4): "You shall not sow your field and",
        ("1Co", 16, 19): "assemblies of Asia!",
        ("Gen", 1, 1): "In beginning"}


def _db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT)")
    con.execute("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT, "
                "greek_pos INT, bracket_id INT, strongs TEXT, strongs_base TEXT)")
    for vid, (key, rows) in enumerate(((("Lev", 25, 4), LEV), (("1Co", 16, 19), COR), (("Gen", 1, 1), OTHER)), 1):
        con.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (vid,) + key + (TEXT[key],))
        con.executemany("INSERT INTO words (verse_id, position, english, greek_pos, bracket_id, strongs, strongs_base) "
                        "VALUES (?,?,?,?,?,?,?)", [(vid,) + r for r in rows])
    con.commit()
    con.close()


def _tsv(path, header, rows):
    path.write_text("\t".join(header) + "\n" + "".join("\t".join(map(str, r)) + "\n" for r in rows),
                    encoding="utf-8", newline="\n")
    Path(str(path) + ".sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n",
                                           encoding="utf-8")


class Repair(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.copy = self.d / "built.db"
        _db(self.copy)
        mp, es = self.d / "mp.tsv", self.d / "es.tsv"
        _tsv(mp, MERGE_PAIR_HEADER, [("Lev", 25, 4, 2, 1, "4687", "3756", "sow", "You shall not", "You shall not sow")])
        _tsv(es, EDGE_SPLIT_HEADER, [("1Co", 16, 19, 1, 2, "3588", "*", "of", "of Asia!", "of", "Asia!")])
        self._saved = (R.MERGE_PAIRS, R.EDGE_SPLITS, R.LIVE_DB)
        R.MERGE_PAIRS, R.EDGE_SPLITS, R.LIVE_DB = mp, es, self.d / "live.db"
        self.plan = self.d / "plan.tsv"

    def tearDown(self):
        R.MERGE_PAIRS, R.EDGE_SPLITS, R.LIVE_DB = self._saved
        shutil.rmtree(self.d, ignore_errors=True)

    def _run(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = R.main([str(a) for a in args])
        return code, buf.getvalue()

    def _digits(self):
        con = sqlite3.connect(self.copy)
        try:
            return {(b, p): (gp, bid) for b, p, gp, bid in con.execute(
                "SELECT v.book, w.position, w.greek_pos, w.bracket_id FROM words w JOIN verses v ON w.verse_id = v.id")}
        finally:
            con.close()

    def test_dry_run_plans_the_rule_and_writes_nothing(self):
        before = self.copy.read_bytes()
        code, out = self._run("--dry-run", self.copy, "--out", self.plan)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.copy.read_bytes(), before)
        self.assertIn("RESTORE-DIGITS PLAN: 4 cells / 2 verses - restored 2 - shifted 2", out)
        lines = self.plan.read_text(encoding="utf-8").splitlines()[1:]
        got = {(l.split("\t")[0], l.split("\t")[3], l.split("\t")[7], l.split("\t")[10], l.split("\t")[11]) for l in lines}
        self.assertEqual(got, {("Lev", "2", "restored", "2", "1"), ("Lev", "0", "shifted", "3", "1"),
                               ("1Co", "1", "restored", "3", "1"), ("1Co", "2", "shifted", "4", "1")})

    def test_strongs_drift_stops(self):
        _tsv(R.MERGE_PAIRS, MERGE_PAIR_HEADER, [("Lev", 25, 4, 2, 1, "9999", "3756", "sow", "x", "x")])
        code, out = self._run("--dry-run", self.copy, "--out", self.plan)
        self.assertEqual(code, 1)
        self.assertIn("Strong's base at positions 2/1", out)

    def test_live_path_refused_everywhere(self):
        shutil.copy(self.copy, R.LIVE_DB)
        for args in (("--dry-run", R.LIVE_DB, "--out", self.plan), ("--verify", R.LIVE_DB, "--plan", self.plan),
                     ("--apply", R.LIVE_DB, "--rollback", self.copy, "--plan", self.plan)):
            code, out = self._run(*args)
            self.assertEqual(code, 1)
            self.assertIn("refusing the LIVE db", out)

    def test_apply_needs_identical_rollback_and_same_plan(self):
        self._run("--dry-run", self.copy, "--out", self.plan)
        code, out = self._run("--apply", self.copy, "--rollback", self.d / "missing.db", "--plan", self.plan)
        self.assertIn("rollback db not found", out)
        rb = self.d / "rb.db"
        shutil.copy(self.copy, rb)
        con = sqlite3.connect(rb); con.execute("UPDATE words SET english = 'x' WHERE id = 1"); con.commit(); con.close()
        code, out = self._run("--apply", self.copy, "--rollback", rb, "--plan", self.plan)
        self.assertIn("not byte-identical", out)
        shutil.copy(self.copy, rb)
        self.plan.write_text(self.plan.read_text(encoding="utf-8") + "extra\n", encoding="utf-8", newline="\n")
        code, out = self._run("--apply", self.copy, "--rollback", rb, "--plan", self.plan)
        self.assertEqual(code, 1)
        self.assertIn("differs from", out)
        self.assertEqual(self.copy.read_bytes(), rb.read_bytes())

    def test_apply_writes_exactly_the_plan_then_verify_is_clean(self):
        self._run("--dry-run", self.copy, "--out", self.plan)
        rb = self.d / "rb.db"
        shutil.copy(self.copy, rb)
        code, out = self._run("--apply", self.copy, "--rollback", rb, "--plan", self.plan)
        self.assertEqual(code, 0, out)
        self.assertIn("RESTORE-DIGITS APPLY: APPLIED 4 cells - before-match 4/4 - after-match 4/4", out)
        self.assertIn("(unchanged)", out)
        d = self._digits()
        self.assertEqual(d[("Lev", 2)], (2, 1))
        self.assertEqual(d[("Lev", 0)], (3, 1))
        self.assertEqual(d[("1Co", 1)], (3, 1))
        self.assertEqual(d[("1Co", 2)], (4, 1))
        self.assertEqual(d[("Gen", 1)], (1, 2))          # not listed: untouched
        code, out = self._run("--verify", self.copy, "--plan", self.plan, "--residue", "Gen 1:1")
        self.assertEqual(code, 0, out)
        self.assertIn("RESTORE-DIGITS VERIFY: plan verses 2 - clean 2 - word-order on listed verses 0", out)
        self.assertIn("=== Gen 1:1", out)
        code, out = self._run("--dry-run", self.copy, "--out", self.d / "again.tsv")
        self.assertIn("RESTORE-DIGITS PLAN: 0 cells", out)  # a second pass changes nothing

    def test_verify_names_a_word_order_hit_before_the_repair(self):
        self._run("--dry-run", self.copy, "--out", self.plan)
        code, out = self._run("--verify", self.copy, "--plan", self.plan)
        self.assertIn("word-order on listed verses", out)
        self.assertNotIn("word-order on listed verses 0", out)


if __name__ == "__main__":
    unittest.main()
