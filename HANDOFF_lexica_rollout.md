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
- **GRADUATION RULE (audit-intensity relaxation).** Verbatim: *"Manual audit relaxes when 2–3 consecutive
  words ship clean at attempt 1 with no new defect classes, no new watch entries, and floors in the predicted
  bucket. At that point: spot-audit becomes the default; full manual audit only on flagged words."*
  - **RULING (2026-07-07, pinned so the criterion isn't adjudicated retroactively):** **φωνή does NOT open the
    streak.** Its senses passed clean, but the audit PROCESS required correction — two standing-rule checks
    (fed-list verify, gloss-note spot-verify) were skipped in CC's first verdict and had to be prompted. "Clean
    at attempt 1" means the audit ran clean, not just that the card was right. Streak counter = 0 going into
    ὀφθαλμός.
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

## SESSION-2 CLOSE STATE (2026-07-07) — read this to resume
Batch-2 paused at **9 shipped**; φωνή G5456 carries to next session, floor not yet run.
- **ENGINE STATE — all LIVE:** V5 prompt (Formatting block + term-of-art line) · gloss-set **case-fold**
  (merges "Heaven"/"heaven"-class artifacts) · **both parser tolerances** (per_sense reuses _sense_spans;
  split_definition falls back to header-less bold-numbered senses). Locking tests (CI + pre-commit):
  `tests/test_lexica_agreement_parse.py`, `tests/test_lexica_glossset_fold.py`.
- **ESCALATION COUNTER = 2** (πολύς full cap-out / range-completeness; ἅγιον near-wall / structure, cleared
  attempt 3). A THIRD wall on any binding constraint trips the mechanism decision to JP immediately.
  Mechanism options UNCHANGED: higher-cap draw-until-match · prompt-steer + re-prove · structure-hint channel
  (ENGINE_LESSONS #3 leans toward structure-hint + a convergence detector, but the call is still JP's).
- **STYLE WATCHES (3 open):** #1 slashes — addressed in V4, body-prose scope still MONITORING (not extended);
  #2 term-of-art — addressed in V5, the point-6 audit is live (first catch-and-clear on οὐρανός); #3
  whitespace — V6 line BANKED, byte-explicit: *"each Sub-use begins on its own line, with a blank line
  before it."* Rides free on the next version bump; no bump yet earned.
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
- **`ENGINE_LESSONS.md`** (repo root) — v2 design backlog, now **18 lessons** (#17 = fabrication family,
  #18 = translation-freight / the 4th freight axis, banked 2026-06-25), self-guarding (every
  word-citation verified against the audit doc before commit). Distinct from this handoff + the audit doc;
  read it before any v2 design work, not before resuming the rollout.

## PER-WORD FLOW (the loop)
1. `lexica_agreement.py --word G#### --runs 3` (→ 10 on wobble). Read the STABLE jobs (present in
   ~all draws) + majority-distinct distinctions; wobbles back-check hole-vs-fold.
2. `build_lexica_def.py --dry-run --force --word G####` → draft. Audit vs the four gates + standard
   checks. If it misses the reviewer structure, redraw (cap 3).
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
- **NEXT UP:** ὀφθαλμός G3788 — reviewer floor `--runs 3` first (no verdict banked). Prediction: literal eye
  vs figurative "eye" (sight/perception/attention, "eyes of the LORD"); watch usage-dimensionality axis.
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
