# Lexica — Design System & Handoff Notes

Companion reference for building Lexica screens in Claude Code. Pair this with any specific
screen mockup. Source of truth for live behaviour/data is the `lexica-bible/lexica` repo;
this captures the **visual system + intent** so a build matches the mockups.

---

## 1. Design tokens

All tokens live in `styles.css :root`. Reproduced here for handoff — **do not invent new
values; pull from these.**

### Color
| Token | Value | Use |
|---|---|---|
| `--bg` | `#f6f3ec` | App background (warm off-white). Every surface sits on this. |
| `--bg-sunk` | `#efebe1` | Recessed areas — left rails, sunk panels. |
| `--paper` | `#fcfaf5` | Card / panel paper. |
| `--ink` | `#15171c` | Primary text. |
| `--ink-2` → `--ink-4` | `#3b3f48` / `#6a6f7a` / `#9a9ea8` | Secondary → faint text. |
| `--rule` / `--rule-2` | `#e3ddd0` / `#d6cfbe` | Hairlines / stronger borders. |
| `--navy` | `#0f1b2d` | Header bar, primary buttons. `--navy-2` hover, `--navy-edge` border. |
| `--accent` | `oklch(0.46 0.08 240)` | **Primary** interactive — links, buttons, badges. `--accent-soft` tints. |
| `--gold` | `oklch(0.58 0.09 75)` | **Highlighted target words ONLY.** Never decorative. `--gold-soft` tint. |
| `--ai` | *(see note F/T2 below)* | AI features (Ask the corpus, Spark affordances). |

### Type
| Token | Stack | Role |
|---|---|---|
| `--f-serif` | Source Serif 4 | Body + **all scripture**. |
| `--f-sans` | DM Sans | UI chrome, labels, controls. |
| `--f-mono` | JetBrains Mono | Verse refs, Strong's numbers, counts. |
| `--f-greek` | Source Serif 4 / Gentium | Greek lemmas. Hebrew is RTL (`script:"hebrew"` flips). |

Base: `15px / 1.5`, `-webkit-font-smoothing: antialiased`.

### Shape & depth
- Radii: `--r-sm 6px`, `--r-md 10px`, `--r-lg 14px`.
- Shadows: `--shadow-sm` (hairline lift), `--shadow-md` (cards/hover), `--shadow-lg` (panels/sheets).

---

## 2. Color usage rules (the part that's easy to get wrong)

1. **Gold is sacred.** Only ever the user's highlighted/target word in a passage. If you're
   reaching for gold for emphasis, use `--accent` or ink weight instead.
2. **Accent = primary action.** Links, search submit, active segmented controls, badges.
3. **AI gets its own visual class.** Ask-the-corpus, the Spark ✦ icon, "Ask AI about…".
   → **Known issue (T2):** `--ai` currently resolves to the same steel-blue as `--accent`, so
   "this is AI" doesn't read as distinct. When building, give `--ai` a separate hue (a cooler
   violet/teal in the same oklch L/C family, e.g. `oklch(0.46 0.08 280)`) and route all AI
   affordances through it. This is the single highest-leverage theme fix.
4. **Navy is structural** — header + primary filled buttons only.

---

## 3. Shared chrome

### Header (`.hdr`)
Sticky navy bar, `max-width 1400px` inner. Left: brand mark (book glyph) + "Lexica" /
"Greek & Hebrew Word Study". Center: nav. Right: pane-toggle icon buttons + avatar.

**Canonical nav order:** Library · Word study · Ask the corpus · Notes · Study · About.

> **Known issue (T3/T4):** the header + its icon set are hand-duplicated in every page's JSX,
> and `library.jsx` has drifted to an *older* 3-item nav (Search/Library/About). Build ONE
> shared `<Header>` (+ shared icon module) and import it everywhere so they can't diverge.

### Right detail panel pattern
Used by Library (word card / cross-ref / note), Word study (word detail), Study (claim card):
- **Desktop:** fixed right sidebar, `460px` (→ `400px` under 1100px). Slides in. Main column
  pads right to make room (`.has-detail`).
- **Mobile:** bottom sheet — scrim + rounded-top panel, `max-height 88vh`, drag handle.

### Breakpoints — **standardize these (currently inconsistent)**
CLAUDE.md states the mobile breakpoint is **1100px**, but pages diverge:
- Library: sheet `<860`, nav drawer `<1024`
- Word study: detail `≤1040`, rail `≤760`
- Ask the corpus: rail `≤980`
- Study: mobile `<1100`

