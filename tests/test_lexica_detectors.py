"""Control fires for the V7 flag-only detector suite (window walk, 2026-07-08).

STANDING RULE (audit tools must fail): every detector proves it fires on a KNOWN POSITIVE from
the archived defect record before any of its zeros is trusted. These are those positives:

  rendering-claim lint  — ἁμαρτία G266 pull-1 (AUDIT_lexica_rollout.md ~line 1341: gloss note
                          claimed the 2Co 5:21 rendering was "sin"; ABP's words-table rendering
                          is "sin offering" — self-refuting within the card) and οὐρανός G3772
                          attempt-1 (~line 569: note claimed capitalized "Heaven" was editorial;
                          position check showed sentence-starts — fabricated premise).
  hedged-citation lint  — δύναμις G1411 pull-2 (ENGINE_LESSONS #25a: sense prose kept Neh 9:6
                          while hedging "may overlap with senses 1 and 4 without reducing to
                          either").
  sub-use overload      — ῥῆμα G4487 sense 1, SHIPPED at exactly 4 Sub-uses (a ruled-LEGITIMATE
                          card: the flag means "merge-review", never "wrong").

Rendering values and verse prose in the fixtures are pinned from the audit doc (the authority)
and the live corpus (Pro 25:3 fetched verbatim 2026-07-08), not from recall.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import build_lexica_def as B


# ── rendering-claim lint ─────────────────────────────────────────────────────────────────────

def test_hamartia_sin_offering_fires():
    """ἁμαρτία control: claimed 'sin' vs actual rendering 'sin offering'. Substring containment
    would PASS this — the compare must be against the rendering, and must fire."""
    fires = B.check_rendering_claim(["sin"], ["sin offering"])
    assert any(f["kind"] == "rendering-mismatch" and f["gloss"] == "sin" for f in fires), fires
    assert fires[0]["rend"] == "sin offering"


def test_ouranos_positional_cap_fires():
    """οὐρανός control: 'Heaven' really is the rendering at Pro 25:3, but it opens the sentence —
    the positional probe must fire so a human adjudicates the note's 'editorial' rationale.
    Verse text is the live ABP prose, fetched verbatim."""
    verse = "Heaven is high, and the earth is deep; but the heart of a king is unascertained."
    fires = B.check_rendering_claim(["Heaven"], ["Heaven"], verse)
    assert any(f["kind"] == "positional-cap" for f in fires), fires


def test_case_mismatch_fires():
    """Case-awareness is LOAD-BEARING (see check_rendering_claim's docstring): claimed 'Heaven'
    where the corpus renders 'heaven' must fire as a case claim, not silently case-fold to a pass."""
    fires = B.check_rendering_claim(["Heaven"], ["heaven"])
    assert any(f["kind"] == "case-mismatch" for f in fires), fires


def test_etos_old_is_clean():
    """Negative control (real shipped card, ἔτος G2094): claimed 'old', rendering 'old',
    mid-sentence in the verse — no fire."""
    verse = ("And to Jonathan, son of Saul, there was a son stricken in the feet, "
             "a son five years old; and this one was in the way in the coming of the message.")
    assert B.check_rendering_claim(["old"], ["old"], verse) == []


def test_gnote_parser_reads_shipped_shape():
    """The parser reads the shipped-corpus bullet shape (real ἔτος note) and skips headless prose
    (real οὐρανός shipped note) — deliberate under-catch, manual rule stays the authority."""
    etos = ('- *old* (rendered at 2Sa 4:4; 2Ch 26:1): "contexts show etos functioning as the '
            'unit in an age expression."')
    claims = B._gnote_claims(etos)
    assert len(claims) == 1 and claims[0]["glosses"] == ["old"] and len(claims[0]["refs"]) == 2
    headless = ('"Heaven/heavens" as used in this translation is formally adequate for both '
                "senses and imports no freight that the contexts reject.")
    assert B._gnote_claims(headless) == []


# ── hedged-citation lint (rule 7c assist) ────────────────────────────────────────────────────

_DUNAMIS_HEDGE = (
    "**1. Persons constituted by their capacity — the powerful**\n\n"
    "Named alongside rulers and officials (Est 2:18). Neh 9:6 may overlap with senses 1 and 4 "
    "without reducing to either.\n"
)


def test_dunamis_hedge_fires():
    """δύναμις pull-2 control: the archived Neh 9:6 hedge must fire, with the sense number."""
    fires = B.hedged_citations(_DUNAMIS_HEDGE)
    assert any(f["sense"] == 1 and "may overlap" in f["hedge"] for f in fires), fires


def test_hedge_pass_is_not_clean_by_design():
    """The phrase list is deliberately non-exhaustive: an unlisted hedge passes the lint. This
    test PINS that under-catch as intended behavior — a pass is NOT rule 7c satisfied."""
    unlisted = ("**1. A sense**\n\nThis verse sits uneasily between the two shelves (Neh 9:6).\n")
    assert B.hedged_citations(unlisted) == []


# ── sub-use overload counter (pile item 11) ──────────────────────────────────────────────────

_RHEMA_S1 = (
    "**1. Spoken communication — something said, whether a single statement, a set of "
    "statements, or an extended address; applied to human speech and to divine speech alike**\n\n"
    "The lemma marks an instance or body of speech as what was actually uttered or declared.\n\n"
    "Sub-use: A single statement, pronouncement, or ruling (Jdg 11:10; 1Ki 2:27; 2Co 13:1).\n\n"
    "Sub-use: A plurality or body of spoken words (Num 11:24; Psa 5:1; Joh 6:68).\n\n"
    "Sub-use: Divine speech in a specific or formal delivery (Gen 15:1; Mat 4:4; 1Pe 1:25).\n\n"
    "Sub-use: An instrument or medium by which something is effected (Eph 5:26).\n\n"
    "**2. A happening, state of affairs, or situation — the thing itself rather than words "
    "about it**\n\n"
    "The lemma refers to an event, occurrence, or circumstance (Exo 2:14; Rth 3:18; Luk 1:37).\n"
)


def test_rhema_sense1_fires_at_four():
    """ῥῆμα control positive: sense 1 shipped at exactly 4 Sub-uses (headlines + lead-ins are the
    shipped card's own, prose trimmed — the counter reads only the 'Sub-use:' lead-ins). Sense 2
    (0 Sub-uses) must stay silent."""
    fires = B.subuse_overload(_RHEMA_S1)
    assert fires == [{"sense": 1, "subuses": 4}], fires


def test_three_subuses_stay_silent():
    """The threshold is 4+: three Sub-uses (the common shipped shape, e.g. ἱερεύς) never flag."""
    block = ("**1. A sense**\n\nBody.\n\nSub-use: a (Gen 1:1).\n\nSub-use: b (Gen 1:2).\n\n"
             "Sub-use: c (Gen 1:3).\n")
    assert B.subuse_overload(block) == []


# ── dynamic fed-sample curve ─────────────────────────────────────────────────────────────────

def test_dynamic_budget_curve():
    """The ruled curve (fed-40 retro item): <=40 feeds ALL (fed-gap family impossible by
    construction); 40/60/80 tiers above. Boundary values pinned exactly."""
    assert B.dynamic_budget(12) == 12          # a 12-occurrence word feeds all 12
    assert B.dynamic_budget(40) == 40          # boundary: still complete evidence
    assert B.dynamic_budget(41) == 40          # first sampled tier
    assert B.dynamic_budget(100) == 40
    assert B.dynamic_budget(101) == 60
    assert B.dynamic_budget(500) == 60
    assert B.dynamic_budget(501) == 80         # a 500+-occurrence word lands ~80
    assert B.dynamic_budget(9049) == 80        # κύριος-scale stays capped


# ── contested-verse registry routing ─────────────────────────────────────────────────────────

def test_registry_hits_2co521():
    """Registry control: a card citing 2Co 5:21 must route, carrying the verbatim dossier bar;
    an unregistered verse must not."""
    hits = B.registry_verse_hits([("2Co", 5, 21), ("Gen", 1, 8)])
    assert len(hits) == 1 and hits[0]["ref"] == "2Co 5:21", hits
    assert "ABP adjudicated the fork" in hits[0]["bar"]          # verbatim dossier text present
    assert "PARKED dossier" in hits[0]["source"]


if __name__ == "__main__":     # plain-script mode for CI + the pre-commit hook
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_lexica_detectors: ok")
