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
    cur = con.cursor()

    # Only touch rows whose gloss is blank or just punctuation (never overwrite real text):
    # after stripping spaces + the usual punctuation, nothing is left.
    BLANK = ("(english IS NULL OR "
             "trim(english, ' .,:;·') = '')")

    total = 0
    for code, digit in NUMERALS.items():
        n = cur.execute(
            f"SELECT COUNT(*) FROM words WHERE strongs = ? AND {BLANK}", (code,)
        ).fetchone()[0]
        print(f"{code} -> '{digit}': {n} blank word(s) to fill")
        total += n
        if args.apply:
            cur.execute(
                f"UPDATE words SET english = ? WHERE strongs = ? AND {BLANK}", (digit, code)
            )

    if args.apply:
        con.commit()
        print(f"\nApplied: filled {total} word(s).")
    else:
        print(f"\nDRY RUN: would fill {total} word(s). Re-run with --apply to write.")
    con.close()

if __name__ == "__main__":
    main()
