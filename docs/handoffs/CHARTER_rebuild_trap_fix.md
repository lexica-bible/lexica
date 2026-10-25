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
**SUPERSEDED 2026-10-26 by §9:** step 9 has no live-only input, so it now runs on the rebuilt COPY
before the swap (Path A). This section stays as the record of the first placement.

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
  `lane3_star_gapfix.json` (JP ruling 2026-10-26): gapfix pin 4 → 6 verses; both slots G3588, blank,
  bracket 2 spanning 6-8 / 14-16 (JP-run read).
**Step 11 (re-key dry run on built2): placed 4,411 · unplaced 0 · inserts 3,873 of 3,873**, all four
controls PASS (agree-strong 4,057 · agree-weak 354 = the identity floor). With G4 in the chain, every
fill row re-keys on a same-code rebuild. Verification = a fresh copy later,
  NOT a re-run on built2 (its gapfix verses are already patched, so a mixed result is expected there).

### G5 — RECORD, NOT A BLOCK: expect 519 xref / 501 strongs_base changes at swap
**JP ruling 2026-10-26: the 9/6 class basis is correct; live's 501 slots are stale.** A rebuild's 8b.2
(re)writes them from the 9/6 classes — that is the fix, not a regression. At any rebuild swap, expect vs
live: `pn_hebrew_xref` **519** rows changed (class only: lemma-only→none 21 · none→lemma-only 498;
hebrew_base unchanged) and proper-noun `words.strongs_base` **501** (`H`→`*` 492 · `*`→`H` 9). Record the
member counts at the swap; a different count is read member by member, a matching count does not block.
(History below: first filed the same day as a pre-swap gate pending the 8/5-vs-9/6 ruling.)

#### (superseded the same day) PRE-SWAP GATE: the name-number class basis
Live's `pn_hebrew_xref` classes and its proper-noun `words.strongs_base` were last written at the 8/6
retirement, on the **8/5** identity classes. The 9/6 Greek-header landing then moved 940 identity rows
between classes and **retirement was never re-run**. A rebuild's 8b.2 writes from the **9/6** classes,
so it changes what live serves on **501 slots** (JP-run read, G4 test copy vs fresh live copy): xref class
lemma-only→none 21 + none→lemma-only 498 = 519 rows, hebrew_base identical on every row; words
`H`→`*` 492 + `*`→`H` 9 = 501 (the other 18 have no Hebrew number, so `*` either way).
**No rebuilt database is swapped live until it is ruled which basis is right — the 8/5 classes (today's
serving) or the 9/6 classes (today's identity table).** Members: rerun the step-10 read B/C on any
rebuild copy. TODO carries the same item.

## §8 G1–G3 BUILT (2026-10-26) — copy dry run handed to JP, NOT yet run
Scripts: `scripts/snapshot_surface_fill.py` (part a, before step 9) · `scripts/restore_surface_fill.py`
(parts a+b + G1, after step 9) · `scripts/health_check.py` floor **389,244 → 395,003** (G3). Locked by
`tests/test_surface_fill_restore.py` (14 cases, both test lists): every reason and gate fires on a
planted case, and the floor reads WARN 1 at 395,002 / OK 0 at 395,003 / WARN 3,873 at 391,130.
`dryrun_rekey_fill.py` gave up its key rules (`key2_at` / `key1_at`) and its G0 check (`g0`) as the
ONE copy both new scripts call (its 7 tests unchanged, all pass). PA sequence + every expected figure:
`docs/handoffs/RUN_rebuild_trap_G1G3.md`.

**Calls made under JP's standing delegation (2026-07-12), each stated so it can be overruled:**
1. **Step 9 runs on the copy in this dry run — required for G1 to measure anything.** The build copies
   the whole db, so the rebuilt copy still holds live's 395,003-row table (fill included, census §2).
   Without step 9 the restore would find every slot already filled and G1 would read 395,003 for free.
   This does not move the real procedure: step 9 stays post-swap on live (§1). *(Superseded §9: the
   real procedure now runs step 9 on the copy too.)*
2. **The frozen snapshot stays out of git.** It carries 4,411 ABP printed forms + the slots' ABP English;
   the repo is public and ABP text is kept out of it (`abp_helps/`, `abp_app_html/` rule). It lives in
   `tests/fixtures/rebuild_trap/` (git-ignored) on PA, with a second copy scp'd to the local checkout;
   integrity = its `.sha256` file + a checksum pinned in `restore_surface_fill.py` after the first run.
3. **The restore refuses the live file.** This lane proves it on copies; wiring it onto live (where
   step 9 runs) is a separate change after this dry run's verdict. *(§9: wired by moving step 9 onto
   the copy instead — the refusal stays, permanently.)*
