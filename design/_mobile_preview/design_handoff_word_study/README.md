# Handoff: Word Study Module (Lexica)

## Overview
**Word Study** is one module of *Lexica*, an AI-assisted Greek & Hebrew Bible word-study tool. This module lets a user look up a single lemma (Greek/Hebrew word, transliteration, English gloss, or Strong's number) and study it across the whole biblical corpus: its sense distribution by book, every occurrence in context, and a full lexicon "word card" (LSJ definition, ABP/KJV renderings, derivation, cognates).

This bundle contains **two layouts of the same module**:
- **Desktop** — a three-pane workspace (`Word Study.html`).
- **Mobile** — a phone layout with a navy module bar on top and a working toolbar on the bottom (`Word Study Mobile Preview.html`, rendered inside an Android device frame for preview).

## About the Design Files
The files in this bundle are **design references created in HTML/React-via-Babel** — runnable prototypes that show the intended look and behavior. They are **not production code to ship directly.** The task is to **recreate these designs in the target codebase's environment**, using its established patterns, component library, and data layer. The real app is a Flask backend serving JSX (see the `lexica-bible/lexica` repo); reuse its conventions. If no environment exists yet, choose an appropriate framework (these prototypes are plain React 18 + CSS, so React is a natural fit) and implement there.

All "data" in `word-study-data.jsx` is **illustrative sample content** (a handful of lemmas and verses), not the real corpus. Wire the UI to the real lexicon/occurrence APIs.

## Fidelity
**High-fidelity.** Final colors, typography, spacing, and interactions are all intended as shown. Recreate pixel-faithfully using the codebase's libraries. Exact tokens are listed under **Design Tokens** below; they are also defined as CSS custom properties at the top of `styles.css`.

---

## Screens / Views

### 1. Desktop — Word Study (`Word Study.html` → `word-study.jsx` + `word-study.css`)
A full-viewport, three-column workspace under the shared navy header. Columns (left→right):

**A. Distribution rail (left, 248px; 232px ≤1320px)** — `BookRail`
- Eyebrow "Distribution by book" + the active lemma (Greek) and book count.
- A scrolling list of books the word occurs in, **sorted by frequency desc**. Each row: book name · a horizontal frequency bar (width ∝ count/max, min 7%) · the count (mono). NT books use steel-blue fill, OT books use gold fill (`TESTAMENT(book)` decides).
- "All books" pinned row at top (paper card, shows total occurrences). Selecting a book filters the occurrence list; selected row is filled navy with light text + gold bar.
- Background `--bg-sunk`, right hairline `--rule`.

**B. Center — search + occurrences (fluid, min 0)** — `SearchBar` + occurrence list
- Sticky search bar at top (paper field, 46px tall, 11px radius, `--rule-2` border, focus ring steel-blue). Placeholder: "A word, transliteration, or Strong's №…". Navy go-button (38px, 8px radius) with arrow.
- **Senses pivot (collapsible)** — `SensesBar` — appears only when the query is an English gloss that maps to multiple lemmas (e.g. "spirit" → πνεῦμα, רוּחַ, נְשָׁמָה). See "Senses pivot" below.
- Filter notice row (when a book is selected): "Filtered to **Book** · N occurrences" + Clear.
- Toolbar of quiet underline toggles: testament `All / OT / NT` and edition `ABP / KJV`. Active toggle = ink text + 2px gold underline.
- **Occurrence list** (`VerseRow`): each row = reference (mono, gold, min 62px) + verse text (Source Serif, 15.5px, line-height 1.5). In ABP edition, tagged target words render as buttons (clicking studies that lemma); the studied lemma is gold. In KJV edition, the gloss words are highlighted with `<mark class="w-hit">` (gold).
- Center column max-width 780px, centered, padding 18/28/70.

**C. Word card (right, 424px; 392px ≤1320px)** — `WordDetail`
- Header: Strong's number (mono) + "‹ Overview" button.
- Hero: large Greek/Hebrew lemma (`--f-greek`, 60px; Hebrew 52px RTL), transliteration · gloss (Source Serif 19px), morphology · type (13px), and an **"Ask AI about <word>"** pill (steel-blue, links to `Ask the Corpus.html?w=STRONGS&tr=…&gk=…`).
- Sections (each separated by a top hairline, 11px uppercase tracked label):
  - **Liddell-Scott-Jones** (LSJ) — short definition with a "Full entry ⌄" expand toggle; LSJ badge (mono, steel-blue).
  - **ABP renders as** — inline list of rendering words each with a small mono count; first is bold. "N senses" meta.
  - **KJV renders as** — same pattern.
  - **Derivation** — italic serif note.
  - **Cognates & related lemmas** — buttons (Greek + translit + gloss + Strong's) that navigate to that lemma.
- Left hairline `--rule`, paper background, body scrolls.

**Responsive collapse (desktop file):** ≤1040px the right card becomes a fixed slide-over (toggled by a header button) with a scrim; ≤760px the left rail also becomes a slide-over; ≤600px the header nav and some chrome hide. (On true mobile, use the dedicated mobile layout instead.)

### 2. Mobile — Word Study (`Word Study Mobile Preview.html` → `word-study-mobile.jsx` + `word-study-mobile.css`)
Phone layout. (The preview wraps it in `android-frame.jsx`; in production drop the frame and let the app fill the viewport.) Top→bottom:

**A. Navy module bar (top, 54px)** — `NavBar` — the **global app nav**, identical destinations to desktop's header: brand mark + six icon tabs — Library · **Word study** · Ask the corpus · Notes · Study · About. Background `--navy`; inactive icons `rgba(231,236,245,0.58)`; the active tab (Word study) is `--gold` with an 18px gold underline. This is the same nav on desktop and mobile — only its position/representation changes (text tabs on desktop, icons on mobile).

**B. Context strip (below nav)** — `wm-ctx` — shows what you're currently studying: Greek lemma (26px) + translit · gloss, with a quiet chevron at the right. Tapping it opens the Word card sheet. Paper background.

**C. Reading area (fills middle, scrolls)** — `wm-main`
- Optional **senses pivot** (collapsible) when a gloss matched multiple lemmas.
- Occurrence header: big count + label ("occurrences" or "in <Book>") + a mono meta of active filters (e.g. "ALL · KJV").
- Book-filter chip (when filtered) with Clear.
- Occurrence list (same `VerseRow` vocabulary as desktop).
- Empty/welcome states when no word is selected (welcome shows tappable example chips).

**D. Working toolbar (bottom)** — `wm-tabs` — the **per-screen tools** (distinct layer from global nav). Four icon+label items, each opens a bottom sheet:
- **Search** → search sheet (autofocus field + gloss/Strong's example chips).
- **Distribution** → the book rail (`RailBody`).
- **Word card** → the full word card (`CardBody`).
- **Views** → edition (ABP/KJV) + testament (All/Old/New) segmented controls, plus an "Ask the corpus" jump.
Active tool tinted steel-blue.

**Bottom sheets** — `Sheet` — rise from the bottom; tall sheets (Distribution, Word card) take ~90% height, Views/Search size to content. A grab zone (handle + header) supports **drag-down-to-dismiss** (pointer events; release past ~110px closes). A scrim sits behind. (This mirrors the Library mobile sheet pattern.)

> Layout principle established in design: **global module nav lives at the top (mirrors desktop); the module's own tools live in a bottom toolbar (thumb reach).** Apply the same shape to every module's mobile view for consistency.

---

## Senses pivot (collapsible) — `SensesBar` / `SensesBarM`
When the search term is a plain-English gloss (or otherwise ambiguous) that maps to several lemmas, the app lands on the highest-frequency lemma's full study view and shows a pivot bar above the occurrences instead of a dead-end list.
- **Header row** (button, toggles open/closed): "**N** words rendered "spirit"" + a Collapse/Expand control with a chevron that rotates 180° when open. When **collapsed**, the header also shows the active lemma inline (Greek + translit + count) so context is never lost.
- **Expanded rows** (one per lemma): Strong's chip · Greek/Hebrew lemma + translit · two labeled rendering lines — `ABP` and `KJV` — each listing that lemma's rendering words at a glance · occurrence count + arrow. The active lemma's row is highlighted (`--accent-soft` bg + 3px steel-blue inset bar). Clicking a row pivots the whole study view to that lemma while keeping the bar in place.
- Default state: **open**. It's collapsible specifically so it never dominates the reading column.

---

## Interactions & Behavior
- **Search submit** (`onSubmit`): resolve the term. Exact Strong's/translit/Greek match with a single lemma → go straight to that lemma's study view. A gloss or ambiguous term mapping to ≥2 lemmas → set the senses list (sorted by occurrence desc), land on the top lemma, show the pivot bar. Single lemma → no pivot.
- **Study a lemma** (`studyLemma`): set active Strong's, clear book filter + senses, (mobile) close any sheet.
- **Pivot sense** (`pickSense`): switch active lemma but keep the senses bar.
- **Book filter**: clicking a rail row filters occurrences to that book; "All books"/Clear resets.
- **Edition toggle** (ABP/KJV): changes how verses render (ABP = tagged interactive words; KJV = gloss-highlighted plain text).
- **Testament filter** (All/OT/NT): filters occurrences via `TESTAMENT(book)`.
- **Deep links**: `?w=STRONGS` selects that lemma on load. The "Ask AI" links pass `?w=&tr=&gk=` to `Ask the Corpus.html`.
- **Mobile sheets**: open via toolbar; dismiss via close button, scrim tap, or drag-down. Sheet entrance is a transform-only slide-up (no opacity fade) so it renders solid immediately.
- **Mobile fit/scaling** (preview only): `Stage` scales the 412×892 phone to the visible viewport using the smaller of `innerHeight`/`clientHeight`/`visualViewport`, anchored to the top. Not needed in production — the app should fill the device viewport natively.
- **Reduced motion / print**: keep content visible without animation.

## State Management
Per `App`/`WordStudyApp`:
- `query` (string) — search box value.
- `activeStrong` (string) — currently studied Strong's id; `LEMMAS[activeStrong]` is the lemma.
- `edition` ("abp" | "kjv"), `testament` ("all" | "ot" | "nt").
- `bookFilter` (string | null) — restrict occurrences to one book.
- `glossSenses` (string[]) + `glossLabel` (string) — lemmas sharing a searched gloss, and the gloss text; drives the pivot bar.
- Desktop adds `view` ("lemma" | "overview"); mobile adds `sheet` ("search" | "dist" | "card" | "views" | null) and uses `welcome` to show the empty state.
- Derived (memoized): `occ` (filtered occurrence ids), `glossWords` (terms to highlight in KJV), `bookCount`.
- **Data fetching (production):** replace the static `LEMMAS`, `VERSES`, `GLOSS_INDEX` with API calls — lemma lookup (by Strong's/translit/gloss), occurrence list (with testament/book filters), and the gloss→lemmas index. `SensesBar` only needs each candidate lemma's word/translit/strongs/occ + ABP/KJV rendering word lists.

## Design Tokens
Defined as CSS custom properties in `styles.css` `:root`.

**Type**
- Sans (UI): `"DM Sans", system-ui, sans-serif` (`--f-sans`)
- Serif (scripture/body/numerals): `"Source Serif 4", Georgia, serif` (`--f-serif`)
- Greek/Hebrew: `"Source Serif 4", "Gentium Plus", "GFS Didot", serif` (`--f-greek`); Hebrew is RTL.
- Mono (refs / Strong's): `"JetBrains Mono", ui-monospace, monospace` (`--f-mono`)

**Color**
- Backgrounds: `--bg #f6f3ec` (warm off-white), `--bg-sunk #efebe1`, `--paper #fcfaf5` (cards)
- Ink: `--ink #15171c`, `--ink-2 #3b3f48`, `--ink-3 #6a6f7a`, `--ink-4 #9a9ea8`
- Rules: `--rule #e3ddd0`, `--rule-2 #d6cfbe`
- Navy (header/module bar): `--navy #0f1b2d`, `--navy-2 #182842`, `--navy-edge #0a1424`
- **Accent (primary / steel blue):** `--accent oklch(0.46 0.08 240)`, `--accent-soft oklch(0.92 0.025 240)` — used for interactive/links and the studied-lemma highlight.
- **Gold (target/highlighted words only):** `--gold oklch(0.58 0.09 75)`, `--gold-soft oklch(0.93 0.04 75)` — verse refs, highlighted gloss/target words, active mobile nav tab.
- *(AI features use a dedicated `--ai` treatment on the Ask-the-corpus module; in Word study the only AI touchpoint is the steel-blue "Ask AI" link.)*

**Radius:** `--r-sm 6px`, plus card radii ~11–12px used in components.

**Shadows:** `--shadow-sm`, `--shadow-md`, `--shadow-lg` (see `styles.css`).

**Type sizing rules:** verse text 15.5px desktop / 16px mobile; hero Greek 60px desktop / 50px mobile card; section labels 11px uppercase, letter-spacing 0.12em; mono refs/counts ~10.5–13px.

## Assets
- **Fonts**: Google Fonts — DM Sans, Source Serif 4, JetBrains Mono (linked in each HTML `<head>`). Substitute your app's equivalents or self-host.
- **Icons**: inline SVGs defined in the JSX (`I` in `word-study.jsx`, `WMI` in `word-study-mobile.jsx`). No icon font/library — reuse or map to your icon set.
- **No raster images** in this module. The Android device frame (`android-frame.jsx`) is a preview-only chrome; do not ship it.
- **Greek/Hebrew text** must use a font with full polytonic Greek + Hebrew coverage; keep Hebrew RTL.

## Files
- `Word Study.html` — desktop shell (loads styles.css, word-study.css, word-study-data.jsx, word-study.jsx).
- `word-study.jsx` — desktop app: `Header`, `BookRail`, `WordDetail`, `SearchBar`, `SensesBar`, `VerseRow`, `App`.
- `word-study.css` — desktop styles (three-pane grid, rail, card, senses pivot, responsive).
- `Word Study Mobile Preview.html` — mobile shell (loads styles.css, word-study.css, word-study-mobile.css, android-frame.jsx, word-study-data.jsx, word-study-mobile.jsx).
- `word-study-mobile.jsx` — mobile app: `NavBar`, `Sheet`, `CardBody`, `RailBody`, `ViewsBody`, `SearchSheet`, `SensesBarM`, `WordStudyApp`, `Stage`.
- `word-study-mobile.css` — mobile chrome (navy bar, context strip, bottom toolbar, sheets) + overrides of the shared content classes.
- `word-study-data.jsx` — **sample** data: `LEMMAS`, `VERSES`, `GLOSS_INDEX`, `CANON_ORDER`, `TESTAMENT()`. Replace with real APIs.
- `styles.css` — shared design tokens (`:root`) + shared header/search/card primitives.
- `android-frame.jsx` — preview-only Android device bezel (`AndroidDevice`). Not part of the product.

### Implementation notes
- These prototypes use multiple `<script type="text/babel">` files sharing one global scope; shared values are exposed on `window` (e.g. `android-frame.jsx` does `Object.assign(window, {...})`). In a real bundler, convert these to proper modules/imports.
- Class-name collisions were deliberately avoided in the prototype (e.g. gloss-sense rows use `.glsense*`/`.glrow*`, distinct from the word card's `.sense`/`.senses`). Keep equivalents namespaced in your implementation.
- Data shown is original synthesis and **not authoritative** — preserve scholarly disclaimers in the real product.
