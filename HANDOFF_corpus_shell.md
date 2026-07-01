# Handoff — Ask-the-corpus onto the shared Shell (first RightStack consumer)

Status at handoff: shell primitives (`Shell` + `RightStack`, `static/src/22-shell.jsx`) are
built, proven, and consumed parity-only by News + Word study + Library. Corpus is the FIRST
real push-stack consumer — build it, then let it audit the primitive before Notes/Study/News-rail.

Do the prereq FIRST, on its own, and verify it live before any shell work. The rail faithfully
inspects whatever the center list feeds it; a list seeded with the wrong words makes the whole
inspect rail garbage. Correctness gates the UI.

---

## (0) PREREQ — diacritic exact-lemma-first resolution  [do first, ship alone]

### Confirmed root (traced in code + live db, not assumed)
- Frontend `ask()` (52-ask-corpus.jsx:395) sends the raw query to `/api/ai-search`.
- `ai_search` (ai.py:1307) does NOTHING deterministic with a bare word: Step 1 (ai.py:1372)
  asks Haiku for *English concept words*, then LSJ-looks-those-up, then Haiku writes the SQL,
  then `key_strongs` come from the model. The occurrence list is the model's SQL output.
- `corpus_panel.py` only adds counts afterward, off the model's `key_strongs`.
- **There is no exact-lemma step anywhere.** A typed `γῆ` is never pinned to G1093.

### SNAG found while tracing — `lemma_plain` was NOT on the live db
CLAUDE.md + memory record the `lemma_plain` exact-match key as live 2026-06-26. It is NOT — the
live `lexicon`/`bdb` have no such column (checked on PA 2026-06-30). The word-study lookup
(`views_lexicon.py` `_has_lemma_plain`, lines 73-80 + 513-532) is guarded, so it silently fell
back to the OLD substring over-match — the documented fix was asleep. `scripts/add_lemma_plain.py`
(additive, re-runnable, adds column + index + fills, touches nothing else) puts it back:
```
python3 scripts/add_lemma_plain.py bible.db --apply   # on PA
touch /var/www/www_lexica_bible_wsgi.py               # reload — per-worker "no column" memory resets
```
This is step 0 of step 0. It wakes word-study's exact-match AND gives corpus the key to reuse.
(Update memory once confirmed — the doc claim is currently false.)

### The fix
Add a deterministic resolver at the TOP of `ai_search`, before Step 1: if the whole query is a
single Greek or Hebrew word (script detection), normalize it with the SAME fold word-study uses
(`views_lexicon._norm_lemma` — accent-stripped, lowercased, hyphen-removed, final-sigma folded),
match `lexicon.lemma_plain` / `bdb.lemma_plain` exactly, and if there's a clean single hit, PIN
that Strong's and drive the occurrence list from that number — skip the English-concept laundering
for that word. Fall through to the model path for a phrase/question or no exact hit.
- REUSE `_norm_lemma` + `lemma_plain` exactly as views_lexicon.py:513-532 already does. Do NOT
  invent a second matcher. Guard on the column existing (mirror `_has_lemma_plain`) so a deploy
  before the data step is still safe.
- KNOWN GAP (measured 2026-06-30): a word whose accent-/point-stripped form maps to MORE THAN
  ONE number falls through to the model path (not wrong, just not pinned). Greek = 27 words
  (~0.5%, negligible — accents barely distinguish Greek). Hebrew = 1,460 (~17% — stripping vowel
  points collapses distinct words to one consonant skeleton, so the Hebrew pin is inherently
  weaker). Same fold Word study uses, so no NEW gap — just consistent behavior.
- Greek → `lexicon`; Hebrew → `bdb`/heb.db. Exact FIRST; the model path is the fallback only.
- Bump `_CACHE_CODE_VER` in ai.py (behavior change not in the prompt fingerprint).

### FIXED (2026-07-01) — was a pre-existing NameError, not the Hebrew branch
The Hebrew "Internal server error" traced to `_assemble_payload` (the SSE streaming tail) reaching
for `_is_thematic`, a helper NESTED in `ai_search` it can't see after being lifted out — even
though it already receives `target_bases`. A fresh streamed search NameError'd whenever it reached
that helper: a model-named additional verse, OR a zero-base-row result. The exact-lemma Hebrew pin
always returns zero base rows (its `SELECT … LIMIT 0` placeholder), so it reliably surfaced a
LATENT bug that cache hits + normal Greek searches had hidden. Fixed by binding a local
`_is_thematic` to the `target_bases` param (commit 04cf9a1). Not caused by the pin — the pin just
exposed it. Redeploy + re-ask אֶרֶץ to confirm the Hebrew pin now completes.

### Acceptance (must pass before shell work starts)
- On PA after --apply: `lemma_plain='γη'` returns G1093 alone (the `LIKE '%γη%'` list is the leak).
- Live: ask "γῆ" in the corpus tab — occurrence list is G1093 only, no `-γη`/`γε-` compounds.
- A plain question ("what is the sabbath") still routes through the model unchanged.

---

## (1) Zone mapping onto Shell

Corpus today = 2 zones (`.ac-rail` history + one `.ac-main` column with everything inline).
Target = the four slots via `Shell` (top nav is global, above the frame):

- **LEFT rail (navigate)** = the existing `.ac-rail` (Recent conversations + New thread). Moves
  into Shell's `rail` slot; contents unchanged.
- **STRIP (search)** = the composer (`AcComposer`) moves from pinned-bottom to the center TOP
  strip, ~59px so it lines up with News/Word study. Follow-ups typed here; Q&A stacks below.
