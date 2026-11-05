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
