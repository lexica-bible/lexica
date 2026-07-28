#!/usr/bin/env python3
"""build_abp_corrections.py — create the abp_corrections table + insert the seed entries.

Tier B of the certification standard: a source defect is never silently fixed in place.
Each one becomes a row here, applied at rebuild time by scripts/apply_abp_corrections.py
(finish_rebuild.sh step 7 — the true final tail step). Schema + first entries approved
at the Session 1/2 checkpoints (see AUDIT_abp_certification.md).

SEED ENTRIES (adjudicated from cert harness run 1, 2026-07-04):
  * Cushi x6 — 2Sa 18, strongs_base H3570 -> H3569 (Class 2; migrates
    fix_cushi_strongs.py into table form — that script then lapses to the graveyard).
  * Jer 49:13 pos 28 — TWO cells, per the run-1 delta TSV (JP's 2026-07-04 paste):
    strongs_base G166 -> G165 AND the bare strongs 166 -> 165 (L11; ABP printed the
    adjective's number on the noun "eon"; the June retag corrected both columns on
    live). Jer 49:13 ONLY — Hab 3:6 was ruled the other way and is deliberately NOT
    here.
  * L2 (1Sa 6:11) + L10 (Mal 3:6) — 4 cells each (Session 5). Both source files
    (abp_texts AND bh_scrape) dropped a Strong's number, leaving a bare "G" the build
    turned into junk (a glued gloss / a stray word / a polluted english_head search
    key). Restored from the OFFICIAL ABP app (apostolicbibleapp.com) — the living
    authoritative Van der Pool text, the standing witness for source-reading
    adjudications. UNLIKE Cushi/Jer these were NOT hand-fixed on live first, so the
    dry-run reads "cell=source" and apply_abp_corrections.py --apply must run against
    live after build --apply to clean the reader-visible defect.
L5 (the null-form "this/these" rows) lands later — its list was under-specified and
must be re-derived first (Session 6), then read against the same ABP app.

The dry run doubles as validation: it reads each target cell in the given db and
classifies it. Against LIVE (already hand-fixed) every entry should read
"cell=corrected". Against a fresh scratch, "cell=source". Anything else — adjudicate
before --apply.

Usage (on PA):
  python3 scripts/build_abp_corrections.py ~/bible-db/bible.db            # dry run
  python3 scripts/build_abp_corrections.py ~/bible-db/bible.db --apply    # create + insert

Re-runnable: CREATE TABLE IF NOT EXISTS; an entry whose key (book,ch,vs,pos,field)
already has an active row is skipped, never duplicated.
"""
import argparse
import os
import sqlite3
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_abp_corrections import cellmatch as _cellmatch   # shared number-safe compare

SCHEMA = """CREATE TABLE IF NOT EXISTS abp_corrections (
    id              INTEGER PRIMARY KEY,
    book            TEXT NOT NULL,      -- ABP abbrev ('2Sa') — survives rebuilds
    chapter         INTEGER NOT NULL,
    verse           INTEGER NOT NULL,
    position        INTEGER NOT NULL,   -- words.position at authoring time
    field           TEXT NOT NULL,      -- words column ('strongs_base', 'english', ...)
    source_value    TEXT,               -- what the faithful parse yields — PRECONDITION
    corrected_value TEXT,
    reason          TEXT NOT NULL,
    ledger_ref      TEXT,               -- 'L2', 'L11', 'Class2-cushi', ...
    applied_at      TEXT NOT NULL CHECK (applied_at IN ('ingest','read')),
    status          TEXT NOT NULL DEFAULT 'active',   -- active | retired | superseded
    created         TEXT NOT NULL
)"""

_CUSHI_REASON = ("Cushite messenger in 2Sa 18 is H3569 (Cush cluster); BH source tags "
                 "H3570 (the person Cushi of Jer 36:14). Migrated from "
                 "fix_cushi_strongs.py; adjudicated cert run 1 Class 2.")
_JER_REASON = ("ABP prints the adjective's number G166 on the noun 'eon' (aion, G165) — "
               "source 'intoG1519 eon.G3588 G166'. Jer 49:13 ONLY: Hab 3:6 was ruled the "
               "opposite way (adjective slot, G166 honest) and is NOT corrected. "
               "Adjudicated cert run 1 Class 3 / L11.")
