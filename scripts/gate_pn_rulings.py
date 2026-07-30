#!/usr/bin/env python3
"""gate_pn_rulings.py — pre-swap gates for the Jacob-class hand-rulings arc
(reviewer-approved 2026-07-30). READ-ONLY on BOTH database files.

Expected delta = scripts/pn_hand_rulings.tsv (kind='ruled') + lane-A rows of
docs/tickets/witness_census_lanes.txt (kind='witness', since 2026-07-30):
  gate A  pn_binding: scratch = live + EXACTLY the ruled keys, nothing else changed —
          every new row has kind='ruled' and the TSV's entity; an extra bind (the
          82nd), a lost row, or a modified row = FAIL/abort.
  gate B  tipnr_entities byte-identical live vs scratch (rulings touch binds only).
  gate C  tipnr_entity_refs row count unchanged.

CONTROL (run FIRST, audit-tools-must-fail): point both arguments at the LIVE file —
gate A must FAIL (unlanded > 0 vs the TSV's expected set), gates B/C must PASS.
STANDING METHOD: post-swap served-layer captures are only valid AFTER the deploy.sh
worker reload (swap -> reload -> capture).
STANDING METHOD (batch-2 lesson, reviewer-ruled): ANY checker edit mid-arc requires
the control re-run BEFORE the fixed checker's PASS counts — the detector-control
discipline applies to the detector itself.

Usage: python3 scripts/gate_pn_rulings.py <live.db> <scratch.db>
"""
import os, sys, sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

if len(sys.argv) != 3:
    sys.exit("usage: gate_pn_rulings.py <live.db> <scratch.db>")
live = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
scr = sqlite3.connect(f"file:{sys.argv[2]}?mode=ro", uri=True)

# expected delta = hand rulings (kind='ruled') + witness lane A (kind='witness').
# The two classes are pinned SEPARATELY: an added row must carry its own class's
# kind — a ruled row can never silently become witness or vice versa (reviewer
# verdict 2026-07-30, the free invariant of the first-class bind type).
tsv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pn_hand_rulings.tsv")
expected = {}   # key -> (uniq, kind)
for ln in open(tsv, encoding="utf-8"):
    if ln.startswith("#") or ln.startswith("name\t") or not ln.strip():
        continue
    nm, bk_s, ch, vs, uniq, ev = ln.rstrip("\n").split("\t")[:6]
    expected[(er.book_num(bk_s), int(ch), int(vs), er.norm_name(nm))] = (uniq, "ruled")
n_ruled = len(expected)
wit = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "tickets", "witness_census_lanes.txt")
if os.path.isfile(wit):
    for ln in open(wit, encoding="utf-8"):
        if ln.startswith("#") or not ln.strip():
            continue
        lane, nm, bk_s, ch, vs, detail = ln.rstrip("\n").split("|")[:6]
        if lane != "A":
            continue
        expected[(er.book_num(bk_s), int(ch), int(vs), er.norm_name(nm))] = (detail, "witness")
print(f"expected: {n_ruled} ruled + {len(expected) - n_ruled} witness = {len(expected)}")

q = "SELECT book, chapter, verse, name, entity_uniq, kind, rule, render, hot, tier FROM pn_binding"
lrows = {(r[0], r[1], r[2], r[3]): r for r in live.execute(q)}
srows = {(r[0], r[1], r[2], r[3]): r for r in scr.execute(q)}

fails = []
added = {k: srows[k] for k in srows if k not in lrows}
removed = [k for k in lrows if k not in srows]
changed = [k for k in lrows if k in srows and srows[k] != lrows[k]]
bad_added = [k for k in added if k not in expected
             or added[k][4] != expected[k][0] or added[k][5] != expected[k][1]
             or added[k][7] != 1]
missing = [k for k in expected if k not in added and k not in lrows]

# A ruled key already live in the OLD file adds nothing (batch-1 rows on a batch-2
# run) — the bar is: every TSV key landed (live-or-added), every ADDED key is a TSV
# key with correct content, nothing removed, nothing modified. (The original
# added==len(expected) form was only right when live held zero rulings; it FAILed
# spuriously on batch 2 — 2026-07-30.)
already_live = sum(1 for k in expected if k in lrows)
okA = not (bad_added or removed or changed or missing)
print(f"gate A: {'PASS' if okA else 'FAIL'} — TSV keys {len(expected)} "
      f"(already live {already_live}, newly added {len(added)}), "
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
