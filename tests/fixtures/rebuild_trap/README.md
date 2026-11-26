# Rebuild-trap fixture folder (CHARTER_rebuild_trap_fix.md G1–G3)

Home of the frozen abp_surface fill:

- `abp_surface_fill_20261126.tsv` — **the pinned file since 2026-11-26** (DESIGN 9.272): the fill
  re-frozen by the form-cell lane from a fresh copy of live after its 10-cell write
  (`snapshot_surface_fill.py --from-restore restore_report_20261115.tsv --amend
  ../surface_amend/abp_surface_amend_20261126.tsv`): 4,418 rows (3,878 insert + 539 update + 1 remove).
  The amendment file is in git (`tests/fixtures/surface_amend/`), pinned as `AMEND_SHA256`.
- `abp_surface_fill_20261115.tsv` (the 11/15 freeze, 4,411 rows) and `abp_surface_fill_20261025.tsv` (the
  first freeze): REMOVED 2026-11-26 (DESIGN 9.275), locally and on PA; the 11/26 file replaced them.
- `restore_report_20261115.tsv` — the 9a apply report that file was made from (4,412 lines); the
  third pinned input of `snapshot_surface_fill.py --check --from-restore` (R1, DESIGN 9.121); still
  the base of the 11/26 freeze. The pre-fill table (~/abp_surface_prefill_20261115.db, on PA) stays: step 1a
  and 9a read it (DESIGN 9.275).
- Each has a `.sha256` beside it; `scripts/restore_surface_fill.py` pins the snapshot
  (`SNAPSHOT_SHA256`), the report (`REPORT_SHA256`) and the amendment file (`AMEND_SHA256`), and refuses
  any other file.

**All of these files are git-ignored on purpose** — they hold ABP's printed Greek and ABP's English,
and this repo is public (same rule as `abp_helps/` and `abp_app_html/`). PA keeps the working copy
in this folder of `~/bible-db`; a second copy sits in the same folder of the local checkout (scp).
Never delete either while the fill is live: with the pre-fill copy and a copy of live, they are the
only way to re-land the fill after a words rebuild.
