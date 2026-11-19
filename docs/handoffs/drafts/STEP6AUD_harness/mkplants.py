# STEP6AUD tests: plant one known positive per detector into a test home's built (each in its own verse, so each FINDING
# names its plant), plus the file-side plants; then re-make the "built =" guard on the planted copy (as STEP5INV T4 did).
# argv: 1 test home.  WSL only, made-up copies only.
import sqlite3, subprocess, sys
from pathlib import Path

H = Path(sys.argv[1])
B = H / "bible-db/bible_edupg_test_built_20261102.db"
R = H / "edition_upgrade_runs"
sys.path.insert(0, str(H / "bible-db/scripts"))
from reorder_english import get_english_order_words

c = sqlite3.connect(B)


def vid(b, ch, v):
    return c.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?", (b, ch, v)).fetchone()[0]


def setw(ref, pos, **kw):
    n = c.execute("UPDATE words SET %s WHERE verse_id=? AND position=?" % ", ".join("%s=?" % k for k in kw),
                  list(kw.values()) + [vid(*ref), pos]).rowcount
    assert n == 1, (ref, pos)


def retext(ref, extra=""):
    ws = [{"english": e, "bracket_id": b, "greek_pos": g, "position": p} for p, e, b, g in c.execute(
        "SELECT position, english, bracket_id, greek_pos FROM words WHERE verse_id=? ORDER BY position", (vid(*ref),))]
    t = " ".join(" ".join((w["english"] or "") for w in get_english_order_words(ws)).split()) + extra
    c.execute("UPDATE verses SET text=? WHERE id=?", (t, vid(*ref)))
    return t


plants = []
# P1 A1 health: a bare-number strongs_base (health_check.py :47-48 WARN)
setw(("2Ki", 1, 1), 1, strongs="4151", strongs_base="4151"); plants.append("P1 A1 2Ki 1:1 @1 strongs_base '4151'")
# P2 A3 cross: function anchor G3588 shows 'glory', its neighbour G1391 (dodson: glory) shows only 'of'
setw(("2Ki", 2, 1), 1, strongs="3588", strongs_base="G3588", english="glory", english_head="glory", lemma="lem3588")
setw(("2Ki", 2, 1), 2, strongs="1391", strongs_base="G1391", english="of", english_head="of", lemma="lem1391")
retext(("2Ki", 2, 1)); plants.append("P2 A3 2Ki 2:1 @1 G3588 'glory' <-> @2 G1391 'of'")
# P3 A4 LORD: 'the LORD said' on G2036, the next slot an empty G2962 (audit_lord_strongs.py repair_shape)
setw(("2Ki", 3, 1), 1, strongs="2036", strongs_base="G2036", english="the LORD said", english_head="said", lemma="lem2036")
setw(("2Ki", 3, 1), 2, strongs="2962", strongs_base="G2962", english="", english_head="", lemma="lem2962")
retext(("2Ki", 3, 1)); plants.append("P3 A4 2Ki 3:1 @1 'the LORD said' on G2036, @2 G2962 empty")
# P4 A5 funcword: G3588 'the son', +1 empty G5207 noun (dodson: son) - in Rom 1:1, a changed-English verse (so C4 lists it, no C4 finding)
setw(("Rom", 1, 1), 1, strongs="3588", strongs_base="G3588", english="the son", english_head="son", lemma="lem3588")
setw(("Rom", 1, 1), 2, strongs="5207", strongs_base="G5207", english="", english_head="", morph="N-NSM", lemma="lem5207")
retext(("Rom", 1, 1)); plants.append("P4 A5 Rom 1:1 @1 G3588 'the son', @2 G5207 empty (N)")
# P5 A6 filler: G2316 rendered 'of'
setw(("2Ki", 4, 1), 1, strongs="2316", strongs_base="G2316", english="of", english_head="of", lemma="lem2316")
retext(("2Ki", 4, 1)); plants.append("P5 A6 2Ki 4:1 @1 G2316 'of'")
# P6 A7 split flip (+ cert check 2) and the C3 word-order hit: rows 'LORD the', text 'the LORD' (audit_split_flip control's shape)
for pos, (s, e) in enumerate([("2962", "LORD"), ("3588", "the"), ("1781", "will command"), ("846", "his"), ("1656", "mercy")], 1):
    setw(("2Ki", 5, 1), pos, strongs=s, strongs_base="G" + s, english=e, english_head=e, lemma="lem" + s)
t = retext(("2Ki", 5, 1))
assert t.startswith("LORD the ")
c.execute("UPDATE verses SET text=? WHERE id=?", ("the LORD " + t[len("LORD the "):], vid("2Ki", 5, 1)))
plants.append("P6 A7/C1 check 2/C3 word-order 2Ki 5:1 rows 'LORD the', text 'the LORD'")
# P7 A8 tier 1: three rows whose lemma is a different root from the lexicon's
for v in (1, 2, 3):
    setw(("2Ki", 6, v), 5, lemma="zzqqxx")
