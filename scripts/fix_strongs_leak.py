#!/usr/bin/env python3
"""
fix_strongs_leak.py — clean leaked Strong's markers out of ABP glosses.

Targets the "AndG." artifact: the ABP/BibleHub source sometimes renders a word with its
Strong's link mashed onto the English ("AndG. you," for σύ in Zec 9:11; "biddingG." in
Act 24:8). The build's digit-strip removed the number but left a bare "G." in the gloss.
This peels the "G." marker and recomputes english_head the same way the build does.

5 spots canon-wide as of the 2026-06-20 scan: Zec 9:11, 1Pe 3:13, Act 24:8, Heb 7:4, Mat 12:14.

Read-only by default; pass --apply to write. PA-only (bible.db is on PA). Touches ONLY
english + english_head on the matched rows — no positions, Strong's, or brackets move, so
nothing downstream (abp_surface / translit / two-ending / dotted) needs rebuilding.

ONE-TIME use: this patches the CURRENT live database. The same peel is folded into
build_words_from_abp.py (strip_leaked_marker), so a future rebuild produces clean glosses
on its own — you do NOT need to re-run this after a rebuild. (Patch-fold pattern: the fold
is the source of truth; this fixes the live data once.)
"""
import argparse
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_abp import _head_word  # the exact head logic the build uses

# Mirror of build_words_from_abp.strip_leaked_marker (kept in sync deliberately).
_LEAK_MARK = re.compile(r"(?<=[a-z])G\.(?=\s|$)")


def _strip(text):
    if not text or "G." not in text:
        return text
    return re.sub(r"\s{2,}", " ", _LEAK_MARK.sub("", text)).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write changes (default = dry run)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    # Broad pre-filter (any "G." run); _strip is the precise test — only a capital G + dot
    # right after a lowercase letter actually changes, so false matches fall out below.
    rows = con.execute(
        """SELECT v.book, v.chapter, v.verse, w.verse_id, w.position,
                  w.strongs_base, w.english, w.english_head
           FROM words w JOIN verses v ON v.id = w.verse_id
           WHERE w.english LIKE '%G.%'
           ORDER BY w.verse_id, w.position"""
    ).fetchall()

    changes = []
    for r in rows:
        new_eng = _strip(r["english"])
        if new_eng == r["english"]:
            continue
        new_head = _head_word(new_eng) if new_eng else None
        changes.append((r, new_eng, new_head))

    if not changes:
        print("No leaked markers to clean. (Nothing matched.)")
        con.close()
        return

    print(f"{len(changes)} gloss(es) to clean:\n")
    for r, new_eng, new_head in changes:
        ref = f"{r['book']} {r['chapter']}:{r['verse']}"
        print(f"  {ref:<14} {r['strongs_base']:<8}")
        print(f"      english : {r['english']!r}  ->  {new_eng!r}")
        print(f"      head    : {r['english_head']!r}  ->  {new_head!r}")

    if args.apply:
        cur = con.cursor()
        for r, new_eng, new_head in changes:
            cur.execute(
                "UPDATE words SET english = ?, english_head = ? WHERE verse_id = ? AND position = ?",
                (new_eng, new_head, r["verse_id"], r["position"]),
            )
        con.commit()
        print(f"\nApplied: cleaned {len(changes)} gloss(es).")
    else:
        print(f"\nDRY RUN: would clean {len(changes)} gloss(es). Re-run with --apply to write.")
    con.close()


if __name__ == "__main__":
    main()
