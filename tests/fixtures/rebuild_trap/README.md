# Rebuild-trap fixture folder (CHARTER_rebuild_trap_fix.md G1–G3)

Home of the frozen abp_surface fill:

- `abp_surface_fill_20261115.tsv` — **the pinned file since 2026-11-15** (DESIGN 9.133): the fill
  re-frozen by the edition upgrade from its copy after step 9a (`scripts/snapshot_surface_fill.py
  --from-restore`, STEP9C-FREEZE): 4,411 rows (3,873 insert + 538 update), one per fill slot at its
  upgraded position.
- `restore_report_20261115.tsv` — the 9a apply report that file was made from (4,412 lines); the
  third pinned input of `snapshot_surface_fill.py --check --from-restore` (R1, DESIGN 9.121).
- `abp_surface_fill_20261025.tsv` — the first freeze (2026-10-25, 4,411 rows at the pre-upgrade
  positions). Kept until the new freeze passes `--check` against the swapped live (charter §7).
- Each has a `.sha256` beside it; `scripts/restore_surface_fill.py` pins the snapshot
  (`SNAPSHOT_SHA256`) and the report (`REPORT_SHA256`) and refuses any other file.

**All of these files are git-ignored on purpose** — they hold ABP's printed Greek and ABP's English,
and this repo is public (same rule as `abp_helps/` and `abp_app_html/`). PA keeps the working copy
in this folder of `~/bible-db`; a second copy sits in the same folder of the local checkout (scp).
Never delete either while the fill is live: with the pre-fill copy and a copy of live, they are the
only way to re-land the fill after a words rebuild.
