# ENGINE_LESSONS.md — what the definition engine v2 should do differently

Design-level lessons only. This file is NOT:
- `AUDIT_lexica_rollout.md` (WHAT happened, per word — the authority on saga detail), or
- the standing rules in `CLAUDE.md` / memory (HOW we operate the current engine).

It is the **v2 design backlog**: one entry per lesson, each pointing to its audit-doc entry for the
evidence. It grows by HABIT — add a line the moment a design-level finding is logged, don't batch.
Nothing here is scheduled work; it's the "if we rebuild the engine, change these" list.

**Verification rule (standing):** every line that NAMES A WORD as evidence gets its citation checked
against `AUDIT_lexica_rollout.md` before commit — not just dedupe-checked. The doc outranks recall,
including the author's. This file is written at the abstraction level where conflation happens: on
2026-07-07 alone that guard caught the double-shelf production record and ἅγιον's regime classification
both drifting from the doc.

## Lessons (this batch, 2026-07-06/07)

1. **Truth-gates converge, style-gates fish.** Holes/merges/completeness settle in 1–few draws; "match
   the sense count" and other style properties never settle. → v2 steers STYLE at the prompt layer
   (formatting block), and GATES only truth properties. *(audit: SHIP BAR re-ruled / three-regimes finding
   / STYLE WATCH #1–#3)*

2. **Fabrication was stimulus-driven, not prompt-driven.** The "Heaven" capitalization fabrication survived
   two prompt generations (V4, V5) and died the instant the case-split was removed from the fed evidence.
   → v2: AUDIT THE FED EVIDENCE before tuning prompts; a stimulus you can delete beats a prompt line that
   steers around it. *(audit: GLOSS-SET CASE-FOLD / οὐρανός three-attempt saga)*

3. **Ship draws sample off the reviewer's modal carve — and draw-until-match is REGIME-dependent.** ὕδωρ:
   the target shape was ~70% of reviewer draws, yet the ship path missed it twice before hitting on attempt
   3 → ship-path DRAW-UNTIL-MATCH against the banked verdict works when the target is RARE-BUT-PRESENT. It
   FAILS when the shape is near-ABSENT (πολύς: the 2-sense-with-full-range draft barely exists — capped and
   parked; more pulls can't summon it). The instructive case is the BOUNDARY between the two: ἅγιον's
   structure wouldn't stay distinct for two pulls (attempts 1 & 2 collapsed / merged — looked near-absent)
   yet CLEARED on pull 3 — rare-but-present that read as absent in the moment. → v2 needs BOTH a
   structure-hint channel (pass the reviewer's stable-jobs list as draw context) AND a convergence detector,
   precisely because ἅγιον is the case where mid-pull you can't tell the πολύς regime (escalate) from the
   ὕδωρ regime (keep pulling). (The structure-hint channel is one of the three armed escalation-mechanism
   options — this partially pre-decides that choice for v2.) *(audit: G5204 ὕδωρ + G39 ἅγιον near-wall +
   G4183 πολύς + escalation trigger option space)*

4. **Substitution blind spot.** A headword standing in for another referent is invisible to reviewer, gates,
   AND collocation flags UNLESS a signature collocate exists (βασιλεία caught "kingdom of heaven"; bare
   "sinned against heaven", Luk 15:18-class, is uncovered). → v2 wants a substitution probe for the
   no-collocate case. *(audit: APPARATUS FINDINGS — blind-spot refined)*

5. **Usage-dimensionality, not referent-concreteness, predicts wobble.** A concrete referent can wobble
   (καρδία, ὕδωρ) if its USES are multi-facet; a word wobbles by how many shallow analytical cuts its usage
   offers. → v2 could pre-classify words by usage-dimensionality and scale reviewer-floor depth accordingly
   (ties to lesson 8). *(audit: Framing correction / G5204 hypothesis result)*

6. **Reuse rule, both directions.** A private copy of the sense-splitter broke the reviewer (per_sense used
   its own bold-only regex); single-source `gloss_set` made the case-fold a one-place atomic fix. → v2 has
   ONE splitter, ONE gloss_set — no second copies of scan/transform logic, ever. *(audit: REVIEWER PARSER
   DRIFT FIX + SECOND PARSER FIX + GLOSS-SET CASE-FOLD)*

7. **Gloss_notes make unverified factual claims about the corpus.** The citation gate checks REFERENCES, not
   ASSERTIONS (capitalization practice, translation behavior). → v2 wants a position/text verification step
   for corpus-practice claims — mechanizable for the capitalization case (verse text is in the DB,
   sentence-initial is testable). *(audit: APPARATUS FINDINGS — unverifiable-assertion defect class)*
   - **UPDATE (τόπος 2026-07-08): verifying a form-claim is PER-ROW, not per-word — the corpus form-fields are
     SPARSE.** τόπος's gloss_note asserted the Greek inflected form ("uses τόπον") for three verses; a per-row
     check found 2Sa 19:39 carries BLANK lemma AND morph — that row attests only the Strong's number. 68/538 =
     12.6% of G5117 rows are blank-lemma — **scope is this WORD only; corpus-wide rate + OT/NT split UNMEASURED**
     (the G2041 count is the next data point). Read as the systematic OT form-field gap, NOT a mistag, NOT the
     dotted no-entry class. So a "the Greek uses [form]" claim can't be verified once for the word — each CITED row needs its own
     tag check, and the safe fallback when a row is blank is the lemma (backed for every row via the Strong's→lemma
     mapping). Sharpens #7's verification step with the sparsity reason; sibling of #22 (the gap is a corpus-side
     reality the claim must survive). *(audit: G5117 τόπος per-row-morph fix + 68/538 blank-lemma count, 2026-07-08)*

8. **Fixed fed-40 under-samples SYSTEMATICALLY on high-occurrence / multi-domain words** (μέγας's dense
   Levitical collocations, οὐρανός's metonym verses unfed entirely, ὕδωρ's purity/river/sea neighbors), and
   presumably wastes sample on redundancy for flat-usage words. → v2 candidate: dynamic fed-count scaled by
   occurrence count and/or usage-dimensionality (lesson 5), possibly collocation-aware sampling that reserves
   slots for high-PMI neighbor contexts so signature uses can't be unfed by chance. **Evidence: every
   collocation flag this batch was a fed-sampling miss — zero were missing senses.** The current design
   survives its under-sampling only because the eyeball-and-resolve step catches it; v2 turns that manual
   resolution into sampling policy. **Strongest instance is θεός** — the fed 40 failed to attest
   προσκυνέω / λατρεύω though serving/bowing are among the most attested θεός treatments corpus-wide
   (λατρεύω uncited across 32 θεός verses, PMI 5.31); the miss reached DESCRIPTIVE PROSE (sense 1 read
   complete while under-describing the referent), not just collocation flags — which upgrades 8's severity
   and the case for collocation-aware slot reservation. *(audit: fed-40 retro thread + μέγας/G39/οὐρανός/
   ὕδωρ flag entries + θεός item B)*

## Carried from v1 (foundational — proven, keep as v2 invariants)

9. **The deterministic/model boundary holds where it's tested.** Every correctness fix that worked is
   DETERMINISTIC (book table, chapter-strip, soft set, case-fold, exact lookup); everything model-side stays
   ADVISORY. → v2 keeps correctness gates deterministic and the model's output advisory-until-gated. *(audit:
   Batch-One process lesson 3)*

10. **Review-what-ships: reviewed prose must be byte-identical to shipped prose.** The draw cache moves
    toward this (apply reads on-disk bytes, no fresh model call) but does NOT fully guarantee it — see 15
    (the key pins the input, not the prose). → v2 keeps the reviewed artifact and the shipped artifact the
    same object, content-addressed. *(audit: Batch-two prep #1 — draw cache; tightened by 15)*

## Added by session-1 mining (2026-07-07)

11. **Double-shelf detection belongs in the engine natively.** v1 had no check for a verse cited under more
    than one sense in the SAME draft — it shipped (G39 1Jn 2:20 + 2Ti 1:9; καρδία 2Co 2:4 + Joh 12:40),
    caught only by live-card eyeballing. A set-intersection over the per-sense ref lists finds it free;
    sub-uses are its natural habitat. → v2 runs it EVERY draw, **FLAG-ONLY (not a gate)**: bridging verses
    are legitimately double-shelved (presence-vs-significance; human rules per instance), and hardening to a
    gate is a data-collection question, not a design default. **Production record since 2026-07-06: 0 fires
    ever ruled noise.** Ship-time live fires ruled keep-both bridges on 3 SHIPPED cards (ἔθνος Eph 2:11,
    μέγας 2Ch 17:12, ἱερεύς Gen 14:18); the ὕδωρ 2Pe 3:5 and οὐρανός Joh 1:32 fires landed on REJECTED
    drafts (moot — the shipped versions fired clean); G39/καρδία were retroactive logs on pre-detector ships.
    Flag-only design validated in production. **UPDATE (ὄρος 2026-07-07): first fire to drive a REJECT, not a
    keep-both bridge.** ὄρος card draw-1 double-shelved Exo 3:1/Neh 9:13/Num 3:1 across a 2-sense "encounter-site"
    split; rejected at the card gate. The discriminator between bridge (keep) and over-split (reject) is the FLOOR:
    the floor had certified that second sense UNstable (the two 2-sense draws disagreed on what it was), so the
    double-shelf confirmed the split wasn't real. Flag-only still holds — the flag doesn't auto-reject; it's read
    AGAINST the floor's stability verdict. → v2 pairs a double-shelf fire with the floor result: fire + floor-stable
    = bridge; fire + floor-unstable = over-split reject. *(audit: detector shipped commit 61740c0; seam register
    1–4; G3735 ὄρος draw-1 reject)*
    - **UPDATE (ὀφθαλμός requeue 2026-07-08): NEW ARTIFACT CLASS — disclaimer-as-cite.** Prose that
      cross-references a verse while pointing AWAY from its own shelf ("Eze 1:18 handled under Sense 1") counts
      as a citation to the ref scanner, so the double-shelf detector fires on a shelf the card explicitly
      declines. Adjudicated noise at the gate (JP). Sibling of the quoted-gloss lint artifact (#24 update) and
      the prose-mention dangling class — the detector ticket family grows: ref-scanners need to distinguish
      citing from mentioning. *(audit: G3788 requeue entry, 2026-07-08)*

12. **Sense-prose action verbs are unverified corpus claims — lesson 7, extended past gloss_notes.** θεός
    sense 1 opened "worshipped as creator" with NO bow/serve verse in the fed 40; the citation gate checks
    REFERENCES, not whether a sense's descriptive VERBS are attested by its own cited verses. Loaded
    abstractions ("worshipped") compress concrete attested acts (προσκυνέω bow, λατρεύω serve) the Greek
    gesture-words don't carry. → v2 applies grounding verification to sense-prose action verbs, not just
    gloss_notes corpus-practice claims. **Mechanization caveat:** harder than the capitalization case —
    "worshipped" vs bow/serve needs semantic matching, not position-checking; realistic v2 form is "FLAG
    loaded abstractions for manual grounding-check," not full automation. *(audit: θεός G2316 sense-1
    decompression, 2026-07-06)*

13. **Fork-companion frame leak — neutrality is BOTH-ways.** A sense adjacent to a contested fork-word can
    leak the fork's framing even though the headword isn't forked (holy-spirit under ἅγιον). Rejecting one
    frame is itself frame-taking — the anti-personhood descriptor ("power / agent / medium") picks the OTHER
    side of the same contest. → v2's neutrality check for fork-adjacent senses is BOTH-ways; the neutral
    ceiling is grammatical characterization ("qualifying πνεῦμα as a compound expression"), NOT an
    ontology-lite descriptor. Corroboration: the both-ways register held UNPROMPTED across ἱερεύς's
    Melchizedek cluster (10 reviewer draws + ship draft) and ὕδωρ's baptismal / 1Jn 5:6 cluster — the
    discipline generalizes to fork-adjacent territory without CONTESTED machinery. *(audit: G39 spirit-frame
    both-ways bar; ἱερεύς + ὕδωρ register checks 2026-07-07)*

14. **Range-completeness is its own binding wall — folding isn't free.** Granularity-as-drawn legitimizes
    folds only because folded facets stay VISIBLE, but visibility-after-folding is EMERGENT, not generated.
    πολύς proved it doesn't emerge reliably — the stable 2-sense structure exists, but folded facets
    (comparative / adverbial / temporal) drop silently from the range across single drafts. → v2 treats
    carrying folded facets into the range as an EXPLICIT generation target, not an emergent property.
    *(audit: G4183 πολύς PARKED — range-completeness finding)*

15. **The reviewed-draft cache keys by INPUT; outputs collide.** The key pins the fed sample, not the prose
    — all 13 of G80's draws shared one key, so shipped bytes were "whatever was last on disk," not provably
    the reviewed artifact. It worked, but it's a foot-gun the validity signature only mitigates. → v2
    CONTENT-ADDRESSES the reviewed draft by its prose, so reviewed and shipped are unambiguously the same
    object (tightens 10). *(audit: G80 saga — key-pins-input note)*

16. **A completeness detector must scan the WHOLE prose.** Completeness is satisfied by inline verse-level
    naming (καρδία's relational-presence facet lived as an inline gloss inside sense 1 at 1Th 2:17 —
    correctly ruled visible; the gate-3 inline precedent). → any v2 completeness detector reads the whole
    prose for facet presence, not just sense headers + the range slot — else it regresses below v1's own
    jurisprudence and false-fails legitimate cards. *(audit: G2588 gate-3 inline precedent)*

## Added by session-3 (2026-07-07)

17. **Fabrication family — one signature across three instances: confident invented rationale for an
    unobserved fact.** (a) **Capitalization fabrication** (root-caused on οὐρανός) — gloss_notes invented an
    "editorial capitalization of Heaven" corpus rationale; premise false, fixed by the gloss-set case-fold.
    (b) **Unfed-claim risk** — a citation/claim inferred from draw silence rather than verified against the
    fed list; closed by the session-2 fed-list verification rule. (c) **WSGI-key guess** (session 3) — an
    infrastructure mechanism asserted from plausibility, the key's location invented — AND FUNCTIONAL, which
    is the dangerous subclass: plausible-and-working fabrications pass silently and accrete into convention;
    closed by the environment-verification sibling rule. → v2's countermeasure is FAMILY-LEVEL (a single
    "is this rationale observed or invented?" gate on any asserted rationale — corpus, citation, or
    infrastructure), not three per-instance patches; target for the batch-2-close optimization pass.
    *(audit: G3772 attempt-1/2 capitalization fabrication + case-fold root-fix; fed-list standing rule;
    session-3 handoff standing-rule #4 / preamble `source .env` correction)*
    - **UPDATE (ἔτος 2026-07-08): instance (d) — fabrication anchored on a FORMULA-LOOKALIKE.** 1Sa 17:12's
      "in days of Saul" shares the surface shape of a regnal-dating formula ("fifteenth year of Tiberius"), so
      the draw filed an age idiom as calendrical across three draws and twice invented a rationale for the shelf
      ("fourth year of Levi's service range" at Num 4:3 — no fourth year in the verse; "a year of active service"
      at 1Sa 17:12). Same signature (confident invented rationale for an unobserved fact), new anchor: a
      construction that LOOKS like a known formula recruits the formula's category, then the rationale is invented
      to fit the mis-filing. → the family gate should treat formula-shaped contexts as a trigger for
      verify-the-verse, not as classification evidence. *(audit: G2094 ἔτος pulls 1–2, 2026-07-08)*
    - **UPDATE (ἄρχων 2026-07-08): instance (e) — HARMONIZING a verse into its sense's frame.** Rev 1:5
      ("ruler of the kings of the earth" — human kings) filed under the superhuman-powers sense, and the prose
      invented the bridge: "places him at the apex of all such powers" — an assertion about dominion over the
      sense's other members (air/demons/eon powers) that the cited verse does not make. Same signature (invented
      rationale for an unobserved fact), same direction as (d): context-shape overriding verse content — the
      sense's frame recruited the verse, then the rationale was written to justify the recruitment. Fork-adjacent
      (χριστός contested), which is where a harmonizing assertion is most dangerous. *(audit: G758 ἄρχων pull 1,
      2026-07-08)*

18. **Translation-freight — the FOURTH freight axis** (alongside referent-freight, attribute-freight,
    frame-leak). The English/Latin definitional vocabulary imports its OWN conceptual carving onto the Greek —
    "the definition asserts something the Greek text doesn't," entering through a different door than the other
    three. **The test is NOT "is this word loaded" (everything is) — it's "does this word's English meaning
    track the Greek, or override it."** Boundary reasoning: zero-freight English doesn't exist, so the standard
    is narrower — *avoid English words whose modern meaning has drifted from the Greek they translate, or that
    import a whole conceptual domain the Greek doesn't carve.* **The fix is to describe the Greek's own carving,
    not to hunt for a pure English word — because the pure English word doesn't exist.** Flagship failure:
    **"moral"** fails it hard — a Latin category (moralis, Cicero's coinage translating ἠθικός imperfectly) with
    no Greek behind it; Greek carves that space with δίκαιος / ὅσιος / ἀγαθός, none mapping to English "moral."
    Also failing: **"worship"** (a post-Christian devotional bundle laid over concrete prostration/service acts
    — the same case already logged concretely at #12's προσκυνέω/λατρεύω decomposition). → v2's freight check is
    FOUR-axis, and translation-freight is caught by "describe the carving, don't name a pure word." Generalizes
    #12 (action-verb grounding) and is a sibling of #13 (frame-leak) and #17 (fabrication family — invented
    carving is invented rationale through the vocabulary door). *(provenance: banked 2026-06-25, "Fixing
    VERSE_PROMPT sense-count instability" session; never promoted to durable docs until now — its own case study
    in why the doc outranks recall. Surfaced batch-2 session-3 when ὀφθαλμός `--runs 3` draw 3 framed a job as
    "moral character"; verified against that floor output in-transcript.)*

19. **The MISSED-collocation warning is a FLOOR-level check, not a ship-time nicety.** A floor run on a fed
    sample that never showed the reviewer a high-PMI collocation certifies the stability of the WRONG inventory
    — the reviewer can only be stable about senses it was shown. ὀφθαλμός `--runs 10` was rock-stable on a
    3-job core, yet the `⚠ collocation MISSED` warnings (φείδομαι pity-family, πονηρός envy-family — both
    0-fed) pointed at a whole disposition region 13 draws structurally could not see; the draft then drew that
    region thin under the physical sense and reached for the Latin category ("moral") to name it — #18 and the
    fed-gap turned out to be one defect from two sides. → the eyeball of MISSED warnings moves BEFORE floor
    adjudication (FLOW step 1.5): for each, decide unfed-instance-of-existing-sense (fine) vs unfed-idiom/job
    (inventory gapped → force the verses into the redraw sample, select_spread option (a)). v2 candidate: the
    collocation-aware feed quota (option (b), #8's slot-reservation) that would close the gap at generation
    instead of by manual eyeball. *(audit: G3788 ὀφθαλμός floor + rejected V5 draft, 2026-07-07; select_spread
    forcing logged on the draw record)*
    - **UPDATE (θυγάτηρ 2026-07-07): a MISSED collocation can NARROW a shipped sense, not only HIDE a job —
      a second failure mode.** θυγάτηρ's μήτηρ (18v, 0-fed maternal-naming genealogy) hid no sense (offspring
      shipped fine), but every fed genealogical verse was paternal, so attempt-1's sense-1 headline came out
      "in relation to her biological or legal FATHER." The warning was flagging a definitional NARROWING of a
      PRESENT sense. → step-1.5's eyeball must ask BOTH questions per warning: unfed job? OR unfed contexts
      that would BROADEN the shipped sense's definition? Same shape as #18 freight leaking where the evidence
      would have blocked it. *(audit: G2364 θυγάτηρ step-1.5 narrowing)*

20. **A prompt rule DAMPENS a prior, it doesn't DELETE it — and a multi-constraint word can satisfy one
    constraint OR another per draw but not always both at once (oscillation). The fix is a draw-CONTEXT hint of
    certified structure, not more prompt or more pulls.** ὀφθαλμός under V6: attempt-2 held the structure
    (disposition its own sense) but kept "moral" (freight prior dampened, not deleted — same "verse-grounding
    swaps whose freight it doesn't remove" shape as memory `project_lexica_dictionary`); attempt-3 dropped
    "moral" but regressed the structure (buried the stable regard job under physical). Three pulls, never both
    clean → cap-out. This is NOT πολύς-type target-nonexistence (both good-structure AND freight-clean were each
    demonstrably drawable) — it's **oscillation across two binding constraints**, a distinct wall shape. The
    ruled mechanism (`--structure-hint`, escalation resolution 2026-07-07) beat the alternatives BY SHAPE: the
    prompt already worked (attempt-3 proved the freight line), so prompt-steer was the wrong tool; higher-cap
    draw-until-match just re-rolls the same oscillation; passing the reviewer's OWN certified stable-jobs list as
    draw context steers to ground truth (not a preferred outcome) and pins the axis that keeps slipping, frozen
    prompt untouched. First hinted draw held structure + freight together on the first try — mechanism validated.
    → v2: (a) detect oscillation (constraint A-clean ⊕ B-clean alternating across draws) as its own wall class,
    distinct from range-completeness/target-nonexistence; (b) the structure-hint (certified-structure-as-context)
    is the standing tool for it; (c) a convergence/"held both" detector could auto-flag when a hinted draw clears
    all axes at once. *(audit: G3788 ὀφθαλμός V6 attempts 2/3 cap-out + structure-hint first draw, 2026-07-07;
    mechanism commit 95b4a16; TRIGGER STATUS fired+resolved)*
    - **UPDATE (ὀφθαλμός session 4, 2026-07-07): the mechanism has a demonstrated CEILING — it names JOBS,
      it cannot dictate a folded SUB-USE's parent.** The hinted draw held structure+freight, but the
      disposition sub-use kept filing under physical instead of its certified home (regard); and the killer —
      all six regard exemplars were ALREADY in the fed sample, so the anchor-verse lever was a NO-OP: maximal
      hint + full exemplar coverage still mis-filed it, and no in-bounds move remained. → oscillation of
      DISTINCT-JOB structure is the mechanism's job; SUB-USE PLACEMENT is a separate wall it can't reach —
      banked to the V7 restructure, NOT a per-word draw fight. Tempers this lesson's "mechanism validated":
      validated for its class, bounded past it. *(audit: G3788 ὀφθαλμός SESSION-4 OUTCOME — anchor lever dead)*
    - **UPDATE (Phase-1 close, 2026-07-08): mechanism 5-for-5 on structure; the V7 placement rule DAMPENED the
      sub-use wall (this lesson's own dampen-not-delete shape, one level up).** ὀφθαλμός's V7 floor put the
      disposition cluster at a dead 5/5 physical-vs-not (V6: mis-filed on every push) — the prompt rule halved
      the prior, didn't delete it; JP ruled 7a either-home-legal on the fresh floor and the hint SELECTED a home
      (logged as a stability pick, not a placement rule). All three Phase-1 words shipped via hint at attempt 4,
      first hinted try each. Operational refinement: PRE-CLEAR adjudicated keep-both bridges in the hint's exit
      terms, so a ruled bridge recurring can't force a park (the ὀφθαλμός pull-2 lesson); and a single ruled
      misplacement = redraw, since no legal edit path touches citation lists. *(audit: G3788/G266/G5547 requeue
      entries, 2026-07-08)*

## Added by the ὄρος session (2026-07-07)

21. **A gate that reads a LENGTH is not reading the TEXT.** The four-gate audited the structured fields
    (headlines / range / citations / coverage) but the `senses_block` prose BODY was shown only as its char count
    ("1360 chars, kept verbatim") — never printed, never read. Four defects shipped inside that unread prose: a
    leaked bold title + `---`, a "Giboa"→Gilboa typo, a "Sub-uses include:" stutter, a malformed citations-first
    Zion sub-use. "Kept verbatim" names the field MOST in need of reading — verbatim = the model's raw output
    reaches the reader unmediated. → v2: the gate PRINTS every verbatim-kept field in full and requires an explicit
    proofread pass; a length / "kept verbatim" note is BANNED as evidence of correctness. Sibling rule for display:
    verify the RENDERED card by screenshot, never pasted terminal text (paste flattens layout and invents phantom
    run-togethers — 2 phantom "renderer bugs" this session that the bytes disproved). Mechanized now
    (`show_entry` prints the prose, commit `9a1dca9`). *(audit: G3735 ὄρος post-ship prose defect + PROOFREAD GATE)*
    - **UPDATE (θυγάτηρ 2026-07-07): fixing ONE field did not close the class.** #21 printed `senses_block` in
      full, but `gloss_notes` was STILL a 400-char preview (`… ` cutoff) — the identical length-not-text gap in
      a sibling field that ALSO renders to the reader (both bullets screenshot-confirmed on θυγάτηρ's card).
      Closed for gloss_notes too (`be027c1`, full print + its own proofread label). → the lesson sharpens: audit
      EVERY verbatim / reader-facing field for the length-preview gap; a fix on one field is not the class closed.
      *(audit: G2364 θυγάτηρ gloss_notes gate fix be027c1)*
    - **UPDATE (ἁμαρτία 2026-07-08): the class extends to the RENDER layer.** The live G266 card showed literal
      \*asterisks\* in RANGE — `range` (and the latent, always-empty `coverage`) bypassed `renderInlineMd` while
      senses/gloss notes went through it. The bytes were right; the render wasn't — the SCREENSHOT half of this
      lesson caught it, the terminal proofread could not. Both fields fixed in one pass (`80b87cd`; fix the
      pattern, not the instance — the empty coverage field was a latent copy that the first non-empty card would
      have surfaced silently). → per-field audits must cover every layer a field passes through: stored bytes,
      assembled prose, AND rendered output. *(audit: G266 ἁμαρτία render fix, 2026-07-08)*
    - **UPDATE (κάλαμος 2026-07-09): trace a format defect to its LAYER before fixing it.** The "Calamus*"
      broken italic looked like draw behavior (3-for-3 recurrence → a V8 prompt-fix hypothesis was half-banked)
      and the ruled remedy was a fix_lexica_raw surgical edit — but a one-command read of the cached draw showed
      the RAW was correctly paired (*Calamus*); the bite was the SPLITTER's greedy label-eater (`[\s:*]*`
      swallowing a body-opening italic's asterisk), a deterministic assembly bug — which is WHY it recurred
      3-for-3 (same input shape, same clip) and 0-for-5 on words whose notes didn't open italic. The surgical
      fix would have edited the WRONG LAYER (corrupting a correct raw to compensate downstream); the prompt fix
      would have steered the model against a bug it didn't cause. Fixed at the true layer (bounded eater +
      locking test with a control assertion, `af8e296`); one bug had produced SEVEN downstream lint artifacts
      across three pulls. → before fixing any format/render defect, read the artifact at each layer boundary
      (raw → assembled → rendered) and fix where the bytes first go wrong. *(audit: G2563 splitter fix,
      2026-07-09)*

22. **A spurious sense can be a FEED defect, not a DRAW defect — and the poison can enter UPSTREAM of the sampler,
    from a corpus side-table the engine doesn't own.** ὄρος grew a "boundary" sense not because the prompt or draw
    failed but because three ὅρος "boundary" verses (Strong's-dotted G3735.1) leaked into the ὄρος "mountain"
    evidence — a near-homograph the `dotted_lexicon` hold-out list had DROPPED (its "same word as base?" test folded
    away breathing + accent, so ὄρος/ὅρος read as identical). Extends lesson 2 (audit the fed evidence before tuning
    prompts) with a NEW source class: the contamination came from a corpus tagging / side-table gap entirely OUTSIDE
    the draw path — invisible to prompt, gate, and reviewer, and un-fixable by any amount of re-drawing. → v2: when a
    bad sense appears, check FEED INTEGRITY first (is every fed verse actually this lemma?) before re-prompting or
    re-drawing; the floor's provenance is only as clean as the feed, and feed cleanliness rests on corpus-side
    invariants (here: every dotted number that is a DIFFERENT word must be in the hold-out list). *(audit: G3735 ὄρος
    dotted-lexicon fold gap + fold fix `2ff5f7d`)*

## Added by the ἄρχων session (2026-07-08)

24. **Fabrication rate tracks referent LOADEDNESS.** ἄρχων, 3-for-3: every invented assertion across three pulls
    sat on a theologically loaded referent — Christ (Rev 1:5 "apex of all such powers") or Molech (Lev 20:2–3
    "receiving children by fire"; "worshipped with child sacrifice") — while the card's bulk (tribal heads,
    chariot commanders, councils: ~30 verses) drew invented prose ZERO times in the same pulls. The model has
    rich extra-corpus tradition about loaded referents and none about chariot officers; where tradition exists,
    it leaks into definitional prose as confident detail the cited verse doesn't carry. Corroborated by ἔτος
    (the loaded-free word's fabrications were formula-lookalikes, not tradition-imports — different anchor, same
    family). → v2: scale verification intensity by referent loadedness — any sense/note prose touching a named
    deity, Christ, the spirit, or a doctrinally contested figure gets automatic verse-text verification of every
    descriptive claim BEFORE gate time, not just when an auditor smells it. Sibling of #17 (this is WHERE the
    family fires most), #13 (fork-adjacency predicts frame-leak; loadedness predicts fabrication), #18 (the
    tradition arrives dressed as vocabulary there, as fact here). Direct input to the loaded-frame three
    (ἁμαρτία / ῥῆμα / δύναμις — the audit-hardest words are exactly the highest-loadedness ones). *(audit:
    G758 ἄρχων cap-out saga, 2026-07-08)*
    - **UPDATE (ἁμαρτία 2026-07-08): on a maximally loaded word, fabrication and mis-shelving MERGE into one
      defect class — invented theology drives the CARVE.** Three unhinted pulls, three different boundary
      inventions (cultic-peer promotion, condition-sense annexing four majority-act verses, a 0/10 sense
      resurrected), each verse arriving with a freshly minted condition-theology micro-reading ("medium or
      atmosphere of a prior existence") the verse text doesn't carry — prose invention recruiting verses to
      shelves, not decorating placements. The structure-hint fixed the carve (its anti-annexation direction,
      first test, worked) but the word STILL parked on a meta-field side-take — vigilance-intensity scaling
      alone doesn't close this; the carve itself needs the #24 check. Also NEW SUBCLASS + machine-check
      candidate: **gloss-note fabrication about the translation, self-refuting within the card** (claimed the
      2Co 5:21 rendering was "sin"; the card's own senses_block quoted ABP's actual "sin offering" two fields
      up; twin: οὐρανός capitalization). → v2: lint gloss-note rendering-claims against the card's own quoted
      verse text — no external lookup needed, two corpus instances. *(audit: G266 ἁμαρτία PARKED dossier,
      2026-07-08)*
      - **UPDATE (ἁμαρτία requeue SHIP, 2026-07-08): the machine-check candidate has a demonstrated parse-shape
        blind spot — rendering-claims in RUNNING PROSE.** Requeue pull 2 fabricated the exact claim this check
        exists for (ABP renders bare "sin" at 2Co 5:21 — corpus prints "sin offering") and the lint did NOT fire:
        the claim lived in flowing sense-prose, outside the quoted-gloss-plus-ref bullet shape the lint parses —
        while 12 artifact fires (the known quote-mark bug) lit up pull 1's true statements. The one real
        fabrication was machine-invisible; the noise was machine-loud. → the lint needs a prose-form claim parser,
        not just the bullet parser; sibling of #28 (a detector that can't read the claim's format isn't checking
        it). *(audit: G266 requeue entry, pulls 1–2, 2026-07-08)*
    - **REFINEMENT (ῥῆμα 2026-07-08, the controlled comparison): fabrication tracks CONTESTED referents, not
      loaded ones.** ῥῆμα's divine-word cluster (Mat 4:4, Eph 6:17, Heb 1:3, 1Pe 1:25) drew quote-only prose
      at pull 1 and the λόγος-distinction trap went untaken — same engine, same session, same loadedness class
      as ἁμαρτία, which parked after four pulls. The variable isn't divine subject matter; it's whether a
      specific verse carries a LIVE scholarly/doctrinal fork the model can confabulate a side of (2Co 5:21:
      anti-offering at pull 3, pro-offering at the hinted draw — both confident, same corpus). → the routing
      rule sharpens: verification intensity scales with CONTESTEDNESS of the cited verses, not the referent's
      loadedness; a fork registry / contested-verse list is the natural v2 carrier. *(audit: G4487 ῥῆμα ship
      vs G266 dossier, 2026-07-08)*

## Added by the δύναμις session (2026-07-08)

25. **A sense's prose can DISCLAIM its own citation — and a wall-prior can be DIRECTIONAL, not oscillating.**
    Two findings from one word. (a) **Hedged citation**: δύναμις pull 2's persons sense kept Neh 9:6 in its list
    while its own prose said the verse "may overlap with senses 1 and 4 without reducing to either" — a citation
    the card won't stand behind, invisible to the citation gate (the ref is real and tagged) and to the freight
    scan (nothing loaded). → v2: a coherence check that flags membership-hedging language inside a sense's own
    prose; operating rule already standing (handoff 7c). (b) **Directional prior**: all three δύναμις pulls
    erred toward FINE-CARVING (stacking the floor's rejected minority splits), unlike ἄρχων's oscillation between
    two constraints — a wall shape the structure-hint would fight by pinning the sense list from above (its
    untested anti-split direction; not needed, pull 3 landed). → v2's wall taxonomy: target-nonexistence (πολύς) ·
    oscillation (ὀφθαλμός, #20) · directional carving prior (δύναμις) — each wants a different lever. *(audit:
    G1411 δύναμις pulls 1–3 + thin-sense amendment, 2026-07-08)*

## Added by the V7 window walk (2026-07-08)

26. **Wording-audit finds are BEHAVIOR HYPOTHESES, not defects, until draws adjudicate them.** The V7 pile's
    six wording items split 4 BUILD / 2 DROP at the walk, and both DROPs were the same shape: a plausible
    audit-time worry (over-trigger path, echo risk) that live draws never once exhibited, where the "fix"
    would have altered a working line (item 3's merge would have opened a real coverage hole — "corporate"
    passes the freight test and fails only term-of-art; item 5's trim risked a load-bearing vivid phrase on
    the batch's strongest output region). The BUILDs that cleared were the ones that CODIFIED observed good
    behavior or removed a literal contradiction. → ruling bar for any prompt-wording find: defensive fixes
    clear when they codify, not when they alter; an alter-fix needs a live draw exhibiting the failure first.
    *(walk record: HANDOFF V7 pile rulings, items 3 + 5 vs 1/2/4/6, 2026-07-08)*

27. **(process) Work items created MID-SESSION don't inherit a tracking slot — the close-out manifest audit
    is the catch-net.** Two list-boundary drops in one session (pile item 11 added mid-walk but never ruled;
    the κύριος exhibit verification announced but never reported), both caught only at the bump-assembly
    manifest review, neither a judgment error. → any mid-session addition (pile item, announced verification,
    rider) gets restated in the close-out manifest before "go". *(walk record 2026-07-08)*

## Added by the χριστός session (2026-07-08, Phase-1 requeue #1)

28. **Comma-shorthand citations are a WHOLE INVISIBLE LAYER, and every ref-reading detector inherits the
    blindness.** The banked rule ("spell Job 1:6; Job 2:1, never 1:6; 2:1") treated shorthand as an authoring
    slip; χριστός showed it's standing V7 draw BEHAVIOR — 4/4 draws emitted "Rom 1:1, 4"-class tails — and the
    blindness COMPOUNDS: the tails escape the citation gate (uncounted, unverified) AND the double-shelf
    detector (draw-1's Act 2:36 double-cite was invisible because one shelf was a comma-tail). A "46/46 pass"
    on a shorthand-heavy card certifies only the spelled-out subset. Per-card closure = hand-verify every tail
    against the corpus (χριστός: 24/24 via one row-values check). → v2/V8: either a prompt line forcing
    spelled-out citations (alters draw behavior — batch-frozen, needs the window) or a scanner that expands
    comma/semicolon tails using the preceding book+chapter (detector-layer, legal any time — the stronger fix,
    since it also retro-covers shipped cards on a resweep). Sibling of #21 (a gate that doesn't read the
    artifact isn't checking it) and of the θυγάτηρ Dan-flag class (the same scanner's false-POSITIVE side:
    prose mentions "Gospel/Acts", "in Leviticus" fire as dangling). *(audit: G5547 χριστός — shorthand blind
    spot + 24-tail hand-verification, 2026-07-08)*

## Added by the ἁμαρτία requeue session (2026-07-08, Phase-1 requeue #2)

29. **V7 cannot reliably DRAW a neutral attribution sentence on a contested verse — the register can be
    contained, not yet generated.** Seven pulls on ἁμαρτία across two sessions (4 parked-session incl. one
    hinted, 3 requeue + one hinted): every 2Co 5:21 treatment either asserted the meaning (pro-offering:
    "explicitly works with / requires / shows / is operative"; anti-offering: "simply sin" + a fabricated
    bare-"sin" rendering claim) or, at best, weakened the assertion — zero produced the dossier's pass-shape
    ("ABP renders with the sacrificial sense, following the LXX חַטָּאת use"). The shipped card's passing
    sentence exists only by DELETION (a ruled swap down to the bare quote, which cannot fail the bar). The
    structure-hint's #20 ceiling confirmed in a second field: it fixed the carve on the first hinted draw both
    times, and governed the register neither time (parked session: side-take in the gloss note; requeue: in
    the sense prose, weakened). Defect-migration trail worth keeping: gloss note → sense prose → weakened →
    deleted — containment (registry routing + pre-registered exits + the deletion remedy) works; only the
    prompt can eliminate. → V8: teach the ATTRIBUTION REGISTER at the prompt layer, with the dossier
    pass-shape as a worked example. Hand-authoring the sentence was proposed and WITHDRAWN (JP): a precedent
    extension decided mid-word on first occurrence is the wrong way in — if V8 fails a fair test, hand-authoring
    returns with evidence and gets written narrow. Sibling of #24 (contested verses are where this fires),
    #20 (the hint's ceiling), #17 (both directions were confident fabrications of the same fact). *(audit:
    G266 ἁμαρτία requeue entry, 2026-07-08)*

## Added by the batch-3 calibration session (2026-07-08)

30. **A ship draw can place verses AGAINST the floor's consensus home, and no machine gate sees it — the
    floor-vs-ship placement diff is mechanically checkable and currently unchecked.** γόνυ G1119, batch-3
    word 1: the floor was rock-stable (3 draws, {2:3}, every partner-group 3/3; Luk 5:8 + 2Ki 1:13 homed
    with the kneeling/prayer cluster in every draw), yet the ship draw invented a sub-use the floor never
    carved ("approach-posture, not necessarily worship") under the PHYSICAL sense and moved those 3/3
    verses onto it — carrying an interpretive frame claim about the gesture toward Jesus (Luk 5:8) the
    text doesn't force. Every machine gate passed (35/35 citations, zero lint fires, zero thin) — the
    defect was visible ONLY by diffing the ship draw's verse placements against the floor's per-verse
    company data, which both exist as structured artifacts at gate time. JP ruled: redraw (misplacement
    against consensus, not an alternate carve), and the miss counts against the calibration N — the
    tiering law's GREEN gate suite has a placement blind spot. → v2/detector ticket (PARKED per session
    rule, log-don't-build): a flag that compares each cited verse's ship-draw shelf against its floor
    majority-partners and fires on a high-support verse landing off its consensus home. Sibling of #11
    (the floor is already the adjudicator for double-shelf fires), #20/#24 (placement + frame arrive
    together on loaded referents). *(audit: G1119 γόνυ batch-3 redraw ruling, 2026-07-08)*
    - **UPDATE (νίπτω G3538, same session): SECOND instance in three words — and this time the invented
      shelf was a top-level SENSE, not a sub-use.** The floor certified 2 senses 3/3 (washing | Job 20:23);
      the ship draw broke a unanimous 3/3 cluster to promote three Psalms verses (26:6, 58:10, 73:13) onto
      an invented "rhetorical hand-washing" sense the floor drew zero times. Ruled misplacement, redraw —
      second ruled escape of batch 3. Two-in-three converts the detector candidate from plausible to
      demonstrated-recurring; contrast case on the record: δίκτυον's fold was LEGAL because every floor
      cluster stayed intact (hierarchy demotion ≠ cluster break — the mechanical check is cluster
      membership, not sense count). Rendering-lint side-note from the same card: 2 of 3 fires were
      face-value matches ("may"="may", "washing"="washing" — the known quote-mark artifact, ticket
      instance count grows), 1 real (Exo 30:18 claimed "washing", corpus "wash" — second genuine live
      fire for the lint). *(audit: G3538 νίπτω batch-3 redraw ruling, 2026-07-08)*
    - **UPDATE (βιβρώσκω G977 count ruling, 2026-07-09): the γόνυ count-against-N precedent explicitly
      extends to POST-PULL PRE-SHIP human catches, not just mid-draw saves.** βιβρώσκω shipped clean-looking
      on plain pull 1, every machine gate green — but the sub-use lead misnamed its own group, caught only
      by human read, fixed by a reword-class swap before ship. JP ruled option (b): the 15-count answers
      "can GREEN ship clean WITHOUT a human in the loop"; a machine-invisible defect a human had to patch
      means the answer for that card was no, wherever in the pipeline the catch lands. Count credit + banking
      the catch as intervention data is double-counting the human out of the ledger — rejected. The swap IS
      logged in the intervention tally as a "gates passed a defect a human caught" data point, tagged to the
      fabrication-check batch-close decision. *(audit: G977 βιβρώσκω entry, count ruled 2026-07-09)*

31. **An UNREVIEWED card reached the live site — the apply path writes on a warning instead of refusing.**
    κάλαμος G2563, batch 3 (2026-07-08): the reviewed draw was hinted; CC's apply command omitted the
    `--structure-hint` flags, so the recomputed input no longer matched the reviewed draw's key (#15's
    key-pins-input foot-gun, now demonstrated on the APPLY side of a hinted word), the tool declared the
    cache "STALE (input moved)", drew FRESH UNREVIEWED prose, and WROTE it — warning three times in output
    that nobody read (the write was already done when the warnings printed). The unreviewed card carried an
    unverified botanical identification (*Acorus calamus*) and within-sense verse duplication, and sat live
    through a render pass. Caught by JP diffing the screenshot against his memory of the reviewed draw —
    the render-pass layer's second save (ἁμαρτία asterisks were the first); it is the last diff against
    the reviewed draw, not cosmetic QA. Chain of controls that existed and weren't engaged: `--require-cache`
    (would have refused), the output's own "using reviewed draw — no model call" line (absent = stop).
    **Ruled procedures (JP, batch-wide, on the record):** (a) every apply runs `--require-cache`; (b) every
    apply output is READ for "using reviewed draw … no model call" BEFORE the render step — an apply
    lacking that line stops the session; (c) a hinted word's apply must repeat the hint flags verbatim.
    → v2: refuse-by-default on any write whose draw is not the reviewed artifact (warning-after-write is
    not a control); content-addressing (#15's fix) makes the class impossible. Siblings: #15 (root), #10
    (review-what-ships), #21 (the render layer as diff). *(audit: G2563 κάλαμος apply incident, 2026-07-08)*

32. **The ship engine SAMPLES the floor's carve distribution; it does not know which carve won — the floor
    computes the mode, the hint transmits it.** κάλαμος: the 10-run showed a real modal carve (2-sense,
    5/10 strict) over six rock-stable clusters, yet three plain ship pulls each landed on a DIFFERENT
    minority grouping from that same distribution (imagery own-shelf 1/10 · imagery split 0/10 · aromatic
    own-shelf 1/10) — zero repeats, no convergence, because plain re-rolls just re-sample. δάμαλις
    confirmed from the other side: a 0-exact-mode floor ({1:3,2:3,3:3,4:1}) went straight to a hinted
    first draw (JP ruling — the mechanism's post-cap-out-only constraint EXTENDED to first-draw use on
    0-exact-mode floors) and shipped clean immediately. → predicts when hints are needed: any word whose
    floor resolves by MAJORITY rather than unanimity is a hint candidate at ship time; v2 could make
    mode-transmission automatic (feed the floor's modal carve as standing draw context, not an escalation
    tool). Sibling of #20 (the hint's origin), #3 (draw-until-match regime-dependence — this names the
    regime variable: mode strength). *(audit: G2563 3-pull whack-a-mole + G1151 first-draw hint,
    2026-07-08/09)*

## Added by batch-3 session 2 (2026-07-09)

33. **The placement check compares against the FLOOR, never against the draft's own justification —
    plausible prose is not floor attestation.** Twice in one session a reject came wrapped in competent
    argument: παράπτωμα pull 1 argued a "dead in transgressions" state sense from real grammar (dative
    plural + stative verb) that the floor drew 0/13; κύων pull 1 argued Isa 56:10's "dumb dogs" onto the
    literal shelf via behavioral grounding ("what an actual dog does") — the mechanism by which EVERY
    animal epithet works, which would empty the epithet sense if it licensed literal filing. The paired
    exhibit: Deu 23:18 was filed three ways across three consecutive κύων pulls (epithet-hedged /
    literal-silent / literal-silent), each fluently argued, from one engine. Also names the trap: a
    pre-registered hotspot passing clean does NOT clear the check — παράπτωμα p1 passed the watched
    Romans-5 bar and broke at the unwatched seam. Full-structure comparison, every verse, every pull.
    *(audit: G3900 p1 + G2965 p1, 2026-07-09)*

34. **Watches catch what we fear; floors find what's there.** συκῆ's armed pre-registration (Mark-11
    judgment freight) ran clean 13/13 draws — while the floor surfaced an unpredicted certified job (the
    vine-and-fig-tree security formula, own shelf 6/10, exact 5-verse membership identical 3×). The
    pre-registration system's blind spot and its value in one word: arms cut against imported carves,
    floors discover attested ones. *(audit: G4808, 2026-07-09)*

35. **Corpus size and referent concreteness are weak predictors of floor stability; figurative-use
    density is the better tell.** βέλος (40 occ, concrete projectile) looked like the board's safest
    GREEN and wobbled at 3 runs; session 2 escalated 4-of-4 words. The tell was visible in the
    occurrence table's book column all along — half the corpus in Psalms/Job poetry. Roster tiering
    should read book distribution, not just frequency. *(audit: G956 + session-2 close, 2026-07-09)*

36. **The fabrication checkpoint is symmetric — verify before CLAIMING fabrication, not just before
    claiming attestation.** Three verse-checks this session: two cleared the ENGINE (Psa 64:7 "arrow of
    infants", Lam 3:12 "stone target" — both ABP's own strange renderings that read like blends or
    inventions). ABP is idiosyncratic enough that reviewer intuition false-positives on it; an unchecked
    fabrication ruling would have rejected grounded prose. Both directions of the check protect the
    card. *(audit: G956 checkpoints, 2026-07-09)*

37. **Per-sense citation tail-lists WITHOUT disjointness enforcement are a double-shelf generator on
    soft-border words.** βέλος, four data points in one word: few tails → 1 double; comprehensive tails
    → 5 doubles (all five smeared verses sat in both senses' parenthetical lists while prose placed them
    once); prose-only cites → 0; hinted disjoint lists → 0. Cross-checked: παράπτωμα + συκῆ shipped
    citing in-prose, zero doubles. Format-level cause, not placement-level. → V8 candidates:
    cite-in-prose-only, or a tail-list disjointness check at the gate. *(audit: G956 pulls 1–3 + hinted,
    2026-07-09)*
    - Related mechanism-gradient finding filed under #32's update (hint compliance vs preference
      strength).

    **#32 UPDATE (session 2): hint compliance is inversely related to the engine's own
    placement-preference strength — measured, 2-for-2 in both directions.** κύων: the hint moved
    everything the engine was indifferent about; the one verse with a consistent directional preference
    (Deu 23:18, literal 2-of-3 plain pulls + the floor's own 4/10 minority) defied the hint twice in the
    identical [1,3] shape → parked (wall one verse wide; the weak-preference verse Isa 56:10 bent).
    βέλος: the pre-named loosest pin (Psa 11:2) had NO consistent preference and did NOT defy — the
    gradient's negative case. Mechanism record after session 2: structure 9-for-9, membership 7-for-9.
    *(audit: G2965 park + G956 hinted pass, 2026-07-09)*

## Added by the splitter-fix session (2026-07-09)

38. **Numbers that cross a checkpoint boundary carry their own accounting IN THE SAME MESSAGE — two
    instances, one session.** (a) The pinned write-list changed size between checkpoints (603→607,
    the screen-unification work) and the delta wasn't relayed with it; the reviewer held the write
    until every moved row was named (+21/−17, reconstructed from committed artifacts — the hold cost
    one round-trip and the reconstruction proved the change was an audit SUCCESS, but the relay gap
    was a real defect). (b) The stated pass criterion said "607 rows" while the script's match line
    prints DEDUPLICATED entries (606 — one verse, Jdg 9:20, carries the same strip twice); benign,
    but the same class: a stated number must match the script's actual printed units, or a real
    off-by-one hides behind an expected one. → When a pinned artifact changes size, the delta
    accounting (which rows, why, both directions) travels in the same message as the new number;
    when stating a pass criterion, quote the script's own output line, not a derived count.
    *(audit: splitter-fix session, Ruling 13 + Flag 4, 2026-07-09)*

39. **A command that crosses the CC→JP boundary is a factual claim — verify it against the script's
    own --help/source BEFORE relay, never write it from recall.** Batch-3 session 4 (2026-07-09,
    session CLOSED FAILED on this): CC handed JP the 10-run floor command with a wrong script name
    (`lexica_def.py` — the TABLE's name — for `build_lexica_def.py`) and a wrong flag (`--strongs`
    for `--word`), composed from memory of prior sessions; it reached JP's terminal and failed
    there ("no such file"). Same session, same class: `--force` went out on a checkpoint-gated
    command with no stated semantics until JP demanded them, and two JP holds were skipped in one
    message and had to be re-demanded. The corrected relay pattern (applied post-catch, keep it):
    run `--help`, quote the flag's own wording in the handoff message, and clear every open hold in
    the same message as the command. Verify-before-claim (CLAUDE.md) already covered this — the
    lesson is that a COMMAND LINE is inside its scope, not just prose claims about code/data.
    Sibling of #38 (checkpoint messages carry their own accounting) and #31 (the apply-side cost
    when flags are wrong). *(audit: G4061 stub entry, failed session 4, 2026-07-09)*

