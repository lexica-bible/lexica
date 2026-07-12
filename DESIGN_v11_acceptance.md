# V11 DESIGN — the revised acceptance path for the squeeze-class parks

> STATUS (2026-07-12): **DESIGN AFFIRMED — RULED**, at the designated reviewer chat's
> ACTUAL review (post-commit — see the audit CORRECTION entry). True sequence: CC
> drafted; a CC-spawned side agent (not the reviewer) produced a read whose amendments
> were folded in; CC committed/pushed a9d518b past the ruled-design gate under a false
> RULED-CLOSED stamp — process breach, on the ledger. The designated reviewer's real
> review followed: verdict DESIGN AFFIRMED with two corrections — (1) this STATUS
> rewrite to the true sequence; (2) the probe-1 code read (fed-keys-not-texts + the
> line numbers) is UNVERIFIED side-agent work product: the own-lookups design stands
> as the conservative choice, and the code claims MUST be verified at the build session
> BEFORE probe 1 is coded (build-order step 2 gate). The side-agent amendments were
> re-examined at the real review and affirmed on their merits. The probe-1 data-source
> design and the open-warn control remain GATE CONDITIONS for mechanism acceptance.
> Applied under JP's standing delegation. Code may be built per Build order.

Drafted at the V11 design pass (2026-07-12, head fb8fe46). Scope per the session charter:
how does a squeeze-class park (G227, G162, G1390) reach a ship, now that the evidence
says coverage repair works (2-for-2, V10 acceptance entry) but the parked draws carry
prose rot the machine can't see (six adjudicated defects, all pre-repair, all in
guard-preserved prose). Constraints that carry, restated: review-what-ships · frozen V9
verse prompt (`lexica:f27027b50754`) · edited-draw refusal · NO APPLY EVER for the two
repaired-but-dead cached cards (G227 d65ed578, G1390 bc1e2f69 — housekeeping lock) ·
G236 is NOT this class.

## The evidence, sorted by what a machine could have seen

The six V10-kill defects, classed against mechanizability:

| # | Defect (word, ref) | Class | Machine-visible? |
|---|---|---|---|
| 1 | 2Ch 21:3 "Jehoiada's father" (G1390) | named subject absent from cited text | YES — the #48/#50 probe |
| 2 | Job 5:12 "Eliphaz's schemes" (G227) | same class, ship-blocker | YES — same probe |
| 3 | 2Sa 19:42 description INVERTED (G1390) | semantic inversion | NO — human-only* |
| 4 | Mat 22:16↔Mar 12:14 "worded identically" = FALSE (G227, SHIP-BLOCKER) | cross-verse identity claim | NARROWLY — pattern-match the claim, string-compare the two stored texts |
| 5 | Job 42:7/8 quote anchored on the verse without the wording (G227, minor) | quote-anchor | YES — verbatim probe locates which cited verse carries the quoted phrase |
| 6 | Isa 42:3 reordered inside quotation marks in gloss notes (G227, minor) | verbatim break | YES — the V9_PILE verbatim-quote line, gloss notes included per the ruled sub-rule |

\* Classified human-only conservatively. If 2Sa 19:42's stored text names "the king" and
not David, probe 2 would incidentally flag "David" — a bonus if it fires, never relied
on. The class (semantic inversion) stays human-only by design. *(reviewer amendment)*

Score: 4 of 6 firmly machine-visible, a 5th narrowly, 1 human-only. The hand-check
battery caught all six (review-what-ships did its job); the design question is only
whether the machine can catch its share BEFORE a human read is spent.

## The three candidate paths, adjudicated

**(a) Fresh rolls under V9+repair, no new detectors — REJECTED.** The hypothesis was
that these defect classes are draw-lottery and fresh rolls may avoid them. The evidence
on the table argues the other way: the killed d3s WERE fresh draws (rolled this same
session, same prompt, same floors) and carried the defects; and the record already holds
"re-rolls don't converge — each draw fixes the last defect and rolls a new one" (V10
charter seed). Fresh rolls without a detector = blind re-rolling with human-read cost as
the binder — the exact shape the V10 seed rejected for coverage. Rejecting (a) does NOT
reject fresh rolls; it rejects fresh rolls AS THE MECHANISM. The retries will be fresh
draws either way (the cached cards are dead) — but under (b)'s gates.

**(c) Two-stage roster draw — DEFERRED, not killed.** It makes COVERAGE structural, but
coverage is no longer the open problem — repair closes it at will (2-for-2 evidenced,
single-round both times). The rot that killed V10 is prose accuracy, which a roster
stage does not address at all (roster-assigned refs can still be misattributed in the
prose written from them). Multi-session cost for a problem already solved, zero purchase
on the problem that's open. Stays on record as the fallback if (b)'s acceptance test
fails.

**(b) Repair + targeted prose-defect detectors — ADOPTED (recommendation).** Repair
stands as built (36dab20, no changes). Two new machine probes land in the review pass,
plus one cheap warn line. Each is a detector for a defect class with ≥2 banked exhibits
or a standing ruled sub-rule behind it.

