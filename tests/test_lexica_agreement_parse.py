"""
test_lexica_agreement_parse.py — the reviewer's per-sense parse must survive header/bold DRIFT.

Regression lock for the μέγας G3173 break (agreement run 2026-07-07): 5 of 10 draws came back with
'0 senses' because the model numbered its senses '1. **text**' (number OUTSIDE the bold) under a
'**Senses:**' header, and lexica_agreement.per_sense kept its OWN bold-only splitter (build_lexica_def
._HEADLINE_RE, which needs '**1. text**' — number INSIDE the bold). The rich 4-sense answers were
thrown away. Fix: per_sense now reuses the production splitter B._sense_spans (plain-number fallback).

The fixture is a faithful snippet of that real draw-1 raw (not a hand-built approximation). The CONTROL
assertion is baked into the test permanently: the bold-only _HEADLINE_RE must find ZERO headlines in
this fixture — that proves the fixture really is the drift format, so the '== 4' can never pass for the
wrong reason (e.g. against a good-format string the old code would also have parsed).
"""
import os
import sys

_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, _SCRIPTS)
import build_lexica_def as B          # noqa: E402
import lexica_agreement as A          # noqa: E402


# Real μέγας G3173 draw-1 output (the "0 senses" draw), trimmed: senses under a "**Senses:**" header,
# each numbered "N. **headline**" with the number OUTSIDE the bold — the exact drift that broke it.
DRIFT_RAW = (
    "**Senses:**\n"
    "1. **Of large scale, intensity, or degree — describing things as exceeding the ordinary in "
    "size, force, or significance.** This is the dominant use. (Gen 1:16, Deu 1:7, Jos 8:29, "
    "Num 11:33, Jdg 2:7, 1Ki 1:40, 2Ki 3:27, 1Ch 11:14, Ezr 3:11, Neh 1:3, Est 4:1, Mat 2:10, "
    "Rev 1:10, Rom 9:2, 1Ti 3:16, 1Ti 6:6, 2Ti 2:20, Eph 5:32, Jud 1:6, Act 2:20, 1Co 9:11, 2Co 11:15)\n"
    "2. **Of persons: high in rank, standing, or prominence — 'great' in social or positional terms.** "
    "Applied to office-holders and the eminent. (Lev 21:10, 2Sa 7:9, Mar 10:42, Act 8:9, Heb 4:14, "
    "Luk 1:15, Tit 2:13)\n"
    "3. **Of persons or things: senior in age or sequence — the comparatively older or prior.** "
    "The comparative form carries the temporal sense. (Exo 2:11, 1Sa 17:13)\n"
    "4. **Comparative: exceeding another in degree, rank, or extent (superlative included).** "
    "One thing surpasses another. (Jos 19:9, 2Ch 17:12, 1Co 13:13)\n"
    "\n"
    "**Range:**\n"
    "From physical bulk to social eminence to seniority.\n"
)


def _senses_block():
    return B.split_definition(DRIFT_RAW)["senses_block"]


def test_control_fixture_is_genuine_drift_bold_only_sees_zero():
    """The known-positive fire: the OLD bold-only regex finds nothing here, so this fixture really is
    the format that broke the reviewer. If this ever starts matching, the fixture stopped testing the
    drift and the '== 4' below is worthless."""
    block = _senses_block()
    assert block, "split_definition should still extract the senses block from a '**Senses:**' header"
    assert len(list(B._HEADLINE_RE.finditer(block))) == 0


def test_per_sense_parses_all_four_drift_senses():
    """The fix: per_sense (via _sense_spans' plain fallback) recovers all four senses the old code 0'd."""
    senses = A.per_sense(_senses_block())
    assert len(senses) == 4
    # each sense carried its grounding refs through (the fingerprint the cross-draw vote aligns on)
    assert all(s["refs"] for s in senses)
    # sense 1 is the dense magnitude list; a few of its verses must be present
    s1_refs = senses[0]["refs"]
    assert (B._norm_book("Gen"), 1, 16) in s1_refs
    assert (B._norm_book("Est"), 4, 1) in s1_refs


if __name__ == "__main__":       # runnable as a plain script for the CI / pre-commit lists (no pytest)
    test_control_fixture_is_genuine_drift_bold_only_sees_zero()
    test_per_sense_parses_all_four_drift_senses()
    print("test_lexica_agreement_parse: ok")