4. **G1b added (stricter than G1a):** with `--prefill`, the builder table must equal the pre-fill copy
   ROW FOR ROW, not just total 391,130 — counts are tripwires, members rule. Valid only for a
   same-code rebuild (a layout-moving rebuild drops `--prefill`).
5. **All or nothing.** Any unplaced slot, or G1a/G1b failing, means NOTHING is written (no partial fill).
   A table already at 395,003 with every slot holding its form reads ALREADY RESTORED; a mix fails.
6. **End-to-end oracle in the run sheet:** the restored copy's table must equal live's (`old3`) row for
   row, both directions `0|0` — independent of the restore's own checks.
Unchanged: reason 5 still cannot fire under these keys (§6 finding). Translit = romanize(form, lemma
of the NEW slot), then the build_abp_translit rule must change 0 rows.

**Run receipts (JP, PA, 2026-10-26; expected | actual):**
- A: HEAD `f266824a` · `key2_at` 1 · disk 7.6G (< 8.0G) · old3 copy `ok` · `delete` · 395003 — all match.
- B snapshot: G0 PASS (4,411 = 3,873 + 538 = the CSV) · O PASS · R PASS · rows 4,411 | 4,411 ·
  inserts/updates 3,873 / 538 | 3,873 / 538 · distinct 4,411 | 4,411 · name slots — | 22 · repeated
  number — | 1,486 · by class fill_pronoun 42 · fill_resolved 3,710 · fill_unlisted 32 · normalize 357 ·
  split_keep 89 · split_receive 68 · split_receive_name 21 · split_trim 92 — Lexicon-uncovered
  32 + 357 = **389** and covered **4,022**, both = the §6 figures. 455,812 bytes, sha256
  `d9435bdea8f3ec768053dbefb8c19a920905ed616bdfcb3b2a5f55cf9b4a295b` → **PINNED** in
  `restore_surface_fill.py`. Name slots 22 vs census Q6's 21: Q6 counted inserts only, so 22 should be
  21 inserts + 1 update — **confirmed** (JP awk read of the snapshot: 21 insert · 1 update). Checksum
  file `sha256sum -c` OK · 4,412 lines (header + 4,411).
- (disk stop: first build attempt hit "disk I/O error" — PA dashboard 9.9/10 GB while `du` read 8.4G;
  the two older test pairs were deleted; a CC-written cleanup line also deleted the finished first
  build output, so the build ran twice — both runs printed identical figures.)
- C build: words 626,305 · skipped 0 · flagged 6,882 · split 80 · PN-star A 1,505 + B 2,552 / 3,161
  refusals — all = the pins. finish_rebuild: Matched 31,649 · corrections applied 33 / skipped 0 · done.
- D 8b: 8b.0 CONTROL OK · SWAP 319 · REMOVE 22 · LEAVE 27 · HOLD 1 · applied 341 · 8b.1 restored 8,
  0 off record · 8b.2 split 3,671 / 10,236 / 12,182 / 4,412 / 1,977 (32,478) · 26,317 rewrites ·
  xref 32,478 · GLOB 0 · **8b.2a LANE-3 STEP: PASS fixes (9,0,0) · gapfix (6,0,0) · fixes2 (7,0,0)** —
  the owed fresh-copy proof of gapfix entries 5–6 (2Sa 18:31/32) · 8b.3 identity 32,478 · binding
  render 15,378 + HOT 68 · slot binds 102 / 0 refused. All = §7.
- **E step 9 on the copy: builder 346,111 + backfill 13,183 + PN backfill 31,836 = 391,130 = G1a.**
- **F floor RED:** pre-fill copy shortfall **3,873** · rebuilt copy without the fill **3,873**.
- **G restore dry:** table 391,130 · vs pre-fill copy 0 / 0 (G1b) · placed **4,411** (agree-strong
  4,057 · agree-weak 354, all listed in `~/rekey/restore_dry3.log`) · unplaced **0** · inserts /
  updates 3,873 / 538 · moved 0 · Lexicon pass 4,022 · uncovered 389 · every gate PASSES.
