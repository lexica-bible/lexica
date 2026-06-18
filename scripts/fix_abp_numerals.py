#!/usr/bin/env python3
"""Fill the English gloss for ABP's Greek-numeral words.

ABP spells some numbers as Greek numeral LETTERS (e.g. 666 = χ ξ ϛ in Rev 13:18),
tagging each letter with a fixed dotted Strong's code. The English gloss (the digit
itself) came across BLANK in the words table, so the reader drops those words and the
number disappears from the end of the verse.

These dotted codes mean the same numeral everywhere they occur, so we fill the gloss
by code. Read-only by default; pass --apply to write. PA-only (bible.db is on PA).

ONE-TIME use: this only patches the CURRENT live database. The real fix is folded into
build_words_from_abp.py (`_numeral_gloss_fill`), so a future words rebuild produces the
numbers on its own — you do NOT need to re-run this after a rebuild. (Twin of the
patch-fold pattern: the fold is the source of truth; this patched the live data once.)
"""
import argparse, sqlite3, sys

# ABP dotted Strong's -> the number it spells.
NUMERALS = {
    "5462.1": "600",   # χ
    "3577.2": "60",    # ξ
    "2193.2": "6",     # ϛ  (note: gloss in the data is "." today)
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write changes (default = dry run)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    total = 0
    for code, digit in NUMERALS.items():
        rows = cur.execute(
            "SELECT rowid, english FROM words WHERE strongs = ?", (code,)
        ).fetchall()
        # Only touch rows whose gloss is blank or just punctuation (never overwrite real text).
        targets = [r for r in rows if not (r["english"] or "").strip(" .,:;·")]
        print(f"{code} -> '{digit}': {len(rows)} word(s) tagged, {len(targets)} blank to fill")
        total += len(targets)
        if args.apply:
            for r in targets:
                cur.execute("UPDATE words SET english = ? WHERE rowid = ?", (digit, r["rowid"]))

    if args.apply:
        con.commit()
        print(f"\nApplied: filled {total} word(s).")
    else:
        print(f"\nDRY RUN: would fill {total} word(s). Re-run with --apply to write.")
    con.close()

if __name__ == "__main__":
    main()
