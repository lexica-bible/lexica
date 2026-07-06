#!/usr/bin/env python3
"""control_malformed_bracket_fix.py — KNOWN-POSITIVE control for the S10 Option A
malformed-bracket fix (build_words_from_abp.py). No bible.db.

Drives the 3 pre-registered verses' real bracket slots through the ACTUAL v2 reader
logic (scripts/reorder_english.get_english_order_words) both ways:
  PRE-FIX  — malformed slots have greek_pos=None, bracket_id=None -> raw Greek order
             (the wrong reading the build currently emits).
  POST-FIX — the fix tags them as one bracket and keeps greek_pos = the source digit
             -> the reader orders by digit and floats trailing punct to the reading-
             last word.
Asserts POST-FIX == the corrected reading from AUDIT_tierB_f_proposed.json, and that
PRE-FIX != it (so the control can actually fail). A BARE stray ']' (Zec 10:3) carries
no digit, so the scan already routes it to skip — noted, not reordered here.

Run locally:
  python3 scripts/control_malformed_bracket_fix.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reorder_english import prose_sequence

BID = 9  # any non-None id; only same-vs-different matters to the reader

# Each verse's malformed group as (greek_pos_digit, english) in STORED (Greek/source)
# position order — taken verbatim from the live word-row + source-feed dumps.
CASES = [
    ("Mat 21:19",
     [(4, "dried up"), (1, "immediately"), (2, "the"), (3, "fig-tree.")],
     ["immediately", "the", "fig-tree", "dried up."]),
    ("1Ch 22:15",
     [(3, "in"), (4, "multitude"), (1, "doing"), (2, "the works")],
     ["doing", "the works", "in", "multitude"]),
    ("Job 24:19",
     [(6, "upon"), (7, "the earth"), (5, "dry;")],
     ["dry", "upon", "the earth;"]),
]

ok = True
for ref, group, expected in CASES:
    pre = [{"bracket_id": None, "greek_pos": None, "english": e} for _, e in group]
    post = [{"bracket_id": BID, "greek_pos": g, "english": e} for g, e in group]
    pre_read = prose_sequence(pre)
    post_read = prose_sequence(post)
    fires = pre_read != expected          # the fix actually changes something
    correct = post_read == expected       # and changes it to the source order
    ok = ok and fires and correct
    print(f"=== {ref} ===")
    print(f"  PRE-FIX  reading (wrong): {pre_read}")
    print(f"  POST-FIX reading        : {post_read}")
    print(f"  expected (from oracle)  : {expected}")
    print(f"  -> {'FIRED + CORRECT' if (fires and correct) else 'FAIL !!'}\n")

print("Zec 10:3: bare stray ']' (no digit) -> scan routes to SKIP; not reordered here.")
print(f"\n=> {'PASS — Option A reorders exactly the 3, to source order.' if ok else 'FAIL.'}")
sys.exit(0 if ok else 1)
