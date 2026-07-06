#!/usr/bin/env python3
"""scan_malformed_brackets.py — READ-ONLY scan of the pinned ABP feed (abp_texts/)
for MALFORMED brackets: a closing ']' that has no matching opening '['. These are the
verses where the build strips the ABP position digits but never reorders (no '[' to
open a bracket), so the digit-ordered words sit in raw Greek order with greek_pos
dropped. This is the pre-registration for the S10 word-side fix (Option A): the fix
must fire on EXACTLY the verses this scan lists.

Method: per verse, walk the raw text and track '[' / ']' depth. A ']' while depth==0
is an unmatched (malformed) close. Also flags a verse that ends with depth>0 (an
unmatched OPEN) so nothing hides. Reports the verse + the offending tail.

Run locally (abp_texts/ is in the repo — no bible.db needed):
  python3 scripts/scan_malformed_brackets.py
"""
import glob
import os
import re

VERSE_RE = re.compile(r"^\((\w+)\s+(\d+):(\d+)\)\s+(.*)")


def scan():
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "abp_texts")
    files = sorted(glob.glob(os.path.join(root, "**", "*.txt"), recursive=True))
    unmatched_close = []
    unmatched_open = []
    for path in files:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = VERSE_RE.match(line.strip())
                if not m:
                    continue
                book, ch, vs, text = m.groups()
                ref = f"{book} {ch}:{vs}"
                # tokenize like the build: split on Strong's numbers so each english
                # chunk is one ABP gloss (may carry a leading position digit + [ / ]).
                chunks = re.split(r"[GH]\*|[GH]\d+(?:\.\d+)*", text)
                depth = 0
                for chunk in chunks:
                    for c in chunk:
                        if c == "[":
                            depth += 1
                        elif c == "]":
                            if depth == 0:
                                # stray close on THIS chunk — does the closing gloss
                                # carry a leading ABP position digit? (that is what the
                                # build reorders by; a bare ']' has nothing to order)
                                bare = re.sub(r"[^\w\s]", "", chunk.lstrip().lstrip("[")).lstrip()
                                digit_backed = bool(re.match(r"\d", bare))
                                unmatched_close.append((ref, digit_backed, chunk.strip()))
                            else:
                                depth -= 1
                if depth > 0:
                    unmatched_open.append((ref, text[-70:]))
    return unmatched_close, unmatched_open


def main():
    closes, opens = scan()
    fire = [(r, t) for r, d, t in closes if d]
    skip = [(r, t) for r, d, t in closes if not d]
    print("MALFORMED-BRACKET SCAN of abp_texts/\n")
    print(f"Stray ']' on a DIGIT-BACKED gloss — the Option A target set: {len(fire)}")
    for ref, chunk in fire:
        print(f"    {ref:<14} closes on: {chunk!r}")
    print(f"\nStray ']' on a BARE gloss (no digit — Option A must SKIP): {len(skip)}")
    for ref, chunk in skip:
        print(f"    {ref:<14} closes on: {chunk!r}")
    print(f"\nUnmatched '[' (stray open — not an Option A target): {len(opens)}")
    for ref, tail in opens:
        print(f"    {ref:<14} …{tail}")


if __name__ == "__main__":
    main()
