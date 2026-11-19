# STEP6AUD tests: made-up stand-ins for the PA-only reference feeds (same bytes every run).
# argv: 1 folder that gets LXX-Rahlfs-1935/ + TAGNT_Mat-Jhn.txt + TAGNT_Act-Rev.txt  2 path of bh_scrape.db to write
# Formats from the loaders: lxx_align.py RahlfsLXX (:150-230, tab files, verse starts in 12-Marvel.Bible/...),
# TAGNTSource (:328-380, 'Mat.1.1#01=...' rows, field 4 'G####=MORPH', field 5 lemma); bh_words (build_words_from_abp :334-352).
import os, sqlite3, sys
from pathlib import Path

H, BH = Path(sys.argv[1]), Path(sys.argv[2])
R = H / "LXX-Rahlfs-1935"
for d in ("07_StrongNumber", "03a_morphology_with_JTauber_patches", "02_lexemes", "12-Marvel.Bible"):
    (R / d).mkdir(parents=True, exist_ok=True)
# Gen 1:1 = 21 tokens G1001..G1021 (the test copies' Gen 1:1 rows), Gen 1:2 = 20 tokens G1001..G1020; then a closing entry
toks = [("1.1.1", list(range(1001, 1022))), ("1.1.2", list(range(1001, 1021))), ("1.1.3", [1001])]
st, mo, lx, vr = [], [], [], []
i = 1
for ref, ss in toks:
    vr.append("%d\t%s" % (i, ref))
    for s in ss:
        st.append("%d\t%d" % (i, s))
        mo.append("%d\tV.PAI3S" % i)
        lx.append("%d\tlem%d" % (i, s))
        i += 1
for rel, lines in (("07_StrongNumber/final_Strongs.csv", st), ("03a_morphology_with_JTauber_patches/patched_623693.csv", mo),
                   ("02_lexemes/OSSP_lexemes.csv", lx), ("12-Marvel.Bible/00-versification_original.csv", vr)):
    (R / rel).write_text("\n".join(lines) + "\n", encoding="utf-8")
for name, book in (("TAGNT_Mat-Jhn.txt", "Mat"), ("TAGNT_Act-Rev.txt", "Act")):
    rows = ["# made-up TAGNT stand-in for the STEP6AUD tests"]
    for v in (1, 2):
        for k, s in enumerate(range(1001, 1021), 1):
            rows.append("%s.1.%d#%02d=NKO\tword (word) word\tword\tG%d=V-PAI-3S\tlem%d=word" % (book, v, k, s, s))
    (H / name).write_text("\n".join(rows) + "\n", encoding="utf-8")
if BH.exists():
    BH.unlink()
c = sqlite3.connect(BH)
c.execute("CREATE TABLE bh_words(book TEXT, chapter INT, verse INT, position INT, strongs TEXT, english TEXT, "
          "italic_words TEXT, smcap_words TEXT, greek_pos INT)")
c.execute("INSERT INTO bh_words VALUES ('genesis', 1, 1, 1, '1722', 'In', '', '', 1)")
c.commit()
c.close()
os.utime(BH, (1767225600, 1767225600))          # a fixed time, so the file's bytes and age are the same every build
print("feeds written:", R, H / "TAGNT_Mat-Jhn.txt", H / "TAGNT_Act-Rev.txt", BH)
