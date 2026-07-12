"""draw_hints.py — the pre-registered CONSTRAINT-hint register for parked-word re-entry.

Design + all five rulings: DESIGN_hint_tooling.md (JP, 2026-07-12, "go with all recs").
Hand-curated, same pattern as the CONTESTED register. Each entry:

  hints:      one-line pre-registered constraints, three legal classes ONLY —
              corpus-fact pins (what a verse says, checkable against verses.text),
              discipline rules (citation/wording rules), reach ceilings (attribute-only
              lines). NEVER a preferred sense wording, sense count, carve, or any
              sentence of a prior draft (the incumbent-comparison line, drawn in the
              design doc and ruled).
  jobs:       optional stable-jobs lines (the existing --structure-hint mechanism's
              content, if a certified stable-jobs list was banked for the word).
  provenance: which park entry / ruling each entry encodes. The audit entry is the
              source of truth; this file is the machine-readable copy. A CI test
              (tests/test_draw_hints.py) asserts every entry names one.

EDITING THIS FILE = A JP CHECKPOINT (ruling 3 — same authority as the rulings it
encodes; same class as a correction-table write). At each hinted word's re-entry
pre-registration the reviewer verifies every line here against the ruling its
provenance cites (ruling 5b) — drift blocks the run until reconciled.

Injection: build_lexica_def.py --hints (see there). Running a word that has an entry
here WITHOUT --hints refuses (ruling 1; override --no-hints REASON, logged on the draw).
"""

