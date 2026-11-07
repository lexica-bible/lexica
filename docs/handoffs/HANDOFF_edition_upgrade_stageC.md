# HANDOFF — edition upgrade, PA sequence: stage B done → stage C next (2026-11-02)

**Opening brief for the next session (paste as-is):**
> Lexica, fresh session. Repo lexica-bible/lexica, local C:\Users\JP\projects\bible-db. bible.db is
> PA-only (~/bible-db/bible.db); JP runs PA commands from my drafts; no runnable command until the
> ruling chat clears it. HEAD should be the commit that adds this handoff (`git log -1 --format=%h --
> docs/handoffs/HANDOFF_edition_upgrade_stageC.md`); code = `3f6b4d3c` (`git diff --quiet 3f6b4d3c HEAD -- scripts
> tests` must pass) — confirm first, stop if not. Lane: edition
> upgrade, PA sequence, **stage C next** (the tail on the built copy). Read this handoff in full,
> docs/handoffs/DESIGN_q2_build.md §9 (rulings §9.58–§9.79 are this session's), CHARTER_edition_upgrade.md
> §4.5–§4.10 + §6, docs/claude/ops.md deploy + cert entries, .claude/commands/rebuild-words.md steps 3,
> 8b, 9–9c. Draft commands only, one block at a time, tee'd under ~/edition_upgrade_runs/. Draft the
> stage C outline first and hold it for the ruling chat.

## State at close
- **HEAD** = this handoff's commit; tree clean; PA pulled to the same commit (stage B ran on
  code `3f6b4d3c` — every later commit is docs-only; check with `git diff --quiet 3f6b4d3c HEAD -- scripts tests`).
- **Live `bible.db` untouched since the 10/25 swap** (cert_invariants 7/7 on 11/1). Its file time moves
  with site cache writes — not evidence of a table change (memory `project_db_backups`).
- **`<src>` = `~/bible-db/bible_edupg_test_20261101.db`** — sqlite `.backup` of live 11/1, plus: 23 cured
  correction rows retired (§9.59/§9.60) and 344 EU- rows inserted (§9.76) → abp_corrections
  **active 372 / retired 23 / superseded 6**.
- **`<built>` = `~/bible-db/bible_edupg_test_built_20261102.db`** — stage B output (build + B --apply).
  Built + B applied 11/2 on code `3f6b4d3c` — every figure as expected (see "Stage B" below). NOT yet
  run: import_tipnr / the tail / anything else — the copy is raw build output + B's verse text.
- **Keep:** `~/bible.db.pre-surface-fill-20261025` (the 9a restore's only old-table source until 9c's
  re-freeze passes `--check` against the swapped live), `~/bible-db/bible_pre_trapwire_swap.db` (rollback
  of record; also the §9.78 evidence), `<src>`, `<built>`.
- **Close-out cleanup — DONE 2026-11-07 (JP):** the two `bible_pre_pnstar_*` copies and `bible_test.db`
  deleted (PA quota), with `~/db_evidence/bible_formlane.db` and the orphaned 9/6 formlane backup.

