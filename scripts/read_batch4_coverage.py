#!/usr/bin/env python3
"""READ-ONLY correlation read — batch-4 shipped cards vs fed-coverage (V9 ruling item 6,
DESIGN_v9_lines.md; JP runs on PA). One row per shipped card: SID, card length, fed count,
cited count, absentees by name. NO writes: bible.db opened read-only, draw files read-only,
no model call, no gate refusal — a report, not a gate.

FED-REF PROVENANCE (reviewer-accepted deviation, on the record): draw records store the fed
COUNT, not the refs. The fed sample recipe is deterministic — no RNG anywhere; ordering roots
in `ORDER BY v.id, w.position` + stable sorts (evidence posted to the reviewer chat,
2026-07-12) — so we REBUILD it with the production functions and TRIPWIRE it: rebuilt count
must equal the record's stored count, or the row prints RECONSTRUCTION MISMATCH and is
EXCLUDED. Determinism is per-database-content: same-count drift from moved data is possible,
which is why every row here carries the RECONSTRUCTION MARKER (fed=REBUILT) into the
correlation table — these fed sets are rebuilt, never the recorded originals (reviewer
labeling condition, same principle as the shape-pinned gate fixture).

Usage (PA):  PYTHONIOENCODING=utf-8 python scripts/read_batch4_coverage.py
"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B

# The seven shipped batch-4 cards; SIDs verified against the audit doc's own entries
# (batch-3 intake roster + step-5 G2665 + reviewer-pick G1516).
SHIPPED = ["G1350", "G4582", "G5281", "G5009", "G2563", "G2665", "G1516"]

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bible.db")


def main():
    conn = sqlite3.connect(f"file:{os.path.abspath(DB)}?mode=ro", uri=True)  # READ-ONLY
    conn.row_factory = sqlite3.Row

    print("SID   | lemma        | raw chars | def_json chars | fed=REBUILT | cited | uncited")
    print("-" * 92)
    for sid in SHIPPED:
        row = conn.execute("SELECT def_json FROM lexica_def WHERE strongs=?", (sid,)).fetchone()
        if not row:
            print(f"{sid} | NO SHIPPED ROW in lexica_def — excluded")
            continue
        entry = json.loads(row["def_json"])
        rec = B.load_draw(sid)
        if rec is None:
            print(f"{sid} | NO DRAW RECORD ({B.draw_path(sid)}) — excluded")
            continue

        # Rebuild the fed sample exactly as the build did (production functions only).
        pred, params = B.abp_filter(conn, sid)
        occs = B.occurrences(conn, pred, params)
        budget = B.dynamic_budget(len(occs))
        sample = B.select_spread(occs, budget)
        sample = B.reserve_collocation_slots(conn, sid, occs, sample)
        have = {f"{o['book']} {o['ch']}:{o['vs']}" for o in sample}
        for ref in rec.get("forced") or []:
            if ref not in have:
                o = next((o for o in occs if f"{o['book']} {o['ch']}:{o['vs']}" == ref), None)
                if o:
                    sample.append(o)

        if len(sample) != rec.get("fed"):
            print(f"{sid} | RECONSTRUCTION MISMATCH — rebuilt fed {len(sample)} != recorded "
                  f"fed {rec.get('fed')} (data moved or non-default budget) — EXCLUDED")
            continue

        fed_keys = [(o["book"], o["ch"], o["vs"]) for o in sample]
        uncited = B.coverage_gate(fed_keys, entry.get("senses_block", ""))
        n_fed = len(set(fed_keys))
        print(f"{sid} | {entry.get('lemma', rec.get('lemma', '?')):<12} | "
              f"{len(entry.get('raw', '')):>9} | {len(row['def_json']):>14} | "
              f"{n_fed:>11} | {n_fed - len(uncited):>5} | "
              f"{', '.join(uncited) if uncited else '(none — full coverage)'}")
    conn.close()
    print("\n(read-only pass — nothing written. fed=REBUILT rows carry the reconstruction "
          "marker into the correlation table. Trimming on a SHIPPED card here is a finding "
          "for JP/reviewer adjudication, rate-sizing only — the 7/15 FINAL + UNTOUCHABLE "
          "count does not move.)")


if __name__ == "__main__":
    main()
