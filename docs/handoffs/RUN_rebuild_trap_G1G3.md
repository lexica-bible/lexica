# RUN — rebuild-trap G1–G3 dry run on PA copies (2026-10-26)

Charter: `CHARTER_rebuild_trap_fix.md` §8. **Every command targets an explicit path under `~/rekey/`
(or the pre-fill copy, read only). Nothing writes `~/bible-db/bible.db`.** The only read of live is
block A's copy (`sqlite3 -readonly … .backup`). Run from `~/bible-db`. Stop at the first line that
does not match its expected value and paste that block's output.

Files this run creates: `~/rekey/old3.db` (fresh copy of live, never written after the copy) ·
`~/rekey/built3.db` (the rebuild; every write lands here) · logs + reports in `~/rekey/` · the frozen
snapshot + `.sha256` in `~/bible-db/tests/fixtures/rebuild_trap/` (git-ignored). Disk: about +0.9 GB.

## A — pull, prove, copy
```bash
cd ~/bible-db && git pull && git log --oneline -1 && grep -c "def key2_at" scripts/dryrun_rekey_fill.py && du -sh ~
```
Expect: the new HEAD · `1` · usage **under 8.0G** (stop if not — the run adds ~0.9 GB).
**Disk lesson (2026-10-26):** `du -sh ~` read 8.4G while PA's dashboard read 9.9 of 10 GB — PA meters
~1.5 GB more than `du`. Go by the DASHBOARD figure: it must leave ~1.5 GB free before block C (the
build's copy + its working file), plus room for the nightly backup.
```bash
sqlite3 -readonly ~/bible-db/bible.db ".backup '$HOME/rekey/old3.db'" && sqlite3 -readonly ~/rekey/old3.db "PRAGMA integrity_check; PRAGMA journal_mode; SELECT count(*) FROM abp_surface;"
```
Expect: `ok` · `delete` · `395003`.

## B — snapshot the fill (part a, before step 9)
```bash
PYTHONIOENCODING=utf-8 python3 scripts/snapshot_surface_fill.py --src ~/rekey/old3.db --prefill ~/bible.db.pre-surface-fill-20261025 --csv ~/abp_surface_fill_dryrun.csv --out ~/bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv 2>&1 | tee ~/rekey/snapshot3.log | tail -16
```
Expect: G0 `4,411 / 538` PASS · O PASS · R PASS · RECEIPT rows `4,411 | 4,411` · inserts/updates
`3,873 / 538 | 3,873 / 538` · distinct slots `4,411 | 4,411` · a sha256 line · `RESULT: SNAPSHOT WRITTEN`.
```bash
cd ~/bible-db/tests/fixtures/rebuild_trap && sha256sum -c abp_surface_fill_20261025.tsv.sha256 && wc -l abp_surface_fill_20261025.tsv && cd ~/bible-db
```
Expect: `OK` · `4412` (header + 4,411).

## C — same-code rebuild (copy only)
```bash
echo rebuild | python3 scripts/build_words_from_abp.py ~/rekey/old3.db bh_scrape.db 2>&1 | tee ~/rekey/build3.log | tail -30
```
Expect (checklist pins): `Words inserted: 626,305` · `Verses skipped: 0` · flagged 6,882 ·
`Split 80 merged subject-name(s)` · `PN-star pass: A 1,505 + B 2,552 written · 3,161 refusals`.
```bash
mv ~/rekey/old3.db.new ~/rekey/built3.db && bash scripts/finish_rebuild.sh ~/rekey/built3.db 2>&1 | tee ~/rekey/finish3.log | tail -15
```
Expect: import_tipnr `31,649` matched · `== finish_rebuild done` (no problem list).

## D — 8b chain on built3 (8b.0 → 8b.3, with 8b.2a)
```bash
~/.virtualenvs/bible-env/bin/python scripts/correct_xref_vs_binding.py ~/rekey/built3.db --rebuild-step 2>&1 | tee ~/rekey/8b0_dry3.log | tail -15
```
Expect: CONTROL OK · SWAP 319 · REMOVE 22 · LEAVE 27 · HOLD 1. Then:
```bash
~/.virtualenvs/bible-env/bin/python scripts/correct_xref_vs_binding.py ~/rekey/built3.db --rebuild-step --apply 2>&1 | tee ~/rekey/8b0_apply3.log | tail -8
```
Expect: applied 341.
```bash
python3 scripts/restore_frozen_pn.py ~/rekey/built3.db 2>&1 | tail -8 && python3 scripts/restore_frozen_pn.py ~/rekey/built3.db --apply 2>&1 | tee ~/rekey/8b1_3.log | tail -8
```
Expect: 8 to restore, then restored 8 · 0 left.
```bash
python3 scripts/retire_hebrew_identity.py ~/rekey/built3.db --fresh-rebuild 2>&1 | tail -12 && python3 scripts/retire_hebrew_identity.py ~/rekey/built3.db --fresh-rebuild --apply 2>&1 | tee ~/rekey/8b2_3.log | tail -12
```
Expect: 0 mismatches · split abp-tag 3,671 · tipnr 10,236 · lemma-only 12,182 · surface 4,412 · none
1,977 (32,478) · 26,317 rewrites · GLOB 0.
```bash
python3 scripts/lane3_rebuild_step.py ~/rekey/built3.db 2>&1 | tee ~/rekey/8b2a_3.log | tail -8
```
Expect: `LANE-3 STEP: PASS` with fixes `(9, 0, 0)` · **gapfix `(6, 0, 0)`** (the owed fresh-copy proof of
2Sa 18:31 p7 + 18:32 p15) · fixes2 `(7, 0, 0)`.
```bash
python3 scripts/build_pn_greek_identity.py ~/rekey/built3.db --apply 2>&1 | tee ~/rekey/8b3_id3.log | tail -8 && python3 scripts/build_entity_binding.py ~/rekey/built3.db --apply 2>&1 | tee ~/rekey/8b3_bind3.log | tail -8 && git checkout -- scripts/pn_binding_hot.txt scripts/pn_binding_numonly.txt
```
Expect: identity 32,478 · binding render 15,378 + HOT 68 · slot binds 102 / 0 refused.

## E — step 9 on built3 (needed: without it G1 measures nothing — see charter §8)
```bash
python3 scripts/build_abp_surface.py ~/rekey/built3.db --bh ~/bible-db/bh_scrape.db 2>&1 | tail -4 && python3 scripts/backfill_abp_surface.py ~/rekey/built3.db --bh ~/bible-db/bh_scrape.db --apply 2>&1 | tail -3 && python3 scripts/backfill_pn_surface.py ~/rekey/built3.db --bh ~/bible-db/bh_scrape.db --apply 2>&1 | tail -3 && python3 scripts/build_abp_translit.py ~/rekey/built3.db && sqlite3 -readonly ~/rekey/built3.db "SELECT count(*) FROM abp_surface"
```
Expect last line: **`391130`** (G1a — the builder chain reproduces the base the fill was laid on).

## F — floor control, RED first (G3)
```bash
python3 scripts/health_check.py ~/bible.db.pre-surface-fill-20261025 --no-backup-check --no-disk-check | grep "abp_surface rows"; python3 scripts/health_check.py ~/rekey/built3.db --no-backup-check --no-disk-check | grep "abp_surface rows"
```
Expect both: `[WARN] abp_surface rows BELOW floor 395003 … : 3873`.

## G — restore, read-only first
```bash
PYTHONIOENCODING=utf-8 python3 scripts/restore_surface_fill.py ~/rekey/built3.db --snapshot tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv --lexicon abp_helps/analytical_lexicon.tsv --prefill ~/bible.db.pre-surface-fill-20261025 --report ~/rekey/restore_dry3.tsv 2>&1 | tee ~/rekey/restore_dry3.log | tail -14
```
Expect (SUMMARY, expected | actual): table before `391,130 | 391,130` · vs pre-fill copy `0 / 0 | 0 / 0` ·
placed `4,411 | 4,411` (agree-strong **4,057** · agree-weak **354**) · unplaced `0 | 0` · inserts /
updates `3,873 / 538 | 3,873 / 538` · moved `0` · Lexicon `{'pass': 4022, 'uncovered': 389}` ·
`RESULT: DRY RUN COMPLETE … every gate PASSES`. The 354 agree-weak rows are listed in full in the log.

## H — restore onto the copy (G1)
```bash
PYTHONIOENCODING=utf-8 python3 scripts/restore_surface_fill.py ~/rekey/built3.db --snapshot tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv --lexicon abp_helps/analytical_lexicon.tsv --prefill ~/bible.db.pre-surface-fill-20261025 --report ~/rekey/restore_apply3.tsv --apply 2>&1 | tee ~/rekey/restore_apply3.log | tail -24
```
Expect: `G1 abp_surface = 395,003 rows (expect 395,003 exactly)` PASS · written rows 4,411 differ 0 ·
other rows differ 0 · translit rule would change 0 · quick_check ok · `G1 table after 395,003 | 395,003` ·
`RESULT: RESTORED, ALL CHECKS PASS (on a copy)`.
```bash
sqlite3 -readonly ~/rekey/built3.db "ATTACH '$HOME/rekey/old3.db' AS o; SELECT (SELECT count(*) FROM (SELECT * FROM main.abp_surface EXCEPT SELECT * FROM o.abp_surface)), (SELECT count(*) FROM (SELECT * FROM o.abp_surface EXCEPT SELECT * FROM main.abp_surface));"
```
Expect: `0|0` — the restored table equals live's, row for row (end-to-end oracle; independent of the
restore's own checks).

## I — floor GREEN on the restored copy, re-run reads ALREADY
```bash
python3 scripts/health_check.py ~/rekey/built3.db --no-backup-check --no-disk-check | grep "abp_surface rows"; PYTHONIOENCODING=utf-8 python3 scripts/restore_surface_fill.py ~/rekey/built3.db --snapshot tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv --lexicon abp_helps/analytical_lexicon.tsv --report ~/rekey/restore_again3.tsv 2>&1 | tail -2
```
Expect: `[OK  ] abp_surface rows BELOW floor 395003 … : 0` · `RESULT: ALREADY RESTORED — nothing to write`.

## J — G5 record (not a gate)
```bash
sqlite3 -readonly ~/rekey/built3.db "ATTACH '$HOME/rekey/old3.db' AS o; SELECT 'xref', (SELECT count(*) FROM (SELECT * FROM main.pn_hebrew_xref EXCEPT SELECT * FROM o.pn_hebrew_xref)), (SELECT count(*) FROM (SELECT * FROM o.pn_hebrew_xref EXCEPT SELECT * FROM main.pn_hebrew_xref)); SELECT 'identity', (SELECT count(*) FROM (SELECT * FROM main.pn_greek_identity EXCEPT SELECT * FROM o.pn_greek_identity)), (SELECT count(*) FROM (SELECT * FROM o.pn_greek_identity EXCEPT SELECT * FROM main.pn_greek_identity)); SELECT 'pn strongs_base', count(*) FROM main.words w JOIN o.words x ON x.verse_id=w.verse_id AND x.position=w.position WHERE w.is_pn=1 AND COALESCE(w.strongs_base,'')<>COALESCE(x.strongs_base,'');"
```
Record (G4 figures): `xref|519|519` · `identity|21|21` · `pn strongs_base|501`.

## K — bring the snapshot home (second copy, from Windows PowerShell)
```powershell
scp appssanding720@ssh.pythonanywhere.com:bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv* C:\Users\JP\projects\bible-db\tests\fixtures\rebuild_trap\
```

Paste back: the tails of B, E (last line), F, G, H (+ the `0|0` line), I, J, and the 8b.2a line.
Keep on PA: `old3.db`, `built3.db`, every log. Delete nothing.
