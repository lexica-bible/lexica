#!/usr/bin/env python3
"""retire_hebrew_identity.py — R-2 candidate 3: the Hebrew retirement rewrite.

THE rewrite site of record (reviewer ruling 2026-07-25, docs/PLAN_r2_c3_rebuild.md:
moved here from import_tipnr.py:719 — import_tipnr is untouched and does not run).
Changed-builder discipline binds: dry-run default, --apply to write, trial on a
COPY first, never the live db.

Consumes the stage-1 `pn_greek_identity` classification as the ONE write set of
record (ruling condition 3 — this script derives nothing itself):

  class      rows     action on words.strongs_base
  abp-tag    3,518    none — VERIFIED already the Greek number
  tipnr     10,731    <- greek_strongs (10,508 from H, 223 from '*' — a gain)
  lemma-only 14,850    <- '*' (14,515 rewritten; 335 already '*', untouched)
  none       3,380    none — Hebrew KEPT (2,853; the 527 always-'*' stay '*')

A row's expected CURRENT value is its frozen Hebrew snapshot, or '*' where the
snapshot records it never had one (the 2026-07-25 trial halt: the first version
assumed every non-abp-tag row carried Hebrew; the live matrix — pasted in
docs/PLAN_r2_c3_rebuild.md — showed 1,085 always-'*' rows across three classes).

Every class also lands in the new cross-ref home `pn_hebrew_xref` (DDL below —
JP checkpoint cleared 2026-07-25). ANY row whose current words state disagrees
with its identity-table class HALTS the run (condition 3: halt, not skip).

Usage (PA, JP runs):
  python3 scripts/retire_hebrew_identity.py ~/bible-db/bible_test.db            # dry-run
  python3 scripts/retire_hebrew_identity.py ~/bible-db/bible_test.db --apply
  (--expect-split a,b,c,d overrides the declared class counts — TEST FIXTURES ONLY)
"""
import os
import sqlite3
import sys

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          os.path.expanduser("~/bible-db/bible.db"))
APPLY = "--apply" in sys.argv

# Declared expectations (docs/PLAN_r2_c3_rebuild.md) — the run REFUSES to start
# if the identity table's class split is not exactly this.
EXPECT = {"abp-tag": 3518, "tipnr": 10731, "lemma-only": 14850, "none": 3380}
for i, a in enumerate(sys.argv):
    if a == "--expect-split" and i + 1 < len(sys.argv):
        vals = [int(x) for x in sys.argv[i + 1].split(",")]
        EXPECT = dict(zip(("abp-tag", "tipnr", "lemma-only", "none"), vals))

DDL = """
CREATE TABLE pn_hebrew_xref (
    verse_id    INTEGER NOT NULL,
    position    INTEGER NOT NULL,
    hebrew_base TEXT,              -- the moved Hebrew number; NULL (declared,
                                   -- never '') for always-Greek abp-tag rows,
                                   -- which never had one
    class       TEXT NOT NULL,     -- abp-tag | tipnr | lemma-only | none.
                                   -- 'none' IS the machine-visible kept-Hebrew
                                   -- exception (C3-Q1); retired by the future
                                   -- gentilic/people-class Greek backfill
                                   -- candidate (the named consumer)
    PRIMARY KEY (verse_id, position)
)
"""


def fail(msg):
    print(f"\nHALT: {msg}")
    sys.exit(1)


