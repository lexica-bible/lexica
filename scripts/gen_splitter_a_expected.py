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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_words_from_abp import iter_verses, _abp_sources  # noqa: E402
# The strip screen is IMPORTED, never copied — both derivations must apply the
# identical rule so their diff can only reflect data, not screen drift
# (dry-run 3: 8 of 19 diff lines were screen mismatch, incl. two the other
# side was WRONG about — 'throne were' Rev 4:4 / 'Let not' G3361 1Sa 18:17).
from audit_helper_double_tag import helper_ok  # noqa: E402


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
            if helper_ok(eng, st.lstrip("G")):
                out.append((f"{book_slug_abbrev} {ch}:{vs}", eng.strip(), st))

    dest = Path(__file__).parent / "splitter_a_expected.tsv"
    with dest.open("w", encoding="utf-8", newline="\n") as f:
        for ref, eng, st in out:
            f.write(f"{ref}\t{eng}\t{st}\n")
    print(f"{len(out)} source-level A candidates -> {dest}")


if __name__ == "__main__":
    main()
