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

### STEP11-DRY ran (11/8, 16:21 UTC, PA HEAD b3178672) — READ DONE, exit 0; built untouched

Log `~/edition_upgrade_runs/step11dry_20261108.log`, folder `step11dry_20261108/`. pre OK (REF 006e16ba); prep OK —
**state.json: 150 tables, 3,809,451 rows, 300 schema entries, 53 s** (no virtual tables); before.db 24,555,520 bytes;
**dry.db 191,848,448 bytes** (the two §9.106 unknowns, now read); each copied table = built's by digest (words
6e069522…, kjv_words 3a944d6d…, bsb_words 0f278f0d…). Built before: words 626,309 · english_head non-blank 353,595 ·
norm filled 0 · norm on a blank head 0; column + all three norm indexes present (no "added column" line). Builder
on the copy: exit 0, recomputed 353,595 / 790,685 / 386,063; distinct renderings → keys words 12,740 → 10,979, kjv
13,826 → 11,296, bsb 100,241 → 89,295 (read-out). Dry copy after: 626,309 · 353,595 · 353,595 · 0. **Delta:** words
changed 353,595 (every one `english_head_norm` NULL → value, no other column), added 0, removed 0; kjv_words 0;
bsb_words 0 — the stated expectation, met. `step11_delta.tsv` 353,595 lines + header, sha256
**5bfe6d3819ab6685ba56dde7b6b66b296e1717450f8d6d8f59f3152914b56d44**. same OK (150 tables + schema, 0 differences).

**Declared figures for STEP11-APPLY (each from that log):** builder output after its first line = the dry run's
(`dry_norm.log`); words read after = `626309|353595|353595|0`; check OK with `--written words,kjv_words,bsb_words`
against the dry folder (unwritten 147 tables + schema = prep, written tables = the dry copy); the dry delta file
still hashes 5bfe6d38….

**Read-out against the last run (not a step-11 figure):** the 10/25 live run normed **354,946** words
(`CHARTER_rebuild_trap_fix.md:528-546`); built has **353,595** non-blank heads — **1,351 fewer**. Step 11 only
derives from `english_head`, so the gap is the edition's English, not this step; no record in the repo attributes
it. CC proposes STEP11-HEADS (read-only, below) to list every row behind it. It does not change any STEP11-APPLY
figure (re-running step 11 after any later English fix just recomputes the column).

### Block STEP11-HEADS (READ-ONLY on src and built — writes one list file + its log; no REF needed: no repo code)

Every `(verse_id, position)` whose english_head is non-blank on one copy and blank on the other, or whose row exists on
one side only. src = `bible_edupg_test_20261101.db` (fresh copy of live, 11/01). Expected: duplicate keys 0 on both
(else STOP); each count read must succeed and be a number (else STOP); src non-blank heads printed (10/25 live: 354,946 — a read-out, src is the 11/01 copy); built must be 353,595 (the STEP11-DRY figure; else STOP);
**lost − gained + src-only-with-head − built-only-with-head = src non-blank − 353,595** (printed; must hold, else the
read is wrong). Classes, list file and breakdowns are READ-OUTS for the ruling chat.

```bash
set +H
L=~/edition_upgrade_runs/step11heads_20261108.log
if [ -e "$L" ]; then echo "STEP11-HEADS RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
echo "STEP11-HEADS (read-only) - english_head non-blank on src vs built: every row behind the 1,351 - $(date -u +%FT%TZ)"
S=~/bible-db/bible_edupg_test_20261101.db
B=~/bible-db/bible_edupg_test_built_20261102.db
O=~/edition_upgrade_runs/step11heads_20261108.tsv
[ -e "$O" ] && { echo "STEP11-HEADS RESULT: STOP - list file already exists: $O"; exit 1; }
for f in "$S" "$B"; do [ -s "$f" ] || { echo "STEP11-HEADS RESULT: STOP - missing: $f"; exit 1; }; [ -e "$f-journal" ] && { echo "STEP11-HEADS RESULT: STOP - $f-journal present (move it aside, never delete)"; exit 1; }; done
NB="(english_head IS NOT NULL AND english_head <> '')"
HS="(s.english_head IS NOT NULL AND s.english_head <> '')"
HT="(t.english_head IS NOT NULL AND t.english_head <> '')"
for f in "$S" "$B"; do
  d=$(sqlite3 -readonly "$f" "SELECT count(*) FROM (SELECT 1 FROM words GROUP BY verse_id, position HAVING count(*) > 1)") || { echo "STEP11-HEADS RESULT: STOP - read failed on $f"; exit 1; }
  echo "duplicate (verse_id, position) keys in $f: $d (expect 0)"
  [ "$d" = "0" ] || { echo "STEP11-HEADS RESULT: STOP - duplicate keys; the row match below would double-count"; exit 1; }
done
NS=$(sqlite3 -readonly "$S" "SELECT sum($NB) FROM words") || { echo "STEP11-HEADS RESULT: STOP - the src count read failed"; exit 1; }
NT=$(sqlite3 -readonly "$B" "SELECT sum($NB) FROM words") || { echo "STEP11-HEADS RESULT: STOP - the built count read failed"; exit 1; }
case "$NS" in ''|*[^0-9]*) echo "STEP11-HEADS RESULT: STOP - the src count is not a number: '$NS'"; exit 1;; esac
case "$NT" in ''|*[^0-9]*) echo "STEP11-HEADS RESULT: STOP - the built count is not a number: '$NT'"; exit 1;; esac
echo "words with a non-blank english_head: src $NS (10/25 live: 354946; read-out) - built $NT (expect 353595) - difference $((NS - NT))"
[ "$NT" = "353595" ] || { echo "STEP11-HEADS RESULT: STOP - built is not the STEP11-DRY figure 353595"; exit 1; }
Q="SELECT v.book, v.chapter, v.verse, s.position, CASE WHEN t.verse_id IS NULL THEN CASE WHEN $HS THEN 'src-only row, head' ELSE 'src-only row, blank' END WHEN $HS AND NOT $HT THEN 'lost' WHEN NOT $HS AND $HT THEN 'gained' END AS cls, s.english, s.english_head, t.english, t.english_head FROM main.words s JOIN main.verses v ON v.id = s.verse_id LEFT JOIN b.words t ON t.verse_id = s.verse_id AND t.position = s.position WHERE cls IS NOT NULL UNION ALL SELECT v.book, v.chapter, v.verse, t.position, CASE WHEN $HT THEN 'built-only row, head' ELSE 'built-only row, blank' END, NULL, NULL, t.english, t.english_head FROM b.words t JOIN b.verses v ON v.id = t.verse_id WHERE NOT EXISTS (SELECT 1 FROM main.words s WHERE s.verse_id = t.verse_id AND s.position = t.position) ORDER BY 1, 2, 3, 4"
sqlite3 -readonly -cmd '.mode tabs' "$S" "ATTACH 'file:$B?mode=ro' AS b; $Q" > "$O" || { echo "STEP11-HEADS RESULT: STOP - the row match failed"; exit 1; }
echo "list: $O - $(wc -l < "$O") rows (book, chapter, verse, position, class, src english, src head, built english, built head) - sha256 $(sha256sum < "$O" | cut -c1-16)..."
echo "--- by class:"
cut -f5 "$O" | sort | uniq -c
NET=$(awk -F'\t' '$5=="lost"||$5=="src-only row, head"{n++} $5=="gained"||$5=="built-only row, head"{n--} END{print n+0}' "$O")
echo "lost - gained + src-only with head - built-only with head = $NET (must = $((NS - NT)))"
[ "$NET" = "$((NS - NT))" ] || { echo "STEP11-HEADS RESULT: STOP - the classes do not add up to the difference; the read is wrong"; exit 1; }
echo "--- 'lost': top 25 built english (what the row reads now) | count"
awk -F'\t' '$5=="lost"{print $8}' "$O" | sort | uniq -c | sort -rn | head -25
echo "--- 'lost': top 25 src heads (what it read before) | count"
awk -F'\t' '$5=="lost"{print $7}' "$O" | sort | uniq -c | sort -rn | head -25
echo "--- first 40 rows:"
head -40 "$O"
echo "STEP11-HEADS RESULT: READ DONE - every row behind the difference is in $O"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### Block STEP11-APPLY (GATE REF 006e16ba; WRITES built: words.english_head_norm + kjv/bsb word_norm) — for the ruling chat

The builder on built, gated on the STEP11-DRY figures above. Order: guards (the reviewer's note 3: `number_fold.py`
= REF and unedited, since the builder imports it; note 2: the `cd` failure now prints a RESULT line) → pre (new
folder `step11apply_20261108`) → the dry delta file still = the declared sha + line count → `same` against the dry
folder (built unchanged since the dry run) → built read before = `626309|353595|0|0` → **the one write** (the
builder on built) → its output after the first line = the dry run's → built read after = `626309|353595|353595|0` →
`check --written words,kjv_words,bsb_words` against the dry folder (147 unwritten tables + schema = prep; the three
written tables = the dry copy). Before the write, any miss = STOP, built untouched. After it, a miss = CHECK, with the
restore source `step11dry_20261108/before.db` (row id + the three norm columns as they were). The builder's own write
is all-or-nothing (the three updates are saved once, at `build_rendering_norm.py:110`; column + indexes already exist on built, so no other change).

```bash
set +H
L=~/edition_upgrade_runs/step11apply_20261108.log
if [ -e "$L" ]; then echo "STEP11-APPLY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP11-APPLY rebuild-words step 11 (build_rendering_norm) on BUILT, gated on the STEP11-DRY figures - WRITES built: words.english_head_norm (353,595 rows), kjv/bsb word_norm (same values) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP11-APPLY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP11-APPLY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
git diff --quiet "$REF" HEAD -- number_fold.py || { echo "STEP11-APPLY RESULT: STOP - number_fold.py differs from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- number_fold.py)" ] || { echo "STEP11-APPLY RESULT: STOP - number_fold.py has uncommitted edits on PA"; exit 1; }
echo "number_fold.py (the builder's import) = $REF, unedited: OK"
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
DD=~/edition_upgrade_runs/step11dry_20261108
D=~/edition_upgrade_runs/step11apply_20261108
E="python3 scripts/eu_step.py"
$E pre --tag STEP11A --ref "$REF" --dir "$D" --db "$B" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP11-APPLY RESULT: STOP - pre (line above); built untouched"; exit 1; }
for f in state.json before.db dry.db dry_norm.log step11_delta.tsv; do [ -s "$DD/$f" ] || { echo "STEP11-APPLY RESULT: STOP - the dry run's $f is missing or empty in $DD; built untouched"; exit 1; }; done
DS=$(sha256sum < "$DD/step11_delta.tsv" | cut -d' ' -f1); DN=$(wc -l < "$DD/step11_delta.tsv")
echo "dry delta file: $DN lines (expect 353596 = header + 353595), sha256 $DS (expect 5bfe6d3819ab6685ba56dde7b6b66b296e1717450f8d6d8f59f3152914b56d44)"
[ "$DS" = 5bfe6d3819ab6685ba56dde7b6b66b296e1717450f8d6d8f59f3152914b56d44 ] && [ "$DN" = "353596" ] || { echo "STEP11-APPLY RESULT: STOP - the dry delta file is not the declared one; built untouched"; exit 1; }
$E same --tag STEP11A --built "$B" --dir "$DD" || { echo "STEP11-APPLY RESULT: STOP - built changed since the dry run (lines above); built untouched"; exit 1; }
RD="SELECT count(*), sum(english_head IS NOT NULL AND english_head <> ''), sum(english_head_norm IS NOT NULL), sum((english_head IS NULL OR english_head = '') AND english_head_norm IS NOT NULL) FROM words"
W0=$(sqlite3 -readonly "$B" "$RD")
echo "words on built before: $W0 (expect 626309|353595|0|0)"
[ "$W0" = "626309|353595|0|0" ] || { echo "STEP11-APPLY RESULT: STOP - built's words read is not the dry run's before picture; built untouched"; exit 1; }
echo "=== APPLY: build_rendering_norm on built (the one write) ==="
OUT=$(python3 scripts/build_rendering_norm.py "$B" 2>&1); r=$?
printf '%s\n' "$OUT" > "$D/apply_norm.log"
echo "$OUT"
echo "exit $r (expect 0)"
SAMEOUT=NO; [ "$(sed 1d <<< "$OUT")" = "$(sed 1d "$DD/dry_norm.log")" ] && SAMEOUT=yes
echo "builder output after its first line = the dry run's: $SAMEOUT"
W1=$(sqlite3 -readonly "$B" "$RD")
echo "words on built after: $W1 (expect 626309|353595|353595|0)"
CHK=$($E check --tag STEP11A --built "$B" --dir "$DD" --written words,kjv_words,bsb_words 2>&1); k=$?
echo "$CHK"
if [ "$r" -eq 0 ] && [ "$SAMEOUT" = "yes" ] && [ "$W1" = "626309|353595|353595|0" ] && [ "$k" -eq 0 ]; then
  echo "STEP11-APPLY RESULT: DONE - built words.english_head_norm filled on the 353,595 rows with a head (none on a blank head), kjv/bsb word_norm unchanged, built = the dry run on the three tables, the other 147 tables + schema unchanged"; exit 0
fi
echo "STEP11-APPLY RESULT: CHECK - an after-figure differs (lines above). Restore source for the three norm columns: $DD/before.db"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP11-HEADS reviewed (11/8) — ESCALATE (mechanical) → fixed (`eb65843f`) → REVIEW: CLEAR

First pass: ESCALATE — the two count reads had no STOP on failure. Fixed per the reviewer's own suggestion (STOP on a
failed read, number check, built 353,595 made a gate); re-tested on a fake home. Second pass, verdict line verbatim:
"REVIEW: CLEAR - read-only block (scope a): both dbs are opened read-only, it runs no repo code, and its only outputs are two run artifacts that are guarded against overwriting. The fix I asked for is in, and every failure path now ends in one STOP line."
Non-blocking note: the `NET=$(awk …)` line has no own failure check; a failed awk still STOPs on the next line's sum.
STEP11-APPLY (a write) stays with the ruling chat.

### STEP11-HEADS ran (11/8, 16:58 UTC) — READ DONE, exit 0 → OPEN edition item "heads gap" (DESIGN §9.107)

Log `~/edition_upgrade_runs/step11heads_20261108.log`; list `step11heads_20261108.tsv` (2,031 rows, sha256
7a5511e9f61e1bfb…). Duplicate keys 0 / 0. Non-blank english_head: src 354,946 · built 353,595 · difference 1,351.
Classes: lost 1,691 · gained 340 · src-only 0 · built-only 0 (same row set on both sides); 1,691 − 340 = 1,351.
Of the 1,691 lost, 1,299 have a blank built english; top src heads lost: "one" 481, "ones" 425, "because" 99,
"know" 63. **No cause asserted.** OPEN under §9.107 ruling 2: a separate edition item, not a step-11 figure; stays
open until read and explained from the rows. Next read on it = CC's, drafted from the tsv (the 1,299 blank-english
lost rows and the 340 gained). STEP11-APPLY does not wait on it (§9.107 ruling 1).

### STEP11-APPLY ran (11/8, 17:28 UTC, PA HEAD b3178672, REF 006e16ba) — DONE, exit 0 → STEP 11 CLOSED on built

Cleared by the ruling chat under §9.107 on reviewer ESCALATE (write; `pre` covers the standard git checks). Log
`~/edition_upgrade_runs/step11apply_20261108.log`, folder `step11apply_20261108/`. Every declared figure met:
number_fold.py = REF, unedited; PRE OK; dry delta 353,596 lines, sha 5bfe6d38… = declared; SAME OK (150 tables +
schema, 0 differences); words before `626309|353595|0|0`; builder exit 0, recomputed 353,595 / 790,685 / 386,063,
output after line 1 = the dry run's; words after `626309|353595|353595|0`; CHECK OK — 147 unwritten tables + schema
0 differences; written tables = the dry copy: words 23ef2493a195 (prep 6e0695228b73), kjv_words 3a944d6da8a0 and
bsb_words 0f278f0d9da2 (= prep, unchanged); no journal; scripts/tests clean. Restore source if ever needed:
`step11dry_20261108/before.db`. **Built = … + SLOT3 + step 11.** Still open: the heads gap (§9.107 ruling 2) —
unchanged by this apply. Housekeeping once stage E no longer needs it: `step11dry_20261108/dry.db` (~192 MB).

## Step 10 (two-ending read) on built — STEP10-READ drafted (11/8)

Rebuild-words step 10 (`.claude/commands/rebuild-words.md:322-330`; order §9.105): `scripts/build_two_ending.py
<built>` opens the db READ-ONLY (`build_two_ending.py:71`, `mode=ro`) and reads only `words.strongs_base` +
`words.morph`, `lsj`, `lexicon`; it prints a header + the JS soften-lists. Its output from the `// AUTO-GENERATED`
line down is compared byte for byte with `static/src/00b-two-ending.jsx` (pinned to REF in the block). IDENTICAL →
step 10 "unchanged" (no paste, no build). DIFFERENT → the diff goes to the ruling chat (a paste + `npm run build` +
push must land before step 8). 10/25 live (read-out, `CHARTER_rebuild_trap_fix.md:575-579`): IDENTICAL; header
classes two-ending 368 · three-ending 283 · no-lsj 41 · noun 68 · unknown 13; soften OT 80 words / 441 displays ·
NT 208 / 396. Edition upgrade changes English (morph is not in scope), but 8b.2 rewrote `strongs_base`, so the
lists are not asserted: IDENTICAL or DIFFERENT is the read-out.

### Block STEP10-READ (GATE REF 006e16ba; READ-ONLY on built — writes only its run folder + log)

```bash
set +H
L=~/edition_upgrade_runs/step10read_20261108.log
if [ -e "$L" ]; then echo "STEP10-READ RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP10-READ rebuild-words step 10 (build_two_ending, read-only) on built, output vs static/src/00b-two-ending.jsx - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP10-READ RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP10-READ RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
D=~/edition_upgrade_runs/step10read_20261108
J=static/src/00b-two-ending.jsx
python3 scripts/eu_step.py pre --tag STEP10 --ref "$REF" --dir "$D" --db "$B" || { echo "STEP10-READ RESULT: STOP - pre (line above); nothing read"; exit 1; }
git diff --quiet "$REF" HEAD -- "$J" || { echo "STEP10-READ RESULT: STOP - $J differs from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- "$J")" ] || { echo "STEP10-READ RESULT: STOP - $J has uncommitted edits on PA"; exit 1; }
echo "$J (the comparison target) = $REF, unedited: OK - $(wc -l < "$J") lines, sha256 $(sha256sum < "$J" | cut -c1-16)..."
python3 scripts/build_two_ending.py "$B" > "$D/two_ending.out" 2> "$D/two_ending.err"; r=$?
echo "exit $r (expect 0) - stderr lines: $(wc -l < "$D/two_ending.err") (expect 0)"
cat "$D/two_ending.err"
[ "$r" -eq 0 ] || { echo "STEP10-READ RESULT: STOP - the builder failed (above)"; exit 1; }
echo "--- header (10/25 live: two-ending 368, three-ending 283, no-lsj 41, noun 68, unknown 13; soften OT 80 / 441, NT 208 / 396):"
sed -n '1,2p' "$D/two_ending.out"
sed -n '/^\/\/ AUTO-GENERATED/,$p' "$D/two_ending.out" > "$D/two_ending_block.jsx"
[ -s "$D/two_ending_block.jsx" ] || { echo "STEP10-READ RESULT: STOP - no AUTO-GENERATED line in the output"; exit 1; }
echo "generated block: $(wc -l < "$D/two_ending_block.jsx") lines, sha256 $(sha256sum < "$D/two_ending_block.jsx" | cut -c1-16)..."
if cmp -s "$D/two_ending_block.jsx" "$J"; then
  echo "STEP10-READ RESULT: READ DONE - IDENTICAL to $J: step 10 unchanged, no paste, no build"; exit 0
fi
echo "--- DIFFERENT: diff $J (left) vs the generated block (right):"
diff "$J" "$D/two_ending_block.jsx"
echo "STEP10-READ RESULT: READ DONE - DIFFERENT from $J (diff above; full output $D/two_ending.out) - for the ruling chat"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP10-READ reviewed (11/8) — REVIEW: CLEAR

Reviewer subagent (11/8), verdict line verbatim: "REVIEW: CLEAR - read-only block (the builder opens the db with mode=ro and only prints); writes go only to a new run folder and a guarded dated log; the REF gate is covered by eu_step pre as accepted at §9.106/§9.107"
Goes straight to PA (read-only). IDENTICAL → step 10 closed "unchanged"; DIFFERENT → the diff goes to the ruling chat.

### STEP10-READ ran (11/8, 18:03 UTC, PA HEAD b3178672, REF 006e16ba) — IDENTICAL → STEP 10 CLOSED "unchanged" (§9.108)

Log `~/edition_upgrade_runs/step10read_20261108.log`. PRE OK; target `00b-two-ending.jsx` = REF, 33 lines, sha256
abdedc13e9f8b35f…; builder exit 0, 0 stderr lines; header = the 10/25 live figures exactly (two-ending 368 ·
three-ending 283 · no-lsj 41 · noun 68 · unknown 13; soften OT 80 / 441 · NT 208 / 396); generated block 33 lines,
same sha → IDENTICAL. No paste, no site build. Observed, no ruling: built reads 451,993,600 bytes in PRE (451,964,928
before the step-11 apply). Next: step 12a (`dotted_lexicon`).

## Step 12a (`dotted_lexicon`) on built — STEP12A-DRY drafted (11/8)

Procedure `rebuild-words.md:355-359` + the step-12 rulings (`DRAFT_rebuild_words_side_tables.md`, Q5: dry on built →
figures declared from that log by path:line → `--apply` gated on them). `build_dotted_lexicon.py <db>` opens ONLY the
path given (`:183-192`, refuses with none), reads `words` (dotted `strongs`), `lexicon`, `abp_ext` + the code-pinned
overrides (`:42-80`), and with `--apply` DROPs + re-CREATEs `dotted_lexicon` only (`:234-242`). Its imports
(`audit_dotted_lemmas`, `build_abp_translit`) open no db at import (connect only inside their own `main()`).
**Dry form:** the builder's `--diff` (keys only, the procedure's read-out) AND its `--apply`, both on a THROWAWAY copy
of the four tables it reads (eu_step prep), then a row-level delta keyed on `strongs` (keys AND lemma/translit
values; rowids change on a re-create, so the row id is not the key) — built → dry and src → dry (the procedure's
"values check vs `<src>`"). Same-code expectation: `+0 / -0`, delta 0 both ways. Edition upgrade: every difference is
a member to read before any apply — the figures are READ-OUTS. Also read out: the table's definition (CREATE line +
any index) on built, src and the dry copy — a DROP loses any index PA added outside git, and `check` compares the
written table's definition only with the dry copy, so this read-out is where a lost index would show.

### Block STEP12A-DRY (GATE REF 006e16ba; READ-ONLY on built and src — writes only the run folder and its throwaway copy)

```bash
set +H
L=~/edition_upgrade_runs/step12a_dry_20261108.log
if [ -e "$L" ]; then echo "STEP12A-DRY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12A-DRY rebuild-words step 12a (build_dotted_lexicon --diff + --apply) on a THROWAWAY copy of words/lexicon/abp_ext/dotted_lexicon - built and src read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12A-DRY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP12A-DRY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
D=~/edition_upgrade_runs/step12a_dry_20261108
E="python3 scripts/eu_step.py"
$E pre --tag STEP12A --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP12A-DRY RESULT: STOP - pre (line above); nothing made"; exit 1; }
for f in "$B" "$S"; do
  echo "--- dotted_lexicon on $f (read-only): definition + row count"
  sqlite3 -readonly "$f" "SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'dotted_lexicon' ORDER BY type, name; SELECT 'rows', count(*) FROM dotted_lexicon" || { echo "STEP12A-DRY RESULT: STOP - dotted_lexicon read failed on $f"; exit 1; }
done
$E prep --tag STEP12A --built "$B" --dir "$D" --copy words,lexicon,abp_ext,dotted_lexicon --save dotted_lexicon || { echo "STEP12A-DRY RESULT: STOP - prep (line above); built untouched"; exit 1; }
echo "=== DRY 1: --diff on the throwaway copy (keys only; the procedure's read-out) ==="
python3 scripts/build_dotted_lexicon.py "$D/dry.db" --diff > "$D/diff.out" 2>&1; r=$?
echo "exit $r (expect 0) - full output $D/diff.out ($(wc -l < "$D/diff.out") lines); first 3 lines, then the REMOVED section (first 40):"
head -3 "$D/diff.out"
sed -n '/^REMOVED/,$p' "$D/diff.out" | head -40
[ "$r" -eq 0 ] || { echo "STEP12A-DRY RESULT: STOP - --diff failed on the copy (above); built untouched"; exit 1; }
echo "=== DRY 2: --apply on the throwaway copy $D/dry.db (built untouched) ==="
AP=$(python3 scripts/build_dotted_lexicon.py "$D/dry.db" --apply 2>&1); a=$?
printf '%s\n' "$AP" > "$D/apply_dry.log"
echo "$AP"
echo "exit $a (expect 0)"
[ "$a" -eq 0 ] || { echo "STEP12A-DRY RESULT: STOP - --apply failed on the copy (above); built untouched"; exit 1; }
grep -q "^Filled dotted_lexicon in " <<< "$AP" || { echo "STEP12A-DRY RESULT: STOP - --apply did not report a fill; built untouched"; exit 1; }
echo "--- dotted_lexicon on the dry copy after: definition + row count"
sqlite3 -readonly "$D/dry.db" "SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'dotted_lexicon' ORDER BY type, name; SELECT 'rows', count(*) FROM dotted_lexicon" || { echo "STEP12A-DRY RESULT: STOP - dotted_lexicon read failed on the dry copy; built untouched"; exit 1; }
$E delta --tag STEP12A --a "$B" --b "$D/dry.db" --table dotted_lexicon:strongs --out "$D/step12a_delta_built.tsv" || { echo "STEP12A-DRY RESULT: STOP - delta built -> dry (line above); built untouched"; exit 1; }
$E delta --tag STEP12A --a "$S" --b "$D/dry.db" --table dotted_lexicon:strongs --out "$D/step12a_delta_src.tsv" || { echo "STEP12A-DRY RESULT: STOP - delta src -> dry (line above); built untouched"; exit 1; }
$E same --tag STEP12A --built "$B" --dir "$D" || { echo "STEP12A-DRY RESULT: STOP - built differs from its prep state (lines above)"; exit 1; }
echo "STEP12A-DRY RESULT: READ DONE - built untouched (same: OK); the two deltas above (files + sha on their DELTA lines) and the --diff are the figures to declare for STEP12A-APPLY"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12A-DRY reviewed (11/8) — ESCALATE (mechanical) → fixed (`e8166ac5`) → REVIEW: CLEAR

First pass: ESCALATE — the dry-copy definition read had no STOP clause. Fixed exactly as asked. Second pass, verdict
line verbatim: "REVIEW: CLEAR - the block only reads built and src; both builder runs hit only the throwaway dry.db; every failure path now ends in one STOP line; the gate guards are in eu_step `pre` as accepted at §9.106/§9.107; no figure is asserted beyond code-traced status lines."
Goes straight to PA (read-only). Unknown until it runs: the dry copy's size (full words + lexicon + abp_ext +
dotted_lexicon; step 11's 192 MB `dry.db` is still on PA).

### STEP12A-DRY ran (11/8, 18:34 UTC, PA HEAD b3178672, REF 006e16ba) — READ DONE, exit 0; built untouched; IDENTICAL

Log `~/edition_upgrade_runs/step12a_dry_20261108.log`. PRE OK (built 451,993,600 B; src 451,964,928 B).
`dotted_lexicon` on built and src: same definition (`CREATE TABLE dotted_lexicon (strongs TEXT PRIMARY KEY, lemma
TEXT, translit TEXT)` + `sqlite_autoindex_dotted_lexicon_1`), 3,627 rows each. PREP OK: 150 tables / 3,809,451 rows
in 61 s; before.db 229,376 B; **dry.db 97,918,976 B**; the four copied tables = built (words 23ef2493a195, lexicon
123b3f07d776, abp_ext 8f9c30bc5f84, dotted_lexicon 9288508f98d4). `--diff`: +0 / −0; skipped buckets form_note 25 ·
no_entry 86 · unreadable 0 · already_ok 7; REMOVED none. `--apply` on the copy: "Filled … with 3627 corrected
headwords", exit 0; definition + 3,627 rows unchanged after. **Delta built → dry 0; src → dry 0** (both files header
only, sha256 c866c00363f6f49c3961768d3103b6833e1a1bcff3f2923a479309197e8619d6). SAME OK. Same-code expectation met.

**Apply or close? (ruling chat asked CC to read §9.105.)** §9.105 rules only the order ("11 → 10 → 12 → 9 → 9a → 9b →
9c per rebuild-words.md"). The procedure it points to prescribes the apply: `rebuild-words.md:351-354` "dry/trial →
figures DECLARED → `--apply` gated on the declared figures"; 12a `:355-359` "`--diff` → declare → `--apply` … Values
check after apply"; Q5 (11/7) the same. Step 12 has NO identical-skip clause (step 10 has one, `:326-327`). So read
as written, the apply runs; STEP12A-APPLY is drafted below, gated on these figures. An identical-skip for step 12
would be a new ruling.

### Block STEP12A-APPLY (GATE REF 006e16ba; WRITES built: dotted_lexicon only, DROP + re-CREATE, same 3,627 rows) — for the ruling chat

The builder's imports are both in `scripts/` (covered by `pre`); nothing at the repo root, so no extra file guard.
Order: guards → pre (new folder `step12a_apply_20261108`) → the dry folder's files present, both delta files =
header only, sha256 c866c003… → `same` against the dry folder → built read before = the dry log's definition + 3,627
rows → **the one write** (`--apply` on built) → its output = the dry run's line with built's path → built read after
= the same definition + 3,627 rows → `check --written dotted_lexicon` against the dry folder (149 unwritten tables +
schema = prep; dotted_lexicon = the dry copy) → the procedure's values check: delta src → built `--zero`. Before the
write, any miss = STOP, built untouched; after it, a miss = CHECK with restore source
`step12a_dry_20261108/before.db` (the whole table as it was).

```bash
set +H
L=~/edition_upgrade_runs/step12a_apply_20261108.log
if [ -e "$L" ]; then echo "STEP12A-APPLY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12A-APPLY rebuild-words step 12a (build_dotted_lexicon --apply) on BUILT, gated on the STEP12A-DRY figures - WRITES built: dotted_lexicon only (drop + re-create, 3,627 rows, identical to src) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12A-APPLY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP12A-APPLY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
DD=~/edition_upgrade_runs/step12a_dry_20261108
D=~/edition_upgrade_runs/step12a_apply_20261108
E="python3 scripts/eu_step.py"
$E pre --tag STEP12AA --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP12A-APPLY RESULT: STOP - pre (line above); built untouched"; exit 1; }
for f in state.json before.db dry.db apply_dry.log step12a_delta_built.tsv step12a_delta_src.tsv; do [ -s "$DD/$f" ] || { echo "STEP12A-APPLY RESULT: STOP - the dry run's $f is missing or empty in $DD; built untouched"; exit 1; }; done
for f in step12a_delta_built.tsv step12a_delta_src.tsv; do
  s=$(sha256sum < "$DD/$f" | cut -d' ' -f1); n=$(wc -l < "$DD/$f")
  echo "dry delta $f: $n line(s) (expect 1 = header only), sha256 $s (expect c866c00363f6f49c3961768d3103b6833e1a1bcff3f2923a479309197e8619d6)"
  [ "$s" = c866c00363f6f49c3961768d3103b6833e1a1bcff3f2923a479309197e8619d6 ] && [ "$n" = "1" ] || { echo "STEP12A-APPLY RESULT: STOP - $f is not the declared empty delta; built untouched"; exit 1; }
done
$E same --tag STEP12AA --built "$B" --dir "$DD" || { echo "STEP12A-APPLY RESULT: STOP - built changed since the dry run (lines above); built untouched"; exit 1; }
RD="SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'dotted_lexicon' ORDER BY type, name; SELECT 'rows', count(*) FROM dotted_lexicon"
EXPD=$(printf '%s\n' "index|sqlite_autoindex_dotted_lexicon_1|" "table|dotted_lexicon|CREATE TABLE dotted_lexicon (strongs TEXT PRIMARY KEY, lemma TEXT, translit TEXT)" "rows|3627")
R0=$(sqlite3 -readonly "$B" "$RD") || { echo "STEP12A-APPLY RESULT: STOP - read before failed; built untouched"; exit 1; }
echo "dotted_lexicon on built before:"; echo "$R0"
[ "$R0" = "$EXPD" ] || { echo "STEP12A-APPLY RESULT: STOP - built's dotted_lexicon is not the dry log's picture (definition + 3627 rows); built untouched"; exit 1; }
echo "=== APPLY: build_dotted_lexicon --apply on built (the one write) ==="
OUT=$(python3 scripts/build_dotted_lexicon.py "$B" --apply 2>&1); r=$?
printf '%s\n' "$OUT" > "$D/apply.log"
echo "$OUT"
echo "exit $r (expect 0)"
SAMEOUT=NO
case "$OUT" in "Filled dotted_lexicon in "*" with 3627 corrected headwords (that table only; nothing else touched).") [ "$(wc -l <<< "$OUT")" = "1" ] && SAMEOUT=yes;; esac
echo "output = the dry run's one line (path aside: Filled dotted_lexicon in ... with 3627 corrected headwords ...): $SAMEOUT"
R1=$(sqlite3 -readonly "$B" "$RD"); echo "dotted_lexicon on built after:"; echo "$R1"
SAMEDEF=NO; [ "$R1" = "$EXPD" ] && SAMEDEF=yes
echo "definition + 3627 rows after = before: $SAMEDEF"
CHK=$($E check --tag STEP12AA --built "$B" --dir "$DD" --written dotted_lexicon 2>&1); k=$?
echo "$CHK"
VAL=$($E delta --tag STEP12AA --a "$S" --b "$B" --table dotted_lexicon:strongs --out "$D/step12a_values_src_built.tsv" --zero 2>&1); v=$?
echo "$VAL"
if [ "$r" -eq 0 ] && [ "$SAMEOUT" = "yes" ] && [ "$SAMEDEF" = "yes" ] && [ "$k" -eq 0 ] && [ "$v" -eq 0 ]; then
  echo "STEP12A-APPLY RESULT: DONE - built dotted_lexicon re-created: 3,627 rows, = the dry run, = src row for row (0 both ways); the other 149 tables + schema unchanged"; exit 0
fi
echo "STEP12A-APPLY RESULT: CHECK - an after-figure differs (lines above). Restore source for dotted_lexicon: $DD/before.db"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12A-APPLY reviewed (11/8) — ESCALATE (write, §9.90), mechanics clean → cleared under §9.109

Reviewer verdict line verbatim: "REVIEW: ESCALATE - STEP12A-APPLY writes built, which is outside what I can clear (§9.90). The mechanical check found no defect, so this goes back to the ruling chat under §9.109."
The write gate stands as ruled at §9.109. The reviewer's one unread citation, `rebuild-words.md:359`, reads "Values
check after apply: `<built>` vs `<src>` both ways." (CC read). Block goes to PA as drafted.

### STEP12A-APPLY ran (11/9, 03:05 UTC, PA HEAD b3178672, REF 006e16ba) — DONE, exit 0 → STEP 12a CLOSED (§9.109 closing)

Log `~/edition_upgrade_runs/step12a_apply_20261108.log`; run folder `step12a_apply_20261108/` (apply.log,
step12a_values_src_built.tsv). PRE OK (built 451,993,600 B, src 451,964,928 B, no journal, triggers 0; both rollbacks
present). Both dry deltas 1 line (header only), sha c866c003… as declared. SAME OK (150 tables + schema, 0
differences). Before = the logged definition + autoindex + 3,627 rows. Builder: one line "Filled dotted_lexicon in …
with 3627 corrected headwords (that table only; nothing else touched).", exit 0 — = the dry run, path aside. After =
before (definition + 3,627 rows). CHECK OK: 149 untouched tables + schema 0 differences; `dotted_lexicon` 3,627 rows,
fingerprint 9288508f98d4 = dry copy = prep; no journal; repo scripts/tests clean. Values check src → built
(key strongs): 3,627 → 3,627, changed 0 / added 0 / removed 0; file header only, sha c866c003…. Restore source not
needed (`step12a_dry_20261108/before.db` kept until the swap).

## Step 12b (`word_gloss`) on built — STEP12B-DRY drafted (11/9)

Procedure `rebuild-words.md:360-367` + Q5 (dry on built → figures declared from that log by path:line → `--apply`
gated on them). `build_word_gloss.py` takes the db as its first non-flag argument (`:39-40`; none = LIVE, so the
block always passes one). It reads `words.strongs_base` (G set, `:411`), `dotted_lexicon` (`:417-418`), `abp_ext`
(`:420-422`), `kjv_strongs` + `bsb_strongs` (Hebrew universe, `:441-444`), `lexicon` (only with `--summary`,
`:540-541`); `~/bible-db/heb.db` (`:76`, opened `:446`, SELECT only); TBESG/TBESH from the pinned copies
(`:62-74`, sha256-refused if changed, `:177-185`; no `--fetch`); Dodson `scripts/apfathers/raw/dodson.csv` (`:75`).
Imports stdlib only. Dry run writes nothing to the db (`:553-556`) but writes `gloss_dotted_blank.tsv` /
`gloss_dotted_abp.tsv` into the CURRENT folder when they have rows (`:522-536`) — so each run goes in its own
scratch folder. `--apply` DROPs + re-CREATEs `word_gloss` only (`:558-561`).
**Dry form (as 12a):** the builder's dry run (+ `--summary`, the loaded-word review) AND its `--apply`, both on a
THROWAWAY copy of the seven tables it reads (eu_step prep), then a row-level delta keyed on `strongs` — built → dry
and src → dry. heb.db is read by sha256 before and after (it sits outside built; proves it unchanged). Also read out:
`word_gloss` definition + rows by source on built, src, and the dry copy after. Same-code expectation: delta 0 both
ways; the edition upgrade changed `words.strongs_base` (8b.2), so any difference is a member to read before an apply.
`PYTHONHASHSEED=0` only fixes the PRINT order of the builder's "by source" line (its Hebrew list is a Python set);
the rows written do not depend on it.
Tested locally on made-up dbs (fake home, repo clone at HEAD): READ DONE, one planted new number shown in both
deltas; re-paste, heb.db missing, heb.db journal, and a changed builder each STOP.
Unknown until it runs: the dry copy's size (words + kjv_strongs + bsb_strongs + 4 small tables) and heb.db's size.

### Block STEP12B-DRY (GATE REF 006e16ba; READ-ONLY on built, src and heb.db — writes only the run folder and its throwaway copy)

```bash
set +H
L=~/edition_upgrade_runs/step12b_dry_20261109.log
if [ -e "$L" ]; then echo "STEP12B-DRY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12B-DRY rebuild-words step 12b (build_word_gloss dry run + --apply) on a THROWAWAY copy of words/dotted_lexicon/abp_ext/lexicon/kjv_strongs/bsb_strongs/word_gloss - built, src and heb.db read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12B-DRY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP12B-DRY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8 PYTHONHASHSEED=0
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
H=~/bible-db/heb.db
D=~/edition_upgrade_runs/step12b_dry_20261109
G=~/bible-db/scripts/build_word_gloss.py
E="python3 scripts/eu_step.py"
RD="SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'word_gloss' ORDER BY type, name; SELECT 'rows', count(*) FROM word_gloss; SELECT 'source', source, count(*) FROM word_gloss GROUP BY source ORDER BY source"
$E pre --tag STEP12B --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP12B-DRY RESULT: STOP - pre (line above); nothing made"; exit 1; }
[ -s "$H" ] || { echo "STEP12B-DRY RESULT: STOP - $H missing or empty"; exit 1; }
[ -e "$H-journal" ] && { echo "STEP12B-DRY RESULT: STOP - a -journal sits beside $H"; exit 1; }
H0=$(sha256sum < "$H" | cut -d' ' -f1)
echo "heb.db (the builder reads it, never writes it): $(stat -c %s "$H") bytes, sha256 $H0"
for f in "$B" "$S"; do
  echo "--- word_gloss on $f (read-only): definition + row count + rows by source"
  sqlite3 -readonly "$f" "$RD" || { echo "STEP12B-DRY RESULT: STOP - word_gloss read failed on $f"; exit 1; }
done
$E prep --tag STEP12B --built "$B" --dir "$D" --copy words,dotted_lexicon,abp_ext,lexicon,kjv_strongs,bsb_strongs,word_gloss --save word_gloss || { echo "STEP12B-DRY RESULT: STOP - prep (line above); built untouched"; exit 1; }
mkdir "$D/dryrun" "$D/applycopy" || { echo "STEP12B-DRY RESULT: STOP - cannot make the two scratch folders; built untouched"; exit 1; }
echo "=== DRY 1: the builder's dry run (+ --summary: the loaded-word review) on the throwaway copy, run from $D/dryrun ==="
( cd "$D/dryrun" && python3 "$G" "$D/dry.db" --summary ) > "$D/dryrun.out" 2>&1; r=$?
cat "$D/dryrun.out"
echo "exit $r (expect 0)"
[ "$r" -eq 0 ] || { echo "STEP12B-DRY RESULT: STOP - the dry run failed on the copy (above); built untouched"; exit 1; }
grep -q '^\[dry-run\] nothing written' "$D/dryrun.out" || { echo "STEP12B-DRY RESULT: STOP - the dry run did not report 'nothing written'; built untouched"; exit 1; }
echo "=== DRY 2: --apply on the throwaway copy $D/dry.db, run from $D/applycopy (built untouched) ==="
( cd "$D/applycopy" && python3 "$G" "$D/dry.db" --apply ) > "$D/apply_dry.log" 2>&1; a=$?
cat "$D/apply_dry.log"
echo "exit $a (expect 0)"
[ "$a" -eq 0 ] || { echo "STEP12B-DRY RESULT: STOP - --apply failed on the copy (above); built untouched"; exit 1; }
grep -q '^Filled word_gloss with ' "$D/apply_dry.log" || { echo "STEP12B-DRY RESULT: STOP - --apply did not report a fill; built untouched"; exit 1; }
echo "--- files the builder left in its two scratch folders (sha256, lines):"
find "$D/dryrun" "$D/applycopy" -type f | sort | while read -r f; do echo "$(sha256sum < "$f" | cut -d' ' -f1)  $(wc -l < "$f") lines  ${f#"$D"/}"; done
echo "--- word_gloss on the dry copy after: definition + row count + rows by source"
sqlite3 -readonly "$D/dry.db" "$RD" || { echo "STEP12B-DRY RESULT: STOP - word_gloss read failed on the dry copy; built untouched"; exit 1; }
$E delta --tag STEP12B --a "$B" --b "$D/dry.db" --table word_gloss:strongs --out "$D/step12b_delta_built.tsv" || { echo "STEP12B-DRY RESULT: STOP - delta built -> dry (line above); built untouched"; exit 1; }
$E delta --tag STEP12B --a "$S" --b "$D/dry.db" --table word_gloss:strongs --out "$D/step12b_delta_src.tsv" || { echo "STEP12B-DRY RESULT: STOP - delta src -> dry (line above); built untouched"; exit 1; }
H1=$(sha256sum < "$H" | cut -d' ' -f1)
echo "heb.db after: sha256 $H1 - unchanged: $([ "$H1" = "$H0" ] && echo yes || echo NO)"
[ "$H1" = "$H0" ] || { echo "STEP12B-DRY RESULT: STOP - heb.db changed during the run (sha above) - report this, do not re-run"; exit 1; }
[ -e "$H-journal" ] && { echo "STEP12B-DRY RESULT: STOP - a -journal now sits beside $H"; exit 1; }
$E same --tag STEP12B --built "$B" --dir "$D" || { echo "STEP12B-DRY RESULT: STOP - built differs from its prep state (lines above)"; exit 1; }
echo "STEP12B-DRY RESULT: READ DONE - built untouched (same: OK), heb.db unchanged; the dry run's counts, the two deltas above (files + sha on their DELTA lines) and the scratch-folder files are the figures to declare for STEP12B-APPLY"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12B-DRY reviewed (11/9) — REVIEW: CLEAR

Verdict line verbatim: "REVIEW: CLEAR - this is a read-only block (scope a). Built, src and heb.db are only read; every write goes to ~/edition_upgrade_runs/step12b_dry_20261109*. No figures are asserted."
Cleared unchanged. Reviewer notes: both log checks match the builder's print lines (`:554`, `:564`); the builder's
`gloss_*.tsv` files land in the scratch folders; heb.db is opened with an ordinary connect but only read — the sha
before/after + journal checks prove it unchanged. Goes straight to PA (read-only). Unknown until it runs: the dry
copy's size and heb.db's size.

### STEP12B-DRY did not complete on PA (ruling chat, 11/9)

First paste cut off mid-block after the `H0=` line (no RESULT, no `exit=`); a re-paste stopped on "log already
exists", as designed. What the first paste left on PA is not known. Ruling (11/9): nothing is deleted or re-run; a
read-only block prints what exists; the move-aside proposal follows the read and is ruled after it.
Cause not known. Unverified possibility, not asserted: the console cut the paste itself (the block was ~5.9 KB).
The log's contents will show whether the run started at all, and the read block is kept to ~2.6 KB.

### Block STEP12B-READ (GATE REF 006e16ba; READ-ONLY — makes only its own empty folder via `pre` and its log)

Prints: any `eu_step` / `build_word_gloss` process still running; `pre` (repo guards; built + src present, no
journal, no triggers); the first paste's log IN FULL (size, last-written time, lines); the run folder's files (size,
last written, first 16 hex of sha256) or "not there"; heb.db sha256 + journal check, compared with the sha the first
paste logged if it got that far; `eu_step same` against the first paste's `state.json` if one exists (built unchanged
since that prep). RESULT: READ DONE, or CHECK if a process is running, heb.db has a journal or changed, or built
differs. Tested locally: empty folder, full folder, running process, built changed, heb.db changed, re-paste.

```bash
set +H
L=~/edition_upgrade_runs/step12b_partial_read_20261109.log
if [ -e "$L" ]; then echo "STEP12B-READ RESULT: STOP - log already exists (kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12B-READ: what the cut-off STEP12B-DRY paste left - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12B-READ RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; S=~/bible-db/bible_edupg_test_20261101.db; H=~/bible-db/heb.db
OL=~/edition_upgrade_runs/step12b_dry_20261109.log; D=~/edition_upgrade_runs/step12b_dry_20261109
echo "--- still running? (any eu_step / build_word_gloss process)"
PS=$(ps -eo pid,etime,args); P=$(grep -E 'eu_step|build_word_gloss' <<<"$PS"); echo "${P:-none}"
python3 scripts/eu_step.py pre --tag STEP12BR --ref "$REF" --dir ~/edition_upgrade_runs/step12b_partial_read_20261109 --db "$B" --db "$S" || { echo "STEP12B-READ RESULT: STOP - pre (line above)"; exit 1; }
echo "--- the first paste's log: $(stat -c '%s bytes, last written %y' "$OL" 2>&1), $(wc -l < "$OL") lines - in full:"
cat "$OL"; echo "--- end of that log"
if [ -d "$D" ]; then echo "--- run folder $D (size, last written, sha256):"
  [ -n "$(find "$D" -type f)" ] || echo "  (no files)"
  find "$D" -type f | sort | while read -r f; do echo "$(stat -c '%s  %y' "$f")  $(sha256sum < "$f" | cut -c1-16)  ${f#"$D"/}"; done
else echo "--- run folder $D: not there"; fi
[ -e "$H-journal" ] && HJ=YES || HJ=no
H1=$(sha256sum < "$H" | cut -d' ' -f1); H0=$(sed -n 's/^heb\.db (the builder reads it.*sha256 \([0-9a-f]*\)$/\1/p' "$OL")
echo "heb.db: $(stat -c %s "$H") bytes, sha256 $H1 - journal beside it: $HJ - first paste logged: ${H0:-not logged} - same: $([ -z "$H0" ] && echo n/a || { [ "$H1" = "$H0" ] && echo yes || echo NO; })"
SM="no state.json - prep never finished; built checked by pre above only"
if [ -s "$D/state.json" ]; then python3 scripts/eu_step.py same --tag STEP12BR --built "$B" --dir "$D" && SM=OK || SM="NOT OK (lines above)"; fi
echo "built vs the first paste's prep state: $SM"
if [ -n "$P" ] || [ "$HJ" = YES ] || [ "${SM#NOT OK}" != "$SM" ] || { [ -n "$H0" ] && [ "$H1" != "$H0" ]; }; then
  echo "STEP12B-READ RESULT: CHECK - something above is not as expected (running process, heb.db journal/changed, or built differs)"; exit 1; fi
echo "STEP12B-READ RESULT: READ DONE - nothing running; built/src: no journal (pre); heb.db unchanged where logged; built vs prep: $SM"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12B-READ reviewed (11/9) — ESCALATE (mechanical, tripwire 2) → fixed → REVIEW: CLEAR

First pass: ESCALATE — the "still running?" line piped `ps` into grep under pipefail (tripwire 2). Fixed with the
reviewer's option (b) exactly: `PS=$(ps -eo pid,etime,args); P=$(grep -E 'eu_step|build_word_gloss' <<<"$PS")`;
nothing else changed; retested (none → READ DONE; fake running process → CHECK). Second pass, verdict line verbatim:
"REVIEW: CLEAR - read-only block (scope a): it only reads built, src, heb.db and the old log/folder; it writes only its new empty folder (made by pre) and its new log; no figures asserted."
Goes straight to PA (read-only).

### STEP12B-READ ran (11/10, 02:38 UTC, PA HEAD b3178672) — READ DONE, exit 0 → partial run CLOSED "no effect" (ruling chat 11/10)

Log `~/edition_upgrade_runs/step12b_partial_read_20261109.log`. No process running; PRE OK. The first paste's log:
1,916 B / 30 lines, written 17:04:44–17:04:49Z 11/9 — PRE OK, heb.db 49,831,936 B sha `885ed4e8…`, word_gloss on
built AND src: same definition, 17,568 rows, same six source counts (abp-ext 116, dodson 5,220, dotted-lemma 3,449,
override 59, tbesg 72, tbesh 8,652); ends there. Run folder present and EMPTY; no state.json (prep never wrote it);
heb.db sha now = logged, no journal. Built, src, heb.db untouched. Ruling (11/10): closed as "no effect"; log + empty
folder moved aside, never deleted; then STEP12B-DRY runs again, same block, same REF. If the re-paste is cut off
again, that is the report — no third paste.
CC observation (no cause asserted): bash reads a whole `if … fi` block before running any of it, and the log holds
lines from after the point where the console display stopped — so the full block reached bash. The run stopped
inside `eu_step prep`, which prints nothing until its whole-database fingerprint finishes (53–61 s on PA at steps
11/12a); its state.json is written only after that.

### Block STEP12B-ASIDE (WRITES only run artifacts: makes one folder, moves the partial log + empty folder into it; no repo code runs)

Name: `~/edition_upgrade_runs/aside_step12b_dry_20261109_partial_noeffect/` holding `step12b_dry_20261109.log` and
the empty `step12b_dry_20261109/`, moved with `mv -n` (never overwrites). STOPs, moving nothing, if: the aside
folder exists, the log or folder is missing, the folder is not empty, an `eu_step`/`build_word_gloss` process runs, or
the log is not 1,916 bytes. DONE only if both originals are gone, both are in the aside folder, and the log's sha256
after = before. Then the original names are free, so the re-run is the cleared STEP12B-DRY block **byte for byte,
original log name** (record copy = tested copy, checked). Tested locally: good case → DONE, then STEP12B-DRY → READ
DONE; re-paste, aside exists, folder not empty, wrong size, running process → each STOP.

```bash
set +H
L=~/edition_upgrade_runs/step12b_moveaside_20261110.log
if [ -e "$L" ]; then echo "STEP12B-ASIDE RESULT: STOP - log already exists (kept as is): $L"; else
( set -uo pipefail
echo "STEP12B-ASIDE - moves the partial STEP12B-DRY log + its empty run folder aside (mv, nothing deleted; no repo code runs) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
R=~/edition_upgrade_runs; N=step12b_dry_20261109; A=$R/aside_${N}_partial_noeffect
[ -e "$A" ] && { echo "STEP12B-ASIDE RESULT: STOP - $A already exists; nothing moved"; exit 1; }
[ -f "$R/$N.log" ] || { echo "STEP12B-ASIDE RESULT: STOP - $R/$N.log not there; nothing moved"; exit 1; }
[ -d "$R/$N" ] || { echo "STEP12B-ASIDE RESULT: STOP - $R/$N not there; nothing moved"; exit 1; }
[ -z "$(ls -A "$R/$N")" ] || { echo "STEP12B-ASIDE RESULT: STOP - $R/$N is not empty (the read found it empty); nothing moved"; ls -la "$R/$N"; exit 1; }
PS=$(ps -eo pid,etime,args); P=$(grep -E 'eu_step|build_word_gloss' <<<"$PS")
[ -z "$P" ] || { echo "STEP12B-ASIDE RESULT: STOP - a process is running (below); nothing moved"; echo "$P"; exit 1; }
n=$(wc -c < "$R/$N.log"); s0=$(sha256sum < "$R/$N.log" | cut -d' ' -f1)
echo "partial log: $n bytes (expect 1916, the read), $(wc -l < "$R/$N.log") lines (expect 30), sha256 $s0"
[ "$n" = 1916 ] || { echo "STEP12B-ASIDE RESULT: STOP - the log is not the 1,916-byte one the read saw; nothing moved"; exit 1; }
mkdir "$A" || { echo "STEP12B-ASIDE RESULT: STOP - cannot make $A; nothing moved"; exit 1; }
mv -n "$R/$N.log" "$A/" && mv -n "$R/$N" "$A/" || { echo "STEP12B-ASIDE RESULT: CHECK - a move failed (above); see the listing"; grep step12b <<<"$(ls -la "$R")"; exit 1; }
echo "--- $A after:"; ls -la "$A" "$A/$N"
s1=$(sha256sum < "$A/$N.log" | cut -d' ' -f1)
OK=yes; [ -e "$R/$N.log" ] && OK=no; [ -e "$R/$N" ] && OK=no; [ -d "$A/$N" ] || OK=no; [ "$s1" = "$s0" ] || OK=no
if [ "$OK" = yes ]; then
  echo "STEP12B-ASIDE RESULT: DONE - partial log (sha $s0, unchanged) + empty run folder now in $A; the original names are free for the STEP12B-DRY re-run"; exit 0; fi
echo "STEP12B-ASIDE RESULT: CHECK - something is not where expected (listing above; log sha after $s1)"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12B-DRY re-run (after STEP12B-ASIDE DONE)

The block "Block STEP12B-DRY" above, unchanged (REF 006e16ba; reviewer CLEAR 11/9), pasted only after STEP12B-ASIDE
ends DONE. Keep the console open until its RESULT and `exit=` lines print.

### STEP12B-ASIDE + re-run reviewed (11/10)

**STEP12B-ASIDE:** first pass ESCALATE — tripwire 1 (bare `!` in the DONE test) and tripwire 2 (`ls | grep` in the
CHECK branch); scope and other mechanics clean. Fixed as the reviewer suggested (`OK=yes … && OK=no` test;
`grep step12b <<<"$(ls -la "$R")"`); nothing else changed; retested. Second pass, verdict line verbatim:
"REVIEW: CLEAR - STEP12B-ASIDE as it stands (`docs/handoffs/DRAFT_stageC_outline.md` lines 6441-6466) only moves run artifacts, overwrites nothing, and no longer hits tripwire 1 or 2."
Reviewer read it as inside the 2026-11-06 run-artifact carve-out (ruling chat 11/10: "scope as the reviewer reads it").
**STEP12B-DRY re-run:** verdict line verbatim: "REVIEW: CLEAR - re-run of the read-only block I cleared 11/9 (scope a), unchanged in the record; its two name guards pass once STEP12B-ASIDE ends DONE. No figures asserted."
CC checked: `git diff --quiet 006e16ba HEAD -- scripts tests` clean; the record's STEP12B-DRY block is byte-identical
to the copy at `5e0213f1`. Order on PA: STEP12B-ASIDE; only if it ends DONE, STEP12B-DRY. If the re-paste is cut off
again, that is the report (no third paste).

### STEP12B-ASIDE + STEP12B-DRY re-run ran (11/14, PA HEAD b3178672) — ASIDE DONE; DRY READ DONE, exit 0, NOT +0/−0

ASIDE 01:23Z: partial log 1,916 B / 30 lines, sha bc969e36…, moved with the empty folder into
`aside_step12b_dry_20261109_partial_noeffect/`; DONE, exit 0. DRY re-run 01:24Z, log
`step12b_dry_20261109.log`: PRE OK; heb.db 49,831,936 B sha 885ed4e8…, unchanged after; word_gloss on built = src
(17,568 rows; abp-ext 116 / dodson 5,220 / dotted-lemma 3,449 / override 59 / tbesg 72 / tbesh 8,652). PREP OK:
150 tables / 3,809,451 rows in 72 s; before.db 831,488 B; dry.db 130,338,816 B; seven copied tables = built. DRY 1
"nothing written", exit 0. DRY 2 filled 17,650 (5,389 Greek base + 3,580 dotted + 8,681 Hebrew), exit 0; by source
after: abp-ext 116 / dodson 5,298 / dotted-lemma 3,449 / override 59 / tbesg 76 / tbesh 8,652. Read-outs: dotted
blank 47 (`gloss_dotted_blank.tsv`, 48 lines, 164536dc…), ABP-glossed dotted 116 (`gloss_dotted_abp.tsv`, 117 lines,
d6b50a4d…), identical in both scratch folders. **Delta built → dry = src → dry: changed 0, added 82, removed 0;**
both files 82 lines + header, sha f70ab8a0…. SAME OK.
Ruling chat (11/14): not the same-code +0/−0 — dodson +78, tbesg +4, the 40 printed all proper nouns. STEP12B-APPLY
NOT drafted. First: (1) the full 82 with source in the record; (2) a repo read of what accounts for them.

### The 82 — repo read (11/14, CC; from what was read, no cause asserted)

- **Gloss-picking code unchanged since 2026-07-06.** `build_word_gloss.py` commits after `a06a90b8` (7/06, G39
  override): one, `1ad10cec` (11/07) — db path argument + TBESG/TBESH read from pinned copies (commit text: the
  pinned files are the versions in place at the 6/22 build and parse identically, 10,846 / 10,790 / 8,723 — the
  same counts the dry run printed). `git diff a06a90b8 HEAD` on the builder touches none of `pick_base`,
  `build_greek_rows`, `OVERRIDES`, `normalize`, `load_dodson`, `parse_tbesg`.
- **Sources unchanged:** `scripts/apfathers/raw/dodson.csv` last changed `982d3c7e` (6/22, first tracked).
- **Where a Greek base row comes from:** the builder makes one row per `DISTINCT words.strongs_base GLOB 'G*'` in the
  db it runs on (`:411`), glossed override → Dodson → TBESG (`pick_base`, `:387-396`). A number gets a row only if
  it is in that db's `words`.
- **Same values where both have the number:** the delta is changed 0 over all 17,568 existing keys (vs built and
  vs src) — current code + pinned sources reproduce every row live already has, overrides included (59 = 59).
- **Not in the repo:** when live's `word_gloss` was last `--apply`'d. Nothing records it; `TODO.md:52-57` still
  lists the post-6/26 overrides' state on PA as unconfirmed.
- **So the open question is data, not code:** are the 82 numbers in src's `words.strongs_base` too (then live's
  word_gloss predates them in live's words), or only in built's (then the edition upgrade brought them in)? The
  repo cannot answer that; STEP12B-MEMBERS below reads it.

### Block STEP12B-MEMBERS (GATE REF 006e16ba; READ-ONLY — makes only its own empty folder via `pre` and its log)

Prints the dry run's `step12b_delta_built.tsv` IN FULL (sha-checked = f70ab8a0…; the 82 with gloss and source), then
for each of the 82 numbers its `words` row count on built and on src (`strongs_base` = the number), side by side,
and how many have none on each. Tested locally (planted number: built 1 / src 0 → READ DONE; wrong file → STOP;
re-paste → STOP).

```bash
set +H
L=~/edition_upgrade_runs/step12b_members_20261114.log
if [ -e "$L" ]; then echo "STEP12B-MEMBERS RESULT: STOP - log already exists (kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12B-MEMBERS: the 82 word_gloss rows the dry run added + each number's words rows on built and src - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12B-MEMBERS RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db; S=~/bible-db/bible_edupg_test_20261101.db
T=~/edition_upgrade_runs/step12b_dry_20261109/step12b_delta_built.tsv; X=f70ab8a0a017836044de54e9c0ece024802f58cb6b5f7d447039b76d85693e64
python3 scripts/eu_step.py pre --tag STEP12BM --ref "$REF" --dir ~/edition_upgrade_runs/step12b_members_20261114 --db "$B" --db "$S" || { echo "STEP12B-MEMBERS RESULT: STOP - pre (line above)"; exit 1; }
s=$(sha256sum < "$T" | cut -d' ' -f1)
echo "delta file $T: $(wc -l < "$T") lines (expect 83 = header + 82), sha256 $s (expect $X)"
[ "$s" = "$X" ] || { echo "STEP12B-MEMBERS RESULT: STOP - not the dry run's delta file"; exit 1; }
echo "--- the delta file in full:"; cat "$T"; echo "--- end of the delta file"
K=$(sed -n "s/^word_gloss\tADDED\t('\([GH][0-9.]*\)',).*/('\1')/p" "$T" | paste -sd, -)
k=$(sed -n "s/^word_gloss\tADDED\t('\([GH][0-9.]*\)',).*/\1/p" "$T" | wc -l)
echo "numbers read from the file: $k (expect 82)"
[ "$k" -gt 0 ] || { echo "STEP12B-MEMBERS RESULT: STOP - no numbers read from the file"; exit 1; }
Q="WITH k(s) AS (VALUES $K) SELECT k.s, count(w.strongs_base) FROM k LEFT JOIN words w ON w.strongs_base = k.s GROUP BY k.s ORDER BY k.s"
QB=$(sqlite3 -readonly "$B" "$Q") || { echo "STEP12B-MEMBERS RESULT: STOP - words read failed on built"; exit 1; }
QS=$(sqlite3 -readonly "$S" "$Q") || { echo "STEP12B-MEMBERS RESULT: STOP - words read failed on src"; exit 1; }
echo "--- words rows per number (number|built|src):"
[ "$(cut -d'|' -f1 <<<"$QB")" = "$(cut -d'|' -f1 <<<"$QS")" ] || { echo "STEP12B-MEMBERS RESULT: STOP - the two number lists differ"; exit 1; }
paste -d'|' <(echo "$QB") <(cut -d'|' -f2 <<<"$QS")
zb=$(awk -F'|' '$2==0{c++} END{print c+0}' <<<"$QB"); zs=$(awk -F'|' '$2==0{c++} END{print c+0}' <<<"$QS")
echo "STEP12B-MEMBERS RESULT: READ DONE - $k numbers; with NO words rows: built $zb, src $zs (of $k)"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12B-MEMBERS reviewed (11/14) — REVIEW: CLEAR

Verdict line verbatim: "REVIEW: CLEAR - read-only block (scope a). The pre gate is in eu_step, the single real gate is the sha, the only writes are an empty run folder and the log, and no figure is asserted without a source."
Reviewer could not run git; the commit claims in the repo read (`a06a90b8`, `1ad10cec`, `982d3c7e`, the
`git diff a06a90b8 HEAD` function check) are CC's reads (11/14, `git log` / `git diff` on this checkout). Limit
noted: a number with a letter suffix would not match the sed and would show as k ≠ 82. Goes straight to PA.

### STEP12B-MEMBERS ran (11/14, 01:34 UTC, PA HEAD b3178672, REF 006e16ba) — READ DONE, exit 0

Log `~/edition_upgrade_runs/step12b_members_20261114.log`. PRE OK. Delta file 83 lines, sha f70ab8a0… (matched); 82
numbers read. **All 82 have `words` rows on built AND src, identical counts; 0 with none on either side.** 78 dodson,
4 tbesg (G6202, G9826, G9827, G9829); all proper nouns. The full list (number | gloss the builder gives | source |
words rows, built = src):

```
G1043 | Gabriel | dodson | 4
G1045 | Gad | dodson | 88
G1066 | Gideon | dodson | 44
G1116 | Gomorrah | dodson | 25
G1136 | Gog | dodson | 14
G1138 | David | dodson | 1150
G1158 | Daniel | dodson | 81
G1443 | Eber | dodson | 12
G1445 | Hebrew | dodson | 44
G1478 | Hezekiah | dodson | 132
G1695 | Emmaus | dodson | 1
G1697 | Hamor | dodson | 13
G1802 | Enoch | dodson | 14
G2166 | Euphrates | dodson | 22
G2187 | Ephraim | dodson | 188
G2194 | Zebulon | dodson | 51
G2196 | Zerah | dodson | 19
G2243 | Elijah | dodson | 113
G2268 | Isaiah | dodson | 54
G2269 | Esau | dodson | 105
G2283 | Tamar | dodson | 25
G2291 | Terah | dodson | 12
G2391 | Jared | dodson | 7
G2408 | Jeremiah | dodson | 134
G2410 | Jericho | dodson | 65
G2421 | Jesse | dodson | 48
G2422 | Jephthah | dodson | 31
G2445 | Joppa | dodson | 13
G2446 | Jordan | dodson | 207
G2449 | Judea | dodson | 87
G2464 | Isaac | dodson | 136
G2466 | Issachar | dodson | 44
G2488 | Jotham | dodson | 26
G2493 | Joel | dodson | 21
G2495 | Jonah | dodson | 31
G2496 | Joram, Jehoram | dodson | 51
G2498 | Jehoshaphat | dodson | 77
G2502 | Josiah | dodson | 55
G2535 | Cain | dodson | 20
G28 | Hagar | dodson | 14
G3098 | Magog | dodson | 5
G3121 | Mahalaleel, Maleleel | dodson | 6
G3198 | Melchizedek | dodson | 10
G3318 | Mesopotamia | dodson | 19
G3413 | Michael | dodson | 15
G3416 | Mnason | dodson | 1
G3475 | Moses | dodson | 862
G3481 | Nathan | dodson | 44
G3508 | Naphtali | dodson | 55
G3604 | Uzziah | dodson | 28
G3683 | Onesiphorus | dodson | 2
G4497 | Rehoboam | dodson | 53
G4502 | Reuben | dodson | 90
G4527 | Sala | dodson | 3
G4545 | Samuel | dodson | 148
G4546 | Samson | dodson | 43
G4564 | Sarah | dodson | 57
G4589 | Seth | dodson | 10
G4611 | Siloam | dodson | 3
G4614 | Sinai | dodson | 41
G4670 | Sodom | dodson | 49
G4672 | Solomon | dodson | 310
G4966 | Shechem | dodson | 68
G5328 | Pharaoh | dodson | 285
G5466 | Chaldean | dodson | 3
G5488 | Haran | dodson | 22
G5601 | Obed | dodson | 33
G5617 | Hosea | dodson | 4
G6 | Abel | dodson | 17
G6202 | Akra | tbesg | 5
G742 | Arphaxad | dodson | 10
G760 | Asa | dodson | 60
G768 | Asher | dodson | 46
G881 | Ahaz | dodson | 43
G9 | Abilene | dodson | 1
G903 | Balaam | dodson | 63
G913 | Barak | dodson | 15
G958 | Benjamin | dodson | 181
G965 | Bethlehem | dodson | 53
G9826 | Bougean | tbesg | 9
G9827 | Edem | tbesg | 1
G9829 | Heliopolis | tbesg | 6
```

**Ruling chat reading (11/14):** the 82 numbers were already in live's `words` (src = the 11/01 copy of live); the
edition upgrade did not introduce them. Live's `word_gloss` lacks rows for them, while the current builder on the same
sources produces them. The +82 fills missing glosses; it changes no existing gloss.
**Note on live's word_gloss (no action here, ruling 11/14):** live's `word_gloss` is 82 rows short of what the current
builder makes from live's own `words` — these 82 proper-noun numbers have no header gloss on live.

**Ruling (11/14, §9.110):** the +82 is accepted as the declared figure for 12b. STEP12B-APPLY gated on the dry
figures (below). Restore source `step12b_dry_20261109/before.db`.

### Block STEP12B-APPLY (GATE REF 006e16ba; WRITES built: word_gloss only, DROP + re-CREATE, 17,568 → 17,650) — for the ruling chat

Declared figures sit at the top of the block, each from the STEP12B-DRY log (11/14 01:24Z):
- both dry delta files 83 lines, sha f70ab8a0… (82 added / 0 changed / 0 removed);
- the dry scratch files (`gloss_dotted_abp.tsv` d6b50a4d…, `gloss_dotted_blank.tsv` 164536dc…);
- heb.db sha 885ed4e8…;
- word_gloss before = definition + 17,568 rows (abp-ext 116 / dodson 5,220 / dotted-lemma 3,449 / override 59 /
  tbesg 72 / tbesh 8,652);
- after = 17,650 (dodson 5,298, tbesg 76, the rest unchanged);
- builder lines "Greek base   : 5389  (blank: 0)", "Greek dotted : 3580  (blank: 47)", "Hebrew       : 8681
  (blank: 0)", and "Filled word_gloss with 17650 glosses (5389 Greek base + 3580 dotted + 8681 Hebrew; that table
  only, nothing else touched)."

**Before the write, each miss is a STOP and built is untouched:** pre; the dry files present; both delta files =
declared; the dry scratch files = declared; `same` (built unchanged since the dry run); heb.db no journal + sha =
declared; word_gloss before = declared.

**The one write:** `build_word_gloss.py "$B" --apply`, run from `step12b_apply_20261114/apply/`.

**After the write, each miss is a CHECK naming the restore source:**
- the 4 builder lines present exactly. The whole output is also compared with the dry run's, but shown only, since
  the by-source line's order may differ.
- the scratch files = declared, and exactly that many.
- word_gloss after = declared.
- `check --written word_gloss` (149 untouched + schema; word_gloss = the dry copy).
- delta src → built with `--expect-sha f70ab8a0…`, i.e. exactly the 82 declared additions.
- heb.db sha unchanged, no journal.

Tested locally (made-up dbs, local figures swapped in): DONE. Built changed since the dry run → STOP; heb.db changed →
STOP; a dry scratch file altered → STOP; an after-figure off → CHECK with the restore source; the real figures on the
local data → STOP; re-paste → STOP.

```bash
set +H
L=~/edition_upgrade_runs/step12b_apply_20261114.log
if [ -e "$L" ]; then echo "STEP12B-APPLY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12B-APPLY rebuild-words step 12b (build_word_gloss --apply) on BUILT, gated on the STEP12B-DRY figures (+82 ruled 11/14) - WRITES built: word_gloss only (drop + re-create, 17,568 -> 17,650 rows) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12B-APPLY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP12B-APPLY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8 PYTHONHASHSEED=0
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
H=~/bible-db/heb.db
DD=~/edition_upgrade_runs/step12b_dry_20261109
D=~/edition_upgrade_runs/step12b_apply_20261114
G=~/bible-db/scripts/build_word_gloss.py
E="python3 scripts/eu_step.py"
RD="SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'word_gloss' ORDER BY type, name; SELECT 'rows', count(*) FROM word_gloss; SELECT 'source', source, count(*) FROM word_gloss GROUP BY source ORDER BY source"
# --- declared figures: STEP12B-DRY log (11/14 01:24Z), ruled 11/14 ---
XD=f70ab8a0a017836044de54e9c0ece024802f58cb6b5f7d447039b76d85693e64; XL=83
XH=885ed4e8eee19492bf433d551353b52366f6021291b731ef7f3b0d6a19288e65
XF=$(printf '%s\n' "gloss_dotted_abp.tsv d6b50a4d1b77240f0b91382b42cd96dc830fe783d43eeb2712cd1e532892c3d2" "gloss_dotted_blank.tsv 164536dcee240e23bb0f71589604a4903cb8fde57ff3e24abc32561c29dbd0df")
XDEF=$(printf '%s\n' "index|sqlite_autoindex_word_gloss_1|" "table|word_gloss|CREATE TABLE word_gloss (strongs TEXT PRIMARY KEY, gloss TEXT, source TEXT)")
XB=$(printf '%s\n' "$XDEF" "rows|17568" "source|abp-ext|116" "source|dodson|5220" "source|dotted-lemma|3449" "source|override|59" "source|tbesg|72" "source|tbesh|8652")
XA=$(printf '%s\n' "$XDEF" "rows|17650" "source|abp-ext|116" "source|dodson|5298" "source|dotted-lemma|3449" "source|override|59" "source|tbesg|76" "source|tbesh|8652")
XO=$(printf '%s\n' "Greek base   : 5389  (blank: 0)" "Greek dotted : 3580  (blank: 47)" "Hebrew       : 8681  (blank: 0)" "Filled word_gloss with 17650 glosses (5389 Greek base + 3580 dotted + 8681 Hebrew; that table only, nothing else touched).")
# --- before the write: every miss is STOP, built untouched ---
$E pre --tag STEP12BA --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP12B-APPLY RESULT: STOP - pre (line above); built untouched"; exit 1; }
for f in state.json before.db dry.db apply_dry.log step12b_delta_built.tsv step12b_delta_src.tsv; do [ -s "$DD/$f" ] || { echo "STEP12B-APPLY RESULT: STOP - the dry run's $f is missing or empty in $DD; built untouched"; exit 1; }; done
for f in step12b_delta_built.tsv step12b_delta_src.tsv; do
  s=$(sha256sum < "$DD/$f" | cut -d' ' -f1); n=$(wc -l < "$DD/$f")
  echo "dry delta $f: $n lines (expect $XL = header + 82 added), sha256 $s (expect $XD)"
  [ "$s" = "$XD" ] && [ "$n" = "$XL" ] || { echo "STEP12B-APPLY RESULT: STOP - $f is not the declared delta; built untouched"; exit 1; }
done
while read -r f x; do
  s=$(sha256sum < "$DD/applycopy/$f" | cut -d' ' -f1); echo "dry scratch file applycopy/$f: sha256 $s (expect $x)"
  [ "$s" = "$x" ] || { echo "STEP12B-APPLY RESULT: STOP - the dry run's $f is not the declared one; built untouched"; exit 1; }
done <<<"$XF"
$E same --tag STEP12BA --built "$B" --dir "$DD" || { echo "STEP12B-APPLY RESULT: STOP - built changed since the dry run (lines above); built untouched"; exit 1; }
[ -e "$H-journal" ] && { echo "STEP12B-APPLY RESULT: STOP - a -journal sits beside $H; built untouched"; exit 1; }
h0=$(sha256sum < "$H" | cut -d' ' -f1); echo "heb.db before: sha256 $h0 (expect $XH)"
[ "$h0" = "$XH" ] || { echo "STEP12B-APPLY RESULT: STOP - heb.db is not the one the dry run read; built untouched"; exit 1; }
R0=$(sqlite3 -readonly "$B" "$RD") || { echo "STEP12B-APPLY RESULT: STOP - read before failed; built untouched"; exit 1; }
echo "word_gloss on built before:"; echo "$R0"
[ "$R0" = "$XB" ] || { echo "STEP12B-APPLY RESULT: STOP - built's word_gloss is not the dry log's picture (definition + 17568 rows by source); built untouched"; exit 1; }
mkdir "$D/apply" || { echo "STEP12B-APPLY RESULT: STOP - cannot make the scratch folder; built untouched"; exit 1; }
# --- the one write ---
echo "=== APPLY: build_word_gloss --apply on built, run from $D/apply (the one write) ==="
( cd "$D/apply" && python3 "$G" "$B" --apply ) > "$D/apply.log" 2>&1; r=$?
cat "$D/apply.log"; echo "exit $r (expect 0)"
# --- after the write: every miss is CHECK ---
SO=yes; while IFS= read -r x; do grep -qFx -- "$x" "$D/apply.log" || SO=NO; done <<<"$XO"
echo "the three count lines + the Filled line = the dry run's: $SO"
echo "whole output = the dry run's (shown only; the by-source line's order may differ): $(cmp -s "$D/apply.log" "$DD/apply_dry.log" && echo yes || echo no)"
SF=yes
while read -r f x; do s=$(sha256sum < "$D/apply/$f" | cut -d' ' -f1); echo "scratch file apply/$f: sha256 $s (expect $x)"; [ "$s" = "$x" ] || SF=NO; done <<<"$XF"
nf=$(find "$D/apply" -type f | wc -l); ne=$(wc -l <<<"$XF"); echo "files in $D/apply: $nf (expect $ne)"; [ "$nf" = "$ne" ] || SF=NO
R1=$(sqlite3 -readonly "$B" "$RD"); echo "word_gloss on built after:"; echo "$R1"
SA=NO; [ "$R1" = "$XA" ] && SA=yes; echo "definition + 17650 rows by source = the dry copy's: $SA"
CHK=$($E check --tag STEP12BA --built "$B" --dir "$DD" --written word_gloss 2>&1); k=$?; echo "$CHK"
VAL=$($E delta --tag STEP12BA --a "$S" --b "$B" --table word_gloss:strongs --out "$D/step12b_values_src_built.tsv" --expect-sha "$XD" 2>&1); v=$?; echo "$VAL"
h1=$(sha256sum < "$H" | cut -d' ' -f1); HS=yes; [ "$h1" = "$XH" ] || HS=NO; [ -e "$H-journal" ] && HS=NO
echo "heb.db after: sha256 $h1 - unchanged, no journal: $HS"
if [ "$r" -eq 0 ] && [ "$SO" = yes ] && [ "$SF" = yes ] && [ "$SA" = yes ] && [ "$k" -eq 0 ] && [ "$v" -eq 0 ] && [ "$HS" = yes ]; then
  echo "STEP12B-APPLY RESULT: DONE - built word_gloss re-created: 17,650 rows = the dry run; vs src exactly the 82 declared additions (0 changed / 0 removed); the other 149 tables + schema unchanged; heb.db unchanged"; exit 0
fi
echo "STEP12B-APPLY RESULT: CHECK - an after-figure differs (lines above). Restore source for word_gloss: $DD/before.db"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12B-APPLY reviewed (11/14) — ESCALATE (write, §9.90), mechanics clean → to the ruling chat (§9.110 write gate)

Verdict line verbatim: "REVIEW: ESCALATE - STEP12B-APPLY writes built (word_gloss DROP + CREATE + INSERT), so under §9.90 the write gate is the ruling chat's call. The mechanics are clean. Two declared figures are only partly traceable to the record (see 1 and 2 below)."
The reviewer's two untraceable items, closed here from the STEP12B-DRY re-run log as pasted by JP 11/14
(`step12b_dry_20261109.log`, the DRY 1 and DRY 2 output), verbatim:
1. Count lines (identical in DRY 1 and DRY 2):
   `Greek base   : 5389  (blank: 0)` · `Greek dotted : 3580  (blank: 47)` · `Hebrew       : 8681  (blank: 0)` ·
   `Filled word_gloss with 17650 glosses (5389 Greek base + 3580 dotted + 8681 Hebrew; that table only, nothing else touched).`
2. Full sha256 values:
   - both delta files `f70ab8a0a017836044de54e9c0ece024802f58cb6b5f7d447039b76d85693e64`, "82 lines + header";
   - heb.db `885ed4e8eee19492bf433d551353b52366f6021291b731ef7f3b0d6a19288e65` (49,831,936 B), before and after;
   - `gloss_dotted_abp.tsv` `d6b50a4d1b77240f0b91382b42cd96dc830fe783d43eeb2712cd1e532892c3d2` (117 lines);
   - `gloss_dotted_blank.tsv` `164536dcee240e23bb0f71589604a4903cb8fde57ff3e24abc32561c29dbd0df` (48 lines);
   - the two scratch files are the same in `dryrun/` and `applycopy/`.
These match XO / XD / XH / XF in the block exactly. A wrong value before the write would STOP; a wrong count line
after it would CHECK.

### STEP12B-APPLY ran (11/14, 01:45 UTC, PA HEAD b3178672, REF 006e16ba) — DONE, exit 0 → STEP 12b CLOSED (§9.110 closing)

Log `~/edition_upgrade_runs/step12b_apply_20261114.log`; run folder `step12b_apply_20261114/` (apply.log, apply/
scratch files, step12b_values_src_built.tsv). Write gate: the 11/14 +82 ruling stands as the §9.110 call. PRE OK;
both dry deltas 83 lines / f70ab8a0…; dry scratch shas matched; SAME OK (150 + schema, 0); heb.db before 885ed4e8…;
word_gloss before = declared (17,568 by source). Builder exit 0; the 3 count lines + Filled line = dry; whole output =
dry. Scratch files 2, shas = declared. After = declared (17,650; dodson 5,298, tbesg 76, rest unchanged). CHECK OK:
149 untouched + schema 0; word_gloss 17,650 rows, fingerprint 22ca5f3ab0c5 = dry copy (prep 17,568, daea2c5f30ba).
Values src → built: 0 changed / 82 added / 0 removed, file sha f70ab8a0… = the dry delta. heb.db after unchanged, no
journal. Restore source not needed (`step12b_dry_20261109/before.db` kept until the swap).
Transcript note (ruling chat, no action): the console echo of the pasted block was garbled on one line; the block ran
in full and ended DONE; the log is authoritative.

## Step 12c (`tipnr_metav_link` person rows) on built — STEP12C-DRY drafted (11/14)

Procedure `rebuild-words.md:367-383`, rulings Q4 (no 12d; READ-ONLY place-link orphan check, expect 0, anything else =
STOP) and blocker 3 (the two untracked leftover lists copied aside and left untouched) in
`DRAFT_rebuild_words_side_tables.md`, and Q5 (dry → declare → apply).

Builder `scripts/build_person_metav_link.py`:
- `--bible <db>` is the db it reads (and with `--apply` writes); without it, LIVE (`:51`, `:53-55`).
- `--index` is metav_index.db (`:52`, `:56-57`).
- `--out-dir` is where the two leftover lists go (`:60-63`, written `:292-293`, `:308-309`, in the dry run too).
- Dry run opens `--bible` read-only and ATTACHes the index read-only (`:116-118`). It reads `tipnr_entities`,
  `tipnr_entity_refs`, `metav_people`, `pn_binding` (`:120-150`).
- `--apply`: `DELETE … WHERE kind='person'` + INSERT the person links + `CREATE INDEX IF NOT EXISTS`
  (`:326-341`); place rows untouched. It adds columns only if the table lacks them (`:328-335`).
- `--check-place-orphans`: read-only (`:66-80`, `:99-112`); prints `PLACE-LINK ORPHANS: N`; exit 0 only at 0.
- It imports `entity_resolution.py` from the repo root (`:48-49`), so the block guards that file against the REF
  itself (§9.107 pattern).

**Dry form (as 12a/12b):**
- the builder's dry run AND its `--apply`, both on a THROWAWAY copy of the five tables (eu_step prep, restore source
  `tipnr_metav_link`), each with `--out-dir` in its own scratch folder;
- the two leftover lists in `scripts/` copied to `aside/`, their sha (or "absent") read before and after;
- metav_index.db sha before and after;
- the place-link orphan check on built (before anything) and on the copy after `--apply`, each must exit 0;
- a delta keyed on `uniq+kind` (person rowids change on re-insert), built → dry and src → dry;
- read-outs: the table definition, rows by kind, and rows by kind/rule on built, src and the copy after.

Same-code expectation: delta 0 both ways. Since 8b.3 rebuilt `pn_binding` and the edition changed entities and
refs, any difference is a member to read before an apply.

Tested locally (made-up tables, a planted new person entity): READ DONE, the planted link in both deltas, orphans 0
twice. Each of these STOPs: re-paste, a planted place orphan on built (the check fires), a metav_index journal,
`entity_resolution.py` edited, metav_index missing. Unknown until it runs: the dry copy's size and metav_index.db's
size.

### Block STEP12C-DRY (GATE REF 006e16ba; READ-ONLY on built, src and metav_index.db — writes only the run folder, its throwaway copy, and the aside copies)

```bash
set +H
L=~/edition_upgrade_runs/step12c_dry_20261114.log
if [ -e "$L" ]; then echo "STEP12C-DRY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12C-DRY rebuild-words step 12c (build_person_metav_link dry run + --apply) on a THROWAWAY copy of tipnr_entities/tipnr_entity_refs/metav_people/pn_binding/tipnr_metav_link + place-link orphan check - built, src, metav_index.db read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12C-DRY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP12C-DRY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
X=~/bible-db/metav_index.db
D=~/edition_upgrade_runs/step12c_dry_20261114
P="python3 scripts/build_person_metav_link.py"
E="python3 scripts/eu_step.py"
RD="SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'tipnr_metav_link' ORDER BY type, name; SELECT 'kind', kind, count(*) FROM tipnr_metav_link GROUP BY kind ORDER BY kind; SELECT 'rule', kind, rule, count(*) FROM tipnr_metav_link GROUP BY kind, rule ORDER BY kind, rule"
git diff --quiet "$REF" HEAD -- entity_resolution.py || { echo "STEP12C-DRY RESULT: STOP - entity_resolution.py differs from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- entity_resolution.py)" ] || { echo "STEP12C-DRY RESULT: STOP - entity_resolution.py has uncommitted edits on PA"; exit 1; }
echo "entity_resolution.py (the builder's import) = $REF, unedited: OK"
$E pre --tag STEP12C --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP12C-DRY RESULT: STOP - pre (line above); nothing made"; exit 1; }
mkdir "$D/aside" "$D/dryrun" "$D/applycopy" || { echo "STEP12C-DRY RESULT: STOP - cannot make the run's sub-folders; built untouched"; exit 1; }
LS0=""; for f in person_metav_link_residual.txt person_metav_link_tier2.txt; do
  if [ -f "scripts/$f" ]; then cp -p "scripts/$f" "$D/aside/" || { echo "STEP12C-DRY RESULT: STOP - cannot copy scripts/$f aside; built untouched"; exit 1; }; LS0="$LS0 $f=$(sha256sum < "scripts/$f" | cut -d' ' -f1)"; else LS0="$LS0 $f=absent"; fi
done
echo "untracked leftover lists in scripts/ (copied aside to $D/aside; the builder is pointed elsewhere):$LS0"
[ -s "$X" ] || { echo "STEP12C-DRY RESULT: STOP - $X missing or empty"; exit 1; }
[ -e "$X-journal" ] && { echo "STEP12C-DRY RESULT: STOP - a -journal sits beside $X"; exit 1; }
X0=$(sha256sum < "$X" | cut -d' ' -f1); echo "metav_index.db (read-only): $(stat -c %s "$X") bytes, sha256 $X0"
for f in "$B" "$S"; do
  echo "--- tipnr_metav_link on $f (read-only): definition + rows by kind + by kind/rule"
  sqlite3 -readonly "$f" "$RD" || { echo "STEP12C-DRY RESULT: STOP - tipnr_metav_link read failed on $f"; exit 1; }
done
echo "=== PLACE-LINK ORPHAN CHECK on built (read-only; must print 0) ==="
$P --bible "$B" --check-place-orphans; o=$?
[ "$o" -eq 0 ] || { echo "STEP12C-DRY RESULT: STOP - the place-link orphan check on built is not 0 (exit $o, above); built untouched"; exit 1; }
$E prep --tag STEP12C --built "$B" --dir "$D" --copy tipnr_entities,tipnr_entity_refs,metav_people,pn_binding,tipnr_metav_link --save tipnr_metav_link || { echo "STEP12C-DRY RESULT: STOP - prep (line above); built untouched"; exit 1; }
echo "=== DRY 1: the builder's dry run on the throwaway copy (leftover lists -> $D/dryrun) ==="
$P --bible "$D/dry.db" --index "$X" --out-dir "$D/dryrun" > "$D/dryrun.out" 2>&1; r=$?
cat "$D/dryrun.out"; echo "exit $r (expect 0)"
[ "$r" -eq 0 ] || { echo "STEP12C-DRY RESULT: STOP - the dry run failed on the copy (above); built untouched"; exit 1; }
grep -qF '[DRY-RUN] No table written.' "$D/dryrun.out" || { echo "STEP12C-DRY RESULT: STOP - the dry run did not report 'No table written'; built untouched"; exit 1; }
echo "=== DRY 2: --apply on the throwaway copy $D/dry.db (leftover lists -> $D/applycopy; built untouched) ==="
$P --bible "$D/dry.db" --index "$X" --out-dir "$D/applycopy" --apply > "$D/apply_dry.log" 2>&1; a=$?
cat "$D/apply_dry.log"; echo "exit $a (expect 0)"
[ "$a" -eq 0 ] || { echo "STEP12C-DRY RESULT: STOP - --apply failed on the copy (above); built untouched"; exit 1; }
grep -q "^Wrote [0-9]* kind='person' rows into tipnr_metav_link" "$D/apply_dry.log" || { echo "STEP12C-DRY RESULT: STOP - --apply did not report its write; built untouched"; exit 1; }
echo "--- files the builder wrote in its two scratch folders (sha256, lines):"
find "$D/dryrun" "$D/applycopy" -type f | sort | while read -r f; do echo "$(sha256sum < "$f" | cut -d' ' -f1)  $(wc -l < "$f") lines  ${f#"$D"/}"; done
echo "--- tipnr_metav_link on the dry copy after: definition + rows by kind + by kind/rule"
sqlite3 -readonly "$D/dry.db" "$RD" || { echo "STEP12C-DRY RESULT: STOP - tipnr_metav_link read failed on the dry copy; built untouched"; exit 1; }
echo "=== PLACE-LINK ORPHAN CHECK on the dry copy after --apply (must print 0) ==="
$P --bible "$D/dry.db" --check-place-orphans; o2=$?
[ "$o2" -eq 0 ] || { echo "STEP12C-DRY RESULT: STOP - the place-link orphan check on the dry copy is not 0 (exit $o2, above); built untouched"; exit 1; }
$E delta --tag STEP12C --a "$B" --b "$D/dry.db" --table tipnr_metav_link:uniq+kind --out "$D/step12c_delta_built.tsv" || { echo "STEP12C-DRY RESULT: STOP - delta built -> dry (line above); built untouched"; exit 1; }
$E delta --tag STEP12C --a "$S" --b "$D/dry.db" --table tipnr_metav_link:uniq+kind --out "$D/step12c_delta_src.tsv" || { echo "STEP12C-DRY RESULT: STOP - delta src -> dry (line above); built untouched"; exit 1; }
X1=$(sha256sum < "$X" | cut -d' ' -f1); echo "metav_index.db after: sha256 $X1 - unchanged: $([ "$X1" = "$X0" ] && echo yes || echo NO)"
[ "$X1" = "$X0" ] || { echo "STEP12C-DRY RESULT: STOP - metav_index.db changed during the run - report this, do not re-run"; exit 1; }
[ -e "$X-journal" ] && { echo "STEP12C-DRY RESULT: STOP - a -journal now sits beside $X"; exit 1; }
LS1=""; for f in person_metav_link_residual.txt person_metav_link_tier2.txt; do if [ -f "scripts/$f" ]; then LS1="$LS1 $f=$(sha256sum < "scripts/$f" | cut -d' ' -f1)"; else LS1="$LS1 $f=absent"; fi; done
echo "leftover lists after - unchanged: $([ "$LS1" = "$LS0" ] && echo yes || echo NO)"
[ "$LS1" = "$LS0" ] || { echo "STEP12C-DRY RESULT: STOP - a leftover list in scripts/ changed (copies in $D/aside) - report this"; exit 1; }
$E same --tag STEP12C --built "$B" --dir "$D" || { echo "STEP12C-DRY RESULT: STOP - built differs from its prep state (lines above)"; exit 1; }
echo "STEP12C-DRY RESULT: READ DONE - built untouched (same: OK); metav_index.db + leftover lists unchanged; place-link orphans 0 on built and on the copy; the dry run's counts, the two deltas above (files + sha on their DELTA lines) and the scratch files are the figures to declare for STEP12C-APPLY"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12C-DRY reviewed (11/14) — REVIEW: CLEAR

Verdict line verbatim: "REVIEW: CLEAR - read-only on built, src and metav_index.db; every write lands in the run folder; the wrapper and tripwires check out; no figure is asserted."
Reviewer spot-checked every line cite against the builder (all match). Built is touched only by the read-only orphan
check. The leftover lists are only copied aside and their sha read; `tipnr_metav_link_residual.txt` is not touched.
Goes straight to PA (read-only).

### STEP12C-DRY ran (11/14, 02:09 UTC, PA HEAD b3178672, REF 006e16ba) — READ DONE, exit 0, NOT +0/−0

Log `~/edition_upgrade_runs/step12c_dry_20261114.log`.
- **Guards and unchanged files:** entity_resolution.py = REF; PRE OK; leftover lists unchanged (residual 7c2233d2…,
  tier2 2b24b761…); metav_index.db 1,966,080 B, a438327f…, unchanged.
- **Place-link orphans:** 0 on built, 0 on the copy (the procedure's gate, met on both sides).
- **Prep:** 3,809,533 rows in 38 s; dry.db 4,628,480 B; the five copied tables = built.
- **Before:** tipnr_metav_link on built = src: 1,644 person rows (overlap 1,419 / strongs 225), no place rows.
- **Builder report:** tier 1 1,133; tier 2 1,473; demoted 26; residual 129; no metaV 371; of 3,132 person
  entities; 2,606 linked.
- **Trial apply:** wrote 2,606 (overlap 1,473 / strongs 1,133).
- **Delta built → dry = src → dry:** changed 0, added 962, removed 0; files 962 lines + header, sha c44c15d6….
  Scratch files identical across the two runs (residual 130 lines a247dfb2…, tier2 1,474 lines 1eed6313…).
- SAME OK.

Ruling chat (11/14): not +0/−0; the 1,644 existing rows are unchanged. STEP12C-APPLY not drafted. First: (1) the 962
by rule from the file; (2) a repo read of what accounts for 1,644 → 2,606; (3) the "7 expected" wording vs 26 listed.

### 1,644 → 2,606 — repo read (11/14, CC; from what was read, no cause asserted)

- **The builder's link inputs:** `tipnr_entities` (section, head, bases), `tipnr_entity_refs`, `metav_people`, and
  metav_index.db (`build_person_metav_link.py:129-145`, `:156-212`). `pn_binding` feeds only the traffic numbers
  (`:146-150`), not which links are made. **It never reads `words`.**
- **Does the 8b.2 Strong's rewrite feed tier 1? Not through this builder.** Tier 1 compares an entity's `bases`
  with metaV's Strong's set (`:168-174`). `bases` are written by `build_entity_binding.py:484` from the TIPNR file's
  own Strong's fields (`entity_resolution.py:592-594`, `:603-605`), not from `words`.
- **Builder code:** last logic change 7/05 (`a25d286c`); the only later commit, `1ad10cec` (11/07), adds
  `--bible`/`--out-dir`/`--check-place-orphans`. `build_metav_person_index.py`: unchanged since `00a1238e` (7/05).
- **Live's table history in the repo:** applied 2026-07-05 with **1,625** links — tier 1 202, tier 2 1,423, demoted 7,
  residual 56 (`HANDOFF_metav_person_link.md:4`, `:29-41`; `docs/claude/data-model.md:257`). Live now holds
  **1,644** (strongs 225 / overlap 1,419), so it changed after 7/05; **nothing in the repo records a later run.**
- **The entity table widened after that:** `7e465865` (2026-07-30) made `build_entity_binding.py --apply` write ALL
  parsed TIPNR entities, not only those used by a render bind (`:455-460`). Its pre-registered figures were 4,247
  entities / 3,132 persons / 31,975 refs. Tonight's prep and report show tipnr_entities 4,247, tipnr_entity_refs
  31,975, 3,132 person entities — the same figures. Also after 7/05: `import_tipnr.py` (7/16, en-dash
  sub-records), `entity_resolution.py` (7/16, 7/24 R-2).
- **Open, for data not code:** whether live's own inputs (src) give the same 2,606 links as built's. STEP12C-MEMBERS
  (2a) answers it exactly, by a trial apply on a copy of src's tables compared link by link with built's trial.

### "7 expected" and the DRY-RUN header — (3), from the code

- **"(7 expected)"** is fixed text in the print at `build_person_metav_link.py:301`, added in `b5b17bb0` (7/05),
  when the demoted bucket held 7 (`HANDOFF_metav_person_link.md:38`). The lines under it print EVERY member of the
  bucket (`:302-304`), so 26 listed = the bucket's size now, matching the tier report's "demoted 26" (`:236`). The
  label does not count anything, and no code checks it against 7.
- **"DRY-RUN three-tier report"** is printed at `:233`, before the `if not APPLY` branch at `:320`, so `--apply`
  prints the same header and then writes (`:326-343`). Both are fixed labels, with no effect on what is written.

### Block STEP12C-MEMBERS (GATE REF 006e16ba; READ-ONLY on built, src and metav_index.db — writes only its run folder and a throwaway copy of src's five tables)

(1) prints the 962 from `step12c_delta_built.tsv` (sha-checked c44c15d6…), counted by rule from the file's
after-column, then listed `uniq | metav_id | rule | score | margin` (also saved to `members_962.txt`).
(2a) copies src's five tables to a throwaway db (eu_step prep on src) and runs the same `--apply` there. It then
compares those links row by row with built's trial result (`step12c_dry_20261114/dry.db`), keyed on `uniq+kind`.
0 = live's own inputs give the same 2,606.
(2b) prints the builder's link inputs src → built: tipnr_entities by uniq, tipnr_entity_refs by
uniq+book+chapter+verse, metav_people by person_id.
Also: metav_index sha unchanged; `same` on src at the end.
Tested locally (planted entity on built only): (1) lists it as strongs; (2a) shows it as the one link src's inputs
don't make; (2b) shows it as the one added entity. A wrong delta file → STOP.

```bash
set +H
L=~/edition_upgrade_runs/step12c_members_20261114.log
if [ -e "$L" ]; then echo "STEP12C-MEMBERS RESULT: STOP - log already exists (kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12C-MEMBERS: the 962 added person links by rule + the builder's trial apply on a copy of SRC + src->built deltas of its inputs - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12C-MEMBERS RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db; S=~/bible-db/bible_edupg_test_20261101.db; X=~/bible-db/metav_index.db
DD=~/edition_upgrade_runs/step12c_dry_20261114; D=~/edition_upgrade_runs/step12c_members_20261114
T=$DD/step12c_delta_built.tsv; XD=c44c15d6fb088ef445854884d3db4d89a6d43f1904f8a3a9cb084289b2f209d2
P="python3 scripts/build_person_metav_link.py"; E="python3 scripts/eu_step.py"
git diff --quiet "$REF" HEAD -- entity_resolution.py || { echo "STEP12C-MEMBERS RESULT: STOP - entity_resolution.py differs from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- entity_resolution.py)" ] || { echo "STEP12C-MEMBERS RESULT: STOP - entity_resolution.py has uncommitted edits on PA"; exit 1; }
$E pre --tag STEP12CM --ref "$REF" --dir "$D" --db "$B" --db "$S" || { echo "STEP12C-MEMBERS RESULT: STOP - pre (line above)"; exit 1; }
s=$(sha256sum < "$T" | cut -d' ' -f1); echo "delta file $T: $(wc -l < "$T") lines (expect 963), sha256 $s (expect $XD)"
[ "$s" = "$XD" ] || { echo "STEP12C-MEMBERS RESULT: STOP - not the dry run's delta file"; exit 1; }
echo "=== (1) the 962 by rule, counted from the file's after-column ==="
awk -F'\t' 'NR>1 {k="other"; if ($6 ~ /, '"'"'strongs'"'"', /) k="strongs"; else if ($6 ~ /, '"'"'overlap'"'"', /) k="overlap"; c[$2" "k]++} END {for (x in c) print x, c[x]}' "$T" | sort
echo "--- the 962 (uniq | metav_id | rule | score | margin):"
sed -n "s/^tipnr_metav_link\tADDED\t.*\t(('\(.*\)', 'person', \([0-9]*\), '\([a-z]*\)', \([0-9.]*\), \([0-9.]*\), 1),)\$/\1 | \2 | \3 | \4 | \5/p" "$T" > "$D/members_962.txt"
cat "$D/members_962.txt"; echo "--- lines listed: $(wc -l < "$D/members_962.txt") (expect 962; the file holds every one either way)"
echo "=== (2a) the same builder --apply on a THROWAWAY copy of SRC's five tables (src = live 11/01; read-only) ==="
[ -e "$X-journal" ] && { echo "STEP12C-MEMBERS RESULT: STOP - a -journal sits beside $X"; exit 1; }
X0=$(sha256sum < "$X" | cut -d' ' -f1)
$E prep --tag STEP12CM --built "$S" --dir "$D" --copy tipnr_entities,tipnr_entity_refs,metav_people,pn_binding,tipnr_metav_link --save tipnr_metav_link || { echo "STEP12C-MEMBERS RESULT: STOP - prep of the src copy (line above); src untouched"; exit 1; }
mkdir "$D/srcrun" || { echo "STEP12C-MEMBERS RESULT: STOP - cannot make $D/srcrun"; exit 1; }
$P --bible "$D/dry.db" --index "$X" --out-dir "$D/srcrun" --apply > "$D/srcrun.out" 2>&1; r=$?
sed -n '1,9p' "$D/srcrun.out"; tail -1 "$D/srcrun.out"; echo "exit $r (expect 0)"
[ "$r" -eq 0 ] || { echo "STEP12C-MEMBERS RESULT: STOP - the trial apply on the src copy failed (above); src untouched"; exit 1; }
$E delta --tag STEP12CM --a "$DD/dry.db" --b "$D/dry.db" --table tipnr_metav_link:uniq+kind --out "$D/links_builtcopy_vs_srccopy.tsv" --show 20 || { echo "STEP12C-MEMBERS RESULT: STOP - delta (line above)"; exit 1; }
X1=$(sha256sum < "$X" | cut -d' ' -f1); echo "metav_index.db unchanged: $([ "$X1" = "$X0" ] && echo yes || echo NO)"
echo "=== (2b) the builder's link inputs, src -> built (read-only) ==="
$E delta --tag STEP12CM --a "$S" --b "$B" --table tipnr_entities:uniq --table tipnr_entity_refs:uniq+book+chapter+verse --table metav_people:person_id --out "$D/inputs_src_built.tsv" --show 20 || { echo "STEP12C-MEMBERS RESULT: STOP - input delta (line above)"; exit 1; }
$E same --tag STEP12CM --built "$S" --dir "$D" || { echo "STEP12C-MEMBERS RESULT: STOP - src differs from its prep state (lines above)"; exit 1; }
echo "STEP12C-MEMBERS RESULT: READ DONE - src untouched (same: OK); (1) the 962 by rule; (2a) links from src's inputs vs from built's inputs: the DELTA line above (0 = the same 2,606); (2b) input deltas src -> built above"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12C-MEMBERS reviewed (11/14) — REVIEW: CLEAR

Verdict line verbatim: "REVIEW: CLEAR - STEP12C-MEMBERS (ruling chat 11/14 items 1-3, DESIGN sec 9.90): reads built, src and metav_index.db only; the builder's --apply runs only on the throwaway copy $D/dry.db; wrapper and tripwires pass; the repo-read cites match the code."
Reviewer checked the file:line cites (all match). It could not open the commit cites; CC confirmed each with
`git log -1` on this checkout (a25d286c 7/05, 1ad10cec 11/07, 00a1238e 7/05, 7e465865 7/30, b5b17bb0 7/05).
Goes straight to PA (read-only).

### STEP12C-MEMBERS ran (11/14, 02:33 UTC, PA HEAD b3178672, REF 006e16ba) — READ DONE, exit 0

Log `~/edition_upgrade_runs/step12c_members_20261114.log`. PRE OK; delta file 963 lines, sha c44c15d6… = the dry run's.
- **(1) The 962 by rule, counted from the file:** `ADDED strongs 908`, `ADDED overlap 54` (the 908/54 split confirmed
  from the file). All 962 listed (`members_962.txt` in the run folder, 962 lines); every one score 1.0 / margin 1.0.
- **(2a) The same builder `--apply` on a throwaway copy of SRC's five tables:** prep 3,809,468 rows in 71 s;
  before.db 1,644 rows; the five copied tables = src's (pn_binding 15,446, digest 50e0d6ef1bac). Report: tier 1
  1,133 / tier 2 1,473 / demoted 26 / residual 129 / no metaV 371, of 3,132; wrote 2,606. Links built-copy →
  src-copy: 2,606 → 2,606, **changed 0, added 0, removed 0** (header-only file, sha c866c003…). metav_index.db unchanged.
- **(2b) Link inputs src → built:** tipnr_entities 4,247 → 4,247, tipnr_entity_refs 31,975 → 31,975, metav_people
  3,086 → 3,086 — 0 differences each. SAME OK (src untouched).

**Ruling chat reading (11/14):** live's own inputs already produce 2,606; the 962 are links live's table never
received after the 7/30 entity-table change (`7e465865`). Not an edition-upgrade effect.
**Observed, no ruling:** pn_binding on src 15,446 rows (50e0d6ef1bac) vs built 15,426 (b9c115b8b82c) — an input to the
traffic numbers only; not a 12c gate.
**Note on live's tipnr_metav_link (no action here, ruling 11/14):** live's table is 962 person links short of what
the current builder makes from live's own entity tables (alongside the 12b note on live's word_gloss).

**Ruling (11/14, §9.111):** the +962 is accepted as the declared figure for 12c. STEP12C-APPLY gated on the
STEP12C-DRY figures (below). Restore source `step12c_dry_20261114/before.db`.

## STEP12C-APPLY drafted (11/14)

Declared figures, all from the STEP12C-DRY log (02:09Z) as ruled:
- both dry delta files 963 lines (962 added, 0 changed, 0 removed), sha `c44c15d6…`;
- built unchanged since the dry run (`same` against `step12c_dry_20261114`);
- tipnr_metav_link on built before = the logged definition + index, 1,644 person rows (overlap 1,419 / strongs 225);
- the builder's six tier-report lines and `Wrote 2606 kind='person' rows into tipnr_metav_link (rule/score/margin recorded).`;
- after: same definition + index, 2,606 (overlap 1,473 / strongs 1,133);
- scratch files = the dry's (residual `a247dfb2…`, tier2 `1eed6313…`), exactly two files;
- place-link orphans 0 on built before the write (STOP) and after (CHECK);
- `check --written tipnr_metav_link`: 149 tables + schema = prep, tipnr_metav_link = the dry copy;
- src → built delta on `uniq+kind` with `--expect-sha c44c15d6…` (the same 962 adds);
- metav_index.db sha `a438327f…`, no journal, before (STOP) and after (CHECK);
- leftover lists in `scripts/` = the dry log's (residual `7c2233d2…`, tier2 `2b24b761…`) before (STOP) and after (CHECK);
- entity_resolution.py = REF, unedited (STOP).

The builder writes with `--out-dir $D/apply`, so it never writes the lists in `scripts/`. Its write
(`build_person_metav_link.py:320-343`) deletes and re-inserts only `kind='person'` rows; place rows are untouched. It
opens built with plain `sqlite3.connect` (no journal-mode change). One line is shown only, not gated: whether the
whole output equals the dry apply output with the scratch-folder path set aside.

Tested locally (made-up tables, one planted new person link): DONE, exit 0; output = the dry's apart from the path. Each
of these STOPs before the write: re-paste; built already written (`same` fails); a leftover list edited; a journal
beside metav_index.db. A wrong after-figure gives CHECK with the restore source named.

### Block STEP12C-APPLY (GATE REF 006e16ba; WRITES built: tipnr_metav_link person rows only, 1,644 → 2,606) — for the ruling chat

```bash
set +H
L=~/edition_upgrade_runs/step12c_apply_20261114.log
if [ -e "$L" ]; then echo "STEP12C-APPLY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP12C-APPLY rebuild-words step 12c (build_person_metav_link --apply) on BUILT, gated on the STEP12C-DRY figures (+962 ruled 11/14) - WRITES built: tipnr_metav_link person rows only (1,644 -> 2,606) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP12C-APPLY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP12C-APPLY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
X=~/bible-db/metav_index.db
DD=~/edition_upgrade_runs/step12c_dry_20261114
D=~/edition_upgrade_runs/step12c_apply_20261114
P="python3 scripts/build_person_metav_link.py"
E="python3 scripts/eu_step.py"
RD="SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'tipnr_metav_link' ORDER BY type, name; SELECT 'kind', kind, count(*) FROM tipnr_metav_link GROUP BY kind ORDER BY kind; SELECT 'rule', kind, rule, count(*) FROM tipnr_metav_link GROUP BY kind, rule ORDER BY kind, rule"
# --- declared figures: STEP12C-DRY log (11/14 02:09Z), ruled 11/14 ---
XD=c44c15d6fb088ef445854884d3db4d89a6d43f1904f8a3a9cb084289b2f209d2; XL=963
XX=a438327f01e023588ef8ada0fe2ff4bc9412dccba073c5491172907387478fd8
XLS=" person_metav_link_residual.txt=7c2233d22d3a900a5c5b99e55eec7aa84dc68c431c0f25625a9adb5c97817872 person_metav_link_tier2.txt=2b24b761d25940336aeb158cc0b900d1751c8b3b8348fac52b6fd9a274887960"
XF=$(printf '%s\n' "person_metav_link_residual.txt a247dfb2b9baeed7166122ea82c119ade68f6d72f8193e6d32a78e84d1e69ac1" "person_metav_link_tier2.txt 1eed6313ee343499f8094d3fef69a3d44d66595928809326a27bbe5e37fde66a")
XDEF=$(printf '%s\n' "index|ix_tipnr_metav_link|CREATE INDEX ix_tipnr_metav_link ON tipnr_metav_link(uniq)" "table|tipnr_metav_link|CREATE TABLE tipnr_metav_link(uniq TEXT, kind TEXT, metav_id INTEGER, rule TEXT, score REAL, margin REAL)")
XB=$(printf '%s\n' "$XDEF" "kind|person|1644" "rule|person|overlap|1419" "rule|person|strongs|225")
XA=$(printf '%s\n' "$XDEF" "kind|person|2606" "rule|person|overlap|1473" "rule|person|strongs|1133")
XO=$(printf '%s\n' "  Tier 1 Strong's-direct :  1133  (linked)" "  Tier 2 verse-overlap   :  1473  (linked)" "  name-only DEMOTED->resid:    26  (not linked)" "  RESIDUAL (hand-list)   :   129" "  no metaV record        :   371" "  ------ 3132 TIPNR person entities;  2606 LINKED" "Wrote 2606 kind='person' rows into tipnr_metav_link (rule/score/margin recorded).")
lists() { local o="" f; for f in person_metav_link_residual.txt person_metav_link_tier2.txt; do if [ -f "scripts/$f" ]; then o="$o $f=$(sha256sum < "scripts/$f" | cut -d' ' -f1)"; else o="$o $f=absent"; fi; done; echo "$o"; }
# --- before the write: every miss is STOP, built untouched ---
git diff --quiet "$REF" HEAD -- entity_resolution.py || { echo "STEP12C-APPLY RESULT: STOP - entity_resolution.py differs from $REF; built untouched"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- entity_resolution.py)" ] || { echo "STEP12C-APPLY RESULT: STOP - entity_resolution.py has uncommitted edits on PA; built untouched"; exit 1; }
echo "entity_resolution.py (the builder's import) = $REF, unedited: OK"
$E pre --tag STEP12CA --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP12C-APPLY RESULT: STOP - pre (line above); built untouched"; exit 1; }
for f in state.json before.db dry.db apply_dry.log step12c_delta_built.tsv step12c_delta_src.tsv; do [ -s "$DD/$f" ] || { echo "STEP12C-APPLY RESULT: STOP - the dry run's $f is missing or empty in $DD; built untouched"; exit 1; }; done
for f in step12c_delta_built.tsv step12c_delta_src.tsv; do
  s=$(sha256sum < "$DD/$f" | cut -d' ' -f1); n=$(wc -l < "$DD/$f")
  echo "dry delta $f: $n lines (expect $XL = header + 962 added), sha256 $s (expect $XD)"
  [ "$s" = "$XD" ] && [ "$n" = "$XL" ] || { echo "STEP12C-APPLY RESULT: STOP - $f is not the declared delta; built untouched"; exit 1; }
done
while read -r f x; do
  s=$(sha256sum < "$DD/applycopy/$f" | cut -d' ' -f1); echo "dry scratch file applycopy/$f: sha256 $s (expect $x)"
  [ "$s" = "$x" ] || { echo "STEP12C-APPLY RESULT: STOP - the dry run's $f is not the declared one; built untouched"; exit 1; }
done <<<"$XF"
$E same --tag STEP12CA --built "$B" --dir "$DD" || { echo "STEP12C-APPLY RESULT: STOP - built changed since the dry run (lines above); built untouched"; exit 1; }
[ -e "$X-journal" ] && { echo "STEP12C-APPLY RESULT: STOP - a -journal sits beside $X; built untouched"; exit 1; }
x0=$(sha256sum < "$X" | cut -d' ' -f1); echo "metav_index.db before: sha256 $x0 (expect $XX)"
[ "$x0" = "$XX" ] || { echo "STEP12C-APPLY RESULT: STOP - metav_index.db is not the one the dry run read; built untouched"; exit 1; }
LS0=$(lists); echo "leftover lists in scripts/ before:$LS0"
[ "$LS0" = "$XLS" ] || { echo "STEP12C-APPLY RESULT: STOP - the leftover lists in scripts/ are not the dry log's; built untouched"; exit 1; }
R0=$(sqlite3 -readonly "$B" "$RD") || { echo "STEP12C-APPLY RESULT: STOP - read before failed; built untouched"; exit 1; }
echo "tipnr_metav_link on built before:"; echo "$R0"
[ "$R0" = "$XB" ] || { echo "STEP12C-APPLY RESULT: STOP - built's tipnr_metav_link is not the dry log's picture (definition + index + 1644 rows by rule); built untouched"; exit 1; }
echo "=== PLACE-LINK ORPHAN CHECK on built before the write (read-only; must print 0) ==="
$P --bible "$B" --check-place-orphans; o0=$?
[ "$o0" -eq 0 ] || { echo "STEP12C-APPLY RESULT: STOP - the place-link orphan check on built is not 0 (exit $o0, above); built untouched"; exit 1; }
mkdir "$D/apply" || { echo "STEP12C-APPLY RESULT: STOP - cannot make the scratch folder; built untouched"; exit 1; }
# --- the one write ---
echo "=== APPLY: build_person_metav_link --apply on built (leftover lists -> $D/apply; the one write) ==="
$P --bible "$B" --index "$X" --out-dir "$D/apply" --apply > "$D/apply.log" 2>&1; r=$?
cat "$D/apply.log"; echo "exit $r (expect 0)"
# --- after the write: every miss is CHECK ---
SO=yes; while IFS= read -r x; do grep -qFx -- "$x" "$D/apply.log" || SO=NO; done <<<"$XO"
echo "the six tier-report lines + the Wrote 2606 line = the dry run's: $SO"
echo "whole output = the dry run's apply output, scratch-folder path aside (shown only): $(diff -q <(sed "s#$D/apply/#OUT/#" "$D/apply.log") <(sed "s#$DD/applycopy/#OUT/#" "$DD/apply_dry.log") > /dev/null && echo yes || echo no)"
SF=yes
while read -r f x; do s=$(sha256sum < "$D/apply/$f" | cut -d' ' -f1); echo "scratch file apply/$f: sha256 $s (expect $x)"; [ "$s" = "$x" ] || SF=NO; done <<<"$XF"
nf=$(find "$D/apply" -type f | wc -l); ne=$(wc -l <<<"$XF"); echo "files in $D/apply: $nf (expect $ne)"; [ "$nf" = "$ne" ] || SF=NO
R1=$(sqlite3 -readonly "$B" "$RD"); echo "tipnr_metav_link on built after:"; echo "$R1"
SA=NO; [ "$R1" = "$XA" ] && SA=yes; echo "definition + index + 2606 rows by rule = the dry copy's: $SA"
echo "=== PLACE-LINK ORPHAN CHECK on built after the write (read-only; must print 0) ==="
$P --bible "$B" --check-place-orphans; o1=$?
CHK=$($E check --tag STEP12CA --built "$B" --dir "$DD" --written tipnr_metav_link 2>&1); k=$?; echo "$CHK"
VAL=$($E delta --tag STEP12CA --a "$S" --b "$B" --table tipnr_metav_link:uniq+kind --out "$D/step12c_links_src_built.tsv" --expect-sha "$XD" 2>&1); v=$?; echo "$VAL"
x1=$(sha256sum < "$X" | cut -d' ' -f1); XS=yes; [ "$x1" = "$XX" ] || XS=NO; [ -e "$X-journal" ] && XS=NO
echo "metav_index.db after: sha256 $x1 - unchanged, no journal: $XS"
LS1=$(lists); LU=NO; [ "$LS1" = "$XLS" ] && LU=yes; echo "leftover lists in scripts/ after - unchanged: $LU"
if [ "$r" -eq 0 ] && [ "$SO" = yes ] && [ "$SF" = yes ] && [ "$SA" = yes ] && [ "$o1" -eq 0 ] && [ "$k" -eq 0 ] && [ "$v" -eq 0 ] && [ "$XS" = yes ] && [ "$LU" = yes ]; then
  echo "STEP12C-APPLY RESULT: DONE - built tipnr_metav_link person rows re-written: 2,606 (overlap 1,473 / strongs 1,133) = the dry run; vs src exactly the 962 declared additions (0 changed / 0 removed); place-link orphans 0; the other 149 tables + schema unchanged; metav_index.db + leftover lists unchanged"; exit 0
fi
echo "STEP12C-APPLY RESULT: CHECK - an after-figure differs (lines above). Restore source for tipnr_metav_link: $DD/before.db"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP12C-APPLY reviewed (11/14) — REVIEW: ESCALATE (write), mechanics clean

Verdict line verbatim: "REVIEW: ESCALATE - STEP12C-APPLY writes built (person rows in tipnr_metav_link, via `build_person_metav_link.py --apply`), so under DESIGN sec 9.90 the ruling chat must clear it. I found no mechanical defects."
Reviewer checked the figures against the record and §9.111, STOP-before / CHECK-after, the builder's write paths, the
eu_step flags, the tripwires and bash validity. Its two open items, closed by CC from the pasted STEP12C-DRY log:
- **full shas:** every 64-character sha in the block is copied from that log (delta, metav_index.db, leftover lists,
  scratch files);
- **definition text:** the dry log printed `index|ix_tipnr_metav_link|CREATE INDEX ix_tipnr_metav_link ON tipnr_metav_link(uniq)`
  and `table|tipnr_metav_link|CREATE TABLE tipnr_metav_link(uniq TEXT, kind TEXT, metav_id INTEGER, rule TEXT, score REAL, margin REAL)`
  on built, src and the dry copy after `--apply`; XDEF is those two lines exactly.
Goes to the ruling chat for the write gate (§9.111).

### STEP12C-APPLY ran (11/14, 18:08 UTC, PA HEAD b3178672, REF 006e16ba) — DONE, exit 0 → STEP 12c CLOSED; step 12 complete (§9.111 closing)

Log `~/edition_upgrade_runs/step12c_apply_20261114.log`; run folder `step12c_apply_20261114/` (apply.log, apply/
scratch files, step12c_links_src_built.tsv). Write gate: the 11/14 +962 ruling stands as the §9.111 call.
entity_resolution.py = REF, unedited; PRE OK; both dry deltas 963 lines / c44c15d6…; dry scratch shas a247dfb2… /
1eed6313… matched; SAME OK (150 + schema, 0); metav_index.db a438327f… before, no journal; leftover lists in scripts/
7c2233d2… / 2b24b761… before; tipnr_metav_link before = declared (logged definition + index; 1,644: overlap 1,419 /
strongs 225); place-link orphans 0 before. Builder exit 0; the six tier-report lines + "Wrote 2606…" = dry; whole
output = dry, scratch-folder path aside. Scratch files 2, shas = declared. After = declared (2,606: overlap 1,473 /
strongs 1,133; definition + index unchanged). Place-link orphans 0 after. CHECK OK: 149 untouched + schema 0;
tipnr_metav_link 2,606 rows, fingerprint c9676803c1c4 = dry copy (prep 1,644, fd14ff7adc86). Links src → built:
0 changed / 962 added / 0 removed, file sha c44c15d6… = the dry delta. metav_index.db after unchanged, no journal;
leftover lists unchanged. Restore source not needed (`step12c_dry_20261114/before.db` kept until the swap).

## Step 9 → 9a → 9b → 9c — CC report (11/14) + STEP9-DRY drafted

**What each step does (rebuild-words.md 278-315; charter §6, §4.8-4.9), and whether it writes built:**
- **9 — rebuild abp_surface. WRITES built: abp_surface only.** Four scripts in order on `<built>`, all reading
  built's own verses / words / lexicon / dotted_lexicon plus `~/bible-db/bh_scrape.db`:
  `build_abp_surface.py` (drops the table, re-creates it, inserts the form-found rows; :297-304),
  `backfill_abp_surface.py --apply` (adds rows the strict aligner missed; insert-only, :137),
  `backfill_pn_surface.py --apply` (adds name-slot rows; insert-only, :339; imports `entity_resolution.py`
  through `build_pn_greek_identity.py`:33-34), `build_abp_translit.py` (fills the translit column; :98).
  The drop removes the 10/25 fill (4,411 slots). The procedure's total 391,130 is the same-code figure; on this
  lane it is re-declared from the dry run (charter §6).
- **9a — put the fill back. WRITES built: abp_surface only.** `restore_surface_fill.py`: dry run → verdict →
  `--apply`; re-keys the frozen 10/25 fill (4,411 = 3,873 inserts + 538 updates) onto the new slots by key 2
  (verse + Strong's + ordinal), key 1 (verse + Strong's + old English) as the check; all or nothing.
  Charter §4.9: no `--prefill`; reason 6 expected large; the reason-6 member list read against the changed-English
  verses; JP's choice at that verdict (key 2 alone inside changed verses, declared, or leave to a follow-up).
- **9b — floor check. Writes nothing.** `health_check.py <built> --no-backup-check --no-disk-check`, the
  `abp_surface rows BELOW floor` line; floor re-declared (charter §6).
- **9c — re-freeze. Writes no database; writes repo files.** `snapshot_surface_fill.py --replace` re-freezes the
  fill from built (new TSV + `.sha256`), the pin in `restore_surface_fill.py` updated in the same commit; §9.87
  re-freezes the punct member file from built in that same commit.

**Finding — 9a, 9b and 9c run code with the 10/25 figures written in; step 9 does not.** Read in the repo at REF:
- `restore_surface_fill.py`:63-64 fixes 391,130 / 395,003 / 4,411 / 3,873 / 538. :291-294: a table that is neither
  391,130 nor 395,003 STOPs before the re-key, so **the 9a dry run cannot run on built unless step 9 lands on
  391,130 exactly.** :360 + :366-371: any unplaced slot writes nothing (G2), so §4.9's "key 2 alone on reason-6
  slots" cannot be expressed. :243: after-count fixed at 395,003.
- `health_check.py`:144 floor fixed at 395,003.
- `snapshot_surface_fill.py`:56 fixes 4,411; its G0 (`dryrun_rekey_fill.py`:57-58, :266-293) requires the fill =
  source minus pre-fill = the approved 10/25 CSV, keyed at the OLD slots — a re-freeze from built cannot pass it.
  Its inputs are "source with the fill" + "pre-fill copy"; for built that pair would be built after 9a + built's
  step-9 table (before 9a). Charter §6 words the before side as `<src>`; that needs reading against the script.
So a code change is needed before 9a's dry run (and for 9b/9c). It is a design item for the ruling chat; CC
drafts it once STEP9-DRY gives the chain total. Step 9 itself has no figure in code, so its dry run can go now.

**§9.87 punct figure (583 vs 607) — where it stands:**
- 583 = unchanged 204 + new-on-eligible 367 + changed-ops 12 (gone 25): gate 3, 11/4,
  `~/edition_upgrade_runs/gate3_member_diff_20261104.log`. §9.87 stands at 583.
- 607 = unchanged 205 + new-on-eligible 390 + changed-ops 12 (gone 24): G3R, 11/6,
  `~/edition_upgrade_runs/gate3_rerun_20261106.log`. CC's reading (DRAFT 2498-2504): +24 = 23 new-on-eligible from
  R2 (the 23 verses named there) + Num 8:26 gone → unchanged; changed-ops the same 12. Not ruled (§9.91).
- That reading was made from the two printed lists, not shown by a block. Built has changed since 11/6 (8b.0-8b.3,
  REKEY, SLOT3, the §9.96 restore, steps 11/10/12; 8b.2a re-wrote English in 16 verses). The figure that gets
  frozen is built's at 9c time. So what is needed is a read-only block that (1) takes the member lists out of the
  two logs and lists every member that moved (expect exactly the 24 named), and (2) re-runs the gate-3 v2 member
  diff on today's built (same punct file `2b0f4cc4…`, eligible `e540d34d…`) and lists every member that moved since
  11/6. Gate 3 reads no abp_surface (0 mentions in `audit_reassembly_diff.py`), so this read can run beside step
  9. Not drafted yet.

**STEP9-DRY** (`step9_dry_20261114`): the step-9 chain on a throwaway copy of built's five tables AND on a
throwaway copy of src's (the same-code control). Read-only on built, src, bh_scrape.db and the pre-fill copy.
Prints each pass's counts (and checks NEW = rows written; the PN arithmetic line; table = the sum of the three passes);
abp_surface definition / rows / blanks / rows with no word at their slot, before and after; four deltas keyed
verse_id+position: built → its copy (what STEP9-APPLY would write), src → its copy (expect the fill coming out:
removed 3,873 / changed 538 / added 0, if live's words are as on 10/25), pre-fill copy → src's copy (expect 0, the
G1b oracle), src's copy → built's copy (the edition's effect). bh_scrape.db sha before/after; `same` on built and
src. Saves built's abp_surface (395,003 rows) to `before.db` as the restore source.
Local test (made-up dbs, fake HOME): clean run READ DONE, exit 0; src → its copy = the planted fill exactly
(1 removed / 1 changed), pre-fill → src's copy 0; re-paste, missing scrape, failed builder each STOP, built untouched.
Disk (estimate, not measured): two copies of words + verses + abp_surface, roughly 200-250 MB each (step 11's copy with words was 192 MB) + two small before.db files.

### Block STEP9-DRY (GATE REF 006e16ba; READ-ONLY on built, src, bh_scrape.db and the pre-fill copy — writes only its run folder and two throwaway copies)
```bash
set +H
L=~/edition_upgrade_runs/step9_dry_20261114.log
if [ -e "$L" ]; then echo "STEP9-DRY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP9-DRY rebuild-words step 9 (surface builder + both backfills + translit) on THROWAWAY copies of built's and src's verses/words/lexicon/dotted_lexicon/abp_surface - built, src, bh_scrape.db, the pre-fill copy read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9-DRY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP9-DRY RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
H=~/bible-db/bh_scrape.db
PF=~/bible.db.pre-surface-fill-20261025
D=~/edition_upgrade_runs/step9_dry_20261114
E="python3 scripts/eu_step.py"
T=verses,words,lexicon,dotted_lexicon,abp_surface
RD="SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'abp_surface' ORDER BY type, name; SELECT 'rows', count(*), 'blank form', sum(form IS NULL OR form = ''), 'blank translit', sum(translit IS NULL OR translit = '') FROM abp_surface; SELECT 'rows with no word at their slot', count(*) FROM abp_surface s WHERE NOT EXISTS (SELECT 1 FROM words w WHERE w.verse_id = s.verse_id AND w.position = s.position)"
num() { grep -m1 -F -- "$2" "$1" | sed 's/.*: *//; s/,//g; s/[^0-9].*//'; }
dlt() { grep -m1 -o 'delta [0-9,]*' "$1" | tr -d 'delta ,'; }
# the step-9 chain, rebuild-words.md step 9, in order, on ONE throwaway copy ($1); outputs kept in $2
chain() {
  local db=$1 o=$2 n1 n2 d2 n3 d3 a3 m3 nt nr
  echo "--- 1/4 build_abp_surface (drops + re-creates abp_surface on the copy)"
  python3 scripts/build_abp_surface.py "$db" --bh "$H" > "$o/1_build.out" 2>&1 || { cat "$o/1_build.out"; echo "chain: build_abp_surface failed"; return 1; }
  grep -E "form found|shows a line|books with no source|Wrote" "$o/1_build.out"
  n1=$(grep -m1 -o 'Wrote [0-9]* rows' "$o/1_build.out" | tr -dc 0-9); [ -n "$n1" ] || { echo "chain: no Wrote line"; return 1; }
  echo "--- 2/4 backfill_abp_surface --apply"
  python3 scripts/backfill_abp_surface.py "$db" --bh "$H" --apply > "$o/2_backfill.out" 2>&1 || { cat "$o/2_backfill.out"; echo "chain: backfill_abp_surface failed"; return 1; }
  grep -E "existing rows|NEW rows|same-as-dictionary|ambiguity|Wrote" "$o/2_backfill.out"
  n2=$(num "$o/2_backfill.out" "NEW rows to add"); d2=$(dlt "$o/2_backfill.out")
  [ -n "$n2" ] && [ "$n2" = "$d2" ] || { echo "chain: backfill NEW ($n2) != rows written ($d2)"; return 1; }
  echo "--- 3/4 backfill_pn_surface --apply (refused slots -> $o/pn_refused.tsv)"
  python3 scripts/backfill_pn_surface.py "$db" --bh "$H" --apply --dump-refused "$o/pn_refused.tsv" > "$o/3_pn.out" 2>&1 || { cat "$o/3_pn.out"; echo "chain: backfill_pn_surface failed"; return 1; }
  sed -n '1,/coverage by book/p' "$o/3_pn.out" | grep -v "coverage by book"; grep -E "refused-slot dump|Wrote" "$o/3_pn.out"
  n3=$(num "$o/3_pn.out" "NEW rows to add"); d3=$(dlt "$o/3_pn.out")
  [ -n "$n3" ] && [ "$n3" = "$d3" ] || { echo "chain: PN backfill NEW ($n3) != rows written ($d3)"; return 1; }
  a3=$(grep -m1 'arithmetic:' "$o/3_pn.out" | sed 's/.*= *//; s/ .*//; s/,//g'); m3=$(grep -m1 'arithmetic:' "$o/3_pn.out" | sed 's/.*must equal *//; s/[^0-9,].*//; s/,//g')
  [ -n "$a3" ] && [ "$a3" = "$m3" ] || { echo "chain: PN arithmetic $a3 != $m3"; return 1; }
  echo "--- 4/4 build_abp_translit"
  python3 scripts/build_abp_translit.py "$db" > "$o/4_translit.out" 2>&1 || { cat "$o/4_translit.out"; echo "chain: build_abp_translit failed"; return 1; }
  cat "$o/4_translit.out"
  nt=$(grep -m1 -o 'Filled [0-9]*' "$o/4_translit.out" | tr -dc 0-9)
  nr=$(sqlite3 -readonly "$db" "SELECT count(*) FROM abp_surface") || { echo "chain: count failed"; return 1; }
  echo "chain total: builder $n1 + backfill $n2 + PN backfill $n3 = $((n1 + n2 + n3)); table now $nr; romanized $nt"
  [ "$nr" = "$((n1 + n2 + n3))" ] || { echo "chain: table count is not the sum of the three passes"; return 1; }
  echo "$n1 $n2 $n3 $nr $nt" > "$o/figures.txt"
}
# --- guards (read-only) ---
git diff --quiet "$REF" HEAD -- entity_resolution.py || { echo "STEP9-DRY RESULT: STOP - entity_resolution.py (imported by the PN backfill) differs from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- entity_resolution.py)" ] || { echo "STEP9-DRY RESULT: STOP - entity_resolution.py has uncommitted edits on PA"; exit 1; }
echo "entity_resolution.py (imported by the PN backfill) = $REF, unedited: OK"
$E pre --tag STEP9 --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP9-DRY RESULT: STOP - pre (line above); nothing made"; exit 1; }
[ -s "$H" ] || { echo "STEP9-DRY RESULT: STOP - $H missing or empty"; exit 1; }
[ -e "$H-journal" ] && { echo "STEP9-DRY RESULT: STOP - a -journal sits beside $H"; exit 1; }
H0=$(sha256sum < "$H" | cut -d' ' -f1); echo "bh_scrape.db (read-only): $(stat -c %s "$H") bytes, sha256 $H0"
if [ -s "$PF" ]; then echo "pre-fill copy (read-only): $PF, $(stat -c %s "$PF") bytes, $(date -u -r "$PF" +%FT%TZ)"; else echo "pre-fill copy: MISSING at $PF (charter 7 keeps it until 9c) - the same-code control below is skipped"; fi
for f in "$B" "$S"; do echo "--- abp_surface on $f (read-only): definition + rows + blanks + rows with no word at their slot"; sqlite3 -readonly "$f" "$RD" || { echo "STEP9-DRY RESULT: STOP - read failed on $f"; exit 1; }; done
# --- built's copy ---
$E prep --tag STEP9 --built "$B" --dir "$D" --copy "$T" --save abp_surface || { echo "STEP9-DRY RESULT: STOP - prep of built's copy (line above); built untouched"; exit 1; }
mkdir "$D/built_run" "$D/src" "$D/src_run" || { echo "STEP9-DRY RESULT: STOP - cannot make the sub-folders; built untouched"; exit 1; }
echo "=== DRY A: the step-9 chain on the throwaway copy of BUILT ($D/dry.db) ==="
chain "$D/dry.db" "$D/built_run" || { echo "STEP9-DRY RESULT: STOP - the chain on built's copy stopped (above); built untouched"; exit 1; }
# --- src's copy: the same-code control (src = live 11/01) ---
$E prep --tag STEP9 --built "$S" --dir "$D/src" --copy "$T" --save abp_surface || { echo "STEP9-DRY RESULT: STOP - prep of src's copy (line above); src untouched"; exit 1; }
echo "=== DRY B: the same chain on the throwaway copy of SRC ($D/src/dry.db) - the same-code control ==="
chain "$D/src/dry.db" "$D/src_run" || { echo "STEP9-DRY RESULT: STOP - the chain on src's copy stopped (above); src untouched"; exit 1; }
read -r a1 a2 a3 ar at < "$D/built_run/figures.txt"; read -r b1 b2 b3 br bt < "$D/src_run/figures.txt"
echo "same-code control on src: builder $b1 / backfill $b2 / PN backfill $b3 / total $br (the 10/25 figures: 346111 / 13183 / 31836 / 391130 - same code on live's own words)"
echo "built: builder $a1 / backfill $a2 / PN backfill $a3 / total $ar (to declare for STEP9-APPLY; not 391,130 by design)"
for f in "$D/dry.db" "$D/src/dry.db"; do echo "--- abp_surface on $f after the chain"; sqlite3 -readonly "$f" "$RD" || { echo "STEP9-DRY RESULT: STOP - read failed on $f"; exit 1; }; done
echo "=== DELTAS (abp_surface, key verse_id+position; every row in the file, first 20 printed) ==="
echo "expect: built -> its dry copy = unknown (read; what STEP9-APPLY writes) | src -> its dry copy = the fill coming out: removed 3,873 (its inserts) / changed 538 (its updates) / added 0, IF live's words are as on 10/25 | pre-fill copy -> src's dry copy = 0 (the G1b oracle) | src's dry copy -> built's dry copy = the edition's effect on the chain (read)"
$E delta --tag STEP9 --a "$B" --b "$D/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_built.tsv" --show 20 || { echo "STEP9-DRY RESULT: STOP - delta built -> dry (line above); built untouched"; exit 1; }
$E delta --tag STEP9 --a "$S" --b "$D/src/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_src.tsv" --show 20 || { echo "STEP9-DRY RESULT: STOP - delta src -> src dry (line above)"; exit 1; }
if [ -s "$PF" ]; then
  $E delta --tag STEP9 --a "$PF" --b "$D/src/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_prefill_srcdry.tsv" --show 20 || { echo "STEP9-DRY RESULT: STOP - delta pre-fill -> src dry (line above)"; exit 1; }
fi
$E delta --tag STEP9 --a "$D/src/dry.db" --b "$D/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_srcdry_builtdry.tsv" --show 20 || { echo "STEP9-DRY RESULT: STOP - delta src dry -> built dry (line above)"; exit 1; }
# --- after: everything read-only stayed as it was ---
H1=$(sha256sum < "$H" | cut -d' ' -f1); echo "bh_scrape.db after: sha256 $H1 - unchanged: $([ "$H1" = "$H0" ] && echo yes || echo NO)"
[ "$H1" = "$H0" ] || { echo "STEP9-DRY RESULT: STOP - bh_scrape.db changed during the run - report this, do not re-run"; exit 1; }
[ -e "$H-journal" ] && { echo "STEP9-DRY RESULT: STOP - a -journal now sits beside $H"; exit 1; }
$E same --tag STEP9 --built "$B" --dir "$D" || { echo "STEP9-DRY RESULT: STOP - built differs from its prep state (lines above)"; exit 1; }
$E same --tag STEP9 --built "$S" --dir "$D/src" || { echo "STEP9-DRY RESULT: STOP - src differs from its prep state (lines above)"; exit 1; }
echo "copies: $D/dry.db $(stat -c %s "$D/dry.db") bytes, $D/src/dry.db $(stat -c %s "$D/src/dry.db") bytes"
echo "STEP9-DRY RESULT: READ DONE - built + src untouched (same: OK); bh_scrape.db unchanged; built's chain total $ar, src's $br; the deltas above (files + sha on their lines) and the pass figures are what STEP9-APPLY declares"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9-DRY reviewed (11/14) — REVIEW: CLEAR

Verdict line verbatim: "REVIEW: CLEAR - read-only block: built, src, bh_scrape.db and the pre-fill copy are only read, all writes go to throwaway copies or new files under ~/edition_upgrade_runs, and the expected figures trace to code and the procedure file"
Reviewer notes (not blockers): the 391,130 control and the pre-fill 0 are printed, not enforced — read them by eye in
the log; free disk is not checked and the per-copy size is an estimate.

### Ruling (11/14, §9.112) — step 9 report logged; 9a/9b/9c code item logged (ruled after STEP9-DRY); punct block ordered; STEP9-DRY cleared

## PUNCT-RECON drafted (11/14, §9.112) — 583 vs 607, member by member

Part 1 reads only the two PA logs (`gate3_member_diff_20261104.log`, `gate3_rerun_20261106.log`): it takes every
`[gone]` / `[new-eligible]` / `[new-NOT-elig]` / `[changed-ops]` line, marks every other frozen ref "unchanged",
checks the lists add up to each log's own "to ruling:" line (else STOP), and lists every ref whose class differs
11/4 → 11/6 (expect 24: 23 absent → new-eligible + Num 8:26 gone → unchanged; members 583 → 607), plus refs
new-eligible on both sides whose printed ops differ. Part 2 re-runs gate 3 exactly as G3R did (port test, the
member diff's tests, v2 controls, then the member diff on built with the same punct file 2b0f4cc4… and eligible
e540d34d…) and lists every move 11/6 → today (expected: unknown). Gate-3 code (`audit_reassembly_diff.py`,
`reorder_english.py`, its tests and fixtures) is unchanged f8e814c2 → 006e16ba, so any move is from built's data.
Exit 1 from the member diff (a hard-fail class non-empty, as on 11/6: content-other Job 3:3) is read, not a STOP.
Built is opened read-only by the diff; its size + time are printed before and after.
Local test (made-up logs + db, punct/eligible fingerprints swapped for the fakes'): every class exercised
(unchanged, gone, changed-ops, new-eligible, new-NOT-elig, absent), READ DONE, exit 0; re-paste STOP; a log with one
list line removed → "do not add up to the log's own summary line" STOP.

### Block PUNCT-RECON (GATE REF 006e16ba; READ-ONLY — writes only its run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/punct_recon_20261114.log
if [ -e "$L" ]; then echo "PUNCT-RECON RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - PUNCT-RECON sec 9.87/9.91 punct members: (1) the 11/4 and 11/6 gate-3 logs member by member (no db) (2) the gate-3 v2 member diff re-run on today's built vs 11/6 - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "PUNCT-RECON RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "PUNCT-RECON RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
F=tests/fixtures/reassembly/punct_members_live_20261030.txt
E=~/edition_upgrade_runs/step5_eligible_20261101.tsv
L1=~/edition_upgrade_runs/gate3_member_diff_20261104.log
L2=~/edition_upgrade_runs/gate3_rerun_20261106.log
D=~/edition_upgrade_runs/punct_recon_20261114
export LC_ALL=C
python3 scripts/eu_step.py pre --tag PUNCT --ref "$REF" --dir "$D" --db "$B" || { echo "PUNCT-RECON RESULT: STOP - pre (line above); nothing made"; exit 1; }
for f in "$F" "$E" "$L1" "$L2"; do [ -s "$f" ] || { echo "PUNCT-RECON RESULT: STOP - missing or empty: $f"; exit 1; }; done
[ "$(sha256sum < "$F" | cut -d' ' -f1)" = 2b0f4cc43efc6dd423d934d4633727f69fcb6f45f894727b3a634265b68a941f ] || { echo "PUNCT-RECON RESULT: STOP - frozen punct file is not the committed one (2b0f4cc4...)"; exit 1; }
[ "$(sha256sum < "$E" | cut -c1-8)" = e540d34d ] || { echo "PUNCT-RECON RESULT: STOP - eligible file is not step 5's (e540d34d...)"; exit 1; }
sed -n 's/^ *\[punct-position *\] \([^ ]* [0-9]*:[0-9]*\) .*/\1/p' "$F" | sort -u > "$D/frozen.txt"
nf=$(wc -l < "$D/frozen.txt"); echo "frozen punct file: $nf members (expect 241; sha 2b0f4cc4 as committed) - eligible file sha e540d34d"
[ "$nf" = 241 ] || { echo "PUNCT-RECON RESULT: STOP - frozen file did not read as 241 members"; exit 1; }
# one gate-3 log -> $D/<n>_status.tsv (ref, class) over the frozen refs + every listed ref; prints the counts and the
# member total (members = unchanged + changed-ops + new-eligible + new-NOT-elig; gone drop out)
status() {
  local log=$1 n=$2 k s g ne nn co un mem
  [ "$(grep -c '^V2 MEMBER DIFF:' "$log")" = 1 ] || { echo "$n: the log does not hold exactly one member-diff summary"; return 1; }
  sed -n 's/^ *\[\(gone\|new-eligible\|new-NOT-elig\|changed-ops\) *\] \([^ ]* [0-9]*:[0-9]*\) .*/\2\t\1/p' "$log" | sort > "$D/${n}_listed.tsv"
  k=$(cut -f1 "$D/${n}_listed.tsv" | uniq -d | wc -l); [ "$k" = 0 ] || { echo "$n: $k ref(s) listed twice"; return 1; }
  awk -F'\t' 'FNR==NR {fz[$1] = 1; next} {c[$1] = $2} END {for (r in fz) if ((r in c) == 0) c[r] = "unchanged"; for (r in c) print r "\t" c[r]}' "$D/frozen.txt" "$D/${n}_listed.tsv" | sort > "$D/${n}_status.tsv"
  g=$(grep -c $'\tgone$' "$D/${n}_status.tsv"); ne=$(grep -c $'\tnew-eligible$' "$D/${n}_status.tsv"); nn=$(grep -c $'\tnew-NOT-elig$' "$D/${n}_status.tsv")
  co=$(grep -c $'\tchanged-ops$' "$D/${n}_status.tsv"); un=$(grep -c $'\tunchanged$' "$D/${n}_status.tsv"); mem=$((un + co + ne + nn))
  s=$(sed -n 's/^V2 MEMBER DIFF:.*| to ruling: //p' "$log")
  echo "$n summary line: $s"
  echo "$n from the lists: gone $g - new on eligible $ne - new on NON-eligible $nn - changed ops $co - unchanged $un (241 - gone - changed) => punct members $mem"
  [ "$s" = "gone $g - new on eligible $ne - changed ops $co - unchanged $un" ] || { echo "$n: the listed members do not add up to the log's own summary line"; return 1; }
  awk -F'\t' '$2 != "gone" {print $1}' "$D/${n}_status.tsv" > "$D/${n}_members.txt"
  sed -n 's/^ *\[new-eligible *\] \([^ ]* [0-9]*:[0-9]*\) *\(.*\)$/\1\t\2/p' "$log" | sort > "$D/${n}_newops.tsv"
}
# two status files -> every ref whose class differs (absent = not a member and not in the frozen file)
moved() {
  join -t $'\t' -a1 -a2 -e absent -o 0,1.2,2.2 "$D/$1_status.tsv" "$D/$2_status.tsv" | awk -F'\t' '$2 != $3' > "$D/moved_$1_$2.tsv"
  echo "--- refs whose class differs, $1 -> $2: $(wc -l < "$D/moved_$1_$2.tsv") (ref | $1 | $2); by move:"
  cut -f2,3 "$D/moved_$1_$2.tsv" | sort | uniq -c | sed 's/\t/ -> /'
  sed 's/\t/ | /g; s/^/    /' "$D/moved_$1_$2.tsv"
  echo "--- new-eligible on both sides with different printed ops, $1 -> $2: $(join -t $'\t' "$D/$1_newops.tsv" "$D/$2_newops.tsv" | awk -F'\t' '$2 != $3' | tee "$D/opsdiff_$1_$2.tsv" | wc -l)"
  sed 's/\t/ | /g; s/^/    /' "$D/opsdiff_$1_$2.tsv"
}
echo "=== PART 1: the two printed logs, member by member (no db) ==="
status "$L1" g3_1104 || { echo "PUNCT-RECON RESULT: STOP - 11/4 log (line above)"; exit 1; }
status "$L2" g3_1106 || { echo "PUNCT-RECON RESULT: STOP - 11/6 log (line above)"; exit 1; }
echo "expect: 11/4 members 583 (204 + 367 + 12), 11/6 members 607 (205 + 390 + 12); 24 moves: 23 absent -> new-eligible (the R2 verses named in DRAFT 2498-2504) + Num 8:26 gone -> unchanged"
moved g3_1104 g3_1106
echo "=== PART 2: the gate-3 v2 member diff re-run on today's built (read-only) ==="
b0=$(stat -c '%s bytes, modified %y' "$B"); echo "built before: $b0"
python3 tests/test_reorder_port.py || { echo "PUNCT-RECON RESULT: STOP - reorder port drifted from the JS baseline"; exit 1; }
python3 tests/test_reassembly_member_diff.py || { echo "PUNCT-RECON RESULT: STOP - the member diff's own tests failed"; exit 1; }
python3 scripts/audit_reassembly_diff.py --controls --v2 || { echo "PUNCT-RECON RESULT: STOP - v2 controls did not fire"; exit 1; }
PYTHONIOENCODING=utf-8 python3 scripts/audit_reassembly_diff.py "$B" --v2 --punct-members "$F" --eligible "$E" > "$D/g3_today.out" 2>&1; r=$?
cat "$D/g3_today.out"; echo "member diff exit $r (1 = a hard-fail class is non-empty, as on 11/6: content-other Job 3:3; 2 = it could not run)"
[ "$r" -le 1 ] || { echo "PUNCT-RECON RESULT: STOP - the member diff did not run (exit $r)"; exit 1; }
status "$D/g3_today.out" g3_today || { echo "PUNCT-RECON RESULT: STOP - today's output (line above)"; exit 1; }
echo "expect: 11/6 -> today = unknown (built changed since 11/6: 8b.0-8b.3, REKEY, SLOT3, the 9.96 restore, steps 11/10/12); every move is listed"
moved g3_1106 g3_today
b1=$(stat -c '%s bytes, modified %y' "$B"); echo "built after: $b1 - unchanged: $([ "$b1" = "$b0" ] && echo yes || echo NO)"
[ "$b1" = "$b0" ] || { echo "PUNCT-RECON RESULT: STOP - built's size or time changed during a read-only run - report this"; exit 1; }
echo "PUNCT-RECON RESULT: READ DONE - 11/4 members $(wc -l < "$D/g3_1104_members.txt"), 11/6 $(wc -l < "$D/g3_1106_members.txt"), today $(wc -l < "$D/g3_today_members.txt"); moves 11/4->11/6 $(wc -l < "$D/moved_g3_1104_g3_1106.tsv"), 11/6->today $(wc -l < "$D/moved_g3_1106_g3_today.tsv") (lists above; every file in $D)"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### PUNCT-RECON reviewed (11/14) — ESCALATE (mechanical, tripwire 1) → fixed → ESCALATE (mechanical, tripwire 2) → fixed → REVIEW: CLEAR

Fix 1: the awk `!(r in c)` → `(r in c) == 0`. Fix 2: the summary read `grep -m1 … | sed …` → `sed -n 's/^V2 MEMBER DIFF:.*| to ruling: //p'`.
Both exactly as the reviewer named; no other change; local re-test identical (READ DONE; tampered log STOPs). CC ran
`git diff --stat` f8e814c2 / e777f965 → 006e16ba over audit_reassembly_diff.py, reorder_english.py, the two tests and
tests/fixtures/reassembly/: empty both ways (affects only how Part 2 moves are explained).
Verdict line verbatim: "REVIEW: CLEAR - read-only block, both mechanical fixes are in, and one full pass over 7349-7419 hit no tripwire."

Ruling chat 11/14: PUNCT-RECON cleared to run on PA (read-only, reviewer CLEAR), either order with STEP9-DRY. Expectations noted, not gates: Part 1 583 → 607 with 24 moves; Part 2 unknown; gate-3 FAIL on Job 3:3 (exit 1) expected, not a stop.

### STEP9-DRY ran (11/14, 18:50 UTC, PA HEAD b3178672, REF 006e16ba) — READ DONE, exit 0

Log `~/edition_upgrade_runs/step9_dry_20261114.log`. built + src untouched (SAME OK both); bh_scrape.db 55,865,344 B,
5e9d4bb6… before = after; pre-fill copy present (442,687,488 B, 10/25 03:09Z). Copies 110,882,816 / 110,923,776 B.
abp_surface before on built and src: 395,003, blanks 0, no-word-at-slot 0, the builder's own definition.
- **Same-code control (src): 346,111 / 13,183 / 31,836 / 391,130** = the 10/25 figures; src → src-dry changed 538 /
  added 0 / removed 3,873 (= the 4,411 fill coming out; full sha from the log line "differences: 4411 - …/step9_delta_src.tsv:
  4411 lines + header, sha256 9cbf2b18766192df5fd578291e0ef02b746cab565fc4f9e26aa5bad5b355f7e4", recorded in full 11/14 for STEP9-DRY2); pre-fill → src-dry **0** (G1b oracle holds).
- **Built: 346,113 / 13,181 / 31,684 / 390,978**; romanized 390,978; blanks 0; no-word-at-slot 0. built → built-dry:
  changed 538 / added 11 / removed 4,036 (4,585 + header, sha `dbfe1912a5ae039ccf7a5fc3f75c5a5bda2216abad7ea654abd4d19b2f499139`).
  src-dry → built-dry (the edition's effect on the chain): changed 4 / added 14 / removed 166 (184 + header, sha
  `0498d40f189516a26290e44f93e57279aa1c67df1dbee794fc270e8497c979a4`).
- PN backfill refusals built 794 vs src 642 (no-match 390/266, bridge-fail 160/131, bridge-ambiguous 185/189,
  ambiguous 9/6, blank-label 50/50); PN slots 32,478 both.

### PUNCT-RECON ran (11/14, 19:00 UTC) — READ DONE, exit 0

Log `~/edition_upgrade_runs/punct_recon_20261114.log`; built unchanged (size + time). Part 1: 11/4 = 583 (204 + 367 +
12, gone 25), 11/6 = 607 (205 + 390 + 12, gone 24), each = its own summary line; moves 11/4 → 11/6 exactly 24
(23 absent → new-eligible: 1Co 7:25, 1Ti 5:18, Deu 15:2, Deu 28:12, Deu 29:6, Eze 18:13, Eze 18:17, Eze 18:8,
Gal 4:21, Isa 13:10, Jer 13:1, Job 34:27, Joh 4:17, Lev 11:11, Lev 12:4, Lev 18:21, Lev 21:11, Lev 23:36,
Lev 25:37, Lev 25:4, Lev 7:26, Neh 5:12, Rom 6:14; + Num 8:26 gone → unchanged); 0 ops differences. Part 2: today's
built = 11/6 member for member (607; 0 moves, 0 ops differences); content-other Job 3:3 the one hard-fail (exit 1,
as on 11/6); word-order 0, dup-gloss 0, Joh 14:26 clean.

### Rulings (11/14, §9.113)
1. §9.87 punct: **607 is the punct-member figure; 583 superseded** (R2's 23 verses + Num 8:26). 9c freezes 607.
   Job 3:3 content-other stays the open hard-fail it was on 11/6.
2. STEP9: control accepted; built's 346,113 / 13,181 / 31,684 / 390,978 (deltas dbfe1912…, 0498d40f…) = the
   candidate declaration for STEP9-APPLY, not yet declared. First a read: all 184 src-dry → built-dry members by
   class, each removed slot joined to its built_run/pn_refused.tsv line; the 152/152 confirmed from the files.
3. The 9a/9b/9c code change is now live (390,978 ≠ 391,130 blocks 9a at :291-294); proposal after the 184 read.

## STEP9-MEMBERS drafted (11/14, §9.113 ruling 2)

Reads only the STEP9-DRY run folder: the src-dry → built-dry delta (guard: 185 lines, sha 0498d40f…), both dry copies
(guard: abp_surface 390,978 / 391,130 as STEP9-DRY left them; size + time before = after), both pn_refused.tsv files
and both 3_pn.out files. (1) Each of the 184 members, one line: kind | verse | position | src-dry row → built-dry row |
the word at that slot on built-dry and on src-dry (Strong's, is_pn, English) | the PN-backfill refusal line at that
slot on built and on src (cause, label, token) — so a removed name slot shows its built refusal, an added one its src
refusal, and a slot whose word moved shows the different words. Then counts by kind × name-slot × refusal cause.
(2) 152/152 from the files: refusal lines (expect 794 / 642), NEW rows from 3_pn.out (31,684 / 31,836), name slots
(32,478 both), abp_surface rows on a name slot (= NEW) and not on one (359,294 both = builder + backfill).
Local test on the made-up STEP9-DRY folder (two refusal lines planted): every member joined to the right words and
refusal lines on both sides; READ DONE; re-paste STOP; the real block on the fake folder STOPs on the delta sha.

### Block STEP9-MEMBERS (GATE REF 006e16ba; READ-ONLY — reads the STEP9-DRY run folder; writes only its own run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/step9_members_20261114.log
if [ -e "$L" ]; then echo "STEP9-MEMBERS RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP9-MEMBERS sec 9.113 ruling 2: the 184 src-dry -> built-dry abp_surface members by class, each joined to the word at its slot on both copies and to the PN-backfill refusal line there; the 152/152 from the files - READ-ONLY (reads only the STEP9-DRY run folder) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9-MEMBERS RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP9-MEMBERS RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
DD=~/edition_upgrade_runs/step9_dry_20261114
T=$DD/step9_delta_srcdry_builtdry.tsv
BD=$DD/dry.db
SD=$DD/src/dry.db
D=~/edition_upgrade_runs/step9_members_20261114
TAB=$'\t'
python3 scripts/eu_step.py pre --tag STEP9M --ref "$REF" --dir "$D" --db "$BD" --db "$SD" || { echo "STEP9-MEMBERS RESULT: STOP - pre (line above); nothing made"; exit 1; }
for f in "$T" "$DD/built_run/pn_refused.tsv" "$DD/src_run/pn_refused.tsv" "$DD/built_run/3_pn.out" "$DD/src_run/3_pn.out"; do [ -s "$f" ] || { echo "STEP9-MEMBERS RESULT: STOP - missing or empty: $f"; exit 1; }; done
s=$(sha256sum < "$T" | cut -d' ' -f1); n=$(wc -l < "$T"); echo "delta file $T: $n lines (expect 185 = header + 184), sha256 $s (expect 0498d40f189516a26290e44f93e57279aa1c67df1dbee794fc270e8497c979a4)"
[ "$s" = 0498d40f189516a26290e44f93e57279aa1c67df1dbee794fc270e8497c979a4 ] && [ "$n" = 185 ] || { echo "STEP9-MEMBERS RESULT: STOP - not the STEP9-DRY delta file"; exit 1; }
bs0=$(stat -c '%s %Y' "$BD" "$SD" | tr '\n' ' ')
cb=$(sqlite3 -readonly "$BD" "SELECT count(*) FROM abp_surface") || { echo "STEP9-MEMBERS RESULT: STOP - read failed on $BD"; exit 1; }
cs=$(sqlite3 -readonly "$SD" "SELECT count(*) FROM abp_surface") || { echo "STEP9-MEMBERS RESULT: STOP - read failed on $SD"; exit 1; }
echo "abp_surface on the copies: built-dry $cb (expect 390978), src-dry $cs (expect 391130)"
[ "$cb" = 390978 ] && [ "$cs" = 391130 ] || { echo "STEP9-MEMBERS RESULT: STOP - the dry copies are not as STEP9-DRY left them"; exit 1; }
# --- (1) the 184 members ---
awk -F'\t' 'NR > 1 {k = $3; gsub(/[() ]/, "", k); split(k, a, ","); print a[1] "\t" a[2] "\t" $2 "\t" $5 "\t" $6}' "$T" > "$D/keys.tsv"
echo "members by kind (expect CHANGED 4 / ADDED 14 / REMOVED 166):"; cut -f3 "$D/keys.tsv" | sort | uniq -c
V=$(cut -f1 "$D/keys.tsv" | sort -un | paste -sd, -); echo "verses touched: $(cut -f1 "$D/keys.tsv" | sort -un | wc -l)"
WQ="SELECT w.verse_id, w.position, v.book, v.chapter, v.verse, COALESCE(w.strongs, ''), COALESCE(w.is_pn, ''), COALESCE(w.english, '') FROM words w JOIN verses v ON v.id = w.verse_id WHERE w.verse_id IN ($V) ORDER BY 1, 2"
sqlite3 -readonly -separator "$TAB" "$BD" "$WQ" > "$D/words_built.tsv" || { echo "STEP9-MEMBERS RESULT: STOP - words read failed on built-dry"; exit 1; }
sqlite3 -readonly -separator "$TAB" "$SD" "$WQ" > "$D/words_src.tsv" || { echo "STEP9-MEMBERS RESULT: STOP - words read failed on src-dry"; exit 1; }
# files in order: words_built, words_src, built refusals, src refusals, keys -> one line per member:
# kind | ref | pos | src-dry row -> built-dry row | built word at the slot | src word at the slot | built refusal | src refusal
awk -F'\t' -v OFS='\t' '
  FNR == 1 {f++}
  f == 1 {wb[$1 SUBSEP $2] = $6 " pn=" $7 " \"" $8 "\""; ref[$1] = $3 " " $4 ":" $5; bk[$1] = $3 "\t" $4 "\t" $5; next}
  f == 2 {ws[$1 SUBSEP $2] = $6 " pn=" $7 " \"" $8 "\""; if (($1 in ref) == 0) {ref[$1] = $3 " " $4 ":" $5; bk[$1] = $3 "\t" $4 "\t" $5}; next}
  f == 3 {rb[$1 "\t" $2 "\t" $3 "\t" $4] = $5 " (label \"" $6 "\", token " $7 ")"; next}
  f == 4 {rs[$1 "\t" $2 "\t" $3 "\t" $4] = $5 " (label \"" $6 "\", token " $7 ")"; next}
  f == 5 {k = $1 SUBSEP $2; r = bk[$1] "\t" $2
          b = (k in wb) ? wb[k] : "(no word)"; s = (k in ws) ? ws[k] : "(no word)"
          x = (r in rb) ? rb[r] : "-"; y = (r in rs) ? rs[r] : "-"
          print $3, ref[$1], $2, $4 " -> " $5, b, s, x, y}' \
  "$D/words_built.tsv" "$D/words_src.tsv" "$DD/built_run/pn_refused.tsv" "$DD/src_run/pn_refused.tsv" "$D/keys.tsv" > "$D/members_184.tsv"
echo "--- the 184 (kind | ref | position | src-dry row -> built-dry row | built word at the slot | src word at the slot | built PN refusal there | src PN refusal there):"
sed 's/\t/ | /g; s/^/  /' "$D/members_184.tsv"
echo "--- lines: $(wc -l < "$D/members_184.tsv") (expect 184)"
echo "--- by class: kind | built word is a name slot | built refusal cause at the slot (- = none) | src refusal cause at the slot:"
awk -F'\t' '{p = ($5 ~ / pn=1 /) ? "name slot" : "not a name slot"; x = $7; sub(/ .*/, "", x); y = $8; sub(/ .*/, "", y); print $1 " | built " p " | built refusal " x " | src refusal " y}' "$D/members_184.tsv" | sort | uniq -c
# --- (2) the 152 / 152 from the files ---
num() { sed -n "/$2/{s/.*: *//; s/,//g; s/[^0-9].*//; p; q}" "$1"; }
rb=$(wc -l < "$DD/built_run/pn_refused.tsv"); rs=$(wc -l < "$DD/src_run/pn_refused.tsv")
nb=$(num "$DD/built_run/3_pn.out" "NEW rows to add"); ns=$(num "$DD/src_run/3_pn.out" "NEW rows to add")
PQ="SELECT count(*) FROM words WHERE is_pn = 1; SELECT count(*) FROM abp_surface s JOIN words w ON w.verse_id = s.verse_id AND w.position = s.position WHERE w.is_pn = 1; SELECT count(*) FROM abp_surface s JOIN words w ON w.verse_id = s.verse_id AND w.position = s.position WHERE COALESCE(w.is_pn, 0) <> 1"
qb=$(sqlite3 -readonly "$BD" "$PQ" | paste -sd' ' -); qs=$(sqlite3 -readonly "$SD" "$PQ" | paste -sd' ' -)
read -r sb pb ob <<<"$qb"; read -r ss ps os <<<"$qs"
for x in "$rb" "$rs" "$nb" "$ns" "$sb" "$pb" "$ob" "$ss" "$ps" "$os"; do [ -n "$x" ] || { echo "STEP9-MEMBERS RESULT: STOP - a figure for the 152/152 did not read (NEW lines or counts above)"; exit 1; }; done
echo "refusal lines in pn_refused.tsv: built $rb, src $rs (expect 794 / 642) - difference $((rb - rs))"
echo "PN backfill NEW rows (3_pn.out): built $nb, src $ns (expect 31684 / 31836) - difference $((ns - nb))"
echo "name slots (words is_pn = 1): built-dry $sb, src-dry $ss (expect 32478 both); NEW + refused: built $((nb + rb)), src $((ns + rs))"
echo "abp_surface rows on a name slot: built-dry $pb, src-dry $ps (expect = the NEW rows, as already-present skips were 0)"
echo "abp_surface rows NOT on a name slot: built-dry $ob, src-dry $os (expect 359294 both = builder + backfill: 346113 + 13181 / 346111 + 13183)"
echo "152 / 152: rows $((ns - nb)) / refusals $((rb - rs)) / table total $((cs - cb))"
bs1=$(stat -c '%s %Y' "$BD" "$SD" | tr '\n' ' '); echo "dry copies size + time before = after: $([ "$bs1" = "$bs0" ] && echo yes || echo NO)"
[ "$bs1" = "$bs0" ] || { echo "STEP9-MEMBERS RESULT: STOP - a dry copy changed during a read-only run - report this"; exit 1; }
echo "STEP9-MEMBERS RESULT: READ DONE - $(wc -l < "$D/members_184.tsv") members listed and classed (all in $D/members_184.tsv); 152/152 lines above; nothing written outside $D"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9-MEMBERS reviewed (11/14) — REVIEW: CLEAR

Verdict line verbatim: "REVIEW: CLEAR - read-only block. The dry copies are opened only by `sqlite3 -readonly` and by eu_step `pre`'s read-only opener. Built and src are never opened. All output goes to a new run folder, which `pre` refuses to make if it already exists, and to a new log behind the log-exists guard. Every parse matches the code that wrote its input, and one full pass found no tripwire."
Reviewer notes (not blockers): assumes no `~/.sqliterc` header setting (as earlier blocks); "name slot" = is_pn printed exactly 1.

### STEP9-MEMBERS ran (11/14, 19:18 UTC, PA HEAD b3178672, REF 006e16ba) — READ DONE, exit 0

Log `~/edition_upgrade_runs/step9_members_20261114.log`; list `step9_members_20261114/members_184.tsv`. Delta file
185 lines / 0498d40f…; copies 390,978 / 391,130, unchanged. 184 = ADDED 14 / CHANGED 4 / REMOVED 166 over 158 verses.
By class: REMOVED name slot with a built refusal there 160 (no-match 127 / bridge-fail 30 / ambiguous 3; src refusal
none); REMOVED not a name slot 6; ADDED name slot 12 (src refusal there: bridge-ambiguous 3, bridge-fail 3, no-match 3,
blank-label 1, none 2); ADDED not a name slot 2; CHANGED 4 (1 name slot, 3 not). 152/152 from the files: refusals
794 − 642, NEW 31,836 − 31,684, table 391,130 − 390,978; name slots 32,478 both; NEW + refused 32,478 both; non-name
rows 359,294 both.

### Ruling (11/14, §9.114)
Read from the list (ruling chat, no cause asserted): at the 160 removed name slots the built English differs from
src's at the same slot (Jabesh/Jabish, Joram/Jehoram, Mathusala/Methuselah, Gergasite/Gergesite, Silvanus/Silas,
Aeneas/Eneas …) and the built refusal label is the built spelling; the other 24 are slot shifts within their verse
(Jos 2:4 19/20, Jdg 11:7 6/7, Rom 9:29 17/18, Gen 34:4 1/2, 2Ki 23:35 6/7 …). **STEP9-APPLY held pending JP's
decision on the 160** (apply now as a recorded known regression, or fix the name-slot matching first). Nothing more
to draft on step 9 until then. The §9.112 9a/9b/9c code-change proposal may proceed meanwhile.

### JP decision + ruling (11/14, §9.115)
JP: **Option B — fix the name-slot matching first.** STEP9-APPLY stays held; STEP9-DRY's 390,978 withdrawn as a candidate.
Ruling: a committed repo file pairing each new-edition spelling with the scrape's old-edition label, consulted by the
name-slot backfill only when a direct match fails; the 160 removed name slots are the list to cover; CC makes the
design choices (format, per label vs per slot, logging) and says why; tests: direct match wins, mapped miss resolves,
unmapped miss refuses; reviewer reads proposal + diff; ruling; push → new code REF; then STEP9-DRY re-run under the
new REF (src control must still be 391,130 / pre-fill → src-dry 0), figures, then the 9a/9b/9c proposal.

## Name-respelling fix — proposal (11/14, CC; code in the working tree, NOT committed until ruled)

**Files.** `scripts/pn_edition_spelling.tsv` (new, 146 rows) · `scripts/backfill_pn_surface.py` (+148 / −2) ·
`tests/test_pn_edition_spelling.py` (new) · the new test added to `.github/workflows/ci.yml` and
`scripts/githooks/pre-commit` (both lists). Nothing else changes; no other builder reads the file.

**Design choices, and why.**
- **Keyed per verse + edition token, not per slot and not globally.** Per slot (position) breaks on the next rebuild:
  STEP9-MEMBERS showed 24 shifts in 158 verses. A global per-spelling rule would assert a respelling everywhere
  from evidence in some verses: Joram/Jehoram are different kings in places, and Num 36:5's joseph → israel is a
  quirk of that one verse's scrape labels. Per verse matches the evidence exactly and survives renumbering.
- **Format:** TSV, `#` comment lines, header `book chapter verse edition_token scrape_tokens note`; tokens are
  `_name_token` values (the backfill's own key), the note carries the evidence (src English at the slot). One old token
  = every refused slot with that edition token in the verse (1Sa 11:1 jabesh ×2); several (comma-separated) = one per
  refused slot in position order, counts must agree, else the row is not used — needed for Gen 4:18, where the two
  Mathusala slots were Methusael and Methusaela in the old edition. Built from the 160 removed name slots:
  157 slots → 146 rows; the other 3 (Num 26:39 Shupham + Shuphamites, Num 36:5 Israel) have the same token on both
  sides and were refused only as ambiguous — they resolve when their partner slots (hupham, huphamites, joseph)
  rejoin the group.
- **Used only on a direct miss, and never changes a direct result.** `pair_verse_listed` runs the existing
  `pair_verse` unchanged; only for slots it REFUSED does it swap in the listed old token and pair the verse again;
  the second result is kept only if every slot the first pass paired keeps exactly its form (else the first pass
  stands and the row reads "conflict"). So the existing rules, refusals and the bridge are untouched, and the list
  can only add rows.
- **Loud, never silent:** a malformed list (bad header/verse/token, self-map, duplicate) stops the run before any read
  or write. The run prints `respelling-list adds`, slots tried / paired / still refused / paired along (a same-token
  slot that resolves once a listed one joins its group, Num 26:39), and every row not used with its reason (direct
  match / no slot with this token / count differs / conflict), up to 50 lines; `--dump-list FILE` writes every
  paired slot (book ch vs pos edition_token old_token form) and every unused row.
- **Same-code safety:** a row fires only in its verse and only on a refused slot carrying the EDITION spelling; src's
  slots carry the old spellings, so on src every row should read "no slot with this token" and src's figures must
  stay 391,130 / pre-fill → src-dry 0 — the STEP9-DRY re-run checks exactly that.

**Tests** (`tests/test_pn_edition_spelling.py`, made-up data in the real table shapes): with an empty list, the
respelled slots refuse as on 11/14; with the list, a direct match still wins (the old-token row is NOT taken),
a mapped miss resolves, an unmapped miss still refuses; the ordered Gen 4:18 shape; a count mismatch leaves the row
unused; the Num 26:39 shape (mapped slot joins the group, both paired in order, one "paired along"); the no-change
guard (a listed slot that would take a blank slot's glued cell → conflict, first pass kept); malformed lists stop the
run; a listed slot whose old token has no scrape row stays refused and is reported ("tried, still refused"); the
committed list loads, 146 rows. `tests/test_pn_surface_backfill.py` (the existing 26-slot suite) passes unchanged.
Tests proven able to fail: with the no-change guard removed, the G checks fail; with the refused-only rule removed,
the "not needed" check fails (the guard still keeps A's direct pairing - two layers).

**Completeness gap — found while building the list.** The 160 are names refused AT THE SAME SLOT. A name that moved
slot is invisible to the 184 delta: e.g. Gen 5:25 / 5:26, where the edition prints the glued cell "Mathusala lived"
(local feed `abp_app_slots_italic.tsv`) and STEP9-MEMBERS shows src's Methuselah slot holding "lived" on built — the
built Mathusala slot sits elsewhere in the verse, and nothing in the 184 says whether it got its Greek. So before
the REF is pushed: **STEP9-NAMESGAP** (read-only, STEP9-DRY folder only) lists every printed name form src-dry has and
built-dry lacks, verse by verse, with built's refusal lines there; any verse outside the 146 rows gets its row from that
read, in the same change, so one REF covers every lost name. Locally tested on made-up data (a planted missing
form is listed with its refusal line; READ DONE).

### Block STEP9-NAMESGAP (v2) (GATE REF 006e16ba; READ-ONLY — reads the STEP9-DRY run folder; writes only its own run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/step9_namesgap_20261114.log
if [ -e "$L" ]; then echo "STEP9-NAMESGAP RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=006e16ba
echo "GATE REF ${REF} - STEP9-NAMESGAP: every printed Greek name form src-dry has and built-dry lacks, verse by verse (catches names that moved slot, which the 184 delta cannot show), with built's refusal lines in each such verse - READ-ONLY (reads only the STEP9-DRY run folder) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9-NAMESGAP RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] || { echo "STEP9-NAMESGAP RESULT: STOP - scripts/eu_step.py missing (PA has not pulled $REF)"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
DD=~/edition_upgrade_runs/step9_dry_20261114
BD=$DD/dry.db
SD=$DD/src/dry.db
BR=$DD/built_run/pn_refused.tsv
D=~/edition_upgrade_runs/step9_namesgap_20261114
TAB=$'\t'
python3 scripts/eu_step.py pre --tag STEP9N --ref "$REF" --dir "$D" --db "$BD" --db "$SD" || { echo "STEP9-NAMESGAP RESULT: STOP - pre (line above); nothing made"; exit 1; }
[ -s "$BR" ] || { echo "STEP9-NAMESGAP RESULT: STOP - missing or empty: $BR"; exit 1; }
bs0=$(stat -c '%s %Y' "$BD" "$SD" | tr '\n' ' ')
NQ="SELECT s.verse_id, v.book, v.chapter, v.verse, s.form, s.position, COALESCE(NULLIF(w.english_head, ''), w.english) FROM abp_surface s JOIN words w ON w.verse_id = s.verse_id AND w.position = s.position JOIN verses v ON v.id = s.verse_id WHERE w.is_pn = 1 ORDER BY 1"
sqlite3 -readonly -separator "$TAB" "$SD" "$NQ" > "$D/names_src.tsv" || { echo "STEP9-NAMESGAP RESULT: STOP - read failed on src-dry"; exit 1; }
sqlite3 -readonly -separator "$TAB" "$BD" "$NQ" > "$D/names_built.tsv" || { echo "STEP9-NAMESGAP RESULT: STOP - read failed on built-dry"; exit 1; }
ns=$(wc -l < "$D/names_src.tsv"); nb=$(wc -l < "$D/names_built.tsv")
echo "name-slot rows read: src-dry $ns (expect 31836), built-dry $nb (expect 31684)"
[ "$ns" = 31836 ] && [ "$nb" = 31684 ] || { echo "STEP9-NAMESGAP RESULT: STOP - the dry copies are not as STEP9-DRY left them"; exit 1; }
# per verse + form: src count vs built count -> MISSING (src > built) / EXTRA (built > src)
awk -F'\t' -v OFS='\t' '
  FNR == 1 {f++}
  f == 1 {k = $2 "\t" $3 "\t" $4 "\t" $5; s[k]++; next}
  f == 2 {k = $2 "\t" $3 "\t" $4 "\t" $5; b[k]++; next}
  END {for (k in s) if (s[k] > b[k]) print "MISSING", k, s[k], b[k] + 0
       for (k in b) if (b[k] > s[k]) print "EXTRA", k, s[k] + 0, b[k]}' \
  "$D/names_src.tsv" "$D/names_built.tsv" | sort -t "$TAB" -k1,1 -k2,2 -k3,3n -k4,4n > "$D/forms_diff.tsv"
mi=$(awk -F'\t' '$1 == "MISSING" {n += $6 - $7} END {print n + 0}' "$D/forms_diff.tsv")
ex=$(awk -F'\t' '$1 == "EXTRA" {n += $7 - $6} END {print n + 0}' "$D/forms_diff.tsv")
mv=$(awk -F'\t' '$1 == "MISSING" {print $2 FS $3 FS $4}' "$D/forms_diff.tsv" | sort -u | wc -l)
echo "forms built lacks: $mi in $mv verses; forms built has extra: $ex; missing - extra = $((mi - ex)) (expect 152 = 31836 - 31684)"
echo "--- MISSING / EXTRA (kind | book ch:vs | form | src count | built count), each MISSING line followed by the src-dry slot(s) holding that form (position | the label the backfill keys on), and each MISSING verse by built's refusal lines there (pos | cause | label | token):"
awk -F'\t' '
  FNR == 1 {f++}
  f == 1 {r[$1 "\t" $2 "\t" $3] = r[$1 "\t" $2 "\t" $3] "      refused: pos " $4 " | " $5 " | " $6 " | " $7 "\n"; next}
  f == 2 {k = $2 "\t" $3 "\t" $4 "\t" $5; sl[k] = sl[k] "      src slot: pos " $6 " | " $7 "\n"; next}
  f == 3 {v = $2 "\t" $3 "\t" $4
          printf "  %s | %s %s:%s | %s | %s | %s\n", $1, $2, $3, $4, $5, $6, $7
          if ($1 == "MISSING") printf "%s", sl[$2 "\t" $3 "\t" $4 "\t" $5]
          if ($1 == "MISSING" && (v in shown) == 0) {shown[v] = 1; printf "%s", (v in r) ? r[v] : "      (no built refusal line in this verse)\n"}}' \
  "$BR" "$D/names_src.tsv" "$D/forms_diff.tsv"
bs1=$(stat -c '%s %Y' "$BD" "$SD" | tr '\n' ' '); echo "dry copies size + time before = after: $([ "$bs1" = "$bs0" ] && echo yes || echo NO)"
[ "$bs1" = "$bs0" ] || { echo "STEP9-NAMESGAP RESULT: STOP - a dry copy changed during a read-only run - report this"; exit 1; }
echo "STEP9-NAMESGAP RESULT: READ DONE - $mi missing forms in $mv verses, $ex extra (all in $D/forms_diff.tsv)"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### Respelling proposal + STEP9-NAMESGAP v1 reviewed (11/14) — block CLEAR; code findings to the ruling chat → v2

Verdict line on the v1 block, verbatim: "REVIEW: CLEAR - STEP9-NAMESGAP: read-only block. It opens the dry copies only through `sqlite3 -readonly` and eu_step `pre`. It writes only its own new run folder and a guarded log, the parsing matches the code that wrote its inputs, and no tripwire fires."
Code findings (no clearance — a builder change goes to the ruling chat, §9.90), with CC's answers:
- (a) the no-change guard holds; the second pass may also pair a same-token slot that is NOT listed ("paired along",
  Num 26:39) — intended, counted separately. Agreed; state it in the ruling.
- (b1) **derivation source** — the old tokens were taken from src's `english`, but the backfill keys on
  `COALESCE(NULLIF(english_head,''), english)` and matches the SCRAPE's labels; where src's head differs from its English
  (likely 1Ch 4:14 "of Ge Charashim", Neh 3:14 "the house of Beth-heccerem", Gen 38:1 "of Adullam") a row would fail
  ("tried, still refused"). **CC: valid — fixed at the source.** NAMESGAP v2 also prints, under each missing form, the
  src-dry slot(s) holding it with exactly the label the backfill keys on; the list is then REBUILT from those labels
  (and the moved names added) before the REF — no row taken from `english` alone.
- (b2) rows that are not respellings (Num 36:5 joseph→israel, 2Ki 9:31 zimri→omri, Act 27:17 gulf→syrtis, Neh 2:19
  arabian→arab, Eze 27:13 greece→greek, Mar 14:67 nazareth→nazarene, Luk 3:33 phares→perez, 2Ch 14:9 zerah→zarai).
  **CC checked each against the STEP9-MEMBERS lines:** the form the slot gets is the printed Greek src had at that
  same slot — Ιωσήφ, Ζαμβρί, Σύρτιν, Αραβί, Ελλάς, Ναζαρηνού, Φαρές, Ζαραϊ — each the Greek of the NEW English
  (Joseph, Zimri, Syrtis, Arabian, Greece, of Nazareth, Phares, Zerah); the old English was the odd one out. The
  STEP9-DRY re-run's `--dump-list` gets a per-row read regardless.
- (c) same-code safety is an argument; the proof is the re-run's src control (391,130; pre-fill → src-dry 0) as a hard
  condition. Agreed.
- (d) malformed-list tests now also prove the table is untouched (29 checks pass).
- (f) both test lists name `test_pn_edition_spelling.py` (ci.yml:70, pre-commit:73).
- Timing: NAMESGAP is gated on 006e16ba — run it BEFORE the respelling REF is pushed or pulled.

**v2 change** (only the output; same reads, same guards): the names query also takes each row's position and
`COALESCE(NULLIF(english_head,''), english)`; each MISSING line is followed by "src slot: pos P | label". Local re-test:
the planted missing form shows its src slot and label, then built's refusal line; READ DONE.

### STEP9-NAMESGAP v2 reviewed (11/14) — REVIEW: CLEAR

Verdict line verbatim: "REVIEW: CLEAR - STEP9-NAMESGAP v2: still read-only and the guards are unchanged; the only change is extra output, and the new label matches the backfill script's own."
Notes: the section echo (not the GATE REF line) describes the new src-slot lines; run it BEFORE PA pulls the
respelling REF. The rebuilt list + code go to the ruling chat afterwards, with findings (b2) and (c) open there.

### STEP9-NAMESGAP ran (11/14, 21:49 UTC, PA HEAD b3178672, REF 006e16ba) — READ DONE, exit 0

Log `~/edition_upgrade_runs/step9_namesgap_20261114.log`; `forms_diff.tsv` in its run folder. Dry copies unchanged.
Name-slot rows 31,836 / 31,684; forms built lacks **163 in 144 verses**, extra 11 (Καϊν ×2, Αχιτόφελ ×2, Ρουβήν,
Συμεών, Ιεζάβελ, Εβραίος, Ιωακείμ, Βηθανία, Ιησούν — names built now matches that src refused); 163 − 11 = 152.
Each missing form shown with src's keyed slot label(s) and built's refusal lines.

### Ruling (11/14, §9.116)
Three shapes read from the list (no cause asserted): (1) spelling variants (the bulk); (2) tokenization/possessive —
Act 27:17 syrtis/gulf, Est 5:9 haman/hamans, Gen 38:1 adullam/adullamite, Neh 2:19 arab/arabian, Jos 9:7
hivites/hivite; (3) a different English word — Num 36:5 israel/joseph, 2Ki 9:31 omri/zimri, Eze 27:13 greek/greece,
Luk 3:33 perez/phares, Mar 14:67 nazarene/nazareth (CC's 8-row Greek check noted). Slot shifts: Gen 5:25/5:26,
Deu 2:13, Est 5:9. **Ruling:** rebuild the list from this log (per verse, new label → src label, used only on a
refusal); mark shape 2 / shape 3 rows; say from the code whether a verse-scoped pair covers the slot shifts; tests as
ruled + one shape-2 + one shape-3; reviewer; ruling; push → new REF; STEP9-DRY re-run — the recovered count is READ,
not forecast.

## Name-respelling fix — proposal v2 (11/14, list rebuilt from STEP9-NAMESGAP; code still uncommitted)

**List rebuilt** (`scripts/pn_edition_spelling.tsv`, **149 rows covering 160 slots**), from the NAMESGAP MISSING section:
per verse, each built refusal paired with the src slot holding the missing form — same position first, else (slot
shift) the verse's remaining missing slot, whose src tokens must agree. Old token = `_name_token` of src's keyed label
(`COALESCE(english_head, english)`), never the displayed English. 163 missing = 160 listed slots + 3 same-token slots
(Num 26:39 Shupham, Shuphamites; Num 36:5 Israel) that resolve when their partners rejoin; 1 built refusal paired with
nothing (2Ki 22:1 pos 3 josiah — refused on src too; not a missing form). Against v1 (146 rows, from `english`): every
v1 pair confirmed by src's keyed label; **+3 rows** — the slot shifts Gen 5:25, Gen 5:26 (mathusala → methuselah,
built pos 1 ← src pos 2) and Est 5:9 (hamans → haman, built pos 12 ← src pos 2/13); Neh 3:14's old token is now src's
label `bethheccerem` (v1 had `beth-heccerem`; same key once hyphens drop). Notes mark the 5 shape-2 and 5 shape-3 rows
and every slot shift, and give each slot's built pos ← src pos.
**Slot shifts — covered by the verse-scoped pair, from what the code does:** `pair_verse` groups a verse's slots by
token and pairs a token's slots with that token's scrape rows in printed order — position is never compared with the
src side. The list only changes the refused slot's token, so a name that moved within its verse pairs exactly as it
would at its old position. Deu 2:13: built already has one Ζαρέδ (count 1 of 2); its refused slot gets `zered → zared`; the scrape's
zared rows both carry Ζαρέδ, so whichever way the group forms, the form is the same (the no-change guard keeps the
slot already paired). Tested: S2 (refused slot at another position than
its direct twin), S4 (Gen 5:25 shape, name only in a glued cell → the bridge path with the old token).
**Tests** (32 checks, all pass): the three ruled cases; shape 2 (possessive "Haman's" in a shifted slot → Αμάν, the
direct Haman slot unchanged); shape 3 (Joseph takes the row the old edition labelled Israel, Israel its own, in order);
the bridge path (S4); plus the v1 cases. The existing `test_pn_surface_backfill.py` passes unchanged.
Recovered count on the real data: read from the STEP9-DRY re-run, not forecast.

### Respelling proposal v2 reviewed (11/14) — no defect found; findings to the ruling chat (no CLEAR: builder change, §9.90)
Reviewer findings, with CC's answers:
1. Rows checkable from the repo only in part (the per-row MISSING lines are in the ruling chat's paste): the +3 rows, Neh 3:14,
   and the per-slot notes confirmed. **Deu 2:13:** the ruling lists it as a slot shift; the list note reads "built pos 15 ← src
   pos 15" (no shift) — CC: from the log it is not a shift. src had Ζαρέδ at pos 10 and 15, built has one Ζαρέδ already and refuses
   pos 15 only; the shift was a count (2 vs 1), not a moved slot. For the ruling chat to state which stands.
2. **"pairs exactly as at its old position" is too strong** — CC: agreed, withdrawn. `_resolve` pairs a group's slots with its
   forms in position order; if two refused slots enter a group with DIFFERENT forms and one has moved, the order could swap them,
   and the no-change guard (first-pass pairings only) would not see it. Checked against the list: every multi-slot group is
   either one Greek form throughout (the jabish/jehoram/anakim groups: Ιαβής/Ιαβίς, Ιωράμ, Ενακίμ) or keeps its positions
   (Num 26:39 1/6 Σωφάν/Οφάμ, Num 36:5 5/13 Ισραήλ/Ιωσήφ, built pos = src pos); Gen 4:18's two slots take two different old
   tokens (two one-slot groups); the shifted slots (Gen 5:25/26 bridge, single slot; Est 5:9 one form) cannot swap. **To
   prove it on the data instead of arguing it:** the STEP9-DRY re-run will compare EVERY slot the list paired (its
   `--dump-list` line) with src-dry's form at the src slot the list note names — any difference = STOP, not a read.
3. Shape marking matches the ruling's lists (2Ch 14:9 zerah/zarai correctly left with the spelling variants).
4. S2, S3, S4 exercise what they claim; each refused in the empty-list baseline.
5. (b2) and (c): covered by the per-slot check above (it reads every shape-2/3 row too) and the src control as a hard
   condition (391,130; pre-fill → src-dry 0).

### Ruling (11/14, §9.117) — respelling fix APPROVED; pushed as the new code REF
Deu 2:13: CC's reading stands (a count difference src 2 / built 1, refusal at the same pos 15 — not a shift). **The
respelling fix is approved**: commit + push as the new code REF; then STEP9-DRY re-run under it with three STOP gates:
(1) src control = 391,130 (346,111 / 13,183 / 31,836); (2) pre-fill → src-dry 0 differences; (3) every slot the list fills
on built-dry carries the same Greek form as src-dry at its matching slot, figures read out (filled via the list, checked,
mismatches 0). Recovered count + new chain total read from that run. Reviewer, then PA.
Before the commit, CC gave the three slot-shift rows their src positions in the note (gate 3 reads them; data unchanged):
Gen 5:25 / 5:26 "built pos 1 <- src pos 2", Est 5:9 "built pos 12 <- src pos 2|13" (both src slots hold Αμάν, per the
NAMESGAP log). Every one of the 160 slot notes now names a src position.

## Respelling fix pushed — new code REF `32a39a10` (11/14); STEP9-DRY2 drafted

`32a39a10` = backfill_pn_surface.py (pair_verse_listed + report) + scripts/pn_edition_spelling.tsv (149 rows / 160 slots;
every slot note names its src position — the 3 shift rows were given theirs before the commit, data unchanged) +
tests/test_pn_edition_spelling.py (32 checks) + the two test lists. Pre-commit: all checks passed. `scripts/` differ
from 006e16ba only by these files; entity_resolution.py unchanged.

**STEP9-DRY2** (`step9_dry2_20261114`, GATE REF 32a39a10): the STEP9-DRY chain, src's copy first, PN backfill now also
writing `--dump-list`. Gates, each a STOP:
- **1** src control = 346,111 / 13,183 / 31,836 / 391,130; plus src → src-dry = STEP9-DRY's delta exactly (sha 9cbf2b18…);
- **2** pre-fill copy → src-dry: 0 differences (`--zero`);
- **3** every slot the list filled on built-dry (from the dump: listed + "paired along") = src-dry's form at the src position
  the list note names ("paired along" = its own position, unchanged); built-dry's row = the dump's form; figures read out:
  filled / checked / mismatches / unchecked — must be checked = filled, 0, 0.
Extra STOP (the list only adds): STEP9-DRY's built copy → this built copy must be ADDED rows only; that count = the
recovered rows. Read: built's chain total (to declare), built → dry (what STEP9-APPLY writes), src-dry → built-dry.
Disk: STOP if home is above 9.3 GB by `du` (the run adds about 0.25 GB). Both STEP9-DRY copies are kept (the old built
copy is read).
Local test (made-up dbs, a fake list committed in a throwaway clone): a respelled name (Isaac → "Isaak") refused without
the list, filled by it, gate 3 "OK … checked 1 - mismatches 0", READ DONE; a list note pointing at the wrong src slot →
"MISMATCH … src pos 0=Αβραάμ" → GATE 3 STOP; the real gate-1 figures on fake data → GATE 1 STOP.

### Block STEP9-DRY2 (GATE REF 32a39a10; READ-ONLY on built, src, bh_scrape.db, the pre-fill copy and STEP9-DRY's built copy — writes only its run folder and two throwaway copies)
```bash
set +H
L=~/edition_upgrade_runs/step9_dry2_run2_20261114.log
if [ -e "$L" ]; then echo "STEP9-DRY2 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=32a39a10
echo "GATE REF ${REF} - STEP9-DRY2 rebuild-words step 9 re-run under the respelling fix (sec 9.117): the chain on THROWAWAY copies of src's and built's verses/words/lexicon/dotted_lexicon/abp_surface; gates (1) src control 391,130 (2) pre-fill -> src-dry 0 (3) every list-filled slot = src-dry's Greek at its matching slot - built, src, bh_scrape.db, the pre-fill copy read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9-DRY2 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] && [ -f scripts/pn_edition_spelling.tsv ] || { echo "STEP9-DRY2 RESULT: STOP - PA has not pulled $REF (eu_step.py / pn_edition_spelling.tsv missing)"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
H=~/bible-db/bh_scrape.db
PF=~/bible.db.pre-surface-fill-20261025
LIST=scripts/pn_edition_spelling.tsv
OLD=~/edition_upgrade_runs/step9_dry_20261114/dry.db
D=~/edition_upgrade_runs/step9_dry2_20261114
E="python3 scripts/eu_step.py"
T=verses,words,lexicon,dotted_lexicon,abp_surface
TAB=$'\t'
RD="SELECT 'rows', count(*), 'blank form', sum(form IS NULL OR form = ''), 'blank translit', sum(translit IS NULL OR translit = '') FROM abp_surface; SELECT 'rows with no word at their slot', count(*) FROM abp_surface s WHERE NOT EXISTS (SELECT 1 FROM words w WHERE w.verse_id = s.verse_id AND w.position = s.position)"
num() { sed -n "/$2/{s/.*: *//; s/,//g; s/[^0-9].*//; p; q}" "$1"; }
dlt() { sed -n "/delta [0-9,]*/{s/.*delta \([0-9,]*\).*/\1/; s/,//g; p; q}" "$1"; }
# the step-9 chain, rebuild-words.md step 9, in order, on ONE throwaway copy ($1); outputs kept in $2
chain() {
  local db=$1 o=$2 n1 n2 d2 n3 d3 a3 m3 nt nr
  echo "--- 1/4 build_abp_surface (drops + re-creates abp_surface on the copy)"
  python3 scripts/build_abp_surface.py "$db" --bh "$H" > "$o/1_build.out" 2>&1 || { cat "$o/1_build.out"; echo "chain: build_abp_surface failed"; return 1; }
  sed -n '/form found\|shows a line\|books with no source\|Wrote/p' "$o/1_build.out"
  n1=$(sed -n 's/.*Wrote \([0-9]*\) rows.*/\1/p' "$o/1_build.out"); [ -n "$n1" ] || { echo "chain: no Wrote line"; return 1; }
  echo "--- 2/4 backfill_abp_surface --apply"
  python3 scripts/backfill_abp_surface.py "$db" --bh "$H" --apply > "$o/2_backfill.out" 2>&1 || { cat "$o/2_backfill.out"; echo "chain: backfill_abp_surface failed"; return 1; }
  sed -n '/existing rows\|NEW rows\|same-as-dictionary\|ambiguity\|Wrote/p' "$o/2_backfill.out"
  n2=$(num "$o/2_backfill.out" "NEW rows to add"); d2=$(dlt "$o/2_backfill.out")
  [ -n "$n2" ] && [ "$n2" = "$d2" ] || { echo "chain: backfill NEW ($n2) != rows written ($d2)"; return 1; }
  echo "--- 3/4 backfill_pn_surface --apply (respelling list $LIST; refused slots -> $o/pn_refused.tsv; list use -> $o/pn_list.tsv)"
  python3 scripts/backfill_pn_surface.py "$db" --bh "$H" --apply --dump-refused "$o/pn_refused.tsv" --dump-list "$o/pn_list.tsv" > "$o/3_pn.out" 2>&1 || { cat "$o/3_pn.out"; echo "chain: backfill_pn_surface failed"; return 1; }
  sed -n '1,/coverage by book/p' "$o/3_pn.out" | sed '/coverage by book/d'; sed -n '/refused-slot dump\|respelling-list dump\|Wrote/p' "$o/3_pn.out"
  n3=$(num "$o/3_pn.out" "NEW rows to add"); d3=$(dlt "$o/3_pn.out")
  [ -n "$n3" ] && [ "$n3" = "$d3" ] || { echo "chain: PN backfill NEW ($n3) != rows written ($d3)"; return 1; }
  a3=$(sed -n '/arithmetic:/{s/.*= *//; s/ .*//; s/,//g; p; q}' "$o/3_pn.out"); m3=$(sed -n '/arithmetic:/{s/.*must equal *//; s/[^0-9,].*//; s/,//g; p; q}' "$o/3_pn.out")
  [ -n "$a3" ] && [ "$a3" = "$m3" ] || { echo "chain: PN arithmetic $a3 != $m3"; return 1; }
  echo "--- 4/4 build_abp_translit"
  python3 scripts/build_abp_translit.py "$db" > "$o/4_translit.out" 2>&1 || { cat "$o/4_translit.out"; echo "chain: build_abp_translit failed"; return 1; }
  cat "$o/4_translit.out"
  nt=$(sed -n 's/^Filled \([0-9]*\).*/\1/p' "$o/4_translit.out")
  nr=$(sqlite3 -readonly "$db" "SELECT count(*) FROM abp_surface") || { echo "chain: count failed"; return 1; }
  echo "chain total: builder $n1 + backfill $n2 + PN backfill $n3 = $((n1 + n2 + n3)); table now $nr; romanized $nt"
  [ "$nr" = "$((n1 + n2 + n3))" ] || { echo "chain: table count is not the sum of the three passes"; return 1; }
  echo "$n1 $n2 $n3 $nr $nt" > "$o/figures.txt"
}
# --- guards (read-only) ---
git diff --quiet "$REF" HEAD -- entity_resolution.py || { echo "STEP9-DRY2 RESULT: STOP - entity_resolution.py (imported by the PN backfill) differs from $REF"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- entity_resolution.py)" ] || { echo "STEP9-DRY2 RESULT: STOP - entity_resolution.py has uncommitted edits on PA"; exit 1; }
echo "entity_resolution.py (imported by the PN backfill) = $REF, unedited: OK"
dk=$(du -sk ~ 2>/dev/null | cut -f1); echo "home in use: $dk KB (the dashboard quota is 10 GB; this run adds about 0.25 GB - two copies like STEP9-DRY's 110 MB + two before.db of 18 MB)"
[ -n "$dk" ] && [ "$dk" -le 9300000 ] || { echo "STEP9-DRY2 RESULT: STOP - home is above 9.3 GB (or du failed) - free space first; nothing made"; exit 1; }
$E pre --tag STEP9B --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP9-DRY2 RESULT: STOP - pre (line above); nothing made"; exit 1; }
[ -s "$H" ] || { echo "STEP9-DRY2 RESULT: STOP - $H missing or empty"; exit 1; }
[ -e "$H-journal" ] && { echo "STEP9-DRY2 RESULT: STOP - a -journal sits beside $H"; exit 1; }
[ -s "$PF" ] || { echo "STEP9-DRY2 RESULT: STOP - the pre-fill copy $PF is missing (gate 2 needs it)"; exit 1; }
[ -s "$OLD" ] || { echo "STEP9-DRY2 RESULT: STOP - STEP9-DRY's built copy $OLD is missing (the recovered-rows delta needs it)"; exit 1; }
H0=$(sha256sum < "$H" | cut -d' ' -f1); echo "bh_scrape.db (read-only): $(stat -c %s "$H") bytes, sha256 $H0 (STEP9-DRY read 5e9d4bb6...)"
echo "respelling list $LIST: $(sed -n '/^[A-Z0-9]/p' "$LIST" | wc -l) rows (the header starts lowercase and is not counted), sha256 $(sha256sum < "$LIST" | cut -d' ' -f1)"
mkdir "$D/built_run" "$D/src" "$D/src_run" || { echo "STEP9-DRY2 RESULT: STOP - cannot make the sub-folders"; exit 1; }
# --- src's copy first: gates 1 and 2 ---
$E prep --tag STEP9B --built "$S" --dir "$D/src" --copy "$T" --save abp_surface || { echo "STEP9-DRY2 RESULT: STOP - prep of src's copy (line above); src untouched"; exit 1; }
echo "=== DRY B: the chain on the throwaway copy of SRC ($D/src/dry.db) - the same-code control ==="
chain "$D/src/dry.db" "$D/src_run" || { echo "STEP9-DRY2 RESULT: STOP - the chain on src's copy stopped (above); src untouched"; exit 1; }
read -r b1 b2 b3 br bt < "$D/src_run/figures.txt"
echo "GATE 1 - src control: builder $b1 / backfill $b2 / PN backfill $b3 / total $br (must be 346111 / 13183 / 31836 / 391130)"
[ "$b1 $b2 $b3 $br" = "346111 13183 31836 391130" ] || { echo "STEP9-DRY2 RESULT: STOP - GATE 1 - the src control moved: the respelling list changed the same-code result"; exit 1; }
echo "GATE 2 - pre-fill copy -> src-dry (must be 0 differences):"
$E delta --tag STEP9B --a "$PF" --b "$D/src/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_prefill_srcdry.tsv" --show 20 --zero || { echo "STEP9-DRY2 RESULT: STOP - GATE 2 - src-dry is not the pre-fill table (line above)"; exit 1; }
echo "src -> src-dry (must be STEP9-DRY's delta exactly: 4,411 lines, sha 9cbf2b18...):"
$E delta --tag STEP9B --a "$S" --b "$D/src/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_src.tsv" --show 5 --expect-sha 9cbf2b18766192df5fd578291e0ef02b746cab565fc4f9e26aa5bad5b355f7e4 || { echo "STEP9-DRY2 RESULT: STOP - src -> src-dry is not STEP9-DRY's delta (line above)"; exit 1; }
# --- built's copy ---
$E prep --tag STEP9B --built "$B" --dir "$D" --copy "$T" --save abp_surface || { echo "STEP9-DRY2 RESULT: STOP - prep of built's copy (line above); built untouched"; exit 1; }
echo "=== DRY A: the chain on the throwaway copy of BUILT ($D/dry.db) ==="
chain "$D/dry.db" "$D/built_run" || { echo "STEP9-DRY2 RESULT: STOP - the chain on built's copy stopped (above); built untouched"; exit 1; }
read -r a1 a2 a3 ar at < "$D/built_run/figures.txt"
echo "built: builder $a1 / backfill $a2 / PN backfill $a3 / total $ar (STEP9-DRY without the list: 346113 / 13181 / 31684 / 390978)"
for f in "$D/dry.db" "$D/src/dry.db"; do echo "--- abp_surface on $f after the chain"; sqlite3 -readonly "$f" "$RD" || { echo "STEP9-DRY2 RESULT: STOP - read failed on $f"; exit 1; }; done
# --- GATE 3: every slot the list filled on built-dry = src-dry's form at its matching slot ---
echo "=== GATE 3 - list-filled slots vs src-dry ==="
LP=$D/built_run/pn_list.tsv
[ -f "$LP" ] || { echo "STEP9-DRY2 RESULT: STOP - GATE 3 - no list dump at $LP"; exit 1; }
# the list notes -> (book ch vs built_pos) -> src position(s) "M" or "M|K"
sed -n '/^[A-Z0-9][A-Za-z0-9]*\t[0-9]/p' "$LIST" | awk -F'\t' -v OFS='\t' '{n = split($6, part, "; "); for (i = 1; i <= n; i++) if (part[i] ~ /^built pos [0-9]+ <- src pos [0-9|]+ /) {split(part[i], w, " "); print $1, $2, $3, w[3], w[7]}}' > "$D/list_slots.tsv"
echo "list slot notes: $(wc -l < "$D/list_slots.tsv") (expect 160)"
awk -F'\t' '$1 == "paired" || $1 == "paired along"' "$LP" > "$D/filled.tsv"
nf=$(wc -l < "$D/filled.tsv"); echo "slots filled via the list on built-dry: $nf ($(awk -F'\t' '$1 == "paired"' "$D/filled.tsv" | wc -l) listed + $(awk -F'\t' '$1 == "paired along"' "$D/filled.tsv" | wc -l) paired along)"
V=$(cut -f2-4 "$D/filled.tsv" | sort -u | awk -F'\t' '{printf "%s(v.book = '"'"'%s'"'"' AND v.chapter = %s AND v.verse = %s)", (NR > 1 ? " OR " : ""), $1, $2, $3}')
[ -n "$V" ] || { echo "STEP9-DRY2 RESULT: STOP - GATE 3 - the list filled no slot at all"; exit 1; }
FQ="SELECT v.book, v.chapter, v.verse, s.position, s.form FROM abp_surface s JOIN verses v ON v.id = s.verse_id WHERE $V"
sqlite3 -readonly -separator "$TAB" "$D/src/dry.db" "$FQ" > "$D/src_forms.tsv" || { echo "STEP9-DRY2 RESULT: STOP - GATE 3 - read failed on src-dry"; exit 1; }
sqlite3 -readonly -separator "$TAB" "$D/dry.db" "$FQ" > "$D/built_forms.tsv" || { echo "STEP9-DRY2 RESULT: STOP - GATE 3 - read failed on built-dry"; exit 1; }
# files: list_slots, src_forms, built_forms, filled -> one line per filled slot; a listed slot uses its note's src position(s),
# a 'paired along' slot (same token, not listed) its own position
awk -F'\t' -v FIG="$D/gate3_figures.txt" '
  FNR == 1 {f++}
  f == 1 {sp[$1 FS $2 FS $3 FS $4] = $5; next}
  f == 2 {sf[$1 FS $2 FS $3 FS $4] = $5; next}
  f == 3 {bf[$1 FS $2 FS $3 FS $4] = $5; next}
  f == 4 {k = $2 FS $3 FS $4 FS $5
          if ($1 == "paired") {p = (k in sp) ? sp[k] : ""} else {p = $5}
          if (p == "") {print "UNCHECKED | " $1 " | " $2 " " $3 ":" $4 " pos " $5 " | " $8 " | the list note names no src position"; nu++; next}
          n = split(p, ps, "|"); srcf = ""; ok = 0
          for (i = 1; i <= n; i++) {x = $2 FS $3 FS $4 FS ps[i]; srcf = srcf (i > 1 ? " / " : "") ps[i] "=" ((x in sf) ? sf[x] : "(none)"); if ((x in sf) && sf[x] == $8) ok = 1}
          b = (k in bf) ? bf[k] : "(none)"
          if (b != $8) ok = 0
          print (ok ? "OK" : "MISMATCH") " | " $1 " | " $2 " " $3 ":" $4 " pos " $5 " | built " b " | src pos " srcf " | " $6 " <- " $7
          nc++; if (ok == 0) nm++}
  END {printf "GATE 3 figures: checked %d - mismatches %d - unchecked %d\n", nc + 0, nm + 0, nu + 0 > FIG}' \
  "$D/list_slots.tsv" "$D/src_forms.tsv" "$D/built_forms.tsv" "$D/filled.tsv" > "$D/gate3.tsv"
sed 's/^/  /' "$D/gate3.tsv"
cat "$D/gate3_figures.txt"
read -r _g _3 _f _c nc _m _x nm _u _y nu < "$D/gate3_figures.txt"
echo "GATE 3 - filled via the list $nf, checked $nc, mismatches $nm, unchecked $nu (must be: checked = filled, mismatches 0, unchecked 0)"
[ "$nc" = "$nf" ] && [ "$nm" = 0 ] && [ "$nu" = 0 ] || { echo "STEP9-DRY2 RESULT: STOP - GATE 3 - a list-filled slot does not carry src-dry's Greek (lines above); built untouched"; exit 1; }
# --- deltas (read) ---
echo "=== DELTAS (abp_surface, key verse_id+position; every row in the file, first 20 printed) ==="
echo "STEP9-DRY's built copy (no list) -> this built copy: the list's only effect - must be ADDED rows only (changed 0, removed 0)"
$E delta --tag STEP9B --a "$OLD" --b "$D/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_old_new_built.tsv" --show 20 || { echo "STEP9-DRY2 RESULT: STOP - delta old -> new built copy (line above)"; exit 1; }
ch=$(awk -F'\t' 'NR > 1 && $2 != "ADDED"' "$D/step9_delta_old_new_built.tsv" | wc -l); ad=$(awk -F'\t' 'NR > 1 && $2 == "ADDED"' "$D/step9_delta_old_new_built.tsv" | wc -l)
echo "recovered rows (added over STEP9-DRY's built copy): $ad - changed or removed: $ch (must be 0)"
[ "$ch" = 0 ] || { echo "STEP9-DRY2 RESULT: STOP - the list changed or removed a row it should only add"; exit 1; }
echo "built -> its dry copy: what STEP9-APPLY would write (read)"
$E delta --tag STEP9B --a "$B" --b "$D/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_built.tsv" --show 20 || { echo "STEP9-DRY2 RESULT: STOP - delta built -> dry (line above); built untouched"; exit 1; }
echo "src-dry -> built-dry: the edition's effect on the chain, after the fix (read; STEP9-DRY: 184 = 4 / 14 / 166)"
$E delta --tag STEP9B --a "$D/src/dry.db" --b "$D/dry.db" --table abp_surface:verse_id+position --out "$D/step9_delta_srcdry_builtdry.tsv" --show 20 || { echo "STEP9-DRY2 RESULT: STOP - delta src dry -> built dry (line above)"; exit 1; }
# --- after: everything read-only stayed as it was ---
H1=$(sha256sum < "$H" | cut -d' ' -f1); echo "bh_scrape.db after: sha256 $H1 - unchanged: $([ "$H1" = "$H0" ] && echo yes || echo NO)"
[ "$H1" = "$H0" ] || { echo "STEP9-DRY2 RESULT: STOP - bh_scrape.db changed during the run - report this, do not re-run"; exit 1; }
[ -e "$H-journal" ] && { echo "STEP9-DRY2 RESULT: STOP - a -journal now sits beside $H"; exit 1; }
$E same --tag STEP9B --built "$B" --dir "$D" || { echo "STEP9-DRY2 RESULT: STOP - built differs from its prep state (lines above)"; exit 1; }
$E same --tag STEP9B --built "$S" --dir "$D/src" || { echo "STEP9-DRY2 RESULT: STOP - src differs from its prep state (lines above)"; exit 1; }
echo "copies: $D/dry.db $(stat -c %s "$D/dry.db") bytes, $D/src/dry.db $(stat -c %s "$D/src/dry.db") bytes"
echo "STEP9-DRY2 RESULT: READ DONE - gates 1, 2, 3 passed; built + src untouched; built's chain total $ar (builder $a1 / backfill $a2 / PN $a3), recovered $ad rows over STEP9-DRY; the deltas above are what STEP9-APPLY declares"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9-DRY2 reviewed (11/14) — REVIEW: ESCALATE (untraced sha + two STOPs beyond §9.117); mechanics clean
Verdict line verbatim: "REVIEW: ESCALATE - the full 64-character sha in gate 1 cannot be traced (the repo records only the prefix 9cbf2b18…), and two of the STOPs go beyond what §9.117 ruled. The mechanics check out."
- The sha: CC traced it to the STEP9-DRY log as pasted 11/14 ("differences: 4411 - …/step9_delta_src.tsv: 4411 lines + header,
  sha256 9cbf2b18766192df5fd578291e0ef02b746cab565fc4f9e26aa5bad5b355f7e4") and recorded it in full in the STEP9-DRY receipt.
- Two STOPs beyond the ruling, for the ruling chat to adopt or drop: (a) src → src-dry delta = STEP9-DRY's exactly (sha above);
  (b) STEP9-DRY's built copy → this built copy = ADDED rows only (the list may only add). Both run after their gates and can
  only stop a run, never pass a bad one.
- Cosmetic: the list row-count label no longer says "incl. header" (the header is not counted). No other change.

### Ruling (11/14, §9.118) — the two extra STOPs adopted; STEP9-DRY2 cleared; the stray first paste
Both extra STOPs adopted: (a) src → src-dry = STEP9-DRY's src delta exactly (sha 9cbf2b18…); (b) STEP9-DRY's built copy →
this built copy = ADDED rows only, its count = the recovered figure. **STEP9-DRY2 cleared as drafted.** Event: JP pasted it
at 22:35Z before the clearance and before `git pull`; it stopped at its own first guard ("PA has not pulled 32a39a10"),
exit 1, before `pre` — nothing made except `~/edition_upgrade_runs/step9_dry2_20261114.log` holding that STOP.
CC's choice for the stray log: **leave it where it is (kept as the record of that stop) and point the re-run at a new log
name** — the only change to the block is `L=~/edition_upgrade_runs/step9_dry2_run2_20261114.log`; the run folder
`step9_dry2_20261114` was never made, so it stays. Then JP: `git pull` in ~/bible-db, confirm HEAD = 32a39a10 or later,
paste the re-run.

### STEP9-DRY2 (log renamed) reviewed (11/14) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - the block is read-only and re-runs the gates ruled in §9.117, with the two extra STOPs adopted in §9.118. It changed in only the two lines you named, and the new log name collides with nothing the block or eu_step pre checks."
PA pulled to a9674438 (contains 32a39a10; later commits docs only) — JP's paste 11/14.

### STEP9-DRY2 ran (11/14, 22:48 UTC, PA HEAD a9674438, REF 32a39a10) — READ DONE, exit 0; all gates passed

Log `~/edition_upgrade_runs/step9_dry2_run2_20261114.log`; run folder `step9_dry2_20261114/`. built + src untouched (SAME OK
both); bh_scrape.db before = after, sha `5e9d4bb6f54cca08e62c631ae31594a23ae6f272220381741a0ba53486fb30bb` (the log's
"bh_scrape.db (read-only): 55865344 bytes, sha256 …" line); list 149 rows, sha `7033aceada33b5d66245191f4aea8cbc898e4c7e3597ecb861bc3779d02096ed`;
home 7,084,200 KB before.
- **Gate 1** src 346,111 / 13,183 / 31,836 / 391,130 — the list used 0 rows on src ("no slot with this token" ×149). **(a)** src →
  src-dry 4,411 + header, sha 9cbf2b18… = STEP9-DRY's. **Gate 2** pre-fill → src-dry 0.
- **Gate 3** list-filled slots on built-dry 163 (160 listed + 3 paired along: Num 26:39 pos 1, 4; Num 36:5 pos 5), checked 163,
  mismatches 0, unchecked 0 — every row OK incl. Gen 5:25/5:26 (built pos 1 ← src pos 2) and Est 5:9 (built pos 12 ← src 2/13).
- **(b)** STEP9-DRY built copy → this built copy: added 163, changed 0, removed 0 (sha 3e8ce53f…).
- **Built chain 346,113 / 13,181 / 31,847 / 391,141**; romanized 391,141; blanks 0; no-word-at-slot 0; PN refusals 631 (ambiguous
  6, blank-label 50, bridge-ambiguous 185, bridge-fail 127, no-match 263); respelling-list adds 163 (used 149 rows).
- built → built-dry: changed 538 / added 11 / removed 3,873 = 4,422 + header, sha
  `467fd9ba9c8e8a73271584558738b707e02033f795fcc8ac8e5f11294ef8a6f2`.
- src-dry → built-dry (the edition's effect, after the fix): changed 4 / added 17 / removed 6 = 27 + header, sha
  `b0fd29d163c371ae1262a50efb9c0a9ab037b7d31d752a55db2375a4e2d7403a`. The 20 printed: ADDED Gen 4:8 (88,2) + (88,22) Καϊν;
  Gen 5:25 (131,1) Μαθουσαλά ADDED / (131,2) REMOVED and Gen 5:26 (132,1) / (132,2) the same (slot shift 2 → 1);
  Gen 34:4 (985,1)/(985,2) Συχέμ ↔ είπε δε swapped; Gen 39:17 (1167,14) Εβραίος ADDED; Deu 33:6 (5817,1) Ρουβήν, (5817,6) Συμεών
  ADDED; Jos 2:4 (5874,19)/(5874,20) οίδα ↔ ουκ swapped; Jos 5:15 (5950,27) Ιησούν ADDED; Jdg 11:7 (6837,6) ουχ ADDED / (6837,7)
  REMOVED; 1Ki 21:15 (9467,4) Ιεζάβελ ADDED; 2Ki 23:35 (10201,6) Ιωακίμ ADDED / (10201,7) REMOVED; 1Ch 27:33 (11143,1) Αχιτόφελ
  ADDED. The other 7 are in the file; STEP9-APPLY prints all 27 before its write (the record gets them from that log).
- Observed (ruling chat, no ruling): built → built-dry now has removed 3,873 / changed 538 — the same two figures as src → src-dry.

### Rulings (11/14, §9.119)
1. **STEP9 declaration:** chain 346,113 / 13,181 / 31,847 / 391,141; built-dry fingerprint as prep reads it; built → dry 4,422 +
   header, sha 467fd9ba…; the 27-member edition delta sha b0fd29d1…; list sha 7033acea…; bh_scrape.db sha 5e9d4bb6…. Record all 27
   members. Draft STEP9-APPLY: the chain on built, with the list, gated on those figures; gate 3 re-run against the src-dry copy after
   the write; check OK on 149 untouched + schema; abp_surface = the dry copy; restore source `step9_dry2_20261114/before.db`. Reviewer
   mechanics; the write gate is ruled in the ruling chat.
2. The §9.112 9a/9b/9c code-change proposal is written against **391,141** and the 10/25 fill figures as the restore reads them;
   reviewer, then ruling, before 9a is drafted. STEP9-APPLY does not wait on it.

## STEP9-APPLY drafted (11/14, §9.119 ruling 1)

Gated on the STEP9-DRY2 figures as ruled. **Before the write, each miss is a STOP, built untouched:** REF 32a39a10 + entity_resolution.py;
pre; the dry run's files present; its built chain = 346,113 / 13,181 / 31,847 / 391,141; dry delta built → dry 4,423 lines / 467fd9ba…;
edition delta 28 lines / b0fd29d1… (and **its 27 members printed in full**, for the record); list sha 7033acea…; bh_scrape.db
5e9d4bb6…, no journal; `same` (built unchanged since STEP9-DRY2's prep). **The write:** the STEP9-DRY2 chain, unchanged, on built
(abp_surface only). **After, each miss → CHECK naming `step9_dry2_20261114/before.db`:** chain figures + romanized 391,141;
pn_list.tsv and pn_refused.tsv byte-identical to the dry run's; `check` (149 untouched + schema; abp_surface = the dry copy); before.db
→ built = the declared built → dry delta (sha 467fd9ba…); gate 3 re-run on built against the src-dry copy (filled 163, checked = filled,
mismatches 0, unchecked 0); bh_scrape.db + list unchanged.
Local test (made-up dbs; a fake STEP9-DRY2 folder made by the cleared block; declared figures swapped for the fake run's): DONE, exit 0
(built = dry copy, before → after = declared delta, gate 3 clean); re-paste → STOP; built already written → "built changed since the dry
run" STOP; a dry-run file altered → CHECK naming the restore source. pn_refused.tsv only has to exist (an empty file is a legitimate
"0 refused"; on PA it holds 631 lines).

### Block STEP9-APPLY (GATE REF 32a39a10; WRITES built: abp_surface only, 395,003 → 391,141) — for the ruling chat
```bash
set +H
L=~/edition_upgrade_runs/step9_apply_20261114.log
if [ -e "$L" ]; then echo "STEP9-APPLY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=32a39a10
echo "GATE REF ${REF} - STEP9-APPLY rebuild-words step 9 on BUILT (surface builder + both backfills with the respelling list + translit), gated on the STEP9-DRY2 figures (sec 9.119) - WRITES built: abp_surface only (395,003 -> 391,141) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9-APPLY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
[ -f scripts/eu_step.py ] && [ -f scripts/pn_edition_spelling.tsv ] || { echo "STEP9-APPLY RESULT: STOP - PA has not pulled $REF"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
H=~/bible-db/bh_scrape.db
LIST=scripts/pn_edition_spelling.tsv
DD=~/edition_upgrade_runs/step9_dry2_20261114
D=~/edition_upgrade_runs/step9_apply_20261114
E="python3 scripts/eu_step.py"
TAB=$'\t'
# --- declared figures: STEP9-DRY2 log (11/14 22:48Z), ruled 11/14 (sec 9.119) ---
XF="346113 13181 31847 391141"
XB=467fd9ba9c8e8a73271584558738b707e02033f795fcc8ac8e5f11294ef8a6f2; XBL=4423
XE=b0fd29d163c371ae1262a50efb9c0a9ab037b7d31d752a55db2375a4e2d7403a; XEL=28
XLIST=7033aceada33b5d66245191f4aea8cbc898e4c7e3597ecb861bc3779d02096ed
XH=5e9d4bb6f54cca08e62c631ae31594a23ae6f272220381741a0ba53486fb30bb
num() { sed -n "/$2/{s/.*: *//; s/,//g; s/[^0-9].*//; p; q}" "$1"; }
dlt() { sed -n "/delta [0-9,]*/{s/.*delta \([0-9,]*\).*/\1/; s/,//g; p; q}" "$1"; }
# the step-9 chain - the STEP9-DRY2 chain, unchanged, here on built ($1); outputs kept in $2
chain() {
  local db=$1 o=$2 n1 n2 d2 n3 d3 a3 m3 nt nr
  echo "--- 1/4 build_abp_surface (drops + re-creates abp_surface)"
  python3 scripts/build_abp_surface.py "$db" --bh "$H" > "$o/1_build.out" 2>&1 || { cat "$o/1_build.out"; echo "chain: build_abp_surface failed"; return 1; }
  sed -n '/form found\|shows a line\|books with no source\|Wrote/p' "$o/1_build.out"
  n1=$(sed -n 's/.*Wrote \([0-9]*\) rows.*/\1/p' "$o/1_build.out"); [ -n "$n1" ] || { echo "chain: no Wrote line"; return 1; }
  echo "--- 2/4 backfill_abp_surface --apply"
  python3 scripts/backfill_abp_surface.py "$db" --bh "$H" --apply > "$o/2_backfill.out" 2>&1 || { cat "$o/2_backfill.out"; echo "chain: backfill_abp_surface failed"; return 1; }
  sed -n '/existing rows\|NEW rows\|same-as-dictionary\|ambiguity\|Wrote/p' "$o/2_backfill.out"
  n2=$(num "$o/2_backfill.out" "NEW rows to add"); d2=$(dlt "$o/2_backfill.out")
  [ -n "$n2" ] && [ "$n2" = "$d2" ] || { echo "chain: backfill NEW ($n2) != rows written ($d2)"; return 1; }
  echo "--- 3/4 backfill_pn_surface --apply (respelling list $LIST; refused slots -> $o/pn_refused.tsv; list use -> $o/pn_list.tsv)"
  python3 scripts/backfill_pn_surface.py "$db" --bh "$H" --apply --dump-refused "$o/pn_refused.tsv" --dump-list "$o/pn_list.tsv" > "$o/3_pn.out" 2>&1 || { cat "$o/3_pn.out"; echo "chain: backfill_pn_surface failed"; return 1; }
  sed -n '1,/coverage by book/p' "$o/3_pn.out" | sed '/coverage by book/d'; sed -n '/refused-slot dump\|respelling-list dump\|Wrote/p' "$o/3_pn.out"
  n3=$(num "$o/3_pn.out" "NEW rows to add"); d3=$(dlt "$o/3_pn.out")
  [ -n "$n3" ] && [ "$n3" = "$d3" ] || { echo "chain: PN backfill NEW ($n3) != rows written ($d3)"; return 1; }
  a3=$(sed -n '/arithmetic:/{s/.*= *//; s/ .*//; s/,//g; p; q}' "$o/3_pn.out"); m3=$(sed -n '/arithmetic:/{s/.*must equal *//; s/[^0-9,].*//; s/,//g; p; q}' "$o/3_pn.out")
  [ -n "$a3" ] && [ "$a3" = "$m3" ] || { echo "chain: PN arithmetic $a3 != $m3"; return 1; }
  echo "--- 4/4 build_abp_translit"
  python3 scripts/build_abp_translit.py "$db" > "$o/4_translit.out" 2>&1 || { cat "$o/4_translit.out"; echo "chain: build_abp_translit failed"; return 1; }
  cat "$o/4_translit.out"
  nt=$(sed -n 's/^Filled \([0-9]*\).*/\1/p' "$o/4_translit.out")
  nr=$(sqlite3 -readonly "$db" "SELECT count(*) FROM abp_surface") || { echo "chain: count failed"; return 1; }
  echo "chain total: builder $n1 + backfill $n2 + PN backfill $n3 = $((n1 + n2 + n3)); table now $nr; romanized $nt"
  [ "$nr" = "$((n1 + n2 + n3))" ] || { echo "chain: table count is not the sum of the three passes"; return 1; }
  echo "$n1 $n2 $n3 $nr $nt" > "$o/figures.txt"
}
# --- before the write: every miss is STOP, built untouched ---
git diff --quiet "$REF" HEAD -- entity_resolution.py || { echo "STEP9-APPLY RESULT: STOP - entity_resolution.py differs from $REF; built untouched"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no -- entity_resolution.py)" ] || { echo "STEP9-APPLY RESULT: STOP - entity_resolution.py has uncommitted edits on PA; built untouched"; exit 1; }
echo "entity_resolution.py (imported by the PN backfill) = $REF, unedited: OK"
$E pre --tag STEP9A --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP9-APPLY RESULT: STOP - pre (line above); built untouched"; exit 1; }
for f in state.json before.db dry.db src/dry.db built_run/figures.txt built_run/pn_list.tsv step9_delta_built.tsv step9_delta_srcdry_builtdry.tsv; do [ -s "$DD/$f" ] || { echo "STEP9-APPLY RESULT: STOP - the dry run's $f is missing or empty in $DD; built untouched"; exit 1; }; done
[ -f "$DD/built_run/pn_refused.tsv" ] || { echo "STEP9-APPLY RESULT: STOP - the dry run's built_run/pn_refused.tsv is missing in $DD; built untouched"; exit 1; }
read -r f1 f2 f3 f4 _f5 < "$DD/built_run/figures.txt"; echo "dry run's built chain: $f1 / $f2 / $f3 / $f4 (declared $XF)"
[ "$f1 $f2 $f3 $f4" = "$XF" ] || { echo "STEP9-APPLY RESULT: STOP - the dry run's figures are not the declared ones; built untouched"; exit 1; }
s=$(sha256sum < "$DD/step9_delta_built.tsv" | cut -d' ' -f1); n=$(wc -l < "$DD/step9_delta_built.tsv"); echo "dry delta built -> dry: $n lines (expect $XBL), sha256 $s (expect $XB)"
[ "$s" = "$XB" ] && [ "$n" = "$XBL" ] || { echo "STEP9-APPLY RESULT: STOP - not the declared built -> dry delta; built untouched"; exit 1; }
s=$(sha256sum < "$DD/step9_delta_srcdry_builtdry.tsv" | cut -d' ' -f1); n=$(wc -l < "$DD/step9_delta_srcdry_builtdry.tsv"); echo "dry delta src-dry -> built-dry: $n lines (expect $XEL), sha256 $s (expect $XE)"
[ "$s" = "$XE" ] && [ "$n" = "$XEL" ] || { echo "STEP9-APPLY RESULT: STOP - not the declared edition delta; built untouched"; exit 1; }
echo "--- the 27 members of src-dry -> built-dry (the edition's effect on the chain, declared; for the record):"
sed '1d; s/\t/ | /g; s/^/  /' "$DD/step9_delta_srcdry_builtdry.tsv"
s=$(sha256sum < "$LIST" | cut -d' ' -f1); echo "respelling list: sha256 $s (expect $XLIST)"
[ "$s" = "$XLIST" ] || { echo "STEP9-APPLY RESULT: STOP - the respelling list is not the one the dry run used; built untouched"; exit 1; }
[ -e "$H-journal" ] && { echo "STEP9-APPLY RESULT: STOP - a -journal sits beside $H; built untouched"; exit 1; }
h0=$(sha256sum < "$H" | cut -d' ' -f1); echo "bh_scrape.db before: sha256 $h0 (expect $XH)"
[ "$h0" = "$XH" ] || { echo "STEP9-APPLY RESULT: STOP - bh_scrape.db is not the one the dry run read; built untouched"; exit 1; }
$E same --tag STEP9A --built "$B" --dir "$DD" || { echo "STEP9-APPLY RESULT: STOP - built changed since the dry run (lines above); built untouched"; exit 1; }
mkdir "$D/run" || { echo "STEP9-APPLY RESULT: STOP - cannot make the run folder; built untouched"; exit 1; }
# --- the write ---
echo "=== APPLY: the step-9 chain on BUILT ($B) - writes abp_surface only ==="
chain "$B" "$D/run"; r=$?
echo "chain exit $r (expect 0)"
# --- after the write: every miss is CHECK ---
FL=""
[ "$r" = 0 ] || FL="$FL chain"
w=""; [ -s "$D/run/figures.txt" ] && read -r w1 w2 w3 w4 w5 < "$D/run/figures.txt" && w="$w1 $w2 $w3 $w4"
echo "built chain: $w (declared $XF); romanized ${w5:-?} (expect ${XF##* })"
[ "$w" = "$XF" ] && [ "${w5:-}" = "${XF##* }" ] || FL="$FL figures"
for f in pn_list.tsv pn_refused.tsv; do a=$(sha256sum < "$D/run/$f" 2>/dev/null | cut -d' ' -f1); b=$(sha256sum < "$DD/built_run/$f" | cut -d' ' -f1); echo "$f = the dry run's: $([ "$a" = "$b" ] && echo yes || echo NO) ($a)"; [ "$a" = "$b" ] || FL="$FL $f"; done
CHK=$($E check --tag STEP9A --built "$B" --dir "$DD" --written abp_surface 2>&1); k=$?; echo "$CHK"; [ "$k" = 0 ] || FL="$FL check"
VAL=$($E delta --tag STEP9A --a "$DD/before.db" --b "$B" --table abp_surface:verse_id+position --out "$D/step9_delta_before_after.tsv" --show 5 --expect-sha "$XB" 2>&1); v=$?; echo "$VAL"
echo "built before -> built after = the declared built -> dry delta (sha $XB): $([ "$v" = 0 ] && echo yes || echo NO)"; [ "$v" = 0 ] || FL="$FL delta"
# gate 3 re-run: every slot the list filled on built = src-dry's form at its matching slot (the STEP9-DRY2 check, now on built)
echo "=== GATE 3 re-run on built after the write ==="
sed -n '/^[A-Z0-9][A-Za-z0-9]*\t[0-9]/p' "$LIST" | awk -F'\t' -v OFS='\t' '{n = split($6, part, "; "); for (i = 1; i <= n; i++) if (part[i] ~ /^built pos [0-9]+ <- src pos [0-9|]+ /) {split(part[i], w, " "); print $1, $2, $3, w[3], w[7]}}' > "$D/list_slots.tsv"
awk -F'\t' '$1 == "paired" || $1 == "paired along"' "$D/run/pn_list.tsv" > "$D/filled.tsv"
nf=$(wc -l < "$D/filled.tsv")
V=$(cut -f2-4 "$D/filled.tsv" | sort -u | awk -F'\t' '{printf "%s(v.book = '"'"'%s'"'"' AND v.chapter = %s AND v.verse = %s)", (NR > 1 ? " OR " : ""), $1, $2, $3}')
nc=0; nm=0; nu=0
if [ -n "$V" ]; then
  FQ="SELECT v.book, v.chapter, v.verse, s.position, s.form FROM abp_surface s JOIN verses v ON v.id = s.verse_id WHERE $V"
  sqlite3 -readonly -separator "$TAB" "$DD/src/dry.db" "$FQ" > "$D/src_forms.tsv" || FL="$FL gate3-read"
  sqlite3 -readonly -separator "$TAB" "$B" "$FQ" > "$D/built_forms.tsv" || FL="$FL gate3-read"
  awk -F'\t' -v FIG="$D/gate3_figures.txt" '
    FNR == 1 {f++}
    f == 1 {sp[$1 FS $2 FS $3 FS $4] = $5; next}
    f == 2 {sf[$1 FS $2 FS $3 FS $4] = $5; next}
    f == 3 {bf[$1 FS $2 FS $3 FS $4] = $5; next}
    f == 4 {k = $2 FS $3 FS $4 FS $5
            if ($1 == "paired") {p = (k in sp) ? sp[k] : ""} else {p = $5}
            if (p == "") {print "UNCHECKED | " $1 " | " $2 " " $3 ":" $4 " pos " $5 " | " $8; nu++; next}
            n = split(p, ps, "|"); srcf = ""; ok = 0
            for (i = 1; i <= n; i++) {x = $2 FS $3 FS $4 FS ps[i]; srcf = srcf (i > 1 ? " / " : "") ps[i] "=" ((x in sf) ? sf[x] : "(none)"); if ((x in sf) && sf[x] == $8) ok = 1}
            b = (k in bf) ? bf[k] : "(none)"
            if (b != $8) ok = 0
            if (ok == 0) print "MISMATCH | " $1 " | " $2 " " $3 ":" $4 " pos " $5 " | built " b " | src pos " srcf
            nc++; if (ok == 0) nm++}
    END {printf "GATE 3 figures: checked %d - mismatches %d - unchecked %d\n", nc + 0, nm + 0, nu + 0 > FIG}' \
    "$D/list_slots.tsv" "$D/src_forms.tsv" "$D/built_forms.tsv" "$D/filled.tsv"
  cat "$D/gate3_figures.txt"
  read -r _g _3 _f _c nc _m _x nm _u _y nu < "$D/gate3_figures.txt"
fi
echo "GATE 3 on built: filled via the list $nf (dry run: 163), checked $nc, mismatches $nm, unchecked $nu (MISMATCH/UNCHECKED lines above, none when clean)"
[ "$nf" = 163 ] && [ "$nc" = "$nf" ] && [ "$nm" = 0 ] && [ "$nu" = 0 ] || FL="$FL gate3"
h1=$(sha256sum < "$H" | cut -d' ' -f1); hj=none; [ -e "$H-journal" ] && hj=PRESENT
echo "bh_scrape.db after: sha256 $h1 (expect $XH); journal beside it: $hj (expect none)"
[ "$h1" = "$XH" ] && [ "$hj" = none ] || FL="$FL bh_scrape"
s=$(sha256sum < "$LIST" | cut -d' ' -f1); [ "$s" = "$XLIST" ] || FL="$FL list"
if [ -z "$FL" ]; then
  echo "STEP9-APPLY RESULT: DONE - built abp_surface rebuilt: 391,141 (346,113 / 13,181 / 31,847) = the dry run; = the dry copy (check OK, 149 untouched + schema); before -> after = the declared delta (sha 467fd9ba...); gate 3: 163 list-filled slots = src's Greek; bh_scrape.db + list unchanged"; exit 0
fi
echo "STEP9-APPLY RESULT: CHECK -$FL differ (lines above). Restore source for abp_surface: $DD/before.db"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

## 9a / 9b / 9c code-change proposal (11/14, CC; §9.112 / §9.119 ruling 2) — design only, no code yet

Written against step 9's declared total **391,141** and the 10/25 fill as the restore reads it (the frozen snapshot
`abp_surface_fill_20261025.tsv`, pinned sha d9435bde…: 4,411 rows = 3,873 inserts + 538 updates). **Two code REFs**, so each is
small and reviewed on its own: **REF-A now** (9a + 9b), **REF-B at 9c** (the re-freeze needs 9a's real report). Every new
option defaults to today's behaviour, so the same-code /rebuild-words steps 9a/9b keep working exactly as written.

**REF-A — `restore_surface_fill.py` (9a):**
1. **`--base N`** — the builder-chain total the restore lays the fill on (G1a). Default 391,130 (today's constant). The edition
   upgrade passes `--base 391141`. G1a = "table == N, else STOP" exactly as now; the write-time recheck (:222) uses the same N.
2. **After-count (G1) computed, not fixed:** N + the inserts actually written (all 3,873 → 391,141 + 3,873 = **395,014**). Every
   other post-write check (written rows = snapshot form + new-slot translit; every other row unchanged; new rows = exactly the insert
   slots; no NBSP / ἡ; translit rule 0; quick_check) stays as is.
3. **Snapshot gate S unchanged** — 4,411 / 3,873 / 538 and the sha pin describe the frozen FILE, which this lane does not change.
4. **§4.9 reason 6, expressed as two optional declared slot lists**, each a TSV made from the 9a DRY RUN's own `--report` after the
   ruling chat rules on its member list, sha-pinned in the apply block:
   - **`--key2-alone FILE`** — slots to place by key 2 alone. Only reason-6 slots may be listed (key 2 found exactly one slot;
     key 1 found none, or several without key 2's slot — `dryrun_rekey_fill.decide` :213-218); each line names the slot (book,
     chapter, verse, old position) and the new position the dry run reported. At apply time each must still be reason 6 with that
     key-2 slot, and must still pass the update/insert precondition and the Analytical-Lexicon check, else STOP.
   - **`--leave-unplaced FILE`** — slots declared to stay unplaced (left to a follow-up), each with its reason.
   - **G2 becomes:** every snapshot slot is placed, or on the key-2 list, or on the leave list — exactly. An unplaced slot on no list,
     a listed slot that now places normally, or a listed slot that is not in the snapshot → STOP, nothing written. With neither list
     given, G2 is today's "unplaced = 0".
   - The verse set ("inside a changed-English verse") is the ruling chat's call on the member list; the restore does not decide it.
5. **`--prefill`** stays optional; the edition upgrade drops it (charter §4.9). No change.

**REF-A — `health_check.py` (9b):** **`--surface-floor=N`** overrides the 395,003 floor for that run (default unchanged — the live
nightly keeps 395,003 until the swap). 9b on built runs with N = 9a's after-count; the floor line must read 0. The constant itself
is re-pinned to the restored total **in the swap commit** (charter §7 re-pin list: "health floor").

**REF-B — `snapshot_surface_fill.py --replace` (9c), proposed now, coded after 9a's report exists:**
- **What the inputs become.** The script freezes "source with the fill minus the pre-fill table". For built that pair is
  **`--src` = built after 9a** (fill at the new slots; its words are the "old words" a FUTURE rebuild re-keys from — which is what the
  snapshot must carry) and **`--prefill` = 9a's `before.db`** (built's abp_surface after step 9, before the restore; G0 reads only
  `abp_surface` from the pre-fill side). Charter §6's "before side = `<src>`" does not fit the script: src's slots are the OLD
  positions, so a diff against it would mix the edition's own moves into the fill. → **For a ruling:** the "before" side is built's
  step-9 table; src stays the 10/25 provenance (its snapshot + the pre-fill copy are kept until the new freeze passes `--check` against
  the swapped live, charter §7, unchanged).
- **G0 changes source.** Today G0 checks the diff against the approved 10/25 CSV keyed at the OLD slots (`dryrun_rekey_fill.g0`,
  :266-293, counts fixed at :57-58). New option **`--from-restore REPORT`** (9a's apply `--report`, per slot: old → new position,
  action, form, placed/declared): G0 = the diff is exactly the placed slots at their NEW positions, forms = the report's, counts taken
  from the report. Without the option, G0 is today's.
- **In the same 9c commit:** the new frozen TSV + `.sha256`; the restore's `SNAPSHOT_SHA256` pin and its file counts (N_ROWS /
  N_INSERT / N_UPDATE = the new file's); the restore's default base (391,141); the `dryrun_rekey_fill` counts its `--check` path
  uses; and §9.87's punct member file re-frozen at **607** (§9.113). The health floor waits for the swap commit (above).

**Tests (REF-A):** `--base` default = today (the existing restore tests unchanged); `--base` other than the table → G1a STOP; after-
count = base + inserts; key-2 list places a reason-6 slot and only that; a listed slot that is not reason 6 → STOP; an unplaced slot on
no list → STOP, nothing written; leave list → that slot unwritten, after = base + the other inserts; `--surface-floor` changes only the
floor line. Each new check proven able to fail.

**Order after REF-A is pushed:** 9a DRY RUN (`--base 391141`, no lists) → its placed / agree-strong / agree-weak / unplaced-by-reason
member list read against the changed-English verses (§4.9) → ruling (key 2 alone / leave) → the lists frozen from the report → 9a APPLY
→ 9b → REF-B → 9c.

### STEP9-APPLY reviewed (11/14) — REVIEW: ESCALATE (write, §9.90); one finding, closed
Verdict line verbatim: "REVIEW: ESCALATE - STEP9-APPLY writes to built, so under §9.90 it goes to the ruling chat. The mechanics check out with one exception: the full bh_scrape.db sha (XH) appears nowhere in the repo except in the block itself."
CC closed it: the STEP9-DRY2 log prints "bh_scrape.db (read-only): 55865344 bytes, sha256 5e9d4bb6f54cca08e62c631ae31594a23ae6f272220381741a0ba53486fb30bb";
the STEP9-DRY2 receipt above now carries it in full. Every other declared figure and sha traced by the reviewer to the receipt.
Noted by the reviewer: on a mismatch `check` writes `step9_dry2_20261114/check_delta_abp_surface.tsv` (a new file, never an overwrite).
Goes to the ruling chat for the write gate (§9.119 ruling 1).

### 9a/9b/9c proposal reviewed (11/14) — REVIEW: ESCALATE (design change, §9.90/§9.112); four gaps → proposal v2
Verdict line verbatim: "REVIEW: ESCALATE - this is a design change to builders and gates (out of reviewer scope under sec 9.90 / sec 9.112), so it goes to the ruling chat. Most claims about current behaviour check out against the code, but there are four gaps the proposal needs to close before code is written (F1-F4 below)."
Current-behaviour claims confirmed (constants, :222, decide :202-221 → reason 6 always has one key-2 slot, G0 reads only
abp_surface from the pre-fill side — it reads verses and the CSV from the src side). Arithmetic 395,014 correct with no leave-list
inserts. 9c before-side: a diff against src WOULD mix edition moves into the fill (G0 diffs whole slot rows).

## 9a / 9b / 9c proposal v2 (11/14, CC) — closes F1-F4; still design only

- **F4 — one code REF, as §9.112 says.** The split is withdrawn. The re-freeze code can be written and tested now: the restore's
  `--report` already carries every column it needs (`write_report` :182-193: book, chapter, verse, old/new position, action, cls,
  form, result, reason, lexicon). All of 9a, 9b and 9c's code lands in one REF before 9a is drafted.
- **F1 — the "already restored" path.** The restore no longer decides restoring vs already-restored from a fixed total. It runs the
  re-key first, then: written set W = placed slots + key-2-listed slots (leave-listed slots are never written); expected after =
  `--base` + the inserts in W. Table = base → restoring; table = expected after AND every slot in W already holds its form →
  ALREADY RESTORED (no write); anything else → STOP. With no lists and the default base this gives 391,130 + 3,873 = 395,003 —
  today's behaviour exactly. The write-time recheck (:222) and G1 (:243) use base and expected-after.
- **F2a — key-2-alone slots get the same checks as normal ones.** A listed reason-6 slot is treated as placed at its key-2 slot and
  then runs the SAME update/insert preconditions (reasons 3/4) and the SAME Analytical-Lexicon check (:162-176). A slot whose class is
  not a Lexicon class has no second witness today either; the 9a dry run's member list will show every reason-6 slot's class and
  lexicon result, so the ruling sees which key-2-alone slots rest on key 2 alone with no witness.
- **F2b — the write covers only W.** apply() writes placed + key-2-listed slots and skips leave-listed ones explicitly (today it
  would STOP on their empty new position, :228 — safe, but now stated and tested).
- **F2c — the leave list re-checks its reason.** Each leave line carries the reason the dry run reported; at apply time the slot
  must still be unplaced with that same reason, else STOP — as strict as the key-2 list.
- **Changed-English verses** (charter §4.9: a reason-6 slot outside a changed verse is a real miss): not enforced in code; the
  ruling on the dry run's member list is where it is checked. Stated so the ruling can accept or reject that.
- **F3 — the 9c inputs, named:**
  - **Pre-fill side:** the 9a APPLY block makes it, with `eu_step prep --save abp_surface` before its write →
    `~/edition_upgrade_runs/step9a_apply_<date>/before.db` = built's abp_surface after step 9 and before 9a. (Not
    `step9_dry2_20261114/before.db`, which is built BEFORE step 9.) → **For a ruling:** charter §6 9c's "before side = `<src>`"
    amended to this named copy.
  - **`snapshot_surface_fill.py --from-restore REPORT`** (the 9a APPLY report): replaces `--csv` (then not required) and G0's CSV
    match. G0 = the diff (built after 9a minus the pre-fill side) is exactly the report's written set W at its NEW positions, form
    for form; insert/update counts from the report; action and cls for each snapshot row from the report (today from the CSV via
    g0's `writes`); verse names (`vold`) from the src side's verses, as today; old form/translit of updates from the pre-fill side,
    as today. The row-count check (:282-283, N_ROWS 4,411) becomes "= the report's |W|" under `--from-restore`.
  - **Step 1a `--check` after the re-freeze:** the same three inputs, pinned — the new frozen TSV (sha in the restore), the 9a report
    committed beside it with its own `.sha256`, and the pre-fill table kept on PA like today's `~/bible.db.pre-surface-fill-20261025`.
    `--check --from-restore <pinned report>` re-derives the rows from a fresh copy of live and must match byte for byte, so future
    same-code /rebuild-words step 1a still passes. rebuild-words.md 1a and 9a commands updated in the same 9c commit.
  - **Counts re-pinned in the 9c commit:** restore N_ROWS / N_INSERT / N_UPDATE (the new file's), its SNAPSHOT_SHA256, its default
    base (391,141); `dryrun_rekey_fill` keeps 3,873 / 538 / EXPECT_DIFF 4,411 / 538 for the 10/25 files (they describe those files);
    the `--from-restore` path takes its counts from the report, never from those constants. §9.87 punct file re-frozen at 607 in the
    same commit. Health floor at the swap commit.
- **Tests added for v2:** already-restored with lists (after = base + W's inserts); key-2-alone slot failing the lexicon / precondition
  → STOP; leave slot whose reason changed → STOP; leave slot never written; `--from-restore` G0 matches only W at new positions
  (a moved, unlisted, or extra row → STOP); `--check --from-restore` byte-for-byte; every default path = today's.

**Rulings asked:** (a) one REF (F4) — CC now follows §9.112 as written; (b) charter §6 9c "before side" → the named step-9a copy;
(c) the changed-English-verse test left to the ruling on the member list, not code; (d) go-ahead to write the code to v2.

### Rulings (11/14, §9.120) — 9a/9b/9c proposal v2 approved
(a) one code change — approved. (b) charter §6 9c "before side = `<src>`" → the named post-step-9 copy (F3) — approved; the charter
edit goes in the same commit as the code, the record citing the old wording beside the new. (c) the "inside a changed-English verse"
test stays a ruling-chat judgement on the dry member list, not code — approved. (d) write the code to v2. Tests: F1 after-count
with no lists reproduces 395,003 on the 10/25 shapes; a key-2 slot failing the form check STOPs; a leave-list slot that has become
placeable STOPs; the re-freeze from a 9a report equals a re-freeze from the 10/25 list on made-up data where both exist. Reviewer on
code + tests; ruling; push → new code REF; 9a drafted only after that REF. STEP9-APPLY: the ruling chat had not received the block —
to be brought with the reviewer's verdict for the write gate.

## 9a / 9b / 9c code (11/14, CC; to v2 under §9.120) — in the working tree, NOT committed until ruled

- **`restore_surface_fill.py`:** `--base N` (default 391,130); `after_count()` = base + inserts among written slots (placed +
  key-2-listed); the re-key runs first, then G1a: table = base → restoring, = after-count → the ALREADY check, else STOP;
  `--key2-alone TSV` (book chapter verse old_position new_position) — a listed slot must be reason 6 with exactly that key-2
  slot, is then placed there and runs the same preconditions 3/4 + Lexicon check; `--leave-unplaced TSV` (book chapter verse
  old_position reason) — must end unplaced with exactly that reason; listed slots must be snapshot slots, on one list only;
  G2 = no undeclared unplaced slot and no listed slot off its listing; `apply()` writes placed + key-2-listed only, checks
  base under the write lock and the after-count before COMMIT. Report format unchanged (listed slots marked in `detail`).
  Docstring gates updated. With no options the BEHAVIOUR is today's (the 22 existing restore tests pass unchanged); the
  OUTPUT is not line for line — corrected 11/14 after review (D5): a new "G1 after-count" summary line, and the G1a lines now
  print after the re-key instead of before it.
- **`health_check.py`:** `--surface-floor=N` for that run (constant 395,003 unchanged; re-pinned at the swap).
- **`snapshot_surface_fill.py`:** `--from-restore REPORT` (exactly one of it and `--csv`): `g0_report` — the diff (src minus
  pre-fill) = exactly the report's placed slots at their new positions, forms equal, inserts not on the pre-fill side, changed
  pre-fill rows = exactly the updates; action/cls from the report; row count and receipt counts from the report; `--check`
  takes it too (step 1a after the re-freeze).
- **Charter §6 9c amended** in the same change (old wording cited in place): before side = the named post-step-9 copy.
- **Tests** (`tests/test_surface_fill_restore.py`, 39 pass, was 22): the four ruled — F1 after-count 391,130 + 3,873 = 395,003
  with no lists on the 10/25 shapes (and 395,014 on 391,141); a key-2 slot failing the form check STOPs (nothing written); a
  leave-listed slot that has become placeable STOPs; the re-freeze from a 9a report = the 10/25 re-freeze, byte for byte (and
  its `--check` reads CURRENT) — plus: `--base` moves G1a; a key-2 slot placed and written (after 5); key-2-listed but places
  normally / at the wrong slot → STOP; leave list leaves the slot, after = base + 2, a second run reads ALREADY; leave reason
  changed → STOP; an unplaced slot on no list → STOP; a listed slot not in the snapshot → STOP; re-freeze on a moved layout keys
  the new slots; a leave-listed slot is not frozen; a re-freeze diff holding a row the report does not → STOP; `--csv` and
  `--from-restore` exclusive; `--surface-floor`. Proven able to fail: with the leave reason check removed, two tests fail; with
  the re-freeze G0 set check removed, its test fails.

### 9a/9b/9c code reviewed (11/14) — REVIEW: ESCALATE (code change, §9.90); D1-D6 → fixed / recorded
Verdict line verbatim: "REVIEW: ESCALATE - this is a code change to builders and gates (restore, health check, re-freeze), so under sec 9.90 it goes to the ruling chat whatever I find. The core logic matches v2 and fails safe, but I found one real defect (D1), three gaps against v2 or the ruling (D2-D4), and CC's \"output unchanged line for line\" claim is not true (D5)."
Reviewer also: no options → behaviour unchanged; key-2 path places only reason 6 at exactly the listed slot; no new way to accept a
wrong table; g0_report sound; the four ruled tests real (the 395,003 one on the real constants).
- **D1 (defect) — FIXED.** A leave-listed slot unplaced for reason 3/4 read "now places" on a later run (the already-restored pass
  skips preconditions) and was counted as a written insert. Now: on a not-at-base table, a leave-listed reason-3/4 slot must NOT hold
  the fill form and is taken as unplaced with its listed reason (so not counted); if it holds the fill form → STOP. Test: reason-3 slot
  left, apply (after 5), second run ALREADY; then the slot given the fill form → "holds the fill form" STOP.
- **D2 — tests ADDED** for a key-2 slot failing the Lexicon check (reason 5, fill_resolved slot, no Lexicon row → STOP, nothing
  written) and for its insert target being filled (reason 4 → STOP), beside the existing precondition-3 test. For the ruling chat:
  "form check" now covered as all three (3, 4, 5).
- **D3 — DONE in this change.** `--from-restore` pins the report: under `--check` a `<report>.sha256` beside it is required and must
  match (missing or wrong → STALE SNAPSHOT); under a re-freeze it is verified when present and the report's sha is printed for
  pinning. Test: check without it → STOP; with it → CURRENT; report changed → STOP.
- **D4 — recorded as a known difference.** The 10/25 G0 checks each update's pre-fill old form against the approved CSV; `g0_report`
  checks the changed pre-fill rows are exactly the update slots (the report has no old_form column). Restore precondition 3 checks
  the old form at apply time. For the ruling chat to accept.
- **D5 — corrected** in the code summary above.
- **D6:** `health_check.py --surface-floor N` (two words) now exits with "give the floor as --surface-floor=N" instead of silently
  checking the default (tested); `g0_report` requires every column it reads (book … form, result) and STOPs cleanly otherwise
  (tested); `apply()` now filters leave-listed slots explicitly. Further deliberate breaks, each caught: key-2 slot match removed →
  the wrong-slot test fails; listed-slot-in-snapshot check removed → its test fails; after-count fixed at base + 3 → three tests fail;
  the D1 fix removed → its test fails.
Tests: 43 pass (22 earlier unchanged + 21 new).

### 9a/9b/9c code re-reviewed after the fixes (11/14) — REVIEW: ESCALATE (code change); D1 closed, no new defect
Verdict line verbatim: "REVIEW: ESCALATE - still a code change to builders and gates, so it goes to the ruling chat under sec 9.90. D1 is closed and I found no new defect in the changed code. Two small points remain for the ruling chat (R1, R2)."
- **R2 — FIXED:** an empty `<report>.sha256` now gives a clean STOP ("… != its .sha256 (empty file)"), tested. (The same pattern in
  the existing `read_snapshot` is left as it was — not part of this change.)
- **R1 — for the ruling chat:** the report is checked against the `.sha256` beside it; the frozen TSV's sha is pinned in code
  (`SNAPSHOT_SHA256`), the report's is not, so a changed report with a regenerated `.sha256` would pass `--check`. CC recommends a code
  pin for the report (`REPORT_SHA256` beside `SNAPSHOT_SHA256` in restore_surface_fill.py, checked by `--check`) **in the 9c commit**,
  where both shas first exist.
- Still for the ruling chat: D4 (known difference: `g0_report` checks the changed pre-fill rows are exactly the updates, not each
  update's old form; restore precondition 3 checks it at apply time).
Tests: 43 pass. Code + tests + charter edit still uncommitted until the ruling.

### Rulings (11/14, §9.121) — 9a/9b/9c code APPROVED; pushed as one code REF
- D4 accepted as a known difference (the restore checks each old form at write time; the re-freeze checks the changed pre-fill rows
  are exactly the update set). Not a gap to close now.
- R1 adopted: the 9a report's fingerprint is fixed in the code in the 9c commit, when both first exist; until then the beside-file
  check stands.
- **The code change is approved**: committed and pushed as one code REF — restore_surface_fill.py, health_check.py,
  snapshot_surface_fill.py, tests/test_surface_fill_restore.py (43), and charter §6 9c amended. Charter old wording, cited here as
  ruled: '"before" side = `<src>` (pre-upgrade live)'; new: "before" side = the named copy of `<built>` taken after step 9 and before
  9a (`~/edition_upgrade_runs/step9a_apply_<date>/before.db`), with `--from-restore <9a's --report>` in place of the 10/25 CSV.
- **Note for STEP9-APPLY (gated on 32a39a10):** its REF guard (`eu_step pre`: scripts/tests = 32a39a10) STOPs on a PA that has pulled
  this new REF. PA stays at a9674438 until STEP9-APPLY has run; 9a's blocks then gate on the new REF after a pull.

**New code REF: `cd6566b3`** (11/14) — the §9.121 change; pre-commit all checks passed. scripts/ and tests/ differ from 32a39a10 only
by restore_surface_fill.py, health_check.py, snapshot_surface_fill.py and tests/test_surface_fill_restore.py.

### STEP9-APPLY ran (11/15, 02:55 UTC, PA HEAD a9674438, REF 32a39a10) — DONE, exit 0 → STEP 9 CLOSED at 391,141 (§9.122)

Log `~/edition_upgrade_runs/step9_apply_20261114.log`; run folder `step9_apply_20261114/`. Write gate cleared by the ruling chat on
the STEP9-DRY2 figures (§9.119). Pre-write: PRE OK; dry figures = declared; dry deltas 4,423 / 467fd9ba… and 28 / b0fd29d1…; list
7033acea…; bh_scrape.db 5e9d4bb6…; SAME OK (150 + schema, 0). Write: chain 346,113 / 13,181 / 31,847 = 391,141; romanized 391,141;
list adds 163 (160 + 3 along); refusals 631. Post-write: figures = declared; pn_list.tsv c505b167… and pn_refused.tsv 235efe2d… =
the dry run's; CHECK OK (149 untouched + schema 0; abp_surface 391,141, fingerprint 70af7a4a08e7 = dry copy; prep 395,003,
18d0bba9d262); before → after = the declared delta (4,422 + header, sha 467fd9ba…: changed 538 / added 11 / removed 3,873); gate 3 on
built 163 / 163 / 0 / 0; bh_scrape.db unchanged, no journal. Restore source not needed (`step9_dry2_20261114/before.db` kept).
**The 27 members of src-dry → built-dry** (the edition's effect on the chain), from the log (verse_id, position):
ADDED (88,2) Καϊν · ADDED (88,22) Καϊν · ADDED (131,1) Μαθουσαλά / REMOVED (131,2) · ADDED (132,1) Μαθουσαλά / REMOVED (132,2) ·
CHANGED (985,1) είπε δε → Συχέμ / (985,2) Συχέμ → είπε δε · ADDED (1167,14) Εβραίος · ADDED (5817,1) Ρουβήν · ADDED (5817,6) Συμεών ·
CHANGED (5874,19) οίδα → ουκ / (5874,20) ουκ → οίδα · ADDED (5950,27) Ιησούν · ADDED (6837,6) ουχ / REMOVED (6837,7) · ADDED (9467,4)
Ιεζάβελ · ADDED (10201,6) Ιωακίμ / REMOVED (10201,7) · ADDED (11143,1) Αχιτόφελ · ADDED (11144,2) Αχιτόφελ · ADDED (12788,12) Αμάν /
REMOVED (12788,13) · ADDED (20007,2) Ιωακείμ · ADDED (26424,2) Βηθανία · REMOVED (30987,17) ωμοιώθημεν / ADDED (30987,18).
(= changed 4 / added 17 / removed 6: the 11 names built now matches, the slot shifts Gen 5:25/26, Est 5:9, Jdg 11:7, 2Ki 23:35,
Rom 9:29, and the Gen 34:4 / Jos 2:4 swaps.)

**Ruling (11/15, §9.122): step 9 applied on built and CLOSED at 391,141.** PA may pull to cd6566b3 (done: PA at ca74e54d). Built's
abp_surface now is the "before side" for 9c (charter §6 amended); 9a's apply block saves it as `step9a_apply_<date>/before.db` (F3).
Next: STEP9A-DRY under cd6566b3.

## STEP9A-DRY drafted (11/15, GATE REF cd6566b3; PA at ca74e54d)

Read-only. **Guards:** pre (REF cd6566b3); the snapshot (+ .sha256) and the Analytical Lexicon present (shas printed; the restore
checks the snapshot against its pin d9435bde…); **built = exactly what STEP9-APPLY left** (`eu_step check` against STEP9-DRY2's prep
+ dry copy: 149 untouched + schema, abp_surface = the dry copy) and abp_surface 391,141; built + src size/time before = after.
**(1) The restore DRY RUN** on built, `--base 391141`, no lists, no `--prefill` (charter §4.9): its S / V / G1a lines and SUMMARY
printed; full output and per-slot report kept. Exit 1 = a gate fails (slots unplaced) — read, not a STOP; a run that does not reach
"RESULT: DRY RUN COMPLETE" is a STOP.
**(2) TRIAL dry run (still writes nothing):** every reason-6 slot from (1) on a key-2 list (book chapter verse old_position
new_position = its key-2 slot), so each runs the same preconditions + Lexicon check there (§9.120 F2a: the member list shows each
reason-6 slot's result). Its SUMMARY printed.
**(3) The member list:** every unplaced slot from (1), one line: reason · verse · old position · the verse's English changed or
not (src → built `verses.text`) · action · cls · **by key 2 alone** (trial: "places, lexicon pass/uncovered" or "FAILS rN") · form ·
src English at the old slot · key 2 → built English there · key 1 · detail. Counts by reason × changed × trial result; **every**
unplaced slot in a verse whose English did NOT change (charter §4.9: a reason-6 slot there is a real miss); the first 80 in changed
verses (all in `members.tsv` on PA). Expected figures: none forecast — the 10/25 restore placed 4,411 on an unchanged text; this is
the first run on the new English (charter §4.9 expects reason 6 to be large).
Local test (made-up dbs from the restore tests' own shapes; a throwaway clone at cd6566b3 + one fake commit setting the snapshot
counts to the fake file's and unpinning it): READ DONE; two reason-6 slots listed, one in a changed verse and one in an unchanged
verse ("real miss" list), each with old/new English; the trial placed both; with the Lexicon row removed the unchanged-verse slot
reads "FAILS r5"; built altered since STEP9-APPLY → STOP; re-paste → STOP.

### Block STEP9A-DRY (GATE REF cd6566b3; READ-ONLY — writes only its run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/step9a_dry_20261115.log
if [ -e "$L" ]; then echo "STEP9A-DRY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=cd6566b3
echo "GATE REF ${REF} - STEP9A-DRY rebuild-words step 9a DRY RUN: restore_surface_fill on built at --base 391141, no lists (sec 9.120/9.122) + the unplaced member list read against the changed-English verses (charter 4.9) - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9A-DRY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
SNAP=tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv
LEX=abp_helps/analytical_lexicon.tsv
DD=~/edition_upgrade_runs/step9_dry2_20261114
D=~/edition_upgrade_runs/step9a_dry_20261115
E="python3 scripts/eu_step.py"
TAB=$'\t'
$E pre --tag STEP9AD --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP9A-DRY RESULT: STOP - pre (line above); nothing read"; exit 1; }
for f in "$SNAP" "$SNAP.sha256" "$LEX"; do [ -s "$f" ] || { echo "STEP9A-DRY RESULT: STOP - missing or empty: $f"; exit 1; }; done
echo "snapshot $SNAP: $(wc -l < "$SNAP") lines, sha256 $(sha256sum < "$SNAP" | cut -d' ' -f1) (the restore checks it against its pin d9435bde...)"
echo "lexicon $LEX: $(wc -l < "$LEX") lines, sha256 $(sha256sum < "$LEX" | cut -d' ' -f1)"
echo "=== built = what STEP9-APPLY left (eu_step check against STEP9-DRY2's prep + dry copy; read-only) ==="
$E check --tag STEP9AD --built "$B" --dir "$DD" --written abp_surface || { echo "STEP9A-DRY RESULT: STOP - built is not STEP9-APPLY's result (lines above)"; exit 1; }
n0=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_surface"); echo "abp_surface on built: $n0 (expect 391141)"
[ "$n0" = 391141 ] || { echo "STEP9A-DRY RESULT: STOP - built's abp_surface is not 391,141"; exit 1; }
bs0=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' ')
# --- the restore dry run (writes only its --report) ---
echo "=== restore_surface_fill DRY RUN on built: --base 391141, no lists, no --prefill (charter 4.9) ==="
python3 scripts/restore_surface_fill.py "$B" --snapshot "$SNAP" --lexicon "$LEX" --report "$D/restore_dry.tsv" --base 391141 > "$D/restore_dry.out" 2>&1; r=$?
sed -n '1,/^RE-KEY/p' "$D/restore_dry.out"
sed -n '/^G1a/{p;n;p}' "$D/restore_dry.out"
sed -n '/^SUMMARY/,$p' "$D/restore_dry.out"
echo "restore exit $r (0 = every slot placed; 1 = a gate fails, i.e. slots unplaced - read below)"
sed -n '/^RESULT: DRY RUN COMPLETE/p' "$D/restore_dry.out" | sed -n '1p' > "$D/result.txt"
[ -s "$D/result.txt" ] || { echo "STEP9A-DRY RESULT: STOP - the restore did not finish its dry run (full output: $D/restore_dry.out)"; exit 1; }
echo "full restore output: $D/restore_dry.out ($(wc -l < "$D/restore_dry.out") lines: the agree-weak, unplaced and moved lists are in it)"
# --- TRIAL (still a dry run, writes nothing): every reason-6 slot on a key-2 list, so each one runs the same
# preconditions + Lexicon check at its key-2 slot (DESIGN 9.120 F2a: the member list shows each one's result) ---
awk -F'\t' -v OFS='\t' 'BEGIN {print "book", "chapter", "verse", "old_position", "new_position"} NR > 1 && $12 == "unplaced" && $13 == 6 {split($10, k, ":"); print $1, $2, $3, $4, k[2]}' "$D/restore_dry.tsv" > "$D/trial_key2.tsv"
n6=$(($(wc -l < "$D/trial_key2.tsv") - 1)); echo "=== TRIAL dry run: all $n6 reason-6 slots by key 2 alone (nothing written) ==="
if [ "$n6" -gt 0 ]; then
  python3 scripts/restore_surface_fill.py "$B" --snapshot "$SNAP" --lexicon "$LEX" --report "$D/restore_trial.tsv" --base 391141 --key2-alone "$D/trial_key2.tsv" > "$D/restore_trial.out" 2>&1; rt=$?
  sed -n '/^SUMMARY/,$p' "$D/restore_trial.out"
  echo "trial exit $rt; the reason-6 slots that would FAIL by key 2 alone are in the member list below (column 'by key 2 alone')"
else
  printf 'book\n' > "$D/restore_trial.tsv"
fi
# --- the member list: every unplaced slot, read against the changed-English verses ---
echo "=== UNPLACED slots, each with its verse's English changed or not (src -> built verses.text) and the English at the slot ==="
awk -F'\t' 'NR > 1 && $12 == "unplaced"' "$D/restore_dry.tsv" > "$D/unplaced.tsv"
nu=$(wc -l < "$D/unplaced.tsv"); echo "unplaced slots: $nu"
VQ="SELECT book, chapter, verse, replace(replace(replace(COALESCE(text, ''), char(9), ' '), char(10), ' '), char(13), ' ') FROM verses"
sqlite3 -readonly -separator "$TAB" "$S" "$VQ" > "$D/verses_src.tsv" || { echo "STEP9A-DRY RESULT: STOP - verses read failed on src"; exit 1; }
sqlite3 -readonly -separator "$TAB" "$B" "$VQ" > "$D/verses_built.tsv" || { echo "STEP9A-DRY RESULT: STOP - verses read failed on built"; exit 1; }
awk -F'\t' 'FNR == 1 {f++} f == 1 {t[$1 FS $2 FS $3] = $4; next} {k = $1 FS $2 FS $3; print k FS (((k in t) && t[k] == $4) ? "same" : "CHANGED")}' "$D/verses_src.tsv" "$D/verses_built.tsv" > "$D/verse_changed.tsv"
echo "verses whose English changed src -> built: $(awk -F'\t' '$4 == "CHANGED"' "$D/verse_changed.tsv" | wc -l) of $(wc -l < "$D/verse_changed.tsv")"
if [ "$nu" -gt 0 ]; then
  # every word row from each copy (no long WHERE list); the awk join below picks the slots it needs
  WQ="SELECT v.book, v.chapter, v.verse, w.position, replace(replace(COALESCE(w.english, ''), char(9), ' '), char(10), ' ') FROM words w JOIN verses v ON v.id = w.verse_id"
  sqlite3 -readonly -separator "$TAB" "$S" "$WQ" > "$D/words_src.tsv" || { echo "STEP9A-DRY RESULT: STOP - words read failed on src"; exit 1; }
  sqlite3 -readonly -separator "$TAB" "$B" "$WQ" > "$D/words_built.tsv" || { echo "STEP9A-DRY RESULT: STOP - words read failed on built"; exit 1; }
  # one line per unplaced slot: reason | verse | old pos | verse English changed | action | cls | by key 2 alone (trial) | form | src English at the old slot | key 2 -> built English there | key 1 | detail
  awk -F'\t' -v OFS='\t' '
    FNR == 1 {f++}
    f == 1 {vc[$1 FS $2 FS $3] = $4; next}
    f == 2 {es[$1 FS $2 FS $3 FS $4] = $5; next}
    f == 3 {eb[$1 FS $2 FS $3 FS $4] = $5; next}
    f == 4 {if (FNR > 1) tr[$1 FS $2 FS $3 FS $4] = (($12 == "placed") ? "places, lexicon " $15 : "FAILS r" $13); next}
    f == 5 {v = $1 FS $2 FS $3; split($10, k2, ":"); nb = (k2[1] == "one") ? eb[v FS k2[2]] : "-"
            t = ($13 == 6 && (v FS $4 in tr)) ? tr[v FS $4] : "-"
            print "r" $13, $1 " " $2 ":" $3, $4, ((v in vc) ? vc[v] : "?"), $6, $7, t, $9, "\"" es[v FS $4] "\"", $10 " \"" nb "\"", $11, $14}' \
    "$D/verse_changed.tsv" "$D/words_src.tsv" "$D/words_built.tsv" "$D/restore_trial.tsv" "$D/unplaced.tsv" > "$D/members.tsv"
  echo "--- by reason x verse English (changed / same) x by key 2 alone:"
  cut -f1,4,7 "$D/members.tsv" | sort | uniq -c
  echo "--- every unplaced slot in a verse whose English did NOT change (charter 4.9: a reason-6 slot here is a real miss) - reason | verse | old pos | verse | action | cls | by key 2 alone | form | src English | key 2 -> built English | key 1 | detail:"
  awk -F'\t' '$4 != "CHANGED"' "$D/members.tsv" | sed 's/\t/ | /g; s/^/  /'
  ni=$(awk -F'\t' '$4 == "CHANGED"' "$D/members.tsv" | wc -l)
  echo "--- unplaced slots in a verse whose English changed: $ni; by reason above; the first 80 (all $ni in $D/members.tsv):"
  awk -F'\t' '$4 == "CHANGED"' "$D/members.tsv" | sed -n '1,80p' | sed 's/\t/ | /g; s/^/  /'
fi
bs1=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' '); echo "built + src size and time before = after: $([ "$bs1" = "$bs0" ] && echo yes || echo NO)"
[ "$bs1" = "$bs0" ] || { echo "STEP9A-DRY RESULT: STOP - built or src changed during a read-only run - report this"; exit 1; }
echo "STEP9A-DRY RESULT: READ DONE - restore dry run at base 391,141: $(cat "$D/result.txt"); unplaced $nu (member list above; report $D/restore_dry.tsv)"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9A-DRY reviewed (11/15) — REVIEW: ESCALATE (two member-list defects) → fixed → re-review
Verdict line verbatim: "REVIEW: ESCALATE - the block is read-only and its wrapper and tripwires pass, but two defects in the member list (the part the ruling reads) need a redraft before it runs"
- **Defect 1 — FIXED:** the "by key 2 alone" column took the trial report's result for EVERY slot, so non-reason-6 slots (e.g.
  reason 7) showed "FAILS rN" as if tried by key 2. Now only reason-6 slots carry a trial result; every other slot shows "-".
  Re-tested with a planted reason-7 slot: "r7 | Gen 1:1 | … | - | …".
- **Defect 2 — FIXED:** the words read built one long OR list of verses (could exceed SQLite's expression depth or the Linux
  argument limit on a large unplaced set). Now each copy's whole words table is read once (no WHERE) and the awk join picks
  the slots.
- **Minor — FIXED:** tabs / newlines inside `verses.text` or `words.english` are replaced by spaces in the reads.
The block above now holds the fixed text.

### STEP9A-DRY re-reviewed (11/15) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - this re-run is read-only; the three fixes are in exactly as named, nothing else moved, and every wrapper item and tripwire passes"

### STEP9A-DRY ran (11/15, 06:44 UTC, PA HEAD ca74e54d, REF cd6566b3) — READ DONE, exit 0

Log `~/edition_upgrade_runs/step9a_dry_20261115.log`; run folder `step9a_dry_20261115/` (`restore_dry.tsv/.out`,
`restore_trial.tsv/.out`, `trial_key2.tsv`, `members.tsv`). PRE OK; snapshot 4,412 lines, sha d9435bde… (= pin); lexicon 39,540
lines, sha 91d9d036…; CHECK OK (built = STEP9-APPLY's result: 149 untouched + schema 0, abp_surface 391,141 / 70af7a4a08e7);
built + src untouched.
**Dry run (`--base 391141`, no lists):** S / V PASS; G1a 391,141 = base; placed 4,328 (agree-strong 3,977 · agree-weak 351);
unplaced 83 (r6 79 · r7 4); inserts / updates 3,809 / 519; moved 5; Lexicon pass 3,944 / uncovered 384; after-count 394,950;
"a gate FAILS" (expected).
**Trial (all 79 r6 on a key-2 list):** placed 4,407 (… · key-2 listed 79); unplaced 4 (r7); listed-not-as-listed 0; inserts /
updates 3,869 / 538; moved 6; Lexicon pass 4,018 / uncovered 389; after-count 395,010.
**Member list:** verses with changed English 15,522 of 31,237. r6 CHANGED places / pass 74 · r6 CHANGED places / uncovered 5
(Lev 20:15 @4, Deu 28:62 @5, Jos 5:5 @30, 1Ki 8:44 @25 [key 1 several 14, 32], Job 32:21 @8) · r7 CHANGED 3 (Jos 12:23 @2 key 1
→ 7, 1Ki 14:20 @4 → 17, Jer 26:21 @19 → 1) · r7 same 1 (Psa 71:0 @0 → 3). 80 of the 82 changed-verse rows printed.

**Ruling (11/15, §9.123):** (1) the 74 r6 / changed / key-2 places / Lexicon pass go on the key-2 list. (2) Held for a read: the
5 r6 uncovered + the 4 r7 — src words ±3 around the old slot, built words ±3 around key 2's slot (and key 1's for r7; all three
candidates for 1Ki 8:44), the Greek form the snapshot would write; Psa 71:0 (the one §4.9 real-miss candidate) printed whole on
both sides. Noted, no ruling: moved 5 / 6; trial after-count 395,010 vs 10/25 395,003. Next: the 9-slot context read, with reviewer
verdict; then the key-2 and leave lists are fixed and STEP9A-APPLY drafted.

**CC notes on the log (checked against the code):**
- "Lexicon uncovered" on the 5 is not a failed check: their classes (normalize ×4, fill_unlisted ×1) are not in
  `LEXICON_CLASSES` (`scripts/apply_abp_surface_fill.py:53-55`), so the restore never Lexicon-checks them
  (`restore_surface_fill.py` evaluate: `want = LEXICON_CLASSES.get(cls)`; no `want` → stays "uncovered").
- Ruling 1 covers 74 rows, but the log printed 72 of them: changed-verse rows 81-82 (both r6 / pass — all 3 r7 and all 5
  uncovered are among the 80 printed) were not shown. The context read prints those two as well.
- 5 of the 74 have blank English on one side at the slot: src blank at 1Ki 17:17 @22, Job 32:21 @9, Psa 92:0 @5; built blank
  at 1Ki 22:48 @14, 1Ki 22:49 @18. Ruling 1's stated basis ("a punctuation / case / wording variant of the src English") does
  not describe these. Key 2 is the Greek number + its count in the verse, and the Lexicon passes, so the Greek word is the same;
  the English moved to a neighbour. The context read shows these 5 too, so the ruling can confirm them.

## STEP9A-CTX drafted (11/15, GATE REF cd6566b3; PA at ca74e54d) — the §9.123 ruling-2 context read

Read-only. **Guards:** pre (REF cd6566b3); the snapshot (+ .sha256), the Lexicon, and STEP9A-DRY's `restore_dry.tsv` (4,412
lines) + `members.tsv` (83 lines) present, their shas printed; built = STEP9-APPLY's result (`eu_step check` against STEP9-DRY2,
as STEP9A-DRY) and abp_surface 391,141; built + src size/time before = after.
**Slots (16):** group **H** = the 9 held by ruling 2 — Lev 20:15 @4, Deu 28:62 @5, Jos 5:5 @30, 1Ki 8:44 @25, Job 32:21 @8,
Jos 12:23 @2, 1Ki 14:20 @4, Jer 26:21 @19, Psa 71:0 @0 (whole verse, both sides). Group **X** = behind ruling 1's basis (CC notes
above): the 2 changed-verse member rows STEP9A-DRY did not print (rows 81-82; printed in full first, with a check that both are
r6 / places, Lexicon pass) + the 5 with blank English on one side (1Ki 17:17 @22, 1Ki 22:48 @14, 1Ki 22:49 @18, Job 32:21 @9,
Psa 92:0 @5).
**Per slot** (a helper written into the run folder; opens src + built read-only; uses the restore's own key rules
`dryrun_rekey_fill.key2_at / key1_at / decide`, the one class list `LEXICON_CLASSES` and the one `agree()` rule): the snapshot
row (action, class, form, old form, strongs + its key-2 count, the key-1 English); whether the restore Lexicon-checks the class;
the dry report's result + keys; the keys recomputed on built (= the report, else the helper exits 1 → STOP); both verse texts;
src words ±3 around the old slot and built words ±3 around every candidate (key 2's; key 1's; all of 1Ki 8:44's), each with
strongs, lemma, is_pn, English and the form on that copy's abp_surface; at each built candidate the restore's precondition
(update: built form = old form; insert: slot empty) and `agree()` (marked "information only" on a class the restore does not
check). No figures forecast.
Local test (the STEP9A-DRY fake copies; a reason-7 slot with key 1 elsewhere, a reason-6 whole-verse slot, a reason-6
"uncovered" slot, a placed update): READ DONE, each slot's keys = the report; a slot not in the snapshot → NOT FOUND, exit 1; a
report key altered → "= the dry report: NO", exit 1; the helper failing inside the block → STOP; built altered → CHECK FAIL →
STOP; re-paste → STOP.

### Block STEP9A-CTX (GATE REF cd6566b3; READ-ONLY — writes only its run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/step9a_ctx_20261115.log
if [ -e "$L" ]; then echo "STEP9A-CTX RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=cd6566b3
echo "GATE REF ${REF} - STEP9A-CTX the 9 held slots of sec 9.123 ruling 2 (+ 7 slots behind ruling 1's basis) read in context on src and built - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9A-CTX RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
SNAP=tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv
LEX=abp_helps/analytical_lexicon.tsv
DD=~/edition_upgrade_runs/step9_dry2_20261114
DA=~/edition_upgrade_runs/step9a_dry_20261115
D=~/edition_upgrade_runs/step9a_ctx_20261115
E="python3 scripts/eu_step.py"
TAB=$'\t'
$E pre --tag STEP9AC --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP9A-CTX RESULT: STOP - pre (line above); nothing read"; exit 1; }
for f in "$SNAP" "$SNAP.sha256" "$LEX" "$DA/restore_dry.tsv" "$DA/members.tsv"; do [ -s "$f" ] || { echo "STEP9A-CTX RESULT: STOP - missing or empty: $f"; exit 1; }; done
echo "STEP9A-DRY report $DA/restore_dry.tsv: $(wc -l < "$DA/restore_dry.tsv") lines (expect 4412), sha256 $(sha256sum < "$DA/restore_dry.tsv" | cut -d' ' -f1)"
echo "STEP9A-DRY member list $DA/members.tsv: $(wc -l < "$DA/members.tsv") lines (expect 83), sha256 $(sha256sum < "$DA/members.tsv" | cut -d' ' -f1)"
[ "$(wc -l < "$DA/restore_dry.tsv")" = 4412 ] && [ "$(wc -l < "$DA/members.tsv")" = 83 ] || { echo "STEP9A-CTX RESULT: STOP - the STEP9A-DRY files are not what its log showed"; exit 1; }
echo "=== built = what STEP9-APPLY left (eu_step check against STEP9-DRY2's prep + dry copy; read-only) ==="
$E check --tag STEP9AC --built "$B" --dir "$DD" --written abp_surface || { echo "STEP9A-CTX RESULT: STOP - built is not STEP9-APPLY's result (lines above)"; exit 1; }
n0=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_surface"); echo "abp_surface on built: $n0 (expect 391141)"
[ "$n0" = 391141 ] || { echo "STEP9A-CTX RESULT: STOP - built's abp_surface is not 391,141"; exit 1; }
bs0=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' ')
# --- the 2 changed-verse member rows STEP9A-DRY did not print (rows 81-82; ruling 1 counted them) ---
awk -F'\t' '$4 == "CHANGED"' "$DA/members.tsv" | sed -n '81,$p' > "$D/unprinted.tsv"
echo "changed-verse member rows not printed by STEP9A-DRY: $(wc -l < "$D/unprinted.tsv") (expect 2); both r6 / places, lexicon pass: $([ "$(awk -F'\t' '$1 == "r6" && $7 == "places, lexicon pass"' "$D/unprinted.tsv" | wc -l)" = 2 ] && echo yes || echo NO)"
[ "$(wc -l < "$D/unprinted.tsv")" = 2 ] || { echo "STEP9A-CTX RESULT: STOP - not 2 unprinted changed-verse rows"; exit 1; }
sed 's/\t/ | /g; s/^/  /' "$D/unprinted.tsv"
# --- the slots: group H = held by ruling 2 (whole verse for Psa 71:0); X = behind ruling 1's basis
# (the 2 unprinted rows + the 5 with blank English on one side) - group book chapter verse old_position whole ---
{ printf 'H\tLev\t20\t15\t4\t0\nH\tDeu\t28\t62\t5\t0\nH\tJos\t5\t5\t30\t0\nH\t1Ki\t8\t44\t25\t0\nH\tJob\t32\t21\t8\t0\n'
  printf 'H\tJos\t12\t23\t2\t0\nH\t1Ki\t14\t20\t4\t0\nH\tJer\t26\t21\t19\t0\nH\tPsa\t71\t0\t0\t1\n'
  awk -F'\t' -v OFS='\t' '{split($2, a, " "); split(a[2], b, ":"); print "X", a[1], b[1], b[2], $3, 0}' "$D/unprinted.tsv"
  printf 'X\t1Ki\t17\t17\t22\t0\nX\t1Ki\t22\t48\t14\t0\nX\t1Ki\t22\t49\t18\t0\nX\tJob\t32\t21\t9\t0\nX\tPsa\t92\t0\t5\t0\n'; } > "$D/slots.tsv"
echo "slots to read: $(wc -l < "$D/slots.tsv") (expect 16)"
P="$D/ctx9_helper.py"
cat > "$P" <<'PY'
"""STEP9A-CTX helper (one-off, edition upgrade step 9a; ruling chat 11/15, sec 9.123 ruling 2). Read-only:
src + built opened mode=ro; the snapshot read with its .sha256 check; the STEP9A-DRY report read.
Per slot: the snapshot row; the dry report's result + keys; the keys recomputed on built with the
restore's own rules (dryrun_rekey_fill.key2_at / key1_at / decide); src words around the old slot and
built words around every candidate slot (key 2's, key 1's), each with its lemma and the form on that
copy's abp_surface; at each built candidate the restore's precondition and the Lexicon agree() result.
argv: <src.db> <built.db> <snapshot.tsv> <lexicon.tsv> <restore_dry.tsv> <slots.tsv>
slots.tsv (no header): group book chapter verse old_position whole(0/1)"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import dryrun_rekey_fill as dr                          # noqa: E402  the key rules
import snapshot_surface_fill as snap                    # noqa: E402  the file format
from apply_abp_surface_fill import LEXICON_CLASSES      # noqa: E402  the one class list
from census_abp_surface_glued import Lexicon, agree     # noqa: E402  the one number + form rule

src_p, built_p, snap_p, lex_p, rep_p, slots_p = sys.argv[1:7]


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=60)


def kf(k):                                     # = the restore report's key text
    return "%s:%s" % (k[0], k[1])


def load(con, keys):
    vid = {}
    for i, b, c, v, t in con.execute("SELECT id, book, chapter, verse, COALESCE(text, '') FROM verses"):
        if (b, c, v) in keys:
            vid[(b, c, v)] = (i, t)
    ids = {x[0] for x in vid.values()}
    lem = {}
    for s, l in con.execute("SELECT strongs_g, COALESCE(lemma, '') FROM lexicon"):
        lem[s] = l if s not in lem else lem[s] + " / " + l
    words = {}
    for v, p, s, sb, e, pn in con.execute(
            "SELECT verse_id, position, strongs, strongs_base, english, is_pn FROM words"):
        if v in ids:
            words.setdefault(v, []).append((p, s, e, pn, lem.get(sb, "")))
    for v in words:
        words[v].sort(key=lambda r: r[0])
    surf = {}
    for v, p, f in con.execute("SELECT verse_id, position, form FROM abp_surface"):
        if v in ids:
            surf[(v, p)] = f
    return vid, words, surf


def show(label, words, surf, vid, marks, whole):
    keep = sorted({w[0] for w in words if whole or any(abs(w[0] - m) <= 3 for m in marks)})
    print("  %s:" % label)
    last = None
    for p, s, e, pn, lem in words:
        if p not in keep:
            continue
        if last is not None and p > last + 1:
            print("         ...")
        last = p
        f = surf.get((vid, p))
        print("    %-9s %3d | %s | %s | is_pn %s | %s | form %s"
              % ("/".join(marks.get(p, [])), p, s, lem or "-", pn,
                 '"%s"' % e if e is not None else "(no English)", f if f is not None else "(none)"))


rows, hexd = snap.read_snapshot(snap_p)
print("snapshot sha256 %s (= its .sha256 file), %d rows" % (hexd, len(rows)))
by = {(r["book"], r["chapter"], r["verse"], r["position"]): r for r in rows}
rep = {}
with open(rep_p, encoding="utf-8", newline="") as f:
    head = f.readline().rstrip("\n").split("\t")
    for line in f:
        d = dict(zip(head, line.rstrip("\n").split("\t")))
        rep[(d["book"], int(d["chapter"]), int(d["verse"]), int(d["old_position"]))] = d
slots = []
with open(slots_p, encoding="utf-8") as f:
    for line in f:
        g, b, c, v, p, whole = line.rstrip("\n").split("\t")
        slots.append((g, b, int(c), int(v), int(p), whole == "1"))
lex = Lexicon(lex_p)
keys = {(b, c, v) for g, b, c, v, p, w in slots}
cs, cb = ro(src_p), ro(built_p)
try:
    sv, sw, ss = load(cs, keys)
    bv, bw, bs = load(cb, keys)
finally:
    cs.close()
    cb.close()

bad = 0
for g, b, c, v, p, whole in slots:
    k = (b, c, v, p)
    r, d = by.get(k), rep.get(k)
    print("\n=== [%s] %s %d:%d old position %d" % (g, b, c, v, p))
    if r is None or d is None or (b, c, v) not in sv or (b, c, v) not in bv:
        print("  NOT FOUND in the snapshot / the dry report / a copy's verses")
        bad += 1
        continue
    print("  snapshot row: %s | class %s | form %s | old form %s | strongs %s (key 2: its number %d of %d with that"
          " strongs in the verse, counting from 0) | key-1 English \"%s\" | is_pn %s"
          % (r["action"], r["cls"], r["form"], r["old_form"], r["strongs"], r["k2_ordinal"], r["k2_count"],
             r["english"], r["is_pn"]))
    want = LEXICON_CLASSES.get(r["cls"])
    print("  the restore Lexicon-checks this class: %s"
          % ("yes, wants agree() in " + "/".join(want) if want else "no - never checked, so 'uncovered'"))
    print("  dry report: %s | reason %s | key 2 %s | key 1 %s | %s"
          % (d["result"], d["reason"] or "-", d["key2"], d["key1"], d["detail"]))
    svid, stext = sv[(b, c, v)]
    bvid, btext = bv[(b, c, v)]
    new_rows = [(q, s, e, pn) for q, s, e, pn, lem in bw.get(bvid, [])]
    k2 = dr.key2_at(r["strongs"], r["k2_ordinal"], new_rows)
    k1 = dr.key1_at(r["strongs"], r["english"], new_rows)
    reason, _ = dr.decide(k2, k1)
    same = kf(k2) == d["key2"] and kf(k1) == d["key1"] and (str(reason) if reason else "") == d["reason"]
    print("  recomputed on built: key 2 %s | key 1 %s | reason %s (= the dry report: %s)"
          % (kf(k2), kf(k1), reason or "-", "yes" if same else "NO"))
    bad += 0 if same else 1
    print("  verse_id src %d / built %d; verse English src -> built: %s" % (svid, bvid, "same" if stext == btext else "CHANGED"))
    print("  src   verse: \"%s\"" % stext)
    print("  built verse: \"%s\"" % btext)
    marks = {}
    if k2[0] == "one":
        marks.setdefault(k2[1], []).append("key2")
    for q in ([k1[1]] if k1[0] == "one" else list(k1[1]) if k1[0] == "amb" else []):
        marks.setdefault(q, []).append("key1")
    show("src words around the old slot (mark | pos | strongs | lemma | is_pn | English | form on src's abp_surface)",
         sw.get(svid, []), ss, svid, {p: ["old"]}, whole)
    show("built words around each candidate (form = built's abp_surface now, before the fill)",
         bw.get(bvid, []), bs, bvid, marks, whole)
    for q in sorted(marks):
        cur = bs.get((bvid, q))
        if r["action"] == "update":
            pre = "update: built's form = the old form: %s (built holds %s)" % ("yes" if cur == r["old_form"] else "NO", cur)
        else:
            pre = "insert: slot empty on built: %s" % ("yes" if cur is None else "NO (holds %s)" % cur)
        s = next(x[1] for x in new_rows if x[0] == q)
        print("  at %s position %d: %s | Lexicon agree(%s, form) = %s%s"
              % ("+".join(marks[q]), q, pre, s, agree(lex, s, r["form"]), "" if want else " (information only)"))
print("\ncontext read: %d slots; every slot found and its keys recomputed = the dry report: %s"
      % (len(slots), "yes" if bad == 0 else "NO (%d)" % bad))
sys.exit(1 if bad else 0)
PY
echo "helper $P: sha256 $(sha256sum < "$P" | cut -d' ' -f1)"
python3 "$P" "$S" "$B" "$SNAP" "$LEX" "$DA/restore_dry.tsv" "$D/slots.tsv"; h=$?
bs1=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' '); echo "built + src size and time before = after: $([ "$bs1" = "$bs0" ] && echo yes || echo NO)"
[ "$bs1" = "$bs0" ] || { echo "STEP9A-CTX RESULT: STOP - built or src changed during a read-only run - report this"; exit 1; }
[ "$h" = 0 ] || { echo "STEP9A-CTX RESULT: STOP - helper exit $h (a slot not found, or its keys differ from the dry report - lines above)"; exit 1; }
echo "STEP9A-CTX RESULT: READ DONE - 16 slots read in context (9 held + 7 behind ruling 1's basis)"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9A-CTX reviewed (11/15) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - read-only context read for the §9.123 ruling-2 slots. It uses the restore's own key, class and agree rules, its wrapper is complete, and it STOPs on any missing slot or key mismatch."
Reviewer observation (no STOP): the "both r6 / places, lexicon pass" check on the 2 unprinted rows prints yes/NO without
stopping — the ruling chat reads that line in the log.

### STEP9A-CTX ran (11/15, 13:11 UTC, PA HEAD ca74e54d, REF cd6566b3) — READ DONE, exit 0

Log `~/edition_upgrade_runs/step9a_ctx_20261115.log`; folder `step9a_ctx_20261115/` (helper sha d3ee7c67… = the local test's).
PRE OK; restore_dry.tsv 4,412 lines (fb5daacf…), members.tsv 83 (1f032d1d…); CHECK OK (391,141, 70af7a4a08e7); unprinted rows 2,
both r6 / places, lexicon pass = **yes** (Heb 12:9 @14 "shall we" → "Shall we"; Luk 9:15 @4 "they laid them" → "laid them");
16 slots, every one's keys recomputed = the dry report; built + src untouched. ("key-1 English "None"" = the snapshot holds no
English for that slot; the helper printed the empty value as None.)

**CC reading, slot by slot (each from the log lines above):**
- **5 r6 "uncovered" — key 2 is right on all 5.** Lev 20:15 @4, Deu 28:62 @5, 1Ki 8:44 @25, Job 32:21 @8 are normalize updates:
  built's key-2 slot already holds exactly the old form (the builder put the same Greek there), so the precondition holds; the
  English there is reworded (his laying with → his laying; for → because; which → of which; … → in no way). 1Ki 8:44's key-1
  slots @14 / @32 hold η / ον — other words. Jos 5:5 @30: the only 390 (ἀναστρέφω) in the verse, slot empty, English paced →
  turned.
- **4 r7 — key 2 is right on all 4; key 1 points at the other copy of the same Greek number:** 1Ki 14:20 key 1 @17 already holds
  εβασίλευσεν (Nadab reigned); Jer 26:21 key 1 @1 already holds ήκουσεν (the rulers heard); Jos 12:23 key 1 @7 already holds της
  (of Gilgal); Psa 71:0 key 1 @3 is των's slot (its own snapshot row, ordinal 1, places there). Key 2's slots are empty.
- **Psa 71:0 is not a real miss:** the verse text is the same, but the word English moved (src: pos 0 blank, pos 1 "A psalm to
  David"; built: pos 0 "A psalm to", pos 1 "David"). Both have no-English article slots, which is why key 1 drifted.
- **The 7 X slots confirm ruling 1:** each is the same Greek number at the same position, slot empty, Lexicon full; the English
  is reworded, recased, or moved to a neighbour (blank on one side).
- **Blocker — the code does not allow a reason-7 slot on the key-2 list.** `restore_surface_fill.py:207-214`: a key-2-listed slot
  that is not reason 6 gets "on the key-2 list but reason 7" → G2 STOP. So today the 4 r7 can only go on the leave list, which
  drops 4 Greek forms live has. **Jos 12:23 is worse:** pos 3's own row (split_keep update `του Ναφαθδώρ` → `Ναφαθδώρ`, snapshot
  line checked in the repo) still places, so leaving pos 2 would strip του from pos 3 and land it nowhere — half of a split.
  Two ways out, for the ruling chat: (A) a small code change letting a reason-7 slot go on the key-2 list on the same terms as
  reason 6 (exactly its listed key-2 slot; same preconditions + Lexicon check), with tests; or (B) leave the 4 and accept the loss,
  incl. Jos 12:23's dropped article. CC recommends A.

**Ruling (11/15, §9.124):** basis of ruling 1 amended ("the English at the slot is reworded, recased, or moved to a neighbouring
word"); the 5 r6 uncovered and the 4 r7 go on the key-2 list; **option A** (reason 7 allowed on the key-2 list on reason 6's terms,
3 tests named); leave list empty, key-2 list = all 83; then STEP9A-DRY re-run with the list (read-outs placed 4,411 / unplaced 0 /
after-count = 391,141 + inserts; gates = the restore's own) → figures declared for STEP9A-APPLY (F3 before.db).

## Reason-7 key-2 code change (11/15, CC; to §9.124 ruling 3) — in the working tree, NOT committed until ruled

`scripts/restore_surface_fill.py` evaluate (:208-213): a key-2-listed slot may now be reason 6 **or 7**; it places only when key 2
finds one slot = exactly the listed new position (for reason 7 that is never key 1's slot), then runs the same preconditions
(3 / 4) and Lexicon check (5) as before; a listed reason-6/7 slot whose key 2 finds another position still STOPs ("on the key-2
list at new position N, key 2 now finds M"); any other reason still STOPs. Docstring (G2, evaluate), the list-section comment and
`--key2-alone` help updated. Nothing else changes (decide(), the leave list, after-count, apply, the 9c re-freeze — which takes
every placed slot whatever its reason).
`tests/test_surface_fill_restore.py` (+4, now 47; fixture: (1,2) 'word' → 'speech' and a second 3056 'word' at (1,5), so key 2 → 2,
key 1 → 5 = reason 7): **r7 listed places** (key 1's slot filled by its own row, left unchanged; table 6); **r7 listed with key 1's
slot empty goes only to its listed slot** (nothing written at (1,5); table 5); **r7 listed at key 1's slot STOPs**, nothing
written; **r7 on no list still STOPs** (G2), nothing written. With the code change reverted, the first three FAIL and the
fourth passes (it guards behaviour that must not change).

### Reason-7 code change reviewed (11/15) — REVIEW: CLEAR (code change → ruling chat, §9.90)
Verdict line verbatim: "REVIEW: CLEAR - the reason-7 key-2 change matches DESIGN 9.124 ruling 3. Reason 7 now goes through the same check, preconditions and Lexicon check as reason 6, and nothing else changed. The 4 tests exercise what their names say. Per 9.90 this verdict goes to the ruling chat, and it is a block clearance, not a receipt of results."
Reviewer note (not a defect): the restore has no check that two snapshot slots land on one new position. CC check
(`dryrun_rekey_fill.py:170-179`): every placement — normal or listed — is key 2's slot, the k-th position carrying the slot's
Greek number; two slots with the same number in a verse have different k, and a position held twice returns "ambiguous" (reason
2, never placed). So two placed slots cannot share a position; reason 7 adds nothing here.

**Ruling (11/15, §9.125):** the reason-7 change is approved; commit + push as the new code REF. PA pulls; then the STEP9A-DRY
re-run with the key-2 list of all 83 (leave list empty), reviewer, PA.

**New code REF `88f7a5f6`** (11/15, pushed; pre-commit all passed): the reason-7 key-2 change + 4 tests + the docs above.

## STEP9A-DRY2 drafted (11/15, GATE REF 88f7a5f6; PA must pull first) — the §9.124/§9.125 re-run with the key-2 list

Read-only. **Guards:** pre (REF 88f7a5f6); snapshot (+ .sha256), Lexicon, and STEP9A-DRY's report present; **that report's sha =
fb5daacf…** (the one STEP9A-CTX printed and the rulings read); built = STEP9-APPLY's result (`eu_step check`) and abp_surface
391,141; built + src size/time before = after.
**The key-2 list (§9.124 ruling 4)** is derived on PA from that report: every unplaced row, at its key-2 slot (`key2` = "one:N");
STOP unless 83 = r6 79 + r7 4 with every key 2 one slot. Saved as `step9a_dry2_20261115/key2_list.tsv` (STEP9A-APPLY reuses it by
sha), printed in full with its sha. Leave list: none.
**The restore DRY RUN** `--base 391141 --key2-alone <list>`, no `--prefill`: its S / L / V / G1a lines, any UNPLACED / LISTED-not-
as-listed / MOVED lists, SUMMARY and RESULT printed; output + report kept (report sha printed). Then: each listed slot found in the
report and placed at exactly its listed position "key-2 alone (listed)" (count, any other printed); the 9 CTX slots as the report
has them.
**Read-outs vs the traced expectation — printed yes/NO, NOT gates (§9.124 ruling 5):** placed 4,411 = agree-strong 3,977 +
agree-weak 351 + key-2 listed 83; unplaced 0; listed-not-as-listed 0; inserts / updates 3,873 / 538 (the S gate's split, all
placed); moved 6 (the trial's 6 — the 4 r7 place at their old positions, CTX log); Lexicon pass 4,022 / uncovered 389 (the trial's
4,018 / 389 + the 4 r7, each Lexicon-checked and agree() full at key 2, CTX log); after-count 391,141 + 3,873 = 395,014; every gate
passes. The gates are the restore's own.
Local test (fake copies; fake clone at 88f7a5f6 + one fake commit setting the snapshot counts / unpinning it): READ DONE, exit 0,
3-slot list (r6 2 + r7 1) all placed "key-2 alone (listed)", restore "every gate PASSES"; the figure lines read NO on fake figures
and yes where they match; a listed slot made to fail its Lexicon check → the restore's LISTED list + "NOT AS LISTED" line, restore
exit 1, block still READ DONE (read-out, not a STOP); report sha not the ruled one → STOP; re-paste → STOP.

### Block STEP9A-DRY2 (GATE REF 88f7a5f6; READ-ONLY — writes only its run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/step9a_dry2_20261115.log
if [ -e "$L" ]; then echo "STEP9A-DRY2 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=88f7a5f6
echo "GATE REF ${REF} - STEP9A-DRY2 rebuild-words step 9a DRY RUN re-run: restore_surface_fill on built at --base 391141 with the key-2 list of all 83 unplaced slots (r6 79 + r7 4), leave list empty (sec 9.124 / 9.125) - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9A-DRY2 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
SNAP=tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv
LEX=abp_helps/analytical_lexicon.tsv
DD=~/edition_upgrade_runs/step9_dry2_20261114
DA=~/edition_upgrade_runs/step9a_dry_20261115
D=~/edition_upgrade_runs/step9a_dry2_20261115
E="python3 scripts/eu_step.py"
$E pre --tag STEP9AD2 --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP9A-DRY2 RESULT: STOP - pre (line above); nothing read"; exit 1; }
for f in "$SNAP" "$SNAP.sha256" "$LEX" "$DA/restore_dry.tsv"; do [ -s "$f" ] || { echo "STEP9A-DRY2 RESULT: STOP - missing or empty: $f"; exit 1; }; done
echo "snapshot $SNAP: $(wc -l < "$SNAP") lines, sha256 $(sha256sum < "$SNAP" | cut -d' ' -f1) (the restore checks it against its pin d9435bde...)"
echo "lexicon $LEX: $(wc -l < "$LEX") lines, sha256 $(sha256sum < "$LEX" | cut -d' ' -f1) (STEP9A-DRY: 91d9d036...)"
RS=$(sha256sum < "$DA/restore_dry.tsv" | cut -d' ' -f1); echo "STEP9A-DRY report $DA/restore_dry.tsv: sha256 $RS (expect fb5daacf..., the report the rulings read)"
[ "$RS" = fb5daacff90133a4242aa3006163c1a4d9a8cff11d0c287d0ecb6668dedc4cf6 ] || { echo "STEP9A-DRY2 RESULT: STOP - the STEP9A-DRY report is not the one the rulings read"; exit 1; }
echo "=== built = what STEP9-APPLY left (eu_step check against STEP9-DRY2's prep + dry copy; read-only) ==="
$E check --tag STEP9AD2 --built "$B" --dir "$DD" --written abp_surface || { echo "STEP9A-DRY2 RESULT: STOP - built is not STEP9-APPLY's result (lines above)"; exit 1; }
n0=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_surface"); echo "abp_surface on built: $n0 (expect 391141)"
[ "$n0" = 391141 ] || { echo "STEP9A-DRY2 RESULT: STOP - built's abp_surface is not 391,141"; exit 1; }
bs0=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' ')
# --- the key-2 list (sec 9.124 ruling 4): every unplaced slot of the STEP9A-DRY report, at its key-2 slot ---
K="$D/key2_list.tsv"
awk -F'\t' -v OFS='\t' 'BEGIN {print "book", "chapter", "verse", "old_position", "new_position"} NR > 1 && $12 == "unplaced" {split($10, k, ":"); print $1, $2, $3, $4, ((k[1] == "one") ? k[2] : "NOT-ONE")}' "$DA/restore_dry.tsv" > "$K"
nk=$(($(wc -l < "$K") - 1)); n6=$(awk -F'\t' 'NR > 1 && $12 == "unplaced" && $13 == 6' "$DA/restore_dry.tsv" | wc -l); n7=$(awk -F'\t' 'NR > 1 && $12 == "unplaced" && $13 == 7' "$DA/restore_dry.tsv" | wc -l); nx=$(awk -F'\t' '$5 == "NOT-ONE"' "$K" | wc -l)
echo "key-2 list $K: $nk slots (expect 83) = reason 6 $n6 (expect 79) + reason 7 $n7 (expect 4); key 2 not one slot: $nx (expect 0); sha256 $(sha256sum < "$K" | cut -d' ' -f1)"
[ "$nk" = 83 ] && [ "$n6" = 79 ] && [ "$n7" = 4 ] && [ "$nx" = 0 ] || { echo "STEP9A-DRY2 RESULT: STOP - the key-2 list is not the ruled 83"; exit 1; }
echo "--- the key-2 list in full (book chapter verse old_position new_position):"
sed -n '2,$p' "$K" | sed 's/\t/ /g; s/^/  /'
# --- the restore dry run with the list (writes only its --report) ---
echo "=== restore_surface_fill DRY RUN on built: --base 391141 --key2-alone (83), no leave list, no --prefill ==="
python3 scripts/restore_surface_fill.py "$B" --snapshot "$SNAP" --lexicon "$LEX" --report "$D/restore_dry2.tsv" --base 391141 --key2-alone "$K" > "$D/restore_dry2.out" 2>&1; r=$?
sed -n '1,/^RE-KEY/p' "$D/restore_dry2.out"
sed -n '/^G1a/{p;n;p}' "$D/restore_dry2.out"
sed -n '/^UNPLACED rows/,/^$/p' "$D/restore_dry2.out"
sed -n '/^LISTED slots that do not resolve/,/^$/p' "$D/restore_dry2.out"
sed -n '/^PLACED rows that MOVED/,/^$/p' "$D/restore_dry2.out"
sed -n '/^SUMMARY/,$p' "$D/restore_dry2.out"
echo "restore exit $r (0 = every gate passes)"
sed -n '/^RESULT: DRY RUN COMPLETE/p' "$D/restore_dry2.out" | sed -n '1p' > "$D/result.txt"
[ -s "$D/result.txt" ] || { echo "STEP9A-DRY2 RESULT: STOP - the restore did not finish its dry run (full output: $D/restore_dry2.out)"; exit 1; }
echo "full restore output: $D/restore_dry2.out ($(wc -l < "$D/restore_dry2.out") lines); report $D/restore_dry2.tsv: $(wc -l < "$D/restore_dry2.tsv") lines, sha256 $(sha256sum < "$D/restore_dry2.tsv" | cut -d' ' -f1)"
# --- each listed slot in the report: placed at exactly its listed position, by the listed rule ---
awk -F'\t' 'FNR == 1 {f++; next} f == 1 {want[$1 FS $2 FS $3 FS $4] = $5; next} ($1 FS $2 FS $3 FS $4) in want {n++; if ($12 == "placed" && $5 == want[$1 FS $2 FS $3 FS $4] && index($14, "key-2 alone (listed)") == 1) ok++; else print "  NOT AS LISTED: " $1 " " $2 ":" $3 " pos " $4 " -> " $5 " " $12 " r" $13 " " $14} END {print "listed slots found in the report: " n + 0 " (expect 83); placed at exactly the listed position by key 2 alone: " ok + 0 " (expect 83)"}' "$K" "$D/restore_dry2.tsv"
echo "--- the 9 slots ruled on the context read (sec 9.124 rulings 2-3), as the report has them - verse | old pos -> new pos | action | cls | result | detail | lexicon:"
awk -F'\t' -v OFS=' | ' '($1 " " $2 ":" $3 " " $4) ~ /^(Lev 20:15 4|Deu 28:62 5|Jos 5:5 30|1Ki 8:44 25|Job 32:21 8|Jos 12:23 2|1Ki 14:20 4|Jer 26:21 19|Psa 71:0 0)$/ {print "  " $1 " " $2 ":" $3, $4 " -> " $5, $6, $7, $12, $14, $15}' "$D/restore_dry2.tsv"
# --- expected read-outs (traced; NOT gates - sec 9.124 ruling 5) ---
SUM=$(sed -n '/^SUMMARY/,$p' "$D/restore_dry2.out")
chk() { case "$SUM" in *"$2"*) echo "  $1: yes";; *) echo "  $1: NO (expected text: $2)";; esac; }
echo "--- read-outs vs the traced expectation (not gates):"
chk "placed 4,411 = agree-strong 3,977 + agree-weak 351 + key-2 listed 83" "4,411 | 4,411   (agree-strong 3,977 · agree-weak 351 · key-2 listed 83)"
chk "unplaced 0" "unplaced                  0 | 0"
chk "listed slots not as listed 0" "listed slots not as listed 0 | 0"
chk "placed inserts / updates 3,873 / 538" "3,873 / 538 | 3,873 / 538"
chk "moved 6 (the trial's 6; the 4 r7 place at their old positions)" "placed rows that moved    — | 6"
chk "Lexicon pass 4,022 / uncovered 389 (the trial's + the 4 r7)" "{'pass': 4022, 'uncovered': 389}"
chk "after-count 391,141 + 3,873 = 395,014" "base 391,141 + inserts written 3,873 = 395,014"
chk "every gate passes" "every gate PASSES"
bs1=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' '); echo "built + src size and time before = after: $([ "$bs1" = "$bs0" ] && echo yes || echo NO)"
[ "$bs1" = "$bs0" ] || { echo "STEP9A-DRY2 RESULT: STOP - built or src changed during a read-only run - report this"; exit 1; }
echo "STEP9A-DRY2 RESULT: READ DONE - restore exit $r: $(cat "$D/result.txt")"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9A-DRY2 reviewed (11/15) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - STEP9A-DRY2 only reads. It re-runs the 9a restore dry run (no --apply) under REF 88f7a5f6 with the 83-slot key-2 list from §9.124 ruling 4 and an empty leave list. Its `chk` texts match the restore's SUMMARY format, and the restore's own gates stay the gates (§9.124 ruling 5)."
Reviewer note (not a stop): "moved 6" assumes the 4 r7 place at their old positions (shown by the CTX log); a NO there is
information, not a failure.

### STEP9A-DRY2 ran (11/15, 13:36 UTC, PA HEAD 476de530, REF 88f7a5f6) — READ DONE, restore exit 0, every gate PASSES

Log `~/edition_upgrade_runs/step9a_dry2_20261115.log`; folder `step9a_dry2_20261115/`. PRE OK; snapshot d9435bde… (pin), lexicon
91d9d036…, STEP9A-DRY report fb5daacf… (= ruled); CHECK OK (391,141, 70af7a4a08e7). Key-2 list 83 = r6 79 + r7 4, NOT-ONE 0,
**sha d0967a0d7a725270bedd914e2760d79b6416d6b40ce38cf84165d3ca36f0dc5e** (printed in full in the log). Restore: S / L / V / G1a PASS;
placed 4,411 (3,977 · 351 · key-2 listed 83); unplaced 0; listed-not-as-listed 0; inserts / updates 3,873 / 538; moved 6 (Gen 5:25
1→2, Gen 5:26 1→2, Gen 34:4 1→2, Jos 5:15 27→26, 2Ki 23:35 6→7, Est 5:9 12→13); Lexicon pass 4,022 / uncovered 389; after-count
395,014; "every gate PASSES". Report `restore_dry2.tsv` 4,412 lines, **sha e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a**.
83 / 83 listed slots placed at exactly their listed position by key 2 alone; the 9 CTX slots placed as ruled. All eight read-outs
yes. Built + src untouched.

**Ruling (11/15, §9.126): STEP9A declaration** (figures above, for STEP9A-APPLY); draft STEP9A-APPLY (F3 before.db, prove built =
STEP9-APPLY's result, restore `--apply` same arguments, after-checks: 395,014 / 149 untouched + schema / before → after = exactly
the 4,411 snapshot rows / the restore's own post-write gates).

## STEP9A-APPLY drafted (11/15, GATE REF 88f7a5f6) — for the ruling chat (a write; reviewer on mechanics)

**Before the write (every miss = STOP, built untouched):** pre (REF 88f7a5f6; run folder `step9a_apply_20261115/`); home disk in use
printed (adds ~0.13 GB); snapshot / lexicon / key-2 list (copied into the run folder) / STEP9A-DRY2 report = the declared shas;
built = STEP9-APPLY's result (`eu_step check` vs STEP9-DRY2) and abp_surface 391,141. **prep** (`--copy
verses,words,lexicon,dotted_lexicon,abp_surface --save abp_surface`, as STEP9-DRY2): state.json, **before.db = built's
abp_surface before 9a (F3, the 9c before side)**, and a THROWAWAY copy dry.db. **The same restore `--apply` on the throwaway copy
first:** exit 0 + "RESTORED, ALL CHECKS PASS"; its placed line = the declared one; its report sha = e154d8d4… (= the dry report,
row for row); its table 395,014; before → throwaway delta (`eu_step delta`, key verse_id+position) = added 3,873 / changed 538 /
removed 0, and its slot + kind set = the report's placed inserts / updates at their new slots (verse ids read from built). `same`:
built untouched since prep.
**The write:** the restore `--apply` on built, the STEP9A-DRY2 arguments (`--base 391141 --key2-alone <the list>`, no leave list,
no `--prefill`); its S / L / V / G1a / MOVED / SUMMARY / W / post-write / T / RESULT lines printed.
**After (every miss = CHECK, naming the restore source `step9a_apply_20261115/before.db`):** restore exit 0 + "RESTORED, ALL
CHECKS PASS" (its own G1 / written-rows / every-other-row / new-rows / NBSP / translit / quick_check gates); placed line = declared;
apply report sha = e154d8d4…; abp_surface 395,014; `eu_step check` vs this block's prep + the throwaway (149 untouched + schema;
abp_surface = the throwaway's); before → after delta sha = the before → throwaway delta's (so exactly the 4,411 snapshot slots).
Local test (fake copies; fake clone at 88f7a5f6 + fake counts/pin; the fake STEP9A-DRY2 folder re-made): DONE, every line as
above (3 inserts + 1 update; check OK; delta = throwaway's); a wrong declared figure → STOP before the write, built byte-identical;
a forced post-write miss → "CHECK - report differ … Restore source …/before.db"; built altered since STEP9-APPLY → STOP; re-paste
→ STOP.

### Block STEP9A-APPLY (GATE REF 88f7a5f6; WRITES built: abp_surface only, 391,141 → 395,014) — for the ruling chat
```bash
set +H
L=~/edition_upgrade_runs/step9a_apply_20261115.log
if [ -e "$L" ]; then echo "STEP9A-APPLY RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=88f7a5f6
echo "GATE REF ${REF} - STEP9A-APPLY rebuild-words step 9a on BUILT: restore_surface_fill --apply at --base 391141 with the 83-slot key-2 list, leave list empty, gated on the STEP9A-DRY2 figures (sec 9.124 / 9.125 + the STEP9A declaration) - WRITES built: abp_surface only (391,141 -> 395,014) - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9A-APPLY RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
SNAP=tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv
LEX=abp_helps/analytical_lexicon.tsv
DD=~/edition_upgrade_runs/step9_dry2_20261114
DA2=~/edition_upgrade_runs/step9a_dry2_20261115
D=~/edition_upgrade_runs/step9a_apply_20261115
E="python3 scripts/eu_step.py"
TAB=$'\t'
# --- declared figures: STEP9A-DRY2 log (11/15 13:36Z), ruled 11/15 (the STEP9A declaration) ---
XSNAP=d9435bdea8f3ec768053dbefb8c19a920905ed616bdfcb3b2a5f55cf9b4a295b
XLEX=91d9d036c0922ef965f03a006de24492f7ba3159b2714a4a47c61cc680e5eac8
XK=d0967a0d7a725270bedd914e2760d79b6416d6b40ce38cf84165d3ca36f0dc5e
XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a
XBASE=391141; XAFTER=395014; XINS=3873; XUPD=538
XSUM="placed                    4,411 | 4,411   (agree-strong 3,977 · agree-weak 351 · key-2 listed 83)"
# the restore on db $1, report $2, output $3 - the STEP9A-DRY2 arguments + --apply
restore() { python3 scripts/restore_surface_fill.py "$1" --snapshot "$SNAP" --lexicon "$LEX" --report "$2" --base "$XBASE" --key2-alone "$D/key2_list.tsv" --apply > "$3" 2>&1; }
# --- before the write: every miss is STOP, built untouched ---
$E pre --tag STEP9AA --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "STEP9A-APPLY RESULT: STOP - pre (line above); built untouched"; exit 1; }
dk=$(du -sk ~ 2>/dev/null | cut -f1); echo "home in use: $dk KB (the dashboard quota is 10 GB; this run adds about 0.13 GB - one copy like STEP9-DRY2's ~110 MB + before.db ~18 MB)"
for f in "$SNAP" "$SNAP.sha256" "$LEX" "$DA2/key2_list.tsv" "$DA2/restore_dry2.tsv"; do [ -s "$f" ] || { echo "STEP9A-APPLY RESULT: STOP - missing or empty: $f; built untouched"; exit 1; }; done
s=$(sha256sum < "$SNAP" | cut -d' ' -f1); echo "snapshot: sha256 $s (expect $XSNAP)"; [ "$s" = "$XSNAP" ] || { echo "STEP9A-APPLY RESULT: STOP - not the declared snapshot; built untouched"; exit 1; }
s=$(sha256sum < "$LEX" | cut -d' ' -f1); echo "lexicon: sha256 $s (expect $XLEX)"; [ "$s" = "$XLEX" ] || { echo "STEP9A-APPLY RESULT: STOP - not the declared lexicon; built untouched"; exit 1; }
cp "$DA2/key2_list.tsv" "$D/key2_list.tsv" || { echo "STEP9A-APPLY RESULT: STOP - cannot copy the key-2 list; built untouched"; exit 1; }
s=$(sha256sum < "$D/key2_list.tsv" | cut -d' ' -f1); echo "key-2 list (copied from STEP9A-DRY2): $(($(wc -l < "$D/key2_list.tsv") - 1)) slots, sha256 $s (expect 83, $XK)"
[ "$s" = "$XK" ] || { echo "STEP9A-APPLY RESULT: STOP - not the declared key-2 list; built untouched"; exit 1; }
s=$(sha256sum < "$DA2/restore_dry2.tsv" | cut -d' ' -f1); echo "STEP9A-DRY2 report: sha256 $s (expect $XR)"; [ "$s" = "$XR" ] || { echo "STEP9A-APPLY RESULT: STOP - not the declared dry report; built untouched"; exit 1; }
echo "=== built = what STEP9-APPLY left (eu_step check against STEP9-DRY2's prep + dry copy; read-only) ==="
$E check --tag STEP9AA --built "$B" --dir "$DD" --written abp_surface || { echo "STEP9A-APPLY RESULT: STOP - built is not STEP9-APPLY's result (lines above); built untouched"; exit 1; }
n0=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_surface"); echo "abp_surface on built: $n0 (expect $XBASE)"
[ "$n0" = "$XBASE" ] || { echo "STEP9A-APPLY RESULT: STOP - built's abp_surface is not $XBASE; built untouched"; exit 1; }
echo "=== prep: state of built, before.db (built's abp_surface before 9a = the 9c before side, F3) and a THROWAWAY copy ==="
$E prep --tag STEP9AA --built "$B" --dir "$D" --copy verses,words,lexicon,dotted_lexicon,abp_surface --save abp_surface || { echo "STEP9A-APPLY RESULT: STOP - prep (line above); built untouched"; exit 1; }
echo "before.db: sha256 $(sha256sum < "$D/before.db" | cut -d' ' -f1), abp_surface $(sqlite3 -readonly "$D/before.db" "SELECT count(*) FROM abp_surface") rows (expect $XBASE)"
# --- the same restore on the THROWAWAY copy first: it must end exactly as STEP9A-DRY2 said ---
echo "=== restore --apply on the THROWAWAY copy $D/dry.db (same arguments) ==="
restore "$D/dry.db" "$D/report_drycopy.tsv" "$D/drycopy.out"; rc=$?
sed -n '/^SUMMARY/,$p' "$D/drycopy.out"
echo "throwaway restore exit $rc (expect 0)"
[ "$rc" = 0 ] && [ -n "$(sed -n '/^RESULT: RESTORED, ALL CHECKS PASS/p' "$D/drycopy.out")" ] || { echo "STEP9A-APPLY RESULT: STOP - the restore did not pass on the throwaway copy (full output $D/drycopy.out); built untouched"; exit 1; }
case "$(cat "$D/drycopy.out")" in *"$XSUM"*) ;; *) echo "STEP9A-APPLY RESULT: STOP - the throwaway copy's placed line is not the declared one; built untouched"; exit 1;; esac
s=$(sha256sum < "$D/report_drycopy.tsv" | cut -d' ' -f1); echo "throwaway report: sha256 $s (expect $XR = STEP9A-DRY2's, row for row)"
[ "$s" = "$XR" ] || { echo "STEP9A-APPLY RESULT: STOP - the throwaway report differs from the dry report; built untouched"; exit 1; }
n=$(sqlite3 -readonly "$D/dry.db" "SELECT count(*) FROM abp_surface"); echo "throwaway abp_surface: $n (expect $XAFTER)"
[ "$n" = "$XAFTER" ] || { echo "STEP9A-APPLY RESULT: STOP - the throwaway table is not $XAFTER; built untouched"; exit 1; }
# before -> throwaway after = exactly the 4,411 snapshot slots: 3,873 added at the inserts' new slots + 538 changed at the updates'
$E delta --tag STEP9AA --a "$D/before.db" --b "$D/dry.db" --table abp_surface:verse_id+position --out "$D/delta_drycopy.tsv" --show 5 > "$D/delta_drycopy.out" 2>&1 || { cat "$D/delta_drycopy.out"; echo "STEP9A-APPLY RESULT: STOP - delta before -> throwaway (lines above); built untouched"; exit 1; }
cat "$D/delta_drycopy.out"
XD=$(sha256sum < "$D/delta_drycopy.tsv" | cut -d' ' -f1)
sqlite3 -readonly -separator "$TAB" "$B" "SELECT id, book, chapter, verse FROM verses" > "$D/verse_ids.tsv" || { echo "STEP9A-APPLY RESULT: STOP - verses read failed; built untouched"; exit 1; }
awk -F'\t' -v OFS='\t' 'FNR == 1 {f++} f == 1 {id[$2 FS $3 FS $4] = $1; next} FNR > 1 && $12 == "placed" {print "abp_surface", (($6 == "insert") ? "ADDED" : "CHANGED"), "(" id[$1 FS $2 FS $3] ", " $5 ")"}' "$D/verse_ids.tsv" "$D/report_drycopy.tsv" | sort > "$D/expect_keys.tsv"
sed '1d' "$D/delta_drycopy.tsv" | cut -f1-3 | sort > "$D/delta_keys.tsv"
na=$(awk -F'\t' '$2 == "ADDED"' "$D/delta_keys.tsv" | wc -l); nc=$(awk -F'\t' '$2 == "CHANGED"' "$D/delta_keys.tsv" | wc -l); nr=$(awk -F'\t' '$2 == "REMOVED"' "$D/delta_keys.tsv" | wc -l)
echo "before -> throwaway: added $na (expect $XINS), changed $nc (expect $XUPD), removed $nr (expect 0); slots + kind = the report's placed inserts / updates at their new slots: $(cmp -s "$D/expect_keys.tsv" "$D/delta_keys.tsv" && echo yes || echo NO); delta sha256 $XD"
[ "$na" = "$XINS" ] && [ "$nc" = "$XUPD" ] && [ "$nr" = 0 ] && cmp -s "$D/expect_keys.tsv" "$D/delta_keys.tsv" || { echo "STEP9A-APPLY RESULT: STOP - the throwaway's change is not exactly the 4,411 snapshot slots; built untouched"; exit 1; }
$E same --tag STEP9AA --built "$B" --dir "$D" || { echo "STEP9A-APPLY RESULT: STOP - built changed since prep (lines above); built untouched"; exit 1; }
# --- the write ---
echo "=== APPLY: restore_surface_fill --apply on BUILT ($B) - writes abp_surface only ==="
restore "$B" "$D/report_apply.tsv" "$D/apply.out"; r=$?
sed -n '1,/^RE-KEY/p' "$D/apply.out"
sed -n '/^G1a/{p;n;p}' "$D/apply.out"
sed -n '/^PLACED rows that MOVED/,/^$/p' "$D/apply.out"
sed -n '/^SUMMARY/,$p' "$D/apply.out"
echo "restore exit $r (expect 0)"
# --- after the write: every miss is CHECK ---
FL=""
[ "$r" = 0 ] && [ -n "$(sed -n '/^RESULT: RESTORED, ALL CHECKS PASS/p' "$D/apply.out")" ] || FL="$FL restore"
case "$(cat "$D/apply.out")" in *"$XSUM"*) ;; *) FL="$FL placed-line";; esac
s=$(sha256sum < "$D/report_apply.tsv" 2>/dev/null | cut -d' ' -f1); echo "apply report: sha256 $s (expect $XR = the dry report, row for row)"; [ "$s" = "$XR" ] || FL="$FL report"
n1=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_surface"); echo "abp_surface on built: $n1 (expect $XAFTER)"; [ "$n1" = "$XAFTER" ] || FL="$FL count"
CHK=$($E check --tag STEP9AA --built "$B" --dir "$D" --written abp_surface 2>&1); k=$?; echo "$CHK"; [ "$k" = 0 ] || FL="$FL check"
VAL=$($E delta --tag STEP9AA --a "$D/before.db" --b "$B" --table abp_surface:verse_id+position --out "$D/delta_built.tsv" --show 5 --expect-sha "$XD" 2>&1); v=$?; echo "$VAL"
echo "built before -> built after = before -> throwaway (exactly the 4,411 snapshot slots; sha $XD): $([ "$v" = 0 ] && echo yes || echo NO)"; [ "$v" = 0 ] || FL="$FL delta"
if [ -z "$FL" ]; then
  echo "STEP9A-APPLY RESULT: DONE - built abp_surface 391,141 -> 395,014 (3,873 inserts + 538 updates = the 4,411 snapshot slots, 83 by key 2 alone); report = the dry report (e154d8d4...); = the throwaway copy (check OK, 149 untouched + schema); the restore's own post-write gates PASS. Pre-9a copy (the 9c before side): $D/before.db"; exit 0
fi
echo "STEP9A-APPLY RESULT: CHECK -$FL differ (lines above). Restore source for abp_surface: $D/before.db"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9A-APPLY reviewed (11/15) — REVIEW: ESCALATE (a write, §9.90 — the gate is the ruling chat's); no mechanical defect
Verdict line verbatim: "REVIEW: ESCALATE - STEP9A-APPLY writes to built (abp_surface 391,141 -> 395,014), so only the ruling chat can rule the write gate (sec 9.90). I found no mechanical defect. One note: the full lexicon sha in the block cannot be traced past its 8-character prefix."
**Lexicon sha, traced:** the full value `91d9d036c0922ef965f03a006de24492f7ba3159b2714a4a47c61cc680e5eac8` is printed on the "lexicon
abp_helps/analytical_lexicon.tsv: 39540 lines, sha256 …" line of both `~/edition_upgrade_runs/step9a_dry_20261115.log` and
`~/edition_upgrade_runs/step9a_dry2_20261115.log` (as pasted 11/15); the block's XLEX is that value. A wrong value would STOP before
the write.

**Ruling (11/15, §9.127): STEP9A-APPLY cleared to run** on the §9.126 figures. After its log: push, write the successor handoff;
nothing else runs on PA in this session (JP: new CC + reviewer sessions after 9a closes).

### STEP9A-APPLY ran (11/15, PA HEAD 476de530, REF 88f7a5f6) — DONE, exit 0 → STEP 9a CLOSED at 395,014 (§9.128)

Log `~/edition_upgrade_runs/step9a_apply_20261115.log`; run folder `step9a_apply_20261115/`. Started 13:57:29Z (GATE REF line;
the full log was pasted on a second paste — the first began at the check section). PRE OK (88f7a5f6 an ancestor of HEAD,
scripts/tests = REF, no journals, both rollback copies present); home in use 7,378,000 KB before the run; snapshot d9435bde…,
lexicon 91d9d036c0922ef9…, key-2 list 83 / d0967a0d…, STEP9A-DRY2 report e154d8d4… — each = declared. Pre-write: CHECK OK vs STEP9-DRY2 (391,141, 70af7a4a08e7); prep: 150 tables / 3,806,633 rows / 300 schema entries;
**before.db 18,194,432 B, sha ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273, 391,141 rows** (the pre-9a copy,
the 9c before side, F3); dry.db 109,780,992 B. Throwaway restore: all gates PASS, placed line = declared, report e154d8d4… (= the
dry report), 395,014; before → throwaway 3,873 added / 538 changed / 0 removed at exactly the report's slots, delta sha
77d619039ef0474c742650e910d18ee150d202612bfd5717031123a850ba1f1a; SAME OK. **Write on built:** S / L / V / G1a PASS; moved 6
(Gen 5:25, 5:26, 34:4, Jos 5:15, 2Ki 23:35, Est 5:9); placed 4,411 (3,977 · 351 · key-2 listed 83); 3,873 / 538; Lexicon 4,022 /
389; W: journal delete, 391,141 under the lock, post-write 395,014, 4,411 written rows = snapshot form + translit, every other row
unchanged, new rows = the insert slots, no NBSP / ἡ, COMMITTED; T: translit rule 0, quick_check ok. **After:** apply report sha
e154d8d4… (`step9a_apply_20261115/report_apply.tsv`); abp_surface 395,014; CHECK OK (149 untouched + schema; abp_surface
219a3ebe7075 = throwaway); before → after delta = the throwaway's (77d61903…).
**Ruling (11/15, §9.128): step 9a applied on built and CLOSED at 395,014.** Observed, no ruling: "APPLY (copy only)" / "(on a
copy)" are the restore's fixed labels. Push; successor handoff (`HANDOFF_edition_upgrade_stageE.md`); nothing further on PA.

## New CC + reviewer sessions (11/15, §9.127) — read-in confirmed; STEP9B drafted (GATE REF 88f7a5f6)

Read-in (repo at f4521e5d, scripts/tests = 88f7a5f6, 476de530 an ancestor of HEAD): handoff SUCCESSOR START; DESIGN §9.105-§9.128;
this record from "Step 9 → 9a → 9b → 9c" to the end. Figures as recorded: built abp_surface 395,014 (`219a3ebe7075`); pre-9a copy
`step9a_apply_20261115/before.db` 18,194,432 B, sha `ea6c54c3…e7273`, 391,141 rows; 9a apply report `report_apply.tsv` 4,412 lines,
sha `e154d8d4…`; key-2 list 83 (`d0967a0d…`), leave list empty; code REF 88f7a5f6, PA HEAD 476de530.

**STEP9B** (`step9b_floor_20261115`), read-only. **Guards (STOP):** pre (REF 88f7a5f6; `--keep` the two rollbacks + the pre-9a copy);
the three 9a files on PA = the recorded shas (before.db also 391,141 rows); built = STEP9A-APPLY's result (`eu_step check` vs the
9a folder's prep + throwaway; on a mismatch check adds a NEW `step9a_apply_20261115/check_delta_abp_surface.tsv`) and abp_surface
395,014; the control copy = the pre-9a sha; built / src / before.db size+time before = after. **Gate (CHECK on a miss):**
`health_check.py <built> --surface-floor=395014 --no-backup-check --no-disk-check` — exactly one floor line, reading
`[OK  ] abp_surface rows BELOW floor 395014 …: 0`; full report printed. **Control (CHECK on a miss):** the same on a COPY of the
pre-9a table → `[WARN] … floor 395014 …: 3873` (the default 395,003 would read 3,862, so it also proves the `=` argument is used
on PA); health_check never opens the kept before.db itself. **Read-out, not a gate:** src at the default floor 395,003, every
report line that differs src → built. The 9b "oracle" half (rebuild-words.md :313-315) is same-code only; the 9a block proved
before → after = exactly the 4,411 slots (§9.128).
Local test (WSL, fake HOME, clone at f4521e5d; made-up built 395,014 / src 395,003 with a real eu_step prep + 3,873 inserts; fake
shas): clean PASS exit 0; re-paste → STOP; control at the default floor → NO (3862) → CHECK; floor pattern broken → CHECK floor;
wrong pre-9a sha → STOP; one built row changed → check FAIL → STOP; -journal beside built → pre STOP; clean re-run PASS.

### Block STEP9B (GATE REF 88f7a5f6; READ-ONLY — writes only its run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/step9b_floor_20261115.log
if [ -e "$L" ]; then echo "STEP9B RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=88f7a5f6
echo "GATE REF ${REF} - STEP9B rebuild-words step 9b on BUILT: health_check abp_surface floor at --surface-floor=395014 (= step 9's 391,141 + the 3,873 restored inserts; charter sec 6, DESIGN 9.120) + a control on a copy of the pre-9a table + src's report beside built's - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9B RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
DA=~/edition_upgrade_runs/step9a_apply_20261115
D=~/edition_upgrade_runs/step9b_floor_20261115
E="python3 scripts/eu_step.py"
# --- declared figures: STEP9A-APPLY log (11/15), DESIGN 9.126 / 9.128 ---
XFLOOR=395014; XPRE=391141; XSHORT=3873
XB4=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273
XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a
XK=d0967a0d7a725270bedd914e2760d79b6416d6b40ce38cf84165d3ca36f0dc5e
# the floor line as health_check prints it (health_check.py:151 label, :299-300 format); $1 = status, $2 = floor, $3 = shortfall
fline() { printf '  [%s] abp_surface rows BELOW floor %s  [fill or a backfill missing?]: %s   (' "$1" "$2" "$3"; }
hc() { python3 scripts/health_check.py "$@" --no-backup-check --no-disk-check; }
# --- before the health check: every miss is STOP ---
$E pre --tag STEP9B --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db --keep "$DA/before.db" || { echo "STEP9B RESULT: STOP - pre (line above); nothing read"; exit 1; }
for f in "$DA/before.db" "$DA/report_apply.tsv" "$DA/key2_list.tsv" "$DA/state.json" "$DA/dry.db"; do [ -s "$f" ] || { echo "STEP9B RESULT: STOP - missing or empty: $f"; exit 1; }; done
echo "=== the 9a files on PA (the 9c inputs) = the STEP9A-APPLY record ==="
s=$(sha256sum < "$DA/before.db" | cut -d' ' -f1); n=$(sqlite3 -readonly "$DA/before.db" "SELECT count(*) FROM abp_surface"); echo "pre-9a copy $DA/before.db: $(stat -c %s "$DA/before.db") bytes, sha256 $s, abp_surface $n rows (expect 18194432, $XB4, $XPRE)"
[ "$s" = "$XB4" ] && [ "$n" = "$XPRE" ] || { echo "STEP9B RESULT: STOP - the pre-9a copy is not the recorded one - report this"; exit 1; }
s=$(sha256sum < "$DA/report_apply.tsv" | cut -d' ' -f1); echo "9a apply report $DA/report_apply.tsv: $(wc -l < "$DA/report_apply.tsv") lines, sha256 $s (expect 4412, $XR)"
[ "$s" = "$XR" ] || { echo "STEP9B RESULT: STOP - the 9a apply report is not the recorded one - report this"; exit 1; }
s=$(sha256sum < "$DA/key2_list.tsv" | cut -d' ' -f1); echo "key-2 list $DA/key2_list.tsv: $(($(wc -l < "$DA/key2_list.tsv") - 1)) slots, sha256 $s (expect 83, $XK)"
[ "$s" = "$XK" ] || { echo "STEP9B RESULT: STOP - the key-2 list is not the recorded one - report this"; exit 1; }
echo "=== built = what STEP9A-APPLY left (eu_step check against STEP9A-APPLY's prep + throwaway copy; read-only) ==="
$E check --tag STEP9B --built "$B" --dir "$DA" --written abp_surface || { echo "STEP9B RESULT: STOP - built is not STEP9A-APPLY's result (lines above)"; exit 1; }
n0=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_surface"); echo "abp_surface on built: $n0 (expect $XFLOOR)"
[ "$n0" = "$XFLOOR" ] || { echo "STEP9B RESULT: STOP - built's abp_surface is not $XFLOOR"; exit 1; }
cp "$DA/before.db" "$D/control_pre9a.db" || { echo "STEP9B RESULT: STOP - cannot copy the pre-9a table for the control"; exit 1; }
s=$(sha256sum < "$D/control_pre9a.db" | cut -d' ' -f1); echo "control copy $D/control_pre9a.db: sha256 $s (expect $XB4)"
[ "$s" = "$XB4" ] || { echo "STEP9B RESULT: STOP - the control copy is not the pre-9a copy"; exit 1; }
st0=$(stat -c '%s %Y' "$B" "$S" "$DA/before.db" | tr '\n' ' ')
FL=""
# --- 9b: the floor on built (the gate: shortfall 0 at the declared floor) ---
echo "=== 9b: health_check on BUILT, --surface-floor=$XFLOOR (full report) ==="
hc "$B" --surface-floor="$XFLOOR" > "$D/health_built.out" 2>&1; r=$?
cat "$D/health_built.out"
echo "health_check exit $r (expect 0)"; [ "$r" = 0 ] || FL="$FL built-exit"
nf=$(grep -cF -- "$(fline 'OK  ' "$XFLOOR" 0)" "$D/health_built.out"); na=$(grep -c 'abp_surface rows BELOW floor' "$D/health_built.out")
echo "9b floor line on built reads [OK  ] ... floor $XFLOOR ...: 0 - $([ "$nf" = 1 ] && [ "$na" = 1 ] && echo yes || echo NO) (matching $nf, floor lines $na; expect 1, 1)"
[ "$nf" = 1 ] && [ "$na" = 1 ] || FL="$FL floor"
# --- control (the detector must fire on a known positive): the pre-9a table at the same floor ---
echo "=== control: health_check on a COPY of the pre-9a table ($XPRE rows, abp_surface only), --surface-floor=$XFLOOR ==="
hc "$D/control_pre9a.db" --surface-floor="$XFLOOR" > "$D/health_control.out" 2>&1; rc=$?
grep 'abp_surface rows BELOW floor' "$D/health_control.out"
echo "control exit $rc (expect 0); its other checks read ERR because the copy holds abp_surface only: $(grep -c '^  \[ERR \]' "$D/health_control.out") ERR lines (full output $D/health_control.out)"
nc=$(grep -cF -- "$(fline WARN "$XFLOOR" "$XSHORT")" "$D/health_control.out")
echo "control floor line reads [WARN] ... floor $XFLOOR ...: $XSHORT (= the 3,873 inserts 9a put back; the default 395003 would read 3862): $([ "$nc" = 1 ] && echo yes || echo NO)"
[ "$rc" = 0 ] && [ "$nc" = 1 ] || FL="$FL control"
# --- read-out, not a gate: src (pre-upgrade live) at its own floor, every line beside built's ---
echo "=== read-out (not a gate): health_check on SRC at the default floor 395003 - lines that differ src -> built ==="
hc "$S" > "$D/health_src.out" 2>&1; rs=$?
echo "src: exit $rs; floor line: $(grep 'abp_surface rows BELOW floor' "$D/health_src.out" | sed 's/^ *//')"
diff <(sed '1,2d' "$D/health_src.out") <(sed '1,2d' "$D/health_built.out") | sed -n '/^[<>]/p' | sed 's/^</  src  :/; s/^>/  built:/'
echo "(full src report: $D/health_src.out)"
st1=$(stat -c '%s %Y' "$B" "$S" "$DA/before.db" | tr '\n' ' ')
echo "built, src and the pre-9a copy: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO)"
[ "$st1" = "$st0" ] || { echo "STEP9B RESULT: STOP - built, src or the pre-9a copy changed during a read-only run - report this"; exit 1; }
if [ -z "$FL" ]; then
  echo "STEP9B RESULT: PASS - built abp_surface $XFLOOR, shortfall 0 at floor $XFLOOR; control: the pre-9a table reads shortfall $XSHORT at the same floor; built = STEP9A-APPLY's result; the 9a files = the record"; exit 0
fi
echo "STEP9B RESULT: CHECK -$FL (lines above)"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9B reviewed (11/15) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - read-only re-run of the ruled 9b gate (§9.120) at the §9.128 after-count, with a control that fires; repo guards are inside `eu_step pre`. The only files it writes are new run artifacts."
Reviewer note (not a stop): the full XR and XK shas rest on this record's STEP9A-DRY2 lines (:8927, :8930) quoting the PA log, not
on DESIGN text; the prefixes match §9.126 / §9.128 and a mismatch can only STOP. Every other figure traced to §9.120 / §9.126 /
§9.128 or health_check.py :144-152, :296-300.

### Ruling (11/15, §9.129) — STEP9B stands on the reviewer's CLEAR; JP runs it as printed
- **The one write outside the run folder:** `~/edition_upgrade_runs/step9a_apply_20261115/check_delta_abp_surface.tsv`, made by
  `eu_step check` (eu_step.py :489-492) only if built differs from what 9a left — a STOP path — and never over an existing file.
- **9b comparison against live — ruled N/A on this lane, not skipped:** `rebuild-words.md` :313-315 limits it to a same-code
  rebuild; this lane's 9a already showed before → after = exactly the 4,411 snapshot slots (3,873 added / 538 changed / 0
  removed, delta `77d61903…`, STEP9A-APPLY ran entry above, §9.128).
- The fingerprint-source point (full XR / XK shas) was raised and withdrawn: the STEP9A-DRY2 "ran" entry (:8927, :8930) carries
  both in full. No change to the block.
- Not a receipt (§9.90 / R2-b): the STEP9B log goes to the ruling chat before 9b is closed. 9c not cleared by any of this.

### STEP9B ran (11/15, 14:34:23Z, PA HEAD 476de530, REF 88f7a5f6) — PASS, exit 0 → STEP 9b CLOSED at 395,014 (§9.130)
Log `~/edition_upgrade_runs/step9b_floor_20261115.log`; folder `step9b_floor_20261115/`. PRE OK (built 452,063,232 B, src
451,964,928 B, no journals, triggers 0; both rollbacks + before.db present). The 9a files = declared, each sha printed in full:
before.db 18,194,432 B / ea6c54c3… / 391,141 rows; report_apply.tsv 4,412 lines / e154d8d4…; key2_list.tsv 83 / d0967a0d….
CHECK OK vs the 9a folder (149 unwritten + schema 0; abp_surface 395,014, 219a3ebe7075 = the throwaway; prep 391,141,
70af7a4a08e7). Built health report: 0 warnings, 0 errors; floor line `[OK  ] abp_surface rows BELOW floor 395014 …: 0` (matching
1, floor lines 1); informational lines: proper-noun extended numbers 24, G-bases with no lexicon gloss 7, metaV person/place
overlap 127 (15 with a place strongs_g). Control (pre-9a copy): `[WARN] … floor 395014 …: 3873`, exit 0, 15 ERR lines (copy holds
abp_surface only). Read-out: src exit 0, `[OK  ] … floor 395003 …: 0`; the floor line is the only line differing src → built.
Built, src, pre-9a copy untouched. No check_delta file written.
**Ruling (11/15, §9.130): step 9b CLOSED.** Next: 9c (code change → reviewer → ruling chat).

## STEP9C-FREEZE drafted (11/15, GATE REF 88f7a5f6) — the PA half of 9c: make the two 9c input files from built

Read-only on every database; writes only `step9c_freeze_20261115/` + its log; nothing into the PA checkout. The 9c CODE commit
(pins, rebuild-words 1a/9a, punct fixture swap, tests) comes after JP's scp and goes reviewer → ESCALATE → ruling chat (§9.129 (7)).
**Guards (STOP):** pre; before.db `ea6c54c3…`, report `e154d8d4…`, 10/25 fill `d9435bde…` (= restore_surface_fill.py:73 pin),
eligible `e540d34d`, PUNCT-RECON's `g3_today_members.txt` present; built = STEP9A-APPLY's result; abp_surface 395,014; built +
before.db untouched. **1. Re-freeze:** `snapshot_surface_fill.py --src <built> --prefill <before.db> --from-restore <report copy
+ .sha256> --out step9c_freeze_20261115/abp_surface_fill_20261115.tsv` (new path; no --replace); its own G0 / O / R; printed
lines checked: placed 4,411 · src-not-in-prefill 4,411 · prefill-not-in-src 538; 4,411 = 3,873 + 538; rows 4,411. **2. Second
derivation:** each new row joined to its 10/25 row through the report (old slot → new slot): action / cls / form / strongs /
k2_ordinal equal on all 4,411 (gates, traced: placement is key 2's slot, key2_at :170-179; 9a wrote the snapshot form); moved
(expect 6) and the other columns' differences are read-outs. **3. Punct:** port test, member-diff tests, v2 controls; `--v2 --list`
→ `punct_members_built_20261115.txt` (charter :555 recipe); 607 lines / 607 refs (§9.113) = PUNCT-RECON's 11/14 set; built's member
diff against the new file = "FAIL … content-other 1 … gone 0 - new on eligible 0 - changed ops 0 - unchanged 607" (exit 1, Job 3:3).
Not here: the `--check` round trip (needs the new pin = the 9c commit); placing files in PA's fixture folder (a checkout write).
Local test (WSL, fake HOME, made-up built with 4,411 fill slots + 3 punct verses + Job 3:3): clean READ DONE exit 0; re-paste STOP;
wrong report sha STOP; wrong pre-fill side → script G0 STOPPED → STOP; a 10/25 form changed → CHECK join; extra 11/14 ref → CHECK
punct; built row changed → STOP; clean re-run READ DONE.

### Block STEP9C-FREEZE (GATE REF 88f7a5f6; READ-ONLY — writes only its run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/step9c_freeze_20261115.log
if [ -e "$L" ]; then echo "STEP9C-FREEZE RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=88f7a5f6
echo "GATE REF ${REF} - STEP9C-FREEZE rebuild-words step 9c inputs: re-freeze the abp_surface fill from built after 9a (snapshot_surface_fill --from-restore the 9a apply report, pre-fill = the pre-9a copy; DESIGN 9.120 F3, charter sec 6) + the punct member list from built (607, DESIGN 9.113) - READ-ONLY on every database; writes only its run folder and log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9C-FREEZE RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
DA=~/edition_upgrade_runs/step9a_apply_20261115
PR=~/edition_upgrade_runs/punct_recon_20261114
OLD=tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv
EL=~/edition_upgrade_runs/step5_eligible_20261101.tsv
D=~/edition_upgrade_runs/step9c_freeze_20261115
NEW="$D/abp_surface_fill_20261115.tsv"
PM="$D/punct_members_built_20261115.txt"
E="python3 scripts/eu_step.py"
# --- declared figures: STEP9A-APPLY / STEP9B logs (DESIGN 9.126, 9.128, 9.130); PUNCT-RECON log (9.113) ---
XB4=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273
XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a
XOLD=d9435bdea8f3ec768053dbefb8c19a920905ed616bdfcb3b2a5f55cf9b4a295b
XROWS=4411; XINS=3873; XUPD=538; XAFTER=395014; XPUNCT=607
XSELF="V2 MEMBER DIFF: FAIL - word-order 0 - content-other 1 - dup-gloss 0 - Joh 14:26 clean - new on non-eligible 0 | to ruling: gone 0 - new on eligible 0 - changed ops 0 - unchanged 607"
# --- before the freeze: every miss is STOP ---
$E pre --tag STEP9C --ref "$REF" --dir "$D" --db "$B" --keep "$DA/before.db" || { echo "STEP9C-FREEZE RESULT: STOP - pre (line above); nothing read"; exit 1; }
for f in "$DA/before.db" "$DA/report_apply.tsv" "$DA/state.json" "$DA/dry.db" "$OLD" "$OLD.sha256" "$EL" "$PR/g3_today_members.txt"; do [ -s "$f" ] || { echo "STEP9C-FREEZE RESULT: STOP - missing or empty: $f"; exit 1; }; done
s=$(sha256sum < "$DA/before.db" | cut -d' ' -f1); echo "pre-9a copy (the --prefill side): sha256 $s (expect $XB4)"; [ "$s" = "$XB4" ] || { echo "STEP9C-FREEZE RESULT: STOP - the pre-9a copy is not the recorded one - report this"; exit 1; }
s=$(sha256sum < "$DA/report_apply.tsv" | cut -d' ' -f1); echo "9a apply report: sha256 $s (expect $XR)"; [ "$s" = "$XR" ] || { echo "STEP9C-FREEZE RESULT: STOP - the 9a apply report is not the recorded one - report this"; exit 1; }
s=$(sha256sum < "$OLD" | cut -d' ' -f1); echo "10/25 frozen fill $OLD: sha256 $s (expect $XOLD, the pin in restore_surface_fill.py:73)"; [ "$s" = "$XOLD" ] || { echo "STEP9C-FREEZE RESULT: STOP - the 10/25 frozen fill is not the pinned one"; exit 1; }
[ "$(sha256sum < "$EL" | cut -c1-8)" = e540d34d ] || { echo "STEP9C-FREEZE RESULT: STOP - eligible file is not step 5's (e540d34d...)"; exit 1; }
echo "=== built = what STEP9A-APPLY left (eu_step check against STEP9A-APPLY's prep + throwaway copy; read-only) ==="
$E check --tag STEP9C --built "$B" --dir "$DA" --written abp_surface || { echo "STEP9C-FREEZE RESULT: STOP - built is not STEP9A-APPLY's result (lines above)"; exit 1; }
n0=$(sqlite3 -readonly "$B" "SELECT count(*) FROM abp_surface"); echo "abp_surface on built: $n0 (expect $XAFTER)"
[ "$n0" = "$XAFTER" ] || { echo "STEP9C-FREEZE RESULT: STOP - built's abp_surface is not $XAFTER"; exit 1; }
st0=$(stat -c '%s %Y' "$B" "$DA/before.db" | tr '\n' ' ')
# --- 1. the fill re-freeze (the script's own G0 / O / R gates; G0 = built minus the pre-9a copy is exactly the report's placed slots at their new positions) ---
cp "$DA/report_apply.tsv" "$D/report_apply.tsv" || { echo "STEP9C-FREEZE RESULT: STOP - cannot copy the 9a report"; exit 1; }
printf '%s  report_apply.tsv\n' "$XR" > "$D/report_apply.tsv.sha256"
echo "=== 1. snapshot_surface_fill on built: --prefill the pre-9a copy, --from-restore the 9a report (copy + .sha256 in the run folder), --out a NEW file in the run folder ==="
python3 scripts/snapshot_surface_fill.py --src "$B" --prefill "$DA/before.db" --from-restore "$D/report_apply.tsv" --out "$NEW" > "$D/snapshot.out" 2>&1; r=$?
cat "$D/snapshot.out"; echo "snapshot exit $r (expect 0)"
[ "$r" = 0 ] && [ -n "$(sed -n '/^RESULT: SNAPSHOT WRITTEN/p' "$D/snapshot.out")" ] || { echo "STEP9C-FREEZE RESULT: STOP - the re-freeze did not pass its own gates (lines above); nothing else made"; exit 1; }
FL=""
chk() { case "$(cat "$D/snapshot.out")" in *"$2"*) echo "  $1: yes";; *) echo "  $1: NO (expected text: $2)"; FL="$FL $3";; esac; }
echo "--- the re-freeze vs the declared figures:"
chk "G0 = the restore report, 4,411 = 3,873 insert + 538 update" "PASS — 4,411 = 3,873 insert + 538 update = the restore report" g0
chk "report placed 4,411 · built-not-in-pre-9a 4,411 · pre-9a-not-in-built 538" "report placed 4,411 · src-not-in-prefill 4,411 · prefill-not-in-src 538" g0-counts
chk "O: every slot on one word row" "PASS — 4,411 slots, each on one word row" o
chk "rows 4,411" "rows                    4,411 | 4,411" rows
chk "inserts / updates 3,873 / 538" "inserts / updates       3,873 / 538 | 3,873 / 538" split
chk "report sha = its .sha256" "restore report sha256 $XR = its .sha256" report
NS=$(sha256sum < "$NEW" | cut -d' ' -f1); echo "new frozen file $NEW: $(($(wc -l < "$NEW") - 1)) rows, $(stat -c %s "$NEW") bytes, sha256 $NS; its .sha256 file: $(cat "$NEW.sha256")"
[ "$(cut -d' ' -f1 "$NEW.sha256")" = "$NS" ] || FL="$FL new-sha"
# --- 2. second derivation (read-out + gates): every new row against its 10/25 row, joined through the report (old slot -> new slot) ---
echo "=== 2. new frozen file vs the 10/25 frozen file, row by row through the 9a report (old slot -> new slot) ==="
awk -F'\t' '
  FNR == 1 {f++; if (f == 2 || f == 3) for (i = 1; i <= NF; i++) col[f, $i] = i; next}
  f == 1 && $12 == "placed" {nw[$1 FS $2 FS $3 FS $5] = $1 FS $2 FS $3 FS $4; np++; next}
  f == 2 {old[$2 FS $3 FS $4 FS $5] = $0; next}
  f == 3 {
    k = $2 FS $3 FS $4 FS $5; n++
    if ((k in nw) == 0) {print "  NOT IN THE REPORT: " k; miss++; next}
    ok = nw[k]; if ((ok in old) == 0) {print "  NO 10/25 ROW: " k " <- " ok; miss++; next}
    split(old[ok], o, "\t"); matched++
    nc = split("action cls form strongs k2_ordinal", must, " ")
    for (j = 1; j <= nc; j++) if (o[col[2, must[j]]] != $(col[3, must[j]])) {bad[must[j]]++; if (shown[must[j]]++ < 5) print "  " must[j] " differs at " k ": 10/25 [" o[col[2, must[j]]] "] -> new [" $(col[3, must[j]]) "]"}
    if (o[col[2, "position"]] != $(col[3, "position"])) moved++
    nr = split("translit old_form old_translit strongs_base english english_head is_pn k2_count", ro, " ")
    for (j = 1; j <= nr; j++) if (o[col[2, ro[j]]] != $(col[3, ro[j]])) diff[ro[j]]++
  }
  END {
    print "rows in the new file " n + 0 " (expect 4411); report placed " np + 0 " (expect 4411); joined to a 10/25 row " matched + 0 " (expect 4411); missing " miss + 0 " (expect 0)"
    printf "must be equal on every row (traced: placed at key 2'"'"'s slot = same full strongs + ordinal; written = the snapshot form, action, cls):"
    for (j = 1; j <= nc; j++) printf " %s %d", must[j], bad[must[j]] + 0; print " (expect 0 each)"
    print "slot moved (old position != new) " moved + 0 " (read-out; STEP9A-APPLY: moved 6)"
    printf "read-out, rows differing 10/25 -> new (not gates):"; for (j = 1; j <= nr; j++) printf " %s %d", ro[j], diff[ro[j]] + 0; print ""
    print "JOIN-OK " ((n == 4411 && np == 4411 && matched == 4411 && miss == 0) ? "yes" : "NO") " " ((bad["action"] + bad["cls"] + bad["form"] + bad["strongs"] + bad["k2_ordinal"]) == 0 ? "yes" : "NO")
  }' "$D/report_apply.tsv" "$OLD" "$NEW" > "$D/join.out" 2>&1
cat "$D/join.out"
[ "$(sed -n 's/^JOIN-OK //p' "$D/join.out")" = "yes yes" ] || FL="$FL join"
# --- 3. the punct member list from built (the 10/30 recipe, charter :555), then built's member diff against it ---
echo "=== 3. punct-position members on built (audit_reassembly_diff --v2 --list; read-only) ==="
python3 tests/test_reorder_port.py > "$D/t_port.out" 2>&1 || { tail -5 "$D/t_port.out"; echo "STEP9C-FREEZE RESULT: STOP - reorder port drifted from the JS baseline (the fill file is made; $D)"; exit 1; }
python3 tests/test_reassembly_member_diff.py > "$D/t_md.out" 2>&1 || { tail -5 "$D/t_md.out"; echo "STEP9C-FREEZE RESULT: STOP - the member diff's own tests failed (the fill file is made; $D)"; exit 1; }
python3 scripts/audit_reassembly_diff.py --controls --v2 > "$D/controls.out" 2>&1 || { tail -5 "$D/controls.out"; echo "STEP9C-FREEZE RESULT: STOP - v2 controls did not fire (the fill file is made; $D)"; exit 1; }
echo "port test, member-diff tests, v2 controls: pass"
python3 scripts/audit_reassembly_diff.py "$B" --v2 --list > "$D/list.out" 2>&1; rl=$?
sed -n '/^   by class:/,/^$/p' "$D/list.out"; echo "list exit $rl (expect 0)"; [ "$rl" = 0 ] || FL="$FL list-exit"
grep -E "^\s*\[punct-position" "$D/list.out" > "$PM"
np=$(wc -l < "$PM"); sed -n 's/^ *\[punct-position *\] \([^ ]* [0-9]*:[0-9]*\) .*/\1/p' "$PM" | sort > "$D/pm_refs.txt"; nu=$(sort -u "$D/pm_refs.txt" | wc -l)
sort "$PR/g3_today_members.txt" > "$D/recon_refs.txt"
echo "punct member file $PM: $np lines, $nu distinct refs, sha256 $(sha256sum < "$PM" | cut -d' ' -f1) (expect $XPUNCT, $XPUNCT)"
echo "ref set = PUNCT-RECON's today members (11/14, $(wc -l < "$D/recon_refs.txt") refs): $(cmp -s "$D/pm_refs.txt" "$D/recon_refs.txt" && echo yes || echo NO); only here $(comm -23 "$D/pm_refs.txt" "$D/recon_refs.txt" | wc -l), only in 11/14 $(comm -13 "$D/pm_refs.txt" "$D/recon_refs.txt" | wc -l) (expect 0, 0)"
[ "$np" = "$XPUNCT" ] && [ "$nu" = "$XPUNCT" ] && cmp -s "$D/pm_refs.txt" "$D/recon_refs.txt" || FL="$FL punct"
python3 scripts/audit_reassembly_diff.py "$B" --v2 --punct-members "$PM" --eligible "$EL" > "$D/self_diff.out" 2>&1; rs=$?
SL=$(sed -n '/^V2 MEMBER DIFF:/p' "$D/self_diff.out"); sed -n '/content-other members/,/^$/p' "$D/self_diff.out"
echo "built vs its own new member file: exit $rs (expect 1, content-other Job 3:3 as on 11/6 and 11/14)"; echo "  $SL"
echo "  = expected (every member unchanged, nothing gone or new): $([ "$SL" = "$XSELF" ] && echo yes || echo NO)"
[ "$rs" = 1 ] && [ "$SL" = "$XSELF" ] || FL="$FL self-diff"
st1=$(stat -c '%s %Y' "$B" "$DA/before.db" | tr '\n' ' ')
echo "built and the pre-9a copy: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO)"
[ "$st1" = "$st0" ] || { echo "STEP9C-FREEZE RESULT: STOP - built or the pre-9a copy changed during a read-only run - report this"; exit 1; }
if [ -z "$FL" ]; then
  echo "STEP9C-FREEZE RESULT: READ DONE - new frozen fill $NEW 4,411 rows (3,873 + 538), sha256 $NS = the 10/25 rows joined through the 9a report; punct members $XPUNCT ($PM, = PUNCT-RECON's); every file in $D for scp"; exit 0
fi
echo "STEP9C-FREEZE RESULT: CHECK -$FL (lines above; files in $D)"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9C-FREEZE reviewed (11/15) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - STEP9C-FREEZE is read-only on every database. It writes only to a new run folder plus its log, every gate wrapper item is present, no tripwire fires, and each figure traces to a ruling, to code or to a cited run receipt."
Every printed text the block matches traced by the reviewer to snapshot_surface_fill.py :170-171, :185, :222, :262, :401-402, :410 and audit_reassembly_diff.py :596-602.

### STEP9C-FREEZE ran (11/15, 15:15:02Z, PA HEAD 476de530, REF 88f7a5f6) — READ DONE, exit 0 (§9.131)
Log `~/edition_upgrade_runs/step9c_freeze_20261115.log`; folder `step9c_freeze_20261115/`. PRE OK; before.db ea6c54c3…, report
e154d8d4…, 10/25 fill d9435bde… = declared; CHECK OK (149 + schema 0; 395,014 / 219a3ebe7075). Re-freeze: G0 / O / R PASS, all six
chk lines yes; RECEIPT rows 4,411, 3,873 / 538, distinct 4,411, name slots 22, k2_count > 1 1,486, by class fill_pronoun 42 ·
fill_resolved 3,710 · fill_unlisted 32 · normalize 357 · split_keep 89 · split_receive 68 · split_receive_name 21 · split_trim 92.
**New frozen fill `abp_surface_fill_20261115.tsv`: 4,411 rows, 455,953 B, sha256
d025cc086cd7f325bafe3c89655c778f8cdc57f67ba127061a3edfd2192472ff.** Join: 4,411 / 4,411 / 4,411 / missing 0; must-equal columns 0;
moved 6; read-outs translit 0, old_form 0, old_translit 0, strongs_base 1, english 83, english_head 23, is_pn 0, k2_count 0.
Punct: tests + controls pass; by class 607 / 1 / 0 / 0; **`punct_members_built_20261115.txt` 607 lines / 607 refs, sha256
0cc4d4288f7a35576b40063b5f1e1b4ff9d21642cef80f4d7bcec02f6dfa7056**, = PUNCT-RECON's 11/14 set (0 / 0); self-diff exit 1, line =
expected (unchanged 607; content-other Job 3:3 "replace: rows[May the] -> text[Maythe]"). Built + pre-9a copy untouched.
**Ruling (11/15, §9.131):** both files accepted as CANDIDATES for the 9c pins, not declared; local copies must hash to these values
(+ report e154d8d4…) after scp; members read of strongs_base 1 / english 83 / english_head 23 before the declaration.
**Eligible-file sha (§9.131 (3)) — CC settles: no full sha needed in the record.** In this block the eligible file is only an
argument to the self-diff, where it is consulted only for NEW members (audit_reassembly_diff.py :542-543); the self-diff found 0 new,
so no eligibility value was read into any figure. The 8-character guard is the same as PUNCT-RECON's (:7369), where the file did
decide members.

## 9c inputs: local copies + members read (11/15, §9.131 ruling 2) — local, no PA run

**scp by JP (11/15)** of `step9c_freeze_20261115/` + `step9a_apply_20261115/key2_list.tsv` to the local staging folder
`C:\Users\JP\edition_upgrade_runs\pa\step9c_freeze_20261115\` (outside the repo). Local sha256, in full:
- `abp_surface_fill_20261115.tsv` d025cc086cd7f325bafe3c89655c778f8cdc57f67ba127061a3edfd2192472ff (4,412 lines) = PA's
- `punct_members_built_20261115.txt` 0cc4d4288f7a35576b40063b5f1e1b4ff9d21642cef80f4d7bcec02f6dfa7056 (607 lines) = PA's
- `report_apply.tsv` e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a (4,412 lines) = PA's
- `key2_list.tsv` d0967a0d7a725270bedd914e2760d79b6416d6b40ce38cf84165d3ca36f0dc5e (83 slots + header) = the §9.126 list
The 10/25 local copy `tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv` = d9435bde… (the pin).

**Members read** (a Python read of the four files: each new row joined to its 10/25 row through the report, new slot → old
slot, as the block's awk join; then each differing column listed; the key-2 list compared as a SET of old slots). Output verbatim:
```text
pairs joined: 4411; key-2 list rows: 83

=== strongs_base: 1 row(s) differ 10/25 -> new ===
  of these on the key-2 list (by old slot): 0; report detail 'key-2 alone (listed)': 0
  Jer 49:3 pos 3->3 [not-listed; agree-strong] insert/split_receive_name strongs * | strongs_base: [H5857] -> [*] | english [Ai] -> [Ai]

=== english: 83 row(s) differ 10/25 -> new ===
  of these on the key-2 list (by old slot): 83; report detail 'key-2 alone (listed)': 83
  Gen 4:8 pos 21->21 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 450 | english: [rose up] -> [that Cain rose up] | english_head [rose] -> [rose]
  Gen 5:16 pos 2->2 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2198 | english: [lived] -> [lived,] | english_head [lived] -> [lived]
  Gen 5:26 pos 1->2 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2198 | english: [lived] -> [lived,] | english_head [lived] -> [lived]
  Gen 31:55 pos 15->15 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 654 | english: [turned] -> [returned] | english_head [turned] -> [returned]
  Gen 41:8 pos 19->19 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 4680 | english: [wise men.] -> [wise ones.] | english_head [wise] -> [ones]
  Gen 41:34 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4160 | english: [let Pharaoh make] -> [let Pharaoh do this,] | english_head [make] -> [do]
  Gen 44:33 pos 18->18 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 80 | english: [his brothers.] -> [his brothers!] | english_head [brothers] -> [brothers]
  Gen 49:30 pos 12->12 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2932 | english: [acquired] -> [acquired —] | english_head [acquired] -> [acquired]
  Exo 16:16 pos 23->23 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 4633 | english: [your tents] -> [of your tents] | english_head [tents] -> [tents]
  Exo 23:18 pos 19->19 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 2378.2 | english: [my sacrifice,] -> [my sacrifice offering,] | english_head [sacrifice] -> [offering]
  Exo 30:8 pos 2->2 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_trim strongs 1821.1 | english: [should ignite] -> [should light up] | english_head [ignite] -> [light]
  Exo 32:26 pos 0->0 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2476 | english: [stood] -> [that Moses stood] | english_head [stood] -> [stood]
  Lev 3:17 pos 0->0 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3544.1 | english: [an] -> [as an] | english_head [\N] -> [\N]
  Lev 20:15 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] update/normalize strongs 2844.2 | english: [his laying with] -> [his laying] | english_head [laying] -> [laying]
  Num 12:1 pos 13->13 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2983 | english: [took] -> [took —] | english_head [took] -> [took]
  Num 16:25 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 450 | english: [rose up] -> [rose] | english_head [rose] -> [rose]
  Num 22:36 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2240 | english: [had came] -> [had come] | english_head [came] -> [come]
  Deu 12:12 pos 19->19 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 3816 | english: [manservants,] -> [menservants,] | english_head [manservants] -> [menservants]
  Deu 13:6 pos 53->53 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 3962 | english: [your fathers,] -> [your fathers;] | english_head [fathers] -> [fathers]
  Deu 28:62 pos 5->5 [K2-LIST; key-2 alone (listed) [key2-listed]] update/normalize strongs 446.2 | english: [for] -> [because] | english_head [\N] -> [because]
  Deu 31:28 pos 13->13 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 1122.3 | english: [judicial recorders!] -> [judicial recorders,] | english_head [recorders] -> [recorders]
  Deu 33:6 pos 0->0 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2198 | english: [Let Reuben live] -> [Let Reuben live,] | english_head [live] -> [live]
  Deu 33:7 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3778 | english: [this for] -> [to this] | english_head [\N] -> [\N]
  Jos 5:5 pos 30->30 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_unlisted strongs 390 | english: [paced] -> [turned] | english_head [paced] -> [turned]
  Jos 7:16 pos 5->5 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4317 | english: [he led] -> [led] | english_head [led] -> [led]
  Jos 12:23 pos 2->2 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/split_receive strongs 3588 | english: [of] -> [the one] | english_head [\N] -> [one]
  Jos 13:21 pos 20->20 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3960 | english: [struck] -> [struck —] | english_head [struck] -> [struck]
  Jos 17:1 pos 17->17 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/split_receive strongs 1063 | english: [For] -> [for] | english_head [\N] -> [\N]
  Jdg 6:6 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4433 | english: [became poor] -> [became poor —] | english_head [poor] -> [poor]
  1Sa 7:10 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_trim strongs 1510.7.3 | english: [was] -> [as Samuel was] | english_head [\N] -> [samuel]
  1Sa 13:6 pos 5->5 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/split_receive strongs 846 | english: [they] -> [it] | english_head [\N] -> [\N]
  1Sa 13:6 pos 6->6 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 4730.2 | english: [were in a strait] -> [was straitly to him,] | english_head [strait] -> [him]
  1Sa 14:35 pos 7->7 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 756 | english: [began] -> [first began] | english_head [began] -> [began]
  1Sa 20:27 pos 26->26 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3756 | english: [he has not] -> [has not come] | english_head [has] -> [come]
  1Sa 22:16 pos 6->6 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 599 | english: [should die] -> [should die —] | english_head [die] -> [die]
  2Sa 5:2 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_trim strongs 1510.6 | english: [was] -> [when Saul was] | english_head [\N] -> [saul]
  2Sa 5:10 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4198 | english: [went along] -> [went] | english_head [went] -> [went]
  2Sa 17:17 pos 22->22 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 935 | english: [to king] -> [king] | english_head [king] -> [king]
  2Sa 18:21 pos 12->12 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4352 | english: [did obeisance to] -> [did obeisance] | english_head [obeisance] -> [obeisance]
  1Ki 8:44 pos 25->25 [K2-LIST; key-2 alone (listed) [key2-listed]] update/normalize strongs 3739 | english: [which] -> [of which] | english_head [which] -> [which]
  1Ki 14:20 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 936 | english: [reigned] -> [reigned —] | english_head [reigned] -> [reigned]
  1Ki 17:17 pos 22->22 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3739 | english: [\N] -> [of which] | english_head [\N] -> [which]
  1Ki 21:15 pos 11->11 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2036 | english: [said] -> [that Jezebel said] | english_head [said] -> [said]
  1Ki 22:48 pos 11->11 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 5553 | english: [gold.] -> [gold;] | english_head [gold] -> [gold]
  1Ki 22:48 pos 14->14 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4198 | english: [go;] -> [\N] | english_head [go] -> [\N]
  1Ki 22:49 pos 17->17 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3756 | english: [did not] -> [wanted it not] | english_head [did] -> [wanted]
  1Ki 22:49 pos 18->18 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2309 | english: [want it] -> [\N] | english_head [want] -> [\N]
  1Ki 22:50 pos 17->17 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3962 | english: [his fore father.] -> [his forefather.] | english_head [father] -> [forefather]
  Ezr 9:5 pos 9->9 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 5014 | english: [humiliation,] -> [humiliation;] | english_head [humiliation] -> [humiliation]
  Job 15:30 pos 7->7 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3133 | english: [may] -> [May] | english_head [may] -> [may]
  Job 18:11 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3643.4 | english: [May] -> [may] | english_head [may] -> [may]
  Job 18:17 pos 3->3 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 622 | english: [May] -> [may] | english_head [may] -> [may]
  Job 20:10 pos 3->3 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3643.4 | english: [May] -> [may] | english_head [may] -> [may]
  Job 27:1 pos 2->2 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4369 | english: [proceeded] -> [proceeding] | english_head [proceeded] -> [proceeding]
  Job 32:21 pos 8->8 [K2-LIST; key-2 alone (listed) [key2-listed]] update/normalize strongs 3766.2 | english: [shall I in any way feel shame.] -> [in no way] | english_head [shame] -> [way]
  Job 32:21 pos 9->9 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 1788 | english: [\N] -> [shall I shame.] | english_head [\N] -> [shame]
  Psa 42:3 pos 5->5 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_pronoun strongs 3450 | english: [for me] -> [to me] | english_head [me] -> [me]
  Psa 48:0 pos 6->6 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4521 | english: [Sabbath.] -> [of Sabbath.] | english_head [sabbath] -> [sabbath]
  Psa 53:0 pos 5->5 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4907 | english: [contemplation;,] -> [contemplation;] | english_head [contemplation] -> [contemplation]
  Psa 71:0 pos 0->0 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3588 | english: [\N] -> [A psalm to] | english_head [\N] -> [psalm]
  Psa 92:0 pos 5->5 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3588 | english: [\N] -> [of the] | english_head [\N] -> [\N]
  Psa 108:7 pos 9->9 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 1266 | english: [I shall divide Shechem into parts;] -> [I shall divide Shechem into parts,] | english_head [parts] -> [parts]
  Psa 147:1 pos 9->9 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2237.1 | english: [may] -> [May] | english_head [may] -> [may]
  Isa 15:2 pos 3->3 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 622 | english: [for] -> [For] | english_head [\N] -> [\N]
  Isa 19:13 pos 10->10 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4105 | english: [they shall cause Egypt to wander] -> [they shall cause Egypt to wander,] | english_head [wander] -> [wander]
  Isa 30:31 pos 5->5 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2274 | english: [shall be vanquished,] -> [shall be vanquished] | english_head [vanquished] -> [vanquished]
  Isa 47:13 pos 19->19 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 312 | english: [let] -> [Let] | english_head [let] -> [let]
  Jer 20:1 pos 2->2 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 191 | english: [heard] -> [heard,] | english_head [heard] -> [heard]
  Jer 26:21 pos 19->19 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 191 | english: [heard] -> [heard,] | english_head [heard] -> [heard]
  Jer 37:12 pos 0->0 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 1831 | english: [came forth] -> [that Jeremiah came forth] | english_head [forth] -> [forth]
  Jer 46:14 pos 23->23 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 4665.3 | english: [your yew tree.] -> [your yew tree!] | english_head [tree] -> [tree]
  Jer 48:18 pos 11->11 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_trim strongs 3643.4 | english: [is destroyed] -> [is destroyed —] | english_head [destroyed] -> [destroyed]
  Jer 48:20 pos 12->12 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/split_receive_name strongs * | english: [Moab] -> [Moab,] | english_head [moab] -> [moab]
  Jer 49:3 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 3643.4 | english: [was destroyed.] -> [was destroyed!] | english_head [destroyed] -> [destroyed]
  Jer 50:16 pos 11->11 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3162 | english: [sword.] -> [sword!] | english_head [sword] -> [sword]
  Lam 5:15 pos 8->8 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 5525 | english: [our dance.] -> [our dance;] | english_head [dance] -> [dance]
  Eze 16:10 pos 9->9 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2224 | english: [I tied] -> [tied] | english_head [tied] -> [tied]
  Mic 2:12 pos 0->0 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4863 | english: [In being gathered] -> [In being gathered,] | english_head [gathered] -> [gathered]
  1Co 4:8 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4147 | english: [Are you] -> [are you] | english_head [\N] -> [\N]
  1Co 14:26 pos 21->21 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 1096 | english: [let] -> [Let] | english_head [let] -> [let]
  Act 14:2 pos 3->3 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 544 | english: [having resisted persuasion,] -> [resisting persuasion,] | english_head [persuasion] -> [persuasion]
  Heb 12:9 pos 14->14 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 5293 | english: [shall we] -> [Shall we] | english_head [shall] -> [shall]
  Luk 9:15 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 347 | english: [they laid them] -> [laid them] | english_head [them] -> [them]
  SET COMPARE english-diff old slots vs key-2 list old slots: same set True; diff-only 0; key2-only 0

=== english_head: 23 row(s) differ 10/25 -> new ===
  of these on the key-2 list (by old slot): 23; report detail 'key-2 alone (listed)': 23
  Gen 31:55 pos 15->15 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 654 | english_head: [turned] -> [returned] | english [turned] -> [returned]
  Gen 41:8 pos 19->19 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 4680 | english_head: [wise] -> [ones] | english [wise men.] -> [wise ones.]
  Gen 41:34 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4160 | english_head: [make] -> [do] | english [let Pharaoh make] -> [let Pharaoh do this,]
  Exo 23:18 pos 19->19 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 2378.2 | english_head: [sacrifice] -> [offering] | english [my sacrifice,] -> [my sacrifice offering,]
  Exo 30:8 pos 2->2 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_trim strongs 1821.1 | english_head: [ignite] -> [light] | english [should ignite] -> [should light up]
  Num 22:36 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2240 | english_head: [came] -> [come] | english [had came] -> [had come]
  Deu 12:12 pos 19->19 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 3816 | english_head: [manservants] -> [menservants] | english [manservants,] -> [menservants,]
  Deu 28:62 pos 5->5 [K2-LIST; key-2 alone (listed) [key2-listed]] update/normalize strongs 446.2 | english_head: [\N] -> [because] | english [for] -> [because]
  Jos 5:5 pos 30->30 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_unlisted strongs 390 | english_head: [paced] -> [turned] | english [paced] -> [turned]
  Jos 12:23 pos 2->2 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/split_receive strongs 3588 | english_head: [\N] -> [one] | english [of] -> [the one]
  1Sa 7:10 pos 1->1 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_trim strongs 1510.7.3 | english_head: [\N] -> [samuel] | english [was] -> [as Samuel was]
  1Sa 13:6 pos 6->6 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_keep strongs 4730.2 | english_head: [strait] -> [him] | english [were in a strait] -> [was straitly to him,]
  1Sa 20:27 pos 26->26 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3756 | english_head: [has] -> [come] | english [he has not] -> [has not come]
  2Sa 5:2 pos 4->4 [K2-LIST; key-2 alone (listed) [key2-listed]] update/split_trim strongs 1510.6 | english_head: [\N] -> [saul] | english [was] -> [when Saul was]
  1Ki 17:17 pos 22->22 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3739 | english_head: [\N] -> [which] | english [\N] -> [of which]
  1Ki 22:48 pos 14->14 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4198 | english_head: [go] -> [\N] | english [go;] -> [\N]
  1Ki 22:49 pos 17->17 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3756 | english_head: [did] -> [wanted] | english [did not] -> [wanted it not]
  1Ki 22:49 pos 18->18 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 2309 | english_head: [want] -> [\N] | english [want it] -> [\N]
  1Ki 22:50 pos 17->17 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3962 | english_head: [father] -> [forefather] | english [his fore father.] -> [his forefather.]
  Job 27:1 pos 2->2 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 4369 | english_head: [proceeded] -> [proceeding] | english [proceeded] -> [proceeding]
  Job 32:21 pos 8->8 [K2-LIST; key-2 alone (listed) [key2-listed]] update/normalize strongs 3766.2 | english_head: [shame] -> [way] | english [shall I in any way feel shame.] -> [in no way]
  Job 32:21 pos 9->9 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 1788 | english_head: [\N] -> [shame] | english [\N] -> [shall I shame.]
  Psa 71:0 pos 0->0 [K2-LIST; key-2 alone (listed) [key2-listed]] insert/fill_resolved strongs 3588 | english_head: [\N] -> [psalm] | english [\N] -> [A psalm to]

=== strongs_base member, both rows in full ===
  10/25: verse_id=20266 | book=Jer | chapter=49 | verse=3 | position=3 | action=insert | cls=split_receive_name | form=Γαϊ | translit=Gai | old_form=\N | old_translit=\N | strongs=* | strongs_base=H5857 | english=Ai | english_head=ai | is_pn=1 | k2_ordinal=1 | k2_count=4
  new  : verse_id=20266 | book=Jer | chapter=49 | verse=3 | position=3 | action=insert | cls=split_receive_name | form=Γαϊ | translit=Gai | old_form=\N | old_translit=\N | strongs=* | strongs_base=* | english=Ai | english_head=ai | is_pn=1 | k2_ordinal=1 | k2_count=4
```
Read, no cause asserted (§9.131): **english 83 = exactly the key-2 list's 83 slots** (set compare by old slot: same set, 0 / 0;
all 83 carry report detail "key-2 alone (listed)"). **english_head 23: all inside those 83.** **strongs_base 1: Jer 49:3 @3 "Ai"**
(name slot, strongs `*`, insert / split_receive_name, agree-strong, NOT on the key-2 list): 10/25 strongs_base H5857, new `*`;
every other column equal. Pointer only, not read: Jer 49:3 is one of the six none → lemma-only verses in §9.95's 8b.2 drift list.

## Jer 49:3 @3 strongs_base (§9.132 ruling 6) — read (b) from the code; read (a) needs PA (JER493-READ drafted)

**(b) Where the fill file's strongs_base column comes from, and what reads it (code at 88f7a5f6 = HEAD for scripts/tests):**
- **Source at freeze time:** the `--src` database's `words.strongs_base` at the slot. `word_rows()` reads `SELECT verse_id,
  position, strongs, strongs_base, english, english_head, is_pn FROM words` (snapshot_surface_fill.py:127-137); `build_rows()`
  takes the slot's one row (:207) and writes `strongs_base=sb` into the frozen row (:214-218). So the 10/25 file holds live's
  words value on 10/25 (its `--src` was a fresh copy of live), and the new file holds built's words value after 9a.
- **What reads it afterwards:**
  - `restore_surface_fill.py`: NO. `load_snapshot()` checks sha / counts / form / old_form only (:145-160); the re-key uses the
    row's `strongs`, `k2_ordinal`, `english` (:204-205), the preconditions use `form` / `old_form` / `action` (:223-231), the
    Lexicon check uses `cls`, `form` and the NEW words row's `strongs` from the database (:233-236; `dr.words_for` reads
    `strongs`, not `strongs_base`, dryrun_rekey_fill.py:132-141). The restore's two `strongs_base` reads (:168, :181) are the
    DATABASE's words column joined to `lexicon` for the translit lemma — not the snapshot column.
  - `dryrun_rekey_fill.py`: NO (no `strongs_base` in the file).
  - `snapshot_surface_fill.py --check` (rebuild-words step 1a): YES, as part of the whole-row, byte-for-byte compare —
    `check_current()` re-derives every row from `--src` (so from that database's `words.strongs_base` at the slot) and
    requires the render to equal the frozen file's bytes (:313-321); a difference is reported per slot by `stale_slots()`,
    which compares every column (:232-246). So after the swap, step 1a's `--check` on a fresh copy of live passes only if
    live's `words.strongs_base` at Jer 49:3 @3 is `*`, as frozen.
  - Tests: `tests/test_surface_fill_restore.py` builds made-up `words` tables with the column (:62, :67); no test reads the
    snapshot's `strongs_base` value on its own — only inside the whole-file re-freeze / `--check` byte compares.
- So the column is a record of the slot's word as it stood ("the OLD words row", docstring :14-15), read back only by the
  byte-for-byte `--check`; nothing places or writes by it.

**(a) What §9.95's drift list records for Jer 49:3 — cannot be answered from the repo.** The repo holds the list at verse level
only: DESIGN :500 (§9.95) and DRAFT :2781-2786 — "none→lemma-only 6 = Num 21:25, 1Sa 20:37, 2Sa 15:6, Jer 48:15, Jer 48:20,
Jer 49:3; all with a Hebrew number". No slot, column or values. The DRIFT-8B2 block text was not appended to this record
(handoff stageD_rekey :74-79: the 8B2 block lived in the 11/6 chat), and the drift log was not pasted into the repo. The read
that answers it is JER493-READ below: every line naming Jer 49:3 / verse id 20266 in `drift8b2_20261106.log` (+ its folder),
the 8b.2 apply run's log and folders (`xref8b2c_*`) and `~/rekey/live_8b3_id.log`; and the Jer 49:3 rows of words,
pn_greek_identity and pn_hebrew_xref on src, the pre-8b rollback copy and built. No cause asserted.

### Block JER493-READ (GATE REF 88f7a5f6; READ-ONLY — writes only its run folder and log; no figure gated)
Local test (WSL, fake HOME, clone at 08d15be7, three made-up dbs + a fake drift log): READ DONE exit 0; missing logs print "not present (or not a file)"; re-paste STOP.
```bash
set +H
L=~/edition_upgrade_runs/jer493_read_20261115.log
if [ -e "$L" ]; then echo "JER493-READ RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=88f7a5f6
echo "GATE REF ${REF} - JER493-READ sec 9.131 follow-up (a): Jer 49:3 in the sec 9.95 drift / 8b.2 logs, and its name-slot rows (words, pn_greek_identity, pn_hebrew_xref) on src, the pre-8b rollback copy and built - READ-ONLY - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "JER493-READ RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
P8=~/bible-db/bible_edupg_test_built_pre_8b_20261106.db
O=~/edition_upgrade_runs
D=$O/jer493_read_20261115
python3 scripts/eu_step.py pre --tag JER493 --ref "$REF" --dir "$D" --db "$S" --db "$P8" --db "$B" || { echo "JER493-READ RESULT: STOP - pre (line above); nothing read"; exit 1; }
st0=$(stat -c '%s %Y' "$S" "$P8" "$B" | tr '\n' ' ')
echo "=== 1. the logs: every line naming Jer 49:3 or verse id 20266 (file: line number: text) ==="
for f in "$O/drift8b2_20261106.log" "$O"/drift8b2_20261106/* "$O/xref8b2c_20261106.log" "$O"/xref8b2c_dry_20261106/* "$O"/xref8b2c_apply_20261106/* ~/rekey/live_8b3_id.log; do
  if [ -f "$f" ]; then n=$(grep -cE 'Jer 49:3([^0-9]|$)|(^|[^0-9])20266([^0-9]|$)' "$f"); echo "--- $f: $n line(s)"; grep -nE 'Jer 49:3([^0-9]|$)|(^|[^0-9])20266([^0-9]|$)' "$f" | cut -c1-400 | sed 's/^/    /'; else echo "--- $f: not present (or not a file)"; fi
done
echo "=== 2. Jer 49:3 on each copy (verse id, then every word row; identity + xref rows of that verse) ==="
for db in "$S" "$P8" "$B"; do
  echo "--- $db"
  v=$(sqlite3 -readonly "$db" "SELECT id FROM verses WHERE book='Jer' AND chapter=49 AND verse=3"); echo "  verse id: $v (the two frozen fill files: 20266)"
  [ -n "$v" ] || { echo "JER493-READ RESULT: STOP - no Jer 49:3 row on $db"; exit 1; }
  echo "  words (position | strongs | strongs_base | english | is_pn):"
  sqlite3 -readonly -separator ' | ' "$db" "SELECT position, quote(strongs), quote(strongs_base), quote(english), quote(is_pn) FROM words WHERE verse_id=$v ORDER BY position" | sed 's/^/    /'
  echo "  pn_greek_identity (position | greek_strongs | greek_lemma | source | hebrew_base):"
  sqlite3 -readonly -separator ' | ' "$db" "SELECT position, quote(greek_strongs), quote(greek_lemma), quote(source), quote(hebrew_base) FROM pn_greek_identity WHERE verse_id=$v ORDER BY position" | sed 's/^/    /'
  echo "  pn_hebrew_xref (position | hebrew_base | class):"
  sqlite3 -readonly -separator ' | ' "$db" "SELECT position, quote(hebrew_base), quote(class) FROM pn_hebrew_xref WHERE verse_id=$v ORDER BY position" | sed 's/^/    /'
done
st1=$(stat -c '%s %Y' "$S" "$P8" "$B" | tr '\n' ' ')
echo "src, pre-8b copy and built: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO)"
[ "$st1" = "$st0" ] || { echo "JER493-READ RESULT: STOP - a database changed during a read-only run - report this"; exit 1; }
echo "JER493-READ RESULT: READ DONE - lines and rows above (no figure gated; a read for the ruling chat)"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### JER493-READ reviewed (11/15) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - read-only block. The gate checks run inside `eu_step.py pre`, the only things written are a new run folder and a new log (neither may already exist), and no figure is gated."
Reviewer notes (not stops): a copy lacking one of the two name tables prints an sqlite error line and the block carries on (reads as "table absent"); the grep pipelines return non-zero on no match, but nothing tests that.

### JER493-READ ran (11/15, 16:17:21Z, PA HEAD 476de530, REF 88f7a5f6) — READ DONE, exit 0
Log `~/edition_upgrade_runs/jer493_read_20261115.log`. PRE OK; src / pre-8b copy / built untouched (size + time).
**Logs, verbatim (column names not printed in the matched lines):**
- `drift8b2_20261106.log` :25 and :50 — `Jer 49:3|20266|3|lemma-only|none|'H5857'|'H5857'|'Ai'|'H5857'|'*'`; :71 —
  `Jer 49:3|20266|3|none|lemma-only|'H5857'|'H5857'`.
- `drift8b2_20261106/folded_differ_bible_edupg_test_20261101.tsv` :6 and `…_built_20261102.tsv` :6 — the same line as :25.
- `xref8b2c_20261106.log`, `xref8b2c_dry_20261106/dry_run_full.log`, `xref8b2c_apply_20261106/apply_full.log`,
  `~/rekey/live_8b3_id.log`: 0 lines. `greek_rows_before.tsv` / `greek_rows_after.tsv` :16902 `20266|2036|'G2036'` — that file
  is keyed by words rowid, so 20266 there is a rowid, not this verse (a false match of the pattern).
**Jer 49:3 (verse id 20266 on all three copies), slot @3 "Ai" (strongs `*`, is_pn 1):**
| copy | words.strongs_base @3 | pn_greek_identity @3 (source, hebrew_base) | pn_hebrew_xref @3 (hebrew_base, class) |
|---|---|---|---|
| src | H5857 | lemma-only, H5857 | H5857, **none** |
| pre-8b copy | H5857 | lemma-only, H5857 | H5857, **none** |
| built | **`*`** | lemma-only, H5857 | H5857, **lemma-only** |
The verse's other name slots: @1 Heshbon (identity surface), @7 Rabbah, @14 Milcom (lemma-only) — xref lemma-only on all three
copies; words strongs_base `*` on src and built, the Hebrew number on the pre-8b copy.
**Answer to §9.132 (a):** yes, @3 is in §9.95's drift list — :71 records slot 3 with `none` → `lemma-only` (the class) and
H5857 / H5857. **CC's reading, from the rows and the code, offered for the ruling — not a finding:** retire_hebrew_identity.py's
rule is `lemma-only` → words.strongs_base `*`, `none` → Hebrew kept (docstring :12-16). On src (live as of 11/01) the slot's
xref class is `none` and words keeps H5857, while its identity row says lemma-only; on built the xref class is `lemma-only` and
words is `*`. That is the §9.95 picture (10/25: 8b.2 ran before 8b.3 rebuilt the identity table; the lane's 8B2c ran after, with
the six none → lemma-only rows in its 26,323), and the frozen files record each copy's words value as it stood: 10/25 H5857,
new `*`.

## 9c code change (11/15, CC; on the §9.133 pins) — in the working tree, NOT committed until ruled

**What changes (6 files + 2 new):**
- `scripts/restore_surface_fill.py` — `SNAPSHOT_SHA256` d9435bde… → **d025cc086cd7f325bafe3c89655c778f8cdc57f67ba127061a3edfd2192472ff**
  (STEP9C-FREEZE log, RECEIPT "sha256" line; §9.133); new **`REPORT_SHA256` = e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a**
  (R1; STEP9A-APPLY log, apply report sha, §9.128; = the STEP9A-DRY2 report, :8930; §9.133); defaults `ROWS_BASE, ROWS_AFTER`
  391,130 / 395,003 → **391,141 / 395,014** (§9.122 base; §9.128 after-count; §9.133 "default base 391,141");
  `N_ROWS / N_INSERT / N_UPDATE` stay 4,411 / 3,873 / 538 — the new file's own counts (STEP9C-FREEZE RECEIPT). Comment block
  cites the old pin and the 10/25 base/after; docstring G1a / G1 / usage lines updated.
- `scripts/snapshot_surface_fill.py` — `pinned_report()` reads `REPORT_SHA256`; `report_pin(required=True)` (the `--check` path)
  now also STOPs unless the report = that pin ("is not the pinned report"), after the existing beside-file `.sha256` check; a
  re-freeze (`required=False`) is unchanged. Docstring: the 9c usage + the R1 sentence under `--check`.
- `tests/test_surface_fill_restore.py` (47 → 51): setUp/tearDown also save and blank `REPORT_SHA256`; `AfterCount`: the F1 ruled
  test keeps 391,130 → 395,003 explicitly (the 10/25 shapes, §9.120 (d)); new `test_defaults_are_the_9c_pins` (391,141 / 395,014 /
  4,411 and both shas); new `PinnedFiles` (2 tests: the local git-ignored snapshot and report each hash to their pin + their
  `.sha256`; SKIP where the files are absent, i.e. CI); new `Refreeze.test_check_requires_the_report_pinned_in_code` (report =
  pin → CURRENT; beside-file `.sha256` right but code pin wrong → STALE "is not the pinned report").
- `tests/test_reassembly_member_diff.py` (9 → 10): the real-file test reads both member files (241 and 607; Gen 2:19 ops the same);
  new `test_frozen_files_match_their_sha256`.
- NEW `tests/fixtures/reassembly/punct_members_built_20261115.txt` (607 lines, sha 0cc4d428…, = the STEP9C-FREEZE file, local copy
  checked) + `.sha256`. The 10/30 file (241) stays.
- `.claude/commands/rebuild-words.md` — 1a command: `--check --src <src> --prefill ~/abp_surface_prefill_20261115.db --from-restore
  tests/fixtures/rebuild_trap/restore_report_20261115.tsv --out tests/fixtures/rebuild_trap/abp_surface_fill_20261115.tsv` + the
  pre-swap STALE note (Jer 49:3 @3) + the 10/25 command kept for the record; 9a command: new snapshot + the same `--prefill`, the
  re-pin (base 391,141, G1 395,014) said to describe live only after the swap, the 10/25 split figures labelled as 10/25 ones.
- `tests/fixtures/rebuild_trap/README.md` — the three files and two pins.
- Local only (git-ignored, not in the diff): `tests/fixtures/rebuild_trap/abp_surface_fill_20261115.tsv` (+ `.sha256`, as made on PA)
  and `restore_report_20261115.tsv` (+ `.sha256`, written by CC: "e154d8d4…  restore_report_20261115.tsv"); `sha256sum -c` OK on
  both; the 10/25 pair untouched.
**Tests:** the two files above 51 + 10 OK; all 78 pre-commit test files pass on the working tree (both files already on the
ci.yml + pre-commit lists). **Proven able to fail:** code-pin compare removed → the R1 test fails; SNAPSHOT_SHA256 changed by one
character → `test_defaults_are_the_9c_pins` + `test_snapshot_file_is_the_pin` fail; one line appended to the new punct file →
the round-trip and sha tests fail. All restored; working tree as described.

**Items for the ruling (not decided in the change):**
- **(i) "committed beside the frozen file" (handoff item 2, R1 §9.121) cannot be done as worded.** `.gitignore:44-47`: "# Rebuild-trap
  frozen fill snapshot (snapshot_surface_fill.py): ABP printed Greek + ABP English, / # ABP text, never in the public repo. PA keeps
  it here; a second copy sits in the local checkout. / tests/fixtures/rebuild_trap/*.tsv / tests/fixtures/rebuild_trap/*.sha256".
  The 10/25 file's handling (README, before this change): "Both files are git-ignored on purpose … PA keeps the working copy in this
  folder of `~/bible-db`; a second copy sits in the same folder of the local checkout (scp)." The report holds the same ABP text
  (forms) as the snapshot. **Proposed:** R1 is met by the code pin (`REPORT_SHA256`, checked by `--check`); the report and the new
  snapshot sit beside each other in the fixture folder on PA and locally, git-ignored, exactly as the 10/25 file. PA's copies are
  placed by a later block (a write to PA's checkout folder → ruling chat).
- **(ii) Between this commit and the swap, live does not match the pins.** Step 1a's new `--check` on a copy of live reads STALE
  (live is the 10/25 layout); 9a's new defaults (base 391,141) do not fit a rebuild of live. Read (b), §9.132: after the swap,
  step 1a's `--check` expects `*` at Jer 49:3 @3 on live (built's value; live today H5857). **Proposed:** accept; no rebuild of
  live runs before the swap; rebuild-words 1a/9a say so (done in this change).
- **(iii) The standing home of the pre-9a copy** (1a's and 9a's `--prefill`). Today `~/edition_upgrade_runs/step9a_apply_20261115/
  before.db` (sha ea6c54c3…, 18,194,432 B, abp_surface only — enough: `--check` reads only abp_surface from the pre-fill side,
  snapshot_surface_fill.py g0_report :152; the restore's G1b compares abp_surface only, restore_surface_fill.py table_diff :281-291). **Proposed:** a copy at
  `~/abp_surface_prefill_20261115.db` (the name rebuild-words now uses), sha-checked = ea6c54c3…, kept like
  `~/bible.db.pre-surface-fill-20261025`; the run-folder original also stays. Made by the same later PA block as (i).
- **(iv) The punct member files.** The new 607 file is added beside the 10/30 file (kept; both tested). DESIGN §6 gate table row 3
  still names the 10/30 file — a design record, not edited; the next gate-3 run names its file in its own block.
- **Not in this change (by ruling):** the health floor 395,003 (swap commit, §9.120 / charter §7); rebuild-words step 9's
  "391,130" and 9b's floor text (swap commit, with the floor); `dryrun_rekey_fill` constants (keep the 10/25 figures, §9.120 F3);
  `apply_abp_surface_fill.py` (one-shot, untouched).
**After the ruling:** one scripts/tests/docs commit = new code REF; then (1) a PA write block for (i)+(iii) (placing the snapshot,
report and pre-fill copy, each sha-checked) → ruling chat; (2) the `--check` run on built under the new REF as its own read-only
block: `--check --src <built> --prefill <the pre-9a copy> --from-restore <report> --out <new snapshot>` → expect SNAPSHOT CURRENT.

### 9c code change reviewed (11/15) — REVIEW: ESCALATE (code change, §9.90); no defect; three gaps → for the ruling
Verdict line verbatim: "REVIEW: ESCALATE - this is a code change (scripts, tests, fixtures, rebuild-words.md), which is a write under the scope rules and DESIGN §9.90, so it goes to the ruling chat. I found no defect in how it works."
Confirmed by the reviewer: constants = the §9.133 declaration; the R1 check runs only under `--check` (`check_current` is the only
`required=True` caller) and AFTER the beside-file `.sha256` check, so a matching `.sha256` cannot get past it (test :654-671);
the F1 ruled test keeps 391,130 → 395,003 by hand; floor tests still 395,003 (swap commit); `PinnedFiles` skips only when the
.tsv is absent; items (i) / (iii) accurate against `.gitignore:44-47`, g0_report :152, table_diff :281-291.
- **Finding 3 (GAP, for a ruling):** `--check --csv …` never reaches the R1 report check (it runs only with `--from-restore`).
  Under the new pin a `--csv` check should still stop at the byte compare (reviewer's reading, untested). **CC recommends:** make
  `--check` require `--from-restore` whenever `REPORT_SHA256` is set (one guard + one test) — not done until ruled.
- **Finding 8 (GAP, for a ruling):** rebuild-words 1a / 9a name `~/abp_surface_prefill_20261115.db`, which exists only once
  item (iii)'s PA block runs; the commands fail until then (no rebuild of live runs before the swap, item (ii)). The pre-9a copy's
  figures there now cite DESIGN 9.128 (added after review). **CC recommends:** the doc lands with this commit; the (i)+(iii) PA
  block follows it, before any `--check` run.
- **Finding 9 (GAP, minor):** the restore docstring's usage line now has a placeholder `--prefill <the pre-fill copy,
  rebuild-words 9a>`, not a pasteable path. **CC:** left as is; it points to the one place the path is kept.
- Notes: `.sha256` file name inside not checked by `PinnedFiles` (first field only); `REPORT_SHA256 = None` means "no pin" as for
  the snapshot (set in shipped code; only tests blank it).

### Rulings (11/15, §9.134) — 9c code APPROVED; finding-3 guard added; committed `19e2fb25` = new code REF
- **Finding-3 guard (adopted):** `snapshot_surface_fill.py` run(): under `--check`, no `--from-restore` while `REPORT_SHA256` is set →
  STOP "--check needs --from-restore …"; test `SnapshotCheck.test_check_with_csv_refused_once_a_report_is_pinned` (restore tests
  51 → 52). Proven able to fail: guard replaced by `if False:` → that test fails; restored → OK. All 78 pre-commit test files pass.
- rebuild-words 1a now names the ruled home `~/abp_surface_prefill_20261115.db` (§9.134 (iii)) and the `--csv` refusal.
- **Reviewer on the delta only:** "REVIEW: ESCALATE - no defect: the 9.134 delta (one guard, one test, the rebuild-words 1a sentence) does what was ruled. ESCALATE only because CLEAR is not available for a code change."
  (Guard cannot block `--from-restore --check` or a re-freeze; other `--csv --check` tests unaffected — setUp blanks the pin.)
- **Punct file content (§9.134 "raised"):** the same kind as the committed 10/30 file — every line parses as a `punct-position`
  member line (`[punct-position] <ref> <ops>`; 607 / 607 parsed, 10/30: 241 / 241), one class only, op kinds delete / insert /
  replace in both, each op naming short English word fragments of the verse (`rows[…] -> text[…]`); longest line 207 chars
  (10/30: 164); 55,412 B (10/30: 22,580 B). Same recipe (`--v2 --list`, charter :555).
- **Committed `19e2fb25`** (pre-commit all checks passed). scripts/ + tests/ differ from 88f7a5f6 by restore_surface_fill.py,
  snapshot_surface_fill.py, test_surface_fill_restore.py, test_reassembly_member_diff.py and the new punct fixture pair (+
  rebuild-words.md and the fixture README outside scripts/tests).

## STEP9C-PLACE drafted (11/15, GATE REF 19e2fb25; PA must pull first) — §9.134 (b): items (i) + (iii) on PA

WRITES 5 new files outside a run folder, overwrites nothing, writes no database: the pinned snapshot (from the STEP9C-FREEZE
run folder) and the ORIGINAL 9a report into the checkout's git-ignored `tests/fixtures/rebuild_trap/` as
`abp_surface_fill_20261115.tsv` / `restore_report_20261115.tsv`, each + a `.sha256` written as "<sha>  <name>"; and
`step9a_apply_20261115/before.db` copied to `~/abp_surface_prefill_20261115.db` (original stays). **Before any write (STOP):**
pre (REF 19e2fb25; `--keep` the three sources); no target and no journal beside the prefill target exists; each source = its
pin (d025cc08…, e154d8d4…, ea6c54c3…); the checkout's restore_surface_fill.py carries both pins; the 10/25 file = d9435bde…; all
four fixture targets git-ignored (`git check-ignore`). **Writes:** `cp -n` / `mv -n`. **After (CHECK):** each placed file's sha =
its pin; `sha256sum -c` on both new pairs + the 10/25 pair; prefill 391,141 rows (read-only); no .tmp left; sources + 10/25 file
size/time unchanged; checkout `git status --porcelain --untracked-files=no -- tests scripts` clean.
Figure sources: XS / XR §9.133 and restore_surface_fill.py :81 / :85 at 19e2fb25; XB4 + 391,141 §9.128 (full sha in the entry);
XOLD the old pin, CHARTER_rebuild_trap_fix.md §8 receipt and the comment in restore_surface_fill.py.
Local test (WSL, fake HOME, clone at 4a99657e; the REAL local snapshot + report as sources, a made-up 391,141-row before.db with
its sha swapped in): clean DONE exit 0; re-paste STOP; targets present → "never overwritten" STOP; a source report changed →
STOP before any write; after the fix, a clean run with PA's three untracked scripts/ files present → DONE exit 0.

### Block STEP9C-PLACE (GATE REF 19e2fb25; WRITES 5 new files — for the ruling chat)
```bash
set +H
L=~/edition_upgrade_runs/step9c_place_20261115.log
if [ -e "$L" ]; then echo "STEP9C-PLACE RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=19e2fb25
echo "GATE REF ${REF} - STEP9C-PLACE DESIGN 9.134 items (i) + (iii): copy the pinned 9c snapshot + the 9a report into the checkout's git-ignored fixture folder, and the pre-9a copy to ~/abp_surface_prefill_20261115.db - WRITES 5 new files, overwrites nothing, no database written - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9C-PLACE RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export LC_ALL=C
O=~/edition_upgrade_runs
DA=$O/step9a_apply_20261115
DF=$O/step9c_freeze_20261115
D=$O/step9c_place_20261115
FX=tests/fixtures/rebuild_trap
XS=d025cc086cd7f325bafe3c89655c778f8cdc57f67ba127061a3edfd2192472ff
XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a
XB4=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273
XOLD=d9435bdea8f3ec768053dbefb8c19a920905ed616bdfcb3b2a5f55cf9b4a295b
# sources and targets (source -> target); the two .sha256 files are made, not copied (see below)
SNAP_S="$DF/abp_surface_fill_20261115.tsv"; SNAP_T="$FX/abp_surface_fill_20261115.tsv"
REP_S="$DA/report_apply.tsv";               REP_T="$FX/restore_report_20261115.tsv"
PRE_S="$DA/before.db";                       PRE_T=~/abp_surface_prefill_20261115.db
sh1() { sha256sum < "$1" | cut -d' ' -f1; }
# --- before any write: every miss is STOP, nothing written ---
python3 scripts/eu_step.py pre --tag PLACE --ref "$REF" --dir "$D" --keep "$PRE_S" --keep "$SNAP_S" --keep "$REP_S" || { echo "STEP9C-PLACE RESULT: STOP - pre (line above); nothing written"; exit 1; }
for t in "$SNAP_T" "$SNAP_T.sha256" "$REP_T" "$REP_T.sha256" "$PRE_T" "$PRE_T-journal"; do [ -e "$t" ] && { echo "STEP9C-PLACE RESULT: STOP - target already exists, never overwritten: $t"; exit 1; }; done
echo "targets: none exists yet (5 files + no journal beside the pre-fill target)"
s=$(sh1 "$SNAP_S"); echo "source snapshot $SNAP_S: sha256 $s (expect $XS = SNAPSHOT_SHA256)"; [ "$s" = "$XS" ] || { echo "STEP9C-PLACE RESULT: STOP - source snapshot is not the pinned one; nothing written"; exit 1; }
s=$(sh1 "$REP_S"); echo "source report $REP_S: sha256 $s (expect $XR = REPORT_SHA256)"; [ "$s" = "$XR" ] || { echo "STEP9C-PLACE RESULT: STOP - source report is not the pinned one; nothing written"; exit 1; }
s=$(sh1 "$PRE_S"); echo "source pre-9a copy $PRE_S: sha256 $s (expect $XB4)"; [ "$s" = "$XB4" ] || { echo "STEP9C-PLACE RESULT: STOP - source pre-9a copy is not the recorded one; nothing written"; exit 1; }
grep -q "SNAPSHOT_SHA256 = \"$XS\"" scripts/restore_surface_fill.py && grep -q "REPORT_SHA256 = \"$XR\"" scripts/restore_surface_fill.py || { echo "STEP9C-PLACE RESULT: STOP - the checkout's restore_surface_fill.py does not carry the two pins; nothing written"; exit 1; }
echo "restore_surface_fill.py at $REF carries SNAPSHOT_SHA256 = $XS and REPORT_SHA256 = $XR"
s=$(sh1 "$FX/abp_surface_fill_20261025.tsv"); echo "10/25 frozen fill (kept, charter sec 7): sha256 $s (expect $XOLD)"; [ "$s" = "$XOLD" ] || { echo "STEP9C-PLACE RESULT: STOP - the 10/25 file is not the one recorded; nothing written"; exit 1; }
for t in "$SNAP_T" "$SNAP_T.sha256" "$REP_T" "$REP_T.sha256"; do git check-ignore -q "$t" || { echo "STEP9C-PLACE RESULT: STOP - $t would NOT be git-ignored; nothing written"; exit 1; }; done
echo "all four fixture targets are git-ignored (.gitignore:46-47)"
st0=$(stat -c '%s %Y' "$SNAP_S" "$REP_S" "$PRE_S" "$FX/abp_surface_fill_20261025.tsv" | tr '\n' ' ')
# --- the writes: copy, never overwrite (cp -n); each placed file sha-checked; every miss after this point is CHECK ---
FL=""
cp -n "$SNAP_S" "$SNAP_T" || FL="$FL cp-snapshot"
printf '%s  abp_surface_fill_20261115.tsv\n' "$XS" > "$SNAP_T.sha256.tmp" && mv -n "$SNAP_T.sha256.tmp" "$SNAP_T.sha256" || FL="$FL snapshot-sha-file"
cp -n "$REP_S" "$REP_T" || FL="$FL cp-report"
printf '%s  restore_report_20261115.tsv\n' "$XR" > "$REP_T.sha256.tmp" && mv -n "$REP_T.sha256.tmp" "$REP_T.sha256" || FL="$FL report-sha-file"
cp -n "$PRE_S" "$PRE_T" || FL="$FL cp-prefill"
echo "=== after: each placed file ==="
for f in "$SNAP_T" "$REP_T" "$PRE_T"; do echo "  $f: $(stat -c %s "$f" 2>/dev/null) bytes, sha256 $(sh1 "$f" 2>/dev/null)"; done
[ "$(sh1 "$SNAP_T")" = "$XS" ] || FL="$FL snapshot-sha"
[ "$(sh1 "$REP_T")" = "$XR" ] || FL="$FL report-sha"
[ "$(sh1 "$PRE_T")" = "$XB4" ] || FL="$FL prefill-sha"
( cd "$FX" && sha256sum -c abp_surface_fill_20261115.tsv.sha256 restore_report_20261115.tsv.sha256 abp_surface_fill_20261025.tsv.sha256 ) || FL="$FL sha256-c"
n=$(sqlite3 -readonly "$PRE_T" "SELECT count(*) FROM abp_surface"); echo "  $PRE_T: abp_surface $n rows (expect 391141)"; [ "$n" = 391141 ] || FL="$FL prefill-rows"
ls "$FX"/*.tmp >/dev/null 2>&1 && FL="$FL tmp-left"
st1=$(stat -c '%s %Y' "$SNAP_S" "$REP_S" "$PRE_S" "$FX/abp_surface_fill_20261025.tsv" | tr '\n' ' ')
echo "sources and the 10/25 file: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO)"; [ "$st1" = "$st0" ] || FL="$FL sources-changed"
g=$(git status --porcelain --untracked-files=no -- tests scripts); echo "checkout tests/ + scripts/ vs git: $([ -z "$g" ] && echo clean || echo "NOT clean: $g")"; [ -z "$g" ] || FL="$FL checkout"
if [ -z "$FL" ]; then
  echo "STEP9C-PLACE RESULT: DONE - placed $SNAP_T (+ .sha256), $REP_T (+ .sha256), $PRE_T; each = its pin; sources, the 10/25 file and the checkout unchanged"; exit 0
fi
echo "STEP9C-PLACE RESULT: CHECK -$FL (lines above). Nothing was overwritten (cp -n / mv -n); a wrong placed file can be moved aside to $D"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9C-PLACE reviewed (11/15) — REVIEW: ESCALATE (a write, §9.90 / §9.134 (b)); one DEFECT → fixed → closed
First verdict verbatim: "REVIEW: ESCALATE - STEP9C-PLACE writes outside a run folder (5 new files: 4 in the checkout's tests/fixtures/rebuild_trap/ plus ~/abp_surface_prefill_20261115.db). Under DESIGN 9.90 / 9.134(b) that means ESCALATE. I found one DEFECT in the mechanics that should be fixed before the ruling chat rules on it."
- DEFECT 1: the end check used `--untracked-files=all`; PA's three untracked scripts/ files (person_metav_link_residual.txt,
  person_metav_link_tier2.txt, tipnr_metav_link_residual.txt) would turn every clean run into CHECK. **Fixed exactly as named:**
  `--untracked-files=no` (as eu_step.py :136, :499); re-tested with those three files present → DONE.
- Notes: gate checks delegated to `eu_step pre` (:132-140, :154), as earlier eu_step blocks; pins match :81 / :85; never
  overwrites; JP pulls 19e2fb25 first; no pushes to scripts/ or tests/ while the block waits (§9.76).
Re-review verbatim: "REVIEW: ESCALATE - STEP9C-PLACE still writes outside a run folder (DESIGN 9.90 / 9.134(b)), so it goes to the ruling chat. Finding 1 is closed and nothing new turned up."

### Ruling (11/15, §9.135) — STEP9C-PLACE cleared to run at 19e2fb25

### STEP9C-PLACE ran (11/15, 17:39:09Z, PA HEAD 1425b124, REF 19e2fb25) — DONE, exit 0
Log `~/edition_upgrade_runs/step9c_place_20261115.log` (PA pulled 476de530 → 1425b124 first). PRE OK (19e2fb25 pulled, an
ancestor, scripts/tests = REF, nothing uncommitted; the three sources present). Targets none existing. Sources = expect:
snapshot d025cc08… (455,953 B), report e154d8d4… (403,318 B), pre-9a copy ea6c54c3… (18,194,432 B); the checkout's
restore_surface_fill.py carries both pins; 10/25 file d9435bde…; all four fixture targets git-ignored. Placed:
`tests/fixtures/rebuild_trap/abp_surface_fill_20261115.tsv` 455,953 B d025cc08…, `restore_report_20261115.tsv` 403,318 B
e154d8d4…, `~/abp_surface_prefill_20261115.db` 18,194,432 B ea6c54c3… (abp_surface 391,141 rows); `sha256sum -c` OK on
abp_surface_fill_20261115 / restore_report_20261115 / abp_surface_fill_20261025; sources + 10/25 file unchanged; checkout clean.
Every line = the §9.135 declaration.

## STEP9C-CHECK drafted (11/15, GATE REF 19e2fb25) — §9.134 (c): rebuild-words 1a's `--check` on built under the 9c pins

Read-only; writes only `step9c_check_20261115/` + its log. Guards (STOP): pre (`--db` built + src, `--keep` the pre-fill copy,
snapshot, report); the two `.sha256` files present; snapshot d025cc08… / report e154d8d4… / pre-fill copy ea6c54c3…; built =
STEP9A-APPLY's result (eu_step check). **1.** The 1a command (rebuild-words.md :74) with `--src` = built → exit 0 and nine printed
lines (snapshot_surface_fill.py at 19e2fb25: :314, :275, :286, :190, :342, :345-347, :348) incl. `RESULT: SNAPSHOT CURRENT`;
misses → CHECK. **2. Control:** the same with `--src` = src (10/25 layout) → must STOP "STALE SNAPSHOT" (§9.134 (ii)). **3. Control:**
`--csv` → must STOP "check needs --from-restore" (the §9.134 guard, :375-379). Built / src / pre-fill size+time and the fixture
folder listing unchanged, else STOP.
Local test (WSL, fake HOME, clone at 1848c08c + a fake commit setting the pins to the fakes; a made-up built with a 4,411-slot fill
re-frozen by the real STEP9C-FREEZE block, files placed as STEP9C-PLACE does; src = built minus one fill row): clean PASS exit 0
(nine yes; src control STALE; --csv control refused); re-paste STOP; a tampered frozen file → CHECK.

### Block STEP9C-CHECK (GATE REF 19e2fb25; READ-ONLY — writes only its run folder and log)
```bash
set +H
L=~/edition_upgrade_runs/step9c_check_20261115.log
if [ -e "$L" ]; then echo "STEP9C-CHECK RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=19e2fb25
echo "GATE REF ${REF} - STEP9C-CHECK rebuild-words step 1a's --check under the 9c pins, on built (DESIGN 9.134 (c)): snapshot_surface_fill --check --src <built> --prefill ~/abp_surface_prefill_20261115.db --from-restore the pinned report - expect SNAPSHOT CURRENT; two controls that must STOP (src = the 10/25 layout -> STALE; --csv -> the 9.134 guard) - READ-ONLY, writes only its run folder and log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP9C-CHECK RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
DA=~/edition_upgrade_runs/step9a_apply_20261115
PF=~/abp_surface_prefill_20261115.db
FX=tests/fixtures/rebuild_trap
SNAP=$FX/abp_surface_fill_20261115.tsv
REP=$FX/restore_report_20261115.tsv
D=~/edition_upgrade_runs/step9c_check_20261115
XS=d025cc086cd7f325bafe3c89655c778f8cdc57f67ba127061a3edfd2192472ff
XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a
XB4=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273
ck() { python3 scripts/snapshot_surface_fill.py --check --src "$1" --prefill "$PF" "$2" "$3" --out "$SNAP" > "$4" 2>&1; }
# --- before the check: every miss is STOP ---
python3 scripts/eu_step.py pre --tag CHECK9C --ref "$REF" --dir "$D" --db "$B" --db "$S" --keep "$PF" --keep "$SNAP" --keep "$REP" || { echo "STEP9C-CHECK RESULT: STOP - pre (line above); nothing read"; exit 1; }
for f in "$SNAP.sha256" "$REP.sha256" "$DA/state.json" "$DA/dry.db"; do [ -s "$f" ] || { echo "STEP9C-CHECK RESULT: STOP - missing or empty: $f"; exit 1; }; done
s=$(sha256sum < "$SNAP" | cut -d' ' -f1); echo "snapshot $SNAP: sha256 $s (expect $XS)"; [ "$s" = "$XS" ] || { echo "STEP9C-CHECK RESULT: STOP - not the pinned snapshot"; exit 1; }
s=$(sha256sum < "$REP" | cut -d' ' -f1); echo "report $REP: sha256 $s (expect $XR)"; [ "$s" = "$XR" ] || { echo "STEP9C-CHECK RESULT: STOP - not the pinned report"; exit 1; }
s=$(sha256sum < "$PF" | cut -d' ' -f1); echo "pre-fill copy $PF: sha256 $s (expect $XB4)"; [ "$s" = "$XB4" ] || { echo "STEP9C-CHECK RESULT: STOP - not the recorded pre-fill copy"; exit 1; }
echo "=== built = what STEP9A-APPLY left (eu_step check against STEP9A-APPLY's prep + throwaway copy; read-only) ==="
python3 scripts/eu_step.py check --tag CHECK9C --built "$B" --dir "$DA" --written abp_surface || { echo "STEP9C-CHECK RESULT: STOP - built is not STEP9A-APPLY's result (lines above)"; exit 1; }
st0=$(stat -c '%s %Y' "$B" "$S" "$PF" | tr '\n' ' '); fx0=$(ls -l --time-style=+%s "$FX" | sha256sum | cut -d' ' -f1)
FL=""
# --- the check (the 1a command, --src = built): must read SNAPSHOT CURRENT ---
echo "=== 1. --check on BUILT under the 9c pins (the rebuild-words 1a command, --src = built) ==="
ck "$B" --from-restore "$REP" "$D/check_built.out"; r=$?
cat "$D/check_built.out"; echo "check exit $r (expect 0)"
chk() { case "$(cat "$D/check_built.out")" in *"$2"*) echo "  $1: yes";; *) echo "  $1: NO (expected text: $2)"; FL="$FL $3";; esac; }
echo "--- vs the declared figures:"
chk "frozen file = its .sha256 and the pin" "PASS — checksum file matches, = the pin in restore_surface_fill.py" pin
chk "report = its .sha256" "restore report sha256 $XR = its .sha256" report-file
chk "report = the pin (R1)" "restore report = the pin in restore_surface_fill.py" report-pin
chk "G0 = the report, 4,411 = 3,873 + 538" "PASS — 4,411 = 3,873 insert + 538 update = the restore report" g0
chk "re-derived = the frozen file byte for byte" "PASS — 4,411 rows, identical bytes" bytes
chk "rows 4,411" "rows                    4,411 | 4,411" rows
chk "inserts / updates 3,873 / 538" "inserts / updates       3,873 / 538 | 3,873 / 538" split
chk "sha256 pin | file" "sha256                  $XS | $XS" sha
chk "SNAPSHOT CURRENT" "RESULT: SNAPSHOT CURRENT" current
[ "$r" = 0 ] || FL="$FL exit"
# --- controls (the check must be able to fail): each must STOP ---
echo "=== 2. control: --check with --src = src (the 10/25 layout, pre-upgrade live) - must read STALE (DESIGN 9.134 (ii)) ==="
ck "$S" --from-restore "$REP" "$D/check_src.out"; rc1=$?
cut -c1-300 <<< "$(grep -E '^STOPPED|^RESULT' "$D/check_src.out")"; echo "control exit $rc1 (expect 1)"
[ "$rc1" = 1 ] && grep -q "STALE SNAPSHOT" "$D/check_src.out" && [ "$(grep -c "SNAPSHOT CURRENT" "$D/check_src.out")" = 0 ] || FL="$FL control-src"
echo "=== 3. control: --check with --csv (any existing file; the 9.134 guard stops before reading it) - must STOP ==="
ck "$B" --csv "$REP" "$D/check_csv.out"; rc2=$?
cut -c1-300 <<< "$(grep -E '^STOPPED|^RESULT' "$D/check_csv.out")"; echo "control exit $rc2 (expect 1)"
[ "$rc2" = 1 ] && grep -q "check needs --from-restore" "$D/check_csv.out" || FL="$FL control-csv"
# --- nothing written ---
st1=$(stat -c '%s %Y' "$B" "$S" "$PF" | tr '\n' ' '); fx1=$(ls -l --time-style=+%s "$FX" | sha256sum | cut -d' ' -f1)
echo "built, src and the pre-fill copy: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO); fixture folder listing before = after: $([ "$fx1" = "$fx0" ] && echo yes || echo NO)"
[ "$st1" = "$st0" ] && [ "$fx1" = "$fx0" ] || { echo "STEP9C-CHECK RESULT: STOP - a database or the fixture folder changed during a read-only run - report this"; exit 1; }
if [ -z "$FL" ]; then
  echo "STEP9C-CHECK RESULT: PASS - --check on built under 19e2fb25: SNAPSHOT CURRENT (4,411 rows, byte for byte; snapshot + report = their pins); both controls STOP (src STALE, --csv refused); nothing written"; exit 0
fi
echo "STEP9C-CHECK RESULT: CHECK -$FL (lines above; outputs in $D)"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP9C-CHECK reviewed (11/15) — ESCALATE (tripwire 2: grep piped to cut, lines 50 / 54) → fixed as named → REVIEW: CLEAR
Fix: both display lines → `cut -c1-300 <<< "$(grep -E '^STOPPED|^RESULT' "<file>")"`; nothing else changed; re-test identical.
Verdict line verbatim: "REVIEW: CLEAR - read-only block. The tripwire 2 hit is fixed: lines 50 and 54 now use <<<. All expected texts trace to code at 19e2fb25, and the wrapper is complete."
Runs only after the ruling chat has read the STEP9C-PLACE log (§9.135). No push while it waits (§9.76).

### Ruling (11/15, §9.136) — STEP9C-PLACE DONE and closed (log read in full from JP's cat of the log; exit=0 as reported)

### STEP9C-CHECK ran (11/15, 17:52:28Z, PA HEAD 1425b124, REF 19e2fb25) — PASS, exit 0 → STEP 9c CLOSED (§9.137)
Log `~/edition_upgrade_runs/step9c_check_20261115.log`. PRE OK; snapshot d025cc08… / report e154d8d4… / pre-fill copy ea6c54c3…
= expect; CHECK OK (149 + schema 0; 395,014 / 219a3ebe7075). **1.** `--check` on built: F PASS (= the pin); report = its .sha256
and = the pin; G0 PASS (placed 4,411 · src-not-in-prefill 4,411 · prefill-not-in-src 538; 4,411 = 3,873 + 538); O PASS; C PASS
4,411 rows identical bytes; RECEIPT 4,411 | 4,411, 3,873 / 538 | 3,873 / 538, sha d025cc08… | d025cc08…; **RESULT: SNAPSHOT
CURRENT**; exit 0; nine lines yes. **2.** src control: "STOPPED: STALE SNAPSHOT — --src no longer yields the frozen fill (G0 the
report places 4,411 slots, the diff holds 4,420 (11 differ, e.g. [(131, 1), (132, 1), (985, 1)]) …"; exit 1. **3.** `--csv`
control: "STOPPED: --check needs --from-restore …"; exit 1. Built / src / pre-fill copy + fixture folder unchanged. RESULT PASS.
CC's reading of the src control's 11, offered only, not a finding: verse ids 131 / 132 / 985 are Gen 5:25 / 5:26 / 34:4 — three
of the six slots 9a placed at a moved position (§9.128 "moved 6"); src holds the fill at the old layout, so a diff of src against
the post-step-9 table differs at moved slots. Not read further; recorded as printed (§9.137).
**Ruling (11/15, §9.137): step 9c CLOSED; steps 9 → 9a → 9b → 9c complete on built.** Next: charter §6 step 4 report.
`step9a_apply_20261115/dry.db` (the 9a throwaway, ~110 MB): left in place for now (CC's call, §9.137) — not needed by any pin.

## Step 4 (compare_words vs live) — CC report: what it needs (11/15, §9.137; nothing drafted, nothing run)

- **The gate, as written** (charter §6 :328-330): "4 compare_words vs live — per-COLUMN attribution: `english` / `english_head` /
  `verses.text` rows = the declared 29% set + Mark 1:9; ANY `strongs` / `strongs_base` / `position` / `morph` delta outside the
  declared (ii) set = stop". Mark 1:9 must appear by name in the `english` diff, value = the app's cell (DESIGN :236-251; Q 7.5 ruled at DESIGN :341:
  informational, no english_rows section).
- **The tool as it stands cannot give that gate** (`scripts/compare_words.py`, 135 lines, unchanged since 7bca8fac): it keys words by
  verse + position over english, english_head, strongs, strongs_base, greek_pos, italic, italic_words, smcap_words, morph, lemma,
  is_pn + a bracket rank (:36-37, :40-68); prints a fingerprint, three counts and the FIRST `--limit` rows of each list (:113-126);
  exit 1 on any difference. It does NOT: count differences per column; read `verses.text`; follow a word that moved position (a move
  shows as one "only in OLD" + one "only in NEW"); write the full member list to a file; or compare any column against a declared set.
- **The declared sets are not member files yet.** CC found no file for "the declared 29% set" (the charter and DESIGN :243 quote the
  phrase only; `step5_eligible_20261101.tsv`, e540d34d, is the 29,071 ELIGIBLE verses — not the same thing, not checked as a
  stand-in). "The declared (ii) set" comes from charter §3's choice (ii) "taken with a declared slot change", but **Q7 was ruled (i)**
  (count-differs keep the old text, §3 :133-135) — so what step 4 must treat as declared position / strongs / strongs_base / morph
  changes is the set of ruled stage C/D changes on built (e.g. REKEY's key moves, the 20 moved words and 10 reorder verses in the
  stageC_repin follow-up list, the digits restore, 8b.2's six none → lemma-only strongs_base rows incl. Jer 49:3 @3, the 8b.2a
  lane-3 repairs) — today spread across records, not one list.
- **"vs live":** `<src>` is the step-1 copy of live (11/01). Whether step 4 compares built against `<src>` (and separately proves live
  = src now), or against a fresh copy of live, is unruled.
- **Open item that lands in this gate:** the heads gap (§9.107 ruling 2: built 1,351 fewer non-blank `english_head`; lost 1,691 /
  gained 340) is an `english_head` column difference — it has to be explained before step 4 can pass that column.
- **CC's proposal (for a ruling, no code yet):** (1) a ruling on what the declared sets are: the changed-English verse set (derived
  src → built from `verses.text`, then ruled as a member list) + Mark 1:9; and the (ii) set = a member list assembled from the ruled
  stage C/D changes, each row citing its § ruling. (2) A read-only first block: the full raw delta built vs src, written in full to
  files — per row (verse, position, column, before, after) for `words`, per verse for `verses.text` — with counts per column and the
  moved-word pairs matched, no gate yet; its figures drive (1). Done with one committed script (the §9.106 rule: no pasted helper),
  so a code change → reviewer → ruling chat; or `compare_words.py` extended. (3) Then the gate block: each column's member set =
  its declared file, exactly.

## Step 4 — item 3 sources report (11/15, §9.138 (3)); repo + local copies only, no PA run

**A. The changed-English verse set — what can produce it from the build's INPUTS (not from built):**
- **Which verses the build takes:** A's eligible file (derivation A's own output, §9.48 "A owns eligibility"; B re-checks it
  against its own decide() on the same frozen inputs, build_prose_from_app.py :28-30, :130-133). PA `~/edition_upgrade_runs/
  step5_eligible_20261101.tsv` (e540d34d…; local copy `C:\Users\JP\edition_upgrade_runs\pa\eligible_20261031.tsv`, same sha):
  31,237 verses, **eligible 29,071 / ineligible 2,166** = count_differs 704 · passdiff 625 · other 464 · rows 111 · dotted 61 ·
  markup 60 · bracket 50 · dash 37 · versification 32 · ours_only 9 · swap 7 · correction 6 (counted from the local copy).
- **Count-differs:** the build's kept-old set is the CHUNK-LEVEL 704 (`tests/fixtures/edition_upgrade/count_differs_chunk_20261031.tsv`,
  0453e3b4…, committed; §9.18: "Frozen count-differs for the build = chunk-level set … 1,849 remains the Q7 'before' for the
  post-build census"); all 704 = A's count_differs verses (checked locally, 704 / 704). The 1,849 census list
  (`~/count_differs_members.tsv`, PA only) is the gate-5 member list, not the build's input — not checked here against the 2,166.
- **verses.text:** B's per-verse list `step5_prose_20261101.tsv` (f2a22ecd…; local copy `prose_20261031.tsv`, same sha) — written
  15,571 · unchanged 13,500 · kept_old 2,166; derived from the feed + src + A's eligible file; B2's apply list was "SAME bytes"
  (HANDOFF_edition_upgrade_stageC.md :82, :88-90). Mark 1:9 is in it: eligible, `written`, 123 → 113 chars. **Available as a member list.**
- **words.english / english_head:** A prints only a COUNT ("english changed 15,588", build_words_from_abp.py :2473-2475); its
  dry run writes strict_fail, eligible, merge_pairs, edge_splits (:2481-2507) — **no per-cell english list exists.** It can be
  produced from inputs only by a new A dry-run output (a code change to the build; a new file = checkpoint) run on a copy of src
  with the step-5 inputs, its count checked = 15,588.
- **Later English writes on built, each with its own file:** finish_rebuild 4b prose corrections (6 active + 118 EU rows) and
  step 7 word corrections (`tests/fixtures/edition_upgrade/eu_batch_rows_20261102/20261103.tsv`, committed; correction carve-out
  `correction_carveout_20261031.tsv`); 8b.2a lane-3 (18 verses: english 35 · english_head 17 cells, `~/rekey/live_8b2a.log`
  + DR "8B2A" entry); merge pairs 1,578 / edge splits 90 (old English kept, `merge_pairs_` / `edge_splits_20261102.tsv`, committed).
- **"29%":** neither lane figure is 29% (B wrote 15,571 = 49.8% of 31,237; A english changed 15,588). The 29% comes from the
  rebuild-trap charter's estimate; not traced further.

**B. The (ii) set — ruled stage C/D changes to strongs / strongs_base / position / morph (inventory checked against DR lines):**
| change | columns | ruling | members in a file? |
|---|---|---|---|
| 10 reorder verses = the 20 moved words | position (whole rows; morph+lemma with them in 7) | §9.93 (a) | listed in DR :2724-2726; file `strongs_pos_census2_20261106.tsv` — PA only |
| 8b.2: the six none → lemma-only rows | strongs_base (H → `*`) | §9.95 | `drift8b2_20261106.log` (PA); Jer 49:3 @3 read (§9.133); the other five's positions from §9.78 only |
| 8b.2: 26,323 rewrites | strongs_base | §9.95 | **counts only** (`xref8b2c_*` logs PA); restores live's 10/25 state, so expected net vs src = the six only — not measured |
| 8b.0: 339 applied | strongs_base | §9.93 (d) | **counts only** in the repo (`xref8b0b_20261106.log` PA; 5 named vs the 10/25 plan, DR :2716-2718) |
| 8b.1: 178 restored to the frozen record | strongs_base | §9.94 (a) | dry-run members local `C:\Users\JP\xref8b1_20261106.log` (182 lines); apply log PA |
| ABPTAG-RESTORE: 16 | strongs_base | §9.96 | named in DR :2880-2912; "src carries the record's number … on all 16" (DR :2812) → net vs src 0 expected |
| Split 80 → 84 (subject-name split, build) | strongs, strongs_base, morph | **NOT ruled** — +4 unattributed, member log muted (DR :314-318) | none |
| PN-star A 1,505 + B 2,552; Filled 5 | strongs; position+strongs | counts = 10/25 (stage B record, D :470; not a § ruling) | **counts only** |
- **Not in the four columns, by their own records:** 8b.2a (DR :3446-3447: "strongs/strongs_base snapshot diff 0 … english 35 ·
  english_head 17 · greek_pos 38 · bracket_id 41 · other columns 0") — so the 8b.2a repairs belong to the English side, not (ii);
  the digits restore (writes `greek_pos, bracket_id` only, eu_repair_restore_digits.py :268); REKEY (no words column); SLOT3, 8b.3.
- **Gaps:** no step measured NET strongs_base built vs src after all of 8b (the census key is strongs+morph+lemma); 8b.0's 339 and
  8b.2's 26,323 are counts only; 6 of the 10 reorder verses have no recorded cause (4 trace to fix_split_merges entries skipped or
  re-keyed on built, §9.72 / §9.77 — CC's reading); Split +4 unruled; the §9.92 "words trace" not found.

**What would produce the (ii) list from the steps' own files (not the delta):** a read-only PA block that extracts members from the
PA-only logs/files above (census2 .tsv; drift8b2 log; xref8b0b / xref8b1b / abptag apply logs if they print members; stage B log
for Split / PN-star) — what each log actually prints is not known until read. Where a step's log holds counts only (8b.2's 26,323
at least), its members cannot come from its own files; the ruling chat to say how those are declared.

## Step 4 raw-delta code (11/15, CC; §9.138 (2) / §9.139) — in the working tree, NOT committed until ruled

Order chosen (§9.139 (5)): this code first (the first NET measure), then the live = src proof and the PA log read, then the A
dry-run English output.
- **NEW `scripts/eu_words_delta.py`** (read-only; both databases opened `mode=ro` + `query_only`; writes only into an existing
  EMPTY `--out`): `--a <src> --b <built> --out <dir>`. Keys: verse = (book, chapter, verse); word = (book, chapter, verse,
  position); row ids and verse_id not compared. Every `words` column both copies have is compared (columns on one side only are
  printed); `bracket_id` as a per-verse first-appearance RANK (as compare_words.py); every `verses` column but id. STOP on a
  duplicate verse or word key, or a word whose verse_id has no verse row.
  **Moved-word pairing rule (stated in the code docstring, §9.138 condition):** identity = (strongs, morph, lemma) — the 11/6
  census v2 key. Per verse, a-side candidates = positions only on a or whose identity differs from b's at the same position; b
  likewise. a:p and b:q (q ≠ p) pair ONLY when their identity matches and no other candidate on either side carries that identity
  in that verse (unique both ways); every other candidate is written as UNPAIRED. A pair is a reading aid — its cells still appear
  as they are.
  Files: words_cells.tsv (book chapter verse position column a b moved), words_only.tsv, words_moved.tsv (with the other columns
  that differ between the paired rows), words_unpaired.tsv, verses_cells.tsv, verses_only.tsv, summary.txt; values via repr();
  each file's line count + sha256 printed; counts per column printed.
- **NEW `tests/test_eu_words_delta.py`** (10): identical → all 0; changed cell listed; bracket renumbered = no difference,
  regrouped = difference; a swap pairs both ways; a repeated identity left UNPAIRED (never forced); a one-side word listed and
  paired when unique; verses.text + a one-side verse listed; neither db written (sha + mtime, no journal); `--out` must exist and
  be empty; same file both sides refused. Proven able to fail: uniqueness check loosened → the repeated-identity test fails;
  bracket rank off → the bracket test fails. Added to ci.yml + pre-commit (79 test files, all pass on the working tree).
- **Charter §6 step 4 amended** (§9.139 (0), old wording cited in place): "the declared 29% set" → "the declared changed-English
  set".
- Not in this change: any gate (§9.139 (6)); the A dry-run output (§9.139 (1)); the PA blocks. After the ruling: commit = new code
  REF; then the raw-delta block (read-only: built vs src into a run folder; reviewer) and the live = src proof block (a fresh copy
  of live, JP's disk check first, the copy and its removal in the block).

### Step 4 raw-delta code reviewed (11/15) — REVIEW: ESCALATE (code change); 3 GAPs → 2 closed, memory open for a ruling
First verdict verbatim: "REVIEW: ESCALATE - this is a code change (new script, new test, CI/hook lines, charter amendment). Under §9.90 that goes to the ruling chat. The mechanics are mostly sound; findings are below."
Confirmed: read-only (`mode=ro` + `query_only`), `--out` must exist and be empty, same file refused; the pairing rule = the
docstring, nothing forced; every member reaches a file; all common columns compared, type-strict, repr keeps None vs ''.
**Fixed after review:** summary.txt written with plain `open(..., newline="\n", errors="surrogateescape")` (any python3);
ONE structure per side (the second copy gone) + a peak-memory line; read-only open via `as_uri()` (escapes ? # %); tests
10 → 16 (str vs int; 1 vs 1.0 — proven: dropping the type check fails exactly that test; one-side column; summary.txt = the
printed output; word with no verse row STOP; duplicate word STOP). 79 pre-commit test files pass.
**Memory, measured locally (WSL, made-up full-size copies: 31,237 verses, 624,740 words rows per side, 13 compared columns, short
values):** peak 757 MB (`time -v` 775,904 KB), 5.5 s. Real rows hold longer English → PA higher; not measured on PA.
Re-review verbatim: "REVIEW: ESCALATE - this is still a code change, so it goes to the ruling chat under §9.90. The Python-version and test GAPs are closed. The memory GAP is reduced, but PA's figure has not been measured, so it stays open as a ruling point."
Known limits, recorded: bracket_id is compared as a rank, so a type-only change in that column alone is hidden; `moved` = "in a pair
on either side", a reading aid. For the run block (reviewer's list): print `python3 --version`; `-journal` check on both copies;
a new dated empty `--out` + dated log; a peak-memory reading (`/usr/bin/time -v` as a second one); the three untracked PA files
left alone.

## STEP4-DELTA drafted (11/15, GATE REF a147c61a; PA pulls first) — the step-4 raw delta, no gate (§9.138 (2) / §9.140)

Read-only on both databases; writes only `step4_delta_20261115/` (+ `delta/` for the script) and its log. Prints python3's version;
pre (REF a147c61a; `--db` built + src: journals, triggers); built = STEP9A-APPLY's result (eu_step check); src size = 451,964,928
(every stage-E log); `/usr/bin/time -v eu_words_delta.py --a src --b built --out step4_delta_20261115/delta`; prints the script's
whole output (counts per column, one-side-column lines, moved / unpaired, six file shas, its peak-memory line), then time's peak /
wall / exit; a STOP from the script keeps the partial folder and STOPs the block (§9.140 (a)); built + src size/time unchanged.
Known limits carried (§9.140): a type-only bracket_id change is hidden by the rank; "moved" is a reading aid.
Local test (WSL, made-up built + 9a folder with morph/lemma; src = a copy with a verse text changed and a word moved): READ DONE
exit 0 (1 moved pair, 1 verses.text, peak 35 MB); re-paste STOP; wrong src size STOP; no morph/lemma → script STOP → block STOP;
duplicate word key → script STOP → block STOP.

### Block STEP4-DELTA (GATE REF a147c61a; READ-ONLY — writes only its run folder and log; no gate)
```bash
set +H
L=~/edition_upgrade_runs/step4_delta_20261115.log
if [ -e "$L" ]; then echo "STEP4-DELTA RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=a147c61a
echo "GATE REF ${REF} - STEP4-DELTA charter sec 6 step 4, the RAW DELTA (DESIGN 9.138 (2) / 9.140): eu_words_delta.py --a src --b built, every member to files, counts per column - NO GATE - READ-ONLY on both databases; writes only its run folder and log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "STEP4-DELTA RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
DA=~/edition_upgrade_runs/step9a_apply_20261115
D=~/edition_upgrade_runs/step4_delta_20261115
XS_SIZE=451964928
echo "python3: $(python3 --version 2>&1)"
# --- before the run: every miss is STOP ---
python3 scripts/eu_step.py pre --tag DELTA4 --ref "$REF" --dir "$D" --db "$B" --db "$S" || { echo "STEP4-DELTA RESULT: STOP - pre (line above; it also refuses a -journal beside either copy); nothing read"; exit 1; }
for f in "$DA/state.json" "$DA/dry.db"; do [ -s "$f" ] || { echo "STEP4-DELTA RESULT: STOP - missing or empty: $f"; exit 1; }; done
echo "=== built = what STEP9A-APPLY left (eu_step check against STEP9A-APPLY's prep + throwaway copy; read-only) ==="
python3 scripts/eu_step.py check --tag DELTA4 --built "$B" --dir "$DA" --written abp_surface || { echo "STEP4-DELTA RESULT: STOP - built is not STEP9A-APPLY's result (lines above)"; exit 1; }
n=$(stat -c %s "$S"); echo "src size: $n bytes (expect $XS_SIZE, as in every stage-E log)"
[ "$n" = "$XS_SIZE" ] || { echo "STEP4-DELTA RESULT: STOP - src is not the size every declared figure was read against"; exit 1; }
st0=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' ')
mkdir "$D/delta" || { echo "STEP4-DELTA RESULT: STOP - cannot make $D/delta"; exit 1; }
# --- the raw delta (src = a, built = b); peak memory read twice: the script's own line and /usr/bin/time -v ---
echo "=== eu_words_delta.py --a src --b built --out $D/delta ==="
if [ -x /usr/bin/time ]; then
  /usr/bin/time -v python3 scripts/eu_words_delta.py --a "$S" --b "$B" --out "$D/delta" > "$D/delta.out" 2> "$D/time.txt"; r=$?
else
  python3 scripts/eu_words_delta.py --a "$S" --b "$B" --out "$D/delta" > "$D/delta.out" 2> "$D/time.txt"; r=$?
  echo "(no /usr/bin/time on this system - the script's own peak line only)"
fi
cat "$D/delta.out"
echo "delta exit $r (expect 0)"
echo "--- /usr/bin/time -v (peak memory, wall time, exit):"
grep -E "Maximum resident set size|Elapsed \(wall clock\)|Exit status|Command terminated" "$D/time.txt"
grep -qv -E "^\s|Command being timed" "$D/time.txt" && { echo "--- anything else the run wrote to stderr:"; grep -v -E "^\s|Command being timed" "$D/time.txt"; }
[ "$r" = 0 ] && [ -n "$(sed -n '/^RESULT: DELTA WRITTEN/p' "$D/delta.out")" ] || { echo "STEP4-DELTA RESULT: STOP - the delta did not finish (exit $r; lines above; partial files kept in $D/delta) - the log goes to the ruling chat, a re-run uses a new dated folder"; exit 1; }
echo "--- files in $D/delta:"
ls -l "$D/delta" | sed 's/^/  /'
st1=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' ')
echo "built and src: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO)"
[ "$st1" = "$st0" ] || { echo "STEP4-DELTA RESULT: STOP - built or src changed during a read-only run - report this"; exit 1; }
echo "STEP4-DELTA RESULT: READ DONE - every member in $D/delta (no gate; nothing ruled from counts; known limits: a type-only bracket_id change is hidden by the rank; 'moved' is a reading aid)"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### STEP4-DELTA reviewed (11/15) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - read-only raw delta under DESIGN 9.138 (2) / 9.140 (no gate); the wrapper checks are all present (git diff, porcelain and merge-base sit inside eu_step pre); the only writes are new run artifacts."
Reviewer notes: src size traced to DR :6179, :6265, :9192 (also built's size before step 11, DESIGN :515 — harmless, src is the
path tested); `morph` / `lemma` on built traceable from the build (build_words_from_abp.py :2639-2642), on src not receipted in
the repo — if absent the script STOPs cleanly and both copies stay untouched.

### STEP4-DELTA ran (11/15, 19:21:30Z, PA HEAD e5f77e11, REF a147c61a) — READ DONE, exit 0 (§9.141)
Log `~/edition_upgrade_runs/step4_delta_20261115.log`; files `step4_delta_20261115/delta/`. Python 3.13.1; PRE OK; built
452,063,232 B, src 451,964,928 B; CHECK OK. 13 words columns compared, none one-sided; rows 31,237 / 626,309 both. Counts:
english 32,962 · english_head 5,427 · strongs 20 · strongs_base 26 · greek_pos 3,318 · bracket_id 4,208 · italic 0 ·
italic_words 0 · smcap_words 0 · is_pn 12 · morph 14 · lemma 14 · english_head_norm 4,891 · only 0 / 0 · moved 20 in 10 verses,
unpaired 0 / 0 · verses.text 15,522 · verses only 0 / 0. words_cells 50,892 lines `62d9c85dd7d7b19a8c398f6894fd3e4ec2f7ce70fb400d61b88504814df27ac4`;
words_moved 20 `d32361b3f814e5e5079ff408272d563605036afbf032dfc0ce8943c970d60f08`; verses_cells 15,522
`870e4782018564c874ec16aa9ac6aa1c9516c4007df917f394db330bfe9857f9`; words_only / words_unpaired / verses_only 0 lines. Peak 638 MB
(no /usr/bin/time on PA). Built + src unchanged. Known limits carried: bracket_id type-only change hidden by the rank; "moved" a
reading aid. **Ruling (§9.141): READ DONE; next the members read of strongs / strongs_base / morph / lemma / is_pn and the 20 pairs.**

## Step 4 members read (11/15, §9.141 (4)-(5)) — local, from the STEP4-DELTA files; no PA run

JP's scp of `step4_delta_20261115/` → `C:\Users\JP\edition_upgrade_runs\pa\step4_delta_20261115\delta\`; local shas = PA's
(words_cells 62d9c85d…, words_moved d32361b3…, verses_cells 870e4782…).
**The 20 moved pairs = §9.93's 10 reorder verses, position for position** (2Ki 23:35 6/7, Est 5:9 12/13, Eze 20:14 7/8, Gen 5:25
1/2, Gen 5:26 1/2, Gen 34:4 1/2, Jdg 11:7 6/7, Jos 2:4 19/20, Jos 5:15 26/27, Rom 9:29 17/18 — DR :2724-2725); unpaired 0.
**The 86 strongs / strongs_base / morph / lemma / is_pn cells — every one attributed, 0 unattributed:**
- **80 at the 20 moved positions** (strongs 20 · strongs_base 20 · morph 14 · lemma 14 · is_pn 12) → §9.93 (a) "whole-row moves into
  the edition's English order". Checked locally: each of the 40 column pairs is an exact swap (built at p = src at q and built at q
  = src at p; 40 / 40, 0 exceptions). morph + lemma in 7 verses, is_pn in the 6 name+verb verses — as the census v2 record says.
- **6 elsewhere, strongs_base H → `*`** → §9.95's six none → lemma-only rows: Num 21:25 @2 (H3478), 1Sa 20:37 @11 (H3129), 2Sa 15:6
  @18 (H53), Jer 48:15 @1 (H4124), Jer 48:20 @12 (H4124), Jer 49:3 @3 (H5857) — positions = §9.78 for five, §9.133 for Jer 49:3.
- Output of the read, verbatim:
```text
in the 10 reorder verses at their moved positions: 80 Counter({'strongs': 20, 'strongs_base': 20, 'morph': 14, 'lemma': 14, 'is_pn': 12})
elsewhere: 6 Counter({'strongs_base': 6})
  1Sa | 20 | 37 | 11 | strongs_base | 'H3129' | '*' | no
  2Sa | 15 | 6 | 18 | strongs_base | 'H53' | '*' | no
  Jer | 48 | 15 | 1 | strongs_base | 'H4124' | '*' | no
  Jer | 48 | 20 | 12 | strongs_base | 'H4124' | '*' | no
  Jer | 49 | 3 | 3 | strongs_base | 'H5857' | '*' | no
  Num | 21 | 25 | 2 | strongs_base | 'H3478' | '*' | no

  M 2Ki | 23 | 35 | 6 | strongs | '1325' | '*' | yes
  M 2Ki | 23 | 35 | 6 | strongs_base | 'G1325' | '*' | yes
  M 2Ki | 23 | 35 | 6 | is_pn | 0 | 1 | yes
  M 2Ki | 23 | 35 | 6 | morph | 'V.AAI3S' | None | yes
  M 2Ki | 23 | 35 | 6 | lemma | 'δίδωμι' | None | yes
  M 2Ki | 23 | 35 | 7 | strongs | '*' | '1325' | yes
  M 2Ki | 23 | 35 | 7 | strongs_base | '*' | 'G1325' | yes
  M 2Ki | 23 | 35 | 7 | is_pn | 1 | 0 | yes
  M 2Ki | 23 | 35 | 7 | morph | None | 'V.AAI3S' | yes
  M 2Ki | 23 | 35 | 7 | lemma | None | 'δίδωμι' | yes
  M Est | 5 | 9 | 12 | strongs | '1492' | '*' | yes
  M Est | 5 | 9 | 12 | strongs_base | 'G1492' | '*' | yes
  M Est | 5 | 9 | 12 | is_pn | 0 | 1 | yes
  M Est | 5 | 9 | 13 | strongs | '*' | '1492' | yes
  M Est | 5 | 9 | 13 | strongs_base | '*' | 'G1492' | yes
  M Est | 5 | 9 | 13 | is_pn | 1 | 0 | yes
  M Eze | 20 | 14 | 7 | strongs | '3361' | '3892.4' | yes
  M Eze | 20 | 14 | 7 | strongs_base | 'G3361' | 'G3892' | yes
  M Eze | 20 | 14 | 7 | morph | 'D' | None | yes
  M Eze | 20 | 14 | 7 | lemma | 'μή' | None | yes
  M Eze | 20 | 14 | 8 | strongs | '3892.4' | '3361' | yes
  M Eze | 20 | 14 | 8 | strongs_base | 'G3892' | 'G3361' | yes
  M Eze | 20 | 14 | 8 | morph | None | 'D' | yes
  M Eze | 20 | 14 | 8 | lemma | None | 'μή' | yes
  M Gen | 5 | 25 | 1 | strongs | '2198' | '*' | yes
  M Gen | 5 | 25 | 1 | strongs_base | 'G2198' | 'G3103' | yes
  M Gen | 5 | 25 | 1 | is_pn | 0 | 1 | yes
  M Gen | 5 | 25 | 1 | morph | 'V.AAI3S' | None | yes
  M Gen | 5 | 25 | 1 | lemma | 'ζάω' | None | yes
  M Gen | 5 | 25 | 2 | strongs | '*' | '2198' | yes
  M Gen | 5 | 25 | 2 | strongs_base | 'G3103' | 'G2198' | yes
  M Gen | 5 | 25 | 2 | is_pn | 1 | 0 | yes
  M Gen | 5 | 25 | 2 | morph | None | 'V.AAI3S' | yes
  M Gen | 5 | 25 | 2 | lemma | None | 'ζάω' | yes
  M Gen | 5 | 26 | 1 | strongs | '2198' | '*' | yes
  M Gen | 5 | 26 | 1 | strongs_base | 'G2198' | 'G3103' | yes
  M Gen | 5 | 26 | 1 | is_pn | 0 | 1 | yes
  M Gen | 5 | 26 | 1 | morph | 'V.AAI3S' | None | yes
  M Gen | 5 | 26 | 1 | lemma | 'ζάω' | None | yes
  M Gen | 5 | 26 | 2 | strongs | '*' | '2198' | yes
  M Gen | 5 | 26 | 2 | strongs_base | 'G3103' | 'G2198' | yes
  M Gen | 5 | 26 | 2 | is_pn | 1 | 0 | yes
  M Gen | 5 | 26 | 2 | morph | None | 'V.AAI3S' | yes
  M Gen | 5 | 26 | 2 | lemma | None | 'ζάω' | yes
  M Gen | 34 | 4 | 1 | strongs | '2036' | '*' | yes
  M Gen | 34 | 4 | 1 | strongs_base | 'G2036' | 'G4966' | yes
  M Gen | 34 | 4 | 1 | is_pn | 0 | 1 | yes
  M Gen | 34 | 4 | 1 | morph | 'V.AAI3S' | None | yes
  M Gen | 34 | 4 | 1 | lemma | 'ἔπω' | None | yes
  M Gen | 34 | 4 | 2 | strongs | '*' | '2036' | yes
  M Gen | 34 | 4 | 2 | strongs_base | 'G4966' | 'G2036' | yes
  M Gen | 34 | 4 | 2 | is_pn | 1 | 0 | yes
  M Gen | 34 | 4 | 2 | morph | None | 'V.AAI3S' | yes
  M Gen | 34 | 4 | 2 | lemma | None | 'ἔπω' | yes
  M Jdg | 11 | 7 | 6 | strongs | '5210' | '3780' | yes
  M Jdg | 11 | 7 | 6 | strongs_base | 'G5210' | 'G3780' | yes
  M Jdg | 11 | 7 | 6 | morph | 'RP.NP' | 'D' | yes
  M Jdg | 11 | 7 | 6 | lemma | 'ὑμεῖς' | 'οὐχί' | yes
  M Jdg | 11 | 7 | 7 | strongs | '3780' | '5210' | yes
  M Jdg | 11 | 7 | 7 | strongs_base | 'G3780' | 'G5210' | yes
  M Jdg | 11 | 7 | 7 | morph | 'D' | 'RP.NP' | yes
  M Jdg | 11 | 7 | 7 | lemma | 'οὐχί' | 'ὑμεῖς' | yes
  M Jos | 2 | 4 | 19 | strongs | '1492' | '3756' | yes
  M Jos | 2 | 4 | 19 | strongs_base | 'G1492' | 'G3756' | yes
  M Jos | 2 | 4 | 20 | strongs | '3756' | '1492' | yes
  M Jos | 2 | 4 | 20 | strongs_base | 'G3756' | 'G1492' | yes
  M Jos | 5 | 15 | 26 | strongs | '*' | '4160' | yes
  M Jos | 5 | 15 | 26 | strongs_base | '*' | 'G4160' | yes
  M Jos | 5 | 15 | 26 | is_pn | 1 | 0 | yes
  M Jos | 5 | 15 | 27 | strongs | '4160' | '*' | yes
  M Jos | 5 | 15 | 27 | strongs_base | 'G4160' | '*' | yes
  M Jos | 5 | 15 | 27 | is_pn | 0 | 1 | yes
  M Rom | 9 | 29 | 17 | strongs | '3666' | '302' | yes
  M Rom | 9 | 29 | 17 | strongs_base | 'G3666' | 'G302' | yes
  M Rom | 9 | 29 | 17 | morph | 'V-API-1P' | 'PRT' | yes
  M Rom | 9 | 29 | 17 | lemma | 'ὁμοιόω' | 'ἄν' | yes
  M Rom | 9 | 29 | 18 | strongs | '302' | '3666' | yes
  M Rom | 9 | 29 | 18 | strongs_base | 'G302' | 'G3666' | yes
  M Rom | 9 | 29 | 18 | morph | 'PRT' | 'V-API-1P' | yes
  M Rom | 9 | 29 | 18 | lemma | 'ἄν' | 'ὁμοιόω' | yes
```
**The asked items:** Jer 49:3 @3 — found (one of the six). The 6 reorder verses with no recorded cause — found: all 10 reorder
verses are here and only as exact whole-row swaps; the delta shows WHAT moved, not WHY — their cause stays unrecorded (open, §9.139
(4)). Split 80 → 84 (+4) — NOT found: no number cell is left outside the 80 + 6, so the +4 left no net difference from src in these
five columns or in position (CC's reading: src was already split, DR :318). Likewise PN-star A / B, Filled 5, 8b.0's 339, 8b.1's
178, ABPTAG's 16 and 8b.2's 26,323 leave no net member here beyond the six.
**english_head_norm — a rule, checked on every member (local):** step 11 fills `english_head_norm = number_fold.normalize(english_head)`
(build_rendering_norm.py :11, :33; `from number_fold import normalize`). All 4,891 head_norm cells sit at a position whose
english_head differs (4,891 / 4,891); on both sides the stored norm = normalize(that side's head) (0 exceptions); the other 536
english_head differences normalize equal on both sides (0 stale). Proposal: declare english_head_norm "attributed by rule (step 11's
function), not by member file", following the english_head set.
**greek_pos 3,318 · bracket_id 4,208 — proposal:** both are derived by the bracket parser from the English line, so A's transplant
changes them; A counts only VERSES with any change (`greek_pos_or_bracket_changed`, build_words_from_abp.py :2459-2460); the PA
stage-B figure for it is not in the repo (`935 -> 737` at DR :2179 is a LOCAL no-dictionary fingerprint, not the build's). Proposal:
the approved A dry-run output (§9.139 (1)) also writes greek_pos and bracket_id cell changes in the same format, its verse count
checked against the stage-B log line (read on PA); plus the later writes from their own files: the digits restore (389 cells,
`restore_digits_plan_20261105.tsv`, PA), the J rows at Joh 14:26, 8b.2a (greek_pos 38 / bracket_id 41, its run files). bracket_id is
compared as a rank in the delta, so the A output must be compared as a rank too.

## Step 4 — two more local reads (11/15, §9.142 (1) and (5)); from the STEP4-DELTA files + committed / local files; no PA run

**(a) The other five columns at the 20 moved positions (§9.142 (1)):** 10 verses × 5 columns (english, english_head,
english_head_norm, greek_pos, bracket_id) = 50 column pairs: **exact swap 9 · equal at both positions on both copies 9 · NOT a swap
32.** The 32, as read (src → built at each position): 2Ki 23:35 greek_pos @6 2 → 1; Est 5:9 english / english_head
("seeing" | "Haman" → "Haman's" | "seeing") and greek_pos / bracket_id (2/1, 2/2 → None); Eze 20:14 english / english_head / norm
("should not" | "be thoroughly" → "thorough one," | "should not"); Gen 5:25 and 5:26 english / english_head / norm (Methuselah →
Mathusala; 5:26 "lived" → "lived,") and greek_pos / bracket_id (bracket removed); Jdg 11:7 english ("Did you" | "not" → "Is it not"
| "that you") + english_head / norm @6 "did" → None; Jos 2:4 english ("I know" | "not" → "I do not" | "know"); Jos 5:15 english /
english_head / norm (Josua → Joshua) + greek_pos / bracket_id (None → 2/1, 2/2); Rom 9:29 english / english_head / norm ("we would
be" | "like." → "we would have been like." | None) + greek_pos / bracket_id @17 (None → 1 / 3). So at the moved positions these five
columns are NOT covered by the (ii) list: they belong with the English / greek_pos / bracket_id declarations (the A dry-run output +
the later writes), as ruled.
**(b) B's verses.text list laid against the delta's 15,522 (§9.142 (5); local `prose_20261031.tsv` = step5_prose f2a22ecd…):**
B written 15,571 · delta 15,522 · **in both 15,522 · in the delta but not B-written 0** · B-written but NOT in the delta **49**. The 49
are exactly 49 of the 118 EU `verses.text` correction rows applied after B in 4b (`tests/fixtures/edition_upgrade/eu_batch_rows_20261103.tsv`,
committed; also in `abp_corrections_active_built_20261106.txt`, 0 in live's active list) — the correction brings those verses back to
the text src has. The other **69 EU verses.text rows are in the delta and built's text = their `corrected_value` exactly (69 / 69).**
So the verses.text delta = B's written set − the 49 EU rows whose correction equals src's text; every delta member is accounted for
by B's list or an EU row. (Not checked locally: that each of the 49 corrected_values equals src's text — src's text is not local;
their absence from the delta says built = src there.)

## Step 4 — §9.143 answers + the heads-gap read (11/15; local, from the STEP4-DELTA files + committed / local files; no PA run)

**What B's list holds per verse** (`prose_20261031.tsv` header): book, chapter, verse, outcome, reason, old_len, new_len, changed —
**lengths only, no text or hash.** So for the non-EU members the gate can check membership and built's text LENGTH = new_len; it
cannot check the text value from B's list alone (said in the record).
**The "6" of 4b's "6 + 118":** the 6 verses of the committed carve-out `tests/fixtures/edition_upgrade/correction_carveout_20261031.tsv`
(1Sa 9:3, 2Ch 10:13, Jer 3:7, Jer 9:23, Neh 12:43, Rev 11:1; §9.51 "carve-out on BOTH sides — A keeps old rows, B keeps old prose,
reason correction"). In B's list each is `kept_old / correction`; none is in the delta, none among the 49 / 69 — same on both copies.
(Live's active list holds 18 verses.text rows; the other 12 are not 4b's: 7 are B `unchanged`, 5 are B `written` and in the delta —
1Ch 22:15, 2Sa 16:18, Job 24:19, Mar 16:17, Mat 21:19.)
**Mark 1:9:** B `written` (123 → 113 chars), in the 15,522, not among the 49.
**Heads gap (§9.107 ruling 2), read from the 5,427 english_head members:** the delta reproduces the 11/8 record exactly — **lost
1,691 (text → None) · gained 340 (None → text) · changed 3,396 · net −1,351.** Every one of them except 2 sits on a cell whose
english also differs:
- lost 1,691 = 1,299 where the english went blank (src english most often "the one" 322, "the ones" 225, "of the ones" 122, "of the
  one" 89, "know" 35, "to the ones" 30, "to the one" 29 …; in 101 of the 1,299 the lost words appear in a neighbour's NEW english at
  −1 / −2) + 392 where the english changed to function words only ("for" 55, "For" 45, "of" 39, "not" 29, "the" 14 …) and the head is None;
- gained 340 = 235 english changed + 105 english filled (built "the ones" 41, "unto" 26, "the one" 26, "according to" 10 …);
- changed 3,396 = 3,394 with the english changed + **2 with the english the SAME:** Isa 48:5 @4 head 'would' → 'what' and Joh 19:18 @10
  'here' → 'ere'. Both are EU typo rows that correct `english` only, with NO english_head row (`eu_batch_rows_20261103.tsv` :158 "what
  whould happen" → "what would happen"; :101 "one h ere on that side," → "one here on that side,"): built's english = src's, its head
  reads like the head of the typo text. **Finding for the ruling chat, no cause asserted.** (12 EU english rows have no head row; for
  the other 10 the head is either equal to src or the english also changed.)
No cause is asserted for the 1,351; the read shows it is carried by English changes, cell by cell. The heads are declared through A's
english_head output (§9.139 (1)) + the later writes.
    LOST with english gone blank (1,299): top src english
         322 'the one'
         225 'the ones'
         122 'of the ones'
          89 'of the one'
          35 'know'
          30 'to the ones'
          29 'to the one'
          19 'want'
          13 'hearken to'
          11 'listen to'
           8 'know.'
           8 'know,'
           8 'hearken'
           8 'abstain'
           7 'turn'
       ...of the 1,299, the lost English words appear in a neighbour's NEW english (±1/±2) and not its old: 101 {-1: 97, -2: 4}
    LOST with english changed but head None (392): top built english
          55 'for'
          45 'For'
          39 'of'
          29 'not'
          14 'the'
          13 'into'
          11 'as'
          11 'to the'
          11 'in'
          10 'of,'
          10 'to'
           7 'upon'
           7 'he'
           6 'these'
           5 'of the'
    GAINED (340): top built english
          41 'the ones'
          26 'unto'
          26 'the one'
          10 'according to'
           7 'of the one'
           5 'of the ones'
           5 'him'
           4 'of which'
           4 'this one'
           4 'the things'
    head changed, english SAME (2):
       ('Isa', 48, 5, 4) ('would', 'what')
       ('Joh', 19, 18, 10) ('here', 'ere')

## §9.144 (5) — is english_head a function of english? + proposed fix mechanics for the 2 (11/15, CC; nothing drafted to run)

**No — english_head is NOT a pure function of english** (build_words_from_abp.py; parse_abp._head_word :80): the base pick is
`_head_word(english)` (last non-function word), but the stored head also depends on —
- `italic_words`: `_strip_italic_heads` re-picks skipping translator-added words (:1815-1834), and again after the subject-name split (:2779-2791);
- `strongs == '*'`: `_star_name_heads` prefers the capitalised NAME (`prefer_name=True`, :1837-1849);
- neighbouring rows: the function-word relocation and oath passes set heads by their own rules (`_fw_derive_head` :1646 used at
  :1694; `_oath_head` :1730 / :1758);
- the OLD edition: merge pairs and edge splits keep the OLD english_head (§9.73 / §9.75; :2072, :2141, :2205);
- hand corrections: the EU batch sets 107 english_head cells directly.
So "stored = derived" over every row cannot be one formula. **A read-only check that would still catch a stale head anywhere:**
recompute the base rule `_head_word(english, italic_words, prefer_name = strongs=='*')` on EVERY row of BOTH built and src (same
code, two copies) and list each copy's rows where stored ≠ recomputed; then compare the two lists. A row that mismatches on built
but NOT on src while its english (and italic_words, strongs) are equal on both is a stale-head candidate — the two known cases are
exactly that shape. Rows that mismatch on both copies are the special passes working (not candidates). Needs a small committed
read-only script (or an eu_words_delta option) → reviewer → ruling chat, then a read-only block.
**Proposed fix mechanics (for after that read, covering everything it finds; not drafted):** the lane's existing correction route —
- a new committed batch file `tests/fixtures/edition_upgrade/eu_batch_rows_heads_20261115.tsv` (+ `.sha256`): one row per stale head
  (book, chapter, verse, position, field `english_head`, source_value = built's head, corrected_value = src's head, ledger_ref
  EU-<verse>, group `typo`, §9.74 / §9.144);
- `eu_batch_insert.py` on built (`--sha256` / `--expect` pinned; it STOPs on any existing abp_corrections row on the same key, of any
  status) → `apply_abp_corrections.py --apply` (guarded: writes a cell only where it still holds source_value; every other active row
  reads "already applied") → `build_rendering_norm.py` on built (step 11's recompute; only the fixed rows' english_head_norm may move);
- in one write block: dry on a throwaway copy first (eu_step prep), before-copy saved, eu_step check after (words + abp_corrections the
  only written tables; every other table + schema unchanged).
- Knock-on, for the record: built's active-corrections count rises by the number of rows (cert_invariants pin / the active-list
  fixture re-pinned at the swap, as the rest of §4.7); the corrections ride to live with the swap, so a future rebuild re-applies them.

## Head-consistency check code (11/15, CC; §9.145 (2), order step (a)) — in the working tree, NOT committed until ruled

- **NEW `scripts/eu_head_check.py`** (read-only: `mode=ro` + `query_only`; writes only into an existing EMPTY `--out`):
  `--a <src> --b <built> --out <dir> [--show "Book C:V@P"]...`. Recomputes the BASE rule with the build's own function
  (`parse_abp._head_word`, the import build_words_from_abp.py :27 uses), in the build's order: plain pick → italic re-pick as
  `_strip_italic_heads` (:1815-1834: only when english has a space and italic_words names words) → name re-pick as `_star_name_heads`
  (:1837-1849: strongs `*`, english has a space, non-empty). Lists each copy's stored ≠ recomputed rows (mismatch_a / mismatch_b, in
  full); a CANDIDATE = mismatch on built only with english, italic_words, strongs equal on both copies (candidates.tsv: verse,
  position, english, stored head src, stored head built, recomputed, italic_words, strongs); built-only rows whose inputs differ are
  counted as "inputs differ" (the recorded LIMIT, §9.145 (2)). Counts both / src only / built only printed, none a gate; `--show`
  prints a named row's full detail on both copies (the block's control). STOP on a duplicate word key or a word with no verse row.
- **NEW `tests/test_eu_head_check.py`** (7): the recompute mirrors the base rule (plain / italic / name); identical copies → no
  candidate (a special-pass row mismatches on both); the Joh 19:18 shape on built only → a candidate; a built-only mismatch with other
  english → "inputs differ"; src-only counted; `--show` yes / NO; neither db written; `--out` empty; same file refused. Proven able to
  fail: italic re-pick off → 3 tests fail; the equal-inputs condition dropped → the inputs-differ test fails. In ci.yml + pre-commit
  (80 test files pass). Speed: 626,309 recomputes ≈ 1 s locally.
- **A note on the control, found while testing the function locally (for the ruling chat before the run):** the base rule gives
  "side" for "one here on that side," and "happen" for "what would happen"; the stored heads come from the italic re-pick. With
  italic_words {on, that, side}, "one here on that side," → 'here' and the typo "one h ere on that side," → 'ere' (= src / built at
  Joh 19:18 @10). For Isa 48:5 @4, "what would happen" gives 'would' with italic {happen} but 'what' with italic {would, happen};
  the typo gives 'whould' either way. italic_words is equal on both copies (the delta's italic_words count is 0) but its value is
  not local — so on the real rows built's 'what' may be what the rule gives and src's 'would' the mismatch. If so, Isa 48:5 @4 will
  NOT be a candidate and the block reads CHECK on that control, with `--show` printing both rows in full; that result comes to the
  ruling chat as found (it would bear on §9.144 (5)'s "built's head must read src's").

### Head-check code reviewed (11/15) — REVIEW: ESCALATE (code change); one DEFECT + one GAP → fixed → closed
First review: "REVIEW: ESCALATE - this is a code change, so under §9.90 it goes to the ruling chat. One DEFECT: `recompute()` runs the two head passes in a different order from the full build."
- **DEFECT — fixed:** the full build re-runs the italic re-pick AFTER writing the rows (build_words_from_abp.py :2784-2790 →
  fix_italic_heads.py :44-73: every row with a space and italic_words, no strongs condition, applied when the pick is not empty), so on
  a star row with italics the italic pick wins over the name pick. recompute() now = plain → italic (verse pass) → name (star rows) →
  italic re-clean LAST. Without the fix such rows would mismatch on both copies and could never become candidates.
- **GAP — fixed:** test `test_star_row_with_italics_ends_on_the_italic_pick` ("Hezekiah went up", italic {up}, `*` → 'went'; no italics
  → 'hezekiah'); switching the re-clean off fails exactly that test.
- **(7c) — added:** rows mismatching on both copies with different stored heads are counted and written to both_differ.tsv (outside the
  check, like inputs-differ). Test added. Tests 9; all 80 pre-commit test files pass.
Second review: "REVIEW: ESCALATE - this is a code change, so it still goes to the ruling chat under §9.90. The DEFECT and the GAP from my first report are both fixed in the working tree, and I found nothing new in the code."
Still open for the ruling chat before the run block: (6) the Isa 48:5 @4 control — CC's reading of `_head_word` confirmed by the reviewer
(parse_abp.py :117-139): if the row's italic_words are {would, happen}, built's 'what' is the rule's head, src's 'would' the mismatch,
and the row is src-only, not a candidate → the control reads CHECK; to be decided BEFORE the run. (7b) the run block declares the
expected control lines up front and gates on them. (7d) every count is a forecast with no source until the run.

## HEADCHECK drafted (11/15, GATE REF 50957fc0; PA pulls first) — the step-4 head-consistency check run (§9.145 (2) / §9.146)

Read-only; writes only `step4_headcheck_20261115/` (+ `check/`) and its log. Same wrapper as STEP4-DELTA (python3 version; pre on built
+ src; built = STEP9A-APPLY's result; src size 451,964,928; size/time unchanged). Runs `eu_head_check.py --a src --b built --show
"Joh 19:18@10" --show "Isa 48:5@4"`, prints its whole output (counts both / src only / built only, candidates, the two SHOW blocks,
four file shas). **Hard control (§9.146):** "SHOW Joh 19:18@10 - candidate: yes", else CHECK. Isa 48:5 @4 printed, not gated.
Local test (WSL; made-up rows: Joh 19:18 @10 built 'ere' / src 'here', italic {on, that, side}; Isa 48:5 @4 built 'what' / src 'would',
italic {would, happen}): READ DONE exit 0 (candidates 1, Joh yes, Isa NO with both lines); re-paste STOP; Joh made non-candidate → CHECK.

### Block HEADCHECK (GATE REF 50957fc0; READ-ONLY — writes only its run folder and log; no gate but the control)
```bash
set +H
L=~/edition_upgrade_runs/step4_headcheck_20261115.log
if [ -e "$L" ]; then echo "HEADCHECK RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=50957fc0
echo "GATE REF ${REF} - HEADCHECK step 4 head-consistency check (DESIGN 9.145 (2) / 9.146): eu_head_check.py --a src --b built, both copies' english_head against the build's base rule, stale-head candidates - NO GATE; hard control Joh 19:18 @10 must be a candidate; Isa 48:5 @4 printed for reading - READ-ONLY on both databases; writes only its run folder and log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "HEADCHECK RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
DA=~/edition_upgrade_runs/step9a_apply_20261115
D=~/edition_upgrade_runs/step4_headcheck_20261115
XS_SIZE=451964928
echo "python3: $(python3 --version 2>&1)"
# --- before the run: every miss is STOP ---
python3 scripts/eu_step.py pre --tag HEADCHK --ref "$REF" --dir "$D" --db "$B" --db "$S" || { echo "HEADCHECK RESULT: STOP - pre (line above; it also refuses a -journal beside either copy); nothing read"; exit 1; }
for f in "$DA/state.json" "$DA/dry.db"; do [ -s "$f" ] || { echo "HEADCHECK RESULT: STOP - missing or empty: $f"; exit 1; }; done
echo "=== built = what STEP9A-APPLY left (eu_step check against STEP9A-APPLY's prep + throwaway copy; read-only) ==="
python3 scripts/eu_step.py check --tag HEADCHK --built "$B" --dir "$DA" --written abp_surface || { echo "HEADCHECK RESULT: STOP - built is not STEP9A-APPLY's result (lines above)"; exit 1; }
n=$(stat -c %s "$S"); echo "src size: $n bytes (expect $XS_SIZE)"
[ "$n" = "$XS_SIZE" ] || { echo "HEADCHECK RESULT: STOP - src is not the size every declared figure was read against"; exit 1; }
st0=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' ')
mkdir "$D/check" || { echo "HEADCHECK RESULT: STOP - cannot make $D/check"; exit 1; }
# --- the check (src = a, built = b); the two named rows printed in full on both copies ---
echo "=== eu_head_check.py --a src --b built --out $D/check --show 'Joh 19:18@10' --show 'Isa 48:5@4' ==="
python3 scripts/eu_head_check.py --a "$S" --b "$B" --out "$D/check" --show "Joh 19:18@10" --show "Isa 48:5@4" > "$D/check.out" 2>&1; r=$?
cat "$D/check.out"
echo "head check exit $r (expect 0)"
[ "$r" = 0 ] && [ -n "$(sed -n '/^RESULT: HEAD CHECK WRITTEN/p' "$D/check.out")" ] || { echo "HEADCHECK RESULT: STOP - the check did not finish (exit $r; lines above; partial files kept in $D/check) - the log goes to the ruling chat"; exit 1; }
# --- control (DESIGN 9.146 (b)): Joh 19:18 @10 must be a candidate; Isa 48:5 @4 is read, not gated ---
FL=""
if [ -n "$(sed -n '/^SHOW Joh 19:18@10 - candidate: yes$/p' "$D/check.out")" ]; then echo "hard control Joh 19:18 @10 is a candidate: yes"; else echo "hard control Joh 19:18 @10 is a candidate: NO"; FL="$FL control-Joh19:18"; fi
echo "Isa 48:5 @4: $(sed -n 's/^SHOW Isa 48:5@4 - //p' "$D/check.out") (a result either way - DESIGN 9.146 (b); the src / built lines above are read in the ruling chat)"
echo "--- files in $D/check:"
ls -l "$D/check" | sed 's/^/  /'
st1=$(stat -c '%s %Y' "$B" "$S" | tr '\n' ' ')
echo "built and src: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO)"
[ "$st1" = "$st0" ] || { echo "HEADCHECK RESULT: STOP - built or src changed during a read-only run - report this"; exit 1; }
if [ -z "$FL" ]; then
  echo "HEADCHECK RESULT: READ DONE - every list in $D/check; candidates are read by member before any fix list (no figure is a gate)"; exit 0
fi
echo "HEADCHECK RESULT: CHECK -$FL (lines above; files in $D/check)"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### HEADCHECK reviewed (11/15) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - read-only run of the ruled step-4 head check (DESIGN 9.146 / 9.145 (2)); the repo guards run inside eu_step pre, same pattern as the cleared STEP4-DELTA; the one hard control is the one 9.146 names; no other figure is a gate."

### HEADCHECK ran (11/15, 21:02:58Z, PA HEAD 3a5f6d9c after a pull from e5f77e11, REF 50957fc0) — READ DONE, exit 0
Log `~/edition_upgrade_runs/step4_headcheck_20261115.log`; files `step4_headcheck_20261115/check/`. Python 3.13.1; PRE OK; CHECK OK
(395,014 / 219a3ebe7075); src 451,964,928 B. **Counts (none a gate):** stored ≠ base rule: src 4 / built 7; on both copies 4 (stored
heads differ on both: 0); src only 0; **built only 3 = CANDIDATES 2 + inputs differ 1.**
- **SHOW Joh 19:18 @10 — candidate: yes** (hard control met): src english 'one here on that side,', head 'here', italic_words
  'on,side,that', strongs '1782', recomputed 'here' — matches; built the same english / italic / strongs, head 'ere', recomputed 'here' — MISMATCH.
- **SHOW Isa 48:5 @4 — candidate: yes:** src english 'what would happen', head 'would', italic_words 'happen,whould', strongs '3739',
  recomputed 'would' — matches; built the same english / italic / strongs, head 'what', recomputed 'would' — MISMATCH.
  (The added-words value is 'happen,whould' on BOTH copies — the old edition's typo form, so 'would' is not an added word and the rule
  gives 'would'. CC's earlier {would, happen} worry does not arise.)
- Files: mismatch_a 4 lines `011b6a7a48e7ff6f4efa2354ffcd983a93d94e6f5bb778bd6247b031ce3f3b33`; mismatch_b 7 `7e32d7983533acd000e59ca292ca39e58b4c2553885c7a219bddd69656ac8e6e`;
  candidates 2 `890d8cd6bc4abbe9176149cf0bd68f4337d5ce24e4fe35641bc8403186044013`; both_differ 0 `6d8e0e3cb2a35dc3cb94c7499229a03c162ed52bf2b5b4523c417dbe97c5b896`.
- Built + src unchanged. HEADCHECK RESULT: READ DONE.
Reading (CC's, for the ruling): the 2 candidates are exactly the two known rows; over every row of both copies there is no other
stale head of this shape. The 1 "inputs differ" row and the 4 both-copies rows are in mismatch_a / mismatch_b on PA (not printed in
the log) — they are outside this check by design; the 1 is answered by the A english_head output.

### HEADCHECK files read (11/15; JP's scp of `step4_headcheck_20261115/`; local shas = PA's: mismatch_a 011b6a7a…, mismatch_b 7e32d798…, candidates 890d8cd6…, both_differ 6d8e0e3c…)
- **The 4 mismatching on BOTH copies, identical on both (so live's state, not an edition delta):** Jer 34:18 @18 'in front of me,'
  head 'front' (rule 'me'); Mal 3:6 @7 english '' head '' (rule None — an empty string where the rule gives none; strongs 241.2, the
  step-7 carried correction L10, §9.59); Mat 25:37 @8 'did we see' head None (rule 'see') and @9 'you' head 'see' (rule None) — the
  head sits on the neighbour, a relocation pass's shape. Outside this check by design.
- **The 1 "inputs differ":** Jos 2:4 @19 — built english 'I do not', head None, rule 'do' (src at @19: 'I know', a moved position — one
  of the 10 reorder verses, §9.93 (a); its english differs, so the check cannot judge it). Answered by the A english_head output; it is
  also one of the 32 non-swap cells at the moved positions (§9.143 (1)), so it is read when the A output's moved-position matching is laid.
- **The 2 candidates** = Isa 48:5 @4 and Joh 19:18 @10, as printed.

## Isa 48:5 @4 added words (§9.147 point 4, asked by the ruling chat) + a Joh 19:18 fix-draft finding (11/15, CC; local reads)

**Was the added-words value in scope of the typo correction? No.** The EU rows for Isa 48:5 are `english` @4 ("what whould happen" →
"what would happen") and `verses.text` only (`eu_batch_rows_20261103.tsv` :158-159); there is no `italic_words` row. On this lane
nothing italic-related comes from the feed: §9.44 "italic flag from the OLD set … nothing italic-related transplants this lane"; the
build takes italic_words from the old-edition metadata (build_words_from_abp.py :6, :339). So 'happen,whould' is the same on src and
built (live's value).
**What the source marks as added:** the pinned app feed (`abp_app_html/abp_app_slots_italic.tsv`, sha 7bd77385… = the charter §2 pin;
local copy checked) has Isa 48:5 slot 4 (G3739 α): english 'what  whould happen', italic 1, **italic_words 'whould happen'** — i.e. the
print marks "would happen" as added and "what" as the Greek word's own rendering. (Joh 19:18 slot 9, G1782 εντεύθεν: english 'one h ere
on that side,', italic_words 'on that side,' — consistent with the check's rule head 'here'.)
**The rule's head with 'would' as an added word:** `_head_word("what would happen", {"would","happen"})` = **'what'** (= built's stored
head); with the stored 'happen,whould' it is 'would' (= src's head) — tested locally with the build's function.
No cause asserted. CC's reading, for the ruling: src's 'would' rests on the typo inside the added-words value ('whould' ≠ 'would', so
'would' counts as a real word); with the added words as the feed marks them, built's 'what' is the rule's head. Nothing written for
this row until ruled.
**Finding for the Joh 19:18 @10 fix draft:** `eu_batch_insert.py` takes `--rows` (a new file) and the group `typo` exists, but its
end check counts ALL `EU-%` rows on the copy against the batch size (:146-151: "EU- rows on the copy: N (expected len(rows))"). Built
already holds the 344 EU rows, so a 1-row batch would end "MISMATCH" after writing. Using it needs a small code change (count only
the rows this run inserts), or another route — to be stated in the draft. Its `created` date is fixed at 2026-11-02 (:33).

### Ruling (11/15, §9.147) — HEADCHECK READ DONE; candidates exactly the 2; §9.144 (5) stands for both; the fix block may be drafted
CC's note to the ruling, before drafting (recorded at f75e2fac, "Isa 48:5 @4 added words"): the pinned feed marks "whould happen" as the
added words at Isa 48:5 slot 4; with 'would' as an added word the build's rule gives 'what' (= built's head), and `_strip_italic_heads`
exists so a head is never an added word. Writing 'would' would set the head to a word the print marks as added; the follow-up
italic_words correction would then make it stale again. Raised to the ruling chat before the Isa row is put in a fix file; the Joh
19:18 @10 row is drafted meanwhile. The 1 inputs-differ row and the 4 both-copies rows were already read (adee2a15, "HEADCHECK files read").

## Joh 19:18 @10 head fix — code part (11/15, CC; §9.148 (3)-(5)) — in the working tree, NOT committed until ruled

**Route:** the lane's existing correction route (§9.145 item 3), with the one code change §9.148 (4) asks for.
- `scripts/eu_batch_insert.py`: the end check now counts only the EU rows THIS run adds (`n_after − n_before == len(rows)`, printed as
  "EU- rows on the copy: N (before M; this batch adds K, expected K)"); before, it compared ALL EU rows on the copy to the batch size, so
  a later batch on built (344 EU rows already) would read MISMATCH after writing. New `--created` (default the first batch's
  2026-11-02, so the first-batch behaviour is unchanged); the Joh row uses 2026-11-15. Nothing else changes (the clash check — any row
  of any status on the same key STOPs — the sha / count pins, the dry run).
- NEW fixture `tests/fixtures/edition_upgrade/eu_batch_rows_heads_20261115.tsv` (+ `.sha256`, `4ba1d7bc1292b8bee8529bdf3f661e417153de243d88a108a33136be1975bb60`):
  one row — Joh 19 18 10 `english_head` source 'ere' → corrected 'here', ledger EU-Joh19:18, group `typo` (§9.74). **Why 'here':**
  english, italic_words ('on,side,that') and strongs ('1782') are equal on both copies; src's stored head 'here' = the build's rule; the
  pinned feed's added words at this slot are 'on that side,' (so the rule's head is the Greek word's own 'here'); built's 'ere' is the
  rule's head of the typo text "one h ere" the EU english row corrected (HEADCHECK SHOW lines; §9.147 / §9.148 (3)).
- NEW `tests/test_eu_batch_insert.py` (6): first batch on a copy with no EU rows → INSERTED (old behaviour); second batch on a copy
  already holding EU rows → INSERTED (fails under the old end check — proven); dry run writes nothing; `--created` sets the date,
  default 2026-11-02; an existing key of any status STOPs; wrong sha / count STOP; the committed heads file = its pin and holds exactly
  the one row. In ci.yml + pre-commit; 81 test files pass.
**Then (after the ruling + commit = new code REF), the PA write block, drafted on that REF:** dry on a throwaway copy (eu_step prep:
words, abp_corrections, kjv_words, bsb_words), then on built: `eu_batch_insert.py --rows <heads file> --sha256 4ba1d7bc… --expect 1
--created 2026-11-15 --apply` → `apply_abp_corrections.py --apply` (guarded; only the cell holding 'ere' is written, every other active
row reads already-applied) → `build_rendering_norm.py` (step 11's recompute: only Joh 19:18 @10's english_head_norm may move) → eu_step
check (written: words, abp_corrections, and the rendering-norm tables = the throwaway; every other table + schema unchanged) and a
row read at Joh 19:18 @10 (head 'here', norm 'here'). Before-copy saved by prep. Then the raw delta re-run (read-only).

### Joh 19:18 fix code reviewed (11/15) — REVIEW: ESCALATE (code change); code sound; two gaps in the planned PA block
Verdict line verbatim: "REVIEW: ESCALATE - this is a code change (eu_batch_insert.py, a new fixture and a new test), so under §9.90 it goes to the ruling chat. The code looks sound. Two gaps in the planned PA block need settling before it is drafted."
Confirmed: the end check counts only this run's rows (the script's only write is the one INSERT); `--created` default keeps the first
batch; the fixture row exact, its header = `load()`, group `typo` in REASON; no existing english_head row at Joh 19:18 @10 in the EU
files or the active lists (only english @10 and verses.text); apply_abp_corrections applies an english_head row at 'ingest' only where
the cell holds 'ere'. Notes: a non-"EU-" ledger_ref would read MISMATCH after writing (not this file); the "EU- rows on the copy" line's
wording changed.
**Gap 1 — build_rendering_norm.py rewrites three whole columns** (words.english_head_norm, kjv_words / bsb_words word_norm;
recompute_norms :57-80, no scope option on the command line). **CC's answer, for the ruling:**
- `number_fold.py` and `build_rendering_norm.py` are UNCHANGED since step 11 ran on built (`git diff --stat 006e16ba HEAD` on both: empty;
  STEP11-APPLY ran at REF 006e16ba, §9.107 closing), and no step since has written built's words / kjv_words / bsb_words (every stage-E
  write was checked by eu_step against its prep). So a full re-run re-writes identical values everywhere except the one fixed head.
- The block proves it, not assumes it: on the throwaway first and then on built, before → after content delta (eu_step delta) on
  words (key verse_id+position), kjv_words and bsb_words — expected exactly 2 cells, both at Joh 19:18 @10 (english_head 'ere' → 'here',
  english_head_norm 'ere' → 'here'), 0 elsewhere; and eu_step check with written = words, abp_corrections (kjv_words / bsb_words must
  then match their prep digests, i.e. unchanged).
- Rejected alternative: an english_head_norm row in the correction file. In a rebuild, corrections apply at step 7 (finish_rebuild)
  before step 11 fills the norm column, so that row would find the cell empty and LOUD-SKIP (apply_abp_corrections exits 1) — a trap
  for every future rebuild.
**Gap 2 — apply_abp_corrections.py's expected counts** (applied 1 · already-applied N · skipped 0) must be traced to built's last apply
log before the block is drafted; and it appends to `<db>.corrections.log` beside built (a new or appended file — the block will say so).
CC traces both when drafting the block.

## HEADFIX drafted (11/15, GATE REF 0cad6894; PA pulls first) — Joh 19:18 @10 head fix on built (§9.148 (3) / §9.149), for the ruling chat (a write)

WRITES built: words (2 cells: Joh 19:18 @10 english_head + english_head_norm 'ere' → 'here') and abp_corrections (1 row); appends to
built's `.corrections.log` (a write outside the run folder, declared, §9.149). **Chain:** `eu_batch_insert.py --rows <heads file>
--sha256 4ba1d7bc… --expect 1 --created 2026-11-15` (dry, then --apply) → `apply_abp_corrections.py --only words` (dry, then --apply) →
`build_rendering_norm.py` (in full, §9.149 (b)). **Declared figures:** heads file sha 4ba1d7bc…; built abp_corrections
active|retired|superseded **374|23|6** before (J run 11/6, DR :2490-2492 "AFTER 374 / 23 / 6"; the committed active list
`abp_corrections_active_built_20261106.txt` = 374 lines: 250 word cells + 124 verses.text) → **375|23|6** after; apply
"would apply 1 · already-applied 250 · LOUD-SKIPPED 0" then "applied 1 · already-applied 250 · LOUD-SKIPPED 0" (250 = the active word
rows in that list; the J run's `--only words` read "already-applied 248" with its 2 rows pending, DR :2492); the cell before
'one here on that side,|ere|ere' (HEADCHECK SHOW + eu_step state), after '…|here|here'.
**Before any write (STOP, built untouched):** pre (REF 0cad6894); heads-file sha; built = STEP9A-APPLY's result; the cell and the counts as
declared; prep (`--copy verses,words,abp_corrections,kjv_words,bsb_words --save words:english_head+english_head_norm --save
abp_corrections`) → before.db = the restore source, sha printed; the WHOLE chain on the throwaway: insert INSERTED, apply lines as
declared, the cell and 375|23|6; built → throwaway delta: words exactly 1 row (Joh 19:18 @10, exactly english_head + english_head_norm
('ere','ere') → ('here','here')), kjv_words + bsb_words 0 (`--zero`), abp_corrections 1 ADDED; the table + index definitions of the four
tables built = throwaway (the norm script creates indexes if missing); `same`. **Write** = the chain on built. **After (CHECK naming
before.db):** chain exit 0, INSERTED, the apply line, the cell, 375|23|6, eu_step check with written = words, abp_corrections (= the
throwaway; kjv_words / bsb_words and every other table + schema = prep), the log's size.
**New "built =" reference for later blocks (§9.149):** `eu_step check --dir ~/edition_upgrade_runs/step4_headfix_20261115 --written
words,abp_corrections` (this block's prep + throwaway) replaces the STEP9A-APPLY guard.
**Knock-on (for the swap commit):** the cert_invariants `abp_corrections_active` pin 374 → 375 and the active-list fixture re-pinned with
§4.7's re-adjudication at the swap (not now).
Local test (WSL, fake HOME, clone at 44f58bf1; made-up built with 374 active corrections (250 word cells already applied + 124
verses.text), 23 retired, 6 superseded, kjv / bsb word tables with their norm indexes, and a 9a prep): DONE exit 0 (dry + built chain
lines exactly as declared, delta 1 / 0 / 1, definitions equal, check OK); re-paste STOP; a second run on the fixed copy STOPs at the
"built = STEP9A-APPLY" guard, built byte-identical; a copy WITHOUT the kjv norm index → "definitions … NO" → STOP before the write.
(First test run, before the copies had the indexes: the post-write check caught the two new indexes as CHECK — the pre-write
definitions check was added from that.)

### Block HEADFIX (GATE REF 0cad6894; WRITES built: words 2 cells + abp_corrections 1 row) — for the ruling chat
```bash
set +H
L=~/edition_upgrade_runs/step4_headfix_20261115.log
if [ -e "$L" ]; then echo "HEADFIX RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=0cad6894
echo "GATE REF ${REF} - HEADFIX Joh 19:18 @10 english_head 'ere' -> 'here' on BUILT (DESIGN 9.144 (5) / 9.147 / 9.148 (3) / 9.149): eu_batch_insert (the 1-row heads file) -> apply_abp_corrections --only words -> build_rendering_norm, dry on a THROWAWAY copy first - WRITES built: words (2 cells) + abp_corrections (1 row); appends TWO reports (the apply's dry run and its write) to built's .corrections.log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "HEADFIX RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
DA=~/edition_upgrade_runs/step9a_apply_20261115
D=~/edition_upgrade_runs/step4_headfix_20261115
F=tests/fixtures/edition_upgrade/eu_batch_rows_heads_20261115.tsv
E="python3 scripts/eu_step.py"
# --- declared figures ---
XF=4ba1d7bc1292b8bee8529bdf3f661e417153de243d88a108a33136be1975bb60     # the heads file (DESIGN 9.149)
XCORR="374|23|6"                 # abp_corrections active|retired|superseded on built (J run 11/6, DR :2490-2492; active list 20261106 = 374 lines)
XCORR_AFTER="375|23|6"           # + the 1 row (DESIGN 9.149)
XAPPLY="applied 1 · already-applied 250 · LOUD-SKIPPED 0"     # 250 = the active word-cell rows (the 20261106 active list: 250 words + 124 verses.text)
XDRYAPPLY="would apply 1 · already-applied 250 · LOUD-SKIPPED 0"
XCELL_BEFORE="one here on that side,|ere|ere"
XCELL_AFTER="one here on that side,|here|here"
cell() { sqlite3 -readonly "$1" "SELECT w.english || '|' || w.english_head || '|' || w.english_head_norm FROM words w JOIN verses v ON v.id = w.verse_id WHERE v.book='Joh' AND v.chapter=19 AND v.verse=18 AND w.position=10"; }
corr() { sqlite3 -readonly "$1" "SELECT (SELECT count(*) FROM abp_corrections WHERE status='active') || '|' || (SELECT count(*) FROM abp_corrections WHERE status='retired') || '|' || (SELECT count(*) FROM abp_corrections WHERE status='superseded')"; }
chain() {   # $1 = db, $2 = output prefix: insert -> apply (words) -> norm; each step's output kept
  python3 scripts/eu_batch_insert.py "$1" --rows "$F" --sha256 "$XF" --expect 1 --created 2026-11-15 > "$2.insert_dry.out" 2>&1 || return 11
  python3 scripts/eu_batch_insert.py "$1" --rows "$F" --sha256 "$XF" --expect 1 --created 2026-11-15 --apply > "$2.insert.out" 2>&1 || return 12
  python3 scripts/apply_abp_corrections.py "$1" --only words > "$2.apply_dry.out" 2>&1 || return 13
  python3 scripts/apply_abp_corrections.py "$1" --only words --apply > "$2.apply.out" 2>&1 || return 14
  python3 scripts/build_rendering_norm.py "$1" > "$2.norm.out" 2>&1 || return 15
  return 0
}
# --- before any write: every miss is STOP, built untouched ---
$E pre --tag HEADFIX --ref "$REF" --dir "$D" --db "$B" --keep ~/bible-db/bible_edupg_test_built_pre_8b_20261106.db --keep ~/bible-db/bible_edupg_test_built_pre_digits_20261105.db || { echo "HEADFIX RESULT: STOP - pre (line above); built untouched"; exit 1; }
dk=$(du -sk ~ 2>/dev/null | cut -f1); echo "home in use: $dk KB (this run adds one throwaway copy of verses + words + abp_corrections + kjv_words + bsb_words and a small before.db)"
s=$(sha256sum < "$F" | cut -d' ' -f1); echo "heads file $F: sha256 $s (expect $XF)"; [ "$s" = "$XF" ] || { echo "HEADFIX RESULT: STOP - not the committed heads file; built untouched"; exit 1; }
echo "=== built = what STEP9A-APPLY left (eu_step check against STEP9A-APPLY's prep + throwaway copy; read-only) ==="
$E check --tag HEADFIX --built "$B" --dir "$DA" --written abp_surface || { echo "HEADFIX RESULT: STOP - built is not STEP9A-APPLY's result (lines above); built untouched"; exit 1; }
c=$(cell "$B"); echo "built Joh 19:18 @10 (english|head|norm): $c (expect $XCELL_BEFORE)"; [ "$c" = "$XCELL_BEFORE" ] || { echo "HEADFIX RESULT: STOP - the cell is not as declared; built untouched"; exit 1; }
c=$(corr "$B"); echo "built abp_corrections active|retired|superseded: $c (expect $XCORR)"; [ "$c" = "$XCORR" ] || { echo "HEADFIX RESULT: STOP - abp_corrections is not as recorded; built untouched"; exit 1; }
[ -e "$B.corrections.log" ] && echo "built's corrections log before: $(stat -c %s "$B.corrections.log") bytes" || echo "built's corrections log before: none (the apply will create it)"
echo "=== prep: state of built, before.db (restore source: words' english_head + english_head_norm by row id, and abp_corrections whole) and a THROWAWAY copy ==="
$E prep --tag HEADFIX --built "$B" --dir "$D" --copy verses,words,abp_corrections,kjv_words,bsb_words --save words:english_head+english_head_norm --save abp_corrections || { echo "HEADFIX RESULT: STOP - prep (line above); built untouched"; exit 1; }
echo "before.db (restore source): sha256 $(sha256sum < "$D/before.db" | cut -d' ' -f1)"
VID=$(sqlite3 -readonly "$B" "SELECT id FROM verses WHERE book='Joh' AND chapter=19 AND verse=18"); echo "Joh 19:18 verse id on built: $VID"
# --- the same chain on the THROWAWAY copy first: it must end exactly as declared ---
echo "=== the chain on the THROWAWAY copy $D/dry.db ==="
chain "$D/dry.db" "$D/dry"; rc=$?
for x in insert apply_dry apply norm; do echo "--- dry $x:"; grep -E "RESULT|abp_corrections (before|after)|EU- rows|summary:|STOP|recomputed|Joh 19:18" "$D/dry.$x.out" | sed 's/^/  /'; done
[ "$rc" = 0 ] || { echo "HEADFIX RESULT: STOP - the chain failed on the throwaway copy at step $rc (outputs $D/dry.*.out); built untouched"; exit 1; }
grep -qF "RESULT: INSERTED - counts as expected" "$D/dry.insert.out" && grep -qF "$XDRYAPPLY" "$D/dry.apply_dry.out" && grep -qF "$XAPPLY" "$D/dry.apply.out" || { echo "HEADFIX RESULT: STOP - the throwaway chain's lines are not the declared ones; built untouched"; exit 1; }
c=$(cell "$D/dry.db"); echo "throwaway Joh 19:18 @10: $c (expect $XCELL_AFTER)"; [ "$c" = "$XCELL_AFTER" ] || { echo "HEADFIX RESULT: STOP - the throwaway cell is not as declared; built untouched"; exit 1; }
c=$(corr "$D/dry.db"); echo "throwaway abp_corrections: $c (expect $XCORR_AFTER)"; [ "$c" = "$XCORR_AFTER" ] || { echo "HEADFIX RESULT: STOP - the throwaway's corrections counts are not as declared; built untouched"; exit 1; }
echo "=== built -> throwaway, every cell (words keyed verse_id+position; kjv_words / bsb_words must not differ; abp_corrections by id) ==="
$E delta --tag HEADFIX --a "$B" --b "$D/dry.db" --table words:verse_id+position --out "$D/delta_words.tsv" --show 5 > "$D/delta_words.out" 2>&1; cat "$D/delta_words.out"
$E delta --tag HEADFIX --a "$B" --b "$D/dry.db" --table kjv_words --table bsb_words --out "$D/delta_kjvbsb.tsv" --zero > "$D/delta_kjvbsb.out" 2>&1; rk=$?; cat "$D/delta_kjvbsb.out"
$E delta --tag HEADFIX --a "$B" --b "$D/dry.db" --table abp_corrections --out "$D/delta_corr.tsv" --show 5 > "$D/delta_corr.out" 2>&1; cat "$D/delta_corr.out"
nw=$(($(wc -l < "$D/delta_words.tsv") - 1)); nc=$(($(wc -l < "$D/delta_corr.tsv") - 1))
w1=$(awk -F'\t' -v k="($VID, 10)" -v was="('ere', 'ere')" -v now="('here', 'here')" 'NR > 1 && $2 == "CHANGED" && $3 == k && $4 == "english_head,english_head_norm" && $5 == was && $6 == now' "$D/delta_words.tsv" | wc -l)
c1=$(awk -F'\t' 'NR > 1 && $2 == "ADDED"' "$D/delta_corr.tsv" | wc -l)
echo "words: $nw row(s) differ (expect 1) - the Joh 19:18 @10 row with exactly english_head + english_head_norm 'ere' -> 'here': $w1 (expect 1); kjv_words + bsb_words differ: exit $rk (expect 0); abp_corrections: $nc row(s) differ, added $c1 (expect 1, 1)"
[ "$nw" = 1 ] && [ "$w1" = 1 ] && [ "$rk" = 0 ] && [ "$nc" = 1 ] && [ "$c1" = 1 ] || { echo "HEADFIX RESULT: STOP - the throwaway differs from built by more or other than the 2 cells + 1 row; built untouched"; exit 1; }
SQ="SELECT type || '|' || name || '|' || tbl_name || '|' || coalesce(sql, '') FROM sqlite_master WHERE tbl_name IN ('words','abp_corrections','kjv_words','bsb_words') ORDER BY type, name"
sqlite3 -readonly "$B" "$SQ" > "$D/schema_built.txt"; sqlite3 -readonly "$D/dry.db" "$SQ" > "$D/schema_dry.txt"
echo "table + index definitions of words / abp_corrections / kjv_words / bsb_words, built = throwaway after the chain: $(cmp -s "$D/schema_built.txt" "$D/schema_dry.txt" && echo yes || echo NO) ($(wc -l < "$D/schema_built.txt") entries)"
cmp -s "$D/schema_built.txt" "$D/schema_dry.txt" || { diff "$D/schema_built.txt" "$D/schema_dry.txt"; echo "HEADFIX RESULT: STOP - the chain changed a table or index definition on the throwaway; built untouched"; exit 1; }
$E same --tag HEADFIX --built "$B" --dir "$D" || { echo "HEADFIX RESULT: STOP - built changed since prep (lines above); built untouched"; exit 1; }
# --- the write ---
echo "=== the chain on BUILT ($B) - writes words (2 cells) + abp_corrections (1 row); appends to $B.corrections.log ==="
chain "$B" "$D/built"; r=$?
for x in insert apply_dry apply norm; do echo "--- built $x:"; grep -E "RESULT|abp_corrections (before|after)|EU- rows|summary:|STOP|recomputed|Joh 19:18" "$D/built.$x.out" 2>/dev/null | sed 's/^/  /'; done
echo "chain on built: exit $r (expect 0)"
# --- after the write: every miss is CHECK ---
FL=""
[ "$r" = 0 ] || FL="$FL chain-step-$r"
grep -qF "RESULT: INSERTED - counts as expected" "$D/built.insert.out" 2>/dev/null || FL="$FL insert"
grep -qF "$XAPPLY" "$D/built.apply.out" 2>/dev/null || FL="$FL apply"
c=$(cell "$B"); echo "built Joh 19:18 @10 after: $c (expect $XCELL_AFTER)"; [ "$c" = "$XCELL_AFTER" ] || FL="$FL cell"
c=$(corr "$B"); echo "built abp_corrections after: $c (expect $XCORR_AFTER)"; [ "$c" = "$XCORR_AFTER" ] || FL="$FL corrections"
CHK=$($E check --tag HEADFIX --built "$B" --dir "$D" --written words,abp_corrections 2>&1); k=$?; echo "$CHK"; [ "$k" = 0 ] || FL="$FL check"
echo "built's corrections log after: $(stat -c %s "$B.corrections.log" 2>/dev/null) bytes (two reports appended - the apply's dry run and its write; a write outside the run folder, declared - DESIGN 9.149; not restorable from before.db)"
if [ -z "$FL" ]; then
  echo "HEADFIX RESULT: DONE - built Joh 19:18 @10 english_head + english_head_norm 'ere' -> 'here'; abp_corrections 374 -> 375 active (EU-Joh19:18 english_head); built = the throwaway (check OK: words + abp_corrections = the dry copy, every other table incl. kjv_words / bsb_words + schema unchanged). Restore source: $D/before.db. Later blocks' 'built =' guard: eu_step check --dir $D --written words,abp_corrections"; exit 0
fi
echo "HEADFIX RESULT: CHECK -$FL differ (lines above). Restore source: $D/before.db (words english_head + english_head_norm by row id; abp_corrections whole)"; exit 1
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### HEADFIX reviewed (11/15) — REVIEW: ESCALATE (a write, §9.90); 0 DEFECT, 2 GAP, 6 NOTE
Verdict line verbatim: "REVIEW: ESCALATE - HEADFIX writes built (words 2 cells, abp_corrections 1 row, and appends to built's .corrections.log), so it is outside reviewer scope under §9.90. I found no defects in how it works: 0 DEFECT, 2 GAP, 6 NOTE."
Confirmed: nothing writes built before the "=== the chain on BUILT" line; the delta awk matches eu_step's TSV writer (key repr,
column order, before/after repr); the definitions check is needed (the norm script creates indexes / columns if missing); every
post-write miss ends in one CHECK naming before.db; the replacement guard is stated.
- **GAP 1 (tracing):** 374|23|6 and "already-applied 250" rest on the J run's record prose (DR :2490-2492, summarising
  `~/edition_upgrade_runs/joh1426_rows_20261106.log`, PA) and the committed active list (374 lines = 124 verses.text + 250 word cells);
  retired 23 / superseded 6 only in the prose; the list does not carry applied_at. Each figure is read live and STOPs before the write
  on a miss. No step after the J run wrote abp_corrections (every later write's eu_step check left it out of its written list and found
  it unchanged). For the ruling: accept the fixture + prose, or a PA read of the J log first.
- **GAP 2 — fixed in the block text:** the apply's DRY run also appends a report to `<db>.corrections.log` (apply_abp_corrections.py
  :144-146), so built's log gets TWO reports; the GATE REF line and the final line now say so ("not restorable from before.db").
- Notes: (1) before the write the delta covers words / kjv_words / bsb_words / abp_corrections; verses is copied but not compared
  (`--only words` never writes verses, :89) — other tables only by the post-write check (a CHECK, not a STOP); (2) the norm script
  rewrites whole columns, so built's -journal is about their size while the throwaway + before.db sit in home — the dry run on the
  throwaway has the same footprint first; only "home in use" is printed; (3) before.db covers the 2 cells + the row; (4) the
  cert_invariants pin 374 → 375 + the active-list fixture at the swap; (5) the cell's before value traced to HEADCHECK and read live;
  (6) PA pulls to ≥ 0cad6894 first; no scripts/tests push while the block waits.

## HEADFIX cleared (11/15, ruling chat §9.150) — NOT yet run
HEADFIX cleared to run at GATE REF 0cad6894, block as printed in "Block HEADFIX" above, after PA pulls. GAP 1 ruled (fixture +
record prose accepted for 374|23|6 and 250). Ruling chat's own check recorded: Joh 19:18 has no row in
abp_surface_fill_20261115.tsv (4,411 rows; 43 Joh, none at 19:18) — the 9c pin is not made stale. Conditions: JP checks PA disk
headroom first; any CHECK/STOP goes to the ruling chat as printed. Session wrapped here (context); the successor runs nothing new
until HEADFIX's log is read. Next guard after it runs: `eu_step check --dir ~/edition_upgrade_runs/step4_headfix_20261115 --written words,abp_corrections`.

### HEADFIX ran (11/16, 03:25:51Z, PA HEAD 842c79ee, REF 0cad6894) — STOP before the write, exit 1; built untouched (to the ruling chat)
From JP's terminal paste (the echo of the pasted block text is overwritten again, as on STEP9B; the run's output is complete through
"exit=1"; the PA log file is the record). PRE OK (repo guards, both rollback copies, run folder made); home in use 7,560,320 KB; heads
file `4ba1d7bc…bb60` = expect; CHECK OK against STEP9A-APPLY (149 + schema 0; abp_surface 395,014 / `219a3ebe7075`; no journal; repo
clean); cell `one here on that side,|ere|ere` = expect; abp_corrections 374|23|6 = expect; built's .corrections.log 47,168 B before;
PREP OK (state.json 150 tables / 3,810,506 rows / 300 schema entries in 35 s; before.db words 626,309 + abp_corrections 403 rows,
10,231,808 B, sha256 `da47ce8c49968f2df564cecada7367336193eaa94a55483b182297caedd957f3`; dry.db verses / words / abp_corrections /
kjv_words / bsb_words digests = built's, 201,183,232 B); Joh 19:18 verse id 27195.
On the THROWAWAY: insert = declared (374 → 375 active, EU- rows 345 = before 344 + 1, "RESULT: INSERTED - counts as expected");
**apply dry: "would apply 1 · already-applied 249 · LOUD-SKIPPED 1"** (declared: would apply 1 · already-applied 250 · LOUD-SKIPPED 0;
Joh 19:18 @10 english "already applied (ok)", english_head "would apply") → the apply exits 1 on any skip (apply_abp_corrections.py
:148) → chain step 13 → **"HEADFIX RESULT: STOP - the chain failed on the throwaway copy at step 13 … built untouched"**, exit=1. The
apply / norm steps never ran (no dry.apply.out / dry.norm.out). The block's grep filter does not show the `!! SKIP` line (:103 / :113 /
:129), so the skipped row is not in the log; it is in `step4_headfix_20261115/dry.apply_dry.out` on PA.
CC local read (no PA run; no cause asserted): of the 250 active word rows (english 121, english_head 109, greek_pos 9, strongs 4,
strongs_base 4, bracket_id 3), 25 have a src → built cell in STEP4-DELTA's words_cells.tsv — the 23 EU rows among them hold their
corrected_value on built; the other 2 are Joh 14:26 @3 bracket_id / greek_pos (S-joh14:26, src None → built 1 / 3, no value on file to
compare); none sits in one of the 10 moved verses. The other 225 are equal on src and built and cannot be read locally.
Nothing to restore (no write reached built). Next: a read-only read of the dry apply output + built's own .corrections.log history
(was the skip there before HEADFIX?) + `eu_step same` (built = prep) — reviewer first, log to the ruling chat. HEADFIX is not re-run
as printed: its log-exists guard STOPs, and the declared "already-applied 250 · LOUD-SKIPPED 0" no longer fits; any re-run is a
changed block → reviewer → ruling chat.

### Block HFREAD (READ-ONLY — writes only its own log; no gate) — why HEADFIX stopped
```bash
set +H
L=~/edition_upgrade_runs/headfix_stop_read_20261116.log
if [ -e "$L" ]; then echo "HFREAD RESULT: STOP - log already exists (kept as is): $L"; else
( set -uo pipefail
echo "HFREAD - READ-ONLY: why HEADFIX stopped (dry apply LOUD-SKIPPED 1) - writes only this log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "HFREAD RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
export PYTHONIOENCODING=utf-8 LC_ALL=C
B=~/bible-db/bible_edupg_test_built_20261102.db
D=~/edition_upgrade_runs/step4_headfix_20261115
echo "=== 1. the dry apply's output on the throwaway, every line except 'already applied (ok)' ==="
grep -v 'already applied (ok)' "$D/dry.apply_dry.out"
echo "=== 2. built's corrections log: size (expect 47168, as before HEADFIX) and every summary / !! line with its line number ==="
stat -c %s "$B.corrections.log"
grep -nE 'summary:|!! ' "$B.corrections.log"
echo "=== 3. built = HEADFIX's prep (read-only, expect differences 0) ==="
python3 scripts/eu_step.py same --tag HFREAD --built "$B" --dir "$D"; echo "same exit: $? (expect 0)"
echo "=== 4. files in the HEADFIX run folder ==="
ls -l "$D"
echo "=== 5. the HEADFIX log file: line count and its last 3 lines ==="
wc -l < ~/edition_upgrade_runs/step4_headfix_20261115.log; tail -3 ~/edition_upgrade_runs/step4_headfix_20261115.log
echo "HFREAD RESULT: READ DONE"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
```

### HFREAD reviewed (11/16) — REVIEW: CLEAR
Verdict line verbatim: "REVIEW: CLEAR - read-only diagnostic. It writes only its own new log (the block stops if that log already exists), it is not a gate, and it has no `!` except inside the `[ -e ]` test."
Confirmed: `eu_step same` = mode_same (:283-294), reads state.json and opens built via ro() (mode=ro + query_only); `--tag` only
prefixes printed lines; the grep patterns match apply_abp_corrections.py's SKIP (:103 / :113 / :129), summary (:137-138) and warning
(:140) lines; the apply appends to `<db>.corrections.log` (:144-146), so section 2 reads built's own history. Note: if
`dry.apply_dry.out` were absent, section 1 prints "No such file" — read as file-not-found, not as no SKIP line. No figure is a gate.
