# HANDOFF — header-lane gate-B enumeration (pre-ruled, ready to run)

Banked 2026-08-23 at session close. Context: the form lane LANDED live that night
(`CHARTER_form_table_rebuild.md` — no-form 2,528 → 642, table 391,130, gate F green).
The header repair then re-ran on a fresh copy (`~/bible-db/bible_hdrlane.db`, KEPT for
diagnosis, reproducible): **gate C fully PASS** — zion uniform Σιών, hadad **12/12**
(better than the ≥9/12 pin: the bridge recoveries fed the headers), abner clean, and
**galilee already folds to Γαλιλαία from the rebuild itself** (batch 3's target state
materialized without the hand-table apply). **Gate B FAILED → the gate's own ABORT held
the door; the copy did not land.** Problem rows visible in the tail: live lemmas like
`ην Δαυίδ`, `προκατελάβετο Δαυίδ`, `είπεν Ιησούς` → None, "outside the ruled classes" —
i.e. live's KNOWN-BAD glued headers dying. That is a hypothesis, not a verdict: gate B's
ruled transition classes were written for restoring the OLD form table, and the landed
table is better than old. A gate that fires on a legitimate improvement gets AMENDED BY
RULING with the class enumerated — never overridden in the moment because the failure
"looks explainable" (reviewer, 2026-08-23).

## Pre-registered by the reviewer (start here, already ruled)
1. **The dispositive split.** Every gate-B problem row classifies as
   (a) live value glued/defective → the transition is CURE; candidate for one new ruled
   class "defective live value removed", keyed to the NBSP detector
   (`LIKE '%'||char(160)||'%'`, control row first — 1Ki 11:17 slot 2); or
   (b) live value CLEAN → real regression, FULL STOP, no class extension covers it.
   **One row in (b) outweighs any count in (a).**
2. **Expected picture to test:** class (a) should reconcile with the known defect
   inventory — the 114 stale rows + the adjacent glued family. Problem count beyond
   what the inventory explains = its own finding.
3. **Batch 3 adjudication rides along:** galilee passing gate C implies the hand-table
   admission may be redundant. Rule it explicitly — does the 73-flip still need
   `greek_header_nominatives.tsv`'s galilee row, or does
   `docs/tickets/greek_header_batch3.md` close as superseded? Not assumed either way.
4. **875 vs 871:** the rebuild receipt (`docs/tickets/greek_header_split.txt`) says
   UNRESOLVED 875; the 8/9 queue banked an 871-name scatter class. One member read:
   same set grown by four, or a different denominator? Prevents a figure collision.

## Mechanics
- Full gate output (not the tail) comes from re-running
  `gate_greek_header.py ~/bible-db/bible.db ~/bible-db/bible_hdrlane.db` — read-only,
  and the copy is deterministic (`build_pn_greek_identity.py <copy> --apply` reproduces
  it) if it was cleaned up.
- After the ruling: amend gate B's classes (locked-test discipline: the new class must
  fire on a known (a) row and REFUSE a synthetic (b) row), re-run the gate, land the
  header table via the same checkpoint→apply discipline the form lane used.
- Then batch 3 (as ruled in #3) → ABP-tab routing, the arc's original goal.
- Acceptance figures from the old pins (4,326 folded / 1,718 names / glued = 30) were
  premised on the OLD table — expect upward movement, adjudicate each against the
  bridge-repair story, don't auto-green and don't auto-stop on improvement.

Standing law: `feedback_verdict_gate` · `feedback_audit_tools_must_fail` ("a gate firing
is a claim") · `feedback_correction_lane_lessons` rule 6 (cross-layer inversion — this
gate is the third instance of a sibling lane's improvement tripping a guard).
