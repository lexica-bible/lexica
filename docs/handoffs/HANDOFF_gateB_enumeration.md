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

---

# ENUMERATION RESULT + RULING RECORD (2026-08-24, JP-run reads, reviewer-ruled)

## The verdict
Gate B's abort was correct AND every problem row is accounted; **zero unexplained
clean casualties**. Full gate re-run (`--dump` mode added to the production gate,
commit `9da1afb5`): 19 violations, NBSP control fired on 1Ki 11:17 slot 2.

- **13 glued → blank** (live NBSP values dying) — cures.
- **6 clean → blank** = six of the form lane's **8 enumerated bridge-fail members**
  (charter, ruled per-member 8/13): Gen 39:17/14 + Gen 41:12/7 (people-word),
  Mar 2:8/4 (unaccented), Mat 9:35/3 (scrape typo — live value was defective),
  Mar 14:66/3 (declined form unattested), Act 18:14/9 (no attestation).
- **Member 7, Act 8:14/9 Σαμάρεια**, left through the then shape-only gentilic door;
  **member 8, Est 1:21/16, IMPROVED** — Μεμουχά → Μεμουχάν via the
  `->surface (headword)` class (ruling 4: that is the named class it went through).
- **Glued arithmetic closed exactly** (inventory reconciliation, pre-reg 2):
  live glued 144 = 30 kept (27 allowlist compounds + 3 parked) + 20 blanked +
  94 replaced with real values. 20 + 94 = 114 = the sentence-glued defect family.
- **The gentilic-drop 21 enumerated**: 5 real people-words (Ethiopians, Tekoahite,
  Assyrians, Grecian, Midianitish) · 7 glued · Σαμάρεια · 5 bridge-claimed blank
  slots (the charter's −1 accounting; the 6th, 2Ch 15:8/34, was already blank in
  BOTH files — nothing to lose) · 3 star slots with NO-FORM + no dictionary entry
  (1Sa 14:50/4 "of Saul's", Heb 11:24/8 "of Pharaoh's", Num 21:25/9 whose live
  value was the verb κατώκησεν — defective, cure).

## Ride-alongs closed
- **Batch 3 = LANDED-VIA-REBUILD, NOT superseded.** Receipt line:
  `galilee|hand-table|146|Γαλιλαία|morph:0|…` — the committed tsv row did the
  folding inside the rebuild (blank morphs + 6 forms mean only the hand table can
  resolve it, confirmed by code read). Copy: Γαλιλαία / surface / **73 exactly**.
  The tsv galilee row is LOAD-BEARING — never remove it.
- **875 replaces 871.** Same class (multi-form names, no safe pick) re-measured on
  the better table: 54 accent-variance + 821 no-nominative. The old 871 was a count
  only (no member list banked), so growth-by-4 is unprovable member-wise — recorded
  as a re-measure, not a collision.

## The amendment (reviewer-approved, SHIPPED same session)
Three changes to gate B, all in `scripts/gate_greek_header.py`, locked by
`tests/test_gate_greek_header.py` (fire + refuse per class, real script on
synthetic files; in BOTH CI lists):
1. **Two pinned per-member lists** with an expected outcome per member (ruling 2 —
   deviation from the pinned outcome violates, not just blanking): the 8
   bridge-fails (7 → blank, Est 1:21 → Μεμουχάν/surface) + the 8 ruled no-form
   blanks. Never shape-based.
2. **NBSP glued-cure class** keyed to the probe; sub-buckets PINNED for this
   landing (ruling 3): blanked 20 / replaced 94 / kept 30 / pinned losses 16 —
   armed only on a transition run so the live-vs-live control still passes.
3. **Gentilic door re-keyed to `er.is_people_group`** (ruling 1) — the build's own
   predicate, imported, never copied. Expected gentilic-drop count drops 21 → 5.

## Expected picture for the amended re-run (post before running — verdict gate)
Gates A and C unchanged-green. Gate B **PASS**: violations 0 · unchanged 30,007
(glued kept 30 inside it) · pinned ruled loss 16 · glued blanked 20 · glued
replaced 94 · gentilic drop 5 · `->surface` + page-attested together **2,336**
(their individual split moves because the 94 + Est 1:21 left those buckets —
recorded as found) · bind-derived 0. Changed-row total must still be 2,471.
Any other number: STOP, enumerate, no auto-green.

## Follow-up filed (ruling 3)
The 20 glued-blanked rows previously showed a garbage word-hint and now show
English — whether any deserve a REAL header is a downstream hand-table question,
tracked in TODO.md, not this lane's blocker.
