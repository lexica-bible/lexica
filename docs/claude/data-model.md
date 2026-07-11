# Lexica reference — Data model
Routed from CLAUDE.md. Read the relevant table's block IN FULL before touching it.
Core invariants are summarized in CLAUDE.md; this file is the authoritative detail.

## bible.db tables

### verses
ABP verse text. `verses.text` is the clean, correctly-ordered English PROSE (what the reader's
prose mode + SEO pages use). NEVER rebuild a single verse from `words` joined by `position` —
that's raw Greek order and SCRAMBLES ABP's bracket-reordered English. (2026-06-21 TSK-panel
garble: `/api/verse` and `views_crossref._abp_text` were stitching words by position; both now
read `verses.text`.) NARROW EXCEPTION — don't let this rule excuse a real data bug: a
"LORD the"-style flip (a determiner stranded AFTER its noun) is NOT the expected bracket
scramble, it's a `_split_compounds` BUILD bug — when it fronts the words it spread onto blank
Greek slots it lines them up in Greek order instead of the source English order. Fixed in the
build split step (preserve source English order when fronting), so the right order is baked back
into `words` and the reader needs no change. Find the full set with `scripts/audit_split_flip.py`
(read-only). Distinct from genuinely bracket-reordered verses, where the rule above still holds.
A leak or defect can sit OUTSIDE a bracket group; the pinned feed adjudicates it there too
(Tier B `abp_corrections`) — don't assume defects live only inside the reordered brackets.
`verses.book` is a TEXT abbreviation — a plain sort is alphabetical; `_ABP_RANK_SQL` maps each
abbrev to Bible order for canonical sort/filter.

### words
ABP word-level interlinear, Strong's tagged. Columns: english, english_head, strongs,
strongs_base, greek_pos, bracket_id, italic, italic_words, smcap_words, is_pn, morph, lemma.
The displayed Greek lemma is joined live from `lexicon` via
`LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base` (the indexed G-prefixed key from Phase 1;
replaced the old `SUBSTR(strongs_base,2)` join — this is why strongs_base MUST stay
G/H-prefixed). `is_pn=1` marks proper nouns (set by import_tipnr.py). `morph`/`lemma` added
rebuild #6 (~78% populated; further fill scrapped — memory `project_abp_morph_gap`).

**`english` vs `english_head`:** `english` is ABP's rendering as printed — a multi-word PHRASE
gloss is parked whole on ONE token slot ("Jesus to them," on the αὐτός token). `english_head`
(built by `parse_abp._head_word` = last non-function word) is the token's OWN render, the RIGHT
column for any "renders as" count — raw `english` fed through the normalizer mis-heads a parked
phrase into a phantom render ("jesus" under a pronoun). All render counters (word-study panel,
def-engine draw, coverage `rendering_sets`) read `english_head`; the chip still DISPLAYS
`english`. Documented limit (pronoun/function slots can carry a trailing parked word): the
citable `parse_abp.HEAD_WORD_TAIL_CAVEAT`; locked by `tests/test_render_head_no_phantom.py`.

### strongs_base format — CRITICAL INVARIANT
- `words.strongs_base` is fully G/H prefixed ('G4151', 'H7307') — normalized 2026-06-01.
- NOT cosmetic: the lexicon join matches `l.strongs_g = w.strongs_base` (strongs_g =
  'G'||strongs). A BARE strongs_base ('4151') won't equal 'G4151' → NULL lemma (missing, not
  wrong). Under the OLD `SUBSTR(strongs_base,2)` join it was worse — a bare base shaved a DIGIT
  → WRONG lemma. (2026-06-03, pre-Phase-1: a rebuild left 592k bare → G2206 ζηλόω rendered as
  ἄκρον/G206. Fixed by `UPDATE words SET strongs_base='G'||strongs_base WHERE strongs_base GLOB
  '[0-9]*'`.) tests/test_strongs_join.py + test_build_invariants.py lock this.
- `words.strongs` is intentionally LEFT BARE ('2206', dotted '2321.1'); the frontend renders
  `G{strongs}`. Only strongs_base carries the prefix.
- DOTTED-NUMBER CAVEAT: strongs_base drops the `.N` (built as `st.split(".")[0]`), so a dotted
  ABP number that's a DIFFERENT word than its base resolves the base's lemma through the join.
  The `dotted_lexicon` side table + a COALESCE in the word card correct this; form-variants like
  1510.x (forms of εἰμί) correctly keep the base lemma.
- **NO-ENTRY DOTTED = LEAK (standing, 2026-07-10 corpus-defect fire).** Every dotted exclusion
  in the pipeline (ranker, def-engine feed, floors) works by `dotted_lexicon` MEMBERSHIP — a
  dotted number with NO row there silently rides into its BASE word's evidence and its chips
  serve the base word's card on click. 86 such numbers exist (the builder's `no_entry` bucket;
  they have no `abp_ext` dictionary entry, so `build_dotted_lexicon.py` can't auto-derive them —
  hand-classify into its `HAND_OVERRIDES` dict, never a hand row). Live bites: δόμα's floor
  voided by a δόμος leak; δίκτυον's live card cites 5 lattice-verse leaks (ruling chain queued).
  Consequences: any no-entry dotted row found at a pre-floor pull = feed contaminant by default;
  ranker occ counts are CEILINGS until the class is triaged.
