# TICKET — lane ②: PN-star merged-verb FIX predicate (proposed, pre-code)

Opened 2026-08-02. Status: **RULED + PASS CODED (2026-08-02) — no data writes; the
rebuild is its own later ride.** Reviewer ruling, same day: predicate approved both
parts; decision point concurred (kept-word attestation NOT required — a kept word makes
no new claim; refusal/kept lists stay itemized for after-the-fact sampling); one added
control requirement — the legitimate-genitive negative, named below.

## WHAT LANDED (2026-08-02, this commit)

- `_redistribute_pn_star_merge` in `build_words_from_abp.py` — the pass exactly as
  ruled; runs after the article pass, before `_split_compounds`; inert without both the
  attestation map and the roster; every decision typed. Build prints its line per
  DECISION and notes the sizing plan owes per-SLOT too.
- `load_name_roster` + `pn_star_split` moved INTO the build; the detector imports them
  (ruling 4 — one roster, one splitter, no drift).
- **Splitter amendment (recorded as a change):** a word in `ARTICLE_STAYS` never
  classifies as a name even when capitalized — sentence-initial 'The' passes the caps
  leg and 'the' sits in the roster, so caps+roster alone could move 'The' onto a star.
- **THE NAMED GENITIVE CONTROL** (reviewer requirement):
  `test_class_b_legitimate_genitive_refuses` — the real Mat 26:1 line with 'jesus'
  hand-attested on the carrier's number must refuse, typed 'carrier-attested-name',
  branch-run. No corpus B row has a name riding its own number beside an empty star
  (grep over the full B list, 2026-08-02), so the branch is proven on a hand map.
- **PINNED FINDING:** on the REAL harvest no name is attested under its own number
  ('jesus'/G2424, 'david'/G1138, 'israel'/G2474 all absent — ABP prints proper nouns on
  G* stars, so the single-token harvest never sees them). Gate (d) is therefore
  PROTECTIVE on today's corpus: it fires on roster-collision words, not on real names.
  Pinned by `test_real_map_names_not_attested_finding` so a harvest change surfaces as
  an environment change, not a silent behavior shift.
- Controls: `tests/test_pn_star_merge_fix.py`, 12/12, added to BOTH CI lists. Verbatim
  fixtures: Mat 27:26 (A write + red), Mat 26:1 (B write + no-roster red + genitive
  red), Gen 23:19 (adjacent genuine merge writes — the reverted adjacency guard stays
  dead), Act 5:3 (straddle), Act 7:28 ('the' never moves). Old parser-level pin
  unchanged (the SOURCE stays merged forever; the split is downstream).
- Detector `--list` crash fixed (the B2 print used the wrong fields — the eyeball list
  for lane ③ was never printable). Detector re-run after the roster move: 4,996
  unchanged, all three controls fired.

## SIZING (item 1) — LANDED 2026-08-02

`--plan` / `--plan --corrected` added to the detector; the plan runs
`_redistribute_pn_star_merge` ITSELF via build_verse_words (the real pass, never a
model). Plan controls: the three known rows must reach the pass with the right class or
the run HALTs. RAW-layer record committed: `docs/audits/PLAN_pn_star_fix_raw.txt` —
**A 1,507 + B 2,552 written (per decision)**; full refusal itemization inside. The plan
logs a typed decision for EVERY multi-word star, so its lines are a SUPERSET of the
detector's 4,996 — reconcile by member, never by count.

**TWO FINDINGS from the raw run (both walked to source):**

1. **Bracketed members are typed-refused and deferred** (A/bracketed 1,324 slots +
   B/bracketed 18): the source brackets them (`Mat 27:47 "[2calls ElijahG* G5455
   1This one]"` — flagship #2 itself), and a move inside an existing bracket ordering
   is the ⑤-family second ruling. The detector's population includes them; the fix
   pass repairs the UNBRACKETED subset. Deliberate, loud, own cycle.
2. **RARE-NUMBER CLASS-A GAP — the flagship refuses.** `Mat 27:26 'scourging'` is
   A/unattested on the real map: φραγελλόω (G5417) prints twice in the whole corpus
   (here + Mar 15:15 'having been scourged,' — pooled, never a single token), so page
   attestation CANNOT exist for it at any threshold. Rare verbs systematically refuse
   class-A moves. **BANKED REVIEWER QUESTION (not decided):** admit the LEXICON
   definition as the evidence source for A/unattested rows (the same evidence
   `_split_compounds` already redistributes by on non-star slots) — sized by the
   corrected plan's new "LEXICON-BACKED class-A unattested" itemization (lexicon is
   PA-only, so the number comes from the `--corrected` run). Threshold-only list
   (attested 1–4 verses): 28 rows, mostly function-word noise — the ≥5 floor looks
   right; the real gap is 0-attested rare numbers.

