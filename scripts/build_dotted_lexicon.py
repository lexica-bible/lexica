#!/usr/bin/env python3
"""build_dotted_lexicon.py — corrected headword lemma + romanization for the ABP
dotted Strong's numbers that are a genuinely different word from their base.

Background: scripts/audit_dotted_lemmas.py shows ~3049 dotted numbers (e.g. 180.2
ἀκατασκεύαστος) whose card headword wrongly resolves to the BASE number's word
(G180 ἀκατάπαυστος) because strongs_base drops the ".N". The correct word is the
headword of the number's OWN abp_ext dictionary entry. This builds a side table,
`dotted_lexicon`, keyed by the full dotted number, so the card can later show the
right word. It touches NOTHING else: not words, not lexicon, and it skips the
[ABP] form-notes (1510.x = forms of εἰμί, where the base lemma is already right).

  python3 scripts/build_dotted_lexicon.py            # DRY RUN: print proposed rows, write nothing
  python3 scripts/build_dotted_lexicon.py --apply    # create + fill dotted_lexicon (that table only)

Reuses the verified Greek extraction from audit_dotted_lemmas.py and the romanizer
from build_abp_translit.py. Reads abp_ext/lexicon/words; writes ONLY dotted_lexicon.
"""
import os
import sqlite3
import sys

from audit_dotted_lemmas import bare, clean_text, first_greek
from build_abp_translit import romanize

DB = os.path.expanduser("~/bible-db/bible.db")


def collect(conn):
    rows = conn.execute(
        "SELECT strongs AS num, COUNT(*) AS uses FROM words "
        "WHERE strongs LIKE '%.%' GROUP BY strongs"
    ).fetchall()
    fixes = []
    skipped = {"form_note": 0, "no_entry": 0, "unreadable": 0, "already_ok": 0}
    for r in rows:
        num = r["num"]
        base = "G" + num.split(".")[0]
        shown = conn.execute(
            "SELECT lemma FROM lexicon WHERE strongs_g = ?", (base,)
        ).fetchone()
        shown_lemma = shown["lemma"] if shown else ""
        ext = conn.execute(
            "SELECT def_html FROM abp_ext WHERE trim(strongs)=? OR trim(strongs)=?",
            (num, "G" + num),
        ).fetchone()
        if not ext:
            skipped["no_entry"] += 1
            continue
        if clean_text(ext["def_html"]).lstrip().startswith("[ABP]"):
            skipped["form_note"] += 1            # form of the base lemma -> base is correct
            continue
        correct = first_greek(ext["def_html"])
        if not correct:
            skipped["unreadable"] += 1
            continue
        if bare(correct) == bare(shown_lemma):
            skipped["already_ok"] += 1           # LSJ entry that already matches the base
            continue
        fixes.append((num, shown_lemma, correct, romanize(correct, correct), r["uses"]))
    fixes.sort(key=lambda t: -t[4])
    return fixes, skipped


def main():
    do_apply = "--apply" in sys.argv
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    fixes, skipped = collect(conn)

    if not do_apply:
        print("dotted | shown now (base) | corrected lemma | romanization | uses")
        for num, shown, correct, tr, uses in fixes:
            print(f"{num} | {shown} | {correct} | {tr} | {uses}")
        print(f"\n[dry-run] {len(fixes)} corrections proposed; skipped {skipped}.")
        print("Nothing written. Re-run with --apply to fill the dotted_lexicon table.")
        conn.close()
        return

    conn.execute("DROP TABLE IF EXISTS dotted_lexicon")
    conn.execute(
        "CREATE TABLE dotted_lexicon (strongs TEXT PRIMARY KEY, lemma TEXT, translit TEXT)"
    )
    conn.executemany(
        "INSERT OR REPLACE INTO dotted_lexicon(strongs, lemma, translit) VALUES (?,?,?)",
        [("G" + num, correct, tr) for num, _shown, correct, tr, _uses in fixes],
    )
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM dotted_lexicon").fetchone()[0]
    conn.close()
    print(f"Filled dotted_lexicon with {n} corrected headwords (that table only; "
          f"nothing else touched).")


if __name__ == "__main__":
    main()
