# ★ SPENT 2026-07-16 — step 4 ran and SHIPPED (fixture `3b69089`, migration `54eb853`). ★
# Everything below is history; the record of what shipped is docs/claude/frontend.md → "THE
# MOBILE SHEET CONTRACT" (step-4 record). Notable correction: `.tall` was a FIXED 90% height,
# not the max-height ceiling claimed below. Do not work from this file.

# HANDOFF — Mobile sheet contract: step 4 (Word study) + the lexicon fixture

**Read `docs/claude/frontend.md` → "THE MOBILE SHEET CONTRACT" first. It is the spec; this file
is only the state of the work and the next move.**

**This prompt is a MEMORY the moment it was written (2026-07-15).** Everything below was true at
commit `cf086b2`. Re-verify each claim against the repo before you lean on it — file:line cites
rot, counts drift, and a later session may have moved things. That is the standing handoff rule
(frontend.md), not a formality: a chip in an earlier arc said "5 call sites" when the truth was 6.

## Where the pass stands

Four hand-rolled sheet frames are gone; **one is left**.

| Frame | Cards | State |
|---|---|---|
| `.zsheet` | 7 (News ×3, Ask-corpus ×2, Notes ×2) | DONE — `05dbd6f` |
| `.detail-sheet` | 5 (word card, chapter overview, xref, note editor, day intro) | DONE — `86e04e5` |
| `.msheet` | 2 (Reading options, You) | DONE — `cf086b2` |
| **`.wm-sheet`** | **4 (Word study: Distribution, Word card, Views, Search)** | **NOT STARTED — blocked, see below** |
| `.mpick` | 1 (book picker) | header spec only; the single sanctioned exception |

`.wm-sheet` still sits on z121 with its own `max-height: 62%` / `.tall { 90% }` and a 6px radius.
That is drift by design until step 4 — don't "fix" it in passing, and don't mistake it for a bug.

## THE BLOCKER — and it is a JP-sanctioned condition, not a preference

Word study is **the app's visual reference surface** (frontend.md). The guardrail says a pass must
leave it byte-identical. That guardrail was **amended this session, with JP in the loop**: it bars
*incidental* convergence, not a unification he ordered — but it bars doing it **silently or
unmeasured**. The binding condition:

> **Word study's pixels do not move until its four sheets are measurable.** Build the lexicon
> fixture FIRST, post it as its own gate, then migrate.

So: fixture → reviewer gate → `.wm-sheet` migration → reviewer gate. Do not reorder this.

## The fixture project — what is already traced, and what is not

`tests/mobile_harness.js` has no lexicon fixture, so Word study renders a landing and nothing else.
Six endpoints, each traced to its PRODUCER (never to what the caller expects — sibling routes
disagree on shape ON PURPOSE; `/api/chapter` returns a bare list while `/api/verse-words` returns
`{words:[…]}`, and reading the neighbour instead of the producer is a logged past failure).

**Top level, traced 2026-07-15 — RE-VERIFY each against the file before use:**

| Endpoint | Caller (`static/src/00-core.jsx`) | Producer | Top-level shape |
|---|---|---|---|
| `lexiconLookup` | :373 | `views_lexicon.py:465` | **bare list** `[{strongs, lemma, translit, gloss}]` |
| `lexiconProfile` | :375 | `views_lexicon.py:1035` | `{strongs, lemma, translit, definition, derivation, related, total, books, corpus, glosses, abp_glosses, kjv_glosses, heb_glosses, bsb_glosses, has_abp, has_kjv, has_heb, has_bsb, alias_note, default_verses, default_truncated}` |
| `lexiconBooks` | :384 | `views_lexicon.py:1263` | `{books: [...]}` |
| `lexiconVerses` | :382 | `views_lexicon.py:1459` | `{verses: [...], glosses: [...], truncated}` |
| `lexiconEnglish` | :386 | `views_lexicon.py:630` | bare list — **shape NOT traced yet** |
| `lexica` | :137 | `views_lexica.py:99` | the stored entry document — **shape NOT traced yet** |

**Still to trace (each is its own producer read — this is the bulk of the work):**
- `glosses` / `abp_glosses` / `kjv_glosses` / `heb_glosses` / `bsb_glosses` — built by `_fold(...)`
  over four different row builders. Rows look like `{"gloss": …, "count": …}` (`views_lexicon.py`
  ~:693, :715, :735, :757 in the `_render_glosses_all` family) — **confirm each, they differ.**
- `books` — `{"book": …, "chapter": …, "verse": …}` appenders around `:1375`, `:1409`, `:1423`.
- `default_verses` / `default_truncated` — `_all_books_verses(...)`, called at `:1252`.
- `related` — `_greek_cognates(conn, snum, _deriv_raw)` at `:1241`; `[]` for Hebrew and for dotted.
- `alias_note` — `alias_note_for(strongs_id)`.
- `verses` rows — `vout.append({"chapter": …, "verse": …})` at `:1518`; note the ALL-books branch
  returns a different row (`{book, chapter, verse}`) than the per-book branch. **Two shapes, one
  endpoint** — get both.

