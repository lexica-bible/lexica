# Rendering-override layer — design bank (2026-07-11)

Banked from JP's chat session. Status marks: **RULED** = decided; **CANDIDATE** = banked
for a later ruling, NOT approved for build. Nothing here is built until JP rules each item.

## Project framing (RULED)
- This is a **rendering-override layer over ABP**, not a standalone translation. ABP stays
  the certified base; every improvement is a diff with provenance — same philosophy as
  `abp_corrections`.
- **Display:** a viewing option within ABP, never a separate "Lexica Bible." Default view is
  pure ABP. An overridden word gets a subtle marker; tap shows ABP original + Lexica
  rendering + citation. Licensing: ABP is copyrighted (Van der Pool) — annotation/overlay is
  defensible, a derivative standalone text is not.
- **Two independent toggles** for two override classes with different epistemic status:
  - (a) **corrections** — ABP contradicts a certified verse-grounded sense or is internally
    inconsistent;
  - (b) **smooth reading** — ABP isn't wrong, just woodenly literal; a reading preference,
    OFF by default, literal always one tap away.
  Same table; a class tag distinguishes them.
- **Sequencing:** dictionary/calibration first — overrides derive from certified senses.
  Exceptions allowed pre-dictionary: grammar-class fixes (hang off the structural cards,
  already live) and errata (go to the corrections table as found).

## Architecture (RULED)
- Override applies at the **query layer**: one accessor like `get_rendering(verse, slot)`
  that checks the override table and falls back to ABP. Every view (chip, prose,
  interlinear, future views) calls it; no view carries its own correction logic.
  `verses.text` stays the oracle — never mutated.
- Table supports **two override types from day one**: slot-level (single word swap) and
  span-level (reorder/merge, e.g. articular infinitives). Do NOT design slot-only and
  migrate later.
- Every override stores a **slot-by-slot lemma mapping** (English token → Strong's). The
  validator hard-refuses any override where a lemma has no English token — "no lemma
  compressed" is machine-checked, not asserted. Loud-fail pattern, same as the definition
  engine's citation gate.
- Once surface forms are per-slot (see substrate note below), the validator additionally
  checks number/case agreement between the override and the inflected form.

## Override pipeline (RULED)
- Flag queue as a calibration byproduct: when a word ships in the dictionary, run its
  occurrences against ABP renderings and log mismatches. JP rules flags in batches;
  overrides ship with the sense citation attached. Doubles as a free second reviewer on the
  engine — a flag can mean the SENSE is wrong, not ABP.

## Pattern-class CANDIDATES (each needs ONE ruling; then CC sweeps the corpus mechanically, JP sample-checks)
1. **Age idiom** — υἱός + numeral + ἐτῶν: "was a son being twenty and three years old" →
   "was a son of twenty and three years." Drops ABP's supplied "being/old" scaffolding;
   zero lemma loss; arguably more literal than ABP. High frequency in Kings/Chronicles.
2. **Regnal formula** — ἐν τῷ + infinitive: "in his taking reign" → "when he began to
   reign." Touches essentially every king in Kings/Chronicles — highest-leverage single
   ruling identified so far.
3. **Negated purpose infinitive** — "so as to not reign" → "from reigning" or "that he
   should not reign." Fewer supplied words than ABP's own.
4. **Infinitive-absolute doubling** — "if doing you should do" (double ποιέω, e.g.
   Jer 22:4) → "if you indeed do." Both lemmas represented (participle → intensifier).
5. **Banked classes, rulings pending** — general ἐν τῷ + infinitive; substantival
   participles ("the ones being sick" → "those who were sick"); stacked genitive chains.
6. **Marginal / parked** — "put a penalty against the land" → "laid a penalty on the land"
   (low priority); v.35-type semicolon splices (punctuation/assembly territory, riskier —
   PARKED).

## Negative exemplar (validator guardrail)
Jer 22:1/22:4 singular λόγος ("this word") vs 22:5 plural ("these words") — ABP correctly
tracks the Greek's own number shift. Smoothing to uniformity would compress a real
distinction. **Number mismatch between override and lemma = hard refuse.**

## Substrate note — slot→surface alignment
The planned span-level overrides need a per-slot inflected-form substrate. **That substrate
already exists:** the `abp_surface` side table (`verse_id, position, form, translit`) holds
ABP's own printed inflected Greek per word slot, built by `scripts/build_abp_surface.py`
from the BibleHub ABP scrape, ~91% match, already LEFT-joined into `/api/chapter`. Known
limits (bank as edge cases, don't silently normalize): bh Greek is accent-only (no
breathing marks); a form is stored only when it differs from the lemma by ending (~56% of
words carry a line); `*`-slot proper nouns are skipped. See
`docs/claude/data-model.md` § abp_surface.
