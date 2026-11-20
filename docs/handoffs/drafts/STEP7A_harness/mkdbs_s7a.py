# STEP7A tests: make the made-up src / built copies + DELTA2 stand-ins. WSL only; no real db is read.
# usage: python3 mkdbs_s7a.py <bible-db dir> <runs dir> <real prose list> <real eligible file> [plant]
# plant: none | extra (built Gen 1:21 @19 english changed again) | chip (1Ch 13:10 the LORD's greek_pos above the verb's on built)
#        | adam (built's Adam xref H122) | lemma (both copies' G2206 lemma 'ζηλῶ') | d2miss (DELTA2 stand-in lacks Mark 1:9 @13)
import os
import shutil
import sqlite3
import sys

sys.dont_write_bytecode = True
BD, RUNS, PRO, EL = sys.argv[1:5]
PLANT = sys.argv[5] if len(sys.argv) > 5 else "none"
WORDS = ("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT, english_head TEXT,"
         " strongs TEXT, strongs_base TEXT, greek_pos INTEGER, bracket_id INTEGER, italic INTEGER, italic_words TEXT,"
         " smcap_words TEXT, is_pn INTEGER, morph TEXT, lemma TEXT, english_head_norm TEXT)")
T_1CH13_S = ("And the LORD was enraged in anger against Uzza, and he struck him there, on account of the stretching out of his"
             " hand upon the ark. And he died there before God.")
T_1CH13_B = ("And the LORD was enraged in anger against Uzza, and struck him there, on account of the stretching out of his"
             " hand upon the ark; and he died there before God.")
T_GEN_S = ("And God made the great whales, and every life of living creatures of reptiles which the waters brought forth"
           " according to their types; and every feathered winged creature according to type. And God beheld that it was good.")
T_GEN_B = ("And God made the great sea monsters, and every soul of living creatures of reptiles which the waters brought forth"
           " according to their types, and every feathered winged creature according to type. And God beheld that it was good.")
