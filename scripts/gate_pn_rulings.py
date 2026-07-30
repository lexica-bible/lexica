#!/usr/bin/env python3
"""gate_pn_rulings.py — pre-swap gates for the Jacob-class hand-rulings arc
(reviewer-approved 2026-07-30). READ-ONLY on BOTH database files.

Expected delta is read from scripts/pn_hand_rulings.tsv itself (81 rows at approval):
  gate A  pn_binding: scratch = live + EXACTLY the ruled keys, nothing else changed —
          every new row has kind='ruled' and the TSV's entity; an extra bind (the
          82nd), a lost row, or a modified row = FAIL/abort.
  gate B  tipnr_entities byte-identical live vs scratch (rulings touch binds only).
  gate C  tipnr_entity_refs row count unchanged.

CONTROL (run FIRST, audit-tools-must-fail): point both arguments at the LIVE file —
gate A must FAIL (0 new rows vs the TSV's expected set), gates B/C must PASS.
STANDING METHOD: post-swap served-layer captures are only valid AFTER the deploy.sh
worker reload (swap -> reload -> capture).

Usage: python3 scripts/gate_pn_rulings.py <live.db> <scratch.db>
"""
import os, sys, sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

if len(sys.argv) != 3:
    sys.exit("usage: gate_pn_rulings.py <live.db> <scratch.db>")
live = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
scr = sqlite3.connect(f"file:{sys.argv[2]}?mode=ro", uri=True)

tsv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pn_hand_rulings.tsv")
expected = {}
for ln in open(tsv, encoding="utf-8"):
    if ln.startswith("#") or ln.startswith("name\t") or not ln.strip():
        continue
    nm, bk_s, ch, vs, uniq, ev = ln.rstrip("\n").split("\t")[:6]
    expected[(er.book_num(bk_s), int(ch), int(vs), er.norm_name(nm))] = (uniq, ev)
print(f"TSV expected ruled binds: {len(expected)}")

q = "SELECT book, chapter, verse, name, entity_uniq, kind, rule, render, hot, tier FROM pn_binding"
lrows = {(r[0], r[1], r[2], r[3]): r for r in live.execute(q)}
srows = {(r[0], r[1], r[2], r[3]): r for r in scr.execute(q)}

fails = []
added = {k: srows[k] for k in srows if k not in lrows}
removed = [k for k in lrows if k not in srows]
changed = [k for k in lrows if k in srows and srows[k] != lrows[k]]
bad_added = [k for k in added if k not in expected
             or added[k][4] != expected[k][0] or added[k][5] != "ruled" or added[k][7] != 1]
missing = [k for k in expected if k not in added and k not in lrows]

okA = (len(added) == len(expected) and not bad_added and not removed
       and not changed and not missing)
print(f"gate A: {'PASS' if okA else 'FAIL'} — added {len(added)} (expect {len(expected)}), "
      f"wrong-content {len(bad_added)}, removed {len(removed)}, modified {len(changed)}, "
      f"unlanded rulings {len(missing)}")
if not okA:
    for k in (bad_added + removed + changed + missing)[:8]:
        print(f"    problem key: {k}")
    fails.append("A")

COLS = "uniq,head,section,gender,area,descr,summary,bases,parents,offspring"
le = list(live.execute(f"SELECT {COLS} FROM tipnr_entities ORDER BY uniq"))
se = list(scr.execute(f"SELECT {COLS} FROM tipnr_entities ORDER BY uniq"))
okB = le == se
print(f"gate B: {'PASS' if okB else 'FAIL'} — tipnr_entities {len(le):,} vs {len(se):,} rows, "
      + ("byte-identical" if okB else "DIFFER"))
if not okB:
    fails.append("B")

lr = live.execute("SELECT count(*) FROM tipnr_entity_refs").fetchone()[0]
sr = scr.execute("SELECT count(*) FROM tipnr_entity_refs").fetchone()[0]
okC = lr == sr
print(f"gate C: {'PASS' if okC else 'FAIL'} — refs {lr:,} vs {sr:,}")
if not okC:
    fails.append("C")

print()
if fails:
    print(f"FAILED gates: {fails} — ABORT, discard the scratch copy.")
    sys.exit(1)
print("Gates A/B/C all PASS. Swap on verdict, reload, then served-layer spot checks.")
