# Handoff — News feed fixture + the last unverified bar

Status at handoff: three of four surfaces ride the shell's mobile collapse (News `1a35822`,
Ask-corpus `dba2edb`, Notes `7c9dd93`). News's bar is the **only one in the icon matrix never
verified by drawn shape** — its mobile branch never reaches its `<Shell>` without feed data, so
the harness can't render it. Two passes (the icon pass, then Notes) reasoned about News's three
glyphs from the shared components instead of seeing them. **This is the oldest unpaid debt in
the shell arc and runs BEFORE Study's collapse** (JP ruling, `50aee6d`): Study cites News as its
reference pattern, and the reference must not be the one instance nobody has checked.

Session opener follows. Paste it whole.

---

Lexica — News feed fixture + the last unverified bar. One session, one debt.

New session. Cold-start: read TODO.md "## Three-zone shell — remaining consumers" (this is its
first item); docs/claude/frontend.md sections "Shell's MOBILE collapse — News, then Ask-corpus,
then Notes" and "Icons: ONE glyph per function"; the harness header rules in
tests/mobile_harness.js. Recent: 565e133, 63b550e, e9089c9.

WHY THIS IS FIRST (JP ruling 50aee6d): News's bar is the ONLY one in the icon matrix never
verified by drawn shape — its mobile branch never reaches its <Shell> without feed data, so the
harness can't render it. Two passes had to reason about News's three glyphs from the shared
components instead of seeing them. Study will cite News as its reference pattern, and the
reference must not be the one instance nobody has checked.

Item 1 — the fixture. News's mobile branch needs enough feed data to mount. Trace what it
actually calls before shaping anything; as of this writing NewsView reaches for /api/news/meta,
/all, /counts, /shape, /status, /resolve (00-core.jsx ~233-271), and the routes live in
views_news.py (/all:541, /meta:573, /counts:592, /list:645, /shape:695, /status:760,
/resolve:803) — VERIFY that list against the code, don't inherit it from this prompt. news.db is
PA-only, so every shape comes from the producing Python's return, per fixture, named in the
harness header. Anything on disk serves from disk. Note the client sends a `key` param and News
is admin/key-gated — the harness's ?admin=1 seeds that key; check the gate is satisfied rather
than assuming.

Item 2 — the verification the fixture exists for. With News's .zbar rendering at an asserted
375px, run the function→glyph check by DRAWN SHAPE (compare the svg's children, not the
component name you typed) against the settled matrix: Threads=Hash, Watch=Panel,
Options=Filter. Read each sheet before blessing its glyph — a label is not a function (the Views
lesson). If a glyph disagrees with the matrix, post the finding and stop; don't silently re-rule
the matrix.

Item 3 — ride-along, closes an open verification. docs/claude/frontend.md logs `.filters-sep`'s
promotion out of its .ws scope as proven-inert-by-search but NOT measured, because Word study
only draws its divider with a word loaded. If this session's News work gives you a lexicon
fixture (or one is cheap once you're in the harness), measure Word study's rendered divider
byte-identical (1x14, --rule-2) and strike the note in frontend.md + TODO.md. If it isn't cheap,
leave it — it's opportunistic, not scope.

Standing constraints and gates: as written in docs/claude/frontend.md — do not re-list them from
memory. The ones this session will lean on hardest: settle on the DRIVER of the dimension not
the surface you're reading; "stable twice" is not "true", so any baseline is HEAD measured by
the identical method in the same session; ?bundle=head is JS-only and cannot baseline a CSS
change (stash round-trip if you touch CSS); scope every read to its own surface (the desktop
mounts every view — an unscoped querySelector returns another tab's hidden 0x0 copy).

The harness is a TOOL, not a gate — it stays out of the CI list. If you add a Node test, it goes
in BOTH gate lists (CI + scripts/githooks/pre-commit) or it gates nothing.

After any .jsx edit: npm run build, source + static/app.js same commit. Stage, post diff +
per-item evidence, stop — no commit until reviewer receipt. Doc close-out separate with its own
receipt: News's bar joins the matrix as verified-by-shape, and TODO's News-fixture item retires.

Deliverables: the per-fixture provenance (producer named per shape); News's bar rendered and
measured at 375px; the function→glyph table by drawn shape; the .filters-sep close-out or an
explicit "left open, here's why"; gates.
