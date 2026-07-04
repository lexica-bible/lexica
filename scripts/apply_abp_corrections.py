#!/usr/bin/env python3
"""apply_abp_corrections.py — guarded apply of the abp_corrections table (Tier B overlay).

The certification standard: source defects are NEVER silently fixed in place — each one
is a row in abp_corrections (created by scripts/build_abp_corrections.py, checkpoint-
approved), applied at REBUILD time as the true final step of finish_rebuild.sh (step 7,
after fix_split_flip — corrections are keyed by position, so nothing may move positions
after this runs).

GUARDED APPLY (the fix_split_merges lesson turned into mechanism): each correction fires
ONLY if the target cell still holds source_value exactly. Any other state is reported
LOUDLY and skipped — never a silent write, never a silent no-op:
  * cell == source_value     -> APPLY (the faithful-parse value; correct it)
  * cell == corrected_value  -> already applied (re-run / live copy) — counted, quiet
  * anything else            -> LOUD SKIP (position drift or an upstream change; the
                                correction needs regrafting, not forcing)

Reads the table FROM THE TARGET DB ITSELF — the rebuild scratch is a snapshot of live,
so once the table exists in live, every copy carries its own corrections. A db without
the table (pre-creation copies) is a clean no-op, so the tail step is deploy-safe.

Only rows with status='active' AND applied_at='ingest' are applied. Writes ONLY the named
words cells; also appends a run report to <db>.corrections.log beside the db.

Usage:
  python3 scripts/apply_abp_corrections.py <db>            # dry run (default)
  python3 scripts/apply_abp_corrections.py <db> --apply    # write

Exit: 0 = clean (applied / already-applied / no table); 1 = at least one LOUD skip.
"""
import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write (default = dry run)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    has_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_corrections'"
    ).fetchone()
    if not has_table:
        print(f"abp_corrections: no table in {args.db} — nothing to apply (ok).")
        conn.close()
        sys.exit(0)

    # words-column whitelist — `field` is interpolated into SQL, so it must be a real column
    word_cols = {r[1] for r in conn.execute("PRAGMA table_info(words)")}

    rows = conn.execute(
        """SELECT * FROM abp_corrections
           WHERE status='active' AND applied_at='ingest'
           ORDER BY book, chapter, verse, position, field"""
    ).fetchall()

    mode = "APPLY" if args.apply else "DRY-RUN"
    lines = [f"[{mode}] abp_corrections -> {args.db}  ({datetime.now():%Y-%m-%d %H:%M:%S})",
             f"  active ingest-time corrections: {len(rows)}"]
    applied = already = skipped = 0
    cur = conn.cursor()

    for c in rows:
        key = f"{c['book']} {c['chapter']}:{c['verse']} pos {c['position']} {c['field']}"
        if c["field"] not in word_cols:
            lines.append(f"  !! SKIP {key}: '{c['field']}' is not a words column")
            skipped += 1
            continue
        hits = conn.execute(
            f"""SELECT w.rowid AS rid, w."{c['field']}" AS val
                FROM words w JOIN verses v ON v.id = w.verse_id
                WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?""",
            (c["book"], c["chapter"], c["verse"], c["position"])).fetchall()
        if len(hits) != 1:
            lines.append(f"  !! SKIP {key}: {len(hits)} matching slot(s) — expected exactly 1")
            skipped += 1
            continue
        val = hits[0]["val"]
        if val == c["corrected_value"]:
            already += 1
            lines.append(f"  == {key}: already {c['corrected_value']!r} (ok)")
        elif val == c["source_value"]:
            if args.apply:
                cur.execute(f'UPDATE words SET "{c["field"]}"=? WHERE rowid=?',
                            (c["corrected_value"], hits[0]["rid"]))
            applied += 1
            lines.append(f"  -> {key}: {c['source_value']!r} -> {c['corrected_value']!r}"
                         f"  [{c['ledger_ref'] or c['reason'][:40]}]")
        else:
            skipped += 1
            lines.append(f"  !! SKIP {key}: cell reads {val!r} — matches NEITHER "
                         f"source {c['source_value']!r} NOR corrected "
                         f"{c['corrected_value']!r}. Position drift or upstream change: "
                         "regraft this correction, do not force it.")

    if args.apply:
        conn.commit()
    conn.close()

    verb = "applied" if args.apply else "would apply"
    lines.append(f"  summary: {verb} {applied} · already-applied {already} · "
                 f"LOUD-SKIPPED {skipped}")
    if skipped:
        lines.append("  !! one or more corrections did NOT land — see the SKIP lines above.")
    report = "\n".join(lines)
    print(report)

    log = Path(args.db + ".corrections.log")
    with log.open("a", encoding="utf-8") as f:
        f.write(report + "\n\n")
    print(f"  (report appended to {log.name})")
    sys.exit(1 if skipped else 0)


if __name__ == "__main__":
    main()
