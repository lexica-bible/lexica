#!/usr/bin/env python3
"""A3/A4: no LSJ / Strong's DEFINITION prose in the Ask-corpus synthesis payload.

Ask-corpus answers are built ONLY from actual verse evidence (the Berean rule) —
not from imported lexicon prose. The audit found LSJ gloss text and Strong's
definition text leaking into answers: the old _format_lsj_context emitted the LSJ
`semantic` blurb (and a cognate `gloss` that can carry Strong's/KJV `def` text) in
the block prepended to the pass-1 SQL-gen call, whose `explanation` the reader sees
when the pool is small and cites no verse.

The fix is STRUCTURAL, not a prompt instruction: the retrieval context is now built
from KEYS ONLY (Strong's number + lemma + transliteration), with a fail-closed guard
(_assert_no_lexicon_prose) that drops the whole block if any definition prose leaks
in — the same philosophy as the pick-parse floor (test_curation_parse.py).

These lock that boundary. Pure — `import ai` needs no bible.db, no model. Run:
    python tests/test_synthesis_no_leak.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai


# A rich LSJ entry shaped like _lsj_concept_lookup returns: `semantic` is LSJ
# definition prose; the cognate `gloss` is _word_gloss()-or-kjv_def-or-strongs_def,
# i.e. it can be raw Strong's/KJV definition text.
def _rich_theos_entry():
    return {
        "strongs": "2316", "lemma": "theós", "translit": "theós",
        "semantic": ("a god, the supreme Divinity; in the plural, gods; used of the one "
                     "true God, the Godhead, deity, divine majesty"),
        "dotted_variants": [],
        "cognates": [{
            "strongs": "G2304", "lemma": "theíos", "translit": "theíos",
            # deliberately a definition-prose gloss (the kind kjv_def/strongs_def carries)
            "gloss": "that which is divine, the divine nature or Godhead, pertaining to God",
        }],
    }


def _rich_agape_entry():
    # A second word from a different concept, so the block has >1 entry.
    return {
        "strongs": "26", "lemma": "agápē", "translit": "agápē",
        "semantic": "love, affection, benevolence, esp. brotherly love, charity as in the KJV",
        "dotted_variants": ["26.1"],
        "cognates": [],
    }


def _assert_keys_present(ctx, entry):
    assert f"G{entry['strongs']}" in ctx, "Strong's number (a retrieval key) must survive"
    assert entry["lemma"] in ctx, "lemma (a retrieval key) must survive"


def _assert_no_prose(ctx, entry):
    """No prose fragment from `entry` (or its cognates) may appear in the context."""
    for frag in ai._prose_snippets([entry]):
        assert frag not in ctx.lower(), f"definition prose leaked: {frag!r}"


def test_retrieval_context_is_keys_only():
    e = _rich_theos_entry()
    ctx = ai._retrieval_context([e])
    _assert_keys_present(ctx, e)
    assert "G2304" in ctx and "theíos" in ctx  # cognate NUMBER + lemma stay (retrieval keys)
    _assert_no_prose(ctx, e)
    # spot-check the exact prose that used to leak
    low = ctx.lower()
    for banned in ("supreme divinity", "godhead", "deity", "divine nature", "pertaining to god"):
        assert banned not in low, f"leaked LSJ/Strong's prose: {banned!r}"


def test_multi_entry_context_clean():
    entries = [_rich_theos_entry(), _rich_agape_entry()]
    ctx = ai._retrieval_context(entries)
    for e in entries:
        _assert_keys_present(ctx, e)
        _assert_no_prose(ctx, e)
    assert "G26.1" in ctx or "26.1" in ctx  # dotted variant number kept
    assert "charity" not in ctx.lower() and "benevolence" not in ctx.lower()


def test_guard_drops_contaminated_block():
    # A future edit that re-emits `semantic` must be caught, not shipped.
    e = _rich_theos_entry()
    clean = ai._retrieval_context([e])
    contaminated = clean + "\nextra: " + e["semantic"]
    assert ai._assert_no_lexicon_prose(contaminated, [e]) == ""


def test_guard_drops_cognate_definition_leak():
    e = _rich_theos_entry()
    clean = ai._retrieval_context([e])
    contaminated = clean + "\n  " + e["cognates"][0]["gloss"]
    assert ai._assert_no_lexicon_prose(contaminated, [e]) == ""


def test_guard_passes_clean_keys():
    # Numbers + lemmas + translit alone must NOT trip the guard (they're keys).
    e = _rich_theos_entry()
    clean = ai._retrieval_context([e])
    assert ai._assert_no_lexicon_prose(clean, [e]) == clean


def test_curation_terms_strip_definition_prose():
    # Pass-2 backstop: key_strongs_data carries `definition`/`derivation`; the terms
    # line must contain the number + lemma but NONE of that definition text.
    ksd = [{
        "strongs": "G2316", "strongs_base": "2316", "lemma": "theós", "translit": "theós",
        "definition": "a deity, especially the supreme Divinity; the Godhead",
        "derivation": "of uncertain affinity; a deity",
    }]
    terms = ai._assert_no_lexicon_prose(
        ", ".join(f"{e.get('strongs','')} {e.get('lemma','')}".strip() for e in ksd),
        ksd,
    )
    assert "G2316" in terms and "theós" in terms
    assert "deity" not in terms.lower() and "godhead" not in terms.lower()


def test_short_labels_not_flagged():
    # A short lemma-ish value (< 12 chars) is a key, not gated prose — no false drop.
    e = {"strongs": "4151", "lemma": "pneûma", "translit": "pneûma",
         "gloss": "spirit", "dotted_variants": [], "cognates": []}
    ctx = ai._retrieval_context([e])
    assert "G4151" in ctx and "pneûma" in ctx


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run()
