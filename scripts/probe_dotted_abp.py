#!/usr/bin/env python3
"""READ-ONLY probe: which ABP dotted numbers whose abp_ext entry begins with "[ABP]"
are a genuinely DIFFERENT word from their base, vs a grammatical FORM of the base.

  - DIFFERENT word: G4521.2 [ABP] sabek "thicket" Gen 22:13   (base G4521 sabbaton)
    -> the card SHOULD show the dotted word; today it wrongly shows the base.
  - FORM of base : the eimi/estin class ([ABP] note -> Strong G####)
    -> the base lemma is the right headword; leave alone.

build_dotted_lexicon.py + audit_dotted_lemmas.py currently SKIP the whole "[ABP]"
class as form-notes, so the DIFFERENT-word ones (the bug the user spotted) never get
their own row. This lists the ambiguous set + two cheap signals so we can pick a clean
discriminator before changing the build. Touches nothing.

On PA:  python scripts/probe_dotted_abp.py
"""
import os
import re
import sqlite3

from audit_dotted_lemmas import bare, clean_text, first_greek

DB = os.path.expanduser("~/bible-db/bible.db")
G_PTR = re.compile(r"\bG\d{2,5}\b")               # a Strong's-number pointer ("Strong G2076")
VERSE_REF = re.compile(r"[A-Z][a-z]{2}[_ ]\d+:\d+")  # a verse cite ("Gen_22:13")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT strongs AS num, COUNT(*) AS uses FROM words "
        "WHERE strongs LIKE '%.%' GROUP BY strongs"
    ).fetchall()

    abp_total = 0
    diff = []
    for r in rows:
        num = r["num"]
        base = "G" + num.split(".")[0]
        shown = conn.execute(
            "SELECT lemma FROM lexicon WHERE strongs_g = ?", (base,)
        ).fetchone()
        base_lemma = shown["lemma"] if shown else ""
        ext = conn.execute(
            "SELECT def_html FROM abp_ext WHERE trim(strongs)=? OR trim(strongs)=?",
            (num, "G" + num),
        ).fetchone()
        if not ext:
            continue
        txt = clean_text(ext["def_html"])
        if not txt.lstrip().startswith("[ABP]"):
            continue                              # only the class the build skips
        abp_total += 1
        fg = first_greek(ext["def_html"])
        if not fg:
            continue                              # no readable Greek -> base stays
        if bare(fg) == bare(base_lemma):
            continue                              # echoes the base -> base already right
        diff.append((
            num, base_lemma, fg,
            bool(G_PTR.search(txt)),              # points to another Strong's -> a FORM
            bool(VERSE_REF.search(txt)),          # cites a verse -> looks like a NEW word
            r["uses"],
            " ".join(txt.split())[:120],
        ))

    conn.close()
    # no-G-pointer first (the likely new-words), then by frequency
    diff.sort(key=lambda t: (t[3], -t[5]))
    print(f'"[ABP]" dotted entries total: {abp_total}')
    print(f'  of those, first-Greek DIFFERS from the base lemma: {len(diff)}')
    print(f'  ... with NO Strong\'s pointer (likely NEW words): '
          f'{sum(1 for d in diff if not d[3])}')
    print(f'  ... WITH a Strong\'s pointer (likely FORMS):       '
          f'{sum(1 for d in diff if d[3])}\n')
    print("num | base lemma | first_greek | hasG? | hasVerse? | uses | text")
    for num, bl, fg, hasg, hasv, uses, txt in diff:
        print(f"{num} | {bl} | {fg} | {'G' if hasg else '-'} | "
              f"{'V' if hasv else '-'} | {uses} | {txt}")


if __name__ == "__main__":
    main()
