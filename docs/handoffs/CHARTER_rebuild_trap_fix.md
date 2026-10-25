# CHARTER — rebuild-trap fix (the abp_surface fill must survive a words rebuild)

2026-10-26. Docs only: no script, no PA command. Inputs: `CENSUS_rebuild_trap.md` (commits
`a7a86e44` + `8a7b5040`, PA reads A–E recorded there). Gates the English-line edition upgrade
(`TODO.md` "edition upgrade to the app's English").

**JP ruling (2026-10-26, quoted):** "the trap is DROP at build_abp_surface.py:297 plus a health
floor below the pre-fill count. The fix must (a) snapshot the fill as the 4,411-row diff before
step 9 and re-apply after, (b) re-key it across position moves, (c) raise the floor above 395,003.
Settle first where step 9 runs (copy vs live)." 8b.3 ordering bug: its own TODO item, not here.

---
## §1 Ruling: where step 9 runs — on the LIVE file, after the swap

**What the three texts said (before this charter):**
| Text | Said | Cite |
|---|---|---|
| `scripts/finish_rebuild.sh` | "after a real swap, re-run build_abp_surface.py + build_abp_translit.py" | `:112-113` |
| `/rebuild-words` step 9 | named no file for the builder or backfills; translit named `bible.db`; numbered after the step-8 swap (but 8b, also numbered after 8, runs on the copy) | `.claude/commands/rebuild-words.md:218-230` (pre-edit) |
| build script closing text | run `build_abp_surface.py {target}` on the COPY, before the swap | `scripts/build_words_from_abp.py:2224-2226` (pre-edit) |

**Which is currently true — `finish_rebuild.sh`.** The record of what was actually done:
- R-1 words rebuild (7/16): "post-swap checks green (health_check 0/0 after the abp_surface
  backfill the checklist had been missing)" — `docs/REBUILD_SCOPE_headword.md:3-5`; "health_check's
  floor caught the omission post-swap" — `TODO_ARCHIVE.md:1359-1360`. The surface work finished on
  live, after the swap.
- Form-table rebuild (8/23): rehearsed on a copy, then **landed by re-running the identical
  sequence against live** — `docs/tickets/CHARTER_form_table_rebuild.md:318-324` (chosen over a
  file swap), `:457-459` (landed).
- Blank-"G." live patch: re-ran `build_abp_surface` + translit on live — `TODO_ARCHIVE.md:2718`.
- Not recorded either way: the 8/5 ② ride.

**Docs fixed in this commit to match:** `/rebuild-words` step 9 now opens with the WHERE line and
names `~/bible-db/bible.db` on the builder and both backfills; the build script's closing text no
longer lists the surface builder/translit among the pre-swap copy steps and instead prints an
after-the-swap pointer to step 9 with the fill warning (print text only — no build behaviour
changed). `finish_rebuild.sh` unchanged.

**Consequence the fix must live with:** step 9's DROP hits the serving table. Between the swap and
the end of step 9 (and the fill re-apply), live serves the old surface table against new positions,
then a table without the fill. Moving step 9 onto the copy is a different design; if the fix lane
wants it, all three texts change together, by ruling — not by drift.

---
## §2 The three parts as pre-registered gates

### Part (a) — snapshot the fill before step 9, re-apply after
**Snapshot = the 4,411-row diff**: live `abp_surface` EXCEPT the pre-fill copy
`~/bible.db.pre-surface-fill-20261025` (on PA, 442,687,488 bytes, census §5 E).
- **G0 (precondition, before anything else):** the diff reads **4,411** live-not-in-copy and **538**
  copy-not-in-live — the 10/26 reads (census §5 results Q5). Any other pair = STOP: something
  besides the fill has changed the table since 10/25, and the diff is no longer "the fill".