- **H restore on the copy: G1 = 395,003 exactly** · written 4,411 = snapshot form + new-slot translit
  (0 differ) · other rows 0 differ · new rows = the insert slots · translit rule changes 0 · quick_check
  ok. **End-to-end oracle: restored table vs the live copy old3 = `0|0`.**
- **I floor GREEN:** restored copy shortfall 0 · re-run: ALREADY RESTORED, 4,411 / 4,411.
- J G5 record (expected = G4): `pn_hebrew_xref` 519 | 519 · `pn_greek_identity` 21 | 21 · name-slot
  `strongs_base` 501 — all = the recorded figures; not a block.
- K snapshot second copy local: `sha256sum -c` OK · 4,412 lines · git-ignored (checked).
**VERDICT (CC, every line read against the pre-registered figure): G1, G2, G3 PASS on a same-code
rebuild copy; nothing written outside `~/rekey/built3.db` (+ the snapshot files).** Not yet done:
wiring the restore onto live's step 9 (it refuses live) — its own change, next.
**REVIEWER VERDICT (pasted by JP, 2026-10-26, quoted):** "Dry run accepted. Every figure matched
pre-registration; G1/G1a/G1b/G3 all proven red-then-green on a fresh copy; `0|0` end-to-end oracle;
G5 recorded and non-blocking. Lane G1–G3 is closed at 1062917f." New held items it logged: the live
wiring decision (what live serves between the step-9 drop to 391,130 and the restore to 395,003 —
a ruling before the live refusal comes off) · snapshot staleness after any slot-moving restore (gates
the edition-upgrade lane) · reason 5 unreachable (§6) · the 8b.3 ordering census still owed. The
pre-fill copy is now also the snapshot's "before" side: it stays past the nightly condition until a
re-freeze exists.

**Open, for the edition-upgrade lane (not this one):** the snapshot's old rows describe the layout it
was taken from. After a restore that MOVES slots, the next rebuild needs a fresh snapshot of the
restored table — and that snapshot's "before" side can no longer be the 10/25 pre-fill copy (the
step-9 output of that rebuild would be). On a same-code rebuild nothing moves and the frozen file stays
valid as is.

## §9 Wiring onto the live procedure (2026-10-26) — PATH A: step 9 + restore on the copy, before the swap
**JP ruling (2026-10-26, quoted from the lane brief):** "a live blip during the rebuild is acceptable.
Path is chosen by one fact you report, then you build without a further ruling" — the fact: does step
9 read anything that exists only on live bible.db? None → Path A (reorder; step 9 + restore on the
built copy; the restore keeps its live refusal). Exists → Path B (swap, then step 9 + restore on live
back-to-back; refusal replaced by the sha256 pin + G1a preconditions). Option 2 (one transaction) ruled out.

**Step 0 answer (CC, verbatim as delivered):** NONE — sequencing only. Step 9 is four scripts; every
input is either a table inside the database file it is given (`verses`, `words`, `lexicon`,
`dotted_lexicon`, `abp_surface` — `build_abp_surface.py:139-142`, `:176-181`;
`backfill_abp_surface.py:56-62`; `backfill_pn_surface.py:243`, `:260-266`; `build_abp_translit.py:85-91`)
or a separate file named on the command line (`--bh ~/bible-db/bh_scrape.db` — `build_abp_surface.py:117`,
`backfill_pn_surface.py:190`). The rebuilt copy carries every one of those tables (the build copies the
whole db, `build_words_from_abp.py:2054-2058`). No step-9 script hard-codes the live path, and the
modules they import open nothing at import time (`lxx_align`; `build_pn_greek_identity` via
`backfill_pn_surface.py:44` — its `DB`/`BH` defaults are strings used only in its own `main()`, which
does not run on import). Proven in practice: the 10/26 copy dry run ran step 9 on `~/rekey/built3.db`
and got 391,130 = G1a (§8 E). History of the placement: step 9 was appended after the swap step when
`abp_surface` was new (`6e815b89`, 2026-06-15 — "RE-RUN … (like import_tipnr.py)", no file named, no
reason given); the build's closing text put the surface builder + translit on the COPY before the swap
(`3f4f5038`, 2026-06-27); `finish_rebuild.sh` said "after a real swap" (`9aac2c6d`, 2026-07-03); §1
(`5fe687d4`) settled on live because that is what the 7/16 and 8/23 runs did — practice, not a
dependency. The one ordering constraint is internal to the copy: step 9 must follow 8b (translit reads
`words.strongs_base`, which 8b.2 rewrites; the PN backfill reads `is_pn` + English, which 8b.2a
repairs) — the order the 10/26 dry run already used.

