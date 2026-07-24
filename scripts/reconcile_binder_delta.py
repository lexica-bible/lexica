#!/usr/bin/env python3
"""reconcile_binder_delta.py — R-2 stage-1 gate: itemize the binder dry-run's movement.

Read-only. Compares the OLD pn_binding_numonly.txt / pn_binding_hot.txt (the committed
R-1 versions, read from git) against the NEW ones the dry-run just wrote, and checks
every DEPARTED number-only row against the 206 accepted binder pairs
(docs/tickets/variant_batch_binder_verdicts.txt). The reviewer's standard: recovered
rows trace to accepted pairs; anything unexplained stops the sequence.

Usage (PA, after the build_entity_binding dry-run):
  python3 scripts/reconcile_binder_delta.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def rows(text):
    out = set()
    for ln in text.splitlines():
        if ln.strip():
            out.add(ln.rstrip("\n"))
    return out


def git_head(path):
    return subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{path}"],
                          capture_output=True, text=True, check=True).stdout


def names_of(rowset):
    return {ln.split("\t")[0].strip() for ln in rowset}


old_num = rows(git_head("scripts/pn_binding_numonly.txt"))
new_num = rows(open(os.path.join(HERE, "pn_binding_numonly.txt"), encoding="utf-8").read())
old_hot = rows(git_head("scripts/pn_binding_hot.txt"))
new_hot = rows(open(os.path.join(HERE, "pn_binding_hot.txt"), encoding="utf-8").read())

accepted = set()
for ln in open(os.path.join(ROOT, "docs", "tickets",
                            "variant_batch_binder_verdicts.txt"), encoding="utf-8"):
    if ln.startswith("#") or not ln.strip():
        continue
    parts = [p.strip() for p in ln.split("|")]
    if len(parts) >= 5 and parts[4].startswith("ACCEPT"):
        accepted.add(parts[1].lower())

departed = old_num - new_num
arrived = new_num - old_num
print(f"number-only rows: {len(old_num)} -> {len(new_num)} "
      f"(departed {len(departed)}, NEW {len(arrived)})")
print(f"hot rows        : {len(old_hot)} -> {len(new_hot)} "
      f"(departed {len(old_hot - new_hot)}, NEW {len(new_hot - old_hot)})\n")

dep_ok = sorted(n for n in names_of(departed) if n.lower() in accepted)
dep_bad = sorted(n for n in names_of(departed) if n.lower() not in accepted)
print(f"departed number-only names tracing to ACCEPTED pairs: {len(dep_ok)}")
print(f"departed names NOT on the accepted list (must be explained): {len(dep_bad)}")
for n in dep_bad:
    for ln in sorted(departed):
        if ln.split("\t")[0].strip() == n:
            print("   ?", ln)

print(f"\nNEW number-only rows (must be zero or explained): {len(arrived)}")
for ln in sorted(arrived)[:50]:
    print("   +", ln)
new_hot_rows = new_hot - old_hot
print(f"NEW hot rows (must be zero or explained): {len(new_hot_rows)}")
for ln in sorted(new_hot_rows)[:50]:
    print("   +", ln)

fail = bool(dep_bad or arrived or new_hot_rows)
print("\nRECONCILE:", "UNEXPLAINED MOVEMENT — STOP" if fail else "CLEAN — every move traces")
sys.exit(1 if fail else 0)
