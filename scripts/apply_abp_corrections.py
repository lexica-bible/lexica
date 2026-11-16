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
    EXCEPT a row SPENT BY LANE-3 (scripts/lane3_spent.py, DESIGN §9.153): a ruled lane-3
    edit (rebuild step 8b.2a) rewrote the cell after this step. Only when the rule's three
    conditions hold AND the row is declared there: printed "~~ ... spent by lane-3" with
    the op it matched, counted on its own ("spent by lane-3: k"), never as already-applied,
    and not a skip. The lane-3 files' shas are printed at the top of every report.

Reads the table FROM THE TARGET DB ITSELF — the rebuild scratch is a snapshot of live,
so once the table exists in live, every copy carries its own corrections. A db without
the table (pre-creation copies) is a clean no-op, so the tail step is deploy-safe.

Only rows with status='active' AND applied_at='ingest' are applied. Writes ONLY the named
words cells; also appends a run report to <db>.corrections.log beside the db.

Usage:
  python3 scripts/apply_abp_corrections.py <db>            # dry run (default)
  python3 scripts/apply_abp_corrections.py <db> --apply    # write

Exit: 0 = clean (applied / already-applied / declared spent / no table); 1 = at least one
LOUD skip.
"""
import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lane3_spent import Lane3Ops, declared, describe  # the ONE spent-by-lane-3 rule (§9.153)


def cellmatch(cell, target):
    """Compare a stored words/verses cell to a correction's TEXT source/corrected
    value. Number columns (greek_pos, position, ...) come back as a number while the
    correction stores text ('1'), so a plain '==' silently never matches — compare as
    text. A blank (NULL) cell equals ONLY a None target, never '' — an empty-string
    cell is a real, distinct value. Text columns behave exactly as a bare '==' did:
    str(str)==target, and None stays distinct from ''."""
    if cell is None:
        return target is None
    return str(cell) == target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write (default = dry run)")
    ap.add_argument("--only", choices=["words", "verses"],
                    help="apply only one target — the two-point rebuild (prose EARLY before "
                         "split-flip, word cells LATE at step 7). Unset = both (back-compatible).")
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
    lane3 = Lane3Ops()
    lines = [f"[{mode}] abp_corrections -> {args.db}  ({datetime.now():%Y-%m-%d %H:%M:%S})",
             f"  active ingest-time corrections: {len(rows)}"]
    lines += [f"  {s}" for s in lane3.lines]
    applied = already = spent = skipped = 0
    cur = conn.cursor()

    for c in rows:
        is_prose = (c["field"] == "verses.text")            # S9 (f): a prose (verses.text) row
        # --only = the two application points. Prose rows are filtered out of the words pass
        # and vice versa, so a prose row (position=-1) never reaches the words position lookup.
        if args.only == "words" and is_prose:
            continue
        if args.only == "verses" and not is_prose:
            continue
        loc = "[verses.text]" if is_prose else f"pos {c['position']} {c['field']}"
        key = f"{c['book']} {c['chapter']}:{c['verse']} {loc}"
        if is_prose:
            hits = conn.execute(
                """SELECT v.rowid AS rid, v.text AS val FROM verses v
                   WHERE v.book=? AND v.chapter=? AND v.verse=?""",
                (c["book"], c["chapter"], c["verse"])).fetchall()
            tbl, col = "verses", "text"
        else:
            if c["field"] not in word_cols:
                lines.append(f"  !! SKIP {key}: '{c['field']}' is not a words column")
                skipped += 1
                continue
            hits = conn.execute(
                f"""SELECT w.rowid AS rid, w."{c['field']}" AS val
                    FROM words w JOIN verses v ON v.id = w.verse_id
                    WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?""",
                (c["book"], c["chapter"], c["verse"], c["position"])).fetchall()
            tbl, col = "words", c["field"]
        if len(hits) != 1:
            lines.append(f"  !! SKIP {key}: {len(hits)} matching slot(s) — expected exactly 1")
            skipped += 1
            continue
        val = hits[0]["val"]
        if cellmatch(val, c["corrected_value"]):
            already += 1
            lines.append(f"  == {key}: already applied (ok)")
        elif cellmatch(val, c["source_value"]):
            if args.apply:
                cur.execute(f'UPDATE {tbl} SET "{col}"=? WHERE rowid=?',
                            (c["corrected_value"], hits[0]["rid"]))
            applied += 1
            lines.append(f"  -> {key}: {'applied' if args.apply else 'would apply'}"
                         f"  [{c['ledger_ref'] or c['reason'][:40]}]")
        else:
            # §9.153 (option B): a lane-3 op may have rewritten this cell after step 7. Asked ONLY
            # here, after source and corrected both failed — so a pre-8b.2a copy still applies.
            m = None if is_prose else lane3.match(conn, c)
            if m and declared(c):
                spent += 1
                lines.append(f"  ~~ {key}: spent by lane-3 8b.2a  [{c['ledger_ref'] or ''}] "
                             f"cell {(val or '')[:70]!r} — matched {describe(*m)} "
                             f"— declared {declared(c)}")
                continue
            skipped += 1
            lines.append(f"  !! SKIP {key}: cell {(val or '')[:70]!r}… matches NEITHER source "
                         "NOR corrected — position drift / upstream change: regraft, do not force.")
            if m:
                lines.append(f"     (the spent-by-lane-3 rule matches {describe(*m)}, but this "
                             "row is NOT declared spent — red until ruled)")

    if args.apply:
        conn.commit()
    conn.close()

    verb = "applied" if args.apply else "would apply"
    lines.append(f"  summary: {verb} {applied} · already-applied {already} · "
                 f"spent by lane-3: {spent} · LOUD-SKIPPED {skipped}")
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