plants.append("P7 A8 2Ki 6:1-3 @5 G1005 lemma 'zzqqxx'")
# P8 A9 tier 2: one anchored Gen 1:2 slot renumbered (G1003 -> G2000)
setw(("Gen", 1, 2), 3, strongs="2000", strongs_base="G2000", lemma="lem2000"); plants.append("P8 A9 Gen 1:2 @3 G1003 -> G2000")
# P9 C1 a second red cert line: an active correction's cell no longer holds (Exo 1:1 @1)
setw(("Exo", 1, 1), 1, english="zzbroken", english_head="zzbroken"); retext(("Exo", 1, 1))
plants.append("P9 C1 check 4 Exo 1:1 @1 reads 'zzbroken'")
# P10 C3 a second content-other: an extra word in the text
c.execute("UPDATE verses SET text = text || ' zzz2' WHERE id=?", (vid("2Ki", 7, 1),)); plants.append("P10 C3 2Ki 7:1 text + 'zzz2'")
# P11 C4 a newly flagged phrase-gloss row OUTSIDE the changed-English verses; P12 the same INSIDE (Rom 1:2, listed only)
for ref in (("2Ki", 8, 1), ("Rom", 1, 2)):
    setw(ref, 1, strongs="3361", strongs_base="G3361", english="to not believe", english_head="believe", lemma="lem3361")
    setw(ref, 2, strongs="4100", strongs_base="G4100", english="", english_head="", lemma="lem4100")
    retext(ref)
plants.append("P11 C4 2Ki 8:1 G3361 'to not believe' + G4100 empty (outside); P12 Rom 1:2 the same (inside)")
# P13 C5 census: one row moved out of the 'same' verse Hab 3:1 into Jon 1:1 (words stays 626,309)
rid = c.execute("SELECT rowid FROM words WHERE verse_id=? ORDER BY position DESC LIMIT 1", (vid("Hab", 3, 1),)).fetchone()[0]
mx = c.execute("SELECT max(position) FROM words WHERE verse_id=?", (vid("Jon", 1, 1),)).fetchone()[0]
c.execute("UPDATE words SET verse_id=?, position=? WHERE rowid=?", (vid("Jon", 1, 1), mx + 1, rid))
retext(("Hab", 3, 1)); retext(("Jon", 1, 1)); plants.append("P13 C5 Hab 3:1 one row moved to Jon 1:1")
c.commit()
print("words %d" % c.execute("SELECT count(*) FROM words").fetchone()[0])
c.close()
# file-side plants: the 10/30 phrase-gloss log reads 663; the 10/30 census log a different figure; G2 verdict line gone;
# BSTD build.out without its PN-star line
(H / "edition_d_phrase_gloss.log").write_text("  FLAGGED BEYOND allowlist (gate <= 671):    663\n", encoding="utf-8")
p = H / "edition_a_count_differs.log"
p.write_text(p.read_text(encoding="utf-8").replace("COUNT-DIFFERS verses: 179 ", "COUNT-DIFFERS verses: 178 "), encoding="utf-8")
p = R / "step4_gate_r2_20261118.log"
p.write_text("".join(ln for ln in p.read_text(encoding="utf-8").splitlines(True) if not ln.startswith("G2: ")), encoding="utf-8")
(R / "step4_b_standard_20261117/build.out").write_text("(no PN-star line)\n", encoding="utf-8")
plants.append("F1 C4 the 10/30 BEYOND line reads 663; F2 C5 the 10/30 COUNT-DIFFERS line reads 178; F3 R no 'G2:' line; F4 R no PN-star line in build.out")
for p_ in plants:
    print("planted:", p_)
# the guard re-made on the planted built (eu_step pre + prep, as mkhome.sh)
g = R / "step4_headfix2_20261116"
subprocess.run(["rm", "-rf", str(g)], check=True)
ref = subprocess.check_output(["git", "-C", str(H / "bible-db"), "log", "-1", "--format=%h"], text=True).strip()
for args in (["pre", "--tag", "TESTPREP", "--ref", ref, "--dir", str(g), "--db", str(B)],
             ["prep", "--tag", "TESTPREP", "--built", str(B), "--dir", str(g), "--copy", "words,abp_corrections", "--save", "abp_corrections"]):
    out = subprocess.run(["python3", "scripts/eu_step.py"] + args, cwd=H / "bible-db", capture_output=True, text=True)
    print(out.stdout.strip().splitlines()[-1])
