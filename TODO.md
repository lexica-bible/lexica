# TODO

Open work only. Finished and scrapped items (with the gory details) are in [TODO_ARCHIVE.md](TODO_ARCHIVE.md).
Each item may end with a small `code:` pointer for Claude to find the right spot — you can skip those lines.

Consolidated 2026-07-01: the DONE/SHIPPED write-ups were moved to the archive + memory; this file now
holds genuinely-open work and parked ideas only.

---

## Open word-study / data issues (low priority, none gating)
- **~48 G1473 (ἐγώ) cells reading 3rd-person reflexives** ("himself/themselves/itself") with a blank
  lemma — by-design skips of the cautious G1473→G846 retag (it refuses to guess reflexives + no-morph
  cells). Consistent with the build. Future cleanup only. code: the g1473_gloss_retag fold in
  build_words_from_abp.py / lxx_align.
- **τοῦτο-paradigm mistags** — a handful of demonstrative forms (τοῦτο, ταῦτα, οὗτοι, τούτου, τούτων)
  carry the wrong Strong's (single-digit counts stranded under G1473/G3779/G846/G1438; the real number
  is G3778, 2,400+ rows). Surface-form collisions, low-impact — a small bidirectional retag when we get
  to it. code: the retag folds in build_words_from_abp.py / lxx_align.
- **Hebrew-OT word finder is NOT number-folded** (KNOWN GAP) — the singular/plural fold is live on
  ABP/KJV/BSB but NOT the `corpus=heb` discovery branch (it matches a token inside a multi-word gloss
  phrase, so the precomputed `*_norm` column doesn't fit). A real fold needs BOTH a normalized-token
  side-index in heb.db AND a looser `gloss LIKE` prefilter. Don't ship a half-fix (folds one direction,
  reintroduces the asymmetry). Hebrew search stays number-exact until both land. Memory
  `project_lexicon_number_fold`.

---

## Three-zone shell — remaining consumers
The shared frame (`Shell` + `RightStack` in `static/src/22-shell.jsx`) is done; Ask-corpus, Notes, Seam
index, and News right-rail all shipped on it 2026-07-01. Full record: memory `project_three_zone_shell`
+ `HANDOFF_corpus_shell.md`. Left to do:
- **News-on-mobile** (net-new, the LAST shell surface) — the News tab isn't reachable on a phone. First
  confirm the cause (missing from the mobile bottom nav vs a stubbed mobile branch), then make it render.
  code: static/src/84-news.jsx, 90-app.jsx, 20-shared-components.jsx
- **Study-on-mobile shell** — mobile Topics/Graphs/Seams still run the OLD single-column branch
  (`.study-view .study-mobile`), not the shell. Give them the shell mobile treatment (rail/inspect as
  sheets), same job as News-on-mobile. code: static/src/55-study.jsx
- **Study per-item inspect DETAIL** (deferred by design) — the Study tab is uniform master-detail now but
  the RIGHT inspect is ZoneEmpty everywhere. Wire it: Topics = clicked verse in context; Graphs = clicked
  claim/node's grounding; Seams = clicked fork's grounding. Each is net-new feature work.
  code: static/src/55-study.jsx (RightStack `push`)
- **PA data step for the Seam index** — run `python scripts/build_lexica_def.py --resplit --all --apply`
  on PA to write the new `divergence_type` + `lead_flip` (+ short `gloss`) into the stored forks (free, no
  model). Until then the Seams list shows but the type badges + Different-lead filter are blank.
- **Ask-corpus POLISH pass** (rail got a big build-out 2026-07-01/02 — per-answer selection, Key passages
  moved into the rail, ONE merged Words-in-scope list, bottom-pinned composer, contested badge via the
  served set; memory `project_three_zone_shell`). DONE 2026-07-02: empty-state hero raised + de-spinnered,
  single Inspect divider, rail dedupe/date-group/cap-10/confirm-Clear-all (display-only). STILL OPEN: the
  occurrence card's target word = the answer's PRIMARY key word (wrong-ish for a broad multi-word answer —
  should be the exact word in THAT verse); recreate the CSS parity gate with a WIDENED prop set (width,
  max-width, flex-basis, overflow-x/y — the old gate missed the News-width + scrollbar bugs). POSSIBLE
  polish: snippet clamp can hide the match (takes the first line, not a window centered on the highlighted
  word) — only if it proves common. code: static/src/52-ask-corpus.jsx, 50-corpus-results.jsx, styles.css
