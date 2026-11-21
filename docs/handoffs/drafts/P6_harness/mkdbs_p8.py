# P8 tests: the made-up files. No real db is read. A 4,411-slot fill (3,873 inserts + 538 updates) so the real
# snapshot_surface_fill.py prints the real expected lines.
# usage: python3 mkdbs_p8.py <bible-db dir> <home> [plant]      plant: none | srcsame (src = live: the control cannot read STALE)
# writes: <bible-db>/bible.db (live), <bible-db>/bible_edupg_test_20261101.db (src: live minus one fill row),
#         <home>/abp_surface_prefill_20261115.db, <home>/report.tsv (a restore report placing the 4,411 slots)
import os
import sqlite3
import sys

sys.dont_write_bytecode = True
BD, HOME = sys.argv[1], sys.argv[2]
PLANT = sys.argv[3] if len(sys.argv) > 3 else "none"
NV, NP, NINS, NUPD = 500, 10, 3873, 538
slots = [(v, p) for v in range(1, NV + 1) for p in range(NP)][:NINS + NUPD]
ins, upd = slots[:NINS], set(slots[NINS:])
allk = [(v, p) for v in range(1, NV + 1) for p in range(NP)]


def ref(v):
    return ("Gen", 1 + (v - 1) // 50, 1 + (v - 1) % 50)


def mk(path, full):
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE abp_surface (verse_id INT, position INT, form TEXT, translit TEXT)")
    if full:
        c.executescript("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);"
                        "CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT, strongs TEXT, strongs_base TEXT,"
                        " english TEXT, english_head TEXT, is_pn INT);")
        for v in range(1, NV + 1):
            c.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (v,) + ref(v) + ("SECRET-VERSE",))
            for p in range(NP):
                c.execute("INSERT INTO words (verse_id, position, strongs, strongs_base, english, english_head, is_pn) VALUES (?,?,?,?,?,?,0)",
                          (v, p, str(100 + p % 4), "G%d" % (100 + p % 4), "SECRET-ENGLISH %d" % p, "head"))
    return c


def fill(c, new, skip=None):
    sins = set(ins)
    for k in allk:
        if k == skip:
            continue
        if k in sins:
            if new:
                c.execute("INSERT INTO abp_surface VALUES (?,?,?,?)", k + ("f%d_%d" % k, "t"))
        elif k in upd:
            c.execute("INSERT INTO abp_surface VALUES (?,?,?,?)", k + (("n%d_%d" % k, "t") if new else ("old", "o")))
        else:
            c.execute("INSERT INTO abp_surface VALUES (?,?,?,?)", k + ("base", "b"))
    c.commit()
    c.close()


fill(mk(os.path.join(BD, "bible.db"), True), True)
fill(mk(os.path.join(BD, "bible_edupg_test_20261101.db"), True), True, skip=None if PLANT == "srcsame" else ins[7])
fill(mk(os.path.join(HOME, "abp_surface_prefill_20261115.db"), False), False)
with open(os.path.join(HOME, "report.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("book\tchapter\tverse\told_position\tnew_position\taction\tcls\tform\tresult\n")
    sins = set(ins)
    for k in slots:
        b, ch, vs = ref(k[0])
        f.write("%s\t%d\t%d\t%d\t%d\t%s\tc1\t%s\tplaced\n" % (b, ch, vs, k[1], k[1], "insert" if k in sins else "update",
                                                         ("f%d_%d" if k in sins else "n%d_%d") % k))
