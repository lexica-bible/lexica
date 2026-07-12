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


def test_prose_stop_cases():
    # Ref followed by ordinary prose: nothing swallowed.
    assert B.ref_spans("Gen 41:32: 'the saying will be true'") == [("Gen", 41, 32)]
    assert B.ref_spans("Joh 4:18 and the woman") == [("Joh", 4, 18)]


def main():
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
    test_prose_stop_cases()
    print("test_ref_tail_expansion: all assertions passed")


if __name__ == "__main__":
    main()