- **AUDIT RULE — dotted-number blindness (hard, standing; two false positives 2026-07-02).**
  ANY Strong's-number audit query operates on the FULL dotted number by DEFAULT (raw `strongs`,
  e.g. `G1246.2`). Grouping/counting on `strongs_base` — which strips the `.N` — is allowed
  ONLY with an explicit reason. Any **"count = 0"** or **"orphan/contaminated rows"** finding
  MUST check dotted variants BEFORE it counts as a finding: a base showing 0 says NOTHING about
  its dotted neighbors, and a base-group can lump a real dotted word (διὰ κενῆς G1246.x) onto an
  unrelated hapax and look like contamination. This matters most at SCALE — the Lexica-def
  rollout arc (~3,954 words) run dot-blind would manufacture false positives wholesale.
  - **Query-shape corollary (standing, 2026-07-11):** match a Strong's number in `words` as
    `strongs='NNN' OR strongs LIKE 'NNN.%'` — NEVER a bare prefix `LIKE 'NNN%'`. Short numbers
    sweep neighbor series ('227%' also matches the whole 2270-family); a bare prefix is safe on
    4-digit numbers only by accident.
- `kjv_strongs.strongs_id` is also fully prefixed (always was).
- Always single-match in SQL: `WHERE w.strongs_base = 'G4151'`.
- After ANY words rebuild: `SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'` = 0.
- The AI SQL-gen prompt (`_AI_SYSTEM_TMPL` in ai.py) matches this invariant (Batch B,
  2026-07-03; the old bare/SUBSTR examples were the last holdout).

### abp_surface
`(verse_id, position, form, translit)` side table of the PRINTED (inflected) Greek per ABP word,
feeding the word-study side-card "in this verse" line (ABP's source has no Greek surface words).
Built read-only by `scripts/build_abp_surface.py --bh ~/bible-db/bh_scrape.db` (PA-only data
step; DROP+rebuilds only its own table, never words/verses). SOURCE = ABP's OWN printed Greek
from `bh_scrape.db` `bh_words.greek` (the BibleHub ABP scrape) — same text as `words`, so it
matches ~91% (Rahlfs/TAGNT capped lower — memory `project_bsb_words`). `/api/chapter` LEFT-JOINs
it only if present (deploy-safe). bh's Greek
is accent-only (no breathing marks), so `strip_marks` stores a form ONLY when it differs from
the lemma by ENDING (no echo lines) → 56% of words show a line. **Backfilled 2026-07-11 by
`scripts/backfill_abp_surface.py`** (+13,851 rows → 359,288): the builder's strict left-to-right
aligner fails where ABP's printed ENGLISH order (words.position) diverges from the scrape's Greek
order (bracket reorders, postpositive particles); the backfill pairs failed slots with leftover
scrape tokens by Strong's number within the verse, refusing on any count mismatch. Re-run it (then
translit) after any build_abp_surface re-run. Characterizer = `scripts/audit_surface_coverage.py`
(read-only; true divergence residual ≈0.65% of content slots — 30,126 of the old "gap" were
Hebrew-numbered OT name slots that can never match Greek, the PN backfill's bucket). Mode-three
interlinear's Greek line falls back form→lemma→name (`greekLineForWord`, 56-library-order-logic);
JP RULED 2026-07-11: no fallback marker. Surface translit FILLED by
`scripts/build_abp_translit.py` (SBL romanization matching the lexicon headword style; the
rough-breathing 'h' is read from the lemma since bh forms have no breathing; re-run after any
position-shifting rebuild). Full record: memory `project_bsb_words`.

### lexicon
Greek Strong's definitions. Has an indexed `lemma_plain` (accent-stripped/lowercased/
final-sigma-folded lemma) — the fast EXACT key the Word-study search matches first (`bdb` has it
too). Built by `scripts/add_lemma_plain.py` (folded into `load_lexicon.py` for the Greek side;
re-run after a lexicon OR bdb reload). Word-study lookup short-circuits on an exact `lemma_plain`
hit, only falling to the slow substring scan when the typed word isn't a headword. **It can
silently VANISH: found MISSING on the live db 2026-06-30 (a reload had dropped it), which left
the exact-match fix asleep — re-applied 2026-07-01. VERIFY the column exists after any reload**
(`PRAGMA table_info(lexicon)`). Ask-corpus's exact-lemma pin uses it too (`_resolve_exact_lemma`
in ai.py). Memory `project_lexicon_finders`.

### lsj / abp_ext
`lsj` — Liddell-Scott-Jones Greek lexicon (display-only cross-reference, never generative).
`abp_ext` — extended ABP data. LSJ word-study summaries live in `lsj.summary_json` /
`abp_ext.summary_json` (see docs/claude/ai.md, cache section).

### dotted_lexicon
Corrected headword for ABP dotted Strong's. Side table in bible.db (built on PA, not in git)
mapping the full dotted number (`G###.N`) → its OWN lemma + romanization, for dotted numbers
that are a genuinely DIFFERENT word from their base (ABP parks its added words at "nearest
Strong's + a dot", so the base lemma is the alphabetical neighbour — G180.2 ἀκατασκεύαστος vs
base G180 ἀκατάπαυστος). `chapter_text`/`verse_words` COALESCE it over the base `lexicon` join;
joined only if present (deploy-safe). Built by `scripts/build_dotted_lexicon.py`, audited by
`scripts/audit_dotted_lemmas.py`. Phrase idioms are pinned via `PHRASE_OVERRIDES` in
build_dotted_lexicon.py (ἀνὰ μέσον). Full record: memory `project_dotted_strongs_lemma`.