- **Dead seam CSS sweep** — after the uniform-shell rewrite, `.seam-row`/`.seam-inspect`/`.seam-insp-*`/
  `.seam-list` are unused (rows reuse `study-row`, list in the shared rail). Harmless, sweep when
  convenient. code: static/styles.css
- **News beast-arm badge** (authored follow-up) — a per-thread "which beast/arm" tag in the why-rail.
  Not built on purpose: the thread→arm map isn't 1:1 (several threads serve BOTH arms), so it's
  hand-authored content JP will sit with, then it drops into the why-section. code: views_news.py map,
  static/src/84-news.jsx
- **Owed post-deploy human check** — click-through of News / Word study / Library on desktop + phone
  (the mobile sheets are the one thing the parity gates can't run locally); confirm the News tab shows in
  the mobile bottom nav (admin) + the News inspect looks balanced without cramping the `.news-bar` row.
  (The Ask-corpus provenance rail was checked in Chrome 2026-07-01 — fine.)

**Copy-shortlist wrapper resolution** (SHIPPED 2026-07-01, two loose ends; memory `project_news_watch`):
1. Deploy the web app (reload) so the copy-to-face button + `POST /api/news/resolve` go live.
2. Archive backfill is draining — `resolve_backfill_all.py` chunked into `daily.sh` (~1000/night under
   Google's ~1,300 clamp), ~5,700 wrappers left, self-terminates (~a week). No action unless a stable
   failing remainder persists → then the PARKED `resolve_attempts`/`resolve_failed` marker.
3. Post-deploy check: News → Kept → Copy shortlist shows "Resolving…" then pastes clean article links,
   not `news.google.com/rss/...` wrappers.

**Copy/Export shortlist + card-link formats** (SHIPPED 2026-07-02; memory `project_news_watch`):
1. Needs a normal CODE deploy — the feed read now carries `i.summary` (fills the copy "description" +
   CSV description) AND `i.resolved_url` per face/member (makes the card/article CLICK open the real
   article instead of the Google wrapper). Both degrade safely without the deploy (blank desc / wrapper
   click that still redirects).
2. Post-deploy check: News → Kept → Copy shortlist (3 formats) + Export (Markdown / CSV) download; a card
   title click lands on the real outlet, not `news.google.com/rss/...`; date window label stays put
   across refresh ("Last 7d" doesn't creep to 8d); right inspect divider lines up with the navy header
   edge when a card is selected; single-source card reads "1 source" (no "· peaked"); the scoring lens
   now lives in the ⓘ popover, not on each card.

---

## Code health / cleanup
The big rework is finished (six phases + a security/code-health pass; memory `project_redesign` /
`project_architecture_rework`). Still open:
1. **Web-route test coverage.** CI auto-runs only the data-invariant tests; the endpoint snapshot harness
   (`snapshot_endpoints.py`) + browser click-through are MANUAL (run against a DB copy during dev), so web
   routes / click behavior aren't checked on every push. That's the main test gap if you ever want to
   close it. One stale golden to re-baseline on PA: `api__cross-references__Joh__3__16.json` with
   `--update` (field `kjv_text`→`text`, now BSB). code: scripts/snapshot_endpoints.py, tests/, .github/
2. **Shared AI "house style" voice snippet** — the last leftover of the prompt-unify item. xref, chapter
   summary, LSJ, etc. each carry their own wording. Build ONE core.py snippet with the VOICE only (plain
   language, short one-idea sentences, no jargon/moralizing); keep LENGTH split by MODEL — HARD
   sentence-counts on Haiku prompts, SOFT adaptive on Sonnet (Haiku overran the token ceiling on a maximal
   chapter). Do NOT convert the person/place `_PN_SYSTEM` hard cap to adaptive. Editing a prompt lazily
   refreshes that category's fingerprint cache (expected). code: core.py snippet; views_crossref.py,
   views_metav.py _PN_SYSTEM, views_summary.py, views_lsj.py prompts. Memory `project_ai_synthesis_quality`.

---

## Where we're behind vs other Bible apps (assessment — revisit later)
We play in the FREE serious-study niche (vs Blue Letter Bible, STEP, e-Sword, Bible Hub — NOT Logos or
YouVersion, which aren't the target). Honest gaps:
- **Fewer translations** — a handful (ABP/KJV/BSB + owner ESV/NIV) vs dozens. Cheap win: public-domain
  ASV/YLT/Darby/Geneva into the Compare picker (see "More texts" below).
- **No reading plans / devotionals / social** — deliberately not our target (chronological mode is the
  closest we have).
- **Reach / awareness is the REAL gap, not features.** One-person app on a small box; the feature set
  punches above that but almost nobody knows it exists. The missing piece is marketing, not code.

## Logos base-tier gaps — two real ones (saved, not being worked)
1. **Grammar search** — search the morph tags themselves ("every aorist participle of this verb"). We
   STORE the tags (~78% of ABP Greek, the Hebrew OT in full); what's missing is the search engine + UI.
   The single biggest thing between us and their base word-study feel. code: morph on words + heb_words.
2. **Dedicated people/places module + timelines** — we HAVE the metaV person/place cards + map, but not
   (a) a browsable "Factbook"-style hub (today cards only open on a word click) or (b) timelines. See "Map
   tab" below for the maps half. code: metav_* tables; memory project_metav_expansion.

---

## Word cards / lexicon — open items

- **Root / family word search — PARKED (needs a real stem field first).** Word study should be able to
  surface a whole family (θεός, ἄθεος, φιλόθεος, θεοσέβεια) by the theo- ROOT. Blocker: `lexicon` has no
  structured stem/root column — only `derivation` (free-text prose). Substring on translit fakes it and
  leaks (euthéōs/βαθέως match "theos" on a letter-accident — the exact reason the 2026-07-01 translit
  lookup was split into labeled Exact/Contains bands). Don't build on substring; build a real root field
  first. Record: memory `project_lexicon_search_overmatch`.

- **Structural / function-word cards — build inventory COMPLETE + LIVE** (εἰμί + prepositions + article +
  conjunctions + particles/negatives + the referent-resolution batch + the ἀνὰ μέσον idiom). Full record +
  the locked build rules: memory `project_structural_deictic_cards`. OPEN: live-case HIGHLIGHT for
  prepositions — light the case-row matching the object's case from morph (the table already shows; wire
  it with the verse live-pull). code: structural.py, views_lexica.py, static/src/20-shared-components.jsx

- **Pointer click-through** (follow-up, not blocking) — the ἵνα `contest_graph` breadcrumb and the
  dikaioō/Lexica-fork `graph_ref` are PLAIN TEXT, not click-to-open. Upgrade both together: thread an
  onOpenGraph callback 90-app → detail-panel → StructuralBody/LexicaFork that switches to the Study tab
  and opens the graph by id (the `studyPending`/`openEntry` plumbing exists for the metaV sidebar).
  code: static/src/90-app.jsx, 30-detail-panel.jsx, 20-shared-components.jsx

- **Lexica dictionary — verse-grounded word defs (Sonnet engine; LSJ display-only).** Pilot + full-build
  BATCH 1 are PUBLIC (~18 cards, `LEXICA_ADMIN_ONLY=False`); contested words hand-pinned; θεός/κύριος
  forked; the rare-word stress test is GREEN. Cutoff = occ ≥ 2 (~3,954 words), PARKED until JP calls the
  full build. Full record + the 3-tier ship-gate + the frame-leak pre-sort rule: memory
  `project_lexica_dictionary`. **NEXT = the batch-2 PRE-SORT / PIPELINE script** (scoped, not built): one
  driver sorts a G-number list into the 3 tiers, runs tiers 1-2 itself (gate-before-build), hands tier 3
  to JP; signals = freq + fork-membership + polysemy proxy + loaded-referent flag. Open sub-items:
  - Point `lexica_agreement.per_sense` at the new `_sense_spans` (still bold-only → a plain draw reads as
    a phantom sense-count wobble at batch scale).
  - Re-check the 80% / min-4 LXX-provenance cutoff at scale (tuned on 18 words).
  - Step 4 significance judge — voting sees that something VARIED, not whether it MATTERS (same blind spot
    as the citation gate, one layer up). Human eyes now; a model pass is unproven.
  - Verbs + Hebrew first-batches = separate tracks.
  - Small: the fork gate names a covenant-membership/NPP reading for dikaioō that `salvation_how` has no
    node for — add one via add_study_graph_salvation.py so the link lands.
  - **Coverage engine (piece A/B) SHIPPED 2026-07-02** (`lexica_coverage.py`; memory `project_lexica_dictionary`).
    Piece A collocation pre-check (token-level PMI, `PMI_MIN=4.0`, warn-only build hook) + piece B
    `coverage_audit` field populated on all 18 entries. Follow-ups: wire `coverage_audit` to the card UI (stored
    data only now); eyeball G166/aionios sense 4 (flagged thin); optional "phrases-not-senses" filter for the
    advisory uncited-collocation lists (theos/kyrios run long); piece A could FORCE a missed collocation into
    the draw at build (warn-only today). Piece C (stratified sampling) DEFERRED — first evidence logged:
    huios+anthrōpos OT-generic vs NT-title conflation.
  (Manual CONTENT edits — batch-2 G2316 sense 4 + G5207 sense 5/believers, and batch-3 G5207 sense 6
   "Son of Man" idiom + G2316 Psa 82 into senses 3/4 — all SHIPPED + LIVE; audit A1/C3 + the θεός metaV fix
   too. Archived. See TODO_ARCHIVE + memory `project_lexica_dictionary`.)
  code: scripts/build_lexica_def.py (imports contested_register), fix_lexica_raw.py, lexica_agreement.py, views_lexica.py

- **Definition-engine audit — items PARKED by JP's scope call (2026-07-01).** Batch 1 (register extraction,
  blocking citation gate, G5485 alias, serve-time fork backstop, +7 gloss overrides) shipped — see memory
  `project_lexica_dictionary`. Not fixed, deliberately queued:
  - **Ask-corpus LSJ / strongs_def leakage (audit A3/A4)** — the ONE path where LSJ text + Strong's interpretive
    paraphrase reach output: `_lsj_concept_lookup` feeds LSJ semantic snippets into the Haiku SQL-gen prompt
    (steers key_strongs), and the Ask-corpus rail renders `target.definition` = `strongs_def` unlabeled
    (the field the word card was moved OFF of, per views_lsj.py:297). Fold into the Corpus right-rail work.
  - **Spelled-out / non-canonical book-name gate (audit B1) — MOSTLY CLOSED 2026-07-02.** A citation with a
    2-letter abbrev ("Ps"/"Jn"/"Mt") or a spelled-out name ("Matthew 5:17") escaped `_REF_RE` (only catches
    numbered books + `Cap+2low`), so it never reached the gate — silent unverified ship (found as a real "Ps 2:7"
    in G5207). `noncanon_book_refs()` now HARD-REJECTS these at write time (canonical codes only). Remaining gap
    (minor): a spelled-out name is rejected, not auto-recovered into its valid code — must be hand-fixed. commit fb1c461.
  - **pinned_core presentation labeling (audit B4)** — the hand-authored pinned core leads the Meaning view
    under the "✓ verified" badge with no marker distinguishing it from engine output; provenance is
    "verse-grounded · LEXICA" unconditionally. Presentation call, fold into the card review.
  code: ai.py (_lsj_concept_lookup consumer), build_lexica_def.py (_REF_RE), static/src/20-shared-components.jsx

- **LSJ "Lexica" overrides** — the blurb is a Haiku "definition" prompt + per-word hand-written overrides
  for loaded lemmas (6 seeded). Memory `project_lsj_overrides`. OPEN: the contested words (αἰώνιος,
  δικαιόω) are now handled by the Lexica dictionary's fairness fork, NOT a hand-written asserting override
  — HOLD δικαιόω, don't hand-write. For Strong's-fallback loaded words (no LSJ entry → raw Strong's def):
  keep Strong's for now, curate later; deferred preference = show nothing rather than a duplicate of the
  headword gloss. code: views_lsj.py _LSJ_OVERRIDES.

- **Two-tier word entry — Summary = the gloss, Expanded = the EVIDENCE** (idea, parked). Governing rule:
  the summary asserts the meaning; the expanded tier only earns its place if it shows the reader something
  they can CHECK. Expanded = (1) render breakdown as PERCENTAGES of the word's own usage with rare senses
  linked to their verses (we own this data — the distribution rail); (2) one worked-example verse per
  sense, inline; (3) a one-line provenance "seam" on the LOADED words only (where the common English gloss
  came from + why we didn't use it — distinct from the auto-derived LXX-provenance flag already shipped).
  HARD don'ts (all rebuild the systematic-theology web the method rejects): NO etymology as a headline, NO
  "related theological concepts" cross-refs, NO our-own commentary on what the word "really means." Goes
  mostly in Word study; scope any expanded section to `.wd` so it can't leak into the LOCKED Library word
  card. code: views_lsj.py; static/src/80-lexicon.jsx + 30-detail-panel.jsx.

- **"Learn" section — plain-language glossary / FAQ** (idea, parked). The audience needs no Greek/Hebrew
  training, so a reader who hits H7307 vs H7308, a dotted number, a homograph suffix, or four per-source
  counts has no in-app way to make sense of it. A text-first FAQ covering: Strong's numbers (G vs H); the
  texts + why counts differ; Hebrew vs Aramaic; letter-suffix homographs / dot = ABP added words; brackets
  + italics; Word study vs Ask the corpus. Best server-rendered like `/read` so Google indexes "what is a
  Strong's number." Mostly WRITING, not code. code: views_seo.py + templates/seo/, or an About sub-page.

- **"Loaded terms" word-study SERIES — authored content layer** (idea, parked). A repeatable series, each
  entry on a fixed SEVEN-SLOT skeleton: loaded English term + etymology → underlying lexeme(s)+Strong's →
  attested range → THE SEAM (where the loading entered — the heart of it) → symmetric audit of the rival
  gloss → case-by-case usage → most defensible rendering. ~6 entries bankable (charis, baptizō, metanoia,
  ekklesia, hamartia + propitiation). THE FORK to settle first: a standalone **Studies** section vs a
  "featured study" overlay inside Word study. Reuse study.db (json body + type + status) vs new tables.
  code: study.db / views_study.py + static/src/55-study.jsx, or new word_study tables.

---

## Ask the corpus — open items
Retrieval is Strong's-keyed SQL (occurrence lists can't be wrong); the leak was only in the prose, now
heavily guarded. Full record: memory `project_ai_search_architecture` + `project_ai_synthesis_quality`.
- **#4 parallelize the cognate + Hebrew DB loops** (follow-up, not started) — read-only independent loops
  run one-at-a-time; running them concurrently claws back seconds on MULTI-head queries only. Needs an
  identical-output before/after diff. Don't touch the model-written single SQL. code: ai.py cognate loop +
  Hebrew supplement loop.
- **Lexical-texture panel follow-ups** (the panel itself is LIVE; memory `project_corpus_enrichment`):
  (1) LXX seam range-preservation — does the Greek keep esh's range at the ~8% divergence? Doubles as the
  short-root Hebrew family fallback. (2) Rebuild bdb `lemma_plain` — re-run `scripts/add_lemma_plain.py` so
  the Hebrew word-study exact-match fast-path goes live again (guarded today, just slower). Memory
  `project_lexicon_search_overmatch`.
- **AI curation hard-tune / answer-shape redesign** — current primary/see-all + inline links is adequate,
  not the end state. Sub-items: the thread's evidence-verse list reads spammy (collapse/summarize/cap);
  label thematic verses so a wordless cross-ref (Rom 14:5 on a Sabbath query) doesn't read like an
  occurrence — DON'T drop them (Gen 1:26 for divine council relies on the same path); broad/thematic-topic
  answers are thin (retrieval is word-based — the bigger answer-shape work). code: ai.py
  _curate_primary_verses + _CURATION_SYSTEM; static/src/52-ask-corpus.jsx, 50-corpus-results.jsx.
- **Small residuals (only if they bug the user):** cross-ref weighting picks the general hub verse not the
  query-specific one (Sonnet still names the specific anchor, so low priority); residual framing lean; LSJ
  blurb was never given the citation after-check (low risk — add only if a bad cite shows up).
- **Word-study leftovers:** the English-word finder's "All" view still finds/counts Hebrew via KJV (heb.db
  only kicks in under the HEB filter) — switch All's Hebrew discovery/count to heb.db if the count matters;
  collect the user's held "small tweaks" to the new Word-study UI. The "All" merged ABP/KJV toggle stays
  PARKED (double-counts the shared NT — needs a counting rule first).
- **Word-study search LABEL — verb+tail follow-up** (low priority) — a verb followed by a NON-italic tail
  particle labels on the tail ("went forth"→forth). The italic-skip can't catch it — needs a POS rule
  (label a verb-slot on the verb via greek_pos/morph). Low value: the tail still carries the verb's sense.
  code: scripts/parse_abp.py _head_word.

---

## AI reference depth — public-domain works (idea)
Feed PD reference works into the synthesis engine the way we do LSJ/BDB. Best picks:
- **Trench (NT synonyms) + Girdlestone (OT synonyms)** — the STANDOUT. Grounds the synonym answers the AI
  was improvising; authoritative, zero license cost. (Same-root GREEK cognates are already wired in; the
  value HERE is SEMANTIC synonyms + the HEBREW side, which has no etymology to walk.)
- Thayer's, Vine's, Strong's own defs, Gesenius — more lexicon depth, easy adds.
- PD COMMENTARIES (Henry, Barnes, Gill, Clarke, JFB, Pulpit) — CAUTION: a commentary layer is IMPORTED
  interpretation, exactly what the Berean text-first rule keeps OUT. Only worth doing walled-off + clearly
  labeled "tradition, not the text"; never let it bleed into the neutral answers.
- LICENSE caution (we've been bitten): some old works have free TEXT wrapped in a not-free database
  license. Grab original scans / known-free digitizations (CCEL, pre-1929 IA printings), not a repackaging.
  code: synthesis pattern in views_lsj.py / ai.py; a loader + side table per source.

---

## Non-canonical texts — open scraps
The library is built + live (Apocrypha, Pseudepigrapha, Testaments — English; 14 Apostolic Fathers with
Greek interlinear). Full record: memory `project_noncanonical_texts`. Open:
- **Possible NEXT books** (not started): Book of Jasher (Moses Samuel 1840 — beware the pseudo-Jasher);
  4 Baruch; Apocalypse of Zephaniah; Joseph and Aseneth.
- **Wire non-canon into the Lexicon / Search tabs.** The non-canon word panel's "In the [book]" count +
  LXX cross-link were HIDDEN 2026-06-11 because they dead-ended — the Lexicon tabs only know the Bible
  corpus. Teach those tabs about the `<book>_words` tables, once, generically as a "non-canonical corpus"
  option (not per book). code: views_lexicon.py + 80-lexicon.jsx.
- **KNOWN GAP — Hebrew/Aramaic interlinear for a non-canonical text.** The extra-text interlinear is
  hard-wired to Greek (joins lexicon on a G-number; word click routes to LSJ). English-only loads are
  language-agnostic, so this only matters for a word-by-word original (e.g. Ben Sira's Hebrew): would need
  a BDB/H-number join in `/api/extra` + right-to-left chips. Not urgent — no Hebrew non-canon is queued.

---

## Notes — open follow-ups
Notes/highlights/bookmarks + opt-in accounts (email/Google) are DONE + LIVE; memory
`project_notes_highlights`. Open:
- **Word-level highlights in KJV** (optional) — KJV still anchors whole-verse; kjv_words has positions, so
  the BSB `renderBsbVerse` per-word pattern could close it. (Compare view intentionally paints whole-verse
  in every column — exact-word paint there would need the column's own translation id threaded into
  `hiForWord`.)
- **Apple sign-in** — only if wanted (needs a paid Apple Developer account; heavier than Google).
- **Email campaigns / reading-plan mailings** — the original "reach" payoff, now that mail is proven.

## Ko-fi / Berean upgrades (manual for now)
Donations are LIVE via Ko-fi; becoming a Berean is a MANUAL admin grant (subscriber emails `bereans@` →
admin flips the role). Memory `project_payments_donations`. Open:
- USER-SIDE: set up the monthly **"Berean" membership tier** on Ko-fi + put the claim instructions in its
  welcome message (the cap CTA points people there).
- OPTIONAL: a Ko-fi webhook → auto-set the berean role (no email-claim step). Berean daily cap stays 10.
  code: views_notes.py (role grant / AI_DAILY_LIMITS); a new Ko-fi webhook endpoint if automated.

---

## Ideas / someday (nothing committed — grab whichever appeals)

**Reader / layout**
- **Word detail as a floating card** — instead of the fixed right sidebar, the lexicon info pops up next
  to the clicked word. code: detail panel in 90-app.jsx.
- **Collapsing toolbar** — shrink the desktop lib-bar to one compact pill that expands on reach, giving
  the text more room. code: lib-bar in 60-library.jsx + styles.css.
- **Chronological timeline scrubber** — a draggable era timeline across the top of chronological reading
  mode for jumping around the sequence. code: chronological reading-mode UI.
- **One smart search box** — merge the Word-study and Ask-corpus inputs into a single field that detects
  what you typed (Strong's vs Greek vs plain question) and routes it.

**Bigger features**
- **Map tab** — biblical geography as its own tab: follow the current chapter's places; search a place +
  pin every verse; or a free-explore world map where clicking a city opens the metaV sidebar. Coordinates
  + the map library are already in place, so it's smaller than it looks.
- **Topic browser** — browse by concept (Atonement, Covenant, Resurrection…) as an alternative to AI
  search. Use an off-the-shelf topic list for the category NAMES only; generate the verses + summaries
  ourselves, Berean-style. Could ride the Study tab.
- **Broader / meaning-based passage search** — find verses ABOUT a concept even when they don't use the
  word, over the bible text itself (staying text-first, no imported library). Would need a concept index.
- **Let published study topics shape AI-search answers — divine council is the test case.** AI search
  carries a hardcoded divine-council override (`_DIVINE_COUNCIL_VERSES` / `_DIVINE_COUNCIL_RE` /
  `dc_strongs` in ai.py) AND a hand-authored "Divine Council" study topic with the same verses. The idea:
  have AI search notice a question matching a published topic, pull that topic's verses in as primary,
  prove it matches today's behavior, then DELETE the one-off — it generalizes to any authored topic. The
  study would need trigger phrases + the word chips. GUARDRAIL: only PUBLISHED text-first TOPICS may feed
  an answer, never denominations/arguments (they take sides). Saved answers must key on the topic's verse
  list so editing the study refreshes them. code: ai.py one-off; add_study_topic.py; views_study.py.
- **Study graphs — remaining bits** (graphs are admin-only). Mobile graph = narrate a traversal (argument
  STEPS vertically), NOT a shrunk 2D chart — hardest thing to preserve is the CONTESTED edges (carry
  "contested" as a colored TAG, not fine dashes, or the map quietly becomes a verdict machine). Also: a
  per-study foundational-words / lexeme strip (the baptizō "medium-neutral" insight was trimmed on the
  understanding it belongs there — specced, not built); a Strong's deep-link from a graph lexeme node
  (today boxes only deep-link verse refs); drop the place "Sin (1)/(2)" from `_COMMON`. code: argmap.py +
  views_study.py + static/src/55-study.jsx; memory project_study_modules.

**More texts + audio**
- **Textus Receptus Greek NT** — a second NT text beside ABP; same Strong's numbering, so it plugs in
  easily, and showing where two Greek texts differ is genuinely rare + useful.
- **More English translations** (ASV, YLT, Darby, Geneva) — public domain; slot into the Compare picker as
  new toggles + their own loader/db (like BSB).
- **Parsed Greek OT as a 2nd parallel text** (parked) — a CATSS-lineage Rahlfs LXX (Eliran Wong's
  LXX-Rahlfs-1935 is most turnkey — surface+lemma+morph+SBL translit paired) would be its OWN parallel
  Greek OT alongside ABP, NOT a patch to ABP's surface line. LICENSE FLAG: CATSS/CCAT is NOT MIT
  (user-declaration requirement) — read the downstream terms before shipping in a donation-taking app.
- **Fuller Greek morphology** — extend the ~78% ABP morph (CATSS for the LXX OT, macula-greek for the NT).
  The ABP-native fill was INVESTIGATED + SCRAPPED (memory `project_abp_morph_gap`) — the only ABP-keyed
  source is a paid PDF, not worth it. code: morph column on words.
- **Dramatized KJV audio** (multi-voice FCBH — rides the same pending Bible Brain key as ESV) +
  **verse-by-verse karaoke** (needs per-verse timing — parked). code: views_bsb/views_esv audio.
- **Extra-biblical texts referenced in scripture** (1 Enoch already in; Dead Sea Scrolls variants) as a
  separate section, never mixed into canon.

**Dead Sea Scrolls — wanted, the hardest one (why it's not done)**
- No public-domain English exists (Vermes / Wise-Abegg-Cook / García Martínez are all modern + copyrighted;
  what's free is photos + academic transcriptions, not a ready-to-read text).
- The scrolls are mostly broken Hebrew/Aramaic fragments — needs the H-number / RTL plumbing flagged above.
- The realistic angle isn't "another book to read" — it's a COMPARE view: the Great Isaiah Scroll (1QIsaa)
  is complete + famous, and its value is showing where it differs from the Masoretic text. A side-by-side
  "variants vs the MT" feature — bigger and different from the apocrypha plumbing. Best first step if/when.
