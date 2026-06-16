#!/usr/bin/env python3
"""
Find two-ending Greek adjectives whose morph source never resolves their gender,
and emit the soften-lists the reader uses to show "Masculine/Feminine".

Greek two-ending adjectives (e.g. ἀόρατος, ον) share ONE form for masculine and
feminine; only the neuter differs. The OT (CATSS) and NT (Robinson) morph sources
often just default such a word to Masculine instead of resolving it by agreement
with its noun — so on the word-study card it can read "Masculine" next to a clearly
feminine noun (γῆ ἀόρατος, Gen 1:2).

Rule (per testament, per word):
  - if the source EVER tags the word Feminine, it has shown it can tell the gender
    apart -> trust all its tags, leave the word alone.
  - if it NEVER tags the word Feminine, its Masculine is just a default -> soften
    that word's Masculine displays to "Masculine/Feminine".
Feminine and Neuter tags are always trusted (neuter form is distinct).

The two-ending signal is the LSJ headword: three-ending lists a feminine ending
then a neuter (ἀγαθός -> ή, όν); two-ending lists only the neuter (ἀγαθοποιός -> όν;
ἀγαθοειδής -> ές); nouns lead with an article (ὁ / ἡ / τό).

READ-ONLY — opens bible.db read-only, never writes it. bible.db is PA-only, so run
this there and paste the printed JS block into static/src/00b-two-ending.jsx.
Re-run after any words rebuild (positions/genders can shift).

    python3 scripts/build_two_ending.py [path/to/bible.db]
"""
import collections
import os
import re
import sqlite3
import sys
import unicodedata

DB = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/bible-db/bible.db")


def norm(s):
    """Accent-strip, lowercase, drop hyphens/apostrophes, fold final sigma."""
    s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                if unicodedata.category(c) != "Mn").lower()
    return s.replace("ς", "σ").replace("-", "").replace("’", "").replace("'", "")


ARTICLES = {"ὁ", "ἡ", "τό", "τὸ", "οἱ", "αἱ", "τά", "τὰ", "ὃ", "ἣ"}
NEUT = {"ον", "ουν", "εσ"}          # two-ending neuter endings (normalized)
FEM = {"η", "α", "εια"}             # three-ending feminine endings (normalized)


def classify(def_html):
    """Read the LSJ headword endings -> 'two-ending' / 'three-ending' / 'noun'."""
    if not def_html:
        return "no-def"
    m = re.search(r"</b>(.*)$", def_html, re.S)
    for t in re.findall(r"<i>(.*?)</i>", m.group(1) if m else def_html):
        t = t.strip()
        if not t or "[" in t:           # skip quantity markers like [ᾰ]
            continue
        if t in ARTICLES:
            return "noun"
        s = norm(t.lstrip("-"))
        if s in NEUT:
            return "two-ending"
        if s in FEM:
            return "three-ending"
    return "unknown"


def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # Index LSJ once by normalized headword (fixes hyphen + final-sigma mismatches).
    lsj = {}
    for row in conn.execute("SELECT plain, key, def_html FROM lsj WHERE key NOT LIKE '-%'"):
        k = norm(row["plain"] or row["key"])
        if k:
            lsj.setdefault(k, row["def_html"])

    # Adjective occurrences per Strong's, split OT/NT with Masc/Fem tallies.
    rows = conn.execute("""
      SELECT strongs_base AS sb,
        sum(morph LIKE 'A.%') AS ot,  sum(morph LIKE 'A-%') AS nt,
        sum(morph LIKE 'A.%' AND substr(morph,instr(morph,'.')+3,1)='M') AS otM,
        sum(morph LIKE 'A-%' AND substr(morph,instr(morph,'-')+3,1)='M') AS ntM,
        sum(morph LIKE 'A.%' AND substr(morph,instr(morph,'.')+3,1)='F') AS otF,
        sum(morph LIKE 'A-%' AND substr(morph,instr(morph,'-')+3,1)='F') AS ntF
      FROM words
      WHERE (morph LIKE 'A.%' OR morph LIKE 'A-%') AND strongs_base GLOB 'G*'
      GROUP BY strongs_base
    """).fetchall()

    def lemma_for(sb):
        r = conn.execute("SELECT lemma FROM lexicon WHERE strongs_g=?", (sb,)).fetchone()
        return r["lemma"] if r else None

    cls_lem = collections.Counter()
    soft_ot, soft_nt = [], []          # (sb, lemma, masc-occurrences-softened)
    for r in rows:
        lemma = lemma_for(r["sb"])
        dh = lsj.get(norm(lemma)) if lemma else None
        c = classify(dh) if dh is not None else ("no-lexicon" if not lemma else "no-lsj")
        cls_lem[c] += 1
        if c != "two-ending":
            continue
        if (r["otM"] or 0) > 0 and (r["otF"] or 0) == 0:
            soft_ot.append((r["sb"], lemma, r["otM"]))
        if (r["ntM"] or 0) > 0 and (r["ntF"] or 0) == 0:
            soft_nt.append((r["sb"], lemma, r["ntM"]))
    conn.close()

    gnum = lambda sb: int(re.sub(r"\D", "", sb) or 0)
    soft_ot.sort(key=lambda x: gnum(x[0]))
    soft_nt.sort(key=lambda x: gnum(x[0]))

    def emit(name, items):
        nums = [f'"{sb}"' for sb, _, _ in items]
        print(f"const {name} = new Set([")
        for i in range(0, len(nums), 12):
            print("  " + ",".join(nums[i:i + 12]) + ",")
        print("]);")

    print("// classes (lemmas):", dict(cls_lem))
    print(f"// soften OT: {len(soft_ot)} words / {sum(x[2] for x in soft_ot)} displays   "
          f"NT: {len(soft_nt)} words / {sum(x[2] for x in soft_nt)} displays")
    print("// ---------- paste everything below into static/src/00b-two-ending.jsx ----------")
    print("// AUTO-GENERATED by scripts/build_two_ending.py — do not hand-edit.")
    print("// Two-ending adjectives whose morph source never tags them Feminine, so their")
    print('// "Masculine" reads as "Masculine/Feminine" (see decodeMorph in 00-core.jsx).')
    print("// Regenerate on PythonAnywhere after a words rebuild; paste the output here.")
    emit("TWO_END_SOFT_OT", soft_ot)
    emit("TWO_END_SOFT_NT", soft_nt)


if __name__ == "__main__":
    main()
