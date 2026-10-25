# RUN — the live words rebuild with the trap fix wired in (Path A, 2026-10-25)

Charter: `CHARTER_rebuild_trap_fix.md` §9. Checklist: `/rebuild-words` (RUN ORDER line). This is a
**same-code rebuild** — every expected figure below comes from the 10/25 copy runs (charter §7 G4
test, §8 G1–G3 receipts). A rebuild that changes code or moves slots (the edition upgrade) needs its
own figures; do not use this sheet for it.

**How this sheet is built:**
- Blocks A–I touch only copies under `~/rekey/` — except three READ-ONLY reads of live (A2 copy-out,
  I pre-swap compare) and nothing else. **The only write to live is block J, the swap.**
- Every command names its file. Live is named **once per block**, in a `LIVE=` line marked `⚠ LIVE`;
  every other path is a copy. (All audit scripts default to plain `bible.db` = live when run from
  `~/bible-db` — so every one below gets the copy path explicitly.)
- **PRE-REG** = figure measured on the 10/25 copy runs. **CHECKLIST** = figure from `/rebuild-words`
  only, never measured by those runs — read line by line, a miss is attributed before going on.
  **FIRST READ** = no figure exists yet; record it.
- Run from `~/bible-db`. Stop at the first line that misses and paste that block.
- **STOP after block I: paste A–I, wait for the verdict. Block J only after it.**

