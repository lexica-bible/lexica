# HAND-OFF 2026-07-31 — reviewer (JP, on PA)

No data written this session. No database read by CC. Two commits landed:
`8cad7ba3` (detector gap closed) and `b914be98` (docs reorg).

---

## 1. G707 arc — SHIPPED and CLOSED

Strict name-match Greek-number inheritance is live: a slot inherits an entity's sole Greek
number only when TIPNR attaches that number to the slot's own printed name. 524 slots went
back to `*`, everything else byte-identical to what was live before.

Receipts: TODO_ARCHIVE 2026-07-31 entry ("ENTITY-LEVEL GREEK-NUMBER INHERITANCE (G707
class) — SHIPPED + LIVE") and `docs/tickets/G707_diff_report.md`.

---

## 2. Detector gap — resolved, and the honest version is worse than the ticket assumed

**The sweep script was never committed.** Commit `5dc96a50` landed only the regression test
and the hit list — no script in the repo, the working tree, or any stash. So the ticket's
step 1 ("read the sweep's predicate") could not be done as written, and I did not pretend
otherwise.

**Its predicate is unrecoverable AND demonstrably ad hoc.** I tried to recover it
behaviourally. The structural core of that sweep produces ~247 rows against the documented
145, and the ~100 it dropped are *structurally identical* to rows it kept:

    'these Galileans'   kept        'this Moses'        dropped
    'of Israel, no.'    kept        'of Israel,'        dropped

Same shape, opposite outcome, no rule I could derive separates them. I stopped fitting
rather than publish a reconstructed predicate I could not stand behind.

**New detector:** `scripts/audit_pn_star_verb_merge.py` — read-only, source-side (reads
`abp_texts/`, never the database), predicate written out in full in the header so the next
session can argue with it rather than reverse-engineer it.

Controls, all three FIRED:

    Mat 26:1   class B  'Jesus finished'   -> blanks G5055,G3588   (the gap case)
    Mat 27:26  class A  'scourging Jesus,' -> blanks G5417         (original positive)
    Mat 27:47  class A  'calls Elijah'     -> blanks G5455         (original positive)

Red-first, both directions:
- Class A alone returns **0** hits at Mat 26:1 — the old orientation was structurally
  blind, not merely unlucky.
- Re-declaring Mat 26:1 as class A makes the run **HALT** instead of printing a count. The
  halt path was executed and observed, not assumed.

---

## 3. Revised count — 4,996. Never diff against 145.

    Class A   star carries the merged English         2,237
    Class B   number carries, star left empty         2,759
       B1     carrier holds a pinned-TIPNR name       2,668
       B2     roster-silent residue, needs eyeball       91
    TOTAL                                             4,996

All 145 old rows are contained in class A — checked row by row, 145/145. The old figure is
**superseded, not adjusted**: it was one orientation of a two-orientation class, produced by
a predicate that no longer exists and that dropped identical shapes inconsistently. Any
"delta vs 145" number would be meaningless.

B2's 91 are **reported, not dropped**. They mix real merges the pinned roster misses
(Bath-sheba, Bezaleel, gentilics like Sadducees/Romans) with bracket-position artifacts that
are NOT defects — `1Sa 25:42 "rose upG450 G* 1Abigail],G*"`, where the name IS printed on
its own star and nothing was lost.

---

## 4. Both PA spot-checks passed — live state matches the source scan

You ran both. No drift; both defect classes are real in served data, not just in the source
files:

- **Mat 26:1** — slot 3 `G5055` carries "Jesus finished"; slot 5 is the star (`is_pn=1`)
  with blank English. The class-B shape is live.
- **Mat 20:22** — slot 2 `G3588` (the article) carries "Jesus"; slot 3 is the star, blank.
  Clicking "Jesus" there serves the article's card.

This matters because a source-side scan is not live state. It is now confirmed at both ends.

---

## 5. The 509 article-slot list is NOT fixable-against as it stands

Same mirror blind spot, and it is control-backed rather than asserted:

- **Control positive** (proves the probe reaches the right population): `Act 19:4
  'Jesus the'` IS in the 509 list.
- **The miss**, same shape, absent: `Mat 20:22` — "Jesus" on the article slot, the name's
  own star blank. Same user-visible defect the 509 exists to catalogue: the card heads with
  the article ὁ instead of the word clicked. Also absent: `2Sa 12:9 'Uriah'`,
  `Gen 22:21 'Huz'`.

Worse, its stated exclusion ("adjacent-empty-slot cases are EXCLUDED") drops **3,564**
article slots carrying English wholesale — and was not applied consistently, since Act 19:4
has an adjacent blank star and survived anyway.

**Verdict: the 509 needs its own control-fired re-sweep before any fix work touches it.**
Chartered for the next session — see `docs/handoffs/HANDOFF_2026-07-31_next_cc.md`.

---

## 6. The reverted guard — worth reading, it nearly shipped wrong

Chasing class-B false positives I added a guard: skip an empty star whose nearest printed
neighbour is itself a star (the `1Sa 25:42` placeholder shape). It looked right and cut 165
rows. Then I checked the exclusions against source and found it was **killing genuine
merges**:

    Gen 23:19   Abraham entombedG2290 G* SarahG*     <- directly adjacent, and IS a merge
    2Sa 11:6    Joab sentG649 G* G3588 UriahG*       <- Joab merged, Uriah is a different name

**Adjacency is not the discriminator.** The discriminator is whether the carrier itself holds
a name — "Abraham entombed" does, "rose up" does not. Guard reverted; the roster test
(pinned TIPNR, no database needed) replaced it, with the residue reported as B2 rather than
silently absorbed either way.

---

## 7. Docs reorg — landed at `b914be98`

21 files moved with `git mv` so history follows: 11 handoffs → `docs/handoffs/`, 9 audits →
`docs/audits/`, 1 stray ticket → `docs/tickets/`. Root keeps the session entry points
(README, TODO.md, TODO_ARCHIVE.md, ENGINE_LESSONS.md, CLAUDE.md).

99 references rewritten across 36 files. Link check over all 181 `docs/` path references:
every one resolves except a **pre-existing** broken pointer —
`docs/tickets/DRILL_greek_header_backfill.md` cites `docs/tickets/greek_header_split.txt`,
which never existed at any commit. Noted, deliberately not fixed (outside that task's
charter). `TODO_ARCHIVE.md` left as written — it is a historical log, not a pointer list.

---

## FLAG FOR YOUR EYE

Nine **provenance strings inside `scripts/draw_hints.py`** were path-prefixed by the reorg
(`"AUDIT_lexica_rollout.md G1244 PARKED entry…"` → `"docs/audits/AUDIT_lexica_rollout.md
G1244 …"`). That is stored citation text, not a path the code opens. `test_draw_hints.py`
checks it by substring so it still passes. Calling it out rather than leaving it buried in a
99-reference diff — if you would rather that payload text stayed byte-frozen, it is a
one-line revert per string.
