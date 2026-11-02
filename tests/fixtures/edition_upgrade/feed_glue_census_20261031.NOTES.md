# feed_glue_census_20261031.tsv — notes (annotation only; the census is NOT re-frozen)

The census file and its `.sha256` are unchanged on purpose: the build checks that hash
(`abp_app_feed.verify_sidecar`), so any edit to the census itself would stop the build, and
re-hashing it would be a re-freeze — ruled against (DESIGN_q2_build.md §9.72, 2026-11-02, JP).

## Glued cells the census missed (found 2026-11-02, P6 preview — feed words absent from the old edition)

| verse | feed cell word | ruled fix |
|---|---|---|
| Jer 14:6 | `drewsniffed` | correction row (EU- batch) |
| 1Ki 7:30 | `fasteningsaxles` | correction row (EU- batch) |
| 1Ki 7:32 | `handsaxles` | correction row (EU- batch) |

All three verses are on the PA eligible list (`eligible_20261031.tsv`), so the transplant takes
their feed English; the fix is the correction batch (§9.72), not the census.
