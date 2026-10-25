---
description: Step-by-step to safely rebuild the ABP words table (copy-first → self-correcting build → tail patches → audits → swap/deploy → re-run dependent builders)
---

You're rebuilding the `words` table. This is high-stakes, data-integrity work (HIGH effort —
read as many spots as the trace needs). Follow this checklist exactly.

**Hard safety rules first (also in CLAUDE.md "Do Not"):**
- bible.db lives on PythonAnywhere ONLY — never rebuild against a local DB, never the live file.
- NEVER `DELETE FROM words` / `DELETE FROM verses` by hand — OT and NT words share the table.
- The build's own DELETE+rebuild clears `is_pn` + proper-noun Strong's and historically stripped the
  G prefix off `strongs_base` (now re-applied at INSERT). After ANY run you MUST re-run
  `import_tipnr.py` and verify the strongs_base invariant (step 5 below).

---

## Words rebuild checklist (if you ever rebuild the words table)
THE REBUILD IS A SINGLE SELF-CORRECTING PASS (2026-06-09, refactor backlog #2). The build now
applies the six former cleanup scripts ITSELF, per verse, inside build_words_from_abp.py —
bracket_punct → g1473_gloss → lord_subject → funcword_subject → lord_oath → greek_pos backfill
(same relative order the old chain used). On a fresh build those six standalone scripts find 0 to
do. Only the fixes that CAN'T fold (per-verse corrections a global rule would regress, or pinned
source mistags) remain, and they run from ONE tail script. PROVEN: an old-way rebuild (build + the
full 14-patch chain) and the new single pass produced a BYTE-IDENTICAL words table
(`compare_words.py`), validated locally on a copy of live 2026-06-09. See memory
`project_architecture_rework`.

COPY-FIRST, ALWAYS — build on a `cp bible.db bible_test.db` copy; the live bible.db is never the
one rebuilt (DELETE only ever hits the copy).

**STEP 0 — `git pull` ON PA FIRST, and PROVE the change is in the file.** PA is pull-only and
can sit many commits behind. A build from a stale checkout runs perfectly and produces a words
table with the fix missing — a clean-looking no-op that poisons every downstream check.
`grep -n <new function> scripts/build_words_from_abp.py` before building; matching line numbers
against the local repo double as file-identity proof. (2026-08-01: PA was 7 commits behind and
the pass wasn't there. Caught only because a traceback's line number didn't match the repo's.)

