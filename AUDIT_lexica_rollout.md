# Lexica definition-engine rollout — audit packet

Frequency-ranked rollout (~3,954 Greek words at occ≥2), built by
`scripts/build_lexica_def.py`. Candidate list from `scripts/rank_lexica_candidates.py`
(read-only; folds `contested_register.LEXICA_ALIASES`, excludes the CONTESTED register +
the 50 `structural.py` closed-class lemmas, flags names/pronouns).

Pass criteria per entry (JP's bar): citation gate clean, **dangling and noncanon empty**.

---

## Batch One — calibration batch

Top 20 content words after skipping FUNC-flagged (I, all, who, someone) + 11
oblique-pronoun / numeral / particle rows the auto-flag missed (the "you/me/us" forms,
ἕως, ἰδού, εἷς).

G5207 υἱός · G2036 ἔπω · G4160 ποιέω · G3004 λέγω · G1093 γῆ · G935 βασιλεύς ·
G2250 ἡμέρα · G1096 γίνομαι · G1325 δίδωμι · G3624 οἶκος · G2992 λαός · G5495 χείρ ·
G1492 εἴδω · G444 ἄνθρωπος · G435 ἀνήρ · G3962 πατήρ · G2064 ἔρχομαι · G4172 πόλις ·
G2980 λαλέω · G2983 λαμβάνω

**+6 extension:** G191 ἀκούω · G3056 λόγος · G4198 πορεύομαι · G4383 πρόσωπον ·
G3686 ὄνομα · G1135 γυνή (woman/wife — pairs with ἀνήρ above).

### Register / fork candidates (flag only — JP's separate call, do NOT resolve)
The whole point of the calibration batch: the top of the frequency list is where fork-candidates
live. Split by where they surfaced —
- **Batch-found — both RULED 2026-07-03, NO fork:**
  - **G5207 υἱός — no action.** The first "looks like a fork-candidate, isn't one" ruling, and the
    template for it: the disputes (Son of Man, Daniel 7 reception) are about the PHRASE and the
    REFERENT, not the lemma. Everyone agrees υἱός means "son," and the entry already locates the
    title-force in the article, not in the word. If it ever needs treatment, that's an ARGUMENT GRAPH
    on Daniel 7, not a word fork. (Same shape as the huios "sons of God" no-fork call and the
    structural-word contest rule: settled meaning + contested application ≠ a lexeme fork.)
  - **G3962 πατήρ — no action.** God-as-Father is an attested use grounded in the greeting formulae;
    the usage isn't contested — unlike θεός, where the grammar itself (John 1:1c) is the battlefield.
- **Prior (already built):**
  - **G3056 λόγος** — known register candidate; sense 5 (the "Word" as a personal/hypostatic
    referent), thin at 1 ref. Real, but the PRIOR column — not batch calibration data.
- Watch on build (not forks): ἔπω/λέγω/λαλέω are three "say/speak" numbers (ἔπω = the aorist half
  of λέγω, suppletive); ἄνθρωπος vs ἀνήρ is the human-vs-male pair. The engine kept them distinct.

### Thin senses (advisory — a sense grounded on too few refs)
Four across the 26, all single-ref figurative extensions, none load-bearing:
- **G5495 χείρ** — #4 (structural projections functioning like hands).
- **G4172 πόλις** — #3 (the figurative "city" for a desired location of a condition).
- **G2983 λαμβάνω** — #5 (take-as-a-model / adopt as an example).
- **G3056 λόγος** — #5 (the "Word" personal/hypostatic referent, 1Jn 1:1). **PRIOR** column — this is
  a prior-built entry, not batch calibration data.
(Note: πρόσωπον's ro draw showed 1 thin sense; its SHIPPED draw has none — the applied draw differs
from the reviewed one, the same draw-drift the draw-cache item addresses.)

### Open items — logged, NO fix now
- **G3962 πατήρ — κύριος-under-πατήρ row (phrase misalignment).** A πατήρ occurrence row
  carries κύριος misaligned under it. Data-side phrase misalignment, not an engine bug;
  parked here for a later pass.
- **Five tagging errors (ABP tag gaps) — surfaced by this batch.** Cases where the gloss set carries
  a word that isn't this lemma at that verse (a mis-tag / mis-alignment, same family as the κύριος
  row above). The definition engine is doubling as a corpus auditor — these fell out for free:
  1. **γῆ** "hand" (Deu 33:13) — no context supports gē = a body part; lemma-assignment anomaly.
  2. **ἀνήρ** "king" (1Sa 17:25) — the Greek there is basileús, not anḗr.
  3. **βασιλεύς** "saying" (Psa 105:14) — attaches to a following speech-introducer, not the lemma.
  4. **θεός** "LORD" ×3 — renders kýrios, not theos (prior-built θεός; logged for the same list).
  5. **χείρ** "lips" (Pro 31:31) — the gloss follows a different underlying text (Hebrew "fruit"),
     diverges entirely from cheír.
  All data-side, non-blocking; parked here as a real case list for the corpus-hygiene pass.

