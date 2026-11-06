# HANDOFF — edition upgrade, stage C: tail RAN (11/4) → review of the tail read-back next (2026-11-04)

**Opening brief for the next session (paste as-is):**
> Lexica, fresh session. Repo lexica-bible/lexica, local C:\Users\JP\projects\bible-db. bible.db is PA-only;
> JP runs PA commands from my drafts; no runnable command until the ruling chat clears it; every cleared block is
> printed IN FULL in chat (memory `feedback_print_cleared_blocks`). Code reference = `61484fbc`
> (`git diff --quiet 61484fbc HEAD -- scripts tests` must pass) — confirm first, stop if not. Lane: edition upgrade,
> PA sequence, stage C. The tail (TAIL v3) RAN on `<built>` 11/4 03:18 UTC; its result is recorded below but NOT
> accepted — the ruling chat reviews it first. Read this handoff in full, then `HANDOFF_edition_upgrade_stageC.md`
> (state at stage B close + follow-up list), `DESIGN_q2_build.md` §9.58–§9.84 + the tail-run notes after §9.84,
> `DRAFT_stageC_outline.md` (every block as drafted/cleared), `CHARTER_edition_upgrade.md` §4.5–§4.10 + §6,
> `.claude/commands/rebuild-words.md` steps 3, 8b, 9–9c. Do NOT draft the §9.59 re-pin until the ruling chat accepts
> the tail read-back. Gate pre-check figures come from the code or a PA log, never from a checklist note.

## Why this session closed
CLAUDE.md stop rule: twice on 11/4 CC put an unchecked figure into a gate pre-check (TAIL v1 expected 626,305 words;
TAIL v2 expected all 124 prose rows at before-text). Both guards stopped safely; nothing ran wrong. Ruled: write this
handoff and close; a fresh session takes the read-back.

## State at close
- **Code reference `61484fbc`** (pre-flight `87b3d44b` + the 20261103 freeze). HEAD = this handoff's commit, docs only on
  top. PA HEAD at the tail run: `8db1604a` (docs-only commits since; PA needs no pull for the next read-only block).
- **Live `bible.db` untouched** since the 10/25 swap.
- **`<src>` = `~/bible-db/bible_edupg_test_20261101.db`** — abp_corrections 372 / 23 / 6, the 21 EU after-values in em-dash
  form (S980).
- **`<built>` = `~/bible-db/bible_edupg_test_built_20261102.db`** — build + B --apply (stage B) + S980 + **the tail (finish_rebuild,
  exit 0)**. NOT yet: re-pin, gate 1, retired-row check, gate 3, 8b, steps 11/10/9/9a/9b/9c, gates 4–7, swap.
- Keep (unchanged from the stage C handoff): `~/bible.db.pre-surface-fill-20261025`, `~/bible-db/bible_pre_trapwire_swap.db`, `<src>`, `<built>`.

