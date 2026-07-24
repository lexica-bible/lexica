# PLAN — R-2 stage 1: Greek identity ADDED ALONGSIDE (Hebrew stays authoritative)

Drafted 2026-07-24 under the five approved rulings (HANDOFF_r2_greek_names.md) and the
reviewer's stage-1 go. Charter: purely ADDITIVE — after this run every reader, join, and
count behaves byte-for-byte as before; the only new things are side tables and audit
reports. The flip (stage 2) is a later code deploy; nothing here is user-visible.

## What rides this run (batch inventory)

1. **Variant map +11** (committed `59a2d78`, hand-checked, decision lines recorded) —
   picked up automatically by the import_tipnr re-run.
2. **STEP extended Greek lexicon import** (Q1: yes, license CLEAR — CC BY 4.0, credit
   already in CREDITS.md). New side table `step_lexicon` built from the same TBESG file
   `build_word_gloss.py` already downloads (reuse its `parse_tbesg`), but keeping the
   full entry per extended G-number: number, Greek lemma, transliteration, brief gloss.
   New table = the Q1-ruled checkpoint; no existing table touched.
3. **Greek identity side table** `pn_greek_identity`, keyed by verse+position for every
   ABP proper-noun word (Q2's side-table ruling applied to stage 1's direction too).
   Per word, layered per the design: (a) real G-number if the ABP text carries one on
   the name, (b) TIPNR's Greek number for the bound entity (renderable once
   `step_lexicon` exists), (c) otherwise lemma-only with an honest empty number
   (Q3's card state — wording lands at stage 2, the STATE is stored now).
   Also snapshots the current Hebrew `strongs_base` per word so the flip's cross-ref
   is frozen at build time.
4. **Two-derivations audit** — the ruled instrument: per entity, occurrence counts
   keyed the old way (Hebrew `strongs_base`) vs the new way (Greek identity). The diff
   report goes to the reviewer BEFORE any swap. Disagreements are resolved against
   TIPNR/ABP, never by preference.
5. **Post-run diagnostic (reviewer-folded):** fresh number-only dump; specifically
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

Step 0 — scripts land in the repo first (to be written next, each reviewed before
commit): `scripts/import_step_lexicon.py`, `scripts/build_pn_greek_identity.py`,
`scripts/audit_two_derivations.py`. All three take the db path as the first argument
and default to dry-run; writes need `--apply`.

1. Copies: `cp ~/bible-db/bible.db ~/bible-db/bible_pre_r2s1_$(date +%F).db`
   then `cp ~/bible-db/bible.db ~/bible-db/bible_test.db`.
2. Roster gate (see above): CLEAN or stop.
3. `python3 scripts/import_tipnr.py bible_test.db --dry-run` → paste the summary.
   Expected movement vs R-1: ONLY the 11 alias surfaces (matched-count rises by their
   row counts; nothing else shifts). Then the real run without `--dry-run`.
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
8. Controls (every detector fires on a known positive before a zero is trusted):
   - maacha @ 2Ch 11:21 — currently number-only; must resolve to H4601.
   - shetharboznai @ Ezr 5:3 — must resolve to H8370.
   - jiphthahel @ Jos 19:14 — must resolve to H3317.
   - NEGATIVE control: syrian (killed gentilic) must NOT gain the place's H758.
   - NO-CHANGE control: abia @ 1Ch 3:10 (R-1 shipped entry) — identical before/after.
   - pn_greek_identity spot: David @ Mat 1:6 must carry a real Greek identity
     (the design's marquee case); one LXX-only form (pile B) must carry the
     lemma-only state, not a fabricated number.
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
