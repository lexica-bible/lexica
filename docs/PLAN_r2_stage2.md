# PLAN — R-2 stage 2: flip the ABP readers to Greek identity (code deploy)

Drafted 2026-07-24 off HANDOFF_r2_greek_names.md's stage-1 close-out. Stage 2 is a CODE
deploy, git-revertible — no rebuild, no database swap. The words table is untouched;
everything the readers start showing comes from the stage-1 side tables already live
(`pn_greek_identity` 32,479 rows, `step_lexicon` 10,846 rows). KJV/BSB stay
Hebrew-keyed (Q4, ruled). Hebrew becomes the cross-reference line, not the identity.

## What changes for a reader (the whole visible surface)

An ABP proper-noun word card, on click:
- Identity header: the GREEK number (G1138; STEP-extended G9xxx via step_lexicon) or,
  for lemma-only words, the printed Greek form with the honest state line
  "ABP-only form — no Strong's mapping" (Q3 wording, ruled).
- Greek lemma/translit resolve from lexicon, else step_lexicon (same COALESCE pattern
  as dotted_lexicon).
- The Hebrew number moves to a quiet cross-reference line (it keeps the OT-number
  path findable — KJV/BSB/Hebrew-reader lines still key Hebrew).
- Occurrence line counts by the Greek identity (see S2-Q4).
- Words in the 'none' bucket (3,380) change NOTHING — they keep today's card.

## Rulings needed BEFORE any code (posted in chat with recommendations)

- **S2-Q1 — flip shape: all ABP card surfaces at once, behind one switch?**
  Partial flips make mixed cards (Greek header, Hebrew count). Recommend: one code
  path/helper feeds every surface, controlled by a single named switch
  (`READER_GREEK_IDENTITY`), default OFF at merge — the deploy that turns it ON is the
  gated step, and rollback is flipping it back (faster than a git revert).
- **S2-Q2 — STEP-extended numbers on the card.** G9xxx isn't a classic Strong's
  number; the provenance contract wants sources labeled. Recommend a small "STEP"
  source tag beside extended numbers, same quiet style as the existing badges.
- **S2-Q3 — already ruled:** lemma-only card state wording stands ("ABP-only form —
  no Strong's mapping").
- **S2-Q4 — occurrence counts under the flip.** The two-derivations report shows the
  honest consequence: e.g. Terah = 14 Hebrew-keyed words but G2291×12 + 2 unnumbered —
  the ABP count line will CHANGE on some cards, because it now counts what actually
  shares the Greek identity. Recommend: numbered identities count by Greek number;
  lemma-only cards count by the stored form; the Hebrew cross-ref line carries its own
  count so nothing the reader could find before becomes unfindable. The stage-1 diff
  report (~/r2s1_deriv_diff.txt) is the pre-declared expectation sheet — every changed
  count must trace to its line there.
- **S2-Q5 — verification shape.** No staging server exists. Recommend: (a) local
  tests incl. a new locked test for the identity helper; (b) deploy with the switch
  OFF (proves the code is inert — cards byte-identical); (c) reviewer receipt; (d) JP
  flips the switch ON (one-line deploy); (e) the post-flip control panel below + JP
  screenshots; (f) reviewer receipt closes the stage. Two receipts, mirroring
  trial-then-apply on a code path.

## Pre-declared control panel (checked live after the flip, posted as pass/fail)

- C1 David @ Mat 1:6 card header shows G1138, Greek lemma Δαυίδ; Hebrew H1732 present
  as cross-ref line only.
- C2 An OT name with a STEP-extended number shows the G9xxx identity + STEP tag, lemma
  from step_lexicon (pick from the identity table at flip time; count expected > 0).
- C3 A lemma-only word (from the 14,850) shows the printed Greek + the Q3 state line,
  NO fabricated number.
- C4 A 'none'-bucket word renders EXACTLY today's card (byte-same payload).
- C5 KJV and BSB name clicks: unchanged (Hebrew-keyed) — one of each, screenshots.
- C6 Occurrence line on C1/C2 matches the two-derivations report's numbers.
- C7 Switch OFF at first deploy: an ABP card payload diffed before/after = identical.
- C8 Maachah @ 2Ch 11:21 (stage-1 showcase) still renders its bound card.

## Order of work (nothing starts before the rulings land)

1. Rulings above → recorded here.
2. Consumer enumeration pass: walk TICKET_headword_class's contamination map +
   `docs/claude/word-study.md` and list EVERY code site that serves an ABP PN
   identity/count; the flip helper replaces each listed site; the list is part of the
   review (grep-before-you-size rule).
3. Code behind the switch + tests; frontend rebuild; commit (switch OFF).
4. Deploy OFF → C7 → receipt → flip ON → C1–C8 + screenshots → receipt → stage closed.
5. Stage 3 (retire Hebrew as identity in the words table) stays parked — its own
   rebuild, only after stage 2 has soaked.