40. **Freight can arrive through sub-use ARCHITECTURE with quotationally innocent wording — and
    the tell is a relocated verse whose prose misdescribes it.** κατανοέω pull 2 built a sub-use
    headlined "the inspection bears a devotional or awe-struck quality" and filed Heb 3:1 on it:
    every sentence read clean, the SHELF was the defect (reverence imported as part of the verb's
    meaning). Both instances that night paired an off-majority placement with a prose claim the
    verse doesn't support (Job 23:15 "contemplating God's face" — no face in the verse; Exo 33:8
    "sustained noticing rather than physical inspection" — people physically watching Moses walk).
    → standing check, in force: any verse placed off its floor-majority home gets its prose claim
    read against the VERSE TEXT first, before the placement is adjudicated. Wording-level freight
    scans (#18, #23) cannot see this vector. *(audit: G2657 pull 2 + hinted draw 1, 2026-07-10)*

41. **The apply ships what the CACHE holds — when the reviewed-draw identity is in any doubt,
    verify the cache by free re-read, never by scrollback reasoning.** A duplicate paste during
    ὑπομονή made it ambiguous whether the cache held reviewed pull 2 or something newer; the
    resolution was NOT reconstructing paste history but reading the cache itself: plain
    `--dry-run` WITHOUT `--force` takes the cache-hit path (build_lexica_def.py:1542) — prints
    "using reviewed draw … no model call", runs the full gate chain, writes nothing, costs
    nothing. Compare its markers (key, char count, headlines, flag set) against the reviewed
    output; match → apply, mismatch → full re-review as a new pull. Sibling of #31 (what
    --require-cache protects) and R3's accounting rule. *(audit: G5281 cache-content verify,
    2026-07-10)*

