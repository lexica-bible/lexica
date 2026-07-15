# Lexica reference — Operations
Routed from CLAUDE.md. Deployment detail, CI/automation, backups, maintenance scripts, SEO,
security, rebuild procedure.

## Deployment (full detail)
- Preferred: `bash ~/bible-db/scripts/deploy.sh` — pulls, runs the invariant tests, loads any
  non-canonical books WHOSE FILES THE PULL CHANGED (diffs old..new HEAD, runs only touched
  loaders — a plain code deploy loads nothing), `pip install`s into the bible-env venv WHEN the
  pull changed `requirements.txt` (a failed install stops the deploy; bare-`pip` fallback if the
  venv path is missing), and reloads the site ONLY if tests pass. A loader hiccup warns but
  never blocks the reload, so adding a book just needs a normal deploy.
- Manual fallback: `cd ~/bible-db && git pull && touch /var/www/www_lexica_bible_wsgi.py`
- PA git is `pull.rebase false`, `merge.autoedit no` (no prompts). The database is NOT in git —
  managed directly on PA.
- Installing BY HAND after a requirements change: on PA, `workon bible-env` THEN
  `pip install -r requirements.txt` — NO `--user` inside the venv (it's
  `/home/appssanding720/.virtualenvs/bible-env`, Python 3.11; a `--user` install lands in the
  system 3.13 dir and is ignored). Then reload.
- **Env vars / secrets live in the WSGI, NOT a `.env`.** `/var/www/www_lexica_bible_wsgi.py`
  sets them with `os.environ['KEY'] = '...'`, and those lines MUST sit ABOVE the app import
  (module-level reads like `GOOGLE_CLIENT_ID = os.environ.get(...)` run at import).
  `core.load_dotenv()` doesn't reliably find a `.env` under the PA web app. Edit the WSGI, then
  reload (touch it). Keys set there: `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID`, `ESV_API_TOKEN`,
  `OWNER_EMAIL`, mail keys `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS` + `MAIL_FROM` +
  `SITE_URL` (+ optional `FCBH_API_KEY`, `MAIL_REPLY_TO`). Outbound mail goes through **Resend**
  (relay `smtp.resend.com:587`, user `resend`, pass = a Resend API key, From
  `noreply@lexica.bible`). The nightly `health_check.py` task can't see the WSGI env, so ITS
  copy of the mail keys + `OWNER_EMAIL` lives in a gitignored `~/bible-db/.env` (the script
  `load_dotenv`s it). Full record + gotchas: memory `project_email_smtp`.

## CI / automation
- **GitHub Actions** (`.github/workflows/ci.yml`) — every push/PR:
  1. The invariant tests — an **EXPLICIT curated list of filenames in ci.yml AND the pre-commit
     hook, NOT a `tests/*.py` glob** — a new test file gates ONLY if added to BOTH lists by hand
     (many test files, incl. the alias + rail-payload-contract tests, are deliberately not in
     the CI list). Tests build their own in-memory data, no bible.db — but the `tests` job
     `pip install`s flask + anthropic + python-dotenv + flask-limiter, because
     `test_synthesis_no_leak.py` imports `ai.py`/`core.py`, which need them at load time; keep
     that list lean, add only when a new test imports something new.
  2. Rebuilds `app.js` and FAILS if the committed copy is stale.
  3. Runs the **node** unit tests `tests/test_ac_word_groups.js` + `tests/test_rstack_logic.js`
     + `tests/test_note_inspect.js` (in the `frontend` job; the pre-commit hook runs them too)
     PLUS the Library reading-mode
     gates `test_library_order.js` + `test_render_markup.js` + the whole-bundle **render smoke
     gate `smoke_app.js`** (renders `<App/>` with real React via `react-dom/server` to catch
     blank-site reference/TDZ errors the pure-logic tests can't see — a component-body error
     passed green before it existed). react/react-dom are TEST-ONLY devDependencies; the app
     loads React from the CDN UMD.
  **Both lists are EXPLICIT filenames, never a glob — a new test file must be added to the CI
  job AND `scripts/githooks/pre-commit` or it gates nothing.**
  **A regression test carries a CONTROL section** (`test_note_inspect.js` is the worked example):
  transcribe the shipped-BROKEN logic beside the fixed one and assert the expectations FAIL
  against it. Otherwise a green only proves the test ran, not that it can see the bug it exists
  for — the same rule as `feedback_audit_tools_must_fail`, applied to a fix instead of a detector.
  Repo is public; check the Actions tab or
  `api.github.com/repos/lexica-bible/lexica/actions/runs`. `gh` CLI is on the dev box
  (2026-06-22; Claude calls it by full path) — NOT on PA. Memory `project_dependabot_workflow`.
