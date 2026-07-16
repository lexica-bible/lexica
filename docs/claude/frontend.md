# Lexica reference — Frontend
Routed from CLAUDE.md. Build system, three-zone shell, Library tab, Notes/accounts, responsive.

## Frontend build step
- SOURCE is `static/src/*.jsx` — per-view files, concatenated (filename order; numeric prefixes)
  into ONE compilation unit. `static/app.js` is the COMPILED output the browser loads. app.js IS
  committed; `node_modules/` is git-ignored. (Phase 4, 2026-06-06: the old 3,461-line
  `static/app.jsx` monolith was split into `static/src/` — see file headers there.)
- After ANY edit to a `static/src/*.jsx` file you MUST rebuild before committing:
  `npm run build` (runs `scripts/build-frontend.js`: concat src → Babel → static/app.js).
  One-time setup: `npm install`. Commit BOTH the .jsx source AND the rebuilt app.js.
- The build runs LOCALLY (Node is on the dev machine, not on PA). PA deploy just pulls the
  already-compiled app.js.
- **app.js is served from a Flask route, NOT `/static/`** (2026-06-29): `/assets/app.js`
  (`app_bundle` in app.py) with `Cache-Control: public, max-age=31536000, immutable`. PA's
  `/static/` mapping can't set a cache header, so the 543KB bundle was re-downloaded every load
  in Firefox. The template loads via `bundle_url()`, which keeps `?v=<mtime>` cache-bust, so a
  deploy changes the URL and the long cache never serves a stale bundle (gzip preserved).
  Everything else stays on `/static/`. Don't try to fix static caching in Flask config — PA
  serves `/static/`, Flask never sees it. Memory `project_static_cache_header`.
- Why concat-then-compile (not `babel <dir>`): one unit emits Babel's spread helper once and
  reproduces the old single-file output exactly.
- Why a build step at all: in-browser Babel recompiled all JSX on every load (~2.5s render
  delay; server TTFB 96ms). Precompiling + production React removes that tax.
- **`design/` is NOT the app** — throwaway design-tool mockups (standalone mini React apps).
  The live frontend is ONLY `static/src/*.jsx` → `static/app.js`. Never audit/edit
  `design/*.jsx` as production; use it only as the visual target (see `design/README.md`).
- **react/react-dom are TEST-ONLY devDependencies** (for the render smoke gates); the app loads
  React 18 from the CDN UMD, NOT from npm.

## Responsive breakpoints
- **Desktop ≥1100px**: navy header, left nav panel (224px), lib-bar toolbar, detail panel as
  right sidebar.
- **Mobile <1100px**: no header, the app's tab nav `.mobile-tabs` fixed at the **TOP** (`top:0` —
  NOT the bottom; the bottom is free for a per-tab bar), panels as bottom sheets. Per-tab bottom
  bars: Library's reading cockpit `.lib-toolbar`, Word study `.wm-tabs`, News `.zbar`.
- JS thresholds: `navVisible >= 1100`, `isMobile < 1100` (two states only).
- CSS: `@media (max-width: 1099px)` / `(min-width: 1100px)` — plus 520px for very small phones
  and a **1500px header nav-overflow** breakpoint (below it the desktop header hides the inline
  nav into a hamburger; subtitle stays). The header actually runs out of room ~1471px: Word
  study / Library / News reserve 472px (`--sidebar-w + 12`) on the right for the floating word
  card. Hamburger = `Header` in `20-shared-components.jsx`; CSS `.hdr-burger`/`.hdr-menu` +
  `@media (max-width:1499px)`.
- One shared height `--bar-h` (48px, :root) sizes EVERY mobile chrome bar (top nav, Library
  cockpit `.lib-toolbar`, `.wm-tabs`, `.zbar`) + sheet clearances — bars/sheets use `100dvh` +
  safe-area, never `100vh`. Don't reclaim it locally: consumers and the sheets' max-height maths
  key off it.

### Shared controls + touch (cross-tab rules, learned the hard way)
- **Measuring a phone layout: `tests/mobile_harness.js`.** Serves the REAL committed bundle +
  `styles.css` + the local React UMD against stubbed payloads, so a phone-width layout can be
  MEASURED in a real engine (`node tests/mobile_harness.js 8099` →
  `/?view=corpus&admin=1`; `&bundle=head` serves the COMMITTED bundle for A/B). A tool, not a gate
  — deliberately NOT in the CI list: it renders, it doesn't assert. Fixture provenance is per
  fixture in its header, each traced to the code that produces it. Three traps it already paid for,
  all in `feedback_audit_tools_must_fail`: assert `window.innerWidth` (Chrome won't window below
  500px — use device emulation), seed `lexica_tour_seen` (the first-run modal covers everything),
  and stub `/api/` ONLY (it once answered for `chronological.json` and blanked the whole desktop).
  `?admin=1` matters — JP reviews as admin, whose nav carries more tabs than a reader's.
  `&notes=1` seeds the notes store (4 notes + 1 journal page).
- **Provenance when a surface has NO server producer (Notes, 2026-07-15 — the adapted form).** The
  rule is "shape fixtures from the producing code", not "from Python". Notes is browser-local:
  `NotesStore` reads `localStorage` once on first load and caches, so its fixture is a
  **localStorage seed written before `app.js` runs**, not an `/api/` stub. Do NOT shape it from
  `views_notes.py` — `notes_sync` stores the client's blob opaquely (`json.dumps(n)`) and hands the
  same blob back, so the server is a round-tripper and never authors a field. The producers are the
  CLIENT: `NotesStore.create()`/`createJournal()` for the record, and — **TWO different anchor
  writers, not one** — `60-library.jsx verseAnchor()` (:1291-1295, the verse-number MENU: stamps
  `start` and `end` to the same verse, so it can only ever make a single-verse note) or
  `resolveSelection()` (:1093-1102, the DRAG-SELECT: stores `start.verse`/`end.verse` separately,
  real `pos` values, and a range `refLabel`). Shape a RANGE fixture from the second; reading only
  the single-verse writer is how you'd "confirm" that ranges aren't stored at all. Name them per
  field in the header as usual. Keep such a seed OPT-IN: notes also paint marks in the Library
  reader, so an always-on seed would quietly move other surfaces' numbers.
- **When a fixture DIMENSION becomes load-bearing, it gets real values with named provenance —
  and unknowns THROW.** The chapter fixture's verse count used to be decoration ("a short slice is
  enough to boot"); the moment `NoteVerseInspect` derived the chapter's last verse from it, that
  count decided a test's outcome, and an invented length would have been deciding results. It now
  carries REAL counts read from the repo's own `abp_texts/` (Joh 4=54, Gen 1=31, Rom 8=39,
  Psa 104=35 — pre-build is fine for a COUNT), and an unknown chapter raises instead of standing
  in. A stand-in that quietly answers for something it knows nothing about isn't a fixture, it's a
  fault injector (the `chronological.json` lesson, second instance).
- **Stub the shape the PRODUCER returns, never the shape the caller expects.** A stub shaped to a
  buggy caller's assumption makes the bug untestable and green. `/api/chapter` stays a bare list in
  the harness precisely because the panel that misread it is what we're catching.
- **Make a fixture row say WHICH row it is.** The harness's verse words carry a `spirit-v{{v}}`
  marker substituted with the requested verse, so a measurement proves which verses actually
  rendered and fetched — not merely how many. "3 rows appeared" is not the same claim as "verses
  21, 22 and 23 appeared", and only the second one catches an off-by-one range.
- **The `?bundle=head` A/B validates against REMEMBERED numbers too, not just stale reads.** Second
  instance: Notes's desktop shell measured 1388px where the previous session banked 1400 — not a
  regression, but the shared chapter fixture having grown to Gen 1's real 31 verses, making the
  page tall enough for a scrollbar. Identical on BOTH bundles. A number from a previous session is
  a memory, not a baseline: re-derive it from HEAD at the same viewport and fixtures.
