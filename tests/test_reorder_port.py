#!/usr/bin/env python3
"""test_reorder_port.py — prove the Python reorder port == the committed JS baseline.

scripts/reorder_english.py must reproduce, byte-for-byte, the JS getEnglishOrderWords
output that test_library_order.js pins in tests/fixtures/order/expected.json (the
`prose` arrays) for John 1, Genesis 1, 1 Chronicles 1, and the 2 Ki 23:29 anchor.

A drifted port would invent phantom hits in the reassembly-diff v2, so this gate runs
BEFORE any corpus v2 run is trusted. Read-only; no db.

Run:  python3 tests/test_reorder_port.py
"""
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from reorder_english import prose_sequence

SNAP = ROOT / "tests" / "snapshots"
FIX = ROOT / "tests" / "fixtures" / "order"


def _rj(p):
    return json.load(io.open(p, encoding="utf-8"))


def fixture_verses():
    """Mirror fixtureVerses() in test_library_order.js — same order, same sources."""
    out = []
    for f in ("api__chapter__Joh__1.json", "api__chapter__Gen__1.json",
              "api__chapter__1Ch__1.json"):
        for v in _rj(SNAP / f):
            out.append((f, v["verse"], v["words"]))
    ki = _rj(FIX / "2ki_23_29.json")
    out.append(("2ki_23_29.json", 29, ki["words"]))
    return out


def main():
    expected = _rj(FIX / "expected.json")
    mismatches = []
    checked = 0
    for src, verse, words in fixture_verses():
        key = f"{src}#{verse}"
        want = expected[key]["prose"]
        got = prose_sequence(words)
        checked += 1
        if got != want:
            mismatches.append((key, want, got))

    if mismatches:
        print(f"PORT DRIFT — {len(mismatches)}/{checked} fixture verses differ from the JS baseline:")
        for key, want, got in mismatches[:10]:
            print(f"  {key}")
            print(f"    JS  : {want}")
            print(f"    PY  : {got}")
        sys.exit(1)
    print(f"ok  reorder port reproduces the JS baseline on all {checked} fixture verses")


if __name__ == "__main__":
    main()
