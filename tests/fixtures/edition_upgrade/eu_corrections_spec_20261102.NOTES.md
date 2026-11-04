# eu_corrections_spec_20261102 — notes (annotation only; the spec TSV and its rows freeze are not edited)

The spec TSV is read by `scripts/eu_batch_expand.py` (`csv.DictReader`), so a note line inside it
would be read as a spec row. Notes live here instead (same pattern as `feed_glue_census_20261031.NOTES.md`).

## 2026-11-03 — rows freeze superseded for 21 after-values (DESIGN_q2_build §9.80)
- `eu_batch_rows_20261102.tsv` (sha256 `ac9b9e8c…`) is the record of the 11/2 insert, as inserted. Kept, unchanged.
- `eu_batch_rows_20261103.tsv` (sha256 `38acc6ba…`) supersedes it as the description of the table: identical
  except 21 `verses.text` rows whose `corrected_value` now holds `—` where it held `--` (`source_value` unchanged —
  it must still match B's text, which carries `--` until finish_rebuild step 5).
- Ruling: a correction's after-value is stored in final corpus form (em-dash); the before-value stays as written.
  Without it, step 5 turns these 21 verses' `--` into `—` and cert check 4 reads 21 red rows.
- The 21: 1Ch 21:3, 1Ch 2:7, 2Ch 34:12, 2Ki 14:23, 2Ki 14:28, 2Ki 18:21, 2Ki 24:5, Act 19:38, Dan 12:11, Dan 9:25,
  Deu 32:24, Exo 29:27, Exo 29:38, Exo 6:24, Ezr 7:6, Jdg 20:48, Jer 49:30, Jer 50:29, Jos 13:3, Lev 5:4, Neh 12:35.
- Applied on both copies by the §9.80 block; each copy's EU rows proven equal to the 20261103 file by the block's
  fingerprint (8 table columns, tab-joined, byte-sorted, sha256 `b709436a…`).
- **Done 2026-11-04 02:57 UTC** (`~/edition_upgrade_runs/stageC_s980_20261103.log`): both copies `saved: 21 changed`,
  0 active `--` after-values (all ledgers), EU fingerprint `b709436a…` = this file; `S980 RESULT: APPLIED on both copies`.
