#!/usr/bin/env python3
"""written_ranges() — the COMPLIANCE channel for the anti-range constraint (ENGINE_LESSONS #80).

WHY ZEROS FROM THIS MUST BE EARNED. The gate report prints this as report-only, so a silent zero
reads as "this card wrote no ranges" — which is a claim. Certification rule: a detector must be
shown firing on a KNOWN POSITIVE before a zero from it means anything. The positives below are
the real ones: the three words that actually paid for this lesson.

DISTINCT FROM THE CITATION GATE. The gate asks "is this cited verse real / does it carry the
lemma" and already catches a false interior. This asks "was a range written at all" — a contract
breach even when the interior is true. Blocking on it was REJECTED (duplicated teeth + false
fires); it reports.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build_lexica_def import written_ranges   # noqa: E402


def test_fires_on_the_three_words_that_paid():
    """G3793's gloss note (four phantom citations, 19:2-5), and the two banked hint pins."""
    assert written_ranges("the crowd praises (Rev 19:1-6)") == ["Rev 19:1-6"]
    assert written_ranges("the courtroom verses (Joh 8:13-17)") == ["Joh 8:13-17"]   # G227
    assert written_ranges("the meal verses (Luk 22:17-19)") == ["Luk 22:17-19"]      # G2168


def test_fires_on_the_en_dash_the_live_cards_actually_use():
    """Live cards write en-dashes, not hyphens (baseline read, 2026-07-15: every one of the 50).
    A hyphen-only detector would have reported a FALSE ZERO across the whole corpus."""
    assert written_ranges("(Ezra 6:11–12)") == ["Ezr 6:11–12"]      # en-dash
    assert written_ranges("(Ezra 6:11—12)") == ["Ezr 6:11—12"]      # em-dash


def test_fires_on_a_range_after_a_chapter_hop():
    """The tail walker keeps walking after a chapter hop; a range in the second unit still counts."""
    assert written_ranges("chained (Mat 5:3, 6:9-11)") == ["Mat 6:9-11"]


def test_counts_every_writing_not_every_unique_range():
    """A range written twice is TWO breaches of the constraint. The live baseline depends on this
    (G2962 = Exo 21:28-29 twice, G956 = 1Sa 20:36-37 twice)."""
    assert written_ranges("(Exo 21:28-29) ... again (Exo 21:28-29)") == \
        ["Exo 21:28-29", "Exo 21:28-29"]


def test_silent_on_the_shape_the_constraint_asks_for():
    """The whole point: an enumerated list is COMPLIANT and must not fire, or the report cries
    wolf on exactly the prose the prompt is trying to buy."""
    assert written_ranges("the crowd praises (Rev 19:1, 19:6)") == []
    assert written_ranges("no refs here at all") == []


def test_silent_on_the_two_historical_traps():
    """Both are banked ref_spans traps and both LOOK like a tail. A numbered book name ("1Pe")
    is not a verse tail (2026-07-12 phantom :1/:2 deltas), and a bracketed annotation must be
    stepped OVER, never read into (G2787, 2026-07-14)."""
    assert written_ranges("(Jas 1:12, 1Pe 1:6)") == []
    assert written_ranges("(Exo 25:14 [x2], 25:15)") == []


def test_reports_ranges_the_expander_refuses():
    """A refused range (backwards, or wider than 30) is still a WRITTEN range — the constraint
    breach is the writing, not the expansion. These must not vanish from the compliance count
    just because ref_spans declined to expand them; that would recreate the silent-undercount
    class this scanner must never repeat."""
    assert written_ranges("backwards (Mat 5:9-2)") == ["Mat 5:9-2"]
    assert written_ranges("wide (Luk 1:1-99)") == ["Luk 1:1-99"]


if __name__ == "__main__":
    fails = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except AssertionError as e:
                fails.append(name)
                print(f"  FAIL {name}\n       {e}")
    print(("FAILED: " + ", ".join(fails)) if fails else "all green")
    sys.exit(1 if fails else 0)