Files this run makes: `~/rekey/pre_rebuild.db` (fresh copy of live; the snapshot check's and the
build's source — never written) · `~/rekey/rebuilt.db` (every write lands here; becomes live at J) ·
logs/reports in `~/rekey/` · at J: `~/bible-db/bible_pre_trapwire_swap.db` (old live, the rollback —
ops.md retention rule 1 naming; the nightly backup skips `bible_pre_*`). Disk: about **+0.9 GB**
until cleanup (a separate step after the receipts — never in a line that names a file still in use).

## A — pull, prove, check inputs and disk
```bash
cd ~/bible-db && git pull && git log --oneline -1 && grep -c "def check_current" scripts/snapshot_surface_fill.py && grep -c "SNAPSHOT_SHA256 = \"d9435bde" scripts/restore_surface_fill.py && ls -l ~/bible.db.pre-surface-fill-20261025 ~/abp_surface_fill_dryrun.csv abp_helps/analytical_lexicon.tsv tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv && (cd tests/fixtures/rebuild_trap && sha256sum -c abp_surface_fill_20261025.tsv.sha256) && ls -lh ~/bible-db/bible_pre_* ~/rekey/*.db 2>&1; du -sh ~
```
Expect: the new HEAD · `1` · `1` · pre-fill copy **442,687,488** bytes · the CSV and the lexicon
present · snapshot **455,812** bytes · `OK` · the `bible_pre_*` / `~/rekey/*.db` listing (record it;
`~/rekey` should hold no `.db` — delete nothing in this run).
**Disk: go by PA's DASHBOARD, not `du`** (it reads ~1.5 GB more). Dashboard must read **≤ 8.0 GB of
10** before A2 (the run adds ~0.9 GB, plus room for the nightly).

## A2 — fresh copy of live (read-only)
```bash
LIVE=~/bible-db/bible.db   # ⚠ LIVE — read only (.backup from a -readonly open)
sqlite3 -readonly "$LIVE" ".backup '$HOME/rekey/pre_rebuild.db'" && sqlite3 -readonly ~/rekey/pre_rebuild.db "PRAGMA integrity_check; PRAGMA journal_mode; SELECT count(*) FROM abp_surface;"
```
Expect (PRE-REG): `ok` · `delete` · `395003`.

## B — step 1a: the snapshot check (writes nothing; `--check` is new — its first PA run)
```bash
PYTHONIOENCODING=utf-8 python3 scripts/snapshot_surface_fill.py --check --src ~/rekey/pre_rebuild.db --prefill ~/bible.db.pre-surface-fill-20261025 --csv ~/abp_surface_fill_dryrun.csv --out tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv 2>&1 | tee ~/rekey/live_1a.log | tail -12
```
Expect (PRE-REG): `PASS — checksum file matches, = the pin` · G0 `old-not-in-prefill 4,411 (expect
4,411) · prefill-not-in-old 538 (expect 538)` then `PASS — 4,411 = 3,873 insert + 538 update = the
approved CSV` · O `PASS — 4,411 slots, each on one word row` · C `PASS — 4,411 rows, identical bytes`
· rows `4,411 | 4,411` · inserts/updates
`3,873 / 538 | 3,873 / 538` · sha256 `d9435bde… | d9435bde…` · **`RESULT: SNAPSHOT CURRENT`**.
`STALE SNAPSHOT` = STOP and paste — something changed live's table or a fill slot's word row since
10/25. Nothing is overwritten; a re-freeze is a ruling.

## C — steps 2 + 3: build and finish (copy only)
```bash
echo rebuild | python3 scripts/build_words_from_abp.py ~/rekey/pre_rebuild.db bh_scrape.db 2>&1 | tee ~/rekey/live_build.log | tail -30
```
Expect (PRE-REG): `Words inserted: 626,305` · `Verses skipped: 0` · flagged 6,882 · `Split 80 merged
subject-name(s)` · `PN-star pass: A 1,505 + B 2,552 written · 3,161 refusals` · the closing text now
says "BEFORE the swap, on THIS COPY …".
```bash
mv ~/rekey/pre_rebuild.db.new ~/rekey/rebuilt.db && bash scripts/finish_rebuild.sh ~/rekey/rebuilt.db 2>&1 | tee ~/rekey/live_finish.log | tail -15
```
Expect (PRE-REG): import_tipnr `31,649` matched · corrections applied 33 / skipped 0 ·
`== finish_rebuild done` (no problem list).

## D — 8b chain on rebuilt.db (8b.0 → 8b.3, with 8b.2a)
```bash
~/.virtualenvs/bible-env/bin/python scripts/correct_xref_vs_binding.py ~/rekey/rebuilt.db --rebuild-step 2>&1 | tee ~/rekey/live_8b0_dry.log | tail -15
```
Expect (PRE-REG): CONTROL OK · SWAP 319 · REMOVE 22 · LEAVE 27 · HOLD 1. Then:
```bash
~/.virtualenvs/bible-env/bin/python scripts/correct_xref_vs_binding.py ~/rekey/rebuilt.db --rebuild-step --apply 2>&1 | tee ~/rekey/live_8b0_apply.log | tail -8
```
Expect: applied 341.
```bash
python3 scripts/restore_frozen_pn.py ~/rekey/rebuilt.db 2>&1 | tail -8 && python3 scripts/restore_frozen_pn.py ~/rekey/rebuilt.db --apply 2>&1 | tee ~/rekey/live_8b1.log | tail -8
```
Expect: 8 to restore, then restored 8 · 0 left.
```bash
python3 scripts/retire_hebrew_identity.py ~/rekey/rebuilt.db --fresh-rebuild 2>&1 | tail -12 && python3 scripts/retire_hebrew_identity.py ~/rekey/rebuilt.db --fresh-rebuild --apply 2>&1 | tee ~/rekey/live_8b2.log | tail -12
```
Expect: 0 mismatches · abp-tag 3,671 · tipnr 10,236 · lemma-only 12,182 · surface 4,412 · none 1,977
(32,478) · 26,317 rewrites · GLOB 0.
```bash
python3 scripts/lane3_rebuild_step.py ~/rekey/rebuilt.db 2>&1 | tee ~/rekey/live_8b2a.log | tail -8
```
Expect: `LANE-3 STEP: PASS` · fixes `(9, 0, 0)` · gapfix `(6, 0, 0)` · fixes2 `(7, 0, 0)`.
```bash
python3 scripts/build_pn_greek_identity.py ~/rekey/rebuilt.db --apply 2>&1 | tee ~/rekey/live_8b3_id.log | tail -8 && python3 scripts/build_entity_binding.py ~/rekey/rebuilt.db --apply 2>&1 | tee ~/rekey/live_8b3_bind.log | tail -8 && git checkout -- scripts/pn_binding_hot.txt scripts/pn_binding_numonly.txt
```
Expect (PRE-REG): identity 32,478 · binding render 15,378 + HOT 68 · slot binds 102 / 0 refused.
```bash
python3 scripts/audit_unfindability.py ~/rekey/pre_rebuild.db ~/rekey/rebuilt.db 2>&1 | tee ~/rekey/live_8b3_unfind.log | tail -12; python3 scripts/audit_two_derivations.py ~/rekey/rebuilt.db 2>&1 | tee ~/rekey/live_8b3_twoder.log | tail -12; PYTHONIOENCODING=utf-8 python3 scripts/gate_greek_header.py ~/rekey/pre_rebuild.db ~/rekey/rebuilt.db 2>&1 | tee ~/rekey/live_8b3_header.log | tail -20
```
Expect: **FIRST READ** — the 8b.3 gates were not part of either 10/25 copy run. Paste the tails;
read GATE C of the header gate (checklist: a pin that used to pass and now FAILS = do not go on).
Nothing moved on this build (re-key: 0 slots moved), so the position-keyed unfindability audit is
valid here (its geometry-aware pre-req applies only to a ride that MOVES name slots).

## E — step 9 on rebuilt.db (the surface rebuild — on the copy, never live)
```bash
python3 scripts/build_abp_surface.py ~/rekey/rebuilt.db --bh ~/bible-db/bh_scrape.db 2>&1 | tail -4 && python3 scripts/backfill_abp_surface.py ~/rekey/rebuilt.db --bh ~/bible-db/bh_scrape.db --apply 2>&1 | tail -3 && python3 scripts/backfill_pn_surface.py ~/rekey/rebuilt.db --bh ~/bible-db/bh_scrape.db --apply 2>&1 | tail -3 && python3 scripts/build_abp_translit.py ~/rekey/rebuilt.db && sqlite3 -readonly ~/rekey/rebuilt.db "SELECT count(*) FROM abp_surface"
```
Expect (PRE-REG): builder `Wrote 346111 rows` · backfill `(delta 13183; …)` · PN backfill
`(delta 31,836; …)` (that script prints commas, the first two do not) · last line **`391130`** (G1a).

## F — step 9b control, RED first (G3)
```bash
python3 scripts/health_check.py ~/bible.db.pre-surface-fill-20261025 --no-backup-check --no-disk-check | grep "abp_surface rows"; python3 scripts/health_check.py ~/rekey/rebuilt.db --no-backup-check --no-disk-check | grep "abp_surface rows"
```
Expect (PRE-REG) both: `[WARN] abp_surface rows BELOW floor 395003 … : 3873`.

## G — step 9a: restore the fill (dry run, then apply — on the copy)
```bash
PYTHONIOENCODING=utf-8 python3 scripts/restore_surface_fill.py ~/rekey/rebuilt.db --snapshot tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv --lexicon abp_helps/analytical_lexicon.tsv --prefill ~/bible.db.pre-surface-fill-20261025 --report ~/rekey/live_restore_dry.tsv 2>&1 | tee ~/rekey/live_restore_dry.log | tail -14
```
Expect (PRE-REG, SUMMARY expected | actual): table before `391,130 | 391,130` · vs pre-fill copy
`0 / 0 | 0 / 0` · placed `4,411 | 4,411` (agree-strong **4,057** · agree-weak **354**) · unplaced
`0 | 0` · inserts / updates `3,873 / 538 | 3,873 / 538` · moved `0` · Lexicon `{'pass': 4022,
'uncovered': 389}` · `RESULT: DRY RUN COMPLETE … every gate PASSES`.
**This is a dry-run → verdict → apply gate.** Paste the tail; apply after the verdict:
```bash
PYTHONIOENCODING=utf-8 python3 scripts/restore_surface_fill.py ~/rekey/rebuilt.db --snapshot tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv --lexicon abp_helps/analytical_lexicon.tsv --prefill ~/bible.db.pre-surface-fill-20261025 --report ~/rekey/live_restore_apply.tsv --apply 2>&1 | tee ~/rekey/live_restore_apply.log | tail -24
```
Expect (PRE-REG): `G1 abp_surface = 395,003 rows (expect 395,003 exactly)` PASS · written rows 4,411
differ 0 · other rows differ 0 · new rows = exactly the insert slots · translit rule would change 0 ·
quick_check ok · `G1 table after 395,003 | 395,003` · `RESULT: RESTORED, ALL CHECKS PASS (on a copy)`.

## H — step 9b GREEN, re-run ALREADY, then steps 5 + 6 (all on the copy)
```bash
python3 scripts/health_check.py ~/rekey/rebuilt.db --no-backup-check --no-disk-check | grep "abp_surface rows"; PYTHONIOENCODING=utf-8 python3 scripts/restore_surface_fill.py ~/rekey/rebuilt.db --snapshot tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv --lexicon abp_helps/analytical_lexicon.tsv --report ~/rekey/live_restore_again.tsv 2>&1 | tail -2; sqlite3 -readonly ~/rekey/rebuilt.db "SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'"
```
Expect (PRE-REG): `[OK  ] abp_surface rows BELOW floor 395003 … : 0` · `RESULT: ALREADY RESTORED —
nothing to write` · step 5 invariant **`0`**.
```bash
python3 scripts/health_check.py ~/rekey/rebuilt.db --no-backup-check --no-disk-check 2>&1 | tee ~/rekey/live_health.log | tail -25
```
Expect: **CHECKLIST** 0 warnings (the full report was never run on a rebuilt copy — any WARN is read
line by line before the swap).
```bash
cd ~/bible-db && R=~/rekey/rebuilt.db; python3 scripts/audit_bracket_order.py $R 2>&1 | tail -6; python3 scripts/scan_strongs_cross.py $R 2>&1 | tail -6; python3 scripts/audit_lord_strongs.py $R 2>&1 | tail -6; python3 scripts/audit_funcword_wrongslot.py $R --preps 2>&1 | tail -6; python3 scripts/scan_content_filler_tags.py $R 2>&1 | tail -6; python3 scripts/audit_split_flip.py $R 2>&1 | tail -4; python3 scripts/audit_corpus_tier1.py $R 2>&1 | tail -8; python3 scripts/audit_corpus_tier2.py $R --rahlfs ~/LXX-Rahlfs-1935 --tagnt ~/TAGNT_*.txt 2>&1 | tail -8
```
Expect (**CHECKLIST**, step 6): bracket CHIP genuine ≈ 2 (Jon 4:9 twin-bracket) · FUNCTION-anchor 0 ·
WRONG-SLOT REPAIRABLE 0 · REPAIRABLE-NOUN ≈ 0 · G2316 0 · **split-flip 0 (MUST)** · A1 ≈ 176 ·
tier 2 ~92%. Paste the tails.

## I — pre-swap compare vs live (read only) — step 4 + the end-to-end oracle + G5 record
```bash
LIVE=~/bible-db/bible.db   # ⚠ LIVE — read only (-readonly open; the copy is attached read-only too)
sqlite3 -readonly "$LIVE" "ATTACH '$HOME/rekey/rebuilt.db' AS b; SELECT 'surface', (SELECT count(*) FROM (SELECT * FROM b.abp_surface EXCEPT SELECT * FROM main.abp_surface)), (SELECT count(*) FROM (SELECT * FROM main.abp_surface EXCEPT SELECT * FROM b.abp_surface)); SELECT 'xref', (SELECT count(*) FROM (SELECT * FROM b.pn_hebrew_xref EXCEPT SELECT * FROM main.pn_hebrew_xref)), (SELECT count(*) FROM (SELECT * FROM main.pn_hebrew_xref EXCEPT SELECT * FROM b.pn_hebrew_xref)); SELECT 'identity', (SELECT count(*) FROM (SELECT * FROM b.pn_greek_identity EXCEPT SELECT * FROM main.pn_greek_identity)), (SELECT count(*) FROM (SELECT * FROM main.pn_greek_identity EXCEPT SELECT * FROM b.pn_greek_identity)); SELECT 'word keys', (SELECT count(*) FROM (SELECT verse_id, position FROM b.words EXCEPT SELECT verse_id, position FROM main.words)), (SELECT count(*) FROM (SELECT verse_id, position FROM main.words EXCEPT SELECT verse_id, position FROM b.words)), (SELECT count(*) FROM b.words), (SELECT count(*) FROM main.words); SELECT 'word cols', sum(COALESCE(w.english,'')<>COALESCE(x.english,'')), sum(COALESCE(w.english_head,'')<>COALESCE(x.english_head,'')), sum(COALESCE(w.greek_pos,'')<>COALESCE(x.greek_pos,'')), sum(COALESCE(w.strongs,'')<>COALESCE(x.strongs,'')), sum(COALESCE(w.is_pn,0)<>COALESCE(x.is_pn,0)), sum(COALESCE(w.bracket_id,'')<>COALESCE(x.bracket_id,'')), sum(COALESCE(w.strongs_base,'')<>COALESCE(x.strongs_base,'')), sum(w.is_pn=1 AND COALESCE(w.strongs_base,'')<>COALESCE(x.strongs_base,'')) FROM b.words w JOIN main.words x ON x.verse_id=w.verse_id AND x.position=w.position; SELECT 'ai cache', (SELECT count(*) FROM (SELECT * FROM main.ai_search_cache EXCEPT SELECT * FROM b.ai_search_cache)), (SELECT count(*) FROM (SELECT key, summary_json FROM main.lsj EXCEPT SELECT key, summary_json FROM b.lsj)), (SELECT count(*) FROM (SELECT strongs, summary_json FROM main.abp_ext EXCEPT SELECT strongs, summary_json FROM b.abp_ext));"
```
Expect, line by line:
- `surface|0|0` — **PRE-REG (the end-to-end oracle):** the restored table = live's, row for row. It
  also proves live's table did not change since A2.
- `xref|519|519` · `identity|21|21` — **PRE-REG, G5 record (not a block):** the 9/6 class basis
  rewrite (charter §7) and the 21-row header table that predates the 10/25 fill (held item 1).
- `word keys|0|0|N|N` — **FIRST READ** for the key half (expected 0|0 on a same-code rebuild; any
  non-zero is read member by member). Counts: CHECKLIST pin 626,309 both sides.
- `word cols|0|0|0|0|0|0|501|501` — english · english_head · greek_pos · strongs · is_pn **0**
  (PRE-REG, G4 §7) · bracket_id **0** (the owed half of held item 3: was 2 at G4 — 2Sa 18:31 p7 +
  18:32 p15 — before gapfix gained them) · strongs_base **501**, all on name slots (PRE-REG, G5).
- `ai cache|0|0|0` — **RECORD, not a block:** AI cache rows written to live since A2. The site writes
  `ai_search_cache` and LSJ/ABP synthesis caches into bible.db (`core.py:341`,
  `views_lsj.py:467-470`); anything here is dropped by the swap and redraws on the next ask (spend).
  If non-zero and you'd rather keep them, say so before J.

**STOP. Paste A–I. Block J waits for the verdict.**

## J — step 8: swap + deploy (the only write to live)
```bash
LIVE=~/bible-db/bible.db   # ⚠ LIVE — swapped here; the old file becomes the rollback
mv "$LIVE" ~/bible-db/bible_pre_trapwire_swap.db && rm -f "$LIVE-wal" "$LIVE-shm" && mv ~/rekey/rebuilt.db "$LIVE" && bash ~/bible-db/scripts/deploy.sh
```
Expect: deploy.sh tests pass · API reload · its 5× sweep clean. Live goes from the old 395,003-row
table to the rebuilt 395,003-row table in one move — no moment without the fill.
**Rollback (one move back):** `mv ~/bible-db/bible.db ~/rekey/rebuilt_rolled_back.db && mv
~/bible-db/bible_pre_trapwire_swap.db ~/bible-db/bible.db && bash ~/bible-db/scripts/deploy.sh`.

## K — after the swap: live reads + step 7 + steps 10/11
```bash
LIVE=~/bible-db/bible.db   # ⚠ LIVE — read only
sqlite3 -readonly "$LIVE" "SELECT count(*) FROM abp_surface; PRAGMA quick_check; PRAGMA journal_mode;" && python3 scripts/health_check.py "$LIVE" --no-backup-check | grep -E "abp_surface rows|disk"
```
Expect: `395003` · `ok` · `delete` · `[OK  ] abp_surface rows BELOW floor 395003 … : 0` · disk line
under the WARN mark.
- Step 7 spot-checks on the served site (after the reload): Eze 31:9 "were jealous of" → ζηλόω ·
  1Chr 1:1 "Adam" → H121, opens metaV · 1Ch 13:10 chip "<verb> · the LORD". Hard-refresh first.
- Steps 10 + 11 per the checklist (unchanged by this lane; step 11 writes live — see the handoff's
  flagged item before running it).

Paste back: A–I (stop), then J + K. Keep on PA: every log, `~/rekey/pre_rebuild.db` until the
receipts are recorded, `bible_pre_trapwire_swap.db` (the rollback — ops.md rule 1), the pre-fill
copy (the snapshot's only "before" side), the snapshot + `.sha256`, `~/abp_surface_fill_dryrun.csv`.
