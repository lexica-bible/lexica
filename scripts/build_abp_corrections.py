#!/usr/bin/env python3
"""build_abp_corrections.py — create the abp_corrections table + insert the seed entries.

Tier B of the certification standard: a source defect is never silently fixed in place.
Each one becomes a row here, applied at rebuild time by scripts/apply_abp_corrections.py
(finish_rebuild.sh step 7 — the true final tail step). Schema + first entries approved
at the Session 1/2 checkpoints (see AUDIT_abp_certification.md).

SEED ENTRIES (adjudicated from cert harness run 1, 2026-07-04):
  * Cushi x6 — 2Sa 18, strongs_base H3570 -> H3569 (Class 2; migrates
    fix_cushi_strongs.py into table form — that script then lapses to the graveyard).
  * Jer 49:13 pos 28 — TWO cells, per the run-1 delta TSV (JP's 2026-07-04 paste):
    strongs_base G166 -> G165 AND the bare strongs 166 -> 165 (L11; ABP printed the
    adjective's number on the noun "eon"; the June retag corrected both columns on
    live). Jer 49:13 ONLY — Hab 3:6 was ruled the other way and is deliberately NOT
    here.
L2 / L5 / L10 land later as their own entries once JP recovers the intended readings.

The dry run doubles as validation: it reads each target cell in the given db and
classifies it. Against LIVE (already hand-fixed) every entry should read
"cell=corrected". Against a fresh scratch, "cell=source". Anything else — adjudicate
before --apply.

Usage (on PA):
  python3 scripts/build_abp_corrections.py ~/bible-db/bible.db            # dry run
  python3 scripts/build_abp_corrections.py ~/bible-db/bible.db --apply    # create + insert

Re-runnable: CREATE TABLE IF NOT EXISTS; an entry whose key (book,ch,vs,pos,field)
already has an active row is skipped, never duplicated.
"""
import argparse
import sqlite3
import sys
from datetime import date

SCHEMA = """CREATE TABLE IF NOT EXISTS abp_corrections (
    id              INTEGER PRIMARY KEY,
    book            TEXT NOT NULL,      -- ABP abbrev ('2Sa') — survives rebuilds
    chapter         INTEGER NOT NULL,
    verse           INTEGER NOT NULL,
    position        INTEGER NOT NULL,   -- words.position at authoring time
    field           TEXT NOT NULL,      -- words column ('strongs_base', 'english', ...)
    source_value    TEXT,               -- what the faithful parse yields — PRECONDITION
    corrected_value TEXT,
    reason          TEXT NOT NULL,
    ledger_ref      TEXT,               -- 'L2', 'L11', 'Class2-cushi', ...
    applied_at      TEXT NOT NULL CHECK (applied_at IN ('ingest','read')),
    status          TEXT NOT NULL DEFAULT 'active',   -- active | retired | superseded
    created         TEXT NOT NULL
)"""

_CUSHI_REASON = ("Cushite messenger in 2Sa 18 is H3569 (Cush cluster); BH source tags "
                 "H3570 (the person Cushi of Jer 36:14). Migrated from "
                 "fix_cushi_strongs.py; adjudicated cert run 1 Class 2.")
_JER_REASON = ("ABP prints the adjective's number G166 on the noun 'eon' (aion, G165) — "
               "source 'intoG1519 eon.G3588 G166'. Jer 49:13 ONLY: Hab 3:6 was ruled the "
               "opposite way (adjective slot, G166 honest) and is NOT corrected. "
               "Adjudicated cert run 1 Class 3 / L11.")

# (book, chapter, verse, position, field, source_value, corrected_value, reason, ledger_ref)
ENTRIES = [
    ("2Sa", 18, 21,  4, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 21, 12, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 22, 19, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 23, 23, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 31,  3, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 32,  6, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("Jer", 49, 13, 28, "strongs_base", "G166",  "G165",  _JER_REASON,   "L11"),
    ("Jer", 49, 13, 28, "strongs",      "166",   "165",   _JER_REASON,   "L11"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="create table + insert (default = dry run)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] build_abp_corrections -> {args.db}")
    print(f"  {len(ENTRIES)} seed entr(ies); created stamp = {date.today().isoformat()}\n")

    has_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_corrections'"
    ).fetchone()
    print(f"  table abp_corrections: {'exists' if has_table else 'will be created'}")
    if args.apply:
        conn.execute(SCHEMA)

    ins = skip = warn = 0
    for (book, ch, vs, pos, field, src, cor, reason, ref) in ENTRIES:
        key = f"{book} {ch}:{vs} pos {pos} {field}"
        # validate against the target db: what does the cell hold right now?
        cell = conn.execute(
            f"""SELECT w."{field}" AS val FROM words w JOIN verses v ON v.id=w.verse_id
                WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?""",
            (book, ch, vs, pos)).fetchall()
        if len(cell) != 1:
            tag = f"!! {len(cell)} matching slot(s) — ADJUDICATE before apply"
            warn += 1
        elif cell[0]["val"] == cor:
            tag = "cell=corrected (already hand-fixed — expected on live)"
        elif cell[0]["val"] == src:
            tag = "cell=source (uncorrected — expected on a fresh scratch)"
        else:
            tag = f"!! cell={cell[0]['val']!r} matches NEITHER — ADJUDICATE before apply"
            warn += 1

        dup = None
        if has_table or args.apply:
            dup = conn.execute(
                """SELECT 1 FROM abp_corrections WHERE book=? AND chapter=? AND verse=?
                   AND position=? AND field=? AND status='active'""",
                (book, ch, vs, pos, field)).fetchone()
        if dup:
            print(f"  == {key}: active row already present — not duplicated. [{tag}]")
            skip += 1
            continue
        if args.apply:
            conn.execute(
                """INSERT INTO abp_corrections (book, chapter, verse, position, field,
                       source_value, corrected_value, reason, ledger_ref, applied_at,
                       status, created)
                   VALUES (?,?,?,?,?,?,?,?,?,'ingest','active',?)""",
                (book, ch, vs, pos, field, src, cor, reason, ref, date.today().isoformat()))
        ins += 1
        print(f"  -> {key}: {src!r} -> {cor!r}  [{ref}]  {tag}")

    if args.apply:
        conn.commit()
        n = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='active'").fetchone()[0]
        print(f"\n  written. active rows in table now: {n}")
    else:
        print(f"\n  DRY RUN — nothing written. would insert {ins}, skip {skip} duplicate(s).")
    if warn:
        print(f"  !! {warn} entr(ies) flagged above — resolve before trusting --apply.")
    conn.close()
    sys.exit(1 if warn else 0)


if __name__ == "__main__":
    main()
