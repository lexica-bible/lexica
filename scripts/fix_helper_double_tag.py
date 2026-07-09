#!/usr/bin/env python3
"""
One-time live-table patch for the polarity-A helper double-tag defect
(CHARTER_splitter_fix.md). The permanent fix is the builder rule
(_strip_helper_double_tag in build_words_from_abp.py); this script applies the
same strip to the CURRENT bible.db so the fix doesn't wait for a full rebuild.

Belt-and-braces: it re-runs the live fingerprint scan AND requires the result
to match the PINNED list (scripts/splitter_a_expected.tsv — the source-derived
607, diffed empty against the table 2026-07-09) row for row. Any asymmetry in
either direction aborts with the differences printed, before anything writes.

Default is DRY-RUN (read-only). --apply writes, one UPDATE per identified row:
    strongs='', strongs_base='', greek_pos=NULL   (english/head untouched —
the row keeps its word as plain untagged text, the shape the builder itself
stores for untagged source text).

Usage on PA (backup FIRST — scripts/backup_db.py):
    python3 scripts/fix_helper_double_tag.py            # dry-run
    python3 scripts/fix_helper_double_tag.py --apply    # after JP's checkpoint OK
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_helper_double_tag import load_words, build_rendering_sets, scan  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(HERE), "bible.db")
PINNED = os.path.join(HERE, "splitter_a_expected.tsv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    with open(PINNED, encoding="utf-8") as f:
        pinned = {tuple(line.rstrip("\n").split("\t")) for line in f if line.strip()}
    print(f"Pinned list: {len(pinned)} rows ({PINNED})")

    ro = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    verses, ref = load_words(ro)
    ren = build_rendering_sets(verses)
    a_clean, _a_review, _b = scan(verses, ref, ren)
    ro.close()

    live = {(r[0], (r[2] or "").strip(), f"G{r[4]}") for r in a_clean}
    targets = [(r[0], r[1], r[2], r[4]) for r in a_clean]  # (ref, pos, eng, strongs)

    only_live = sorted(live - pinned)
    only_pinned = sorted(pinned - live)
    if only_live or only_pinned:
        print("MISMATCH between the live scan and the pinned list — ABORTING, nothing written.")
        for r in only_live:
            print(f"  live-only:   {r}")
        for r in only_pinned:
            print(f"  pinned-only: {r}")
        sys.exit(1)
    print(f"Live scan matches the pinned list exactly: {len(live)} rows.")

    if not args.apply:
        print("DRY-RUN — no changes made. Re-run with --apply after checkpoint approval.")
        return

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=10000")
    # ref -> verse_id, rebuilt the same way load_words built ref
    vid_of = {}
    for vid, book, ch, vs in conn.execute("SELECT id, book, chapter, verse FROM verses"):
        vid_of[f"{book} {ch}:{vs}"] = vid

    changed = 0
    for refstr, pos, eng, st in targets:
        cur = conn.execute(
            "UPDATE words SET strongs='', strongs_base='', greek_pos=NULL"
            " WHERE verse_id=? AND position=? AND strongs=?",
            (vid_of[refstr], pos, st),
        )
        if cur.rowcount != 1:
            conn.rollback()
            print(f"ABORT: {refstr} pos {pos} G{st} matched {cur.rowcount} rows (expected 1). "
                  "Rolled back — nothing written.")
            sys.exit(1)
        changed += 1
    conn.commit()
    print(f"Applied: {changed} helper rows untagged.")

    for st, want_rows, want_verses in (("2008", 38, 37), ("977", 39, 38)):
        rows, vs = conn.execute(
            "SELECT count(*), count(DISTINCT verse_id) FROM words WHERE strongs=?", (st,)
        ).fetchone()
        mark = "OK" if (rows, vs) == (want_rows, want_verses) else "CHECK FAILED"
        print(f"  G{st}: {rows} tags / {vs} verses (want {want_rows}/{want_verses}) [{mark}]")
    bare = conn.execute(
        "SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'").fetchone()[0]
    print(f"  strongs_base bare-number invariant: {bare} (must be 0)")
    conn.close()


if __name__ == "__main__":
    main()
