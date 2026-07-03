#!/usr/bin/env python3
"""Batch E task 1: the exact-lemma PIN's retrieval SQL is alias-folded too.

A Greek-script "χάρις" search pins to the textbook head G5485 (_resolve_exact_lemma,
matching the dictionary headword). But ABP tags the occurrences on G5484 (the form
charin) — so an UNFOLDED retrieval `WHERE w.strongs_base='G5485'` pulled ZERO verses
and the synthesis read an empty pool. The pin returning G5485 is correct; the fix folds
the alias at the ONE query-assembly point (ai.py, the `if _pinned:` Greek SQL branch)
via the SAME _fold_alias the key-words path uses — generic over the alias map, no charis
special case.

The display/canonical split is preserved: _ks_pairs keeps the PRE-fold number so the loop
still shows χάρις and folds it to G5484 for the key word (see test_key_strongs_alias) —
only the retrieval number is folded here.

Pure — `import ai` needs no bible.db, no model. Run:
    python tests/test_pin_retrieval_alias.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai
import contested_register


def test_pinned_alias_folds_for_retrieval():
    # Greek-script charis pins to G5485; the number that reaches the retrieval WHERE
    # is the canonical G5484 that ABP actually tags.
    pinned = "G5485"
    assert ai._fold_alias(pinned) == "G5484"


def test_generic_over_the_map():
    # No charis special case — every alias the register knows folds the same way.
    for alias, canon in contested_register.LEXICA_ALIASES.items():
        assert ai._fold_alias(alias) == canon


def test_split_lemma_pin_folds_for_retrieval():
    # The exact-lemma pin for a Greek-script "ἅγιος" resolves the textbook head G40; the
    # number that reaches the retrieval WHERE is the canonical G39 that ABP actually tags —
    # so the same plain split-lemma alias folds at the pin-retrieval point too.
    assert ai._fold_alias("G40") == "G39"


def test_non_alias_pin_passes_through():
    # A normal pinned Greek number (fire G4442) reaches retrieval unchanged.
    for n in ("G4442", "G2316", "G4151"):
        assert ai._fold_alias(n) == n


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run()