### pn_binding / tipnr_entities / tipnr_entity_refs
The Issue-2 entity-binding tables (PA-only, NOT in git; rebuilt by
`scripts/build_entity_binding.py --apply`, which writes ONLY these, never words/verses).
`pn_binding(book,chapter,verse,name,entity_uniq,kind,rule,render,hot,tier)` keyed
(book,ch,vs,name) maps a PN occurrence → its verse-correct TIPNR entity (render=1 rows only; a
floor = no row → Fix A); `tipnr_entities` = the entity's own card content (uniq/head/section/
gender/area/descr/summary/bases/parents+offspring, kin for PERSONS only); `tipnr_entity_refs` =
its reference list. Served by `/api/metav/entity` → the `.pnbound` card. Re-run `--apply` after
a words rebuild (re-tiers from live metaV each run). Memory `project_entity_resolution_rebuild`.

### tipnr_metav_link
Cross-links a bound TIPNR entity → its rich MetaV record (PA-only, NOT in git).
`(uniq, kind, metav_id, rule, score, margin)`; kind='person' LIVE (1,625 rows, 2026-07-05)
mapping a person entity → `metav_people.person_id` so the panel renders the rich David-style
card (place edition reserves kind='place'). **SERVED since 2026-07-05:** `/api/metav/entity`
adds a `metav` rich-card field via ONE join (gated: `section='person'` + NOT `is_people_group`
+ a born/died-or-≥2-kin bio bar), fallback rich → thin TIPNR → Strong's; frontend
`MetavPersonBody` (shared with the name card) fills the bound card under the TIPNR spine.
**Titles ship per-referent** (the seven pharaohs each link to their own record; the composite
`Pharaoh@Exo.1.11` correctly UNLINKED) — do NOT widen the link-build title check, it'd delete
good links. Built by `scripts/build_metav_person_index.py` (MetaV CSVs → staging
`metav_index.db`, PA-only) + `scripts/build_person_metav_link.py --apply`; re-run BOTH after a
words rebuild. Memory `project_metav_person_link`; spec `HANDOFF_metav_person_link.md`.