→ Pick the 1100px standard (with one secondary rail breakpoint if a 3-pane page needs it) and
apply it uniformly. Divergence is why panes collapse at different widths page-to-page.

---

## 4. Component patterns

- **Cards** (`.card`): paper bg, `--rule` border, `--r-md`, hover lifts (`translateY(-1px)` +
  `--shadow-md`), active state shows a left ink bar. Grid: `repeat(auto-fill, minmax(260px,1fr))`.
- **Search field** (`.search-field`): 46px, `--bg` fill, focus → white + accent ring. AI variant
  (`.ai-field`) focuses to the AI hue.
- **Segmented control** (`.seg` / `.seg-b`): the standard toggle (editions, English/Greek, OT/NT).
  Active = white chip + `--shadow-sm`.
- **Chips** (`.chip`): pill filters. `.chip.suggest` is mono + accent-soft for AI suggestions.
- **Badges**: `.card-badge` mono accent tag; `.solid` = filled accent. Strong's tags are mono.
- **Verse markup mini-language** (parsed in `parseVerse`): `[ ]` word-order group · `^N`
  ordinal · `*italic*` · `{english|STRONGS|active}` clickable lemma. Keep this exact syntax —
  the reader, word study, and corpus all depend on it.

---

## 5. Per-surface intent (one line each)

- **Library** — interlinear reader; per-word Strong's, OT/NT canon rail (Law/History/Wisdom),
  version toggles, an "About / This chapter" synthesis panel.
- **Word study** — 3 panes: distribution-by-book rail · occurrence rows · word card (LSJ, ABP/KJV
  renders-as senses, derivation, cognates). Deep-links in via `?w=STRONGS`.
- **Ask the corpus** — plain-language Q&A across the canon, "✦ Synthesis" answers with inline
  clickable refs/lemmas + evidence verses. Carries `--ai`. Keep the *"maps reasoning, not truth"*
  / "not authoritative" disclaimers prominent.
- **Study** — Argument Graph workspace; layered DAG, verse clustering, verdict logic per
  tradition. Caption: *"maps reasoning, not truth."* Preserve that restraint.
- **Notes / About** — built in production, not yet mocked. Next up.

---

## 6. Action items pulled from the audit

**Theme**
- **T1** — Study page sits on plain white; restore `--bg` warm tone behind the graph so it
  belongs to the suite.
- **T2** — split `--ai` off from `--accent` (see §2.3).
- **T3** — resync `library.jsx` header to canonical nav.
- **T4** — extract one shared `<Header>` + icon module.

**Function**
- **F1** — terminology: align the lemma tab's name (see §7).
- **F2** — `library.jsx` ignores `?ref=`; `Ask the corpus` / `Study` "Read in context" links
  land on the wrong chapter. Add a `?ref=` (book/chapter/verse) handler that selects + scrolls.

---

## 7. Terminology cleanup — "Lexicon" → current term  ⚠️ DECISION NEEDED

"Lexicon" is the **legacy internal name** for the **Words / Word study** surface. The UI mostly
moved on (mobile tab reads "Words") but the codename is everywhere. Confirm the ONE canonical
user-facing term, then apply below. (Placeholder `<TERM>` = your chosen name.)

**A. User-facing strings — fix now, trivial, no risk**
- `library-mobile.jsx` — "Tap a word for its lexicon entry" → "…its `<TERM>` entry".
- Sweep any About/help/tour copy for "lexicon".

**B. Internal rename — mechanical sweep, mostly safe**
- `static/styles.css` — dozens of `.lexicon-*` classes → `.<term>-*` (rename in CSS + JSX together).
- `80-lexicon.jsx` (file), `LexiconView` (component), `handleNavigateToLexicon`,
  `lexiconPendingStrongs` / `setLexiconPendingStrongs` → renamed consistently.

**C. ⚠️ Back-compat — do NOT blind-rename these**
- **View id `"lexicon"`** is persisted to `localStorage["lexica.view.v1"]` and listed in
  `_VIEWS`. If you change the stored string, migrate old values (map legacy `"lexicon"` → new id
  on read) or users lose their last-tab state.
- **`?lex=` deep-link param** is used by crawlable word pages to open this tab. Keep accepting
  `?lex=` (alias to the new param) so existing/indexed links don't break.

---

*Generated as a handoff companion. Update alongside the mockups as the design evolves.*
