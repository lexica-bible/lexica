# TICKET — word-position binding lane (same-verse same-name multi slots)

Opened 2026-08-07 at lane unpark (JP's ordering — next in the card-work queue,
TODO.md). **Census-first charter: nothing is designed and no data is written
until the re-derived census is confirmed and the reviewer has ruled on the
open questions below.**

## Charter (assembled — no prior ticket existed for this lane)
This lane never had its own ticket or a frozen member list. The charter is the
sum of:
- TODO.md open-lanes block: ~118 same-verse same-name multi slots + malchiah
  Ezr 10:25 + the mary class (8 verses / 16 slots); un-partitionable at the
  (book,ch,vs,name) bind key BY CONSTRUCTION; needs word-position-level binding.
- TODO_ARCHIVE 2026-07-30 census close: ≈118 slots = mary 16 + 102 across 22
  tail names (genealogy lists genuinely naming two like-named people in one
  verse — the Dishon pattern). The census certificate (banked verbatim there)
  identifies this class as one of the two things the automatic binder can't do.
- DRILL_lane_c.md named residue: the 5 multi-in-chapter slots (azariah 1Ch 6
  genealogy, joash 2Ch 25:20 both kings, benaiah, harim) — related shape,
  chapter grain not verse grain; NOT auto-folded here (ruling R3 below).
- DRILL_witness_divergence.md: malchiah Ezr 10:25 demoted from lane A to this
  lane (two Malchiahs in the verse).

## STALE-CENSUS status (binding)
The ~118 was derived 2026-07-30. Since then: the PN-star rebuild ride shipped
2026-08-05 and 17 lane-③ hand repairs landed 2026-08-07 — positions, brackets,
and identity assignments have all moved. The live-vs-source rule (55/71
phantoms in lane ③) applies: **the figure is a hypothesis until re-derived
against the live table.**

## Census tool (this session's build)
`scripts/census_wordpos_multi.py` — READ-ONLY, mirror functions copied from
`scripts/audit_pn_lanes.py` (the census pipeline's production mirrors; read in
full before writing this). Predicate: identity slot with a words row, chip-order
clicked name multi-referent (metaV+TIPNR test), UNBOUND (exact or unique-compact
bind test, same as the lanes script), same normalized name on ≥2 slots in the
same verse. Reports separately (not in the lane figure):
- **bound-PAINTED bucket**: same-name multi verses where a render bind EXISTS —
  the one (book,ch,vs,name) bind paints every same-name slot, possibly wrong
  for one of them. New sizing input, was invisible to the unbound-only census.
- Excluded by construction: the 340 no-words-row identity slots (own deferred
  lane, TODO) — the census inner-joins words.
Controls: known positive malchiah Ezr 10:25 must appear; known negative jesus
Mat 8:5 must be absent (this one only proves the ≥2-slots threshold, not the
bind test — the positive control is the load-bearing one). Either failing →
exit 2.

Run on PA:
```
cd ~/bible-db && PYTHONIOENCODING=utf-8 python3 scripts/census_wordpos_multi.py bible.db
```

## What the ~118 was counting (July close-out language, quoted per reviewer)
TODO_ARCHIVE 2026-07-30: "same-verse same-name multi ≈118 slots (mary 16 + 22
tail names / 102 — genealogy lists genuinely naming two like-named people in
one verse, the Dishon pattern; un-partitionable at the verse+name key BY
CONSTRUCTION; fix = word-position binding)". So 118 = 16 mary + 102 across 22
other names, all UNBOUND, verse grain. The bound-painted class was NOT in it
(the census walked an unbound dump). Whether variant-spelling pairs
(malchiah-class) were inside the 102 is not recoverable — no member list was
kept; TODO's phrasing ("~118 ... + malchiah Ezr 10:25 + the mary class")
lists malchiah BESIDE the figure, which fits it being outside.

