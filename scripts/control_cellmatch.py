#!/usr/bin/env python3
"""control_cellmatch.py — both-directions control for the number-safe correction
comparator (apply_abp_corrections.cellmatch). No DB.

Proves: (1) a number column (greek_pos, stored as a number) now matches its text
source/corrected value — so a correction APPLIES on a true match and still SKIPS on a
mismatch; (2) TEXT columns behave EXACTLY as the old bare '==' did (existing 18 rows
re-verify identically); (3) a blank (NULL) cell stays distinct from ''.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_abp_corrections import cellmatch

# (name, cell_value, target, expected)
CASES = [
    # number column (greek_pos) — the Mat 20:29 case, both directions
    ("num: cell=1 vs source '1'  -> APPLY",    1,   "1", True),
    ("num: cell=1 vs corrected '2' -> not yet", 1,  "2", False),
    ("num: cell=2 vs corrected '2' -> already", 2,  "2", True),
    ("num: cell=5 (drift) vs '1'  -> SKIP",     5,  "1", False),
    ("num: cell=5 (drift) vs '2'  -> SKIP",     5,  "2", False),
    # text columns — must be identical to a bare '=='
    ("text: exact match",        "of their buttocks.G", "of their buttocks.G", True),
    ("text: mismatch",           "the LORD",            "LORD the",            False),
    ("text: empty vs empty",     "",                    "",                    True),
    ("text: 'g' head match",     "buttocksg",           "buttocksg",           True),
    # blank (NULL) cell distinctness
    ("null cell vs '' -> distinct", None, "",  False),
    ("null cell vs None -> equal",  None, None, True),
]

ok = True
for name, cell, target, expected in CASES:
    got = cellmatch(cell, target)
    status = "OK" if got == expected else "FAIL !!"
    if got != expected:
        ok = False
    print(f"  [{status}] {name}   (got {got}, want {expected})")

# text behaviour must equal the OLD comparator (bare ==) on every text/None case
print("\n  text/None parity vs old '==':")
parity = True
for cell, target in [("a", "a"), ("a", "b"), ("", ""), (None, ""), (None, None), ("x", None)]:
    old = (cell == target)
    new = cellmatch(cell, target)
    if old != new:
        parity = False
        print(f"    DIVERGES on ({cell!r},{target!r}): old={old} new={new}")
print("    identical on all text/None cases" if parity else "    !! divergence above")

ok = ok and parity
print(f"\n=> {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