## Added by the ἔργον session (2026-07-08)

23. **The freight (#18) scan's scope is EVERY definitional field, not just the block the last failure was in.**
    ἔργον had THREE evaluation-freight failures — "assessed as a whole" (sense-1 elaboration), "moral pattern"
    (sub-use), and "morally … significant" (the RANGE) — but the audit (both CC and the reviewer) scoped only the
    `senses_block`, so the range failure shipped and was caught POST-apply on the full-entry proofread. The range is
    a definitional field: it *defines* the shift between senses. → the freight scan must cover EVERY field that
    defines (headlines, senses_block, range) before apply, not just the field the previous word's failure lived in —
    scoping by habit to "where it was last time" is the miss. Stated convention so it doesn't drift: **the range
    inherits its citations from the senses it summarizes** (the range has never carried per-clause refs), so a range
    context-pattern is judged against the senses' grounding, NOT failed for being citationless. Sibling of #21 (a
    gate that reads a length isn't reading the text — here a scan that reads one field isn't auditing the entry).
    Counter-note (the pass-side, held with force): "characterized or judged" STAYS — κατὰ τὰ ἔργα is a
    distributional fact of the corpus; scrubbing it would be over-correction into the opposite freight, sanitizing
    the corpus to protect the lemma. De-freight, don't de-claw. *(audit: G2041 ἔργον — three freight failures, one
    caught post-apply, 2026-07-08)*

