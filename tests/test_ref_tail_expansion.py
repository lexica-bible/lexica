"""
test_ref_tail_expansion.py — the #28 ref-scanner fix (batch-5 s1, 2026-07-12, JP-ruled build):
ranges ("Job 42:7–8") and comma/semicolon shorthand tails ("Rom 1:1, 4" / "Lev 21:10, 21:12")
now expand into real citations via ref_spans(), so the citation gate, coverage, LXX counts,
and the double-shelf detector all SEE the tail verses.

Exhibit provenance (the banked five-word set; TODO ticket + audit doc):
  χριστός G5547  — comma-tails "Rom 1:1, 4" / "Lev 21:10, 21:12", 4/4 draws (ENGINE_LESSONS #28)
  ἀληθής  G227   — "Job 42:7–8" in 3/3 hinted draws, 42:8 never counted (batch-5 s1)
  δόμα    G1390  — Gen 42 comma-shorthand tails ×6 (lesson #44)
  εἰρηνικός / καταπέτασμα — comma-shorthand sets; EXACT stored shapes live in the PA draw
  files, verified by the read-only audit_range_tails.py run (acceptance's PA half).

CONTROL assertions baked in (audit-tools-must-fail): the OLD bare scanner must MISS every
tail fixture here — proving the fixtures reproduce the blindness, so the passes can't be
vacuous.

Run under pytest or as a plain script. In BOTH the CI list (.github/workflows/ci.yml) and
the pre-commit hook (scripts/githooks/pre-commit).
"""
import os
import sys

_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, _SCRIPTS)
import build_lexica_def as B          # noqa: E402


def _old(text):
    """The pre-fix behavior: bare Book ch:vs matches only."""
    return [(B._norm_book(bk), int(ch), int(vs)) for bk, ch, vs in B._REF_RE.findall(text)]


# ── ἀληθής: the range-dash (en-dash, and hyphen/em-dash variants) ───────────────────────────

def test_range_dash_expands_and_control_misses():
    text = 'twice faults the friends (Job 42:7–8) for not speaking true'
    assert ("Job", 42, 8) in B.ref_spans(text)
    assert ("Job", 42, 7) in B.ref_spans(text)
    assert ("Job", 42, 8) not in _old(text), "control failed: old scanner now sees the tail"


def test_range_hyphen_and_interior():
    # A range asserts its interior: 8:13-17 yields all five verses.
    got = B.ref_spans("the legal cluster (Joh 8:13-17) extends this")
    assert got == [("Joh", 8, v) for v in (13, 14, 15, 16, 17)], got


def test_range_guards():
    # Backwards or absurd "ranges" stop expanding instead of guessing.
    assert B.ref_spans("Joh 8:17–13 nonsense") == [("Joh", 8, 17)]
    assert B.ref_spans("Psa 119:1–176 sweep") == [("Psa", 119, 1)]   # span > 30 refused


def test_refusals_surface_loudly():
    # Reviewer merge condition 2026-07-12: a refused tail must never be silent — it lands in
    # refused_tails() (printed at the gate report + by audit_range_tails.py).
    assert B.refused_tails("Psa 119:1–176 sweep") == ["Psa 119:1–176"]
    assert B.refused_tails("Joh 8:17–13 nonsense") == ["Joh 8:17–13"]
    assert B.refused_tails("clean (Job 42:7–8) range") == []


# ── χριστός: comma verse-tails and comma ch:vs tails ────────────────────────────────────────

def test_comma_verse_tail():
    text = "as promised (Rom 1:1, 4) concerning his son"
    assert B.ref_spans(text) == [("Rom", 1, 1), ("Rom", 1, 4)]
    assert ("Rom", 1, 4) not in _old(text), "control failed"


def test_comma_chapter_verse_tail():
    text = "the priestly rule (Lev 21:10, 21:12) applies"
    assert B.ref_spans(text) == [("Lev", 21, 10), ("Lev", 21, 12)]
    assert ("Lev", 21, 12) not in _old(text), "control failed"


def test_semicolon_chapter_verse_tail():
    # "; 16:15" is a citation shape (the καταπέτασμα shorthand family); a bare "; 8" is not.
    text = "sprinkled before the veil (Lev 4:17; 16:15) and hung (Exo 40:21)"
    got = B.ref_spans(text)
    assert ("Lev", 16, 15) in got and ("Exo", 40, 21) in got, got
    assert B.ref_spans("true; 8 men stood (Gen 41:32; 9 more)") == [("Gen", 41, 32)]


