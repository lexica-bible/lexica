"""
test_lexica_section_split.py — the section-header splitter must not eat the body's own markdown.

Regression lock for the κάλαμος G2563 splitter bite (batch 3, 2026-07-08): _SECTION_RE's trailing
junk-eater was the greedy class `[\\s:*]*`, which on a label-and-text shared line whose body OPENS
with an italic term ("**Gloss notes:** *Calamus* ...") swallowed the italic's opening asterisk —
the stored raw was correct, the assembled gloss_notes showed "Calamus* ..." (a literal asterisk on
the live card), and the rendering-claim lint fired seven garbled artifacts across three pulls, all
downstream of this one bite. Fix: bounded eater `[\\s:]*\\*{0,2}[\\s:]*` — at most the label's own
closing bold pair, never the body's markdown.

CONTROL assertion baked in: the OLD greedy pattern must FAIL the italic-body case in this very
fixture set — proving the fixtures reproduce the bug, so the pass can't be vacuous.

Also PINS the known bounded-eater edge (JP ruling 2026-07-08): a PLAIN label whose body opens bold
("Gloss notes: **term**") loses that opening pair — no draft has produced the shape; pinned so the
behavior is chosen, not accidental. The BOLD-label + bold-body case is safe (the label's own closing
pair is consumed first) and asserted safe.

Run under pytest or as a plain script. In BOTH the CI list (.github/workflows/ci.yml) and the
pre-commit hook (scripts/githooks/pre-commit).
"""
import os
import re
import sys

_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, _SCRIPTS)
import build_lexica_def as B          # noqa: E402

OLD_GREEDY = re.compile(r'^\s*\*{0,2}\s*(senses|range|gloss notes|coverage)\b[\s:*]*(.*?)\s*$', re.I)


def _body(line):
    m = B._SECTION_RE.match(line)
    assert m, f"section header not recognized: {line!r}"
    return m.group(2)


def test_italic_opening_body_survives():
    # The κάλαμος shape: bold label, colon inside the bold, body opens with an italic term.
    line = "**Gloss notes:** *Calamus* (used at Exo 30:23, Son 4:14) — imports a precision"
    assert _body(line).startswith("*Calamus*"), _body(line)


def test_control_old_pattern_reproduces_the_bite():
    # CONTROL: the old greedy class must eat the opening asterisk on the same fixture —
    # proving the fixture is the bug shape, so the test above can't pass vacuously.
    line = "**Gloss notes:** *Calamus* (used at Exo 30:23, Son 4:14) — imports a precision"
    m = OLD_GREEDY.match(line)
    assert m and m.group(2).startswith("Calamus*"), "control failed: fixture no longer reproduces the bug"


def test_bold_label_bold_body_safe():
    # Bold label + bold-opening body: the label's own closing pair is consumed first, body intact.
    line = "**Gloss notes:** **calamus** is the Latin trade name"
    assert _body(line).startswith("**calamus**"), _body(line)


def test_pinned_edge_plain_label_bold_body():
    # PINNED (not endorsed): plain label + bold-opening body loses the opening pair — the bounded
    # eater cannot tell it from a label's closing pair. No draft has produced this shape; if one
    # does and this pin trips the wrong way, the fix is a smarter anchor, decided then.
    line = "Gloss notes: **calamus** is the Latin trade name"
    assert _body(line).startswith("calamus**"), _body(line)


def test_existing_shapes_unchanged():
    # Every header shape the docstring above _SECTION_RE promises, before and after the fix:
    assert _body("**SENSES**") == ""                                        # caps, header alone
    assert B._SECTION_RE.match("**Senses** (ordered by frequency...):")     # parenthetical tail
    assert _body("**Range:** The word stretches from A to B") == "The word stretches from A to B"
    assert _body("Range:") == ""                                            # un-bolded label
    assert _body("Gloss notes: plain text body") == "plain text body"       # plain label + text


def main():
    test_italic_opening_body_survives()
    test_control_old_pattern_reproduces_the_bite()
    test_bold_label_bold_body_safe()
    test_pinned_edge_plain_label_bold_body()
    test_existing_shapes_unchanged()
    print("test_lexica_section_split: all assertions passed")


if __name__ == "__main__":
    main()
