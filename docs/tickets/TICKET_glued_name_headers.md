# TICKET — glued name headers + the 8/8 header-table drift

Opened 2026-08-09. **Found by the batch-3 control run, not by a reader report.** Blocks
greek-header batch 3 (galilee, `greek_header_batch3.md`), which is drafted and correct but
cannot be measured against a baseline that is itself wrong.

## The symptom
`gate_greek_header.py` run live-against-live — the control that must pass — FAILS on three
names that PASSED on 2026-07-31 (receipt: `greek_header_batch2.md`, "hadad/zion/abner + all
six batch-1 pins PASS"). All 13 hand-table names still pass. Only the AUTOMATIC layer slipped.

```
gate C: hadad 1Ki 11 — Greek-headed 8/12, English-despite-page-form 1 (must be 0): FAIL
gate C: pin uniform zion = 'Σιών': FAIL (got [])
gate C: pin verse-form abner: 49 fallback rows, FAIL (1 mismatch / none found)
```

## What actually changed (JP-run, read-only, three files compared)
| | pre-8/5 copies * | live 2026-08-09 |
|---|---|---|
| glued rows (name joined to another word) | **30** | **144** |
| zion | 168 rows, ALL `surface` = Σιών | **0 surface** — 164 per-verse Σιών, 3 no header, 1 `διεπέτασε Σιών` |
| hadad 1Ki 11 headed | 9 / 12 | 8 / 12 |
| rows with a folded header (`surface`) | 4,326 | **3,951 (−375)** |
| names with a folded header | 1,718 | **1,705 (−13)** |
| rows with NO header at all (`none`) | 2,353 | **2,454 (+101)** |

\* `bible_pre_pnstar_20260803.db` and `bible_pre_pnstar_swap_20260805.db` — identical to each
other on every figure above, so the break is AFTER 8/5.

**Attribution is by elimination, not by observation:** no commit touches this lane between
8/5 and now (`git log --since=2026-08-06 -- scripts/build_pn_greek_identity.py` is empty of
behavior changes; the two Aug-5 builder commits are Hebrew-snapshot fixes). The only live
write on record in that window is the 8/8 wordpos binding apply, which re-runs the header
build per `/rebuild-words` step 8.3. Stated as elimination so nobody upgrades it later.

## The mechanism (read in the code, then confirmed in the data)
A name gets ONE folded header only if every printed form of it is byte-identical
(`build_pn_greek_identity.py` → `headword()`, the `indeclinable` branch). ABP prints some
name slots as TWO words — a verb glued to the name, joined by a **non-breaking space**
(`U+00A0`), e.g. `απέδρα Αδάρ` "Hadad fled", `ην Νώε` "was Noah", `είπεν Ιησούς` "said
Joshua". One such row in a name's inventory breaks the byte-identical test and drops the
WHOLE name back to per-verse scatter. Zion is the proof: it had zero glued rows and 168
folded rows before; it has one glued row and zero folded rows now.

## TWO SEPARATE CLASSES — do not flatten them into one fix
1. **The 8/8 drift (NEW, 114 extra glued rows).** Almost all of the growth is in classes that
   did not exist before: `tipnr` 0 → 67, `lemma-only` 15 → 58, `abp-tag` 4 → 8. These arrived
   with the slot moves.
2. **11 glued `surface` rows (OLD — the count is 11 in BOTH the pre-copies AND live).** These
   have been live since July and are the worse kind: a `surface` value is the name's header
   EVERYWHERE it appears, so a glued value poisons that name globally. The 58 `lemma-only`
   ones only affect their own verse.

Per-source split today: tipnr 67 · lemma-only 58 · surface 11 · abp-tag 8 = 144 rows across
**84 names**.

## DETECTOR — and the trap it already sprang
```sql
SELECT count(*) FROM pn_greek_identity WHERE greek_lemma LIKE '%'||char(160)||'%';
```
**A plain-space search returns 0 against rows you can see with your own eyes.** The separator
is U+00A0, not U+0020. This lane ALREADY learned this once — commit `5a533f9b` (July): "first
pass required plain space, fixed 0". It was hit again on 2026-08-09 and caught only because
the zero contradicted rows already on screen. Any count here fires on 1Ki 11:17 position 2
FIRST, or it is not trusted.

## Open questions for the fix lane (not decided here)
- Should a two-word compound slot feed the name-form inventory at all? A verb+name slot is
  not a printed form OF THE NAME. Excluding them would restore zion and likely most of the 13
  lost names — but it changes what the builder sees, so it needs its own expected picture.
- The 11 old glued `surface` headers need naming individually before any change: each is a
  name whose card currently heads with a verb attached.
- Whatever lands, it rewrites `pn_greek_identity` → checkpoint, gate control first, and the
  same "identity layer untouched" gate A that batch 2 used.

## STANDING FIX (separate from the data question)
`/rebuild-words` step 8.3 re-runs the header build but nothing checks the result — which is
exactly why this shipped silently and sat live for a day. The gate run is now written into
that step: after `build_pn_greek_identity.py --apply`, run `gate_greek_header.py <pre-copy>
<db>` and read gate C. A pin that used to pass and now fails means the rebuild moved name
slots into the header inventory.

## REPAIR ATTEMPT 2026-08-09 — the fix works, but a SECOND defect blocks it
Rebuilt the header table on a copy against today's form table (live untouched).

**What went right — the repair is proven:**
- Gate C **fully green**, including the three names that caught this: hadad 9/12 with
  English-despite-page-form **0**, zion PASS, abner PASS. Gate A PASS.
- Galilee changed **exactly 73** rows, and glued came out **exactly 30**. Batch 3 is
  validated as far as it can be without shipping.

**What blocks it — gate B FAIL, 218 violations, all of one shape: a header that exists
today would come out EMPTY.** Enumerated: 256 rows lose their value; **172 of them are
currently CLEAN and correct** (`Αδάμ` Gen 3:12, `Λωτ` Gen 13:14, `Εβραίος` Gen 39:17) —
only 84 were glued. **252 of the 256 have NOTHING in today's tables to build from:** no
lemma on the word, no printed form for that slot.

### The second defect: the form table lost name-slot coverage
`abp_surface` holds NO rows for name slots by construction — `backfill_pn_surface.py`
adds them, keyed by verse_id+position. **The 8/8 ride moved name slots, so the backfilled
forms sit at the old slot numbers.** Name slots with no printed form:
**2,361 (pre-8/5) → 2,528 (live), +167.**

So the 8/8 ride broke TWO things. The first framing in this ticket — "rebuild the header
against a fresh form table" — is WRONG: the form table is itself missing coverage, and a
header rebuild on today's inputs DESTROYS 172 good headers. **Live is currently better
than a fresh build for those rows.**

### Numbers that do NOT reconcile — recorded, not smoothed
- **218 (gate) vs 256 (enumeration).** The gate allows 40 as gentilic drops → 258, which
  is 2 more than 256. The two sets are not the same set; the 2 are unpinned.
- **+167 newly-uncovered slots vs 252 rows with nothing to build from** — leaves ~85 rows
  whose slot was ALREADY uncovered on 8/5 while live still carries a header. Live's header
  table predates both backups, so it holds values from a state neither file shows. No
  further explanation is offered because none is proven.
- **Folded rows came out 4,408** against the expected 4,326 + 73 = 4,399. **+9 unexplained.**

### Repair order now needed (NEEDS A RULING — it breaks this lane's own gate)
1. Restore the form table's name-slot coverage: re-run `backfill_pn_surface.py`, then
   `build_abp_translit.py` for the new rows (per that script's own docstring).
2. THEN rebuild the header table.
3. **Gate A requires `abp_surface` byte-identical** — step 1 breaks it by construction.
   Either gate A is re-scoped for this lane (compare only pre-existing rows) or the form
   repair runs as its own lane with `audit_surface_coverage.py` as its gate. Reviewer call.
4. Re-check the +9 and the 2 unpinned rows against the repaired build before any swap.

Scratch copy `bible.db.hdrfix` is reproducible from the same command; deleting it loses
nothing. **Live has not been touched at any point.**

## Blocks
`greek_header_batch3.md` (galilee → Γαλιλαία). The batch-3 admission is unaffected and stays
correct; it cannot be VERIFIED until the gate is green again, because the acceptance test is
"exactly 73 rows flip" and a broken baseline makes that unmeasurable.
