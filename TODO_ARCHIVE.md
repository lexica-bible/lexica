# TODO — Archive (finished & scrapped work)

History and "don't redo this" notes. Nothing here is open. Deep detail lives in the
memory files; this is the plain-English record plus the rollback database names and the
few "leave it alone" verdicts worth keeping.

---

## Word-study English finder — singular/plural number-fold — DONE + LIVE 2026-07-01
Full record: memory `project_lexicon_number_fold`.
- **The bug:** `/api/lexicon/english` matched a typed word letter-for-letter against attested renderings, so
  a singular query missed a plural-only rendering — searching "magistrate" never found theos G2316 (rendered
  "magistrates" at Exo 22:28, elohim-as-rulers). Reverse too.
- **The fix:** a precomputed `*_norm` column on each rendering table (`words.english_head_norm`, kjv/bsb
  `word_norm`) holds `number_fold.normalize(rendering)`; the finder matches `<col>_norm = normalize(query)`.
  Same function both sides, no inverse. `number_fold.py` = curated irregular map (attested forms only) +
  careful singularizer (-ss/-ous/-es/-ies traps) + per-token for phrase heads. Deploy-safe fallback via
  `_has_norm`.
- **How it was gated:** backfill the columns, then an UNLIMITED disjoint-Strong's collision read across
  ABP/KJV/BSB (a legit fold shares a Strong's across its forms; a cross-word collision shares none). Caught
  exactly 3 real over-folds (news→new, does→doe, Heres→here) + a phrase leak ("the news"→"the new"), all
  fixed, final read clean. LESSON: an early LIMIT-200 collision read sorted the dangerous low-count pairs off
  the bottom — run collision reads with NO limit.
- **Drift guard:** `scripts/build_rendering_norm.py` (idempotent, also the DDL). Wired into the words-rebuild
  dependent-builder tail + `/rebuild-words` step 11, and `recompute_norms(only="bsb_words")` at the tail of
  `load_bsb_words.py`. kjv_words is static → one-time backfill.
- **KNOWN GAP (see TODO open items):** the Hebrew-OT discovery branch is NOT folded.
- **Follow-on — surface + bold the matched rendering (commits 8600646 + 15bd3ef):** the results summary
  shows the top-8 renderings per source, so a word matched via a rare rendering below the cap (G746
  "magistrates" ×1, H3423 "magistrate" ×1) never showed. `lexicon_english`'s `_top_glosses_*` now keep the
  full list (dropped a Python slice, no extra DB cost); `_fold` bolds the matched rendering (`normalize`
  compare, reusing the search fold) and surfaces it in its sorted spot if buried; a `{trunc:true}` sentinel
  → trailing " …" whenever a source has more forms than shown (independent of the match). Frontend shared
  `renderRend()` bolds via `.glrow-match` (weight only). Lookup/translit path unchanged.

## Study tab restructure + admin-only gate + concept-topic deprecation — DONE + LIVE 2026-07-01
Full record: memory `project_study_modules` + `project_three_zone_shell`.
- **Uniform master-detail shell** — Topics, Graphs AND Seams now share ONE `<Shell>` frame: LEFT rail = the
  list, CENTER = the content (TopicPage / GraphPage / the seam's both-priors `SeamPriors`, mounts once),
  RIGHT = a ZoneEmpty "covenant" (per-item detail wiring DEFERRED — see the open follow-ups). ONE top-strip
  switcher (`study-sub`, left) + tools (Seams filter / admin preview toggle, right); `seam-rail` RETIRED.
  Inspect top:0 + `.app.view-study` pill offset (matches Word study). Took several wrong turns (left-list ↔
  Seams-shape pivots) before landing on the left-list master-detail — that IS the settled shape, don't
  re-derive. Commit a94e5a5.
- **Whole Study tab is ADMIN-ONLY** (reversed the 2026-06-16 public go-live). Link hidden (`{owner && …}` in
  the desktop Header + mobile tab) AND a single `@bp.before_request` on the study blueprint 403s EVERY
  `/api/study/*` route for non-admins; `/api/lexica/seams` hard-gated the same way (the public per-word card
  `/api/lexica/<strongs>` untouched). Intended: retires the reader's Nave's-topical block (`for-name`) + the
  xref "In studies:" line (`for-verse`) — they vanish gracefully. Verified on the box (403s + word-card 404 =
  not-gated). Commit 0ab7bad.
- **Imported Nave's/MetaV CONCEPT topics DEPRECATED (removed)** — supersedes the old "unpublish the imported
  concepts" plan (which only hid them; as admin you still saw the drafts). `scripts/deprecate_concept_topics.py`
  (dry-run default; backs up study.db; `--apply` soft-deletes `type='topic' AND json source='metav'`; `--undo`
  reverses). Soft-delete works because every study query — admin list included (views_study.py:813) — filters
  `deleted=0` (verified before applying). **Ran on PA 2026-07-01: 1817 concept topics removed, Divine Council
  (blank source) + the 696 name-topics (`type='name'`) + the Library Nave's sidebar block all kept.** Don't
  re-run `load_study_topics.py` (it refills the list). Undo = `--undo --apply`. Commit 371e45d.

## Shell unification — Notes + Seam index + News right-rail — DONE + LIVE 2026-07-01
Three more surfaces onto the shared `Shell`, plus News-rail follow-ups. Full record: memory
`project_three_zone_shell`, `project_lexica_dictionary`, `project_study_modules`, `project_news_watch`.
- **NOTES (desktop) on `<Shell>`** — rail = the note index, strip = search/filter, center = the editor
  (edited IN-TAB now, no more bounce to the Library), right = the note's anchored verse (`VerseRow`, a
  `‹ Read in context` link jumps to the reader). Editor guts factored into `useNoteEditor` + `NoteEditFields`
  (35-notes.jsx) so the Library rail editor and the tab editor CAN'T drift; `JournalView` split so its page
  list can sit in the rail. Right inspect floats top:0 with a header band (flipped from the safe below-nav
  default once seen). Mobile unchanged (tap → jump to the Library editor).
  - Deliberately NO "new blank note" button: a verse note IS its anchor; a note without one is a journal
    page (own creation path). A strip-level "new note" would need a verse-picker = the reader in a costume.
- **SEAM INDEX** — a new `Seams` Study module (`SeamIndex`, 55-study.jsx) on `<Shell>`: rail = the
  Topics·Graphs·Seams section switcher, center = the contested-word list (badge = `divergence_type`, tag =
  `lead_flip`), right = the both-priors card reusing `LexicaFork` + a live graph link. Pure READ over
  `lexica_def` fork data via a new `/api/lexica/seams` (views_lexica.py) — no engine touch. Two hand-authored
  axes added to each `CONTESTED` entry (build_lexica_def.py): `divergence_type` (referent|content|loaded, the
  badge) + `lead_flip` (does the lead sense flip when the priors swap — the "Different-lead" filter; values
  from the 2026-06-25 run: ekklesia/dikaioō/aionios/charis=true). psyche (fork-absent control) drops out
  naturally. LESSON (JP): keep the two axes SEPARATE — `divergence_type` is descriptive (why), `lead_flip` is
  the computed swap-test (whether); collapsing them would have put theos in "Different-lead" wrongly.
  **PA step owed:** `build_lexica_def.py --resplit --all --apply` to write the fields into the stored forks.
- **NEWS right-rail (selected state)** — the inspect was ALWAYS the feed-shape dashboard; now it flips: click
  a card → why-it-scored (`ai_why` + score + thread + the verbatim `queries.py` two-beasts lens) + sources
  (deduped per outlet, each with `via` = Google News/RSS) + the cluster's article list; `‹ Watch` resets.
  Card BODY click = select; headline + Keep/Dismiss keep their own action. Backend: one read-only add — `via`
  per member from the stored `query` column (no re-score; the in-memory feed cache rebuilds on the deploy
  reload). **Gate check (JP):** the "why-it-scored" data was a RENDER, not an engine touch — confirmed on PA
  that every scored row already stores `ai_why` (7136/7136). Then card cleanup: date = PEAK day only (dropped
  "· latest"); moved the ai_why + the "+N more" source expander OFF the card into the rail (card = headline +
  thread + date + a plain "N sources" count). "‹ Watch" moved to the RIGHT to match the Library overlay's
  `.detail-back`. Beast-arm badge DEFERRED (thread→arm isn't 1:1 — authored follow-up, still open).
- **News tab re-fetch on tab-return — FIXED.** News was the ONE main tab conditionally rendered
  (`mainView === "news" && <NewsView/>`), so leaving it UNMOUNTED the component → state lost → the initial
  fetch re-ran on every return. Diagnosed before patching (not a focus refire; a plain unmount). Fix = the
  sibling pattern: mount on first visit, keep mounted under `display:none` (`newsEverVisited`, twin of
  `libEverVisited`). State + scroll survive; new articles only via the Refresh button.
- **display:none scroll rule — corrected (was over-general).** The old note ("display:none wipes an overflow
  box's scrollTop in Chrome") is TRUE ONLY when the box is `position:absolute` (the RightStack layers). In
  NORMAL document flow scroll SURVIVES display:none — verified live in Chrome 149 with a minimal repro (both
  cases tested), so the keep-mounted News feed keeps its scroll. Corrected in CLAUDE.md + the 22-shell.jsx
  comment + memory `project_three_zone_shell`. So display:none is NOT universally unsafe.
- **News nav item flashed ~500ms on refresh in Firefox — FIXED.** News is the only GATED nav item
  (`showNews = owner || newsReader`); `newsReader` seeds synchronously from localStorage but `owner` started
  false and only flipped true after the async `/api/stats/owner` fetch (after first paint) — so the owner's
  first frame had no News. Firefox paints that frame; Chrome's timing hid it. Fix = seed `owner`
  synchronously from a cached `lexica.owner.v1`, mirroring `newsReader`; the fetch still runs + rewrites the
  cache. SECURITY check (JP): safe because every News endpoint enforces `_can_read()` server-side (404 to a
  non-admin/non-key) — a forged cache only flashes an empty tab, never real data. Optimistic nav UI, not a
  bypass.

## Ask the corpus — first real RightStack consumer + exact-lemma pin — DONE + LIVE 2026-07-01
The first surface to USE the shell for NEW content (not a parity migration). Full record: memory
`project_three_zone_shell` + `project_ai_search_architecture` + build spec `HANDOFF_corpus_shell.md`.
- **Prereq — exact-lemma pin.** Corpus had NO deterministic word resolution: a typed lemma (γῆ) went
  straight to Haiku's English-concept step, so the occurrence list was the model's guess (pulled -γη
  look-alikes). `_resolve_exact_lemma` (ai.py) now pins a bare single Greek/Hebrew word to its EXACT
  Strong's via the indexed `lemma_plain` and overrides the model's sql + key word. `_CACHE_CODE_VER`→40.
  - **SNAG found + fixed:** `lemma_plain` was documented LIVE since 2026-06-26 but was actually MISSING on
    the live db (a reload had dropped it) — so Word-study's exact-match-first was ALSO asleep. Re-ran
    `scripts/add_lemma_plain.py --apply` (lexicon 5,523 + bdb 8,674). LESSON: verify the column after any
    reload. See memory `project_lexicon_search_overmatch`.
  - **Latent streaming bug surfaced + fixed:** the Hebrew pin (empty base SQL) exposed a pre-existing
    `NameError` — `_assemble_payload` (the SSE tail, lifted out of `ai_search`) reached for the nested
    `_is_thematic` it can't see. Fresh streamed searches with a model-named extra verse OR zero base rows
    hit it; cache hits + normal Greek searches skipped it. Fixed by binding a local `_is_thematic` to the
    `target_bases` param (commit 04cf9a1). NOT caused by the pin.
- **Shell frame (step 2):** desktop `AskCorpusView` → `<Shell>`, composer in a top strip, mobile kept its
  old `.ac` layout.
- **Inspect drill (step 3):** a synthesis verse-ref CHIP peeks into the RightStack rail
  (occurrence → fork → word), KEY PASSAGES rows keep the jump-to-Library (chip = peek, row = leave —
  corrected after I first mis-wired the row body as the peek). The frequency panel moved to the rail's idle
  state, unframed. Floats top:0 (unified, `.ac-rstack`) after the user rejected the below-nav "cut off" look.
- **Still owed:** a visual-polish pass (JP batching) — see the open item in TODO.md. UTF-8 console lesson
  saved (memory `feedback_utf8_console_output`).

## Three-zone shell — primitives built + 3 shipped surfaces migrated — DONE 2026-06-30
The shared navigate/read/inspect frame went from shared CSS to real components, and all THREE shipped
surfaces (News, Word study, Library) were migrated parity-only. Full record + gate methods: memory
`project_three_zone_shell`.
- **Built `Shell` + `RightStack`** in `static/src/22-shell.jsx` (greenfield, unwired first): Shell = the
  four-slot frame + a real desktop→mobile collapse (bottom toolbar + sheets); RightStack = the
  inspect-panel stack (parent owns the array, child pushes, center-select resets).
- **Migrated** News (`648f757`) + Word study (`0366ad2`) onto `<Shell>` (desktop; each keeps its own
  mobile branch), and Library (`b4c4827`) — its 5 inspect panels carry the shared `.zinspect`,
  `.detail-side` slimmed to extras, App-level gating machine untouched (NARROW, not RightStack).
  `ThreeZone` retired (`14e9149`).
- **Lessons:** (1) hidden stack layers must use `visibility`, NOT `display:none` — display:none wipes an
  overflow box's scrollTop in Chrome. (2) top:0 split — a SHIPPED surface keeps its float (`.zinspect`
  top:0), a NEW surface starts below the nav (`.zinspect.rstack`). (3) prove parity with throwaway gates:
  frame DOM + computed-style diff, and for Library a Node state-machine gate that drives TRANSITION
  sequences (word-over-xref → close → uncover-and-state-survives), not just a snapshot. (4)
  `59-dayintro.jsx` is CRLF — the Edit tool flipped it to LF; restore with `git checkout` + `sed -i`.
- **Owed:** post-deploy human click-through of the 3 tabs on desktop + phone (mobile sheets can't run
  locally — bible.db/news.db are PA-only).

---

## Hebrews 13 missing from the corpus — restored — DONE 2026-06-30
Heb 13 (25 verses) was absent: the `verses` table held Heb 1–12 only. A per-chapter count audit
across all 66 books found it was Hebrews-ONLY — one dropped chapter, not an import-wide failure.
- **Root cause (cascade):** the ABP source file `abp_hebrews.txt` was missing ch 13 (a copy-paste
  gap — it ended at 12:29). The words table hangs the BibleHub scrape onto verse rows that already
  exist, so with no Heb 13 verse row, the Heb 13 scrape words were SKIPPED. One missing thing (the
  verse rows) dropped the whole chapter. bh_scrape.db HAD Heb 13 all along.
- **Lesson:** the words build only emits rows for verses already in the `verses` table; a missing
  verse row silently drops its words (the build counts the skip, never corrupts). Short source =
  silently-dropped chapter, not a loud error. The per-verse parser can't lose verses mid-chapter,
  so a per-chapter count is the right detector.
- **Fix (additive, NOT a rebuild):** user pasted the 25 verses in ABP format; appended to
  `abp_hebrews.txt` (LF — that file's blob is LF, repo is mixed, match a file's endings). New
  `scripts/add_hebrews13.py` adds ONLY Heb 13, reusing the canonical `build_words_from_abp`
  per-verse machinery so the rows match the corpus. `--apply` is additive-only + refuses a re-run.
- **The proof (reusable):** the dry-run snapshots live to a throwaway copy, REGENERATES Heb 12
  through the same path and diffs it byte-for-byte (✅ IDENTICAL on 483 build-owned columns) —
  proving the path reproduces the canonical build, so the Heb 13 rows are trustworthy. Pure read +
  local build, no network. PROOF 2 confirmed the TAGNT pronoun fix fired on Heb 13 (3rd-person
  G1473→G846, 1st/2nd person left alone).
- **Documentation-push catch:** reading the full `/rebuild-words` checklist found a blind spot the
  chapter-12 proof can't see — Heb 13:12 has the `ὁ+ἴδιος` "his own" (G2398) shape that
  `fix_idios_own` (a `finish_rebuild.sh` tail patch, not the build) relocates. The dry-run now also
  runs the local idempotent tail patches against the copy; `--apply`'s follow-up is the canonical
  `finish_rebuild.sh` + the side-table builders + the verify gates.
- **Verified live:** Hebrews → 13 chapters (13=25 verses); names resolved (Jesus G2424 ×4,
  Timothy G5095, Italy G2482); 13:12 "his own" on the G2398 slot; `/read/hebrews/13` → 200.
- One cosmetic leftover, NOT fixed (deliberately — don't edit proven code for a nit): the dry-run's
  own logging splices a stray verse-text line into one word-row block; cause not reproducible
  locally (no scrape/TAGNT on the dev box). Diagnostic-only, no data impact.
Full record: memory `project_hebrews13_restore`.

---

## αἰών/αἰώνιος mistag (Jer 49:13 + Hab 3:6) + Psa 24:7 numbering — DONE 2026-06-29
Two reviewer-flagged corpus tags, query-first then fixed.
- **Jer 49:13 + Hab 3:6 — TWO source typos, fixed at root.** The query sweep proved it was NOT a class
  confusion — only two noun forms wrongly tagged the adjective G166: Jer 49:13 pos 28 `αιώνα` (accusative of
  the noun αἰών) and Hab 3:6 pos 19 `αιώνος` (genitive). Both are plain noun forms BibleHub's ABP mis-tagged
  as αἰώνιος (G165 and G166 are next-door, noun vs adjective). Confirmed in `bh_scrape.db` (`3588-166 τον
  αιώνα` / `166 αιώνος`) — our build copies the source number faithfully, so it's a source slip, not our code.
  Fixed in BOTH places: live `words` (set strongs=165/strongs_base=G165 on the two slots) AND `bh_scrape.db`
  (so a future rebuild reproduces the right number). The αἰώνιος card was rebuilt to drop the bad evidence —
  `build_lexica_def.py --word G166 --apply --force` (39/39 pass): Jer 49:13 dropped entirely (it had only the
  mistagged noun); Hab 3:6 correctly STAYED, because pos 22 `αιώνιαι` "his eternal" is a genuine G166 adjective
  in the same verse. Surgical proof the root fix landed. **No αἰών G165 Lexica card exists**, so no G165
  rebuild was run (would have built an unwanted new card + a paid model call).
- **GOTCHA worth keeping:** `build_lexica_def.py --word G## --apply` SKIPS as "up to date" after a data-only
  change — the skip-stamp is the PROMPT fingerprint, not the data. Must pass `--force` to re-pull evidence
  after a retag. And the flag is `--word`, not `--strongs`.
- **Psa 24:7 — NOT a tag bug, no fix.** ABP numbers Psalms the LXX way (our Psa 24 = LXX Psa 23), so the ref
  has no row in `verses`; the citation gate's `noverse` bucket logs it as "verse not in our text," never as a
  tag fault. The bucket worked as designed — closed without a change.

---

## No-verse lint (dangling "1Ti—" refs in the citation gate) — DONE 2026-06-29 (commit c41bcd8)
`_REF_RE` only matched a complete `Book ch:vs`, so a book token with no chapter:verse after it ("1Ti—") was
invisible — not even logged as a miss. `dangling_book_refs()` in build_lexica_def.py strips the complete refs
first, then flags any leftover NUMBERED-book name that's a real `verses.book` code; folded onto the gate's
`audit` as an advisory `dangling` line (never a fail) + a `show_entry` print. Three deliberate scope calls:
numbered-only (a bare "Gen" matches "For"/"God" and legit "throughout Genesis"), advisory not blocking, and
lexica-build only (ai.py's own `_VERSE_REF_RE` left alone — port later if wanted). Distinct from the
RECOVERABLE sibling gap (spaced "2 Chr 26:11", commit 632e54a) — a dangling ref has no verse to bind, so it
can only be flagged. Fires on future builds/`--resplit`; a free `--resplit --apply --all` would sweep the 18
live cards.

---

## ἵνα / Isaiah-6 hardening argument graph — BUILT + PUBLISHED + card wired — DONE 2026-06-29
The graph the ἵνα structural card points out to: does Mark's ἵνα at the hardening verses mark PURPOSE or
RESULT? `scripts/add_study_graph_hina_hardening.py` → study.db `hina_hardening` (published; graphs are public
now). Shared claim pool + three readings (purpose / result / "the fork predates ἵνα"). Forward pointer wired:
the G2443 entry in `structural.py` carries a `contest_graph` field (graph id + Mark 4:12 / Matt 13:13 / John
12:40), rendered by `StructuralBody` (Full entry) as a breadcrumb to Study › Graphs — shows on every ἵνα card
but NAMES the loaded verses so a mundane purpose-ἵνα is never painted as contested. Reverse direction (verse →
graph chip) rides the existing public for-verse index, no wiring.
- **THE FINDING (computed, not seated):** all three readings come out **DEPENDS-on-contested** — the graph
  MAPS the contest, it does not resolve it. Nobody wins; the seam is mapped.
- **The lesson worth keeping — EDGE-SEATING (caught by JP's Claude-chat reviewer, held three rounds).** First
  build rated the "predates ἵνα" thesis STANDS on two SOLID edges (the Hebrew→LXX form shift; three evangelists
  framing one citation three ways). Both underlying FACTS are both-camps-grant — but the INFERENCE from those
  facts to "ἵνα transmits, doesn't create" is exactly what the purpose camp denies. Rating the edges solid
  relocated the contest from a labeled node into two edge-strength labels and forced a false STANDS — the
  sophisticated form of seating. Fix B: drop both edges to contested → thesis computes DEPENDS like the others.
  RULE: "the fact is shared" is NOT "the inference from the fact is shared." Check 5 (verdict computed, not
  authored) can fail in the EDGE, not just the node.
- **Deliberate omission:** the Aramaic Targum substratum (Jeremias) layer — out of corpus, contested, wouldn't
  change any verdict. Slots in later as one more contested supporting edge if wanted.
- Full record: memory `project_study_modules` + `project_structural_deictic_cards`.

## Ask-corpus lexical-texture panel — WIRED LIVE + verified — DONE 2026-06-29
The computed distribution/family panel (proven on read-only protos earlier the same day) is now in the
live Ask-corpus path. Engine = **`corpus_panel.py`** (repo root, pure logic, the two protos merged);
`panel` field on the `/api/ai-search` payload; `CorpusPanel` drawn ABOVE the Synthesis tag in
52-ask-corpus.jsx. Counts are fact (no model call) — it's structure over the note, not generated prose.
- **The forks (decided WITH JP via his Claude-chat reviewer):** INLINE in the search (not a separate
  async endpoint — the DB work is indexed + fast; built after the answer behind a deadline + dropped on
  any miss, so it can't slow/break the paid answer); reader sees the **confident family + a one-line "N
  set aside"** count (hidden at 0); **compact strip + expand**, bars scaled WITHIN each language.
- **Degradation was the real work, not plumbing:** no clean head / empty / a head that doesn't occur /
  heb.db missing all resolve to "show less" (no panel/no group), never a crash or a fabricated row. Short
  Hebrew roots (≤2 consonants) gloss-anchor instead of flooding. `_CACHE_CODE_VER` 38→39.
- **Follow-on same day (commit 027e595):** widened the Greek stem proposer to see leading-prefix
  compounds (`prosabbaton` = pro+sabbaton — a real Sabbath time-word the strict prefix match missed);
  **only the proposer widened, the gloss gate untouched**, so false friends still drop. Then made panel
  rows clickable (→ Word study) and **removed the lemma chips** below the note (panel covers them);
  de-duped the repeated language header on multi-head queries.
- **LIVE-VERIFIED** (JP): fire rich, sabbath flat, sheol's Hebrew + short-root held, headless query → no
  panel. Behavior locked by `tests/test_corpus_panel.py` (in CI + the pre-commit hook). Commits 9504583 +
  027e595. Two follow-ups still open (LXX seam, bdb lemma_plain rebuild) — see TODO.md. Full record +
  discipline: memory `project_corpus_enrichment`.

## Rare-word stress test + dictionary cutoff + split3 splitter — DONE 2026-06-29
The deploy gate before building the verse-grounded dictionary (`lexica_def`) out by frequency:
does the engine stay HONEST when starved, or manufacture senses to fill the template?
- **Result: GREEN.** 18 rare words (occ 1/2/3/5, proper nouns + already-built excluded) × 3 draws.
  Zero manufacturing — no senses-over-occurrences, no ungrounded senses, no citation real-misses;
  the engine self-flags thin coverage honestly; the two controls split right (βαθμός 2 senses on
  2 occurrences, θεά homograph); the doctrinal-freight tempter προγινώσκω stayed neutral (didn't
  pick election). Trust settled. Full record + the detector set: memory `project_lexica_dictionary`.
- **Cutoff = occ ≥ 2** — a VALUE line, not a safety line: the engine is honest even at occ=1, but a
  1-occurrence word comes back single-sense + thin (≈ the LSJ gloss already), so grounding only earns
  its keep at 2+. Survey: 4,809 content words; 855 at occ=1 → **occ ≥ 2 = ~3,954 to build**, 855
  hapaxes stay on LSJ. PARKED — not batch-built till JP calls it.
- **Splitter fixed: split2 → split3 (bold-OR-plain sense headers).** The build splitter recognized a
  sense header only when BOLD (`**N.**`); a plain-numbered draw (`1.`/`2.`, common on rare words) gave
  an empty glance and `validate_entry` REFUSED the word. `split_definition` + `sense_provenance` now
  route through `_sense_spans` — bold parsed exactly as before (early-return on any bold match, so
  existing cards are byte-identical), plain accepted as a fallback. Prompt frozen, so the 18 live cards
  re-split FREE (`--resplit --apply --all`); verified zero drift first (`verify_resplit_glances.py`).
- **False-alarm "bleed" — NOT real (don't re-chase).** A dikaioō line reported in Χριστός's gloss_notes
  after the re-split was a STALE BROWSER CARD: db + live API both verified clean, scan found 0
  numbered-lines-outside-senses across all 18, "vindicate" lives only in dikaioō. The split3 matcher
  only reads the senses section and is inert on bold words, so it structurally can't write gloss_notes —
  proven before changing anything. Lesson: verify the data before "fixing" a splitter that isn't the cause.
- New PA-only read-only rigs (reuse the frozen engine, lexica_agreement pattern): `stress_rare_survey.py`,
  `stress_lexica_rare.py` (+`--resummarize`), `verify_resplit_glances.py`, `dump_lexica_entry.py`.
- Open follow-up (logged in TODO): point `lexica_agreement.per_sense` at `_sense_spans` before the batch
  build (it still keys bold-only — a plain draw would read as a phantom sense-count wobble).

## Numbered-book citation bug (Lexica engine) — FIXED 2026-06-28, commit 632e54a
Surfaced by the διάδοχος G1240 draws in the stress run above. The verse-ref parser wanted the numeral
GLUED to the book (`2Ch`); when a draw wrote it SPACED (`2 Chr 26:11`), the space orphaned the `2`, the
plain-book branch grabbed a bare `Chr` that matches no real book code, the citation gate logged no-verse,
and the sense read ungrounded — though the verse is real. NOT manufacturing.
- **Fix is parser-side, VERSE_PROMPT frozen.** The numbered branch now allows a separator + uncapped
  letters; `_norm_book` maps the label back to the stored code (all 8 numbered families, built against the
  real `SELECT DISTINCT book` list) by RE-ATTACHING the numeral already in the text — it never guesses
  1-vs-2. `cited_refs` + `sense_provenance` + `audit_lxx_provenance` routed through it; `trial_lexica_def`
  patched for parity; `stress_lexica_rare` needed no change (it rides `cited_refs`).
- **A verse-list disambiguation resolver was designed, then REJECTED** (the dump's catch) — the numeral is
  in the source, so recover-don't-infer is strictly safer, no homograph risk. Lesson worth keeping.
- **Verified read-only on PA** (`confirm_numbered_ref_fix.py`): the two διάδοχος refs → 2Ch/1Ch, 2/2 pass;
  nothing that already resolved moved book or testament; no shipped card affected (the spaced refs lived
  only in the stress dumps, never in `lexica_def`).
- **Audit blind spot it closes:** pre-fix, the short `1 Ch 18:17` form VANISHED rather than logging as a
  miss, so the stress run's gate numbers under-counted on numbered books — the engine was slightly MORE
  honest than the harness could measure. Doesn't move the occ≥2 cutoff; an audit re-run for build-out now
  counts them. Full record: memory `project_lexica_dictionary`.
- **Open sibling gap (still in TODO):** a ref with no chapter:verse (the charis `1Ti—`) is still invisible
  to the gate — a separate lint.

## Small doc/UI cleanup pass — DONE 2026-06-28
A batch of small finishes, all committed + pushed to master:
- **Cockpit Play/Pause icons → thin outlines** (`static/src/10-icons.jsx`, commit 3cc3c45). Were filled
  media glyphs (solid triangle + bars); re-stroked to thin outlines to match the design mockup + the
  outline `Icon.Modes`. Closes the last open item under "Mobile reading cockpit redesign". Memory
  `project_reader_appearance`.
- **Dead ABP "bracket column" CSS — confirmed ALREADY gone.** Grepped `static/styles.css`: only
  `.lib-bracket-group` (the keeper, `display:contents`) remains; `.lib-bracket`/`-unit`/`-glyph`/`-trail`
  were removed in an earlier pass. The code-health TODO item was stale → retired (no code change).
- **Stray "MM" scrubbed from `structural.py`** (commit 3c062ed). A bare "MM" in a comment listing
  provenance kinds (LEXICA/LSJ/MM) made the Claude-chat reviewer think Moulton-Milligan was loaded — it
  never was, no MM table/data anywhere. Comment-only change.
- **`snapshot_endpoints.py` default base → `https://www.lexica.bible`** (commit e10c1c6). The old
  `appssanding720.pythonanywhere.com` base 404s now the site's on the custom domain; `--base` still
  overrides. The stale John 3:16 golden was re-baselined (user ran `--update`, commit b686073) — closes
  the lone snapshot-harness leftover.
- **STATE.md added** (repo root, commit 577695e). A flat ground-truth LIVE/PARKED/NOT BUILT snapshot
  (stack, reference works, definition engine, structural cards, graphs, entity resolution, open work)
  for the external Claude-chat reviewer. POINT-IN-TIME, not a living doc — refresh when state changes,
  don't trust as live. Memory `feedback_claude_chat_collab`.

## Navigation-state audit — DONE + LIVE 2026-06-29
The reader's side panels and the gold "you are here" marker drifted out of sync with the text.
One root cause behind several "different" bugs: the reader's real position lives in the reader
(`selBook`/`selChapter`), but the side-panel cards + the marker live in the app shell — browsing
INSIDE the reader (book list, chapter chip, page turn, chrono step) moved the reader without telling
the shell, and the shell's nav object leaked stale fields forward. Symptoms, all confirmed broken on
live then fixed + re-verified desktop AND mobile: cross-ref/word panel stuck on the old book after a
book click; gold highlight bleeding onto a coincidental verse in the next chapter; flip
chrono→canonical dropped the current book; switch text then turn the page snapped back to the old
text. Fix: ONE reconcile point — the reader reports every move (`onReaderPos`), the shell keeps
whatever matches the new spot and drops the rest (`handleReaderPos`). Plus: clean nav object on page
turn (no stale spread), keep the book on chrono→canonical, SummaryPanel remount key, News empty-state
waits for its data. Repro 4 ("word-study jump wrong verse") was the highlight bleed, gone with the
reconcile — the jump itself never actually failed. Lesson: don't let a browse handler change the
reader position without going through the reconcile, and never spread the old nav bag into a new nav.
Commit bc47330. Full record: memory `project_nav_reconcile`.

## Firefox cold-load / app.js caching — DONE + LIVE 2026-06-29
News (and the whole app) "popped in ~1s late" in Firefox, fine in Chrome. Cause: PythonAnywhere's
static server sends the 543KB app.js with no cache instruction, so Firefox re-downloaded it every
load (~0.6s measured); Chrome guessed it could cache and was fine. PA's `/static/` mapping has no
knob for cache headers. Fix: serve the bundle from a Flask route (`/assets/app.js`) with a year-long
immutable cache; the `?v=<mtime>` cache-bust keeps it deploy-safe; gzip preserved (verified on live).
A residual ~1s on a genuinely cold Firefox load (the News tab's two small data fetches) was left
as-is per the user — not worth more time. Commit 6808b32. Full record: memory
`project_static_cache_header`.

## Proper-noun / entity resolution rebuild — BUILT + LIVE 2026-06-28 (Issue 2)
Click a proper noun and the card now describes the RIGHT person/place for THAT verse, not a
same-named one (the "Cushi → Acts", "Eden → wrong place" bug). The old cards looked up the entity
by NAME alone (which can't tell three Cushis or four Edens apart); now every occurrence is bound to
a specific entity from the TIPNR proper-noun database, and the card shows that entity's own sourced
description. 14,817 clicks bind correctly; the rest fall back to the safe summary — **zero
confident-wrong** (a wrong-but-confident card is weighted a loss, so we accept a lower match rate to
kill it). Built in the design brief's order: a shared engine (`entity_resolution.py`), a documented
versification map, name normalization (gentilic + KJV/LXX spellings, hyphen compounds), the binder,
the Cushi 6-slot number fix, the hand-check of the leftovers, and the card. Tables `pn_binding` /
`tipnr_entities` / `tipnr_entity_refs` (PA-only, rebuilt by `build_entity_binding.py --apply`); served
by `/api/metav/entity`. Re-run the build + the Cushi fix after any words rebuild.
Lessons worth keeping: TIPNR uses DIFFERENT columns for places vs persons (reading them the same put a
maps-URL under "Children"); a React state must be declared before the effect that depends on it (a
use-before-declare white-screened the app and neither the build nor the tests catch it — needs a
browser); the map staying hidden on an ambiguous place (Eden) is the guard working, not a bug. Full
record + numbers + the design brief: memory `project_entity_resolution_rebuild` + `entity_resolution_rebuild.md`.

**Bound-card display polish — 2026-06-28 (follow-on; pushed, deploy pending).** Three fixes after the build,
caught by review of the LIVE card: (1) "Appears N×" is a working LINK to the word's occurrence list again
(it had become plain text); (2) the card no longer paints the PREVIOUS word's identity for a beat before the
bind lands — the rail panel was REUSED across clicks and cleared its referent state in an effect that runs
after the first paint, so it showed e.g. Adam's person card under the "Eden" header, then swapped to the
Mesopotamia place. Fix = remount the panel per word (`key={activeEntry.id}` on both DetailPanel instances in
90-app.jsx); settled cards are byte-identical so unbound words are unchanged. (3) A fixed caveat under the BDB
block when a bound card shows ("dictionary entry for the word, all its meanings, not only this place/person" —
static, no referent-detection). Plus a general FRAME-0 rule: BDB + LSJ flashed "Not found" for one frame
before their own lookup ran — start their loading flag true at mount so the first frame is "Loading…". KEY
LESSON: verify a transient UI bug in the LOADING frames, not just the settled DOM (a `MutationObserver` that
records each distinct frame catches the stale paint). Commits 17d8d73 / 900c945 / f3ddfb9. Memory `project_entity_resolution_rebuild`.

**Bound-card occurrences — DONE + LIVE 2026-06-28 (the "Appears N×" follow-up, resolved a different way).**
The open question was: the count was the entity's (Eden 13) but the link opened the word's full list (every
Eden). Resolved by making the bound card show the REAL word-occurrence controls every other word has —
ABP + Hebrew OT + KJV + BSB, keyed to the entity's own number, each showing the actual word in every verse —
instead of an entity-only verse-pointer list. The card was a one-off: the Hebrew occurrence counts + sections
were gated off for any proper noun; now a bound entity un-gates them (off `boundEntity` + `isHebrewWord`).
The ABP count needed a new `/api/strongs-count/<n>?by=base` (a backfilled PN's bare `strongs` is '*', so it's
only countable on `strongs_base`). KEY FINDING (don't re-investigate): there is NO viable "pure Greek" option
for OT names — TIPNR's Greek form (Eden = εδεμ) is a STEPBible-extended number (G9827) our lexicon lacks and
ABP never uses; ABP individuates the name (Gen 2:8 = παράδεισος G3857 "garden" + a separate "Eden" word) and
those Greek occurrences already surface via the Hebrew base. A TIPNR ref-list ("Where this place appears", a
new `/api/metav/entity-refs` endpoint + inline verse list) was BUILT then REMOVED in the same arc — it listed
pointers, some without the word, so the real occurrence controls supersede it (endpoint + helper deleted).
Commits 3d4ab60 / f4dfecf / f81a295 / 359220b (deploy pending). Memory `project_entity_resolution_rebuild`.

## εἰμί ("to be") subject merge — FIXED + LIVE 2026-06-28 (PN-subject fold, Issue 4)
Last of the 2026-06-28 issue batch. A proper-noun subject of the copula was glued onto the εἰμί (G1510)
verb's cell with the subject's own Greek word floated as a trailing empty `*` — same defect as the big
PN-subject fold but MISSED because the subject isn't in the tipnr name roster. Expected ~47 from the
source, but the live still-merged count was only **2**: Sarai (Gen 11:30 "Sarai was"), Crete (Zep 2:6
"Crete shall be") — the corpus-wide fold had already swept the named-roster rest. FIX (commit c4a11ae):
`fix_pn_subject_merge.py` extended with `_peel_eimi` (single leading word → name, rest → verb) and a
gate that fires on G1510 + capitalized non-roster lead + adjacent empty `*`, minus sentence-initial
function leads (`_FUNCTION_LEAD`, moved into the fix as the one source of truth; the audit imports it).
Conservative: unbracketed slot-after shape only. The third εἰμί+empty-`*` cell, 2Ki 10:15 "It is.", is
correctly skipped (function lead). Applied on PA → import_tipnr → surface → translit; dry-run 0, audit
0, health_check 0/0. Folds into the build via the same `run()`; 3 new tests (1 positive + 2 negatives).
Restore note: this came right after closing out the bible.db scare/restore — that replay was re-verified
clean first (PN-subject + italic-heads both 0, health_check 0/0). Memory `project_pn_subject_verb_fold`.

---

## Word-study search over-match + slow — FIXED + LIVE 2026-06-26 (+ 2 match-list UI fixes)
Typing a short Greek word (ἵνα) returned ~17 junk hits (γάγγραινα, εἶναι, Σινᾶ…) and was slow:
`lexicon_lookup()` matched a substring LIKE on the accent-stripped lemma — a leading-wildcard scan,
no index, no ranking, so it over-matched anything CONTAINING the letters and buried the exact word.
FIX (535150d): an indexed `lemma_plain` column (accent-stripped/lowercased/final-sigma-folded) on
`lexicon` + `bdb` (`scripts/add_lemma_plain.py`, folded into `load_lexicon.py`); the lookup matches
EXACT `lemma_plain = ?` first and short-circuits — the substring scan now runs only as a "contains"
fallback when the typed word isn't a headword. LIVE on PA (lexicon 5,523 + bdb 8,674 rows); ἵνα → ἵνα,
Hebrew רוח → H7304–H7308, both instant. Deploy-safe (`_has_lemma_plain` guard). **LESSON: never leave
a search on a leading-wildcard `LIKE '%x%'` — store a normalized, indexed key and match it exactly.**
Two follow-on Word-study match-list UI fixes the same session (63ccedf, 6d33ada): the Greek/Hebrew
match list now COLLAPSES into a header when you pick a word (was vanishing — it was gated on
`!profile`; now uses the same `.glsenses` card as the English results via `renderMatches`), and each
match row shows the per-source "used as" renderings (ABP/HEB/KJV/BSB + totals) instead of one
dictionary gloss — new `_render_glosses_all()` in views_lexicon.py, a standalone twin of
`lexicon_english`'s builders (kept separate so that path can't regress; enriches multi-result lists
only). Full record: memory `project_lexicon_search_overmatch`.

## Proper-noun SUBJECT folded onto its verb — DONE + LIVE 2026-06-26
Corpus-wide: where ABP put a subject NAME right after its verb, the build crammed the name onto the
verb's cell and left the name's own Greek word (a bare `G*` slot) blank/untagged, so "David took" read
as G2983 (took) and the name wasn't clickable. ~2,300 real cases (the 634 with no adjacent `*` slot —
false alarms + "David said"-type verbs with NO `G*`, where ABP merely supplied the subject — were
correctly LEFT ALONE). FIXED by `scripts/fix_pn_subject_merge.py`: the name goes on the LOWER of the
two adjacent slots and the verb on the higher, so BOTH reading modes show "David took" name-first
(matching the ABP source) with NO bracket added — chip mode only reorders inside brackets, so a bracket
would NOT have fixed chip order (the earlier "#2 = bracket-reorder" theory was WRONG; corrected against
the render code). Applied on PA (~2,278 flat + 19 bracketed), import_tipnr resolved the new name slots,
surface/translit rebuilt; build-folded so a rebuild reproduces it. `scripts/fix_tamar_subject.py` was
the wrong (insert) approach and was DELETED. Full record: memory `project_pn_subject_verb_fold`.

## ἵνα structural card + the STRUCTURAL-WORD CONTEST RULE — DONE 2026-06-26

ἵνα G2443 shipped as a PURE structural card (commit d7518b1) — purpose finding, exemplar Mark 3:14 (a plain
uncontested purpose, NOT the hardening verses). The long-held-out question — is ἵνα a structural card, or does
purpose-vs-result need a fork? — is RESOLVED: the result/ekbatic debate is a GRAMMATICAL (not doctrinal)
question, flagged ON the card (glance/full via the contested-flag), NOT a fork. Additive: G2443 was already
falling through, so no routing/frontend change.

The verdict worth keeping — **STRUCTURAL-WORD CONTEST RULE:** a structural word whose grammar is settled but
whose APPLICATION is doctrinally contested at specific verses does NOT get a fairness-gate fork. Fairness forks
are for CONTENT words whose senses are contested between reading-communities (dikaioō: forensic/infused/
covenant). A structural word's senses aren't the contested thing — what's contested is WHICH settled sense
applies in a given verse (a passage-level question, not a lexical one). So the card stays grammatically honest
and the loaded verses point OUT to an argument graph: the lexeme is innocent, the passage is contested. Forking
it would teach a falsehood about the grammar to "solve" a problem the word doesn't own.

STILL OPEN (moved to TODO.md): the Isaiah-6 hardening argument-graph — ἵνα's verse-pointer target — isn't built;
its evidence is the Hebrew-imperative → LXX passive + μήποτε → Synoptic ἵνα/ὅτι translation chain. Full record:
memory `project_structural_deictic_cards`.

## Word-study search LABEL — pick the slot's OWN word, not an added (italic) one — DONE 2026-06-25

From a user report: the Word-study "favor" search listed λαμβάνω/G2983 (a take/receive word). Root —
`words.english_head` (the one English word the finder matches a word by) was the LAST real word of the
gloss (`parse_abp._head_word`). When ABP appends a translator-ADDED (italic) word it became the label:
Lev 19:15 "take favor" (favor italic) labeled λαμβάνω "favor". ~6,720 multi-word glosses carried an
added word as their head; the finder drops function words but λαμβάνω is a content word, so it slipped.

FIX (commit 025e6a8): `_head_word(text, italic_words)` now skips italic (added) words too, falling back
to the plain pick only when EVERY content word is added (bare article slots unchanged — no regression).
Carried into the build as a final pass `_strip_italic_heads` so a rebuild reproduces it (no re-run
needed — UNLIKE the other fix_*.py). Live data repaired by `scripts/fix_italic_heads.py` (`--apply`;
`--strongs G####`/`--all` to review; touches english_head ONLY; re-runnable, a 2nd run reports 0).
**4,409 labels corrected**; the other ~2,300 correctly fell back. Lambano's 22 all land on the verb;
broad sample overwhelmingly right (dry land→dry, seven times→seven, procreated, behold, unleavened).
Proved the rule on the 30-row sample locally before touching PA; invariant tests 22/22. Full record:
memory `project_english_head_label`.

LEFT ON PURPOSE (not regressions — all follow ABP's own italic marking): verb + a NON-italic tail
particle ("went forth"→forth, "went down"→down) still labels on the tail (the tail isn't an added word,
so italic-skip can't catch it — needs a part-of-speech rule); and a few where ABP marked the NOUN as
the added word, so the label lands on a modifier ("round about place"→round G4066, "young man"→young
G3495). Spot-fixable via `--strongs`. Open follow-up kept in TODO.md.

---

## Two reader bug-fixes — dotted-cognate Lexica routing + Bible-switch-after-search — DONE 2026-06-25

Both frontend-only, found while reviewing the ekklēsia word card. Pushed (`87d1555`, `77c538e`); deploy is a
normal pull. Detail: memory `project_lexica_dictionary` (dotted) + the commit messages.

- **A dotted cognate borrowed its base word's Lexica definition.** The card fetched `/api/lexica/<strongs_base>`,
  and `strongs_base` drops ABP's dotted ".N", so G1577.1 ἐκκλησιάζω (verb) + G1577.2 ἐκκλησιαστής (agent noun)
  both showed ekklēsia's (G1577) noun senses under their own correct headword. FIX: fetch by the FULL number
  (`entry.strongs_raw`, keeps the dot) in `30-detail-panel.jsx` → a dotted word 404s and falls through to its own
  abp_ext/LSJ entry. STANDING RULE: the Lexica / word-card fetch must use the full dotted number, never
  `strongs_base` — `dotted_lexicon` has 3619 words that would mis-route at full-dictionary scale. The six built
  entries were never wrong in CONTENT (`abp_filter` excludes dotted from a base's evidence); pure display routing.

- **Couldn't switch Bibles after clicking an in-text search result.** `jumpToResult` baked the current
  `translation` into the persistent `nav`. Because a search jump ALSO sets a `highlight`, the switch-version
  re-scroll effect (`useEffect [translation]`) re-emitted that nav on every version click, and the nav effect's
  `if (nav.translation) setTranslation(nav.translation)` re-applied the stale version — snapping you back. FIX
  (`60-library.jsx:743`): drop `translation` from the search-result nav (you're searching the text you're already
  in, so it never needs to force a version). Switching works again AND still re-scrolls to the found verse.
  LESSON: don't put `translation` in a `nav` that also carries a `highlight` — line 404 re-applies it every time
  that nav re-fires.

---

## Donations live via Ko-fi + GitHub Sponsors ruled out — DONE 2026-06-24

First working donate path since Stripe closed his account (which had killed Ko-fi). Full record: memory
`project_payments_donations`.

- **In-app donate button.** Beside the `hello@lexica.bible` contact button on the welcome-tour final card + the
  About page (`static/src/70-search.jsx`). Started as `♥ Support via PayPal` → paypal.me/LexicaBible (dfa5c71),
  then SWAPPED to `☕ Support on Ko-fi` → ko-fi.com/lexica (6e3b9fa) — Ko-fi gives a real donation page
  (one-off/monthly/tiers) vs PayPal.me's bare send-money box. `.donate-btn.kofi` brand-coral CSS.
- **Account-menu Support link (2bf08d5).** A quiet "Support on Ko-fi" row in the AccountModal, shown ONLY to
  role `user` (hidden from berean+admin — don't nag people who already pay/run it). Needed the client to know
  the role: `/api/auth/me` already returned it but the store dropped it — now `refreshAccount()` captures `role`
  into auth state + `authInfo()` exposes it (display-only; real gates stay server-side).
- **Cap CTA → Ko-fi (2bf08d5).** The Ask-corpus "out of searches" nudge now points to Ko-fi to become a Berean
  (was the `bereans@` email). The CLAIM step (which account to upgrade — a Ko-fi payment can't tell the app who
  they are) moves to the Ko-fi membership welcome message → email `bereans@` → admin grants the role.
- **GitHub repo Sponsor button (dec076f → a8a5d58).** `.github/FUNDING.yml` = `ko_fi: lexica` (dropped the
  PayPal.me `custom` line so it's Ko-fi-only). Needs repo Settings → Features → "Sponsorships" ticked to show.
- **Accuracy fix (8edb463).** First cap CTA said "unlimited searches" — WRONG; berean is 10/day
  (`AI_DAILY_LIMITS`). User caught it. Reworded to number-agnostic "more searches a day" so the copy can't drift
  from the cap. Don't write "unlimited".

**Lessons / don't-redo:**
- **GitHub Sponsors is a DEAD END for him — don't re-pitch it.** It dropped PayPal Feb 2023 and pays out ONLY
  via Stripe Connect (or a fiscal host like Open Source Collective). He's Stripe-banned, so the program is
  blocked; the FUNDING.yml button is the workaround (no Stripe, no enrollment).
- **Ko-fi takes 0% on tips/donations** (free plan, forever) — only PayPal's ~3% + $0.30 processing. The 5% Ko-fi
  cut is ONLY for memberships/shop/monthly; Ko-fi Gold ($12/mo) waives that.
- Ko-fi is PayPal-backed for him (he set PayPal as its processor), so money lands in his PayPal;
  paypal.me/LexicaBible still works under the hood.

Commits: dfa5c71, dec076f, 6e3b9fa, a8a5d58, 2bf08d5, 8edb463.

## Full code audit after the 2026-06-23 change run — DONE (commits 6eaec4e, 1f36bbd)

Read-only audit of the search-perf + mobile-UX + cap/email work, then the agreed cleanups. The one
finding that MATTERED was infra, not code:

- **The heb.db speed index wasn't live on PA.** The perf commit (572b754) added two by-Strong's indexes.
  The bible.db one (`bsb_strongs`) auto-creates on every reload (app.py `_migrate_db`), but the heb.db one
  (`idx_heb_words_strongs`) does NOT — a deploy never re-runs `load_hebrew.py` and startup never opens
  heb.db. So the Hebrew half of the "fix the slowdown" commit was silently not applied. User created it by
  hand on PA (`CREATE INDEX IF NOT EXISTS idx_heb_words_strongs ON heb_words(strongs)`) and confirmed the
  Word-study "spirit" search is right again. Recorded as a standing GOTCHA in memory `project_ci_automation`:
  heb.db indexes are ALWAYS manual on PA.

Cleanups shipped:
- **Removed the dead `/api/search` Search tab** (6eaec4e): the route + its two KJV helpers in views_search.py,
  the unused `api.search` frontend helper, the two `/api/search` probes in snapshot_endpoints.py + their two
  stale snapshot gold files, and the dead `.donate-btn.kofi/.github` CSS from the donate→contact swap. Kept
  `/api/text-search` (the live Library search) — verified byte-identical. views_search.py now hosts only it.
- **Finder heb.db churn (1f36bbd):** `lexicon_english` opened heb.db ~4-6 times per search; now ONE shared
  lazy handle (pure-Greek searches still never touch it), plus the catch-all 500 the other lexicon routes
  have, plus a note on the books/verses Hebrew corpus default. Each query's logic unchanged.

DELIBERATELY NOT DONE: collapsing the `_totals_hebdb` per-H-number loop into one grouped read (it was on the
audit's lead list). A homograph form (H1254a) must count under BOTH its base and the form to match the word's
own page (commit 45282f8) — a single `GROUP BY strongs` can't express that, and the fold can't be verified
locally (heb.db is PA-only). Left the loop, just moved it onto the shared connection. Don't re-attempt.
LESSON: the index already made each per-number read cheap, so the loop was never the cost — the repeated
OPENS were. Full record: memory `project_hebrew_source_swap`.

---

## Search-speed fix + mobile UX + cap/contact-email pass — DONE + PUSHED (2026-06-23, commits 572b754…ede0633)

A run of small shipped changes (all pushed to master; user deploys):
- **"All searches slow" = MISSING INDEXES (root-caused, 572b754).** The recent Hebrew-source swap + BSB-as-
  a-word-study-source started looking words up BY STRONG'S NUMBER in two tables with no index on that column,
  so every lookup full-scanned: heb.db `heb_words.strongs` and bible.db `bsb_strongs.strongs_id`. The Word-study
  English finder runs several per search (one a per-H-number loop), so it stacked many full scans. FIX: added
  `idx_heb_words_strongs` (load_hebrew.py) + `idx_bsb_strongs_id` (load_bsb_words.py + the app.py startup
  self-heal beside the kjv ones). Confirmed missing live via `PRAGMA index_list`, created by hand on PA for an
  instant fix. LESSON (same one app.py already learned for kjv): a new by-Strong's table needs a strongs index.
  Full record: memory `project_hebrew_source_swap`.
- **Mobile word study:** inline search bar + "Searching…" on the empty screen; English multi-result list
  auto-collapses on pick (desktop + mobile). (b6ab11d)
- **Mobile Ask the corpus:** a "New search" button so a fresh thread is reachable (was buried in the history
  rail). (f3c99a2)
- **Greek/Hebrew match list (mobile):** one flex line that shrinks to fit — fixed right-edge overflow + the
  dead space under short rows (the desktop fixed-column grid was wider than a phone). (ede0633)
- **Chrono mobile cockpit:** shows the short "Gen 1–3" abbrev label, not the full passage name. (5ca22f4)
- **Daily cap user tier 5→3** (views_notes.py `AI_DAILY_LIMITS`); at the cap a "Berean membership" nudge links
  `bereans@lexica.bible`, replacing the dead "support the site" donate text. (6321534, b0f8668, 2b92662)
- **Donate buttons → contact email:** the processor-dead Ko-fi / GitHub Sponsors buttons were removed from the
  welcome-tour final step + About; replaced with `mailto:hello@lexica.bible` and copy reframed "Support
  Lexica"→"Get in touch". (6b969ef) Inbound mail (hello@ + bereans@) now forwards to Proton via **Cloudflare
  Email Routing** (send-only Resend can't receive). Full records: memories `project_email_smtp`,
  `project_payments_donations`, `project_ai_spend_caps`, `project_ai_search_redesign`, `project_chronological_tab`.

---

## Reader word card — metaV name false-positives on common OT words — FIXED + LIVE (2026-06-23, 54aafab)

A common Hebrew word BSB/KJV capitalizes mid-verse (midbar "Wilderness of Sinai", H4057) tripped the reader's
metaV NAME lookup and popped a bogus place/person card; the same capital-letter guess (`kjvIsPN`) also wrongly
HID gentilic clans BDB tags "Adjective" (Philistines, Moabites).
- FIX: gate the lookup on whether the Strong's is actually a NAME — `core._HEB_NAME_STRONGS`, a startup set of
  bare H-numbers that are proper nouns or gentilics, built from heb.db's OWN morphology by DOMINANT use
  (`app._build_heb_name_cache`, mirrors the Greek `_FUNCTION_STRONGS` cache). KJV/BSB chapter endpoints send
  `heb_name` per Hebrew word; `30-detail-panel.jsx` gates `kjvIsPN` on `entry.hebName`. Greek/NT words + a
  missing heb.db carry no flag → fall back to the capital-letter rule (deploy-safe). No hardcoded word lists.
- TRIED FIRST + REVERTED: a `bdb.part_of_speech` "Proper" check. Dead end — 409 H-numbers have a BLANK tag
  (incl. Egypt H4714), and gentilics are tagged "Adjective", so it both leaked (So/No) and hid clans.
- Verified on heb.db: Joshua/Egypt/Philistines dominant-name; midbar + the particles al(H5921)/asher(H834)/
  et(H853)/al-not(H408) zero-name (the "So"/"No" leakers). Also strip the bare wiki URL from metaV place
  comments (`cleanPlaceComment`). Full record: memory `project_metav_expansion`.
- LESSON (process): three slips this session — linkified the wiki URL instead of just stripping it (not asked),
  guessed a table name (`metav_places_aliases`; it's `metav_place_aliases`) → query errored, and dumped a
  ~1000-row query he had to scroll. Memory `feedback_confirm_ask_before_big_changes` (2026-06-23).

## Word-card lemma gloss: KJV/BSB/Hebrew + Word study wired + Hebrew byform fix — ALL LIVE (2026-06-23)

Finished what the entry below started — `word_gloss` now feeds EVERY word card, not just ABP.
- KJV/BSB chapter endpoints join it via the new `core.word_gloss_join()` (deploy-safe; folds a Hebrew
  byform suffix in SQL). The Hebrew reader (separate `heb.db`, can't join bible.db) looks it up cross-db,
  byform folded. Frontend threads `entry.lemmaGloss` into the 3 entry builders.
- The card shows the plain meaning UP TOP for every word with a gloss that isn't a name/place
  (`showLemmaGloss` in 30-detail-panel.jsx). Words with an "in this verse" form line drop the contextual
  English onto it; no-form words (KJV, ~44% of ABP) let the meaning replace the in-verse word up top
  (user's call). Word study tab Greek "definition" + cognate/lookup glosses lead with `word_gloss` too.

HEBREW BYFORM WRONG-LEADS (the real find): TBESH splits some H-numbers into a/b senses; the build kept the
alphabetical-first, so midbar (H4057) read "mouth" (1x homonym) not "wilderness" (271x).
- First fix matched the heb.db byform LETTER -> FAILED: heb.db byform tagging is MIXED (some plain `H####`,
  some `H####a`), so nothing matched and it fell back to "mouth". Caught by the dry-run still showing "mouth"
  (the BSB card only LOOKED right because that word ALSO mis-matched a metaV place, which shows the verse's
  own word -> see the open follow-up in TODO.md).
- WORKING fix (9dfb25d): match the TBESH sense against heb.db's own GLOSS TEXT instead. `--byform-audit`
  measures the rest by confidence (coverage = share of heb.db uses the picked sense covers; <0.5 = review).
  A Claude-chat review of the audit gave 25 hand overrides (14 confident + 11 leans); residual ~294
  low-coverage words are synonym-noise (correct, not errors). H2742 + 5 coin-tosses left as-is.
- LESSON: don't assume a sister dataset (TBESH vs heb.db/TAHOT) tags byforms the same way — verify with a
  live query before building on it (cost two attempts). Re-run `--byform-audit` after any rebuild.

Commits: 577beb0 (wiring) -> 236f7a5 (no-form words show it too) -> 9dfb25d (gloss-text fix) ->
2ce4255/287f63b (audit + confidence) -> ee77fb1/f2b85a2 (25 overrides). Full record: memory
`project_word_card_gloss`. Open follow-up moved to TODO.md: metaV place/person false-positives.

---

## Word-card lemma gloss: source chosen + built — Greek + Hebrew, ABP live (2026-06-23)

The card's lemma gloss used to come from `lexicon.kjv_def` (KJV-ized + alphabetical, so it led with
"charity"/"Ghost"). Replaced with a new `word_gloss` side table: Greek = Dodson's plain ranges + TBESG fill
for LXX-extended numbers + a few plain-meaning overrides; Hebrew = TBESH + overrides; ABP dotted words
glossed by their OWN lemma (TBESG-lemma index, then ABP's own dictionary, then numbers/particles by hand).
17505 rows, no blanks on the words people study. ABP card wired (`core.word_gloss_cols`, deploy-safe) and
live-verified. **KJV/BSB/Hebrew card wiring is the one piece left — it's back in TODO.md** (the frontend
un-gate touches the locked card, so it was held for a fresh pass). Memory: `project_word_card_gloss`.
- Lessons (also in the feedback memories): the source was picked by a PLAIN-MEANING quality pass on the
  LOADED words, NOT by coverage — TBESG's one-word gloss is loaded (grace/hell/propitiation), Dodson's
  ranges win but still lead loaded on χάρις → hand-override. ABP tags grace as **G5484 (charin), never
  G5485** — the override had to target the number ABP actually uses. Dotted scholarly-prose hapax are left
  blank (they show the LSJ section) rather than risk a wrong auto-pulled gloss.

---

## Ask-corpus tuning — functionality + cleanup (2026-06-23)

Commits 1822ffa, fd4eb7c, 4b06414, e1f1713 (pushed, awaiting deploy). Visual polish deferred to Claude
design. Full record: memory `project_ai_search_redesign`.
- **Synthesis prose cleanup (ai.py, both prompts).** The old "you MUST mention EVERY key_strongs term"
  rule FORCED the answer to ramble about a mis-injected word, then call it "incidental" (the "giant
  hunter" → geras case). Relaxed to "discuss only the words that bear on the question; OMIT an unrelated
  one — don't name it to dismiss it." Added: no empty "()", cite verses BY REFERENCE (never quote the full
  verse text). Prompt edits self-refresh the `search:` cache (no salt bump).
- **Prose verse references all clickable (52-ask-corpus.jsx `AcProse`).** Was: a verse the AI named that
  the search didn't retrieve fell through to plain text (looked "typed out / not clickable"). Now every
  recognized ref is a chip that jumps to the reader; a non-retrieved one renders quiet/dotted (`.ac-ref-soft`)
  so it doesn't imply evidence.
- **Evidence list = ONE flat verse list (50-corpus-results.jsx).** Dropped the per-chapter book·chapter
  headings + collapsible boxes (user: "you can only collapse one at a time"). `CorpusGroup` deleted;
  `CorpusResults` flattens into primary / additional `.vlist`s of `VerseRow` — same look as the Word-study
  occurrence list. `.corpus-group*` CSS now dead (left for the design pass). `VerseRow` untouched.
- **Saved conversations sync cross-device (was localStorage-only).** New `corpus` table in notes.db +
  `POST /api/corpus/sync` (views_notes.py, a near-copy of /api/notes/sync — id key, newer-wins, tombstones;
  caps 60 convos / 250 KB each). Client: a corpus section in `NotesStore` (`corpusConvos`/`upsertConvo`/
  `clearConvos`/`syncCorpusNow`), riding the same account plumbing (synced alongside notes/plan). Logged-out
  still works browser-local. Table auto-creates on first sync (deploy = a normal pull).
- **Mobile "Recent" button (52-ask-corpus.jsx).** ROOT BUG: `setRailOpen(true)` was never called → the
  history rail was unreachable on mobile. Added `.ac-mobi-hist`.
- **Cache key normalized for caps/punctuation (ai.py `_cache_key`).** "Is hell the same as Sheol?" and
  "is hell the same as sheol" now reuse one cached answer instead of each paying for a fresh search. Only
  the key is normalized (lowercase, punctuation→space, collapse spaces); the model still gets the original
  wording. Search-path only.
- **Off-topic key-word chips — TRACED + mitigated.** A temp `AISEARCH-DIAG` log (commit 05be72d, since
  removed) printed model-picked vs cognate-added per search; live result: the cognate EXPANDER is clean
  (only tight, real relatives). The stray chips (doorkeeper/burning under "giant hunter → Greek equivalent")
  are the MODEL over-reaching in `key_strongs` on a vague question — non-deterministic (a re-run was clean).
  My earlier γίγας→γηράσκω "collision" theory was wrong for this case. Fixed (e1f1713) by tightening the
  `key_strongs` instruction to the word + direct equivalents only ("when in doubt leave it out") — reduces,
  not 100%. A frontend chip relevance-gate was OFFERED + DECLINED (over-build for a rare cosmetic thing).
  LESSON: instrument the deterministic code before assuming it's the culprit — it was the model, not the
  expander.

## BSB in Ask-corpus + Hebrew left-to-right "prose" (2026-06-22, "round 2 for BSB")

Frontend-only follow-on (commits e367753, 40147cc, fd27b57; pushed, awaiting deploy). Memories
`project_hebrew_source_swap` + `project_hebrew_ot_interlinear`.
- **BSB added to the Ask-corpus answer's verse-text toggle (e367753).** Was ABP·KJV·HEB → now
  ABP·BSB·KJV·HEB. The shared `VerseRow` (50-corpus-results.jsx) + `api.bsbVerseWords` already rendered
  BSB (Word study used them), so it was just the missing button + a small `.ac-tm` gap trim so four fit on
  a phone. `static/src/52-ask-corpus.jsx`.
- **HEB scoped to OT verses + default always ABP (e367753 then 40147cc).** HEB used to gray on "no Hebrew
  word cited" and auto-show for a pure-Hebrew answer. Now: HEB grays unless the answer has OT verses
  (`hasOtVerse` = any result whose book isn't in `NT_BOOKS`), and HEB mode shows ONLY those OT verses — so a
  mixed Greek+Hebrew answer no longer renders blank rows (heb.db is OT-only). The auto-show-HEB behavior was
  REMOVED (40147cc) — the user never asked for it; every answer now defaults to ABP and the reader flips
  manually. (The auto-HEB predated this work; I carried it forward by mistake, then pulled it.)
- **Hebrew "Prose" in the reader = the chips flipped LEFT-TO-RIGHT (fd27b57).** CLOSES the parked "Hebrew
  OT prose mode — pick the flavor" idea. The Prose button (was grayed for Hebrew) toggles `viewMode` + a
  `.lib-heb-ltr` class that sets the row/content `direction:ltr`; only the WORD order flips L→R, each
  `.lib-iw-heb` keeps `direction:rtl` so the letters stay correct. A true L→R read of the LETTERS is
  impossible/backwards (what the prior session meant by "impossible") — flipping word ORDER sidesteps it.
  Strong's/Interlinear still work. Wired in 60-library.jsx (lib-bar + render) + 59b-library-nav.jsx (mobile
  ModesSheet). Flag `hebProse = hebMode && viewMode==="prose"`. Matches the Ask-corpus Hebrew layout.

## Ask-corpus + Hebrew word-study fixes — BSB phrase net, HEB click, brackets, aligned interlinear (2026-06-22)

Follow-on session after the Hebrew source swap + KJV demote (below). All pushed, awaiting the user's
deploy. Memories `project_ai_search_architecture` + `project_hebrew_source_swap`.
- **BSB in the AI phrase search (136865d).** The phrase supplement (re-runs the model's own multi-word
  phrases against the readable verse text, to catch contiguous phrases the per-word gloss can't) scanned
  ABP + KJV; added a third scan over `bsb_verses` (deploy-safe guard for a missing table) so a phrase
  worded the modern way is caught. RECALL ONLY — a BSB hit maps back to its ABP verse and displays as ABP
  words; the synth still reads/quotes ABP. `_CACHE_CODE_VER` 37→38. Backend-only.
- **Ask-corpus H-number click → HEB, not KJV (6d030b2).** The synth's lemma chips + Strong's links
  hard-coded "kjv" for H-numbers — a leftover from before the source swap. Pointed them at "heb"
  (loadProfile still falls back to KJV for the byforms heb.db lacks). `static/src/52-ask-corpus.jsx`.
- **TAHOT supplied-word brackets in "Hebrew renders as" (966a6c3 + e38124a).** STEP TAHOT wraps SUPPLIED
  English words (added for sense, KJV-italics style) in `[ ]`. `_normalize_gloss` only stripped brackets
  off a gloss's outer ends, so a bracket glued to an inner word survived ("[men of]" → broken "[men").
  FIRST fix stripped all brackets — which EXPOSED a second bug: the last-word head-picker then chose the
  SUPPLIED word ("mighty [one]" → "one" in Psa 45:3). FINAL: drop the whole `[..]` span and keep the real
  word ("mighty [one]" → "mighty"); fall back to the de-bracketed gloss only when no content word remains
  ("[men]" → "men", "the [mighty]" → "mighty"). `views_lexicon.py _normalize_gloss`. LESSON: a fix can
  expose the next layer — the user caught the "one" before deploy.
- **Aligned Hebrew occurrence interlinear (66ae84d).** The HEB display drew two opposite-direction lines —
  Hebrew R→L over a gloss line L→R — so the same word sat top-right / bottom-left and nothing aligned.
  Rebuilt as per-word columns: each Hebrew word stacked over its gloss, laid L→R (letters stay RTL via
  dir + unicode-bidi:isolate; only the word ORDER flips). BibleHub style. heb.db has only word glosses
  (no smooth prose) so columns are the right shape. `static/src/50-corpus-results.jsx` (VerseRow heb
  branch) + `.corpus-heb-int`/`.chi-*` CSS.
- **Comment reword (99ebd5b).** Dropped "ABP's wooden English" from the BSB-scan comment — the user
  corrected me for over-characterizing ABP (the app's anchor) off one example (a Hebrew gloss line, not
  even ABP). Memory `feedback_dont_disparage_abp`.

DEAD END reconfirmed: Hebrew PROSE for the occurrence list can't exist — heb.db has only word-by-word
glosses, no smooth translation. (The library-reader Hebrew-prose idea — a separate surface, transliteration
L→R or Hebrew R→L — stays parked in TODO.md.)

## Demote visible KJV in the reader + BSB as the TSK xref fallback (2026-06-22)

Follow-on to the Hebrew source swap below. KJV's old heavy lifting is covered now (heb.db = Hebrew
evidence, BSB = free modern English), so the VISIBLE KJV was demoted — it stays a reference/compare
everywhere else (word-study ABP·HEB·KJV·BSB toggle + compare untouched). Commits 7cf8524 (demote +
xref fallback) + 849e28c (xref picker reads BSB). Full record: memories `project_hebrew_source_swap`
+ `project_ai_synthesis_quality` (which-text-for-which-AI-job).
- **Reader source row** (static/src/59b-library-nav.jsx): desktop ABP·KJV·BSB·More → **ABP·BSB·HEB·More**;
  KJV moved into the "More ▾" popout beside ESV/NIV; HEB grays on NT (OT-only). Deploy-safe via
  `kjvInMore = hebShown` — if heb.db is absent the third slot falls back to KJV and KJV leaves "More".
  Mobile flat picker sinks KJV to the END of the row (user confirmed) via a `renderPick` helper.
- **TSK xref fallback → BSB** (views_crossref.py + 40-crossref-panel.jsx): new `_bsb_text` reads
  `bsb_verses` (deploy-safe, swallows a missing table); displayed verse field renamed `kjv_text`→`text`
  (BSB-or-KJV); synthesis ref_block + source line prefer ABP→BSB→KJV; the Step-1 Haiku candidate picker
  now reads BSB too (KJV fallback) — clearer than "thou/thee" for judging links. `_XREF_VER` salt bumped to
  `bsb-fallback-4` so cached payloads refresh (else stale rows serve the old `kjv_text` key → blank refs).
- **HARD DECISION HELD:** the cross_references/TSK KJV verse-id skeleton is UNCHANGED — heb.db is OT-only so
  it can't back whole-Bible OT↔NT cross-refs, and the skeleton is invisible + free; only the displayed/fed
  fallback TEXT moved to BSB.
- LESSON: when a cached AI payload's SHAPE or message TEXT changes (not the prompt), bump the manual salt —
  the fingerprint covers prompts only, so a renamed field would otherwise serve stale rows with the wrong
  key. The `snapshot_endpoints.py` golden for the non-curated xref route goes stale (re-baseline with
  `--update` on PA after deploy) but it's not in pytest/CI.

---

## Hebrew word source: KJV bridge → real Hebrew OT (heb.db) (2026-06-22)

Switched the OT Hebrew OCCURRENCE source from the KJV's reverse-engineered Strong's tagging
(BDB → kjv_strongs → kjv_words) to the real Hebrew OT (heb.db → heb_words, STEP TAHOT) everywhere a
Hebrew word's evidence is shown. One session, commits aa159eb…13184c9. KJV-as-a-TEXT left untouched.
Full record + the open Phase-2 items: memory `project_hebrew_source_swap`. Highlights:
- **Verified FIRST** with a read-only PA script (`scripts/compare_heb_source.py`): heb.db vs the bridge —
  verse counts match ~99.8%, versification ALIGNS (heb.db is English versification, no Psalm-superscription
  offset), and 150 H-numbers the KJV uses aren't in heb.db (mostly Strong's BYFORMS TAHOT files under the
  parent, e.g. H3212 → H1980) → those fall back to KJV. LESSON: a data-source swap earns its trust from a
  read-only count/versification compare before any code change.
- **Surfaces switched:** Word study (`views_lexicon.py` — new `heb` corpus + `has_heb`/`heb_glosses`),
  Ask-corpus (`ai.py` — code-side heb.db occurrence supplement, mirrors the cognate/phrase ones,
  `_CACHE_CODE_VER`→37), SEO /word (`views_seo.py`), reader rail (`30-detail-panel.jsx` + new
  `/api/hebrew/strongs-count`). Cross-DB merging is all CODE-SIDE — heb.db is never attached to the AI's SQL.
- **BSB added as a 4th word-study source** in the same pass (toggles ABP·HEB·KJV·BSB; finder shows all four
  "renders as" lines + a HEB/BSB filter) — the user wanted to compare how every Strong's-tagged Bible renders
  a number.
- **Found DEAD:** the old standalone Search tab — `api.search` has no caller, `/api/search` orphaned (left in
  `views_search.py`, harmless). NOT switched. Live search = `/api/text-search` + Word study + Ask-corpus.
- LESSON: heb.db `strongs` is H-prefixed/zero-stripped ("H7307"); match `strongs = ? OR strongs GLOB ?`
  (sid+"[A-Za-z]"). Result rows MUST carry an H-prefixed strongs_base or the AI citation guard + gold
  highlight silently miss.

---

## AI-search cost meter + broken-pipe root cause (2026-06-22)

Started from a SIGPIPE / "broken pipe" log line on an AI search the user flagged.
- **The broken pipe was NOT just a client disconnect.** The timing log showed that search's DB step
  (`sqlrun`) took **235s** (normally <1s) — the browser gave up during the ~4-minute hang, then the server
  finished and the write found a closed pipe. One-off (every other search ~1s — likely momentary PA
  $10-tier DB contention), not a code bug. LESSON: a broken pipe can be a *symptom* of a server-side stall —
  check `sqlrun` before blaming the client.
- **SLOW-SQL guard** (commit 04d824f): `ai.py` warns when the DB step exceeds 10s, with elapsed + rows + the
  SQL inline → a recurrence is one grep (`SLOW SQL` in `/var/log/www.lexica.bible.*.log`), not eyeballing.
- **Cost meter** (commit 023d57f): a `cache[haiku-sqlgen]` / `cache[sonnet-pass2]` token-split `log.info`
  after each model call (fresh / write / read). Confirmed LIVE — the Haiku SQL prompt **caches** (write=6151,
  over Haiku's 4096 floor; the "borderline at 4k" worry was unfounded); Sonnet pass-2 does **not** and can't
  (its system prompt ~1,800 tok is under Sonnet's 2,048 floor + the verse payload varies). So **no free
  caching win — don't chase it.** One "Ask the corpus" search ≈ **3¢** (Sonnet pass-2 ~75%); a repeat of the
  same question is free (served from the saved row). The only cost levers (trim verses / move pass-2 off
  Sonnet) are tiny or reverse the 2026-06-21 neutrality fix — left alone. Both log lines KEPT as a permanent
  meter (user's call). Full record: memory `project_ai_search_architecture`.
- **Surfaced, still OPEN (in TODO.md #2 "AI curation hard-tune"):** the Ask-corpus answer-shape cleanup —
  save/reopen whole conversations (the history click re-runs a question as a follow-up today = the cache-miss
  bug), kill the inline "see all 156" verse dump (route to Word study), recheck verse curation. PLANNED, not done.

## Three reader fixes + dotted [ABP] widening (2026-06-21)

A batch of bugs the user spotted in one session:
- **Dotted [ABP] different-words promoted** (commits 130d7e7, fe3bd48; `--summary` e6d2b87; probe 6b7d9a3).
  `build_dotted_lexicon.py` skipped EVERY `[ABP]`-prefixed abp_ext entry as a form-note, so ~570 genuinely
  different words ABP parks at a dotted number (G4521.2 σαβέκ "thicket" vs base σάββατον; χερούβ "cherub",
  εφούδ "ephod", αρσενικός "male" …) wrongly showed the base word on the card. New skip = `base=="G1510" OR
  "Strong G####" in the text`. TWO false starts: skip-by-`[ABP]`-prefix (too greedy, buried σαβέκ) and
  skip-by-"Strong G####"-alone (missed the future-tense εἰμί forms έσται/εισίν which list only verses). dotted_lexicon
  3049→3619 rows. Re-run with the db PATH as a positional (that was missed first run). Full record + recipe:
  memory `project_dotted_strongs_lemma`.
- **Result-list italic highlight** (commit 664eb1f). The "gold hugs `english_head` only" fix had covered only
  the plain multi-word branch; the two italic branches still painted the whole slot, so a supplied italic "the"
  lit up. Unified into one `tight && hc` block. Memory `project_ai_search_redesign`.
- **Trailing ABP dash + em-dash** (commit b78aefb + `scripts/fix_emdash.py`). ABP's clause dash `--` glued to a
  bracket's last word rendered INSIDE the `]`; the trail-lift now recognizes dashes (reader + detail panel) and
  lifts them outside with a leading space. `fix_emdash.py` then swapped every `--`→`—` in words.english +
  verses.text (double-hyphen only). Memory `project_library_bracket`.
- STILL OPEN (handed to its own session): the Word study tab folds dotted-different-words into the base number —
  see TODO.md #4.
- NOTE: a model-side safety-check outage blocked git pushes for part of this session, so a couple of PA data
  steps were run directly (sqlite `REPLACE(...,char(8212))`) instead of via the not-yet-pushed script.

---

## ABP blank "G." Strong's numbers — FILLED (commit df5c624, 2026-06-20)

ABP's own source left EXACTLY 5 words with a numberless "G." (a 'G' with no digits — the Strong's
number was never assigned). The build splits verses on real Strong's markers, so a numberless "G."
wasn't recognized and that word's English glued onto the next real number ("bidding" landed on the
article G3588 in Act 24:8; "AndG. you," collapsed καί onto σύ in Zec 9:11). Filled each with the right
number and split the merged slot: Zec 9:11 & 1Pe 3:13 "And"→G2532, Heb 7:4 "And view"→G2334,
Mat 12:14 "And the"→G3588, Act 24:8 "bidding"→G2753.
- Live patch: `scripts/fill_blank_strongs.py --apply`, then re-ran `build_abp_surface` + `build_abp_translit`
  (the 4 splits shift word slots). Build fold: `apply_blank_strongs_fills` runs at the end of the words
  build, so a rebuild reproduces it — don't re-run the one-time script. `scan_strongs_leak.py` stays as a guard.
- LESSON: the root was ABP's OWN blank number, NOT our scraper — BibleHub-live renders these clean.
  Confirmed against the eSword ABP source files (`abp_texts/`) before touching anything. An earlier
  "peel the G. text" approach was the WRONG fix and was reverted (these needed their NUMBER filled, not
  the text stripped). Full record: memory `project_blank_strongs_fill`.

---

## Word-study dead-CSS sweep — DONE (commit 103f81c, 2026-06-19)

The word-card fold orphaned a pile of `.wd-*` rules (`.wd-hero/.wd-sub/.wd-tr/.wd-gloss/.wd-morph/.wd-greek/
.wd-strongs/.wd-head/.wd-head-r/.wd-overview/.wd-sec*/.wd-badge/.wd-askai*`) plus `.lexicon-toolbar`/
`.lexicon-corpus-toggle`/`.lct-btn` — all removed (CSS-only, 33 lines). KEPT (still live, grep-confirmed):
`.wd`/`.wd.hidden`/`.wd-scrim` (panel shell), `.wm-card`, the `.wd .detail-*` overrides, and
`.wm-searchsheet` (the orphan list had it wrong — still used by the mobile Search sheet). Re-confirmed clean
2026-06-20 (`.lct-btn`/`.wd-hero`/`.lexicon-toolbar` = 0 matches). NOTE: 2026-06-20b briefly re-added then
removed a `.wd-askai` footer button + removed `.lsj-toggle` (toggle deleted) — no new dead CSS left. Full
record: memory `project_ai_search_redesign`.

## Argument graphs replace Denominations/Arguments — DONE 2026-06-18

The flat two-sided **Argument** editor and the **Denomination** (support/tension) editor were REPLACED by
one new `graph` study kind: a shared pool of provenance-tagged CLAIMS joined by per-tradition LINKS
(strength-tagged), stress-tested by `argmap.py` and drawn as a left→right SVG chart per tradition (shared
verses pinned across the overlay flip). Nothing was authored in the old two types (user confirmed), so they
were removed outright, not migrated. Read-only in-app; authored via `scripts/add_study_graph.py` (ships the
Baptism graph — 3 traditions). Engine guarded by `tests/test_argmap.py` (CI + the pre-commit hook). Study tab
now stays mounted (`display:none`) so it keeps its place across tab switches. Chart colors are FIXED
theme-safe vars (`--chart-*`: navy verse / slate conclusion / navy contested), not `--accent`/`--ink` (twin
browns in sepia + flip in dark). Verdict strings are COMPUTED from graph structure, never hand-set.
- DEFERRED ("cut 2"): in-app graph editor, React Flow drag canvas, undercut scoring in the stress test, an
  "In studies" verse back-reference for graphs.
- LESSON (the build's real value): the chart kept catching fairness bugs the flat list hid — a cross-axis
  feed (an efficacy argument routed into a recipient conclusion), an argument-from-silence rated unevenly vs
  its mirror, a missing strongest plank, a thesis set stricter than the tradition actually holds. Two checks
  did most of the work: is every node grounded in what it claims, and is each side's STRONGEST version on the
  board. Built/reviewed alongside Claude chat via screenshots — method in memory `feedback_claude_chat_collab`.
- REFINED the same day (fairness pass, all live): split credo's conclusion by axis (who vs efficacy);
  Acts 16:33 → weak with Lydia/Stephanas as the clean-silence household anchors; gave credo its covenant
  plank (Jer 31/Heb 8); made regeneration's thesis the EFFECTS claim ("Baptism saves") with "grace is an
  infused substance" surfaced as a required premise (not buried in a label), and 1 Pet 3:21 / Mark 16:16
  rated weak for self-qualifying. Chart polish: foreignObject node labels (wrap, no spill), tighter spacing,
  a distinct dotted "weak" line style. The five checks behind all this are now the `argument-graph-review`
  skill (auto-triggers on graph work).
Full record: memory `project_study_modules`.

## Word-study def + cross-ref synthesis: text-first cleanup — DONE 2026-06-17

Three small fixes, all live (pushed; deployed and confirmed by the user):
- **Cross-ref synthesis reads the cross-refs in ABP, not KJV** (commit f105b05). The "Related passages"
  write-up was quoting verses in KJV ("thou gavest", "thou hast hearkened" on Gen 3:6) because Torrey's TSK
  is stored against KJV verses and only the SOURCE verse was fed in ABP. Now each curated ref is rebuilt
  from ABP (`_abp_text` in views_crossref.py — interlinear english joined in order, the same text the panel
  shows), KJV only as a versification-miss fallback. **LESSON:** the AI-cache fingerprint (`_XREF_VER`)
  covers the PROMPTS only — changing what TEXT you feed (the user message) does NOT change the hash, so
  cached rows keep serving the old output. Bump a manual salt (`"msg:abp-refs-1"`) when the message
  construction changes. Memory `project_ai_synthesis_quality`.
- **LSJ Strong's-fallback def leads with the KJV rendering** (commit 769d269). A word with no LSJ entry
  (2 Peter 2:4 ταρταρόω G5020) showed ONLY `lexicon.strongs_def` — Strong's paraphrase "to incarcerate in
  eternal torment", imported doctrine the text-first rule rejects. Now: `kjv_def` ("cast down to hell") →
  `derivation` → `strongs_def` (last resort). Affects every LSJ-gap word. Memory `project_lsj_lookup`.
  Follow-up (TODO #5) — DONE 2026-06-17 (commit f2c270f): the Lexicon match dropdown + word profile now
  use the same `kjv_def → derivation → strongs_def` order. The Search RESULT rows render no def text (word
  clicks re-fetch LSJ, already text-first), so nothing to change there. Same commit deleted the dead
  `/api/cross-references/synthesis/` route — the frontend only calls `/curated/`, which already curates
  (Haiku) + writes the synthesis (Sonnet, in ABP); shared prompt + fingerprint kept, so no cache churn.
- **Hero headword auto-shrinks to fit** (commit 503df96). Long names (Nebuchadnezzar) overflowed the word
  card at the fixed 56/46px; a measure-and-scale `useLayoutEffect` (`heroRef`, 30-detail-panel.jsx) now
  shrinks an over-long headword to one line (22px floor, re-fits on word/layout/resize/font-load). Memory
  `project_detail_panel_interlinear`. Don't re-pin `.detail-greek`'s font-size.

Also captured this session (not built): the "let published study TOPICS shape AI search answers" idea,
with the hardcoded divine-council corpus in ai.py as the one-off it would replace — kept as an open item
in TODO.md ("Let study results shape AI search answers").

LINE-ENDING note (same recurring gotcha): the editor flipped views_crossref.py LF→CRLF on a multi-line
edit (a ~600-line phantom diff), caught from the commit's +/- count and fixed before pushing; views_lsj.py
and 30-detail-panel.jsx edited the same session stayed LF. Confirmed 30-detail-panel.jsx is all-LF (the
docs had wrongly listed it CRLF — corrected). Full lore: memory `project_frontend_build_step`.

---

## ABP dotted Strong's headword + word-card formatting — DONE 2026-06-17

The word-study card showed the WRONG Greek headword for ABP's dotted Strong's numbers — e.g. Gen 1:2
"unready" = G180.2 ἀκατασκεύαστος ("unformed") was displayed as G180 ἀκατάπαυστος ("unceasing"). Cause:
the build makes `strongs_base` by chopping the ".N" (`sbase = st.split(".")[0]`), and the card resolves
the headword via the lexicon join on `strongs_base`, so it lands on the alphabetical-neighbour base
number (ABP parks its own added words at "nearest Strong's + a dot"). ~3049 numbers / 15,786 word-spots.
- **Fix:** `scripts/build_dotted_lexicon.py` builds a `dotted_lexicon` side table (full `G###.N` → correct
  lemma + romanization, pulled from each one's OWN abp_ext entry); `chapter_text`/`verse_words` COALESCE it
  over the base join (deploy-safe — joined only if the table exists); `build_abp_surface.py` made
  dotted-aware so a corrected word stops echoing on the "in this verse" line. Read-only audit:
  `scripts/audit_dotted_lemmas.py` (`--show G####` dumps a raw abp_ext entry).
- **Lessons:** (1) the first "3643 wrong" count was mostly FALSE — εἰμί-style forms (1510.x) are inflected
  forms of the SAME base lemma and correct as-is. Real different-word cases are told apart by the abp_ext
  entry shape: `[ABP] <form> … Strong G####` = a form note → leave the base; a full LSJ entry (no `[ABP]`) =
  a genuinely different word → fix. (2) `words.lemma` (LXX-aligned) is a DEAD END as the fix source — blank
  for ~all of these; the correct lemma is the first Greek word of the dotted number's own abp_ext entry
  (Greek stored as HTML entities inside `<grk>` tags → unescape + strip tags). (3) Verify the Greek
  extraction on real data before trusting a count — a too-narrow Greek code range read empty and reported
  "0 wrong."
- **Re-run after any words rebuild:** `build_dotted_lexicon.py --apply` → `build_abp_surface.py --bh` →
  `build_abp_translit.py`. Full record: memory `project_dotted_strongs_lemma`.
- **Card formatting (same session):** the hero now reads lemma → romanization · gloss → a labeled,
  evenly-spaced "in this verse" block (form, romanization stacked under it, parsing), split into two grouped
  boxes (`.detail-hero-id` / `.detail-hero-occ`); parsing-only cards (indeclinables) sit tight via
  `.detail-hero-occ--tight`. 30-detail-panel.jsx + styles.css. (An "in this verse" label had been removed
  back on 2026-06-15; it's back now and kept.)
- **Other surfaces (2026-06-17):** the SEO `/read` pages, the AI verse-word context (`ai._fetch_verse_words`),
  and ABP Search now get the same correction via a shared `core.dotted_lexicon_cols()` helper (per-word, so no
  grouping is affected; deploy-safe). Only the **Lexicon tab** is left open (TODO.md) — it groups + clicks
  through by the base number, so it needs a bigger change, not a display swap.

## Outbound email — Resend SMTP, password reset + nightly health-check — DONE 2026-06-16

Parked since 2026-06-09 "until a custom domain" so the sender setup got done ONCE properly
(authenticated `@lexica.bible`, not a throwaway Gmail). lexica.bible landed, so it got built.
Full record + the test-error decoder: memory `project_email_smtp`.
- **Sender:** Resend (SMTP relay `smtp.resend.com:587`, user `resend`, pass = a Resend API key,
  From `noreply@lexica.bible`). DNS (MX + SPF + DKIM + DMARC) added in Cloudflare, DNS-only. New
  module `mailer.py` (no Flask dep, no-op until configured — deploy-safe like the Google button).
- **Password reset + set-password:** `request-reset` (always ok, no account-existence leak) /
  `reset` (single-use, 1h, clears every session then signs in) / `set-password` (Google-only
  accounts add a password). `password_resets` table in notes.db; the emailed link opens the SPA at
  `/?reset=<token>`. Frontend: forgot/reset modes in the auth box + a Password box in the Account panel.
- **Nightly health-check email:** `health_check.py` got `--email/--only-warn/--email-to`; a daily PA
  scheduled task (23:53 UTC) mails only on a real failure.
- **Lessons:** (1) the web app reads keys from the WSGI but a cron has NO WSGI env, so the task's
  copy of the mail keys lives in a gitignored `~/bible-db/.env` — keys exist in BOTH places on purpose.
  (2) Test errors: **535** = bad SMTP username/key (user must be the literal `resend`); **550 "domain
  not verified"** = key is fine, just wait for Resend's DNS check (or fix a Cloudflare doubled-domain
  name typo). Cloudflare publishes instantly; Resend re-checks on its own slow timer.

## Study tab — public go-live + study↔reader links + speedup — DONE 2026-06-16

The Study tab (admin-only since 2026-06-12) opened to the public, plus a batch of linking/perf/UX work.
Full record: memory `project_study_modules`.
- **Go-live:** published TOPICS + the metaV NAME-topics are now readable by anyone, no login;
  denominations/arguments, drafts, and all editing/writes stay admin-only; private `notes` stripped for
  readers. Backend split the old all-admin `_guard` into write-only; reads branch on `is_admin`. Name-topics
  imported as drafts, so `publish_topics.py` got a `--names` flag (the plain script only flipped concept topics).
- **Two-way links:** study verse references are clickable (jump into the reader); tapping a verse number shows
  an "In studies:" line in the xref panel (`/api/study/for-verse`, a cached verse→topics index that includes
  **hand-authored studies only** — excludes `source='metav'` so the giant Nave's imports, e.g. Psalms=1008
  verses, don't blanket the reader).
- **Speedup:** opening a topic was ~5 reads PER verse (9–13s on big topics, nothing cached). Now one batched
  pass (`_resolve_map`) + an in-process cache → ~1–2s.
- **Verse-add box fix + `add_study_topic.py` loader** (load a hand-authored topic via dry-run/--apply; first
  use: Divine Council).

Lessons worth keeping:
- **Plain `git pull` does NOT reload the web app** — it bit us repeatedly this session (new routes 404'd,
  backend changes didn't take, the browser kept a cached `app.js`). Use `deploy.sh` (pull + reload) and
  hard-refresh; if a just-shipped change "isn't working," suspect a missed reload FIRST. (Now called out in
  memory `feedback-deploy-command`.)
- **A query param can be silently dropped before the app.** The editor's `GET /api/study/verse?ref=…`
  arrived with an EMPTY ref (400) for the admin — every POST-with-JSON call worked, only the GET-with-an-
  encoded-query (space+colon) lost its param (root cause never pinned — proxy/edge sanitization suspected;
  service worker ruled out). Fix: made it a POST body. If a GET query param ever vanishes again, switch to a
  body before chasing ghosts.
- **Keep the in-app editor even though the loader exists** — it's admin-only (invisible to readers) and is the
  only home for the `✦ Draft with AI` intro (uses the WSGI key, no shell key), quick edits, and denom/argument
  types. Loader = bulk drop-in; editor = touch-ups + intros.

## SEO / search discoverability — DONE 2026-06-16

The site was invisible to Google: the React app served an empty shell with no per-passage URLs, and
there were no icons/share data. Built the whole discoverability layer (memories `project_seo_pages` +
`project_seo_branding`):
- **Branding:** favicons (svg/ico/apple-touch/192/512) + a 1200×630 `og.png` share card, generated from
  one logo by `scripts/gen-icons.js`; meta/description/OG/Twitter tags; `robots.txt`. Icons/share live
  in `static/`; `app.py` serves the root paths crawlers fetch.
- **Crawlable pages (`views_seo.py` + `templates/seo/`):** `/read/...` chapter/book pages (ABP/KJV/BSB/
  Hebrew interlinear, brackets + red Greek-order numbers) + `/word/<strongs>` word-study pages +
  generated `/sitemap.xml` (~18-19k URLs). Public-domain texts ONLY. App deep-links in via `/?b=&c=&t=`
  and `/?lex=` (read on mount in 90-app.jsx). Phases 1a/1b/2/3 all shipped (commits 09eead5 → 00f7207).
- **Google Search Console:** Domain property `lexica.bible`, Cloudflare-verified, sitemap submitted
  (Domain props need the FULL sitemap URL). Discovered ~4,561 pages immediately.

Lessons worth keeping:
- **og:image must be a real PNG, not an SVG** — most link-preview scrapers won't render SVG.
- **Center a lockup by measure-then-crop, not hand-placed coordinates** — guessing text widths put the
  share card off-center twice; rendering the art, auto-cropping the ink, and compositing centered fixed it.
- **ABP brackets ≠ italics** — they're distinct ABP notation (a `bracket_id` group drawn `[ ]` in Greek
  order with position numbers), NOT the italic helper-word styling. Don't conflate them.
- **Interlinear chips must reserve all three rows** (lemma/english/strongs, invisible placeholder when a
  row is empty) or function words push their English up into the original-language line.
- **Can't test the SEO pages locally** (no bible.db on the dev box, must not create one) — verified by
  py_compile + standalone Jinja parse, then deploy-tested. Worked fine.

## SEO word-page polish + mobile toolbar centering — DONE 2026-06-16

Follow-ups after the SEO launch (same day):
- **Word pages (`/word/<strongs>`, commit dfcdd2b):** example passages now jump to the verse + highlight
  it (chapter page got `id="v<n>"` anchors + a tiny scroll/highlight script, soft gold `.verse-hi`,
  `scroll-margin-top:24vh` so it lands upper-third — kept crawlable rather than bouncing into the app,
  user's call). A HEBREW word's examples open the Hebrew OT interlinear (`/read/.../heb`, refs from
  heb.db so the verse truly has the word — was wrongly pointing at the Greek ABP). "Rendered as" chips:
  stripped stray punctuation + merged dups; left NON-clickable (filtering is the in-app Lexicon's job).
- **Mobile reading toolbar (commit 9e9a631):** the play button was hidden on no-audio texts, which
  unbalanced the row and shoved the centered book/chapter sideways. Now always rendered, grayed +
  disabled when there's no audio → row balanced, book/chapter centered. This OVERRODE the old
  "always hide dead audio" rule for the mobile toolbar only (memory `feedback_gray_dont_hide` updated;
  desktop bar / audio dock still hide).

## Docs slimmed — CLAUDE.md → standing rules + pointers — DONE 2026-06-16

Restructured the always-loaded docs so the rules that matter stand out instead of drowning in a
changelog. CLAUDE.md 908 → 599 lines:
- The ~90-line Words rebuild checklist moved to a slash command, `.claude/commands/rebuild-words.md`
  (`/rebuild-words`) — it only matters when actually rebuilding; CLAUDE.md keeps a 6-line pointer.
- Library Tab section (~294 lines of dated UI changelog, already mirrored in the project_* memories)
  condensed to ~100 lines of standing rules + memory pointers.
- Deployment + AI-cache sections trimmed to the operational facts (where secrets/tokens live, which
  db holds what, the gates, the cache scheme + LANDMINE); dated "done/live" setup history dropped (it
  was already in this archive + memory). Stale "BibleHub scrape — status" block retired.
- Commits 422ff46 / 07bf65b / 868709d, pushed.

Memory tidied the same way: the index (MEMORY.md) went 20.5 → 13.9 KB (long lines → one-line hooks;
fixed the stale "next up: sepia+dark / refactor #1" line); the 63 topic files left intact — they're
the detail CLAUDE.md now points at. New preference saved: memory `feedback_lean_claude_md` (keep
CLAUDE.md lean — heavy procedures → slash commands, done/live history → memory + TODO_ARCHIVE).

## Two-ending adjective gender (Masculine/Feminine) — FIXED, route a, LIVE 2026-06-16

Greek two-ending adjectives (ἀόρατος, ον) share ONE form for masculine and feminine; the OT (CATSS) and
NT (Robinson) morph sources often just DEFAULT such a word to Masculine, so the word-study card read the
wrong gender next to a feminine noun (Gen 1:2 "earth, unseen": γῆ feminine, ἀόρατος showed Masculine). NOT
a display bug — `decodeMorph` faithfully shows the single gender letter the source gave. FIXED via route
(a): for a two-ending adjective the source NEVER tags Feminine (so it has never shown it can tell them
apart), the card now shows **"Masculine/Feminine"**; words the source DOES resolve, plus all Feminine/Neuter
tags, are left alone (decided per testament). ~836 displays (OT 441 / NT 395). The two-ending signal = the
LSJ headword endings (three-ending lists a feminine ending then a neuter — ἀγαθός → ή, όν; two-ending lists
only the neuter — ἀγαθοποιός → όν). Generator `scripts/build_two_ending.py` → `static/src/00b-two-ending.jsx`
(`TWO_END_SOFT_OT/_NT` sets) + a tweak to `decodeMorph` in 00-core.jsx; commits fbd22cc + 2e874e2.
**Re-run the generator after any words rebuild** (genders/tallies shift) and rebuild app.js.

LESSONS: (1) measure-first paid off — the source turned out INCONSISTENT (resolves some two-ending words,
defaults others), which is exactly why the never-Feminine rule is right and a blanket "blur every masculine"
would be wrong (it'd also expose detector slips like εἷς, which the never-F rule auto-excludes). (2) Matching
our words to LSJ by lemma needs BOTH the hyphen (ἀδικ-ητικός) AND the final sigma ς folded, or ~96% miss —
cost two bad runs before the numbers were real.

DEFERRED — route (b): resolve to a REAL gender from the neighboring noun (match the same-verse noun by
case+number, which is reliably tagged; only gender is the unknown). Safe only when there's exactly one clear
match, else fall back to "Masculine/Feminine"; needs the neighboring words at display time (the card sees
only the clicked word now) or a precompute pass. Parked, not rejected. Memory `project_two_ending_gender`.

## ABP variant-reading (Bos/CP/Ald/Six) footnotes — INVESTIGATED + proof built + SCRAPPED 2026-06-16

ABP's own dagger apparatus ("CP reads X", "see Bos for variants"). The data IS in the free ABP 2nd-ed
PDF (archive.org `apostolic-bible`), but the PDF has **no verse anchors**: footnotes pool at each page
BOTTOM with their text only; the verse numbers + the daggers that tie a note to its word are in a custom
font that extracts as NOTHING. So a note pins only to its PAGE (~15-24 verses); the verse is INFERRED from
the English gloss (distinctive word = nailed, e.g. "dimness"→Gen 15:12; a common word over a wide span =
a guess). No digital module carries it either — BibleHub/studybible.info bare; the e-Sword/MySword ABP
modules (incl. the user's local SQLitePlus-encrypted `abp+.bblx`) are text-only, no `<RF>` footnotes
(verified by opening them). PDF English decodes via a fixed +29 letter-shift; each variant's Greek is a
SEPARATE garbled font, so only the English meaning is recoverable. A 5-note Isaiah proof shipped († on the
verse → folded into the TSK cross-ref card) then was fully REMOVED. **VERDICT (user): niche + lossy —
"bereans don't need this; it's nothing you can't find by digging into the Hebrew/Greek."** Path B (diff
the printed Greek editions vs ABP ourselves) also rejected (same hard alignment as Rahlfs; would be our
apparatus, not ABP's). KEPT from the session: verse#/Strong's# now scale with the reading font (CLAUDE.md).
DON'T re-pitch. Memory `project_pending_improvements`.

## ABP surface romanization (translit) — DONE + SHIPPED 2026-06-15

The ABP "in this verse" side-card form now carries a romanization (Hebrew/BSB already did) — the parked
follow-up from the inflected-form section below. `scripts/build_abp_translit.py` fills `abp_surface.translit`
(348,935 forms, read-only) with a Greek→Latin romanization matched to the lexicon's OWN SBL headword style
(confirmed by sampling `lexicon.translit` — theós / pneûma / archḗ / huiós): keeps accents, eta→ē / omega→ō,
ch/th/ph, **rough breathing → "h" read from the dictionary form** (the bh surface forms carry no breathing),
**initial rho → rh**, and upsilon y-vs-u (y standalone, u in a diphthong incl. υι). Tested on real words before
filling. NOT the throwaway ~40-line map the earlier note warned against — it handles the long tail (breathings,
iota subscript, diphthongs, gamma-nasal, final sigma) and matches the app's existing romanization, so it's safe
under the accuracy brand. Re-run after any position-shifting words/abp_surface rebuild (next to build_abp_surface).
LESSON kept: the empty-string-in-string trap — `'' in 'αεηο'` is True, so word-initial upsilon silently became
'u'; use SETS for membership. Commits d9adc7a (script) + 4e73577 (upsilon fix). Memory `project_bsb_words`.

## ABP morphology gap — INVESTIGATED + SCRAPPED 2026-06-15

Looked hard at filling the ~22% of ABP words with no morph (135,774). Verdict: not worth it; don't re-investigate.
Measured on PA, the gap breaks down: 32,473 proper names (ABP doesn't parse them — correct), ~32,922
indeclinable / no-surface-form words (καί / ἐν / the article etc. — nothing to parse, correctly blank), and only
~70,379 inflected content words that genuinely could be filled (~86% OT). The single ABP-keyed source for those
is Van der Pool's **Analytical Lexicon** — a paid $5 426-page PDF (an extraction project), whose parses also carry
real nominative/accusative + gender ambiguity with no clean tiebreak. For a side-panel detail aimed at non-Greek
readers, the juice isn't worth the squeeze. Also checked **STEPBible's ABGk/abpgrk** (Tyndale's adaptation): it's
the SAME ABP text, not an upgrade — single-dot accent + no breathing (like what we already have), no inline
morphology, under Van der Pool's "all rights reserved" copyright (NOT the CC-BY that covers STEPBible's own
TAGNT/TAGOT). The free CC-BY TAGOT is Rahlfs-based, so it can't reach ABP's Vaticanus-Sixtine-only OT words anyway.
Full record: memory `project_abp_morph_gap`.

## ABP inflected-form side-card line — DONE + LIVE 2026-06-15 (Hebrew + BSB + ABP; KJV impossible)

The click-a-word side card shows the printed in-context Greek/Hebrew form on a small line under the dictionary
lemma. Hebrew (heb_words pointed word) + BSB (bsb_words form/form_translit) were easy. ABP was the hard one
(3 of 4; KJV can't — English↔Strong's, no original word). The ABP trail, lessons worth keeping:
- ABP's own source is English+Strong's only — no Greek surface words. So the printed form is ALIGNED in by
  Strong's and stored in a SEPARATE read-only table `abp_surface(verse_id, position, form, translit)`
  (`scripts/build_abp_surface.py`, never touches words/verses; served by /api/chapter's deploy-safe LEFT JOIN).
- FIRST built off Rahlfs-1935 (OT) / TAGNT (NT) → capped at OT 75% / NT 84%. The user spotted WHY, and it's the
  lesson: **ABP's OT is the Vaticanus-Sixtine text family; Rahlfs is an eclectic edition. Where the two Greek OTs
  disagree the Strong's match fails — a STRUCTURAL cap, no Rahlfs-based source can close it against ABP.**
- FIX: ABP's OWN printed Greek, already on PA — `bh_scrape.db` `bh_words.greek` (the BibleHub ABP scrape). Same
  text as our words → 91% found. Builder `--bh` expands bh compound cells (`4160-3588-2316`/`εποίησεν ο θεός`)
  and bridges ABP's raw G1473 pronoun mis-tag to the live corrected numbers before aligning.
- bh's Greek is ACCENT-ONLY (no breathing marks): an accent-only inflection (dative `αρχή`) looks like the
  breathing-marked lemma (`ἀρχή`) → would echo a useless line on ~every word. `strip_marks` only keeps a form
  that differs from the lemma by ENDING → 56% of words show a line; the rest ABP prints = the dictionary word.
  Shown forms are breathing-less = ABP-authentic (user chose authentic over Rahlfs-polished, knowingly).
- The Rahlfs/TAGNT path stays in the builder as an alt source. Surface translit is now DONE (the section above,
  `build_abp_translit.py`); a full parsed-LXX 2nd parallel text stays a PARKED follow-up (in TODO.md). Re-run
  `build_abp_surface.py --bh` THEN `build_abp_translit.py` after any words rebuild that shifts positions. Full
  record: memory `project_bsb_words`. Commits f536c52 (Rahlfs first cut) → 0b5e5ae + 0b908b7 (bh).

---

## Front-end split — LibraryView render block out to 59c — DONE 2026-06-14

Closed TODO #3 ("split the oversized front-end file"). `static/src/60-library.jsx` had grown to 3,369
lines; split in two passes.
- PREAMBLE (earlier 2026-06-14): self-contained code before the `LibraryView` component →
  `59a-library-helpers.jsx` + `59b-library-nav.jsx`. Behavior-neutral — app.js unchanged except 3
  header comments (the moved code was top-level and used nothing from LibraryView).
- RENDER BLOCK (this session): the ~600-line verse-renderer family (renderVerse + its chip/bracket
  inner helpers, renderProseWords, KJV, BSB/plain, Hebrew, flow, Didache/non-canon) → a new
  `59c-library-render.jsx`, the `LibRender` IIFE module. Each renderer takes a `ctx` bundle of the 19
  live values it needs from LibraryView (book/chapter; note/highlight helpers hiClass / vnumEl /
  noteMarker / noteVnum / noteDotInline / vnumNoteHandlers; toggles wordMode / showInterlinear /
  showStrongs; onWordClick / handleVerseNum; refs highlightRef / vnumPressRef; selBook / nav / corpus /
  nonCanon / didVerses). LibraryView builds ctx once per render and binds 13 thin one-line wrappers, so
  every call site in the 540-line return reads UNCHANGED — the only new code is the ctx object + 13
  wrappers. 60-library.jsx: 3,369 → 1,918 lines. Commit 547c483, pushed; user spot-checked live
  (ABP chip+prose, KJV, BSB, Hebrew, Didache, Compare — all good).

Why wrappers / not byte-identical: unlike the preamble (top-level move, app.js unchanged), this changed
call sites (`renderVerse(v)` → wrapper), so the "app.js unchanged" proof didn't apply. Verified instead
by clean build + `node --check`, an audit that every ctx field is destructured in each function that uses
it with no LibraryView-local leaked through, 13 wrappers present + old defs gone, and a deterministic
rebuild.

LESSON — line endings (cost ~30 min): the repo's `static/src/*.jsx` are NOT all CRLF (the old CLAUDE.md /
memory claim). They're MIXED — 60-library.jsx is LF, others (59a/59b, 10-icons, 30-detail-panel,
59-dayintro) CRLF. I wrote the new/changed files CRLF on that assumption, flipping 60-library LF→CRLF
(whole-file diff); fixed by converting both to LF to match HEAD. app.js legitimately carries 4 CRLF from
CRLF sources' block comments. RULE: match a file's existing endings, don't flip a whole file; check with
`xxd`/byte-count, NOT Git-for-Windows `grep`/piped `git show` (both falsely called the LF 60-library
"CRLF"). Docs corrected: CLAUDE.md + memory project_frontend_build_step / project_code_quality.

## Library AI synthesis — framing-over-prohibition pass — DONE 2026-06-14

Killed three output leaks in the Library's AI writers WITHOUT adding "don't say X" rules — the
user's explicit ask. All three traced to the same mistake: a blacklist/command bolted on, fighting
the frame. Fixed the FRAME + the worked EXAMPLE instead. Full record: memory `project_ai_synthesis_quality`
("Framing over prohibition"). Backend `.py` only, no app.js rebuild; user deploys (his step), reviewing live.
- **LSJ word definition (views_lsj.py)** — was still citing Homer/Iliad despite a "don't reference
  Homer/Plato/Attic" blacklist (we feed it a classical lexicon entry, then forbid echoing it — the
  blacklist loses, and naming Homer primes it). Reframed: audience = someone *reading the Greek Bible*,
  the entry = "source material to distill"; dropped the blacklist. Also fixed the user's self-reference
  catch (it re-announced the headword / defined in a circle) via "the reader is already looking at the
  word + its translation; pick up from there." Pulled the two asks into constants + added `_LSJ_SYNTH_VER`
  → LSJ now **fingerprint-self-heals** (a `_synth_ver` stamp in summary_json), so a prompt edit
  auto-refreshes; the old `clear_parse_jargon_cache.py` is no longer needed for prompt changes.
- **Chapter summary (views_summary.py)** — "Moses wrote/records…" opened every Pentateuch chapter
  because the author line was injected into the chapter prompt (+ "use the author's name"). Fix = SCOPE:
  the author now feeds ONLY the book blurb; the chapter prompt just says what happens, so Moses is named
  only where the text puts him. Auto-refreshes via the existing summary fingerprint.
- **TSK xref synthesis (views_crossref.py)** — self-referenced "related passages" + "thematic/the thread",
  because the worked EXAMPLE itself modeled it ("Later passages keep returning…", "The thread is…"). The
  example beat the rule. Rewrote the example to name specifics ("Running through all of it is…"), reframed
  to "write from inside the text… name a specific passage when it carries the point," dropped the quoted
  blacklist. Auto-refreshes via `_XREF_VER`.

OPEN backstop (only if LSJ still cites Homer once live): strip the obvious classical author names out of
the entry text before the model sees it — no rule, just don't feed it. Left for a follow-up thread.

## Days month-grouping + mobile sticky header + intro/overview mobile header — DONE 2026-06-14

Small polish round, all live/pushed. Full record: memory `project_chronological_tab` "SESSION 2026-06-14".
- **Days list = ~12 collapsible MONTH blocks** (58-dayplan.jsx) — 365 rows was too long to scroll.
  Accordion, one month open at a time, auto-opens to the month you're reading. `monthSize = ceil(total/12)`.
- **Mobile Days progress header is now STICKY** (was `position:static` after an earlier bleed-through
  attempt) — pulled to the sheet edges so it's a solid full-width bar, no rows peek beside/above it.
- **Mobile intro card + overview popup header = compact `‹` chevron** inline with the title (not the
  wide "‹ Overview"/"‹ Intro" text), ✕ dropped from both (handle + tap-outside close them), title
  auto-shrinks to one line via the NEW `useFitText` hook (20-shared-components.jsx; `useLayoutEffect`
  added to 00-core). The painful path here (stacked-above, reserved-gutter — both rejected) is the
  lesson in memory `feedback_ui_iteration`: on a fussy visual tweak, shrink the control, don't relayout.
- **More popout + Compare dropdown swallow their dismiss click** (capture-phase one-shot, like the Aa
  menu) so the outside click that closes them doesn't also hit a word chip behind.
- **Search popup mode toggle (Any/All/Phrase) → underline tabs** (was a filled box), mirroring the
  source picker.

## Chronological views cleanup — rail design language — DONE 2026-06-14

Gave the chronological views the same look as the detail-rail pass. All live (user deployed as we
went). Full record: memory `project_chronological_tab` "CHRONOLOGICAL VIEWS CLEANUP" + `project_side_panel_rail`.
- **In-reader chapter marker** (`.lib-chrono-chapmark`, reader + Compare): gold → navy; spacing 16/9 →
  28px top / 5px bottom (heading hugs what it labels).
- **Days plan rebuilt:** dropped the per-row left check, the gold "Today" highlight, the navy "Reading"
  tint, and the open/collapse caret. One marker on the RIGHT — navy ✓ (read, click to undo) / navy dot
  (the day you're reading); clickable only on the day you're on (un-mark a prior day = select it first).
  One-click on a day = collapse the open day + open this + move the dot + load its first reading. Navy
  backbone spine (pseudo-element on a full-height inner wrapper, not a border on the scroll box — the
  border only spanned the visible rows) + a GOLD sub-rib on the open day's passages. Active passage =
  just bold. "Jump to today" selects today too.
- **Eras picker** matched Days: navy spine + gold sub-rib on the open era, de-boxed headers, no caret.
- **Mobile Days:** tap-a-day = same select behavior but the sheet STAYS open (a separate
  non-closing `onPickPassage`); NO spine; bigger rows/text; progress header `position:static` (sticky
  pinned below the scroll padding and rows bled through the gap). A mobile-Eras restyle was TRIED then
  REVERTED — user said Eras-on-mobile is fine, only Days needed work.
- **Reading-intro "Today's passages" + metaV "Nave's" rows:** dropped per-item boxes → plain hover rows.
- **Word/xref back-link follows the rail base:** "‹ Intro" over the chrono day-intro, "‹ Overview"
  otherwise (LibraryView `detailBase` → App `backLabel`).
- **Source picker + Eras/Days toggle → underline tabs.** The source row is a 4-equal-column GRID so the
  active "More" label (HEB/ESV/a book name) can't change a tab's width and shove ABP/KJV/BSB — the real
  "resize" bug (the inline-flex `.seg` was content-sized; flex:1 1 0 didn't equalize). A FIXED-height
  popout was tried for the menu first and REVERTED — the user only wanted the BUTTON to stop resizing.
- **More menu → floating popout** (anchored under the source row; ESV/NIV/Hebrew under a default-open
  "Bibles" group). Both the More popout and the Compare ▾ menu close on click-outside / Esc (document
  listener; replaced Compare's old z-90 scrim that sat under the toolbar). Picking a row text closes More.

## Book-summary author list — added scribes; metaV fold-in TRIED then REVERTED — 2026-06-13

The reading-pane book blurb names the writer from `_BOOK_AUTHORS` (views_summary.py), which lists
only well-established authors and leaves the anonymous books blank. SHIPPED: the two scribes that the
text itself names — Jeremiah/Baruch (Jer 36) and Romans/Tertius (Rom 16:22), added inline to the
value. Those render cleanly (Jeremiah's blurb opens "Jeremiah… dictated this book to his scribe
Baruch"). That's the only lasting change.

TRIED AND BACKED OUT: folding metaV's **Writers** list (gusheng/MetaV — same dataset as People/Places)
into the blank books — Judges/Ruth/1-2 Samuel=Samuel, Kings=Jeremiah, Chronicles=Ezra, Job=Moses,
Esther=Mordecai (Hebrews metaV honestly marks "Unknown"). First as a LIVE read of `metav_writers`
(book_id 1-66 → abbrev via core `_KJV_BOOK_ID_REV`), then baked into the one list. Either way Haiku
WOULDN'T name those disputed authors — the summary SYSTEM prompt only names an author "when well
established", so it stayed silent (Job showed no writer). So we loosened `_AUTHOR_LINE_TMPL` to license
a "traditionally attributed to X" hedge — and it OVER-CORRECTED: Job's blurb then flatly said "Moses
wrote this book" and the chapter summary even narrated "Moses records, Job did not sin." Reverted the
hedge AND removed all the metaV gap-fills; the anonymous books are blank again.

Lessons worth keeping:
- **The name in the list is INERT — the prompt push is what broke it.** With normal wording Haiku
  just ignored Job=Moses and left the blurb blank; only the extra "traditionally attributed to X /
  don't omit the author" hedge forced it to assert. So a disputed name SITTING in the list is harmless;
  the danger is instructing Haiku to use it.
- **Don't hard-push Haiku on shaky facts.** It doesn't do "honest hedge" well — push it to name a
  disputed author and it asserts the claim outright (and leaks it into the chapter narration). Better
  to feed only well-established names and let Haiku stay silent on the rest.
- **DECIDED: don't re-add the metaV names.** Every gap-fill is a disputed/traditional attribution (the
  exact reason the curated list omitted them); none is "well established." Without the push Haiku would
  unpredictably assert some as fact. Curated list stays well-established-only + scribes. Don't re-try.
- **metaV doesn't fabricate, but it's confident about disputed traditions.** Honest "Unknown" for
  Hebrews, but flat Job→Moses, Esther→Mordecai, Kings→Jeremiah, etc. — fringe/Talmudic, not settled.
  Its data was also looser than ours in two spots (Psalms="David" vs our "David and other psalmists";
  John="John" vs "the apostle John"), so a blind total-swap would've been a downgrade.
- Not a cache/wiring bug — Jeremiah picking up Baruch immediately proved deploy + cache-refresh worked.
- `metav_writers` table exists (loaded by load_metav.py) but is NOT read anywhere now — dormant.
- Commits: 870db14 (live-read), bbf5148 (bake-in), 645c38f (hedge), c02ea0f (revert to scribes-only).
- OPEN, optional: 1 Peter "by Silvanus" (1Pe 5:12) as a scribe — debated (scribe vs carrier), left out.

---

## Study modules — admin Study tab + MetaV/Nave's import — BUILT 2026-06-12

Recovered a lost idea ("a DB that had study topics") → it was the **MetaV** dataset
(github.com/gusheng/MetaV, the same one People/Places/cross-refs came from), which carries
Nave's+Torrey's **Topics + TopicIndex**. Built an admin-only **Study** tab: sub-switch
**Topics · Denominations · Arguments**. Topics = a sectioned browse; denomination/argument = a
position→support→tension→resolution claim editor. Own `study.db` (gitignored, PA-only),
`views_study.py`, `static/src/55-study.jsx`. Loader `scripts/load_study_topics.py` imported
~1,819 concept topics + 696 person/place "name-topics". Full record: memory `project_study_modules`.

**Follow-on, all SHIPPED 2026-06-12/13:** the Nave's-sidebar tap-through; a real TWO-SIDED argument
layout (Side A | Side B + resolution, its own `sides` shape); a stepped reader WALKTHROUGH (built then
DROPPED for collapsible subtopics on the page — same cure, one view) + a BOOK sub-collapse inside big
subtopics; a "Preview as reader" admin toggle (all types now read-first); AI-drafted text-first Berean
topic INTROS (Haiku default / Sonnet for the public batch, sharpened prompt; ✦ button + bulk script);
title comma-flip for display + alphabetical list sort; and a publish/dupe-cleanup script set. Only the
public "go-live" flip (open published topics to visitors) is left.

Lessons worth keeping:
- **Topics are NOT claims.** First cut forced every topic into the support/tension/resolution
  shape; a plain topic is just "a subject + its verses," so that shape made no sense. Split into
  TWO shapes — sectioned topic browse vs the claim editor. Don't re-merge them.
- **Filter MetaV name-topics by NAME, not a verse-count proxy.** Nave's lists every proper name;
  those are already in the metaV sidebar + word search. Drop them using MetaV's own People/Places
  lists (short whitelist for God/Jesus/Holy Spirit); keep concepts. The verses-count "bandaid" was
  wrong — it kept big names and could drop small concepts.
- **MetaV's curated topics ≠ a concordance.** Subtopics ("Affliction — consolation under / made
  beneficial") are thematic and include verses without the keyword — real value over plain search.
  For bare names it IS just "where mentioned" (= search), hence dropping them.
- **CSV gotcha:** read MetaV CSVs as `utf-8-sig` — a BOM in the header made every verse link drop
  (the "0 verses" symptom). `--replace` clears prior `metav*` rows first so a re-run is clean.
- Verse text shown = **ABP prose** (the words' english joined like Prose mode), KJV per-verse fallback.
- **Walkthrough → collapse (06-13).** A stepped one-at-a-time reader was built first; on small topics it
  barely differed from the page, so it was dropped for collapsible subtopics (the cleaner fix). Don't re-add.
- **Nave's titles are index-style** ("Life, Eternal", "Devil"=Satan, "Accusation, False"). Match the
  curated `_COMMON` hot-list to the REAL titles (`find_topics.py`); flip them for DISPLAY only
  (`displayTitle`), don't rename the stored data. "X, the" = "The X" (mergeable dupe); "X, <aspect>" is a
  real subtopic (keep). Merge folds "X, the"→"X" with a dry-run + study.db backup + soft-delete.
- **Slow topic load was connection churn**, not the ABP word-stitching — `_resolve_body` opened a fresh
  db connection PER VERSE (~67 for a big topic). One shared connection fixed it (commit 25ad365).
- **Script API key:** the Anthropic key lives in the WSGI, not the shell — bulk scripts need
  `export ANTHROPIC_API_KEY=...` first or `core._anthropic` is None and they no-op.

## Focus mode + reader gesture/scroll fixes — DONE 2026-06-11

All on master, pushed. Full record: memory `project_focus_mode`.

- **Focus mode (distraction-free reading).** Tap blank space in the reader to strip the chrome; Esc or
  tap exits. NOT remembered across reloads. **Mobile** hides the chrome outright (header/nav/toolbar/tabs/
  audio — audio keeps playing). **Desktop** darkens everything with a click-through dark wash and floats
  the text as a `position:fixed`, centered, self-scrolling "book page" with big ‹ › page-turn arrows in
  the side gutters. Files: `90-app.jsx` (flag + shell class), `60-library.jsx` (trigger/page-turn/arrows),
  end of `styles.css`. Iterated live with the user: desktop went from hide-all → dark-spotlight; the page
  got centered on the whole screen (not the offset column), made tall with both edges, and the arrows
  moved to hug the page edges and grew to 76px. Open by-design: word-click lexicon shows dimmed behind
  the page in desktop focus.
- **Verse-number hit area tightened.** Digits moved to an inner `.lib-vnum-num` hit target; the `.lib-vnum`
  gutter is `user-select:none` + inert. Killed the "click/drag beside the number highlights the verse" bug.
- **Highlight pop-up = dismiss-only click** (matches the verse-number menu). First click closes it and is
  swallowed (no chip/verse/focus underneath). LESSON: the close re-renders before the click lands, so a
  state-in-closure check read stale — fixed with a `swallowClickRef` set at mouse-DOWN, checked AFTER the
  `justSelectedRef` (selection-ending) check. Two passes to get right.
- **Pericope headings left-aligned on both** mobile + desktop (were centered on mobile); mobile keeps the
  hidden verse-gutter width so the heading lines up with the verse text.
- **Jump-to-verse scroll:** reader lands the verse in the UPPER THIRD (not centered); left nav scrolls the
  active book to the TOP of its own `.nav-scroll` list, never the window (which used to push the verse
  off-screen). Decided per-case: reader = upper-third, nav = top.

## NIV text + multi-text Compare + reader UI tweaks — DONE 2026-06-10

All on master, deployed. Detail: memory `project_esv_audio` (NIV) + `project_pericopes_parallel` (Compare).

- **NIV — 2nd owner-only text, mirrors ESV exactly.** `views_niv.py`, own `niv.db` (gitignored, PA-only),
  `core.niv_db`, NIV toggle next to ESV. TEXT-ONLY — checked FCBH and it doesn't carry NIV audio (commercially
  licensed), so no audio route. Source = aruljohn/Bible-niv (66 JSON files, `book/chapters/verses`); loaded by
  `scripts/load_niv.py ~/Bible-niv ~/bible-db/niv.db` (maps book name → 1-66 id, ~31,104 verses). The loader
  fixes the source's backtick-for-apostrophe quirk (`God`s` → `God's`); validated the format against the real
  repo before loading. No WSGI change — the existing `OWNER_EMAIL` gate covers it.
- **"Parallel" → multi-text COMPARE (pick 2–4).** Choose any 2–4 of ABP/KJV/BSB/ESV/NIV side by side.
  Desktop = N columns (`.lib-cmp-2/3/4`); mobile = stacked, one labeled line per text (user picked
  "stack per verse" over side-scroll). `compareSel` array holds the picks; per-text loaders fire when their
  id is selected; render = ordered UNION of verse keys (chapter+verse) so a missing verse leaves a blank cell.
  BSB/ESV/NIV inherit the Psalm alignment for free (all English = MT numbering). Notes/highlights SHARED across
  columns (plain columns got the anchor + whole-verse highlight paint + note dot; ABP/KJV inherit theirs).
  LESSON: in compare the home-text exact-WORD highlight paint rounds up to whole-verse (translation is
  "parallel", matches no note's home text) — left as-is on purpose (reads clean in narrow columns).
- **Reader UI tweaks (same session):** mobile note/journal/copy bar is icon-only (reused the existing
  `note-btn-lbl` span that CSS already hides on mobile; desktop keeps the text); mobile prose verse number
  kept `inline` instead of `inline-block` — that was the cause of the number dangling at a line end (an
  inline-block creates a wrap point after it; inline doesn't). Book selector left as-is (the translation
  buttons live in the left nav, not the toolbar, so columns don't crowd it).

---

## ESV (owner-only) + read-along audio + visitor stats — DONE 2026-06-10

A big session. All on master, deployed. Full detail: memory `project_esv_audio` + `project_visitor_stats`.

- **ESV reading text — owner-only, server-gated, LIVE.** Crossway-copyright → not public. Gated to the
  owner's notes.db login on the SERVER (404 to everyone else, not just a hidden toggle). Own `esv.db`
  (gitignored, PA-only), loaded by `scripts/load_esv.py` from github.com/lguenth/mdbible (`by_book/NN_Name.md`;
  31,104 verses). `views_esv.py`. Reads like BSB (plain, proseLocked).
- **Read-along audio.** BSB is LIVE for everyone — public-domain openbible.com Souer mp3s (no key, no
  self-host). ESV audio built (FCBH Bible Brain, NT-only fileset) but waits on `FCBH_API_KEY`. Shared
  `core._USFM_BOOK` + `usfm_titlecase()` (FCBH wants UPPERCASE, openbible title-case).
- **Player evolved through several user passes** (lessons): custom player with skip buttons → then
  "Listen button = play/pause + just a bar" → then moved into the TOOLBAR (icon) → chrono got inline
  per-chapter controls, which were CLUNKY on mobile and got REVERTED to one scroll-aware toolbar button
  (plays the chapter at ~45% mid-screen; bar inline only at the playing chapter in chrono). KEY BUG FIX:
  the play/pause icon must reflect ONLY whether audio is playing (`showPause = audioPlaying`) — tying it
  to the in-view chapter made it flip on scroll ("doesn't catch up").
- **KJV/BSB/ESV now read as continuous PROSE** (`renderFlowVerse`, `.lib-prose-flow`) like ABP — they used
  to render one block per verse everywhere (most obvious in chrono). Word/chip + parallel modes unchanged.
- **Visitor stats — owner-only, in-house.** Tried GoatCounter (one script tag) then REMOVED it for a
  private counter in `notes.db` (`visits` table; daily IP+UA hash, referrer, no cookies/IPs, owner's own
  visits skipped). `views_stats.py`; About → **About|Stats toggle** (not a separate tab; `85-stats.jsx`).
- **One shared site-owner gate:** `views_notes.is_owner()` (`OWNER_EMAIL`, falls back to `ESV_OWNER_EMAIL`)
  — set ONE env var to gate both ESV + Stats. views_esv dropped its local copy. GOTCHA confirmed again:
  the env line must sit ABOVE the app import in the WSGI + reload (module-level read at import).
- Smaller wins: tab remembered across refresh (`localStorage` `lexica.view.v1`); distinct verse-marker
  icons (bookmark ribbon vs note/highlight pencil); desktop chapter label dropped from the toolbar;
  source picker compacted so the owner's 5th button (ESV) fits; verse-menu Note icon-only on mobile;
  all scrollable popouts got `overscroll-behavior: contain` so they don't bleed-scroll the reader.

---

## Words-table rebuild → one self-correcting pass (refactor backlog #2) — DONE 2026-06-09

The rebuild used to be: wipe the word table, rebuild from source, then run a long chain of ~14 patch
scripts in an exact order to fix it back up — the riskiest job in the repo. Now the build fixes
itself. The six shape-keyed, re-runnable cleanup steps run INSIDE the build, per verse
(bracket_punct, g1473_gloss, lord_subject, funcword_subject, lord_oath, greek_pos backfill), in the
same order the old chain used. Only the genuine per-verse patches that a blanket rule would break
stay behind, run by one tail script (`scripts/finish_rebuild.sh`) plus a final punctuation pass.

- **Proven, not hoped.** Built it BOTH ways on a copy of the live database — old way (build + all 14
  patches) and new way (the one self-correcting pass) — and compared every word: **byte-identical**
  (same 624,575 rows, same fingerprint). Tools: `scripts/compare_words.py` (whole-table compare),
  `tests/test_folded_fixes.py` (now in CI + the commit hook).
- **Validated locally first**, on copies in a folder OUTSIDE the repo (`C:\Users\JP\lexica-val`:
  bible.db + bh_scrape.db + the Rahlfs/TAGNT alignment files). The live database was never touched.
  Committed `815c1c6`, pushed, CI green, deployed to PA.
- **Bonus, the one place the new build beats the old chain:** the final punctuation pass also tidies
  ~202 spots where a comma sat on the verb instead of the last word shown in the LORD-subject
  brackets ("said · the LORD,").
- **Kept as small pinned patches (can't fold):** split_merges (237 — a general splitter rule
  regresses ~85 other verses), subject_reorder / mat25_37 / supplied_attach (hand-listed reorder
  verses), theos_filler_tags + kyrios_mistags (a few SOURCE mis-tags you can't rebuild away — e.g.
  Greek "Cyrus" looks like "of the lord"), merge_misses. ~270 verses out of 31,000 — small and stable.
- vs the LIVE database there were 17,498 differences, ALL pre-existing drift (older head-word
  handling + a newer proper-noun list + 3 Cyrus fixes live never got) — none from the fold; the
  old-way rebuild showed the same drift. The standalone fix_*.py scripts are KEPT as re-appliers; on
  a fresh build they find 0 to do.

**THE STANDING LEVER — CHECKED 2026-06-09, DECLINED (keep the patch).** The word-splitter GUESSES
which English word goes with which Greek word by matching the dictionary — that leaky guess is what the
237-verse `fix_split_merges` patch cleans up. The idea was to feed the real word-by-word alignment data
(the Rahlfs/TAGNT files from the pronoun fix) into the splitter (`_split_compounds`) to replace the
guess and retire the patch. A read-only check on the lexica-val copy killed it: that data is Greek-only
— it tells you each Greek word's grammar but never which English word pairs with it, so it can't do the
English-to-Greek matching that IS the splitter's job. It can only act as a grammar filter afterward, and
the filter can't tell a good split from a bad one: allowing only plain nouns/verbs would wrongly throw
away 126 of the 240 good fixes (53% — the good splits land on little words like "and"/"me"/"not" all the
time), and the grammar tag is missing on a fifth of all words. The one clean signal — "never pile a real
word onto 'the'" — covers under half the garbles and the build already guards it. So the frozen
237-verse patch stays: small, stable, proven. **LESSON:** an alignment with no English in it can't
replace an English-pairing step; it can only filter, and a filter can't reconstruct the missing pairing.
Throwaway check scripts: `C:\Users\JP\lexica-val\check_splitter_morph.py` + `check_237_targets_morph.py`.
See memory `project_architecture_rework` (#2) and `project_parser_number_reversal`. DON'T re-investigate.

---

## BSB (Berean Standard Bible) reading text — DONE 2026-06-08

Public-domain modern reading text alongside ABP/KJV. Loaded by `scripts/load_bsb.py` into
`bsb_verses`, served by `views_bsb.py` (`/api/bsb/chapter`); third option in the Library toggle
(commit `4c88501`). Also added an eSword-style in-text search box that searches whichever text you're
reading, via the generic `/api/text-search` (commit `05fe6d5`). No word-level/Strong's data by design.

---

## Free-form Journal — second note mode — DONE 2026-06-09

"Verse notes | Journal" toggle in the Notes tab: plain-text titled pages, a full-page autosaving
editor, riding the same store / sync / Export-Import as anchored notes (`kind:"journal"`, no anchor).
Plus copy + "send verse to journal" from the reader (drag-select bar AND the verse-number menu) into
the page you have open. Detail in memory `project_notes_highlights`.

---

## Front-end "build a word entry" de-dup (refactor backlog #3, front-end half) — DONE 2026-06-08

The three copy-pasted entry-builders now share one core (`entrySnum()` + `wordEntryCore()` in
static/src/00-core.jsx); makeEntry / flattenAiResults / the library makeEntry each spread the core
and add only their own id + extras. No behavior change. Commit `007446c`. Closes the front-end half
of refactor backlog #3 (the backend half was redesign Phase 2).

---

## Notes accounts + sync (email + Google) — DONE 2026-06-09

Built right after the notes feature, same session. Notes started browser-only; the user weighed a
"sync code" (decided too clunky to copy around) and went with real **email + password accounts**,
then added **Google sign-in** too. Because the notes were already stored in the migration-ready
shape (each note has its own id from creation), turning on accounts was a straight copy — nothing
from the browser-only build was wasted.

- It's the **first time the site stores anything a visitor creates** — everything before was
  read-only/no-login. User data lives in its OWN file, `notes.db`, kept separate from the Bible
  database so a corpus rebuild can't touch it.
- Accounts are **opt-in**: the app stays fully usable with no login (notes just stay on that one
  browser). Sign in and your notes follow you to any device.
- Passwords are stored scrambled one-way (never readable). Staying logged in uses a random token,
  not the password. Sync merges by each note's id, newest edit wins; deletes leave a marker so they
  spread instead of coming back.
- Google sign-in is wired so the button only appears once it's fully set up — a half-finished deploy
  can't break the site.
- **Not done:** "forgot password" / set-a-password — that needs the site to send email, which isn't
  set up on PythonAnywhere yet. So a Google-only account has no password to fall back on for now.

Lessons that cost time (in memory `project_notes_highlights`): the site's secrets/keys live in the
**WSGI file** (`os.environ[...]`), not a `.env` — the `.env` on PA was empty and ignored, so the
Google ID had to go in the WSGI file, above the app import, then reload. Diagnose a missing Google
button with `curl <site>/api/auth/config`. And `google-auth` needs a `pip install` in the venv after
pulling (it's in requirements.txt).

---

## Notes & highlights (study notes) — DONE 2026-06-09

Readers can now write study notes and paint color highlights right in the Library, and find them
again later. Built and shipped in one session as small POCs, tweaked live against the user's testing.

- **Where they're kept:** the browser only (`localStorage`) — no database, no login, nothing on
  PythonAnywhere. Decided browser-first on purpose: the saved shape is exactly what a future
  account/sync would use, so moving notes "up to the cloud" later is a straight copy, not a rewrite.
  Each note gets its own id the moment it's created, so merging two devices later won't duplicate.
- **How you make one:** drag-select words → a little bar with 5 highlight colors + a "Note" button;
  or right-click a verse number (long-press on phones) for a whole-verse note. These don't fight the
  existing clicks — a word still opens the lexicon, a verse number still opens cross-references.
- **A note and a highlight are the same thing** — one record that can have text, a color, or both.
- **Finding them:** a new Notes tab lists everything with text search, plus Export (downloads a
  backup file) and Import (merges one back in, safe to re-run). A bookmark shows in the margin of
  any verse that has one.

Lessons / why certain choices: chip mode has no spaces between words, so the saved quote had to be
rebuilt from the chips (not the raw selection). On mobile the browser's own copy/share toolbar fights
a popup near the selection, so the "Add note" bar is pinned to the screen bottom there. The margin
marker had to live *inside* the verse text (indent the first line only) or it shoved every wrapped
line over. Highlights paint only in the text they were made in (ABP word-for-word; KJV/BSB whole
verse) — true cross-translation paint is a known follow-up. Open follow-ups are listed in TODO.md;
full detail in memory `project_notes_highlights`.

---

## AI result cache — unified prompt-fingerprint scheme — DONE 2026-06-09

The four Haiku-backed caches (AI search, reading summaries, TSK cross-refs, person/place blurbs) all
live in the one `ai_search_cache` table but each versioned itself differently: search hashed its own
prompt (good — edit the prompt, the cache auto-refreshes), but summaries used a hand-bumped number you
had to remember to change, and the cross-ref + person/place caches never refreshed on a prompt edit at
all. Fixed: every cache now tags its rows `category:hash-of-its-own-prompt`. Edit any prompt and only
that cache refreshes, lazily, with no manual bump.

- One shared set of helpers in `core.py` (`ai_fingerprint`, `ai_cache_get/put`, `ai_cache_prune`,
  plus a one-time `ai_cache_drop_legacy` sweep). Each cache prunes only its OWN stale rows at startup.
- **The landmine, handled:** search's old startup cleanup deleted every other cache's rows except the
  ones it spared by name. Switching the other caches to the new tag would have made that delete wipe
  them. It's now scoped to search's own rows only. Proven with a focused test (search prune leaves the
  others untouched, and each cache prunes only its own).
- **Per-book authors (the user's call):** a summary's row key stays stable, the author goes only in the
  tag — so editing one book's author refreshes just that book, while editing the prompt wording refreshes
  all summaries.
- LSJ was deliberately left out — it stores its summaries in the lexicon tables, not this cache table.
- One-time cost: the first run after deploy clears the old-format rows, so everything cached before
  regenerates once on next view. Unavoidable when changing the tagging scheme.
- Verified locally without touching the real database: logic test on a throwaway copy + a full app boot
  against a copy of the database (startup cleanup ran clean). Closes refactor backlog #4's cache half;
  the paired prompt-STYLE cleanup is still open in TODO.md.
  `code: core.py helpers, ai.py ~741-805, views_summary.py, views_crossref.py, views_metav.py, app.py startup`

---

## Word click-targets ("dual-ordering") — mostly done

The goal: when one slot bundled several English words, give each its own clickable chip while
keeping both the Greek order (chip view) and the English reading order (prose view) correct.
Again — never a reading bug, just click precision. The mechanism is proven and the bulk shipped:

- **"the LORD" + verb** — split so "the LORD" is its own chip. 795 spots fixed, live 2026-06-05.
  Rollback: `bible_pre_lordsubj_20260605.db`. `script: fix_lord_subject.py`
- **Nouns stuck on a function word** — moved the noun's English back onto its own empty slot.
  Done in three rounds (everyday nouns, then idioms, then plurals/in-bracket cases), 108 fixes
  total, live 2026-06-06. Rollbacks: `bible_pre_funcword_20260606.db`,
  `bible_pre_funcword_idioms_20260606.db`. `script: fix_funcword_subject.py`
- **Scrapped:** a third case (a verb's English wrapping around its subject) — too few, too varied,
  and would need risky row inserts for tiny payoff. Parked for good.
- **ἴδιος "own"** — 'his/their/its own' (ὁ G3588 + ἴδιος G2398) parked on the article slot with ἴδιος
  empty beside it. Same relocate move as the noun fix, but the orphan is the ADJECTIVE ἴδιος, so the
  folded noun pass skipped it. 13 spots (1Co/1Ti/2Ti/2Pe/Heb), live 2026-06-14. Rollback:
  `bible_pre_idios_20260614.db`. `script: fix_idios_own.py` (+ `dump_verse_words.py`, read-only inspector).

The "the"/article cleanup is now essentially CLOSED (see live TODO): a 2026-06-14 read-only
`audit_funcword_wrongslot.py` re-measure showed the NOUN-behind-"the" case at **0** (the folded
`funcword_subject` already handles it — the old "highest-volume remaining" framing was stale), the
ἴδιος "own" subset is fixed (above), and the ~25 remaining gray-zone cases (midst/least/whole/indeed,
some defensible Greek) are left on purpose. The proven method if anyone resumes a similar cleanup:
always start read-only and measure first; copy the database before any real change; never run a
blanket delete; keep repair scripts narrow, re-runnable, with a dry-run; and add them to the
checklist in CLAUDE.md.

---

## Non-canonical library — built and live (2026-06-07)

A whole shelf of extra texts now lives in the Library under the "Other" menu, walled off from Bible
search and word counts (ABP stays the anchor). All English-only unless noted:
- **Septuagint Apocrypha** (16 books, Brenton 1851).
- **Pseudepigrapha** — 1-2 Enoch, Jubilees, 2-3 Baruch, Apocalypse of Abraham, Assumption of Moses,
  2 Esdras/4 Ezra, Life of Adam and Eve, Psalms of Solomon, Letter of Aristeas, Ascension of Isaiah,
  Sibylline Oracles (mostly R.H. Charles; sources per-book in memory).
- **Testaments of the Twelve Patriarchs** (12 separate books, Charles).
- **Apostolic Fathers** (14, incl. Didache) — these have the **full Greek interlinear**, same
  word-study layer as the Bible: Brannan/Lake Greek → Strong's (openscriptures + Dodson glosses) →
  Lightfoot English. Polycarp ch 10-14 survive only in Latin → English-only there.

How it's built (generic, re-runnable): each text gets its own two tables `<book>_words` /
`<book>_verses`, served by `/api/extra/<book>/chapter/<n>`, loaded by `scripts/load_extra.py`. Adding
a future text = tag it, drop two json files, add one line to `NONCANON`, load. `englishOnly:true`
locks the reader to Prose for texts with no original-language tagging. The full pipeline, source URLs,
and per-book parsing quirks are in memory `project_noncanonical_texts`. Still open (in the live TODO):
more books (Jasher, 4 Baruch…), optional hand-written headings, wiring these into the Lexicon/Search
tabs, and the Hebrew-interlinear gap.

---

## Search results now match the Library look — done

The AI search result verses were restyled to match the polished Library reading view: plain word
chips in reading order, no Strong's clutter, brackets kept, gold highlights kept (same as Library's
chip mode). Also stopped re-fetching each verse's words one at a time — the search response now
carries the words the server already built. `code: Search results in static/src/70-search.jsx`

---

## Lexicon tab — finished (ongoing polish only)

The word-study flow (search → word profile → gloss chips → book distribution → verse list) is done
and reads cleanly, matched to the Library look. Anything left is minor spacing/hierarchy polish done
as noticed — nothing structural. `code: LexiconView in static/src/80-lexicon.jsx`

---

## Full corpus audit — done, corpus is sound (2026-06-05)

Checked all ~624k words against independent reference texts. **Verdict: the corpus is sound.**
- Internal consistency check: zero of the pronoun-class corruption that bit us before.
- External agreement: ~92% match against the reference Greek texts. The other 8% is *not* error —
  it's genuine edition/translation differences and proper-noun number quirks. **100% is the wrong
  target** (it would mean rewriting our text into theirs) — don't chase it.
- One real issue found and fixed: 1,724 pronoun slots labeled with the wrong person, corrected.
  Rollback: `bible_pre_g1473gloss_20260605.db`. `script: fix_g1473_gloss.py`
- A residual ~1,069 cases are blocked on missing grammar data — not chased, not worth guessing.
- Audit scripts are read-only and in the rebuild checklist. `scripts: audit_corpus_tier1/2.py`

---

## Word-order garble fixes — done (2026-06-05)

A rebuild had left some multi-word phrases reading backwards or bundled wrong.
- **"this/that of X" over-reach** — fixed; 3,438 verses corrected. Rollback:
  `bible_pre_splitfix_20260604.db`.
- **Bracketed phrases reading scrambled** — fixed; 374 → 0. (Memory: project_bracket_order_fix.)
- **Hab 3:14 showed up twice** — root cause was a duplicated line in the source text file; removed
  at source and cleaned the live database. `script: fix_hab314_dupes.py`
- **Punctuation on the wrong word** — fixed (365 verses). `script: fix_bracket_punct.py`
- Known harmless false alarms in the old audit tools (~8 twin-bracket flags) — database is correct,
  **don't re-chase them.**

---

## Lexicon coverage for pronouns — done (2026-06-04)

Made sure pronoun forms (this/that/who/me/you in all their endings) resolve to a real dictionary
entry instead of a terse fallback. Found the big paradigms already resolve fine; added a handful of
small redirect stubs for the few genuine gaps. Rollback for the stubs is a one-line delete (in the
memory note). Reopen only if a specific word is reported showing the terse gloss.

---

## Text structure — done

- **Section headings** added across the whole canon (2,431 of them), shown in chip/prose/parallel.
  (Song of Solomon has none — the source doesn't carry them; not a bug.)
- **Prose reading mode** — normal books flow as paragraphs with small verse numbers; poetry keeps
  one line per verse.
- **Font size control** — A−/A+ buttons, remembered in the browser.

---

## Reader typeface picker — TRIED + REVERTED (2026-06-11)

Built a "Reading font" picker (Source Serif default · Cardo · Gentium) in the text-style menu, then
**pulled it the same day** (commits 8a9a635/6a08858 in, f1f96a5 out). **Why it failed:** the reader
was already on Source Serif 4 — a good serif — so this was a preference toggle, not an upgrade. The
two alternatives both looked worse on the user's Windows display (Cardo renders thin/rough; Gentium
also disliked). Replacement candidates (Literata, EB Garamond, Noto Serif) didn't win either, so the
user scrapped the whole picker rather than keep weaker fonts. **Lesson: don't re-add a serif picker —
Source Serif is the keeper.** What DID work and is worth remembering if this ever comes back: scope a
font swap to the reader by overriding `--f-serif`/`--f-greek` inline on `.lib-reading` (custom props
inherit, so the rest of the app is untouched); Google fonts lazy-load (the binary downloads only when
a glyph renders); and Cardo/Gentium need a Hebrew fallback (Frank Ruhl Libre) since they carry no
Hebrew — that fallback DID render cleanly (no boxes). Memory `project_reader_appearance`.

---

## Pronoun number fix + grammar display — done (2026-06-04)

Live as rebuild #6. Rollback: `bible_pre_morph_20260604.db`. (Memory: project_pronoun_fix_path_c.)
- Added word-grammar data (part of speech, tense, case…) covering ~78% of words.
- Fixed "he is a prophet" word order (Gen 20:7) and a couple of related ordering cases.
- Word grammar now shows in plain English in the word pop-up for ABP Greek (e.g. "Verb · Aorist ·
  Active · Indicative · 3rd person · Singular").

---

## MetaV (people & places) — done

- People sidebar (bio, family, genealogy) and places sidebar (map + coordinates), with proper-noun
  clicks routed correctly in both ABP and KJV.
- Hebrew names route to the people/places view with the Hebrew dictionary stacked below; clans
  (the "-ites") are labeled "People / Clan". When a name has no data, a short AI blurb fills in
  (text-first, cached).
