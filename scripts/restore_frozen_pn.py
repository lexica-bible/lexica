#!/usr/bin/env python3
"""restore_frozen_pn.py — rebuild-chain step 8b, BEFORE retire_hebrew_identity.

A fresh words rebuild + import_tipnr writes TIPNR's Hebrew numbers onto the
proper-noun slots — but import_tipnr re-breaks hand fixes (Cushi H3569 comes
back as H3570) and can fill or miss slots differently than the frozen record.
retire_hebrew_identity verifies every row against the frozen record and halts
on the first mismatch, so those drifted slots must be put back FIRST.

The oracle is pn_greek_identity.hebrew_base — proven a byte-for-byte carrier
of the frozen pn_hebrew_xref record (JP-run check 4, 2026-08-01, receipt
docs/tickets/RECLASS_catchup_declaration.md; retire_hebrew_identity re-proves
it on every --fresh-rebuild run before dropping anything).

What it does, per identity row EXCEPT class 'abp-tag' (those slots carry
their Greek number straight from the build and are never touched):
  expected = hebrew_base, or '*' where the frozen record says the slot never
  had one; any words slot not at its expected value is set to it.

Declared expectation: 363 slots restored (the 2026-07-31 G707-session census:
357 hand-fix-zone slots + the 6 Cushi slots). A different count HALTS —
look before overriding (--expect N; the census may legitimately move if
import_tipnr/TIPNR.txt changed under the roster-freeze rule).

Usage (PA, JP runs, on the rebuild copy AFTER finish_rebuild.sh):
  python3 scripts/restore_frozen_pn.py ~/bible-db/bible_test.db           # dry-run
  python3 scripts/restore_frozen_pn.py ~/bible-db/bible_test.db --apply
"""
import os
import sqlite3
import sys

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          os.path.expanduser("~/bible-db/bible_test.db"))
APPLY = "--apply" in sys.argv

EXPECT = 363
for i, a in enumerate(sys.argv):
    if a == "--expect" and i + 1 < len(sys.argv):
        EXPECT = int(sys.argv[i + 1])


def fail(msg):
    print(f"\nHALT: {msg}")
    sys.exit(1)


def main():
    print(f"{'[APPLY] ' if APPLY else '[DRY-RUN] '}restore_frozen_pn -> {DB}\n")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=10000")

    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='pn_greek_identity'").fetchone():
        fail("pn_greek_identity absent — the frozen record is not on this copy.")

    rows = conn.execute("""
        SELECT g.verse_id, g.position, g.hebrew_base, g.source,
               w.rowid AS wrow, w.strongs_base AS cur, w.english_head
        FROM pn_greek_identity g
        LEFT JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
        WHERE g.source != 'abp-tag'
    """).fetchall()

    fixes = []
    for r in rows:
        if r["wrow"] is None:
            fail(f"identity row ({r['verse_id']},{r['position']}) has no words "
                 "row — position drift; stop before restoring anything.")
        expected = r["hebrew_base"] if r["hebrew_base"] is not None else "*"
        if r["cur"] != expected:
            fixes.append((expected, r["wrow"], r["verse_id"], r["position"],
                          r["cur"], r["english_head"]))

    print(f"checked {len(rows):,} frozen-record slots (abp-tag excluded); "
          f"{len(fixes)} differ from the frozen record (declared {EXPECT}):")
    for exp, _, vid, pos, cur, head in fixes:
        print(f"  ({vid},{pos}) {head or '?'}: {cur!r} -> {exp!r}")
    if len(fixes) != EXPECT:
        fail(f"restore count {len(fixes)} != declared {EXPECT} — the drift "
             "set moved since the census; look at the member list above "
             "before overriding with --expect.")

    if not APPLY:
        print("\n[DRY RUN] No changes written. Re-run with --apply.")
        conn.close()
        return

    conn.executemany("UPDATE words SET strongs_base=? WHERE rowid=?",
                     [(exp, wrow) for exp, wrow, *_ in fixes])
    conn.commit()

    remaining = conn.execute("""
        SELECT count(*) FROM pn_greek_identity g
        JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
        WHERE g.source != 'abp-tag'
          AND w.strongs_base != COALESCE(g.hebrew_base, '*')
    """).fetchone()[0]
    print(f"\nrestored {len(fixes)} slot(s); slots still off the frozen "
          f"record: {remaining} (must be 0)")
    conn.close()
    if remaining:
        fail("slots still disagree with the frozen record after restore — "
             "do NOT continue the chain.")
    print("Done — retire_hebrew_identity may now run (--fresh-rebuild).")


if __name__ == "__main__":
    main()
