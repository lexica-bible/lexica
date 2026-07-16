"""Door-1 lock for the stopword-highlight bug (TICKET_highlight_cited_set.md).

The SQL-gen prompt TELLS the model to omit articles/particles from key_strongs, but
nothing enforced it — on the Gen 1:1 arche thread the model included G3588 (the
article) and every "the" in the evidence verses lit gold. `_filter_function_keys`
is the hard filter at the acceptance point in ai.py: any key whose resolved number
sits in the function-word sets (core._FUNCTION_STRONGS, the startup-populated
strongs_base set; views_lexicon._HEB_FUNCTION_STRONGS for Hebrew) is dropped no
matter what the model sent.

Control per the standing rule: the known-bad case (G3588 in a key list) must be
caught before any clean result counts. core._FUNCTION_STRONGS is empty without the
live DB, so the test populates it IN PLACE (same mechanism app.py uses at startup)
and restores it after.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core
from ai import _filter_function_keys


def _with_function_sets(fn):
    # core._FUNCTION_STRONGS holds BARE numbers (Greek — the set itself is the
    # language); app.py's override set shows the format ("3361", "1473").
    saved = set(core._FUNCTION_STRONGS)
    core._FUNCTION_STRONGS.clear()
    core._FUNCTION_STRONGS.update({"3588", "2532", "1722"})   # the article + kai + en
    try:
        fn()
    finally:
        core._FUNCTION_STRONGS.clear()
        core._FUNCTION_STRONGS.update(saved)


def test_door1_control_g3588_is_dropped():
    # THE known-bad case: the Gen 1:1 arche thread's key set included the article.
    def check():
        pairs = [("3588", "G"), ("746", "G"), ("2316", "G")]
        out = _filter_function_keys(pairs)
        assert ("3588", "G") not in out
        assert ("746", "G") in out and ("2316", "G") in out
    _with_function_sets(check)


def test_bare_prefix_resolves_greek_and_still_drops():
    # A bare-number pair with no resolved prefix is Greek by the prompt contract.
    def check():
        out = _filter_function_keys([("3588", None), ("746", None)])
        assert ("3588", None) not in out
        assert ("746", None) in out
    _with_function_sets(check)


def test_hebrew_function_word_dropped_greek_twin_kept():
    # H853 (the untranslatable object marker) is in the Hebrew function set; the
    # GREEK number 853 is a real content word and must survive — proves the filter
    # is language-aware, not digit-blind.
    def check():
        out = _filter_function_keys([("853", "H"), ("853", "G")])
        assert ("853", "H") not in out
        assert ("853", "G") in out
    _with_function_sets(check)


def test_empty_function_set_passes_everything():
    # Deploy safety: before the startup cache populates (or on a DB-less run) the
    # filter is a no-op, never an over-blocker.
    saved = set(core._FUNCTION_STRONGS)
    core._FUNCTION_STRONGS.clear()
    try:
        pairs = [("3588", "G"), ("746", "G")]
        assert _filter_function_keys(pairs) == pairs
    finally:
        core._FUNCTION_STRONGS.update(saved)


def test_control_fires():
    # Audit-tools-must-fail: the detector (this test file's premise) must FIRE on a
    # seeded positive — an unfiltered pass-through would fail test_door1 above, but
    # prove it directly: with G3588 seeded, a filter that returns its input unchanged
    # is caught here.
    def check():
        out = _filter_function_keys([("3588", "G")])
        assert out == []
    _with_function_sets(check)


if __name__ == "__main__":   # pre-commit / CI run this file as a plain script
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"ok  {_name}")
    print("key_strongs filter tests passed")
