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


_CTX = [("Gen", 1, 1, "made", "", "In the beginning God made the heaven and the earth.", "made", "", [])]
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


# ── PATH (c) ROSTER (PATH (c) DESIGN — CLOSED, AUDIT 2026-07-13) ────────────────────────────────
# The three path-(c) words carry a floor-consensus roster. These guard the mechanism, red-first.
_PATH_C = {"G236": 2, "G1390": 2, "G227": 3}   # word -> ruled roster sense count
# The injection's closing boundary sentence — RULED VERBATIM; a reword is a design breach.
_ROSTER_BOUNDARY = ("this fixes only how many senses and which verses group, from the consensus, "
                    "never the wording.")


def test_the_three_path_c_words_carry_a_wellformed_roster():
    for sid, count in _PATH_C.items():
        r = DRAW_HINTS[sid].get("roster")
        assert r, f"{sid}: path-(c) word missing its roster"
        assert r["count"] == count, f"{sid}: roster count {r['count']} != ruled {count}"
        assert len(r["groups"]) == count, f"{sid}: {len(r['groups'])} groups != count {count}"
        assert r.get("floor"), f"{sid}: roster names no floor"
        assert r.get("provenance", "").strip(), f"{sid}: roster provenance is REQUIRED"


def test_roster_rides_after_constraint_check_with_verbatim_boundary():
    r = DRAW_HINTS["G236"]["roster"]
    msg = B.verse_user_msg("G236", "allasso", _GSET, _CTX,
                           hint=["a job"], constraints=["a pin."], roster=r)
    # order: occurrences -> STRUCTURE CHECK -> CONSTRAINT CHECK -> ROSTER (frozen prompt untouched)
    assert (msg.index("OCCURRENCES") < msg.index("STRUCTURE CHECK")
            < msg.index("CONSTRAINT CHECK") < msg.index("ROSTER (floor consensus")), msg
    assert f"{r['count']} senses." in msg
    assert _ROSTER_BOUNDARY in msg, "boundary sentence must appear VERBATIM"
    # seam verses fold into their ruled home group (Jer 13:23 -> group 2), so the draw sees the home
    assert "Jer 13:23" in msg
    # no roster passed -> no scaffold (a draw must never see an empty ROSTER section)
    assert "ROSTER (floor consensus" not in B.verse_user_msg("G236", "allasso", _GSET, _CTX)


def test_roster_folds_the_signature_no_key_collision():
    r = DRAW_HINTS["G227"]["roster"]
    base = B.draw_signature("G227", "alethes", _GSET, _CTX)
    anchored = B.draw_signature("G227", "alethes", _GSET, _CTX, roster=r)
    # a roster-anchored draw can NEVER key-collide with an unanchored one
    assert base != anchored


def test_55_sense_count_guard_fires_red_first_on_mismatch():
    r = DRAW_HINTS["G236"]["roster"]   # count = 2
    collapsed = "**1. To exchange** foo (Gen 1:1)"                                  # 1 sense
    match     = "**1. To exchange** foo (Gen 1:1)\n\n**2. To transform** bar (Exo 2:2)"   # 2
    split     = match + "\n\n**3. Extra** baz (Lev 3:3)"                            # 3
    assert B.roster_count_diff(r, collapsed)["ok"] is False, "must FIRE on a collapse (2->1)"
    assert B.roster_count_diff(r, split)["ok"] is False, "must FIRE on a split (2->3)"
    ok = B.roster_count_diff(r, match)
    assert ok["ok"] is True and ok["ship_count"] == ok["roster_count"] == 2


def test_phrase_context_reaches_the_draw():
    """The fragment-rendering fix's injection half: a multi-word slot phrase shows in the
    here-tag with its translator additions named, and a fragment-risk head is annotated in the
    gloss set; a single-word slot's tag is unchanged."""
    ctx = [("2Ch", 4, 13, "latticed", "", "prose here", "latticed works;", "works", []),
           ("Gen", 1, 1, "made", "", "prose here", "made", "", [])]
    msg = B.verse_user_msg("G1350", "diktyon", [("latticed", 1), ("made", 1)], ctx,
                           pmap={"latticed": [("latticed works", 1)]})
    assert 'phrase here: "latticed works;" (added words: works)' in msg
    assert 'always inside a phrase: "latticed works"' in msg
    assert '[here: "made"]' in msg


