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
- **G3056 λόγος** — known register candidate. Built anyway as calibration data; audit
  will flag what it flags.
- Watch on build: ἔπω/λέγω/λαλέω are three "say/speak" numbers (ἔπω = the aorist half of
  λέγω, suppletive); ἄνθρωπος vs ἀνήρ is the human-vs-male pair. Not forks — checking the
  engine keeps them distinct.

### Open items — logged, NO fix now
- **G3962 πατήρ — κύριος-under-πατήρ row (phrase misalignment).** A πατήρ occurrence row
  carries κύριος misaligned under it. Data-side phrase misalignment, not an engine bug;
  parked here for a later pass.

### Calibration wins
- **G1325 δίδωμι — freight-flagging works on a non-contested word.** The engine flagged
  the gloss *impute* (1Sa 22:15; Jon 1:14; Heb 8:10) as importing forensic/theological
  freight beyond what the context requires — exactly the freight-flag behaviour, on a plain
  verb, no fork needed.

### Redraws
- **G1325 δίδωμι — RESOLVED.** First draw carried a `1Sa` dangling ref (no ch:vs) inside
  the *impute* gloss-note → failed the dangling-empty bar. Redraw came back 40/40, dangling
  gone. Cause was draw-level drafting looseness, not data.

### Batch One — apply result (2026-07-03)
17 written clean · 7 prior stamp-skipped (υἱός, γῆ, βασιλεύς, ἡμέρα, οἶκος, χείρ, λόγος)
· **2 rejected, not written:** λαός G2992 + πρόσωπον G4383, both on a `Ruth` citation.

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