- **LINE-ENDINGS for the app.js check (cost a CI fail 2026-06-14; the "all CRLF" claim CORRECTED
  same day):** Keep `git config core.autocrlf false` — with `autocrlf=true` your local
  `git diff` HIDES CR mismatches, so a wrong `app.js` slips past the hook and CI rejects it as
  stale. The `static/src/*.jsx` files are MIXED, NOT all CRLF: some LF (60-library.jsx,
  90-app.jsx, 30-detail-panel), some CRLF (59a/59b, 10-icons, 59-dayintro). Babel keeps a
  `/* */` block comment's CRLF in `app.js`, so app.js carries 4 CRLF from CRLF sources — the
  build reproduces them, so CI matches as long as you commit src + app.js together. RULE: match
  a file's EXISTING endings; do NOT flip a whole file. Check real endings with `xxd`/a byte
  count, NOT Git-for-Windows `grep -c $'\r'` or piped `git show` (both falsely reported the LF
  60-library.jsx as CRLF). Verify like CI before pushing:
  `git checkout HEAD -- static/src/ && npm run build && git diff --quiet -- static/app.js`.
- **Pre-commit hook** (`scripts/githooks/pre-commit`, wired via
  `git config core.hooksPath scripts/githooks`) — local twin of CI: rebuilds+stages app.js if a
  `static/src/*.jsx` is staged, then runs the tests and blocks the commit on failure. LOCAL DEV
  MACHINE ONLY — on PA it was unset (`git config --unset core.hooksPath`; PA has no Node).
  Bypass once with `git commit --no-verify`.
- **Dependabot** (`.github/dependabot.yml`) — weekly; PRs for pip/npm/actions, GROUPED (one PR
  per ecosystem: pip minor/patch batched + majors solo, all `@babel/*` together, actions
  batched). Not auto-merged. **Claude can't merge/close PRs — the safety classifier blocks it
  even with your OK; it hands you the `gh pr merge/close` commands.** A normal `deploy.sh` does
  the pip install after a merge. Memory `project_dependabot_workflow`.
- Nightly `health_check.py --email --only-warn` — LIVE on PA (daily scheduled task, 23:53 UTC).
  `--only-warn` = mails ONLY on a failed check. Task's mail keys + `OWNER_EMAIL` in
  `~/bible-db/.env`. Memory `project_email_smtp`.

## Backups — `scripts/backup_db.py` (2026-06-28)
The live dbs are PA-only + not in git, and a careless session has blanked bible.db.
`backup_db.py` is the floor: a daily, VERIFIED, rotating backup of EVERY live db
(auto-discovers `*.db` — bible/notes/study/esv/niv/heb/news/bh_scrape), kept in `~/db_backups/`
OUTSIDE the repo so a folder-nuke can't reach them. Uses SQLite's online `.backup()` (safe on a
live db, no torn copy), a `PRAGMA quick_check` gate (a bad copy never rotates out a good one),
gzip + chmod 0444 on older copies, and a `.info` manifest per copy so `--list` shows row counts
instantly. Restore = pick a stamp from `--list`, `gunzip -c` (or cp) over a `.new`, swap with
the reversible `mv`. **`study.db` is the one irreplaceable file** (hand-authored argument
graphs, no rebuild script). LIVE as a daily PA task (13:30 UTC, `--keep 7`). Memory
`project_db_backups`.

## Maintenance / data-quality scripts
- `scripts/health_check.py <db>` — READ-ONLY scanner; run after ANY import/rebuild. ~14 checks
  (strongs_base invariant, dups, misalignment, fragmented brackets, missing/orphan greek_pos,
  strongs range, lexicon/bdb coverage) + person/place overlap report. Should be 0 warnings.
  `--email [--only-warn] [--email-to=addr]` mails via `mailer.py`.
  **PLACEMENT RULE (2026-07-11):** any assertion about live PA DATA (row floors, table counts —
  e.g. the `abp_surface ≥ 359,288` backfill floor) goes HERE, not in pre-commit/CI — those run
  on the dev box and GitHub where bible.db doesn't exist, so the check would always pass and
  read as fake coverage. Control-fire every new check on a known-bad input before trusting it.