# ── the fed occurrence line: a blank head must never reach the model as "None" ───────────────
#
# THE DEFECT (G3464 canary, 2026-07-14, live model call): _occ_lines built its tag with
# f'[here: "{rend}"' where rend = words.english_head. That column is None BY DESIGN when ABP's
# gloss on the slot carries no content word (parse_abp.py:135/:144 — head = last non-function
# word; _head_word returns None for an all-function gloss). The f-string printed that absence as
# the TEXT "None", which is NOT visibly distinct from a real rendering. The model believed it and
# wrote 'the second occurrence tagged "None"' into the card; the verbatim-quote gate then killed
# the draw for quoting a word no verse contains. The gate was RIGHT — the feed was lying.
# 45% of Greek rows have a blank head (correct, mostly articles/particles), so this fed every draw.
#
# The fix states the absence explicitly and UNQUOTABLY. No quote marks: nothing for the model to
# lift, nothing for the quote gate to match. The function-word gloss ("of") is deliberately NOT
# named — feeding it invites the next fabrication ("mýron is rendered *of*").

# (book, ch, vs, rend, form, prose, phrase, ital, context) — the ctx tuple fetch_context builds.
# The 9th element is the grounded-naming context list (2026-07-15); [] = no neighbors fed.
_OCC_BLANK_HEAD = [("Joh", 12, 3, None, "", "Then Mary, taking a pound of perfumed liquid...",
                    "of", "", [])]
_OCC_NORMAL     = [("Mat", 26, 7, "liquid", "μύρου (mýrou)",
                    "there came to him a woman having an alabaster flask of perfumed liquid...",
                    "perfumed liquid", "", [])]

# The tag carries NO apostrophe either: "ABP's" would put one in, and a bare ' is a quote
# character the gate's span-matching has to reason about. Say it without possessives.
_BLANK_HEAD_TAG = ("[no content-word rendering on this slot — the English for this occurrence is "
                   "carried by the surrounding phrase]")


def test_blank_head_never_feeds_the_string_none():
    """THE REGRESSION. A blank english_head must not reach the model as the word None."""
    lines = B._occ_lines(_OCC_BLANK_HEAD)
    assert "None" not in "\n".join(lines), (
        "a blank english_head leaked into the feed as the text 'None' — the G3464 defect: %r" % (lines,))


def test_blank_head_states_the_absence_explicitly():
    """Tight per #76: assert the EXACT emitted tag, not merely that something changed. This also
    pins that the function-word gloss ('of', the fixture's phrase) is NOT named as a rendering —
    feeding it invites the next fabrication. Silence would pass a bare 'None' check while leaving
    the model to infer (#69(i)); the exact-match is what forbids both."""
    lines = B._occ_lines(_OCC_BLANK_HEAD)
    assert lines[0] == "  Joh 12:3 " + _BLANK_HEAD_TAG, repr(lines[0])
    assert lines[1] == "     Then Mary, taking a pound of perfumed liquid..."


def test_blank_head_tag_is_unquotable():
    """The tag must carry NO quote character — the quote gate matches quoted spans against verse
    text, and the whole defect was the model quoting a value the feed invented. Asserted on the
    EMITTED line, never on the constant: a constant checked against itself proves nothing."""
    tagline = B._occ_lines(_OCC_BLANK_HEAD)[0]
    assert '"' not in tagline, repr(tagline)
    assert "'" not in tagline, repr(tagline)


def test_normal_row_tag_is_byte_unchanged():
    """THE CONTROL (reviewer condition, mandatory): this edit must not perturb the 55% that work.
    A row WITH a head keeps the exact original tag shape, quotes and all."""
    lines = B._occ_lines(_OCC_NORMAL)
    assert lines[0] == '  Mat 26:7 [here: "liquid"; phrase here: "perfumed liquid"; form: μύρου (mýrou)]', \
        repr(lines[0])


if __name__ == "__main__":     # plain-script mode for CI + the pre-commit hook
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_draw_hints: ok")