**Path taken: A.** New run order (`/rebuild-words` RUN ORDER line): 0 → 1 → **1a snapshot check** → 2
build → 3 finish → 8b.0–8b.3 (incl. 8b.2a) → **9 surface rebuild → 9a restore → 9b floor + oracle, all
on the copy** → 4 → 5 → 6 → 7 → **8 swap** → 10 → 11. Live is never served without the fill: the
swap replaces one 395,003-row table with another. Step numbers kept as labels (other docs cite them).

**What changed (this commit):**
- `/rebuild-words`: RUN ORDER line; new step 1a; step 9 re-written for the copy (`<built>` on every
  command), with 9a (restore, dry run → verdict → apply) and 9b (floor + `0|0` oracle vs live); step 8
  moved below 9b; step 6 notes it runs after 9b (before step 9 the copy's floor passes for free).
- `scripts/snapshot_surface_fill.py --check` (step 1a): the frozen file must pass its `.sha256`, equal
  the pin in `restore_surface_fill.py`, and equal what `--src` (a fresh copy of live) yields **byte for
  byte**. Pass → `SNAPSHOT CURRENT`, nothing written. Else `STALE SNAPSHOT`, naming the slots that
  differ (or the G0/O check that failed) — never overwritten; a re-freeze stays a ruling (`--replace`,
  without `--check`). Missing file under `--check` stops too. Default mode unchanged.
- `restore_surface_fill.py`: live refusal KEPT (docstring + message now say why: it only ever runs on
  the copy at 9a). No logic change.
- Print text only: `build_words_from_abp.py` closing text and `finish_rebuild.sh`'s last echo now say
  step 9 / 9a / 9b run on the copy before the swap (were "after the swap, on live").
- `docs/claude/data-model.md` abp_surface paragraph; census §2 pointer.
- Tests: `tests/test_surface_fill_restore.py` +7 cases (`SnapshotCheck`): current on a matching copy
  (writes nothing; also against the pin) · stale when a fill slot's old English changed (G0 still
  passes — the byte compare catches it) · stale when a fill form changed (G0's CSV check) · stale when
  live's table gained a row (G0 count) · refuses a file that is not the pinned one · refuses a missing
  file and `--check` with `--replace`. Every stale case asserts the frozen file is byte-unchanged.
  Existing 15 + `test_rekey_dryrun.py` 7 unchanged and green; 22 + 7 total.

**Live RUN sheet:** `docs/handoffs/RUN_rebuild_trap_live.md` — same-code rebuild, every figure marked
PRE-REG (measured 10/26), CHECKLIST (checklist figure, never measured on a rebuilt copy: step 6
audits, full health report) or FIRST READ (8b.3 gates, word-key compare). Pre-registered from the
dry runs: snapshot CURRENT `d9435bde…` · G1a 391,130 → G1 395,003 · placed 4,411 / unplaced 0
(4,057 strong · 354 weak) · floor red 3,873 → green 0 · restored table vs pre-swap live `0|0` · G5
519|519 · 21|21 · 501 · words english/english_head/greek_pos/strongs/is_pn 0 · bracket_id 0 (the owed
half of held item 3). Hard STOP after block I (pre-swap compare) for the verdict; block J (swap) is
the only live write.

**Found while wiring (flagged, not changed):**
- **Step 11 has the old step-9 shape.** The build never writes `words.english_head_norm` (its INSERT
  list, `build_words_from_abp.py:2154-2157`) and the finder only checks that the column EXISTS
  (`views_lexicon.py:100-108`), so between the swap and step 11 the ABP English finder would fold on
  blank values for every rebuilt row. Not measured on PA. Its own check (same Step-0 question) before
  the next live rebuild.
- **The site writes AI caches into bible.db** (`ai_search_cache`, `core.py:341`; LSJ/ABP synthesis,
  `views_lsj.py:467-470`). Rows written between the copy (A2) and the swap are dropped by the swap and
  redraw on the next ask. True of every file-swap rebuild; the run sheet records the count before J.
- 8b.3 ordering (held item 4) unchanged: 8b.3 still reads the copy's carried live surface table before
  step 9 — the same input it had before this reorder.
- `~/abp_surface_fill_dryrun.csv` is a G0 input of step 1a and was missing from the PA keep list —
  added.

## §10 LIVE REBUILD — RUN (JP, PA, 2026-10-26 16:37–18:12) — SWAPPED, every figure matched or ruled
Sheet `RUN_rebuild_trap_live.md`, HEAD `a1998f0e`. Receipts (expected | actual = match unless noted):
- **A / A2:** inputs present, snapshot `OK` · dashboard 7.8 / 10 GB · live copy `ok` · `delete` · 395,003.
- **B (1a, first PA run of `--check`):** G0 4,411 / 538 · O · C byte-identical · sha256 `d9435bde…` both
  sides · `SNAPSHOT CURRENT`.
- **C:** build 626,305 · 0 · 6,882 · split 80 · PN-star 1,505 + 2,552 / 3,161 (article-slot pass 923 /
  411 recorded, unpinned) · finish: import_tipnr 31,649 · corrections 33 / 0 · `done`.
- **D (8b):** 8b.0 CONTROL OK, 369 = 319 / 22 / 27 / 1, applied 341 · 8b.1 Cushi 8 → 0 · 8b.2 classes
  exact, 26,317 rewrites, xref 32,478, GLOB 0 · 8b.2a PASS (9,0,0) (6,0,0) (7,0,0) · 8b.3 identity 32,478,
  render 15,378 + HOT 68, slot binds 102 / 0.
- **8b.3 gates (first read):** unfindability PASS 0 / 0 · two-derivations 10 / 10 PASS · header gate C
  PASS, **A + B FAIL — attributed member by member, ABORT overridden by the reviewer for this run:**
  gate A = `pn_binding` 3 rows, the 3 Michaiah binds (2Ki 22:12, 2Ch 17:7, Neh 12:41) `ruled /
  spelling-equiv` → `fuzzy`, same entity (checklist-predicted); `tipnr_entities` / `abp_surface`
  byte-identical; words 626,309 + verses 31,237 both sides. Gate B = 21 header rows (the held 21): 18
  page-attested fallbacks + 1 glued cure + 2 Sheshach violations; its 4 PIN lines (17 / 20 / 94 / 30 →
  0 / 0 / 1 / 29) are the 9/6 landing's own counts and cannot recur on a post-landing compare (by
  design). Root: gates A/B were built for the 7/30 header-only lane — re-scope for full rebuilds is a
  logged follow-up.
