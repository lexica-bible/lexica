# TODO

Open work only. Finished and scrapped items (with the gory details) are in [TODO_ARCHIVE.md](TODO_ARCHIVE.md).
Each item may end with a small `code:` pointer for Claude to find the right spot — you can skip those lines.

Consolidated 2026-07-01: the DONE/SHIPPED write-ups were moved to the archive + memory; this file now
holds genuinely-open work and parked ideas only.

---

## ABP corpus certification audit — TIER A CERTIFIED END TO END (full record `AUDIT_abp_certification.md` + memory `project_abp_certification`)
Sessions 1-3 DONE 2026-07-03/04. Live bible.db IS pinned source (74-file hash manifest) + faithful parser
(re-parse+diff certified) + versioned correction table (`abp_corrections`, 18 rows) + invariant suite green
(`cert_invariants.py`, 7/7, each with a proof-of-fire control). Session 3 rebuilt+swapped live (old file
retained `bible_pre_certswap_20260704.db`), erasing the 11-verse residue; dead `_sort_brackets` deleted.
Session 4 DONE: Cushi person-as-place binding floored (see archive), check 7 added, render count reconciled.
Session 5 DONE: TIPNR pinned (manifest 75, binder proven byte-identical); nightly backup damage-check +
durable self-test; L2/L10 correction rows landed (source-attested via the official ABP app, table 8->16,
suite green at pin 16); two-source seam doc written (`AUDIT_entity_seam.md`).
Session 6 DONE 2026-07-04: 97-card section-label defect FIXED + live (`parse_tipnr` types each entity from
its OWN row, not the block header — 8 places flipped person→place, 3 EXCLUDED entities stopped binding,
net −13 render, loud-fail raise on unknown type under a mixed header); mirror census re-run on clean labels
(P1=0, valid); check 7 hardened to BOTH directions (mirror leg + control); L5 discrepancy explained
(closure a, no drift). Cert 7/7 green, pin 16. Full record `AUDIT_entity_seam.md` + `HANDOFF_session7.md`.
Session 7 DONE 2026-07-04: **L5 CLOSED** — all 9 candidates read vs the ABP app (JP verse-pasted): 8 clean
(αὐτός/ἐγώ/οὕτως legitimately render "this/these"), 1 real mistag fixed — Dan 4:33 pos 1 αὐτῇ (αὐτός)
mis-numbered as ἐγώ, corrected G1473→G846 (decided by dative agreement with ὥρᾳ + αυτ- spelling, not a
breathing eyeball; escaped Path C = blank-lemma unanchored, Daniel-4 OG/Theod. divergence). Two `abp_corrections`
rows added via the L2/L10 door (table 16→18), applied live, **pin bumped 16→18, cert 7/7 green**. Luke 23:38
carry-forward closed (language reference = binder artifact, no row). Full record in `AUDIT_abp_certification.md`
L5 batch-two entry.
Carry-forwards:
**Session 8 DONE 2026-07-04: Door 1 (Path-C census) CLOSED + Door 2 (import_tipnr twin) FIXED+proven.
Both queued for one Session-9 rebuild. Full handoff = `HANDOFF_cert_session9.md`.**
Carry-forwards (all three = ONE Session-9 HIGH-seat rebuild; three per-column-attributed diffs):
- **Path-C G1473 residue — CENSUSED + CLOSED (Session 8, ledger L12).** Dan 4:33 is NOT a lone stray:
  Daniel holds **170** source-attested pronoun mistags (αὐτός/σύ/ὑμεῖς/ἡμεῖς still numbered 1473), read off
  `abp_surface` (ABP's own Greek — refines the old "no our-data detector" claim to BLANK-form slots only).
  Corpus-wide raw ~3,577 is **VOID as a count** — a MIX of real pronoun mistags + subject/possessive FOLD
  slots (blank-english, correctly-placed but mis-numbered; NOT `abp_surface` misalignment — placement is
  RELIABLE), proportions unknown until the per-slot fix pass.
  → FIX QUEUED (Session 9): Path C `abp_surface` fallback (form→Strong's table for the closed pronoun set)
  WITH a per-slot form/english sanity gate (skip+log where they don't match; blank-form slots stay app reads).
- **import_tipnr.py twin bug — FIXED + dry-run-proven (Session 8, commit 96bb662), NOT yet applied.**
  Ported entity_resolution's col-8-own-type fix into `import_tipnr.parse_tipnr`; the **10** mixed-block
  places (Beth-gader/Eshtemoa/Etam/Gedor/Gibeon/Ir-nahash/Keilah/Shechem/Tekoa/Zanoah) flip person→place,
  independently pinned + mirror-clean + raise both ways (`scripts/dryrun_tipnr_typefix.py`). The `tipnr`
  re-import is the Session-9 rebuild step; pre-registered Door-2 delta = exactly those 10 type changes.
- **Certify the OTHER 7 redistribution passes (Door 3 — diagnosis OPEN, opens Session 9 with a seam).**
  L9 certified `_split_compounds` ONLY. Still uncertified: `_split_numbered`, `_redistribute_pronoun_compounds`,
  `_fix_backwards_pairing`, `_split_pn_article_lump`, `_funcword_noun_relocate`, `_lord_subject_split`,
  `_lord_oath_fix`. **Seam banked:** the fold slots ARE subject-pass output — 2 known-positives Num 20:9 pos 2
  + 1Sa 18:6 pos 8; any Door-3 census detector must fire on those before its zero is trusted. Same
  census+control approach as L9.
- **Stump filter leak** (noted, low priority): `lint_split_wrong_slot.py`'s stemmer stump filter misses
  sibling forms whose count is <3 (sid/com/rott). Didn't matter once recipient-scoping shrank the haystack;
  fix if the filter is reused at scale.

## Open word-study / data issues (low priority, none gating)
- **Place-map pin = interim plurality heuristic** (2026-07-05). The map on a place word card
  (`_pin_from_rows` in views_metav.py) picks the coordinate the MOST metav_places rows agree on when a
  name carries several referents (Lebanon = region + Mount Hermon + a Jerusalem structure). Safe direction:
  a wrong pin needs multiple rows agreeing on the wrong point; failure mode is no-pin, never a misplaced
  pin (Eden still declines). BUT it leans on coincidental exact-coordinate duplication — a name whose
  referents are all distinct points gets no pin forever, even though the bound TIPNR entity
  (`Lebanon@Deu.1.7`) already says which referent the verse means. Real fix = an entity-level join: TIPNR
  entity → the matching metav_places row, or OpenBibleInfo coordinates (per-referent IDs native). Folds
  into the queued MetaV↔TIPNR cross-link work (same join problem as the person panels, places edition).
  memory `project_metav_expansion` / `project_entity_resolution_rebuild`.
- **OpenBibleInfo place ingest — the real fix for bound-place maps** (logged 2026-07-05, not started).
  The entity→coordinate join (E) was PARKED because `metav_places` has no per-referent key: name+root
  can auto-link only the single-referent places. The place-link dry-run (`scripts/build_tipnr_metav_link.py`,
  read-only) proved it — of 361 place entities: 241 confident (187 unique-name / 42 by-area / 12
  coord-agree), **86 HAND-RESOLVE** (genuinely different places at different coords — Bethel, Aphek, Ramah;
  these are what users notice). Hand-curating 86 ancient sites risks a wrong pin (breaks the accuracy bar).
  **2026-07-05 — a cheaper fix than OpenBibleInfo surfaced.** The old blocker ("metav has no per-referent
  verse key") was WRONG: MetaV's `MainIndex.csv` (unloaded) tags every word with PlaceID + verse, so the
  same distill that built the PERSON link (see below) gives place→verse + place→Strong's — a MetaV-native
  per-referent key that likely solves the 86 with NO new external source and NO new licensing. **Try the
  MainIndex place distill FIRST;** fall back to ingesting **OpenBibleInfo** (openbible.info/geo, per-referent
  IDs + refs + confidence + coords; `/credits` licensing check BEFORE ingest) only if the MetaV key comes up
  short. Either shares the `tipnr_metav_link` table (kind='place'). Nothing is wrong today — the interim Eden
  guard keeps the 86 SAFE, they just decline the map. memory `project_metav_person_link` /
  `project_metav_expansion` / `project_entity_resolution_rebuild`.
- **MetaV person rich-card serving — DONE + LIVE 2026-07-05** (moved to TODO_ARCHIVE). Left three parked
  follow-ups below.
- **Nave's retirement (DECIDED, scoped; own task, after S9).** Remove Nave's: study.db name-topic data +
  the name-path sidebar section (`naveTopical` + `/api/study/for-name` wiring) + the `/credits` line if
  listed. Rationale: tradition-provenance topical curation (interpretive verdicts as headings); finding-aid
  superseded by corpus occurrence links; interpretive claims belong in argument graphs where labeled +
  stress-tested. **Topic-page ROUTE survival is a SEPARATE decision — don't delete the route reflexively.**
  memory `project_metav_person_link` + `project_study_modules`.
- **BSB entity-resolution coverage (own task/review — wrong-identity risk class).** Ephraimites/Num 2:18
  (BSB `bene-X` "sons of X" construct) reached only the H1121 (`ben`) dictionary card. First step: test
  Levites Neh 11:3 on BSB — fires People/Clan = binding is cross-translation, gap is the construct-phrase
  class (maybe kin to Psa 39:1 phrase-gloss, S9 charter); doesn't fire = entity cards ABP-only today,
  document + scope from there. memory `project_metav_person_link` / `project_entity_resolution_rebuild`.
- **Dan 1:6 trio — hand-resolve the alias-record residual.** Azariah/Hananiah/Mishael @Dan.1.6 all score
  0.00 (below_floor) because MetaV tags their Daniel verses to the Babylonian-name alias records (Shadrach/
  Meshach/Abednego), not the Hebrew-name records — a known-SAFE residual, not ambiguity. Diagnosis + hand-
  resolve steps are in `HANDOFF_metav_person_link.md`; pick the person_id + write it into the residual notes.
- **Badge / verification-token unification (design backlog).** Two families — provenance badges (metaV/
  TIPNR/"Matched to this verse") vs verification marks ("✓ N/N verified"); rule now in `docs/design.md`.
  Converge instances opportunistically, no sweep.
- **Phase-6: PN Greek surface-form backfill for interlinear mode** (deferred, not a bug). In the new
  interlinear reading mode (2026-07-04) proper nouns show their capitalized English name on the Greek line
  because ABP prints Φαραώ/Νεχαώ etc. but those forms were never ingested (no lexicon join for `*` PNs → no
  `abp_surface` row). Backfill `abp_surface.form` for PN tokens so the Greek line shows the real Greek; it
  slots into the `greekLineForWord` chain at step 1 (inflected) with ZERO UI change. Needs cert-style
  position-alignment verification when it runs. Full record: memory `project_reading_modes`.
- **~48 G1473 (ἐγώ) cells reading 3rd-person reflexives** ("himself/themselves/itself") with a blank
  lemma — by-design skips of the cautious G1473→G846 retag (it refuses to guess reflexives + no-morph
  cells). Consistent with the build. Future cleanup only. code: the g1473_gloss_retag fold in
  build_words_from_abp.py / lxx_align.
- **τοῦτο-paradigm mistags** — demonstrative forms wrongly tagged; the real number is G3778 (~3,401 rows).
  **ENUMERATED + CONFIRMED 2026-07-03 (read-only), retag still PARKED** — nothing in a definition batch
  depends on it (G846/G3778 are structural cards, not `lexica_def`). The **15 confirmed strays** (all
  τ-initial forms, unambiguous — certified by control `SELECT count(*) … G3778 AND form GLOB 'τούτ*'/'ταύτ*'`
  = 3401):
  - G1473 (11): Deu 6:25, Ezr 9:14, Hag 2:18, Eze 45:16, Jer 7:1, Jer 8:12, Jer 11:3, Jer 33:4, Jer 44:23, Mat 24:2, Luk 22:51
  - G3779 (2): Jos 11:16, Jer 5:23 · G846 (1): Jos 19:8 · G1438 (1): Rev 19:20
  The **9 null-form "this/these" candidates** under G1473/G3779/G846 (Dan 4:33, Eze 36:32, Mat 3:15, 1Ch 27:6,
  1Co 1:24, 2Ki 18:9/18:10/25:8, Ezr 7:6) are **RESOLVED — L5 closed Session 7** (read vs ABP app: 8 clean,
  Dan 4:33 fixed G1473→G846; see the cert section above). The ου-/αυ-initial forms (οὗτος/αὕτη) are excluded on
  purpose — `ουτ*` collides with οὕτως G3779, `αυτ*` with αὐτός G846.
  **MATCH THE STORED REALITY:** surface `form` is accent-only, no breathing, circumflex→tonos (τοῦτο→τούτο) —
  a bare `tout*`/`τουτ*` GLOB on translit/form MISSES the accent (the γῆ #18A bug class; a translit control
  returned 13 not 3401 until switched to `τούτ*`/`ταύτ*` on the form column). When run: dry-run → ~15-row
  write to G3778, same careful pattern as the αἰών fix. code: the retag folds in build_words_from_abp.py / lxx_align.
  - Other finds parked alongside (need the ABP source, not auto-strays): G1438 has αυτού / υμάς-form rows
    (a reflexive-fold class, separate from τοῦτο). Dead lead checked + dropped: blank-english is NOT a mistag
    signature under G1473 — only 8 of ~3,322 blanks are demonstrative; the rest are ordinary ἐγώ folded into
    the verb rendering. Form-match is the only reliable finder.
  - LESSON (banked): the translit accent bug here is the #18A (γῆ) diacritic class biting an AUDIT query —
    one more argument for the normalize-both-sides fix when the Ask-corpus right-rail work starts.
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
- **Ask-corpus MOBILE rail** (PARKED 2026-07-03, JP's call — next fresh checkpoint) — desktop rail is DONE,
  fixture-locked (`test_ac_word_groups.js` + `test_rstack_logic.js` + `test_rail_payload_contract.py`) + CI-gated,
  and confirmed by a live Chrome pass. Mobile still runs the OLD `.ac` layout (an `if (isMobile)` early return
  in AskCorpusView) — no Shell/RightStack, no provenance rail. Net-new (mobile never had it), so no parity gate.
  code: static/src/52-ask-corpus.jsx (the isMobile branch), 22-shell.jsx (mobile sheet mode).
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
- **Ask-corpus POLISH pass** (rail got a big build-out 2026-07-01/02 — per-answer selection, Key passages
  moved into the rail, ONE merged Words-in-scope list, bottom-pinned composer, contested badge via the
  served set; memory `project_three_zone_shell`). DONE 2026-07-02: empty-state hero raised + de-spinnered,
  single Inspect divider, rail dedupe/date-group/cap-10/confirm-Clear-all (display-only). STILL OPEN: the
  occurrence card's target word = the answer's PRIMARY key word (wrong-ish for a broad multi-word answer —
  should be the exact word in THAT verse); recreate the CSS parity gate with a WIDENED prop set (width,
  max-width, flex-basis, overflow-x/y — the old gate missed the News-width + scrollbar bugs). POSSIBLE
  polish: snippet clamp can hide the match (takes the first line, not a window centered on the highlighted
  word) — only if it proves common. code: static/src/52-ask-corpus.jsx, 50-corpus-results.jsx, styles.css
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

**Paywall-aware face selection + 🔒 badge** (SHIPPED 2026-07-02; memory `project_news_watch`):
1. Needs a normal CODE deploy (backend `_pick_face` penalty + `pw` per member; frontend badge).
2. Post-deploy spot-check (still OWED — no mixed cluster in the window at ship time): find a cluster
   with a paywalled outlet (WaPo/NYT/…) + a free/wire source, confirm the FREE one is the card face and
   the paywalled one shows 🔒 down in the inspect sources. Then switch presets windowed ↔ Max on that
   cluster and confirm the face stays non-paywalled in both. Unit tests cover the logic; this is the
   only human check left.

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
   close it. (The Joh 3:16 xref golden `kjv_text`→`text` re-baseline is DONE — committed b686073.)
   - **CI test list is an EXPLICIT set of filenames (ci.yml + pre-commit hook), NOT a `tests/*.py` glob.**
     So a bunch of real tests DON'T gate: the alias tests, `test_scope_detect`, `test_thread_skeleton`,
     `test_lexicon_lookup_bands`, `test_rail_payload_contract`, etc. Low urgency (they run locally + are
     stable), but if you want them enforced, add the filenames to both lists — or switch CI to a glob run
     (`for f in tests/test_*.py; do python "$f"; done`) once every file is import-clean from repo root.
   code: scripts/snapshot_endpoints.py, tests/, .github/
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

- **BDB as Hebrew LSJ-analog (IDEA — the app has no real BDB today; see the Licensing section).** Load
  OpenScriptures BDB (PD, 1906), display-only + Summary/Full-entry tabs matching the LSJ pattern. Synth
  pass = compression of BDB per entry (~8.6k entries): compress/drop cognate front-matter, slice per
  H-number NOT per root article (BDB nests derivatives under roots — whole-article input bleeds siblings).
  Summaries carry a BDB provenance tag, NEVER LEXICA. Independent of the Greek rollout queue. Would slot
  in as the Hebrew counterpart to LSJ (the current `bdb` table is Strong's Hebrew, not real BDB).

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

- **Word-study card: numbering-crosswalk (`alias_note`) header badge** (follow-up, not blocking) — the
  Word-study card now renders the shared Lexica body (2026-07-03, fb36ac8) but does NOT show the standard↔ABP
  Strong's-number crosswalk badge the Library card shows in its header. The data is free on the same
  `/api/lexica` fetch (`d.alias_note`); only the header badge markup/placement is missing (scoped out to
  avoid creep). Match Library's `detail-strong-alias` markup. code: static/src/80-lexicon.jsx.

- **Pointer click-through** (follow-up, not blocking) — the ἵνα `contest_graph` breadcrumb and the
  dikaioō/Lexica-fork `graph_ref` are PLAIN TEXT, not click-to-open. Upgrade both together: thread an
  onOpenGraph callback 90-app → detail-panel → StructuralBody/LexicaFork that switches to the Study tab
  and opens the graph by id (the `studyPending`/`openEntry` plumbing exists for the metaV sidebar).
  code: static/src/90-app.jsx, 30-detail-panel.jsx, 20-shared-components.jsx

- **Lexica dictionary — verse-grounded word defs (Sonnet engine; LSJ display-only).** Pilot + full-build
  BATCH 1 are PUBLIC (~18 cards, `LEXICA_ADMIN_ONLY=False`); contested words hand-pinned; θεός/κύριος
  forked; the rare-word stress test is GREEN. **FREQUENCY ROLLOUT STARTED — its own BATCH ONE DONE + LIVE
  2026-07-03** (26 calibration words: top-20 content + 6 extension; ran as a checkpointed apply loop, not
  the pipeline driver). Cutoff = occ ≥ 2 (~3,954 words). Full record + the 3-tier ship-gate + frame-leak
  pre-sort rule: memory `project_lexica_dictionary`; **Batch One lessons + calibration numbers + the full
  batch-two prep list = `AUDIT_lexica_rollout.md`.** **DRAW CACHE (#1) DONE + LIVE 2026-07-03 (commit 484e226):**
  `--dry-run` saves the reviewed draw to `~/bible-db/draws/G####.json`, `--apply` ships it byte-for-byte with no
  model call (validity = hash of the full model input; stale→redraw, edited→hard refuse; `--require-cache` default
  under `--all`); kills the reviewed≠shipped class (πρόσωπον/δίδωμι/πατήρ). Tests + E2E-proven on G25. Remaining
  batch-two headline items: the **PRE-SORT / PIPELINE driver** (scoped, not built — one driver sorts a G-number
  list into the 3 tiers, runs 1-2 gate-before-build, hands 3 to JP; signals = freq + fork-membership +
  polysemy proxy + loaded-referent); **sampling rate** (100% eyeball register/loaded + SENSE STRUCTURE,
  ~1-in-5 rest); **structural backfill** (οὕτω G3779, ἕως G2193, ἰδού G2400, εἷς G1520 + the 8 oblique
  pronouns); **ἅγιον G39 gloss check** before build; ranker checks stamps upfront; ai.py↔build `_norm_book`
  cross-comments (bare "Jud" disagrees by design). (Batch One register/adjudication calls all ruled
  2026-07-03: πατήρ ships the 3-sense draw; υἱός + πατήρ no fork — see `AUDIT_lexica_rollout.md`.) Open sub-items:
  - Point `lexica_agreement.per_sense` at the new `_sense_spans` (still bold-only → a plain draw reads as
    a phantom sense-count wobble at batch scale).
  - Re-check the 80% / min-4 LXX-provenance cutoff at scale (tuned on 18 words).
  - Step 4 significance judge — voting sees that something VARIED, not whether it MATTERS (same blind spot
    as the citation gate, one layer up). Human eyes now; a model pass is unproven.
  - Verbs + Hebrew first-batches = separate tracks.
  - **Seam next-stage ("Build A") — feed design undecided.** Today's pipeline is hand-authored register →
    engine attaches forks → seams auto-display (so the shipped browse IS harvested, but its upstream is
    hand-curated — both, not either). Open question: does anything BESIDES a hand-forked word ever propose a
    seam? i.e. does engine output (freight flags, thin contested senses) generate seam CANDIDATES into a
    triage queue (harvest + Keep/Dismiss curation), or does the register stay the only gate for full forks?
    JP rules before any build. Batch One produced the first test cases either way (freight flags on plain
    words — impute, hearken/heed; λόγος sense 5 thin; the υἱός "looks like a fork, isn't one" ruling).
  - Small: the fork gate names a covenant-membership/NPP reading for dikaioō that `salvation_how` has no
    node for — add one via add_study_graph_salvation.py so the link lands.
  - **Coverage engine (piece A/B) SHIPPED 2026-07-02** (`lexica_coverage.py`; memory `project_lexica_dictionary`).
    Piece A collocation pre-check (token-level PMI, `PMI_MIN=4.0`, warn-only build hook) + piece B
    `coverage_audit` field populated on all built entries (38, via the 2026-07-03 `--resplit --all`).
    **FLAG GATE shipped 2026-07-03** (commit 967ce57; `AUDIT_lexica_rollout.md` #7): the "phrases-not-senses"
    filter for the uncited-collocation lists is DONE — the advisory flag now fires only at PMI ≥ 5.0 + a
    neighbor stoplist (οὕτω/ὅσος) + report-time mutual dedup; a share cap was tried and dropped (0 drops on
    frequent words, inverts on the rare tail). 163→73 flags across the 26; `scripts/audit_lexica_flags.py`
    inspects it. Remaining follow-ups: wire `coverage_audit` to the card UI (stored data only now); eyeball
    G166/aionios sense 4 (flagged thin); piece A could FORCE a missed collocation into the draw at build
    (warn-only today). Piece C (stratified sampling) DEFERRED — first evidence logged: huios+anthrōpos
    OT-generic vs NT-title conflation.
  (Manual CONTENT edits — batch-2 G2316 sense 4 + G5207 sense 5/believers, and batch-3 G5207 sense 6
   "Son of Man" idiom + G2316 Psa 82 into senses 3/4 — all SHIPPED + LIVE; audit A1/C3 + the θεός metaV fix
   too. Archived. See TODO_ARCHIVE + memory `project_lexica_dictionary`.)
  code: scripts/build_lexica_def.py (imports contested_register), fix_lexica_raw.py, lexica_agreement.py, views_lexica.py

- **Verse-aware gloss-note flag on word cards (design-scoping first, NO build — parked; draw cache is now done, so unblocked whenever JP wants it; not batch-two-blocking).**
  JP's idea: when a reader opens a word card FROM a specific verse in the interlinear, and that entry's
  gloss_note cites that verse, surface the note at the TOP of the card. Example: tap δίδωμι at 1Sa 22:15 →
  card leads with the impute-freight note because that verse is one of its cited occurrences. Static Library
  card view UNCHANGED — this is interlinear-entry context only. Scope in order:
  1. **Structured-refs prerequisite.** gloss_notes is stored as one prose blob; the citation catcher
     (`cited_refs`/`_REF_RE` in build_lexica_def.py) already pulls `(book,ch,vs)` from any prose (sense_provenance
     does it per-sense). Determine: is per-NOTE catch reliable off the stored blob, or does the build need a
     structured `verses:[]` field per gloss_note? If the latter → new field → JP checkpoint BEFORE anything lands.
     Also determine whether the 26 live entries can be back-parsed or need a resplit-style pass.
  2. **Precision rule.** Flag fires ONLY on exact verse match to a note's citations — never on every occurrence
     of the word. A wrong-verse flag is worse than no flag.
  3. **Design-doctrine ruling for JP (one-pill rule / emphasis budget).** Candidate: a subordinate text line at
     the card top, no new pill, no container, linking down to the note. JP rules on the visual form before build.
  4. **UI-copy principle (stated).** Flag PRESENT = a known note exists; flag ABSENT = no claim. Gloss notes are
     EXCEPTION reports over a ~40-verse sample, so absence must NEVER read as "verified clean."
  5. **Adjacency.** Relationship to the parked word-study-card provenance feature (both surface an entry's
     self-knowledge at point of reading). Scope shared card-header mechanism vs independent; don't merge without
     JP's call.
  Boundaries: scoping doc only — no schema, no UI, no build until JP reviews. Prereq facts already checked:
  gloss_notes only fires where a gloss narrows/loads/diverges, so most verses of a word carry no note (flag is
  silent by design — reinforces principle 4). code: build_lexica_def.py (`split_definition`/`cited_refs`),
  views_lexica.py (`/api/lexica`), 20-shared-components.jsx (`LexicaBody`), 30-detail-panel.jsx (fetch path).

- **Definition-engine audit — items PARKED by JP's scope call (2026-07-01).** Batch 1 (register extraction,
  blocking citation gate, G5485 alias, serve-time fork backstop, +7 gloss overrides) shipped — see memory
  `project_lexica_dictionary`. Not fixed, deliberately queued:
  - **Ask-corpus LSJ / strongs_def leakage (audit A3/A4)** — the ONE path where LSJ text + Strong's interpretive
    paraphrase reach output: `_lsj_concept_lookup` feeds LSJ semantic snippets into the Haiku SQL-gen prompt
    (steers key_strongs), and the Ask-corpus rail renders `target.definition` = `strongs_def` unlabeled
    (the field the word card was moved OFF of, per views_lsj.py:297). Fold into the Corpus right-rail work.
  - **pinned_core presentation labeling (audit B4)** — the hand-authored pinned core leads the Meaning view
    under the "✓ verified" badge with no marker distinguishing it from engine output; provenance is
    "verse-grounded · LEXICA" unconditionally. Presentation call, fold into the card review.
  - **Vocabulary watchlist lint (advisory, definition engine)** — a read-only lint that flags post-biblical
    philosophical/theological vocabulary in `lexica_def` prose. Watchlist SEED: moral, ethical, transcendent,
    ontological, person/personhood (of God/spirit), Trinity, unmerited, sacrament, ordinance, hypostasis.
    ADVISORY report, NOT a write-blocker — same spirit as the two-bucket citation miss log. Scoped 2026-07-02
    alongside the G2316 "moral authority" fix. (The corpus-search side got a prompt-rule guard in
    `_CURATION_SYSTEM`; this is the parallel lint for the frozen definitions.)
  - **One-time watchlist sweep of frozen definitions** — run the vocabulary watchlist read-only across ALL
    existing `lexica_def` prose and report hits for JP review. "Moral authority" sailed through every
    structural guard, so there may be more already frozen in. DEPENDS on the watchlist above existing — can
    be that same script's first run.
  - **VERSE_PROMPT vocabulary rule (definition engine)** — add the same corpus-vocabulary rule into
    `VERSE_PROMPT` (the build-time prompt) so freshly-generated definitions avoid the post-biblical category
    terms at the source, not just on edit. QUEUED behind the next controlled re-prove cycle (psychē-drift
    precedent — a prompt change re-proves against a frozen baseline before shipping); explicitly NOT a
    one-off edit.
  code: ai.py (_lsj_concept_lookup consumer), build_lexica_def.py (_REF_RE, VERSE_PROMPT), static/src/20-shared-components.jsx

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
- **FULL AUDIT DONE 2026-07-02 — decision doc = `AUDIT_ask_corpus.md` (repo root).** Order = A → deploy +
  acceptance → B → D → C → E. **Banner comes down after batches A+B verified live.**
  - **BATCH A SHIPPED 2026-07-02 (commit 559283f, `_CACHE_CODE_VER`→42, 99 tests green).** F1 mixed-signal
    scope (both OT+NT / both greek+hebrew now answer both, not collapse to one), F2 book-aware pick-parse
    ("1 John 3:1" no longer shown as John 3:1), F4 scoped-rare-word always runs pass-2, F13 follow-up
    context drops notice-turns, F9 O.T./N.T. periods, Fix 6 divine-council hardcode removed. **JP's
    post-deploy step:** run the #20B acceptance checks 1–5 PLUS the two mixed-signal cases now baked into
    `tests/test_scope_detect.py` ("compare the OT and NT view of the Sabbath", "charis in greek and hebrew").
  - **BATCH B SHIPPED 2026-07-03 (commit 7b55783 + empty-SQL nudge).** F3 schema/examples truthed up
    (strongs_base stated as always G/H-prefixed; every example → prefixed single-match; all 3 example JOINs →
    `l.strongs_g = w.strongs_base`; KJV-comparison join `'G'||w.strongs_base`="GG4151" → `= w.strongs_base`).
    F12 user-typed Strong's numbers always permitted — a bare typed number pins like a typed word
    (`_resolve_typed_strongs` + `tests/test_typed_strongs.py`, wired into CI + pre-commit). F15 pass-1 context
    "previous turn" → "recent turns". Fingerprint auto-busted (template sha1 5446f2→45aa8c9). **Live
    spot-checks: 4/5 passed** (co-occurrence, Hebrew, typed G4442, + others). **KJV-comparison FAILED live —
    see the whole-book-comparison card below; Batch B didn't break it, it never worked.** Shipped a friendly
    empty-SQL message as the immediate patch.
  - **BATCH C (thread skeleton) — SHIPPED 2026-07-02 (commit df60d22), moved to TODO_ARCHIVE.**
  - **BATCH D/E** — rail+failure UX (F6/F7/F8/F11) and cost+cache (Tier 1 normalizer, F14 pinned
    short-circuit, #4 parallelize loops). Quality, not roughness.
- **Whole-book KJV/ABP comparison — real feature (queued, from the Batch B live-check).** "acts kjv vs abp"
  fails: no specific word, so the SQL-gen model returns empty SQL → the friendly nudge now (word-level
  works: "grace in KJV vs ABP" fires the specific-word example). Making whole-book work is NOT a prompt
  line. **CC's noise analysis (start here, don't re-derive):** the naive join `LOWER(w.english_head) !=
  LOWER(kw.word)` across a whole book matches ALMOST EVERY word — ABP and KJV are different translations, so
  their words rarely match exactly, so "differs" is true nearly everywhere → the pool floods and pass-2
  Sonnet drowns in noise. The real question the feature must answer FIRST: **which differences are worth
  surfacing?** (a meaningful rendering split, not any lexical variance). Options to weigh: cluster by
  Strong's + only surface where the SAME number gets clearly different English families; cap to N most
  frequent/most divergent; or restrict to a curated "loaded word" set per book. Design before code.
  code: ai.py comparison path + `_AI_SYSTEM_TMPL` comparison section; static/src/52-ask-corpus.jsx.
- **Hebrew-word SQL-gen misses the ABP words table — fold into the LXX-seam card (same work).** A Hebrew
  query builds `WHERE w.strongs_base = 'H7307'` against `words`, which is Greek ABP text → GUARANTEED 0
  rows; the heb.db (+90) + cognate (+21) supplements carry the whole answer (correct + full, but the "thin,
  patched downstream" shape Batch B exists to kill). Fix = teach SQL-gen to also query the Greek LXX
  counterpart (ruach H7307 ↔ pneuma G4151) so the main query searches the real ABP OT text. The H→G mapping
  "isn't always clean" — which is EXACTLY what the **LXX seam** project builds (see the LXX-seam range-
  preservation / H↔G alignment work under the lexical-texture panel follow-ups). ONE card, two payoffs: when
  the seam table exists, this SQL-gen fix becomes a lookup instead of a guess. Don't build a throwaway H→G
  map here — wait for the seam. code: ai.py `_AI_SYSTEM_TMPL` Hebrew-bridge section.
- **Tier 1 semantic cache — scope fold SHIPPED 2026-07-03 (`_CACHE_CODE_VER`→47).** The exact-repeat
  cache already existed + was free; the one hole (punctuation-strip vs O.T./N.T. scope detection collided
  "fire O.T." with "fire o t") is closed — detected scope is folded into the cache key (`_scope_tag`),
  `tests/test_cache_key_scope.py`. **Tier 2 = NO-GO** at current volume (see AUDIT_ask_corpus.md). STILL
  OPEN: the OPTIONAL filler-strip normalizer (fold "what does X mean" → "X") — MUST reuse
  `_LANG_SCOPE_TERMS`/`_TESTAMENT_SCOPE_TERMS` as the never-collapse boundary AND inherit Batch A's
  mixed-signal rule (one value per axis = scope, two = unset — never strip a scope word). code: ai.py.
- **G2455 (Jew / Judas) tagging-side split — decide if it's worth fixing** (surfaced by the Batch E task 3
  alias review, 2026-07-02). ABP crams TWO different words on G2455: Ἰουδαῖος "Jews" (~177) AND Ἰούδας
  "Judas/Judah" (~41). NOT an alias-fold candidate (folding "Jew" there would drag Judas in) — it's a
  data-surgery class: the "Jew" occurrences would need re-tagging to their own number (G2453, currently 0
  in ABP) before anything downstream is clean. Low urgency; only matters if a Jew/Judas Ask-corpus search
  reads muddy. read-only audit path: the query set in this session's transcript.
- **G4119 (πλείων "more") tagging-side merge — writeup** (surfaced by the homeless-lemma sweep, 2026-07-02).
  G4119 = 0 rows in ABP; the comparative πλείων is collapsed into its base word **G4183 πολύς "many/much"**.
  NOT an alias-fold candidate — folding "more" into G4183 drags the whole πολύς pool along (same class as
  G2455). Data-surgery: the πλείων occurrences would need re-tagging to G4119 before a "more/greater" search
  or a Lexica entry for the comparative is clean. Low urgency. Anchors that pinned it: Mat 21:36 / Heb 3:3 /
  Joh 21:15.
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

## Licensing / attributions (page LIVE 2026-07-03; ABP wording the only open item)
Full record — source→license map, the BY-SA share-alike bucket, the bdb-is-Strong's-Hebrew lesson:
memory `project_licensing_attributions`. `/credits` + CREDITS.md are LIVE, linked from the App About
page + the crawlable SEO footer.
- **OPEN — ABP wording:** credits.html credits ABP to © Charles Van der Pool with NO permission claim
  (an HTML-comment placeholder marks the spot). Fill in the real permission/attribution line after the
  Van der Pool conversation — and keep the About "built on…" sentence un-polished until then, since his
  required wording may need to fold into/near it. ABP permission = the one real licensing exposure in the
  shipped app, a separate paid/permission question (not an attribution one).
- **OPTIONAL courtesy:** a thank-you note to OpenBible.info (geo place-coords) — CC BY doesn't require it.

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
