"""The word card's short meaning from its own renders-as counts (JP's ruling, DESIGN 9.253).
Rows below are the live cards' real lists, read 11/23. Own throwaway db; never touches bible.db.

Run:  python tests/test_short_meaning.py
"""
import json
import os
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from flask import Flask

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                     # noqa: E402
import short_meaning as M       # noqa: E402
import views_lexicon as VL      # noqa: E402

G4151 = [("spirit", 565), ("wind", 43), ("spirits", 37), ("breath", 29), ("winds", 2)]
H7307 = [("spirit", 218), ("wind", 104), ("breath", 38), ("winds", 8), ("side", 5), ("spirits", 3), ("sides", 2)]
H5315 = [("life", 228), ("self", 225), ("person", 81), ("appetite", 31), ("soul", 26), ("selves", 19), ("lives", 15), ("desire", 15)]


class Rule(unittest.TestCase):
    def test_jps_two_examples(self):
        self.assertEqual(M.from_counts(G4151), "spirit, wind, breath")
        self.assertEqual(M.from_counts(H7307), "spirit, wind, breath")

    def test_forms_of_one_word_count_as_one(self):
        self.assertEqual(M.from_counts(H5315), "self, life, person")     # 244 vs 243 after folding
        self.assertEqual(M.from_counts([("saying", 1485), ("says", 1122), ("say", 400), ("said", 162), ("speak", 57)]), "say")
        self.assertEqual(M.from_counts([("do", 889), ("did", 618), ("made", 473), ("make", 326), ("doing", 136)]), "do, make")
        self.assertEqual(M.from_counts([("loved", 143), ("love", 104), ("loving", 65), ("loves", 30)]), "love")
        self.assertEqual(M.from_counts([("die", 100), ("died", 80), ("dying", 20)]), "die")
        self.assertEqual(M.fold_renderings([("seed", 5), ("see", 4)]), [("seed", 5), ("see", 4)])

    def test_a_form_folds_only_into_a_base_in_its_own_list(self):
        self.assertEqual(M.from_counts([("blessed", 92), ("happy", 1)]), "blessed")
        self.assertEqual(M.from_counts([("anointed", 39)]), "anointed")
        self.assertEqual(M.from_counts([("offering", 120), ("sin", 104), ("sins", 69)]), "sin, offering")

    def test_rare_renderings_are_cut(self):
        self.assertEqual(M.from_counts([("gentleness", 4), ("dejectedly", 1), ("mutterer", 1)]), "gentleness")
        self.assertEqual(M.from_counts([("steps", 28), ("ascents", 15), ("going", 2), ("thoughts", 1)]), "steps, ascents")
        self.assertEqual(M.from_counts([("wait", 4), ("hope", 2), ("x", 1)]), "wait, hope")

    def test_filler(self):
        self.assertEqual(M.from_counts([("just", 157), ("one", 124), ("ones", 87), ("thing", 5)]), "just")
        self.assertEqual(M.from_counts([("holiness", 191), ("place", 100), ("thing", 67)]), "holiness")
        self.assertEqual(M.from_counts([("one", 300), ("certain", 20)]), "one, certain")
        self.assertEqual(M.from_counts([("place", 90), ("room", 5)]), "place, room")

    def test_nothing_counted(self):
        self.assertEqual(M.from_counts([]), "")

    def test_no_wrong_merges(self):
        fold = lambda *w: [g for g, _c in M.fold_renderings([(x, 10 - i) for i, x in enumerate(w)])]
        self.assertEqual(fold("news", "new"), ["news", "new"])
        self.assertEqual(fold("offering", "offer"), ["offering", "offer"])
        self.assertEqual(fold("evening", "even"), ["evening", "even"])
        self.assertEqual(fold("clothing", "cloth"), ["clothing", "cloth"])
        self.assertEqual(fold("clothed", "cloth"), ["clothed", "cloth"])
        self.assertEqual(fold("clothed", "clothe"), ["clothe"])
        self.assertEqual(fold("lives", "live"), ["live"])
        self.assertEqual(fold("lives", "life"), ["life"])

    def test_each_kept_word_says_why(self):
        self.assertTrue(all(isinstance(v, str) and v for v in M.COUNTS_MISLEAD.values()))
        self.assertNotIn("G4151", M.COUNTS_MISLEAD, "JP's own example reads from the counts")

    def test_the_headers_read_one_by_one_are_kept_by_name(self):
        """DESIGN 9.255: a phrase's leftover word never heads a card."""
        for n in ("G1831", "G4863", "G2521", "H408", "H6440", "H2009"):
            self.assertIn(n, M.COUNTS_MISLEAD)
        for n in ("H7307", "H5315", "G4160", "G165", "G4716", "G3086"):     # read, and left on the counts
            self.assertNotIn(n, M.COUNTS_MISLEAD)
        # These pages pool different Greek words: a stored meaning would put "Dorcas" on a spear.
        for n in ("G1393", "G1393.1", "G1303", "G1303.1", "G1315"):
            self.assertNotIn(n, M.COUNTS_MISLEAD)

    def test_every_hand_override_is_decided(self):
        """A new override in build_word_gloss.py must be placed here too, never dropped silently."""
        src = (ROOT / "scripts" / "build_word_gloss.py").read_text(encoding="utf-8")
        found = set()
        for name in ("OVERRIDES", "HEBREW_OVERRIDES", "DOTTED_OVERRIDES"):
            a = src.index("\n" + name + " = {")
            found |= set(re.findall(r'"([GH]\d+(?:\.\d+)?)":\s*"', src[a:src.index("\n}\n", a)]))
        on_counts = {"G4151", "H3293", "H3651", "H5492", "H2530", "H328", "H1430", "H4609", "H1984", "H2556", "H1933"}
        function_word = {"H853"}
        self.assertEqual(len(found), 60)
        self.assertEqual(found - set(M.COUNTS_MISLEAD) - on_counts - function_word, set())
        self.assertEqual(on_counts & set(M.COUNTS_MISLEAD), set())


