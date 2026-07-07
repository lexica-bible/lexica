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
  see the two V6 watches under ENGINE STATE (over-trigger, philosophize).**
- **V7 PILE (prompt-wording candidates, banked 2026-07-07 S3 — next bump, own checkpoint; NONE block V6).**
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
  3. **Doubled vocabulary bar.** Term-of-art line + freight line now govern headline word choice with two
     tests; agree so far, but two tests on one behavior = an over-trigger path (stricter wins by default). Fix:
     subordinate term-of-art into the freight line as an example clause — one test. **WATCH LINK:** if V6 watch
     (i) freight-paranoia fires, the doubled bar is a suspect alongside the new line.
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
- **RETRO PILE (decide with full-batch evidence):** substitution probe (bare-headword-substitution blind
  spot, ENGINE_LESSONS #4) · pre-V5 triage + post-batch redraw phase · the existing fed-40 / reviewer-tier
  questions below.
- **`ENGINE_LESSONS.md`** (repo root) — v2 design backlog, now **19 lessons** (#17 = fabrication family,
  #18 = translation-freight / the 4th freight axis banked 2026-06-25, #19 = MISSED-collocation is a
  floor-level check), self-guarding (every
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
- **SHIPPED + LIVE (10):** G1096 γίνομαι (session start, from-draw first exercise) · G80 ἀδελφός
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
  standing-rule checks run pre-ship — fed-list + gloss-notes verified; style-watch #3 structural-mislabel banked).
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
- **REMAINING (~9 after ὀφθαλμός):** ὄρος G3735 · ἔτος G2094 · ἄρχων G758 · ἔργον G2041 ·
  ἁμαρτία G266 · ῥῆμα G4487 · δύναμις G1411 · θυγάτηρ G2364 · τόπος G5117. (Full locked-20 list + selection method in
  the audit doc's Batch Two section.)
  - **Loaded-frame watch:** ἁμαρτία / ῥῆμα / δύναμις (audit hardest for a disguised loaded frame).
  - **Tight-agreement test (refined hypothesis):** θυγάτηρ / ὄρος — genuine one-dimension nouns,
    predicted to agree tightly at 3. Data so far: ἔθνος clean-binary → tight; **φωνή clean-multi (3
    distinct jobs) → still tight at 3**; πολύς/καρδία multi-*shallow*-axis → wobble; ὕδωρ stable-3
    but needed `--runs 10` (structure wobbled). Working rule: separability (not job-COUNT) predicts
    tightness — clean-separable jobs agree even at 3, shallow overlapping axes wobble. Confirm on the two.
    Note φωνή also showed the spread axis can surprise (propagation, not the speaker-type axis predicted).

## QUEUED FOR NEXT SESSION (surfaced at this session's close — do before/at ἔθνος)
1. **Double-shelf detector — BUILT + control-fired (2026-07-06). LIVE in the audit path, flag-only.**
   `double_shelved(senses_block)` in `build_lexica_def.py` — a set-intersection over the per-sense verse
   lists `sense_specs()` already carries (same splitter + ref regex + book normalizer as the card), stored in
   `entry["audit"]["double_shelved"]` and printed by `show_entry` beside the dangling/noncanon lines as
   `⚠ double-shelved: 1Jn 2:20 in senses [1, 4]`. **NOT a gate** — double-shelving is sometimes legitimate
   (a bridging verse), so it's a conscious per-word adjudication at the gate, JP rules per instance. Whether
   it hardens to a gate is a batch-retro question on accumulated rare-vs-common data.
   **AUTHORITATIVE CONTROL — DONE + GREEN on PA 2026-07-06.** `--resplit --word G39 --dry-run` fired
   `⚠ double-shelved: 1Jn 2:20 in senses [1, 4]` (the known positive) AND surfaced a second G39 seam,
   `2Ti 1:9 in senses [1, 3]` — both logged, NOT reopens (G39 stays as shipped). Sub-use refs ARE captured
   (sense 4's list picks up 1Jn 2:20 from the sub-use sentence), so the extraction has no sub-use blind spot.
   **NO code fix happened between the no-fire and the green run** (file unchanged since `61740c0`): the
   suspected sub-use-extraction bug was DISPROVEN by a local test on the real G39 text; the PA no-fire was
   just stale code (PA hadn't pulled the detector commit), and the `git pull` is what flipped it silent→firing.
   The detector is LIVE in the per-word audit; **ἔθνος is the first word audited with it live.** Parked-draft
   sweep DONE 2026-07-06: G80 clean, G4183 clean, **G2588 καρδία = two logged seams** (`2Co 2:4` senses [1,2];
   `Joh 12:40` senses [1,4]) — retroactive seam-logs on shipped prose, adjudicate at leisure, NOT reopens.
2. **Word-study card header — GREEK HALF DONE (commit `7bee235`, 2026-07-06), HEBREW HALF QUEUED.** The card's
   hero gloss sourced the top in-verse *rendering* (`abp_glosses[0]`), not `word_gloss`, so hand-widened
   overrides silently reverted there (G39 "holy" vs Library "holy, set apart"). Greek fixed frontend-only:
   `firstGloss` now leads with `shortLemmaGloss(profile.definition)` (word_gloss leads that chain for Greek),
   matching Library for all Greek overrides. **HEBREW still shows the top rendering** — its `profile.definition`
   is the long definition paragraph, NOT `word_gloss`. Fix = a small **API change** (return the Hebrew
   `word_gloss` in its own profile field) + one matching frontend line. **Own checkpoint (API change, not
   frontend-only).** ⚠ The sourcing comment MUST say **Strong's Hebrew** — the table is named `bdb` but holds
   Strong's Hebrew, not real Brown-Driver-Briggs; this is exactly where a future edit would mislabel it.
3. **θεός G2316 sense-1 item "B" — completeness improvement, NOT a correction (own checkpoint, JP's go).**
   Sense 1 shipped grounded (2026-07-06, "worshipped" removed, treatment-verbs all cited). B = add the concrete
   devotional acts προσκυνέω "bow down" / λατρεύω "serve" back into the treatment-list, which need a citation
   first: sense 1's current 40 don't attest either (sample leans commission/covenant/prophecy). Candidate
   **Matt 4:10** (quotes Deut 6:13 — grounds both verbs in one verse); **verify the tag-match gate finds the
   θεός tag in it** before any write, then extend the list to "served, bowed down to, named, invoked in oaths,
   prayed to, and spoken of as acting in history." CONTESTED-card evidence change → own checkpoint, JP's go
   before any write. No urgency; the card is honest as shipped. (Corpus backs it: `coverage_audit` flags
   λατρεύω uncited across 32 θεός verses, PMI 5.31.)

## RETRO LIST (decide with full-batch evidence, not per-word)
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
