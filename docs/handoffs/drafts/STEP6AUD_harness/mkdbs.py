# STEP6AUD tests: build the made-up src / built test copies (WSL; never a real db).
# argv: 1 the d34d6723 test clone (scripts, abp_app_html sample)  2 the 11/18 test copies folder  3 out folder
# Starts from the step-4/5 test copies (626,309 words / 31,237 verses, made-up rows "wordN") and adds what each
# step-6 audit reads, so every zero-floor audit reads 0 on the clean pair, plus the in-corpus known positives the
# real data carries (Psa 39:1 phrase-gloss control, Job 3:3 content-other, Heb 11:24 the spent-by-lane-3 row).
import csv, json, shutil, sqlite3, sys
from pathlib import Path

REPO, IN, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(REPO / "scripts"))
from reorder_english import get_english_order_words          # the reader's order (v2 reassembles in it)
from audit_abp_app_vs_surface import load_app                # the census's own app loader

OUT.mkdir(parents=True, exist_ok=True)
NAMES = {"src": "bible_edupg_test_20261101.db", "built": "bible_edupg_test_built_20261102.db"}
dod = list(csv.reader(open(REPO / "scripts/apfathers/raw/dodson.csv", encoding="utf-8"), delimiter="\t"))[1:]
heb_op = {op["pos"]: op for op in json.load(open(REPO / "scripts/lane3_star_fixes2.json", encoding="utf-8"))["Heb 11:24"]["ops"]}
app, _ = load_app(str(REPO / "abp_app_html/abp_app_slots.tsv"))


def vid(c, b, ch, v):
    return c.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?", (b, ch, v)).fetchone()[0]


def setw(c, ref, pos, **kw):
    v = vid(c, *ref)
    cols = ", ".join("%s=?" % k for k in kw)
    n = c.execute("UPDATE words SET %s WHERE verse_id=? AND position=?" % cols, list(kw.values()) + [v, pos]).rowcount
    assert n == 1, (ref, pos, kw)


def retext(c):
    """verses.text = the rows' English in the reader's order (no brackets but Heb 11:24 on built), so v1 + v2 read 0."""
    rows = c.execute("SELECT verse_id, position, english, bracket_id, greek_pos FROM words ORDER BY verse_id, position")
    by = {}
    for v, p, e, b, g in rows:
        by.setdefault(v, []).append({"english": e, "bracket_id": b, "greek_pos": g, "position": p})
    for v, ws in by.items():
        t = " ".join((w["english"] or "") for w in get_english_order_words(ws))
        c.execute("UPDATE verses SET text=? WHERE id=?", (" ".join(t.split()), v))


# the census's "same" verse: a verse the slots sample pairs, its row count made = the app's sub-slot count
# (the census counts a verse count-differs on slot count alone, census_count_differs.py :52, align_verse :291)
VP = ("Hab", 3, 1)
VQ = ("Jon", 1, 1)            # not in the sample; it gives / takes the rows, so words stays 626,309
assert VP in app and VQ not in app, (VP in app, VQ in app)
NAPP = len(app[VP])

