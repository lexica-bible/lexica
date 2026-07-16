# REVIEW PAYLOAD — RC-2 re-review (blank star rows: trace results + rescoped fix)

Follow-up to `REVIEW_rebuild_precode.md` Change 2. The approval was conditional on a trace
confirming the 477 blank rows fail at the roster lookup; the trace was run and the picture
is MORE SPECIFIC than the original claim, so per the verdict's own terms it comes back.
RC-1 and retention are applied and pushed (commit 6d7a6ee); nothing RC-2 has been edited.

## What the trace found

**1. Full classification of all 477 blank star rows** (list pulled from the live db, sorted
by the shape of the cell immediately before each blank):

| Pile | Count | Example (cell before the blank) | Diagnosis |
|---|---|---|---|
| Name LEADS the cell | 148 | `Shaul died,` (1Ch 1:49) · `Syria came` (1Ch 18:5) | The predicted class. Splittable. |
| Name buried MID-phrase | 64 | `to king David,` (2Sa 17:17) · `an Egyptian man` (1Sa 30:11) | Name present but not leading; peeling needs reordering judgment. |
| No name in English at all | 40 | `he asked` (1Ch 10:13) · `his procreating` (Gen 11:21) | Source-verified: ABP's English renders the name as a pronoun or folds it away entirely. |
| Cell before is ALSO empty | 225 | trailing `G3588 G*` pairs (1Ki 1:43, 1Sa 7:17) | Source-verified: bare Greek article+name slots ABP gives no separate English word. |

Source spot-checks (from `abp_texts/`, diagnosis-grade): Gen 11:21 Greek repeats "Reu" where
the English says "his"; 1Ch 10:13's second star is rendered "he"; 1Ki 1:43 ends
`...to reign.G936 G3588 G*` — the Greek carries name-slots the English never voices.
**Piles 3+4 (265 rows, 56%) have nothing to redistribute — they are correct as blank
English.** Their only open question is whether such rows should carry a number with no
English (a Strong's-backfill question for the audit session, not a build-English fix).

**2. Roster-failure confirmation (condition a).** The splitter's read-only preview was run
on the live db. Result: `Would split 0 merged name(s)` — every roster-known name was already
split by the earlier production run; skip counters show 653 "no adjacent empty slot" (correct
as-is) and 1 "couldn't peel". The 477 blanks appear in NO counter — they are dropped at the
`is_roster or is_eimi` name check before any shape accounting, exactly the roster-gap
diagnosis. For the 148 cap-lead rows the shape is present and only the name test fails.
(1Ch 10:13's "Saul died" cell, the puzzle case, turned out to be already split — its
remaining blank is a pile-3 "he asked" row, not a roster miss.)

## Rescoped RC-2 proposal

**In scope — the 148 cap-lead rows.** Extend `fix_pn_subject_merge.py` with the `is_capfall`
path as previously specified: capitalized lead, lead not in `_FUNCTION_LEAD`, not roster-known,
adjacent empty `*` slot strictly AFTER, both slots unbracketed; peel exactly one leading word.
Conditions carried over:
- (b) red-first fixture: a synthetic "Shaul died," row added to the local test harness,
  shown FAILING before the change and passing after.
- (c) arithmetic closed before apply: capfall dry-run count on the test copy reconciled
  against the 148 prediction (shortfall = bracketed/slot-before rows, each named) BEFORE
  `--apply`. Control: 1Ch 1:49 → a Shaul row with real identity, no blank row.

**Explicitly NOT in scope, with disposition:**
- 64 mid-phrase rows → ticketed to the audit session (`TICKET_missing_strongs_pn.md` gets
  the list). Peeling a mid-phrase name reorders English — not done blind in a batch run.
- 265 no-English rows → reclassified from "defect" to "correct as blank English"; the
  post-run double-star re-audit treats them as an expected, named residue class instead of
  a failure. Whether they deserve a number-without-English is an audit-session ruling.

**Post-run expectation (replaces "477 → ~0"):** blank-star count 477 → ~329 (477 − 148),
with the remainder itemized by pile; capfall actual vs predicted reconciled row-for-row.

Verdict requested: approve the rescoped capfall (148-row class) + the two dispositions.
