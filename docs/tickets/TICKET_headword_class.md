# TICKET — Head-word defect class: wrong heads, blank-star rows, wrong highlights

Status: OPEN — root cause traced 2026-07-16. Fix rides `/rebuild-words` (JP ruling R-1:
rebuild approved; batch inventory below). References `docs/tickets/TICKET_missing_strongs_pn.md`
(piles 3–5 = this class) and `docs/PROVENANCE_CONTRACT.md`.

## The three symptoms are ONE defect class (confirmed by trace)

(a) Starred names looking up trailing common words ("Hezekiah said," → head "said").
(b) Wrong English words attached to lemmas ("renders as" counts, English finder).
(c) Corpus-search highlighting painting stopwords or the wrong word.

All three consume the same stored value: `words.english_head`. The stored value is wrong
for one class of slots, plus one shape where the row has no English at all. Library
in-text search (the eSword-style search) is NOT affected — it highlights by re-matching
the typed query against the verse prose (`views_search.py` + `59a-library-helpers.jsx
highlightTerms`), never touching english_head.

## Root cause — two build-time defects

**RC-1: the head pick is "last non-function word," with no name preference.**
`scripts/parse_abp.py:80-124 _head_word()` walks the slot's tokens from the END and
returns the first token not in `_FUNCTION_WORDS`/`_HEAD_STOP`. Its own docstring
documents the failure: `'the LORD said' -> 'said'`. "said/saying/field/area/woman/man"
are content words, so the stoplists never skip them, and a trailing verb always beats a
leading proper name. This is the documented-but-underestimated
`HEAD_WORD_TAIL_CAVEAT` (parse_abp.py:127-136): written as a pronoun/function-tail
caveat, it silently also covers the name-plus-verb class the PN sweep exposed.

**RC-2: a two-tag chunk emits an empty star row.**
`build_words_from_abp.py:249-256` splits a line on Strong's tags and gives EVERY tag a
row from the text immediately before it. In `Shaul died,G599 G*` (abp_1chronicles.txt,
1Ch 1:49) the text before `G*` is a lone space → an `english=None, strongs='*',
strongs_base='*'` row (the 477 blank rows), while "Shaul died," rides on the G599 row
with head "died". The standalone parser `parse_abp.py:205-239 parse_words()` HAS a
repair for exactly this shape (extract the capitalized name from the previous word) —
**the live builder never calls it**; it has its own `parse_abp_line`/`_emit_words` with
no name extraction.

## Why the prior fixes didn't hold — they never touched the pick

- `025e6a8` + `8a45266` (fix_italic_heads / `_strip_italic_heads`): italic-skip ONLY —
  stop the head landing on a translator-added word. Never changed the last-word order,
  never saw the trailing-verb class or the two-tag shape.
- `da170fe` + `664eb1f` (frontend): changed which token gets PAINTED gold in result
  lists — paint only the token equal to the stored head. Faithfully paints the WRONG
  word when the stored head is wrong, and its fallback (`59c-library-render.jsx:47-67`)
  golds EVERY non-italic token when the head is missing/unfindable — that is symptom
  (c)'s stopword highlighting ("the", "of", "by"), fed by RC-2's blank rows and by
  all-function slots.