- **⚠ `?bundle=head` IS JS-ONLY, BY CONSTRUCTION — it CANNOT baseline a CSS change.** It serves
  `git show HEAD:static/app.js`; `styles.css` always comes live off disk. So on a CSS edit the mix
  run is HEAD's code against YOUR stylesheet — neither before nor after. Treat it as diagnostic
  only. **For CSS, the baseline of record is the STASH ROUND-TRIP**, in the same session, same
  browser, same fixtures: back the files up → `git stash push -u` → `npm run build` (so app.js on
  disk is HEAD's too) → measure → `git stash pop` → rebuild → **byte-check the restore against the
  backup**. Anything else is comparing against a memory.
- **"Stable twice" is NOT "true" — a stability check can pass on a transient.** The Notes frame
  reads 1388 or 1400 depending on when you look (a scrollbar during load), and BOTH values survived
  a settle-until-unchanged probe and a double-read six seconds apart, in different runs. Two
  "stable" readings that disagree mean the probe is measuring the weather. **The only baseline of
  record is HEAD measured by the IDENTICAL method in the SAME session** — that is what proved 1400
  is the truth and every 1388 was the artifact. This is the settle lesson's final form; the earlier
  two (wait before reading; validate the baseline) are subsumed by it.
- **Settle on the DRIVER of the dimension, not on the surface you're reading.** The probe that
  produced the phantom waited for the Notes rail — while the LIBRARY, mounted alongside, was still
  loading and driving the page height that decides the scrollbar that decides the width.
- **A fix scoped to a desktop container does not reach the phone.** The Notes row clamp went on
  `.notes-rail-scroll` (desktop-only); the same list renders in the mobile sheet, where rows stayed
  107px. Measured per surface, not inferred from the desktop pass. Put the rule on the ROW.
- **A HANDOFF STATES WHAT IT MEASURED AND ORDERS THE NEXT SESSION TO RE-MEASURE IT.** The standing
  form for a banked session opener (`HANDOFF_*.md`): give the next session the measured state so it
  starts informed, AND tell it to verify that state against the repo, because a prompt is a memory
  the moment it's written. Everything ages — endpoint lists, chip counts, file:line cites. A chip
  in this arc said "5 call sites" when the truth was 6; a later session had added one after the
  chip was authored. Point at the doc for standing rules rather than re-listing them (a re-listed
  rule is a copy that drifts); spend the prompt's words on the WHY and on the stop conditions.
- **OPEN VERIFICATION — `.filters-sep` promotion (2026-07-15).** The rule was promoted out of its
  `.ws` scope so Notes could reuse it. Proven inert by exhaustive search (one rule for that class,
  no competitor, so the specificity drop has nothing to lose to) — but NOT measured, because Word
  study only renders its divider once a word is loaded and the harness has no lexicon fixture.
  **Close it in the next session that has a word loaded: measure Word study's rendered divider
  byte-identical (1×14, `--rule-2`).** Logged as reasoned-not-measured on purpose.
  **STILL OPEN after the News-fixture session (2026-07-15) — and now with the cost measured, not
  guessed.** It was carried as an opportunistic ride-along ("cheap once you're in the harness").
  It isn't: Word study draws the divider only behind `profile` or `groupings`
  (`80-lexicon.jsx:1013` / `:1071`), and reaching either needs a lexicon fixture over SIX
  endpoints (`lexiconLookup` / `lexiconProfile` / `lexiconVerses` / `lexiconEnglish` /
  `lexiconBooks` / `lexica`), each with its own payload to trace to its producer. That's a
  fixture project the size of the News one, not a ride-along — **so it is scheduled work, not
  scrap-time work.** The inert-by-search half re-confirmed (one `.filters-sep` rule in
  `static/styles.css`, no competitor; the `design/` hits are throwaway mockups, not the app).
- **`:hover` is a POINTER affordance — gate it on `@media (hover: hover)`.** On a touch screen
  `:hover` latches onto whatever you last touched, so drag-scrolling a list paints every row you
  held on the way past. Any hover wash on a touch-scrollable list needs the gate (the News lists,
  chips and card rows all do).
- **`.seg-b`'s selected state is a WHITE pill (`--ctl-on`) and it is SHARED** — Notes, Study,
  Library nav, the News view tabs. If a control's selected state looks wrong for its context, the
  control is probably wearing the wrong class; **restyling `.seg-b` to fix one caller silently
  restyles four others.** (News's score chips read white beside accent date chips until they were
  moved onto `.news-presets` — one rule, both.) Same shape as the "reference the system, never a
  local copy" rule: pick the right shared class, don't fork the colour.

## Three-zone shell (shared workspace frame)
Navigate / read / inspect. **Frame components in `static/src/22-shell.jsx`:** `Shell` (four-slot
frame — desktop `.zshell` grid + a real desktop→mobile collapse to a bottom toolbar `.zbar` +
`.zsheet` sheets) and `RightStack` (the inspect-panel STACK — depth 1 = one card; a child drills
via `useRightStackCtl().push()`, back pops; the PARENT owns the array via `useRightStack()` so a
center peer-select can `reset()`; lower layers stay mounted, hidden with **`visibility` NOT
`display:none`** — because these panels are `position:absolute; inset:0`, where `display:none`
would wipe an overflow box's scrollTop (the Chrome-149 proof + why it's safe elsewhere: memory
`project_three_zone_shell`). Keys are push-unique minted ids, never by card
type). `ZoneEmpty` stays in `20-shared-components.jsx`. CSS: `.zshell/.zrail/.zcenter/.zinspect`
+ `.rstack*` + mobile `.zbar/.zsheet`.

**Share the FRAME, not the CONTENTS** — never pull a tab's card/feed styling into `.z*` classes.

**top:0 split (was load-bearing; now user-preference):** a SHIPPED surface keeps
float-behind-the-nav (`.zinspect` base, `top:0`); a NEW surface's DEFAULT is BELOW the nav
(`.zinspect.rstack`, `top:var(--hdr-h)`) — BUT Ask-corpus (first real consumer) overrides back
to `top:0` (`.ac-rstack`) so its inspect floats OVER the navy header, unified with News/Word
study (the user's call — the below-nav gap read as "cut off by the top banner"). The split is
the user's per-surface choice, not a hard rule; a top:0 consumer must give each RightStack state
a header BAND (`var(--hdr-h)`) so content clears the navy header (+ a `.app.view-<x>
.hdr-right` account-pill offset).

**Migrations (all parity-only, proven by parity gates — frame DOM + computed-style diff;
Library also a Node state-machine gate):** News + Word study render `<Shell>` on desktop
(`Shell` has `railClass`/`centerClass`); Word study still keeps its own `if (isMobile)` branch,
News's mobile branch now renders `<Shell isMobile>` too (see the mobile-collapse block below).
Library's five
inspect panels carry shared `.zinspect` with `.detail-side` slimmed to its extras — its
App-level gating machine (one-at-a-time word>xref>note>summary, back-as-uncover, reconcile) is
UNTOUCHED and NOT forced into RightStack. ThreeZone retired.

**Ask-corpus = FIRST real RightStack consumer (LIVE 2026-07-01):** desktop on `<Shell>` — chat
layout; rail = threads, center = answer, inspect = the selected answer's provenance (Key passages
+ a merged "Words in scope" list). A synthesis chip + passage rows PEEK the occurrence → fork →
word drill (`.ac-rstack`, top:0). **Mobile now on the shell's collapse too (2026-07-15)** — see the
collapse block below. Spec: `HANDOFF_corpus_shell.md` + memory `project_three_zone_shell`.

