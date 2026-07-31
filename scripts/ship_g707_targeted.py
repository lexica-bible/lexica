#!/usr/bin/env python3
"""ship_g707_targeted.py — the G707-class targeted ship (JP ruling (b), 2026-07-31).

Ships ONLY the strict-name-match gate's effect onto a copy of live; the 7/30
reclassification catch-up explicitly does NOT ship (its own ticket). Writes:

  1. words.strongs_base -> '*' on exactly the LEAVER slots (live cross-ref
     class 'tipnr', new identity source != 'tipnr') — the honest no-Greek-
     number state; Hebrew stays reachable via the cross-ref.
  2. pn_hebrew_xref.class -> 'lemma-only' on those same slots (hebrew_base
     byte-untouched). Uniform lemma-only: 'none' means words still carries
     Hebrew (not true here) and 'surface' is not a cross-ref class; the
     binder's guard CASE treats hebrew-carrying rows identically either way
     (build_entity_binding.occ_base_parts — verified 2026-07-31).
  3. pn_greek_identity replaced by the gated table from the scratch build.

Everything else byte-identical to live — verified by full-column recounts,
not sampling. retire_hebrew_identity does NOT run (its class-count
re-declaration belongs to the catch-up ticket).

Usage (PA, JP runs; SHIP is a fresh `cp bible.db bible_ship.db`):
  python3 scripts/ship_g707_targeted.py bible_ship.db --live ~/bible-db/bible.db \
      --scratch ~/bible-db/bible_test.db            # dry-run
  ... --apply
"""
import os
import sqlite3
import sys

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SHIP = os.path.expanduser(ARGS[0]) if ARGS else None
APPLY = "--apply" in sys.argv


def opt(name, default):
    for i, a in enumerate(sys.argv):
        if a == name and i + 1 < len(sys.argv):
            return os.path.expanduser(sys.argv[i + 1])
    return os.path.expanduser(default)


LIVE = opt("--live", "~/bible-db/bible.db")
SCRATCH = opt("--scratch", "~/bible-db/bible_test.db")

# Pinned expectations (session receipts G1-G3, 2026-07-31). A different count
# means the inputs moved since the verdict — HALT, do not loosen.
EXPECT_LEAVERS = 524
EXPECT_IDENTITY_ROWS = 32479
EXPECT_G707 = [("arimathea", 4)]

LEAVER_SQL = """
    SELECT x.verse_id, x.position
    FROM live.pn_hebrew_xref x
    JOIN scratch.pn_greek_identity g
      ON g.verse_id = x.verse_id AND g.position = x.position
    WHERE x.class = 'tipnr' AND g.source != 'tipnr'
"""


def fail(msg):
    print(f"\nHALT: {msg}")
    sys.exit(1)


