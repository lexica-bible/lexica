#!/usr/bin/env python3
"""READ-ONLY audit of ABP dotted Strong's headwords.

For every dotted ABP number (e.g. 180.2) it compares:
  - what the word card shows now: the BASE lexicon lemma (via strongs_base,
    which the build made by chopping the ".2" off -> G180), against
  - the word's OWN ABP dictionary entry (abp_ext, keyed by the full dotted
    number), whose definition begins with the correct lemma.

Where they disagree (ignoring accent marks) the headword is wrong -- e.g.
G180.2 shows G180 ἀκατάπαυστος but should be ἀκατασκεύαστος.

Touches nothing. On PA:  python scripts/audit_dotted_lemmas.py
"""
import os
import re
import sqlite3
import unicodedata

DB = os.path.expanduser("~/bible-db/bible.db")

_GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]+")


def first_greek(html: str) -> str:
    """First Greek word of an abp_ext definition (drop tags + morpheme hyphens)."""
    txt = re.sub(r"<[^>]+>", " ", html or "")
    txt = txt.replace("­", "").replace("-", "")      # join "ἀκατα-σκεύαστος"
    m = _GREEK.search(txt)
    return m.group(0) if m else ""


def bare(s: str) -> str:
    """Accent- and case-insensitive form, so the same word stored with different
    accent encoding doesn't read as a difference."""
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    dotted = conn.execute(
        "SELECT strongs AS num, COUNT(*) AS uses FROM words "
        "WHERE strongs LIKE '%.%' GROUP BY strongs"
    ).fetchall()

    wrong, no_entry = [], 0
    for r in dotted:
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
            no_entry += 1
            continue
        should = first_greek(ext["def_html"])
        if should and bare(should) != bare(shown_lemma):
            wrong.append((num, shown_lemma, should, r["uses"]))

    conn.close()

    wrong.sort(key=lambda t: -t[3])
    print(f"dotted numbers: {len(dotted)}   "
          f"WRONG headword: {len(wrong)}   "
          f"no ABP dict entry: {no_entry}")
    print("dotted | shown now (base) | should be (ABP dict) | uses")
    for num, shown_lemma, should, uses in wrong:
        print(f"{num} | {shown_lemma} | {should} | {uses}")


if __name__ == "__main__":
    main()
