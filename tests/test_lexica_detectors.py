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


def test_2ch413_phrase_claim_is_clean():
    """2Ch 4:13 fixture (the JP-caught fragment-rendering finding, 2026-07-12; word rows
    source-verified against the printed ABP that session): pos-7 english 'latticed works;'
    head 'latticed' italic_words 'works' · pos-13 english 'latticed work' head 'work' no italics.
    A note claiming *latticed work* — the TRUE rendering — must be clean now (the head-only
    compare fired it as a mismatch, the δίκτυον *work* bullet's cause); claiming the bare
    fragment *work* stays clean too (it IS a head)."""
    heads = ["latticed", "work"]
    phrases = [("latticed works;", "works"), ("latticed work", "")]
    assert B.check_rendering_claim(["latticed work"], heads, "", phrases) == []
    assert B.check_rendering_claim(["work"], heads, "", phrases) == []


def test_phrase_containment_still_fires():
    """The ἁμαρτία protection survives phrase-awareness: a claim CONTAINED in the phrase but not
    equal to it (or to the head, or to the phrase minus additions) must still fire."""
    fires = B.check_rendering_claim(["sin"], ["offering"], "", [("sin offering", "")])
    assert any(f["kind"] == "rendering-mismatch" and f["gloss"] == "sin" for f in fires), fires


def test_isa245_bartered_away_is_clean():
    """G236 Isa 24:5 control (the over-called defect that survived two adjudications): ABP prints
    'bartered away', the head column keeps only 'away'. Claiming *bartered away* is clean; a
    fabricated *barter* still fires."""
    heads = ["away"]
    phrases = [("bartered away", "")]
    assert B.check_rendering_claim(["bartered away"], heads, "", phrases) == []
    fires = B.check_rendering_claim(["barter"], heads, "", phrases)
    assert any(f["kind"] == "rendering-mismatch" for f in fires), fires


def test_identical_string_punct_noise_is_dead():
    """The identical-string noise family (G236, fired on all three draws): a claimed gloss that
    differs from the rendering only by outer punctuation ('exchange,' vs 'exchange') is the SAME
    string, never a mismatch."""
    assert B.check_rendering_claim(["exchange,"], ["exchange"]) == []
    assert B.check_rendering_claim(["away."], ["away"]) == []


def test_emphasis_italics_are_not_gloss_claims():
    """G162 d1 *perform* control (emphasis-italics-as-gloss noise class): italics in the bullet
    head AFTER the ref paren opens are emphasis, not rendering claims. The leading gloss before
    the paren is still read."""
    bullet = ('- *captive* (1Ch 5:21; 2Ch 21:17, where the raiders *perform* the taking): '
              'prose continues.')
    claims = B._gnote_claims(bullet)
    assert len(claims) == 1 and claims[0]["glosses"] == ["captive"], claims


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


# ── double-shelve flag (grounding-list citations only, 2026-07-12) ───────────────────────────

_DBL_BLOCK = (
    "**1. Persons taken captive** (1Ch 5:21; 2Ch 21:17; Amo 1:6)\n\nProse.\n\n"
    "**2. Property carried off** (1Ch 5:21; 2Ch 14:15)\n\nProse.\n"
)


def test_double_shelve_fires_on_grounding_lists():
    """G162 d1 control: a verse in TWO senses' grounding lists must fire, exactly once, naming
    both senses. The single-list verses stay silent."""
    fires = B.double_shelved(_DBL_BLOCK)
    assert fires == [{"ref": "1Ch 5:21", "senses": [1, 2]}], fires


def test_prose_mention_is_not_a_second_shelf():
    """G162 d3 Amo 1:6 control (prose-mention-counted-as-citation noise class): sense 2 MENTIONING
    sense 1's verse in prose — the convention's legal cross-reference form — is not a second
    shelving. Only a second grounding list fires."""
    block = (
        "**1. Persons taken captive** (Amo 1:6; 2Ch 21:17)\n\nProse.\n\n"
        "**2. Property carried off** (1Ch 5:21)\n\nThe raid catalog (as Amo 1:6 shows for "
        "persons) keeps goods distinct.\n"
    )
    assert B.double_shelved(block) == []


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


