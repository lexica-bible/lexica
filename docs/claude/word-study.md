# Lexica reference — Word study tab
Routed from CLAUDE.md. The Lexicon/Word-study surface + its endpoints.

## Layout / history
- **REDESIGNED 2026-06-19 — memory `project_ai_search_redesign`.** "Word study" is a 3-pane
  layout (distribution rail · occurrences · word card) in `static/src/80-lexicon.jsx`; AI search
  was split OUT into its own **"Ask the corpus"** tab (`static/src/52-ask-corpus.jsx`, view key
  `corpus`). `--ai` token = the AI accent. `/api/lexicon/profile` also returns `derivation` +
  `related` (cognates, on-the-fly from lexicon `derivation` text).
- **Mobile word study + unified word card (2026-06-19c):** desktop + mobile share
  `renderDistRows`/`renderSenses`/`renderWordCardInner`; the English "words rendered" list is a
  collapsible `.glsenses`/`.glrow` card pinned above occurrences. Mobile branches
  `if (isMobile)` before the desktop `.ws` return: context strip (`.wm-ctx`) → reading area
  (`.wm-main`) → icon-only bottom tools bar (`.wm-tabs`). **The word CARD reuses the Library
  detail card's shared classes** (`.detail-hero`/`.sec`/`.detail-head`/`.detail-strong-head`/
  `.detail-body`/`.occ-link`) — **word-study-only tweaks MUST be scoped to `.wd`; NEVER edit the
  shared rule (it leaks into the Library word card, which the user has LOCKED).** Mobile sheets
  (`WsSheet`) use shared `useSwipeToDismiss` (`.wm-sheet` reserves safe-area); `.occ-link`
  action links are `--ai`; results filters are underline `.tg` tabs.
- **Desktop mirrors the Library shell (2026-06-20):** the right word card is a fixed full-height
  panel over the navy header; card head = header height so the divider runs unbroken (empty
  state too, `.wd .empty-pane::before`); columns match Library (224px rail / `--sidebar-w`
  card); account pill shifted via `.app.view-lexicon .hdr-right`. `.brail-top` height = the
  search box so divider lines align; "All books" lost its box. The per-book bar's scaling is a
  DEAD END (46px track too narrow) — left linear.
- LexiconView is always-mounted (display:none) so state survives tab switches.

## Search behavior
- Flow: search box → word profile → gloss chips → book distribution → verse list. Smart search
  detects Strong's (G4151, H7307), Greek, Hebrew, English.
- **Transliteration/lemma lookup = RANKED Exact / Contains bands (2026-07-01).**
  `/api/lexicon/lookup` (Greek/Hebrew/translit path — NOT `/english`) returns ONE list split by
  a `match` tag: an **Exact** band (dictionary headword `lemma_plain` OR
  `strip_accents(lower(translit)) = q` — the translit tier pins "theos"→θεός G2316 and keeps
  euthéōs/βαθέως OUT) above a labeled **"Other words containing …"** divider holding substring
  hits (deduped vs exact, ordered by Strong's number — deterministic; substring can't tell
  family from letter-accident, so the label states a STRING match, not a relationship).
  Empty-exact still shows the divider. **MIN-LENGTH GATE (2026-07-03):** the contains scan is
  SKIPPED for a query under 3 FOLDED letters — γῆ folds to "γη" (2), and a 2-letter fragment
  sits inside dozens of unrelated words. Gate on FOLDED length (`len(qn)`), never raw codepoints
  (accented input can count 3+ raw). At 3+ letters KEEP substring, do NOT switch to prefix:
  Greek compounds put the root at the TAIL as often as the head (ἄλογος/φιλόλογος under λόγος).
  Exact band untouched, so γῆ still answers G1093. Locked by
  `tests/test_lexicon_lookup_bands.py` (drives the real endpoint). The corpus-scoping path keys
  off `lemma_plain` equality, never this scan. Frontend auto-opens ONLY a lone true hit
  (exact=1, nothing else). The source/language filter bar is HIDDEN over a lookup set (it only
  re-queries the English-rendering search). `80-lexicon.jsx`
  `matchBands`/`renderMatchRow`/`showLookup`; `.glmatch-div` CSS.
- **PARKED — do NOT build: root/family search** (θεός, ἄθεος, φιλόθεος by theo- root). Blocker:
  `lexicon` has NO structured stem/root column — only free-text `derivation`. Substring fakes it
  and leaks (euthéōs is the proof). Needs a real root field first.