## First-run post-mortem (2026-08-07, run 1: CONTROL FAIL, verdict withheld)
- **Control failure walked down (diagnostic triad, JP-run):** Ezr 10:25 prints
  the two same-named men as "Malchiah" (p10) AND "Malchijah" (p16) — different
  spellings, both is_pn, both identity slots, both DECLINED by the binder
  (pn_binding rule='multi', render=0), malchiah = 9 metaV people. The census
  groups by identical normalized name, so a variant-spelling pair can never
  group. Census logic sound for what it counts; the CONTROL was mis-keyed
  (expected malchiah inside the lane). Fix: bucket C (below) + re-keyed
  controls (pair in bucket C · mary Mat 27:61 in lane · jesus Mat 8:5 absent).
- **BUCKET C added:** verses holding ≥2 unbound multi-referent single slots
  whose different names are spelling-near (SequenceMatcher ≥ 0.80) — HAND-
  REVIEW candidates, never members. The malchiah-class home.
- **Pre-registration error, owned (reviewer point 2):** I pre-registered that
  azariah/joash "should NOT appear". Wrong conflation: DRILL_lane_c's "5
  multi-in-chapter slots (two Joashes, Azariah genealogy) = named residue with
  the word-position class" counts lane-C slots with several CANDIDATES in the
  chapter — a different set from verses printing the name twice (1Ch 6:9
  Azariah begat Azariah; 2Ki 14:1 Joash of Judah + Joash of Israel in one
  sentence). Those ARE Dishon-pattern members; the census over-includes
  nothing here. R3's frame corrects to: the lane-C 5 stay out only where they
  are chapter-grain, not by name.
- **Run-1 lane figure 96** (mary 16 ✓ anchor). 96 vs 118: −22, not yet
  attributable member-by-member (no July list); candidate explanations = the
  8/5 rebuild + 8/7 repairs moving slots into bound/painted state, definitional
  drift in the July count, and variant-spelling pairs sitting outside the
  predicate. Run 2 (with bucket C) is the number the verdict runs on.

## FOLLOW-ON TICKET (reviewer point 4, out of this lane's scope)
The bound-painted bucket (run 1: 1,470 slots / 713 groups — one verse-level
bind paints every same-name slot in the verse) is correct where the repeated
name is the same referent (Saul/Joseph/Pharaoh narrative repetition — most of
the list) and wrong where it isn't. Auditing those 713 groups for wrong paints
is its OWN lane — a bind created on a known multi-referent verse is where a
wrong paint would hide. Not folded here.

## Diff frame (what the fresh census is checked against)
No frozen member-by-member list exists, so the diff runs against the charter's
NAMED members + aggregates; the fresh output then becomes the frozen list:
- total ≈118 slots (drift expected and must be explained by the 8/5 rebuild /
  8/7 repairs, not waved through)
- mary: 16 slots / 8 verses expected
- malchiah Ezr 10:25 present (also the control)
- ~22 tail names besides mary, genealogy-heavy (run 1: 27 — azariah/joash
  verse-level pairs are legitimate members, see post-mortem)
- malchiah/malchijah Ezr 10:25 in bucket C (control)
CENSUS VERDICT (2026-08-07, run 2): **PASS — CONFIRMED, frozen.**
Expected vs actual: lane unchanged from run 1 (96/47/28, mary 16 ✓) — identical;
malchiah/malchijah in bucket C ✓ (and it is the ONLY variant-spelling pair in
the corpus); controls 3/3 OK. 96 vs July ~118 = −22, direction consistent with
the 8/5 rebuild + 8/7 repairs; member-by-member attribution impossible (no July
list) per the accepted degraded gate. **Frozen member list:
docs/tickets/wordpos_census_20260807.txt — the lane's baseline from here on.**
Known lane facts from the list: mary 16/8 verses (July anchor exact) · joash 12
· azariah 8 · 1Ch 1:41 dishon is a THREE-slot verse (as is Act 1:13 james) ·
gilead/jezreel/penuel groups may be person-vs-place pairs, not two people —
per-slot adjudication will sort kind, not the census.

