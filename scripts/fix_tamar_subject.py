#!/usr/bin/env python3
"""
fix_tamar_subject.py — split the proper noun "Tamar" back off the verb it was
merged onto, so it carries its own Hebrew proper-noun number (H8559) again.

ABP floats the subject name as a trailing numberless "G*" after the verb's gloss
block (e.g. "Tamar boreG5088 G*"). At build time the name got swallowed into the
verb's English cell, so it lost its own slot — import_tipnr never saw a "*" word to
resolve, and "Tamar" inherited the verb's Greek number with is_pn=0.

All 6 such spots in the corpus (found by sweeping every "Tamar" word and keeping the
ones still glued to a verb / is_pn=0). The other ~20 Tamar words are already correct
(strongs_base=H8559, is_pn=1) and are left untouched:

  Gen 38:26   "Tamar has done justice"  G1344  ->  "Tamar" H8559 + "has done justice" G1344
  Rth 4:12    "Tamar bore"              G5088  ->  "Tamar" H8559 + "bore"              G5088
  2Sa 13:8    "Tamar went"              G4198  ->  "Tamar" H8559 + "went"              G4198
  2Sa 13:10   "Tamar took"              G2983  ->  "Tamar" H8559 + "took"              G2983
  2Sa 13:19   "Tamar took"              G2983  ->  "Tamar" H8559 + "took"              G2983
  2Sa 13:20   "Tamar sat"               G2523  ->  "Tamar" H8559 + "sat"               G2523

H8559 (not the Greek G2283) to match every other Tamar in the DB — the app tags OT
proper nouns with their Hebrew number, and the name lookup expects an H-number.
Name reads first in every case (matches the source word order and the current
display), so the new name word goes at the merged slot's position and the verb
shifts one slot later. The verb keeps its own number/gloss/morph unchanged.

Read-only by default; pass --apply to write. PA-only (bible.db lives on PA). Each
fix only fires when the slot still looks merged ("Tamar <verb>" with is_pn=0), so
re-running is safe — already-split rows are skipped.

Each split adds one word to its verse, so later words there shift by one slot.
Re-run build_abp_surface.py + build_abp_translit.py afterwards so the "in this
verse" Greek line stays aligned.

  python3 scripts/fix_tamar_subject.py bible.db            # dry run (default)
  python3 scripts/fix_tamar_subject.py bible.db --apply    # write changes
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_abp import _head_word  # the exact head logic the build uses

NAME = "Tamar"
NAME_BASE = "H8559"     # strongs_base for the new name word
NAME_STRONGS = "*"      # bare strongs column — matches the clean Tamar siblings

# (book, chapter, verse, merged_english) — merged_english is the exact current cell
# text, name + verb glued. The verb gloss is everything after "Tamar ".
FIXES = [
    ("Gen", 38, 26, "Tamar has done justice"),
    ("Rth", 4,  12, "Tamar bore"),
    ("2Sa", 13, 8,  "Tamar went"),
    ("2Sa", 13, 10, "Tamar took"),
    ("2Sa", 13, 19, "Tamar took"),
    ("2Sa", 13, 20, "Tamar sat"),
]

# Columns the build inserts, plus is_pn (the name IS a proper noun).
_INSERT = ("INSERT INTO words (verse_id, position, english, english_head, strongs, strongs_base,"
           " greek_pos, bracket_id, italic, italic_words, smcap_words, morph, lemma, is_pn)"
           " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")


def _name_row(vid, position):
    # greek_pos/bracket_id/morph/lemma None, italic 0 — a fresh proper-noun slot,
    # exactly how the build emits an unresolved name before import_tipnr runs.
    return (vid, position, NAME, _head_word(NAME), NAME_STRONGS, NAME_BASE,
            None, None, 0, "", "", None, None, 1)


def apply_tamar_fixes(conn, apply=False, log=print):
    changed = 0
    for book, ch, vs, merged in FIXES:
        ref = f"{book} {ch}:{vs}"
        vrow = conn.execute(
            "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?", (book, ch, vs)
        ).fetchone()
        if not vrow:
            log(f"  {ref}: verse not found — skipped")
            continue
        vid = vrow[0]

        # Find the still-merged slot: exact text, glued to a verb (is_pn=0).
        w = conn.execute(
            "SELECT position, strongs, strongs_base FROM words"
            " WHERE verse_id=? AND english=? AND is_pn=0",
            (vid, merged),
        ).fetchone()
        if not w:
            log(f"  {ref}: no merged {merged!r} slot (already split?) — skipped")
            continue
        pos, vstrongs, vbase = w[0], w[1], w[2]
        verb = merged[len(NAME) + 1:]  # drop "Tamar "

        log(f"  {ref}: {merged!r} ({vbase})  ->  "
            f"{NAME!r} ({NAME_BASE}, is_pn=1) + {verb!r} ({vbase})")

        if apply:
            # Open a one-slot gap at `pos` without tripping any (verse_id,position)
            # uniqueness: bump everything from `pos` up by a big offset, then bring
            # it back +1. The merged verb cell lands at pos+1; pos is now free.
            conn.execute(
                "UPDATE words SET position = position + 1000000 WHERE verse_id=? AND position >= ?",
                (vid, pos),
            )
            conn.execute(
                "UPDATE words SET position = position - 999999 WHERE verse_id=? AND position >= 1000000",
                (vid,),
            )
            # The verb cell is now the lone row at pos+1: trim it to just the verb.
            conn.execute(
                "UPDATE words SET english=?, english_head=? WHERE verse_id=? AND position=?",
                (verb, _head_word(verb), vid, pos + 1),
            )
            # Drop the name into the freed slot.
            conn.execute(_INSERT, _name_row(vid, pos))
        changed += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write changes (default = dry run)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    n = apply_tamar_fixes(con, apply=args.apply, log=print)
    if args.apply:
        con.commit()
        print(f"\nApplied: split {n} Tamar slot(s). "
              f"Now re-run build_abp_surface.py + build_abp_translit.py.")
    else:
        print(f"\nDRY RUN: would split {n} Tamar slot(s). Re-run with --apply to write.")
    con.close()


if __name__ == "__main__":
    main()
