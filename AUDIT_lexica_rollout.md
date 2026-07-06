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
