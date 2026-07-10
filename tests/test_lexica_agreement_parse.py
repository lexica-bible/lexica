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


# Real ἱερεύς G2409 draw-1 output (a "0 senses" draw under V4): NO "Senses:" header at all — a title
# line (which the prompt asked it NOT to write) then bold-numbered senses "**N. ...**", then a real
# "Gloss notes:" header. split_definition keyed the senses off a "Senses" section header, found none,
# and returned an empty block → 0 senses. Fix: fall back to the pre-section text when it holds numbered
# headlines. (Different drift from DRIFT_RAW above: there the header existed and the NUMBER was outside
# the bold; here the header is absent and the number is inside the bold.)
HEADERLESS_RAW = (
    "**G2409 hiereús**\n"
    "**1. Person who holds and performs a cultic office — one appointed to conduct sacrifice, ritual, "
    "and sacred duty within an organized religious structure** (Gen 14:18; Exo 2:16; Lev 1:5; Deu 17:12; "
    "1Ki 4:4; 2Ki 11:4; Ezr 1:5; Neh 2:16; Job 12:19; Jer 6:13; Luk 1:5; Luk 5:14; Mar 1:44; Mat 8:4; "
    "Mat 12:5; Act 14:13). Sub-use: the referent is non-Israelite — priest of Midian (Exo 2:16), priest "
    "of Zeus (Act 14:13). Sub-use: paired with a leadership stratum (Jer 6:13; Neh 2:16; Ezr 1:5).\n"
    "**2. Holder of a perpetual priestly office — designated by oath to an enduring cultic standing** "
    "(Psa 110:4; Heb 5:6; Heb 7:1; Heb 7:3; Heb 7:11; Heb 7:21).\n"
    "**3. Status-designation for a collective — a body of persons in a mediatorial relation to God** "
    "(Rev 1:6; Rev 5:10; Rev 20:6).\n"
    "**Gloss notes:** The gloss \"seven\" (Jos 6:4) is a mistranslation; it does not render hiereús.\n"
)


# Real εὐχαριστέω G2168 draw-1 output (a "0 senses" draw under V8, floor 20260710-224950),
# trimmed but faithful: a genuinely ONE-JOB word drawn in the V8 house shape — single bold
# HEADLINE (no number anywhere), organizing paragraph, "**Sub-use:**" items, then real Range /
# Gloss notes headers. Both numbered finders (bold _HEADLINE_RE and plain _PLAIN_HDR) see
# nothing → 0 senses (7 of 10 draws). Fix: the _LONE_HEADLINE_RE one-sense fallback, which must
# fire LOUDLY (sense_split_mode == 'headline') per the banked condition — never silently.
ONE_SENSE_RAW = (
    "**Expressing gratitude directed toward a recipient** — the act of verbally acknowledging a "
    "benefit, deliverance, or favorable circumstance by addressing the one held responsible for it.\n"
    "\n"
    "The lemma functions across all supplied occurrences in one way: a speaker or writer directs an "
    "expression of acknowledgment to a person or being credited with a good they have received or "
    "witnessed. Three recurring constructions can be distinguished within this single job:\n"
    "\n"
    "**Sub-use:** Directed to God for benefits received in or through other persons "
    "(Rom 1:8; 1Co 1:4; 1Th 1:2; Col 1:3; Php 1:3; Phm 1:4; Eph 5:20; 1Th 5:18).\n"
    "\n"
    "**Sub-use:** Accompanying the taking and breaking of food (Mat 15:36; Mat 26:27; Mar 8:6; "
    "Luk 22:17; Luk 22:19; 1Co 11:24; Joh 6:11; Act 27:35).\n"
    "\n"
    "**Sub-use:** Addressed directly to a person encountered or present (Luk 17:16: the Samaritan "
    "fell at Jesus's feet giving thanks to him; Rom 16:4: thanks given to Prisca and Aquila).\n"
    "\n"
    "**Range:** Most concrete in the meal settings, where the lemma marks a discrete spoken address "
    "to God at a named physical moment before eating (Mat 15:36, Act 27:35).\n"
    "\n"
    "**Gloss notes:** The single gloss \"thanks\" consistently renders the verbal act accurately.\n"
)


def _senses_block():
    return B.split_definition(DRIFT_RAW)["senses_block"]