## Rulings this session (DESIGN_q2_build.md §9, one line each)
- §9.58 `pn_binding.rule` blank = `''` (never NULL); the 3 Michaiah rows are NOT declared.
- §9.59 retire set = cured ∩ A-eligible ∩ feed-taken field (23); Strong's rows never; pin = 28 + 344 = **372**.
- §9.60 order: A dry run → SELECT + retire → B dry run.
- §9.61 post-build gate: every retired row's built cell = corrected_value; failing rows print FULL text.
- §9.62 PA figures 29,071 / 1,421 / passdiff 625 are the lane's; the 604 passdiff = follow-up lane.
- §9.63 §9.61 amended: the 5 named prose rows may equal B's feed text (both texts recorded).
- §9.64 declared_deltas contents; built-copy name; mid-run re-pin; §4.8 figures re-declared as one-liners.
- §9.65 R1 (later: no change needed — §9.77).  §9.66 R2 split-merge re-key.  §9.67 R3 lane-3 re-key (Heb 11:24 out).
- §9.68 P5 name census → corrections batch on `<src>`.  §9.69 Sheshach ×2 declared unchanged.
- §9.70 gate B count pins re-declared on the built copy; changing header rows declared by name.
- §9.71 corrections apply at step 7 (Act 7:3 depends on R2) + the sequence.
- §9.72 R2 members, P5 rulings, batch shape; glue census annotated (`…NOTES.md`), not re-frozen.
- §9.73 merge pairs: A keeps the OLD split for the two words (1,578 / 1,380, frozen).
- §9.74 P6 rulings (32 typos, 37 appended glosses, agape → love, Jeroboam II, Deu 32:24); batch 119 cells.
- §9.75 edge split (90, frozen); the 9 punctuation-only misses stay feed.
- §9.76 the 117 near misses stay feed; batch forms; expansion 344 rows; INSERTED 372 / 23 / 6.
- §9.77 re-keys landed: R1 none, R2 18 (+ Eze 20:14), R3 2; Jos 2:4 in place; Rom 9:29 → follow-up lane.
- §9.78 step 1a STALE on 5 slots, G5-explained (10/25 `*`→H moves); stage A passed as ruled.
- §9.79 B's guard allows an active verse-text row only when its source_value is exactly B's text.

## Frozen fixtures this lane (tests/fixtures/edition_upgrade/ unless noted)
- cert_invariants check 4: pin `abp_corrections_active` **51 in code → re-freeze to 372** (member list +
  pin) at stage C, as a scripts-only commit + PA pull, no reload (§9.59/§9.64).
