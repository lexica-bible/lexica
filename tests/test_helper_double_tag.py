#!/usr/bin/env python3
"""Locking tests for the helper double-tag strip (splitter charter,
CHARTER_splitter_fix.md): the _strip_helper_double_tag build pass + the shared
helper_ok screen. Synthetic 13-element rows, no bible.db (PA-only).

The canonical cases are the three charter exhibits plus the two wrong-call
lessons the source-vs-table diff surfaced ('Let not' G3361 / 'throne were').

Run:  python tests/test_helper_double_tag.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import build_words_from_abp as B  # noqa: E402

_FAILS = []

# Row tuple layout (13): 0:pos 1:english 2:english_head 3:strongs 4:strongs_base
#   5:greek_pos 6:bracket_id 7:italic 8:italic_words 9:smcap_words 10:abp_pos 11:morph 12:lemma


def row(pos, eng, strongs, *, head=None, gpos=None, bid=None):
    sbase = strongs.split(".")[0] if strongs not in ("", "*") else strongs
    return (pos, eng, head, strongs, sbase, gpos, bid, 0, "", "", None, None, None)


def check(desc, got, want):
    if got != want:
        _FAILS.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
    else:
        print(f"  ok: {desc}")


def test_strip_pass():
    # Jud 1:9 — peeled helper outside the bracket, verb opens it, same tag
    rows = [row(21, "May", "2008", head="may"),
            row(22, "reproach", "2008", head="reproach", gpos=2, bid=3),
            row(23, "you", "4671", gpos=3, bid=3)]
    B._strip_helper_double_tag(rows)
    check("Jud 1:9 helper tag blanked", (rows[0][3], rows[0][4], rows[0][5]), ("", "", None))
    check("Jud 1:9 helper english kept", rows[0][1], "May")
    check("Jud 1:9 verb row untouched", rows[1], row(22, "reproach", "2008", head="reproach", gpos=2, bid=3))

    # Job 18:13 — two-word helper "And may", dotted-free
    rows = [row(0, "And may", "977", head="may"),
            row(1, "be devoured", "977", head="devoured", gpos=3, bid=1)]
    B._strip_helper_double_tag(rows)
    check("Job 18:13 helper tag blanked", (rows[0][3], rows[0][4]), ("", ""))

    # Jas 2:21 — legit reorder split, BOTH pieces inside the bracket: untouched
    rows = [row(7, "Was", "1344", gpos=1, bid=1),
            row(8, "justified,", "1344", head="justified", gpos=5, bid=1)]
    before = list(rows)
    B._strip_helper_double_tag(rows)
    check("Jas 2:21 legit split untouched", rows, before)

    # 1Sa 18:17 'Let not' G3361 — shared tag IS the negation: never strip
    rows = [row(0, "Let not", "3361", head="let"),
            row(1, "be", "3361", gpos=2, bid=1)]
    before = list(rows)
    B._strip_helper_double_tag(rows)
    check("'Let not' G3361 never stripped", rows, before)

    # Rev 4:4 'throne were' — content lead: never strip
    rows = [row(0, "throne were", "2362", head="throne"),
            row(1, "sitting", "2362", head="sitting", gpos=2, bid=1)]
    before = list(rows)
    B._strip_helper_double_tag(rows)
    check("'throne were' content lead never stripped", rows, before)

    # Dotted tags must match on the FULL dotted number
    rows = [row(0, "may", "1510.4", head="may"),
            row(1, "be", "1510.5", gpos=2, bid=1)]
    before = list(rows)
    B._strip_helper_double_tag(rows)
    check("dotted mismatch (1510.4 vs 1510.5) not stripped", rows, before)

    # Different tag entirely -> untouched (adjacency alone never fires)
    rows = [row(0, "may", "2064", head="may"),
            row(1, "come", "2065", head="come", gpos=2, bid=1)]
    before = list(rows)
    B._strip_helper_double_tag(rows)
    check("different tags not stripped", rows, before)


def test_helper_ok_screen():
    cases = [
        ("May", "2008", True), ("And may", "977", True), ("was", "5312", True),
        ("they", "2799", True), ("Let us", "2147", True), ("It is", "3544.1", True),
        ("Let not", "3361", False),        # tag IS the negation
        ("should not", "3756", False),
        ("throne were", "2362", False),    # content lead
        ("but that", "3739", False),       # relative-pronoun tag
        ("shall", "1473", False),          # pronoun tag
        ("we should give", "4222", False), # 'give' is content
        ("", "2008", False), (None, "2008", False),
    ]
    for eng, st, want in cases:
        check(f"helper_ok({eng!r}, G{st}) == {want}", B.helper_ok(eng, st), want)


if __name__ == "__main__":
    test_strip_pass()
    test_helper_ok_screen()
    if _FAILS:
        print("\n".join(_FAILS))
        sys.exit(1)
    print("ALL PASS")
