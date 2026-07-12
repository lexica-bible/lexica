"""V10 coverage REPAIR PASS controls (DESIGN_v10_repair.md, CLOSED at d04b6e6; built under
JP's standing delegation 2026-07-12). Three ruled controls, all db-free and model-free
(the model is a mock — CI never calls the API):

  1. MUST-FAIL / FIRE control: a G1390-d3-SHAPED trimmed card (sole absentee Deu 23:23)
     must FIRE the repair path, the mock's corrected card must pass the re-run coverage
     gate, and the repair record (refs / rounds / prompt_ver) must be present.
  2. NO-OP control: a full-coverage card must NOT trigger repair (the mock raises if
     called).
  3. STRUCTURE-GUARD control: a mock repair output that drops a sense, rewords a
     headline, or removes an existing citation must be REFUSED (draw dead, no round 2).

FIXTURE PROVENANCE (the test_coverage_gate precedent, reviewer-ruled pattern): the
fixtures pin the SHAPE and the NAMED ABSENTEE (Deu 23:23) from the G1390 RE-PARKED audit
entry (d3 = 37/38, sole absentee Deu 23:23, 2Sa 19:42 cited beside the hole). They are
NOT the cached d3 raw — that lives in the PA-side draw cache and is deliberately not in
CI (CC-never-touches-PA boundary). The acceptance test runs against the real cached
draws (or the pre-specified fresh fallback) on PA, not here.

Red-first: this file was run BEFORE the repair hook existed and failed loudly
(AttributeError on coverage_repair) — the controls provably fire before any green is
trusted (audit-tools-must-fail).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_lexica_def as B


# ── The G1390 d3 SHAPE. Fed sample (subset-sized), books/verses from the park entry;
# ctx rows carry the (book, ch, vs, rend, form, prose, phrase, ital) feed shape.
FED = [("2Sa", 19, 42), ("Pro", 18, 16), ("Psa", 68, 18), ("Eph", 4, 8),
       ("Mat", 7, 11), ("Deu", 23, 23)]

CTX = [
    ("2Sa", 19, 42, "gift",  "", "…or has he lifted a gift to us?", "", ""),
    ("Pro", 18, 16, "gift",  "", "A gift of a man widens him…", "", ""),
    ("Psa", 68, 18, "gifts", "", "…you received gifts by man…", "", ""),
    ("Eph", 4, 8,   "gifts", "", "…he gave gifts to men.", "", ""),
    ("Mat", 7, 11,  "gifts", "", "…know to give good gifts to your children…", "", ""),
    ("Deu", 23, 23, "gift",  "", "…as you vowed to the LORD your God a gift…", "", ""),
]

RAW_TRIMMED = (
    "Senses:\n"
    "**1. A gift transferred between people.** Grounding: 2Sa 19:42 (\"has he lifted a "
    "gift to us?\"); Pro 18:16; Mat 7:11.\n"
    "**2. A gift given by or to God.** Grounding: Psa 68:18; Eph 4:8.\n"
    "Range: from human transfer to divine giving.\n"
    "Gloss notes: none.\n"
)

# The corrected card the FIRE-control mock returns: Deu 23:23 housed in sense 2 with the
# minimum prose, nothing else changed.
RAW_REPAIRED = (
    "Senses:\n"
    "**1. A gift transferred between people.** Grounding: 2Sa 19:42 (\"has he lifted a "
    "gift to us?\"); Pro 18:16; Mat 7:11.\n"
    "**2. A gift given by or to God.** Grounding: Psa 68:18; Eph 4:8; a vowed gift to "
    "God belongs here (Deu 23:23).\n"
    "Range: from human transfer to divine giving.\n"
    "Gloss notes: none.\n"
)

# Guard fixtures — each integrates Deu 23:23 but breaks a ruled line.
RAW_DROPPED_SENSE = (       # sense 1 gone entirely
    "Senses:\n"
    "**1. A gift given by or to God.** Grounding: Psa 68:18; Eph 4:8; Deu 23:23; "
    "2Sa 19:42; Pro 18:16; Mat 7:11.\n"
    "Range: from human transfer to divine giving.\n"
    "Gloss notes: none.\n"
)
RAW_REWORDED_HEADLINE = (   # sense 2's headline reworded
    "Senses:\n"
    "**1. A gift transferred between people.** Grounding: 2Sa 19:42 (\"has he lifted a "
    "gift to us?\"); Pro 18:16; Mat 7:11.\n"
    "**2. Divine gift-giving.** Grounding: Psa 68:18; Eph 4:8; Deu 23:23.\n"
    "Range: from human transfer to divine giving.\n"
    "Gloss notes: none.\n"
)
RAW_LOST_CITATION = (       # Deu 23:23 added but Pro 18:16 removed
    "Senses:\n"
    "**1. A gift transferred between people.** Grounding: 2Sa 19:42 (\"has he lifted a "
    "gift to us?\"); Mat 7:11.\n"
    "**2. A gift given by or to God.** Grounding: Psa 68:18; Eph 4:8; Deu 23:23.\n"
    "Range: from human transfer to divine giving.\n"
    "Gloss notes: none.\n"
)

# Two-absentee shape for the two-round path: Pro 18:16 ALSO uncited at round 0.
RAW_TRIMMED_TWO = RAW_TRIMMED.replace("; Pro 18:16;", ";")
# Round 1 integrates only Deu 23:23 (guard-clean, still one short)…
RAW_HALF_REPAIRED = RAW_TRIMMED_TWO.replace(
    "Psa 68:18; Eph 4:8.", "Psa 68:18; Eph 4:8; Deu 23:23.")
# …round 2 integrates Pro 18:16 too.
RAW_FULLY_REPAIRED = RAW_HALF_REPAIRED.replace(
    "; Mat 7:11.", "; Mat 7:11; Pro 18:16.")


class Mock:
    """A scripted call_model: returns its outputs in order, records every user message."""
    def __init__(self, *outputs):
        self.outputs, self.msgs = list(outputs), []
    def __call__(self, msg):
        self.msgs.append(msg)
        if not self.outputs:
            raise AssertionError("call_model called more times than scripted")
        return self.outputs.pop(0)


def senses_of(raw):
    return B.split_definition(raw)["senses_block"]


def main():
    # ── 1. FIRE control (must-fail-first): the G1390 d3 shape fires the repair path.
    mock = Mock(RAW_REPAIRED)
    final, rec, probs = B.coverage_repair(RAW_TRIMMED, FED, CTX, mock)
    assert probs == [], f"FIRE control refused a clean repair: {probs!r}"
    assert rec is not None and rec["rounds"] == 1, rec
    assert rec["refs"] == ["Deu 23:23"], rec
    assert rec["prompt_ver"].startswith("repair:"), rec
    # the repaired card passes the re-run coverage gate (production gate, never a copy)
    assert B.coverage_gate(FED, senses_of(final)) == []
    assert final == RAW_REPAIRED
    # the repair message carried the ruled clause, the named absentee WITH its verse
    # text (same feed shape), and the full card — and only the absentee, not cited refs
    msg = mock.msgs[0]
    assert "not yet cited under a sense" in msg
    assert "Deu 23:23" in msg and "as you vowed to the LORD" in msg
    assert RAW_TRIMMED.strip() in msg
    assert "Psa 68:18 [here:" not in msg, "a CITED ref was fed as an absentee"

    # ── 2. NO-OP control: full coverage → repair must NOT fire, model never called.
    def never(_msg):
        raise AssertionError("repair fired on a full-coverage card")
    final, rec, probs = B.coverage_repair(RAW_REPAIRED, FED, CTX, never)
    assert (final, rec, probs) == (RAW_REPAIRED, None, [])

    # ── 3. STRUCTURE-GUARD controls (red-first on the mocks): each breach = draw DEAD,
    # exactly one model call (dead, not re-repaired — the design's adjudication rule).
    for bad, what in ((RAW_DROPPED_SENSE, "dropped sense"),
                      (RAW_REWORDED_HEADLINE, "reworded headline"),
                      (RAW_LOST_CITATION, "removed citation")):
        mock = Mock(bad, RAW_REPAIRED)      # a round 2 would consume the second output
        final, rec, probs = B.coverage_repair(RAW_TRIMMED, FED, CTX, mock)
        assert probs, f"guard did NOT refuse a {what}"
        assert len(mock.msgs) == 1, f"{what}: guard breach was re-repaired (round 2 ran)"
        assert final == RAW_TRIMMED, f"{what}: a guard-refused raw leaked out"
    # direct guard reads, for the record
    assert B.repair_guard(RAW_TRIMMED, RAW_REPAIRED) == []
    assert B.repair_guard(RAW_TRIMMED, RAW_DROPPED_SENSE)
    assert B.repair_guard(RAW_TRIMMED, RAW_REWORDED_HEADLINE)
    assert B.repair_guard(RAW_TRIMMED, RAW_LOST_CITATION)

    # ── 4. CAP-OUT: a guard-clean card that never integrates → dead after exactly 2
    # rounds (the ruled cap), original raw preserved (the cached draw is not clobbered).
    mock = Mock(RAW_TRIMMED, RAW_TRIMMED, RAW_TRIMMED)
    final, rec, probs = B.coverage_repair(RAW_TRIMMED, FED, CTX, mock)
    assert probs and any("cap" in p.lower() for p in probs), probs
    assert len(mock.msgs) == 2, f"cap is 2 rounds, ran {len(mock.msgs)}"
    assert final == RAW_TRIMMED

    # ── 5. TWO-ROUND success: two absentees, one integrated per round; record names
    # both refs, rounds == 2, round-2 message carries only the REMAINING absentee.
    mock = Mock(RAW_HALF_REPAIRED, RAW_FULLY_REPAIRED)
    final, rec, probs = B.coverage_repair(RAW_TRIMMED_TWO, FED, CTX, mock)
    assert probs == [], probs
    assert rec["rounds"] == 2 and set(rec["refs"]) == {"Deu 23:23", "Pro 18:16"}, rec
    assert B.coverage_gate(FED, senses_of(final)) == []
    assert "Deu 23:23 [here:" not in mock.msgs[1], "round 2 re-fed an integrated ref"

    print("test_repair_pass: ok")


if __name__ == "__main__":
    main()
