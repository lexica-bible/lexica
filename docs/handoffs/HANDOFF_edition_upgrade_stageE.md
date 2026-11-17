# HANDOFF — edition upgrade, stage E (written 2026-11-08)

Successor to `HANDOFF_edition_upgrade_gate2.md` (gate 2 green and closed; stage D CLOSED). Standing rules and the
follow-up list in `HANDOFF_edition_upgrade_stageC_repin.md` still apply. Rulings only in `DESIGN_q2_build.md` §9
(sole register, latest **§9.158**). Order of the remaining steps: charter `CHARTER_edition_upgrade.md` §6 +
`.claude/commands/rebuild-words.md`.

## SUCCESSOR START (11/16 late, step 4 in progress; HEADFIX2 closed §9.156; STEP4-DELTA2 READ DONE §9.157) — open here

- **11/16 23:05Z: STEP4-DELTA2 (raw delta re-run on the fixed built) READ DONE — the REFERENCE delta for the step-4 gate (§9.157)**:
  `~/edition_upgrade_runs/step4_delta2_20261116/delta/`, words_cells 50,890 `86e44c58…dafc` (= the 11/15 delta less the two
  Joh 19:18 @10 cells). Counts: english 32,962 · english_head 5,426 · greek_pos 3,318 · bracket_id 4,208 · english_head_norm 4,890 ·
  verses.text 15,522. **NEXT: the A dry-run output code** (build_words_from_abp.py AppTransplant: one row per changed cell — verse,
  position, column, before, after — for english, english_head, greek_pos, bracket_id as the delta's per-verse rank; §9.139 (1) +
  §9.142 (4) conditions: changes nothing A writes, tested on/off; inputs sha-checked vs step 5 (eligible e540d34d… etc.); counts =
  english changed 15,588 + a named stage-B figure, greek_pos/bracket verse count vs the stage-B log line) → reviewer → ruling chat.
  Then the live = src proof (JP disk check) + the PA log read (stage-B greek_pos/bracket line, 11/1 retire log, strongs_base rows vs
  pn_greek_identity). Gate block unapproved.

