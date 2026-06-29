"""Fail-closed parsing of the pass-2 curation tail (ai._parse_curation).

The Ask-corpus synthesis prose streams to the reader live; the verse picks ride in a
JSON tail after a fixed ===VERSES=== marker. The danger of that reshape is the
pick-parse: a garbled tail that half-parses could silently mark WRONG verses as
primary/additional. The parser is therefore fail-CLOSED — any malformed or missing
tail returns None, and the caller falls back rather than show wrong evidence. These
cases lock that floor (run by CI + the pre-commit hook; no bible.db needed).
"""
import ai


def test_clean_parse():
    raw = ("Sabbaton (G4521) is the seventh-day rest.\n\n"
           "In the numeral idiom it means the week.\n"
           "===VERSES===\n"
           '{"primary_verses": ["Exo 20:8", "Mar 2:27"], "additional_verses": ["Gen 2:3"]}')
    out = ai._parse_curation(raw)
    assert out is not None
    primary, additional, explanation = out
    assert primary == ["Exo 20:8", "Mar 2:27"]
    assert additional == ["Gen 2:3"]
    assert explanation.startswith("Sabbaton")
    # The tail must NEVER leak into the displayed prose.
    assert "===VERSES===" not in explanation
    assert "primary_verses" not in explanation


def test_paragraph_breaks_preserved():
    raw = ("First sense here.\n\nSecond sense here.\n"
           '===VERSES===\n{"primary_verses": ["Joh 1:1"]}')
    _, _, explanation = ai._parse_curation(raw)
    assert explanation == "First sense here.\n\nSecond sense here."


def test_missing_additional_defaults_empty():
    raw = 'Prose.\n===VERSES===\n{"primary_verses": ["Joh 1:1"]}'
    primary, additional, _ = ai._parse_curation(raw)
    assert primary == ["Joh 1:1"]
    assert additional == []


# ── fail-closed cases: every one must return None (never wrong picks) ──────────

def test_missing_marker_fails_closed():
    assert ai._parse_curation('Prose, no marker. {"primary_verses": ["Joh 1:1"]}') is None


def test_broken_json_fails_closed():
    assert ai._parse_curation('Prose.\n===VERSES===\n{"primary_verses": ["Joh 1:1",}') is None


def test_no_json_after_marker_fails_closed():
    assert ai._parse_curation("Prose.\n===VERSES===\nthe model forgot the json") is None


def test_empty_prose_fails_closed():
    # Marker present + valid picks, but no synthesis before it → unusable, fall back.
    assert ai._parse_curation('===VERSES===\n{"primary_verses": ["Joh 1:1"]}') is None


def test_primary_not_a_list_fails_closed():
    assert ai._parse_curation('Prose.\n===VERSES===\n{"primary_verses": "Joh 1:1"}') is None


def test_primary_key_missing_fails_closed():
    assert ai._parse_curation('Prose.\n===VERSES===\n{"additional_verses": ["Joh 1:1"]}') is None


def test_empty_and_none_input_fails_closed():
    assert ai._parse_curation("") is None
    assert ai._parse_curation(None) is None
