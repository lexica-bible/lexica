#!/usr/bin/env python3
"""gate_tipnr_scope_widen.py — pre-swap gates for the TIPNR scope-widening scratch run
(reviewer-final list, TODO.md 2026-07-30). READ-ONLY on BOTH database files.

Automates gates 3, 4, 5, 9. Gates 1/2/6 run separately (procedure in TODO.md);
gates 7/8 are post-swap served-layer checks.

STANDING METHOD (reviewer, 2026-07-30 close-out): post-swap served-layer captures are
only valid AFTER the deploy.sh worker reload — workers keep the OLD file open across a
file move, so a pre-reload capture mixes stale answers (Achsah episode). Order is always:
swap -> reload -> capture.

  gate 3  every live tipnr_entities row survives BYTE-IDENTICAL in scratch (full
          diff, all 10 columns, no sampling)
  gate 4  pn_binding byte-identical live vs scratch — ANY diff = FAIL (abort, not warn)
  gate 5  scratch tipnr_entities = 4,247 total AND split person/place/other =
          3,132 / 1,013 / 102 (pre-registered from the local parse of the pinned file)
  gate 9  scratch tipnr_entity_refs = 31,975 rows (pre-registered from the same parse)

CONTROL (run FIRST, per the audit-tools-must-fail rule): point both arguments at the
LIVE file. Gates 3+4 must PASS (a file equals itself) and gate 5 must FAIL (live holds
2,355, not 4,247) — that proves the count detector fires. Then run live vs scratch.

Usage: python3 scripts/gate_tipnr_scope_widen.py <live.db> <scratch.db>
Exit 0 only when every automated gate passes.
"""
import sys, sqlite3

if len(sys.argv) != 3:
    sys.exit("usage: gate_tipnr_scope_widen.py <live.db> <scratch.db>")

live = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
scr  = sqlite3.connect(f"file:{sys.argv[2]}?mode=ro", uri=True)

EXPECT_TOTAL = 4247
EXPECT_SPLIT = {"person": 3132, "place": 1013, "other": 102}
EXPECT_REFS  = 31975

COLS = "uniq,head,section,gender,area,descr,summary,bases,parents,offspring"
fails = []

def gate(n, ok, detail):
    print(f"gate {n}: {'PASS' if ok else 'FAIL'} — {detail}")
    if not ok:
        fails.append(n)

# ── gate 3: superset, byte-identical ─────────────────────────────────────────
live_rows = {r[0]: r for r in live.execute(f"SELECT {COLS} FROM tipnr_entities")}
scr_rows  = {r[0]: r for r in scr.execute(f"SELECT {COLS} FROM tipnr_entities")}
missing = [u for u in live_rows if u not in scr_rows]
changed = [u for u in live_rows if u in scr_rows and scr_rows[u] != live_rows[u]]
gate(3, not missing and not changed,
     f"{len(live_rows):,} live rows: {len(missing)} missing, {len(changed)} changed in scratch"
     + (f"  e.g. {sorted(missing + changed)[:5]}" if missing or changed else ""))

# ── gate 4: pn_binding byte-identical (ABORT class) ──────────────────────────
q = "SELECT * FROM pn_binding ORDER BY book, chapter, verse, name, entity_uniq"
a, b = live.execute(q).fetchall(), scr.execute(q).fetchall()
gate(4, a == b, f"live {len(a):,} rows vs scratch {len(b):,} rows"
     + ("" if a == b else "  << ANY diff here = full abort, scratch discarded"))

# ── gate 5: total + tier split ───────────────────────────────────────────────
split = dict(scr.execute("SELECT section, count(*) FROM tipnr_entities GROUP BY section"))
total = sum(split.values())
gate(5, total == EXPECT_TOTAL and split == EXPECT_SPLIT,
     f"scratch total {total:,} (expect {EXPECT_TOTAL:,}); split {split} (expect {EXPECT_SPLIT})")

# ── gate 9: refs row count ───────────────────────────────────────────────────
nrefs = scr.execute("SELECT count(*) FROM tipnr_entity_refs").fetchone()[0]
gate(9, nrefs == EXPECT_REFS, f"scratch refs {nrefs:,} (expect {EXPECT_REFS:,})")

print()
if fails:
    print(f"FAILED gates: {fails} — ABORT, discard the scratch copy. No partial fixes inside the run.")
    sys.exit(1)
print("Automated gates 3/4/5/9 all PASS. Continue with gates 2 and 6, then paste "
      "everything for the swap verdict.")