T_MAR_S = "And it came to pass in those days, Jesus came from Nazareth of the of Galilee, and he was immersed by John into the Jordan."
T_MAR_B = "And it came to pass in those days, Jesus came from Nazareth of Galilee, and was immersed by John into the Jordan."
T_EZE = "Because of the multitude of his branches; and the trees of the paradise of God were jealous of it."
T_ADAM = "Adam, Seth, Enosh,"
VERSES = [(1, "1Ch", 13, 10), (2, "Eze", 31, 9), (3, "1Ch", 1, 1), (4, "Gen", 1, 21), (5, "Mar", 1, 9), (6, "Joh", 19, 18)]
# word rows: (vid, pos, english, english_head, strongs_base, greek_pos, bracket_id, is_pn, head_norm)
COMMON = [
    (1, 1, "And", "And", "G2532", None, None, 0, "and"), (1, 2, "was enraged", "enraged", "G2373", 2, 7, 0, "enrage"),
    (1, 3, "the LORD", "LORD", "G2962", 1, 7, 0, "lord"), (1, 4, "in anger", "anger", "G2372", None, None, 0, "anger"),
    (1, 5, "against", "against", "G1909", None, None, 0, "against"), (1, 6, "Uzza,", "Uzza", "*", None, None, 1, "uzza"),
    (1, 8, "him", "him", "G846", None, None, 0, "him"), (1, 9, "there,", "there", "G1563", None, None, 0, "there"),
    (1, 10, "on account of", "account", "G1223", None, None, 0, "account"),
    (1, 11, "the stretching out", "stretching", "G1614", None, None, 0, "stretch"),
    (1, 12, "of his", "his", "G846", None, None, 0, "his"), (1, 13, "hand", "hand", "G5495", None, None, 0, "hand"),
    (1, 14, "upon", "upon", "G1909", None, None, 0, "upon"), (1, 15, "the", "the", "G3588", None, None, 0, "the"),
    (1, 20, "he died", "died", "G599", None, None, 0, "die"), (1, 21, "there", "there", "G1563", None, None, 0, "there"),
    (1, 22, "before", "before", "G1725", None, None, 0, "before"), (1, 23, "God.", "God", "G2316", None, None, 0, "god"),
    (2, 1, "Because of", "Because", "G1223", None, None, 0, "because"),
    (2, 2, "the multitude", "multitude", "G4128", None, None, 0, "multitude"),
    (2, 3, "of his branches;", "branches", "G2814", None, None, 0, "branch"),
    (2, 4, "and", "and", "G2532", None, None, 0, "and"), (2, 5, "the trees", "trees", "G3586", None, None, 0, "tree"),
    (2, 6, "of the paradise", "paradise", "G3857", None, None, 0, "paradise"),
    (2, 7, "of God", "God", "G2316", None, None, 0, "god"),
    (2, 8, "were jealous of", "jealous", "G2206", None, None, 0, "jealous"), (2, 9, "it.", "it", "G846", None, None, 0, "it"),
    (3, 1, "Adam,", "Adam", "*", None, None, 1, "adam"), (3, 2, "Seth,", "Seth", "*", None, None, 1, "seth"),
    (3, 3, "Enosh,", "Enosh", "*", None, None, 1, "enosh"),
    (4, 1, "And", "And", "G2532", None, None, 0, "and"), (4, 2, "God", "God", "G2316", None, None, 0, "god"),
    (4, 3, "made", "made", "G4160", None, None, 0, "make"), (4, 4, "the great", "great", "G3173", None, None, 0, "great"),
    (4, 6, "and", "and", "G2532", None, None, 0, "and"), (4, 7, "every", "every", "G3956", None, None, 0, "every"),
    (4, 11, "of living creatures", "creatures", "G2198", None, None, 0, "creature"),
    (4, 12, "of reptiles", "reptiles", "G2062", None, None, 0, "reptile"),
    (4, 13, "which", "which", "G3739", None, None, 0, "which"),
    (4, 14, "the waters brought forth", "brought", "G1806", None, None, 0, "bring"),
    (4, 15, "according to", "according", "G2596", None, None, 0, "accord"),
    (4, 18, "their", "their", "G846", None, None, 0, "their"),
    (4, 20, "and every feathered winged creature according to type. And God beheld that it was good.", "good", "G2570",
     None, None, 0, "good"),
    (5, 1, "And", "And", "G2532", None, None, 0, "and"), (5, 2, "it came to pass", "pass", "G1096", 2, 3, 0, "pass"),
    (5, 3, "in", "in", "G1722", 1, 3, 0, "in"), (5, 4, "those", "those", "G1565", None, None, 0, "those"),
    (5, 5, "days,", "days", "G2250", None, None, 0, "day"), (5, 6, "Jesus", "Jesus", "G2424", None, None, 1, "jesus"),
    (5, 7, "came", "came", "G2064", None, None, 0, "come"), (5, 8, "from", "from", "G575", None, None, 0, "from"),
    (5, 9, "Nazareth", "Nazareth", "G3478", None, None, 1, "nazareth"),
    (5, 12, "and", "and", "G2532", None, None, 0, "and"), (5, 14, "by", "by", "G5259", None, None, 0, "by"),
    (5, 15, "John", "John", "G2491", None, None, 1, "john"), (5, 16, "into", "into", "G1519", None, None, 0, "into"),
    (5, 17, "the Jordan.", "Jordan", "G2446", None, None, 1, "jordan"),
    (6, 10, "here", "here", "G1782", None, None, 0, "here"),
]
SRC_ONLY = [
    (1, 7, "he struck", "struck", "G3960", None, None, 0, "strike"), (1, 18, "ark.", "ark", "G2787", None, None, 0, "ark"),
    (1, 19, "And", "And", "G2532", None, None, 0, "and"),
    (4, 5, "whales", "whales", "G2785", None, None, 0, "whale"), (4, 10, "life", "life", "G5590", None, None, 0, "life"),
    (4, 16, "types;", "types", "G1085", None, None, 0, "type"), (4, 17, "", "", "G846", None, None, 0, ""),
    (4, 19, "types;", "types", "G1085", None, None, 0, "type"),
    (5, 10, "of the", "the", "G3588", None, None, 0, "the"), (5, 11, "of Galilee,", "Galilee", "G1056", None, None, 1, "galilee"),
    (5, 13, "he was immersed", "immersed", "G907", None, None, 0, "immerse"),
]
BUILT_ONLY = [
    (1, 7, "struck", "struck", "G3960", None, None, 0, "strike"), (1, 18, "ark;", "ark", "G2787", None, None, 0, "ark"),
    (1, 19, "and", "And", "G2532", None, None, 0, "and"),
    (4, 5, "sea monsters", "monsters", "G2785", None, None, 0, "monster"), (4, 10, "soul", "soul", "G5590", None, None, 0, "soul"),
    (4, 16, "types;", "types", "G1085", None, None, 0, "type"), (4, 17, "", "", "G846", None, None, 0, ""),
    (4, 19, "types,", "types", "G1085", None, None, 0, "type"),
    (5, 10, "of", "the", "G3588", 1, 9, 0, "the"), (5, 11, "Galilee,", "Galilee", "G1056", 2, 9, 1, "galilee"),
    (5, 13, "was immersed", "immersed", "G907", None, None, 0, "immerse"),
]


