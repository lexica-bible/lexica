#!/usr/bin/env python3
"""F12: a user-typed Strong's number is a retrieval KEY, always permitted.

Ask-corpus's SQL-gen prompt tells the model "never use Strong's numbers not in the
LSJ context block" — which collided with a user typing "G4442" directly (the number
they cited would be dropped as an "invented" one). The fix: a query that IS a single
prefixed Strong's number is PINNED (ai._resolve_typed_strongs), the same guaranteed-
occurrence machinery as a bare typed Greek word; an embedded number is permitted at
the prompt level (the LSJ-CONTEXT exception line).

These lock the pure parser (ai._parse_typed_strongs) — no bible.db, no model. Run:
    python tests/test_typed_strongs.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai


# ── whole-query typed numbers pin (normalized: uppercased, zero-stripped) ──

def test_greek_number():
    assert ai._parse_typed_strongs("G4442") == "G4442"

def test_lowercase_prefix_uppercased():
    assert ai._parse_typed_strongs("g4442") == "G4442"

def test_hebrew_number():
    assert ai._parse_typed_strongs("H784") == "H784"

def test_surrounding_whitespace():
    assert ai._parse_typed_strongs("  G4442  ") == "G4442"

def test_space_after_prefix():
    assert ai._parse_typed_strongs("G 4442") == "G4442"

def test_leading_zeros_stripped():
    assert ai._parse_typed_strongs("G04442") == "G4442"


# ── things that must NOT pin (fall through to the model) ──

def test_bare_number_is_ambiguous():
    # No G/H prefix → Greek-vs-Hebrew ambiguous → not pinned.
    assert ai._parse_typed_strongs("4442") is None

def test_dotted_not_pinned():
    # strongs_base drops the dot, so the pin can't target a dotted variant.
    assert ai._parse_typed_strongs("G166.1") is None

def test_embedded_number_not_whole_query():
    assert ai._parse_typed_strongs("what is G4442") is None
    assert ai._parse_typed_strongs("fire G4442 in judgment") is None

def test_plain_word():
    assert ai._parse_typed_strongs("fire") is None

def test_zero_not_valid():
    assert ai._parse_typed_strongs("G0") is None

def test_empty_and_none():
    assert ai._parse_typed_strongs("") is None
    assert ai._parse_typed_strongs(None) is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_typed_strongs: {len(fns)} checks passed.")
