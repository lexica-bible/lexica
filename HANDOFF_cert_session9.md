# ABP Corpus Certification — Session 9 handoff (CANONICAL S9 charter)

**Seat: HIGH from the start.** Session 9 *is* the rebuild session — the whole point is a full
words rebuild carrying SEVEN fixes at once. Don't open it on the low/medium census seat.

**This is the single canonical S9 charter.** It merges the cert doors (a)-(c) with the
reassembly-diff arc (d)-(g). The reassembly diagnosis + tools + decisions live in
`AUDIT_reassembly_rebuild.md` (memory `project_reassembly_diff`) — that doc is the technical
backing for (d)-(g); THIS file is the rebuild charter that governs the physical rebuild.

## Frame (unchanged, governs all audit sessions)
Two-tier standard. **Tier A** = ingest-faithfulness. **Tier B** = source defects as a versioned overlay
(`abp_corrections`, 18 rows). Certification COMPLETE since Session 3; every session extends the perimeter,
never re-opens it. Full record: `AUDIT_abp_certification.md`. Standing witness for source readings = the
official ABP app (apostolicbibleapp.com).

## The Session-9 job: ONE rebuild, SEVEN fixes
All remaining doors + the reassembly-diff fixes are rebuild work, so they share **one physical rebuild** —
the discipline is what keeps it safe:

**Batching contract (verbatim, non-negotiable):** one physical rebuild, **seven separately pre-registered
diffs** — (a) Path-C `abp_surface` fallback, (b) `import_tipnr` apply, (c) Door-3 reorder passes,
(d) `build_words` token-slotting fix, (e) reorder float adds `)`, (f) the 13 digit leaks (Tier B +
tolerant `load_abp_prose`), (g) phrase-gloss under-distribution fix (ONLY if the trace confirms it's the
same step — else drop to a follow-up session). Each delta must be attributable to exactly one fix.
**Attribution is PER-COLUMN, not per-row** — a fold slot takes edits from two fixes (Path-C changes its
`strongs`/`strongs_base`, a subject pass changes its `english`), so the same row legitimately shows two
deltas from two fixes; pre-register by (row, column). **This now ALSO binds (a)↔(d):** the slotting fix
(d) and the pronoun fix (a) touch the SAME fold slots — (a) rewrites the number, (d) rewrites the english/
order — so a fold row can show a `strongs_base` delta from (a) AND an `english`/position delta from (d);
both must be pre-registered by column, or that row is unlocalizable → stop. **If any delta can't be pinned
to exactly one fix → fall back to sequential rebuilds.** A combined diff that comes back as one
undifferentiated blob with something unexplained is stop-condition 2 with no way to localize.

## The three fixes