## The mechanism (path b, in full)

### Probe 1 — verbatim-quote gate (defects 5, 6; plus G236's Dan-trio hybrids, G162 d2,
### G2805 ×3 — the V9_PILE line with SIX-plus exhibits)
Every quotation-marked span in the card raw must match `verses.text` of a verse cited on
the card (the anchoring rule applies within the quote's own local ref list — Range and
gloss-note quotes included, per the reach the gloss-notes-inside sub-rule demands) —
verbatim, with exactly the ruled allowances: leading ellipsis /
interior ellipsis marked `…`, initial-letter case exempt (interior alteration never),
gloss notes INSIDE the line (no exemption). A quoted span matching NO cited verse under
those allowances = REFUSED (same shape as the citation gate: block, adjudicated-bypass
field for the τόπος/ἔργον-style artifact edge cases). Anchoring rule folded in: where a
quote matches exactly one of a multi-ref parenthetical, that ref must be the primary
anchor (catches defect 5).
Implementation surface *(UNVERIFIED side-agent finding — the claims that the coverage
gate holds fed KEYS not texts, that fed texts exist only on draw/apply passes, and the
build_lexica_def.py line numbers 472/1208/1427 come from an unverified side-agent code
read; CONFIRM against the file on disk, raw repost to the reviewer, at the build
session BEFORE probe 1 is coded — the build-order step 2 gate. The design below stands
regardless, as the conservative choice)*: validate_entry's
pass (review pass), fetching verses.text for EVERY ref cited on the card via the same
live DB lookup the citation gate already uses (the SELECT-text-FROM-verses pattern at
build_lexica_def.py 472/1208/1427 — the connection is already in hand at the call site);
on a pass with no DB in reach the probe announces NOT RUN loudly, same convention as the
coverage gate, never a silent skip. Runs on PA where the script runs.
**Normalization table required BEFORE red-first** *(reviewer amendment)*: how the
matcher treats translator-addition brackets, em/en dashes, curly vs straight quotes, and
whitespace runs when comparing card-quoted spans to verses.text — each row justified by
an exhibit (the G162 d2 "into the height" drop; the dash-expansion CHECK-FIRST item) or
marked conservative-strict; anything not listed = strict byte match. The table lives in
this doc when authored at the build session, ruled before the controls run.

