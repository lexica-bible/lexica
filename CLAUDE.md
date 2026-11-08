# Lexica — CLAUDE.md

## What this file is (read this first)
This is the **core rules file** — always loaded, kept lean on purpose. The deep per-area
reference (schemas, gotchas, incident records) lives in `docs/claude/*.md` — NOT optional
background: they encode past incidents and load-bearing detail.
**MANDATORY ROUTING RULE:** before editing an area, read its routed doc below — the whole
relevant section, not a skim; all of them if a task spans areas. Never rely on a summary in this
file where a routed doc has the detail.

| Touching… | Read first |
|---|---|
| Any table, join, schema, data invariant, MetaV/TIPNR, lexica_def, structural cards | `docs/claude/data-model.md` |
| Frontend build, Library tab, reading modes, three-zone shell, Notes/accounts, mobile | `docs/claude/frontend.md` |
| Ask-the-corpus, AI cache, TSK xref, summaries, synthesis prompts | `docs/claude/ai.md` |
| Word study tab, lexicon endpoints, English finder | `docs/claude/word-study.md` |
| Deploy, CI, backups, rebuilds, maintenance scripts, news nightly, SEO pages, rate limits | `docs/claude/ops.md` |
| Visual design detail | `docs/design.md` (doctrine summary below) |

Active work state lives in `TODO.md` + the `HANDOFF_*.md` / `AUDIT_*.md` docs — never here.

## Overview
Lexica is a Flask-based Greek and Hebrew Bible word study app. ABP (Apostolic Bible Polyglot)
interlinear is the primary text; KJV is a fully searchable parallel corpus. The design is
scholarly but accessible — no prior Greek training required.

Stack: Flask (Python) + SQLite · React 18 (UMD) with JSX in `static/src/*.jsx` precompiled by
Babel to `static/app.js` (committed) · deployed on PythonAnywhere ($10 Dev tier) · repo
`lexica-bible/lexica` on GitHub. `bible.db` lives ONLY on PA, never locally, never in git.

