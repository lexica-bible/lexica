# Handoff — next session

## Lexica dictionary: ONE step left — rebuild the six through the reviewer

**Read memory `project_lexica_dictionary` first** — the SIX-WORD RUN block + the softened prompt
rule — before touching anything.

### Where we are (almost done)
- **Pins APPLIED + VERIFIED on PA.** The 3 frame-leakers — dikaioō (G1344), charis (G5484),
  aionios (G166) — have their neutral core hand-pinned: it leads the card, the model's framed senses
  sit below as **"Attested uses,"** the fork shows the frames cleanly with no repeated core line. JP
  confirmed the 3 cards render the neutral core first. (Commits `c777ea5` pin + `62a7a7d` a
  `show_entry` crash fix.) psychē / sarx / ekklēsia gate-ship as-is, untouched.
- **v3 PROMOTED (commit `eb09636`).** `build_lexica_def.VERSE_PROMPT` is now the proven sub-use-test
  prompt, confirmed **byte-for-byte** identical to the reviewer's frozen V3 + the trial copy
  (sha1 `32ba5b6e704a52c3`, 3637 chars) by an actual diff this round — not recollection. The reviewer's
  report label is now dynamic, so it reads "(the live engine)" for v3.

### The only remaining step — rebuild the six through the reviewer, then apply
On PA (`git pull` first to get `eb09636`):
1. `workon bible-env`
2. `export ANTHROPIC_API_KEY=$(grep -oE "sk-ant-[A-Za-z0-9_-]+" /var/www/www_lexica_bible_wsgi.py)`
3. **Review (never a blind single draw):** `python scripts/lexica_agreement.py --runs 10`
   (all six, ~$1.80, ~10–15 min). Read each word's "YOUR CALL" line — confirm **STABLE / no hole**
   (a whole sense dropping across draws). It's the proven prompt, so expect the same clean result as
   the 2026-06-25 run; the 3 pinned words may still wobble *frame* in the senses — that's fine, the
   pin leads the card. A HOLE (not a frame wobble) is the only thing that should stop the apply.
4. **If all six are clean:** `python scripts/build_lexica_def.py --apply` — rebuilds all six under v3
   (the stamp changed, so it regenerates; the 3 leakers get the pinned core on top). ~$0.18.
5. Reload, spot-check the six cards.

When the six rebuild clean on the promoted-and-diffed v3, **this whole arc is discharged.** The next
horizon is the full-dictionary build (roll out top-down by word frequency; the reviewer is the gate,
the pin pattern is the contested-word fix).

### Already decided — do NOT re-litigate
- Plan A (pure engine + agreement gate). Hand-pin only the contested *core* (surgical) — DONE for the 3.
- **No prompt-tuning the 3 to fix the leak.** Priors live in the model's training, not the verses; the
  reviewer reads *steady-vs-varying, not neutral*, so a prompt could make a core steadily commit to one
  contested frame and read "clean." A human settles a contested core either way. Revisit a prompt pass
  only when hand-pinning becomes a chore (more fork-bearers need it than not + clear benefit) — judgment,
  not a count.
- Keep the reviewer's per-draw lists in the report permanently (audit layer for the company column).

### Predictive rule (for the full build)
A fork-word leaks when its contested frame is **statable as a definition** (forensic, infused-grace,
duration) → hand-pin the core. It stays clean when the frame is a **construction on a plain sense**
(sin-nature on flesh, the-Church on assembly) → gate-ship. Pre-sort fork-bearers by this; don't find
leakers one at a time.
