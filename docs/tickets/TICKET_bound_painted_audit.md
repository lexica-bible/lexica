# TICKET — Bound-painted audit lane (opened 2026-08-08)

Follow-on of the word-position binding lane (CLOSED 8/8 — TICKET_wordpos_binding.md).
Class: verses where a verse-grain render bind EXISTS and 2+ same-name slots sit in the
verse — the ONE bind paints every same-name slot, and wrong paints hide here.
Last sizing: 1,470 slots / 713 groups (separate bucket of census_wordpos_multi.py).
R2 ruling (banked 8/7): these are BOUND — users see something today, possibly wrong;
a change can break a working display. Risk posture is therefore stricter than the 96.

## Charter
- **Worklist = a FRESH run of `scripts/census_wordpos_multi.py` on PA** (separate
  "bound-PAINTED" bucket). No prior list is reused — the list changes with bind batches.
  Census controls (malchiah bucket-C / mary in-lane / jesus absent) must print OK;
  exit 2 = stop and look, the output is not trustworthy.
- **Discovery-time carve-out in force** (rider 3): any wrongly-painted neighbor found
  while adjudicating a group is recorded HERE, in that group's verdict row, at that
  moment — never re-derived later. (Zero carve-out entries were banked from the wordpos
  lane — prereg close block says "none are bound-painted carve-outs".)
- **OUT of scope, do not touch:**
  - Elnatham Ezr 8:16 p15 — held as in-verse variant-spelling APPENDIX candidate only.
  - Chapter-grain 5 (azariah/joash/benaiah/harim) — parked; per R3 any fold-in
    RETURNS TO THE REVIEWER, never automatic.

## Inherited guards (every slot, every batch — from the wordpos lane, unchanged)
- **Precedence** — slot rows land only where they are needed; a collision with an
  existing slot row = stop-and-look, never overwrite.
- **Stale-name check** — TSV `name` = the printed english_head AT the slot; a mismatch
  vs the live words row = refuse (rebuild-moves-positions tripwire).
- **Referent-kind check** — rows may point at PLACE/group entities (Cushi = the land
  Cush; Judah = the people via the patriarch); never assume "two referents = two people".
- **Shared contiguity classifier** — `scripts/bracket_contiguity.py`, imported, never
  re-implemented; bracket-adjacent groups get per-mode display evidence (chip order,
  not prose — prose passing proves nothing about chip mode).
- **Evidence classes PINNED** (DESIGN_wordpos_binding.md), including
  `source-order-filing` valid ONLY at its three conditions. Cross-verse parallel-list
  inference stays BANNED (jeiel precedent) without a new ruling.
- **Candidate rosters MANDATORY per group, near-match** — exact/prefix/near-0.80,
  never exact-only (4 misses in the wordpos lane). **No write without the roster
  attached to the group's record.**
- **Codicil 2** — automated gates are position-integrity only; entity correctness has
  exactly one gate: the reviewer's per-row verdict.

## Refusal discipline
Anything that trips a guard or lands ambiguous goes on the **loud-refusal list** below
for JP/reviewer review — never a best-guess write. Verdict gate applies throughout:
JP-run dry-run paste → verdict (expected beside actual) → apply.

## Status
- [ ] Fresh census run on PA (JP) — painted-bucket list pasted, controls OK
- [ ] Worklist frozen from that paste; batches cut
- [ ] Batch adjudication (rosters attached per group)
- [ ] Loud-refusal list → review
- [ ] Dry-run → verdicts → apply → deploy → 3-mode verification

## Loud-refusal list
(empty)

## Carve-outs discovered this lane
(none yet)
