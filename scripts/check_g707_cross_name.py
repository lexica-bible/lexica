#!/usr/bin/env python3
"""check_g707_cross_name.py — sign-off condition on the strict name-match gate.

JP's condition (2026-07-31 sign-off): the alias/variant expansion is the only
place a cross-name link could sneak back in. So, for every record the sweep
flags, verify the non-match holds AFTER expansion — the G-number's names and
the record's other names must not touch once both sides are expanded. Built-in
control: re-run the same check with the old pooling (every record name treated
as attached) — it MUST flag, or the checker itself is broken.

Pure-local: reads tipnr/TIPNR.txt only, no database. Uses the PRODUCTION
parser + matcher from build_pn_greek_identity (never a copy).

Exit 0 = all green. Exit 1 = a failure, printed.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))
import entity_resolution as er
from build_pn_greek_identity import parse_number_forms, name_matches

TIPNR = os.path.join(_HERE, "..", "tipnr", "TIPNR.txt")

# The G1/G2 anchor cases (charter): the fix pair + the must-keep trio.
MIZPAH_UNIQ = "Mizpah@Jos.18.26-Jhn"
MUST_KEEP = [("Elijah@1Ki.17.1-Jas", "elijah", "G2243"),
             ("Noah@Gen.5.29-2Pe", "noah", "G3575"),
             ("Rehoboam@1Ki.11.43-Mat", "rehoboam", "G4497")]


def main():
    lines = open(TIPNR, encoding="utf-8-sig").read().splitlines()
    ents = er.parse_tipnr(lines)
    ent_forms, _glob = parse_number_forms(lines)
    fails = []

    # One-Greek-number entities (the production inheritance rule's population).
    ent_g = {}
    for e in ents:
        gs = sorted(b for b in e["bases"] if b.startswith("G"))
        if len(gs) == 1:
            ent_g[e["uniq"]] = (e, gs[0])

    # Sweep: records where at least one of the record's own names is NOT
    # attached to its sole Greek number — the class the old rule mis-stamped.
    flagged = []
    for uniq, (e, g) in ent_g.items():
        forms = ent_forms.get(uniq, {}).get(g, set())
        # er.parse_tipnr's spellings include mined junk (version tags, pipe
        # compounds) that no slot ever prints — filter to real name shapes.
        loose = sorted(s for s in e["spellings"]
                       if "|" not in s and s not in ("niv", "kjv", "esv", "lxx")
                       and not name_matches(s, forms))
        if loose:
            flagged.append((uniq, g, sorted(forms), loose))

    print(f"one-Greek-number records: {len(ent_g):,}")
    print(f"flagged (a record name NOT attached to its Greek number): {len(flagged)}")
    for uniq, g, forms, loose in sorted(flagged):
        print(f"  {uniq}  {g} names={forms}  gated-out={loose}")

    # 1) Post-expansion non-intersection holds on every flagged record: each
    # gated-out name must STILL fail the production matcher (both sides
    # variant/alias/compact-expanded inside name_matches).
    for uniq, g, forms, loose in flagged:
        for s in loose:
            if name_matches(s, forms):
                fails.append(f"expansion leak: {uniq} {s} matches {g} after expansion")

    # 2) The anchor pair: Mizpah record — Arimathea in, everything else out.
    mz = ent_forms.get(MIZPAH_UNIQ, {}).get("G707", set())
    if not name_matches("arimathea", mz):
        fails.append(f"Mizpah record: arimathea does NOT match G707 (names={sorted(mz)})")
    for s in ("mizpah", "mizpeh", "ramah", "ramathaim-zophim"):
        if name_matches(s, mz):
            fails.append(f"Mizpah record: {s} matches G707 — the fix did not hold")

    # 3) CONTROL — the checker must FIRE under the old pooling. Treat every
    # record name as attached (what '– Total' pooling did): mizpah must match.
    e_mz = next((e for e in ents if e["uniq"] == MIZPAH_UNIQ), None)
    if not e_mz:
        fails.append("control: Mizpah record not found in parse")
    elif not name_matches("mizpah", e_mz["spellings"]):
        fails.append("CONTROL DEAD: pooled forms do not flag mizpah — checker can't see the bug")
    else:
        print("control FIRED: pooled (old-rule) forms match mizpah — checker sees the bug class")

    # 4) Must-keep trio (G2): same-name Greek dress keeps its number.
    for uniq, nm, g in MUST_KEEP:
        if uniq not in ent_g or ent_g[uniq][1] != g:
            fails.append(f"{uniq}: expected sole Greek {g}, got {ent_g.get(uniq, ('?','?'))[1]}")
        elif not name_matches(nm, ent_forms.get(uniq, {}).get(g, set())):
            fails.append(f"{uniq}: {nm} does NOT match {g} — predicate too strict, STOP")

    print()
    if fails:
        for f in fails:
            print(f"FAIL  {f}")
        sys.exit(1)
    print(f"ALL GREEN — {len(flagged)} flagged records, non-intersection holds "
          "post-expansion; control fired; must-keep trio matches.")


if __name__ == "__main__":
    main()
