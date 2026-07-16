# TICKET — Stopword highlighting in Ask-the-corpus: cited-set contamination

Status: OPEN — diagnosed 2026-07-16 (the head-word live control: prediction FAILED the
right way — head data in the control verses is CLEAN; the defect is in the highlight
set, not the words table). DECOUPLED from the head-word rebuild — ships on the fast
path (code + tests + deploy, gentilic-guard pattern). JP ruling: fix BOTH doors
regardless of which fired.

## Symptom
An arche (G746) search's key passages highlight "the" / "by" across Gen 1:1-3,
Act 3:15, 5:31, 19:27, 19:35. Verified against live rows: every highlighted stopword
is a correctly-stored ARTICLE slot carrying G3588 — the highlight set contains the
article's number, so every article lights up.

## The two doors (close both)

**Door 1 — unenforced AI instruction.** `ai.py`'s SQL-gen prompt tells Haiku to omit
particles/articles/prepositions from `key_strongs` (~line 213) — nothing enforces it.
If the model lists 3588, every article in every evidence verse glows.
Fix: hard filter in the backend where key_strongs is accepted — drop any number in
the function-word sets (`_FUNCTION_STRONGS` / `_HEB_FUNCTION_STRONGS`, the existing
171-word Greek set + Hebrew analog; reuse the sets, never a copy).

**Door 2 — cross-language twin auto-add.** `_acCited` in `52-ask-corpus.jsx:45-55`
takes each key number and adds the bare digits PLUS `G<bare>` PLUS `H<bare>`. Any
legitimate Hebrew key number whose digits collide with a Greek function word's number
manufactures the wrong key (H3588 "ki" → G3588 the article), and vice versa — a latent
defect class for EVERY H/G digit collision, not just function words.
Fix: stop manufacturing the twin — only add the prefixed form(s) actually present in
the key list (keep the bare form for legacy matching only where the payload itself is
bare). Mirror in `App.citedStrongsApp` (the comment says _acCited mirrors it — find
and fix BOTH copies; grep before sizing, standing rule).

## Which door fired here
**Door 1 CONFIRMED (JP, 2026-07-16):** G3588 (ὁ) appears in the words-in-scope list
on the Gen 1:1 arche thread — the model included the article, nothing enforced the
omission. Both doors fixed regardless (JP ruling).

## Implemented 2026-07-16 (awaiting receipt)
- Door 1: `ai.py _filter_function_keys` — hard filter at the key_strongs acceptance
  point, BEFORE the per-language caps (a dropped article doesn't eat a slot). Reuses
  `core._FUNCTION_STRONGS` + `views_lexicon._HEB_FUNCTION_STRONGS` (both bare-number
  sets; empty set = no-op, deploy-safe). Locked by tests/test_key_strongs_filter.py
  (5 tests incl. the G3588 known-bad control + a language-awareness proof: H853
  drops, G853 survives).
- Door 2: ONE shared builder `_acCitedSet` in 51-corpus-logic.jsx replaces BOTH
  drifting copies (52-ask-corpus `_acCited`, 90-app `citedStrongsApp`). Emits ONLY
  language-prefixed numbers — the twin-manufacture is gone, and bare forms are out
  of the set entirely (matchers bare both sides, so a bare key collided cross-
  language even without the twins). Bare key numbers resolve Greek per the prompt
  contract. Locked by tests/test_ac_cited_set.js (7 tests incl. the H3588 control).
- Both test files added to the pre-commit AND ci.yml explicit lists (standing rule).
- Cached answers: stored payloads keep their old key_strongs — the Door-2 frontend
  fix cleans their highlighting anyway (prefixed-only set); Door 1 applies to new
  draws. No cache purge needed.

## The THIRD leg (post-deploy, 2026-07-16) — saved threads needed their own fix
First deploy did NOT clear the Gen 1:1 symptom. The claim above was WRONG for
door-1 cases: "self-heal via the frontend" only covered twin-manufactured
collisions. This thread's stored key list legitimately CONTAINS G3588 (the model
put it there — the "ho" chip), and reopened threads replay a BROWSER-STORED copy,
never re-hitting the answer endpoint — so neither the acceptance filter nor a
cache-read filter can touch them. Three legs now closed:
1. Acceptance (new draws): `ai.py _filter_function_keys` — as above.
2. Server cache reads: `ai.py _drop_function_key_entries` on the cache-hit path,
   mirroring the `contested` re-stamp (pure lookup, no model).
3. Display time (browser-saved threads): `/api/lexicon/function-strongs` — a tiny
   endpoint serving the prefixed function-word set (mirrors /api/lexica/contested,
   the codebase's own precedent for exactly this staleness problem) +
   `_acDropFunctionKeys` in 51-corpus-logic.jsx, applied in ProvenancePanel and
   AcTurn before the cited set is built AND before the chips render (the "ho" chip
   disappears too). Network miss = empty set = under-filter only.
Locked by 4 added tests in tests/test_ac_cited_set.js (stored-thread G3588
control, no-op-on-miss, H853/G853 language-awareness, excludeSet path).

## Live check after deploy (JP)
Re-open the Gen 1:1 arche thread: articles ("the", "by") no longer highlight in key
passages; "beginning"/"God"/content words still do (the fix must not go dark).

## Adjacent findings (same rail component, JP scope addition 2026-07-16)
- **Chip counts are corpus-wide by design** (`occCount` sums the panel's total-Bible
  counts). JP's standing want: search-relevant counts — occurrences within THIS
  search's verse pool. Honest scoping: the answer payload does NOT carry per-word
  pool counts (only the curated key passages + results); a real fix needs the
  backend to compute per-key-word counts over the pinned pool and ship them in the
  payload. No existing TODO entry found (checked 2026-07-16) — entry ADDED to
  TODO.md. Do not approximate from the shipped passages (they're a curated subset).
- **Zero-length bars** (gē, archēgos, ho, thea): the `hasCount:false` state — rows
  the panel has no count for render a minimum-width bar, identical to a tiny real
  count. Silent-fallback rule violation (a missing number must look different from
  a small number). Folded into the TODO entry.
- **"23 related forms set aside — spelling matches, meaning unconfirmed"**: working
  as designed (the gloss-unconfirmed cognate aside from the words-in-scope builder).

## Controls (per door, before any zero is trusted)
- Door 1: feed the acceptance path a key_strongs list containing "3588" → the filter
  must drop it (unit test on the backend filter).
- Door 2: a key list containing H3588 (and an H-number colliding with a Greek content
  word, e.g. proving no over-filtering) → the built set must NOT contain G3588 (unit
  test on the set builder; the frontend logic is testable in the Node gate).
- Live control: re-run the arche/Gen 1:1 ask (prompt-cache allowing) → no article
  highlights in key passages; content words still highlight (Gen 1:1 "beginning"
  stays gold — the fix must not go dark).

## Non-scope
- words-table data (clean in the control verses).
- The all-gold fallback in `59c-library-render.jsx` (paints every word when a slot has
  no locatable head): related display behavior, evaluated AFTER the head-word rebuild
  per TICKET_headword_class — not touched here.
