# ENGINE_LESSONS.md — what the definition engine v2 should do differently

Design-level lessons only. This file is NOT:
- `AUDIT_lexica_rollout.md` (WHAT happened, per word — the authority on saga detail), or
- the standing rules in `CLAUDE.md` / memory (HOW we operate the current engine).

It is the **v2 design backlog**: one line per lesson, each pointing to its audit-doc entry for the
evidence. It grows by HABIT — add a line the moment a design-level finding is logged, don't batch.
Nothing here is scheduled work; it's the "if we rebuild the engine, change these" list.

## Lessons (this batch, 2026-07-06/07)

1. **Truth-gates converge, style-gates fish.** Holes/merges/completeness settle in 1–few draws; "match
   the sense count" and other style properties never settle. → v2 steers STYLE at the prompt layer
   (formatting block), and GATES only truth properties. *(audit: SHIP BAR re-ruled / three-regimes finding
   / STYLE WATCH #1–#3)*

2. **Fabrication was stimulus-driven, not prompt-driven.** The "Heaven" capitalization fabrication survived
   two prompt generations (V4, V5) and died the instant the case-split was removed from the fed evidence.
   → v2: AUDIT THE FED EVIDENCE before tuning prompts; a stimulus you can delete beats a prompt line that
   steers around it. *(audit: GLOSS-SET CASE-FOLD / οὐρανός three-attempt saga)*

3. **Ship draws sample off the reviewer's modal carve.** ὕδωρ: the target shape was ~70% of reviewer draws,
   yet the ship path missed it twice before hitting on attempt 3. → v2 candidate: ship-path DRAW-UNTIL-MATCH
   against the banked reviewer verdict, natively (not a manual redraw loop). *(audit: G5204 ὕδωρ)*

4. **Substitution blind spot.** A headword standing in for another referent is invisible to reviewer, gates,
   AND collocation flags UNLESS a signature collocate exists (βασιλεία caught "kingdom of heaven"; bare
   "sinned against heaven", Luk 15:18-class, is uncovered). → v2 wants a substitution probe for the
   no-collocate case. *(audit: APPARATUS FINDINGS — blind-spot refined)*

5. **Usage-dimensionality, not referent-concreteness, predicts wobble.** A concrete referent can wobble
   (καρδία, ὕδωρ) if its USES are multi-facet; a word wobbles by how many shallow analytical cuts its usage
   offers. → v2 could pre-classify words by usage-dimensionality and scale reviewer-floor depth accordingly
   (ties to lesson 8). *(audit: Framing correction / G5204 hypothesis result)*

6. **Reuse rule, both directions.** A private copy of the sense-splitter broke the reviewer (per_sense used
   its own bold-only regex); single-source `gloss_set` made the case-fold a one-place atomic fix. → v2 has
   ONE splitter, ONE gloss_set — no second copies of scan/transform logic, ever. *(audit: REVIEWER PARSER
   DRIFT FIX + SECOND PARSER FIX + GLOSS-SET CASE-FOLD)*

7. **Gloss_notes make unverified factual claims about the corpus.** The citation gate checks REFERENCES, not
   ASSERTIONS (capitalization practice, translation behavior). → v2 wants a position/text verification step
   for corpus-practice claims — mechanizable for the capitalization case (verse text is in the DB,
   sentence-initial is testable). *(audit: APPARATUS FINDINGS — unverifiable-assertion defect class)*

8. **Fixed fed-40 under-samples SYSTEMATICALLY on high-occurrence / multi-domain words** (μέγας's dense
   Levitical collocations, οὐρανός's metonym verses unfed entirely, ὕδωρ's purity/river/sea neighbors), and
   presumably wastes sample on redundancy for flat-usage words. → v2 candidate: dynamic fed-count scaled by
   occurrence count and/or usage-dimensionality (lesson 5), possibly collocation-aware sampling that reserves
   slots for high-PMI neighbor contexts so signature uses can't be unfed by chance. **Evidence: every
   collocation flag this batch was a fed-sampling miss — zero were missing senses.** The current design
   survives its under-sampling only because the eyeball-and-resolve step catches it; v2 turns that manual
   resolution into sampling policy. **Strongest instance is θεός** — the fed 40 failed to attest
   προσκυνέω / λατρεύω though serving/bowing are among the most attested θεός treatments corpus-wide
   (λατρεύω uncited across 32 θεός verses, PMI 5.31); the miss reached DESCRIPTIVE PROSE (sense 1 read
   complete while under-describing the referent), not just collocation flags — which upgrades 8's severity
   and the case for collocation-aware slot reservation. *(audit: fed-40 retro thread + μέγας/G39/οὐρανός/
   ὕδωρ flag entries + θεός item B)*

## Carried from v1 (foundational — proven, keep as v2 invariants)

9. **The deterministic/model boundary holds where it's tested.** Every correctness fix that worked is
   DETERMINISTIC (book table, chapter-strip, soft set, case-fold, exact lookup); everything model-side stays
   ADVISORY. → v2 keeps correctness gates deterministic and the model's output advisory-until-gated. *(audit:
   Batch-One process lesson 3)*

10. **Review-what-ships: reviewed prose must be byte-identical to shipped prose.** The draw cache made this
    an invariant (apply reads the reviewed bytes, no fresh model call). → v2 keeps the reviewed artifact and
    the shipped artifact the same object. *(audit: Batch-two prep #1 — draw cache)*

## Added by session-1 mining (2026-07-07)

11. **Double-shelf detection belongs in the engine natively.** v1 had no check for a verse cited under more
    than one sense in the SAME draft — it shipped (G39 1Jn 2:20 + 2Ti 1:9; καρδία 2Co 2:4 + Joh 12:40),
    caught only by live-card eyeballing. A set-intersection over the per-sense ref lists finds it free;
    sub-uses are its natural habitat. → v2 runs it EVERY draw, **FLAG-ONLY (not a gate)**: bridging verses
    are legitimately double-shelved (presence-vs-significance; human rules per instance), and hardening to a
    gate is a data-collection question, not a design default. **Production record since 2026-07-06: 0 fires
    ever ruled noise.** Ship-time live fires ruled keep-both bridges on 3 SHIPPED cards (ἔθνος Eph 2:11,
    μέγας 2Ch 17:12, ἱερεύς Gen 14:18); the ὕδωρ 2Pe 3:5 and οὐρανός Joh 1:32 fires landed on REJECTED
    drafts (moot — the shipped versions fired clean); G39/καρδία were retroactive logs on pre-detector ships.
    Flag-only design validated in production. *(audit: detector shipped commit 61740c0; seam register 1–4)*

12. **Sense-prose action verbs are unverified corpus claims — lesson 7, extended past gloss_notes.** θεός
    sense 1 opened "worshipped as creator" with NO bow/serve verse in the fed 40; the citation gate checks
    REFERENCES, not whether a sense's descriptive VERBS are attested by its own cited verses. Loaded
    abstractions ("worshipped") compress concrete attested acts (προσκυνέω bow, λατρεύω serve) the Greek
    gesture-words don't carry. → v2 applies grounding verification to sense-prose action verbs, not just
    gloss_notes corpus-practice claims. **Mechanization caveat:** harder than the capitalization case —
    "worshipped" vs bow/serve needs semantic matching, not position-checking; realistic v2 form is "FLAG
    loaded abstractions for manual grounding-check," not full automation. *(audit: θεός G2316 sense-1
    decompression, 2026-07-06)*
