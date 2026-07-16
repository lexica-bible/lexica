#!/usr/bin/env python3
"""
test_tipnr_roster.py — locks the TIPNR name roster against key hijacks.

Born 2026-07-16: the alternate-spelling harvest let an alphabetically-earlier
entity steal a later entity's key (Barabbas claimed 'jesus' -> G912; 79 names
regressed). Three green spot-controls (Christian/Ashchenaz/Elias) said nothing
about the rest — a control proves its key. This test runs BOTH layers:

  1. Sentinel names — the historically-hijacked keys pinned to their true
     numbers, plus the alias-batch gains the reviewer approved.
  2. The full zero-regression diff against scripts/roster_baseline.json via
     the production checker (never a copy of it).

Runs on the pinned tipnr/TIPNR.txt in the repo — no database needed.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_roster_regression as gate

# The hijack casualties of 2026-07-16 (pinned to the OLD loader's correct
# answers) + the reviewed alias-batch gains.
SENTINELS = {
    "jesus":     {"g": "G2424"},   # was stolen by Barabbas (G912)
    "judah":     {"h": "H3063", "g": "G2455"},   # was stolen by Hodaviah / Juda-place
    "simon":     {"g": "G4613"},   # was stolen by Peter's number
    "jacob":     {"g": "G2384"},   # was stolen by Israel's number
    "joseph":    {"g": "G2501"},
    "lord":      {"h": "H3068"},   # was stolen by Immanuel
    "syria":     {"h": "H758"},    # was stolen by Edom's number
    "edom":      {"h": "H123"},
    "daniel":    {"h": "H1840"},
    "zedekiah":  {"h": "H6667"},
    # reviewed alias-batch gains that must KEEP working:
    "christian": {"g": "G5546"},   # Group row's own number, NOT Jesus' G2424
    "ashchenaz": {"h": "H813"},    # the original ticket control
}


def test_sentinels(now):
    bad = []
    for name, want in SENTINELS.items():
        entry = now.get(name)
        if entry is None:
            bad.append(f"{name}: missing from roster")
            continue
        h, g = entry
        got = {"h": h, "g": g}
        for slot, num in want.items():
            if got[slot] != num:
                bad.append(f"{name}: {slot}={got[slot]}, want {num}")
    assert not bad, "sentinel name(s) wrong:\n  " + "\n  ".join(bad)
    print(f"  ok: {len(SENTINELS)} sentinel names carry their true numbers")


def test_zero_regression(now):
    baseline = json.loads((ROOT / "scripts" / "roster_baseline.json")
                          .read_text(encoding="utf-8"))
    regressions, gains, new_keys = gate.diff(baseline, now)
    assert not regressions, (
        f"{len(regressions)} roster regression(s) vs baseline:\n  "
        + "\n  ".join(f"{k}: {why}" for k, why in sorted(regressions)[:20]))
    print(f"  ok: 0 regressions vs baseline ({len(baseline)} names;"
          f" gains {gains}, new {len(new_keys)})")


def test_detector_fires():
    # The gate must FAIL on a known positive before its zero is trusted:
    # poison one baseline entry and require diff() to flag it.
    poisoned = {"jesus": ["H9999", "G912"], "ghost-name": [None, "G1"]}
    now = {"jesus": [None, "G2424"]}
    regressions, _g, _n = gate.diff(poisoned, now)
    reasons = {k for k, _ in regressions}
    assert "jesus" in reasons and "ghost-name" in reasons, (
        "regression detector failed to fire on planted defects")
    print("  ok: detector fires on planted number-change and missing-name")


if __name__ == "__main__":
    print("== tipnr roster locks ==")
    test_detector_fires()
    now = gate.current_lookup()
    test_sentinels(now)
    test_zero_regression(now)
    print("All roster locks hold.")