## CENSUS RATIFIED (reviewer, 2026-08-07) — with three riders
1. Ezr 10:25 (bucket C) is a flagged APPENDIX member of this lane's per-slot
   work — adjudicated with the rest, variant-spelling status in evidence; it
   does NOT wait for a future lane.
2. Person/place shared-name pairs (gilead, jezreel, penuel, haran Gen 11:31,
   shechem-adjacent) are still multi-referent; the design must NOT assume
   "two referents" means "two people" anywhere in its data model.
3. Bound-painted follow-on carve-out: a wrongly-painted neighbor discovered
   during per-slot work on the 96 is recorded in the follow-on ticket AT
   DISCOVERY TIME, not re-derived later.

## DECIDE AT SESSION OPEN — open questions for the reviewer
The charter carries no explicit banked rulings (no prior ticket), so these are
the open questions, with recommendations (standing delegation: CC+reviewer
recommendation applies as the ruling):
- **R1 — class predicate.** Confirm the census predicate above (unbound
  Jacob-class slot, same normalized name ≥2 slots per verse, chip-order names)
  as THE lane membership definition. Recommendation: yes — it is the 07-30
  census's own frame re-run, not a new definition.
- **R2 — bound-painted bucket scope.** Does the painted bucket (bind exists,
  2+ same-name slots, one bind paints all) belong to this lane? It shares the
  mechanism (word-position grain) but was outside the ~118. Recommendation:
  census it now (done — separate bucket), rule on scope AFTER the numbers are
  on the table; do not fold into the lane figure silently.
- **R3 — chapter-grain residue.** The 5 multi-in-chapter slots (azariah, joash,
  benaiah, harim) are the same disease at chapter grain. Recommendation: keep
  OUT of this lane's verse-grain census; revisit only if the mechanism design
  turns out to cover them for free.
- **R4 — mary class + malchiah fold-in.** TODO.md already folds them in.
  Recommendation: confirm — same predicate catches both, no special-casing.

## RULINGS BANKED (reviewer, 2026-08-07 — gate phase CLOSED)
- **R1 RATIFIED.** The predicate IS the lane membership definition (the 07-30
  frame re-run against live). Codicil: "same normalized name" has a known
  blind spot (variant spellings), proven singular by Ezr 10:25; covered by
  the bucket-C appendix, NOT by widening the predicate.
- **R2 RATIFIED — painted bucket OUT of this lane.** Risk classes differ: the
  96 are unbound (users get nothing today; a fix can only add), the 1,470 are
  bound (users get something, possibly wrong; changes can break working
  displays). Follow-on lane stands; discovery-time carve-out in force.
- **R3 RATIFIED as amended.** GRAIN, not name, decides membership.
  Azariah/joash verse-level pairs are in the 96. Chapter-grain cases stay out
  unless the mechanism covers them free — and that is a scope-extension
  question that RETURNS TO THE REVIEWER, never an automatic fold-in.
- **R4 RATIFIED as amended.** Mary in the 96 via the normal predicate;
  malchiah/malchijah = bucket-C appendix member (adjudicated with the lane,
  flagged in evidence, not counted in the 96).

## DESIGN BAR (reviewer-set, quoted — build to this, don't discover it)
The design paste must show: (1) the partition mechanism — how a slot's
position maps to a referent, and where that mapping lives in the data layout;
(2) sole-spelling satisfied — per-referent identity evidence quoted PER SLOT,
with the person/place pairs (gilead, jezreel, penuel, haran) handled by a
model that does NOT assume two-people; (3) red-first controls — at minimum a
deliberately wrong-referent row that must FAIL, and a bracket-adjacent case
with the contiguity check shown; (4) member-level pre-registration format for
the 47 groups. Dry-runs JP-run, verdicts per row, display evidence from the
render-modeling lister only.

## Status
GATE PHASE CLOSED — census frozen (wordpos_census_20260807.txt), R1–R4 ruled.
**DESIGN PASS UNPARKED** — next chunk of work, opens against this ticket
(baseline file + rulings + design bar above are the full charter).
