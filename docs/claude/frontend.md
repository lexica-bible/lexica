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
- **Mobile <1100px**: no header, sticky mobile toolbar (lib-toolbar), bottom tab nav, panels as
  bottom sheets.
- JS thresholds: `navVisible >= 1100`, `isMobile < 1100` (two states only).
- CSS: `@media (max-width: 1099px)` / `(min-width: 1100px)` — plus 520px for very small phones
  and a **1500px header nav-overflow** breakpoint (below it the desktop header hides the inline
  nav into a hamburger; subtitle stays). The header actually runs out of room ~1471px: Word
  study / Library / News reserve 472px (`--sidebar-w + 12`) on the right for the floating word
  card. Hamburger = `Header` in `20-shared-components.jsx`; CSS `.hdr-burger`/`.hdr-menu` +
  `@media (max-width:1499px)`.
- One shared height `--bar-h` (48px, :root) sizes EVERY mobile chrome bar (top nav, Library
  cockpit `.lib-toolbar`, `.wm-tabs`) + sheet clearances — bars/sheets use `100dvh` + safe-area,
  never `100vh`.

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
Library also a Node state-machine gate):** News + Word study render `<Shell>` on desktop (each
keeps its own `if (isMobile)` branch; `Shell` has `railClass`/`centerClass`). Library's five
inspect panels carry shared `.zinspect` with `.detail-side` slimmed to its extras — its
App-level gating machine (one-at-a-time word>xref>note>summary, back-as-uncover, reconcile) is
UNTOUCHED and NOT forced into RightStack. ThreeZone retired.

**Ask-corpus = FIRST real RightStack consumer (LIVE 2026-07-01):** desktop on `<Shell>` — chat
layout; rail = threads, center = answer, inspect = the selected answer's provenance (Key passages
+ a merged "Words in scope" list). A synthesis chip + passage rows PEEK the occurrence → fork →
word drill (`.ac-rstack`, top:0). Mobile still the old layout. Spec: `HANDOFF_corpus_shell.md` +
memory `project_three_zone_shell`.

**Notes + Seam index + News-rail SHIPPED 2026-07-01** (desktop): Notes on `<Shell>` (rail =
note index, center = editor edited IN-TAB, right = the note's anchored verse via `VerseRow`;
editor guts shared via `useNoteEditor`/`NoteEditFields`; inspect top:0). Seam index = a `Seams`
Study module on `<Shell>` (see data-model.md, study.db). News gained a SELECTED-state inspect
(click a card → why-it-scored; `‹ Watch` resets — memory `project_news_watch`). Mobile for all
three stays the old layout. Only remaining consumer = **News-on-mobile** (net-new, not a
migration). Full record: memory `project_three_zone_shell`.

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
