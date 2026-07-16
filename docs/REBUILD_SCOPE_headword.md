# REBUILD SESSION SCOPE — head-word fix run (R-1, one heavyweight run)

Status: **READY TO RUN 2026-07-16 — all three review gates cleared (payloads
REVIEW_rebuild_precode.md / REVIEW_rc2_rereview.md / REVIEW_alias_batch.md), gate zero cleared,
all approved code LANDED (RC-1 6d7a6ee · RC-2 098a742 · alias batch 3ca0f29 · retention). Only
the run itself remains — fresh session, this charter + /rebuild-words.** Procedure = the `/rebuild-words`
slash command, not improvised. This doc is the session charter; the tickets hold the
detail (`TICKET_headword_class.md`, `TICKET_missing_strongs_pn.md`).

## Gate zero — disk space (pre-flight, BLOCKS the run)
**CLEARED 2026-07-16 (JP paste): dashboard 1.1 GB free**; minus the ~0.4 GB pre-rebuild
backup leaves ~0.7 GB ≥ the 600 MB floor. Backups pile 1.2 GB, bible.db 403 MB at check
time. Re-verify only if significant new data lands before the run.
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
- **Alias batch (reviewer conditions, 2026-07-16):**
  1. **Gentilic guard regression** — before the binding re-apply is trusted, re-run the
     two live-verified guard checks (Canaanitess 1Ch 2:3 → honest fallback; Midian
     Exo 2:15 → place card) PLUS at least one NEW-name gentilic (e.g. Christian
     Act 11:26 or Tyrians 1Ch 22:4). Guard behavior shifts → STOP.
  2. Ambiguous-drop list = `docs/tickets/alias_ambiguous_dropped.txt` (**149** spellings
     after the 2026-07-16 two-phase harvest fix; 31 overlap hand ALIASES and still
     resolve through it. The earlier 93 was the HIJACK BUG's signature — first-writer
     alternates stole 56 keys instead of dropping/deferring; see the roster-regression
     incident below).
  2b. **Roster zero-regression gate (PERMANENT, reviewer-mandated 2026-07-16):**
     `python3 scripts/check_roster_regression.py` must print CLEAN before ANY
     import_tipnr run whose loader or TIPNR file changed. Locked in CI by
     `tests/test_tipnr_roster.py` (sentinels: jesus=G2424, judah=H3063/G2455,
     simon=G4613, lord=H3068 … + christian=G5546, ashchenaz=H813). Incident: the
     landed alias batch let alphabetically-earlier entities steal 79 keys
     (jesus→G912 Barabbas); three green spot-controls didn't cover the other 4,300.
     A control proves its key; roster changes require the full diff. NOTE: elias no
     longer resolves from the roster natively — it resolves via hand ALIASES at
     ladder step 7 (elias→elijah), which is the control now.
  3. **Christian → G5546 (own Group number, NOT G2424)** — load-bearing, fires before
     the roster is trusted. RAN GREEN on the pinned file 2026-07-16, re-verify on PA.
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