**TEE EVERY LONG RUN — `2>&1 | tee run.log | tail -60`.** The build and `finish_rebuild.sh`
print per-step counts that are pinned in this checklist, and a bare `| tail` throws them away.
They are NOT recoverable: the steps settle, so a re-run reports "nothing to do". (2026-08-01:
`fix_split_merges` 237 and `import_tipnr`'s matched count were both lost this way.)

**THE BUILD'S FIRST ARGUMENT IS THE SOURCE, and it builds into `<source>.new`** — so
`... bible_test.db bh_scrape.db` makes a SECOND 412MB copy. Two copies plus the working file can
exceed the PA quota; `df -h ~` is useless here (it shows the shared filer, not the quota — the
dashboard has the real number). A `disk I/O error` on the very first snapshot write, leaving a
0-byte `.new`, is out-of-space, not corruption.

**RUN ORDER (re-settled 2026-10-26, `docs/handoffs/CHARTER_rebuild_trap_fix.md` §9; steps 10 + 11
re-homed onto the copy by JP ruling after the 10/26 run, charter §10 — the step NUMBERS are labels
other docs cite, not the order):**
0 → 1 → **1a snapshot check** → 2 build → 3 finish → 8b.0 → 8b.1 → 8b.2 → 8b.2a → 8b.3 →
**11 rendering norm (copy) → 10 two-ending read (copy)** →
**9 surface rebuild (on the copy) → 9a fill restore (copy) → 9b health floor + oracle (copy)** →
4 → 5 → 6 → 7 → **8 swap + deploy**.
Names used below: `<src>` = the fresh copy of live from step 1 (the snapshot check's source AND
the build's source — the build opens it read-only, never writes it); `<built>` = the build's
`<src>.new`, renamed. **Everything up to step 8 runs on copies; the swap is the only step that
touches live `abp_surface`, and live is never served without the fill.** Nothing writes live
after the swap: step 11 now fills the norm column on the copy, and step 10 reads the copy (its
output, if any, rides the step-8 deploy).

1. Rollback copy: `cp bible.db bible_pre_<reason>_<date>.db`; `cp bible.db bible_test.db`.
   (Full-rebuild fallbacks keep this receipted naming — ops.md retention item 1. But
   ordinary ARC ships use the single overwritten `bible.db.rollback` name, ops.md item 6;
   and before DELETING any old copy, check the newest nightly in ~/db_backups is stamped
   AFTER the last swap — the nightly runs ~13:30 UTC and does not cover an evening ship.)
1a. **SNAPSHOT CHECK — before the build, on `<src>`** (added 2026-10-26, charter §9). The
   2026-10-25 abp_surface fill is frozen ONCE in `tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv`
   (+ `.sha256`; git-ignored ABP text — on PA and in the local checkout only; sha256 pinned in
   `restore_surface_fill.py`). Before every rebuild, prove the frozen file still describes live:
   `PYTHONIOENCODING=utf-8 python3 scripts/snapshot_surface_fill.py --check --src <src> --prefill ~/bible.db.pre-surface-fill-20261025 --csv ~/abp_surface_fill_dryrun.csv --out tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv`
   It writes nothing. **Must print `RESULT: SNAPSHOT CURRENT`.** `STALE SNAPSHOT` = STOP: live's
   table or a fill slot's word row changed since the freeze (or the file is not the pinned one) —
   surface it, never overwrite (a re-freeze is a ruling: `--replace`, without `--check`). `<src>`
   must be a copy of live taken NOW; live itself is refused. A missing frozen file also stops: copy
   the second copy back, never re-freeze to get past it.
2. Rebuild (self-correcting): `python3 scripts/build_words_from_abp.py bible_test.db bh_scrape.db`
   (type 'rebuild'; re-applies the 'G' prefix at INSERT). Needs Rahlfs + TAGNT for pronoun
   correction + morph. Confirm `Words inserted: 626,305` (the tail patches add 4 more; live
   pin = 626,309), `Verses skipped: 0`, flagged 6,882 (pinned, ops.md), and
   `Split 80 merged subject-name(s)` — **re-pinned 2026-10-26** from the two lane-② ride logs
   on PA (`~/bible-db/build_pnstar.log`, `build_pnstar2.log`) and the 10/26 re-key build, all
   three 80. Was 2,436 before the 8/5 lane-② PN-star pass, whose class B now splits most of
   these names off their verbs earlier in the same build (2,436 = 2,299 roster/εἰμί + 137
   capfall, `docs/tickets/blank_star_classes.md`; still in the pre-② `run_build.log`).
   Also pinned since 8/5: `PN-star pass: A 1,505 + B 2,552 written · 3,161 refusals`
   (`docs/tickets/TICKET_pn_star_fix.md`).
   GATE (2026-07-16, permanent): if import_tipnr.py or tipnr/TIPNR.txt changed since the
   last run, `python3 scripts/check_roster_regression.py` must print CLEAN before
   import_tipnr runs — the roster is frozen outside reviewed re-baselines
   (tests/test_tipnr_roster.py locks it in CI; the Barabbas-stole-'jesus' incident).
   FOLDED INTO THIS PASS (no longer separate): bracket_punct (~331v), g1473_gloss (~1,724),
   lord_subject (~795), funcword_subject (~108), lord_oath (29), greek_pos backfill. Already at
   build from before: pronoun correction (Rahlfs/TAGNT), _redistribute_pronoun_compounds,
   _split_compounds, _fix_backwards_pairing (7 number-reversal verses), _split_pn_article_lump
   (Act 19:4). RETIRED long ago: fix_article_noun_swaps.py (deleted).
   NEW 2026-06-14 — `_emit_words` bracket PEEL: a helper word sharing a bracketed verb's single
   Strong's ("May [2be found 1your hand]") was glued INSIDE the bracket; it now sits OUTSIDE
   ("May [be found your hand]"). ~943 verses, +~1,023 word slots (why the count rose). The source
   bracket parser is now shared — `build.iter_source_tokens`, and the bracket audits delegate to it
   so they can't drift from the build. See memory project_bracket_helper_peel.
   NEW 2026-06-18 — `_emit_words` VERB SPLIT (`_split_numbered`): ABP wraps some verbs' English
   around the subject, giving ONE Greek word TWO position numbers under a single Strong's with
   nothing between them ("1Was 5justified]" G1344; "1may 5search 7out" G327). The old code read
   only the FIRST number, glued the gloss onto that slot and dropped the rest — a skipped bracket
   number + the verb in the wrong reading order. Now each numbered piece becomes its own word,
   sharing the verb's Strong's. 321 chunks / 308 verses canon-wide (Job 57, Isa 24, 1Co 23,
   Jas 11…), +323 word slots (part of why the count rose). Single-number chunks are byte-identical.
   See memory project_verb_split_slots.
   NEW 2026-06-20 — blank-"G." FILL (`apply_blank_strongs_fills`, a FINISHING step at the very end
   of the build, after the insert loop): ABP's source leaves EXACTLY 5 words with a numberless "G."
   (Zec 9:11/1Pe 3:13 "And"→G2532, Heb 7:4 "And view"→G2334, Mat 12:14 "And the"→G3588,
   Act 24:8 "bidding"→G2753). The build merges them onto the next number; this fills the right number
   and splits the slot. Runs automatically on rebuild — do NOT re-run the one-time fill_blank_strongs.py.
   The 4 splits shift positions, so step 9 (surface + translit re-run) covers them. See memory
   project_blank_strongs_fill.
3. Tail — one command: `bash scripts/finish_rebuild.sh bible_test.db`. Restores proper nouns
   (import_tipnr, **31,649 matched** — re-pinned 2026-10-26: the 10/26 re-key chain's log equals
   the 8/5 lane-② ride's `~/bible-db/finish_pnstar2.log` line for line, timestamps aside; was 31,392
   at the 2026-07-16 roster, before lane ② — the build CLEARS is_pn + PN
   Strong's) then the PINNED
   data-patches that can't fold, then a final punctuation float. Each only touches its own named
   verses, safe to re-run.
   **THE SCRIPT'S VERDICT IS THE GATE (2026-07-14).** It does NOT abort mid-chain (steps are
   independently re-runnable; a half-patched copy is worse than a finished one with named
   failures) — instead it COLLECTS any step that reported a problem and REFUSES to print
   `== finish_rebuild done ==`, naming them and exiting non-zero. **If you do not see the
   `done` line, DO NOT SWAP.** (Before this it printed `done` regardless — a failing step just
   scrolled past.)
   **RIDING import_tipnr: the p2wl:v2 GUARD FIXTURE DRIFT CHECK** (`check_p2_guard_fixture.py`,
   JP-ruled). import_tipnr is the sole writer of `is_pn=1`, so the check fires there automatically
   — nothing extra to run. It asks whether the corpus still matches the name-marking the probe-2
   test fixture claims (baseline verified 2026-07-12). **A drift flag does NOT mean the rebuild
   is wrong — it means the FIXTURE is stale.** Decide whether the corpus change is legitimate,
   PASTE the run's findings into `check_p2_guard_fixture.py` (never retype — #71), re-date
   `FIXTURE_VERIFIED`, re-run the probe-2 tests, then swap. Silence = it matched.
   The steps:
   - fix_subject_reorder (20) / fix_mat25_37 (1) / fix_supplied_attach (5): hand-listed
     synthetic-bracket verses needing per-verse English rewrites no general rule produces.
   - fix_theos_filler_tags (2): Lam 3:16 "and"→καί, 1Pe 1:23 "of God living" split. Pinned.
   - fix_split_merges (237): reorder-MERGE garbles. STAYS A PATCH — the general splitter
     (carry=True in _split_compounds) regresses ~85 other verses, so the provably-clean subset is
     frozen in scripts/split_merge_fixes.json. Its positions are ABSOLUTE, so any build step that
     INSERTS a word ahead of a target shifts it and the patch skips it (safe: strongs precondition
     caught it). The `_emit_words` peel shifted 4 ALSO-peeled verses — Isa 31:8, Jer 17:18,
     Jer 37:20, Job 31:30 (refreshed 2026-06-14); the 2026-06-18 verb split shifted Rom 3:4's later
     pair by +1 (refreshed 2026-06-18, the only overlap of the 308 split verses). REFRESH BY GRAFTING
     only the shifted verses (regen on the new build, copy just those keys); do NOT commit a full
     `_gen_split_candidates.py` regen — it re-baselines and drops ~36 unrelated verses to build drift.
     (Retiring this via the Rahlfs/TAGNT alignment was viability-checked 2026-06-09 and DECLINED: the
     alignment is Greek-only so it can't replace the English-pairing guess, and a morph filter
     over-blocks 53% of the good fixes — see memory project_architecture_rework #2. Don't re-investigate.)
   - fix_kyrios_mistags (3): Dan 4:19 "and"→καί; "of Cyrus" Dan 11:1/Ezr 5:13 → H3566. Pinned.
   - fix_merge_misses (1): Dan 9:10 hand-verified merge the auto generator misses. Pinned.
   - fix_idios_own (13): 'his/their/its own' (ὁ G3588 + ἴδιος G2398) parked on the article slot →
     relocate the English onto the empty ἴδιος slot (greek_pos carried in brackets). The orphan is
     the ADJECTIVE ἴδιος, so the folded NOUN funcword_subject skips it — hence a standalone pinned
     patch. Idempotent; corpus-wide on the exact ὁ+ἴδιος "own" shape (1Co/1Ti/2Ti/2Pe/Heb). 2026-06-14.
   - dedup_words (0 now — Hab 3:14 fixed at source) → fix_bracket_punct ONCE MORE (~202 cells):
     floats a trailing comma left on the verb onto the last chip of the LORD-subject brackets made
     in the pass (e.g. "said · the LORD,"). Runs LAST so it tidies brackets created above; re-run
     settles to 0.
4. PROVE IT (the gate): `python3 scripts/compare_words.py bible.db --compare bible_test.db`.
   Keyed by verse+position over all display columns, bracket-numbering normalised. Expect a small,
   EXPLAINABLE diff vs live (live is older code/data: ~17k english_head head-word drift +
   ~32 newer-TIPNR proper-noun numbers + the 3 Cyrus fixes live lacks — none are errors). For a
   clean [IDENTICAL] readout, compare against an OLD-WAY rebuild instead (stash the build edits,
   rebuild + run the full chain) — that isolates any genuine change introduced by a code edit.
5. Invariant (MUST be 0): `SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'`
6. Audits (the gates), all on bible_test.db, AFTER 9b (before step 9 the copy still carries live's
   old surface table, so its floor line passes for free): `health_check.py` (0 warnings) → `audit_bracket_order.py`
   (CHIP genuine **3** — re-declared 2026-10-26 from the live rebuild, where live's own copy and the
   rebuild both read 3; was "≈ 2", the known Jon 4:9 twin-bracket FPs) → `scan_strongs_cross.py`
   (FUNCTION-anchor 0) → `audit_lord_strongs.py` (WRONG-SLOT REPAIRABLE 0) →
   `audit_funcword_wrongslot.py --preps` (REPAIRABLE-NOUN ≈ 0) → `scan_content_filler_tags.py`
   (G2316 0) → `audit_split_flip.py bible_test.db` (**MUST be 0** — the "LORD the" determiner-flip
   guard; if non-zero the `_split_compounds` source-phrase-order fix regressed, don't swap) →
   `audit_corpus_tier1.py` (A1 **177** — re-declared 2026-10-26, live copy and rebuild both 177; was
   "≈ 176") → `audit_corpus_tier2.py bible_test.db --rahlfs
   ~/LXX-Rahlfs-1935 --tagnt ~/TAGNT_*.txt` (~92%).
7. Spot-check: Greek (Eze 31:9 "were jealous of" → ζηλόω), proper noun (1Chr 1:1 "Adam" → H121,
   opens metaV), LORD dual-order (1Ch 13:10 chip → "<verb> · the LORD").
8. Swap + deploy — **MOVED below 9b (2026-10-26):** it is the LAST step and the only live action
   (RUN ORDER line above; steps 10/11 moved before it, onto the copy). 8b below still runs on the copy, right after step 3.
8b. **R-2 RETIREMENT CHAIN (post-2026-07-26, MANDATORY after import_tipnr):** import_tipnr writes the
   HEBREW stopgap numbers; live serving is GREEK-keyed with Hebrew in `pn_hebrew_xref`. After
   import_tipnr (still on the test copy, before the gates), IN THIS ORDER:
   0. **`~/.virtualenvs/bible-env/bin/python scripts/correct_xref_vs_binding.py <db> --rebuild-step`
      (dry-run, read it, then `--rebuild-step --apply`)** — landed with the 2026-10-24 live
      correction (record `docs/tickets/RECORD_xref_vs_binding_fix_20261024.md`). import_tipnr
      re-writes the June stopgap numbers (Gen 25:15 back to H1908 etc.); this re-applies the
      ruled correction to the WORD only, keyed by verse + name through the binding (never by
      position — the Cushi lesson), so step 1 finds no drift on these slots. Expect CONTROL OK
      and the same decisions as the 10/24 live plan (SWAP 319 · REMOVE 22 · LEAVE 27 · HOLD 1)
      unless the binding or the slot set moved — a different split is read member by member,
      never forced. Skipping it: step 1's restore count balloons by ~341 and HALTS. At step 3
      the binder relabels the 3 Michaiah binds (2Ch 17:7, 2Ki 22:12, Neh 12:41) `ruled` →
      `fuzzy`, same entity — expected (row-level check, 10/24).
   1. `scripts/restore_frozen_pn.py <db>` (dry-run then --apply) — puts import_tipnr's drift back
      to the frozen record. Declared restore count **6** (the 2Sa 18 Cushi class, H3570→H3569 —
      RE-DECLARED at the 8/1 ride from the full-population dry-run on a real fresh build; the
      first declaration of 363 carried a mis-ported "357 hand-fix-zone" census figure that was
      never fresh-import drift). A different count HALTS — read the member list before any
      override. Replaces the old "re-run fix_cushi_strongs" note: the frozen record covers it.
      **RE-DECLARED 6 → 8 on 2026-10-26** (`restore_frozen_pn.py` `EXPECT`, receipt in the code
      comment): the full 2Sa 18 Cushi set — all 8 'Cushi' slots, H3570 → H3569 — confirmed member
      for member by the independent name-keyed fix (`apply_cushi_namekeyed.py` dry run lists the
      same 8; Jer 36 / Zep 1 refused by design). Any other count is attributed member by member
      and re-declared in code — `--expect` was removed.
   2. `scripts/retire_hebrew_identity.py <db> --fresh-rebuild` (dry-run then --apply). The copy
      carries live's stale pn_hebrew_xref; --fresh-rebuild proves the identity table is a
      byte-for-byte carrier of the frozen record (0 mismatches or HALT), then drops + rebuilds
      the xref. Declared five-class split — **the code's figure is the authority**
      (`retire_hebrew_identity.py` `EXPECT`, re-declared 2026-10-26 after the 9/6 Greek-header
      landing; receipt in the code comment): abp-tag 3,671 · tipnr 10,236 · lemma-only 12,182 ·
      surface 4,412 · none 1,977 (32,478). (Superseded: 2026-08-05 3,671 / 10,236 / 12,166 /
      3,951 / 2,454; 2026-08-01 3,518 / 10,216 / 12,066 / 4,326 / 2,353.) **Any later rebuild of
      pn_greek_identity on live changes this split — re-declare it in the same change.** Any
      other split, or a sixth class, HALTS by design — stop and re-declare, never
      --expect-split past it.
      **PRE-REGISTERED serving deltas vs pre-rebuild live (compare by member where it matters —
      all three groups LANDED EXACT on the 8/1 ride):**
      +9 slots gain Greek (saul ×8 → G4549, zacharias ×1 → G2197 — members in the receipt) ·
      2,190 slots Hebrew→'*' (1,524 lemma-only + 666 surface churn) · **1,523** slots
      '*'→Hebrew (none-class churn; was declared 1,575 — that read lacked its GROUP BY and
      counted the group total; 52 of the group are never-had-a-number gentilics that stay '*',
      receipt amended). Anything outside these three groups at the serving column = HALT.
      **TRAP: a delta-group pre-registration comes from a GROUP BY'd read with the query text
      committed beside the number — a bare aggregate wears an arbitrary label, and a number
      without its derivation cannot be re-checked.**
      **TRAP (four casualties on the 8/1 ride — flipped writes, audit refusals, the sizing
      window, the sizing bins): any figure asserted about a post-correction artifact must be
      derived THROUGH the correction layer with the same inputs the build uses (Rahlfs/TAGNT
      + lexicon + BH), and the derivation command committed with the figure. The article-slot
      swap check is `audit_article_slot_carrier.py --predict-vs <copy>` — member set-equality
      with a named tail allowance; counts are tripwires, the member set rules (§6l).**
   2a. **LANE-3 HAND REPAIRS — `python3 scripts/lane3_rebuild_step.py <db>`** (added 2026-10-26,
      `docs/handoffs/CHARTER_rebuild_trap_fix.md` G4). Re-applies the three frozen lane-3 files
      (fixes 9 → gapfix 6 → fixes2 7 verses; gapfix gained 2Sa 18:31/32 on 2026-10-26) and judges
      each from its own output; **it must print
      `LANE-3 STEP: PASS`, or DO NOT go on.** Without it a rebuild silently REVERTS 16 live verses
      (Mat 9:11 "the Pharisees seeing" merges back, etc.). HERE, not in finish_rebuild.sh: fixes2 is
      pinned to Mat 27:26's `G2424`, which only returns in step 2; and step 3 below must see the
      repaired words (live's identity rows for these slots were built after the repairs). Tolerates a
      contiguity FAIL from the fixes file only on slots the gapfix file then marks (read at run
      time); gapfix must PASS there; fixes2 is strict; a re-run passes as "already applied".
   3. `scripts/build_pn_greek_identity.py <db> --apply` → `scripts/build_entity_binding.py <db>
      --apply` (xref-sourced guard numbers) → gates: `scripts/audit_unfindability.py <pre> <db>` +
      **PRE-REQ (reviewer-ruled 2026-08-05, TICKET_pn_star_fix.md): before any ride whose
      build pass MOVES name slots, audit_unfindability needs a geometry-aware mode
      (identity-level matching per attribute_unfindability.py v4) — position-keyed, it
      fails on exactly the moved class (2,049 on the ② ride, all attributed, 0 real).
      Baseline capture on a pre-retirement copy = build_pn_greek_identity --ignore-xref,
      the ONLY correct mode (stale-xref branches misclassify; two defects, ticket).** +
      `scripts/audit_two_derivations.py <db>`.
      **THEN GATE THE HEADER RESULT — added 2026-08-09 after it shipped broken and sat live
      for a day (TICKET_glued_name_headers.md): `scripts/gate_greek_header.py <pre-copy> <db>`
      and READ GATE C. Re-running the header build is not the same as it coming out right.
      A pin that used to pass and now FAILS means the rebuild pushed two-word compound slots
      (verb glued to a name, joined by U+00A0) into the name-form inventory — one such row
      drops a whole name off its folded header. The 8/8 ride cost 375 folded rows, 13 names,
      and +101 rows with no header at all, entirely unnoticed.**
      **On a FULL words rebuild, gates A and B ABORT by design** (they were built for the 7/30
      header-only lane): 10/26 = 3 Michaiah binding relabels (A), the 21 header rows (B), and the
      landing-only PIN lines. That ABORT was overridden for the **10/26 run only** — the next full
      rebuild aborts there again and needs its OWN ruling, member by member, until A/B are
      re-scoped (charter §10, handoff held item 12). Gate C is still read as above.
   **G707 gate (2026-07-31):** build_pn_greek_identity applies strict name-match inheritance
   (removal-only; tests/test_pn_name_match.py). Run the removal-only census
   (ship_g707_targeted.py preconditions) before any swap.
   Skipping this chain leaves the serving repoints DORMANT (no pn_hebrew_xref → H-keyed pages fine
   but Greek identity gone) — the run record: docs/PLAN_r2_c3_rebuild.md.
9. **WHERE: on the rebuilt COPY `<built>`, after 8b.3 and steps 11 + 10, BEFORE the gates (4–7) and
   the step-8 swap** (re-settled 2026-10-26, `docs/handoffs/CHARTER_rebuild_trap_fix.md` §9 — supersedes the
   §1 "live, after the swap" placement, which was practice, not a dependency). Step 9 reads nothing
   that exists only on live: the db's own `verses` / `words` / `lexicon` / `dotted_lexicon` /
   `abp_surface` (the build copies the whole db) plus `~/bible-db/bh_scrape.db` (its own file, named
   by `--bh`). Proven: the 10/26 copy dry run ran it on `built3` → 391,130 = G1a. It must come AFTER
   8b: translit reads `words.strongs_base` (8b.2 rewrites it), the PN backfill reads `is_pn` + the
   English (8b.2a repairs 16 verses). **Never run step 9 on live** — its DROP would serve a
   fill-less table, and the restore refuses live.
   RE-RUN `scripts/build_abp_surface.py <built> --bh ~/bible-db/bh_scrape.db` (like import_tipnr.py): the `abp_surface`
   side table is keyed by verse_id+position, so any rebuild that SHIFTS positions (splits/merges/bracket peel)
   leaves stale forms until it's rebuilt. Read-only on words/verses. THEN
   `scripts/backfill_abp_surface.py <built> --bh ~/bible-db/bh_scrape.db --apply` — the surface builder writes
   only form-FOUND rows (~345,437; 346,111 on the 10/26 build); the 2026-07-11 backfill added ~13,851 rows for forms it can't
   find (13,183 on 10/26). THEN `scripts/backfill_pn_surface.py <built> --bh ~/bible-db/bh_scrape.db --apply` — the Phase-6 PN
   printed-Greek passes (30,121 name-slot rows, 2026-07-27/28; 31,836 on 10/26; the interlinear Greek line for
   names reads from these). THEN `scripts/build_abp_translit.py <built>` to refill the romanization
   (`abp_surface.translit`, same rows/keys — SBL style from the lexicon, 'h' from the lemma) — it covers
   all backfilled rows too. **The table must now read 391,130** (same-code rebuild; G1a). A
   different total on a same-code rebuild = STOP before 9a.
   **⚠ The 2026-10-25 abp_surface FILL (4,411 writes, table 391,130 → 395,003; record
   `docs/handoffs/CENSUS_abp_surface_fill.md`) is NOT re-created by any builder above** — step 9 drops
   it; 9a puts it back. `apply_abp_surface_fill.py` is one-shot (keyed to 391,130 rows); never re-run it.
9a. **RESTORE THE FILL — on `<built>`, dry run → verdict → `--apply`** (charter G1–G3 §8, wired §9).
   `PYTHONIOENCODING=utf-8 python3 scripts/restore_surface_fill.py <built> --snapshot tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv --lexicon abp_helps/analytical_lexicon.tsv --prefill ~/bible.db.pre-surface-fill-20261025 --report <report.tsv>`
   (read-only; then the same + `--apply`). Same-code expected: table before 391,130 · vs pre-fill
   copy 0 / 0 (G1b) · placed 4,411 (agree-strong 4,057 · agree-weak 354) · unplaced 0 · inserts /
   updates 3,873 / 538 · moved 0; after `--apply`: **G1 = 395,003 exactly** · translit rule changes 0
   · `RESULT: RESTORED, ALL CHECKS PASS`. All or nothing: any unplaced slot or a G1a/G1b miss writes
   NOTHING. `--prefill` (G1b) is for a same-code rebuild only — a rebuild that MOVES slots (the
   edition upgrade) drops it, re-declares these figures, and needs a re-freeze afterwards (handoff
   held item "snapshot staleness"). The restore refuses live by design: it only ever runs here.
9b. **HEALTH FLOOR + ORACLE — on `<built>`.** `health_check.py <built> --no-backup-check
   --no-disk-check`: the `abp_surface rows BELOW floor 395003` line must read `[OK  ] … : 0`
   (floor raised 2026-10-26 from 389,244 — charter G3: builder chain 391,130 + the fill's 3,873
   inserts; shortfall 3,873 exactly = the fill is missing; the 2026-07-16 miss is why the guard
   exists). Then, on a same-code rebuild, the restored table vs live, read-only both ways, must be
   `0|0` (the end-to-end oracle; also proves live's table did not change since `<src>` was taken).
8. **Swap + deploy (the only live action):** `mv bible.db bible_pre_<reason>_<date>.db; mv <built> bible.db`; then
   `bash ~/bible-db/scripts/deploy.sh` — its API reload is the dashboard-Reload equivalent and its
   built-in 5× sweep is the verification (the G2 stale-worker rule — never bare touch). Live goes from
   the old 395,003-row table to the rebuilt 395,003-row table in one move; no fill-less moment. At the
   swap, record G5 (expected, not a block): `pn_hebrew_xref` 519 | 519 · `pn_greek_identity` 21 | 21 ·
   name-slot `strongs_base` 501 (charter §7).
10. **WHERE: on `<built>`, right after step 11, before step 9** (JP ruling after the 10/26 run). RE-GENERATE
   the two-ending adjective soften-lists: run `scripts/build_two_ending.py <built>` on PA — **always give the
   path; with none it reads LIVE** (`build_two_ending.py:36`). It opens the file read-only and reads only
   `words.strongs_base` + `words.morph`, `lsj`, `lexicon` — nothing live-only; it must follow 8b (8b.2
   rewrites `strongs_base`). **Diff before any paste:** compare the output from its `// AUTO-GENERATED` line
   down against `static/src/00b-two-ending.jsx`. Identical → no paste, no build, record "unchanged".
   Different → paste, rebuild `app.js` LOCALLY, commit + push BEFORE step 8, so the step-8 deploy.sh pulls
   it in with the swap (genders/tallies can shift on a rebuild). Drives the "Masculine/Feminine"
   word-study display. Memory `project_two_ending_gender`.
11. **WHERE: on `<built>`, right after 8b.3, before step 10 and step 9** (JP ruling after the 10/26 run —
   same Step-0 answer as step 9: no live-only input). RE-RUN `scripts/build_rendering_norm.py <built>` —
   **always give the path** (with none it opens `bible.db` in the current folder, live from `~/bible-db`;
   a wrong path makes a new empty file). Refills `words.english_head_norm` (the number-fold column the
   Word-study English finder matches on). **WHY IT IS REQUIRED, not optional:** the build empties `words`
   but keeps the column, and its insert never fills it (`build_words_from_abp.py:2154-2157`), so every
   rebuilt row is blank; the finder uses the column whenever it EXISTS (`views_lexicon.py:100-108`,
   `:943-947`), so a swap without step 11 serves an ABP English finder that matches nothing (code trace; the
   live count after the 10/26 swap is in charter §10). Each value
   comes only from the same row's `english_head` through `number_fold.normalize` (plain text function),
   so it must follow everything that writes `english_head` (8b.2a repairs English) — nothing after 8b.3
   does. Also refreshes kjv/bsb `word_norm` (unchanged by a build). Running it again rewrites the same
   values. Memory `project_lexicon_finders`.
   **If it ever has to run on LIVE (the 10/26 exception, charter §10): never within 60 s of a reload**
   (each worker's first-request warm-up writes bible.db, `app.py:441-469`).
LOCAL HARNESS (no PA / no live DB): `tests/test_folded_fixes.py` exercises the six folds on synthetic
rows; `test_build_invariants.py` + `test_strongs_join.py` lock the Strong's invariants (all in CI +
the pre-commit hook). The full rebuild + both-way compare ran locally on a copy 2026-06-09.
FIXED (2026-06-05): Hab 3:14 double-insert. ROOT CAUSE was the ABP source — two byte-identical
`(Hab 3:14)` lines in `abp_texts/abp_ot_texts/abp_habakkuk.txt` (the ONLY duplicated verse marker
in the whole corpus); `iter_verses()`/the build have no per-verse-key dedup, so every rebuild
inserted it twice. Duplicate source line removed → future rebuilds insert it once. Existing live DB
cleaned (without a rebuild) by `scripts/fix_hab314_dupes.py` (scoped to Hab 3:14's verse_id;
collapses dup (verse_id,position) rows to the lowest id). This cleared the lone `misalignment:1`/
`fragmented:1` health warnings + the audit_bracket_order WORDSET hit.
