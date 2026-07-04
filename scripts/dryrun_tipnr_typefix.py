#!/usr/bin/env python3
"""
DRY-RUN (parse-only, NO DB write, NO import) for the import_tipnr person/place
type fix — cert Session 8, Door 2. Run on PA:

    cd ~/bible-db && python3 scripts/dryrun_tipnr_typefix.py

Proves, before any `tipnr` re-import:

  (1) PINNED EXPECTATION + MATCH. `expected_flips()` is an INDEPENDENT line-scan
      (it does NOT call the parser under test) enumerating the mixed-block places
      the header-first bug mistyped 'person': main records under a PERSON+PLACE
      header whose own col-8 == 'Place'. The fixed parser's own flip set (from its
      `_audit` hook) must equal that list exactly. Two independent derivations; if
      they disagree, loud. This is the committed expectation — a number/list, not
      a range. (It also settles the docs' 8-vs-10 count conflict by enumeration.)

  (4) MIRROR — zero flips outside a mixed block. Any col-8-vs-header override in a
      SINGLE-type block (mixed_hdr False) is surfaced loudly; expected count 0.
      Plus: any override that is NOT person->place is surfaced.

  (3) RAISE control, BOTH directions. An unrecognized col-8 type RAISES inside a
      PERSON+PLACE block and does NOT raise inside a single-PERSON block.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                        # scripts/ -> import_tipnr
from import_tipnr import parse_tipnr, TIPNR_PINNED


def expected_flips(lines):
    """INDEPENDENT of parse_tipnr: main records under a PERSON+PLACE header whose
    own col-8 == 'Place'. Returns {name}. This is the pinned expectation."""
    out, mixed = set(), False
    for line in lines:
        if line.startswith("$=========="):
            low = line.lower()
            mixed = ("person" in low and "place" in low)
            continue
        if not line.strip() or line[0] in (" ", "\t"):
            continue
        parts = line.split("\t")
        f0 = parts[0].strip()
        if "@" not in f0:
            continue
        col8 = parts[8].strip() if len(parts) > 8 else ""
        if mixed and col8 == "Place":
            out.add(f0.split("@")[0].strip())
    return out


def main():
    lines = open(TIPNR_PINNED, encoding="utf-8-sig").read().splitlines()

    # actual: the fixed parser's own record of every col-8-vs-header override
    audit = []
    parse_tipnr(lines, _audit=audit)
    actual   = {a[0] for a in audit if a[1] == "person" and a[2] == "place"}
    expected = expected_flips(lines)

    print("== (1) FLIP SET: independent expectation vs fixed parser ==")
    print(f"   expected (line-scan) : {len(expected)}")
    print(f"   actual   (parser)    : {len(actual)}")
    only_exp = sorted(expected - actual)
    only_act = sorted(actual - expected)
    print(f"   MATCH: {'YES' if expected == actual else 'NO'}")
    if only_exp: print(f"   in expected only: {only_exp}")
    if only_act: print(f"   in parser only  : {only_act}")
    print("   flipped places (person -> place):")
    for nm in sorted(actual):
        print(f"     {nm}")

    print("\n== (4) MIRROR: overrides that should NOT happen ==")
    outside_mixed = [a for a in audit if not a[3]]                 # override in a single-type block
    other_dir     = [a for a in audit if not (a[1] == "person" and a[2] == "place")]
    print(f"   flips OUTSIDE a mixed block (expect 0): {len(outside_mixed)}")
    for a in outside_mixed: print(f"     OUTSIDE-MIXED: {a}")
    print(f"   overrides NOT person->place  (expect 0): {len(other_dir)}")
    for a in other_dir: print(f"     OTHER-DIR: {a}")

    print("\n== (3) RAISE control (both directions) ==")
    row = "\t".join(["Testname@Gen.1.1=H9999", "", "", "", "", "", "", "", "Bogus"])
    try:
        parse_tipnr(["$========== PERSON+PLACE ==========", row])
        print("   mixed block  -> did NOT raise: FAIL")
    except ValueError:
        print("   mixed block  -> raised: PASS")
    try:
        parse_tipnr(["$========== PERSON ==========", row])
        print("   single block -> no raise: PASS")
    except ValueError:
        print("   single block -> raised: FAIL")


if __name__ == "__main__":
    main()
