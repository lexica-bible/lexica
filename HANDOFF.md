# Handoff — next session

## Lexica dictionary: verify the pin on PA, then promote v3

**Read memory `project_lexica_dictionary` first** — the SIX-WORD RUN block + the softened prompt
rule — before touching anything.

### Where we are
- The agreement reviewer (`scripts/lexica_agreement.py`, read-only, PA-only) is built + proven on the
  6 pilot words — no holes.
- **DONE this session (commit `c777ea5`, pushed):** the 3 frame-leakers — dikaioō (G1344),
  charis (G5484), aionios (G166) — have their neutral core HAND-PINNED. The fork's existing
  hand-authored `core` is now lifted to the definition's lead (`entry.pinned_core`); the model's
  framed senses sit below it under an **"Attested uses"** label; the fork drops its duplicate
  "Core (all agree)" line when pinned. Pure display — done in `assemble()`, so it applies via
  `--resplit` with NO model call. The 3 cores were confirmed fork-neutral before pinning (charis +
  aionios clean; dikaioō neutral by spanning declare *and* make on purpose).
- psychē, sarx, ekklēsia — clean cores, gate-ship as-is, untouched.

### Step 1 — PA-verify the pin (FREE, no model call — do this first)
After a normal deploy (the pull brings the new `app.js` + script):
1. `workon bible-env`
2. `python scripts/build_lexica_def.py --resplit --dry-run` — eyeball the **PINNED CORE** line on the
   3 leakers (others unchanged). No write, no cost.
3. If it reads right: `python scripts/build_lexica_def.py --resplit --apply` — re-splits all 6 from
   stored raw and writes; the 3 get the pinned core, the other 3 are rewritten identically. Free.
   **(Required — the old stored rows have no `pinned_core`; the card change alone won't show it until
   the rows are rewritten.)**
4. Reload the site, open the 3 cards (admin), confirm: neutral core LEADS, framed senses read as
   "Attested uses" below, fork shows the frames with no repeated core line.

### Step 2 — the remaining gate: promote v3 + rebuild the six through the reviewer
Only after the pin reads right on the 3 cards:
1. Promote v3 (frozen in `lexica_agreement.py` / `trial_lexica_prompt.py`) into
   `build_lexica_def.VERSE_PROMPT`. Changes the synth stamp → the six regenerate on the next `--apply`.
2. Rebuild all six THROUGH the reviewer (`lexica_agreement.py --runs 10`) — never a blind single
   draw. The pin rides on top of whatever v3 draws (it's display-side), so the leakers stay neutral-led.

### Already decided — do NOT re-litigate
- Plan A (pure engine + agreement gate). Hand-pin only the contested *core* (surgical) — DONE for the 3.
- **No prompt-tuning the 3 to fix the leak.** Priors live in the model's training, not the verses; and
  the reviewer reads *steady-vs-varying, not neutral* — a prompt could make a core steadily commit to one
  contested frame and read "clean." A human settles a contested core either way. Revisit a prompt pass
  only when hand-pinning becomes a chore (more fork-bearers need it than not + clear benefit) — judgment,
  not a count.
- **v3 stays frozen until Step 1 is verified** — promoting early auto-builds the leakers; the pin keeps
  them neutral-led, but verify the pin in isolation first (one change at a time).
- Keep the reviewer's per-draw lists in the report permanently (audit layer for the company column).

### Predictive rule (for the full build later)
A fork-word leaks when its contested frame is **statable as a definition** (forensic, infused-grace,
duration) → hand-pin the core. It stays clean when the frame is a **construction on a plain sense**
(sin-nature on flesh, the-Church on assembly) → gate-ship. Pre-sort fork-bearers by this; don't find
leakers one at a time.