_L2_REASON = ("ABP source (abp_texts AND bh_scrape) dropped the Strong's number on the "
              "'buttocks' word (edron) — printed a bare 'G'; the build folded the next tag "
              "G1473 (auton, 'their') onto the slot and glued 'G' into the gloss + the "
              "english_head search key. Restored to G1475.3 (attested 3x same-chapter: 1Sa "
              "5:9 / 5:12 / 6:5) and confirmed by the official ABP app (apostolicbibleapp.com) "
              "1Sa 6:11 = 1475.3-1473. L2.")
_L10_REASON = ("ABP source dropped the Strong's number on the verb 'change' (elloiomai) — a "
               "bare trailing 'G' (bh_scrape shows a dangling '3756-'), which the build "
               "emitted as a stray word with a 'g' english_head. Restored to G241.2 (ouk "
               "G3756 stays on pos 6) per the official ABP app (apostolicbibleapp.com) Mal "
               "3:6. L10.")

_ACT73_REASON = ("S10 word-side. Act 7:3 ending: ABP lumps 'I show to you!' onto ἄν (G302) with "
                 "trailing empty σοι/δείξω slots; the build spread them but left δείξω ('I show', "
                 "G1166) reading AFTER σοι ('to', G4671), so the words show 'which to I show you!'. "
                 "Source/prose read 'which I show to you!'. Give pos 19+20 a shared bracket + "
                 "greek_pos (I show=1, to=2) so the reader orders them — each word keeps its own "
                 "english/number; 'which' (18) and 'you!' (21) stay put. Reorder metadata ONLY "
                 "(option B), no english/strongs moved. Verified via scripts/control_act7_3.py "
                 "(reorder_english render = 'a land which I show to you!').")

_MAT2029_REASON = ("S10 word-side. Mat 20:29 bracket '[multitudeG3793 1a great]': 'multitude' has "
                   "NO source position digit, so it took BH's greek_pos 1 — tying with 'a great' "
                   "(source digit 1). A tie leaves the reader unable to order them, so the words "
                   "show as 'multitude a great'; source/prose read 'a great multitude'. Set "
                   "'multitude' greek_pos 1->2 so it reads after 'a great' (the trailing '.' then "
                   "floats to it). Its own bracket; the only mixed numbered/un-numbered case in "
                   "the feed. Mirrors the Mat 20:29 prose Tier B row (S9 f).")

_JER923_REASON = ("Jer 9:23 clause 1: ABP's own order digits carry a typo — '[2boast 1the "
                  "2wise man]' (duplicate 2, missing 3) while the two parallel clauses read "
                  "'[3boast 1the 2strong man]' / '[3boast 1the 2rich man]' correctly. CONFIRMED "
                  "in the official ABP app (apostolicbibleapp.com, JP screenshot 2026-07-28): "
                  "same defective digits in its Greek display; the app is unaffected because it "
                  "renders digits raw (readers reorder mentally) and its independent gloss line "
                  "reads the correct order — only a resolver like our build executes them, "
                  "yielding 'Let not the boast wise man'. Intent beyond doubt from the two "
                  "correctly-marked siblings + the app's own gloss. Digit-only fix: 'boast' "
                  "greek_pos 2->3; wording untouched (our eSword edition prints 'wise man', the "
                  "app 'wise one' — edition difference, out of scope). Word row + prose row "
                  "together fix reading text, chips, and interlinear (all read the same stored "
                  "order). Reported by JP from reading, classified 2026-07-25.")

_DAN433_REASON = ("ABP tags the feminine-dative 'αὐτῇ' (αὐτός, G846) with ἐγώ's number G1473 at "
                  "Dan 4:33 pos 1 ('αὐτῇ τῇ ὥρᾳ' = 'in that very hour', Theodotion). Decided by "
                  "MORPHOLOGY, not a breathing eyeball: a dative slot agreeing with τῇ ὥρᾳ spelled "
                  "αυτ- can only be αὐτῇ (αὐτός) — οὗτος's fem. dative is ταύτῃ (ταυτ-) and αὕτη is "
                  "nominative, so neither fits. Official ABP app (apostolicbibleapp.com) shows the "
                  "slot numbered 1473, rendering 'In this hour'. Escaped Path C because Daniel 4 "
                  "(OG-vs-Theodotion divergence) left the row unanchored — blank lemma/morph, so the "
                  "corpus-wide αὐτός→G846 correction never reached it. L5.")

