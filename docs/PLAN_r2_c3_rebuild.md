# PLAN — R-2 candidate 3: Hebrew retirement rebuild (run plan, stage-1 pattern)

Drafted 2026-07-25 under the frozen candidate-3 charter (docs/PLAN_r2_stage3.md)
and wave receipt W1-C3 (serving code live-dormant at 4dac41c7 — the swap alone
activates it, no deploy gap). Declared expectations are stated BEFORE the trial;
any run result off-expectation stops the lane until explained.

## DEVIATION FOR RULING (one item, recommendation attached)

The charter names `import_tipnr.py:719` as the rewrite site. Drafting the run
surfaced a cleaner shape: **nothing in import_tipnr's inputs changed since
stage 1** (no TIPNR.txt edit, no parser edit, no words rebuild — current words
already carry its output), so re-running it does no new work and editing it
puts the roster-frozen importer in play for no gain. *Recommendation:* the
rewrite is a NEW dedicated builder `scripts/retire_hebrew_identity.py` that
runs AFTER the gates, reading the stage-1 `pn_greek_identity` classes (the
write-set's own definition) to (a) rewrite `words.strongs_base` per the class
table and (b) create + fill `pn_hebrew_xref`. import_tipnr is not edited and
does not run; the roster gate still runs as the standing ritual (expected
CLEAN — trivially, since the importer is untouched). Trial-then-apply binds on
the new builder + the two edited builders below exactly as it would have on
import_tipnr. The charter's intent (one auditable rewrite site, gated) is
kept; only the file named changes. Reviewer rules before any script is built.

## JP CHECKPOINT — the new table (open; clears at JP's word on this DDL)

One new table in bible.db, created by the retirement builder on the TEST copy
first, live only at the swap:

    CREATE TABLE pn_hebrew_xref (
        verse_id    INTEGER NOT NULL,
        position    INTEGER NOT NULL,
        hebrew_base TEXT,              -- the moved Hebrew number; NULL (declared,
                                       -- never '') for the 3,518 always-Greek
                                       -- abp-tag rows, which never had one
        class       TEXT NOT NULL,     -- abp-tag | tipnr | lemma-only | none.
                                       -- 'none' IS the machine-visible kept-Hebrew
                                       -- exception (C3-Q1); retired by the future
                                       -- gentilic/people-class Greek backfill
                                       -- candidate (the named consumer)
        PRIMARY KEY (verse_id, position)
    );
    CREATE INDEX idx_pnx_heb ON pn_hebrew_xref(hebrew_base);

Same shape the reviewer ruled and the locked test's `_retire` fixture carries.
The rebuild receipt must cite JP's OK.

## What rides this run (inventory)

1. **`scripts/retire_hebrew_identity.py`** (new, pending the deviation ruling)
   — dry-run default, `--apply` to write; prints the per-class rewrite counts
   and refuses to run if `pn_greek_identity` is absent or its class split
   differs from the declared expectations below.
2. **`scripts/build_pn_greek_identity.py` edit** — re-run AFTER the rewrite
   must source `hebrew_base` from `pn_hebrew_xref` (the Q2 home), not from the
   now-rewritten column; classification of abp-tag likewise guarded (a
   rewritten G9xxx row must not be misread as native abp-tag — class comes
   from the xref, which is authoritative post-rewrite).
3. **`entity_resolution.py` / binder check** — the binder's number-guard
   compares a word's stored number to the entity's own number set. Entity
   bases already include Greek sub-record numbers (stage-1 fact: the identity
   builder read them from `er.parse_tipnr`). Expectation declared below; if
   binds floor in the trial, the fix is extending `tipnr_entities.bases`, not
   loosening the guard.
4. **No words rebuild** (`build_words_from_abp.py` does NOT run), no
   import_tipnr run, KJV/BSB/heb.db untouched (Q4).

## Declared expectations (checked in the trial, every one, no sampling)

- Roster gate: CLEAN (baseline 4,331 exact) — importer untouched, any delta
  is unexplained and STOPS the run.
- Rewrite counts, exact: abp-tag 3,518 rows byte-unchanged (proven by the
  diff, not assumed) · tipnr 10,731 → the served Greek number · lemma-only
  14,850 → `'*'` · none 3,380 keep Hebrew, untouched bytes.
- `pn_hebrew_xref`: exactly 32,479 rows; hebrew_base NULL on exactly the
  abp-tag 3,518; class split = the stage-1 split exactly.
- GLOB invariant: `SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'`
  = 0 (G9xxx passes — starts with 'G').
- compare_words vs the pre-copy: exactly 25,581 changed rows
  (10,731 + 14,850), every one itemized to its class, zero unexplained.
- Unfindability gate (G3 condition 1, mandatory): the 14,850 enumerated
  BEFORE (Hebrew-keyed in words) and AFTER (xref home + identity lemma) —
  zero findable-before/unfindable-after. Detector control-tested on a known
  positive first (certification rule).
- Two-derivations audit re-run: control panel all PASS.
- Entity binding: render/hot/numonly counts equal the live baseline
  (14,830 / 68 / 885) or every delta itemized to a named cause.
- health_check + cert_invariants: PASS.
- The wave's locked test run against the TRIAL DB shape stays green.

## Run shape (all commands JP's, on PA; dry-run before every write)

1. Copies: `cp bible.db bible_pre_r2c3_$(date +%F).db` + `cp bible.db bible_test.db`
   (backup retention: the pre-rebuild known-good is KEPT past the swap).
2. Roster gate → CLEAN or stop.
3. `retire_hebrew_identity.py bible_test.db` (dry-run) → paste counts →
   expectations match → `--apply`.
4. `build_pn_greek_identity.py bible_test.db --apply` (Q2-sourced re-run).
5. `build_entity_binding.py bible_test.db --apply` after its own dry-run.
6. Gates, in order: GLOB · compare_words itemized · unfindability gate ·
   two-derivations · health_check · cert_invariants.
7. Full evidence bundle → reviewer receipt (cites JP's table OK) → swap
   (one reversible move; serving code activates itself) → dashboard Reload +
   5× sweep anyway (workers hold open db handles) → live checks → G5
   re-receipt of both flips + the switch-semantics record.

## G5 reminder (rides after the swap)

READER_GREEK_FLIPS OFF no longer means Hebrew-everywhere — expected, recorded,
not a defect. Both flips re-receipted against the rewritten tables.
