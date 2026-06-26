#!/usr/bin/env python3
"""
audit_pn_verb_merge.py — find proper nouns merged onto a following verb.

The Tamar bug (a name glued to the verb's cell, is_pn=0, carrying the verb's
number instead of its own) can hit ANY name wherever ABP floats the subject as a
bare "G*" after the verb. This READ-ONLY scan finds every such leak corpus-wide.

How it decides a row is a merge:
  1. Build the NAME set = every single-word proper-noun head (english_head of
     is_pn=1 rows that are one capitalized word, e.g. "Tamar", "David", "Judah").
  2. Flag a word when ALL hold:
       - is_pn = 0                         (not already a proper noun)
       - strongs_base is a real number     (G#### / H#### — the verb's, not '*')
       - english is two-or-more words      (name + verb glued)
       - its FIRST word is in the NAME set (a real name leads the cell)

It prints one line per flagged row (book ch:verse — english — number), grouped so
you can eyeball the list. Nothing is written. Some hits may be legitimate (a name
that doubles as a common word); we review the list before fixing anything.

  python3 scripts/audit_pn_verb_merge.py bible.db
"""
import argparse
import re
import sqlite3
import sys

def _first_word(eng):
    """First real word of a gloss, ignoring leading brackets/quotes/spaces."""
    if not eng:
        return None
    s = eng.lstrip("[(\"'“‘ \t")
    m = re.match(r"[A-Za-z][A-Za-z'\-]*", s)
    return m.group(0) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    # 1. NAME set — single-word capitalized proper-noun heads.
    names = set()
    for r in conn.execute(
        "SELECT DISTINCT english_head FROM words WHERE is_pn=1 AND english_head IS NOT NULL"
    ):
        h = (r["english_head"] or "").strip()
        if h and " " not in h and h[0].isupper() and h.isalpha():
            names.add(h)
    print(f"Known single-word names: {len(names):,}\n")

    # 2. Scan non-PN, real-numbered, multi-word cells whose first word is a name.
    rows = conn.execute(
        """SELECT v.book, v.chapter, v.verse, w.english, w.strongs_base
           FROM words w JOIN verses v ON v.id = w.verse_id
           WHERE w.is_pn = 0
             AND w.english LIKE '% %'
             AND w.strongs_base GLOB '[GH][0-9]*'
           ORDER BY v.id, w.position"""
    ).fetchall()

    hits = []
    for r in rows:
        fw = _first_word(r["english"])
        if fw and fw in names:
            hits.append((fw, r["book"], r["chapter"], r["verse"],
                         r["english"], r["strongs_base"]))

    print(f"Flagged {len(hits):,} merged-name candidate(s):\n")
    # Group by the leaked name, most frequent first.
    by_name = {}
    for fw, *rest in hits:
        by_name.setdefault(fw, []).append(rest)
    for fw in sorted(by_name, key=lambda n: (-len(by_name[n]), n)):
        items = by_name[fw]
        print(f"── {fw}  ({len(items)})")
        for book, ch, vs, eng, base in items:
            print(f"     {book} {ch}:{vs:<4} {base:<7} {eng!r}")
    print(f"\nTotal: {len(hits):,} candidates across {len(by_name):,} names.")
    conn.close()


if __name__ == "__main__":
    main()