# Bracket-digit sweep DUPLICATE pass reasons (2026-07-28). Triage record + witness evidence:
# docs/tickets/bracket_digit_sweep.txt. All app reads fetched from apostolicbibleapp.com
# /Chapters/<Book> <ch>.html the same day.
_BD_1SA93_REASON = ("Bracket-digit sweep: '[6were lost 1the 2donkeys 3of Kish 4the 5father "
                    "6of Saul]' — duplicate 6, missing 7. APP-SAME (official app carries the "
                    "identical typo). Intent by inference: verb sorts last, Jer 9:23 pattern. "
                    "'were lost' 6->7 -> 'the donkeys of Kish the father of Saul were lost'.")
_BD_1SA178_REASON = ("Bracket-digit sweep: '[2not 2I 1Am]' — duplicate 2, missing 3. "
                     "APP-CORRECTED: official app reads '[3not 2I 1Am]' = 'Am I not'. Live "
                     "reads 'Am not I' (tie luck, readable but deviant). 'not' 2->3.")
_BD_2CH1013_REASON = ("Bracket-digit sweep: '[2abandoned 1king 2Rehoboam]' — duplicate 2, "
                      "missing 3. APP-SAME. Intent by inference (verb last, Jer 9:23 "
                      "pattern): 'abandoned' 2->3 -> 'king Rehoboam abandoned'.")
_BD_EXO323_REASON = ("Bracket-digit sweep: '[4removed 1all 2the 3people 4the 6ear-rings "
                     "5gold]' — duplicate 4. APP-CORRECTED: official app reads '[4removed "
                     "1all 2the 3people 5the 7ear-rings 6gold]'. Digit rows ONLY: live "
                     "verses.text already reads 'the gold ear-rings' (fixed by a later build "
                     "pass) but stored digits still garble chip/interlinear order. 2nd 'the' "
                     "4->5, 'ear-rings' 6->7, 'gold' 5->6.")
_BD_JER37_REASON = ("Bracket-digit sweep: '[4saw 5her breach-of-contract 1the "
                    "2covenant-breaker 1Judah]' — duplicate 1, missing 3. APP-PARALLEL: app "
                    "3:7 carries the same typo, but the app's own 3:8 twin reads '[4feared "
                    "not 1the 2covenant-breaker 3Judah]'. 'Judah' 1->3 -> 'the "
                    "covenant-breaker Judah saw her breach-of-contract'.")
_BD_JOB3913_REASON = ("Bracket-digit sweep: '[2conceive 1the stork 2and 3feathers]' — "
                      "duplicate 2, missing 4. APP-CORRECTED: official app reads "
                      "'[4conceive 1the stork 2and 3feathers]'. 'conceive' 2->4 -> 'the "
                      "stork and feathers conceive?'.")
_BD_MAR1617_REASON = ("Bracket-digit sweep: '[3languages 3they shall speak 2new]' — "
                      "duplicate 3, missing 1. APP-CORRECTED: official app reads "
                      "'[3languages 1they shall speak 2new]' = 'they shall speak new "
                      "languages'. Live reads 'new languages they shall speak' (readable "
                      "but deviant from source intent). 'they shall speak' 3->1.")
_BD_REV111_REASON = ("Bracket-digit sweep: '[2stood 1the 2angel]' — duplicate 2, missing 3. "
                     "APP-SAME. Intent by inference (verb last, Jer 9:23 pattern): 'stood' "
                     "2->3 -> 'the angel stood,' (trailing comma floats to group end).")

# Bracket-digit sweep MIXED pass reasons (2026-07-28, second batch). Live re-bin collapsed
# 24 source-side door candidates to 5: the BH digit-fill already fixed 18 on live (ticket).
# All 5 are APP-CORRECTED witness: the official app shows the exact intended digit.
_BD_1SA2111_REASON = ("Bracket-digit sweep MIXED: live digits [3not 2this 2Is] tie 'this' "
                      "before 'Is' -> prose 'this Is not David'. APP-CORRECTED: app reads "
                      "[3not 2this 1Is] = 'Is this not David'. 'Is' 2->1.")
_BD_2SA1618_REASON = ("Bracket-digit sweep MIXED: live digits [2serving to him 2I will be] "
                      "tie -> 'serving to him I will be'. APP-CORRECTED: app reads "
                      "[2serving to him 1I will be] = 'I will be serving to him'. "
                      "'I will be' 2->1.")