# ── #30 floor-vs-ship placement diff (un-parked step 4, 2026-07-10) ──────────────────────────
# Control positives are the three BANKED break records + the banked clean negative
# (AUDIT_lexica_rollout.md: G1119 γόνυ pull-1 · G3538 νίπτω pull-1 · G2657 κατανοέω hinted
# draw-1 — the hard class · G1350 δίκτυον ruled-legal fold). PINNED facts (verse identities,
# floor shapes, tallies) are from the audit doc; the OTHER cluster members are synthetic
# scaffolding sized to the banked cluster shapes — the detector reads structure, not corpus.

def _shelves(*sense_ref_lists):
    """Ship-side helper: sense_specs()-shaped senses from ref-tuple lists."""
    return [{"headline": f"sense {i}", "refs": list(refs)}
            for i, refs in enumerate(sense_ref_lists, 1)]


_GONY_PHYS = [("Heb", 12, 12), ("Isa", 35, 3), ("Job", 4, 4)]                       # scaffolding
_GONY_KNEEL = [("Luk", 5, 8), ("2Ki", 1, 13),                                       # PINNED
               ("Act", 9, 40), ("Act", 20, 36), ("1Ki", 8, 54), ("Ezr", 9, 5)]      # scaffolding


def test_gony_pull1_fires():
    """γόνυ control (#30 born here): floor 3/3 STABLE {2:3}, Luk 5:8 + 2Ki 1:13 homed with the
    kneeling cluster in EVERY draw; the ship draw moved both under PHYSICAL (the invented
    'approach-posture' sub-use lives inside that numbered sense). Every machine gate was green
    (35/35) — this flag must fire, on exactly the two moved verses (the movers), never on the
    stationary kneeling verses."""
    floor = [[set(_GONY_PHYS), set(_GONY_KNEEL)]] * 3
    ship = _shelves(_GONY_PHYS + [("Luk", 5, 8), ("2Ki", 1, 13)],
                    [r for r in _GONY_KNEEL if r not in {("Luk", 5, 8), ("2Ki", 1, 13)}])
    fires = B.floor_ship_diff(floor, ship)
    assert sorted(f["ref"] for f in fires) == ["2Ki 1:13", "Luk 5:8"], fires
    luk = next(f for f in fires if f["ref"] == "Luk 5:8")
    assert luk["kept"] == ["2Ki 1:13"]                       # the movers moved TOGETHER
    assert all(b["same"] == 3 and b["n"] == 3 for b in luk["broken"])   # off 3/3 homes


_NIPTO_TRIO = [("Psa", 26, 6), ("Psa", 58, 10), ("Psa", 73, 13)]                    # PINNED
_NIPTO_WASH = _NIPTO_TRIO + [("Gen", 18, 4), ("Exo", 30, 18), ("Joh", 13, 5),       # scaffolding
                             ("Mat", 6, 17), ("2Ki", 5, 12), ("Gen", 43, 31)]


def test_nipto_pull1_fires():
    """νίπτω control (#30 second instance): floor 3/3 STABLE at 2 (washing | Job 20:23); the
    ship draw promoted the Psalms trio onto an invented top-level 'rhetorical hand-washing'
    sense, breaking a unanimous 3/3 cluster. Job 20:23 (single-verse sense, no floor company)
    must stay silent; so must the stationary washing verses."""
    floor = [[set(_NIPTO_WASH), {("Job", 20, 23)}]] * 3
    ship = _shelves([r for r in _NIPTO_WASH if r not in set(_NIPTO_TRIO)],
                    _NIPTO_TRIO,
                    [("Job", 20, 23)])
    fires = B.floor_ship_diff(floor, ship)
    assert sorted(f["ref"] for f in fires) == ["Psa 26:6", "Psa 58:10", "Psa 73:13"], fires


# κατανοέω floor shape (audit doc, agreement_G2657 10-run): two poles — visual 10/10 together,
# mental 9-10/10 — plus banked either-home MIGRATORS that flip draw-to-draw. Psa 10:14 = floor
# mental 9/10 / visual 1/10 (pinned tallies from the hinted-draw-1 record).
_KAT_VISUAL = [("Neh", 2, 13), ("Num", 32, 8), ("Act", 27, 39), ("Act", 11, 6),     # PINNED
               ("1Ki", 3, 21), ("Exo", 33, 8), ("Job", 30, 20), ("Psa", 22, 17), ("Gen", 3, 6)]
