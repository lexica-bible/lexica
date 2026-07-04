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
  * L2 (1Sa 6:11) + L10 (Mal 3:6) — 4 cells each (Session 5). Both source files
    (abp_texts AND bh_scrape) dropped a Strong's number, leaving a bare "G" the build
    turned into junk (a glued gloss / a stray word / a polluted english_head search
    key). Restored from the OFFICIAL ABP app (apostolicbibleapp.com) — the living
    authoritative Van der Pool text, the standing witness for source-reading
    adjudications. UNLIKE Cushi/Jer these were NOT hand-fixed on live first, so the
    dry-run reads "cell=source" and apply_abp_corrections.py --apply must run against
    live after build --apply to clean the reader-visible defect.
L5 (the null-form "this/these" rows) lands later — its list was under-specified and
must be re-derived first (Session 6), then read against the same ABP app.

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
_L2_REASON = ("ABP source (abp_texts AND bh_scrape) dropped the Strong's number on the "
              "'buttocks' word (edron) — printed a bare 'G'; the build folded the next tag "
              "G1473 (auton, 'their') onto the slot and glued 'G' into the gloss + the "
              "english_head search key. Restored to G1475.3 (attested 3x same-chapter: 1Sa "
              "5:9 / 5:12 / 6:5) and confirmed by the official ABP app (apostolicbibleapp.com) "
              "1Sa 6:11 = 1475.3-1473. L2.")
_L10_REASON = ("ABP source dropped the Strong's number on the verb 'change' (elloiomai) — a "
               "bare trailing 'G' (bh_scrape shows a dangling '3756-'), which the build "
               "emitted as a stray word with a 'g' english_head. Restored to G241.2 (ouk "
               "G3756 stays on pos 6) per the official ABP app (apostolicbibleapp.com) Mal "
               "3:6. L10.")

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
    # L2 — 1Sa 6:11 pos 21 (Session 5; defect still live, apply after build --apply)
    ("1Sa",  6, 11, 21, "strongs",      "1473",                "1475.3",             _L2_REASON,  "L2"),
    ("1Sa",  6, 11, 21, "strongs_base", "G1473",               "G1475",              _L2_REASON,  "L2"),
    ("1Sa",  6, 11, 21, "english",      "of their buttocks.G", "of their buttocks.", _L2_REASON,  "L2"),
    ("1Sa",  6, 11, 21, "english_head", "buttocksg",           "buttocks",           _L2_REASON,  "L2"),
    # L10 — Mal 3:6 pos 7, the stray verb slot (Session 5; defect still live)
    ("Mal",  3,  6,  7, "strongs",      "",   "241.2", _L10_REASON, "L10"),
    ("Mal",  3,  6,  7, "strongs_base", "",   "G241",  _L10_REASON, "L10"),
    ("Mal",  3,  6,  7, "english",      "G",  "",      _L10_REASON, "L10"),
    ("Mal",  3,  6,  7, "english_head", "g",  "",      _L10_REASON, "L10"),
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