### (a) Path-C `abp_surface` fallback — Door 1's queued fix (NEW code, then rebuild)
Door 1 is CLOSED as census (ledger L12). The residue: pronoun slots (αὐτός/σύ/ὑμεῖς/ἡμεῖς) still numbered
G1473 where Path C's Rahlfs aligner couldn't reach (divergence zones + fold slots). Daniel alone = **170**
source-attested mistags. **Fix:** where Rahlfs can't align, read the number straight off `abp_surface`'s
form (a fixed form→Strong's table for the closed pronoun set: σου→4675, αυτου→846, υμων→5216, ημων→2257,…).
- **DESIGN CONSTRAINT — per-slot sanity gate.** `abp_surface` is trusted where a form EXISTS (placement is
  reliable — proven this session), but the fix MUST NOT write blindly: for each slot check the form-class is
  compatible with the slot's english (or that english is blank/fold), else **skip and log**. Blank-form
  slots (Dan 4:33's kind) carry no form → the fallback can't see them; they stay source-app reads.
- **Do NOT trust the corpus 3,577 as a target count** — it's VOID (a mix of real mistags + fold-companion
  slots, proportions unknown). The per-slot pass produces the real split; don't pre-commit a number.
- Visibility triage if the pass ever partial-ships: fix HAS-ENGLISH mistags first (reader-visible, e.g.
  "yours"/"him" numbered 1473), fold companions (blank-english) second — same form→number treatment, just
  lower urgency.

### (b) `import_tipnr` apply — Door 2's fix (code DONE, just re-import)
Fix is committed + dry-run-proven (commit 96bb662): `import_tipnr.parse_tipnr` now types each entity from
its own col-8 ({Place,Male,Female}, identical to entity_resolution) not the block header; raises on an
unrecognized type in a PERSON+PLACE block. `scripts/dryrun_tipnr_typefix.py` (parse-only) is GREEN:
**10** mixed-block places flip person→place (Beth-gader/Eshtemoa/Etam/Gedor/Gibeon/Ir-nahash/Keilah/
Shechem/Tekoa/Zanoah — Judah founder-towns), mirror 0/0, raise both directions. **Pre-registered Door-2
delta = exactly those 10 entities' type change in the `tipnr` table**, nothing else. Just re-run
import_tipnr on the rebuilt copy.

### (c) Door 3 — the 7 uncertified reorder passes (DIAGNOSIS OPEN, start here)
`_split_numbered`, `_redistribute_pronoun_compounds`, `_fix_backwards_pairing`, `_split_pn_article_lump`,
`_funcword_noun_relocate`, `_lord_subject_split`, `_lord_oath_fix`. Same census+control method as L9.
**Evidence already banked this session — Door 3 opens with a live seam, not a blind census:**
- The **fold slots ARE subject-pass output** (`_lord_subject_split`/`_funcword_noun_relocate`): a subject/
  possessive name whose english folded onto the adjacent verb/noun, its own slot left blank-english +
  numbered 1473. First step = trace those two passes in code from the seam.
- **Two durable known-positives** (with their query — the full-verse dump):
  - `Num 20:9 pos 2` — form Μωυσής, blank english, 1473 ("Moses took" folded onto the verb at pos 1).
  - `1Sa 18:6 pos 8` — form Δαυίδ, blank english, 1473 ("David returned" folded onto the verb at pos 7).
  - Query: full-verse dump `SELECT ..., w.position, w.english, w.strongs, w.bracket_id, s.form FROM words
    w JOIN verses v … LEFT JOIN abp_surface s ON s.verse_id=w.verse_id AND s.position=w.position WHERE
    (book,ch,vs)=… ORDER BY w.position;`
- **CONTROL RULE (unchanged):** any Door-3 census detector must FIRE on those two rows before its zero is
  trusted (same shape as the Session-7 Dan 4:33 dead-detector catch and the Session-8 census control).

### (d) `build_words` token-slotting fix — the 364 word-order defects (DIAGNOSIS OPEN, trace first)
Reassembly-diff (v2, order-aware) found **364** verses where the word rows are in the wrong order vs
`verses.text` — proven WORDS-side by the source-arbiter dump (`scripts/dump_family_source.py`; all 7
families self-adjudicated, PROSE right / WORDS wrong; 5 of 6 have NO bracket, so it's the ROWS, not the
reorder). Suspect = `_split_compounds` article-fronting (`build_words_from_abp.py` ~386-470; its own
comment flags a reverted "the LORD/their X" over-reach). **Trace first** — build Jer 48:1 in isolation and
watch the split step before touching code. Pre-registered (d) delta = the `english`/position corrections on
those rows; drive v2 to zero.

### (e) reorder float adds `)` — paren-edge
The English-order float (`getEnglishOrderWords` + its Python port `reorder_english.py`, and the chip lift)
moves a trailing clause mark past a reordered group, but only for `. , ; : ! ? ·` — NOT `)`. Heb 10:8
class ("…the law)" renders "…offered) …law"). Add `)` to the float set (shared prose + reader). Small.

### (f) the 13 digit leaks → Tier B + tolerant parser
`load_abp_prose` choked on a MALFORMED source bracket (a `]` with no `[`, Mat 21:19 shape) and leaked the
order digits into `verses.text` ("1let", "4dried"). Run `dump_family_source.py --scan-brackets` FIRST to
get the full set. Van der Pool source defect → log each as a **Tier B `abp_corrections` entry** AND make
`load_abp_prose` TOLERATE an unmatched bracket (don't leak). This is verses.text-side (13 rows), not words.

### (g) phrase-gloss under-distribution — CONDITIONAL on the (d) trace
Psa 39:1 "to not sin" parked entirely on G3361 (μή), neighbor G264 blank — should distribute (same class as
the G846 "jesus 2" finding). `_split_compounds` is the distributor, so HYPOTHESIS: the SAME leaky lexicon-
evidence gate over-reaches (d) AND under-reaches here. **This class is v2- AND v1-INVISIBLE** (order- and
bag-neutral). Ship (g) in THIS rebuild only if the (d) trace confirms one mechanism; else it's a follow-up.
Either way the gate block gains its own detector (below).

### Already LIVE (NOT a rebuild diff)
The chip clause-mark lift fix (the "the word. was God" bug) shipped this session in the frontend — reader
render only, no corpus change. Do not carry it as a diff.

## The 8-vs-10 explanation (so it doesn't resurface as a phantom conflict)
`import_tipnr`'s twin flips **10** mixed-block places; `entity_resolution` (Session 6) flipped **8**. These
are TWO parsers with different line-skipping strictness legitimately counting different sets — **NOT a stale
doc, NOT a discrepancy**. The Session-8 dry-run's independent line-scan settled it by enumeration (it
couldn't have if either number were hardcoded — which is exactly why the line-scan design was right).

## State entering Session 9
- `cert_invariants.py` 7/7 green; `abp_corrections` 18 rows (pin 18); manifest 75 files. CERTIFIED STATE
  HOLDS — the three fixes are ADDITIVE, gated behind the rebuild's pre-registered diffs.
- Door 1 CLOSED (census); Door 2 code DONE + proven (not applied); Door 3 diagnosis OPEN.
- (d) diagnosis OPEN (trace `_split_compounds`); (e)/(f) scoped, ready; (g) conditional on the (d) trace.
- Reassembly-diff tools committed (READ-ONLY): `audit_reassembly_diff.py` (v1 bag + v2 order-aware,
  `--controls`/`--list`), `reorder_english.py` (+ `tests/test_reorder_port.py`, proven byte-equal to the JS),
  `check_draw_citations.py`, `dump_family_source.py` (+ `--scan-brackets`).
- After the rebuild+swap: re-run the dependent builders in order (import_tipnr → build_abp_surface →
  build_abp_translit → entity binding → dotted_lexicon → rendering-norm → two-ending), re-pin the invariant
  row counts ONLY in the deliberate-rebuild commit after compare_words passed, and re-run `cert_invariants.py`.

## Gate block (must all pass before the swap)
- `compare_words.py` reviewed (pre-registered per-column diffs only, per the batching contract)
- `cert_invariants.py` 7/7 + `--controls` all fire; row pins re-pinned in the rebuild commit
- L9 split lint = 0
- `tests/test_reorder_port.py` green (the port is the v2 arbiter — prove it FIRST)
- **v1 AND v2 reassembly at CRITERION** (`--controls` + `--controls --v2` fire first):
  **zero word-order + zero content-other + NO NEW punct-position.** punct-position stays but is pinned as a
  FROZEN ALLOWLIST — RE-COUNT after the rebuild (the slot fix may cure some free), then enumerate the
  survivors; any new punct hit fails the gate.
- **phrase-gloss under-distribution detector** (multi-word gloss on a function-word tag + adjacent blank
  content slot) — build read-only, control-test it FIRES on Psa 39:1, drive to an agreed floor. Required in
  the gate whether or not (g) ships this rebuild.
- THEN wire v2 into `cert_invariants.py` as a standing invariant (the words rows and `verses.text` can
  never silently drift again).

## Standing rules (all inherited, none weakened this session)
Checkpoint rule; CC can't query bible.db (JP runs every query on PA); control-test rule (fire on a known
positive, reuse the production detector never a second copy); new-finding rule; verify-before-sizing;
query-preservation (every ledger count carries its defining query verbatim); loud-fails are the guard
working; corrections are two cells (`strongs` + `strongs_base`); diff joins use `IS` on nullable columns.
Accepted limits, do not re-open: `HEAD_WORD_TAIL_CAVEAT`, `SPLIT_FUNCWORD_SLOT_CAVEAT`.

**Two rules earned fresh proof-of-value this session:**
- **control-test** — the census control (`grep '^Dan 4:33' pronoun_review.tsv`) had to fire before any zero
  downstream was trusted; and Door-2's dry-run pinned its expectation with an INDEPENDENT line-scan, not the
  parser under test.
- **verify-before-sizing** — the οὗτος lead (Rahlfs `non-pron:3778`) LOOKED like a demonstrative-mistag
  cluster; inspecting the real live cells killed it (divergence-zone noise; the slots were σου/αυτου/names).
  And "abp_surface misaligns ~91%" was a wrong root-cause guess retracted by a 5-cell inspection before it
  hardened in the ledger.

## Closed + certified — DO NOT re-open
L9 · flip class · em-dash class · Cushi · Jer 49:13 · Hab 3:6 · Session-3 swap · Session-4 Cushi binding ·
Session-5 TIPNR pin · L2 · L10 · 97-card label defect · mirror census · check-7 both-directions · L5 (all 9
read) · Luke 23:38 (binder artifact) · **[Session 8] Door 1 census** (cluster, sized; the FIX is queued, the
census is closed) · **[Session 8] the abp_surface "misalignment" scare** (resolved: reliable placement,
words-side fold class).

## Out of scope
Re-opening anything certified in Sessions 1–8; schema changes to `abp_corrections`; treating the corpus
3,577 as a real count; any Lexica feature work. The queued index memory-file merge is repo hygiene, not
audit work.