_KAT_MENTAL = [("Heb", 3, 1), ("Heb", 10, 24), ("Psa", 119, 15), ("Hab", 3, 2),     # PINNED
               ("Job", 23, 15), ("Psa", 94, 9), ("Mat", 7, 3), ("Luk", 6, 41), ("Isa", 57, 1)]


def _kat_floor():
    """10 floor draws: poles stable; Psa 10:14 mental in 9, visual in 1; two migrators flipping
    on DIFFERENT schedules (either-home class — their company with any pole stays a minority,
    so the detector must be structurally blind to them)."""
    draws = []
    for d in range(1, 11):
        vis, men = set(_KAT_VISUAL), set(_KAT_MENTAL)
        (vis if d == 10 else men).add(("Psa", 10, 14))
        (vis if d <= 5 else men).add(("Jas", 1, 23))
        (vis if 4 <= d <= 8 else men).add(("Luk", 12, 24))
        draws.append([vis, men])
    return draws


def test_katanoeo_hint1_fires_the_hard_class():
    """κατανοέω hinted-draw-1 control — THE HARD CLASS: an otherwise-PASSING draw (hint exit
    terms all green) carrying ONE 0/10 off-floor placement (Exo 33:8 filed MENTAL; floor visual
    10/10, mental 0/10) plus Psa 10:14 filed VISUAL (floor mental 9/10). If #30 catches this,
    it's real. Migrators land wherever — no fire; every stationary pole verse — no fire."""
    ship = _shelves([r for r in _KAT_VISUAL if r != ("Exo", 33, 8)]
                    + [("Psa", 10, 14), ("Jas", 1, 23)],
                    _KAT_MENTAL + [("Exo", 33, 8), ("Luk", 12, 24)])
    fires = B.floor_ship_diff(_kat_floor(), ship)
    assert sorted(f["ref"] for f in fires) == ["Exo 33:8", "Psa 10:14"], fires
    exo = next(f for f in fires if f["ref"] == "Exo 33:8")
    assert exo["kept"] == [] and len(exo["broken"]) == 8                  # off its whole home
    assert all(b["same"] == 10 for b in exo["broken"])                    # 10/10 floor company


def test_diktyon_fold_is_clean():
    """δίκτυον clean negative: floor 3/3 {3:3} (fishing | trap | architecture); the ship draw
    folded trap to a SUB-USE under a combined catching sense — ruled LEGAL, zero verses changed
    cluster. Hierarchy demotion is not a cluster break: a merge must NEVER fire this flag."""
    fish = [("Mat", 4, 20), ("Luk", 5, 4), ("Joh", 21, 6), ("Ecc", 9, 12),
            ("Eze", 26, 5), ("Pro", 1, 17)]
    trap = [("Psa", 25, 15), ("Psa", 31, 4), ("Job", 18, 8)]
    arch = [("1Ki", 7, 17), ("Jer", 52, 22), ("Exo", 27, 4)]
    floor = [[set(fish), set(trap), set(arch)]] * 3
    assert B.floor_ship_diff(floor, _shelves(fish + trap, arch)) == []


def test_floor_diff_record_reads_the_real_splitter_and_names_unseen():
    """End-to-end shape check: floor_diff_record parses a senses_block with the PRODUCTION
    splitter and lists floor-unseen citations so an empty fires list can't read as 'every
    citation checked' (σελήνη class). Majority default pinned: N=3 → 2, N=10 → 6."""
    floor = {"draws": [[{("Gen", 1, 1), ("Gen", 1, 2)}, {("Exo", 2, 2)}]] * 3,
             "meta": {"file": "agreement_G0000_v7_test.json", "strongs": "G0000",
                      "prompt": "v7", "runs": 3}}
    block = ("**1. First job** (Gen 1:1; Gen 1:2)\n\nProse.\n\n"
             "**2. Second job** (Exo 2:2; Rev 22:21)\n\nProse.\n")
    rec = B.floor_diff_record(floor, block)
    assert rec["fires"] == [] and rec["floor_unseen"] == ["Rev 22:21"], rec
    assert rec["majority"] == 2 and rec["runs"] == 3
    assert B.floor_ship_diff([[{("Gen", 1, 1)}]] * 10, []) == []          # n=10 → majority 6, no ship refs