**`.ac` carries a pre-existing `overflow-x: hidden` — SAFE CLEANUP CANDIDATE, not urgent.**
It predates the mobile pass and masks any sideways overflow inside Ask-corpus. The scroll JP
reported on his real phone is **GONE** — confirmed by him on device after the mobile pass shipped
("no scroll", 2026-07-15, post-deploy of `dba2edb` + `5d8e489`); the landing and the search box
were both rebuilt in those, which is the likeliest reason. Measured independently at 320 + 375,
reader + admin, landing + thread, with a detector control-tested on a forced 500px probe: nothing
overflows. So the mask is now known to be hiding nothing, and removing it is a tidy-up someone can
take whenever they're in here — no repro needed, just re-measure after. Note the trap it sets while
it stays: `document.scrollWidth` reads clean *through* this clip even with a 500px probe on the
page — use `getBoundingClientRect()` to hunt overflow here (memory
`feedback_audit_tools_must_fail`).

**Notes + Seam index + News-rail SHIPPED 2026-07-01** (desktop): Notes on `<Shell>` (rail =
note index, center = editor edited IN-TAB, right = the note's anchored verse via `VerseRow`;
editor guts shared via `useNoteEditor`/`NoteEditFields`; inspect top:0). Seam index = a `Seams`
Study module on `<Shell>` (see data-model.md, study.db). News gained a SELECTED-state inspect
(click a card → why-it-scored; `‹ Watch` resets — memory `project_news_watch`). Full record:
memory `project_three_zone_shell`.

### The Notes inspect — two defects, one panel (fixed 2026-07-15, `e9089c9`)
The anchored-verse panel shipped 2026-07-01 with two bugs that only a range note showed both of.
Both decisions are now pure in **`static/src/34-notes-logic.jsx`**, locked by
`tests/test_note_inspect.js` (in CI + pre-commit).
- **`/api/chapter` returns a BARE LIST** (`views_library.py:268`, `jsonify([...])`), and the
  Library consumes it as one (`60-library.jsx:444`, `setVerses(data)`). The panel read `d.verses`
  → always empty → the chapter's last verse always fell back to the anchor → the "after"
  neighbour could never render. **Sibling routes disagree on shape ON PURPOSE**
  (`/api/verse-words` returns `{words:[...]}`), so read the producer; don't pattern-match off the
  route next door. Two independent derivations agreeing (the Python's return + the other
  consumer's use) is what settles it.
- **A note anchors a RANGE, and the read path never looked.** `resolveSelection()`
  (`60-library.jsx:1093-1102`) stores `start.verse` and `end.verse` separately from the two edges
  of a drag-select; the panel used `start.verse` only, so a multi-verse note showed its first
  verse while the band still said "John 4:21–23". **Trace the WRITE path before believing a data
  bug** — here the write was innocent and the stored `refLabel` was already a range, so it was
  display-only: no loss, no history to repair.
- **THE LESSON — two defects on one surface can hide behind each other.** Fixing the list-read
  alone would have rendered a range note's OWN second verse as a *dimmed neighbour* — presenting
  the note's text as context, which is worse than omitting it. When one panel has two faults, fix
  them together and pin the interaction with a test; don't ship the half that looks green.
- **A label is a promise.** The old anchor row wore the range label on a single rendered verse.
  Now the band carries the range and each anchor row carries its own ref. A label that says more
  than the panel renders is a bug even when nothing crashes.

## WORD STUDY IS THE VISUAL REFERENCE SURFACE
When a visual question is ambiguous, the tiebreaker is **what does Word study do** — the way
Library is the canonical *reader* (docs/design.md), Word study is the canonical *workspace*. Six
rulings now converge on it, so this is a standing rule, not a coincidence:

| Ruling | The reference |
|---|---|
| Landing rhythm | title → search → helper → samples; an empty state names the ACTION that fills it |
| Empty-state hero mark | `width="30" height="30"` **at the call site** — never sized by CSS |
| Verse-list formatting | the **UNOVERRIDDEN base**: normal weight, inherited ink, italics recede |
| Strip grouping | groups separated by `.filters-sep` (1×14, `--rule-2`) |
| Empty-state band | a truly-empty inspect drops its band; the shared cross-line is the one divider |
| Guardrail | **Word study byte-identical** is the hard gate on any cross-surface pass |

- **It is the reference BECAUSE it is unmodified.** The verse-list ruling is the sharpest case:
  Word study has no `.corpus-text` override at all, so "converge on Word study" resolves to
  "delete the other surface's overrides" — the smallest possible fix, not a new rule. Check
  whether the reference is plain before inventing something to copy.
- **A future divergence from it needs a LOGGED reason** in the CSS at the divergence, naming what
  meaning the difference carries (Notes's anchor/near emphasis is a legitimate one: the panel has
  a distinction Word study's flat list doesn't).
- **Never "also converge" the reference.** If a pass moves Word study's pixels, the pass is wrong
  — that's how a reference stops being one.

### Italics are translator-supplied words — they never out-shout the scripture (2026-07-15, `63b550e`)
In ABP an italic word is the TRANSLATOR's, not the text's — the least original thing on the page,
so it must always be the quietest. `.lib-prose-italic` (`color: var(--ink-2); font-style: italic`)
is the ONE rule that marks them, everywhere: the KJV/BSB branches in `50-corpus-results.jsx` and
the ABP prose path in `59c-library-render.jsx` all use it. The Notes inspect broke it **both ways**
at once, and both are traps for the next surface that styles verse text:
- **Inheritance:** `.note-insp-anchor .corpus-text { font-weight: 600 }` — the italic span
  INHERITED the weight and rendered bold-italic. A weight on a verse container hits the italics too.
- **Direct-beats-inherited:** `.note-insp-near .corpus-text { color: var(--ink-4) }` dims the row,
  but `.lib-prose-italic` sets `--ink-2` DIRECTLY on the span, so it beat the inherited dim and the
  supplied word rendered **darker than the real scripture beside it** — the exact inversion of what
  italics mean. **Any rule that dims verse text must say what happens to the italics inside it**,
  because `.lib-prose-italic`'s hard-coded colour only "recedes" from the default ink.
Fix shape: leave `.lib-prose-italic` alone (the reference depends on it) and scope the correction
to the diverging surface — `.note-insp-anchor .lib-prose-italic { font-weight: 400 }` +
`.note-insp-near .lib-prose-italic { color: inherit }`.

**An empty state names the ACTION that fills the room — and the answer can differ by surface.**
Word study's is the reference ("Search a Greek or Hebrew word… to study it here"). Notes's center
said "Pick a note from the list", which is TRUE on desktop — the empty list is open beside it,
already saying "In the Library, select some text…". On a phone the collapse puts that list behind
a button, so for a reader with nothing saved the line pointed at an empty room and buried the only
first step one tap away. Fixed mobile-only (`isMobile && !anyNotes`), and that is not a fork: the
two surfaces differ *because their reachability differs*. Ask what's already on screen before
writing "pick from the list".

### Shell's MOBILE collapse — News, then Ask-corpus, then Notes (all 2026-07-15)
`MobileBar`/`ZoneSheet`/`.zbar` shipped in Phase 1 with **nothing using them** until News. **Study
is the last surface still parked** on its own old single-column branch. `Shell` mobile = center
inline + `mobile={{tools, sheet, sheetTitle, sheetBare, onCloseSheet}}`; a tool opens its zone as a
swipe-dismiss sheet. What the three consumers proved, so the next doesn't re-derive it:

- **A bar slot names a ZONE, not a verb — the DEFAULT, with one bought-out exception.** Count the
  surface's actual zones, don't inherit a button count: News collapsed three, Notes two (its list +
  the anchored-verse inspect).
  **⚠ THE EXCEPTION — Ask-corpus's "New search" (JP ruling, 2026-07-15).** This rule's own worked
  example USED to be this button ("a one-shot ACTION, so it stays in the center strip"). **JP
  reversed it on the pixels, and the reversal is the record now:** a 2-slot bar with dead space,
  sitting under a floating button that ate a row of the thread, is a worse phone than a 3-slot bar.
  Ask-corpus's mobile bar is Recent / Inspect / **New search** (`Icon.Plus`, grays until a thread
  exists). What survives intact is the rule's PURPOSE — it exists to stop a glyph/function
  MISMATCH, and `Plus` means "start a new one" and nothing else, so nothing is double-booked. The
  zone/verb split stays the DEFAULT for any new bar; this is the one place it's bought out.
  **Two things worth knowing before citing this rule or the exception:**
  - **"Primary actions live in the bar" is NOT true of this app** — it was the stated rationale for
    the change and it doesn't survive a look at the matrix. Every other bar slot in every other tab
    names a zone or a panel. The only other verb in any bar is Library's cockpit `Play`/`Pause`, and
    the cockpit is the documented odd one out (it's the mixed bar). The change stands on the
    dead-space/reclaimed-row argument, which is real and measured — not on a consistency that
    isn't there. Don't propagate the verb to a third bar by citing "consistency."
  - A verb slot sets `on: false` permanently — it fires and leaves; it is never a room you can be
    sitting in, so it must never paint an active state.
- **A MODE switch is not a zone either — and if it gates the bar's meaning, it stays in the
  center.** Notes's `Verse notes | Journal` seg decides what its list slot even holds, so burying
  it in a sheet would hide the key to the bar; it rides the center strip (`.notes-mstrip`), which
  also keeps it reachable without a tap the way the old single column had it.
- **A control the collapse BURIES needs its content moved, not just its zone.** Notes's
  search/filters sit in the desktop CENTER strip because the rail is open beside them. On a phone
  the list is behind a button, so a filter left in the center would drive a list you can't see —
  they go INTO the list sheet with the list they filter. Ask what each control acts on, not where
  desktop happens to put it.
- **A zone that doesn't apply YET grays, it doesn't vanish** (`tools[].disabled`) — gray-don't-hide,
  and Word study's bar already did it (3 of 4 tabs gray until a word loads). Ask-corpus's Inspect
  grays until the first answer. **Notes adds the PERMANENT gray:** in Journal mode its inspect is
  empty BY DESIGN (pages have no verse anchor, ever), not "empty yet" — and it still grays rather
  than dropping the slot, so the bar doesn't reshuffle under the reader when they switch modes. A
  zone that can never apply *in this mode* is still gray, not gone.
- **Prove a gray by RECTS, and prove occlusion by HIT TEST.** A disabled tool must still render a
  real 22×22 glyph box (mounted-and-hidden reads as present — check `svgW`/rects, not presence).
  And when a sheet overlaps the bar, don't compare z-index declarations: ask
  `document.elementFromPoint()` what actually paints on top. Declarations get defeated by stacking
  contexts; the hit test can't be. (Notes's sheet is z51 over the z30 bar — confirmed by hit test,
  which is why nothing inside a sheet needs its own bar clearance.)
