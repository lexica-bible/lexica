# DESIGN — Hint tooling for parked-word re-entry (batch-5 prep)

Status: **RULED (JP, 2026-07-12, "go with all recs" — all five items) + reviewer
concur-with-amendments banked.** Build not started; the reviewer reads this doc in
full next session before code lands. Companion ticket: the fragment-rendering fix
(TODO.md) — **sequenced FIRST by ruling 4.**

## RULINGS (JP, 2026-07-12)
1. **Refuse-when-notes-forgotten: YES** — running a registered word without `--hints`
   refuses (override `--no-hints REASON`, logged).
2. **Hinted ships count WITH A MARKER** — hinted-ship vs unaided-ship never conflated
   in one number (the dagger-style asterisk convention; exact glyph/wording set at the
   batch-5 charter).
3. **Hint-register edits require JP approval** — same authority as the rulings they
   encode.
4. **The rendering-layer fix lands BEFORE hint re-entry** — three of the seven shelf
   words carry checker/rendering exhibits; re-running them through a known-defective
   layer would contaminate the re-entry evidence.
5. **Reviewer amendments accepted:** (a) the scoreboard marker (= ruling 2);
   (b) **hint-provenance verification at re-entry pre-reg** — before a hinted word's
   floor/draws fire, the reviewer verifies each register line against its cited ruling
   (committed-wording-governs, applied to hints). Written into the procedure below.

## What this is, in plain terms

