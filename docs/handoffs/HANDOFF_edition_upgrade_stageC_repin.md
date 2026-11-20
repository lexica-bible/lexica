# HANDOFF — edition upgrade, stage C: re-pin 374 and close (written 2026-11-06)

> **DONE 2026-11-06 15:43 UTC — stage C CLOSED.** C3a′ OK · C3b `4d66afa3` (pin 374) · C4′ gate 1 7/7 · C5′ 23/23,
> all as expected; record at the end of `DRAFT_stageC_outline.md`. The "First task" below is spent; start from "Then".
> **Reviewer-subagent setup → `HANDOFF_edition_upgrade_reviewer_setup.md`** (findings to clear first).
> **Stage D current state → `HANDOFF_edition_upgrade_stageD_rekey.md`** (this file's Standing rules + Follow-up list still apply).

Successor to `HANDOFF_edition_upgrade_stageC_tail.md`. Every block, result and ruling of this stretch is in
`DRAFT_stageC_outline.md` (sections from "C6 gate 3 RAN" to "J DONE + G3R AS DECLARED"). Rulings: DESIGN §9.86–§9.89.

## State (11/6)
- **Built copy** `~/bible-db/bible_edupg_test_built_20261102.db` = post-tail + **R2** (§9.88 restore-digit repair:
  389 cells, other rows 625,920 unchanged) + **J** (§9.89 Joh 14:26 rows applied).
  - corrections: **374 active** / 23 retired / 6 superseded (same on `<src>`)
  - gate 3 re-run **AS DECLARED** (`gate3_rerun_20261106.log`): word-order 0 · content-other 1 (Job 3:3, FEED,
    §9.87) · Joh 14:26 clean · new on non-eligible 0
  - §9.52 punct members on built **607** = unchanged 205 + new-on-eligible 390 + changed-ops 12; **gone 24**
    (583 → 607 reconciled: +23 R2 restored-punct verses + Num 8:26 back to unchanged — list in DRAFT)
- **`<src>`** `~/bible-db/bible_edupg_test_20261101.db`: 374 active (the 2 `S-joh14:26` rows inserted, not applied — src
  is the build input).
- **Rollback copy** `~/bible-db/bible_edupg_test_built_pre_digits_20261105.db` (452 MB, = built before R2) — **keep until
  the swap** (ruling 11/6).
- **Code ref `e777f965`** (CI green). Docs HEAD after this handoff: see the git log. PA HEAD at last run: 6da053c9.
- Cert pin in code is still **372** — on built, check 4 reads 374 vs 372 until C3b lands (expected).
  Live check 4 reads red (51 vs the pin) until the swap — accepted, do not "fix".

## Next session's FIRST task — cleared conditionally by the ruling chat (run as printed; any mismatch = STOP, bring it back)
1. **C3a′ dump** — block in DRAFT "Block C3a′ — RE-PIN DUMP 374" (REF e777f965, script sha c463ee4a…). Expect
   `REPIN DUMP: OK - 374 = 372 + 2 S-joh14:26 - retired 23 - sha256 446fee35…`, exit 0. It writes
   `~/edition_upgrade_runs/abp_corrections_active_built_20261106.txt` + `.sha256` only if the dump = the local derivation.
2. **scp** (PowerShell, two separate lines — no brace expansion):
   `scp appssanding720@ssh.pythonanywhere.com:~/edition_upgrade_runs/abp_corrections_active_built_20261106.txt ./tests/fixtures/corrections/`
   `scp appssanding720@ssh.pythonanywhere.com:~/edition_upgrade_runs/abp_corrections_active_built_20261106.txt.sha256 ./tests/fixtures/corrections/`
   Check: sha256 = 446fee35b4080e522e5b2af19aca9dc3acc0b1c582ae56ba4c35ccd0fec539e3, 374 lines, LF.
3. **C3b commit** (scripts/tests only, `git commit -F`): `scripts/cert_invariants.py` PINS `abp_corrections_active`
   372 → 374 (comment: §9.89, 372 + 2 S-joh14:26, read off the built copy 2026-11-06, members
   `tests/fixtures/corrections/abp_corrections_active_built_20261106.txt` (sha256 446fee35...)) + the file + `.sha256`.
   Expect **3 files changed, 376 insertions(+), 1 deletion(-)**; any other file → STOP. Push. The old 20261104 file stays.
4. **PA pull** (no reload): `cd ~/bible-db && git pull --ff-only && git log -1 --format=%h`
5. **C4′ gate 1** — DRAFT "Block C4′" with `REF=__REPIN_COMMIT__` replaced by the C3b hash. Expect controls all FIRED,
   **7/7** (words 626,309, verses 31,237, check 4 = 374 all holding, em-dash 0), `GATE1 RESULT: 7/7`, exit 0.
6. **C5′ retired-row** — DRAFT "Block C5′", same REF. Expect `PASS 23/23 HOLD (corrected_value 18 - feed text 5)`, exit 0.
7. → **stage C closed.**

## Then
- **Reviewer-subagent setup is the first thing after stage C closes** (ruling chat).
- **Stage D (8b chain)** per `.claude/commands/rebuild-words.md` + DESIGN §2 gate table:
  - `tests/fixtures/edition_upgrade/declared_deltas.json` written BEFORE gate 2, per §9.64; **pn_binding first**.
  - §9.85: the −57 import_tipnr matches member by member (Hebrew-key vs Greek-key shown, not assumed) + named member
    rulings for the five cells **2Ki 9:31, Num 36:5 pos 13, Jos 5:15 pos 26, 2Ki 23:35 pos 7, Est 5:9 pos 12/13**.
  - **Gen 46:26 pos 19 = lane ③ hand repair pending at 8b.2a** (`scripts/lane3_star_fixes2.json`; built holds its exact
    "before" state; no lane-③ verse is on the R2 lists).
- **§9.87 punct re-freeze (607)** at the 9c fixture commit (replaces `punct_members_live_20261030.txt`, 241).
- **Follow-up list (out of this lane):** Job 3:3 "Maythe", Joh 3:15 "eternal. life.", the " )" set (2Th 1:10, Rev 2:9,
  Rom 4:17, Rom 9:1, Luk 2:23, Heb 7:11, Phm 1:12, Luk 2:35, Eze 26:7) — all FEED-attributed (CHECK 3), declared in gate
  3's record; the nine doubled-words; Split 80 → 84 attribution (OPEN by name past the swap — charter :235-237 set aside for it by JP,
  §9.205; un-muting the member log, build_words_from_abp.py :2773, is a later code change JP raises); **import_tipnr −57** (31,649 → 31,592; OPEN by name past the swap — charter
  :235-237 set aside for it by JP, §9.210, 11/20; the sum's +660 term has no members: no pre-8b copy of the 10/25 run exists; no rebuild
  or further read asked); **Mark 1:9 τῆς** (built 'of', 'Galilee,' on the next word; the app's τῆς blank and its Galilee cell "of
  Galilee," — accepted as built by JP, §9.210, 11/20, charter §4.10 set aside for this row; to be brought to the app's cells AFTER the
  swap; NOT a work order until JP raises it); the 11/2 held items (DESIGN §9.75/§9.76: the 117 near
  misses + Rom 9:29, verb chip blank this lane); the old-English punctuation members R2 surfaced.
  - **C4 joined-slot rows (§9.203, 11/19 — JP: "we can fix/split them later if it makes sense to"; NOT a work order, JP raises
    it):** (a) the **101 rows whose english is blank on built** — account v2 `docs/handoffs/drafts/STEP6AUD_C4_account_20261119.txt`
    (sha 60fb07b9…4b96): the 100 "orphan … -> None" lines + Joh 10:37 @2; the edition prints each "not + verb" as ONE joined slot and the
    build puts its English on the function word. On those rows the verb's chip is not drawn, it is not clickable, and it is out of its
    word's "renders as" list, the rendering filter and the English finder (DR "### C4 account v2 …" (2)). (b) **The 8 rows with
    greek_pos / bracket_id movement**: Exo 34:24 @14, Job 4:18 @5, Pro 30:11 @8, Isa 1:13 @18, Eze 20:39 @28, 1Ti 5:8 @10, 2Ti 1:16 @17
    (both columns → blank) and 1Sa 20:27 @27 (bracket_id blank → 4) — every cell IS in the step-4 declared list, STEP4-DELTA2
    words_cells (86e44c58…dafc; lines 18015-6, 30900-1, 45820-1, 25516-7, 19233-4, 5733-4, 10658-9, 4912, header = line 1), none in
    the named pre_8b → built list (DR :12569 on), so all from the build leg. (c) **Surfaces not read** for a blank-english row: the SEO
    word pages (views_seo.py :162-186), Ask-the-corpus (ai.py :574-582, :1131-1134), the search tab, the detail panel, and how
    `_normalize_gloss` folds a function word's phrase ("I know not"). Also: NO-EVIDENCE 1,814 → 2,140 on built — a read-out with no
    account (§9.201); no count on built was pre-registered for §4.4 — a lane GAP (§9.201).
