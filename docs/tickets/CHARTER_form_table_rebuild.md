# CHARTER — printed-form table (abp_surface) full rebuild

**Status: DRAFT — nothing in here runs until (1) Step 0 re-pins the numbers on PA and
(2) JP/reviewer sign off on the charter.** Written 2026-08-12 from
`docs/handoffs/HANDOFF_form_lane.md` (numbers banked 2026-08-09 — treat every figure below
as stale until Step 0 returns it fresh). Every script name, flag, and run order below was
verified against the repo scripts' own docstrings and `/rebuild-words` steps 8.3/9 on
2026-08-12. Standing law read at charter time: `feedback_correction_lane_lessons` (all five
rules applied below), `feedback_audit_tools_must_fail`, `feedback_verify_before_claiming`.

## The job
The 8/8 wordpos apply re-ran the header build before the form table was rebuilt, and the
form table lost coverage for name slots: **2,361 → 2,528 slots with no printed form (+167,
banked 8/9)**. `backfill_pn_surface.py` cannot repair it — its 8/9 dry-run added 0 rows
(2,543 refusals): it only reads scrape rows with a BLANK Strong's number, so numbered names
(Jesus G2424, Paul, Peter) were never in its reach. Their forms come only from
`build_abp_surface.py`, which rebuilds the whole table. **So this is a rebuild-class lane
with its own gate (gate F). Gate A of the header lane is NOT re-scoped** (reviewer ruling
2026-08-09) — "form table untouched" is what made that session's findings trustworthy.

Downstream, already proven, waiting on this and NOT part of this charter:
header repair (gate C green on a copy 8/9) → batch 3 galilee (exactly 73 rows,
`7ed55e38`) → ABP-tab routing.

