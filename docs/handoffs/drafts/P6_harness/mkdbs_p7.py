# P7 tests: make the made-up pair "the rollback file" (old live) and "bible.db" (the swapped-in file). No real db is read.
# The pair is built so that the G5 read gives EXACTLY the real expected figures (DESIGN 9.222 (5), 9.223): the unmodified
# expectations in p7_check.py are what the tests exercise. Only the three digests of (1) are the made-up files' own.
# usage: python3 mkdbs_p7.py <bible-db dir> <rollback file name> [plant]
# plant: none | xrefkey (one class move sits on a seventh verse) | count (one more identity row changed)
#        | slot (one more name-slot strongs_base change) | wordsdig (a words cell changed after the digests were taken)
#        | notable (word_gloss missing on live) | verseid (a verse id names another verse on live)
import os
import sqlite3
import sys

sys.dont_write_bytecode = True
BD, RBN = sys.argv[1], sys.argv[2]
PLANT = sys.argv[3] if len(sys.argv) > 3 else "none"
SIX = [("Num", 21, 25), ("1Sa", 20, 37), ("2Sa", 15, 6), ("Jer", 48, 15), ("Jer", 48, 20), ("Jer", 49, 3)]
REKEY = [("2Ki", 23, 35, 6), ("Est", 5, 9, 12), ("Gen", 5, 25, 1), ("Gen", 5, 26, 1), ("Gen", 34, 4, 1), ("Jos", 5, 15, 27)]
VERSES = SIX + [k[:3] for k in REKEY] + [("Psa", 1, i) for i in range(1, 81)]          # ids 1-6, 7-12, 13-92
MOVES = ([("surface", "lemma-only")] * 33 + [("lemma-only", "surface")] * 6 + [("none", "surface")] * 6 + [("surface", "tipnr")] * 6
         + [("lemma-only", "tipnr")] * 3 + [("none", "lemma-only")] * 2 + [("lemma-only", "none")])   # 57
SLOTS = [("*", "G5")] * 3 + [("G5", "*")] * 3 + [("G5", "G6")] * 6 + [("H5", "*")] * 6                 # 18
SCHEMA = ("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, english TEXT, english_head TEXT, strongs TEXT,"
          " strongs_base TEXT, greek_pos INTEGER, bracket_id INTEGER, italic INTEGER, italic_words TEXT, smcap_words TEXT, is_pn INTEGER,"
          " morph TEXT, lemma TEXT, english_head_norm TEXT);"
          "CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);"
          "CREATE TABLE pn_hebrew_xref (verse_id INTEGER NOT NULL, position INTEGER NOT NULL, hebrew_base TEXT, class TEXT NOT NULL, PRIMARY KEY (verse_id, position));"
          "CREATE TABLE pn_greek_identity (verse_id INTEGER NOT NULL, position INTEGER NOT NULL, greek_strongs TEXT, greek_lemma TEXT, source TEXT NOT NULL, hebrew_base TEXT, PRIMARY KEY (verse_id, position));"
          "CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, verse_id INT, position INT, status TEXT);"
          "CREATE TABLE abp_surface (verse_id INT, position INT, surface TEXT);"
          "CREATE TABLE pn_binding (a); CREATE TABLE pn_slot_binding (a); CREATE TABLE tipnr_metav_link (a); CREATE TABLE word_gloss (a);")


def mk(path, new):
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.executescript(SCHEMA)
    for i, (b, ch, v) in enumerate(VERSES, 1):
        c.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (i, b, ch, v, "SECRET-VERSE-TEXT %d" % i))
        c.execute("INSERT INTO words (verse_id, position, english, strongs_base, is_pn) VALUES (?,?,?,?,0)", (i, 0, "SECRET-WORD", "G1"))
    for i in range(1, 7):                                                    # the six class moves, none -> lemma-only
        vid = i
        if PLANT == "xrefkey" and i == 6:
            c.execute("INSERT INTO pn_hebrew_xref VALUES (6, 3, 'H1', 'none')")   # Jer 49:3 does not move ...
            vid = 21
        c.execute("INSERT INTO pn_hebrew_xref VALUES (?,?,?,?)", (vid, 3, "H1", "lemma-only" if new else "none"))
    if PLANT != "xrefkey":
        c.execute("INSERT INTO pn_hebrew_xref VALUES (21, 3, 'H1', 'none')")      # ... and a seventh verse does (Psa 1:9)
    for j, k in enumerate(REKEY):                                            # the 6 re-keyed records: old position = new + 1
        pos = k[3] if new else k[3] + 1
        c.execute("INSERT INTO pn_hebrew_xref VALUES (?,?,?,?)", (7 + j, pos, "H2", "tipnr"))
        c.execute("INSERT INTO pn_greek_identity VALUES (?,?,?,?,?,?)", (7 + j, pos, "G9", "x", "tipnr", "H2"))
    for j, (a, b) in enumerate(MOVES):
        gs = ("G2", "b") if (new and j < 9) else ("G1", "a")
        c.execute("INSERT INTO pn_greek_identity VALUES (?,?,?,?,?,?)", (13 + j, 2, gs[0], gs[1], b if new else a, "H3"))
    c.execute("INSERT INTO pn_greek_identity VALUES (70, 2, 'G1', 'a', ?, 'H3')", ("none" if (new and PLANT == "count") else "tipnr",))
    for j, (a, b) in enumerate(SLOTS):
        c.execute("INSERT INTO words (verse_id, position, english, strongs_base, is_pn) VALUES (?,?,?,?,1)", (13 + j, 5, "Name", b if new else a))
    c.execute("INSERT INTO words (verse_id, position, english, strongs_base, is_pn) VALUES (31, 5, 'Name', ?, 1)",
              ("H6" if (new and PLANT == "slot") else "H5",))
    for i in range(5):
        c.execute("INSERT INTO abp_surface VALUES (?,?,?)", (i + 1, 0, "s"))
    c.execute("INSERT INTO abp_corrections VALUES (1, 1, 0, 'active')")
    for t in ("pn_binding", "pn_slot_binding", "tipnr_metav_link", "word_gloss"):
        c.execute("INSERT INTO %s VALUES (1)" % t)
    if new and PLANT == "notable":
        c.execute("DROP TABLE word_gloss")
    if new and PLANT == "verseid":
        c.execute("UPDATE verses SET verse = 99 WHERE id = 80")
    c.commit()
    c.close()


old, live = os.path.join(BD, RBN), os.path.join(BD, "bible.db")
mk(old, False)
mk(live, True)
sys.path.insert(0, os.path.join(BD, "scripts"))
import eu_step as E  # noqa: E402
c = E.ro(live)
d = {t: E.digest(c, t) for t in ("words", "abp_corrections", "abp_surface")}
c.close()
print("BUILT = {%s}" % ", ".join('"%s": (%d, "%s")' % (t, d[t][0], d[t][1][:12]) for t in d))
if PLANT == "wordsdig":
    w = sqlite3.connect(live)
    w.execute("UPDATE words SET english = 'changed' WHERE verse_id = 40 AND position = 0")
    w.commit()
    w.close()