## THE PIN — PRE-REGISTERED EXPECTED PICTURE (corrected layer, PA, 2026-08-02)

Derivation: `python3 scripts/audit_pn_star_verb_merge.py --plan --corrected`, run on PA
2026-08-02 03:08 UTC against the build's real inputs (Rahlfs + TAGNT + lexicon 5,523 +
BH index 31,089); full member record = `plan_pn_star_corrected.txt` on PA (regenerable
by the same command; raw-layer twin committed at `docs/audits/PLAN_pn_star_fix_raw.txt`,
LF endings). All three plan controls FIRED.

**PINNED BUILD LINE (per decision — the build's own Results basis):**

    PN-star pass: A 1,505 + B 2,552 written · 3,161 refusals
    (A/bracketed 1,324 · A/no-name 760 · A/straddle 462 · A/unattested 335 ·
     B/no-name 88 · B/straddle 83 · A/ambiguous 82 · B/bracketed 18 ·
     A/all-names 5 · A/star 3 · B/star-carrier 1)

Per-slot view and class-A write targets (G3588 1,320 · G1161 139 · G1063 9, rest ≤6)
in the PA file. The next rebuild's Results line must match these NUMBERS and the
member set must match the PA file BY MEMBER; the tail allowance for the ride is
derived fresh at the ride (named members only), per the inherited trap.

**RAW→CORRECTED delta — fully attributed, member-level (diff pasted 2026-08-02, both
files diffed on PA with --strip-trailing-cr):**
- Bulk: same refusal, truer pronoun number after correction (G1473 → G846/G4675/G4771/
  G5216/G3450/G2257 …) — behavior identical, layer relabel only. Same for several
  class-B writes ('jesus'/'pilate'/'sarah' members, count unchanged at 2,552).
- 3 raw 'ambiguous' rows RESOLVE to writes (corrections break the two-neighbour tie):
  1Ki 8:26 'to'→G3588 · 1Ki 8:41 'this'→G3778 · Gen 25:5 'to'→G3588.
- 5 raw writes FLIP to refusals on the truer number: Mat 27:2 'to' · 1Ki 2:1 'to' ·
  2Ch 36:4 'to' · Exo 2:21 'to' · Gen 40:4 'them to' (all G846-family neighbours).
- Net class A: 1,507 − 5 + 3 = 1,505 ✓; ambiguous 88 − 6 = 82 ✓ (3 pairs, both sides).
- 2 raw refusal rows vanish (Hos 4:15, Isa 41:8 'o'→G1161 candidates reshaped by
  correction) offset by new unattested entries for the 5 flipped members: 329 → 335 ✓.

**RARE-NUMBER QUESTION — CLOSED BY THE SIZING, recommendation to reviewer: REJECT the
lexicon fallback.** The corrected run's lexicon-backed itemization = 22 rows, and they
are dominated by connector scraps ('of', 'in', 'and', 'at', 'a certain') that should
NOT move; it does not rescue Mat 27:26 ('scourging' absent — G5417's lexicon entry
doesn't carry it either). The rare-number rows stay loud typed refusals (status quo,
live-served today); any future repair is a hand-reviewed per-row lane (splitter-B
precedent), never an evidence-rule loosening. Threshold-only list: 16 rows on the
corrected layer, function-word noise — the ≥5 floor stands.

## STILL OWED before the rebuild ride (in order)

1. Reviewer receipt on the rare-number recommendation above (JP pastes the block).
2. Lane ③ (B2 91-row eyeball) — worked against the pinned corrected-plan list on PA,
   not the detector's live output (sequencing ruled 2026-08-02: sizing scopes the
   eyeball). The B/no-name rows in the plan = 88; the detector's B2 = 91 (its splitter
   has no caps/stays legs) — the eyeball reconciles the two lists BY MEMBER first.
3. The rebuild ride (`/rebuild-words` as amended 8/1), verdict-gated against the pin.

## The defect, restated Charter = TODO ② (both session-open rulings JP-confirmed 7/31). Detector =
`scripts/audit_pn_star_verb_merge.py` (4,996: A 2,237 · B 2,759 = B1 2,668 + B2 91;
re-run 2026-08-02 on this tree, all three controls fired, counts unchanged).
Precedent inherited whole: ruling 10 (`TICKET_509_article_slot_resweep.md` §6j–§6l) —
attestation, not geometry; member sets, not counts; derivation through the correction
layer.

## The defect, restated

ABP glues a proper-noun star chunk and an adjacent content word's English into one cell;
`_split_compounds` skips star slots, so the build never redistributes it. Two mirrored
orientations:

