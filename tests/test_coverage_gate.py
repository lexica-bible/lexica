"""V9 coverage gate (JP-ruled 2026-07-12, DESIGN_v9_lines.md RULINGS block): every FED
occurrence must be cited under a sense; trimming is a ship defect (floor-legal only).

MUST-FAIL FIXTURE PROVENANCE (reviewer condition, on the record): the trimmed fixture
below pins the SHAPE and the NAMED ABSENTEE (Jdg 21:2) from the G2805 d1 park entry
(AUDIT_lexica_rollout.md, G2805 RE-PARKED: d1 = 34/39, 5 uncited incl. 10/10 Jdg 21:2).
It is NOT the cached d1 raw — that lives in the PA-side draw cache and is deliberately
not in CI (CC-never-touches-PA boundary). If JP later wants the real raw as a second
fixture, that's additive, his call.

Red-first: this file was run BEFORE the gate existed and failed (raw output in the V9
design pass session record) — the detector provably fires on the defect class before
any zero is trusted (audit-tools-must-fail).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_lexica_def as B


# The G2805 d1 SHAPE: a fed sample whose senses block cites some refs but leaves the
# named absentee (Jdg 21:2) uncited. Books/verses are the park entry's own.
FED = [("Jdg", 21, 2), ("Mat", 8, 12), ("Mat", 13, 42), ("Jer", 31, 15)]

SENSES_TRIMMED = (
    "**1. Weeping in judgment.** Grounding: Mat 8:12; Mat 13:42.\n"
    "**2. Weeping in grief.** Grounding: Jer 31:15.\n"
)

SENSES_FULL = (
    "**1. Weeping in judgment.** Grounding: Mat 8:12; Mat 13:42.\n"
    "**2. Weeping in grief.** Grounding: Jer 31:15; Jdg 21:2.\n"
)

# #28 tie-in: Jdg 21:2 covered ONLY through a range tail — proves the gate rides the
# production ref_spans scanner (tails expanded), never a private copy.
SENSES_RANGE = (
    "**1. Weeping in judgment.** Grounding: Mat 8:12; Mat 13:42.\n"
    "**2. Weeping in grief.** Grounding: Jer 31:15; Jdg 21:1–3.\n"
)


def entry_with(fed_uncited, bypass_reason=None):
    """Minimal entry that passes every OTHER validate_entry check, so the coverage
    problem (or its absence) is the only variable."""
    audit = {"misses": [], "real": 0, "noverse": 0, "noncanon": [],
             "fed_uncited": fed_uncited}
    if bypass_reason:
        audit["bypass_reason"] = bypass_reason
    return {"strongs": "G2805", "sense_headlines": ["1. x"], "fork": None,
            "senses_block": SENSES_TRIMMED, "audit": audit}


def main():
    # 1 — MUST-FAIL (red-first control): the G2805 d1 shape fires the gate, absentee named.
    missing = B.coverage_gate(FED, SENSES_TRIMMED)
    assert missing == ["Jdg 21:2"], f"must-fail fixture did NOT fire: {missing!r}"

    # 2 — clean control: every fed ref cited -> no finding.
    assert B.coverage_gate(FED, SENSES_FULL) == []

    # 3 — #28 tie-in: coverage through a range tail counts (production scanner).
    assert B.coverage_gate(FED, SENSES_RANGE) == []

    # 4 — ref-level doubles (the Amo 5:5 x2 class): fed twice, cited once = covered;
    # and an uncited double is reported ONCE.
    fed_doubled = FED + [("Jdg", 21, 2), ("Mat", 8, 12)]
    assert B.coverage_gate(fed_doubled, SENSES_FULL) == []
    assert B.coverage_gate(fed_doubled, SENSES_TRIMMED) == ["Jdg 21:2"]

    # 5 — validate_entry wiring: an uncited fed ref REFUSES the write (problem listed)…
    problems = B.validate_entry(entry_with(["Jdg 21:2"]))
    assert any("coverage gate FAILED" in p and "Jdg 21:2" in p for p in problems), problems
    # …a stamped bypass reason downgrades it to a loud warn (no problem)…
    assert not any("coverage gate" in p
                   for p in B.validate_entry(entry_with(["Jdg 21:2"], "adjudicated: reason")))
    # …None = not-checked (resplit pass) is NOT a failure — distinct from [] = clean.
    assert not any("coverage gate" in p for p in B.validate_entry(entry_with(None)))
    assert not any("coverage gate" in p for p in B.validate_entry(entry_with([])))

    print("test_coverage_gate: all assertions passed")


if __name__ == "__main__":
    main()