- **11/16 21:13Z: HEADFIX2 RAN — DONE, exit 0, at code REF `d34d6723` (§9.153–§9.155; spent-by-lane-3 rule).** Built Joh 19:18
  @10 english_head + norm 'ere' → 'here'; abp_corrections 374|23|6 → 375|23|6; apply "applied 1 · already-applied 249 · spent by
  lane-3: 1 · LOUD-SKIPPED 0" (spent = Heb 11:24 @7 english); built → throwaway 1 words row / kjv+bsb 0 / corrections +1; check OK;
  built's corrections log 47,168 → 75,652 B. Restore source `~/edition_upgrade_runs/step4_headfix2_20261116/before.db`
  (sha `da47ce8c…57f3`). **Every later block's "built =" guard: `eu_step check --dir
  ~/edition_upgrade_runs/step4_headfix2_20261116 --written words,abp_corrections`** (supersedes the STEP9A and the
  step4_headfix_20261115 guards below). Record: DRAFT "HEADFIX2 ran". Next once the ruling chat has read the log: the raw-delta
  re-run (read-only), then the A dry-run output code (§9.155 (8)). Swap knock-ons: cert pin abp_corrections_active 374 → 375 +
  active-list fixture re-pin; the cert's spent pin (1) is already in d34d6723.
- Still open from §9.153: the PA log read gains (a) the 11/1 retire block's log (write 1 to src's abp_corrections) and (b) a
  read-only check that the 4 active strongs_base rows are not in pn_greek_identity — both before the gate.

(Below: the 11/15 start block, kept for history.)

Read the 9c section below for pins, roles and open items — it still holds, except where this block overrides it.
- **Code REF `0cad6894`** (§9.149: eu_batch_insert `--created` + this-run EU count; heads fixture
  `tests/fixtures/edition_upgrade/eu_batch_rows_heads_20261115.tsv`, sha `4ba1d7bc…bb60`). Step-4 tools landed this session:
  `scripts/eu_words_delta.py` (raw delta, a147c61a), `scripts/eu_head_check.py` (head-consistency check, 50957fc0).
- **built is still STEP9A-APPLY's result** until HEADFIX runs (guard: `eu_step check --dir
  ~/edition_upgrade_runs/step9a_apply_20261115 --written abp_surface`).
- **11/16: HEADFIX RAN and STOPPED before any write (§9.151)** — the dry apply on the throwaway LOUD-SKIPPED Heb 11:24 @7 english (cell 'daughter,'; lane-3 8b.2a rewrote it after the J run — CC's reading, not ruled). Built unchanged = STEP9A-APPLY's result; the STEP9A guard below still holds. A re-run is a CHANGED block (new dated folder/log, counts read from built). Record: DRAFT "HFREAD ran".
- (was) **HEADFIX (Joh 19:18 @10 english_head + norm 'ere' → 'here'; abp_corrections 374 → 375 active) is CLEARED (§9.150), NOT YET RUN.**
  Block text: `DRAFT_stageC_outline.md` → "Block HEADFIX". Conditions: PA pulls to ≥ 0cad6894; JP checks PA disk headroom first;
  a CHECK/STOP goes to the ruling chat as printed, nothing restored before it is read. **After it runs, every later block's
  "built =" guard is `eu_step check --dir ~/edition_upgrade_runs/step4_headfix_20261115 --written words,abp_corrections`.**
  Swap-commit knock-ons it adds: cert pin abp_corrections_active 374 → 375; active-list fixture re-pin.
- **Step-4 state:** (ii) member list ruled (§9.142); verses.text declared list ruled (§9.143–§9.144); english_head_norm by rule
  (§9.142); Isa 48:5 @4 a declared single row, no fix (§9.148); charter §6 step 4 wording amended (§9.139 (0)).
- **Order left:** HEADFIX run + its log read → raw-delta re-run (read-only) → A dry-run output code (english, english_head,
  greek_pos, bracket_id cell changes; conditions §9.139 (1) / §9.142 (4)) → live = src proof (after JP's disk check) + PA log read
  (census2, drift8b2, 8b.0/8b.1/ABPTAG, stage B incl. greek_pos/bracket line) → all lists laid against the delta → the step-4 gate
  block, still unapproved. Then charter steps 5 → 8, then the swap.

## Step 9c closed (11/15) — earlier start block, still valid for pins/roles/open items

Rulings: `DESIGN_q2_build.md` §9 (sole register, latest **§9.158**). Run record: `DRAFT_stageC_outline.md`, from "Step 9 → 9a →
9b → 9c" to the end (every block text, log, verdict). Roles unchanged: ruling chat rules; CC drafts + tests on made-up copies;
the `reviewer` subagent CLEARs read-only blocks and re-runs of ruled gates only (§9.90) — writes and code changes go to the ruling
chat; JP runs every block on PA and pastes the log (the log itself, not a summary — §9.136). Messages to the ruling chat go in one
paste block.

**State of built** (`~/bible-db/bible_edupg_test_built_20261102.db`): everything in "State (11/8, end)" below + steps 11, 10
(unchanged), 12a/b/c, **9 (391,141), 9a (abp_surface 395,014, fingerprint `219a3ebe7075`), 9b (floor 395,014 held, §9.130) and 9c
(re-frozen + pinned, `--check` SNAPSHOT CURRENT on built, §9.137)**. Steps 9 → 9a → 9b → 9c complete. src
`~/bible-db/bible_edupg_test_20261101.db` untouched by steps 9 → 9c. Earlier, src received four writes to its
abp_corrections as the build's source copy for corrections (§9.153 (1)): 11/1 the 23 retired (that block's log not yet read,
so its full write set is open), 11/2 the 344 EU- rows, 11/3-4 S980's 21 values, 11/6 the 2 S-joh14:26 rows. The live = src
proof covers words + verses only (§9.139 (4)). Rollbacks kept: `bible_edupg_test_built_pre_8b_20261106.db`,
`bible_edupg_test_built_pre_digits_20261105.db`.

**Code:** REF **`19e2fb25`** (§9.134: the 9c re-pin). PA HEAD **`1425b124`** (docs after it need no pull for code; `eu_step pre`
needs the block's REF to be an ancestor of PA's HEAD). **The 9c pins** (`scripts/restore_surface_fill.py`):
- `SNAPSHOT_SHA256` = `d025cc086cd7f325bafe3c89655c778f8cdc57f67ba127061a3edfd2192472ff` — `tests/fixtures/rebuild_trap/abp_surface_fill_20261115.tsv`
  (4,411 rows = 3,873 + 538, 455,953 B).
- `REPORT_SHA256` = `e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a` — `tests/fixtures/rebuild_trap/restore_report_20261115.tsv`
  (the 9a apply report, 4,412 lines; R1).
- Default base / after 391,141 / 395,014; N_ROWS / N_INSERT / N_UPDATE 4,411 / 3,873 / 538.
- Both files + `.sha256` are git-ignored ABP text, on PA (placed by STEP9C-PLACE, §9.136) and locally; the 10/25 pair stays beside
  them (charter §7). `snapshot_surface_fill.py --check` needs `--from-restore` while a report is pinned (§9.134 guard).
- **Pre-fill copy (1a / 9a `--prefill`):** `~/abp_surface_prefill_20261115.db` — 18,194,432 B, sha256
  `ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273`, abp_surface 391,141 rows (§9.134 (iii)); the original
  `~/edition_upgrade_runs/step9a_apply_20261115/before.db` stays.
- **Punct member file:** `tests/fixtures/reassembly/punct_members_built_20261115.txt` (607, `0cc4d428…7056`, committed); the 10/30
  file (241) kept.
- **Until the swap, live does not match these pins** (§9.134 (ii)): 1a `--check` on live reads STALE (e.g. Jer 49:3 @3 frozen `*`,
  live H5857); 9a's default base does not fit live. No rebuild of live runs before the swap. NOT yet re-pinned (swap commit): the
  health floor 395,003 (`health_check.py:144`) and rebuild-words step 9 / 9b text.
- 9a/9c run folders on PA: `step9a_*`, `step9b_floor_20261115`, `step9c_freeze_20261115`, `step9c_place_20261115`,
  `step9c_check_20261115`, `jer493_read_20261115`. The 9a throwaway `step9a_apply_20261115/dry.db` (~110 MB) left in place (§9.137:
  CC's call; needed only if a later block re-checks built against the 9a prep).

**Next:** charter §6 **step 4** (compare_words vs live, per-column attribution) → 5 → 6 → 7 → 8, then the swap (stage G). CC's
report on what step 4 needs goes to the ruling chat first (§9.137).

**Open items (none blocked 9; carry into steps 4 → 8):**
- **Heads gap** (§9.107 ruling 2): built has 1,351 fewer non-blank `english_head` than src (lost 1,691 / gained 340; list
  `~/edition_upgrade_runs/step11heads_20261108.tsv`). Open until read and explained from the rows; CC drafts the read.
- **Notes on live, no action:** live's word_gloss lacks 82 proper-noun glosses built has (12b, §9.110); live's tipnr_metav_link is
  962 person links short of what the current builder makes from live's own entity tables (12c, §9.111).
- **Job 3:3 content-other** — the open hard-fail from the §9.87 punct work (§9.113 ruling 1); stays open, follow-up corrections batch.
- **pn_binding src 15,446 vs built 15,426** — observed at 12c, no ruling (§9.111); the 160-row gate-2 delta (`f26fb503`, §9.102-9.103).
- **Label note:** the restore prints "APPLY (copy only)" / "(on a copy)" on any `--apply` run, built included (§9.128) — a label.
- The follow-up lane list below (§9.100) stands.

## Progress 11/8 → 11/15 (history; the section above is current)
- **Shared step script landed:** `scripts/eu_step.py` (pre / prep / same / delta / check) + `tests/test_eu_step.py`,
  **code REF `006e16ba`** (§9.106). New blocks call it instead of pasting a helper; `pre` runs the REF git checks
  (`mode_pre` :126-136); a block whose builder imports a repo-root file guards that file itself (§9.107).
- **Step 11 APPLIED on built and CLOSED** (§9.107): english_head_norm filled on 353,595 rows; kjv/bsb unchanged.
  Built = everything below + **step 11**. Record: `DRAFT_stageC_outline.md` "Stage E opened" onward.
- **OPEN edition item — the heads gap** (§9.107 ruling 2): built has 1,351 fewer non-blank `english_head` than src
  (lost 1,691 / gained 340; list `~/edition_upgrade_runs/step11heads_20261108.tsv`). Not a step-11 figure; open until
  read and explained from the rows; CC drafts the next read.
- **Step 10 CLOSED "unchanged"** (§9.108: IDENTICAL, no paste).
- **Step 12a APPLIED on built and CLOSED** (§9.109 + closing, 11/9 03:05Z): dotted_lexicon re-created, 3,627 rows = src.
- **Step 12b APPLIED on built and CLOSED** (§9.110, 11/14 01:45Z): word_gloss 17,650 = 17,568 + 82 proper-noun
  glosses live already lacked (in live's words, never glossed; note on live, no action).
- **Step 12c APPLIED on built and CLOSED** (§9.111 + closing, 11/14 18:08Z): tipnr_metav_link 2,606 = 1,644 + 962
  person links live's own entity tables already produce but live's table never received (note on live, no action).
  **Step 12 (a, b, c) complete.** Next: 9 → 9a → 9b → 9c (§9.87 punct 583 vs 607 ruled before 9c).
- **Step 9 report + STEP9-DRY drafted** (reviewer CLEAR, 11/14; DRAFT outline "Step 9 → 9a → 9b → 9c"). Found: the
  9a/9b/9c scripts have the 10/25 figures written in (391,130 / 395,003 / 4,411) — a code change is needed before
  the 9a dry run (design item for the ruling chat). Punct: **607 ruled** (§9.113).
- **Step 9 APPLIED on built and CLOSED at 391,141** (§9.122, 11/15 02:55Z) after the respelling fix (code REF 32a39a10, §9.117;
  163 name forms recovered — the 160 name slots STEP9-MEMBERS found losing their Greek were fixed before the apply, §9.114-9.119).
  **9a/9b/9c code REF cd6566b3** (§9.121).
- **Step 9a APPLIED on built and CLOSED at 395,014** (§9.128, 11/15). Code REF **88f7a5f6** (§9.125: a reason-7 slot may be
  key-2-listed). Full state + what is next: the section below.

## State (11/8, end)
- **Built** `~/bible-db/bible_edupg_test_built_20261102.db` = **8b.0 + REKEY + 8b.1 + §9.96 restore + 8b.2 + 8b.2a +
  8b.3 + SLOT3**. words 626,309 (digest 2b23f546), abp_surface 395,003 (623cca1f), identity 32,478 at
  3,671 / 10,246 / 12,216 / 4,382 / 1,963, pn_binding 15,426 (render 15,358 + HOT 68), **pn_slot_binding 105**
  (102 + the 3 Jehoram-of-Judah slots, §9.104). Gate 2 GREEN on it (GATE2-RUN3, §9.103).
- **src** `~/bible-db/bible_edupg_test_20261101.db`. **Rollbacks (keep until the swap):**
  `bible_edupg_test_built_pre_8b_20261106.db` (built before 8b.0), `bible_edupg_test_built_pre_digits_20261105.db`.
  SLOT3's own restore source: `~/edition_upgrade_runs/slot3_20261107/slot_before.tsv` (the 102 rows).
- **Code REF `f0e60cf7`** (pushed; PA pulled 11/8). Chain tonight: `1da5abf0` → `1ad10cec` (§9.99, step-12
  prerequisites) → `36ead576` (§9.101, G5) → `c37fd41d` (§9.102, G6; gate 2 closed here, §9.103) → `f0e60cf7`
  (§9.104, the 3 slot rulings + `tests/test_slot_rulings_judah.py`). Docs after it: the §9.104 / handoff commit.
- **Gate 2 tooling now in the gate** (`scripts/gate_greek_header.py --declared`): G5 `pn_binding.delta_file` +
  sha256 (a committed row-level delta file, both directions); G6 `gate_b.shape_exceptions` {file, sha256} (a
  committed gate `--dump`, exact set, each must fire). The lane's declared file is **v4**
  (`tests/fixtures/edition_upgrade/declared_deltas.json`), GENERATED by `scripts/eu_declared_gate2.py` from three
  sha-pinned fixtures: `pn_binding_delta_20261107.tsv` (160, f26fb503…), `identity_delta_20261107.tsv` (58,
  62a99ffe…), `gate2_shape_exceptions_20261107.tsv` (34, b43e0a12…). Tests: `test_gate_declared.py` (30),
  `test_eu_declared_gate2.py` (4), `test_slot_rulings_judah.py` (4).
- **Reviewer subagent:** clears read-only blocks and re-runs of ruled gates only (§9.90); it ESCALATES writes, and
  that stands — no §9 extends it to write checks (ruling chat 11/8, SLOT3). Writes go to the ruling chat.

## Tonight's PA logs and run folders (`~/edition_upgrade_runs/`; never overwrite — paste once)
`gate2dump_20261107_r2.log` (+ `gate2dump_20261107/`) · `gate2run1_20261107_r2.log` (+ `gate2run1_20261107/`) ·
`g2read_20261107.log` · `g2memb_20261107.log` (+ `g2memb_20261107/member_sheet.tsv`) · `g2sit_20261107.log` ·
`g2r113_20261107.log` · `gate2run2_20261107.log` (+ `gate2run2_20261107/gate2_run2_dump.tsv`, the G6 source) ·
`gate2run3_20261107.log` · `slot3_20261107.log` (+ `slot3_20261107/slot_before.tsv`, `slot3_20261107/dry.db` —
**leave both**). The two first-paste logs `gate2dump_20261107.log` / `gate2run1_20261107.log` hold only the REF STOP.
Local copies of the three fixture inputs: `C:\Users\JP\edition_upgrade_runs\pa\`.
**Run record gap:** tonight's blocks are recorded in DESIGN §9.99–§9.104 and these logs; they were NOT appended to
`DRAFT_stageC_outline.md` (the block texts were drafted in a CC scratchpad, not the repo).

## Next — in this order
1. **Step 12 (side-table builders) on built.** Its five questions were ruled 11/7 and its code landed at `1ad10cec`
   (`DRAFT_rebuild_words_side_tables.md` is the record; `rebuild-words.md` step 12 is the procedure). What is left
   is the run: 12a `dotted_lexicon` → 12b `word_gloss` → 12c person metaV links (+ read-only place-orphan check,
   expect 0), each dry/trial on `<built>` first, figures declared from that log by path:line, `--apply` gated on
   them (§ Q5). **Order RULED (ruling chat 11/8, DESIGN §9.105): 11 → 10 → 12 → 9 → 9a → 9b → 9c**, as
   `rebuild-words.md` has it; charter §6 amended to match (one line, `76623539`). So steps 11 (rendering norm) and
   10 (two-ending read) run on built BEFORE step 12.
2. **§9.87 punct figure at the 9c fixture:** §9.87 stands at 583; 607 is a CC claim, NOT ruled (§9.91). The
   583 → 607 reconciliation is shown member by member and ruled before the 9c re-freeze commit.
3. **Stage E steps 9 → 9a → 9b → 9c** on built (charter §6): 9 surface rebuild (builder-chain total re-declared,
   not 391,130); 9a fill restore without `--prefill` (dry → verdict on the reason-6 members → apply); 9b health
   floor (re-declared); 9c re-freeze on built (`snapshot_surface_fill.py` replace mode, before = `<src>`; pin in
   `restore_surface_fill.py` in the same change). Then 4 → 8 per charter §6.
4. /wrap after each ruled step.

## Follow-up lane (from §9.100 — declared at gate 2, fixed later; none blocks stage E)
- Gen 4:18 @16: binding lost — 'mathusala' at Gen 4:18 → Methushael@Gen.4.18.
- Silas/Silvanus ×3 (1Th 1:1@2, 2Co 1:19@16, 2Th 1:1@2): unbound on both copies.
- Gen 39:17 @14: blank name-cell shape (english None, is_pn 1, G1445).
- 1Ch 1:38: name-key ezar → Ezer@Gen.36.21.
- 2Ki 22:1: 'boscath' lost fuzzy Bozkath.
- Name-keys: thara → Terah, thamar → Tamar, urias → Uriah (bindings REMOVED), phares → Perez, huphamites (lost
  fuzzy Muppim).
- 8 header names → UNRESOLVED-no-nominative (golan, greece, binea, bethhaccerem, …): nominative resolution.
- Pre-existing candidate corrections: 1Sa 12:9 @13 xref H3003 vs the Greek Ιαβίν = Jabin (H2985 at Jdg 4);
  Num 36:5 @13 xref H3478 vs identity G2501 (frozen record restored over built-before H3130).
- 1Sa 11:3 @6: Ιαβής on ', saying,' with is_pn 1, on both copies.
- Est 1:17 ')' stays on the §9.87 list.
- Isa 48:5 @4 (§9.148): italic_words 'happen,whould' (the typo still in the added-words value, both copies) → the corrected
  value; and src / live's english_head 'would' (built keeps 'what', a declared single row of the step-4 gate).
- `check_wordpos_prereg.py` R4 refuses the 4 Israel-king joram rows (evidence quotes keep "Jehoram …") — §9.98.
- Still open from earlier (stageC_repin follow-up list): the 10 reorder verses — eSword/ABP order confirmation
  before the swap (§9.93 b); notes-store position anchors at the 20 moved words — before stage G.

## PA housekeeping
- **Owed — backup stamp read after the 11/8 13:30 UTC nightly** (no manual backup run):
  `cat ~/db_backups/last_success.txt; grep -nE 'XX|!!|Backing up|All backups verified' ~/db_backups/backup.log | tail -12; ls -l ~/db_backups | grep -E 'bible\.db\.'`
  — expect the stamp dated 11/8, no `XX`, the 11/6 + 11/7 bible.db copies compressed.
- Disk: home was 6.3G after the 11/7 cleanup; tonight's folders are small (SLOT3's `dry.db` ≈ 20 MB).
- Local only: Git for Windows' system `core.autocrlf=true` turns the sha-pinned fixtures into CRLF on a FRESH
  local clone (the delta file then hashes 8c91eea… instead of f26fb503…). This checkout has `autocrlf=false`;
  PA is Linux. Clone with `-c core.autocrlf=false` for any local test of these fixtures.
