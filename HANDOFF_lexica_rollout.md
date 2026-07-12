# HANDOFF — Lexica definition-engine rollout (batch 2 / calibration)

Fresh-session handoff for continuing the frequency rollout. **The audit doc
`AUDIT_lexica_rollout.md` is the AUTHORITY** on saga details (commits `e8d42b5`, `67b4086`,
`d7695eb`, `91f74da`, `a06a90b`, `81cd58a`). This file is the rule-state + task-state summary;
where they seem to differ, the doc wins (lesson banked from a πολύς/G80 conflation this session —
trust the doc, not chat memory).

## PRE-REGISTERED EXPECTATIONS CARRIED FORWARD (must NOT soften in transit)
1. **The four-gate ship bar** is the ship test — not sense-count matching. Do not reintroduce
   "match the reviewer's count" by any back door (demanding a redraw purely to change a count is
   exactly that).
2. **The escalation trigger stays armed** at one-more-wall (see below). A third content-wall trips
   the mechanism decision to JP immediately — it does not wait for the retro.
These two are the load-bearing ones. Everything else below supports them.

## DOTTED-LEXICON CONTAMINATION (2026-07-07, ὄρος session) — HOLD-OUT FLAGS ARMED
A dotted Strong's number that is a DIFFERENT word from its base can leak into the base word's
Lexica floor if it is missing from `dotted_lexicon`. Two classes found + status:
- **FOLD class — FIXED.** `build_dotted_lexicon.py` compared a dotted number's own word to the
  base with `bare()`, which strips breathing AND accent, so near-homographs folded together and
  the different word was dropped (ὄρος mountain vs ὅρος boundary; νόμος law vs νομός pasture). Fix:
  `same_word()` — case/final-sigma-insensitive but breathing/accent-SENSITIVE (commit `2ff5f7d`).
  Rebuild adds exactly 5 numbers (G3735.1 ὅρος, G3551.1 νομός, G4224.1 ποτός, G53.1 ἄγνος,
  G5606.1 ὠμός), removes 0. **REBUILT + LIVE 2026-07-07; closes the fold class corpus-wide.**
  **ὄρος G3735 SHIPPED** at one sense on the clean 641-row feed (floor
  `agreement_G3735_v6_20260707-221141` = STABLE-at-1; draw-1's 2-sense "encounter-site" split
  REJECTED on the double-shelf gate — Exo 3:1/Neh 9:13/Num 3:1 in both senses — clean re-draw
  shipped, cache key `65dfcf90`, citation gate 36/36). **POST-SHIP PROSE FIX (same day):** the
  rendered card exposed 4 byte defects the four-gate never read (it audited fields, not the prose
  body) — a leaked title + `---`, "Giboa"→Gilboa typo, a "Sub-uses include:" stutter, a malformed
  Zion sub-use. Fixed by `fix_lexica_raw.py` (no model call, senses untouched) + split hardening
  (`9a1dca9`); gate re-passed 36/36. Root lesson → the PROOFREAD GATE below.
- **NO-ENTRY class — LOGGED, NOT fixed (~90 dotted numbers, mostly the δ-cluster).** No `abp_ext`
  dictionary entry, so the builder can't recover them; they still leak. Mix of real foreign leaks +
  harmless same-word forms — separating them is the ticket's first job.
- **⚠ HOLD-OUT FLAGS — do NOT run a floor on these before the no-entry ticket lands or a manual
  hold-out is placed:** **δοξάζω G1392** (skin/doe), **διώκω G1377** (aqueduct/poles/stories),
  **δόξα G1391** (glory/glorious — low-risk same field, still flag). They carry no-entry leaks.
- **δίδωμι G1325 (SHIPPED) — RESOLVED:** only leak is 1325.1 "mortgaged" at Neh 5:3 (no-entry, not
  held out by the fix). Direct check ran: **NOT cited** in the live card → card STANDS with a one-line
  provenance note (feed cleaned post-ship, no card change; the 1-row leak persists pending the no-entry
  ticket). Re-ship only if the no-entry remedy changes it.
- **POST-ROLLOUT TICKET — "dotted-number full audit":** separate same-word rows from true foreign
  leaks · no-entry remedy design · inverse-direction audit (dotted rows on the list that map wrong;
  bare rows that should have been dotted) · homonym heuristic (wrist-under-fruit, same spelling —
  invisible to any comparator) · εἰμί-anomaly resolution (bare G1510 base_occ=1) · the 2 blank
  abp_surface `form` cells (Isa 19:2, Eze 40:12). Merges with the parked ὀρ-collision sweep.

## HANDOFF PROCEDURE (standing, adopted 2026-07-09 after the session-1→2 handoff failure)
**CC is the sole author of both handoffs** — the CC-opener block AND the reviewer-chat inheritance
block. The reviewer chat writes no handoff. (Session 1→2 had two authors: the two handoffs
conflicted on the watch tally, and the chat handoff carried a five-item correction set as a bare
count — unverifiable, three rounds of stuck back-and-forth.)

**During the session** — reviewer-chat state flows to CC as it happens, not at close:
1. Any pre-registration, watch, or ruling made in the reviewer chat gets relayed to CC when it's
   made (the existing "line for CC" pattern). CC banks it in the session log immediately.
2. If it wasn't banked with CC, it doesn't exist at handoff. No end-of-session memory dump from
   the chat.

**At close, in this order:**
3. JP asks the reviewer chat ONE question: "anything armed that isn't banked?" Anything surfaced
   gets relayed and banked. That is the chat's entire handoff duty.
4. All pending writes land → close commit → THEN CC writes both handoff blocks pointing at that
   commit. Handoff written before the close commit is invalid.
5. JP pastes the CC block into the new CC session and the reviewer block into the new chat.

**Content rules (CC-enforced when writing the blocks):**
6. Docs are the single source. No tally, procedure, or case-law item is restated — point:
   "state per close-out at commit `<hash>`." Any number in a handoff must be findable in a
   committed doc at that hash.
7. Every verification gate ships with its clearing procedure: commit hash + exact grep string or
   expected header + pass condition. A gate without a one-command clear is malformed — rewrite it
   before the close commit.
8. No counts without contents. "Five corrections" is banned; list the five verbatim, or point at
   the commit where they landed, or the item doesn't ship.
   - **Corollary (roster-gap incident, 2026-07-09): a close-out that references a LIST must commit
     the list, not its length.** The batch-3 roster lived in chat from approval onward; the close
     banked the tally (in the arithmetic) but never the names (in no tally) — same class as the #27
     tracking-slot lesson. Close-out check: every list the log references exists verbatim in a
     committed doc.
   - **R4 (2026-07-09, see SESSION-DISCIPLINE RULES below): a named procedure ships with its
     exact verified invocation, not just its name.**

**Receiving-instance rule (both CC and chat, next session):**
9. A gate that can't be cleared by its attached procedure converts to a logged caveat
   ("accepted on standing evidence, unverified: <item>") — not an indefinite hold. Holds are for
   failed checks, not missing ones.

