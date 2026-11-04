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
- Banked for every gate from here: add `[ -z "$(git status --porcelain -- scripts tests)" ] || STOP` after the
  `git diff --quiet <REF> HEAD -- scripts tests` line (closes the uncommitted-edit gap).
- Next: PA pull → C4 gate 1 (REF f8e814c2) → output to the ruling chat before §9.61/§9.63 is drafted.

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
