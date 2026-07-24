# G3 memo — what the retirement rebuild writes into the 14,850 lemma-only number cells

For the reviewer's G3 ruling (docs/PLAN_r2_stage3.md; blocking candidate-3
sizing). Question surfaced in the evidence pass (docs/R2_stage3_evidence.md §1):
the design says lemma-only words get "lemma identity without a number," but never
says what `words.strongs_base` holds for those rows after the Hebrew number is
retired as identity.

Who these rows are: the `pn_greek_identity` lemma-only bucket (14,850 of 32,479)
— ABP proper-noun words whose printed Greek form has NO number in any scheme:
not an inline ABP tag, not a TIPNR/STEP-extended number (the identity builder's
layer (c); STEP coverage was measured at stage 1, so "no number" is a checked
fact, not a gap we could fill). Their Hebrew `strongs_base` today is the R-1
stopgap backfill.

## Option A — leave the Hebrew number in the cell

The cell keeps its current Hebrew number; only the numbered rows (abp-tag +
tipnr) flip to Greek.

- For: every existing join/count/tag keeps working for these rows; nothing
  becomes unfindable even before consumers are touched.
- Against: the column stops meaning one thing — "Greek identity, except 14,850
  rows where it's still the Hebrew stopgap." That mixed state is exactly what
  stage 3 exists to retire, and every future consumer has to know the
  exception. The reader tag fallback would keep printing a Hebrew number under
  a word whose card says "no Strong's mapping" — the Agag-class seam reappears
  for this bucket permanently.

## Option B — clear the cell (no number; Hebrew moves to the Q2 cross-ref home)

The cell goes to the no-number state these words honestly have (the same way a
numberless PN reads '*'/blank today); the Hebrew number lives ONLY in the Q2
cross-ref table, where every card/count that wants the OT path looks it up.

- For: the column means one thing everywhere; matches the ruled Q3 card state
  ("ABP-only form — no Strong's mapping" — a missing identity is data); the tag
  helper's lemma-only branch (already in #2's scope) renders these correctly
  with no extra casework.
- Against: number-keyed reads stop returning these rows, so the rebuild's
  must-touch list grows: the Hebrew cross-ref count and any "findable by
  H-number" path must read the Q2 home instead (already G4's class of work —
  same repoint the cross-ref count needs anyway). Word study reaches these
  words by lemma/stored-form only.

## Option C — STEP-extend (assign a G9xxx-style number)

Not actually available: lemma-only is DEFINED as "no number in any scheme
after checking STEP" — stage 1 measured TBESG coverage and these are the
residue. Assigning numbers would mean minting our own, which fabricates an
identity the sources don't carry (provenance contract violation). Listed only
because the ruling named it as an option to be dispositioned.

## Recommendation (per delegation rule — applied as the ruling if accepted)

**Option B.** It is the only option consistent with the already-ruled Q3 state
and the retirement's purpose; its cost (repointing H-number findability at the
Q2 home) is work G4 already mandates for the cross-ref count, so it enlarges an
existing must-touch item rather than adding a new class. Option A preserves
convenience by keeping the exact mixed identity stage 3 is chartered to end;
Option C is fabrication.

One condition to carry into the rebuild charter if B is ruled: the two-
derivations-style gate must count these 14,850 rows explicitly (before: Hebrew-
keyed; after: reachable via Q2 home + lemma) and show zero rows that were
findable before and unfindable after — the S2-Q4 "nothing becomes unfindable"
bar applied to the retirement.
