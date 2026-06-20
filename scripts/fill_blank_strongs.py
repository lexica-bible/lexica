#!/usr/bin/env python3
"""
fill_blank_strongs.py — fill the 5 ABP words that have a BLANK Strong's number.

ABP's source writes a numberless "G." (a 'G' with no digits) for a handful of words — the
Strong's number was simply never assigned there. Because "G." isn't a real tag, the build
glued that word's English onto the NEXT real number, corrupting both (e.g. "bidding" landed
on the article G3588 in Act 24:8). These are ALL 5 such spots in the whole ABP source
(grep-verified — there are no others):

  Zec 9:11   split "And you,"          -> "And"      G2532 (καί)     + "you,"      (G4771)
  1Pe 3:13   split "And who is"        -> "And"      G2532 (καί)     + "who is"    (G5100)
  Heb 7:4    split "And view how great"-> "And view" G2334 (θεωρέω)  + "how great" (G4080)
  Mat 12:14  split "And the Pharisees" -> "And the"  G3588 (article) + "Pharisees" (G*)
  Act 24:8   number swap only "bidding"-> G2753 (κελεύσας); the glossless article it merged
                                          onto had no English of its own, so nothing splits.

Numbers confirmed against BibleHub's tagged ABP. (BibleHub's stray 3739 on Mat 12:14 is a bad
tag — "the"/οἱ is the article G3588, not the relative pronoun G3739.) The "And" rides in the
gloss on Heb 7:4 / Mat 12:14 exactly as ABP groups it (δέ folded in), not split into its own word.

Read-only by default; pass --apply to write. PA-only (bible.db is on PA). The four split verses
gain one word, so their later words shift by one slot — re-run build_abp_surface.py and
build_abp_translit.py afterwards so the "in this verse" line stays aligned.

ONE-TIME use on the live db. The same fill is folded into build_words_from_abp.py
(apply_blank_strongs_fills, called at the end of the build), so a future rebuild reproduces it
on its own — you do NOT need to re-run this after a rebuild.
"""
import argparse
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_abp import _head_word  # the exact head logic the build uses

# Peel a leaked "G." marker so the guard can match the clean gloss whether or not the
# live data still carries the raw "AndG." text.
_LEAK = re.compile(r"(?<=[a-z])G\.(?=\s|$)")


def _peel(text):
    if not text or "G." not in text:
        return text
    return re.sub(r"\s{2,}", " ", _LEAK.sub("", text)).strip()


# The 5 fixes. "split" = the blank word merged onto the next real word; carve it back out.
# "number" = the blank word's gloss is the survivor's whole gloss; just give it the right number.
FILLS = [
    {"ref": ("Zec", 9, 11),  "kind": "split",  "left": "And",       "base": "G2532", "right": "you,"},
    {"ref": ("1Pe", 3, 13),  "kind": "split",  "left": "And",       "base": "G2532", "right": "who is"},
    {"ref": ("Heb", 7, 4),   "kind": "split",  "left": "And view",  "base": "G2334", "right": "how great"},
    {"ref": ("Mat", 12, 14), "kind": "split",  "left": "And the",   "base": "G3588", "right": "Pharisees"},
    {"ref": ("Act", 24, 8),  "kind": "number", "gloss": "bidding",  "base": "G2753"},
]

# Columns the build inserts; is_pn is set later by import_tipnr (none of these are proper nouns).
_INSERT = ("INSERT INTO words (verse_id, position, english, english_head, strongs, strongs_base,"
           " greek_pos, bracket_id, italic, italic_words, smcap_words, morph, lemma)"
           " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")


def _new_word_row(vid, position, gloss, base):
    bare = base[1:] if base[:1] in ("G", "H") else base
    return (vid, position, gloss, _head_word(gloss), bare, base,
            None, None, 0, "", "", None, None)


def apply_blank_strongs_fills(conn, apply=False, log=print):
    """Apply the 5 blank-Strong's fills to an open bible.db connection. Read-only unless
    apply=True. Guarded: each fix only fires when the word still looks merged, so it is
    safe to run again (already-fixed rows are skipped). Returns the number changed."""
    changed = 0
    for f in FILLS:
        book, ch, vs = f["ref"]
        ref = f"{book} {ch}:{vs}"
        row = conn.execute(
            "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?", (book, ch, vs)
        ).fetchone()
        if not row:
            log(f"  {ref}: verse not found — skipped")
            continue
        vid = row[0]
        w = conn.execute(
            "SELECT english, strongs_base FROM words WHERE verse_id=? AND position=0", (vid,)
        ).fetchone()
        if not w:
            log(f"  {ref}: no word at slot 0 — skipped")
            continue
        cur_eng, cur_base = w[0], w[1]
        peeled = _peel(cur_eng)

        if f["kind"] == "split":
            want = f"{f['left']} {f['right']}"
            if peeled != want:
                log(f"  {ref}: slot 0 is {cur_eng!r} (expected {want!r}) — skipped (already fixed?)")
                continue
            log(f"  {ref}: {cur_eng!r}  ->  {f['left']!r} ({f['base']}) + {f['right']!r} ({cur_base})")
            if apply:
                # collision-safe shift of every word in the verse by +1, then carve slot 0
                conn.execute("UPDATE words SET position = position + 1000000 WHERE verse_id=?", (vid,))
                conn.execute("UPDATE words SET position = position - 1000000 + 1 WHERE verse_id=?", (vid,))
                conn.execute(
                    "UPDATE words SET english=?, english_head=? WHERE verse_id=? AND position=1",
                    (f["right"], _head_word(f["right"]), vid),
                )
                conn.execute(_INSERT, _new_word_row(vid, 0, f["left"], f["base"]))
            changed += 1
        else:  # number-only
            if cur_base == f["base"]:
                log(f"  {ref}: slot 0 already {f['base']} — skipped (already fixed)")
                continue
            if peeled != f["gloss"]:
                log(f"  {ref}: slot 0 is {cur_eng!r} (expected {f['gloss']!r}) — skipped")
                continue
            log(f"  {ref}: {cur_eng!r}/{cur_base}  ->  {f['gloss']!r}/{f['base']}")
            if apply:
                bare = f["base"][1:]
                conn.execute(
                    "UPDATE words SET english=?, english_head=?, strongs=?, strongs_base=?"
                    " WHERE verse_id=? AND position=0",
                    (f["gloss"], _head_word(f["gloss"]), bare, f["base"], vid),
                )
            changed += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write changes (default = dry run)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    n = apply_blank_strongs_fills(con, apply=args.apply, log=print)
    if args.apply:
        con.commit()
        print(f"\nApplied: filled {n} word(s). Now re-run build_abp_surface.py + build_abp_translit.py.")
    else:
        print(f"\nDRY RUN: would fill {n} word(s). Re-run with --apply to write.")
    con.close()


if __name__ == "__main__":
    main()
