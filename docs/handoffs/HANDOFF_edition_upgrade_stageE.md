# HANDOFF — edition upgrade, stage E (written 2026-11-08)

Successor to `HANDOFF_edition_upgrade_gate2.md` (gate 2 green and closed; stage D CLOSED). Standing rules and the
follow-up list in `HANDOFF_edition_upgrade_stageC_repin.md` still apply. Rulings only in `DESIGN_q2_build.md` §9
(sole register, latest **§9.207**). Order of the remaining steps: charter `CHARTER_edition_upgrade.md` §6 +
`.claude/commands/rebuild-words.md`.

## SUCCESSOR START (11/21 — the swap is cleared pending the put-back block) — OPEN HERE
**UPDATE 11/21 later - PB and PB0 are CLEARED (DESIGN 9.230); the swap can be scheduled; JP sets the hour.** PB0 (read-only) runs before P6R; PB (the put-back) runs ONLY if the ruling chat rules it on a P6B or P6C log it has read. Sources: docs/handoffs/drafts/P6_harness/block_pb.sh 0593313eac3994eabf885658cc8d202efd1c282c4e0ebfb5410ba5e77d9b534d and block_pb0.sh 5bdca89b198fd8081699de13e8dcb6a8e1d5dbaa05d2f6ce6a0a623609f0922a; both in full in DR "## PB - THE FILE-ONLY PUT-BACK". **The sequence, as cleared:** the program uploaded -> P6A -> PB0 -> the push (the swap commit; re-check below) -> P6R -> Disable -> P6B -> Enable + Reload -> P6C -> P7 (its own block, NOT yet drafted or cleared). **Terms for the day:** P6R and the Disable are NOT started between 11:00 and 14:30 UTC (6:00-9:30 AM Eastern); P6R not pasted until PB0 DONE; no pull, deploy or edit on PA between PB0 DONE and P6B; PB0 is not the block waiting when the swap commit is pushed; no deploy after anything but P6B DONE; any STOP or CHECK goes to the ruling chat first (a PB STOP: the web app left as it is); P6B's and P6C's logs go to the ruling chat by cat, P6A's / PB0's / P6R's CC reads against their DONE lines; after a PB DONE and Enable + Reload, JP says what the site shows and CC reads the public pages. The 8-path diff term is MET (DESIGN 9.231); at commit time the 8-path git diff must hash 003bb52f...83ee or there is no push and it goes to the ruling chat. Nothing else is owed before JP sets the hour. P7 was HELD (DESIGN 9.232: its code guard missed the three files of adfb8ac5 that the swap-day pull also brings) and is CORRECTED, back with the ruling chat, NOT cleared: block 527722ce6b7363ae39ebc958e8089815bceafdae2fa610c16a58c727235163a1 (source drafts/P6_harness/block_p7.sh, __XP7__ filled), program p7_check.py 911f5ec9d62c6bf3e58bc2eafd11513f1fda653333da88b66b49f751f8624a36 unchanged (local copy C:\Users\JP\edition_upgrade_runs\p7_check_20261121.py); 34 tests on the REAL history (run_p7.sh -> tests_p7.out); reviewer ESCALATE x2, no defect in the changed lines; record DR "### P7 HELD (9.232)". The eleven points are ruled (9.232). **The swap is not started until P7 is cleared; P7 is cleared before P6R is pasted.** PB: a revert pulled early has NO cleared path (9.232 corrects 9.230 point 3). Both programs (p6_check, p7_check) are uploaded and hash-checked before P6A. Before the push CC prints `git rev-parse HEAD:<path>` for the block's eleven pinned files against its PINS; a miss = no push. NEXT: the ruling chat's clearance of the corrected P7; register it. The 'FIRST task' paragraph below is DONE.
**Where it stands.** Charter §6 step 8 (the swap, the only live action). Every pre-swap read is done and ruled (§9.213-§9.229). The swap
and rollback blocks are **CLEARED AS PRINTED (§9.229), held on ONE gap**: the put-back block below. Nothing has run on PA for the swap;
live is untouched; the site is up.
**Your FIRST task — the put-back block (§9.229 (1); owed BEFORE P6R runs).** A file-only put-back for the two states RB0 refuses:
(a) P6B ending CHECK after the renames, or "NOT IN PLACE" / "NOT the pre-swap file"; (b) P6B DONE but P6C failing before PA is on the swap
commit. It must:
- read `~/edition_upgrade_runs/p6_swap/rollback.txt` (P6B writes it before the first rename: line 1 the rollback file's name, line 2 live's
  full sha just before the move);
- keep whatever sits at bible.db under a `bible_pre_` name (backup_db.py :63 skips `bible_pre_*`; a name without it would be backed up nightly
  — reviewer D1 on RB1);
- put the rollback file back as bible.db and show its sha = line 2;
- leave NO deploy to run. CC's `git revert` of the pushed swap commit follows before any other deploy.
- Same form as RB1 (DR "## P6 — THE SWAP and its ROLLBACK", :18749 on, every block in full): still-file hold, `mv -n`, put-back on a miss,
  CHECK = the site stays disabled.
- Test it on the WSL homes for EACH state above (the harness: docs/handoffs/drafts/P6_harness/ — mkhome_p6.sh, run_p6.sh; WSL clone at
  ~/gate4/repo = d34d6723; Git Bash needs `MSYS_NO_PATHCONV=1 wsl -e bash /mnt/c/...`).
