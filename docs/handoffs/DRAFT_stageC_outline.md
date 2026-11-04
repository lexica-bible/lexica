# DRAFT — edition upgrade, stage C outline (the tail on `<built>`) — HELD for the ruling chat

**Status: DRAFT 2026-11-03. Nothing run. No command below is cleared.** Repo confirmed at session
start: HEAD `c3620aa0` (= the stage C handoff's commit), `git diff --quiet 3f6b4d3c HEAD -- scripts tests`
passes. Sources read in full: `HANDOFF_edition_upgrade_stageC.md`, `DESIGN_q2_build.md` §9,
`CHARTER_edition_upgrade.md` §4–§6, `.claude/commands/rebuild-words.md`, `docs/claude/ops.md` deploy +
cert entries, `scripts/finish_rebuild.sh`, `scripts/apply_abp_corrections.py`, `scripts/cert_invariants.py`
(check 4), `scripts/fix_emdash.py`, `scripts/audit_reassembly_diff.py` (arg handling + `run_report_v2`).

Names: `<src>` = `~/bible-db/bible_edupg_test_20261101.db` · `<built>` = `~/bible-db/bible_edupg_test_built_20261102.db`.
Logs: `~/edition_upgrade_runs/stageC_*_<date>.log`, every run tee'd.

---

## Three findings before stage C can run (all from the committed code)

### F1 — 21 EU prose rows will fail cert check 4 after the em-dash step (needs a ruling; blocks C2)
- 21 of the 118 EU `verses.text` rows carry a literal `--` in BOTH `source_value` and `corrected_value`
  (read from `tests/fixtures/edition_upgrade/eu_batch_rows_20261102.tsv`): 2Ki 18:21, Neh 12:35, 2Ki 24:5,
  Jer 49:30, Exo 6:24, 1Ch 2:7, Jos 13:3, Exo 29:27, Jer 50:29, Act 19:38, Lev 5:4, 1Ch 21:3, Exo 29:38,
  Deu 32:24, 2Ki 14:23, 2Ki 14:28, 2Ch 34:12, Dan 9:25, Dan 12:11, Ezr 7:6, Jdg 20:48.
  No EU word row carries `--` (their "before" values were taken after `fix_emdash`, §9.76).
- The chain: finish_rebuild 4b writes `corrected_value` (with `--`) →
  step 5 `fix_emdash.py` does `REPLACE(text,'--','—')` on every verse (`fix_emdash.py:45-46`) →
  cert check 4 compares the cell to `corrected_value` byte for byte (`cert_invariants.py:105-123`, via
  `cellmatch` = plain text equality, `apply_abp_corrections.py:38-47`) → **21 rows read `—`, certified
  value holds `--` → check 4 RED ×21 at gate 1.** Any later re-run of the corrections apply would also
  LOUD-skip these 21 (cell matches neither side).
- No precedent: none of the 13 seeded prose rows in `build_abp_corrections.py` carries `--` or `—`
  (checked), so this is the first time a prose correction meets step 5.
- **Recommendation (option 1):** on `<built>`, before the tail, rewrite those 21 rows'
  `corrected_value` to the em-dash form (`REPLACE(corrected_value,'--','—')`), `source_value`
  untouched (it must still match B's text, which carries `--` until step 5). 4b then writes the final
  text directly, step 5 finds nothing left in those verses, check 4 holds. One gated block: count
  before (expect 21) → UPDATE scoped to `ledger_ref LIKE 'EU-%' AND field='verses.text' AND
  corrected_value LIKE '%--%'` → count after (expect 0 with `--`, 21 with `—`) → every changed row
  printed in full. Correction-table write on the copy = checkpoint. The frozen
  `eu_batch_rows_20261102.tsv` stays the record of the insert as made; a dated NOTES line records the
  21-row amendment (no re-freeze; its `.sha256` is checked by `eu_batch_insert.py`).
- Rejected: (2) accept 21 red rows — forcing; (3) teach check 4 that `--` = `—` — weakens the check
  and would put stale `--` values into the live table at the swap.

### F2 — the §9.61/§9.63 retired-row check has no script (code owed; blocks C5)
`grep` finds no script that reads retired rows against built cells. Proposed:
`scripts/eu_retired_check.py <built>` — read-only (opens `mode=ro`, refuses `~/bible-db/bible.db`).
For each of the 23 retired rows: built cell must equal `corrected_value`; for exactly ids
51 / 25 / 27 / 24 / 45 (2Sa 16:18, 1Ch 22:15, Job 24:19, Mat 21:19, Mar 16:17) the built text may
instead equal B's feed text — **derived by B's own code from the pinned feed** (imported from
`build_prose_from_app.py`, not copied, not retyped from §9.63), then put through the same
`--`→`—` swap step 5 applies. Any failing row prints FULL source / corrected / feed / built text (§9.61
note). Expected: `23 / 23 HOLD (18 = corrected_value · 5 = feed text)`. Count of retired rows ≠ 23 = STOP.
Tests on a synthetic db (pass, each failure shape, the five-id carve-out refusing a sixth id); added to
ci.yml + pre-commit.

### F3 — the v2 punct member diff (§9.52) has no run mode (code owed; blocks C6)
`audit_reassembly_diff.py` takes only `--v2 / --controls / --verse / --list`; nothing reads
`tests/fixtures/reassembly/punct_members_live_20261030.txt` (241 lines, `--list` line format). DESIGN §2
already names it "a new RUN MODE of the existing audit". Proposed: `--v2 --punct-members <frozen>
--eligible <eligible.tsv>` printing: word-order members (all), content-other members (all), punct members
GONE / NEW-on-eligible (listed for ruling) / NEW-on-non-eligible (FAIL) / SAME verse, different ops
(listed). Member = the verse ref; the ops text is shown, not keyed. Exit non-zero on any word-order,
content-other or NEW-on-non-eligible member. Tests + both test lists. The default run is unchanged
(proved by a byte-identical default-path test).

**Landing order for F2 + F3:** one code commit, local tests green, pushed, PA pulled — BEFORE C1. That
commit becomes the code reference for every stage-C gated block (`git diff --quiet <F2F3-commit> HEAD --
scripts tests`). The check-4 re-pin (C3) is a second, later code commit and moves the reference again.

---

## Stage C — step outline (each step its own block, drafted only after the one before it is read)

**C0 (PA, no db write)** — `git pull`; prove the F2/F3 code is in the files (`grep -n` the new function
names; line numbers vs local); `git diff --quiet <F2F3-commit> HEAD -- scripts tests`. `ls -l` both copies
(`<built>` 451,964,928 bytes at stage B close — its time may move only if something wrote it).

**C1 (PA, read-only, then the F1 write if ruled)** — on `<built>`: `abp_corrections` by status (expect
active 372 / retired 23 / superseded 6; EU- 344); the 21 `--` rows listed. Then, only if F1 option 1 is
ruled, the F1 block (chained: the read's exact count line gates the UPDATE).

**C2 (PA, writes `<built>`)** — `bash scripts/finish_rebuild.sh <built> 2>&1 | tee ~/edition_upgrade_runs/stageC_tail_<date>.log | tail -80`.
Gate = the `== finish_rebuild done` line. **The script's verdict does not see patch skips** — none of
`fix_subject_reorder` / `fix_supplied_attach` / `fix_split_merges` exits non-zero on a skip (read), so each
step's own lines are read from the log, and every figure comes back as an old-vs-new one-liner (§9.64 c).
Expected, per step:
| step | expected on `<built>` | source |
|---|---|---|
| 1 import_tipnr | matched: re-declare (31,649 on 10/25); p2 guard fixture check silent, or its findings read | §4.8; roster gate N/A — no change to `import_tipnr.py` / `TIPNR.txt` since 10/24 (git log) |
| fix_subject_reorder | 18 applied · SKIPPED exactly Isa 28:20, Mar 14:44 ("has no bracket") | §9.65 / §9.77 R1 |
| fix_mat25_37 | 1 | — |
| fix_supplied_attach | 4 applied · SKIP exactly Isa 28:20 | §9.77 R1 |
| fix_theos_filler_tags | 2 | — |
| fix_split_merges | patched figure from `eu_rekey_dump_20261102.log` (owed — not in the tree); skips exactly Rom 9:29, Jdg 11:7, 2Ti 4:10. **It prints only 10 skip samples** (`fix_split_merges.py:51`) — skipped > 10 = STOP and list them read-only | §9.66 / §9.72 / §9.77 |
| fix_kyrios_mistags · fix_merge_misses · fix_idios_own · dedup | 3 · 1 · 13 · 0 (re-declare any move) | rebuild-words step 3 |
| fix_bracket_punct | re-declare (~202 on a same-text rebuild) | — |
| 4b prose corrections | `applied 124 · already-applied 0 · LOUD-SKIPPED 0` (118 EU + 6 still-present) | §9.79 |
| 5 fix_emdash | remaining `--`: words 0, verses 0 | — |
| 6 fix_split_flip | re-declare (1 flip / 1 verse pinned since 8/1) | finish_rebuild.sh:77-79 |
| 7 word-cell corrections | `applied 248 · already-applied 0 · LOUD-SKIPPED 0` (22 old + 119 english + 107 english_head); Act 7:3's four apply after R2 | §9.71 / §9.76 |
Any LOUD skip at 4b or 7 = STOP, not skip (§9.8). Words after the tail: 626,309 (626,305 + 4).

**C3 (local + PA pull, no reload) — the §9.59 re-pin.** Read-only dump on PA of `<built>`'s active rows in
the 10/31 member-file format (book, chapter, verse, position, field, ledger_ref; 372 lines) → scp down
(read-only touchpoint) → freeze `tests/fixtures/corrections/abp_corrections_active_built_<date>.txt` +
`.sha256` → `cert_invariants.py` PINS `abp_corrections_active` 51 → 372 (comment names the file) →
scripts-only commit, push, PA pull, **no reload** (§9.64 b). Nothing runs cert_invariants automatically
(grep: no caller), so live is not affected until the swap commit. New code reference = this commit.
`docs/claude/ops.md` cert line updated in the same commit.

**C4 (PA, read-only) — gate 1.** `cert_invariants.py --controls` (all fire) → `cert_invariants.py <built>`
→ **7/7**. Check 1 words 626,309 / verses 31,237; check 4 = 372 HOLD (needs F1 + C3); check 3 em-dash 0.

**C5 (PA, read-only) — §9.61/§9.63 retired-row check.** `eu_retired_check.py <built>` → `23 / 23 HOLD`.

**C6 (PA, read-only) — gate 3.** `python3 -m pytest tests/test_reorder_port.py` green →
`audit_reassembly_diff.py --controls --v2` FIRED → `audit_reassembly_diff.py <built> --v2 --punct-members
tests/fixtures/reassembly/punct_members_live_20261030.txt --eligible ~/edition_upgrade_runs/step5_eligible_20261101.tsv`.
Expected: word-order 0 **with Joh 14:26 absent** (if it is present the lane STOPS, §4.10) · content-other 0 ·
NEW-on-non-eligible 0 · the punct member diff (gone / new-on-eligible / changed ops) **comes to the ruling
chat — STOP here (§9.52)**.

Stage D (8b.0–8b.3, `declared_deltas.json` written before gate 2) starts only after C6 is ruled.

## Owed / open, carried
- `eu_rekey_dump_20261102.log`'s full `fix_split_merges` patched/skipped figure (for the C2 table).
- Split 80 → 84 one-liner (§9.64 c) — still owed to the ruling chat from stage B.
- `declared_deltas.json` + the gate B predicted header member list — stage D, before gate 2.
