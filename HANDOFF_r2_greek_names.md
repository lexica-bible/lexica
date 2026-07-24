# HANDOFF — R-2 Greek-name migration (open a fresh session from this doc)

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
