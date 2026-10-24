# RECORD — stored Hebrew number vs bound entity: the 2026-10-24 live correction

Apply record. Every figure below is copied from JP-run PA output pasted into the session
on 2026-10-24. It is NOT a reviewer receipt (R2-b); verdicts at each gate were JP's.

## What was wrong
Name slots whose stored Hebrew number (pn_hebrew_xref + its frozen copy
pn_greek_identity.hebrew_base, plus the word itself on kept-Hebrew slots) was not one of
the bound person's/place's own numbers. Found at Gen 25:15 "Hadar" (Χολδάδ, Ishmael's son):
bound to the right man (Hadad@Gen.25.15-1Ch, H2301/H2316; KJV H2316) but stored H1908, the
Edomite Hadad. Source of the wrong numbers: the June TIPNR stopgap (import_tipnr, name-keyed).

## Instruments (all in git)
- `scripts/audit_xref_vs_binding.py` — read-only census + 7 rule-based classes; CONTROL =
  Gen 25:15 + 1Ch 1:30 in class 4. Locked `tests/test_audit_xref_vs_binding.py`.
- `scripts/correct_xref_vs_binding.py` — the correction; shares the census's slot set, KJV
  resolution and classifier. Rules: GUARD (KJV = stored → never changed) → R0 JP per-row
  rulings → R1 remove (no-Hebrew entity) → R2 Esther leave → R3 KJV-backed swap → R4 KJV
  third number → R5/R6/R7. CONTROL = Gen 25:15 → H2316, 1Ch 1:30 → H2301, Zep 1:1 Cushi
  left by the guard. Locked `tests/test_correct_xref_vs_binding.py`.

## Gate sequence (JP-run, read-only unless marked)
1. Census: 27,979 slots with a stored H · 13,838 bound · 13,469 agree · **369 mismatched** ·
   CONTROL OK. Classed: NT 31 · COMPOUND 94 (all split) · SAME-NAME 197 · VARIANT 17 ·
   PRINTED-NAME 24 · OTHER 6; KJV backs the binding on 322.
2. Review of 40 rows against the pinned TIPNR → JP rulings (hard guard; Esther H783 stays;
   compound → KJV's number; NT judged by binding; 22 held rows ruled per row).
3. Dry run 1: SWAP 303 · REMOVE 22 · LEAVE 22 · HOLD 22. Dry run 2 (held rulings in):
   **SWAP 319 · REMOVE 22 · LEAVE 27 · HOLD 1** (Baal 1Ch 5:23), CONTROL OK — matched the
   pre-registration on every figure; JP verdict APPROVED.
4. Rollback copy `~/bible.db.pre-xref-fix-20261024` (PRAGMA quick_check `ok`, 442,597,376
   bytes = live). Test copy apply (scratch write): **APPLIED 341**, every count = plan;
   re-check SWAP 0 · REMOVE 0 · LEAVE 29 · HOLD 1.
5. Binder: dry-run counts differed (floor reasons moved; 3 Michaiah rows bind natively) →
   STOP → row-level check on two scratch copies after a real binder run each
   (control = uncorrected, from the rollback copy): pn_binding 15,446 = 15,446, 0 only-in-
   control, 0 only-in-corrected, **0 entity or render differences**; only the 3 Michaiah rows
   (2Ch 17:7, 2Ki 22:12, Neh 12:41 → Micaiah, same entity) change label `ruled` → `fuzzy`;
   pn_slot_binding 102 = 102, identical.
6. **LIVE APPLY 2026-10-24 22:41:** `cmp` live = rollback copy, then `APPLIED 341 changes in
   one transaction.`, exit 0, CONTROL OK ×3, every after-count = plan. deploy.sh reload 22:42,
   sweep 5×200. Selected after-counts (site's own count, core.h_abp_predicate):

   | number | before → after |
   |---|---|
   | H1908 Hadad | 45 → 18 |
   | H1130 Ben-hadad | 0 → 25 |
   | H2316 / H2301 (Ishmael's son) | 0 → 1 / 0 → 1 |
   | H7927 Shechem (town) | 0 → 64 |
   | H7928 Shechem (man) | 67 → 3 |
   | H7586 Saul | 426 → 404 |
   | H5680 Hebrew | 23 → 30 |
   | H7433 Ramoth-gilead | 0 → 17 |
   | H5654 Obed-edom | 0 → 20 |
   | H7614 Sheba (land) | 0 → 19 |

   Full list: PA `~/xreffix_live_apply.out`; plan `~/xreffix_live/correct_xref_vs_binding_plan.tsv`.

## Open after the apply
- Served check (JP): H1908 18 · H1130 25 · H7927 64 · H7586 404 + Paul in Acts shows no
  H-number · G1056 Galilee still 73.
- Baal 1Ch 5:23 held (Mount Baal-hermon is H1179 — confirm the compound first).
- Next binder run (words rebuild step 3): the 3 Michaiah rows' label `ruled` → `fuzzy`,
  same entity — expected, not a regression.
- Rebuild durability: `/rebuild-words` 8b step 0 (`--rebuild-step`) lands in this commit.
- Disk: rollback copy stays until a nightly backup postdates the apply (single-rollback
  rule); the scratch copies `~/bible_xreffix_test.db` + `~/bible_xreffix_ctrl.db` can go.
- Known, no lane: 14,141 unbound slots aren't checked by the census; the 841 "two numbers
  for one name" rows (Levi/Levite, Judah/Jew …) are left by ruling.
