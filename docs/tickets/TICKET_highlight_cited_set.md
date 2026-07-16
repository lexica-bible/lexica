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
Determined by the key-word chips in the Gen 1:1 thread's rail ("What this answer
rests on"): a 3588-family chip visible → Door 1; absent → Door 2. PENDING JP's answer.
The answer picks the control test's known-bad case; both fixes land either way.

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
