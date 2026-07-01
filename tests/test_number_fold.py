"""Number-fold correctness for the Word-study English finder.

Two guarantees are locked here:
  1. The regular singularizer handles the tricky endings (the -es/-ss/e-stem traps).
  2. SYMMETRY — normalize(query)==normalize(rendering) for known singular/plural pairs.
     If the symmetry asserts pass, both-directions reachability (incl. plural->singular)
     is guaranteed by construction, not by luck.
No DB needed — pure functions, runs in CI with the other test_*.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from number_fold import normalize, singularize


def test_singularizer_table():
    cases = {
        "houses": "house",     # e-stem: plain -s, NOT -es (would give "hous")
        "verses": "verse",     # e-stem after s
        "witness": "witness",  # -ss stays whole
        "grass": "grass",      # -ss stays whole
        "cities": "city",      # consonant + ies -> y
        "boxes": "box",        # -xes sibilant cluster -> strip es
        "matches": "match",    # -ches sibilant cluster -> strip es
        "kisses": "kiss",      # -sses -> strip es
        "magistrates": "magistrate",
        "magistrate": "magistrate",
        "cats": "cat",
        "as": "as",            # < 4 letters, untouched
        "is": "is",
    }
    for word, want in cases.items():
        assert singularize(word) == want, f"singularize({word!r}) -> {singularize(word)!r}, want {want!r}"


def test_symmetry_pairs():
    # The core contract: query and rendering land on the same key.
    assert normalize("magistrate") == normalize("magistrates")
    assert normalize("child") == normalize("children")
    assert normalize("house") == normalize("houses")
    assert normalize("foot") == normalize("feet")
    assert normalize("tooth") == normalize("teeth")
    assert normalize("mouse") == normalize("mice")
    assert normalize("ox") == normalize("oxen")
    assert normalize("city") == normalize("cities")


def test_multiform_fold_to_one_key():
    # brother has TWO attested plurals (archaic brethren, modern brothers) — all one key.
    assert normalize("brother") == normalize("brothers") == normalize("brethren") == "brother"
    # cherub / cherubim / cherubims — three forms, one key.
    assert normalize("cherub") == normalize("cherubim") == normalize("cherubims") == "cherub"


def test_invariants_inert():
    # Same in both numbers, or a -ss singular — must normalize to themselves untouched.
    for w in ("witness", "grass", "sheep", "swine", "as", "is"):
        assert normalize(w) == w


def test_no_overfold_short_words():
    # Short words that merely end in s are not plurals.
    assert normalize("its") == "its"
    assert normalize("was") == "was"
