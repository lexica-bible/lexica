# HANDOFF — rebuild-trap fix → next lane: build G1–G3

Written 2026-10-26 at session close. The governing record is
`docs/handoffs/CHARTER_rebuild_trap_fix.md` (gates G0–G5, rulings quoted, §6 dry run, §7 G4 test);
the code-cited census is `docs/handoffs/CENSUS_rebuild_trap.md`. Read the charter in full first.

## Where it stands
- **The trap:** `/rebuild-words` step 9 runs `build_abp_surface.py`, which DROPs `abp_surface`; no
  builder re-creates the 4,411-row 2026-10-25 fill; the health floor (389,244) sits below the pre-fill
  391,130, so the loss is silent. Step 9 now runs on the rebuilt COPY before the swap (charter §9;
  the §1 "live, after the swap" placement is superseded).
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

## UPDATE 2026-10-26 (live run) — REBUILD SWAPPED LIVE; the fill survived. Receipts: charter §10
JP ran `RUN_rebuild_trap_live.md` A–K on PA; reviewer cleared A–I and the swap. Live now = the rebuilt
db: 395,003 surface rows (restored table = old live row for row), floor GREEN, invariants 0, site
serving. Rollback = `~/bible-db/bible_pre_trapwire_swap.db` (one move back). Rulings: header gate A/B
ABORT overridden for this run (attributed) · Sheshach follows the page. **Owed next (not run):**
checklist steps 7 (served spot-checks), 10 (two-ending regen) and 11 (`build_rendering_norm.py`, held
item 9 — live-relevant now). `~/rekey/pre_rebuild.db` (the pre-run copy of live) can go after the
receipts are filed and a nightly postdates the swap — a separate step, never in a line naming a file
still in use.

## UPDATE 2026-10-26 (wiring lane) — PATH A BUILT; next = JP runs the live sheet (when he wants a rebuild)
Step 0 answer: **step 9 reads nothing that exists only on live — sequencing only** (receipt + history
verbatim in charter **§9**). So, by JP's ruling, Path A: step 9, the restore (9a) and the floor +
oracle (9b) all run on the rebuilt COPY before the swap; the swap is the only live write and live is
never served without the fill. The restore keeps its live refusal. New step **1a**
`snapshot_surface_fill.py --check` proves the frozen file still matches a fresh copy of live
(`SNAPSHOT CURRENT`) or stops (`STALE SNAPSHOT`, never overwrites). Checklist reordered (RUN ORDER
line; numbers kept as labels). Tests 22 + 7 green (+7 new check-mode cases).
**Next:** the live run sheet `docs/handoffs/RUN_rebuild_trap_live.md` (same-code rebuild; hard stop
after block I for the verdict; block J = the swap). Nothing was run on PA in this lane.
**Before the NEXT live rebuild, also look at:** step 11 has the old step-9 shape (held item 9).

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
1. ~~**21 Greek headers + Sheshach**~~ — **CLOSED 2026-10-26 (live rebuild):** the 21 rows shipped at
   the swap; reviewer ruled Sheshach "header follows the page" (Σεσάκ Jer 51:41 · Σησάχ Jer 25:26).
11. **`surface` vs `lemma-only` label (NEW, reviewer 10/26)** — the 2 Sheshach rows went `surface` →
   `lemma-only` at the swap (accepted). Trace what the label changes on the card, and whether a header
   that matches the page should carry `surface`.
12. **Header gate A/B re-scope (NEW, reviewer 10/26)** — `gate_greek_header.py` A/B were built for the
   7/30 header-only lane and abort on any full rebuild (binding relabels, the 21 rows, landing pins).
   ABORT was overridden for the 10/26 run only; re-scope before the next rebuild.
13. **Small follow-ups from the live run** — `health_check.py` waits only 5 s, so it reports false
   "locked" errors in the minutes after a deploy (site workers' warm-up writes the AI cache) · the
   build's closing text calls its source "live" when the source is a copy (its printed swap command
   would move the copy and reload the site — never run it) · two old `bible_pre_pnstar_*` rollback
   copies (~824 MB) beyond ops.md rule 1.
2. **Header landing `->surface` 461 vs its receipt's 451** — 10 rows unattributed against
   `HANDOFF_gateB_enumeration.md`; class totals reconcile exactly.
3. ~~**Fresh-copy proof of gapfix entries 5–6**~~ — **CLOSED 2026-10-26:** gapfix (6,0,0) on built3, and
   the live rebuild's block I read `bracket_id` 0 vs live.
4. **8b.3 ordering** — the identity build reads `abp_surface` before step 9 rebuilds it. Census still
   owed; not touched by the G1–G3 lane.
6. ~~**Live wiring decision**~~ — **RESOLVED 2026-10-26 (charter §9, Path A):** there is no gap; step 9
   and the restore run on the copy before the swap. The live refusal stays.
9. **Step 11 has the old step-9 shape (flagged in the wiring lane) — NOW LIVE-RELEVANT:** the 10/26
   swap happened and steps 10 + 11 have NOT run. The build never writes `words.english_head_norm`
   (`build_words_from_abp.py:2154-2157`) and the finder only checks the column exists
   (`views_lexicon.py:100-108`), so until step 11 runs the ABP English finder may fold on blank values.
   Not measured on PA. Same Step-0 question (any live-only input?) before the next rebuild; if none, it
   moves onto the copy.
10. **AI caches live in bible.db (RECORD)** — rows written between the copy and the swap are dropped by
   the swap (they redraw on the next ask). The live sheet records the count before the swap.
7. **Snapshot staleness (NEW)** — a restore that MOVES slots makes the frozen file stale for the next
   rebuild; a re-freeze needs a "before" side other than the 10/25 pre-fill copy. Gates the
   edition-upgrade lane (already gated on this landing).
8. **Reason 5 unreachable** under the current keys (charter §6) — unchanged, recorded.
5. **G5 record (not a block)** — JP ruled the 9/6 class basis correct; at any rebuild swap expect 519
   xref rows (class only) + 501 PN `strongs_base` slots to change. Record the counts.

## Files that stay on PA (do not delete)
(Revised 2026-10-26, reviewer-logged.) `~/rekey/` = logs + dry-run TSVs ONLY (every old/built pair
deleted; disk 6.3G by `du` / ~7.8 GB by PA's meter — PA reads ~1.5 GB over `du`, go by the dashboard) ·
`~/bible.db.pre-surface-fill-20261025` (the only pre-fill copy AND the snapshot's "before" side — it
stays past the nightly-backup condition until a re-freeze exists) · `~/bible.db.pre-xref-fix-20261024` ·
`~/bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv` + `.sha256` (git-ignored; a
second copy in the local checkout; sha256 `d9435bde…` pinned in `restore_surface_fill.py` at `0c2e6cfb`) ·
`~/abp_surface_fill_dryrun.csv` (the approved fill CSV — a G0 input of step 1a; added to this list in
the wiring lane). Untracked on PA: `docs/tickets/greek_header_split.txt` (a dry-run
receipt — leave, never commit). Note: `build_entity_binding.py` dry runs rewrite two TRACKED files
(`scripts/pn_binding_hot.txt`, `pn_binding_numonly.txt`) — `git checkout --` them after a test run.