- **10 reorder verses, eSword order confirmation before swap** (DESIGN §9.93 (b); owed before stage G, not
  before 8b): 2Ki 23:35 pos 6/7, Est 5:9 pos 12/13, Eze 20:14 pos 7/8, Gen 5:25 pos 1/2, Gen 5:26 pos 1/2,
  Gen 34:4 pos 1/2, Jdg 11:7 pos 6/7, Jos 2:4 pos 19/20, Jos 5:15 pos 26/27, Rom 9:29 pos 17/18 — whole-row moves
  into the edition's English order (census `strongs_pos_census2_20261106.log`); confirm each against eSword/ABP.
  **JP 11/20 (§9.214): the APP EDITION rules (charter §0.1); eSword is a witness only — only a verse where built
  matches NEITHER eSword NOR the app feed is brought (ruling chat + JP).** **CLOSED 11/20 (§9.216): eSword read set aside
  by JP; built = feed at all 10 pairs and a fresh read of the app pages = feed for all 10 (DR "### P2 — the 10 reorder verses").**
- **L9 split lint on built (charter §4.2) — OPEN by name, FIRST on the list after the swap** (JP, §9.214, 11/20;
  §4.2 set aside for the swap). Needs new code: a lint mode that replays the split through the app-feed transplant
  (`lint_split_wrong_slot.py` + its sizing partner `size_split_compounds.py`); new REF, PA pull, tests, a
  read-only block. NOT a work order until JP raises it. Detail: DR "### L9 on built — the code answer (§9.214)".
