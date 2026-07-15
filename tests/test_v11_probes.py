"""V11 prose-defect detectors (DESIGN_v11_acceptance.md, ruled 2026-07-12):
probe 1 = verbatim-quote GATE · probe 2 = named-subject WARN · scanner 3 =
identity-claim WARN · open-warn-blocks-apply (GATE CONDITION).

MUST-FAIL FIXTURE PROVENANCE (reviewer condition, on the record): every fixture
below embeds its own card text AND verse text — CI runs without bible.db
(test_coverage_gate.py pattern). Card snippets are the REAL BYTES of the killed
repaired draws, captured at the V11 build session's sanctioned one-time read-only
PA consult (2026-07-12): G227 sig d65ed5782628 / prose_sha 99e396f952ee,
G1390 sig bc1e2f690e17 / prose_sha e29c0a75e864 (both repaired round 1,
repair:4730e155f73d — draw-file fields `repaired`/`repair_rounds`, NOT `repair`;
an early probe read the wrong key and printed None, which means nothing).
Verse texts are verses.text bytes from the same consult. The six defects are the
V10 ACCEPTANCE TEST entry's adjudicated kills (AUDIT_lexica_rollout.md).
G2168 no-op control: shipped zero-defect card, sig b1c14fb6c2ef.

Red-first: this file was run BEFORE the detectors existed and failed
(AttributeError, raw output in the V11 build session record) — every detector
provably fires on its banked defect class before any zero is trusted.
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_lexica_def as B


# ── Embedded verse texts (verses.text bytes, PA consult 2026-07-12) ─────────────────────────
VT = {
    ("2Ch", 21, 3): "And their father gave to them many gifts — silver, and gold, and shields, with cities being walled in Judah. But the kingdom he gave to Jehoram, for he was the first-born.",
    ("Job", 5, 12): "effacing counsels of clever ones, that in no way should their hands perform true;",
    ("Job", 42, 7): "And it came to pass after the LORD speaking all these words to Job, the LORD said to Eliphaz the Temanite, You sinned and your two friends, for you spoke not anything before me true, as my attendant Job.",
    ("Job", 42, 8): "And now, take seven calves, and seven rams, and go to my attendant Job! and he shall offer a yield offering for you, for in no way shall I receive of his face, for but on account of him I would have destroyed you. For you did not speak true concerning my attendant Job.",
    ("Isa", 42, 3): "A reed being crushed he will not break, and smoking flax he will not extinguish; but to validity he will bring forth judgment.",
    ("Mat", 22, 16): "And they sent to him their disciples with the Herodians, saying, Teacher, we know that you are true, and the way of God in truth you teach, and there is no care to you concerning any one, for you see not to the person of men.",
    ("Mar", 12, 14): "And they having come, say to him, Teacher, we know that you are true, and there is no care to you concerning anyone; for you see not to the person of men, but in truth the way of God you teach. Is it allowed to give tribute to Caesar, or not?",
    ("2Sa", 19, 42): "And the men of Judah answered to the men of Israel, and said, Because the king is a near relative to us. And why is this you are enraged on account of this matter? Or in eating have we eaten any food from the king, or a gift given to us?",
    ("Psa", 68, 18): "You ascended into the height; you captured captivity; you received gifts by men; for even to encamp among the ones resisting persuasion.",
    ("Num", 3, 9): "And you shall give the Levites to Aaron your brother, and to his sons to the priests for a gift being given; these to me are from the sons of Israel.",
    ("Gen", 41, 32): "And concerning the repetition of the dream to Pharaoh twice, it is because the saying by God will be true, and God will hasten to do it.",
    # V11.1 ticket-1 verse bytes (JP live reads, 2026-07-12, this session's record):
    ("Lev", 23, 38): "besides the Sabbaths of the LORD, and besides your gifts, and besides all your vows, and besides all your voluntary offerings, which ever you shall give to the LORD.",
    ("Job", 1, 15): "And Sabeans fell upon and captured them, and the servants they killed by swords. And I alone escaped, and I came to report to you.",
    ("2Ti", 3, 6): "For from out of these are the ones entering into the houses, and capturing the vain women heaped with sins, being led by various desires,",
    ("Neh", 9, 26): "And they changed and revolted from you. And they tossed your law behind their body, and they killed your prophets, the ones testifying to them to turn them towards you. And they made great provocations to anger.",
    ("Rom", 1, 23): "and they bartered the glory of the incorruptible God for a representation of an image of corruptible man, and birds, and four-footed creatures, and reptiles.",
    ("2Ch", 31, 14): "And Kore the son of Imnah the Levite, the gatekeeper according to the east, was over the gifts, to give the first-fruits of the LORD, and the holy things of the holies,",
    ("Gen", 31, 7): "But your father cheated me, and bartered my wage for the ten lambs. And the God of my father did not give to him the power to do evil against me.",
    ("Num", 28, 2): "Give charge to the sons of Israel! And you shall say to them, saying, My gifts, my presents, my yield offerings for a scent of pleasant aroma you shall observe to bring near to me in my holidays.",
    # V11.1 ticket-2 verse bytes (JP live reads, 2026-07-12, this session's record):
    ("Pro", 18, 16): "A gift of a man widens him; and sits him by monarchs.",
    ("Mat", 7, 11): "If then, you being wicked, know to give good gifts to your children, how much rather your father, the one in the heavens shall give good things to the ones asking him?",
    ("Luk", 11, 13): "If then you, being wicked ones, know to give good gifts to your children; how much more the father from heaven shall give holy spirit to the ones asking him?",
    # V11.1 ticket-3 verse bytes (JP live read, 2026-07-12, this session's record):
    ("Gen", 35, 2): "And Jacob said to his house, and to all the ones with him, Take away the alien gods from your midst, and cleanse and change your robes!",
    # meta:v2 3c verse bytes (JP live read, 2026-07-12; also banked in test_quote_repair.py):
    ("Jer", 2, 11): "if nations changed their gods, and these are not gods! But my people changed their glory by which they do not derive benefit.",
    # meta:v2 3b verse bytes (JP live read, 2026-07-13): Isa 43:9 has "speak truth" and
    # "truth" but not "speak what is true" — so the gloss-word spans match and only the
    # rendering-contrast span needs the exemption.
    ("Isa", 43, 9): "All the nations were brought together, and rulers from them shall be brought together. Who will announce these things? Or the things from the beginning, who will announce? Let them bring forth their witnesses, and let them be justified, and let them hear, and let them speak truth!",
}


def sub(*keys):
    return {k: VT[k] for k in keys}


# ── G2168 no-op control (shipped card, sig b1c14fb6c2ef; raw + verse bytes from the same
# sanctioned PA consult). Verse set = every ref the card's quotes/named claims touch. ─────────
G2168_VT = {
    ("Rom", 1, 8): "First indeed, I give thanks to my God through Jesus Christ for all of you, that the belief of yours is announced in the entire world.",
    ("Rom", 1, 21): "Because having known God, they glorified him not as God, or gave thanks; but acted in folly in their thoughts, and their senseless heart was darkened.",
    ("Rom", 7, 25): "I give thanks to God because of Jesus Christ our Lord. It is so then, I myself indeed to the mind serve the law of God, but to the flesh the law of sin.",
    ("Rom", 14, 6): "The one regarding the day, regards it to the Lord; and the one not regarding the day, regards it not to the Lord. The one eating, eats to the Lord, for he gives thanks to God; and the one not eating, eats not to the Lord, and he gives thanks to God.",
    ("Rom", 16, 4): "(who placed their own neck for my life, to whom not I only give thanks, but also all the assemblies of the nations;)",
    ("1Co", 1, 4): "I give thanks to my God at all times for you, for the favor of God, to the one being given to you in Christ Jesus;",
    ("1Co", 1, 14): "I give thanks to God that not one of you I immersed except Crispus and Gaius,",
    ("1Co", 10, 30): "If I partake in favor, why am I blasphemed for what I give thanks?",
    ("1Co", 11, 24): "and having given thanks he broke it, and said, Take eat, this is my body being broken for you; this do in my remembrance!",
    ("1Co", 14, 17): "For you indeed well give thanks, but the other is not edified.",
    ("1Co", 14, 18): "I give thanks to my God, speaking with languages more than all of you;",
    ("Joh", 6, 11): "And Jesus took the bread loaves, and having given thanks, he distributed to the disciples, and the disciples to the ones reclining; in like manner also of the little fishes, as much as they wanted.",
    ("Joh", 6, 23): "(but other small boats came from Tiberias near the place where they ate the bread having given thanks to the Lord).",
    ("Joh", 11, 41): "Then they lifted away the stone where the one having died was situated. And Jesus lifted his eyes upward, and said, O father, I give thanks to you that you heard me.",
    ("1Th", 5, 18): "In everything give thanks! for this is the will of God in Christ Jesus for you.",
    ("Act", 27, 35): "And having said these things, and having taken bread, he gave thanks to God before all; and having broken he began to eat.",
    ("Act", 28, 15): "And from there the brethren having heard the things concerning us, came forth to meet us as far as Appii Forum and Three Taverns; whom Paul seeing, having given thanks to God, he took courage.",
    ("Rev", 11, 17): "saying, We give thanks to you, O Lord God almighty, the one being, and the one who was, and the one coming; that you have taken your great power and reigned.",
    ("Luk", 17, 16): "and he fell upon his face by his feet giving thanks to him; and he was a Samaritan.",
    ("Luk", 18, 11): "The Pharisee standing prayed these things to himself, God, I give thanks to you that I am not as the rest of the men, predacious, unjust, adulterers, or even as this tax collector.",
    ("Luk", 22, 17): "And having received the cup, having given thanks, he said, Take this, and divide it among yourselves!",
    ("Luk", 22, 19): "And having taken the bread, having given thanks he broke, and he gave it to them, saying, This is my body, the one for you being given; this do in my remembrance!",
    ("Mat", 15, 36): "And having taken the seven bread loaves, and the fishes, having given thanks he broke and gave to his disciples, and the disciples to the multitude.",
    ("Mat", 26, 27): "And having taken the cup, and giving thanks, he gave to them, saying, You drink of it all!",
    ("Mar", 8, 6): "And he exhorted the multitude to recline upon the ground. And having taken the seven bread loaves, having given thanks, he broke, and gave to his disciples, that they should place it near them; and they placed it near the multitude.",
    ("Mar", 14, 23): "And having taken the cup, having given thanks, he gave to them, and all drank of it.",
    ("Eph", 1, 16): "cease not giving thanks for you, making mention of you in my prayers,",
}

G2168_RAW = """**Expressing gratitude or acknowledgment directed toward a recipient**

