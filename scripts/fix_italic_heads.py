#!/usr/bin/env python3
"""fix_italic_heads.py — make a word's SEARCH LABEL (words.english_head) its own
rendering, never a translator-ADDED (italic) word.

ABP bundles an added clarifying word into a slot's gloss and marks it italic (no
Greek behind it). The label-picker took the LAST real word, so an added word at the
end became the label: "take favor" (favor italic) labeled λαμβάνω/G2983 as "favor",
which made λαμβάνω surface in the Word-study finder under a search for "favor".

This recomputes english_head with the SAME rule the build now uses
(parse_abp._head_word, skipping italics; falls back to the plain pick when every
content word is added, so bare article slots are left exactly as they are). Touches
words.english_head ONLY — never strongs / strongs_base / italic / english. Fully
re-runnable: a row already on its own word won't change, so a second run reports 0.

  python scripts/fix_italic_heads.py                 # DRY RUN: counts + before/after, writes nothing
  python scripts/fix_italic_heads.py --all           #   ...print every change, not just a sample
  python scripts/fix_italic_heads.py --strongs G2983 #   ...only one Strong's number (spot-check)
  python scripts/fix_italic_heads.py --apply         # write the new labels

PA-only (bible.db lives there). Re-run after a words rebuild only if needed — the
build now carries the same pass (_strip_italic_heads), so a rebuild reproduces it.
"""
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_abp import _head_word

DB = os.path.expanduser("~/bible-db/bible.db")


def main():
    argv = sys.argv[1:]
    do_apply = "--apply" in argv
    show_all = "--all" in argv
    only = None
    if "--strongs" in argv:
        only = argv[argv.index("--strongs") + 1].upper()
    limit = 40
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    where = "w.english LIKE '% %' AND COALESCE(w.italic_words,'') != ''"
    params = []
    if only:
        where += " AND w.strongs_base = ?"
        params.append(only)

    rows = conn.execute(
        f"""SELECT w.verse_id, w.position, v.book, v.chapter, v.verse,
                   w.english, w.english_head, w.italic_words, w.strongs_base
            FROM words w JOIN verses v ON v.id = w.verse_id
            WHERE {where}
            ORDER BY w.verse_id, w.position""",
        params,
    ).fetchall()

    changes = []   # (verse_id, position, ref, english, old, new, sbase)
    for r in rows:
        italic_set = {x.strip().lower() for x in (r["italic_words"] or "").split(",") if x.strip()}
        if not italic_set:
            continue
        new_head = _head_word(r["english"], italic_set)
        old_head = r["english_head"]
        if not new_head or new_head == old_head:
            continue
        ref = f'{r["book"]} {r["chapter"]}:{r["verse"]}'
        changes.append((r["verse_id"], r["position"], ref, r["english"], old_head, new_head, r["strongs_base"]))

    print(f"scanned (multi-word glosses carrying an added/italic word): {len(rows)}")
    print(f"labels that change (head was an added word, a real word exists): {len(changes)}")

    if not do_apply:
        shown = changes if show_all else changes[:limit]
        if shown:
            print(f"\nbefore -> after{' (all)' if show_all else f' (first {len(shown)})'}:")
            for _, _, ref, eng, old, new, sb in shown:
                print(f'  {ref:>14}  {sb:<8} | {eng:<28} | {old}  ->  {new}')
        print(f"\n[dry-run] nothing written. Re-run with --apply to rewrite {len(changes)} labels.")
        conn.close()
        return

    conn.executemany(
        "UPDATE words SET english_head = ? WHERE verse_id = ? AND position = ?",
        [(new, vid, pos) for (vid, pos, _, _, _, new, _) in changes],
    )
    conn.commit()
    conn.close()
    print(f"\nDone. Rewrote {len(changes)} labels (words.english_head only).")
    print("Re-run WITHOUT --apply to confirm it reports 0 changes (re-runnable check).")


if __name__ == "__main__":
    main()
