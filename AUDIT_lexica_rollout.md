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
  6. **πόλις** Gen 46:28 + Jer 26:6 — both marked "None" for rendering (the lemma may be absent as
     inflected, or carried by a different form); the G4172 build flagged them unusable as evidence.
     Same phrase-boundary / lemma-alignment family as the κύριος row above; surfaced 2026-07-03 by
     the round-2 headline pass, check with the rest in the corpus-hygiene sweep.
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
1. **Draw cache — DONE + LIVE 2026-07-03** (commit 484e226). ro (`--dry-run`) saves the model's prose
   to `~/bible-db/draws/G####.json`; `--apply` reads it, no model call, ships it byte-for-byte. Same
   split/gate/validate chain runs on the cached prose — the cache changes WHAT is gated, never WHETHER.
   Validity = a live-recomputed hash of the exact model input (prompt + fed sample + model); STALE
   (input moved) is ignored, EDITED (prose bytes changed since review) is a hard refuse. `--require-cache`
   refuses a word with no reviewed draw (ON by default under `--all`; `--allow-unreviewed` opts out).
   Single-word `--apply` stays permissive with a loud UNREVIEWED banner and writes no draw file. `--force`
   draws fresh + refreshes the cache. Client is now lazy (applying cached draws needs no API key). Kills
   the three lesson-2 risk classes. Tests: `tests/test_lexica_draw_cache.py` (no anthropic dep).
   - **E2E proof (G25 ἀγαπάω):** ro saved draw key `d226a19d`; apply printed `using reviewed draw … —
     no model call`; shipped `raw` == reviewed `raw` BYTE-IDENTICAL. G25 is now LIVE.
   - **G25 content JUDGED, flag resolved clean — SHIPPED, no redraw (JP, 2026-07-03).** ONE sense with
     directional/object range is the defensible structure for ἀγαπάω (and the anti-"agape = special
     divine love" position — the right side of that gloss fight). The `ἀλλήλων` "one another" collocation
     flag (0-in-the-fed-40) resolves on substance: the reciprocal use is NOT absent — it's covered as
     "reciprocal community obligation (Lev 19:18; Luk 6:32)"; the draw reached the same seam through
     other fed verses. What's unfed is the specific Johannine command-form instances (Joh 13:34 / 1Jn 3–4),
     not the sense. No sampler nudge.
   - **GENERALIZABLE RULE — flag + eyeball is the designed control, it just worked.** When a collocation
     flag fires and the eyeball confirms the sense IS covered via other verses: that's a PASS — record
     "flag resolved: sense present, instances unfed" and ship. Only nudge the sample when the eyeball
     finds the sense GENUINELY ABSENT. Do NOT build a force-feed mechanism preemptively — the flag +
     eyeball IS the control (flag fired → looked → covered). If batch two turns up a flagged collocation
     whose sense is really missing, THAT's when the force-feed question gets real, with a concrete case
     to design against.
   - **PREP #1 CLOSED (2026-07-03) — mechanism proven end-to-end.**
     - Draw cache shipped `484e226` — ro saves `draws/G####.json`, apply ships it verbatim, no model
       call. Six tests green (`tests/test_lexica_draw_cache.py`).
     - Validity = live-recomputed hash of the full model input; stale → redraw, edited prose → hard refuse.
     - `--require-cache` default under `--all`, opt-out `--allow-unreviewed`; `--force` refreshes cache.
     - E2E G25: ro key `d226a19d` → reviewed → apply `using reviewed draw … — no model call`, same key,
       gates 36/36 on the cached prose → BYTE-IDENTICAL. G25 live as batch-two entry #1.
     - Batch One's three failure cases (πρόσωπον fresh-draw reject, δίδωμι vanishing/appearing dangling,
       πατήρ 4→3 sense swap) are now structurally impossible on the cached path.