def make(path, rows, texts, side):
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.execute("PRAGMA journal_mode=DELETE")
    c.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT)")
    c.executemany("INSERT INTO verses VALUES (?, ?, ?, ?, ?)", [v + (texts[v[0]],) for v in VERSES])
    c.execute(WORDS)
    c.executemany("INSERT INTO words (verse_id, position, english, english_head, strongs, strongs_base, greek_pos, bracket_id,"
                  " italic, italic_words, smcap_words, is_pn, morph, lemma, english_head_norm)"
                  " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, '', '', ?, 'x', 'x', ?)",
                  sorted([(v, p, e, h, s.lstrip("GH") if s != "*" else "*", s, g, b, n, hn)
                          for v, p, e, h, s, g, b, n, hn in rows]))
    c.execute("CREATE TABLE lexicon (strongs_g TEXT PRIMARY KEY, lemma TEXT)")
    lem = "ζηλῶ" if PLANT == "lemma" else "ζηλόω"
    c.executemany("INSERT INTO lexicon VALUES (?, ?)", [("G2206", lem), ("G2785", "κῆτος"), ("G2962", "κύριος"),
                                                        ("G2373", "θυμόω")])
    c.execute("CREATE TABLE pn_hebrew_xref (verse_id INTEGER NOT NULL, position INTEGER NOT NULL, hebrew_base TEXT,"
              " class TEXT NOT NULL)")
    adam = "H122" if (PLANT == "adam" and side == "built") else "H121"
    c.executemany("INSERT INTO pn_hebrew_xref VALUES (?, ?, ?, ?)", [(3, 1, adam, "tipnr"), (3, 2, "H8352", "tipnr")])
    c.execute("CREATE TABLE pn_binding(book INTEGER, chapter INTEGER, verse INTEGER, name TEXT, entity_uniq TEXT, kind TEXT,"
              " rule TEXT, render INTEGER, hot INTEGER, tier INTEGER)")
    c.executemany("INSERT INTO pn_binding VALUES (?,?,?,?,?,?,?,?,?,?)",
                  [(13, 1, 1, "adam", "Adam@Gen.2.19", "person", "r1", 1, 0, 1),
                   (13, 1, 1, "seth", "Seth@Gen.4.25", "person", "r1", 1, 0, 1)])
    c.execute("CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, position INT,"
              " field TEXT, source_value TEXT, corrected_value TEXT, status TEXT)")
    c.execute("INSERT INTO abp_corrections VALUES (1, 'Gen', 1, 1, 1, 'english', 'a', 'b', 'active')")
    c.commit()
    c.close()


