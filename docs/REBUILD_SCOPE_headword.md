# REBUILD SESSION SCOPE — head-word fix run (R-1, one heavyweight run)

Status: DRAFT 2026-07-16, awaiting JP gate clearance. Procedure = the `/rebuild-words`
slash command, not improvised. This doc is the session charter; the tickets hold the
detail (`TICKET_headword_class.md`, `TICKET_missing_strongs_pn.md`).

## Gate zero — disk space (pre-flight, BLOCKS the run)
- Requirement: **≥600 MB free AFTER the pre-rebuild backup exists**, shown by paste
  (`du -sh ~/db_backups/ ~/bible-db/*.db*` + the PA dashboard's free number — the
  NFS `df` figure is the shared server, NOT the account allowance; lesson 2026-07-16).
- Pre-backup check (reviewer flag 2026-07-16): confirm NO `bible.db-wal` / `bible.db-shm`
  sidecar exists at backup time (`ls ~/bible-db/bible.db-*` should find nothing) — an
  orphaned journal sidecar means the file alone may not hold the latest writes. Orphaned
  sidecars on dead TEST dbs are ignorable; don't delete any mid-run.
- Standing rule: NEVER delete the only pre-rebuild backup. If space forces a choice,
  keep the most recent known-good, drop older. (2026-07-16 trim: four old bible.db
  dailies dropped, July 13/14/15 kept, ~540 MB freed — pile now 1.1 GB.)

## In the run (batched per R-1 — fire once)
1. **RC-2 — two-tag emit fix** (`build_words_from_abp.py`): a `G*` tag after an
   empty/whitespace chunk pulls the capitalized name out of the previous slot (port
   of the standalone parser's repair). Kills the 477 blank-star rows.
2. **RC-1 — name-aware head pick, SCOPED to star/PN-tagged slots only**
   (`parse_abp._head_word` + call sites): prefer the capitalized non-sentence-initial
   token ONLY where the slot's tag is the star/PN tag. All other slots keep the
   existing pick (the 14,938 measurement proved a blanket rule would rewrite correct
   heads).
3. **Spelling-variant alias map** (`import_tipnr.py` ALIASES): curated variant→
   canonical entries for the ~1,690-row variant/LXX pile — every entry hand-checked
   against Strong's/TIPNR before it lands (wrong number > missing number). LXX-only
   forms with NO canonical target are NOT force-mapped — they wait for the Greek-name
   migration (R-2, own rebuild later; `DESIGN_greek_name_identity.md`). The curation
   happens BEFORE the run and lands in the same deploy.
4. **Backup keep-count** (`scripts/backup_db.py`): retention ~7 → 3 for the big
   file(s) — caps the backup pile ~800 MB permanently (JP-approved 2026-07-16).
5. **`finish_rebuild.sh` acceptance run** — owed from the Lexica-dictionary work;
   satisfied by observing this run, no extra work.

## NOT in the run
- Greek-name identity migration (R-2): its own staged rebuild AFTER this one — its
  audit diff needs clean heads as input (JP concurred 2026-07-16).
- The highlight cited-set fix (`TICKET_highlight_cited_set.md`): fast-path code fix,
  independent of the rebuild.
- The all-gold highlight fallback re-evaluation: AFTER this rebuild shows what
  genuinely head-less slots remain.

## Controls (every one fires before its zero is trusted)
- RC-2: 1Ch 1:49 → a Shaul row with real identity, no blank row (known positive).
- RC-1: Isa 38:21 "Isaiah said" → head isaiah · Jos 17:1 "Bashan area." → bashan ·
  Deu 15:12 "Hebrew woman," → hebrew.
- Non-regression: "God made" → made · "my spirit" → spirit · the five frozen S11
  pass-controls · `test_render_head_no_phantom.py` · strongs_base GLOB invariant = 0.
- Alias map: Ashchenaz @ 1Ch 1:6 → H813 (the ticket's control), plus the double-star
  count drops by the mapped amount — measured, not assumed.
- Post-run re-audit: re-run the double-star sweep; expected residue = LXX-only forms
  (deferred to R-2) + individually-justified rows. Any other residue = STOP.

## Dependent chain after the words build (in order, per the settled build order)
import_tipnr → PN surface → translit → build_rendering_norm → build_dotted_lexicon
(verify) → build_entity_binding (dry-run → JP review → --apply) →
build_metav_person_index/build_person_metav_link → fix_emdash/health_check → deploy.
(The gentilic guard is already live; the binding rebuild here re-runs it on the new
words — expect the render count to move because star rows gain real names/numbers;
account for the delta the same way as 2026-07-16, arithmetic must close.)

## Session shape
Fresh session, HIGH effort (words-table work). First step: show the RC-1/RC-2 code
changes + the alias-map batch for JP review BEFORE any build command. Build into
`bible.db.new` only; swap is JP's single reversible move. No build command posts
until gate zero's paste clears.