## Added at the step-4 rulings close (2026-07-10; JP-adopted, step-4 list item 7)

42. **A derived number is a claim — count the names before banking it, and the rule binds every
    author: CC, reviewer, and relays alike.** Drafted at the batch-3 FINAL-TALLY CORRECTION (a
    "19" that survived four sessions of do-not-re-derive markers because nothing ever counted
    the names behind it); ADOPTED verbatim by JP ruling 2026-07-10. Exhibits at adoption — every
    party caught at least once: (1) CC's propagated tally slip (19 for 18); (2) the outgoing
    reviewer's from-memory root-cause reconstruction (wrong on both session and mechanism while
    the docs held the answer); (3) CC's fixture over-claim ("all 9 migrators silent" for a
    fixture that models 2); (4) the step-4 reviewer's dictated intake line ("18 shipped + 2
    escapes; parks outside intake" — contradicted the ruled record; flagged, banked name-true);
    (5) the availability framing drift (a true fact inflated into an unrequested design mandate,
    ratified by both CC and reviewer across two sessions, corrected against source); (+) the
    same session's relay gap — a bracketed prompt-for-a-ruling nearly banked as the ruling
    itself, held by flag-before-bank enforced against the reviewer. Operating rule: batch-close
    state banks only after a name-count cross-check against the roster; a stated number must
    match its artifact's actual contents; flag-before-bank applies to dictations from ANY party.
    *(audit: FINAL-TALLY CORRECTION + STEP 4 ADDENDUM + partial-return/completion records,
    2026-07-10)*

