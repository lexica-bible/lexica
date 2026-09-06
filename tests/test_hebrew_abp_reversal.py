#!/usr/bin/env python3
"""Locked test — no ABP results for a Hebrew number (JP ruling 2026-09-06,
docs/tickets/CHARTER_hebrew_abp_reversal.md).

Drives the REAL profile/verses routes (Flask test client) on the ws-flips fixture,
where H90 (Agag) carries two ABP words rows on its strongs_base — the exact shape
that used to open the ABP tab for a Hebrew number. POSITIVE FIRST: the fixture is
shown to still hold those rows, so a grey tab is a refusal, not an absence.

  * H90 profile: has_abp False, served corpus never 'abp' (even when asked)
  * H90 verses (All books + one book) with corpus=abp: empty
  * Greek numbers unchanged: G4815 opens; G9826 (tipnr identity, flips ON) opens
  * the reader card's Hebrew cross-ref carries NO ABP count (hebrew_count None)

Run:  python tests/test_hebrew_abp_reversal.py
"""
import json
import os
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    import core
    import views_lexicon
    from views_metav import _greek_identity_payload
    from test_ws_greek_flips import _make_db
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(views_lexicon.bp)
    client = app.test_client()
    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "heb_reversal.db")
    _make_db(dbp)

    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    old_db, old_flag = core.DB, core.READER_GREEK_FLIPS
    try:
        core.DB = dbp
        core.READER_GREEK_FLIPS = True
        raw = sqlite3.connect(dbp)
        check("POSITIVE: fixture holds ABP words rows under H90 (the shape that used to open the tab)",
              raw.execute("SELECT count(*) FROM words WHERE strongs_base = 'H90'").fetchone()[0], 2)
        raw.close()

        p = json.loads(client.get("/api/lexicon/profile/H90").get_data(as_text=True))
        check("H90 profile: ABP tab grey", p.get("has_abp"), False)
        check("H90 profile: served corpus is not ABP", p.get("corpus") != "abp", True)
        p2 = json.loads(client.get("/api/lexicon/profile/H90?corpus=abp").get_data(as_text=True))
        check("H90 profile asked for ABP: still not ABP", p2.get("corpus") != "abp", True)
        check("H90 profile asked for ABP: tab still grey", p2.get("has_abp"), False)

        v = json.loads(client.get("/api/lexicon/verses/H90/all?corpus=abp").get_data(as_text=True))
        check("H90 All-books list under ABP: empty", v.get("verses"), [])
        v = json.loads(client.get("/api/lexicon/verses/H90/1Sa?corpus=abp").get_data(as_text=True))
        check("H90 one-book list under ABP: empty", v.get("verses"), [])

        g = json.loads(client.get("/api/lexicon/profile/G4815").get_data(as_text=True))
        check("Greek word unchanged: ABP tab open", g.get("has_abp"), True)
        g = json.loads(client.get("/api/lexicon/profile/G9826").get_data(as_text=True))
        check("Greek identity number unchanged: ABP tab open", g.get("has_abp"), True)

        conn = sqlite3.connect(dbp)
        conn.row_factory = sqlite3.Row
        pay = _greek_identity_payload(conn, 1, 3)
        check("reader card cross-ref keeps the Hebrew number", pay["hebrew_base"], "H90")
        check("reader card cross-ref carries NO ABP count", pay["hebrew_count"], None)
        conn.close()
    finally:
        core.DB, core.READER_GREEK_FLIPS = old_db, old_flag

    if fails:
        print("\n".join(fails))
        return 1
    print("\nAll Hebrew-ABP reversal checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