### Calibration wins
- **Freight-flagging fires on non-contested words** (the plain-meaning bar, without a fork):
  - **G1325 δίδωμι** — flagged the gloss *impute* (1Sa 22:15; Jon 1:14; Heb 8:10) as importing
    forensic/theological freight the context doesn't require.
  - **G1135 γυνή** — flagged *wife* as narrower than many contexts need (1Co 7:1: the generic
    female, not a marital frame).
- **Two hard-reject saves** — λαός + πρόσωπον apply draws cited "Ruth" (unresolvable label); the
  write-time citation gate blocked both rather than ship an unverified ref. The gate is the floor.
- **"Better is reportable"** — the widened dangling lint surfaced pre-existing bare-Ruth/Esther refs
  sitting in already-shipped entries (χάριν). Found debt, didn't create it.
- **The engine made the Berean / plain-meaning call unprompted** (senses kept honest without a fork):
  - **G191 ἀκούω** — the hear/heed split: the entry keeps the obedience-weight CONTEXTUAL, explicitly
    noting the lemma doesn't change form between "heard" and "hearkened" — it refused to lexicalize
    compliance into the word. The one that could most easily have gone wrong, gotten right.
  - **G1135 γυνή** — flagged that English imposes the wife/woman split; the Greek lemma is one word
    doing two contextual jobs.
  - **G2992 λαός** — resisted a theologized "people of God" as a separate sense; kept it as the same
    word with a possessive/covenant relationship added by context.

### Redraws
- **G1325 δίδωμι — RESOLVED.** First draw carried a `1Sa` dangling ref (no ch:vs) inside
  the *impute* gloss-note → failed the dangling-empty bar. Redraw came back 40/40, dangling
  gone. Cause was draw-level drafting looseness, not data.

### Batch One — CLOSED, 26 applied (2026-07-03)
First apply: 17 written clean · 7 prior stamp-skipped (υἱός, γῆ, βασιλεύς, ἡμέρα, οἶκος, χείρ,
λόγος) · 2 rejected on a `Ruth` citation (λαός G2992 + πρόσωπον G4383). After the book-normalizer
fix: λαός + πρόσωπον re-applied clean, πατήρ redrawn to clear its `Col` dangling. **All 26 built.**

### CLOSED — πατήρ G3962 sense structure (ruled 2026-07-03)
**The new 3-sense draw STANDS.** The 1Jn 2:13 elder-address is a contextual sub-use, not a sense —
the gloss_note treatment is better lexicography than the old draw's thin standalone sense 3. The
redraw judged equal-or-better on read; the old draw's epistolary-clustering coverage note is
preserved in the logs.

