#!/usr/bin/env python3
"""RULING 10 (TICKET_509 §6j, 2026-08-01): the article-slot pass's POSITIVE
predicate — the write requires that every moved word is an ABP-attested
rendering of the target's number, or it refuses.

Locks the two 2026-08-01 HALT witnesses as BRANCH-PROVEN controls, not
position-coincident ones (the Gen 22:21 lesson — a control that produces the
expected output without taking the rule's branch proves nothing):

  2Sa 12:9  'Uriah' on G3588, blank G846 one side, blank star the other — the
            shape §6i demanded for ruling 6's first real coverage. The pass must
            log 'unattested' for the G846 side and 'star' for the star side; the
            log entry is emitted BY the refusing branch, so a passing assertion
            proves the branch ran.
  Mat 20:22 'Jesus' on G3588 beside a blank G1161 (δέ, English pooled on G611
            in the source) — the "empty has a second meaning" witness.

RED-FIRST, both witnesses: the SAME fixture with the moved word hand-inserted
into the map must make the pass WRITE — proving the attestation check, not slot
geometry, is what refuses. (This reproduces the halted behaviour through the
new code, deliberately.)

Fixtures are the VERBATIM source lines from abp_texts (checked 2026-08-01 by
grep before use — a fixture string is a claim). Pure stdlib, no DB.

Run:  python tests/test_article_slot_attestation.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build_words_from_abp import (  # noqa: E402
    build_attestation_map, build_verse_words, parse_abp_line,
)

# Verbatim from abp_texts/abp_ot_texts/abp_2samuel.txt (2026-08-01)
LINE_2SA_12_9 = (
    "(2Sa 12:9)  Why is it G5100 thatG3754 you treated as worthlessG5336.3 "
    "theG3588 wordG3056 of the LORD,G2962 G3588 to doG4160 theG3588 "
    "wicked thing G4190 inG1722 his eyes?G3788 G1473 UriahG3588 G* theG3588 "
    "HittiteG* you struckG3960 byG1722 the broadsword,G4501 andG2532 G3588 "
    "his wifeG1135 G1473 you tookG2983 to yourselfG4572 forG1519 wife,G1135 "
    "andG2532 himG1473 you killedG615 byG1722 the broadswordG4501 "
    "of the sonsG5207 of Ammon.G*"
)

# Verbatim from abp_texts/abp_nt_texts/abp_matthew.txt (2026-08-01)
LINE_MAT_20_22 = (
    "(Mat 20:22)  And answeringG611 G1161 JesusG3588 G* said,G2036 "
    "You do not knowG3756 G1492 whatG5100 you ask.G154 Are you ableG1410 "
    "to drinkG4095 theG3588 cupG4221 whichG3739 IG1473 am aboutG3195 "
    "to drink?G4095 AndG2532 theG3588 immersionG908 whichG3739 I am G1473 "
    "immersedG907 to be immersed?G907 They sayG3004 to him,G1473 "
    "We are able.G1410"
)

# Verbatim from abp_texts/abp_nt_texts/abp_1corinthians.txt (2026-08-01) —
# the unbracketed 'his own' -> G2398 repair, the pass's positive exemplar.
LINE_1CO_3_8 = (
    "(1Co 3:8)  [2the oneG3588 3plantingG5452 1And]G1161 andG2532 "
    "the oneG3588 wateringG4222 are one;G1520 G1510.2.6 and eachG1538 G1161 "
    "[2his ownG3588 G2398 3wageG3408 1shall receive]G2983 according toG2596 "
    "his ownG3588 G2398 toil.G2873"
)


def _build(line, ren, log):
    _bk, _ch, _vs, abp_words = parse_abp_line(line)
    return build_verse_words(list(abp_words), [], None,
                             ren=ren, article_refusals=log)


def _slot(rows, base, english):
    for r in rows:
        if r[4] == base and (r[1] or "").strip() == english:
            return r
    return None


def test_2sa12_9_refuses_both_neighbours_by_branch():
    """Uriah stays on G3588; the log carries the star AND unattested branches.

    At PASS time the blank neighbour still carries its SOURCE number G1473 —
    the G1473->846 pronoun retag runs later in the chain, which is exactly why
    the attestation map is harvested from source numbers: pass and map speak
    the same layer. (The scratch's built rows read G846 because of that later
    retag; the write itself happened against 1473.)"""
    log = []
    rows = _build(LINE_2SA_12_9, {"1473": frozenset({"him", "his"})}, log)
    assert _slot(rows, "3588", "Uriah") is not None, "Uriah left the article slot"
    assert not any(r[4] in ("1473", "846") and (r[1] or "").strip() == "Uriah"
                   for r in rows), "Uriah written onto the pronoun — the halted defect"
    reasons = {(e[2], e[3]) for e in log}
    assert ("1473", "unattested") in reasons, \
        "no 'unattested' log for G1473 — the attestation branch never ran"
    assert any(base in ("*", "") and why == "star" for base, why in reasons), \
        "no 'star' log — ruling 6's branch never ran (Gen 22:21 coincidence class)"


def test_2sa12_9_red_first_permissive_map_writes():
    """With 'uriah' hand-attested for the pronoun the pass WRITES — proving the
    attestation check, not geometry, is what refuses above."""
    log = []
    rows = _build(LINE_2SA_12_9, {"1473": frozenset({"uriah"})}, log)
    assert any(e[3] == "WRITTEN" and e[2] == "1473" for e in log), \
        "permissive map did not write — the refusal above is not attestation's"


def test_mat20_22_refuses_pooled_delta():
    """'Jesus' must not land on the δέ whose English lives on G611."""
    log = []
    rows = _build(LINE_MAT_20_22, {"1161": frozenset({"and", "but"})}, log)
    assert _slot(rows, "3588", "Jesus") is not None, "Jesus left the article slot"
    assert not any(r[4] == "1161" and "Jesus" in (r[1] or "") for r in rows)
    assert any(e[2] == "1161" and e[3] == "unattested" for e in log)
    # the source's own attribution is untouched: G611 keeps 'And answering'
    assert any(r[4] == "611" and (r[1] or "").strip() == "And answering"
               for r in rows)


def test_mat20_22_red_first():
    log = []
    _build(LINE_MAT_20_22, {"1161": frozenset({"jesus"})}, log)
    assert any(e[3] == "WRITTEN" and e[2] == "1161" for e in log), \
        "permissive map did not write — refusal is not attestation's"


def test_1co3_8_attested_repair_writes():
    """Branch test: attested moved words DO move — the predicate is a gate, not
    a shutdown. (Synthetic map; on the REAL single-token map this row currently
    refuses — 'his' has no one-to-one page attribution under G2398 — and lands
    in --plan's unattested list. That refusal is the ruling working, not a bug.)"""
    log = []
    rows = _build(LINE_1CO_3_8, {"2398": frozenset({"his", "own"})}, log)
    assert any(e[3] == "WRITTEN" and e[2] == "2398" for e in log), \
        "attested repair refused — the pass is inert, not gated"
    assert _slot(rows, "2398", "his own") is not None


# Verbatim from abp_texts/abp_nt_texts/abp_matthew.txt (2026-08-01) — the
# false-write class the SINGLE-TOKEN harvest exists to stop: carrier 'but the'
# sits between blank G1473 (σου, its 'your' pooled on 'of your brother') and
# blank G1161 (δέ, whose word 'but' actually is).
LINE_MAT_7_3 = (
    "(Mat 7:3)  But whyG5100 G1161 do you seeG991 theG3588 speck,G2595 "
    "the oneG3588 inG1722 theG3588 eyeG3788 G3588 of your brother,G80 G1473 "
    "but theG3588 G1161 [2inG1722 G3588 3yourG4674 4eyeG3788 1beam]G1385 "
    "you do notG3756 contemplate?G2657"
)


def test_mat7_3_unique_target_wins():
    """With 'but' attested only for δέ, the write lands on G1161 — not the
    pronoun the polluted pooled harvest would have chosen."""
    log = []
    _build(LINE_MAT_7_3, {"1161": frozenset({"but"})}, log)
    written = [e for e in log if e[3] == "WRITTEN"]
    assert any(e[2] == "1161" for e in written), "the δέ repair did not land"
    assert not any(e[2] == "1473" for e in written), \
        "'but' written onto the pronoun — the Mat 7:3 false-write class"


def test_mat7_3_ambiguous_refuses_both():
    """Both neighbours attested -> 'ambiguous' refusal, never a coin-flip."""
    log = []
    _build(LINE_MAT_7_3,
           {"1161": frozenset({"but"}), "1473": frozenset({"but"})}, log)
    assert not any(e[3] == "WRITTEN" and e[2] in ("1161", "1473") for e in log
                   if e[4] == ("but",)), "ambiguous pair still wrote"
    amb = {e[2] for e in log if e[3] == "ambiguous"}
    assert {"1161", "1473"} <= amb, "ambiguity branch did not log both sides"


def test_real_map_single_token_purity():
    """The REAL map must carry the one-to-one attributions and NOT the pooled
    pollution — the measured discriminator behind the single-token ruling."""
    ren = build_attestation_map()
    assert "but" in ren.get("1161", ()), "'but' lost for δέ — harvest broken"
    assert "and" in ren.get("2532", ()), "'and' lost for καί — harvest broken"
    assert "but" not in ren.get("1473", ()), \
        "'but' attested for the pronoun — pooled pollution is back"
    assert "and" not in ren.get("1473", ()), \
        "'and' attested for the pronoun — the >=5 threshold regressed"


def test_no_map_means_no_writes():
    """ren=None leaves the pass INERT — the safe failure is zero writes."""
    for line in (LINE_2SA_12_9, LINE_MAT_20_22, LINE_1CO_3_8):
        log = []
        _build(line, None, log)
        assert not any(e[3] == "WRITTEN" for e in log), \
            "pass wrote without an attestation map"


def test_attestation_map_threshold_and_single_token():
    """build_attestation_map honours the distinct-verse threshold AND refuses
    pooled (multi-word) attributions entirely."""
    verses = [
        ("Gen", 1, 1, [("alpha", "G100", None, False, False)]),
        ("Gen", 1, 2, [("alpha", "G100", None, False, False)]),
        ("Gen", 1, 3, [("gamma", "G200", None, False, False)]),
        ("Gen", 1, 4, [("delta epsilon", "G300", None, False, False)]),
        ("Gen", 1, 5, [("delta epsilon", "G300", None, False, False)]),
    ]

    def fake_iter(*_a, **_k):
        return iter(verses)

    import build_words_from_abp as b
    orig = b.iter_verses
    b.iter_verses = fake_iter
    try:
        ren2 = b.build_attestation_map(sources=["x"], min_verses=2)
        ren1 = b.build_attestation_map(sources=["x"], min_verses=1)
    finally:
        b.iter_verses = orig
    assert ren2.get("100") == frozenset({"alpha"}), ren2
    assert "200" not in ren2, "single-verse pair passed the >=2 threshold"
    assert ren1.get("200") == frozenset({"gamma"})
    assert "300" not in ren1 and "300" not in ren2, \
        "pooled multi-word token was harvested — one-to-one rule broken"


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
