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
6. (if the decision in §3 uses two keys) the keys disagree.
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
**G3 — health_check floor = 395,003.** Control, red first: the check **fails on the pre-fill copy**
(391,130 → shortfall 3,873) and **passes on live** (395,003), both shown before the floor change is
trusted. It must also fail on a rebuilt table that lacks the fill (that is the trap it exists for).
**Wording flag for the reviewer:** the ruling says "above 395,003". The check fires when the count is
BELOW the floor (`scripts/health_check.py:138-140`), so a floor set strictly above 395,003 would fail
live today. This charter reads it as "raise it to 395,003" — the lowest floor that still catches the
loss. Confirm or correct.

---
## §3 Decision owed — the re-key method

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

**K2 + the second-derivation check (CC lean, for the reviewer's ruling).** Place by K2; accept a
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