- Then the reviewer (it will ESCALATE: a write to live), then the ruling chat clears it. Then the swap can be scheduled.
**The eight cleared shas (§9.229):** program `p6_check_20261121.py` 3dfe1600963b792bdaff114f132eb0675b5794eb626ae8ab88dc1fec1d8208e6 · P6A
2ed1ccc6560dad1c167323c1d59e608be54ba00cbcfb6abeac75aeac053a8284 · P6R f822d62437750c13c7ef13a528d7f0cbb34c6e7cce3bb1629ebc24530028e630 ·
P6B 959daceebfad8e82496126d15d91cb88effaa557f303d201c2106135787fd54f · P6C 596eca57000c45b8d62433fc4581aa4948efb136afd82e4d1eef0ad7dbad1e70 ·
RB0 73939c63dbe5efce7d5e93ad8b4a628b4544c924e0bf04c42c56f0861de70ada · RB1 8c60304bbb12a55b179a0dd05681cec65af28b3cd194057161d6da5cb9526af6 ·
RB2 a67c31b9e21378f76cd5d6eb2ac12a4289fe74f97d7c1b7d7a847ee29190cc40. The program's local copy is `C:\Users\JP\edition_upgrade_runs\p6_check_20261121.py`
(JP uploads it to `~/edition_upgrade_runs/` before P6A). Each block is printed in full in DR under "### Block P6A (sha256 …)" etc.; the
source files (with __XP__ unfilled) and the program are in `docs/handoffs/drafts/P6_harness/` with the tests; filling __XP__ with the
program's sha reproduces each cleared sha (CC checked all seven, 11/21). Re-hash before printing any block.
**THE SWAP COMMIT — NOT committed, NOT pushed.** The working tree holds exactly the cleared change set (8 paths: rebuild-words.md, ai.py,
audit_phrase_gloss_underdist.py, cert_invariants.py, health_check.py, test_surface_fill_restore.py, and the two UNTRACKED fixture files
`tests/fixtures/corrections/abp_corrections_active_built_20261121.txt` + `.sha256`). **Do not touch them; commit nothing else that sweeps
them up — commit docs by named paths only.**
- Cleared: swap_commit.diff 002f2791…41f6 (seven paths) (§9.227).
- The full 8-path change set: `docs/handoffs/drafts/SWAP_COMMIT/swap_commit_full.patch` 003bb52f…83ee.
- **The term (§9.229), already stated in DR:** the full set = those seven hunks unchanged plus the fixture .txt hashing 005da9f3…3048, and
  nothing else. CC proved it 11/21: the full patch minus the .txt section equals swap_commit.diff byte for byte; the .txt section's 375 added
  lines hash 005da9f3…3048.
- **At P6 time, between P6A DONE and P6R:** `git add -N` the two fixture paths; the 8-path `git diff` must hash 003bb52f…83ee. Then commit
  those 8 paths ONLY with `git commit -F docs/handoffs/drafts/SWAP_COMMIT/commit_message.txt` (the subject must start "edition upgrade: THE
  SWAP COMMIT": P6B, P6C and RB0 check it). Then push (on P6's clearance); no other deploy between the push and the swap.
**Pins:** built `~/bible-db/bible_edupg_test_built_20261102.db` full sha **d2c8603b4700d6dce089b688c5e00e8a3fdec879eea96bef5a6ce7cd09ca1523**
(§9.222 (1)); src 5da9bb95…7e01; LIVESRC words 626309/1ce75b22…5b26, verses 31237/5717b045…21ae; PA HEAD 1d5e34ee, scripts/tests = REF
d34d6723 (P6A / P6R / P6B check it).
**The sequence:** P6A (site up) → CC commits + pushes the swap commit (PA does NOT pull) → P6R (site up) → JP DISABLES → P6B (the window) →
JP ENABLES, then RELOADS → P6C (deploy.sh) → P7 (read-only, ≥ 60 s after the reload; its own block, not yet drafted: cert_invariants 7/7 at
375 / 1; health_check floor 395,014; the G5 read with "surface" labels and the six pn_hebrew_xref keys vs §9.95's six verses (§9.223); Part
B on the served site) → P8 (the 9c snapshot --check on swapped live) → P9 (the next nightly). Rollback (only if ruled): CC pushes the revert
→ RB0 → Disable → RB1 → Enable + Reload → RB2.
**The window rules (§9.215, §9.228, §9.229):** the hour is JP's, low traffic, never inside 13:00-14:30 UTC (the 13:30 health + backup
tasks); while the app is disabled visitors see the browser's certificate warning (PA's wildcard certificate), accepted. A P6B / RB1 STOP
saying "nothing moved" → JP ENABLES at once, then the log goes to the ruling chat. A CHECK, "NOT IN PLACE" or "NOT the pre-swap file" →
the site STAYS disabled and the log goes to the ruling chat at once. P6A's and P6R's logs CC reads against their DONE lines; P6B's and
P6C's go to the ruling chat by cat. Any re-run = the same block with _r2 on its log (and P6A's folder), brought as a pair with the block
that reads that log (§9.229 Q-c). If RB0 / RB1 STOP before the move, every deploy is held until ruled (Q-d).
**Carried OPEN by name past the swap** (DR "### Carried OPEN by name past the swap"; stageC_repin follow-up list):
- Job 3:3 content-other (new on built; it goes live with the swap).
- Split +4; import_tipnr −57; Mark 1:9 τῆς (fix after the swap).
- The C4 joined-slot rows; the stray files in PA's checkout.
- **L9 on built (first after the swap, §9.214).**
- The Q6 redraw pass for summary / xref / pn / chrono (§9.226): those serve old-English answers until it runs.
- Built Strong's vs the feed's (§9.218); Jdg 11:7 1473 vs 5210 (§9.217).
- rebuild-words step 8's 10/25 G5 figures to mark as 10/25-only (§9.227 point).
- The P4 live copy (`~/edition_upgrade_runs/p4_live_tables_20261121/live_copy_20261121.db`, ~460 MB) kept until a removal block is ruled.
**JP's standing instructions (11/21):** questions go to the ruling chat, not to JP (CC + reviewer recommend; the ruling chat rules; JP is asked
only what cannot be done without him); and NO confirmation-only notes to the ruling chat — register a ruling and carry on; send only a block
or commit for clearance, a log to rule on, a question, a finding, or an answer a ruling asked for, leading with what needs ruling (the
"## STANDING (JP, 11/21)" section below).

## STANDING (JP, 11/21) — ruling-chat traffic
The ruling chat asked that this sit beside "the 11/21 instruction on questions to JP"; CC found no such instruction written in this handoff
or the register, so it stands here on its own (CC to place it beside that one once its text is in the record). JP's standing instruction (via the ruling chat, 11/21):
1. Do NOT send a note to the ruling chat only to say a ruling was registered. Register it and carry on; the register is the record (JP carries
   each note across by hand).
2. Send to the ruling chat ONLY when something needs it: a block or commit for clearance, a log to rule on, a question, a finding, or an
   answer the ruling asked for.
3. When sending, LEAD with what needs ruling. Leave out the "registered as ruled" recap and the repeated STILL OWED list unless it changed.
4. If a ruling's wording was wrong or cannot be registered as given, say so — that is a question, and it goes.
5. The ruling chat does not reply to a pure acknowledgement; its silence on one is not a hold.