## SESSION-DISCIPLINE RULES R1–R4 (standing, drafted 2026-07-09 — post-mortem of the
## splitter-fix session's opening fails; fail record = audit doc post-mortem entry)
- **R1 — Commands are verified, never recalled.** Any command handed to JP for execution is
  verified against the script on disk (name, flags, semantics) BEFORE handover — never written
  from recall. Cheap visible form: a one-line "verified against scripts/<name>" preceding the
  command block. This extends the existing verify-before-claim term from claims to commands: a
  command line crossing the CC→JP boundary IS a factual claim (ENGINE_LESSONS #39).
- **R2 — Named procedures use their designated instrument.** Floor, cert, rebuild, and any
  other named procedure run via their designated instrument script (floor =
  `lexica_agreement.py --runs N`; cert = `cert_invariants.py`; rebuild = `/rebuild-words`).
  Ad-hoc reconstructions are REJECTED even if functionally plausible. Reason: comparability —
  improvised output can't be read against prior runs, which silently corrupts the series even
  when the improvisation is correct.
- **R3 — Holds are blocking.** An open hold means the only legal next-message content is that
  hold's clearance (or stop-and-report). No parallel progress while a hold is open; "clear it
  next message" then moving to other work is a violation. Unaccounted output crossing a
  checkpoint (a number, filename, or line with no explanation) AUTO-OPENS a hold — it must not
  take JP or the reviewer noticing (extends ENGINE_LESSONS #38's accounting term).
- **R4 — Handoffs carry commands, not just procedure names.** Any handoff that tells the next
  session to run a named procedure writes out the exact invocation (script + flags) verbatim,
  R1-verified. "Run the floor, straight to 10" is insufficient; the standard is
  `cd ~/bible-db && python scripts/lexica_agreement.py --word <ID> --runs 10`. (Amends the
  HANDOFF PROCEDURE content rules above — a procedure name without its invocation is malformed,
  same class as a gate without its one-command clear.)

## AVAILABILITY CONSTRAINT — STANDING (JP ruling 2026-07-10, session 6; banked ahead of wrap
## because it governs the very next session's opening)
JP relocates cross-country + starts a new job within 1–2 weeks of 2026-07-10. **JP's hours are
variable; batch decisions when he's away, work normally when he's present.** [Wording replaced
2026-07-10 per reviewer relay — the prior "multi-day gaps possible / the engine degrades to
SLOWER, never to STALLED" line was framing drift: a true fact inflated into an unrequested
design mandate. The ruled operational consequences below are unchanged.] Ruled operational
consequences:
- **Async-tolerant sessions:** every session opens from docs alone (the handoff test is now the
  norm, not the fallback). No session may depend on same-day JP follow-up. Anything needing a JP
  ruling banks as a PENDING item with evidence attached; the session proceeds on everything else.
- **Ruling batching — AMENDED (JP standing rules, 2026-07-10, via reviewer relay):**
  (i) **The DEFAULT at a decision point is ask-in-chat, live, hashed out there** — the doc
  entry RECORDS the decision; it is not the medium of deciding. Batched decision lists are
  for GENUINE ABSENCES only (then: one list per close, each item one line + the number it
  turns on + recommendation attached; lead with the ask, evidence below; JP rules when
  present, any device, any order).
  (ii) **Anything that reaches JP is written in PLAIN TERMS — what happens, what changes,
  what it costs.** Dense technical blocks are CC↔reviewer traffic only. (Exhibit: the step-4
  12-item list arrived as jargon and required a full re-explanation in chat; the re-explained
  items 2 and 6 are the model.)
- **Priority order under constrained attention:** (a) the 10 owed count-eligible GREEN ships
  (buy GREEN activation → the easy 80% then ships with zero JP read) — but see the step-3 sequencing
  consequence: #30 must be live first, so (b) actually leads; (b) step 4 V8 pile triage + #30
  un-park (opens the insurance clause's final-10 window); (c) RED/loaded words ONLY in real JP
  review windows — they permanently need him and don't rush; (d) layout/surface work (step 6) is
  JP-independent, schedule into gaps.
- **What does NOT change:** committed wording governs · R1–R4 · #38 accounting · two-tier bar as
  adopted · the variance watch tags · **no ruling is ever inferred from JP's silence — silence =
  pending, not approval.**

## STANDING LAW (the rules this session generated)
- **FOUR-GATE SHIP BAR** (replaces count-match). A draft ships if it clears all four, whatever its
  sense count: (1) **no holes** — every stable reviewer job present + distinct; (2) **no merges** —
  no collapse of a majority-distinct distinction; (3) **completeness** — every reviewer-attested
  facet visible somewhere (own sense, thin sense, or explicitly in the range), nothing silently
  dropped; (4) **granularity ships as drawn** — finer/coarser within the reviewer's observed
  distribution is fine, verse-supported flickers ship as thin senses (G80 standard, applied
  symmetrically). Plus the standing gates: citations clean, dangling empty, collocation flags
  adjudicated, loaded-frame, senses ≤ occ.
  - **Gate-3 precedent:** inline verse-level naming inside a sense satisfies gate 3 (καρδία's
    relational-presence at 1Th 2:17). Visible-at-its-verse counts as "visible somewhere."
  - **Gate-3 detector:** the uncited-rendering flag; control case = πολύς attempt-3 dropped 'long'
    (13× uncited).
- **REVIEWER FLOOR:** every word gets `lexica_agreement.py --word G#### --runs 3` before ship;
  escalate to `--runs 10` on any appear/vanish, merge, or job-boundary wobble in the 3. No word
  ships on a single draft's structure.
- **PROOFREAD GATE (NEW, ὄρος 2026-07-07 — the four-gate audited structured fields but NOT the
  prose body, so a typo/stutter/broken-fragment shipped).** Print and READ the full `senses_block`
  at gate time (now auto-printed by `show_entry`, commit `9a1dca9`), and verify the RENDERED card
  via a screenshot before close-out — not the pasted terminal text (paste flattens layout and
  invents phantom run-togethers). Candidate for the formal V7 gate list.
  - **EXTENDED to `gloss_notes` (θυγάτηρ 2026-07-07, commit `be027c1`):** `gloss_notes` was still a
    400-char PREVIEW (`… ` cutoff) — the same "char count isn't the artifact" gap. Now prints in full
    with its own PROOFREAD label. Proofread BOTH `senses_block` and `gloss_notes` at the dry-run gate;
    `gloss_notes` renders to the reader (both bullets, screenshot-confirmed on θυγάτηρ), so a byte
    defect past char 400 would otherwise reach the card.
  - HABIT (not a gate): for a `fix_lexica_raw` round, run dry-run → review → apply as TWO
    exchanges, not apply-in-the-same-pass. The exact-once abort makes it near-zero risk either way,
    but the split review is cleaner.
- **SESSION LOG (2026-07-07, ὄρος):** dotted-lexicon fold fix shipped + live (`2ff5f7d`, draw 641);
  ὄρος card shipped at one sense then corrected in place for 4 prose defects (no re-draw, certified
  senses untouched; `fix_lexica_raw` + `9a1dca9`), rendered clean + screenshot-verified; δίδωμι leak
  resolved (not cited); streak 0 into θυγάτηρ; dotted-number audit ticket sized + hold-out flags armed.
- **GRADUATION RULE (audit-intensity relaxation).** Verbatim: *"Manual audit relaxes when 2–3 consecutive
  words ship clean at attempt 1 with no new defect classes, no new watch entries, and floors in the predicted
  bucket. At that point: spot-audit becomes the default; full manual audit only on flagged words."*
  - **RULING (2026-07-07, pinned so the criterion isn't adjudicated retroactively):** **φωνή does NOT open the
    streak.** Its senses passed clean, but the audit PROCESS required correction — two standing-rule checks
    (fed-list verify, gloss-note spot-verify) were skipped in CC's first verdict and had to be prompted. "Clean
    at attempt 1" means the audit ran clean, not just that the card was right. Streak counter = 0 going into
    ὀφθαλμός.
  - **RULING (2026-07-07, ὄρος):** **ὄρος does NOT open the streak either.** Attempt-1's floor grew a false
    "boundary" sense; the cause being a data defect (dotted-lexicon fold gap) doesn't rescue it — the pass
    did not run clean. **Streak counter = 0 carrying into θυγάτηρ.**
- **REDRAW DISCIPLINE:** cap **3** off-target `--dry-run --force` pulls, then stop to JP. Drawing
  until the draft matches the reviewer-established structure is audit-against-known-structure, NOT
  draw-shopping (every draw gets the full audit). `--from-draw` refuses EDITED drafts by design —
  "hand-tune the split" can never mean editing the draw JSON.
- **SPIRIT-FRAME BOTH-WAYS BAR** (for πνεῦμα-adjacent / fork-companion senses): reject BOTH
  creedal-procession/person language ("proceeds from", "a divine person") AND impersonal-ontology
  language ("power / force / agent / medium" asserted as what it IS). Accept doing/relation-level
  description only. **Neutral ceiling reference = "qualifying πνεῦμα as a compound expression"**
  (grammatical, asserts no ontology). A stable job can still fail on frame.
- **ESCALATION TRIGGER (armed).** Content-wall tally: πολύς = 1 full cap-out (range-completeness);
  ἅγιον = near-wall (2 rejects, structure, cleared attempt 3). **A third cap-out on ANY binding
  constraint (range, structure, OR frame) trips the mechanism decision to JP immediately.** Option
  space (named, not decided): higher-cap draw-until-match · prompt-steer + re-prove cycle · a
  per-word structure-hint channel passing the reviewer's stable-jobs list as draw CONTEXT without
  touching the frozen VERSE_PROMPT.

## V7 WINDOW — CLOSED (2026-07-08). Engine = V7. Read this block to resume; older state below is history.
**The walk:** format decision → ten-pile items + item 11 → retro list under the 6,000-frame → bump.
Every ruling JP's, one at a time; full ledger on the V7 PILE header below.
- **ENGINE V7 LIVE (`b8cbe7c`):** six prompt edits (line→entry ×2 · two-directional gloss flag, "more
  doctrinally specific" kept one-way DELIBERATELY — flattening covered by broader/less-loaded, not a missed
  symmetry · headline scope marker · **Sub-use placement rule** (files by JOB, not imagery — the ὀφθαλμός
  wall; control fire = ὀφθαλμός at requeue, **two-way placement watch pre-registered**: mis-files curing AND
  previously-correct filings moving both get logged on first V7 draws) · house-shape line (JP format ruling:
  HYBRID — em-dash headline stays norm; ἔτος organizing paragraph codified for one-job-many-frames; labeled
  own-line items where citations cluster; rationale rests on citation density ALONE — the watch-#3 "readability"
  attribution was corrected against the doc: cosmetic convention divergence, no parse risk) · gloss-note sense
  anchors, permissive, JP wording ("no sense to anchor stays unanchored" = load-bearing, fabrication door) —
  codifies the observed late-batch anchoring drift (11/12 notes anchored on the last 3 ships; sweep table in
  session log). Stamp `lexica:6f982c804354` (inert). Reviewer `V7_PROMPT` byte-identical; default `v7`.
  `trial_lexica_prompt.py` DELETED (throwaway rig; history in git).
- **FLAG-ONLY DETECTOR SUITE LIVE (`5831175`), all control-fired (tests/test_lexica_detectors.py, CI+hook):**
  rendering-claim lint (case-awareness LOAD-BEARING, docstring-pinned, οὐρανός fire is the reason; ἁμαρτία
  "sin"/"sin offering" = the rend-compare control) · hedged-citation lint (7c assist; list pinned
  NON-EXHAUSTIVE — a pass is NOT 7c satisfied) · sub-use overload counter (4+ → merge-review; NO ceiling,
  #14; control positive = ῥῆμα sense 1 at exactly 4, a legitimate card) · **CONTESTED-VERSE REGISTRY**
  (`contested_register.CONTESTED_VERSES`; #24 ῥῆμα refinement — verification scales with VERSE contestedness;
  seeded 2Co 5:21, dossier bar VERBATIM + cite; a hit is ROUTING not a flag: mandatory verse-text verification,
  word leaves the zero-read tier).
- **DYNAMIC FED SAMPLING LIVE (`c7f8620`):** ≤40 occ feeds ALL (fed-gap family impossible by construction;
  **measured: 4,017/5,254 Greek lemmas = 76% at ≤40**); tiers 40/60/80 above; top-10 PMI neighbors each
  GUARANTEED a fed verse (#8 option (b)). Cost "roughly flat" = PROJECTION, not measurement. **MIRROR
  INVARIANT:** reviewer + audit_lexica_coverage recompute the fed draw exactly as the build (else the floor
  certifies the wrong inventory, #19 at tool level).
- **REVIEWER TIERING LAW (JP-approved, the 6,000-frame; 0-for-17 was the problem statement, and it
  over-states the corpus — batch-2 was the hand-picked hard top):**
  - **GREEN (ships with ZERO JP READ — machine gates stay; CC spot-check rate set at calibration):**
    pre-draw screens ALL pass (≤40 occ · no contested-register hit · no CONTESTED_VERSES hit · no
    loaded-referent list hit · not fork-adjacent) AND post-draw ALL pass (floor stable at `--runs 3`
    MACHINE-SCORED — any tool warning auto-escalates to 10 and the word leaves GREEN, no judgment call ·
    hard gates green · ZERO fires across the whole flag suite). One fire of anything → AMBER.
  - **AMBER:** JP reads ONLY the flagged region. Thin senses fold in here (7b test, one glance).
  - **RED:** register/registry/referent hits, escalated floors, walls, high-occ — full current process.
    Batch-2-class words live here permanently.
  - **No pre-classification of floor depth** — the tight-agreement predictor was dented 3× (ὕδωρ, φωνή,
    ἔτος); auto-escalation on the tool's own warnings is the classifier.
  - **SHADOW CALIBRATION pins (pre-registered):** activation bar = ZERO escapes (JP-caught,
    nothing-flagged defects) across a stated N of GREEN-tier words; **N proposed by CC BEFORE batch 3
    opens, never adjudicated after**; calibration BLOCKED until all four detectors control-fire (done,
    `5831175`) — GREEN is earned by measurement, never assumed. Any escape → new detector/screen,
    recalibrate.
- **POST-V7 ROLLOUT SEQUENCE (JP, on the record):** **Phase 1** — requeue AS the V7 control fires (next
  session; 3 words, single runs, full audit): χριστός (fork machinery + register write, HELD until its
  session) → ἁμαρτία (verse registry + rendering lint on the exact defect that parked it) → ὀφθαλμός
  (placement-line known positive; restructure decision JP-alone). These three ARE the V7 validation.
  **Phase 2** — batch 3 = shadow calibration (~20 words, composed: majority GREEN-candidates + seeded
  RED so all routing exercises; JP audits everything; escapes are the measure). **Phase 3** — throttle by
  measurement: zero escapes → GREEN activates, batch sizes grow (50 → 100+), JP's read shrinks to
  AMBER/RED + spot rate; any escape → detector, recalibrate. Batch size is governed by escape rate, not
  schedule. **Metric restart:** graduation streak resets under V7; clean-at-attempt-1 is the leading
  indicator for 6,000-on-this-engine vs needs-a-V8.
- **SESSION LOG (V7 walk, 2026-07-08):** MISSED-collocation sweep RAN read-only over all 18 shipped cards —
  **16/18 fully clean, zero senses lost corpus-wide to date**; two candidate reads folded into the
  consolidated re-audit, NOT opened (ἅγιον+κλητός occasion-job; οὐρανός+βασιλεία metonymy, the known #4
  blind spot). Gloss-note anchoring sweep: late-jump drift, real + desirable → codified (table in chat log;
  0–1 loose refs words 1–15, 11/12 anchored on ἄρχων/δύναμις/ῥῆμα). κύριος exhibit verification CLOSED:
  V1 flowing style carries citations as TERMINAL per-sense ref-lists (35 refs in one parenthesis) —
  detaching evidence from claims; strengthens the hybrid ruling; byte-exactness not certifiable through the
  fetch layer and not needed. Display-layer/three-zone question resolved: = the two tickets (gloss-note
  sense-anchoring markers · canonical note ordering); JP ruled HOLD for the three-zone redesign — with
  anchors codified, the superscript ticket is now a PURE RENDERING job over data the cards carry.
  ENGINE_LESSONS #26 (wording-audit finds are hypotheses — the 3/5 pattern) + #27 (mid-session items need
  the manifest catch-net; two list-boundary drops caught at bump assembly). Config-test tally: 1 correction
  (watch-#3 misattribution, JP-caught, recovered by quoted record), high-quality recovery.

## PHASE-1 SESSION LOG — χριστός G5547 SHIPPED + LIVE (2026-07-08, first V7 control fire)
Full per-word record: audit doc `### G5547 χριστός`. The standing facts a next session needs:
- **Register = 9 forks now.** χριστός entered (`664add7`): referent fork, loci-bounded
  (`contest_verses = ["Psa 2", "Dan 9:25"]`; Dan 9:26 verified untagged, excluded), NO pin_core
  (θεός/κύριος pattern), core kept inert (title→name diachronic clause cut on JP review).
- **Write-sequencing law (better than the work order — use it for any future fork+rebuild pair):**
  commit register → `git pull` on PA (NO reload — pull alone doesn't reload the app) → floor/draw/apply
  (row lands WITH fork) → deploy/reload. The serve-backstop 404 gap never opens.
- **Ship path:** floor `--runs 3`→10 (boundary wobble escalation; verdict STABLE, 3-carve majority 7/10,
  2-sense merges bidirectional = no competing carve) → 3 plain pulls all failed gate 2 (title job merged
  into name [d2] and into OT [d3]; d1 = double-shelf + off-majority placements) → **cap-out ruled per
  ἄρχων precedent (NOT content-wall, tally stays 3)** → structure-hint draw (3rd use, 3rd success,
  key `a918c5c8`) passed all four gates + all seam-verse majority homes first try → 2 ruled swaps
  (Mar 9:41 out of the "christs" bullet — real lint fire, wrong list member; χρίσμα cross-lemma aside cut)
  → screenshot-verified, 5-point checklist green. **Streak 0** (attempt 4 via mechanism).
- **V7 control-fire results (pre-registered watches, all logged):** dynamic sampling tier-correct
  (607 occ → 81 fed = 80 + 1 PMI slot; mirror invariant held, reviewer printed the same feed) ·
  Psa 2:2 single-shelved 13/13 draws + on the card, registry no over-trigger, no under-trigger ·
  placement watch fired BOTH directions (d1 recruited 1Ch 16:22/Psa 105:15 into an essay-style sense
  against a ~10/10 floor home; hinted draw filed everything on majority homes) · hedge lint 1 noise fire
  adjudicated · rendering lint: 1 REAL fire (d3 claimed "ones" where corpus renders "christs" — first
  genuine live fire) + a confirmed PARSER ARTIFACT (see ticket) · hybrid house shape exhibited as ruled
  (dump where citations are uniform, own-line items where they cluster — first live exhibit; watch the
  "Grounding refs:" label wording across Phase 1, one instance ≠ a rule).
- **NEW V8-PILE ITEM (live-exhibited, #26 bar met): comma-shorthand citations** — "Rom 1:1, 4" /
  "Lev 21:10, 21:12" tails in 4/4 draws; gate-invisible (the ref scanner needs Book ch:vs), which also
  BLINDED the double-shelf detector to d1's Act 2:36 double-cite. Per-card closure = hand-verify the
  tails (24/24 verified via one row-values IN check). ENGINE_LESSONS #28.
- **TICKET: rendering-lint parser artifact** (code-confirmed): `_gnote_claims` keeps the quote marks in
  the captured gloss (`"anointed"` ≠ `anointed` → every quoted gloss fires mismatch) AND cross-pairs
  every gloss with every ref in a bullet. Fix = strip quote chars + keep pairing caveat documented;
  flag-layer only, legal any time, must keep tests/test_lexica_detectors.py control fires green. TODO.md.

## PHASE-1 SESSION LOG — ἁμαρτία G266 SHIPPED + LIVE (2026-07-08, second V7 control fire)
Full per-word record: audit doc `### G266 ἁμαρτία — LIVE` (the requeue entry; the PARKED dossier above it stays
as history). Standing facts for the next session:
- **Ship path:** V7 floor `--runs 3`→10 ({2:4,3:6}, cultic shelf exactly 5/10 → rule 7a; act+condition 10/10;
  2Co 5:21 contested again, no majority shelf) → 3 plain pulls all rejected (side-take on 2Co 5:21 in all three,
  once each direction + once structural; pull 2's anti-offering rendering FABRICATION was invisible to the
  rendering lint — prose-form claim, #24 update) → cap-out per precedent → hinted draw (mechanism 4th use):
  structure + gloss-note register clean FIRST TIME in 7 pulls → JP rulings: 2Co 5:21 either-shelf-legal
  (CC's condition pin was an over-pin; contested-verse standard), 2Th 2:3 + Gal 2:17 keep-both bridges per #11
  ("[partially]" = honest wording), citation-list strips withdrawn (fix_lexica_raw boundary forbids), Branch-A
  insertion withdrawn → **V8 design list** → ONE delete-class swap (register clause → bare rendering quote) →
  gate 78/78 → screenshot-verified.
- **V7 control-fire results:** registry routing caught the side-take every pull (its designed job); dynamic
  sampling data point #2 (582→82 = 80 + 2 PMI slots; step-1.5 ZERO missed warnings — slot reservation covered
  the V6 warning families); rendering lint: 12 artifact fires (quote-mark bug) + 1 real fabrication MISSED
  (prose-form blind spot → detector ticket scope grows); no comma-shorthand tails in any of the 4 draws
  (χριστός contrast — watch continues); "[partially]" list markers = new draw style, ruled positive.
- **ENGINE_LESSONS #29** (V8 input: teach the attribution register — V7 contains but cannot draw it) + #21/#24
  updates. **Render fix shipped `80b87cd`:** range + coverage now through renderInlineMd (live card showed raw
  asterisks in RANGE; latent coverage copy closed same pass; legal mid-batch per rule #7).
- **Streak 0. Phase 1 = 2 of 3.** Next: ὀφθαλμός G3788 — placement-line known positive, restructure decision
  JP-alone, fresh session recommended.

## PHASE-1 SESSION LOG — ὀφθαλμός G3788 SHIPPED + LIVE (2026-07-08, third V7 control fire). PHASE 1 COMPLETE 3/3.
Full record: audit doc `### G3788 ὀφθαλμός — LIVE` (the requeue entry; V6 saga above it is history). Standing facts:
- **Ship path:** fresh V7 floor 3→10 ({3:5,4:4,5:1}; physical + regard 10/10, perception own-sense 6/10;
  **desire/disposition cluster 5/5 physical-vs-not** — the V7 placement rule improved the V6 wall, didn't cure it)
  → JP ruled the pre-registered restructure question: **(b) fresh floor supersedes the V6 bar, 7a either-home-legal,
  gate-3 visibility mandatory** → 3 plain pulls rejected (scatter / 2 ruled misplacements among 5 fires / 0-in-10
  merge) → cap-out per precedent → hinted draw passed all exits first try (**mechanism 5-for-5 structural**),
  zero post-apply edits, screenshot-verified. Hint logged as SELECTING the regard home from two legal options —
  not a placement rule; the 5/5 finding stays live for batch-3 splits.
- **New jurisprudence:** pre-clear adjudicated bridges in the hint's exit terms (pull-2 lesson — a ruled keep-both
  recurring must not force a park) · a single ruled misplacement = redraw (no legal edit path into citation lists)
  · **NEW detector-artifact class: disclaimer-as-cite** (Eze 1:18 "handled under Sense 1" counted as a shelf;
  ticket family with the quoted-gloss artifact).
- **PHASE 1 COMPLETE.** Streak 0 across all three (mechanism ships, standing ruling). **Batch-3 shadow
  calibration UNBLOCKED. CC's pre-registered N = 15 GREEN-tier words, zero escapes; count carries across batches
  if batch 3 routes fewer than 15 GREEN.** Awaiting JP's go + batch-3 roster composition (majority
  GREEN-candidates + seeded RED, ~20 words).

## SESSION-3 HANDOFF BLOCKS (written AFTER close commit 4c7bcc9, per the handoff procedure)

### CC-OPENER BLOCK (paste into the new CC session)
BATCH-3 SESSION 3 — continue shadow calibration.
State source of truth: close commit 4c7bcc9 ("batch-3 session-2 close"). Do not trust any number in
this handoff over the docs at that commit.
READ FIRST, in order: (1) HANDOFF_lexica_rollout.md — "HANDOFF PROCEDURE" block, then the BATCH-3
SESSION 2 LOG block (the running record), then Queue item 4; (2) AUDIT_lexica_rollout.md — session-2
entries (G3900, G2965, G4808, G956 + SESSION 2 CLOSE); (3) ENGINE_LESSONS.md #33–#37 + the #32 update
(+ #30–#32 if not already known).
Opening check (clearing procedure): `git log --oneline -3` shows 4c7bcc9; `grep -c "BATCH-3 SESSION 2
LOG" HANDOFF_lexica_rollout.md` returns ≥1; `grep -c "^37\." ENGINE_LESSONS.md` returns 1. All pass =
cleared, proceed; a failed check = rule-9 caveat, not a hold.
State per the session-2 close at 4c7bcc9 (pointers, not restatements): batch 10 shipped / 2 escapes /
2 parked / count 2/15 / streak 0; remaining 6 GREEN (ταμεῖον G5009 · βιβρώσκω G977 · διανοίγω G1272 ·
ὑπομονή G5281 · ἐπιτιμάω G2008 · κατανοέω G2657) + 2 RED (περιτομή G4061 · σκληρύνω G4645).
FIRST ACT: no mandated word — the session-1 RED precondition was met by παράπτωμα. The streak's best
candidates are the plain verbs; per lesson #35, check the occurrence table's BOOK DISTRIBUTION before
predicting any word GREEN. Standing ruled procedures (session-1 log, verbatim): --require-cache every
apply · read the apply output for "using reviewed draw … no model call" before render · hinted applies
repeat hint flags verbatim · occurrence-table query before the floor · screenshots to the reviewer
chat, CC gets pass/fail relayed. Handoff procedure (a1ebfa4) in force: CC single-author, bank on
relay, no counts without contents (+ the roster corollary: commit lists, not lengths).

### REVIEWER-CHAT INHERITANCE BLOCK (paste into the new reviewer chat)
You are the reviewer chat for Lexica batch-3 shadow calibration, session 3. Your predecessor's
unbanked working notes are dead by design; everything ruled is in the repo at commit 4c7bcc9 —
CC (the code session) reads it and relays. Your duties: audit CC's floor reads and draft verdicts
against the banked bars; make rulings when asked (they get relayed to CC and banked as they happen —
if it isn't banked with CC, it doesn't exist); receive render screenshots and relay pass/fail; at
close JP asks you ONE question: "anything armed that isn't banked?" Watches you inherit (contents in
the audit doc's SESSION 2 CLOSE entry at 4c7bcc9): describe-don't-preach (9-for-9) · "Grounding
refs:" (0 sightings) · fold-compression (1 of 6) · overload look-trigger (2-for-2 ruled + one
unadjudicated fire) · floor-vs-ship placement class (detector parked; two named variants) ·
header-gloss ticket (systemic, 2 sightings) · tail-list disjointness (V8 candidate) · symmetric
fabrication checkpoint (#36: verify before claiming fabrication — ABP false-positives intuition).
Parked words are not yours to reopen: πολύς, ἄκανθα, κύων (κύων's revisit = "adjudicate the
ambiguity or enforce the majority" on Deu 23:18, JP's call at a future window).

## BATCH-3 SESSION 5 (2026-07-09/10) — CLOSED. **ROSTER COMPLETE.** Five shipped in one
## session: περιτομή G4061 (RED, adopted orphaned floor, hinted) · σκληρύνω G4645 (RED,
## hinted) · ὑπομονή G5281 (PLAIN attempt 2 — COUNTED, JP ruling) · ταμεῖον G5009 (cap-out →
## hinted) · κατανοέω G2657 (3 plain + 1 hint fail → hinted draw 2). Both REDs retired.
## Full per-word records: audit doc session-5 entries. Session-6 handoff blocks below are the
## resume point; this log is history.

## STEP-4 RULINGS — CLOSED (ruled in-chat 2026-07-10; informed approval — the plain-terms
## rundown preceded the word, per the new standing rule. Transmission completed same day:
## CC held items 1-3/7-11 pending against a relay that carried the reviewer's PROMPT for a
## ruling, not the ruling — the completion relay carried JP's verbatim "yes, approve all
## eight." Evidence per item = audit doc STEP 4 entry + ADDENDUM + partial-return record;
## full item texts with recommendations = git history at 2820931.)
1. #30 detector as built — **APPROVED** (incl. the `audit.floor_diff` stored field).
2. V8 draft — **APPROVED FOR THE STEP-5 TEST FIRE ONLY** (promotion = a separate ruling after).
3. Tooling batch — **APPROVED** (build in the gap; flag/apply layer only, control fires stay green).
4. Step-5 word — **CC PICKS per the ranker rule** (delegation affirmed explicitly).
5. Final-10 sequencing — **YES, 3-run→escalate** (re-open only if the first two escalate).
6. Streak — **YES: any human intervention resets it; the word still ships with the fix.**
   Banked framing: the streak is a SCOREBOARD of unassisted performance, never a shipping gate.
7. Lesson #42 — **ADOPTED verbatim** → now a numbered lesson in ENGINE_LESSONS.md; the
   step-4 exhibits (#3-#5) convert from contingent to unconditional.
8. Flag-1 stale line — **APPROVED**, the inline annotation is permanent.
9. Corpus-defect protocol — **ADOPTED** (the draft block below is now law).
10. Roadmap — **CONFIRMED** as ordered and marked.
11. #30 fire-class definition — **DEFERRAL CONFIRMED** (defined at the step-5 control fire).
12. Cost pendings (poetry trigger + N=6-7) — **DEFERRED to batch-4 selection.**
**GATE CONSEQUENCE: STEP 5 UNLOCKED** (items 1/2/4 in hand). #30 is live at the next dry-run
gate; V7 remains the shipping engine unless and until the step-5 ruling promotes V8.

## ROADMAP (consolidated 2026-07-10, step-4 session; RE-MARKED same day on reviewer relay —
## JP-LIGHT is a workflow POSTURE, not an absence; no travel window, no countdown. Items are
## classified by what they genuinely need, two independent axes:
##   JUDGMENT = a call only JP can make (rulings, roster approval, taste, doctrine).
##   EXECUTION = PA-terminal hands (the standing CC/DB boundary — unchanged, not new).
##   CC-ALONE = repo-only work needing neither until an accept/eyeball at the end.)
1. **JP rules the step-4 list above** — JUDGMENT (one line per item, recommendations attached).
2. **Step 5 — V8 control fire** — JUDGMENT (fire-class definitions + promote/park ruling,
   batched) + EXECUTION (floor/draw commands, screenshots). #30 fire classes DEFINED here.
3. **Tooling tickets** (ruling-list item 3) — CC-ALONE (flag/apply-layer code + CI tests;
   no DB writes, no rulings beyond item 3; runnable while everything else pends).
4. **Batch-4 selection — the final 10** — JUDGMENT (roster approval, one list) + EXECUTION
   (the ranker run that produces the candidate table); CC drafts the recommendation.
5. **Final-10 run with #30 live → GREEN activation** — EXECUTION per word (floors, applies,
   screenshots) + JUDGMENT only where the two-tier design asks it (AMBER glances, RED reads,
   batched flag rulings); activation = the insurance clause satisfied.
6. **Step 6 — layout session against V8 output** — CC-ALONE prep + build of the display
   tickets (enumerated in the audit doc STEP 4 triage); JUDGMENT at the end (taste rulings,
   gray-vs-hide calls are JP's per standing rule).
7. **Refresh-on-touch queue for the 54 older-stamp cards** (policy RULED step 3) — EXECUTION
   + per-card JUDGMENT identical to a ship's (each refresh reviews like a ship); converges on
   the high-traffic oldest 42 by itself.
8. **News-on-mobile** — CC-ALONE build (frontend); EXECUTION to deploy; JUDGMENT = accept on
   eyeball. Last unbuilt three-zone surface.
9. **Variance watch-tag reader-record review** — JUDGMENT (needs field records first;
   register banked in the audit doc, starts empty/forward-only).
POST-GREEN POINTER (not a roadmap item — JP ruling, in-chat 2026-07-10): **Seam next-stage
"Build A"** stays parked at TODO.md:594 until after GREEN activation; it enters this roadmap
then by JP ruling, not before. (Context ruled with it: the Study tab — where Seams display —
is down from public, conceptual stage; Study-on-mobile is tracked-but-unordered, DEPENDENT on
Study's return. Status detail: STATE.md Study line.)
10. **Human-review-dial decision** — JUDGMENT, LAST — only after #30 and #40 have track
    records (step-3 cost-lever order). **MECHANISM BANKED (JP, 2026-07-10, via reviewer
    relay):** dump N shipped entries to text → fresh-chat batch review against the ruled
    standards (rubric = the V8-encoded rules: attribute-don't-adjudicate · groupings cite a
    member · no unattested attitude labels) → flag list back to JP → flagged entries
    re-checked → catches become fixtures, permanently upgrading the automated suite. JP
    framing banked with it: streak ≠ futureproofing — error-flagging stays alive at scale
    without cost blowup; checkers never turn off, graduation removes only the human read.
    Scope note: this solves easy-word VOLUME; hard words (escalation class) stay hands-on by
    design — separate issue, not a gap.

## CORPUS-DEFECT PROTOCOL — DRAFT (step-4 session, 2026-07-10; PENDING JP, ruling-list item 9.
## Detection largely exists — #36 runs both directions, #22 feed-integrity-first; what's ruled
## here is ROUTING.)
1. **Classify at the layer boundaries first** (#21/#22 standard): read the artifact raw →
   assembled → rendered; corpus-side means the defect is in words/verses/side-tables, not in
   the draw or splitter. An engine-side artifact never parks a word.
2. **Corpus-side confirmed → the word parks DATA-BLOCKED** (a data hold, distinct from the
   park roster): one audit-doc line — word · defect · which instrument is blocked. The session
   proceeds on other work; the batch does not stall.
3. **The fix becomes a ticket, JP-independent where possible:** CC builds the dry-run +
   row-level checks; JP executes on PA per the standing CC/DB boundary (checkpoint approval
   before any write, as ever). Known members of this family already banked: dotted no-entry
   remedy · splitter double-tag · the ὄρος fold class (FIXED — the exemplar).
4. **After ANY data fix touching a word's evidence, its saved floor is INVALID.** The floor
   re-runs FRESH at full cost (stated, not hidden); `--from-json` re-reads of the old floor
   are analysis-only, never certification. Cross-check the blast radius the standing way:
   `check_draw_citations.py` sweep for other shipped cards touching the fixed rows.
5. **Un-park = fresh floor + the standard flow**; the DATA-BLOCKED line closes with the fix
   commit hash. Pre-emptive holds are the same mechanism (the armed hold-outs G1392/G1377/
   G1391 are DATA-BLOCKED before their floors ever run — do not floor them while tagged).

## BATCH 5 — RUN SESSION 1 (hinted re-entry) — CC OPENER BLOCK (paste into the new CC
## session; opens from docs alone. State source of truth = close commit 8a4dceb; trust
## docs over any number in a handoff.)
BATCH 5 RUN SESSION 1 — hinted re-entry, word 1 = ἀληθής G227. Open from docs alone;
state source of truth = close commit 8a4dceb. ("me/I" = JP.)
READ FIRST, in order: (1) this handoff — BATCH-5 CHARTER (RULED) + BUILD SESSION 1 RECORD
+ the BATCH 4 CLOSED record in Queue item 5; (2) AUDIT_lexica_rollout.md — BUILD SESSION 1
entry (walk 7/7, ἀλλάσσω leave-it ruling) + the G227 PARKED entry IN FULL; (3)
scripts/draw_hints.py header + the G227 entry; (4) DESIGN_hint_tooling.md RULINGS block;
(5) TODO.md batch-5 prep items (standing-query key-shape audit · section-matcher sweep —
BOTH are "before batch 5" items: decide/run them at open, before any word fires).
Opening check: `git log --oneline -1` shows 8a4dceb or a descendant; `python
tests/test_draw_hints.py` prints ok; the handoff charter block says RULED. Failed check =
rule-9 caveat, not a hold.
State: batch 4 CLOSED, count 7/15 name-true FINAL + UNTOUCHABLE · hinted scoreboard opens
at 0/7 (separate line, superscript-h marker, never joins the 7/15) · re-entry order RULED:
ἀληθής G227 → κλαυθμός G2805 → αἰχμαλωτεύω G162 → ἀλλάσσω G236 → εὐχαριστέω G2168 →
δόμα G1390 → διαιρέω G1244, then the six queue words UNAIDED (ἡσυχάζω G2270, μερίζω G3307,
παραπορεύομαι G3899, σιωπάω G4623, ἐκλύω G1590, ἐπανίσταμαι G1881) · V8 live (stamp
lexica:7ef8620328a9) · δίκτυον live card carries the ONE known-issue *work* bullet —
engine-prose fragment instance, fixed by a fresh draw under the new feed (refresh RULED
2026-07-12 s1: SLOT 8, after the seven hinted / before the six unaided — charter
amendment 5; from-draw refresh path).
FLOORS RULED: FRESH 10-run floors for ALL SEVEN (`--word <SID> --runs 10 --prompt v8`),
no park-floor reuse, saved park floors = historical artifacts only, NO override/reuse path
exists or gets built. Floors are UNHINTED by design (hints fire at build draws only, via
`build_lexica_def.py --hints`); floor tool already mirrors the new phrase-context feed.
PER-WORD GATE ORDER (unchanged): screens → pre-reg banked in the reviewer chat → fresh
floor → adjudication → build draws (--hints MANDATORY on registered words; refusal is
live; --no-hints REASON = logged override, JP-approved only) → apply (repeat --hints so
the fingerprint matches) → render = HARD gate (ledger 8e9e956).
AMENDMENT-2 AT EVERY PRE-REG: reviewer verifies the console-printed hint lines match
draw_hints.py verbatim, and the register lines against their cited park rulings, BEFORE
the floor fires. Register edits = JP checkpoint (ruling 3; the CI membership pin enforces
it). 3-defect budget applies to hinted draws.
Standing rules carry: R1 on-disk verify before relay (repost, never reference) · counts
are names · bank on reviewer relay · big output → file · exact-or-dotted BOTH clauses
(side tables G-prefixed, words bare) · pre-clears adjudicated per floor attestation ·
verbatim-quote watch (V9 candidate, three-word record). JP runs all PA commands; show
code before changing it; also owed to JP when convenient: the G1093/G3962/G435 gloss-note
re-check read (command in the BUILD SESSION 1 record context).

## BATCH 5 — RUN SESSION 1 — REVIEWER-CHAT INHERITANCE BLOCK (paste into the new reviewer chat)
You are the reviewer chat for Lexica batch-5 run session 1 (hinted re-entry). Everything
ruled is in the repo at 8a4dceb — CC reads and relays; your first act = R1-verify 8a4dceb
on disk (raw output REPOSTED, not referenced) and reconcile CC's opening summary against
the handoff's RULED charter + the audit doc's BUILD SESSION 1 entry. State you inherit:
batch 4 closed 7/15 final · hinted scoreboard 0/7 with the superscript-h marker (your
amendment 1) · re-entry order ruled, ἀληθής first · fresh floors ALL SEVEN ruled, floors
unhinted · your register walk passed 7/7 with the ἀλλάσσω leave-it ruling banked. YOUR
MECHANISM (amendment 2) fires at every pre-reg: verify the printed hints match
draw_hints.py verbatim + the register lines against their cited park rulings before any
floor. Ledger carried: the s3 queue miscount stands against the reviewer ledger (re-count,
never carry) · relay drops → repost · the two batch-5 prep items (key-shape audit,
section-matcher sweep) are decide/run-at-open items — hold CC to them before word 1.
Mapping note: the key-shape audit IS the ticketed form of the three carried key-shape
slips (the TODO entry says it would have caught all three); the section-matcher sweep is
its sibling with its OWN provenance (V9_PILE note 2026-07-11, the #47 reader gaps) — two
items, nothing missing.

## BUILD SESSION 1 — RECORD (2026-07-12; both builds LANDED, no word runs). Full record =
## audit doc BUILD SESSION 1 entry. Fragment-rendering fix + three checker noise classes
## fixed w/ control tests (2Ch 4:13 + Isa 24:5 fixtures; phantom test green); hint tooling
## built per the ruled design (draw_hints.py seven-entry register, --hints/--no-hints REASON
## refusal default, signature + draw-record + console print, CI membership pin = the ruling-3
## tripwire; tests in BOTH CI lists). Floor tool mirrors the new feed. CONSEQUENCE: user-msg
## shape changed — every cached draw/saved floor predates it; charter rules floor reuse.
## STILL OWED: δίκτυον *work* bullet — the bullet analyzed the head fragment "work" as the
## whole render; true render "latticed work" (pos 13, roman, JP-verified vs printed ABP).
## ENGINE-PROSE instance of the fragment class, distinct from the checker false-warn
## instances (scanner damage, fixed this session) — needs a fresh-draw refresh (word run,
## batch 5). Also owed: JP PA re-check of the G1093/G3962/G435 "tagging error" note
## speculations. (Framing clause = reviewer amendment to the s1 opener, applied here.)

## BATCH-5 CHARTER — RULED (JP, 2026-07-12, relayed via the reviewer chat; all three
## decisions closed)
1. **Marker (RULED, adopted as drafted):** hinted ships carry a superscript-h on every
   scoreboard line ("δόμαʰ") and count on their OWN line — "hinted re-entries: N/7" —
   never joining the closed unaided 7/15 name-true count. The closed count is final and
   untouchable. Register note wording: "shipped WITH pre-registered constraint hints
   (draw record: draw_hints)."
2. **Re-entry order (RULED, adopted as drafted):** ἀληθής G227 → κλαυθμός G2805 →
   αἰχμαλωτεύω G162 → ἀλλάσσω G236 → εὐχαριστέω G2168 → δόμα G1390 → διαιρέω G1244; then
   the six rolled-forward queue words UNAIDED (hinted and unaided never interleave within
   a session without a charter note). ἀληθής re-enters with its banked pre-registration
   SUBJECT TO the amendment-2 hint-provenance verification at re-entry pre-reg (reviewer
   mechanism).
3. **Floors (RULED): FRESH FLOORS FOR ALL SEVEN re-entry words. No reuse of saved park
   floors.** Rationale on the record (JP): the feed shape changed for every word;
   "unaffected" is a derived claim, not an artifact, and mixed provenance creates an
   unbounded audit surface. The ~70-draw cost is accepted. **Do NOT build any
   fingerprint-override/reuse path — the stale-draw refusal stands as-is.** Saved park
   floors remain in the record as historical artifacts, never fed to new draws.
4. **Procedure carried:** render check stays a HARD gate (ledger 8e9e956) · hint-provenance
   verification at every pre-reg (ruling 5b, reviewer's mechanism) · gate order screens →
   pre-reg banked → floor → adjudication → draws · exact-or-dotted both clauses · 3-defect
   budget applies to hinted draws · batch-5 prep items still open: standing-query key-shape
   audit + section-matcher sweep (TODO). [Both RUN at the s1 open, 2026-07-12 — see TODO.]
5. **δίκτυον refresh — RULED (JP, 2026-07-12, batch-5 run session 1; charter AMENDMENT,
   reviewer-recommended slot adopted): SCHEDULED this batch, SLOT 8** — after the seven
   hinted re-entries, before the six unaided queue words. From-draw refresh path; δίκτυον
   has NO register entry, so its draw runs without constraint hints (--hints not
   applicable — an unregistered word). Grounds on the record: the refresh wants the new
   phrase-context feed exercised and the hint tooling proven stable (the seven provide
   both), and slot 8 neither displaces nor interleaves with the ruled re-entry order.

## BUILD SESSION 1 (post-batch-4) — CC OPENER BLOCK (SPENT — session ran 2026-07-12; paste into the new CC session; opens
## from docs alone. State source of truth = close commit 506f106; trust docs over any
## number in a handoff.)
BUILD SESSION 1 — rendering-layer fix + hint tooling. Open from docs alone; state source
of truth = close commit 506f106. ("me/I" = JP.)
READ FIRST, in order: (1) HANDOFF_lexica_rollout.md Queue item 5 — the BATCH 4 CLOSED +
RUN SESSION 3 records; (2) DESIGN_hint_tooling.md IN FULL (rulings at top — all five
ruled, build order inside); (3) TODO.md "Def-engine rendering layer" ticket; (4)
AUDIT_lexica_rollout.md — FRAGMENT-RENDERING INVESTIGATION entry + BATCH 4 CLOSED entry;
(5) V9_PILE.md (new: #49 pipeline exhibits ×3, verbatim-quote V9-general, checker
exhibits).
Opening check: `git log --oneline -1` shows 506f106 or a descendant; `grep -c "RULINGS
(JP, 2026-07-12)" DESIGN_hint_tooling.md` = 1; the audit doc's BATCH 4 CLOSED entry
exists. Failed check = rule-9 caveat, not a hold. R1 debt from s3: verify bff58fb +
506f106 on disk and relay raw output to the reviewer first thing.
State: count 7/15 name-true FINAL (batch closed by JP ruling; δίκτυον rebuilt clean,
dagger off) · streak 2 · 7 words on the structure-hint shelf with banked hint lines
(διαιρέω, δόμα, εὐχαριστέω, ἀληθής, ἀλλάσσω, κλαυθμός, αἰχμαλωτεύω) · 6 queue words
rolled forward unrun (ἡσυχάζω G2270, μερίζω G3307, παραπορεύομαι G3899, σιωπάω G4623,
ἐκλύω G1590, ἐπανίσταμαι G1881) · V8 live (stamp lexica:7ef8620328a9) · δίκτυον live
card carries ONE known-issue (the *work* gloss bullet, fragment class — from-draw
refresh after the fix).
WORK ORDER (ruled, ruling 4 sequences it): (1) fragment-rendering fix BUILD — phrase
context (`words.english` + italic data) to the def-engine's renderings count +
gloss-note layer + claim-checker; phantom-render protection PRESERVED
(test_render_head_no_phantom stays green); 2Ch 4:13 pos-7/pos-13 = new fixture; also
fix checker noise classes on the record (identical-string, emphasis-italics-as-gloss,
prose-mention-counted-as-citation); (2) hint-tooling build per the RULED design
(draw_hints.py register + --hints/--no-hints REASON + signature + draw-record +
console print + CI provenance test); (3) reviewer walk of the seven register entries
vs their park entries; (4) batch-5 charter draft (marker wording for hinted ships,
re-entry order, fresh-floor list) → JP. NO WORD RUNS this session — no floors, no
draws, no applies. CC-ALONE code work; show code before changing it; JP runs any PA
read checks. Standing rules all carry: R1 on-disk verify before relay · counts are
names · bank on reviewer relay · big output → file · exact-or-dotted both clauses.

## BUILD SESSION 1 — REVIEWER-CHAT INHERITANCE BLOCK (paste into the new reviewer chat)
You are the reviewer chat for Lexica BUILD SESSION 1 (post-batch-4). Everything ruled
is in the repo at close commit 506f106 — CC reads and relays; your first act =
R1-verify 506f106 AND bff58fb on disk (raw git log, owed from s3's close) and read
DESIGN_hint_tooling.md in full — your s3 predecessor concurred on the SUMMARY only;
the full-doc read is yours, and your amendments (scoreboard marker + hint-provenance
verification at re-entry pre-reg) are already ruled in. State you inherit: batch 4
CLOSED at 7/15 name-true final, streak 2, dagger off (δίκτυον rebuilt clean; its live
card carries the one known-issue *work* bullet) · 7 shelf words with banked hint lines
· 6 queue words rolled forward · all five hint rulings in the design doc's RULINGS
block. This session is BUILD ONLY: no floors, no draws, no ships — your duties are
code-review shaped: verify the fragment fix preserves the phantom-render protection
(the certified test + the new 2Ch 4:13 fixture), verify the hint register's seven
entries against their park-entry rulings word-for-word (amendment 2 is YOUR mechanism),
verify the --hints refusal default and the draw-record/signature wiring, and hold the
no-word-runs line. Ledger notes carried: the s3 queue miscount is logged against the
reviewer ledger (counts are names — re-count, never carry) · relay drops happen, repost
rather than reference · three key-shape slips + the standing-query audit ticket remain
open batch-5 prep items.

## BATCH-4 RUN SESSION 3 — CC OPENER BLOCK (SPENT — session 3 CLOSED at 506f106; paste into the new CC session; opens from docs
## alone. State source of truth = close commit 4094dab (δίκτυον chain close; supersedes the
## wrap 8ab9468 pin); do not trust any number in a handoff over the docs at that commit.)
READ FIRST, in order: (1) this handoff — Queue item 5 (the batch-4 blocks incl. the RUN
SESSION 2 record) + the POST-S2 STATE ADD below; (2) AUDIT_lexica_rollout.md — δίκτυον
RULING CHAIN entry (top) + G227 PARKED + G2168 PARKED + FLOOR-VOID entries; (3)
ENGINE_LESSONS.md #47–#48; (4) V9_PILE.md (carve-invention = CONFIRMED V9 EDIT ×5;
cross-lemma misattribution = NEW class, 2 exhibits).
Opening check: `git log --oneline -1` shows 4094dab (or a descendant); `grep -c "^48\."
ENGINE_LESSONS.md` returns 1; `grep -c "RULING CHAIN — RUN + CLOSED"
AUDIT_lexica_rollout.md` returns 1. A failed check = rule-9 caveat, not a hold.
State at 8ab9468 (pointers, not restatements): count 7/15 name-true (δίκτυον† unchanged,
chain still QUEUED) · streak 1 · V8 live (stamp `lexica:7ef8620328a9`) · straight-to-10
standing · 4 parked on the structure-hint shelf (διαιρέω, δόμα, εὐχαριστέω, ἀληθής —
untouchable until the hint tooling exists) · hold-outs G1392/G1377/G1391 DATA-BLOCKED ·
queue = 7 words for 8 owed. FIRST ACT = double re-selection, one word at a time, full
screens each: r15 ἀλλάσσω G236 then r16 κλαυθμός G2805 (both table-walk concurred at s2
close; local register screens already PASS — re-verify against contested_register.py on
disk, mechanical). GATE ORDER (re-ruled after two s2 sequence slips — a third is a
config-test bump signal): screens → pre-reg banked in the reviewer chat → floor →
adjudication → build draws. NOTHING fires between reviewer concur and the bank.
Standing procedures unchanged from the s2 opener below, PLUS: pre-pull patterns
exact-or-dotted, BOTH clauses (`words`: `strongs='NNN' OR strongs LIKE 'NNN.%'`, never
bare prefix; **`dotted_lexicon`: keys are G-PREFIXED — use `'GNNN.%'`, a bare check
matches nothing and reads as clean** — data-model corollary, δίκτυον-chain catch) ·
headline-fallback marker = expected on one-sense draws, every fallback draw
inspected · singular "Gloss note:" now parses (splitter package #2) · floors
`--word <SID> --runs 10 --prompt v8` · R1 on disk before relay · commit lists not lengths.
POST-S2 STATE ADD (2026-07-11/12): **δίκτυον ruling chain CLOSED through (d)** — (b)
cousins classified from the source (1350.1 δικτυόω, 1350.2 δικτυωτός) · (a) side-table
rows LIVE on PA (`fb495a3` + builder --apply, row-proven) · (c) REBUILD ruled · (d) KEEP
ruled, **dagger stays on until the clean rebuild ships**. The δίκτυον rebuild = a named
execution item alongside the double re-selection (fresh floor on the cleaned feed, full
ship review). Record = audit doc δίκτυον RULING CHAIN entry.

## BATCH-4 RUN SESSION 3 — REVIEWER-CHAT INHERITANCE BLOCK (paste into the new reviewer chat)
You are the reviewer chat for Lexica batch-4 run, session 3. Everything ruled is in the
repo at wrap commit 8ab9468 — CC reads and relays; your first act = reconcile CC's opening
summary against the audit doc's G227 PARKED + G2168 PARKED entries and R1-verify 8ab9468
on disk. State you inherit: count 7/15 (δίκτυον†), streak 1, 4 batch-4 parks all on the
structure-hint shelf, budget clock RESET per word. Session 2 precedents now in force:
cross-lemma misattribution is a NAMED defect class (two-lexeme verses; verify whose word a
quoted phrase belongs to via the verse's word rows — the 1Jn 2:8 tag-pull is the model) ·
carve-invention is a CONFIRMED V9 edit at ×5 (banks forward, V8 untouched) · pre-clears
bank BEFORE the build draw (the three G227 pre-clears are the model) · machine hard-blocks
count as defect-class draws (δόμα d2 + G227 d2 precedents) · the pre-set 3-defect rule
counts DRAWS not defects. Gate order is the hard line: screens → pre-reg banked HERE →
floor → adjudication → build draws; two s2 slips are on the ledger and a third bumps the
config test. First work = double re-selection screens for ἀλλάσσω G236 then κλαυθμός
G2805, one at a time, no compression.

## BATCH-4 RUN SESSION 2 — CC OPENER BLOCK (SPENT — session 2 CLOSED at 8ab9468; kept as
## the standing-procedures reference the s3 opener points into. Opens from docs
## alone. State source of truth = close commit 25d4a40; do not trust any number in a handoff
## over the docs at that commit.)
READ FIRST, in order: (1) this handoff — Queue item 5 (the batch-4 blocks), then the BATCH-4
RUN state below; (2) AUDIT_lexica_rollout.md — G1390 PARKED entry (top) + G1516 entry +
BATCH-4 CORPUS-DEFECT FIRE entry + N=6-7 entry; (3) ENGINE_LESSONS.md #45–#46; (4) V9_PILE.md.
State at 25d4a40 (pointers, not restatements): **COUNT 7/15 name-true — δίκτυον†, σελήνη,
ὑπομονή, ταμεῖον, κάλαμος, καταπέτασμα, εἰρηνικός** († = the queued δίκτυον contamination
ruling chain, JP's, 4 steps, counted until ruled) · **streak 1** (verified vs item 6's
committed wording: only draft INTERVENTION resets; a park ships nothing and touches no
draft = neutral — σελήνη-after-ἄκανθα precedent; δόμα's park does not break εἰρηνικός's 1)
· V8 live (stamp
`lexica:7ef8620328a9`), drift-warning firing = anomaly = stop · **STRAIGHT-TO-10 ruled for
all remaining floors (3-run retired this batch; item-5 re-open SPENT)** · N=6-7 ruled KEEP
10 · queue = 8 words: **εὐχαριστέω G2168 FIRST (enters by re-selection — screens before
anything: contested-register 0-check (local), CONTESTED_VERSES [('2Co',5,21)] occurrence
check, loaded-referent + fork-adjacency hand-reads per the WRITTEN rule in the BATCH-4
SELECTION entry, Last-Supper gloss-note watch pre-noted)** then αἰχμαλωτεύω G162 (Eph 4:8
quote-crux annotation), ἡσυχάζω G2270, μερίζω G3307 (1Co 1:13 annotation), παραπορεύομαι
G3899, σιωπάω G4623, ἐκλύω G1590, ἐπανίσταμαι G1881 (hot poetry label 51/67,
expect-heavier-work). Parked, not yours to reopen: πολύς, ἄκανθα, κύων + διαιρέω and δόμα
(both re-enter ONLY via the structure-hint path when that tooling exists). Hold-outs
G1392/G1377/G1391 DATA-BLOCKED — never floor them.
STANDING PROCEDURES (ruled, batch-wide): every pre-pull = 3 lines (base-vs-dotted split ·
dotted-cousin identification · true verse table) and **any no-entry dotted row = feed
contaminant by default** (ENGINE_LESSONS #45; the fed-count tripwire on the floor header is
the check that a fix reached the feed) · floors: `--word <SID> --runs 10 --prompt v8` ·
gate: `--dry-run --word <SID> --floor <agreement json>` · apply: `--apply --require-cache
--floor <same>` + read "using reviewed draw … no model call" + row-verify stamp+floor_diff ·
manual shorthand-tail check MANDATORY before any CLEAN (#28 not landed) · quote-crux
pass-shape precedent = δόμα d2/d3 (describe each text, name the divergence, never merge) ·
carve-invention is the dominant reject mode (4-for-6) — the within-shape attestation law and
the self-indicting-prose tell (#46) are the working filters · R1 commands verified on disk
before relay · commit lists not lengths · bank on reviewer relay.

## BATCH-4 RUN SESSION 2 — REVIEWER-CHAT INHERITANCE BLOCK (paste into the new reviewer chat)
You are the reviewer chat for Lexica batch-4 run, session 2. Your predecessor's unbanked
notes are dead by design; everything ruled is in the repo at close commit 25d4a40 — CC reads
and relays; reconcile CC's first summary against the audit doc's G1390 PARKED + G1516 +
CORPUS-DEFECT FIRE + N=6-7 entries before accepting it, and R1-verify BOTH `25d4a40` AND the
wrap `5c0fc20` on disk (the wrap changed enforcement-relevant docs: this opener pair, lessons
#45–#46, the no-entry standing rule in data-model). Your first act = that reconciliation,
same discipline every session.
State you inherit: count 7/15 name-true (δίκτυον carries a † — the contamination ruling
chain is JP's and QUEUED, not yours to run; nobody decrements a name-true count, #42) ·
straight-to-10 ruled for all remaining floors, item-5 re-open condition SPENT · 8 queued
words, εὐχαριστέω G2168 first via full screens (it entered by re-selection) · V8 live,
fire classes per `7689884` (CLEAN requires the manual shorthand-tail check until #28 lands;
UNSEEN-REAL ships, UNSEEN-FABRICATED hard-rejects — the citation gate blocked one
autonomously at δόμα d2, that precedent stands) · watch-tag register EMPTY, forward-only ·
V9_PILE carries carve-invention as an EDIT CANDIDATE ×4 with direction on file — you watch
for instance five and for the self-indicting-prose tell (#46).
Your duties, unchanged in kind: audit CC's floor reads and gate reads against the banked
bars; pre-registrations before outputs exist; adjudicate fires per the ruled taxonomy
(within-shape attestation law; either-home migrators; folds never fire); rulings relayed to
CC get banked as they happen — if it isn't banked with CC, it doesn't exist; render
screenshots → pass/fail; per-word budget frame = the G2665 precedent (decision rule before
draw 3; three defect-class draws → no draw 4, park-leaning record to JP). Both standing
process rules: ask JP live in plain terms at decision points; batched lists only for
genuine absences. Flag-before-bank binds your dictations too — the record shows tally slips
caught on both sides of this desk; count names, not labels.

## STEP-5 SESSION — CC OPENER BLOCK (RAN + CLOSED 2026-07-10 — all five charter jobs delivered:
## G2665 shipped+live on draw 3, V8 PROMOTED (JP KEEP), count 6/15 (JP BOOK), #30 fire classes
## banked `7689884`, V9_PILE.md established. Record = audit doc STEP 5 entry; commits fa18656 /
## 7689884 / f631194 / the close commit. This block is HISTORY; resume point = Queue item 5
## (batch-4 selection). The reviewer-chat inheritance block below is likewise closed.)
## (original text follows)
## STEP-5 SESSION — CC OPENER BLOCK (opens from docs alone. State at step-4 wrap: the reviewer
## ALREADY reconciled this session-pair — #30 ACCEPTED, V8 hunks byte-checked PASS, list FINAL
## AT 12. RULINGS CLOSED 12/12 in-chat 2026-07-10 (the STEP-4 RULINGS — CLOSED block above):
## items 1/2/4 in hand → THE GATE IS OPEN — run step 5. Also green: item-3 tooling batch and
## /consolidate (MEMORY.md 18KB + topic file 487 lines, due) as parallel gap work.)
Step-5 charter when unlocked: (1) pick the control word per ruled item 4 (ranker command in
the list, R1-verified); (2) fresh floor under the CURRENT data state — reviewer runs
`--prompt v8` per its inheritance; (3) full pipeline with `--floor` wired (#30 live) — dry-run
gate, screenshots, render pass; (4) **DEFINE #30 fire classes + count consequences from the
control fire's own record, BEFORE the final-10 window opens** (the banked build-note term);
(5) V8 promote-or-park recommendation to a short JP list (promotion = copy V8_DRAFT_PROMPT
into build_lexica_def.VERSE_PROMPT, stamp flips to `lexica:7ef8620328a9`, reviewer re-syncs
its frozen copy + _check_prompt_sync target — one commit, byte-checked). Read first: this
block + the STEP-4 RULINGS — CLOSED block + audit doc STEP 4 entry + ADDENDUM + completion
record. R1–R4 in force; standing process rules apply (ask JP live in plain terms when he's
present; batch only in genuine absences); V7 stays the shipping engine until the step-5
promote-or-park ruling.
**R4 COMMANDS (verified at the step-4 wrap against the scripts on disk — lexica_agreement.py
--word :695 / --prompt :696 [choices from PROMPTS, v8 legal] / --runs :698, save pattern
agreement_<SID>_<prompt>_<ts>.json into ~/bible-db per save_run :518; build_lexica_def.py
--floor landed at ac8ea96. Re-verify per R1 if the scripts moved since):**
- ranker (ruled item 4): the verbatim line in RULING LIST item 4.
- floor under V8:  `cd ~/bible-db && python scripts/lexica_agreement.py --word <SID> --runs 10 --prompt v8`
- dry-run gate with #30 live:  `cd ~/bible-db && python scripts/build_lexica_def.py --dry-run --word <SID> --floor ~/bible-db/agreement_<SID>_v8_<TIMESTAMP>.json`
- apply (ruled procedures in force):  `cd ~/bible-db && python scripts/build_lexica_def.py --apply --word <SID> --require-cache --floor <same json>` — hinted words repeat their hint
  flags verbatim; read the "using reviewed draw … no model call" line before the render step.

## STEP-5 REVIEWER-CHAT INHERITANCE BLOCK (paste into the new reviewer chat when step 5 runs)
You are the reviewer chat for the Lexica STEP-5 session (V8 control fire + #30 fire-class
definition). Your predecessor (step-4 chat) already did its jobs — #30 ACCEPTED, V8 hunks
byte-checked PASS (4 insertion hunks, 18 lines, zero removals), ruling list finalized at 12 —
and its unbanked notes are dead by design; everything ruled is in the repo (audit doc STEP 4
entry + ADDENDUM, handoff RULING LIST). CC reads the repo and relays; reconcile CC's first
summary against those blocks before accepting it. State: count 5/15 two-tier (δίκτυον, σελήνη,
ὑπομονή, ταμεῖον, κάλαμος) · final-10 queue EMPTY until batch-4 selection · V7 live, V8 =
candidate `v8` in lexica_agreement.py (would-be stamp lexica:7ef8620328a9) · **RULINGS
CLOSED 12/12 in-chat 2026-07-10 — verify the handoff's STEP-4 RULINGS — CLOSED block exists,
then the gate is open** (item 2 approved the TEST FIRE only; promotion is a separate ruling).
Also since your predecessor: lesson #42 ADOPTED into ENGINE_LESSONS (six catches enumerated) ·
two standing process rules (ask JP live in plain terms; batched lists = genuine absences only)
· Study/Seams marked down-from-public (status only, STATE.md) · Build A = post-GREEN pointer.
**Your enforcement posture (unchanged):** committed wording governs · R1 commands verified on
disk · R2 designated instruments · R3 holds block, unaccounted output auto-opens one · R4
handoffs carry verbatim commands · #38 delta accounting · derived numbers are claims — count
the names (#42 is now ADOPTED LAW in ENGINE_LESSONS, six catches enumerated, two of them the
step-4 reviewer's own; flag-before-bank applies to YOUR dictations too, demonstrated).
**Your specific step-5 jobs:** (1) confirm the control word came from the ranker output per
ruled item 4, not from memory; (2) the floor runs under `--prompt v8` on the designated
instrument (lexica_agreement.py), fresh, current data state; (3) the ship pipeline runs with
`--floor` so #30 is live at the gate — read its fires; (4) **#30 FIRE CLASSES + count
consequences get DEFINED here, from this fire's own record, BEFORE the final-10 window opens**
— hold anything that tries to define them from recall; (5) V8 promote-or-park goes to JP as a
short list with a rendered-card screenshot (JP eyeballs the card, never a prompt); on promote,
byte-check the VERSE_PROMPT copy + the reviewer's frozen-copy re-sync in one commit. Parked
words are not yours to reopen: πολύς, ἄκανθα, κύων. Watch-tag register (audit doc) starts
empty, forward-only — first entries arrive with the final-10 ships.

## STEP-4 SESSION — CC OPENER BLOCK (RAN + CLOSED 2026-07-10 — all four numbered items
## delivered + the three gap-work docs items; record = audit doc STEP 4 entry, RULING LIST +
## ROADMAP + PROTOCOL DRAFT above, commits ac8ea96 + the close commit. This block is HISTORY;
## resume point = the STEP-5 opener above.)
## (original text follows)
## STEP-4 SESSION — CC OPENER BLOCK (reviewer-concurred plan, banked session 6; opens from docs
## alone per the availability constraint. Read first: audit doc STEP 3 block + AUDIT SESSION
## packet + this block. JP-LIGHT: draft/build everything, FIRE NOTHING — V7 stays live default
## until JP's batched ruling returns. Silence = pending.)
1. **#30 DETECTOR FIRST (gates everything):** floor-vs-ship placement diff, flag-only, at the
   dry-run gate. Control-fire on the three banked positives BEFORE trusting any zero — γόνυ p1
   (Luk 5:8 + 2Ki 1:13 off 3/3 homes) · νίπτω p1 (Psalms trio off unanimous cluster) ·
   κατανοέω hint-1 Exo 33:8 (0/10 off-floor inside an otherwise-PASSING hinted draw — the hard
   class; if #30 catches this it's real) · clean negative = δίκτυον. Fixtures buildable from the
   banked break records; floor JSONs on PA if needed (`ls ~/bible-db/agreement_G1119* etc.`).
   Wire into tests/test_lexica_detectors.py + CI + hook, BOTH lists (CI rule). **Bank in the
   build notes: #30 fire classes and their count consequences get DEFINED at the step-5 control
   fire, before the final-10 window opens — not discovered mid-count on ship 7.** (Until then
   #30 fires are judgment-class under the ruled taxonomy; an adjudicated-noise fire must not
   disqualify a count ship — ὑπομονή precedent extends only to recognition-class.)
2. **PILE TRIAGE:** full inventory table — every item, source pointer, class (prompt / tooling /
   display), recommendation. WS3 scoping ruled: noise families (#28 shorthand, quote-strip
   parser artifact, disclaimer-as-cite) → TOOLING fixes, never prompt edits.
3. **V8 PROMPT DIFF — DRAFTED, NOT FIRED:** per-edit traceability (pile item + expected effect +
   control plan). Big candidates on record: #29 attribution register · #40 shelf-architecture ·
   tail-list disjointness · uncited-category check · dangling-ref prose exclusion. New stamp
   computed; reviewer byte-checks; default stays v7.
4. **CLOSE = ONE RULING LIST ["PHONE-READABLE" struck 2026-07-10 — stylistic assumption, not
   a JP ruling; format itself unchanged]:** ask first, evidence below, one line each — and
   every item carries a RECOMMENDED answer (incl. the step-5 control-fire word, with rationale);
   JP overrules rather than composes. Nothing fires until the list returns. **Gap work while
   pending (all JP-independent, ruled 2026-07-10 at session-6 close):** step-6 layout prep +
   display tickets · `/consolidate` (MEMORY.md over threshold; lexica topic file 476 lines) ·
   THREE DOCS ITEMS (JP-asked, reviewer-endorsed):
   (i) **JP QUICK-REFERENCE** — how to drive the new system: ruling-list workflow, what a
   two-tier check-in looks like vs the old kind, when JP is needed vs not; note banked: V8
   reaches JP as a rendered card to eyeball via step 5's control fire, never a prompt to paste.
   (ii) **ROADMAP consolidation** — one ordered block from the scattered banked backlog
   (final-10 run → GREEN activation → step-6 layout vs content eras → refresh-on-touch queue
   for the 54 → remaining three-zone surfaces → batch-4 selection → variance watch-tag
   reader-record review → human-review-dial decision once #30 + #40 have records), each item
   marked JP-NEEDED vs JP-INDEPENDENT per the availability constraint.
   (iii) **CORPUS-DEFECT PROTOCOL draft** — detection mostly exists (#36 runs both directions);
   missing is ruled ROUTING when a floor/draw surfaces a corpus defect: word parks with a
   DATA-BLOCKED tag → fix queued as JP-independent tooling where possible → after ANY data fix
   the floor re-runs FRESH (the free --from-json re-render is only valid while the data is
   unchanged — a corpus fix invalidates the saved floor; real cost, stated). CC drafts,
   reviewer reviews, JP rules from a list.

## STEP-4 REVIEWER-CHAT INHERITANCE BLOCK (paste into the new reviewer chat)
You are the reviewer chat for the Lexica STEP-4 session (V8 pile triage + prompt-bump draft +
#30 detector un-park). State: batch-3 CLOSED 18 shipped / 2 escapes / 2 parked (18 RULED — the
old "19" was a propagated tally slip) · two-tier bar ADOPTED with variance watch tags · count
5/15 (δίκτυον, σελήνη, ὑπομονή, ταμεῖον, κάλαμος) · GREEN activates only when the final 10 ran
with #30 live · JP availability INTERMITTENT (relocation) — the session is JP-LIGHT: draft/build
everything, FIRE NOTHING; V7 stays live default; close = ONE ruling list, every
item with a recommended answer; silence = pending, never approval. CC reads the repo and relays;
reconcile CC's first summary against the handoff STEP-4 CC OPENER + the audit doc's STEP 3 block
+ AUDIT SESSION packet before accepting it.
**Your enforcement posture:** committed wording governs · R1 commands verified on disk ("verified
against scripts/<name>" line) · R2 designated instruments · R3 holds block, unaccounted output
auto-opens one · R4 handoffs carry verbatim commands · #38 delta accounting with script-printed
units · derived numbers are claims — count the names (lesson candidate #42; both prior exhibits
are yours and CC's) · the fire-nothing seam is yours to hold.
**Your specific jobs this session:** (1) verify #30's control fires on ALL THREE banked positives
(γόνυ p1 · νίπτω p1 · κατανοέω hint-1 Exo 33:8 — the hard class) + the δίκτυον clean negative
BEFORE any zero is trusted; (2) byte-check the V8 prompt draft against the ruled pile items,
per-edit traceability; (3) check the ruling list itself — every item one line, ask first,
recommended answer attached, count consequences stated with members; (4) if the corpus-defect
protocol draft is reached (gap-work item iii), review it. **Pending JP rulings you carry to the
list:** skip-3-run poetry · delete-swap streak criterion · lesson #42 · Flag-1 stale line ·
#30 fire classes (defined at step 5, before the final-10 window). Parked words are not yours to
reopen: πολύς, ἄκανθα, κύων.

## SESSION-6 HANDOFF — CC OPENER BLOCK (RAN + CLOSED 2026-07-10: steps 1–3 + audit session done,
## step 4 commissioned. HISTORY — resume point = the STEP-4 block above. Numbers inside are
## superseded: 18 shipped RULED (not 19), count 5/15 two-tier (not 3/15); record = audit doc
## STEP 3 block + FINAL-TALLY CORRECTION. Cost-scaling levers: RULED at step 3 (no longer
## pending). Still-pending JP rulings carried to the step-4 list: skip-3-run for poetry-heavy
## words · streak criterion for delete-class swaps · lesson candidate #42 (tally cross-check,
## audit doc) · Flag-1 stale-line ruling · #30 fire classes → defined at step 5.)
CLOSE-OUT STACK SESSION — the batch is done; this session adjudicates and synthesizes. No new
words. State source of truth: the docs at the close commit (git log will show it as the wrap
commit, 2026-07-10). Read first, in order: (1) this block + STANDING LAW + R1–R4 above;
(2) AUDIT_lexica_rollout.md session-5 entries (G4061, G4645, G5281, G5009, G2657 — each has
watch, floor adjudication, pull ledger, rulings, ship record); (3) ENGINE_LESSONS.md #38–#41.
**1. FINAL STATE (do not re-derive; 18 RULED by JP session 6, 2026-07-10 — see the audit doc's
FINAL-TALLY CORRECTION entry):** batch-3 = **18 shipped / 2 escapes (γόνυ, νίπτω — both
session 1, human-caught) / 2 parked (ἄκανθα, κύων — DO NOT REVISIT; κύων's revisit is a JP
call at a future window) · count 3/15 (δίκτυον, σελήνη, ὑπομονή) · streak 0.**
- **The count means SHIPS-WITHIN-BUDGET** (JP ruling, G5281): a plain-pull word that ships
  inside the 3-pull cap with no human catch counts; machine-flagged rejects are not
  interventions. Hinted/escalated ships are off-count.
- **Second tally = FIRST-DRAW RELIABILITY** (split off by the same ruling, for the economics
  model): ὑπομονή 1 plain fail (machine-caught) · ταμεῖον 3 plain fails (2 variance + 1
  defect) · κατανοέω 3 plain fails (3 distinct modes: double-shelf / freight-shelf /
  over-coarse) + 1 hint fail (off-floor misplacement).
- Shipped list session 5: περιτομή, σκληρύνω, ὑπομονή, ταμεῖον, κατανοέω (all LIVE,
  screenshot-passed). Sessions 1–3 ships: see their log blocks.
**2. CLOSE-OUT STACK (six-step ruled plan + the audit session, dependency arrows explicit):**
step 1 batch-close review → step 2 fabrication-check / intervention-tally adjudication →
**AUDIT SESSION (between 2 and 3; charter drafted by the REVIEWER from the spec it holds —
scope: reject reclassification [defect vs variance, recount 3/15 both ways], economics model
[uses BOTH tallies above], gate load-bearing analysis; documents as input; recommendations
not rulings)** → step 3 scale-protocol decision (CONSUMES the audit's reject reclassification
+ economics model — do NOT run step 3 before the audit) → step 4 V8 pile triage + prompt bump
(CONSUMES the audit's gate load-bearing analysis; V7 freeze lifts here) → step 5 V8 control
fire (NOT optional) → step 6 visual layout session against V8 output.
**3. OPEN DECISIONS with their evidence (present, don't decide):**
- **Two-tier bar** (defects reject / floor-legal variance ships): JP position statement banked
  (audit doc, ταμεῖον entry); exhibits = ταμεῖον (3 draws burned on reader-immaterial
  structure) + κατανοέω (the natural experiment: defect / defect+variance / pure-variance
  rejects across 3 pulls — pull 3 would arguably have shipped under two-tier).
- **Ship-vs-floor divergence watch:** ταμεῖον = lead exhibit (3/3 plain draws built the same
  figurative shelf the floor scattered); ruled resolution = floor stays the instrument,
  evidence to V8 pile; possible designed test = floor re-run at higher per-draw attention.
- **Pre-existing pending JP rulings (still pending, do not decide):** skip-3-run for
  poetry-heavy words · streak criterion for delete-class swaps · dictionary cost-scaling
  levers (the audit's economics model feeds this one).
**4. NEW STANDING INSTRUMENTS from session 5 (rules, in force):**
- **Relocated-verse prose check:** any verse placed off its floor-majority home gets its prose
  claim read against the verse text FIRST (control case: Exo 33:8 "sustained noticing" for
  people physically watching — the draw rewrote the verse to fit the shelf).
- **Two defect signatures:** shelf-first-verse-fitted-after (freight via sub-use ARCHITECTURE,
  invisible to wording checks — κατανοέω pull 2's "devotional or awe-struck" shelf) ·
  misplacement + prose-misdescription pairing (two hits same night: Job 23:15 invented "face",
  Exo 33:8 re-narration).
- **Incumbent-comparison protocol (JP ruled in):** incumbent posted at word open, files only;
  comparison AFTER ship; never enters draw context or floor reads. **3-for-3 pattern on
  record:** every incumbent led with a sense the corpus doesn't lead with AND carried 1–2
  senses the corpus doesn't attest (ὑπομονή ground-of-reliance gap · ταμεῖον treasury-first
  inversion · κατανοέω attainment-vs-attention, Jas 1:23-24 the counter-verse). For close
  review + methodology page.
- **Cache-content verify (procedure worth keeping):** before any apply where the reviewed-draw
  identity is in ANY doubt, re-read the cache free: plain `--dry-run` WITHOUT `--force` = the
  cache-hit path, no model call, no write (verified build_lexica_def.py:1542).
- Loading-cards ticket: TODO.md, NOT-NOW flag intact — same cards every time, JP logging names.
**5. VERBATIM COMMANDS (R4; all verified against the scripts on disk this session):**
- Floor re-render, FREE, any saved run: `cd ~/bible-db && python scripts/lexica_agreement.py --from-json <file>.json`
  Saved session-5 runs: agreement_G4061_v7_20260709-235238.json · agreement_G4645_v7_20260710-005811.json ·
  agreement_G5281_v7_20260710-014609.json · agreement_G5009_v7_20260710-035236.json ·
  agreement_G2657_v7_20260710-043937.json
- New floor: `cd ~/bible-db && python scripts/lexica_agreement.py --word G#### --runs 10`
- Plain draw: `cd ~/bible-db && python scripts/build_lexica_def.py --word G#### --dry-run --force`
- Free cache re-read: `cd ~/bible-db && python scripts/build_lexica_def.py --word G#### --dry-run`
- Apply (repeat any hint flags verbatim): `cd ~/bible-db && python scripts/build_lexica_def.py --word G#### --apply --require-cache`
- Occ table: `sqlite3 ~/bible-db/bible.db "SELECT DISTINCT strongs FROM words WHERE strongs LIKE '####%';"` +
  **[SUPERSEDED SHAPE — batch-5 key-shape audit 2026-07-12: bare prefix sweeps neighbor series
  ('227%' hits the 2270-family). Use exact-or-dotted: `strongs='NNN' OR strongs LIKE 'NNN.%'`.
  Historical template kept for the session-6 record only — never copy it.]** +
  book spread + `count(DISTINCT v.id), count(*)` variants (audit doc session-5 entries carry the exact texts)
- Style-ledger checks (def_json fields): gloss-note italic leads
  `sqlite3 ~/bible-db/bible.db "SELECT strongs, lemma FROM lexica_def WHERE json_extract(def_json,'\$.gloss_notes') LIKE '%*\"%';"` ·
  citations-only paragraphs `sqlite3 ~/bible-db/bible.db "SELECT strongs, lemma FROM lexica_def WHERE json_extract(def_json,'\$.senses_block') LIKE '%' || char(10) || '(%';"`
**6. AUDIT CHARTER:** the reviewer chat holds the drafting spec (NOT prose to inherit — the
new reviewer drafts fresh from the spec in its inheritance block below). It slots between
close steps 2 and 3.
Standing ruled procedures stay in force verbatim (session-1 log): --require-cache every
apply · read "using reviewed draw … no model call" before render · hinted applies repeat
hint flags verbatim · occ-table before floor · screenshots to the reviewer chat. R1–R4 hard.
Handoff test (JP): a zero-context session must be able to run steps 1–2 and commission the
audit from this block + the docs it points to alone.

## SESSION-6 REVIEWER-CHAT INHERITANCE BLOCK (paste into the new reviewer chat)
You are the reviewer chat for the Lexica batch-3 CLOSE-OUT (session 6). Batch-3 is COMPLETE:
18 shipped / 2 escapes / 2 parked / count 3/15 (ships-within-budget definition) / streak 0
(18 ruled by JP session 6 — the docs' former "19" was a propagated tally slip, see the audit
doc's FINAL-TALLY CORRECTION entry).
Your predecessor's working notes are dead by design; everything ruled is in the repo at the
wrap commit — CC reads it and relays. Read the handoff SESSION-6 CC OPENER + the audit doc's
session-5 entries BEFORE accepting CC's first summary (reconcile-against-docs applies to you).
**Your enforcement posture (hold CC to these):** committed wording governs · delta accounting
at checkpoints in-message with script-printed units (#38) · placement vs floor, not prose ·
verify before claiming fabrication, both directions (#36) · R1 commands verified on disk with
a "verified against scripts/<name>" line · R2 named procedures use their designated
instrument · R3 holds block everything, unaccounted output auto-opens one · R4 handoffs carry
verbatim commands · relocated-verse prose check (verse text vs prose claim before placement
review) · the two defect signatures (shelf-first-verse-fitted-after; misplacement +
misdescription pairing).
**You draft the AUDIT-SESSION CHARTER fresh from this spec** (do not reconstruct predecessor
prose): evidence synthesis — reject reclassification (classify every banked reject defect-class
vs variance-class, recount the 15-count both ways; known flip: ταμεῖον ships pull 1 under
two-tier → 4/15 minimum; predecessor's guess N=6–9) · economics model (both tallies: count +
first-draw reliability) · gate load-bearing analysis (which exit terms caught real defects vs
enforced reader-immaterial structure) · **STAMP CENSUS (added 2026-07-10, JP-ruled split of
the old-cards question): live cards per prompt version + the content-convention deltas
separating each era from V8. Command (verified vs build_lexica_def.py:1595, column synth_ver):
`sqlite3 ~/bible-db/bible.db "SELECT synth_ver, count(*) FROM lexica_def GROUP BY synth_ver;"`
Framing rule: RENDERING uniformity is FREE (template change covers every era, zero draws);
CONTENT structure is version-stamped and re-drawing costs review — the refresh policy
(refresh-all / refresh-on-touch / stamp-and-leave) is a step-3 economics decision, and the
layout session (step 6) designs knowing whether it renders one content-shape or three.**
Documents as input; recommendations not rulings; slotted between close steps 2 and 3; step 3
consumes its outputs.
**Predecessor positions on record (positions, NOT rulings):** count-it on budget-ships
(already ruled) · hint-over-park on structure conflicts · floor-stays-the-instrument on
divergence · two-tier bar to the scale decision with session 5 as evidence.
Watches you inherit (contents in the audit doc): describe-don't-preach · fold-compression ·
overload look-trigger (one unadjudicated fire, session 2) · header-gloss ticket (3 sightings)
· tail-list disjointness · #28 citation-shorthand family (now comma + dash-range + semicolon
variants) · dangling-book-ref prose-noise exclusion (V8 candidate) · "prose asserts a category
whose members are all uncited" (V8 candidate, σκληρύνω) · ship-vs-floor divergence.
Parked words are not yours to reopen: πολύς, ἄκανθα, κύων.

## BATCH-3 SESSION 4 (2026-07-09) — CLOSED FAILED (JP ruling; ENGINE_LESSONS #39). No word
## shipped, no floor run, no writes anywhere. Failure: CC relayed the 10-run floor command from
## RECALL — wrong script name (`lexica_def.py` for `build_lexica_def.py`) + wrong flag
## (`--strongs` for `--word`) — and it reached JP's terminal ("no such file") before correction;
## `--force` also went out unexplained until JP demanded semantics; earlier, two JP holds were
## skipped in one message and had to be re-demanded. Rulings taken THIS session remain VALID
## (banked + pushed): βιβρώσκω count (b) · περιτομή next · six-step close plan.
## RESUME STATE FOR SESSION 5 — περιτομή G4061 mid-pre-pull:
## · occ table STAGED NOT BANKED: 36 verses / 40 occ, 4 doubles (Col 2:11, Rom 2:25, Rom 4:10,
##   Rom 4:12), no dotted cousins (bare 4061 only). Doubles judged plausibly genuine (Pauline
##   rhetorical repetition; none in splitter_b_evidence.txt, whose PA copy = committed copy,
##   886 lines both) — but the 8-row row-level check is STILL OWED before banking:
##   sqlite3 ~/bible-db/bible.db "SELECT v.book, v.chapter, v.verse, w.position, w.english FROM
##   words w JOIN verses v ON v.id=w.verse_id WHERE w.strongs='4061' AND (v.book,v.chapter,v.verse)
##   IN (VALUES ('Col',2,11),('Rom',2,25),('Rom',4,10),('Rom',4,12)) ORDER BY 1,2,3,4;"
## · floor command — CORRECTED 2026-07-09 (rule R2: the designated floor instrument is
##   lexica_agreement.py, not a build_lexica_def loop). Verified against
##   scripts/lexica_agreement.py ON DISK (--word line 564, --runs line 567, prompt defaults v7):
##   cd ~/bible-db && python scripts/lexica_agreement.py --word G4061 --runs 10
##   The earlier loop line stood here labeled "VERIFIED against --help" — flags were real but the
##   INSTRUMENT was wrong (fail-2 class). It RAN at 23:27 on 2026-07-09 before this fix landed:
##   10 paid draws on the wrong instrument, NO floor produced. Those 10 outputs are NON-FLOOR,
##   DO NOT USE for agreement stats or any comparison. Cost logged in the audit post-mortem.
## · order: doubles verify → table banks 36/40 → floor. RED watch below stays banked; book
##   distribution note (JP term, banked verbatim): Rom+Gal = 22/40 heavy figurative/identity load;
##   OT sparse (Gen 1 · Exo 2 · Jer 1); "sample spread should force at least one OT concrete hit so
##   the rite sense isn't reconstructed from Paul's polemic alone."
## Both traveling rulings taken at open:
## (1) βιβρώσκω count = option (b), γόνυ precedent — count stays 2/15, intervention tally +1
## ("gates passed a defect a human caught", tagged to the fabrication-check batch-close decision);
## precedent EXTENDED to post-pull pre-ship human catches (ENGINE_LESSONS #30 update). βιβρώσκω
## stands shipped (batch tally 13 shipped; "14" here was the tally slip, corrected per the
## session-6 ruling). (2) Next word = περιτομή G4061 (RED seed) — spreads the
## REDs across sessions, σκληρύνω inherits the lessons; straight-to-10, standing terms in force.
## ὑπομονή endurance-vs-hope pre-registration stays banked for its GREEN slot. Record: audit doc
## G977 entry (count ruled) + this block.
**BATCH-3 CLOSE PLAN (JP directive, banked 2026-07-09; order ruled):** 1. batch-close review
(count, escapes, parked words: πολύς · ἄκανθα · κύων) → 2. fabrication-check / intervention-tally
adjudication (includes the βιβρώσκω "gates passed a human-caught defect" data point) → 3. V8 pile
triage + prompt bump (V7 freeze lifts at close; pile so far: comma-shorthand citation class ·
"line"→"entry" fix · gloss-note asymmetry · doubled vocabulary bar · #29 attribution register ·
plus whatever batch 3 adds) → 4. visual layout session run against V8 output (sequenced after the
bump so layout decisions aren't invalidated by V8 structure changes — whitespace, sub-use
formatting). **BOTH CC FLAGS RULED IN (JP, 2026-07-09) — plan amended to the SIX-STEP RULED
version:** 1. batch-close review → 2. fabrication-check / intervention-tally adjudication →
3. scale-protocol decision (input = step-2 escape/intervention evidence; output constrains V8
batch ambition; BETWEEN not inside, so the economics ruling stays untangled from pile triage) →
4. V8 pile triage + prompt bump → 5. V8 control fire (NOT optional — a bump doesn't re-render
shipped cards; layout judged against V7-shaped cards defeats the sequencing rationale) →
6. visual layout session against the V8-drawn card(s).
**G4061 περιτομή RED watch PRE-REGISTERED (banked before any pull exists):** NOT in the contested
register (verified: no 4061 in contested_register.py) — RED routing carries the word alone. Expected
profile: literal rite · "the circumcision" as a GROUP label (people/party metonymy, Acts/Gal/Rom) ·
figurative heart-circumcision (Rom 2:29, Php 3:3, Col 2:11). Fabrication temptations named: (i)
covenant-theology freight / supersessionist framing ("true circumcision" verdicts) — describe-don't-
preach hardest on Rom 2:28-29 + Php 3:3; (ii) παράπτωμα's second-costume rule in force: EVERY
peer-level carve must be floor-attested, comparison is full-structure vs floor, not flagged hotspots;
(iii) any within-draw double-shelf = self-disqualifying. Whether group-metonymy and heart-circumcision
earn peer shelves is the floor's call, not this note's — attested = follow it. Straight-to-10, no 3-run.

## PAUSE LIFTED 2026-07-09 — splitter-fix session COMPLETE, charter CLOSED. Polarity A shipped
## LIVE (607 helper rows untagged; rule folded into the builder + locked in CI); polarity B
## deferred to its own TODO ticket (878-case evidence frozen). Exhibit words verified clean at
## render; G2008 38/37 + G977 39/38 (charter's G977 "37" = drafting miscount, corrected); both
## stale "may" gloss bullets deleted + cards re-rendered. Record: AUDIT splitter-fix entry +
## ENGINE_LESSONS #38. Calibration RESUMES at the session-3 close state below (βιβρώσκω count
## still pending JP; next-word decision travels with it).

## BATCH-3 SESSION 3 LOG (2026-07-09) — CLOSED. **CALIBRATION PAUSED at close (JP ruling): the
## splitter double-tag data fix runs FIRST, in its own dedicated session — charter =
## CHARTER_splitter_fix.md (no-write gate + acceptance checks are IN the charter, ruled verbatim).**
**Close state: 3 shipped this session (ἐπιτιμάω · διανοίγω · βιβρώσκω, all LIVE) · streak 0 ·
βιβρώσκω COUNT PENDING JP (3 options, audit doc G977 entry; CC recommends 3/15 + intervention-tally
data point) · next-word decision (κατανοέω vs RED) travels with that ruling · GREEN remaining 3:
ταμεῖον G5009 · ὑπομονή G5281 (pre-register endurance-vs-hope split BEFORE its floor) · κατανοέω
G2657 · RED remaining 2: περιτομή G4061 · σκληρύνω G4645. JP ruling behind the pause: cards are
permanent surfaces — patching around bad data in permanent prose is backwards; fix the data, then
delete the two stale "may" gloss bullets (G977 + G2008) and re-render. Ordering ruled: data fix →
exhibit words verify clean → bullet swaps → re-render → calibration resumes. Inherited watch
unadjudicated as ever: session-2 overload look-trigger fire.**
**Opened:** clearing gate PASSED all three checks (4c7bcc9 · session-2 log grep · lesson #37 grep).
**Opener selection (lesson #35 applied):** six-way book-distribution read on the remaining GREEN run
BEFORE any prediction; ranking banked (ὑπομονή worst — OT hope/expectation vs NT endurance two-sense
risk, pre-register the split before its floor; ταμεῖον dotted-cousin policing; κατανοέω soft mind-verb
borders). **ἐπιτιμάω G2008 approved as opener (JP ruling)** — 27/39 Gospels, one concrete speech-act;
Psalms divine-rebuke = known-shape risk (βέλος divine-archer precedent). Pre-registered expectation
banked: dominant rebuke-a-person cluster + possible divine-rebuke cluster (attested = follow it);
anything else = surprise, audited before drafting.
**Pre-pulls:** dotted 2008.1 = distinct noun ("reproach" 7/7, incl. the God-rebukes-waters texts —
so the verb's divine set is smaller than the raw book column implied; banked). CC error caught +
corrected in-flight: first dotted query used 'G2008.1' but the dotted column stores bare '2008.1' —
a detector that couldn't fire; corrected pull returned the 7 rows. Doubles: Zec 3:2 (genuine ×2) +
Jud 1:9 (see ticket below).
**DOUBLE-TAG TICKET (TODO.md, e208e5d + cf028f5):** Jud 1:9 "May"+"reproach" BOTH tagged 2008 —
verified vs eSword + ABP app (JP): BUILD ARTIFACT (source tags "reproach" only; splitter split the
one chunk "May [2reproach" into two tagged rows). Class sized read-only: **731 adjacent same-tag
helper pairs** (may/shall/will/did/do/does/let). Splitter-family fix, folds into next words rebuild;
NOT mid-calibration. #36 run both ways (verified before calling defect). G2008 occ table corrected:
**37 verses / 38 real occ, single true double Zec 3:2.** No floor rerun (Jud 1:9 glued to Zec 3:2
10/10); watch banked: renderings claims checked vs real occurrences so "may" can't leak.
**Floor:** 3-run {2:3} but structure rotates (3 different carves, 2 draws double-shelve at floor) →
mandated 10-run (5th straight escalation, ἐπιτιμάω OFF-COUNT, count stays 2/15). 10-run
{1:1,2:3,3:5,4:1}, NO exact modal carve, no complete carve repeats 3× → first-draw hint legal
(δάμαλις extension, 3rd use). Certified clusters: directive core (Gospels stop/silence/demon/storm,
10/10; silence trio own-shelf 1/13 = folds) · personal reproof (Gen 37:10+1Ki 1:6 10/10, Luk 17:3+
2Ti 4:2 10/10, pairs share shelf 6/10; own shelf 6-7/10 = majority-distinct PEER) · Psalms nations
(9:5+119:21 10/10, +68:30 9/10; own shelf 4-5/10 = below peer). **Pre-registration answered with a
twist: Zec 3:2+Jud 1:9 pair (10/10) rides the demon/force core 7/10, NOT the Psalms set.** All
wobbles fold; no holes.
**RULINGS (JP relay, banked):** (1) Psa 106:9 homes with the Psalms group (8/10 with 68:30; two-way
character named on record — semantically cousin to Mar 4:39, floor attestation governs). (2) Nations
cluster = labeled sub-use, NOT peer (4-5/10). Rth 2:16 draw-6 wobble closed as FOLD. **Reviewer
overcompression caught by CC + accepted:** "two labeled satellites" would have folded the 6-7/10
majority-distinct reproof cluster (gate-2 merge); corrected structure = TWO PEERS (directive+nations-
sub-use | personal reproof). Logged as a challenge-the-reviewer catch.
**HINT FLAGS (verbatim reference — apply must repeat exactly):**
  --structure-hint "A sharp directive or check aimed at stopping, silencing, or redirecting someone
  or something - persons, crowds, demons, disease, the storm; including the commands to keep silent,
  the crowd rebukes, the Peter exchanges, the 'The Lord rebuke you' formula as one pair (Zec 3:2;
  Jud 1:9, together and only here), and AS A LABELED SUB-USE the divine word against nations and the
  proud (Psa 9:5, 68:30, 106:9, 119:21 - these four cited only here): Mat 8:26, 12:16, 16:22, 17:18,
  19:13, 20:31; Mar 1:25, 3:12, 4:39, 8:30, 8:32, 8:33, 9:25, 10:13, 10:48; Luk 4:35, 4:39, 4:41,
  8:24, 9:21, 9:42, 18:15, 18:39, 19:39, 23:40; Zec 3:2; Jud 1:9; Psa 9:5, 68:30, 106:9, 119:21"
  --structure-hint "A personal reproof or correction addressed to someone for conduct or attitude
  judged wrong: Gen 37:10; Rth 2:16; 1Ki 1:6; Luk 9:55, 17:3; 2Ti 4:2"
Pins: Psa 106:9 nations sub-use · Zec/Jud pair whole, sense 1 only · Luk 23:40 sense 1 (core company
10/10; named most-likely-to-fight) · Psa 119:21 with Psalms four · double-shelf = fail. Flag
disjointness verified (#37); 37/37 placed.
**Hinted draw 1 (key 79c2b36f) = BAR-FAIL — the hint mechanism's FIRST STRUCTURAL DEFIANCE (structure
record 9-for-10).** Drew 2 senses but INVERTED the ruled structure: reproof folded into sense 1's
human sub-use (gate-2 merge of majority-distinct) + demoted nations cluster promoted to peer. Plus
Rth 2:16 → punitive sense on "mildest instance" prose (#33) + **Luk 9:55 dropped entirely (36/37 —
presence gap)**. Machine gates all green (#30 again). Credit noted: gloss note defused the "may" row
itself (optative rendering, not a sense) — the double-tag leaked into the feed and the engine handled
it; no-rerun call confirmed.
**ADJUDICATION PRE-REGISTERED (JP-approved + tightened, banked before output exists):** (a) inversion
recurring OR a partial (reproof shelved but nations ALSO peer as a 3rd sense = still ruling-2
defiance) → first STRUCTURE wall (vs membership), ὀφθαλμός-class package to JP stating plainly the
engine keeps overriding the floor's own 6-7/10 majority at draw time; (b) pass = exactly 2 senses,
reproof peer, nations labeled sub-use inside sense 1, all 37 present, pins home → ship path (full
placement check + "reproach throughout" renderings check vs real occurrences); (c) structure obeyed
+ new break elsewhere → ordinary reject, hinted attempt 2. #32 predicted-defiance framing banked:
floor itself preferred this carve in several draws — a repeat = the wall confirming, not noise.
**Hinted pull 2 (key 38b56cad) = branch (b) PASS on every term** (2 senses correct polarity ·
37/37 placed, Luk 9:55 restored · tails disjoint, #37 fifth hold · all pins home). Wall did NOT
materialize — first successful hint against an engine-preferred inverse carve; #32 note closed as
"hint overrode the preferred carve on attempt 2." Reviewer rulings banked: #28 tail-caveat on
record (gate 30/30 = prose refs only; tail correctness rests on the hint-construction chain) ·
LXX non-fire CORRECT (no OT-majority shelf remains) · Psa 68:30 verse-check cleared the engine
(#36) · renderings all reproach-family, "may" defect row defused by the draft's own gloss note.
**Second CC catch: reviewer's "count 3/15" corrected — hint use = off-count per the explicit
Queue-4 term; count stays 2/15.** Rth 2:16 blank-English row traced: SECOND SPLITTER EXHIBIT
(inverse shape — English pooled on the negation row 3756, verb row blank; ticket updated 94b7e2d).
**APPLIED 2026-07-09: pass line "using reviewed draw … (key 38b56cad) — no model call" + stamp
6f982c804354 both confirmed; prose byte-matched; written to lexica_def. Render PASS (7-point
checklist) → ἐπιτιμάω CLOSED, LIVE 2026-07-09.** Ship-with-intervention, off-count, streak 0.
Header-gloss ticket THIRD SIGHTING ("rebuke, chide" vs the card's own anti-blame-register gloss
notes). RANGE typography traced to code: Range/Coverage lack the serif class (.lex-prose) the
senses block gets (20-shared-components.jsx:257 / styles.css:1435) — standing template gap on ALL
cards, not new; two-line fix proposed, held for JP's go. **Session-3 running tally: shipped
ἐπιτιμάω (off-count) · count 2/15 · streak 0 · describe-don't-preach 10-for-10 · fold-compression
1 of 7 · "Grounding refs:" 0 · header-gloss 3 sightings · GREEN remaining 5: ταμεῖον G5009 ·
βιβρώσκω G977 · διανοίγω G1272 · ὑπομονή G5281 · κατανοέω G2657 (ὑπομονή pre-ruled: pre-register
the endurance-vs-hope split BEFORE its floor) · RED remaining 2: περιτομή G4061 · σκληρύνω G4645.**
**G1272 διανοίγω (in progress, OFF-COUNT — 6th straight escalation across sessions 2–3):** occ table
38 verses / 40 occ (Exo 13:12 ×2, Lam 2:16 ×2); no dotted cousins. 3-run {3:3} count-uniform but the
THIRD shelf rotates completely (stretching/spreading 6-verse · abstract/cosmological Job 38:32+
Zec 13:1 · root-spreading Job 29:19 solo) + d1 double-shelves 2Ki 6:17/Eze 21:22 — the ἐπιτιμάω
pattern exactly → mandated 10-run, banked. **Pre-registered for the 10-run (reviewer, banked):**
two stable clusters expected to hold — inner-faculty 5-verse formula (Luk 24:32, 24:45, Act 16:14,
17:3, Hos 2:15 — identical 3/3) + physical bulk with womb verses inside (no own shelf 3/3; the
womb-formula question answered at 3-run) — either moving = flagged surprise. Luk 24:31 files
PHYSICAL 3/3 (eyes-opened-recognized — consistent; name at ship). Fringe to settle: Job 29:19,
38:32, Pro 31:20, Zec 13:1, Gen 3:5.
**DECISION ITEM FOR JP (session boundary, reviewer-flagged, banked): the 3-run has stopped screening.**
6 escalations in 6 words (sessions 2–3) = paying 13 draws where 10 would do. Option 1 (cheap,
reversible, sequencing-only): skip the 3-run and go straight to 10 for any word with a poetry/Psalms
book share (the #35 tell). Option 2 (bigger save, touches the bar definitions — needs its own
validation pass): test whether 6–7 draws carry the 10-run's signal. Neither ruled; JP's call at a
session boundary, not mid-word.
**THRESHOLD FALSIFIED BY CONTROL DATA (banked before the number shipped — the check worked):** the
proposed ≥25% poetry/prophets trigger has NO clean split on the 14-word validation pull: σελήνη 61.5%
+ κῆπος 55.3% both PASSED at 3 draws (clean ships) while δάμαλις escalated at 23.7%. Book share flags
risk (#35's soft form stands) but cannot decide sequencing mechanically. **REVISED RULE PROPOSED
(grounds = the 6-for-6 streak itself, not the book table): for the REMAINDER OF BATCH 3 ONLY — a
hand-picked hard tail — skip the 3-run, straight to 10. Expires at batch close; reversible.** Note:
validation-pull percentages include dotted-cousin rows (strongs_base grouping) — conclusion robust,
the σελήνη/δάμαλις gap is huge either way.
**SCALE-PROTOCOL DECISION ITEM (banked for the batch-3 close window / build-plan economics; ~14,000
lemmas total, honest projection = thousands of dollars under the calibration protocol):** calibration
is deliberately expensive (buying trust in the bars); the batch-build phase should run the CHEAPEST
protocol calibration VALIDATED — the cheap path must be validated during calibration to be licensed
at scale. Four levers, biggest first: (1) occ-count gradient — ≤5-occ words can't carry complex sense
structure; 2–3 draw floor (or 1 draw + audit) for the long tail, which is MOST of the dictionary;
(2) N=10 → N=6-7 validation experiment — rerun two settled words at N=7, check every ruling
reproduces (~35% cut on every hard word if it holds); (3) model tiering — cheaper model for floor
draws (clustering agreement, not prose), Sonnet for the build draw; needs a head-to-head on a
settled word first; (4) the sequencing fix (real but small). None ruled; JP's call at batch close.
**διανοίγω 10-run: floor STABLE at 2-sense mode (exact carve 4×), both pre-registrations held,
plain pull 1 hit every bar → ONE #36 fabrication catch (Hos 2:15 "door of hope" = Hebrew/KJV
reading imported; ABP reads "open wide her understanding") → ruled delete-class swap via
fix_lexica_raw (apply-then-swap sequencing; diff = the cut phrase only) → within-sense duplication
ruled BLEMISH (κάλαμος cross-ref; reviewer's tell: sub-use adding ≤1 new verse re-citing shelved
members = redundant regroup, answers the overload fire) → render PASS →**
**διανοίγω CLOSED, LIVE 2026-07-09.** Ship-with-intervention (minor class), off-count, streak 0 +
OPEN streak-criterion definition question flagged for JP (hint escalation vs one deleted
parenthetical — criterion doesn't distinguish; audit entry has it). Header-gloss COUNTER-EXAMPLE
logged ("open fully" consistent — ticket stays 3 sightings). **Session-3 running tally: shipped
ἐπιτιμάω + διανοίγω (both off-count) · count 2/15 · streak 0 · describe-don't-preach 11-for-11 ·
fold-compression 1 of 8 · "Grounding refs:" 0 · GREEN remaining 4: ταμεῖον G5009 · βιβρώσκω G977 ·
ὑπομονή G5281 · κατανοέω G2657 · RED remaining 2: περιτομή G4061 · σκληρύνω G4645.**
**THREE RULINGS (JP 2026-07-09, "whatever you guys recommend" — CC+reviewer joint recommendation
adopted as the ruling):** (1) **STRAIGHT-TO-10 for the remainder of batch 3** — the 3-run screen is
0-for-6 on this hand-picked hard tail; grounds = the streak itself (the 25% poetry threshold was
FALSIFIED, see above); expires at batch close, reversible. (2) **Streak criterion STANDS,
conservative** — the test is whose judgment the ship depended on; διανοίγω was wrong as drawn and
shipped correct only because the audit caught it → streak 0 was right. (3) **Intervention CLASS now
tracked in the tally** (hint-escalation vs swap-class) without changing the streak rule — feeds the
batch-close decision on whether the cheap batch-build path needs a fabrication-check step.
**Intervention-class tally opened (retroactive, this batch):** hint-escalation ships = κάλαμος ·
δάμαλις · παράπτωμα(-hintless, RED plain pull 2: none) — precisely: hinted ships κάλαμος, δάμαλις,
συκῆ, βέλος, χριστός, ἁμαρτία, ὀφθαλμός, ἐπιτιμάω; swap-class ships: ἁμαρτία (1 delete-swap, also
hinted), χριστός (2 ruled swaps, also hinted), διανοίγω (1 delete-swap, PLAIN — the only
swap-on-plain ship); clean-plain ships: δίκτυον, σελήνη, κῆπος(AMBER), γόνυ, νίπτω (the 2 escapes),
παράπτωμα (pull 2).
**G977 βιβρώσκω CLOSED, LIVE 2026-07-09** (first word under straight-to-10; unanimous {2:10} floor,
plain pull 1, one reword-class swap ["cultic law" lead misnamed its group — machine-invisible,
human-caught], render PASS). Splitter EXHIBIT 3 = Job 18:13 ("And may"+"be devoured" both 977; occ
corrected 39/37, Isa 51:8 sole true double; gloss-note-as-detector heuristic + downstream-surfaces
line banked to the ticket 63dbd6f). #36 session tally 4 engine-clears / 1 catch. Precedent:
intra-sense form-based organization = engine's prose discretion when memberships match the floor.
Header-gloss counter-example #2. Swap-on-plain ship #2 (with διανοίγω). **COUNT PENDING JP** —
options (a) on-count 3/15 (reviewer) · (b) escape-class per γόνυ precedent · (c) CC middle path
RECOMMENDED: 3/15 + swap logged as "GREEN-would-have-shipped-this" data point. Full record: audit
doc G977 entry. **Session-3 running tally: shipped ἐπιτιμάω + διανοίγω (off-count) + βιβρώσκω
(count pending) · streak 0 · describe-don't-preach 12-for-12 · fold-compression 1 of 9 · "Grounding
refs:" 0 · GREEN remaining 3: ταμεῖον G5009 · ὑπομονή G5281 · κατανοέω G2657 · RED remaining 2:
περιτομή G4061 · σκληρύνω G4645.**

## BATCH-3 SESSION 2 LOG (2026-07-09) — CLOSED; see the audit doc's SESSION 2 CLOSE entry for the
## tally + case law. This block is the session's running record, banked as it happened.
**Opened:** clearing gate PASSED with a rule-9 caveat (the handoff's grep string "SESSION 1 CLOSED
2026-07-09" isn't verbatim in the doc; the same fact appears as the session-1 log header + Queue item 4
wording — JP ruled gate cleared, not held).
**GREEN ROSTER GAP (logged, JP-confirmed):** the 17 GREEN roster NAMES are not in any committed doc —
only counts + the 8 processed words. Blocks GREEN resumption only; JP pastes the remaining 12 names,
CC banks them here before any GREEN draw. (Rule-8 class: count without contents.)
**RED seed = G3900 παράπτωμα, JP-confirmed** (strongest routing exercise: Romans-5 freight, highest
fabrication temptation, NOT in the contested register — RED routing must carry the word alone).
**Reviewer watch PRE-REGISTERED (banked on relay):** παράπτωμα is the floor-vs-ship placement-class
profile — one dominant Pauline sense + quieter literal/lesser senses. Watch the draft (i) promoting the
Romans-5 sense's placement above what the occurrence table supports, (ii) burying a lesser sense the
floor puts higher. Reviewer compares PLACEMENT, not presence, at render.
**G3900 παράπτωμα (RED, in progress):** occ table 36 verses/40 occ (4 doubles: Col 2:13, Eze 18:26,
Mat 6:15, Rom 5:15); Jer 22:21 = 3900.1, correctly excluded (no leak). 3-run {1:2,2:1} → rule-mandated
10-run: **{1:7,2:3}, floor called STABLE at 1 sense.** The Pauline/Adamic carve appeared 3× with three
DIFFERENT memberships zero repeats (d9 {11:11} · d10 {5:15,5:18,5:20,11:11} + Rom 5:15 double-shelved ·
3-run d3 {5:15,11:11}; 3-run junk carve "(Unattested…)" over Zec 9:5+Rom 5:20) = ὄρος-class optional
sub-slice. Rom 5:15 + Rom 11:11 both 10/10 support, 10/10 company with the general cluster. All
pair-drops back-checked = folds (single-sense subset draws). Zero MISSED-collocation warnings.
**Pre-registered ship bars (banked on relay + floor):** (i) Romans-5 material promoted to PEER sense =
bar-fail (floor certified the split unstable — reviewer's γόνυ/νίπτω-in-Romans-5-clothes watch);
sub-use/texture inside sense 1 = legal. (ii) Watch absorption drift toward Rom 4:25/Eph 2:5 — none
formed at floor. (iii) Any within-draw double-shelf = self-disqualifying. Mode 7/10 majority (not
unanimous) → #32 hint candidate on cap-out only; plain pull first.
**Pull 1 (key b74b0d48) = BAR-FAIL, redraw.** Adam material placed LEGALLY (sub-use in sense 1 — bar (i)
passed) but the draw invented a DIFFERENT peer sense the floor drew 0/13: "state of accumulated
offenses" over Eph 2:1/2:5/Col 2:13 (dead-in construction), breaking Col 2:13 (10/10) + Eph 2:1 (8/10)
off unanimous floor homes — νίπτω-class misplacement — AND double-shelved Col 2:13 [1,2] (machine fire
+ pre-registered bar (iii), first co-arrival of the two signals). 3 "dead in" rendering-mismatch fires
= quote-mark noise class (context wording, not a rendering claim). Sub-use overload (5) moot pending
pull 2. Gloss-note uniformity claim ("transgression(s)") to verify against corpus on the shipping pull.
**Reviewer observation BANKED (JP relay, pull-1 ruling): the placement class has a SECOND costume.**
Session-1 escapes = right senses, wrong level; G3900 pull 1 = floor-UNATTESTED peer carve (plausible
grammar, zero floor attestation) while the pre-registered hotspot passed clean. Passing a pre-registered
bar does NOT clear the placement check — every peer-level carve must be floor-attested; the comparison
is full-structure vs the floor, not flagged hotspots. (ENGINE_LESSONS candidate ONLY if the shape
repeats — pull 2 did NOT repeat it, so banked here, no lesson entry.) Double-shelf flag confirmed as a
correlated tripwire for the class, not a substitute detector.
**Pull 2 (SAME key b74b0d48 — multi-draft key, fingerprint check ruled in) = PASSED CC audit:** 1 sense
= floor mode; Rom 5 as construction (c) + scale-sub-use (legal placement); dead-in trio home; 4 machine
fires all quote-mark noise; tails 5/5 vs table; freight + describe-don't-preach clean. Blemish notes
(no action): Eph 2:1/2:5 loose fit under construction (a); Dan 6 "religious" context wording. Pending:
corpus render-uniformity check + cache fingerprint (0/1 greps) → apply --require-cache --from-draw.
**Checks PASSED (JP relay + PA output):** renders = transgressions 23 + transgression 17 = 40/40, exactly
the header's 2, all transgression-family → uniformity claim verified full-corpus (JP tightening on
record: a 3rd rendering would have failed "uniformly" even if transgression-shaped — note edit, not
redraw). Greps 0/1 → key b74b0d48 holds pull-2 prose. **Describe-don't-preach 7-for-7** (JP: Rom 5
scale-not-function prose = hardest test yet, held). **Construction-fit example banked (JP shading):**
Eph 2:1/2:5 under construction (a) = pull-1 residue homed in the roomiest construction, not the
best-fitting — the example case if a placement-diff tool ever scores construction-level fit. Not a bar.
Apply cleared; awaiting "using reviewed draw … no model call" line before render.
**APPLIED 2026-07-09: "using reviewed draw … (key b74b0d48) — no model call" line CONFIRMED verbatim;**
prose byte-matches reviewed pull 2 (2127/622 chars, same 4 noise-class fires, no new); written to
lexica_def. **Render PASS (reviewer relay) → G3900 CLOSED, LIVE. RED seed #1 exercised — session-2
routing precondition MET; RED routing verdict: behaved as designed start to finish.** Full record: the
audit doc's G3900 entry (incl. the header-gloss provenance ticket + the "the lemma" V7.1 decision item
— frozen to the batch-close window per standing rule 7). Watch tallies after G3900: describe-don't-
preach 7-for-7 · fold-compression 1 of 4 · "Grounding refs:" 0 · overload tally unchanged (no fire) ·
κύων/συκῆ pre-registrations still unfired. Count 2/15 unchanged (RED off-count), streak 0 (pull-1
bar-fail). ~~NEXT: 12 GREEN roster names needed~~ **roster banked by name `460c02e` + un-staled
`8e6c1c7` (live remainder 9 GREEN + 2 RED).**
**G2965 κύων (in progress, OFF-COUNT — escalated per ἄκανθα precedent):** occ table 37 verses/38 occ
(1Ki 21:19 ×2); dotted cousins .1 (Exodus garments) /.2/.3 (Esther) /.4 (1Sa 9:24) all correctly
excluded, no leak. 3-run {2:1,3:2} job-boundary wobble → rule-mandated 10-run: **{2:4,3:6} — floor
called STABLE at the 3-sense mode, grouping-variance regime (κάλαμος class), no holes** (all wobbles
fold; 2Ki 9:36 + 1Ki 21:24 back-checked = subset sampling). Clusters: literal · dyadic insult (six
Samuel/Kings verses 10/10) · epithet core (Mat 7:6/Php 3:2/Rev 22:15 10/10) — the two figurative
clusters NEVER exchange members in 3-sense draws (reviewer's discourse-mechanics read confirmed:
dyadic status-ladder vs categorical boundary); merge direction in all four 2-sense draws = the two
figurative clusters folding. No complete carve repeats identically (fringe scatter: Isa 56:11, Deu
23:18, Ecc 9:4, 2Pe 2:22) — exact mode exists → plain pull first, hint on cap-out (#32).
**PRE-REGISTERED MAJORITY HOMES (ship placement bars):** literal = Psa 59:6 (9/10; double-shelved in
2 floor draws — strain point), Psa 59:14, Ecc 9:4 (7/9, reviewer watch answered), Job 30:1 (6/10),
Isa 66:3 (9/10), Exo 11:7, 2Pe 2:22 (9/10) · insult = 6 Samuel/Kings + Psa 22:16 (9/10), Psa 22:20,
Psa 68:23 · epithet = core + Isa 56:10 (8/10), Isa 56:11 (thin 2/10) · **Deu 23:18 = the contested
one: 6/10 epithet majority home; literal filing = 4/10 minority, needs adjudication not silence.**
Any ship-draft double-shelf = automatic fail. **Pre-registration adjudication limit (banked):** the
committed wording at 5188565 is only "most-likely-GREEN-to-fire" — whether floor-level escalation
satisfies "fire" is the reviewer chat's call (armed content never banked); fact banked = escalated
off GREEN at floor, count stays 2/15.
**RULING (JP chat, banked verbatim): "κύων pre-registration FIRED, mechanism = job-boundary wobble →
mandatory 10-run → off GREEN."** Basis: committed wording governs; "fire" for a GREEN word = leaving
the GREEN tier (ἄκανθα precedent); any narrower private meaning died unrelayed — the standing rule
working as designed. συκῆ pre-registration stays armed; its CONTENT owed one banked sentence from JP
(requested — do not draw συκῆ before it lands).
**Pull 1 (key 76bec69c) = BAR-FAIL, redraw. Zero machine fires; 3 placement breaks vs the
pre-registered homes:** Isa 56:10–11 → literal sub-use vs 8/10 epithet home (biggest break) · Ecc 9:4
→ figurative vs 7/9 literal (the predicted escape shape on the neighbor verse — 2Pe 2:22 itself was
filed literal CORRECTLY) · Psa 68:23 → literal vs 5/6 insult company. Deu 23:18 bar HELD (figurative
shelf, honest hedge). Also the 4/10 minority 2-sense merge shape with the epithet job NOT visible as
a labeled sub-use (δίκτυον-fold visibility not met) — but the redraw rides on the membership breaks.
More #30 evidence: machine all-green, floor comparison caught everything.
**συκῆ ARMED CONTENT (JP, banked verbatim — fresh arm from this chat, prior meaning dead unrelayed;
hold released at this commit):** "συκῆ pre-registration: watch whether the draft imports the Mark 11
cursing narrative's freight into the word itself — the word means the fig tree, full stop; any
headline or sense carve organized around judgment-on-Israel symbolism, barrenness-as-verdict, or the
cursing episode as a distinct 'job' is imported theology, not attested usage, since the symbolic work
belongs to the narrative act, not the lemma."
**LESSON CANDIDATE (JP, 2× this session — παράπτωμα p1 dead-in argument, κύων p1 Isa 56 behavioral-
grounding argument):** the placement check compares against the FLOOR, never against the draft's own
justification, however competent the prose — plausible prose is not floor attestation. (Formal
ENGINE_LESSONS entry = close-out decision.)
**Pull 2 (same key) = BAR-FAIL #2, whack-a-mole:** fixed all three pull-1 breaks (Isa 56:10–11
epithet ✓, Ecc 9:4 literal ✓, 2Pe 2:22 literal ✓), drew the 3-sense mode — then broke FOUR different
verses: Deu 23:18 SILENTLY literal (the pre-named νίπτω shape on the pre-named verse, bar violated) ·
Psa 22:16+22:20 → categorical vs 9/10+5/5 insult company · Psa 68:23 → categorical vs 5/6 insult ·
Job 30:1 → categorical vs 6/10 literal. Zero machine fires both pulls. κάλαμος 3-pull pattern
replaying per #32 (mode sampled, not obeyed). Pull 3 = last plain pull before cap-out → mode-hint
with pinned homes.
**Pull 3 (same key) = BAR-FAIL #3 → CAP-OUT.** 2-sense minority shape; Psa 59:6 DOUBLE-SHELVED [1,2]
(machine fire; 59:14 rides both lists too) = automatic fail; Deu 23:18 silently literal AGAIN (3-pull
record on that verse: epithet-hedged / literal-silent / literal-silent). Note: this fold DID label the
categorical sub-uses (visibility half improved while membership broke). Three pulls, three shapes
{2,3,2}, three distinct break sets — sampling regime fully characterized (κάλαμος twin; JP's
three-disjoint-break-sets line satisfied). Zero relevant machine fires except the p3 double-shelf.
**HINT FLAGS (verbatim reference for the apply — hinted applies repeat these exactly):**
  --structure-hint "The literal animal - dog as physical creature: the Kings scavenging-judgment
  formula, behavioral similes (Jdg 7:5; Psa 59:6, 59:14; Pro 7:22, 26:11, 26:17; 2Pe 2:22; Ecc 9:4;
  Luk 16:21), rulings and valuations (Exo 11:7, 22:31; Isa 66:3; Job 30:1)"
  --structure-hint "Dyadic insult or self-abasement between persons - speaker places self or one
  adversary on a status ladder: 1Sa 17:43, 24:14; 2Sa 3:8, 9:8, 16:9; 2Ki 8:13; and the hostile-pack
  Psalms 22:16, 22:20, 68:23"
  --structure-hint "Categorical label marking a class of persons outside a boundary: Isa 56:10-11;
  Mat 7:6; Php 3:2; Rev 22:15; Deu 23:18"
**Pre-clearances proposed to JP (κάλαμος lesson):** Psa 59:6/59:14 literal-only (simile-about-enemies
prose fine, citation on literal shelf only; repeat double-shelf = fail not bridge) · Deu 23:18 epithet
per 6/10 home (hedged sanctuary-context prose welcome; silent literal = fail).
**PRE-CLEARANCE RULINGS (JP, banked verbatim — adjudication criteria for the hinted draft):**
Ruling 1 — Psa 59:6/59:14 LITERAL-ONLY, no double-shelf tolerance; any appearance on job 2/3 "even as
a 'cf.' or parenthetical" = fail (9/10 literal majority; simile is the vehicle, the word denotes the
animal). Ruling 2 — Deu 23:18 JOB 3; hedge welcome, hedge NOT required; confident job-3 filing = pass;
"any literal filing, hedged or not, against the pin" = automatic fail.
**HINTED DRAW (key d4485213) = FAIL — the mechanism's FIRST MEMBERSHIP DEFIANCE (record 6-for-7).**
Structure fully obeyed (3 senses, speech-mechanics seam, hint logged on draw). Ruling 1 HELD (Psa
59:6/59:14 literal-only ✓; Psalms trio dyadic ✓; Job 30:1/Ecc 9:4/2Pe 2:22 literal ✓). Ruling 2
VIOLATED: Deu 23:18 primary = sense-1 labeled sub-use ("the lemma itself designates the animal") +
sense-3 "may belong" hedge = literal filing against the pin + double-shelf [1,3] + 7c fire. PLUS Isa
56:10 double-shelved [1,3] vs 8/10 home + the hint's own job 3. Machine caught BOTH double-shelves
(flags + floor agree for once). Wall class = the ὀφθαλμός disposition-placement limit (V7 pile item
6): hint moved structure, could not move these two memberships. CC recommendation to JP: ONE more
hinted pull, flags verbatim (no data on hinted-pull variance; one defiance = still sampling); a second
defiance on the same verses = repeated membership wall → ὀφθαλμός-class decision (park vs V8
prompt-restructure) to JP.
**HINTED PULL 2 APPROVED (JP) — ADJUDICATION PRE-REGISTERED BEFORE OUTPUT EXISTS:**
(a) Deu 23:18 literal primary (hedged or not) OR either verse double-shelved again → membership wall
CONFIRMED, ὀφθαλμός class, **κύων PARKS — no third hinted pull** ("spending money to re-measure a
measured thing"); (b) both pins obeyed + everything else home → ship path resumes (full 38-verse
placement check still runs); (c) pins obeyed but a NEW break elsewhere → ordinary reject, counts as
hinted-tier attempt 2; existence of a hinted attempt 3 = CC flags against Queue-4 terms, no
improvising; (d) Isa 56:10: prose MENTION of the barking idiom inside sense 3's own paragraphs =
fine; the failure mode is citation/filing on shelf 1, not acknowledging the literal substrate.
**MECHANISM-RECORD OBSERVATION (JP, banked):** both defied verses are where the engine showed a
consistent directional preference across plain pulls (Deu 23:18 literal 2-of-3 + the floor's own 4/10
minority; Isa 56:10 layered reading in p1 + the hinted gloss note) — the hint moved everything the
engine was indifferent about and failed exactly where it has a preference. *Hint compliance appears
inversely related to the engine's own placement-preference strength.* Sharper than the ὀφθαλμός
characterization. If parks: session ships = παράπτωμα only; parked = ἄκανθα + κύων; next word from
remaining GREEN roster.
**HINTED PULL 2 (key d4485213): clause (a) FIRED — Deu 23:18 double-shelved [1,3] AGAIN → κύων
PARKED 2026-07-09.** REVISIT FRAMING (JP refinement, banked): the keep-both option is not a concession
to the engine — Deu 23:18's floor was itself 6/4, the closest majority on the board, and the referent
is genuinely debated; frame the revisit as "adjudicate the ambiguity or enforce the majority" (the
δάμαλις move), NOT "fix the defiance." Isa 56:10 cured, 37/38 placements home — the wall is ONE VERSE wide, held through
two hinted draws in the same shape. Preference-strength observation CONFIRMED with a gradient (weak
preference bent, strong held). Mechanism record: structure 8-for-8, membership 6-for-8. Full record +
revisit question (ruling-not-redraw: keep-both adjudication on Deu 23:18 or V8 placement mechanism):
audit doc G2965 entry. Park roster πολύς + ἄκανθα + κύων. Session tally: ships = παράπτωμα (RED);
count 2/15; streak 0; GREEN remaining 8 (κύων off roster): συκῆ · βέλος · ταμεῖον · βιβρώσκω ·
διανοίγω · ὑπομονή · ἐπιτιμάω · κατανοέω; RED remaining 2.
**G4808 συκῆ (in progress, OFF-COUNT — escalated per ἄκανθα precedent):** occ table 38 base verses/39
occ (Mat 21:19 ×2); dotted Amo 4:9 + Jer 5:17 (4808.1) excluded, no leak. **Pre-registration verdict
at FLOOR level (JP, banked): FREIGHT STAYED OUT** — 13 total draws, zero judgment/barrenness carves,
cursing verses home literal 9/10; the pre-registration's draft-level half stays armed (prose is where
imported theology blooms). 3-run {1:1,2:2} appear/vanish → 10-run **{1:3,2:5,3:1,4:1}, NO exact modal
carve** (the 2-sense draws split literal+formula vs literal+parable). **NEW STABLE JOB FOUND: the
vine-and-fig-tree security formula** (1Ki 4:25, 2Ki 18:31, Isa 36:16, Mic 4:4, Zec 3:10) — 10/10
support+company, own sense 6/10, exact 5-verse membership identical 3× (d2/d6/d9) = certified.
Illustration carve = uncertifiable scatter (4+ shapes, zero repeats; d7 split visionary+fable
singletons) — discourse role, not a sense; folds. "Illustration isn't a sense — it's what a speaker
does with the word; a carve that can't exist without double-shelving is self-refuting" (JP, the 3-run
read, confirmed at depth). **NEW DRAW-QUALITY ARTIFACT logged:** d1 built a 6-verse card on the idiom
ignoring 33 fed verses; d9 drew NO literal sense — degenerate draws, not carves (all [1,9] wobble
noise resolves to this). **COUNT-BLEED FRAMING (JP, banked):** 2/15 with three escalations = the
tiering doing triage; the GREEN streak measures words the engine handles WITHOUT depth — routing hard
words out is the design. **Floor call: 0-exact-mode → first-draw hint LEGAL (δάμαλις extension). CC
recommends 2-job hint (literal plant · formula idiom); illustration fringe NOT hinted (not a certified
job). Homes proposed pending JP:** formula-5 own shelf exact · Joh 1:48 literal (6/9; allusion prose
ok) · Jdg 9:10 literal (~5/8, wobbliest verse; fable prose ok) · prosperity-loss verses literal (d5
absorption = 1/10) · cursing/parable/apocalyptic literal-cited-only.
**HOMES CLEARED (JP) + two additions, banked pre-run:**
(1) **Jdg 9:10 tolerance ruling (verbatim):** "citation literal-only; a fable-framing sentence in
prose is welcome; a fable sub-use LABEL under the literal sense is also acceptable (it's a genuine
discourse frame and sub-uses aren't shelves) — what fails is a peer sense or any second-shelf
citation." (2) **PRESENCE FLOOR (named check, this draft):** sense 1 citing under 20 of the 33
literal-home verses = completeness fail even if every present citation is correctly placed — the
degenerate-draw shape (d1/d9) at draft level; presence has a floor too, not just placement.
(3) **ENGINE_LESSONS candidate (JP + CC concur):** "watches catch what we fear; floors find what's
there" — the armed freight watch ran clean 13/13 while the actual finding (formula shelf) was
unpredicted. Close-out decision.
**συκῆ HINT FLAGS (verbatim reference — the apply must repeat these exactly):**
  --structure-hint "The literal fig tree as a plant - agricultural, botanical, and narrative
  occurrences, INCLUDING verses where the tree sits in parable, simile, fable, or apocalyptic
  discourse (the discourse frame is prose context, not a sense): Gen 3:7; Num 13:23, 20:5; Deu 8:8;
  Jdg 9:10-11; Psa 105:33; Pro 27:18; Son 2:13; Isa 34:4; Jer 8:13; Hos 2:12, 9:10; Joe 1:7, 1:12,
  2:22; Hab 3:17; Hag 2:19; Mat 21:19-21, 24:32; Mar 11:13, 11:20-21, 13:28; Luk 13:6-7, 21:29;
  Joh 1:48, 1:50; Jas 3:12; Rev 6:13"
  --structure-hint "The 'under one's own vine and fig tree' formula - a fixed idiom of settled
  security and undisturbed possession, exactly these five: 1Ki 4:25; 2Ki 18:31; Isa 36:16; Mic 4:4;
  Zec 3:10"
**Hinted first draw (key 1c350763, single-draft key — fingerprint waived) = PASSED both audits.**
Presence floor: 38/38 TOTAL coverage (33 literal + formula 5; third total-coverage card) — the
degenerate-draw fear inverted. Jdg 9:10 cleanest tolerance path (literal-only, fruit-behavior
sub-use). No double-shelves. Overload (5 sub-uses) ruled KEEP by both (distinct discourse frames,
#14; Son 2:13/Mat 24:32 seam = carve-aesthetics, both correctly placed). Ficus carica = uncontested
species (noted for the κάλαμος precedent, not doubted). Mat 21:19 ×2 unmarked = blemish-no-action.
**συκῆ PRE-REGISTRATION FINAL (JP, banked): freight stayed out at floor (13/13) AND at draft (prose
describes narrative acts, never adjudicates) — both halves answered, WATCH RETIRED on this word.**
Pending: gloss-note check (2Ki 18:31 bare "tree" AND sole divergence — a second row = note edit, not
redraw) → apply (flags verbatim + --require-cache) → pass-line read → render.
**Gloss check PASSED (exactly one row: 2Ki 18:31 "tree" — divergence real AND sole, full-corpus).
APPLIED 2026-07-09: hint-injection line + "using reviewed draw … (key 1c350763) — no model call" both
confirmed verbatim; prose byte-matches reviewed draft; written to lexica_def.**
**Render PASS → συκῆ CLOSED, LIVE 2026-07-09.** LXX-note conformance = answered from code
(20-shared-components.jsx:246, shared component, placement/boilerplate fixed; δάμαλις = prior
specimen). Full record: audit doc G4808 entry. **Session-2 running tally: shipped παράπτωμα (RED) +
συκῆ · parked κύων · both tonight's ships off-count (escalations) → count 2/15, streak 0 ·
describe-don't-preach 8-for-8 · fold-compression 1 of 5 · "Grounding refs:" 0 · συκῆ watch RETIRED ·
GREEN remaining 7: βέλος · ταμεῖον · βιβρώσκω · διανοίγω · ὑπομονή · ἐπιτιμάω · κατανοέω; RED
remaining 2: περιτομή G4061 · σκληρύνω G4645.**
**G956 βέλος NEXT (JP-confirmed; count needs a scorable word). WATCHES ARMED PRE-TABLE (JP, banked):**
(1) **Eph 6:16 freight** — lone NT occurrence, only loaded one; the word means the projectile, the
spiritual-warfare frame is Paul's discourse; a sense carved around "spiritual attack" = imported
freight; correct handling = literal weapon + metaphor as prose context or at most a sub-use.
(2) **LXX-skew gate check** — near-all-OT evidence means the provenance note SHOULD fire on any
shipping sense; a non-fire = machine-gate question (shared component just code-confirmed tonight).
(3) **Divine-archer wildcard** — lightning-as-God's-arrows (Psalms, Habakkuk) + pestilence/judgment
arrows (Deu 32, Job 6): arrows are arrows, who looses them is context — BUT if the floor carves a
stable God's-arrows cluster (the συκῆ formula-five shape), that's attested, we follow the evidence;
"pre-registration cuts against imported carves, not attested ones."
**βέλος occ table:** 38 base verses / 40 occ (2Ki 13:15 ×2, 13:17 ×2); dotted 956.1 (Eze 4:2, 17:17,
21:22, Jer 51:27) excluded, no leak. 3-run {2:2,3:1} + Isa 49:2 double-shelved 2/3 → mandated 10-run
(FOURTH escalation tonight, βέλος off-count). **LESSON CANDIDATE (JP, banked): corpus size + referent
concreteness are weak floor-stability predictors; figurative-use density is the better tell** (βέλος:
half the corpus is Psalms/Job poetry — the tell was in the book column all along). Not the
scorable-word hope failing; the pre-word difficulty estimate was wrong.
**10-run {1:1,2:8,4:1} — floor called STABLE at 2-sense mode (literal projectile | affliction-figured-
as-arrows), κάλαμος grouping-variance regime; count mode 8/10 strong → PLAIN PULLS FIRST (no
first-draw hint; δάμαλις extension needs 0-exact-mode count).** Findings vs the three pre-reads:
figurative core CERTIFIES (Job 6:4+Psa 38:2 10/10, +57:4/16:9/64:7 9-10/10, Eph 6:16 with them 8/10;
own shelf 6/10 majority-distinct) · lance trio (Job 30:13/34:6/39:22) = certified CLUSTER 10/10
internal, own shelf 3× identical membership (d2/d3/d9) but majority home literal 7/10 → sub-use right,
peer = minority · Isa 49:2 RESOLVED literal 8/10 (no Deu 23:18 rerun) · **theophany set (2Sa 22:15,
Psa 18:14, 77:17, 144:6, Deu 32:23; internal 9-10/10) = TRUE 5/5 literal-vs-figurative → 7a: either
home legal, conditions = set stays together + single-shelved.** Floor double-shelves (d8 Psa 127:4;
d10 2Sa 22:15+Psa 18:14) = border strain markers. **SHIP BARS BANKED:** Eph 6:16 inside the figurative
sense, headline = affliction/hostility-figured-as-arrows NOT "spiritual attack" · lance trio
sub-use-or-fold, not peer · Isa 49:2 literal · theophany together, single-shelved, either home ·
double-shelf = fail · LXX-skew watch fires at ship (note should fire on any shipping sense).
**7a EDGE SHARPENED (JP, pre-draft, banked):** the theophany latitude requires Deu 32:23's membership
explicitly — if the set goes figurative, Deu 32:42 travels with 32:23 (same divine-archer speech);
splitting the Deu 32 pair across shelves = coherence break INSIDE the latitude. Set travels whole or
7a doesn't apply. **Second draft watch:** d1's Eph 6:16-solo shape (1/10 artifact) = imported-freight
in floor clothes; a solo Eph sense fails on minority structure AND the freight watch.
**Pull 1 (key 80d9354c) = BAR-FAIL on one pin: Isa 49:2 double-shelved [1,2]** (machine flag + prose
confirms; pin was literal-only, 8/10 home). Everything else HELD: theophany 7a exercised clean
(literal option, set whole, Deu pair together) · lance trio sub-use with honest weapon-type
agnosticism · Eph 6:16 in-cluster, headline "harmful force figured as an arrow" (freight watch passed
at headline). LXX note fired senses 1+2 (skew watch satisfied at draft level). **Carried to pull-2
audit:** (1) Psa 64:7 prose "infant's arrow" — verse-text check required before any version ships
(fabrication-family checkpoint); (2) gloss-note/shelf mismatch — note calls Psa 127:4 "clean instance
of Sense 2" but the card cites it nowhere in the senses block.
**Psa 64:7 CHECK CLEARED (verse text read):** ABP reads "the arrow of infants became their
calamities" — the strange construction is the TEXT's own (LXX), not a fabrication. Shipping prose must
track "arrow of infants" as written; "divine judgment" framing = interpretation, watch but not a
block. Checkpoint closed.
**Pull 2 (same key) = BAR-FAIL #2: FIVE double-shelves** (Deu 32:23, Psa 11:2, 45:5, 91:5, 127:4 —
citation tail-lists swept borders onto both shelves; heaviest double count of the night). Isa 49:2
FIXED (sense 1 only) and the Psa 127:4 note-mismatch cured — then broke new ground: the Deu 32 pair
split exactly as pre-named (32:42 sense-2-only, 32:23 both = 7a coherence break). Psa 64:7 prose
tracked "arrow of infants" verbatim ✓. Whack-a-mole pattern continues. Pull 3 = last plain pull.
**TAIL-LIST MECHANISM (JP observation pull 2, CONFIRMED 3-for-3 at pull 3):** the five pull-2 doubles
all sat in per-sense parenthetical citation tail-lists while prose placed them once; pull 1 (few
tails) = 1 double, pull 2 (comprehensive tails) = 5, pull 3 (prose-only cites) = 0. "Comprehensive
per-sense citation lists are a double-shelf generator on words with soft borders." Cross-checked vs
record: παράπτωμα + συκῆ shipped cards cite in-prose, zero doubles at ship. → ENGINE_LESSONS entry
candidate + V8 prompt item (cite-in-prose-only). Format-level finding, not placement-level.
**Pull 3 (same key) = BAR-FAIL #3 → CAP-OUT.** Zero double-shelves (the correlation's third point) but:
2Ki 13:17 figurative vs 7/10 literal company WITH an explicit "the two senses overlap at this verse"
hedge = 7c violation (card won't commit to its own citation) — the verse JP pre-named at pull 2 ·
"being setting on fire" prose garble (proofread catch, unshippable) · Isa 49:2 pin dodged by omission
(uncited). Two machine fires = known noise classes. Three pulls: {Isa 49:2 double} → {5 tail doubles}
→ {13:17 hedge-break} — corrections propagate, breaks move; whack-a-mole third word running.
**HINT FLAGS (verbatim reference — apply must repeat exactly; theophany stability pick = FIGURATIVE,
the 4-of-5 figurative-draw composition, κάλαμος stability-pick precedent):**
  --structure-hint "The literal projectile shot or wielded as a physical weapon - combat, hunting,
  siege machinery, the lance-trio contexts as a delivery-mode sub-use, and the quiver/symbolic-act
  verses: 1Sa 20:36-37; 2Sa 18:14; 2Ki 9:24, 13:15-18 (including 13:17, the arrow Joash physically
  shoots), 19:32; 1Ch 12:2; 2Ch 26:15; Job 20:25, 30:13, 34:6, 39:22; Psa 11:2, 91:5, 120:4, 127:4;
  Isa 5:28, 7:24, 37:33, 49:2; Lam 3:12; Joe 2:8"
  --structure-hint "Affliction, hostility, or divine action figured as arrows - no literal archer in
  view: Job 6:4, 16:9; Psa 7:13, 38:2, 45:5, 57:4, 64:7; the divine-storm set whole and together
  (2Sa 22:15; Psa 18:14, 77:17, 144:6; Deu 32:23, 32:42); Eph 6:16 inside this sense, never alone"
Weak-majority Psalms (11:2, 91:5, 120:4, 127:4) pinned literal with their floor companion Isa 49:2.
**PINS VERIFIED + CLEARED (JP, line-by-line vs banked floor). Status note banked: Psa 11:2 = the
loosest pin (7/10, company leans figurative 6/7 with the affliction core) — pre-named as the most
likely defiance point; if the hinted draft double-shelves or migrates EXACTLY Psa 11:2, that's the
preference-gradient pattern → straight to the κύων wall file, not a redraw loop.**
**ADJUDICATION CARRIED FROM κύων (pre-registered before output):** defiance on a pinned verse in the
same shape twice = wall, park · obey-pins-but-new-break = ordinary reject, attempt 2 of the hinted
tier · full prose proofread on ANY structurally passing draft, no skimming familiar-looking parts
(the pull-3 "being setting" garble is the reason).
**HINTED DRAW (key a41ba4d3) = PASSED full audit. ALL PINS HELD** (Isa 49:2 + 2Ki 13:17 + weak-
majority Psalms literal incl. Psa 11:2 — the pre-named defiance point did NOT defy; theophany whole
figurative, Deu pair together; lance sub-use; Eph 6:16 in-sense, freight headline clean). Zero
double-shelves despite tail-lists (disjoint). Mechanism record → structure 9-for-9, membership
7-for-9; NO wall on this word. **Proofread caught a fabrication SUSPECT that verse-check CLEARED:**
Lam 3:12 "stone as aim-point" — ABP's own text reads "he set up a stone target for me as the aim for
the arrow" (the stone is textual; suspicion checked BEFORE claimed, cleared the engine); Job 16:9
"arrows of his marauders" verbatim ✓. Residue: "in a contest" = not in verse, blemish-no-action
(substance textual). LXX note fired 1+2 (skew watch satisfied). → apply --require-cache --from-draw
a41ba4d3 + both flags verbatim (single-draft key, fingerprint waived).
**JP rulings + findings banked pre-apply:** "in a contest" = blemish-no-action CONFIRMED (παράπτωμα
"public accountability" class) · **SYMMETRIC-CHECKPOINT lesson candidate:** 3 fabrication checkpoints
this session, 2 cleared the ENGINE (Psa 64:7, Lam 3:12) — ABP renderings are strange enough that
reviewer intuition false-positives on them; "verify before claiming fabrication, not just before
claiming attestation" · **preference-gradient 2-for-2 both directions** (predicted κύων's wall;
predicted-absent = no wall on Psa 11:2) · **tail-list refinement (4th data point):** the generator is
tail-lists WITHOUT disjointness enforcement — the hint's explicit memberships enforced disjointness;
V8 candidates = cite-in-prose-only OR a disjointness check.
**APPLIED 2026-07-09: hint line + "using reviewed draw … (key a41ba4d3) — no model call" CONFIRMED
verbatim; prose byte-matches (4502/826); written to lexica_def.**
**Render PASS → βέλος CLOSED, LIVE 2026-07-09.** Full record: audit doc G956 entry. Header-gloss
ticket SECOND SIGHTING ("missile" unattested in all three translations — systemic). Prose-"missile"
= no-action, rendering-claim vs descriptive-vocabulary distinction on record. **Session-2 running
tally: shipped παράπτωμα (RED) + συκῆ + βέλος · parked κύων · all three ships off-count (escalations)
→ count 2/15, streak 0 · describe-don't-preach 9-for-9 · fold-compression 1 of 6 · "Grounding refs:"
0 · GREEN remaining 6: ταμεῖον · βιβρώσκω · διανοίγω · ὑπομονή · ἐπιτιμάω · κατανοέω; RED remaining
2: περιτομή G4061 · σκληρύνω G4645.**

## BATCH-3 SESSION 1 LOG (2026-07-08/09) — shadow calibration opened. Read this + the audit doc's
## batch-3 entries to resume session 2.
**Roster JP-approved: 17 GREEN candidates + 3 seeded RED** (G3900 παράπτωμα · G4061 περιτομή · G4645
σκληρύνω — **all three UNEXERCISED; session 2 must run at least one** to complete the routing-exercise
goal). Words processed 8: **γόνυ p2 (ESCAPE 1) · δίκτυον p1 (count 1) · νίπτω p2 (ESCAPE 2) · ἄκανθα
PARKED · σελήνη p1 (count 2, zero-fire) · κῆπος p1 AMBER · κάλαμος attempt-4 hint + APPLY INCIDENT
(#31) + SPLITTER FIX (af8e296) · δάμαλις first-draw hint (middle-case type specimen).**
**Tally: 7 shipped / 2 escapes / 1 parked / count 2/15 / streak 0 / 12 remaining.**
**THE 12 REMAINING, BY NAME (roster gap closed 2026-07-09 — the close had banked counts without contents):**
GREEN candidates (9): συκῆ G4808 (fig-tree; Mark-11 freight pre-registration armed) · κύων G2965 (dog;
pre-named most-likely-GREEN-to-fire, Phil 3:2/Rev 22:15 epithet) · βέλος G956 (dart) · ταμεῖον G5009
(secret chamber) · βιβρώσκω G977 (eat) · διανοίγω G1272 (open fully) · ὑπομονή G5281 (endurance) ·
ἐπιτιμάω G2008 (rebuke) · κατανοέω G2657 (perceive/consider). Seeded RED (3, all unexercised AT
SESSION-1 CLOSE; G3900 since EXERCISED + SHIPPED in session 2 → live remainder = 9 GREEN + 2 RED = 11):
παράπτωμα G3900 (sin-family, fork-adjacent) · περιτομή G4061 (Gal/Rom contest) · σκληρύνω G4645
(Rom 9:18 hardening fork). Processed 8 (all from the GREEN 17): G1119 G1350 G3538 G173 G4582 G2779
G2563 G1151 — arithmetic: 17 − 8 = 9 GREEN + 3 RED = 12 ✓. Both escapes were
the floor-vs-ship placement class, caught ONLY by human comparison (machine gates green both times) —
the parked placement-diff detector's evidentiary basis (ENGINE_LESSONS #30).
- **Ruled procedures (standing, batch-wide):** every apply `--require-cache` (or `--from-draw`); hinted
  applies repeat hint flags VERBATIM; apply output READ for "using reviewed draw … no model call" before
  the render step (absent = full stop); occurrence-table query BEFORE the floor (mirror check + tails
  pre-armed); screenshots to chat-Claude only (CC gets pass/fail relayed); content-fingerprint check
  before --from-draw on MULTI-DRAFT keys only (single-write keys have nothing to disambiguate).
- **Case law born this session** (index; detail = audit doc batch-3 close + ENGINE_LESSONS #30–#32):
  cluster-membership-not-sense-count (the fold/misplacement line) · bar-fail vs escape (bar-fail-on-GREEN
  pre-ruled: breaks streak, not the escape count) · three-regime floor taxonomy (stable / grouping-
  variance / membership-scatter) + **middle case shippable on 3 conditions** (stable membership · a carve
  repeated identically ≥3× · every contested placement majority-homed or 7a-selected; δάμαλις = type
  specimen) · **mechanism extension: first-draw hint legal on 0-exact-mode floors** · sampler-not-
  mode-knower (#32: the floor computes the mode, the hint transmits it) · layer-tracing before format
  fixes (#21 update) · merge-review = look-trigger (2-for-2 ruled) · streak = draw quality, routing =
  audit cost.
- **Open watches into session 2:** describe-don't-preach 6-for-6 (standing) · κύων + συκῆ pre-registrations
  (unfired; κύων pre-named most-likely-GREEN-to-fire) · fold-compression tendency (1 of 3) · overload
  threshold tally (2-for-2 ruled correct carves; 5-for-5 → tuning log-line) · "Grounding refs:" label (0).
- **Tickets banked this session:** display window — sub-use indent (κῆπος test page) · LXX ⓘ + multi-sense
  footnote (δάμαλις/σελήνη/κῆπος test pages) · V6 style-alignment decision. Engine (parked) — apply
  refuse-by-default + content-hash (one ticket, two demonstrated halves). Detector (parked) — floor-vs-ship
  placement diff (evidence: 2 escapes + 2 κάλαμος bar-fails, all mechanically flaggable). Lint noise-shape
  family: quote-mark · disclaimer-as-cite · case-position · lemma-transliteration-as-claimed-gloss ·
  dangling-refs ("Dan" = canonical).

## SESSION-3 CLOSE STATE (2026-07-07) — read this to resume
**SESSION-4 FIRST ACT: the ὀφθαλμός morning fork** (re-roll vs. argued-shelving on cached draw `0abd875d`) —
see BATCH STATE. Session-3 shipped φωνή (batch #10 / 9-of-20 roster), fired + resolved the first escalation
(structure-hint mechanism), and parked ὀφθαλμός one fix-list short of shipping.
- **State carried below is current through S3.** V6 live (freight + whitespace); `--force-verse` + `--structure-hint`
  live; escalation counter 3/3 fired+resolved; V7 pile banked; lessons #18/#19 + FLOW step 1.5 + graduation rule live.
- **ENGINE STATE — all LIVE:** **V6 prompt** (Formatting block + term-of-art line + **translation-freight line**
  [ENGINE_LESSONS #18] + **Sub-use whitespace line**; stamp now `lexica:1ccea0a44740`, was `0c58c8a74b4f`) ·
  gloss-set **case-fold** (merges "Heaven"/"heaven"-class artifacts) · **both parser tolerances** (per_sense
  reuses _sense_spans; split_definition falls back to header-less bold-numbered senses). Locking tests (CI +
  pre-commit): `tests/test_lexica_agreement_parse.py`, `tests/test_lexica_glossset_fold.py`.
  - **V6 bump mechanics (2026-07-07, S3):** freight + whitespace lines added to `VERSE_PROMPT` AND to the
    reviewer's byte-identical frozen copy (renamed `V5_PROMPT`→`V6_PROMPT`, `PROMPTS` default → `v6`) in the
    same commit; `_check_prompt_sync` green. **Stamp bump is INERT** — grep-gated: the only stamp-reader that
    rebuilds is `build_lexica_def.py`'s own per-word skip check; no cron/deploy runs `--all`, serve layer
    ignores `synth_ver`. The 10 shipped words now read "stale-stamped" (cosmetic; prose untouched, nothing
    auto-rebuilds). ⚠ the manual `--resplit --all --apply` Seam step would relabel un-redrawn rows V6 without
    re-drawing — don't read a bare V6 stamp as "reviewed under V6."
  - **TWO V6 WATCHES (check on first V6 draws, ὀφθαλμός redraw is the first):** (i) **over-trigger** — reviewer/
    engine flagging ordinary glosses as "drifted" (freight-paranoia); the "all are loaded" clause is the retained
    guard. (ii) **philosophize** — output discussing the freight rule instead of following it. If either fires,
    the line comes back to the table before word 12.
- **ESCALATION COUNTER = 3 — TRIGGER FIRED + RESOLVED (2026-07-07).** πολύς (range-completeness) · ἅγιον
  (structure near-wall) · **ὀφθαλμός (structure↔freight oscillation — 3 pulls, never both clean; cap-out ruled
  straight-across per οὐρανός, no reset for the V6 bump)**. **Mechanism ruled = STRUCTURE-HINT, now LIVE:**
  `--structure-hint` (commit 95b4a16) passes the reviewer's certified stable-jobs list as draw CONTEXT (steers to
  ground truth, frozen prompt untouched, logged like --force-verse, post-cap-out use only). NOT draw-until-match,
  NOT prompt-steer (freight line proven to work). **A FOURTH wall re-arms the trigger** → reopen the option space
  (higher-cap · prompt-steer · widen the hint) with the structure-hint's first-use evidence in hand.
- **STYLE WATCHES:** #1 slashes — addressed in V4, body-prose scope still MONITORING (not extended);
  #2 term-of-art — addressed in V5, the point-6 audit is live (first catch-and-clear on οὐρανός); #3
  whitespace — **SHIPPED in V6** (2026-07-07): *"each Sub-use begins on its own line, with a blank line
  before it."* rode along with the freight bump; first live test = ὀφθαλμός redraw. **NEW post-V6 watches:
  see the two V6 watches under ENGINE STATE (over-trigger, philosophize).** **#4 "the lemma" meta-register
  (FILED 2026-07-08, χριστός — was recall-only until now, exactly the #27 tracking-slot class):** sense
  prose narrates the analysis ("the lemma describes / functions as…") instead of stating the meaning.
  Long-standing house dialect, PERSISTED THROUGH V7 UNCHANGED → prompt-version-independent; the freight/
  whitespace lines neither caused nor cured it. Sometimes load-bearing (usage-behavior senses — χριστός
  2–3, where what the word is DOING is the sense), sometimes filler (openers that survive deletion intact).
  If ever ruled a defect, the fix is an EXPLICIT prose-register rule at a prompt window, not hoping a
  revision washes it out. No ruling requested; collect per card.
- **V7 PILE — ALL RULED at the window walk (JP, 2026-07-08); ledger: 1 BUILD · 2 BUILD · 3 DROP
  (premise corrected inline below) · 4 BUILD · 5 DROP (revisit = a shipped note quoting the aphorism) ·
  6 BUILD (prompt-steer, placement rule) · 7 BUILD (rendering-claim lint) · 8 BUILD (hedge lint) ·
  9 DEFER (revisit = second formula-lookalike, escape-weighted) · 10 BUILD (verse registry) · 11 BUILD
  (sub-use overload counter, added mid-walk). Builds live: prompt `b8cbe7c`, detectors `5831175`,
  sampling `c7f8620`. See "V7 WINDOW — CLOSED" above for the standing law. Item text below kept as
  the historical bank.**
  From a post-approval wording audit of the full V6 prompt (register / both-ways neutrality / stop-rules /
  new-line interaction / scope markers). Priority:
  1. **"line" → "entry" (×2), PRIORITY.** Method step 2 ("note the variation in the sense's line") and Output
     ("within that sense's line") mean the sense's *entry*, but the new whitespace line mandates each Sub-use
     begin on its own *line* — literal self-contradiction in the exact region the whitespace line stabilizes.
     **WATCH LINK:** if the whitespace watch wobbles on first V6 draws, this ambiguity is suspect #1 BEFORE the
     new line itself — and it would escalate from V7 pile to active-defect (one-word fix, but touches the
     whitespace blast radius mid-gate, so it does NOT jump the queue on its own).
  2. **Gloss-note flag is one-directional.** "Narrower, more loaded, or more doctrinally specific" flags only
     over-loading; no channel for a gloss BROADER/flatter than context (under-translation) — same asymmetry as
     the dikaioō lesson. Fix: "narrower or broader, more or less loaded, than the context supports."
  Lower priority:
  3. **Doubled vocabulary bar — RULED DROP at the V7 walk (JP 2026-07-08), premise corrected; do NOT
     resurrect at V8.** The banked "two tests on one behavior" premise was wrong: the tests differ —
     "corporate" PASSES the freight test (its plain English tracks "applied to a group") and fails only
     term-of-art (debate-register). Merging would trade a never-observed over-trigger (watch (i) 0 fires
     across all live V6 draws) for a real coverage hole on the ἱερεύς-"corporate" class. Both lines stay.
     **WATCH LINK (still live):** if V6 watch (i) freight-paranoia ever fires, the doubled bar re-opens as
     suspect #1.
  4. **Missing scope marker:** "gloss-free characterization" (Output) vs "you may use it" (gloss paragraph) —
     reconciliation inferable (headline not a bare gloss; matching gloss word may appear in the elaboration) but
     unstated. Fix: state it.
  5. **Register trim:** "It records how one translation disambiguated the word - a set of decisions, not the
     meaning" is quotable rationale (echo-into-gloss-notes risk). Trim-and-convert candidate. Rest passes register.
  6. **Disposition-placement mechanism limit (ὀφθαλμός evidence package, S4 2026-07-07).** Structure-hint +
     regard-anchor could NOT move a folded sub-use (disposition-toward-another) off physical onto its certified
     parent (regard): all six regard exemplars already fed AND the maximal (steering-clause) hint still filed it
     under physical. The wall is a PROMPT-RESTRUCTURE question, not a per-word draw fight. Option-space decision
     (widen hint channel / prompt-steer / higher-cap) reserved to JP, to be made WITH V7. Full record: audit doc
     `##### SESSION-4 OUTCOME — PARKED`.
  - **RECORD ENTRY (LOG, DO NOT "FIX").** The freight line's placement UNDER Formatting deliberately scopes it
    to senses + range; **gloss notes are outside its jurisdiction by design** — flagging a loaded gloss requires
    NAMING it, so "moral" quoted inside a gloss note is the line WORKING, not leaking. Consistent with the June-25
    "unless the gloss itself is under discussion" and the point-6 audit bar (headlines, body prose, range only).
    Logged so a future session doesn't "correct" the scoping as an oversight.
  - **Otherwise green:** neutrality + stop-rules bounded (import-drop rule, doctrinal-career ban, omit-if-nothing).
- **REDRAW QUEUE (3, post-batch, under V5+):** ἅγιον (slash headlines) · μέγας (slash sense-4) · ἱερεύς
  ("corporate" echo). Cosmetic-only, each cleared on neutrality, NOT hand-edited. Full detail: audit doc
  `### REDRAW QUEUE`.
- **STANDING RULES BORN THIS SESSION (operating discipline — follow next session):**
  1. **Fed-list verification** — an "unfed" claim is verified by READING the fed list, never inferred from
     draw silence (absorption and absence look identical from draw output; only the fed list distinguishes).
  2. **Gloss-notes assertion spot-check** — any gloss_notes claim ABOUT THE TRANSLATION (capitalization
     practice, etc.) is verified against the actual text, not just its refs (the citation gate checks refs,
     not assertions). Extends to sense-prose action verbs (ENGINE_LESSONS #12).
  3. **git-pull-first + the real PA preamble** — every PA command block starts with:
     `cd ~/bible-db && git pull && workon bible-env`
     (two stale-state incidents drove the pull; make it invariable). **Do NOT append `source .env`**
     — it currently ABORTS on an unquoted line in `.env` (`MAIL_FROM=Lexica <noreply@…>`; bash reads
     the `<` as a redirect, 2026-07-07). It's also unnecessary for the lexica scripts: both
     `build_lexica_def.py` (`get_key()`) and `lexica_agreement.py` (via `B.get_key()`) read the
     `ANTHROPIC_API_KEY` line out of `~/bible-db/.env` themselves — no `source` needed. NEVER grep
     `/var/www/…_wsgi.py` for the key (the script's docstring shows that, but it is NOT how we run it
     — don't read production files for secrets). Standalone `.env` fix, when convenient: quote the
     value → `MAIL_FROM="Lexica <noreply@lexica.bible>"` (unblocks anything that does `source .env`,
     e.g. the deploy script).
  4. **Infra/environment claims get VERIFIED, not asserted** — a sibling to "the audit doc
     outranks recall." Fresh sessions guess machine/env details confidently and plausibly (the
     grep-the-WSGI-for-the-key slip, 2026-07-07). Any claim about how the server runs, where a
     secret lives, what the venv/preamble is → check against the machine or ask JP, never assert
     from plausibility. Same defect class as the capitalization fabrication: invented rationale
     for an unobserved fact, aimed at the server instead of the corpus.
  5. **SESSION-OPEN: read the relevant `ENGINE_LESSONS.md` entries BEFORE the first word** (consumer side of the
     /wrap ENGINE_LESSONS gate, commit `f96a9a8`). The write side is gated at close; reading is not — and S5
     proved the *content* was adequate (τόπος's form-claim was #7 verbatim) while *consumption* was the gap, so
     the catch came from CLAUDE.md not the file, a re-derivation cost. Belongs in the open preamble alongside
     git-pull and the roster count-by-NAMES check. Verify the file by READING it, never by the handoff's lesson
     count (the count lagged the file this session — #20 line vs #21/#22 committed).
  6. **REGISTER-CHECK BEFORE ANY WRITE on a word outside tonight's roster** (ἔργον session, 2026-07-08). Before
     `--apply` / `--resplit` / `fix_lexica_raw` on a word that isn't the one you're actively shipping, check the
     contested register (`contested_register.py`) first — a loaded lemma may be forked, which changes what the
     operation must preserve. Born from checking χριστός's fork status before touching it in the `---` sweep;
     converts the "loaded word + about-to-modify → caution" instinct into procedure.
  7a. **5/5 SPLIT RULE (JP 2026-07-08, δύναμις).** A 5/5 split on a structure question = either shape legal as
     drawn, no per-word JP ruling needed. Conditions: the minority-invisible facet stays VISIBLE (named sub-use
     or inline construction — cited-in-a-list doesn't satisfy gate 3), and all other pre-registered bars hold.
     A 6/4 is not a 5/5 — 6 makes the majority shape the bar.
  7b. **THIN-SENSE AMENDMENT (JP 2026-07-08, δύναμις — governs all off-target rulings against minority carves).**
     An off-target ruling against a below-threshold carve bars it as a STRUCTURAL PEER (a sense absorbing
     majority-sense verses or reshaping the certified carve), NOT as a THIN sense (single-ref or near, self-
     flagged by the audit, absorbing nothing). Thin senses stay governed by the G80 standard. Test at the card:
     removing the thin sense leaves its verses homeless/force-fit → legitimate residue; verses fold cleanly →
     fold them.
  7c. **NO HEDGED CITATIONS (born δύναμις pull 2).** A sense's prose may not hedge its own verse's membership
     ("may overlap with senses X and Y without reducing to either") — a citation the card won't stand behind
     fails on coherence. If the draw can't shelve a verse confidently, the verse moves or the sense re-carves.
  7. **RENDER/SPLIT-LAYER FIXES ARE NOT ENGINE RESTRUCTURING (mid-batch ruling, JP 2026-07-08).** The mid-batch
     freeze protects the comparison baseline = what the engine DRAWS (prompt + draw behavior). A fix to the
     splitter / assembly / serve layer (`body()`, `--resplit`, render) only re-carves or re-displays already-drawn
     prose — draws before and after stay comparable — so it is LEGAL mid-batch. (Contrast: a VERSE_PROMPT change
     is engine restructuring and stays frozen till batch close.)
  8. **QUEUE GATE (JP 2026-07-08).** /wrap must either update the `## Queue` section or affirmatively state
     "Queue unchanged" — silence invalid. Same mechanism as the ENGINE_LESSONS wrap gate. The Queue holds
     ordering only; any content detail found in the Queue itself is drift and gets moved to its pointer target.
     A queue entry carrying a BLOCKED-ON claim gets its blocker verified by content-read (not existence-check)
     at the wrap that writes it.
  spot, ENGINE_LESSONS #4) · pre-V5 triage + post-batch redraw phase · the existing fed-40 / reviewer-tier
  questions below.
- **`ENGINE_LESSONS.md`** (repo root) — v2 design backlog, now **20 lessons** (#17 = fabrication family,
  #18 = translation-freight / the 4th freight axis banked 2026-06-25, #19 = MISSED-collocation is a
  floor-level check, #20 = dampen-not-delete + oscillation wall → structure-hint mechanism), self-guarding (every
  word-citation verified against the audit doc before commit). Distinct from this handoff + the audit doc;
  read it before any v2 design work, not before resuming the rollout.

## PER-WORD FLOW (the loop)
1. `lexica_agreement.py --word G#### --runs 3` (→ 10 on wobble). Read the STABLE jobs (present in
   ~all draws) + majority-distinct distinctions; wobbles back-check hole-vs-fold.
   - **1.5 (NEW, S3 — EYEBALL MISSED-COLLOCATION WARNINGS *BEFORE* CALLING FLOOR STABILITY).** A floor run
     on a fed sample that never showed the reviewer a high-PMI collocation certifies the stability of the WRONG
     inventory. Read every `⚠ collocation MISSED by draw` line (the draw prints them); for each, decide whether
     it's an unfed instance of an existing sense (fine) or an unfed IDIOM/JOB the reviewer couldn't have seen
     (→ the inventory is gapped; force those verses into the redraw sample, select_spread option (a)). This is
     a floor-level gate, not a ship-time nicety — it caught ὀφθαλμός's disposition region that 13 reviewer draws
     structurally couldn't (φείδομαι pity-family / πονηρός envy-family, both 0-fed). ENGINE_LESSONS #19.
2. `build_lexica_def.py --dry-run --force --word G####` → draft. Audit vs the four gates + standard
   checks (incl. the **#18 translation-freight** scan: no Latin/English category — "moral", "worship" —
   in headlines, body, or range; name the attested quality instead). If it misses the reviewer structure, redraw (cap 3).
3. Ship the first passer: `build_lexica_def.py --apply --word G#### --from-draw KEY8` (KEY8 printed
   by the draw; no model call on apply).
4. Post-ship: confirm `no model call`, gate pass, stamp current, senses on disk match.
5. Log the word in `AUDIT_lexica_rollout.md` (per-word flag rate, any precedent, wall status).

## BATCH STATE
- **BATCH-2 ACTIVE WORK CLOSED 2026-07-08 — 17 shipped · 3 parked (πολύς, ὀφθαλμός, ἁμαρτία — ἁμαρτία since
  SHIPPED at the Phase-1 requeue, see its session log block) · 0 unstarted.
  The V7 WINDOW IS OPEN** (V7 pile + requeue decisions [χριστός #1, ἁμαρτία #2, ὀφθαλμός restructure] + batch
  retro list + display-layer window question — all JP-sequenced from here).
- **SHIPPED + LIVE (18; batch-2 locked-20 = 17 shipped · 3 parked · 0 to go):** G1096 γίνομαι (session start, from-draw first exercise) · G80 ἀδελφός
  (4 senses) · G2588 καρδία (4 senses, one-draw ship) · G39 ἅγιον (4 senses, near-wall) · G1484
  ἔθνος (2 senses, converged attempt 2; detector's first live fire, Eph 2:11 bridge ruled+logged) ·
  G3173 μέγας (4 senses, one-draw ship; multi-shallow-axis wobble no-holes; 2Ch 17:12 bridge ruled) ·
  G2409 ἱερεύς (3 senses, granularity-as-drawn; first concrete role-noun; Gen 14:18 bridge ruled,
  dangling "Heb" accepted, V4 formatting 5/5) · G3772 οὐρανός (3 senses, attempt 3; cured a
  gloss_notes fabrication via the gloss-set case-fold — batch's strongest fix-the-input case; V5
  formatting 6/6; core-2 tightest of the batch) · G5204 ὕδωρ (3 senses, attempt 3; physical/ritual/
  figurative; naive tight-noun prediction FALSIFIED, usage-dimensionality confirmed; no wall, counter 2) ·
  G5456 φωνή (3 senses, one-draw ship; STABLE at 3 no escalation; utterance/non-vocal-sound/circulated-report;
  clean-multi agreed TIGHTLY at 3; seam #5 utterance↔report LOGGED, card honored not broke it; both
  standing-rule checks run pre-ship — fed-list + gloss-notes verified; style-watch #3 structural-mislabel banked) ·
  **G3735 ὄρος** (1 sense, clean 641-row feed after the dotted-lexicon fold fix `2ff5f7d`; STABLE-at-1; the
  ὀρ- homograph tail re-tagged upstream, +5 dotted numbers) ·
  **G2364 θυγάτηρ** (5 senses, attempt 2; multi-shallow-axis, tight prediction falsified; ARGUED-SHELVING ship —
  figurative visible via Ecc 12:4, Pro 30:15/1Sa 1:16 ruled-shelved; step-1.5 caught+fixed a paternal narrowing;
  Dan dangling-flag GRADUATED to systematic defect; screenshot-verified; gloss_notes-full gate fix `be027c1`).
  · **G5117 τόπος** (2 senses, attempt-2 redraw; physical + scope/opening; people-metonymy argue-shelved into
  the range, not a standalone sense — attempt-1's people-sense REJECTED for internal incoherence, headline
  asserting what its own gloss_note retracted; 2 post-ship `fix_lexica_raw` prose fixes, no model; BANKED LESSON:
  inflected-form claims in notes need PER-ROW morph verify — 2Sa 19:39 blank lemma+morph, 68/538 ~13% blank-lemma
  systematic OT gap; screenshot-verified).
  · **G2041 ἔργον** (2 senses, attempt 1 + 3 post-apply freight patches; deed/act | task-labor, product in range;
  THREE #18 freight failures one caught POST-apply → ENGINE_LESSONS #23 "freight scan = every definitional field";
  works-of-law de-freighted UNPROMPTED (credit); detector FIRST FIRE on a hallucinated cite (draw 5, not shipped);
  `---` root fix `1be84b7` + corpus sweep → G5547 χριστός also cleaned, class closed; blank-lemma 16.0% = class
  rate; streak 0; screenshot-verified).
  · **G2094 ἔτος** (1 sense, attempt 3 + 2 ruled prose swaps [de-jargon "eschatological", biographical-register
  refit for Exo 6:16/1Sa 17:12]; floor 3↔1 wobble → `--runs 10` = {1:8,2:2} STABLE-at-1, majority threshold ≥6/10
  pre-registered BEFORE the run; pulls 1–2 killed by verse-level fabrications — the 1Sa 17:12 "in days of Saul"
  FORMULA-LOOKALIKE anchor, logged ENGINE_LESSONS #17 instance (d); NOT a content-wall (structure held, trigger
  tally unchanged); per-row morph verified on the gloss-note parse claim (ετών N.GPN ×2); inline quotes
  spot-verified; tight-agreement predictor dented a 3rd time; streak 0; screenshot-verified).
  · **G758 ἄρχων** (2 senses [human ruler | superhuman-domain ruler], **CAP-OUT at 3 pulls → JP ruled cap-out
  NOT content-wall (tally stays 3) → one structure-hint draw [2nd use, validated] shipped clean** + 4 ruled
  prose swaps incl. the **1Co 2:6/2:8 seam NAMED ON THE CARD** via gloss-note bullet (φωνή-pattern; gloss-note
  routing avoids the sense-citation boundary); floor {2:9,4:1}, superhuman 8/10 required, tenure 1/10 folds;
  Rev 1:5 ruled stricter-bar into sense 1; all 3 pulls' fabrications sat on Christ/Molech → **ENGINE_LESSONS
  #24 loadedness-scaled verification**; #17 instance (e) harmonizing; exit-condition pre-registration honored;
  streak 0; screenshot-verified).
  · **G1411 δύναμις** (3 senses [army/host | broad capacity, deed folded-visible | persons THIN], attempt 3 + 3
  ruled swaps [τέρας "wonder" import cut from sub-use AND range — #23 fired live, range copy caught second-pass];
  floor {2:1,3:5,4:4}: capacity/force split 1/10, deed exactly 5/10 → **5/5 rule born (7a)**; pulls 1–2 = consistent
  OVER-SPLIT prior (stacked rejected carves, not oscillation) + **hedged-citation defect class born (7c)**; pull-3
  persons thin-sense → rule collision → **thin-sense amendment (7b)**, resolved pre-ship; **LXX provenance note
  first live fire + first render** (mechanism closed); "LORD of the forces" formula shipped; #24 held (Est 2:18 +
  Neh 9:6 verbatim-verified); streak 0; screenshot-verified).
- **word_gloss:** G39 "Holy Place" → "holy, set apart" override LIVE (`a06a90b` + `--apply` rebuild
  on PA). Verified: word_gloss row = `holy, set apart|override`; count 17508 stable; `override`
  58→59, `tbesg` 73→72 (only G39 moved). **Library card confirmed rendering "hágion · holy, set apart"**
  (JP screenshot) — override live end to end. (The word-study card shows only "holy" — a separate
  display-layer gap, see queued tasks.)
- **PARKED:** G4183 πολύς — reviewer says stable-2 (number/degree), but the comparative/adverbial/
  temporal facets won't stay folded-and-visible in one draft (range-completeness wall). UN-STUCK by
  the four-gate bar (attempts 1/2/3 all failed gate-3 completeness only — corrected record, NOT a
  merge; one flagged discrepancy vs JP's recollection on attempt 2, non-blocking). Re-attempt when
  sequencing suits: first draft clearing all four gates ships, whatever its count.
- **ὀφθαλμός G3788: PARKED (final, S4 2026-07-07) — mechanism limit, disposition wall → V7.** The morning fork
  resolved: re-roll EXHAUSTED in-bounds (all six regard exemplars already fed → anchor lever dead; maximal
  hint still filed disposition under physical). JP ruled PARK + bank the wall as a V7 restructure input; the
  one ruled pull is UNSPENT. Full record: audit doc `##### SESSION-4 OUTCOME — PARKED`. History below:
- **◀ (S3 close) ὀφθαλμός G3788: PARKED at cached draw `0abd875d` (best draw yet).** The structure-hint
  mechanism WORKED: first draw to hold **structure + freight together** — certified 3-job structure restored
  (physical / **regard its own sense 2, not buried** / figurative-perception), **"moral" gone everywhere**, gates
  1–2 pass, whitespace + six-point clean, citations 41/41, both V6 watches clean across all three live V6 draws.
  Parked (not shipped) under the heightened bar + don't-ship-tired rule. **Two-item fix list for morning:**
  (1) **2Pe 2:14** out of the silent sense-1 physical list → into the disposition group with the **mandatory
  straddle note OR an argued shelving** (it's physical 5/10 in the floor); (2) **disposition sub-use re-homed**
  under regard (sense 2) or its own region — sub-use-of-PHYSICAL is outside the allowed set (repeats attempt-3's
  evaluative-under-organ error, milder). **Two minor riders:** locate the dangling-"Gal" flag source (NOT in the
  raw prose — likely summary-side extraction, verify); the Job 7:7 "inner prospect"→figurative shelving call.
  **MORNING FORK (decide first): hinted re-roll vs. argued-shelving path.** ⚠ **Re-roll odds note:** hint job 2
  bundled disposition INTO regard and the draw DECLINED it (homed disposition under physical instead) — so a
  re-roll may not place disposition where wanted without a sharper hint or the forced verses re-scoped. **Streak
  stays 0.** Full saga + attempt-3 raw + cap-out record: audit doc `### G3788 ὀφθαλμός … #### V6 ATTEMPTS → CAP-OUT`.
- **REMAINING: none — batch closed.** **ῥῆμα G4487 SHIPPED** (2 senses [speech | event/matter], attempt 1 + 1
  swap — the loaded-frame set's only first-pull survivor; cleanest floor since φωνή [STABLE-at-2 on 3 runs, no
  escalation → predictor: separability is the signal, class 1-for-3]; λόγος-distinction trap untaken;
  standing-check 2nd fire [Mar 9:32 false ref deleted, Mat 18:16 "matter" confirmed]; 1Pe 1:25 ×2 per-row
  verified; **#24 refined: fabrication tracks CONTESTED verses, not loaded referents** — ῥῆμα/ἁμαρτία controlled
  comparison; screenshot-verified both frames). **δύναμις SHIPPED**; **ἁμαρτία G266 PARKED**
  (cap-out + hinted draw tripped pre-registered exit (c) on a 2Co 5:21 gloss-note side-take — full dossier in
  the audit doc; routes to the V7 requeue with χριστός; the hint's anti-annexation direction WORKED
  structurally, the kill was meta-field). Standing check born: **gloss-note rendering-claims verified against
  the printed verse text before they pass** (two corpus instances of self-refuting meta-field fabrication:
  οὐρανός, ἁμαρτία). 2Co 5:21 = reviewer-attested contested shelf (4/3/2+1 tally); branch-A attribution shape
  (ABP's "sin offering" is the corpus's rendering; explanations name the LXX חַטָּאת precedent as the
  translation's basis, never Paul's meaning) is the hard bar at requeue.
  (Full locked-20 list + selection method in the audit doc's Batch Two section.) **ὄρος + θυγάτηρ + τόπος + ἔργον
  + ἔτος + ἄρχων SHIPPED** — moved to the LIVE list above. Their tools: the operationalized freight test, #23
  full-field scope, and NEW **#24 loadedness-scaled verification** (every descriptive claim on a loaded referent
  verse-text-verified before gate time — the ἄρχων lesson, born on exactly their word class). δύναμις carries a
  free preview: uncited "rulers and powers" collocation logged on the ἄρχων card (25v, PMI 5.46).
- **STRUCTURE-HINT APPLY MECHANICS (2nd use, ἄρχων):** a hinted draw's cache fingerprint INCLUDES the hint list —
  the `--apply --from-draw` command must repeat the SAME `--structure-hint` flags byte-identical, or the tool
  reads the draw as "stale" and refuses (a correct refusal; nothing writes). Code-verified, cost one retry. **Loaded-frame three (ἁμαρτία / ῥῆμα / δύναμις) are the audit-hardest —
  the operationalized freight test (evaluation in a definition = fail; as cited context = pass) + #23 full-field
  scope are the tools they'll lean on.**
- **POST-FINALIZATION REQUEUE LIST (JP-ruled standing queue):** ~~#1 χριστός~~ **SHIPPED 2026-07-08**
  (fork + register landed together — see PHASE-1 SESSION LOG above). **#1 now = ἁμαρτία G266** (parked
  2026-07-08, exit (c); inherits the branch-A attribution bar, the 2Co 5:21 shelf tally, the sense-2 membership
  roster, and the theology-drives-the-carve dossier). Also the destination for anything the consolidated
  re-audit flags as redraw-worthy.
- **CONSOLIDATED RE-AUDIT (retro, one item):** re-audit pre-current-standards entries against the current gate set
  (freight + form-claims + structural coherence). χριστός already showed all three (self-collapsing 4→2 senses,
  Psa 2:2 double-shelf, unverified form-claims). Feeds the requeue list.
  - **Loaded-frame watch:** ἁμαρτία / ῥῆμα / δύναμις (audit hardest for a disguised loaded frame).
  - **Tight-agreement test (refined hypothesis):** θυγάτηρ / ὄρος — genuine one-dimension nouns,
    predicted to agree tightly at 3. Data so far: ἔθνος clean-binary → tight; **φωνή clean-multi (3
    distinct jobs) → still tight at 3**; πολύς/καρδία multi-*shallow*-axis → wobble; ὕδωρ stable-3
    but needed `--runs 10` (structure wobbled). Working rule: separability (not job-COUNT) predicts
    tightness — clean-separable jobs agree even at 3, shallow overlapping axes wobble. Confirm on the two.
    Note φωνή also showed the spread axis can surprise (propagation, not the speaker-type axis predicted).

## Queue (dependency-ordered — order lives HERE, detail lives at the pointers)
1. ~~ABP Session 9 certification~~ **DONE — arc CLOSED at S11 (2026-07-06, `1f2fd62`): rebuilt, gated, swapped,
   certified live.** The doc merge happened 2026-07-05 (`9bdaa32`). Nothing opens; remaining work (verified
   2026-07-08 against the S11 close state) = `verify_prose_leak.py` Tier-B-applied mode · `lint_split_wrong_slot.py`
   stale 18,339/12,692 label → 18,384/12,718 · prune stray worktree `.claude/worktrees/keen-goodall-f3e661/`
   (all detail: TODO.md S11 follow-ups). The other three S11 follow-ups are ALREADY DONE: G1096 redraw (shipped
   from-draw at batch-2 open), `--from-draw` ship path (`c4617d0`), citation-sweep rule (codified in
   `docs/claude/ai.md`). Detail: `CHARTER_cert_session9.md` top banner + memory `project_abp_certification`.
2. ~~V7 engine window~~ **CLOSED 2026-07-08** (`b8cbe7c` / `5831175` / `c7f8620`): all 11 pile items ruled,
   retro list closed, tiering law + calibration pins + rollout sequence on the record. Detail: the
   "V7 WINDOW — CLOSED" block in this handoff. Display tickets (sense-anchoring markers, note ordering)
   ruled HOLD for the three-zone redesign — with anchors codified in V7, a pure rendering job.
3. **Requeue rebuilds = Phase 1, the V7 control fires** — IN PROGRESS. **χριστός G5547 SHIPPED + LIVE
   2026-07-08** (fork + register landed together; record: the PHASE-1 SESSION LOG block below + the audit
   doc's G5547 entry). **ἁμαρτία G266 SHIPPED + LIVE 2026-07-08** (second control fire; hinted draw + one
   delete-class swap; ENGINE_LESSONS #29 = the V8 attribution-register input; record: its PHASE-1 SESSION LOG
   block + the audit doc's requeue entry). **ὀφθαλμός G3788 SHIPPED + LIVE 2026-07-08 — PHASE 1 COMPLETE 3/3**
   (hinted draw, zero swaps; the 5/5 placement finding + (b) ruling + disclaimer-as-cite artifact: its session
   log block + audit entry). The three V7 control fires are done; all three shipped via the structure-hint
   mechanism (5-for-5 structural), streak 0 per the standing ruling.
4. ~~Batch-3 = Phase 2 shadow calibration~~ **ROSTER COMPLETE 2026-07-10 (session 5): 18 shipped /
   2 escapes / 2 parked / count 3/15 (ships-within-budget) / streak 0. Record: SESSION-6 HANDOFF
   blocks above + audit doc session-1/2/3/5 entries.**
5. **CLOSE-OUT STACK — steps 1–3 + audit session DONE (session 6, 2026-07-10).** Step 1 signed
   off 18/2/2 (tally corrected by ruling, see audit doc FINAL-TALLY CORRECTION) · step 2 tally
   banked · audit packet banked reviewer-concurred (`a3e4e42`) · step 3 all six ruled + the
   activation-insurance amendment (record: audit doc STEP 3 block). Count 5/15 two-tier
   (δίκτυον, σελήνη, ὑπομονή, ταμεῖον, κάλαμος). **STEP 4 RAN + CLOSED 2026-07-10:** #30 built
   + control-fired on all three banked positives (`ac8ea96`) · pile triaged in full (audit doc
   STEP 4 entry) · V8 drafted NOT fired (candidate `v8` in lexica_agreement.py, live default
   v7, would-be stamp `lexica:7ef8620328a9`) · roadmap + corpus-defect protocol + JP quickref
   banked. **STEP-4 RULINGS CLOSED 12/12 in-chat 2026-07-10 (CLOSED block above; #42 adopted
   → ENGINE_LESSONS). STEP 5 RAN + CLOSED same day: V8 PROMOTED (JP KEEP ruling; live stamp
   `lexica:7ef8620328a9`; swap `fa18656`, re-sync `f631194`) · G2665 καταπέτασμα shipped+live
   (draw 3; draws 1–2 rejected, defect classes on record) · #30 fire classes BANKED (`7689884`)
   · first `audit.floor_diff` stored write · COUNT 6/15 name-true (δίκτυον, σελήνη, ὑπομονή,
   ταμεῖον, κάλαμος, καταπέτασμα; BOOK ruled by JP) · V9_PILE.md established. Full record:
   audit doc STEP 5 entry. **BATCH-4 SELECTION DONE 2026-07-10: roster of 10 APPROVED
   rank-true (διαιρέω G1244 · δόμα G1390 · εἰρηνικός G1516 · αἰχμαλωτεύω G162 · ἡσυχάζω G2270
   · μερίζω G3307 · παραπορεύομαι G3899 · σιωπάω G4623 · ἐκλύω G1590 · ἐπανίσταμαι G1881;
   10 picks = 9 owed + 1 spare). Both cost pendings RESOLVED per ruled item 12: poetry trigger
   RETIRED-as-rule / KEPT-as-label · N=6-7 paper replay APPROVED, no live change until JP sees
   the report. Routing table (6 out) + fork-adjacency rule banked verbatim; queue annotations
   ≠ watch tags. Record = audit doc BATCH-4 SELECTION entry (above STEP 5).** **WORD 1
   διαιρέω PARKED 2026-07-10 (three defect-class draws, pre-set no-draw-4 rule; floor was
   STABLE — defects all in the drafting prose; record = audit doc G1244 PARKED entry).
   Count 6/15 unchanged · nine words remain for nine owed, SPARE CONSUMED · εὐχαριστέω r15 =
   next-pass-up on further attrition · item-5 re-open ARMED (διαιρέω escalated; δόμα's 3-run
   decides) · ~~RULED ORDER: the N=6-7 paper checker builds + runs BEFORE δόμα's floor
   fires~~ **N=6-7 RAN + RULED same day: KEEP 10 (checker `c8d32fd`, 37 floors replayed
   zero-cost; exact-match bar failed honestly — known-stable and known-parked floors
   indistinguishable; V8 table no positive evidence; re-open = scale phase only, bar
   pre-registered blind; record = audit doc N=6-7 entry)** · structure-hint experiment
   queued to the tooling window; διαιρέω re-openable via that path.** **CORPUS-DEFECT FIRE
   same day (record = audit doc BATCH-4 CORPUS-DEFECT FIRE entry): δόμα G1390 DATA-BLOCKED
   (no-entry dotted 1390.1 leaked its feed; 3-run VOID, not an item-5 escalation — the fresh
   post-fix 3-run decides) · δίκτυον G1350 reader-facing contamination CONFIRMED (counted
   ship; architecture sense sits on 1350.1/.2 lattice rows; STAYS in the count until JP's
   4-step ruling chain) · δίδωμι stands · remaining eight roster words CLEAN · fix ticket =
   3 side-table entries via the builder, CC designs / JP executes checkpointed · standing
   amendments: no-entry dotted = contaminant by default, engine claims R1-verified, ranker
   occ = ceilings.** **εἰρηνικός G1516 SHIPPED + COUNTED same day — COUNT 7/15 name-true
   (δίκτυον†, σελήνη, ὑπομονή, ταμεῖον, κάλαμος, καταπέτασμα, εἰρηνικός; † = queued
   contamination chain). The calibration's first zero-reject word (pre-pull → 3-run certify
   → single draw → CLEAN → render PASS); UNSEEN-REAL ×6, five machine-invisible — the
   manual tail check load-bearing; streak 1. Record = audit doc G1516 entry.** **δόμα
   G1390 PARKED same day (JP; 3 defect-class draws on clean data — super-shelf +
   harmonization / UNSEEN-FABRICATED with the batch's first live gate-BLOCK / Ecc 5:1
   misplacement verse-confirmed; 19 draws by name; record = audit doc G1390 PARKED entry).
   ITEM 5: re-opened per roster reading, JP re-ruled STRAIGHT-TO-10 for the remaining
   words, 3-run retired for the batch, re-open condition SPENT. Roster: 7 words for 8
   owed → εὐχαριστέω G2168 ENTERS BY RE-SELECTION (screens queue next session: GREEN set
   + no-entry dotted pull + Last-Supper gloss watch). V9 case now overwhelming:
   carve-invention ×4 with edit direction banked (V9_PILE).** **RUN SESSION 2
   (2026-07-10/11): εὐχαριστέω G2168 PARKED (JP; pre-set 3-defect rule — carve-invention
   [V9 instance FIVE → CONFIRMED V9 EDIT, reviewer graduation] / Rom 16:4 verse-confirmed
   misplacement / Rom 16:4 verse-contradicted claim — the last two ONE stimulus trap, the
   parenthetical "to whom" mis-resolved; joins διαιρέω + δόμα on the structure-hint
   shelf). Floor STABLE at mode 1 post-fix. TWO READER GAPS FIXED same session: #47
   one-sense headline fallback (`40bfc78`; one-job house-shape cards scored 0 senses —
   first ship-path fallback exercised at d3's dry-run, marker LOUD) + singular "Gloss
   note:" label leaking the note into Range (splitter package #2). Sequence slips ×2
   logged as a PATTERN (config-test ledger). Eucharist watch 4-for-4 pass. Count 7/15,
   streak 1, both unchanged. Roster: 7 words for 8 owed → next-pass-up RE-SELECTION,
   full screens first. Record = audit doc G2168 PARKED + FLOOR-VOID entries.**
   **ἀληθής G227 (re-selection r14) PARKED same session (JP "PARK"; pre-set 3-defect
   rule — cross-lemma misattribution ×2 [NEW class, reviewer-named: 1Jn 2:8's "true
   light" = ἀληθινός G228 bled onto G227, d1 in a sense / d3 in Range] + machine
   hard-block d2 ["At 8:16" unverifiable refs, autonomous refusal] + double-shelf class
   d1/d2; draws IMPROVED 6→3→1 — parked on the rule, strongest structure-hint candidate
   on the shelf; floor STABLE 4-block, three pre-clears exercised correctly; standing
   procedure adopted: pre-pull patterns exact-or-dotted, never bare prefix). Count 7/15,
   streak 1 still unchanged. Roster: 6 words for 8 owed → next-pass-up ×2 (r15 ἀλλάσσω
   G236 first, then next clean rank), full screens each. Record = audit doc G227 PARKED
   entry.** **RUN SESSION 3 (2026-07-12): ἀλλάσσω G236 (re-selection r15) PARKED (JP
   "park if recommended"; pre-set 3-defect rule — d1 Isa 40:31/41:1 unattested split
   [2 defects, CORRECTED from 3: the Isa 24:5 gloss-note defect WITHDRAWN on verse text,
   head-column checker over-call — ticket priority raised] / d2 Gen 35:2 trade placement
   + Lev 27:10 double-shelve + 2Ki 5:5↔1Ki 5:14 transplant verse-confirmed / d3 Gal 4:20
   solo carve 0/10 "kept none"; trajectory 2→3→1, floor STABLE, 5th on the structure-hint
   shelf; full gate order held, zero sequence slips). Count 7/15, streak 1, both
   unchanged. Record = audit doc G236 PARKED entry.** **κλαυθμός G2805 (re-selection
   r16) PARKED same session (JP "--park"; pre-set 3-defect rule — the #49
   range-overclaim class fired ALL THREE draws on the judgment-refrain referent:
   d1 "permanent/abiding" + Gen 46:29 parting-header contradiction / d2 "no possibility
   of comfort" / d3 "permanent exclusion" + Jer 3:21 Rachel misattribution
   verse-confirmed; mechanical layer perfect 3-for-3 [#30 clean ×3, refrain shelf exact
   7 ×3, cousin κλαυθμών excluded cleanly] — the cleanest structure-hint signature yet;
   6th on the shelf; V9 pile +3 incl. the verbatim-quote V9-general candidate). Count
   7/15, streak 1, both unchanged. BOTH re-selections parked → roster 7 queued for
   8 owed, sequence question to JP. Record = audit doc G2805 PARKED entry (top).
   KNOWN-FRICTION line (reviewer): outputs posted between reviewer turns can silently
   miss the relay — REPOST rather than reference.** **δίκτυον G1350 REBUILT + SHIPPED
   CLEAN + LIVE same session (2026-07-12): fresh floor on the cleaned feed fed 34 =
   c171fd4 PROVEN at the feed (contaminated pull fed 40) · architecture sense FLOOR-REAL
   (own shelf 10/10 all draws) · ship draw 1 with ZERO machine warns / #30 zero fires /
   cousin six absent · "invisibly" ruled note-not-defect (taxonomy line:
   interpretive-theological = defect, physical-descriptive = note) · render PASS, alien
   verses GONE from the live card → **RULING-CHAIN (d) CONDITION MET, DAGGER OFF —
   COUNT 7/15 NAME-TRUE NO ASTERISK, STREAK 2.** Record = audit doc δίκτυον REBUILT
   entry.** **FRAGMENT-RENDERING INVESTIGATION same session (JP-caught): english_head
   fragments feed the def-engine rendering layer; fleet sweep = ONE hit (δίκτυον work
   bullet, known-issue logged, dagger STAYS OFF by JP ruling); rendering-layer ticket
   in TODO. Record = audit doc FRAGMENT-RENDERING entry.** **αἰχμαλωτεύω G162 PARKED
   same session (JP; 3-defect rule — crux-discipline rotation: d1 double-shelve ×2 /
   d2 reversal-reach / d3 harmonization-by-summary ["the giving of gifts" vs the
   psalm's "received"]; crux pair inseparable 10/10 on the floor; d1's crux handling
   PERFECT — the hint is one sentence. 7th on the shelf. Record = audit doc G162
   PARKED entry.** **BATCH 4 CLOSED BY JP RULING same session: final 7/15 name-true
   (δίκτυον rebuilt-clean, σελήνη, ὑπομονή, ταμεῖον, κάλαμος, καταπέτασμα, εἰρηνικός) ·
   streak 2 · 7 on the structure-hint shelf (διαιρέω, δόμα, εὐχαριστέω, ἀληθής,
   ἀλλάσσω, κλαυθμός, αἰχμαλωτεύω) · SIX queue words rolled forward UNRUN (ἡσυχάζω
   G2270, μερίζω G3307, παραπορεύομαι G3899, σιωπάω G4623, ἐκλύω G1590, ἐπανίσταμαι
   G1881 — the in-chat "4 remain / max 11" was a miscount, corrected in the audit
   entry; ruling unaffected; reviewer logged the same miscount against its own ledger).
   Record = audit doc BATCH 4 CLOSED entry.** **HINT TOOLING DESIGNED + FULLY RULED
   same session: `DESIGN_hint_tooling.md` (bff58fb, rulings folded in at the close
   commit) — constraint-hint register (draw_hints.py, provenance-carrying, JP-approved
   edits only) + `--hints` injection after the occurrences, frozen prompt + floors +
   gates untouched. JP RULED ALL FIVE: refuse-when-notes-forgotten YES · hinted ships
   count WITH MARKER (never conflated with unaided) · register edits = JP checkpoint ·
   rendering-layer fix lands FIRST · reviewer amendments accepted (marker +
   hint-provenance verification at every re-entry pre-reg).** NEXT SESSION OPENS ON:
   **(1) the fragment-rendering fix BUILD (ruling 4 sequences it first — phrase context
   to the def-engine rendering layer, phantom protection preserved, 2Ch 4:13 fixture;
   ticket detail in TODO.md) · (2) hint-tooling build per the ruled design · (3)
   reviewer walk of the seven register entries · (4) batch-5 charter (marker wording,
   re-entry order, fresh-floor list). NO WORD RUNS until (1) and (2) land.** Then
   batch 5 = shelf re-entry with hints + the six rolled-forward words → GREEN
   activation, then step 6 layout. R1 note for the next opener: verify commits
   bff58fb + the session-close commit on disk first thing (the reviewer's record
   holds them as owed artifacts). Item-3 tooling (incl. the structure-hint experiment — now the named re-entry
   path for ALL FOUR parked batch-4 words) + /consolidate = parallel gap work, still green.**
6. (was 4, historical) **Batch-3 sessions 1–2 record** — **sessions 1 AND 2 CLOSED 2026-07-09.**
   Session 2: 3 shipped (παράπτωμα RED — routing exercise met · συκῆ · βέλος, all off-count via
   escalation), κύων parked (one-verse wall, Deu 23:18), 4-of-4 escalations; count 2/15, streak 0;
   remaining 6 GREEN + 2 RED. Record: BATCH-3 SESSION 2 LOG block + audit doc session-2 entries +
   ENGINE_LESSONS #33–#37 + #32-update. Session-1 record below unchanged. (roster approved
   17 GREEN + 3 RED; 8 words processed: 7 shipped / 2 escapes / 1 parked; count 2/15, streak 0, 12 words
   remaining; the 3 RED seeds unexercised — session 2 must run one). Session-1 record: the BATCH-3 SESSION 1
   LOG block above + audit doc batch-3 entries + ENGINE_LESSONS #30–#32. **Two terms made explicit
   2026-07-08 (JP chat-thread review):**
   (i) a structure-hint use on a batch-3 word removes it from the calibration count (a GREEN word that caps out
   has left GREEN by definition — stated so it's not implicit); (ii) HYPOTHESIS carried, not believed: "fed
   count ~80 is load-bearing" (n=3: χριστός 607→81, ἁμαρτία 582→82, ὀφθαλμός 645→85; confounded with V7 + PMI
   slots landing together). Note GREEN words feed ALL occurrences, so batch 3 mostly does NOT test the ~80
   tier — that test resumes on the next high-frequency batch. Detail: tiering law + calibration pins in the
   V7 block; frequency-cutoff logic, audit doc.

Background tier (no ordering): former TODO/retro pile items — consolidated pre-standards re-audit (NOW ALSO
CARRIES: ἅγιον+κλητός occasion-job read · οὐρανός+βασιλεία metonymy read — the V7 sweep's two candidates),
blank-lemma query, backup rewrite, invariant #8, Dan-flag, no-entry triage, inverse-dotted audit, homonym
heuristic, topic-file merge, ~~MISSED-warning sweep~~ (RAN at the V7 walk: 16/18 clean, zero senses lost),
draw-cache archive, word-study-header Hebrew half (detail: TODO.md), θεός sense-1 item B (detail: memory
project_lexica_dictionary DEFERRED + audit doc).

## RETRO LIST — **DECISION ITEMS CLOSED at the V7 walk (JP, 2026-07-08) under the 6,000-definition /
minimum-JP-audit frame.** Outcomes: style ticket → codified (house shape, V7) · MISSED-collocation sweep →
RAN, 16/18 clean · warning-suppression-by-coverage → still a v2 nicety, untouched · reviewer tiering →
GREEN/AMBER/RED law (V7 block above) · fed-40 sufficiency → ANSWERED by dynamic sampling (≤40 feeds all,
measured 76%) · thin-sense accumulation → an AMBER flag (7b test) · gloss-notes assertion-verification →
BUILT (rendering-claim lint) · substitution-probe → stays minor/open (the οὐρανός-βασιλεία re-audit read
feeds it). Item text kept below as the historical bank.
(original header: decide with full-batch evidence, not per-word)
- **Style ticket — single-sense multi-construction organizing paragraph (JP-ruled 2026-07-08, N=1 ἔτος):** ἔτος's
  "It appears in four recurring constructions…" paragraph between headline and bullets. Not a defect, not a gate;
  ἔτος stands as shipped. Collect instances through batch-2 close (ἄρχων / δύναμις candidates if they fold hard):
  does the draw produce the paragraph unprompted? Consistent → V7 codifies it as the house shape for
  one-sense-many-facets cards; sporadic → V7 forces it one way. JP decides at V7 with instances in hand.
- **MISSED-collocation sweep (NEW, S3 — cheap, do at batch close):** re-run one `--dry-run` per shipped word
  and read its `⚠ collocation MISSED` warnings; ὀφθαλμός proved a 0-fed high-PMI collocation can hide a whole
  unfed job (disposition region) that a stable floor never saw. Confirm none of the 10 shipped cards has the
  same buried-inventory gap. If several do → escalates the case for select_spread option (b) (collocation-aware
  feed quota, ENGINE_LESSONS #8/#19) over per-word forcing.
- **Warning-suppression-by-coverage (NEW, S3 — v2 nicety):** the MISSED-collocation warning keys on the
  collocation's OWN verses, so once a forced verse (Deu 15:9) covers an idiom family, the warning still fires
  ("0 in fed") because it can't see the family is now represented. Refinement: suppress/annotate a MISSED
  warning when a forced verse already covers that collocation's family. Minor; not now.
- Reviewer tiering: is per-word min-3 the right floor, or tier by boundary type (clean-separable →
  ship on 3; multi-shallow-axis → 10)?
- Fed-40 sufficiency: the 40-verse (20/20) spread is pragmatic, not derived (~4% on a 900-occ word).
  Test = flags resolve as "unfed instances" (fine) vs "genuinely-absent sense" (too thin). Data
  points so far: G80/καρδία/πολύς flags all unfed; **G39's 7-flag rate = the spread under-sampling
  dense Numbers/Leviticus cultic vocabulary** (senses still fed-grounded → no nudge).
- Thin-sense accumulation across the batch (advisory).
- Sense-count / consistency variance across the batch.
- The 2-vs-3 fold-to-range strain (πολύς): if the retro rules multi-verse flickers ship as standing
  senses, it revisits G80's Psa 35:14 verdict (asymmetry: 1 verse vs a trio).
- The parked mechanism decision (higher-cap vs steer vs structure-hint), if the trigger trips.
- **Gloss_notes assertion-verification (NEW, οὐρανός 2026-07-07).** New defect class: gloss_notes can make
  plausible-but-false factual claims about the translation (the citation gate checks refs, not assertions).
  Standing manual check adopted (spot-verify translation-practice claims before ship); mechanizable
  position-check probe is a retro candidate. Full record: `AUDIT_lexica_rollout.md` apparatus-findings block.
- **Substitution-probe (NEW).** Bare headword-substitution with no signature collocate (Luk 15:18 "sinned
  against heaven") is invisible to reviewer/gates/collocations. "Kingdom of heaven" is NOT blind (βασιλεία
  collocate catches it). Minor; decide if a probe is worth building across the whole rollout.
- **Standing rule banked (not a retro question, already in force):** unfed claims are verified against the
  fed list, never inferred from draw silence (absorption vs absence look identical from draw output).

## KEY FILES
- `scripts/build_lexica_def.py` (engine; `--from-draw`, `--dry-run --force`, cap logic)
- `scripts/lexica_agreement.py` (reviewer; `--runs N`)
- `scripts/rank_lexica_candidates.py` (candidate list; `--skip-built`, OBL/STRC/FUNC flags)
- `scripts/check_draw_citations.py` (prose-fix sweep — run after any Tier B corpus prose fix)
- `contested_register.py` (fork words — excluded from rollout) · `scripts/build_word_gloss.py`
  (header gloss OVERRIDES) · `AUDIT_lexica_rollout.md` (the authority) · `docs/claude/ai.md`
  (the Tier B prose-fix → draw-sweep standing rule) · `ENGINE_LESSONS.md` (design-level v2 backlog —
  one line per lesson, grows by habit; distinct from the audit doc's per-word saga)
- **Locking tests (run under pytest or as plain scripts; both in CI + pre-commit):**
  `tests/test_lexica_agreement_parse.py` (both parser-drift fixes) · `tests/test_lexica_glossset_fold.py`
  (case-fold). Add new lexica tests to BOTH the CI list (`.github/workflows/ci.yml`) and the hook
  (`scripts/githooks/pre-commit`).