## Standing guards in this lane's path (correction-lane rule 2 — listed at charter time)
- `health_check` floors `abp_surface` at **389,244** rows — a rebuild that skips either
  backfill trips it (that's its purpose; 2026-07-16 miss).
- Both backfills use INSERT OR IGNORE on (verse_id, position) — not a blocker here: the
  full rebuild replaces the table first, so the backfills see a fresh table. Their own
  docstrings ORDER them after a full rebuild.
- `build_abp_surface.py` writes ONLY the `abp_surface` table, never words/verses (its
  docstring; gate F still asserts it — F6).
- `gate_greek_header.py` pins will legitimately move when the form table changes — that
  gate belongs to the header lane and runs there, on the repaired baseline. A form-lane
  run of it is not owed and would fail by design.
- No words rebuild happens here, so the `/rebuild-words` chain (retirement, TIPNR,
  step 8.3) is NOT in this lane's path.

## Step 0 — re-pin the numbers on live (read-only, before anything else)
All commands run by JP on PA. Expected values are the 8/9 banked figures; a different
number is not a stop, it re-pins the charter — but a WILDLY different number (wrong sign,
wrong magnitude) is a stop-and-look.

0a. Name slots with no printed form (banked: 2,528) + total name slots in the same read:
```
sqlite3 ~/bible-db/bible.db "SELECT (SELECT count(*) FROM words w WHERE w.is_pn=1 AND NOT EXISTS(SELECT 1 FROM abp_surface s WHERE s.verse_id=w.verse_id AND s.position=w.position)) AS pn_no_form, (SELECT count(*) FROM words WHERE is_pn=1) AS pn_total;"
```

0b. Table total vs the floor (banked: ≥ 389,244):
```
sqlite3 ~/bible-db/bible.db "SELECT count(*) AS abp_surface_total FROM abp_surface;"
```

0c. Two-word forms in the form table, with the known-positive control IN the query
(separator is U+00A0 = char(160), never a plain space — a plain-space probe reads 0
against rows on screen; this lane paid for that twice, commit `5a533f9b` + 2026-08-09):
```
sqlite3 ~/bible-db/bible.db "SELECT 'nbsp_forms', count(*) FROM abp_surface WHERE form LIKE '%'||char(160)||'%' UNION ALL SELECT 'CONTROL must be >=1', count(*) FROM pn_greek_identity WHERE greek_lemma LIKE '%'||char(160)||'%';"
```
If the control row reads 0, the probe is void, not a clean count — settle the separator
byte with `hex()` on a row you can see before reporting anything.

0d. **Member list of the lost slots (the landings check depends on this).** The +167 is a
set difference against a pre-8/5 backup (live's own history can't produce it).
**Reviewer pin 3 (2026-08-12): the reference backup is PRE-REGISTERED here — named by JP
BEFORE the diff runs, never chosen after seeing live's numbers.**

> **PIN FAILED — STOP RECORDED 2026-08-13 (JP-run reads).** Self-check results, all with
> the identical 0a predicate: Aug 6 ride file **2,659** · Aug 5 ride file (unpacked)
> **2,659** · live **2,528**. Live matching the banked 2,528 proves the predicate is the
> banked one, so the files are truly not the baseline: **the copy that read 2,361 has
> rotated out of `~/db_backups`** (pre-8/5 bible.db entries are info-slips only). Also
> on record and unexplained: the 8/5/8/6 copies read WORSE than live — the banked
> "2,361 until the 8/8 write" timeline is incomplete. Step 0d is BLOCKED pending a
> reviewer ruling on the recommendation below.
>
> **CC recommendation to the reviewer:** re-pin the baseline to the Aug 6 ride file
> (2,659) and redefine F3's arrivals list as "slots covered on 8/6, uncovered live" —
> the loss across the 8/8 ride specifically, which is this lane's defect. Keep the F1
> ceiling at ≤ 2,361 unchanged (it's the banked pre-8/5 figure and the full rebuild is
> expected to beat every one of these numbers). Add 2,659 to the reconciliation table
> as its own row. The 2,659-vs-2,528 improvement between 8/6 and live gets pinned as a
> fourth open number, not absorbed.
>
> Superseded pin, kept for the record: `~/db_backups/bible_ride.db.20260806-133032.db` (Aug 6 nightly —
> pinned 2026-08-12 from JP's `ls -l ~/db_backups/` paste). Why this one: it predates the
> 8/8 00:31 live write (the moment the damage landed) and is already uncompressed. The
> directory holds NO plain bible.db backup older than Aug 10 (June/July entries are
> info-slips only); `bible.db.pre_boundpainted_b3` (Aug 8 17:22) POSTDATES the 00:31
> write and is ruled out. **Self-check before the diff runs:** the 0a-shaped no-form
> count on this file must read **2,361** (the banked pre-damage figure). Any other
> number → the pin is wrong; fall back to `bible_ride.db.20260805-133029.db.gz`
> (unpack to a scratch copy, same self-check) and stop if that misses too.

Then:
```
sqlite3 ~/bible-db/bible.db "ATTACH '/home/appssanding720/db_backups/bible_ride.db.20260806-133032.db' AS pre; CREATE TEMP TABLE lost AS SELECT w.verse_id, w.position FROM words w WHERE w.is_pn=1 AND NOT EXISTS(SELECT 1 FROM abp_surface s WHERE s.verse_id=w.verse_id AND s.position=w.position) AND EXISTS(SELECT 1 FROM pre.abp_surface p WHERE p.verse_id=w.verse_id AND p.position=w.position); SELECT count(*) FROM lost; .mode tabs
.once /tmp/formlane_lost_slots.tsv
SELECT verse_id, position FROM lost;"
```
Expected near 167. **Caveat (named, not hidden):** verse_id/position keys are only
comparable across the two files if no words rebuild moved slots between them — the 8/8
ride DID move name slots, so if the count comes back far from 167, the key drift is the
first suspect, not the data. In that case the member list gets built the slower way
(by book/chapter/verse + name token), and the charter pauses for that.

0e. Dump the compound-name allowlist candidates WITH the English column (the adjudicator —
a name reads as a place, a defect reads as a sentence):
```
PYTHONIOENCODING=utf-8 sqlite3 ~/bible-db/bible.db "SELECT p.greek_lemma, v.book, v.chapter, v.verse, w.english FROM pn_greek_identity p JOIN verses v ON v.id=p.verse_id JOIN words w ON w.verse_id=p.verse_id AND w.position=p.position WHERE p.greek_lemma LIKE '%'||char(160)||'%' ORDER BY p.greek_lemma;"
```
Banked expectation: 144 rows, of which **27 are genuine compound names** (Βαάλ Ερμών
Baal-hermon, Γασιών Γαβέρ Ezion-geber, Αππίου Φόρου Appii Forum, both Αρειον Πάγον rows…)
and a handful are known-bad parked particles (Act 12:19 `Ηρώδης δε`, Act 13:1 `Μαναήν τε`,
Jos 12:23 `του Ναφαθδώρ`). The 27 get pinned as **allowlist file
`docs/tickets/compound_names_allowlist.tsv`** with verse refs, before any build. Pin
`Βαρώθ␣␣Χαμααμ` (Jer 41:17) by its exact bytes via `hex()` — it carries TWO non-breaking
spaces and any single-NBSP assumption breaks on it.

0f. Baseline audit run on LIVE (read-only) — this is the control run (live against
itself) the gate compares against:
```
PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/audit_surface_coverage.py ~/bible-db/bible.db --bh ~/bible-db/bh_scrape.db
```
Keep the full output; gate F diffs the rebuilt copy's run against it.

## Steps 1–3 — the rebuild, on a copy, never live
1. Copy (on PA): `cp ~/bible-db/bible.db ~/bible-db/bible_formlane.db` — plus confirm the
   most recent nightly backup predates nothing we'd need back (single-rollback rule,
   memory `project_db_backups`).
2. **Dry-run first, verdict before write** (verdict gate — the dry-run paste gets an
   expected picture posted beside it before the write command is ever posted):
```
PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/build_abp_surface.py ~/bible-db/bible_formlane.db --bh ~/bible-db/bh_scrape.db --dry-run
```
3. After the verdict: the same command without `--dry-run`, then IN THIS ORDER (each
   backfill dry-run → verdict → `--apply`, same discipline):
```
PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/backfill_abp_surface.py ~/bible-db/bible_formlane.db --bh ~/bible-db/bh_scrape.db --apply
```
```
PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/backfill_pn_surface.py ~/bible-db/bible_formlane.db --bh ~/bible-db/bh_scrape.db --apply
```
```
PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/build_abp_translit.py ~/bible-db/bible_formlane.db
```
(Order and the both-backfills requirement are from the scripts' own docstrings and
`/rebuild-words` step 9.)

## Gate F — the form lane's own gate (all on the copy, vs the Step-0 live baseline)
A passing gate must be asked what it still permits — F3 and F4 are the landings checks,
not just departures.
- **F1 — coverage floor:** name slots with no printed form (0a query against the copy)
  **≤ 2,361**. **Direction, stated once so nobody re-derives it wrong (reviewer pin 1,
  2026-08-12): 2,361 is the count of name slots WITHOUT a printed form as of 8/5 — a
  missing-slots metric, so LOWER is better and the gate is at-or-below.** A "coverage"
  reading (≥) is the inverted one; the handoff's own line is "no printed form: 2,361
  (pre-8/5) → 2,528 (live)". Higher than 2,361 is a stop.
- **F2 — table floor:** `abp_surface` total **≥ 389,244** (0b against the copy).
- **F3 — landings, member-level:** every key in the Step-0d lost-slots list has a row in
  the copy's `abp_surface`. Count of misses = 0, or each miss enumerated with its verse
  and English before any verdict. "The total went down" is a departure count; this is the
  arrival count.
- **F4 — allowlist survives:** all 27 pinned compound rows still present byte-identical
  (Jer 41:17 checked by `hex()`). A missing legitimate compound is a defect of the fix.
- **F5 — audit diff:** `audit_surface_coverage.py` on the copy; its built-in stored-count
  cross-check green; gap-class totals diffed against the Step-0f live baseline, every
  class delta explained by name (no "roughly the same").
- **F6 — blast radius:** words/verses row counts identical before/after on the copy
  (`SELECT count(*) FROM words; SELECT count(*) FROM verses;` — builder claims read-only
  on both; assert it).
- **F7 — detector certification:** before trusting any zero in F1–F5, the probe fires on
  a known positive in the same command (the 0c pattern). A zero from a probe that never
  fired is not a zero.

## Reconciliation table — the adjacent figures, one row each (reviewer pin 2, 2026-08-12)
Four figures sit near each other in the record and are NOT the same thing. Each Step-0 /
gate read lands in its row; any two rows that should be equal and aren't is a stop.

| Figure | What it counts | Layer / table | Produced by (8/9) | Feeds |
|---|---|---|---|---|
| **2,361** | name slots with NO printed form, pre-8/5 | words.is_pn=1 with no abp_surface row | 0a-shaped read on the pre-8/5 backup | F1 ceiling |
| **2,528** | same metric, live today | same | 0a-shaped read on live 8/9; re-pinned by Step 0a | F1 baseline |
| **~167** | the member list: slots covered pre-8/5, uncovered live (2,528 − 2,361 if no other churn) | same, set difference vs the pinned backup | Step 0d | F3 arrivals list |
| **256** | rows a fresh HEADER rebuild would blank today | pn_greek_identity (header lane, enumeration) | header-lane enumeration 8/9 | header lane; open no. 1 |
| **172** | the subset of those 256 that are currently correct | same | same enumeration | header lane context only |
| **218** | gate B violations | gate_greek_header's own count | gate B run 8/9 | open no. 1 (218+40 allowed = 258 vs 256 → 2 rows unpinned) |
| **~85** | blanked rows whose slot was ALREADY uncovered on 8/5 yet live still heads them | pn_greek_identity vs abp_surface history | 8/9 backup comparison | open no. 3 |

Note the family split: the first three are FORM-table counts (this lane's gate); the last
four are HEADER-table counts (the next lane) and never substitute for an F1/F3 read.

## Pin the three open numbers here (during verification, not quietly closed)
1. **218 (gate B) vs 256 (enumeration), 2 rows unpinned** — while the copy and live are
  both on hand, enumerate both sets member-level and name the 2.
2. **Folded rows 4,408 vs expected 4,399 (+9)** — belongs to the header lane's re-run, but
  if the form rebuild changes the folded-row inputs, note what moved; the header lane
  inherits the pinned number, not the mystery.
3. **~85 live-headed rows whose slot was already uncovered on 8/5** — with the rebuilt
  copy, check whether those slots now carry forms; either way, write down what live's
  heads were resting on. Live's headers stay NON-restore evidence
  (`docs/tickets/receipt_headers_no_source_20260809.txt`).

## Checkpoint → landing on live
Gate F green is a CHECKPOINT, not a go: results (gate output + the three pinned numbers)
go to JP/reviewer before any live write.

**Recommended landing (decision owed at the checkpoint):** re-run the identical proven
command sequence (steps 2–3) against LIVE, then re-run gate F read-only against live —
rather than a whole-file swap. Reason: this lane touches ONLY the `abp_surface` side
table ("drop the table to undo" is the builder's own design), while a whole-file swap
would also carry across anything else that changed on live since the copy was cut. A
whole-file swap (`mv` pair, one reversible move, per `/rebuild-words` step 8) remains the
fallback if the reviewer prefers the gated-bytes-are-the-shipped-bytes property.
Either way: backup verified first; **no backup copy deleted until the nightly (~13:30
UTC) postdates the live write** (single-rollback rule).

## STOP conditions
- Any write to `words`, `verses`, `pn_greek_identity`, or a binding table → full stop;
  this lane owns `abp_surface` (+ its translit column) only.
- Row counts outside the ruled shape (F1–F6) → stop, enumerate members, don't push.
- Step 0 returns a number that changes the lane's premise (e.g. backfill_pn_surface
  suddenly CAN add rows, or the no-form count moved a lot) → stop, re-charter.
- A gate red is a disagreement, not a verdict — locate whether the fault is the pass or
  the measurement before acting (the lane-A lesson).
- Live's stale headers are never a restore source, wholesale or piecemeal.

## After this lane (not this charter)
Header repair re-runs UNCHANGED on the repaired baseline: `build_pn_greek_identity.py
<copy> --apply` + `gate_greek_header.py <live> <copy>`; acceptance zion 168/168 ·
hadad ≥9/12 · 4,326 folded / 1,718 names · glued **= 30 exactly** · gate C green · 114
stale rows cleared. Then batch 3 (galilee, exactly 73). Then routing.
