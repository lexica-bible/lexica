#!/usr/bin/env python3
"""Lane ② (TICKET_pn_star_fix.md, reviewer-ruled 2026-08-02): the PN-star
merged-verb fix pass — red-first controls on BOTH orientations.

Every control is BRANCH-PROVEN (the log entry is emitted by the branch under
test), never position-coincident. Fixtures are VERBATIM source lines from
abp_texts (grep-checked 2026-08-02 — a fixture string is a claim). Pure
stdlib + the vendored TIPNR roster; no database.

The named legitimate-genitive control (reviewer requirement, 2026-08-02):
no corpus class-B row has a name riding its own number beside an empty star
(checked over the full detector B list), so the branch is proven on the real
Mat 26:1 line with the name hand-attested onto the carrier — the pass must
refuse typed 'carrier-attested-name' — plus real-map assertions that names ARE
page-attested under their own numbers ('jesus'→G2424, 'david'→G1138), which is
what gives that refusal leg its teeth on a real "of Jesus"-class carrier.

Run:  python tests/test_pn_star_merge_fix.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build_words_from_abp import (  # noqa: E402
    build_attestation_map, build_verse_words, load_name_roster,
    parse_abp_line, pn_star_split,
)

# Verbatim from abp_texts/abp_nt_texts/abp_matthew.txt (2026-08-02)
LINE_MAT_27_26 = (
    "(Mat 27:26)  ThenG5119 he releasedG630 to themG1473 G3588 Barabbas.G* "
    "G3588 AndG1161 scourging Jesus,G* G5417 he delivered him upG3860 "
    "thatG2443 he should be crucified.G4717"
)
LINE_MAT_26_1 = (
    "(Mat 26:1)  AndG2532 it came to passG1096 whenG3753 Jesus finishedG5055 "
    "G3588 G* allG3956 G3588 these words,G3056 G3778 he saidG2036 to G3588 "
    "his disciples,G3101 G1473"
)
# Verbatim from abp_texts/abp_ot_texts/abp_genesis.txt (2026-08-02) — the
# genuine ADJACENT merge that killed the old adjacency guard: the discriminator
# is what the carrier holds, never how close the star sits.
LINE_GEN_23_19 = (
    "(Gen 23:19)  And afterG3326 G1161 these things G3778 Abraham "
    "entombedG2290 G* SarahG* G3588 his wifeG1135 G1473 inG1722 theG3588 "
    "caveG4693 of theG3588 fieldG68 atG3588 Double Cave,G1362 whichG3739 "
    "isG1510.2.3 beforeG561 Mamre;G* thisG3778 isG1510.2.3 HebronG* inG1722 "
    "theG3588 landG1093 of Canaan.G*"
)
# Verbatim from abp_texts/abp_nt_texts/abp_acts.txt (2026-08-02)
LINE_ACT_5_3 = (
    "(Act 5:3)  [3saidG2036 1AndG1161 2Peter],G* Ananias,G* whyG1302 "
    "has Satan filledG4137 G3588 G* G3588 your heartG2588 G1473 for you to "
    "lie against G5574 G1473 theG3588 [2spiritG4151 G3588 1holy],G39 "
    "andG2532 to pilferG3557 fromG575 theG3588 valueG5092 of theG3588 "
    "place?G5564"
)
LINE_ACT_7_28 = (
    "(Act 7:28)  DoG3361 [2to do away withG337 3meG1473 1you want],G1473 "
    "G2309 in whichG3739 mannerG5158 you did away withG337 "
    "the Egyptian yesterday?G5504 G3588 G*"
)

_ROSTER = None
_REAL_REN = None


def roster():
    global _ROSTER
    if _ROSTER is None:
        _ROSTER = load_name_roster()
    return _ROSTER


def real_ren():
    global _REAL_REN
    if _REAL_REN is None:
        _REAL_REN = build_attestation_map()
    return _REAL_REN


def _build(line, ren, log, names=None):
    _bk, _ch, _vs, abp_words = parse_abp_line(line)
    return build_verse_words(list(abp_words), [], None, ren=ren,
                             names=roster() if names is None else names,
                             pn_star_refusals=log)


def _slot(rows, base, english):
    for r in rows:
        if r[4] == base and (r[1] or "").strip() == english:
            return r
    return None


def test_roster_hazard_premise():
    """The measured hazard the splitter legs exist for: the roster really does
    contain common English words — and the real names the fixtures need."""
    names = roster()
    for common in ("the", "new", "mount", "queen"):
        assert common in names, "hazard premise gone: %r left the roster" % common
    for name in ("jesus", "abraham", "satan", "david", "egyptian"):
        assert name in names, "fixture name %r missing from roster" % name


def test_splitter_legs():
    """'the' (roster + stays-word) and lowercase roster words never classify as
    names; a capitalized roster name does."""
    names = roster()
    n, o = pn_star_split("The Egyptian yesterday?", names)
    assert n == [1] and o == [0, 2], (n, o)
    n, o = pn_star_split("the mount of Zion", names)   # lowercase roster words stay
    assert n == [3] and o == [0, 1, 2], (n, o)
    n, o = pn_star_split("Jesus finished", names)
    assert n == [0] and o == [1], (n, o)


def test_class_a_positive_mat27_26():
    """'scourging' leaves the star for G5417; 'Jesus,' stays; bracket pair with
    English order (star's name reads second: 'scourging Jesus')."""
    log = []
    rows = _build(LINE_MAT_27_26, {"5417": frozenset({"scourging"})}, log)
    assert any(e[0] == "A" and e[4] == "WRITTEN" and e[3] == "5417"
               for e in log), "class-A write branch never ran"
    # the trailing comma floats to the bracket's position-last chip afterward
    # (_bracket_punct_float, the established bracket convention)
    verb = _slot(rows, "5417", "scourging,")
    star = _slot(rows, "*", "Jesus")
    assert verb is not None, "'scourging' did not land on G5417"
    assert star is not None, "the star lost its name"
    assert verb[6] == star[6] and verb[6] is not None, "no shared bracket"
    assert (verb[5], star[5]) == (1, 2), "English order lost (moved run leads)"


def test_class_a_red_unattested():
    """Same fixture, 'scourging' NOT attested for G5417 → typed 'unattested' —
    attestation refuses, not slot geometry."""
    log = []
    rows = _build(LINE_MAT_27_26, {"5417": frozenset()}, log)
    assert any(e[0] == "A" and e[4] == "unattested" and e[3] == "5417"
               for e in log), "the unattested branch never ran"
    assert _slot(rows, "*", "scourging Jesus,") is not None, \
        "star changed despite the refusal"


def test_class_b_positive_mat26_1():
    """'Jesus' moves to the empty star; 'finished' stays on G5055; the blank
    G3588 between them is untouched."""
    log = []
    rows = _build(LINE_MAT_26_1, {"5055": frozenset({"finished"})}, log)
    assert any(e[0] == "B" and e[4] == "WRITTEN" and e[3] == "5055"
               for e in log), "class-B write branch never ran"
    star = _slot(rows, "*", "Jesus")
    verb = _slot(rows, "5055", "finished")
    assert star is not None, "'Jesus' did not land on the star"
    assert verb is not None, "the carrier lost its own word"
    assert star[6] == verb[6] and star[6] is not None, "no shared bracket"
    assert (star[5], verb[5]) == (1, 2), "English order lost ('Jesus finished')"
    assert not any(r[4] == "3588" and (r[1] or "").strip() == "Jesus"
                   for r in rows), "'Jesus' leaked onto the article"


def test_class_b_red_no_roster():
    """Roster without 'jesus' → typed 'no-name' (the B2 branch), no write."""
    log = []
    names = set(roster()) - {"jesus"}
    _build(LINE_MAT_26_1, {"5055": frozenset({"finished"})}, log, names=names)
    assert any(e[0] == "B" and e[4] == "no-name" for e in log), \
        "the no-name branch never ran"
    assert not any(e[4] == "WRITTEN" for e in log), "wrote without a roster name"


def test_class_b_legitimate_genitive_refuses():
    """THE NAMED CONTROL (reviewer 2026-08-02): a capitalized roster name that
    the page itself attests on the carrier's number ('of Jesus' class) must
    refuse, typed 'carrier-attested-name' — the never-attested leg, branch-run."""
    log = []
    rows = _build(LINE_MAT_26_1, {"5055": frozenset({"finished", "jesus"})}, log)
    assert any(e[0] == "B" and e[4] == "carrier-attested-name" and e[3] == "5055"
               for e in log), "the carrier-attested-name branch never ran"
    assert not any(e[4] == "WRITTEN" for e in log), \
        "wrote a name the page attests on the carrier"
    assert _slot(rows, "5055", "Jesus finished") is not None, \
        "carrier changed despite the refusal"


def test_gen23_19_adjacent_genuine_merge_writes():
    """Gen 23:19 — directly adjacent AND genuine. The reverted adjacency guard
    stays dead: 'Abraham' moves to the empty star; 'Sarah' keeps her own star."""
    log = []
    rows = _build(LINE_GEN_23_19, {"2290": frozenset({"entombed"})}, log)
    assert any(e[0] == "B" and e[4] == "WRITTEN" and e[3] == "2290"
               for e in log), "the adjacent genuine merge did not write"
    assert _slot(rows, "*", "Abraham") is not None
    assert _slot(rows, "2290", "entombed") is not None
    assert _slot(rows, "*", "SarahG*") is None and \
        _slot(rows, "*", "Sarah") is not None, "Sarah's own star was disturbed"


def test_act5_3_straddle_refuses():
    """'has Satan filled' — kept words both sides of the name → typed
    'straddle'; two slots cannot hold three positions."""
    log = []
    rows = _build(LINE_ACT_5_3, {"4137": frozenset({"has", "filled"})}, log)
    assert any(e[0] == "B" and e[4] == "straddle" and e[3] == "4137"
               for e in log), "the straddle branch never ran"
    assert _slot(rows, "4137", "has Satan filled") is not None, \
        "straddled phrase did not stay whole"


def test_act7_28_stays_word_never_moves():
    """'the Egyptian yesterday?' — 'the' is in the roster but is a stays-word,
    so the split is Egyptian-only and straddles → refuse; 'the' never reaches a
    star under any map."""
    log = []
    rows = _build(LINE_ACT_7_28, {"5504": frozenset({"yesterday"})}, log)
    assert any(e[0] == "B" and e[4] == "straddle" for e in log), \
        "expected the straddle refusal for the Egyptian carrier"
    assert not any(r[4] == "*" and "the" in (r[1] or "").lower().split()
                   for r in rows), "'the' reached a star slot"


def test_no_map_or_roster_means_no_writes():
    """ren=None or names=None leaves the pass INERT — zero writes."""
    for line in (LINE_MAT_27_26, LINE_MAT_26_1, LINE_GEN_23_19):
        for ren, names in ((None, roster()), ({"5417": frozenset({"scourging"})}, None)):
            log = []
            _build(line, ren, log, names=names if names is not None else set())
            if names is None:
                log2 = []
                _bk, _ch, _vs, abp_words = parse_abp_line(line)
                build_verse_words(list(abp_words), [], None, ren=ren,
                                  names=None, pn_star_refusals=log2)
                assert not any(e[4] == "WRITTEN" for e in log2), \
                    "pass wrote without a roster"
            else:
                assert not any(e[4] == "WRITTEN" for e in log), \
                    "pass wrote without an attestation map"


def test_real_map_names_not_attested_finding():
    """PINNED FINDING (2026-08-02): on the REAL harvest NO name sits under its
    own number ('jesus'/G2424, 'david'/G1138, 'israel'/G2474 all absent) —
    ABP prints proper nouns on G* stars, so the single-token harvest never
    sees them. Gate (d) is therefore PROTECTIVE on today's corpus (it fires
    only on roster-collision words; branch proven synthetically above), and
    the full detector B list holds zero own-number-name carriers (grep-checked
    2026-08-02). If this pin ever flips, the harvest's environment changed —
    re-derive gate (d)'s real firing count in the sizing before trusting it."""
    ren = real_ren()
    for base, name in (("2424", "jesus"), ("1138", "david"), ("2474", "israel")):
        assert name not in ren.get(base, ()), \
            "%r now attested under G%s — harvest environment changed" % (name, base)


def main():
    tests = [(k, v) for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("PASS  %s" % name)
        except AssertionError as e:
            failed += 1
            print("FAIL  %s: %s" % (name, e))
    print("%d/%d passed" % (len(tests) - failed, len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
