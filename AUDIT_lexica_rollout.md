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
- **Batch-found:**
  - **G5207 υἱός** — the strong one. Sense 3 (a filial relationship to a divine referent — divine
    sonship) and sense 6 (the fixed "son of man" phrase) both sit on live christological ground, and
    the entry's own RANGE note already does register-adjacent work: it flags that the Gospel title's
    definiteness is carried by the article (the construction), not by any shift in what huios means.
    Register review candidate — JP's call.
  - **G3962 πατήρ** — sense 3 (God designated "father"). Rides the sense-structure adjudication item
    below; one decision covers both.
- **Prior (already built, re-flagged):**
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

### Open adjudication — πατήρ G3962 sense structure (JP's call)
The πατήρ redraw (to clear the Col dangling) also **restructured the senses**: the elder-address
sense dropped from a thin standalone sense (old draw's sense 3) to a **gloss_note** in the fresh
draw. Both are defensible; which ships is JP's call. If the old structure was right, the fix is one
`--force` redraw (gamble on the draw) or the draw-cache feature below. Flagged, not resolved.

## Batch-two prep list (closing section)
1. **Draw-cache feature (ro caches the reviewed draw, apply writes THAT draw).** Batch One produced
   **three concrete costs of apply-regenerating instead of writing the reviewed draft:**
   - πρόσωπον — passed the ro pass 39/39, then the apply draw wrote "Ruth" and was hard-rejected.
   - δίδωμι — the ro draw carried a `1Sa` dangling; needed a redraw.
   - πατήρ — the redraw silently restructured the senses (elder-address → gloss_note).
   Same root each time: the draft we review is not the draft we ship. A draw-cache removes the class.
2. **Sampling rate — set from this batch's findings (the calibration batch's actual job).** What
   Batch One showed: the write-time gate is a reliable AUTO floor — it hard-rejected every bad-
   citation draw (2 Ruth saves) with zero false blocks, and the freight-flag + dangling lints fire
   on their own. So a full human eyeball of every word is NOT required to catch hard errors. What
   still needs eyes: register/fork candidates, loaded-referent words, and sense-structure drift
   (πατήρ). PROPOSAL for JP: 100% eyeball on register/loaded-referent words; sample the rest at a
   fixed rate (suggest ~1-in-5) with the gate as the floor under the unsampled remainder. JP sets
   the number.
3. **Structural backfill (belongs on structural cards, NOT the definition engine):**
   - **οὕτω G3779** ("thus, so" — rank 49): an adverb/connector whose meaning is set by context —
     structural-card shape, like the particles.
   - **the oblique pronoun forms** (σοῦ G4675, μοῦ G3450, μέ G3165, σέ G4571, ὑμῶν G5216,
     ἡμῶν G2257, σοί G4671, ὑμῖν G5213, μοί G3427): ABP tags these as their own high-frequency
     numbers; they're pointer forms, not lexemes with a sense range. Add to the structural inventory.
4. **ἅγιον G39 gloss check** (rank 50): the word_gloss reads "Holy Place," but G39 is the ABP-tagged
   holy family (the SPLIT_LEMMA_ALIASES target for hagios G40 → G39). "Holy Place" looks too narrow
   for the whole family — verify the gloss before G39 is ever built or surfaced.

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
