# HANDOFF — edition upgrade, stage D: REKEY + 8b.1 (written 2026-11-06)

Successor to `HANDOFF_edition_upgrade_stageC_repin.md` (its "Standing rules" and "Follow-up list" still apply) and
`HANDOFF_edition_upgrade_reviewer_setup.md` (done). Every stage-D block, result and ruling so far:
`DRAFT_stageC_outline.md` (sections from "Stage D opened (11/6)") and DESIGN `DESIGN_q2_build.md` §9.85–§9.94 —
DESIGN is the sole ruling register.

## Why the last session closed
CLAUDE.md stop rule. In the §9.93(c)/(B) store inventory CC told the ruling chat `pn_hebrew_xref` is "not read by
position before 8b.2 drops and rebuilds it". False: `retire_hebrew_identity.py` main() opens with an oracle gate
(`:162-172`) that joins the OLD xref to `pn_greek_identity` by (verse_id, position) and HALTS on any xref row with no
identity row at the same position. CC had grepped the write lines, not read main(). Caught while drafting REKEY;
nothing ran on it. **Consequence:** the ruled REKEY (§9.94 (b)/(3)) moves the 6 identity records but not their 6 xref
rows → 8b.2 would HALT (n_only_xref = 6). The REKEY spec needs a ruling-chat amendment before it is drafted.

## State (11/6, end)
- **Built** `~/bible-db/bible_edupg_test_built_20261102.db`: post-tail + R2 + J + **8b.0 applied** (8B0b: 366 plan,
  applied 339, words 626,309). 8b.1 / 8b.2 / 8b.2a / 8b.3 NOT run. No re-key done.
- **Rollback copies:** `bible_edupg_test_built_pre_8b_20261106.db` (= built before 8B0b, sha a4faa4d8…0107) and
  `bible_edupg_test_built_pre_digits_20261105.db` (before R2). Keep both until the swap.
- **Code REF `83f8f570`** (pushed; **PA has NOT pulled it** — PA HEAD at last run `0bb60e4a`). Pull before the next
  block: `cd ~/bible-db && git pull --ff-only && git log -1 --format=%h`.
  - `restore_frozen_pn.py` EXPECT = 178 (§9.94 (a)).
  - `gate_greek_header.py`: `--declared` supports `pn_binding.renamed_rows` (§9.92 G2), `gate_b` block (G3),
    per-table `key_moves_file` for abp_surface in gate A + pn_greek_identity in gate B (§9.94 (c) G4).
  - `scripts/eu_pn_binding_diff.py` (G1, read-only full pn_binding diff).
  - `tests/fixtures/edition_upgrade/declared_deltas.json` **v2**; `pn_greek_identity_key_moves_20261106.tsv` (6);
    `abp_surface_key_moves_20261106.tsv` (15).
- **Reviewer subagent** `.claude/agents/reviewer.md` (§9.90: clears read-only blocks + re-runs of ruled gates only;
  a CLEAR is never a receipt).

## The 8B1 result (182) and what was ruled
`~/edition_upgrade_runs/xref8b1_20261106.log` (local copy was scp'd to `C:\Users\JP\xref8b1_20261106.log` — not in
the repo). 182 = CUSHI 8 · MOVED 6 · OTHER 168 (groups in DESIGN §9.94). 8b.2 halts unless every non-abp-tag identity
slot holds its frozen value (`retire_hebrew_identity.py:225-230`), and restore is all-or-none → **restore-all 178**
after the re-key (§9.94 (a)): 8 + 168 + Est 5:9@12 `'*'->'H2001'` + Jos 5:15@27 `'H3091'->'*'`; the other 4 re-keyed
records already match (Gen 34:4@1 H7927, 2Ki 23:35@6 H3079, Gen 5:25@1 / 5:26@1 H4968).

## Next session's FIRST task — take to the ruling chat, do not draft blocks yet
1. Report the error above and the fix: REKEY moves **three** position-keyed sets on built, not two —
   `pn_greek_identity` 6 + **`pn_hebrew_xref` 6 (same moves file)** + `abp_surface` 15. Check before proposing:
   does the old xref have exactly one row at each of the 6 old positions and none at the 6 new ones (read-only on
   built)? retire's oracle also compares `hebrew_base` across the join — moving both rows together keeps it equal.
2. **Re-do the store/consumer inventory properly** before any write: for each of 8b.1 (`restore_frozen_pn.py`), 8b.2
   (`retire_hebrew_identity.py`), 8b.2a (`lane3_rebuild_step.py` → `fix_lane3_star_merges.py`), 8b.3
   (`build_pn_greek_identity.py`, `build_entity_binding.py` + `build_slot_binding.land`, `audit_unfindability.py`,
   `audit_two_derivations.py`) and gate 2 — READ main() top to bottom and list every (verse_id, position) read.
   The 11/6 inventory (CC's chat answer) is not trustworthy past the xref miss.
3. After the ruling: draft REKEY (wrapper at the then-current REF, pre-checks a/b/c as 8B1, each move: source present,
   target empty or a swap partner, else STOP; one transaction per table or one overall; counts unchanged; verify every
   verse_id → ref first: 131 Gen 5:25 · 132 Gen 5:26 · 985 Gen 34:4 · 5874 Jos 2:4 (DERIVED, not read) · 5950 Jos 5:15
   · 6837 Jdg 11:7 · 10201 2Ki 23:35 · 12788 Est 5:9 · 30987 Rom 9:29; double-paste guard) and 8B1b (expected
   `MEMBERS: total 178 - CUSHI 8 - MOVED 0 - OTHER 170 - greek-numbered 0`, apply on exact match, `restored 178` /
   0 off record, words 626,309). Then 8b.2 (its own declared class split + write set — read the code's EXPECT first).

## Open for gate 2 (member rulings, §9.85 + §9.93 + §9.94 (e))
The 85 unattributed restore members (J Joram 27 · N 30 · S 9 · X 19); Gen 39:17, 1Ch 1:38 Ezar, Est 1:17 ")",
Eze 20:14 English, Gen 5:25/26 Mathusala; the five §9.85 named cells (cite by NAME — three of their positions moved);
**Jos 5:15@27 Joshua — live record class none, built H3091 restored to '*' under §9.94 (a); candidate correction, with
Gen 4:18** (ruling chat 11/6, after 8B1b).

**State update 11/6 19:01 UTC:** STAGED-READ, REKEY (three-set: identity 6 + xref 6 + abp_surface 15) and 8B1b
(restored 178) are DONE and ACCEPTED on built (`DRAFT_stageC_outline.md`, last section). Built = 8b.0 + REKEY + 8b.1.
PA HEAD `2cdc4cf5`; code REF still `83f8f570`. Next: 8B2. The "FIRST task" list below is DONE except item 2's
inventory, which STAGED-READ's record carries.
First gate-2 run includes gate B `--dump`; full pn_binding list from `eu_pn_binding_diff.py`.

## Standing rules
Unchanged from `HANDOFF_edition_upgrade_stageC_repin.md`, plus: print the PA pull line with every block whose REF
moved; member tables print raw verse_ids, not just refs.