for which, name in NAMES.items():
    p = OUT / name
    shutil.copyfile(IN / name, p)
    c = sqlite3.connect(p)
    c.executescript("""
      UPDATE words SET bracket_id=NULL, greek_pos=NULL;
      UPDATE words SET is_pn=1 WHERE strongs_base='*';
      UPDATE words SET english_head=english, english_head_norm=lower(english);
      UPDATE words SET lemma = CASE WHEN strongs_base LIKE 'G%' THEN 'lem'||substr(strongs_base,2) ELSE NULL END;
      DROP TABLE IF EXISTS abp_corrections;
      CREATE TABLE abp_corrections(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, position INT, field TEXT,
                                   source_value TEXT, corrected_value TEXT, status TEXT, applied_at TEXT, ledger_ref TEXT, reason TEXT);
      CREATE TABLE lexicon(strongs TEXT, lemma TEXT, kjv_def TEXT, strongs_def TEXT);
      CREATE TABLE word_gloss(strongs TEXT, gloss TEXT);
      CREATE TABLE bdb(strongs_id TEXT, description TEXT);
      CREATE TABLE lsj(plain TEXT, def_html TEXT);
      CREATE TABLE abp_surface(id INTEGER PRIMARY KEY);
    """)
    for r in dod:
        n = str(int(r[0]))
        c.execute("INSERT INTO lexicon VALUES (?,?,?,?)", (n, "lem" + n, r[3], r[4]))
        c.execute("INSERT INTO word_gloss VALUES (?,?)", ("G" + n, r[3]))
    c.executemany("INSERT INTO bdb VALUES (?,?)", [("H3478", "Israel"), ("H3129", "Jonathan"), ("H53", "Absalom"),
                                                  ("H4124", "Moab"), ("H5857", "Ai")])
    c.execute("INSERT INTO lsj VALUES ('lem3588', '<b>ART.</b> the definite article')")
    c.execute("WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM n WHERE i < ?) INSERT INTO abp_surface SELECT i FROM n",
              (395014 if which == "built" else 395003,))
    # Psa 39:1 - the phrase-gloss built-in control (audit_phrase_gloss_underdist.py :8-10): "to not sin" on G3361, G264 blank
    setw(c, ("Psa", 39, 1), 3, strongs="3361", strongs_base="G3361", english="to not sin", english_head="sin", lemma="lem3361")
    setw(c, ("Psa", 39, 1), 4, strongs="264", strongs_base="G264", english="", english_head="", lemma="lem264")
    # Heb 11:24 @7 / @8 - lane-3 fixes2 (scripts/lane3_star_fixes2.json); src before 8b.2a, built after it
    o7, o8 = heb_op[7], heb_op[8]
    if which == "built":
        setw(c, ("Heb", 11, 24), 7, strongs="2364", strongs_base=o7["sbase"], english=o7["new_eng"], english_head=o7["new_head"],
             greek_pos=o7["new_gpos"], bracket_id=o7["new_bid"], lemma="lem2364")
        setw(c, ("Heb", 11, 24), 8, strongs="*", strongs_base=o8["sbase"], is_pn=1, english=o8["new_eng"], english_head=o8["new_head"],
             greek_pos=o8["new_gpos"], bracket_id=o8["new_bid"], lemma=None)
    else:
        setw(c, ("Heb", 11, 24), 7, strongs="2364", strongs_base=o7["sbase"], english=o7["old_eng"], english_head="daughter",
             lemma="lem2364")
        setw(c, ("Heb", 11, 24), 8, strongs="*", strongs_base="*", is_pn=1, english="", english_head="", lemma=None)
    # the census "same" verse
    vp, vq = vid(c, *VP), vid(c, *VQ)
    have = c.execute("SELECT count(*) FROM words WHERE verse_id=?", (vp,)).fetchone()[0]
    if have > NAPP:
        for (rid,) in c.execute("SELECT rowid FROM words WHERE verse_id=? ORDER BY position DESC LIMIT ?", (vp, have - NAPP)).fetchall():
            mx = c.execute("SELECT max(position) FROM words WHERE verse_id=?", (vq,)).fetchone()[0]
            c.execute("UPDATE words SET verse_id=?, position=? WHERE rowid=?", (vq, mx + 1, rid))
    elif have < NAPP:
        for (rid,) in c.execute("SELECT rowid FROM words WHERE verse_id=? ORDER BY position DESC LIMIT ?", (vq, NAPP - have)).fetchall():
            mx = c.execute("SELECT max(position) FROM words WHERE verse_id=?", (vp,)).fetchone()[0]
            c.execute("UPDATE words SET verse_id=?, position=? WHERE rowid=?", (vp, mx + 1, rid))
    retext(c)
    c.execute("UPDATE verses SET text = text || ' zzextra' WHERE id=?", (vid(c, "Job", 3, 3),))   # Job 3:3 content-other
    # abp_corrections: active ingest rows that HOLD (english cells in Exo), + the Heb 11:24 @7 row (holds on src, spent on built)
    hold = 374 if which == "built" else 373
    slots = c.execute("SELECT v.book, v.chapter, v.verse, w.position, w.english FROM words w JOIN verses v ON v.id=w.verse_id "
                      "WHERE v.book='Exo' AND w.position=1 ORDER BY v.id LIMIT ?", (hold,)).fetchall()
    for b, ch, v, pos, e in slots:
        c.execute("INSERT INTO abp_corrections(book,chapter,verse,position,field,source_value,corrected_value,status,applied_at,"
                  "ledger_ref,reason) VALUES (?,?,?,?,'english','old',?,'active','ingest','TEST','test row')", (b, ch, v, pos, e))
    c.execute("INSERT INTO abp_corrections(book,chapter,verse,position,field,source_value,corrected_value,status,applied_at,"
              "ledger_ref,reason) VALUES ('Heb',11,24,7,'english',?,?,'active','ingest','EU-Heb11:24','test row')",
              ("of Pharoah's daughter,", o7["old_eng"]))
    for i in range(23):
        c.execute("INSERT INTO abp_corrections(book,chapter,verse,position,field,source_value,corrected_value,status,applied_at,"
                  "ledger_ref,reason) VALUES ('Lev',1,?,1,'english','x','y','retired','ingest','TEST','retired')", (i + 1,))
    for i in range(6):
        c.execute("INSERT INTO abp_corrections(book,chapter,verse,position,field,source_value,corrected_value,status,applied_at,"
                  "ledger_ref,reason) VALUES ('Lev',2,?,1,'english','x','y','other','ingest','TEST','other')", (i + 1,))
    c.commit()
    n = c.execute("SELECT count(*) FROM words").fetchone()[0]
    a = c.execute("SELECT count(*) FROM abp_corrections WHERE status='active' AND applied_at='ingest'").fetchone()[0]
    c.execute("VACUUM")
    c.close()
    print("%s: words %d - active ingest corrections %d - %s rows %d (app sub-slots %d)" % (which, n, a, VP, NAPP, NAPP))
