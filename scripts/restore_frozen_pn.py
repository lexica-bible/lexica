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

Declared expectation: 6 slots (the 2Sa 18 Cushi class, H3570 -> H3569).
RE-DECLARED at the 8/1 ride from this script's own full-population dry-run
on the real fresh build: 28,961 slots checked, exactly the 6 Cushi differed.
The first declaration said 363 ("357 hand-fix-zone + 6 Cushi") — the 357 was
ported from a memory line about the G707-session census without verifying
what that census compared; it was never fresh-import drift. Evidence of
agreement everywhere else: the 1,085 still-'*' slots after import match the
frozen record's always-'*' count to the row. A different count HALTS.

SUPERSEDED 2026-08-05 (lane-② ride, reviewer-ruled): the "6" figure is itself
stale — the member derivation split it 5 clean renumbers + 3 Cushi-verse
position churn, entangled with 2,520 slots the PN-star pass legitimately
moved (attribution: scripts/cross_restore_vs_plan.py, zero unattributed).
The Cushi hand fix is now NAME-keyed (scripts/apply_cushi_namekeyed.py) and
the frozen record was re-baselined to the new geometry. The next ride's
expectation must be RE-DECLARED from its own dry-run against the NEW record.
The --expect override is REMOVED (same ruling): the one thing the 2026-08-05
HALT proved is that an override must never absorb a geometry change — a
count mismatch here always ends in a member-level attribution, never a flag.

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

EXPECT = 6
# TEST FIXTURES ONLY (the sanctioned --expect-split pattern): the harness sets
# the declared figure for synthetic dbs via env, never via a runtime flag.
if os.environ.get("RESTORE_EXPECT_FIXTURE"):
    EXPECT = int(os.environ["RESTORE_EXPECT_FIXTURE"])
if "--expect" in sys.argv:
    print("HALT: --expect was removed (reviewer ruling 2026-08-05) — a count "
          "mismatch is attributed by member (cross_restore_vs_plan.py) and the "
          "declared figure re-declared in code, never overridden at run time.")
    sys.exit(1)


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
             "set moved since the census; attribute the member list above "
             "(scripts/cross_restore_vs_plan.py) and re-declare in code — "
             "there is no runtime override.")

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
