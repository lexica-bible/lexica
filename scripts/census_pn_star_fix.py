#!/usr/bin/env python3
"""Read-only census grounding the lane-2 fix predicate (PN-star merged-verb).

Imports the committed detector's sweep + the build's own ruling-10 attestation
map — no copies, no database. Measures, per hit:

  Class A (star carries "scourging Jesus,"; blank numbered neighbour):
    - which gloss words are roster-name words (the star's OWN) vs moved
    - straddle vs clean split (_slot_order)
    - whether EVERY moved word is ren-attested for the blank neighbour's base
    - name-word count (0 names on a class-A star = its own bucket)

  Class B (carrier "Jesus finished"; empty star):
    - which carrier words are roster names (the run that would move to the star)
    - straddle vs clean split
    - whether every KEPT (non-name) word is ren-attested for the carrier's base
"""
import io, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from audit_pn_star_verb_merge import sweep, name_roster
from build_words_from_abp import build_attestation_map, _slot_order, _SLOT_NORM
from entity_resolution import norm_name

def word_split(eng, names):
    """(name_idx, other_idx) over eng.split()."""
    name_idx, other_idx = [], []
    for gi, w in enumerate(eng.split()):
        n = norm_name(_SLOT_NORM.sub("", w))
        (name_idx if n in names else other_idx).append(gi)
    return name_idx, other_idx

def norms(eng, idxs):
    ws = eng.split()
    return [w for w in (_SLOT_NORM.sub("", ws[k]).lower() for k in idxs) if w]

def main():
    names = name_roster()
    print("building attestation map (ruling-10 ren, min_verses=5)...", flush=True)
    ren = build_attestation_map()
    hits = sweep()
    a = [h for h in hits if h[0] == "A"]
    b = [h for h in hits if h[0] == "B"]

    # ---- class A ----
    ca = collections.Counter()
    ex = collections.defaultdict(list)
    for cls, fn, bk, ch, vs, eng, numstr in a:
        name_idx, other_idx = word_split(eng, names)
        blanks = numstr.split(",")
        if not name_idx:
            ca["A: no roster name on the star"] += 1
            ex["A: no roster name on the star"].append((bk, ch, vs, eng, numstr))
            continue
        if not other_idx:
            ca["A: all words are names (nothing to move)"] += 1
            ex["A: all words are names (nothing to move)"].append((bk, ch, vs, eng, numstr))
            continue
        if _slot_order(name_idx, other_idx) is None:
            ca["A: STRADDLE"] += 1
            ex["A: STRADDLE"].append((bk, ch, vs, eng, numstr))
            continue
        if len(blanks) > 1:
            ca["A: clean split, 2+ blank neighbours"] += 1
            ex["A: clean split, 2+ blank neighbours"].append((bk, ch, vs, eng, numstr))
            continue
        base = blanks[0][1:].split(".")[0]
        moved = norms(eng, other_idx)
        att = ren.get(base, frozenset())
        if moved and all(w in att for w in moved):
            ca["A: clean split, 1 blank, ATTESTED"] += 1
            ex["A: clean split, 1 blank, ATTESTED"].append((bk, ch, vs, eng, numstr))
        else:
            ca["A: clean split, 1 blank, unattested"] += 1
            ex["A: clean split, 1 blank, unattested"].append((bk, ch, vs, eng, numstr))

    # ---- class B ----
    cb = collections.Counter()
    for cls, fn, bk, ch, vs, eng, numstr in b:
        nums = numstr.split(",")
        carrier_num = nums[0]
        between = nums[1:]
        name_idx, other_idx = word_split(eng, names)
        if not name_idx:
            cb["B: no roster name on carrier (=B2)"] += 1
            ex["B: no roster name on carrier (=B2)"].append((bk, ch, vs, eng, numstr))
            continue
        if not other_idx:
            cb["B: carrier is ALL name words"] += 1
            ex["B: carrier is ALL name words"].append((bk, ch, vs, eng, numstr))
            continue
        if _slot_order(other_idx, name_idx) is None:
            cb["B: STRADDLE"] += 1
            ex["B: STRADDLE"].append((bk, ch, vs, eng, numstr))
            continue
        base = carrier_num[1:].split(".")[0]
        kept = norms(eng, other_idx)
        att = ren.get(base, frozenset())
        key = "B: clean split, kept words ATTESTED for carrier" if (
            kept and all(w in att for w in kept)) else \
            "B: clean split, kept words unattested for carrier"
        if between:
            key += " (+intervening blanks)"
        cb[key] += 1
        ex[key].append((bk, ch, vs, eng, numstr))

    print("\nCLASS A (%d)" % len(a))
    for k, v in sorted(ca.items()):
        print("  %-52s %5d" % (k, v))
    print("\nCLASS B (%d)" % len(b))
    for k, v in sorted(cb.items()):
        print("  %-52s %5d" % (k, v))
    print("\n--- examples (up to 6 each) ---")
    for k in list(sorted(ca)) + list(sorted(cb)):
        print("\n[%s]" % k)
        for e in ex[k][:6]:
            print("   %s %d:%d  %r  %s" % e)

if __name__ == "__main__":
    main()