- **Class A** — the star carries the merged English, a numbered neighbour sits blank:
  `Mat 27:26 "scourging Jesus,G* G5417"` → the "Jesus" chip carries "scourging";
  clicking G5417's word is impossible, the star's chip says the wrong thing.
- **Class B** — the number carries it, the star sits empty:
  `Mat 26:1 "Jesus finishedG5055 G3588 G*"` → "Jesus" rides τελέω's chip; the name has
  no chip of its own.

## THE PROPOSED PREDICATE (stated in full, before any code)

One new build pass, `_redistribute_pn_star_merge(rows, ren, names, refusals)`, running
**beside the pronoun/article passes, before `_split_compounds`** (it must see the
original bundled gloss, and it must run after any pass that fills blank slots — same
order constraint as the article pass). Touches english/english_head/greek_pos/bracket_id
ONLY — never strongs/strongs_base/is_pn. The star keeps its `*` identity; import_tipnr
fills it as it always has. Every decision is typed into the refusal log (the pass's full
decision record, ruling-10 style): WRITTEN / straddle / no-name / all-names /
unattested / carrier-attested-name / ambiguous / bracketed.

**Shared machinery, imported never copied:** the ruling-10 attestation map
(`build_attestation_map`, single-word tokens, ≥5 distinct verses, source-layer base
numbers) and `_slot_order` (the straddle rule). The name roster = the pinned TIPNR set
the detector already uses (`name_roster()` — moves into the build, detector imports it,
ruling-4 discipline).

**MEASURED HAZARD the predicate must carry (census 2026-08-02, script committed below):
the roster contains common English words** — TIPNR spelling *parts* include 'the',
'new', 'mount', 'queen' (census: `Rev 21:2 'new Jerusalem'` classed all-names;
`Est 7:2 'queen Esther'` likewise). So roster membership ALONE never licenses a move;
it only ever splits "the star's own words" from "the rest", and every write is gated by
attestation evidence as below.

### Class A — star carries (per star slot, unbracketed, multi-word English)

