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
  roster:     optional FLOOR-CONSENSUS carve for a path-(c) word (PATH (c) DESIGN —
              CLOSED, AUDIT 2026-07-13). A DISTINCT LEGAL CLASS from hints/jobs: the
              hand-carve ban above (no preferred sense count, no carve) governs
              hints/jobs ONLY. A roster is allowed to fix HOW MANY senses and WHICH
              verses group, because it is not hand-invented — it is the floor's OWN
              repeated-review consensus (count = the modal per-draw sense count; homes
              = hand-authored from the floor's per-verse company, banked with
              provenance). It never fixes the WORDING. Shape:
                {floor, count, groups:[[refs]…], seams:[{ref,group,why}],
                 float:[refs], excluded:[refs], provenance}
              Injected only under the --roster flag (soft-explicit draw context; frozen
              V9 prompt untouched); enforced post-draw by #30 membership + the #55
              sense-count guard. See DESIGN_hint_tooling.md's floor-consensus class.
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
        # PATH (c) roster — BYTE-FOR-BYTE from AUDIT "PATH (c) DESIGN — CLOSED" (2026-07-13; #51).
        # COUNT-anchored: poles blur ~2/10 even under clean anchors; the #55 count guard is the enforcer.
        "roster": {
            "floor": "agreement_G1390_v9_20260712-181939.json", "count": 2,
            "groups": [
                ["Psa 68:18","Eph 4:8","Mat 7:11","Luk 11:13","Pro 18:16","Pro 19:17","Gen 25:6","Gen 47:22",
                 "Dan 2:6","Dan 2:48","Dan 5:17","2Ch 2:10","2Ch 21:3","2Ch 32:23","1Ki 13:7","Php 4:17",
                 "Hos 9:1","Hos 10:6","Ecc 3:13","Ecc 5:19","Deu 23:23","Eze 46:16","Eze 46:17","2Sa 19:42"],
                ["Num 18:6","Num 18:7","Num 18:11","Num 18:29","Num 3:9","Num 28:2","Lev 7:30","Lev 23:38",
                 "Exo 28:38","Eze 46:5","Eze 20:31","2Ch 31:14","Ecc 5:1"]],
            "seams": [], "float": ["Num 27:6"],
            "provenance": "floor agreement_G1390_v9_20260712-181939.json pole-affinity, sharpened anchors Mat 7:11 / Num 18:6 (2/10 clean) + modal count; count-anchored; Psa 68:18+Eph 4:8 homed A on the sharpened read (float premise falsified); ruling 2026-07-13"},
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
        # PATH (c) roster — BYTE-FOR-BYTE from AUDIT "PATH (c) DESIGN — CLOSED" (2026-07-13; #51).
        # MEMBERSHIP-anchored: count soft (modal 3 of a 1-5 spread); #30 membership is the enforcer.
        "roster": {
            "floor": "agreement_G227_v9_20260712-154728.json", "count": 3,
            "groups": [
                ["1Jn 2:8","1Jn 2:27","1Pe 5:12","2Pe 2:22","3Jn 1:12","Act 12:9","Dan 8:26","Deu 13:14",
                 "Gen 41:32","Isa 41:26","Isa 43:9","Job 42:7","Job 42:8","Joh 3:33","Joh 4:18","Joh 5:31",
                 "Joh 5:32","Joh 8:26","Joh 10:41","Joh 19:35","Joh 21:24","Pro 22:21","Tit 1:13"],
                ["Joh 8:13","Joh 8:14","Joh 8:16","Joh 8:17"],
                ["2Ch 31:20","Isa 42:3","Job 5:12","Job 17:10","Php 4:8","Pro 1:3"]],
            "seams": [
                {"ref":"Isa 42:3","group":3,"why":"THE residual — cond 7/10 + own company Job5:12/Pro1:3/Php4:8/2Ch31:20 at 7-8/10; d3 wrongly soloed it (#30 fire)"},
                {"ref":"Joh 3:33","group":1,"why":"floor fact 6 vs jurid 1; d3's second #30 drift (put it juridical)"}],
            "float": ["Rom 3:4","Mar 12:14","Mat 22:16","Neh 7:2","Joh 7:18","2Co 6:8"],
            "excluded": ["Joh 8:15"],
            "provenance": "floor agreement_G227_v9_20260712-154728.json 3-anchor (Gen41:32/Joh8:13/Pro1:3) + Isa 42:3 own company (two reads converge) + modal count; membership-anchored (count soft, #30 the enforcer); ruling 2026-07-13"},
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
    "G236": {    # ἀλλάσσω — change/exchange · HOME-anchored (path (c))
        "hints": [
            "A verse straddling the substitution/trade seam (e.g. Lev 27:10) gets ONE home or a "
            "named dual, never a silent double listing.",
            "Dan 4:16 reads 'seven times shall change over him'; Dan 4:25/4:32 read 'seven "
            "seasons shall change over you' — quote one verse and name it, never blend the pair.",
        ],
        "jobs": [],
        # PATH (c) roster — copied BYTE-FOR-BYTE from AUDIT_lexica_rollout.md "PATH (c) DESIGN —
        # CLOSED" (2026-07-13; lesson #51). HOME-anchored: the #30 membership guard is the enforcer.
        "roster": {
            "floor": "agreement_G236_v9_20260712-165959.json", "count": 2,
            "groups": [
                ["1Ki 5:14","1Ki 20:25","2Ki 5:5","2Ki 5:22","2Ki 5:23","2Sa 12:20","Act 6:14","Exo 13:13",
                 "Ezr 6:11","Ezr 6:12","Gal 4:20","Gen 31:7","Gen 35:2","Gen 41:14","Isa 24:5","Jer 2:11",
                 "Jer 52:33","Lev 27:10","Lev 27:27","Lev 27:33","Neh 9:26","Psa 106:20","Rom 1:23"],
                ["1Co 15:51","1Co 15:52","Dan 4:16","Dan 4:25","Dan 4:32","Heb 1:12","Isa 40:31","Isa 41:1","Psa 102:26"]],
            "seams": [{"ref":"Jer 13:23","group":2,"why":"floor 5/5 true seam; ruled transformation (V11.2 #30 park — d3 drifted it to substitution)"}],
            "float": [],
            "provenance": "floor agreement_G236_v9_20260712-165959.json modal homes + AUDIT G236 V11.2 park (Jer 13:23 #30) + draw_hints Gal 4:20/Lev 27:10 rulings; hint-1 (Isa 40:31/41:1) RETIRED into this roster; ruling 2026-07-13"},
        "provenance": "AUDIT_lexica_rollout.md G236 PARKED entry (re-selection r15, run session 3, "
                      "2026-07-12) + BATCH 4 CLOSED banked hints; JP batch-close ruling 2026-07-12. "
                      "Hint (Dan-trio quote discipline) ADDED at the V11 run session (2026-07-12): "
                      "drafted in the G236 RE-PARKED entry (batch-5 run session 2), amendment-2 "
                      "byte-verified against verses.text raw output (Dan 4:16/4:25/4:32), "
                      "reviewer-confirmed, applied under JP's standing delegation. "
                      "Gal 4:20 clause REMOVED at re-entry (run session 2 amendment, 2026-07-12): "
                      "the fresh V9 floor agreement_G236_v9_20260712-165959 homes Gal 4:20 with "
                      "substitution 7-8/10 vs the clause's transformation pin — floor-is-ground-"
                      "truth ruling, reviewer-recommended, applied under JP's standing delegation "
                      "for this word (on the session record). "
                      "Hint-1 (Isa 40:31/41:1 transformation grouping) RETIRED 2026-07-13 into the "
                      "path-(c) roster (subsumed, group 2); see the roster's own provenance.",
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
    "G5088": {   # τίκτω — bear/give birth
        "hints": [
            "Jer 22:26 reads 'into a land of which you were not birthed there; and there you "
            "shall die' - quote its wording byte-exact, keeping ABP's 'of which ... there' "
            "construction, or describe the verse without quoting it.",
        ],
        "jobs": [],
        "provenance": "AUDIT_lexica_rollout.md G5088 PARKED entry (2026-07-14) + quote-repair "
                      "cap-out (V11.2 cap 1, draw 79d00733 DEAD, refused repair banked "
                      "G5088_quote_refused_79d00733.json, 2026-07-15): the model normalized "
                      "ABP's 'of which ... there' to 'where' twice (draw + repair). Jer 22:26 "
                      "bytes = JP live sqlite read 2026-07-15 (on the session record); applied "
                      "under JP's standing delegation, reviewer verification at re-entry "
                      "(ruling 5b).",
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