## What landed this session (all pushed)
- `87b3d44b` — `scripts/eu_retired_check.py` (§9.81; label **`RETIRED-ROW CHECK:`**, exit 0 / 1 / 2),
  `build_prose_from_app.feed_text` (one place B's text is made), `audit_reassembly_diff.py --v2 --punct-members <frozen>
  --eligible <tsv>` (§9.82; label **`V2 MEMBER DIFF:`**), tests in both lists.
- `61484fbc` — `tests/fixtures/edition_upgrade/eu_batch_rows_20261103.tsv` (+ `.sha256`, `38acc6ba…`) beside the unchanged
  20261102 freeze; `eu_corrections_spec_20261102.NOTES.md`; DESIGN §9.83 + the S980 record.
- Docs: DESIGN §9.80–§9.84 + three run notes; rebuild-words step-2 note corrected (the build itself adds the 4 rows).

## Rulings this session (DESIGN §9, one line each)
- §9.80 correction after-values in final corpus form (em-dash); before-value as written. S980 applied it to 21 EU rows on both copies.
- §9.81 retired-row check approved.  §9.82 v2 frozen-241 compare mode approved.
- §9.83 five expected tail skips (Isa 28:20, Mar 14:44, Rom 9:29, Jdg 11:7, 2Ti 4:10); split-merge forecast 234 / 3; other figure = review.
- §9.84 the nine doubled-word slips → follow-up lane (§9.72); 14 normal repeats kept; "be be" ×2 already EU-corrected.

## S980 (11/4 02:57 UTC, `stageC_s980_20261103.log`) — accepted
Both copies: pre-check 372 / 23 / 6, EU fingerprint `16f2c6f5…` = 20261102 file, exactly the 21 refs (ids 60, 71, 80, 92, 107,
110, 113, 147, 169, 175, 192, 207, 210, 226, 235, 241, 255, 269, 272, 287, 311); then `saved: 21 changed`, 0 active `--`
after-values (all ledgers), fingerprint `b709436a…` = 20261103 file. `S980 RESULT: APPLIED on both copies`.

## The tail — run 1 and run 2 stopped at pre-check (nothing ran); run 3 (TAIL v3, cleared) RAN
Logs `~/edition_upgrade_runs/stageC_tail_20261104.log` (v1 stop), `stageC_tail2_…` (v2 stop), **`stageC_tail3_20261104.log`** (the run).
v3 pre-check, all as expected: words 626,309 · active 372 · prose rows 124 · EU prose at before-text 118 · the 6 carve-out
verses already at after-text (1Sa 9:3, 2Ch 10:13, Jer 3:7, Jer 9:23, Neh 12:43, Rev 11:1) · verses with `--` 2,650 · no corrections log.

**Result vs the cleared figures and vs the 10/25-equivalent tail (`~/bible-db/finish_pnstar2.log`):**
| step | v3 (11/4) | 10/25 log | cleared | |
|---|---|---|---|---|
| import_tipnr Matched / Unmatched / still `*` | 31,592 / 734 (687 names) / 885 | 31,649 / 683 (648) / 828 | re-declare | **−57 matched — attribute** |
| fixture drift check | no lines | — | silent | ok |
| fix_subject_reorder | applied 7 · 13 SKIPPED | applied 7 · 13 SKIPPED | 18 / Isa 28:20 + Mar 14:44 | same 13 names as 10/25; CC's "18/2" forecast was wrong |
| fix_mat25_37 | applied | applied | — | same |
| fix_supplied_attach | applied 0 · 5 SKIP | applied 0 · 5 SKIP | 4 / Isa 28:20 | same 5 names (Psa 79:13, Eze 11:3, Job 35:13, Isa 65:11, Isa 28:20); forecast wrong |
| fix_theos_filler_tags / kyrios / merge_misses / idios / dedup | 3 / 2 / 1·0 / 13 / 0 | 3 / 2 / 1·0 / 13 / 0 | same | same |
| **fix_split_merges** | **206 patched · 31 skipped** | 208 · 29 | **234 / 3** | **differs from cleared — review (§9.83)**; +2 skips vs 10/25 fits Jdg 11:7 + Rom 9:29 — UNVERIFIED (only 10 skip samples print; the read-back did not show them) |
| fix_bracket_punct | 196 edits / 95 verses | 200 / 98 | re-declare | one-liner owed |
| 4b prose corrections | applied 118 · already 6 · LOUD 0 | 0 · 18 · 0 | 118 / 6 | ok |
| fix_emdash | `--` words 4,120 / verses 2,629 → 0 / 0 | 2,591 / 0 → 0 / 0 | 0 / 0 | ok |
| fix_split_flip | 1 flip / 1 verse | 1 / 1 | re-declare | same |
| 7 word corrections | applied 248 · already 0 · LOUD 0 | 33 · 0 · 0 | 248 | ok |
| end | exit 0 · words 626,309 · prose at after-text 124 · `--` 0 / 0 | — | same | ok |

**Read honestly:** no loud skip anywhere, every correction landed, the end state is the cleared one. The cleared skip
figures were CC forecasts that counted every patch entry as applying; on a plain rebuild many entries already skip (the
build now produces their result) — the 10/25 log shows the same skips. Under the clearance wording ("any other skip stops";
"234/3 or review") the run is OUT of the cleared figures and needs the ruling chat's review before anything else.

## After close (11/4) — tail accepted, re-pin landed
- Tail v3 ACCEPTED (CHECK 1 v2 + CHECK 2b, §9.85 defers the −57 to gate 2). Detail: `DRAFT_stageC_outline.md`.
- C3a RE-PIN DUMP on PA: `REPIN DUMP: OK - 372 = 28 carried + 344 EU - retired 23 - sha256 80db1c35…`
  (`~/edition_upgrade_runs/repin_dump_20261104.log`); the scp'd file is byte-identical to a local rebuild.
- **C3b re-pin `f8e814c2`** (3 files: cert_invariants pin 51 → 372 + `abp_corrections_active_built_20261104.txt`
  + `.sha256`) = the gate-1 code reference.
- **ACCEPTED SIDE EFFECT (ruling 11/4):** from PA's pull of `f8e814c2` until the swap, `cert_invariants.py` on
  LIVE reads check 4 red (51 active vs pin 372). Expected; nothing runs it automatically. Do not "fix" it.
- Banked for every gate from here: add `[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || STOP`
  after the `git diff --quiet <REF> HEAD -- scripts tests` line (closes the uncommitted-edit gap). AMENDED 11/4: the
  first form (without `--untracked-files=no`) stopped gate 1 on three untracked dumps PA has carried from an earlier
  lane — `scripts/person_metav_link_residual.txt`, `person_metav_link_tier2.txt`, `tipnr_metav_link_residual.txt`.
  Leave those files alone (ruling).
- **GATE 1 ACCEPTED (11/4 04:53 UTC, `~/edition_upgrade_runs/gate1_cert_20261104.log`):** REF f8e814c2, PA HEAD
  7358c8bf; controls 6/6 FIRED; built copy 7/7 — `CERTIFIED STATE HOLDS (7/7 green)`.
- **C5 RETIRED-ROW GATE PASSED (11/4 05:01 UTC, `retired_check_20261104.log`):** 11 tests OK; `PASS 23/23 HOLD
  (corrected_value 18 - feed text 5)`, the 5 = §9.63's named verses.
- **C6 GATE 3 RAN (11/4 14:30 UTC, `gate3_member_diff_20261104.log`): FAIL — HELD by the ruling chat** (not accepted,
  not failed). word-order 112 · content-other 1 (Job 3:3 "Maythe") · dup-gloss 0 · Joh 14:26 HIT · new on non-eligible
  0 | gone 25 · new-on-eligible 367 · changed-ops 12 · unchanged 204 (Psa 89:35 on none). Pre-rulings §9.86/§9.87 wait
  on CHECK 3 (record + block: `DRAFT_stageC_outline.md` "C6 gate 3 RAN"). CC local finding: 111 of the 112 are
  merge-pair / edge-split verses (§9.73/§9.75, eligible by rule), Joh 14:26 on neither — so CHECK 3's passdiff
  intersect is forecast to print STOP.
- **CHECK 3 RAN (11/4): STOP** — 0/112 in passdiff (111 merge-pair/edge-split rows, A-side; Joh 14:26 on neither,
  a `the` before `comforter,` — CHECK 3's "half-cured" was WRONG: CHECK 4 shows live = built on every row); 11/11
  punctuation items = FEED. §9.86 does not apply. Record: `DRAFT_stageC_outline.md` "CHECK 3 RAN".
- CHECK 3 accepted; §9.86 withdrawn; gate 3 STOPPED (§4.10). Pre-ruling §9.88 (fix at the restore rule + scoped
  digit repair on the built copy) waits on CHECK 4. Code read: restores copy english + head only (:2112, :2174).
- **CHECK 4 RAN (11/5 01:51 UTC, `check4_20261104.log`): NOT CONFIRMED (99/111)**, held for the ruling chat. CC sort of
  item 1 (by the ruling's join test): 95 JOIN cleanly · 4 renumbered/odd · 7 live-no-digits (synthesise) · 5 digits
  identical (cause elsewhere). Exposure 150 cells / 123 verses; ~15 of the 24 non-hit exposure verses sit on the §9.87
  punct new-on-eligible list (hand count). Joh 14:26 live = built, pre-existing. Item 4: 1,177 cells / 558 verses
  outside (557 eligible + 1 dash). Detail: `DRAFT_stageC_outline.md` "CHECK 4 RAN".
- CHECK 4 accepted. §9.88 final + §9.89 (Joh 14:26 = live defect → correction rows). Code landed **820a6109** (+
  af14ec30 display): `_join_neighbour_group` (one rule, build + repair), `eu_repair_restore_digits.py`. Code
  differs from the ruling's wording in 5 named ways (DRAFT "§9.88 final") — owed an OK with R1.
- §9.88 amended to the implemented rule (11/5). R1 ran 02:23 → STOP on CC's same-word check at Gen 25:10 (PN bound
  to H2845 after the build); fixed **9fbef17f**. Dash verse = Gen 46:26 p19.
- **R1 re-run (11/5 02:34): PLAN WRITTEN** 389 cells / 133 verses (restored 117, shifted 272), plan sha 694e1564;
  item-2 NOT in the plan 45 (expected 0) = 23 verses whose pair is fully unbracketed on built (rule point 3; read
  in order already). CHECK 4's "15 punct members = digit loss" note was wrong (old-English punctuation). Read:
  DRAFT "R1 re-run".
- R1 accepted. **R2 cleared conditionally** (JP runs without returning if it matches the spec) — block in DRAFT "R2".
- **R2 RAN 11/6: APPLIED 389 + VERIFIED** — receipt exact (other rows 625,920 unchanged), word-order 0 on all 1,456
  listed verses, residue 8/8 clean; 144 punct-position (27 plan + the 15 §9.87 verses + rest) → §9.87 re-freeze.
  Rollback copy `bible_edupg_test_built_pre_digits_20261105.db` kept. Gen 46:26 = lane-③ repair pending at 8b.2a.
- R2 ACCEPTED 11/6. §9.89 rows landed in code **e777f965** (2 rows, pos 3 joins bracket 4; pin 372 → 374). Blocks J +
  G3R drafted, held (DRAFT "§9.89").
- **J DONE + G3R AS DECLARED (11/6):** 374 active on src + built, Joh 14:26 clean; word-order 0, content-other 1
  (Job 3:3), new on non-eligible 0. §9.52 re-freeze count **607** (205 + 390 + 12; 583 + 23 R2 punct + Num 8:26).
- Next: C3a′ dump (held) → C3b commit (pin 374 + member file 446fee35) → PA pull → C4′ gate 1 → C5′ retired-row →
  §9.87 punct re-freeze (9c) → stage D.

## Owed to the ruling chat (next session drafts, read-only)
1. **The full split-merge skip list (31)** vs the 10/25 list (29): the script prints only 10 samples. Needs a read-only
   member check — for each of the 237 `split_merge_fixes.json` entries, does `<built>` hold the patch's `new_eng`/`new_pos`
   (patched) or not (skipped, and why) — and the same list for the 10/25 run if recoverable (`finish_pnstar2.log` lines 160-169
   show its 10 samples). Expected if the +2 reading holds: the 29 of 10/25 + Jdg 11:7 + Rom 9:29.
2. **import_tipnr −57 matched** (31,592 vs 31,649; unmatched +51): attribution by member — likely names whose English
   changed with the app edition (the matcher keys on English), not yet read.
3. **fix_bracket_punct 196 / 95 vs 200 / 98** — one-liner + members if asked.
4. Carried: Split 80 → 84 member attribution (before the swap); the 10/25 skip lists show the "expected skips" for
   subject_reorder / supplied_attach are a standing 13 / 5 — §9.83's list should be amended to the real sets.

## Next steps after the read-back is accepted (order unchanged)
§9.59 re-pin commit (dump 372 active keys from `<built>`, freeze, PINS 51 → 372, scripts-only, PA pull, no reload — new
reference) → gate 1 `cert_invariants.py --controls` then `<built>` 7/7 → `eu_retired_check.py <built>` → gate 3 v2 member
diff (STOP for the §9.52 punct ruling) → stage D (8b; `declared_deltas.json` written before gate 2) → E → F → G.

## Lessons banked this session (memory)
- **A gate pre-check figure is a claim: trace it through the code or a PA log, never a checklist note** (626,305 came from the
  rebuild-words note; the build's own blank-number fill adds the 4 rows). For an expected copy state, trace where each group
  of rows came from (rebuilt vs carried over from live — the 6 carve-out prose rows).
- **Never put `!!` inside double quotes in a block JP pastes** — interactive bash swaps it for the previous command. Single-quote grep patterns.
- **Forecast a patch's count from the previous run's log, not from its entry count** (this handoff's table).
- Every cleared PA block is printed in full in chat (`feedback_print_cleared_blocks`).
