# Lexica — CLAUDE.md

## Overview
Lexica is a Flask-based Greek and Hebrew Bible word study app. ABP (Apostolic Bible Polyglot) interlinear is the primary text; KJV is a fully searchable parallel corpus. The design is scholarly but accessible — no prior Greek training required.

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

## Instructions for Claude Code
(Account: user is on the Max 20x plan — ample headroom. Bias to being THOROUGH and
CORRECT over conserving tool calls. The notes below are about staying focused and
keeping context sharp, NOT about rationing usage.)
- Target the specific function/section relevant to the task — for focus, not frugality
- app.py and the frontend are now split into modules (app.py → core.py + ai.py +
  views_*.py; the old app.jsx → static/src/*.jsx). Read the relevant module/region, not
  everything — for focus, but read as many as correctness needs
- Read as much as you need to get it right — do not starve a task of context to save calls
- Do not attempt to access bible.db directly
- Make minimal changes — do not refactor unrelated code
- Ask for clarification before making large changes
- Go straight to the relevant function; don't scan the whole codebase out of habit

## Effort mode (Opus 4.8) — on the Max 20x plan, headroom is ample
Pick effort by task TYPE. When in doubt, lean higher — the plan affords it.
- **Routine work** (known edits, data scripts, config tweaks, one-line fixes):
  medium effort is plenty; stay efficient but don't cut corners on correctness.
- **Diagnosis / root-cause / data-integrity work** (a symptom several hops from
  its cause, anything touching the words table or Strong's invariants): HIGH
  effort — read as many spots as the trace needs and reason it through. A wrong
  guess on data is expensive (see the 2026-06-03 strongs_base regression — one
  wrong word hid a 592k-row break).
- When unsure which mode you're in, ask the user, or state your assumption.

## Working style (not hard caps — 20x plan, optimize for correctness)
- Show code before changing it (ALWAYS — every mode, no exceptions)
- WORD-ORDER / Strong's-order / proper-noun-slot swaps: confirm the layout against
  the SOURCE (eSword/ABP) ONLY — NEVER guess "what eSword probably shows." If the
  source isn't in front of you, ask the user to check. Read-only dry-run is the
  source of truth before any --apply. (2026-06-07 Act 19:4 lesson.)
- Prefer focused reads over broad scans — for context quality, not call-rationing
- No artificial tool-call or file-count ceiling; use what the task genuinely needs.
  For diagnosis, that may be many reads — that's expected and fine.
- Still avoid genuinely wasteful moves (re-reading a file you just edited, scanning
  the whole repo when you know the target)

## Important
- bible.db lives on PythonAnywhere only, not locally
- Never query or test against a local database
- All db changes must be made on PythonAnywhere

## Deployment
- Preferred deploy: `bash ~/bible-db/scripts/deploy.sh` — pulls, runs the invariant tests, loads any
  non-canonical books WHOSE FILES THE PULL CHANGED (diffs old..new HEAD, runs only the touched
  loaders — a plain code deploy loads nothing), `pip install`s into the bible-env venv WHEN the pull
  changed `requirements.txt` (2026-06-22; a failed install stops the deploy, bare-`pip` fallback if the
  venv path is missing), and reloads the site ONLY if the tests pass. A loader hiccup warns but never
  blocks the reload, so adding a book just needs a normal deploy.
- Manual fallback: `cd ~/bible-db && git pull && touch /var/www/www_lexica_bible_wsgi.py`
- PA git is set `pull.rebase false`, `merge.autoedit no` (no prompts). The database is NOT in git
  (too large) — managed directly on PA.
- After a `requirements.txt` change: `deploy.sh` now runs the `pip install` itself (see above), so a
  normal deploy covers it. Installing BY HAND (manual deploy): on PA, `workon bible-env` THEN
  `pip install -r requirements.txt` — NO `--user` inside the venv (it's
  `/home/appssanding720/.virtualenvs/bible-env`, Python 3.11; a `--user` install lands in the system
  3.13 dir and is ignored). Then reload.
- **Env vars / secrets live in the WSGI, NOT a `.env`.** `/var/www/www_lexica_bible_wsgi.py` sets them
  with `os.environ['KEY'] = '...'`, and those lines MUST sit ABOVE the app import (module-level reads
  like `GOOGLE_CLIENT_ID = os.environ.get(...)` run at import). `core.load_dotenv()` doesn't reliably
  find a `.env` under the PA web app — don't rely on one. Edit the WSGI, then reload (touch it). Keys
  set there: `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID`, `ESV_API_TOKEN`, `OWNER_EMAIL`, the mail keys
  `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS` + `MAIL_FROM` + `SITE_URL` (+ optional `FCBH_API_KEY`,
  `MAIL_REPLY_TO`). Outbound mail goes through **Resend** (relay `smtp.resend.com:587`, user `resend`,
  pass = a Resend API key, From `noreply@lexica.bible`). The nightly `health_check.py` task can't see the
  WSGI env, so ITS copy of the mail keys + `OWNER_EMAIL` lives in a gitignored `~/bible-db/.env` (the
  script `load_dotenv`s it). Full record + gotchas: memory `project_email_smtp`.
- **Accounts / roles / gated texts** (full records: memories `project_user_roles`, `project_esv_audio`,
  `project_visitor_stats`; setup history in TODO_ARCHIVE):
  - Roles nologin / user / berean / admin — a `role` column in `notes.db users`; gates in `views_notes`
    (`is_admin()`, `is_berean()` = berean-or-admin, `is_logged_in()`). `OWNER_EMAIL` is ALWAYS admin
    (bootstrap, even before the column migrates). user (any sign-in) = AI search (login-gated, costs
    money); berean = ESV + NIV; admin = visitor Stats + the in-app Admin page (sets others' roles).
  - Sign-in is email or Google; Google needs `GOOGLE_CLIENT_ID` + the `google-auth` package and the
    button just hides if either is missing (a code-only deploy never breaks). `notes.db` is gitignored,
    PA-only.
  - ESV + NIV (berean-gated) each have their own `esv.db` / `niv.db` (gitignored, PA-only;
    `scripts/load_esv.py` / `load_niv.py`; `views_esv.py` / `views_niv.py`).
- **Audio sources:** ESV = Crossway's own API (api.esv.org, `ESV_API_TOKEN` in the WSGI — whole-Bible
  Max McLean; `views_esv._crossway_audio_url` follows the 302 to the signed mp3), with FCBH
  (`FCBH_API_KEY`, NT-only) as fallback. KJV = public-domain audiotreasure.com, no key (voice set
  `KJV_AT`; Job/Song/Philemon/2–3 John/Jude fall back to the music set `KJV_FF`). BSB = public-domain,
  no setup. NIV = no audio source (dead end).

## CI / automation (added 2026-06-07)
- **GitHub Actions** (`.github/workflows/ci.yml`) — runs on every push/PR: (1) the invariant tests
  (the `tests/test_*.py` set — strongs-join, build-invariants, folded-fixes, argmap; they build their own in-memory data, no
  bible.db needed), (2) rebuilds `app.js` and FAILS if the committed copy is stale. Repo is public; check
  the Actions tab or query `api.github.com/repos/lexica-bible/lexica/actions/runs`. `gh` CLI is installed on the dev box now (2026-06-22; Claude calls it by full path) — NOT on PA. See memory `project_dependabot_workflow`.
  - **LINE-ENDINGS for the app.js check (cost a CI fail 2026-06-14; the "all CRLF" claim CORRECTED
    same day):** Keep `git config core.autocrlf false` — with `autocrlf=true` (Git-for-Windows default)
    your local `git diff` HIDES CR mismatches, so a wrong `app.js` slips past the hook and CI rejects it
    as stale. The `static/src/*.jsx` files are MIXED, NOT all CRLF: some LF (60-library.jsx, 90-app.jsx,
    30-detail-panel), some CRLF (59a/59b, 10-icons, 59-dayintro). Babel keeps a `/* */` block comment's
    CRLF in `app.js`, so app.js carries 4 CRLF from the CRLF sources — the build reproduces them, so CI
    matches as long as you commit src + app.js together. RULE: match a file's EXISTING endings; do NOT
    flip a whole file (noisy diff + changes app.js's CRLF set). Check real endings with `xxd`/a byte
    count, NOT Git-for-Windows `grep -c $'\r'` or piped `git show` (both falsely reported the LF
    60-library.jsx as CRLF this session). Verify like CI before pushing:
    `git checkout HEAD -- static/src/ && npm run build && git diff --quiet -- static/app.js`.
- **Pre-commit hook** (`scripts/githooks/pre-commit`, wired via `git config core.hooksPath scripts/githooks`)
  — local twin of CI: rebuilds+stages app.js if a `static/src/*.jsx` is staged, then runs the tests and
  blocks the commit on failure. LOCAL DEV MACHINE ONLY — on PA it was unset (`git config --unset
  core.hooksPath`) because PA has no Node. Bypass once with `git commit --no-verify`.
- **Dependabot** (`.github/dependabot.yml`) — weekly; opens PRs for pip/npm/actions updates, now
  GROUPED (one PR per ecosystem: pip minor/patch batched + majors solo, all `@babel/*` together,
  actions batched — 2026-06-22). Not auto-merged. **Claude can't merge/close PRs — the safety
  classifier blocks it even with your OK, so it hands you the `gh pr merge/close` commands to run.**
  A normal `deploy.sh` does the `pip install` after a merge. Full record: memory
  `project_dependabot_workflow`.
- Nightly `health_check.py --email --only-warn` email — LIVE on PA 2026-06-16 (daily PA scheduled task,
  23:53 UTC). `--only-warn` = mails ONLY when a check fails (silent on clean nights). The task's mail keys
  + `OWNER_EMAIL` are in `~/bible-db/.env` (a cron can't read the WSGI env). Memory `project_email_smtp`.

## Frontend build step (added 2026-06-06)
- The SOURCE is `static/src/*.jsx` — per-view files, concatenated (filename order;
  numeric prefixes set it) into ONE compilation unit. `static/app.js` is the COMPILED
  output the browser loads (index.html points at `app.js`). The compiled `app.js` IS
  committed to git; `node_modules/` is git-ignored. (Phase 4, 2026-06-06: the old
  3,461-line `static/app.jsx` monolith was split into `static/src/` — see the file
  headers there for what each holds. Same split spirit as the app.py blueprints.)
- After ANY edit to a `static/src/*.jsx` file you MUST rebuild before committing:
  `npm run build` (runs `scripts/build-frontend.js`: concat src -> Babel -> static/app.js).
  One-time setup: `npm install`. Commit BOTH the .jsx source AND the rebuilt app.js.
- The build runs LOCALLY (Node is on the dev machine, not needed on PA). PA deploy is
  unchanged — it just `git pull`s the already-compiled app.js.
- Why concat-then-compile (not `babel <dir>`): one unit emits Babel's spread helper
  once and reproduces the old single-file output exactly (the src files joined by "\n"
  reconstruct the original app.jsx).
- Why the build step at all: in-browser Babel was recompiling all the JSX on every page
  load (~2.5s render delay; server TTFB was only 96ms). Precompiling + production React
  builds removes that tax. Babel-standalone and dev React were dropped from index.html.
- **`design/` is NOT the app — it's throwaway design-tool mockups (standalone mini React apps).**
  The live frontend is ONLY `static/src/*.jsx` → `static/app.js`. Never audit/edit `design/*.jsx`
  as production; use it only as the visual target. (The design tool kept mistaking its own
  `design/library.jsx` mockup for the real app — see the callout in `design/README.md`.)

## Stack
- Backend: Flask (Python), SQLite
- Frontend: React 18 (production UMD), JSX in static/src/*.jsx precompiled via Babel to
  static/app.js (build step — see "Frontend build step" above), HTML/CSS
- Deployed: PythonAnywhere ($10 Dev tier)
- Version control: GitHub (repo: lexica-bible/lexica)

## Project Structure

/home/appssanding720/
bible-db/
bible.db          # main SQLite database
app.py            # Flask app, all routes
templates/
index.html      # single page app
static/
src/             # frontend SOURCE — per-view *.jsx (00-core … 90-app)
app.js           # COMPILED bundle the browser loads (built from src/, committed)
styles.css       # all styles
scripts/          # build-frontend.js + one-time import/migration scripts

## SEO / crawlable pages + site icons
The SPA is invisible to search engines, so `views_seo.py` serves plain server-rendered HTML
(templates `templates/seo/`) the crawler can read, all reusing the JSON endpoints' read-only SQL:
- `/read/` (book index) · `/read/<slug>` (book) · `/read/<slug>/<ch>` (ABP) · `/read/<slug>/<ch>/<text>`
  (kjv|bsb|heb) — interlinear chips with ABP brackets/numbers; `/word/<strongs>` (G/H word study);
  `/sitemap.xml` generated (chapters + every Strong's used). **PUBLIC-DOMAIN TEXTS ONLY — never ESV/NIV.**
- The app deep-links INTO these: `/?b=&c=&t=` jumps to a chapter, `/?lex=G####` opens the Lexicon —
  read once on mount in `static/src/90-app.jsx`, then the query is stripped.
- `app.py` serves the root files crawlers fetch (`/favicon.ico`, `/apple-touch-icon.png`, `/robots.txt`);
  `/sitemap.xml` is the seo blueprint's. Icons + `og.png` share card live in `static/`, regenerated by
  `scripts/gen-icons.js` (transient `sharp` dep). seo.* endpoints are rate-limit-exempt.
- Full record: memories `project_seo_pages` + `project_seo_branding`. Google Search Console is set up
  (Domain property, sitemap submitted).

## Database Tables
- `verses` — ABP verse text. `verses.text` is the clean, correctly-ordered English PROSE (what
  the reader's prose mode + SEO pages use). NEVER rebuild a single verse from `words` joined by
  `position` — that's raw Greek order and SCRAMBLES ABP's bracket-reordered English. (2026-06-21
  TSK-panel garble: `/api/verse` and `views_crossref._abp_text` were stitching words by position;
  both now read `verses.text`.)
- `words` — ABP word-level interlinear, Strong's tagged. Columns: english, english_head, strongs, strongs_base, greek_pos, bracket_id, italic, italic_words, smcap_words, is_pn, morph, lemma. The displayed Greek lemma is joined live from `lexicon` via `LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base` (the indexed G-prefixed key added in Phase 1; replaced the old `SUBSTR(strongs_base,2)` join — this is why strongs_base MUST stay G/H-prefixed). `is_pn=1` marks proper nouns (set by import_tipnr.py). `morph`/`lemma` columns added rebuild #6 (~78% populated).
- `abp_surface` — `(verse_id, position, form, translit)` side table of the PRINTED (inflected) Greek per ABP word,
  feeding the word-study side-card "in this verse" line (ABP's source has no Greek surface words). Built read-only
  by `scripts/build_abp_surface.py --bh ~/bible-db/bh_scrape.db` (PA-only data step; DROP+rebuilds only its own
  table, never words/verses). SOURCE = ABP's OWN printed Greek from `bh_scrape.db` `bh_words.greek` (the BibleHub
  ABP scrape) — same text as `words`, so it matches ~91% (Rahlfs/TAGNT was tried first but capped at 75%: ABP-OT
  is Vaticanus-Sixtine vs Rahlfs's eclectic text). `/api/chapter` LEFT-JOINs it only if present (deploy-safe).
  bh's Greek is accent-only (no breathing marks), so `strip_marks` stores a form ONLY when it differs from the
  lemma by ENDING (no echo lines) → 56% of words show a line. Surface translit now FILLED by
  `scripts/build_abp_translit.py` (SBL romanization matching the lexicon headword style; the rough-breathing
  'h' is read from the lemma since bh forms have no breathing; re-run after any position-shifting rebuild).
  Full record: memory `project_bsb_words`.
- `lexicon` — Greek Strong's definitions
- `lsj` — Liddell-Scott-Jones Greek lexicon
- `abp_ext` — extended ABP data
- `dotted_lexicon` — corrected headword for ABP dotted Strong's. A side table in bible.db (built on PA,
  not in git) mapping the full dotted number (`G###.N`) → its OWN lemma + romanization, for the dotted
  numbers that are a genuinely DIFFERENT word from their base (ABP parks its added words at "nearest
  Strong's + a dot", so the base lemma is the alphabetical neighbour — G180.2 ἀκατασκεύαστος vs base
  G180 ἀκατάπαυστος). `chapter_text`/`verse_words` COALESCE it over the base `lexicon` join so the word
  card shows the right word; joined only if present (deploy-safe). Built by `scripts/build_dotted_lexicon.py`,
  audited by `scripts/audit_dotted_lemmas.py`. Full record: memory `project_dotted_strongs_lemma`.
- `books` — book metadata (name, testament, regex)
- `ai_search_cache` — cached AI query results and TSK synthesis
- `kjv_verses` — KJV full verse text (31,102 verses)
- `kjv_words` — KJV word-level tokens with position and italic flag
- `kjv_strongs` — KJV word → Strong's number mapping
- `bdb` — Brown-Driver-Briggs Hebrew lexicon (H-numbers)
- `pericopes` — section headings (book, chapter, verse, heading); populated from bh_scrape.db.bh_headings; DISPLAYED in the reader (all render modes) via `/api/chapter`'s LEFT JOIN + `.pericope-heading` in 59c-library-render.jsx
- `bsb_verses` — Berean Standard Bible verse text (public domain), mirrors kjv_verses on 1-66 book ids
- `bsb_words` / `bsb_strongs` — BSB per-word interlinear (LIVE 2026-06-15; loaded on PA = 386,063 words /
  381,948 Strong's / 66 books), mirroring `kjv_words`/`kjv_strongs`:
  `bsb_words(word_id, book_id, chapter, verse_num, verse_pos, word, italic, punc, form, form_translit)` +
  `bsb_strongs(id, word_id, strongs_id)`. strongs_id fully H/G-prefixed (same invariant as kjv_strongs; locked
  in test_build_invariants.py). `form` = the original word AS PRINTED (inflected Hebrew/Greek) + `form_translit`
  its transliteration (from the Berean tables' "WLC / Nestle Base TR RP WH NE NA SBL" + "Translit" columns,
  added 2026-06-15) — they feed the word-detail side-card "in this verse" line; the chip top line + interlinear
  stay the dictionary lemma. `/api/bsb/chapter` selects them only if present (PRAGMA guard, deploy-safe).
  Built by `scripts/load_bsb_words.py` from the Berean Bible project's Strong's-tagged tables
  (`bereanbible.com/bsb_tables.tsv`, public domain, CC0). Gives BSB chip mode + clickable word study (served by
  the `views_bsb` word routes; lemma/xlit joined from lexicon/bdb exactly like KJV) + per-word highlights.
  PA-only one-time data load (like bsb_verses) — `load_bsb_words.py` has a `--dry-run` that checks the tokens
  rebuild the live bsb_verses text before writing. Source-format gotchas + the deploy step: memory `project_bsb_words`.
- **Separate DB files (NOT bible.db, all gitignored + PA-only):** `notes.db` — user accounts/notes/
  highlights/journals + a `visits` table (owner-only visitor stats: day + daily IP+UA hash + referrer)
  + `password_resets` (short-lived single-use reset tokens, added 2026-06-16).
  `esv.db` — owner-only ESV text (`esv_verses`), loaded by `scripts/load_esv.py`. `niv.db` — owner-only
  NIV text (`niv_verses`), loaded by `scripts/load_niv.py`. See "Owner-only features".
  `heb.db` — **PUBLIC** Hebrew OT interlinear: `heb_words` (per word: hebrew, strongs H-number, morph,
  gloss, translit, grammar) + `heb_verses`, all 39 books from STEP **TAHOT** (Translators Amalgamated
  Hebrew OT, CC BY). Loaded by `scripts/load_hebrew.py`; served by the PUBLIC `views_heb.py`
  (`core.heb_db()`, no owner gate on the data). **PUBLIC for everyone, no login (2026-06-11)** —
  `hebPickable` gates on `hebAvail` (heb.db loaded), not the old `hebOwner`. Routes: `/api/hebrew/status`,
  `/api/hebrew/chapter/<book>/<ch>`, `/api/hebrew/verse-words/<book>/<ch>/<v>` (one verse, feeds the
  word-detail side panel's interlinear), and `/api/hebrew/strongs-count/<H#>` (2026-06-22, feeds the rail's
  "in Hebrew OT" link). **heb.db is now ALSO the Hebrew-word EVIDENCE source for Word study + Ask-corpus +
  SEO (not just a reading text) — see "Hebrew word sourcing" below + memory `project_hebrew_source_swap`.**
  Full record (the text itself): memory `project_hebrew_ot_interlinear`.
  `study.db` — authored "study modules" (built 2026-06-12/13; **topics opened to the PUBLIC 2026-06-16**):
  one `entries` table (row per topic / graph / name; `json` body + `type` + `status`).
  Served by `views_study.py` (`core.study_db()`); the **Study** tab (`static/src/55-study.jsx`). TOPICS = a
  sectioned browse (collapsible subtopics + a BOOK sub-collapse, alphabetical, comma-flipped display
  titles); GRAPHS = an argument map (admin-only): a shared pool of CLAIMS joined by per-tradition LINKS, each
  claim tagged with provenance (text/lexicon = grounded; tradition/conjecture/inference = not) + each link with
  a strength (solid/contested/weak), stress-tested by `argmap.py` (is the conclusion reachable from grounded
  claims on solid links? else name the load-bearing joint, or flag a gap; a grounded+SOLID objection knocks
  its target out → "overturned"). Drawn as a left→right SVG chart per tradition (auto-laid-out: barycenter
  row-ordering + lines routed through the column GAPS so nothing crosses a box). READ-ONLY in-app — authored via
  `scripts/add_study_graph.py`. (Replaced the old Denominations/Arguments claim editors 2026-06-18; full record
  + the graph json shape in memory `project_study_modules`.) Topics open READ-first (Edit button, admin); a
  "Preview as reader" admin toggle skins the tab as a visitor sees it.
  Verse text = ABP prose (KJV fallback).
  **GATING (go-live 2026-06-16): READING is split — published TOPICS + the metaV NAME-topics are PUBLIC
  (no login); argument graphs, all DRAFTS, and every WRITE/editor route stay admin-only; private
  `notes` are stripped from anything served to a reader.** Two-way study↔reader links: a study's verse
  references are clickable (jump into the reader — the resolver returns book/chapter/verse), and tapping a
  verse number shows an "In studies:" line in the xref panel (`/api/study/for-verse/<book>/<ch>/<v>`, a
  cached verse→topics index that includes HAND-AUTHORED studies only — `source != 'metav'`, so the giant
  Nave's imports don't blanket the text). PERF: a whole entry resolves in one batched pass (`_resolve_map`)
  + an in-memory `_RESOLVED_CACHE` (a 1000-verse topic opened ~13s→~1s). The editor's verse lookup is
  **`POST /api/study/verse`** (a query param was silently dropped before the app) and normalizes a typed
  ref to its full book name (`_canonical_ref`: gen 1:1 → Genesis 1:1). Topic INTROS are AI-written,
  text-first Berean (`✦ Draft with AI` button uses the WSGI key; `_draft_intro`/`_INTRO_SYSTEM`).
  Scripts: `add_study_topic.py` (hand-authored topic) + `add_study_graph.py` (hand-authored argument graph; both dry-run default / `--apply`),
  `load_study_topics.py` (MetaV import), `generate_topic_intros.py`, `publish_topics.py` (draft↔published;
  **`--names`** for the metaV name-topics), `find_topics.py`, `find_topic_dupes.py`, `merge_the_dupes.py`.
  Full record: memory `project_study_modules`.
- `<book>_words` / `<book>_verses` — non-canonical texts, each in its OWN two tables, walled off
  from the Bible's tables and from search/word counts. Built by `scripts/load_extra.py`; served by
  `/api/extra/<book>/chapter/<n>`. English-only texts (no Greek) load with an empty words table.
  Now LIVE (built by the per-group loaders under `scripts/`; all wired in the `NONCANON` array in
  static/src/60-library.jsx and auto-loaded by deploy.sh):
    * Septuagint Apocrypha — 16 Brenton books, English-only (`scripts/apocrypha/load_apocrypha.py`)
    * Pseudepigrapha — 1 Enoch, 2 Enoch, Jubilees, 2 Baruch, Apocalypse of Abraham, Assumption of
      Moses, all English-only (`scripts/apocrypha/load_pseudepigrapha.py` + `scripts/enoch/`)
    * Testaments of the Twelve Patriarchs — 12 separate English-only books (load_pseudepigrapha.py)
    * Apostolic Fathers — 14 books with FULL GREEK INTERLINEAR (not englishOnly): Didache,
      1-2 Clement, 7 Ignatian letters, Polycarp, Martyrdom of Polycarp, Barnabas, Diognetus,
      Shepherd of Hermas. Built by `scripts/apfathers/build_af.py` (+ `build_hermas.py` for Hermas)
      and loaded by `scripts/apfathers/load_apfathers.py`. Greek+lemma from Brannan/Lake (CC-BY-SA),
      Strong's mapped via openscriptures + Dodson glosses, English from Lightfoot. See memory
      `project_noncanonical_texts` for the pipeline + the build_af raw/ inputs (gitignored).
  See TODO.md "Non-canonical texts" + memory
  `project_noncanonical_texts`.

## Key Design Decisions
- ABP is the primary text — all word study anchored in ABP interlinear
- KJV is a full parallel corpus — searchable, with its own strongs, word clicks, and sidebar
- Italic words in KJV (italic=1) are translator additions with no source word
- Strong's G-numbers → lexicon/lsj tables; H-numbers → bdb table
- No systematic theology imported — text speaks first (Berean approach)
- Function words (171-word set) are filtered from search results
- Two-ending Greek adjectives (masculine & feminine share one form) show "Masculine/Feminine" on the
  word-study card when the morph source never resolves them — `decodeMorph` (00-core.jsx) checks the
  `TWO_END_SOFT_OT/_NT` sets in `static/src/00b-two-ending.jsx`, generated by `scripts/build_two_ending.py`
  (re-run after a words rebuild). Feminine/Neuter tags + words the source does resolve are left alone.
  Memory `project_two_ending_gender`.

## strongs_base format — CRITICAL INVARIANT
- `words.strongs_base` is fully G/H prefixed ('G4151', 'H7307') — normalized 2026-06-01
- This is NOT cosmetic: the lexicon join matches `l.strongs_g = w.strongs_base` (strongs_g =
  'G'||strongs). A BARE strongs_base ('4151') won't equal 'G4151' → NULL lemma (missing, not
  wrong). Under the OLD `SUBSTR(strongs_base,2)` join it was worse — a bare base shaved a DIGIT →
  WRONG lemma. (2026-06-03, pre-Phase-1: a rebuild left 592k bare → G2206 ζηλόω rendered as
  ἄκρον/G206. Fixed by `UPDATE words SET strongs_base='G'||strongs_base WHERE strongs_base GLOB
  '[0-9]*'`.) tests/test_strongs_join.py + test_build_invariants.py lock this invariant.
- `words.strongs` (the other column) is intentionally LEFT BARE ('2206', dotted '2321.1');
  the frontend renders it as `G{strongs}`. Only strongs_base carries the prefix.
- DOTTED-NUMBER CAVEAT: strongs_base drops the `.N` (built as `st.split(".")[0]`), so a dotted ABP number
  that's a DIFFERENT word than its base resolves the base's lemma through the join. The `dotted_lexicon`
  side table + a COALESCE in the word card correct this (see that table + memory `project_dotted_strongs_lemma`);
  form-variants like 1510.x (forms of εἰμί) correctly keep the base lemma.
- `kjv_strongs.strongs_id` is also fully prefixed (was always so)
- Always use single-match in SQL: WHERE w.strongs_base = 'G4151'
- After ANY words-table rebuild, verify: `SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'` must be 0
- AI system prompt may still reference old triple-match — update if issues arise

## Book Abbreviations
- ABP verses table uses: Mar (Mark), Joh (John), Php (Philippians), Jas (James), Heb (Hebrews)
- NT_BOOKS, BOOK_ORDER, BOOK_LABELS in static/src/00-core.jsx all use these abbreviations
- _KJV_BOOK_ID in app.py matches the same set

## Responsive Breakpoints
- **Desktop ≥1100px**: navy header, left nav panel (224px), lib-bar toolbar, detail panel as right sidebar
- **Mobile <1100px**: no header, sticky mobile toolbar (lib-toolbar), bottom tab nav, panels as bottom sheets
- JS thresholds: `navVisible >= 1100`, `isMobile < 1100`, `desktopBar` removed (two states only)
- CSS: `@media (max-width: 1099px)` / `@media (min-width: 1100px)` — no other breakpoints except 520px for very small phones

## Library Tab
Full per-feature history lives in memory (each block names its file). This keeps the standing
rules + gotchas; open the named memory for the backstory.

**Layout**
- Desktop toolbar (lib-bar): `[‹ Ch ›] | [Compare ▾] | [Strong's] [Interlinear] | [Chip] [Prose]`.
  Text source lives in the LEFT NAV, not the toolbar. ABP/BSB/HEB are one-click (HEB grays on NT —
  OT-only; falls back to KJV in the slot if heb.db is absent); KJV/ESV/NIV + non-canon books fold
  into a **"More ▾"** floating popout. (KJV was demoted into "More" 2026-06-22 — BSB is the default
  English now; the `kjvInMore = hebShown` flag keeps KJV up top only when heb.db can't fill the slot.
  Memory `project_hebrew_source_swap`.) The source row + Eras/Days are **underline tabs**, NOT boxed
  segments — the source row is a 4-equal-column grid (`.nav-source-seg.seg`) so a long "More" label
  can't shove the others.
- Mobile cockpit (lib-toolbar, fixed at the BOTTOM/thumb-zone on the Library tab) is an
  ICON row of five EQUAL-width slots (2026-06-20): `[🔍 Search] [▷ Play] [Abbr Ch] [ⓘ Info] [⚙ Options]`.
  Center slot keeps TEXT but shows the 3-letter book abbreviation (`selBook.abbrev`, "Amo 1"), not the
  full name; right slot is the sliders `Icon.Modes` (opens the reading-options sheet), not ABP/KJV text.
  Audio scrubber docks above the cockpit (`.lib-audio-dock`); desktop chrono keeps the inline one.
- Compare ▾, the "More" popout, and the Aa size/theme menu all close on outside-click/Esc AND
  **swallow that dismiss click** (capture-phase one-shot) so it doesn't hit a word chip behind them.

**Text sources / HEB**
- HEB = public Hebrew OT interlinear (memory `project_hebrew_ot_interlinear`): OT books only (book
  list + mobile picker drop NT in HEB mode), NO chronological order (Chronological is grayed in
  Hebrew). On a non-Hebrew text sitting on a NT book the HEB selector is grayed, not hidden.
- **Gray-vs-hide is the user's per-control call** (memory `feedback_gray_dont_hide`): GRAY a real
  feature that doesn't apply here (HEB on NT, Search on ESV/NIV, the MOBILE reading toolbar's play
  button when a text has no audio — kept grayed so the row stays balanced + book/chapter centered,
  2026-06-16); HIDE Compare + the order toggle on non-canon, and ESV/NIV (copyright). Propose gray for
  inactive-but-applicable, but confirm per control.

**Reader appearance** (memory `project_reader_appearance`)
- Reader font = `--f-serif` (Source Serif 4). The `Aa ▾` menu / mobile ModesSheet hold A−/A+ size +
  the **Light · Sepia · Dark** theme toggle. A font PICKER was tried and reverted — don't re-add one.
- Verse number + per-word Strong's SCALE with the A−/A+ size (`.lib-vnum` ≈0.5×, `.lib-iw-strongs`
  ≈0.53× of `--lib-font-size`) — keep relative, don't pin to fixed px.
- Themes ride `data-theme` on `<html>` (`lexica.theme.v1`); colors are vars at the TOP of styles.css.
  **Add new buttons with `--ctl-bg`/`--ctl-on`, never hardcoded `#fff`.** Dark traps: an
  `--ink`/`--accent` background flips LIGHT in dark, so pair its text with `var(--paper)`; borders use
  `var(--rule)` not `var(--line)`; navy header stays navy in every theme.
- **Palette tokens (reset 2026-06-19 to the Claude Design spec — implement his calls, don't freelance
  hues):** `--accent` = STEEL-BLUE (oklch 240, primary links/active), `--ai` = VIOLET (280, AI features),
  `--hl-match` = `#f0d27a` (the ONE shared gold for a matched/target word — used by `.corpus-hit` +
  `.lib-search-mark`, fixed across themes). **Gold (`--gold`) is RESERVED for target words ONLY** — active
  tabs, count pills, etc. use `--accent`. Navy = brand header + the chronological "you are here" active-passage
  rule (one shared `.nav-passage.on/.plan-passage.on/.mpick-passage.on`, dark falls back to `--spine-nt`; see
  memory `project_chronological_tab`). Memory `project_ai_search_redesign`.
- Desktop scrollbars slim app-wide + `html { scrollbar-gutter: stable }` reserves the gutter so
  swapping ABP↔KJV never shifts layout. Fonts load **`display=optional`, NOT `swap`**
  (templates/index.html) — kills the mobile toolbar reload flash. Don't switch back.

**Render modes**
- Chip = every word clickable, interlinear stack (Greek → English → Strong's). Prose = plain inline,
  only verse numbers tappable. KJV locks Prose to English. English-only non-canon books: the Chip
  toggle gives a verse-per-line layout (`renderExtraLines`); Strong's/Interlinear stay locked.
- **Hebrew "Prose" = the same interlinear chips flipped LEFT-TO-RIGHT** (2026-06-22): the Prose button
  (was grayed in Hebrew) toggles `viewMode` and a `.lib-heb-ltr` class that sets the row/content
  `direction:ltr` — only the WORD order flips; each `.lib-iw-heb` keeps its own `direction:rtl` so the
  letters stay correct. Strong's/Interlinear still work in it. Flag `hebProse = hebMode && viewMode==="prose"`
  in BOTH 60-library.jsx (desktop lib-bar + render) and 59b-library-nav.jsx (mobile ModesSheet). Matches the
  Ask-corpus Hebrew layout. Memory `project_hebrew_ot_interlinear`.
- **Chip-vs-prose for verses shown OUTSIDE the reader** (memory `project_lexicon_tab`): CHIP (ABP
  brackets + punctuation outside `]`) = reading pane + side-card interlinear. PROSE (plain, no
  brackets) = TSK xref, Study verses, side-card quote, in-text find list, AND Search + Lexicon result
  lists. Don't bracket the prose surfaces.
- **ABP brackets render INLINE in the reader's chips** (memory `project_library_bracket`): `[`/`]`
  ride inside the word's english cell (`.lib-iw-brk`), NOT a separate column. Old `.lib-bracket*`
  column CSS is dead.
- Italic = translator additions, muted/italic: KJV (italic=1), ABP (words.italic=1), ABP `[word]`.

**Compare** (memory `project_pericopes_parallel`)
- Pick 2–4 of ABP/KJV/BSB/ESV/NIV side by side (`translation === "parallel"`, `compareSel` = which).
  Desktop = N columns; mobile = stacked, one labeled line per text. Notes/highlights shared across
  columns (whole-verse paint).
- Labels are **navy, not gold**. Mobile per-line label runs INLINE with the verse — the chip box MUST
  be plain `inline`, NOT `inline-flex` (inline-flex drops a wrapping verse below the label). Chip mode
  IS allowed in compare (only place ABP Greek shows beside translations).
- Desktop picker = checkbox dropdown on Compare. Mobile = the Reading sheet's Text picker: TAP = read
  one, LONG-PRESS = tick into the 2–4 compare set.

**Chronological / reading plan** (memory `project_chronological_tab`)
- Reading-order toggle Canonical|Chronological, any version. Static `chronological.json` (no DB). An
  `Eras | Days` toggle sits atop the chrono picker.
- Days = a 365-day plan with per-text progress (`lexica.plan.v1`), binned into ~12 collapsible Month
  blocks. Component `static/src/58-dayplan.jsx`.
- Chrono mode shows an ESV-style daily Reading-intro panel (AI title+summary + era timeline):
  `views_chrono.py` + `static/src/59-dayintro.jsx`. **NO brown** anywhere — markers/hovers use
  `--accent`, not `--gold` (memory `feedback_no_brown`).

**Navigation / jumps**
- Left-nav book list is an ACCORDION (memory `project_book_nav_polish`): click a book to open its
  chapters, click again to collapse; testament spine + per-book chapter counts. Hover/active pills use
  `color-mix(... var(--bg) ...)`, NOT `--bg-sunk` (invisible on sepia). Mobile `Book Ch ▾` opens to
  the BOOK list first.
- Jumping to a verse (search/lexicon/read-in-context/xref/note) lands it in the UPPER THIRD; the left
  nav scrolls the active book to the TOP of its own list, never the window. The verse-number click
  target is an inner `.lib-vnum-num` hugging the digits (the empty gutter is inert).
- **Chrono jump rule:** an EXTERNAL jump (Search/Lexicon/Notes — flagged `nav.extern`) drops the
  reader back to canonical; an IN-READER jump (verse-number xref, word panel, chasing an xref) STAYS
  chronological (moves `chronoPos` to the passage). Either way `chronoPos` survives.
- Clicking a verse number opens the TSK Cross-Reference panel. Desktop link-over from Search/Lexicon
  auto-opens that verse's xref card over the chapter summary (tucked under any open word/note card).

**Detail rail** (memories `project_side_panel_rail`, `project_detail_panel_interlinear`,
`project_bsb_words`)
- Word clicks → LSJ (G-numbers), BDB (H-numbers), or metaV (proper nouns); KJV/Hebrew route the same.
- The side panel's Interlinear toggle FOLLOWS the reading text (KJV/BSB/Hebrew/ABP endpoints);
  Greek/Hebrew leads, English muted. ABP brackets inline.
- Headword = the dictionary lemma (big) + a small "in this verse" inflected-form line for
  Hebrew/BSB/ABP (ABP via the `abp_surface` side table; KJV has none).
- Rail stacks ≤3 deep: summary/Intro → xref → (word OR note). The "‹ back" link NAMES the card
  beneath it; the note card keeps just an X (DESKTOP). Word/xref panels trigger `has-detail` → compacts
  `.lib-reading` on desktop.
- **Mobile = bottom sheets, unified 2026-06-19:** every rail panel + word-study/notes/reading sheet
  shares ONE slide-up animation + scrim + radius/shadow and closes by **swipe-down + tap-scrim — NO close
  X on mobile** (X stays on DESKTOP panels; real centered modals like Account/password keep theirs).
  Section spacing aligns to the LOCKED word card. `useSwipeToDismiss`, memory `project_mobile_gestures`.
  Heights still drift (not yet unified — see that memory).

**Other**
- Focus mode (memory `project_focus_mode`): tap blank to enter, Esc/tap exits. Mobile hides chrome.
  **Desktop (rebuilt 2026-06-19): a dark + blurred wash makes the chrome RECEDE and go NON-interactive
  (click the wash to exit); the centered "book page" is READ-ONLY — any tap exits, word/verse clicks are
  off (those panels sit behind the wash). Light shadow, plain ‹ › chevrons (circles were tried + reverted).**
  Not remembered.
- In-text search (magnifying-glass panel, memory `project_esword_reference`): searches the current
  text; modes Any/All/Phrase; range presets + whole-word/case/exclude; `/api/text-search`. **Gotcha:**
  ABP's `verses.book` is a TEXT abbreviation, so a plain sort is alphabetical — `_ABP_RANK_SQL` maps
  each abbrev to Bible order so ABP sorts/filters canonically.
- Library remembers your spot across reloads (memory `project_refresh_persistence`): the `lexica.*`
  keys restore book/chapter/translation/order/compare/theme/font. **Lesson: restore instant toggles
  synchronously in the `useState` initializer, not an async effect — else the default flashes before
  the saved value.** Wheel over fixed chrome (header/nav/toolbar/rail) doesn't scroll the reading pane.

## Notes, Highlights, Bookmarks + Accounts (study notes — LIVE 2026-06-09)
Full detail: memory `project_notes_highlights`. The headline facts:
- **Sign-in lives in the DESKTOP header:** right side of the navy header — a "Log in" pill (opens the
  `AuthModal`, `authOpen` in 90-app.jsx) when signed out, or your **display name (else email)** when signed
  in. Clicking it opens the **account panel as a dropdown anchored under the button on the current page**
  (`AccountModal anchored`, `accountOpen` in 90-app.jsx) — it no longer jumps to the Notes tab (2026-06-20).
  The signed-in label is PLAIN TEXT now (the old pill/chip was dropped). `Header` props
  `email`/`name`/`onLogin`/`onAccount`. **Mobile has NO header**, so account there stays in the Notes tab;
  the in-tab account row is HIDDEN on desktop (redundant with the header).
- **Browser-local first; accounts are OPT-IN.** Notes live in the browser (`localStorage`
  `lexica.notes.v1`) and the app is fully usable with NO account. Signing in (below) syncs them
  across devices. One record = a word-position anchor + optional text + optional color + optional
  bookmark flag — a note, highlight, and bookmark are the SAME record:
  `{id, device, corpus, translation, book, bookName, chapter, start:{verse,pos}, end:{verse,pos},
  snippet, body, color, bookmark, deleted, created, updated}`. `id` minted AT CREATION. Delete is a
  SOFT delete (`deleted:true` tombstone) so deletes propagate through sync/import.
- **Accounts / sync — `notes.db`, the FIRST + ONLY visitor-write path on the site.** Kept OUT of
  bible.db (corpus is rebuilt; user data must survive). `core.notes_db()`; tables `users`, `tokens`,
  `notes` (one row per note, keyed by `code = "u<user_id>"`). `users` carries an optional `name`
  column (display name, auto-added on startup; shown instead of the email when set). `views_notes.py`
  blueprint: `/api/auth/signup|login|logout|me|config|google|set-name|delete-account` + `/api/notes/sync`
  (Bearer token). `set-name` saves/clears the display name; `delete-account` permanently removes the
  user + all their notes/plan/tokens (the in-app confirm makes you type "delete"). Passwords
  one-way hashed (werkzeug, ships with Flask). Stay-logged-in = random bearer token in `tokens` +
  browser `localStorage` `lexica.auth.v1`; logout deletes it. Sync = two-way last-write-wins by id.
  Guards: rate limits, size/count caps, parameterized SQL. Tables auto-create (deploy is a normal pull).
  Password **reset** + **set-password** (so a Google-only account can add one) are LIVE 2026-06-16 via
  SMTP/Resend — `request-reset`/`reset`/`set-password` in views_notes + a `password_resets` table; the
  emailed link opens the SPA at `/?reset=<token>`. `request-reset` always returns ok (never reveals
  whether an email has an account); `reset` is single-use + 1h + clears every existing session. NO email
  *verification* on signup yet. Mail setup + the 535/550 gotchas: memory `project_email_smtp`.
- **Google sign-in (optional).** `/api/auth/google` verifies Google's signed token (`google-auth`)
  and finds-or-creates the account by email. Shows only when `GOOGLE_CLIENT_ID` is set AND
  `google-auth` is importable — both checked LAZILY in `_google_ready()` so a deploy before setup
  can't break the site (button just stays hidden). See Deployment for the PA setup (it's done + live).
- Gestures (do NOT fight word-click=lexicon / verse-number=TSK): drag-select text → bar with 5 color
  swatches + "Note"; right-click (desktop) / long-press (mobile) a verse number → menu
  (Bookmark · Note · 5 colors). Mobile "Add note" bar pins to screen bottom (clear of the OS
  copy/share toolbar); `selectionchange` backstop. Inline bookmark marker at the start of any verse
  with a record (indents first line only).
- Anchoring is PER READING TEXT and covers non-canon texts too. ABP AND BSB (2026-06-15) capture exact
  word-spots (`data-note-pos` on the chip spans, `data-note-verse` on rows); KJV still anchors at the
  whole verse. Square corners + flush chips make a multi-word highlight one continuous bar. Same-anchor
  reuse (no dupes) via `NotesStore.findAnchor`.
- **Highlights paint across ALL translations (verse-level), 2026-06-09.** A highlight shows in ABP,
  KJV, and BSB alike — `chapterNotes` (`forChapter`) gathers every translation's records for the
  book+chapter; `hiForWord` paints EXACT words only in the text it was made in (`n.translation ===
  translation`) and ROUNDS UP to the whole verse in any other translation (words don't line up
  cross-text). The old same-`translation`-only wall is gone. ABP and BSB paint per-WORD inside their own
  text (BSB since 2026-06-15, via bsb_words positions); KJV still paints whole-verse only — KJV word-level
  is the one remaining open piece (kjv_words has positions, so the BSB `renderBsbVerse` pattern could close it).
- **Journal — free-form second note mode (LIVE 2026-06-09).** "Verse notes | Journal" toggle in the
  Notes tab. A journal page is the SAME record shape with `kind:"journal"` + `title` + `body` and NO
  anchor (no `.start`) — plain text, autosaving full-page editor, rides the same store/sync/Export-
  Import. Store: `journals()`, `createJournal()`, `getActiveJournal()`/`setActiveJournal()` (the page
  you last opened, in `localStorage` `lexica.journal.active.v1`), `appendToJournal()`. The merge guard
  lets `kind:"journal"` through without an anchor; `all()` keeps journals OUT of the verse-note list.
  Server per-page cap is bigger for journals (`_MAX_JOURNAL_BYTES` 64KB vs notes' 8KB).
- **Copy + send-verse-to-journal from the reader.** The drag-select bar AND the verse-number menu both
  carry Copy (verse text to clipboard) + Journal (appends `Genesis 1:8 (ABP) — text` — full book name +
  the reading text tagged; parallel reads `ABP/KJV`, non-canon gets no tag — via `journalLine()` in
  60-library.jsx, to the OPEN journal page; if none is open it flashes "Open a journal page first").
  A small `lib-flash` toast confirms. Both menus share ONE left-to-right order — colors · Note · Journal ·
  Copy (· Bookmark on the verse menu only) — keep them aligned if you touch either.
- Files: `static/src/12-notes-store.jsx` (`NotesStore` + sync/auth + journal helpers + `NOTE_COLORS`/
  `NOTE_COLOR_CSS` + `useNotesVersion`), `static/src/35-notes.jsx` (`NoteAddPopover`, `VerseNoteMenu`,
  `NoteColorRow`, `NotesPanel` editor, `JournalView`/`JournalEditor`, `NotesView` tab, `AuthModal`).
  Wiring in `60-library.jsx` (selection, paint, markers, verse menu, copy/journal, `flash`) + `90-app.jsx`
  (`activeNote` + panel + Notes tab). Notes tab: text search + filters (All/Bookmarks/Highlights/Notes)
  + sort (Recent/Reference) + collapsible group-by-book + the Journal toggle. **Top decluttered
  2026-06-11: the account email + Log out (or Log in / Sign up) sit in the title row — no "Signed in:"
  label, no Sync-now button, and the Export/Import buttons were dropped from the UI** (the
  store/sync code stays; account sync covers cross-device). **Mobile gotcha (fixed 2026-06-11): the
  base `.seg`/`.seg-b` pill styling was defined ONLY in the `≥1100px` desktop block, so any `.seg`
  control outside the Library on a phone (Notes mode/filter/sort, the owner About|Stats toggle)
  rendered as plain run-on text — a mirror rule now lives in the `≤1099px` block.** The mobile
  reading-options sheet (ModesSheet) shows Order + Study-layer as text labels (chip/prose + font
  stay icons).

## TSK Cross-Reference Panel
- Endpoint: GET /api/cross-references/curated/<book>/<chapter>/<verse>
- Step 1: Haiku selects 8-10 strongest refs from the full TSK list, reading the candidates + the
  source verse in BSB (KJV fallback — clearer than "thou/thee" for judging links; 2026-06-22,
  `cand_texts`). The picker returns indices into `all_refs`, so the cross_references KJV verse-id
  join is untouched.
- Step 2: Sonnet (claude-sonnet-4-6) writes the synthesis — adaptive length (~100-word soft
  ceiling, runs longer for a rich link), anchored in ABP source vocabulary. Prompt carries a
  worked example. (Moved off Haiku 2026-06-09 — ONLY the synthesis is Sonnet; the Step-1 picker
  and every other AI feature stay on Haiku.) BOTH the source verse AND the curated cross-refs are
  fed to it in ABP (2026-06-17, `_abp_text` in views_crossref.py); the fallback when ABP's
  versification lacks a verse is now **BSB, then KJV** (2026-06-22, `_bsb_text`) — so the write-up
  never quotes KJV "thou/thee". The displayed verse field is **`text`** (BSB-or-KJV; renamed from
  `kjv_text` 2026-06-22, frontend 40-crossref-panel.jsx). A `msg:` salt in `_XREF_VER` (now
  `bsb-fallback-4`) is bumped on any message/payload change so cached rows refresh (the fingerprint
  covers the prompts, not the message text or payload shape).
- Cached in ai_search_cache, key prefix `xref_cur:`/`xref_synth:`, ver_key=`xref:<hash>`
  (fingerprint of the two xref prompts — see "AI result cache" below)

## Lexicon Tab
- **REDESIGNED 2026-06-19 (under development) — see memory `project_ai_search_redesign`.** "Word study"
  is now a 3-pane layout (distribution rail · occurrences · word card) in `static/src/80-lexicon.jsx`;
  AI search was split OUT into its own **"Ask the corpus"** tab (`static/src/52-ask-corpus.jsx`, view
  key `corpus`) — it no longer renders inside Word study. New `--ai` steel-blue theme token = the AI
  accent. `/api/lexicon/profile` now also returns `derivation` + `related` (cognates, on-the-fly from the
  lexicon `derivation` text). The data flow + endpoints below are unchanged; the UI is still in flux
  (visual-fidelity + AI-curation passes pending). The two sections below describe the data model, not the
  current layout.
- **2026-06-19c — mobile word study built + the word card unified:** desktop + mobile share
  `renderDistRows`/`renderSenses`/`renderWordCardInner`; the English "words rendered" list is a
  collapsible `.glsenses`/`.glrow` card pinned above the occurrences. **Mobile (<1100px)** branches
  `if (isMobile)` before the desktop `.ws` return: context strip (`.wm-ctx`) → reading area (`.wm-main`)
  → icon-only bottom tools bar (`.wm-tabs`). The top section-nav is ICON-ONLY now too. **One shared height
  `--bar-h` (48px, in :root) sizes EVERY mobile chrome bar** (top nav, Library cockpit `.lib-toolbar`,
  `.wm-tabs`) + the sheet clearances — bars/sheets use `100dvh` + safe-area, never `100vh`. The **word CARD
  reuses the Library detail card's shared classes** (`.detail-hero`/`.sec`/`.detail-head`/
  `.detail-strong-head`/`.detail-body`/`.occ-link`) so the two can't drift — **word-study-only tweaks MUST
  be scoped to `.wd`; NEVER edit the shared rule (it leaks into the Library word card, which the user has
  LOCKED).** Mobile sheets (`WsSheet`) use the shared `useSwipeToDismiss` hook (`.wm-sheet` reserves
  `env(safe-area-inset-bottom)`); `.occ-link` action links are steel-blue `--ai`; results filters are
  underline `.tg` tabs. Full record: memory `project_ai_search_redesign`.
- **2026-06-20 — desktop Word study mirrors the Library shell.** The right word card is a fixed full-height
  panel over the navy header (like the Library's `.detail-side`): card head = header height so the divider
  runs unbroken across (empty state too, via `.wd .empty-pane::before`), columns match the Library (224px
  rail / `--sidebar-w` card), Strong's-number size back to the shared 18px, and the account pill is shifted
  clear with `.app.view-lexicon .hdr-right`. Distribution rail: `.brail-top` height = the search box so the
  two divider lines align; "All books" lost its box. The per-book bar's scaling is a DEAD END (46px track too
  narrow to read any curve change — left at the original linear). Memory `project_ai_search_redesign`.
- Dedicated word study tab — separate from AI Search
- Flow: search box → word profile → gloss chips → book distribution → verse list
- Smart search: detects Strong's (G4151, H7307), Greek, Hebrew, English
- Endpoints: `/api/lexicon/lookup`, `/api/lexicon/profile/<strongs>`, `/api/lexicon/verses/<strongs>/<book>`
- `lexicon_verses` response: `{verses: [{chapter, verse, words: [{w, h, i?}]}], glosses: [{gloss, count}]}`
  - `h=true` marks the target word in each verse (rendered highlighted in gold)
  - `glosses` = per-book rendering breakdown (chips update when a book is selected)
  - Optional `?gloss=spirit` param filters verse list to a specific rendering
- **Word-source toggle (focused word): ABP · HEB · KJV · BSB** (2026-06-22) — a number's occurrences,
  book distribution, and "renders as" in each. **Hebrew DEFAULTS to HEB = heb.db (the REAL Hebrew OT, NOT
  the old KJV bridge); the ~150 byform/Aramaic/name numbers heb.db lacks fall back to KJV (`has_heb` false).**
  Greek defaults to ABP. KJV/BSB stay explicit text toggles (KJV-as-text untouched). `lexicon_profile/books/
  verses` carry per-source branches + `has_abp/has_heb/has_kjv/has_bsb` + `abp/heb/kjv/bsb_glosses`; heb/bsb
  occurrence lists re-fetch per-verse in `VerseRow` (heb = an ALIGNED interlinear: each Hebrew word
  stacked over its gloss, laid LTR — letters stay RTL — replacing the old two-opposite-direction
  Hebrew-line + gloss-line that never lined up; `.corpus-heb-int`/`.chi-*` CSS; bsb mirrors KJV). The
  English-word finder shows all 4 "renders as" lines per word + a HEB/BSB filter, each line carrying that
  SOURCE'S TOTAL count (2026-06-22 — matches the word's own study page, counted the way `lexicon_profile`
  does; the lone ambiguous count on the right was dropped; HEB total folds homographs via `_heb_match`). The
  Hebrew object-marker אֵת H853 is dropped from the finder (`_HEB_FUNCTION_STRONGS`, the Hebrew analog of the
  Greek function-word filter — caveat: et's "him/them" suffix forms share H853 so they drop too). Full record:
  memory `project_hebrew_source_swap`.
- LexiconView is always-mounted (display:none) so state survives tab switches

## Search Tab — DEAD (no UI caller as of 2026-06-22)
- **The standalone Search tab is GONE from the app: `api.search` has no caller and `/api/search` is an
  orphaned endpoint (left in views_search.py, harmless). Live search now = the Library in-text search
  (`/api/text-search`, still used) + Word study (`/api/lexicon/*`) + Ask the corpus (`/api/ai-search`). The
  notes below describe the dead endpoint; don't wire new work to it.**
- Left input: lexicon/Strong's search; Right input: AI natural language query
- **Lexicon mode**: browse-only, ABP | KJV | All corpus toggle
  - ABP: ABP words table (Greek, dotted strongs e.g. G2321.1)
  - KJV: kjv_strongs/kjv_words (standard strongs, both G and H numbers)
  - All: ABP Greek + KJV Hebrew OT (best cross-testament view)
  - Word groupings and chips reflect the active corpus
- **AI mode**: study mode only, corpus filter All | OT | NT in toolbar alongside Curated | Canonical | ABP | KJV
- Search endpoint (`/api/search`) returns `{abp_results, kjv_results, abp_groupings, kjv_groupings, variants}`
- Search cache key prefix: `v3|`

## AI Search
- SQL gen + term-extraction on **Haiku**; the displayed **synthesis + verse curation (pass 2) on
  Sonnet** (`claude-sonnet-4-6`, 2026-06-21 — Haiku parroted the question's framing on nuanced
  "same vs different" questions and over-asserts; same lesson as xref/summary)
- Berean system prompt — no imported theology
- key_strongs: up to 10 chips (6 Greek + 4 Hebrew max)
- Empty-result retry (LAST RESORT, 2026-06-21): Haiku broadens the SQL only when the first query
  AND the cheap fallbacks (explanation-cited verses, proper-noun english LIKE) ALL come up empty —
  not the instant the SQL is empty. Saved a wasted ~5s call on Hebrew/empty searches.
- **Hebrew evidence from heb.db (2026-06-22):** a Hebrew target (H-number) pulls a canonical SPREAD of its
  REAL occurrences from heb_words (code-side supplement, mirrors the cognate/phrase ones), injected + tagged
  with the H-number so the citation guard counts them and the answer reads grounded. The model's KJV-bridge
  SQL (BDB → kjv_strongs → ABP) stays as a fallback. heb.db reads guarded; verses ABP's versification lacks
  are skipped (can't display). `_CACHE_CODE_VER`→37. Verse evidence has an **ABP·BSB·KJV·HEB display toggle**
  (per-turn in `AcTurn`, 50/52-corpus files; the shared `VerseRow` already renders all four). It ALWAYS
  defaults to ABP — the old auto-show-HEB-for-Hebrew-answers was dropped 2026-06-22 (user's call). HEB grays
  unless the answer has OT verses, and shows ONLY those OT verses when picked (heb.db is OT-only, so a mixed
  Greek+Hebrew answer no longer renders blank rows) — gate is `hasOtVerse` = any non-`NT_BOOKS` result.
  Memory `project_hebrew_source_swap`.
- **Speed shape (2026-06-21): model-bound.** terms ~1s + write-SQL ~5s (Haiku) + pass-2 synthesis
  ~11-12s (Sonnet, scales with how many verses it reads); DB ~0.1s. **Phrase queries no longer scan
  the 600k word-gloss:** a multi-word `english LIKE '%phrase%'` is re-run against the FULL verse text
  (`verses.text` + `kjv_verses` + `bsb_verses`, ~31k rows each) in code (the phrase supplement), and a phrase-ONLY query
  (phrase LIKE, no Strong's-number filter) SKIPS the gloss SQL entirely — it was ~6-7s and fruitless
  (cut a live "son of perdition" 15→9s). The proper-noun name-scan only fires when results are thin
  (`< _PROPER_NOUN_NEED`) — a common capitalized word like "Sabbath" was burning ~7s on a redundant
  scan. Timing `log.info("ai_search timing …")` kept on, plus per-call `cache[haiku-sqlgen]`/
  `cache[sonnet-pass2]` token-split lines + a `SLOW SQL` (>10s DB step) warning — a cost/stall meter
  (grep the PA `*.log`; ~3¢/search, Haiku SQL prompt caches, Sonnet pass-2 can't). "Stream verses
  first" = a not-yet-done frontend idea. Full record: memory `project_ai_search_architecture`.
- **Citation guard + grounding (2026-06-21).** Occurrence lists are pulled by Strong's = unfakeable;
  the leak is in the PROSE. A verse the model names/adds is checked against the target Strong's set —
  one containing NONE of the target words is `is_thematic` → frontend "Additional references" (kept,
  labeled, never primary). REGIME-AWARE: no target word (broad question) ⇒ no flag. The pass-1 prose
  is written from MEMORY before retrieval (can get a verse number wrong — it once wrote 2Th 3:3 for
  2:3), so the DISPLAYED explanation is ALWAYS the pass-2 GROUNDED one whenever the answer names a
  verse, even a short one (pass-2 is told to cite ONLY from the real retrieved list). Ranking is
  skipped only for a small pool whose prose cites nothing. Separate pass-3 dropped (folded into
  pass-2). Full record: memory `project_ai_search_architecture`.
- **Synthesis inputs + seatbelt (2026-06-21).** The verses handed to pass-2 are a SPREAD across books
  (`_spread_sample`: round-robin a few per book, not `results[:N]` — which, ordered by verse id, was
  early-OT-only, so a both-testament word came back OT-only and mislabeled "the LXX"); within each book
  the most cross-referenced verse (TSK count via `_xref_scores`, falls back to position order on any
  miss) wins the seat. Frontend SEATBELT (`AcProse` in 52-ask-corpus.jsx): the synthesis prose only
  LINKS a verse ref that's actually in the retrieved results — a verse the model named but we never
  retrieved renders as plain (unverified) text.
- **Honest empty-state + neutrality (2026-06-21).** Payload carries `grounded: false` when the search
  found no real occurrence (SQL 0 rows AND every shown verse is thematic/model-named); the frontend
  shows a pale-amber "no direct occurrences" caveat instead of a confident write-up. Both explanation
  prompts (`_AI_SYSTEM_TMPL` + `_CURATION_SYSTEM`) carry a NEUTRALITY rule — answer from the text, not
  the question's framing ("same?" vs "different?" must give the same answer; if the text doesn't
  settle it, say so. Killed the parrot-the-framing bug.)
- **Same-root cognate supplement (2026-06-22).** After the SQL runs, each GREEK target's same-root
  family is pulled in deterministically (`_greek_cognates` + the `_cognate_is_tight` stem filter in
  ai.py) — the relative's verses + a chip, but ONLY if it actually occurs (e.g. σαββατισμός G4520 /
  Heb 4:9 under σάββατον). Greek only (BDB has no etymology). A code/context change like this isn't in
  the search fingerprint → bump `_CACHE_CODE_VER` (now 38). Memory `project_ai_search_architecture`.
- **Synthesis standing rules — Berean (2026-06-22).** The displayed note (`_CURATION_SYSTEM`, mirrored
  in `_AI_SYSTEM_TMPL`): NO doctrinal verdicts (never rule a practice binding/abolished/etc. or assign a
  stance to an author — report the verse, let the reader conclude); contested "is X binding" questions
  are IN SCOPE (answer, withhold only the verdict — never refuse/deflect/rephrase); prose uses
  transliteration + Strong's number, NEVER raw Greek/Hebrew script (that's for the chips). All
  LOAD-BEARING. + REPORT, DON'T CHARACTERIZE (8721341, tested live): every clause must pin to a verse
  that states it — killed the soft-framing slop ("instituted at creation"/"reinterpreted") via the FRAME
  + a worked example, NOT a blacklist. + a SABBATH-vs-WEEK lexical note (σάββατον = the seven-day WEEK in
  the "first/one of the sabbaths" idiom — 1Co 16:2 etc., overrides ABP's wooden gloss) + no "what the
  verse doesn't do" riders. Memory `project_ai_synthesis_quality`.
- **Follow-ups (Ask the corpus) carry the recent thread** — last 6 turns + their key lemmas, sent as a
  `context` query param, woven into the term + SQL prompts only to resolve references ("it"/"the same
  word"). A "New thread" button (rail) resets. Follow-ups are never cached (thread-specific).
- Cached in ai_search_cache, ver_key=`search:<hash>` (fingerprint of system prompt +
  `_CURATION_SYSTEM` + book list + `_CACHE_CODE_VER` salt). See "AI result cache" below.

## AI result cache (ai_search_cache) — prompt-fingerprint scheme
Full record: memory `project_ai_cache_unify`; the synthesis model map + the author lesson:
memory `project_ai_synthesis_quality`.
- Every AI synthesis caches here with `ver_key = "<category>:<sha1-of-its-own-prompt>"` — categories
  `search:` (ai.py), `summary:` (views_summary.py), `xref:` (views_crossref.py), `pn:` (views_metav.py),
  `chrono:` (views_chrono.py, key `chrono_intro:<day>`). Editing a prompt changes only its category's
  hash, so just that cache refreshes — no manual version bump. The row key is stable + unique, so a
  regen overwrites the stale row in place. (xref, chapter summary, AND the ask-corpus synthesis/curation
  run on Sonnet; the rest on Haiku.)
- Helpers in core.py: `ai_fingerprint(category, *parts)`, `ai_cache_get(query, ver_key)` (an old-prompt
  row misses → regenerates), `ai_cache_put`, `ai_cache_prune(category, keep_prefix)`. Each category
  prunes ONLY its own stale rows at startup (app.py).
- **LANDMINE:** a delete must be scoped to its OWN category (search's startup cleanup is `search:%`
  only). If you add a new cache category, give it its own `<category>:<hash>` tag + its own startup
  prune — never widen another category's delete.
- summary rows add a per-book author suffix `summary:<tpl-hash>:<author-hash>`. `_BOOK_AUTHORS`
  (views_summary.py) feeds the BOOK BLURB only, NOT the chapter summary — well-established authors +
  named scribes only, the rest left blank on purpose (don't hard-push Haiku on disputed authors;
  memory `project_ai_synthesis_quality`).
- LSJ word-study summaries live in `lsj.summary_json` / `abp_ext.summary_json`, NOT this table, but
  self-heal the same way: a `_synth_ver` stamp (= `ai_fingerprint("lsj", ...)` in views_lsj.py) is
  checked on read and dropped/regenerated when the prompt changes — so editing the LSJ prompt
  auto-refreshes too, no clear script needed.

## BibleHub ABP Scrape
- Scraper: `scripts/scrape_biblehub_abp.py` — captures strongs, greek_pos, italic (last-word
  heuristic), strips `[ ]` brackets. The scrape (`bh_scrape.db`) is complete.
- The words table is rebuilt from `bh_scrape.db` — see the `/rebuild-words` command + "Database
  Tables → words". (morph column: filled to ~78% at rebuild #6; further fill scrapped 2026-06-15 —
  memory `project_abp_morph_gap`.)
- **Do NOT add conjugated manuscript forms** — the audience are non-Greek readers (standing rule).

## cross_references table
- Columns: id, verse_id, verse_ref_id
- Both IDs map to kjv_verses.verse_id
- 386,518 rows loaded from Torrey's TSK
- Join pattern: cross_references cr JOIN kjv_verses kv ON cr.verse_ref_id = kv.verse_id

## MetaV (person/place sidebar)
- Tables: `metav_people` (+_aliases, _groups, _relationships), `metav_places` (+_aliases; has lat/lon, strongs_g)
- Looked up by NAME (not strongs). Frontend fetches person + place in parallel; toggle shown when both exist
- Hebrew proper nouns: route to metaV (person/place) with BDB stacked BELOW (KJV-style). `isHebrewWord` (any H#)
  drives BDB; `isHebrew = isHebrewWord && !isPN` drives the Hebrew hero/LSJ suppression
- Default tab (Phase 6): trusts the word's OWN tipnr type via `pn_types` (a SET — 'person'/'place'/
  'person,place'). A clean single type is authoritative; ambiguous ('person,place', a genuinely shared
  number like Adam H121) or absent pn_types falls back to the strongs_g heuristic (place's G-number
  matching the word's strongs_base — note metav_places.strongs_g only holds G-numbers, so OT/H words
  always fall through to Person unless pn_types pins them). The Person/Place toggle is SUPPRESSED when
  pn_types is a clean single type (the other metaV card is a name-coincidence).
- tipnr schema (Phase 6, backlog #5): `entity_types` column holds the type SET so a strongs shared by a
  person AND a place keeps BOTH (was a PK collision: last-imported type won → Adam H121 read 'place').
  `entity_type` = single primary token (legacy). Migration adds the column at PA startup; re-run
  import_tipnr.py after any rebuild to populate. Old "do NOT trust entity_type" rule is now obsolete —
  pn_types (the set) is trustworthy.
- Gentilics (`/ites?$/`: Hivite, Sinite…): card labeled "People / Clan", place header "Homeland", AI summary
  fires on the clan tab. Kept as persons (Table-of-Nations genealogy is the value; only Jebusite has map coords)
- AI curation: `/api/metav/ai-description/<name>` — Haiku, 1-2 sentences, text-first prompt, cached in
  ai_search_cache (`pn:` key). Fills entries with no metaV/BDB data
- CRITICAL: the lexicon join is `LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base` (Phase 1 indexed key).
  strongs_g only ever holds 'G…', so a Hebrew H-number can never match — this STRUCTURALLY replaced the old
  `SUBSTR(strongs_base,2) ... LIKE 'G%'` guard that a Hebrew H121 used to slip past (bogus Greek G121 lemma
  made the metaV effect early-return and broke Hebrew-PN metaV). Applies to BOTH chapter_text and verse_words

## Maintenance / data-quality scripts
- `scripts/health_check.py <db>` — READ-ONLY scanner; run after ANY import/rebuild. ~14 checks (strongs_base
  invariant, dups, misalignment, fragmented brackets, missing/orphan greek_pos, strongs range, lexicon/bdb
  coverage) + person/place overlap report. Should be 0 warnings. `--email [--only-warn] [--email-to=addr]`
  mails the report via `mailer.py` (the nightly PA task; SMTP creds from `~/bible-db/.env`).
- `fix_greek_pos_gaps.py` / `fix_bracket_gaps_absorb.py` / `fix_orphan_greek_pos.py` / `dedup_words.py` —
  targeted data repairs, all with `--dry-run`. Touch only the named column; never blanket DELETE
- `fix_emdash.py` (`--dry-run` / `--apply`) — swaps ABP's literal `--` clause dash for an em-dash `—` in
  `words.english` + `verses.text` (double hyphen only; single hyphens like Beer-sheba are safe). Reversible;
  PA-only data step; RE-RUN after any words/verses rebuild (not folded into the build). Memory `project_library_bracket`.

## Rate limiting / security (2026-06-07 security pass)
- `core.limiter` (flask-limiter, memory storage): site-wide default `300/min` per endpoint per IP
  (flood backstop on the DB routes); paid AI endpoints set tighter `@limiter.limit("200 per hour")`
  which overrides the default. Static assets exempted via a `request_filter` in app.py (page loads
  never trip it). 429s handled by the errorhandler in app.py.
- AI-generated SQL runs on a READ-ONLY connection (`db_ro`), single-statement, SELECT-only guard;
  failures log the SQL/error server-side ONLY (never returned to the client — info disclosure).
- Verdict: read-only, no-auth, no-PII public app; all user input is parameterized; secrets via .env
  (gitignored); Flask debug off in prod (app.run(debug=True) is local-only). No critical findings.

## Refactor backlog (status 2026-06-07 — redesign Phases 0–6 done)
- See memory `project_architecture_rework.md` and TODO.md. DONE: #1 centralize Strong's handling (Phase 1 —
  `lexicon.strongs_g` join key + frontend `strongsBare`/`strongsTag`); #2 patch-fold (2026-06-09 — the six
  shape-keyed cleanup scripts now run INSIDE build_words_from_abp.py as one self-correcting pass; proven
  byte-identical to the old build+14-patch chain via compare_words.py; see "Words rebuild checklist"); #3
  backend DRY serialization (Phase 2, `_serialize_word_core`); #4 detail-panel state (Phase 4,
  `{hero, sections[]}`); #5 tipnr PK collision (Phase 6, `entity_types` type-set). REMAINING: the
  destructive-DELETE half of #2 stays (copy-first neutralises it — user's call 2026-06-09) and the frontend
  half of #3 (makeEntry/flattenAiResults dedup).

## Do Not
- Do not add KJV as the sole primary study text — ABP remains the anchor
- Do not touch existing ABP tables when adding unrelated features
- Do not commit bible.db to git
- NEVER run `DELETE FROM words` or `DELETE FROM verses` — OT and NT words are both in the words table; clearing destroys hard-to-recover data. If re-importing, use INSERT OR IGNORE (safe to re-run).
- Avoid the full DELETE+rebuild in `build_words_from_abp.py` unless truly necessary. It
  (a) clears `is_pn` and proper-noun Strong's, and (b) historically stripped the G prefix
  off strongs_base. The script is now patched (prefixes at INSERT, prints a reminder), but
  after ANY run you MUST re-run `import_tipnr.py` and verify the strongs_base invariant above.

## Words rebuild checklist (if you ever rebuild the words table)
The full step-by-step lives in the **`/rebuild-words`** slash command
(`.claude/commands/rebuild-words.md`): copy-first → single self-correcting build → tail patches →
the audit gates → swap/deploy → re-run the dotted-lexicon/surface/translit/two-ending builders. It's a rare,
high-stakes job, so the 90-line procedure is kept out of this always-loaded file. The hard SAFETY
rules for the words table stay in **Do Not** above; background in memory
`project_architecture_rework`.
