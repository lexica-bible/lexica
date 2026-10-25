# Rebuild-trap fixture folder (CHARTER_rebuild_trap_fix.md G1–G3)

Home of the frozen 2026-10-25 abp_surface fill:

- `abp_surface_fill_20261025.tsv` — written by `scripts/snapshot_surface_fill.py` (4,411 rows, one
  per fill slot: the fill write, the old value, the slot's OLD words row, the key-2 ordinal).
- `abp_surface_fill_20261025.tsv.sha256` — its checksum; `scripts/restore_surface_fill.py` refuses
  the file without a matching one (and against the pinned value in its code, once pinned).

**Both files are git-ignored on purpose** — they hold ABP's printed Greek and ABP's English, and
this repo is public (same rule as `abp_helps/` and `abp_app_html/`). PA keeps the working copy in
this folder of `~/bible-db`; a second copy sits in the same folder of the local checkout (scp).
Never delete either while the fill is live: with the pre-fill copy and a copy of live, it is the
only way to re-land the fill after a words rebuild.
