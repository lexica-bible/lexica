"""The two read-only checks from DESIGN 9.257: English typed in the Greek font, and one Greek word on
two rows with both pieces inside a bracket. Own throwaway db; never touches bible.db.

Run:  python tests/test_split_and_font_checks.py
"""
import csv
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import audit_abp_app_vs_surface as A    # noqa: E402
import audit_split_rendering as S       # noqa: E402


class Font(unittest.TestCase):
    def test_fires_on_english_in_the_greek_font(self):
        for g in ("δαγγερ και", "δαγγερδαγγερ εν", "- Φορ τηε ενδ.λἡμμα", "τω βψ.", "- βεσιδεσ με.προ",
                  ".  ιCП Γρ ητοι.είτε", "- χομμανδερ-ιν-χηιεφ.άρχων", "ζωογονούντων τηε λιvινγ."):
            self.assertTrue(A.english_font(g), g)

    def test_quiet_on_real_greek(self):
        for g in ("και", "το", "εν", "συν", "μεν", "Δαν", "Ουρ", "ιν", "μαν", "πνεύμα", "ου  ποιἡσετε", "", None):
            self.assertFalse(A.english_font(g), g)


def row(pos, eng, st="1325", gpos=1, bid=1, form="δώσι"):
    return (pos, eng, st, gpos, bid, form)


class Pairs(unittest.TestCase):
    def test_one_word_on_two_rows(self):
        self.assertEqual(S.pairs_in_verse([row(4, "they should"), row(5, "give her")]), [(0, 1, "same-form")])

    def test_second_piece_just_after_the_bracket(self):             # Deu 4:10 on live, 11/23
        self.assertEqual(S.pairs_in_verse([row(25, "let"), row(26, "hear", gpos=None, bid=None)]), [(0, 1, "same-form")])

    def test_a_missing_form_is_named(self):
        self.assertEqual(S.pairs_in_verse([row(4, "let"), row(5, "hear", form="")]), [(0, 1, "form-missing")])

    def test_not_a_pair(self):
        for rows in ([row(4, "holy"), row(5, "holy")],                  # a word said twice
                     [row(4, "a", form="άγιος"), row(5, "b", form="αγία")],   # two different forms
                     [row(4, "a"), row(6, "b")],                        # not neighbours
                     [row(4, "a"), row(5, "b", st="1326")],             # two numbers
                     [row(4, "a", gpos=None, bid=None), row(5, "b")],   # the helper audit's shape (second opens a bracket)
                     [row(4, "a", st="*"), row(5, "b", st="*")]):       # name slots
            self.assertEqual(S.pairs_in_verse(rows), [], rows)


class WholeRun(unittest.TestCase):
    def run_it(self, with_controls):
        d = tempfile.mkdtemp()
        db = os.path.join(d, "t.db")
        c = sqlite3.connect(db)
        c.executescript("""CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
            CREATE TABLE words (verse_id INT, position INT, english TEXT, strongs TEXT, greek_pos INT, bracket_id INT);
            CREATE TABLE abp_surface (verse_id INT, position INT, form TEXT, translit TEXT);""")
        with open(S.FROZEN, encoding="utf-8", newline="") as f:
            frozen = {f"{x['book']} {x['chapter']}:{x['verse']}": x["strongs"] for x in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
                      if x["shape"] == "both-inside-bracket"}
        refs = [(r, frozen[r]) for r in S.CONTROLS] if with_controls else [("Gen 1:1", "1325")]
        for vid, (r, num) in enumerate(refs, 1):
            b, ch, v = r.replace(":", " ").split()
            c.execute("INSERT INTO verses VALUES (?,?,?,?,'x')", (vid, b, int(ch), int(v)))
            for pos, eng in ((1, "they should"), (2, "give her")):
                c.execute("INSERT INTO words VALUES (?,?,?,?,1,1)", (vid, pos, eng, num))
                c.execute("INSERT INTO abp_surface VALUES (?,?,'δώσι','')", (vid, pos))
        c.commit()
        c.close()
        before = open(db, "rb").read()
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_split_rendering.py"), "--db", db, "--out", os.path.join(d, "o")],
                           capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(before, open(db, "rb").read(), "the check must not change the database")
        return r

    def test_controls_pass(self):
        r = self.run_it(True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SPLIT AUDIT CONTROLS: PASS", r.stdout)

    def test_a_missing_control_fails_the_run(self):
        r = self.run_it(False)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("FAILED", r.stdout)


if __name__ == "__main__":
    unittest.main()
