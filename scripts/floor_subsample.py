#!/usr/bin/env python3
"""
floor_subsample.py — the N=6-7 PAPER REPLAY (ruled at batch-4 selection, 2026-07-10;
pulled forward by JP ruling: runs BEFORE the next floor fires. NO LIVE CHANGE follows
from this report until JP rules on it.)

READ-ONLY on saved lexica_agreement floor files (agreement_<SID>_<prompt>_<ts>.json).
Zero model calls, zero db access, pure computation.

WHAT IT TESTS — and the printed limit that governs reading it:
  For each saved 10-run floor, replay every 7-of-10 draw subset (C(10,7) = 120) and ask
  whether the machine-computable structure reproduces:
    (a) the CONSENSUS-PAIR SET — verse pairs co-shelved in a strict majority of draws
        (>= 6/10 baseline, >= 4/7 subset), computed by build_lexica_def.consensus_pairs,
        the SAME code path the live #30 detector reads through (one copy ever, #6);
    (b) the MODAL SENSE COUNT — the most-common cited-sense count (senses with >= 1 ref,
        the load_floor shape; ties kept as a set and compared as a set).
  REPRODUCTION CRITERION (reviewer-pinned before results existed, conservative):
    a subset reproduces only on EXACT match of BOTH (a) and (b). A subset that flips
    STABLE-shaped structure to anything else counts as a failure to reproduce, even if
    a human might have called it either way.
  CONTROL (audit-tools-must-fail rule): the same criterion runs on every 3-of-10 subset
    (also 120). Live evidence says 3-runs mis-certify (G1244's real 3-run had no mode);
    if the 3-subset reproduction rate is not clearly BELOW the 7-subset rate, this
    checker is not discriminating and its 7-subset numbers must not be trusted.

Report partitions by PROMPT VERSION — V7 and V8 tables are never blended; only the V8
table touches the N=7 licensing decision (cross-wording inference is the defect the
step-5 session refused).

Usage (on PA, where the floor files live):
  python scripts/floor_subsample.py                      # all ~/bible-db/agreement_*.json
  python scripts/floor_subsample.py file1.json file2.json
"""
import glob
import json
import os
import sys
from collections import Counter
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B

LIMIT_BANNER = (
    "LIMIT — STRUCTURE STABILITY ONLY: this replay tests whether the machine-computable\n"
    "structure (consensus pairs, modal sense count) survives resampling. It cannot and\n"
    "does not test whether any HUMAN adjudication (hole-vs-fold calls, STABLE rulings,\n"
    "ship decisions) would have come out the same. Output is 'structure holds at 7',\n"
    "never 'the ruling holds at 7'."
)


def counts_per_draw(draws):
    """Cited-sense count per draw from the load_floor shape (senses carrying >= 1 ref)."""
    return [len(senses) for senses in draws]


def modal_set(counts):
    """The set of most-common counts (ties kept — compared as a set, stated in the header)."""
    if not counts:
        return frozenset()
    c = Counter(counts)
    top = max(c.values())
    return frozenset(k for k, v in c.items() if v == top)


def replay(draws, k):
    """Replay every k-of-N subset; return (reproduced_both, pairs_ok, mode_ok, total,
    example_failures) against the full-N baseline under the pinned criterion."""
    base_pairs = frozenset(B.consensus_pairs(draws))
    base_mode = modal_set(counts_per_draw(draws))
    total = pairs_ok = mode_ok = both = 0
    examples = []
    for idx in combinations(range(len(draws)), k):
        sub = [draws[i] for i in idx]
        p = frozenset(B.consensus_pairs(sub))
        m = modal_set(counts_per_draw(sub))
        p_match, m_match = (p == base_pairs), (m == base_mode)
        total += 1
        pairs_ok += p_match
        mode_ok += m_match
        both += (p_match and m_match)
        if not (p_match and m_match) and len(examples) < 3:
            lost = sorted(base_pairs - p)[:4]
            gained = sorted(p - base_pairs)[:4]
            examples.append(
                f"      subset draws {tuple(i + 1 for i in idx)}: "
                + ("pairs drifted" if not p_match else "")
                + (f" lost e.g. {lost}" if lost else "")
                + (f" gained e.g. {gained}" if gained else "")
                + ("" if not p_match else " ")
                + (f"mode {sorted(m)} vs baseline {sorted(base_mode)}" if not m_match else "")
            )
    return both, pairs_ok, mode_ok, total, examples


def main():
    paths = sys.argv[1:] or sorted(glob.glob(os.path.expanduser("~/bible-db/agreement_*.json")))
    print("=" * 92)
    print("FLOOR SUBSAMPLE REPLAY — the N=6-7 paper test (zero draws, saved files only)")
    print(LIMIT_BANNER)
    print("=" * 92)
    loaded, skipped = [], []
    for path in paths:
        try:
            floor = B.load_floor(path)
        except SystemExit as e:          # load_floor hard-refuses only on sid mismatch (not passed here)
            skipped.append((path, str(e)))
            continue
        except Exception as e:
            skipped.append((path, f"unreadable: {e}"))
            continue
        meta = floor["meta"]
        if len(floor["draws"]) < 10:
            skipped.append((path, f"only {len(floor['draws'])} draws — not a 10-run, no subsample target"))
            continue
        loaded.append((floor, meta))

    print("\nCORPUS (every file named — the input list is explicit, nothing silent):")
    for floor, meta in loaded:
        print(f"  IN   {meta['file']}  word {meta['strongs']}  prompt {meta['prompt']}  runs {meta['runs']}")
    for path, why in skipped:
        print(f"  SKIP {os.path.basename(path)}  ({why})")
    if not loaded:
        sys.exit("\nno 10-run floor files found — nothing to replay.")

    by_prompt = {}
    for floor, meta in loaded:
        by_prompt.setdefault(meta["prompt"] or "?", []).append((floor, meta))

    for prompt in sorted(by_prompt):
        print("\n" + "=" * 92)
        print(f"PROMPT {prompt.upper()} — this table stands alone; never blend it with another prompt's")
        if prompt != "v8":
            print("  (NOT the live engine's wording — context only; the N=7 licensing decision")
            print("   reads the V8 table alone)")
        print(f"{'word':<8} {'file':<44} {'7-of-10 both':>12} {'pairs':>7} {'mode':>7} {'3-of-10 CONTROL':>16}")
        for floor, meta in by_prompt[prompt]:
            b7, p7, m7, t7, ex7 = replay(floor["draws"], 7)
            b3, _, _, t3, _ = replay(floor["draws"], 3)
            print(f"{meta['strongs']:<8} {meta['file']:<44} {b7:>7}/{t7:<4} {p7:>7} {m7:>7} {b3:>11}/{t3:<4}")
            for line in ex7:
                print(line)
        print("  CONTROL READ: the 3-of-10 column must sit clearly BELOW the 7-of-10 column.")
        print("  If it doesn't, the checker is not discriminating and this table proves nothing.")

    print("\n" + "=" * 92)
    print("Decision this feeds (JP's, not this script's): do escalation floors run 7 draws")
    print("instead of 10? NO LIVE CHANGE until JP rules on this report.")


if __name__ == "__main__":
    main()