def main():
    print(f"{'[APPLY] ' if APPLY else '[DRY-RUN] '}retire_hebrew_identity -> {DB}\n")
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=10000")

    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='pn_greek_identity'").fetchone():
        fail("pn_greek_identity absent — the write set of record does not exist here.")
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='pn_hebrew_xref'").fetchone():
        fail("pn_hebrew_xref already exists — this run is single-shot per copy; "
             "start from a fresh copy of the pre-rebuild db.")

    split = {r["source"]: r["c"] for r in conn.execute(
        "SELECT source, count(*) AS c FROM pn_greek_identity GROUP BY source")}
    print("identity class split:", {k: split.get(k, 0) for k in EXPECT})
    if {k: split.get(k, 0) for k in EXPECT} != EXPECT:
        fail(f"class split differs from the declared expectation {EXPECT} — "
             "the write set moved since the plan was declared; stop and re-declare.")

    # One pass over the write set, verifying every row's CURRENT words state
    # against its class before anything is written (halt, not skip).
    rows = conn.execute("""
        SELECT g.verse_id, g.position, g.greek_strongs, g.hebrew_base, g.source,
               w.rowid AS wrow, w.strongs_base AS cur
        FROM pn_greek_identity g
        LEFT JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
    """).fetchall()

    updates, xref = [], []
    n_write = {"tipnr-H": 0, "tipnr-*": 0, "lemma-only": 0, "lemma-already*": 0,
               "none-H": 0, "none-*": 0}
    n_nullheb = 0
    for r in rows:
        cls = r["source"]
        if r["wrow"] is None:
            fail(f"identity row ({r['verse_id']},{r['position']}) has no words row.")
        if r["hebrew_base"] is None:
            n_nullheb += 1
        if cls == "abp-tag":
            if r["cur"] != r["greek_strongs"] or not (r["cur"] or "").startswith("G"):
                fail(f"abp-tag row ({r['verse_id']},{r['position']}): words carries "
                     f"{r['cur']!r}, identity says {r['greek_strongs']!r}.")
            if r["hebrew_base"] is not None:
                fail(f"abp-tag row ({r['verse_id']},{r['position']}) carries a "
                     f"hebrew_base {r['hebrew_base']!r} — snapshot contradiction.")
        else:
            expected = r["hebrew_base"] if r["hebrew_base"] is not None else "*"
            if r["cur"] != expected:
                fail(f"{cls} row ({r['verse_id']},{r['position']}): words carries "
                     f"{r['cur']!r} but the frozen snapshot expects {expected!r} — "
                     f"the column moved since stage 1.")
            was_star = r["hebrew_base"] is None
            if cls == "tipnr":
                if not (r["greek_strongs"] or "").startswith("G"):
                    fail(f"tipnr row ({r['verse_id']},{r['position']}) has no "
                         f"Greek number ({r['greek_strongs']!r}).")
                updates.append((r["greek_strongs"], r["wrow"]))
                n_write["tipnr-*" if was_star else "tipnr-H"] += 1
            elif cls == "lemma-only":
                if was_star:
                    n_write["lemma-already*"] += 1   # already the C3-Q2 state
                else:
                    updates.append(("*", r["wrow"]))
                    n_write["lemma-only"] += 1
            else:  # 'none': verified above, bytes untouched (C3-Q1)
                n_write["none-*" if was_star else "none-H"] += 1
        xref.append((r["verse_id"], r["position"], r["hebrew_base"], cls))

    # PN words OUTSIDE the write set (post-stage-1 drift would show here).
    orphans = conn.execute("""
        SELECT count(*) FROM words w WHERE w.is_pn = 1
        AND NOT EXISTS (SELECT 1 FROM pn_greek_identity g
                        WHERE g.verse_id = w.verse_id AND g.position = w.position)
    """).fetchone()[0]
    print(f"verified {len(rows):,} rows against their classes — all consistent.")
    print(f"planned rewrites: tipnr {n_write['tipnr-H']:,} H->Greek + "
          f"{n_write['tipnr-*']:,} '*'->Greek (gain), "
          f"lemma-only {n_write['lemma-only']:,} H->'*' "
          f"({n_write['lemma-already*']:,} already '*', untouched); "
          f"kept: none {n_write['none-H']:,} Hebrew + {n_write['none-*']:,} '*', "
          f"abp-tag {EXPECT['abp-tag']:,} untouched")
    print(f"total rows changing: {len(updates):,}")
    print(f"pn_hebrew_xref rows to write: {len(xref):,} "
          f"(no-Hebrew-number rows: {n_nullheb:,})")
    print(f"is_pn words outside the write set: {orphans:,} (expected 0)")
    if orphans:
        fail("proper-noun words exist outside the stage-1 classification — "
             "the write set is stale; stop and re-declare.")

    if not APPLY:
        print("\n[DRY RUN] No changes written. Re-run with --apply.")
        conn.close()
        return

    conn.execute(DDL)
    conn.executemany("INSERT INTO pn_hebrew_xref VALUES (?,?,?,?)", xref)
    conn.execute("CREATE INDEX idx_pnx_heb ON pn_hebrew_xref(hebrew_base)")
    conn.executemany("UPDATE words SET strongs_base=? WHERE rowid=?", updates)
    conn.commit()

    # Post-write verification, every declared invariant, no sampling.
    bad_glob = conn.execute(
        "SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'").fetchone()[0]
    n_x = conn.execute("SELECT count(*) FROM pn_hebrew_xref").fetchone()[0]
    n_null = conn.execute("SELECT count(*) FROM pn_hebrew_xref "
                          "WHERE hebrew_base IS NULL").fetchone()[0]
    n_empty = conn.execute("SELECT count(*) FROM pn_hebrew_xref "
                           "WHERE hebrew_base = ''").fetchone()[0]
    print(f"\nwrote pn_hebrew_xref: {n_x:,} rows "
          f"(no-Hebrew-number rows: {n_null:,}, expected {n_nullheb:,}; "
          f"empty-string: {n_empty:,}, expected 0)")
    print(f"applied {len(updates):,} strongs_base rewrites")
    print(f"GLOB invariant (bare-number strongs_base): {bad_glob} (expected 0)")
    ok = (bad_glob == 0 and n_x == len(xref)
          and n_null == n_nullheb and n_empty == 0)
    conn.close()
    if not ok:
        fail("post-write verification failed — do NOT swap; restore the copy.")
    print("\nDone — all post-write checks pass. Gates (compare_words, "
          "unfindability, two-derivations, health_check) still ride separately.")


if __name__ == "__main__":
    main()