1. Split the star's English: roster-name words = the star's OWN (they stay);
   everything else = the moved run. No name words → **refuse 'no-name'** (the
   gentilic/B2-kin residue — 130 rows, reported to lane ③'s eyeball, never auto-written).
   All words names → **refuse 'all-names'** (6 rows; over-classification by the roster
   hazard lands here, which is the safe direction — status quo).
2. Kept words on both sides of the moved run → **refuse 'straddle'** (`_slot_order`;
   91 rows — `1Co 1:16 'house of Stephanas;'`).
3. Candidates = immediately adjacent slots holding a real number with blank English
   (the detector's own geometry). Bracketed neighbour → refuse 'bracketed' (⑤'s cycle).
4. **RULING-10 GATE: every moved word must be ren-attested for the candidate's base**,
   else refuse 'unattested'. Both candidates attest → refuse 'ambiguous', never a
   coin-flip.
5. Write = the pronoun-pass mechanism verbatim: new 2-slot bracket, greek_pos by
   `_slot_order` (English order). The star keeps the name words and its `*` tag.

### Class B — number carries (per empty star slot, unbracketed)

1. Carrier = the nearest slot with English on one side, walking across blank slots
   (the detector's walk), multi-word. Every slot between is blank by construction, so
   the 2-slot bracket renders clean even when non-adjacent (`G3588` between — 194 rows;
   render check owed at fix time).
2. Moved run = the roster-name words; kept = the rest. Same straddle rule
   (92 rows — `Act 5:3 'has Satan filled'` refuses). No name words → B2, refuse
   'no-name', lane ③'s list. All words names → refuse 'all-names' — 11 rows, and this
   is deliberate: `Act 19:4 'Jesus the'` is `_split_pn_article_lump`'s row (sole-owner
   ruling, §6j), and `1Sa 11:11 'Saul put'`-type rows where the roster eats both words
   need the eyeball, not a pass.
3. **THE B GATE (this class's analog of ruling 10 — a name has no number to attest
   against, so the evidence runs NEGATIVE):** every moved word must be (a) a roster
   name, (b) capitalized as printed (ABP prints proper nouns capitalized; a lowercase
   roster collision like 'the' never moves), and (c) **NOT ren-attested for the
   carrier's base** — a word the page itself prints on that number elsewhere is not
   evidence of a merge, and this is the branch that keeps 'the'/'mount'/'queen'-type
   roster collisions off the star. Any moved word failing (c) → refuse
   'carrier-attested-name'.
4. The kept (non-name) words stay on the carrier — they do not move, so no attestation
   is REQUIRED of them (census: requiring it would refuse 721 rows on harvest gaps like
   'should'/'having', auxiliaries that almost never occur as single-word tokens).
   **DECISION POINT for the reviewer, stated honestly:** the strict alternative (kept
   words must attest for the carrier) biases refusal, per ruling-10's cost asymmetry;
   the census says it costs 721 genuine-looking merges (`Act 1:15 'Peter having risen
   up'` refused because 'having' has no single-token attestation). Recommendation:
   don't require it — the moved-word gates (a)–(c) carry the safety load, and the
   kept words are the live status quo either way. The sizing itemizes both populations
   so the ruling is data-revisitable.
5. Write: name word(s) to the star slot, new 2-slot bracket, greek_pos by English
   order. Intervening blank slots untouched (a bare G3588 is an ordinary state —
   ruling 7's reasoning).

### The census the predicate was designed against (RAW source layer — sizing only,
### NOT the pre-registered picture; derivation committed: `scripts/census_pn_star_fix.py`,
### to be folded into the audit's `--plan`)

```
CLASS A (2,237)                                    CLASS B (2,759)
  straddle                        91                 straddle                          92
  all-names (nothing to move)      6                 carrier all name words            11
  clean, 1 blank, ATTESTED     1,661                 clean, kept attested          1,849
  clean, 1 blank, unattested     238                   (of which +intervening blanks 130)
  clean, 2+ blank neighbours     111                 clean, kept unattested          721
  no roster name on star         130                   (of which +intervening blanks  64)
                                                     no roster name on carrier        86
```

(The A 2-blank rows resolve per gate 4 — attestation picks or 'ambiguous' refuses.
Class-B buckets above split kept-word attestation for the decision point; the B write
count under the RECOMMENDED predicate is bounded by 1,849+721 minus straddle-free rows
failing gates (b)/(c) — the real number comes from the sizing instrument, not this
census. B's no-name 86 vs the detector's B2 91: two tokenizers, same job — the fix and
the sizing will use ONE splitter, the detector's list stays the eyeball list.)

## Controls (red-first, BOTH orientations, before any count is trusted)

Unit fixtures = verbatim source lines verified against `abp_texts/`, locked in
`tests/test_pn_star_verb_merge.py` (the existing pin flips to the split shape):

- **A-positive** `Mat 27:26`: 'scourging' → G5417, star keeps 'Jesus,', bracket+gpos,
  log entry emitted BY the write branch.
- **A-red** same fixture, 'scourging' removed from a hand-built ren['5417'] → typed
  'unattested' — proves attestation refuses, not slot geometry.
- **B-positive** `Mat 26:1`: 'Jesus' → the star, 'finished' stays on G5055, G3588
  untouched.
- **B-red (roster)** 'jesus' dropped from the roster → 'no-name'.
- **B-red (negative attestation)** 'jesus' hand-inserted into ren['5055'] → typed
  'carrier-attested-name' — the collision guard is what refuses, branch-proven.
- **B-collision** a fixture whose carrier is "the LORD said"-shaped with 'the' in the
  roster → 'the' never moves (gate (b)/(c) branch).
- **Genuine-adjacent control** `Gen 23:19` 'Abraham entombedG2290 G* SarahG*' → still
  WRITES (the reverted adjacency guard stays dead — carrier-holds-a-name is the
  discriminator).
- **Straddle controls** both classes (`1Co 1:16`, `Act 5:3`) → typed 'straddle'.
- Detector's three controls keep firing on the source; a run that loses one HALTS.

## Pre-registered expected picture (owed BEFORE the rebuild ride, not in this doc)

Per the 8/1 trap (four casualties): **every pinned figure derives THROUGH the
correction layer** — the audit grows `--plan` / `--plan --corrected` /
`--predict-vs <copy>` analogs mirroring `audit_article_slot_carrier.py`, run on PA with
the build's real inputs (Rahlfs/TAGNT pronoun corrections + lexicon + BH), member-level
decision record committed, **both counting bases printed** (per-decision and per-slot).
Swap condition = member set-equality with a NAMED tail allowance (each member named to
its owning pinned step — this lane's list derived fresh, never copied from 8/1's
idios×13+2). The RAW census above is a design instrument only and is never compared
against the corrected plan by count.

Sequencing stands: fix session now → its OWN rebuild ride (`/rebuild-words` as amended
8/1) → full detector run between. Never folds with ⑤ (38 bracketed rows) or anything
else. Roster frozen — any TIPNR change runs `check_roster_regression.py` first.

## Pointers
- `docs/handoffs/HANDOFF_pn_star_ride.md` — the lane-2 opener this executes.
- `docs/tickets/TICKET_detector_gap.md` — detector close-out, the 4,996.
- `TICKET_509_article_slot_resweep.md` §6j–§6l — ruling 10, the inherited traps.
- `scripts/build_words_from_abp.py` — `_redistribute_article_slot` (the template),
  `build_attestation_map`, `_slot_order`, `_split_pn_article_lump` (Act 19:4 owner).
