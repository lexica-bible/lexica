# HANDOFF — edition upgrade, gate 2 (written 2026-11-07)

Successor to `HANDOFF_edition_upgrade_stageD_rekey.md` (stage D is done through 8b.3). Standing rules and the
follow-up list in `HANDOFF_edition_upgrade_stageC_repin.md` still apply. Every block, result and ruling:
`DRAFT_stageC_outline.md` (stage D sections onward); rulings only in `DESIGN_q2_build.md` §9 (sole register,
latest §9.98).

## State (11/7, end)
- **Built** `~/bible-db/bible_edupg_test_built_20261102.db` = **8b.0 + REKEY + 8b.1 + §9.96 restore + 8b.2 + 8b.2a +
  8b.3** (8B3c applied; after-check re-run by 8B3CX: CHECK OK on every table). words 626,309 (digest 2b23f546),
  abp_surface 395,003 (623cca1f), identity 32,478 at 3,671 / 10,246 / 12,216 / 4,382 / 1,963, pn_binding 15,426
  (render 15,358 + HOT 68), pn_slot_binding 102.
- **src** `~/bible-db/bible_edupg_test_20261101.db`. **Rollbacks (keep until the swap):**
  `bible_edupg_test_built_pre_8b_20261106.db` (built before 8b.0), `bible_edupg_test_built_pre_digits_20261105.db`.
- **Code REF `1da5abf0`** (scripts/tests; PA pulled). Later commits are docs/config only (no pull needed for a
  block gated on `1da5abf0`). `scripts/pn_slot_rulings.tsv`: 4 Israel-king slots (2Ki 8:16@4, 8:25@4, 8:29@4,
  8:29@38) now keyed 'joram' (§9.98 a).
- **Reviewer subagent** now runs on the session's model (`model:` line removed, `395c52bd`); still clears read-only
  blocks and re-runs of ruled gates only (§9.90); a CLEAR is never a receipt.

## Gate 2's declared inputs (all on PA, run folders under `~/edition_upgrade_runs/`)
- **Identity:** `pn8b3_20261107/identity_delta.tsv` — the 58 rows (sha `62a99ffe59658f46…`, 59 lines). All 58 feed
  `gate_b.changed_rows` (§9.92 G3 shape `{book, chapter, verse, position, name}`, generated from the file, never
  typed; name = the file's `label_norm`). Gate B fails any greek_strongs change except None → G with source tipnr
  (`gate_greek_header.py:349-356`) — the 10 in this list are all that kind. Gate B's four pins come only from the
  first run's output.
- **pn_binding:** `pn8b3c_20261107/pn_binding_delta_after.tsv` — 160 rows (added 70 / removed 90, all render=1);
  replaces `pn_binding {"identical": true}` in `tests/fixtures/edition_upgrade/declared_deltas.json` (§9.98 b).
- **Slot table:** the 4 name changes jehoram → joram (every other column equal).
- **Header receipt of record:** `pn8b3c_20261107/greek_header_split_dry.txt` (2,606 lines, sha `59dac6f7…`). The
  apply copy and PA's repo receipt differ only in the order of tied forms on 9 lines (RDIFF8B3C: fields 1–5 differ
  on 0 lines).

## Next session — in this order, each block through the reviewer first
1. **Gate 2 dump (read-only):** `python3 scripts/eu_pn_binding_diff.py <src> <built>` — every differing pn_binding
   row, both copies' values (§9.92 G1). Compare its row set with `pn_binding_delta_after.tsv` (that file is built
   before → after; the dump is src → built — expect the same 160 plus any src/built differences that predate 8b.3,
   if any; read, don't assume).
2. **First gate 2 run (read-only):** `python3 scripts/gate_greek_header.py <src> <built> --declared
   tests/fixtures/edition_upgrade/declared_deltas.json --dump <out.tsv>` on the CURRENT file (v2: pn_binding
   identical, gate_b at the code pins, changed_rows []). Expected to FAIL (§9.92); its output is the only source for
   the re-declared figures. Then member rulings → amend the file (v3) → re-run.
3. /wrap after each ruled step as usual.

## Member list for gate 2 (rulings owed; carry from the stage D handoff + today)
- From the stage D handoff: the 85 unattributed restore members (J Joram 27 · N 30 · S 9 · X 19); Gen 39:17, 1Ch 1:38
  Ezar, Est 1:17 ")", Eze 20:14 English, Gen 5:25/26 Mathusala; the five §9.85 named cells (cite by NAME).
- §9.96: Silas/Silvanus ×3 (record G4609 with lemma Σιλουανός = G4610) — candidate correction.
- §9.97: Gen 4:18 @14/@16 (record H4967 Methushael vs edition "Mathusala" → G3103) and Num 36:5 @13 (Joseph/Israel)
  — candidate corrections; Jos 5:15@27 now G2424 tipnr — keep. Header receipt: 8 names indeclinable → UNRESOLVED
  (golan, greece, binea, bethhaccerem, …) — display-affecting.
- §9.98: `check_wordpos_prereg.py` R4 would now refuse the 4 joram rows (their evidence quotes keep "Jehoram …").
- Sheshach rows (§9.69) declared UNCHANGED; they enter gate_b.changed_rows only if the first run shows them changed
  (a new ruling then).

## PA housekeeping (11/7)
- Home was at quota (8.3G); deleted by JP: both `bible_pre_pnstar_*`, `bible_test.db`, the 9/6 formlane backup
  (+ `.info`), `~/db_evidence/bible_formlane.db` → **6.3G**. Kept: `bible_pre_trapwire_swap.db` (rollback of
  record), `~/bible.db.pre-surface-fill-20261025` (step 9a's source until 9c), the hdrlane 9/6 backup (§9.95), the
  4 form-lane TSVs. The 8B3c after-check had died on the quota (OSError 122) — keep an eye on space before big runs.
- **Owed — backup stamp read after the 11/8 13:30 UTC nightly** (no manual backup run: bible.db keeps 3, a manual
  run deletes the oldest):
  `cat ~/db_backups/last_success.txt; grep -nE 'XX|!!|Backing up|All backups verified' ~/db_backups/backup.log | tail -12; ls -l ~/db_backups | grep -E 'bible\.db\.'`
  — expect the stamp dated 11/8, no `XX`, the 11/6 + 11/7 bible.db copies compressed. The 11/7 run likely failed on
  the full disk (unverified).