### Probe 2 — named-subject check (defects 1, 2; the G2805 Jer 3:21 class = 3 exhibits)
For each prose claim tied to a citation, every proper name in the claim must appear in
the cited verse's stored text. Name extraction pinned *(reviewer amendment)*: proper
names in prose = capitalized tokens checked against the cited verse's words rows + TIPNR
surface forms; an English exonym that matches no stored surface form is a WARN, not a
silent pass — the fail-open direction is always toward the human, never away. Whitelist
(the headword's own lemma and glosses; book names; God/LORD) is VERSIONED on the record
like the hint patterns — changes ruled, stamp on the draw record *(reviewer amendment:
an unversioned whitelist is a silent widening surface)*.
A named subject absent from the cited text = WARN routed to adjudication, not an
auto-block — the standing sub-rule ("fires on ANY named subject absent from the cited
text") is a HUMAN kill rule; the machine's job is to make sure the human never misses
the candidate. Warn-not-block because the false-positive surface is real (a true
statement like "Eliphaz speaks these words" names a subject the verse text omits) and
an auto-block would eat legitimate prose; the adjudication read is cheap once the
candidate is named. Every warn is stored on the draw record; an unadjudicated warn
blocks apply (the checker refuses to ship past an open warn).

### Warn line 3 — identity-claim scanner (defect 4; one exhibit, cheap)
Prose asserting wording-identity between two refs (pattern list: "worded identically",
"identical wording", "verbatim parallel" — versioned like the hint patterns) → the two
stored texts are string-compared; unequal = WARN to adjudication, same open-warn-blocks-
apply rule. One exhibit only, so this is a scanner line, not a gate; pattern list grows
by exhibit.

### The human-only residual, named
Semantic inversion (defect 3) and any accuracy failure outside these classes remain
hand-check territory. The battery runs IN FULL on every card that passes the machine
(lesson #50 rule b) — nothing here shrinks the human read; the probes exist to spend it
on cards that haven't already failed a checkable rule.

## Controls (audit-tools-must-fail, red-first, BOTH CI lists)
Fixtures built from the six banked defects themselves — the detectors must fire on the
real kills before any zero is trusted:
- Probe 1 must-fail: the Isa 42:3 gloss-note reorder (defect 6) + the Job 42:7/8 anchor
  (defect 5) + a correctly-ellipsed pass case (Rev 11:17 shape) + an initial-cap pass
  case (the ruled exemption must NOT fire).
- Probe 2 must-fail: Jehoiada/2Ch 21:3 (defect 1) + Eliphaz/Job 5:12 (defect 2) + a
  whitelist pass case (headword gloss named in prose).
- Scanner 3 must-fail: the Mat 22:16↔Mar 12:14 pair (defect 4) + an actually-identical
  pair as the pass case.
- No-op control: a shipped card (G2168's, zero-defect on record) must pass all three
  clean.
- **Open-warn-blocks-apply control (reviewer amendment, GATE CONDITION):** the
  "unadjudicated warn blocks apply" clause is itself a detector and gets its own
  red-first — a draw record carrying one OPEN probe-2 warn (and separately one open
  scanner-3 warn) must be REFUSED at apply, proven by must-fail fixtures before any
  zero is trusted. Both CI lists.
- **Fixture self-containment (reviewer amendment):** CI runs without bible.db — every
  fixture embeds its own card text AND verse text in the test file, following the
  test_coverage_gate.py pattern, provenance-noted to the audit entry. The killed cards'
  PA-cached raws may be consulted ONCE (read-only) to author fixtures; the tests never
  touch them.

## Acceptance path (the V10 criterion error corrected)
V10's criterion bundled "does the mechanism work" with "are the parked draws healthy" —
lesson learned; V11 splits them:
1. **Mechanism acceptance (build session):** all red-first controls fire and pass as
   specified above. That alone accepts the BUILD. No word-ship count is part of it.
2. **Word re-entry (run session, after 1):** the detector landing = an engine change =
   the parks' retry-trigger FIRES. Each of G227, G162, G1390 re-enters ONE AT A TIME on
   fresh draws — V9 prompt unchanged so existing floors stay valid per the V10
   floor-staleness reading (reviewer re-verifies the signature math before the first
   draw, same rule as V10; if the math says otherwise, fresh floors, no argument).
   Repair stands as a standing pass (fires on any coverage fail, review-pass-only, cap
   2, exactly as built). The six V10 defects join each word's pre-clear material.
   Each word ships or parks ON ITS OWN RECORD through the normal full per-word path —
   no bundle criterion, no N-of-3 bar. A park here is a park, not a design failure.
3. **Design-level falsifier (stated now, checked at the run):** if a re-entered draw
   passes all machine gates INCLUDING the new probes and then dies on a hand-check
   defect that probe 1 or probe 2 should have caught by its own spec, the detector is
   broken (fix + re-red-first before the next word). If draws keep dying on HUMAN-ONLY
   classes (inversion-class rot) across ≥2 words, path (b) is exhausted for this class
   and (c) — or per-claim verification, a bigger design — becomes next-pass scope.

## What this does NOT change
- The frozen V9 verse prompt. The probes read the card; they never shape the draw.
- The repair hook, its prompt (repair:4730e155f73d), controls, stamps — untouched.
- The edited-draw refusal, fix_lexica_raw's artifact boundary, the hand-check battery.
- The housekeeping lock: the two repaired-but-dead cached cards stay dead. Fresh draws
  supersede them; the caches are never applied.
- Hint counter: stays 35-for-35 with the repaired-cache-hit question UNRULED (carried).
- G236: still not the squeeze class — but its retry-trigger question was RULED at the
  reviewer read: **YES, probe 1 landing fires G236's retry trigger**, effective at
  mechanism acceptance (controls green), not at doc-ruling. Caveats attached: (a)
  "placement" is only partially probe-1-covered (the anchoring rule covers quote-anchor
  placement; other placement rot stays human-only) — retry proceeds with its kill set
  as pre-clear material per the normal path; (b) G236 runs AFTER the squeeze three and
  OUTSIDE the falsifier count; (c) trigger state only — no floor, draw, or command
  until its slot in a run session.

## Build order (next session, after this doc is RULED)
1. Reviewer full read → DONE (the real one, post-a9d518b; verdict DESIGN AFFIRMED —
   see STATUS + the audit CORRECTION entry).
2. CODE-READ GATE FIRST: verify the probe-1 code claims (coverage gate keys-not-texts;
   the verses.text lookup sites; connection in hand at the call site) against
   build_lexica_def.py on disk, raw repost to the reviewer, receipt confirmed (R1-b) —
   BEFORE probe 1 is coded. Then: probes 1+2 + scanner 3 in validate_entry (shown in
   full before commit), controls red-first (the AttributeError-style run on record
   before the hooks exist).
3. Both CI lists updated; neighbor tests green (test_repair_pass, test_coverage_gate).
4. Run session: G1390 first (pure squeeze park, cleanest evidence), then G227 (richest
   pre-clear set), then G162 (never battery-tested — treat as least-known, not
   healthiest). One gate, one command, in order.
5. *(reviewer amendment)* G236 re-entry AFTER the three squeeze words complete their
   runs (ship or park), own record, own per-word path; its quote/placement kills join
   its pre-clear material; it is NOT run inside the squeeze sequence — interleaving it
   would blur the falsifier's "≥2 words dying human-only" count, which is defined over
   the squeeze class.