**Fixture rules that are NOT optional** (all paid for already — memory
`feedback_audit_tools_must_fail`):
- Shape from the PRODUCER, per field, cited in the fixture header. The VALUES may be illustrative;
  the SHAPES may not.
- **Any value the code COMPUTES on rather than prints is not free to be illustrative.** A verse
  count, a Strong's number that resolves through a table, a date in a rolling window.
- **Unknowns THROW.** `CHAPTER_LEN` raises on an unknown chapter rather than inventing one — match
  that. A stand-in that answers for something it knows nothing about is a fault injector.
- **Unknown seed values 400 loudly** (standing harness behaviour, ratified). Don't add a seed that
  silently degrades to empty.
- Count axis (empty / few / many) where a surface holds a LIST — `&notes=many` is the worked
  example (`MANY_EXTRA`, generated from the traced single-verse anchor writer).

## What step 4 must do once the fixture exists

1. **`.tall` resolves under the two-class model — already ruled:** Distribution and Word card are
   **Panels** (they hold data); Views and Search are **Menus** (controls only). `.tall` was never
   drift — it was this distinction, un-named.
2. **Verify Menu stability on Views AND Search** across every state each owns. **The Menu class's
   precondition is law: controls may DISABLE but never UNMOUNT; a card that hides controls is a
   Panel.** Word study's bar already greys 3 of 4 tabs until a word loads, so check the sheet
   contents too, not just the bar.
3. Per card, by rect: header present (`.sh-head` or the child's `.sh-band`), radius
   `--sheet-radius` 18px, z151, handle 40×4, height (Panel = fixed fill; Menu = stable), swipe both
   cases with a FORCED overflow (destructive case last).
4. **Word study's own byte-identical guardrail still applies to everything that is NOT the sheet
   frame.** Its landing, verse lists, `.filters-sep` grouping and word card CONTENTS must not move.
5. **Close the open `.filters-sep` verification while the fixtures are live** (ordered, and open
   across three sessions now). It draws only behind `profile` or `groupings`
   (`80-lexicon.jsx:1013` / `:1071`) — which is exactly why it needs this fixture. Measure Word
   study's rendered divider byte-identical: **1×14, `--rule-2`**.

## OPEN VERIFICATION LEDGER — carry this on every step report until closed

1. **News' selected why-head inside its sheet** — never reached. Its default band measures 36.8
   post-`sh-band`; the SELECTED state (which carries a `‹ Watch` control, so expect ~42.4 per the
   band-with-control ruling) is unmeasured. Not claimed.
2. **The day-intro card** (`59-dayintro.jsx`) — needs chronological mode; never opened. It shares
   the identical code path as the chapter overview (`Sheet bare` + `.detail-card`), which measured
   716/48/764 — but that is an inference, not a measurement.
3. **`.filters-sep`** — reasoned inert by exhaustive search, never measured. See step 4 item 5.

## Traps this pass paid for — do not re-pay them

- **The pane FREEZES CSS animations.** A raw rect read catches `slide-up`'s first frame forever and
  every number is 40px wrong. `el.getAnimations().forEach(a => a.finish())` before EVERY read. The
  tell is an internally impossible rect (bottom past the viewport).
- **An open sheet COVERS the zone bar** (documented, hit-test proven). You cannot tap another
  zone's button while a sheet is open — close it first, and **check your tap's return value**; a
  probe that ignores it silently measures the wrong sheet. That happened.
- **Assert the PRECONDITION, not just the result.** A 1400px filler with default flex-shrink gets
  squashed by a flex-column body → nothing overflows → the swipe test passes vacuously. Use
  `flex: 0 0 1400px` and assert `scrollHeight > clientHeight` BEFORE the gesture.
- **A 200 from the right port is not a 200 from your code.** A stale harness from an earlier
  session held 8099 and answered happily. Control-test the FAILURE case (bad seed must 400), and
  prefer a fresh port to killing something a parallel session may own.
- **`env(safe-area-inset-*)` is 0 in the harness** — desktop Chrome. Anything safe-area is
  unreachable by measurement; **reading the rule IS the check**. A double-counted home indicator
  shipped through two all-green steps this way.
- **The viewport is elastic** — assert `innerWidth` at BOTH ends of every probe.
- **A detector built from class names you recalled is a guess.** A made-up selector (`.ac-insp-head`)
  produced a false FAIL that a reviewer then ruled on. Define by computed style, then control-test:
  break the thing, prove the detector goes blind, restore, prove it comes back.
- Menu heights shift a few px between page loads with font-load timing (`display=optional`). The
  invariant under test is **state-change** stability, not the absolute number.

## Standing constraints

- `.detail-head` / `.detail-body` / the band classes are **SHARED with the desktop side panels** —
  the shell owns mobile chrome only. Desktop guard of record = **the stash round-trip**, same
  session/browser/fixtures (`?bundle=head` is JS-only and CANNOT baseline a CSS change).
- Gate discipline: post the fixture, then the migration, each with verification, before committing.
  **If a ruling's factual basis collapses mid-step, the retraction posts BEFORE the commit.**
- After any `static/src/*.jsx` edit: `npm run build`, commit BOTH source and `static/app.js`.
