#!/usr/bin/env python3
"""Regression fixture for the phrase-boundary gloss-misalignment class.

ABP parks a whole multi-word phrase gloss on ONE token slot ("Jesus to them," sits on
the αὐτός/G846 pronoun). The word-study "renders as" list used to COUNT raw words.english
and run it through _normalize_gloss, whose both-ends function-word trim deleted the true
pronoun ("them") and surfaced the parked proper noun -> a phantom "jesus" render under a
pronoun. Fix: every render COUNT reads the token's own head (english_head), while the
displayed chip keeps the full ABP english. See parse_abp.HEAD_WORD_TAIL_CAVEAT.

This drives the REAL /api/lexicon/verses endpoint over a tiny temp bible.db, so the split
under test is the shipped SQL/logic, not a re-implementation:
  * the render counts (`glosses`) come from english_head  -> no "jesus" phantom;
  * the verse chip (`verses[].words[].w`) still shows the full "Jesus to them,";
  * the ?gloss= filter keys off the head, not the parked phrase.

Run:  python tests/test_render_head_no_phantom.py
Needs flask (CI installs it for the other endpoint tests).
"""
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _build_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INTEGER,
                             verse INTEGER, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INTEGER, position INTEGER,
                            english TEXT, english_head TEXT, strongs TEXT,
                            strongs_base TEXT, italic INTEGER);
    """)
    # One Matthew verse. Two G846 slots: the phrase-parked pronoun (english carries the
    # whole "Jesus to them," but english_head is the token's OWN word "them"), and a clean
    # single-word pronoun ("him", head blank like real single-word rows). Plus a non-target
    # word so the highlight flag is exercised.
    c.execute("INSERT INTO verses VALUES (1,'Mat',1,1,'Jesus said to them, and saw him.')")
    rows = [
        # id verse pos english             english_head strongs sbase   italic
        (1,  1,   0,  "Jesus to them,",    "them",      "846",  "G846", 0),
        (2,  1,   1,  "said",              None,        "3004", "G3004", 0),
        (3,  1,   2,  "him",               None,        "846",  "G846", 0),
    ]
    c.executemany("INSERT INTO words VALUES (?,?,?,?,?,?,?,?)", rows)
    c.commit()
    c.close()


def _client(db_path):
    import core
    core.DB = db_path  # db_ro() reads this at call time -> temp db, read-only
    from flask import Flask
    from views_lexicon import bp
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app.test_client()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    tmp = tempfile.mkdtemp()
    db_path = os.path.join(tmp, "bible.db")
    _build_db(db_path)
    cl = _client(db_path)
    fails = []

    def check(desc, cond):
        if cond:
            print(f"  ok: {desc}")
        else:
            fails.append(f"  FAIL: {desc}")

    def verses(**qs):
        return cl.get("/api/lexicon/verses/G846/Mat",
                      query_string={"corpus": "abp", **qs}).get_json()

    r = verses()
    renders = {g["gloss"] for g in r.get("glosses", [])}

    # 1) The class itself: no parked proper noun leaks into the render counts.
    check("G846 renders contain no 'jesus' phantom", "jesus" not in renders)
    check("G846 renders carry the real pronouns (them, him)",
          "them" in renders and "him" in renders)

    # 2) Display is untouched — the chip still shows the FULL ABP english.
    chips = [w["w"] for v in r.get("verses", []) for w in v.get("words", [])]
    check("verse chip still shows the full 'Jesus to them,'", "Jesus to them," in chips)

    # 3) The ?gloss= filter keys off the head, not the parked phrase.
    check("?gloss=them selects the verse (head match)",
          len(verses(gloss="them").get("verses", [])) == 1)
    check("?gloss=jesus selects nothing (phrase never becomes a render)",
          len(verses(gloss="jesus").get("verses", [])) == 0)

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILED")
        return 1
    print("\nAll render-head fixtures hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