- **Sheshach — REVIEWER RULING:** the header follows the page — Σεσάκ at Jer 51:41 (slot 1), Σησάχ at Jer
  25:26 (slot 25) (live had Σησάχ on both, `surface`; the rebuild carries each verse's printed form,
  `lemma-only`). Rebuilt rows ship. **Held item 1 CLOSED on content.** Label change accepted for the
  swap; NEW held: trace what `surface` vs `lemma-only` changes on the card, and whether a page-matching
  header should carry `surface`.
- **E (step 9 on the copy):** 346,111 + 13,183 + 31,836 = **391,130** (G1a).
- **F:** floor RED 3,873 on the pre-fill copy and the rebuild.
- **G (9a):** dry run 4,411 placed (4,057 / 354), 0 unplaced, 3,873 / 538, moved 0, G1b 0 / 0, Lexicon
  4,022 / 389 · apply **G1 395,003 exactly**, 0 rows differ, translit rule 0, quick_check ok.
- **H:** floor GREEN 0 · ALREADY RESTORED · GLOB 0 · full health report 0 warnings / 0 errors · tier 2
  92.26% · six step-6 audits identical on the live copy and the rebuild: bracket genuine 3 · cross
  function-anchor 0 · LORD REPAIRABLE 0 · REPAIRABLE-NOUN 0 · split-flip 0 · A1 177 (checklist "≈ 2" /
  "≈ 176" were stale — re-declared to 3 / 177).
