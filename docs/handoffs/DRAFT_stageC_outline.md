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