- **Joram H3088 ×27 — receipt owed** (DESIGN §9.94 (d)): frozen H3088 vs import_tipnr H3141 at 2Ki 3–12; no ruling
  or receipt found in the repo for the H3088 value.
- **Gen 4:18 Methushael H4967 — restore fixes built, note at gate 2** (§9.94 (d)): the edition's "Mathusala" made
  import_tipnr match Methuselah H4968; the 8b.1 restore puts the frozen H4967 back.
- **`/rebuild-words` step 12 (side-table builders) — runs on `<built>` before step 9** (JP rulings 11/7): code
  prerequisites LANDED `1ad10cec` (new code REF — PA pulls before gate 2); procedure text in `rebuild-words.md`
  step 12; record `docs/handoffs/DRAFT_rebuild_words_side_tables.md`.
- **Notes-store position anchors at the 20 moved words — before stage G** (§9.94 (d)): user notes anchor by word
  position (`static/src/12-notes-store.jsx:9-11`); a note on a moved word would point at its partner after the swap.

## Standing rules (unchanged, all still apply)
- CC drafts PA blocks; the ruling chat clears; JP runs. Every block printed IN FULL in chat. "Draft X now?" questions
  go to the ruling chat, never JP.
- Gate wrapper: `git diff --quiet "$REF" HEAD -- scripts tests` + `[ -z "$(git status --porcelain --untracked-files=no
  -- scripts tests)" ]` + `git merge-base --is-ancestor "$REF" HEAD`. Leave the three untracked PA files alone
  (`scripts/person_metav_link_residual.txt`, `person_metav_link_tier2.txt`, `tipnr_metav_link_residual.txt`).
- No `!` in pasted blocks except `!=` (use `repr()`, flags). Commit with `-F <file>`; prepend `.venv/Scripts` to PATH.
  No pushes of scripts/tests while a gated block waits.

## Tripwires banked this stretch
- **A gate's frozen-list Strong's = BUILD-time `strongs_base`;** later chain steps rewrite it (import_tipnr binds
  `*` → H-number, `import_tipnr.py:719`). Compare against `strongs`/`strongs_base` both (R1's first STOP, 11/5).
- **With `pipefail`, `big_output | grep -q` can report failure on a match** (grep exits early, the writer dies). Feed
  grep with `<<< "$var"`, never a pipe, in gate checks.
- **A `-journal` file beside a copy**: stop before writing; move it aside (never delete) before restoring a rollback.
- **A charter/handoff description of live rows is a claim** — read the rows (CHECK 3 repeated the charter's wrong
  "spirit holy, no digits"; live already had the digits).
- **Bracket groups read at their first member, sorted by greek_pos; a group's trailing punctuation floats to its
  last member** — test a digit fix through `reorder_english` before choosing it (Joh 14:26 option B failed on this).
