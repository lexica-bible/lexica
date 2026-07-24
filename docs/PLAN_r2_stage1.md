# PLAN — R-2 stage 1: Greek identity ADDED ALONGSIDE (Hebrew stays authoritative)

Drafted 2026-07-24 under the five approved rulings (HANDOFF_r2_greek_names.md) and the
reviewer's stage-1 go. Charter: purely ADDITIVE — after this run every reader, join, and
count behaves byte-for-byte as before; the only new things are side tables and audit
reports. The flip (stage 2) is a later code deploy; nothing here is user-visible.

## What rides this run (batch inventory)

1. **Variant map +11** (committed `59a2d78`, hand-checked, decision lines recorded) —
   picked up automatically by the import_tipnr re-run.
2. **Binder variant batch +206** (added after the 2026-07-24 frame correction — see the
   correction block atop `docs/tickets/variant_batch_verdicts.txt` and the binder-side
   verdicts in `docs/tickets/variant_batch_binder_verdicts.txt`, sub-batched
   NEW-SESSION / R1-REVISIT per the reviewer's condition). Entries live in
   `entity_resolution.py` as the labeled `R2_BINDER_VARIANTS` block; picked up by the
   `build_entity_binding --apply` re-run. **Why this is low-risk (asserted per reviewer
   condition):** a binder alias only ever ADDS a fuzzy candidate — the binder renders a
   fuzzy bind only when the word's stored number also sits in the entity's own number
   set AND the clicked verse is in the entity's reference list; ties floor as HOT. An
   imperfect entry can only leave a word floored, never attach a wrong card. 27 pairs
   killed (gentilic class → pile U; true two-target ambiguity; already covered). All
   25 binder tests pass with the block in place.
3. **STEP extended Greek lexicon import** (Q1: yes, license CLEAR — CC BY 4.0, credit
   already in CREDITS.md). New side table `step_lexicon` built from the same TBESG file
   `build_word_gloss.py` already downloads (reuse its `parse_tbesg`), but keeping the
   full entry per extended G-number: number, Greek lemma, transliteration, brief gloss.
   New table = the Q1-ruled checkpoint; no existing table touched.
4. **Greek identity side table** `pn_greek_identity`, keyed by verse+position for every
   ABP proper-noun word (Q2's side-table ruling applied to stage 1's direction too).
   Per word, layered per the design: (a) real G-number if the ABP text carries one on
   the name, (b) TIPNR's Greek number for the bound entity (renderable once
   `step_lexicon` exists), (c) otherwise lemma-only with an honest empty number
   (Q3's card state — wording lands at stage 2, the STATE is stored now).
   Also snapshots the current Hebrew `strongs_base` per word so the flip's cross-ref
   is frozen at build time.
5. **Two-derivations audit** — the ruled instrument: per entity, occurrence counts
   keyed the old way (Hebrew `strongs_base`) vs the new way (Greek identity). The diff
   report goes to the reviewer BEFORE any swap. Disagreements are resolved against
   TIPNR/ABP, never by preference.
6. **Post-run diagnostic (reviewer-folded):** fresh number-only dump; specifically
   re-check the 82 killed variant pairs — any of their rows still number-only points at
   the word cell (possessive/plural/split), which becomes the next parked pile, not a
   map fix.

KJV/BSB untouched (Q4). No words rebuild: `build_words_from_abp.py` does NOT run —
nothing in the build changed since R-1. Only import_tipnr (writes PN numbers into
words on the COPY) and the two new additive builders run.

## Roster-freeze gate — exact expectation, declared up front

`python3 scripts/check_roster_regression.py` must print **CLEAN — zero additions,
zero changes, zero losses (baseline 4,331 exact)**. The variant map is not part of the
roster (checked 2026-07-24 against roster_baseline.json: none of the 399 R-1 alias keys
are in it; the map is consulted only after a roster miss). Any non-CLEAN result —
including "just additions" — STOPS the run: nothing in this batch touches
import_tipnr's parser or TIPNR.txt, so any delta at all is unexplained.

## Run shape (all commands run by JP on PA; dry-run before every write)

Step 0 — DONE 2026-07-24: `scripts/import_step_lexicon.py`,
`scripts/build_pn_greek_identity.py`, `scripts/audit_two_derivations.py` are in the
repo. All three take the db path as the first argument; the two writers default to
dry-run and need `--apply`; the audit is read-only and prints a labeled CONTROL PANEL
block (named PASS/FAIL per control) at the end of its output.

1. Copies: `cp ~/bible-db/bible.db ~/bible-db/bible_pre_r2s1_$(date +%F).db`
   then `cp ~/bible-db/bible.db ~/bible-db/bible_test.db`.
2. Roster gate (see above): CLEAN or stop.
3. `python3 scripts/import_tipnr.py bible_test.db --dry-run` → paste the summary.
   Expected movement vs R-1: **Matched: 0** (corrected 2026-07-24 after the actual
   dry-run — the original "+11 rows" expectation predated the frame correction; the
   11 surfaces got their numbers in R-1 via DIRECT, so the remaining '*' words are
   the mangled-cell residue no name list fixes. The batch's movement shows at the
   build_entity_binding step as new binds, and words stays byte-identical here).
   Then the real run without `--dry-run`.
   RESULT 2026-07-24: roster CLEAN 4,331 exact; dry-run Matched 0 / 745 residue ✓;
   STEP dry-run: 10,846 entries, TIPNR Greek coverage 476/476 = 100% (the lone
   "missing G0" is TIPNR's nine unnamed#N placeholder people, number 0 — not a word).
4. `python3 scripts/import_step_lexicon.py bible_test.db` (dry-run report: entry count,
   G9xxx coverage, spot lemmas) → `--apply`.
5. `python3 scripts/build_pn_greek_identity.py bible_test.db` (dry-run report: words
   covered, split across the three source layers, unresolved tail) → `--apply`.
6. `python3 scripts/audit_two_derivations.py bible_test.db > ~/r2s1_deriv_diff.txt` —
   goes to the reviewer with the gate results.
7. Gates on bible_test.db, same bar as `/rebuild-words`:
   - strongs_base invariant: `SELECT count(*) FROM words WHERE strongs_base GLOB
     '[0-9]*'` = 0.
   - `health_check.py` — 0 warnings (incl. the abp_surface floor; surface/translit do
     NOT need a re-run — import_tipnr changes numbers, never positions — the floor
     check proves it stayed intact).
   - `compare_words.py bible.db --compare bible_test.db` — every differing row must be
     a PN slot explained by the 11 aliases or their knock-on TIPNR fills; itemized to
     zero unexplained, R-1 style.
   - `build_entity_binding` re-run + the guard trio from R-1 — expected deltas
     itemized (new binds only where an alias surface now resolves; hittites ×13 and
     Pharaoh ×7 stay honestly unbound).
8. Controls — ALL emitted by `audit_two_derivations.py`'s CONTROL PANEL block (JP's
   paste shows named PASS/FAIL lines; no grepping):
   - N1 maacha @ 2Ch 11:21 → H4601 · N2 shetharboznai @ Ezr 5:3 → H8370 ·
     N3 jiphthahel @ Jos 19:14 → H3317 (the known positives — number-only today).
   - N4 NEGATIVE: no 'syrian' word carries the place number H758.
   - N5 NO-CHANGE: abia @ 1Ch 3:10 stays H29 (R-1 shipped entry).
   - B1 BIND-POSITIVE: maacha @ 2Ch 11:21 must now have a rendered entity card
     (binder-side, per the added batch item). B2 BIND-NEGATIVE: 'syrian' must have
     no rendered bind.
   - G1 David @ Mat 1:6 carries a real Greek identity (G1138). G2 the LXX-only pile
     carries the honest lemma-only state (count > 0). G3 the no-number-no-lemma
     bucket is counted, not hidden.
9. Reviewer sees: gate outputs + the two-derivations diff + control results. Receipt
   BEFORE the swap (pasted reviewer text only, per R2-b).
10. Swap (one reversible move): `mv bible.db bible_pre_r2s1_swap.db && mv
    bible_test.db bible.db` → touch wsgi. Backups rotation stands.

## Rollback

Stage 1 rollback = swap the pre-file back (one move). The two side tables are additive;
live code never reads them until stage 2, so even a missed defect in them cannot change
what readers see. Stage 2 (the flip) is a git-revertible code deploy; stage 3 (retire
Hebrew as identity) is its own later rebuild with the same discipline.

## Open items to settle while writing the scripts (not blockers)

- Whether TBESG actually carries every TIPNR G9xxx name number — measured in step 4's
  dry-run report; any gap feeds Q3's lemma-only state and gets counted, not papered.
- Pile U (Group entities for gentilics) is NOT in this run — it needs the entity-model
  work; the killed gentilic pairs wait there.
