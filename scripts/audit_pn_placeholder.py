#!/usr/bin/env python3
"""
audit_pn_placeholder.py — does each merged name-on-verb cell have an empty
proper-noun slot sitting next to it?

The merge (Tamar/David/Moses…) folds the subject name into the verb's English
("Judah took") and leaves the name's OWN slot blank right beside it
(english '', strongs_base '*', is_pn 1). If that empty slot is always adjacent,
the fix is in-place (move the name onto its slot, let import_tipnr resolve it) —
no inserts, no position shifts.

This READ-ONLY scan, for every merged cell (is_pn=0, real number, multi-word,
first word a tipnr name), checks position+1 then position-1 for an empty '*'
slot, and tallies:
  - with slot   : the clean in-place fixable ones (real merges)
  - without slot: no adjacent empty slot — false alarms (e.g. "On account of"
                  = the preposition) OR a real merge the build shaped differently

It prints the two counts and lists the no-slot REAL-name cases (the ones that
would need a closer look), capped. Writes nothing.

  python3 scripts/audit_pn_placeholder.py bible.db
"""
import argparse
import re
import sqlite3


def _first_word(eng):
    if not eng:
        return None
    s = eng.lstrip("[(\"'“‘ \t")
    m = re.match(r"[A-Za-z][A-Za-z'\-]*", s)
    return m.group(0) if m else None


def _empty_star_at(conn, vid, pos):
    r = conn.execute(
        "SELECT 1 FROM words WHERE verse_id=? AND position=? AND strongs_base='*'"
        " AND (english IS NULL OR trim(english)='')",
        (vid, pos),
    ).fetchone()
    return r is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    names = set()
    for r in conn.execute("SELECT name FROM tipnr"):
        nm = (r["name"] or "").strip().lower()
        if len(nm) > 1:
            names.add(nm)

    rows = conn.execute(
        """SELECT w.verse_id, w.position, v.book, v.chapter, v.verse,
                  w.english, w.strongs_base
           FROM words w JOIN verses v ON v.id = w.verse_id
           WHERE w.is_pn = 0
             AND w.english LIKE '% %'
             AND w.strongs_base GLOB '[GH][0-9]*'
           ORDER BY v.id, w.position"""
    ).fetchall()

    with_slot = 0
    after = before = 0
    no_slot = []
    for r in rows:
        fw = _first_word(r["english"])
        if not (fw and fw[0].isupper() and fw.lower() in names):
            continue
        vid, pos = r["verse_id"], r["position"]
        if _empty_star_at(conn, vid, pos + 1):
            with_slot += 1; after += 1
        elif _empty_star_at(conn, vid, pos - 1):
            with_slot += 1; before += 1
        else:
            no_slot.append((fw, r["book"], r["chapter"], r["verse"],
                            r["english"], r["strongs_base"]))

    total = with_slot + len(no_slot)
    print(f"Merged name-on-verb cells: {total:,}\n")
    print(f"  WITH an adjacent empty '*' slot : {with_slot:,}"
          f"  (after {after:,} / before {before:,})  ← clean in-place fix")
    print(f"  WITHOUT a slot                  : {len(no_slot):,}"
          f"  ← false alarms + any odd ones\n")

    print("No-slot cases (review — false alarms like 'On account of' expected here):")
    for fw, book, ch, vs, eng, base in no_slot[:120]:
        print(f"     {book} {ch}:{vs:<4} {base:<7} {eng!r}")
    if len(no_slot) > 120:
        print(f"     … and {len(no_slot) - 120:,} more")
    conn.close()


if __name__ == "__main__":
    main()