- **Two ways to keep content off the bar; pick by whether the surface has a PINNED control.** News
  pins its shell to `100dvh - --bar-h` and lets the fixed `.zbar` float over the scrolling feed,
  which pads itself clear. Ask-corpus CAN'T — its composer is pinned to the bottom, so a floating
  bar sits on the input. It ends the shell ABOVE the bar instead
  (`100dvh - 2*--bar-h - both safe areas`, `.ac-frame.zshell-m`) and nothing inside re-adds the
  safe area. Same rule, different shape. **Notes took News's shape** — its editor's Save/Delete
  scrolls with the body, nothing is pinned — so the test is literally "is anything pinned to the
  bottom", not "does it feel like a chat".
- **⚠ MAKING A CONTAINER `display:flex` CAN SHRINK A CHILD THAT USED TO FILL IT — check every child
  for `margin: … auto` first (2026-07-15, `5eaeb23`).** Ask-corpus's mobile composer was made a flex
  COLUMN purely to re-order the quota line above the input. That silently narrowed the follow-up
  field from **339px to 215px**: `.ac-composer.pinned .ac-field` carries `margin: 0 auto`, and in a
  flex container an item with AUTO margins on the cross axis does not stretch — the auto margins
  absorb the free space and the item shrinks to fit its content. As a plain block it filled the
  width and `max-width` did the capping. **The landing didn't break, which is the tell worth
  remembering:** its auto margin sits on the COMPOSER, not on the field, so only the pinned one
  moved. A layout rule added for one child reaches every child. Fix was to scope the flex to the one
  state that needed it (`.ac-m .ac-composer.hero`). **This class of regression is INVISIBLE to the
  gates** — they're logic tests and CI has no browser — so measure a geometry change against a real
  baseline (a `git show <sha>:static/styles.css` swap; `?bundle=head` is JS-only and cannot baseline
  CSS) or it ships. This one shipped and JP caught it on his phone.
- **If the surface owns its scrolling, `.zcenter-m` must not be a second scroll box around it**
  (`overflow: hidden`), or the pinned composer floats on a nested scroller. **`.zcenter-m` is a
  scroll box BY DEFAULT** (`flex:1 1 auto; overflow-y:auto`), so any surface whose center already
  has its own scrolling body inherits a nested pair silently. Notes makes it the flex COLUMN
  instead (`overflow:hidden; display:flex; flex-direction:column`), so its fixed mode strip and
  its scrolling editor body keep exactly their desktop jobs. Count the scroll boxes by walking the
  subtree's computed `overflow-y` — don't assume.
- **A panel's own header band is DESKTOP chrome — hide it inside the sheet.** The sheet's
  `sheetTitle` already names the panel, so Ask-corpus's rail printed "Recent conversations" twice,
  one line apart (`.ac-m .zsheet .ac-rail-top { display: none }`). Caught in a screenshot, not in
  the numbers. **The other resolution: let the band BE the header and pass no `sheetTitle`.** Pick
  that when the band says something the title can't — Notes's inspect band carries the verse ref
  ("John 4:24"), which is more use than a repeated "Anchored verse". Then re-size it: a desktop
  band is `min-height: var(--hdr-h)` to clear the navy nav it floats over, and inside a sheet
  there's no nav to clear, so it's just a title row.
