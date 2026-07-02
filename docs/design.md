# Lexica design doctrine

## Principle

Lexica's visual language is quiet. The app is a reading instrument: text,
hierarchy, whitespace, and hairline structure carry all organization. Visual
weight is a scarce resource spent only on meaning.

This wasn't imposed — it was recovered. The Library reader, the most
hand-curated surface in the app, established the language first: bare muted
mono for verse numbers and references, small-caps section headers, italics for
editorial voice, hairlines and whitespace for structure, zero chrome on
repeating elements. Other surfaces drifted away from it by copying each
other's card patterns; the 2026-07 de-box pass brought them home.

## Canonical surface

**Library is the reference implementation.** When a rule below is ambiguous,
the tiebreaker is: what does the Library reader do? New surfaces should look
like they were built by whoever built Library.

## Rules

### 1. No decorative containers
The panel is the container; rows are content. Repeating elements — list rows,
feed items, section wrappers — get no borders, no card backgrounds, no
border-radius. Rows separate by whitespace or hairline divider. Interaction is
a subtle hover wash; selection is an accent left-bar + wash, never a box.

Implementation: the shared `.listrow` base class + `:root` tokens. A surface
recolors via `--row-accent` on its container. Surfaces reference the system;
no local copies. (Local copies are how the card pattern drifted across six
surfaces in the first place.)

### 2. References are text
Strong's numbers, verse references, and translation tags render as bare text:
mono or small caps, muted color, no background, no border. The typeface and
color make them read as references; fixed-width alignment makes them read as
columns. Clickable references get hover underline, nothing more.

Implementation: the shared `.refmark` class (mono, no fill/border/padding);
color + size come from context, prose-clickable tokens add `.refmark--link`.

### 3. Backgrounds and highlights are semantic
A background color is a mark, not a style. Legitimate marks: a matched word in
an evidence snippet, a selected item, a warning state. If a highlight isn't
carrying meaning a reader needs at that moment, it doesn't exist. The evidence
highlight in Key Passage snippets is the model: one color, one job.

### 4. One pill: CONTESTED
The CONTESTED badge is the only pill in the app. It's rare, it's a warning
from the fairness gate, and it's supposed to interrupt reading. That's the
bar: nothing else gets a pill without the same justification. (Fitting that
the fairness gate is the one thing allowed to shout.)

### 5. Emphasis budget
Every screen gets a small number of loud elements. Before adding visual weight
to anything, name the meaning it carries. "Grouping" → use a small-caps header
and a hairline. "Looks clickable" → use hover. The default is the quietest
version that works; ornament must argue its way in.

## Deliberate exceptions

- **Input surfaces** — composers, note editors, search fields. Inputs are
  supposed to read as bounded.
- **Semantic notices** — the contested-reading callout, grounding cautions,
  the under-construction banner. Callouts, not list rows.
- **Selected states** — accent/wash treatment everywhere; never a border box.

## Known debt (tracked, intentional)

- Mobile Ask-corpus keeps the inline Key Passages block until a mobile
  inspect pattern exists; delete it when one lands.
- `.study-verse-row` (admin topic editor) still boxed; sweep later.
- Standalone `.cpanel` (computed distribution panel, streams above the
  synthesis) kept boxed on purpose — it sits alone in the prose answer flow,
  not a list pane, so its bounds separate computed fact from generated prose.

## History

- 2026-07-02: de-box pass (commit 35128f9) — card pattern removed from News,
  Study, Notes, Ask-corpus; `.listrow` system installed. Follow-up passes:
  section-level containers (24389e2), Word Study search states +
  reference-tag de-chip / `.refmark` (cdbff76).
