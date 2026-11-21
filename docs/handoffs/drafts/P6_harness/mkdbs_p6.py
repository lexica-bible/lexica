# P4 tests: make the made-up src / built / live copies. No real db is read.
# usage: python3 mkdbs_p4.py <bible-db dir> [plant]
# plant: none | livewords (live words cell differs from src) | books (live differs from src in books)
#        | extra (a table on live only) | sb (built has one strongs_base cell more than declared) | nosumv (built lacks lsj.summary_v)
import os
import sqlite3
import sys

sys.dont_write_bytecode = True
BD = sys.argv[1]
PLANT = sys.argv[2] if len(sys.argv) > 2 else "none"
WORDS = ("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT, english_head TEXT,"
         " strongs TEXT, strongs_base TEXT, greek_pos INTEGER, bracket_id INTEGER, italic INTEGER, italic_words TEXT,"
         " smcap_words TEXT, is_pn INTEGER, morph TEXT, lemma TEXT, english_head_norm TEXT)")


def base(c, sumv=True):
    c.executescript(WORDS + ";"
                    "CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);"
                    "CREATE TABLE ai_search_cache (query TEXT PRIMARY KEY, result_json TEXT NOT NULL, ver_key TEXT NOT NULL, created_at REAL NOT NULL);"
                    "CREATE INDEX idx_ai_cache_ver ON ai_search_cache(ver_key);"
                    "CREATE TABLE lsj (key TEXT PRIMARY KEY, plain TEXT, translit TEXT, def_html TEXT, summary_json TEXT"
                    + (", summary_v INTEGER DEFAULT 0" if sumv else "") + ");"
                    "CREATE TABLE abp_ext (strongs TEXT PRIMARY KEY, def_html TEXT, summary_json TEXT, abp_summary_v INTEGER);"
                    "CREATE TABLE books (id INTEGER PRIMARY KEY, name TEXT, sort_order INTEGER);"
                    "CREATE TABLE lexicon (strongs TEXT, kjv_def TEXT, strongs_g TEXT);"
                    "CREATE INDEX idx_lexicon_strongs_g ON lexicon(strongs_g);"
                    "CREATE TABLE tipnr (id INTEGER PRIMARY KEY, name TEXT, entity_types TEXT);"
                    "CREATE TABLE pn_hebrew_xref (verse_id INTEGER NOT NULL, position INTEGER NOT NULL, hebrew_base TEXT, class TEXT NOT NULL, PRIMARY KEY (verse_id, position));"
                    "CREATE TABLE pn_greek_identity (verse_id INTEGER NOT NULL, position INTEGER NOT NULL, greek_strongs TEXT, greek_lemma TEXT, source TEXT NOT NULL, hebrew_base TEXT, PRIMARY KEY (verse_id, position));"
                    "CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, verse_id INT, position INT, active INT);")
    for v in range(1, 6):
        c.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (v, "Gen", 1, v, "verse text %d" % v))
    rid = 0
    for v in range(1, 6):
        for p in range(0, 6):
            rid += 1
            pn = 1 if p == 2 else 0
            sb = "H%d" % (100 + v) if pn else "G%d" % (1000 + 10 * v + p)
            c.execute("INSERT INTO words VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (rid, v, p, "w%d_%d" % (v, p), "w%d" % p, sb.lstrip("GH") if not pn else "*", sb, None, None, 0, None,
                       None, pn, None, None, "w%d" % p))
        c.execute("INSERT INTO pn_hebrew_xref VALUES (?,?,?,?)", (v, 2, "H%d" % (100 + v), "none" if v < 4 else "tipnr"))
        c.execute("INSERT INTO pn_greek_identity VALUES (?,?,?,?,?,?)", (v, 2, None, None, "lemma-only" if v < 3 else "tipnr", "H%d" % (100 + v)))
    for i in range(4):
        c.execute("INSERT INTO ai_search_cache VALUES (?,?,?,?)", ("q%d" % i, "SECRET-AI-TEXT-%d" % i, ("search:abc" if i < 2 else "summary:x:y"), 1.0))
    c.execute("INSERT INTO lsj VALUES ('k1','p','t','SECRET-DEF',NULL" + (",1" if sumv else "") + ")")
    c.execute("INSERT INTO abp_ext VALUES ('G1','SECRET-DEF',NULL,1)")
    c.execute("INSERT INTO books VALUES (1,'Genesis',1)")
    c.execute("INSERT INTO lexicon VALUES ('1','x','G1')")
    c.execute("INSERT INTO tipnr VALUES (1,'Adam',NULL)")
    c.execute("INSERT INTO abp_corrections VALUES (1, 1, 1, 1)")


