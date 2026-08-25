"""Locked tests for gate_greek_header.py's AMENDED gate-B classes
(HANDOFF_gateB_enumeration.md ruling, 2026-08-24).

Discipline (feedback_audit_tools_must_fail): every new class must FIRE on a
known-good member and REFUSE a synthetic bad row — a class that can only pass
proves nothing. Runs the REAL gate script on two tiny synthetic files (no
bible.db needed); asserts the gate-B classification lines, not the exit code
(gate C legitimately fails on synthetic data, and the numeric landing pins
legitimately mismatch a six-row fixture — both are expected here).

Run:  python tests/test_gate_greek_header.py
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "gate_greek_header.py")

SCHEMA = """
CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
CREATE TABLE words(verse_id INT, position INT, english TEXT, english_head TEXT,
                   is_pn INT);
CREATE TABLE pn_binding(book, chapter, verse, name, entity_uniq, kind, rule,
                        render, hot, tier);
CREATE TABLE tipnr_entities(uniq, head, section, gender, area, descr, summary,
                            bases, parents, offspring);
CREATE TABLE abp_surface(verse_id INT, position INT, form TEXT, translit TEXT);
CREATE TABLE pn_greek_identity(verse_id INT, position INT, greek_strongs TEXT,
                               greek_lemma TEXT, source TEXT);
"""

VERSES = [(1, "Gen", 1, 1), (2, "Gen", 1, 2), (3, "Gen", 1, 3),
          (4, "Gen", 1, 4), (5, "Est", 1, 21), (6, "Mat", 9, 35)]
WORDS = [(1, 1, "David", "", 1), (2, 1, "Samuel", "", 1),
         (3, 1, "the Ethiopians", "", 1), (4, 1, "Tyre", "", 1),
         (5, 16, "Memucan.", "", 1), (6, 3, "Jesus", "", 1)]
NBSP = "\xa0"
LIVE_IDENT = [
    (1, 1, "G1000", f"ην{NBSP}Δαυίδ", "tipnr"),    # glued -> blank: CURE class
    (2, 1, "G2000", "Σαμουήλ", "tipnr"),           # clean -> blank: VIOLATION
    (3, 1, None, "Αιθίοπες", "lemma-only"),        # people-word drop: door fires
    (4, 1, None, "Τύρος", "lemma-only"),           # place-name drop: door REFUSES
    (5, 16, None, "Μεμουχά", "lemma-only"),        # pinned member, pinned outcome
    (6, 3, "G2424", "Ισηούς", "abp-tag"),          # pinned member, DEVIATES
]
SCR_IDENT = [
    (1, 1, "G1000", None, "tipnr"),
    (2, 1, "G2000", None, "tipnr"),
    (3, 1, None, None, "none"),
    (4, 1, None, None, "none"),
    (5, 16, None, "Μεμουχάν", "surface"),          # the pinned improved outcome
    (6, 3, "G2424", "Ιησούς", "surface"),          # pin expects blank -> deviation
]


def build_db(path, ident):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO verses VALUES (?,?,?,?)", VERSES)
    conn.executemany("INSERT INTO words VALUES (?,?,?,?,?)", WORDS)
    conn.executemany("INSERT INTO pn_greek_identity VALUES (?,?,?,?,?)", ident)
    conn.commit()
    conn.close()


class TestGateBAmendedClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.live = os.path.join(cls.tmp, "live.db")
        cls.scr = os.path.join(cls.tmp, "scr.db")
        build_db(cls.live, LIVE_IDENT)
        build_db(cls.scr, SCR_IDENT)
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        cls.out = subprocess.run(
            [sys.executable, GATE, cls.live, cls.scr],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
            env=env).stdout
        # Control run: live against itself must pass gate B entirely (the
        # numeric landing pins stay un-armed when nothing changed).
        cls.ctrl = subprocess.run(
            [sys.executable, GATE, cls.live, cls.live],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
            env=env).stdout

    def problems(self):
        return [l for l in self.out.splitlines() if "problem:" in l]

    def test_glued_cure_fires_and_is_not_a_violation(self):
        self.assertIn("glued cure (blanked) 1", self.out)
        self.assertFalse(any("Δαυίδ" in l for l in self.problems()),
                         "the glued cure row was flagged as a violation")

    def test_clean_blanking_is_refused(self):
        self.assertTrue(any("Σαμουήλ" in l and "outside the ruled classes" in l
                            for l in self.problems()),
                        "a clean value dying must stay a violation")

    def test_gentilic_door_fires_on_people_word(self):
        self.assertIn("gentilic drop 1", self.out)
        self.assertFalse(any("Αιθίοπες" in l for l in self.problems()))

    def test_gentilic_door_refuses_place_name(self):
        self.assertTrue(any("not a people-word" in l and "'Tyre'" in l
                            for l in self.problems()),
                        "the re-keyed door must refuse a non-people-word")

    def test_pinned_member_fires_on_its_exact_outcome(self):
        self.assertIn("pinned ruled loss 1", self.out)
        self.assertFalse(any("Μεμουχ" in l for l in self.problems()))

    def test_pinned_member_deviation_is_refused(self):
        self.assertTrue(any("PINNED member" in l and "Mat" in l
                            for l in self.problems()),
                        "a pinned member off its pinned outcome must violate")

    def test_numeric_pins_arm_on_a_transition_run(self):
        self.assertTrue(any("'PIN'" in l for l in self.problems()),
                        "landing-count pins must arm when rows changed")

    def test_control_run_passes_gate_b(self):
        self.assertIn("gate B: PASS", self.ctrl,
                      "live-vs-live control must pass gate B (pins un-armed)")


if __name__ == "__main__":
    unittest.main()