2. **Sampling rate proposal (from this batch).** The write-time gate is a reliable AUTO floor (2 Ruth
   saves, zero false blocks); the freight/dangling lints self-fire. So no full eyeball needed for hard
   errors. Eyes still required on: register/loaded-referent words + SENSE STRUCTURE (lesson 4).
   PROPOSAL: 100% eyeball on register/loaded words; sample the rest ~1-in-5 with the gate as floor.
   JP sets the number.
   - **Rendering-sweep design (parked, design question only — relates to sampling but doesn't replace it).**
     A cheap second pass that walks each entry's UNCITED renderings (e.g. δίδωμι "gave" 513×) and verifies
     each against a small sample of its own verses — closing the uncited-rendering hole incrementally,
     as an alternative to raising the 40-verse dial. Scope the design before deciding; not a substitute for
     the sampling-rate call above.
3. **Structural backfill checkpoint** (belongs on structural cards, NOT the engine): οὕτω G3779,
   ἕως G2193, ἰδού G2400, εἷς G1520, + the 8 oblique pronoun forms (σοῦ/μοῦ/μέ/σέ/ὑμῶν/ἡμῶν/σοί/ὑμῖν,
   μοί G3427).
4. **ἅγιον G39 gloss check** before it builds — word_gloss reads "Holy Place," too narrow for the
   ABP-tagged holy family (the hagios G40→G39 alias target). Verify first.
5. **Ranker learns to check stamps upfront** — skip already-built words in the candidate list so the
   ro/apply passes don't re-draw prior entries.
6. **ai.py ↔ build cross-comments** — the two `_norm_book` copies disagree on bare "Jud" (ai=Judges,
   build=Jude) by design; add a cross-note in each so the divergence reads as intentional.
7. **Uncited-collocation triage rule — RESOLVED 2026-07-03 (gate DESIGNED, not yet in the engine —
   checkpoint before it lands).** `scripts/audit_lexica_flags.py` (read-only) scored the 163 round-2
   uncited-collocation flags against a proposed gate. **ADOPTED: PMI ≥ 5.0 + neighbor stoplist
   (οὕτω G3779, ὅσος G3745 — extend as function words surface above the floor) + mutual dedup.**
   163 → 73 survivors (~2.8/word), read as overwhelmingly real (milk-and-honey / inherit-the-land /
   ends-of-the-earth under γῆ; "thus says the Lord Almighty" ἀμήν+παντοκράτωρ under λέγω; third-day /
   forty-days numerals under ἡμέρα; καὶ ἐγένετο narrative ὅτε/ἡνίκα under γίνομαι).
   - **PMI 5.0 HELD** after reading the near-miss band: it loses a few real formulas (υἱός+πρωτότοκος
     4.56, πόλις+πύλη 4.65, οἶκος+Ἰακώβ 4.50, λέγω+σαβαώθ 4.98) but dropping to 4.5 readmits
     ὅταν/πῶς/ἄλλος/numerals/Πέτρος — and the flag is ADVISORY (worst-miss catcher, not every-miss).
   - **Share cap DROPPED (proposed ≤20%, did 0 drops).** Every neighbor here sits under 6% of its
     target's verses — the 26 are the most frequent words in the corpus, so even οὕτω's 164 co-verses
     is 5.6% of ποιέω. Worse, it INVERTS on the rollout: on an occ≥2 rare word a neighbor covering 40%
     of its verses is the DOMINANT usage the definition must show, not noise. A ≤20% cap would suppress
     exactly the flags that matter most on precisely the words the rollout is for. Left out; may return
     FREQUENCY-CONDITIONED if a rare-word batch turns up real broad-pairing noise.
   - **Mutual dedup KEPT** in the gate though this batch never exercised it (λόγος↔γίνομαι both died on
     the PMI floor first).
   - Batch-two-prep origin was "batch data says most are noise (numerals, time-words); at ~3,900 words
     the eyeball cost needs a rule for which collocations warrant a look." That rule is the gate above.

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

## Batch Two — 20-word calibration (rollout session 1, 2026-07-06)
The session prompt's "calibration batch 1" (doc numbering: Batch Two, the batch after the 26). Cutoff
occ≥2; verbs + Hebrew held as separate tracks, so this batch is **20 nouns/adjectives**. Candidate
list from `rank_lexica_candidates.py --top 70 --skip-built` (the `--skip-built` flag added this
session — excludes the 38 live entries, count shown in the header). Verbs held out to keep the batch
homogeneous so the ~2.8-flags/word bar means one thing.

**Built against the S11 corpus state** (post-S11 prose, 28-row correction table). So a future Tier B
prose fix must run the `check_draw_citations.py` sweep against these 20 like any shipped card (the
standing rule in docs/claude/ai.md).

**The 20 (frequency order):** ἀδελφός G80 · πολύς G4183 · καρδία G2588 · ἅγιον G39 · ἔθνος G1484 ·
μέγας G3173 · ἱερεύς G2409 · οὐρανός G3772 · ὕδωρ G5204 · φωνή G5456 · ὀφθαλμός G3788 · ὄρος G3735 ·
ἔτος G2094 · ἄρχων G758 · ἔργον G2041 · ἁμαρτία G266 · ῥῆμα G4487 · δύναμις G1411 · θυγάτηρ G2364 ·
τόπος G5117. Routed OUT: **αἰών G165 → contested/fork track** (loaded "eternity" frame, noun sibling
of the forked aionios G166). Watch hardest for a disguised loaded frame at ἁμαρτία / ῥῆμα / δύναμις.

### Register-completeness findings (ranker flag gaps closed this session)
The top frequency band is function words the register didn't exclude, so they surfaced as "content."
Flagged (not built) in `rank_lexica_candidates.py`, flag-only per JP (structural cards are a separate
pipeline): 10 oblique personal-pronoun forms → `OBL` (belong to ἐγώ/σύ/ἡμεῖς/ὑμεῖς, so the structural
backfill can't double-count them); ὑμεῖς/ἡμεῖς → `FUNC`; ἕως/ἰδού/εἷς/οὕτω/δύο → `STRC`; ἐνώπιον →
`STRC` (preposition); ἐκεῖ/νῦν/ἔτι → `STRC` (deictic adverbs). These are the queued structural-backfill
set, now visible in the ranker.

### G80 ἀδελφός — LIVE (4 senses, sense 4 advisory-thin). The calibration lesson of the batch.
Shipped the attempt-3 draw (key d4eb6ed8), no model call on apply, gate 40/40, stamp current. Senses:
sibling / ethnic-institutional group / messianic-apostolic community / "equivalent to a sibling" (thin,
Psa 35:14); LXX note on sense 2.
- **The saga.** First draw = 3 senses + a dangling "Jas"; the redraw to clear the dangling flipped it
  to 4 (added the Psa 35:14 figurative). **All 13 draws (reviewer + redraws) and the ship share key
  d4eb6ed8** — the key pins the INPUT, not the output; same fed sample → same key every draw. So
  `--from-draw d4eb6ed8` did NOT pick attempt 3 by key; the on-disk bytes attempt 3's `--dry-run
  --force` last wrote are what shipped. **Disk state is the selector, the key is the gate.**
- **The reviewer read.** `lexica_agreement.py --runs 10`: count {3:6, 4:4}, but the **3 core jobs
  present + distinct in ALL 10** — the only wobble is Psa 35:14 (10/10 verse support, no stable home:
  folds into 2 or 3, or splits as a 4th). A fold, not a hole.
- **The reversal (logged honestly).** First ruling was "STABLE at 3, ship 3, Psa 35:14 in range." That
  over-read the 10-run: "6/10 fold it" is a plurality of PRESENTATION styles, not a verdict the 4th job
  is false. The manufacture bar guards HOLLOW senses; Psa 35:14 has 10/10 support + a real comparative
  use, so sense 4 is THIN not manufactured — same class as batch-one χείρ #4 / πόλις #3 (shipped
  advisory-thin).
- **RERULED BAR (banked, generalizes to the other 19): the reviewer gates CORE STRUCTURE, not surface
  count.** A draw ships if the stable jobs are present + distinct (sibling/ethnic/faith, LXX on 2) and
  any flicker-sense carries the thin flag. Attempt 3 passes; attempt 2's **merge-3** (ethnic+faith
  collapsed, Psa 35:14+Heb 8:11 split into a "moral context" sense) FAILS it — a 3-count that holed a
  stable distinction. "Match the majority count" was the wrong bar.
- **OFF-DISTRIBUTION finding (about the reviewer, not just G80).** Attempt 2's merge-3 shape did NOT
  appear in any of the reviewer's 10 draws (ethnic + faith never share a sense in the ground truth). A
  live draw produced a shape outside the observed 10 → the 10-run may UNDER-SAMPLE the draw space.
- **FED-40 sample question (banked for the retro).** The 40-verse (20 OT / 20 NT) spread is pragmatic,
  not derived — for a 1000-occ word it's a ~4% sample. The batch test: do collocation flags resolve as
  UNFED instances (fine) or GENUINELY-ABSENT senses (sample too thin)? Log the per-word distinction as
  it accumulates; answer at the retro alongside the reviewer-sample question. **G80: both flags
  (δώδεκα, παρακαλέω) resolved as unfed — the sense is present via other fed verses.**
- **RETRO question.** G80's mid-range boundary wanders across three shapes at 4/3/3 (clean-3 / merge-3 /
  4-sense); it took the reviewer + 3 redraws to settle one word. If the other 19 behave like this,
  **per-word reviewer runs go from exceptional to standard** — decide at the batch retro.
- **Redraw-loop discipline.** Drawing until the structure matches a pre-established consensus is
  audit-against-known-structure, not shopping (every draw got the full audit); capped at 3 off-target
  pulls before stopping to JP. `--from-draw` refuses EDITED drafts by design, so "hand-tune the split"
  can never mean editing the JSON — a real constraint is sampler/prompt-side (frozen VERSE_PROMPT →
  re-prove cycle) or a new mechanism, both JP design decisions.

### Reviewer tiering — RULED 2026-07-06 (batch-wide procedure)
Every word gets a **minimum 3 reviewer runs** (`lexica_agreement.py --runs 3`) before ship; escalate to
**10** on any appear/vanish, merge, or job-boundary wobble in the 3. **No word ships on a single draft's
structure** — G80 and πολύς both proved a clean-looking single draw is one shape of several (πολύς caught
its off-distribution over-split draft the word after the ruling was made). Cost ~$0.09/word floor, ~$2 for
the batch — cheap insurance that also feeds the retro with data from all 20, not only the words that wobbled
in front of us. Prediction under test (see G4183): one-dimension concrete nouns agree tightly at 3;
multi-shallow-axis words escalate.

### G4183 πολύς — PARKED-HARD (stable 2, but the range won't hold the folds). The batch's first pipeline-resistant word.
Reviewer `--runs 10`: count {2:3, 3:4, 4:2, 5:1}, mean 3.1. **Stable core = 2 jobs at 10/10** — (1) large in
number/count, (2) large in degree/intensity/magnitude. Every 3rd+ cut is unstable and differently carved:
comparative (4/10), adverbial (2/10), temporal "long time" (3/10), collective-mass (1/10), populous-nation
(1/10). No job holes; the extras all fold into the core 2.
- **Ship target set** = 2 senses + range carrying comparative/adverbial/temporal as folded facets. Three
  redraws for it: attempts **3 / 5 / 3** senses — cap hit, none was 2. PARKED.
- **THE FINDING (bigger than short odds): range-completeness is the binding constraint, not sense-count.**
  Across the pulls the temporal "long" use (13× rendering) was made its own thin sense (attempt 2), dropped
  entirely (attempt 3, flagged 'long' 13× uncited), or would bury under "degree" (the 2-sense draws). **No
  single draw holds the stable 2 core AND keeps all folded facets visible in the range.** The
  2-sense-with-full-range draft may barely exist in the draw space.
- **PARK rationale = batch integrity, not indecision.** Option C (steer VERSE_PROMPT) mid-batch would draw
  later words from a different engine than earlier ones — contaminating the comparability the batch exists to
  build; a prompt steer is a BETWEEN-batch change with a re-prove cycle, informed by all 20 words. Option B
  (higher-cap blind fishing) runs straight into the range-completeness finding — the target draft may not
  exist to fish for. So πολύς ships at end-of-batch or after, once the mechanism is decided on full-batch
  evidence.
- **FALSIFIED-PREDICTION REFINEMENT (banked).** Predicted grammar-driven boundaries → high agreement; FALSE
  for πολύς. The number-vs-degree split IS rock-stable; the finer cuts (comparative/adverbial/temporal) are
  not. So the wobble axis is NOT semantic-seam-vs-grammar — it's **how many shallow analytical cuts a word's
  usage offers.** Testable prediction for the rest: one-dimension concrete nouns (θυγάτηρ, ὕδωρ, ὄρος) agree
  tightly; multi-shallow-axis words wobble on cut-count regardless of whether the cuts are grammar-keyed.
- **2-vs-3 UNDER STRAIN (retro).** Holding the pre-registered fold-to-range, but logging honestly that it
  assumed folding was FREE — the pulls showed fold-AND-stay-visible is the hard part. If the retro rules that
  comparative-class MULTI-VERSE flickers ship better as standing senses, that revisits G80's Psa 35:14 verdict
  too (asymmetry: G80 = 1 verse, πολύς comparative = a trio Heb 11:4 / Luk 11:31 / 2Ti 2:16 — a real difference).
- **Flag rate** (per the ≥5.0 record): πολύς = **2 flags** (chrónos 6.13, hýdōr 5.05); the sub-5.0
  collocations (éthnos / pisteúō / dóxa) are stored-informational, not counted.

### G3173 μέγας — LIVE (4 senses, one-draw ship under the four gates). Multi-shallow-axis wobble, no holes.
Shipped the first fresh draft (key 3dc9ec8a), no model call on apply, gate 40/40, stamp current, 40 verses.
4 senses: (1) magnitude — large in size/volume/force/degree; (2) rank/status — high in importance/rank/
significance; (3) senior in age or birth order; (4) greater/greatest (comparative & superlative).
- **REVIEWER (clean --runs 10 after the parser fix; the FIRST run was 5/10 format-broken — see the parser
  fix below).** Spread {3:5, 4:3, 5:2}, mean 3.7, ZERO holes (every wobble verse folds). Stable core =
  magnitude + rank/status, both 10/10 every draw. Third cluster = the greater/greatest/elder material
  (Jos 19:9, 1Co 13:13, 2Ch 17:12, 1Sa 17:13, Exo 2:11, Heb 8:11) gets its own slot in 8/10 draws —
  carved as "comparative" (7/10) and/or "senior in age" (4/10 standalone). The shipped draft splits it
  into age (#3) + comparative (#4); that finer carving is WITHIN the reviewer's distribution (draws
  2/7/8/9 split them) → gate-4 ships-as-drawn. Adverbial "greatly" (1Sa 10:2) + weighty-significance =
  shallow facets that fold into magnitude/degree + range. **CONFIRMS the multi-shallow-axis prediction:
  wobbled 3/4/5 on cut-count, spine stable, all folds.** Answer to "does age hold its own slot?": NOT on
  its own (4/10) — it's a sub-cut of the greatness cluster; not forced as a standalone.
- **Four gates PASS.** No holes / no merges (magnitude, status, greatness all distinct). Completeness:
  age #3, comparative #4, weighty folded in #2 + range, adverbial folds in #1 — coverage audit "10 top
  renderings, 0 uncited" (gate-3 detector finds nothing dropped). Citations 40/40, dangling empty, 4
  senses (0 thin, 0 circular), senses ≤ occ, not a loaded word.
- **DOUBLE-SHELF: 2Ch 17:12 in senses [2, 4] — ruled BRIDGE, both homes kept.** "Jehoshaphat waxed great
  exceedingly" = status (#2) expressed through a growing-greater/comparative form (#4); mirrors the verse's
  own migration in the reviewer. **Seam register: 2Ch 17:12 double-shelved [2,4], ruled bridge, precedent
  Eph 2:11 / 1Jn 2:20.** Detector's second live fire; adjudicated at ship.
- **Flag rate 3 counted** (mikrón PMI 6.7, krázō 6.02, phóbos 5.49; thálassa 4.61 informational) — ALL
  resolve as unfed instances of magnitude: great-vs-small pairing (mikrón), great/loud voice (krázō), great
  fear (phóbos), the great sea (thálassa). Sense present via other fed verses; the high count is the fed-40
  under-sampling the "great + X" collocations, same shape as G39's 7. No sampler nudge. Data point for the
  fed-40 retro.
- **Corpus-hygiene yield (symmetric audit, free):** gloss_notes flag "saying" (Eze 3:12 — μέγας modifies
  "quake", a translation-parse divergence) and "strong" (Dan 7:7 — modifies "teeth", separate predicate).
  Translation mistags, not word divergence; same free-audit family as batch one's tagging-error list.
- **STYLE WATCH — slash-headlines (note-and-batch, opened at ἅγιον).** ἅγιον shipped with a "set apart /
  expansion" template stamped across all 4 headlines (cosmetic hedge-pattern, style-property). μέγας sense 4
  "Greater / greatest (comparative and superlative)" — borderline, grammatical-pair notation, defensible.
  Counter: **2 words, 2 sightings, 1 bad / 1 borderline.** Disposition: NO gate change mid-batch (trajectory
  data — style gates fish, πολύς capped on a style-class constraint); fold a headline-prose instruction into
  V4 if/when the prompt revises for other reasons. Revisit sooner if the slash pattern recurs in bad form.

### PROMPT V3 → V4 (2026-07-07) — style-only bump, no-slash headlines. Style-watch trigger tripped.
The slash-headline style-watch (opened at ἅγιον, μέγας sense 4 the second sighting) tripped; JP ruled
the note-and-batch disposition dead and V4 ships BEFORE ἱερεύς's reviewer floor.
- **THE STEER — a segregated "Formatting (senses and range)" block** placed AFTER the whole Output list
  (away from the semantic Method/Constraints AND from the Gloss-notes bullet, so slash-quoting like
  "place / places" in gloss_notes stays legal). Positive phrasing throughout — names what good looks like,
  not just bans (pure bans invite substitute hedges). Five points in one pass:
  (1) **headline shape** — one capitalized head phrase, elaboration set off with an em-dash (the μέγας
  pattern named as the norm); (2) **commit to one phrasing** — join a real grammatical pair with "and" or
  a parenthesis, never a slash or slash-apposition; (3) **sub-uses** — one consistent lead-in, "Sub-use:";
  (4) **citation flow** — refs in parens, an example phrase paired with its own ref inline
  ("(1Co 13:13: the greatest of these)") over long semicolon chains; (5) **Range** — keep the current
  concrete-end → extended-end → what-moves-it paragraph (a "keep doing this", not a fix).
  (First shipped as a single Senses-bullet line, then expanded in place to the block before ἱερεύς drew —
  still V4, nothing produced under the one-liner, zero rework.)
- **VALIDATION (control-fire for the block):** ἱερεύς G2409's first V4 draw gets a FORMATTING audit against
  all five points alongside the four gates; both audits reported when the draw lands.
- **CONTROL-FIRE PARTIAL RESULT — 4 of 5 landing, looking good.** ἱερεύς draw-1 raw (even though it 0'd on
  the header drift) shows the block steering right: **em-dash headlines ✓, "Sub-use:" lead-ins consistent
  ✓, no slashes ✓, citation flow clean ✓** — plus it caught a "seven"/ἑπτά mistag as free hygiene. The 5th
  point (Range shape) awaits a fully-parsed draft. The block is steering the right things.
- **WATCH ITEM — V4 header question: CLOSED 2026-07-07.** ἱερεύς's clean `--runs 10` came back 10/10 parsed,
  ZERO breaks (spread {1:3,2:3,3:4} sums to 10), after the first floor's 2/3 drop. That reads as small-sample
  variance, not a systematic V4 effect — the header drop did not recur on the next full run. Combined with
  the parser fallback making header-omission harmless regardless, one more clean word was the bar and this
  was it. Closed. (Formal header-emit tracking would need raw inspection; deprioritized — it's moot now.)
- **CONTENT SIGNAL (through the breakage):** ἱερεύς's 2 readable draws (the parsed draw 2 + the inspected
  draw 1) MATCH on the referent axis — general cultic office (pagan folded as sub-use) / Melchizedek-
  perpetual / collective-Revelation. 2 of 2 on the predicted role-noun axis; trajectory holding, the clean
  floor after the fix confirms.
- **SCOPE: style-only, ZERO rework.** No structure/method change. No unshipped V3 verdicts exist —
  ἔθνος + μέγας shipped, ἱερεύς not yet run — so V4-now costs no redraw and needs no carry-forward
  exception. Full discipline, clean generation boundary.
- **SHIPPED ENTRIES NOT RETRO-EDITED.** ἅγιον + μέγας keep their slash headlines (review-what-ships);
  they'd only get the V4 phrasing if ever legitimately redrawn.
- **MECHANICS.** `VERSE_PROMPT` (engine) + the reviewer's frozen copy edited byte-identical; copy renamed
  `V3_PROMPT`→`V4_PROMPT`, `PROMPTS`/`--prompt` default flipped to `v4` (runs + saved files now stamp
  "V4"). The vestigial trial-rig drift check (`_check_v3_sync`, comparing to the throwaway
  `trial_lexica_prompt`) retired for `_check_prompt_sync`, which asserts the live invariant that matters
  now: `V4_PROMPT == B.VERSE_PROMPT` (reviewer must draw under the engine's exact prompt). Verified
  byte-identical + sync-silent locally. Prompt-hash `stamp` auto-rolls; old cached draws go stale
  (harmless — shipped words already written, ἱερεύς draws fresh under V4).

### REVIEWER PARSER DRIFT FIX (2026-07-07) — μέγας 10-run surfaced audit-tooling debt, engine clean
The μέγας G3173 `--runs 10` came back `!! 5 draw(s) parsed to 0 senses (format break): [1,4,6,7,8]`.
- **ROOT CAUSE (logged): the reviewer reimplemented the sense-split with the bold-only `_HEADLINE_RE`
  instead of reusing `_sense_spans`** — a batch-one reuse-rule violation. Those 5 draws numbered their
  senses `1. **headline**` (number OUTSIDE the bold) under a `**Senses:**` header; `_HEADLINE_RE` wants
  `**1. headline**` (number INSIDE), matched nothing, and `per_sense` threw away 5 rich 4-sense answers.
  Confirmed by inspecting draw 1's saved raw — a complete magnitude/rank/age/comparative answer, not
  truncation. **The SHIP path was never at risk:** `split_definition` → `_sense_spans` has a plain /
  number-outside-bold fallback (`_PLAIN_HDR`) that parses this format fine. This was audit-tooling debt,
  not an engine bug — the same split3 drift class, one layer up in the reviewer's parser.
- **FIX:** `lexica_agreement.per_sense` now reuses `B._sense_spans` (no second copy of the split).
  Locked by `tests/test_lexica_agreement_parse.py` (added to CI + pre-commit lists) — control-tested:
  the fixture is a real draw-1 snippet, and the test permanently asserts the bold-only regex sees ZERO
  in it (so `== 4` can't pass for the wrong reason). Demonstrated old→0 / new→4 before landing.
- **SECOND COPY FLAGGED, NOT TOUCHED:** `audit_lxx_provenance.py:31` `sense_chunks` has the SAME
  bold-only reimplementation (same latent 0-parse bug). Out of the ship path — queued behind the μέγας
  pin, to fix with its own control test, deliberately NOT folded in blind this turn.
- **TOOL-HEALTH FINDING (banked).** Both halves of the posture worked: the loud `!! 0 senses` banner
  kept the polluted aggregate (mean 1.9, every "drops in [1,4,6,7,8]" = the dead draws) from being read
  as semantics, and the 8 CLEAN draws (3 first-run + 5 here) already told the truth (stable 2 magnitude +
  rank/status, age semi-stable, shallow-axis tail folds). Diagnosis was one read-only inspect, not a
  blind re-roll.

### SECOND PARSER FIX (2026-07-07) — header-OMISSION drift, surfaced by ἱερεύς's first V4 floor
ἱερεύς G2409 `--runs 3` under V4 came back 2/3 "0 senses" — a DIFFERENT drift from the first fix.
- **ROOT CAUSE: `split_definition` keyed the senses off a "Senses:" SECTION HEADER; some drafts omit it**
  and dive straight into a title line (`**G2409 hiereús**`, which the prompt asked them NOT to write) +
  bold-numbered senses `**1. … — …**` (number INSIDE the bold this time). No "Senses" header → empty
  block → 0 senses, upstream of the first fix (which only helps once a block is extracted). The draft's
  CONTENT was excellent (clean 3-sense read, working "Sub-use:" lead-ins, caught a "seven"/ἑπτά mistag).
- **SHIP PATH SAFE (confirmed):** `validate_entry` refuses a header-less draft ("sense_headlines empty")
  rather than mis-shipping — no card was ever at risk. Reviewer-only silent 0, again.
- **FIX:** `split_definition` now captures the pre-section `preamble` and, when NO "Senses" section
  exists, falls back to it — GUARDED by `_sense_spans(pre)` so a stray prose preamble is never mistaken
  for senses, and zero change when a "Senses" header is present. Fixes reviewer AND ship path in one
  place. Locked by `test_lexica_agreement_parse.py` (real ἱερεύς draw-1 fixture; control asserts NO
  "Senses" header present so the fallback path is genuinely exercised; old→0 / new→3 demonstrated).
- **RATIFIED PRINCIPLE (JP):** the PARSER owns tolerance to real model variance; the PROMPT owns steering
  the ideal. Fixing header-omission at the prompt is whack-a-mole against a coin-flip (draw 2 emitted the
  header, draws 1/3 didn't — stochastic); fixing it in the parser makes it permanently moot. Same lesson
  as the first fix, one layer up.

### G2409 ἱερεύς — LIVE (3 senses, granularity-as-drawn). First concrete-role word; framework held with no new rule.
Shipped the fresh draft (key 1dec7a91), no model call on apply, gate 40/40, stamp current, 40 verses. 3
senses: (1) cultic office / priest (referent sub-uses pagan/Midian + certification folded in); (2)
perpetual, archetypal office (Melchizedek + Heb 7); (3) collective/corporate priestly standing (Rev).
- **REVIEWER `--runs 10` (after both parser fixes; first 3-run was 2/3 header-broken → drove the second
  parser fix).** Spread {1:3, 2:3, 3:4}, mean 2.1. Core "cultic office" = 10/10 (unanimous). Melchizedek =
  own slot only 4/10; collective = own slot 5/10; institutional-authorities cluster = own slot 1/10.
  Neither cluster cleared the ~7/10 bar → **THIRD BUCKET (granularity-as-drawn)** per the pre-registered
  rule: bank "cultic office stable; Melchizedek + collective visible at sense-OR-named-sub-use tier; ship
  draw's carve stands as long as gates clear, whatever the count." **NO HOLES** — both clusters present in
  ALL 10 (own sense, folded into office, or merged together in draw 7); the "promotion" wobble is pure
  TIER-flicker, content never missing. The shipped 3-sense carve is one of the 4/10 clean shapes.
- **PREDICTION RECORD — role-noun hypothesis fully settled.** Referent-axis wobble ✓, no shallow-cut
  fishing ✓, tight-ish core ✓. Truth-properties converged (core 10/10); the ONLY instability was tier
  assignment — a granularity property, exactly what granularity-as-drawn absorbs. **The framework needed
  NO new rule for a new word class (first concrete role-noun) — the strongest evidence for the framework.**
  Contrast μέγας (multi-shallow-axis *carving*) vs ἱερεύς (*promotion*): different wobble shapes, same gates.
- **DETECTOR: Gen 14:18 in senses [1,2] — ruled BRIDGE, both homes kept.** The verse is the hinge of the
  word's own history: Melchizedek holds the office in Genesis and becomes the archetype the Psalm + Hebrews
  build on. **FIRST model-self-annotated seam** — the draft wrote "Gen 14:18 [echoed]" in sense 2, marking
  its own bridge (the prior 3 needed the detector to surface them). **Seam register: Gen 14:18 [1,2], ruled
  bridge, model-annotated, 4th entry — cleanest yet.**
- **DANGLING "Heb" — ACCEPTED per-instance (option A), Psa-82 discourse class.** The flag is the phrase "in
  Hebrews the lemma is used contrastively" (sense 2 sub-use), with Heb 7:21 cited in the SAME clause —
  legitimate discourse about the book's argument, not a botched citation. Dangling is flag-only (no hard
  block). **LINT PRINCIPLE BANKED: do NOT soft-skip a book abbreviation that is load-bearing in the same
  entry** — "Heb" appears in 7 real citations here; soft-skipping it (option C) would blind the lint exactly
  where a dropped chapter number is most likely. Keep the flag armed globally, accept this instance. Redraw
  (option B) correctly priced out: gambling a 4/10-likelihood clean carve over a flag-only cosmetic hit is
  the πολύς lesson inverted.
- **REGISTER — both-ways bar HELD through reviewer floor (10 draws) AND ship draw**, on the most loaded
  cluster in the word (Melchizedek/perpetual priesthood). All headlines descriptive — "exemplified by
  Melchizedek and then predicated of another figure on that same basis," "one *described as*," "*said to*
  occupy the same order." Never names Christ, never editorializes. **SECOND word where the neutrality bar
  generalized beyond CONTESTED status without being asked** (after ἔθνος's "gentiles" freight handling).
- **Flags: 3 counted** (haphḗ 6.53, katharízō 5.79, énanti 5.22; epitíthēmi/aírō/horáō/μέγας < 5.0
  informational) — ALL Levitical ritual-duty words (leprosy-mark inspection, cleansing, laying-on,
  offering) folding into sense 1's cultic-office range ("certifying purity" named there). Same fed-40
  under-sampling of dense Leviticus vocab as G39. **μέγας = "the great [high] priest" is NOT a missing
  sense** — ἱερεύς means "priest," μέγας supplies "high"; the reviewer's 10 draws never carved a high-priest
  sense. Resolves clean, no nudge.
- **FORMATTING CONTROL-FIRE — V4 VALIDATED, 5/5 on the raw text.** (1) headlines head—em-dash—elaboration ✓;
  (2) no slashes in headlines ✓; (3) "Sub-use:" lead-in consistent 3× ✓; (4) citation flow ✓ — **under
  maximum load (27-verse grounding) the model differentiated bare-list-for-grounding from inline-example-
  for-illustration ("the priest of Midian (Exo 2:16)") on its own — judgment, not mere compliance**; (5)
  range concrete→extended→what-moves-it, textbook ✓. The block is steering the right things.
  - **Body-prose slash — style-watch scoping note (NOT a violation).** "institutional/hereditary" (range) +
    "Zeus/Dia" (sub-use) are slashes in BODY prose; the V4 rule is headline-scoped, so neither breaks it.
    Both are legitimate pair-notation (not the ἅγιον hedge template), so JP is slow to extend the rule to
    body prose. Logged as a scoping question for a future rev, not a fix.

### STYLE WATCH #2 — term-of-art echo (opened at ἱερεύς, 2026-07-07)
JP's ruling on ἱερεύς sense 3 "corporate": CLEARED on neutrality (plain of-a-body sense, self-defined in
place, referent question left open — both-ways satisfied), but LOGGED as a style concern: words with a life
as terms of art in theological debate ("corporate" → corporate election / corporate personality) carry an
echo even when used innocently. **TRIPPED SAME SESSION (2026-07-07):** JP re-counted the shipped ἱερεύς card
— sense 3 "corporate" + the range clause "corporate identity ascribed to a redeemed people" = 2–3 echo
sightings on ONE card, threshold met. → V5 style line shipped (below). NOT a gate, NOT a redraw trigger, no
retro-edit to ἱερεύς.

### PROMPT V4 → V5 (2026-07-07) — style-only, term-of-art line. Style-watch #2 tripped.
- **THE LINE (Formatting block, same segregated place as the V4 lines):** "Prefer descriptive vocabulary
  with no life as a term of art in theological debate; where a plain word carries the sense, use it (e.g.
  'applied to a group' rather than 'corporate')." Positive phrasing, one example, tight.
- **SCOPE: style-only, ZERO rework.** Word boundary — no unshipped V4 verdicts (ἱερεύς shipped; οὐρανός
  floor not yet run). Full discipline, no carry-forward exception (same justification as V3→V4).
- **MECHANICS.** `VERSE_PROMPT` + reviewer copy edited byte-identical; `V4_PROMPT`→`V5_PROMPT`,
  `PROMPTS`/`--prompt` default → `v5`, sync check repointed to `V5_PROMPT == B.VERSE_PROMPT`. Block title
  widened to "layout and wording" to admit the vocabulary rule. Verified byte-identical + sync-silent.
- **CONTROL-FIRE: the formatting audit is now 6 POINTS** — the echo check joins headline-shape, no-slash,
  sub-use lead-in, citation-flow, range-shape. οὐρανός's first draw gets all six alongside the four gates.

### REDRAW QUEUE (post-batch, optional — under V5)
Cosmetic-only entries shipped under earlier prompt generations, each cleared on neutrality/content, NOT
hand-edited (review-what-ships holds). Queued for OPTIONAL redraw under V5 after the batch closes:
- **ἅγιον G39** (V3) — slash-headlines (the "set apart / …" template across all 4).
- **μέγας G3173** (V4) — slash-headline (sense 4 "Greater / greatest (comparative and superlative)").
- **ἱερεύς G2409** (V4) — term-of-art echo ("corporate" ×2).
(ἱερεύς occurrence-count "32" note: that was JP's NT filter, not a data issue — no action.)

### APPARATUS FINDINGS — surfaced by οὐρανός G3772 (2026-07-07). The session's biggest yield.
Three apparatus-level findings, independent of how the οὐρανός card finally ships:
- **NEW DEFECT CLASS — unverifiable-assertion in gloss_notes.** The citation gate verifies *references*;
  NOTHING verifies *claims about the corpus* (capitalization practice, translation behavior, form-field
  assertions). Gloss_notes are where the engine makes factual claims in its OWN voice, and those can be
  plausible-but-fabricated. Case: οὐρανός attempt-1 gloss_notes claimed the capitalized "Heaven" (3×) was
  "an editorial decision imported by the translation [implying] a proper name or distinct theological
  referent." Position check (Gen 1:8 / Job 11:8 / Pro 25:3) showed it was **two sentence-starts + one
  naming act** — the premise was fabricated. **The note's CONCLUSION was right** (same word, no distinct
  referent — it even flattered our no-metonym ruling), **built on a false premise.** → REDRAW (attempt 1
  of 3 burned). Caught by a human read of the raw (JP's sentence-position question) — the judge-on-the-raw
  rule paying out; the pipeline had it green.
  - **"AGREEMENT IS NOT EVIDENCE."** The same note that was a triumph an hour earlier (rejecting a
    manufactured metonym *unprompted*) was right-conclusion-on-fabricated-premise. Gloss_notes that flatter
    our existing rulings get the SAME verification as ones that don't.
  - **RETRO CANDIDATE:** the capitalization case is mechanizable (verse text is in the DB, sentence-initial
    is testable), but the general class (engine asserts something about the translation) lands as a
    **standing manual check: gloss_notes making factual claims about translation practice get spot-verified
    before ship.** Cheap rule; fired once already.
- **BLIND-SPOT, REFINED — bare-substitution only.** Earlier framed as "headword-substitution uses are
  invisible to the whole apparatus." REFINED: "kingdom of heaven" HAS a signature neighbor (βασιλεία), and
  the collocation flag CAUGHT it (basileía uncited, 33v, PMI 5.86) — resolved clean as phrase-level
  periphrasis (divine-realm sense present; Son-of-Man precedent, no lemma sense). So the true blind spot is
  only *bare* substitution with NO signature collocate (Luk 15:18 "sinned against heaven"). Minor + unfed;
  filed to the substitution-probe retro, not a per-card patch.
- **METHOD NOTE / STANDING RULE — "no draw surfaced it" ≠ "unfed."** Absorption and absence look identical
  from draw output; only a read of the FED LIST distinguishes them. **Unfed claims are verified against the
  fed list, not inferred from draw silence.** Cheap rule; today it converted a guess (metonym "unfed") into
  a verified finding (fed-40 dumped + read, no metonym verse present; closest = Jas 5:12 "swear by heaven" =
  oath-by-the-throne, a divine-realm sub-use, not agent-substitution).

### GLOSS-SET CASE-FOLD (2026-07-07) — root fix for the gloss_notes fabrication (option A)
Two prompt generations produced two "Heaven"-capitalization fabrications → the stimulus is in the INPUT,
not the model. Root: `gloss_set` grouped on `english_head`, so a sentence-initial/naming capital ("Heaven"
3×) surfaced as a rendering DISTINCT from "heaven" (636×), and the engine invented a rationale for it.
- **THE FIX (single-source — `gloss_set` in build_lexica_def, imported by the reviewer, so no dual-copy
  ritual):** fold case-variants of the same rendering, keep the most-frequent surface form as the label
  (rows arrive count-DESC → first-seen wins), sum the counts. Folds the EVIDENCE SUMMARY only — citation
  verse text stays verbatim (the corpus is untouched; we fold the summary, not the Bible). Locked by
  `tests/test_lexica_glossset_fold.py` (added to CI + pre-commit): real G3772/G39 fixtures, a CONTROL
  asserting the raw table genuinely holds the split, old→`heaven(6),Heaven(3)` / new→`heaven(9)` shown.
- **CONFIRM-CHECK GATE (ran BEFORE landing, full rollout population = 47 words).** Only 3 case-splits
  exist, ALL artifact-class — and the referent-fork class (God/god, Lord/lord, Spirit/spirit) is ABSENT,
  because those lemmas are CONTESTED/excluded (the safety argument, verified not assumed):
  - **γῆ 'Earth' (1×)** — Gen 1:10 "God called the dry land, Earth." Naming. Artifact.
  - **οὐρανός 'Heaven' (3×)** — Gen 1:8 naming + Job 11:8 / Pro 25:3 sentence-initial. Artifact.
  - **ἅγιον 'Holy' (9×)** — 8 clean (Isa 6:3 / Rev 4:8 trisagion quote-initial; Isa 33:5 / 57:15 / Jer 2:3
    sentence-initial; Isa 60:14 / 62:12 / Zec 14:20 title-phrase "Holy People" / "Holy to the LORD").
    **Luk 1:35 "Holy spirit shall come upon you" — EXAMINED INDIVIDUALLY under the spirit-frame bar** (the
    one sweep verse touching an armed constraint). RULED artifact-class for the fold: the πνεῦμα-fork
    attaches to the NOUN/phrase (person-Spirit vs power), never to the adjective; ἅγιον's lemma meaning
    ("set apart, of the divine sphere") is identical either way, and the shipped ἅγιον sense 4 already
    ships both-ways-neutral on "holy spirit" phrases. Folding gloss-set case deletes no verse, no text,
    and nothing the fork machinery (CONTESTED register on the spirit lemmas) uses. **The eyeball gate
    earned its keep here — confidence would have been right 8× and unexamined on the 1 verse where
    unexamined is unacceptable.**
- **REVIEWER-VALIDITY RULING (said out loud, not assumed):** the οὐρανός 10-run that banked core-2 ran with
  the case-split IN the fed evidence. **Verdict survives** — the fabrication showed up in gloss_notes, never
  in sense structure; all 10 draws carved the same sky + divine-realm core from CONTEXT (the prompt reasons
  from context, gloss set is secondary). The fold merges one rendering's count; it cannot move
  context-driven structure. No re-run needed.
- **SCOPE NOTE:** shipped cards are NOT retro-changed by this — the fold only affects FUTURE draws. A shipped
  card with a latent case-artifact note (if any) would be caught by the standing gloss_notes assertion-check
  on its next redraw, not auto-fixed here.

### G3772 οὐρανός — LIVE (3 senses, attempt 3). The batch's strongest fix-the-input case study.
Shipped the attempt-3 draft (key 663a2977), no model call on apply, gate 34/34, stamp current, 34 verses.
3 senses: (1) sky/aerial expanse; (2) domain of divine presence (C = eschatological inheritance folded in
as a named sub-use); (3) natural sky as a figure (Lev 26:19 "heaven as iron").
- **REVIEWER (`--runs 3` → `--runs 10`, tightest core of the batch).** Spread {2:4, 3:4, 4:2}, mean 2.8.
  Core-2 = physical sky + divine realm, BOTH 10/10. C (eschatological) own-slot 4/10, D (personified
  heavens) own-slot 3/10 — neither clears ~7/10 → **THIRD BUCKET (granularity-as-drawn)**. No holes;
  role/realm-noun prediction held (referent-realm axis, cleaner core than ἱερεύς, two flicker facets).
- **THE THREE-ATTEMPT SAGA (a truth-defect redraw loop, NOT a granularity loop).**
  - **attempt 1** — clean stable-2 + C-as-sense-3, BUT gloss_notes fabricated an "editorial capitalization"
    claim about "Heaven" (3×). Position check (Gen 1:8 naming + Job 11:8 / Pro 25:3 sentence-initial) showed
    the premise false → REJECT. (Caught by JP's judge-on-the-raw position question; pipeline was green.)
  - **attempt 2** — reproduced the fabrication (testably worse: claimed the capital marks a sky-vs-abode
    distinction, but all 3 capitals are the SKY sense) + an off-distribution source-vs-dwelling realm-split.
    The TELL fired → targeted look, not a blind attempt 3.
  - **ROOT FIX (gloss-set case-fold, option A)** — see the fold entry above. Stimulus deleted.
  - **attempt 3 — fabrication GONE on the very next pull.** "2 renderings" (was 3), no capitalization note;
    gloss_notes now makes a VERIFIED singular/plural claim (the 4 plural cites checked against fed text
    before crediting — the new assertion-verification standing check running one word after it was written).
    The attempt-2 realm-split did NOT recur → confirms it was noise. Ships.
- **ROOT-CAUSE CHAIN VALIDATED END TO END** — stimulus identified → sweep-gated → deleted → fabrication
  gone next pull. **The batch's strongest single case for fix-the-input over prompt-whack-a-mole.** Two
  prompt generations (V4, V5) could not steer around a stimulus in the evidence; deleting it worked immediately.
- **D's placement IMPROVED across attempts** — attempt 3 shelves personified-heavens under SKY (named, all
  4 verses), which is where the reviewer's own majority folded it (~7/10). The load-bearing question didn't
  just clear, it landed in the best spot.
- **Sense 3 (figurative) — borderline, SHIPPED under the anti-count-preference rule.** Lev 26:19 is arguably
  physical-sky-in-a-simile (a sub-use of sense 1) and 2Co 5:2 self-acknowledges drawing on the domain sense,
  so it's a slightly-forced grouping. But verse-supported (not hollow), on-distribution (draw 5, 1/10), and
  holes/merges nothing. Rejecting it would be granularity preference in a gate costume — the exact back-door
  the four-gate reruling closes. **The rule matters most precisely when the entry mildly bugs us.**
- **FORMATTING 6/6 — V5's control-fire DONE.** Point 6 (term-of-art echo) got its first live catch:
  "sovereign / transcendence" flagged on attempt 1, confirmed CLEAN on attempt 3 (descriptive "divine
  presence/authority/agency"). All 6 points green on the raw.
- **METONYM — (a) verified unfed** (fed-40 dumped + read; no kingdom-of-heaven / sinned-against-heaven; Jas
  5:12 "swear by heaven" = oath-by-the-throne, divine-realm sub-use). βασιλεία collocation flag (33v) DID
  catch "kingdom of heaven" → resolved as phrase-level periphrasis (Son-of-Man precedent, divine-realm
  present). Detector silent (no seam this carve; Joh 1:32 in sense 1 only). Flags all sky/realm folds, clean.
- **CAP ACCOUNTING (for the record):** 3 attempts used, **but NO WALL** — attempt 3 shipped. The trigger
  counter stays at 2 (πολύς, ἅγιον); escalation mechanism armed + undischarged. Close call: this word came
  within one un-caught fabrication of tripping it. Attempts were spent on a TRUTH defect, which is the only
  thing attempts are for.

### STYLE WATCH #3 — "Sub-use:" whitespace convention (opened at ὕδωρ side-check, 2026-07-07)
First WHITESPACE-class sighting (the 6 formatting points cover word-choice + layout-shape, not spacing).
Byte check of shipped prose (`lexica_def`, repr of every "Sub-use:" context): within each card CONSISTENT,
across cards DIVERGENT — **ἱερεύς (V4) = `\n\nSub-use:` (own paragraph); οὐρανός (V5) + ἅγιον (V3) =
`. Sub-use:` (inline after the period).** Sorted DRAW-LEVEL (models pick different conventions per draw,
shipped verbatim by review-what-ships), NOT render-level (bytes genuinely differ). **Cosmetic — parser
keys on the bold/number headline, never spacing** (no parse risk, unlike the two drift bugs).
- **Disposition (JP nod'd own-line for V6, byte-explicit):** candidate V6 formatting line, phrased so the
  WHITESPACE ITSELF is unambiguous (vague "separate sub-uses clearly" is what produced two conventions) —
  **"each Sub-use begins on its own line, with a blank line before it."** Positive-phrased per standing
  rule. Rides free on the next version bump (whitespace alone doesn't justify a bump); if no V6 trigger
  lands before batch-2 closes, it ships with the post-batch redraw phase's prompt (where the 3 redrawn
  cards come back convention-consistent). NOT a gate, NOT a redraw trigger, no retro-edit. Unlike the
  slash/echo watches (which accumulated toward a threshold), the inconsistency is already demonstrated
  across 3 cards — so this can fold into the next prompt rev on JP's nod rather than waiting for more sightings.
- **Shipped cards keep their spacing;** they'd pick up the convention only on optional post-batch redraw
  (the redraw queue already holds ἅγιον/μέγας/ἱερεύς).

### G5204 ὕδωρ — LIVE (3 senses, attempt 3). The tight-agreement prediction, falsified-then-refined.
Shipped the attempt-3 draft (key ad02528a), no model call on apply, gate 34/34, stamp current, 34 verses.
3 senses: (1) physical water (cosmogonic + comparison-figurative as named sub-uses); (2) ritual
immersion/purification (1Jn 5:6 folded here descriptively); (3) figurative — water as symbol/origin.
- **REVIEWER `--runs 3` → `--runs 10`.** Count clustered but STRUCTURE wobbled (the tool's exact warning):
  physical 10/10, **ritual 9/10, figurative ~7/10** (both majority-distinct), cosmogonic/1Jn5:6 minority.
  Stable core = physical/ritual/figurative. The first-run draw-3 "merge ritual into physical" was a 1/10
  fluke, did NOT recur.
- **HYPOTHESIS RESULT — the point of this word.** Naive "tight one-dimension concrete noun" prediction
  **FALSIFIED** (ὕδωρ is stable at 3, not 1–2). Refined **usage-dimensionality hypothesis CONFIRMED**: the
  *substance* is one thing, but the *uses* genuinely span literal / ritual / figurative → ~3 stable jobs.
  **The trio isn't uniform** — θυγάτηρ / ὄρος may still run tighter (fewer usage-facets); "concrete" was
  never the right axis, usage-dimensionality is.
- **THREE-ATTEMPT SAGA (a granularity loop, NOT a truth-defect loop like οὐρανός).** attempt 1 UNDER-carved
  (merged ritual + figurative, promoted 1Jn 5:6) — gate-2 fail ×2. attempt 2 OVER-carved the periphery
  (fixed ritual, but still merged the 7/10 figurative, promoted cosmogonic 1/10 + thin 1Jn 5:6) — gate-2
  fail. **Opposite directions on the same axis (figurative folding); neither shape appeared in the 10.**
  attempt 3 HIT the target (physical/ritual/figurative distinct). Base rate ~70%, hit on the 3rd pull —
  **NO WALL** (target demonstrably existed in the draw space = draw variance, not target-nonexistence like
  πολύς). Escalation counter stays at 2; the "wall-with-existing-target → best case for draw-until-match,
  weakest for prompt-steer" frame was pre-registered but went undischarged.
- **LEXICOGRAPHY POINT WORTH KEEPING (the draft's genuine insight):** literal-water-in-a-simile vs
  word-used-figuratively is real lexicography — in Rev 1:15 "voice as many waters" the WORD isn't figurative,
  the COMPARISON is, so literal water serving a simile belongs under physical (a named sub-use), and only
  water-standing-for-something-else (wife/speech/baptism-type/name-origin) is sense 3. A sharper cut than the
  reviewer's broad figurative bucket. **The draft had a good idea, executed inconsistently** — 2Sa 14:14
  ("as water spilt") loosely shelved under sense-1 "destructive force" (under-fits a transience simile),
  Ecc 11:1 under the navigation sub-use. Minor placement imperfections (verses visible, no false claim, no
  hole) — well below the wall/gate-failure bar; shipped under the anti-count-preference rule.
- **CLEAN CHECKS:** register descriptive on ritual + 1Jn 5:6 (no sacramental editorializing); gloss_notes
  sense-3 claim VERIFIED true under the standing assertion-check ("the word itself is not metaphorical but
  the surrounding argument extends its reference" — accurate); formatting ~5.5/6 (one borderline term-of-art,
  "typological" for 1Pe 3:20, but it names the text's own move, 1Pe 3:21); detector silent; collocation flags
  (unclean-water / river / sea) all physical-sense unfed, clean.

### G5456 φωνή — LIVE (3 senses, one-draw ship). Clean-multi that agreed tightly; the seam-honoring card.
Shipped the first draw (key 2e3b7ede), no model call on apply, gate 37/37, stamp lexica:0c58c8a74b4f,
37 verses. 3 senses: (1) audible sound by a living being — cry/call/utterance (loud-voice μεγάλη φωνή,
prophets'-voices-as-proclamations, and greeting-sound Luk 1:44 all as named sub-uses); (2) non-vocal
acoustic phenomenon (instrument/thunder/wind/water); (3) circulated report/proclamation (Gen 45:16, Ezr 1:1,
Act 2:6). LXX-provenance note fires on sense 3.
- **REVIEWER `--runs 3` → STABLE, no escalation.** Count locked `{3:3}` mean 3.0; identical three jobs in all
  draws; all four wobble verses (Luk 1:44, 1Ki 8:55, 2Ki 7:10, Luk 23:23) FOLD (main partner stays cited).
  No appear/vanish, no merge, no job-boundary wobble → shipped from one draw, escalation counter stays 2.
- **PREDICTION SCORING.** CC's 2-sense call (voice vs sound) = MISS, self-reported and NOT rescued into a
  sub-use (correct under granularity-as-drawn — ticked). JP's theophany thin-sense = MISS (divine speaker
  folded into job 1 as drawn). The third sense (circulated report) was pre-registered by neither. μεγάλη φωνή
  as sub-use = HIT. **Dimensionality lesson:** usage-dimensionality predicted THAT there'd be spread and there
  was — but the axis was **propagation** (utterance → circulated report), not the speaker-type axis both priors
  watched. Hypothesis right on presence-of-spread, wrong on which axis; bank as a refinement, not a falsify.
  Clean-multi (3 distinct jobs) still agreed TIGHTLY at 3 — so "clean-separable → tight" holds even at 3 jobs;
  it's multi-*shallow*-axis that wobbles (πολύς/καρδία), not multi-job-count.
- **GATE 2 = the strong pass (the seam we pre-registered).** Company column exposed the utterance↔report seam
  live: 1Ch 15:16 / 2Ch 5:13 at 3/3 support but only 2/3 with the report cluster (draw 3 shelved them under
  job 1), and Act 13:27 crossed it in reverse (job 1 in draws 1&3, job 3 in draw 2). The card did NOT collapse
  the seam — it DEFENDS it in prose: sense-3's sub-use note pulls Gen 3:8 / Exo 3:18 to the boundary and argues
  them back into sense 1 ("addressable utterance, not a rumour"), and it shelved the praise-voice seam verses
  (1Ch 15:16 / 2Ch 5:13) under sense 1, matching draws 1–2's majority. Not merged, not thinned (0 thin/circular).
- **SEAM REGISTER #5 — utterance ↔ report (job 1 ↔ job 3).** LIVE seam, logged. Evidence above. The card
  HONORED it rather than breaking on it — logged anyway, because the register records where seams *live*, not
  only where they break (JP's ruling). Adjudication per instance if it recurs; not a gate.
- **STANDING-RULE CHECKS RUN (both, pre-ship — JP caught that CC's first verdict skipped them).**
  · **Fed-list verify:** the three prose tag-alongs (Heb 3:15, 2Pe 1:18, 1Co 14:8) all confirmed IN the fed 40
  by re-deriving `select_spread`→`fetch_context` on PA — builder cited what it was fed, nothing from training,
  37/37 stands. (Verified against the fed list, not inferred from draw silence.)
  · **Gloss-notes spot-verify** against `verses.text`: Act 2:6 = "…they heard each one of them speaking…" (note's
  straddle-caveat grounded) AND the verse opens "the report of this" = φωνή as sense-3 report; Luk 1:44 = "the
  sound of your greeting" = a spoken salutation, so the note's "voice would be equally accurate" is grounded.
- **COLLOCATIONS (3 uncited flags):** κραυγή (outcry), εἰσακούω (hearken to), κράζω (cry out) — all
  utterance-domain, all fold into sense 1 (which explicitly covers weeping cries / shouted proclamations /
  "hearken to his voice"). None signals an absent 4th sense; reviewer never surfaced one. Fold, not hole.
- **STYLE WATCH #3 (structural-mislabel, retro line).** Sense-3's "Sub-use:" header carries a *seam
  adjudication* whose verdict shelves both verses under sense 1 — so it isn't a sub-use OF sense 3 at all.
  Semantically right, structurally mislabeled; doesn't trip a gate as drawn. Retro candidate: a "Sub-use"
  header carrying boundary-verdict content. (Also confirms the pre-existing V6 whitespace watch — Sub-use runs
  inline, not on its own line; banked for the next version bump, not blocked.)
- **PROCESS NOTE (judge-on-the-raw, working as designed).** JP read the raw prose independently and caught two
  standing-rule checks CC's initial verdict had asserted-past rather than run (fed-list + gloss-notes). Both
  then passed — but the catch is the point: adjudication happens on the raw, and CC's readout is not the ground
  truth until the raw backs it. Same discipline that caught three relay errors last session.

### G3788 ὀφθαλμός — V6 REDRAW PENDING (V5 draft rejected). The freight line's birth + the floor-gap lesson.
The batch's hardest word so far and its biggest process yield. NOT shipped; first V5 draft (key 2fa587bb)
rejected on three defects; fixed by the V6 bump + a forced-sample redraw (pending).
- **FLOOR `--runs 3` → `--runs 10` (multi-shallow-axis, the 10 was mandatory).** Spread {3:6,4:3,5:1} mean 3.5.
  STABLE CORE = 3 jobs: (1) physical organ (10/10); (2) eyes as regard/estimation — the "in the eyes of X"
  favor/judgment Hebraism (Jdg 6:17/Rth 2:2/1Sa 1:18/2Sa 3:19/2Ki 1:13/1Ch 28:8 mutually 9–10/10); (3) figurative
  inner/spiritual perception (Eph 1:18 + Gal 3:1, together 8/10). The 4th–5th senses in higher-count draws split
  MINORITY facets below majority-distinct → FOLD: "eyes of the LORD" (2Ch 6:20/Neh 1:6/1Pe 3:12/Heb 4:13/Psa 5:5,
  internally 10/10 but split-from-human-regard only 3/10 → named-sub-use candidate); moral-disposition
  (Pro 6:17/2Pe 2:14, own sense only in the 3-run fluke). No hole. **Prediction scoring:** CC's literal-vs-figurative
  = too coarse (missed the "in the eyes of" middle job); JP's evaluative-idiom axis right that it's load-bearing
  (= job 2) but INVERTED on the detail — the perception split (Eph 1:18) is the stable 3rd job, the moral idiom is
  what folds. Confirms the refined hypothesis: multi-shallow-axis → wobble → needs the 10.
- **STEP 1.5 EYEBALL (the new floor gate, born here).** The draw printed 5 `⚠ collocation MISSED` warnings.
  Two carried an unfed JOB, not just unfed instances: **φείδομαι "eye shall not spare/pity"** (Deu 7:16/13:8/19:13)
  and **πονηρός "evil/envious eye"** (Deu 15:9/Mat 20:15) — both 0-fed, both the *eye as seat of one's disposition
  toward another* (clemency withheld / generosity begrudged), the same joint as haughty/adulterous. Verses pulled
  and read on PA: FOLD (inventory sound, no re-floor) — but into a disposition region the current card lacks.
  Pro 23:6 non-issue (ABP "bewitching man" buries the eye-idiom). → ENGINE_LESSONS #19: a stable floor on a gapped
  sample certifies the wrong inventory; eyeball MISSED warnings BEFORE adjudicating stability.
- **THE V5 DRAFT'S THREE DEFECTS (raw read).** (1) **#18 translation-freight** — sense-1 sub-use "the eye as
  embodying a **moral character**" + range "the **moral** evaluative gaze"; the flagship banned category, and the
  fix sits in the card's own citations (ABP: Pro 6:17 "insulting eye", 2Pe 2:14 "eyes full of an adulterous one"
  — attested qualities, not the Latin category). (2) **Silent minority-shelving** — Pro 6:17/2Pe 2:14 shelved under
  physical (a 3/10 reading) presented clean, no straddle note; violates the φωνή/Act-2:6 visible-boundary precedent
  (φωνή EARNED gate-2 by arguing its boundary; this card hid it). (3) **gloss_notes false absence claim** —
  "no gloss imports a sense the contexts do not support" asserted while 5 MISSED warnings sat unexamined
  (fabrication-family signature: confident absence, lookup not run). Corrected one over-reach in the review itself:
  the "eyes of your thought" point does NOT flag ὀφθαλμός — "thought" renders the companion noun, not ὀφθαλμός
  (verify-before-claim applied to our own audit). **Gates otherwise:** gate-2 passes (senses 2/3 distinct, eyes-of-LORD
  as substance of sense 2 = visible, sense 4 intact), gate-4 the 2/3 split is the draw-8 minority carve within
  distribution, citations 33/33. Structure fine; vocabulary + epistemics failed.
- **THE FIX — V6 bump (the freight line born from this word) + forced sample.** #18 was banked 2026-06-25 but never
  in the durable docs; ὀφθαλμός surfaced it. Authored the freight line (JP-approved, trim-and-convert to imperative:
  reframes not blacklists — "moral" is one illustration, mechanism is "describe the carving"), added to VERSE_PROMPT
  + the reviewer's byte-identical copy in one commit, pin V5→V6, stamp `0c58c8a74b4f`→`1ccea0a44740`; the banked
  Sub-use whitespace line rode along (disjoint failure modes → still one-change-per-gate). Grep-gated: stamp bump
  INERT (no auto-rebuild reader). **select_spread option (a):** force Deu 13:8 + 15:9 into the redraw sample only,
  logged on the draw as coverage-completeness (idiom-family representation), NOT steering; option (b) collocation-aware
  quota → v2. **TWO V6 WATCHES on first draws:** over-trigger (freight-paranoia; "all are loaded" is the guard) and
  philosophize (discussing the rule vs following it).
- **PRE-REGISTERED REDRAW BAR:** 4–5 senses in-distribution · disposition-toward-another its own region OR an
  argued sub-use of regard (capacious for insulting/adulterous/begrudging/pitiless, attested qualities naming it) ·
  Pro 6:17+2Pe 2:14 straddle-noted · NO Latin categories in headlines/body/range · six-point formatting incl. the
  whitespace line's first live test. **Streak stays 0** (attempt 1 not clean regardless of remedy path).

#### V6 ATTEMPTS → CAP-OUT → STRUCTURE-HINT MECHANISM (2026-07-07, the trigger's first fire)
- **Attempt 2 (V6-forced, key 6d0fbdf0):** structure FIXED — disposition-toward-another drawn as its own sense 2,
  forced Deu 13:8/15:9 landed there; gloss_notes fixed (real gaps, no false absence claim); whitespace line PASSED
  its first live test; both V6 watches clean. **BUT "moral" survived** in the sense-2 headline + range (2 sites,
  both "moral or evaluative") — the freight line DAMPENED (V5 "moral character" as the naming → V6 vestigial
  modifier) but did not DELETE. Gate fail on freight. NOT shipped.
- **Attempt 3 (V6-forced re-roll, key 6d0fbdf0, prose refreshed — same input-key, colliding outputs per lesson
  #15):** freight FIXED ("moral" gone everywhere) **but STRUCTURE REGRESSED** (verified on the RAW, not readout):
  the stable **regard job** ("favor/in the eyes of," own sense in 10/10 reviewer draws) was **demoted to sub-use
  (a) of sense 1 (physical organ)**, bundled with the disposition idioms — a merge of a majority-distinct job into
  physical (**gate 2 fail**) leaving regard non-distinct (**gate 1 fail**); and the minority divine-eyes cluster
  (own-sense 3/10) was **promoted to standalone sense 2**. Structure inverted from the certified read. NOT shipped.
- **CAP-OUT RULED (JP, 2026-07-07).** Count straight across per the οὐρανός precedent (attempts counted across a
  mid-stream fix): V5 draft + V6-forced + V6 re-roll = **3 off-target pulls = cap** (no counter reset for the V6
  bump). The word **oscillates** — attempt 2 held structure/failed freight, attempt 3 held freight/failed
  structure — never both in one pull within the cap. **Escalation counter 2→3** (πολύς range-completeness ·
  ἅγιον structure near-wall · ὀφθαλμός structure↔freight alignment). The armed trigger FIRED and is RESOLVED in
  this ruling.
- **MECHANISM = STRUCTURE-HINT (ruled, not draw-until-match, not prompt-steer).** Rationale on record: the hint is
  the reviewer's OWN 10-run output (certified ground truth, not a preferred outcome) → steers toward the floor,
  not toward a wanted answer; higher-cap pulls risk continued oscillation; prompt-steer is the wrong tool since
  attempt 3 proved the freight line WORKS. Implementation: `--structure-hint` (commit 95b4a16) injects the stable
  3-job list into the draw CONTEXT (user message, after the occurrences), frozen V6 prompt untouched; names JOBS
  not carving/count/sub-uses (granularity-as-drawn governs); logged on the draw record (structure_hint /
  structure_hint_why) like --force-verse. Fired with the 3 jobs (physical / regard-estimation-disposition /
  figurative-perception) + the 2 forced verses.
- **HEIGHTENED SHIP BAR on the hinted draw (not relaxed):** full four-gate re-audit of the WHOLE structure ·
  **2Pe 2:14 straddle note or argued shelving REQUIRED** (physical 5/10 in the floor — silent shelving blocked in
  EITHER direction) · disposition visible with attested qualities naming it (own sense or argued sub-use) · NO
  Latin categories anywhere · six-point formatting · both V6 watches. **Execution rule: ship tonight ONLY if
  unambiguously clean; any judgment call (arguable shelving, borderline phrase) → PARK till morning with the draw
  cached.** Heightened scrutiny doesn't get audited tired.

##### Attempt-3 raw (archived — structure-regression verified on THIS, not a readout)
```
1. The physical organ of sight in a living body — ... Sub-use: the organ ... "favor in your/his eyes" (Jdg 6:17;
   Rth 2:2; 1Sa 1:18; Est 5:2); "pleased in the eyes of" (2Sa 3:19); "your eye should be wicked towards" (Deu 15:9);
   "spare your eye upon him" (Deu 13:8); "an insulting eye" (Pro 6:17) ... [regard + disposition bundled UNDER
   physical]. Sub-use: witness/firsthand (Deu 3:21; Ezr 3:12; 1Co 2:9; Mar 8:18). Sub-use: concealment/disclosure
   (Num 5:13; 1Ch 28:8; Exo 13:9).
2. Eyes attributed to a non-bodily subject — God/divine (2Ch 6:20; Neh 1:6; Psa 5:5; 1Pe 3:12; Heb 4:13).
3. Eyes used figuratively for the understanding or inner capacity to perceive (Eph 1:18; 1Jn 2:11; Gal 3:1).
Range: physical → inner understanding (Eph 1:18) / God's watchfulness (Heb 4:13). Gloss notes: "eyes/eye" formal,
"imports no theological freight" [no "moral" anywhere — freight fixed]. (Full raw in draws/G3788.json history / session transcript.)
```

#### HINTED DRAW → PARKED (structure-hint's first output, draw `0abd875d`, 2026-07-07 S3 close)
**The mechanism WORKED.** First draw to hold **structure + freight together**: certified 3-job structure restored
(physical / **regard its own sense 2 — NOT buried** / figurative-perception), gates 1–2 pass, **"moral" gone
everywhere**, whitespace + six-point clean, citations 41/41, both V6 watches clean across all three live V6 draws.
The oscillation is broken — no longer a structural wall. **PARKED (not shipped)** under the heightened bar + the
don't-ship-tired rule, on a two-item fix list:
1. **2Pe 2:14 — mandatory straddle note absent, silently shelved.** It sits in sense-1's MAIN physical list ("eyes
   full of an adulterous one"), not even grouped with the disposition sub-use — a defined-bar failure (the verse
   was pre-registered for a note/argued shelving either way; physical 5/10 in the floor).
2. **Disposition sub-use homed under PHYSICAL, not regard.** Deu 15:9/13:8/Pro 6:17 hang under sense 1; the bar
   allowed "own region OR argued sub-use of REGARD" — sub-use-of-physical is outside the set (attempt-3's
   evaluative-under-organ error, milder — regard survived as sense 2).
Minor riders: dangling-"Gal" flag NOT in the raw prose (likely summary-side extraction — verify); Job 7:7
"inner prospect"→figurative shelving is a borderline call. **MORNING FORK (session-4 first act): hinted re-roll
vs. argued-shelving path.** ⚠ Re-roll odds: hint job 2 bundled disposition INTO regard and the draw DECLINED it
(homed disposition under physical) — a re-roll may need a sharper hint or the forced verses re-scoped to land
disposition where wanted. Streak stays 0.

##### SESSION-4 RULINGS (JP, 2026-07-07) — fork resolved, low-odds probe approved
- **GATE RULING = GATE-FAILING.** Primary ground: disposition-under-physical is outside the pre-registered
  allowed set (own region OR argued sub-use of REGARD) — the placement was never legal, so **argued-shelving
  of item 2 was never on the table.** The fork PARTIALLY COLLAPSED: argued-shelving was only ever live for
  item 1 (2Pe 2:14) and the riders. Secondary/reinforcing ground: it contradicts the certified fold-direction
  and blurs the majority-distinct physical↔regard line.
- **RE-ROLL APPROVED, conditional — logged as a LOW-ODDS PROBE.** One pull. Failure is informative, not a
  setback: if outcome 2 lands (structure+freight hold, disposition still mis-homed), that is first-use evidence
  on the structure-hint mechanism's LIMITS, held for the option-space reopening per the trigger block. Hard stop
  either way; a regression (loses structure or freight) = the FOURTH wall → re-arm. Diagnosis "model homes the
  forced disposition verses under the organ because they read as literal-eye idioms" = HYPOTHESIS (not in the
  attempt raw); the add-a-regard-verse lever rests on it, odds modest.
- **`--force-verse` is ADD-ONLY** (verified in code: appends beyond budget, never drops an auto-pick, hard-errors
  on non-occurrence). "Re-scope" therefore = KEEP Deu 13:8 + 15:9 (disposition coverage), ADD one regard-anchor
  verse — no swap/removal exists.
- **ANCHOR CRITERION (pre-registered):** the added verse must (a) come from the certified floor's regard
  exemplars (Jdg 6:17 / Rth 2:2 / 1Sa 1:18 / 2Sa 3:19 / 1Ch 28:8), and (b) render the idiom with
  regard/disposition VISIBLE in the ABP English surface — not buried (Pro 23:6 = the known negative). Eyeball
  against this, no picking on feel.
- **CONDITIONS PRECEDENT (one PA session before the pull):** `git pull` → confirm the `forced` field on
  `draws/G3788.json` matches Deu 13:8 + 15:9 (audit-doc claim, not yet draw-record-verified) → eyeball the five
  anchors against the criterion → finalize verse. Only then the pull.
- **SHIP GATE (amended outcome 1, FINAL):** disposition under regard with the three-region carving *argued in
  the draw prose* · 2Pe 2:14 in disposition with the mandatory straddle note OR argued shelving on the record ·
  dangling-"Gal" source located (raw shown if raw-side) · Job 7:7 explicit call · structure + freight held ·
  six-point + whitespace clean · both V6 watches clean · citations clean.

##### SESSION-4 OUTCOME — PARKED (JP, 2026-07-07): mechanism limit found, disposition wall → V7
- **VOID RUN — does NOT count against the ruled pull.** One draw fired with the UN-trimmed hint 2 ("…distinct
  from the physical organ") AND a no-op anchor (1Sa 1:18 already in the base sample). Caught PRE-audit by the
  22-OT arithmetic (`fed 42` = 20 base + only 2 new; three OT verses forced → one already present) and the
  identical draw key `0abd875d` (inputs unchanged from the parked draw). Not the ruled configuration → not
  audited, not shipped, pull not spent. **Process defect:** the ruled pre-pull checklist (trim hint 2, no-op
  check) ran UN-applied before the draw fired — the checks must GATE the pull, not trail it.
- **ANCHOR LEVER DEAD.** Read-only probe (reproduced `select_spread`, BUDGET 40) confirmed ALL SIX certified
  regard exemplars — Jdg 6:17, Rth 2:2, 1Sa 1:18, 2Sa 3:19, 1Ch 28:8, 2Ki 1:13 — are ALREADY in the base
  sample. Under-feeding of regard was never the cause; no in-criterion anchor exists to add as a new variable.
- **PARKED-DRAW HINT DISCLOSURE.** Draw `0abd875d` carried the "distinct from the physical organ" steering
  clause in its stored hint (session-3 origin; job-naming-only scope became law in session 4). Legal when
  drawn, disclosed for the record — it means the parked draw was already the MAXIMAL push.
- **WALL — FIRED in substance, DECISION DEFERRED to V7.** Strongest-form evidence: maximal push (steering clause
  + full regard-exemplar coverage) STILL filed disposition under physical. In-bounds re-roll is EXHAUSTED (no
  new anchor; trimming the hint only weakens the push). Option-space decision (widen hint channel / prompt-steer
  / higher-cap) stays RESERVED to JP, to be made WITH the V7 restructure — NOT a batch-2 fight. The one ruled
  pull remains UNSPENT if ὀφθαλμός reopens.
- **RIDERS park with the draw** (dangling-"Gal", Job 7:7). **STANDING WATCH:** a second dangling flag on any of
  the next 9 graduates flag-sourcing from rider to defect.
- **ROSTER:** ὀφθαλμός PARKED (second park alongside πολύς). Batch-2: **9 shipped, 2 parked, 9 to go. Streak 0.**
- **→ V7 PILE:** disposition-placement mechanism limit (ὀφθαλμός evidence package) added to the V7 restructure
  inputs. The wall becomes a prompt-restructure question, not a per-word draw fight.

### ESCALATION TRIGGER (standing, batch-wide)
If a SECOND batch word caps out with **range-completeness** as the binding constraint, the mechanism decision
(B vs C) moves from the retro to RIGHT THEN — two occurrences is a pattern, one is a hard word.

### SHIP BAR — RE-RULED 2026-07-06 (the SECOND reruling): four gates, not count-match
The first reruling (G80) said "reviewer gates core structure, not surface count." This finishes the job:
a draft ships if it clears FOUR gates, **whatever its sense count** —
1. **No holes** — every stable reviewer job is present + distinct.
2. **No merges** — no collapse of a distinction the reviewer showed majority-distinct.
3. **Completeness** — every reviewer-attested facet is visible SOMEWHERE (own sense, thin sense, or
   explicitly in the range). Nothing silently dropped. **Detector = the uncited-rendering flag; its control
   is the πολύς attempt-3 'long' catch** (a dropped temporal facet the flag caught at 13× uncited).
4. **Granularity ships as drawn** — splitting finer/coarser WITHIN the reviewer's observed distribution is
   fine; verse-supported flickers ship as thin senses (the G80 standard, now applied SYMMETRICALLY).
All prior gates unchanged (citations, dangling, collocation, loaded-frame, senses ≤ occ). Cap stays 3.
- **DERIVATION.** Granularity is a STYLE dimension, not a TRUTH dimension — sense counts have no ground truth
  (human lexicons split καρδία/πολύς across every count 2→6 the same way our draws do). Only holes, merges,
  and dropped facets actually MISLEAD a reader; "match the majority count" was chasing phantom precision.
- **Corrects a backwards asymmetry.** We shipped G80's ONE-verse Psa 35:14 as a thin sense while forcing
  πολύς's MULTI-verse comparative trio to fold — the weaker-grounded flicker got a sense, the better-grounded
  one didn't. The four gates apply G80's thin-sense standard symmetrically: verse-supported ships (as sense
  or thin sense); the only hard floor is that nothing attested is invisible.

### Framing correction — the wobble axis is USAGE dimensionality, not referent concreteness
καρδία was mis-labeled "concrete noun, one dimension." The REFERENT is concrete (a body organ); the CORPUS
USAGE is almost entirely the multi-facet inner-self abstraction (cognitive / affective / volitional /
relational). It wobbled — which CONFIRMS the refined hypothesis (multi-axis → wobble), not falsifies it.
**Banked: a body-part word can be maximally abstract in use; predict wobble from the usage's dimensionality,
not the referent's concreteness.** The genuine tight-agreement test transfers to θυγάτηρ / ὕδωρ / ὄρος.

### G2588 καρδία — VERDICT STABLE (ship under the four gates)
`--runs 10`. **Stable jobs (gate-1 present + distinct):** (1) cognitive — thought/intention/disposition,
10/10; (2) affective — emotion, distinct 8/10; (3) will-as-acted-upon — the hardened/turned cluster (Exo
4:21, Num 32:9, 1Sa 6:6, Ezr 6:22), distinct ~8/10. Minority collapses exist (draws 4/6 merge affect into
cognition; draw 5 folds the hardening cluster), so **gate 2 requires all three distinct — a 2-sense draft
that merges any pair FAILS.** Extra senses if drawn: moral-disposition (5/10, the Mat 5:8 cluster) and
relational-presence (2/10, the 1Th 2:17 / 1Jn 3:19 "in your hearts / absent in body" cluster) — **gate 3
requires both clusters visible as a sense OR in the range, never silently dropped.** All wobbles back-check
as FOLDS (incl. Eze 17:16, draw-7-only, partner cluster survives everywhere). No holes. Ship path: fresh
`--dry-run --force`, audit vs the four gates + standard checks, first passer ships via `--from-draw`. Cap 3.

### πολύς re-scored under the four gates (for the record — now UN-STUCK, re-attempt when sequencing suits)
The four-gate bar unblocks πολύς: it stays parked only for sequencing, not for a mechanism decision.
- **attempt 1 (3-sense number/degree/comparative)** — FAIL gate 3 (completeness): adverbial + temporal not
  visible in the range.
- **attempt 3 (3-sense, same shape)** — FAIL gate 3: temporal dropped ('long' 13× uncited — the gate-3
  detector firing on its control case).
- **attempt 2 (5-sense number/degree/comparative/nation-scale/long-time)** — by its headlines + range I read
  this as FAIL gate 3 too (adverbial "greatly" not visible), NOT a merge — number and degree stay distinct.
  **DISCREPANCY FLAGGED:** JP's ruling recalled attempt 2 as a merge failure; I don't see a merge in the
  headlines. Can pull the saved `agreement_G4183`/draw file to settle it if it matters for the record —
  either way it fails a gate, so it doesn't change the "re-attempt" plan.
- **Under the new bar, the first πολύς draft that keeps number + degree distinct AND makes comparative,
  adverbial, and temporal all visible (sense / thin sense / range) ships — whatever its count.**

### G2588 καρδία — LIVE (4 senses, one-draw ship under the four-gate bar)
Shipped the first fresh draft (key dad558e7), no model call on apply, gate 40/40, stamp current, 40 verses.
4 senses: cognitive / affective / moral-character-volitional / will-acted-upon.
- **GATE-3 PRECEDENT BANKED: inline verse-level naming inside a sense satisfies gate 3.** The
  relational-presence facet (1Th 2:17 "present in heart though absent in body", Php 1:7) is not its own sense
  — it's named AT its verses inside senses 1 & 2 ("mental/volitional presence as opposed to physical";
  "affectionate attachment"). That's "visible somewhere," and arguably better placement than a range line (a
  reader looking up 1Th 2:17 lands on the explanation). Demanding a redraw would smuggle count-preferences
  back in — the thing the reruling exists to stop.
- **Flag rate: 2** (euthýs 6.79, hypsóō 5.59 — "upright heart" / "heart lifted up", both resolve to senses
  present). "whole heart" (hólos) was cited this draft so it dropped off. Loaded-frame clean (the "soul"
  gloss-note names an over-import without manufacturing a sense — symmetric-audit standard applied right).
- **THE THREE-REGIMES FINDING (calibration headline so far).** G80 = 13 draws, πολύς = cap-out (parked),
  καρδία = 1 draw. Truth-property gates (holes / merges / completeness) CONVERGE fast; the style-property
  gate (match-the-count) FISHES. The four-gate reruling moved καρδία from a likely multi-draw slog to a
  one-draw ship by dropping the count-match requirement — the bar change IS the calibration win.

### G39 ἅγιον — LIVE (4 senses; near-wall, cleared on attempt 3). The first loaded-watch-zone word.
Shipped the attempt-3 draw (key 944bcb81), no model call, gate 40/40, stamp current, 40 verses. 4 senses:
persons-quality / location-sanctuary / things-offerings / holy-spirit. **Near-wall — 2 rejects
(structure-binding), cleared on the last attempt:** attempt 1 collapsed to 1 sense (all merged), attempt 2
merged the substantive sanctuary into the adjectival quality (the exact substantive-vs-adjective axis
pre-flagged), attempt 3 kept persons / place / things / spirit all distinct.
- **SPIRIT-FRAME BOTH-WAYS BAR (banked precedent).** πνεῦμα G4151 is a contested fork-word; ἅγιον is its
  standard companion, so the holy-spirit sense's FRAME can fail even when the JOB is 6/10-stable. Amended
  bar: reject BOTH creedal-procession/person language ("proceeds from", "a divine person") AND
  impersonal-ontology language ("power / force / agent / medium" asserted as what the spirit IS). Accept
  DOING/RELATION-level description only. **Neutral ceiling = attempt 2's "qualifying πνεῦμα as a compound
  expression"** (grammatical, asserts no ontology). The shipped sense 4 ("of divine origin or quality,
  distinct from human spirit") = relation/attested-contrast level → passes. The reviewer's own "agent /
  medium / divine power" framings (draws 1/5) would FAIL this bar — the subtle failure mode, not safe harbor.
- **SYMMETRIC-AUDIT banked (the standing method at its best).** The shipped draft's "place/places"
  gloss-note flags that even the CONVENTIONAL rendering supplies a noun the Greek lacks (τὸ ἅγιον = "the
  set-apart [space]"; "place" is a translator's addition). Auditing an uncontested gloss is what keeps
  favor-not-grace a method, not a filter.
- **Flag rate 7 — adjudicated, not waved.** All map to unfed cultic vocabulary whose senses ARE present +
  fed-grounded (naós/tópos → sense 2; stolḗ/skeûos/offerings → sense 3; bebēlόō → holy-vs-profane under 1).
  The high rate is a FED-40 finding: the 20-OT/20-NT balanced spread under-samples dense Numbers/Leviticus
  cultic vocabulary (temple, garments, vessels, offerings). Senses grounded by OTHER fed verses → no sampler
  nudge. Data point for the fed-40 retro question.
- **1Jn 2:20 DOUBLE-SHELVED (logged seam, no reopen).** The verse is cited under BOTH sense 1 (said of
  God/the divine) AND sense 4's "holy one" title sub-use — the exact migratory behavior the reviewer showed
  for it, baked into one card. Not false (the title genuinely bridges both; citation gate passed), but a
  reader tracing 1Jn 2:20 gets two answers. **Cosmetic unless a pattern emerges across the batch.** G39
  ships AS-IS. → this is the **known positive for the queued double-shelf detector** (a post-draw
  set-intersection over the per-sense verse lists; must fire on 1Jn 2:20). See the handoff's queued tasks.
- **word_gloss follow-up:** "Holy Place" confirmed too narrow (ABP folds the adjective ἅγιος G40 into G39, so
  the header must lead with "holy, set apart", not the narrow substantive). Override via the `OVERRIDES` dict
  in build_word_gloss.py (same path as G166/G5484) + `--apply` rebuild; through DB checkpoint.

### G1484 ἔθνος — LIVE (2 senses, converged attempt 2). Detector's first live fire; clean binary → tight agreement.
Shipped the attempt-2 draw (key e2ea2f75), no model call on apply, gate 40/40, stamp current, 40 verses. 2
senses: (1) a people-group / nation (Israel included); (2) non-Jewish peoples contrasting with the
covenant/believing community (the nations-as-outsiders category). Matches the banked reviewer verdict
exactly (STABLE at 2, unanimous {2:3}).
- **ATTEMPT 1 FAILED — neighbor-bleed (gate 1 hole).** Draw gave sense 1 = nation, sense 2 = "a nation
  measured by SIZE/quality of population" (Gen 12:2 "great nation") — the μέγας collocation read INTO the
  headword. The genuine stable job (nations-as-outsiders) was demoted to the range, and an off-distribution
  size sense took its slot. A truth-property miss (stable job not distinct + a manufactured sense), not a
  style-count quibble. Redrew (attempt 2), which converged; neighbor-bleed did not recur. Cap not stressed.
- **DOUBLE-SHELF DETECTOR — FIRST LIVE FIRE (2026-07-06), adjudicated ship.** `⚠ double-shelved: Eph 2:11 in
  senses [1, 2]`. RULED legitimate bridge, both homes kept — ὑμεῖς τὰ ἔθνη ἐν σαρκί names the referent as a
  people-group (sense 1) while the clause exists to draw the circumcision/uncircumcision boundary (sense 2);
  removing either home misrepresents the verse. Structurally identical to G39's 1Jn 2:20. **Seam register:
  Eph 2:11 double-shelved [1,2], ruled bridge, precedent 1Jn 2:20.** The tool's first live catch landed on
  exactly the verse class it was built to surface, adjudicated in seconds — flag-only working as designed.
- **Loaded-frame clean.** gloss_notes rejects capital-G "Gentiles" as a theological category (imports later
  ecclesiastical weight), keeps it as a plain social boundary marker; no "heathen." The real two-sense split
  stayed intact — rejecting the freight did NOT flatten the structure (the pre-registered over-correction risk).
- **Flag rate 1 counted** (exaírō PMI 5.42, "drive out the nations" Deu 7:1 = dispossessed-outsiders,
  covered by sense 2, instances unfed → resolves clean; μέγας 4.41 < 5.0 informational). Detector zero on
  attempt 1 trusted (control-green on G39); it fired on attempt 2 → live and honest.
- **TIGHT-AGREEMENT PREDICTION CONFIRMED.** ἔθνος = clean binary (nation vs outsider-nations) → agreed
  tightly at the reviewer's stable 2, one redraw to land the shape. Contrast πολύς/καρδία (multi-shallow-axis
  → wobble). The refined hypothesis holds; θυγάτηρ/ὕδωρ/ὄρος remain the pending tight-agreement test.

### G2364 θυγάτηρ — LIVE (5 senses, attempt 2). Multi-shallow-axis; tight prediction falsified again; the argued-shelving ship.
Shipped the attempt-2 draw (key `dda605a1`), no model call on apply, gate 32/32, stamp current, 5 senses,
**screenshot-verified end-to-end** (both scroll passes clean; gloss_notes both bullets render full — the
full-print gate fix `be027c1` earned its keep on its first live word). 5 senses = **draw-8's exact carving**
(offspring / vocative / collective / covenant-membership / towns), within the floor's {2:2,3:4,4:3,5:1}.
- **FLOOR: multi-shallow-axis, `--runs 10` mandatory.** Count 2–5 (mean 3.3). ONE stable-distinct core
  (offspring, 10/10). Everything else folds/unfolds: vocative 5/10 (coin-flip → granularity), city-personification
  6/10 (slim majority-distinct), covenant-membership 2/10 (folds into collective), daughter-towns always cited but
  own-sense ~5/10, figurative idiom (Ecc/Pro/1Sa) DROPPED ENTIRELY in 2 draws. **Tight prediction FALSIFIED,
  usage-dimensionality rule re-confirmed** (concrete referent, multi-facet usage — same as καρδία). Feed clean
  (562 = daughter 304 + daughters 257 + towns 1; no contamination).
- **ATTEMPT 1 REJECTED — three grounds.** (1) gate-3 completeness: figurative facet SILENTLY DROPPED (Ecc
  12:4 / Pro 30:15 / 1Sa 1:16 all absent) — the draw-2/8 failure mode. (2) mis-carving (ὀφθαλμός-shaped):
  "daughter of Zion" buried as a sub-use of "offspring of a biological FATHER" (wrong parent) while covenant-
  membership (2/10) got promoted to its own sense — backwards from the floor's ordering; Joh 12:15 / Luk 23:28
  double-listed across two sub-uses. (3) step-1.5 paternal narrowing (below).
- **STEP 1.5 CAUGHT A DEFINITIONAL NARROWING (not a hidden job).** μήτηρ MISSED (18v, 0 fed) = the maternal-
  naming genealogical formula (confirmed on PA: 1Ki 15:2 "his mother was Maachah daughter of Abishalom"). It did
  not hide a sense; it NARROWED the shipped one — attempt-1's sense-1 headline read "in relation to her biological
  or legal FATHER" because every fed genealogical verse is paternal. An accuracy defect (father-only "daughter"),
  same shape as ὀφθαλμός's "moral" freight. → redraw bar #3: parent-neutral headline. **Second unprompted step-1.5
  catch in two words** (ὄρος homograph, θυγάτηρ narrowing) — the law is compounding.
- **ATTEMPT 2 PASSED (no force — narrowing was draw-luck).** Fresh draw: sense 1 = "biological or ADOPTIVE
  filial relation" (parent-neutral, +adoptive rearing Act 7:21/Heb 11:24); city-personification its own sense 3;
  figurative visible via Ecc 12:4 sub-use; no double-listing; gloss_notes complete. All four gates + the 3 added
  bars clear. Father-narrowing confirmed STOCHASTIC not sample-driven — force budget untouched (1Ki 15:2 reserved,
  never needed; JP's no-force-on-attempt-2 call paid off with the signal).
- **ARGUED SHELVING (ruled 2026-07-07, δίδωμι precedent) — converts the figurative co-member drops from silent
  to ruled.** Facet ships visible via Ecc 12:4 "daughters of song." Two co-members out of the senses, ruled
  acceptable (uncited, uncontested): **Pro 30:15** "the leech's daughters" — fed + cited 8/10 in the floor yet
  dropped in BOTH card draws, so a re-roll to fetch it is a coin-flip, not worth the last cap slot; **1Sa 1:16**
  "daughter of Belial" — renders on the card via gloss_notes only. **Register/coverage:** sense 3's personification
  is register-neutral; the daughter-of-Babylon judgment-oracle register (Psa 137:8; Isa 47:1; Zec 2:7) is real, OT,
  and UNFED in the 40 but covered by the shipped construction. Drop **RULED, not silent.**
- **μήτηρ warning still prints on the apply log** — expected (nothing forced; it keys off the fed sample); threat
  neutralized by bar 3. NOT waved through (flagged so a future reader doesn't misread a live warning on a shipped card).
- **DANGLING-FLAG DEFECT — GRADUATED to systematic (armed watch fired).** Dangling "Dan" (from "daughters of
  Dan," the tribe, 2Ch 2:14) = the SECOND dangling flag on a roster word (after ὀφθαλμός's "Gal") AND reproduced
  across both θυγάτηρ draws → SYSTEMATIC, not draw-luck. Diagnosis: the ref-extractor reads tribe/place tokens that
  match book abbreviations ("Dan" the tribe ≠ book Daniel) as dangling book refs. Card text is correct; the FLAG is
  the false positive. → TODO ticket: detector needs a tribe/place-vs-book disambiguation pass (post-rollout).
  Retires ὀφθαλμός's "summary-side extraction" hypothesis for the rider.
- **Streak 0** (attempt-2 ship, by definition not attempt-1-clean).
- **ROSTER (corrected):** θυγάτηρ = locked-20 #19, the **11th ship**. Batch-2: **11 shipped · 2 parked (πολύς,
  ὀφθαλμός) · 7 to go** (ἔτος, ἄρχων, ἔργον, ἁμαρτία, ῥῆμα, δύναμις, τόπος). (JP's in-session "10/20, 8 to go" was
  off by one — the roster docs still listed the already-shipped ὄρος under REMAINING.)

### TRIGGER STATUS (standing — survives session end) — FIRED + RESOLVED 2026-07-07
Content-wall tally (now **3**): **πολύς = full cap-out (range-completeness)**; **ἅγιον = near-wall (structure,
cleared attempt 3)**; **ὀφθαλμός = cap-out (structure↔freight oscillation — 3 pulls, never both clean at once)**.
The trigger, armed at one-more-wall, **FIRED on ὀφθαλμός and was RESOLVED by JP's ruling: mechanism = STRUCTURE-HINT.**
Not draw-until-match (risks continued oscillation), not prompt-steer (attempt 3 proved the freight line works) —
the structure-hint passes the reviewer's OWN certified stable-jobs list as draw CONTEXT (steers to ground truth,
not a preferred outcome), frozen VERSE_PROMPT untouched. **Now LIVE:** `--structure-hint` (commit 95b4a16), logged
on the draw record like --force-verse; scoped to post-cap-out use only, NOT routine steering. **If a FOURTH wall
lands,** the trigger re-arms — reopen the option space (higher-cap · prompt-steer · widen the hint channel) with
the structure-hint's first-use evidence in hand.

### Parked-hard list
- **G4183 πολύς** — un-stuck by the four-gate reruling; parked for sequencing only. Re-attempt: first draft
  clearing all four gates ships. (Re-score + detail above.)
