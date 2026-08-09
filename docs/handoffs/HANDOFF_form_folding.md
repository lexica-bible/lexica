# HANDOFF — inflected-form folding, then ABP-tab routing (one ticket, hard order)

Banked 2026-08-09. Opener for a fresh session. **Nothing here is live state — it is what was
measured on 2026-08-09, and a prompt is a memory the moment it is written. Re-verify every number
and every file reference against the repo and against PA before you build on it.** The standing
rules for this work are NOT restated here on purpose (a re-listed rule is a copy that drifts):
read `CLAUDE.md`, then `docs/claude/word-study.md` + `docs/claude/data-model.md`, and the
tripwire index in memory `feedback_verify_before_claiming` before making any claim.

## The job, in one line
Fold a word's inflected forms under one identity, THEN let Word study's ABP tab open a name's ABP
occurrences. **Folding first is a hard dependency, not a preference** — see the trap below.

## Why it exists (the user-visible symptom)
JP searched Word study for Galilee. The ABP tab was greyed out. ABP contains Galilee all over the
Gospels, so the tab looked broken. It was not: it is honest about the NUMBER and wrong about the
TEXT.

## What was measured (2026-08-09, JP-run on PA — RE-RUN THESE)
- `words` rows under `strongs_base='G1056'`: **0**. `kjv_strongs` rows for G1056: **63**.
- ABP prints Galilee **73** times (`words` where `english LIKE '%Galilee%'`), every one carrying
  `strongs='*'` AND an **empty `lemma`**.
- `pn_greek_identity` carries the place name numberless: **5 distinct forms / 72 rows** —
  Γαλιλαίας 37 · Γαλιλαίαν 20 · Γαλιλαία 13 · Γαλιλαάν 1 · Γαλιλαίς 1.
- The GENTILIC Γαλιλαῖος ("Galilean") **does** carry G1057. Only the place name is numberless.
- Unchased and stated rather than papered over: 73 (`words`) vs 72 (identity). One row. Nobody
  has explained it. It may be nothing; it may be a real hole. Do not assume.

## Why the tab greys (read, not inferred — but re-read it)
Two separate disabled sets in `static/src/80-lexicon.jsx`, and they are NOT the same mechanism:
- the search-scope tabs use `_comboOK`, which can only grey ABP when the language filter is
  Hebrew — so never for a Greek word, and almost certainly not what JP hit;
- the word-card tabs use `!profile.has_abp`, and `has_abp` (`views_lexicon.py`) asks whether any
  ABP word carries the NUMBER. For G1056 that is 0, so the tab greys correctly and misleadingly.

## ⚠ THE TRAP — the whole reason routing is blocked
The by-form door already exists (`_pn_lemma_rows`, `views_lexicon.py`) but it matches
`greek_lemma` **exactly** and requires `greek_strongs IS NULL`. Forms are stored **per inflected
form, not folded**. So a by-form view keyed on `Γαλιλαία` returns **13 of 72**, with nothing on
screen saying the other 59 exist.

**Shipping routing without folding trades a grey tab for a wrong count. A grey tab says nothing;
a wrong count says something false.** That is a bar violation, not a rough edge. Reviewer-endorsed
hold, 2026-08-09.

## Scope
- **In:** folding inflected forms under one identity, for numberless proper-noun forms AND the
  long-standing `κύριε → κύριος` class (the same job — they were merged into one ticket by ruling
  on 2026-08-09, see TODO.md).
- **Then:** the ABP tab opens a name's real ABP occurrences, honestly counted.
- **Out:** backfilling entity data; the interim "explain the grey" label (**JP DECLINED it
  2026-08-09 — do not re-pitch**).

## Stop conditions — bring these back rather than pushing through
- The fold cannot produce a complete, honest count for a name → STOP. Report the count you can
  prove and what is missing. Do not ship a partial count as a total.
- Folding needs a morphology lookup that does not exist yet → STOP and scope that separately;
  do not hand-roll a form-stripper that "usually works". A wrong fold silently merges two words.
- The 73-vs-72 gap turns out to be a real hole → that is its own finding; report it, don't absorb
  it into the fold.
- Any write to `words`, `pn_greek_identity`, or a binding table → checkpoint first. This ticket
  was scoped as a lookup/display problem; if it becomes a data-writing problem, that is a
  different ticket with different gates.

## Where the rest lives
`TODO.md` → "Word Study's greyed ABP tab" and the merged-ticket entry beneath it (full diagnosis,
the paste-form correction, the second-order "bare No matches" honesty problem).
`docs/claude/data-model.md` → the `tipnr_entities.area` mixed-content warning added the same day.
