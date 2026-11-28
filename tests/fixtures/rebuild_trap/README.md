# Rebuild-trap fixture folder (CHARTER_rebuild_trap_fix.md G1–G3)

Home of the frozen abp_surface fill:

- `abp_surface_fill_20261127.tsv` — **the pinned file since 2026-11-28** (DESIGN 9.280-9.289): the fill
  re-frozen by the split double rows lane on a whole-file copy written by its program
  (`snapshot_surface_fill.py --prefill <the copy's builder table> --from-restore restore_report_20261127.tsv
  --amend ../surface_amend/abp_surface_amend_split_20261127.tsv`): 3,952 rows (3,412 insert + 539 update +
  1 remove); proven there to give back the written table at every slot. The amendment file is in git
  (`tests/fixtures/surface_amend/`), pinned as `AMEND_SHA256`.
- `abp_surface_fill_20261126.tsv` (the form-cell lane's freeze, 4,418 rows) — superseded 11/28; REMOVED 2026-11-28
  (DESIGN 9.291), locally and on PA, after the 11/27 file's step-1a check read PASS (DESIGN 9.290).
- `abp_surface_fill_20261115.tsv` (the 11/15 freeze, 4,411 rows) and `abp_surface_fill_20261025.tsv` (the
  first freeze): REMOVED 2026-11-26 (DESIGN 9.275), locally and on PA; the 11/26 file replaced them.
- `restore_report_20261127.tsv` — the split copy-proof's dry-run report the 11/27 file was made from (4,419
  lines); the third pinned input of `snapshot_surface_fill.py --check --from-restore` (R1, DESIGN 9.121). The
  pre-fill table it pairs with is `~/abp_surface_prefill_20261127.db` on PA (391,142 rows): step 1a and 9a read it.
- `restore_report_20261115.tsv` (the 11/26 file's report) and `~/abp_surface_prefill_20261115.db` — superseded
  11/28; REMOVED 2026-11-28 (DESIGN 9.291), the report locally and on PA, the pre-fill table on PA. The 11/15
  table's original `~/edition_upgrade_runs/step9a_apply_20261115/before.db` stays (its own item, DESIGN 9.275 (3)).
- Each has a `.sha256` beside it; `scripts/restore_surface_fill.py` pins the snapshot
  (`SNAPSHOT_SHA256`), the report (`REPORT_SHA256`) and the amendment file (`AMEND_SHA256`), and refuses
  any other file.

**All of these files are git-ignored on purpose** — they hold ABP's printed Greek and ABP's English,
and this repo is public (same rule as `abp_helps/` and `abp_app_html/`). PA keeps the working copy
in this folder of `~/bible-db`; a second copy sits in the same folder of the local checkout (scp).
Never delete either while the fill is live: with the pre-fill copy and a copy of live, they are the
only way to re-land the fill after a words rebuild.