Seven words failed their runs for specific, known reasons — each park came with a
one-line note that would probably have prevented it ("don't blend the psalm's wording
with Ephesians' wording"). This tool stores those notes and shows them to the engine
when it re-drafts the word. The engine still reasons from the verses; the note is a
guard rail, not an answer key.

## What already exists

`--structure-hint JOB` (build_lexica_def.py) injects a prior review's certified
stable-JOBS list into the draw's user message, AFTER the occurrences, as a
"STRUCTURE CHECK" — frozen system prompt untouched, hint recorded on the draw file
(`structure_hint` + `structure_hint_why`), and part of the draw cache key so a hint
change forces a fresh draw. Ruled 2026-07-07 as the cap-out escalation mechanism.

## The extension: CONSTRAINT hints

A second hint kind: one-line pre-registered constraints. Three classes, all drawn from
this batch's park evidence:

1. **Corpus-fact pins** — verse facts the model repeatedly gets wrong.
   e.g. "Psa 68:18 reads 'you RECEIVED gifts by men'; Eph 4:8 (quoting it) reads
   'he GAVE gifts to men' — describe each text's own wording; never summarize jointly."
   e.g. "1Jn 2:8: this lemma's word is the COMMANDMENT; the 'true light' is ἀληθινός
   G228 — off-limits."
2. **Discipline rules** — citation/wording rules the engine knows but drops.
   e.g. "Cite every reference under exactly ONE sense; a verse carrying two senses is
   stated as a named dual, never silently listed twice."
   e.g. "Quotes inside quotation marks must match the supplied verse text verbatim;
   mark trims with an ellipsis."
3. **Reach ceilings** — referent-specific attribute-only lines.
   e.g. "The exclusion-state prose asserts only what a cited text states:
   characteristic-of-the-place YES; permanence/duration/hopelessness NO."

### The line that keeps this legal (the reviewer's flag, answered)

The incumbent-comparison rule says: never feed adjudication content or the incumbent
card's prose into a draw. Constraint hints stay on the right side of that line because:

- **Pre-registered**: every hint line is banked in the audit doc BEFORE the re-entry
  session opens, with provenance (which park, which ruling). No hint is written
  mid-adjudication for the draw being adjudicated.
- **Fact/discipline only, never outcome**: a hint may state what a verse says (checkable
  against `verses.text`), a citation rule, or an attribution ceiling. It may NOT name a
  preferred sense wording, sense count, carve, or any sentence of a prior draft.
  Job-name hints (the existing kind) remain the only structural steer, and they name
  jobs only.
- **JP rules the register**: adding or editing a hint line = a checkpoint (same class as
  a correction-table write).

## Storage

A hand-curated, in-repo register — same pattern as CONTESTED_VERSES:

`draw_hints.py` (new file, imported by build_lexica_def.py):

```python
DRAW_HINTS = {
  "G162": {
    "hints": [
      "Psa 68:18 reads 'you received gifts by men'; Eph 4:8 (quoting it) reads 'he gave gifts to men' - describe each text's own wording, never summarize the pair jointly.",
      "Cite every reference under exactly ONE sense; a verse carrying two senses (e.g. 1Ch 5:21 persons+property) is stated as a named dual, never silently listed twice.",
    ],
    "jobs": [],            # optional stable-jobs lines (existing mechanism's content)
    "provenance": "AUDIT_lexica_rollout.md G162 PARKED entry, 2026-07-12; JP batch-close ruling",
  },
  ...
}
```

Verbatim from the banked hint candidates; the audit entry is the source of truth, the
register is the machine-readable copy. A CI test asserts every register entry names a
provenance string.

## Injection

- New CLI flag `--hints` on build_lexica_def.py: loads DRAW_HINTS[word] and injects a
  labeled "CONSTRAINT CHECK (pre-registered)" section into the user message, after the
  occurrences (and after any STRUCTURE CHECK). Wording mirrors the structure-hint
  section: constraints are checks, the occurrences remain the primary evidence.
- **Loud, and refuse-by-default the other way**: running a word that HAS register
  entries WITHOUT `--hints` prints a warning and (proposal) refuses unless
  `--no-hints REASON` is passed — a parked word re-entering without its banked hints is
  almost certainly an operator mistake. JP rules this default.
- Hint text joins the draw signature (cache key) and is stored on the draw record
  (`draw_hints` + provenance), exactly like structure_hint. The dry-run console prints
  the injected lines so the reviewer sees what the draw saw.

## What does NOT change

- Frozen system prompt (V8) untouched. Floors untouched (a hint changes drafting, not
  the corpus; saved STABLE floors from the parks remain the #30 reference — fresh
  floors only where the standing data-fix rule already requires one).
- Full gate order per word: screens → pre-reg banked → (floor if owed) → build draws →
  adjudication → apply → render. Hints don't shortcut anything.
- The 3-defect budget still applies to hinted draws.

## Count semantics (JP ruling needed)

The 15-count measured UNASSISTED ship rate; a structure-hint use removes a word from
that count by the standing batch-3 term. Proposal: hinted re-entry ships count on a
separate "hinted" scoreboard (the card is just as reviewed and just as live — only the
calibration statistic differs). JP rules the wording.

## The seven words' hint lines (drafted from the banked candidates — reviewer verifies
## each against its park entry before the register lands)

- **διαιρέω G1244**: one-sense-per-ref discipline; no invented carve (every sense's
  members attested in its floor); no narrative frames on cited verses (the Gideon/
  Abimelek class — describe the verse's own text).
- **δόμα G1390**: Psa 68:18 received / Eph 4:8 gave — describe each, never merge;
  Ecc 5:1's δόμα is human→God cultic (the floor's home), not divine bestowal.
- **εὐχαριστέω G2168**: Rom 16:4's "to whom" resolves to Prisca and Aquila (16:3) —
  the thanks is TO THEM; negated occurrences (Rom 1:21) are the same sense in negation,
  not their own shelf.
- **ἀληθής G227**: 1Jn 2:8 — this lemma = the commandment; the "true light" is
  ἀληθινός G228, off-limits in senses AND range; verses carrying both the correspondence
  and juridical questions (Joh 5:31–32, 3Jn 1:12) are named duals, never double-listed.
- **ἀλλάσσω G236**: Isa 40:31 / Isa 41:1 belong with the transformation group
  (Psa 102:26, Heb 1:12, 1Co 15:51, Dan 4:16); Gal 4:20 belongs with the
  condition/transformation group, not its own sense; substitution/trade straddlers
  (Lev 27:10) = named dual or one home.
- **κλαυθμός G2805**: exclusion-state prose asserts only what a text states —
  "will obtain among the excluded" is the ceiling (no permanence/abiding/hopelessness);
  the weeping-and-gnashing sentence is quoted verbatim from the supplied text or not
  quoted.
- **αἰχμαλωτεύω G162**: the two register lines shown in the Storage example.

## Build plan (after JP's ruling)

1. `draw_hints.py` register + CI provenance test.
2. `--hints` / `--no-hints REASON` flag + injection + signature + draw-record fields +
   console print. Fixture test: hint text present in user message, after occurrences;
   signature changes when a hint changes.
3. Reviewer walk of the seven register entries against their park entries.
4. Batch-5 charter: re-entry order, count semantics per JP's ruling, fresh-floor list
   (δόμα and εὐχαριστέω have post-fix floors; the rest reuse saved STABLE floors).

## Re-entry procedure additions (per ruling 5b)

At each hinted word's pre-registration, BEFORE anything fires: the reviewer verifies
every register line for that word against the ruling its provenance cites (one grep
into the audit doc) — drift between the ruled wording and the file's wording blocks
the run until reconciled.

## Ruling list — CLOSED (see RULINGS block at top; formerly the open questions)

All four resolved 2026-07-12 per recommendation, plus both reviewer amendments.
Build order: (1) rendering-layer fix → (2) hint tooling (register + flag + tests) →
(3) reviewer walk of the seven register entries → (4) batch-5 charter → re-entry.
