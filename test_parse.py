#!/usr/bin/env python3
"""Quick smoke test for parse_abp.py covering all ABP token variants."""

import sqlite3, sys, tempfile, os
sys.path.insert(0, os.path.dirname(__file__))
from parse_abp import parse_words, parse_text, build_database

SAMPLE = """
(Gen 1:1)  InG1722 the beginningG746 God madeG4160 G3588 G2316 G3588 G3772 G2532 G3588 G1093
(Gen 1:2)  G3588 G1093 G1161 G2258 G517 G2532 G172 G2532 G4655 G1883 G3588 G12 G2532 G4151 G2316 G2018 G1883 G3588 G5204
(Gen 2:8)  G2532 G5452 G2962 G3588 G2316 G3857 G1722 G2275 G2596 G395 G2532 G5087 G1563 G3588 G444 G3739 G4111
(Gen 2:8)  [2gardenG3857 1the] EdenG* G2532
(Gen 2:9)  [2dayG2250 1 the third].G5154 G2532 G3588 G1093 G1544 G985 G5528
(Gen 3:1)  wasG1510.7.3 G1161 G3588 G3789 G5429 G3956 G3588 G2342
(Gen 49:3)  ReubenG* G4416Reuben G4413 G1473 G2479 G1473 G746
"""

def check(condition, msg):
    if not condition:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"ok   {msg}")

# --- parse_words unit tests ---
words = parse_words("InG1722 the beginningG746 God madeG4160 G3588 G2316")
check(words[0] == (0, "In", "1722"),              "first word: english='In', strongs='1722'")
check(words[1] == (1, "the beginning", "746"),    "multi-word english gloss")
check(words[2] == (2, "God made", "4160"),        "multi-word english gloss 2")
check(words[3] == (3, None, "3588"),              "bare G-number -> english=None")
check(words[4] == (4, None, "2316"),              "bare G-number 2 -> english=None")

# proper noun G*
words2 = parse_words("EdenG* G2532")
check(words2[0][2] == "*",                        "proper noun stored as '*'")

# dotted ABP extension
words3 = parse_words("[2dayG2250 1 the third].G5154")
check(words3[1][2] == "5154",                     "dotted extension G5154 captured")

# --- full pipeline test ---
parsed = parse_text(SAMPLE)
check(len(parsed) >= 5,                           f"parsed at least 5 verse blocks (got {len(parsed)})")

with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
    db = f.name

try:
    build_database(db, parsed)
    conn = sqlite3.connect(db)
    n_verses = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
    n_words  = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    null_eng = conn.execute("SELECT COUNT(*) FROM words WHERE english IS NULL").fetchone()[0]
    star_st  = conn.execute("SELECT COUNT(*) FROM words WHERE strongs='*'").fetchone()[0]
    dot_st   = conn.execute("SELECT COUNT(*) FROM words WHERE strongs LIKE '%.%'").fetchone()[0]
    base     = conn.execute(
        "SELECT strongs, strongs_base FROM words WHERE strongs LIKE '%.%' LIMIT 1"
    ).fetchone()
    conn.close()

    check(n_verses >= 5,       f"DB has >=5 verses (got {n_verses})")
    check(n_words  > 0,        f"DB has word rows (got {n_words})")
    check(null_eng > 0,        f"NULL english rows exist (bare G-numbers) -- got {null_eng}")
    check(star_st  > 0,        f"strongs='*' rows exist (proper nouns) -- got {star_st}")
    check(dot_st   > 0,        f"dotted strongs rows exist -- got {dot_st}")
    check(base is not None,                "dotted strongs row found")
    check(base[1] == base[0].split(".")[0], f"strongs_base '{base[1]}' == base of '{base[0]}'")
finally:
    os.unlink(db)

print("\nAll tests passed.")
