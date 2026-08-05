#!/usr/bin/env python3
"""apply_cushi_namekeyed.py — the 2Sa 18 Cushi hand fix, keyed by NAME not slot.

Reviewer-ruled 2026-08-05 (lane-② ride): the frozen record's position-keyed
restore proved fragile the moment a build pass legitimately moved names between
slots. This applies the one standing hand fix — Cushi is H3569, import_tipnr
re-breaks it to H3570 — wherever the name NOW sits:

    every words slot IN 2Sa 18 whose word is 'cushi' (normalized) AND whose
    strongs_base is 'H3570' -> 'H3569'

The 2Sa 18 scope is load-bearing, not caution: 'Cushi' is ALSO a genuinely-
H3570 man elsewhere (Zep 1:1 Zephaniah's ancestor, Jer 36:14) — the hand fix
has only ever covered the 2Sa 18 runner. Within the chapter, position is not
consulted at all, so a pass that moved the name still gets its fix
(control-tested), and a non-Cushi slot carrying H3570 is refused by the name
leg (control-tested). Mirrors restore_frozen_pn's write shape exactly:
strongs_base only.

Dry-run by default; --apply writes. Run on the rebuild copy AFTER import_tipnr
and BEFORE the identity re-baseline capture (build_pn_greek_identity), so the
new frozen record carries the hand fix.

Usage:
  python3 scripts/apply_cushi_namekeyed.py <db>            # dry-run
  python3 scripts/apply_cushi_namekeyed.py <db> --apply
"""
import re
import sqlite3
import sys

_NORM = re.compile(r"[^\w]")

WRONG, RIGHT = "H3570", "H3569"
NAME = "cushi"


def norm(w):
    return _NORM.sub("", (w or "")).lower()


BOOK, CHAPTER = "2Sa", 18


def find_members(conn):
    """(rowid, verse_id, position, english) of every 2Sa-18 name-keyed hit."""
    out = []
    for rowid, vid, pos, eng, head in conn.execute(
            "SELECT w.rowid, w.verse_id, w.position, w.english, w.english_head"
            " FROM words w JOIN verses v ON v.id = w.verse_id"
            " WHERE w.strongs_base = ? AND v.book = ? AND v.chapter = ?",
            (WRONG, BOOK, CHAPTER)):
        if norm(head) == NAME or norm(eng) == NAME:
            out.append((rowid, vid, pos, eng))
    return out


def main():
    db = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    apply_ = "--apply" in sys.argv
    if not db:
        print("usage: apply_cushi_namekeyed.py <db> [--apply]")
        sys.exit(2)
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=10000")

    members = find_members(conn)
    print(f"{'[APPLY] ' if apply_ else '[DRY-RUN] '}cushi name-keyed fix -> {db}")
    print(f"  {len(members)} slot(s) match (word '{NAME}' at {WRONG}):")
    for rowid, vid, pos, eng in members:
        print(f"    ({vid},{pos}) {eng!r}: {WRONG} -> {RIGHT}")
    # every remaining H3570 row is shown so a refusal is visible, not silent —
    # out-of-scope rows (Zep 1:1 / Jer 36:14 class) are LEGITIMATE H3570s
    others = conn.execute(
        "SELECT w.verse_id, w.position, w.english, v.book, v.chapter"
        " FROM words w JOIN verses v ON v.id = w.verse_id"
        " WHERE w.strongs_base = ?", (WRONG,)).fetchall()
    refused = [o for o in others
               if not any(o[0] == m[1] and o[1] == m[2] for m in members)]
    print(f"  {len(refused)} other {WRONG} slot(s) refused (name leg or "
          f"outside {BOOK} {CHAPTER} — those stay {WRONG} by design):")
    for vid, pos, eng, bk, ch in refused:
        print(f"    ({vid},{pos}) {bk} {ch} {eng!r} — stays {WRONG}")

    if not apply_:
        print("\n[DRY RUN] nothing written. Re-run with --apply.")
        conn.close()
        return
    conn.executemany("UPDATE words SET strongs_base=? WHERE rowid=?",
                     [(RIGHT, m[0]) for m in members])
    conn.commit()
    left = conn.execute(
        "SELECT count(*) FROM words w JOIN verses v ON v.id = w.verse_id"
        " WHERE w.strongs_base=? AND v.book=? AND v.chapter=? AND "
        "(w.english_head LIKE '%ushi%' OR w.english LIKE '%ushi%')",
        (WRONG, BOOK, CHAPTER)).fetchone()[0]
    print(f"\napplied {len(members)}; {BOOK} {CHAPTER} cushi-looking slots "
          f"still {WRONG}: {left} (must be 0)")
    conn.close()
    sys.exit(1 if left else 0)


if __name__ == "__main__":
    main()