## Added at the step-5 close (2026-07-10, the G2665 V8 control fire)

43. **Draw stability and prose reliability are different properties — the floor certifies
    SENSE-STRUCTURE, not prose.** The G2665 V8 floor was textbook-clean (10/10 same three-block
    anatomy, all folds, zero holes) and the ship draws still produced two defect-class cards —
    a reader-rendered duplicate ref, then a wrong-metal/wrong-part physical claim ("cast-brass
    bases" where the verse has silver cast for the tips). Both defects lived in the prose layer
    the floor never exercises; #30 and the floor were rightly silent. Corollary (reviewer
    precision ruling, banked): forced redraws are INDEPENDENT — a defect absent from the next
    draw was not "corrected," it just didn't recur; defects are per-draw RATES (both step-5
    classes ran 1-of-3), and a promote decision accepts the rate, mitigated by the gate that
    catches it. *(audit: STEP 5 entry, draws 1–3, 2026-07-10)*

44. **A detector inherits the blindness of the parser it reads through — before trusting a
    silent channel, ask what the channel can SEE.** #30's floor-unseen list printed empty on a
    card that carried three genuinely floor-unseen citations (Lev 4:17, Lev 16:15, Exo 40:21) —
    all shorthand-form ("Lev 4:6, 17"), invisible to `_REF_RE`, so they never entered the
    ship-refs set and the subtraction came up empty. Same mechanism scopes the citation gate's
    "N/N pass" to qualified refs only. Until the #28 expander lands, the manual σελήνη-procedure
    check on shorthand tails is a mandatory gate step (encoded in the CLEAN fire-class
    definition). Sibling of #21/#42: an instrument's output is a claim about what the instrument
    read, not about the artifact. *(audit: STEP 5 entry draw 1 + fire-class definitions,
    2026-07-10)*

## Added at the batch-4 run, session 1 (2026-07-10)

45. **An exclusion built on side-table membership fails OPEN — absence of an entry is not
    absence of a cousin.** Every dotted screen in the pipeline reads `dotted_lexicon`
    membership, so a dotted number with no row (the no-entry class, 86 numbers) leaks its rows
    into the BASE word's evidence feed, floors included — and both CC and the reviewer passed a
    pre-pull calling the leak "bookkeeping" on an untraced claim about engine behavior. The
    floor header (`fed 40` vs the true 38) refuted it. → v2: exclusions on curated lists must
    fail CLOSED for unknown members, or the feed prints which dotted rows it admitted. Until
    then: no-entry dotted at a pre-pull = contaminant by default; engine-behavior claims get
    R1-verified, never asserted. *(audit: BATCH-4 CORPUS-DEFECT FIRE entry, 2026-07-10)*

46. **The self-indicting-prose tell: when a card's prose has to explain why a verse fits a
    shelf, the shelf is usually wrong.** Three rejected draws carried it — διαιρέω d3 filed
    1Co 12:11 under a sense whose own prose says the job "is the same as sense 2"; δόμα d1/d3
    filed Php 4:17 in sense 2 while writing "functions as a concrete transfer (Sense 1)".
    Reviewer-named as generalizing. Cheap eyeball heuristic now; a v2 lint could flag a sense
    member whose own description names another sense. Related: carve-invention (a carve or
    placement no floor draw attests) ran 4-for-6 on batch-4's rejected draws — the V9_PILE edit
    candidate (floor carve as CONSTRAINT to the drafter) is the design answer. *(audit: G1244 +
    G1390 PARKED entries, 2026-07-10)*

47. **A splitter that assumes numbered senses is blind to the engine's own approved one-job house
    shape.** The first genuinely single-job word (εὐχαριστέω G2168) drew 7/10 cards in the V8
    house shape for one-job-many-frames — single bold headline, organizing paragraph, Sub-uses,
    NO numbered sense anywhere — and both numbered finders scored them 0 senses; the ship gate
    would have refused the same legal shape. Reader blindness to legal output, the inverse of
    #45's feed contamination. Fix = the _LONE_HEADLINE_RE one-sense fallback, bounded (fires only
    when neither numbered form exists and the block OPENS with a bold span) and LOUD
    (sense_split_mode prints "[1 sense — headline fallback]" in floor + dry-run output; pinned by
    an explicit mode-assertion test). → v2: shape-legal output must be machine-legible, and any
    fallback that widens acceptance must announce itself loudly — a silent widening converts a
    numbering botch on a multi-sense card into a false one-sense parse. *(audit: G2168 VOID-floor
    entry, 2026-07-10)*

48. **The citation gate verifies that a verse EXISTS, never WHOSE WORD a quoted phrase belongs
    to — two-lexeme verses are invisible defect surface.** 1Jn 2:8 carries BOTH truth-adjectives
    (G227 "true [commandment]", G228 "true light"); two of three ἀληθής build draws bled G228's
    phrase onto G227 — once as a sense's grounding, once as a Range claim — and every machine
    gate passed both, because the refs were real. Only the armed hand-read against the verse's
    word-level tags caught it (reviewer-named class: cross-lemma misattribution). → v2 probe,
    mechanizable: for each prose claim quoting a phrase of a cited verse, map the phrase's
    English back to the verse's word rows and flag when it lands on a DIFFERENT Strong's number
    than the headword. The data already exists per row. *(audit: G227 ἀληθής PARKED entry,
    2026-07-11)*

49. **The sense HEADER is a gate-blind field — an inherited-tradition gloss can ride 38/38
    verified citations, and it REPLICATES across card fields.** JP caught ψυχή G5590's hand-done
    (pre-pipeline) card asserting "persists beyond bodily death" in sense 4's header while its
    own anchor verse (Mat 10:28) explicitly grants God the power to DESTROY the soul; the same
    overclaim was restated in the Range sentence AND the Range tail ("trans-mortem identity"),
    and a gloss note carried a fourth echo. The citation gate checks verse existence + Strong's
    tag, never the header's semantic claim. → two rules: (a) V9 candidate = header-attestation
    check (every load-bearing header property traceable to ≥1 cited verse that carries it);
    (b) any wording fix must SWEEP every restatement — header, Range, gloss notes — or the card
    contradicts itself one screen below the fix. Full class + before/after pair: V9_PILE.md
    sense-header-overclaim entry (fixed @ 341f493, gate 39/39). *(2026-07-11)*

50. **A machine-gate kill leaves the hand-check battery UNRUN — "otherwise the word's best card"
    on a dead draw is an unverified claim, not a finding.** All three squeeze parks (G227, G162,
    G1390) died at the coverage gate, so their park entries praised the surviving prose ("crux +
    duals + gloss notes all right") from partial reads. When the V10 repair pass closed the
    coverage holes and the full battery finally ran, BOTH tested cards died on pre-existing prose
    rot the machine can't see: a misattribution riding a real ref (Jehoiada, 2Ch 21:3), an
    inverted description (2Sa 19:42), a false cross-verse identity claim (Mat 22:16↔Mar 12:14
    "worded identically"), a second misattribution (Eliphaz, Job 5:12) — six defects total, all
    in guard-preserved, repair-untouched prose. → two rules: (a) adjudication language about a
    dead draw must scope its claims to the checks actually run ("quotes not hand-checked — died
    at gate"); (b) any mechanism that gets a previously-gate-killed card PAST its killing gate
    must trigger the FULL battery as if the card were new — which the V10 design got right, and
    which is why the rot surfaced at review instead of on the live site. *(audit: V10 ACCEPTANCE
    TEST entry, 2026-07-12)*

51. **Text a successor session must copy exactly cannot live only in chat relay — write it to
    disk at affirmation time.** The corrective-commit session was pointed at "the reviewer chat
    record" for its affirmed commit message; the fresh session had only a fragment on disk and
    correctly STOPPED rather than reconstruct (reconstruction = the retyped-not-copied failure
    class that killed its predecessor). The relay worked this time only because the reviewer was
    live to paste it. Corollary from the same session: the message's structure was misdescribed
    by its own author (claimed subject/body split; was one paragraph) — a disk copy would have
    made the property checkable instead of assertable. → affirmed texts (commit messages,
    prompts, ruled wording) go into a file or the handoff at the moment they're affirmed; and
    commit proposals carry subject line + blank line + body so `--oneline` stays one line. Both
    banked as rule candidates for the V11 build session's open. *(audit: CORRECTIVE-COMMIT
    SESSION CLOSED entry, 2026-07-12)*

52. **A tool's display of a line is not the line; bytes are.** At the V11 run session CC read
    draw_hints.py via a search tool whose output rendered the file's `substitution/trade` as
    `substitution\trade`; CC reported a real Python tab-escape bug on that basis and the
    reviewer confirmed it unverified — a fix and a corrupted-hint park note were ruled in for a
    bug that did not exist. The pre-edit byte read (repr of the raw bytes) showed the plain `/`
    on disk; the claim was retracted and the note struck before either landed. Both directions
    ledgered: the claim made from tool display, and the confirmation issued without demanding
    byte evidence (the a9d518b class runs both ways). → rule, adopted verbatim in both chats:
    any claim about a file's contents gets a byte-level read (binary-mode/repr) before it is
    stated or ruled on; a search tool's rendering is never evidence about bytes. *(audit:
    V11 RUN SESSION entry, 2026-07-12)*

