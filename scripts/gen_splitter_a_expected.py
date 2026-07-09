#!/usr/bin/env python3
"""
Independent SOURCE-level derivation of the polarity-A strip list (splitter
double-tag charter). Reads the raw ABP text files with the builder's OWN parse
helpers (parse_abp_line -> _emit_words peel) and lists every peeled helper word
that (a) sits outside a bracket with no position number, (b) shares its
Strong's with the bracket-opening piece that follows, and (c) screens as a bare
auxiliary — the same three tests audit_helper_double_tag.py applies to the
words TABLE. Two derivations of one fact: their diff is the oracle.

Writes scripts/splitter_a_expected.tsv (ref \t helper_english \t strongs).
Read-only over the source; touches no database.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_words_from_abp import (  # noqa: E402
    _STRONGS_RE, _VERSE_RE, _emit_words, iter_verses, _abp_sources,
)

HELPER_HEADS = {
    "may", "might", "shall", "should", "will", "would", "let", "did", "do", "does",
    "was", "were", "be", "been", "is", "are", "am", "had", "has", "have",
    "can", "could", "must", "and", "but", "then", "so", "that", "when",
}
_PUNCT = re.compile(r"[^\w\s]")

def norm(s):
    return _PUNCT.sub("", (s or "")).lower().strip()


def head_or_eng(eng):
    words = [w for w in (eng or "").split() if norm(w)]
    return norm(words[-1]) if words else ""


def main():
    out = []
    for book_slug_abbrev, ch, vs, words in iter_verses(*_abp_sources()):
        # iter_verses yields the ABP file's own book token (already the abbrev)
        for i, (eng, st, abp_pos, opens, closes) in enumerate(words):
            if not st or st == "G*" or not eng:
                continue
            if abp_pos is not None or opens or closes:
                continue                       # helper must sit OUTSIDE, unnumbered
            if i + 1 >= len(words):
                continue
            neng, nst, nap, nopens, ncloses = words[i + 1]
            if nst != st or not nopens:
                continue                       # next piece: same tag, opens the bracket
            lead = head_or_eng(eng)
            if lead in HELPER_HEADS and len(eng.split()) <= 2:
                out.append((f"{book_slug_abbrev} {ch}:{vs}", eng.strip(), st))

    dest = Path(__file__).parent / "splitter_a_expected.tsv"
    with dest.open("w", encoding="utf-8", newline="\n") as f:
        for ref, eng, st in out:
            f.write(f"{ref}\t{eng}\t{st}\n")
    print(f"{len(out)} source-level A candidates -> {dest}")


if __name__ == "__main__":
    main()