The lemma appears uniformly in one job across all 39 occurrences: the speaker or actor directs gratitude toward a recipient for something received or done. The construction is consistent — a beneficiary acknowledges a benefactor — whether the expression is spoken aloud, prayed, or enacted over food. Three recurring configurations appear:

**1. Verbal address to God acknowledging what has been done or given — the dominant use**

The speaker names God as recipient and states or implies the grounds: a community's faith, personal rescue, a hearing granted, a gift of grace, or simply the state of affairs. This covers nearly all of the epistle occurrences and several narrative ones.

(Rom 1:8: "I give thanks to my God through Jesus Christ for all of you"; 1Co 1:4: "I give thanks to my God at all times for you, for the favor of God"; 1Co 1:14: "I give thanks to God that not one of you I immersed except Crispus and Gaius"; Joh 11:41: "O father, I give thanks to you that you heard me"; 1Th 1:2; 1Th 2:13; 1Th 5:18: "In everything give thanks!"; 2Th 1:3; 2Th 2:13; 2Co 1:11; Col 1:3; Col 1:12; Col 3:17; Eph 1:16; Eph 5:20; Php 1:3; Phm 1:4; Rom 1:21 — negated: "gave thanks" not rendered to God though God was known; Rom 7:25: "I give thanks to God because of Jesus Christ our Lord"; Rom 14:6 ×2: "he gives thanks to God"; Act 28:15: "having given thanks to God, he took courage"; Rev 11:17: "We give thanks to you, O Lord God almighty … that you have taken your great power and reigned"; 1Co 14:17: "you indeed well give thanks, but the other is not edified"; 1Co 14:18: "I give thanks to my God, speaking with languages more than all of you")

Sub-use: Gratitude directed to a human benefactor rather than to God — the same acknowledgment of benefit, but the recipient is a person. Rom 16:4 names Prisca and Aquila as the ones to whom thanks is owed: "to whom not I only give thanks, but also all the assemblies of the nations." Luk 17:16 shows the healed Samaritan "giving thanks to him" — falling at Jesus's feet, directed at the one who cleansed him. (Rom 16:4; Luk 17:16)

Sub-use: Gratitude expressed as self-display rather than genuine acknowledgment — the Pharisee in Luk 18:11 uses the form of the lemma in prayer ("God, I give thanks to you that I am not as the rest of the men") but the context frames it as self-congratulation performed before God; the lemma itself is not a different word here, but the narrative frames the act as hollow. (Luk 18:11)

**2. Giving thanks over food before distributing or eating it — a ritual-gestural use**

In several narratives the lemma describes an action performed over bread or a cup immediately before breaking and distributing. The gesture is embedded in a physical sequence: take → give thanks → break → distribute. The thanks is still directed toward God (Act 27:35 makes this explicit: "he gave thanks to God before all"), but the lemma's role here is specifically the spoken or enacted acknowledgment that precedes handling the food.

(Mat 15:36: "having taken the seven bread loaves, and the fishes, having given thanks he broke and gave to his disciples"; Mat 26:27: "having taken the cup, and giving thanks, he gave to them"; Mar 8:6: "having taken the seven bread loaves, having given thanks, he broke"; Mar 14:23: "having taken the cup, having given thanks, he gave to them"; Luk 22:17: "having received the cup, having given thanks, he said, Take this, and divide it among yourselves!"; Luk 22:19: "having taken the bread, having given thanks he broke"; 1Co 11:24: "having given thanks he broke it, and said, Take eat, this is my body"; Joh 6:11: "Jesus took the bread loaves, and having given thanks, he distributed"; Joh 6:23: "near the place where they ate the bread having given thanks to the Lord"; Act 27:35: "having taken bread, he gave thanks to God before all; and having broken he began to eat")

