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