- **English-word finder = NUMBER-FOLDED (2026-07-01).** `/api/lexicon/english` matches against
  attested renderings via a precomputed `*_norm` column (`words.english_head_norm` /
  `kjv_words`+`bsb_words` `word_norm`) so singular↔plural reach each other ("magistrate" finds
  theos G2316, rendered "magistrates" in Exo 22:28). Query and rendering pass the SAME
  `number_fold.normalize` (curated irregular map + careful singularizer + -ous/-ss guards +
  per-token for phrase heads) — no inverse. Deploy-safe: `_has_norm` falls back to exact match
  if the backfill hasn't run. Built by `scripts/build_rendering_norm.py` (PA step; RE-RUN after
  a words rebuild — in the checklist — and auto-run at the tail of load_bsb_words.py).
  **KNOWN GAP:** the Hebrew-OT discovery branch (`corpus=heb`) is NOT folded — matches a token
  inside a multi-word gloss phrase; needs a normalized-token side-index in heb.db + a looser
  number-blind `gloss LIKE` prefilter. **The results summary SURFACES + BOLDS the searched
  rendering:** each result's per-source "renders as" line shows top 8 by count, bolds the match
  (`.glrow-match`, weight only), appends it in sorted position if below the cap; trailing ` …`
  marks a source with more forms. All in `lexicon_english`'s `_fold`/`_top_glosses_*` (NOT
  `lexicon_profile`); the lookup/translit path untouched. Memory
  `project_lexicon_number_fold`.
- The English finder shows all 4 "renders as" lines per word + a HEB/BSB filter, each line
  carrying that SOURCE'S TOTAL count (counted the way `lexicon_profile` does; HEB total folds
  homographs via `_heb_match`). The Hebrew object-marker אֵת H853 is dropped from the finder
  (`_HEB_FUNCTION_STRONGS`; caveat: et's "him/them" suffix forms share H853 so they drop too).

## Endpoints / data
- `/api/lexicon/lookup`, `/api/lexicon/profile/<strongs>`, `/api/lexicon/verses/<strongs>/<book>`
- `lexicon_verses` response:
  `{verses: [{chapter, verse, words: [{w, h, i?}]}], glosses: [{gloss, count}]}` — `h=true`
  marks the target word (rendered gold); `glosses` = per-book rendering breakdown; optional
  `?gloss=spirit` filters to one rendering.
- **`<book>` accepts `all`** (2026-06-24): default "All books" lists EVERY occurrence in
  canonical order. `_all_books_verses()` in views_lexicon.py serves all four sources, returns
  lightweight verse keys tagged with `book` (lazy `VerseRow` re-fetches text), honors
  `?testament=ot|nt`, caps at `_ALL_VERSES_CAP` (6000) with `truncated` for mega-frequency
  function words. Book rail / OT-NT tabs / rendering chips all narrow it. Occurrence lists
  render **50 at a time with "See more" (+50)** (`visibleCount`).
- **Word-source toggle (focused word): ABP · HEB · KJV · BSB** (2026-06-22) — a number's
  occurrences, distribution, and "renders as" per source. **Hebrew DEFAULTS to HEB = heb.db (the
  REAL Hebrew OT, NOT the old KJV bridge); the ~150 byform/Aramaic/name numbers heb.db lacks
  fall back to KJV (`has_heb` false).** Greek defaults to ABP. `lexicon_profile/books/verses`
  carry per-source branches + `has_abp/has_heb/has_kjv/has_bsb` + per-source glosses; heb/bsb
  occurrence lists re-fetch per-verse in `VerseRow` (heb = an ALIGNED interlinear: each Hebrew
  word stacked over its gloss, laid LTR — letters stay RTL; `.corpus-heb-int`/`.chi-*` CSS; bsb
  mirrors KJV). Memory `project_hebrew_source_swap`.

## Search tab — REMOVED (2026-06-23)
The old standalone Search tab and `/api/search` are GONE (route + KJV helpers + the unused
`api.search` frontend helper deleted, commit 6eaec4e). **views_search.py hosts ONLY
`/api/text-search`.** Live search = Library in-text search (`/api/text-search`) + Word study
(`/api/lexicon/*`) + Ask the corpus (`/api/ai-search`). Don't wire new work to `/api/search`.
