# TODO

Open work only. Finished and scrapped items (with the why + lessons) are in [TODO_ARCHIVE.md](TODO_ARCHIVE.md).
Each item may end with a small `code:` pointer for Claude to find the right spot — you can skip those lines.

**How this file is laid out (consolidated 2026-11-07):** the first four sections are the work that is
open NOW (the ~20–30 the /wrap limit counts). Everything under **Parked** waits for JP to raise it —
banked, not scheduled, never pre-pitched. **Ideas** = nothing committed.

---

## Active lane — ABP edition upgrade (English line → the app's edition)
- **STATE 11/8: STAGE D CLOSED; gate 2 GREEN and closed** (GATE2-RUN3 at `c37fd41d`, §9.103; declared file
  v4 = G5 delta file + G6 shape exceptions). Built = 8b.0 + REKEY + 8b.1 + §9.96 + 8b.2 + 8b.2a + 8b.3 + SLOT3
  (pn_slot_binding 102 → 105, the 3 Jehoram-of-Judah slots, §9.104). Code REF `f0e60cf7`. **NEXT: stage E —
  step 12 runs on built (12a → 12b → 12c, dry first), the §9.87 punct ruling (583 vs 607) before 9c, then
  9 → 9a → 9b → 9c.** Opener `docs/handoffs/HANDOFF_edition_upgrade_stageE.md` (copy names, figures, logs,
  follow-up lane); out-of-lane follow-ups in `HANDOFF_edition_upgrade_stageC_repin.md`. Rulings =
  `docs/handoffs/DESIGN_q2_build.md` §9 (sole register); charter `docs/handoffs/CHARTER_edition_upgrade.md`.
- Still owed: B's step in `/rebuild-words` · Split 80 → 84 re-declare.
- **`/rebuild-words` step 12, the side-table builders — run on the lane's built copy before step 9** (JP 11/7):
  `build_dotted_lexicon` → `build_word_gloss` → `build_person_metav_link` (+ place-orphan check). Prerequisite
  code LANDED `1ad10cec` (new code REF); procedure text is in `rebuild-words.md` step 12. Each sub-step's figures
  are declared from its dry-run log before `--apply`. Record: `docs/handoffs/DRAFT_rebuild_words_side_tables.md`.
- Rides this rebuild as DECLARED ROWS, never a live patch (JP 10/30): Joh 14:26 word-order (`comforter,`
  on the wrong slot vs `verses.text`; predates 10/25 — entered between the 7/06 S11 swap and 10/25,
  not traced) and Mark 1:9 "of the of" (DESIGN §5). Punct-position 241 = the first frozen member file
  (charter §4.3; the S9 "260" pin is retired — never a member list).
- Cert pin note: `cert_invariants` now pins `abp_corrections_active` = 374 for the BUILT copy (372 per
  §9.59 `f8e814c2` + 2 S-joh14:26 per §9.89; members `abp_corrections_active_built_20261106.txt`); the old "30→51 rides the next deploy" line is superseded. What check 4 reads on
  live before the swap = the lane's question, not resolved here.
- Rollback + snapshot: `bible_pre_trapwire_swap.db` = rollback of record. `~/bible.db.pre-surface-fill-20261025`
  STAYS until the re-freeze (charter §6 step 9c: after the build, on the copy, before = pre-upgrade live)
  passes its own `--check` against the swapped live — it is the frozen snapshot's only "before" side, so
  the rotation/single-rollback rule does not apply to it.
- HOLD (JP 10/30, not this lane): after the upgrade, does the app feed take over the Greek/Strong's role
  from `abp_texts/` + `bh_scrape.db`? Decide after the English-line upgrade lands (charter §3).
- FOLLOW-UP LANE (JP 11/1, §9.62, not this lane): **tag-placement reconciliation** — 604 verses where the
  lexicon-gated passes place Strong's under different words on old vs feed English (keep old rows this
  lane). Members = the `passdiff` rows of PA `~/edition_upgrade_runs/strict_fail_20261031.tsv` (local
  copy `C:\Users\JP\edition_upgrade_runs\pa\passdiff_pa_only_604.tsv`). **The PA file name is a FIXED
  stamp in code (`build_words_from_abp.py:2463`) — a re-run of A's dry run overwrites it; keep the local copy.**

## Owed checks (read-only — JP on PA, or an eyeball)
- **Backup stamp read after the 11/8 13:30 UTC nightly** (the 11/7 run likely failed on the full disk —
  unverified; no manual backup run):
  `cat ~/db_backups/last_success.txt; grep -nE 'XX|!!|Backing up|All backups verified' ~/db_backups/backup.log | tail -12; ls -l ~/db_backups | grep -E 'bible\.db\.'`
  — expect a 11/8 stamp, no `XX`, the 11/6 + 11/7 bible.db copies compressed.
- **Helper audit controls** (refreshed 10/25, not yet re-run on PA): the next `scripts/audit_helper_double_tag.py`
  run should show 4 PASS — 2Ki 11:16 G2007 · Psa 69:21 G4222 · Act 13:19 G2624 (A-review) · Rth 2:16 (B).
  Any FAIL = read it before trusting the counts.
- **word_gloss overrides — PA state unconfirmed.** Overrides added after 2026-06-26 (the +7 from `95c4c97`:
  G3340/G5486/G32/G652/G4352/G86/G1067; εἰμί G1510; G39 `a06a90b`) only reach the card after
  `build_word_gloss.py --apply` on PA. Read-only check:
  `sqlite3 ~/bible-db/bible.db "SELECT strongs, gloss, source FROM word_gloss WHERE strongs IN ('G1510','G32','G652','G4352','G86','G1067','G3340','G5486','G39') ORDER BY strongs"`
  — expect source = override and the glosses in `build_word_gloss.py` OVERRIDES. If not: pull, then
  `--apply` (dry-run first).
- **Nave's retirement — confirm the data side on PA, then close.** The name-path sidebar section is GONE
  (2026-07-16, "Nave's dead code removed (data nuked on PA)"; `30-detail-panel.jsx:589`), and Nave's is not on
  `/credits`, but nothing in the repo shows whether the study.db `type='name'` name-topic rows were deleted:
  `sqlite3 ~/bible-db/study.db "SELECT type, deleted, count(*) FROM entries GROUP BY type, deleted"`.
  The admin-gated `/api/study/for-name` route is a SEPARATE decision (rides Study's return — don't delete
  it reflexively).
- **JP read-only sweeps (from 7/31):** bible-wide count of PN chips with NO Greek line in ABP chip view
  (scopes the Hiram item to the class, not the sighting) · bible-wide `,,` count on `verses.text` (class or
  one-off — feeds the Van der Pool errata list).
- **Eyeballs (verification debt, nothing blocks on them):** Ask-corpus mobile, both states (numbers verified
  at 375px; the VISUAL was never certified — the screenshot tool timed out) · Ask-corpus #20B acceptance
  checks 1–5 + the two mixed-signal cases in `tests/test_scope_detect.py` ("compare the OT and NT view of
  the Sabbath", "charis in greek and hebrew") · post-deploy click-through of Word study / Library on desktop
  + phone (the mobile sheets are the one thing the parity gates can't run locally) · Hebrew "bolder
  English": chip mode + Interlinear OFF should match prose exactly (the dimming while Interlinear is on is
  deliberate; if too strong on his phone = a design-tweak ruling, not a bug).
- **Mobile sheet ledger (never measured):** News' selected why-head inside its sheet (expect ~42.4 per the
  band-with-control ruling) · Day-intro card (needs chronological mode in the harness — inference only) ·
  keyboard-lift (a SHELL-level ruling for all cards; needs a real phone). Spec: `docs/claude/frontend.md`
  → "THE MOBILE SHEET CONTRACT".