There is also one instance where the grounds for gratitude become the frame: 1Co 10:30: "If I partake in favor, why am I blasphemed for what I give thanks?" — the thanks here is performed over food received as a gift, and the lemma refers to the spoken acknowledgment accompanying that partaking.

---

**Range:** At its most concrete, the lemma names the verbal-gestural act of giving thanks over bread or a cup immediately before breaking and distributing (Mat 15:36; 1Co 11:24). At its most extended, it covers any directed acknowledgment of benefit — in prayer, in letters, in continuous disposition ("at all times," "cease not") — addressed to God or, in two cases, to a human person. What moves the word along this range is the presence or absence of a physical food-act in the immediate context; when food-taking and breaking surround the lemma, the gestural dimension is foregrounded; when the setting is prayer, correspondence, or instruction, the act is purely verbal acknowledgment.

**Gloss notes:** The sole gloss "thanks" (always inside a phrase) is a serviceable rendering throughout. No sense attested in the occurrences goes unrepresented by it. The phrase-constructions the translation uses ("I give thanks," "having given thanks," "giving thanks") accurately reflect the Greek's participial and finite forms. No freight is imported that the contexts do not support; the gloss neither narrows the word to a specifically liturgical or eucharistic sense nor forces it into one. The gloss does not distinguish the food-act use (Sense 2) from the prayer use (Sense 1), which is appropriate — the lemma itself does not divide."""


def entry_with(audit_extra=None):
    """Minimal entry passing every OTHER validate_entry check (coverage-gate test pattern)."""
    audit = {"misses": [], "real": 0, "noverse": 0, "noncanon": [], "fed_uncited": []}
    audit.update(audit_extra or {})
    return {"strongs": "G9999", "sense_headlines": ["1. x"], "fork": None,
            "senses_block": "x", "audit": audit, "raw": ""}


