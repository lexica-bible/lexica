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


# ── 3b. Greek-numeral gloss fill ──────────────────────────────────────────────
def test_numeral_gloss_fill():
    # Rev 13:18 tail: the three numeral letters arrive blank / bare "." -> 600 60 6
    rows = [row(0, None, "5462.1"),
            row(1, None, "3577.2"),
            row(2, ".",  "2193.2")]
    B._numeral_gloss_fill(rows)
    check("χ 5462.1 -> 600", by_pos(rows, 0)[1], "600")
    check("ξ 3577.2 -> 60",  by_pos(rows, 1)[1], "60")
    check("ϛ 2193.2 (bare '.') -> 6", by_pos(rows, 2)[1], "6")
    check("numeral head matches gloss", by_pos(rows, 0)[2], "600")

    # a real gloss already there -> left alone; a non-numeral code -> untouched
    rows = [row(0, "six hundred", "5462.1", head="hundred"),
            row(1, "word", "3056", head="word")]
    B._numeral_gloss_fill(rows)
    check("existing numeral gloss untouched", by_pos(rows, 0)[1], "six hundred")
    check("non-numeral code untouched", by_pos(rows, 1)[1], "word")


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


# ── 7b. split a verb spread over 2+ ABP slots (Jas 2:21 class) ──────────────────
def test_split_numbered():
    # Jas 2:21: one verb (G1344) whose English wraps the subject -> "1Was 5justified]".
    # The old single-number read kept slot 1 and dropped slot 5, gluing "Was justified"
    # onto position 1 (wrong order, missing bracket number). Now BOTH slots survive.
    _, _, _, w = B.parse_abp_line(
        "(Jas 2:21)  [3AbrahamG* G3588 4our FatherG3962 G1473 2notG3756 "
        "6byG1537 7worksG2041 1Was 5justified],G1344")
    was      = next(x for x in w if x[0] == "Was")
    justified= next(x for x in w if x[0].startswith("justified"))
    check("'Was' keeps slot 1", was[2], 1)
    check("'justified' keeps slot 5 (was dropped before)", justified[2], 5)
    check("both halves share the verb strongs", (was[1], justified[1]), ("G1344", "G1344"))
    check("']' closes on the last half only", (was[4], justified[4]), (False, True))
    # the bracket's slot numbers are now complete 1..7 (no hole)
    nums = sorted(x[2] for x in w if x[2] is not None)
    check("bracket numbering 1..7 complete", nums, [1, 2, 3, 4, 5, 6, 7])

    # Three-piece split (Job 3:4 "1may 5search 7out" for G327).
    _, _, _, w = B.parse_abp_line("(Job 3:4)  1may 5search 7outG327")
    check("three slots all emitted", [x[0] for x in w], ["may", "search", "out"])
    check("three slots keep their numbers", [x[2] for x in w], [1, 5, 7])
    check("three slots share one strongs", {x[1] for x in w}, {"G327"})

    # Single-number chunk is untouched -> no spurious split, byte-identical word list.
    _, _, _, w = B.parse_abp_line(
        "(Gen 1:1)  InG1722 the beginningG746 God madeG4160 G2316 all.G3956")
    check("single-number chunks: no spurious split", [x[0] for x in w],
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


# ── 11. proper-noun subject split (post-insert DB fold, like fill_blank_strongs) ──
def test_pn_subject_split():
    import sqlite3
    if B.apply_pn_subject_split is None:
        check("pn-subject fold importable", False, True)
        return
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT)")
    con.execute("CREATE TABLE words(verse_id INT, position INT, english TEXT, english_head TEXT,"
                " strongs TEXT, strongs_base TEXT, greek_pos INT, bracket_id INT, italic INT,"
                " italic_words TEXT, smcap_words TEXT, morph TEXT, lemma TEXT, is_pn INT DEFAULT 0)")
    con.execute("CREATE TABLE tipnr(name TEXT)")
    con.execute("INSERT INTO tipnr VALUES('David')")
    con.execute("INSERT INTO verses VALUES(1,'1Sa',16,23)")     # flat, unbracketed
    con.execute("INSERT INTO verses VALUES(2,'1Ch',11,7)")      # bracketed after-shape -> split
    con.execute("INSERT INTO verses VALUES(3,'X',1,1)")         # bracketed before-shape -> skip

    def w(vid, pos, eng, sbase, gp=None, bid=None, ispn=0, head=None, lemma=None):
        con.execute("INSERT INTO words(verse_id,position,english,english_head,strongs,strongs_base,"
                    "greek_pos,bracket_id,italic,italic_words,smcap_words,morph,lemma,is_pn)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (vid, pos, eng, head, sbase.lstrip("GH"), sbase, gp, bid, 0, "", "", None, lemma, ispn))

    # flat case
    w(1, 1, "David took", "G2983", head="took", lemma="lambano")   # name glued on the verb
    w(1, 2, "", "*", ispn=1)                                        # David's empty G* slot
    # bracketed after-shape: name reads first (gpos1), empty '*' right after, in bracket 7
    w(2, 1, "David stayed", "G2523", gp=1, bid=7, head="stayed")
    w(2, 2, "", "*", gp=None, bid=7, ispn=1)
    # bracketed BEFORE-shape (empty slot precedes the merge): unsupported -> skipped
    w(3, 1, "", "*", gp=None, bid=8, ispn=1)
    w(3, 2, "Moses said", "G2036", gp=1, bid=8, head="said")

    n = B.apply_pn_subject_split(con, apply=True, log=lambda *a: None)
    con.commit()
    flat = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT position,english,strongs_base FROM words WHERE verse_id=1 ORDER BY position")}
    check("flat: two splits total (flat + bracketed)", n, 2)
    check("flat: name on lower slot, '*' for import_tipnr", flat[1], ("David", "*"))
    check("flat: verb on higher slot, keeps its number", flat[2], ("took", "G2983"))
    # bracketed: name + verb both stay in bracket 7 sharing greek_pos 1 (name reads first)
    brk = {r[0]: (r[1], r[2], r[3], r[4]) for r in con.execute(
        "SELECT position,english,strongs_base,greek_pos,bracket_id FROM words WHERE verse_id=2 ORDER BY position")}
    check("bracketed: name on lower slot in-bracket, reorder# kept", brk[1], ("David", "*", 1, 7))
    check("bracketed: verb on higher slot, same reorder# + bracket", brk[2], ("stayed", "G2523", 1, 7))
    # before-shape bracketed: left untouched
    bef = [tuple(r) for r in con.execute(
        "SELECT english,strongs_base FROM words WHERE verse_id=3 ORDER BY position")]
    check("bracketed before-shape skipped", bef, [("", "*"), ("Moses said", "G2036")])


# ── 11c. εἰμί (copula) subject split — Issue 4 (non-roster subjects) ─────────────
def test_eimi_subject_split():
    import sqlite3
    if B.apply_pn_subject_split is None:
        check("pn-subject fold importable (eimi)", False, True)
        return
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT)")
    con.execute("CREATE TABLE words(verse_id INT, position INT, english TEXT, english_head TEXT,"
                " strongs TEXT, strongs_base TEXT, greek_pos INT, bracket_id INT, italic INT,"
                " italic_words TEXT, smcap_words TEXT, morph TEXT, lemma TEXT, is_pn INT DEFAULT 0)")
    con.execute("CREATE TABLE tipnr(name TEXT)")
    con.execute("INSERT INTO tipnr VALUES('David')")      # the εἰμί subjects are NOT in the roster
    con.execute("INSERT INTO verses VALUES(1,'Gen',11,30)")   # 'Sarai was'        -> split
    con.execute("INSERT INTO verses VALUES(2,'2Ki',10,15)")   # 'It is.' func lead -> skip
    con.execute("INSERT INTO verses VALUES(3,'Zep',2,6)")     # cap lead, NO empty * -> skip

    def w(vid, pos, eng, sbase, gp=None, bid=None, ispn=0, head=None):
        con.execute("INSERT INTO words(verse_id,position,english,english_head,strongs,strongs_base,"
                    "greek_pos,bracket_id,italic,italic_words,smcap_words,morph,lemma,is_pn)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (vid, pos, eng, head, sbase.lstrip("GH"), sbase, gp, bid, 0, "", "", None, None, ispn))

    # POSITIVE: copula subject not in roster, empty '*' right after -> split
    w(1, 0, "And", "G2532", head="and")
    w(1, 1, "Sarai was", "G1510", head="was")
    w(1, 2, "", "*", ispn=1)
    w(1, 3, "sterile,", "G4723", head="sterile")
    # NEGATIVE 1: function-word lead 'It is.' WITH an empty '*' -> must NOT peel
    w(2, 1, "It is.", "G1510", head="is")
    w(2, 2, "", "*", ispn=1)
    # NEGATIVE 2: capitalized non-roster lead but NO adjacent empty '*' -> must NOT peel
    w(3, 1, "Crete shall be", "G1510", head="be")
    w(3, 2, "a pasture", "G3542", head="pasture")

    B.apply_pn_subject_split(con, apply=True, log=lambda *a: None)
    con.commit()

    eimi = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT position,english,strongs_base FROM words WHERE verse_id=1 ORDER BY position")}
    check("εἰμί: name on lower slot as '*' for import_tipnr", eimi[1], ("Sarai", "*"))
    check("εἰμί: verb on higher slot keeps G1510", eimi[2], ("was", "G1510"))

    func = [tuple(r) for r in con.execute(
        "SELECT english,strongs_base FROM words WHERE verse_id=2 ORDER BY position")]
    check("εἰμί: function lead + empty '*' -> untouched", func, [("It is.", "G1510"), ("", "*")])

    noslot = [tuple(r) for r in con.execute(
        "SELECT english,strongs_base FROM words WHERE verse_id=3 ORDER BY position")]
    check("εἰμί: capitalized lead + no empty '*' -> untouched", noslot,
          [("Crete shall be", "G1510"), ("a pasture", "G3542")])


# ── 11d. capitalized-lead fallback split — RC-2 (roster-gap spellings) ──────────
def test_capfall_subject_split():
    """RC-2 (2026-07-16, reviewer-gated): a merged cell whose lead is a capitalized
    NON-roster name (genealogy spelling variants — Shaul, Zephi…) with an adjacent
    empty '*' slot still splits: the roster doesn't know the spelling, but the empty
    '*' is ABP's own declaration a proper-noun word belongs there. Same conservative
    shape as the εἰμί path: unbracketed, slot strictly AFTER, one leading word."""
    import sqlite3
    if B.apply_pn_subject_split is None:
        check("pn-subject fold importable (capfall)", False, True)
        return
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT)")
    con.execute("CREATE TABLE words(verse_id INT, position INT, english TEXT, english_head TEXT,"
                " strongs TEXT, strongs_base TEXT, greek_pos INT, bracket_id INT, italic INT,"
                " italic_words TEXT, smcap_words TEXT, morph TEXT, lemma TEXT, is_pn INT DEFAULT 0)")
    con.execute("CREATE TABLE tipnr(name TEXT)")
    con.execute("INSERT INTO tipnr VALUES('David')")      # 'Shaul' is NOT in the roster
    con.execute("INSERT INTO verses VALUES(1,'1Ch',1,49)")   # 'Shaul died,'      -> split
    con.execute("INSERT INTO verses VALUES(2,'1Ch',10,13)")  # 'he asked' lc lead -> skip
    con.execute("INSERT INTO verses VALUES(3,'Deu',15,12)")  # 'Hebrew servant' _NOT_SUBJECT -> skip
    con.execute("INSERT INTO verses VALUES(4,'X',1,1)")      # cap lead, slot BEFORE -> skip

    def w(vid, pos, eng, sbase, gp=None, bid=None, ispn=0, head=None, lemma=None):
        con.execute("INSERT INTO words(verse_id,position,english,english_head,strongs,strongs_base,"
                    "greek_pos,bracket_id,italic,italic_words,smcap_words,morph,lemma,is_pn)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (vid, pos, eng, head, sbase.lstrip("GH"), sbase, gp, bid, 0, "", "", None, lemma, ispn))

    # POSITIVE: the 1Ch 1:49 control shape — non-roster capitalized lead + empty '*' after
    w(1, 1, "Shaul died,", "G599", head="died", lemma="apothnesko")
    w(1, 2, "", "*", ispn=1)
    # NEGATIVE 1: lowercase lead with an empty '*' -> untouched
    w(2, 1, "he asked", "G1905", head="asked")
    w(2, 2, "", "*", ispn=1)
    # NEGATIVE 2: _NOT_SUBJECT lead (gentilic heading a non-verb phrase) -> untouched
    w(3, 1, "Hebrew servant", "G3816", head="servant")
    w(3, 2, "", "*", ispn=1)
    # NEGATIVE 3: capitalized non-roster lead but the empty '*' is BEFORE -> untouched
    w(4, 1, "", "*", ispn=1)
    w(4, 2, "Zephi came", "G2064", head="came")

    B.apply_pn_subject_split(con, apply=True, log=lambda *a: None)
    con.commit()

    cap = {r[0]: (r[1], r[2]) for r in con.execute(
        "SELECT position,english,strongs_base FROM words WHERE verse_id=1 ORDER BY position")}
    check("capfall: name on lower slot as '*' for import_tipnr", cap[1], ("Shaul", "*"))
    check("capfall: verb on higher slot keeps its number", cap[2], ("died,", "G599"))
    for vid, label, want in (
            (2, "lowercase lead untouched", [("he asked", "G1905"), ("", "*")]),
            (3, "_NOT_SUBJECT lead untouched", [("Hebrew servant", "G3816"), ("", "*")]),
            (4, "slot-before shape untouched", [("", "*"), ("Zephi came", "G2064")])):
        got = [tuple(r) for r in con.execute(
            "SELECT english,strongs_base FROM words WHERE verse_id=? ORDER BY position", (vid,))]
        check(f"capfall: {label}", got, want)


# ── 11b. italic-head re-clean runs AFTER the PN-subject split ───────────────────
def test_italic_heads_after_pn_split():
    # The subject-name split rewrites english_head via _head_word WITHOUT the italic
    # set, so a split verb whose gloss ends in a translator-ADDED word keeps that added
    # word as its label. The build now runs the italic-head pass AFTER the split to fix
    # it (the ordering gap that left 12 mislabeled cells live after a restore replay).
    import sqlite3
    if B.apply_pn_subject_split is None or getattr(B, "apply_italic_heads", None) is None:
        check("pn-split + italic-head folds importable", False, True)
        return
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT)")
    con.execute("CREATE TABLE words(verse_id INT, position INT, english TEXT, english_head TEXT,"
                " strongs TEXT, strongs_base TEXT, greek_pos INT, bracket_id INT, italic INT,"
                " italic_words TEXT, smcap_words TEXT, morph TEXT, lemma TEXT, is_pn INT DEFAULT 0)")
    con.execute("CREATE TABLE tipnr(name TEXT)")
    con.execute("INSERT INTO tipnr VALUES('David')")
    con.execute("INSERT INTO verses VALUES(1,'1Sa',1,1)")
    # "David take favor" glued on the verb; 'favor' is a translator addition (italic).
    con.execute("INSERT INTO words(verse_id,position,english,english_head,strongs,strongs_base,"
                "greek_pos,bracket_id,italic,italic_words,smcap_words,morph,lemma,is_pn)"
                " VALUES(1,1,'David take favor','take','2983','G2983',NULL,NULL,0,'favor','',NULL,NULL,0)")
    con.execute("INSERT INTO words(verse_id,position,english,english_head,strongs,strongs_base,"
                "greek_pos,bracket_id,italic,italic_words,smcap_words,morph,lemma,is_pn)"
                " VALUES(1,2,'',NULL,'*','*',NULL,NULL,0,'',NULL,NULL,NULL,1)")

    B.apply_pn_subject_split(con, apply=True, log=lambda *a: None)
    con.commit()
    # name -> pos1, verb 'take favor' -> pos2; its head was recomputed WITHOUT the italic
    # set, so it (wrongly) became the added word 'favor'.
    head_before = con.execute(
        "SELECT english_head FROM words WHERE verse_id=1 AND position=2").fetchone()[0]
    check("pre-pass: split verb head is the added word", head_before, "favor")

    B.apply_italic_heads(con, apply=True, log=lambda *a: None)
    head_after = con.execute(
        "SELECT english_head FROM words WHERE verse_id=1 AND position=2").fetchone()[0]
    check("post-pass: head re-cleaned to the real word", head_after, "take")

    # re-runnable: a second pass changes nothing
    again = B.apply_italic_heads(con, apply=True, log=lambda *a: None)
    check("post-pass is re-runnable (0 on second run)", len(again), 0)


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
