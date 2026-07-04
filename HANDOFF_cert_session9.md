# ABP Corpus Certification — Session 9 handoff

**Seat: HIGH from the start.** Session 9 *is* the rebuild session — the whole point is a full
words rebuild carrying three fixes at once. Don't open it on the low/medium census seat.

## Frame (unchanged, governs all audit sessions)
Two-tier standard. **Tier A** = ingest-faithfulness. **Tier B** = source defects as a versioned overlay
(`abp_corrections`, 18 rows). Certification COMPLETE since Session 3; every session extends the perimeter,
never re-opens it. Full record: `AUDIT_abp_certification.md`. Standing witness for source readings = the
official ABP app (apostolicbibleapp.com).

## The Session-9 job: ONE rebuild, THREE fixes
All three remaining doors are rebuild work, so they share **one physical rebuild** — but the discipline
is what keeps it safe:

**Batching contract (verbatim, non-negotiable):** one physical rebuild, **three separately pre-registered
diffs** — (a) Path-C `abp_surface` fallback, (b) `import_tipnr` apply, (c) Door-3 reorder passes. Each
delta must be attributable to exactly one fix. **Attribution is PER-COLUMN, not per-row** — a fold slot
takes edits from two fixes (Path-C changes its `strongs`/`strongs_base`, a subject pass changes its
`english`), so the same row legitimately shows two deltas from two fixes; pre-register by (row, column).
**If any delta can't be pinned to exactly one fix → fall back to sequential rebuilds.** A combined diff
that comes back as one undifferentiated blob with something unexplained is stop-condition 2 with no way to
localize.

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

## The 8-vs-10 explanation (so it doesn't resurface as a phantom conflict)
`import_tipnr`'s twin flips **10** mixed-block places; `entity_resolution` (Session 6) flipped **8**. These
are TWO parsers with different line-skipping strictness legitimately counting different sets — **NOT a stale
doc, NOT a discrepancy**. The Session-8 dry-run's independent line-scan settled it by enumeration (it
couldn't have if either number were hardcoded — which is exactly why the line-scan design was right).

## State entering Session 9
- `cert_invariants.py` 7/7 green; `abp_corrections` 18 rows (pin 18); manifest 75 files. CERTIFIED STATE
  HOLDS — the three fixes are ADDITIVE, gated behind the rebuild's pre-registered diffs.
- Door 1 CLOSED (census); Door 2 code DONE + proven (not applied); Door 3 diagnosis OPEN.
- After the rebuild+swap: re-run the dependent builders in order (import_tipnr → build_abp_surface →
  build_abp_translit → entity binding → dotted_lexicon → rendering-norm → two-ending), re-pin the invariant
  row counts ONLY in the deliberate-rebuild commit after compare_words passed, and re-run `cert_invariants.py`.

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