## SUCCESSOR START (11/19 end; charter §6 STEPS 4 + 5 + 6 PASSED — §9.193, §9.194, §9.204; next = step 7) — open here
- **11/21 Q2 code read + Q3 PA-help read RECORDED (DR "### Q2 — the AI cache code read", "### Q3 — PA's Disable / Enable"); both to the ruling chat as questions.** Q2 pick: bump 48→49 (search only), rest by Q6 post-swap pass. Q3: PA help silent → a 1-minute Disable/Enable test by JP before P6.
- **Step 6 PASSED (§9.204)** on `step6_audit_20261119.log` as disposed: C4 by JP's ruling (a) (§9.203; built 747, account v2); Job 3:3
  content-other OPEN; bracket order + the §4.2 L9 split on built's words NOT measured by this run; read-outs as §9.201; the §4.4
  pre-registration GAP recorded. Nothing re-run, re-pinned or rebuilt; live not touched.
- **NEXT = charter §6 step 7, CC's to bring** (charter §6: "7 spot-check (1Ch 13:10 chip order, Eze 31:9, 1Chr 1:1; add Gen 1:21 'sea
  monsters', Mark 1:9)"; rebuild-words step 7). Read the charter step-7 line + rebuild-words step 7 first; the form is a proposal to the
  ruling chat (what is checked, on which copy, how, expected), then a read-only block. **Step 7's plan goes to the ruling chat before
  anything in it runs on PA (§9.205).**