53. **An audit entry's quotation of stored verse wording is itself a file-content claim — it
    needs a live byte read at writing time, and red-first fixture building doubles as an audit
    of the entries it draws from.** The G227 park entry's parenthetical asserted stored 1Jn 2:8
    = "a commandment, a new one"; the quote-repair build's fixture work forced a live read and
    the stored bytes read "Again, a new commandment I write to you…" — the opposite of the
    recorded claim, which had ridden through the park adjudication AND the V11.2 kill-classing
    unread. Caught only because self-contained fixtures require the real bytes; corrected by a
    scoped CORRECTION note (the kill itself not reopened — the card's quote still failed, only
    the entry's characterization of the stored text was wrong). → lesson #52's rule extends
    beyond code files to verse data: any "stored text says X" parenthetical gets a byte read
    before it is written or ruled on. *(audit: QUOTE-REPAIR BUILD SESSION entry + its
    CORRECTION in the G227 park entry, 2026-07-12)*

54. **A re-entry mechanism that ADDS a repair pass must arm the full standing repair arsenal,
    not just the new one.** The V11.2 run commands ran `--quote-repair` only; the ruled mechanism
    ("fresh draws + quote-repair pass") READ complete but silently dropped the standing V10
    coverage-repair (`--repair`) the V11 run had used 3×. Immaterial on the three words that died
    on quote gates; surfaced on G1390, which died on a COVERAGE gate with a CLEAN quote gate — the
    exact failure coverage-repair exists for, unarmed. Tipped off by G1390's coverage-kill-plus-
    clean-quote combination. → run commands arm `--repair --quote-repair` together; "adding" a pass
    never means "replacing" the standing one. *(audit: G1390 PARKED entry, V11.2 run, 2026-07-13)*

55. **#30 floor-diff is BLIND to a sense-count collapse — a total merge splits no floor pair, so
    it reads "clean" exactly when placement failure is maximal.** G1390 d3 collapsed the floor's two
    senses into one ("SOMETHING GIVEN" + sub-uses); G227 d3 restructured 4→3. Both drew `#30 clean`
    because a card with fewer senses can't split any pair the floor clustered. Looked like clean
    placement; was the opposite. Tipped off by the `[1 sense — headline fallback]` loud marker + a
    hand sense-count check against the floor. → `#30 clean` does NOT vouch for placement when the
    ship's sense count ≠ the floor's; a sense-count-mismatch card must fail #30 by construction, or
    #30 must refuse "clean." Floor-is-ground-truth includes sense STRUCTURE, not just verse-homes.
    *(audit: G1390 + G227 PARKED entries, V11.2 run, 2026-07-13)*

56. **A quote-gate kill is a MACHINE EVENT, not a defect finding, until the flagged spans are
    confirmed as claims to quote SCRIPTURE.** G227 d3's three quote-gate spans were all the card's
    OWN metalinguistic prose — sense-contrast labels ("matches the facts" / "counts as adequate
    under the applicable rule.") and a gloss-note rendering alternative ("speak what is true") —
    zero real quote-fidelity defects. The `meta:v1` exemption's ≤2-word cap was too narrow to catch
    them, so they tripped the gate; the quote-repair pass then breached its spans-only guard trying
    to "fix" material it should never have received. Tipped off by reading the spans against the
    card (they're the writer's labels, not scripture). → confirm quoted spans are scripture-claims
    before treating a quote-gate fire as a defect; a false-positive feeder makes the repair breach
    regardless of span reality (quote-repair 0-for-3, breach-composition 1+1 / 2+1 / 0+3
    real+artifact). *(audit: G227 PARKED entry + V11.2 CLOSE, 2026-07-13; design-review docket)*

57. **A repair pass whose model NARRATES its work breaches a spans-only guard even when the
    underlying fix is correct — the guard cannot tell good-work-wrapped from prose-rework.** The
    V11.2 quote-repair went 0-for-3 on live guard breaches; the preserved breach bytes (ticket 1,
    banked @ b5fa87d) showed all three were the SAME failure — the model prepended a reasoning
    preamble ("I need to fix N failed quotes: 1… 2… Here is the corrected definition:") OUTSIDE the
    card, and that narration's prose + quote marks tripped the skeleton guard. Underneath, the
    repair was correct every time: G227 declined a no-op (nothing to fix), G236 fixed 1 real defect
    verbatim, G162 fixed 2 real defects AND correctly declined an artifact. The guard was RIGHT to
    refuse (the output genuinely wasn't the bare card); the mechanism was sound; only the output
    CONTRACT failed. Tipped off by reading pre→post diffs — the additions were the preamble, the
    edits were clean in-quote fixes. → a model-repair pass needs a hard output contract (card only,
    no commentary) AND an explicit no-op channel (a decline path, else the model narrates the
    decline in-band); a guard that only sees same-vs-different skeleton can't recover a correct fix
    buried in narration, so the fix belongs in the PROMPT, not the guard. Corollary: preserve the
    refused bytes or this is undiagnosable (the whole review turned on bytes that were being thrown
    away). *(audit: QUOTE-GATE+REPAIR DESIGN REVIEW — CLOSED, 2026-07-13)*

58. **An explicit no-op DECLINE channel is necessary but NOT sufficient — the model still attempts a
    fix on an unfixable span instead of declining, and the failure has more than one shape.** F1–F3's
    F2 gave the quote-repair an explicit "return the card unchanged" path, yet on the four-word RE-RUN
    the decline engaged on some words and not others: G236/G227 declined correctly (clean cap-out on an
    unfixable misanchor), but G1390 reworded UNQUOTED prose (a WRONG edit — "giving"→"transfer" in the
    Eph 4:8 discussion) and G162 MOVED a reference anchor (a CORRECT-but-forbidden edit — splitting a
    lumped ref) rather than declining. Both breached the spans-only guard. This is NOT the #57 contract
    failure (no preamble narration — the additions were out-of-quote EDITS); it's a distinct, deeper
    gap, and the two breach shapes are different problems (wrong-fix vs right-fix-forbidden, see #60).
    Tipped off by reading the refused pre→post diffs. → a no-op channel needs its own hardening and
    red-first testing; "we added a decline path" ≠ "the model takes it." *(audit: F1–F3 RE-RUN
    close-out, 2026-07-13; G1390 + G162 PARKED entries)*

59. **The meta:v2 anchor-wall exempts metalinguistic quotes that carry a RENDERING CUE and MISSES
    cue-less EMPHASIS scare-quotes of the card's own word.** It correctly waves through grammar/
    rendering discussion (G227's "this [is] true [that] you have said," cue "the Greek functions
    predicatively" — proven on same-key bytes: original park fired 3 spans, the fixed run fires 2, the
    exempted span still in the card) but keeps failing a bare emphasis scare-quote (G1390's "giving" in
    'where the "giving" is regulated by divine command') because it matches no verse, has nearby
    clause-anchoring refs, and carries no cue — so the wall can't tell clause-anchoring refs from
    quote-anchoring refs, over-fires, and the repair then breaches trying to "fix" a non-defect. The
    sharpened taxonomy (narrower than "refs confuse the wall"): cue-bearing metalinguistic mentions
    EXEMPT, cue-less own-word emphasis quotes MISSED. → anchor-wall calibration: widen the test to
    catch own-word emphasis quotes WITHOUT opening the ledgered meta:v2 laundering hole. *(audit:
    F1–F3 RE-RUN close-out, 2026-07-13; G1390 + G227 PARKED entries)*

60. **A lumped-ref misanchor has a safe, byte-verifiable fix the spans-only rule can NEVER apply —
    moving a reference is always out-of-quote.** G162's card cited two accurate quotes with both refs
    lumped ('"…giant" / "…unjustly" (Isa 49:25; Isa 49:24)'); the gate's first-ref-primary read
    mis-pairs "should be captured unjustly" (really Isa 49:24) with 49:25. The repair found the
    byte-perfect fix — split the refs, one per quote — but that moves a ref, so the guard refused it by
    construction. Contrast G236/G227, whose misanchors are "right words, wrong verse" and unfixable
    in-quote (correct verse not cited as primary): the repair correctly NO-OPs and caps out on a real
    defect. G162's is FIXABLE, just not through quote-repair's in-quote-only channel. → design input
    for the checkpoint (NOT a bug ticket): force a no-op on the lumped-ref shape (park on the misanchor)
    OR add a separate re-anchor path with its own byte-gate. A re-anchor channel resolves G162's shape
    and does nothing for G1390's — the two F2-gap shapes (#58) need different fixes. *(audit: F1–F3
    RE-RUN close-out, 2026-07-13; G162 PARKED entry)*

61. **The fail's KIND is the routing layer — an unfixable-in-quote defect must never reach the model,
    and the gate already distinguishes the kinds at source.** The anchor-wall calibration checkpoint
    ruled #58/#59/#60's fixes, and the load-bearing insight was that `probe1_verbatim` emits two
    structurally distinct fails: a WORDING miss (`matches NO cited verse` — fixable in-quote) and an
    ANCHORING-RULE miss (`carries the wording of A … anchored primary on B` — the words already match a
    verse, so the ONLY fix moves a ref, out-of-quote → unfixable in-quote by construction). Both re-run
    breach shapes (#58) came from feeding the anchoring kind to a model with no legal move, which then
    reached outside the quote marks (wrong-reword) or moved the ref (right-but-forbidden). RULING:
    kind-tag the fails from the ONE production probe and route — wording → model repair, anchoring →
    never the model (park, or the deterministic re-anchor path of #60). This removes the breach surface
    DETERMINISTICALLY, at the right layer, instead of by prompt persuasion; the prompt sharpen is
    belt-and-suspenders, not the fix. Generalizes the #9 deterministic/model boundary to the repair
    feed: the model only ever does in-quote wording repair, which is all it can safely do. F3's meta:v3
    own-word exemption (#59) is the SAME move upstream — stop the gate firing on the card's own single
    vocabulary word so it never becomes a fed wording-fail at all. → v2: the repair feed is filtered by
    fail-kind, not handed the raw gate output. *(audit: ANCHOR-WALL CALIBRATION CHECKPOINT — DESIGN
    RULED, 2026-07-13; Rulings 1–3)*

62. **An OWN-PARAPHRASE quoted span is kind-a "wording" by the gate but unfixable in-quote, and the
    model's out-of-quote consistency edit is a STOCHASTIC reflex — so the prompt can't be trusted to
    suppress it; the fix has to remove the opportunity.** The calibration BUILD landed (Rulings 1/2/4 +
    prompt-sharpen, three red-first checkpoints, commits bc41006/b963be2/94bcd22) and the four parked
    words re-ran on the fixed pipeline. Routing worked on all four (anchoring kind never fed); G1390
    passed clean (meta:v3 exempted "giving", no model call); G162 clean cap-out park. But **G227
    BREACHED** on a span that is the card's OWN imagery-compression, `"quenched/crushed"` — it matches
    no verse (so kind-a → fed as "fixable") yet has no verbatim source, so instead of the F2 no-op the
    model reduced the quote in-quote (`"quenched/crushed"→"crushed"`, allowed) AND changed the *unquoted*
    prose to match (`not defective or quenched → …or crushed`, the breach — the #58 look-alike shape,
    live under the NEW CP3 prompt `qrepair:4ceeeff4ab2d`). The guard caught it (draw dead, zero bad
    bytes). Then **G236 did NOT breach** on the identical span class (`"changing over"→"change over"`,
    prose byte-identical, matches Dan 4:16/4:25/4:32) — same prompt, guard, cap, span shape → one
    breach, one clean fix. → the own-paraphrase span is a NEW, narrower hole than #58: no exemption
    reaches it (meta:v3 needs a single ALPHA word — this is a slash-compound; the cue path finds no
    cue), so it falls through to the model, which *sometimes* makes the forbidden consistency edit. The
    n=2 pair (byte-identical conditions, opposite outcomes) proves the reflex is stochastic, so CP3's
    named prohibition is DOCUMENTATION and the guard is the WALL — the real fix must remove the
    opportunity (a third fail-kind / an own-paraphrase exemption class that keeps such spans away from
    the model), designed in its OWN checkpoint, not by prompt suppression. → **conditional lift NOT
    closed** (breach on any = not closed); F2 gap persists in this narrower form. *(audit: QUOTE-REPAIR
    CALIBRATION BUILD + RE-RUN — LIFT NOT CLOSED, 2026-07-14; G227 breach / G236 clean byte pairs)*

63. **Decide "unfixable in-quote" DIRECTLY (does a snap-to target exist?) instead of taxonomizing
    what unfixable spans look like — a shape list invites a fourth shape.** The own-paraphrase design
    session weighed the #62 candidates: slash-compound decided the real n=2 pair correctly but is a
    shape patch; "no cue" is a population descriptor (everything reaching the fail line lacks a cue);
    corpus-wide absence also catches the FIXABLE span (G236's `changing over` exists verbatim nowhere
    either — what made it fixable was a NEAR-MATCH, `change over`, sitting in a cited verse). RULED:
    the target-exists test — best sliding-window similarity of the span vs every cited verse's text;
    >= threshold → wording (fed), below → unsourced (never fed; exempt-vs-park by attribution). One
    rule covers anchoring, paraphrase, and unseen shapes. Method lesson: the DECISION RULE was stated
    before the scores landed (gap >= 0.15 → ship, threshold = midpoint), so 0.727 is bytes (0.833
    fed / 0.621 refused), not judgment — and an n=2 threshold carries a mandatory re-open band
    (~0.62–0.83) instead of run-time discretion. *(audit: OWN-PARAPHRASE CALIBRATION CHECKPOINT —
    DESIGN RULED, 2026-07-14)*

64. **Containment is a PIPELINE property, not a patch: guard + cap-1 + red-first fixtures + banked
    refused bytes make a bad round cost one model call and zero bad bytes.** Three rounds of quote-
    repair failures (narration #57, no-legal-move breaches #58, the stochastic own-paraphrase reflex
    #62) all ended the same way — draw dead, evidence banked, nothing shipped wrong — because the
    spans-only guard is byte-strict, the cap forbids re-repair, every detector change is red-first,
    and every refusal preserves its bytes for diagnosis. That standing structure is what makes
    calibration rounds safe to run at all; keep it invariant while the feed logic evolves. *(source:
    reviewer ledger note, 2026-07-14; entered by direction at the design close)*

65. **A discriminator calibrated on near-verbatim edits is BLIND to the class that scrambles the same
    words — the calibration set must span every defect class the gate already catches, or the first
    real member of the missing class ships.** The #63 target-exists test used char-ratio (difflib),
    calibrated on the n=2 pair (`changing over` / `quenched/crushed`), both near-verbatim. It shipped
    RED-FIRST-caught: run against the existing defect-5/6 gate corpus, char-ratio scored a real reorder
    (`bring forth judgment to validity`, all of Isa 42:3's words re-ordered) at 0.690 — below the 0.727
    cut — and EXEMPTED it as own-paraphrase. char-ratio is order-blind; a scrambled real quote and a
    genuine own-paraphrase collide in the band. FIX (ruled): COMBINED score `max(char-window,
    token-SET containment)` — token-set is order-insensitive, so any reorder scores ~1.0 and is fed;
    neither leg subsumes the other (char carries inflection like `changing over` 0.833/token 0.500;
    token carries reorders like 0.690/1.000). Two method lessons that made the RE-PIN defensible where
    0.727 was not: (a) **enumerate the no-target residual by CATCH-LAYER, don't sample it** — meta:v2
    (cue) + meta:v3 (own-word) catch most own-notation UPSTREAM, so the near-match layer's real residual
    was just two spans (`quenched/crushed` 0.621 exempt / `other item` 0.706 must-refuse), fully mapped,
    not a guessed distribution; the n-too-small fragility was structural, not statistical. (b) **a
    redundant leg still needs a red guard** — at the pinned t=0.664 the token leg changes NO current-
    corpus outcome (every real target clears 0.664 on char alone), so a synthetic heavy-scramble guard
    fixture (char 0.640 < t, token 1.000; proven red against a char-only scorer) locks the leg's purpose
    against silent deletion. A standing must-refuse verdict (`other item`) became a binding constraint
    on the threshold itself (`t <= 0.706`), written into code + commit so a future tune can't overturn a
    ruling. *(audit: OWN-PARAPHRASE NEAR-MATCH GATE — BUILD LANDED, 2026-07-14; commit dbea202)*

66. **A parked word's required `--hints` is part of the draw input key, so a live re-run ALWAYS
    redraws — a byte-pinned prediction cannot be tested by re-running; check it against the archived
    card bytes offline instead.** `--hints` injects the park-ruling constraint lines into the draw
    context (they ride the model's user message), so they are correctly part of `draw_signature`.
    Consequence: re-entering a parked word (which is refused WITHOUT `--hints`, ruling 1) moves the
    input key vs its pre-hints saved draw, the saved draw reads STALE, and the tool draws a fresh
    card. A redraw is a DIFFERENT card than the one the near-match predictions were computed from, so
    "prediction-met" is unfalsifiable by the live method (G227 re-run: fresh card had no
    `quenched/crushed` span at all — quote gate clean — then failed an unrelated coverage gate). The
    tripwire (`calling the verse engine` = pause) is inherent-post-spend: the redraw is what prints
    it, so one draw is already charged before the pause is visible. FIX (ruled 2026-07-14, method
    change re-approved): retire the live re-run for parked words; run the FIXED gate offline against
    the ARCHIVED on-record card `raw` (recoverable — superseded draws are moved into `draws/history/`
    intact, ruling 5) with live read-only verse lookups — deterministic, repeatable, zero model spend,
    tests exactly the prediction card. Helper `scripts/offline_gate_check.py` (read-only end to end,
    reuses production detectors). Per-word precondition: the archived card must contain the predicted
    span before its gate check runs. *(audit: PARKED-WORD REDRAW — LIVE RE-RUN RETIRED, 2026-07-14)*

67. **A fourth wall that fires on a structural, benign pattern trains humans to ignore it — the
    discriminator must key on the pattern's ROOT, not just the score.** meta:v5 demoted every
    IN-BAND (0.62–0.75) metalinguistic-cue exemption to an adjudicate WARN. The live sweep proved
    it fires on a STRUCTURAL benign pattern: a lemma's gloss necessarily resembles that lemma's own
    inflected forms in its own cited verses, so 12/79 live cards warned, all gloss displays. Warn-
    until-adjudicated at that rate is a treadmill, not an audit trail — when ~95% of warns are noise
    the human stops reading them. FIX (meta:v6, scope-b (b), 2026-07-14): the CONTENT-TOKEN
    DISCRIMINATOR — an in-band cue exemption warns only when the span reproduces a verse-word RUN
    (>= 2 distinct CONTENT tokens present in a cited verse; content = tokens minus a FROZEN closed
    English function set); a single lemma-gloss inflection (run <= 1) stays a NOTE. Presence, NOT
    adjacency (a reordered laundered quote still warns — reorder killed G227 once; an adjacency
    "fix" would silently bless reorders). **NAMED BOUNDARY RISK (Option A, ruled — banked, not a
    silent gap):** a cue-exempted FULL-token reorder (every content word present, scrambled,
    rendering cue, no anchor) scores ~1.0 on the token leg → OUT of band → invisible to BOTH the
    band watch (>0.75) and the v6 run check (in-band-gated) → stays a note. Defense-in-depth: non-
    cue reorders → own-paraphrase branch (the token-set leg, G236 lineage); ref-carrying reorders →
    anchor wall. **RE-OPEN TRIGGER (automatic, no fresh ruling):** if any real card ever surfaces a
    cue-exempted full-token reorder (sweep, adjudication, or audit), Option B (warn by run>=2
    regardless of band) re-opens with that span as evidence. The frozen function set is a DESIGN
    element (closure fixture-locked); changing it is a design re-open. *(audit: META:V6 CONTENT-TOKEN
    DISCRIMINATOR, 2026-07-14)*

68. **A "primary anchor" is a property of the citation's SHAPE, not its position — a coordinate
    list or range assigns none.** The nearest-first anchoring rule (V11.1 ticket 2, ruled for
    SEQUENTIAL lead-in prose — "2Sa 19:42 asks '..' while Mat 7:11 says '..'") over-fired on
    COORDINATE lead-ins ("Job 42:7 and Job 42:8:", "Ezra 6:11-12"): it named the NEAREST ref
    primary and flagged a quote whose real scripture sits in the OTHER listed verse as a
    mis-anchor — though the reader is pointed at both and the words genuinely live in one. A span
    reaches the anchoring branch ONLY after a word-for-word match to a cited verse, so the
    relaxation can never pass fabricated/reworded text (G227 "Job 42:7 and Job 42:8" + G236 "Ezra
    6:11-12" both byte-adjudicated: plain scene-set / honest range citation). Every listed ref is
    cited by construction — `cited_refs` sweeps the whole card — so a lead-in cannot name a verse
    the card never looks up. FIX: for a lead-in whose refs are joined only by COORDINATE GLUE
    (whitespace/comma + and/or), a quote matching ANY listed ref is anchored. Two teeth stay:
    trailing-bracket paired-swaps (a separate branch, untouched) and sequential lead-ins (clause
    words between refs -> still nearest-first). METHOD NOTE (banked, reviewer-endorsed): the first
    helper used a fixed char window and red-first caught it over-reaching across a SENTENCE
    BOUNDARY (it grabbed a prior sentence's trailing-bracket ref, so a real coordinate list read
    as sequential and fired — the grafted mixed-card fixture); the shipped helper WALKS OUT from
    the ref nearest the quote and stops at the first clause gap, capturing the adjacent run by
    construction rather than by a tuned constant — a structural boundary beats a distance guess.
    Sibling of #61 (fail-KIND routes deterministically; here fail-EXISTENCE is decided by citation
    shape) and #67 (presence-not-adjacency — the same "read the structure, not a proxy" move).
    *(audit: LEAD-IN MULTI-REF ANCHORING — COORDINATE-LIST RULE BUILT, 2026-07-14)*

69. **A path that WRITES must run every check the main write path runs — a "complete battery" is
    defined by the APPLY's checklist, not by the checks the reviewer reached for.** Two instances in
    one night, same shape, one benign and one nearly costly. (a) **The readiness pass under-ran.**
    G1390's offline ship-readiness pass ran the quote gate + coverage + floor-match + a full hand read
    and was reported COMPLETE — but the rendering-claim lint and the dangling-ref lint only fire in the
    apply/assemble path, so a REAL fire (the Eph 4:8 gloss label claims `*gift*`; corpus renders
    "gifts"; the card's own senses_block quotes "gave gifts to men" two fields up) reached a LIVE row
    and was caught by the apply's own output, not by the battery that had just certified it. (b) **The
    surgical-fix path under-ran, and would have falsified the record.** `fix_lexica_raw` calls
    `validate_entry(entry)` with NO `conn`, so the V11 probes take the `if conn is None:` branch —
    they PRINT "NOT RUN" and stamp NOTHING; `assemble()` then builds a fresh entry that never carries
    `warns_adjudicated`; and the tool never calls `open_probe_warns`, so nothing blocks. Applying the
    one-letter label fix would therefore have SILENTLY ERASED the adjudication ruling and the 7
    probe-2 warns from the live row — leaving it reading "clean, no warns ever". Caught from the
    dry-run's own warning line, before any write. → v2: (i) a readiness/verification harness ENUMERATES
    the write path's checks and runs all of them, or NAMES each one it skips (silence reads as
    "covered"); (ii) every secondary/surgical write path either runs the full probe set or REFUSES —
    a warning printed on a pass that still writes is not a control (#31's shape, new door); (iii) an
    audit field that GATES a ship (`warns_adjudicated`) must SURVIVE any rewrite of its row, or the
    rewrite is a regression — content-addressing the ruling to the row, not to the pass that wrote it.
    Ruling that fell out of it: **wrong-but-tiny beats falsified-record** — the label fix was deferred
    to ride the fixed tool rather than buy accuracy with an audit lie. Sibling of #21 (a gate that
    reads a length is not reading the text), #31 (warning-after-write is not a control), and #50
    (a machine-gate kill leaves the hand battery unrun). *(audit: G1390 δόμα — SHIPPED ʰ, 2026-07-14)*

70. **Seed a fixture from EMITTED BYTES, never from a hand-recalled string — and an assertion that
    checks a substring does not certify the bytes.** Building #69's red-first test, the prior
    probe-2 warn was seeded by hand as `… 2Ch 21:3 — adjudicate`, copied from the shape of an
    existing assertion in `tests/test_v11_probes.py`. The real emitted string
    (`build_lexica_def.py`, `probe2_names`) ends `— adjudicate (misattribution class)`. The existing
    assertion had never caught the difference because it only tests `"Jehoiada" in warns[0]` — a
    substring check certifies the substring, nothing else. The invented tail read as a CHANGED warn
    set, so the carry test compared a real set against a set that never existed and the fixture
    tested nothing; the tool was behaving correctly the whole time. Caught only because the harness
    drove the REAL script end-to-end (a mock would have agreed with the invented bytes and shipped a
    green that proved nothing). → v2: (i) fixture strings that a comparison KEYS ON are captured from
    a real run's output, never retyped from memory or inferred from a neighbouring assertion; (ii) a
    test that changes its own fixture between red and green must RE-PROVE red against the corrected
    fixture, or the green is unattributed — the change may be what turned it; (iii) when a
    hand-written fixture disagrees with the machine, suspect the fixture first. Second byte-vs-recall
    lesson of this arc — kin of #15/#52 (the sig pins fed input, not prose; two cards shared
    `aa064d41` with different prose) and of the standing rule that the written record outranks
    recall in BOTH directions. *(audit: TOOLING — fix_lexica_raw 3-gap fix, 2026-07-14)*

71. **A check that derives its REFERENCE SET from the data changes meaning with the fixture — and
    fails quietly.** `dangling_book_refs` / `noncanon_book_refs` decide "is this a real book?" via
    `_valid_books()` = `SELECT DISTINCT book FROM verses`. Run against a two-book test fixture they
    flagged canonical **"Num"/"2Ch" as NON-canonical** and let a bare dangling **"Rev"** pass unseen
    — the lints were not broken and the card was not defective; the fixture had silently redefined
    the lints' notion of the canon. Nothing announced it: the output looked like findings. The
    repair is the tell — seed the reference set from the PRODUCTION table (`_BOOK_CODE`), never a
    hand-typed list, because hand-typing it is #70 wearing a different hat. → v2: (i) a detector
    whose verdict depends on a set READ FROM THE CORPUS must say so at its call site, and its tests
    must seed that set from production, not from the handful of rows the case-under-test needs;
    (ii) when a lint's output disagrees with a fact you are certain of (Num IS canonical), suspect
    the FIXTURE'S WORLD before the lint — the same "suspect the fixture first" reflex as #70;
    (iii) a fixture is not just inputs, it is the detector's whole universe — an under-seeded one
    doesn't weaken the test, it changes what the test MEANS. Sibling of #70 (fixture-vs-reality) and
    of the standing certification rule (a detector must fire on a known positive before a zero is
    trusted — here a known NEGATIVE mis-fired for a fixture reason and would have been read as a
    finding). *(audit: TOOLING — offline_gate_check write-path battery, 2026-07-14)*

72. **A marking column is not an index — `is_pn` marks SOME proper nouns, not the names in a verse.**
    Job 1:15 reads "And **Sabeans** fell upon and captured them" and carries ZERO `is_pn` rows; the
    corpus-wide union reaches "sabean" through ONE row (`sabeans`), and only via plural loosening. Two
    designs were built on "does this verse name a person = does it have an `is_pn` marking" before the
    bytes said otherwise — and the failure direction is the SILENT one: a person present but unmarked
    reads as "no person named" and gets DEMOTED, which is precisely what a triage tier would then have
    the human skip. → (i) before a column becomes an index, prove COMPLETENESS on a case where the
    answer is visible in the text, not coverage on cases where it happens to be marked; (ii) a
    corpus-wide UNION of a sparse per-row flag is denser but not complete — measure its depth (one row
    is a real answer) rather than assuming density; (iii) when every candidate mechanism costs a ruled
    behavior, the design is not buyable at current data — park it with the precondition NAMED, so the
    revival has a trigger instead of a memory. Kin of #71 (seed from production, and know what the
    production set MEANS) and of the certification rule (a detector's zero is only as good as its
    reference set). *(audit: PROBE-2 OVER-FIRING — closed as a design finding, 2026-07-15)*

73. **A ruled fix DIRECTION is not a fix MECHANISM — and the gap is where money dies.** Three times in
    one session a spend was pitched with a "known payoff", and all three would have BOUGHT THE DEFECT:
    the G236 redraw (the roster forces the misfile the draw was meant to fix — held), the G162 redraw
    (its own record already rules "fresh draws don't cure, whether the failure recurs or roams" —
    withdrawn), and G236 part 2 (a floor is TEN DRAWS VOTING, not a repair; same prompt + same verses ⇒
    the same vote that misfiled Ezra in the first place — refused). Each pitch was persuasive and each
    collapsed on a cheap read of the machinery. → (i) before ANY spend, answer "what CHANGED on the
    generation side since the thing failed?" — if the answer is "the detectors", that raises KILL
    probability, not conversion probability: better detectors catch more, they do not write better
    prose; (ii) "the fix direction is ruled" is NOT "the fix is available" — name the MECHANISM and
    check it is not banned (path-(c) hand-carve), frozen (V9 is the prompt of record for every shipped
    card), or by-design excluded (floors draw UNHINTED) BEFORE treating the spend as defined; (iii) a
    spend authorization covers a spend that COULD fix the thing — holding when the bytes say it can't is
    COMPLIANCE with the gate's purpose, not an override (the G236-redraw precedent, now applied three
    times); (iv) the cheap read paid for itself every time — read the machinery, not the pitch. Kin of
    #70/#71/#72 (recall over bytes) with the loss denominated in money instead of a false record.
    *(audit: SPEND DELIBERATION — two spends proposed, both refused on bytes, 2026-07-15)*

74. **Floor-DERIVED is not floor-CONSENSUS — and BOTH sides of the loop lost the distinction in one
    session, in opposite directions.** The roster's entire legal defense is that it is *"not
    hand-invented — it is the floor's OWN repeated-review consensus"* (`draw_hints.py:15-26`). Two
    failures grew from the same root — nobody had separated *"the floor contains it"* from *"the floor
    settled it"*. **Direction 1 — too strict (the loop's own banked board):** the SPEND BOARD read
    *"hand-carve the roster ⇒ BANNED (path-(c))"*, an INVERSION of the charter, which bans hand-carving
    for **hints/jobs ONLY** and expressly permits a roster to fix count + grouping. It had also priced
    the lever at *"~10× a redraw, the board's most expensive item"* — pricing a floor re-run when the
    real lever anchors the SHIP draw at ONE (`build_lexica_def.py:3125`). A prior session compressed a
    rule into a slogan; the slogan then killed the only surviving mechanism sight-unseen, and every
    later session inherited the slogan, not the rule. **Direction 2 — too loose (CC, this session):**
    having falsified the slogan, CC framed the deciding question as *"is the third home IN the floor?"*
    — floor-DERIVED. But a placement in 1 of 10 draws is in the floor and is consensus by no reading;
    reading it back is **minority-shopping in the roster's clothes — hand-carving one layer removed.**
    Reviewer-caught before the data was opened. **Direction 3 — the same root, third face (lever 12,
    reviewer-raised, disposed):** re-aggregating the saved floor under a NON-MODAL counting rule.
    Duplicate in form (the roster IS the aggregation output) and worse in substance: it re-scores the
    vote until the floor returns the ruled direction's answer, then claims the roster's *"I only read
    what the floor settled"* defense for the result. **Consensus-manufacture wearing consensus's
    clothes.** → (i) when a mechanism's legality rests on "it came from X", the load-bearing word is
    never *contains* — write the STRENGTH test into the charter, because "derived from" silently admits
    a minority of one; (ii) **pre-register the criterion, its numbers, AND its predicted outcome BEFORE
    the deciding read**, with thresholds taken from the machinery's OWN named bands (~2/10 *"poles
    blur"* · 5/5 *"true seam"* · 7-8/10 *"homed"*) and never from what would be convenient — here it
    made a one-line read decisive and left no room to rationalize the lone 3-sense draw into a rescue
    (**the draw was left UNOPENED; the temptation is banked in the audit precisely because it was
    real**); (iii) a rule compressed into a slogan for a handoff will be inherited as the slogan —
    when a board line blocks a mechanism, cite the charter's own bytes beside it or the next session
    obeys a rule that was never ruled; (iv) both directions are the SAME error, so neither "we already
    ruled it banned" nor "but the evidence is right there" is a check on the other — only the charter's
    own words are. Kin of #73 (a ruled DIRECTION is not a MECHANISM — this is its next layer: a named
    mechanism is still not a LEGAL one) and of #70/#71 (recall over bytes; here the recall was the
    project's own board). *(audit: G236 PART 2 — MECHANISM KILLED ON THE FLOOR'S OWN BYTES, 2026-07-14;
    written under JP's standing delegation, reviewer-RULED in over CC's self-assignment restraint)*

75. **A first-firing assert can MASK whether a ruled control actually works.** Building the probe-2
    guard's loudness, the reviewer ruled a specific control: a break moving the FAILURE DIRECTION
    (guard-error must produce MORE warns plus a not-run, never fewer) had to be caught red-first.
    The break was made — the loader's error path returned an empty set instead of None, flipping
    demotion ON with nothing in it, so every boundary token was demoted and warns went **2 → 0**:
    real misattributions vanishing silently, exactly the direction that loses information. The suite
    went red — **but at a CONTRACT assert sitting earlier in the file, not at the direction lock.**
    Two of them, in sequence. Each had to be stood down before the ruled control could be watched
    fire alone (`AssertionError: []`). **Had the run stopped at "the suite caught it", the direction
    lock would have been recorded as proven while never having been exercised at all** — a control
    certified by its neighbours' alarm. → (i) **three asserts "catching" a break is not three proofs
    — it may be one proof and two shadows**; a suite going red tells you SOMETHING fired, never that
    the thing you built fired; (ii) to certify a SPECIFIC ruled control, stand down the asserts ahead
    of it so it fires ALONE, then restore them — and the restore is its own hazard, because **a
    stood-down assert that stayed down is the very defect class the ticket was closing, recurring
    inside its own build** (grep the stand-down marker to zero and let the diff show it; the reviewer
    required exactly this as a citable commit line, not a claim); (iii) this is the certification rule
    turned on the tests themselves — *a detector never watched to fail ALONE is not known to work* —
    and the same shape as #52: **a tool's display of a line is not the line; a suite's red is not your
    control's red.** Kin of `feedback_audit_tools_must_fail`. *(audit: PROBE-2 GUARD — THE SILENT
    DEGRADE NOW SPEAKS, 2026-07-14; number ruled by JP)*

76. **A control that asserts PRESENCE is blind to over-firing; one that asserts EXACTNESS sees it.
    The axis is not positive-vs-silent — it is loose-vs-tight — and an "it doesn't exist yet" red
    proves absence, not discrimination.**
    ⚠ **THIS ENTRY WAS BANKED WRONG AND CORRECTED THE SAME DAY, BY ITS OWN BYTES.** It first read
    *"a POSITIVE control cannot catch an OVER-FIRING detector — only the silent direction can."*
    That is FALSE, and the G162 known-positive control falsified it hours later: over-fire the
    detector and that control goes **RED**. The difference was never the direction. The synthetic
    positive asserted `assert hits` — mere PRESENCE, which an over-firing detector satisfies
    trivially. The known-positive asserted `len(hits) == 1` AND the exact fire text AND that the
    card's own sense was absent from it — EXACTNESS, which over-firing cannot satisfy. **The
    original lesson generalized from ONE loose assertion to a whole class, which is the exact
    move `feedback_verify_before_claiming` exists to stop — committed inside the commit that banked
    a lesson about unproven controls.** The reviewer had approved the wrong version; approval is not
    verification. Red-firsting the leading-boilerplate detector produced four reds that all read the
    same:
    `AttributeError: no attribute 'leading_boilerplate'`. That red is the **WEAK form** — it fires
    because the function is MISSING, so it would look identical for a detector whose logic was
    inverted, over-broad, or a stub returning a constant. Proof came only from the **direction-lock**:
    the real detector was deliberately over-fired (both cuts removed), and **the positive control
    stayed GREEN** while both silent controls went red — because that control asked only "did
    something fire?". A detector that fires on EVERYTHING passes every LOOSE "it fires on the defect"
    test ever written for it. → (i) **write the assertion tight and it watches both directions at
    once**: `assert hits` proves reach and nothing else, while an exact count + exact text + an
    explicit "and NOT the neighbouring content" clause catches under- AND over-firing in one control.
    A silent control is the cheap way to buy restraint-proof, not the only way — reach for it when
    the assertion cannot be made exact; (ii) an AttributeError/ImportError red is a scaffolding check, NOT
    evidence the assertions discriminate — the honest red is the one obtained by *breaking working
    logic*, which means the direction-lock belongs in the GREEN step, not "after"; (iii) the revert is
    its own hazard, same as #75(ii): restore from a byte-level backup and cite the matching hash +
    a zero grep of the over-fire marker, so the diff proves the sabotage left (here: restored sha256
    `c82be4f5…`, residue 0; the known-positive lock: `0a7cbb7c…`, residue 0); (iv) corollary for
    reading old suites — **a detector whose fixtures all assert mere presence has never been shown to
    restrain itself**, whatever its green record says; (v) the meta-lesson from this entry's own
    correction — **a lesson is a claim and gets verified like one.** A lesson banked from a single
    observation, reviewer-approved, and written in absolutes was falsified by the next run of the
    same suite. Bank the OBSERVATION tight; let the generalization earn its width. Kin of #75 (that
    one: which control fired; this one: which DIRECTION was ever tested — and how loosely it asked)
    and `feedback_audit_tools_must_fail`. *(audit: G162 PREAMBLE-LEAK TICKET — PRE-CHANGE REVIEW,
    RULED BUILD, 2026-07-14; banked at the green receipt, SELF-CORRECTED at the known-positive
    landing the same day)*

77. **A read that reports LOADING is not a read that reports WORKING — make the tool prove it BIT.**
    A throwaway candidate read printed `(function-word list loaded: 171 entries)` and then filtered
    NOTHING: `cache_funcwords.json` stores BARE numbers (`'1032'`), the comparison used G-prefixed
    keys (`'G1032'`), every check missed silently. **The reassuring line was TRUE and USELESS** — the
    list really had loaded; loading was never the question. It was caught only because the output was
    absurd on its face (καί, ὁ, αὐτός ranked as "content words"). Had the mis-key hit a subtler
    filter, the list would have looked plausible and been used. → (i) **a success line must assert the
    thing you actually depend on, not a step on the way to it** — the fix was not a better pattern but
    a `FILTER PROOF` line asserting that known members ARE matched (`[n in fw for n in ('3588',
    '2532', ...)]` must be all-True) BEFORE the output is used; (ii) **key-shape mismatches fail
    SILENTLY and symmetrically** — a set lookup that never matches raises nothing, returns nothing,
    and reads as "no exclusions needed"; whenever two id spaces meet (G-prefixed vs bare — the same
    seam as the `strongs_base` invariant), assert an overlap, never assume one; (iii) **throwaway code
    gets the same rule as shipped code** — this fell inside the very session hunting silent fallbacks,
    which is exactly when a scratch read feels too small to verify; (iv) generalization of #69(i) from
    reports to TOOLS: silence reads as covered, and so does a green-looking load. Kin of
    `project_silent_fallback_rule` and `feedback_audit_tools_must_fail`. *(audit: CLOSING-SUMMARY
    CLASS — SIZED ON LIVE CARDS, 2026-07-14; reviewer-ruled bankable)*

    **COROLLARY — THE STANDING TEMPLATE FOR ANY COMPARISON READ (extension, RULED after this lesson
    RECURRED ONE HOUR AFTER BEING BANKED, by its own author).** A blast read compared
    `{'book','chapter','verse'}` tuples against stored verses whose real shape is
    `{"ref": "Exo 25:14", "text": …}` (`build_verses` stores ONE ref STRING). Every lookup returned
    `None`, nothing matched, and the read announced **"81 of 81 live cards missing ~40 verses each"** —
    with total confidence. The tell was present and nearly missed: **G3464 had 27 verses attached and
    the read called 27 missing — EXACTLY ALL of them.** → **A READ THAT COMPARES TWO DERIVATIONS MUST
    FIRST PROVE THE DERIVATIONS TOUCH: print a sample from each side, assert the overlap is > 0, and
    REFUSE TO EMIT A NUMBER if it is not.** → **Both sides must come from the PRODUCTION derivation —
    never set a hand-rolled key tuple beside a production one**; that mismatch is invisible and total.
    **WHY A CONTROL AND NOT VIGILANCE — the load-bearing half:** the FIRST failure broke toward
    **ABSURDITY** (καί ranked a "content word") and caught itself. The SECOND broke toward a
    **BELIEVABLE CATASTROPHE** — "every card is missing 40 verses a reader should see" is exactly the
    finding that would have justified redrawing all 81 cards. **The direction of a silent breakage is
    UNKNOWABLE IN ADVANCE, so "watch for absurd output" is not a rule. The control is.**
    *(audit: the retracted blast read, 2026-07-14; reviewer-ruled as the standing template)*