# ── V11.1 ticket 5: per-bullet SET semantics (_claim_fires; ruled 2026-07-12) ────────────────
# The G236 d1 six-coarse-fires class: a bullet claiming several glosses across several refs
# means "distributed across", never "each at every". d1 bytes OVERWRITTEN — the class
# fixtures below are labeled RECONSTRUCTED per the standing ruling; the check_rendering_claim
# CORE they compose is untouched and stays pinned by every fixture above.

def test_claim_fires_distributed_bullet_is_clean():
    """RECONSTRUCTED (coarse class): glosses [change, exchange] across refs A/B where A
    renders 'change' and B renders 'exchange' — the distributed claim is TRUE and must be
    clean. Old semantics fired 2 (each gloss at the other's ref)."""
    per_ref = {("Psa", 102, 26): (["change"], "", None),
               ("Lev", 27, 10): (["exchange"], "", None)}
    assert B._claim_fires(["change", "exchange"], per_ref) == []


def test_claim_fires_psa10620_anchor():
    """RECONSTRUCTED real-catch anchor (G236 d1, audit-adjudicated kill): a claimed gloss the
    corpus renders nowhere in the bullet's refs fires — EXACTLY ONCE for a single-gloss
    single-ref bullet (never the old per-pair double count)."""
    per_ref = {("Psa", 106, 20): (["changed"], "", None)}
    fires = B._claim_fires(["barter"], per_ref)
    assert len(fires) == 1 and fires[0]["kind"] == "rendering-mismatch", fires
    assert fires[0]["ref"] == "Psa 106:20"


def test_claim_fires_unmatched_ref_fires_once():
    """A ref where NO claimed gloss matches fires once, when another gloss matched elsewhere
    (the bullet claims coverage of that ref and delivers none)."""
    per_ref = {("Psa", 102, 26): (["change"], "", None),
               ("Exo", 13, 13): (["sold"], "", None)}
    fires = B._claim_fires(["change"], per_ref)
    assert len(fires) == 1 and fires[0]["ref"] == "Exo 13:13", fires


def test_claim_fires_poscap_survives():
    """The οὐρανός class survives set semantics: an exact match at a ref where the gloss sits
    sentence-initial still emits the positional-cap adjudication flag, with the ref named."""
    verse = "Heaven is high, and the earth is deep; but the heart of a king is unascertained."
    per_ref = {("Pro", 25, 3): (["Heaven"], verse, None)}
    fires = B._claim_fires(["Heaven"], per_ref)
    assert any(f["kind"] == "positional-cap" and f["ref"] == "Pro 25:3" for f in fires), fires


def test_claim_fires_case_mismatch_preferred():
    """A gloss clean nowhere reports its most informative kind: case-mismatch (matched only
    case-folded at some ref) beats a plain mismatch from another ref."""
    per_ref = {("Gen", 1, 8): (["sky"], "", None),
               ("Pro", 25, 3): (["heaven"], "", None)}
    fires = B._claim_fires(["Heaven"], per_ref)
    assert len(fires) == 1 and fires[0]["kind"] == "case-mismatch", fires


# ── contested-verse registry routing ─────────────────────────────────────────────────────────

def test_registry_hits_2co521():
    """Registry control: a card citing 2Co 5:21 must route, carrying the verbatim dossier bar;
    an unregistered verse must not."""
    hits = B.registry_verse_hits([("2Co", 5, 21), ("Gen", 1, 8)])
    assert len(hits) == 1 and hits[0]["ref"] == "2Co 5:21", hits
    assert "ABP adjudicated the fork" in hits[0]["bar"]          # verbatim dossier text present
    assert "PARKED dossier" in hits[0]["source"]


