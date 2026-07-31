"""Regression check for the PN-star merged-verb class (issue-log 2026-07-31).

ABP source attaches a verb's English to the adjacent proper-noun star chunk
("scourging Jesus,G* G5417" — Mat 27:26; "calls ElijahG* G5455" — Mat 27:47),
leaving the verb's own G-number as an empty-english slot. _split_compounds
deliberately skips star slots, so the built words table carries the verb on the
name's chip and the verb chip renders blank. 145 spots corpus-wide (scan held
in the issue report; data fix deferred to a cert-style session).

This test pins two things at the PARSER level:
  1. The verb's Strong's number is never lost — its slot must exist.
  2. The current merged state: the star slot's English still carries the verb.
     When the data fix lands, flip assertion (2) to expect the split.
"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build_words_from_abp import parse_abp_line

SRC = os.path.join(os.path.dirname(__file__), "..", "abp_texts", "abp_nt_texts",
                   "abp_matthew.txt")


def _verse(ch, vs):
    tag = "(Mat %d:%d)" % (ch, vs)
    with io.open(SRC, encoding="utf-8") as f:
        for line in f:
            if line.startswith(tag):
                return parse_abp_line(line)[3]
    raise AssertionError("verse line not found: " + tag)


def _check(ch, vs, verb_num, star_gloss_word):
    words = _verse(ch, vs)
    nums = [w[1] for w in words]
    assert verb_num in nums, "Mat %d:%d lost %s slot" % (ch, vs, verb_num)
    star_glosses = [w[0] for w in words if w[1] == "G*"]
    merged = [g for g in star_glosses if star_gloss_word in g.lower()]
    # Current (known-bad, data-class) state: the verb rides on the star slot and
    # the verb slot is empty. If this starts failing, the merge class changed —
    # re-check the corpus scan and flip these expectations to the split shape.
    assert merged, "Mat %d:%d: star slot no longer carries '%s' — merged-verb " \
                   "state changed; update this test to the fixed shape" \
                   % (ch, vs, star_gloss_word)
    verb_glosses = [w[0] for w in words if w[1] == verb_num]
    assert verb_glosses == [""], "Mat %d:%d: %s slot gained english %r" \
                                 % (ch, vs, verb_num, verb_glosses)


def main():
    _check(27, 26, "G5417", "scourging")   # φραγελλόω riding on Jesus' star slot
    _check(27, 47, "G5455", "calls")       # φωνέω riding on Elijah's star slot
    print("test_pn_star_verb_merge: PASS (2 verses pinned)")


if __name__ == "__main__":
    main()
