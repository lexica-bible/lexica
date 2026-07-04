#!/usr/bin/env python3
"""
fix_cushi_strongs.py — Issue 2, step 4. By-verse correction of the Cushi runner.

The 6 "Cushi/Cushite" slots in 2 Samuel 18 are stored H3570 (the person Cushi, who
belongs at Jer.36.14), but the verse-identified word there is the Cushite messenger =
H3569, which sits in Cush's number cluster. With the wrong number the binder's fuzzy
second key fails and the slots floor; corrected to H3569 they bind & render Cush/
Cushite by name+verse.

SCOPED TO 2 SAMUEL 18 ONLY — never a global H3570 swap. H3570 also lives at Jer.36.14
(the real Cushi, correctly H3570) and Zep.1.1 (mis-stored H3570 but binds right by
name+verse — harmless). Both are LEFT untouched. Reversible (H3569 -> H3570 to undo).

Touches words.strongs_base for the matched 2Sa-18 slots ONLY; never words.english,
verses, or any other column/row. Re-run after any words-table rebuild (a rebuild
regenerates strongs_base from bh_scrape and would re-introduce the mis-tag).

Acceptance (from the brief, both proven below before any write):
  (a) the 6 runners would render Cush/Cushite once set to H3569
  (b) no word OUTSIDE 2 Samuel 18 changes — the H3570 footprint elsewhere is inert.

Usage (on PythonAnywhere):
  python3 scripts/fix_cushi_strongs.py                 # dry-run, report only
  python3 scripts/fix_cushi_strongs.py --apply         # write the 6 slots
  python3 scripts/fix_cushi_strongs.py --tipnr /path/tipnr.txt   # reuse a local copy
"""

import os
import sys
import sqlite3
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          "/home/appssanding720/bible-db/bible.db")
APPLY = "--apply" in sys.argv
TIPNR_LOCAL = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--tipnr"
                    and i + 1 < len(sys.argv)), None)

TIPNR_URL = (
    "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/"
    "Proper%20Nouns/TIPNR%20-%20Translators%20Individualised%20Proper%20Names"
    "%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt"
)

FROM_NUM = "H3570"     # the mis-stored Cushi number
TO_NUM = "H3569"       # the verse-identified Cushite number (in Cush's cluster)
BOOK, CHAPTER = "2Sa", 18


def load_tipnr():
    if TIPNR_LOCAL:
        return open(TIPNR_LOCAL, encoding="utf-8-sig").read().splitlines()
    print("Downloading TIPNR...")
    with urllib.request.urlopen(TIPNR_URL) as r:
        return r.read().decode("utf-8-sig").splitlines()


def main():
    print(f"{'[APPLY] ' if APPLY else '[DRY-RUN] '}fix_cushi_strongs -> {DB}")
    print(f"  scope: {BOOK} {CHAPTER}, 'Cushi*' slots, {FROM_NUM} -> {TO_NUM}\n")

    conn = sqlite3.connect(DB)   # opened RW; only writes under --apply, scoped below
    conn.row_factory = sqlite3.Row
    has_pn = "is_pn" in {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    pn_where = "w.is_pn = 1" if has_pn else "w.strongs_base = '*'"

    # ── the candidate slots ───────────────────────────────────────────────────
    rows = conn.execute(f"""
        SELECT w.rowid AS rid, v.chapter AS ch, v.verse AS vs,
               w.english_head AS head, w.strongs_base AS base
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE {pn_where} AND v.book = ? AND v.chapter = ?
          AND (lower(w.english_head) LIKE 'cushi%' OR lower(w.english) LIKE 'cushi%')
        ORDER BY v.verse
    """, (BOOK, CHAPTER)).fetchall()

    print(f"Found {len(rows)} 'Cushi*' slot(s) in {BOOK} {CHAPTER}:")
    to_fix, skipped = [], []
    for r in rows:
        mark = ""
        if er.norm_base(r["base"]) == FROM_NUM:
            to_fix.append(r["rid"]); mark = "-> FIX"
        elif er.norm_base(r["base"]) == TO_NUM:
            mark = "(already H3569)"
        else:
            skipped.append(r); mark = "(unexpected # — SKIP)"
        print(f"   {BOOK} {r['ch']}:{r['vs']:<3} head={r['head']!r:14} stored={r['base']!r:8} {mark}")
    if skipped:
        print("\n  WARNING: slots with an unexpected number were NOT touched (verify by hand).")
    print(f"\n  to correct {FROM_NUM} -> {TO_NUM}: {len(to_fix)}")

    # ── acceptance (a): would these render Cush/Cushite at H3569? ──────────────
    ents = er.parse_tipnr(load_tipnr())
    name_idx, base_idx, compact_idx = er.build_indexes(ents)
    print("\nAcceptance (a) — would the corrected slots render Cush/Cushite?")
    all_ok = True
    for r in rows:
        if er.norm_base(r["base"]) not in (FROM_NUM, TO_NUM):
            continue
        b = er.bind_occurrence(ents, name_idx, base_idx, compact_idx,
                               r["head"] or "Cushi", er.book_num(BOOK), r["ch"], r["vs"], TO_NUM)
        who = ents[b.entity]["uniq"] if b.render else "—"
        ok = b.render and ents[b.entity]["head"] == "cush"
        all_ok = all_ok and ok
        print(f"   {BOOK} {r['ch']}:{r['vs']:<3} -> render={b.render} ({b.kind}) {who} "
              + ("[ok]" if ok else "[NO]"))
    print(f"  => acceptance (a): {'PASS' if all_ok and to_fix else 'check above'}")

    # ── acceptance (b): the H3570 footprint elsewhere is left untouched ────────
    print("\nAcceptance (b) — H3570 footprint (only the 2Sa-18 slots may change):")
    foot = conn.execute(f"""
        SELECT v.book AS book, v.chapter AS ch, COUNT(*) AS c
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE {pn_where} AND w.strongs_base = ?
        GROUP BY v.book, v.chapter ORDER BY v.book, v.chapter
    """, (FROM_NUM,)).fetchall()
    for r in foot:
        tag = " <- these get corrected" if (r["book"] == BOOK and r["ch"] == CHAPTER) else " (left as-is)"
        print(f"   {FROM_NUM} at {r['book']} {r['ch']}: {r['c']}{tag}")

    if not APPLY:
        print("\n[DRY-RUN] No changes written. Re-run with --apply once the above looks right.")
        conn.close()
        return

    if not to_fix:
        print("\nNothing to correct. Done.")
        conn.close()
        return

    print(f"\nApplying {len(to_fix)} correction(s)...")
    conn.executemany("UPDATE words SET strongs_base = ? WHERE rowid = ?",
                     [(TO_NUM, rid) for rid in to_fix])
    conn.commit()
    left = conn.execute(f"""
        SELECT COUNT(*) FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE {pn_where} AND v.book=? AND v.chapter=? AND w.strongs_base=?
    """, (BOOK, CHAPTER, FROM_NUM)).fetchone()[0]
    conn.close()
    print(f"  done. {FROM_NUM} remaining in {BOOK} {CHAPTER}: {left} (should be 0)")
    print("  re-run build_entity_binding.py + (after a words rebuild) re-run this fix.")


if __name__ == "__main__":
    main()
