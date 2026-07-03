#!/usr/bin/env python3
"""audit_lexica_flags.py — READ-ONLY. Inspect the uncited-collocation flags across the built Lexica
entries and score them against the ADOPTED flag gate (PMI floor + neighbor stoplist + mutual dedup;
the share cap was dropped — see AUDIT_lexica_rollout.md batch-two-prep #7). Prints every flag with
its columns, the survivors, the near-misses (fail exactly one threshold), and the σάββατον/οὕτω
sanity pair. Writes NOTHING.

Reuses build_lexica_def (occurrences) + lexica_coverage (coverage_audit, FLAG_PMI_MIN, FLAG_STOP,
dedup_mutual) — no reimplemented scan, no second copy of the gate. The gate is POLICY now, not
batch-scoped, so the roster is read live from lexica_def (every built entry), not a hardcoded list.
Pass Strong's numbers as args to restrict to a subset.

  python scripts/audit_lexica_flags.py            # every built entry
  python scripts/audit_lexica_flags.py G4160 G935 # just these
"""
import os
import sys
import json
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import build_lexica_def as B
import lexica_coverage as C

DB = os.path.expanduser("~/bible-db/bible.db")

# The gate is imported from the engine so this tool can never drift from what actually ships.
PMI_MIN = C.FLAG_PMI_MIN            # collocation flag floor (5.0)
STOP = C.FLAG_STOP                  # flag-stoplisted neighbors (οὕτω G3779, ὅσος G3745, …)
# The share cap was DROPPED from the gate (0 drops on frequent words, inverts on the rare-word tail).
# It is still COMPUTED and shown as a column for the frequency-conditioned revisit, but never gates.

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
conn.create_function("strip_accents", 1, B.strip_accents)

nums = [n if n[:1] in ("G", "H") else "G" + n for n in sys.argv[1:]]
if not nums:
    nums = [r["strongs"] for r in
            conn.execute("SELECT strongs FROM lexica_def ORDER BY strongs").fetchall()]

flags = []
for sid in nums:
    row = conn.execute("SELECT def_json FROM lexica_def WHERE strongs=?", (sid,)).fetchone()
    if not row:
        continue
    d = json.loads(row["def_json"])
    occs = B.occurrences(conn, *B.abp_filter(conn, sid))
    vc = len({o["vid"] for o in occs}) or 1                       # target verse count = share denominator
    ca = C.coverage_audit(conn, sid, occs,
                          entry_refs=B.cited_refs(d.get("raw", "")),
                          sense_specs=B.sense_specs(d.get("senses_block", "")),
                          contest_verses=None, is_contested=False)
    for c in ca["collocations"]:
        if c["cited"]:
            continue                                             # only the UNCITED flags
        flags.append({"target": sid, "tlem": d.get("lemma", sid), "neighbor": c["neighbor"],
                      "nlem": c["lemma"], "ntr": c["translit"], "pmi": c["score"],
                      "v": c["verses"], "share": c["verses"] / vc, "reasons": []})

# ── gate: PMI floor + stoplist, then report-time mutual dedup (the shared engine helper) ──
for f in flags:
    if f["pmi"] < PMI_MIN:
        f["reasons"].append("pmi")
    if f["neighbor"] in STOP:
        f["reasons"].append("stop")
passed = [f for f in flags if not f["reasons"]]
kept = {(f["target"], f["neighbor"]) for f in C.dedup_mutual(passed)}
for f in passed:
    if (f["target"], f["neighbor"]) not in kept:
        f["reasons"].append("mutual")

def survivor(f):
    return not f["reasons"]

def thr(f):
    return [r for r in f["reasons"] if r in ("pmi", "stop")]

# ── full table ──
flags.sort(key=lambda f: (f["target"], -f["pmi"]))
print(f"\nADOPTED GATE: PMI>={PMI_MIN}  stoplist={sorted(STOP)}  + mutual dedup   "
      f"(share shown, NOT gated)\n")
hdr = f'{"TARGET":<14}{"NEIGHBOR":<20}{"PMI":>6}{"V":>5}{"SHARE":>7}  {"STOP":<4}{"MUT":<4}VERDICT'
print(hdr)
print("-" * (len(hdr) + 6))
for f in flags:
    verdict = "SURVIVE" if survivor(f) else "drop:" + ",".join(f["reasons"])
    print(f'{f["tlem"][:13]:<14}{(f["nlem"] + " " + f["ntr"])[:19]:<20}'
          f'{f["pmi"]:>6.2f}{f["v"]:>5}{f["share"]:>6.1%}  '
          f'{"Y" if f["neighbor"] in STOP else "·":<4}'
          f'{"Y" if "mutual" in f["reasons"] else "·":<4}{verdict}')

# ── totals ──
from collections import Counter
n_surv = sum(survivor(f) for f in flags)
drops = Counter()
for f in flags:
    for r in f["reasons"]:
        drops[r] += 1
print(f'\nTOTAL flags: {len(flags)}   ->  SURVIVE: {n_surv}   DROP: {len(flags) - n_surv}')
print(f'  dropped-by: pmi={drops["pmi"]}  stop={drops["stop"]}  mutual={drops["mutual"]}')

# ── near-misses: fail exactly one threshold ──
near = [f for f in flags if len(thr(f)) == 1]
print(f'\nNEAR-MISSES ({len(near)}) — fail exactly one threshold:')
for f in near:
    print(f'  {f["tlem"][:13]:<14}{(f["nlem"] + " " + f["ntr"])[:19]:<20}'
          f'{f["pmi"]:>6.2f}{f["v"]:>5}{f["share"]:>6.1%}   fails: {thr(f)[0]}')

# ── sanity rows ──
print("\nSANITY (should: σάββατον/ἕβδομος survive, οὕτω/ὅσος die):")
watch = {"G4521": "σάββατον", "G1442": "ἕβδομος", "G3779": "οὕτω", "G3745": "ὅσος"}
for base, name in watch.items():
    hits = [f for f in flags if f["neighbor"] == base]
    if not hits:
        print(f'  {name} ({base}): not flagged (already cited, below floor, or absent)')
    for f in hits:
        print(f'  {name} under {f["tlem"]}: PMI {f["pmi"]:.2f}  share {f["share"]:.1%}  '
              f'-> {"SURVIVE" if survivor(f) else "drop:" + ",".join(f["reasons"])}')
conn.close()