- The snapshot must also carry, per fill slot, the OLD `words` row it was keyed to (at least
  verse_id, position, strongs, english, english_head, is_pn) — re-keying (part b) needs it, and after
  the swap the old rows exist only in the pre-rebuild rollback copy (`/rebuild-words` step 1). So the
  snapshot is taken from a pre-swap file. 4,411 rows, 4,411 distinct slots, every one with its old
  words row (no slot without one — census §5 C read 0 orphans on live).
- The 538 updates keep their recorded OLD value (the copy-side row) as their precondition, the same
  rule the apply used: write only where the stored form still equals the old one
  (`scripts/apply_abp_surface_fill.py:239-242`).

**G1 — table count after the re-apply = 395,003 exactly.**
- Arithmetic it rests on: the builder chain (step 9: builder + both backfills) must first total
  **391,130** (sub-gate G1a — the 8/23 figure the fill was laid on, `CHARTER_form_table_rebuild.md:457-459`).
  Then +3,873 inserts; the 538 updates add none. 391,130 + 3,873 = 395,003.
- G1a ≠ 391,130 = STOP before any re-apply: the builders' own output moved, so 395,003 no longer
  follows and the target must be re-declared by ruling, member by member — never assumed.
- G1 interacts with G2: any unplaced insert leaves the total below 395,003, so **G1 fails and the
  run stops at a checkpoint**. A listed reason explains a shortfall; it never passes one.

### Part (b) — re-key every fill slot across position moves
**G2 — every one of the 4,411 fill slots ends in exactly one bin:** placed at a new key, or
**unplaced with a reason** from this closed list:
1. no slot in the rebuilt verse matches the key;
2. more than one slot matches (ambiguous — never pick);
3. update precondition failed (the builder's value at the new slot ≠ the recorded old value);
4. insert target is no longer empty (a builder now writes a form there);
5. number + form agreement fails at the new slot (see the second-derivation check below);
6. cross-check found no slot, or more than one (key 1 empty/ambiguous while key 2 found one slot);
7. **key conflict** — key 2 and key 1 each found one slot, and they are different slots
   (added by JP ruling 2026-10-26, §3).
Placed + unplaced = 4,411, itemized by class and by reason; the unplaced list is a file, member by
member. Plus, on every placed row:
- **Second derivation:** every Lexicon-backed row (the classes in
  `apply_abp_surface_fill.py:53-55`) re-passes the apply's own number + form agreement check at its
  NEW slot (`:258-267`, the `agree()` rule from `census_abp_surface_glued.py`) — an independent
  witness that the form landed on the right Greek word, sharing no code with the re-key.
- **Untouched elsewhere:** every non-fill row = the builder chain's output, byte for byte.
- **Translit:** each placed row's translit = `romanize(form, lemma of the NEW slot)` (the apply's
  rule, `:92-100`, `:230-236`); a following `build_abp_translit.py` run changes 0 rows.

### Part (c) — the floor
**G3 — health_check floor = 395,003 exactly** (JP ruling 2026-10-26: "Floor = 395,003 exactly (G3
as written)" — the "above" wording below is answered). Control, red first: the check **fails on the pre-fill copy**
(391,130 → shortfall 3,873) and **passes on live** (395,003), both shown before the floor change is
trusted. It must also fail on a rebuilt table that lacks the fill (that is the trap it exists for).
**Wording flag for the reviewer:** the ruling says "above 395,003". The check fires when the count is
BELOW the floor (`scripts/health_check.py:138-140`), so a floor set strictly above 395,003 would fail
live today. This charter reads it as "raise it to 395,003" — the lowest floor that still catches the
loss. Confirm or correct.