- **No bar collision:** `.zbar` is `bottom:0`; the app's own `.mobile-tabs` is `top:0`. The bottom
  is free. (Library's cockpit is the exception — it owns the bottom on its own tab.)
- **Pin to the visible viewport** or the whole page rubber-bands: the surface needs
  `height: calc(100dvh - var(--bar-h) - safe-top)` + `overflow:hidden`, plus
  `.app.view-<tab> .main { padding-bottom: 0 }`. Same trick as Ask-corpus's `.ac`.
- **The scroll box needs its own bottom clearance** (`--bar-h` + safe-area) or the last row hides
  behind the fixed bar.
- **A panel that carries its own header + scroll box goes in as a BARE sheet** (`sheetBare`), else
  the padded `.zsheet-body` nests a second scroll box and collapses the flex-fill. **⚠ But a bare
  sheet's CHILD owns the scroll box, so `ZoneSheet` has no `scrollRef` to hand the dismiss
  gesture** — that shipped as a real bug (scroll-up dragged the sheet shut). `useSwipeToDismiss`
  now falls back to the nearest scrollable ancestor of the touch when no ref is given (an explicit
  `scrollRef` still wins, so every other sheet is unchanged). **The fallback can't rescue a scroll
  box that isn't a plain `overflow:auto` descendant** — hand it a ref then.
  **PROVE the fallback on a FORCED overflow, never by code read.** It binds only a box that
  *actually* overflows (`scrollHeight > clientHeight + 1`), so a sheet whose fixture content is
  short exercises nothing and passes vacuously. Notes's inspect needed +1400px of injected filler
  before the gesture could fail at all. Two cases, destructive one LAST with the subject asserted
  still attached: scrolled DOWN → drag must NOT dismiss (transform stays `none`; this is the bug
  the fallback exists for), then at top → drag past 90px MUST dismiss.
- **Bottom-bar icons are 22px** (`.zbar-btn svg`), sized at the bar so every consumer inherits one
  size and the shared `Icon.*` glyphs (14–16px, drawn for dense inline rows) stay untouched. The
  in-app references DISAGREE — Word study `.wm-tab` 22px vs Library cockpit `.mbar-*` 21px — 22
  wins as the icon-only-equal-slots shape and 2:1 app-wide. Don't invent a fourth number.
  **Library's cockpit stays a documented 21px EXCEPTION** — it's the mixed bar (it carries the
  book/chapter text button), so its icons are sized to the type beside them. That's the original
  ruling's own logic applied, not amended.
- Bar height stays `--bar-h`: the app's bar rhythm and the sheets' max-height maths key off it.
- **A BASELINE read obeys settle-before-read exactly like a verification read** — and a wrong
  baseline is worse than a wrong verification, because it inverts the sign of every comparison
  after it. Notes's desktop baseline was taken ~1s after navigate and measured 1388px wide: the
  page was still tall enough for a transient scrollbar, and the post-change re-read at a true
  1400px looked like a 12px regression that never existed. Settle on a CONDITION (the rows are
  there AND `scrollHeight` stopped moving), not on a `setTimeout` guess.
- **`?bundle=head` is the baseline validator of record.** When a guardrail looks failed, A/B the
  COMMITTED bundle at the same viewport BEFORE diagnosing the working copy — same page, same
  fixtures, only the bundle swaps. That is what proved the 1388 was the bad number, not the 1400.
- **THE VIEWPORT IS ELASTIC — ASSERT `innerWidth` INSIDE THE READ, AT BOTH ENDS (2026-07-15).**
  The browser pane auto-fits its viewport to content, so a phone-width measurement is not a
  setting you make once and trust. Two ways it bit in one session: a resize to 375 silently
  reverted to 1280 during a long-running probe, leaving a MOBILE-rendered DOM (`news-m`, the
  branch had mounted at 375) laid out at desktop width — every pixel a lie, and nothing about
  the DOM saying so, because `isMobile` (`90-app.jsx:80`, `innerWidth < 1100`) only re-checks on
  a real resize EVENT that a viewport override doesn't fire. Then, worse: an overflow detector
  that planted a 500px probe **widened the window to 500**, so it compared 500 against 500 and
  reported "clean" — *the act of measuring changed the thing measured*, and the failure mode was
  a reassuring zero. **It was caught only because the detector was control-tested on its own
  known positive** (`feedback_audit_tools_must_fail`) — the check that is supposed to be a
  formality is the one that found it. So: read `innerWidth` at the START and END of the same
  script, assert both are the width you meant, and treat any injected geometry as suspect.
- **Scope every read to the surface you mean.** The desktop app mounts every view at once, so a
  bare `document.querySelector('.zempty')` or `.zbar` happily returns ANOTHER tab's
  mounted-and-hidden copy at 0×0 — it bit twice in one session (a `.zbar` that was Ask-corpus's
  while measuring Notes, a `.zempty` that was Ask-corpus's while measuring Word study). Query
  inside the owning surface's root and assert the rect is non-zero.

### Icons: ONE glyph per function, from `10-icons.jsx` (2026-07-15)
**RULE THE MATRIX FUNCTION-FIRST — one row per FUNCTION, one column per BAR, each cell the
current glyph; then one ruling per row.** This is the method, not a formality: the first pass
tabulated by glyph ("who uses `WsI.Search`?"), unified the source inside one tab, and declared
the app-wide job done — while `Icon.Info` still meant *chapter overview* in Library and *how the
feed works* in News, and `Icon.Grid` meant *chip view* in the reader AND Word study's "Views". A
glyph-first list cannot surface a double-booking by construction; a function-first one surfaces
it in the first pass. The settled matrix:

| Function | Library cockpit | Word study | News | Ask-corpus | Notes |
|---|---|---|---|---|---|
| Search | `Search` | `Search` | — | (inside the field) | (inside the list sheet) |
| Detail panel / inspect | `Panel` | `Panel` (word card) | `Panel` (Watch) | `Panel` | `Panel` (Anchored verse) |
| Filter — narrow the set | — | `Filter` ("Views") | `Filter` (Options) | — | (inside the list sheet) |
| Reading/display options | `Modes` | — | — | — | — |
| Playback ‡ | `Play`/`Pause` | — | — | — | — |
| Start a new one ‡ | — | — | — | `Plus` (New search) | — |
| The list you navigate by | `[Book Ch]` text | `Book` | `Hash` | `Clock` | `Note` / `Book` † |

‡ The two VERB rows — the exceptions to "a bar slot names a zone" (see the rule above). `Plus` is
Ask-corpus's, JP-ruled 2026-07-15. Both are bought-out cases, not licence for a third: a verb needs
its own ruling, and it never paints an active state.

† Notes's list slot is **MODE-FOLLOWING** — the first one. One slot, two content names: `Note`
(pencil) for "Verse notes", `Book` for "Journal pages", flipping with the `Verse notes | Journal`
seg. Allowed *because* the row names content and this list's content genuinely changes; a fixed
glyph would have to be wrong in one mode. **Conditions on any future mode-following slot:** the
mode control must be VISIBLE on the same screen as the bar (Notes keeps its seg in the center
strip for exactly this — a slot whose meaning changes behind a closed sheet is a trap), and both
names must already be in that tab's own vocabulary.

- **The last row is content-named ON PURPOSE — do NOT merge it.** Those glyphs name what the
  list *holds* (threads are hashes, recent is time, distribution is books); one shared glyph
  would put a hashtag on "Recent conversations". Tab-specific by design, not drift.
- **CROSS-TAB REUSE PRECEDENT (Notes, 2026-07-15): the last row is per-tab SCOPED, so the same
  glyph may serve two tabs' list slots.** `Book` is Word study's Distribution button AND Notes's
  journal list. Tolerated because bar glyphs are only ever seen one tab at a time, and because
  the reusing tab **already owned that glyph in its own vocabulary** (Notes's journal ZoneEmpty
  used `Icon.Book` long before the bar did) — reaching for the tab's existing word beats minting
  a novel one. This licence is for the content-named row ONLY; every other row is app-wide
  one-glyph-one-function and a collision there is still a bug.
- `Info` means **help** and nothing else. `Grid` means **chip view** and nothing else. `Modes`
  means **reading options** and nothing else. Check here before reusing any of them.
- **A control's LABEL is not its function — open the sheet.** "Views" got the grid glyph off its
  name; it actually holds Edition/Testament/Go-deeper, i.e. a filter. Read the contents, then rule.
- **Verify a merge by SHAPE, not by the component name you typed** — compare the drawn children
  (`rect3|pathM15 3v18` etc.) across bars; that's what proves two bars really share a glyph.
- **THE WHOLE MATRIX IS NOW VERIFIED BY DRAWN SHAPE (2026-07-15, `b2fa9be`).** News was the last
  holdout — its mobile branch couldn't reach its `<Shell>` without feed data, so two passes
  reasoned about its three glyphs from the shared components instead of seeing them. The harness
  News fixture closed it: rendered at an asserted 375px, News reads Threads=`Hash`
  (`M10 3 8 21…`), Watch=`Panel` (`rect[3 3 18 18 rx2] + M15 3v18`), Options=`Filter`
  (`M3 6h18M6 12h12M10 18h4`) — the matrix as ruled, nothing re-ruled. Cross-bar by shape: the
  Panel row is BYTE-IDENTICAL across News's Watch, Ask-corpus's Inspect, Notes's Anchored verse
  and Word study's Word card (four bars, one glyph), and News's Options equals Word study's
  Views. **The reasoned-from-components reading turned out RIGHT — which is the point worth
  keeping: it was right, and it was still unverified.** A correct guess and a measurement are
  the same value and different facts.
  Notes's three slots read back `pathM4 20h4L18.5 9.5…` (pencil), `pathM4 4.5A2.5…` (book) and
  `rect3|pathM15 3v18` (Panel — character-for-character the shape above).
- **Drive a state change THROUGH the control, and hit-test it first.** `el.click()` fires happily
  on something `display:none`, so a mode flip "verified" that way proves the state changed, not
  that a reader could change it. Read the button's rect, ask `elementFromPoint()` at its centre
  whether that button is really what's there, tap THAT, then re-read the glyph by shape.
`Icon.*` is the only icon set. Word study used to keep a private `WsI` — deleted, because it was a
**fork, not drift**: its `Sliders` was character-for-character identical to `Icon.Modes`, and that
one drawing meant "Views" in Word study and "Reading options" in Library. One glyph, two jobs, in
two bars. `Card` + `ChevR` had no shared twin, so they were **promoted into `Icon`** rather than
deleted. Views now takes `Icon.Grid` (arrangement); `Icon.Modes` means reading options and nothing
else.
- **Never fork a glyph to resize it.** The `Icon.*` components spread props, so pass
  `width`/`height` at the call site (`<Icon.Search width="20" height="20"/>`). This is load-bearing:
  the CSS around those uses sets only the flex SLOT (`.wm-search-i { flex: 0 0 20px }`), never the
  glyph, so swapping a 20px fork for a bare 16px shared component silently shrinks a shipped
  control. Bars are the exception — they size at the bar (`.zbar-btn svg`, `.wm-tab svg`), so bar
  buttons take the component bare.
- Before adding a glyph, grep the set for the FUNCTION, not the shape.

## Library tab
Full per-feature history in memory (each block names its file). Standing rules + gotchas here.

### Layout
- Desktop toolbar (lib-bar): `[‹ Ch ›] | [Compare ▾] | [Strong's] [Interlinear] | [Chip] [Prose]`.
  Text source lives in the LEFT NAV, not the toolbar. ABP/BSB/HEB one-click (HEB grays on NT;
  falls back to KJV in the slot if heb.db absent); KJV/ESV/NIV + non-canon fold into a
  **"More ▾"** popout. (KJV demoted into "More" 2026-06-22 — BSB is the default English; the
  `kjvInMore = hebShown` flag keeps KJV up top only when heb.db can't fill the slot.) The source
  row + Eras/Days are **underline tabs**, NOT boxed segments — the source row is a 4-equal-column
  grid (`.nav-source-seg.seg`) so a long "More" label can't shove the others.
- Mobile cockpit (lib-toolbar, fixed at the BOTTOM/thumb-zone on Library) is an ICON row of five
  EQUAL-width slots (2026-06-20): `[🔍 Search] [▷ Play] [Abbr Ch] [ⓘ Info] [⚙ Options]`. Center
  slot shows the 3-letter book abbreviation ("Amo 1"); right slot is sliders `Icon.Modes` (opens
  the reading-options sheet). Audio scrubber docks above the cockpit (`.lib-audio-dock`);
  desktop chrono keeps the inline one. The play button GRAYS (not hides) when a text has no
  audio, keeping the row balanced.
- Compare ▾, the "More" popout, and the Aa size/theme menu close on outside-click/Esc AND
  **swallow that dismiss click** (capture-phase one-shot) so it doesn't hit a chip behind them.

### Text sources / HEB
- HEB = public Hebrew OT interlinear (memory `project_hebrew_ot_interlinear`): OT books only
  (book list + mobile picker drop NT in HEB mode), NO chronological order (grayed in Hebrew).
  On a non-Hebrew text sitting on a NT book the HEB selector is grayed, not hidden.
- **Gray-vs-hide is the user's per-control call** (memory `feedback_gray_dont_hide`): GRAY a
  real feature that doesn't apply here (HEB on NT, Search on ESV/NIV, mobile play w/o audio);
  HIDE Compare + the order toggle on non-canon, and ESV/NIV (copyright). Propose gray for
  inactive-but-applicable, confirm per control.

### Reader appearance (memory `project_reader_appearance`)
- Reader font = `--f-serif` (Source Serif 4). `Aa ▾` menu / mobile ModesSheet hold A−/A+ size +
  the Light · Sepia · Dark theme toggle. A font PICKER was tried and reverted — don't re-add.
- Verse number + per-word Strong's SCALE with A−/A+ (`.lib-vnum` ≈0.5×, `.lib-iw-strongs` ≈0.53×
  of `--lib-font-size`) — keep relative, never fixed px.
- Themes ride `data-theme` on `<html>` (`lexica.theme.v1`); colors are vars at the TOP of
  styles.css. **New buttons use `--ctl-bg`/`--ctl-on`, never hardcoded `#fff`.** Dark traps: an
  `--ink`/`--accent` background flips LIGHT in dark, so pair its text with `var(--paper)`;
  borders use `var(--rule)` not `var(--line)`; navy header stays navy in every theme.
- **Palette tokens (reset 2026-06-19 to the Claude Design spec — implement his calls, don't
  freelance hues):** `--accent` = STEEL-BLUE (oklch 240, primary links/active), `--ai` = VIOLET
  (280, AI features), `--hl-match` = `#f0d27a` (the ONE shared gold for a matched/target word —
  `.corpus-hit` + `.lib-search-mark`, fixed across themes). **Gold (`--gold`) is RESERVED for
  target words ONLY** — active tabs, count pills, etc. use `--accent`. Navy = brand header + the
  chronological "you are here" active-passage rule (shared
  `.nav-passage.on/.plan-passage.on/.mpick-passage.on`, dark falls back to `--spine-nt`).
  **NO brown anywhere** — markers/hovers use `--accent`, not `--gold` (memory
  `feedback_no_brown`). Memory `project_ai_search_redesign`.
- Desktop scrollbars slim app-wide + `html { scrollbar-gutter: stable }` so swapping ABP↔KJV
  never shifts layout. Fonts load **`display=optional`, NOT `swap`** (templates/index.html) —
  kills the mobile toolbar reload flash. Don't switch back.

### Render modes (memory `project_reading_modes`)
THREE ABP reading modes, `viewMode` = chip|prose|interlinear (2026-07-04; a 3-way
Chip·Interlinear·Prose control, Interlinear ABP-only).
- **Chip** = words clickable, **English reading order** (bracket groups reordered by `greek_pos`
  ascending); ABP `[ ]` marks + superscript order digits are **STRIPPED from chip** —
  interlinear-only now.
- **Prose** = plain inline, only verse numbers tappable. Clicking Prose always works: it
  SNAPSHOTS the Strong's/Interlinear toggles, unticks both, switches; the next switch away
  restores them (a manual toggle touch discards the snapshot). Snapshot lives in `libOptions`
  (`lexica.opts.v1`).
- **Interlinear (mode three)** = faithful as-printed ABP: Greek main line in **source order (NO
  reorder)** with the `[ ]` marks + superscript digits, English gloss ABOVE + Strong's BELOW
  driven by the Interlinear/Strong's toggles (both default ON on entry; a line toggled off is
  NOT rendered so its space collapses → bare Greek reads tight). PN Greek line falls back
  inflected→lemma→capitalized English name; Strong's prints `strongs_base` verbatim (H#### stays
  H####). ABP-only (`translation==="abp"`); other texts read a stored `interlinear` value as chip.
- Toggle semantics UNIFORM: Interlinear = gloss layer, Strong's = number layer, over whatever
  base a mode shows. KJV locks Prose to English. English-only non-canon: Chip = verse-per-line
  (`renderExtraLines`), Strong's/Interlinear locked.
- Order helpers (`getEnglishOrderWords`/`groupForGreekMode`/`orderBracketGroupWords`), the
  Greek-line fallback (`greekLineForWord`), the PN click payload (`pnClickPayload`), and the
  prose/toggle reducer (`libViewTransition`) all live in shared
  **`static/src/56-library-order-logic.jsx`** (browser globals + Node `module.exports`),
  Node-tested by `tests/test_library_order.js` + `tests/test_render_markup.js`.
- **Bracket trail punctuation must land on a chip that RENDERS** (Jer 46:15 class, fixed
  2026-07-11): chip mode lifts a group's clause mark and re-emits it after the group's last
  member — but a label-less folded pronoun/article sorts LAST (no order digit) and its chip is
  null, so the mark silently vanished (4,395 verses / 4,925 marks). Landing spot =
  `lastRenderedIndex` in 56-library-order-logic.jsx (walks back to the last member with
  english/english_head — prose's float in `getEnglishOrderWords` already guarded this way);
  pinned by test 16. Sizing tool (read-only, Jer 46:15/16 controls):
  `scripts/audit_chip_trail_drop.py`. Residual: 11 doubled-mark verses (TODO.md).
- **Hebrew "Prose" = the same interlinear chips flipped LEFT-TO-RIGHT** (2026-06-22): the Prose
  button toggles `viewMode` and a `.lib-heb-ltr` class setting row/content `direction:ltr` —
  only WORD order flips; each `.lib-iw-heb` keeps its own `direction:rtl` so letters stay
  correct. Strong's/Interlinear still work. Flag `hebProse = hebMode && viewMode==="prose"` in
  BOTH 60-library.jsx and 59b-library-nav.jsx. Matches the Ask-corpus Hebrew layout.
- **Chip-vs-prose OUTSIDE the reader** (memory `project_lexicon_tab`): CHIP (ABP brackets +
  punctuation outside `]`) = reading pane + side-card interlinear. PROSE (plain, no brackets) =
  TSK xref, Study verses, side-card quote, in-text find list, Search + Lexicon result lists.
  Don't bracket the prose surfaces.
- **ABP brackets render INLINE in the reader's chips** (memory `project_library_bracket`):
  `[`/`]` ride inside the word's english cell (`.lib-iw-brk`), NOT a separate column. Old
  `.lib-bracket*` column CSS is dead.
- Italic = translator additions, muted/italic: KJV (italic=1), ABP (words.italic=1), ABP `[word]`.

### Compare (memory `project_pericopes_parallel`)
- Pick 2–4 of ABP/KJV/BSB/ESV/NIV side by side (`translation === "parallel"`, `compareSel`).
  Desktop = N columns; mobile = stacked, one labeled line per text. Notes/highlights shared
  across columns (whole-verse paint).
- Labels are **navy, not gold**. Mobile per-line label runs INLINE with the verse — the chip box
  MUST be plain `inline`, NOT `inline-flex` (inline-flex drops a wrapping verse below the
  label). Chip mode IS allowed in compare (only place ABP Greek shows beside translations).
- Desktop picker = checkbox dropdown on Compare. Mobile = the Reading sheet's Text picker:
  TAP = read one, LONG-PRESS = tick into the 2–4 compare set.

### Chronological / reading plan (memory `project_chronological_tab`)
- Reading-order toggle Canonical|Chronological, any version. Static `chronological.json`
  (no DB). An `Eras | Days` toggle atop the chrono picker.
- Days = a 365-day plan with per-text progress (`lexica.plan.v1`), binned into ~12 collapsible
  Month blocks. Component `static/src/58-dayplan.jsx`.
- Chrono mode shows an ESV-style daily Reading-intro panel (AI title+summary + era timeline):
  `views_chrono.py` + `static/src/59-dayintro.jsx`.

### Navigation / jumps
- Left-nav book list is an ACCORDION (memory `project_book_nav_polish`): click a book to open
  its chapters, click again to collapse; testament spine + per-book chapter counts. Hover/active
  pills use `color-mix(... var(--bg) ...)`, NOT `--bg-sunk` (invisible on sepia). Mobile
  `Book Ch ▾` opens to the BOOK list first.
- Jumping to a verse lands it in the UPPER THIRD; the left nav scrolls the active book to the
  TOP of its own list, never the window. The verse-number click target is an inner
  `.lib-vnum-num` hugging the digits (the empty gutter is inert).
- **Chrono jump rule:** an EXTERNAL jump (Search/Lexicon/Notes — flagged `nav.extern`) drops the
  reader back to canonical; an IN-READER jump (verse-number xref, word panel, chasing an xref)
  STAYS chronological (moves `chronoPos`). Either way `chronoPos` survives.
- **Rail + jump-marker reconcile (2026-06-29):** the reader's real position lives in LibraryView
  (`selBook`/`selChapter`); the rail cards (`libCrossRef`/`activeEntry`/`activeNote`) + the gold
  jump-marker (`libNav`) live in App. LibraryView reports every move via `onReaderPos`; App's
  `handleReaderPos` keeps a card/marker that MATCHES the new book+chapter and drops the rest.
  This is the ONE place that keeps them in step — don't add a browse handler that moves
  `selBook`/`selChapter` without it, and never spread the old `nav` bag into a new one (a stale
  `translation`/`extern` rides along — the page-turn text-snap bug). Also here: `setOrder`
  canonical keeps the passage's book; `turnPage` emits a clean nav object. Memory
  `project_nav_reconcile`. **`onReaderPos`/`handleReaderPos` carry only (book, chapter) — NO
  verse.** So in chrono the reconcile MUST keep the passage you're already on when it still
  covers that chapter; else a chapter split across a day boundary snaps you to the FIRST passage
  covering it and the clicked plan day never opens — hit 141/365 days (fix cf5c6ec, shared logic
  `static/src/57-chrono-logic.jsx` `chronoReconcile`, locked by `tests/test_chrono_reconcile.js`).
- Clicking a verse number opens the TSK Cross-Reference panel. Desktop link-over from
  Search/Lexicon auto-opens that verse's xref card over the chapter summary.

### Detail rail (memories `project_side_panel_rail`, `project_detail_panel_interlinear`,
`project_bsb_words`)
- Word clicks → LSJ (G-numbers), BDB (H-numbers), or metaV (proper nouns); KJV/Hebrew route the
  same. The side panel's Interlinear toggle FOLLOWS the reading text; Greek/Hebrew leads,
  English muted. ABP brackets inline.
- Headword = the dictionary lemma (big) + its dictionary gloss; the word's *in-this-verse*
  English sits DOWN on the inflected "in this verse" form line (Hebrew/BSB/ABP; ABP form via
  `abp_surface`; KJV has none). **Lemma gloss = the `word_gloss` side table** (see
  data-model.md), which REPLACED the KJV-ized `lexicon.kjv_def` ("charity"/"Ghost"). The card
  shows the plain meaning up top for EVERY word with a gloss that isn't a name/place
  (`showLemmaGloss` in 30-detail-panel.jsx) — words with an "in this verse" form line drop the
  contextual english onto it; no-form words let the meaning replace the in-verse word up top.
- Rail stacks ≤3 deep: summary/Intro → xref → (word OR note). The "‹ back" link NAMES the card
  beneath it; the note card keeps just an X (DESKTOP). Word/xref panels trigger `has-detail` →
  compacts `.lib-reading` on desktop.
- **Mobile = bottom sheets, unified 2026-06-19:** every rail panel + word-study/notes/reading
  sheet shares ONE slide-up animation + scrim + radius/shadow and closes by **swipe-down +
  tap-scrim — NO close X on mobile** (X stays on DESKTOP panels; real centered modals keep
  theirs). Section spacing aligns to the LOCKED word card. `useSwipeToDismiss`, memory
  `project_mobile_gestures`. Heights still drift (not yet unified — see that memory).

### Other Library features
- Focus mode (memory `project_focus_mode`): tap blank to enter, Esc/tap exits. Mobile hides
  chrome. Desktop (rebuilt 2026-06-19): a dark + blurred wash makes the chrome RECEDE and go
  non-interactive (click the wash to exit); the centered "book page" is READ-ONLY — any tap
  exits, word/verse clicks off. Light shadow, plain ‹ › chevrons (circles tried + reverted).
  Not remembered across reloads.
- In-text search (magnifying-glass panel, memory `project_esword_reference`): searches the
  current text; modes Any/All/Phrase; range presets + whole-word/case/exclude;
  `/api/text-search`. Gotcha: `_ABP_RANK_SQL` for canonical ABP sort (verses.book is text).
- Library remembers your spot across reloads (memory `project_refresh_persistence`): the
  `lexica.*` keys restore book/chapter/translation/order/compare/theme/font. **Lesson: restore
  instant toggles synchronously in the `useState` initializer, not an async effect — else the
  default flashes before the saved value.** Wheel over fixed chrome doesn't scroll the reading
  pane.

## Notes, highlights, bookmarks + accounts (memory `project_notes_highlights`)
- **Sign-in lives in the DESKTOP header:** a "Log in" pill (opens `AuthModal`, `authOpen` in
  90-app.jsx) when signed out, or your display name (else email) when signed in. Clicking opens
  the **account panel as a dropdown anchored under the button** (`AccountModal anchored`,
  `accountOpen`) — no longer jumps to Notes (2026-06-20). Signed-in label is PLAIN TEXT.
  **Mobile has NO header** — account + login live in the **"You" sheet** (rightmost mobile
  bottom-toolbar slot, replaced About; `YouSheet` in 90-app.jsx, 2026-07-05): person/initial
  icon → bottom sheet with account row (login form, or account+logout), an appearance section
  (font size + theme, sharing lifted App state), and an About row. **The Notes tab renders NO
  login row** (mobile or desktop). `AccountModal` is `anchored={!isMobile}` — desktop dropdown,
  CENTERED modal on mobile.
- **Browser-local first; accounts are OPT-IN.** Notes live in `localStorage` `lexica.notes.v1`;
  fully usable with no account. Signing in syncs across devices. One record = a word-position
  anchor + optional text/color/bookmark flag — a note, highlight, and bookmark are the SAME
  record: `{id, device, corpus, translation, book, bookName, chapter, start:{verse,pos},
  end:{verse,pos}, snippet, body, color, bookmark, deleted, created, updated}`. `id` minted AT
  CREATION. Delete is SOFT (`deleted:true` tombstone) so deletes propagate through sync/import.
- **Accounts / sync — `notes.db`, the FIRST + ONLY visitor-write path on the site.** Kept OUT
  of bible.db (corpus is rebuilt; user data must survive). `core.notes_db()`; tables `users`
  (optional `name` display column), `tokens`, `notes` (keyed `code = "u<user_id>"`).
  `views_notes.py`: `/api/auth/signup|login|logout|me|config|google|set-name|delete-account` +
  `/api/notes/sync` (Bearer token). `delete-account` permanently removes user + all data (the
  confirm makes you type "delete"). Passwords one-way hashed (werkzeug). Stay-logged-in = random
  bearer token in `tokens` + `localStorage` `lexica.auth.v1`. Sync = two-way last-write-wins by
  id. Guards: rate limits, size/count caps, parameterized SQL. Tables auto-create. Password
  reset + set-password (Google-only accounts can add one) LIVE 2026-06-16 via SMTP/Resend —
  `request-reset`/`reset`/`set-password` + `password_resets` table; emailed link opens
  `/?reset=<token>`. `request-reset` always returns ok (never reveals whether an email has an
  account); `reset` is single-use + 1h + clears every session. NO email verification on signup
  yet. Mail gotchas: memory `project_email_smtp`.
- **Google sign-in (optional).** `/api/auth/google` verifies Google's signed token
  (`google-auth`), finds-or-creates by email. Shows only when `GOOGLE_CLIENT_ID` is set AND
  `google-auth` importable — both checked LAZILY in `_google_ready()` so a deploy before setup
  can't break the site.
- Gestures (do NOT fight word-click=lexicon / verse-number=TSK): drag-select text → bar with 5
  color swatches + "Note"; right-click (desktop) / long-press (mobile) a verse number → menu
  (Bookmark · Note · 5 colors). Mobile "Add note" bar pins to screen bottom (clear of the OS
  copy/share toolbar); `selectionchange` backstop. Inline bookmark marker at verse start
  (indents first line only).
- Anchoring is PER READING TEXT, covers non-canon too. ABP AND BSB capture exact word-spots
  (`data-note-pos` on chip spans, `data-note-verse` on rows); KJV anchors whole-verse.
  Square corners + flush chips make a multi-word highlight one continuous bar. Same-anchor
  reuse (no dupes) via `NotesStore.findAnchor`.
- **Highlights paint across ALL translations (verse-level).** `chapterNotes` (`forChapter`)
  gathers every translation's records; `hiForWord` paints EXACT words only in the text it was
  made in and ROUNDS UP to whole verse elsewhere. ABP and BSB paint per-WORD in their own text;
  KJV still whole-verse only (kjv_words has positions, so the BSB `renderBsbVerse` pattern
  could close it).
- **Journal** — free-form second note mode. "Verse notes | Journal" toggle. A journal page =
  same record shape with `kind:"journal"` + `title` + `body`, NO anchor — autosaving full-page
  editor, same store/sync. Store: `journals()`, `createJournal()`,
  `getActiveJournal()`/`setActiveJournal()` (`lexica.journal.active.v1`), `appendToJournal()`.
  Merge guard lets `kind:"journal"` through without anchor; `all()` keeps journals out of the
  verse-note list. Server cap `_MAX_JOURNAL_BYTES` 64KB vs notes' 8KB.
- **Copy + send-verse-to-journal from the reader.** Both the drag-select bar AND the
  verse-number menu carry Copy + Journal (appends `Genesis 1:8 (ABP) — text` via `journalLine()`
  in 60-library.jsx, to the OPEN journal page; none open → flash "Open a journal page first").
  A `lib-flash` toast confirms. Both menus share ONE left-to-right order — colors · Note ·
  Journal · Copy (· Bookmark on the verse menu only) — keep aligned if you touch either.
- Files: `static/src/12-notes-store.jsx` (NotesStore + sync/auth + journal helpers +
  NOTE_COLORS/NOTE_COLOR_CSS + useNotesVersion), `static/src/35-notes.jsx` (NoteAddPopover,
  VerseNoteMenu, NoteColorRow, NotesPanel editor, JournalView/JournalEditor, NotesView tab,
  AuthModal). Wiring in 60-library.jsx + 90-app.jsx. Notes tab: text search + filters
  (All/Bookmarks/Highlights/Notes) + sort (Recent/Reference) + collapsible group-by-book +
  Journal toggle. Export/Import buttons dropped from UI (store/sync code stays).
