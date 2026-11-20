# TIPNR57 tests: make the three made-up copies (src, built, pre_8b) + the three logs. WSL only; no real db is read.
# usage: python3 mkdbs57.py <repo> <bible-db dir> <runs dir> [plant]
#   plant: none | tipnr (built's tipnr table one row short + one row changed)
import os
import sqlite3
import sys
import types

sys.dont_write_bytecode = True   # the test setup must not leave a cache folder either (the block checks for one)

REPO, BD, RUNS = sys.argv[1:4]
PLANT = sys.argv[4] if len(sys.argv) > 4 else "none"
sys.modules["check_p2_guard_fixture"] = types.SimpleNamespace(check_guard_fixture=lambda c: (True, []))
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.argv = ["import_tipnr.py", "x"]
import import_tipnr as T  # noqa: E402

lines = open(os.path.join(REPO, "tipnr", "TIPNR.txt"), encoding="utf-8-sig").read().splitlines()
_lookup, TIP = T.parse_tipnr(lines)

WORDS = ("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT, english_head TEXT,"
         " strongs TEXT, strongs_base TEXT, greek_pos INTEGER, bracket_id INTEGER, italic INTEGER, italic_words TEXT,"
         " smcap_words TEXT, is_pn INTEGER, morph TEXT, lemma TEXT, english_head_norm TEXT)")
VERSES = [(1, "Gen", 1, 1), (2, "Gen", 2, 1), (3, "Exo", 1, 1), (4, "Mat", 1, 1), (5, "Mat", 1, 2), (6, "Num", 1, 1)]
# (verse_id, position, english, strongs_base, is_pn) per copy. Cases (src -> built):
#  A Gen 2:1 @1 'Moses' -> 'Qzxmoses' (LOST, TEXT-CHANGED)   B Exo 1:1 @1 'Qzxaaron' -> 'Aaron' (GAINED, TEXT-CHANGED)
#  C Mat 1:1 @2 'Jesus' name cell -> a numbered non-name cell (LOST, NOT-A-NAME-CELL)
#  D Mat 1:2 @5 'of Judah,' -> no cell @5 on built (LOST, NO-CELL)   E Gen 1:1 'David' @3 -> @4 (MOVED)
#  F Gen 1:1 @1 'Abraham' same   G Gen 2:1 @2 em-dash name cell on both   H Exo 1:1 @2 blank name cell on both
SRC = [(1, 1, "Abraham", "H85", 1), (1, 2, "begot", "G1080", 0), (1, 3, "David", "H1732", 1), (1, 4, "and", "G2532", 0),
       (2, 1, "Moses", "H4872", 1), (2, 2, "Joshua—", "*", 1), (2, 3, "Pharaoh", "H6547", 1),
       (3, 1, "Qzxaaron", "*", 1), (3, 2, "", "*", 1),
       (4, 1, "book", "G976", 0), (4, 2, "Jesus", "G2424", 1),
       (5, 1, "and", "G2532", 0), (5, 2, "begat", "G1080", 0), (5, 3, "Jacob", "G2384", 1), (5, 4, "the", "G3588", 0),
       (5, 5, "of Judah,", "G2455", 1),
       (6, 1, "spoke", "G2980", 0)]
BUILT = [(1, 1, "Abraham", "G11", 1), (1, 2, "begot", "G1080", 0), (1, 3, "and", "G2532", 0), (1, 4, "David", "G1138", 1),
         (2, 1, "Qzxmoses", "*", 1), (2, 2, "Joshua—", "*", 1), (2, 3, "Qzxph", "*", 1),
         (3, 1, "Aaron", "G2", 1), (3, 2, "", "*", 1),
         (4, 1, "book", "G976", 0), (4, 2, "Jesus", "G2424", 0),
         (5, 1, "and", "G2532", 0), (5, 2, "begat", "G1080", 0), (5, 3, "Jacob", "G2384", 1), (5, 4, "the", "G3588", 0),
         (6, 1, "spoke", "G2980", 0)]