- **BODY (answer)** = the answer stack, unchanged in substance:
  - **Occurrence-count panel stays put** — the "HOW OFTEN THESE WORDS OCCUR" box (`CorpusPanel`,
    Greek/Hebrew split, +more expanders) IS the result-shape summary. Keep it at the top of
    center; it does NOT reflow into the body and is NOT a right-rail candidate.
  - synthesis prose (`AcProse`) + the occurrence LIST (`CorpusResults`) with its ABP·BSB·KJV·HEB
    text toggle. The list stays in center.
- **RIGHT rail (inspect)** = NEW. `RightStack`, the drill below. New surface ⇒ sits BELOW the nav
  (`.zinspect.rstack`, `top:var(--hdr-h)`), not the shipped surfaces' top:0 float.

## (2) The RightStack drill — occurrence → fork → word  [confirmed order]

New interaction: clicking an occurrence PUSHES it into the inspect rail and STAYS in corpus.
"Read in context ›" stays the explicit jump-out to the reader. That peek-vs-leave verb split is
the covenant (same distinction Library kept going the other way) — don't collapse them.

- **Depth 1 — Occurrence** (`root`): the clicked verse in the current text mode
  (ABP/BSB/KJV/HEB — honor the list's `textMode`), target word highlighted, its form + gloss,
  "Read in context ›" (jump-out). Because the card already carries form + gloss, the reader is
  oriented without the full entry.
  - If the word is contested: a **"Contested reading ›"** push (depth 2) AND, alongside it, a
    **"Full word study ›"** push that skips to depth 3. Do NOT force the fork — exposing the seam
    is the covenant; forcing every reader through it hands down a verdict. Keep both reachable.
  - If the word is plain: just **"Full word study ›"** → word (depth 2, no fork layer).
- **Depth 2 — Fork** (contested words only): the contested-readings card (reuse the lexica fork /
  both-priors rendering). Carries its own "Full word study ›" → depth 3.
- **Depth 3 (or depth 2 for plain words) — Word**: the full word card (reuse
  `renderWordCardInner` / `LexicaBody` — the same body Word study/Library render; scope any
  corpus-only tweak, NEVER edit the shared `.detail-*` rules).

- **Peer-select** — clicking a DIFFERENT occurrence in the center list calls `ctl.reset()` and
  re-seeds depth 1 with the new verse.
- Scroll survives push/pop via the `visibility:hidden` layer trap already in `RightStack` — do
  NOT switch to display:none.

## (3) Wiring (real names)

- `useRightStack()` in `AskCorpusView` owns `ctl` (the parent holds the array so peer-select can
  `reset()`). Pass `ctl` to `<RightStack>` and drive it from the occurrence-click handler.
- Push shape: `ctl.push({ backLabel, render })`; `_id` is minted push-unique (don't key by type).
- `RightStack` root = the depth-1 occurrence card (or `empty` = a `ZoneEmpty` "pick an occurrence"
  state when nothing is selected).
- Occurrence click today = `onReadInContext` (jumps out). SPLIT it: row click → set the inspect
  (push/reset); keep a separate "Read in context ›" affordance inside the depth-1 card for the
  jump-out.
- `Shell` props: `rail`, `center`, `inspect={<RightStack .../>}` (RightStack renders its own
  `.zinspect.rstack` aside — pass it directly, no second wrapper), `isMobile`, `mobile`.

## (4) Mobile

Adopt Shell's collapse; retire corpus's own `railOpen` logic. `mobile = { tools, sheet,
sheetTitle, onCloseSheet, sheetBare }`:
- Bottom `MobileBar` with slots for the left rail (history) and the inspect (occurrence detail).
- Inspect opens as a `ZoneSheet` with `bare` + an INLINE `RightStack` (`inline` prop) so the stack
  lives inside the sheet instead of a fixed panel escaping to the viewport edge.
- The composer/strip stays visible; the Q&A body is the inline center.

## (5) Verification gates

- **Widen the CSS parity gate prop list** (the bug that missed the News width + scroll issues):
  the gate compared too few props. When you verify corpus's inspect, the prop set MUST include
  `width, max-width, flex-basis, overflow-y, overflow-x` on top of the existing geometry set. The
  gates were run in-session (Node, not committed) — recreate with the widened list and run it on
  corpus's `.zinspect.rstack` vs the News/Word-study reference.
- Behavioral: a small state check that (a) a push then pop UNCOVERS depth 1 with its scrollTop
  intact, (b) peer-select resets to depth 1 on the new verse, (c) a plain word shows no fork layer.
- Live click-through on desktop Chrome (the user doesn't test in Chrome — check it) + one phone.

## (6) Build order

1. Prereq resolver (§0) — ship + verify live alone.
2. Shell frame swap for corpus (rail/center/strip), occurrence-count panel stays put, list stays
   center. No inspect yet — prove the frame at parity first.
3. RightStack inspect: depth-1 occurrence card + the click-to-push / read-in-context split.
4. Add fork (depth 2) + word (depth 3) layers + peer-select reset.
5. Mobile collapse.
6. Widened parity gate + behavioral check + Chrome/phone click-through.

## Files
- `static/src/52-ask-corpus.jsx` — the surface (AskCorpusView, AcTurn, AcComposer, CorpusResults).
- `static/src/22-shell.jsx` — Shell / RightStack (consume, don't edit).
- `static/src/20-shared-components.jsx` — `ZoneEmpty`.
- `static/styles.css` — `.zshell/.zrail/.zcenter/.zinspect/.rstack*` (frame; share, don't fork) +
  new `.ac-*` inspect-content classes (surface-specific).
- `ai.py` — the prereq resolver (top of `ai_search`) + `_CACHE_CODE_VER` bump.
- Rebuild `static/app.js` (`npm run build`) before committing; commit src + app.js together.