## HOW TO TALK TO THE USER — read every session, no exceptions
Plain, concise English — like a colleague, not a textbook. The user is a data-center engineer
(CCNA, Linux, lots of hands-on) — NOT a programmer. Assume infra/CLI/networking fluency (don't
explain basic console steps), but use NO developer jargon. Avoid words like *idempotent,
transaction, schema, query/SELECT, commit, null, boolean, lock/read-lock, upsert, snapshot* —
translate them into plain terms ("running it again just redoes the same work, no harm"; "that
command only reads the database, it never changes it"). Short answers; skip heading-heavy formal
reports unless he asks for depth; skip "want me to walk you through it?" offers — just give the
answer. He has flagged this MORE THAN ONCE — treat it as a hard rule, not a preference. Full
detail + the exact words I've slipped on before: memory `feedback_communication_style`.

## THE BAR — 100% accuracy + completeness — read every session, no exceptions
This is a project of accuracy and specifics. A wrong gloss/lemma/number misinforms a reader who
trusts it and can't check the Greek/Hebrew himself. The bar is NOT negotiable:
- **100% accuracy AND completeness.** Coverage (every word has *a* value) is NOT quality (the
  value is *right*) — prove BOTH before calling anything done. "Good enough", "basically done",
  "mostly covered" are rejected. Measure the gap completely (every row, no sampling), drive it
  to zero, re-verify.
- **Do NOT ship half-baked work to "get the job done."** If I catch myself writing a hedge —
  "it can read a bit X", "KJV-flavored", "good enough for now", "we can refine later" — STOP.
  That hedge means it isn't validated. Validate the SOURCE'S QUALITY on real samples BEFORE
  building on it; never ship a source I've already doubted and plan to "check after." The check
  comes before the commit, not after he pushes back. (Earned by the word-card gloss shipped on
  `kjv_def` after I'd flagged it risky.)
- **Never suggest an AI prompt change that REGRESSES the model** (parrots framing, over-asserts,
  adds jargon, blacklists instead of reframing). See memory `project_ai_synthesis_quality`.
- **Don't create work that we'll have to come back and fix.** Anything less than
  correct-and-complete is not a shortcut, it's a future bug.
- **If I'm about to propose or ship something less than this:** stop, run `/wrap`, and write a
  clean hand-off prompt for a fresh session instead of limping forward. Full record: memory
  `feedback_accuracy_completeness_bar`.

## VERIFY BEFORE YOU CLAIM — read every session, no exceptions
Every factual claim about the code/data/sources gets CHECKED against the actual source BEFORE I
say it — read the file+line, run the read-only check, look at the real rows. Inferring from one
or two lines and stating it as fact is banned. (I twice said the ABP word card "shows a
dictionary gloss" without tracing the display logic; it shows the in-verse English word.)
**No clean-sweep claims:** never call something a "clean sweep / sure win / validated / stark
improvement" from a flattering sample — check EVERY item or label it a spot-check with the rest
unverified, and probe STRESS cases (loaded/edge), not easy ones. (TBESG "validated" off
love/spirit/God broke on χάρις→"grace". Reporting a source's value ≠ vouching it's right.)
**Self-trigger:** if I make a claim I didn't verify, OR I catch myself having guessed, I STOP,
run `/wrap` immediately, and write clean handoff notes for a fresh session — I do NOT keep
going. Full record: memory `feedback_verify_before_claiming`.

## Design doctrine
Lexica's visual language is quiet. Text, hierarchy, whitespace, and hairline structure do the
work. **Library is the canonical surface** — when any rule is ambiguous, the tiebreaker is "what
does the Library reader do?" New surfaces should look built by whoever built Library.
(Full record: `docs/design.md`.)

1. **No decorative containers.** Panels are containers; content is rows. No borders,
   backgrounds, or radii on repeating elements. Rows separate by whitespace or hairline
   divider; hover wash + accent left-bar for interaction/selection. Shared system: `.listrow`
   + tokens (`--row-accent` etc.). Reference the system, never local copies.
2. **References are text.** Strong's numbers, verse refs, translation tags: bare mono or small
   caps, muted, no chrome. Shared class: `.refmark`.
3. **Backgrounds and highlights are semantic, never stylistic.** A background means something
   is *marked*. If a highlight isn't carrying meaning a reader needs, it doesn't exist.
4. **One pill: CONTESTED.** It's rare, it's a warning, it's allowed to interrupt. Nothing else
   gets a pill without the same justification.
5. **Emphasis budget.** Before adding visual weight, name the meaning it carries. Default to
   the quietest version that works; ornament must argue its way in. **Quiet is not formless** —
   a list of choices must still read as discrete items at rest.
6. **One radius, plus one SHEET radius.** All rounded rectangles use the shared `--radius`
   token (6px, soft-square; never 0-sharp, never lozenge). **Mobile bottom sheets are the one
   sanctioned exception: `--sheet-radius` (18px), owned by the shared `Sheet` shell** — a sheet
   corner reads at a different scale than a chip's (at ~30px tall a chip would go lozenge). JP-ruled
   2026-07-15; history: frontend.md → "The mobile sheet contract". Also `50%` circles, `0`.
7. **Toggles — never box + underline together.** Text segments → underline-under-active, no box
   (`.seg--line`). Icon toggles → boxed active.

Bounded exceptions: input surfaces, semantic notices/callouts, selected states (as accent/wash,
never a border box). **Word study is the reference surface for workspace visuals, as Library is
for the reader** (`docs/claude/frontend.md` → "Word study is the visual reference surface").

## Key design decisions (project-wide, not per-feature)
- ABP is the primary text — all word study anchored in ABP interlinear. KJV is a full parallel
  corpus. Never add KJV as the sole primary study text.
- No systematic theology imported — text speaks first (Berean approach).
- **PLAIN MEANING, NOT TRADITION (hard rule):** glosses/word-meanings = the plain, attested
  sense, NEVER the theologically-loaded or equivocated English (χάρις = "favor/kindness", NOT
  "grace"; πνεῦμα = "spirit/breath", NOT "Ghost"). Give the RANGE when a word has one; a single
  church-word gloss is a red flag. Applies to the word card, AI synthesis, lexicon, studies.
  Memory `feedback_plain_meaning_not_tradition`.
- Italic words (KJV `italic=1`, ABP `words.italic=1`, ABP `[word]`) are translator additions.
- Function words filtered from search: Greek `core._FUNCTION_STRONGS` (LSJ-derived at startup +
  app.py's override list); Hebrew `views_lexicon._HEB_FUNCTION_STRONGS`.
- Do NOT add conjugated manuscript forms to the reader — the audience are non-Greek readers.
- **Gray-vs-hide is the user's per-control call:** gray a real feature that doesn't apply here;
  hide copyright-gated or truly irrelevant controls. Propose gray for inactive-but-applicable,
  confirm per control. Memory `feedback_gray_dont_hide`.

## Working with this codebase
(Max 5x plan: bias to THOROUGH and CORRECT over conserving tool calls; the focus notes below
are about context quality, not rationing.)
- **Show code before changing it — ALWAYS, every mode, no exceptions.**
- Go straight to the relevant module/function. Read as much as correctness needs — never starve
  a task of context — but don't scan the whole codebase out of habit.
- Make minimal changes; do not refactor unrelated code. Ask before large changes.
- **Grep before you size a fix.** Before calling a change "small," count every copy of the thing
  you're editing — a definition or pattern often lives in several places. (A fix scoped off one
  copy missed a 6-copy set of paren-float handling.)
- **Effort by task type:** routine known edits → medium. Diagnosis / root-cause /
  data-integrity work (anything touching the words table or Strong's invariants) → HIGH effort,
  read every spot the trace needs (the strongs_base regression: one wrong word hid a 592k-row
  break). Unsure which mode → ask, or state the assumption.
- **Two independent derivations = the diff is your oracle.** When one fact is produced two ways
  (word rows vs clean `verses.text`, two parsers of one source, a build vs its feed), their
  disagreement is the truth-finder — trust neither side alone. Resolve each mismatch against the
  pinned/authoritative source, never by picking the reading you prefer.
- **WORD-ORDER / Strong's-order / proper-noun-slot swaps:** confirm the layout against the
  SOURCE (eSword/ABP) ONLY — never guess "what eSword probably shows." If the source isn't in
  front of you, ask the user to check. Read-only dry-run is the source of truth before any
  `--apply`. (2026-06-07 Act 19:4 lesson.)
- **CC/DB boundary:** Claude cannot query bible.db (or news.db) directly, ever. All DB steps
  run by the user on PA; Claude proposes the exact command, the user confirms before any write.
  Checkpoint approval before any correction-table write, schema change, or binding-logic change.
  **But `abp_texts/` IS in the repo — read it, don't ask JP to paste ABP text.** DIAGNOSIS-grade
  only: the PRE-BUILD source (brackets unreordered, Strong's inline), NOT the bytes any gate
  compares. **Anything byte-exact — a quote fix, an `--old` string — comes from a PA dump of the
  built `verses.text`, never from `abp_texts/`.**
- **Edition-upgrade lane:** every read-only block and every re-run of a DESIGN-ruled gate goes to the reviewer subagent first; CC prints a block only under its CLEAR line; ESCALATE text goes to the ruling chat; writes go to the ruling chat directly (DESIGN 9.90).
- After ANY edit to `static/src/*.jsx`: `npm run build`, commit BOTH source and rebuilt
  `app.js`. Full build-system detail + line-ending traps: `docs/claude/frontend.md`.

## Hard safety rules — Do Not
- Do not touch existing ABP tables when adding unrelated features.
- Never commit any live db to git; never query or test against a local db — all db work is on PA.
- **NEVER run `DELETE FROM words` or `DELETE FROM verses`.** OT and NT share the words table;
  clearing destroys hard-to-recover data. Re-imports use INSERT OR IGNORE.
- A words rebuild (`build_words_from_abp.py`) only when truly necessary, and only by the
  **`/rebuild-words`** procedure (`.claude/commands/rebuild-words.md`) — rare, high-stakes, never
  improvised. Rebuild scripts NEVER write the live db — they build into `bible.db.new`, swapped by
  hand with one reversible move (a parallel session once blanked bible.db; memory
  `project_db_backups`). After ANY run: `import_tipnr.py` + the strongs_base check (below).
- **A hand edit to live must go into the frozen file the rebuild re-applies, in the same change,
  or the next rebuild undoes it** (`docs/claude/data-model.md` → "Hand repairs on live").
- **NEVER use WAL journal mode for any db on PA.** PA's home dir is NFS; WAL corrupts on a
  crash (news.db, 2026-07-05 — page-1 lost mid fold-back). Use `journal_mode=DELETE` +
  `busy_timeout` on every read-write opener. Applies to every db.
- `study.db` is the one irreplaceable file; nightly verified backups → `docs/claude/ops.md`.

## Critical data invariants (summary — full detail in docs/claude/data-model.md)
- **`words.strongs_base` is fully G/H prefixed** ('G4151', 'H7307'). The lexicon join is
  `l.strongs_g = w.strongs_base`; a bare base → NULL lemma (a WRONG lemma under the old SUBSTR
  join). After any words rebuild `SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'`
  must be 0. `words.strongs` is intentionally bare. Locked by tests/test_strongs_join.py +
  test_build_invariants.py.
- **AUDIT RULE — dotted-number blindness (hard, standing).** Any Strong's-number audit operates
  on the FULL dotted number (`strongs`, e.g. `G1246.2`) by default; grouping on `strongs_base`
  only with an explicit reason. Any "count = 0" or "orphan/contaminated" finding MUST check
  dotted variants before it counts as a finding. Dotted numbers carry real content (G303.1
  ἀνὰ μέσον, διὰ κενῆς). Cost two false positives.
- **`verses.text` is the clean, correctly-ordered English prose.** NEVER rebuild a verse from
  `words` joined by `position` — that's raw Greek order and scrambles ABP's bracket-reordered
  English. Narrow exception: a "LORD the"-style determiner flip is a `_split_compounds` BUILD
  bug, not the expected scramble (`scripts/audit_split_flip.py`).
- **A missing verse row silently drops its words** at build time (the Hebrews-13 lesson).
- Every detector must fire on a known positive before trusting a zero (certification rule).

## Deployment quick reference (full detail + CI/pre-commit: docs/claude/ops.md)
- `bash ~/bible-db/scripts/deploy.sh` — pull → invariant tests → loaders/pip only if changed →
  API reload (all workers together) + 5× sweep, only if tests pass. NEVER bare `touch` for
  serving code — stale-worker mix (G2 rule).
- **Env vars/secrets live in the WSGI file, NOT a `.env`** — `os.environ[...]` lines ABOVE the
  app import in `/var/www/www_lexica_bible_wsgi.py`. Scheduled tasks can't see it; their keys
  live in a gitignored `~/bible-db/.env`.

## Project structure
PA path `/home/appssanding720/bible-db/`: `bible.db` (PA-only) · `app.py` → core.py + ai.py +
views_*.py · `templates/index.html` · `static/src/*.jsx` (SOURCE, 00-core … 90-app) →
`static/app.js` (COMPILED, committed) · `static/styles.css` · `scripts/` (build-frontend.js +
import/migration/audit) · `docs/claude/` (the routed docs).
`design/` is NOT the app — throwaway design-tool mockups only. The live frontend is ONLY
`static/src/*.jsx` → `static/app.js`. Never audit/edit `design/*.jsx` as production.
