# HANDOFF — lane ③ hand-repair session (71 candidates + Mat 27:26)

> **CLOSED 2026-08-07 — lane executed in full, 72/72 dispositioned, reviewer
> signed off.** Ledger + re-run order: `docs/audits/LANE3_b2_dispositions.md`
> ("REPAIR LEDGER"). Do not re-open; this file is history only.

Written 2026-08-05 at the ②-ride wrap. The ride is CLOSED (pin held ×2, swapped, live,
healthy) — do NOT re-open it. This session is the separate hand lane it left behind.

## CC OPENER (paste to start the next session)

> Read CLAUDE.md, then docs/handoffs/HANDOFF_lane3_hand_repairs.md. You're running the
> lane-③ hand-repair session: the 71 adjudicated repair candidates from
> docs/audits/LANE3_b2_dispositions.md (verbatim rows + per-row source evidence beside
> it), plus Mat 27:26 'scourging' (the A/unattested flagship refusal, same hand lane).
> Every repair is hand-per-row and JP-checkpointed: propose the exact cell edits per
> verse with the source line quoted (abp_texts is diagnosis-grade; anything byte-exact
> comes from a PA dump of the live built state), dry-run before any --apply, reviewer
> verdict-gated. Rulings already made: possessive wording keeps the apostrophe-s as
> printed; Gen 35:18 Ben-oni is a JP-ruled artifact (nothing to move); the 29 artifacts
> in the dispositions file are CLOSED. Repairs land as a re-runnable patch in the
> rebuild path (split_merge_fixes precedent — the splitter-B rules), NEVER a loosening
> of the pass's evidence gates. Traps: the words table is live — writes are
> JP-run-on-PA only, one verse at a time is fine; positions are the LIVE table's, not
> the plan's; after any batch, the member checker + the render-modeling lister
> (scripts/list_split_merge_skips.py display_seq) adjudicate by RENDERED text, never
> the data-layout scanner.

## REVIEWER PROMPT (paste to open the review thread)

> You're reviewing the Lexica lane-③ hand-repair session. Context: the PN-star pass
> shipped 2026-08-05 (TICKET_pn_star_fix.md, ride CLOSED); its typed refusals left a
> hand lane — 71 adjudicated repair candidates (docs/audits/LANE3_b2_dispositions.md:
> gentilic 22 · roster-silent name 41 · possessive 8) plus Mat 27:26 (rare-verb
> A/unattested; lexicon-fallback already REJECTED by receipt — repair is per-row
> evidence, not a rule change). Standard: every repair proposed with the quoted source
> line, dry-run pasted, your verdict before apply; member-level always; no evidence-gate
> loosening ever; the render-modeling lister is the display oracle (the data-layout
> scanner is banned as display evidence — hard trap in the ticket). Batches are fine
> but each row is individually adjudicated (splitter-B precedent). JP checkpoints:
> commands, dry-run pastes, ship notice.

## STATE (don't re-derive)

- Live is the ②-ride build: 626,309 words, pin A 1,505 + B 2,552 / 3,161 typed served.
- Rollbacks: `bible_pre_pnstar_20260803.db` (pre-build) + `bible_pre_pnstar_swap_20260805.db`
  (pre-swap). Delete NOTHING until a clean nightly postdates 2026-08-05 23:26 UTC.
- Repair mechanics available: the pass's write shape (2-slot bracket, greek_pos by
  English order) is the house pattern; a hand repair mimics it per row.
- After repairs ship: re-run build_abp_surface + both backfills + translit if any
  positions/text moved (floor 389,244), and the fixed verses re-read in the app.
- Other open lanes (NOT this session): geometry-aware unfindability mode (owed before
  any future slot-moving ride) · ⑤-family bracketed rows (A 1,324 + B 18 + the 38) ·
  /consolidate on TODO.md.