DRAW_HINTS = {
    "G1244": {   # διαιρέω — divide/distribute
        "hints": [
            "Cite every reference under exactly ONE sense; a verse genuinely carrying two senses "
            "is stated as a named dual, never silently listed twice.",
            "Every sense must be attested by its own cited verses — never invent a carve whose "
            "members the texts do not show.",
            "Describe each cited verse's own text; never add a narrative frame the verse does not "
            "state (events from surrounding chapters stay out of a verse's description).",
        ],
        "jobs": [],
        "provenance": "AUDIT_lexica_rollout.md G1244 PARKED entry (batch-4 word 1, 2026-07-09/10) "
                      "+ BATCH 4 CLOSED banked hints; JP batch-close ruling 2026-07-12",
    },
    "G1390": {   # δόμα — gift
        "hints": [
            "Psa 68:18 reads 'you received gifts by men'; Eph 4:8 (quoting it) reads 'he gave "
            "gifts to men' — describe each text's own wording, never summarize the pair jointly.",
            "Ecc 5:1's δόμα is a human-to-God cultic gift, not divine bestowal.",
            "Eph 4:9, 4:10, and 4:11 do not carry this word — in Ephesians only 4:8 does; "
            "never cite 4:9-11, and never write the passage as a range ('Eph 4:8-11') — cite "
            "4:8 alone.",
        ],
        "jobs": [],
        "provenance": "AUDIT_lexica_rollout.md G1390 PARKED entry (batch-4 word 2, 2026-07-10/11) "
                      "+ BATCH 4 CLOSED banked hints; JP batch-close ruling 2026-07-12. "
                      "Eph 4:9-11 pin: V9 floor agreement_G1390_v9_20260712-181939 (real-miss "
                      "Eph 4:9/4:10/4:11 in draw 8, passage-tail neighbor-slip) + the ruled "
                      "pre-emptive-pin default for neighbor-slip floors (G2168 validation, "
                      "fe9d757); applied under JP's standing delegation 2026-07-12.",
    },
    "G2168": {   # εὐχαριστέω — give thanks
        "hints": [
            "Rom 16:4's 'to whom' resolves to Prisca and Aquila (named in Rom 16:3) — the thanks "
            "is to them.",
            "A negated occurrence (e.g. Rom 1:21 'they gave not thanks') is the same sense in "
            "negation, never its own sense.",
            "Luk 22:18 does not carry this word — the meal verses there are Luk 22:17 and 22:19 "
            "only; never cite 22:18, and never write the passage as a range ('Luk 22:17-19') — "
            "list the verses out.",
        ],
        "jobs": [],
        "provenance": "AUDIT_lexica_rollout.md G2168 PARKED entry (batch-4 word 3, 2026-07-10/11) "
                      "+ BATCH 4 CLOSED banked hints; JP batch-close ruling 2026-07-12. "
                      "Luk 22:18 pin: V9 floor agreement_G2168_v9_20260712-174545 (real-miss "
                      "Luk 22:18 in draws 2/6, neighbor-slip class) + the G227 Joh 8:15 pin "
                      "precedent incl. its range clause (bdcff64/f30ff73); applied under JP's "
                      "standing delegation 2026-07-12, reviewer retro-verification on the record.",
    },
    "G227": {    # ἀληθής — true
        "hints": [
            "1Jn 2:8: this lemma's word is the COMMANDMENT ('a true commandment'); the 'true "
            "light' there is ἀληθινός G228, a different word — off-limits in senses AND range.",
            "A verse carrying both the correspondence question and the juridical question (e.g. "
            "Joh 5:31-32, 3Jn 1:12) is stated as a named dual, never silently listed twice.",
            "Joh 8:15 does not carry this word — the courtroom verses are Joh 8:13, 8:14, 8:16, "
            "8:17 only; never cite 8:15, and never write the passage as a range ('Joh 8:13-17') "
            "— list the four verses out.",
        ],
        "jobs": [],
        "provenance": "AUDIT_lexica_rollout.md G227 PARKED entry (re-selection r14, run session 2, "
                      "2026-07-11) + BATCH 4 CLOSED banked hints; JP batch-close ruling 2026-07-12. "
                      "Joh 8:15 pin: V9 floor agreement_G227_v9_20260712-154728 (real-miss Joh 8:15 "
                      "in draws 1/4/6/9/10, adjudicated one class, neighbor-slip) + JP add ruling "
                      "2026-07-12 (batch-5 run session 2). Range clause: build draw 2, 2026-07-12 "
                      "(second forced dry-run this session; input key c17fa2cd names inputs shared "
                      "with draw 1, not draw-2 bytes — raw is in the session record) — 8:15 rode "
                      "in via gloss-note range 'Joh 8:13-17' under the #28 scanner; JP tighten "
                      "ruling 2026-07-12.",
    },
    "G236": {    # ἀλλάσσω — change/exchange
        "hints": [
            "Isa 40:31 and Isa 41:1 belong with the transformation group (Psa 102:26, Heb 1:12, "
            "1Co 15:51, Dan 4:16).",
            "A verse straddling the substitution/trade seam (e.g. Lev 27:10) gets ONE home or a "
            "named dual, never a silent double listing.",
        ],
        "jobs": [],
        "provenance": "AUDIT_lexica_rollout.md G236 PARKED entry (re-selection r15, run session 3, "
                      "2026-07-12) + BATCH 4 CLOSED banked hints; JP batch-close ruling 2026-07-12. "
                      "Gal 4:20 clause REMOVED at re-entry (run session 2 amendment, 2026-07-12): "
                      "the fresh V9 floor agreement_G236_v9_20260712-165959 homes Gal 4:20 with "
                      "substitution 7-8/10 vs the clause's transformation pin — floor-is-ground-"
                      "truth ruling, reviewer-recommended, applied under JP's standing delegation "
                      "for this word (on the session record).",
    },
    "G2805": {   # κλαυθμός — weeping
        "hints": [
            "Exclusion-state prose asserts ONLY what a cited text states: weeping as "
            "characteristic of the place YES; permanence, duration, or hopelessness NO.",
            "The weeping-and-gnashing sentence is quoted verbatim from the supplied verse text "
            "or not quoted; trims are marked with an ellipsis.",
        ],
        "jobs": [],
        "provenance": "AUDIT_lexica_rollout.md G2805 PARKED entry (re-selection r16, run session 3, "
                      "2026-07-12) + BATCH 4 CLOSED banked hints; JP batch-close ruling 2026-07-12",
    },
    "G162": {    # αἰχμαλωτεύω — take captive
        "hints": [
            "Psa 68:18 reads 'you received gifts by men'; Eph 4:8 (quoting it) reads 'he gave "
            "gifts to men' - describe each text's own wording, never summarize the pair jointly.",
            "Cite every reference under exactly ONE sense; a verse carrying two senses (e.g. "
            "1Ch 5:21 persons+property) is stated as a named dual, never silently listed twice.",
        ],
        "jobs": [],
        "provenance": "AUDIT_lexica_rollout.md G162 PARKED entry (queue word 1, run session 3, "
                      "2026-07-12; hint candidates reviewer-banked in that entry); JP batch-close "
                      "ruling 2026-07-12",
    },
}
