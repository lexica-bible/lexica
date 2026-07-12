# Lexica reference — AI features
Routed from CLAUDE.md. Ask-the-corpus, the AI result cache, TSK cross-references, summaries.

## Model map
SQL gen + term extraction + most features on **Haiku**; the displayed synthesis surfaces —
Ask-corpus pass-2, TSK xref synthesis, chapter summary — on **Sonnet** (`claude-sonnet-4-6`).
Reason: Haiku parroted the question's framing on nuanced questions and over-asserts. Never
suggest a prompt change that regresses (parrots framing, over-asserts, adds jargon, blacklists
instead of reframing) — memory `project_ai_synthesis_quality`.

## TSK Cross-Reference panel
- Endpoint: `GET /api/cross-references/curated/<book>/<chapter>/<verse>`
- Step 1: Haiku selects 8-10 strongest refs from the full TSK list, reading candidates + source
  verse in BSB (KJV fallback — clearer than "thou/thee" for judging links; `cand_texts`). The
  picker returns indices into `all_refs`, so the cross_references KJV verse-id join is untouched.
- Step 2: Sonnet writes the synthesis — adaptive length (~100-word soft ceiling, runs longer for
  a rich link), anchored in ABP source vocabulary; prompt carries a worked example. BOTH the
  source verse AND the curated refs are fed in ABP (`_abp_text` in views_crossref.py); fallback
  when ABP's versification lacks a verse = **BSB, then KJV** (`_bsb_text`) — the write-up never
  quotes KJV "thou/thee". Displayed verse field = **`text`** (renamed from `kjv_text`; frontend
  40-crossref-panel.jsx). A `msg:` salt in `_XREF_VER` (now `bsb-fallback-4`) is bumped on any
  message/payload change so cached rows refresh (the fingerprint covers the prompts, not message
  text or payload shape).
- Cached in ai_search_cache, ONE row per verse: key `xref_cur:<book>:<ch>:<vs>` holds BOTH the ref
  list AND the synthesis text. No `xref_synth:` key exists — a stale claim of one here cost a wasted
  exhibit-hunt query 2026-07-12. ver_key=`xref:<hash>`.

## AI Search (Ask the corpus)
- **Exact-lemma pin (2026-07-01).** A bare typed single Greek/Hebrew word is pinned to its EXACT
  Strong's BEFORE the model (`_resolve_exact_lemma` in ai.py, indexed `lemma_plain`), and
  OVERRIDES the model's sql + key word so the occurrence list is that ONE number, not the
  English-concept guess. Greek → direct `strongs_base`
  query; Hebrew → empty SQL, filled by the heb.db supplement. Homograph/dotted collisions
  (Greek 27, Hebrew 1,460) fall through to the model. A query that IS a typed Strong's number
  ("G4442"/"H784") pins the SAME way (`_resolve_typed_strongs`, Batch B 2026-07-03) — a user
  citing a key is always permitted, never the model inventing one. `_CACHE_CODE_VER`→40.
- **Daily spend caps** — per account/UTC-day (user 3 / berean 10 / admin unlimited + uncounted)
  AND a whole-site daily ceiling (~50 ≈ $2). Enforced server-side in `ai_search` BEFORE any model
  runs; cached/reopened answers never count. Knobs = `AI_DAILY_LIMITS` + `AI_SITE_DAILY`
  (views_notes.py); frontend caps 3 follow-ups/thread. Memory `project_ai_spend_caps`.
- Berean system prompt — no imported theology. key_strongs: up to 10 chips (6 Greek + 4 Hebrew).
- Empty-result retry (LAST RESORT): Haiku broadens the SQL only when the first query AND the
  cheap fallbacks (explanation-cited verses, proper-noun english LIKE) ALL come up empty.
