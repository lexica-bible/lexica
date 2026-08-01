# HANDOFF — article-slot lane A: ruling 10 landed, rebuild ride pending

Written 2026-08-01 at the close of the fix session. Two audiences: the next CC
session (below) and the reviewer chat (paste block at the end).

## Where things stand (nothing here needs re-deriving)

- **Ruling 10 is LANDED, committed, pushed** (`8b24be38` + `7f3c6d94`). The
  article-slot pass now writes only with positive proof: every moved word must
  be a rendering ABP prints ONE-TO-ONE (single-word tokens only) on the target's
  number in ≥5 distinct verses; both-neighbours-attested refuses as 'ambiguous';
  every refusal typed and logged; no map = no writes.
- **Record:** `docs/tickets/TICKET_509_article_slot_resweep.md` §6j (ruling +
  amendments + measured picture) · `docs/audits/PLAN_ruling10_article_slot.txt`
  (the FULL decision record — all 929 writes, all 332 refusals, the 102-row
  threshold revisit list) · `tests/test_article_slot_attestation.py` (10/10,
  in both CI lists) · memory `project_article_slot_lane_a`.
- **Pinned numbers:** writes 929 · lane B 1,376 HELD · bins P 930 / R 240 /
  D 1,519 (P = pre-pass 1 + 929 ✓; lane A 929 + 383 = 1,312 pin ✓).
- **Old 1,240 broken writes: SUBSUMED.** A rebuild re-derives everything from
  source, so the 929/332 record IS their re-audit. Their only surviving copy is
  `bible_test.db` on PA — quarantined evidence, NEVER swap it.
- **No database was changed in the fix session. Live is untouched.**

## Sequencing — what runs before what

1. **FIRST: the "7/30 RECLASSIFICATION CATCH-UP" session** (TODO, own charter).
   It owns re-declaring `retire_hebrew_identity`'s expected split. Step 8b halts
   by design until that lands — do NOT talk past it with `--expect-split`.
2. **THEN: the rebuild ride** (`/rebuild-words` procedure, full chain incl. 8b,
   import_tipnr, roster-freeze check, backfill_abp_surface + backfill_pn_surface).
   Ruling 10 rides that rebuild; it needs no build step of its own.
3. NEVER fold with TODO ② (PN-star merged-verb). Do not open ⑤ (38 bracketed).

## The rebuild session's contract (pre-registered — run and compare, don't re-argue)

- Build prints one line: `Article-slot pass (ruling 10): N written, M refusals
  (…typed…)`. **Expected: N=929, refusal mix matching the PLAN receipt.** Tee
  the whole run; per-step counts are not recoverable afterwards.
- Live sizing query (regenerate via `--plan` / `live_sizing_sql`, never hand-edit
  the list): **must land 1,519–1,759** against pre-rebuild baseline **2,670**.
  - Inside the window → proceed to the rest of the checklist.
  - **Below 1,519 → over-refusal**: safe, don't halt the rebuild for it, but read
    the refusal log before calling it done.
  - **Above 1,759 → the predicate leaked → HALT, no swap** — same posture as 8/1.
- Verdict gate applies: paste the dry-run/count output, state expected beside
  actual, verdict before any swap. Compare lists by MEMBER where members matter.
- Also owed on that ride (TODO ④b): re-verify the checklist pins the 8/1 run
  couldn't confirm — fix_split_flip (1 vs pinned 175/196, unexplained),
  fix_split_merges 237, import_tipnr 31,392, `audit_split_flip.py = 0`, step 6
  audits, `compare_words.py`, and the full 8b chain.
- After the rebuild: unpark the carrier-gap attribution + pass-disabled replay
  (they only mean something measured against the NEW pass).

## Traps already paid for (inherit, don't rediscover)

- PA is pull-only and drifts behind — pull first, then grep
  `build_attestation_map` in `scripts/build_words_from_abp.py` ON PA as the
  file-identity proof before any build.
- The attestation map and the pass both speak SOURCE-layer numbers (2Sa 12:9's
  neighbour is G1473 at pass time; the →846 retag runs later). Any check keyed
  on built numbers will look broken when it isn't.
- A pooled (multi-word) token attests nothing — that ambiguity IS the defect
  class. Don't "improve" the harvest by widening it.
- The ≥5 floor is measured, not taste ('and'→G1473 defect singles reach 4).
  Revisit only through the 102-row threshold list in the PLAN receipt.
- Bin P still counts departures; the WRITES section of the PLAN receipt is the
  landings ledger. Both exist on purpose — read the one the question needs.

## Paste block for the reviewer chat

> Lexica, article-slot lane A. The 8/1 halt (pass wrote English onto numbers
> not the word's own; bin P counted departures, not landings) was answered same
> day by RULING 10: a write now requires that every moved word is a rendering
> ABP itself prints one-to-one (single-word tokens only) on the target's number
> in ≥5 distinct verses; both-neighbours-attested refuses; every refusal typed;
> no map = no writes. Applied under JP's standing delegation.
>
> Evidence: sizing on the real map = 929 writes (broken pass wrote 1,241),
> lane B 1,376 held, bins P 930 / R 240 / D 1,519 with P = 1 + 929 reconciling;
> full per-row decision record committed (PLAN_ruling10_article_slot.txt, no
> capped samples); halt witnesses 2Sa 12:9 / Mat 20:22 are now branch-proven
> controls (refusal logged BY the refusing branch, red-firsted with a permissive
> map that must write) — this replaces Gen 22:21, which refused by position
> luck. First harvest draft was caught writing δέ's 'but' onto a pronoun
> (Mat 7:3) via pooled-token contamination; fixed by the one-to-one rule.
> Pre-registered rebuild window: live count 1,519–1,759 vs baseline 2,670; low
> = over-refusal (safe, review), high = leak (halt, no swap). No DB touched;
> rebuild waits behind the 7/30 reclassification catch-up (step 8b).
>
> Asks: (1) any hole in the attestation predicate as a positive rule — a way a
> wrong word still gets written that the one-to-one harvest + ≥5 floor +
> ambiguity refusal doesn't catch? (2) is the 1,519–1,759 window sound as the
> ONLY acceptable non-halt outcome, or does it need a member-level condition
> too? (3) anything about the 102-row threshold list that should be handled
> before the rebuild instead of after?