# pre_8b = built before 8b: same cells; the import's numbers stored on the name cells; Gen 2:1 @3 still 'Pharaoh'
# (the pre_8b -> built LOST); Exo 1:1 @1 stored '*' though the matcher gives a number (a section-4 disagreement)
PRE = [(1, 1, "Abraham", "H85", 1), (1, 2, "begot", "G1080", 0), (1, 3, "and", "G2532", 0), (1, 4, "David", "H1732", 1),
       (2, 1, "Qzxmoses", "*", 1), (2, 2, "Joshua—", "*", 1), (2, 3, "Pharaoh", "H6547", 1),
       (3, 1, "Aaron", "*", 1), (3, 2, "", "*", 1),
       (4, 1, "book", "G976", 0), (4, 2, "Jesus", "G2424", 0),
       (5, 1, "and", "G2532", 0), (5, 2, "begat", "G1080", 0), (5, 3, "Jacob", "G2384", 1), (5, 4, "the", "G3588", 0),
       (6, 1, "spoke", "G2980", 0)]


def make(path, rows, tip):
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.execute("PRAGMA journal_mode=DELETE")
    c.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT)")
    c.executemany("INSERT INTO verses VALUES (?, ?, ?, ?, 'x')", VERSES)
    c.execute(WORDS)
    c.executemany("INSERT INTO words (verse_id, position, english, english_head, strongs, strongs_base, is_pn)"
                  " VALUES (?, ?, ?, ?, ?, ?, ?)", [(v, p, e, e, s.lstrip("GH") if s != "*" else "*", s, n)
                                                   for v, p, e, s, n in rows])
    c.execute("CREATE TABLE bdb (strongs_id TEXT PRIMARY KEY, word TEXT)")
    c.executemany("INSERT INTO bdb VALUES (?, 'x')", [("H85",), ("H4714",), ("H175",)])
    c.execute("CREATE TABLE lexicon (strongs TEXT PRIMARY KEY, word TEXT)")
    c.executemany("INSERT INTO lexicon VALUES (?, 'x')", [("2424",), ("2541",)])
    c.execute("CREATE TABLE tipnr (strongs TEXT PRIMARY KEY, name TEXT NOT NULL, entity_type TEXT, entity_types TEXT)")
    c.executemany("INSERT INTO tipnr VALUES (?, ?, ?, ?)", tip)
    c.execute("CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, position INT,"
              " field TEXT, source_value TEXT, corrected_value TEXT, status TEXT)")
    c.execute("INSERT INTO abp_corrections VALUES (1, 'Gen', 1, 1, 1, 'english', 'a', 'b', 'active')")
    c.commit()
    c.close()


tb = list(TIP)
if PLANT == "tipnr":
    tb = sorted(tb)
    gone = tb.pop(0)
    tb[0] = (tb[0][0], tb[0][1] + " (changed)", tb[0][2], tb[0][3])
    print("planted on built's tipnr: removed %r, changed %r" % (gone[0], tb[0][0]))
make(os.path.join(BD, "bible_edupg_test_20261101.db"), SRC, TIP)
make(os.path.join(BD, "bible_edupg_test_built_20261102.db"), BUILT, tb)
make(os.path.join(BD, "bible_edupg_test_built_pre_8b_20261106.db"), PRE, TIP)


def log(path, m, u, d):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("(made-up stand-in)\n== finish_rebuild on x ==\n\n── python3 scripts/import_tipnr.py x ──\n")
        f.write("  Matched  : {:,}\n  Unmatched: {:,} words  ({:,} distinct names)\n".format(m, u, d))


log(os.path.join(BD, "finish_pnstar2.log"), 6, 2, 2)                        # src's import: 6 (1 more than src now = 5)
log(os.path.join(RUNS, "stageC_tail3_20261104.log"), 4, 3, 3)               # built's import
log(os.path.join(RUNS, "step4_b_standard_20261117", "finish.out"), 4, 3, 3)  # BSTD = pre_8b
print("made: src / built / pre_8b, %d tipnr rows (built %d), logs" % (len(TIP), len(tb)))
