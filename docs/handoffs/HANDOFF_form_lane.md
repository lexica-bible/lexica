# HANDOFF — the form-table lane (charter to write, not run)

Banked 2026-08-09, close of the folding session. **Everything here is what was measured that
day. A prompt is a memory the moment it's written — re-verify against the repo and PA before
building on any number.** Standing rules are deliberately NOT restated: read `CLAUDE.md`, then
`docs/claude/word-study.md`, then memory `project_greek_header_fold` and the tripwire indexes
in `feedback_audit_tools_must_fail` + `feedback_verify_before_claiming`.

## The one-line job
Write the charter for rebuilding the printed-form table so name slots regain their forms.
**Write it. Do not run it.** Everything downstream is already proven and waiting.

## Why this is first (the dependency, not a preference)
Order is **form lane → header repair → batch 3 (galilee) → ABP-tab routing.** Each is blocked
by the one before it, and both of the last two are already DONE-and-parked:
- **Header repair: PROVEN.** Rebuilt on a copy 2026-08-09 — gate C fully green, including the
  three names that caught the regression (zion 168/168, hadad 9/12 with 0 English-despite-page,
  abner). It fails only on gate B, and only because the form table underneath it is incomplete.
- **Batch 3 galilee: PROVEN.** Landed exactly 73 rows, glued exactly 30, in that same build.
  Committed at `7ed55e38`; record `docs/tickets/greek_header_batch3.md`.

So the ONLY thing standing between today and a green gate is the form table.

## What is actually broken (read, not inferred — but re-read it)
The 8/8 wordpos apply re-ran the header build BEFORE rebuilding the form table
(`/rebuild-words` step 8.3 comes before step 9 — the ordering is the defect, and a gate step
has since been written into 8.3). Name slots moved; the form table's name-slot rows stayed at
the old slot numbers.
- Name slots with **no printed form: 2,361 (pre-8/5) → 2,528 (live), +167.**
- A header rebuild on today's inputs **blanks 256 rows, 172 of them currently correct.**
- **`backfill_pn_surface.py` cannot fix it: dry-run adds 0 rows**, 2,543 refusals. It only
  reads scrape rows with a BLANK Strong's number — numbered names (Jesus G2424, Paul, Peter)
  were never in its reach. Their forms come from `build_abp_surface.py`, which rebuilds the
  whole table. **That is why this is a rebuild-class lane and not a re-run.**

## Charter shape (proposed — the next session's job is to WRITE this, with JP/reviewer sign-off)
1. Full `build_abp_surface.py` rebuild on a COPY (never live), `--bh ~/bible-db/bh_scrape.db`.
2. Then `backfill_abp_surface.py` AND `backfill_pn_surface.py` (the script's own docstring says
   both are required after a full rebuild), then `build_abp_translit.py` for the new rows.
3. Gate: `audit_surface_coverage.py`. Acceptance floor = name slots with no form back to
   **≤ 2,361**, and `abp_surface` total not below the **389,244** floor (memory
   `project_bsb_words` — a rebuild that skips a backfill trips this).
4. Checkpoint → swap → then the header lane re-runs UNCHANGED against the repaired table.

**Gate A is NOT re-scoped** (reviewer ruling 2026-08-09). "Form table untouched" is what made
every finding in that session trustworthy; the form lane carries its own gate instead.

## Then, in order
- **Header repair:** re-run `build_pn_greek_identity.py <copy> --apply` + `gate_greek_header.py
  <live> <copy>`. Full acceptance: zion 168/168 · hadad ≥9/12 · **4,326 folded rows / 1,718
  names** · glued **= 30 exactly** (not ≤30 — the 30 are legitimate; their disappearance is
  itself a defect) · gate C green · the 114 stale rows cleared.
- **Batch 3:** galilee must still change exactly 73. It rides the same rebuild — the hand-table
  row is already on PA.
- **Routing:** only then does the ABP tab open a name's occurrences.

## STOP conditions
- Any write to `words`, `pn_greek_identity`, `abp_surface`, or a binding table → checkpoint
  first, on a copy, gate before swap.
- The form rebuild changes row counts outside the ruled shape → stop, enumerate, don't push.
- **Live's headers are NOT a restore set.** They were read from the stale form table mid-chain;
  the clean-looking ones are right by luck. Evidence only, with its own status header:
  `docs/tickets/receipt_headers_no_source_20260809.txt` (417 rows). Restoring them wholesale
  would launder a bad read into the record.

## Numbers left OPEN — pin these during form-lane verification, don't let them close quietly
- **218 (gate B violations) vs 256 (enumeration).** The gate allows 40 as gentilic drops → 258,
  two rows over. Not the same set; the 2 are unpinned.
- **Folded rows came out 4,408** against the expected 4,326 + 73 = **4,399. +9 unexplained.**
- **~85 blanked rows whose slot was already uncovered on 8/5** yet live still heads them. Live's
  header table predates both surviving backups, so no file on hand explains them.

## Filed follow-ons (do not fold into this lane)
- **871 names scattered across more than one form** — the real class size. This session's
  process (page receipts → hand table → gate pin → decomposition proof) is the template.
- **The particle pair + Nephedor:** Act 12:19 `Ηρώδης δε` ("And Herod"), Act 13:1 `Μαναήν τε`,
  Jos 12:23 `του Ναφαθδώρ` (article, not name). The first two come from the FORM TABLE, so
  they survive a header rebuild by design — that's why they're parked and named, not absorbed.
- **The 27 legitimate compound names** go into the gate as a pinned allowlist with their
  verses, or every future run re-argues them. Pin `Βαρώθ␣␣Χαμααμ` (Jer 41:17) with its exact
  bytes — it carries TWO non-breaking spaces.

## For the reviewer
The session's rulings that should carry forward: gate A stays hard · a control run is live
against itself · one clean page receipt admits a headword · a shape detector names a class, so
split it before designing the fix · the acceptance number stays 30 exactly · anything other
than the pre-registered figure is a STOP with the deviation enumerated. What worked was
posting the expected picture beside every command before it ran — three wrong framings died
that way, two of them mine.
