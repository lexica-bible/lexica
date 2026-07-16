# HANDOFF — rebuild-prep session close (2026-07-16, at 2501ee2)

Supersedes the earlier 8488ba3 handoff. Session closed clean; wrap ran (living docs + memory
updated). This is the pick-up sheet.

## 1. REBUILD: READY TO RUN — the next session's whole job
All three review gates cleared (payloads `REVIEW_rebuild_precode.md` / `REVIEW_rc2_rereview.md`
/ `REVIEW_alias_batch.md`, verdicts pasted + logged) **and gate zero cleared** (JP dashboard
paste: 1.1 GB free). Every approved change is LANDED in code with controls green:
- **RC-1** scoped star-slot head pick (6d7a6ee) — name beats trailing common word, star slots only.
- **RC-2** capitalized-lead splitter fallback (098a742) — red-first fixture in
  tests/test_folded_fixes.py; 1Ch 10:13 puzzle closed by live-row proof (Saul already split).
- **Alias batch** (3ca0f29) — see §3.
- **Backup retention** bible.db keep-3 (6d7a6ee).
Only the run remains: **fresh session, HIGH effort, `/rebuild-words` procedure, opener =
`docs/REBUILD_SCOPE_headword.md`** (status header there says READY TO RUN and carries
everything below). First post = the copy-first backup command; nothing writes before JP's
paste confirms the backup exists.

## 2. Five run-time gates (written IN the charter — listed here for the record)
1. Pre-rebuild backup exists before anything writes; **no `-wal`/`-shm` sidecar on bible.db**
   at backup time.
2. RC-2 dry-run catch count reconciles against the **148-row baseline**
   (`docs/tickets/blank_star_classes.md`) before apply; shortfall itemized.
3. **Christian → G5546** (Group row's own number, not parent Jesus' G2424) fires before the
   roster is trusted.
4. Gentilic guard re-checks pass before the binding re-apply is trusted: Canaanitess 1Ch 2:3
   honest fallback · Midian Exo 2:15 place card · at least one NEW-name gentilic
   (Christian/Tyrians). Guard behavior shifts → **STOP**.
5. Post-rebuild double-star residue = the **221 documented leaves**
   (`docs/tickets/alias_leave_list.txt` + decisions/caution rows) + the blank-star classes
   (`blank_star_classes.md`). Anything else → **STOP**.

## 3. Alias batch outcome (the day's biggest find)
- **Loader root-cause fix**: `import_tipnr.parse_tipnr` had discarded 10,127 en-dash
  sub-record lines as comments since day one — every alternate spelling (Elias, Sabta,
  Ashchenaz) and every sub-record Strong's was lost; the hand ALIASES map was compensating.
  Fixed: roster 2,824 → 4,387 keys; numbered entities 2,687 → 2,862; Group gentilic rows keep
  their OWN numbers.
- **`scripts/tipnr_alias_variants.py`** — 399 hand-checked KJV/LXX variant entries, wired at
  ladder step 7 (inline ALIASES wins on overlap). Per-entry verdict + reason =
  `docs/tickets/alias_decisions.txt` (16 rejects incl. wrong-sibling traps + LXX common-noun
  transliterations; 2 fragment cautions parked).
- **Leave-list** `docs/tickets/alias_leave_list.txt`: 10 common-word keys (RC-1 territory) +
  209 LXX-only/research names, honest-unmapped per R-2.
- **93 ambiguous spellings dropped + logged** (`docs/tickets/alias_ambiguous_dropped.txt`);
  23 overlap hand ALIASES and still resolve through it — no behavior change. (An earlier
  simulation said 149; 93 is the number the landed code produces and logs.)
- Count reconciliation: 1,296 dump names → 1,075 resolvable + 221 documented, unexplained 0.
- Takes effect at the rebuild's import_tipnr step — nothing on the live site changes until then.

## 4. Stale items from the previous handoff — REMOVED
- "Alias map ~1,690 rows is the big pre-run lift" — DONE (and it became a loader fix + 399
  entries, not 1,690 hand lines).
- RC-2 open questions — CLOSED (approved, fixture green, puzzle resolved).
- Gate zero disk paste — CLEARED.

## 5. Open fronts carried forward UNCHANGED (pointers as before)
1. **Synthesis Greek script** — `docs/tickets/TICKET_synthesis_greek_script.md`; parked.
2. **Greek-name migration** — `docs/DESIGN_greek_name_identity.md`; awaits JP's Q1–Q5 rulings;
   sequenced AFTER this rebuild.
3. **Provenance audit sweep** — contract §8, AUDIT ONLY session.
4. **Contract RENDER build work** — chartered nowhere yet (§6 name-echo, §5 tappable tags,
   §4 name-path state line, AI tag on summaries); TODO.md entry.
5. **pn_binding hand-check rows** — 65 HOT + 798 number-only on PA; fold into the audit session.
6. **Descriptor-of-individual gentilics** — `docs/tickets/TICKET_gentilic_binding.md`;
   audit-session line item.
7. **5 known-red tests** — tests/test_lexica_draw_cache.py without the live DB; TODO.md entry.
8. **Ask-corpus counts + zero-bars** — TODO.md entry; JP's timeline.

Standing rulings (R-1 batch-into-one-run, R-2 Greek-name direction + never-fabricate, backup
retention, scoped head-pick) unchanged — see memory + the 8488ba3 handoff history in git.