- **Hebrew evidence from heb.db (2026-06-22):** an H-number target pulls a canonical SPREAD of
  real occurrences from heb_words (code-side supplement, mirrors the cognate/phrase ones),
  injected + tagged with the H-number so the citation guard counts them. The model's KJV-bridge
  SQL stays as fallback. Verses ABP's versification lacks are skipped. Verse evidence has an
  **ABP·BSB·KJV·HEB display toggle** (per-turn in `AcTurn`); ALWAYS defaults to ABP (the old
  auto-show-HEB was dropped, user's call). HEB grays unless the answer has OT verses and shows
  ONLY those (gate `hasOtVerse` = any non-`NT_BOOKS` result). Memory
  `project_hebrew_source_swap`.
- **Speed shape: model-bound.** Phrase queries don't scan the 600k word-gloss: a multi-word LIKE
  is re-run against FULL verse text (verses.text + kjv_verses + bsb_verses) in code, and a
  phrase-ONLY query SKIPS the gloss SQL entirely. The proper-noun name-scan only fires when
  results are thin (`< _PROPER_NOUN_NEED`). Timing `log.info("ai_search timing …")` + per-call
  token-split lines + a `SLOW SQL` warning stay on (grep PA logs; Haiku SQL prompt caches, Sonnet
  pass-2 can't).
- **Synthesis STREAMS (SSE, 2026-06-29).** `/api/ai-search` returns an event-stream for a FRESH
  search: `panel` event first, prose streams (`delta` events), verse evidence in a `done` event.
  Cache hits / quota / login / errors stay one-lump JSON (frontend branches on content-type).
  `X-Accel-Buffering: no` is the whole fix for PA buffering. Pass-2 output: prose FIRST, then
  `===VERSES===`, then one-line JSON of picks — parsed by FAIL-CLOSED `_parse_curation` (bad
  tail → re-run non-streamed `_curate_primary_verses`, keep streamed prose; never a wrong-verse
  split). Helpers in ai.py: `_curation_prompt`, `_curate_primary_verses`, `_stream_curation`,
  `_assemble_payload`, `_streamable_prose`, `_sse`. Frontend `api.aiSearchStream` (00-core.jsx)
  + `AcProse`.
- **Citation guard + grounding (2026-06-21).** Occurrence lists are pulled by Strong's =
  unfakeable; the leak is in the PROSE. A verse the model names containing NONE of the target
  words is `is_thematic` → "Additional references" (kept, labeled, never primary). REGIME-AWARE:
  no target word (broad question) ⇒ no flag. The pass-1 prose is written from MEMORY before
  retrieval, so the DISPLAYED explanation is ALWAYS the pass-2 GROUNDED one whenever the answer
  names a verse (pass-2 cites ONLY from the real retrieved list). Ranking skipped only for a
  small pool whose prose cites nothing.
- **No lexicon definition prose in the synthesis payload — A3/A4 INVARIANT (2026-07-01).**
  Answers are built ONLY from verse evidence + retrieval KEYS (Strong's/lemma/translit), never
  LSJ or Strong's DEFINITION text. The LSJ context fed to pass-1 is keys-only
  (`ai._retrieval_context`, which REPLACED `views_lsj._format_lsj_context` — that leaked LSJ
  `semantic` + a cognate gloss into the visible explanation). Fail-closed guard
  `_assert_no_lexicon_prose` drops any block carrying def prose. Keep the exclusion STRUCTURAL
  (don't "tell the model to ignore LSJ" — the text must not be in the payload). Locked by
  `tests/test_synthesis_no_leak.py` (CI + pre-commit). The answer PROVENANCE rail rides the SAME
  payload (`results`/`is_primary`/`key_strongs`/`grounded` + `contested`), never a second lookup.
- **Synthesis inputs + seatbelt.** Verses handed to pass-2 are a SPREAD across books
  (`_spread_sample`: round-robin per book, not `results[:N]` — which was early-OT-only and
  mislabeled both-testament words "the LXX"); within each book the most cross-referenced verse
  (TSK count via `_xref_scores`) wins the seat. Frontend SEATBELT (`AcProse`): the prose only
  LINKS a verse ref actually in retrieved results — a model-named unretrieved verse renders
  plain.
- **Honest empty-state + neutrality.** Payload carries `grounded: false` when the search found
  no real occurrence → pale-amber "no direct occurrences" caveat instead of a confident
  write-up. Both explanation prompts carry a NEUTRALITY rule — answer from the text, not the
  question's framing ("same?" vs "different?" must give the same answer; if the text doesn't
  settle it, say so).
- **Same-root cognate supplement (2026-06-22).** Each GREEK target's same-root family is pulled
  deterministically (`_greek_cognates` + `_cognate_is_tight` stem filter) — the relative's
  verses + a chip, ONLY if it actually occurs (σαββατισμός G4520 / Heb 4:9 under σάββατον).
  Greek only (BDB has no etymology). A code/context change like this isn't in the search
  fingerprint → bump `_CACHE_CODE_VER`.
- **Computed lexical-texture panel (2026-06-29).** A deterministic distribution panel ABOVE the
  synthesis (FACT, not generated): per query word, its gloss-confirmed family with full corpus
  counts + per-language bars. NO model call — built from `key_strongs` AFTER the answer, behind
  a tight wall-clock deadline + dropped on any miss (own connections + SQLite watchdog + 250ms
  lock-wait — can't slow or break the paid answer). None when no clean head; NEVER manufactures.
  Engine = **`corpus_panel.py`** (repo root); `panel` field on the payload; `CorpusPanel` in
  52-ask-corpus.jsx — its rows ARE the per-word doorway into Word study. Family = STEM proposes
  (translit prefix, prefix-compound aware) / GLOSS disposes; borderline words COUNTED, not
  listed. Locked by `tests/test_corpus_panel.py`. Memory `project_corpus_enrichment`.
- **Synthesis standing rules — Berean (all LOAD-BEARING).** The displayed note
  (`_CURATION_SYSTEM`, mirrored in `_AI_SYSTEM_TMPL`): NO doctrinal verdicts (never rule a
  practice binding/abolished or assign a stance to an author — report the verse, let the reader
  conclude); contested "is X binding" questions are IN SCOPE (answer, withhold only the verdict);
  prose uses transliteration + Strong's number, NEVER raw script. REPORT, DON'T CHARACTERIZE —
  every clause pins to a verse that states it. A SABBATH-vs-WEEK lexical note (σάββατον = the
  seven-day WEEK in the "one of the sabbaths" idiom) + no "what the verse doesn't do" riders.
  CORPUS VOCABULARY: describe meaning from the corpus's own renderings, NOT post-biblical
  category terms (person/Trinity/unmerited/sacrament/moral authority/hypostasis); report an
  action as an action; prefer the ABP word (delivered not salvation, favor not grace, immerse not
  baptize, assembly not church); on a CONTESTED word describe attested use without resolving the
  contest. Memory `project_ai_synthesis_quality`.
- **Follow-ups carry the recent thread** — last 6 turns + key lemmas as a `context` query param,
  woven into term + SQL prompts only to resolve references. **Pass-2 ALSO gets a `skeleton`
  param (Batch C, 2026-07-02)** — a client-built digest of what earlier ANSWERS covered → an
  injected "don't restate, build on it" directive in `_curation_prompt`
  (`_skeleton_directive`). Caps 6 turns / 1000 chars, injected per-request so a first turn's
  prompt is byte-identical (no fingerprint change). "New thread" (rail) resets. Follow-ups are
  never cached, so the skeleton has zero cache implications.
- **LANGUAGE/TESTAMENT SCOPE directive (2026-07-02, #20B).** Greek-first stays DEFAULT (ABP is
  a Greek primary text incl. the LXX; Hebrew is a cross-ref layer). A query naming a language or
  testament gets an override via `_detect_scope`/`_scope_directive` (ai.py), added to
  `_curation_prompt` only — retrieval + panel untouched. Divergence rule: stay scoped, cross to
  the other language only on a sense divergence (one short bridge note). MIXED-SIGNAL rule
  (Batch A): a query naming TWO competing values on one axis ("compare the OT and NT") is a
  comparison, NOT a scope — that axis goes unset, never first-match. INVARIANT: the term lists
  `_LANG_SCOPE_TERMS`/`_TESTAMENT_SCOPE_TERMS` are the never-collapse boundary the parked
  Tier-1/2 cache normalizer MUST reuse — don't build a second list.
- Cached in ai_search_cache, ver_key=`search:<hash>` (fingerprint of system prompt +
  `_CURATION_SYSTEM` + book list + `_CACHE_CODE_VER` salt). The cache ROW KEY is NORMALIZED
  (`_cache_key` in ai.py: lowercase, punctuation→space, collapse spaces) so trivial variants
  reuse one answer. Only the KEY is normalized — models get original wording. Search-path only;
  follow-ups (with `context`) are never cached.
- AI-generated SQL runs on a READ-ONLY connection (`db_ro`), single-statement, SELECT-only
  guard; failures log SQL/error server-side ONLY (never returned to the client).

## AI result cache (ai_search_cache) — prompt-fingerprint scheme
Full record: memory `project_ai_cache_unify`.
- Every AI synthesis caches with `ver_key = "<category>:<sha1-of-its-own-prompt>"` — categories
  `search:` (ai.py), `summary:` (views_summary.py), `xref:` (views_crossref.py), `pn:`
  (views_metav.py), `chrono:` (views_chrono.py, key `chrono_intro:<day>`). Editing a prompt
  changes only its category's hash → just that cache refreshes; a regen overwrites the stale row
  in place.
- Helpers in core.py: `ai_fingerprint(category, *parts)`, `ai_cache_get` (old-prompt row misses
  → regenerates), `ai_cache_put`, `ai_cache_prune(category, keep_prefix)`. Each category prunes
  ONLY its own stale rows at startup (app.py).
- **LANDMINE:** a delete must be scoped to its OWN category (search's startup cleanup is
  `search:%` only). A new cache category gets its own `<category>:<hash>` tag + its own startup
  prune — never widen another category's delete.
- summary rows add a per-book author suffix `summary:<tpl-hash>:<author-hash>`. `_BOOK_AUTHORS`
  (views_summary.py) feeds the BOOK BLURB only, NOT the chapter summary — well-established
  authors + named scribes only, the rest blank on purpose.
- LSJ word-study summaries live in `lsj.summary_json` / `abp_ext.summary_json`, NOT this table,
  but self-heal the same way: a `_synth_ver` stamp (= `ai_fingerprint("lsj", ...)` in
  views_lsj.py) checked on read, dropped/regenerated when the prompt changes. The LSJ blurb is a
  Haiku **"definition"** prompt (open with the meaning; Koine anchor, no book-naming;
  favor-not-grace example) + per-word **"Lexica" overrides** shown DIRECTLY, no model call, for
  loaded lemmas LSJ leads classical on (`_LSJ_OVERRIDES`/`_ovkey` in views_lsj.py — badged
  "Lexica" not LSJ; the Summary|Full-entry toggle still shows raw LSJ). Memory
  `project_lsj_card`.

## Lexica definition engine — Tier B prose-fix discipline (2026-07-06)
The draw cache (`draws/G####.json`, the reviewed-verbatim store the Lexica cards render from) carries a
validity signature that covers ONLY a word's SAMPLED verses. A Tier B corpus prose fix to a verse a card
merely CITES but that wasn't in its fed sample (e.g. Mat 21:19 under the common γίνομαι G1096) does NOT
move that signature — the card keeps quoting the pre-fix reading and nothing auto-refreshes.
- **STANDING RULE: a prose correction is NOT done until the sweep runs and comes back reviewed.** Every
  Tier B prose fix ends with `python3 scripts/check_draw_citations.py bible.db --draws ~/bible-db/draws`
  (READ-ONLY; flags any shipped card whose cited verse is a reassembly-diff hit). **This runs against
  bible.db, so JP runs it on PA and pastes the output — CC never runs it directly.** `word-order` /
  `content-other` / `dup-gloss` collisions are actionable (mis-ordered reading or baked apparatus);
  `punct-position` is the cosmetic comma-placement residual (240 corpus-wide post-S11 — cards render clean
  `verses.text`, no redraw).
- **Affected cards get a targeted redraw + reviewed ship:** `--dry-run --force --word G####` regenerates and
  re-writes the draw for review, then `--apply --word G#### --from-draw KEY8` ships the reviewed bytes with
  NO model call (KEY8 = the draw signature's first 8 chars). `--from-draw` refuses on a missing/stale/edited
  draw or a key mismatch — a refuse is the enforcement working: regenerate-and-re-review, never loosen it.
