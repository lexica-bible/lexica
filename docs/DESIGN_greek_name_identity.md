# DESIGN — Greek name identity for ABP proper nouns

Status: DESIGN PASS ONLY (JP ruling R-2, 2026-07-16: direction approved; no build this
session). Supersedes-in-direction the earlier "don't re-pitch a pure Greek re-key" ruling
(memory `project_entity_resolution_rebuild` / data-model.md "Bound-card occurrences") —
that ruling rejected a re-key under the OLD constraint set; R-2 changes the goal, so the
constraint that killed it (lexicon lacks STEP-extended G-numbers) becomes work item, not
blocker. Ties to `docs/PROVENANCE_CONTRACT.md` §4 (three-state model) and
`docs/tickets/TICKET_headword_class.md` (rebuild ordering).

## Where we are (the stopgap)

ABP proper nouns carry `strongs='*'`; `import_tipnr.py` backfills `strongs_base` with the
entity's HEBREW number by matching the in-verse English through its ladder. Consequences:
- An ABP (Greek text) name's identity is a Hebrew number reached via an English spelling.
- The word card's Strong's head, lexicon join, and occurrence counts all key Hebrew.
- LXX-only forms (oumasphae, aisi, ephradabak…) have no English-keyed match → double-star
  rows, no identity at all.
- The lexicon join `l.strongs_g = w.strongs_base` structurally can't show a Greek lemma
  for these words.

## Target state (R-2)

The ABP interlinear reads GREEK names: a proper noun in the Greek text carries a Greek
identity — Greek Strong's number where one exists, Greek lemma always — with the Hebrew
number kept as cross-reference data, not as the identity. LXX-only forms resolve to their
Greek identity like any other Greek word. Where NO mapping exists in any scheme, the card
shows the honest state — "ABP-only form, no Strong's mapping" — never a fabricated bind
(provenance contract: this is a fourth labeled condition under the source-of-record rule,
rendered like the three-state model's unmatched cases; a missing identity is data, not a
gap to paper over).

## What changes, per layer

1. **Source of Greek identity (the core question).** Candidates:
   - The ABP text's own inline tags where a real G-number exists on the name.
   - TIPNR's Greek forms — these are STEP-extended numbers (e.g. G9827) our `lexicon`
     table lacks and ABP never prints. Usable only if we import the STEP extended Greek
     lexicon as a side table.
   - The Greek surface itself: lemma identity without a number (lemma + romanization
     from the text), for names no numbering scheme covers.
   Recommendation: layered — real G-number when the text carries one; STEP-extended
   number IF we import that lexicon (open question Q1); otherwise lemma-only identity
   with the honest no-number state.
2. **import_tipnr.py** stops writing the Hebrew number into `strongs_base` for ABP rows
   and instead writes the Greek identity; the Hebrew number moves to a cross-reference
   column or side table (open question Q2 — new field = checkpoint rule, JP OK needed
   before any new column lands).
3. **Lookup/join**: `l.strongs_g = w.strongs_base` starts matching naturally once
   strongs_base holds a G-number the lexicon knows. STEP-extended numbers need their own
   joined table (same COALESCE pattern as `dotted_lexicon`).
4. **Occurrence counts**: bound-card ABP counts currently ride the Hebrew base
   (`/api/strongs-count/<n>?by=base`). Under Greek identity the ABP line counts by the
   Greek key; the KJV/BSB/Hebrew lines keep their own keys (each text counts by its own
   scheme — this is the provenance contract's per-source labeling applied to numbers).
   The Hebrew↔Greek cross-reference makes the cross-text lines still findable.
5. **Entity binding**: `tipnr_entities.bases` must then include the Greek keys, or the
   binder's number-guard (fuzzy path) starts flooring everything ABP-side. Binding is
   name+verse-primary so exact binds survive; the fuzzy number-guard is the exposure.
6. **Word study / SEO / AI feeds**: every consumer keying `strongs_base` H-numbers for
   ABP names follows the same swap; the contamination map in TICKET_headword_class lists
   the consumer set.

## Migration & rollback

- Build-side only, into `bible.db.new` per `/rebuild-words` discipline; live never
  patched. The head-word fix (TICKET_headword_class) MUST land first or in the same
  run — its name extraction is what puts clean name slots under this migration.
- Staged: (stage 1) add the Greek identity alongside the Hebrew stopgap (both stored,
  Hebrew still authoritative) + audit diff; (stage 2) flip the readers to Greek identity
  behind verification; (stage 3) retire the stopgap as identity, keep as cross-ref.
  Each stage independently rollback-able (stage 2 is a code deploy, revertible by git;
  stage 1/3 are rebuilds with the standing bible.db.new swap + backup rotation).
- The two-derivations rule applies: the Hebrew-keyed and Greek-keyed occurrence counts
  for the same entity are independent derivations — their diff is the audit instrument
  for stage 1.

## Open questions — JP rulings needed (not decided here)

- **Q1**: Import the STEP extended Greek lexicon (source of the G9xxx name lemmas) as a
  side table? It's the only way TIPNR's Greek numbers become renderable. Licensing check
  needed (STEP/Tyndale material — CREDITS.md addition).
- **Q2**: Where does the Hebrew number live after the flip — second column on `words`,
  or a side table? (New-field checkpoint either way.)
- **Q3**: LXX-only forms with no number in ANY scheme: lemma-only identity — is
  lemma + "ABP-only form, no Strong's mapping" the approved card rendering? (Exact
  wording is a JP call; the contract requires the state be visible, not its words.)
- **Q4**: Do KJV/BSB name clicks (H-number keyed today, correct for those texts) stay
  untouched? (Design assumes YES — this migration is ABP-side identity only.)
- **Q5**: Timing — same `/rebuild-words` run as the head-word fix (one heavyweight run,
  more risk per run) or the run after (two runs, cleaner isolation)? Design recommends:
  head-word fix + alias map in the approved run now; Greek identity as its own staged
  rebuild after, since its stage-1 audit WANTS the cleaned heads as input.
