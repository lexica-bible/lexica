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

## Added at the batch-4 open (2026-07-10, JP count reversal via reviewer relay)

45. **A ship whose in-budget rejects were defect-class does not count, though it shipped in
    budget.** Ships-within-budget absorbs VARIANCE; a defect firing on 2 of 3 draws is a rate
    (#43), and the clean third draw is a fact about sampling, not the engine. Two supporting
    principles ruled with it: (i) a control word cannot be scored against a rubric its own
    output authored (G2665 wrote the #30 fire classes — polluted instrument, one level up from
    the hand-patched-card objection); (ii) draws are owned by the committed wording they ran
    under — G2665 drew pre-promotion, which is why step 5 left the count open rather than
    booking it. Exhibit: G2665 ruled SHIPPED OFF-COUNT at batch-4 open; the 6/15 booking
    reversed to 5/15. Retroactive scope = OPEN (JP rules with the WS1 classification table in
    hand — "look first, then rule"). *(audit: BATCH-4 OPEN amendment above the STEP 5 entry,
    2026-07-10)*
