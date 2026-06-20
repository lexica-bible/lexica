#!/usr/bin/env python3
"""
scan_strongs_leak.py — READ-ONLY. Never writes.

Finds ABP words whose ENGLISH gloss has a leaked Strong's marker stuck inside it
— the "AndG." artifact (Zec 9:11 σύ: english "AndG. you,", head "andg").

How the leak happens: the build splits each verse on Strong's markers (G#### /
G####.#) and clean_english() strips bare DIGITS from a gloss. If a Strong's number
ever ends up glued inside a gloss instead of between two words ("AndG2532 you,"),
the digits get stripped but the bare "G" (and its dot) survive — leaving "AndG.".

Fingerprint = a capital G sitting right after a lowercase letter ("...dG"), or a
"G" immediately followed by a digit (an un-stripped number). Real English glosses
never do that — "God", "Gentiles", "of God", "Gog" all start G on a word boundary,
so they don't match.

Read-only: just reports. Nothing is changed. PA-only (bible.db is on PA).

Usage:
  python3 scripts/scan_strongs_leak.py bible.db
"""
import re
import sqlite3
import sys

DB = next((a for a in sys.argv[1:] if not a.startswith("--")), "bible.db")

# capital G right after a lowercase letter and NOT continuing a word  ("AndG.", "AndG2532")
# OR a G immediately followed by a digit (a whole Strong's number that never got split off).
LEAK = re.compile(r"[a-z]G(?![a-z])|G\d")


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    # GLOB pre-filter (case-sensitive in SQLite) keeps the scan cheap; the regex below
    # is the real test. '*[a-z]G*' = a lowercase letter then capital G somewhere.
    rows = con.execute(
        """SELECT v.book, v.chapter, v.verse, w.position,
                  w.strongs, w.strongs_base, w.english, w.english_head
           FROM words w JOIN verses v ON v.id = w.verse_id
           WHERE w.english GLOB '*[a-z]G*' OR w.english GLOB '*G[0-9]*'
           ORDER BY w.verse_id, w.position"""
    ).fetchall()
    con.close()

    hits = [r for r in rows if r["english"] and LEAK.search(r["english"])]
    if not hits:
        print("No leaked-Strong's glosses found. Clean.")
        return
    print(f"{len(hits)} word(s) with a leaked Strong's marker in the gloss:\n")
    for r in hits:
        ref = f"{r['book']} {r['chapter']}:{r['verse']}"
        print(f"  {ref:<14} pos {r['position']:<3} {r['strongs_base'] or r['strongs']:<10} "
              f"english={r['english']!r}  head={r['english_head']!r}")
    print(f"\nTotal: {len(hits)}. (Read-only scan — nothing changed.)")


if __name__ == "__main__":
    main()
