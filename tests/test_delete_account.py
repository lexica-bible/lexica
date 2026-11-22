"""Locked test: POST /api/auth/delete-account removes EVERY row the account owns in notes.db -
notes, plan, saved Ask-the-corpus conversations, its daily AI-usage counters, reset links,
tokens, the user row - and nothing that belongs to anyone else (another account's rows, the
whole-site usage total user_id 0). Temp notes.db; no live data.

Run:  python tests/test_delete_account.py
"""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from flask import Flask        # noqa: E402
import core                    # noqa: E402
import views_notes as N        # noqa: E402

OWNED = {"notes": "code", "plan": "code", "corpus": "code"}      # keyed by "u<id>"
BY_UID = {"ai_usage": "user_id", "password_resets": "user_id", "tokens": "user_id", "users": "id"}


class DeleteAccount(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.db = str(Path(t.name) / "notes.db")

        def opener():
            c = sqlite3.connect(self.db)
            c.row_factory = sqlite3.Row
            return c
        p = mock.patch.object(N, "notes_db", opener)
        p.start()
        self.addCleanup(p.stop)
        N._ensure_tables()
        c = opener()
        for uid in (1, 2):
            o = f"u{uid}"
            c.execute("INSERT INTO users (id, email, pass_hash, created) VALUES (?,?,?,?)",
                      (uid, f"a{uid}@x", "h", "t"))
            c.execute("INSERT INTO tokens (token, user_id, created) VALUES (?,?,?)", (f"tok{uid}", uid, "t"))
            c.execute("INSERT INTO notes (code, id, json, updated, deleted) VALUES (?,?,?,?,0)", (o, "n1", "{}", "t"))
            c.execute("INSERT INTO plan (code, json, updated) VALUES (?,?,?)", (o, "{}", "t"))
            c.execute("INSERT INTO corpus (code, id, json, updated, deleted) VALUES (?,?,?,?,0)", (o, "c1", "{}", "t"))
            c.execute("INSERT INTO ai_usage (user_id, day, n) VALUES (?,?,3)", (uid, "2026-11-21"))
            c.execute("INSERT INTO password_resets (token, user_id, created, expires) VALUES (?,?,?,9e9)",
                      (f"r{uid}", uid, "t"))
        c.execute("INSERT INTO ai_usage (user_id, day, n) VALUES (0, '2026-11-21', 9)")   # the site total
        c.commit()
        c.close()
        app = Flask(__name__)
        app.config["RATELIMIT_ENABLED"] = False
        core.limiter.init_app(app)
        app.register_blueprint(N.bp)
        self.client = app.test_client()

    def count(self, table, col, val):
        c = sqlite3.connect(self.db)
        try:
            return c.execute(f"SELECT count(*) FROM {table} WHERE {col} = ?", (val,)).fetchone()[0]
        finally:
            c.close()

    def test_every_owned_row_goes_and_nothing_else(self):
        r = self.client.post("/api/auth/delete-account", headers={"Authorization": "Bearer tok1"})
        self.assertEqual((r.status_code, r.get_json()), (200, {"ok": True}))
        for t, col in OWNED.items():
            self.assertEqual(self.count(t, col, "u1"), 0, t)
            self.assertEqual(self.count(t, col, "u2"), 1, t)
        for t, col in BY_UID.items():
            self.assertEqual(self.count(t, col, 1), 0, t)
            self.assertEqual(self.count(t, col, 2), 1, t)
        self.assertEqual(self.count("ai_usage", "user_id", 0), 1)

    def test_no_token_deletes_nothing(self):
        r = self.client.post("/api/auth/delete-account")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.count("corpus", "code", "u1"), 1)
        self.assertEqual(self.count("users", "id", 1), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