- **11/20 CHARTER §6 STEP 7 PASSED (§9.212) on STEP7A's log (READ; H121 + ζηλόω read from cells on both copies). NEXT = the STEP-8 PLAN (the swap; the only live action) — CC brings a plan before any block; what it must carry is listed in §9.212.** Owed: Eze 31:9 @22 lemma line from check.out (paste showed 2 unreadable chars) when the run folder is next copied down; the declared-list lines for Est 5:9 @13, Jos 5:15 @27 + 5 MOVED verses.
- **11/21 §9.225: abp_corrections trace CLOSED (P4B taken on CC's report). If a ruling later leans on P4B's lines, its log goes to the ruling chat by cat first.** Owed before P6: Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/21 P4B RAN: DONE — the 23 traced: retired on src/built = exactly the live-active-only members, ids = the delta's 23. abp_corrections fully accounted for (346 new, 23 retired, 34 same, 0 live-only).** Owed before P6: Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/21 §9.224: Q1 RULED — the 54 summaries DROP (JP: "make the calls bro idk"). P6 prints final dropped counts, site stopped; any other differing table beyond the four = STOP.** Owed: P4B result, Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/21 §9.223: item (7) answered, no table unruled.** CARRIED TO P7: its G5 read prints the 6 xref keys vs §9.95's six verses; labels read "surface".
- **11/21 P4 RULED (§9.222): built sha d2c8603b…1523 = P6 pin; live = src; G5 for P7 accepted; 54 summaries = JP's call; item (7) answered — all seven tables have a register line (DR "### P4 RULED").** Owed: P4B log (the 23), Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/21 P4 log HELD (ruling chat wants the cat); asked: "other" labels (= surface, from the 8B3R log), "6+6+58" (wrong: double count; 63 distinct rows), abp_corrections trace (23 via block P4B — reviewer CLEAR; 346 via delta copy-down).** DR "### P4 log HELD".
- **11/21 P4 RAN: FINDINGS (1) — CC's miss: abp_corrections (the lane's own re-adjudicated table) was left off the expected list; delta shows nothing live-only (removed 346, added 0, status changed 23). Built full sha d2c8603b…1523. Swap drops 99 AI-cache rows + 50 lsj + 4 abp_ext summaries. All other gates as declared. To the ruling chat.**
- **11/21 P4 CLEARED (§9.221)** — JP uploads p4_check_20261121.py, runs the block, pastes the console. On its log the ruling chat rules Q1, live = src, built sha = P6 pin, G5 for P7.
- **11/21 BLOCK P4 DRAFTED + TESTED (14 cases) — reviewer ESCALATE x2 (it adds a live copy; NOTES 1/2 taken; verse-id gate added after pass 2, not re-read) → WITH THE RULING CHAT for clearance.** DR "## Block P4"; program p4_check_20261121.py sha 3a82deca…6606; block b38f48d9…2566.
- **11/21 P3 CLOSED (§9.220)** on P3b. P6 record must carry one line: notes made after 11/21 05:21Z are not covered. NEXT: P4.
- **11/21 P3b RAN: DONE, the run of record** — no stored note anchors in the 10 verses (live 0, deleted 0), same as the first run. To the ruling chat. NEXT: P4.
- **11/21 P3 HELD (§9.219) on §9.190 (5)(b) (hash-then-run gap; CC + reviewer missed it); first run (05:16Z, live 0/deleted 0) kept, not the run of record. P3b (read-once launcher, block c581e9fc…e9f, program unchanged) reviewer CLEAR → JP runs it, log by cat to the ruling chat.** NEXT: P4.
- **11/21 P3 RAN: DONE** — no stored note anchors in any of the 10 verses (live 0, deleted 0). To the ruling chat. NEXT: P4.
- **11/20 P3 BLOCK CLEARED by the reviewer (second pass; pass 1 ESCALATE on extra log lines, fixed)** — DR "### Block P3"; program p3_notes_20261120.py sha b5940f2b…738b, JP uploads it, then runs the block. File storage 7.4 / 10.0 GB recorded. NEXT: P4 (the copy + every-table read).
- **11/20 P2 STAYS CLOSED (§9.218):** limits in full; the step-4 gate (§9.193) and STEP6AUD v2 word-order 0 (§9.204) named as the reads covering the verse text; neither checks Strong's vs the feed (Jdg 11:7 carried). Owed before P6: P3, P4, Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/20 P2 RULED CLOSED (§9.217):** reviewer read the P2 scripts + outputs → ESCALATE on one read-out cell (2Ki 23:35 src bracket unlisted), corrected; verdicts (1)+(2) unchanged; page shas 9/9 tie; limits 4(b)(c) added; Jdg 11:7 1473 vs 5210 on the follow-up list. Back to the ruling chat. Owed before P6: P3, P4, Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/20 P2 CLOSED (§9.216):** JP set the eSword read aside; built = the app feed at all 10 reorder pairs (reading order, control fires), and a fresh read of the 9 app pages = the frozen feed for all 10 verses, every slot (control fires). Nothing to bring. Owed before P6: P3, P4, Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/20 P1 + TASKS TAB RULED (§9.215):** P1(b)/(c) CLOSED; P1(a) read-out; check.out + tipnr57 log shas = pins; SWAP WINDOW = outside 13:00-14:30 UTC (STOP on a miss). --keep: bible.db keeps 3 (backup_db.py :71/:219) — after 3 post-swap nightlies the rollback copy is the only whole pre-swap live. Owed before P6: P2 + eSword, P3, P4, Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/20 P1 DONE + TASKS TAB RECORDED** (DR "### P1 + Tasks tab — read locally"): 1Ch 25:3 traced ON the step-4 list (5 english cells, no row moved); Eze 31:9 @22 = τρυφή on both (the garble was the screen paste); Est 5:9 / Jos 5:15 cause = the name English changed (Haman's, Josua→Joshua). Tasks: 13:30 health + backup, 06:00 news (never opens bible.db), NO 23:53 task → proposed swap window outside 13:00-14:30 UTC. Next: P2 sheets, P3, P4, Q2 read, PA Disable/Enable help.
- **11/20 JP RULED (§9.214): Q11 = the APP EDITION rules the 10 reorder verses (eSword a witness only; built matching NEITHER is brought). Q7: L9 cannot run on built without new code (lint replays abp_texts, never reads words) → charter §4.2 SET ASIDE for the swap; L9 on built OPEN, first after the swap.** DR "### L9 on built — the code answer (§9.214, 11/20)". Still owed before P6: P1, P2 + eSword read, P3, P4, Q2 read, PA Disable/Enable, swap commit diff, rollback block.
- **11/20 SWAP PLAN RULED (§9.213): order P1 → P9 accepted, clears nothing; conditions (i)-(v) (built sha in P4's block; rollback = a block cleared with P6; JP's Tasks tab before P6; P3 counts/positions only; swap commit diff + tests to the ruling chat before push). Job 3:3 is NEW on built (CC's 'both copies' was wrong). WITH JP: Q7 (L9 unmeasured on built), Q11 (eSword vs app edition), the P1 copy-down, the Tasks tab. CC NEXT: P1/P2 sheets after the copy-down; P3 + P4 blocks; Q2 cache code read; PA help on Disable/Enable (Q3); 1Ch 25:3 owed before P6.**
- **11/20 STEP-8 SWAP PLAN DRAFTED (DR "## Charter §6 step 8 — the SWAP PLAN", :17064-17263): P1-P9 + rollback path + carried list + Q1-Q12; reviewer ESCALATE (1 DEFECT: P2 witness -> eSword/ABP for all 10; 7 GAP) answered in the text. WITH THE RULING CHAT; no block drafted, nothing run. Owed from JP (P1): copy-down of step7a check.out, tipnr57_read_20261119.log, DELTA2 words_cells.tsv + words_moved.tsv.**
- *(History)* **11/20 STEP7A (step 7 Part A) DRAFTED → reviewer ESCALATE (§9.190 (5)(b) read-once) → fixed → CLEAR.** DR "## Block STEP7A", block :16551-16628 sha fd36bed1…c97d; program :16633-17027 sha 7e40ccf3…2859 (upload file `C:SERSJPEDITION_UPGRADE_RUNSSTEP7A_CHECK_20261120.PY`); TESTS `DRAFTS/STEP7A_TESTS_20261120.TXT` (A1�A11), HARNESS `DRAFTS/STEP7A_HARNESS/`. **NEXT: THE RULING CHAT CLEARS IT � JP UPLOADS THE PROGRAM, RUNS THE BLOCK, CATS THE LOG THERE.** COMMITS LOCAL UNTIL IT HAS RUN.
- *(HISTORY)* **11/20 JP RULED (§9.210): −57 OK (charter §4.8 set aside for this row; OPEN past the swap); Mark 1:9 accepted as built, fix after the swap (charter §4.10 note; Part A expects built as is).** Both on the stageC_repin follow-up list. **NEXT (CC): step 7 Part A block; the declared-list lines (record item).**
- *(History)* **11/20 CACHE57 RAN → READ; RULED (§9.209): built = HEADFIX2 shown; the TIPNR57 cache STOP RELEASED (line that moved not shown — LIMIT holds); TIPNR57 read taken as read; tipnr table CLOSED. Live bible.db 460271616 B, changed 2026-11-20T08:22:43Z — noted for the swap step.** CC's answers in DR "### CACHE57 log RULED (§9.209": what touches .git (TIPNR57's git status, no GIT_OPTIONAL_LOCKS; earlier blocks the same); later blocks' cache check = cache folders + contents only (`find … -printf`, tested) + GIT_OPTIONAL_LOCKS=0. **NOW WITH JP: the −57's unlisted +660 (set aside like Split +4, or not) and Mark 1:9.** CC owes: declared-list lines for Est 5:9 @13, Jos 5:15 @27 + 5 MOVED verses; Part A.
- *(History)* **11/20 CACHE57 CLEARED TO RUN (§9.208; sha dc873847…6ccf, hashed by the ruling chat too). NEXT: JP runs it as printed → log to the ruling chat by cat; push the held commits once it has run.** Still owed before step 8: the cache-STOP ruling; the −57 to JP; the declared-list lines for Est 5:9 @13, Jos 5:15 @27 + the 5 MOVED verses (CC); Mark 1:9 (JP); Part A; the rest of the pre-swap list.
- **11/20 TIPNR57 RAN → STOP at the cache guard (§9.207; it stands, nothing removed/re-run, no cause assumed).** The read itself printed READ (tipnr table SAME, 2862 rows; 57 = +660 +251 +9 −864 +1 +0; the +660 a count with no members). The after-guard on built did not run. **OWED FIRST: block CACHE57** (DR "## Block CACHE57", :16294-16391, sha dc873847…6ccf; reviewer ESCALATE (a piped grep) → fixed → CLEAR, both verbatim in DR; tests `drafts/CACHE57_tests_20261120.txt`) — read-only: which listing line moved + git status + the built guard → reviewer → ruling chat → JP runs, cat to the ruling chat. CC test gap (fact): every TIPNR57 test home had NO cache folder, so the fingerprint's `.`/`..` lines were never tested against existing folders. **Then:** the −57 to JP (charter :235-237); CC cites declared-list lines for Est 5:9 @13, Jos 5:15 @27 and the 5 MOVED verses (1Ch 25:3, 2Ki 23:35, Gen 5:25, 5:26, 34:4).
- **11/20 RULED (§9.206): step-7 plan Q2 A + B ACCEPTED (7 before 8 stands; step 7 ruled on Part A's log; Part B under step 8); TIPNR57 CLEARED TO RUN as printed; Q1 Mark 1:9 put to JP (Part A's Mark 1:9 expectation waits on him; no write to built cleared).** NEXT: (a) JP runs TIPNR57 → log to the ruling chat by cat; (b) CC drafts Part A (read-only block, built + src, expectations with register/log lines; 1Ch 13:10 prints text + length, no 157/158 expectation) → reviewer → ruling chat; (c) JP's Mark 1:9 answer. Closing the −57 is ruled on the log; the count-only src term, if unlisted, is JP's to set aside (§9.206 (4)).
- *(History)* **11/20: BOTH DRAFTS BROUGHT, with the ruling chat** (one paste): (1) **step-7 spot-check PLAN** (DR "## Charter §6 step 7 — the
  spot-check PLAN") — Part A on the copies before step 8 (read-only block, drafted only after the plan is ruled) + Part B on the served
  site after the reload; expected per verse with sources; **Q1 Mark 1:9's τῆς cell reads 'of' (in a bracket with 'Galilee,') — neither
  blank nor the app's value as §4.10 / DESIGN :251 declared;** Q2 the A + B split. (2) **Block TIPNR57** (DR "## The import_tipnr −57
  read"; block :15734-15801 sha 0144cf99…2daf; program :15806-16162 XCHK 331dc30f…bffc; upload file
  `C:\Users\JP\edition_upgrade_runs\tipnr57_check_20261119.py`; tests `drafts/TIPNR57_tests_20261119.txt`, harness `drafts/TIPNR57_harness/`,
  WSL homes `~/gate57/*`). Reviewer ESCALATE (cache files + a comment) → fixed → **CLEAR**, both verbatim in DR. Runs only on the ruling
  chat's clearance; then the log goes there by JP's cat. Its src term "10/25 log − src now" is a COUNT only (no pre-8b copy of that run).
