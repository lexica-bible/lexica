#!/usr/bin/env python3
"""READ-ONLY audit of ABP dotted Strong's headwords.

For every dotted ABP number (e.g. 180.2) it compares:
  - what the word card shows now: the BASE lexicon lemma (via strongs_base,
    which the build made by chopping the ".2" off -> G180), against
  - the word's OWN ABP dictionary entry (abp_ext, keyed by the full dotted
    number), whose definition begins with the correct lemma.

Where they disagree (ignoring accent marks) the headword is wrong -- e.g.
G180.2 shows G180 ἀκατάπαυστος but should be ἀκατασκεύαστος.

The ABP dict stores Greek as HTML codes (&kappa;, &#x1F00;) inside <grk> tags,
with the morpheme hyphen sitting BETWEEN two <grk> spans, so the reader has to
drop tags, turn the codes back into letters, and join the hyphen first.

Touches nothing. On PA:  python scripts/audit_dotted_lemmas.py
"""
import html
import os
import re
import sqlite3
import sys
import unicodedata

DB = os.path.expanduser("~/bible-db/bible.db")

# Greek and Coptic (0x370-0x3ff) + Greek Extended (0x1f00-0x1fff), by code number
# so we never have to spell out tricky boundary letters or \u escapes.
def _is_greek(c: str) -> bool:
    o = ord(c)
    return 0x370 <= o <= 0x3ff or 0x1f00 <= o <= 0x1fff


def first_greek(def_html: str) -> str:
    """First Greek word of an abp_ext definition."""
    txt = re.sub(r"<[^>]+>", "", def_html or "")      # drop <grk>/<span>/<p> tags
    txt = html.unescape(txt)                           # &kappa; -> letter, &#x1F00; -> letter
    txt = txt.replace(chr(0xad), "").replace("-", "")  # join "akata-skeuastos"
    run, started = [], False
    for c in txt:
        if _is_greek(c):
            run.append(c)
            started = True
        elif started:
            break
    return "".join(run)


def clean_text(def_html: str) -> str:
    """Tags dropped + entities decoded, for eyeballing an entry's structure."""
    return html.unescape(re.sub(r"<[^>]+>", "", def_html or ""))


def bare(s: str) -> str:
    """Accent-, case-, and final-sigma-insensitive form, so the same word stored
    with different accent encoding doesn't read as a difference."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return s.replace("ς", "σ")


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    if len(sys.argv) > 1:                 # --show G#### ... : dump those entries
        for num in sys.argv[1:]:
            if num == "--show":
                continue
            row = conn.execute(
                "SELECT def_html FROM abp_ext WHERE trim(strongs)=? OR trim(strongs)=?",
                (num, "G" + num.lstrip("G")),
            ).fetchone()
            if not row:
                print(f"{num}: (no ABP dict entry)")
                continue
            print(f"{num}: lemma-guess={first_greek(row['def_html'])!r}")
            print("   " + clean_text(row["def_html"])[:160].replace(chr(10), " "))
        conn.close()
        return

    dotted = conn.execute(
        "SELECT strongs AS num, COUNT(*) AS uses FROM words "
        "WHERE strongs LIKE '%.%' GROUP BY strongs"
    ).fetchall()

    wrong, no_entry, unreadable, form_note = [], 0, 0, 0
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
        # True ABP form-notes keep the base lemma: the whole εἰμί family (base==G1510 —
        # not all carry a "Strong G####" pointer) plus anything else pointing to a real
        # Strong's via "Strong G####". A "[ABP]" entry that is a DIFFERENT word (σαβέκ vs
        # σάββατον) is none of those. (Matches build_dotted_lexicon.py / probe_dotted_abp.py.)
        if base == "G1510" or re.search(r"Strong\s+G\d", clean_text(ext["def_html"])):
            form_note += 1
            continue
        should = first_greek(ext["def_html"])
        if not should:
            unreadable += 1
            continue
        if bare(should) != bare(shown_lemma):
            wrong.append((num, shown_lemma, should, r["uses"]))

    conn.close()

    wrong.sort(key=lambda t: -t[3])
    print(f"dotted numbers: {len(dotted)}   "
          f"WRONG headword: {len(wrong)}   "
          f"ABP form notes (fine): {form_note}   "
          f"no ABP dict entry: {no_entry}   "
          f"couldn't read def: {unreadable}")
    print("dotted | shown now (base) | should be (ABP dict) | uses")
    for num, shown_lemma, should, uses in wrong:
        print(f"{num} | {shown_lemma} | {should} | {uses}")


if __name__ == "__main__":
    main()