_BD_MIC113_REASON = ("Bracket-digit sweep MIXED: live digits [2the head 3of sin 3is] -> "
                     "'the head of sin is'. APP-CORRECTED: app reads [2the head 3of sin "
                     "1is] = 'is the head of sin'. 'is' 3->1.")
_BD_NEH1243_REASON = ("Bracket-digit sweep MIXED: live digits [2gladness 2with great;] tie "
                      "-> 'gladness with great;'. APP-CORRECTED: app reads [2gladness "
                      "1with great] = 'with great gladness'. 'with great;' 2->1 (the "
                      "trailing ';' floats to group end).")
_BD_PSA1161_REASON = ("Bracket-digit sweep MIXED: live digits [2shall listen to 2the LORD] "
                      "tie -> 'that shall listen to the LORD the voice'. APP-CORRECTED "
                      "(app Ps 116:2, LXX verse offset): [2shall listen to 1 the LORD] = "
                      "'that the LORD shall listen to the voice'. 'the LORD' 2->1.")

# (book, chapter, verse, position, field, source_value, corrected_value, reason, ledger_ref)
ENTRIES = [
    ("2Sa", 18, 21,  4, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 21, 12, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 22, 19, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 23, 23, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 31,  3, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("2Sa", 18, 32,  6, "strongs_base", "H3570", "H3569", _CUSHI_REASON, "Class2-cushi"),
    ("Jer", 49, 13, 28, "strongs_base", "G166",  "G165",  _JER_REASON,   "L11"),
    ("Jer", 49, 13, 28, "strongs",      "166",   "165",   _JER_REASON,   "L11"),
    # L2 — 1Sa 6:11 pos 21 (Session 5; defect still live, apply after build --apply)
    ("1Sa",  6, 11, 21, "strongs",      "1473",                "1475.3",             _L2_REASON,  "L2"),
    ("1Sa",  6, 11, 21, "strongs_base", "G1473",               "G1475",              _L2_REASON,  "L2"),
    ("1Sa",  6, 11, 21, "english",      "of their buttocks.G", "of their buttocks.", _L2_REASON,  "L2"),
    ("1Sa",  6, 11, 21, "english_head", "buttocksg",           "buttocks",           _L2_REASON,  "L2"),
    # L10 — Mal 3:6 pos 7, the stray verb slot (Session 5; defect still live)
    ("Mal",  3,  6,  7, "strongs",      "",   "241.2", _L10_REASON, "L10"),
    ("Mal",  3,  6,  7, "strongs_base", "",   "G241",  _L10_REASON, "L10"),
    ("Mal",  3,  6,  7, "english",      "G",  "",      _L10_REASON, "L10"),
    ("Mal",  3,  6,  7, "english_head", "g",  "",      _L10_REASON, "L10"),
    # L5 — Dan 4:33 pos 1, αὐτῇ (αὐτός) mis-numbered as ἐγώ (Session 7; defect live, apply after build --apply)
    ("Dan",  4, 33,  1, "strongs",      "1473",  "846",  _DAN433_REASON, "L5"),
    ("Dan",  4, 33,  1, "strongs_base", "G1473", "G846", _DAN433_REASON, "L5"),
    # S10 — Mat 20:29 pos 7, the un-numbered bracket word "multitude" (word side)
    ("Mat", 20, 29,  7, "greek_pos",    "1",     "2",    _MAT2029_REASON, "S10-mat2029"),
    # S10 — Act 7:3 pos 19/20, reorder "I show" before "to" via reorder metadata (option B).
    # Both cells are blank now -> source_value is None (a NULL cell matches only None).
    ("Act",  7,  3, 19, "bracket_id",   None,    "1",    _ACT73_REASON,   "S10-act7:3"),
    ("Act",  7,  3, 19, "greek_pos",    None,    "2",    _ACT73_REASON,   "S10-act7:3"),
    ("Act",  7,  3, 20, "bracket_id",   None,    "1",    _ACT73_REASON,   "S10-act7:3"),
    ("Act",  7,  3, 20, "greek_pos",    None,    "1",    _ACT73_REASON,   "S10-act7:3"),
    # Jer 9:23 pos 4 'boast' — source order-digit typo (duplicate 2, missing 3), word side
    ("Jer",  9, 23,  4, "greek_pos",    "2",     "3",    _JER923_REASON,  "JER9:23"),
    # ---- Bracket-digit sweep, DUPLICATE pass (2026-07-28; docs/tickets/bracket_digit_sweep.txt).
    # Witness classes per row: APP-CORRECTED = the official ABP app (apostolicbibleapp.com,
    # fetched 2026-07-28) shows FIXED digits = exact intent; APP-SAME = app carries the same
    # typo (Jer 9:23 class), intent by inference; APP-PARALLEL = intent from a corrected twin.
    ("1Sa",  9,  3,  1, "greek_pos",    "6",     "7",    _BD_1SA93_REASON,   "BD-1Sa9:3"),
    ("1Sa",  9,  3, -1, "verses.text",
     "And the donkeys of Kish the father were lost of Saul. And Kish said to Saul his son, "
     "Take with yourself one of the servant-lads, and rise up and go and seek the donkeys!",
     "And the donkeys of Kish the father of Saul were lost. And Kish said to Saul his son, "
     "Take with yourself one of the servant-lads, and rise up and go and seek the donkeys!",
     _BD_1SA93_REASON, "BD-1Sa9:3"),
    ("1Sa", 17,  8, 18, "greek_pos",    "2",     "3",    _BD_1SA178_REASON,  "BD-1Sa17:8"),
    ("1Sa", 17,  8, -1, "verses.text",
     "And he stood and yelled out to the battle array of Israel, and said to them, Why are "
     "you come forth to deploy for battle right opposite us? Am not I a Philistine, and you "
     "are Hebrews of Saul? Choose for yourselves a man, and let him come down to me!",
     "And he stood and yelled out to the battle array of Israel, and said to them, Why are "
     "you come forth to deploy for battle right opposite us? Am I not a Philistine, and you "
     "are Hebrews of Saul? Choose for yourselves a man, and let him come down to me!",
     _BD_1SA178_REASON, "BD-1Sa17:8"),
    ("2Ch", 10, 13,  7, "greek_pos",    "2",     "3",    _BD_2CH1013_REASON, "BD-2Ch10:13"),
    ("2Ch", 10, 13, -1, "verses.text",
     "And the king answered them hard; and king abandoned Rehoboam the counsel of the elders.",
     "And the king answered them hard; and king Rehoboam abandoned the counsel of the elders.",
     _BD_2CH1013_REASON, "BD-2Ch10:13"),
    # Exo 32:3 — digit rows ONLY: live verses.text already reads correctly ("the gold
    # ear-rings"), fixed by a later build pass, but the stored digits still garble the
    # word-order surfaces (chips/interlinear). No prose row — its precondition can't match.
    ("Exo", 32,  3,  5, "greek_pos",    "4",     "5",    _BD_EXO323_REASON,  "BD-Exo32:3"),
    ("Exo", 32,  3,  6, "greek_pos",    "6",     "7",    _BD_EXO323_REASON,  "BD-Exo32:3"),
    ("Exo", 32,  3,  8, "greek_pos",    "5",     "6",    _BD_EXO323_REASON,  "BD-Exo32:3"),
    ("Jer",  3,  7, 21, "greek_pos",    "1",     "3",    _BD_JER37_REASON,   "BD-Jer3:7"),
    ("Jer",  3,  7, -1, "verses.text",
     "And I said after her committing harlotry all these things, Turn to me! And she turned "
     "not. And the Judah covenant-breaker saw her breach-of-contract.",
     "And I said after her committing harlotry all these things, Turn to me! And she turned "
     "not. And the covenant-breaker Judah saw her breach-of-contract.",
     _BD_JER37_REASON, "BD-Jer3:7"),
    ("Job", 39, 13,  5, "greek_pos",    "2",     "4",    _BD_JOB3913_REASON, "BD-Job39:13"),
    ("Job", 39, 13, -1, "verses.text",
     "The wing delighting ostriches; but should the stork conceive and feathers?",
     "The wing delighting ostriches; but should the stork and feathers conceive?",
     _BD_JOB3913_REASON, "BD-Job39:13"),
    # Mar 16:17 — readable-but-deviant live ("new languages they shall speak"); included per
    # reviewer lean (app gives exact intended digits); JP may pull it at the dry-run gate.
    ("Mar", 16, 17, 13, "greek_pos",    "3",     "1",    _BD_MAR1617_REASON, "BD-Mar16:17"),
    ("Mar", 16, 17, -1, "verses.text",
     "And signs to these believing shall follow closely; in my name they shall cast out "
     "demons; new languages they shall speak;",
     "And signs to these believing shall follow closely; in my name they shall cast out "
     "demons; they shall speak new languages;",
     _BD_MAR1617_REASON, "BD-Mar16:17"),
    ("Rev", 11,  1,  7, "greek_pos",    "2",     "3",    _BD_REV111_REASON,  "BD-Rev11:1"),
    # ---- MIXED pass batch (2026-07-28, second): 5 verses, single-digit + prose each.
    ("1Sa", 21, 11,  9, "greek_pos",    "2",     "1",    _BD_1SA2111_REASON, "BD-1Sa21:11"),
    ("1Sa", 21, 11, -1, "verses.text",
     "And the servants of Achish said to him, this Is not David the king of the land? Did "
     "not the women joining in a dance to this one taking the lead, saying, Saul struck his "
     "thousands, and David his ten thousands?",
     "And the servants of Achish said to him, Is this not David the king of the land? Did "
     "not the women joining in a dance to this one taking the lead, saying, Saul struck his "
     "thousands, and David his ten thousands?",
     _BD_1SA2111_REASON, "BD-1Sa21:11"),
    ("2Sa", 16, 18, 21, "greek_pos",    "2",     "1",    _BD_2SA1618_REASON, "BD-2Sa16:18"),
    ("2Sa", 16, 18, -1, "verses.text",
     "And Hushai said to Absalom, No, but following after whoever the LORD chooses, and "
     "this people, and every man of Israel. serving to him I will be and I shall sit down "
     "with him.",
     "And Hushai said to Absalom, No, but following after whoever the LORD chooses, and "
     "this people, and every man of Israel. I will be serving to him and I shall sit down "
     "with him.",
     _BD_2SA1618_REASON, "BD-2Sa16:18"),
    ("Mic",  1, 13,  8, "greek_pos",    "3",     "1",    _BD_MIC113_REASON,  "BD-Mic1:13"),
    ("Mic",  1, 13, -1, "verses.text",
     "even noise of chariots and ones riding. Dwelling Lachish the head of sin is to the "
     "daughter of Zion; for in you they found the impious deeds of Israel.",
     "even noise of chariots and ones riding. Dwelling Lachish is the head of sin to the "
     "daughter of Zion; for in you they found the impious deeds of Israel.",
     _BD_MIC113_REASON, "BD-Mic1:13"),
    ("Neh", 12, 43, 16, "greek_pos",    "2",     "1",    _BD_NEH1243_REASON, "BD-Neh12:43"),
    ("Neh", 12, 43, -1, "verses.text",
     "And they sacrificed in that day great sacrifices, and they were glad. For God "
     "gladdened them gladness with great; and their wives and their children were glad; "
     "and the gladness in Jerusalem was heard from far off.",
     "And they sacrificed in that day great sacrifices, and they were glad. For God "
     "gladdened them with great gladness; and their wives and their children were glad; "
     "and the gladness in Jerusalem was heard from far off.",
     _BD_NEH1243_REASON, "BD-Neh12:43"),
    ("Psa", 116, 1,  3, "greek_pos",    "2",     "1",    _BD_PSA1161_REASON, "BD-Psa116:1"),
    ("Psa", 116, 1, -1, "verses.text",
     "I loved that shall listen to the LORD the voice of my supplication.",
     "I loved that the LORD shall listen to the voice of my supplication.",
     _BD_PSA1161_REASON, "BD-Psa116:1"),
    ("Rev", 11,  1, -1, "verses.text",
     "And was given to me a reed measure likened to a rod. And the stood angel, saying, "
     "Arise and measure the temple of God, and the altar, and the ones doing obeisance in it!",
     "And was given to me a reed measure likened to a rod. And the angel stood, saying, "
     "Arise and measure the temple of God, and the altar, and the ones doing obeisance in it!",
     _BD_REV111_REASON, "BD-Rev11:1"),
    # Jer 9:23 prose — the same typo executed into verses.text (clause 1 only)
    ("Jer",  9, 23, -1, "verses.text",
     "Thus says the LORD, Let not the boast wise man in his wisdom! And let not the strong "
     "man boast in his strength! And let not the rich man boast in his riches!",
     "Thus says the LORD, Let not the wise man boast in his wisdom! And let not the strong "
     "man boast in his strength! And let not the rich man boast in his riches!",
     _JER923_REASON, "JER9:23"),
]


# S9 fix (f): the 5 prose (verses.text) Tier B rows. Read from the adjudication file so the
# adjudicated text keeps ONE source of truth. Same overlay, NO schema change — reuse existing
# columns with position=-1 (a non-slot sentinel, inert to the words path) and field='verses.text'.
# apply_abp_corrections routes these to a guarded verses.text UPDATE (its --only verses point).
_F_REASON = ("S9 fix (f): malformed-bracket order / Mat 20:29 dropped word — verses.text order "
             "corrected against the pinned feed; the parser cannot fix these (needs the "
             "adjudicated bracket order).")


def _prose_tierB(path="AUDIT_tierB_f_proposed.json"):
    import json
    import os
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        rows = []
        for r in json.load(f):
            book, cv = r["ref"].rsplit(" ", 1)
            ch, vs = cv.split(":")
            rows.append((book, int(ch), int(vs), -1, "verses.text",
                         r["before"], r["after"], _F_REASON, "S9-f"))
        return rows


ENTRIES += _prose_tierB()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="create table + insert (default = dry run)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] build_abp_corrections -> {args.db}")
    print(f"  {len(ENTRIES)} seed entr(ies); created stamp = {date.today().isoformat()}\n")

    has_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_corrections'"
    ).fetchone()
    print(f"  table abp_corrections: {'exists' if has_table else 'will be created'}")
    if args.apply:
        conn.execute(SCHEMA)

    ins = skip = warn = 0
    for (book, ch, vs, pos, field, src, cor, reason, ref) in ENTRIES:
        key = f"{book} {ch}:{vs} pos {pos} {field}"
        # validate against the target db: what does the cell hold right now?
        if field == "verses.text":                          # S9 (f): prose row — check verses.text
            cell = conn.execute(
                "SELECT text AS val FROM verses WHERE book=? AND chapter=? AND verse=?",
                (book, ch, vs)).fetchall()
        else:
            cell = conn.execute(
                f"""SELECT w."{field}" AS val FROM words w JOIN verses v ON v.id=w.verse_id
                    WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?""",
                (book, ch, vs, pos)).fetchall()
        if len(cell) != 1:
            tag = f"!! {len(cell)} matching slot(s) — ADJUDICATE before apply"
            warn += 1
        elif _cellmatch(cell[0]["val"], cor):
            tag = "cell=corrected (already hand-fixed — expected on live)"
        elif _cellmatch(cell[0]["val"], src):
            tag = "cell=source (uncorrected — expected on a fresh scratch)"
        else:
            tag = f"!! cell={cell[0]['val']!r} matches NEITHER — ADJUDICATE before apply"
            warn += 1

        dup = None
        if has_table or args.apply:
            dup = conn.execute(
                """SELECT 1 FROM abp_corrections WHERE book=? AND chapter=? AND verse=?
                   AND position=? AND field=? AND status='active'""",
                (book, ch, vs, pos, field)).fetchone()
        if dup:
            print(f"  == {key}: active row already present — not duplicated. [{tag}]")
            skip += 1
            continue
        if args.apply:
            conn.execute(
                """INSERT INTO abp_corrections (book, chapter, verse, position, field,
                       source_value, corrected_value, reason, ledger_ref, applied_at,
                       status, created)
                   VALUES (?,?,?,?,?,?,?,?,?,'ingest','active',?)""",
                (book, ch, vs, pos, field, src, cor, reason, ref, date.today().isoformat()))
        ins += 1
        print(f"  -> {key}: {src!r} -> {cor!r}  [{ref}]  {tag}")

    if args.apply:
        conn.commit()
        n = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='active'").fetchone()[0]
        print(f"\n  written. active rows in table now: {n}")
    else:
        print(f"\n  DRY RUN — nothing written. would insert {ins}, skip {skip} duplicate(s).")
    if warn:
        print(f"  !! {warn} entr(ies) flagged above — resolve before trusting --apply.")
    conn.close()
    sys.exit(1 if warn else 0)


if __name__ == "__main__":
    main()