- **30 seconds, never done: map the REST of the PN card's outbound links.** Only the occurrence links were
  checked (all go to Word study, `30-detail-panel.jsx:1383-1505`). Read-only.

## Before / with the next words rebuild
- **Rebuild order: the name-header build reads abp_surface before step 9 rebuilds it.** `/rebuild-words`
  8b.3 runs `build_pn_greek_identity.py`, which takes name-slot forms from `abp_surface` joined on
  (verse_id, position) (`build_pn_greek_identity.py:292-305`); step 9 rebuilds that table later — so the
  headers come from the PRE-rebuild surface table matched to the NEW positions (and, while the fill is
  live, from fill forms too — 2 headers already equal a fill form, census §5 Q7). Same shape as the 8/8
  glued-header incident (`HANDOFF_form_lane.md:25`). Read-only census first (which headers would change,
  by member) before any reorder.
- **Geometry-aware unfindability — OBLIGATION before the next ride that MOVES name slots.**
  `audit_unfindability.py` needs identity-level matching (the `attribute_unfindability.py` v4 logic) —
  position-keyed, it fails on exactly the moved class (2,049 on the ②-ride, all attributed, 0 real).
  Named pre-req in `/rebuild-words`.
- **Header receipt order is not repeatable** (found 11/7, 8B3c): `build_pn_greek_identity.py:520-521` sorts
  each name's forms by count only, so tied forms print in row order — two builds of the SAME table wrote
  receipts differing on 9 lines (RDIFF8B3C). Add the form as a second sort key; receipt-only change, run a
  local fingerprint first.
- **The build's closing text calls its source "live"** (`build_words_from_abp.py:2826-2828`): with a copy as
  source, its printed swap command would move the COPY and reload the site. Never run it as printed.
- **`build_rendering_norm.py` loose ends:** (a) "recomputed N" counts rows TOUCHED, not changed — a re-run
  never reads "0 to do"; (b) the printed undo `ALTER TABLE <t> DROP COLUMN <c>` (`:17`, `:113`) fails —
  SQLite refuses to drop an indexed column (`idx_words_ehnorm`); fix the text; (c) `--stats` has no change
  preview; (d) the finder caches "column exists" per worker (`views_lexicon.py:97-108`) — after any column
  drop, reload or the finder errors; (e) always give step 11 an explicit path — the default is `bible.db`
  in the current folder (`:96`) and a bad path creates a new empty file.
- **Re-scope `/rebuild-words` step 7** (JP-held 10/25): mark which items are data-checkable (Eze 31:9
  binding, 1Chr 1:1 identity + metaV bind, Sheshach headers — all readable through the site's read-only
  endpoints) and which must be SEEN (1Ch 13:10: Chip view "the LORD was enraged", Interlinear
  "[²was enraged ¹the LORD]"). Say "card shows H121", not "→ H121" (the word row is G76 since R-2). Lesson
  kept: CC once wrote the chip reading backwards from a pre-July build comment without reading the
  renderer (`59c-library-render.jsx` chip vs interlinear paths).
- **Stale frozen 'none' class in pn_hebrew_xref — rides the next identity rebuild (JP 10/24), no lane before
  then.** The class was set by `retire_hebrew_identity.py` (last run 8/6); identity was rebuilt after the
  8/23 form lane, the retirement wasn't. Now: none→none 1,956 words / 279 numbers · none→lemma-only 458 /
  100 · none→surface 40 / 7 (total 2,454 = the 8/6 declared count — control). **498 words** carry the
  H-number while xref still says 'none' (e.g. H1908 Hadad 1Ki 11:18…, 1Ch 1:47/51). Reader impact not
  traced. Catch-up = re-run the retirement on a copy; its declared split will no longer match, so it halts
  and needs a re-declaration (precedent `docs/tickets/RECLASS_catchup_declaration.md`). Live write → full
  checkpoint lane. **Don't fold with the gentilic none→none backfill** (Parked → names).
- **split_merges JSON: 29 superseded keys** — the PN-star pass fixes 29 of the 237 patch verses upstream
  (they skip on precondition; all 30 adjudicated DISPLAY-EQUAL, split_skips4.log). Retire at the next
  regen; harmless meanwhile. code: scripts/split_merge_fixes.json
- **Header-lane leftovers (read when the header lane is next touched):** the 9/6 landing moved 461 identity
  rows into `surface` (lemma-only→surface 421 + none→surface 40) vs the 451 receipted in
  `docs/handoffs/HANDOFF_gateB_enumeration.md` "Expected picture" — class totals reconcile, 10 rows
  unattributed · `surface` vs `lemma-only` label (reviewer 10/25): the 2 Sheshach rows went surface →
  lemma-only at the swap (accepted) — trace what the label changes on the card, and whether a header that
  matches the page should carry `surface`.
