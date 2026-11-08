# Lexica reference — Operations
Routed from CLAUDE.md. Deployment detail, CI/automation, backups, news nightly, maintenance
scripts, SEO, security, rebuild procedure. (Architecture-refactor history: memory
`project_architecture_rework`.)

## Deployment (full detail)
- Preferred: `bash ~/bible-db/scripts/deploy.sh` — pulls, runs the invariant tests, loads any
  non-canonical books WHOSE FILES THE PULL CHANGED (diffs old..new HEAD, runs only touched
  loaders — a plain code deploy loads nothing), `pip install`s into the bible-env venv WHEN the
  pull changed `requirements.txt` (a failed install stops the deploy; bare-`pip` fallback if the
  venv path is missing), and reloads the site ONLY if tests pass. A loader hiccup warns but
  never blocks the reload, so adding a book just needs a normal deploy.
- Manual fallback: `cd ~/bible-db && git pull`, then a proper reload (below) — NOT a bare touch.
- **RELOAD RULE (G2 stale-worker lesson, reviewer-ruled 2026-07-24):** for any deploy that
  changes SERVING code, the dashboard-Reload-equivalent is the standard — a `touch` reload
  once left a half-refreshed worker mix live (old code 404ing, mixed state 500ing, while a
  console run of the same code+data was clean). The 5× repeated-curl sweep on a changed
  endpoint is part of DEPLOY VERIFICATION, not incident response. **deploy.sh implements
  both since 2026-07-26** (PA API reload — the button's exact equivalent — + built-in sweep).
  The API token: PA injects `API_TOKEN` into consoles opened AFTER the token exists
  (Account → API Token) — an already-open console won't have it; reopen. Without a token
  deploy.sh stops loudly and says to press the dashboard button by hand.
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
  reload (deploy.sh's API reload, or the dashboard button). Keys set there: `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID`, `ESV_API_TOKEN`,
  `OWNER_EMAIL`, mail keys `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS` + `MAIL_FROM` +
  `SITE_URL` (+ optional `FCBH_API_KEY`, `MAIL_REPLY_TO`). Outbound mail goes through **Resend**
  (relay `smtp.resend.com:587`, user `resend`, pass = a Resend API key, From
  `noreply@lexica.bible`). The nightly `health_check.py` task can't see the WSGI env, so ITS
  copy of the mail keys + `OWNER_EMAIL` lives in a gitignored `~/bible-db/.env` (the script
  `load_dotenv`s it). Full record + gotchas: memory `project_email_smtp`.
- **Google sign-in setup.** Diagnose a missing Google button with
  `curl -s <site>/api/auth/config` → `{"google_client_id": ...}`; `null` = env not
  loaded (the WSGI line is missing, sits BELOW the app import, or no reload). `google-auth` is in
  requirements (pip install in `bible-env`). Google Cloud consent screen: **External**, client type
  **Web application**, JS origin = the https site URL, then **Publish app** (email + profile scopes
  need no verification review). The client ID is public, not a secret.
- **Web logs** (`/var/log/www.lexica.bible.access.log`, `.error.log`, `.server.log`; older ones
  rotate to `.N.gz`). Each access line carries an address in its FIRST field AND ends
  `"<client IP>" response-time=<seconds>` — dropping only the first field still shows visitors'
  IPs (11/8 slip); strip both with
  `sed -E 's/^[^ ]+ //; s/"[^"]*" (response-time=)/\1/'`. A News share-key holder's requests carry
  `?key=` in the URL — mask it too (`s/key=[^ &"]*/key=HIDDEN/g`). The byte count is AFTER PA's
  front end gzips the reply (`/api/news/all` logs 10.7 MB for a 53 MB JSON body; the app itself
  has no compression). Code 499 = the browser gave up before the reply came back.

## CI / automation
- **GitHub Actions** (`.github/workflows/ci.yml`) — every push/PR:
  1. The invariant tests — an **EXPLICIT curated list of filenames in ci.yml AND the pre-commit
     hook, NOT a `tests/*.py` glob** — a new test file gates ONLY if added to BOTH lists by hand
     (`scripts/githooks/pre-commit` too, or it gates nothing; many test files, incl. the alias +
     rail-payload-contract tests, are deliberately not in the list). Tests build their own
     in-memory data, no bible.db — but the `tests` job `pip install`s flask + anthropic +
     python-dotenv + flask-limiter, because `test_synthesis_no_leak.py` imports `ai.py`/`core.py`,
     which need them at load time; keep that list lean, add only when a new test imports
     something new.
  2. Rebuilds `app.js` and FAILS if the committed copy is stale.
  3. Runs the **node** tests listed in the `frontend` job (the pre-commit hook runs them too),
     incl. the Library reading-mode gates and the whole-bundle **render smoke gate
     `smoke_app.js`** (renders `<App/>` with real React via `react-dom/server` to catch blank-site
     reference/TDZ errors the pure-logic tests can't see — a component-body error passed green
     before it existed). react/react-dom are TEST-ONLY devDependencies; the app loads React from
     the CDN UMD.
  **A regression test carries a CONTROL section** (`test_note_inspect.js` is the worked example):
  transcribe the shipped-BROKEN logic beside the fixed one and assert the expectations FAIL
  against it. Otherwise a green only proves the test ran, not that it can see the bug it exists
  for — the same rule as `feedback_audit_tools_must_fail`, applied to a fix instead of a detector.
  Repo is public; check the Actions tab or
  `api.github.com/repos/lexica-bible/lexica/actions/runs`. `gh` CLI is on the dev box (Claude
  calls it by full path) — NOT on PA. Memory `project_dependabot_workflow`.
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
  batched). Not auto-merged. **Merging: the safety classifier blocked `gh pr merge/close` on
  6/22 but it worked 10/25 on JP's explicit ask — try when he asks; if denied, hand him the
  `gh pr merge/close` commands.** A normal `deploy.sh` does the pip install after a merge.
  Memory `project_dependabot_workflow`.
- Nightly `health_check.py --email --only-warn` — LIVE on PA (daily scheduled task, 23:53 UTC).
  `--only-warn` = mails ONLY on a failed check. Task's mail keys + `OWNER_EMAIL` in
  `~/bible-db/.env`. Memory `project_email_smtp`.

## DISK RETENTION POLICY (reviewer-ruled 2026-07-26; item 6 JP-approved 2026-07-30 — the
## permanent fix for the recurring 98%-full incidents; nothing here is optional)
1. **Rebuild fallbacks (`bible_pre_*`): exactly ONE per receipted rebuild** — the
   swap-adjacent copy. Uncompressed until the rebuild's receipt chain closes + 7
   days; gzip after; DELETE when the next receipted swap's fallback exists with
   green gates. This is a hand-run policy applied at rebuild close-outs, not automated.
2. **The nightly backup job backs up LIVE dbs ONLY** — `backup_db.py` skips
   `bible_pre_*`, `*_test*`, `*.new*` (patterns in the script cite this ruling; do
   not re-broaden). Backing up a fallback was the leak: every rebuild's 410M copy
   silently gained a second 410M nightly duplicate.
3. **Stray journal fragments** (`-wal`/`-shm`/`-journal` leftovers in bible-db or
   db_backups) are deletable as a class on sight.
4. **Disk guard in health_check** (`disk_check`): WARN ≥85%, ERR ≥95% with the
   remedy named in the line. Quota via `DISK_QUOTA_GB` env (default 10 — JP
   upgraded PA storage to 10 GB on 2026-08-01 after the 5 GB cap broke a build
   snapshot AND the nightly bible.db backup on the same day; the "free space"
   line a script prints is the shared filer, never the quota).
6. **ARC ROLLBACK COPIES — single-name rule (after 5 quota hits in one day; numbered 6 because
   other docs cite "ops.md item 6"; old item 5 was a one-day cleanup log):** the
   per-ship rollback copy is only ever
   `bible.db.rollback` — each ship OVERWRITES it, never mints a new
   `bible.db.pre_<arc>` name (that naming pattern is retired; four of them
   stacked up in one week and blew the quota mid-swap). Deeper history = the
   nightly verified copies. **PRECONDITION for dropping an old copy: the newest
   nightly bible.db copy in `~/db_backups` must be STAMPED AFTER the last swap**
   (`ls -lh ~/db_backups | grep bible`) — the nightly runs ~13:30 UTC, so an
   evening ship's state is NOT covered until the next day; if the nightly is
   older, the previous arc copy stays as the deep rollback until a nightly
   captures the current state (reviewer-sequenced 2026-07-30: deleting
   pre_greekhdr before that check would have left no path back past two arcs).

## Backups — `scripts/backup_db.py`
The live dbs are PA-only + not in git, and a careless session has blanked bible.db.
`backup_db.py` is the floor: a daily, VERIFIED, rotating backup of EVERY live db
(auto-discovers `*.db` — bible/notes/study/esv/niv/heb/news/bh_scrape), kept in `~/db_backups/`
OUTSIDE the repo so a folder-nuke can't reach them. Uses SQLite's online `.backup()` (safe on a
live db, no torn copy), a `PRAGMA quick_check` gate (a bad copy never rotates out a good one),
gzip + chmod 0444 on older copies (gzipped to a `.gz.part` name, read back in full, then renamed —
a failed gzip keeps the raw copy and FAILS the run so the freshness alarm fires; the 10/25 quota
hit had left a cut-short .gz under the real name and stamped success —
`tests/test_backup_rotate.py`), and a `.info` manifest per copy so `--list` shows row counts
instantly. Restore = pick a stamp from `--list`, `gunzip -c` (or cp) over a `.new`, swap with
the reversible `mv`. **`study.db` is the one irreplaceable file** (hand-authored argument
graphs, no rebuild script). LIVE as a daily PA task (13:30 UTC, `--keep 7`; bible.db keeps 3 by
the script's `KEEP_OVERRIDE`). Memory `project_db_backups`. **Rotation only touches dbs still
present in `~/bible-db`:** once a working db is deleted, its backups are orphaned — never
compressed, never removed — until deleted by hand (two 9/6 copies sat uncompressed for two months;
the hdrlane one is kept on purpose as a §9.95 reference).

## News watch nightly (`scripts/news/daily.sh`)
The News tab's data (news.db) is refreshed by ONE PA scheduled task:
`bash ~/bible-db/scripts/news/daily.sh`. Story, rulings and labeler lessons: memory
`project_news_watch`.
- **Runs the bible-env venv python** (`$HOME/.virtualenvs/bible-env/bin/python`) and hard-stops if
  it's missing — PA's system python3 lacks `anthropic`, so a plain-`python3` task fails SILENTLY at
  the scoring step.
- **Step order:** `gather_news.py` (Google-News thread searches) → `pull_rss.py` (outlet feeds) →
  `score_news.py` (Haiku, only unscored rows) → `group_news.py` (event labels) →
  `resolve_new_faces.py` (real article links + page-date check; `|| true`) →
  `merge_dups.py --apply --nightly` (same-article merge; `|| true`).
- **NEVER add `--rescore` to the nightly** — it re-tags the whole corpus and costs money every
  night; it's a by-hand step after a thread-KEY change in `queries.py`.
- **`resolve_backfill_all.py` step is DISABLED** (commented out) since 2026-07-05: it crashed mid
  write-back and corrupted news.db (a lost page-1 write during a WAL fold-back on PA's NFS home,
  with the site reading at the same time; `d6b8c310`). Every news opener now uses
  `journal_mode=DELETE` + `busy_timeout` (`bbbe0963`). Re-enabling it is a deliberate decision, not
  a revert.
- **`ANTHROPIC_API_KEY` must be in `~/bible-db/.env`** — the scorer and labeler read it there; a
  scheduled task can't see the WSGI env. A missing key only prints "ANTHROPIC_API_KEY not set" and
  leaves an unscored backlog.
- **daily.sh does NOT git-pull.** A deploy (`deploy.sh`) is what puts news code live before the
  nightly runs.
- **Switch + drift log for the cross-night labeler fix (ON since 2026-10-31):**
  `touch ~/news_seed_off` → the next nightly labels the old way (same-night labels only, no reuse
  check); `rm ~/news_seed_off` turns it back on. No code or data change; labels already written
  stay. Each nightly appends one line to `~/news_reuse.log` ("reuse check: offered N, approved A,
  rejected R"). Live re-check: `tests/fixtures/news_clustering/relabel_check.py --run --nights-only`.
- **The nightly's own output** lands in `/var/log/schedule-log-1448472.log` (+ `.1`) — each night
  starts `==> [YYYY-MM-DD …] gathering`; the `==> grouping` section holds the labeler's ERR and
  "left unlabeled tonight … id N" lines. Zero ERR lines does NOT prove every AI call answered: a
  blank or partial reply is counted as "no" without a log line (parked in TODO).
- **CI sees FROZEN labels** (`tests/test_news_clustering.py`) — any labeler/prompt change also needs
  `relabel_check.py --run` on PA (writes nothing; tee it to a log, PA's console cuts long output).
- **news.db path footgun:** the real file is `~/bible-db/news.db` (`core.NEWS_DB`). A bare
  `sqlite3 news.db …` run from `~` CREATES an empty `~/news.db` decoy that reads exactly like a
  blanked database. Always use the full path; `rm ~/news.db` clears a decoy.

## Maintenance / data-quality scripts
- `scripts/health_check.py <db>` — READ-ONLY scanner; run after ANY import/rebuild. Data checks
  (strongs_base invariant, dups, misalignment, fragmented brackets, missing/orphan greek_pos,
  strongs range, lexicon/bdb coverage, abp_surface floor) + backup + disk checks + person/place
  overlap report. Should be 0 warnings. `--email [--only-warn] [--email-to=addr]` mails via
  `mailer.py`.
  **Backup check = freshness AND damage** (cert Session 5; a freshness-only check was blind to the
  2026-07-02 corrupt-but-recent copy): freshness reuses the one guard in `cert_manifest.py`; every kept
  backup is swept — raw `.db` gets `PRAGMA quick_check`, `.db.gz` gets a full stream-read (gzip's own
  checksum catches truncation). `--backup-controls` = the durable proof-of-fire (seeds a truncated raw +
  truncated gz in a temp dir, requires exactly those two warns).
  **Right after a deploy it can report false `database is locked` errors:** each site worker's
  first-request warm-up (`app.py` `_warm_caches`) writes the AI cache into bible.db, and
  health_check's `sqlite3.connect` waits only Python's default 5 s. Wait a few minutes, or re-read
  the failed checks with `sqlite3 -readonly -cmd ".timeout 60000"` — "locked" is unread, never a pass.
  **PLACEMENT RULE (2026-07-11):** any assertion about live PA DATA (row floors, table counts —
  e.g. the `abp_surface ≥ 395,003` floor) goes HERE, not in pre-commit/CI — those run
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
  source-phrase fronting) is the real cure; the fixer is FOLDED into finish_rebuild.sh as step 6
  (position-only swap; ORDER IS LOAD-BEARING: after ALL pinned patches + fix_emdash, before the
  abp_corrections words apply) as a guarded safety net — pin re-declared 2026-08-01 in
  finish_rebuild.sh: expect 1 flip / 1 verse per rebuild. Re-run surface+translit after any
  `--apply`.
  **LESSON — it once OVER-FIRED while its own audit read 0.** It swapped "noun, the" even when
  the "the" belonged to the FOLLOWING noun (Jer 48:1 "…forces, the God" → wrong "…the forces,
  God"), causing 175 of 180 v2 word-order defects; cert S2 had read those ~175 as a second flip
  producer. `audit_split_flip` read 0 because it shared the fixer's flawed "noun,the = stranded
  determiner" assumption — only the independent v2 oracle (rows vs `verses.text`) caught it. A
  shared fixer/audit detector shares its blind spot. Scoped in S10 (`49f09c66`: two clean-text
  guards in `find_flips` + `audit_split_flip --control`). Memories `project_reassembly_diff`,
  `project_abp_certification` + `project_build_folded_fixes` §5.
- `build_abp_corrections.py` + `apply_abp_corrections.py` — the Tier-B **abp_corrections** table
  (in bible.db; active rows + `superseded` ones such as the Cushi rows) and its guarded apply
  (fires only when the cell still holds the recorded fresh-parse value, LOUD skip otherwise, log
  beside the db). **The active count is pinned in code** — `cert_invariants.PINS
  ['abp_corrections_active']` + a frozen member list (+ `.sha256`) in
  `tests/fixtures/corrections/`; re-dump and re-pin together whenever the active set changes.
  The current pin is read off the edition-upgrade BUILT copy, so live and the built copy differ
  until that swap. **A row's `corrected_value` is stored in FINAL corpus form (em-dash `—`, never
  `--`); `source_value` stays as the build writes it** — finish_rebuild step 5 swaps `--` AFTER 4b
  applies prose rows, and cert check 4 compares byte for byte (edition-upgrade §9.80, 2026-11-04).
  New source-defect corrections = new rows via build_abp_corrections.py (checkpoint first), never
  a new fix script.
  **The overlay also carries PROSE (verses.text) corrections (b196b9a)** — no schema change,
  `field='verses.text'` + `position=-1` sentinel (inert to the words path), before/after in the
  source/corrected cols. `apply_abp_corrections.py --only {words,verses}` gives TWO apply points in
  finish_rebuild: prose at step 4b (BEFORE split-flip, its oracle), words at step 7 (`--only
  words`). Full record: `docs/audits/AUDIT_abp_certification.md`.
- `fix_emdash.py [db]` (`--apply`) — swaps ABP's literal `--` clause dash for `—` in
  `words.english` + `verses.text` (double hyphen only; Beer-sheba safe). FOLDED 2026-07-03: runs
  as a tail step of finish_rebuild.sh (after fix_split_merges — a "--" precondition there must
  match first). Memory `project_library_bracket`.
- `cert_manifest.py build|verify` + `cert_reparse_harness.py` — the ABP-certification feed pin
  (76 files since 2026-10-31 = 75 + the app feed `abp_app_html/abp_app_slots_italic.tsv`; SHA-256,
  committed as `cert_manifest.json`) and the Tier A re-parse harness (full
  production build into `bible.db.new`, row-diff vs live, reports cert_report_summary.txt /
  cert_deltas.tsv). Read-only on live. Records: `docs/audits/AUDIT_abp_certification.md` +
  `docs/audits/AUDIT_abp_invariants.md`.
- `cert_invariants.py [db]` / `--controls` — the runnable ABP invariant suite (Tier A CERTIFIED
  end-to-end as of the 2026-07-04 live rebuild+swap). READ-ONLY; 7 checks: row pins
  (`PINS` in the script — words/verses, never the pre-tail build count; pronoun-review flag count
  6,882 at the 2026-07-16 head-word rebuild is an advisory anchor, not a suite check — the tsv is
  overwritten per build, so an unpinned count can't be diffed later), split-flip=0 (imports the
  production `find_flips`, never a copy), em-dash '--'=0, correction-overlay reconciliation (failures NAME the row), feed
  manifest, backup freshness, and (Session 4) person/place binding — no proper-noun name renders
  BOTH a fuzzy-place AND an exact-person (the Cushi shape; reads pn_binding+tipnr_entities,
  deploy-safe = passes if the tables are absent). `--controls` seeds bad input into a throwaway
  db and proves checks 1-4 + 7 fire (5-6 fired on live incidents). **RE-PIN RULE: the pins move
  ONLY in a deliberate-rebuild commit after compare_words passed — never hand-edited to force
  green.** One ruled exception (JP 2026-10-31, `6e9d2df8`): a COUNT pin left stale by a later
  landing (the 27 BD-* rows), with every row proven HOLDING on live, is re-pinned in its own commit
  with a frozen live member list as the receipt. Memory `project_abp_certification`.
- `gate_greek_header.py <live> <scratch> [--declared <json>]` — the pre-swap header gate (A identity
  tables untouched · B header-table delta shape · C controls/pins). **`--declared` (landed `c07288d6`,
  edition-upgrade charter §4.5):** a per-lane file `tests/fixtures/<lane>/declared_deltas*.json`
  (committed) states the EXPECTED deltas; gate A then checks actual == declared per table (counts for
  words/verses; a member set on the tight key book+chapter+verse+name for pn_binding, with
  `changes: {col: [from, to]}` and unchanged columns by name), gate B accepts only the declared key
  moves. Undeclared = FAIL in today's wording; a declared row with NO delta = FAIL naming it. Without
  the flag the gate is byte-for-byte the old one. Run at `/rebuild-words` 8b.3, BEFORE step 9 (so
  abp_surface is still identical). Test `tests/test_gate_declared.py` (four cases); worked example
  `tests/fixtures/rebuild_trap/declared_deltas_20261025.json` (the 10/25 Michaiah rows).
- **Edition-upgrade lane scripts (landed 2026-10-31; rulings = `docs/handoffs/DESIGN_q2_build.md` §9):** `abp_app_feed.py` (the one feed reader: manifest sha+size pin; `--check`; `--attribute <copy>`
  read-only) · `census_feed_{dash,markup,brackets}.py` (read-only feed scanners -> frozen
  `tests/fixtures/edition_upgrade/*_census_20261031.tsv` + `.sha256`; brackets has `--control`) ·
  `build_words_from_abp.py --app-feed` (derivation A, two-build compose; `--dry-run COPY_DB` read-only,
  `--dry-run-nodb` local; writes `strict_fail_<date>.tsv` + `eligible_<date>.tsv` to `--out`, default
  `~/edition_upgrade_runs`; `--gen-count-differs`) · `build_prose_from_app.py` (derivation B: `--eligible`
  = A's file; `--dry-run COPY_DB` / `--dry-run-nodb` / `--apply COPY_DB`; refuses the live path). Tests:
  test_abp_app_feed, test_feed_censuses, test_app_transplant (incl. the default-path fingerprint),
  test_build_prose — all in CI + pre-commit. Console output is ASCII (cp1252-safe).
- `fix_italic_heads.py` (`--dry-run`/`--apply`, `--strongs G####`, `--all`) — makes a slot's
  SEARCH LABEL (`words.english_head`) its OWN rendering, never a translator-added italic word
  ("take favor" had labeled λαμβάνω/G2983 "favor"). english_head ONLY; re-runnable.
  Build-folded (`_strip_italic_heads` in build_words_from_abp.py), so a rebuild reproduces it.
  4,409 fixed 2026-06-25. Memory `project_build_folded_fixes` §6.
- `fix_pn_subject_merge.py` (`--apply`/`--list-skipped`, dry-run default) — splits a subject
  NAME ABP crammed onto its verb's cell back onto its own clickable `*` slot (name on the LOWER
  slot, verb keeps its number; bracketed cases keep both in-bracket sharing the reorder number).
  2,297 fixed 2026-06-26 (2,278 flat + 19 bracketed) + 2 εἰμί copula merges 2026-06-28 (Sarai
  Gen 11:30, Crete Zep 2:6; `_peel_eimi` fires on a G1510 cell with a capitalized non-roster
  lead + adjacent empty `*`, minus function-word leads, unbracketed slot-after only).
  Build-folded (`apply_pn_subject_split`, after insert, BEFORE import_tipnr). After `--apply`:
  re-run import_tipnr → build_abp_surface → build_abp_translit. Audit for the εἰμί class:
  `scripts/audit_eimi_subject_merge.py`. Memory `project_build_folded_fixes` §8.
- `build_entity_binding.py` (dry-run default / `--apply`) — the Issue-2 entity-binding build.
  PA-only, reversible; **re-run after any words rebuild** (re-tiers from live metaV). Binder
  logic in `entity_resolution.py`. The old `fix_cushi_strongs.py` is RETIRED — the 6 Cushi slots
  live in `abp_corrections`, applied by the rebuild tail (and `/rebuild-words` 8b.1
  `restore_frozen_pn.py` restores the full 2Sa 18 Cushi set: 8 since 2026-10-25). Memory
  `project_entity_resolution_rebuild`.
- `add_hebrews13.py` (dry-run default / `--apply`) — ONE-OFF additive repair, done: restored
  Hebrews 13 (the source had no ch 13 → no verse rows → its words were skipped). Worked example of
  the additive-insert proof (dry-run regenerates Heb 12, diffs byte-for-byte vs live). **General
  invariant: a missing verse row silently drops its words.** Memory `project_build_folded_fixes` §10.

## Words rebuild
The full step-by-step lives in the **`/rebuild-words`** slash command
(`.claude/commands/rebuild-words.md`): copy-first → single self-correcting build → tail patches
→ audit gates → swap/deploy, with import_tipnr, entity binding and the surface/translit/
two-ending/rendering-norm builders re-run on the built copy. Step 12 (JP 11/7) re-runs `build_dotted_lexicon.py` →
`build_word_gloss.py` → `build_person_metav_link.py` on the built copy before step 9. Since `1ad10cec`
the dotted builder REQUIRES a db path (it used to hard-wire LIVE bible.db and ignore any path), the
gloss builder reads pinned STEPBible copies (`tests/fixtures/stepbible/`, `--fetch` to download), and
the metaV link builder takes `--out-dir` + a read-only `--check-place-orphans`. Rare, high-stakes — never improvise. Hard safety rules stay in CLAUDE.md "Do Not". Background: memory
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
check is the second kind.

**`import_tipnr.py` is the SOLE writer of `is_pn=1`** (the build CLEARS it; everything else only
reads it) — which is why the p2wl:v2 guard fixture drift check is chained there and fires
automatically, standalone run included. The claim it checks is single-sourced in
`scripts/check_p2_guard_fixture.py`, which OWNS it (the probe-2 test imports it — never a second
copy). **Drift ≠ a broken rebuild: it means the FIXTURE is stale.** Paste the run's findings in,
re-date `FIXTURE_VERIFIED`, re-run the probe-2 tests. Detail: `docs/DESIGN_p2_guard_drift_check.md`.

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
