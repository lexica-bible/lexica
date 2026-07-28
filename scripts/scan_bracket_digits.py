#!/usr/bin/env python3
"""scan_bracket_digits.py — corpus-wide sweep for the Jer 9:23 defect class:
bracket groups whose ABP order digits are malformed.

Ruled 2026-07-28 (reviewer, after Jer 9:23 closed): the second confirmed marker typo in the
source makes this a class; the class is mechanically detectable, so sweep it once, read-only.

WHAT THIS ADDS vs prior art: scan_malformed_brackets.py catches broken bracket SHELLS
(a stray ']' with no opener). Nothing existing validates the DIGITS inside a well-formed
group. A group whose numbered members carry digits that are not the exact set 1..K
(duplicates, gaps, digits beyond the group) makes the reorder unreliable — the Jer 9:23
signature was [2,1,2] (duplicate 2, missing 3).

HONEST SCOPE (on the record per the ruling): a clean digit set does NOT prove the order is
RIGHT — a well-formed-but-wrong numbering is invisible to any mechanical check. This sweep
catches the malformed class only.

SOURCE vs LIVE: this runs on abp_texts/ (the pre-build source in the repo), so a defect
already corrected in the live db STILL flags here — that is correct behavior. Groups whose
verse carries an active greek_pos/bracket_id correction row (imported from
build_abp_corrections.ENTRIES — the production ledger, not a copy) are labeled
"corrected-live"; the real work list is the UNCORRECTED remainder.

REUSE RULE: parsing is parse_abp.parse_words — the production parser, never a re-implementation
(ENGINE_LESSONS #87 rebuild-lane: a replica of a mechanism is not the mechanism).

Classes reported:
  DUPLICATE  — a digit appears twice in one group           (Jer 9:23 signature)
  GAP        — fully-numbered group missing a digit from 1..K
  OVER       — a digit exceeds the count of numbered members
  MIXED      — some members numbered, some not (known live case: Mat 20:29, corrected)

Fire-proof: run with --control first; it FAILS unless Jer 9:23 is flagged DUPLICATE.
Usage:
  python scripts/scan_bracket_digits.py --control     # must flag Jer 9:23, exit 0 only then
  python scripts/scan_bracket_digits.py               # full sweep, list + counts
"""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_abp import parse_text
from build_abp_corrections import ENTRIES

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "abp_texts")

# Verses holding an active reorder-metadata correction row in the production ledger.
CORRECTED_LIVE = {(e[0], e[1], e[2]) for e in ENTRIES
                  if e[4] in ("greek_pos", "bracket_id")}


def classify(members):
    """members = [(pos, english, greek_pos)]. Only GLOSSED members participate — a bare tag
    slot with no English (english None, prints as '-') carries nothing to reorder, and its
    missing digit is its normal state (first sweep run: 7,878 such false MIXED flags). The
    real mixed case is an un-numbered member WITH text (Mat 20:29 'multitude')."""
    digits = [g for (_, e, g) in members if e is not None]
    nums = [d for d in digits if d is not None]
    if not nums:
        return None                      # bracket with no digits at all — not this class
    problems = []
    if len(nums) != len(set(nums)):
        problems.append("DUPLICATE")
    if len(nums) < len(digits):
        problems.append("MIXED")
    k = len(nums)
    if any(d > k for d in nums):
        problems.append("OVER")
    elif not problems and set(nums) != set(range(1, k + 1)):
        problems.append("GAP")
    return problems or None


def sweep():
    flagged = []
    files = []
    for sub in ("abp_ot_texts", "abp_nt_texts"):
        d = os.path.join(ROOT, sub)
        files += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".txt")]
    for path in files:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for book, ch, vs, words in parse_text(text):
            groups = defaultdict(list)
            for pos, eng, strongs, gpos, bid in words:
                if bid is not None:
                    groups[bid].append((pos, eng, gpos))
            for bid, members in groups.items():
                probs = classify(members)
                if probs:
                    flagged.append((book, ch, vs, bid, probs, members))
    return flagged


def reads_as(members):
    """Execute the digits the way production does (reorder_english.py: sort by greek_pos,
    missing -> 999, stable) and render the clause the reader gets."""
    glossed = [(e, g) for (_, e, g) in members if e is not None]
    ordered = sorted(glossed, key=lambda t: t[1] if t[1] is not None else 999)
    return " ".join(e for (e, _) in ordered)


def report(flagged):
    counts = defaultdict(int)
    work, done, benign = [], [], []
    for (book, ch, vs, bid, probs, members) in flagged:
        for p in probs:
            counts[p] += 1
        # Severity by MECHANISM (reorder_english.py:25-27 sorts by digit, missing->999,
        # stable): GAP/OVER preserve relative order -> harmless; DUPLICATE = a tie whose
        # outcome is source-order luck (Jer 9:23); MIXED = a glossed word silently sorted
        # to the group's END (Mat 20:29). Only DUPLICATE/MIXED can garble.
        row = (book, ch, vs, bid, probs, members)
        if not ("DUPLICATE" in probs or "MIXED" in probs):
            benign.append(row)
        elif (book, ch, vs) in CORRECTED_LIVE:
            done.append(row)
        else:
            work.append(row)
    print(f"flagged groups: {len(flagged)}  ->  WORK LIST {len(work)} · corrected-live "
          f"{len(done)} · benign-by-mechanism (GAP/OVER only) {len(benign)}")
    for p in sorted(counts):
        print(f"  {p}: {counts[p]}")
    for label, rows in (("== WORK LIST (DUPLICATE/MIXED in source, NOT corrected live) ==", work),
                        ("== corrected-live (flag expected, no action) ==", done)):
        print(f"\n{label}")
        for (book, ch, vs, bid, probs, members) in rows:
            digits = [g for (_, e, g) in members if e is not None]
            glosses = " | ".join((e or "-") for (_, e, _) in members)
            print(f"  {book} {ch}:{vs} group {bid} {'+'.join(probs)} digits={digits}")
            print(f"      source: [{glosses}]")
            print(f"      reads:  {reads_as(members)}")
    print(f"\n== benign-by-mechanism (GAP/OVER only; relative order preserved by the sort) ==")
    for (book, ch, vs, bid, probs, members) in benign:
        digits = [g for (_, e, g) in members if e is not None]
        print(f"  {book} {ch}:{vs} group {bid} {'+'.join(probs)} digits={digits}")
    print("\nCaveats (ruled): clean digits do NOT prove correct order — this sweep catches the "
          "malformed class only. Source-level scan; live fixes go through the corrections door "
          "per flagged group, with intent evidence, individually. 'reads:' executes the digits "
          "with the production sort semantics for eyeball triage — the live db may already "
          "differ where other build passes intervened.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", action="store_true",
                    help="fire-proof: fail unless Jer 9:23 flags DUPLICATE")
    args = ap.parse_args()
    flagged = sweep()
    if args.control:
        hit = [f for f in flagged if f[0] == "Jer" and f[1] == 9 and f[2] == 23
               and "DUPLICATE" in f[4]]
        if hit:
            (book, ch, vs, bid, probs, members) = hit[0]
            print(f"CONTROL PASS: Jer 9:23 flagged {probs} digits="
                  f"{[g for (_, _, g) in members]}")
            sys.exit(0)
        print("CONTROL FAIL: Jer 9:23 NOT flagged — do not trust this sweep's zeros.")
        sys.exit(1)
    report(flagged)


if __name__ == "__main__":
    main()
