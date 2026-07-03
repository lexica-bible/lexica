#!/usr/bin/env python3
"""Ask-corpus key-word alias fold: the model's textbook Strong's is rewritten to the
number the corpus actually tags, so counting / highlighting / the lexical-texture panel
all key on ONE number.

ABP tags charis on G5484 (the form charin), not the textbook G5485 — the same split the
Lexica dictionary already knows about (contested_register.LEXICA_ALIASES). When "charis"
is typed in Latin letters the exact-lemma pin can't fire, so the model returns the textbook
G5485; unfolded, the panel counted G5485 (~0 rows in ABP), dropped the whole charis family,
and the synthesis crowned G5485 "the primary term" while the verses it read were tagged
G5484. ai._fold_alias closes that gap, generically over the alias map.

These lock the fold + the dedup order. Pure — `import ai` needs no bible.db, no model. Run:
    python tests/test_key_strongs_alias.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai
import contested_register


def test_alias_folds_to_canonical():
    # G5485 (textbook charis) → G5484 (the number ABP tags), from the ONE alias map.
    assert ai._fold_alias("G5485") == "G5484"
    # The mapping is exactly the register's — no hard-coded charis special case.
    for alias, canon in contested_register.LEXICA_ALIASES.items():
        assert ai._fold_alias(alias) == canon


def test_split_lemma_alias_folds():
    # A plain split-lemma pair (not a contested word): hagios "holy" G40 is dead in ABP;
    # the occurrences live on G39. The fold rewrites the textbook key word to the number
    # ABP tags, at the key-words assembly point — same machinery as charis, no special case.
    assert ai._fold_alias("G40") == "G39"


def test_non_alias_passes_through():
    # A normal key word is untouched (Greek fire, Hebrew ruach, a dotted number).
    for n in ("G4442", "H7307", "G1510.1", "H784"):
        assert ai._fold_alias(n) == n


def test_fold_then_dedup_collapses_the_pair():
    # The live loop folds FIRST, then dedups (first entry wins the display). A model list
    # carrying BOTH the alias and the canonical number must collapse to one canonical entry.
    raw = ["G5485", "G5484", "G5487"]     # textbook charis, canonical charis, charitoo
    seen, out = set(), []
    for p in raw:
        c = ai._fold_alias(p)             # the REAL fold helper the loop uses
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    assert out == ["G5484", "G5487"]      # G5485 folded onto G5484, the dup dropped
    assert "G5485" not in out


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run()