- `dedup_words.py` — drops byte-identical duplicate rows (tail safety net, 0-expect). Old
  targeted repairs (fix_greek_pos_gaps, fix_bracket_gaps_absorb, fix_orphan_greek_pos, …) are
  RETIRED to `scripts/graveyard/` (cert Session 2 — build-folded or adjudicated dead; see
  graveyard/README.md).
- `audit_split_flip.py <db>` (READ-ONLY) + `fix_split_flip.py <db> [--apply]` — the "LORD the"
  flip (determiner stranded AFTER its noun, vs clean `verses.text`). Audit shares its detector
  with the fixer (`find_flips`) so they can't drift; the fixer swaps each pair toward
  `verses.text` order and LOOPS to convergence. The build's root fix (`_split_compounds`
  source-phrase fronting) covers ONLY that pass — a SECOND flip producer (proper-noun slots)
  regenerates ~175 flip verses on any rebuild (proven by the 2026-07-04 cert harness), so the
  fixer is FOLDED into finish_rebuild.sh as step 6 (position-only swap, after ALL pinned patches
  + fix_emdash, before the abp_corrections apply). Re-run surface+translit after any `--apply`.
  **⚠ 2026-07-06: this pass OVER-FIRES — it swaps "noun, the" even when the "the" belongs to the
  FOLLOWING noun (Jer 48:1 "…forces, the God" → wrong "…the forces, God"), causing 175 of 180 v2
  word-order defects. Its own `audit_split_flip` reads 0 because it reuses the fixer's flawed
  "noun,the = stranded determiner" assumption; only the independent v2 oracle catches it. Blocks
  the S9 swap; needs scoping to genuine strands. Detail: memory `project_reassembly_diff`.**
  Memories `project_abp_certification` + `project_split_compounds_flip`.
- `build_abp_corrections.py` + `apply_abp_corrections.py` — the Tier-B **abp_corrections** table
  (in bible.db; 18 rows: Cushi ×6 + Jer 49:13 ×2 + L2 1Sa 6:11 ×4 + L10 Mal 3:6 ×4 + L5
  Dan 4:33 ×2) and its guarded apply (fires only when the cell still holds the recorded
  fresh-parse value, LOUD skip otherwise, log beside the db). New source-defect corrections = new
  rows via build_abp_corrections.py (checkpoint first), never a new fix script.
  **2026-07-06 (b196b9a): the overlay now also carries PROSE (verses.text) corrections — no schema
  change, `field='verses.text'` + `position=-1` sentinel (inert to the words path), before/after in
  the source/corrected cols. `apply_abp_corrections.py --only {words,verses}` gives TWO apply points
  in finish_rebuild: prose at step 4b (BEFORE split-flip, its oracle), words at step 7 (`--only
  words`). The 5 (f) prose rows seed from `AUDIT_tierB_f_proposed.json` at the S9 rebuild — live's
  table is still 18 until that swap.** Full record: `AUDIT_abp_certification.md`.
- `fix_emdash.py [db]` (`--apply`) — swaps ABP's literal `--` clause dash for `—` in
  `words.english` + `verses.text` (double hyphen only; Beer-sheba safe). FOLDED 2026-07-03: runs
  as a tail step of finish_rebuild.sh (after fix_split_merges — a "--" precondition there must
  match first). Memory `project_library_bracket`.
- `cert_manifest.py build|verify` + `cert_reparse_harness.py` — the ABP-certification feed pin
  (74 files, SHA-256, committed as `cert_manifest.json`) and the Tier A re-parse harness (full
  production build into `bible.db.new`, row-diff vs live, reports cert_report_summary.txt /
  cert_deltas.tsv). Read-only on live. Records: `AUDIT_abp_certification.md` +
  `AUDIT_abp_invariants.md`.
