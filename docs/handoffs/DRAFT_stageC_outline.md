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

---

## 2026-11-03 — pre-flight done; the two PA blocks (HELD — neither is cleared)

F1 → ruled §9.80 · F2 → §9.81, landed · F3 → §9.82, landed. Pre-flight commit **`87b3d44b`** (scripts/tests:
`eu_retired_check.py`, `build_prose_from_app.feed_text`, the v2 member-diff mode, two test files, both test
lists) = the "code unchanged" reference. Labels to grep: **`RETIRED-ROW CHECK:`** · **`V2 MEMBER DIFF:`** ·
**`S980 RESULT:`**.

### Block P1 — PA pull + HEAD confirm + the two owed figures (read-only apart from the pull)
```bash
cd ~/bible-db && git pull && git log -1 --format='PA HEAD %h %s' && git diff --quiet 87b3d44b HEAD -- scripts tests && echo "scripts/tests unchanged since 87b3d44b"
grep -n "patched\|skipped\|skip samples\|verse not found" ~/edition_upgrade_runs/eu_rekey_dump_20261102.log | head -60
grep -Hn "merged subject-name" ~/edition_upgrade_runs/stageB_build_20261102.log ~/bible-db/build_pnstar.log ~/bible-db/build_pnstar2.log
```
Expected: PA HEAD = the docs commit that adds this section (CC posts the hash); "unchanged since 87b3d44b";
the split-merge patched/skipped lines; Split lines reading 84 (stage B) and 80 (both lane-② logs).

### Block S980 — §9.80 on both copies (gated; runs only on clearance, after P1 confirms PA HEAD)
Pre-checks BOTH copies before writing either: status counts 372 / 23 / 6; each copy's EU rows equal
`eu_batch_rows_20261102.tsv` exactly (fingerprint `16f2c6f5…` — a formatting mismatch here is a safe STOP,
nothing written); exactly the 21 ruled refs in scope, printed with ids; no OTHER active row (any ledger) with
`--` in its after-value. Then per copy (src first): rewrite the 21 after-values (`--` → `—`), and BEFORE saving
check — 21 changed · zero active rows with `--` in the after-value across all ledgers (any printed in full) ·
the 21 hold `—` in the after-value AND still `--` in the before-value · every other cell of every row unchanged ·
status counts unchanged · EU rows now equal `eu_batch_rows_20261103.tsv` (fingerprint `b709436a…`). Any miss →
the change is UNDONE, not saved, STOP. Tested locally on throwaway copies built from the frozen file (not
bible.db): applies once; a second run stops at the pre-check; an older row with `--` stops it; a failed
after-check leaves the copy unchanged.
```bash
( set -uo pipefail
REF=87b3d44b
echo "GATE REF ${REF} - S980 block - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "S980 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
PYTHONIOENCODING=utf-8 python3 - ~/bible-db/bible_edupg_test_20261101.db ~/bible-db/bible_edupg_test_built_20261102.db <<'PY'
import hashlib, os, sqlite3, sys
# §9.80: EU prose after-values to final corpus form ('--' -> em dash), on BOTH copies. Before-values untouched.
SRC, BUILT = sys.argv[1], sys.argv[2]
LIVE = os.path.realpath(os.path.expanduser("~/bible-db/bible.db"))
EM = chr(8212)
OLD_FP = "16f2c6f515fbcee6de2fac2ec06acefa787cad9c6afc375499e0ec179b1b96ab"   # = eu_batch_rows_20261102.tsv
NEW_FP = "b709436a40be5ad57574700534495677dc33244fd0bd4f61923c2d4af50e274a"   # = eu_batch_rows_20261103.tsv
WANT = ("1Ch 21:3,1Ch 2:7,2Ch 34:12,2Ki 14:23,2Ki 14:28,2Ki 18:21,2Ki 24:5,Act 19:38,Dan 12:11,Dan 9:25,"
        "Deu 32:24,Exo 29:27,Exo 29:38,Exo 6:24,Ezr 7:6,Jdg 20:48,Jer 49:30,Jer 50:29,Jos 13:3,Lev 5:4,Neh 12:35")
COUNTS = {"active": 372, "retired": 23, "superseded": 6}
SCOPE = "status='active' AND ledger_ref LIKE 'EU-%' AND field='verses.text' AND instr(corrected_value,'--')>0"


class Stop(Exception):
    pass


def fp(con):
    rows = ["\t".join("" if x is None else str(x) for x in r) for r in con.execute(
        "SELECT book,chapter,verse,position,field,source_value,corrected_value,ledger_ref "
        "FROM abp_corrections WHERE ledger_ref LIKE 'EU-%'")]
    rows.sort(key=lambda s: s.encode("utf-8"))
    return hashlib.sha256(("\n".join(rows) + "\n").encode("utf-8")).hexdigest()


def counts(con):
    return dict(con.execute("SELECT status, count(*) FROM abp_corrections GROUP BY status").fetchall())


def rest(con, ids):
    """every column of every row, except the 21 rows' corrected_value"""
    h = hashlib.sha256()
    q = ",".join("?" * len(ids))
    for r in con.execute(f"SELECT id,book,chapter,verse,position,field,source_value,reason,ledger_ref,"
                         f"applied_at,status,created,CASE WHEN id IN ({q}) THEN '<21>' ELSE corrected_value END "
                         f"FROM abp_corrections ORDER BY id", ids):
        h.update(repr(tuple(r)).encode("utf-8"))
    return h.hexdigest()


def dash_rows(con):
    return con.execute("SELECT id, ledger_ref, book||' '||chapter||':'||verse, field, corrected_value "
                       "FROM abp_corrections WHERE status='active' AND instr(corrected_value,'--')>0 "
                       "ORDER BY id").fetchall()


def target(db):
    if not os.path.isfile(db):
        raise Stop(f"not found: {db}")
    if os.path.realpath(db) == LIVE:
        raise Stop(f"refusing the LIVE db {db}")


def pre(db):
    target(db)
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        c = counts(con)
        print(f"  [{db}] status counts {c}")
        if c != COUNTS:
            raise Stop(f"{db}: status counts {c} != {COUNTS}")
        f = fp(con)
        print(f"  [{db}] EU rows fingerprint {f[:12]}... (20261102 file = {OLD_FP[:12]}...)")
        if f != OLD_FP:
            raise Stop(f"{db}: EU rows do not match eu_batch_rows_20261102.tsv")
        rows = con.execute(f"SELECT id, book||' '||chapter||':'||verse FROM abp_corrections WHERE {SCOPE} "
                           "ORDER BY id").fetchall()
        refs = ",".join(sorted((r[1] for r in rows), key=lambda s: s.encode("utf-8")))
        print(f"  [{db}] in scope: {len(rows)}")
        for i, ref in rows:
            print(f"      id {i:>4}  {ref}")
        if len(rows) != 21 or refs != WANT:
            raise Stop(f"{db}: in-scope rows are not exactly the 21 ruled refs (got {len(rows)}: {refs})")
        other = [r for r in dash_rows(con) if r[0] not in {i for i, _ in rows}]
        for r in other:
            print(f"  !! [{db}] active row OUTSIDE the 21 with '--' in its after-value: {r!r}")
        if other:
            raise Stop(f"{db}: {len(other)} other active row(s) carry '--' in the after-value")
        return [i for i, _ in rows]
    finally:
        con.close()


def write(db, ids):
    con = sqlite3.connect(db)
    try:
        con.execute("PRAGMA busy_timeout=5000")
        con.execute("PRAGMA journal_mode=DELETE")
        before_rest, before_counts = rest(con, ids), counts(con)
        q = ",".join("?" * len(ids))
        n = con.execute(f"UPDATE abp_corrections SET corrected_value=replace(corrected_value,'--',?) "
                        f"WHERE id IN ({q}) AND {SCOPE}", [EM] + ids).rowcount
        bad = []
        if n != 21:
            bad.append(f"UPDATE changed {n} rows, expected 21")
        left = dash_rows(con)                                # ALL ledgers, all active rows
        for r in left:
            print(f"  !! [{db}] active row with '--' in after-value after the write: {r!r}")
        if left:
            bad.append(f"{len(left)} active row(s) still carry '--' in the after-value")
        ok21 = con.execute(f"SELECT count(*) FROM abp_corrections WHERE id IN ({q}) AND instr(corrected_value,?)>0 "
                           f"AND instr(source_value,'--')>0", [*ids, EM]).fetchone()[0]
        if ok21 != 21:
            bad.append(f"{ok21} of the 21 have an em-dash after-value AND a '--' before-value")
        if rest(con, ids) != before_rest:
            bad.append("something other than the 21 after-values changed")
        if counts(con) != before_counts:
            bad.append("status counts moved")
        f = fp(con)
        if f != NEW_FP:
            bad.append(f"EU rows fingerprint {f[:12]}... != eu_batch_rows_20261103.tsv {NEW_FP[:12]}...")
        if bad:
            con.rollback()
            raise Stop(f"{db}: NOT saved (undone): " + " | ".join(bad))
        con.commit()
    finally:
        con.close()
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        q = ",".join("?" * len(ids))
        for i, ref, cv in con.execute(f"SELECT id, book||' '||chapter||':'||verse, corrected_value FROM abp_corrections "
                                      f"WHERE id IN ({q}) ORDER BY id", ids):
            print(f"      id {i:>4}  {ref:<11} after-value now: {cv}")
        print(f"  [{db}] saved: 21 changed - active rows with '--' in after-value (all ledgers) "
              f"{len(dash_rows(con))} - EU fingerprint {fp(con)[:12]}... = 20261103 file - counts {counts(con)}")
    finally:
        con.close()


done = []
try:
    print("-- pre-checks (read-only, both copies, before any write) --")
    ids_src, ids_built = pre(SRC), pre(BUILT)
    print("-- write: src --")
    write(SRC, ids_src)
    done.append("src")
    print("-- write: built --")
    write(BUILT, ids_built)
    done.append("built")
    print("S980 RESULT: APPLIED on both copies - 21 + 21 after-values in em-dash form, 0 active '--' after-values")
except Stop as e:
    print(f"S980 RESULT: STOP - {e} - copies saved by this run: {', '.join(done) or 'none'}")
    sys.exit(1)
PY
) 2>&1 | tee ~/edition_upgrade_runs/stageC_s980_20261103.log; echo "exit=${PIPESTATUS[0]}"
```
Expected last line: `S980 RESULT: APPLIED on both copies - 21 + 21 after-values in em-dash form, 0 active '--' after-values`,
then `exit=0`. After it passes: CC commits the 20261103 rows freeze + `.sha256` + the spec NOTES file (see flag 3).

### Owed figures
- **Split 80 → 84** (subject-name split, `build_words_from_abp.py:2737`): old **80** = the 10/25 build and both
  lane-② ride logs (rebuild-words step 2 pin); new **84** = stage B build, 11/2 (`stageB_build_20261102.log`).
  +4. Not attributed by member: the build runs the split with its member list muted (`log=lambda *_a: None`,
  `build_words_from_abp.py:2735`), and both copies are already split, so no dry run can list them now. §4.8
  wants member attribution before the swap — method owed (CC to draft; not blocking the tail).
- **Split-merge patched/skipped** from `eu_rekey_dump_20261102.log`: CC cannot read PA files — block P1 prints it.
  Note: that log is the 11/2 throwaway run of the R2 re-keys (18 patched); it may not carry the full tail figure.

### Flags for the ruling chat
1. **The banked skip list leaves out two skips the record already expects.** `fix_split_merges` Jdg 11:7 —
   "no re-key … the entry skips by itself" (§9.72) — and 2Ti 4:10 — "already skips on a plain rebuild" (§9.66).
   As banked ("expected skips are exactly Isa 28:20, Mar 14:44, Rom 9:29 — any other skip stops the lane") both
   would stop the tail. Amend the list to include them, or confirm the stop. (Isa 28:20 skips in two steps:
   `fix_subject_reorder` and `fix_supplied_attach`.)
2. **Supersession note is a sidecar file**, `eu_corrections_spec_20261102.NOTES.md`, not a line inside the spec
   TSV: `eu_batch_expand.py` reads that TSV with `csv.DictReader`, so a note line would become a bogus spec row.
3. **The re-freeze files sit under `tests/`, so committing them moves the "code unchanged" reference.** Proposed:
   commit them only AFTER block S980 passes (the block proves each table equals the file); that commit becomes
   the tail block's reference, and `git diff --stat 87b3d44b <it>` = exactly those three fixture files (shown in
   the tail block). Until then they stay local and uncommitted.
4. **S980 undoes its own change if any after-check fails** (all checks run before the change is saved) — one
   step beyond the ruling's "assert after the write".

### P1 result (PA, 2026-11-04 02:41) + the two owed figures
- PA HEAD `19501224`, scripts/tests unchanged since `87b3d44b`.
- **Split 80 → 84:** stage B build log line 36 reads `Split 84`; `build_pnstar.log` + `build_pnstar2.log` line 34 read `Split 80`. +4, members not yet attributed (method owed before the swap).
- **Split-merge:** `eu_rekey_dump_20261102.log` has no patched/skipped line — by design: that script only DUMPS rows; the §9.77 "18 patched" came from running the real patch on a throwaway db of those rows. The prediction is in PA's own pre-A check (`preA_check_20261101.log`, local copy `~/edition_upgrade_runs/pa/`): `fix_split_merges: 237 verses, 218 eligible, 22 eligible verses differ at a watched cell` = the 18 re-keyed + Jdg 11:7 + Rom 9:29 + 2Ti 4:10 + Act 2:38 (applies — only its bracket number differs). **Predicted tail: 234 patched · 3 skipped (Jdg 11:7, Rom 9:29, 2Ti 4:10).** Gap checked: the merge-pair / edge-split code landed after the pre-A check; 9 merge-pair verses and 1 edge-split verse are split-merge entries — Neh 5:12 + Eze 20:14 are re-keyed on rows that include that code (§9.77); the other 8 (2Ki 10:19, Eze 34:4, Jdg 14:16, Job 10:18, Job 13:20, Job 19:22, Luk 10:42, Mat 15:32) were not flagged at any watched cell on pre-A and the merge-pair rule only restores OLD English, so they are predicted to apply. A prediction, not a reading — the tail's own line is the figure.
- This confirms flag 1: the tail is predicted to skip Jdg 11:7 and 2Ti 4:10, which the banked list does not name.

---

## 2026-11-04 — S980 passed; post-S980 commit `61484fbc`; the TAIL block (HELD — not cleared)

S980: both copies `saved: 21 changed`, 0 active `--` after-values, EU fingerprint `b709436a…` = the 20261103 file;
`S980 RESULT: APPLIED on both copies`, exit 0 (full record DESIGN §9.83 note). Post-S980 commit `61484fbc` (+ `a1d466c9`):
`git diff --stat 87b3d44b 61484fbc -- scripts tests` = exactly the three fixture files (`eu_batch_rows_20261103.tsv`,
its `.sha256`, `eu_corrections_spec_20261102.NOTES.md`). Stored-file checksums: 20261103 = `38acc6ba…`, 20261102 = `ac9b9e8c…` (unchanged).

### Block TAIL — finish_rebuild on `<built>` (GATE REF `61484fbc`)
Stops before running anything if: code differs from the reference · the copy is missing or is live · `import_tipnr.py` /
`TIPNR.txt` changed since 10/24 (roster gate) · the copy is not pre-tail (words must read 626,305, active corrections 372).
```bash
( set -uo pipefail
REF=61484fbc
echo "GATE REF ${REF} - TAIL block - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "TAIL RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
[ -f "$B" ] || { echo "TAIL RESULT: STOP - built copy missing: $B"; exit 1; }
[ "$(realpath "$B")" != "$(realpath ~/bible-db/bible.db)" ] || { echo "TAIL RESULT: STOP - that is the LIVE db"; exit 1; }
T=$(git log --since=2026-10-24 --oneline -- scripts/import_tipnr.py tipnr/TIPNR.txt)
[ -z "$T" ] || { echo "TAIL RESULT: STOP - import_tipnr.py / TIPNR.txt changed since 10/24 (roster regression gate owed): $T"; exit 1; }
W=$(sqlite3 -readonly "$B" "SELECT count(*) FROM words")
A=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_corrections WHERE status='active'")
echo "before tail: words ${W} (expect 626305 = raw build, tail not yet run) - active corrections ${A} (expect 372)"
[ "$W" = 626305 ] && [ "$A" = 372 ] || { echo "TAIL RESULT: STOP - the copy is not in its post-S980 pre-tail state"; exit 1; }
ls -l "$B"
bash scripts/finish_rebuild.sh "$B"; rc=$?
echo "finish_rebuild exit=${rc}"
echo "after tail: words $(sqlite3 -readonly "$B" "SELECT count(*) FROM words") (expect 626309) - '--' left: words $(sqlite3 -readonly "$B" "SELECT count(*) FROM words WHERE english LIKE '%--%'") / verses $(sqlite3 -readonly "$B" "SELECT count(*) FROM verses WHERE text LIKE '%--%'") (expect 0 / 0)"
echo "TAIL RESULT: RAN - finish_rebuild exit ${rc} - clearance reads each step's own lines, not the done line"
exit $rc
) 2>&1 | tee ~/edition_upgrade_runs/stageC_tail_20261104.log | tail -80; echo "exit=${PIPESTATUS[0]}"
```

### Read-back (read-only) — each step's own lines, new tail vs the 10/25-equivalent tail log
`finish_pnstar2.log` matches the 10/25 chain line for line (rebuild-words step 3), so it gives the "old" side of every one-liner.
```bash
for L in ~/edition_upgrade_runs/stageC_tail_20261104.log ~/bible-db/finish_pnstar2.log; do echo "######## $L"; grep -n "^GATE REF\|^before tail\|^after tail\|TAIL RESULT\|^== \|^── \|Matched  :\|Unmatched:\|still strongs_base\|FIXTURE\|DRIFT\|pplied\|APPLYING\|SKIP\|skip\|patched\|summary:\|LOUD\|words to edit\|rows to delete\|flips to repair\|Remaining\|with '--'\|Nothing to do\|Saved\|!!\|DO NOT SWAP\|finish_rebuild" "$L" | grep -v "^[0-9]*:── Sample\|^[0-9]*:  -> \|^[0-9]*:  == "; done
```

### Expected (the tail's own lines are the authority; §9.83)
| step | expected |
|---|---|
| import_tipnr | Matched: re-declare vs 31,649; fixture drift check silent, or its findings read |
| fix_subject_reorder | `applied 18 verse fixes.` · SKIPPED exactly Isa 28:20, Mar 14:44 |
| fix_mat25_37 | applied |
| fix_supplied_attach | `applied 4 verse fixes.` · SKIP exactly Isa 28:20 |
| fix_theos_filler_tags · fix_kyrios_mistags · fix_merge_misses · fix_idios_own · dedup_words · fix_bracket_punct | same as the 10/25 log, or re-declared one-liner |
| fix_split_merges | **`234 verse(s) patched, 3 skipped`**, skip samples exactly Jdg 11:7, Rom 9:29, 2Ti 4:10 — any other figure = STOP for review |
| 4b prose corrections | `applied 124 · already-applied 0 · LOUD-SKIPPED 0` |
| fix_emdash | remaining 0 / 0 |
| fix_split_flip | re-declare vs 10/25 (1 flip / 1 verse pinned since 8/1) |
| 7 word corrections | `applied 248 · already-applied 0 · LOUD-SKIPPED 0` |
| end | `== finish_rebuild done` (not evidence alone) · words 626,309 · `--` 0 / 0 |

### Flag 5 — doubled words new in the app edition's prose (found reading the S980 output; local census, not PA)
2Ki 14:28 now reads "Hamath belonging to to Judah": the feed has "belonging to" on G3588 and "to Judah," on the name
(old edition: "Hamath to Judah"). Not caused by S980. Census of B's feed text on the 29,071 PA-eligible verses, doubled
words absent from the old prose: **25 spots / 25 verses.** Most read as deliberate repeats (Samuel, Samuel · O, O ·
behold, behold · Absalom, Absalom · Lord, Lord · you; you …); "be be" ×2 is already in the batch. **Nine look like slips
(no punctuation between):** 2Ki 14:28 "to to" · Deu 24:8 "you you" · Eze 11:12 "you you" · Jdg 20:34 "they they" ·
Ezr 4:15 "this this" · Est 8:8 "with with" · Joe 2:2 "it it" · Luk 13:28 "there there" · Joh 19:21 "that that"
(not each read against the Greek yet — some may be grammatical). §9.72 put real-word typos out of this lane; if any are
to be fixed in this lane, the rows must be inserted BEFORE the tail (they change the 372 and the re-pin).

---

## 2026-11-04 — tail run 1 STOPPED at its own pre-check (nothing ran); TAIL v2 (HELD for re-clearance)

Run 1: `before tail: words 626309 (expect 626305 …)` → `TAIL RESULT: STOP`. The copy is right, the check was wrong: the build's
own blank-number fill adds 4 rows after the `Words inserted: 626,305` line (DESIGN §9.84 note), so a finished build reads
626,309 and the tail adds none. v2 changes ONLY the pre-tail check (words 626,309, plus three signs the tail has not run:
active prose rows still at their before-text 124 · verses with `--` > 0 · no `<built>.corrections.log`) and the after-tail
words note, and writes a new log name (`stageC_tail2_…`) so run 1's log stays. Paste one block at a time (run 1's read-back
failed because two blocks landed on one line).

### Block TAIL v2 (GATE REF `61484fbc`)
```bash
( set -uo pipefail
REF=61484fbc
echo "GATE REF ${REF} - TAIL block v2 - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "TAIL RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
[ -f "$B" ] || { echo "TAIL RESULT: STOP - built copy missing: $B"; exit 1; }
[ "$(realpath "$B")" != "$(realpath ~/bible-db/bible.db)" ] || { echo "TAIL RESULT: STOP - that is the LIVE db"; exit 1; }
T=$(git log --since=2026-10-24 --oneline -- scripts/import_tipnr.py tipnr/TIPNR.txt)
[ -z "$T" ] || { echo "TAIL RESULT: STOP - import_tipnr.py / TIPNR.txt changed since 10/24 (roster regression gate owed): $T"; exit 1; }
W=$(sqlite3 -readonly "$B" "SELECT count(*) FROM words")
A=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_corrections WHERE status='active'")
P=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_corrections c JOIN verses v ON v.book=c.book AND v.chapter=c.chapter AND v.verse=c.verse WHERE c.status='active' AND c.field='verses.text' AND v.text=c.source_value")
D=$(sqlite3 -readonly "$B" "SELECT count(*) FROM verses WHERE text LIKE '%--%'")
if [ -e "$B.corrections.log" ]; then L=PRESENT; else L=none; fi
echo "before tail: words ${W} (expect 626309 = 626,305 inserted + the build's own 4 blank-number splits) - active corrections ${A} (expect 372) - prose rows still at their before-text ${P} (expect 124) - verses with '--' ${D} (expect more than 0) - corrections log ${L} (expect none)"
[ "$W" = 626309 ] && [ "$A" = 372 ] && [ "$P" = 124 ] && [ "$D" -gt 0 ] && [ "$L" = none ] || { echo "TAIL RESULT: STOP - the copy is not in its post-S980 pre-tail state"; exit 1; }
ls -l "$B"
bash scripts/finish_rebuild.sh "$B"; rc=$?
echo "finish_rebuild exit=${rc}"
echo "after tail: words $(sqlite3 -readonly "$B" "SELECT count(*) FROM words") (expect 626309 - no tail step adds words) - '--' left: words $(sqlite3 -readonly "$B" "SELECT count(*) FROM words WHERE english LIKE '%--%'") / verses $(sqlite3 -readonly "$B" "SELECT count(*) FROM verses WHERE text LIKE '%--%'") (expect 0 / 0)"
echo "TAIL RESULT: RAN - finish_rebuild exit ${rc} - clearance reads each step's own lines, not the done line"
exit $rc
) 2>&1 | tee ~/edition_upgrade_runs/stageC_tail2_20261104.log | tail -80; echo "exit=${PIPESTATUS[0]}"
```

### Read-back v2 (read-only)
```bash
for L in ~/edition_upgrade_runs/stageC_tail2_20261104.log ~/bible-db/finish_pnstar2.log; do echo "######## $L"; grep -n "^GATE REF\|^before tail\|^after tail\|TAIL RESULT\|^== \|^── \|Matched  :\|Unmatched:\|still strongs_base\|FIXTURE\|DRIFT\|pplied\|APPLYING\|SKIP\|skip\|patched\|summary:\|LOUD\|words to edit\|rows to delete\|flips to repair\|Remaining\|with '--'\|Nothing to do\|Saved\|!!\|DO NOT SWAP\|finish_rebuild" "$L" | grep -v "^[0-9]*:── Sample\|^[0-9]*:  -> \|^[0-9]*:  == "; done
```
Expected: as the table above (§9.83), with words 626,309 before AND after.

---

## 2026-11-04 — tail run 2 (v2) STOPPED at its pre-check (nothing ran); TAIL v3 (HELD for re-clearance)

v2 read `prose rows still at their before-text 118 (expect 124)`. The 6 old prose rows are on the 6 carve-out verses, which keep
live's already-corrected prose, so they read their AFTER-text; only the 118 EU rows are at before-text. **4b's expected line is
therefore `applied 118 · already-applied 6 · LOUD-SKIPPED 0`** (replaces "applied 124" in the expected table above). The
read-back's `!!` (inside double quotes) was replaced by bash with the previous command — the pattern is now single-quoted.
v3 = v2 with the prose check split in two (EU at before-text 118; the old 6 at after-text, named) plus an after-tail count of
all 124 prose rows at their after-text; new log name `stageC_tail3_…`.

### Block TAIL v3 (GATE REF `61484fbc`)
```bash
( set -uo pipefail
REF=61484fbc
echo "GATE REF ${REF} - TAIL block v3 - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "TAIL RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
[ -f "$B" ] || { echo "TAIL RESULT: STOP - built copy missing: $B"; exit 1; }
[ "$(realpath "$B")" != "$(realpath ~/bible-db/bible.db)" ] || { echo "TAIL RESULT: STOP - that is the LIVE db"; exit 1; }
T=$(git log --since=2026-10-24 --oneline -- scripts/import_tipnr.py tipnr/TIPNR.txt)
[ -z "$T" ] || { echo "TAIL RESULT: STOP - import_tipnr.py / TIPNR.txt changed since 10/24 (roster regression gate owed): $T"; exit 1; }
J="FROM abp_corrections c JOIN verses v ON v.book=c.book AND v.chapter=c.chapter AND v.verse=c.verse WHERE c.status='active' AND c.field='verses.text'"
W=$(sqlite3 -readonly "$B" "SELECT count(*) FROM words")
A=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_corrections WHERE status='active'")
PE=$(sqlite3 -readonly "$B" "SELECT count(*) $J AND c.ledger_ref LIKE 'EU-%' AND v.text=c.source_value")
PO=$(sqlite3 -readonly "$B" "SELECT c.book||' '||c.chapter||':'||c.verse $J AND c.ledger_ref NOT LIKE 'EU-%' AND v.text=c.corrected_value ORDER BY 1" | paste -sd,)
PN=$(sqlite3 -readonly "$B" "SELECT count(*) $J")
D=$(sqlite3 -readonly "$B" "SELECT count(*) FROM verses WHERE text LIKE '%--%'")
if [ -e "$B.corrections.log" ]; then L=PRESENT; else L=none; fi
echo "before tail: words ${W} (expect 626309) - active corrections ${A} (expect 372) - active prose rows ${PN} (expect 124)"
echo "before tail: EU prose rows at their before-text ${PE} (expect 118) - old prose rows already at their after-text: ${PO} (expect 1Sa 9:3,2Ch 10:13,Jer 3:7,Jer 9:23,Neh 12:43,Rev 11:1 - the 6 carve-out verses keep live's corrected prose)"
echo "before tail: verses with '--' ${D} (expect more than 0) - corrections log ${L} (expect none)"
[ "$W" = 626309 ] && [ "$A" = 372 ] && [ "$PN" = 124 ] && [ "$PE" = 118 ] && [ "$PO" = "1Sa 9:3,2Ch 10:13,Jer 3:7,Jer 9:23,Neh 12:43,Rev 11:1" ] && [ "$D" -gt 0 ] && [ "$L" = none ] || { echo "TAIL RESULT: STOP - the copy is not in its post-S980 pre-tail state"; exit 1; }
ls -l "$B"
bash scripts/finish_rebuild.sh "$B"; rc=$?
echo "finish_rebuild exit=${rc}"
echo "after tail: words $(sqlite3 -readonly "$B" "SELECT count(*) FROM words") (expect 626309) - active prose rows at their after-text $(sqlite3 -readonly "$B" "SELECT count(*) $J AND v.text=c.corrected_value") (expect 124) - '--' left: words $(sqlite3 -readonly "$B" "SELECT count(*) FROM words WHERE english LIKE '%--%'") / verses $(sqlite3 -readonly "$B" "SELECT count(*) FROM verses WHERE text LIKE '%--%'") (expect 0 / 0)"
echo "TAIL RESULT: RAN - finish_rebuild exit ${rc} - clearance reads each step's own lines, not the done line"
exit $rc
) 2>&1 | tee ~/edition_upgrade_runs/stageC_tail3_20261104.log | tail -80; echo "exit=${PIPESTATUS[0]}"
```

### Read-back v3 (read-only; single-quoted pattern)
```bash
for L in ~/edition_upgrade_runs/stageC_tail3_20261104.log ~/bible-db/finish_pnstar2.log; do echo "######## $L"; grep -n '^GATE REF\|^before tail\|^after tail\|TAIL RESULT\|^== \|^── \|Matched  :\|Unmatched:\|still strongs_base\|FIXTURE\|DRIFT\|pplied\|APPLYING\|SKIP\|skip\|patched\|summary:\|LOUD\|words to edit\|rows to delete\|flips to repair\|Remaining\|with .--.\|Nothing to do\|Saved\|!!\|DO NOT SWAP\|finish_rebuild' "$L" | grep -v '^[0-9]*:── Sample\|^[0-9]*:  -> \|^[0-9]*:  == '; done
```
Expected: split-merge `234 verse(s) patched, 3 skipped` (Jdg 11:7, Rom 9:29, 2Ti 4:10) · subject-reorder skips Isa 28:20 + Mar 14:44 ·
supplied-attach skips Isa 28:20 · 4b `applied 118 · already-applied 6 · LOUD-SKIPPED 0` · step 7 `applied 248 · already-applied 0 ·
LOUD-SKIPPED 0` · finish_rebuild exit 0 · words 626,309 · prose at after-text 124 · `--` 0 / 0.

## 2026-11-04 — tail v3 read-back: CHECK 1 + CHECK 2 (read-only; HELD for clearance)
Ruling chat: tail v3 result HELD pending two read-only checks; §9.83 amended (JP) — expected skip set = the 10/25
standing set (split-merge 29, subject-reorder 13, supplied-attach 5, by name) + exactly Jdg 11:7 and Rom 9:29 as new
split-merge skips; 206/31 accepted only if the 31 = the 10/25 29 + those two; the 234/3 forecast withdrawn.
Both scripts are one-offs written under `~/edition_upgrade_runs/` by the block itself (not `scripts/` — the code
reference stays `61484fbc`); each block checks the pasted script's sha256 before running it.

**Method notes (why not the plain re-run the ruling describes):**
- CHECK 1: the step already ran on both copies, so a PATCHED verse no longer holds its before-English and fails the
  step's own test too. Each verse is read two ways: patch result present at every `new_pos` (punctuation / `--`
  normalised — fix_bracket_punct and fix_emdash run after) → patched; otherwise the step's own test (same queries,
  order and reason text as `fix_split_merges.py:46-71`) gives the skip reason; the step's test passing now = would
  patch today = stop. Live (the 10/25 output) gives the 29. Cross-checks: counts = each log's own line; each log's 10
  printed samples must be in its list. Blind spot: a skip whose cells already equal the patch result reads as patched
  — the count check catches it. Checked: no lane-3 verse and no EU word correction touches a split-merge verse.
- CHECK 2: live's numbers are post-8b (8b re-numbers thousands of name cells), so they don't show what the import
  decided. Per side: take the cells the import saw (`is_pn = 1` — import_tipnr is the only writer), put back their
  import-time English (undo lane-3 8b.2a on live only, then step-7 word corrections, then the em dash), set them `*`,
  run the real `import_tipnr.py` on a throwaway copy. Proof: built has no 8b, so its stored result must equal the re-run
  cell for cell; each re-run's Matched/Unmatched must equal its own log. Then pair matched cells per verse; lost/gained
  get a class (EDITION-TEXT / TOKEN-SPLIT / OTHER); any OTHER stops.

Tested locally on synthetic databases (not bible.db): pass case; extra skip, eligible-now, missing sample (check 1);
OTHER cell, wrong log figure, built proof broken (check 2) — each stops. Reason text matched the real
`fix_split_merges.py` dry-run on 4 reason kinds. Both whole blocks ran end to end in a fake home (heredoc → sha → run → tee).

### Block CHECK 1 (GATE REF `61484fbc`, read-only)
```bash
set +H
( set -uo pipefail
REF=61484fbc
echo "GATE REF ${REF} - CHECK 1 split-merge skips (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "CHECK1 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; L=~/bible-db/bible.db
N=~/edition_upgrade_runs/stageC_tail3_20261104.log; O=~/bible-db/finish_pnstar2.log
for f in "$B" "$L" "$N" "$O"; do [ -f "$f" ] || { echo "CHECK1 RESULT: STOP - missing: $f"; exit 1; }; done
P=~/edition_upgrade_runs/check1_split_skips_20261104.py
cat > "$P" <<'PY'
"""CHECK 1 (one-off, read-only): name every fix_split_merges skip on the built copy (tail v3, 11/4)
and on live (the 10/25 run), and diff the two sets.

Both databases are opened read-only. Nothing is written anywhere.

Why not just re-run the step's test: the step already ran on both copies, so a PATCHED verse no
longer holds its "before" English and fails the step's own test too. So each verse is read two
ways and the logs check the result:
  1. patch result present  - every entry's new_pos cell holds new_eng (punctuation and '--'/em dash
                             normalised, since fix_bracket_punct and fix_emdash run after the patch)
                             -> PATCHED
  2. otherwise             - the step's own test (fix_split_merges.py lines 46-71, same queries, same
                             order, same reason text) gives the skip reason -> SKIPPED
  3. the step's test passes now -> ELIGIBLE-NOW (should be 0: the step would patch it today)
Cross-checks: the counts must equal the step's own log line, and each log's 10 printed skip
samples must be in the list.

Usage: python3 check1_split_skips_20261104.py <built.db> <live.db> <tail3.log> <finish_pnstar2.log>
"""
import hashlib
import json
import os
import re
import sqlite3
import sys

BUILT, LIVE, LOG_NEW, LOG_OLD = sys.argv[1:5]
FIXES_PATH = os.path.join(os.environ.get("CHECK_REPO") or os.path.expanduser("~/bible-db"),
                          "scripts", "split_merge_fixes.json")
FIXES_SHA = "eab8e565cd1dd34231254088091ffb13b93e8ec52cdbb53a8b622a1148dcc8c5"   # = 61484fbc
EXPECT_NEW_ONLY = {"Jdg 11:7", "Rom 9:29"}    # ruling: the 10/25 29 + these two, nothing lost
EXPECT_OLD_ONLY = set()
EM = chr(8212)
PUNCT = ".,;:?" + chr(33) + chr(183) + ")"      # chr(33) = exclamation mark (kept out of the paste)
EDGE = re.compile("^[(]+|[" + re.escape(PUNCT) + "]+$")

raw = open(FIXES_PATH, "rb").read()
FIXES = json.loads(raw.decode("utf-8"))
stops = []


def norm(s):
    s = (s or "").replace("--", EM).strip()
    prev = None
    while prev != s:
        prev = s
        s = EDGE.sub("", s).strip()
    return " ".join(s.split())


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


def step_test(conn, verse, ops):
    """fix_split_merges.py's own guard, verbatim in effect. None = would patch now."""
    book, rest = verse.rsplit(" ", 1)
    ch, vs = rest.split(":")
    r = conn.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                     (book, int(ch), int(vs))).fetchone()
    if r is None:
        return None, "verse not found"
    vid = r[0]
    for op in ops:
        row = conn.execute(
            "SELECT id, english, strongs_base FROM words WHERE verse_id=? AND position=?",
            (vid, op["old_pos"])).fetchone()
        if row is None:
            return vid, "no row at pos %s" % op["old_pos"]
        if row[2] != "G" + op["sbase"]:
            return vid, "strongs mismatch pos %s (%s != G%s)" % (op["old_pos"], row[2], op["sbase"])
        if (row[1] or "") != (op["old_eng"] or ""):
            return vid, "english mismatch pos %s (%s)" % (op["old_pos"], repr(row[1]))
    return vid, None


def result_present(conn, vid, ops):
    """(loose, strict, head) - does every new_pos cell hold the patch's result?"""
    loose = strict = head = True
    for op in ops:
        rows = conn.execute(
            "SELECT english, english_head, strongs_base FROM words WHERE verse_id=? AND position=?",
            (vid, op["new_pos"])).fetchall()
        pick = [r for r in rows if r[2] == "G" + op["sbase"]] or rows
        if not pick:
            return False, False, False
        e, h = pick[0][0] or "", pick[0][1] or ""
        strict &= e == (op["new_eng"] or "")
        loose &= norm(e) == norm(op["new_eng"])
        head &= h == (op["new_head"] or "")
    return loose, strict, head


def classify(path):
    conn = ro(path)
    out = {"PATCHED": [], "SKIPPED": {}, "ELIGIBLE-NOW": [], "loose_only": [], "head_differs": []}
    for verse, ops in FIXES.items():
        vid, reason = step_test(conn, verse, ops)
        if vid is not None and reason is None:
            out["ELIGIBLE-NOW"].append(verse)
            continue
        if vid is not None:
            loose, strict, head = result_present(conn, vid, ops)
            if loose:
                out["PATCHED"].append(verse)
                if not strict:
                    out["loose_only"].append(verse)
                if not head:
                    out["head_differs"].append(verse)
                continue
        out["SKIPPED"][verse] = reason
    conn.close()
    return out


SAMPLE = re.compile(r"^\s{3}(\S+ \d+:\d+): (.*)$")
COUNT = re.compile(r"(\d+) verse\(s\) patched, (\d+) skipped")


def read_log(path):
    """The step's own count line and its printed skip samples, from a finish_rebuild log."""
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    starts = [i for i, l in enumerate(lines) if "fix_split_merges.py" in l]
    if not starts:
        return None, None, []
    i = starts[0]
    patched = skipped = None
    samples = []
    j = i + 1
    while j < len(lines) and "fix_kyrios_mistags" not in lines[j]:
        m = COUNT.search(lines[j])
        if m and patched is None:
            patched, skipped = int(m.group(1)), int(m.group(2))
        if "skip samples" in lines[j]:
            k = j + 1
            while k < len(lines):
                s = SAMPLE.match(lines[k])
                if not s:
                    break
                samples.append((s.group(1), s.group(2)))
                k += 1
        j += 1
    return patched, skipped, samples


def side(label, path, log):
    res = classify(path)
    lp, ls, samples = read_log(log)
    sk = res["SKIPPED"]
    print("== %s  %s" % (label, path))
    print("   step's own log line (%s): %s patched / %s skipped" % (log, lp, ls))
    print("   this check: patched %d - skipped %d - eligible-now %d   (of %d entries)"
          % (len(res["PATCHED"]), len(sk), len(res["ELIGIBLE-NOW"]), len(FIXES)))
    print("   patched only after punctuation / dash normalising: %d %s"
          % (len(res["loose_only"]), ", ".join(res["loose_only"])))
    print("   patched but english_head differs from the patch's: %d %s"
          % (len(res["head_differs"]), ", ".join(res["head_differs"])))
    if res["ELIGIBLE-NOW"]:
        print("   ELIGIBLE-NOW: " + ", ".join(res["ELIGIBLE-NOW"]))
        stops.append("%s: %d verse(s) would patch now" % (label, len(res["ELIGIBLE-NOW"])))
    if lp is None:
        stops.append("%s: no fix_split_merges count line in %s" % (label, log))
    elif (lp, ls) != (len(res["PATCHED"]), len(sk)):
        stops.append("%s: this check %d/%d vs the log %d/%d"
                     % (label, len(res["PATCHED"]), len(sk), lp, ls))
    same_reason = 0
    print("   log's skip samples (%d):" % len(samples))
    for v, why in samples:
        mine = sk.get(v)
        tag = "in list, same reason" if mine == why else ("in list, reason now: " + str(mine)
                                                         if v in sk else "NOT IN LIST")
        same_reason += mine == why
        print("     %-10s log: %s   -> %s" % (v, why, tag))
        if v not in sk:
            stops.append("%s: log sample %s is not in the skip list" % (label, v))
    if len(samples) != 10:
        stops.append("%s: %d skip samples read from the log, expected 10" % (label, len(samples)))
    print("   samples in the list: %d of %d - same reason text: %d of %d"
          % (sum(v in sk for v, _ in samples), len(samples), same_reason, len(samples)))
    print("   all %d skips (step's reason, read now):" % len(sk))
    for v in sk:
        print("     %-10s %s" % (v, sk[v]))
    print()
    return set(sk)


def main():
    print("CHECK 1 - fix_split_merges skips by name - read-only")
    sha = hashlib.sha256(raw).hexdigest()
    print("split_merge_fixes.json: %d entries - sha256 %s (%s)"
          % (len(FIXES), sha, "= 61484fbc" if sha == FIXES_SHA else "DIFFERS from 61484fbc"))
    if sha != FIXES_SHA:
        stops.append("patch file differs from the code reference")
    if os.path.realpath(BUILT) == os.path.realpath(LIVE):
        print("CHECK1 RESULT: STOP - built and live are the same file")
        sys.exit(1)
    print()
    new = side("BUILT (tail v3, 11/4)", BUILT, LOG_NEW)
    old = side("LIVE (10/25 run)", LIVE, LOG_OLD)
    new_only, old_only = sorted(new - old), sorted(old - new)
    print("== difference")
    print("   skipped on built, not on live (%d): %s" % (len(new_only), ", ".join(new_only) or "-"))
    print("   skipped on live, not on built (%d): %s" % (len(old_only), ", ".join(old_only) or "-"))
    print("   skipped on both (%d)" % len(new & old))
    print("   expected: +Jdg 11:7, +Rom 9:29, nothing the other way")
    if set(new_only) != EXPECT_NEW_ONLY or set(old_only) != EXPECT_OLD_ONLY:
        stops.append("difference is not +Jdg 11:7 +Rom 9:29 / nothing")
    print()
    if stops:
        print("CHECK1 RESULT: STOP - " + " | ".join(stops))
        sys.exit(1)
    print("CHECK1 RESULT: AS EXPECTED - %d skips on built = the %d of 10/25 + Jdg 11:7 + Rom 9:29"
          % (len(new), len(old)))


if __name__ == "__main__":
    main()
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = 9b4e4bde65842a5f43cd14bace14668b562f5815ef9590e87ee93abd5d5b3ae8 ] || { echo "CHECK1 RESULT: STOP - the pasted script does not match the drafted one"; exit 1; }
PYTHONIOENCODING=utf-8 python3 "$P" "$B" "$L" "$N" "$O"
) 2>&1 | tee ~/edition_upgrade_runs/check1_split_skips_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: built `206 / 31` = log; live `208 / 29` = log; eligible-now 0 / 0; 10 of 10 samples in each list; difference
`+Jdg 11:7, +Rom 9:29`, nothing the other way (2Ti 4:10 on both) → `CHECK1 RESULT: AS EXPECTED`. Anything else = STOP, review.

### Block CHECK 2 (GATE REF `61484fbc`; sources read-only, writes only `~/edition_upgrade_runs/check2_20261104/`)
```bash
set +H
( set -uo pipefail
REF=61484fbc
echo "GATE REF ${REF} - CHECK 2 import_tipnr -57 (sources read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "CHECK2 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
T=$(git log --since=2026-10-24 --oneline -- scripts/import_tipnr.py scripts/tipnr_alias_variants.py tipnr/TIPNR.txt)
[ -z "$T" ] || { echo "CHECK2 RESULT: STOP - the name roster or matcher changed since 10/24: $T"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; L=~/bible-db/bible.db
N=~/edition_upgrade_runs/stageC_tail3_20261104.log; O=~/bible-db/finish_pnstar2.log
W=~/edition_upgrade_runs/check2_20261104
for f in "$B" "$L" "$N" "$O"; do [ -f "$f" ] || { echo "CHECK2 RESULT: STOP - missing: $f"; exit 1; }; done
mkdir -p "$W"
P=~/edition_upgrade_runs/check2_tipnr_lost_20261104.py
cat > "$P" <<'PY'
"""CHECK 2 (one-off): trace the -57 import_tipnr matches (built 31,592 vs the 10/25 run's 31,649).

The built copy and live are opened READ-ONLY. The only files written are two throwaway copies under
<workdir> (scratch_built.db, scratch_live.db) and their import_tipnr output.

Why a throwaway copy: on live, 8b re-numbers thousands of name cells after the import, so live's
numbers no longer show what the import decided. So for each side this takes the cells the import
looked at (is_pn = 1: import_tipnr is the only writer of is_pn = 1, and it marks exactly the cells
that were '*' when it ran), puts back the English they had when the import ran, sets them to '*',
and runs the real, unchanged scripts/import_tipnr.py on that copy. Steps after the import that
change English are undone, newest first:
  - lane-3 hand repairs (8b.2a; live only): cell back to old_eng where it holds new_eng
  - word corrections (tail step 7): cell back to source_value where it holds corrected_value
  - fix_emdash (tail step 5): em dash back to '--'
Proof the method reproduces the step: the built copy has not had 8b, so its stored result must
match the re-run cell for cell, and each re-run's Matched figure must equal its own log line.

Usage: python3 check2_tipnr_lost_20261104.py <built.db> <live.db> <tail3.log> <finish_pnstar2.log> <workdir>
"""
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict

BUILT, LIVE, LOG_NEW, LOG_OLD, WORK = (os.path.abspath(a) for a in sys.argv[1:6])
REPO = os.environ.get("CHECK_REPO") or os.path.expanduser("~/bible-db")
EM = chr(8212)
LANE3 = ("lane3_star_fixes2.json", "lane3_star_gapfix.json", "lane3_star_fixes.json")  # undo newest first
stops = []


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


MATCHED = re.compile(r"Matched\s*:\s*([\d,]+)")
UNMATCHED = re.compile(r"Unmatched:\s*([\d,]+) words\s*\(([\d,]+) distinct")


def import_figures(text):
    """Matched / Unmatched from the FIRST import_tipnr run in a log or an output."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if "import_tipnr.py" in l), 0)
    m = u = None
    for l in lines[start:]:
        if m is None and MATCHED.search(l):
            m = int(MATCHED.search(l).group(1).replace(",", ""))
        if u is None and UNMATCHED.search(l):
            g = UNMATCHED.search(l)
            u = (int(g.group(1).replace(",", "")), int(g.group(2).replace(",", "")))
        if m is not None and u is not None:
            break
    return m, u


def make_scratch(label, src):
    path = os.path.join(WORK, "scratch_%s.db" % label)
    for p in (path, path + "-journal"):
        if os.path.exists(p):
            os.remove(p)
    c = sqlite3.connect("file:%s" % path, uri=True)
    c.execute("ATTACH DATABASE ? AS src", ("file:%s?mode=ro" % src,))
    c.execute("CREATE TABLE verses AS SELECT id, book, chapter, verse FROM src.verses")
    c.execute("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INTEGER, position INTEGER,"
              " english TEXT, english_now TEXT, strongs_base TEXT, stored_sb TEXT, is_pn INTEGER)")
    c.execute("INSERT INTO words SELECT rowid, verse_id, position, english, english, '*',"
              " strongs_base, 0 FROM src.words WHERE is_pn = 1")
    c.execute("CREATE TABLE bdb AS SELECT strongs_id FROM src.bdb")
    c.execute("CREATE TABLE lexicon AS SELECT strongs FROM src.lexicon")
    corr = c.execute("SELECT book, chapter, verse, position, source_value, corrected_value"
                     " FROM src.abp_corrections WHERE status = 'active' AND field = 'english'").fetchall()
    c.commit()
    c.execute("DETACH DATABASE src")
    vid = {(b, ch, vs): i for i, b, ch, vs in c.execute("SELECT id, book, chapter, verse FROM verses")}

    def ref_id(ref):
        book, rest = ref.rsplit(" ", 1)
        ch, vs = rest.split(":")
        return vid.get((book, int(ch), int(vs)))

    undone = Counter()
    for fname in (LANE3 if label == "live" else ()):   # 8b.2a has not run on built
        d = json.load(open(os.path.join(REPO, "scripts", fname), encoding="utf-8"))
        d.pop("_comment", None)
        for ref, spec in d.items():
            for op in spec["ops"]:
                if op.get("new_eng") == op.get("old_eng"):
                    continue
                n = c.execute("UPDATE words SET english = ? WHERE verse_id = ? AND position = ?"
                              " AND english IS ?", (op.get("old_eng"), ref_id(ref), op["pos"],
                                                    op.get("new_eng"))).rowcount
                undone["lane-3 cells"] += n
    for b, ch, vs, pos, before, after in corr:
        n = c.execute("UPDATE words SET english = ? WHERE verse_id = ? AND position = ?"
                      " AND english IS ?", (before, vid.get((b, ch, vs)), pos, after)).rowcount
        undone["word-correction cells"] += n
    undone["em-dash cells"] = c.execute("UPDATE words SET english = REPLACE(english, ?, '--')"
                                        " WHERE instr(english, ?) > 0", (EM, EM)).rowcount
    c.commit()
    total = c.execute("SELECT count(*) FROM words").fetchone()[0]
    c.close()
    print("   throwaway copy %s: %d name cells (is_pn = 1); undone: lane-3 %d, word corrections %d,"
          " em dash %d" % (path, total, undone["lane-3 cells"], undone["word-correction cells"],
                           undone["em-dash cells"]))
    return path


def run_import(label, path):
    out = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "import_tipnr.py"), path],
                         cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
                         env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    text = out.stdout + out.stderr
    with open(os.path.join(WORK, "scratch_%s_import.out" % label), "w", encoding="utf-8") as fh:
        fh.write(text)
    if "still strongs_base='*'" not in text:
        stops.append("%s: import_tipnr did not finish on the throwaway copy (exit %d)"
                     % (label, out.returncode))
    return import_figures(text)


def load(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    refs = {i: "%s %d:%d" % (b, ch, vs) for i, b, ch, vs in
            c.execute("SELECT id, book, chapter, verse FROM verses")}
    rows = {}
    for wid, v, pos, eng, now, sb, stored in c.execute(
            "SELECT id, verse_id, position, english, english_now, strongs_base, stored_sb FROM words"):
        rows[wid] = dict(ref=refs[v], pos=pos, eng=eng or "", now=now or "", sb=sb, stored=stored)
    c.close()
    return rows


def core(eng):
    """letters of the name part: drop leading all-lowercase words (of, the, to, land ...)."""
    toks = eng.split()
    while len(toks) > 1 and toks[0].lower() == toks[0]:
        toks = toks[1:]
    return re.sub(r"[^a-z]", "", " ".join(toks).lower())


def verse_text(conn, ref, idx):
    """the verse's cells as the import saw them: name cells from the throwaway copy (import-time
    English), every other cell as stored now. pos -> (english, strongs_base now)"""
    book, rest = ref.rsplit(" ", 1)
    ch, vs = rest.split(":")
    cells = conn.execute("SELECT w.position, w.english, w.strongs_base FROM words w JOIN verses v"
                         " ON v.id = w.verse_id WHERE v.book = ? AND v.chapter = ? AND v.verse = ?"
                         " ORDER BY w.position", (book, int(ch), int(vs))).fetchall()
    out = {}
    for p, e, s in cells:
        r = idx.get((ref, p))
        out[p] = (r["eng"] if r else (e or ""), s)
    return out


def main():
    print("CHECK 2 - import_tipnr matches, 10/25 run vs tail v3 - sources read-only")
    if os.path.realpath(BUILT) == os.path.realpath(LIVE):
        print("CHECK2 RESULT: STOP - built and live are the same file")
        sys.exit(1)
    os.makedirs(WORK, exist_ok=True)
    log_new = import_figures(open(LOG_NEW, encoding="utf-8", errors="replace").read())
    log_old = import_figures(open(LOG_OLD, encoding="utf-8", errors="replace").read())
    print("logs: tail v3 Matched %s / Unmatched %s  -  10/25 (%s) Matched %s / Unmatched %s"
          % (log_new[0], log_new[1], os.path.basename(LOG_OLD), log_old[0], log_old[1]))
    if None in log_new or None in log_old:
        stops.append("could not read Matched/Unmatched from a log")

    sides = {}
    for label, src, logf in (("built", BUILT, log_new), ("live", LIVE, log_old)):
        print("== %s  %s" % (label, src))
        p = make_scratch(label, src)
        fig = run_import(label, p)
        print("   re-run on the throwaway copy: Matched %s / Unmatched %s   (its own log: %s / %s) %s"
              % (fig[0], fig[1], logf[0], logf[1], "SAME" if fig == logf else "DIFFERS"))
        if fig != logf:
            stops.append("%s: re-run %s/%s vs log %s/%s" % (label, fig[0], fig[1], logf[0], logf[1]))
        sides[label] = load(p)

    # Proof on built (no 8b yet): the stored result vs the re-run, cell by cell
    b = sides["built"]
    st = {i for i, r in b.items() if r["stored"] != "*"}
    rr = {i for i, r in b.items() if r["sb"] != "*"}
    numdiff = [i for i in st & rr if b[i]["stored"] != b[i]["sb"]]
    print("== proof on built: stored matched %d - re-run matched %d - stored only %d - re-run only %d"
          " - same cell, other number %d" % (len(st), len(rr), len(st - rr), len(rr - st), len(numdiff)))
    for tag, ids in (("stored only", st - rr), ("re-run only", rr - st), ("other number", numdiff)):
        for i in sorted(ids, key=lambda k: (b[k]["ref"], b[k]["pos"])):
            r = b[i]
            print("   %-12s %-11s pos %-3d import-time %r  now %r  stored %s  re-run %s"
                  % (tag, r["ref"], r["pos"], r["eng"], r["now"], r["stored"], r["sb"]))
    if st != rr:
        stops.append("built: stored result and re-run differ (%d / %d cells)"
                     % (len(st - rr), len(rr - st)))
    print()

    # Pair the matched cells verse by verse: same position + number, then same number elsewhere
    def by_verse(rows):
        d = defaultdict(list)
        for r in rows.values():
            if r["sb"] != "*":
                d[r["ref"]].append(r)
        return d

    L, B = by_verse(sides["live"]), by_verse(sides["built"])
    lost, gained, moved_list = [], [], []
    for ref in sorted(set(L) | set(B)):
        lv, bv = list(L.get(ref, [])), list(B.get(ref, []))
        for r in list(lv):
            hit = next((x for x in bv if x["pos"] == r["pos"] and x["sb"] == r["sb"]), None)
            if hit:
                lv.remove(r); bv.remove(hit)
        for r in list(lv):
            hit = next((x for x in bv if x["sb"] == r["sb"]), None)
            if hit:
                lv.remove(r); bv.remove(hit); moved_list.append((r, hit))
        lost += lv
        gained += bv
    moved = len(moved_list)
    print("== MOVED (%d): same number, other cell of the same verse - not a loss" % moved)
    for r, h in moved_list:
        print("   %-11s %s  10/25 pos %d %r  ->  built pos %d %r" % (r["ref"], r["sb"], r["pos"], r["eng"],
                                                                 h["pos"], h["eng"]))
    print()

    lc, bc = ro(LIVE), ro(BUILT)
    lidx = {(r["ref"], r["pos"]): r for r in sides["live"].values()}
    bidx = {(r["ref"], r["pos"]): r for r in sides["built"].values()}

    def reason(r, here_idx, other_idx, other_conn, here_conn):
        """class for a cell matched on one side and not the other"""
        o = other_idx.get((r["ref"], r["pos"]))
        other_cells = verse_text(other_conn, r["ref"], other_idx)
        here_cells = verse_text(here_conn, r["ref"], here_idx)
        changed = [c[0] for c in here_cells.values()] != [c[0] for c in other_cells.values()]
        o_eng = o["eng"] if o else None
        cell_now = other_cells.get(r["pos"], (None, None))
        if o is not None and o_eng == r["eng"]:
            cls = "OTHER (same English, different result)"
        elif not changed and o is None:
            cls = "OTHER (verse English unchanged)"
        else:
            name = core(r["eng"])
            joined = re.sub(r"[^a-z]", "", " ".join(c[0] for c in other_cells.values()).lower())
            if name and name in joined:
                cls = "TOKEN-SPLIT (name letters still in the verse, carved differently)"
            elif changed or (o is not None and o_eng != r["eng"]):
                cls = "EDITION-TEXT (the English wording changed)"
            else:
                cls = "OTHER"
        return cls, o_eng, cell_now

    def show(title, rows, here_idx, other_idx, other_conn, here_conn, here, other):
        classes = Counter()
        print("== %s (%d): %s matched, %s not - by verse" % (title, len(rows), here, other))
        for r in sorted(rows, key=lambda x: (x["ref"], x["pos"])):
            cls, o_eng, cell_now = reason(r, here_idx, other_idx, other_conn, here_conn)
            classes[cls.split(" ")[0]] += 1
            print("   %-11s pos %-3d %s %r -> %s   |   %s: name cell %r, cell as read %r (number now %s)   [%s]"
                  % (r["ref"], r["pos"], here, r["eng"], r["sb"], other, o_eng, cell_now[0],
                     cell_now[1], cls))
        print("   classes: " + ", ".join("%s %d" % kv for kv in sorted(classes.items())))
        names = Counter(core(r["eng"]) or r["eng"] for r in rows)
        print("   by name: " + ", ".join("%s %d" % kv for kv in names.most_common()))
        print()
        return classes

    lcls = show("LOST", lost, lidx, bidx, bc, lc, "10/25", "built")
    gcls = show("GAINED", gained, bidx, lidx, lc, bc, "built", "10/25")
    lc.close(); bc.close()
    net = len(lost) - len(gained)
    lm = sum(1 for r in sides["live"].values() if r["sb"] != "*")
    bm = sum(1 for r in sides["built"].values() if r["sb"] != "*")
    print("== sums: lost %d - gained %d = net %d ; re-run matched 10/25 %d - built %d = %d ;"
          " moved within a verse (same number, other cell) %d"
          % (len(lost), len(gained), net, lm, bm, lm - bm, moved))
    if log_old[0] is not None and log_new[0] is not None:
        print("   logs: %d - %d = %d" % (log_old[0], log_new[0], log_old[0] - log_new[0]))
        if net != log_old[0] - log_new[0]:
            stops.append("net %d does not equal the logs' difference %d" % (net, log_old[0] - log_new[0]))
    others = lcls.get("OTHER", 0) + gcls.get("OTHER", 0)
    if others:
        stops.append("%d cell(s) in class OTHER" % others)
    print()
    if stops:
        print("CHECK2 RESULT: STOP - " + " | ".join(stops))
        sys.exit(1)
    print("CHECK2 RESULT: AS EXPECTED - net -%d = %d lost - %d gained, every one EDITION-TEXT or"
          " TOKEN-SPLIT, method proven on built" % (net, len(lost), len(gained)))


if __name__ == "__main__":
    main()
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = b03d2a0b3ea27ca29c5091c93a224c86fefff5f323b213bf9f9e11a83e8aa724 ] || { echo "CHECK2 RESULT: STOP - the pasted script does not match the drafted one"; exit 1; }
PYTHONIOENCODING=utf-8 python3 "$P" "$B" "$L" "$N" "$O" "$W"
) 2>&1 | tee ~/edition_upgrade_runs/check2_tipnr_lost_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: both re-runs SAME as their logs (31,592 / 734 (687); 31,649 / 683 (648)); built proof stored-only 0 /
re-run-only 0; net = 57; every lost/gained cell EDITION-TEXT or TOKEN-SPLIT → `CHECK2 RESULT: AS EXPECTED`. Any OTHER
or a figure off = STOP, members printed.

## 2026-11-04 — CHECK 1 ran (03:59 UTC) and STOPPED on the live side; CHECK 2 rejected → CHECK 2b ruled; both HELD
**CHECK 1 result** (`~/edition_upgrade_runs/check1_split_skips_20261104.log`): built side exact — 206 / 31 = log, 10 of 10
samples, same reasons, eligible-now 0. Live side read 196 / 41 vs its log 208 / 29: 12 extra "skips", all "strongs mismatch"
(Act 7:3, Exo 4:23, Eze 20:14, Gen 31:49, Isa 56:10, Jas 4:2, Job 8:10, Joh 13:8, Joh 19:15, Jos 2:4, Neh 5:12, Rom 3:4).
**Cause = CC's draft error:** v1 read live against the patch file at `61484fbc`, but `63744245` (11/2, §9.77) re-keyed 18
entries to the app edition's wording (e.g. Gen 31:49 "Let God" → "May God"); the 10/25 run used the file before that.
All 12 extras are among the 18 re-keyed (checked locally against git); the other 6 re-keyed entries still matched
(they are in live's "patched only after normalising" line). The 29 on both sides are exactly the live log's count.
**v2:** live read against `63744245^:scripts/split_merge_fixes.json` (sha `7efa15d3…`); built unchanged. Tested: v1 on a
synthetic live made from the old file stops the same way; v2 passes; whole block ran in a fake home.

**CHECK 2 rejected** (too much machinery). **CHECK 2b** as ruled: built `*` name cells with English vs live's cell at the same
verse + position, and the reverse; class TEXT-CHANGED / TEXT-SAME; sums a review line; stops only on gate / missing file /
same file. 93 lines. Tested on a synthetic pair (lost changed / lost same / gained / both `*` / no live cell).

### Block CHECK 1 v2 (GATE REF `61484fbc`, read-only)
```bash
set +H
( set -uo pipefail
REF=61484fbc
echo "GATE REF ${REF} - CHECK 1 v2 split-merge skips (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "CHECK1 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; L=~/bible-db/bible.db
N=~/edition_upgrade_runs/stageC_tail3_20261104.log; O=~/bible-db/finish_pnstar2.log
for f in "$B" "$L" "$N" "$O"; do [ -f "$f" ] || { echo "CHECK1 RESULT: STOP - missing: $f"; exit 1; }; done
P=~/edition_upgrade_runs/check1v2_split_skips_20261104.py
cat > "$P" <<'PY'
"""CHECK 1 v2 (one-off, read-only): name every fix_split_merges skip on the built copy (tail v3, 11/4)
and on live (the 10/25 run), and diff the two sets.

Both databases are opened read-only. Nothing is written anywhere.

Why not just re-run the step's test: the step already ran on both copies, so a PATCHED verse no
longer holds its "before" English and fails the step's own test too. So each verse is read two
ways and the logs check the result:
  1. patch result present  - every entry's new_pos cell holds new_eng (punctuation and '--'/em dash
                             normalised, since fix_bracket_punct and fix_emdash run after the patch)
                             -> PATCHED
  2. otherwise             - the step's own test (fix_split_merges.py lines 46-71, same queries, same
                             order, same reason text) gives the skip reason -> SKIPPED
  3. the step's test passes now -> ELIGIBLE-NOW (should be 0: the step would patch it today)
Cross-checks: the counts must equal the step's own log line, and each log's 10 printed skip
samples must be in the list.

v2: each side is read against the patch file ITS run used. Built (tail v3) = the file at 61484fbc.
Live (10/25) = the file before 63744245 (11/2, DESIGN 9.77 re-keyed 18 entries to the app edition's
wording) - v1 read live against the re-keyed file and so miscounted those 18 (12 read as skips).

Usage: python3 check1_split_skips_20261104.py <built.db> <live.db> <tail3.log> <finish_pnstar2.log>
"""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys

BUILT, LIVE, LOG_NEW, LOG_OLD = sys.argv[1:5]
FIXES_PATH = os.path.join(os.environ.get("CHECK_REPO") or os.path.expanduser("~/bible-db"),
                          "scripts", "split_merge_fixes.json")
FIXES_SHA = "eab8e565cd1dd34231254088091ffb13b93e8ec52cdbb53a8b622a1148dcc8c5"   # = 61484fbc
EXPECT_NEW_ONLY = {"Jdg 11:7", "Rom 9:29"}    # ruling: the 10/25 29 + these two, nothing lost
EXPECT_OLD_ONLY = set()
EM = chr(8212)
PUNCT = ".,;:?" + chr(33) + chr(183) + ")"      # chr(33) = exclamation mark (kept out of the paste)
EDGE = re.compile("^[(]+|[" + re.escape(PUNCT) + "]+$")

REPO = os.environ.get("CHECK_REPO") or os.path.expanduser("~/bible-db")
OLD_SHA = "7efa15d301db3342884e20181daf26c7633c70b36874e7ca4458e26c3667323f"    # = 63744245^
raw = open(FIXES_PATH, "rb").read()
FIXES = json.loads(raw.decode("utf-8"))
raw_old = subprocess.run(["git", "-C", REPO, "show", "63744245^:scripts/split_merge_fixes.json"],
                         capture_output=True, check=True).stdout
FIXES_OLD = json.loads(raw_old.decode("utf-8"))
stops = []


def norm(s):
    s = (s or "").replace("--", EM).strip()
    prev = None
    while prev != s:
        prev = s
        s = EDGE.sub("", s).strip()
    return " ".join(s.split())


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


def step_test(conn, verse, ops):
    """fix_split_merges.py's own guard, verbatim in effect. None = would patch now."""
    book, rest = verse.rsplit(" ", 1)
    ch, vs = rest.split(":")
    r = conn.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                     (book, int(ch), int(vs))).fetchone()
    if r is None:
        return None, "verse not found"
    vid = r[0]
    for op in ops:
        row = conn.execute(
            "SELECT id, english, strongs_base FROM words WHERE verse_id=? AND position=?",
            (vid, op["old_pos"])).fetchone()
        if row is None:
            return vid, "no row at pos %s" % op["old_pos"]
        if row[2] != "G" + op["sbase"]:
            return vid, "strongs mismatch pos %s (%s != G%s)" % (op["old_pos"], row[2], op["sbase"])
        if (row[1] or "") != (op["old_eng"] or ""):
            return vid, "english mismatch pos %s (%s)" % (op["old_pos"], repr(row[1]))
    return vid, None


def result_present(conn, vid, ops):
    """(loose, strict, head) - does every new_pos cell hold the patch's result?"""
    loose = strict = head = True
    for op in ops:
        rows = conn.execute(
            "SELECT english, english_head, strongs_base FROM words WHERE verse_id=? AND position=?",
            (vid, op["new_pos"])).fetchall()
        pick = [r for r in rows if r[2] == "G" + op["sbase"]] or rows
        if not pick:
            return False, False, False
        e, h = pick[0][0] or "", pick[0][1] or ""
        strict &= e == (op["new_eng"] or "")
        loose &= norm(e) == norm(op["new_eng"])
        head &= h == (op["new_head"] or "")
    return loose, strict, head


def classify(path, fixes):
    conn = ro(path)
    out = {"PATCHED": [], "SKIPPED": {}, "ELIGIBLE-NOW": [], "loose_only": [], "head_differs": []}
    for verse, ops in fixes.items():
        vid, reason = step_test(conn, verse, ops)
        if vid is not None and reason is None:
            out["ELIGIBLE-NOW"].append(verse)
            continue
        if vid is not None:
            loose, strict, head = result_present(conn, vid, ops)
            if loose:
                out["PATCHED"].append(verse)
                if not strict:
                    out["loose_only"].append(verse)
                if not head:
                    out["head_differs"].append(verse)
                continue
        out["SKIPPED"][verse] = reason
    conn.close()
    return out


SAMPLE = re.compile(r"^\s{3}(\S+ \d+:\d+): (.*)$")
COUNT = re.compile(r"(\d+) verse\(s\) patched, (\d+) skipped")


def read_log(path):
    """The step's own count line and its printed skip samples, from a finish_rebuild log."""
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    starts = [i for i, l in enumerate(lines) if "fix_split_merges.py" in l]
    if not starts:
        return None, None, []
    i = starts[0]
    patched = skipped = None
    samples = []
    j = i + 1
    while j < len(lines) and "fix_kyrios_mistags" not in lines[j]:
        m = COUNT.search(lines[j])
        if m and patched is None:
            patched, skipped = int(m.group(1)), int(m.group(2))
        if "skip samples" in lines[j]:
            k = j + 1
            while k < len(lines):
                s = SAMPLE.match(lines[k])
                if not s:
                    break
                samples.append((s.group(1), s.group(2)))
                k += 1
        j += 1
    return patched, skipped, samples


def side(label, path, log, fixes):
    res = classify(path, fixes)
    lp, ls, samples = read_log(log)
    sk = res["SKIPPED"]
    print("== %s  %s" % (label, path))
    print("   step's own log line (%s): %s patched / %s skipped" % (log, lp, ls))
    print("   this check: patched %d - skipped %d - eligible-now %d   (of %d entries)"
          % (len(res["PATCHED"]), len(sk), len(res["ELIGIBLE-NOW"]), len(fixes)))
    print("   patched only after punctuation / dash normalising: %d %s"
          % (len(res["loose_only"]), ", ".join(res["loose_only"])))
    print("   patched but english_head differs from the patch's: %d %s"
          % (len(res["head_differs"]), ", ".join(res["head_differs"])))
    if res["ELIGIBLE-NOW"]:
        print("   ELIGIBLE-NOW: " + ", ".join(res["ELIGIBLE-NOW"]))
        stops.append("%s: %d verse(s) would patch now" % (label, len(res["ELIGIBLE-NOW"])))
    if lp is None:
        stops.append("%s: no fix_split_merges count line in %s" % (label, log))
    elif (lp, ls) != (len(res["PATCHED"]), len(sk)):
        stops.append("%s: this check %d/%d vs the log %d/%d"
                     % (label, len(res["PATCHED"]), len(sk), lp, ls))
    same_reason = 0
    print("   log's skip samples (%d):" % len(samples))
    for v, why in samples:
        mine = sk.get(v)
        tag = "in list, same reason" if mine == why else ("in list, reason now: " + str(mine)
                                                         if v in sk else "NOT IN LIST")
        same_reason += mine == why
        print("     %-10s log: %s   -> %s" % (v, why, tag))
        if v not in sk:
            stops.append("%s: log sample %s is not in the skip list" % (label, v))
    if len(samples) != 10:
        stops.append("%s: %d skip samples read from the log, expected 10" % (label, len(samples)))
    print("   samples in the list: %d of %d - same reason text: %d of %d"
          % (sum(v in sk for v, _ in samples), len(samples), same_reason, len(samples)))
    print("   all %d skips (step's reason, read now):" % len(sk))
    for v in sk:
        print("     %-10s %s" % (v, sk[v]))
    print()
    return set(sk)


def main():
    print("CHECK 1 v2 - fix_split_merges skips by name - read-only")
    sha = hashlib.sha256(raw).hexdigest()
    print("split_merge_fixes.json: %d entries - sha256 %s (%s)"
          % (len(FIXES), sha, "= 61484fbc" if sha == FIXES_SHA else "DIFFERS from 61484fbc"))
    if sha != FIXES_SHA:
        stops.append("patch file differs from the code reference")
    sha_old = hashlib.sha256(raw_old).hexdigest()
    print("10/25 patch file (63744245^): %d entries - sha256 %s (%s) - entries that differ: %d"
          % (len(FIXES_OLD), sha_old, "as drafted" if sha_old == OLD_SHA else "DIFFERS",
             sum(FIXES_OLD.get(k) != v for k, v in FIXES.items())))
    if sha_old != OLD_SHA:
        stops.append("the 10/25 patch file is not the drafted one")
    if os.path.realpath(BUILT) == os.path.realpath(LIVE):
        print("CHECK1 RESULT: STOP - built and live are the same file")
        sys.exit(1)
    print()
    new = side("BUILT (tail v3, 11/4; file at 61484fbc)", BUILT, LOG_NEW, FIXES)
    old = side("LIVE (10/25 run; file before 63744245)", LIVE, LOG_OLD, FIXES_OLD)
    new_only, old_only = sorted(new - old), sorted(old - new)
    print("== difference")
    print("   skipped on built, not on live (%d): %s" % (len(new_only), ", ".join(new_only) or "-"))
    print("   skipped on live, not on built (%d): %s" % (len(old_only), ", ".join(old_only) or "-"))
    print("   skipped on both (%d)" % len(new & old))
    print("   expected: +Jdg 11:7, +Rom 9:29, nothing the other way")
    if set(new_only) != EXPECT_NEW_ONLY or set(old_only) != EXPECT_OLD_ONLY:
        stops.append("difference is not +Jdg 11:7 +Rom 9:29 / nothing")
    print()
    if stops:
        print("CHECK1 RESULT: STOP - " + " | ".join(stops))
        sys.exit(1)
    print("CHECK1 RESULT: AS EXPECTED - %d skips on built = the %d of 10/25 + Jdg 11:7 + Rom 9:29"
          % (len(new), len(old)))


if __name__ == "__main__":
    main()
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = 96a16b5338e47144df34de89f405ce038490246af6b20104f18e00653597d745 ] || { echo "CHECK1 RESULT: STOP - the pasted script does not match the drafted one"; exit 1; }
PYTHONIOENCODING=utf-8 python3 "$P" "$B" "$L" "$N" "$O"
) 2>&1 | tee ~/edition_upgrade_runs/check1v2_split_skips_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: as CHECK 1 — built 206 / 31, live 208 / 29 (each = its log), 10 of 10 samples, difference +Jdg 11:7 +Rom 9:29
only → `CHECK1 RESULT: AS EXPECTED`; plus the 10/25 file line "as drafted - entries that differ: 18".

### Block CHECK 2b (GATE REF `61484fbc`, read-only)
```bash
set +H
( set -uo pipefail
REF=61484fbc
echo "GATE REF ${REF} - CHECK 2b unmatched name cells (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "CHECK2b RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; L=~/bible-db/bible.db
for f in "$B" "$L"; do [ -f "$f" ] || { echo "CHECK2b RESULT: STOP - missing: $f"; exit 1; }; done
P=~/edition_upgrade_runs/check2b_tipnr_cells_20261104.py
cat > "$P" <<'PY'
"""CHECK 2b (one-off, read-only): built's unmatched name cells vs live's cell at the same verse +
position, and the reverse. Both databases opened read-only; nothing is written.

LOST   = built name cell (is_pn = 1) still '*' with English, live's cell there is not '*'
GAINED = live name cell (is_pn = 1) still '*' with English, built's cell there is not '*'
Class  = TEXT-CHANGED (the two verses' English sequences differ) or TEXT-SAME.
Live's numbers are post-8b, so the sums are a review line, never a stop.

Usage: python3 check2b_tipnr_cells_20261104.py <built.db> <live.db>
"""
import os
import sqlite3
import sys

BUILT, LIVE = sys.argv[1:3]
EXPECT_CELLS, EXPECT_NAMES, EXPECT_NET = 734, 687, 31649 - 31592   # tail v3 log; the two Matched lines
Q = ("SELECT v.id, v.book, v.chapter, v.verse, w.position, w.english, w.strongs_base"
     " FROM words w JOIN verses v ON v.id = w.verse_id")


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


def stars(c):
    """(ref, pos) -> (verse id, english) for name cells still '*' with English"""
    return {("%s %d:%d" % (b, ch, vs), pos): (vid, eng) for vid, b, ch, vs, pos, eng, sb in
            c.execute(Q + " WHERE w.is_pn = 1 AND w.strongs_base = '*'"
                          " AND w.english IS NOT NULL AND w.english <> ''")}


def verse(c, ref):
    """pos -> (english, strongs_base) for one verse"""
    book, rest = ref.rsplit(" ", 1)
    ch, vs = rest.split(":")
    return {pos: (eng or "", sb) for _v, _b, _c, _s, pos, eng, sb in
            c.execute(Q + " WHERE v.book = ? AND v.chapter = ? AND v.verse = ? ORDER BY w.position",
                      (book, int(ch), int(vs)))}


def compare(here, here_c, other_c):
    """cells '*' on this side whose cell on the other side is not '*'"""
    out = []
    for (ref, pos), (vid, eng) in here.items():
        mine, theirs = verse(here_c, ref), verse(other_c, ref)
        o_eng, o_sb = theirs.get(pos, ("(no cell)", None))
        if o_sb == "*":
            continue
        same = [e for e, _ in mine.values()] == [e for e, _ in theirs.values()]
        out.append((vid, pos, ref, eng, o_eng, o_sb, "TEXT-SAME" if same else "TEXT-CHANGED"))
    return sorted(out)


def show(title, rows, here, other):
    print("== %s (%d)" % (title, len(rows)))
    for cls in ("TEXT-CHANGED", "TEXT-SAME"):
        part = [r for r in rows if r[6] == cls]
        print("   -- %s (%d)" % (cls, len(part)))
        for _vid, pos, ref, eng, o_eng, o_sb, _cls in part:
            print("   %-11s pos %-3d %s %r   %s %r (number %s)" % (ref, pos, here, eng, other, o_eng, o_sb))
    print()
    return sum(r[6] == "TEXT-SAME" for r in rows)


def main():
    print("CHECK 2b - import_tipnr unmatched cells, built vs live - read-only")
    if os.path.realpath(BUILT) == os.path.realpath(LIVE):
        print("CHECK2b RESULT: STOP - built and live are the same file")
        sys.exit(1)
    bc, lc = ro(BUILT), ro(LIVE)
    b, l = stars(bc), stars(lc)
    names = len({e.strip() for _v, e in b.values()})
    print("built unmatched: %d cells / %d distinct English (tail log: %d / %d) %s"
          % (len(b), names, EXPECT_CELLS, EXPECT_NAMES,
             "SAME" if (len(b), names) == (EXPECT_CELLS, EXPECT_NAMES) else "DIFFERS - review"))
    print("live '*' name cells with English: %d (post-8b)" % len(l))
    print()
    lost, gained = compare(b, bc, lc), compare(l, lc, bc)
    same = show("LOST: built '*', live numbered", lost, "built", "live")
    same += show("GAINED: live '*', built numbered", gained, "live", "built")
    net = len(lost) - len(gained)
    print("== sums: lost %d - gained %d = %d ; logs' difference %d ; %s"
          % (len(lost), len(gained), net, EXPECT_NET,
             "SAME" if net == EXPECT_NET else "DIFFERS - review (live is post-8b)"))
    print("   TEXT-SAME cells: %d (review, listed above)" % same)
    print("CHECK2b RESULT: READ - lost %d, gained %d, net %d vs %d, TEXT-SAME %d"
          % (len(lost), len(gained), net, EXPECT_NET, same))


if __name__ == "__main__":
    main()
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = e044ac410010d1e9a02a33e22118dedf81d3afc121bb6875e0bb42b8609d873f ] || { echo "CHECK2b RESULT: STOP - the pasted script does not match the drafted one"; exit 1; }
PYTHONIOENCODING=utf-8 python3 "$P" "$B" "$L"
) 2>&1 | tee ~/edition_upgrade_runs/check2b_tipnr_cells_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: built unmatched 734 / 687 (SAME); lost − gained vs 57 and the TEXT-SAME list are review lines; ends
`CHECK2b RESULT: READ`.

### CHECK 1 v2 + CHECK 2b — RAN on PA 11/4 (04:06–04:07 UTC), both cleared as printed; held for ruling-chat read

PA HEAD 8db1604a (older master commit; gate is scripts/tests vs 61484fbc — passed). Logs:
`~/edition_upgrade_runs/check1v2_split_skips_20261104.log`, `~/edition_upgrade_runs/check2b_tipnr_cells_20261104.log`.

**CHECK 1 v2 — `CHECK1 RESULT: AS EXPECTED`, exit 0.** Old patch file sha 7efa15d3… as drafted, entries
that differ 18. Built 206/31 = log; live 208/29 = log; eligible-now 0 both; 10/10 samples each, same
reasons. Difference: +Jdg 11:7 +Rom 9:29, nothing the other way; 29 on both. Review notes only:
built "patched only after normalising" = 2 (Isa 56:10, Luk 12:40) vs live 1 (Luk 12:40) — Isa 56:10 is
one of the 18 re-keyed entries; 2Ti 4:10 skip reason reads `'For'` on built vs `'for'` on live (edition
capital), on both lists as ruled.

**CHECK 2b — `CHECK2b RESULT: READ`, exit 0.** Built unmatched 734 / 687 SAME as the tail log. Live '*'
name cells with English: 16,636. LOST 193 (117 TEXT-CHANGED, 76 TEXT-SAME); GAINED 16,079 (8,106 /
7,973); net −15,886 vs 57 (review line); TEXT-SAME total 8,049.
Reading (CC, for the ruling chat — not a ruling): the cell comparison is swamped by 8b, which has run on
live and not yet on built (handoff line 27: 8b not yet run). rebuild-words.md 8b: import_tipnr writes the
HEBREW stopgap numbers; live serving is Greek-keyed with Hebrew in `pn_hebrew_xref` (8b.2). That matches
the shape — GAINED is live '*' vs built H-number (e.g. Gen 2:8 Eden H5731), LOST TEXT-SAME is live
G-number vs built '*' (e.g. Gen 2:14 Euphrates G2166). Not checked member by member. So this method
cannot isolate the −57; it does show the edition-text side directly. Cells worth a look (live English
→ built English at the same slot): 2Ki 9:31 'with Omri,' → 'to Zimri,' H2174; Num 36:5 pos 13 'of
Israel,' → 'of Joseph,' H3130; Jos 5:15 pos 26 'Josua' → 'did' G4160; 2Ki 23:35 pos 7 'Jehoiakim' →
'gave' G1325; Est 5:9 pos 12/13 'Haman' ↔ 'seeing' G1492 (a name cell sits one slot over); Psa 89:35
'I lie to David, no.' → 'I lie to David?'; spelling changes (Gergesite→Gergasite, Zerubbabel→Zorobabel,
Bethany→Bethania, Seredites→Sardites, Simon→Simeon Deu 33:6, Jonas→Jonah Joh 21:15/16, Klopas→Cleophas,
Rahab→Rachab Mat 1:5).

## Tail v3 ACCEPTED (11/4); C3 re-pin + C4 gate 1 drafted, held

Ruling chat 11/4: CHECK 1 v2 + CHECK 2b accepted; §9.85 (JP) defers the −57 import_tipnr matches to gate 2
(pn_binding declared delta, member by member, after 8b on built — "Hebrew-key vs Greek-key" shown, not
assumed); named member rulings owed in declared_deltas.json for 2Ki 9:31, Num 36:5 pos 13, Jos 5:15 pos 26,
2Ki 23:35 pos 7, Est 5:9 pos 12/13; Psa 89:35 → §9.52 v2 STOP; the edition spellings are declared, not
reviewed. Built copy is post-tail: no further writes until the re-pin commit lands.

**Why C3 starts with a PA dump:** the 23 retired keys exist only in `<built>`'s table (no committed list),
so the 372 member list cannot be built locally. **C3a** (PA, read-only, below): one-off
`repin_dump_20261104.py` lists `<built>`'s `status='active' AND applied_at='ingest'` rows (the exact rows
cert check 4 counts) in the 10/31 format and writes the file + `.sha256` ONLY if: 372 = 28 carried + 344 EU;
EU keys = `eu_batch_rows_20261103.tsv`'s 344 (sha 38acc6ba…); every carried row is one of the 51
(`abp_corrections_active_live_20261031.txt`, sha 5b1a7595…); 51 − carried = 23, each `retired` on the copy,
copy's retired total 23; 0 active rows outside `ingest`. Tested on made-up dbs (good / one EU row missing /
one old row not retired / one stray row → OK, STOP, STOP, STOP; refuses to overwrite).
**C3b** (local): scp the two files to `tests/fixtures/corrections/`, check the sha, then ONE commit:
`scripts/cert_invariants.py` PINS `abp_corrections_active` 51 → 372 (comment names the file + sha) +
the member file + `.sha256`. Planned diff summary: `scripts/cert_invariants.py | 2 +-` ·
`tests/fixtures/corrections/abp_corrections_active_built_20261104.txt | 372 +` · `….sha256 | 1 +` →
`3 files changed, 374 insertions(+), 1 deletion(-)`. ops.md cert line follows in a separate docs commit
(the ruling says scripts/tests-only). **C3c** (PA): `cd ~/bible-db && git pull --ff-only` — no reload.
Side effect: cert_invariants on LIVE reads check 4 red (51 vs 372) from the pull until the swap; nothing
runs it automatically (grep: only comments mention it).
**C4** gate 1 (below) gets its REF from C3b; printed again with the hash filled before it is run.
CC note for the ruling chat: the standing code check `git diff --quiet <REF> HEAD -- scripts tests`
compares PA's last commit to REF, not the files on disk (a test with an uncommitted edit passed it).
PA is pull-only, so it holds in practice — flagged, not changed.

### Block C3a — RE-PIN DUMP (GATE REF 61484fbc, read-only)
```bash
set +H
( set -uo pipefail
REF=61484fbc
echo "GATE REF ${REF} - RE-PIN DUMP built active corrections (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "REPIN DUMP: STOP - scripts/tests differ from $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; O=~/edition_upgrade_runs
[ -f "$B" ] || { echo "REPIN DUMP: STOP - missing: $B"; exit 1; }
for f in "$O/abp_corrections_active_built_20261104.txt" "$O/abp_corrections_active_built_20261104.txt.sha256"; do [ -e "$f" ] && { echo "REPIN DUMP: STOP - already exists: $f"; exit 1; }; done
P=$O/repin_dump_20261104.py
cat > "$P" <<'PY'
"""Re-pin dump (one-off, read-only) - DESIGN 9.59. Lists the built copy's active ingest correction
rows (the rows cert check 4 counts) in the 10/31 member-file format, and checks them against two
committed files before writing anything:
  - EU- rows (ledger_ref EU-...) = the 344 keys of tests/fixtures/edition_upgrade/eu_batch_rows_20261103.tsv
  - every other active row is one of the 51 in tests/fixtures/corrections/abp_corrections_active_live_20261031.txt
  - the 51 minus those carried rows = the retire set: each one is status 'retired' on the copy,
    and the copy's retired total is that same number
Expected: 372 = 28 carried + 344 EU; retired 23. The member file + .sha256 are written ONLY when every
check passes. The database is opened read-only; the only writes are the two files in OUT_DIR.

Usage: python3 repin_dump_20261104.py <built.db> <repo> <out_dir>
"""
import hashlib
import os
import sqlite3
import sys

BUILT, REPO, OUT_DIR = sys.argv[1:4]
OLD_REL = "tests/fixtures/corrections/abp_corrections_active_live_20261031.txt"
OLD_SHA = "5b1a75952c3358ab1ef75431b15f324cc90c3561f33950deb3f37aa824196298"
EU_REL = "tests/fixtures/edition_upgrade/eu_batch_rows_20261103.tsv"
EU_SHA = "38acc6ba99d8ef8ac7b2eccb92494115bde94e9f957751677ebf86cf420f6717"
NAME = "abp_corrections_active_built_20261104.txt"
EXPECT_ACTIVE, EXPECT_EU, EXPECT_CARRIED, EXPECT_RETIRED = 372, 344, 28, 23
stops = []


def key(book, ch, vs, pos, field, ref):
    return (book, int(ch), int(vs), int(pos), field, ref)


def line(k):
    return "%s\t%d\t%d\t%d\t%s\t%s" % k


def read_fixture(rel, sha, label):
    raw = open(os.path.join(REPO, rel), "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    print("%s: %s - sha256 %s (%s)" % (label, rel, got[:16], "as committed" if got == sha else "DIFFERS"))
    if got != sha:
        stops.append("%s file is not the committed one" % label)
    return raw.decode("utf-8").splitlines()


def show(title, keys):
    print("== %s (%d)" % (title, len(keys)))
    for k in keys:
        print("   " + line(k))


def main():
    print("RE-PIN DUMP - built copy's active correction rows - read-only")
    if os.path.realpath(BUILT) == os.path.realpath(os.path.expanduser("~/bible-db/bible.db")):
        print("REPIN DUMP: STOP - this is live, not the built copy")
        sys.exit(1)
    old = {key(*l.split("\t")) for l in read_fixture(OLD_REL, OLD_SHA, "51-row member")}
    eu_lines = read_fixture(EU_REL, EU_SHA, "EU rows")
    eu = set()
    for l in eu_lines[1:]:
        c = l.split("\t")
        eu.add(key(c[0], c[1], c[2], c[3], c[4], c[7]))
    print("   51-row file keys %d - EU file keys %d" % (len(old), len(eu)))

    conn = sqlite3.connect("file:%s?mode=ro" % BUILT, uri=True, timeout=30)
    conn.execute("PRAGMA query_only=1")
    by_status = conn.execute("SELECT status, applied_at, count(*) FROM abp_corrections "
                             "GROUP BY status, applied_at ORDER BY status, applied_at").fetchall()
    print("\nbuilt copy abp_corrections by status / applied_at:")
    for s, a, n in by_status:
        print("   %-11s %-8s %d" % (s, a, n))
    rows = conn.execute("SELECT book, chapter, verse, position, field, ledger_ref FROM abp_corrections "
                        "WHERE status='active' AND applied_at='ingest'").fetchall()
    active = [key(*r) for r in rows]
    if len(set(active)) != len(active):
        stops.append("%d duplicate active key(s)" % (len(active) - len(set(active))))
    active = set(active)
    other_active = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='active' "
                                "AND applied_at IS NOT 'ingest'").fetchone()[0]
    act_eu = {k for k in active if k[5].startswith("EU-")}
    carried = active - act_eu
    retire_set = old - carried

    print("\nactive ingest rows %d (expect %d) = carried %d (expect %d) + EU %d (expect %d)"
          % (len(active), EXPECT_ACTIVE, len(carried), EXPECT_CARRIED, len(act_eu), EXPECT_EU))
    print("active rows NOT applied at ingest: %d (expect 0)" % other_active)
    for got, want, what in ((len(active), EXPECT_ACTIVE, "active"), (len(carried), EXPECT_CARRIED, "carried"),
                            (len(act_eu), EXPECT_EU, "EU")):
        if got != want:
            stops.append("%s %d, expected %d" % (what, got, want))
    if other_active:
        stops.append("%d active row(s) not applied at ingest" % other_active)

    miss_eu, extra_eu = sorted(eu - act_eu), sorted(act_eu - eu)
    print("EU rows vs the EU file: missing %d - extra %d" % (len(miss_eu), len(extra_eu)))
    if miss_eu or extra_eu:
        stops.append("EU rows differ from the EU file")
        show("EU file rows not active on the copy", miss_eu)
        show("active EU rows not in the EU file", extra_eu)
    not_old = sorted(carried - old)
    print("carried rows not in the 51-row file: %d (expect 0)" % len(not_old))
    if not_old:
        stops.append("%d carried row(s) are not in the 51-row file" % len(not_old))
        show("carried rows not in the 51-row file", not_old)

    not_retired = []
    for k in sorted(retire_set):
        st = [r[0] for r in conn.execute(
            "SELECT status FROM abp_corrections WHERE book=? AND chapter=? AND verse=? AND position=? "
            "AND field=? AND ledger_ref=?", k)]
        if st != ["retired"]:
            not_retired.append((k, st))
    retired_total = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='retired'").fetchone()[0]
    conn.close()
    print("retire set (51 minus carried) %d (expect %d) - status 'retired' on the copy %d - "
          "copy's retired total %d" % (len(retire_set), EXPECT_RETIRED,
                                      len(retire_set) - len(not_retired), retired_total))
    if len(retire_set) != EXPECT_RETIRED or not_retired or retired_total != EXPECT_RETIRED:
        stops.append("retire set does not check out")
    for k, st in not_retired:
        print("   NOT RETIRED: %s  status %s" % (line(k), st))

    print()
    show("carried rows (the 28 of the 51 still active)", sorted(carried))
    show("retired rows (51 minus carried)", sorted(retire_set))
    print()
    if stops:
        print("REPIN DUMP: STOP - " + " | ".join(stops) + " - nothing written")
        sys.exit(1)
    body = "".join(line(k) + "\n" for k in sorted(active)).encode("utf-8")
    sha = hashlib.sha256(body).hexdigest()
    path = os.path.join(OUT_DIR, NAME)
    with open(path, "wb") as f:
        f.write(body)
    with open(path + ".sha256", "wb") as f:
        f.write(("%s  %s\n" % (sha, NAME)).encode("utf-8"))
    print("wrote %s (%d lines) + .sha256" % (path, body.count(b"\n")))
    print("REPIN DUMP: OK - %d = %d carried + %d EU - retired %d - sha256 %s"
          % (len(active), len(carried), len(act_eu), len(retire_set), sha))


if __name__ == "__main__":
    main()
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = 5f25e8f694aa7da242c88ce77fd9134730908becebb72d56ae0ead38b42fccfa ] || { echo "REPIN DUMP: STOP - the pasted script does not match the drafted one"; exit 1; }
PYTHONIOENCODING=utf-8 python3 "$P" "$B" ~/bible-db "$O"
) 2>&1 | tee ~/edition_upgrade_runs/repin_dump_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: both fixture lines `(as committed)`; status/applied_at `active ingest 372 · retired ingest 23 ·
superseded ingest 6`; `active ingest rows 372 = carried 28 + EU 344`; `NOT applied at ingest: 0`; EU missing 0
/ extra 0; carried not in the 51: 0; retire set 23 / retired 23 / total 23; the 28 + 23 keys listed; ends
`REPIN DUMP: OK - 372 = 28 carried + 344 EU - retired 23 - sha256 <hex>`, exit=0. Then (local, read-only
touchpoint): `scp PA:~/edition_upgrade_runs/abp_corrections_active_built_20261104.txt{,.sha256} ./tests/fixtures/corrections/`

### Block C4 — GATE 1 (REF = the C3b commit; filled in when it exists)
```bash
set +H
( set -uo pipefail
REF=__REPIN_COMMIT__
echo "GATE REF ${REF} - GATE 1 cert_invariants on the built copy (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "GATE1 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
grep -q '"abp_corrections_active": 372,' scripts/cert_invariants.py || { echo "GATE1 RESULT: STOP - the corrections pin is not 372 in this checkout"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
[ -f "$B" ] || { echo "GATE1 RESULT: STOP - missing: $B"; exit 1; }
python3 scripts/cert_invariants.py --controls; c=$?
[ "$c" -eq 0 ] || { echo "GATE1 RESULT: STOP - controls exit $c (a check that cannot fire is void)"; exit 1; }
python3 scripts/cert_invariants.py "$B"; r=$?
[ "$r" -eq 0 ] && echo "GATE1 RESULT: 7/7 on the built copy" || echo "GATE1 RESULT: STOP - suite exit $r (names above)"
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/gate1_cert_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: controls `[FIRED]` ×6 + `ALL CONTROLS FIRED`; suite `[OK  ]` ×7 — check 1 words 626,309 / verses
31,237, check 4 = 372 active all holding, check 3 em-dash 0 — `CERTIFIED STATE HOLDS (7/7 green)`,
`GATE1 RESULT: 7/7 on the built copy`, exit=0.

## GATE 1 ACCEPTED (11/4); C5 retired-row gate drafted, held

Gate 1 (REF f8e814c2, PA HEAD 7358c8bf, `gate1_cert_20261104.log`): controls 6/6 FIRED, built copy 7/7. The first
try stopped on the new uncommitted-edit line (three untracked `scripts/*metav_link*.txt` dumps on PA); the line is
amended to `--untracked-files=no` for every gate from here (ruling 11/4; the three files are left alone).

**C5 — §9.61/§9.63 retired-row gate.** Runs the approved `scripts/eu_retired_check.py` (§9.81, at f8e814c2) on
`<built>`, after its own 11 tests on PA (they include failing cases: a check that cannot fire is void).
Expected figure, from the code + §9.63's step-7b evidence: the 23 retired rows (the C3a dump's list) =
11 `greek_pos` + 12 `verses.text`; the 5 named prose rows (ids 51 2Sa 16:18, 25 1Ch 22:15, 27 Job 24:19,
24 Mat 21:19, 45 Mar 16:17) hold on B's feed text (derived by B's own `feed_text` from the pinned feed,
then the em-dash swap); the other 18 hold on `corrected_value` → `PASS 23/23 HOLD (corrected_value 18 -
feed text 5)`. Any failing row prints its full source / corrected / feed / built text. Tested in a throwaway
checkout at f8e814c2 on a made-up db (tests green, stray file passed the code check, the check's STOP came
through as exit 2).

### Block C5 — RETIRED-ROW GATE (GATE REF f8e814c2, read-only)
```bash
set +H
( set -uo pipefail
REF=f8e814c2
echo "GATE REF ${REF} - RETIRED-ROW GATE (sec 9.61/9.63) on the built copy (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "RETIRED-ROW CHECK: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "RETIRED-ROW CHECK: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
[ -f "$B" ] || { echo "RETIRED-ROW CHECK: STOP - missing: $B"; exit 1; }
python3 tests/test_eu_retired_check.py; t=$?
[ "$t" -eq 0 ] || { echo "RETIRED-ROW CHECK: STOP - the check's own tests exit $t (a check that cannot fire is void)"; exit 1; }
PYTHONIOENCODING=utf-8 python3 scripts/eu_retired_check.py "$B"; r=$?
echo "check exit $r (0 PASS / 1 FAIL / 2 STOP)"
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/retired_check_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: `Ran 11 tests` / `OK`; 23 `ok` lines (18 `corrected_value`, 5 `feed text` — ids 24, 25, 27, 45, 51);
`RETIRED-ROW CHECK: PASS 23/23 HOLD (corrected_value 18 - feed text 5)`; `check exit 0`; `exit=0`.

**C5 RAN 11/4 05:01 UTC (cleared as printed; REF f8e814c2, PA HEAD 7358c8bf; `retired_check_20261104.log`):**
11 tests OK; 23 `ok` lines — 18 `corrected_value` + 5 `feed text` (ids 24 Mat 21:19, 25 1Ch 22:15, 27 Job 24:19,
45 Mar 16:17, 51 2Sa 16:18); `RETIRED-ROW CHECK: PASS 23/23 HOLD (corrected_value 18 - feed text 5)`, exit 0.
The 23 rows = the C3a retired list, row for row (11 greek_pos + 12 verses.text). No FAIL rows. Next: C6 gate 3.
Re-run 11/4 13:32 UTC (same block, same REF/HEAD): identical result, PASS 23/23 (18 + 5), exit 0. The log file now holds this re-run (tee overwrote the 05:01 run).

## C5 ACCEPTED (11/4); C6 gate 3 drafted, held

Ruling chat 11/4: retired-row gate accepted (23/23, 18/5); the 13:32 duplicate run noted, no action. GO for gate 3.
Standing: "draft X now?" questions go to the ruling chat, not JP.

**C6 — gate 3, v2 member diff (REF f8e814c2, read-only).** Checks first: frozen punct file
`tests/fixtures/reassembly/punct_members_live_20261030.txt` sha 2b0f4cc4… as committed (241 members; Psa 89:35
is NOT in it); eligible file `~/edition_upgrade_runs/step5_eligible_20261101.tsv` sha prefix e540d34d (the only
fingerprint on record, HANDOFF_edition_upgrade_stageC.md "PA figures"). Then the port test
(`tests/test_reorder_port.py`, 137 verses = JS baseline), the member diff's own 9 tests, the v2 controls, and
the member diff (`audit_reassembly_diff.py <built> --v2 --punct-members <frozen> --eligible <step5>`).
Hard fails (exit 1): any word-order / content-other / dup-gloss member, Joh 14:26 not clean, any NEW punct
member on a non-eligible verse. Otherwise the gate STOPS after printing gone / new-on-eligible / changed-ops
for the §9.52 ruling. Counts on those lists are not forecast (first v2 member diff on this copy); the ruling
chat expects Psa 89:35 among the new members — not checked ahead of the run. Tested in a throwaway checkout at
f8e814c2 on a made-up copy: shifted comma on an eligible verse → listed + `GATE3 RESULT: NO FAIL - STOP HERE`
(exit 0); same verse not eligible → `GATE3 RESULT: FAIL` (exit 1).

### Block C6 — GATE 3 (GATE REF f8e814c2, read-only)
```bash
set +H
( set -uo pipefail
REF=f8e814c2
echo "GATE REF ${REF} - GATE 3 reassembly v2 member diff on the built copy (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "GATE3 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "GATE3 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
F=tests/fixtures/reassembly/punct_members_live_20261030.txt
E=~/edition_upgrade_runs/step5_eligible_20261101.tsv
for f in "$B" "$F" "$E"; do [ -f "$f" ] || { echo "GATE3 RESULT: STOP - missing: $f"; exit 1; }; done
[ "$(sha256sum < "$F" | cut -d' ' -f1)" = 2b0f4cc43efc6dd423d934d4633727f69fcb6f45f894727b3a634265b68a941f ] || { echo "GATE3 RESULT: STOP - frozen punct file is not the committed one"; exit 1; }
[ "$(sha256sum < "$E" | cut -c1-8)" = e540d34d ] || { echo "GATE3 RESULT: STOP - eligible file is not step 5's (e540d34d...)"; exit 1; }
echo "frozen punct file: $(grep -c . "$F") members (sha 2b0f4cc4 as committed) - eligible file sha e540d34d as recorded"
python3 tests/test_reorder_port.py || { echo "GATE3 RESULT: STOP - reorder port drifted from the JS baseline"; exit 1; }
python3 tests/test_reassembly_member_diff.py || { echo "GATE3 RESULT: STOP - the member diff's own tests failed (a check that cannot fire is void)"; exit 1; }
python3 scripts/audit_reassembly_diff.py --controls --v2 || { echo "GATE3 RESULT: STOP - v2 controls did not fire"; exit 1; }
PYTHONIOENCODING=utf-8 python3 scripts/audit_reassembly_diff.py "$B" --v2 --punct-members "$F" --eligible "$E"; r=$?
case "$r" in
  0) echo "GATE3 RESULT: NO FAIL - STOP HERE: the gone / new-on-eligible / changed-ops lists above go to the ruling chat (sec 9.52)";;
  1) echo "GATE3 RESULT: FAIL - named above (word-order / content-other / dup-gloss / Joh 14:26 / new on non-eligible)";;
  *) echo "GATE3 RESULT: STOP - member diff exit $r";;
esac
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/gate3_member_diff_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: the file line (241 members, 2b0f4cc4, e540d34d); `ok  reorder port reproduces the JS baseline on all
137 fixture verses`; `Ran 9 tests` / `OK`; `V2 CONTROLS PASSED.`; member diff: word-order 0, content-other 0,
dup-gloss 0, `Joh 14:26 ... clean`, NEW on a NON-eligible verse 0; `V2 MEMBER DIFF: NO FAIL - ...`;
`GATE3 RESULT: NO FAIL - STOP HERE ...`; exit=0. The full gone / new-on-eligible / changed-ops lists come to the
ruling chat. Stage D (8b) waits on that ruling.

## C6 gate 3 RAN (11/4 14:30 UTC) — FAIL, HELD; CHECK 3 drafted, held

**Run** (`~/edition_upgrade_runs/gate3_member_diff_20261104.log`, REF f8e814c2, PA HEAD 7358c8bf): inputs as drafted
(241 / 2b0f4cc4 / e540d34d); port test OK (137); 9 tests OK; `V2 CONTROLS PASSED.` Member diff:
`V2 MEMBER DIFF: FAIL - word-order 112 - content-other 1 - dup-gloss 0 - Joh 14:26 HIT - new on non-eligible 0 | to
ruling: gone 25 - new on eligible 367 - changed ops 12 - unchanged 204` → `GATE3 RESULT: FAIL`, exit=1. Live 10/30
read word-order 1 (Joh 14:26) / content-other 0 (DESIGN §2 table), so 111 word-order + 1 content-other are new on
this copy. The full lists are in the PA log (and the 11/4 chat).

**Ruling chat 11/4: HELD (not accepted, not failed).** Reading: the 112 = verb cell at clause end in rows vs earlier in
the edition prose, read as tag placement (the §9.62 604 passdiff class); Job 3:3 and Joh 14:26 to be shown; Psa 89:35
on none of the §9.52 lists. Pre-rulings, applying if CHECK 3 shows them: **§9.86 (JP)** word-order criterion for this
build = all members ⊂ passdiff 604/625 (Joh 14:26 declared with them if same shape and consistent with charter 4.10);
**§9.87 (JP)** §9.52: the edition's punctuation governs — gone 25 / new-on-eligible 367 / changed-ops 12 accepted,
frozen punct file re-frozen from this copy (expected 583 = 204 + 367 + 12) in the 9c re-freeze commit; any item CHECK 3
puts on B = build defect, lane stops; feed items (Job 3:3, Joh 3:15, the " )" set) → follow-up corrections batch with
the nine doubled-words, declared in gate 3's record.

**CC local finding (before CHECK 3; files in the repo, not a PA read):** 111 of the 112 word-order verses are on the
frozen merge-pair list (`merge_pairs_20261102.tsv`, 104) or edge-split list (`edge_splits_20261102.tsv`, 13; the two
overlap); only Joh 14:26 is on neither. Samples: Lev 25:4 "You shall not" / "sow", Joh 2:3 "They do not" / "have." —
the §9.73 rule puts the OLD verb back on its own cell, and v2 then places that cell after the noun while the feed prose
has it after "not". Per §9.62 + the B record, passdiff verses are NOT eligible and keep old rows AND old prose (B
wrote 15,571 + left 13,500 = the 29,071 eligible only), while merge-pair verses stay eligible (§9.73) — so the
passdiff intersect is forecast at or near 0/112 → CHECK 3 prints STOP. Not checked against PA's eligible file yet.
Local run of B's own helper on the pinned feed (local feed sha 7bd77385… = manifest): Job 3:3 feed cell
`May[6be destroyed` (no space) → FEED; Joh 3:15 cell `1eternal.].` → FEED; all nine " )" verses carry `] )` / `], )`
/ `]; )` in the feed → FEED.

**CHECK 3** (one-off `check3_20261104.py`, sha 9ed2a151…, read-only, 77 lines): (1) the 112 (parsed from the gate 3
log, must equal its headline) vs step 5's reason column — in-passdiff count, NOT-in-passdiff by name — plus an added
line vs the merge-pair / edge-split lists; (2) Joh 14:26 rows (pos, english, bracket_id, greek_pos, strongs),
verses.text, charter §4.10 text, then the audit's own `--verse` v2 view; (3–4) feed cells / B's text
(`feed_text` + `emdash`) / verses.text for Job 3:3, Joh 3:15 and the nine " )" verses, one FEED-or-B line each.
`CHECK3 RESULT: AS RULED` only if 0 outside passdiff and every attribution FEED; else STOP (exit 1). Tested on a
made-up copy in a throwaway checkout at f8e814c2: full block end to end (inputs line, 4 items, --verse, STOP, exit=1);
all-passdiff log → AS RULED exit 0; text ≠ B's → STOP line; log headline mismatch → STOP before any read.

### Block CHECK 3 (GATE REF f8e814c2, read-only)
```bash
set +H
( set -uo pipefail
REF=f8e814c2
echo "GATE REF ${REF} - CHECK 3 gate-3 follow-up on the built copy (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "CHECK3 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "CHECK3 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; E=~/edition_upgrade_runs/step5_eligible_20261101.tsv
G=~/edition_upgrade_runs/gate3_member_diff_20261104.log; C=docs/handoffs/CHARTER_edition_upgrade.md
for f in "$B" "$E" "$G" "$C"; do [ -f "$f" ] || { echo "CHECK3 RESULT: STOP - missing: $f"; exit 1; }; done
[ "$(sha256sum < "$E" | cut -c1-8)" = e540d34d ] || { echo "CHECK3 RESULT: STOP - eligible file is not step 5's (e540d34d...)"; exit 1; }
grep -qF 'V2 MEMBER DIFF: FAIL - word-order 112 - content-other 1' "$G" || { echo "CHECK3 RESULT: STOP - gate 3 log is not the 14:30 run"; exit 1; }
S=~/edition_upgrade_runs/check3_20261104.py
cat > "$S" <<'PYEOF'
"""CHECK 3 (one-off, read-only, 11/4): gate 3 follow-up. argv: built_db eligible_tsv gate3_log charter_md"""
import collections, csv, re, sqlite3, sys
sys.path.insert(0, "scripts")
import build_prose_from_app as BP
db, elig, log, charter = sys.argv[1:5]
L = open(log, encoding="utf-8").read()
wo = [(b, int(c), int(v)) for b, c, v in re.findall(r"\[word-order\s*\] (\S+) (\d+):(\d+)", L)]
head = re.search(r"word-order members: (\d+)", L)
if not head or len(wo) != int(head.group(1)) or len(set(wo)) != len(wo):
    sys.exit(f"CHECK3 RESULT: STOP - word-order list in the gate 3 log does not match its own headline ({len(wo)})")
st = {(r["book"], int(r["chapter"]), int(r["verse"])): r["reason"] or "eligible"
      for r in csv.DictReader(open(elig, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE)}
def refs(p): return {(r["book"], int(r["chapter"]), int(r["verse"])) for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE)}
mp, es = refs("tests/fixtures/edition_upgrade/merge_pairs_20261102.tsv"), refs("tests/fixtures/edition_upgrade/edge_splits_20261102.tsv")
nm = lambda k: f"{k[0]} {k[1]}:{k[2]}"
print(f"== 1. the {len(wo)} word-order verses vs step 5's reason (passdiff in the file: {sum(1 for r in st.values() if r == 'passdiff')})")
print(f"   in passdiff: {sum(1 for k in wo if st.get(k) == 'passdiff')} / {len(wo)} - step-5 status of the {len(wo)}: {dict(collections.Counter(st.get(k, 'MISSING') for k in wo))}")
out = [k for k in wo if st.get(k) != "passdiff"]
print(f"   NOT in passdiff ({len(out)}):")
for i in range(0, len(out), 10):
    print("     " + ", ".join(nm(k) for k in out[i:i + 10]))
print(f"   (added) on the merge-pair list {sum(1 for k in wo if k in mp)} - edge-split list {sum(1 for k in wo if k in es)} - "
      f"either {sum(1 for k in wo if k in mp or k in es)} - neither: {', '.join(nm(k) for k in wo if k not in mp and k not in es) or 'none'}")
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
def vtext(k): return con.execute("SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?", k).fetchone()
print(f"== 2. Joh 14:26 (step-5 status: {st.get(('Joh', 14, 26), 'MISSING')})")
vid, t = vtext(("Joh", 14, 26))
print(f"   verses.text: {t}")
for p, e, bi, gp, s in con.execute("SELECT position, english, bracket_id, greek_pos, strongs FROM words WHERE verse_id=? ORDER BY position", (vid,)):
    print(f"   pos {p:3} {repr(e):24} bracket_id {bi} greek_pos {gp} strongs {s}")
lines = open(charter, encoding="utf-8").read().splitlines()
i = next(n for n, x in enumerate(lines) if x.startswith("- **John 14:26"))
print("   charter 4.10 declaration:")
for x in lines[i:]:
    if not x.strip() or x.startswith("#"):
        break
    print("   | " + x)
app = BP.AppTransplant(BP.abp_source_texts())
PAREN = (r"\][,;.]? \)", " )")
CASES = [(("Job", 3, 3), r"May\[", "Maythe"), (("Joh", 3, 15), r"\.\]\.", "eternal. life.")] + [((b, c, v),) + PAREN for b, c, v in
         [("2Th", 1, 10), ("Rev", 2, 9), ("Rom", 4, 17), ("Rom", 9, 1), ("Luk", 2, 23), ("Heb", 7, 11), ("Phm", 1, 12), ("Luk", 2, 35), ("Eze", 26, 7)]]
att = collections.Counter()
print("== 3-4. feed cells / B's text (feed_text + emdash, B's own helper) / verses.text on the built copy")
for k, feed_re, mark in CASES:
    ka = app.pairs[k]
    cells = " | ".join(s["english"] for s in app.feed[ka])
    bt, vt = BP.emdash(BP.feed_text(app, k)), vtext(k)[1]
    v = ("STOP - verses.text is not B's text" if vt != bt else f"STOP - '{mark}' not in the text" if mark not in bt
         else "FEED" if re.search(feed_re, cells) else "B")
    att[v.split(" ")[0]] += 1
    print(f"   {nm(k)} feed: {cells}\n      B   : {bt}\n      text: {vt}\n   {nm(k)} -> {v}  ('{mark}' in text; feed pattern {repr(feed_re)} {'found' if re.search(feed_re, cells) else 'NOT found'})")
con.close()
ok = not out and set(att) == {"FEED"}
print(f"CHECK3 RESULT: {'AS RULED' if ok else 'STOP'} - outside passdiff {len(out)} / {len(wo)} - Joh 14:26 printed for the 4.10 read - attributions {dict(att)}")
sys.exit(0 if ok else 1)
PYEOF
[ "$(sha256sum < "$S" | cut -c1-8)" = 9ed2a151 ] || { echo "CHECK3 RESULT: STOP - one-off script is not as drafted (9ed2a151...)"; exit 1; }
echo "inputs: eligible e540d34d - gate 3 log = the 14:30 FAIL run - charter sha $(sha256sum < "$C" | cut -c1-8) - script 9ed2a151"
PYTHONIOENCODING=utf-8 python3 "$S" "$B" "$E" "$G" "$C"; r=$?
echo "--- Joh 14:26 through the audit's own --verse (v2, read-only) ---"
PYTHONIOENCODING=utf-8 python3 scripts/audit_reassembly_diff.py "$B" --v2 --verse "Joh 14:26"
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/check3_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: the inputs line (e540d34d, the 14:30 FAIL log, charter 9cb591c9, script 9ed2a151); item 1 with the step-5
status of the 112 and the merge-pair/edge-split line (forecast: either 111, neither Joh 14:26); item 2 as stored; item 3
`Job 3:3 -> FEED`; item 4 `-> FEED` ×10; `CHECK3 RESULT:` STOP if any of the 112 is outside passdiff (forecast), with
attributions {'FEED': 11}; then the Joh 14:26 --verse view; exit=1 on STOP.

## CHECK 3 RAN (11/4) — STOP, as forecast; held for the ruling chat

`~/edition_upgrade_runs/check3_20261104.log`, REF f8e814c2. `CHECK3 RESULT: STOP - outside passdiff 112 / 112 - ...
attributions {'FEED': 11}`, exit=1.
- **Item 1:** in passdiff **0 / 112**; all 112 eligible. On the merge-pair list 104, edge-split 13, either **111**,
  neither **Joh 14:26** (= CC's local forecast). §9.86's condition (112 ⊂ passdiff) does NOT hold: the 111 are
  word rows A built under §9.73/§9.75 (old verb put back on its own cell) that v2 places after the noun while
  the feed prose has it after "not". Not B, not the feed — A's rows. Mechanism (which bracket_id/greek_pos the
  restored verb cell carries) NOT traced yet.
- **Item 2, Joh 14:26:** ~~spirit/holy now carry digits — the part §4.10 named is cured~~ **WRONG (CC, corrected
  after CHECK 4): live rows are identical to built on all 26 cells; live ALREADY carries the spirit/holy digits.
  Nothing was cured — the claim rested on the charter's wording, not a live read.** pos 2 `the` (3588, no bracket) sits before pos 3
  `comforter,`; prose has it after. Reassembled `But the the comforter, holy spirit,` vs text `But the comforter,
  the holy spirit,`. Same v2 signature as live (`comforter,` displaced). §4.10: "if the built copy still shows the
  hit, the lane STOPS on it".
- **Items 3–4:** Job 3:3, Joh 3:15 and all nine " )" verses → **FEED** (11/11; verses.text = B's text on every
  one). Under §9.87 these go to the follow-up corrections batch with the nine doubled-words.

## CHECK 3 accepted; §9.86 withdrawn; CHECK 4 drafted, held (11/4)

Ruling chat 11/4: CHECK 3 accepted; §9.86 withdrawn; gate 3 stays STOPPED per charter 4.10. §9.87 stands (Job 3:3,
Joh 3:15, the nine " )" verses → follow-up corrections batch, FEED-attributed, declared in gate 3's record).
Diagnosis to confirm: A's §9.73/§9.75 restores put back old English but not old bracket_id/greek_pos. **Pre-ruling
§9.88 (JP), if CHECK 4 confirms:** fix at the rule (restore carries bracket_id/greek_pos from the old row; code +
fingerprint dry run + test → new ref); scoped repair UPDATE on exactly the item-2 cell set from the frozen old rows,
receipted, pre-repair rollback copy first; gate 3 re-run (word-order 0 except Joh 14:26 if a separate cell defect →
bracket_id/greek_pos correction rows, Act 7:3 S10 mechanism → pin 372→N + member file, re-pin, gate 1 re-run).

**CC code read (before CHECK 4):** compose takes each cell's greek_pos/bracket_id from the FEED row
(`build_words_from_abp.py:2397`, fields 5–6 = `f[5], f[6]`); `_restore_merge_pairs` (:2112) and
`_apply_edge_splits` (:2174) put back only english + english_head. So a restored cell keeps the feed cell's digits —
none on a feed-blank cell. Consistent with the diagnosis. Also from :2397: every eligible verse takes the feed's
digits on every cell by design, so item 4 is expected NOT bounded by item 2 (not counted yet).

**CHECK 4** (one-off `check4_20261104.py`, sha db61ef7f…, read-only on BOTH live and built — built opened
`mode=ro`, live ATTACHed `mode=ro`). A matching cell = same verse + position + Strong's; cells that don't match are
counted, not compared. (1) the gate-3 word-order verses on the merge-pair/edge-split lists, one line each: restored
cells live vs built (bracket_id/greek_pos), LOST/kept; (2) every restored cell of all 1,578 pairs / 1,380 verses +
90 splits: live-has/built-NULL count (bracket, greek_pos), both-set-but-different, no-match, verse list 10 per line;
(3) Joh 14:26 live beside built, both reassembled through the audit's own `reassemble_ordered`, "the the" YES/NO,
then the audit's own `--verse` on live; (4) anywhere in built: english set, bracket_id NULL, live's cell has
bracket_id — inside/outside the item-2 set, outside by step-5 status, every outside cell written to
`~/edition_upgrade_runs/check4_item4_outside_20261104.tsv`. `CHECK4 RESULT: CONFIRMED` only if 111 hit verses and
all 111 LOST. Tested on made-up live/built copies in a throwaway checkout at f8e814c2, whole block end to end:
LOST rows, a kept row → NOT CONFIRMED exit 1, a different-Strong's cell → NO MATCHING CELL, an outside cell → listed
+ written, live --verse view printed.

### Block CHECK 4 (GATE REF f8e814c2, read-only)
```bash
set +H
( set -uo pipefail
REF=f8e814c2
echo "GATE REF ${REF} - CHECK 4 restore-digits read, live vs built (read-only, both) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "CHECK4 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "CHECK4 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; LIVE=~/bible-db/bible.db
E=~/edition_upgrade_runs/step5_eligible_20261101.tsv; G=~/edition_upgrade_runs/gate3_member_diff_20261104.log
for f in "$B" "$LIVE" "$E" "$G"; do [ -f "$f" ] || { echo "CHECK4 RESULT: STOP - missing: $f"; exit 1; }; done
[ "$(sha256sum < "$E" | cut -c1-8)" = e540d34d ] || { echo "CHECK4 RESULT: STOP - eligible file is not step 5's (e540d34d...)"; exit 1; }
grep -qF 'V2 MEMBER DIFF: FAIL - word-order 112 - content-other 1' "$G" || { echo "CHECK4 RESULT: STOP - gate 3 log is not the 14:30 run"; exit 1; }
S=~/edition_upgrade_runs/check4_20261104.py
cat > "$S" <<'PYEOF'
"""CHECK 4 (one-off, read-only, 11/4): do A's merge-pair / edge-split restores drop the old bracket
digits? argv: built_db live_db eligible_tsv gate3_log outside_tsv. A cell = same verse + position + Strong's."""
import collections, csv, re, sqlite3, sys
sys.path.insert(0, "scripts")
from audit_reassembly_diff import reassemble_ordered
from audit_abp_app_vs_surface import BOOK_ORDER
built, live, elig, log, outp = sys.argv[1:6]
con = sqlite3.connect(f"file:{built}?mode=ro", uri=True)
con.execute("ATTACH DATABASE ? AS L", (f"file:{live}?mode=ro",))
def tsv(p): return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
key = lambda r: (r["book"], int(r["chapter"]), int(r["verse"]))
st = {key(r): r["reason"] or "eligible" for r in tsv(elig)}
cells, src = collections.defaultdict(set), {}
for name in ("merge_pairs", "edge_splits"):
    R = tsv(f"tests/fixtures/edition_upgrade/{name}_20261102.tsv")
    src[name] = f"{len(R)} {'pairs' if name == 'merge_pairs' else 'splits'} in {len({key(r) for r in R})} verses"
    for r in R:
        cells[key(r)].update((int(r["blank_pos"]), int(r["neighbor_pos"])))
rank = {b: i for i, b in enumerate(BOOK_ORDER)}
order = lambda ks: sorted(ks, key=lambda k: (rank.get(k[0], 99), k[1], k[2]))
nm = lambda k: f"{k[0]} {k[1]}:{k[2]}"
Q = ("SELECT w.position, w.english, w.bracket_id, w.greek_pos, w.strongs FROM {d}words w JOIN {d}verses v ON w.verse_id = v.id "
     "WHERE v.book = ? AND v.chapter = ? AND v.verse = ? ORDER BY w.position")
def rows(k, d=""): return {r[0]: r for r in con.execute(Q.format(d=d), k)}
dg = lambda r: f"{'-' if r[2] is None else r[2]}/{'-' if r[3] is None else r[3]}"
lost_cells, lostv, n_b, n_g, differ, smis, line = set(), set(), 0, 0, 0, 0, {}
for k in order(cells):
    B, Lv, parts = rows(k), rows(k, "L."), []
    for p in sorted(cells[k]):
        b, l = B.get(p), Lv.get(p)
        if not b or not l or b[4] != l[4]:
            smis += 1; parts.append(f"p{p} NO MATCHING CELL"); continue
        lb, lg = l[2] is not None and b[2] is None, l[3] is not None and b[3] is None
        if lb or lg:
            lost_cells.add(k + (p,)); lostv.add(k); n_b += lb; n_g += lg
        elif (l[2], l[3]) != (b[2], b[3]):
            differ += 1
        parts.append(f"p{p} {repr(b[1])} L {dg(l)} B {dg(b)}" + (f" (live {repr(l[1])})" if l[1] != b[1] else ""))
    line[k] = " ; ".join(parts)
wo = [(b, int(c), int(v)) for b, c, v in re.findall(r"\[word-order\s*\] (\S+) (\d+):(\d+)", open(log, encoding="utf-8").read())]
hit = [k for k in wo if k in cells]
print(f"== 1. the {len(hit)} gate-3 word-order verses on the merge-pair/edge-split lists - restored cells, live (L) vs built (B), bracket_id/greek_pos")
for k in hit:
    print(f"   {nm(k):11} {'LOST' if k in lostv else 'kept'}  {line[k]}")
print(f"   live digits -> built NULL on a restored cell: {sum(1 for k in hit if k in lostv)} / {len(hit)}")
print(f"== 2. full exposure: merge pairs {src['merge_pairs']} + edge splits {src['edge_splits']} = {len(cells)} verses, {sum(len(s) for s in cells.values())} restored cells")
print(f"   cells live-has / built-NULL: {len(lost_cells)} (bracket_id {n_b} - greek_pos {n_g}) in {len(lostv)} verses"
      f" | both set but different: {differ} | no matching cell (position/Strong's): {smis}")
lv = order(lostv)
for i in range(0, len(lv), 10):
    print("     " + ", ".join(nm(k) for k in lv[i:i + 10]))
J = ("Joh", 14, 26)
Bj, Lj = rows(J), rows(J, "L.")
print("== 3. Joh 14:26 - pos | LIVE english b/g strongs | BUILT english b/g strongs")
for p in sorted(set(Bj) | set(Lj)):
    l, b = Lj.get(p), Bj.get(p)
    print(f"   {p:3} | " + (f"{repr(l[1]):16} {dg(l):5} {l[4]}" if l else "-") + " | " + (f"{repr(b[1]):16} {dg(b):5} {b[4]}" if b else "-"))
asm = lambda R: " ".join(reassemble_ordered([dict(position=r[0], english=r[1], bracket_id=r[2], greek_pos=r[3]) for r in R.values()]))
print(f"   live  reassembled: {asm(Lj)}\n   built reassembled: {asm(Bj)}")
print(f"   live reassembles 'the the': {'YES' if 'the the' in asm(Lj) else 'NO'} - built: {'YES' if 'the the' in asm(Bj) else 'NO'}")
print("== 4. anywhere in built: english set, bracket_id NULL, live's matching cell has bracket_id")
A = con.execute("SELECT v.book, v.chapter, v.verse, w.position FROM words w JOIN verses v ON w.verse_id = v.id "
                "JOIN L.verses lv ON lv.book = v.book AND lv.chapter = v.chapter AND lv.verse = v.verse "
                "JOIN L.words lw ON lw.verse_id = lv.id AND lw.position = w.position AND lw.strongs IS w.strongs "
                "WHERE w.english IS NOT NULL AND w.bracket_id IS NULL AND lw.bracket_id IS NOT NULL").fetchall()
inside = [a for a in A if tuple(a) in lost_cells]
out = [a for a in A if tuple(a) not in lost_cells]
ov = order({tuple(a[:3]) for a in out})
print(f"   total {len(A)} - inside the item-2 set {len(inside)} - OUTSIDE {len(out)} cells in {len(ov)} verses"
      f" -> {'BOUNDED by item 2' if not out else 'NOT bounded by item 2'}")
print(f"   OUTSIDE by step-5 status: {dict(collections.Counter(st.get(k, 'MISSING') for k in ov))}")
with open(outp, "w", encoding="utf-8", newline="\n") as f:
    f.write("book\tchapter\tverse\tposition\tstep5\n")
    for a in sorted(out, key=lambda a: (rank.get(a[0], 99), a[1], a[2], a[3])):
        f.write(f"{a[0]}\t{a[1]}\t{a[2]}\t{a[3]}\t{st.get(tuple(a[:3]), 'MISSING')}\n")
print(f"   OUTSIDE list (every cell) -> {outp}; first 50 verses:")
for i in range(0, min(len(ov), 50), 10):
    print("     " + ", ".join(nm(k) for k in ov[i:i + 10]))
con.close()
ok = len(hit) == 111 and all(k in lostv for k in hit)
print(f"CHECK4 RESULT: {'CONFIRMED' if ok else 'NOT CONFIRMED'} - gate-3 verses with lost digits {sum(1 for k in hit if k in lostv)}/{len(hit)}"
      f" - exposure {len(lost_cells)} cells / {len(lostv)} verses - item 4 {'bounded' if not out else f'NOT bounded ({len(out)} cells outside)'}")
sys.exit(0 if ok else 1)
PYEOF
[ "$(sha256sum < "$S" | cut -c1-8)" = db61ef7f ] || { echo "CHECK4 RESULT: STOP - one-off script is not as drafted (db61ef7f...)"; exit 1; }
echo "inputs: eligible e540d34d - gate 3 log = the 14:30 FAIL run - script db61ef7f - live and built both opened read-only"
PYTHONIOENCODING=utf-8 python3 "$S" "$B" "$LIVE" "$E" "$G" ~/edition_upgrade_runs/check4_item4_outside_20261104.tsv; r=$?
echo "--- Joh 14:26 on LIVE through the audit's own --verse (v2, read-only) ---"
PYTHONIOENCODING=utf-8 python3 scripts/audit_reassembly_diff.py "$LIVE" --v2 --verse "Joh 14:26"
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/check4_20261104.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: inputs line; item 1 = 111 lines, `live digits -> built NULL on a restored cell: 111 / 111`; item 2 header
`merge pairs 1578 pairs in 1380 verses + edge splits 90 splits in 90 verses = 1456 verses, 3336 restored cells`,
counts not forecast; item 3 live rows without digits on spirit/holy (charter: live rows `the comforter, spirit
holy,`), live "the the" not forecast; item 4 expected NOT bounded (compose takes feed digits on every eligible
verse), count not forecast; `CHECK4 RESULT: CONFIRMED - ...` exit=0 if 111/111.

## CHECK 4 RAN (11/5 01:51 UTC) — NOT CONFIRMED (99/111); held for the ruling chat

`~/edition_upgrade_runs/check4_20261104.log` (REF f8e814c2, PA HEAD 7358c8bf, script db61ef7f), exit=1.
`CHECK4 RESULT: NOT CONFIRMED - gate-3 verses with lost digits 99/111 - exposure 150 cells / 123 verses - item 4 NOT
bounded (1177 cells outside)`. Ruling chat (11/4, with the clearance) amended §9.88: the repair is NOT "copy live's
digits"; it depends on whether the lost cell's live bracket matches the group the feed gives its neighbour in built
(yes for all → join that group with the old greek_pos; else the rule synthesises a group).

**Item 1 sorted by that test (CC, from the printed lines; script `sort_check4.py` in the session scratchpad):**
- **95 JOIN** — every lost cell's neighbour (the "not" cell) carries in built the SAME bracket + greek_pos as in live,
  and the lost cell's old greek_pos = neighbour's + 1. Joining the neighbour's group with the old greek_pos gives
  back live's digits exactly. Gen 9:4 … Rom 6:14 (all LOST verses except the 4 below).
- **4 RENUMBERED / odd:** Lev 12:4 (p18 live 1/1 → built 2/1: feed renumbered the group; p19 joins group 2 at gp 2 —
  plus a p12/p13 pair of the 7-shape below); Jer 5:29 (live p3 english is None but the build's old row is "I not";
  old gp of p4 = 1 collides with neighbour's 1 — live ≠ the build's old rows here); 1Co 16:19 and Joh 8:39 (edge
  splits "of" + name: built group renumbered AND the name's greek_pos differs, 1/3 vs live 3/2, 3/4 vs 4/2).
- **7 kept, live has NO digits on the pair; the feed puts a lone bracket on the "not" cell, verb none:** Exo 23:9,
  Lev 7:26, Lev 18:21, Lev 21:1, Lev 25:37, Joh 12:49, Mat 15:32. Nothing to copy from live → synthesise.
- **5 kept, digits identical live/built on the restored cells:** Pro 7:11, Pro 14:13, Pro 29:19, Isa 9:17, Isa 60:18 —
  the hit comes from elsewhere in the verse; neither restore rule touches it. Not read yet.

**Item 2:** 150 cells live-has / built-NULL (bracket 147, greek_pos 150) in 123 verses; both-set-but-different 17;
no matching cell 1. 24 of the 123 are not gate-3 word-order hits; **15 of those 24 are on gate 3's §9.87
new-on-eligible punctuation list** (count from the gate 3 output: Gen 25:10, Exo 22:18, Deu 1:4, Jdg 20:17,
1Sa 23:19, 1Ki 7:2, Ezr 7:15, Neh 7:43, Son 3:7, Eze 2:3, Eze 13:2, Eze 13:16, Eze 47:22, Joh 1:45, Act 14:6) —
mostly "of"/name edge-split cells. Those "punctuation" members look like digit-loss side effects, not edition
punctuation; the punct re-freeze (§9.87, expected 583) should come AFTER the repair. Other 9: Gen 41:14, Deu 28:64,
2Ki 15:1, 1Ch 23:9, Pro 6:25, Mat 1:6, Act 2:10, 1Co 10:1, 1Co 10:20.

**Item 3, Joh 14:26:** live = built on all 26 rows (digits included); live reassembles "But the the comforter, holy
spirit," too, and the audit's own --verse on live prints the same HIT. Pre-existing live defect (the unbracketed
`the` at pos 2), untouched by this lane. **Charter §4.10's "rows read `spirit holy,` (no bracket digits)" is wrong —
live carries 1/2 and 1/1; CC's CHECK 3 "half-cured" note repeated it (corrected above).** Under §9.88 it is the
"separate cell defect" case.

**Item 4:** 1,324 cells; 147 inside the item-2 set; 1,177 OUTSIDE in 558 verses = 557 eligible (feed digits by
design, :2397) + **1 `dash` verse — not eligible, so its rows should be the old rows; a lost bracket there is
unexplained.** Every outside cell: `~/edition_upgrade_runs/check4_item4_outside_20261104.tsv`.

## §9.88 final + §9.89 (11/5); code landed 820a6109 + af14ec30; R1 (repair dry run) drafted, held

Ruling chat 11/5: CHECK 4 accepted (99/111; rule + named residue). **§9.88 (JP) final:** one rule for A's restores
and the built-copy repair — a restored cell joins its neighbour's bracket group as it stands in built (no group →
new group of the two, neighbour gp 1), greek_pos = neighbour's + 1; repair scoped to the item-2 set (150 cells /
123 verses), rollback copy `bible_edupg_test_built_pre_digits_<date>.db`, receipt (expect 150 changed, 0 outside),
then per-verse v2 for the 123; residue named reads (1Co 16:19, Joh 8:39, Jer 5:29 if still hit, Pro 7:11,
Pro 14:13, Pro 29:19, Isa 9:17, Isa 60:18, the dash verse). **§9.89 (JP):** Joh 14:26 = pre-existing live defect,
charter 4.10 corrected; fixed by bracket_id/greek_pos correction rows (pin 372 → 376 or actual), inserted with
the repair. Punct re-freeze waits until after the repair. Sequence: code commit → PA pull → R1/R2 → Joh 14:26 rows →
gate 3 re-run → residue rulings → re-pin → gate 1 → retired-row re-run → stage D.

**Where the code differs from the ruling's wording (CC; owed a ruling-chat OK with R1):**
1. **Side-aware.** 20 restored cells sit BEFORE their neighbour — all "of" + a name (17 merge pairs: 1Ki 7:2,
   1Sa 23:19, Deu 1:4, Eze 2:3, Eze 13:2, Eze 13:16, Eze 47:22, Ezr 7:15, Gen 25:10, Jdg 20:17, Neh 7:43, Son 3:7,
   1Co 16:19, Act 2:10, Act 14:6, Joh 1:45, Joh 8:39; 3 edge splits: 1Ch 23:9, 2Ki 15:1, Mat 1:6). "neighbour + 1"
   would read "Name of"; the row takes the neighbour's number and the neighbour moves up one.
2. **Members at/after the slot move up one** — otherwise two members share a number and the order is a tie.
3. **Ungrouped neighbour → the restored row stays/becomes ungrouped, no new group.** Two adjacent ungrouped rows
   already read in position order = the merged cell's order (`reorder_english.py`: a group reads at its first
   member); a new 2-cell group reads the same but would touch many more cells and add group ids.
4. **A row already in place is left alone** (a second pass changes nothing — unit-tested).
5. **"150 changed, 0 outside the set" will not hold as worded:** the plan is every cell the rule changes —
   item-2 cells, restored rows outside item 2 (e.g. the 7 where live had no digits), and shifted members. R1
   prints item-2 in/not-in the plan and the plan cells outside item 2; R2's receipt proves nothing outside the
   PLAN moves (digest of every other words row before/after).

**Code (820a6109, scripts/tests only; af14ec30 display-only):** `_join_neighbour_group` in build_words_from_abp.py,
called by `_restore_merge_pairs` and `_apply_edge_splits`. New `scripts/eu_repair_restore_digits.py` (dry run →
plan TSV; apply needs a byte-identical rollback copy and the same plan, receipts before/after + outside digest;
verify = per-verse v2 + residue print_verse; refuses the live path in every mode). Tests: test_app_transplant 47
(7 fail on the old restores; two old "digits stay feed" assertions updated — one encoded "murder. You shall not"),
new test_eu_repair_restore_digits 6 (2 fail on the old rule), both in the hook + CI lists. CI green on 820a6109.
**Local fingerprint (no dictionary):** eligible / strict_fail / merge-pair / edge-split lists byte-identical; only
line moved `greek_pos/bracket_id changed 935 -> 737`. **Local rehearsal** (A's rows vs B's text through the audit's
diff_verse_v2, 1,606 local merge/edge verses): word-order **131 -> 0** (incl. Pro 7:11, Pro 14:13, Pro 29:19,
Isa 9:17, Isa 60:18, 1Co 16:19, Joh 8:39 locally); punct-position 117 -> 144 — the restored OLD English carries old
punctuation (Lev 11:11 "meats." vs edition "meats,", Rom 6:14 "you;" vs "you.", Deu 29:6 "bread;" vs "bread,"),
§9.73's own normalization. Expect those on gate 3's re-run as new punct members for ruling.

### Block R1 — restore-digits DRY RUN (GATE REF af14ec30, read-only on built and live)
PA pull first (no reload): `cd ~/bible-db && git pull --ff-only && git log -1 --format=%h`
```bash
set +H
( set -uo pipefail
REF=af14ec30
echo "GATE REF ${REF} - R1 restore-digits DRY RUN on the built copy (read-only; live read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "R1 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "R1 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "R1 RESULT: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; LIVE=~/bible-db/bible.db
P=~/edition_upgrade_runs/restore_digits_plan_20261105.tsv; O=~/edition_upgrade_runs/check4_item4_outside_20261104.tsv
for f in "$B" "$LIVE" "$O"; do [ -f "$f" ] || { echo "R1 RESULT: STOP - missing: $f"; exit 1; }; done
[ -e "$P" ] && { echo "R1 RESULT: STOP - plan file already exists: $P (move it aside first)"; exit 1; }
python3 tests/test_app_transplant.py || { echo "R1 RESULT: STOP - build tests failed"; exit 1; }
python3 tests/test_eu_repair_restore_digits.py || { echo "R1 RESULT: STOP - repair tests failed (a repair that cannot fail is void)"; exit 1; }
PYTHONIOENCODING=utf-8 python3 scripts/eu_repair_restore_digits.py --dry-run "$B" --out "$P" --live "$LIVE"; r=$?
echo "--- the non-eligible 'dash' verse(s) from CHECK 4 item 4 (named for the R2 residue read) ---"
awk -F'\t' 'NR>1 && $5=="dash" {print "   " $1 " " $2 ":" $3 " position " $4}' "$O"
[ "$r" -eq 0 ] && echo "R1 RESULT: PLAN WRITTEN - nothing written to any db; the plan goes to the ruling chat before R2" || echo "R1 RESULT: STOP - dry run exit $r"
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/restore_digits_R1_20261105.log; echo "exit=${PIPESTATUS[0]}"
```
Tested end to end in a throwaway checkout at af14ec30 on made-up built/live copies holding all 1,456 listed verses:
47 + 6 tests OK; plan 1,688 cells / 1,456 verses (restored 1,668, shifted 20 = the 20 "of"+name cells); every
live-has/copy-lacks cell in the plan; dash line printed; a second run STOPs on the existing plan file.
Expected on PA: tests OK; `RESTORE-DIGITS PLAN: N cells / V verses - restored R - shifted S - plan sha256 xxxxxxxx`
(N not forecast); item-2 150 cells / 123 verses, NOT in the plan expected 0 (any listed = a neighbour cell, or a
cell whose neighbour is ungrouped in built — reads in place); `R1 RESULT: PLAN WRITTEN`; exit=0. R2 (rollback copy
→ apply with this plan → receipt → verify + residue) is drafted after the ruling chat reads R1.

## R1 ran 11/5 02:23 — STOP on CC's own same-word check (Gen 25:10); fixed 9fbef17f; R1 re-run drafted, held

Ruling chat 11/5: §9.88 amended to the implemented rule (side-aware; displaced members shift; no new group; idempotent;
receipt = exactly R1's plan, nothing outside it). Code 820a6109 / af14ec30 accepted; CI green on both (af14ec30
confirmed 11/5). R1 cleared at af14ec30.

**R1 result (`restore_digits_R1_20261105.log`, PA HEAD c294a9e2):** tests 47 OK / 6 OK; then
`RESTORE-DIGITS STOP: Gen 25:10: Strong's base at positions 11/12 is 3588/H2845, the frozen list says 3588/*`;
dash verse = **Gen 46:26 position 19**; exit=1. No plan file written (the plan is written only after the check).
**Cause = CC's check, not the data:** the frozen list holds the BUILD-time strongs_base; import_tipnr later binds a
proper noun's strongs_base `*` to its H-number and leaves `strongs` as `*` (`import_tipnr.py:719`; other later
writers of Strong's: fix_subject_reorder.py:112, fill_blank_strongs.py:123, …). The check also stopped at the first
miss, so one run could not show them all.
**Fix 9fbef17f (scripts/tests):** `same_word` — a listed position matches if the frozen value equals the copy's bare
strongs_base, its strongs, or strongs without a dotted suffix; EVERY listed position is checked first, each miss
named ("NOT THE LISTED WORD: …"), then STOP with no plan. Tests 7 (2 new fail on the old check). Block re-tested at
9fbef17f: PN rows rebound to H-numbers → plan written, same plan sha d4fcbad8 as before; one listed position holding
another word → named, no plan, exit 1.

### Block R1 (re-run) — GATE REF 9fbef17f, read-only on built and live
PA pull first (no reload): `cd ~/bible-db && git pull --ff-only && git log -1 --format=%h`
```bash
set +H
( set -uo pipefail
REF=9fbef17f
echo "GATE REF ${REF} - R1 restore-digits DRY RUN on the built copy (read-only; live read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "R1 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "R1 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "R1 RESULT: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; LIVE=~/bible-db/bible.db
P=~/edition_upgrade_runs/restore_digits_plan_20261105.tsv; O=~/edition_upgrade_runs/check4_item4_outside_20261104.tsv
for f in "$B" "$LIVE" "$O"; do [ -f "$f" ] || { echo "R1 RESULT: STOP - missing: $f"; exit 1; }; done
[ -e "$P" ] && { echo "R1 RESULT: STOP - plan file already exists: $P (move it aside first)"; exit 1; }
python3 tests/test_app_transplant.py || { echo "R1 RESULT: STOP - build tests failed"; exit 1; }
python3 tests/test_eu_repair_restore_digits.py || { echo "R1 RESULT: STOP - repair tests failed (a repair that cannot fail is void)"; exit 1; }
PYTHONIOENCODING=utf-8 python3 scripts/eu_repair_restore_digits.py --dry-run "$B" --out "$P" --live "$LIVE"; r=$?
echo "--- the non-eligible 'dash' verse(s) from CHECK 4 item 4 (named for the R2 residue read) ---"
awk -F'\t' 'NR>1 && $5=="dash" {print "   " $1 " " $2 ":" $3 " position " $4}' "$O"
[ "$r" -eq 0 ] && echo "R1 RESULT: PLAN WRITTEN - nothing written to any db; the plan goes to the ruling chat before R2" || echo "R1 RESULT: STOP - dry run exit $r"
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/restore_digits_R1_20261105.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: tests 47 OK / 7 OK; no "NOT THE LISTED WORD" lines (any = named for ruling, no plan); the plan lines and
`RESTORE-DIGITS PLAN: …`; item-2 "NOT in the plan" 0; `Gen 46:26 position 19`; `R1 RESULT: PLAN WRITTEN`; exit=0.

## R1 re-run (11/5 02:34) — PLAN WRITTEN; CC read; R2 not drafted (ruling chat reads R1 first)

`restore_digits_R1_20261105.log`, REF 9fbef17f, PA HEAD c71ce26f; tests 47 OK / 7 OK; no NOT THE LISTED WORD lines.
`RESTORE-DIGITS PLAN: 389 cells / 133 verses - restored 117 - shifted 272 - plan sha256 694e1564`; dash verse Gen 46:26
p19; exit=0. **Item-2: 150 cells / 123 verses - in the plan 105 - NOT in the plan 45** (expected 0). Plan cells
outside item 2: 284 in 132 verses.

**CC read (from the printed lines + the frozen lists; nothing new run on PA):**
- **The 45 not in the plan = 23 verses where BOTH cells of the pair are unbracketed on built** (live had them
  bracketed): 18 of the 20 "of" + name pairs, both cells (all but 1Co 16:19 and Joh 8:39, which are in the plan) =
  36 cells, plus Exo 22:18, Deu 28:64, 1Co 10:1, 1Co 10:20 (both cells) and Gen 41:14 (one cell) = 9. Ruled point (3): an ungrouped neighbour leaves the restored
  cell ungrouped; two adjacent unbracketed cells read in position order. None of the 23 was a gate-3 word-order hit,
  so they already read in order. They are 23 of CHECK 4's 24 "non-hit exposure" verses (the 24th, Pro 6:25, is in
  the plan). **Correction to CHECK 4's note:** the 15 of them on §9.87's punctuation list are NOT digit-loss side
  effects — the repair does not touch them; their punctuation difference is the restored OLD English (Gen 25:10 old
  "Heth." vs edition "Heth —"), the same class as the ~27 rehearsal verses. They stay for the §9.87 re-freeze. The
  ruling's "the 24 item-2 verses outside gate 3 are covered by the repair" holds for Pro 6:25 only.
- **22 plan verses carry shifted cells only** (the restored cell already held its slot but shared the number with
  another member). By position: 18 read the same after (restored cell already first among the tied — Gen 17:5,
  Exo 23:3, Lev 18:26, Lev 19:4, Num 11:17, Num 18:22, 1Sa 25:31, 2Ch 26:18, Psa 78:10, Psa 125:1, Pro 9:13,
  Pro 10:3, Pro 14:22, Isa 2:4, Isa 10:20, Jer 46:28, Luk 11:46, 1Co 16:7 — renumbering only); **4 change reading =
  the gate-3 residue Pro 7:11, Pro 14:13, Pro 29:19, Isa 9:17** (restored verb moves ahead of the word it was tied
  with). Isa 60:18 (5th residue) is cured by its restored cell moving 1/4 → 1/3 next to "shall not".
- Restored cells that move off live's number without a reading change: Isa 1:24 (1/5 → 1/3, no member between),
  Num 16:9 (tie 3/3 → 4), Pro 6:25 and Jer 49:36 (gp none → last-in-group number). Jer 5:29, Joh 8:39 and 1Co 16:19
  get the side-aware placement (the "of" ahead of the name) = their gate-3 hits.
- All of this is a reading of the plan, not a result: R2's verify (per-verse v2 on the repaired copy) is the proof.
  For R2, the 23 untouched item-2 verses go in verify's `--residue` list (rows vs text printed in full) so the 123
  are each shown, with the named residue + Gen 46:26.

## R1 accepted; R2 (apply + verify) CLEARED CONDITIONALLY, drafted (11/5)

Ruling chat 11/5: R1 accepted (plan 694e1564, 389 / 133; the 45 outside the plan are §9.88 point 3, no action; CHECK 4
note correction accepted; the 15 punct verses stay for the §9.87 re-freeze). R2 cleared conditionally — JP runs it
without returning if it matches the spec: ref 9fbef17f; rollback copy `bible_edupg_test_built_pre_digits_20261105.db`
first, byte-identical; apply only plan 694e1564 (sha-checked); receipt APPLIED 389 - before 389/389 - after 389/389 -
other rows unchanged (count); v2 word-order over all 1,456 listed verses = 0; full prints of the 123 lost-digit verses,
the residue (Pro 7:11, Pro 14:13, Pro 29:19, Isa 9:17, Isa 60:18, Jer 5:29, Joh 8:39, 1Co 16:19) and Gen 46:26 pos 19;
any receipt mismatch = self-rollback, STOP.

Block notes: the receipt check is the exact line `APPLIED 389 cells - before-match 389/389 - after-match 389/389 -
other rows 625,920 digest … (unchanged)` (625,920 = gate 1's 626,309 words − 389); anything else → restore from the
rollback copy (cp + cmp) and STOP. A `-journal` file beside the built copy STOPs the block before anything starts, and
is moved aside (never deleted) before a restore, so SQLite cannot replay it onto the restored file. The print list =
123 + Pro 7:11, Pro 14:13, Pro 29:19, Isa 9:17, Isa 60:18 + Gen 46:26 (129; Jer 5:29, Joh 8:39, 1Co 16:19 are in the
123), cross-checked = CHECK 4's 99 LOST + R1's 23 untouched + Pro 6:25. Gen 46:26 pos 17–21 printed from built and
live (sqlite3 -readonly). Tested at 9fbef17f on made-up copies: good run → APPLIED + verify, exit 0; receipt mismatch
→ restored byte-identical, exit 1; rollback copy present → STOP, nothing done; wrong plan → STOP, nothing done.

### Block R2 — restore-digits APPLY + VERIFY (GATE REF 9fbef17f; writes the built copy only)
```bash
set +H
( set -uo pipefail
REF=9fbef17f
echo "GATE REF ${REF} - R2 restore-digits APPLY + VERIFY on the built copy (writes the built copy only; live read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "R2 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "R2 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "R2 RESULT: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; RB=~/bible-db/bible_edupg_test_built_pre_digits_20261105.db; LIVE=~/bible-db/bible.db
P=~/edition_upgrade_runs/restore_digits_plan_20261105.tsv
for f in "$B" "$P" "$LIVE"; do [ -f "$f" ] || { echo "R2 RESULT: STOP - missing: $f"; exit 1; }; done
[ -e "$RB" ] && { echo "R2 RESULT: STOP - rollback copy already exists: $RB (nothing done)"; exit 1; }
[ -e "$B-journal" ] && { echo "R2 RESULT: STOP - a journal file sits beside the built copy: $B-journal (nothing done)"; exit 1; }
[ "$(sha256sum < "$P" | cut -c1-8)" = 694e1564 ] || { echo "R2 RESULT: STOP - plan file is not R1's (694e1564...) (nothing done)"; exit 1; }
cp -p "$B" "$RB" && cmp -s "$B" "$RB" || { echo "R2 RESULT: STOP - rollback copy not byte-identical to the built copy (built copy untouched)"; exit 1; }
echo "rollback copy: $RB - byte-identical to the built copy ($(stat -c%s "$RB") bytes) - plan 694e1564"
out=$(PYTHONIOENCODING=utf-8 python3 scripts/eu_repair_restore_digits.py --apply "$B" --rollback "$RB" --plan "$P" 2>&1); a=$?
echo "$out"
ok=0; echo "$out" | grep -qF "RESTORE-DIGITS APPLY: APPLIED 389 cells - before-match 389/389 - after-match 389/389 - other rows 625,920 digest" && echo "$out" | grep -qF "(unchanged)" && ok=1
if [ "$a" -ne 0 ] || [ "$ok" -ne 1 ]; then
  [ -e "$B-journal" ] && mv "$B-journal" "$B-journal.stale_$(date -u +%H%M%S)" && echo "moved aside a leftover journal file"
  cp -p "$RB" "$B" && cmp -s "$RB" "$B" && echo "R2 RESULT: STOP - receipt not as cleared (apply exit $a); built copy RESTORED from the rollback copy, byte-identical" || echo "R2 RESULT: STOP - receipt not as cleared AND THE RESTORE DID NOT VERIFY - do nothing else, bring this here"
  exit 1
fi
RES="Gen 9:4,Gen 24:8,Gen 25:10,Gen 37:24,Gen 41:14,Exo 22:18,Exo 22:21,Exo 22:29,Lev 11:11,Lev 12:4,Lev 18:6,Lev 18:18,Lev 19:28,Lev 21:11,Lev 22:4,Lev 22:12,Lev 22:21,Lev 23:7,Lev 23:21,Lev 23:35,Lev 23:36,Lev 25:4,Num 1:49,Num 6:6,Num 8:26,Num 9:12,Deu 1:4,Deu 7:3,Deu 10:16,Deu 15:2,Deu 18:2,Deu 28:12,Deu 28:50,Deu 28:64,Deu 29:6,Jdg 12:1,Jdg 20:17,1Sa 23:19,2Sa 11:13,2Sa 20:3,1Ki 2:28,1Ki 7:2,2Ki 15:1,1Ch 23:9,2Ch 29:7,Ezr 7:15,Ezr 10:6,Neh 5:12,Neh 6:1,Neh 7:43,Job 2:10,Job 10:19,Job 11:11,Job 16:5,Job 19:22,Job 21:14,Job 23:6,Job 34:27,Psa 32:6,Psa 51:17,Psa 56:3,Psa 69:5,Psa 94:14,Psa 107:4,Psa 119:141,Psa 119:153,Psa 119:155,Pro 1:25,Pro 3:32,Pro 5:6,Pro 6:25,Pro 10:30,Son 3:7,Isa 1:11,Isa 1:12,Isa 9:19,Isa 13:10,Isa 15:6,Isa 42:8,Isa 53:9,Isa 57:11,Isa 57:20,Jer 5:22,Jer 5:29,Jer 9:9,Jer 13:1,Jer 44:17,Jer 45:3,Eze 2:3,Eze 4:14,Eze 12:12,Eze 12:13,Eze 13:2,Eze 13:16,Eze 16:4,Eze 16:49,Eze 18:6,Eze 18:8,Eze 18:13,Eze 18:17,Eze 47:22,Dan 2:44,Amo 5:22,Amo 5:23,Mat 1:6,Luk 8:27,Joh 1:45,Joh 2:3,Joh 4:17,Joh 8:39,Joh 8:43,Act 2:10,Act 14:6,Act 27:31,Rom 6:14,1Co 7:10,1Co 7:25,1Co 10:1,1Co 10:20,1Co 16:19,Gal 4:21,1Ti 5:18,2Ti 4:3,Pro 7:11,Pro 14:13,Pro 29:19,Isa 9:17,Isa 60:18,Gen 46:26"
[ "$(echo "$RES" | tr ',' '\n' | sort -u | grep -c .)" -eq 129 ] || { echo "R2 RESULT: STOP - print list is not the 123 + 5 residue + Gen 46:26 (repair stays applied; rollback copy kept)"; exit 1; }
echo "--- verify: v2 over all 1,456 listed verses + full prints of the 123 lost-digit verses, the residue, Gen 46:26 ---"
vout=$(PYTHONIOENCODING=utf-8 python3 scripts/eu_repair_restore_digits.py --verify "$B" --plan "$P" --residue "$RES" 2>&1); v=$?
echo "$vout"
echo "--- Gen 46:26 positions 17-21 (pos 19 = the dash residue cell), built then live (read-only) ---"
for D in "$B" "$LIVE"; do echo "  $(basename "$D"):"; sqlite3 -readonly -separator ' | ' "$D" "SELECT w.position, w.english, w.bracket_id, w.greek_pos, w.strongs FROM words w JOIN verses v ON w.verse_id = v.id WHERE v.book = 'Gen' AND v.chapter = 46 AND v.verse = 26 AND w.position BETWEEN 17 AND 21 ORDER BY w.position" | sed 's/^/    /'; done
if [ "$v" -eq 0 ] && echo "$vout" | grep -qF "word-order on listed verses 0"; then
  echo "R2 RESULT: APPLIED 389 + VERIFIED - word-order on the 1,456 listed verses 0 - rollback copy kept - output to the ruling chat"; exit 0
fi
echo "R2 RESULT: APPLIED 389 - verify did NOT read word-order 0 (exit $v; named above) - repaired copy and rollback copy both kept - output to the ruling chat"; exit 1
) 2>&1 | tee ~/edition_upgrade_runs/restore_digits_R2_20261105.log; echo "exit=${PIPESTATUS[0]}"
```
Expected: rollback copy line (byte-identical, plan 694e1564); `RESTORE-DIGITS APPLY: APPLIED 389 cells - before-match
389/389 - after-match 389/389 - other rows 625,920 digest X -> X (unchanged)`; per-verse v2 lines for the 133 plan
verses; `all 1456 listed verses: {...}` with no word-order list; 129 full prints; Gen 46:26 pos 17–21 built + live;
`RESTORE-DIGITS VERIFY: plan verses 133 - clean … - word-order on listed verses 0`; `R2 RESULT: APPLIED 389 +
VERIFIED …`; exit=0. Punctuation-only hits on the plan verses are expected (old-English punctuation, §9.87 re-freeze).

## R2 RAN (11/6 14:49 UTC) — APPLIED 389 + VERIFIED; held for the ruling chat

`restore_digits_R2_20261105.log`, REF 9fbef17f, PA HEAD c71ce26f. Rollback copy
`bible_edupg_test_built_pre_digits_20261105.db` byte-identical (451,964,928 bytes), plan 694e1564.
`RESTORE-DIGITS APPLY: APPLIED 389 cells - before-match 389/389 - after-match 389/389 - other rows 625,920 digest
9035d8f6 -> 9035d8f6 (unchanged)`. Verify: plan verses 133 — clean 106, punct-position 27; **all 1,456 listed
verses {clean 1,312, punct-position 144} — word-order 0**; `RESTORE-DIGITS VERIFY: plan verses 133 - clean 106 -
word-order on listed verses 0`; `R2 RESULT: APPLIED 389 + VERIFIED …`. (The pasted output ends on that line; the
`exit=` line after the tee is not in the paste — the RESULT line prints only on the exit-0 path.)

**CC read:**
- **Residue all clean:** Pro 7:11, Pro 14:13, Pro 29:19, Isa 9:17, Isa 60:18, Jer 5:29, Joh 8:39, 1Co 16:19.
- **27 plan verses punct-position** = the restored OLD English's punctuation/capitals vs the edition prose (meats. /
  meats,; You / you; dash placement Num 8:26, Eze 18:17, Lev 19:4, Gal 4:21, Deu 28:12). Lev 18:21 and Deu 28:12 show
  insert/delete word lines but v2 files them punct-position, which by its rule (`audit_reassembly_diff.py:210`) means
  the words with punctuation stripped are in the text's order. → §9.87 re-freeze.
- **The 23 untouched item-2 verses:** 8 clean (Gen 41:14, Deu 28:64, 2Ki 15:1, 1Ch 23:9, Mat 1:6, Act 2:10, 1Co 10:1,
  1Co 10:20); 15 punct-position = exactly the 15 §9.87 verses (Gen 25:10 Heth., Exo 22:18 You, Deu 1:4, Jdg 20:17,
  1Sa 23:19, 1Ki 7:2, Ezr 7:15, Neh 7:43, Son 3:7, Eze 2:3, Eze 13:2, Eze 13:16, Eze 47:22, Joh 1:45, Act 14:6).
- **Gen 46:26 (dash residue) = a lane-③ hand repair not yet applied, not a defect:** built pos 19 "of Jacob's sons —"
  (no digits) + pos 20 blank `*` is EXACTLY the `old_eng` state of `scripts/lane3_star_fixes2.json` "Gen 46:26"; live
  holds its `new` state ("sons —" 1/2, "of Jacob's" 1/1). Lane-3 repairs run at /rebuild-words step 8b.2a
  (rebuild-words.md:242; DESIGN §9.67) = stage D, not yet run on the built copy. The verse already reads right
  (v2 clean); the word-click on "of Jacob's" is what 8b.2a restores. No lane-3 verse (18) is on the merge-pair /
  edge-split lists, so the repair cannot have disturbed 8b.2a's strict before-check.
- Joh 14:26 untouched (not listed) — §9.89 correction rows are the next step.

## R2 accepted; §9.89 Joh 14:26 rows (code e777f965) + gate 3 re-run drafted, held (11/6)

Ruling chat 11/6: R2 ACCEPTED (389/389, other rows 625,920 unchanged, word-order 0 on 1,456, residue 8/8). Rollback copy
`bible_edupg_test_built_pre_digits_20261105.db` kept until the swap. Gen 46:26 pos 19 = lane ③ pending at 8b.2a (not
residue). Lev 18:21 / Deu 28:12 punct filing per :210 accepted. 27 + 15 punct-only verses → §9.87 re-freeze. GO §9.89.

**Which cells (CC):** ABP (`abp_texts`, diagnosis-grade) reads "But theG3588 G1161 comforter,G3875 theG3588 [2spirit
G3588 1holy]" — the second "the" comes AFTER "comforter,". The rows (live = built, CHECK 4) hold pos 2 "the" (3588)
before pos 3 "comforter," (3875), both undigited. Two digit-only fixes tested through the v2 reorder port on the 26
real rows: **A — pos 3 joins pos 0/1's bracket 4 as its 3rd word → "But the comforter, the holy spirit," = clean**;
B — a new 2-word group for pos 2+3 (the Act 7:3 shape, 4 rows) → "comforter the," (the group's comma floats onto
"the") = punct-position. A chosen: **2 rows, pin 372 → 374** (not 376).
**Code e777f965 (scripts/tests):** two ENTRIES in `build_abp_corrections.py` (Joh 14:26 pos 3 bracket_id None → "4",
greek_pos None → "3", ledger `S-joh14:26`, reason `_JOH1426_REASON`), next to the S10 Act 7:3 rows. New test
`test_correction_reorder_rows.py` (3: rows have the ruled shape; the unfixed verse is still a word-order hit; with
the rows it reads clean — 2 fail without the rows), in hook + CI lists.

**Block J** (chained; each write runs only on the previous step's exact output): row test → BEFORE (counts both
copies, Joh 14:26 pos 0–7 on built, the audit's --verse) → seed dry run on src and built, each must be exactly the 2
Joh 14:26 lines with `cell=source` and "would insert 2" → seed --apply src then built, each "active rows … now: 374" →
`apply_abp_corrections.py <built> --only words` dry run must read "would apply 2 · already-applied 248 ·
LOUD-SKIPPED 0" (248 = the 372 active minus 124 verses.text, from the 11/4 member file; no active digit row sits on a
verse R2 changed) → --apply, same receipt → AFTER (counts, rows, --verse must read clean). The seeder's other ~57
entries print "not duplicated"/flag lines on these copies (cells changed since seeding) — expected noise, filtered;
its exit code is not used. Rollback if needed: delete the two `S-joh14:26` rows on each copy and set built pos 3 back to
NULL/NULL. Tested on made-up copies (372 active, 248 already applied): DONE; a second run STOPs at the seed dry run
("would insert 0"), nothing written.
**Block G3R** (read-only, after J): needs J's log to say DONE; same inputs/tests/controls as gate 3; AS DECLARED only if
exit 1 with exactly `word-order 0 - content-other 1 - dup-gloss 0 - Joh 14:26 clean - new on non-eligible 0` and the
content-other line is Job 3:3. Tested: AS DECLARED on a made-up copy; STOP without J's log.
Cert check 4 on built reads 374 vs pin 372 until the re-pin (the sequence's next code step).

### Block J — Joh 14:26 correction rows (GATE REF e777f965)
PA pull first (no reload): `cd ~/bible-db && git pull --ff-only && git log -1 --format=%h`
```bash
set +H
( set -uo pipefail
REF=e777f965
echo "GATE REF ${REF} - J Joh 14:26 correction rows (sec 9.89): insert on src + built, apply on built - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "J RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "J RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "J RESULT: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; SRC=~/bible-db/bible_edupg_test_20261101.db
for f in "$B" "$SRC"; do [ -f "$f" ] || { echo "J RESULT: STOP - missing: $f"; exit 1; }; [ -e "$f-journal" ] && { echo "J RESULT: STOP - journal file beside $f"; exit 1; }; done
python3 tests/test_correction_reorder_rows.py || { echo "J RESULT: STOP - the row test failed"; exit 1; }
counts() { sqlite3 -readonly "$1" "SELECT group_concat(status || ' ' || n, ' / ') FROM (SELECT status, count(*) n FROM abp_corrections GROUP BY status ORDER BY status)"; }
rows() { sqlite3 -readonly -separator ' | ' "$B" "SELECT w.position, w.english, w.bracket_id, w.greek_pos, w.strongs FROM words w JOIN verses v ON w.verse_id = v.id WHERE v.book = 'Joh' AND v.chapter = 14 AND v.verse = 26 AND w.position <= 7 ORDER BY w.position" | sed 's/^/    /'; }
echo "--- BEFORE: corrections src [$(counts "$SRC")] built [$(counts "$B")]; Joh 14:26 pos 0-7 on built:"; rows
PYTHONIOENCODING=utf-8 python3 scripts/audit_reassembly_diff.py "$B" --v2 --verse "Joh 14:26"
L1="  -> Joh 14:26 pos 3 bracket_id: None -> '4'  [S-joh14:26]  cell=source"; L2="  -> Joh 14:26 pos 3 greek_pos: None -> '3'  [S-joh14:26]  cell=source"
for D in "$SRC" "$B"; do
  o=$(PYTHONIOENCODING=utf-8 python3 scripts/build_abp_corrections.py "$D" 2>&1)
  echo "--- seed dry run on $(basename "$D"):"; echo "$o" | grep -E "^  -> |would insert" | sed 's/^/  /'
  grep -qF "would insert 2, " <<< "$o" && [ "$(echo "$o" | grep -c '^  -> ')" -eq 2 ] && grep -qF "$L1" <<< "$o" && grep -qF "$L2" <<< "$o" || { echo "J RESULT: STOP - seed dry run on $(basename "$D") is not exactly the 2 Joh 14:26 rows (nothing written)"; exit 1; }
done
for D in "$SRC" "$B"; do
  o=$(PYTHONIOENCODING=utf-8 python3 scripts/build_abp_corrections.py "$D" --apply 2>&1)
  echo "$o" | grep -E "^  -> |written" | sed 's/^/  /'
  grep -qF "active rows in table now: 374" <<< "$o" && [ "$(echo "$o" | grep -c '^  -> ')" -eq 2 ] || { echo "J RESULT: STOP - insert on $(basename "$D") not as expected (src done first; see above)"; exit 1; }
done
o=$(python3 scripts/apply_abp_corrections.py "$B" --only words 2>&1)
echo "--- apply dry run on built:"; echo "$o" | grep -E "Joh 14:26|summary|SKIP" | sed 's/^/  /'
grep -qF "would apply 2 " <<< "$o" && grep -qF "already-applied 248 " <<< "$o" && grep -qF "LOUD-SKIPPED 0" <<< "$o" && [ "$(echo "$o" | grep -c 'Joh 14:26 pos 3 .*would apply')" -eq 2 ] || { echo "J RESULT: STOP - apply dry run not exactly 2 / 248 / 0 (rows inserted on both copies, cells NOT written)"; exit 1; }
o=$(python3 scripts/apply_abp_corrections.py "$B" --only words --apply 2>&1)
echo "$o" | grep -E "Joh 14:26|summary" | sed 's/^/  /'
grep -qF "applied 2 " <<< "$o" && grep -qF "already-applied 248 " <<< "$o" && grep -qF "LOUD-SKIPPED 0" <<< "$o" || { echo "J RESULT: STOP - apply receipt not 2 / 248 / 0"; exit 1; }
echo "--- AFTER: corrections src [$(counts "$SRC")] built [$(counts "$B")]; Joh 14:26 pos 0-7 on built:"; rows
v=$(PYTHONIOENCODING=utf-8 python3 scripts/audit_reassembly_diff.py "$B" --v2 --verse "Joh 14:26" 2>&1); echo "$v"
grep -qF "RESULT: clean reassembly (no hit)" <<< "$v" && echo "J RESULT: DONE - 2 rows on src + built (374 active each), applied on built, Joh 14:26 reads clean" || { echo "J RESULT: STOP - Joh 14:26 does not read clean after the apply"; exit 1; }
) 2>&1 | tee ~/edition_upgrade_runs/joh1426_rows_20261106.log; echo "exit=${PIPESTATUS[0]}"
```

### Block G3R — gate 3 re-run (GATE REF e777f965, read-only; after J)
```bash
set +H
( set -uo pipefail
REF=e777f965
echo "GATE REF ${REF} - GATE 3 RE-RUN v2 member diff on the built copy after R2 + J (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "GATE3 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "GATE3 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "GATE3 RESULT: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
F=tests/fixtures/reassembly/punct_members_live_20261030.txt
E=~/edition_upgrade_runs/step5_eligible_20261101.tsv
J=~/edition_upgrade_runs/joh1426_rows_20261106.log
for f in "$B" "$F" "$E" "$J"; do [ -f "$f" ] || { echo "GATE3 RESULT: STOP - missing: $f"; exit 1; }; done
[ "$(sha256sum < "$F" | cut -d' ' -f1)" = 2b0f4cc43efc6dd423d934d4633727f69fcb6f45f894727b3a634265b68a941f ] || { echo "GATE3 RESULT: STOP - frozen punct file is not the committed one"; exit 1; }
[ "$(sha256sum < "$E" | cut -c1-8)" = e540d34d ] || { echo "GATE3 RESULT: STOP - eligible file is not step 5's (e540d34d...)"; exit 1; }
grep -qF "J RESULT: DONE" "$J" || { echo "GATE3 RESULT: STOP - block J has not finished clean ($J)"; exit 1; }
echo "frozen punct file: $(grep -c . "$F") members (sha 2b0f4cc4) - eligible e540d34d - block J done"
python3 tests/test_reorder_port.py || { echo "GATE3 RESULT: STOP - reorder port drifted from the JS baseline"; exit 1; }
python3 tests/test_reassembly_member_diff.py || { echo "GATE3 RESULT: STOP - the member diff's own tests failed"; exit 1; }
python3 scripts/audit_reassembly_diff.py --controls --v2 || { echo "GATE3 RESULT: STOP - v2 controls did not fire"; exit 1; }
out=$(PYTHONIOENCODING=utf-8 python3 scripts/audit_reassembly_diff.py "$B" --v2 --punct-members "$F" --eligible "$E" 2>&1); r=$?
echo "$out"
if [ "$r" -eq 1 ] && grep -qF "V2 MEMBER DIFF: FAIL - word-order 0 - content-other 1 - dup-gloss 0 - Joh 14:26 clean - new on non-eligible 0 |" <<< "$out" && grep -qF "[content-other] Job 3:3 " <<< "$out"; then
  echo "GATE3 RESULT: AS DECLARED - word-order 0 - Joh 14:26 clean - new on non-eligible 0 - the one content-other is Job 3:3 (FEED, sec 9.87) - the sec 9.52 lists above go to the re-freeze"; exit 0
fi
echo "GATE3 RESULT: NOT AS DECLARED (member diff exit $r) - named above"; exit 1
) 2>&1 | tee ~/edition_upgrade_runs/gate3_rerun_20261106.log; echo "exit=${PIPESTATUS[0]}"
```

## J DONE + G3R AS DECLARED (11/6 15:09–15:10 UTC); re-pin 372 → 374 chain drafted, held

**J** (`joh1426_rows_20261106.log`, REF e777f965, PA HEAD 6da053c9): BEFORE active 372 / retired 23 / superseded 6 on both
copies + the Joh 14:26 hit; seed dry runs exactly the 2 rows on both ("would insert 2, skip 57"); inserts "now: 374" ×2;
apply `would apply 2 · already-applied 248 · LOUD-SKIPPED 0` then `applied 2 · …`; AFTER 374 / 23 / 6, pos 3
`comforter, | 4 | 3`, `RESULT: clean reassembly (no hit)`; `J RESULT: DONE`, exit=0.
**G3R** (`gate3_rerun_20261106.log`): tests/controls green; `V2 MEMBER DIFF: FAIL - word-order 0 - content-other 1 -
dup-gloss 0 - Joh 14:26 clean - new on non-eligible 0 | to ruling: gone 24 - new on eligible 390 - changed ops 12 -
unchanged 205`; content-other = Job 3:3; `GATE3 RESULT: AS DECLARED`, exit=0.

**§9.52 re-freeze count = 607** punct-position members on the built copy = unchanged 205 + new-on-eligible 390 +
changed-ops 12 (gone 24 drop out). §9.87's 583 (first gate 3) → 607 = **+24**, reconciled member by member against the
two printed lists: **23 new-on-eligible** from R2 (restored old-English punctuation: 1Co 7:25, 1Ti 5:18, Deu 15:2,
Deu 28:12, Deu 29:6, Eze 18:8, Eze 18:13, Eze 18:17, Gal 4:21, Isa 13:10, Jer 13:1, Job 34:27, Joh 4:17, Lev 7:26,
Lev 11:11, Lev 12:4, Lev 18:21, Lev 21:11, Lev 23:36, Lev 25:4, Lev 25:37, Neh 5:12, Rom 6:14) + **Num 8:26** (gone →
unchanged: after R2 its dash op equals the frozen one again; gone 25 → 24, unchanged 204 → 205). The other R2
punct verses were members already (Jer 49:36, Lev 19:4, Psa 78:10 — in the first 367). Changed-ops: same 12.

**Re-pin chain (ruling 11/6: same C3a/C3b/C4 shape, then gate 1 + retired-row re-runs):**
- **C3a′** (PA, read-only on built; writes 2 files): one-off `repin_dump_20261106.py` (sha c463ee4a…) — active ingest
  = the committed 372 file + exactly the two `S-joh14:26` rows; retired 23; non-ingest active 0; dump bytes = the local
  derivation (372 file + 2 keys, sha256 **446fee35…**), else nothing written. Tested: good → file byte-identical to
  local; missing row / stray row / 22 retired / file exists → STOP, nothing written; whole block end to end on a
  made-up copy.
- **C3b** (local): scp both files to `tests/fixtures/corrections/`, sha = 446fee35…, ONE commit: cert_invariants PINS
  `abp_corrections_active` 372 → 374 (comment names the new file + sha) + `abp_corrections_active_built_20261106.txt`
  + `.sha256`. Planned diff: `3 files changed, 376 insertions(+), 1 deletion(-)`. Old 20261104 file kept (history).
- **C3c** (PA): pull, no reload. **C4′** gate 1 (pin 374; 7/7 expected, words 626,309 unchanged — R2/J wrote digits
  only) and **C5′** retired-row re-run (PASS 23/23, 18/5 expected — no retired row is on a verse R2/J touched), both
  REF = the C3b commit, filled in when it exists.

### Block C3a′ — RE-PIN DUMP 374 (GATE REF e777f965; read-only on built, writes 2 files)
```bash
set +H
( set -uo pipefail
REF=e777f965
echo "GATE REF ${REF} - C3a RE-PIN DUMP 374 built active corrections (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "REPIN DUMP: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "REPIN DUMP: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; O=~/edition_upgrade_runs
[ -f "$B" ] || { echo "REPIN DUMP: STOP - missing: $B"; exit 1; }
grep -qF "J RESULT: DONE" "$O/joh1426_rows_20261106.log" || { echo "REPIN DUMP: STOP - block J has not finished clean"; exit 1; }
for f in "$O/abp_corrections_active_built_20261106.txt" "$O/abp_corrections_active_built_20261106.txt.sha256"; do [ -e "$f" ] && { echo "REPIN DUMP: STOP - already exists: $f"; exit 1; }; done
P=$O/repin_dump_20261106.py
cat > "$P" <<'PY'
"""Re-pin dump 372 -> 374 (one-off, read-only) - DESIGN 9.89. Lists the built copy's active ingest correction
rows (the rows cert check 4 counts) in the member-file format and writes the file + .sha256 ONLY if:
  - active ingest rows = the committed 372-row file (tests/fixtures/corrections/abp_corrections_active_built_20261104.txt)
    plus exactly the two S-joh14:26 rows, nothing else
  - retired total 23, no active row outside 'ingest'
  - the bytes written equal the independent local derivation (372 file + the 2 keys, sha256 446fee35...)
The database is opened read-only; the only writes are the two files in OUT_DIR.

Usage: python3 repin_dump_20261106.py <built.db> <repo> <out_dir>
"""
import hashlib
import os
import sqlite3
import sys

BUILT, REPO, OUT_DIR = sys.argv[1:4]
OLD_REL = "tests/fixtures/corrections/abp_corrections_active_built_20261104.txt"
OLD_SHA = "80db1c35"
NEW = {("Joh", 14, 26, 3, "bracket_id", "S-joh14:26"), ("Joh", 14, 26, 3, "greek_pos", "S-joh14:26")}
LOCAL_SHA = "446fee35b4080e522e5b2af19aca9dc3acc0b1c582ae56ba4c35ccd0fec539e3"
NAME = "abp_corrections_active_built_20261106.txt"


def key(b, c, v, p, f, r):
    return (b, int(c), int(v), int(p), f, r)


def line(k):
    return "%s\t%d\t%d\t%d\t%s\t%s" % k


def main():
    print("RE-PIN DUMP 374 - built copy's active correction rows - read-only")
    stops = []
    if os.path.realpath(BUILT) == os.path.realpath(os.path.expanduser("~/bible-db/bible.db")):
        print("REPIN DUMP: STOP - this is live, not the built copy")
        sys.exit(1)
    raw = open(os.path.join(REPO, OLD_REL), "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    print("372-row member file: %s - sha256 %s (%s)" % (OLD_REL, got[:16], "as committed" if got.startswith(OLD_SHA) else "DIFFERS"))
    if not got.startswith(OLD_SHA):
        stops.append("372-row file is not the committed one")
    old = {key(*l.split("\t")) for l in raw.decode("utf-8").splitlines()}
    conn = sqlite3.connect("file:%s?mode=ro" % BUILT, uri=True, timeout=30)
    conn.execute("PRAGMA query_only=1")
    print("built copy abp_corrections by status / applied_at:")
    for s, a, n in conn.execute("SELECT status, applied_at, count(*) FROM abp_corrections GROUP BY status, applied_at ORDER BY status, applied_at"):
        print("   %-11s %-8s %d" % (s, a, n))
    rows = [key(*r) for r in conn.execute("SELECT book, chapter, verse, position, field, ledger_ref FROM abp_corrections "
                                          "WHERE status='active' AND applied_at='ingest'")]
    other = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='active' AND applied_at IS NOT 'ingest'").fetchone()[0]
    retired = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='retired'").fetchone()[0]
    conn.close()
    active = set(rows)
    if len(active) != len(rows):
        stops.append("%d duplicate active key(s)" % (len(rows) - len(active)))
    missing, extra = sorted(old - active), sorted(active - old)
    print("active ingest rows %d (expect 374) - of the 372 file missing %d (expect 0) - not in it %d (expect 2)"
          % (len(active), len(missing), len(extra)))
    for k in missing:
        print("   MISSING: " + line(k))
    for k in extra:
        print("   NEW:     " + line(k))
    if len(active) != 374 or missing or set(extra) != NEW:
        stops.append("active rows are not the 372 + the two S-joh14:26 rows")
    print("active rows NOT applied at ingest %d (expect 0) - retired total %d (expect 23)" % (other, retired))
    if other or retired != 23:
        stops.append("non-ingest active %d / retired %d" % (other, retired))
    body = "".join(line(k) + "\n" for k in sorted(active)).encode("utf-8")
    sha = hashlib.sha256(body).hexdigest()
    print("dump sha256 %s - local derivation %s (%s)" % (sha[:16], LOCAL_SHA[:16], "SAME" if sha == LOCAL_SHA else "DIFFERENT"))
    if sha != LOCAL_SHA:
        stops.append("dump differs from the local derivation")
    if stops:
        print("REPIN DUMP: STOP - " + " | ".join(stops) + " - nothing written")
        sys.exit(1)
    path = os.path.join(OUT_DIR, NAME)
    for p in (path, path + ".sha256"):
        if os.path.exists(p):
            print("REPIN DUMP: STOP - already exists: %s - nothing written" % p)
            sys.exit(1)
    with open(path, "wb") as f:
        f.write(body)
    with open(path + ".sha256", "wb") as f:
        f.write(("%s  %s\n" % (sha, NAME)).encode("utf-8"))
    print("wrote %s (%d lines) + .sha256" % (path, body.count(b"\n")))
    print("REPIN DUMP: OK - 374 = 372 + 2 S-joh14:26 - retired 23 - sha256 %s" % sha)


if __name__ == "__main__":
    main()
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = c463ee4a3864de54d5d63d5fe5f25968e0f66b3702e564558b7d3033cdebbe7d ] || { echo "REPIN DUMP: STOP - the pasted script does not match the drafted one"; exit 1; }
PYTHONIOENCODING=utf-8 python3 "$P" "$B" ~/bible-db "$O"
) 2>&1 | tee ~/edition_upgrade_runs/repin_dump_20261106.log; echo "exit=${PIPESTATUS[0]}"
```

### Block C4′ — GATE 1 re-run (REF = the C3b commit, filled in when it exists)
```bash
set +H
( set -uo pipefail
REF=__REPIN_COMMIT__
echo "GATE REF ${REF} - C4 GATE 1 re-run, cert_invariants on the built copy (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "GATE1 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "GATE1 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "GATE1 RESULT: STOP - PA has not pulled $REF"; exit 1; }
grep -q '"abp_corrections_active": 374,' scripts/cert_invariants.py || { echo "GATE1 RESULT: STOP - the corrections pin is not 374 in this checkout"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
[ -f "$B" ] || { echo "GATE1 RESULT: STOP - missing: $B"; exit 1; }
python3 scripts/cert_invariants.py --controls; c=$?
[ "$c" -eq 0 ] || { echo "GATE1 RESULT: STOP - controls exit $c (a check that cannot fire is void)"; exit 1; }
python3 scripts/cert_invariants.py "$B"; r=$?
[ "$r" -eq 0 ] && echo "GATE1 RESULT: 7/7 on the built copy" || echo "GATE1 RESULT: STOP - suite exit $r (names above)"
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/gate1_cert_20261106.log; echo "exit=${PIPESTATUS[0]}"
```

### Block C5′ — RETIRED-ROW GATE re-run (REF = the C3b commit, filled in when it exists)
```bash
set +H
( set -uo pipefail
REF=__REPIN_COMMIT__
echo "GATE REF ${REF} - C5 RETIRED-ROW GATE re-run (sec 9.61/9.63) on the built copy (read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "RETIRED-ROW CHECK: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "RETIRED-ROW CHECK: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "RETIRED-ROW CHECK: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
[ -f "$B" ] || { echo "RETIRED-ROW CHECK: STOP - missing: $B"; exit 1; }
python3 tests/test_eu_retired_check.py; t=$?
[ "$t" -eq 0 ] || { echo "RETIRED-ROW CHECK: STOP - the check's own tests exit $t (a check that cannot fire is void)"; exit 1; }
PYTHONIOENCODING=utf-8 python3 scripts/eu_retired_check.py "$B"; r=$?
echo "check exit $r (0 PASS / 1 FAIL / 2 STOP)"
exit "$r"
) 2>&1 | tee ~/edition_upgrade_runs/retired_check_20261106.log; echo "exit=${PIPESTATUS[0]}"
```

## C3a′ RAN (11/6 15:25:58 UTC) — OK as expected; C3b next

Run 1 (PA HEAD 6da053c9, REF e777f965), every line vs the expected picture: 372 file sha 80db1c35 "as committed";
built `active ingest 374 · retired ingest 23 · superseded ingest 6`; active ingest 374 (expect 374), missing 0
(expect 0), not in it 2 (expect 2) = `NEW: Joh 14 26 3 bracket_id S-joh14:26` + `… greek_pos S-joh14:26`; non-ingest
active 0, retired 23; dump sha 446fee35b4080e52 = local (SAME); wrote 374 lines + .sha256;
`REPIN DUMP: OK - 374 = 372 + 2 S-joh14:26 - retired 23 - sha256 446fee35b4080e522e5b2af19aca9dc3acc0b1c582ae56ba4c35ccd0fec539e3`, exit=0.
Run 2 (15:26:15, an accidental re-paste) STOPPED at the "already exists" guard, nothing written — but its `tee`
overwrote `repin_dump_20261106.log`, so **the PA log now holds the run-2 STOP; run 1's OK output is recorded here only**
(from JP's paste). The two written files are run 1's; the C3b scp check (sha 446fee35…, 374 lines, LF) re-proves them.

## C3b landed 4d66afa3; C4′ gate 1 RAN (11/6 15:39:30 UTC) — 7/7 as expected

**Copy check (before C3b):** `sha256sum -c` against the scp'd `.sha256` = OK (446fee35…); 374 lines; byte count CR 0 /
LF 374. Two early CR checks gave false hits; the byte count is the record. **Corrected 11/6 (the first note here
said "matched the letter r" — a guess, wrong):** in local Git Bash (MSYS bash 5.2.37), `$'\r'` inside `"$(…)"` comes
out as NOTHING (tested: 0 bytes; `grep -c $'\r' <<< xyz` = 1 inside `"$(…)"`, 0 outside), so grep got an empty
pattern, which matches every line. The `od -c | grep -c '\\r'` count (227) was a separate bad check, not traced. Not
tested on PA's bash. Committed blob sha = 446fee35… (no ending conversion).
**C3b** `4d66afa3`: `3 files changed, 376 insertions(+), 1 deletion(-)` = planned. PA pulled 6da053c9 → 4d66afa3.
**C4′** (`gate1_cert_20261106.log`, REF 4d66afa3, PA HEAD 4d66afa3): controls 1, 2, 3, 4, 7, 7b all FIRED ("ALL CONTROLS
FIRED"); built copy 1–7 all `[OK]`, `CERTIFIED STATE HOLDS (7/7 green)`, `GATE1 RESULT: 7/7 on the built copy`, exit=0.
OK lines carry no figures; per the code, check 1 OK = words 626,309 + verses 31,237 exactly (`check_row_pins`), check 4
OK = exactly 374 active ingest rows, each holding (`check_corrections`), check 3 OK = em-dash 0 — the expected picture.
Next: C5′ (REF 4d66afa3).

## C5′ retired-row RAN (11/6 15:43:04 UTC) — PASS as expected → STAGE C CLOSED

`retired_check_20261106.log`, REF 4d66afa3, PA HEAD 4d66afa3: the check's own tests `Ran 11 tests … OK`; all 23 rows
`ok` (feed text = ids 24, 25, 27, 45, 51; the other 18 corrected_value); `RETIRED-ROW CHECK: PASS 23/23 HOLD
(corrected_value 18 - feed text 5)`, check exit 0, exit=0 — the expected picture exactly.
**Stage C closed** on the built copy (re-pin chain C3a′ → C3b → C4′ → C5′ all as expected). Live untouched; live check 4
stays red (51 vs pin 374) until the swap — accepted. Next per `HANDOFF_edition_upgrade_stageC_repin.md` "Then":
reviewer-subagent setup (ruling chat), then stage D.

## Stage D opened (11/6): file v1, 8B0 STOP → CMP / ROWS / census → 8B0b DONE

Rulings DESIGN §9.90–§9.93. Code REF `0cf4a11c` (gate-2 tooling, §9.92); fixtures REF **`0bb60e4a`**
(`declared_deltas.json` v1). Trigger check on built (JP, 16:47): no rows.
- **8B0** (`xref8b0_20261106.log`, 16:55 UTC; first paste STOPPED at the code check — PA had not pulled `0bb60e4a`;
  pulled, re-pasted): pre-checks OK; pre_8b rollback copy made, sha256 `a4faa4d8…0107` = built; words 626,309;
  CONTROL OK ×3; dry run **366 = SWAP 317 · REMOVE 22 · LEAVE 26 · HOLD 1, third copy 339** vs the 10/25 369 =
  319 / 22 / 27 / 1, 341 (`CHARTER_rebuild_trap_fix.md:467`) → `8B0 RESULT: STOP - plan is not 369`, nothing written.
  HOLD = 1Ch 5:23@13 'Baal' H1168 (R0 ruling, same as 10/25).
- **8B0-CMP** (`xref8b0_compare_20261106.log`; reference `~/correct_xref_vs_binding_plan.tsv`, 10/25 17:30, 369,
  rebuild-step): left 4 — 1Ch 1:38@13 Ezer→'Ezar,' `*` · Est 1:17@19 'Artaxerxes),' `*` · Gen 34:4@2 (row moved to
  @1) · Gen 39:17@14 English blank `*`; joined 1 — Gen 34:4@1 Shechem H7928 SWAP H7927; decision changed 0.
- **8B0-ROWS** (`xref8b0_rows_20261106.log`): Gen 34:4 pos 1/2 exchanged english + strongs + is_pn (greek_pos and
  bracket_id blank on both copies — greek_pos is the in-bracket order only); Gen 39:17 Strong's fixed per position,
  "Hebrew servant," on pos 12, pos 14 blank, bracket widened; 1Ch 1:38 'Ezar,' `*`; Est 1:17 'Artaxerxes),' `*`.
- **STRONGS-POS census v2** (`strongs_pos_census2_20261106.log`/.tsv; key strongs+morph+lemma): rows 626,309 both;
  same 31,227 · REORDER-WHOLE 10 · REORDER-SPLIT 0 · DIFFERS 0 · SKIPPED 0; control Gen 34:4 = REORDER-WHOLE.
  The 10: 2Ki 23:35 6/7, Est 5:9 12/13, Eze 20:14 7/8, Gen 5:25 1/2, Gen 5:26 1/2, Gen 34:4 1/2, Jdg 11:7 6/7,
  Jos 2:4 19/20, Jos 5:15 26/27, Rom 9:29 17/18. morph+lemma moved with Strong's in 7; Est 5:9, Jos 2:4, Jos 5:15
  have no morph/lemma (English↔number agreement only).
- **abp_surface at the 20 positions** (JP read 17:20): src = built, 15 forms, in src's order — on built each now
  sits against the other word of its pair (Gen 34:4 pos 1 'είπε' vs built's Shechem row). For §9.93 (c).
- **8B0b** (`xref8b0b_20261106.log`): ruling chat 11/6 — **ACCEPTED: `8B0b RESULT: DONE`, applied 339, exit 0.**
  The output went to the ruling chat directly; the figures beyond those are in the PA log, not relayed here.

## 8B1 STOPPED (182) → §9.94 restore-all 178 + re-key; session closed under the stop rule (11/6)

**8B1** (`xref8b1_20261106.log`, 17:30 UTC, REF `0bb60e4a`): pre-checks OK; `checked 28,807 frozen-record slots …;
182 differ (declared 8)` → `HALT`, dry-run exit 1; `MEMBERS: total 182 - CUSHI 8 - MOVED 6 - OTHER 168 -
greek-numbered 6` → `8B1 RESULT: STOP`, nothing written. Frozen records at the 20 moved positions: 2Ki 23:35@7
lemma-only H3079 · Est 5:9@13 surface H2001 · Gen 5:25@2 / 5:26@2 tipnr H4968 · Gen 34:4@2 tipnr H7927 · Jos 5:15@26
none NULL; none at the other 14. OTHER by origin (CC, repo receipts; DESIGN §9.94): C 24 · E1 23 · E2 12 · E3 7 · E4 16
traced; J 27 · N 30 · S 9 · X 19 unattributed. Ruled §9.94: restore all 178; re-key 6 identity records + 15
abp_surface forms; G4 per-table key moves. Docs `b3931161`; code/fixtures `83f8f570` (not yet pulled on PA).
**Stop:** CC's store inventory said `pn_hebrew_xref` is not read by position before 8b.2 rebuilds it; 8b.2's oracle
gate reads it (`retire_hebrew_identity.py:162-172`). REKEY / 8B1b not drafted. Next: `HANDOFF_edition_upgrade_stageD_rekey.md`.

## Reviewer calibrated; STAGED-READ, REKEY (three-set), 8B1b DONE (11/6, 18:48–19:01 UTC) → built = 8b.0 + REKEY + 8b.1

Reviewer calibration (T1 known-good 8B0-CMP / T2 8B0b write / T3 two-edit): T2, T3 as expected; T1 ESCALATED on the
test's own defects (re-presented an already-run block under its log name; 10/25 tally not in DESIGN) — ruling chat
ACCEPTED all three. reviewer.md amended `844bb47b` (figure sources incl. cited run receipts/logs; run artifacts under
`~/edition_upgrade_runs` are not writes, must not overwrite; model fable / effort low); CLAUDE.md routing line `2cdc4cf5`.
Routing live: read-only blocks + ruled-gate re-runs → reviewer first; writes → ruling chat.
- **STAGED-READ** (`stageD_read1_20261106.log`, 18:48 UTC, REF `83f8f570`, reviewer CLEAR): position-keyed stores at
  the 20 moved positions, both copies — verse_ids 10/10 (Eze 20:14 = 21045); identity 6 at the 6 OLD positions on both
  copies; `pn_hebrew_xref` 6 at the same keys, join mismatches 0, whole-table oracle 0/0 both copies; abp_surface 15/15;
  active correction rows at the 10 verses 0; pn_slot_binding 0. Inventory behind it: every 8b script's position reads
  = words, pn_greek_identity, pn_hebrew_xref, abp_surface, abp_corrections, pn_slot_binding; lane-3 JSON files touch
  none of the 10 verses. Ruling: three-set REKEY sufficient.
- **REKEY** (`rekey_20261106.log`, 19:00 UTC, REF `83f8f570`, ruling-chat cleared): one transaction — identity 6 +
  xref 6 (old→new per `pn_greek_identity_key_moves_20261106.tsv`) + abp_surface 15 (6 pair swaps via temp slot + 3
  singles); 27 guards OK; counts unchanged (identity 32,478 · xref 32,478 · surface 395,003 · words 626,309); oracle
  0/0 after; the 6 records now at 2Ki 23:35@6, Est 5:9@12, Gen 5:25@1, Gen 5:26@1, Gen 34:4@1, Jos 5:15@27 with xref
  beside each; `REKEY RESULT: DONE`, exit 0. **ACCEPTED.**
- **8B1b** (`xref8b1b_20261106.log`, 19:01 UTC, REF `83f8f570`): pre (d) identity at the 6 new positions 6; dry run
  `178 differ (declared 178)`; `MEMBERS: total 178 - CUSHI 8 - MOVED 0 - OTHER 170 - greek-numbered 0` (OTHER = the
  168 + Est 5:9@12 `'*'->'H2001'` + Jos 5:15@27 `'H3091'->'*'`); apply `restored 178 slot(s); ... 0 (must be 0)`;
  words 626,309; `8B1b RESULT: DONE`, exit 0. **ACCEPTED.** Gate-2 member added: Jos 5:15@27 Joshua (live record
  class none, built H3091 restored to '*' under §9.94 (a); candidate correction, with Gen 4:18).
- Next: 8B2 (`retire_hebrew_identity.py --fresh-rebuild`) drafted for the ruling chat; receipt of the last run =
  `RUN_rebuild_trap_live.md:85` / `CHARTER_rebuild_trap_fix.md:468`.
- **8B2 STOP (`xref8b2_20261106.log`, REF `83f8f570`, ruling-chat cleared): dry run only, nothing written.** Pre-checks
  a–f all OK (oracle 0/0, frozen slots off record 0, Greek-numbered non-abp-tag 0, words 626,309, xref 32,478); the dry
  run HALTED on the class split: built = abp-tag 3,671 · tipnr 10,236 · **lemma-only 12,191 · surface 4,409 · none
  1,971** vs the code's declared 12,182 / 4,412 / 1,977 (lemma-only +9 = surface −3 + none −6; total 32,478 either
  way). STOP ACCEPTED (ruling chat 11/6). Run artifacts left in place: `~/edition_upgrade_runs/xref8b2_dry_20261106/`
  (greek_rows_before.tsv, dry_run_full.log) — a redraft needs new folder names (double-paste guard). Receipt trail:
  the 10/25 chain ran 8b.2 on the PRE-8b.3 identity (declared split `RUN_rebuild_trap_live.md:85`), then 8b.3 rebuilt
  `pn_greek_identity` — `identity|21|21` vs live at the swap (`RUN_rebuild_trap_live.md:157`,
  `CHARTER_rebuild_trap_fix.md:492`), incl. the 2 Sheshach rows surface→lemma-only (`TODO.md:183-184`,
  `CHARTER_rebuild_trap_fix.md:481`); the post-8b.3 split was never re-declared in the code. Next: read-only drift
  block (identity source vs xref class, both copies; built vs the 9/6 hdrlane backup if present), then propose the
  re-declaration + derived rewrite count (tipnr + lemma-only-with-H + surface-with-H) — proposal only, no commit.
  **DRIFT-8B2 printed 11/6** (reviewer ESCALATE → two mechanical fixes → CLEAR; log `drift8b2_20261106`, folder
  `drift8b2_20261106/`), RAN on picture: 9 = surface→lemma-only 3 (Jos 12:23, Jer 25:26, Jer 51:41) + none→lemma-only 6 (Num 21:25,
  1Sa 20:37, 2Sa 15:6, Jer 48:15, Jer 48:20, Jer 49:3; all with a Hebrew number); `live_8b3_id.log` = same split. **Ruled
  §9.95:** EXPECT 3671 / 10236 / 12191 / 4409 / 1971, rewrites 26,323, xref 32,478, GLOB 0; next session = scripts
  commit then 8B2b (`xref8b2b_*`).

## EXPECT re-declared (12b3e689); 8B2b STOP on an abp-tag row (11/6)

Scripts commit `12b3e689` (pushed): `retire_hebrew_identity.py` EXPECT = 3671 / 10236 / 12191 / 4409 / 1971 per §9.95,
comment cites `~/rekey/live_8b3_id.log`, `drift8b2_20261106.log`, `RUN_rebuild_trap_live.md:157`; the 4 retire tests +
the pre-commit list green. 8B2b = the 11/6 8B2 block text verbatim (recovered from the 11/6 session transcript, diffed
identical to what JP ran) with only REF 12b3e689, labels 8B2b, folders/log `xref8b2b_*`, the new split and 26,323.
- **8B2b STOP (`xref8b2b_20261106.log`): dry run HALTED, nothing written.** HALT on abp-tag row (23928,2): words
  G4610 vs identity G4609 (the abp-tag check, `retire_hebrew_identity.py:227-230`; ruling chat's read of the log). The
  script stops at the first bad row, so the count is unknown. STOP ACCEPTED (ruling chat 11/6). `xref8b2b_dry_20261106/`
  exists on PA (the apply folder is made only after a clean dry run) — the next redraft needs new names.
- Ruling chat next: read-only, via the reviewer, both copies — (1) every abp-tag identity row whose word differs
  from the record's greek_strongs (ref, position, english, word strongs/strongs_base, record greek_strongs/lemma,
  total); (2) per row: any abp_corrections row at that verse/position (any status/field), membership in R2's 389-cell
  plan (`~/edition_upgrade_runs/restore_digits_plan_20261105.tsv` path:line), src vs built values; (3) verse 23928 →
  ref. Then CC proposes per row which side is authoritative, with the receipt — proposal only, no write.
- **ABPTAG-READ** (REF 12b3e689, read-only, reviewer ESCALATE on a missing porcelain line → added → CLEAR) RAN:
  `abptag_read_20261106.log` — 16 failing abp-tag rows on built, 0 on src (ruling chat's read; the log is not in the
  repo). **Ruled §9.96:** frozen record authoritative, restore all 16 (Eze 27:13@1 H3120→G1673; 1Th 1:1@2, 2Co 1:19@16,
  2Th 1:1@2 G4610→G4609; 12 `'*'` rows → their record's G number); gate-2 member Silas/Silvanus ×3. Next:
  ABPTAG-RESTORE (write → ruling chat) then 8B2c (`xref8b2c_*`).

## ABPTAG-RESTORE + 8B2c drafted, held for the ruling chat (11/6)

`abptag_read_20261106.log` scp'd (read-only touchpoint; not in the repo). Read in full: the 16 built rows match §9.96
(Eze 27:13@1 H3120->G1673; 1Th 1:1@2, 2Co 1:19@16, 2Th 1:1@2 G4610->G4609; 12 `'*'` rows -> record G); all 16 strongs `'*'`
(the normal abp-tag name-slot state: 3,655 passing abp-tag rows also carry `'*'`); src carries the record's number at the
same position on all 16 (word english differs on 15 (all but Act 16:6 'Galatian'): the edition's English). Corrections at two of the positions
(Act 16:6@6 ids 72/73, Mat 1:13@0 ids 93/94) are english / english_head only (+ verses.text ids 74/95) — no strongs_base
row, no clash. R2 plan: none of the 16 verses.
Tests (made-up dbs): pass; re-paste (folder guard); re-run on fixed rows (row guard); drifted row; missing log line;
before-count 17; a change outside the 16 inside the transaction (rolled back, db unchanged). Whole block in a fake home
on a made-up built copy of 626,309 words / 3,671 abp-tag rows: DONE, other 626,293 rows' digest unchanged.
Helper sha256 2ac942af3fa6eed3f9d292ceb483e6ba5b1db2c4259b76685db8bcd612d9ab4f. Run order: ABPTAG-RESTORE, then 8B2c only
after it reads DONE.

### Block ABPTAG-RESTORE (GATE REF 12b3e689; WRITES built: 16 words.strongs_base)
```bash
set +H
( set -uo pipefail
REF=12b3e689
echo "GATE REF ${REF} - ABPTAG-RESTORE 16 abp-tag strongs_base back to the frozen record on the built copy (sec 9.96; WRITES built) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "ABPTAG-RESTORE RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "ABPTAG-RESTORE RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "ABPTAG-RESTORE RESULT: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
R=~/bible-db/bible_edupg_test_built_pre_8b_20261106.db
O=~/edition_upgrade_runs
RL="$O/abptag_read_20261106.log"
D="$O/abptag_restore_20261106"
[ -f "$B" ] || { echo "ABPTAG-RESTORE RESULT: STOP - missing: $B"; exit 1; }
[ -s "$RL" ] || { echo "ABPTAG-RESTORE RESULT: STOP - read log missing or empty: $RL"; exit 1; }
if [ -e "$D" ]; then echo "ABPTAG-RESTORE RESULT: STOP - output folder already exists (already ran?): $D"; exit 1; fi
t=$(sqlite3 -readonly "$B" "SELECT count(*) FROM sqlite_master WHERE type='trigger'") || { echo "ABPTAG-RESTORE RESULT: STOP - trigger read failed"; exit 1; }
echo "pre (a) triggers on built: $t (expect 0)"
[ "$t" = "0" ] || { echo "ABPTAG-RESTORE RESULT: STOP - built has triggers"; exit 1; }
if [ -e "$B-journal" ]; then echo "ABPTAG-RESTORE RESULT: STOP - $B-journal present (move it aside, never delete; bring it back)"; exit 1; fi
echo "pre (b) no -journal beside built: OK"
[ -s "$R" ] || { echo "ABPTAG-RESTORE RESULT: STOP - pre_8b rollback copy missing or empty: $R"; exit 1; }
echo "pre (c) pre_8b copy present: $(stat -c '%s bytes, %y' "$R") - built now $(stat -c '%s bytes' "$B") (size only)"
mkdir -p "$D"
P="$D/abptag_restore_20261106.py"
cat > "$P" <<'PY'
"""ABPTAG-RESTORE (DESIGN sec 9.96): put words.strongs_base back to the frozen record's
greek_strongs on the 16 abp-tag rows the ABPTAG-READ log listed as failing on built.

WRITES the built copy: 16 single-row changes to words.strongs_base, nothing else.
All 16 go in one transaction; any failed check before COMMIT rolls ALL of them back.

Before writing, every row must still be EXACTLY what the read log printed:
  - its verse_id maps to the expected ref, and the read log holds the row's exact line
  - one words row at (verse_id, position) with the logged english / strongs / strongs_base
  - the identity record there is abp-tag with greek_strongs = the new value
  - strongs is '*' (no Greek-numbered word is touched)
Inside the transaction, before COMMIT:
  - each UPDATE changed exactly 1 row; total changes 16
  - the retire_hebrew_identity.py abp-tag check (:223-233) passes on every abp-tag row
    (no words row / strongs_base differs / not G / record carries hebrew_base) - 0 failing,
    abp-tag rows 3,671
  - words 626,309; every word row other than the 16 is unchanged (rowid, strongs, strongs_base
    digest); the 16 still have strongs '*'; GLOB invariant (bare-number strongs_base) 0
After COMMIT, the 16 rows are re-read and printed.

Usage: python3 abptag_restore_20261106.py <built.db> <abptag_read_20261106.log>
"""
import hashlib
import sqlite3
import sys

DB, READLOG = sys.argv[1:3]
WORDS_EXPECT = 626309
ABPTAG_EXPECT = 3671
# verse_id, position, ref, english, strongs, strongs_base now, new strongs_base, the read log's exact line
ROWS = [
    (21270, 1, 'Eze 27:13', 'Greece,', '*', 'H3120', 'G1673',
     "  21270 | Eze 27:13 | 1 | 'Greece,' | '*' | 'H3120' | 'G1673' | 'Ελλάς' | strongs_base differs; strongs_base not G"),
    (23928, 2, '1Th 1:1', 'Silvanus,', '*', 'G4610', 'G4609',
     "  23928 | 1Th 1:1 | 2 | 'Silvanus,' | '*' | 'G4610' | 'G4609' | 'Σιλουανός' | strongs_base differs"),
    (24148, 16, '2Co 1:19', 'Silvanus', '*', 'G4610', 'G4609',
     "  24148 | 2Co 1:19 | 16 | 'Silvanus' | '*' | 'G4610' | 'G4609' | 'Σιλουανού' | strongs_base differs"),
    (24461, 2, '2Th 1:1', 'Silvanus,', '*', 'G4610', 'G4609',
     "  24461 | 2Th 1:1 | 2 | 'Silvanus,' | '*' | 'G4610' | 'G4609' | 'Σιλουανός' | strongs_base differs"),
    (24627, 9, 'Act 1:23', 'Justus,)', '*', '*', 'G2459',
     "  24627 | Act 1:23 | 9 | 'Justus,)' | '*' | '*' | 'G2459' | 'Ιούστος' | strongs_base differs; strongs_base not G"),
    (25170, 6, 'Act 16:6', 'Galatian', '*', '*', 'G1052',
     "  25170 | Act 16:6 | 6 | 'Galatian' | '*' | '*' | 'G1052' | 'Γαλατικήν' | strongs_base differs; strongs_base not G"),
    (25225, 0, 'Act 17:21', '( Athenians', '*', '*', 'G117',
     "  25225 | Act 17:21 | 0 | '( Athenians' | '*' | '*' | 'G117' | 'Αθηναίοι' | strongs_base differs; strongs_base not G"),
    (25374, 19, 'Act 21:29', 'Paul.)', '*', '*', 'G3972',
     "  25374 | Act 21:29 | 19 | 'Paul.)' | '*' | '*' | 'G3972' | 'Παύλος' | strongs_base differs; strongs_base not G"),
    (25553, 12, 'Act 27:17', 'Syrtis Gulf', '*', '*', 'G4950',
     "  25553 | Act 27:17 | 12 | 'Syrtis Gulf' | '*' | '*' | 'G4950' | 'Σύρτιν' | strongs_base differs; strongs_base not G"),
    (26424, 2, 'Joh 1:28', 'Bethania', '*', '*', 'G963',
     "  26424 | Joh 1:28 | 2 | 'Bethania' | '*' | '*' | 'G963' | NULL | strongs_base differs; strongs_base not G"),
    (27237, 1, 'Joh 20:18', 'Then Mary', '*', '*', 'G3137',
     "  27237 | Joh 20:18 | 1 | 'Then Mary' | '*' | '*' | 'G3137' | 'Μαρία' | strongs_base differs; strongs_base not G"),
    (28665, 6, 'Mar 6:22', 'of Herodias,)', '*', '*', 'G2266',
     "  28665 | Mar 6:22 | 6 | 'of Herodias,)' | '*' | '*' | 'G2266' | 'Ηρωδιάδος' | strongs_base differs; strongs_base not G"),
    (29083, 13, 'Mar 15:21', 'Rufus,)', '*', '*', 'G4504',
     "  29083 | Mar 15:21 | 13 | 'Rufus,)' | '*' | '*' | 'G4504' | 'Ρούφου' | strongs_base differs; strongs_base not G"),
    (29141, 13, 'Mat 1:12', 'Zorobabel;', '*', '*', 'G2216',
     "  29141 | Mat 1:12 | 13 | 'Zorobabel;' | '*' | '*' | 'G2216' | 'Ζοροβάβελ' | strongs_base differs; strongs_base not G"),
    (29142, 0, 'Mat 1:13', 'and Zorobabel', '*', '*', 'G2216',
     "  29142 | Mat 1:13 | 0 | 'and Zorobabel' | '*' | '*' | 'G2216' | 'Ζοροβάβελ' | strongs_base differs; strongs_base not G"),
    (31003, 4, 'Rom 10:12', 'both of Jew', '*', '*', 'G2455',
     "  31003 | Rom 10:12 | 4 | 'both of Jew' | '*' | '*' | 'G2455' | 'Ιουδαίου' | strongs_base differs; strongs_base not G"),
]


def stop(msg):
    print("ABPTAG-RESTORE RESULT: STOP - " + msg)
    sys.exit(1)


def q(v):
    return "NULL" if v is None else repr(v)


def retire_abptag_failing(c):
    bad = 0
    n = 0
    for r in c.execute("""
        SELECT g.greek_strongs, g.hebrew_base, w.rowid AS wrow, w.strongs_base
        FROM pn_greek_identity g
        LEFT JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
        WHERE g.source = 'abp-tag'"""):
        n += 1
        greek, heb, wrow, cur = r
        if wrow is None or not cur == greek or not (cur or "").startswith("G") or heb is not None:
            bad += 1
    return n, bad


def digest_except(c, skip):
    h = hashlib.sha256()
    n = 0
    for rowid, s, sb in c.execute("SELECT rowid, strongs, strongs_base FROM words ORDER BY rowid"):
        if rowid in skip:
            continue
        h.update(("%d\t%s\t%s\n" % (rowid, s, sb)).encode("utf-8"))
        n += 1
    return n, h.hexdigest()


if not len(ROWS) == 16:
    stop("the row list does not hold 16 rows")
log = open(READLOG, encoding="utf-8").read().split("\n")
c = sqlite3.connect(DB, timeout=30)
c.execute("PRAGMA journal_mode=DELETE")
c.execute("PRAGMA busy_timeout=10000")

# ---- guards, nothing written yet
print("--- guards (before any write)")
targets = []
for vid, pos, ref, eng, strongs, sb_now, sb_new, logline in ROWS:
    tag = "%d@%d %s" % (vid, pos, ref)
    if logline not in log:
        stop("%s: the read log does not hold this row's line" % tag)
    v = c.execute("SELECT book || ' ' || chapter || ':' || verse FROM verses WHERE id=?", (vid,)).fetchone()
    if not v or not v[0] == ref:
        stop("%s: verse_id maps to %s" % (tag, v[0] if v else "nothing"))
    w = c.execute("SELECT rowid, english, strongs, strongs_base FROM words WHERE verse_id=? AND position=?",
                  (vid, pos)).fetchall()
    if not len(w) == 1:
        stop("%s: %d words rows at this slot (expect 1)" % (tag, len(w)))
    rowid, e, s, sb = w[0]
    if not (e, s, sb) == (eng, strongs, sb_now):
        stop("%s: word now english %s strongs %s strongs_base %s - not the logged %s %s %s"
             % (tag, q(e), q(s), q(sb), q(eng), q(strongs), q(sb_now)))
    if not s == "*":
        stop("%s: strongs is %s, not '*' (a Greek-numbered word)" % (tag, q(s)))
    g = c.execute("SELECT source, greek_strongs FROM pn_greek_identity WHERE verse_id=? AND position=?",
                  (vid, pos)).fetchone()
    if not g or not g[0] == "abp-tag" or not g[1] == sb_new:
        stop("%s: identity record is %s, not abp-tag %s" % (tag, g, sb_new))
    print("  OK %s pos %d english %s strongs %s strongs_base %s -> %s (record abp-tag %s)"
          % (ref, pos, q(e), q(s), q(sb), q(sb_new), q(g[1])))
    targets.append((rowid, sb_now, sb_new, tag))
if not len({t[0] for t in targets}) == 16:
    stop("the 16 rows are not 16 different words rows")
skip = {t[0] for t in targets}
n_before = c.execute("SELECT count(*) FROM words").fetchone()[0]
if not n_before == WORDS_EXPECT:
    stop("words before %d (expect %d)" % (n_before, WORDS_EXPECT))
n0, dig0 = digest_except(c, skip)
na0, bad0 = retire_abptag_failing(c)
print("before: words %d - abp-tag rows %d, failing the retire check %d (expect 16) - other word rows %d digest %s"
      % (n_before, na0, bad0, n0, dig0[:8]))
if not bad0 == 16:
    stop("failing abp-tag rows before is %d, not 16" % bad0)

# ---- the write: one transaction
c.isolation_level = None
c.execute("BEGIN IMMEDIATE")
ch0 = c.total_changes
for rowid, sb_now, sb_new, tag in targets:
    cur = c.execute("UPDATE words SET strongs_base=? WHERE rowid=? AND strongs_base=? AND strongs='*'",
                    (sb_new, rowid, sb_now))
    if not cur.rowcount == 1:
        c.execute("ROLLBACK")
        stop("%s: UPDATE changed %d rows (expect 1) - rolled back, nothing written" % (tag, cur.rowcount))
changes = c.total_changes - ch0
na1, bad1 = retire_abptag_failing(c)
n_after = c.execute("SELECT count(*) FROM words").fetchone()[0]
n1, dig1 = digest_except(c, skip)
star = c.execute("SELECT count(*) FROM words WHERE rowid IN (%s) AND strongs='*'" % ",".join("?" * 16),
                 tuple(sorted(skip))).fetchone()[0]
glob = c.execute("SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'").fetchone()[0]
print("in transaction: changes %d (expect 16) - abp-tag rows %d (expect %d), failing the retire check %d (expect 0)"
      % (changes, na1, ABPTAG_EXPECT, bad1))
print("in transaction: words %d (expect %d) - other word rows %d digest %s (expect %s, unchanged) - the 16 with strongs '*': %d (expect 16) - GLOB %d (expect 0)"
      % (n_after, WORDS_EXPECT, n1, dig1[:8], dig0[:8], star, glob))
ok = (changes == 16 and na1 == ABPTAG_EXPECT and bad1 == 0 and n_after == WORDS_EXPECT
      and n1 == n0 and dig1 == dig0 and star == 16 and glob == 0)
if not ok:
    c.execute("ROLLBACK")
    stop("a check inside the transaction failed (line above) - rolled back, nothing written")
c.execute("COMMIT")
c.close()

# ---- after, read-only
r = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=30)
print("--- the 16 rows after:")
for vid, pos, ref, eng, strongs, sb_now, sb_new, logline in ROWS:
    w = r.execute("SELECT english, strongs, strongs_base FROM words WHERE verse_id=? AND position=?", (vid, pos)).fetchone()
    print("  %d | %s | %d | %s | strongs %s | strongs_base %s (was %s)" % (vid, ref, pos, q(w[0]), q(w[1]), q(w[2]), q(sb_now)))
na2, bad2 = retire_abptag_failing(r)
print("after: abp-tag rows %d, failing the retire check %d (expect 0)" % (na2, bad2))
if not bad2 == 0:
    stop("after COMMIT the retire check reads %d failing" % bad2)
print("ABPTAG-RESTORE RESULT: DONE - 16 strongs_base restored to the frozen record - retire abp-tag check 0 failing on %d rows - words %d - other rows unchanged"
      % (na2, WORDS_EXPECT))
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = 2ac942af3fa6eed3f9d292ceb483e6ba5b1db2c4259b76685db8bcd612d9ab4f ] || { echo "ABPTAG-RESTORE RESULT: STOP - the pasted script does not match the drafted one"; exit 1; }
PYTHONIOENCODING=utf-8 python3 "$P" "$B" "$RL"; r=$?
if [ -e "$B-journal" ]; then J=PRESENT; else J=none; fi
echo "journal after: $J (expect none)"
[ "$r" -eq 0 ] && [ "$J" = "none" ] || { echo "ABPTAG-RESTORE RESULT: NOT DONE - helper exit $r, journal $J (the helper's own RESULT line above says what stopped it)"; exit 1; }
exit 0
) 2>&1 | tee ~/edition_upgrade_runs/abptag_restore_20261106.log; echo "exit=${PIPESTATUS[0]}"
```

### Block 8B2c (GATE REF 12b3e689; = 8B2b with folder/log names `xref8b2c_*` only)
```bash
set +H
( set -uo pipefail
REF=12b3e689
echo "GATE REF ${REF} - 8B2b retire_hebrew_identity --fresh-rebuild on the built copy (dry run, apply only on the sec 9.95 picture) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "8B2b RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "8B2b RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "8B2b RESULT: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
R=~/bible-db/bible_edupg_test_built_pre_8b_20261106.db
O=~/edition_upgrade_runs
D1="$O/xref8b2c_dry_20261106"; D2="$O/xref8b2c_apply_20261106"
[ -f "$B" ] || { echo "8B2b RESULT: STOP - missing: $B"; exit 1; }
if [ -e "$D1" ] || [ -e "$D2" ]; then echo "8B2b RESULT: STOP - output folder already exists (already ran?): $D1 / $D2"; exit 1; fi
t=$(sqlite3 -readonly "$B" "SELECT count(*) FROM sqlite_master WHERE type='trigger'") || { echo "8B2b RESULT: STOP - trigger read failed"; exit 1; }
echo "pre (a) triggers on built: $t (expect 0)"
[ "$t" = "0" ] || { echo "8B2b RESULT: STOP - built has triggers"; exit 1; }
if [ -e "$B-journal" ]; then echo "8B2b RESULT: STOP - $B-journal present (move it aside, never delete; bring it back)"; exit 1; fi
echo "pre (b) no -journal beside built: OK"
[ -s "$R" ] || { echo "8B2b RESULT: STOP - pre_8b rollback copy missing or empty: $R"; exit 1; }
echo "pre (c) pre_8b copy present: $(stat -c '%s bytes, %y' "$R") - built now $(stat -c '%s bytes' "$B") (size only)"
OA=$(sqlite3 -readonly "$B" "SELECT count(*) FROM pn_greek_identity g JOIN pn_hebrew_xref x ON x.verse_id=g.verse_id AND x.position=g.position WHERE g.hebrew_base IS NOT x.hebrew_base")
OB=$(sqlite3 -readonly "$B" "SELECT count(*) FROM pn_hebrew_xref x WHERE NOT EXISTS (SELECT 1 FROM pn_greek_identity g WHERE g.verse_id=x.verse_id AND g.position=x.position)")
echo "pre (d) oracle gate, whole table, before: hebrew_base mismatches $OA, xref rows outside the identity table $OB (expect 0 / 0)"
[ "$OA" = "0" ] && [ "$OB" = "0" ] || { echo "8B2b RESULT: STOP - oracle gate is not 0 / 0 before the run"; exit 1; }
RS=$(python3 scripts/restore_frozen_pn.py "$B" 2>&1); rs=$?
grep -E "^checked" <<< "$RS"
echo "pre (e) restore_frozen_pn dry run exit $rs (1 expected: 0 differ is a count mismatch against its declared 178, nothing written on a dry run)"
grep -qF "0 differ from the frozen record (declared 178)" <<< "$RS" || { echo "8B2b RESULT: STOP - frozen slots off record is not 0"; exit 1; }
G=$(sqlite3 -readonly "$B" "SELECT count(*) FROM pn_greek_identity g JOIN words w ON w.verse_id=g.verse_id AND w.position=g.position WHERE g.source <> 'abp-tag' AND w.strongs GLOB '[0-9]*'")
echo "pre (f) non-abp-tag identity records sitting on a Greek-numbered word: $G (expect 0; was 6 before REKEY)"
[ "$G" = "0" ] || { echo "8B2b RESULT: STOP - an identity record sits on a Greek-numbered word"; exit 1; }
W0=$(sqlite3 -readonly "$B" "SELECT count(*) FROM words")
X0=$(sqlite3 -readonly "$B" "SELECT count(*) FROM pn_hebrew_xref")
echo "words before: $W0 (expect 626309) - pn_hebrew_xref before: $X0 (expect 32478)"
[ "$W0" = "626309" ] || { echo "8B2b RESULT: STOP - words before is not 626309"; exit 1; }
[ "$X0" = "32478" ] || { echo "8B2b RESULT: STOP - pn_hebrew_xref before is not 32478"; exit 1; }
mkdir -p "$D1"
sqlite3 -readonly "$B" "SELECT rowid, strongs, quote(strongs_base) FROM words WHERE strongs GLOB '[0-9]*' ORDER BY rowid" > "$D1/greek_rows_before.tsv"
echo "snapshot: Greek-numbered word rows (rowid, strongs, strongs_base) before: $(wc -l < "$D1/greek_rows_before.tsv") rows"
DRY=$(python3 scripts/retire_hebrew_identity.py "$B" --fresh-rebuild 2>&1); d=$?
printf '%s\n' "$DRY" > "$D1/dry_run_full.log"
grep -E "oracle gate|identity class split|^verified|^  class|^planned rewrites|^total rows changing|^pn_hebrew_xref rows to write|^is_pn words outside|^HALT|DRY RUN" <<< "$DRY"
echo "dry run exit $d (expect 0)"
[ "$d" -eq 0 ] || { echo "8B2b RESULT: STOP - dry run exit $d, nothing written"; exit 1; }
grep -qF "fresh-rebuild oracle gate: hebrew_base mismatches 0 (must be 0), xref rows outside the identity table 0 (must be 0)" <<< "$DRY" || { echo "8B2b RESULT: STOP - oracle gate line is not 0 / 0"; exit 1; }
grep -qF "identity class split: {'abp-tag': 3671, 'tipnr': 10236, 'lemma-only': 12191, 'surface': 4409, 'none': 1971}" <<< "$DRY" || { echo "8B2b RESULT: STOP - class split is not 3,671 / 10,236 / 12,191 / 4,409 / 1,971"; exit 1; }
grep -qF "verified 32,478 rows against their classes" <<< "$DRY" || { echo "8B2b RESULT: STOP - not 32,478 rows verified"; exit 1; }
grep -qF "total rows changing: 26,323" <<< "$DRY" || { echo "8B2b RESULT: STOP - rows changing is not 26,323 (read the planned-rewrites line)"; exit 1; }
grep -qF "pn_hebrew_xref rows to write: 32,478 " <<< "$DRY" || { echo "8B2b RESULT: STOP - xref rows to write is not 32,478"; exit 1; }
grep -qF "is_pn words outside the write set: 0 (expected 0)" <<< "$DRY" || { echo "8B2b RESULT: STOP - is_pn words outside the write set"; exit 1; }
grep -qF "[DRY RUN] No changes written" <<< "$DRY" || { echo "8B2b RESULT: STOP - no DRY RUN line"; exit 1; }
echo "dry run = the sec 9.95 picture (split 3,671 / 10,236 / 12,191 / 4,409 / 1,971 - 26,323 rewrites - xref 32,478) - applying"
mkdir -p "$D2"
APP=$(python3 scripts/retire_hebrew_identity.py "$B" --fresh-rebuild --apply 2>&1); a=$?
printf '%s\n' "$APP" > "$D2/apply_full.log"
grep -E "^stale pn_hebrew_xref dropped|^wrote pn_hebrew_xref|^applied|^GLOB invariant|^HALT|post-write checks" <<< "$APP"
echo "apply exit $a (expect 0)"
W1=$(sqlite3 -readonly "$B" "SELECT count(*) FROM words")
X1=$(sqlite3 -readonly "$B" "SELECT count(*) FROM pn_hebrew_xref")
echo "words after: $W1 (expect 626309) - pn_hebrew_xref after: $X1 (expect 32478)"
OA2=$(sqlite3 -readonly "$B" "SELECT count(*) FROM pn_greek_identity g JOIN pn_hebrew_xref x ON x.verse_id=g.verse_id AND x.position=g.position WHERE g.hebrew_base IS NOT x.hebrew_base")
OB2=$(sqlite3 -readonly "$B" "SELECT count(*) FROM pn_hebrew_xref x WHERE NOT EXISTS (SELECT 1 FROM pn_greek_identity g WHERE g.verse_id=x.verse_id AND g.position=x.position)")
echo "oracle gate, whole table, after (identity vs the rebuilt xref): $OA2 / $OB2 (expect 0 / 0)"
GL=$(sqlite3 -readonly "$B" "SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'")
echo "GLOB invariant after (bare-number strongs_base): $GL (expect 0)"
sqlite3 -readonly "$B" "SELECT rowid, strongs, quote(strongs_base) FROM words WHERE strongs GLOB '[0-9]*' ORDER BY rowid" > "$D2/greek_rows_after.tsv"
GD=$(diff "$D1/greek_rows_before.tsv" "$D2/greek_rows_after.tsv" | grep -c '^[<>]') || true
echo "Greek-numbered word rows rewritten (before/after snapshot diff lines): $GD (expect 0)"
if [ -e "$B-journal" ]; then J=PRESENT; else J=none; fi
echo "journal after: $J (expect none)"
if [ "$a" -eq 0 ] && grep -qF "wrote pn_hebrew_xref: 32,478 rows" <<< "$APP" && grep -qF "applied 26,323 strongs_base rewrites" <<< "$APP" && grep -qF "GLOB invariant (bare-number strongs_base): 0 (expected 0)" <<< "$APP" && grep -qF "all post-write checks pass" <<< "$APP" && [ "$W1" = "626309" ] && [ "$X1" = "32478" ] && [ "$OA2" = "0" ] && [ "$OB2" = "0" ] && [ "$GL" = "0" ] && [ "$GD" = "0" ] && [ "$J" = "none" ]; then
  echo "8B2b RESULT: DONE - 26,323 rewrites - xref rebuilt 32,478 - oracle 0/0 - GLOB 0 - Greek-numbered rows untouched - words 626309 unchanged"; exit 0
fi
echo "8B2b RESULT: CHECK - an after-figure differs from the expected picture (lines above)"; exit 1
) 2>&1 | tee ~/edition_upgrade_runs/xref8b2c_20261106.log; echo "exit=${PIPESTATUS[0]}"
```

## ABPTAG-RESTORE + 8B2c RAN — DONE, ACCEPTED (11/6, 23:45–23:46 UTC) → built = 8b.0 + REKEY + 8b.1 + §9.96 restore + 8b.2

- **ABPTAG-RESTORE** (`abptag_restore_20261106.log`, REF 12b3e689, PA HEAD 12b3e689): pre a/b/c OK (pre_8b copy
  451,964,928 bytes); 16 guards OK; before words 626,309 · abp-tag 3,671 failing 16 · other rows 626,293 digest 5efa7864;
  in transaction changes 16 · failing 0 · words 626,309 · other rows digest 5efa7864 unchanged · 16 with strongs `'*'` ·
  GLOB 0; the 16 rows printed with the record's numbers; after failing 0; `ABPTAG-RESTORE RESULT: DONE`; journal none;
  exit=0.
- **8B2c** (`xref8b2c_20261106.log`, folders `xref8b2c_dry_20261106/` + `xref8b2c_apply_20261106/`): pre a–f OK (oracle
  0/0, 0 differ (declared 178), Greek-numbered non-abp-tag 0, words 626,309, xref 32,478); Greek-numbered snapshot 593,224
  rows; dry run oracle 0/0, split 3,671 / 10,236 / 12,191 / 4,409 / 1,971, verified 32,478, five remaining 0; planned
  tipnr 10,070 H->Greek + 166 '*'->Greek, lemma-only 11,959 H->'*' (232 already '*'), surface 4,128 H->'*' (281 already
  '*'), kept none 1,800 Hebrew + 171 '*', abp-tag 3,671; total rows changing 26,323; xref to write 32,478 (no-Hebrew
  4,521); is_pn outside 0. Apply: stale xref dropped, wrote 32,478 (no-Hebrew 4,521 = expected), applied 26,323, GLOB 0,
  all post-write checks pass; after words 626,309, xref 32,478, oracle 0/0, GLOB 0, Greek-numbered rows rewritten 0,
  journal none; `8B2b RESULT: DONE`; exit=0.
- Ruling chat 11/6: both ACCEPTED. Next: 8B2A (`lane3_rebuild_step` = 8b.2a) drafted, held.

## 8B2A (step 8b.2a, lane3_rebuild_step) drafted, held for the ruling chat (11/6)

Expected figures = the last 8b.2a run: `~/rekey/live_8b2a.log` (10/25 live rebuild; command `RUN_rebuild_trap_live.md:87`,
result recorded `CHARTER_rebuild_trap_fix.md:345`): `LANE-3 STEP: PASS` fixes (9, 0, 0) · gapfix (6, 0, 0) · fixes2
(7, 0, 0); the block reads that line and the 22 per-verse `=== V === (N cell edits)` lines from the log itself
(`grep -n`, path:line printed) and requires the dry run and the apply to reproduce them exactly (tripwire 5: per-pass
patch counts from the log). Line format = `lane3_rebuild_step.py:156-158`, unchanged since 10/25 (last change f9747889, comment dates only).
Lane-3 files pinned at 12b3e689 (committed bytes): fixes e8942de0 (changed 11/2 by 63744245 §9.77 R3: Isa 30:31, Jer
50:16 re-keyed to built's wording; entry count 9 unchanged) · gapfix 8c8ad0af · fixes2 e6a7efc7.
**Dry run:** `lane3_rebuild_step` has no dry-run mode and saves file by file, and gapfix joins brackets the fixes file
creates (Num 25:8 joins 2, 3), so a per-file dry run on built cannot work. The block copies the 18 lane-3 verses'
verses + words rows from built (read-only, built's own table layout) into a throwaway `lane3_dry.db`, runs the real
step on it, and applies to built only if the result line and all 22 per-verse lines equal the 10/25 log. After: built
must equal the dry copy on all 18 verses (all columns).
**Words checks:** 626,309 before/after; whole-table (rowid, strongs, strongs_base) snapshot diff 0; rows outside the 18
verses unchanged (all-column digest); inside them only english / english_head / greek_pos / bracket_id change
(`fix_lane3_star_merges.py:193-196`). Read-out from the files' ops: english 35 · greek_pos 38 · bracket_id 41
(english/greek_pos = `lane3_rebuild_step.py:8`); english_head depends on the rows.
**10 moved verses:** none is a lane-3 member — checked from the three files (18 distinct verses) and by the helper at
run time (STAGED-READ said the same). **Gen 46:26 pos 19:** fixes2 entry; shows as `=== Gen 46:26 === (2 cell edits)`,
BEFORE pos 19 "of Jacob's sons —" gpos - bid - [G5207] + pos 20 None [*], AFTER pos 19 'sons —' gpos 2 bid 1 + pos 20
"of Jacob's" gpos 1 bid 1, render PASS, contiguity PASS — printed in full by the block.
Tests: whole block in a fake home on a made-up built copy (626,309 words; the 18 verses in their pinned before-state):
DONE; re-paste STOP (folder); already applied STOP at the dry run, built unchanged; a changed pinned verse SKIP → STOP,
built unchanged; missing 10/25 log STOP. Helper sha256 9262e528f8e97f47b87da8f5f462b9eceec2ee92e5ea5989a2205f70576960e4.

### Block 8B2A (GATE REF 12b3e689; WRITES built: lane-3 english / english_head / greek_pos / bracket_id)
```bash
set +H
( set -uo pipefail
REF=12b3e689
echo "GATE REF ${REF} - 8B2A lane3_rebuild_step (step 8b.2a) on the built copy - dry run on a throwaway copy of the 18 lane-3 verses, apply only on the 10/25 picture - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "8B2A RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "8B2A RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "8B2A RESULT: STOP - PA has not pulled $REF"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
R=~/bible-db/bible_edupg_test_built_pre_8b_20261106.db
O=~/edition_upgrade_runs
L=~/rekey/live_8b2a.log
D="$O/lane3_8b2a_20261106"
M="$D/lane3_dry.db"
[ -f "$B" ] || { echo "8B2A RESULT: STOP - missing: $B"; exit 1; }
[ -s "$L" ] || { echo "8B2A RESULT: STOP - last 8b.2a run log missing or empty: $L"; exit 1; }
if [ -e "$D" ]; then echo "8B2A RESULT: STOP - output folder already exists (already ran?): $D"; exit 1; fi
t=$(sqlite3 -readonly "$B" "SELECT count(*) FROM sqlite_master WHERE type='trigger'") || { echo "8B2A RESULT: STOP - trigger read failed"; exit 1; }
echo "pre (a) triggers on built: $t (expect 0)"
[ "$t" = "0" ] || { echo "8B2A RESULT: STOP - built has triggers"; exit 1; }
if [ -e "$B-journal" ]; then echo "8B2A RESULT: STOP - $B-journal present (move it aside, never delete; bring it back)"; exit 1; fi
echo "pre (b) no -journal beside built: OK"
[ -s "$R" ] || { echo "8B2A RESULT: STOP - pre_8b rollback copy missing or empty: $R"; exit 1; }
echo "pre (c) pre_8b copy present: $(stat -c '%s bytes, %y' "$R") - built now $(stat -c '%s bytes' "$B") (size only)"
for fs in lane3_star_fixes.json:e8942de0cf5df9b998568f70ef66042b1c968564e8fb5781526887532dd98948 lane3_star_gapfix.json:8c8ad0afc76468eb3f32c1c3419a0ea30d10650d5c448365dcc86d746b6d36b2 lane3_star_fixes2.json:e6a7efc762ff5185f4cab2983dada481955f7aab92ca417d516703182c042b22; do
  f=${fs%%:*}; want=${fs#*:}; got=$(sha256sum < "scripts/$f" | cut -d' ' -f1)
  echo "lane-3 file $f sha256 ${got:0:8} (expect ${want:0:8})"
  [ "$got" = "$want" ] || { echo "8B2A RESULT: STOP - $f is not the pinned file"; exit 1; }
done
EXP="LANE-3 STEP: PASS  (patched, already, skipped per file: fixes (9, 0, 0) · gapfix (6, 0, 0) · fixes2 (7, 0, 0))"
echo "last 8b.2a run ($L), result line with its line number:"
grep -n "^LANE-3 STEP:" "$L"
[ "$(grep -c "^LANE-3 STEP:" "$L")" = "1" ] && [ "$(grep "^LANE-3 STEP:" "$L")" = "$EXP" ] || { echo "8B2A RESULT: STOP - the last run's result line is not: $EXP"; exit 1; }
LH=$(grep -E '^=== .+ === \(' "$L")
echo "last run: per-verse patch lines with their line numbers (expect 22):"
grep -nE '^=== .+ === \(' "$L"
[ "$(grep -cE '^=== .+ === \(' "$L")" = "22" ] || { echo "8B2A RESULT: STOP - the last run does not show 22 per-verse patch lines"; exit 1; }
mkdir -p "$D"
P="$D/lane3_8b2a_helper.py"
cat > "$P" <<'PY'
"""8B2A helper (one-off, edition upgrade stage D, step 8b.2a). Never writes the built copy.

  prep  <built.db> <dry.db> <state.json>
        Reads built read-only. Lists the lane-3 verses from the three pinned files, checks none is
        one of the 10 moved verses, checks words = 626,309, then writes a THROWAWAY copy of just
        those verses (their verses + words rows, built's own table layout) to <dry.db> for the dry
        run, and records built's before-state to <state.json>.
  check <built.db> <dry.db> <state.json>
        Reads built and the dry copy read-only after the real step ran on built:
          - words still 626,309
          - every words row outside the lane-3 verses unchanged (all columns, digest)
          - inside the lane-3 verses only english / english_head / greek_pos / bracket_id changed
            (fix_lane3_star_merges.py:193-196), same rows at the same positions
          - each lane-3 verse on built now reads exactly as the dry run left it (all columns)

Usage: python3 lane3_8b2a_helper.py prep|check <built.db> <dry.db> <state.json>
"""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

MODE, BUILT, DRY, STATE = sys.argv[1:5]
SCRIPTS = Path.home() / "bible-db" / "scripts"
FILES = ("lane3_star_fixes.json", "lane3_star_gapfix.json", "lane3_star_fixes2.json")
ALLOWED = ("english", "english_head", "greek_pos", "bracket_id")
MOVED = ("Gen 5:25", "Gen 5:26", "Gen 34:4", "Jos 2:4", "Jos 5:15", "Jdg 11:7", "2Ki 23:35", "Est 5:9",
         "Rom 9:29", "Eze 20:14")
WORDS_EXPECT = 626309
N_VERSES = 18


def stop(msg):
    print("8B2A RESULT: STOP - " + msg)
    sys.exit(1)


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


def lane3_verses():
    out = []
    for f in FILES:
        d = json.loads((SCRIPTS / f).read_text(encoding="utf-8"))
        d.pop("_comment", None)
        for v in d:
            if v not in out:
                out.append(v)
    return out


def key(v):
    book, rest = v.rsplit(" ", 1)
    ch, vs = rest.split(":")
    return book, int(ch), int(vs)


def verse_ids(c, verses):
    ids = {}
    for v in verses:
        r = c.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?", key(v)).fetchall()
        if not len(r) == 1:
            stop("%s: %d verse rows (expect 1)" % (v, len(r)))
        ids[v] = r[0][0]
    return ids


def columns(c):
    return [r[1] for r in c.execute("PRAGMA table_info(words)")]


def verse_rows(c, vid):
    return [list(r) for r in c.execute("SELECT rowid, * FROM words WHERE verse_id=? ORDER BY position, rowid", (vid,))]


def outside_digest(c, vids, cols):
    vi = cols.index("verse_id") + 1
    h = hashlib.sha256()
    n = 0
    for r in c.execute("SELECT rowid, * FROM words ORDER BY rowid"):
        if r[vi] in vids:
            continue
        h.update(repr(tuple(r)).encode("utf-8"))
        h.update(b"\n")
        n += 1
    return n, h.hexdigest()


if MODE == "prep":
    c = ro(BUILT)
    verses = lane3_verses()
    print("lane-3 verses in the three files: %d (expect %d): %s" % (len(verses), N_VERSES, ", ".join(verses)))
    if not len(verses) == N_VERSES:
        stop("lane-3 verse count is %d, not %d" % (len(verses), N_VERSES))
    hit = [v for v in MOVED if v in verses]
    print("of the 10 moved (re-keyed) verses, lane-3 members: %s (expect none)" % (", ".join(hit) or "none"))
    if hit:
        stop("a moved verse is a lane-3 member: %s" % hit)
    ids = verse_ids(c, verses)
    nw = c.execute("SELECT count(*) FROM words").fetchone()[0]
    print("words on built before: %d (expect %d)" % (nw, WORDS_EXPECT))
    if not nw == WORDS_EXPECT:
        stop("words before is %d" % nw)
    cols = columns(c)
    for need in ("id", "verse_id", "position", "english", "english_head", "strongs", "strongs_base",
                 "greek_pos", "bracket_id"):
        if need not in cols:
            stop("words has no column %s" % need)
    before = {v: verse_rows(c, ids[v]) for v in verses}
    n_out, dig = outside_digest(c, set(ids.values()), cols)
    if Path(DRY).exists():
        stop("dry copy already exists: %s" % DRY)
    d = sqlite3.connect(DRY)
    d.execute("PRAGMA journal_mode=DELETE")
    for t in ("verses", "words"):
        sql = c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0]
        d.execute(sql)
    qs = ",".join("?" * len(ids))
    vrows = c.execute("SELECT * FROM verses WHERE id IN (%s)" % qs, tuple(ids.values())).fetchall()
    d.executemany("INSERT INTO verses VALUES (%s)" % ",".join("?" * len(vrows[0])), vrows)
    wrows = c.execute("SELECT * FROM words WHERE verse_id IN (%s)" % qs, tuple(ids.values())).fetchall()
    d.executemany("INSERT INTO words VALUES (%s)" % ",".join("?" * len(wrows[0])), wrows)
    d.commit()
    d.close()
    Path(STATE).write_text(json.dumps({"verses": verses, "ids": ids, "cols": cols, "before": before,
                                       "outside_rows": n_out, "outside_digest": dig}), encoding="utf-8")
    print("dry copy: %d verses, %d words rows -> %s" % (len(vrows), len(wrows), DRY))
    print("built before: lane-3 verse rows %d - rows outside them %d, digest %s"
          % (sum(len(x) for x in before.values()), n_out, dig[:8]))
    print("8B2A PREP: OK")

elif MODE == "check":
    st = json.loads(Path(STATE).read_text(encoding="utf-8"))
    c, d = ro(BUILT), ro(DRY)
    cols = st["cols"]
    if not columns(c) == cols:
        stop("words columns changed")
    nw = c.execute("SELECT count(*) FROM words").fetchone()[0]
    n_out, dig = outside_digest(c, set(st["ids"].values()), cols)
    print("words on built after: %d (expect %d)" % (nw, WORDS_EXPECT))
    print("rows outside the lane-3 verses: %d, digest %s (expect %d, %s - unchanged)"
          % (n_out, dig[:8], st["outside_rows"], st["outside_digest"][:8]))
    bad = []
    if not nw == WORDS_EXPECT:
        bad.append("words after %d" % nw)
    if not (n_out == st["outside_rows"] and dig == st["outside_digest"]):
        bad.append("a row outside the lane-3 verses changed")
    changed = {k: 0 for k in ALLOWED}
    other = []
    same_as_dry = 0
    for v in st["verses"]:
        vid = st["ids"][v]
        b = st["before"][v]
        a = verse_rows(c, vid)
        if not ([r[0] for r in a] == [r[0] for r in b]):
            bad.append("%s: rows differ in number or rowid" % v)
            continue
        for rb, ra in zip(b, a):
            for i, name in enumerate(cols, start=1):
                if not rb[i] == ra[i]:
                    if name in ALLOWED:
                        changed[name] += 1
                    else:
                        other.append("%s rowid %s %s" % (v, ra[0], name))
        dr = [list(r) for r in d.execute("SELECT * FROM words WHERE verse_id=? ORDER BY position, rowid", (vid,))]
        if [r[1:] for r in a] == dr:
            same_as_dry += 1
        else:
            bad.append("%s: built does not read as the dry run left it" % v)
    print("cells changed on built (lane-3 verses): %s"
          % " - ".join("%s %d" % (k, changed[k]) for k in ALLOWED))
    print("cells changed in any other column: %d (expect 0)%s" % (len(other), (" " + "; ".join(other[:20])) if other else ""))
    print("lane-3 verses where built = the dry-run result (all columns): %d/%d" % (same_as_dry, len(st["verses"])))
    if other:
        bad.append("a column outside english/english_head/greek_pos/bracket_id changed")
    if bad:
        for b in bad:
            print("  problem: " + b)
        print("8B2A CHECK: FAIL")
        sys.exit(1)
    print("8B2A CHECK: OK")
else:
    stop("mode must be prep or check")
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = 9262e528f8e97f47b87da8f5f462b9eceec2ee92e5ea5989a2205f70576960e4 ] || { echo "8B2A RESULT: STOP - the pasted helper does not match the drafted one"; exit 1; }
PYTHONIOENCODING=utf-8 python3 "$P" prep "$B" "$M" "$D/state.json" || { echo "8B2A RESULT: STOP - prep did not pass (line above); built untouched"; exit 1; }
sqlite3 -readonly "$B" "SELECT rowid, strongs, quote(strongs_base) FROM words ORDER BY rowid" > "$D/strongs_before.tsv"
echo "snapshot: every words row (rowid, strongs, strongs_base) before: $(wc -l < "$D/strongs_before.tsv") rows (expect 626309)"
DRY=$(python3 scripts/lane3_rebuild_step.py "$M" 2>&1); d=$?
printf '%s\n' "$DRY" > "$D/dry_run_full.log"
echo "--- dry run on the throwaway copy (full output: $D/dry_run_full.log):"
grep -E '^=== |^SKIP|^ALREADY|render check|contiguity check|^APPLIED|^  .. lane3_star_|^LANE-3 STEP' <<< "$DRY"
echo "dry run exit $d (expect 0)"
[ "$d" -eq 0 ] || { echo "8B2A RESULT: STOP - dry run exit $d; built untouched"; exit 1; }
[ "$(grep "^LANE-3 STEP:" <<< "$DRY")" = "$EXP" ] || { echo "8B2A RESULT: STOP - dry run result line differs from the last run's; built untouched"; exit 1; }
[ "$(grep -E '^=== .+ === \(' <<< "$DRY")" = "$LH" ] || { echo "8B2A RESULT: STOP - dry run per-verse patch lines differ from the last run's; built untouched"; exit 1; }
echo "dry run = the 10/25 picture (PASS - fixes 9 / gapfix 6 / fixes2 7 patched - the same 22 per-verse lines) - applying to built"
APP=$(python3 scripts/lane3_rebuild_step.py "$B" 2>&1); a=$?
printf '%s\n' "$APP" > "$D/apply_full.log"
echo "--- apply on built (full output: $D/apply_full.log):"
grep -E '^=== |^SKIP|^ALREADY|render check|contiguity check|^APPLIED|^  .. lane3_star_|^LANE-3 STEP' <<< "$APP"
echo "--- Gen 46:26 (lane 3 at 8b.2a; fixes2) as the apply printed it:"
awk '/^=== Gen 46:26 ===/{p=1} p{print} p&&/contiguity check/{p=0}' <<< "$APP"
echo "apply exit $a (expect 0)"
AS=$(grep "^LANE-3 STEP:" <<< "$APP"); AH=$(grep -E '^=== .+ === \(' <<< "$APP")
sqlite3 -readonly "$B" "SELECT rowid, strongs, quote(strongs_base) FROM words ORDER BY rowid" > "$D/strongs_after.tsv"
DF=$(diff "$D/strongs_before.tsv" "$D/strongs_after.tsv"); GD=$(grep -c '^[<>]' <<< "$DF") || true
echo "words rows whose strongs or strongs_base changed (before/after snapshot diff lines): $GD (expect 0)"
CHK=$(PYTHONIOENCODING=utf-8 python3 "$P" check "$B" "$M" "$D/state.json" 2>&1); k=$?
echo "$CHK"
if [ -e "$B-journal" ]; then J=PRESENT; else J=none; fi
echo "journal after: $J (expect none)"
if [ "$a" -eq 0 ] && [ "$AS" = "$EXP" ] && [ "$AH" = "$LH" ] && [ "$GD" = "0" ] && [ "$k" -eq 0 ] && [ "$J" = "none" ]; then
  echo "8B2A RESULT: DONE - LANE-3 STEP PASS fixes 9 / gapfix 6 / fixes2 7 - built = the dry run on all 18 verses - strongs/strongs_base untouched - words 626309"; exit 0
fi
echo "8B2A RESULT: CHECK - an after-figure differs from the expected picture (lines above)"; exit 1
) 2>&1 | tee ~/edition_upgrade_runs/lane3_8b2a_20261106.log; echo "exit=${PIPESTATUS[0]}"
```

## 8B2A RAN — DONE, ACCEPTED (11/7, 01:28 UTC) → built = 8b.0 + REKEY + 8b.1 + §9.96 restore + 8b.2 + 8b.2a
Log `~/edition_upgrade_runs/lane3_8b2a_20261106.log` (folder `lane3_8b2a_20261106/`), PA HEAD 12b3e689, exit=0.
Pre (a) 0 · (b) OK · (c) pre_8b 451,964,928 bytes · the three lane-3 file shas matched (e8942de0 / 8c8ad0af / e6a7efc7).
10/25 log `~/rekey/live_8b2a.log`: result line at :1142, the 22 per-verse lines at :4–:1107 (Mat 9:11 :4 … Gen 46:26
:1050, Mat 27:26 :1107). Prep: 18 lane-3 verses, moved-verse members none, words 626,309, dry copy 368 rows, rows
outside 625,941 digest 3718e4db. Dry run and apply both `LANE-3 STEP: PASS` fixes (9, 0, 0) · gapfix (6, 0, 0) ·
fixes2 (7, 0, 0), the same 22 per-verse lines; fixes-pass contiguity FAIL only at 2Sa 14:4 (1,4), Num 25:8 (2,4)(3,15),
Num 25:14 (2,5), Num 25:15 (2,4), filled by gapfix. Gen 46:26 (fixes2): pos 19 "of Jacob's sons —" → 'sons —' gpos 2
bid 1, pos 20 None → "of Jacob's" gpos 1 bid 1; prose before = after = verses.text; render + contiguity PASS. After:
strongs/strongs_base snapshot diff 0 · words 626,309 · outside rows 625,941 digest 3718e4db unchanged · cells english 35
· english_head 17 · greek_pos 38 · bracket_id 41 · other columns 0 · built = dry run 18/18 · journal none ·
`8B2A RESULT: DONE`. **Ruling chat: ACCEPTED.** Next: 8B3 (the four builders).

## 8B3 (step 8b.3: the four scripts) drafted, held for the ruling chat (11/7)

Expected figures = the last 8b.3 run (10/25, commands `RUN_rebuild_trap_live.md:91-97`, results `CHARTER_rebuild_trap_fix.md:468-470`):
`~/rekey/live_8b3_id.log` (split 3,671 / 10,236 / 12,191 / 4,409 / 1,971, `Wrote pn_greek_identity: 32,478 rows.`),
`~/rekey/live_8b3_bind.log` (`render 15,378 + HOT 68`, slot 102 landable / 0 refused, `pn_slot_binding written: 102 rows.`,
plus the hand-ruling / witness / tipnr_entities lines), `~/rekey/live_8b3_unfind.log` (PASS 0 / 0),
`~/rekey/live_8b3_twoder.log` (`controls: 10  failed: 0`). The block greps each log with `-n` (path:line printed) and
requires the dry run to reproduce those lines. None of the four scripts or their inputs changed since 10/24 (git log).
**Words never written (read from each main()):** `build_pn_greek_identity.py` writes only `pn_greek_identity` (:536-552)
plus its receipt file `docs/tickets/greek_header_split.txt` (:508-526); `build_entity_binding.py` reads through a
read-only connection (:131) and writes only `tipnr_entities` / `tipnr_entity_refs` / `pn_binding` (:462-496), two tracked
dump files `scripts/pn_binding_{hot,numonly}.txt` (:438-443) and an ignored one (:423); its `build_slot_binding.land()`
writes only `pn_slot_binding` (`build_slot_binding.py:147-155`); both audits open read-only (`audit_unfindability.py:55`,
`audit_two_derivations.py:32`). The block checks it anyway: words 626,309 and a per-row fingerprint of every words row
(all columns) before/after, diff 0; abp_surface count + digest unchanged.
**Dry run first:** the binder has a dry-run mode but the identity builder's prints no rows, so the block copies what
the four scripts read (verses; the proper-noun words rows + every row of the pn_slot_rulings verses; abp_surface at
those keys; pn_binding, pn_hebrew_xref, pn_greek_identity, tipnr_*, pn_slot_binding, metav_*) into a throwaway copy,
runs identity → binding → two-derivations there, and compares the five rebuilt tables row by row with built's
before-snapshot (`before.db`, plus `identity_before.tsv` / `binding_before.tsv`). Expected delta 0 on all five
(declared_deltas.json: pn_binding + tipnr_entities identical; identity = the 6 key moves only, already on built).
Any difference → STOP before built is touched, listed in full if ≤ 40, else counts by class + the first 40. Then the
real runs on built in order, each only if the previous one's output = the dry run's; after: built = the dry copy and
0 differences vs before, the 6 REKEY records and the 16 §9.96 abp-tag rows printed (retire's abp-tag check 16/16).
**Unfindability matches by position** (the open geometry-aware pre-req, `/rebuild-words` step 3), and REKEY moved 6
name records. Against src as-is it fails exactly on the 5 in-scope moved records (2Ki 23:35@7 lemma-only, Est 5:9@13
surface, Gen 5:25@2 / 5:26@2 / 34:4@2 tipnr; Jos 5:15@26 is 'none', out of scope) — the block runs it that way and
requires exactly those 5. The PASS run uses a throwaway copy of src's identity + xref with the committed moves file
(`pn_greek_identity_key_moves_20261106.tsv`) applied: expected = the 10/25 PASS 0 / 0. The audit reads only words +
xref on the after side, so the 8b.3 builders cannot move its result; it is re-run after them anyway.
The binder's two tracked dumps are copied into the run folder and put back with `git checkout` after each run.
Tests (fake home, made-up built copy with the 6 moved records, the 16 abp-tag rows and the twoder controls; the real
scripts): DONE; re-paste STOP; one changed row → STOP at the dry-run delta with the row listed, built untouched;
class shift → STOP at the split; missing 10/25 log → STOP; 50 changed rows → counts by class + first 40.

### Block 8B3 (GATE REF 12b3e689; WRITES built: pn_greek_identity, pn_binding, tipnr_entities, tipnr_entity_refs, pn_slot_binding)
```bash
set +H
( set -uo pipefail
REF=12b3e689
echo "GATE REF ${REF} - 8B3 the four 8b.3 scripts (build_pn_greek_identity, build_entity_binding, audit_unfindability, audit_two_derivations) on the built copy - dry run on a throwaway copy, apply only on the expected picture - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "8B3 RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "8B3 RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "8B3 RESULT: STOP - PA has not pulled $REF"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
R=~/bible-db/bible_edupg_test_built_pre_8b_20261106.db
O=~/edition_upgrade_runs
D="$O/pn8b3_20261107"
M="$D/dry.db"
U="$D/unf_before_rekeyed.db"
L1=~/rekey/live_8b3_id.log; L2=~/rekey/live_8b3_bind.log; L3=~/rekey/live_8b3_unfind.log; L4=~/rekey/live_8b3_twoder.log
RC=docs/tickets/greek_header_split.txt
TX="scripts/pn_binding_hot.txt scripts/pn_binding_numonly.txt"
[ -f "$B" ] || { echo "8B3 RESULT: STOP - missing: $B"; exit 1; }
[ -f "$S" ] || { echo "8B3 RESULT: STOP - missing: $S"; exit 1; }
for f in "$L1" "$L2" "$L3" "$L4"; do [ -s "$f" ] || { echo "8B3 RESULT: STOP - last 8b.3 run log missing or empty: $f"; exit 1; }; done
if [ -e "$D" ]; then echo "8B3 RESULT: STOP - output folder already exists (already ran?): $D"; exit 1; fi
t=$(sqlite3 -readonly "$B" "SELECT count(*) FROM sqlite_master WHERE type='trigger'") || { echo "8B3 RESULT: STOP - trigger read failed"; exit 1; }
echo "pre (a) triggers on built: $t (expect 0)"
[ "$t" = "0" ] || { echo "8B3 RESULT: STOP - built has triggers"; exit 1; }
for f in "$B" "$S"; do if [ -e "$f-journal" ]; then echo "8B3 RESULT: STOP - $f-journal present (move it aside, never delete; bring it back)"; exit 1; fi; done
echo "pre (b) no -journal beside built or src: OK"
[ -s "$R" ] || { echo "8B3 RESULT: STOP - pre_8b rollback copy missing or empty: $R"; exit 1; }
echo "pre (c) pre_8b copy present: $(stat -c '%s bytes, %y' "$R") - built now $(stat -c '%s bytes' "$B") (size only)"
EXP_ID=$(printf '%s\n' "  abp-tag    3,671" "  tipnr      10,236" "  lemma-only 12,191" "  surface    4,409" "  none       1,971" "Wrote pn_greek_identity: 32,478 rows.")
P_ID='^  (abp-tag|tipnr|lemma-only|surface|none) +[0-9,]+$|^Wrote pn_greek_identity: '
P_BIND='^  pn_binding      : |^  tipnr_entities  : |^slot rulings: |^pn_slot_binding written: |^Hand rulings: |^Witness |REFUSED|FAILED|OVERRIDE'
P_UNF='^findable-(before|after) +check failures: |^UNFINDABILITY GATE: '
echo "--- last 8b.3 run (10/25), the lines this run must reproduce, with their line numbers:"
echo "$L1:"; grep -nE "$P_ID" "$L1"
[ "$(grep -E "$P_ID" "$L1")" = "$EXP_ID" ] || { echo "8B3 RESULT: STOP - the 10/25 identity log does not show the ruled split 3,671 / 10,236 / 12,191 / 4,409 / 1,971 and 32,478 rows"; exit 1; }
echo "$L2:"; grep -nE "$P_BIND" "$L2"
LBIND=$(grep -E "$P_BIND" "$L2")
grep -qxF "  pn_binding      : render 15,378 + HOT 68" <<< "$LBIND" && grep -qE '^slot rulings: 102 landable, 0 refused of ' <<< "$LBIND" && grep -qxF "pn_slot_binding written: 102 rows." <<< "$LBIND" || { echo "8B3 RESULT: STOP - the 10/25 binding log does not show render 15,378 + HOT 68 and 102 slot binds / 0 refused"; exit 1; }
[ "$(grep -cE 'REFUSED|FAILED' <<< "$LBIND")" = "0" ] || { echo "8B3 RESULT: STOP - the 10/25 binding log shows a refusal or failure"; exit 1; }
echo "$L3:"; grep -nE "$P_UNF|^rows in scope" "$L3"
LUNF=$(grep -E "$P_UNF" "$L3")
[ "$LUNF" = "$(printf '%s\n' "findable-before check failures: 0 (expected 0)" "findable-after  check failures: 0 (expected 0)" "UNFINDABILITY GATE: PASS — zero findable-before/unfindable-after.")" ] || { echo "8B3 RESULT: STOP - the 10/25 unfindability log is not PASS 0 / 0"; exit 1; }
echo "$L4:"; grep -nE '^Hebrew-keyed PN numbers: |^agree: |^controls: ' "$L4"
LTWO=$(grep -E '^controls: ' "$L4")
[ "$LTWO" = "controls: 10  failed: 0" ] || { echo "8B3 RESULT: STOP - the 10/25 two-derivations log is not controls 10 failed 0"; exit 1; }
mkdir -p "$D"
P="$D/pn8b3_helper.py"
cat > "$P" <<'PY'
"""8B3 helper (one-off, edition upgrade stage D, step 8b.3). Never writes the built copy or src.

  prep    <built.db> <dry.db> <dir>   read built; save its before-state (the five tables the two
                                      builders replace -> <dir>/before.db + two snapshot files;
                                      words per-row fingerprints; abp_surface count + digest);
                                      write a THROWAWAY copy (<dry.db>) holding just what the four
                                      8b.3 scripts read, for the dry run
  srcmini <src.db> <out.db>           a THROWAWAY copy of src's identity + xref (+ words keys) with
                                      the committed REKEY moves applied, as the unfindability
                                      audit's before side (its matching is by position)
  unf1    <audit.log> <src.db>        the as-is audit (src vs built): findable-after failures must
                                      be exactly the in-scope records at the old REKEY positions
  delta   <a.db> <b.db> <label>       row-level differences in the five tables, a -> b
  check   <built.db> <dry.db> <dir>   after the apply: words + abp_surface unchanged, built = dry
                                      copy on the five tables, delta vs before, the 6 re-keyed
                                      records and the 16 abp-tag rows

Usage: python3 pn8b3_helper.py <mode> ...
"""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path.home() / "bible-db"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
MOVES = REPO / "tests" / "fixtures" / "edition_upgrade" / "pn_greek_identity_key_moves_20261106.tsv"
WORDS_EXPECT = 626309
IDENTITY_EXPECT = 32478
UNF1_EXPECT = 5
SCOPE = ("tipnr", "lemma-only", "surface")
# the five tables build_pn_greek_identity / build_entity_binding (+ build_slot_binding.land) replace
OUT = (("pn_greek_identity", ("verse_id", "position")),
       ("pn_binding", ("book", "chapter", "verse", "name")),
       ("tipnr_entities", ("uniq",)),
       ("tipnr_entity_refs", None),
       ("pn_slot_binding", ("book", "chapter", "verse", "position")))
# everything the four scripts read (main() of each, top to bottom)
READS = ("verses", "words", "abp_surface", "pn_binding", "pn_hebrew_xref", "pn_greek_identity",
         "tipnr_entities", "tipnr_entity_refs", "pn_slot_binding", "metav_places",
         "metav_place_aliases", "metav_people", "metav_people_aliases")
ABPTAG16 = ((21270, 1), (23928, 2), (24148, 16), (24461, 2), (24627, 9), (25170, 6), (25225, 0),
            (25374, 19), (25553, 12), (26424, 2), (27237, 1), (28665, 6), (29083, 13), (29141, 13),
            (29142, 0), (31003, 4))


def stop(msg):
    print("8B3 RESULT: STOP - " + msg)
    sys.exit(1)


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


def tables(c):
    return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def cols(c, t):
    return [r[1] for r in c.execute("PRAGMA table_info(%s)" % t)]


def moves():
    out = []
    for ln in MOVES.read_text(encoding="utf-8").splitlines()[1:]:
        if ln.strip():
            v, o, n = ln.split("\t")
            out.append((int(v), int(o), int(n)))
    if not len(out) == 6:
        stop("moves file has %d rows, not 6" % len(out))
    return out


def ref(c, vid):
    r = c.execute("SELECT book, chapter, verse FROM verses WHERE id=?", (vid,)).fetchone()
    return "%s %d:%d" % r if r else "verse %s ?" % vid


def words_fingerprints(c, path):
    h = hashlib.sha256()
    n = 0
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in c.execute("SELECT rowid, * FROM words ORDER BY rowid"):
            line = "%s\t%s\n" % (r[0], hashlib.sha1(repr(tuple(r)).encode("utf-8")).hexdigest())
            f.write(line)
            h.update(line.encode("utf-8"))
            n += 1
    return n, h.hexdigest()


def surface_digest(c):
    rows = sorted(repr(tuple(r)) for r in c.execute("SELECT * FROM abp_surface"))
    h = hashlib.sha256()
    for s in rows:
        h.update(s.encode("utf-8"))
        h.update(b"\n")
    return len(rows), h.hexdigest()


def keyed(c, t, key):
    cs = cols(c, t)
    d = {}
    for r in c.execute("SELECT * FROM %s" % t):
        k = tuple(r[cs.index(x)] for x in key) if key else tuple(r)
        d.setdefault(k, []).append(tuple(r))
    for k in d:
        d[k].sort(key=repr)
    return cs, d


def delta(a, b, refc):
    """Print row-level differences a -> b on the five tables. Returns the total."""
    total = 0
    for t, key in OUT:
        ca, da = keyed(a, t, key)
        cb, db = keyed(b, t, key)
        if not ca == cb:
            print("  %s: columns differ %s -> %s" % (t, ca, cb))
            total += 1
            continue
        rem = sorted((k for k in da if k not in db), key=repr)
        add = sorted((k for k in db if k not in da), key=repr)
        chg = sorted((k for k in da if k in db and not da[k] == db[k]), key=repr)
        n = len(rem) + len(add) + len(chg)
        total += n
        print("  %s: rows %d -> %d - changed %d, added %d, removed %d"
              % (t, sum(len(x) for x in da.values()), sum(len(x) for x in db.values()), len(chg), len(add), len(rem)))
        if not n:
            continue
        si = ca.index("source") if t == "pn_greek_identity" else None
        ri = ca.index("render") if t == "pn_binding" else None
        def cls(rows):
            if si is not None:
                return rows[0][si]
            if ri is not None:
                return "render=%s" % rows[0][ri]
            return t
        classes = {}
        for k in chg:
            c_ = "changed %s -> %s" % (cls(da[k]), cls(db[k]))
            classes[c_] = classes.get(c_, 0) + 1
        for k in add:
            c_ = "added %s" % cls(db[k])
            classes[c_] = classes.get(c_, 0) + 1
        for k in rem:
            c_ = "removed %s" % cls(da[k])
            classes[c_] = classes.get(c_, 0) + 1
        if n > 40:
            print("    by class: " + " - ".join("%s %d" % kv for kv in sorted(classes.items())))
            print("    first 40:")
        shown = 0
        for kind, ks, src in (("CHANGED", chg, None), ("ADDED", add, db), ("REMOVED", rem, da)):
            for k in ks:
                if shown == 40:
                    break
                shown += 1
                where = ("  [%s]" % ref(refc, k[0])) if t == "pn_greek_identity" else ""
                if kind == "CHANGED":
                    print("    CHANGED %s%s: %s -> %s" % (k, where, da[k], db[k]))
                else:
                    print("    %s %s%s: %s" % (kind, k, where, src[k]))
    return total


MODE = sys.argv[1]

if MODE == "prep":
    B, DRY, DIR = sys.argv[2], sys.argv[3], Path(sys.argv[4])
    c = ro(B)
    have = tables(c)
    miss = [t for t in READS if t not in have]
    if miss:
        stop("built has no table(s) %s" % miss)
    nw = c.execute("SELECT count(*) FROM words").fetchone()[0]
    ni = c.execute("SELECT count(*) FROM pn_greek_identity").fetchone()[0]
    print("words on built before: %d (expect %d) - identity rows %d (expect %d)" % (nw, WORDS_EXPECT, ni, IDENTITY_EXPECT))
    if not (nw == WORDS_EXPECT and ni == IDENTITY_EXPECT):
        stop("words or identity count before")
    for v, o, n in moves():
        at_new = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, n)).fetchone()[0]
        at_old = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()[0]
        if not (at_new == 1 and at_old == 0):
            stop("REKEY record %s %d->%d: %d at new, %d at old on built" % (ref(c, v), o, n, at_new, at_old))
    print("REKEY records on built: 6/6 at their new positions, none at the old")
    if Path(DRY).exists() or (DIR / "before.db").exists():
        stop("dry copy or before.db already exists")
    # before-state of the five tables the builders replace
    bconn = sqlite3.connect(str(DIR / "before.db"), uri=True)
    bconn.execute("PRAGMA journal_mode=DELETE")
    bconn.execute("ATTACH DATABASE ? AS b", ("file:%s?mode=ro" % B,))
    for t, _k in OUT:
        bconn.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
        bconn.execute("INSERT INTO main.%s SELECT * FROM b.%s" % (t, t))
    bconn.execute("CREATE TABLE verses AS SELECT id, book, chapter, verse FROM b.verses")
    bconn.commit()
    bconn.execute("DETACH DATABASE b")
    bconn.close()
    for t, order, f in (("pn_greek_identity", "verse_id, position", "identity_before.tsv"),
                        ("pn_binding", "book, chapter, verse, name, entity_uniq", "binding_before.tsv")):
        cs = cols(c, t)
        with open(DIR / f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(cs) + "\n")
            n = 0
            for r in c.execute("SELECT * FROM %s ORDER BY %s" % (t, order)):
                fh.write("\t".join(repr(x) for x in r) + "\n")
                n += 1
        print("snapshot %s before: %d rows -> %s" % (t, n, DIR / f))
    nwf, wdig = words_fingerprints(c, DIR / "words_before.tsv")
    ns, sdig = surface_digest(c)
    print("words fingerprints before: %d rows, digest %s - abp_surface before: %d rows, digest %s" % (nwf, wdig[:8], ns, sdig[:8]))
    # the throwaway copy: what the four scripts read
    from build_slot_binding import read_tsv
    slot_v = set()
    for r in read_tsv():
        x = c.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                      (r["book"], int(r["chapter"]), int(r["verse"]))).fetchone()
        if x:
            slot_v.add(x[0])
    d = sqlite3.connect(DRY, uri=True)
    d.execute("PRAGMA journal_mode=DELETE")
    d.execute("ATTACH DATABASE ? AS b", ("file:%s?mode=ro" % B,))
    for t in READS:
        d.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
    d.execute("CREATE TEMP TABLE sv (id INTEGER PRIMARY KEY)")
    d.executemany("INSERT INTO sv VALUES (?)", [(v,) for v in sorted(slot_v)])
    for t in READS:
        if t == "words":
            d.execute("INSERT INTO main.words SELECT * FROM b.words WHERE is_pn=1 OR verse_id IN (SELECT id FROM sv)")
        elif t == "abp_surface":
            d.execute("INSERT INTO main.abp_surface SELECT * FROM b.abp_surface s WHERE EXISTS "
                      "(SELECT 1 FROM main.words w WHERE w.verse_id=s.verse_id AND w.position=s.position)")
        else:
            d.execute("INSERT INTO main.%s SELECT * FROM b.%s" % (t, t))
    for (sql,) in c.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND tbl_name IN (%s)"
                            % ",".join("?" * len(READS)), READS):
        d.execute(sql)
    d.commit()
    counts = {t: d.execute("SELECT count(*) FROM main.%s" % t).fetchone()[0] for t in READS}
    d.execute("DETACH DATABASE b")
    d.close()
    print("dry copy: " + " - ".join("%s %d" % (t, counts[t]) for t in READS))
    print("  (words = the proper-noun rows + every row of the %d verses pn_slot_rulings.tsv names)" % len(slot_v))
    json.dump({"words_rows": nwf, "words_digest": wdig, "surface_rows": ns, "surface_digest": sdig},
              open(DIR / "state.json", "w", encoding="utf-8"))
    print("8B3 PREP: OK")

elif MODE == "srcmini":
    S, OUTDB = sys.argv[2], sys.argv[3]
    c = ro(S)
    if Path(OUTDB).exists():
        stop("exists: %s" % OUTDB)
    d = sqlite3.connect(OUTDB, uri=True)
    d.execute("PRAGMA journal_mode=DELETE")
    d.execute("ATTACH DATABASE ? AS s", ("file:%s?mode=ro" % S,))
    for t in ("pn_greek_identity", "pn_hebrew_xref"):
        d.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
        d.execute("INSERT INTO main.%s SELECT * FROM s.%s" % (t, t))
    d.execute("CREATE TABLE words (verse_id INTEGER, position INTEGER, strongs_base TEXT)")
    d.execute("INSERT INTO main.words SELECT verse_id, position, strongs_base FROM s.words")
    for v, o, n in moves():
        for t in ("pn_greek_identity", "pn_hebrew_xref"):
            a = d.execute("SELECT count(*) FROM main.%s WHERE verse_id=? AND position=?" % t, (v, o)).fetchone()[0]
            b = d.execute("SELECT count(*) FROM main.%s WHERE verse_id=? AND position=?" % t, (v, n)).fetchone()[0]
            if not (a == 1 and b == 0):
                stop("src %s %s %d->%d: %d at old, %d at new" % (t, ref(c, v), o, n, a, b))
            d.execute("UPDATE main.%s SET position=? WHERE verse_id=? AND position=?" % t, (n, v, o))
        print("  src record %s (verse_id %d) pos %d -> %d: identity + xref moved" % (ref(c, v), v, o, n))
    d.commit()
    ni = d.execute("SELECT count(*) FROM main.pn_greek_identity").fetchone()[0]
    nx = d.execute("SELECT count(*) FROM main.pn_hebrew_xref").fetchone()[0]
    nw = d.execute("SELECT count(*) FROM main.words").fetchone()[0]
    d.execute("DETACH DATABASE s")
    d.close()
    print("re-keyed src copy: identity %d - xref %d - words keys %d -> %s" % (ni, nx, nw, OUTDB))
    print("8B3 SRCMINI: OK")

elif MODE == "unf1":
    LOG, S = sys.argv[2], sys.argv[3]
    c = ro(S)
    exp = set()
    for v, o, n in moves():
        r = c.execute("SELECT source FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()
        print("  src record %s (verse_id %d) at old pos %d: class %s%s"
              % (ref(c, v), v, o, r[0] if r else None, " (in the audit's scope)" if r and r[0] in SCOPE else " (out of scope)"))
        if r and r[0] in SCOPE:
            exp.add((v, o))
    text = Path(LOG).read_text(encoding="utf-8").splitlines()
    got = set()
    nb = na = None
    for ln in text:
        if ln.startswith("findable-before check failures: "):
            nb = ln.split(": ")[1].split()[0]
        if ln.startswith("findable-after  check failures: "):
            na = ln.split(": ")[1].split()[0]
        if ln.startswith("  AFTER ("):
            k = ln[len("  AFTER ("):].split(")")[0].split(",")
            got.add((int(k[0]), int(k[1])))
    print("as-is audit: before failures %s (expect 0) - after failures %s (expect %d) - failing keys = old REKEY keys in scope: %s"
          % (nb, na, UNF1_EXPECT, "yes" if got == exp else "NO (got %s, expect %s)" % (sorted(got), sorted(exp))))
    if not (nb == "0" and na == str(UNF1_EXPECT) and len(exp) == UNF1_EXPECT and got == exp):
        stop("the as-is unfindability audit is not exactly the moved-position picture")
    print("8B3 UNF1: OK")

elif MODE == "delta":
    A, Bp, label = sys.argv[2], sys.argv[3], sys.argv[4]
    a, b = ro(A), ro(Bp)
    print("delta, %s:" % label)
    n = delta(a, b, a)
    print("  total row differences: %d (expect 0)" % n)
    sys.exit(0 if n == 0 else 1)

elif MODE == "check":
    B, DRY, DIR = sys.argv[2], sys.argv[3], Path(sys.argv[4])
    st = json.load(open(DIR / "state.json", encoding="utf-8"))
    c, d, bef = ro(B), ro(DRY), ro(str(DIR / "before.db"))
    bad = []
    nw = c.execute("SELECT count(*) FROM words").fetchone()[0]
    nwf, wdig = words_fingerprints(c, DIR / "words_after.tsv")
    a_lines = (DIR / "words_after.tsv").read_text(encoding="utf-8").splitlines()
    b_lines = (DIR / "words_before.tsv").read_text(encoding="utf-8").splitlines()
    wdiff = sum(1 for x, y in zip(b_lines, a_lines) if not x == y) + abs(len(a_lines) - len(b_lines))
    print("words on built after: %d (expect %d) - per-row fingerprint lines differing from before: %d (expect 0) - digest %s (before %s)"
          % (nw, WORDS_EXPECT, wdiff, wdig[:8], st["words_digest"][:8]))
    if not (nw == WORDS_EXPECT and wdiff == 0 and wdig == st["words_digest"]):
        bad.append("words changed")
    ns, sdig = surface_digest(c)
    print("abp_surface after: %d rows, digest %s (expect %d, %s - unchanged)" % (ns, sdig[:8], st["surface_rows"], st["surface_digest"][:8]))
    if not (ns == st["surface_rows"] and sdig == st["surface_digest"]):
        bad.append("abp_surface changed")
    print("built after vs the dry copy (must be identical):")
    if delta(d, c, c):
        bad.append("built differs from the dry run")
    print("built after vs built before (the snapshot):")
    if delta(bef, c, c):
        bad.append("a table differs from its before-snapshot")
    print("the 6 REKEY records on built after (verse_id, position, greek_strongs, greek_lemma, source, hebrew_base | xref | words english, strongs, strongs_base, is_pn):")
    for v, o, n in moves():
        g = c.execute("SELECT * FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, n)).fetchone()
        x = c.execute("SELECT hebrew_base, class FROM pn_hebrew_xref WHERE verse_id=? AND position=?", (v, n)).fetchone()
        w = c.execute("SELECT english, strongs, strongs_base, is_pn FROM words WHERE verse_id=? AND position=?", (v, n)).fetchone()
        old = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()[0]
        print("  %s new pos %d: %s | xref %s | words %s | identity rows at old pos %d: %d" % (ref(c, v), n, g, x, w, o, old))
        if g is None or old:
            bad.append("REKEY record %s" % ref(c, v))
    print("the 16 abp-tag rows (9.96) on built after (identity | words strongs, strongs_base) - retire's abp-tag check:")
    ok16 = 0
    for v, p in ABPTAG16:
        g = c.execute("SELECT greek_strongs, greek_lemma, source, hebrew_base FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, p)).fetchone()
        w = c.execute("SELECT english, strongs, strongs_base FROM words WHERE verse_id=? AND position=?", (v, p)).fetchone()
        good = bool(g and w and g[2] == "abp-tag" and w[2] == g[0] and (w[2] or "").startswith("G") and g[3] is None)
        ok16 += good
        print("  %s (verse_id %d) pos %d: %s | %s | %s" % (ref(c, v), v, p, g, w, "OK" if good else "FAIL"))
    print("abp-tag check on the 16: %d/16 OK" % ok16)
    if not ok16 == 16:
        bad.append("abp-tag rows")
    if bad:
        for b_ in bad:
            print("  problem: " + b_)
        print("8B3 CHECK: FAIL")
        sys.exit(1)
    print("8B3 CHECK: OK")
else:
    stop("unknown mode")
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = ac99767f6b85ea7f68487f433760fce5ef1a2930e6e38fb97fd102439214bb56 ] || { echo "8B3 RESULT: STOP - the pasted helper does not match the drafted one"; exit 1; }
if [ -f "$RC" ]; then cp "$RC" "$D/greek_header_split_before.txt"; echo "header receipt on PA before: $(wc -l < "$RC") lines (kept as $D/greek_header_split_before.txt)"; else echo "header receipt on PA before: none"; fi
python3 "$P" prep "$B" "$M" "$D" || { echo "8B3 RESULT: STOP - prep did not pass (line above); built untouched"; exit 1; }
python3 "$P" srcmini "$S" "$U" || { echo "8B3 RESULT: STOP - re-keyed src copy did not pass (line above); built untouched"; exit 1; }
echo "=== DRY RUN on the throwaway copy (built untouched) ==="
DID=$(python3 scripts/build_pn_greek_identity.py "$M" --apply 2>&1); di=$?
printf '%s\n' "$DID" > "$D/dry_identity.log"; cp "$RC" "$D/greek_header_split_dry.txt"
echo "--- 1 build_pn_greek_identity (full output: $D/dry_identity.log):"
grep -E "$P_ID|^identity split|^name-match gate|^pn_binding render rows|^proper-noun words|^pn_hebrew_xref loaded|^hand-table|^receipt written" <<< "$DID"
echo "exit $di (expect 0)"
[ "$di" -eq 0 ] && [ "$(grep -E "$P_ID" <<< "$DID")" = "$EXP_ID" ] || { echo "8B3 RESULT: STOP - dry identity build is not the ruled split / 32,478; built untouched"; exit 1; }
DBD=$(python3 scripts/build_entity_binding.py "$M" --apply 2>&1); db=$?
printf '%s\n' "$DBD" > "$D/dry_binding.log"
for f in $TX; do cp "$f" "$D/$(basename "$f" .txt)_dry.txt"; done; git checkout -- $TX
echo "--- 2 build_entity_binding (full output: $D/dry_binding.log; its two scripts/ dumps kept in $D and put back in the repo):"
grep -E "$P_BIND" <<< "$DBD"
echo "exit $db (expect 0)"
[ "$db" -eq 0 ] && [ "$(grep -E "$P_BIND" <<< "$DBD")" = "$LBIND" ] || { echo "8B3 RESULT: STOP - dry binding lines differ from the 10/25 run; built untouched"; exit 1; }
DTW=$(python3 scripts/audit_two_derivations.py "$M" 2>&1); dt=$?
printf '%s\n' "$DTW" > "$D/dry_twoder.log"
echo "--- 4 audit_two_derivations on the dry copy (full output: $D/dry_twoder.log):"
grep -E '^Hebrew-keyed PN numbers: |^agree: |^\[(PASS|FAIL)\] |^controls: ' <<< "$DTW"
echo "exit $dt (expect 0)"
[ "$dt" -eq 0 ] && [ "$(grep -E '^controls: ' <<< "$DTW")" = "$LTWO" ] || { echo "8B3 RESULT: STOP - dry two-derivations is not controls 10 failed 0; built untouched"; exit 1; }
U1=$(python3 scripts/audit_unfindability.py "$S" "$B" --list 2>&1); u1=$?
printf '%s\n' "$U1" > "$D/unf_asis.log"
echo "--- 3a audit_unfindability as-is, src vs built (position-keyed; full output: $D/unf_asis.log):"
grep -E "$P_UNF|^rows in scope|^  (BEFORE|AFTER) " <<< "$U1"
echo "exit $u1 (expect 1: fails on the moved records only)"
[ "$u1" -eq 1 ] && python3 "$P" unf1 "$D/unf_asis.log" "$S" || { echo "8B3 RESULT: STOP - as-is unfindability is not the moved-position picture; built untouched"; exit 1; }
U2=$(python3 scripts/audit_unfindability.py "$U" "$B" --list 2>&1); u2=$?
printf '%s\n' "$U2" > "$D/unf_rekeyed.log"
echo "--- 3b audit_unfindability, re-keyed src copy vs built (full output: $D/unf_rekeyed.log):"
grep -E "$P_UNF|^rows in scope|^  (BEFORE|AFTER) " <<< "$U2"
echo "exit $u2 (expect 0)"
[ "$u2" -eq 0 ] && [ "$(grep -E "$P_UNF" <<< "$U2")" = "$LUNF" ] || { echo "8B3 RESULT: STOP - unfindability (re-keyed) is not PASS 0 / 0; built untouched"; exit 1; }
python3 "$P" delta "$D/before.db" "$M" "built before -> dry copy after the two builders" || { echo "8B3 RESULT: STOP - the dry run changes rows (listed above); built untouched"; exit 1; }
echo "dry run = the expected picture (split + 32,478 - binding lines = 10/25 - controls 10/0 - unfindability 0/5 as-is, 0/0 re-keyed - 0 row differences) - applying to built"
echo "=== APPLY on built, in order ==="
AID=$(python3 scripts/build_pn_greek_identity.py "$B" --apply 2>&1); ai=$?
printf '%s\n' "$AID" > "$D/apply_identity.log"; cp "$RC" "$D/greek_header_split_apply.txt"
echo "--- 1 build_pn_greek_identity on built (full output: $D/apply_identity.log):"
grep -E "$P_ID" <<< "$AID"
echo "exit $ai (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$AID")" = "$(sed 1d <<< "$DID")" ] && echo yes || echo NO)"
[ "$ai" -eq 0 ] && [ "$(sed 1d <<< "$AID")" = "$(sed 1d <<< "$DID")" ] || { echo "8B3 RESULT: CHECK - identity on built did not reproduce the dry run; binding NOT run. Built's identity before-state: $D/before.db"; exit 1; }
ABD=$(python3 scripts/build_entity_binding.py "$B" --apply 2>&1); ab=$?
printf '%s\n' "$ABD" > "$D/apply_binding.log"
TXS=yes; for f in $TX; do cp "$f" "$D/$(basename "$f" .txt)_apply.txt"; cmp -s "$f" "$D/$(basename "$f" .txt)_dry.txt" || TXS=NO; git show "HEAD:$f" | cmp -s - "$f" && echo "  $f from this run = the repo copy" || echo "  $f from this run differs from the repo copy (kept in $D)"; done; git checkout -- $TX
echo "--- 2 build_entity_binding on built (full output: $D/apply_binding.log):"
grep -E "$P_BIND" <<< "$ABD"
echo "exit $ab (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$ABD")" = "$(sed 1d <<< "$DBD")" ] && echo yes || echo NO) - scripts/ dumps = the dry run's: $TXS"
[ "$ab" -eq 0 ] && [ "$(sed 1d <<< "$ABD")" = "$(sed 1d <<< "$DBD")" ] && [ "$TXS" = "yes" ] || { echo "8B3 RESULT: CHECK - binding on built did not reproduce the dry run. Before-state of the five tables: $D/before.db"; exit 1; }
AU=$(python3 scripts/audit_unfindability.py "$U" "$B" --list 2>&1); au=$?
printf '%s\n' "$AU" > "$D/apply_unf.log"
echo "--- 3 audit_unfindability (re-keyed src copy vs built) after the builders:"
grep -E "$P_UNF" <<< "$AU"
echo "exit $au (expect 0) - output = the dry run's: $([ "$AU" = "$U2" ] && echo yes || echo NO)"
ATW=$(python3 scripts/audit_two_derivations.py "$B" 2>&1); at=$?
printf '%s\n' "$ATW" > "$D/apply_twoder.log"
echo "--- 4 audit_two_derivations on built:"
grep -E '^agree: |^controls: ' <<< "$ATW"
echo "exit $at (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$ATW")" = "$(sed 1d <<< "$DTW")" ] && echo yes || echo NO)"
CHK=$(python3 "$P" check "$B" "$M" "$D" 2>&1); k=$?
echo "$CHK"
cmp -s "$D/greek_header_split_dry.txt" "$D/greek_header_split_apply.txt" && RCS=yes || RCS=NO
if [ -f "$D/greek_header_split_before.txt" ]; then cmp -s "$D/greek_header_split_before.txt" "$D/greek_header_split_apply.txt" && RB=same || RB=differs; else RB="no earlier copy"; fi
echo "header receipt ($RC): this run = the dry run's: $RCS - vs the copy on PA before: $RB (read-out)"
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] && GS=clean || GS=DIRTY
echo "repo scripts/tests after: $GS (expect clean)"
if [ -e "$B-journal" ]; then J=PRESENT; else J=none; fi
echo "journal after: $J (expect none)"
if [ "$au" -eq 0 ] && [ "$AU" = "$U2" ] && [ "$at" -eq 0 ] && [ "$(sed 1d <<< "$ATW")" = "$(sed 1d <<< "$DTW")" ] && [ "$k" -eq 0 ] && [ "$RCS" = "yes" ] && [ "$GS" = "clean" ] && [ "$J" = "none" ]; then
  echo "8B3 RESULT: DONE - identity 32,478 at the ruled split - binding render 15,378 + HOT 68, slot 102 / 0 - unfindability PASS 0/0 (re-keyed), 0/5 as-is = the moved records - two-derivations 10/0 - built = the dry run, 0 row differences vs before - words 626309 + abp_surface unchanged"; exit 0
fi
echo "8B3 RESULT: CHECK - an after-figure differs from the expected picture (lines above). Before-state of the five tables: $D/before.db"; exit 1
) 2>&1 | tee ~/edition_upgrade_runs/pn8b3_20261107.log; echo "exit=${PIPESTATUS[0]}"
```

## 8B3 RAN — STOP at the dry identity build; ACCEPTED as the §9.70 case (11/7, 02:57 UTC) → built untouched, still = 8b.0 + REKEY + 8b.1 + §9.96 restore + 8b.2 + 8b.2a

Log `~/edition_upgrade_runs/pn8b3_20261107.log`, PA HEAD 12b3e689. pre (a) 0 · (b) OK · (c) pre_8b copy 451,964,928 bytes,
built 451,964,928. 10/25 lines found where expected: `live_8b3_id.log:13-17` (split) + `:66` (32,478);
`live_8b3_bind.log:8,10,12,14` (hand rulings / witness lanes), `:59` tipnr_entities 4,247, `:60` render 15,378 + HOT 68,
`:63-69` the 7 Jehoram→Joram OVERRIDE lines, `:70` slot 102 landable / 0 refused, `:71` 102 written;
`live_8b3_unfind.log:5` in scope 26,830, `:6-7` 0 / 0, `:9` PASS; `live_8b3_twoder.log:2` Hebrew-keyed 2,330 /
Greek-keyed 502, `:6` agree 2,330 / disagree 0, `:2352` controls 10 failed 0. Header receipt on PA before: 2,614 lines.
Prep OK: words 626,309, identity 32,478, REKEY 6/6 at the new positions; snapshots identity 32,478 / binding 15,446;
words fingerprint digest 2b23f546; abp_surface 395,003 digest 623cca1f; dry copy words 33,376 (51 slot-ruling verses).
SRCMINI OK (6 records moved; identity 32,478 · xref 32,478 · words keys 626,309).
**Dry identity build (exit 0):** split abp-tag 3,671 · tipnr **10,246** · lemma-only **12,216** · surface **4,382** ·
none **1,963** = 32,478 (10/25: 3,671 / 10,236 / 12,191 / 4,409 / 1,971; net +10 / +25 / −27 / −8); name-match gate
refused 526 across 43 pairs; receipt: names classified 2,602, UNRESOLVED 886. → `8B3 RESULT: STOP`, exit=1. Binding,
audits and the apply never ran.
**Correction to the 8B3 draft:** it said none of the four scripts' inputs changed since 10/24. True of the files in
git; NOT of the words table, which the identity builder reads (labels, lemmas) and which this lane rebuilt from the
edition's text. The 10/25 split was therefore an expectation, not a given — the dry run caught it before built.
**Side effect:** the dry identity build rewrote PA's receipt `docs/tickets/greek_header_split.txt` (generated,
untracked; every identity run rewrites it). The earlier copy is in the run folder as `greek_header_split_before.txt`.
**Ruling (chat, 11/7):** STOP accepted; the §9.70 case — identity rebuilt from the edition's text; re-declare on built
with the changed rows named; not a defect. Read-only 8B3R ordered (below); then a proposal (not written) for the
re-declared split for 8B3b and the gate_b changed_rows list (§9.92 G3).

## 8B3R (read-only: what the dry identity build changed) drafted (11/7)

Reads only the files 8B3 left in `~/edition_upgrade_runs/pn8b3_20261107/` (`before.db` = built's five tables before
8b.3, `dry.db` = the throwaway copy after the dry identity build, `unf_before_rekeyed.db` = src's identity + xref with
the 6 moves applied, `dry_identity.log`, the two receipt copies), `~/rekey/live_8b3_id.log`, and src through one
read-only open (english for the printed rows). Every database is opened read-only; no builder runs. Writes two list
files into the run folder: `identity_delta.tsv` (every differing row) and `receipt_delta.tsv` (every per-name change).
Prints: (0) the before / dry splits recomputed from the tables, dry = the dry log, and before.db vs src re-keyed (0
means this delta is also the src → built picture gate 2 will compare); (1) counts by source before → after, by
greek_strongs changed / unchanged (and how: appears / vanishes / changes), rows gate B counts (greek_strongs /
greek_lemma / source) vs hebrew_base-only, then the first 60 rows in verse_id order with ref, position, english on built,
english on src (src position for a moved record), strongs_base on built, before → after record — plus the first 2 rows
of any source change the 60 don't show; (3) the refusal / pair / names / UNRESOLVED figures, 10/25 vs dry, each with
its log path:line, every GATED pair whose count differs, and the receipt-level per-name changes (the before copy's
figures are checked against the 10/25 log's; the copy itself carries no date); (4) whether any of the 6 re-keyed or
16 abp-tag rows are in the delta.
Tests (fake home, the real 8B3 test block stopped at the split first): 1 changed row (a REKEY record) listed and
flagged; re-paste STOP; 3 changed rows incl. an abp-tag row losing its number (greek_strongs vanishes, abp-tag 1 of 16
flagged, a class beyond the shown rows printed); the log-line patterns checked against PA's own line formats.

### Block 8B3R (GATE REF 12b3e689; READ-ONLY — writes two list files into the run folder)

```bash
set +H
( set -uo pipefail
REF=12b3e689
echo "GATE REF ${REF} - 8B3R read-only: what the 8B3 dry identity build changed (files in pn8b3_20261107/ + one read-only open of src) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "8B3R RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "8B3R RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "8B3R RESULT: STOP - PA has not pulled $REF"; exit 1; }
export PYTHONIOENCODING=utf-8
S=~/bible-db/bible_edupg_test_20261101.db
B=~/bible-db/bible_edupg_test_built_20261102.db
D=~/edition_upgrade_runs/pn8b3_20261107
L1=~/rekey/live_8b3_id.log
RC=docs/tickets/greek_header_split.txt
for f in "$D/before.db" "$D/dry.db" "$D/unf_before_rekeyed.db" "$D/dry_identity.log" "$D/greek_header_split_dry.txt" "$S" "$L1"; do [ -s "$f" ] || { echo "8B3R RESULT: STOP - missing or empty: $f"; exit 1; }; done
[ -e "$D/apply_identity.log" ] && { echo "8B3R RESULT: STOP - $D has an apply log: 8B3 got past the dry run, this read does not fit"; exit 1; }
P="$D/pn8b3r_helper.py"
[ -e "$P" ] && { echo "8B3R RESULT: STOP - helper already in the folder (already ran?): $P"; exit 1; }
for f in "$S" "$B" "$D/before.db" "$D/dry.db" "$D/unf_before_rekeyed.db"; do if [ -e "$f-journal" ]; then echo "8B3R RESULT: STOP - $f-journal present (move it aside, never delete; bring it back)"; exit 1; fi; done
echo "pre: no -journal beside src, built or the folder's three copies: OK"
echo "built now (read-out; 8B3 stopped before writing it): $(stat -c '%s bytes, modified %y' "$B")"
echo "folder: $(ls "$D" | tr '\n' ' ')"
cat > "$P" <<'PY'
"""8B3R helper (one-off, read-only): what the 8B3 dry identity build changed.

Reads only the files 8B3 left in its run folder <dir> (before.db = built's tables before 8b.3,
dry.db = the throwaway copy after the dry identity build, unf_before_rekeyed.db = src's identity
with the 6 REKEY moves applied, dry_identity.log, the two receipt copies), the 10/25 identity
log, and src (one read-only open, english for the printed rows). Every database is opened
read-only. Writes two list files into <dir>: identity_delta.tsv, receipt_delta.tsv.

Usage: python3 pn8b3r_helper.py <dir> <src.db> <live_8b3_id.log>
"""
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path.home() / "bible-db"
sys.path.insert(0, str(REPO))
import entity_resolution as er  # norm_name: the label form gate B compares (gate_greek_header.py)

MOVES = REPO / "tests" / "fixtures" / "edition_upgrade" / "pn_greek_identity_key_moves_20261106.tsv"
ABPTAG16 = ((21270, 1), (23928, 2), (24148, 16), (24461, 2), (24627, 9), (25170, 6), (25225, 0),
            (25374, 19), (25553, 12), (26424, 2), (27237, 1), (28665, 6), (29083, 13), (29141, 13),
            (29142, 0), (31003, 4))
CLASSES = ("abp-tag", "tipnr", "lemma-only", "surface", "none")
SHOW = 60
COLS = ("greek_strongs", "greek_lemma", "source", "hebrew_base")


def stop(msg):
    print("8B3R RESULT: STOP - " + msg)
    sys.exit(1)


def ro(path):
    if not Path(path).is_file():
        stop("missing: %s" % path)
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


def ident(c):
    return {(r[0], r[1]): tuple(r[2:]) for r in c.execute(
        "SELECT verse_id, position, %s FROM pn_greek_identity" % ", ".join(COLS))}


def split_of(rows):
    s = {k: 0 for k in CLASSES}
    for v in rows.values():
        s[v[2]] = s.get(v[2], 0) + 1
    return s


def fmt_split(s):
    return " / ".join("%s %s" % (k, format(s.get(k, 0), ",")) for k in CLASSES) + \
        " = %s" % format(sum(s.values()), ",")


D, SRC, LIVE_LOG = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
OUT1, OUT2 = D / "identity_delta.tsv", D / "receipt_delta.tsv"
if OUT1.exists() or OUT2.exists():
    stop("output list already exists (already ran?): %s" % OUT1)
moves = []
for ln in MOVES.read_text(encoding="utf-8").splitlines()[1:]:
    if ln.strip():
        v, o, n = ln.split("\t")
        moves.append((int(v), int(o), int(n)))
if not len(moves) == 6:
    stop("moves file has %d rows, not 6" % len(moves))
new2old = {(v, n): (v, o) for v, o, n in moves}

bef_c, dry_c, unf_c = ro(D / "before.db"), ro(D / "dry.db"), ro(D / "unf_before_rekeyed.db")
bef, dry, unf = ident(bef_c), ident(dry_c), ident(unf_c)
vref = {r[0]: (r[1], r[2], r[3]) for r in bef_c.execute("SELECT id, book, chapter, verse FROM verses")}


def ref(vid):
    r = vref.get(vid)
    return "%s %d:%d" % r if r else "verse %s ?" % vid


# ---- (0) the inputs are what 8B3 left
print("=== (0) the run folder's tables")
sb, sd = split_of(bef), split_of(dry)
print("before.db identity (built before 8b.3): %s" % fmt_split(sb))
print("dry.db identity (after the dry build):  %s" % fmt_split(sd))
dlog = (D / "dry_identity.log").read_text(encoding="utf-8").splitlines()
logsplit = {}
for ln in dlog:
    m = re.match(r"^  (abp-tag|tipnr|lemma-only|surface|none) +([0-9,]+)$", ln)
    if m:
        logsplit[m.group(1)] = int(m.group(2).replace(",", ""))
print("dry.db split = the split in dry_identity.log: %s" % ("yes" if logsplit == sd else "NO (%s)" % logsplit))
if not logsplit == sd:
    stop("dry.db does not hold the dry run's identity table")
same_src = sum(1 for k in set(bef) | set(unf) if not bef.get(k) == unf.get(k))
print("before.db identity vs src's identity with the 6 REKEY moves applied (unf_before_rekeyed.db): "
      "%d rows differ (0 = built's identity before 8b.3 was src's, re-keyed; then this delta is "
      "also the src -> built picture gate 2 will compare)" % same_src)

# ---- (1) the full delta, before.db -> dry.db
print()
print("=== (1) identity delta, before.db -> dry.db (every row in %s)" % OUT1)
rem = sorted(k for k in bef if k not in dry)
add = sorted(k for k in dry if k not in bef)
chg = sorted(k for k in bef if k in dry and not bef[k] == dry[k])
print("rows: before %s, after %s - changed %d, added %d, removed %d"
      % (format(len(bef), ","), format(len(dry), ","), len(chg), len(add), len(rem)))
wrows = {(r[0], r[1]): r[2:] for r in dry_c.execute(
    "SELECT verse_id, position, english, english_head, strongs_base FROM words WHERE is_pn=1 OR verse_id IN "
    "(SELECT DISTINCT verse_id FROM pn_greek_identity)")}
by_src, by_gs, by_gate, missing_w = {}, {"greek_strongs changed": 0, "greek_strongs unchanged": 0}, {}, 0
gs_kinds = {}
lines = []
keys = [("CHANGED", k) for k in chg] + [("ADDED", k) for k in add] + [("REMOVED", k) for k in rem]
keys.sort(key=lambda t: t[1])
for kind, k in keys:
    b, a = bef.get(k), dry.get(k)
    sb_, sa_ = (b[2] if b else "-"), (a[2] if a else "-")
    by_src[(sb_, sa_)] = by_src.get((sb_, sa_), 0) + 1
    gsb, gsa = (b[0] if b else None), (a[0] if a else None)
    if gsb == gsa:
        by_gs["greek_strongs unchanged"] += 1
    else:
        by_gs["greek_strongs changed"] += 1
        kind_gs = ("appears (None -> G, after source tipnr)" if gsb is None and gsa and sa_ == "tipnr"
                   else "appears (None -> G, other source)" if gsb is None
                   else "vanishes (G -> None)" if gsa is None else "changes (G -> other G)")
        gs_kinds[kind_gs] = gs_kinds.get(kind_gs, 0) + 1
    diffcols = [c for i, c in enumerate(COLS) if not (b and a and b[i] == a[i])]
    gate = "gate-B row" if (b is None or a is None or not b[:3] == a[:3]) else "hebrew_base only"
    by_gate[gate] = by_gate.get(gate, 0) + 1
    w = wrows.get(k)
    if w is None:
        missing_w += 1
    eng, head, sbase = (w if w else (None, None, None))
    label = er.norm_name((head or eng) or "")
    lines.append((kind, k, eng, sbase, label, ",".join(diffcols), b, a))
with open(OUT1, "w", encoding="utf-8", newline="\n") as f:
    f.write("kind\tverse_id\tref\tposition\tenglish_built\tstrongs_base_built\tlabel_norm\tcols_changed\t"
            "before(greek_strongs,greek_lemma,source,hebrew_base)\tafter\n")
    for kind, k, eng, sbase, label, dc, b, a in lines:
        f.write("%s\t%d\t%s\t%d\t%r\t%r\t%r\t%s\t%r\t%r\n" % (kind, k[0], ref(k[0]), k[1], eng, sbase, label, dc, b, a))
print("by source, before -> after:")
for (x, y), n in sorted(by_src.items(), key=lambda t: (-t[1], t[0])):
    print("  %-10s -> %-10s %s" % (x, y, format(n, ",")))
print("net per class (after - before): " + " / ".join(
    "%s %+d" % (c, sd.get(c, 0) - sb.get(c, 0)) for c in CLASSES))
print("by greek_strongs: changed %s, unchanged %s" % (format(by_gs["greek_strongs changed"], ","),
                                                     format(by_gs["greek_strongs unchanged"], ",")))
for kk, n in sorted(gs_kinds.items()):
    print("  greek_strongs %s: %d" % (kk, n))
print("rows gate B counts as changed (greek_strongs / greek_lemma / source differ): %s - hebrew_base only: %s"
      % (format(by_gate.get("gate-B row", 0), ","), format(by_gate.get("hebrew_base only", 0), ",")))
print("delta rows with no words row in the dry copy: %d (expect 0)" % missing_w)
src_c = ro(SRC)


def src_eng(k):
    sk = new2old.get(k, k)
    r = src_c.execute("SELECT english FROM words WHERE verse_id=? AND position=?", sk).fetchone()
    return (r[0] if r else "(no row)"), sk


print()
print("first %d rows (verse_id order): ref @pos | english on built | english on src (src pos if moved) | "
      "strongs_base built | before -> after (greek_strongs, greek_lemma, source, hebrew_base)" % SHOW)
shown_cls = set()
for kind, k, eng, sbase, label, dc, b, a in lines[:SHOW]:
    se, sk = src_eng(k)
    shown_cls.add(((b[2] if b else "-"), (a[2] if a else "-")))
    print("  %s %s @%d | %r | src %r%s | %s | %s -> %s  [%s]"
          % (kind, ref(k[0]), k[1], eng, se, (" (src pos %d)" % sk[1]) if not sk == k else "",
             sbase, b, a, dc))
extra = [(cl, [x for x in lines if ((x[6][2] if x[6] else "-"), (x[7][2] if x[7] else "-")) == cl][:2])
         for cl in sorted(by_src) if cl not in shown_cls]
if extra:
    print("source changes not in the first %d - first 2 rows of each:" % SHOW)
    for cl, xs in extra:
        for kind, k, eng, sbase, label, dc, b, a in xs:
            se, sk = src_eng(k)
            print("  [%s -> %s] %s %s @%d | %r | src %r | %s | %s -> %s  [%s]"
                  % (cl[0], cl[1], kind, ref(k[0]), k[1], eng, se, sbase, b, a, dc))

# ---- (3) receipts and the 10/25 log
print()
print("=== (3) the dry receipt vs the 10/25 run")
llog = Path(LIVE_LOG).read_text(encoding="utf-8").splitlines()


def figures(lines_, name):
    out = {}
    gated = {}
    for i, ln in enumerate(lines_, 1):
        if ln.startswith("name-match gate refused") or ln.startswith("receipt written") \
                or ln.startswith("  (gentilic tokens excluded"):
            print("  %s:%d: %s" % (name, i, ln))
        m = re.match(r"^name-match gate refused ([0-9,]+) slot inheritances across ([0-9,]+) ", ln)
        if m:
            out["refused"], out["pairs"] = (int(x.replace(",", "")) for x in m.groups())
        m = re.search(r"names classified: ([0-9,]+), UNRESOLVED: ([0-9,]+)", ln)
        if m:
            out["names"], out["unresolved"] = (int(x.replace(",", "")) for x in m.groups())
        m = re.match(r"^  GATED (.+) ×([0-9]+)$", ln)
        if m:
            gated[m.group(1)] = int(m.group(2))
    return out, gated


fl, gl = figures(llog, LIVE_LOG)
fd, gd = figures(dlog, str(D / "dry_identity.log"))
for key, lab in (("refused", "name-match gate refusals"), ("pairs", "name->number pairs refused"),
                 ("names", "names classified"), ("unresolved", "UNRESOLVED")):
    a_, b_ = fl.get(key), fd.get(key)
    print("  %-28s 10/25 %s -> dry %s (%s)" % (lab, a_, b_, "same" if a_ == b_ else "%+d" % ((b_ or 0) - (a_ or 0))))
print("  GATED pair lines: 10/25 %d (sum %d) - dry %d (sum %d)" % (len(gl), sum(gl.values()), len(gd), sum(gd.values())))
for p in sorted(set(gl) | set(gd)):
    if not gl.get(p) == gd.get(p):
        print("    GATED %s: 10/25 %s -> dry %s" % (p, gl.get(p, "-"), gd.get(p, "-")))


def receipt(path):
    names, breath = {}, 0
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        if ln.startswith("# ") and " -> " in ln and not ln.startswith("# breathing repairs"):
            breath += 1
        if not ln or ln.startswith("#"):
            continue
        p = ln.split("|")
        names[p[0]] = p[1:]
    return names, breath


rb_path, rd_path = D / "greek_header_split_before.txt", D / "greek_header_split_dry.txt"
if rb_path.exists():
    rb, bb = receipt(rb_path)
    rd, bd = receipt(rd_path)
    unb = sum(1 for v in rb.values() if v[0].startswith("UNRESOLVED"))
    und = sum(1 for v in rd.values() if v[0].startswith("UNRESOLVED"))
    print("  receipt on PA before 8B3 (copy): names %s, UNRESOLVED %s, breathing lines %d - matches the 10/25 "
          "log's figures: %s (figures only; the copy carries no date)"
          % (format(len(rb), ","), format(unb, ","), bb,
             "yes" if (len(rb), unb) == (fl.get("names"), fl.get("unresolved")) else "NO"))
    print("  dry receipt: names %s, UNRESOLVED %s, breathing lines %d (log says %s / %s)"
          % (format(len(rd), ","), format(und, ","), bd, fd.get("names"), fd.get("unresolved")))
    gone = sorted(set(rb) - set(rd))
    new = sorted(set(rd) - set(rb))
    moved = sorted(n for n in set(rb) & set(rd) if not rb[n][0] == rd[n][0] or not rb[n][2] == rd[n][2])
    occ = sorted(n for n in set(rb) & set(rd) if n not in moved and not rb[n][1] == rd[n][1])
    print("  per name, before copy -> dry: only before %d, only dry %d, class or headword changed %d, "
          "occurrence count only %d" % (len(gone), len(new), len(moved), len(occ)))
    trans = {}
    for n in moved:
        t = (rb[n][0], rd[n][0])
        trans[t] = trans.get(t, 0) + 1
    for (x, y), n in sorted(trans.items(), key=lambda t: -t[1]):
        print("    class %s -> %s: %d" % (x, y, n))
    with open(OUT2, "w", encoding="utf-8", newline="\n") as f:
        f.write("kind\tname\tbefore(class|occ|headword|morph|forms)\tdry\n")
        for kind, ns in (("ONLY_BEFORE", gone), ("ONLY_DRY", new), ("CHANGED", moved), ("OCC_ONLY", occ)):
            for n in ns:
                f.write("%s\t%s\t%s\t%s\n" % (kind, n, "|".join(rb.get(n, [])), "|".join(rd.get(n, []))))
    print("  first %d (only before / only dry / class or headword changed; all in %s):" % (SHOW, OUT2))
    for kind, ns in (("ONLY_BEFORE", gone), ("ONLY_DRY", new), ("CHANGED", moved)):
        for n in ns:
            if SHOW <= 0:
                break
            SHOW -= 1
            print("    %s %s: %s -> %s" % (kind, n, "|".join(rb.get(n, [])[:4]) or "-", "|".join(rd.get(n, [])[:4]) or "-"))
else:
    print("  no receipt copy from before 8B3 in the folder - receipt compare by log figures only")

# ---- (4) the 6 re-keyed + 16 abp-tag rows
print()
print("=== (4) the 6 REKEY records and the 16 abp-tag rows in the delta?")
dk = {k for _kind, k, *_r in lines}
for v, o, n in moves:
    print("  REKEY %s @%d: %s" % (ref(v), n, ("IN the delta: %r -> %r" % (bef.get((v, n)), dry.get((v, n))))
                                  if (v, n) in dk else "not in the delta"))
hit16 = [k for k in ABPTAG16 if k in dk]
print("  abp-tag 16: %d of 16 in the delta%s" % (len(hit16), "" if not hit16 else
                                                 " - " + "; ".join("%s @%d %r -> %r" % (ref(k[0]), k[1], bef.get(k), dry.get(k)) for k in hit16)))
print("8B3R RESULT: READ DONE - %d identity rows differ (list: %s)" % (len(lines), OUT1))
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = dcd1f07ac0bbfc12c8d012e34972173a32e8574644092ba5b6b94af4dbcba711 ] || { echo "8B3R RESULT: STOP - the pasted helper does not match the drafted one"; exit 1; }
if [ -f "$RC" ]; then cmp -s "$RC" "$D/greek_header_split_dry.txt" && echo "receipt in PA's repo now ($RC) = the dry run's copy (8B3's dry build rewrote it; the earlier one is $D/greek_header_split_before.txt) - read-out" || echo "receipt in PA's repo now ($RC) differs from the dry run's copy - read-out"; else echo "receipt in PA's repo now: none - read-out"; fi
python3 "$P" "$D" "$S" "$L1"; h=$?
for f in "$S" "$B" "$D/before.db" "$D/dry.db" "$D/unf_before_rekeyed.db"; do [ -e "$f-journal" ] && echo "journal after: PRESENT beside $f"; done
echo "journal after: checked (a PRESENT line above = a problem)"
echo "list files: $(wc -l < "$D/identity_delta.tsv" 2>/dev/null) lines identity_delta.tsv - $(wc -l < "$D/receipt_delta.tsv" 2>/dev/null) lines receipt_delta.tsv (each with a header line)"
[ "$h" -eq 0 ] || { echo "8B3R RESULT: STOP - helper exit $h (line above)"; exit 1; }
exit 0
) 2>&1 | tee ~/edition_upgrade_runs/pn8b3r_20261107.log; echo "exit=${PIPESTATUS[0]}"
```

Reviewer subagent on Block 8B3R (11/7), verdict line verbatim: "REVIEW: CLEAR - read-only block (scope a): every database open is mode=ro + query_only, no builder or gate script runs, the only writes are run artifacts in ~/edition_upgrade_runs (helper, two new TSVs, a new dated log), wrapper and tripwires all pass, and the block carries no ruled figure to trace (it reads out; it asserts nothing beyond what it computes)." Non-blocking notes kept as read-guidance (block bytes unchanged): paste once (tee blanks the log on a re-paste); a `None` figure in (3) means "line not found", not zero; read "delta rows with no words row" (expect 0) before using the TSV; the (0) remark is a hint, the "rows gate B counts" line is the gate-relevant figure.

### Proposal for after 8B3R (CC, not written — for the ruling chat)

**Re-declared split for 8B3b:** abp-tag 3,671 · tipnr 10,246 · lemma-only 12,216 · surface 4,382 · none 1,963 =
32,478, verbatim from `pn8b3_20261107/dry_identity.log` (the only source; not re-derived). 8B3b = Block 8B3 with new
folder/log names (`pn8b3b_*`), EXP_ID = that split, and the dry-run delta rule changed from "0 rows" to:
pn_greek_identity differs from before.db by EXACTLY the rows in 8B3R's `identity_delta.tsv` (its sha256 pinned in the
block, compared row for row), the other four tables still 0. Binding + unfindability expectations unchanged (the binder
and `build_slot_binding` never read pn_greek_identity — grep; unfindability's before side reads src only).
Two-derivations reads identity (hebrew_base, greek_strongs; control G1 David @ Mat 1:6), so its 2,330 / 502 count lines
may move: gate stays `controls: 10  failed: 0`, the count lines printed as read-outs.
**gate_b.changed_rows shape (§9.92 G3, code `scripts/gate_greek_header.py:402-435`):**
`[{"book": "Gen", "chapter": 5, "verse": 25, "position": 1, "name": "<label>"}, ...]` — one entry per
`identity_delta.tsv` row whose greek_strongs / greek_lemma / source differ (the "rows gate B counts" figure); rows that
differ only in hebrew_base are NOT listed (gate B compares those three columns only, :312-314, and a listed row with no
change fails, :428-429). book = built's `verses.book` text; position = built's position (the gate re-keys src through
the moves file first, :345); name = the TSV's `label_norm` (= `er.norm_name` of built's english_head-or-english, the
value the gate checks, :431-435). Generated from the TSV by a script, never typed by hand; count stated next to it.
**Not cleared by changed_rows (each needs its own ruling if 8B3R shows it):** (a) any greek_strongs change except
None → G with after-source tipnr — gate B fails it whatever the list says (:349-356); (b) a changed row whose
transition falls outside gate B's per-row classes (pinned / glued / breathing / → surface / page-attested / gentilic)
fails at :397 even when listed; (c) Sheshach (Jer 51:41 pos 1, Jer 25:26 pos 25) in the delta = a new ruling (§9.92 as
amended); (d) the four pins are NOT taken from 8B3R — per §9.92 they come only from gate 2's first-run output.

## 8B3R RAN — READ DONE (11/7, 17:31 UTC); ruled §9.97 → 8B3b

Log `~/edition_upgrade_runs/pn8b3r_20261107.log`, exit 0, journals clean. before.db split = the 10/25 split; dry.db
split = the dry log's (3,671 / 10,246 / 12,216 / 4,382 / 1,963); before.db vs src re-keyed: 0 rows differ.
**58 identity rows differ**, 0 added / 0 removed, all 58 gate-B rows (hebrew_base-only 0), words row present for all:
surface → lemma-only 33 · lemma-only → surface 6 · none → surface 6 · surface → tipnr 6 · lemma-only → tipnr 3 ·
none → lemma-only 2 · lemma-only → none 1 (Gen 38:1 @18, "an Adullamite,") · none → tipnr 1 (Jos 5:15 @27, G2424);
greek_strongs: 10 appear (None → G, after tipnr), 48 unchanged, none vanish or change. Of the 6 REKEY rows only
Jos 5:15 @27 is in the delta; none of the 16 abp-tag rows. Log figures (`live_8b3_id.log:18/19/64` vs
`dry_identity.log:18/19/64`): refusals 526 / 43 pairs both; gentilic excluded 1,736 → 1,729; names classified
2,610 → 2,602; UNRESOLVED 877 → 886; GATED magiddo→G717 2 → 1, megiddo→G717 9 → 10. The receipt copy from before
8B3 matches the 10/25 figures (2,610 / 877). Per name: only-before 32, only-dry 24, class/headword changed 8 (all
indeclinable → UNRESOLVED-no-nominative), occurrence-only 62. Lists: `pn8b3_20261107/identity_delta.tsv` (59 lines),
`receipt_delta.tsv` (127 lines). Ruling: §9.97 (DESIGN).

## 8B3b drafted (11/7) — held for the ruling chat; the list-file pin comes from PA first

8B3b = the cleared 8B3 block with only the §9.97 changes (generator: the 8B3 generator + string replacements, each
asserted to hit exactly once; helper = the 8B3 helper + one function): (1) folder/log `pn8b3b_20261107`; (2) the
10/25 identity log is still checked against its own split (EXP_OLD), the dry identity build against the §9.97 split
(EXP_ID); (3) the dry delta: pn_greek_identity must equal `identity_delta.tsv` exactly — same keys, same before and
after (greek_strongs, greek_lemma, source, hebrew_base) — any row not declared, declared-but-absent or with other
values is listed and STOPs; the other four tables 0; the same rule in the after-check (built vs before); built vs the
dry copy stays 0; (4) two-derivations: controls 10 / 0 required (unchanged), the Hebrew-keyed / agree lines compared
with the 10/25 log as a read-out ("same" / "differ"); (5) everything else byte-for-byte 8B3. The list file is checked
against a pinned sha256 + 59 lines before anything runs, then copied into the new folder (`identity_delta_declared.tsv`)
and re-checked. **The pin is not known locally** (the file is only on PA; the pasted 8B3R output lacks two of its
columns and has one garbled Greek cell), so read-only line PIN8B3B read it (below); the block carries that pin in its two
pin slots (filled 11/7 after PIN8B3B; before that the slots held `000…0`, which would only STOP at the pin check).
Tests (fake home, real scripts; the chain 8B3 STOP → 8B3R list → 8B3b): clean 2-row case DONE (dry = declared,
built = dry, built vs before = declared, abp-tag 16/16, repo clean); a declared row that breaks an abp-tag row →
applied, then CHECK at abp-tag 15/16 (the after-check catches it); re-paste STOP; list file altered → STOP at the pin;
rows already applied (declared rows absent) → STOP at the dry delta, built untouched (file time same); a row with other
values and a row not on the list → each listed, STOP.

### Block 8B3b (GATE REF 12b3e689; WRITES built: pn_greek_identity, pn_binding, tipnr_entities, tipnr_entity_refs, pn_slot_binding) — pinned 11/7 from PIN8B3B

```bash
set +H
( set -uo pipefail
REF=12b3e689
echo "GATE REF ${REF} - 8B3b (DESIGN 9.97) the four 8b.3 scripts (build_pn_greek_identity, build_entity_binding, audit_unfindability, audit_two_derivations) on the built copy - dry run on a throwaway copy, identity = the 58 declared rows, apply only on the expected picture - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "8B3b RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "8B3b RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "8B3b RESULT: STOP - PA has not pulled $REF"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
R=~/bible-db/bible_edupg_test_built_pre_8b_20261106.db
O=~/edition_upgrade_runs
D="$O/pn8b3b_20261107"
DL0="$O/pn8b3_20261107/identity_delta.tsv"
DL="$D/identity_delta_declared.tsv"
M="$D/dry.db"
U="$D/unf_before_rekeyed.db"
L1=~/rekey/live_8b3_id.log; L2=~/rekey/live_8b3_bind.log; L3=~/rekey/live_8b3_unfind.log; L4=~/rekey/live_8b3_twoder.log
RC=docs/tickets/greek_header_split.txt
TX="scripts/pn_binding_hot.txt scripts/pn_binding_numonly.txt"
[ -f "$B" ] || { echo "8B3b RESULT: STOP - missing: $B"; exit 1; }
[ -f "$S" ] || { echo "8B3b RESULT: STOP - missing: $S"; exit 1; }
for f in "$L1" "$L2" "$L3" "$L4"; do [ -s "$f" ] || { echo "8B3b RESULT: STOP - last 8b.3 run log missing or empty: $f"; exit 1; }; done
[ -s "$DL0" ] || { echo "8B3b RESULT: STOP - declared list (8B3R) missing or empty: $DL0"; exit 1; }
echo "declared list: $DL0 - $(wc -l < "$DL0") lines (expect 59 = header + 58) - sha256 $(sha256sum < "$DL0" | cut -c1-16)..."
[ "$(sha256sum < "$DL0" | cut -d' ' -f1)" = 62a99ffe59658f46b9e8a5e385d643b7a147870f38f83136b541d52c5950acca ] && [ "$(wc -l < "$DL0")" = "59" ] || { echo "8B3b RESULT: STOP - the declared list is not the pinned 8B3R file (9.97)"; exit 1; }
if [ -e "$D" ]; then echo "8B3b RESULT: STOP - output folder already exists (already ran?): $D"; exit 1; fi
t=$(sqlite3 -readonly "$B" "SELECT count(*) FROM sqlite_master WHERE type='trigger'") || { echo "8B3b RESULT: STOP - trigger read failed"; exit 1; }
echo "pre (a) triggers on built: $t (expect 0)"
[ "$t" = "0" ] || { echo "8B3b RESULT: STOP - built has triggers"; exit 1; }
for f in "$B" "$S"; do if [ -e "$f-journal" ]; then echo "8B3b RESULT: STOP - $f-journal present (move it aside, never delete; bring it back)"; exit 1; fi; done
echo "pre (b) no -journal beside built or src: OK"
[ -s "$R" ] || { echo "8B3b RESULT: STOP - pre_8b rollback copy missing or empty: $R"; exit 1; }
echo "pre (c) pre_8b copy present: $(stat -c '%s bytes, %y' "$R") - built now $(stat -c '%s bytes' "$B") (size only)"
EXP_OLD=$(printf '%s\n' "  abp-tag    3,671" "  tipnr      10,236" "  lemma-only 12,191" "  surface    4,409" "  none       1,971" "Wrote pn_greek_identity: 32,478 rows.")
P_ID='^  (abp-tag|tipnr|lemma-only|surface|none) +[0-9,]+$|^Wrote pn_greek_identity: '
P_BIND='^  pn_binding      : |^  tipnr_entities  : |^slot rulings: |^pn_slot_binding written: |^Hand rulings: |^Witness |REFUSED|FAILED|OVERRIDE'
P_UNF='^findable-(before|after) +check failures: |^UNFINDABILITY GATE: '
echo "--- last 8b.3 run (10/25), the lines this run must reproduce, with their line numbers:"
echo "$L1:"; grep -nE "$P_ID" "$L1"
EXP_ID=$(printf '%s\n' "  abp-tag    3,671" "  tipnr      10,246" "  lemma-only 12,216" "  surface    4,382" "  none       1,963" "Wrote pn_greek_identity: 32,478 rows.")
[ "$(grep -E "$P_ID" "$L1")" = "$EXP_OLD" ] || { echo "8B3b RESULT: STOP - the 10/25 identity log does not show the ruled split 3,671 / 10,236 / 12,191 / 4,409 / 1,971 and 32,478 rows"; exit 1; }
echo "$L2:"; grep -nE "$P_BIND" "$L2"
LBIND=$(grep -E "$P_BIND" "$L2")
grep -qxF "  pn_binding      : render 15,378 + HOT 68" <<< "$LBIND" && grep -qE '^slot rulings: 102 landable, 0 refused of ' <<< "$LBIND" && grep -qxF "pn_slot_binding written: 102 rows." <<< "$LBIND" || { echo "8B3b RESULT: STOP - the 10/25 binding log does not show render 15,378 + HOT 68 and 102 slot binds / 0 refused"; exit 1; }
[ "$(grep -cE 'REFUSED|FAILED' <<< "$LBIND")" = "0" ] || { echo "8B3b RESULT: STOP - the 10/25 binding log shows a refusal or failure"; exit 1; }
echo "$L3:"; grep -nE "$P_UNF|^rows in scope" "$L3"
LUNF=$(grep -E "$P_UNF" "$L3")
[ "$LUNF" = "$(printf '%s\n' "findable-before check failures: 0 (expected 0)" "findable-after  check failures: 0 (expected 0)" "UNFINDABILITY GATE: PASS — zero findable-before/unfindable-after.")" ] || { echo "8B3b RESULT: STOP - the 10/25 unfindability log is not PASS 0 / 0"; exit 1; }
echo "$L4:"; grep -nE '^Hebrew-keyed PN numbers: |^agree: |^controls: ' "$L4"
LTWO=$(grep -E '^controls: ' "$L4")
LTWC=$(grep -E '^Hebrew-keyed PN numbers: |^agree: ' "$L4")
[ "$LTWO" = "controls: 10  failed: 0" ] || { echo "8B3b RESULT: STOP - the 10/25 two-derivations log is not controls 10 failed 0"; exit 1; }
mkdir -p "$D"
cp "$DL0" "$DL"; [ "$(sha256sum < "$DL" | cut -d' ' -f1)" = 62a99ffe59658f46b9e8a5e385d643b7a147870f38f83136b541d52c5950acca ] || { echo "8B3b RESULT: STOP - declared list copy differs"; exit 1; }
P="$D/pn8b3_helper.py"
cat > "$P" <<'PY'
"""8B3b helper (one-off, edition upgrade stage D, step 8b.3; = the 8B3 helper + the declared identity
list, DESIGN 9.97). Never writes the built copy or src.

  prep    <built.db> <dry.db> <dir>   read built; save its before-state (the five tables the two
                                      builders replace -> <dir>/before.db + two snapshot files;
                                      words per-row fingerprints; abp_surface count + digest);
                                      write a THROWAWAY copy (<dry.db>) holding just what the four
                                      8b.3 scripts read, for the dry run
  srcmini <src.db> <out.db>           a THROWAWAY copy of src's identity + xref (+ words keys) with
                                      the committed REKEY moves applied, as the unfindability
                                      audit's before side (its matching is by position)
  unf1    <audit.log> <src.db>        the as-is audit (src vs built): findable-after failures must
                                      be exactly the in-scope records at the old REKEY positions
  delta   <a.db> <b.db> <label> <declared.tsv>
                                      row-level differences in the five tables, a -> b; the
                                      identity rows must be exactly the declared list (key +
                                      before/after), the other four tables 0
  check   <built.db> <dry.db> <dir> <declared.tsv>
                                      after the apply: words + abp_surface unchanged, built = dry
                                      copy on the five tables, delta vs before, the 6 re-keyed
                                      records and the 16 abp-tag rows

Usage: python3 pn8b3b_helper.py <mode> ...
"""
import ast
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path.home() / "bible-db"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
MOVES = REPO / "tests" / "fixtures" / "edition_upgrade" / "pn_greek_identity_key_moves_20261106.tsv"
WORDS_EXPECT = 626309
IDENTITY_EXPECT = 32478
UNF1_EXPECT = 5
SCOPE = ("tipnr", "lemma-only", "surface")
# the five tables build_pn_greek_identity / build_entity_binding (+ build_slot_binding.land) replace
OUT = (("pn_greek_identity", ("verse_id", "position")),
       ("pn_binding", ("book", "chapter", "verse", "name")),
       ("tipnr_entities", ("uniq",)),
       ("tipnr_entity_refs", None),
       ("pn_slot_binding", ("book", "chapter", "verse", "position")))
# everything the four scripts read (main() of each, top to bottom)
READS = ("verses", "words", "abp_surface", "pn_binding", "pn_hebrew_xref", "pn_greek_identity",
         "tipnr_entities", "tipnr_entity_refs", "pn_slot_binding", "metav_places",
         "metav_place_aliases", "metav_people", "metav_people_aliases")
ABPTAG16 = ((21270, 1), (23928, 2), (24148, 16), (24461, 2), (24627, 9), (25170, 6), (25225, 0),
            (25374, 19), (25553, 12), (26424, 2), (27237, 1), (28665, 6), (29083, 13), (29141, 13),
            (29142, 0), (31003, 4))


def stop(msg):
    print("8B3b RESULT: STOP - " + msg)
    sys.exit(1)


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


def tables(c):
    return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def cols(c, t):
    return [r[1] for r in c.execute("PRAGMA table_info(%s)" % t)]


def moves():
    out = []
    for ln in MOVES.read_text(encoding="utf-8").splitlines()[1:]:
        if ln.strip():
            v, o, n = ln.split("\t")
            out.append((int(v), int(o), int(n)))
    if not len(out) == 6:
        stop("moves file has %d rows, not 6" % len(out))
    return out


def ref(c, vid):
    r = c.execute("SELECT book, chapter, verse FROM verses WHERE id=?", (vid,)).fetchone()
    return "%s %d:%d" % r if r else "verse %s ?" % vid


def words_fingerprints(c, path):
    h = hashlib.sha256()
    n = 0
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in c.execute("SELECT rowid, * FROM words ORDER BY rowid"):
            line = "%s\t%s\n" % (r[0], hashlib.sha1(repr(tuple(r)).encode("utf-8")).hexdigest())
            f.write(line)
            h.update(line.encode("utf-8"))
            n += 1
    return n, h.hexdigest()


def surface_digest(c):
    rows = sorted(repr(tuple(r)) for r in c.execute("SELECT * FROM abp_surface"))
    h = hashlib.sha256()
    for s in rows:
        h.update(s.encode("utf-8"))
        h.update(b"\n")
    return len(rows), h.hexdigest()


def keyed(c, t, key):
    cs = cols(c, t)
    d = {}
    for r in c.execute("SELECT * FROM %s" % t):
        k = tuple(r[cs.index(x)] for x in key) if key else tuple(r)
        d.setdefault(k, []).append(tuple(r))
    for k in d:
        d[k].sort(key=repr)
    return cs, d


IDCOLS = ("greek_strongs", "greek_lemma", "source", "hebrew_base")


def declared(path):
    """The declared identity rows (8B3R's identity_delta.tsv): {(verse_id, position): (before, after)}."""
    out = {}
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines[0].startswith("kind\tverse_id\tref\tposition\t"):
        stop("declared list header is not 8B3R's: %s" % path)
    for ln in lines[1:]:
        f = ln.split("\t")
        k = (int(f[1]), int(f[3]))
        if k in out:
            stop("declared list has key %s twice" % (k,))
        out[k] = (ast.literal_eval(f[-2]), ast.literal_eval(f[-1]))
    return out


def delta(a, b, refc, expect=None):
    """Print row-level differences a -> b on the five tables. Returns the total of differences
    NOT allowed: with expect, the identity rows must equal it exactly (key + before/after)."""
    total = 0
    for t, key in OUT:
        ca, da = keyed(a, t, key)
        cb, db = keyed(b, t, key)
        if not ca == cb:
            print("  %s: columns differ %s -> %s" % (t, ca, cb))
            total += 1
            continue
        rem = sorted((k for k in da if k not in db), key=repr)
        add = sorted((k for k in db if k not in da), key=repr)
        chg = sorted((k for k in da if k in db and not da[k] == db[k]), key=repr)
        n = len(rem) + len(add) + len(chg)
        print("  %s: rows %d -> %d - changed %d, added %d, removed %d"
              % (t, sum(len(x) for x in da.values()), sum(len(x) for x in db.values()), len(chg), len(add), len(rem)))
        if t == "pn_greek_identity" and expect is not None:
            ix = [ca.index(x) for x in IDCOLS]
            def rec(rows):
                return tuple(rows[0][i] for i in ix) if rows else None
            got = {k: (rec(da.get(k)), rec(db.get(k))) for k in set(rem) | set(add) | set(chg)}
            extra = sorted(k for k in got if k not in expect)
            absent = sorted(k for k in expect if k not in got)
            wrong = sorted(k for k in got if k in expect and not got[k] == expect[k])
            bad = len(extra) + len(absent) + len(wrong)
            total += bad
            trans = {}
            for k in got:
                tr = "%s -> %s" % ((got[k][0] or ("-",) * 4)[2], (got[k][1] or ("-",) * 4)[2])
                trans[tr] = trans.get(tr, 0) + 1
            print("    by source: " + " - ".join("%s %d" % kv for kv in sorted(trans.items(), key=lambda x: (-x[1], x[0]))))
            print("    = the declared list (%d rows, key + before/after values): %s - not declared %d, declared but "
                  "absent %d, values differ %d" % (len(expect), "yes" if not bad else "NO", len(extra), len(absent), len(wrong)))
            shown = 0
            for kind, ks in (("NOT DECLARED", extra), ("DECLARED, ABSENT", absent), ("VALUES DIFFER", wrong)):
                for k in ks:
                    if shown == 40:
                        break
                    shown += 1
                    print("    %s %s  [%s]: got %s - declared %s" % (kind, k, ref(refc, k[0]), got.get(k), expect.get(k)))
            continue
        total += n
        if not n:
            continue
        si = ca.index("source") if t == "pn_greek_identity" else None
        ri = ca.index("render") if t == "pn_binding" else None
        def cls(rows):
            if si is not None:
                return rows[0][si]
            if ri is not None:
                return "render=%s" % rows[0][ri]
            return t
        classes = {}
        for k in chg:
            c_ = "changed %s -> %s" % (cls(da[k]), cls(db[k]))
            classes[c_] = classes.get(c_, 0) + 1
        for k in add:
            c_ = "added %s" % cls(db[k])
            classes[c_] = classes.get(c_, 0) + 1
        for k in rem:
            c_ = "removed %s" % cls(da[k])
            classes[c_] = classes.get(c_, 0) + 1
        if n > 40:
            print("    by class: " + " - ".join("%s %d" % kv for kv in sorted(classes.items())))
            print("    first 40:")
        shown = 0
        for kind, ks, src in (("CHANGED", chg, None), ("ADDED", add, db), ("REMOVED", rem, da)):
            for k in ks:
                if shown == 40:
                    break
                shown += 1
                where = ("  [%s]" % ref(refc, k[0])) if t == "pn_greek_identity" else ""
                if kind == "CHANGED":
                    print("    CHANGED %s%s: %s -> %s" % (k, where, da[k], db[k]))
                else:
                    print("    %s %s%s: %s" % (kind, k, where, src[k]))
    return total


MODE = sys.argv[1]

if MODE == "prep":
    B, DRY, DIR = sys.argv[2], sys.argv[3], Path(sys.argv[4])
    c = ro(B)
    have = tables(c)
    miss = [t for t in READS if t not in have]
    if miss:
        stop("built has no table(s) %s" % miss)
    nw = c.execute("SELECT count(*) FROM words").fetchone()[0]
    ni = c.execute("SELECT count(*) FROM pn_greek_identity").fetchone()[0]
    print("words on built before: %d (expect %d) - identity rows %d (expect %d)" % (nw, WORDS_EXPECT, ni, IDENTITY_EXPECT))
    if not (nw == WORDS_EXPECT and ni == IDENTITY_EXPECT):
        stop("words or identity count before")
    for v, o, n in moves():
        at_new = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, n)).fetchone()[0]
        at_old = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()[0]
        if not (at_new == 1 and at_old == 0):
            stop("REKEY record %s %d->%d: %d at new, %d at old on built" % (ref(c, v), o, n, at_new, at_old))
    print("REKEY records on built: 6/6 at their new positions, none at the old")
    if Path(DRY).exists() or (DIR / "before.db").exists():
        stop("dry copy or before.db already exists")
    # before-state of the five tables the builders replace
    bconn = sqlite3.connect(str(DIR / "before.db"), uri=True)
    bconn.execute("PRAGMA journal_mode=DELETE")
    bconn.execute("ATTACH DATABASE ? AS b", ("file:%s?mode=ro" % B,))
    for t, _k in OUT:
        bconn.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
        bconn.execute("INSERT INTO main.%s SELECT * FROM b.%s" % (t, t))
    bconn.execute("CREATE TABLE verses AS SELECT id, book, chapter, verse FROM b.verses")
    bconn.commit()
    bconn.execute("DETACH DATABASE b")
    bconn.close()
    for t, order, f in (("pn_greek_identity", "verse_id, position", "identity_before.tsv"),
                        ("pn_binding", "book, chapter, verse, name, entity_uniq", "binding_before.tsv")):
        cs = cols(c, t)
        with open(DIR / f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(cs) + "\n")
            n = 0
            for r in c.execute("SELECT * FROM %s ORDER BY %s" % (t, order)):
                fh.write("\t".join(repr(x) for x in r) + "\n")
                n += 1
        print("snapshot %s before: %d rows -> %s" % (t, n, DIR / f))
    nwf, wdig = words_fingerprints(c, DIR / "words_before.tsv")
    ns, sdig = surface_digest(c)
    print("words fingerprints before: %d rows, digest %s - abp_surface before: %d rows, digest %s" % (nwf, wdig[:8], ns, sdig[:8]))
    # the throwaway copy: what the four scripts read
    from build_slot_binding import read_tsv
    slot_v = set()
    for r in read_tsv():
        x = c.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                      (r["book"], int(r["chapter"]), int(r["verse"]))).fetchone()
        if x:
            slot_v.add(x[0])
    d = sqlite3.connect(DRY, uri=True)
    d.execute("PRAGMA journal_mode=DELETE")
    d.execute("ATTACH DATABASE ? AS b", ("file:%s?mode=ro" % B,))
    for t in READS:
        d.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
    d.execute("CREATE TEMP TABLE sv (id INTEGER PRIMARY KEY)")
    d.executemany("INSERT INTO sv VALUES (?)", [(v,) for v in sorted(slot_v)])
    for t in READS:
        if t == "words":
            d.execute("INSERT INTO main.words SELECT * FROM b.words WHERE is_pn=1 OR verse_id IN (SELECT id FROM sv)")
        elif t == "abp_surface":
            d.execute("INSERT INTO main.abp_surface SELECT * FROM b.abp_surface s WHERE EXISTS "
                      "(SELECT 1 FROM main.words w WHERE w.verse_id=s.verse_id AND w.position=s.position)")
        else:
            d.execute("INSERT INTO main.%s SELECT * FROM b.%s" % (t, t))
    for (sql,) in c.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND tbl_name IN (%s)"
                            % ",".join("?" * len(READS)), READS):
        d.execute(sql)
    d.commit()
    counts = {t: d.execute("SELECT count(*) FROM main.%s" % t).fetchone()[0] for t in READS}
    d.execute("DETACH DATABASE b")
    d.close()
    print("dry copy: " + " - ".join("%s %d" % (t, counts[t]) for t in READS))
    print("  (words = the proper-noun rows + every row of the %d verses pn_slot_rulings.tsv names)" % len(slot_v))
    json.dump({"words_rows": nwf, "words_digest": wdig, "surface_rows": ns, "surface_digest": sdig},
              open(DIR / "state.json", "w", encoding="utf-8"))
    print("8B3b PREP: OK")

elif MODE == "srcmini":
    S, OUTDB = sys.argv[2], sys.argv[3]
    c = ro(S)
    if Path(OUTDB).exists():
        stop("exists: %s" % OUTDB)
    d = sqlite3.connect(OUTDB, uri=True)
    d.execute("PRAGMA journal_mode=DELETE")
    d.execute("ATTACH DATABASE ? AS s", ("file:%s?mode=ro" % S,))
    for t in ("pn_greek_identity", "pn_hebrew_xref"):
        d.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
        d.execute("INSERT INTO main.%s SELECT * FROM s.%s" % (t, t))
    d.execute("CREATE TABLE words (verse_id INTEGER, position INTEGER, strongs_base TEXT)")
    d.execute("INSERT INTO main.words SELECT verse_id, position, strongs_base FROM s.words")
    for v, o, n in moves():
        for t in ("pn_greek_identity", "pn_hebrew_xref"):
            a = d.execute("SELECT count(*) FROM main.%s WHERE verse_id=? AND position=?" % t, (v, o)).fetchone()[0]
            b = d.execute("SELECT count(*) FROM main.%s WHERE verse_id=? AND position=?" % t, (v, n)).fetchone()[0]
            if not (a == 1 and b == 0):
                stop("src %s %s %d->%d: %d at old, %d at new" % (t, ref(c, v), o, n, a, b))
            d.execute("UPDATE main.%s SET position=? WHERE verse_id=? AND position=?" % t, (n, v, o))
        print("  src record %s (verse_id %d) pos %d -> %d: identity + xref moved" % (ref(c, v), v, o, n))
    d.commit()
    ni = d.execute("SELECT count(*) FROM main.pn_greek_identity").fetchone()[0]
    nx = d.execute("SELECT count(*) FROM main.pn_hebrew_xref").fetchone()[0]
    nw = d.execute("SELECT count(*) FROM main.words").fetchone()[0]
    d.execute("DETACH DATABASE s")
    d.close()
    print("re-keyed src copy: identity %d - xref %d - words keys %d -> %s" % (ni, nx, nw, OUTDB))
    print("8B3b SRCMINI: OK")

elif MODE == "unf1":
    LOG, S = sys.argv[2], sys.argv[3]
    c = ro(S)
    exp = set()
    for v, o, n in moves():
        r = c.execute("SELECT source FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()
        print("  src record %s (verse_id %d) at old pos %d: class %s%s"
              % (ref(c, v), v, o, r[0] if r else None, " (in the audit's scope)" if r and r[0] in SCOPE else " (out of scope)"))
        if r and r[0] in SCOPE:
            exp.add((v, o))
    text = Path(LOG).read_text(encoding="utf-8").splitlines()
    got = set()
    nb = na = None
    for ln in text:
        if ln.startswith("findable-before check failures: "):
            nb = ln.split(": ")[1].split()[0]
        if ln.startswith("findable-after  check failures: "):
            na = ln.split(": ")[1].split()[0]
        if ln.startswith("  AFTER ("):
            k = ln[len("  AFTER ("):].split(")")[0].split(",")
            got.add((int(k[0]), int(k[1])))
    print("as-is audit: before failures %s (expect 0) - after failures %s (expect %d) - failing keys = old REKEY keys in scope: %s"
          % (nb, na, UNF1_EXPECT, "yes" if got == exp else "NO (got %s, expect %s)" % (sorted(got), sorted(exp))))
    if not (nb == "0" and na == str(UNF1_EXPECT) and len(exp) == UNF1_EXPECT and got == exp):
        stop("the as-is unfindability audit is not exactly the moved-position picture")
    print("8B3b UNF1: OK")

elif MODE == "delta":
    A, Bp, label, EXP = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
    a, b = ro(A), ro(Bp)
    print("delta, %s:" % label)
    n = delta(a, b, a, declared(EXP))
    print("  differences outside the declared identity rows: %d (expect 0)" % n)
    sys.exit(0 if n == 0 else 1)

elif MODE == "check":
    B, DRY, DIR, EXP = sys.argv[2], sys.argv[3], Path(sys.argv[4]), sys.argv[5]
    st = json.load(open(DIR / "state.json", encoding="utf-8"))
    c, d, bef = ro(B), ro(DRY), ro(str(DIR / "before.db"))
    bad = []
    nw = c.execute("SELECT count(*) FROM words").fetchone()[0]
    nwf, wdig = words_fingerprints(c, DIR / "words_after.tsv")
    a_lines = (DIR / "words_after.tsv").read_text(encoding="utf-8").splitlines()
    b_lines = (DIR / "words_before.tsv").read_text(encoding="utf-8").splitlines()
    wdiff = sum(1 for x, y in zip(b_lines, a_lines) if not x == y) + abs(len(a_lines) - len(b_lines))
    print("words on built after: %d (expect %d) - per-row fingerprint lines differing from before: %d (expect 0) - digest %s (before %s)"
          % (nw, WORDS_EXPECT, wdiff, wdig[:8], st["words_digest"][:8]))
    if not (nw == WORDS_EXPECT and wdiff == 0 and wdig == st["words_digest"]):
        bad.append("words changed")
    ns, sdig = surface_digest(c)
    print("abp_surface after: %d rows, digest %s (expect %d, %s - unchanged)" % (ns, sdig[:8], st["surface_rows"], st["surface_digest"][:8]))
    if not (ns == st["surface_rows"] and sdig == st["surface_digest"]):
        bad.append("abp_surface changed")
    print("built after vs the dry copy (must be identical):")
    if delta(d, c, c):
        bad.append("built differs from the dry run")
    print("built after vs built before (the snapshot; identity = the declared list, the rest 0):")
    if delta(bef, c, c, declared(EXP)):
        bad.append("a table differs from its before-snapshot")
    print("the 6 REKEY records on built after (verse_id, position, greek_strongs, greek_lemma, source, hebrew_base | xref | words english, strongs, strongs_base, is_pn):")
    for v, o, n in moves():
        g = c.execute("SELECT * FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, n)).fetchone()
        x = c.execute("SELECT hebrew_base, class FROM pn_hebrew_xref WHERE verse_id=? AND position=?", (v, n)).fetchone()
        w = c.execute("SELECT english, strongs, strongs_base, is_pn FROM words WHERE verse_id=? AND position=?", (v, n)).fetchone()
        old = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()[0]
        print("  %s new pos %d: %s | xref %s | words %s | identity rows at old pos %d: %d" % (ref(c, v), n, g, x, w, o, old))
        if g is None or old:
            bad.append("REKEY record %s" % ref(c, v))
    print("the 16 abp-tag rows (9.96) on built after (identity | words strongs, strongs_base) - retire's abp-tag check:")
    ok16 = 0
    for v, p in ABPTAG16:
        g = c.execute("SELECT greek_strongs, greek_lemma, source, hebrew_base FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, p)).fetchone()
        w = c.execute("SELECT english, strongs, strongs_base FROM words WHERE verse_id=? AND position=?", (v, p)).fetchone()
        good = bool(g and w and g[2] == "abp-tag" and w[2] == g[0] and (w[2] or "").startswith("G") and g[3] is None)
        ok16 += good
        print("  %s (verse_id %d) pos %d: %s | %s | %s" % (ref(c, v), v, p, g, w, "OK" if good else "FAIL"))
    print("abp-tag check on the 16: %d/16 OK" % ok16)
    if not ok16 == 16:
        bad.append("abp-tag rows")
    if bad:
        for b_ in bad:
            print("  problem: " + b_)
        print("8B3b CHECK: FAIL")
        sys.exit(1)
    print("8B3b CHECK: OK")
else:
    stop("unknown mode")
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = 07ec0ac5836bcc170e953a515fb093b4bef676f735644d80ae4036d822fe9442 ] || { echo "8B3b RESULT: STOP - the pasted helper does not match the drafted one"; exit 1; }
if [ -f "$RC" ]; then cp "$RC" "$D/greek_header_split_before.txt"; echo "header receipt on PA before: $(wc -l < "$RC") lines (kept as $D/greek_header_split_before.txt)"; else echo "header receipt on PA before: none"; fi
python3 "$P" prep "$B" "$M" "$D" || { echo "8B3b RESULT: STOP - prep did not pass (line above); built untouched"; exit 1; }
python3 "$P" srcmini "$S" "$U" || { echo "8B3b RESULT: STOP - re-keyed src copy did not pass (line above); built untouched"; exit 1; }
echo "=== DRY RUN on the throwaway copy (built untouched) ==="
DID=$(python3 scripts/build_pn_greek_identity.py "$M" --apply 2>&1); di=$?
printf '%s\n' "$DID" > "$D/dry_identity.log"; cp "$RC" "$D/greek_header_split_dry.txt"
echo "--- 1 build_pn_greek_identity (full output: $D/dry_identity.log):"
grep -E "$P_ID|^identity split|^name-match gate|^pn_binding render rows|^proper-noun words|^pn_hebrew_xref loaded|^hand-table|^receipt written" <<< "$DID"
echo "exit $di (expect 0)"
[ "$di" -eq 0 ] && [ "$(grep -E "$P_ID" <<< "$DID")" = "$EXP_ID" ] || { echo "8B3b RESULT: STOP - dry identity build is not the 9.97 split 3,671 / 10,246 / 12,216 / 4,382 / 1,963 and 32,478; built untouched"; exit 1; }
DBD=$(python3 scripts/build_entity_binding.py "$M" --apply 2>&1); db=$?
printf '%s\n' "$DBD" > "$D/dry_binding.log"
for f in $TX; do cp "$f" "$D/$(basename "$f" .txt)_dry.txt"; done; git checkout -- $TX
echo "--- 2 build_entity_binding (full output: $D/dry_binding.log; its two scripts/ dumps kept in $D and put back in the repo):"
grep -E "$P_BIND" <<< "$DBD"
echo "exit $db (expect 0)"
[ "$db" -eq 0 ] && [ "$(grep -E "$P_BIND" <<< "$DBD")" = "$LBIND" ] || { echo "8B3b RESULT: STOP - dry binding lines differ from the 10/25 run; built untouched"; exit 1; }
DTW=$(python3 scripts/audit_two_derivations.py "$M" 2>&1); dt=$?
printf '%s\n' "$DTW" > "$D/dry_twoder.log"
echo "--- 4 audit_two_derivations on the dry copy (full output: $D/dry_twoder.log):"
grep -E '^Hebrew-keyed PN numbers: |^agree: |^\[(PASS|FAIL)\] |^controls: ' <<< "$DTW"
echo "exit $dt (expect 0) - count lines (Hebrew-keyed / agree) vs 10/25: $([ "$(grep -E '^Hebrew-keyed PN numbers: |^agree: ' <<< "$DTW")" = "$LTWC" ] && echo same || echo differ) (read-out, 9.97)"
[ "$dt" -eq 0 ] && [ "$(grep -E '^controls: ' <<< "$DTW")" = "$LTWO" ] || { echo "8B3b RESULT: STOP - dry two-derivations is not controls 10 failed 0; built untouched"; exit 1; }
U1=$(python3 scripts/audit_unfindability.py "$S" "$B" --list 2>&1); u1=$?
printf '%s\n' "$U1" > "$D/unf_asis.log"
echo "--- 3a audit_unfindability as-is, src vs built (position-keyed; full output: $D/unf_asis.log):"
grep -E "$P_UNF|^rows in scope|^  (BEFORE|AFTER) " <<< "$U1"
echo "exit $u1 (expect 1: fails on the moved records only)"
[ "$u1" -eq 1 ] && python3 "$P" unf1 "$D/unf_asis.log" "$S" || { echo "8B3b RESULT: STOP - as-is unfindability is not the moved-position picture; built untouched"; exit 1; }
U2=$(python3 scripts/audit_unfindability.py "$U" "$B" --list 2>&1); u2=$?
printf '%s\n' "$U2" > "$D/unf_rekeyed.log"
echo "--- 3b audit_unfindability, re-keyed src copy vs built (full output: $D/unf_rekeyed.log):"
grep -E "$P_UNF|^rows in scope|^  (BEFORE|AFTER) " <<< "$U2"
echo "exit $u2 (expect 0)"
[ "$u2" -eq 0 ] && [ "$(grep -E "$P_UNF" <<< "$U2")" = "$LUNF" ] || { echo "8B3b RESULT: STOP - unfindability (re-keyed) is not PASS 0 / 0; built untouched"; exit 1; }
python3 "$P" delta "$D/before.db" "$M" "built before -> dry copy after the two builders" "$DL" || { echo "8B3b RESULT: STOP - the dry run's rows differ from the declared 58 or touch another table (listed above); built untouched"; exit 1; }
echo "dry run = the expected picture (split + 32,478 - binding lines = 10/25 - controls 10/0 - unfindability 0/5 as-is, 0/0 re-keyed - identity = the 58 declared rows, the other four tables 0) - applying to built"
echo "=== APPLY on built, in order ==="
AID=$(python3 scripts/build_pn_greek_identity.py "$B" --apply 2>&1); ai=$?
printf '%s\n' "$AID" > "$D/apply_identity.log"; cp "$RC" "$D/greek_header_split_apply.txt"
echo "--- 1 build_pn_greek_identity on built (full output: $D/apply_identity.log):"
grep -E "$P_ID" <<< "$AID"
echo "exit $ai (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$AID")" = "$(sed 1d <<< "$DID")" ] && echo yes || echo NO)"
[ "$ai" -eq 0 ] && [ "$(sed 1d <<< "$AID")" = "$(sed 1d <<< "$DID")" ] || { echo "8B3b RESULT: CHECK - identity on built did not reproduce the dry run; binding NOT run. Built's identity before-state: $D/before.db"; exit 1; }
ABD=$(python3 scripts/build_entity_binding.py "$B" --apply 2>&1); ab=$?
printf '%s\n' "$ABD" > "$D/apply_binding.log"
TXS=yes; for f in $TX; do cp "$f" "$D/$(basename "$f" .txt)_apply.txt"; cmp -s "$f" "$D/$(basename "$f" .txt)_dry.txt" || TXS=NO; git show "HEAD:$f" | cmp -s - "$f" && echo "  $f from this run = the repo copy" || echo "  $f from this run differs from the repo copy (kept in $D)"; done; git checkout -- $TX
echo "--- 2 build_entity_binding on built (full output: $D/apply_binding.log):"
grep -E "$P_BIND" <<< "$ABD"
echo "exit $ab (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$ABD")" = "$(sed 1d <<< "$DBD")" ] && echo yes || echo NO) - scripts/ dumps = the dry run's: $TXS"
[ "$ab" -eq 0 ] && [ "$(sed 1d <<< "$ABD")" = "$(sed 1d <<< "$DBD")" ] && [ "$TXS" = "yes" ] || { echo "8B3b RESULT: CHECK - binding on built did not reproduce the dry run. Before-state of the five tables: $D/before.db"; exit 1; }
AU=$(python3 scripts/audit_unfindability.py "$U" "$B" --list 2>&1); au=$?
printf '%s\n' "$AU" > "$D/apply_unf.log"
echo "--- 3 audit_unfindability (re-keyed src copy vs built) after the builders:"
grep -E "$P_UNF" <<< "$AU"
echo "exit $au (expect 0) - output = the dry run's: $([ "$AU" = "$U2" ] && echo yes || echo NO)"
ATW=$(python3 scripts/audit_two_derivations.py "$B" 2>&1); at=$?
printf '%s\n' "$ATW" > "$D/apply_twoder.log"
echo "--- 4 audit_two_derivations on built:"
grep -E '^agree: |^controls: ' <<< "$ATW"
echo "exit $at (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$ATW")" = "$(sed 1d <<< "$DTW")" ] && echo yes || echo NO)"
CHK=$(python3 "$P" check "$B" "$M" "$D" "$DL" 2>&1); k=$?
echo "$CHK"
cmp -s "$D/greek_header_split_dry.txt" "$D/greek_header_split_apply.txt" && RCS=yes || RCS=NO
if [ -f "$D/greek_header_split_before.txt" ]; then cmp -s "$D/greek_header_split_before.txt" "$D/greek_header_split_apply.txt" && RB=same || RB=differs; else RB="no earlier copy"; fi
echo "header receipt ($RC): this run = the dry run's: $RCS - vs the copy on PA before: $RB (read-out)"
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] && GS=clean || GS=DIRTY
echo "repo scripts/tests after: $GS (expect clean)"
if [ -e "$B-journal" ]; then J=PRESENT; else J=none; fi
echo "journal after: $J (expect none)"
if [ "$au" -eq 0 ] && [ "$AU" = "$U2" ] && [ "$at" -eq 0 ] && [ "$(sed 1d <<< "$ATW")" = "$(sed 1d <<< "$DTW")" ] && [ "$k" -eq 0 ] && [ "$RCS" = "yes" ] && [ "$GS" = "clean" ] && [ "$J" = "none" ]; then
  echo "8B3b RESULT: DONE - identity 32,478 at the 9.97 split, = before + the 58 declared rows - binding render 15,378 + HOT 68, slot 102 / 0 - unfindability PASS 0/0 (re-keyed), 0/5 as-is = the moved records - two-derivations 10/0 - built = the dry run, nothing else differs vs before - words 626309 + abp_surface unchanged"; exit 0
fi
echo "8B3b RESULT: CHECK - an after-figure differs from the expected picture (lines above). Before-state of the five tables: $D/before.db"; exit 1
) 2>&1 | tee ~/edition_upgrade_runs/pn8b3b_20261107.log; echo "exit=${PIPESTATUS[0]}"
```

### Line PIN8B3B (read-only; reads the 8B3b pin off PA)

```bash
( f=~/edition_upgrade_runs/pn8b3_20261107/identity_delta.tsv; echo "PIN8B3B $(date -u +%FT%TZ) - $f"; [ -s "$f" ] || { echo "PIN8B3B STOP - missing or empty"; exit 1; }; echo "sha256 $(sha256sum < "$f" | cut -d' ' -f1) - $(wc -l < "$f") lines (expect 59) - $(stat -c '%s bytes, modified %y' "$f")"; echo "kinds: $(cut -f1 "$f" | sort | uniq -c | tr '\n' ' ')"; echo "first key: $(sed -n 2p "$f" | cut -f2-4) - last key: $(tail -1 "$f" | cut -f2-4)" ); echo "exit=$?"
```

Reviewer subagent (11/7), verdict line verbatim: "REVIEW: CLEAR - read-only block (scope a): six read-only commands on one run-artifact file, no database opened, no file written (no tee, nothing to overwrite), no `!`, and every line it prints is a read-out whose only ruled anchors (58 rows / 59 lines / all CHANGED) trace to §9.97 and the 8B3R helper code." Expected: 59 lines; kinds 58 CHANGED + 1 header; first/last key read-outs (8B3R printed Gen 4:18 @14 first, Mat 1:5 @7 last); the sha is the pin.

PIN8B3B ran (11/7, 17:43:05Z), exit 0: sha256 `62a99ffe59658f46b9e8a5e385d643b7a147870f38f83136b541d52c5950acca`, 59 lines, 8,536 bytes, modified 17:31:17 UTC; kinds 58 CHANGED + 1 header; first key 98 Gen 4:18 @14, last key 29134 Mat 1:5 @7 (= 8B3R's first and last printed rows). Pin filled into Block 8B3b's two slots; nothing else changed.

## 8B3b RAN — STOP at the dry binding check (11/7, 17:47 UTC); ruled §9.98 → slot TSV edit + 8B3c

Log `~/edition_upgrade_runs/pn8b3b_20261107.log`, PA HEAD 12b3e689. Pin OK (59 lines, 62a99ffe…); pre (a) 0 · (b) OK ·
(c) 451,964,928; the 10/25 lines as in 8B3; header receipt before 2,606 lines; prep and SRCMINI as in 8B3 (words
626,309, identity 32,478, REKEY 6/6, snapshots 32,478 / 15,446, digests 2b23f546 / 623cca1f, dry words 33,376).
Dry identity = the §9.97 split, 526 / 43, 2,602 / 886, exit 0. **Dry binding (exit 0) differed from 10/25:** Hand
rulings 149 replaced (10/25: 151; jonas Joh 21:15/16 gone), `pn_binding render 15,358 + HOT 68` (−20), OVERRIDE 3
(2Ch 22:6 ×2, 2Ki 1:17), `!! REFUSED` ×4 jehoram G1 STALE-NAME (printed 'joram') → slot 98 / 4, written 98 →
`8B3b RESULT: STOP`, exit=1, built untouched. Ruling §9.98 (DESIGN).
**Landed:** `1da5abf0` — `scripts/pn_slot_rulings.tsv`, the 4 rows' printed-name key 'jehoram' → 'joram' with a
comment citing the 8B3b REFUSED lines and the 8B1b log's built 'Joram' (`xref8b1b_20261106.log` OTHER lines 2Ki 8:16
@4, 8:25 @4, 8:29 @4, 8:29 @38); 102 rows still parse; tests green (pre-commit); pushed. **PA must `git pull` (no
deploy, no reload) before 8B3c.**

## 8B3c drafted (11/7) — held for the ruling chat

8B3c = the pinned 8B3b block with only the §9.98 changes (generator asserts each replacement hits once): REF
`1da5abf0`; folder/log `pn8b3c_20261107`; helper file `pn8b3c_helper.py` (= the 8B3b helper + the slot-name rule +
the pn_binding read-out). **Binding expected** = the 10/25 lines minus the OVERRIDE lines, with the Hand line taken
from `pn8b3b_20261107/dry_binding.log` (must start "204 … 3 … 149 replaced") and `render 15,358 + HOT 68`; Witness
A / C / verse-offset and tipnr_entities = 10/25; slot 102 / 0; written 102; any REFUSED / FAILED line = STOP;
OVERRIDE lines printed as a count (10/25: 7). **Dry delta + after-check:** identity = the 58 pinned rows (unchanged
rule); pn_slot_binding = exactly the 4 name changes (book 12 = 2Ki; 8:16 @4, 8:25 @4, 8:29 @4, 8:29 @38; 'jehoram' →
'joram', every other column equal), anything else in the table or a missing one = STOP — see the CC note in §9.98
(the ruling's "0" can't hold: land() stores the name); tipnr_entities + tipnr_entity_refs 0; pn_binding = READ-OUT
written in full to `pn_binding_delta.tsv` (after-check: `pn_binding_delta_after.tsv`), printed by class + first 40,
not counted. Built vs the dry copy stays 0 on all five tables.
Tests: unit (made-up before/after copies): good case passes with the read-out file written; one slot not renamed →
listed NOT SEEN, STOP; an extra slot change → listed OTHER, STOP. Chain on the fake home (repo at `1da5abf0`; 8B3 stop
→ 8B3R list → 8B3c, slot rule emptied because the made-up copy has no slot rows): DONE, all four "= the dry run's:
yes", CHECK OK; and a binding-line mismatch (fake 10/25 log still carrying the old names) → STOP before built.

### Block 8B3c (GATE REF 1da5abf0; WRITES built: pn_greek_identity, pn_binding, tipnr_entities, tipnr_entity_refs, pn_slot_binding)

```bash
set +H
( set -uo pipefail
REF=1da5abf0
echo "GATE REF ${REF} - 8B3c (DESIGN 9.97 + 9.98) the four 8b.3 scripts (build_pn_greek_identity, build_entity_binding, audit_unfindability, audit_two_derivations) on the built copy - dry run on a throwaway copy, identity = the 58 declared rows, slot names = the 4, pn_binding delta read out, apply only on the expected picture - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "8B3c RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "8B3c RESULT: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "8B3c RESULT: STOP - PA has not pulled $REF"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
R=~/bible-db/bible_edupg_test_built_pre_8b_20261106.db
O=~/edition_upgrade_runs
D="$O/pn8b3c_20261107"
DL0="$O/pn8b3_20261107/identity_delta.tsv"
DL="$D/identity_delta_declared.tsv"
M="$D/dry.db"
U="$D/unf_before_rekeyed.db"
L1=~/rekey/live_8b3_id.log; L2=~/rekey/live_8b3_bind.log; L3=~/rekey/live_8b3_unfind.log; L4=~/rekey/live_8b3_twoder.log
RC=docs/tickets/greek_header_split.txt
TX="scripts/pn_binding_hot.txt scripts/pn_binding_numonly.txt"
[ -f "$B" ] || { echo "8B3c RESULT: STOP - missing: $B"; exit 1; }
[ -f "$S" ] || { echo "8B3c RESULT: STOP - missing: $S"; exit 1; }
for f in "$L1" "$L2" "$L3" "$L4"; do [ -s "$f" ] || { echo "8B3c RESULT: STOP - last 8b.3 run log missing or empty: $f"; exit 1; }; done
[ -s "$DL0" ] || { echo "8B3c RESULT: STOP - declared list (8B3R) missing or empty: $DL0"; exit 1; }
echo "declared list: $DL0 - $(wc -l < "$DL0") lines (expect 59 = header + 58) - sha256 $(sha256sum < "$DL0" | cut -c1-16)..."
[ "$(sha256sum < "$DL0" | cut -d' ' -f1)" = 62a99ffe59658f46b9e8a5e385d643b7a147870f38f83136b541d52c5950acca ] && [ "$(wc -l < "$DL0")" = "59" ] || { echo "8B3c RESULT: STOP - the declared list is not the pinned 8B3R file (9.97)"; exit 1; }
if [ -e "$D" ]; then echo "8B3c RESULT: STOP - output folder already exists (already ran?): $D"; exit 1; fi
t=$(sqlite3 -readonly "$B" "SELECT count(*) FROM sqlite_master WHERE type='trigger'") || { echo "8B3c RESULT: STOP - trigger read failed"; exit 1; }
echo "pre (a) triggers on built: $t (expect 0)"
[ "$t" = "0" ] || { echo "8B3c RESULT: STOP - built has triggers"; exit 1; }
for f in "$B" "$S"; do if [ -e "$f-journal" ]; then echo "8B3c RESULT: STOP - $f-journal present (move it aside, never delete; bring it back)"; exit 1; fi; done
echo "pre (b) no -journal beside built or src: OK"
[ -s "$R" ] || { echo "8B3c RESULT: STOP - pre_8b rollback copy missing or empty: $R"; exit 1; }
echo "pre (c) pre_8b copy present: $(stat -c '%s bytes, %y' "$R") - built now $(stat -c '%s bytes' "$B") (size only)"
EXP_OLD=$(printf '%s\n' "  abp-tag    3,671" "  tipnr      10,236" "  lemma-only 12,191" "  surface    4,409" "  none       1,971" "Wrote pn_greek_identity: 32,478 rows.")
P_ID='^  (abp-tag|tipnr|lemma-only|surface|none) +[0-9,]+$|^Wrote pn_greek_identity: '
P_BIND='^  pn_binding      : |^  tipnr_entities  : |^slot rulings: |^pn_slot_binding written: |^Hand rulings: |^Witness |REFUSED|FAILED|OVERRIDE'
P_UNF='^findable-(before|after) +check failures: |^UNFINDABILITY GATE: '
echo "--- last 8b.3 run (10/25), the lines this run must reproduce, with their line numbers:"
echo "$L1:"; grep -nE "$P_ID" "$L1"
EXP_ID=$(printf '%s\n' "  abp-tag    3,671" "  tipnr      10,246" "  lemma-only 12,216" "  surface    4,382" "  none       1,963" "Wrote pn_greek_identity: 32,478 rows.")
[ "$(grep -E "$P_ID" "$L1")" = "$EXP_OLD" ] || { echo "8B3c RESULT: STOP - the 10/25 identity log does not show the ruled split 3,671 / 10,236 / 12,191 / 4,409 / 1,971 and 32,478 rows"; exit 1; }
echo "$L2:"; grep -nE "$P_BIND" "$L2"
LBIND=$(grep -E "$P_BIND" "$L2")
grep -qxF "  pn_binding      : render 15,378 + HOT 68" <<< "$LBIND" && grep -qE '^slot rulings: 102 landable, 0 refused of ' <<< "$LBIND" && grep -qxF "pn_slot_binding written: 102 rows." <<< "$LBIND" || { echo "8B3c RESULT: STOP - the 10/25 binding log does not show render 15,378 + HOT 68 and 102 slot binds / 0 refused"; exit 1; }
[ "$(grep -cE 'REFUSED|FAILED' <<< "$LBIND")" = "0" ] || { echo "8B3c RESULT: STOP - the 10/25 binding log shows a refusal or failure"; exit 1; }
L3B="$O/pn8b3b_20261107/dry_binding.log"
[ -s "$L3B" ] || { echo "8B3c RESULT: STOP - the 8B3b dry binding log is missing: $L3B"; exit 1; }
HAND3B=$(grep -E '^Hand rulings: ' "$L3B")
echo "$L3B (declared Hand line, 9.98 b): $(grep -nE '^Hand rulings: ' "$L3B" | cut -c1-110)..."
case "$HAND3B" in "Hand rulings: 204 new render binds, 3 already-agreeing, 149 replaced floor/HOT rows "*) ;; *) echo "8B3c RESULT: STOP - the 8B3b dry log has no single Hand rulings line with 149 replaced"; exit 1;; esac
BASE=$(grep -vE 'OVERRIDE' <<< "$LBIND")
EXPB=$(while IFS= read -r l; do case "$l" in "Hand rulings: "*) printf '%s\n' "$HAND3B";; "  pn_binding      : "*) printf '%s\n' "  pn_binding      : render 15,358 + HOT 68";; *) printf '%s\n' "$l";; esac; done <<< "$BASE")
echo "expected binding lines (OVERRIDE lines aside): Hand rulings = the 8B3b line (149) - Witness A / C / verse-offset + tipnr_entities = 10/25 - $(grep -E '^  pn_binding' <<< "$EXPB") - $(grep -E '^slot rulings' <<< "$EXPB") - $(grep -E '^pn_slot_binding written' <<< "$EXPB")"
echo "$L3:"; grep -nE "$P_UNF|^rows in scope" "$L3"
LUNF=$(grep -E "$P_UNF" "$L3")
[ "$LUNF" = "$(printf '%s\n' "findable-before check failures: 0 (expected 0)" "findable-after  check failures: 0 (expected 0)" "UNFINDABILITY GATE: PASS — zero findable-before/unfindable-after.")" ] || { echo "8B3c RESULT: STOP - the 10/25 unfindability log is not PASS 0 / 0"; exit 1; }
echo "$L4:"; grep -nE '^Hebrew-keyed PN numbers: |^agree: |^controls: ' "$L4"
LTWO=$(grep -E '^controls: ' "$L4")
LTWC=$(grep -E '^Hebrew-keyed PN numbers: |^agree: ' "$L4")
[ "$LTWO" = "controls: 10  failed: 0" ] || { echo "8B3c RESULT: STOP - the 10/25 two-derivations log is not controls 10 failed 0"; exit 1; }
mkdir -p "$D"
cp "$DL0" "$DL"; [ "$(sha256sum < "$DL" | cut -d' ' -f1)" = 62a99ffe59658f46b9e8a5e385d643b7a147870f38f83136b541d52c5950acca ] || { echo "8B3c RESULT: STOP - declared list copy differs"; exit 1; }
P="$D/pn8b3c_helper.py"
cat > "$P" <<'PY'
"""8B3c helper (one-off, edition upgrade stage D, step 8b.3; = the 8B3b helper + DESIGN 9.98: the slot
table may differ only by the 4 jehoram -> joram names, the pn_binding delta is a READ-OUT saved to a
file). Never writes the built copy or src.

  prep    <built.db> <dry.db> <dir>   read built; save its before-state (the five tables the two
                                      builders replace -> <dir>/before.db + two snapshot files;
                                      words per-row fingerprints; abp_surface count + digest);
                                      write a THROWAWAY copy (<dry.db>) holding just what the four
                                      8b.3 scripts read, for the dry run
  srcmini <src.db> <out.db>           a THROWAWAY copy of src's identity + xref (+ words keys) with
                                      the committed REKEY moves applied, as the unfindability
                                      audit's before side (its matching is by position)
  unf1    <audit.log> <src.db>        the as-is audit (src vs built): findable-after failures must
                                      be exactly the in-scope records at the old REKEY positions
  delta   <a.db> <b.db> <label> <declared.tsv> <pn_binding_delta.tsv>
                                      row-level differences in the five tables, a -> b; the
                                      identity rows must be exactly the declared list (key +
                                      before/after); pn_slot_binding = the 4 declared name
                                      changes; tipnr_entities / tipnr_entity_refs 0;
                                      pn_binding differences written in full + printed
                                      by class + first 40, NOT counted (9.98 b)
  check   <built.db> <dry.db> <dir> <declared.tsv> <pn_binding_delta_after.tsv>
                                      after the apply: words + abp_surface unchanged, built = dry
                                      copy on the five tables, delta vs before, the 6 re-keyed
                                      records and the 16 abp-tag rows

Usage: python3 pn8b3c_helper.py <mode> ...
"""
import ast
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path.home() / "bible-db"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
MOVES = REPO / "tests" / "fixtures" / "edition_upgrade" / "pn_greek_identity_key_moves_20261106.tsv"
WORDS_EXPECT = 626309
IDENTITY_EXPECT = 32478
UNF1_EXPECT = 5
SCOPE = ("tipnr", "lemma-only", "surface")
# the five tables build_pn_greek_identity / build_entity_binding (+ build_slot_binding.land) replace
OUT = (("pn_greek_identity", ("verse_id", "position")),
       ("pn_binding", ("book", "chapter", "verse", "name")),
       ("tipnr_entities", ("uniq",)),
       ("tipnr_entity_refs", None),
       ("pn_slot_binding", ("book", "chapter", "verse", "position")))
# everything the four scripts read (main() of each, top to bottom)
READS = ("verses", "words", "abp_surface", "pn_binding", "pn_hebrew_xref", "pn_greek_identity",
         "tipnr_entities", "tipnr_entity_refs", "pn_slot_binding", "metav_places",
         "metav_place_aliases", "metav_people", "metav_people_aliases")
ABPTAG16 = ((21270, 1), (23928, 2), (24148, 16), (24461, 2), (24627, 9), (25170, 6), (25225, 0),
            (25374, 19), (25553, 12), (26424, 2), (27237, 1), (28665, 6), (29083, 13), (29141, 13),
            (29142, 0), (31003, 4))


def stop(msg):
    print("8B3c RESULT: STOP - " + msg)
    sys.exit(1)


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=30)
    c.execute("PRAGMA query_only=1")
    return c


def tables(c):
    return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def cols(c, t):
    return [r[1] for r in c.execute("PRAGMA table_info(%s)" % t)]


def moves():
    out = []
    for ln in MOVES.read_text(encoding="utf-8").splitlines()[1:]:
        if ln.strip():
            v, o, n = ln.split("\t")
            out.append((int(v), int(o), int(n)))
    if not len(out) == 6:
        stop("moves file has %d rows, not 6" % len(out))
    return out


def ref(c, vid):
    r = c.execute("SELECT book, chapter, verse FROM verses WHERE id=?", (vid,)).fetchone()
    return "%s %d:%d" % r if r else "verse %s ?" % vid


def words_fingerprints(c, path):
    h = hashlib.sha256()
    n = 0
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in c.execute("SELECT rowid, * FROM words ORDER BY rowid"):
            line = "%s\t%s\n" % (r[0], hashlib.sha1(repr(tuple(r)).encode("utf-8")).hexdigest())
            f.write(line)
            h.update(line.encode("utf-8"))
            n += 1
    return n, h.hexdigest()


def surface_digest(c):
    rows = sorted(repr(tuple(r)) for r in c.execute("SELECT * FROM abp_surface"))
    h = hashlib.sha256()
    for s in rows:
        h.update(s.encode("utf-8"))
        h.update(b"\n")
    return len(rows), h.hexdigest()


def keyed(c, t, key):
    cs = cols(c, t)
    d = {}
    for r in c.execute("SELECT * FROM %s" % t):
        k = tuple(r[cs.index(x)] for x in key) if key else tuple(r)
        d.setdefault(k, []).append(tuple(r))
    for k in d:
        d[k].sort(key=repr)
    return cs, d


IDCOLS = ("greek_strongs", "greek_lemma", "source", "hebrew_base")
# DESIGN 9.98 (a): the 4 Israel-king slots whose ruled printed name became 'joram' (2Ki = book 12)
SLOT4 = {(12, 8, 16, 4), (12, 8, 25, 4), (12, 8, 29, 4), (12, 8, 29, 38)}
SLOT4_FROM, SLOT4_TO = "jehoram", "joram"


def declared(path):
    """The declared identity rows (8B3R's identity_delta.tsv): {(verse_id, position): (before, after)}."""
    out = {}
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines[0].startswith("kind\tverse_id\tref\tposition\t"):
        stop("declared list header is not 8B3R's: %s" % path)
    for ln in lines[1:]:
        f = ln.split("\t")
        k = (int(f[1]), int(f[3]))
        if k in out:
            stop("declared list has key %s twice" % (k,))
        out[k] = (ast.literal_eval(f[-2]), ast.literal_eval(f[-1]))
    return out


def delta(a, b, refc, expect=None, readout=None):
    """Print row-level differences a -> b on the five tables. Returns the total of differences
    NOT allowed. With expect (the declared identity rows): identity must equal it exactly (key +
    before/after) and pn_slot_binding may differ only by the SLOT4 name changes. With readout (a
    file path): pn_binding differences are written there in full and printed by class + first 40,
    and are NOT counted (9.98 b)."""
    total = 0
    for t, key in OUT:
        ca, da = keyed(a, t, key)
        cb, db = keyed(b, t, key)
        if not ca == cb:
            print("  %s: columns differ %s -> %s" % (t, ca, cb))
            total += 1
            continue
        rem = sorted((k for k in da if k not in db), key=repr)
        add = sorted((k for k in db if k not in da), key=repr)
        chg = sorted((k for k in da if k in db and not da[k] == db[k]), key=repr)
        n = len(rem) + len(add) + len(chg)
        print("  %s: rows %d -> %d - changed %d, added %d, removed %d"
              % (t, sum(len(x) for x in da.values()), sum(len(x) for x in db.values()), len(chg), len(add), len(rem)))
        if t == "pn_greek_identity" and expect is not None:
            ix = [ca.index(x) for x in IDCOLS]
            def rec(rows):
                return tuple(rows[0][i] for i in ix) if rows else None
            got = {k: (rec(da.get(k)), rec(db.get(k))) for k in set(rem) | set(add) | set(chg)}
            extra = sorted(k for k in got if k not in expect)
            absent = sorted(k for k in expect if k not in got)
            wrong = sorted(k for k in got if k in expect and not got[k] == expect[k])
            bad = len(extra) + len(absent) + len(wrong)
            total += bad
            trans = {}
            for k in got:
                tr = "%s -> %s" % ((got[k][0] or ("-",) * 4)[2], (got[k][1] or ("-",) * 4)[2])
                trans[tr] = trans.get(tr, 0) + 1
            print("    by source: " + " - ".join("%s %d" % kv for kv in sorted(trans.items(), key=lambda x: (-x[1], x[0]))))
            print("    = the declared list (%d rows, key + before/after values): %s - not declared %d, declared but "
                  "absent %d, values differ %d" % (len(expect), "yes" if not bad else "NO", len(extra), len(absent), len(wrong)))
            shown = 0
            for kind, ks in (("NOT DECLARED", extra), ("DECLARED, ABSENT", absent), ("VALUES DIFFER", wrong)):
                for k in ks:
                    if shown == 40:
                        break
                    shown += 1
                    print("    %s %s  [%s]: got %s - declared %s" % (kind, k, ref(refc, k[0]), got.get(k), expect.get(k)))
            continue
        if t == "pn_slot_binding" and expect is not None:
            ni = ca.index("name")
            def rest(rows):
                return [tuple(x for i, x in enumerate(r) if not i == ni) for r in rows]
            okk = set(k for k in chg if k in SLOT4 and len(da[k]) == 1 and len(db[k]) == 1
                      and da[k][0][ni] == SLOT4_FROM and db[k][0][ni] == SLOT4_TO and rest(da[k]) == rest(db[k]))
            other = sorted(set(chg) - okk, key=repr) + add + rem
            unseen = sorted(SLOT4 - okk)
            total += len(other) + len(unseen)
            print("    = the 4 declared name changes (2Ki 8:16@4, 8:25@4, 8:29@4, 8:29@38 %s -> %s, every other column "
                  "equal; 9.98 a): %s - seen %d, other differences %d, declared but not seen %d"
                  % (SLOT4_FROM, SLOT4_TO, "yes" if not (other or unseen) else "NO", len(okk), len(other), len(unseen)))
            for k in other[:40]:
                print("    OTHER %s: %s -> %s" % (k, da.get(k), db.get(k)))
            for k in unseen:
                print("    NOT SEEN %s: %s -> %s" % (k, da.get(k), db.get(k)))
            continue
        if t == "pn_binding" and readout is not None:
            def what(k):
                if k not in da:
                    return "added render=%s" % ",".join(str(r[ca.index("render")]) for r in db[k])
                if k not in db:
                    return "removed render=%s" % ",".join(str(r[ca.index("render")]) for r in da[k])
                if not len(da[k]) == len(db[k]):
                    return "changed: row count %d -> %d" % (len(da[k]), len(db[k]))
                cc = sorted({ca[i] for x, y in zip(da[k], db[k]) for i in range(len(x)) if not x[i] == y[i]})
                return "changed: " + ",".join(cc)
            keys = [("CHANGED", k) for k in chg] + [("ADDED", k) for k in add] + [("REMOVED", k) for k in rem]
            classes = {}
            with open(readout, "w", encoding="utf-8", newline="\n") as f:
                f.write("kind\tbook\tchapter\tverse\tname\tclass\tbefore\tafter\n")
                for kind, k in keys:
                    c_ = what(k)
                    classes[c_] = classes.get(c_, 0) + 1
                    f.write("%s\t%s\t%s\t%s\t%s\t%s\t%r\t%r\n" % (kind, k[0], k[1], k[2], k[3], c_, da.get(k), db.get(k)))
            print("    READ-OUT, not a stop (9.98 b) - all %d in %s" % (n, readout))
            if n:
                print("    by class: " + " - ".join("%s %d" % kv for kv in sorted(classes.items(), key=lambda x: (-x[1], x[0]))))
                print("    first 40:")
            for kind, k in keys[:40]:
                print("    %s %s [%s]: %s -> %s" % (kind, k, what(k), da.get(k), db.get(k)))
            continue
        total += n
        if not n:
            continue
        si = ca.index("source") if t == "pn_greek_identity" else None
        ri = ca.index("render") if t == "pn_binding" else None
        def cls(rows):
            if si is not None:
                return rows[0][si]
            if ri is not None:
                return "render=%s" % rows[0][ri]
            return t
        classes = {}
        for k in chg:
            c_ = "changed %s -> %s" % (cls(da[k]), cls(db[k]))
            classes[c_] = classes.get(c_, 0) + 1
        for k in add:
            c_ = "added %s" % cls(db[k])
            classes[c_] = classes.get(c_, 0) + 1
        for k in rem:
            c_ = "removed %s" % cls(da[k])
            classes[c_] = classes.get(c_, 0) + 1
        if n > 40:
            print("    by class: " + " - ".join("%s %d" % kv for kv in sorted(classes.items())))
            print("    first 40:")
        shown = 0
        for kind, ks, src in (("CHANGED", chg, None), ("ADDED", add, db), ("REMOVED", rem, da)):
            for k in ks:
                if shown == 40:
                    break
                shown += 1
                where = ("  [%s]" % ref(refc, k[0])) if t == "pn_greek_identity" else ""
                if kind == "CHANGED":
                    print("    CHANGED %s%s: %s -> %s" % (k, where, da[k], db[k]))
                else:
                    print("    %s %s%s: %s" % (kind, k, where, src[k]))
    return total


MODE = sys.argv[1]

if MODE == "prep":
    B, DRY, DIR = sys.argv[2], sys.argv[3], Path(sys.argv[4])
    c = ro(B)
    have = tables(c)
    miss = [t for t in READS if t not in have]
    if miss:
        stop("built has no table(s) %s" % miss)
    nw = c.execute("SELECT count(*) FROM words").fetchone()[0]
    ni = c.execute("SELECT count(*) FROM pn_greek_identity").fetchone()[0]
    print("words on built before: %d (expect %d) - identity rows %d (expect %d)" % (nw, WORDS_EXPECT, ni, IDENTITY_EXPECT))
    if not (nw == WORDS_EXPECT and ni == IDENTITY_EXPECT):
        stop("words or identity count before")
    for v, o, n in moves():
        at_new = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, n)).fetchone()[0]
        at_old = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()[0]
        if not (at_new == 1 and at_old == 0):
            stop("REKEY record %s %d->%d: %d at new, %d at old on built" % (ref(c, v), o, n, at_new, at_old))
    print("REKEY records on built: 6/6 at their new positions, none at the old")
    if Path(DRY).exists() or (DIR / "before.db").exists():
        stop("dry copy or before.db already exists")
    # before-state of the five tables the builders replace
    bconn = sqlite3.connect(str(DIR / "before.db"), uri=True)
    bconn.execute("PRAGMA journal_mode=DELETE")
    bconn.execute("ATTACH DATABASE ? AS b", ("file:%s?mode=ro" % B,))
    for t, _k in OUT:
        bconn.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
        bconn.execute("INSERT INTO main.%s SELECT * FROM b.%s" % (t, t))
    bconn.execute("CREATE TABLE verses AS SELECT id, book, chapter, verse FROM b.verses")
    bconn.commit()
    bconn.execute("DETACH DATABASE b")
    bconn.close()
    for t, order, f in (("pn_greek_identity", "verse_id, position", "identity_before.tsv"),
                        ("pn_binding", "book, chapter, verse, name, entity_uniq", "binding_before.tsv")):
        cs = cols(c, t)
        with open(DIR / f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(cs) + "\n")
            n = 0
            for r in c.execute("SELECT * FROM %s ORDER BY %s" % (t, order)):
                fh.write("\t".join(repr(x) for x in r) + "\n")
                n += 1
        print("snapshot %s before: %d rows -> %s" % (t, n, DIR / f))
    nwf, wdig = words_fingerprints(c, DIR / "words_before.tsv")
    ns, sdig = surface_digest(c)
    print("words fingerprints before: %d rows, digest %s - abp_surface before: %d rows, digest %s" % (nwf, wdig[:8], ns, sdig[:8]))
    # the throwaway copy: what the four scripts read
    from build_slot_binding import read_tsv
    slot_v = set()
    for r in read_tsv():
        x = c.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                      (r["book"], int(r["chapter"]), int(r["verse"]))).fetchone()
        if x:
            slot_v.add(x[0])
    d = sqlite3.connect(DRY, uri=True)
    d.execute("PRAGMA journal_mode=DELETE")
    d.execute("ATTACH DATABASE ? AS b", ("file:%s?mode=ro" % B,))
    for t in READS:
        d.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
    d.execute("CREATE TEMP TABLE sv (id INTEGER PRIMARY KEY)")
    d.executemany("INSERT INTO sv VALUES (?)", [(v,) for v in sorted(slot_v)])
    for t in READS:
        if t == "words":
            d.execute("INSERT INTO main.words SELECT * FROM b.words WHERE is_pn=1 OR verse_id IN (SELECT id FROM sv)")
        elif t == "abp_surface":
            d.execute("INSERT INTO main.abp_surface SELECT * FROM b.abp_surface s WHERE EXISTS "
                      "(SELECT 1 FROM main.words w WHERE w.verse_id=s.verse_id AND w.position=s.position)")
        else:
            d.execute("INSERT INTO main.%s SELECT * FROM b.%s" % (t, t))
    for (sql,) in c.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL AND tbl_name IN (%s)"
                            % ",".join("?" * len(READS)), READS):
        d.execute(sql)
    d.commit()
    counts = {t: d.execute("SELECT count(*) FROM main.%s" % t).fetchone()[0] for t in READS}
    d.execute("DETACH DATABASE b")
    d.close()
    print("dry copy: " + " - ".join("%s %d" % (t, counts[t]) for t in READS))
    print("  (words = the proper-noun rows + every row of the %d verses pn_slot_rulings.tsv names)" % len(slot_v))
    json.dump({"words_rows": nwf, "words_digest": wdig, "surface_rows": ns, "surface_digest": sdig},
              open(DIR / "state.json", "w", encoding="utf-8"))
    print("8B3c PREP: OK")

elif MODE == "srcmini":
    S, OUTDB = sys.argv[2], sys.argv[3]
    c = ro(S)
    if Path(OUTDB).exists():
        stop("exists: %s" % OUTDB)
    d = sqlite3.connect(OUTDB, uri=True)
    d.execute("PRAGMA journal_mode=DELETE")
    d.execute("ATTACH DATABASE ? AS s", ("file:%s?mode=ro" % S,))
    for t in ("pn_greek_identity", "pn_hebrew_xref"):
        d.execute(c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0])
        d.execute("INSERT INTO main.%s SELECT * FROM s.%s" % (t, t))
    d.execute("CREATE TABLE words (verse_id INTEGER, position INTEGER, strongs_base TEXT)")
    d.execute("INSERT INTO main.words SELECT verse_id, position, strongs_base FROM s.words")
    for v, o, n in moves():
        for t in ("pn_greek_identity", "pn_hebrew_xref"):
            a = d.execute("SELECT count(*) FROM main.%s WHERE verse_id=? AND position=?" % t, (v, o)).fetchone()[0]
            b = d.execute("SELECT count(*) FROM main.%s WHERE verse_id=? AND position=?" % t, (v, n)).fetchone()[0]
            if not (a == 1 and b == 0):
                stop("src %s %s %d->%d: %d at old, %d at new" % (t, ref(c, v), o, n, a, b))
            d.execute("UPDATE main.%s SET position=? WHERE verse_id=? AND position=?" % t, (n, v, o))
        print("  src record %s (verse_id %d) pos %d -> %d: identity + xref moved" % (ref(c, v), v, o, n))
    d.commit()
    ni = d.execute("SELECT count(*) FROM main.pn_greek_identity").fetchone()[0]
    nx = d.execute("SELECT count(*) FROM main.pn_hebrew_xref").fetchone()[0]
    nw = d.execute("SELECT count(*) FROM main.words").fetchone()[0]
    d.execute("DETACH DATABASE s")
    d.close()
    print("re-keyed src copy: identity %d - xref %d - words keys %d -> %s" % (ni, nx, nw, OUTDB))
    print("8B3c SRCMINI: OK")

elif MODE == "unf1":
    LOG, S = sys.argv[2], sys.argv[3]
    c = ro(S)
    exp = set()
    for v, o, n in moves():
        r = c.execute("SELECT source FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()
        print("  src record %s (verse_id %d) at old pos %d: class %s%s"
              % (ref(c, v), v, o, r[0] if r else None, " (in the audit's scope)" if r and r[0] in SCOPE else " (out of scope)"))
        if r and r[0] in SCOPE:
            exp.add((v, o))
    text = Path(LOG).read_text(encoding="utf-8").splitlines()
    got = set()
    nb = na = None
    for ln in text:
        if ln.startswith("findable-before check failures: "):
            nb = ln.split(": ")[1].split()[0]
        if ln.startswith("findable-after  check failures: "):
            na = ln.split(": ")[1].split()[0]
        if ln.startswith("  AFTER ("):
            k = ln[len("  AFTER ("):].split(")")[0].split(",")
            got.add((int(k[0]), int(k[1])))
    print("as-is audit: before failures %s (expect 0) - after failures %s (expect %d) - failing keys = old REKEY keys in scope: %s"
          % (nb, na, UNF1_EXPECT, "yes" if got == exp else "NO (got %s, expect %s)" % (sorted(got), sorted(exp))))
    if not (nb == "0" and na == str(UNF1_EXPECT) and len(exp) == UNF1_EXPECT and got == exp):
        stop("the as-is unfindability audit is not exactly the moved-position picture")
    print("8B3c UNF1: OK")

elif MODE == "delta":
    A, Bp, label, EXP, RD = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
    if Path(RD).exists():
        stop("exists: %s" % RD)
    a, b = ro(A), ro(Bp)
    print("delta, %s:" % label)
    n = delta(a, b, a, declared(EXP), RD)
    print("  differences outside the declared rows (identity 58, slot names 4; pn_binding read out): %d (expect 0)" % n)
    sys.exit(0 if n == 0 else 1)

elif MODE == "check":
    B, DRY, DIR, EXP, RD = sys.argv[2], sys.argv[3], Path(sys.argv[4]), sys.argv[5], sys.argv[6]
    st = json.load(open(DIR / "state.json", encoding="utf-8"))
    c, d, bef = ro(B), ro(DRY), ro(str(DIR / "before.db"))
    bad = []
    nw = c.execute("SELECT count(*) FROM words").fetchone()[0]
    nwf, wdig = words_fingerprints(c, DIR / "words_after.tsv")
    a_lines = (DIR / "words_after.tsv").read_text(encoding="utf-8").splitlines()
    b_lines = (DIR / "words_before.tsv").read_text(encoding="utf-8").splitlines()
    wdiff = sum(1 for x, y in zip(b_lines, a_lines) if not x == y) + abs(len(a_lines) - len(b_lines))
    print("words on built after: %d (expect %d) - per-row fingerprint lines differing from before: %d (expect 0) - digest %s (before %s)"
          % (nw, WORDS_EXPECT, wdiff, wdig[:8], st["words_digest"][:8]))
    if not (nw == WORDS_EXPECT and wdiff == 0 and wdig == st["words_digest"]):
        bad.append("words changed")
    ns, sdig = surface_digest(c)
    print("abp_surface after: %d rows, digest %s (expect %d, %s - unchanged)" % (ns, sdig[:8], st["surface_rows"], st["surface_digest"][:8]))
    if not (ns == st["surface_rows"] and sdig == st["surface_digest"]):
        bad.append("abp_surface changed")
    print("built after vs the dry copy (must be identical):")
    if delta(d, c, c):
        bad.append("built differs from the dry run")
    print("built after vs built before (identity = the declared 58, slot names = the 4, tipnr tables 0, pn_binding read out):")
    if delta(bef, c, c, declared(EXP), RD):
        bad.append("a table differs from its before-snapshot")
    print("the 6 REKEY records on built after (verse_id, position, greek_strongs, greek_lemma, source, hebrew_base | xref | words english, strongs, strongs_base, is_pn):")
    for v, o, n in moves():
        g = c.execute("SELECT * FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, n)).fetchone()
        x = c.execute("SELECT hebrew_base, class FROM pn_hebrew_xref WHERE verse_id=? AND position=?", (v, n)).fetchone()
        w = c.execute("SELECT english, strongs, strongs_base, is_pn FROM words WHERE verse_id=? AND position=?", (v, n)).fetchone()
        old = c.execute("SELECT count(*) FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, o)).fetchone()[0]
        print("  %s new pos %d: %s | xref %s | words %s | identity rows at old pos %d: %d" % (ref(c, v), n, g, x, w, o, old))
        if g is None or old:
            bad.append("REKEY record %s" % ref(c, v))
    print("the 16 abp-tag rows (9.96) on built after (identity | words strongs, strongs_base) - retire's abp-tag check:")
    ok16 = 0
    for v, p in ABPTAG16:
        g = c.execute("SELECT greek_strongs, greek_lemma, source, hebrew_base FROM pn_greek_identity WHERE verse_id=? AND position=?", (v, p)).fetchone()
        w = c.execute("SELECT english, strongs, strongs_base FROM words WHERE verse_id=? AND position=?", (v, p)).fetchone()
        good = bool(g and w and g[2] == "abp-tag" and w[2] == g[0] and (w[2] or "").startswith("G") and g[3] is None)
        ok16 += good
        print("  %s (verse_id %d) pos %d: %s | %s | %s" % (ref(c, v), v, p, g, w, "OK" if good else "FAIL"))
    print("abp-tag check on the 16: %d/16 OK" % ok16)
    if not ok16 == 16:
        bad.append("abp-tag rows")
    if bad:
        for b_ in bad:
            print("  problem: " + b_)
        print("8B3c CHECK: FAIL")
        sys.exit(1)
    print("8B3c CHECK: OK")
else:
    stop("unknown mode")
PY
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = faa299aa9da4bd11cf5627066e5f7352390d38c66d5ec5fb78add2173242eb66 ] || { echo "8B3c RESULT: STOP - the pasted helper does not match the drafted one"; exit 1; }
if [ -f "$RC" ]; then cp "$RC" "$D/greek_header_split_before.txt"; echo "header receipt on PA before: $(wc -l < "$RC") lines (kept as $D/greek_header_split_before.txt)"; else echo "header receipt on PA before: none"; fi
python3 "$P" prep "$B" "$M" "$D" || { echo "8B3c RESULT: STOP - prep did not pass (line above); built untouched"; exit 1; }
python3 "$P" srcmini "$S" "$U" || { echo "8B3c RESULT: STOP - re-keyed src copy did not pass (line above); built untouched"; exit 1; }
echo "=== DRY RUN on the throwaway copy (built untouched) ==="
DID=$(python3 scripts/build_pn_greek_identity.py "$M" --apply 2>&1); di=$?
printf '%s\n' "$DID" > "$D/dry_identity.log"; cp "$RC" "$D/greek_header_split_dry.txt"
echo "--- 1 build_pn_greek_identity (full output: $D/dry_identity.log):"
grep -E "$P_ID|^identity split|^name-match gate|^pn_binding render rows|^proper-noun words|^pn_hebrew_xref loaded|^hand-table|^receipt written" <<< "$DID"
echo "exit $di (expect 0)"
[ "$di" -eq 0 ] && [ "$(grep -E "$P_ID" <<< "$DID")" = "$EXP_ID" ] || { echo "8B3c RESULT: STOP - dry identity build is not the 9.97 split 3,671 / 10,246 / 12,216 / 4,382 / 1,963 and 32,478; built untouched"; exit 1; }
DBD=$(python3 scripts/build_entity_binding.py "$M" --apply 2>&1); db=$?
printf '%s\n' "$DBD" > "$D/dry_binding.log"
for f in $TX; do cp "$f" "$D/$(basename "$f" .txt)_dry.txt"; done; git checkout -- $TX
echo "--- 2 build_entity_binding (full output: $D/dry_binding.log; its two scripts/ dumps kept in $D and put back in the repo):"
grep -E "$P_BIND" <<< "$DBD"
echo "exit $db (expect 0)"
DB1=$(grep -E "$P_BIND" <<< "$DBD"); DB2=$(grep -vE 'OVERRIDE' <<< "$DB1")
echo "OVERRIDE lines: $(grep -cE 'OVERRIDE' <<< "$DB1") (10/25: 7; read-out)"
[ "$db" -eq 0 ] && [ "$DB2" = "$EXPB" ] && [ "$(grep -cE 'REFUSED|FAILED' <<< "$DB1")" = "0" ] || { echo "8B3c RESULT: STOP - dry binding lines are not the 9.98 picture (Hand 149, render 15,358 + HOT 68, slot 102 / 0, written 102, Witness + tipnr_entities = 10/25, no REFUSED); built untouched"; exit 1; }
DTW=$(python3 scripts/audit_two_derivations.py "$M" 2>&1); dt=$?
printf '%s\n' "$DTW" > "$D/dry_twoder.log"
echo "--- 4 audit_two_derivations on the dry copy (full output: $D/dry_twoder.log):"
grep -E '^Hebrew-keyed PN numbers: |^agree: |^\[(PASS|FAIL)\] |^controls: ' <<< "$DTW"
echo "exit $dt (expect 0) - count lines (Hebrew-keyed / agree) vs 10/25: $([ "$(grep -E '^Hebrew-keyed PN numbers: |^agree: ' <<< "$DTW")" = "$LTWC" ] && echo same || echo differ) (read-out, 9.97)"
[ "$dt" -eq 0 ] && [ "$(grep -E '^controls: ' <<< "$DTW")" = "$LTWO" ] || { echo "8B3c RESULT: STOP - dry two-derivations is not controls 10 failed 0; built untouched"; exit 1; }
U1=$(python3 scripts/audit_unfindability.py "$S" "$B" --list 2>&1); u1=$?
printf '%s\n' "$U1" > "$D/unf_asis.log"
echo "--- 3a audit_unfindability as-is, src vs built (position-keyed; full output: $D/unf_asis.log):"
grep -E "$P_UNF|^rows in scope|^  (BEFORE|AFTER) " <<< "$U1"
echo "exit $u1 (expect 1: fails on the moved records only)"
[ "$u1" -eq 1 ] && python3 "$P" unf1 "$D/unf_asis.log" "$S" || { echo "8B3c RESULT: STOP - as-is unfindability is not the moved-position picture; built untouched"; exit 1; }
U2=$(python3 scripts/audit_unfindability.py "$U" "$B" --list 2>&1); u2=$?
printf '%s\n' "$U2" > "$D/unf_rekeyed.log"
echo "--- 3b audit_unfindability, re-keyed src copy vs built (full output: $D/unf_rekeyed.log):"
grep -E "$P_UNF|^rows in scope|^  (BEFORE|AFTER) " <<< "$U2"
echo "exit $u2 (expect 0)"
[ "$u2" -eq 0 ] && [ "$(grep -E "$P_UNF" <<< "$U2")" = "$LUNF" ] || { echo "8B3c RESULT: STOP - unfindability (re-keyed) is not PASS 0 / 0; built untouched"; exit 1; }
python3 "$P" delta "$D/before.db" "$M" "built before -> dry copy after the two builders" "$DL" "$D/pn_binding_delta.tsv" || { echo "8B3c RESULT: STOP - the dry run differs beyond the declared rows (identity 58, slot names 4) or touches a tipnr table (listed above); built untouched"; exit 1; }
echo "dry run = the expected picture (split + 32,478 - binding lines = the 9.98 picture - controls 10/0 - unfindability 0/5 as-is, 0/0 re-keyed - identity = the 58 declared rows, slot names = the 4, tipnr tables 0, pn_binding delta read out) - applying to built"
echo "=== APPLY on built, in order ==="
AID=$(python3 scripts/build_pn_greek_identity.py "$B" --apply 2>&1); ai=$?
printf '%s\n' "$AID" > "$D/apply_identity.log"; cp "$RC" "$D/greek_header_split_apply.txt"
echo "--- 1 build_pn_greek_identity on built (full output: $D/apply_identity.log):"
grep -E "$P_ID" <<< "$AID"
echo "exit $ai (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$AID")" = "$(sed 1d <<< "$DID")" ] && echo yes || echo NO)"
[ "$ai" -eq 0 ] && [ "$(sed 1d <<< "$AID")" = "$(sed 1d <<< "$DID")" ] || { echo "8B3c RESULT: CHECK - identity on built did not reproduce the dry run; binding NOT run. Built's identity before-state: $D/before.db"; exit 1; }
ABD=$(python3 scripts/build_entity_binding.py "$B" --apply 2>&1); ab=$?
printf '%s\n' "$ABD" > "$D/apply_binding.log"
TXS=yes; for f in $TX; do cp "$f" "$D/$(basename "$f" .txt)_apply.txt"; cmp -s "$f" "$D/$(basename "$f" .txt)_dry.txt" || TXS=NO; git show "HEAD:$f" | cmp -s - "$f" && echo "  $f from this run = the repo copy" || echo "  $f from this run differs from the repo copy (kept in $D)"; done; git checkout -- $TX
echo "--- 2 build_entity_binding on built (full output: $D/apply_binding.log):"
grep -E "$P_BIND" <<< "$ABD"
echo "exit $ab (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$ABD")" = "$(sed 1d <<< "$DBD")" ] && echo yes || echo NO) - scripts/ dumps = the dry run's: $TXS"
[ "$ab" -eq 0 ] && [ "$(sed 1d <<< "$ABD")" = "$(sed 1d <<< "$DBD")" ] && [ "$TXS" = "yes" ] || { echo "8B3c RESULT: CHECK - binding on built did not reproduce the dry run. Before-state of the five tables: $D/before.db"; exit 1; }
AU=$(python3 scripts/audit_unfindability.py "$U" "$B" --list 2>&1); au=$?
printf '%s\n' "$AU" > "$D/apply_unf.log"
echo "--- 3 audit_unfindability (re-keyed src copy vs built) after the builders:"
grep -E "$P_UNF" <<< "$AU"
echo "exit $au (expect 0) - output = the dry run's: $([ "$AU" = "$U2" ] && echo yes || echo NO)"
ATW=$(python3 scripts/audit_two_derivations.py "$B" 2>&1); at=$?
printf '%s\n' "$ATW" > "$D/apply_twoder.log"
echo "--- 4 audit_two_derivations on built:"
grep -E '^agree: |^controls: ' <<< "$ATW"
echo "exit $at (expect 0) - output = the dry run's (first line aside): $([ "$(sed 1d <<< "$ATW")" = "$(sed 1d <<< "$DTW")" ] && echo yes || echo NO)"
CHK=$(python3 "$P" check "$B" "$M" "$D" "$DL" "$D/pn_binding_delta_after.tsv" 2>&1); k=$?
echo "$CHK"
cmp -s "$D/greek_header_split_dry.txt" "$D/greek_header_split_apply.txt" && RCS=yes || RCS=NO
if [ -f "$D/greek_header_split_before.txt" ]; then cmp -s "$D/greek_header_split_before.txt" "$D/greek_header_split_apply.txt" && RB=same || RB=differs; else RB="no earlier copy"; fi
echo "header receipt ($RC): this run = the dry run's: $RCS - vs the copy on PA before: $RB (read-out)"
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] && GS=clean || GS=DIRTY
echo "repo scripts/tests after: $GS (expect clean)"
if [ -e "$B-journal" ]; then J=PRESENT; else J=none; fi
echo "journal after: $J (expect none)"
if [ "$au" -eq 0 ] && [ "$AU" = "$U2" ] && [ "$at" -eq 0 ] && [ "$(sed 1d <<< "$ATW")" = "$(sed 1d <<< "$DTW")" ] && [ "$k" -eq 0 ] && [ "$RCS" = "yes" ] && [ "$GS" = "clean" ] && [ "$J" = "none" ]; then
  echo "8B3c RESULT: DONE - identity 32,478 at the 9.97 split, = before + the 58 declared rows - binding render 15,358 + HOT 68, Hand 149, slot 102 / 0 - unfindability PASS 0/0 (re-keyed), 0/5 as-is = the moved records - two-derivations 10/0 - built = the dry run, vs before only the declared rows (pn_binding delta read out) - words 626309 + abp_surface unchanged"; exit 0
fi
echo "8B3c RESULT: CHECK - an after-figure differs from the expected picture (lines above). Before-state of the five tables: $D/before.db"; exit 1
) 2>&1 | tee ~/edition_upgrade_runs/pn8b3c_20261107.log; echo "exit=${PIPESTATUS[0]}"
```

## 8B3c RAN — applied; the after-check did not run (disk quota) (11/7); ruled: cleanup + re-check block 8B3CX

From the ruling chat's read of `~/edition_upgrade_runs/pn8b3c_20261107.log` (CC has not seen the log itself): the
dry run passed and all four apply steps reproduced it (log lines 194 / 213 / 218 / 222 "yes"); the after-check
stopped with `OSError 122 Disk quota exceeded` in `words_fingerprints` (helper :427, writing `words_after.tsv`), and a
git command left `.git/index.lock`. Dry pn_binding delta (read-out): added 70 / removed 90. **Built is at 8b.3 —
built = 8b.0 + REKEY + 8b.1 + §9.96 + 8b.2 + 8b.2a + 8b.3 — verification owed.**
**Ruled (one block, writes to PA home only, built untouched):** (1) quota / usage read-out; (2) delete exactly
`pn8b3_20261107/dry.db`, `pn8b3_20261107/unf_before_rekeyed.db`, `pn8b3b_20261107/dry.db`,
`pn8b3b_20261107/unf_before_rekeyed.db`, `lane3_8b2a_20261106/lane3_dry.db` (logs, TSVs, before.db stay) — sizes
before, du after; (3) `.git/index.lock` removed only if no git process holds it, then scripts/tests clean and the two
binder dumps = HEAD (restored if not); (4) the pinned 8B3c helper's check re-run with the same arguments, plus the
receipt / journal / repo lines, ending in a RESULT line. Expected: CHECK OK, built = dry copy, identity 58, slot 4,
pn_binding read-out = the dry delta (added 70 / removed 90), abp-tag 16/16, Jos 5:15@27 G2424. After the run: /wrap.

### Block 8B3CX (GATE REF 1da5abf0; deletes 5 throwaway copies + a stale git lock; built read-only)

Also checks, from the 8B3c run's saved logs, that the unfindability and two-derivations after-runs equal the dry
run's (the conditions the original DONE line needed). Paste-once marker `pn8b3c_20261107/recheck_started`.
Tests (fake home, the 8B3c test folder after a simulated stop: lock file, a changed dump, partial `words_after.tsv`,
the 5 copies present): DONE (5 deleted, lock removed, dump restored, check OK, saved-log comparisons yes); re-paste →
STOP; a git process listed → STOP, lock left in place.

```bash
set +H
( set -uo pipefail
REF=1da5abf0
echo "GATE REF ${REF} - 8B3CX after 8B3c's disk-quota stop: quota read-out, delete 5 throwaway copies, clear the git index lock, re-run the 8B3c after-check (built read-only) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
git diff --quiet "$REF" HEAD -- scripts tests || { echo "8B3CX RESULT: STOP - scripts/tests differ from $REF"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD || { echo "8B3CX RESULT: STOP - PA has not pulled $REF"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
O=~/edition_upgrade_runs
D="$O/pn8b3c_20261107"
M="$D/dry.db"
DL="$D/identity_delta_declared.tsv"
P="$D/pn8b3c_helper.py"
RC=docs/tickets/greek_header_split.txt
TX="scripts/pn_binding_hot.txt scripts/pn_binding_numonly.txt"
for f in "$B" "$M" "$D/before.db" "$D/state.json" "$D/words_before.tsv" "$DL" "$P" "$D/apply_binding.log" "$D/dry_binding.log"; do [ -s "$f" ] || { echo "8B3CX RESULT: STOP - missing or empty: $f"; exit 1; }; done
[ -e "$D/recheck_started" ] && { echo "8B3CX RESULT: STOP - this block already ran ($D/recheck_started) - paste once"; exit 1; }
touch "$D/recheck_started" || { echo "8B3CX RESULT: STOP - cannot write in $D (disk still full?)"; exit 1; }
[ "$(sha256sum < "$P" | cut -d' ' -f1)" = faa299aa9da4bd11cf5627066e5f7352390d38c66d5ec5fb78add2173242eb66 ] || { echo "8B3CX RESULT: STOP - $P is not the pinned 8B3c helper"; exit 1; }
echo "pinned 8B3c helper present: $P (sha256 matches)"
if [ -e "$B-journal" ]; then echo "8B3CX RESULT: STOP - $B-journal present (move it aside, never delete; bring it back)"; exit 1; fi
echo "built: no -journal - $(stat -c '%s bytes, modified %y' "$B") (read-out; this block opens built read-only)"
echo "=== (1) quota / usage ==="
if command -v quota >/dev/null 2>&1; then quota -s 2>&1 || echo "(quota printed nothing usable)"; else echo "quota command: not available on this host"; fi
echo "du ~ (whole home): $(du -sh ~ 2>/dev/null | cut -f1)"
du -sh "$O"/* 2>/dev/null | sort -h | tail -25
echo "=== (2) delete the 5 ruled throwaway copies (logs, TSVs and before.db stay) ==="
for f in "$O/pn8b3_20261107/dry.db" "$O/pn8b3_20261107/unf_before_rekeyed.db" "$O/pn8b3b_20261107/dry.db" "$O/pn8b3b_20261107/unf_before_rekeyed.db" "$O/lane3_8b2a_20261106/lane3_dry.db"; do
  if [ -e "$f-journal" ]; then echo "8B3CX RESULT: STOP - $f-journal present; not deleting"; exit 1; fi
  if [ -f "$f" ]; then echo "  delete $f - $(stat -c '%s bytes' "$f")"; rm -f "$f" || { echo "8B3CX RESULT: STOP - rm failed: $f"; exit 1; }; [ -e "$f" ] && { echo "8B3CX RESULT: STOP - still present: $f"; exit 1; }; else echo "  already absent: $f"; fi
done
echo "du after: home $(du -sh ~ 2>/dev/null | cut -f1) - edition_upgrade_runs $(du -sh "$O" 2>/dev/null | cut -f1)"
if command -v quota >/dev/null 2>&1; then quota -s 2>&1 | tail -3; fi
echo "=== (3) git index lock + binder dumps ==="
LK=.git/index.lock
if [ -e "$LK" ]; then
  echo "  $LK present: $(stat -c '%s bytes, modified %y' "$LK")"
  if command -v fuser >/dev/null 2>&1; then FU=$(fuser "$LK" 2>&1); echo "  fuser: ${FU:-nothing holds it}"; else FU=""; echo "  fuser: not available"; fi
  GP=$(ps -u "$(id -u)" -o pid=,args= | grep -E '(^|/| )git( |$)' | grep -v grep)
  echo "  git processes of this user: ${GP:-none}"
  [ -z "$GP" ] && [ -z "$(fuser "$LK" 2>/dev/null)" ] || { echo "8B3CX RESULT: STOP - a git process may hold $LK; not removing"; exit 1; }
  rm -f "$LK" || { echo "8B3CX RESULT: STOP - could not remove $LK"; exit 1; }
  echo "  $LK removed"
else
  echo "  $LK: not present"
fi
for f in $TX; do
  if git show "HEAD:$f" | cmp -s - "$f"; then echo "  $f = HEAD"; else echo "  $f differs from HEAD - restoring"; git checkout -- "$f" || { echo "8B3CX RESULT: STOP - git checkout failed: $f"; exit 1; }; git show "HEAD:$f" | cmp -s - "$f" && echo "  $f = HEAD after restore" || { echo "8B3CX RESULT: STOP - $f still differs"; exit 1; }; fi
done
GSP=$(git status --porcelain --untracked-files=no -- scripts tests)
echo "  git status scripts/tests: ${GSP:-clean}"
[ -z "$GSP" ] || { echo "8B3CX RESULT: STOP - scripts/tests not clean after the restore"; exit 1; }
[ -e "$LK" ] && { echo "8B3CX RESULT: STOP - $LK came back"; exit 1; }
echo "=== (4) the 8B3c after-check, re-run (same pinned helper, same arguments; built read-only) ==="
CHK=$(python3 "$P" check "$B" "$M" "$D" "$DL" "$D/pn_binding_delta_after.tsv" 2>&1); k=$?
echo "$CHK"
echo "check exit $k (expect 0)"
UOK=NO; [ -s "$D/apply_unf.log" ] && cmp -s "$D/apply_unf.log" "$D/unf_rekeyed.log" && UOK=yes
TOK=NO; [ -s "$D/apply_twoder.log" ] && [ "$(sed 1d "$D/apply_twoder.log")" = "$(sed 1d "$D/dry_twoder.log")" ] && TOK=yes
echo "from the 8B3c run's saved logs: unfindability after = the dry run's: $UOK - two-derivations after = the dry run's (first line aside): $TOK"
cmp -s "$D/greek_header_split_dry.txt" "$D/greek_header_split_apply.txt" && RCS=yes || RCS=NO
if [ -f "$D/greek_header_split_before.txt" ]; then cmp -s "$D/greek_header_split_before.txt" "$D/greek_header_split_apply.txt" && RB=same || RB=differs; else RB="no earlier copy"; fi
echo "header receipt ($RC): 8B3c apply = its dry run: $RCS - vs the copy on PA before: $RB (read-out)"
[ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] && GS=clean || GS=DIRTY
echo "repo scripts/tests after: $GS (expect clean)"
if [ -e "$B-journal" ]; then J=PRESENT; else J=none; fi
echo "journal after: $J (expect none)"
echo "du after the check: edition_upgrade_runs $(du -sh "$O" 2>/dev/null | cut -f1)"
if [ "$k" -eq 0 ] && [ "$UOK" = "yes" ] && [ "$TOK" = "yes" ] && [ "$RCS" = "yes" ] && [ "$GS" = "clean" ] && [ "$J" = "none" ]; then
  echo "8B3CX RESULT: DONE - 8B3c verified: built = its dry copy, vs before only the declared rows (identity 58, slot names 4; pn_binding read out), words 626309 + abp_surface unchanged, abp-tag 16/16 - built = 8b.0 + REKEY + 8b.1 + 9.96 + 8b.2 + 8b.2a + 8b.3"; exit 0
fi
echo "8B3CX RESULT: CHECK - an after-figure differs (lines above); built was not written by this block"; exit 1
) 2>&1 | tee ~/edition_upgrade_runs/pn8b3cx_20261107.log; echo "exit=${PIPESTATUS[0]}"
```

## PA disk cleanup (11/7) — ruling chat; JP ran it

PA home was at quota (8.3G). Read-only repo check per file (record: this session's report) → JP deleted:
`~/bible-db/bible_pre_pnstar_20260803.db`, `~/bible-db/bible_pre_pnstar_swap_20260805.db` (closed lanes, every banked
figure recorded; the `~/db_evidence/` twins `TODO.md` claimed were never made), `~/bible-db/bible_test.db`,
`~/db_backups/bible_formlane.db.20260906-153935.db` + `.info` (orphaned — rotation only runs for databases still in
`~/bible-db`), `~/db_evidence/bible_formlane.db` (8/23 gated copy). Home now **6.3G**. Kept:
`~/bible-db/bible_pre_trapwire_swap.db` (rollback of record, §9.78 evidence), `~/bible.db.pre-surface-fill-20261025`
(step 9a's only old-table source until 9c), the hdrlane 9/6 backup (§9.95), the 4 form-lane TSVs. Doc notes:
`data-model.md:715`, `HANDOFF_article_slot_rebuild.md:21-22`, `TODO.md` (pnstar + disk-thinning lines),
`HANDOFF_edition_upgrade_stageC.md:29-30`. Still owed: block 8B3CX (the 8B3c after-check) and the backup-stamp read.

## 8B3CX RAN (11/7, 19:53 UTC) — after-check OK; RESULT CHECK on the header receipt line only

Log `~/edition_upgrade_runs/pn8b3cx_20261107.log` (local copy `C:\Users\JP\edition_upgrade_runs\pn8b3cx_20261107.log`):
the 5 copies were already gone (deleted by hand earlier), no git lock, dumps = HEAD, scripts/tests clean. **8B3c
CHECK: OK** — words 626,309, 0 rows differing, digest 2b23f546; abp_surface 395,003 / 623cca1f; built = dry copy on
all five tables; built vs before: identity 58 = the declared list; pn_binding 15,446 → 15,426, added 70 / removed 90
(read-out, all 160 in `pn8b3c_20261107/pn_binding_delta_after.tsv`); tipnr tables 0; pn_slot_binding = the 4 name
changes; 6 REKEY records (Jos 5:15 @27 = G2424 tipnr); abp-tag 16/16; saved-log comparisons yes / yes; repo clean;
journal none. Only miss: `header receipt … 8B3c apply = its dry run: NO - vs the copy on PA before: differs` → RESULT
CHECK. Ruling chat: 8B3c ACCEPTED as DONE under §9.97/§9.98; the receipt NO is a quota artifact — one read-only
line first (below), then record.

### Line RCPT8B3C (read-only; the four receipt copies)

```bash
( cd ~/edition_upgrade_runs/pn8b3c_20261107 || exit 1; echo "RCPT8B3C $(date -u +%FT%TZ)"; for f in greek_header_split_before.txt greek_header_split_dry.txt greek_header_split_apply.txt ~/bible-db/docs/tickets/greek_header_split.txt; do if [ -e "$f" ]; then echo "$f: $(wc -l < "$f") lines - $(stat -c '%s bytes, modified %y' "$f") - sha256 $(sha256sum < "$f" | cut -d' ' -f1)"; else echo "$f: MISSING"; fi; done; for p in "greek_header_split_dry.txt greek_header_split_apply.txt" "greek_header_split_dry.txt greek_header_split_before.txt" "greek_header_split_dry.txt $HOME/bible-db/docs/tickets/greek_header_split.txt"; do set -- $p; echo "cmp $1 vs $(basename "$2"): $(cmp "$1" "$2" 2>&1 || true)"; done; echo "apply copy last line: $(tail -n 1 greek_header_split_apply.txt | cut -c1-120)" ); echo "exit=$?"
```

Reviewer subagent (11/7), verdict line verbatim: "REVIEW: CLEAR - read-only line (reads four files, no db opened, no tee, no write, no `!`, no grep); every expected figure is a read-out, not a gate, and the traceable ones trace to code". Expected: before = dry, same sha (2,606 lines — the 8B3b block printed "header receipt on PA before: 2606 lines"); apply likely shorter (cmp "EOF on greek_header_split_apply.txt …"); repo receipt = the apply copy unless the cp itself was cut short.

## Reviewer config (11/7, ruling chat)

`.claude/agents/reviewer.md`: the `model: fable` line removed — the reviewer subagent now runs on the session's
model; `effort: low` unchanged. Config-only commit `395c52bd`.

### RCPT8B3C ran (11/7, 20:03 UTC) — NOT truncated: same size, different content

before = dry: 2,606 lines, 182,942 bytes, sha 59dac6f7…, cmp silent. apply = PA repo receipt: 2,606 lines,
182,942 bytes, sha 0051be4c… (the copy is complete — cp was not cut short). cmp dry vs apply: "differ: char 20408,
line 290"; the apply copy ends on the normal last line ("# breathing repairs …"). **The ruling chat's quota-truncation
reading does not fit** — the two receipts have identical length and different bytes. Likely cause (hypothesis, not
verified): the receipt lists each name's forms sorted by count only (`build_pn_greek_identity.py:521`), so tied forms
print in the order the rows came out of the db (`:374-383`), which can differ between the throwaway dry copy and
built. The identity table itself is identical (8B3CX: built = dry copy, 0 differences). Not recorded as DONE yet:
read-only line RDIFF8B3C below first.

### Line RDIFF8B3C (read-only; what differs between the dry and apply receipts)

Reviewer subagent (11/7), verdict line verbatim: "REVIEW: CLEAR - read-only line: it only reads two run-artifact text files, uses no db, writes nothing, has no `!`, and its field split matches the writer at build_pn_greek_identity.py:523". Expected if the hypothesis holds: the diff shows reordered forms from line ~290; "differing as written" ≥ 1; fields 1–5 (name / class / occurrences / headword / morph count — the member-list content) 0; after putting each form list in one fixed order 0. Any non-zero in the last two = a finding for the ruling chat (STILL DIFFERS lines list it). Tested locally on made-up receipts: a reorder reads 1 / 0 / 0; a class change reads STILL DIFFERS.

### RDIFF8B3C ran (11/7, 20:06 UTC) — the receipts differ only in the order of tied forms

9 of 2,606 lines differ (290 ashkelon, 429 belial, 456 bethanath, 1136 ibleam, 1500 kirjatharba, 1903 ophrah, 2052
rehob, 2353 taanach, 2508 zaphon); every one is the same forms with the same counts listed in a different order among
equal counts. **Fields 1–5 (name / class / occurrences / headword / morph count) differ on 0 lines; with each form list
put in one fixed order, 0 lines differ.** So the hypothesis holds (`build_pn_greek_identity.py:521` sorts by count
only; ties follow db row order, which differs between the throwaway dry copy and built). The header member list is
identical. Receipt of record = the dry copy (`pn8b3c_20261107/greek_header_split_dry.txt`, 2,606 lines, sha
59dac6f7…); PA's repo receipt now holds the apply version (sha 0051be4c…) — generated, untracked, display order only.

## 8B3c DONE — ACCEPTED (11/7, ruling chat) → built = 8b.0 + REKEY + 8b.1 + §9.96 + 8b.2 + 8b.2a + 8b.3

Under §9.97 / §9.98: identity = the 58 declared rows (split 3,671 / 10,246 / 12,216 / 4,382 / 1,963); slot table =
the 4 jehoram → joram names; tipnr tables unchanged; pn_binding 15,446 → 15,426 (added 70 / removed 90). **Gate 2's
pn_binding declared input = `~/edition_upgrade_runs/pn8b3c_20261107/pn_binding_delta_after.tsv` (160 rows)** — it
replaces `pn_binding {"identical": true}` in `declared_deltas.json` (§9.98 b). Gate B changed_rows come from the 58 in
`pn8b3_20261107/identity_delta.tsv` (sha 62a99ffe…, §9.97). **Next session:** the gate 2 dump
(`scripts/eu_pn_binding_diff.py <src> <built>`, read-only) and the first gate 2 run (`gate_greek_header.py --declared`,
read-only, expected to FAIL per §9.92), each through the reviewer. Handoff: `HANDOFF_edition_upgrade_gate2.md`.

## Stage E opened (11/8): the shared step script `scripts/eu_step.py` — APPROVED (DESIGN §9.106), code REF `006e16ba`

Ruled "after stage D" (ruling chat): the one-off helper pattern (8B2A / 8B3 / 8B3b / 8B3c / SLOT3:
a ~500-line helper pasted as a heredoc, sha-checked, then prep / dry / delta / apply / check) becomes ONE committed
script. Approved 11/8 (§9.106) and pushed as `006e16ba`: `scripts/eu_step.py` + `tests/test_eu_step.py` (14 cases;
ci.yml + pre-commit lists). The block's REF guard now pins the script like any other — no pasted helper, no helper sha (lesson 19:
long heredocs arrive garbled through the PA console).

Five modes; each ends on one line `<TAG> <MODE>: OK` or `<TAG> <MODE>: STOP - why` (check: FAIL); the block keeps
the RESULT line. It never writes the db it checks.
- **pre** — repo guards in the 11/6 order (REF pulled → ancestor of HEAD → scripts/tests = REF → nothing
  uncommitted); each `--db` present, no `-journal` (checked before opening), triggers 0; each `--keep` rollback copy
  present; the run folder must not exist, made last.
- **prep** — read-only on built: `state.json` = every ordinary table's row count + an order-free content digest
  (sum of sha256 per row) + the whole schema (virtual tables listed, their shadow tables digested); `before.db` =
  each `--save` table, or row id + named columns (a restore source); `dry.db` = the THROWAWAY copy of each `--copy`
  table with its indexes and row ids; each copied table proven = built's by digest.
- **same** — built's schema + every table's digest = `state.json` (built untouched since prep).
- **delta** — row-level differences a → b on named tables, ALL written to a TSV (no cap) + its sha256, printed per
  table (counts, by changed column, NULL→value / value→NULL / value→other value) + first N. Key = row id by default
  or named columns (then rows are counted per distinct value, so a duplicated row is a difference). Every text
  compare is byte-exact (`COLLATE BINARY`; a NOCASE column can't hide a case-only change). `--zero`, `--expect-sha`.
- **check** — after the apply: every table NOT in `--written` = its prep digest (schema too); each written table =
  the dry copy's (digest; on a mismatch the row-level file is written and the first 40 printed); written tables'
  schema = the dry copy's; no `-journal`; scripts/tests clean.

What stays in the block: the step's own builder command, its log, the step-specific read-outs and the declared
figures. The apply block (a WRITE: ruling chat) = pre (new folder) → `same` against the dry folder → the builder on
built → `check --written …` against the dry folder → the dry delta re-read by sha.

### Block STEP11-DRY (GATE REF 006e16ba; READ-ONLY on built — writes only the run folder and its throwaway copy)

Rebuild-words step 11 (`build_rendering_norm.py`, fills `words.english_head_norm` + kjv/bsb `word_norm`) on a
throwaway copy of the three tables it touches. Goes to the reviewer (§9.106 ask 2); nothing runs on PA until it
CLEARs. PA pulls first (`cd ~/bible-db && git pull`). Expected: pre/prep/same OK; the builder exits 0 with no "not
present" line; the delta is a READ-OUT (figures declared from this log for the apply block) — same-code expectation
kjv_words / bsb_words changed 0; words: only `english_head_norm` changes, no row added or removed.
**Unknowns until PA runs it (no estimates):** (1) the size of the throwaway copy `dry.db` (three full tables + their
indexes; prep prints it — the PA home quota was hit once on 11/7); (2) how long the whole-db fingerprint takes (prep
and `same` each fingerprint every table of built; prep prints its time).

```bash
set +H
L=~/edition_upgrade_runs/step11dry_20261108.log
if [ -e "$L" ]; then echo "STEP11-DRY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP11-DRY rebuild-words step 11 (build_rendering_norm) on a THROWAWAY copy of words/kjv_words/bsb_words - built read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || exit 1
[ -f scripts/eu_step.py ] || { echo "STEP11-DRY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
D=~/edition_upgrade_runs/step11dry_20261108
E="python3 scripts/eu_step.py"
$E pre --tag STEP11 --ref "$REF" --dir "$D" --db "$B" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP11-DRY RESULT: STOP - pre (line above); nothing made"; exit 1; }
$E prep --tag STEP11 --built "$B" --dir "$D" --copy words,kjv_words,bsb_words --save words:english_head_norm --save kjv_words:word_norm --save bsb_words:word_norm || { echo "STEP11-DRY RESULT: STOP - prep (line above); built untouched"; exit 1; }
echo "--- words on built (read-only): rows | english_head non-blank | english_head_norm filled | norm on a blank head"
sqlite3 -readonly "$B" "SELECT count(*), sum(english_head IS NOT NULL AND english_head <> ''), sum(english_head_norm IS NOT NULL), sum((english_head IS NULL OR english_head = '') AND english_head_norm IS NOT NULL) FROM words"
echo "--- the norm column + the three norm indexes on built:"
sqlite3 -readonly "$B" "SELECT 'column', name FROM pragma_table_info('words') WHERE name = 'english_head_norm'; SELECT 'index', name FROM sqlite_master WHERE type = 'index' AND name IN ('idx_words_ehnorm', 'idx_kjvwords_norm', 'idx_bsbwords_norm') ORDER BY name"
echo "=== DRY RUN: build_rendering_norm on the throwaway copy $D/dry.db (built untouched) ==="
DRY=$(python3 scripts/build_rendering_norm.py "$D/dry.db" 2>&1); r=$?
printf '%s\n' "$DRY" > "$D/dry_norm.log"
echo "$DRY"
echo "exit $r (expect 0)"
[ "$r" -eq 0 ] || { echo "STEP11-DRY RESULT: STOP - the builder failed on the copy (above); built untouched"; exit 1; }
if grep -q "not present" <<< "$DRY"; then echo "STEP11-DRY RESULT: STOP - the builder skipped a table on the copy; built untouched"; exit 1; fi
echo "--- words on the dry copy after: rows | english_head non-blank | english_head_norm filled | norm on a blank head"
sqlite3 -readonly "$D/dry.db" "SELECT count(*), sum(english_head IS NOT NULL AND english_head <> ''), sum(english_head_norm IS NOT NULL), sum((english_head IS NULL OR english_head = '') AND english_head_norm IS NOT NULL) FROM words"
$E delta --tag STEP11 --a "$B" --b "$D/dry.db" --table words --table kjv_words --table bsb_words --out "$D/step11_delta.tsv" || { echo "STEP11-DRY RESULT: STOP - delta (line above); built untouched"; exit 1; }
$E same --tag STEP11 --built "$B" --dir "$D" || { echo "STEP11-DRY RESULT: STOP - built differs from its prep state (lines above)"; exit 1; }
echo "STEP11-DRY RESULT: READ DONE - built untouched (same: OK); the delta above + $D/step11_delta.tsv (sha on the DELTA line) are the figures to declare for the apply block"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP11-DRY reviewed (11/8) — REVIEW: CLEAR

Reviewer subagent (11/8), verdict line verbatim: "REVIEW: CLEAR - read-only on built (every open of built is mode=ro or sqlite3 -readonly; the builder only touches $D/dry.db); the gate is ruled in §9.106 at REF 006e16ba; the only things it writes are run artifacts in a new folder, with guards against overwriting."
Its notes for the ruling chat (none blocks the CLEAR): (1) git guards now run inside `eu_step.py pre`, accepted as the
§9.106 replacement; (2) `cd ~/bible-db || exit 1` is the one failure path with no RESULT line (`exit=1` still shows);
(3) `build_rendering_norm.py` imports `number_fold.py` from the repo root, outside the guarded `scripts tests` paths —
**the apply block should guard `number_fold.py` too** (its declared figures depend on it); (4) the two unknowns carried
as stated. Next: JP runs it on PA after `cd ~/bible-db && git pull`; the log comes back for the declaration.