- Verdict: not a regression — **incomplete coverage by design**. Each fix patched a
  consumer or a sub-case; the pick itself (RC-1) and the emit (RC-2) were never changed.
  There is no second hidden extraction path for stored heads: `_head_word` is the single
  head-pick implementation, called from every writer (build passes `_split_compounds`,
  `_redistribute_pronoun_compounds`, `_fix_backwards_pairing`, `_lord_subject_split`,
  `_funcword_noun_relocate`, `_lord_oath_fix`, `_strip_italic_heads`, plus
  fix_italic_heads.py / fix_pn_subject_merge.py / add_hebrews13.py /
  build_rendering_norm.py). Highlighting has no own pick — it compares against the
  stored value (Ask-corpus evidence highlights by Strong's position and is clean).

## Contamination map (what a wrong head poisons)

- PN Strong's lookup: `import_tipnr.py` keys on the full slot `english` — "Hezekiah
  said," falls off its match ladder → double-star row (TICKET_missing_strongs_pn pile 4).
- PN counts/binding: `views_metav.py:114` (`WHERE english_head=?`), pn_binding keyed on
  english_head, `56-library-order-logic.jsx:139` (PN click payload name).
- Lemma→English: `views_lexicon.py` "renders as"/top-gloss/grouped renders (:383-398,
  :604-607, :675-686, :1158-1164, :1292-1295), the number-folded English finder
  (`english_head_norm`, build_rendering_norm.py), `ai.py` SQL-gen + KJV-differs join,
  build_lexica_def renders-as sets, SEO pages, word cards (30-detail-panel.jsx:702).
- Highlighting: `59c-library-render.jsx` head-gold + all-gold fallback.

## Fix design (all build-side; NO in-place patching of the live db)

1. **RC-2 first — port the name extraction into the live builder's emit path:** when a
   `G*` tag follows an empty/whitespace chunk and the previous word's English contains a
   capitalized token, split the name out of the previous slot onto the star row (the
   `parse_abp.parse_words` repair, adapted to `_emit_words`/`build_verse_words`). Kills
   the 477 blank rows and puts real names on star rows.
2. **RC-1 — name-aware head pick, SCOPED TO NAME-TAGGED SLOTS ONLY (measured
   2026-07-16):** the corpus-wide count of "slot starts with a capitalized word that
   isn't the head" is 14,938 — and most of those are CORRECT: in "the LORD said" the
   slot's number tag belongs to the VERB, so "said" is the right head for that slot.
   A blanket prefer-the-capitalized-token rule would wrongly rewrite thousands of
   intended heads. The scoped rule: prefer the capitalized non-sentence-initial token
   ONLY where the slot's tag is the star/PN tag (the head is supposed to BE the name).
   All other slots keep the existing pick unchanged. Sentence-start false positives
   remain the risk to test (the Lexica engine's sentence-starter demotion faced the
   same issue — reuse its lesson, not its code).
3. Re-run the dependent chain per `/rebuild-words`: import_tipnr (its full-slot ladder
   now sees clean name slots) → surface → translit → build_rendering_norm →
   build_entity_binding. The frontend gold-paint logic needs NO change once heads are
   right; the all-gold fallback only fires on genuinely head-less slots after the fix —
   re-evaluate whether it should instead paint nothing (provenance-contract silent-
   fallback rule) AFTER the rebuild shows what remains.
4. Every recompute site listed above inherits the fix automatically (they all call
   `_head_word`) — but the rebuild gate must include the control cases below.

**MEASURED COUNTS (PA run, 2026-07-16 — replaces the "500+" estimate):**
- Blank-star rows (RC-2): **477 exact**.
- Starred rows with a common-word head (RC-1 in-scope): **36** on the 10-word probe
  list — a minor pile; the full set will surface during the rebuild gate.
- The 2,203 double-star total therefore splits ≈ 477 blank + ~36 mislabeled-head +
  **~1,690 spelling-variant/LXX-only** — the ALIAS MAP is the bulk of the workload,
  not the build fix. Fix-order implication: RC-2 + scoped RC-1 ride the rebuild as
  planned, but the variant-map curation (TICKET_missing_strongs_pn fix A) is the
  larger effort and should start first since it lands before the same rebuild.
- Lemma-leak spot-check: H2396 (Hezekiah) shows a SINGLE head "hezekiah" ×123 — the
  junk heads are confined to starred rows, not spread across real numbers. Symptom
  (b) is contained; the wrong-highlight symptom (c) should likewise be concentrated
  on starred/blank slots plus the all-function fallback (live control still pending —
  JP to supply a known-bad passage).

## Controls (must fire before any zero is trusted)

- RC-2: 1Ch 1:49 "Shaul died,G599 G*" → a Shaul row with H7586-class identity, no blank
  row. (Known positive from the PA sweep.)
- RC-1: Isa 38:21 "Isaiah said" → head "isaiah"; Jos 17:1 "Bashan area." → head
  "bashan"; Deu 15:12 "Hebrew woman," → head "hebrew".
- Non-regression: "God made" → "made", "my spirit" → "spirit" (the documented correct
  tail picks), the five frozen S11 pass-controls, `test_render_head_no_phantom.py`.
- Highlight: a JP-supplied known-bad passage — **JP: please give one or two passages
  where you saw "the/of/by" highlighted**, so the fix has a live control, not just the
  derived ones.

## Measurement queries (JP runs on PA; sizes the class before the fix is scoped)

Pile sizes (the "500+" estimate → real numbers):
```
# Blank-star rows (RC-2), exact count:
sqlite3 ~/bible-db/bible.db "SELECT count(*) FROM words WHERE strongs='*' AND strongs_base='*' AND COALESCE(english,'')='';"

# Starred rows whose head is a common verb/noun (RC-1 within the starred class):
sqlite3 ~/bible-db/bible.db "SELECT count(*) FROM words WHERE strongs='*' AND strongs_base='*'
  AND lower(COALESCE(english_head,'')) IN ('said','saying','woman','man','field','area','wife','daughter','son','king');"

# The RC-1 class corpus-wide (not just starred): multi-word slots holding a capitalized
# mid-slot token where the head is NOT that token — sized via the star-adjacent proxy:
sqlite3 ~/bible-db/bible.db "SELECT count(*) FROM words
  WHERE english LIKE '% %' AND english GLOB '*[A-Z]*'
    AND english_head IS NOT NULL
    AND lower(substr(english, 1, 1)) != substr(english, 1, 1)
    AND instr(lower(english), lower(english_head)) > 1
    AND lower(english_head) != lower(replace(replace(substr(english, 1, instr(english||' ', ' ')-1), ',', ''), '.', ''));"
```
The third one approximates "slot starts with a capitalized word that isn't the head" —
it will over/under-count edge shapes; treat it as a scoping number, not a finding. The
lemma-leak diagnostic (symptom b) is per-number:
```
# Top 'renders as' junk for a known lemma — e.g. H2396 Hezekiah: heads that aren't the name:
sqlite3 ~/bible-db/bible.db "SELECT english_head, count(*) FROM words
  WHERE strongs_base='H2396' GROUP BY 1 ORDER BY 2 DESC;"
```
(Repeat per suspect number; a name-lemma whose top heads include verbs = the leak.)

## Rebuild batch inventory (R-1: fire once)

Riding this `/rebuild-words` run:
1. This ticket (RC-1 + RC-2).
2. The `finish_rebuild.sh` acceptance run OWED from the Lexica-dictionary work (memory:
   watch JP's next real rebuild) — satisfied by this run, no extra work.
3. Nothing else found pending against the words build (TODO.md checked 2026-07-16; the
   S11 certification arc is closed). The spelling-variant alias map
   (TICKET_missing_strongs_pn fix A) is import_tipnr-side and re-runs with the chain
   anyway — land it before the rebuild so one run carries both.
