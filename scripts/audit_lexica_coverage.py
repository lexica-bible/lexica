#!/usr/bin/env python3
"""
audit_lexica_coverage.py — READ-ONLY collocation audit for Lexica dictionary words (PIECE A).

For a target word it recomputes the EXACT fed draw the build uses (select_spread over the word's
real occurrences) and scans ALL occurrences for repeated adjacent-lemma collocations. Any
collocation above the floor with ZERO representatives in the draw is a sampling blind spot — the
model never saw the pattern, so a whole sense can go missing (the G5207 "son of man" case).

  workon bible-env
  python scripts/audit_lexica_coverage.py --word G5207
  python scripts/audit_lexica_coverage.py --word G2316 --floor 10 --window 2
  python scripts/audit_lexica_coverage.py --all              # every built lexica_def word
  python scripts/audit_lexica_coverage.py --word G5207 --show-all   # list all collocs, not just misses

READ-ONLY: opens bible.db mode=ro; only SELECTs. No writes, no model calls. bible.db is PA-only.
"""

import argparse, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The evidence helpers + the draw sampler come from the build script so the audit and the build
# agree by construction (same occurrences, same select_spread).
import build_lexica_def as B
import lexica_coverage as C


def audit_word(conn, sid, budget, floor, window, stop, show_all):
    pred, params = B.abp_filter(conn, sid)
    occs = B.occurrences(conn, pred, params)
    if not occs:
        print(f"  {sid}: no occurrences — skip.")
        return None
    sample = B.select_spread(occs, budget)
    sample_vids = {o["vid"] for o in sample}
    findings = C.scan_collocations(conn, sid, occs, sample_vids, stop=stop, floor=floor, window=window)
    missed = C.missed_collocations(findings)

    lemma, translit = B.lex_head(conn, sid)
    print(f"\n{'='*70}\n{sid}  {lemma} ({translit})")
    print(f"  occurrences {len(occs)} | fed draw {len(sample_vids)} verses | "
          f"floor {floor} | window {window}")
    print(f"  collocations at/above floor: {len(findings)}   (missed by draw: {len(missed)})")

    rows = findings if show_all else missed
    if not rows:
        print("  ✓ no collocation missed by the draw." if not show_all
              else "  (no collocations at/above floor)")
    for f in rows:
        tag = "✗ MISSED" if f["missed"] else f"  in-draw {f['in_draw']}"
        print(f"    {tag}  {f['neighbor']} {f['lemma']} ({f['translit']})  "
              f"— {f['verses']} verses; e.g. {', '.join(f['examples'][:4])}")
    return {"sid": sid, "findings": findings, "missed": missed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number, e.g. G5207")
    ap.add_argument("--all", action="store_true", help="every built word in lexica_def")
    ap.add_argument("--budget", type=int, default=B.BUDGET)
    ap.add_argument("--floor", type=int, default=C.COLLOC_FLOOR)
    ap.add_argument("--window", type=int, default=C.COLLOC_WINDOW)
    ap.add_argument("--show-all", action="store_true",
                    help="list every collocation at/above floor, not just the ones the draw missed")
    args = ap.parse_args()

    if not args.word and not args.all:
        sys.exit("Pass --word G#### or --all.")

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    if args.all:
        if not C._table_exists(conn, "lexica_def"):
            sys.exit("--all needs lexica_def built.")
        targets = [r["strongs"] for r in
                   conn.execute("SELECT strongs FROM lexica_def ORDER BY strongs").fetchall()]
    else:
        w = args.word.upper()
        targets = ["G" + w if w[:1] not in ("G", "H") else w]

    stop = C.function_bare_strongs(conn)
    print(f"function-word stop-list: {len(stop)} numbers")

    total_missed = 0
    for sid in targets:
        r = audit_word(conn, sid, args.budget, args.floor, args.window, stop, args.show_all)
        if r:
            total_missed += len(r["missed"])
    conn.close()
    print(f"\n{'='*70}\nDONE. {len(targets)} word(s); {total_missed} missed collocation(s) total.")


if __name__ == "__main__":
    main()
