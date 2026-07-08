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


def audit_word(conn, sid, budget, floor, window, stop, show_all, pmi_min):
    pred, params = B.abp_filter(conn, sid)
    occs = B.occurrences(conn, pred, params)
    if not occs:
        print(f"  {sid}: no occurrences — skip.")
        return None
    # MIRROR INVARIANT (V7): recompute the fed draw EXACTLY as the build does — dynamic budget
    # + collocation slot reservation — or this audit reports a draw the engine never fed.
    if budget is None:
        budget = B.dynamic_budget(len(occs))
    sample = B.select_spread(occs, budget)
    sample = B.reserve_collocation_slots(conn, sid, occs, sample)
    sample_vids = {o["vid"] for o in sample}
    findings = C.scan_collocations(conn, sid, occs, sample_vids, stop=stop,
                                   floor=floor, window=window, pmi_min=pmi_min)
    flagged = C.missed_collocations(findings)

    lemma, translit = B.lex_head(conn, sid)
    print(f"\n{'='*70}\n{sid}  {lemma} ({translit})")
    print(f"  occurrences {len(occs)} | fed draw {len(sample_vids)} verses | "
          f"floor {floor} | window {window} | tightness threshold {pmi_min}")
    print(f"  collocations at/above floor: {len(findings)}   (FLAGGED — tight & draw-missed: {len(flagged)})")

    rows = findings if show_all else flagged
    if not rows:
        print("  ✓ no tight collocation missed by the draw." if not show_all
              else "  (no collocations at/above floor)")
    for f in rows:
        sc = f"{f['score']:5.1f}" if f["score"] is not None else "  -  "
        if f["flagged"]:
            tag = "✗ FLAG "
        elif f["missed"]:
            tag = "· miss "     # draw-missed but below the tightness bar (not flagged)
        else:
            tag = f"in-draw{f['in_draw']:2d}"
        print(f"    {tag} PMI {sc}  {f['neighbor']} {f['lemma']} ({f['translit']})  "
              f"— {f['verses']} verses; e.g. {', '.join(f['examples'][:4])}")
    return {"sid": sid, "findings": findings, "flagged": flagged}


def coverage_word(conn, sid):
    """PIECE B — read the STORED entry (read-only), recompute its coverage_audit, print it. Works on
    any db (current, a backup, or a scratch copy with senses stripped) since it re-derives from the
    stored raw prose + the live occurrences. No model, no write."""
    import json
    row = conn.execute("SELECT def_json FROM lexica_def WHERE strongs=?", (sid,)).fetchone()
    if not row or not row["def_json"]:
        print(f"\n{sid}: no stored entry — skip.")
        return None
    entry = json.loads(row["def_json"])
    raw = entry.get("raw", "")
    senses_block = entry.get("senses_block", "")
    pred, params = B.abp_filter(conn, sid)
    occs = B.occurrences(conn, pred, params)
    cov = C.coverage_audit(
        conn, sid, occs,
        entry_refs=B.cited_refs(raw),
        sense_specs=B.sense_specs(senses_block),
        contest_verses=B.contest_verses(sid),
        is_contested=(sid in B._CONTESTED_BY_SID))

    lemma, translit = B.lex_head(conn, sid)
    colls, rends = cov["collocations"], cov["renderings"]
    cu = [c for c in colls if not c["cited"]]
    print(f"\n{'='*70}\n{sid}  {lemma} ({translit})   [coverage]  contested={cov['contested']}")
    print(f"  tight collocations: {len(colls)} ({len(cu)} UNCITED) | "
          f"top renderings: {len(rends)} ({sum(1 for r in rends if not r['cited'])} uncited)")
    for c in cu:
        print(f"    · collocation UNCITED  {c['neighbor']} {c['lemma']} ({c['translit']})  "
              f"{c['verses']}v  PMI {c['score']}")
    # always print the senses tally so a CLEAN pass is distinguishable from a check that never ran
    senses = cov["senses"]
    circ = [t for t in cov["thin_senses"] if t["self_only"]]
    thin_only = [t for t in cov["thin_senses"] if not t["self_only"]]
    note = "" if cov["contested"] else "  (circular check inert — not a contested word)"
    print(f"  senses: {len(senses)} checked, {len(thin_only)} thin, {len(circ)} circular{note}")
    if cov["contested"]:                       # show each sense's refs + what falls OUTSIDE the locus
        for s in senses:
            out = f"  OUTSIDE: {', '.join(s['outside'])}" if s["outside"] else "  (all inside disputed passage)"
            print(f"    sense {s['sense']} [{s['support_refs']} ref(s)]: {', '.join(s['refs']) or '(none)'}{out}")
    for t in cov["thin_senses"]:
        kind = "CIRCULAR (self-only)" if t["self_only"] else "thin"
        print(f"    · sense {t['sense']} {kind} — {t['support_refs']} support ref(s): {t['headline'][:60]}")
    print(f"  flags: {'; '.join(cov['flags']) if cov['flags'] else '(none — clean)'}")
    return {"sid": sid, "coverage": cov}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number, e.g. G5207")
    ap.add_argument("--all", action="store_true", help="every built word in lexica_def")
    ap.add_argument("--budget", type=int, default=None,
                    help="override; default mirrors the engine's dynamic_budget curve")
    ap.add_argument("--floor", type=int, default=C.COLLOC_FLOOR)
    ap.add_argument("--window", type=int, default=C.COLLOC_WINDOW)
    ap.add_argument("--pmi-min", type=float, default=C.PMI_MIN,
                    help="tightness threshold to flag a missed collocation (calibrate from --show-all)")
    ap.add_argument("--show-all", action="store_true",
                    help="list every collocation at/above floor (with its PMI score), not just flags")
    ap.add_argument("--coverage", action="store_true",
                    help="PIECE B: recompute the STORED entry's coverage_audit (cited-or-not + "
                         "thin/circular senses) read-only — works on a scratch/backup db too")
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

    if args.coverage:
        for sid in targets:
            coverage_word(conn, sid)
        conn.close()
        print(f"\n{'='*70}\nDONE (coverage). {len(targets)} word(s).")
        return

    stop = C.function_bare_strongs(conn)
    print(f"function-word stop-list: {len(stop)} numbers")

    total_flagged = 0
    for sid in targets:
        r = audit_word(conn, sid, args.budget, args.floor, args.window, stop,
                       args.show_all, args.pmi_min)
        if r:
            total_flagged += len(r["flagged"])
    conn.close()
    print(f"\n{'='*70}\nDONE. {len(targets)} word(s); {total_flagged} flagged collocation(s) total.")


if __name__ == "__main__":
    main()