def _has_senses_header(raw):
    for ln in raw.splitlines():
        m = B._SECTION_RE.match(ln)
        if m and m.group(1).lower() == "senses":
            return True
    return False


def test_control_headerless_fixture_has_no_senses_header():
    """Known-positive fire for the header-omission fix: this fixture has NO 'Senses:' header, so the
    OLD section-keyed extraction (sections['senses']) was empty → 0 senses. If a 'Senses' header ever
    creeps into the fixture, it stops exercising the fallback and the '== 3' below is worthless."""
    assert not _has_senses_header(HEADERLESS_RAW)
    # it DOES carry a real later section header, so the parser isn't just seeing a headerless blob
    assert any(B._SECTION_RE.match(ln) for ln in HEADERLESS_RAW.splitlines())


def test_headerless_draft_recovers_three_senses():
    """The fix: split_definition falls back to the pre-section bold-numbered senses when no 'Senses'
    header is present, recovering all three the old code 0'd — and the gloss-notes section still splits
    out separately (the fallback only claims the pre-header senses, not the whole draft)."""
    fields = B.split_definition(HEADERLESS_RAW)
    assert len(fields["sense_headlines"]) == 3
    assert len(A.per_sense(fields["senses_block"])) == 3
    assert "mistranslation" in fields["gloss_notes"]     # gloss-notes still parsed, not swallowed
    # a genuine preamble with NO numbered senses must NOT be mistaken for senses (guard holds)
    assert B.split_definition("Here is the definition.\n\nRange: it stretches wide.")["sense_headlines"] == []


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


def test_control_one_sense_fixture_has_no_numbered_sense():
    """Known-positive fire for the headline fallback: NEITHER numbered finder sees anything in the
    raw — that proves the fixture really is the un-numbered one-job shape, so the '== 1' below can
    never pass via the bold or plain path."""
    assert len(list(B._HEADLINE_RE.finditer(ONE_SENSE_RAW))) == 0
    assert len(list(B._PLAIN_HDR.finditer(ONE_SENSE_RAW))) == 0


def test_one_sense_card_parses_via_headline_fallback():
    """The fix: the opening bold headline becomes the single sense, with all sub-use refs carried
    through in its body; Range and Gloss notes still split out (the fallback claims only the senses)."""
    fields = B.split_definition(ONE_SENSE_RAW)
    assert len(fields["sense_headlines"]) == 1
    assert fields["sense_headlines"][0].startswith("Expressing gratitude")
    senses = A.per_sense(fields["senses_block"])
    assert len(senses) == 1
    refs = senses[0]["refs"]
    assert (B._norm_book("Rom"), 1, 8) in refs
    assert (B._norm_book("Luk"), 17, 16) in refs
    assert "meal settings" in fields["range"]
    assert "thanks" in fields["gloss_notes"]


def test_split_mode_reports_headline_fallback_loudly():
    """Banked condition (reviewer, 2026-07-10): every fallback parse announces itself. The mode for
    the one-sense fixture must be 'headline' — explicitly NOT 'bold' or 'plain' (guards against any
    future widening of _HEADLINE_RE, digit-anchored today) — while the numbered fixtures keep their
    modes and a no-bold-open blob stays 'none' with zero senses."""
    assert B.sense_split_mode(B.split_definition(ONE_SENSE_RAW)["senses_block"]) == "headline"
    assert B.sense_split_mode(B.split_definition(DRIFT_RAW)["senses_block"]) == "plain"
    assert B.sense_split_mode(B.split_definition(HEADERLESS_RAW)["senses_block"]) == "bold"
    # a stray preamble that does NOT open with a bold span: no fallback, no senses
    blob = "Here is the definition.\n\nRange: it stretches wide."
    assert B.split_definition(blob)["sense_headlines"] == []
    assert B.sense_split_mode(B.split_definition(blob)["senses_block"]) == "none"


if __name__ == "__main__":       # runnable as a plain script for the CI / pre-commit lists (no pytest)
    test_control_fixture_is_genuine_drift_bold_only_sees_zero()
    test_per_sense_parses_all_four_drift_senses()
    test_control_headerless_fixture_has_no_senses_header()
    test_headerless_draft_recovers_three_senses()
    test_control_one_sense_fixture_has_no_numbered_sense()
    test_one_sense_card_parses_via_headline_fallback()
    test_split_mode_reports_headline_fallback_loudly()
    print("test_lexica_agreement_parse: ok")