def main():
    # ═══ PROBE 1 — verbatim-quote gate ═══
    # 1a MUST-FAIL, defect 6 (G227 gloss-note reorder, real bytes): quoted span reordered
    # vs stored Isa 42:3; gloss notes are INSIDE the line (standing sub-rule).
    raw_d6 = ('- *validity* (Isa 42:3): The rendering is interpretive — the translation maps it '
              'onto the outcome of a process ("bring forth judgment to validity").')
    fails, notrun = B.probe1_verbatim(raw_d6, sub(("Isa", 42, 3)))
    assert fails and "bring forth judgment to validity" in fails[0], (fails, notrun)
    assert not notrun

    # 1b MUST-FAIL, defect 5 (G227 quote-anchor, real bytes): wording is Job 42:8's,
    # anchored primary on Job 42:7 — the anchoring rule fires.
    raw_d5 = ('The accusation against the friends is that they "did not speak true" before God '
              '(Job 42:7; also Job 42:8 above).')
    fails, notrun = B.probe1_verbatim(raw_d5, sub(("Job", 42, 7), ("Job", 42, 8)))
    assert fails and "anchor" in fails[0] and "42:8" in fails[0], (fails, notrun)

    # 1c PASS, marked interior ellipsis (G1390 real bytes vs Num 3:9).
    raw_ell = '"you shall give the Levites to Aaron … for a gift being given" (Num 3:9)'
    fails, notrun = B.probe1_verbatim(raw_ell, sub(("Num", 3, 9)))
    assert fails == [] and notrun == [], (fails, notrun)

    # 1d PASS, initial-letter case exemption (must NOT fire): capitalized quote start vs
    # mid-sentence lowercase in Gen 41:32.
    raw_cap = '"The saying by God will be true" (Gen 41:32)'
    fails, notrun = B.probe1_verbatim(raw_cap, sub(("Gen", 41, 32)))
    assert fails == [] and notrun == [], (fails, notrun)
    # …and interior alteration NEVER: an interior word swap must fail even with caps intact.
    raw_int = '"the saying by God shall be true" (Gen 41:32)'
    fails, _ = B.probe1_verbatim(raw_int, sub(("Gen", 41, 32)))
    assert fails, "interior alteration passed — the exemption leaked past the initial letter"

    # 1e PASS, row 7 edge punctuation (G162-card exhibit shape): trailing comma inside the
    # closing quote where the verse carries a semicolon.
    raw_edge = ('Psa 68:18 reads "You ascended into the height; you captured captivity; '
                'you received gifts by men," describing a triumphant march.')
    fails, notrun = B.probe1_verbatim(raw_edge, sub(("Psa", 68, 18)))
    assert fails == [] and notrun == [], (fails, notrun)

    # 1f NOT-RUN (loud, and it BLOCKS — amendment 1): unmatched quote while a cited text is
    # unavailable is never a pass and never a silent fail.
    vt_missing = {("Isa", 42, 3): VT[("Isa", 42, 3)], ("Psa", 68, 18): None}
    fails, notrun = B.probe1_verbatim(raw_d6, vt_missing)
    assert notrun and not fails, (fails, notrun)

    # ═══ PROBE 1 — V11.1 ticket 2: leading-attribution anchoring + paired-quote bracket
    # (ruled at session open; exhibits regenerated as real bytes from the surviving d2 raws,
    # fail lines in the session record: G1390 2Sa 19:42 + Mat 7:11, G227 Job 42:7/8).
    # The trailing-bracket branch (defect 5's teeth, fixture 1b) is UNTOUCHED and re-proven
    # every run; the swap twin below pins the paired branch's own teeth. ═══

    # 1p MUST-CLEAR — leading attribution, head-window shape (G1390 real bytes): "2Sa 19:42
    # asks whether «…»" anchors on the NEAREST ref, not the farther Pro 18:16. The first
    # quote's fire must SURVIVE — it drops Pro 18:16's interior semicolon (never-exempt
    # class), proving the anchoring fix loosens no matching.
    raw_lead = ('"a gift of a man widens him and sits him by monarchs" (Pro 18:16); '
                '2Sa 19:42 asks whether "a gift given to us" had influenced Judah.')
    fails, notrun = B.probe1_verbatim(raw_lead, sub(("Pro", 18, 16), ("2Sa", 19, 42)))
    assert len(fails) == 1 and "matches NO" in fails[0] and "widens him" in fails[0], fails
    assert not any("anchor" in f for f in fails) and notrun == [], (fails, notrun)

    # 1q MUST-CLEAR — leading attribution inside a bracket item (G1390 real bytes): within
    # "(Mat 7:11, …; note that Luk 11:13 specifies … while Mat 7:11 says «good things,»)"
    # the quote anchors on the nearest ref (Mat 7:11), not the item's first (Luk 11:13).
    raw_item = ('"you, being wicked ones, know to give good gifts to your children" '
                '(Luk 11:13); "you being wicked, know to give good gifts to your children" '
                '(Mat 7:11, the shared construction; note that Luk 11:13 specifies the '
                'father "shall give holy spirit" while Mat 7:11 says "good things," so the '
                'verses are not identically worded)')
    fails, notrun = B.probe1_verbatim(raw_item, sub(("Mat", 7, 11), ("Luk", 11, 13)))
    assert fails == [] and notrun == [], (fails, notrun)

    # 1r MUST-CLEAR — paired quotes, one ordered bracket (G227 real bytes): two correct
    # quotes joined by "and" sharing "(Job 42:7, Job 42:8)"; the bracket-adjacent quote
    # pairs with the LAST ref (42:8, its true home)…
    raw_pair = ('the LORD twice charges that Eliphaz and friends "spoke not anything before '
                'me true, as my attendant Job" and "did not speak true concerning my '
                'attendant Job" (Job 42:7, Job 42:8).')
    fails, notrun = B.probe1_verbatim(raw_pair, sub(("Job", 42, 7), ("Job", 42, 8)))
    assert fails == [] and notrun == [], (fails, notrun)
    # …and the TEETH twin: the same pair with the quotes SWAPPED (bracket order no longer
    # matches quote order) must fire — the paired branch keeps full anchoring teeth.
    raw_pair_swap = ('the LORD twice charges that Eliphaz and friends "did not speak true '
                     'concerning my attendant Job" and "spoke not anything before me true, '
                     'as my attendant Job" (Job 42:7, Job 42:8).')
    fails, _ = B.probe1_verbatim(raw_pair_swap, sub(("Job", 42, 7), ("Job", 42, 8)))
    assert len(fails) == 1 and "anchor" in fails[0], fails

    # ═══ PROBE 1 — V11.1 ticket 3: markdown-emphasis strip (norm:v2). Exhibit class =
    # G236 d1 Gen 35:2 bold-inside-quote (audit-adjudicated formatting ARTIFACT). The d1
    # raw is OVERWRITTEN — fixture is a labeled RECONSTRUCTION to the class shape (ruled-b
    # precedent); verse bytes real. verses.text carries zero asterisks (live count in the
    # session record), so stripping both sides can mask nothing. ═══

    # 1s MUST-CLEAR — RECONSTRUCTED: bold marks inside an otherwise-verbatim quote are
    # formatting, not alteration…
    raw_bold = ('Jacob\'s household is told to "cleanse and **change** your robes" (Gen 35:2).')
    fails, notrun = B.probe1_verbatim(raw_bold, sub(("Gen", 35, 2)))
    assert fails == [] and notrun == [], (fails, notrun)
    # …TEETH twin: the strip exempts MARKS only — a real word swap under bold still fires.
    raw_bold_alt = ('Jacob\'s household is told to "cleanse and **exchange** your robes" '
                    '(Gen 35:2).')
    fails, _ = B.probe1_verbatim(raw_bold_alt, sub(("Gen", 35, 2)))
    assert len(fails) == 1 and "matches NO" in fails[0], fails
    # …and single-asterisk italics, same class.
    raw_ital = ('Jacob\'s household is told to "cleanse and *change* your robes" (Gen 35:2).')
    fails, notrun = B.probe1_verbatim(raw_ital, sub(("Gen", 35, 2)))
    assert fails == [] and notrun == [], (fails, notrun)

    # ═══ PROBE 1 — metalinguistic-mention exemption. meta:v2 (F3, 2026-07-13,
    # ENGINE_LESSONS #56/#57): the ≤2-word cap is RETIRED and replaced by the ANCHOR
    # WALL. Exemption now holds when all three of: (a) span matches no cited verse,
    # (b) NO local ref anchor (_local_refs returns []), (c) a metalinguistic cue sits in
    # the context window. The no-anchor test is the non-word-count discriminator that
    # blocks laundering — a smuggled misquote always attaches a ref, so an unanchored
    # span makes no scripture claim to be unfaithful to. Exemptions stay LOUD — a note in
    # the notes list, never a silent skip (lesson #47). Real bytes: reliable (G227 d2),
    # captivating (G162 d2), other item (G236 d2), all from the banked/live consults;
    # the meta:v2 3a–3c fixtures below add the real PRE bytes that parked G227/G236. ═══

    # 1t MUST-CLEAR with note — "reliable" (real bytes; "rendering" context pattern).
    raw_rel = ('The gloss set does not include a distinct "reliable" or "trustworthy" '
               'rendering for the person-characterization uses.')
    notes = []
    fails, notrun = B.probe1_verbatim(raw_rel, {}, notes=notes)
    assert fails == [] and notrun == [], (fails, notrun)
    assert any('reliable' in n and 'EXEMPTED' in n for n in notes), notes

    # 1u MUST-CLEAR with note — "captivating" (real bytes; "sense of" pattern; 2Ti 3:6's
    # stored text has "capturing", correctly no match).
    raw_cap = ('- None of the supplied occurrences attests any sense of purely intellectual '
               'or spiritual "captivating" independent of the control-and-removal image; '
               '2Ti 3:6 is the closest case.')
    notes, warns = [], []
    fails, notrun = B.probe1_verbatim(raw_cap, sub(("2Ti", 3, 6)), notes=notes, warns=warns)
    assert fails == [] and notrun == [], (fails, notrun)
    # meta:v6 (scope-b (b) ruling, 2026-07-14): "captivating" is char-0.700 to "capturing" in the
    # cited 2Ti 3:6 (IN band), but it is a SINGLE content token (run 1) -- a lemma-gloss inflection,
    # NOT a verse-word run -- so the discriminator keeps it a NOTE. (v5 briefly warned this whole
    # class; v6's run check clears it -- the 12-live-card blast radius.)
    assert warns == [], warns
    assert len(notes) == 1 and 'captivating' in notes[0], notes

    # 1v MUST-STILL-REFUSE — "other item" (real bytes) is unanchored, matches nothing, and no cue
    # reaches scare-quotes-around-a-concept. With the EMPTY cited set here, meta:v4's empty-set
    # rule (2026-07-14) blocks any own-paraphrase exemption — nothing to be a paraphrase OF — so it
    # FAILS (kind unsourced). In its real card (non-empty cited set) it is fed->cap->park instead;
    # either way it never exempts (ruled must-refuse). Still one fail, no exemption note.
    raw_oth = ('the two are distinguished by whether an "other item" is explicitly placed '
               'in the position vacated.')
    notes = []
    fails, _ = B.probe1_verbatim(raw_oth, {}, notes=notes)
    assert len(fails) == 1 and 'other item' in fails[0] and notes == [], (fails, notes)

    # 1w MUST-STILL-REFUSE — a long span carrying a REF still fires. WALL RELOCATION
    # (meta:v2, reviewer-noted): pre-F3 this was blocked by the ≤2-word cap; now it is
    # blocked by the ANCHOR WALL (the trailing "(Gen 35:2)" makes it anchored, so the
    # exemption is skipped regardless of length or cue). Same verdict, different wall —
    # not a behavior change. This is the misquote-riding-"sense of" laundering channel,
    # kept structurally closed by the ref, not by the word count.
    raw_long = ('the sense of "cleanse and exchange your robes entirely" (Gen 35:2).')
    notes = []
    fails, _ = B.probe1_verbatim(raw_long, sub(("Gen", 35, 2)), notes=notes)
    assert len(fails) == 1 and notes == [], (fails, notes)

    # 1x — condition (a) alone: a short span with a pattern that MATCHES its verse is a
    # normal pass — no fail, no note (exemption never touches real matches).
    notes = []
    fails, notrun = B.probe1_verbatim('the word "change" (Gen 35:2).', sub(("Gen", 35, 2)),
                                      notes=notes)
    assert fails == [] and notrun == [] and notes == [], (fails, notrun, notes)

    # 1y MUST-STILL-REFUSE — Levites class, RECONSTRUCTED (ruled: d1 overwritten; the
    # self-label class the exemption must never reach). Under meta:v2 the ANCHOR WALL
    # blocks it: the trailing "(Num 3:9)" makes the span anchored, so the exemption is
    # skipped (the pattern-hit/word-count reasoning is moot once a ref is present).
    raw_lev = ('the Levites are given as "sacred allocation for the sanctuary" (Num 3:9).')
    notes = []
    fails, _ = B.probe1_verbatim(raw_lev, sub(("Num", 3, 9)), notes=notes)
    assert len(fails) == 1 and notes == [], (fails, notes)

    # ── meta:v2 3a–3c: the REAL PRE bytes that parked the words on the live gate (F3
    # charter — the exemption is proven on the actual bytes, not a paraphrase). ──

    # 3a MUST-CLEAR (G227 d3 real bytes, key d65ed578, verbatim window) — two multi-word
    # metalinguistic labels the card quotes from ITSELF ("the lemma shifts from X to Y"):
    # no verse match, no ref anchor, "the lemma" cue. The ≤2-word cap could never reach
    # these (4 and 6 words) — meta:v2's whole reason to exist.
    raw_g227 = ('In juridical-flavored contexts about witness and judgment, the lemma '
                'shifts from "matches the facts" to "counts as adequate under the '
                'applicable rule." The question is not primarily whether the content is '
                'accurate but whether the testimony is receivable or the judgment stands.')
    notes = []
    fails, notrun = B.probe1_verbatim(raw_g227, {}, notes=notes)
    assert fails == [] and notrun == [], (fails, notrun)
    assert any('matches the facts' in n and 'EXEMPTED' in n for n in notes), notes
    assert any('counts as adequate' in n and 'EXEMPTED' in n for n in notes), notes

    # 3b MUST-CLEAR (G227 d3 real bytes, FULL bullet from the header) — the reviewer-ruled
    # extension: the fixture now INCLUDES the "(Isa 43:9)" ref in the bullet header, so the
    # "out of _local_refs' window" claim is PROVEN, not asserted. The rendering-contrast
    # span "speak what is true" still has no local anchor (the header ref is >48 chars back,
    # not in its enclosing paren) and carries a "rendering"/"the lemma" cue → exempt. The
    # other spans ("truth", "speak", "speak truth") DO occur in Isa 43:9 → they match and
    # pass, never touching the exemption. Proves the exemption covers the gloss_notes field
    # (both G227 unanchored spans came from here) on the true card shape.
    raw_g227b = ('**"truth" (Isa 43:9):** The lemma here is an accusative object of "speak"; '
                 'rendering it as a noun ("speak truth") rather than an adjective phrase '
                 '("speak what is true") is within the range of sense 1 but slightly '
                 'abstracts toward a nominalized concept the Greek adjective does not require.')
    notes = []
    fails, notrun = B.probe1_verbatim(raw_g227b, sub(("Isa", 43, 9)), notes=notes)
    assert fails == [] and notrun == [], (fails, notrun)
    assert any('speak what is true' in n and 'EXEMPTED' in n for n in notes), notes

    # 3c MUST-STILL-REFUSE (G236 d3 real bytes, key 9bf3f7ef, verbatim window) — "they
    # changed their gods" is a GENUINE misquote (Jer 2:11 reads "if nations changed their
    # gods") sitting unanchored in a paired-quote list (the shared "(Jer 2:11)" is too
    # far off for the anchor rule to reach the first quote). NO cue in its window, so the
    # cue requirement keeps it FAILING. THIS is the case that killed "unanchored alone =
    # exempt": without the cue wall a real misquote would launder straight through.
    raw_g236 = ('replacing one thing with another in a transfer that the context marks '
                'as illegitimate or as a violation: "they changed their gods" and "my '
                'people changed their glory" (Jer 2:11, two occurrences);')
    notes = []
    fails, _ = B.probe1_verbatim(raw_g236, sub(("Jer", 2, 11)), notes=notes)
    assert len(fails) == 1 and 'they changed their gods' in fails[0], (fails, notes)
    assert not any('EXEMPTED' in n for n in notes), notes

    # ═══ PROBE 1 — meta:v3 OWN-WORD exemption (Ruling 2, 2026-07-13, ENGINE_LESSONS
    # #59). ADDITIVE to the cue path (untouched): a SINGLE word that is the card's own
    # vocabulary (appears UNQUOTED elsewhere) and is NOT attribution-anchored is an
    # emphasis mention, not a scripture claim. Real G1390 bytes (bank bda7de94): the
    # Range sentence's scare-quoted "giving" + the card's own unquoted "giving".
    # #59 CORRECTION (verified 2026-07-13, this session): the real span's clause refs sit
    # past _local_refs' 12-char window (_local_refs returns []), so the pre-v3 wall failed
    # it on MISSING CUE, not on the refs; meta:v3 exempts it regardless. Verse bytes
    # already in VT (Num 3:9, Lev 23:38). Red-first: before meta:v3 this span FAILED
    # (session record: FAILS=['quote "giving" matches NO cited verse...']). ═══
    raw_giving = ('one party grants another something of material value; the giving may be '
                  'freely offered, solicited, or withheld. At its most institutionalized it '
                  'names portions assigned within the priestly-cultic order, where the '
                  '"giving" is regulated by divine command rather than personal generosity '
                  '(Num 3:9; Lev 23:38).')
    notes = []
    fails, notrun = B.probe1_verbatim(raw_giving, sub(("Num", 3, 9), ("Lev", 23, 38)), notes=notes)
    assert fails == [] and notrun == [], (fails, notrun)
    # the LOUD note is PRESENT (Ruling 2 visibility; reviewer tightening 2026-07-13)
    assert any('giving' in n and 'EXEMPTED' in n and 'own-word' in n for n in notes), notes

    # attribution TEETH (the load-bearing case): the SAME single own-word WITH a
    # trailing-bracket ref is attribution-anchored -> the exemption must NOT touch it,
    # and NO exemption note is emitted. Proves meta:v3 can't launder an attributed
    # single-word misquote. "giving" is not in Num 3:9's stored text.
    raw_giving_attr = ('the giving may be freely offered; the priestly "giving" (Num 3:9) is '
                       'regulated by divine command.')
    notes = []
    fails, _ = B.probe1_verbatim(raw_giving_attr, sub(("Num", 3, 9)), notes=notes)
    assert len(fails) == 1 and 'giving' in fails[0], (fails, notes)
    assert not any('EXEMPTED' in n for n in notes), notes

    # ═══ PROBE 1 — FAIL-KIND TAGGING (Ruling 1 / ENGINE_LESSONS #61, 2026-07-13):
    # probe1_verbatim tags each fail AT SOURCE as "wording" (matches no verse —
    # fixable in-quote) or "anchoring" (right words, wrong ref — unfixable in-quote)
    # via an optional parallel fail_kinds list, index-aligned to fails. The tag is
    # written by the SAME branch that emits the fail (not a re-derived copy), so the
    # classifier and the fail can never drift. Card = the REAL G236 mixed card's two
    # spans (banked key 59667b81, F1-F3 RE-RUN): "changes this word" (Ezr 6:11-on-6:12,
    # anchoring) + "changing over" (matches no verse, wording). Verse bytes = JP live
    # reads 2026-07-13. Red-first: before fail_kinds existed this raised TypeError. ═══
    G236MIX_VT = {
        ("Ezr", 6, 11): "And from me was rendered a decree, that every man who ever changes this word the timber of his house shall be demolished, and a stake being straight up he shall be pitched upon it, and his house will be for ravaging.",
        ("Ezr", 6, 12): "And the God of whom encamps with his name there, he shall eradicate every king and people who should stretch out his hand to change and remove from view the house of God, that one in Jerusalem. I Darius rendered the decree. Carefully let it become!",
        ("Dan", 4, 32): "And from men they shall banish you, and with wild beasts your dwelling shall be, and grass as an ox they shall feed you, and seven seasons shall change over you, until of which time you shall know that the highest dominates the kingdom of men, and to whom ever it seems good to give it.",
    }
    raw_g236mix = ('Ezra threatens anyone who "changes this word" (Ezr 6:12; Ezr 6:11). '
                   'The repeated seasons "changing over" the king mark successive intervals '
                   '(Dan 4:32).')
    kinds = []
    fails, notrun = B.probe1_verbatim(raw_g236mix, G236MIX_VT, fail_kinds=kinds)
    assert len(fails) == 2 and notrun == [], (fails, notrun)
    assert len(kinds) == len(fails), (kinds, fails)         # index-parallel
    ai = next(i for i, f in enumerate(fails) if "anchored primary" in f)
    wi = next(i for i, f in enumerate(fails) if "matches NO" in f)
    assert kinds[ai] == "anchoring", (kinds, fails)
    assert kinds[wi] == "wording", (kinds, fails)
    # the exact banked fail lines are reproduced (real bytes, not a paraphrase)
    assert ('quote "changes this word" carries the wording of Ezr 6:11 but is anchored '
            'primary on Ezr 6:12 (anchoring rule)') == fails[ai], fails[ai]
    assert ('quote "changing over" matches NO cited verse under the ruled allowances '
            '(verbatim-quote gate)') == fails[wi], fails[wi]
    # the list stays OPTIONAL — every existing caller that omits it is unaffected.
    f2, n2 = B.probe1_verbatim(raw_g236mix, G236MIX_VT)
    assert f2 == fails and n2 == [], (f2, n2)

    # ═══ PROBE 2 — named-subject warn ═══
    # 2a MUST-FAIL, defect 1 (G1390 real bytes): Jehoiada absent from 2Ch 21:3.
    raw_d1 = ("Jehoiada's father distributing silver, gold, and shields to his sons (2Ch 21:3);")
    warns, notrun = B.probe2_names(raw_d1, sub(("2Ch", 21, 3)))
    # EXACT set — a book-code or furniture token warning here is extraction junk (the "Isa"
    # false-warn class caught at the first green run; refs are stripped, book codes whitelisted).
    assert len(warns) == 1 and "Jehoiada" in warns[0] and notrun == [], (warns, notrun)

    # 2b MUST-FAIL, defect 2 (G227 real bytes): Eliphaz absent from Job 5:12; the quoted span
    # is probe-1 territory and must not mask the name.
    raw_d2 = ('Eliphaz’s schemes are frustrated so that "their hands perform true" comes to '
              'nothing (Job 5:12 — the clause attributes the quality of truthfulness to an '
              'action that the clever men wished to accomplish).')
    warns, notrun = B.probe2_names(raw_d2, sub(("Job", 5, 12)))
    assert len(warns) == 1 and "Eliphaz" in warns[0] and notrun == [], (warns, notrun)

    # 2c BONUS CASE — documented, NOT a spec obligation (design footnote: never relied on):
    # defect 3's sentence names David; 2Sa 19:42 says only "the king".
    raw_d3 = ('David receiving provisions from his kin with no royal gift involved '
              '(2Sa 19:42: "a gift given to us");')
    warns, notrun = B.probe2_names(raw_d3, sub(("2Sa", 19, 42)))
    assert len(warns) == 1 and "David" in warns[0] and notrun == [], (warns, notrun)

    # 2d PASS, whitelist: God/LORD + the headword's own lemma/translit never warn.
    raw_wl = "God gives every good gift, as doma marks the thing given (2Ch 21:3)."
    warns, notrun = B.probe2_names(raw_wl, sub(("2Ch", 21, 3)),
                                   extra_whitelist=("δόμα", "doma"))
    assert warns == [] and notrun == [], (warns, notrun)

    # 2e PASS, subject present: Jehoram IS in 2Ch 21:3.
    raw_ok = "the kingdom went to Jehoram as the first-born (2Ch 21:3)."
    warns, notrun = B.probe2_names(raw_ok, sub(("2Ch", 21, 3)))
    assert warns == [] and notrun == [], (warns, notrun)

    # ═══ PROBE 2 — p2wl:v2 sentence-starter/label demotion (V11.1 ticket 1, MUST-FIX;
    # rulings 2026-07-12, reviewer-adjudicated under standing delegation). Boundary set =
    # paragraph/chunk start · ". " "! " "? " · "Sub-use:" label · "- " list start · "**"
    # label — semicolon and bare colon EXCLUDED (byte-forced: Korah + Sabean classes).
    # Demotion only when a corpus-name guard set is supplied AND the token is not in it;
    # known_names=None = no demotion (fail toward the human). Card bytes = REAL surviving
    # d2 raws (V111_CONSULT.md one-time consult); [completion] marks where the banked
    # excerpt's 120-char window cut a word and the obvious tail was restored. Verse bytes
    # = live reads, same session. Guard fixture set mirrors the live control run on PA:
    # korah/solomon/laban/jesus/peter ARE words-table name-marked heads; votive/active/
    # applying are NOT (raw output in the session record). ═══
    KNOWN = frozenset({"korah", "solomon", "laban", "jesus", "peter"})

    # 2f MUST-CLEAR — "Sub-use:" label class (G1390 real bytes, Votive; [offerings" (Lev
    # 23:38).] completes the window cut; the quote is Lev 23:38's own wording).
    raw_votive = ('Sub-use: Votive and voluntary sanctuary offerings — "besides the Sabbaths of '
                  'the LORD, and besides your gifts, and besides all your vows, and besides all '
                  'your voluntary offerings" (Lev 23:38).')
    warns, notrun = B.probe2_names(raw_votive, sub(("Lev", 23, 38)), known_names=KNOWN)
    assert warns == [] and notrun == [], (warns, notrun)

    # 2g MUST-CLEAR — "- " list-start class (G162 real bytes, None; [closest case.]
    # completes the window cut).
    raw_none = ('- None of the supplied occurrences attests any sense of purely intellectual or '
                'spiritual "captivating" independent of the control-and-removal image; 2Ti 3:6 '
                'is the closest case.')
    warns, notrun = B.probe2_names(raw_none, sub(("2Ti", 3, 6)), known_names=KNOWN)
    assert warns == [] and notrun == [], (warns, notrun)

    # 2h MUST-CLEAR — sentence-start-after-period class (G236 real bytes, Applying).
    raw_apply = ('the Lev 27 verses are regulatory substitutions, not market transactions. '
                 'Applying "barter" to Neh 9:26 and Rom 1:23 (which this translation also does) '
                 'is defensible.')
    warns, notrun = B.probe2_names(raw_apply, sub(("Neh", 9, 26), ("Rom", 1, 23)),
                                   known_names=KNOWN)
    assert warns == [] and notrun == [], (warns, notrun)

    # 2i MUST-KEEP — semicolon is NOT a boundary (ruled condition, own test): Korah after
    # "); " keeps its warn on boundary logic ALONE — the guard set here deliberately lacks
    # korah, so a wrongly-widened boundary set is the only thing that could eat this warn.
    # (G1390 real bytes; 2Ch 31:14's stored text names KORE — the run's first true positive.)
    raw_korah = ('(1Ki 13:7); Korah oversees the distribution of "gifts" (2Ch 31:14).')
    warns, notrun = B.probe2_names(raw_korah, {("2Ch", 31, 14): VT[("2Ch", 31, 14)],
                                               ("1Ki", 13, 7): None},
                                   known_names=KNOWN - {"korah"})
    assert len(warns) == 1 and "Korah" in warns[0] and notrun == [], (warns, notrun)

    # 2j MUST-KEEP — bare colon is NOT a boundary (ruled condition, own test): Sabean after
    # "): " keeps its warn (exonym-variant class, warn by design — stored text has plural
    # "Sabeans", the \b whole-word check correctly misses it); Active at the "- " list start
    # demotes in the same chunk. (G162 real bytes.)
    raw_sabean = ('- Active (the agent captures): Sabean raiders "fell upon and captured" '
                  "Job's livestock servants (Job 1:15).")
    warns, notrun = B.probe2_names(raw_sabean, sub(("Job", 1, 15)), known_names=KNOWN)
    assert len(warns) == 1 and "Sabean" in warns[0] and notrun == [], (warns, notrun)

    # 2k MUST-KEEP — corpus-guard save (ruled condition, own test): Laban at a real
    # sentence start survives ONLY because the guard knows it (G236 real bytes)…
    raw_laban = ('a transaction framed as substitution rather than purchase. Laban "bartered '
                 'my wage for the ten lambs" (Gen 31:7).')
    warns, notrun = B.probe2_names(raw_laban, sub(("Gen", 31, 7)), known_names=KNOWN)
    assert len(warns) == 1 and "Laban" in warns[0] and notrun == [], (warns, notrun)
    # …and the demotion twin: an empty guard set demotes it (the designed trade, pinned).
    warns, _ = B.probe2_names(raw_laban, sub(("Gen", 31, 7)), known_names=frozenset())
    assert warns == [], warns

    # 2l MUST-CLEAR — word-list class, real-byte anchor (G1390, English mid-sentence;
    # p2wl:v2 list addition, position rule can't reach it).
    raw_eng = ('in Num 28:2 the word governs ritual offerings brought to God on feast days, '
               'a setting the English "presents" does not capture.')
    warns, notrun = B.probe2_names(raw_eng, sub(("Num", 28, 2)))
    assert warns == [] and notrun == [], (warns, notrun)

    # 2m MUST-CLEAR — word-list additions Greek + Peoples. RECONSTRUCTED (ruled 2026-07-12:
    # d1 raws overwritten, no surviving bytes for these classes; sentence authored to the
    # class shape so each list entry is test-pinned).
    raw_recon = ('the Greek term is rendered narrowly here, and the Peoples addressed are '
                 'the same group (Num 28:2).')
    warns, notrun = B.probe2_names(raw_recon, sub(("Num", 28, 2)))
    assert warns == [] and notrun == [], (warns, notrun)

    # 2n DEFAULT — known_names=None means NO demotion (fail toward the human): the Votive
    # noise line warns again when the guard is absent.
    warns, _ = B.probe2_names(raw_votive, sub(("Lev", 23, 38)))
    assert len(warns) == 1 and "Votive" in warns[0], warns

    # ═══ SCANNER 3 — identity claim ═══
    # 3a MUST-FAIL, defect 4 (G227 real bytes): "worded identically" is FALSE for
    # Mat 22:16 vs Mar 12:14.
    raw_d4 = ('Teachers acknowledge Jesus: "you are true, and the way of God in truth you teach" '
              '(Mat 22:16; the parallel affirmation at Mar 12:14 is worded identically).')
    warns = B.scan3_identity(raw_d4, sub(("Mat", 22, 16), ("Mar", 12, 14)))
    assert any("DIFFER" in w for w in warns), warns

    # 3b PASS, actually-identical pair (synthetic texts, fixture-owned dict — the scanner
    # compares whatever texts it is handed).
    vt_same = {("Mat", 22, 16): "identical stored wording.", ("Mar", 12, 14): "identical stored wording."}
    assert B.scan3_identity("(Mat 22:16; Mar 12:14 is worded identically)", vt_same) == []

    # 3d MUST-FAIL, scan3:v2 exhibit (G227 V11-run draw-1 real bytes, reviewer-accepted
    # 2026-07-12): "the phrasing is identical in sense" asserts identity without the v1
    # wordings; the pattern list grows by exhibit.
    raw_v2 = ('The questioners address Jesus, "we know that you are true" '
              '(Mat 22:16; Mar 12:14, where the phrasing is identical in sense).')
    warns = B.scan3_identity(raw_v2, sub(("Mat", 22, 16), ("Mar", 12, 14)))
    assert any("DIFFER" in w for w in warns), warns

    # 3c WARN when the pair can't be resolved (fail toward the human).
    warns = B.scan3_identity("this phrase is worded identically in the tradition.", {})
    assert warns, "unresolvable identity claim passed silently"

    # ═══ OPEN-WARN-BLOCKS-APPLY (GATE CONDITION, own red-first) ═══
    # 4a one OPEN probe-2 warn refuses apply…
    e = entry_with({"probe2_warns": ["named subject \"Jehoiada\" absent — adjudicate"]})
    assert B.open_probe_warns(e), "open probe-2 warn did NOT block"
    # 4b …separately, one OPEN scanner-3 warn refuses apply…
    e = entry_with({"scan3_warns": ["claims identical but texts DIFFER — adjudicate"]})
    assert B.open_probe_warns(e), "open scanner-3 warn did NOT block"
    # 4c …and probe-1/probe-2 NOT-RUN items block too (amendment 1: a missing verse text
    # must never become a ship path)…
    e = entry_with({"probe1_notrun": ["quote x — NOT RUN"]})
    assert B.open_probe_warns(e), "probe-1 NOT-RUN did NOT block"
    e = entry_with({"probe2_notrun": ["name x — NOT RUN"]})
    assert B.open_probe_warns(e), "probe-2 NOT-RUN did NOT block"
    # 4d …an adjudication stamp clears exactly that set; a clean record was never blocked.
    e = entry_with({"probe2_warns": ["w"], "warns_adjudicated": "ruled: reviewer note"})
    assert B.open_probe_warns(e) == []
    assert B.open_probe_warns(entry_with()) == []

    # ═══ validate_entry WIRING (own-lookups, conn passed; in-memory DB, no bible.db) ═══
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE verses (book TEXT, chapter INT, verse INT, text TEXT)")
    conn.execute("INSERT INTO verses VALUES ('Isa', 42, 3, ?)", (VT[("Isa", 42, 3)],))
    e = entry_with()
    e["raw"] = raw_d6
    problems = B.validate_entry(e, conn)
    assert any("verbatim-quote gate FAILED" in p for p in problems), problems
    # …and no junk probe-2 warns from citation text (the "Isa" class).
    assert e["audit"]["probe2_warns"] == [], e["audit"]["probe2_warns"]
    assert e["audit"]["probe_vers"]["norm"] == B.NORM_VER
    # bypass rides the same adjudicated path as the citation gate.
    e = entry_with({"bypass_reason": "adjudicated: artifact edge case"})
    e["raw"] = raw_d6
    assert not any("verbatim-quote" in p for p in B.validate_entry(e, conn)), "bypass ignored"
    # no connection = loud NOT RUN, never a crash and never a block-by-accident.
    e = entry_with()
    e["raw"] = raw_d6
    assert not any("verbatim-quote" in p for p in B.validate_entry(e)), "conn=None must not gate"
    conn.close()

    # ═══ NO-OP CONTROL — G2168 (shipped, zero-defect on record; sig b1c14fb6c2ef) ═══
    # Ruled expectation (reviewer, 2026-07-12): probe 1 clean + scanner 3 clean + probe 2
    # exactly the documented true-statement warns — Prisca/Aquila vs Rom 16:4 (the names
    # live in 16:3) and Jesus vs Luk 17:16 ("his feet") — proving the warn path fires on
    # real candidates a block would have eaten. Token-level that is THREE warn lines
    # covering the two documented claims. Verse texts limited to the refs the card's
    # QUOTES and NAMED CLAIMS touch; other cited refs resolve None, which must produce
    # zero NOT-RUNs here (every quote matches an available text; no name rides a
    # None-text chunk).
    vt_full = {k: G2168_VT.get(k) for k in B.cited_refs(G2168_RAW)}
    notes = []
    fails, notrun = B.probe1_verbatim(G2168_RAW, vt_full, notes=notes)
    assert fails == [] and notrun == [], (fails, notrun)
    # meta:v1 control: the shipped card earns ZERO exemptions — its quoted glosses all
    # match cited verses, so the exemption path never engages on a clean card.
    assert notes == [], notes
    assert B.scan3_identity(G2168_RAW, vt_full) == []
    warns, notrun = B.probe2_names(G2168_RAW, vt_full,
                                   extra_whitelist=("εὐχαριστέω", "eucharisteō"))
    named = sorted({w.split('"')[1] for w in warns})
    assert named == ["Aquila", "Jesus", "Prisca"] and notrun == [], (warns, notrun)

    # …and re-run WITH the p2wl:v2 guard active (V11.1 ticket-1 ruled control): all three
    # documented warns sit mid-sentence or possessive, so demotion must not eat any of them.
    warns, notrun = B.probe2_names(G2168_RAW, vt_full,
                                   extra_whitelist=("εὐχαριστέω", "eucharisteō"),
                                   known_names=frozenset({"jesus", "prisca", "aquila"}))
    named = sorted({w.split('"')[1] for w in warns})
    assert named == ["Aquila", "Jesus", "Prisca"] and notrun == [], (warns, notrun)

    # ═══ p2wl:v2 GUARD SOURCE — _p2_corpus_names (#71 ticket, 2026-07-14) ═══════════════════
    # WHY THIS EXISTS: the KNOWN fixture above is a synthetic set, and that is CORRECT where it
    # sits — 2f-2i test the DEMOTION BOUNDARY LOGIC and want controlled input, and CI runs
    # without bible.db (header condition) so the real corpus is unreachable here by ruling.
    # But that left the BRIDGE untested: _p2_corpus_names is the production function that
    # actually loads the guard, and NOTHING exercised its success path — its only prior
    # exercise was the validate_entry wiring block above, whose in-memory db has no `words`
    # table, so the guard threw, degraded to None, demotion switched OFF, and the test passed
    # GREEN on a blown-up guard. A guard whose zero has never been proven against a known
    # positive is the certification rule's own failure case. Production callers:
    # build_lexica_def.py:2892 (validate_entry) + offline_gate_check.py:134.
    # Uses the PRODUCTION function, never a copy. Rows mirror the words-table shape the real
    # read depends on (is_pn + english_head); the guard is lowercased + DISTINCT by contract.
    pn = sqlite3.connect(":memory:")
    pn.execute("CREATE TABLE words (english_head TEXT, is_pn INT)")
    pn.executemany("INSERT INTO words VALUES (?, ?)",
                   [("Korah", 1), ("korah", 1),      # DISTINCT + lower() must fold these to one
                    ("Solomon", 1), ("Laban", 1),
                    ("gifts", 0),                    # is_pn=0 must NOT reach the guard
                    ("", 1)])                        # empty head must NOT reach the guard
    got = B._p2_corpus_names(pn)
    assert got == {"korah", "solomon", "laban"}, got          # FIRES on a known positive
    assert "gifts" not in got and "" not in got, got          # is_pn=0 / empty excluded

    # …and the loaded guard must actually DRIVE demotion through the production path: "Solomon"
    # at a sentence start is a real name and KEEPS its warn; "Applying" at a sentence start is
    # card furniture and is demoted. Same raw, same boundary — only guard membership differs.
    raw_guard = ('the gifts are regulatory. Solomon received nothing here (2Ch 21:3). '
                 'Applying "barter" to 2Ch 21:3 is defensible.')
    warns, notrun = B.probe2_names(raw_guard, sub(("2Ch", 21, 3)), known_names=got)
    named = sorted({w.split('"')[1] for w in warns})
    assert named == ["Solomon"] and notrun == [], (warns, notrun)

    # DEGRADE PATH — PROVEN, not assumed. No `words` table => guard unavailable => None =>
    # NO demotion (fail toward the human, never a silent widening). This is the state the
    # wiring block above was silently running in.
    nodb = sqlite3.connect(":memory:")
    assert B._p2_corpus_names(nodb) is None, "missing words table must degrade to None"
    warns, notrun = B.probe2_names(raw_guard, sub(("2Ch", 21, 3)), known_names=None)
    named = sorted({w.split('"')[1] for w in warns})
    assert named == ["Applying", "Solomon"], (warns, notrun)   # degrade ADDS, never removes
    pn.close()
    nodb.close()

    print("test_v11_probes: all assertions passed")


if __name__ == "__main__":
    main()