### word_gloss
Plain-meaning lemma gloss for the word card (`strongs` → `gloss` + `source`). Side table in
bible.db (built on PA, not in git; ~17.5k rows). Greek = Dodson base + TBESG fill + overrides +
dotted-by-lemma; Hebrew = TBESH + overrides. Joined via `core.word_gloss_cols()` (ABP) and
`core.word_gloss_join()` (KJV/BSB chapter endpoints — folds a Hebrew byform in SQL); Hebrew
reader does a cross-db lookup (heb.db can't join bible.db). All deploy-safe, aliased
`AS kjv_def`/returned as `lemma_gloss`. Built by `scripts/build_word_gloss.py`
(`--summary`/`--apply`). ABP + KJV/BSB/Hebrew cards + the Word study tab ALL LIVE (2026-06-23).
Full record: memory `project_word_card_gloss`.

### lexica_def — the Lexica dictionary
Our OWN verse-grounded definition per word (written from the Bible's own usage, not LSJ's
classical glosses). Side table in bible.db (built on PA, not in git). **Real columns are only
`strongs / lemma / translit / def_json / synth_ver / updated` — everything listed next is a
FIELD INSIDE the `def_json` JSON, not a column (a query on `raw` errors; 2026-07-10 lesson
from the blast-radius sweep — search `def_json` for card-content checks).** One row = frozen fields
`sense_headlines`/`senses_block`/`range`/`gloss_notes`/`coverage` + `sense_prov` (per-sense
LXX-provenance flag, Option B) + `fork` (contested-word readings + a Study-graph link; also
carries `gloss` + two hand-authored SEAM axes `divergence_type` (referent|content|loaded) +
`lead_flip` — set in the `CONTESTED` register, no model, written on any `--resplit`) + `verses`
+ `audit` (citation-gate result; since 2026-07-10 also `audit.floor_diff` — the #30
floor-vs-ship placement record, present ONLY when the apply ran with `--floor <agreement json>`;
its `floor_unseen` list sees qualified refs only until the #28 shorthand expander lands)
+ `raw` (so a better splitter re-splits with NO model call).

Built by `scripts/build_lexica_def.py` (frozen `VERSE_PROMPT` → Sonnet → split → citation gate →
fork → write; `--apply` build / `--resplit --apply` re-split stored raw, free; surgical raw
typo-fixes via `scripts/fix_lexica_raw.py`, no model call — accepts an empty `--new`, a text CUT).

**The `CONTESTED` fork register is `contested_register.py` (repo root, 2026-07-01) — the ONE
copy, imported by build_lexica_def + trial_lexica_def + views_lexica; edit it there, never
re-copy.**

**The citation gate BLOCKS the write (2026-07-01, was report-only):** `validate_entry` rejects a
row with a real/no-verse miss (tagging misses stay non-blocking, logged);
`--force-gate-bypass "reason"` stores the reason in `audit.bypass_reason`, stamped only on a
word whose gate failed.

Served by `views_lexica.py` `/api/lexica/<strongs>` → the `LexicaBody` card
(20-shared-components, BESIDE `LsjBody`). BOTH the Library word card (`30-detail-panel.jsx`
`case "lsj"`) AND the Word-study card (`80-lexicon.jsx`, 2026-07-03) fetch `/api/lexica` and
render the SAME `LexicaBody`/`StructuralBody`/idiom body — parity is structural, not hand-kept.
**Word-study gates the Lexica body to GREEK numbers**: Library never shows `LexicaBody` for a
Hebrew word (it pushes the `bdb` section, not `lsj`), so a Hebrew number keeps its BDB
definition on both surfaces. **Also `/api/lexica/seams`** (read-only, same file) — every row
that carries a `fork`, feeding the Seam index Study module (`SeamIndex` in 55-study.jsx). After
adding/moving a `divergence_type`/`lead_flip` in `CONTESTED`, run
`build_lexica_def.py --resplit --all --apply` on PA to write it into stored forks (free).

**Two serve-time guards in `/api/lexica/<strongs>` (2026-07-01):** (a) a `LEXICA_ALIASES` map
(the register's `aliases` fields PLUS the standalone `SPLIT_LEMMA_ALIASES` dict — plain
corpus-tagging splits that aren't contested words, 2026-07-02) serves the ONE real row for a
word ABP tags differently — KJV/BSB clicking charis ask for G5485, get the G5484 row. A
NUMBERING CROSSWALK (`alias_note`) shows the standard↔ABP pairing in the card header, computed
by the ONE shared helper `contested_register.alias_note_for()` — INVARIANT: any new card/route
that needs it calls that helper (both `/api/lexica` + `/api/lexicon/profile` do), never a
private copy. Full record + the LSJ-404-ride + `SPLIT_LEMMA_ALIAS_NOTES` pool caveat: memory
`project_ai_search_architecture`. (b) a fork BACKSTOP — a `CONTESTED` word whose stored row has
no `fork` (built before it entered the register, the θεός/κύριος batch-1 gap) 404s + logs loudly
instead of serving a one-sided entry (card falls to LSJ).

**PUBLIC since 2026-06-25** (`LEXICA_ADMIN_ONLY=False`; a word with no entry 404s → the normal
LSJ card, deploy-safe; flip the flag back to re-gate). LIVE on ~18+26 words: the 6 pilot
(psychē + the 5 contested forks dikaioō/charis-G5484/aionios/sarx/ekklesia) + 12 from full-build
BATCH 1 + the frequency-rollout Batch One (26 words, 2026-07-03).

**Frame-leakers are HAND-PINNED** (dikaioō/charis/aionios): `pin_core` in `CONTESTED` lifts the
neutral fork core to `entry.pinned_core`, which LEADS the card while the model's framed senses
drop below as "Attested uses" (`assemble()` display override, re-applies via `--resplit`, no
model call). Full record + the V3 prompt-lock: memory `project_lexica_dictionary`.

**Batch-build safety gate = the agreement reviewer `scripts/lexica_agreement.py`** (read-only,
PA-only; draws a word N×, per-verse SUPPORT+COMPANY tells a fold from a hole) — it certifies
PROMPT stability, NOT the written draw (the `--apply` citation gate does that), so a reviewer
re-run before a write is OPTIONAL once the prompt is diff-locked. 3-tier ship-gate + cutoff
occ ≥ 2 (splitter split3): memory `project_lexica_dictionary` + `AUDIT_lexica_rollout.md`.

**θεός G2316 + κύριος G2962** are membership-only forks (no `pin_core`, the sarx/ekklesia
pattern) — loaded-referent words that shipped pure-engine in batch 1, then were hand-forked. Fork
content (θεός's John 1:1c narrow fork, κύριος's OT-YHWH-applied-to-Jesus set) lives in
`contested_register.py`; full record: memory `project_lexica_dictionary`.

**LXX-provenance note (Option B) LIVE 2026-06-25:** a subordinate "rests on Septuagint
(Greek-OT) usage" flag on senses grounded ≥80% OT (≥4 OT refs) — `sense_provenance()` derives it
from stored citations (book = OT/NT), NO model, recomputed on every build/`--resplit` (`--all`
rolls it across the batch). Threshold set against a census —
`scripts/audit_lxx_provenance.py --preview`.

**COVERAGE ENGINE (2026-07-02, `lexica_coverage.py` at repo root):** piece A = collocation
pre-check (token-level PMI, floor+threshold+0-in-draw, `PMI_MIN=4.0`; warn-only build hook) +
piece B = a `coverage_audit` field on every entry (tight collocations/renderings cited-or-not +
per-sense thin/circular via `contest_verses` in the register). Populated by
`scripts/populate_coverage_audit.py` (narrow — splices ONLY that key, never `--resplit`).
Read-only audit `scripts/audit_lexica_coverage.py --coverage`. Piece C (stratified sampling)
DEFERRED. NOT wired to the card UI — stored data only. Full record: memory
`project_lexica_dictionary`.

### Structural / function-word card
A word-card entry TYPE (beside the Lexica dictionary + LSJ) for words whose meaning resolves
OUTSIDE the lexeme (copula, prepositions, …): states the word's grammatical FUNCTION + the
construction relations it appears in (provenance tag GRAMMAR). Hand-authored in `structural.py`
(a code dict keyed by BASE Strong's — NO model, NO PA data build; normal code deploy), served by
`views_lexica.py` `/api/lexica/<strongs>` which resolves a structural base FIRST (own gate
`STRUCTURAL_ADMIN_ONLY`, currently False = public).

**`structural_entry` routes a dotted number three ways through ONE gate (invariant — keeps every
card seam-free):** a decodable FORM of the base → the card + its own parse (εἰμί's ~7,800
conjugates, decoded from the dot); a declared frozen IDIOM (ἀνὰ μέσον G303.1, in `_IDIOMS`) → a
one-line CONTENT note (`kind:"idiom"`, "Phrase/Idiom" header — its card hero shows the `_IDIOMS`
phrase + a hand-authored `translit` VERBATIM, never the dotted_lexicon lemma/romanizer that
mangle a two-word phrase, and the abp_surface "in this verse" line is suppressed; the reader
chip + word-study search read dotted_lexicon directly so the same phrase is pinned there via
`PHRASE_OVERRIDES` — 2026-06-26); ANY other dotted child (a different word ABP parked at
"nearest Strong's + a dot", e.g. G303.2 "stairs") → None → falls through to its own word entry,
so a parked number never borrows the card.

Card = `StructuralBody` (20-shared-components.jsx) with a **glance/full split** (the "Function"
tab = the finding + a use-boundary pointer; "Full entry" = scope/relations/cross-refs — eimi
splits, shorter prepositions collapse to one view); `30-detail-panel.jsx` branches `case "lsj"`
on `lexica.kind` ("Grammar"/"Idiom" badge); `.gram-*` CSS.

The structural inventory is **COMPLETE**: εἰμί (copula) + the prepositions, conjunctions,
particles/negatives (incl. the **οὐ/μή MECHANISM CUT** — two lexemes split by fact vs non-fact,
with the compounds inheriting), the article ὁ, **ἵνα** (G2443 — purpose; exemplar Mark 3:14, the
worked example for the CONTEST RULE below), and the **REFERENT-RESOLUTION batch** — a SECOND
structural class beside εἰμί's complement-resolution: a pointer with no content of its own, the
antecedent recovered from context (οὗτος/αὐτός/οὐδείς/μηδείς; ὁ δέ rides the article card;
ἰδού SCOPED OUT as forward-pointing deixis). Full roll-call + per-word findings + dates: memory
`project_structural_deictic_cards`. Exemplars are verbatim-ABP, verified live before commit.

**STRUCTURAL-WORD CONTEST RULE** (ἵνα = the worked example): a structural word with SETTLED
grammar but a doctrinally-CONTESTED application at specific verses does NOT get a fairness-gate
fork — the card stays grammatically honest, and the loaded verses point OUT to an argument graph
where the contest is mapped (the lexeme is innocent; the passage is contested). UNLIKE a
content-word fork, where the lexeme's OWN senses fork (dikaioō → salvation_how). ἵνα's pointer
is WIRED: the `hina_hardening` argument graph is built + published and the ἵνα card carries a
`contest_graph` breadcrumb (graph id + the 3 loaded verses) to Study › Graphs, rendered by
StructuralBody in Full entry. See memory for the graph build.

**Card verse lines are verbatim ABP** (a Greek-construction card — ABP is the right
source even for a KJV reader). Full record + the locked build rules (cut-by-form /
list-by-context, verbatim-ABP, contested-fork prepositions, the dotted-routing gate): memory
`project_structural_deictic_cards`.

### Other bible.db tables
- `books` — book metadata (name, testament, regex).
- `ai_search_cache` — cached AI query results + TSK synthesis (see docs/claude/ai.md).
- `kjv_verses` — KJV full verse text (31,102 verses).
- `kjv_words` — KJV word-level tokens with position and italic flag (italic=1 = translator add).
- `kjv_strongs` — KJV word → Strong's mapping (strongs_id fully prefixed).
- `bdb` — **MISNAMED: actually the STRONG'S HEBREW dictionary, NOT Brown-Driver-Briggs**
  (8,674 rows = H1–H8674, one-line Strong's glosses; genuine BDB is ~10k+ root-organized and
  wouldn't land on that count). The app has NO real BDB. The table NAME stays (threaded through
  queries/code/CSS `bdb-*`); only USER-FACING labels were corrected to "Strong's Hebrew"
  (2026-07-03). Source = a public-domain Strong's-Hebrew dump (1890 text, PD, no CC credit).
  If real BDB is ever wanted it's PD + digitized (OpenScriptures) — a new-source decision.
- `pericopes` — section headings (book, chapter, verse, heading); from bh_scrape.db.bh_headings;
  displayed in all reader render modes via `/api/chapter`'s LEFT JOIN + `.pericope-heading`.
- `bsb_verses` — Berean Standard Bible verse text (public domain), mirrors kjv_verses.
- `bsb_words` / `bsb_strongs` — BSB per-word interlinear (LIVE 2026-06-15; 386,063 words /
  381,948 Strong's / 66 books), mirroring kjv_words/kjv_strongs:
  `bsb_words(word_id, book_id, chapter, verse_num, verse_pos, word, italic, punc, form,
  form_translit)` + `bsb_strongs(id, word_id, strongs_id)`. strongs_id fully H/G-prefixed
  (locked in test_build_invariants.py). `form` = the original word AS PRINTED + `form_translit`
  its transliteration — they feed the word-detail side-card "in this verse" line; the chip top
  line + interlinear stay the dictionary lemma. `/api/bsb/chapter` selects them only if present
  (PRAGMA guard, deploy-safe). Built by `scripts/load_bsb_words.py` from the Berean project's
  Strong's-tagged tables (`bereanbible.com/bsb_tables.tsv`, CC0). PA-only one-time data load;
  `--dry-run` checks the tokens rebuild live bsb_verses text before writing. Source-format
  gotchas + deploy step: memory `project_bsb_words`.
- `cross_references` — id, verse_id, verse_ref_id; both IDs map to kjv_verses.verse_id;
  386,518 rows from Torrey's TSK. Join:
  `cross_references cr JOIN kjv_verses kv ON cr.verse_ref_id = kv.verse_id`.
- `<book>_words` / `<book>_verses` — non-canonical texts, each in its OWN two tables, walled
  off from the Bible's tables and search/word counts. Built by `scripts/load_extra.py`; served
  by `/api/extra/<book>/chapter/<n>`. English-only texts load with an empty words table. LIVE
  (per-group loaders under `scripts/`, wired in `NONCANON` in static/src/60-library.jsx,
  auto-loaded by deploy.sh):
  - Septuagint Apocrypha — 16 Brenton books, English-only (`scripts/apocrypha/load_apocrypha.py`)
  - Pseudepigrapha — 1 Enoch, 2 Enoch, Jubilees, 2 Baruch, Apoc. Abraham, Assumption of Moses,
    English-only (`load_pseudepigrapha.py` + `scripts/enoch/`)
  - Testaments of the Twelve Patriarchs — 12 separate English-only books
  - Apostolic Fathers — 14 books with FULL GREEK INTERLINEAR: Didache, 1-2 Clement, 7 Ignatian
    letters, Polycarp, Martyrdom of Polycarp, Barnabas, Diognetus, Shepherd of Hermas. Built by
    `scripts/apfathers/build_af.py` (+ `build_hermas.py`), loaded by `load_apfathers.py`.
    Greek+lemma from Brannan/Lake (CC-BY-SA), Strong's via openscriptures + Dodson glosses,
    English from Lightfoot. Memory `project_noncanonical_texts` (pipeline + gitignored raw/).

## Separate DB files (NOT bible.db; all gitignored + PA-only)
- `notes.db` — user accounts/notes/highlights/journals + `visits` (owner-only visitor stats) +
  `password_resets` + `corpus` (saved Ask-corpus conversations, synced via `/api/corpus/sync`
  same id/newer-wins/tombstone as notes) + `ai_usage` (Ask-corpus daily spend caps; user_id 0 =
  site total). Detail: docs/claude/frontend.md (Notes/accounts).
- `esv.db` / `niv.db` — gated texts (`load_esv.py` / `load_niv.py`; `views_esv.py` /
  `views_niv.py`). ESV+NIV are berean-gated (roles below).
- `heb.db` — **PUBLIC** Hebrew OT interlinear: `heb_words` (hebrew, strongs H-number, morph,
  gloss, translit, grammar) + `heb_verses`, all 39 books from STEP **TAHOT** (CC BY). Loaded by
  `scripts/load_hebrew.py`; served by PUBLIC `views_heb.py` (`core.heb_db()`). Routes:
  `/api/hebrew/status`, `/api/hebrew/chapter/<book>/<ch>`,
  `/api/hebrew/verse-words/<book>/<ch>/<v>`, `/api/hebrew/strongs-count/<H#>`. heb.db is ALSO
  the Hebrew-word EVIDENCE source for Word study + Ask-corpus + SEO (not just a reading text) —
  memory `project_hebrew_source_swap`. Full record: memory `project_hebrew_ot_interlinear`.
- `study.db` — authored study modules; **the ONE irreplaceable file** (hand-authored argument
  graphs, no rebuild script). One `entries` table (row per topic/graph/name; json body + type +
  status). Served by `views_study.py`; the Study tab (`static/src/55-study.jsx`), sub-switch
  Topics · Graphs · Seams. **The WHOLE Study surface is ADMIN-ONLY (2026-07-01):** the nav link
  shows only for owner/admin AND a single `@bp.before_request` (`_study_admin_only`) 403s every
  `/api/study/*` route for non-admins — one gate, all 8 routes. `/api/lexica/seams` is
  hard-gated the same way (403, flipped from empty-200; the public per-word `/api/lexica/<strongs>`
  is UNTOUCHED). Consequence, intended: gating for-name + for-verse retires the reader's Nave's
  block AND "In studies:" line for non-admins (client no-ops on the 403). SEAMS is a NON-study.db
  surface — read-only over `lexica_def` fork data; `load()` short-circuits `mod === "seam"`.
  **Uniform master-detail shell (2026-07-01):** LEFT rail = list (shared `study-row`), CENTER =
  content (TopicPage / GraphPage / `SeamPriors`), RIGHT = inspect (ZoneEmpty this phase —
  per-item detail wiring DEFERRED). One top-strip switcher (`study-sub`); `seam-rail` RETIRED.
  Inspect floats top:0 (`.study-rstack`) with a `view-study`-scoped account-pill offset. The old
  centered column (`.study-view max-width:820`) survives for MOBILE only. `.study-*` CSS only —
  never touch shared `.detail-*`. GRAPHS = argument maps (admin-only): shared pool of CLAIMS +
  per-tradition LINKS, provenance (text/lexicon = grounded; tradition/conjecture/inference =
  not) + strength (solid/contested/weak), stress-tested by `argmap.py`. Drawn as a left→right SVG
  chart per tradition. READ-ONLY in-app — authored via `scripts/add_study_graph.py`. Topics open
  READ-first; a "Preview as reader" admin toggle. Verse text = ABP prose (KJV fallback). Curation:
  readers see PUBLISHED topics only (the ~1817 imported Nave's/MetaV concept topics are deprecated
  + soft-deleted — Topics is hand-authored only now; KEPT: the 696 `type='name'` name-topics feed
  the Library Nave's sidebar). Editor verse
  lookup = `POST /api/study/verse` (normalizes refs via `_canonical_ref`). Topic INTROS are
  AI-written text-first Berean (`✦ Draft with AI`; `_draft_intro`/`_INTRO_SYSTEM`). PERF: whole
  entry resolves in one batched pass (`_resolve_map`) + `_RESOLVED_CACHE`. Scripts:
  `add_study_topic.py`, `add_study_graph.py` (dry-run default / `--apply`),
  `load_study_topics.py` (**DEPRECATED, do NOT re-run: refills the deprecated concept list**),
  `generate_topic_intros.py`, `publish_topics.py` (`--names` for metaV name-topics),
  `find_topics.py`, `find_topic_dupes.py`, `merge_the_dupes.py`, `deprecate_concept_topics.py`
  (`--undo` reverses). Full record: memory `project_study_modules`.

## Accounts / roles / gated texts
Roles nologin / user / berean / admin — a `role` column in `notes.db users`; gates in
`views_notes` (`is_admin()`, `is_berean()` = berean-or-admin, `is_logged_in()`). `OWNER_EMAIL`
is ALWAYS admin (bootstrap, even before the column migrates). user (any sign-in) = AI search
(login-gated, costs money); berean = ESV + NIV; admin = visitor Stats + the in-app Admin page
(sets others' roles). Sign-in is email or Google; Google needs `GOOGLE_CLIENT_ID` + the
`google-auth` package and the button hides if either is missing (a code-only deploy never
breaks). Full records: memories `project_user_roles`, `project_esv_audio`,
`project_visitor_stats`.

## Audio sources
ESV = Crossway's own API (api.esv.org, `ESV_API_TOKEN` in the WSGI — whole-Bible Max McLean;
`views_esv._crossway_audio_url` follows the 302 to the signed mp3), FCBH (`FCBH_API_KEY`,
NT-only) as fallback. KJV = public-domain audiotreasure.com, no key (voice set `KJV_AT`;
Job/Song/Philemon/2–3 John/Jude fall back to music set `KJV_FF`). BSB = public-domain, no setup.
NIV = no audio source (dead end).

## Book abbreviations
ABP verses table uses: Mar (Mark), Joh (John), Php (Philippians), Jas (James), Heb (Hebrews).
NT_BOOKS, BOOK_ORDER, BOOK_LABELS in static/src/00-core.jsx use the same set; `_KJV_BOOK_ID` in
app.py matches.

## MetaV (person/place sidebar)
- Tables: `metav_people` (+_aliases, _groups, _relationships), `metav_places` (+_aliases; has
  lat/lon, strongs_g). Looked up by NAME (not strongs). Frontend fetches person + place in
  parallel; toggle shown when both exist.
- **KJV/BSB reader word → metaV name gate (2026-06-23):** the lookup fires only when the word's
  Strong's is a NAME (proper noun or gentilic) per `core._HEB_NAME_STRONGS` — a startup set
  built from heb.db morphology by DOMINANT use (`app._build_heb_name_cache`, mirrors
  `_FUNCTION_STRONGS`; endpoints send `heb_name`, `30-detail-panel.jsx` gates `kjvIsPN` on
  `entry.hebName`; Greek/NT + no-heb.db fall back to capitals). Killed bogus place cards for
  common words BSB caps mid-verse without hiding clans BDB tags "Adjective" (Philistines).
  Place comments strip a bare wiki URL. Memory `project_metav_expansion`.
- Hebrew proper nouns: route to metaV (person/place) with BDB stacked BELOW. `isHebrewWord`
  (any H#) drives BDB; `isHebrew = isHebrewWord && !isPN` drives the Hebrew hero/LSJ suppression.
- Default tab (Phase 6): trusts the word's OWN tipnr type via `pn_types` (a SET —
  'person'/'place'/'person,place'). A clean single type is authoritative; ambiguous or absent
  falls back to the strongs_g heuristic (metav_places.strongs_g holds only G-numbers, so OT/H
  words fall through to Person unless pn_types pins them). The Person/Place toggle is SUPPRESSED
  when pn_types is a clean single type.
- tipnr schema: `entity_types` column holds the type SET so a strongs shared by a person AND a
  place keeps BOTH (was a PK collision: last-imported type won → Adam H121 read 'place').
  `entity_type` = legacy single token. Migration adds the column at PA startup; re-run
  import_tipnr.py after any rebuild. pn_types (the set) is trustworthy.
- Gentilics (`/ites?$/`): card labeled "People / Clan", place header "Homeland", AI summary
  fires on the clan tab. Kept as persons (Table-of-Nations genealogy is the value).
- AI curation: `/api/metav/ai-description/<name>` — Haiku, 1-2 sentences, SCOPED to the clicked
  book/ch/verse. **VERSE-GROUNDED (2026-07-05, "G"): fed the displayed verse text + the reader's
  translation identity (`_displayed_verse`), told to explain the name AS RENDERED there — NOT
  fact-check the shown text against Hebrew/English/other traditions** (it was denying ABP's
  Greek/LXX forms, e.g. "Antilebanon isn't in the verse" at Deu 1:7 / Jos 1:4). Cache key +
  fingerprint include verse+translation (`pn:<name>:<bk><ch>:<v>:<translation>`). Fills entries
  with no metaV/BDB data. The place endpoint withholds the map pin when the name maps to >1
  place or the matched row lacks its own coords. Both = **Fix A**, the permanent floor under
  whatever the binder can't bind.
- **Multi-referent guard on the NAME path (2026-07-05).** `/api/metav/person` is the UNBOUND
  path (called only when no verse-bind owns the card). If the bare name is borne by >1 man it
  returns `{"ambiguous":true}` and serves NO bio. Signal = several `metav_people` candidates
  (name OR alias) OR
  several TIPNR person entities under the surface name; the metaV+alias leg is PRIMARY.
  Single-referent names (David) still serve rich. `_name_is_multi_referent` in views_metav.py.
- **VERSE-BOUND ENTITY CARD — the Issue-2 rebuild, LIVE 2026-06-28.** A PN click first asks
  `GET /api/metav/entity/<name>?book=&chapter=&verse=` for the verse-CORRECT TIPNR entity (from
  `pn_binding`); when bound it LEADS the rail with a sourced `.pnbound` card (canonical name +
  TIPNR description + kin + region + "Matched to this verse" + a TIPNR badge), FOLLOWED by ONE
  standard word-occurrence control keyed to the entity's OWN number — only the line for the text
  being READ. (EVERY word card shows just the active text's occurrence line — 2026-06-28; the
  full cross-Bible breakdown lives in Word study.) A bind GATES the whole name-based metaV fetch
  (kills the name-guess person/place card + Groups + Nave's + place-LSJ at once). 404 → the old
  name-path + Fix A, byte-same (deploy-safe). 14,803 render binds, zero confident-wrong; TIPNR
  is the identity spine, metaV is enrichment only. Engine = **`entity_resolution.py`** (repo
  root, pure logic); tables built by `scripts/build_entity_binding.py --apply`.
- **Bound places SHOW a map again (2026-07-05):** coords come THROUGH the entity endpoint
  (`_place_coord_rows` + `_pin_from_rows`, pinning the coordinate MOST rows agree on). The bound
  path prefers rows whose OWN name matches the entity over rows merely ALIASED to it (so a
  name matching only via an alias declines rather than pinning the aliased place's coords).
  Interim guard; real per-referent fix = the parked OpenBibleInfo ingest.
- **People/Clan render (2026-07-05, "C"):** a gentilic word bound to its eponymous-ancestor
  PERSON entity (Hittites→Heth, Jews→Judah — TIPNR models peoples that way, ~819 binds) renders
  "People / Clan", drops the ancestor's Parents/Children, titles with the people term + a
  "Descended from X" line. Classifier `is_people_group` in `entity_resolution.py` (ONE list,
  shared with the audit; bare `-im` excluded — collides with Ephraim/Miriam). A hyphenated click
  ("Beth-el") RETRIES hyphen-blind against `pn_binding` (bind keyed on english_head "bethel").
  Full record: memory `project_metav_expansion`.
- **Bound-card occurrences:** these PNs carry a real Strong's on `strongs_base` but a bare
  `strongs='*'` (TIPNR backfilled the number), so the bound card un-gates the standard
  occurrence sections and the ABP count comes from `/api/strongs-count/<n>?by=base`. OT names
  key to HEBREW on purpose — TIPNR's Greek form is a STEP-extended number (G9827) our lexicon
  lacks and ABP never uses; the ABP Greek occurrences still surface via the Hebrew base.
  **Don't re-pitch a "pure Greek" re-key.** (The old "Appears N×" TIPNR ref-list was tried +
  removed — it listed verse pointers, some without the word.) Full record + build order:
  memory `project_entity_resolution_rebuild`.
- CRITICAL: the lexicon join `l.strongs_g = w.strongs_base` structurally prevents a Hebrew
  H-number matching a Greek row (the old SUBSTR+LIKE guard let H121 slip → bogus G121 lemma
  broke Hebrew-PN metaV). Applies to BOTH chapter_text and verse_words.

## BibleHub ABP scrape
- Scraper: `scripts/scrape_biblehub_abp.py` — captures strongs, greek_pos, italic (last-word
  heuristic), strips `[ ]` brackets. The scrape (`bh_scrape.db`) is complete.
- The words table is rebuilt from `bh_scrape.db` — see `/rebuild-words` + the words section.
- Do NOT add conjugated manuscript forms — the audience are non-Greek readers (standing rule).

## Two-ending adjectives
Two-ending Greek adjectives (masc & fem share one form) show "Masculine/Feminine" on the
word-study card when the morph source never resolves them — `decodeMorph` (00-core.jsx) checks
`TWO_END_SOFT_OT/_NT` in `static/src/00b-two-ending.jsx`, generated by
`scripts/build_two_ending.py` (re-run after a words rebuild). Feminine/Neuter tags + words the
source resolves are left alone. Memory `project_two_ending_gender`.