### Part (d) — the lane-3 hand repairs ride the rebuild (JP ruling 2026-10-26, promoted from TODO)
**MOVED 2026-10-26 (JP ruling, after the G4 test's step 1):** the step is `/rebuild-words` **8b.2a**,
`scripts/lane3_rebuild_step.py <db>` — after 8b.2, before 8b.3 — and is no longer in
`finish_rebuild.sh`. Why: the dry run on the test build SKIPPED Mat 27:26 (`strongs mismatch pos 7
(* != G2424)`); live's `G2424` there comes from the identity table (`G2424 / tipnr`) and reaches the
word only in 8b.2, which runs after finish_rebuild. All 16 other repaired name slots are `'*'` on live
with no Greek number in the identity table, and their identity rows (lemma-only / none / surface) were
built after the repairs — so 8b.3 must see the repaired words. **Bracket rule (JP ruling):** no
pinned FAIL lines — a contiguity FAIL from the fixes file is tolerated only on a slot listed in
`lane3_star_gapfix.json` (same verse, position and bracket; read at run time; the 10/26 dry run's 4
FAIL verses are exactly gapfix's 5 slots); gapfix must then PASS on every such verse; any other FAIL
fails; fixes2 strict. Matcher = `judge()` in the step script, locked by
`tests/test_lane3_rebuild_step.py` (12 cases). Text below is the first placement, kept as the record.

**G4 (first placement, superseded above) — `finish_rebuild.sh` step 8 runs `fix_lane3_star_merges.py` on `$1` for ALL THREE frozen
files, in the ledger's order** (`docs/audits/LANE3_b2_dispositions.md`): `lane3_star_fixes.json`
(9 verses / 23 ops) → `lane3_star_gapfix.json` (4 / 5 — bracket marks only, needs fixes' brackets) →
`lane3_star_fixes2.json` (7 / 17). **Correction 10/26:** the census and first draft named two files;
the gapfix file was missed because it touches only `bracket_id`, a column the per-column compare did
not check. Each file passes only on the script's own count line with N pinned (9, 4, 7): all N
patched OR all N already applied, 0 skipped, no per-verse render/contiguity FAIL (JP ruling: a mix
fails). The repair script gained an explicit ALREADY check (every pinned cell holds its new value)
because its SKIP line cannot tell "already fixed" from "state changed"; locked by
`tests/test_lane3_already_applied.py`; matcher checked on 9 fake outputs. Then step 10 vs live must
read **english 0**, plus greek_pos 0, english_head 0 and bracket_id 0 (name-slot `strongs_base`
excepted while 8b is skipped) — the first two files' edits are exactly the 35 english + 38 greek_pos
cells of the 10/26 compare. Committed 2026-10-26 after JP's read.
**Predicted limit (unverified, for the re-run test):** a SECOND full chain run re-runs `import_tipnr`
first, which numbers every `'*'` slot that has English (`import_tipnr.py:381-387`) — including the
name slots step 8 just filled. Any it resolves change `strongs_base`, so step 8's ALREADY check (pinned
`'*'`) reports SKIP and the chain fails loudly. A first run is unaffected (step 8 runs after
import_tipnr — the order the live repair had). Re-running step 8 ALONE passes via already-applied.

---
## §3 The re-key method — RULED 2026-10-26

**JP ruling (quoted):** "key 2 (verse_id + ordinal of strongs within verse) primary; key 1
(verse_id + strongs + english) runs alongside as cross-check. Both agree → placed. Disagree →
unplaced, reason 'key conflict'. Lexicon check stays as third witness where covered. Add 'key
conflict' to the six fixed reasons; count the Lexicon-uncovered group in the dry run."

How the ruling reads in the gates: placed = key 2 and key 1 each find exactly one slot and it is
the SAME slot, and (where the class is Lexicon-backed) number + form agree there. Reason 7 = both
found one slot, different slots. Where key 2 finds one slot but key 1 finds none or several, that is
not "both agree", so it is unplaced — counted as its own reason (6) so the dry run shows its size.
**Consequence to read at the dry-run checkpoint:** a slot whose English changes cannot pass key 1,
so under this ruling every such slot is unplaced. On a same-code rebuild that should be few; on the
English-line edition upgrade it is the 29% case. The dry run reports reason 6 by itself so this is
measured, not argued.

**Second ruling, after the dry run (JP 2026-10-26):** "'key 1 several, incl. key 2's slot' =
agreement. Tag as agree-weak in the TSV and summary." Placed = agree-strong (key 1 finds exactly key
2's slot) or agree-weak (key 1 finds several, key 2's among them). Reason 6 now = key 1 none, or
several without key 2's slot. Expected on the same copies: placed 4,403 (4,050 strong + 353 weak) /
unplaced 8.

**What a same-code rebuild moves (JP ruling 2026-10-26, recorded):** on a rebuild from the same code
and inputs as live, **zero fill slots move** (10/26 dry run: key 2 found every one of the 4,411 at its
old position). So for the trap fix alone the payload is **preserve + re-apply**; the re-key keys are
exercised for real only by a rebuild that moves positions or English — the edition upgrade.

**The analysis the ruling was made on (kept as the record):**

Facts both candidates rest on: `verse_id` is stable across a rebuild (the build reads `verses`,
never writes it — census §2); `position` is not (splits, merges, swaps — census §2); the old words
rows come from the pre-swap file (§2a). Keys compare the FULL dotted `strongs`, never
`strongs_base` (CLAUDE.md audit rule — dotted-number blindness). **The rebuild this fix gates is the
English-line edition upgrade, which changes English words in 29% of paired verses**
(`TODO.md` edition-upgrade item) — that is the stress case for any key with English in it.

**K1 — verse_id + strongs + english** (the old slot's printed English).
- Misses everything the motivating rebuild exists to change: any slot whose English changes finds
  no match (reason 1) though the Greek word is the same. On the edition upgrade that is the main
  case, not an edge.
- Also misses: English moved between cells by build passes (punctuation float, article-slot pass,
  PN subject split moving a name off its verb, em-dash swap); strongs changed by the build
  (pronoun retag, PN numbering) where the new build differs from the old one.
- Ambiguous (reason 2) where a verse carries the same number + English twice ("the blood" twice in
  Mar 14:24 — memory `feedback_audit_tools_must_fail` #20).
- Blank-English slots (blank article slots are normal — `data-model.md` "Article slots") collapse
  to verse + strongs.
- Failure shape: mostly LOUD (no match), rarely wrong.

**K2 — verse_id + ordinal of strongs within the verse** (the k-th slot carrying number N, in
position order).
- Survives English changes — the edition upgrade's main case.
- Misses when the count of number N in the verse changes: a verb split (`_split_numbered`, one
  Greek word → two slots with the same number), the PN subject split, the blank-"G." fill, a merge
  or dedup — every later occurrence of N shifts by one. Name slots are the worst case: many carry
  `'*'`, and the PN split adds `'*'` slots. **21 fill inserts sit on name slots** (census §5 Q6).
- Misses a strongs change at the slot itself (both that number's and the new number's ordinals move).
- Split renderings (one Greek word on two rows with the same number, `data-model.md` "Word-study ABP
  tab total") — which half carries the form is a position fact the ordinal can't see.
- **Failure shape: can be SILENTLY WRONG.** If two slots with the same number swap order, or an
  extra one appears before them, K2 places the form on the other occurrence — and two occurrences
  of one word in a verse can be different inflections. Nothing in K2 notices.

**K1 ∧ K2 (both must agree; disagreement = reason 6).** Inherits K1's English blindness, so on the
edition upgrade it places little. Listed for completeness.

**K2 + the second-derivation check (CC lean before the ruling; superseded by the ruling above).** Place by K2; accept a
placement only if the G2 number + form agreement passes at the new slot; else unplaced (reason 5).
That turns K2's silent failure into a loud one for the Lexicon-backed classes. What it still misses:
(i) rows NOT in a Lexicon-backed class have no second witness — their count must be read off the
apply's class list before this lean can be accepted; (ii) two occurrences of the same word in the
SAME inflection swapping order — same form, so the misplacement is invisible and also harmless to
the reader; (iii) everything K2 misses as "no slot" stays unplaced (honest, not wrong).
**Sizing is unknown until a dry run on a built copy** reports, per key, placed / unplaced by reason
(census §5: not answerable by a read of live). That dry run is the first owed step of the fix lane,
before any write.

---
## §6 The re-key dry run (built 2026-10-26; PA sequence handed to JP, NOT yet cleared)
Script `scripts/dryrun_rekey_fill.py`, locked by `tests/test_rekey_dryrun.py` (both test lists).
Reads `--old` (a copy of live taken before the build: fill + old positions), `--prefill`, `--built`
(build + finish_rebuild.sh, step 9 NOT run), the approved fill CSV and the Lexicon; opens every
database read-only; writes only a TSV report. Refuses the live path, any file named `bible.db`,
the same file twice, and a `.db` report path. Controls before results: G0 (4,411 / 538 and = the
CSV), V (verses identical old vs built), C1 identity (key 2 maps every row to itself; no reason
1/2/5/7), C2 (the Lexicon witness fails a form against a neighbour's number). Reasons 3 and 4 are
not evaluated (they need step-9 output).
**Finding while testing — the Lexicon witness cannot fire as a third witness under these keys.**
Both keys require the SAME full strongs, so the new slot always carries the old slot's number, and
the agreement check reads only number + form. Agreement at the new slot is therefore identical to
agreement at the old slot, which C1 already proves passes. Reason 5 can never be non-zero in a
completed run; in particular the witness cannot catch a form put on the wrong occurrence of the
same number (the key-2 silent-failure case, §3). Reported for the reviewer — no change made.
**DRY RUN RESULT (JP ran on PA 2026-10-26, steps 1–11; build = same code as live's 8/5 ride —
build line, split 80, PN-star pin and the whole repair-chain log match the ride's logs):**
G0 PASS (4,411 / 538 = CSV) · V PASS (31,237) · C1 PASS (key 2 self-maps 4,411/4,411; reason 6 on
identity = 354) · C2 PASS (3,836 of 3,858 covered forms fail on a neighbour's number).
Placed **4,050** · unplaced **361** = reason 6 "key 1 several, incl. key 2's slot" **353** + reason 6
"key 1 none" **7** + reason 7 key conflict **1**; reasons 1/2/5 = 0. Key 2 found exactly one slot for
all 4,411, and **no placed row moved** (positions identical on this build). Lexicon: 3,667 pass ·
383 uncovered among placed; uncovered group overall 389 (fill_unlisted 32 · normalize 357).
Unplaced on name slots 9. G1 preview: placed inserts 3,528 of 3,873 → G1 cannot reach 395,003.
Reading: the 353 are the identity floor (a verse repeating the same number + English — true on live
itself), not rebuild movement; the 7 + 1 sit where the words-level compare found English changed
(35 english diffs, all in the 16 lane-3 hand-repair verses — see TODO "lane-3 hand repairs not in the
rebuild chain"; member check of the 8 owed). The motivating stress case (positions/English moving,
the edition upgrade) was NOT exercised by this build — nothing moved.
**RE-RUN under the agree-weak ruling (JP, PA, 2026-10-26 06:51, same copies):** every expected figure
exact — placed **4,403** (4,050 strong + 353 weak) · unplaced **8** (reason 6 key 1 none 7 · reason 7
1) · C1 identity 0 unplaced, weak floor 354 · placed inserts 3,865 of 3,873 · name slots unplaced 0.
**All 8 are lane-3 repair slots** (each = one op: live English = the op's new_eng, built = its
old_eng): Gen 46:26 p19 · Lev 24:10 p3 · 1Sa 14:50 p3 · 2Ch 14:12 p11 · Isa 30:31 p5 · Jer 50:16 p11 ·
Heb 11:24 p7 · Mat 9:11 p2 (the reason-7 row). **Pre-registered for the G4 test:** with the lane-3
step in the chain, the same dry run reads placed 4,411 · unplaced 0 · placed inserts 3,873 of 3,873.
8b is left out of the dry-run sequence: it writes only `strongs_base` and name tables
(`correct_xref_vs_binding.py:259`, `restore_frozen_pn.py:113`, `retire_hebrew_identity.py:295`),
none of which the dry run reads. Step 8 (swap + deploy) is never part of it.

## §7 G4 test on PA (2026-10-26, fresh copy old2 → built2, full 8b) — step 10 record
Ran: build (log identical to the first test build) → finish_rebuild (log identical, timestamps aside) →
8b.0 (CONTROL OK; SWAP 319 · REMOVE 22 · LEAVE 27 · HOLD 1; applied 341) → 8b.1 (after re-declaring
6→8: restored 8, 0 left) → 8b.2 (after re-declaring the class split: 26,317 rewrites, xref 32,478,
GLOB 0) → **8b.2a LANE-3 STEP: PASS** (9/4/7 patched; re-run 0/9 · 0/4 · 0/7 already applied) →
8b.3 (identity 32,478; binding render 15,378 + HOT 68; slot binds 102/0 refused).
**Step 10 vs a fresh copy of live:** words english / english_head / greek_pos / strongs / is_pn **0**
— G4's own gate (the lane-3 repairs survive) PASSES. Explained differences, each attributed row by row:
- `pn_greek_identity` 21|21 — header table predates the 10/25 fill (JP ruling: explained; TODO held).
- `pn_binding` 3|3 — the 3 Michaiah binds ruled/spelling-equiv → fuzzy, same entity (checklist-predicted).
- **`pn_hebrew_xref` 519 + words `strongs_base` 501 — see G5.**
- words `bracket_id` 2 — 2Sa 18:31 p7 + 18:32 p15, the 8/7 wordpos-lane hand repair (interior-blank
  bracket marks, `TICKET_wordpos_binding.md:261-279`), held by no frozen file → added to
  `lane3_star_gapfix.json` (JP ruling 2026-10-26; diff pending read). Verification = a fresh copy later,
  NOT a re-run on built2 (its gapfix verses are already patched, so a mixed result is expected there).

### G5 — PRE-SWAP GATE: the name-number class basis (JP ruling 2026-10-26: held, ruling required)
Live's `pn_hebrew_xref` classes and its proper-noun `words.strongs_base` were last written at the 8/6
retirement, on the **8/5** identity classes. The 9/6 Greek-header landing then moved 940 identity rows
between classes and **retirement was never re-run**. A rebuild's 8b.2 writes from the **9/6** classes,
so it changes what live serves on **501 slots** (JP-run read, G4 test copy vs fresh live copy): xref class
lemma-only→none 21 + none→lemma-only 498 = 519 rows, hebrew_base identical on every row; words
`H`→`*` 492 + `*`→`H` 9 = 501 (the other 18 have no Hebrew number, so `*` either way).
**No rebuilt database is swapped live until it is ruled which basis is right — the 8/5 classes (today's
serving) or the 9/6 classes (today's identity table).** Members: rerun the step-10 read B/C on any
rebuild copy. TODO carries the same item.

## §4 STOP conditions
- G0 diff ≠ 4,411 / 538 · G1a builder total ≠ 391,130 · any G2 placed row failing the second
  derivation · any non-fill row differing from the builder chain · G3 control not red on the
  pre-fill copy · any write outside `abp_surface` (+ the health_check floor line) in this lane.
- The pre-fill copy is load-bearing (the snapshot's only "before" side): it is not deleted while
  this lane is open, whatever the rotation rule says (memory `project_db_backups`, 9/6 trap).

## §5 Out of this charter (filed / flagged)
- **8b.3 ordering** (the name-header build reads abp_surface before step 9 rebuilds it) — TODO item.
- `ship_g707_targeted.py:176-178` carries an older 389,409 floor — one-shot ship script, not run here.
- `build_abp_surface.py:164` and `build_abp_translit.py:83` open the db without the
  `journal_mode=DELETE` + `busy_timeout` lines CLAUDE.md requires of read-write openers.
- `fix_lane3_star_merges.py:9-10` says it rides the post-rebuild chain; nothing calls it.