# ── leading-boilerplate detector (G162 preamble-leak ticket, reviewer-ruled BUILD 2026-07-14) ─
#
# WHAT THIS CLASS IS: the model opens the card with its own working note ("Here is the corrected
# definition ...") instead of the bare card. Both prompts forbid it (build_lexica_def.py:200 draw,
# :1896 repair). NOTHING checks it — verified against the full detector enumeration in
# offline_gate_check.py:94-156. split_definition SILENTLY DISCARDS the leak (pre-section lines go
# to a local `preamble` that reaches senses_block in no path), so a contract-breaching draw reads
# gate-clean. That silent discard is what this detector ends; it is REPORT-ONLY and no block rule
# ships with it (reviewer ruling, meta:v5 blast-radius precedent).
#
# ⚠ FIXTURE PROVENANCE — READ BEFORE TRUSTING A ZERO FROM THIS DETECTOR.
# The fixtures below are SYNTHETIC and are NOT the bytes of any real card. They test BOUNDARY
# LOGIC only (the #71 precedent: a hand-typed fixture is the right tool where it tests boundary
# logic, and CI cannot read the corpus by ruling). They are deliberately NOT rebuilt from the kill
# record's prose: the archived G162 quote there is TRUNCATED ("... integrated into Sense 1 ..."),
# and a fixture rebuilt from a doc's prose is a typed claim, which is banned.
# ⇒ THE KNOWN-POSITIVE CONTROL IS **OWED, NOT DONE**. This file's own standing rule (see the
# module docstring) is that a detector fires on a KNOWN POSITIVE from the archived defect record
# before any zero of its is trusted. The known positive is G162's archived draw
# (draws/history/G162_20260713T022852_aa064d41.json) — PA-only, `draws/` is gitignored, so CC
# cannot read it. Until that read runs, this detector's boundary logic is proven and its ZEROS
# ARE NOT. Do not report "clean" off this suite alone.

_BP_CLEAN = """**Senses:**

**1. to take captive.** The word takes people, never cities (2Ch 21:17).

**Range:** it runs from the seizing of persons to their carrying off.
"""

_BP_META = """Here is the full corrected definition with the unplaced occurrences integrated.

**Senses:**

**1. to take captive.** The word takes people, never cities (2Ch 21:17).

**Range:** it runs from the seizing of persons to their carrying off.
"""

_BP_TITLE = """**G162 αἰχμαλωτεύω (aichmalōteuō)**

---

**Senses:**

**1. to take captive.** The word takes people, never cities (2Ch 21:17).
"""

_BP_HEADERLESS_CLEAN = """**1. to take captive.** The word takes people, never cities (2Ch 21:17).

**Range:** it runs from the seizing of persons to their carrying off.
"""


def test_leading_boilerplate_fires_on_meta_note():
    """THE CLASS: a working note before the first section header. Must surface, tagged meta."""
    hits = B.leading_boilerplate(_BP_META)
    assert hits, "leading_boilerplate must fire on a model working note opening the card"
    assert hits[0]["kind"] == "meta"
    assert "Here is the full corrected definition" in hits[0]["text"]


def test_leading_boilerplate_silent_on_clean_card():
    """The other direction, alone: a card that opens on its section header fires NOTHING."""
    assert B.leading_boilerplate(_BP_CLEAN) == []


def test_leading_boilerplate_silent_on_headerless_senses():
    """The split_definition fallback shape (no 'Senses:' header, senses lead as bold-numbered
    lines). The senses are the CARD, not boilerplate — firing here would flood the signal."""
    assert B.leading_boilerplate(_BP_HEADERLESS_CLEAN) == []


def test_leading_boilerplate_tags_bare_title_apart_from_meta():
    """The KNOWN-BENIGN class (ὄρος 2026-07-07: drafts open with a title line and/or a --- rule
    the prompt asked them not to write; the splitter already handles it). It is still a contract
    breach, so it surfaces — but tagged `title`, NEVER `meta`, so the sweep can size the two
    classes apart before any block rule is written."""
    hits = B.leading_boilerplate(_BP_TITLE)
    assert hits, "a bare title line is still a contract breach and must surface"
    assert [h["kind"] for h in hits] == ["title"]


if __name__ == "__main__":     # plain-script mode for CI + the pre-commit hook
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_lexica_detectors: ok")