- `merge_pairs_20261102.tsv` (+ .sha256, 3fb43b41…) — the build STOPs on any difference.
- `edge_splits_20261102.tsv` (+ .sha256, 03edab28…) — same.
- `eu_corrections_spec_20261102.tsv` — the 119-cell fix list.
- `eu_batch_rows_20261102.tsv` (+ .sha256, ac9b9e8c…) — the 344 rows inserted on `<src>`.
- `feed_glue_census_20261031.NOTES.md` — annotation only.
- **`declared_deltas.json` — NOT YET WRITTEN** (stage C, before gate 2). Contents per §9.64/§9.69/§9.70:
  words scratch_count 626,309 · verses 31,237 · `abp_surface` + `tipnr_entities` identical ·
  `pn_greek_identity` keys only-in-live 0 / only-in-scratch 0, no key-moves file · `pn_binding` declared
  identical on the FIRST gate run, every differing row brought to JP member by member, file amended,
  gate re-run · Michaiah ×3 OUT · Sheshach ×2 (Jer 51:41 pos 1, Jer 25:26 pos 25) declared UNCHANGED ·
  gate B's four count pins (17/20/94/30) re-declared on the built copy, changing header rows by name
  (predicted member list from P5 + the transplanted name cells — owed before stage C's gate 2).

## PA figures (the lane's)
- A: transplanted **29,071** · strict_fail **1,421** (passdiff 625) · english changed 15,588 · merge
  pairs **1,578 / 1,380** · edge splits **90 / 90** · both frozen lists MATCHES.
- B: written **15,571** · unchanged **13,500** · EU rows matched on written verses **118**.
- Step-5 lists saved as `~/edition_upgrade_runs/step5_{eligible,strict_fail,prose}_20261101.tsv`
  (eligible e540d34d…, strict_fail 1513e235…, prose f2a22ecd…).

## Stage B — DONE 11/2 (logs `stageB_build_20261102.log`, `stageB_Bapply_20261102.log`)
- B1 build: expected `Words inserted: 626,305` · `Verses skipped: 0` · flagged 6,882 · article-slot 923 ·
  PN-star A 1,505 + B 2,552 / 3,161 · both frozen-list MATCHES (build mode) · A's figures above ·
  `.new` renamed to `bible_edupg_test_built_20261102.db` in the same command · eligible + strict_fail
  SAME bytes as step 5. Re-declare one-liners (old vs new): **Split 80 → 84** (runs on the rows after the
  new English goes in — owed to the ruling chat as a one-liner, §9.64 c), **Filled 5 → 5**.
- B2 `--apply` on `<built>`: expected `APPLIED: 15,571` · EU matched 118 · prose list SAME bytes.
- **Actual, B1:** Words inserted 626,305 · Verses skipped 0 · flagged 6,882 · article-slot 923 written / 411
  refusals · PN-star A 1,505 + B 2,552 / 3,161 · transplanted 29,071 · strict_fail 1,421 (passdiff 625) ·
  english changed 15,588 · merge pairs 1,578 / 1,380 · edge splits 90 / 90 · `merge-pair list: MATCHES …
  (1,578 rows)` · `edge-split list: MATCHES … (90 rows)` · Filled 5 · Split 84 · renamed to
  `bible_edupg_test_built_20261102.db` (451,964,928 bytes) · eligible + strict_fail SAME bytes as step 5.
- **Actual, B2:** written 15,571 · unchanged 13,500 · kept old 2,166 · active prose rows on the copy 124 ·
  EU rows matched on written verses 118 / other 0 · `APPLIED: 15,571 verses.text rows written` · prose
  list SAME bytes as step 7.
- **Trap:** the build printed its own "NEXT … swap it in" text, which calls the copy "live". Never run
  it — stage C follows this outline.

## Build outline (stages A–G)
A pre-build ✅ (§9.78) → B build + B apply ✅ (11/2) → **C tail (next)**: finish_rebuild.sh on `<built>` (re-declare
patch counts; 4b applies 6 active + 118 EU prose rows; step 7 applies 22 + EU word rows; §9.59 re-pin
372 mid-run) → gate 1 cert 7/7 → **§9.61/§9.63 retired-row check** → gate 3 v2 (Joh 14:26 clean; STOP for
the §9.52 punct ruling) → D 8b chain (8b.0–8b.3, lane-3 PASS with the R3 re-keys) → gate 2 header gate
`--declared` (write the file first) → E steps 11 → 10 → 9 → 9a (no `--prefill`; reason-6 list to JP) →
9b → v2 again → **9c re-freeze** (staleness §9.78) → F gates 4–7 → G rollback copy + swap + deploy.

## Follow-up lane (not this lane)
604 passdiff (tag placement, §9.62) · the 117 merge-rule near misses (§9.76) · Rom 9:29 (§9.77) ·
versification map Pro 16 / Pro 24 / Jer 10 / Hab 3 (§9 Q7, held on old text) · italic transplant
(§9.44: italic stays OLD) · the feed's Greek column (unused this lane; carries stray notes, e.g. Gen 6:7).
**Doubled words new in the app edition's prose (§9.84, 11/4)** — to the follow-up lane under §9.72, not this build:
the nine slips 2Ki 14:28 "to to" · Deu 24:8 "you you" · Eze 11:12 "you you" · Jdg 20:34 "they they" · Ezr 4:15
"this this" · Est 8:8 "with with" · Joe 2:2 "it it" · Luk 13:28 "there there" · Joh 19:21 "that that". Reviewed and
kept (normal repeats, 14): Exo 18:18, Lev 6:12, Lev 23:21, Deu 9:26, Deu 32:39, 1Sa 3:4, 2Sa 19:4, Pro 29:16, Eze 5:7,
Eze 30:2, Eze 40:4, Dan 8:26, Zec 2:6, Mar 6:16; plus "be be" ×2 (Lev 6:13, 2Ch 34:25), already corrected by the EU batch.

## CC rules banked this session (memory)
- Gate on unchanged code: `git diff --quiet <commit> HEAD -- scripts tests`, never an exact HEAD.
- No pushes while a gated block is waiting for JP.
- A conditional clearance is ONE chained block that greps the exact gate line (`feedback_conditional_clearance_chained`).
- "Local fingerprint" = before/after `--dry-run-nodb`; lists byte-identical; only intended lines move (`feedback_local_fingerprint`).
- Copies keep a receipted name: a build copy contains `_test` (or starts `bible_pre_`) so the nightly skips it;
  rename a `.new` in the SAME command as the build (8/5 vanish defense).
- bible.db file time ≠ table change (site cache writes) — cert is the evidence (`project_db_backups`).

## Gate state
Nothing past stage B is cleared. Stage C is drafted by the next session and held for the ruling chat.
