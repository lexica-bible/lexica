#!/usr/bin/env python3
"""
check_roster_regression.py — the PERMANENT roster zero-regression gate
(reviewer-mandated 2026-07-16, after the alternate-spelling key hijack: a
first-writer save let Barabbas claim 'jesus' — 79 names silently changed
numbers, and three green spot-controls said nothing about the other 4,300.
A control proves its key; roster changes require THIS full diff.)

Read-only. Parses the pinned TIPNR file with the CURRENT loader and compares
every name against scripts/roster_baseline.json:

  HARD REGRESSION (exit 1, itemized):
    - a baseline name is gone from the roster
    - a baseline name's Hebrew or Greek number changed or was emptied
  Fine (reported as counts only):
    - a name gained a number it lacked
    - a brand-new name

Any deliberate, reviewed roster change re-baselines with --update-baseline —
never hand-edit the JSON.

Usage:
  python3 scripts/check_roster_regression.py            # gate (exit 1 on regression)
  python3 scripts/check_roster_regression.py --update-baseline
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "scripts" / "roster_baseline.json"
sys.path.insert(0, str(ROOT / "scripts"))


def current_lookup():
    sys.argv = [sys.argv[0], "--dry-run"]  # import guard: module reads flags at import
    import import_tipnr
    lines = (ROOT / "tipnr" / "TIPNR.txt").read_text(encoding="utf-8").splitlines()
    lookup, _rows = import_tipnr.parse_tipnr(lines)
    return {k: [v["h"], v["g"]] for k, v in lookup.items()}


def diff(baseline, now):
    """EXACT-match gate: ANY difference from the baseline fails — a changed
    number, an emptied number, a vanished name, a FILLED slot (a 'gain' flips
    the testament fallback on real words — the Jesus/Immanuel H6005 lesson,
    2026-07-16), or a brand-new name. Returns (regressions, new_keys); both
    must be empty, or the change re-baselines under review."""
    regressions = []
    for k, (bh, bg) in baseline.items():
        if k not in now:
            regressions.append((k, f"name gone (was h={bh} g={bg})"))
            continue
        nh, ng = now[k]
        if nh != bh:
            regressions.append((k, f"Hebrew {bh} -> {nh}"))
        if ng != bg:
            regressions.append((k, f"Greek {bg} -> {ng}"))
    new_keys = [k for k in now if k not in baseline]
    return regressions, new_keys


def main():
    update = "--update-baseline" in sys.argv  # read BEFORE current_lookup clobbers argv
    now = current_lookup()
    if update:
        BASELINE.write_text(
            json.dumps({k: now[k] for k in sorted(now)}, indent=0, ensure_ascii=False)
            + "\n", encoding="utf-8")
        print(f"baseline UPDATED: {len(now)} names -> {BASELINE.name}")
        print("Commit this only as part of a reviewed roster change.")
        return
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    regressions, new_keys = diff(baseline, now)
    print(f"roster now: {len(now)} names | baseline: {len(baseline)}")
    if regressions or new_keys:
        if regressions:
            print(f"\n!! {len(regressions)} name(s) answer differently than the baseline:")
            for k, why in sorted(regressions):
                print(f"   {k:24} {why}")
        if new_keys:
            print(f"\n!! {len(new_keys)} name(s) are NEW vs the baseline"
                  f" (first 20): {sorted(new_keys)[:20]}")
        print("\n!! The roster is FROZEN outside reviewed changes. DO NOT run"
              " import_tipnr with this loader; fix it or, for a reviewed"
              " deliberate change, --update-baseline.")
        sys.exit(1)
    print("roster regression check: CLEAN (exact match, 0 differences)")


if __name__ == "__main__":
    main()