def main():
    if not SHIP:
        fail("usage: ship_g707_targeted.py <ship-copy.db> [--live ..] [--scratch ..] [--apply]")
    print(f"{'[APPLY] ' if APPLY else '[DRY-RUN] '}ship_g707_targeted -> {SHIP}")
    print(f"  live reference: {LIVE}\n  gated scratch:  {SCRATCH}\n")
    conn = sqlite3.connect(SHIP)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute(f"ATTACH ? AS live", (LIVE,))
    conn.execute(f"ATTACH ? AS scratch", (SCRATCH,))

    # ── Preconditions (every one a HALT, none a warning) ─────────────────────
    n_id = conn.execute("SELECT count(*) FROM scratch.pn_greek_identity").fetchone()[0]
    if n_id != EXPECT_IDENTITY_ROWS:
        fail(f"scratch identity rows {n_id:,} != pinned {EXPECT_IDENTITY_ROWS:,}")

    # Removal-only invariant (the generalized C2): a slot's served Greek
    # number may disappear but never differ.
    n_swap = conn.execute("""
        SELECT count(*) FROM live.pn_hebrew_xref x
        JOIN scratch.pn_greek_identity g
          ON g.verse_id = x.verse_id AND g.position = x.position
        JOIN live.words lw
          ON lw.verse_id = x.verse_id AND lw.position = x.position
        WHERE x.class = 'tipnr' AND g.source = 'tipnr'
          AND lw.strongs_base != g.greek_strongs
    """).fetchone()[0]
    if n_swap != 0:
        fail(f"removal-only violated: {n_swap} slot(s) would change number (must be 0)")

    leavers = conn.execute(LEAVER_SQL).fetchall()
    if len(leavers) != EXPECT_LEAVERS:
        fail(f"leaver count {len(leavers)} != pinned {EXPECT_LEAVERS}")

    # The identity tables may differ ONLY at the leaver slots (greek column).
    n_gdiff = conn.execute("""
        SELECT count(*) FROM live.pn_greek_identity lg
        JOIN scratch.pn_greek_identity g
          ON g.verse_id = lg.verse_id AND g.position = lg.position
        WHERE COALESCE(lg.greek_strongs,'') != COALESCE(g.greek_strongs,'')
    """).fetchone()[0]
    n_gdiff_outside = conn.execute(f"""
        SELECT count(*) FROM live.pn_greek_identity lg
        JOIN scratch.pn_greek_identity g
          ON g.verse_id = lg.verse_id AND g.position = lg.position
        WHERE COALESCE(lg.greek_strongs,'') != COALESCE(g.greek_strongs,'')
          AND (lg.verse_id, lg.position) NOT IN ({LEAVER_SQL})
    """).fetchone()[0]
    print(f"leaver slots: {len(leavers)} (pinned {EXPECT_LEAVERS})")
    print(f"identity greek-number diffs vs live identity: {n_gdiff} "
          f"(outside the leaver set: {n_gdiff_outside}, must be 0)")
    if n_gdiff_outside != 0:
        fail("identity table differs beyond the leaver set — enumerate before shipping")

    if not APPLY:
        print("\n[DRY RUN] No changes written. Re-run with --apply.")
        return

    # ── Writes ───────────────────────────────────────────────────────────────
    conn.executemany(
        "UPDATE words SET strongs_base='*' WHERE verse_id=? AND position=?", leavers)
    conn.executemany(
        "UPDATE pn_hebrew_xref SET class='lemma-only' WHERE verse_id=? AND position=?",
        leavers)
    conn.execute("DROP TABLE pn_greek_identity")
    conn.execute("""
        CREATE TABLE pn_greek_identity (
            verse_id      INTEGER NOT NULL,
            position      INTEGER NOT NULL,
            greek_strongs TEXT,
            greek_lemma   TEXT,
            source        TEXT NOT NULL,
            hebrew_base   TEXT,
            PRIMARY KEY (verse_id, position)
        )
    """)
    conn.execute("INSERT INTO pn_greek_identity SELECT * FROM scratch.pn_greek_identity")
    conn.execute("CREATE INDEX idx_pngi_greek ON pn_greek_identity(greek_strongs)")
    conn.execute("CREATE INDEX idx_pngi_heb ON pn_greek_identity(hebrew_base)")
    conn.commit()

    # ── Post-verify: full recounts, zero tolerance ───────────────────────────
    probs = []
    g707 = conn.execute("SELECT english_head, count(*) FROM words "
                        "WHERE strongs_base='G707' GROUP BY 1").fetchall()
    if sorted(g707) != sorted(EXPECT_G707):
        probs.append(f"G707 breakdown {g707} != {EXPECT_G707}")
    n_wdiff = conn.execute("""
        SELECT count(*) FROM words w JOIN live.words lw ON lw.rowid = w.rowid
        WHERE lw.strongs_base != w.strongs_base
    """).fetchone()[0]
    if n_wdiff != EXPECT_LEAVERS:
        probs.append(f"words rows differing vs live = {n_wdiff}, expected {EXPECT_LEAVERS}")
    n_xdiff = conn.execute("""
        SELECT count(*) FROM pn_hebrew_xref x
        JOIN live.pn_hebrew_xref lx
          ON lx.verse_id = x.verse_id AND lx.position = x.position
        WHERE lx.class != x.class OR (lx.hebrew_base IS NOT x.hebrew_base)
    """).fetchone()[0]
    if n_xdiff != EXPECT_LEAVERS:
        probs.append(f"xref rows differing vs live = {n_xdiff}, expected {EXPECT_LEAVERS}")
    bad_glob = conn.execute(
        "SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'").fetchone()[0]
    if bad_glob != 0:
        probs.append(f"bare-number invariant broken: {bad_glob} rows")
    for g, nm in (("G717", "megiddo"), ("G3558", "sheba"), ("G914", "jehoiada"),
                  ("G2914", "caphtor"), ("G4554", "sepharad")):
        n = conn.execute("SELECT count(*) FROM words WHERE strongs_base=? "
                         "AND english_head=?", (g, nm)).fetchone()[0]
        if n:
            probs.append(f"{g} still on {nm}: {n} slot(s)")
    n_surface = conn.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
    if n_surface < 389409:
        probs.append(f"abp_surface {n_surface:,} below the 389,409 floor")

    print(f"applied: {len(leavers)} words rewrites + xref class updates, "
          f"identity table replaced ({n_id:,} rows)")
    if probs:
        for p in probs:
            print(f"FAIL  {p}")
        fail("post-verify failed — do NOT swap; discard the ship copy.")
    print("post-verify: words diff 524 exact, xref diff 524 exact, G707 = "
          "arimathea 4, bare-number 0, foreign-name spot checks clean, "
          "surface floor holds.")
    print("\nAll checks pass. Swap is JP's step (single-rollback rule).")


if __name__ == "__main__":
    main()
