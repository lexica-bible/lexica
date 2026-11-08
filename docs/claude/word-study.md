# Lexica reference — Word study tab
Routed from CLAUDE.md. The Lexicon/Word-study surface + its endpoints.

## Layout
- "Word study" is a 3-pane layout (distribution rail · occurrences · word card) in
  `static/src/80-lexicon.jsx` (memory `project_ai_search_redesign`); AI search is its own
  **"Ask the corpus"** tab (`static/src/52-ask-corpus.jsx`, view key `corpus`). `--ai` token = the
  AI accent. `/api/lexicon/profile` also returns `derivation` + `related` (cognates, on-the-fly
  from lexicon `derivation` text).
- **Mobile + unified word card:** desktop + mobile share
  `renderDistRows`/`renderSenses`/`renderWordCardInner`; the English "words rendered" list is a
  collapsible `.glsenses`/`.glrow` card pinned above occurrences. Mobile branches
  `if (isMobile)` before the desktop `.ws` return: context strip (`.wm-ctx`) → reading area
  (`.wm-main`) → icon-only bottom tools bar (`.wm-tabs`). **The word CARD reuses the Library
  detail card's shared classes** (`.detail-hero`/`.sec`/`.detail-head`/`.detail-strong-head`/
  `.detail-body`/`.occ-link`) — **word-study-only tweaks MUST be scoped to `.wd`; NEVER edit the
  shared rule (it leaks into the Library word card, which the user has LOCKED).** Mobile sheets
  ride the shared `Sheet` shell (frontend.md → "The mobile sheet contract"; the old `WsSheet` /
  `.wm-sheet` frame is gone); `.occ-link` action links are `--ai`; results filters are underline
  `.tg` tabs.
- **Desktop** uses the shared workspace frame (frontend.md → "Three-zone shell"): 224px rail /
  `--sidebar-w` card, account pill shifted via `.app.view-lexicon .hdr-right`; `.brail-top` height
  = the search box so divider lines align. The per-book bar's scaling is a DEAD END (46px track
  too narrow) — left linear.
- **Ask AI placement:** desktop = right of the search bar (`.searchbar-ask`, once a word is loaded);
  mobile = the Views sheet's "Go deeper" (80-lexicon.jsx). Supersedes the original "link near the top of
  the word card".
- **Word-study card Definition block = the SAME shared body Library uses** — it fetches
  `api.lexica(profile.strongs)` (full dotted number) and renders idiom note → `StructuralBody` →
  `LexicaBody` → else the LSJ/BDB path. **GREEK ONLY** (`/^G/i.test(profile.strongs)`): Library never
  renders `LexicaBody` for a Hebrew word (it shows the BDB section), so neither does the card. The block
  HOLDS until the fetch resolves (FRAME-0 first-paint rule, frontend.md). The Summary/Full toggles live
  inside the shared components — carrying them IS the parity; never fork the component.
- **Numbering crosswalk in the card header:** `/api/lexicon/profile` returns `alias_note`
  (`contested_register.alias_note_for`, the same helper the Library card uses) → rendered beside the
  Strong's badge as `.detail-strong-alias` inside the one `.detail-strong-wrap` unit.
- LexiconView is always-mounted (display:none) so state survives tab switches.

## Search behavior
- Flow: search box → word profile → gloss chips → book distribution → verse list. Smart search
  detects Strong's (G4151, H7307), Greek, Hebrew, English.
- **Transliteration/lemma lookup = RANKED Exact / Contains bands.**
  `/api/lexicon/lookup` (Greek/Hebrew/translit path — NOT `/english`) returns ONE list split by
  a `match` tag: an **Exact** band (dictionary headword `lemma_plain` OR
  `strip_accents(lower(translit)) = q` — the translit tier pins "theos"→θεός G2316 and keeps
  euthéōs/βαθέως OUT) above a labeled **"Other words containing …"** divider holding substring
  hits (deduped vs exact, ordered by Strong's number — deterministic; substring can't tell
  family from letter-accident, so the label states a STRING match, not a relationship).
  Empty-exact still shows the divider. **MIN-LENGTH GATE:** the contains scan is
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
- **English-word finder = NUMBER-FOLDED.** `/api/lexicon/english` matches against
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
  `project_lexicon_finders`.