- `cert_invariants.py [db]` / `--controls` — the runnable ABP invariant suite (Tier A CERTIFIED
  end-to-end as of the 2026-07-04 live rebuild+swap). READ-ONLY; 7 checks: row pins
  (words 626,305 / verses 31,237), split-flip=0 (imports the production `find_flips`, never a
  copy), em-dash '--'=0, correction-overlay reconciliation (failures NAME the row), feed
  manifest, backup freshness, and (Session 4) person/place binding — no proper-noun name renders
  BOTH a fuzzy-place AND an exact-person (the Cushi shape; reads pn_binding+tipnr_entities,
  deploy-safe = passes if the tables are absent). `--controls` seeds bad input into a throwaway
  db and proves checks 1-4 + 7 fire (5-6 fired on live incidents). **RE-PIN RULE: the pins move
  ONLY in a deliberate-rebuild commit after compare_words passed — never hand-edited to force
  green.** Memory `project_abp_certification`.
- `fix_italic_heads.py` (`--dry-run`/`--apply`, `--strongs G####`, `--all`) — makes a slot's
  SEARCH LABEL (`words.english_head`) its OWN rendering, never a translator-added italic word
  ("take favor" had labeled λαμβάνω/G2983 "favor"). english_head ONLY; re-runnable.
  Build-folded (`_strip_italic_heads` in build_words_from_abp.py), so a rebuild reproduces it.
  4,409 fixed 2026-06-25. Memory `project_english_head_label`.
- `fix_pn_subject_merge.py` (`--apply`/`--list-skipped`, dry-run default) — splits a subject
  NAME ABP crammed onto its verb's cell back onto its own clickable `*` slot (name on the LOWER
  slot, verb keeps its number; bracketed cases keep both in-bracket sharing the reorder number).
  2,297 fixed 2026-06-26 (2,278 flat + 19 bracketed) + 2 εἰμί copula merges 2026-06-28 (Sarai
  Gen 11:30, Crete Zep 2:6; `_peel_eimi` fires on a G1510 cell with a capitalized non-roster
  lead + adjacent empty `*`, minus function-word leads, unbracketed slot-after only).
  Build-folded (`apply_pn_subject_split`, after insert, BEFORE import_tipnr). After `--apply`:
  re-run import_tipnr → build_abp_surface → build_abp_translit. Audit for the εἰμί class:
  `scripts/audit_eimi_subject_merge.py`. Memory `project_pn_subject_verb_fold`.
- `build_entity_binding.py` (dry-run default / `--apply`) — the Issue-2 entity-binding build.
  PA-only, reversible; **re-run after any words rebuild** (re-tiers from live metaV). Binder
  logic in `entity_resolution.py`. The old `fix_cushi_strongs.py` is RETIRED — the 6 Cushi slots
  live in `abp_corrections`, applied by the rebuild tail. Memory
  `project_entity_resolution_rebuild`.
- `add_hebrews13.py` (dry-run default / `--apply`) — ONE-OFF additive repair (DONE+LIVE
  2026-06-30): restored missing Hebrews 13 (the ABP source file had no ch 13 → no verse rows →
  its words were skipped, since the build only emits words for verses already in `verses`).
  Dry-run proves the path by regenerating Heb 12 and diffing byte-for-byte vs live. **General
  invariant: a missing verse row silently drops its words.** Memory
  `project_hebrews13_restore`.

## Words rebuild
The full step-by-step lives in the **`/rebuild-words`** slash command
(`.claude/commands/rebuild-words.md`): copy-first → single self-correcting build → tail patches
→ audit gates → swap/deploy → re-run the dotted-lexicon/surface/translit/two-ending +
rendering-norm builders + import_tipnr + entity binding + metav person link. Rare, high-stakes —
never improvise. Hard safety rules stay in CLAUDE.md "Do Not". Background: memory
`project_architecture_rework`. The build scripts (`build_words_from_abp.py` +
`build_words_from_bh.py`) write ONLY to `bible.db.new` (a consistent online snapshot); the live
file is never opened for writing; swap is one reversible `mv`.

**`finish_rebuild.sh`'s contract — DO NOT "fix" it with `set -e` (2026-07-14).** The no-abort is
DELIBERATE: every tail step is independently targeted and re-runnable, so a half-patched copy is
worse than a finished one with named failures. It keeps going, COLLECTS any step that reported a
problem, and REFUSES to print `== finish_rebuild done ==` — naming them and exiting non-zero.
**No `done` line ⇒ DO NOT SWAP.** (Until 2026-07-14 `run()` never looked at an exit code at all,
so ANY failing step — `import_tipnr` included — scrolled past and it still printed `done`; a
failure degrading into a green-looking finish.) A step that "reported a problem" may have FAILED
**or** may have completed and flagged something for a human — the p2wl:v2 guard fixture drift
check is the second kind. **Its clean path with real steps is UNVERIFIED (stubs only) — watch the
first live run.**