# ── δόμα: chained comma-shorthand ───────────────────────────────────────────────────────────

def test_chained_comma_tails():
    text = "Joseph's brothers (Gen 42:19, 31, 33, 34) and the blessing (1Ch 16:2)"
    got = B.ref_spans(text)
    assert got == [("Gen", 42, 19), ("Gen", 42, 31), ("Gen", 42, 33), ("Gen", 42, 34),
                   ("1Ch", 16, 2)], got
    assert len(_old(text)) == 2, "control failed: old scanner should see only the two full refs"


def test_tail_then_full_ref_unaffected():
    # A comma followed by a REAL Book ch:vs is not a tail — both parse as full refs, no dupes.
    got = B.ref_spans("(Gen 41:32, Deu 13:14)")
    assert got == [("Gen", 41, 32), ("Deu", 13, 14)], got


# ── consumers see the expansion ─────────────────────────────────────────────────────────────

def test_gate_path_cited_refs_deduped():
    got = B.cited_refs("(Job 42:7–8) and again Job 42:8 by name")
    assert got == [("Job", 42, 7), ("Job", 42, 8)], got


def test_double_shelf_detector_sees_tails():
    # The χριστός d1 Act 2:36 class: a comma-tail second shelving was INVISIBLE pre-fix.
    block = ("**1. title** — the anointed one (Act 2:30, 36).\n"
             "**2. name** — as a name (Act 2:36).\n")
    flagged = [d["ref"] for d in B.double_shelved(block)]
    assert "Act 2:36" in flagged, flagged


def test_numbered_book_after_comma_not_swallowed():
    # THE FIRST-RESWEEP PHANTOM (2026-07-12): a comma before a NUMBERED book name must not
    # donate its digit as a verse. "Jas 1:12, 1Pe 1:6" invented "Jas 1:1" pre-fix.
    got = B.ref_spans("beloved (Jas 1:12, 1Pe 1:6) endures")
    assert got == [("Jas", 1, 12), ("1Pe", 1, 6)], got
    got = B.ref_spans("promised (2Sa 7:8, 1Ch 17:7) forever")
    assert got == [("2Sa", 7, 8), ("1Ch", 17, 7)], got
    # Greeting-formula lists: every ref full, nothing phantom.
    got = B.ref_spans("(Gal 1:3, Eph 1:2, 2Th 1:2)")
    assert got == [("Gal", 1, 3), ("Eph", 1, 2), ("2Th", 1, 2)], got
    # And a REAL verse tail still expands when followed by a numbered book.
    got = B.ref_spans("(Rom 1:1, 4, 1Co 1:2)")
    assert got == [("Rom", 1, 1), ("Rom", 1, 4), ("1Co", 1, 2)], got


def test_prose_stop_cases():
    # Ref followed by ordinary prose: nothing swallowed.
    assert B.ref_spans("Gen 41:32: 'the saying will be true'") == [("Gen", 41, 32)]
    assert B.ref_spans("Joh 4:18 and the woman") == [("Joh", 4, 18)]


# ── BRACKETED ANNOTATION MUST NOT TRUNCATE A CITATION CHAIN (G2787 pull, 2026-07-14) ─────────
#
# THE DEFECT: the model annotates a verse where the lemma occurs twice — "Exo 25:14 [x2], 25:15".
# That prose is TRUE and the prompt never asked for it (VERSE_PROMPT has no such convention,
# machine-checked): the FEED lists one line per OCCURRENCE, so a twice-occurring verse appears
# twice and the model says so. But _TAIL_UNIT_RE only walks a book-less tail across [,;] or a
# dash, so the bracket STOPPED THE WALK and every ref after it in the chain was dropped —
# SILENTLY. G2787's coverage gate reported 9 absentees of which FIVE WERE CITED IN THE CARD.
# Worse than a gate-reporting bug: ref_spans feeds build_verses, so a lost ref never gets its
# verse attached — where the lost ref is not also FED, nothing fires and the card ships short.
# That is the silent-undercount class this scanner's docstring says it must never recreate.
#
# THE FIX IS SKIP-ONLY (reviewer-bound): the walker may STEP OVER "[...]" between a ref and its
# tail. It may NEVER COUNT bracket contents. The scanner's deliberate conservatism is untouched.
# The [x2] annotation is NOT discouraged anywhere — the parser adapts to true prose, not the
# reverse.

