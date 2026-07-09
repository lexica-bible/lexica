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

**Receiving-instance rule (both CC and chat, next session):**
9. A gate that can't be cleared by its attached procedure converts to a logged caveat
   ("accepted on standing evidence, unverified: <item>") — not an indefinite hold. Holds are for
   failed checks, not missing ones.

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

## BATCH-3 SESSION 2 LOG (2026-07-09) — in progress; state per close commit 5188565 + this block.
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

## BATCH-3 SESSION 1 LOG (2026-07-08/09) — shadow calibration opened. Read this + the audit doc's
## batch-3 entries to resume session 2.
**Roster JP-approved: 17 GREEN candidates + 3 seeded RED** (G3900 παράπτωμα · G4061 περιτομή · G4645
σκληρύνω — **all three UNEXERCISED; session 2 must run at least one** to complete the routing-exercise
goal). Words processed 8: **γόνυ p2 (ESCAPE 1) · δίκτυον p1 (count 1) · νίπτω p2 (ESCAPE 2) · ἄκανθα
PARKED · σελήνη p1 (count 2, zero-fire) · κῆπος p1 AMBER · κάλαμος attempt-4 hint + APPLY INCIDENT
(#31) + SPLITTER FIX (af8e296) · δάμαλις first-draw hint (middle-case type specimen).**
**Tally: 7 shipped / 2 escapes / 1 parked / count 2/15 / streak 0 / 12 remaining.** Both escapes were
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
4. **Batch-3 = Phase 2 shadow calibration** — **IN PROGRESS; session 1 CLOSED 2026-07-09** (roster approved
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