def mk(path, sumv=True):
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    base(c, sumv)
    c.commit()
    return c


s = mk(os.path.join(BD, "bible_edupg_test_20261101.db"))
s.close()
# built: 2 strongs cells, 3 strongs_base cells (2 on name slots: v1 @2 H101 -> *, v5 @2 * stays... see below), 1 is_pn cell
b = mk(os.path.join(BD, "bible_edupg_test_built_20261102.db"), sumv=(PLANT != "nosumv"))
b.execute("UPDATE words SET strongs='1999', strongs_base='G1999' WHERE verse_id=1 AND position=3")      # strongs + strongs_base
b.execute("UPDATE words SET strongs='1998', strongs_base='G1998' WHERE verse_id=2 AND position=4")      # strongs + strongs_base
b.execute("UPDATE words SET strongs_base='*' WHERE verse_id=1 AND position=2")                         # name slot H -> *
b.execute("UPDATE words SET is_pn=1 WHERE verse_id=3 AND position=5")                                 # is_pn only
if PLANT == "sb":
    b.execute("UPDATE words SET strongs_base='H999' WHERE verse_id=4 AND position=2")                  # one more (name slot H -> H)
b.execute("UPDATE pn_hebrew_xref SET class='lemma-only' WHERE verse_id=1")                            # none -> lemma-only
b.execute("UPDATE pn_greek_identity SET source='none' WHERE verse_id=2")                              # lemma-only -> none
if PLANT == "verserow":
    b.execute("UPDATE verses SET verse=9 WHERE id=5")                                             # verse id 5 names another verse on built
if PLANT == "verseid":
    b.execute("UPDATE words SET verse_id=9 WHERE verse_id=5")                                     # verse 5 renumbered on built
b.execute("UPDATE abp_corrections SET active=0")
b.execute("DELETE FROM ai_search_cache WHERE query='q3'")
b.commit()
b.close()
# live: src + the site's writes (two new cache rows, one changed, an lsj summary)
lv = mk(os.path.join(BD, "bible.db"))
lv.execute("INSERT INTO ai_search_cache VALUES ('q9','SECRET-AI-TEXT-9','xref:zz',2.0)")
lv.execute("INSERT INTO ai_search_cache VALUES ('q8','SECRET-AI-TEXT-8','weird no colon',2.0)")
lv.execute("UPDATE ai_search_cache SET result_json='SECRET-AI-TEXT-NEW' WHERE query='q0'")
lv.execute("UPDATE lsj SET summary_json='SECRET-SUMMARY' WHERE key='k1'")
if PLANT == "livewords":
    lv.execute("UPDATE words SET english='changed' WHERE id=7")
if PLANT == "books":
    lv.execute("UPDATE books SET sort_order=2")
if PLANT == "extra":
    lv.execute("CREATE TABLE stray (x)")
    lv.execute("INSERT INTO stray VALUES (1)")
lv.commit()
lv.close()
# print the words / verses digests of src (the harness swaps them in for LIVESRC's in the TEST copy only)
sys.path.insert(0, os.path.join(BD, "scripts"))
import eu_step as E  # noqa: E402
c = E.ro(os.path.join(BD, "bible_edupg_test_20261101.db"))
for t in ("words", "verses"):
    n, d = E.digest(c, t)
    print("%s %d %s" % (t, n, d))
c.close()
