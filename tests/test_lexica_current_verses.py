"""Dictionary cards quote TODAY's verse text (ruling chat 11/22). lexica_def stores a copy of each
cited verse from build time; the serve route replaces it by ref, so an edition change cannot leave a
card quoting the old English. Own throwaway db; never touches bible.db.

Run:  python tests/test_lexica_current_verses.py
"""
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from flask import Flask

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                 # noqa: E402
import views_lexica as VL   # noqa: E402

ENTRY = {
    "strongs": "G25", "lemma": "agapao", "translit": "agapao",
    "senses_block": "**1. to love** (Joh 3:16).",
    "verses": [
        {"ref": "Joh 3:16", "text": "OLD EDITION wording of this verse."},
        {"ref": "1Co 13:4", "text": "OLD EDITION wording of the second verse."},
        {"ref": "Rev 99:1", "text": "A verse the text does not carry."},
    ],
    "raw": "the stored prose blob",
}


class CurrentVerses(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = os.path.join(self.tmp.name, "t.db").replace(os.sep, "/")
        c = sqlite3.connect(self.db)
        c.executescript("""
            CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
            CREATE TABLE lexica_def (strongs TEXT, def_json TEXT);
            INSERT INTO verses (book, chapter, verse, text) VALUES
                ('Joh', 3, 16, 'TODAY wording of this verse.'),
                ('1Co', 13, 4, 'TODAY wording of the second verse.');
        """)
        c.execute("INSERT INTO lexica_def VALUES ('G25', ?)", (json.dumps(ENTRY),))
        c.commit()
        c.close()
        self.patch = mock.patch.object(core, "DB", self.db)
        self.patch.start()
        app = Flask(__name__)
        app.register_blueprint(VL.bp)
        self.client = app.test_client()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def card(self):
        r = self.client.get("/api/lexica/G25")
        self.assertEqual(r.status_code, 200)
        return json.loads(r.get_data(as_text=True))

    def test_card_quotes_todays_text(self):
        v = {x["ref"]: x["text"] for x in self.card()["verses"]}
        self.assertEqual(v["Joh 3:16"], "TODAY wording of this verse.")
        self.assertEqual(v["1Co 13:4"], "TODAY wording of the second verse.")

    def test_ref_with_no_verse_is_left_out(self):
        self.assertEqual([x["ref"] for x in self.card()["verses"]], ["Joh 3:16", "1Co 13:4"])

    def test_rest_of_the_card_unchanged(self):
        d = self.card()
        self.assertEqual(d["senses_block"], ENTRY["senses_block"])
        self.assertEqual(d["lemma"], "agapao")
        self.assertNotIn("raw", d)

    def test_stored_row_is_not_written(self):
        self.card()
        c = sqlite3.connect(self.db)
        stored = json.loads(c.execute("SELECT def_json FROM lexica_def").fetchone()[0])
        c.close()
        self.assertEqual(stored, ENTRY)

    def test_control_the_check_fires_without_the_fix(self):
        with mock.patch.object(VL, "_current_verses", lambda conn, sid, stored: stored):
            with self.assertRaises(AssertionError):
                self.test_card_quotes_todays_text()


if __name__ == "__main__":
    unittest.main()