- The English finder shows all 4 "renders as" lines per word + a HEB/BSB filter, each line
  carrying that SOURCE'S TOTAL count (counted the way `lexicon_profile` does; HEB total folds
  homographs via `_heb_match`). The Hebrew object-marker אֵת H853 is dropped from the finder
  (`_HEB_FUNCTION_STRONGS`; caveat: et's "him/them" suffix forms share H853 so they drop too).
- **"Renders as" chips set the translation AND the gloss in one click** — `pickRender(lineCorpus, gloss)`
  (80-lexicon.jsx): every chip (ABP/HEB/KJV/BSB) switches `profileCorpus` to that chip's Bible and applies
  its gloss together; on the already-active tab it's the plain `selectGloss` toggle. It passes `lineCorpus`
  explicitly because `setProfileCorpus` updates async.
- **Function words show the CONNECTOR, not ABP's glued content word.** ABP lumps extra English onto a
  function-word token ("baked in", "shall not be"), and `english_head` picks the content word. For Greek
  function words (`is_func`, `_FUNCTION_STRONGS`) `_normalize_gloss(raw, is_func=True)` pulls the connector
  from the phrase (strong: preposition/negative/conjunction → weak: article/copula/pronoun → first word only
  if none); `_fold_glosses(..., drop_singletons=True)` drops leftover singletons on the profile only (small
  per-book counts are legit). Verse text is faithful ABP — never rewrite it. Read-only inspector:
  `scripts/inspect_funcword_glosses.py`. Memory `project_funcword_gloss_labeling`.
- **Result-list head-word highlight:** in result lists (Word study, Search, Ask-corpus — the shared
  `VerseRow` → `renderProseWords` path with `tightSpace`, 59c-library-render.jsx) the `--hl-match` gold
  paints only the matched word's `english_head`, never a helper ABP glued into the slot ("is love", "his
  love"); italic helpers render italic but NEVER gold. The reader (non-tight) is untouched — a real
  multi-word gloss still paints as one bar there. Trade-off accepted: a verb glossed to several English words
  golds only its head in result lists.

## Endpoints / data
- `/api/lexicon/lookup`, `/api/lexicon/profile/<strongs>`, `/api/lexicon/verses/<strongs>/<book>`
- `lexicon_verses` response:
  `{verses: [{chapter, verse, words: [{w, h, i?}]}], glosses: [{gloss, count}]}` — `h=true`
  marks the target word (rendered gold); `glosses` = per-book rendering breakdown; optional
  `?gloss=spirit` filters to one rendering.
- **`<book>` accepts `all`:** default "All books" lists EVERY occurrence in
  canonical order. `_all_books_verses()` in views_lexicon.py serves all four sources, returns
  lightweight verse keys tagged with `book` (lazy `VerseRow` re-fetches text), honors
  `?testament=ot|nt`, caps at `_ALL_VERSES_CAP` (6000) with `truncated` for mega-frequency
  function words. Book rail / OT-NT tabs / rendering chips all narrow it. Occurrence lists
  render **50 at a time with "See more" (+50)** (`visibleCount`).
- **Word-source toggle (focused word): ABP · HEB · KJV · BSB** — a number's
  occurrences, distribution, and "renders as" per source. **Hebrew DEFAULTS to HEB = heb.db (the
  REAL Hebrew OT, NOT the old KJV bridge); the ~150 byform/Aramaic/name numbers heb.db lacks
  fall back to KJV (`has_heb` false).** Greek defaults to ABP. `lexicon_profile/books/verses`
  carry per-source branches + `has_abp/has_heb/has_kjv/has_bsb` + per-source glosses; heb/bsb
  occurrence lists re-fetch per-verse in `VerseRow` (heb = an ALIGNED interlinear: each Hebrew
  word stacked over its gloss, laid LTR — letters stay RTL; `.corpus-heb-int`/`.chi-*` CSS; bsb
  mirrors KJV). Memory `project_hebrew_source_swap`.
- **Dotted different-words get their OWN profile (2026-06-21).** ABP parks added words at
  "nearest Strong's + a dot"; the `dotted_lexicon` table names the ones that are a genuinely different
  word (data-model.md). `views_lexicon.py` helpers `_dotted_ready` / `_dotted_diff_row(conn,num)` /
  `_abp_strongs_filter(conn,num,sid)`: a dotted different-word → its OWN rows by `w.strongs`; a base
  number → `strongs_base` EXCLUDING members of `dotted_lexicon`. Wired into every ABP word query
  (profile, `lexicon_books`, `lexicon_verses`, `lexicon_english` grouping + `_top_glosses_abp`);
  `lexicon_lookup` also finds them by their own lemma/romanization; a different-word profile is
  LXX-only (KJV side off). Frontend highlights the FULL number (`80-lexicon.jsx` citedStrongs,
  `50-corpus-results.jsx` VerseRow). The old fold into the base was 100% backend — search parsing
  and reader clicks already carried the full `G###.N`. Memory `project_build_folded_fixes` §11a.

## `/api/search` — REMOVED
The old standalone Search tab and `/api/search` are gone (commit 6eaec4e). **views_search.py hosts
ONLY `/api/text-search`.** Live search = Library in-text search (`/api/text-search`) + Word study
(`/api/lexicon/*`) + Ask the corpus (`/api/ai-search`). Don't wire new work to `/api/search`.

## Lemma-keyed entry for numberless PN identities — `PN:<form>` (2026-07-28)
The ~14,850 lemma-only PN identities (real Greek name-form, no Strong's number in any
scheme) open Word study via a `PN:<greek_lemma>` key through the SAME
profile/verses routes (`views_lexicon._pn_lemma_rows` = the ONE derivation, identical to
the card's static count in views_metav's lemma-only branch — PARITY list==count is a
locked CI test, `test_pn_lemma_wordstudy.py`). Invariants:
- **Key namespace**: `PN:` prefix, checked BEFORE the number regex in profile/verses —
  never mint another key shape that could collide with the `[GH]\d+(\.\d+)?` space.
- The profile answers with `strongs: "PN:<form>"` + `name_form: true`; the frontend
  displays "PN" in the header and gates Ask/corpus toggles off `name_form` — the full
  key must keep flowing through `profile.strongs` (book rail / verses / testament
  re-fetches all key off it; displaying it raw was the only change).
- List is LEMMA-WIDE (every occurrence of the printed form) per the all-Edens ruling;
  identity disambiguation stays on the reader cards. The header state line says so.
- `?lex=PN:<form>` works as a URL entry (90-app reads `lex` verbatim).
- **How a name FOLDS to one header (standing).** `pn_greek_identity.greek_lemma` is per
  occurrence, not per name. One folded header (`source='surface'`) only happens when every
  printed form of the name is byte-identical, or the name is in the receipted hand table
  `scripts/greek_header_nominatives.tsv` (page-cited, batch records
  `docs/tickets/greek_header_batch*.md`). **Proper-noun rows never carry `words.lemma`** — all
  32,478 are blank, by design — so the header comes from the printed-form table or the hand
  table, never from a dictionary lemma. Admission rule: every printed form the SAME stem
  declined AND the headword printed on ABP's own pages; one clean page receipt is enough
  (reviewer 2026-08-09), ambiguous forms carry no weight.
- **TRIPWIRE — two-word name values are joined by U+00A0, not a space.** `greek_lemma LIKE
  '% %'` reads **0** against rows you can see. Use `LIKE '%'||char(160)||'%'`, and fire it on
  known rows first — the 27 pinned compound names (`compound_names_allowlist.tsv`, read from
  hex), NOT 1Ki 11:17 slot 2: that glued row was cured and now reads plain `Αδάρ` (live
  2026-10-24). This lane has now learned it twice — commit `5a533f9b` (July) and again 2026-08-09.
- **TRIPWIRE — that detector finds a CLASS, not a defect.** Of 144 two-word values, 27 are
  genuine compound names (Βαάλ Ερμών Baal-hermon, Γασιών Γαβέρ Ezion-geber, Αππίου Φόρου
  Appii Forum, both Αρειον Πάγον Areopagus rows) and must stay — pinned byte-exact (hex
  column) in `docs/tickets/compound_names_allowlist.tsv` since the form lane; gates check
  the file, never re-argue the members. Adjudicate on the ENGLISH
  column: a name reads as a place, a defect reads as a sentence ("And Herod" = `Ηρώδης δε`).
  Known-bad and parked: Act 12:19, Act 13:1, Jos 12:23.
- **Form-table state:** `abp_surface` floor = 395,003 rows (the builder chain's 391,130 + the
  2026-10-25 fill's 3,873; floor checked in `scripts/health_check.py`). Name slots with no printed
  form were **642** when the form lane landed (2026-08-23; the 10/25 fill may have moved it). Name-slot
  coverage includes the BRIDGE rule in `backfill_pn_surface.py`: a labeled name slot may take
  a glued star cell's extracted name word only on same-book standalone attestation (exact
  form, refuse-on-doubt; cause codes bridge-fail/bridge-ambiguous distinct from no-match).
  Why: glued scrape cells ("made=Σολομών") enter the pools under the VERB's English, and the
  8/8 label fill moved ~172 slots off the blank-label path that had covered them. Full
  record: `docs/tickets/CHARTER_form_table_rebuild.md`.
- **ABP-tab routing via the folded header (2026-09-06, `CHARTER_abp_tab_routing.md`).** A Greek
  number with NO words row (starred name slots — Galilee G1056) used to grey the ABP tab and
  silently fall back to KJV. `_header_bridge` now routes it through its folded header when, and
  only when: the lexicon lemma folded like `lemma_plain` reaches numberless rows that are ALL
  `source='surface'` (no `lemma-only` residual — Zion 168+1 / Aram 12+5 refused until folded), ONE
  stored value, and the key has ONE lexicon owner (γαζα, ηλι collide → refused). `_bridge_if_grey`
  consults it only when the production predicate finds nothing, so MIXED numbers (47 at landing
  with a same-header numberless residue — own follow-up) and ordinary words never change.
  Bridged: the ABP branch (book counts, All-books + per-book lists with `position`, total) =
  `_pn_lemma_rows(header)` — the PN: page's derivation, PARITY locked in
  `tests/test_abp_tab_bridge.py`; renderings stay empty; profile carries `abp_header` (JP-approved
  field, present only when bridged) which drives the ruled state line under the count. Israel /
  Jerusalem (lemma-only only, one value) HELD by ruling: they route only once the header lane vets
  them as `surface`, never via a lemma-only door. Census tool: `scripts/audit_abp_tab_bridge.py`
  (read-only, live + a pre-fold copy). NOT bridged: `/api/lexicon/books` (only the rendering-chip
  book narrowing calls it — empty for bridged names, so the chip doesn't narrow; open in TODO.md).
- **In-verse highlight:** the verse-row highlighter matches by Strong's number everywhere
  EXCEPT this lane — a PN: page has no number, so the profile/verses rows carry each
  occurrence's `position` (the name's own word slot from pn_greek_identity) and VerseRow lights
  it via `hiPositions`. **Hebrew numbers too:** when `_abp_strongs_filter`'s cross-ref arm
  is in use (`_h_xref_union_on`), both ABP verse lists send `positions` — every slot that
  SAME filter matched in the verse, one row per verse — because the xref-only words store
  '*' and can't match by number. VerseRow prefers `positions`, else `position`. Greek-number
  lists never get the field. Locked `tests/test_hebrew_xref_positions.py`.
- **Each reader shows its own occurrences (JP 9/6, ratified 10/24):** an H-number's ABP tab
  lists ABP's own name slots linked to that number — ABP shows ABP, KJV shows KJV, HEB shows
  Hebrew, whether the key is G or H. The 9/6 "no ABP results for an H-number" reversal was
  WITHDRAWN (charter archived, docs/tickets/archive/).
