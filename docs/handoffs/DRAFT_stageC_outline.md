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
