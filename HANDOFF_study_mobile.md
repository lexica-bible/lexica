# Handoff — Study on the shell's mobile collapse (the fourth and last consumer)

Status at handoff: three surfaces ride the collapse (News `1a35822`, Ask-corpus `dba2edb`,
Notes `7c9dd93`). Study is the last tab on the OLD single-column mobile branch
(`.study-view .study-mobile`, `static/src/55-study.jsx`).

**TWO GATES BEFORE ANY BUILDING — both can stop this session dead:**
1. **News's bar must be verified-by-shape first** (`HANDOFF_news_fixture.md`). Study cites News
   as its reference pattern; a reference must be verified before it is cited.
2. **Study is admin-gated and DOWN FROM PUBLIC** (JP ruling 2026-07-10, standing): its priority
   follows Study's return from conceptual-stage hold. It is **tracked, not ordered**. JP's
   explicit go is required regardless of where this sits in any queue.

Session opener follows. Paste it whole.

---

Lexica — Study on the shell's mobile collapse. The last parked tab.

New session. Cold-start: docs/claude/frontend.md "Shell's MOBILE collapse — News, then
Ask-corpus, then Notes" (three consumers, their proofs, and every gotcha they paid for);
"Icons: ONE glyph per function" incl. the settled matrix and its two precedents (the
mode-following slot, the cross-tab reuse rule); "WORD STUDY IS THE VISUAL REFERENCE SURFACE";
the Notes + Ask-corpus arcs in TODO_ARCHIVE.md.

PREREQUISITE — HARD GATE: if News's bar is not yet verified-by-shape, STOP and run
HANDOFF_news_fixture.md first. Study cites News as its reference pattern, and the reference must
be verified before it is cited. This is not a preference and not a "should" — do not proceed
past it under momentum.

Scope: Study is the fourth and last consumer. Mobile Topics/Graphs/Seams still run the OLD
single-column branch (.study-view .study-mobile) in static/src/55-study.jsx.

⚠ TWO THINGS MAKE THIS UNLIKE THE OTHER THREE — read before planning:

1. Study is ADMIN-GATED AND DOWN FROM PUBLIC (JP ruling 2026-07-10, standing). Its priority
   follows Study's return from conceptual-stage hold; it is tracked, not ordered. CONFIRM WITH
   JP THAT IT IS ORDERED before building. If it isn't, stop here.
2. Study is the argument-graph tab (one shared claim pool, many per-position overlays). Its
   zones may NOT map like the reading tabs' do. The other three collapsed a list + a detail
   panel; a graph's rail/center/inspect may not be the same kind of furniture. ALSO: the right
   inspect is ZoneEmpty everywhere today (per-item detail was deferred by design) — so you may
   be collapsing a zone that has no content yet, which is a real question, not a detail. If the
   zone→sheet mapping is genuinely ambiguous, PROPOSE AND STOP for a ruling. Forcing Study into
   the reading tabs' shape because three tabs did it that way is exactly the "inherit a button
   count" failure the pattern exists to prevent.

Method, same as the Notes handoff that worked: LOOK FIRST. Mount Study in
tests/mobile_harness.js at an asserted 375px (device emulation; Chrome floors at 500px; seed the
tour-seen flag), inventory what the desktop layout carries — every rail, panel and affordance,
measured not assumed — and map zones to sheets the way the first three did. News earned three
buttons, Ask-corpus two, Notes two. Study earns whatever it has. Zones get bar slots; one-shot
actions and mode switches don't. Propose the button set with reasoning before building.

Icons: function-first. For each button name the function, check the settled matrix, use the
canonical glyph, verify by DRAWN SHAPE not component name. Study's list button is content-named
per the last-row ruling — propose its content name. If a function has no canonical glyph,
propose one, and read the sheet before naming it (a label is not a function). Note the two
precedents already in the matrix in case they apply.

Landing/empty state: measure against Word study's landing rhythm (the reference) and converge, or
log the divergence in the CSS with its reason. Note Study's inspect is ZoneEmpty by design — an
empty state that can never fill is a permanent gray, not an "empty yet" (Notes's Journal mode is
the precedent).

Fixtures: Study reads study.db (PA-only) — shape from the producing Python, named per fixture in
the harness header. If a surface has no server producer, frontend.md has the adapted form.
Anything on disk serves from disk.

Standing constraints and gates: as written in docs/claude/frontend.md — don't re-list them from
memory. Load-bearing here: layout only, desktop untouched and PROVEN so per surface; Word study
byte-identical is the hard gate; the CSS baseline is the stash round-trip (?bundle=head swaps
only app.js); "stable twice" is not "true" — baseline = HEAD by the identical method, same
session; settle on the driver of the dimension; a fix scoped to a desktop container does not
reach the phone; gray-never-hide proven by rects; occlusion proven by hit test; swipe fallback
proven on a FORCED overflow with the destructive case last; screenshots alongside numbers.

After any .jsx edit: npm run build, source + static/app.js same commit. Stage, post diff +
per-item evidence, stop — no commit until receipt. Doc close-out separate with its own receipt:
Study joins frontend.md as the fourth consumer with whatever it proves; the "Study is the last
one parked" line retires from TODO + memory.

Deliverables: the zone inventory and proposed button set with reasoning (or the propose-and-
stop); before/after at asserted 375px; function→glyph by drawn shape; landing divergence table;
per-surface desktop guardrails vs a HEAD baseline by identical method; gates.