- **Split +4 DONE (§9.205):** JP set charter :235-237 aside for this row only; carried OPEN by name past the swap (charter §4.8 note);
  no rebuild. Un-muting the split's member log = a later code change, JP's to raise.
- **PRE-SWAP LIST — every item owed BEFORE STEP 8** (§9.204, plus the items already on record):
  - ~~**The tipnr read (§9.204)**~~ — DONE: TIPNR57 read (§9.207), cache STOP released + tipnr table CLOSED (§9.209), the −57 set aside by JP (§9.210; OPEN by name past the swap). Was: a read-only block that LISTS or ATTRIBUTES the 57 lost import_tipnr matches (31,649 → 31,592) and compares
    the tipnr table built vs src. CC drafts it → reviewer (read-only) → ruling chat. Record: DR :779-800 (CHECK 2), :1490-1505 (CHECK 2b
    could not isolate the 57 — 8b had run on live, not on built); import_tipnr.py :371-374 (tipnr table), :717-723 (words writes) at d34d6723.
  - ~~JP's call on Split 80 → 84 (+4)~~ — RULED OK, §9.205 (rule set aside for this row; open by name past the swap).
  - ~~JP's call on Mark 1:9~~ — RULED §9.210: accept as built, fix after the swap (charter §4.10 note); Part A expects built as it stands (step 4 G7).
  - **Declared-list lines (record item, §9.209/§9.210):** Est 5:9 @13, Jos 5:15 @27 and the five MOVED verses (1Ch 25:3, 2Ki 23:35, Gen 5:25, 5:26, 34:4). CC owes.
  - ~~**Step 7 Part A**~~ — PASSED, §9.212.
  - **Job 3:3 content-other OPEN** (§9.113, §9.195 Q2) — whether the swap can go with it open is not ruled.
  - **The swap commit re-pins:** phrase-gloss 747 (§9.203); cert pin abp_corrections_active 374 → 375 + the active-list fixture
    (§9.156 (4)); health floor 395,003 → 395,014 (§9.130, health_check.py :144); the punct 607 file, snapshot, manifest, L9 scope
    (charter :351-352).
  - **The C4 follow-up item** (stageC_repin follow-up list, "C4 joined-slot rows").
  - Already on record: the 10 reorder verses' eSword order (§9.93 (b)); notes-store anchors at the 20 moved words (before stage G);
    live moving after the 11/18 copy (the swap step's, §9.181).

## SUCCESSOR START (11/19 night; STEP6AUD RAN — step 6 NOT PASSED, C4 FINDING, §9.199) — superseded by 11/19 end above
- **STEP6AUD log ruled (§9.199; DR "## The step-6 audit log — RULED"):** every gate PASSED except **C4: built BEYOND allowlist 747 > 671**
  (src 662). Serving deltas + PN-star CLOSED. Count-differs pin = 27c2f790…0a82.
- **C4 account + read-outs BROUGHT (§9.200 asks; DR "### C4 account + the three read-outs"; rows in
  `drafts/STEP6AUD_C4_account_20261119.txt`):** all 173 new rows rest on a STEP4-DELTA2 english cell and are the app edition's own
  JOINED slots (e.g. `3756-1097` 'I know not'); no built count was ever pre-registered. Proposal: (a) accept + re-pin at swap (CC's pick)
  or (b) hold for a build change. The run copy sits at `C:\Users\JP\edition_upgrade_runs\pa\step6_audit_20261119\` — outside the
  repo, NOT committed (verse text).
- **§9.201–§9.202:** stop rule NOT triggered; no built pre-registration = a recorded GAP. Account rewritten to **v2** (reviewer ESCALATE on v1
  → CLEAR on v2, both verbatim in DR "### C4 account v2 …"). JP's call: (a) **on condition "not losing any context or greek"**. CC's reads of
  the three conditions show MORE than the blank cell: 7 rows also lose greek_pos + bracket_id; in chip view the verb's chip is not drawn;
  the verb can't be clicked; γινώσκω's "renders as" counts + the English finder lose the row.
- **§9.203: JP ruled C4 (a)** ("i just want it to line up w/ the official version"): 747 is built's figure, the 671 restated to 747 for
  this lane, re-pin in the swap commit; C4 FINDING disposed. Follow-ups carried by name (stageC_repin "C4 joined-slot rows"). Step 6 NOT
  yet passed. **NEXT = the ruling chat on CC's two proposals (DR "### C4 ruled (a) …"):** import_tipnr −57 CLOSE on its outputs (words
  side inside the passed step-4 delta; pn_binding passed gate 2) · Split 84 CARRY open by name. Then step 6 can be ruled.
- Still OWED: import_tipnr −57; Split 84 (open by name) — both proposed (above).

## SUCCESSOR START (11/19 late; STEP6AUD CLEARED TO RUN, §9.198) — superseded by 11/19 night above
- **Block STEP6AUD CLEARED** (§9.198; DR "### STEP6AUD CLEARED"): block DR :14595-14736, sha **e4449a39…3f10** (142 lines; GAP 1 (b)
  applied — `XJOBSRC=""`, the only change from the tested 4ce43493…9b52); check program DR :14741-15301 sha 109d95de…3627 unchanged,
  upload file `C:\Users\JP\edition_upgrade_runs\step6aud_check_20261119.py` → PA `/home/appssanding720/edition_upgrade_runs/`.
- **NEXT = JP runs it** (after the nightly backup, so cert check 6 is fresh), then pastes the log's cat to the ruling chat; CC reads the
  same log against §9.198's expected list and cites each log line. A FINDING or STOP goes as printed; nothing re-run before it is read.
- Still OWED: import_tipnr −57; Split 84 (open by name); serving deltas + PN-star (ruled on the STEP6AUD log).

## SUCCESSOR START (11/19 later; charter §6 STEPS 4 + 5 PASSED, §9.193 + §9.194; next = step 6) — superseded by 11/19 late above
- **Step 5 PASSED** (§9.194): Block STEP5INV (DR "## Charter §6 step 5"; read-only, reviewer CLEAR) — built's bare-number
  strongs_base = 0. Log `~/edition_upgrade_runs/step5_invariant_20261119.log`, run folder `step5_invariant_20261119/` (kept).
- **NEXT = charter §6 step 6, CC's to bring** (§9.194 (5)): "audits (all floors re-declared per §4.8) + the S9 block (§4.1–4.4)"; the
  audit list and floors = `.claude/commands/rebuild-words.md` step 6 (:181 on). Read CHARTER §4.1–4.4 + §4.8 and DESIGN §9 on step 6
  first. Same form as STEP4GATE / STEP5INV: GATE REF d34d6723 (PA's scripts), eu_step pre, the "built =" HEADFIX2 guard before and
  after, any embedded program text sha-pinned (long text by upload), tested on WSL copies with a planted known positive per detector,
  reviewer (CLEAR only if read-only), log to the ruling chat by JP's cat.
- **11/19 late: step-6 PROPOSAL DRAFTED + REVIEWED** (DR "## Charter §6 step 6 — PROPOSAL"; reviewer ESCALATE, 1 DEFECT + 5 GAP
  answered) — with the ruling chat, Q1–Q7 open (cert pin 374 vs built 375; Job 3:3; count-differs expected set; the §4.8 ASK rows;
  F-A audit_bracket_order and F-B the L9 lint both read the OLD abp_texts, not built; "= src" gating).
- **11/19 later: PROPOSAL RULED (§9.195)** — FORM accepted for drafting + tests (no run cleared); Q1 (a) · Q2 on conditions · Q3 · Q5 (a)
  · Q6 (a) · Q7. Read-backs in DR "### §9.195 read-backs". **Back to the ruling chat first:** abp_texts is files, not a table, so the
  "148 unwritten tables" proof cannot exist (proposed guard: cert check 5 + git diff on abp_texts); the serving-delta "G2 covers it" claim
  withdrawn. **OWED:** import_tipnr −57 read; Split 84 open by name. **NEXT after that answer:** draft STEP6AUD + the check program, test on
  WSL with a planted positive per detector, reviewer, then the ruling chat for clearance.
- **11/19 end: come-back RULED (§9.196)** — abp_texts guarded by cert check 5 + `git diff --quiet d34d6723 HEAD -- abp_texts
  cert_manifest.json` + porcelain (STOP each); Q2 stands (Job 3:3 named OPEN; built + src both show exactly it); lane-3 CLOSED by reference;
  both 10/30 log lines grepped in-block (≤ 671 = charter gate text; 1,849 member diff vs the file). Answers in DR "### §9.196 answers".
  **STILL OWED (not step-6 blockers):** import_tipnr −57 read; Split 84 open by name; serving deltas (the G2 log line, grep it in STEP6AUD).
  **§9.197 (11/19):** manifest pre-check accepted; STEP6AUD greps + prints the G2 line from `step4_gate_r2_20261118.log` (missing =
  FINDING) and, if that line lacks the strongs_base share, the same log's delta-count line; serving deltas ruled on the STEP6AUD log.
  **NEXT = draft STEP6AUD + check program** per DR "## Charter §6 step 6 — PROPOSAL" as amended by §9.195–§9.197 → WSL tests (a planted
  positive per detector; name the hand-written-output ones: tier-2, L9 lint + sizing, census) → reviewer (close N3: re-check the §4.8 table,
  identity splits, CHARTER_rebuild_trap_fix :488-491, rebuild-words :311-315, health_check :23 / :296-306) → ruling chat for clearance.
  Check-program text goes up by PA's Files upload, sha-pinned, through the read-once launcher.
- **11/19 night: STEP6AUD DRAFTED + TESTED + REVIEWED** (DR "## The step-6 audit block — DRAFT"; block DR :14595-14736 sha 4ce43493…9b52;
  check program DR :14741-15301 sha 109d95de…3627 = XCHK; upload file `C:\Users\JP\edition_upgrade_runs\step6aud_check_20261119.py`; tests
  `docs/handoffs/drafts/STEP6AUD_tests_20261119.txt` + harness `drafts/STEP6AUD_harness/`, WSL homes `~/gate6/h3-h5`). Reviewer ESCALATE, 0 DEFECT.
  **With the ruling chat for clearance:** GAP 1 (the ruled src condition for Job 3:3 should FAIL on the record, DR :1828 — keep, or `XJOBSRC=""`);
  the allowlist added to the git guard; the 66-count + red check 5 made STOPs (CC's reading of §9.196 "each"); Q6 scope gate on built only;
  GAP 2 (PN-star has no database-side read — the build-log lines are printed). Nothing runs on PA before that clearance.
- **WSL test homes:** `~/gate5/home3-5` (built from `~/gate4/repo` at d34d6723 + its test copies; the head of `docs/handoffs/drafts/STEP5INV_tests_20261119.txt`
  shows how — copy scripts/tests/.git + both test dbs into a home, test pre + prep make the guard folder). No sqlite3 tool in WSL —
  write reads in Python.

## SUCCESSOR START (11/19; charter §6 STEP 4 PASSED, §9.193; next = step 5) — superseded by 11/19 later above
- **Step 4 PASSED** (§9.193) on two logs read in the ruling chat: STEP4GATE run 2 (`~/edition_upgrade_runs/step4_gate_r2_20261118.log`,
  G1–G8 PASS, FINDINGS 0) + LIVESRC (§9.181). Charter §6 step 4 now carries the amended text (§9.186 (3)) and the PASSED line.
  Scope: 13 words columns + verses.text; abp_corrections outside by design; live changing before the swap = the swap step's to carry.
- **NEXT = charter §6 step 5 ("strongs_base invariant 0"), CC's to bring** (§9.193 (11)): draft → test on copies → reviewer →
  ruling chat as the lane's rules require. Copies on PA unchanged from the 11/18 list below (src, built = HEADFIX2's result, pre_8b).
- **Kept on PA, no removal unless brought to the ruling chat:** the upload `~/edition_upgrade_runs/step4gate_check_20261118.py`, run
  folders `step4_gate_20261118/` (run-1 STOP) and `step4_gate_r2_20261118/`.
- **Lesson (PA web console):** a ~420-line paste reached bash with ONE extra line break (CAUSE1, §9.193 (9): what differed established,
  how NOT). The screen echo of a long paste is not a faithful copy — never read a cause off it. Bring long program text by PA's Files
  upload, sha-pinned, run through the read-once launcher (DR "## The step-4 gate block, run 2"); logs go to the ruling chat by JP's
  `cat`, never on CC's summary.

## SUCCESSOR START (11/18 end; step 4 — every held item CLOSED; next = the step-4 gate block PROPOSAL) — superseded by 11/19 above
- **Closed on PA logs read by the ruling chat:** (c) control §9.169 · (b) standard (pre_8b = T_b) §9.173 · the xref8b0 sha line
  §9.177 · pre_8b → built = the named list + the norm rule, and the composition src → pre_8b → built = STEP4-DELTA2 cell for cell
  §9.178 · **live = src** (fresh copy of live, words + verses EMPTY delta, digests with row ids equal) §9.181 · every throwaway removed
  (T_c §9.172, T_b §9.175, the live copy §9.183). Run records: `DRAFT_stageC_outline.md` from "## (b) the STANDARD" to the end.
- **Copies on PA now:** src `bible_edupg_test_20261101.db` (451,964,928 B, full sha `5da9bb95c4b1337054dd8dd82ec3cbbb5ac97790c151ee56b33fdac0caf57e01`);
  built `bible_edupg_test_built_20261102.db` (HEADFIX2 state, guard = `eu_step check --dir step4_headfix2_20261116`); pre_8b
  `bible_edupg_test_built_pre_8b_20261106.db` (sha `a4faa4d8…0107`, full in DRAFT "BSTD ran"). Dashboard 7.4 / 10.0 GB (§9.184).
- **NEXT = CC's step-4 gate block PROPOSAL (unapproved — §9.138 (6), §9.183 (5)).** Inputs to read first: §9.138 (3) + (6) (the gate
  lays the raw delta built vs src against the declared lists; members either way unlisted = finding), §9.139 (1)–(4), §9.142–§9.145
  (the (ii) member list, the 50 other-column cells, B's length-only limit, the head-consistency check), §9.157 (STEP4-DELTA2 = the
  reference delta), §9.177–§9.178 (the named pre_8b → built list and the composition). GATE REF d34d6723 = PA's scripts (no pull).
  The proposal goes to the reviewer → ESCALATE → ruling chat before any code or block.
- **11/18 later: PROPOSAL DRAFTED + REVIEWED** (DRAFT "## Step-4 gate — PROPOSAL", reviewer ESCALATE, 0 defect, gaps answered) — with
  the ruling chat. Six questions put there (32 moved-position cells; heads gap; G6's corrected length check — as ruled, §9.144 (1) fails
  2,629 verses on the em-dash swap; G4 option a/b; embedded vs committed check; charter step-4 wording) + G2's census source. Nothing
  drafted as a block until ruled.
- **11/18 evening: §9.185 ruled the proposal (option a; corrected G6 length rule; embedded check). GSRC ran (READ DONE). Block
  STEP4GATE DRAFTED + TESTED** (DRAFT "## The step-4 gate block — DRAFT"; check.py sha c9ec9108…a61b; outputs
  `docs/handoffs/drafts/STEP4GATE_tests_20261118.txt`); reviewer ESCALATE, 0 defect, GAP 1 (Joh 19:18 "no member" basis) → ruling
  chat with the charter step-4 text. UNAPPROVED until read there; JP runs it only on that clearance.

## SUCCESSOR START (11/16 end; step 4 in progress; the (c) → (b) route ruled §9.160) — open here

Rulings: DESIGN §9 (latest **§9.160**). Run record: `DRAFT_stageC_outline.md` (the end is current). Roles unchanged (§9.90):
the ruling chat rules; CC drafts + tests on made-up copies; the `reviewer` subagent CLEARs read-only blocks and re-runs of ruled
gates only — writes and code go to the ruling chat; JP runs every block on PA and pastes the log; every cleared block goes IN FULL
in the reply; ruling-chat messages in one paste block.
- **Code REF `adfb8ac5`** (§9.158: the A dry-run `--cells` read-out). Before it: `d34d6723` (§9.154: spent-by-lane-3 rule,
  `scripts/lane3_spent.py`; cert pin `abp_corrections_spent_lane3` 1). **PA HEAD `1d5e34ee`** (last pull, 11/16) — scripts/tests
  there = d34d6723, so a block at REF adfb8ac5 or later needs a PA pull first (`cd ~/bible-db && git pull --ff-only && git log -1
  --format=%h`, no reload).
- **built** `~/bible-db/bible_edupg_test_built_20261102.db` = **HEADFIX2's result** (§9.156): Joh 19:18 @10 english_head + norm
  'here'; abp_corrections **375|23|6**. **"built =" guard for every block: `eu_step check --dir
  ~/edition_upgrade_runs/step4_headfix2_20261116 --written words,abp_corrections`** (a block citing STEP9A-APPLY for words or
  abp_corrections is wrong). Restore source `step4_headfix2_20261116/before.db` (sha `da47ce8c…57f3`).
- **src** `~/bible-db/bible_edupg_test_20261101.db` (451,964,928 B): the build's source copy for corrections (four writes to its
  abp_corrections on record, §9.153 (1)); untouched by steps 9 → 9c and by HEADFIX2. Rollbacks kept:
  `bible_edupg_test_built_pre_8b_20261106.db` (= build + B2 + tail + R2 + J, before 8b.0) and
  `bible_edupg_test_built_pre_digits_20261105.db` (= right after the stage-C tail).
- **Reference delta = STEP4-DELTA2** (§9.157): `~/edition_upgrade_runs/step4_delta2_20261116/delta/` — words_cells 50,890
  `86e44c58502748d24be623f4f11c859db540d4c08e4f058dd26dd4345c9fdafc`, verses_cells 15,522 `870e4782…57f9`, words_moved 20
  `d32361b3…0f08`. Counts: english 32,962 · english_head 5,426 · strongs 20 · strongs_base 26 · greek_pos 3,318 · bracket_id 4,208 ·
  is_pn 12 · morph 14 · lemma 14 · english_head_norm 4,890 · verses.text 15,522.
- **NEXT — the approved route for the four columns (english / english_head / greek_pos / bracket_id), §9.159–§9.160, in this order
  (plan text: DRAFT "§9.159 (3) — PLAN"):**
  1. **PA log read** (read-only, reviewer scope): the stage-B log's timestamps (wall time) + its greek_pos/bracket_id line + the
     bh_scrape sha; the 11/1 retire block's log (write 1 to src's abp_corrections, quoted); the 4 active strongs_base rows
     (Jer 49:13 @28 G165, 1Sa 6:11 @21 G1475, Mal 3:6 @7 G241, Dan 4:33 @1 G846) against pn_greek_identity. Also (§9.158 (4)) the
     stored type of words.greek_pos (typeof / declared type) on src and built.
  2. **Removal block** (§9.160 (4)): `step4_headfix_20261115/dry.db` and `step9a_apply_20261115/dry.db` may go (before.db in both
     stays); the block names which guards still read step9a's dry.db first (CC's reading: none since §9.156 (3) — confirm from the
     DRAFT blocks). HEADFIX2's dry.db STAYS. JP's disk check first (home 7,771,060 KB of 10 GB on 11/16).
  3. **(c) control block** — T_c = src → OLD build (no --app-feed) → finish_rebuild.sh in full (corrections on) → step 11 norm;
     `eu_words_delta --a src --b T_c`, 13 columns + verses.text. Expected only: the lane-3 8b.2a cells, the 23 retired rows' cells,
     Joh 14:26 @3, english_head_norm only where english_head differs; moved 0; verses.text 0; strongs-side columns = src's own 8b
     chain, counts only. 4b/7 LOUD-skip EU- rows (finish exits 1); a non-EU skip = STOP. Anything else in the four columns = build
     drift since 10/25, read and ruled before (b). **A write block** (the build writes `<src>.new`) → reviewer on mechanics →
     ESCALATE → ruling chat.
  4. its log → ruling → **T_c removal** block.
  5. **(b) standard block** — T_b = src → `--app-feed` build (step-5 inputs) → B2 apply → finish_rebuild.sh in full;
     `eu_words_delta --a built_pre_8b_20261106 --b T_b`: **expected EMPTY**; any member is a finding. Must reproduce the stage-B
     figures (HANDOFF_..._stageC.md :83-89; DESIGN :470): 626,305 · 0 · 6,882 · 923/411 · PN-star 1,505 + 2,552 / 3,161 ·
     transplanted 29,071 · strict_fail 1,421 (625) · english changed 15,588 · merge 1,578/1,380 + edge 90/90 MATCHES · Filled 5 ·
     Split 84; B2 15,571 / 13,500 / 2,166, EU 118. A miss on 15,588 or 29,071 = STOP-and-read; the greek_pos/bracket verse count is
     printed beside the stage-B line (it may move: §9.88's rule entered the build at 820a6109). Same write-block route.
  6. **pre_8b → built read** (read-only): every member attributed to its own file (8b.0 / 8b.1 / 8b.2 / ABPTAG, REKEY / the 10
     reorder verses, 8b.2a, step 11 norm by rule, 10 / 12, HEADFIX2).
  7. the live = src proof (keeps its place before the gate) → the step-4 gate block (still UNAPPROVED).
  **Conditions for (c) and (b), §9.160 (2):** STOP if `<src>.new` exists (never let the build delete one); src sha256 before =
  after; pre_8b read-only; LIVE untouched — say how finish_rebuild.sh is pointed at the throwaway (it takes the db path as $1;
  no step swaps or deploys) and STOP on live's size/time changing; `pronoun_review.tsv` (build :2867) is UNTRACKED and not ignored,
  `unmatched_pn.txt` (import_tipnr :694) is gitignored — declare them left or moved; the "Type 'rebuild'" prompt piped as stage B
  did (quote the stage-B record); every later-apply skip named in the log; new dated folder + log each run, re-paste STOP.
  **Trap for the (b) block:** an `--app-feed` build writes its report files (strict_fail / eligible / merge_pairs /
  edge_splits `_20261031.tsv` — a FIXED stamp, `report()` default) into `--out`, whose default is `~/edition_upgrade_runs`
  — it would overwrite the 10/31 files there. Pass `--out <the run folder>`; check those paths do not exist first.
- **Ruled — do not re-open:** the (ii) member list (§9.142); the verses.text declared list (§9.143–§9.144); english_head_norm by
  rule (§9.142, now 4,890 members); Isa 48:5 @4 a declared single row (§9.148); Heb 11:24 @7 english = the one declared
  spent-by-lane-3 row (§9.152–§9.154); the A cells list (`--cells`) is a READ-OUT only, gates nothing (§9.159 (2)); (a)
  rule-attribution for the four columns NOT adopted (§9.159 (2)).
- **Still open:** the 10 reorder verses' cause / eSword order confirmation (§9.93 (b), before the swap); notes-store position
  anchors at the 20 moved words (before stage G); the follow-up lane list below. Swap knock-ons: cert pin abp_corrections_active
  374 → 375 + the active-list fixture re-pin (the spent pin 1 is already in d34d6723); built's .corrections.log carries HEADFIX2's
  two appended reports (declared).

(Below: the 11/16 mid-day notes and the 11/15 start block, kept for history.)

### 11/16 mid-day notes (history)

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

Rulings: `DESIGN_q2_build.md` §9 (sole register, latest **§9.160**). Run record: `DRAFT_stageC_outline.md`, from "Step 9 → 9a →
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