def test_bracket_does_not_truncate_chain():
    """The four REAL card strings from the G2787 draw (pasted from its emitted senses_block).
    Each must yield its FULL ref set — these are the five the gate called absent while the card
    cited them."""
    assert B.ref_spans("Exo 25:14 [x2], 25:15") == [("Exo", 25, 14), ("Exo", 25, 15)]
    assert B.ref_spans("Jos 3:3, 3:6 [x2], 3:8, 3:11") == [
        ("Jos", 3, 3), ("Jos", 3, 6), ("Jos", 3, 8), ("Jos", 3, 11)]
    assert B.ref_spans("1Sa 4:3, 4:4 [x2], 4:5") == [("1Sa", 4, 3), ("1Sa", 4, 4), ("1Sa", 4, 5)]
    assert B.ref_spans("2Sa 6:2, 6:3 [x2], 6:4") == [("2Sa", 6, 2), ("2Sa", 6, 3), ("2Sa", 6, 4)]


def test_bracket_skip_handles_the_live_card_shapes():
    """G3538's live shape ('9:7 [×2], 11' — a same-chapter verse tail after the annotation) and a
    multi-word bracket (G3464 wrote '[x2, including the second occurrence tagged ...]')."""
    assert B.ref_spans("Job 9:7 [×2], 11") == [("Job", 9, 7), ("Job", 9, 11)]
    assert B.ref_spans("Joh 12:3 [x2, including the second occurrence], 12:5") == [
        ("Joh", 12, 3), ("Joh", 12, 5)]


def test_bracket_contents_are_never_counted():
    """SKIP-ONLY, the binding scope. A digit-bearing bracket must not invent a ref: the walker
    steps OVER it, it never reads INSIDE it."""
    assert B.ref_spans("Gen 1:1 [see 2:3]") == [("Gen", 1, 1)]
    assert B.ref_spans("Gen 1:1 [see 2:3], 5") == [("Gen", 1, 1), ("Gen", 1, 5)]
    # a bracket carrying a full ref shape still contributes nothing of its own
    assert B.ref_spans("Gen 1:1 [cf. 2:3]") == [("Gen", 1, 1)]


def test_numbered_book_after_bracket_still_not_swallowed():
    """The docstring's standing guard must survive the skip: G5207's live shape is
    '32:14 [animal young]; 2Ch ...' — the '; 2' is 2Chronicles' DIGIT, not a verse tail."""
    assert B.ref_spans("Gen 32:14 [animal young]; 2Ch 5:2") == [("Gen", 32, 14), ("2Ch", 5, 2)]


def test_bracket_free_forms_are_byte_unchanged():
    """THE CONTROL (reviewer condition): this edit must not perturb what already works."""
    assert B.ref_spans("Exo 25:14, 25:15") == [("Exo", 25, 14), ("Exo", 25, 15)]
    assert B.ref_spans("Jos 3:3, 3:6, 3:8, 3:11") == [
        ("Jos", 3, 3), ("Jos", 3, 6), ("Jos", 3, 8), ("Jos", 3, 11)]
    assert B.ref_spans("Rom 1:1, 4") == [("Rom", 1, 1), ("Rom", 1, 4)]
    assert B.ref_spans("Job 42:7–8") == [("Job", 42, 7), ("Job", 42, 8)]


def main():
    test_bracket_does_not_truncate_chain()
    test_bracket_skip_handles_the_live_card_shapes()
    test_bracket_contents_are_never_counted()
    test_numbered_book_after_bracket_still_not_swallowed()
    test_bracket_free_forms_are_byte_unchanged()
    test_range_dash_expands_and_control_misses()
    test_range_hyphen_and_interior()
    test_range_guards()
    test_comma_verse_tail()
    test_comma_chapter_verse_tail()
    test_semicolon_chapter_verse_tail()
    test_chained_comma_tails()
    test_tail_then_full_ref_unaffected()
    test_gate_path_cited_refs_deduped()
    test_double_shelf_detector_sees_tails()
    test_numbered_book_after_comma_not_swallowed()
    test_prose_stop_cases()
    print("test_ref_tail_expansion: all assertions passed")


if __name__ == "__main__":
    main()


