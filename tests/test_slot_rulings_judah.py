"""Locked test for the DESIGN §9.100 DEFECT x3 slot rulings (2Ki 8:16 p10, 8:25 p12, 8:29 p31 ->
Jehoram@1Ki.22.50-Mat, king of Judah). The new edition prints "Joram" for both kings in these
verses; the single verse-level pn_binding row 'joram' -> Joram@2Ki.1.17-2Ch paints every 'joram'
cell, so the three Judah cells need slot rulings (the served card reads pn_slot_binding first).

Runs the REAL scripts/build_slot_binding.land() and scripts/check_wordpos_prereg.py on a tiny
synthetic copy of the three verses as built prints them (verse text verbatim from
g2sit_20261107.log), with the ruling rows taken from the committed scripts/pn_slot_rulings.tsv:
  1. the TSV holds exactly the three rows as ruled (name, slot, entity, kind, flag)
  2. all 7 2Ki 8 joram rows land (0 refused); each Judah slot prints an OVERRIDE
     Joram@2Ki.1.17-2Ch -> Jehoram@1Ki.22.50-Mat; the table holds the right entity per slot
  3. the prereg checker passes the three new rows (R1-R5, incl. the R4 quote gate)
  4. control (the checker can fire): the Judah entity proposed at the Israel slot p4 as well is
     REFUSED by R5 duplicate - a wrong-slot twin must not pass silently

Run:  python tests/test_slot_rulings_judah.py
"""
import contextlib
import io
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_slot_binding as bsb

JUDAH, ISRAEL = "Jehoram@1Ki.22.50-Mat", "Joram@2Ki.1.17-2Ch"
TEXT = {
    16: "In the fifth year of Joram son of Ahab king of Israel, Joram son of Jehoshaphat king of Judah reigned.",
    25: "In the twelfth year of Joram son of Ahab king of Israel Ahaziah son of Joram king of Judah reigned.",
    29: ("And king Joram returned to be treated medically in Jezreel from the wounds of which the Syrians "
         "struck him in Ramoth Gilead, during his waging war against Hazael king of Syria. And Ahaziah, son "
         "of Joram king of Judah went down to see Joram son of Ahab in Jezreel, because he was infirm."),
}
# name cells as built prints them (g2sit_20261107.log: position, english, english_head)
NAMES = {16: [(4, "Joram"), (10, "Joram")], 25: [(4, "Joram"), (12, "of Joram")],
         29: [(4, "Joram"), (31, "of Joram"), (38, "Joram")]}
NEW = {(16, 10), (25, 12), (29, 31)}


def ruling_rows():
    out = [r for r in bsb.read_tsv() if r["book"] == "2Ki" and r["chapter"] == "8" and r["name"] == "joram"]
    return out


def make_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
CREATE TABLE words(verse_id INT, position INT, english TEXT, english_head TEXT, bracket_id INT);
CREATE TABLE tipnr_entities(uniq TEXT PRIMARY KEY, section TEXT);
CREATE TABLE pn_binding(book INT, chapter INT, verse INT, name TEXT, entity_uniq TEXT, kind TEXT,
                        rule TEXT, render INT, hot INT, tier INT);
""")
    for i, vs in enumerate((16, 25, 29), 1):
        c.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (i, "2Ki", 8, vs, TEXT[vs]))
        for pos, eng in NAMES[vs]:
            c.execute("INSERT INTO words VALUES (?,?,?,?,NULL)", (i, pos, eng, "joram"))
        c.execute("INSERT INTO pn_binding VALUES (12,8,?,'joram',?,'exact','',1,0,1)", (vs, ISRAEL))
    c.executemany("INSERT INTO tipnr_entities VALUES (?,?)", [(JUDAH, "person"), (ISRAEL, "person")])
    c.commit()
    c.close()


def write_tsv(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(bsb.COLS) + "\n")
        for r in rows:
            fh.write("\t".join(r[c] for c in bsb.COLS) + "\n")


class TestJudahSlotRulings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.db = os.path.join(cls.tmp, "built.db")
        make_db(cls.db)
        cls.rows = ruling_rows()

    def test_tsv_holds_the_three_ruled_rows(self):
        new = [r for r in self.rows if (int(r["verse"]), int(r["position"])) in NEW]
        self.assertEqual(len(new), 3)
        for r in new:
            self.assertEqual((r["entity_uniq"], r["referent_kind"], r["evidence_class"], r["flags"]),
                             (JUDAH, "person", "kin-in-verse", "paint-override"))
            self.assertIn("Joram", r["evidence_quote"])
            self.assertIn("king of Judah", r["evidence_quote"])
        self.assertEqual(len(self.rows), 7)
        self.assertEqual(len(bsb.read_tsv()), 105)

    def test_all_seven_land_with_the_right_entity_per_slot(self):
        tsv = os.path.join(self.tmp, "seven.tsv")
        write_tsv(tsv, self.rows)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            landed, refused = bsb.land(self.db, apply=True, tsv=tsv)
        out = buf.getvalue()
        self.assertEqual((landed, refused), (7, 0), out)
        for vs, pos in sorted(NEW):
            self.assertIn("OVERRIDE 2Ki 8:%d p%d joram: verse-grain paint %s -> slot %s" % (vs, pos, ISRAEL, JUDAH), out)
        c = sqlite3.connect(self.db)
        got = {(v, p): e for v, p, e in c.execute("SELECT verse, position, entity_uniq FROM pn_slot_binding")}
        c.close()
        for vs, names in NAMES.items():
            for pos, _e in names:
                self.assertEqual(got[(vs, pos)], JUDAH if (vs, pos) in NEW else ISRAEL, (vs, pos))

    def test_prereg_checker_passes_the_three_new_rows(self):
        tsv = os.path.join(self.tmp, "three.tsv")
        write_tsv(tsv, [r for r in self.rows if (int(r["verse"]), int(r["position"])) in NEW])
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_wordpos_prereg.py"), self.db, tsv],
                           capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ALL PASS", r.stdout)
        self.assertEqual(r.stdout.count(": PASS (ok)"), 3, r.stdout)

    def test_control_judah_entity_twice_in_a_verse_is_refused(self):
        bad = [dict(r) for r in self.rows if (int(r["verse"]), int(r["position"])) == (16, 10)]
        twin = dict(bad[0], position="4", evidence_quote="Joram son of Ahab king of Israel")
        tsv = os.path.join(self.tmp, "twin.tsv")
        write_tsv(tsv, bad + [twin])
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_wordpos_prereg.py"), self.db, tsv],
                           capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("R5 DUPLICATE", r.stdout)


if __name__ == "__main__":
    unittest.main()
