# HANDOFF — rebuild-trap fix → next lane: build G1–G3

Written 2026-10-26 at session close. The governing record is
`docs/handoffs/CHARTER_rebuild_trap_fix.md` (gates G0–G5, rulings quoted, §6 dry run, §7 G4 test);
the code-cited census is `docs/handoffs/CENSUS_rebuild_trap.md`. Read the charter in full first.

## Where it stands
- **The trap:** `/rebuild-words` step 9 runs `build_abp_surface.py`, which DROPs `abp_surface`; no
  builder re-creates the 4,411-row 2026-10-25 fill; the health floor (389,244) sits below the pre-fill
  391,130, so the loss is silent. Step 9 runs on the LIVE file after the swap (settled, charter §1).
- **G4 PASSED on PA 2026-10-26** — the lane-3 hand repairs now ride the rebuild as checklist step
  **8b.2a** (`scripts/lane3_rebuild_step.py`; after 8b.2, before 8b.3). Full run on a fresh live copy:
  words english/english_head/greek_pos/strongs/is_pn = live exactly; re-key dry run placed 4,411 of
  4,411 fill rows, 0 unplaced, all 3,873 inserts. Every other difference attributed row by row (§7).
- **Re-key method RULED** (charter §3): key 2 (verse + ordinal of the full strongs) primary, key 1
  (verse + strongs + English) cross-check; agree-strong or agree-weak (key 1 several, key 2's among
  them) = placed. On a same-code rebuild nothing moves; the keys are only really exercised by the
  English-line edition upgrade. The Lexicon "third witness" cannot fire under these keys (§6).
- **Declared figures re-declared this session** (all were stale): build split 2,436 → 80 and
  import_tipnr matched 31,392 → 31,649 (checklist); `restore_frozen_pn.py` EXPECT 6 → 8 (the full
  2Sa 18 Cushi set); `retire_hebrew_identity.py` class split → the 9/6 figures. Receipts in the code.

## UPDATE 2026-10-26 (later) — COPY DRY RUN PASSED; next = wire the restore onto live's step 9
JP ran the whole RUN sheet on `~/rekey/old3.db` → `built3.db`: every figure = the pre-registered one
(receipts + verdict in charter §8). G1 395,003 exactly · G2 4,411 placed / 0 unplaced · G3 floor red
3,873 on the pre-fill copy and the fill-less rebuild, green 0 on the restored copy · restored table =
live's row for row (`0|0`) · gapfix (6,0,0) fresh-copy proof done · G5 519 / 21 / 501 recorded.
Snapshot sha256 pinned in `restore_surface_fill.py`; second copy local (git-ignored).
**Next lane:** let `restore_surface_fill.py` run on live at `/rebuild-words` step 9 (after both
backfills + translit) — remove the live refusal by ruling, put the snapshot step before the swap in
the checklist, and decide what live serves between the step-9 drop and the restore (charter §1
consequence). Only then may a rebuilt db be swapped. Disk: `~/rekey/old3.db` + `built3.db` DELETED
2026-10-26 after the receipts were recorded (`du -sh ~` 6.3G after; PA's dashboard reads ~1.5 GB
over `du`). `~/rekey/` now holds logs + TSVs only; the next lane takes fresh copies.

## UPDATE 2026-10-26 (second session) — G1–G3 BUILT; the copy dry run is owed
Built + locally tested, NOT yet run on PA (charter **§8** has the design calls; run sheet
`docs/handoffs/RUN_rebuild_trap_G1G3.md` has every command with its expected figure):
`scripts/snapshot_surface_fill.py` (freeze the 4,411-row diff + each slot's old words row + key-2
ordinal; checksum beside it) · `scripts/restore_surface_fill.py` (re-key with the shared key rules,
reasons 3/4/5 at the new slot, G1a 391,130 → G1 395,003 exactly, all or nothing; refuses live) ·
health floor 389,244 → **395,003** · `tests/test_surface_fill_restore.py` (14 cases, both lists).
**Next step: JP runs the RUN sheet on fresh copies (`~/rekey/old3.db` → `built3.db`), pastes the
tails; read each against the sheet's expected figure (verdict); then pin the snapshot's sha256 in
`restore_surface_fill.py` (`SNAPSHOT_SHA256`), then a separate change wires the restore onto live's
step 9.** The snapshot file is git-ignored (ABP text, public repo) — after step K it exists on PA and
locally only; never delete either copy.

## (superseded) NEXT LANE — build the trap fix (charter G1–G3; G0 + G4 already defined/passed)
Snapshot the fill (the 4,411-row diff live − `~/bible.db.pre-surface-fill-20261025`, plus each slot's
old words row) BEFORE step 9 → step 9 rebuild + both backfills → re-key with `dryrun_rekey_fill.py`'s
keys → re-apply (538 updates only where the builder value equals the recorded old form; 3,873 inserts
only into empty slots; translit from the new slot's lemma) → **G1 table = 395,003 exactly** (builder
chain must first total 391,130) · **G2 every slot placed or unplaced with a closed-list reason** ·
**G3 health floor = 395,003, red on the pre-fill copy first**. Reasons 3/4 (need step-9 output) are
first evaluated there. Copy-first; dry run → verdict → apply, as always.

## Held items (none blocks the build; each has a TODO entry)
1. **21 Greek headers + Sheshach** — live's header table predates the 10/25 fill; any header rebuild
   changes 21 rows (mostly gains). Sheshach gets two spellings (Σεσάκ / Σησάχ) — content ruling first.
2. **Header landing `->surface` 461 vs its receipt's 451** — 10 rows unattributed against
   `HANDOFF_gateB_enumeration.md`; class totals reconcile exactly.
3. **Fresh-copy proof of gapfix entries 5–6** (2Sa 18:31 p7, 18:32 p15) — added after the G4 run;
   built2 already had them patched, so prove on the next fresh copy (expect `gapfix (6, 0, 0)`).
4. **8b.3 ordering** — the identity build reads `abp_surface` before step 9 rebuilds it.
5. **G5 record (not a block)** — JP ruled the 9/6 class basis correct; at any rebuild swap expect 519
   xref rows (class only) + 501 PN `strongs_base` slots to change. Record the counts.

## Files that stay on PA (do not delete)
`~/rekey/` logs + TSVs (the two older test pairs old/built + old2/built2 were DELETED 2026-10-26 for
disk: PA's dashboard read 9.9 of 10 GB while `du -sh ~` read 8.4G, and the G1–G3 build hit "disk I/O
error"; both pairs were superseded, results recorded in §6/§7; old3/built3 = the G1–G3 pair) ·
`~/bible.db.pre-surface-fill-20261025` (the only pre-fill copy — the snapshot's "before" side) ·
`~/bible.db.pre-xref-fix-20261024`. Untracked on PA: `docs/tickets/greek_header_split.txt` (a dry-run
receipt — leave, never commit). Note: `build_entity_binding.py` dry runs rewrite two TRACKED files
(`scripts/pn_binding_hot.txt`, `pn_binding_numonly.txt`) — `git checkout --` them after a test run.
