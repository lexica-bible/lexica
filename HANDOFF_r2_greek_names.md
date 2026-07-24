# HANDOFF — R-2 Greek-name migration (open a fresh session from this doc)

## ★ STAGE 2 CLOSED — LIVE 2026-07-24, receipt 2 issued (commit 7b31eb4). ABP
## proper-noun cards now carry the GREEK identity; Hebrew demoted to a labeled
## cross-ref line. Close-out block atop docs/PLAN_r2_stage2.md (nine checks green,
## count gate proven both ways, 146 changed counts fully traced). Cosmetic thread
## (STEP-tag placement + line formats + arrows) CLOSED 2026-07-24, receipt on d4b8958
## — final shape + arrow ruling in docs/tickets/TICKET_step_tag_placement.md.
## Open: stage-3 candidates ONLY (parked, scoping unparks on reviewer's call):
## Word study ABP branch flip + reader interlinear tags Greek-keyed for backfilled
## PNs (chapter feed was kept out of flip scope by ruling — card G9826 over in-text
## H90 is by design) + Hebrew retirement rebuild.
## Rollback: delete the READER_GREEK_IDENTITY=1 line in the WSGI file + reload.

## ★ STAGE 1 LIVE — swapped 2026-07-24, reviewer-receipted. READ THIS FIRST.

