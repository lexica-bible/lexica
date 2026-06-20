# Handoff: Testament Book Spine (Library nav)

## Overview
A color-coded "book spine" running down the left edge of the Library book-navigation
rail. Each book group carries a 3px vertical bar — **warm gold for Old Testament**,
**cool blue for New Testament** — so the reader senses which testament they're scrolling
through without reading labels. A spelled-out, color-matched `OLD TESTAMENT` /
`NEW TESTAMENT` header sits above the first category of each testament and teaches the
spine's meaning. Same treatment in all three themes (light / sepia / dark); only the
hue adapts to the palette.

## About the Design Files
The files in this bundle are **design references created in HTML/CSS** — a prototype of
the intended look, not production code to paste in wholesale. The task is to apply this
spine treatment to the Library book-nav in the real `lexica-bible/lexica` codebase
(Flask + `static/src/*.jsx`), using its existing nav markup and the design-token system
already in `static/styles.css`. The actual change here is small and CSS-only plus a few
class names on the nav group elements.

## Fidelity
**High-fidelity.** Exact colors, widths, spacing, and per-theme token values are given
below and are final. Recreate pixel-for-pixel using the existing token variables.

## The Change (CSS-only + class names)

### 1. New design token: `--spine-nt`
The NT spine must read **cool** in every theme. `--accent` could not be reused because
in sepia it is a warm olive-brown (`#4a4636`), which killed the warm/cool contrast. So a
dedicated token was added to each theme's `:root` block:

| Theme | `--gold` (OT spine) | `--spine-nt` (NT spine) |
|-------|---------------------|--------------------------|
| Light (`:root`)              | `oklch(0.58 0.09 75)` | `var(--navy-2)` → `#182842` |
| Sepia (`:root[data-theme="sepia"]`) | `oklch(0.58 0.09 75)` (inherited) | `oklch(0.47 0.10 248)` |
| Dark (`:root[data-theme="dark"]`)   | `oklch(0.78 0.11 75)` | `#9db4d8` |

Add `--spine-nt` immediately after `--accent-soft` in each of the three `:root` blocks.

### 2. Spine rules
```css
/* No gap between same-testament groups so the spine runs continuous. */
.nav-group { margin-bottom: 0; }
/* A touch more air above a new testament block (where the OT/NT tag shows). */
.nav-group--tnew { margin-top: 10px; }
.nav-group--tnew:first-child { margin-top: 0; }

/* Testament spine: warm OT / cool NT, identical treatment across all themes. */
.nav-group--ot { border-left: 3px solid var(--gold);     padding-left: 7px; }
.nav-group--nt { border-left: 3px solid var(--spine-nt); padding-left: 7px; }

/* Spelled-out OT/NT header above the first category of each testament,
   color-matched to its spine. */
.nav-testament {
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; padding: 2px 10px 5px;
}
.nav-group--ot .nav-testament { color: var(--gold); }
.nav-group--nt .nav-testament { color: var(--spine-nt); }
```

### 3. Markup / class names on each book group
Each category group in the nav rail gets:
- `nav-group` (always) + `nav-group--ot` **or** `nav-group--nt` (which testament)
- `nav-group--tnew` on the **first** group of each testament (adds top spacing)
- a `<div class="nav-testament">Old Testament|New Testament</div>` as the first child of
  that first group, before the `.nav-div` category header

```html
<div class="nav-group nav-group--nt nav-group--tnew">
  <div class="nav-testament">New Testament</div>
  <div class="nav-div"><span class="nav-div-n">Gospels</span></div>
  <button class="nav-book"><span class="nav-book-name">Matthew</span><span class="nav-book-count">28</span></button>
  …
</div>
<div class="nav-group nav-group--nt">
  <div class="nav-div"><span class="nav-div-n">Pauline Epistles</span></div>
  …
</div>
```
Map each book category to OT/NT by its canonical testament. In the codebase the nav is
data-driven — set the modifier class from whatever testament field the book list already
carries (e.g. `book.testament === "NT"`).

## Design Tokens (relevant subset)
- `--gold` — OT spine + OT testament label
- `--spine-nt` — **new** — NT spine + NT testament label (cool blue, per-theme above)
- `--navy-2` `#182842` — light-theme NT spine source
- Spine width: **3px**, group `padding-left: 7px`
- `.nav-testament`: 10.5px / 700 / `letter-spacing: 0.08em` / uppercase
- Inter-group gap: **0** within a testament; `10px` top margin on `.nav-group--tnew`

## Rationale / gotchas
- Do **not** swap other sepia `--accent` usages (links, refs, badges) to the cool blue —
  sepia's warm accent is intentional palette identity. The cool token is scoped to the
  spine only, where warm-vs-cool *encodes* OT-vs-NT.
- Earlier iterations used 2px with soft tint variants (`--gold-soft` / `--accent-soft`)
  that washed out on both parchment and navy. Final is full-strength 3px in every theme.

## Files
- `spine-mockup.html` — standalone visual reference; toggles Light / Sepia / Dark to
  show the spine in each. Loads `static/styles.css`.
- `static/styles.css` — the actual rules live here: token block (`--spine-nt`, ~lines
  29–101) and spine rules (`.nav-group--ot/--nt/.nav-testament`, ~lines 2759–2777).
