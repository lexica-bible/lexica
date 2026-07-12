"""Constraint-hint register + injection tests (DESIGN_hint_tooling.md, JP-ruled 2026-07-12).

Guards: (1) every draw_hints.py entry carries provenance naming its audit-doc ruling record
(the register is the machine-readable copy; the audit entry is the source of truth); (2) the
register holds exactly the seven JP-ruled batch-4 shelf words — ANY membership change is a JP
checkpoint (ruling 3), so a diff here must fail CI until this list is deliberately updated;
(3) injection shape: constraints ride in the USER message, after the occurrences and after any
STRUCTURE CHECK (frozen system prompt untouched), and join the draw signature so a hint change
can never silently reuse a stale draw.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import build_lexica_def as B
from draw_hints import DRAW_HINTS

# The seven batch-4 shelf words (BATCH 4 CLOSED, JP ruling 2026-07-12). Editing the register =
# a JP checkpoint; this pin makes an unruled edit fail loudly instead of shipping silently.
RULED_SEVEN = {"G1244", "G1390", "G2168", "G227", "G236", "G2805", "G162"}


def test_register_membership_is_the_ruled_seven():
    assert set(DRAW_HINTS) == RULED_SEVEN, sorted(DRAW_HINTS)


def test_every_entry_names_provenance_and_one_line_hints():
    for sid, e in DRAW_HINTS.items():
        assert sid[:1] == "G" and sid[1:].isdigit(), f"{sid}: keys are G-prefixed"
        assert e.get("provenance", "").strip(), f"{sid}: provenance is REQUIRED (design doc)"
        assert "AUDIT_lexica_rollout.md" in e["provenance"], f"{sid}: provenance must name the audit doc"
        assert e.get("hints"), f"{sid}: entry with no hint lines"
        for h in e["hints"]:
            assert h.strip() and "\n" not in h, f"{sid}: hints are ONE line each"
        assert isinstance(e.get("jobs", []), list), f"{sid}: jobs must be a list"


_CTX = [("Gen", 1, 1, "made", "", "In the beginning God made the heaven and the earth.", "made", "")]
_GSET = [("made", 1)]


def test_constraints_ride_after_occurrences_and_structure_check():
    msg = B.verse_user_msg("G0000", "test", _GSET, _CTX,
                           hint=["a stable job"], constraints=["Gen 1:1 reads 'made' - a pin."])
    occ = msg.index("OCCURRENCES")
    struct = msg.index("STRUCTURE CHECK")
    cons = msg.index("CONSTRAINT CHECK (pre-registered)")
    assert occ < struct < cons, (occ, struct, cons)
    assert "Gen 1:1 reads 'made' - a pin." in msg
    # No constraints -> section absent entirely (a draw must never see an empty scaffold).
    assert "CONSTRAINT CHECK" not in B.verse_user_msg("G0000", "test", _GSET, _CTX)


def test_hint_change_changes_signature():
    base = B.draw_signature("G0000", "test", _GSET, _CTX)
    hinted = B.draw_signature("G0000", "test", _GSET, _CTX, constraints=["line one"])
    hinted2 = B.draw_signature("G0000", "test", _GSET, _CTX, constraints=["line two"])
    assert base != hinted and hinted != hinted2


def test_phrase_context_reaches_the_draw():
    """The fragment-rendering fix's injection half: a multi-word slot phrase shows in the
    here-tag with its translator additions named, and a fragment-risk head is annotated in the
    gloss set; a single-word slot's tag is unchanged."""
    ctx = [("2Ch", 4, 13, "latticed", "", "prose here", "latticed works;", "works"),
           ("Gen", 1, 1, "made", "", "prose here", "made", "")]
    msg = B.verse_user_msg("G1350", "diktyon", [("latticed", 1), ("made", 1)], ctx,
                           pmap={"latticed": [("latticed works", 1)]})
    assert 'phrase here: "latticed works;" (added words: works)' in msg
    assert 'always inside a phrase: "latticed works"' in msg
    assert '[here: "made"]' in msg


if __name__ == "__main__":     # plain-script mode for CI + the pre-commit hook
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_draw_hints: ok")
