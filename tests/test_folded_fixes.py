#!/usr/bin/env python3
"""Unit tests for the six post-build fixes now FOLDED into build_words_from_abp.py
(the single-pass rebuild). Each fold is a pure per-verse transform on the 13-element
row tuple, so it can be exercised with synthetic rows — no bible.db (which is PA-only).

These lock the folded logic against the canonical case each standalone fix_*.py was
written for. The whole-table fingerprint comparison on PA (old chain vs new pass) is
the end-to-end proof; this file is the fast local guard on the port itself.

Run:  python tests/test_folded_fixes.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import build_words_from_abp as B  # noqa: E402

_FAILS = []

# Row tuple layout (13): 0:pos 1:english 2:english_head 3:strongs 4:strongs_base
#   5:greek_pos 6:bracket_id 7:italic 8:italic_words 9:smcap_words 10:abp_pos 11:morph 12:lemma


def row(pos, eng, sbase, *, head=None, gpos=None, bid=None, italic=0,
        iw="", morph=None, lemma=None):
    """Build one synthetic word row. strongs_base is BARE (build-stage convention)."""
    return (pos, eng, head, sbase, sbase, gpos, bid, italic, iw, "", None, morph, lemma)


def by_pos(rows, p):
    return next(r for r in rows if r[0] == p)


def check(desc, got, want):
    if got != want:
        _FAILS.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
    else:
        print(f"  ok: {desc} -> {got!r}")


# ── 1. bracket-punctuation float ──────────────────────────────────────────────
def test_bracket_punct():
    # 1Co 4:7 shape "[2you? 1scrutinizes]" — chip should read "you scrutinizes?"
    rows = [row(0, "you?", "4771", head="you", gpos=2, bid=1),
            row(1, "scrutinizes", "350", head="scrutinizes", gpos=1, bid=1)]
    B._bracket_punct_float(rows)
    check("punct floats off non-last word", by_pos(rows, 0)[1], "you")
    check("punct lands on position-last word", by_pos(rows, 1)[1], "scrutinizes?")

    # a standalone punct token is blanked and floated
    rows = [row(0, "him", "846", head="him", gpos=1, bid=2),
            row(1, ".", "", gpos=2, bid=2),
            row(2, "loved", "25", head="loved", gpos=3, bid=2)]
    B._bracket_punct_float(rows)
    check("standalone punct token blanked", by_pos(rows, 1)[1], "")
    check("floated onto last real word", by_pos(rows, 2)[1], "loved.")

    # nothing to float -> unchanged
    rows = [row(0, "the", "3588", head=None, gpos=1, bid=1),
            row(1, "word", "3056", head="word", gpos=2, bid=1)]
    snap = [r[:] for r in rows]
    B._bracket_punct_float(rows)
    check("no trailing punct -> unchanged", rows, snap)


# ── 2. greek_pos backfill ─────────────────────────────────────────────────────
def test_greek_pos_backfill():
    # "[2God did]" split -> "God"(gpos2) + "did"(gpos None) ; "did" inherits 2
    rows = [row(0, "God", "2316", head="God", gpos=2, bid=1),
            row(1, "did", "4160", head="did", gpos=None, bid=1)]
    B._greek_pos_backfill(rows)
    check("null greek_pos inherits preceding", by_pos(rows, 1)[5], 2)

    # leading null-gp word takes the NEXT number (backward pass)
    rows = [row(0, "and", "2532", head=None, gpos=None, bid=3),
            row(1, "LORD", "2962", head="LORD", gpos=1, bid=3)]
    B._greek_pos_backfill(rows)
    check("leading null greek_pos takes next", by_pos(rows, 0)[5], 1)

    # non-bracket null greek_pos is left alone (only brackets are touched)
    rows = [row(0, "word", "3056", head="word", gpos=None, bid=None)]
    B._greek_pos_backfill(rows)
    check("non-bracket greek_pos untouched", by_pos(rows, 0)[5], None)


# ── 3. LORD-oath formula ──────────────────────────────────────────────────────
def test_lord_oath():
    rows = [row(0, "As", "2962", head="As"),
            row(1, "the LORD lives,", "2198", head="lives")]
    B._lord_oath_fix(rows)
    check("oath: kyrios gets 'As the LORD'", by_pos(rows, 0)[1], "As the LORD")
    check("oath: kyrios head -> LORD", by_pos(rows, 0)[2], "LORD")
    check("oath: zao keeps the remainder", by_pos(rows, 1)[1], "lives,")
    check("oath: zao head -> lives", by_pos(rows, 1)[2], "lives")

    # next chip is not zao -> untouched
    rows = [row(0, "As", "2962", head="As"),
            row(1, "the LORD lives,", "9999", head="lives")]
    snap = [r[:] for r in rows]
    B._lord_oath_fix(rows)
    check("oath: non-2198 neighbour untouched", rows, snap)


# ── 4. LORD-subject dual-ordering ─────────────────────────────────────────────
def test_lord_subject():
    # 1Ch 13:10 shape: verb carries "the LORD was enraged"; empty kyrios slot next
    rows = [row(0, "the LORD was enraged", "2373", head="enraged"),
            row(1, "", "2962", head=None)]
    B._lord_subject_split(rows)
    kyrios, verb = by_pos(rows, 1), by_pos(rows, 0)
    check("kyrios slot gets 'the LORD'", kyrios[1], "the LORD")
    check("kyrios head -> LORD", kyrios[2], "LORD")
    check("kyrios greek_pos = 1 (reads first)", kyrios[5], 1)
    check("verb keeps the verb gloss", verb[1], "was enraged")
    check("verb head -> enraged", verb[2], "enraged")
    check("verb greek_pos = 2", verb[5], 2)
    check("both share a new bracket", kyrios[6] == verb[6] and kyrios[6] is not None, True)

    # no adjacent empty kyrios -> untouched
    rows = [row(0, "the LORD was enraged", "2373", head="enraged"),
            row(1, "something", "2962", head="something")]
    snap = [r[:] for r in rows]
    B._lord_subject_split(rows)
    check("no empty kyrios -> untouched", rows, snap)

    # wrapped 'May the LORD add' (word before LORD) -> not the clean head shape
    rows = [row(0, "May the LORD add", "4369", head="add"),
            row(1, "", "2962", head=None)]
    snap = [r[:] for r in rows]
    B._lord_subject_split(rows)
    check("wrapped jussive -> untouched", rows, snap)


# ── 5. function-word noun-relocate ────────────────────────────────────────────
def test_funcword_noun_relocate():
    lex = {"2588": {"heart"}, "4172": {"city"}}

    # article G3588 "in his heart." next to empty G2588 (morph N) whose def has "heart"
    rows = [row(0, "in his heart.", "3588", head="heart"),
            row(1, "", "2588", morph="N-ASF")]
    B._funcword_noun_relocate(rows, lex)
    check("noun slot receives the bundled english", by_pos(rows, 1)[1], "in his heart.")
    check("noun slot keeps its OWN strongs", by_pos(rows, 1)[4], "2588")
    check("function word blanked", by_pos(rows, 0)[1], None)

    # orphan is NOT a noun (morph not N) -> untouched
    rows = [row(0, "in his heart.", "3588", head="heart"),
            row(1, "", "2588", morph="V-AAI-3S")]
    snap = [r[:] for r in rows]
    B._funcword_noun_relocate(rows, lex)
    check("non-noun orphan -> untouched", rows, snap)

    # def does not contain the head -> untouched
    rows = [row(0, "in his heart.", "3588", head="heart"),
            row(1, "", "4172", morph="N-ASF")]
    snap = [r[:] for r in rows]
    B._funcword_noun_relocate(rows, lex)
    check("def mismatch -> untouched", rows, snap)

    # PROPER-NOUN orphan is still '*' at build time -> never a target here (faithful)
    rows = [row(0, "in Zion", "1722", head="zion"),
            row(1, "", "*", morph="N-DSF")]
    snap = [r[:] for r in rows]
    B._funcword_noun_relocate(rows, lex)
    check("'*' (unresolved PN) orphan -> untouched", rows, snap)

    # in-bracket pair (round 3): host + empty noun share a bracket; host greek_pos
    # is carried to the noun so prose order holds.
    rows = [row(0, "to the city", "3588", head="city", gpos=3, bid=4),
            row(1, "", "4172", morph="N-ASF", gpos=None, bid=4)]
    B._funcword_noun_relocate(rows, lex)
    check("in-bracket: noun receives english", by_pos(rows, 1)[1], "to the city")
    check("in-bracket: noun inherits host greek_pos", by_pos(rows, 1)[5], 3)
    check("in-bracket: noun keeps its bracket", by_pos(rows, 1)[6], 4)
    check("in-bracket: host blanked", by_pos(rows, 0)[1], None)


# ── 6. g1473-gloss retag ──────────────────────────────────────────────────────
def test_g1473_gloss():
    check("lxx_align _EN_BUCKET imported", B._G1473_BUCKET is not None, True)

    # 3rd-person gloss -> autos G846, no morph needed
    rows = [row(0, "him", "1473", head="him")]
    B._g1473_gloss_retag(rows)
    check("3P 'him' -> 846", by_pos(rows, 0)[4], "846")
    check("3P lemma -> αὐτός", by_pos(rows, 0)[12], "αὐτός")
    check("3P bare strongs too", by_pos(rows, 0)[3], "846")

    # 2nd-person 'your' with genitive-singular morph -> sou G4675
    rows = [row(0, "your", "1473", head="your", morph="RP.GS")]
    B._g1473_gloss_retag(rows)
    check("2P 'your' RP.GS -> 4675", by_pos(rows, 0)[4], "4675")
    check("2P lemma -> σύ", by_pos(rows, 0)[12], "σύ")

    # 1st-singular gloss is CONSISTENT with εγω -> left untouched
    rows = [row(0, "I", "1473", head="I")]
    B._g1473_gloss_retag(rows)
    check("1S 'I' -> untouched", by_pos(rows, 0)[4], "1473")

    # reflexive -> never guessed
    rows = [row(0, "yourself", "1473", head="yourself")]
    B._g1473_gloss_retag(rows)
    check("reflexive -> untouched", by_pos(rows, 0)[4], "1473")

    # 2P with NO parseable morph -> skipped (never guessed)
    rows = [row(0, "you", "1473", head="you", morph=None)]
    B._g1473_gloss_retag(rows)
    check("2P no-morph -> untouched", by_pos(rows, 0)[4], "1473")


# ── 7. bracket-helper split (parse-time peel) ──────────────────────────────────
def test_bracket_helper_split():
    # OPEN variant: a helper word ("May") shares the bracketed verb's single
    # Strong's (G2147) and sits before "[2be found". It must be peeled OUTSIDE the
    # bracket; the verb opens the bracket and keeps the SOURCE position number (2).
    _, _, _, w = B.parse_abp_line(
        "(Psa 21:8)  May [2be foundG2147 G3588 1your hand]G5495 G1473 done.G1")
    may, verb = w[0], w[1]
    check("open: 'May' peeled to its own word", may[0], "May")
    check("open: 'May' shares the verb strongs", may[1], "G2147")
    check("open: 'May' sits OUTSIDE the bracket", (may[3], may[4]), (False, False))
    check("open: bracket opens on the verb", (verb[0], verb[3]), ("be found", True))
    check("open: verb keeps SOURCE position number", verb[2], 2)

    # CLOSE variant: "1may] be found" — the trailing "be found" is peeled OUT,
    # after the ']', sharing the same Strong's.
    _, _, _, w = B.parse_abp_line(
        "(Psa 21:8)  [2your right hand G1188 G1473 1may] be foundG2147 end.G1")
    ci = next(i for i, x in enumerate(w) if x[4])        # the closing word
    closer, trail = w[ci], w[ci + 1]
    check("close: bracket closes on 'may'", closer[0], "may")
    check("close: 'be found' peeled OUTSIDE the ']'",
          (trail[0], trail[3], trail[4]), ("be found", False, False))
    check("close: trailing word shares the strongs", trail[1], "G2147")

    # No straddling text -> unchanged: a single-word bracket is NOT split.
    _, _, _, w = B.parse_abp_line("(Gen 1:1)  [1one]G1520 thing.G2")
    check("single-word bracket stays one word", w[0][0], "one")
    check("single-word bracket opens AND closes", (w[0][3], w[0][4]), (True, True))

    # A plain verse gains no extra words (byte-identical word list).
    _, _, _, w = B.parse_abp_line(
        "(Gen 1:1)  InG1722 the beginningG746 God madeG4160 G2316 all.G3956")
    check("plain verse: no spurious split", [x[0] for x in w],
          ["In", "the beginning", "God made", "", "all."])


# ── 8. iter_source_tokens (the parser the bracket audits share) ────────────────
def test_iter_source_tokens():
    # The bracket audits delegate to this, so it must apply the SAME peel as the
    # words build — otherwise an audit drifts from the build's bracket boundaries.
    toks = list(B.iter_source_tokens(
        "May [2be foundG2147 G3588 1your hand]G5495 G1473 by allG3956 "
        "G3588 [2your right hand G1188 G1473 1may] be foundG2147 end.G1"))
    may = next(t for t in toks if t["eng"] == "May")
    check("iter: 'May' is OUTSIDE the bracket (br None)", may["br"], None)
    check("iter: 'May' shares the verb strongs", may["sbase"], "G2147")
    verb = next(t for t in toks if t["eng"] == "be found" and t["br"] is not None)
    check("iter: 'be found' opens a bracket", verb["br"], 1)
    check("iter: 'be found' keeps source position 2", verb["abp_pos"], 2)
    trailing = [t for t in toks if t["eng"] == "be found" and t["br"] is None]
    check("iter: trailing 'be found' peeled outside the ']'", len(trailing), 1)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            print(f"== {name} ==")
            fn()
    if _FAILS:
        print("\n" + "\n".join(_FAILS))
        print(f"\n{len(_FAILS)} FAILED")
        return 1
    print("\nAll folded-fix unit tests pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
