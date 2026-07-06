#!/usr/bin/env python3
"""control_act7_3.py — control for the S10 Act 7:3 option-B fix (reorder metadata).
No DB. Drives the REAL Act 7:3 tail slots through the actual v2 reader
(reorder_english.get_english_order_words) both ways and prints the rendered ending.

The fix: give ONLY pos 19 ("to") + pos 20 ("I show") a shared bracket + greek_pos
(I show=1, to=2). "which" (18) and "you!" (21) stay non-bracketed, so they hold
their positions and the bracket group renders between them. Nothing's english /
strongs / greek data moves — each word keeps its own number.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reorder_english import prose_sequence

# Real stored tail (pos 17-21), english + the two columns the reader reads.
def tail(bid19, gp19, bid20, gp20):
    return [
        {"bracket_id": None, "greek_pos": None, "english": "a land"},   # 17
        {"bracket_id": None, "greek_pos": None, "english": "which"},    # 18
        {"bracket_id": bid19, "greek_pos": gp19, "english": "to"},      # 19
        {"bracket_id": bid20, "greek_pos": gp20, "english": "I show"},  # 20
        {"bracket_id": None, "greek_pos": None, "english": "you!"},     # 21
    ]

before = prose_sequence(tail(None, None, None, None))          # current build
after = prose_sequence(tail(1, 2, 1, 1))                        # option B: 19->gpos2, 20->gpos1

expected = ["a land", "which", "I show", "to", "you!"]

print("Act 7:3 ending — reader render:")
print(f"  BEFORE (current): {' '.join(before)}")
print(f"  AFTER  (option B): {' '.join(after)}")
print(f"  EXPECTED         : {' '.join(expected)}")
ok = after == expected and before != expected
print(f"\n  pos 21 'you!' stays last: {after[-1] == 'you!'}")
print(f"  => {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
