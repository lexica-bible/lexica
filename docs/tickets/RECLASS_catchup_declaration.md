# 7/30 reclassification catch-up — declaration record (2026-08-01)

The 7/30 Greek-header rebuild rewrote `pn_greek_identity` (five classes, new
'surface' class) but the retirement copy-step never re-ran, so
`retire_hebrew_identity.py`'s declared class counts went stale and step 8b of
`/rebuild-words` halts by design. This session re-declared the counts ONCE,
from live (JP ruling: declare once, from the final shape). All reads below
were run by JP on PA 2026-08-01, read-only, pasted verbatim.

## Check 4 — the oracle gate (run FIRST; reviewer-ruled the go/no-go)

`pn_greek_identity.hebrew_base` vs `pn_hebrew_xref.hebrew_base`, mismatches:

    0

= the identity table is a byte-for-byte carrier of the frozen Hebrew record,
so the rebuild-copy handling (drop the stale xref, rebuild it from the
identity table) is legal. Had this been nonzero, the xref copy would be the
only carrier and nothing could be dropped.

## Check 1 — the class split (this IS the new declaration)

    abp-tag|3518
    lemma-only|12066
    none|2353
    surface|4326
    tipnr|10216

Total 32,479 (unchanged population). Now hard-coded as EXPECT in
`retire_hebrew_identity.py`.

## Check 2 — full matrix (identity class × xref class × words value)

    abp-tag|abp-tag|G|3518
    lemma-only|lemma-only|star|10216
    lemma-only|none|H|1524
    lemma-only|none|star|326
    none|lemma-only|star|1575
    none|none|H|661
    none|none|star|117
    surface|lemma-only|star|3577
    surface|none|H|666
    surface|none|star|83
    tipnr|lemma-only|star|6
    tipnr|none|H|2
    tipnr|none|star|1
    tipnr|tipnr|G|10207

Arithmetic locks to the row: old always-'*' 527 = 326+117+83+1 · old none
3,380 = 1,850+778+749+3 · old lemma-only 14,850 + the 524 G707 ship flips
= 15,374 = 10,216+1,575+3,577+6 · tipnr 10,207 = 10,731−524 · abp-tag 3,518
unchanged.

## Check 3 — the held-out gainers (must be EXACTLY these 9)

    7531|44|G4549|*|saul
    7578|4|G4549|*|saul
    7588|9|G4549|H7586|saul
    7591|1|G4549|H7586|saul
    7703|4|G4549|*|saul
    7729|3|G4549|*|saul
    7804|4|G4549|*|saul
    7954|5|G4549|*|saul
    27434|12|G2197|*|zacharias

No 10th row — the gainer set did not drift since 7/30. They land through the
normal chain at the rebuild (identity class 'tipnr' → retirement writes the
Greek number); nothing special ships for them.

## Follow-up read — the star→H restore count

Of the 1,575 `none|lemma-only|star` rows (classed kept-Hebrew now, but their
Hebrew was moved out at the first retirement):

    has-H|1575

All 1,575 carry a real frozen Hebrew number — at the rebuild they regain it
(fresh import refills it; class 'none' keeps it).

## PRE-REGISTERED serving deltas for the rebuild (vs live today)

- **+9** slots gain a served Greek number (the members above, saul/zacharias).
- **2,190** slots move Hebrew → no-number ('*'): 1,524 now classed lemma-only
  + 666 now classed surface. Hebrew stays reachable via the cross-ref.
- **1,575** slots move no-number → Hebrew (the none-class churn above).
- Everything else byte-identical at the serving column.

## What landed in code (same commit)

- `retire_hebrew_identity.py`: five-class EXPECT (declared above) · typed
  'surface' branch with its own count assertion (declared N / handled N /
  remaining 0 per class) · any class outside the five HALTS (the door
  'surface' walked in through is closed) · `--fresh-rebuild` re-proves the
  check-4 oracle on its own copy, then drops the stale xref at write time
  only. 'surface' rows write xref class 'lemma-only' (G707 ship precedent —
  'surface' is not a cross-ref class).
- `restore_frozen_pn.py` (new, chain step BEFORE the retirement): puts
  import_tipnr's drift back to the frozen record (hand-fix zone; declared
  363 = 357 census + 6 Cushi — a differing dry-run halts for a look).
  **Where the 363 splits:** the 6 are the 2Sa 18 Cushi slots (David's
  runner) — a fresh import writes H3570, the frozen record and the hand fix
  say H3569 (fix_cushi_strongs.py history; also noted in
  G707_diff_report.md). The 357 are the OTHER hand-fix-zone slots the
  G707-session row-by-row mismatch census counted (fresh-import value vs
  frozen record; that census is where "357 hand-fix-zone + Cushi 6" was
  first recorded — memory project_entity_resolution_rebuild). The dry-run
  prints every member, so the 363 is re-derivable at the ride, not taken
  on faith.
- Locks: `tests/test_retire_reclass.py` (5 cases, red-first on the sixth
  class / broken oracle / wrong restore count), in both CI lists;
  `test_retire_builder.py` updated to five-value splits.
- `/rebuild-words` step 8b amended with the new chain order + these deltas.