- **Path-C pronoun residue (cert ledger L12, OPEN — Door 1 census closed, FIX not built).** Daniel = **170**
  source-attested pronoun mistags (αὐτός/σύ/ὑμεῖς/ἡμεῖς still numbered G1473), read off `abp_surface`. Census
  surface = Path C's `pronoun_review.tsv` (flagged on raw 1473, so a rebuild re-flags it); control
  `grep '^Dan 4:33' pronoun_review.tsv` must fire before trusting any zero. Corpus-wide raw 3,577 is VOID as
  a mistag count (mixes genuine mistags with blank-english subject/possessive FOLD slots). Queued fix = give
  Path C an `abp_surface` fallback: where Rahlfs can't align, read the number off the ABP form via a fixed
  form→Strong's table for the closed pronoun set (σου→4675, αυτου→846, υμων→5216, ημων→2257 …), WITH a
  per-slot form/english sanity gate (skip a slot whose form isn't pronoun-shaped). Then rebuild — a rebuild,
  not an `abp_corrections` batch (wrong tool at this volume). If batched with other fixes: separately
  pre-registered diff, attribution per (row, column). S9's (P) fix left the Path-C number side untouched.
  Record: `docs/audits/AUDIT_abp_certification.md` §L12 + Door 1 disposition.
- **Cert-lane tool labels:** `verify_prose_leak.py` needs a "Tier B applied" mode (its parser-only check
  FAILs-that-aren't on the 5 Tier-B prose verses against a finished scratch — next rebuild shouldn't
  re-derive this) · `lint_split_wrong_slot.py:325` still prints "sizing: 18,339 / 12,692" → 18,384 / 12,718
  (the real post-S11 scope; both harnesses agree) · `audit_surface_coverage.py`'s stored-vs-live control
  needs the backfill sum (its MISMATCH warning is a permanent false alarm on any backfilled table).

## Small fixes, ready when wanted
- **Ask-corpus mobile `.ac { overflow: hidden }` mask (styles.css ~:5116) — optional tidy-up.** Predates
  the mobile pass and hides any sideways overflow inside Ask-corpus; JP confirmed the phone scroll gone
  (2026-07-15) and it measured clean at 320 + 375, so it masks nothing today. Remove it when someone is in
  there, then re-measure with getBoundingClientRect (scrollWidth reads clean through the clip).
- **health_check false "database is locked"** in the minutes after a deploy (sqlite opens with the 5 s default
  wait; workers' warm-up writes the AI cache — ops.md). code: scripts/health_check.py
- **WAL crumbs (zero-risk):** orphan 0-byte -wal/-shm files in ~/bible-db (bible_test.db-wal,
  bible_test_scratch.db-*, proseonly.db-* — two with no parent). Repo grep 7/31: NO script opens WAL;
  check their file dates, then delete.
- **Invariant #8:** add a `journal_mode=delete` assertion to `cert_invariants.py` (7/7 → 8/8) so a WAL flip
  is caught by the suite, not just the session tripwire.
- **Tests that gate nothing:** `tests/test_lexica_draw_cache.py` fails 5 tests on any machine without the
  live DB (no such table — needs a skip-without-DB guard or a fixture; unticketed known-red is rot) · the
  CI list is an EXPLICIT set of filenames (`.github/workflows/ci.yml` + `scripts/githooks/pre-commit`), so
  real tests don't gate: the alias tests, `test_scope_detect`, `test_thread_skeleton`,
  `test_lexicon_lookup_bands`, **`test_rail_payload_contract`** (pins the rail field names
  `grounded`/`contested`/`alias_note` from the producing side; never added — git log -S). Add to BOTH lists
  after confirming each runs clean in CI's environment, or switch CI to a glob once every file is
  import-clean from repo root.
- **Phone Strong's tags: `.lib-iw-strongs` is set to 9px in the phone CSS** (`static/styles.css:2555`) —
  drift from the "Strong's tags scale, never a fixed px" rule (frontend.md); fix the CSS. (JP ruling 11/7)
- **Delete-account leaves Ask-corpus history behind** (code read, not checked on PA; a separate task card
  was raised). `/api/auth/delete-account` (`views_notes.py` ~:629-652) deletes notes, plan,
  password_resets, tokens, users — NOT `corpus` (saved Ask-the-corpus chats, keyed by the same
  `code = "u<id>"`) and not `ai_usage` (per-user daily counters); its docstring promises "ALL its data".
- **Stale code comments:** `styles.css` ~:83-85 (News panel "matches Library/Word study width" — the token
  below is the deliberately narrower `--news-sidebar-w: 380px`) · `views_notes.py` header (:17-18) lists 5
  tables, there are 7 (+ corpus, ai_usage) · `views_lsj.py:30` cites the deleted memory
  `project_synthesis_no_parse` · `80-lexicon.jsx:129-130` says the alias_note header badge is "not wired
  here" (it is — :1204).
- **Dead CSS:** `.corpus-group*` rules (styles.css ~1534-1571; the `.corpus-groups` container is live) and
  `.ac-construction*` (~4936-4945, ~5197; the banner went in `ffdd966f`) have no callers.
- **`/api/lexicon/books` has no bridge branch** (`views_lexicon.py:1580ff`): for the 6 bridged names its ABP
  answer is empty, so clicking a rendering chip quietly shows the unnarrowed book list (the page's own list
  comes from the bridged profile). Fix = the same `_bridge_if_grey` → `_pn_lemma_rows` door the verses
  endpoint uses. Low stakes. JP-checked 10/24: `books/G1056?corpus=kjv` IS populated; only ABP + the
  no-corpus default come back empty.
- **The `PN:<form>` name-form lane sends one list entry per hit**, so a verse naming the person twice shows
  two rows with the same key (`_pn_lemma_rows` → `lexicon_verses` PN branch; the bridged branches share it).
  Fix: one row per verse carrying all its slots, as lane (f) did.
- **Word-study results sidebar lists only ONE KJV rendering** (galilee shows 62; the card's "galilee, for"
  line and the KJV tab say 63) — display finding.
- **Word-study card header — HEBREW HALF** (Greek half done `7bee235`): the Hebrew card's hero gloss is
  `profile.definition` = `bdb.description` (`views_lexicon.py:1337-1345`), the long paragraph, not
  `word_gloss`. Fix = return the Hebrew `word_gloss` in its own profile field + one frontend line. **Own
  checkpoint (API change).** ⚠ The sourcing comment MUST say **Strong's Hebrew** — the table is named `bdb`
  but is not Brown-Driver-Briggs.
- **Possessive PN card header shows the head-form ("Davids")** — the form-name line title-cases
  `english_head` (a lookup key: lowercased, punctuation stripped). Display-layer only: render the PN entry's
  canonical name or re-title-case the raw english, never the head. Words data is correct.
- **RANGE/Coverage serif gap** — Range + Coverage lines (`20-shared-components.jsx:322`, `:332`) lack the
  `.lex-prose` serif class (styles.css:1439) the senses block + gloss notes use. Two-line fix + rebuild;
  ruled to the Lexica display session; a visual change → JP's yes.
- **Trailing-clause float set copy-pasted in 6 live places** (build + 4 render + port) — unify to one shared
  definition so they can't drift.
- **Library search handed GREEK characters** returns a bare "No matches" (reads as "not in the Bible") — it
  should say the search is English-only (reviewer-ruled 7/29).
- **PARKED (JP 7/15): desktop Ask-corpus strip's hand-inlined plus → `Icon.Plus`** (`52-ask-corpus.jsx`
  `.ac-strip-new` still draws its own at a different stroke width). "Reference the system" — but it MOVES
  DESKTOP PIXELS, so it needs a desktop-scoped pass + JP's eye.

---

## Parked — JP raises (banked, not scheduled)

### ABP text & data lanes
Write-class items are each a checkpoint lane that starts with a PA row read. Opener:
`docs/handoffs/HANDOFF_abp_source_material.md`; Concordance record `docs/handoffs/CENSUS_abp_concordance_diff.md`.
- **Label corrections — 540 + 13 + 152.** 540 + 13 same-slot number disagreements (app vs ours; Isa 39:8
  pos 1 = suspected slot misalignment; the 540 still need the audit to write a TSV) + 152 Concordance
  candidates (Concordance number matches the Lexicon, ours doesn't: 18 repeating pairs = 86 verses incl.
  ἔνθεν 1759.3 → 1759.2 ×28, 4 already in the 13, + 66 singles). List `abp_helps/adj_b_pairs.tsv` /
  `adj_b_verses.tsv`. Precondition: PA row read of all 152 (the 66 singles' rows are unproven).
- **Concordance residue, our side: 25 slot errors + 10 split renderings.** 16 verses where the app has the
  number and its English but none of our rows carries it · 9 starred verses with the word 2+ times in the
  app vs 1 here (Pro 5:7 ἄκυρος doubtful — the app also tags `μη` 207.2) · 10 one-slot-vs-two (the
  split-rendering shape; fold into the next item at its census). Rows `abp_helps/adj_d_rows.tsv`.
  Precondition: PA row read of all 35.
- **Split-rendering double rows, 628** (JP ruled a counting defect 10/25 — the 7/9 polarity-A record had
  left them as legitimate): one Greek word carries two word rows with the same number (2Ki 11:16 `they put
  | upon` G2007; Gen 24:41 `they should | give her` G1325). 174 outside-bracket (on the helper audit's
  A-review list) · **454 both-inside-bracket — NO detector** (the helper audit skips this shape by design).
  Why it matters: the double rows inflate occurrence counts and the ≥2 check. List `abp_helps/split_rendering_628.tsv` (git-ignored); evidence CENSUS §5. Precondition: PA row read of
  all 628 (the 20-verse read was a sample) + a detector for the 454 before any write.
- **Held list (read-by-hand, no writes queued)** — full rows in the handoff + `CENSUS_abp_surface_fill.md`:
  191 name slots with no printed form · 30 vs 27 glued names (re-read the full `~/abp_app_audit_rerun.txt`
  C3 block) · Baal 1Ch 5:23 · 33 unlisted forms · 3 app letters with no ruling · 4 split conflicts + Isa
  41:14 · Deu 4:45 · 60 plain-η spots · 23 + 3 unflagged glued splits · 1,823 empty-lemma slots · MIXED 42
  names (no Concordance verse lists for names) · Concordance leftovers (44 print inconsistencies, 16 label
  holds, 3 unplaced refs, CENSUS §6 classes). **ACTION inside it: 28 English-in-Greek cells** ("δαγγερ")
  pass the app audit's English-font check (it looks for a Latin letter) — the 10/25 fill held all 28, but
  **fix the audit check before the list feeds another write.**
- (d) **English-Greek Index** — last of the purchased helps; not started.
- **Phrase-gloss under-distribution (671, fix (g) deferred):** adjudicate a sample of the "not+verb" class
  vs the ABP app (defect vs ABP negation convention), then distribute true defects dual-ordering-style.
  Detector `scripts/audit_phrase_gloss_underdist.py`.
- **Splitter polarity B — English pooled on a function word** (hand-review only, filed 7/9, reviewer Ruling
  8). 878-case evidence frozen in `scripts/splitter_b_evidence.txt` (finder `audit_helper_double_tag.py`).
  Dominant shape "did/shall not X" on the negation with the verb row blank. Notes for the discriminator:
  Job 18:13 pos 3–4 pools on the PRONOUN (hosts widen beyond negations; both polarities in one verse) · the
  B screen matches only the pooled phrase's LAST word (misses mid-phrase content words) · **Zec 3:2 negative
  control** — pooled English on a CONTENT word's own row is legitimate · fix = a hand-verified re-runnable
  patch in the rebuild path (split_merge_fixes precedent), NOT the auto-splitter; every case adjudicated,
  no batch approval. Standing acceptance rule: re-check "no helper-word chips" on Jud 1:9, Rth 2:16,
  Job 18:13 (chips + search highlighting read the words table).
- **⑤ Bracketed article-slot rows (38) — open ruling, own cycle, own controls.** 20 whole-slot moves
  (cheap) + 18 partial moves needing a NEW position inside an existing ordering (`1Pe 4:2`, an 11-slot
  group whose positions run to 9). **Do not split off the easy 20** — a rule that fires on half a class
  can't be restated later. Exhibit `1Co 3:8` (one `'his own'` repaired, its bracketed twin not).
- **③ Hand-repair lane — 71 candidates** (eyeball DONE 8/3, `docs/audits/LANE3_b2_dispositions.md`):
  gentilic 22 · roster-silent name 41 · possessive 8 (keeps apostrophe-s, JP-ruled) + Mat 27:26.
  Hand-per-row, JP-checkpointed.
- **②-pass gap census (chip/interlinear ordering):** the PN-star pass's 194 cross-blank B-writes left the
  interior blank OUTSIDE the new bracket; chip/interlinear group only consecutive same-bracket runs, so
  those verses likely mis-order there (prose unaffected). Read-only census → dry-run → reviewer. code:
  scripts/lane3_star_gapfix.json · groupForGreekMode in static/src/56-library-order-logic.jsx
- **Carrier-gap attribution + pass-disabled replay** (unparked by the 8/1 rebuild): both only mean something
  against the now-live ruling-10 pass. Ticket §6j; defect set of record = `--predict-vs` (2,520 rows).
- **Bracket-digit sweep — 2 parked verses** (lane closed 7/28–29, `docs/tickets/bracket_digit_sweep.txt`):
  Act 10:28 (app splits into TWO bracket groups) · Num 19:2 ('is not' vs 'has not'). The Van der Pool
  errata list compiles from that ticket once these are ruled or deferred. Template note: the
  marker-permutation sweep, if ever run, inherits the sweep pattern (precondition-pinned rows, intent
  evidence per flagged group, same door).
- **340 identity slots with no words row** (DIAGNOSED 7/29, fix deferred): all 'none'-class position holes
  inside normal verses, NT-heavy (Joh 73, Act 33, Mat 30) — NOT the 345 no-name slots; reads as none-class
  rows stamped from a stale position map. Cert territory — scratch db + pre-registered
  gates, NEVER a live patch. Tool `scripts/audit_pn_lanes.py` lane 2.
- **~48 G1473 (ἐγώ) cells reading reflexives** ("himself/themselves") with a blank lemma — by-design skips of
  the cautious G1473→G846 retag. Future cleanup only.
- **τοῦτο-paradigm mistags — 15 confirmed strays** (enumerated 7/3; retag PARKED; real number G3778):
  G1473 ×11 (Deu 6:25, Ezr 9:14, Hag 2:18, Eze 45:16, Jer 7:1, 8:12, 11:3, 33:4, 44:23, Mat 24:2, Luk 22:51) ·
  G3779 ×2 (Jos 11:16, Jer 5:23) · G846 (Jos 19:8) · G1438 (Rev 19:20). **Match the stored reality:** the
  `form` column is accent-only, circumflex→tonos (τοῦτο→τούτο) — a bare `τουτ*` GLOB misses (a translit
  control read 13, not 3,401, until switched to `τούτ*`/`ταύτ*` on form). ου-/αυ-initial forms excluded on
  purpose (collide with οὕτως / αὐτός). G1438 αυτού/υμάς rows = a separate reflexive class. When run:
  dry-run → ~15-row write, the αἰών-fix pattern.
- **G2455 Jew/Judas split** (ABP crams Ἰουδαῖος ~177 + Ἰούδας ~41 on one number) and **G4119 πλείων merged
  into G4183** — data-surgery (re-tag), NOT alias folds. Low urgency.
- **Versification map for the 148 off-by-one verses** (989 verse_missing slots) — gated on eyeball review of
  neighbor content (a wrong map stores real-looking Greek from the WRONG verse).
- **ἔπω-class tag-synonym rulings table** — the abp_surface "absent" residual is hotspot-shaped (G2036 = 457
  of 2,494); each pair = ONE JP ruling applied via an explicit mapping table, NEVER fuzzy matching.
- **Doubled-mark residual (Jer 46:15 class)** — 11 verses where lifted punctuation accumulated two marks;
  since the 7/11 chip fix they render together (parity with prose). Decide dedupe/keep-first. List with
  `python3 scripts/audit_chip_trail_drop.py bible.db --list`.
- **Double comma 1Ki 9:27 is SOURCE-ATTESTED** (JP checked eSword 7/31) — we match the page; goes on the Van
  der Pool errata list. Normalizing our text = an abp_corrections ruling, never a silent cleanup.
- 2 blank abp_surface `form` cells (Isa 19:2, Eze 40:12) — note-only · stemmer stump filter in
  `lint_split_wrong_slot` misses sibling forms with count <3 — fix only if reused at scale.

### Names, places, entities (R-2 · PN · MetaV)
- **Gentilic cluster:** (1) people-class Greek backfill — retires the genuine none→none rows in
  pn_hebrew_xref (C3-Q1 condition b), adjacent to pile U; related: the 2,358 PN printed-Greek residue
  (`docs/tickets/TICKET_pn_lemma_residue.md` — scrape recovery CLOSED, needs a new source) · (2) `is_pn`
  gaps: Gen 39:17 & 41:12 "hebrew" slots; "midianitish" (Num 25:15) not recognized by
  `er.is_people_group` (changes builder output — never mid-lane) · (3) gentilic PN cards read as places
  (Assyrians → Assyria pin) — reviewer-ruled keep; card should say "people of [region]".
- **R-2 parked (pull, not push; `docs/tickets/alias_leave_list.txt` pile comments):** gentilic Group rows
  binding own Group entities (pile U) · per-reign Pharaoh links (pile V) · ladder possessive-strip (pile P) ·
  vocative-aware peel (Isa 41:14) · josua/shapan/meramoth micro alias batch · the 178 lookup H/G fill-gains
  reverted for byte-identity (per-word review) · binder Greek-key bases extension (PARKED BY RULING; record
  `docs/PLAN_r2_stage3.md`) · Lexica-minted PN numbers (DEFERRED, `TICKET_lexica_pn_numbers.md`).
- **pn_binding — 352 spelling-variant rows (abia→abijah)** → R-2's variant batch; per-pair eyeball +
  roster-freeze check (class hand-check of all 1,310 DONE 7/16, `docs/audits/AUDIT_provenance_sweep.md` §4).
- **Entity data thin spots:** Joram/Israel is TIPNR-only (honest, thin) · the person card serves Israel
  nation/land mentions — both in the entity-data backfill bucket, out of the display tickets by ruling.
- **25-name disambiguation lane** (banked 7/30): one metaV person but 2+ real TIPNR people, so the guard
  declines the card — first customers of a future multi-entity card: Achsah, Alemeth, Asriel, Calcol, Eder,
  Hakkoz, Hanniel, Harbona, Hotham, Ishmaiah, Izhar, Jaasiel, Jekamiah, Joiada, Joshaphat, Mahlah,
  Mehetabel, Nahum, Palti, Rab-saris, Salome, Sharezer, Shemer, Zattu, Zerubbabel.
- **Jacob-class name cards — open lanes only** (shipped arcs in TODO_ARCHIVE + memory
  `project_pn_card_confidence`; census denominator 591 slots / 156 names): 1Ki 4:13 gilead p4 (wrong-paint;
  ships ONLY with the compound-name lane) · Elnatham Ezr 8:16 p15 (variant-spelling appendix) · chapter-grain
  5 (azariah/joash/benaiah/harim — any fold-in RETURNS TO THE REVIEWER) · Jabish ruling (9 "Jabish Gilead"
  verses + gilead 1Ch 10:12 / 2Ch 18:3) · chip-merge (1) compound-number DATA admission (H6100, H7433; card
  number for EVERY merged pair, Greek side too — Dibon Gad G1045; order: verify vs pages + xref layer, land as
  recorded links with receipts, THEN chips/cards wear them) (2) pair co-occurrence count line.
- **Greek-header hand-table polish** — 857 UNRESOLVED names (receipt `greek_header_split.txt` is PA-only,
  regenerated each build). Batch discipline: declension-only names with a page-attested dictionary form;
  real spelling variance stays per-verse; abner/absalom + EGYPT PINNED verse-form. BANKED: per-row-exclusion
  mechanism (egypt ~1,189 + adonijah 38 + artaxerxes). The split file caps each form list (~6) — big names
  need the bh_scrape census. Record `docs/tickets/DRILL_greek_header_backfill.md`.
- **Header leftovers:** 20 glued-blanked rows (ruling 3, 8/24 — now show English; any deserve a real header?
  members in `HANDOFF_gateB_enumeration.md`) · Mat 9:35 scrape typo `Ισηούς` → corrections-lane citation ·
  Mar 2:8 / Mar 14:66 variant forms = hand-table candidates.
- **Same-name / renamed drops (358 slots, opened 7/31 at the G707 ship)** — ruled correct-to-drop (text-first)
  but each carries a defensible link (edom/Esau, horeb/Sinai, molech/Moloch, gehenna…); verbatim list
  `docs/tickets/G707_diff_report.md` Group B. Any allowlist = cert-#7-style machinery, red-first gates.
- **Star-slot G-number (vocative-O residue, own ruling):** Jer 15:5 Ιερουσαλήμ serves lemma-only/no-number
  while G2419 exists — an R-2 identity-rules question (FINDING in `docs/tickets/vocative_head_words.txt`).
- **"Field" oddity** — capitalized 'field' (Isa 29:17 al.) serves a metaV PLACE card via name match (flag only).
- **Hiram 1Ki 9:27: no Greek above the chip in ABP chip view** — the card header has Χειράμ, so likely not a
  scrape gap: chip Greek reads `w.lemma||w.inflected` and abp_surface skips name slots (the 30,126-slot gap).
  DIAGNOSE BEFORE TOUCHING (bh_scrape row + words/abp_surface; do other Greek-headed name chips show Greek?).
  Page-attested-empty = a finding, not a fix. Count the class first (Owed checks).
- **Place-card raw fields:** `area: ">"` on 959 place records — TIPNR place rows use a different column layout
  (the read lands on a '>' marker); person-side `area` is mixed by design too (~1,150 "Tribe of X" vs ~400
  regions/periods). Parser pass (section='place' in `entity_resolution.parse_tipnr`) and/or display
  fallback; check FIRST whether the reader already suppresses it.
- **Place-map pin = interim plurality heuristic** (`_pin_from_rows`, views_metav.py:388): failure mode is
  no-pin, never a misplaced pin, but distinct-point referents never get a pin. Real fix = an entity-level
  join. **Try the MetaV `MainIndex.csv` place distill FIRST** (PlaceID + verse per word — likely solves the 86
  HAND-RESOLVE places from the `scripts/build_tipnr_metav_link.py` dry run, no new source/licensing); fall back
  to OpenBibleInfo (licensing check BEFORE ingest). Shares `tipnr_metav_link` (kind='place').
- **BSB entity-resolution coverage** (wrong-identity risk class): Ephraimites/Num 2:18 (BSB `bene-X`) reaches
  only H1121. First step: Levites Neh 11:3 on BSB — fires = construct-phrase gap; doesn't = cards ABP-only.
- **Dan 1:6 trio** (Azariah/Hananiah/Mishael) — hand-resolve the alias-record residual (steps in
  `docs/handoffs/HANDOFF_metav_person_link.md`).
- **Adonai-card residue:** (2) adonai (H136) rides the PN lane while its blurb calls it "a title for God" —
  revisit as an is_pn classification question · (3) PROVENANCE SEAM: AI summary sits directly above verified
  TIPNR/METAV data in one visual register — the disclaimer carries the whole load.
- **Eponym both-senses upgrade** (JP option (b), 7/11): per-occurrence sense from an explicit JP-ruled pattern
  list on neighbor words ("king of", "land of", "tribe of" → territorial) — never fuzzy guessing; sub-candidate:
  person-vs-territory TALLY for H3063/H3478 ("most" kept meanwhile). code: 30-detail-panel.jsx EPONYM_LINES
- **ABP-tab routing follow-ups** (record `docs/tickets/CHARTER_abp_tab_routing.md`): (a) Zion 168+1, Aram 12+5 —
  header lane folds the lemma-only residual, then they route with no code change · (b) Israel 2,584 /
  Jerusalem 753 — route only via the header lane's `surface` class, never a lemma-only door (reviewer-refused
  9/6) · (d) collisions γαζα G1047/G1048, ηλι G2241/G2242 refused by rule.
- **Deferred by ruling (provenance arc, closed 7/31):** hedged name-match pill conversion · Contested fork-header
  hover (ruled no) · Study-tab tags (wait for Study) · ac-prov-contested left title-only.

### Reader / Library
- **QUEUED, own session (reviewer-approved 8/9): the consumed-jump refactor** — treat a jump's `translation`
  as CONSUMED once applied so no re-send can re-assert it; the real cure for all three hand-stripped sites
  (search jump, page turn, version switch). Touches the load-bearing nav effect. Rule + producers:
  `docs/claude/frontend.md` → "Navigation / jumps".
- **Unselected translation tabs read as disabled** (`.seg-b`'s selected state is a white pill) — fooled JP AND
  the reviewer in one session. **Do NOT "fix" it by graying for real**; a visual change needs JP's yes.
  code: static/src/59b-library-nav.jsx:178
- **Highlight span boundaries in translation text modes** (banked 7/31, H7307 BSB; check KJV too) — diagnose
  first: (1) punctuation bleed (Gen 6:3 `"My Spirit`) — the renderer puts trailing punctuation INSIDE the span
  by construction (`50-corpus-results.jsx` `{w.word}{w.punc}`); (2) suspect targets (Gen 7:22 lights only `of`;
  Gen 26:35) — if alignment genuinely maps רוח there, document, don't "fix"; (3) multi-word spans are plausibly
  correct. Render-layer, no data writes expected.
- **Word-level highlights in KJV** (optional) — kjv_words has positions; the BSB `renderBsbVerse` per-word
  pattern could close it (Compare paints whole-verse in every column on purpose).
- **Badge / verification-token unification** — provenance badges vs "✓ N/N verified" marks (rule in
  `docs/design.md`); converge opportunistically, no sweep.
- **Reader display layers (ABP overrides + divine-name display)** — FUTURE LANE, parked behind batch one +
  FRAME-0. Design: `docs/RENDERING_OVERRIDES.md` ("Reader display layers" section).

### Word study & lexicon
- **Greek text search / inflected-form lookup** (JP hit it 7/29 searching κύριε): Library in-text search is
  English-only by design (views_search.py). If built, it MUST compare accent-insensitively both sides (reuse
  the existing normalizer — `docs/tickets/accent_divergence.txt`; never write a second one) or it inherits the
  4,250-row false-miss class. The κύριε half has its own door: ABP's printed forms already sit under G2962
  (κύριε 663 · κυρίου 2422 · κυρίω 832 · κύριον 591). (The English-only message is under Small fixes.)
- **Word-study profile slow on mega-frequency Greek words** — BASELINE TO BEAT = LIVE 6.5 s / 155 KB on G2316
  (curl-verified 7/25). Not a stage-3 cost. Directions: trim default_verses (first N + lazy rest), one grouped
  aggregate read, or cache hot profiles. code: views_lexicon.py lexicon_profile / _all_books_verses
- **Hebrew-OT word finder is NOT number-folded** (known gap) — needs BOTH a normalized-token side-index in heb.db
  AND a looser `gloss LIKE` prefilter. Don't ship a half-fix (folds one direction, reintroduces the asymmetry).
- **English finder "All" view** still finds/counts Hebrew via KJV (heb.db only under HEB) — switch if the count
  matters · the "All" merged ABP/KJV toggle stays PARKED (double-counts the shared NT; needs a counting rule) ·
  collect JP's held "small tweaks" to the Word-study UI.
- **Search LABEL verb+tail** (low) — "went forth" labels on "forth"; needs a POS rule. code: scripts/parse_abp.py _head_word
- **Root / family word search — needs a real stem field first** (`lexicon` has only free-text `derivation`;
  translit substring leaks — euthéōs matches "theos"). Never build on substring.
- **Structural cards: live-case HIGHLIGHT for prepositions** — light the case-row matching the object's case
  from morph. code: structural.py, views_lexica.py, 20-shared-components.jsx
- **Provenance render — tappable badge tooltips** (rest CLOSED 7/16, `docs/CHARTER_provenance_render.md`): ONE
  shared component + ONE registry keyed by contract §2; own session.
- **LSJ "Lexica" overrides** — contested words (αἰώνιος, δικαιόω) go through the dictionary's fairness fork —
  HOLD δικαιόω, don't hand-write. Strong's-fallback loaded words: curate later; preference = show nothing
  rather than duplicate the headword gloss. code: views_lsj.py _LSJ_OVERRIDES
- **(optional) 46 dotted scholarly-prose hapax have no word_gloss** — they show the LSJ section instead
  (accepted 2026-06-23); hand-finish one-liners only if 100% header coverage is wanted.
- **Dotted-number full audit** (sized 7/7; the FOLD class is FIXED, `2ff5f7d`): no-entry class ~86 numbers (mostly
  δ-cluster) — triage same-word forms (1510.x, 1391, 1364, 133) from foreign leaks (1392, 1377, 1303.x, 1393.2
  ×46, 137.1 ×74); remedy design is its own conversation · **⚠ HOLD-OUT FLAGS — do NOT floor δοξάζω G1392,
  διώκω G1377, δόξα G1391 before the remedy lands or a manual hold-out is placed** (mirrored in
  HANDOFF_lexica_rollout) · inverse-direction audit (dotted rows mapped to the wrong entry) · homonym heuristic
  (καρπός G2590.1 "wrist"; a gloss-divergence grep is the candidate detector) · draw-cache archive for rejected
  draws (`--force` overwrites them). δίδωμι G1325 carries a 1-row leak (1325.1 "mortgaged", Neh 5:3) — not cited
  in the live card. code: scripts/build_dotted_lexicon.py, audit_dotted_lemmas.py
- Ideas, parked: **BDB as Hebrew LSJ-analog** (OpenScriptures BDB, PD 1906; slice per H-number, NOT per root
  article; BDB provenance tag, never LEXICA) · **two-tier word entry** (Summary = the gloss, Expanded = checkable
  EVIDENCE — usage percentages with rare senses linked to their verses, one worked-example verse per sense, a
  one-line provenance seam on loaded words only; NO etymology headline, NO "related concepts", NO our-own commentary; scope to `.wd`) · **"Learn"
  plain-language FAQ** (server-rendered like `/read`) · **PN definition engine** (verse-grounded blurbs for
  people/places/groups — after def-engine calibration).

### Lexica definition engine — law + queue = `docs/handoffs/HANDOFF_lexica_rollout.md`
Authority `docs/audits/AUDIT_lexica_rollout.md`; design backlog `ENGINE_LESSONS.md`. Live cards 85 (DB-counted —
the table is the count). NEXT = see the HANDOFF top pointer (never restated here).
- **Display-layer window — 8 banked tickets** (gloss-note sense anchors · note ordering · V6-era style alignment ·
  LXX ⓘ + multi-sense footnote · header-gloss provenance, 3 sightings · RANGE/Coverage serif gap · marker at the
  citation · sub-use styling) + the **verse-aware gloss-note flag** scoping — full text in the HANDOFF
  "DISPLAY-LAYER WINDOW" section. Window opening UNRULED.
- **Engine: refuse-by-default** — `--require-cache` is now default under `--all` (opt out `--allow-unreviewed`);
  single-word `--apply` stays permissive with a warning (confirm that's the ruling). Still open: pin the reviewed
  draft by a CONTENT hash alongside the input key (three different drafts carried key 1f20c1b1 in one session;
  ENGINE_LESSONS #15/#31).
- **Checker residue** (flag-layer, legal any time; keep `tests/test_lexica_detectors.py` controls green —
  case-awareness is load-bearing, never case-fold): prose-form rendering claims are invisible (the parser reads
  only quoted-gloss-plus-ref bullets — ἁμαρτία pull 2's fabrication went unflagged; ENGINE_LESSONS #24) · the
  gloss × ref cross-pairing within a bullet (document or fix) · dangling-book-ref false fires on tribe/place/prose
  tokens ("daughters of Dan", "Gal", "Gospel/Acts", "in Leviticus") — require adjacency to a ch:vs or exclude
  tribe/place names · (a) δίκτυον *work* bullet analyzed the fragment "work" for the true render "latticed work" —
  needs a fresh draw under the new shape · (b) re-check the "tagging error" speculations in the G1093/G3962/G435
  gloss notes (likely parked-phrase artifacts; JP PA read). code: scripts/build_lexica_def.py
- **Def-engine audit — parked by JP's scope call (7/1):** Ask-corpus inspect card `strongs_def` fallback (Ask
  section) · pinned_core presentation labeling (audit B4 — hand-authored core under the "✓ verified" badge with no
  marker) · **vocabulary watchlist lint** (advisory, read-only; seed: moral, ethical, transcendent, ontological,
  person/personhood, Trinity, unmerited, sacrament, ordinance, hypostasis) + its first run = a one-time sweep of
  frozen definitions · **VERSE_PROMPT vocabulary rule** — queued behind the next controlled re-prove cycle, NOT a
  one-off edit.
- **Open sub-items:** point `lexica_agreement.per_sense` at `_sense_spans` (bold-only reads as phantom wobble) ·
  re-check the 80% / min-4 LXX-provenance cutoff at scale (tuned on 18 words) · step-4 significance judge (human
  eyes now) · verbs + Hebrew first-batches = separate tracks · seam "Build A" feed design (JP rules first) · add a
  covenant-membership/NPP node to `salvation_how` (add_study_graph_salvation.py) · coverage engine: wire
  `coverage_audit` to the card UI, eyeball G166 sense 4, piece A could FORCE a missed collocation into the draw
  (warn-only today), piece C (stratified sampling) DEFERRED — its first evidence: huios+anthrōpos OT-generic vs
  NT-title conflation.
- **FOUR-WORD RE-RUN (G162/G227/G236/G1390, opened 7/14) — may be spent; check AUDIT_lexica_rollout** (its later
  entry reads "parked-word queue COMPLETE — four words characterized, one shipped", G1390 live). If still open:
  JP-gated, real spend; fragility-band watch 0.62–0.75 = stop and report; `t <= 0.706` constraint in code;
  authority = HANDOFF top pointer + ENGINE_LESSONS #63–#65.
- **Some word cards render "loading" only** (JP 7/10) — same cards every time → bad/missing per-word data, not
  timing. First card JP names becomes the repro case. Not mid-calibration.
- `STRUCT_BACKFILL` (`scripts/rank_lexica_candidates.py:69`) — add ναί/ὁμοίως/ποτέ (pending JP one-liner, flag-only).
- **Prose-economy design ticket** — JP's own inquiry; zero-spend, fresh-head design work. Not pre-decided, not
  pre-pitched.

### Ask the corpus & AI synthesis
Decision doc `docs/audits/AUDIT_ask_corpus.md` (order A → B → D → C → E; A `559283f`, B `7b55783`, C `df60d22`
shipped; the "Under construction" banner came down with `ffdd966f`). The 7/2–3 "Batch D/E" alias work in
TODO_ARCHIVE is a separate ad-hoc batch — the audit's D and E below are still open.
- **Batch D/E** — rail + failure UX (F6/F7/F8/F11) · cost + cache: Tier 1 filler-strip normalizer ("what does X
  mean" → "X"; MUST reuse `_LANG_SCOPE_TERMS`/`_TESTAMENT_SCOPE_TERMS` as the never-collapse boundary and inherit
  Batch A's mixed-signal rule; Tier 2 = NO-GO at current volume) · F14 pinned short-circuit · #4 parallelize the
  cognate + Hebrew loops (multi-head queries only; needs an identical-output diff; don't touch the model SQL).
- **Words-in-scope counts should be search-relevant** (JP standing gripe) — rail chips show TOTAL-Bible counts;
  compute per key word over THIS search's pinned pool and ship in the payload — never approximate from curated key
  passages; `hasCount:false` rows get a visibly distinct "no count" state (silent-fallback rule).
  code: ai.py, 52-ask-corpus.jsx + 51-corpus-logic.jsx
- **Ask-corpus inspect card: `strongs_def` fallback (remaining half of audit A3/A4)** — the SQL-gen half is FIXED
  (LSJ context is keys-only via `ai._retrieval_context`; locked by `tests/test_synthesis_no_leak.py`). Still open:
  with no Lexica entry, the inspect card shows `target.definition` = `strongs_def` (ai.py `row["strongs_def"]`;
  `.ac-insp-gloss` in 52-ask-corpus.jsx) unlabeled — the Strong's paraphrase the word card was moved OFF of.
- **Polish leftovers:** the occurrence card's target word = the answer's PRIMARY key word (should be the exact word
  in THAT verse) · recreate the CSS parity gate with a WIDENED prop set (width, max-width, flex-basis, overflow-x/y
  — the old gate missed the News-width + scrollbar bugs) · possible: snippet clamp can hide the match.
- **Whole-book KJV/ABP comparison** ("acts kjv vs abp" returns the nudge) — the naive `english_head != kw.word`
  join floods (two translations rarely match), so decide FIRST which differences are worth surfacing (same Strong's
  with clearly different English families; cap to N; or a curated loaded-word set). Design before code.
- **Hebrew-word SQL-gen misses the ABP words table** (a Hebrew number against Greek `words` = guaranteed 0; heb.db
  + cognate supplements carry the answer). Fix = query the LXX counterpart — ONE card with the LXX seam work; don't
  build a throwaway H→G map, wait for the seam.
- **Lexical-texture panel follow-ups:** LXX seam range-preservation (does the Greek keep esh's range at ~8%
  divergence?) · re-run `scripts/add_lemma_plain.py` so the Hebrew exact-match fast-path goes live again.
- **Curation / answer-shape redesign** — evidence list reads spammy; label thematic verses (Rom 14:5 on a Sabbath
  query) — DON'T drop them (Gen 1:26 divine council relies on that path); broad topics are thin. Small residuals
  (only if they bug JP): hub-verse weighting, residual framing lean, LSJ blurb has no citation after-check.
- **Shared AI "house style" voice snippet** — ONE core.py snippet with the VOICE only; LENGTH stays split by model
  (HARD sentence counts on Haiku, SOFT on Sonnet — Haiku overran the ceiling on a maximal chapter); do NOT convert
  `_PN_SYSTEM`'s hard cap. A prompt edit refreshes that category's cache (expected).
- **AI verse-synthesis revisit (umbrella, bank only — exhibits verbatim in `docs/claude/ai.md`):**
  1. **Divine-name drift** ("Yahweh"/"YHWH" vs ABP's "the LORD", Jer 46:25 exhibit) — JP rules ONE convention,
     then a prompt line PLUS a post-generation check (prompt-only drifts). Pairs with the voice snippet.
  2. **Unhedged contested assertion** — the 1Co 8:5 Connection panel states the Psa 82 "human rulers" reading flat.
     The HARD variant: it adjudicated a CITED passage, so a caution list keyed to the panel's own passage misses
     it. Open questions: contested-topics prompt instruction; hand-curated caution list; auditability (panels
     regenerate, exhibits vanish). **Start by diffing views_summary.py vs views_crossref.py prompts** — the Psa 82
     chapter summary hedged right.
  3. **Nimrod fidelity watch** — the synth READS ABP, so Gen 10:9 should keep ABP/LXX's "giant hunter", not KJV's
     "mighty hunter". Test live; if it says "mighty hunter", fix with a POSITIVE line in `_CURATION_SYSTEM` (+ mirror
     `_AI_SYSTEM_TMPL`) to use the supplied verses' wording — not a blacklist. Memory `project_ai_synthesis_quality`.
- **AI blurb verse-check cert** (SCOPED, not started) — make "verse-checked" a state a blurb can EARN;
  `docs/tickets/TICKET_blurb_verse_check.md` (incl. specimen #3, Num 33:45). Behind the Lexica batch tooling.
- **PD reference works** — Trench (NT synonyms) + Girdlestone (OT synonyms) are the standout; Thayer/Vine/Gesenius
  easy adds. PD commentaries = IMPORTED interpretation — only walled off + labeled "tradition, not the text".
  License caution: free text inside a not-free database wrapper — use original scans / known-free digitizations.

### Study tab — ON HOLD (deprioritized, JP 7/15; waits for JP to raise it)
- Study-on-mobile shell (Topics/Graphs/Seams still on the old `.study-mobile` branch; copy the three landed
  News/Ask/Notes commits; opener `docs/handoffs/HANDOFF_study_mobile.md`) · per-item inspect DETAIL (right
  inspect is ZoneEmpty everywhere; spec: Topics = clicked verse in context, Graphs = clicked claim/node's
  grounding, Seams = clicked fork's grounding). code: static/src/55-study.jsx
- **Study graphs bits:** mobile graph = narrate a traversal, NOT a shrunk chart — carry CONTESTED edges as a
  colored TAG, not fine dashes, or the map becomes a verdict machine · per-study lexeme strip · Strong's deep-link
  from a lexeme node · drop "Sin (1)/(2)" from `_COMMON`. code: argmap.py, views_study.py
- **Pointer click-through** — the ἵνα `contest_graph` breadcrumb + dikaioō `graph_ref` are plain text; thread an
  onOpenGraph callback (the `studyPending`/`openEntry` plumbing exists).
- **Published study topics shape AI-search answers** (divine council = test case: retire the hardcoded
  `_DIVINE_COUNCIL_*` one-off once a topic reproduces it). GUARDRAIL: only PUBLISHED text-first TOPICS feed an
  answer, never arguments; saved answers key on the topic's verse list.
- **"Loaded terms" series** (seven-slot skeleton; charis, baptizō, metanoia, ekklesia, hamartia, propitiation) —
  settle standalone Studies vs featured-in-Word-study first · **topic browser** (category names only, our own
  verses + summaries).
- `/api/study/for-name` route survival — separate decision from the Nave's data (see Owed checks).

### News — ON HOLD (JP 2026-10-31)
- **OPEN step (4) of the dedupe lane: `--fill-links`** for the 2,283 unlinked Google rows scored 5+ (mostly older
  than the 60-day page-date backfill), then re-report + apply. Rollback copy `~/db_backups/news.db.pre-merge-2026-10-25`.
  Left unmerged on purpose: 39 B1 sets (~25 different articles, 6 EWTN slug renames now 404, ~8 unreachable).
- **PARKED — re-enable the nightly archive backfill (`resolve_backfill_all.py`)?** Commented out of daily.sh since
  it crashed mid write-back on 2026-07-05 and corrupted news.db (`d6b8c310`). The journal-mode root cause is fixed
  (`bbbe0963`: every news opener uses DELETE), but turning the step back on was never decided. Until then
  Google-wrapper faces older than the 50h forward-fill window stay wrappers (still clickable). code:
  scripts/news/daily.sh, scripts/news/resolve_backfill_all.py
- **PARKED — News page load is 70–150 s (measured 11/8, PA access log, Nov 6–8).** `/api/news/all` sends the
  WHOLE scored archive (30,207 rows, 10.7 MB, every score incl. below the 5 floor, with summaries); a rebuild is
  ~70–150 s, a same-worker repeat 3.7 s; two loads abandoned by the browser (499). Suspect, not yet timed: the
  22,834 unlabeled (score <5) rows go through the lexical `_cluster` (each row vs every group), which grows
  nightly; the `_ALL_CACHE` is per worker and busts on every nightly pull. Not caused by any change since 10/31
  (only request-path commits: Admin Stats, `d6df215e`/`dc2be0c0`). Fix = a design call (what the page must send:
  the FeedShape "buried" readout and the Any-score filter read below-floor rows). Time the pieces on PA before
  choosing. Web-log reads: PA writes the real client IP as a quoted field before `response-time=` — filter with
  `sed -E 's/^[^ ]+ //; s/"[^"]*" (response-time=)/\1/; s/key=[^ &"]*/key=HIDDEN/g'`.
  code: views_news.py `_all_cards` / `_cluster` / `all_news`
- **Corroboration as a rank input** (Aug 14 ruling, layer 3) — stays parked until labeler fusion is measurably down
  (`relabel_check.py --run`); otherwise it rewards falsely "well-corroborated" fused cards.
- **Admin's LIVE Keep/Dismiss squeeze the headline on a phone** (Kept rows ~148px / 5 lines) — pre-existing; "a
  control that works earns its row"; stacking actions under the headline = a design call on live controls.
  code: static/src/84-news.jsx `.news-actions`
- **Reader bookmarks** (review table is per-person, keeps feed nothing) · **shareable News deep link** (`/?view=news`,
  ideally per-story, survives signup; copy the `?news=`/`?b=`/`?lex=` pattern in 90-app.jsx) · **beast-arm badge**
  (thread→arm map isn't 1:1 — hand-authored by JP; code: views_news.py map, 84-news.jsx).
- Eyeballs when News returns: copy shortlist pastes clean links; a card title click lands on the real outlet ·
  paywall spot-check (FREE outlet as card face, 🔒 on the paywalled source, stable across presets) · News tab in the
  mobile bottom nav (admin) + News inspect balance vs the `.news-bar` row.

### Accounts, Ko-fi, licensing, non-canon, tests
- **Notes:** Apple sign-in (needs a paid Apple Developer account) · email campaigns / reading-plan mailings.
- **Ko-fi:** USER-SIDE — set up the monthly "Berean" tier + claim instructions in its welcome message · OPTIONAL —
  Ko-fi webhook → auto-set the berean role (cap stays 10). code: views_notes.py
- **Licensing:** the live page is `templates/seo/credits.html`, NOT CREDITS.md — keep both in step · optional
  thank-you note to OpenBible.info.
- **Non-canon:** possible next books (Jasher 1840 — beware the pseudo-Jasher; 4 Baruch; Apocalypse of Zephaniah;
  Joseph and Aseneth) · wire the `<book>_words` tables into the Lexicon/Search tabs once, generically (the
  "In the [book]" count + LXX link are HIDDEN since 6/11 because they dead-ended) · KNOWN GAP: no Hebrew/Aramaic
  interlinear for a non-canon text (G-number join + LSJ routing are hard-wired).
- **Web-route test coverage** — endpoint snapshot harness (`scripts/snapshot_endpoints.py`) + browser click-through
  are MANUAL, so routes/clicks aren't checked per push. The main test gap if you ever want to close it.

### Future projects (banked — JP raises; framing in memory)
- **Dataset publication with receipts** — after the Greek PN work completes (or ABP permission resolves): standoff
  annotation + receipts + errata upstream. Framing: memory `project_licensing_attributions`.
- **Genealogy-of-Jesus map** — the person-card tag navigates to a walkable lineage (both Mat 1 / Luk 3 lines, edge
  receipts). Framing: memory `project_metav_expansion`.
- **Grammar search** (search the morph tags — ~78% of ABP Greek, the Hebrew OT in full; engine + UI missing) — the
  biggest gap vs Logos base tier.
- **People/places hub + timelines** — a browsable "Factbook" (cards open only on a word click today) + timelines.

---

## Ideas / someday (nothing committed — grab whichever appeals)
- **Reach is the real gap, not features** — a one-person app few people know about; the missing piece is marketing.
- **Reader / layout:** word detail as a floating card · collapsing toolbar (lib-bar → one compact pill) ·
  chronological timeline scrubber · one smart search box (Word study + Ask, routes by what you typed).
- **Chrono Phase 2 — PARKED (JP wants eventually, not queued):** exact hand-curated per-reading dates; SUB-ERAS
  (Saul / David / Solomon — a range or a point); milestone labels ON the timeline track; a stitched single-scroll
  "today's reading". code: static/src/59-dayintro.jsx, 58-dayplan.jsx, 60-library.jsx
- **LXX transliterated-phrase pseudo-names** (Jer 46:17 "Saon Esbeie Moed") — no entity can ever bind; a
  hand-curated note table (likely a dozen cases) instead of the AI shrug. First step: enumerate unbound PN clicks
  with no TIPNR/metaV candidate. code: Fix-A fallback in views_metav.py
- **Map tab** (coordinates + map library already in place) · **meaning-based passage search** (needs a concept index).
- **More texts:** Textus Receptus NT (same numbering; showing where two Greek texts differ) · PD translations (ASV,
  YLT, Darby, Geneva) into Compare · Rahlfs LXX as its OWN parallel Greek OT, never a patch to ABP (LICENSE FLAG:
  CATSS/CCAT is not MIT) · fuller Greek morphology from CATSS / macula-greek (the ABP-native fill was SCRAPPED) ·
  dramatized KJV audio + verse-by-verse karaoke · extra-biblical texts as a separate section, never mixed into canon.
- **Dead Sea Scrolls** — wanted, hardest: no PD English, mostly Hebrew/Aramaic fragments (needs the H-number/RTL
  plumbing). Realistic first step: a 1QIsaa vs Masoretic variants COMPARE view.