Swapped after the full gate bundle: reconcile CLEAN (every bind move traced to the 206
accepted pairs; 3 hot arrivals verified honestly-ambiguous), applies matched trials,
control panel 10/10 PASS (audit_two_derivations.py prints it — G1 David@Mat 1:6 =
G1138 closed by the sub-record fix), gates 0 / 1-warning-root-caused / **IDENTICAL**
(626,309 rows, same fingerprint — purely-additive proven at byte level). JP verified
the Maachah @ 2Ch 11:21 card live (the batch's showcase recovery) + normal reading.

What live now carries (all additive; no reader behavior changed):
- pn_binding 14,830 render (+300) / 68 hot / 885 numonly; binder map +206
  (`R2_BINDER_VARIANTS`, verdicts in docs/tickets/variant_batch_binder_verdicts.txt).
- `step_lexicon` 10,846 rows (TBESG full entries; TIPNR Greek coverage 476/476 — the
  lone "G0" is TIPNR's nine unnamed#N placeholders, not a word).
- `pn_greek_identity` 32,479 rows: abp-tag 3,518 · tipnr 10,731 · lemma-only 14,850 ·
  none 3,380 (the sized residue: docs/tickets/TICKET_pn_lemma_residue.md).
- Rollback: `~/bible-db/bible_pre_r2s1_swap.db` (one reversible move back).

Open threads: (1) nightly backup freshness must flip under 25h on 2026-07-25 — the
8-day failure was the disk quota, cleaned this session; if it fails again it's real
I/O, investigate before anything else. (2) The 3,380 lemma residue ticket (pull).
(3) The 3 hot arrivals (Elnathan/Malchijah/Nergal-sar-ezer) sit in the hand-check
queue. Stages 2–3 (reader flip, Hebrew retirement) PARKED until JP raises them.
Run log + declared expectations: docs/PLAN_r2_stage1.md.

Written 2026-07-16 at JP's ask, consolidating: `docs/DESIGN_greek_name_identity.md`
(direction approved by JP, R-2 ruling 2026-07-16 — design only, no build yet),
the provenance audit (`AUDIT_provenance_sweep.md`), and the R-1 parked piles
(`docs/tickets/alias_leave_list.txt`). Authorities unchanged; this doc ADDS nothing to
them except consolidation and the ruling questions phrased for chat.

## What R-2 is, in one paragraph

Today an ABP proper noun's identity is a HEBREW Strong's number reached by matching the
English spelling (the R-1 stopgap). R-2 gives Greek-text names a GREEK identity — real
G-number where the text carries one, STEP-extended number if we import that lexicon,
otherwise the Greek lemma with an honest "no Strong's mapping" state — with the Hebrew
number demoted to cross-reference. LXX-only forms (the pile-B research tail) finally get
an identity instead of double-star blanks. NT name cards also become verse-bindable
(today David @ Mat 1:6 rides the name-path card because Greek binds don't exist).

## Standing constraints (all inherited, none new)

- Build-side ONLY into `bible.db.new` per `/rebuild-words`; live never patched; dry-run
  before any --apply; JP reviews the diff.
- **Roster freeze tripwire**: any `import_tipnr.py` / TIPNR.txt change must pass
  `scripts/check_roster_regression.py` CLEAN (exact match incl. fills/new names) BEFORE
  import runs (the Barabbas-steals-'jesus' lesson).
- Head-word fix landed FIRST (R-1, live 2026-07-16) — the precondition is satisfied;
  R-2 is its own staged rebuild (that half of Q5 is already history).
- Two-derivations audit: stage 1 stores Greek identity ALONGSIDE the Hebrew stopgap;
  the diff between Hebrew-keyed and Greek-keyed occurrence counts is the audit
  instrument before anything flips.
- Staging (from the design): (1) add Greek identity beside Hebrew, audit; (2) flip the
  readers by code deploy (git-revertible); (3) retire Hebrew as identity, keep as
  cross-ref. Each stage rolls back independently.
- New column or table = checkpoint: JP OK before it lands (Q2 below).

## The five rulings — phrased for JP to rule in chat (recommendations included)

- **R2-Q1 — Import the STEP extended Greek lexicon?** It's the only way TIPNR's G9xxx
  name numbers become showable words (our lexicon lacks them; ABP never prints them).
  Needs a licensing check (Tyndale/STEP; CREDITS.md addition) BEFORE ingest.
  *Recommendation: yes, pending the license check — without it, most TIPNR Greek name
  numbers stay unrenderable and Q3's lemma-only state carries far more weight.*
- **R2-Q2 — Where does the Hebrew number live after the flip?** Second column on the
  words table, or a side table. Either is a new-field checkpoint.
  *Recommendation: side table keyed by the Greek identity — keeps the words table's
  shape untouched (every existing consumer keeps working blind), and the cross-ref is
  a lookup, not a per-word fact.*
- **R2-Q3 — Card wording for LXX-only names with no number in any scheme.** The state
  must be visible (provenance contract); the words are JP's call.
  *Recommendation: "ABP-only form — no Strong's mapping." Same quiet caveat style as
  "Matched by name — not checked against this verse."*
- **R2-Q4 — KJV/BSB name clicks stay Hebrew-keyed?** They're correct for those texts
  today; the design assumes untouched.
  *Recommendation: yes — ABP-side identity only. Confirm so the scope line is a ruling,
  not an assumption.*
- **R2-Q5 — Run shape.** The head-word half already resolved (landed first, R-1).
  Remaining decision: stage 1 (add-alongside rebuild) as its own run now, with stages
  2/3 gated on the stage-1 audit?
  *Recommendation: yes — one rebuild for stage 1, code-deploy flip later, retire in a
  final rebuild. Matches the design and keeps every step small enough to check.*

## R2-Q1 license check — PASSED (logged 2026-07-24, before any import)

Checked at the source: the STEPBible-Data repository (github.com/STEPBible/STEPBible-Data)
licenses ALL its data, including the TBESG extended Greek lexicon file
("TBESG - Tyndale Brief lexicon of Extended Strongs for Greek - CC BY.txt"),
under CC BY 4.0. Required credit: "STEP Bible" linked to www.STEPBible.org. No other
restrictions; commercial use and modification allowed with attribution.
CREDITS.md already carries the required line (TBESG/TBESH, STEP Bible / Tyndale House,
CC BY 4.0) — same terms as TAHOT and TIPNR already in use. No new credit needed;
Q1's condition is satisfied and the STEP ingest is cleared.

## Riding along: the 352-row variant batch (audit 2026-07-16)

The numonly hand-check's recoverable bucket: surface spellings that failed the string
match but sit one letter or two from their sole candidate (abia/abiah→abijah class).
Concrete candidate list generated: **`docs/tickets/variant_batch_candidates.txt`**
(233 unique pairs / 391 rows — the audit quoted 352 rows under a broader suffix screen;
the file is the working list, and the eyeball pass is the filter that matters).
**Conditions attached (reviewer-accepted):** every pair individually eyeballed against
TIPNR before it enters the variant map; roster-freeze gate before import; lands inside
R-2's stage-1 rebuild, never as a live patch. Expect the eyeball pass to kill some
pairs — a close spelling is a candidate, not a match.

## Variant batch — FRAME CORRECTION (2026-07-24, later same day)

The pass below dispositioned the pairs on the NUMBER axis. The source bucket
(pn_binding_numonly.txt) is the BIND-floored class — words that already carry numbers
but have no entity card. The binder keeps its OWN alias map
(`entity_resolution.VARIANT_ALIASES`, number-guarded) and never reads
`scripts/tipnr_alias_variants.py`. So: the 11 landed entries are kept (honest value:
step-7 resolution with the TRUE entity type — import_tipnr's DIRECT list was already
covering 10 of them number-wise but stamps everything type 'place'; 'gedi' is new), and
the ACTUAL bind recovery is an open second pass: derive binder-map entries from the
same per-pair TIPNR evidence (ref-match at the attested verse = the bind standard),
gentilic kills carry over (ruled floor-stays / pile U), the 139 R-1-shipped pairs need
their own binder-side look (their R-1 decision lines are reusable evidence). Reviewer
receipt required before anything lands in entity_resolution.py. Full correction block:
top of `docs/tickets/variant_batch_verdicts.txt`.

## Variant batch eyeball pass — DONE (2026-07-24)

All 233 pairs dispositioned against TIPNR via the production parser
(`docs/tickets/variant_batch_verdicts.txt` has every line): **139 SHIPPED** (already in the
R-1 map, identical), **11 ACCEPT** (now added to `tipnr_alias_variants.py`, 410 entries,
decision lines appended to alias_decisions.txt), **1 MERGED** (bethhoron upper/lower →
one entry, shared H1032), **82 KILL**. The kill reasons matter for stage 1:
- Most kills: the surface ALREADY resolves directly in the TIPNR lookup since the R-1
  loader fix — the ladder finds it before the variant map is consulted, so an entry is
  dead code. If any of those rows are still number-only after R-1, the failure is in the
  word cell (possessive/plural/split), not the map — re-derive from a post-R-1 numonly
  dump during the stage-1 audit.
- Gentilic kills (arabian, chaldean, mede, persian, samaritan, syrian, +micha/juda):
  the loader drops these as ambiguous because TIPNR gives the gentilic its OWN number
  distinct from the place. Aliasing to the place would hand them the wrong number —
  these are Pile U work (Group-entity binds), not map entries.
- raphaiah: the file's raphah suggestion killed; the shipped rephaiah entry is the
  person TIPNR names at the attested verse.
Roster note — CORRECTED 2026-07-24 (the first version of this paragraph claimed the 11
would show as roster additions; checked against roster_baseline.json and that was wrong):
the variant map is NOT part of the roster. The baseline holds only parse_tipnr's own
name list (4,331 — none of R-1's 399 alias keys are in it), and the map is consulted
only after the roster misses. Expected freeze-gate result at the stage-1 import:
**CLEAN, zero additions, zero changes.** The 11 map entries are instead proven by
per-word controls (named in the stage-1 plan) and by their decision lines.

## Parked R-1 candidates (pull, not push — pick up only if R-2's work touches them)

From `docs/tickets/alias_leave_list.txt` pile comments (all reviewer-accepted parks):
- **Pile U — hittites ×13**: gentilic Group rows now carry their OWN number (H2850) and
  honestly unbind from the ancestor person (Heth). Proper fix = bind Group rows to their
  own Group entities — natural R-2 companion since it's an identity-model change.
- **Pile V — Pharaoh ×7**: title demotions at the person-link layer; recovery needs
  per-reign disambiguation via reign refs. Stays parked unless R-2 builds the machinery.
- **Pile P — possessive/plural cells** ("Aaron's," / "being Romans."): ladder
  possessive-strip improvement, own review.
- **Pile R micro alias batch**: josua/shapan/meramoth — canonical keys exist
  (joshua/shaphan/meremoth); clean 3-name reviewer-gated batch any time.
- **Vocative-aware peel** (Isa 41:14 "O Israel") — parked ladder improvement.
- **The 178 lookup H/G fill-gains** reverted for byte-identity in R-1: NT name words
  still ride the Hebrew fallback. R-2's Greek identity supersedes most of them —
  re-derive from the R-2 audit rather than replaying the old list.
- (Pile B — LXX-only research tail — IS the R-2 target set, not a rider.)

## Session-open checklist for the fresh session

1. Read: this doc → `docs/DESIGN_greek_name_identity.md` →
   `docs/tickets/TICKET_headword_class.md` (consumer contamination map) →
   `docs/claude/data-model.md` (routing rule).
2. Get the five rulings from JP in chat (recommendations above; delegation rule applies
   where he defers).
3. Q1 yes → licensing check BEFORE any STEP ingest; CREDITS.md line drafted for review.
4. Variant batch eyeball pass (233 pairs) — output: the approved variant-map additions
   + a kill list with reasons.
5. Stage-1 rebuild plan as a dry-run first; JP runs PA commands; reviewer sees the
   stage-1 two-derivations diff before any swap.