**`import_tipnr.py` is the SOLE writer of `is_pn=1`** (the build CLEARS it; everything else only
reads it) — which is why the p2wl:v2 guard fixture drift check is chained there and fires
automatically, standalone run included. The claim it checks is single-sourced in
`scripts/check_p2_guard_fixture.py`, which OWNS it (the probe-2 test imports it — never a second
copy). **Drift ≠ a broken rebuild: it means the FIXTURE is stale.** Paste the run's findings in,
re-date `FIXTURE_VERIFIED`, re-run the probe-2 tests. Detail: `DESIGN_p2_guard_drift_check.md`.

## Rate limiting / security (2026-06-07 pass)
- `core.limiter` (flask-limiter, memory storage): site-wide `300/min` per endpoint per IP; paid
  AI endpoints set tighter `@limiter.limit("200 per hour")`. Static assets exempted via a
  `request_filter` in app.py. 429s handled by the errorhandler.
- AI-generated SQL: READ-ONLY connection (`db_ro`), single-statement, SELECT-only guard;
  failures logged server-side only.
- Verdict: read-only, no-auth-required, public app; user input parameterized; secrets via
  WSGI/gitignored .env; Flask debug off in prod. No critical findings.

## SEO / crawlable pages + site icons
The SPA is invisible to search engines, so `views_seo.py` serves plain server-rendered HTML
(`templates/seo/`) reusing the JSON endpoints' read-only SQL:
- `/read/` (book index) · `/read/<slug>` (book) · `/read/<slug>/<ch>` (ABP) ·
  `/read/<slug>/<ch>/<text>` (kjv|bsb|heb) — interlinear chips with ABP brackets/numbers;
  `/word/<strongs>` (G/H word study); `/sitemap.xml` generated (chapters + every Strong's used);
  `/credits` (attributions page — every text/lexicon/data/font source + its license name+link;
  CC BY/BY-SA/CC0 REQUIRE the license named AND linked). **PUBLIC-DOMAIN TEXTS ONLY — never
  ESV/NIV.**
- The app deep-links INTO these: `/?b=&c=&t=` jumps to a chapter, `/?lex=G####` opens the
  Lexicon — read once on mount in `static/src/90-app.jsx`, then the query is stripped.
- `app.py` serves root files crawlers fetch (`/favicon.ico`, `/apple-touch-icon.png`,
  `/robots.txt`); `/sitemap.xml` is the seo blueprint's. Icons + `og.png` live in `static/`,
  regenerated by `scripts/gen-icons.js` (transient `sharp` dep). seo.* endpoints are
  rate-limit-exempt.
- Full record: memories `project_seo_pages` + `project_seo_branding`. Google Search Console set
  up (Domain property, sitemap submitted).

## Licensing / provenance quick reference
LSJ = display-only cross-reference, never generative. Strong's Greek = OpenScriptures (CC BY-SA,
not PD). Strong's Hebrew 1890 = public domain (the `bdb` table — see data-model.md). Dodson /
TBESG / TBESH = plain short glosses. MM (Moulton-Milligan) = NOT in the app. LEXICA tag reserved
only for verse-grounded senses. Share-alike bucket (MetaV, AF Greek, OpenScriptures Strong's
Greek) = keep out of any future dictionary export. /credits page is live; ABP permission email
sent + Van der Pool public-domain intent received (official dedication not yet executed).

## Refactor backlog (status 2026-06-07 — redesign Phases 0–6 done)
See memory `project_architecture_rework` and TODO.md. DONE: #1 centralize Strong's handling
(Phase 1); #2 patch-fold (the six shape-keyed cleanup scripts run INSIDE build_words_from_abp.py
as one self-correcting pass; proven byte-identical via compare_words.py); #3 backend DRY
serialization (Phase 2, `_serialize_word_core`); #4 detail-panel state (Phase 4,
`{hero, sections[]}`); #5 tipnr PK collision (Phase 6, `entity_types`). REMAINING: the
destructive-DELETE half of #2 (copy-first neutralises it — user's call 2026-06-09) and the
frontend half of #3 (makeEntry/flattenAiResults dedup).
