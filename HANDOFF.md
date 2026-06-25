# Handoff — next session

## Lexica dictionary: hand-pin the 3 contested cores, then promote v3

**Read memory `project_lexica_dictionary` first** — the SIX-WORD RUN block + the softened prompt
rule — before touching anything.

### Where we are
The agreement reviewer (`scripts/lexica_agreement.py`, read-only, PA-only) is built and proven on
the 6 pilot words — no holes. Ship split is decided:

- **psychē, sarx, ekklēsia** — clean cores, cleared to ship from the gate as-is.
- **dikaioō (G1344), charis (G5484), aionios (G166)** — frame-leak: the def's core pre-picks a
  contested frame draw-to-draw (dikaioō → forensic / faith-vs-law; charis → infused vs unmerited
  favor; aionios → duration vs age-to-come).

### The job, in order
1. **Hand-pin the core** of the 3 leakers — settle a neutral, attested core line for each, the way
   the fork is hand-authored, so the def stops pre-picking a frame. The other 3 need nothing.
   - **First open question to design + show JP before authoring:** where the pinned core lives and
     how it overrides the model's core — a fixed field in `build_lexica_def.CONTESTED` alongside the
     fork, vs. picking a reviewed neutral draw and storing it.
2. **Then** promote v3 (the candidate prompt frozen in `lexica_agreement.py` / `trial_lexica_prompt.py`)
   into `build_lexica_def.VERSE_PROMPT`, and **rebuild all six through the reviewer** — never a blind
   single draw.

### Already decided — do NOT re-litigate
- Plan A (pure engine + agreement gate). No Plan B hand-curation of full sense lists — hand-pin only
  the contested *core* (surgical).
- **No prompt-tuning the 3 to fix the leak.** Priors live in the model's training, not the verses;
  and the reviewer reads *steady-vs-varying, not neutral* — a prompt could make a core steadily commit
  to one contested frame and read "clean." A human settles a contested core either way. Revisit a
  prompt pass only when hand-pinning becomes a chore (more fork-bearers need it than not + clear
  benefit) — judgment, not a count.
- **v3 stays frozen until the 3 cores are pinned** — promoting early auto-builds the leakers and ships
  the leak.
- Keep the reviewer's per-draw lists in the report permanently (audit layer for the company column).

### Hard stop
Do NOT touch live `build_lexica_def.py` or promote v3 until the 3 cores are settled and shown to JP.

### Predictive rule (for the full build later)
A fork-word leaks when its contested frame is **statable as a definition** (forensic, infused-grace,
duration) → hand-pin. It stays clean when the frame is a **construction on a plain sense** (sin-nature
on flesh, the-Church on assembly) → gate-ship. Pre-sort fork-bearers by this; don't find leakers one
at a time.
