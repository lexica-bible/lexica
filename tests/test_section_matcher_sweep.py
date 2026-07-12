"""
test_section_matcher_sweep.py — the batch-5 prep sweep (TODO "Section-matcher shape-conformance
sweep", V9_PILE note 2026-07-11): _SECTION_RE + _sense_spans walked against every label/shape
variant the house style permits, so the next legal variant is found HERE, by test, not by a
live floor (the #47 lesson: the one-sense card scored 0 and the singular "Gloss note:" label
leaked the note into Range — both were legal shapes nobody had enumerated).

Two kinds of assertion:
  HANDLED — the shape parses and files correctly today; the pin locks it against drift.
  PINNED GAP (not endorsed) — a shape the matcher does NOT handle today; the pin records the
  chosen current behavior so a change is a decision, not an accident. Each gap is flagged in
  the batch-5 session record for a JP call; none is fixed here (splitter changes touch every
  live card's parse and are checkpoint-class).

Run under pytest or as a plain script. In BOTH the CI list (.github/workflows/ci.yml) and the
pre-commit hook (scripts/githooks/pre-commit).
"""
import os
import sys

_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, _SCRIPTS)
import build_lexica_def as B          # noqa: E402


def _hdr(line):
    m = B._SECTION_RE.match(line)
    return (m.group(1).lower(), m.group(2)) if m else None


# ── HANDLED: section-label variants ─────────────────────────────────────────────────────────

def test_label_variants_all_recognized():
    # Every label spelling/casing/emphasis combination the house style permits today.
    cases = [
        ("**Senses:**",                          "senses", ""),
        ("Senses:",                              "senses", ""),
        ("**SENSES**",                           "senses", ""),
        ("  **Range:** The word stretches",      "range", "The word stretches"),
        ("Range:",                               "range", ""),
        ("range: lowercase label",               "range", "lowercase label"),
        ("**Gloss notes:**",                     "gloss notes", ""),
        ("Gloss notes: plain body",              "gloss notes", "plain body"),
        ("**Gloss note:** singular bold",        "gloss note", "singular bold"),
        ("Gloss note: singular plain",           "gloss note", "singular plain"),
        ("**Coverage:**",                        "coverage", ""),
        ("Coverage: adequate across both testaments", "coverage", "adequate across both testaments"),
    ]
    for line, want_label, want_body in cases:
        got = _hdr(line)
        assert got is not None, f"legal label not recognized: {line!r}"
        assert got == (want_label, want_body), f"{line!r} -> {got}"


def test_singular_gloss_note_files_to_gloss_notes():
    # End-to-end: the G2168 singular-label fix — the note must land in gloss_notes, never Range.
    prose = ("**Senses:**\n**1. first sense** — grounded (Gen 1:1).\n"
             "**Range:** narrow.\n"
             "Gloss note: 'thank' is adequate.\n")
    d = B.split_definition(prose)
    assert "adequate" in d["gloss_notes"], d
    assert "adequate" not in d["range"], d


# ── HANDLED: sense-header variants ──────────────────────────────────────────────────────────

def test_sense_header_variants():
    bold = "**1. correspondence** — body one (Gen 1:1).\n**2. juridical** — body two (Job 9:2)."
    assert [h for h, _ in B._sense_spans(bold)] == ["correspondence", "juridical"]
    assert B.sense_split_mode(bold) == "bold"

    plain = "1. correspondence — body one (Gen 1:1).\n2) juridical — body two (Job 9:2)."
    assert len(B._sense_spans(plain)) == 2
    assert B.sense_split_mode(plain) == "plain"

    lone = "**gives thanks to God** — the one job, organizing paragraph (Rom 1:8)."
    spans = B._sense_spans(lone)
    assert len(spans) == 1 and spans[0][0] == "gives thanks to God"
    assert B.sense_split_mode(lone) == "headline"


def test_bold_wins_over_plain_zero_drift():
    # A bold entry parses EXACTLY as before even when plain-numbered lines also exist in bodies.
    mixed = "**1. head** — body citing 1. something plain-looking.\n2) stray plain line."
    assert [h for h, _ in B._sense_spans(mixed)] == ["head"]
    assert B.sense_split_mode(mixed) == "bold"


# ── PINNED GAPS (not endorsed — each flagged for a JP call, batch-5 session record) ─────────

def test_pinned_gap_singular_sense_label():
    # Singular "Sense:" (the one-sense analog of the G2168 "Gloss note:" leak) is NOT a header
    # today. Accepting it is NOT a one-line fix: _SECTION_RE needs no colon, so matching bare
    # "sense" would turn common prose lines ("Sense 2 narrows...") into section headers.
    assert _hdr("Sense: the single job") is None
    assert _hdr("**Sense:** the single job") is None


def test_pinned_gap_heading_and_bullet_labels():
    # Markdown-heading and bullet-prefixed labels are not house shapes and do not match.
    assert _hdr("### Senses") is None
    assert _hdr("- Senses: bulleted") is None


def test_pinned_gap_bold_paren_numbering_collapses():
    # Bold paren numbering "**1) x**" matches neither numbered finder (bold needs "N.", plain
    # needs the digit at line start) → the lone-headline fallback reads the block as ONE sense.
    # Not silent: sense_split_mode prints the loud '[1 sense — headline fallback]' marker at
    # floor + dry-run, so a multi-sense collapse is seen before any ship.
    block = "**1) first** — body (Gen 1:1).\n**2) second** — body (Job 9:2)."
    assert len(B._sense_spans(block)) == 1
    assert B.sense_split_mode(block) == "headline"


def test_pinned_hazard_bare_label_word_opens_section():
    # CHOSEN-NOT-ACCIDENTAL: the colon is optional, so a prose line BEGINNING with a label word
    # is read as a section header ("Coverage of the term..." opens coverage). House prose has
    # never produced the shape mid-body; pinned so any future change is deliberate.
    got = _hdr("Coverage of the term is thin in the prophets")
    assert got == ("coverage", "of the term is thin in the prophets"), got


def main():
    test_label_variants_all_recognized()
    test_singular_gloss_note_files_to_gloss_notes()
    test_sense_header_variants()
    test_bold_wins_over_plain_zero_drift()
    test_pinned_gap_singular_sense_label()
    test_pinned_gap_heading_and_bullet_labels()
    test_pinned_gap_bold_paren_numbering_collapses()
    test_pinned_hazard_bare_label_word_opens_section()
    print("test_section_matcher_sweep: all assertions passed")


if __name__ == "__main__":
    main()