- **I (vs live, read-only):** surface **0|0** (end-to-end oracle) · xref 519|519 · identity 21|21 · word
  keys 0|0, 626,309 both sides · english / english_head / greek_pos / strongs / is_pn / **bracket_id 0**
  (held item 3's bracket half CLOSED) · strongs_base 501, all name slots · AI cache 0|0|0.
- **J (reviewer-cleared):** swap 18:06; old live → `~/bible-db/bible_pre_trapwire_swap.db` (442,912,768
  bytes, the rollback) · deploy.sh: up to date, tests passed, API reload, sweep 200 ×5.
- **K:** live 395,003 · quick_check ok · `delete` · floor GREEN 0 · disk 7.03 / 10 GB. First two
  health_check runs hit `database is locked` on the words checks: each site worker's first-request
  warm-up writes the AI cache (`app.py:430-458`) and health_check waits only Python's default 5 s
  (`health_check.py:30`). Re-read the 4 words checks directly with a 60 s wait: bare strongs_base 0 ·
  exact dupes 0 · misalignment 0 · fragmented over 190 0.
- **G5 recorded at the swap:** `pn_hebrew_xref` 519 · `pn_greek_identity` 21 · name-slot `strongs_base` 501
  moved — the 9/6 class basis (ruled correct), not a block.
**Not done in this run:** checklist steps 7 (served spot-checks), 10 (two-ending regen) and 11
(`build_rendering_norm.py`, the flagged after-swap item). Follow-ups logged: header gate A/B re-scope ·
health_check busy wait · the build's closing text calls its source "live" when the source is a copy ·
`surface`/`lemma-only` label trace · two old `bible_pre_pnstar_*` rollback copies (ops.md rule 1).

### §10a The post-swap tail — RECORDED EXCEPTION (JP rulings after the census, verbatim)
- "Order this run: 11 → 7 → 10. Step 11 never runs within 60 s of a reload."
- "Steps 10 and 11 are re-homed pre-swap in the checklist (11 on the copy after 8b, 10 reads the copy,
  both before 9). This run is the recorded exception since rebuilt.db is live."
- "build_rendering_norm.py opener gets the CLAUDE.md timeout + journal-mode lines before any live run."
- "Step 10: diff script output vs current static/src/00b-two-ending.jsx before any paste; identical → no
  paste/deploy, record "unchanged"."

**Why the exception:** the 10/26 run swapped `rebuilt.db` into place before steps 10/11 ran, so there
is no post-8b copy left to run them on (`~/rekey/pre_rebuild.db` is the OLD words). This one time, step
11 writes live and step 10 reads live. Census basis (CC, repo-only): step 11's value per row comes only
from that row's `english_head` through `number_fold.normalize`; the build keeps the column but never
fills it (`build_words_from_abp.py:2111`, `:2154-2157`); the column existed on live before the swap
(census Q2: `idx_words_ehnorm` on live `words`); the finder uses it whenever it exists
(`views_lexicon.py:100-108`, `:943-947`) → predicted live count **0 non-blank / 626,309 rows** —
the ABP English finder matching nothing until step 11. **Live count (JP, PA, read-only, 18:51):
`0` non-blank / `626309` rows — expected 0 / 626,309, MATCH.** The column is present on live (the
read did not error) and blank on every row. Step 11 on live gated by JP next.
**Step 11 PRE-REG (JP, PA, read-only, 19:03 — rows the script will touch | rows with a non-space value):**
words `354946 | 354946` · kjv_words `790685 | 790685` · bsb_words `386063 | 386063`. Expected run
output: no "added column" line · `recomputed 354,946` / `790,685` / `386,063` · After: `354,946` /
`790,685` / `386,063` rows normed (kjv/bsb: a surplus would be an old value on a now-blank row —
attributed, not ignored) · distinct-renderings/keys figures FIRST READ. After-read of non-blank
`english_head_norm`: 354,946, lower only by heads made of quote marks alone (normalize → '').
Served check: ABP English finder "magistrate" → θεός G2316 (Exo 22:28 "magistrates").
**Step 11 RUN (JP gate cleared; JP, PA, 19:05–19:08, `git pull` a1998f0e → 7b4b5e95 — the new opener
lines rode the pull — then `python scripts/build_rendering_norm.py ~/bible-db/bible.db`, no reload).
Expected | actual:** no "added column" line | none · recomputed words `354,946 | 354,946` · kjv
`790,685 | 790,685` · bsb `386,063 | 386,063` · After rows normed `354,946 / 790,685 / 386,063 |
354,946 / 790,685 / 386,063` — **all MATCH**. FIRST READ (distinct renderings → keys): words 12,739 →
10,990 · kjv 13,826 → 11,296 · bsb 100,241 → 89,295.
**Served finder check (CC, read-only GET `www.lexica.bible/api/lexicon/english?q=magistrate&corpus=abp`,
no reload since step 11): PASS** — θεός G2316 listed, ABP gloss `magistrates` count 2, flagged as a
fold match. The 2 = Exo 22:28 + 1Sa 28:13 ("I see magistrates" G2316), both read in `abp_texts/`
(abp_exodus.txt:609, abp_1samuel.txt:743). Also folded singular + plural on one word: δικαστής G1348
`magistrate` 6 + `magistrates` 5; κωμάρχης G2967.1 `magistrates` 1. Before step 11 the ABP side of
this call matched nothing (all norms blank). After-read of non-blank `english_head_norm` (JP, PA,
read-only): **`354946` — expected 354,946, MATCH** (no quote-only heads). **Step 11 CLOSED.**
**Step 7 (CC, served site, read-only API GETs — no word card opened, so no AI summary drawn):**
- Eze 31:9 — `/api/verse-words/Eze/31/9` pos 15 "were jealous of" → G2206 ζηλόω (bracket 2). **PASS.**
- 1Chr 1:1 — word row pos 0 "Adam," = `G76` Ἀδάμ, is_pn (Greek-keyed since R-2, by design); the card's
  identity read `/api/pn/greek-identity …pos=0` = `hebrew_base H121`, source tipnr; `/api/metav/entity/Adam
  …pos=0` = bound, exact, metaV person 78 "Adam". **PASS** (the checklist's "→ H121" is the card's
  Hebrew line, not the word row).