st = {1: T_1CH13_S, 2: T_EZE, 3: T_ADAM, 4: T_GEN_S, 5: T_MAR_S, 6: "here"}
bt = {1: T_1CH13_B, 2: T_EZE, 3: T_ADAM, 4: T_GEN_B, 5: T_MAR_B, 6: "ere"}
brows = COMMON + BUILT_ONLY
if PLANT == "extra":
    brows = [r if (r[0], r[1]) != (4, 19) else (4, 19, "types:", "types", "G1085", None, None, 0, "type") for r in brows]
if PLANT == "chip":
    brows = [(1, 3, "the LORD", "LORD", "G2962", 3, 7, 0, "lord") if (r[0], r[1]) == (1, 3) else r for r in brows]
make(os.path.join(BD, "bible_edupg_test_20261101.db"), COMMON + SRC_ONLY, st, "src")
make(os.path.join(BD, "bible_edupg_test_built_20261102.db"), brows, bt, "built")
# DELTA2 stand-ins: header + the lines the real file holds for these verses + one Joh 19:18 pair (other verses are filtered)
dd = os.path.join(RUNS, "step4_delta2_20261116", "delta")
os.makedirs(dd, exist_ok=True)
WC = """book	chapter	verse	position	column	a	b	moved
1Ch	1	3	1	english	'Methuselah,'	'Mathusala,'	no
1Ch	13	10	7	english	'he struck'	'struck'	no
1Ch	13	10	18	english	'ark.'	'ark;'	no
1Ch	13	10	19	english	'And'	'and'	no
Gen	1	21	5	english	'whales'	'sea monsters'	no
Gen	1	21	5	english_head	'whales'	'monsters'	no
Gen	1	21	5	english_head_norm	'whale'	'monster'	no
Gen	1	21	10	english	'life'	'soul'	no
Gen	1	21	10	english_head	'life'	'soul'	no
Gen	1	21	10	english_head_norm	'life'	'soul'	no
Gen	1	21	19	english	'types;'	'types,'	no
Joh	19	18	10	english	'here'	'ere'	no
Mar	1	9	10	english	'of the'	'of'	no
Mar	1	9	10	greek_pos	None	1	no
Mar	1	9	10	bracket_id	None	2	no
Mar	1	9	11	english	'of Galilee,'	'Galilee,'	no
Mar	1	9	11	greek_pos	None	2	no
Mar	1	9	11	bracket_id	None	2	no
Mar	1	9	13	english	'he was immersed'	'was immersed'	no
"""
if PLANT == "d2miss":
    WC = "".join(l + "\n" for l in WC.splitlines() if not l.startswith("Mar\t1\t9\t13\t"))
with open(os.path.join(dd, "words_cells.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write(WC)
with open(os.path.join(dd, "verses_cells.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("book\tchapter\tverse\tcolumn\ta\tb\n")
    for k, a, b in ((("1Ch", 13, 10), T_1CH13_S, T_1CH13_B), (("Gen", 1, 21), T_GEN_S, T_GEN_B), (("Joh", 19, 18), "here", "ere"),
                    (("Mar", 1, 9), T_MAR_S, T_MAR_B)):
        f.write("\t".join([k[0], str(k[1]), str(k[2]), "text", repr(a), repr(b)]) + "\n")
shutil.copy(PRO, os.path.join(RUNS, "step5_prose_20261101.tsv"))
shutil.copy(EL, os.path.join(RUNS, "step5_eligible_20261101.tsv"))
print("made: src / built (plant %s), DELTA2 stand-ins, the real prose + eligible files" % PLANT)