## Process lessons (Batch One)
1. **Confirmation tools must be able to fail.** Two instances in one day — the τοῦτο sweep's void
   zero (accent-normalization killed the pattern, so it "passed" by matching nothing) and the stale
   `audit_dangling_context.py` copy printing byte-identical output after the lint changed. Same lesson:
   control-test a detector against a KNOWN positive, and never keep two copies of scan logic. **RULE:
   any new audit helper reuses the production detector, never reimplements it** (the reporter now
   imports `dangling_book_refs`' own regexes).
2. **Apply regenerates — reviewed ≠ shipped.** Three costs: πρόσωπον passed ro then hard-rejected at
   apply (saved by the gate); δίδωμι's ro `1Sa` dangling vanished at apply while a NEW Jos-surface one
   appeared; the πατήρ redraw shipped a structurally different entry (4→3 senses) than the reviewed
   one. Draw cache is the highest-priority batch-two item — it turns three risk classes into zero.
3. **The deterministic/model boundary held everywhere it was tested.** Every fix that worked is
   deterministic (book table, chapter-strip, soft set, exact lookup); everything model-side stayed
   advisory. The Judges/Jude proof is the template: turn a style rule into a correctness argument and
   lock it with a test.
4. **Sense-structure variance is the gate-invisible failure mode.** πατήρ drew 4 senses then 3 from
   identical input; both pass every gate. So batch-two sampling can't just count gate failures — it
   needs a human read of SENSE STRUCTURE on the sample, the only place draw variance shows.

## Calibration numbers
- **Draws:** ~22 model draws total (19 first-apply + δίδωμι redraw + λαός/πρόσωπον redraws; πατήρ
  force-redraw on top). SHIPPED: 19 fresh entries + 7 prior = 26. **2 hard rejects** (both "Ruth",
  both systematic, both fixed), **1 genuine dangling** shipped-then-redrawn (πατήρ Col), **0 unverified
  citations shipped.** (The precise total-draw count would need every raw log; the shipped-entry figures
  are exact.)
- **Freight-flag hit rate on PLAIN words was high** — impute (δίδωμι), wife (γυνή), hearken/heed
  (ἀκούω), commit (ποιέω), execute (δίδωμι). This answers the open question: the flags work OUTSIDE
  the CONTESTED register.
- **Tagging-error yield ≈ 6 corpus rows per 26 words** (5 tag errors + the κύριος row). Projected
  across ~3,954 words ≈ **~900 misalignment rows** expected. That number should decide whether the
  phrase-boundary fix gets scheduled BEFORE or DURING the rollout.

## Batch-two prep list (consolidated closing section)
1. **Draw cache** — ro saves the reviewed draw, apply writes THAT draw. Highest priority (kills the
   three lesson-2 risk classes).
2. **Sampling rate proposal (from this batch).** The write-time gate is a reliable AUTO floor (2 Ruth
   saves, zero false blocks); the freight/dangling lints self-fire. So no full eyeball needed for hard
   errors. Eyes still required on: register/loaded-referent words + SENSE STRUCTURE (lesson 4).
   PROPOSAL: 100% eyeball on register/loaded words; sample the rest ~1-in-5 with the gate as floor.
   JP sets the number.
3. **Structural backfill checkpoint** (belongs on structural cards, NOT the engine): οὕτω G3779,
   ἕως G2193, ἰδού G2400, εἷς G1520, + the 8 oblique pronoun forms (σοῦ/μοῦ/μέ/σέ/ὑμῶν/ἡμῶν/σοί/ὑμῖν,
   μοί G3427).
4. **ἅγιον G39 gloss check** before it builds — word_gloss reads "Holy Place," too narrow for the
   ABP-tagged holy family (the hagios G40→G39 alias target). Verify first.
5. **Ranker learns to check stamps upfront** — skip already-built words in the candidate list so the
   ro/apply passes don't re-draw prior entries.
6. **ai.py ↔ build cross-comments** — the two `_norm_book` copies disagree on bare "Jud" (ai=Judges,
   build=Jude) by design; add a cross-note in each so the divergence reads as intentional.
7. **Uncited-collocation triage rule** — batch data says most are noise (numerals, time-words); at
   ~3,900 words the eyeball cost needs a rule for which collocations actually warrant a look.

### Open finding — spelled-out book names ≠ stored code (systematic)
The model writes the natural name **"Ruth"**; the stored `verses.book` code is **`Rth`**.
`_norm_book` only re-glues *numbered* books, so a plain single-word name whose first 3
letters differ from its code (Ruth→Rth, Judges→Jdg, …) falls through to the non-canonical
hard-reject. Not a draw slip — a build-normalizer gap. FIX PENDING (deterministic name→code
map, option-1 shape) — checkpoint before landing. λαός + πρόσωπον redraw after it ships.
- **Confirms the apply-regenerates risk:** πρόσωπον passed the ro pass 39/39 clean, then the
  apply draw wrote "Ruth" and was blocked. A word can pass review and fail apply — the
  write-time gate is the real floor, not the reviewed draft.

### Dangling-lint widening + triage (2026-07-03)
Wiring the book table into the dangling recognizer lit up **18 flags across the built entries** the
old numbered-only lint was blind to. Triaged against the actual sentence (`audit_dangling_context.py`):
- **16 prose collisions** — book labels that are also everyday words / person names: Joshua, John,
  Nehemiah, Job ×3, Mark, Daniel ×3, Ruth, Esther, Son ×3, Exodus. Fixed by a `_DANGLING_SOFT`
  skip-set (bare-word scan only; the ch:vs catcher is untouched).
- **1 chapter-ref** — θεός "Psa 82's gods": a code + chapter, no verse. Now treated as a legitimate
  whole-chapter reference (`_CHAP_ONLY_RE` strips chapter refs before the dangling scan).
- **1 genuine dangling** — see fix list.
- **Finding: "better is reportable."** The old "χάριν dangling-empty across all 18" claim was only
  true of what the numbered-only lint could see — bare Ruth/Esther refs sat in shipped entries all
  along. The widened lint surfaced pre-existing debt, it didn't create it.
- **Two book codes are also English words:** `Job` and `Son` (= Song of Songs). They straddle the
  code/word line, so they can't obey "codes never excluded" cleanly. Because the chapter-strip runs
  first, every real Job/Song citation carries a number and is consumed before the bare-word scan, so
  a bare leftover is always the word — safe to soft-skip. `test_lexica_book_norm` names exactly those
  two as the only permitted code∩soft overlap.

### Fix list — advisory debt (entries stay live, no batch-close block)
- **G3962 πατήρ — dangling `Col`** ("Col — implicit" in a ref list, no number). A genuine botched
  citation, shipped this batch. Riding with the λαός/πρόσωπον redraws (a fresh πατήρ draw should not
  repeat it); falls back to debt if a redraw keeps reproducing it. Count: 1.

### Known soft spot (accepted, written down not discovered later)
- The chapter-strip means a chapter-only ref dropped **inside a citation list** now passes the
  dangling lint silently — we can't cheaply tell it from discursive whole-chapter prose. Accepted per
  the 2026-07-03 ruling (whole-chapter arguments like Psa 82 are legitimate).

### Engine notes
- **The fed sample is deterministic per word.** Both δίδωμι draws fed the identical 40-verse
  spread and the identical missed-collocation list. So a **redraw fixes drafting, never
  sample coverage** — a coverage gap (a real sense the spread never fed) survives a redraw
  and needs a sampler change or a manual eyeball, not a re-run.