- Jer 51:41 / 25:26 — identity lemma Σεσάκ (pos 1) / Σησάχ (pos 25), both `lemma-only`, H8347 — the
  reviewer's Sheshach ruling as served. **PASS.**
- 1Ch 13:10 — data: pos 1 "was enraged" θυμόω + pos 2 "the LORD" κύριος, same bracket 1 (greek_pos 2 /
  1). **Data PASS; the rendered chip NOT checked by CC** — see the loop below; JP eyeballs it.
- **Found (out of lane, flagged):** opening `https://www.lexica.bible/?b=1Ch&c=13&t=abp` (the /read/
  pages' deep-link shape) in CC's fresh built-in browser (no saved position, narrow/mobile layout) put
  the reader in an endless loop — `/api/chapter/1Ch/13` and `/api/chapter/Gen/1` alternating, 56,000+
  requests to live in a few minutes, page stuck on "Loading…". Tab closed. **JP opened its own lane
  ahead of step 10; findings (reproduced locally, dated to `bc47330c` 2026-06-28 — not the swap) in
  TODO.md "reader deep-link request loop".**
- **JP ruling after step 7:** items 1–3 accepted on data-level checks (loop risk); 1Ch 13:10 pending
  JP's look at the reader's Chip view. Step 10's read-only diff may run now; no paste/deploy until
  the loop lane reports.
- **Step 10 (JP, PA, 19:10, read-only — `build_two_ending.py ~/bible-db/bible.db`, output from the
  `// AUTO-GENERATED` line diffed vs `static/src/00b-two-ending.jsx`): `IDENTICAL` → "unchanged", no
  paste, no build, no deploy.** Header: classes (lemmas) two-ending 368 · three-ending 283 · no-lsj 41 ·
  noun 68 · unknown 13; soften OT 80 words / 441 displays · NT 208 / 396 (the file's own lists count
  80 / 208 — CC). **Step 10 CLOSED.** Consequence for the loop lane (JP ruling 3): there is no step-10
  deploy to ride, so a loop fix deploys on its own.
Done before any live run: `build_rendering_norm.py` opener now sets `journal_mode=DELETE` +
`busy_timeout=60000` (was the 5 s default — the 10/26 "database is locked" class). Checklist
`/rebuild-words` re-homed: RUN ORDER `… 8b.3 → 11 → 10 → 9 → 9a → 9b → 4 → 5 → 6 → 7 → 8`.
Receipts (step 11 count, step 7 spot-checks, step 10 diff): _to be recorded here._

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
