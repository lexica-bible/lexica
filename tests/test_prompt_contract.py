#!/usr/bin/env python3
"""VERSE_PROMPT's contract + the frozen-prompt stamp pin.

WHY THIS FILE EXISTS. synth_ver() is a hash of VERSE_PROMPT's bytes, and it is the identity the
whole draw cache hangs on (build_lexica_def.py: synth_ver / the draw fingerprint). So ANY edit to
the prompt — even a whitespace nudge — stales every cached draw for every word. That is a real
cost, and it must never happen by accident. This file pins the stamp: an unacknowledged prompt
edit fails CI. Moving the prompt is allowed; moving it silently is not. Update PROMPT_STAMP in
the same commit as the prompt edit, and say why in the message.

STAMP HISTORY (each line = a deliberate prompt move):
  lexica:7d7758f4156b  grounded-naming feed, +/-2 context + referent rule   (238147a, 2026-07-15)
  lexica:bd8b7e3f8209  anti-range constraint line (ENGINE_LESSONS #80)      (this commit)

The text asserts below are the contract, not the behavior. A prompt line cannot be unit-tested for
OBEDIENCE — that is watched on the next drawn card's gate tail at BATCH REVIEW, never asserted here
(reviewer ruling, 2026-07-15, control (c)).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import build_lexica_def as B   # noqa: E402

# READ FACT, not recalled: PASTED from this file's own RED run against the edited prompt
# (leg 2 of the red-first sequence, 2026-07-15), which printed the value it computed.
PROMPT_STAMP = "lexica:bd8b7e3f8209"


def test_prompt_stamp_is_pinned():
    """The frozen prompt's identity. Fails the moment VERSE_PROMPT's bytes move."""
    assert B.synth_ver() == PROMPT_STAMP, (
        f"VERSE_PROMPT changed: stamp is {B.synth_ver()}, pinned at {PROMPT_STAMP}.\n"
        "Every cached draw for every word is now stale. If the edit is deliberate: update\n"
        "PROMPT_STAMP + the STAMP HISTORY block above in the same commit as the prompt edit."
    )


def test_verse_prompt_carries_the_anti_range_constraint():
    """ENGINE_LESSONS #80 — the standing anti-range line. Three words paid for it (G227,
    G2168 pins; G3793's 'Rev 19:1-6' -> four phantom citations). Contract only: whether the
    model OBEYS is watched on the next card's gate tail at BATCH REVIEW, never asserted here."""
    flat = " ".join(B.VERSE_PROMPT.split())   # wrap-independent: line breaks are not the contract
    assert "REFERENCES NAME VERSES ONE BY ONE" in flat
    assert "Never write a span of verses as a reference range." in flat
    # It must live with the truth rules (Constraints), not with Formatting — a written range
    # asserts unchecked verses, the same class as QUOTES ARE VERBATIM.
    c = B.VERSE_PROMPT.index("Constraints:")
    o = B.VERSE_PROMPT.index("Output (compact")
    assert c < B.VERSE_PROMPT.index("REFERENCES NAME VERSES ONE BY ONE") < o


def test_anti_range_line_does_not_swallow_the_sense_range_section():
    """The collision hazard this line was worded around: 'range' is load-bearing vocabulary in
    FOUR other places in this same prompt (Method step 4, the Output 'Range:' line, the
    Formatting header, and Formatting's 'Keep Range as one paragraph'). The constraint governs
    REFERENCES only; if the carve-out sentence goes missing, an unqualified ban is left sitting
    next to a required section it could degrade."""
    flat = " ".join(B.VERSE_PROMPT.split())   # the carve-out sentence wraps; wrap is not the claim
    assert "This governs REFERENCES only; the Range section, which states how far the " \
           "word's meaning stretches, is unaffected." in flat
    # the sense-Range section the carve-out protects must still be there to protect
    assert "Range: one line on how far the word stretches and what moves it." in flat
    assert "4. State the attested range" in flat
    assert "Keep Range as one paragraph" in flat


if __name__ == "__main__":
    fails = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except AssertionError as e:
                fails.append(name)
                print(f"  FAIL {name}\n       {e}")
    print(("FAILED: " + ", ".join(fails)) if fails else "all green")
    sys.exit(1 if fails else 0)
