#!/usr/bin/env python3
"""Regression fixtures for the word-study lookup's Exact / contains bands.

Locks the min-length gate on the CONTAINS band (views_lexicon.lexicon_lookup):
a query under 3 FOLDED letters (γῆ -> "γη" -> 2) skips the substring scan entirely,
so a 2-letter fragment can't drag in dozens of letter-accidents (Πέργη, ἀγωγή under
γῆ). A 3+-letter query (λόγος) keeps the substring scan, so real family compounds
that carry the root at the TAIL (ἄλογος, φιλόλογος) still surface — a prefix match
would have wrongly dropped those.

Drives the REAL endpoint through a Flask test client over a tiny temp bible.db, so
the match logic under test is the shipped SQL, not a re-implementation (a second
copy of the scan could pass while the real one regresses).

Run:  python tests/test_lexicon_lookup_bands.py
Needs flask (CI installs it for the other endpoint tests).
"""
import os
import sqlite3
import sys
import tempfile
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _norm(s):
    # Mirror core._norm_lemma / add_lemma_plain: strip marks, lower, fold hyphen + final sigma.
    nfd = unicodedata.normalize("NFD", s)
    stripped = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return stripped.lower().replace("-", "").replace("ς", "σ")


def _build_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE lexicon (strongs TEXT PRIMARY KEY, lemma TEXT, translit TEXT,
                              kjv_def TEXT, derivation TEXT, strongs_def TEXT,
                              strongs_g TEXT, lemma_plain TEXT);
        CREATE TABLE bdb (strongs_id TEXT PRIMARY KEY, lemma TEXT, xlit TEXT,
                          description TEXT, lemma_plain TEXT);
        CREATE TABLE dotted_lexicon (strongs TEXT PRIMARY KEY, lemma TEXT, translit TEXT);
        CREATE TABLE word_gloss (strongs TEXT PRIMARY KEY, gloss TEXT);
        -- present-but-empty; the >1-row enrichment path queries these unguarded.
        CREATE TABLE words (id INTEGER PRIMARY KEY, strongs TEXT, strongs_base TEXT, english_head TEXT);
        CREATE TABLE kjv_words (word_id INTEGER PRIMARY KEY, word TEXT, italic INTEGER);
        CREATE TABLE kjv_strongs (id INTEGER PRIMARY KEY, word_id INTEGER, strongs_id TEXT);
    """)
    # Greek lexicon rows. lemma_plain built with the same fold the data step uses.
    lex = [
        # (strongs, lemma, translit)  -- the target and its letter-accidents / real family
        ("1093", "γῆ", "gē"),            # G1093 the target
        ("4011", "Πέργη", "Pergē"),      # accident: contains "γη" (a city name)
        ("72",   "ἀγωγή", "agōgē"),      # accident: contains "γη"
        ("3056", "λόγος", "logos"),      # λόγος target (3+ letters)
        ("249",  "ἄλογος", "alogos"),    # real family, root at TAIL -> contains "λογος"
        ("5386", "φιλόλογος", "philologos"),  # real family, root at TAIL
    ]
    for st, lemma, tr in lex:
        c.execute(
            "INSERT INTO lexicon (strongs, lemma, translit, strongs_g, lemma_plain)"
            " VALUES (?,?,?,?,?)", (st, lemma, tr, "G" + st, _norm(lemma)))
    # A dotted different-word: γηγενής must be findable by its OWN search (contains band,
    # 6 folded letters) but must NOT be dragged in under the 2-letter γῆ query.
    c.execute("INSERT INTO dotted_lexicon (strongs, lemma, translit) VALUES (?,?,?)",
              ("G1093.1", "γηγενής", "gēgenēs"))
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


def _nums(resp_json, match=None):
    return {r["strongs"] for r in resp_json if match is None or r.get("match") == match}


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

    def get(q):
        return cl.get("/api/lexicon/lookup", query_string={"q": q}).get_json()

    # 1) γῆ -> G1093 exact-first (the part that already worked; lock it).
    r = get("γῆ")
    check("γῆ returns G1093 in the exact band", "G1093" in _nums(r, "exact"))

    # 2) γῆ's contains band is junk-free / empty — the 2-letter gate skips the scan.
    #    Πέργη + ἀγωγή (letter-accidents) must NOT appear; γηγενής must NOT be dragged in.
    cont = _nums(r, "contains")
    check("γῆ contains band empty (no Πέργη/ἀγωγή/γηγενής)",
          cont == set())
    check("γῆ result has no G4011/G72/G1093.1 anywhere", not (
          {"G4011", "G72", "G1093.1"} & _nums(r)))

    # 3) Length gate runs on the FOLDED query, not raw codepoints: feed γ + η + a combining
    #    circumflex (3 raw codepoints, folds to "γη" = 2). Still gated -> contains empty.
    raw = "γῆ"  # γ, η, COMBINING GREEK PERISPOMENI
    check("test input really is 3 raw codepoints", len(raw) == 3)
    r2 = get(raw)
    check("accented-raw γῆ still hits G1093 exact", "G1093" in _nums(r2, "exact"))
    check("accented-raw γῆ still gated (contains empty)", _nums(r2, "contains") == set())

    # 4) Diacritic-free γη (2 letters) still reaches G1093 — normalizer works both ways —
    #    and stays gated.
    r3 = get("γη")
    check("unaccented γη hits G1093 exact", "G1093" in _nums(r3, "exact"))
    check("unaccented γη contains band empty", _nums(r3, "contains") == set())

    # 5) γηγενής findable by its OWN search (6-letter query runs the scan).
    r4 = get("γηγενής")
    check("γηγενής found by its own search", "G1093.1" in _nums(r4))

    # 6) λόγος (3+ letters) keeps the scan: real tail-root family survives. The gate must
    #    NOT silently empty a normal-length lemma's contains band.
    r5 = get("λόγος")
    lc = _nums(r5, "contains")
    check("λόγος contains band populates", len(lc) > 0)
    check("λόγος contains includes the real family (ἄλογος)", "G249" in lc)

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILED")
        return 1
    print("\nAll lexicon-lookup band fixtures hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