class Routes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = os.path.join(self.tmp.name, "t.db").replace(os.sep, "/")
        c = sqlite3.connect(self.db)
        c.executescript("""
            CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
            CREATE TABLE words (verse_id INT, position INT, english TEXT, english_head TEXT, strongs TEXT, strongs_base TEXT);
            CREATE TABLE word_gloss (strongs TEXT, gloss TEXT, source TEXT);
            CREATE TABLE tipnr (strongs TEXT, entity_type TEXT);
            CREATE TABLE kjv_words (word_id INT, word TEXT);
            CREATE TABLE kjv_strongs (word_id INT, strongs_id TEXT);
            CREATE TABLE lexicon (strongs TEXT, lemma TEXT);
            CREATE TABLE dotted_lexicon (strongs TEXT, lemma TEXT, translit TEXT);
            INSERT INTO verses VALUES (1, 'Gen', 1, 1, 'x');
            INSERT INTO word_gloss VALUES ('G5484', 'favor, kindness, goodwill', 'override'),
                                          ('G4151', 'spirit, breath, wind', 'override'),
                                          ('G4004.4', 'fifty years old', 'override'),
                                          ('H853', 'marks the direct object', 'override');
            INSERT INTO tipnr VALUES ('G1138', 'person');
            INSERT INTO lexicon VALUES ('4151', 'a'), ('5484', 'b'), ('1138', 'c'), ('3756', 'd'), ('7777', 'e'), ('4004', 'f'),
                                       ('2419', 'Ἱερουσαλήμ'), ('2486', 'Ἰχνεύω');
            INSERT INTO dotted_lexicon VALUES ('G7777.1', 'other', ''), ('G4004.4', 'fifty', '');
        """)
        i = 0
        for sb, st, rows in (("G4151", "4151", G4151), ("G5484", "5484", [("favor", 230)]), ("G1138", "1138", [("david", 50)]),
                             ("G3756", "3756", [("not", 9)]), ("G7777", "7777.1", [("the", 1)]), ("G4004", "4004.4", [("old", 3)]),
                             ("G2419", "2419", [("Jerusalem", 5)]), ("G2486", "2486", [("prowling", 3)])):
            for g, n in rows:
                for _ in range(n):
                    i += 1
                    c.execute("INSERT INTO words VALUES (1, ?, ?, ?, ?, ?)", (i, g, g, st, sb))
        for sid, rows in (("H7307", H7307), ("G7777", [("wrongword", 40)]), ("H5113", [("Nod", 3)])):
            for g, n in rows:
                for _ in range(n):
                    i += 1
                    c.execute("INSERT INTO kjv_words VALUES (?, ?)", (i, g))
                    c.execute("INSERT INTO kjv_strongs VALUES (?, ?)", (i, sid))
        c.commit()
        c.close()
        for p in (mock.patch.object(core, "DB", self.db), mock.patch.object(VL, "_heb_ready", lambda: False),
                  mock.patch.object(VL, "_bsb_ready", lambda conn: False), mock.patch.dict(VL._MEANING_CACHE, clear=True),
                  mock.patch.object(VL, "_FUNCTION_STRONGS", {"3756"})):   # filled at app startup, not on import
            p.start()
            self.addCleanup(p.stop)
        app = Flask(__name__)
        app.register_blueprint(VL.bp)
        self.client = app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def get(self, s):
        return json.loads(self.client.get(f"/api/lexicon/short-meaning/{s}").get_data(as_text=True))

    def test_override_is_replaced_by_counts_for_pneuma(self):
        self.assertEqual(self.get("G4151"), {"short_meaning": "spirit, wind, breath"})

    def test_a_word_whose_counts_mislead_keeps_its_gloss(self):
        self.assertEqual(self.get("G5484"), {"reviewed_gloss": "favor, kindness, goodwill"})

    def test_a_name_and_a_function_word_are_left_alone(self):
        self.assertEqual(self.get("G1138"), {})
        self.assertEqual(self.get("G3756"), {})

    def test_hebrew_with_no_hebrew_list_reads_the_kjv_list(self):
        self.assertEqual(self.get("H7307"), {"short_meaning": "spirit, wind, breath"})

    def test_bad_number(self):
        self.assertEqual(self.get("xyz"), {})
        self.assertEqual(self.get("G4151a"), {})

    def test_hebrew_byform_reads_its_base(self):
        self.assertEqual(self.get("H7307a"), {"short_meaning": "spirit, wind, breath"})

    def test_dotted_word_never_borrows_its_base_numbers_list(self):
        self.assertEqual(self.get("G7777.1"), {})

    def test_dotted_override_keeps_its_gloss(self):
        self.assertEqual(self.get("G4004.4"), {"reviewed_gloss": "fifty years old"})

    def test_a_name_keeps_its_capital(self):
        with mock.patch.object(core, "_HEB_NAME_STRONGS", {"5113"}):
            self.assertEqual(self.get("H5113"), {"short_meaning": "Nod"})
        self.assertEqual(self.get("G2419"), {"short_meaning": "Jerusalem"})

    def test_a_capital_only_comes_back_on_a_name_and_from_the_text(self):
        VL._MEANING_CACHE.clear()
        self.assertEqual(self.get("H5113"), {"short_meaning": "nod"})       # not on the name list
        self.assertEqual(self.get("G2486"), {"short_meaning": "prowling"})  # capital headword, lower-case text

    def test_the_source_editors_note_is_stripped(self):
        s = "the same as נוֹדlemma נוֹדּ extra dagesh, corrected to נוֹד; vagrancy; Nod, the land of Cain; Nod."
        self.assertEqual(core.clean_heb_definition(s), "the same as נוֹד; vagrancy; Nod, the land of Cain; Nod.")
        for keep in ("a lemma of the root; to go", "corrected, to go straight", "", None):
            self.assertEqual(core.clean_heb_definition(keep), (keep or ""))

    def test_charis_kjv_number_reads_the_gloss_on_its_abp_number(self):
        self.assertEqual(self.get("G5485"), {"reviewed_gloss": "favor, kindness, goodwill"})

    def test_kept_number_with_no_stored_meaning_shows_no_header(self):
        with mock.patch.dict(M.COUNTS_MISLEAD, {"G4151.7": "the counts are the base number's mixed list"}):
            self.assertEqual(self.get("G4151.7"), {})

    def test_function_word_beats_the_kept_list(self):
        with mock.patch.object(VL, "_HEB_FUNCTION_STRONGS", frozenset({"853"})):
            self.assertEqual(self.get("H853"), {})

    def test_step_only_and_bridged_numbers_are_names(self):
        with mock.patch.object(VL, "_step_lexicon_row", lambda conn, s: {"lemma": "x"} if s == "9826" else None):
            self.assertEqual(self.get("G9826"), {})
        with mock.patch.object(VL, "_bridge_if_grey", lambda *a: "Γαλιλαία"):
            self.assertEqual(self.get("G4151.9"), {})

    def test_an_empty_answer_is_never_cached(self):
        self.get("G1138")
        self.assertNotIn("G1138", VL._MEANING_CACHE)
        self.get("G4151")
        self.assertIn("G4151", VL._MEANING_CACHE)


if __name__ == "__main__":
    unittest.main()
