#!/usr/bin/env python3
"""audit_unfindability.py — R-2 candidate 3, G3 condition 1 (MANDATORY gate).

The S2-Q4 bar: nothing findable before the Hebrew retirement may become
unfindable after it. Read-only. Enumerates EVERY affected row (no sampling)
across the two databases:

  BEFORE db — TWO SHAPES, auto-detected (2026-08-01, the 8/1 ride):
  * PRE-RETIREMENT shape (no pn_hebrew_xref — the original C3 flow): every
    scoped row must match its frozen snapshot in words: strongs_base = its
    hebrew_base, or '*' for rows that never had one.
  * RETIRED shape (pn_hebrew_xref present — live since 7/26, the normal case
    for any rebuild now): "findable" means the retired serving contract —
    Hebrew intact in the xref, identity intact in words (tipnr → its Greek
    number; lemma-only/surface → '*' + a stored Greek lemma). The old check
    read the pre-retirement shape against retired live and drowned in 20,329
    false BEFORE failures — worse, each one SKIPPED that row's after-check,
    so the after-leg zero covered a tenth of the scope. Both legs now run on
    every row, always.

  AFTER db (the rebuilt test copy): each of those same rows must still be
  reachable BOTH ways —
    * by its Hebrew number, through pn_hebrew_xref (the serving path
      core.h_abp_predicate actually uses), and
    * as an identity: tipnr rows carry the Greek number in words;
      lemma-only rows have a stored Greek lemma (Q3's honest state).

CONTROL (certification rule — the detector must fire before a zero counts):
before the real pass, a synthetic missing row is pushed through the same
checker and MUST come back as a failure, else the audit aborts.

Usage (PA, read-only):
  python3 scripts/audit_unfindability.py ~/bible-db/bible_pre_r2c3_<date>.db ~/bible-db/bible_test.db
"""
import sqlite3
import sys

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
BEFORE, AFTER = sys.argv[1], sys.argv[2]


def ro(path):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def check_after(a, vid, pos, heb, cls, greek, lemma, words_base):
    """Return a list of failure strings for one row (empty = findable)."""
    out = []
    x = a.execute("SELECT hebrew_base, class FROM pn_hebrew_xref "
                  "WHERE verse_id=? AND position=?", (vid, pos)).fetchone()
    if x is None:
        out.append("no pn_hebrew_xref row (Hebrew path gone)")
    elif x["hebrew_base"] != heb:
        out.append(f"xref hebrew_base {x['hebrew_base']!r} != snapshot {heb!r}")
    if cls == "tipnr":
        if words_base != greek:
            out.append(f"words carries {words_base!r}, not the Greek identity {greek!r}")
    elif cls in ("lemma-only", "surface"):
        # surface (7/30 reclassification): page-attested headword, no Greek
        # number — same serving shape as lemma-only ('*' + stored lemma).
        if words_base != "*":
            out.append(f"words carries {words_base!r}, expected '*'")
        if not lemma:
            out.append("no stored Greek lemma — identity lost, not just numberless")
    return out


def main():
    b, a = ro(BEFORE), ro(AFTER)

    # ── CONTROL: the checker must fail a known-missing row ──────────────────
    ctl = check_after(a, -1, -1, "H0000", "tipnr", "G0000", None, None)
    if not ctl:
        print("CONTROL FAILED: the detector did not fire on a synthetic missing "
              "row — audit aborted, zero would be meaningless.")
        sys.exit(2)
    print(f"control: detector fires on a planted missing row ({len(ctl)} finding(s)) — OK\n")

    retired_before = b.execute(
        "SELECT 1 FROM sqlite_master WHERE name='pn_hebrew_xref'").fetchone() is not None
    scope = ("('tipnr', 'lemma-only', 'surface')" if retired_before
             else "('tipnr', 'lemma-only')")
    rows = b.execute(f"""
        SELECT g.verse_id, g.position, g.hebrew_base, g.source, g.greek_strongs,
               g.greek_lemma, w.strongs_base AS before_base
        FROM pn_greek_identity g
        LEFT JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
        WHERE g.source IN {scope}
    """).fetchall()
    print(f"BEFORE shape: {'RETIRED (xref present)' if retired_before else 'pre-retirement'}")
    print(f"rows in scope ({scope}, from the BEFORE db): {len(rows):,}")

    after_base = {(r["verse_id"], r["position"]): r["strongs_base"]
                  for r in a.execute("SELECT verse_id, position, strongs_base FROM words")}
    # AFTER's own identity table is the re-run's; lemma per row from BEFORE's
    # snapshot is the floor (the re-run may only add).
    fails_before = fails_after = 0
    examples = []
    for r in rows:
        if retired_before:
            # BEFORE-findability asks ONE question: was the Hebrew number
            # reachable before — in the xref (retired rows) OR still in the
            # words cell (rows live serves the OLD way because the 7/30
            # reclassification's copy-step never ran there; the 2,190
            # H-carrying churn rows are exactly this, stale-but-findable).
            # The identity SHAPE is the AFTER contract, not a before demand.
            if r["hebrew_base"] is not None:
                bx = b.execute("SELECT hebrew_base FROM pn_hebrew_xref "
                               "WHERE verse_id=? AND position=?",
                               (r["verse_id"], r["position"])).fetchone()
                in_xref = bx is not None and bx["hebrew_base"] == r["hebrew_base"]
                in_words = r["before_base"] == r["hebrew_base"]
                if not (in_xref or in_words):
                    fails_before += 1
                    if len(examples) < 10:
                        examples.append(
                            f"BEFORE ({r['verse_id']},{r['position']}): Hebrew "
                            f"{r['hebrew_base']!r} in neither home (words "
                            f"{r['before_base']!r}, xref "
                            f"{bx['hebrew_base'] if bx else 'NO ROW'!r})")
        else:
            expected = r["hebrew_base"] if r["hebrew_base"] is not None else "*"
            if r["before_base"] != expected:
                fails_before += 1
                if len(examples) < 10:
                    examples.append(f"BEFORE ({r['verse_id']},{r['position']}): "
                                    f"words {r['before_base']!r} != snapshot {expected!r}")
        # The after-leg runs on EVERY row — a broken before-row is exactly the
        # one whose after-state must still be seen (the old `continue` hid it).
        probs = check_after(a, r["verse_id"], r["position"], r["hebrew_base"],
                            r["source"], r["greek_strongs"], r["greek_lemma"],
                            after_base.get((r["verse_id"], r["position"])))
        if probs:
            fails_after += 1
            if len(examples) < 10:
                examples.append(f"AFTER ({r['verse_id']},{r['position']}): " + "; ".join(probs))

    print(f"findable-before check failures: {fails_before:,} (expected 0)")
    print(f"findable-after  check failures: {fails_after:,} (expected 0)")
    for e in examples:
        print("  " + e)
    b.close(); a.close()
    if fails_before or fails_after:
        print("\nUNFINDABILITY GATE: FAIL — do not swap.")
        sys.exit(1)
    print("\nUNFINDABILITY GATE: PASS — zero findable-before/unfindable-after.")


if __name__ == "__main__":
    main()
