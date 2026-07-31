# Predicate spec — strict name-match Greek-number inheritance (G707 class)

**Status: awaiting JP sign-off. No build until signed off.**
Ruling being implemented (2026-07-31b): a proper-noun slot inherits its entity's Greek
number ONLY if the slot's own printed name matches a name TIPNR attaches to that G-number.
Ramah drops too. No allowlist this session. Entity records, binds, map pins untouched —
this changes slot-number inheritance only, inside `build_pn_greek_identity.py`.

## Where the per-number names come from (TIPNR's own rows)
Each TIPNR entity record lists its numbers on separate lines, and each line carries the
English names that number goes with:

- The record's own first line: the head name + its head number
  (`Elijah@1Ki.17.1-Jas=H0452G` → "Elijah" ↔ H452).
- The `– Named` / `– Greek` / `– (same form as previous)` lines: the number sits in
  column 2 (`G0707«G0707`), the names in column 1's alt-part (`Arimathea|Mizpah@…` →
  "Arimathea") and column 3's version list (`Elias =KJV; [ ] =ESV,NIV`).
  The `[ ]` token means "the versions print the record's main name" — so it expands to
  the head name (that's how Elijah/Noah/Rehoboam keep their numbers).
- The record's summary text: every `<strong="G2243">Elijah</strong>` pair — a second
  in-file witness, only ever ADDS names TIPNR itself prints.
- `– Total` lines are EXCLUDED — they pool every name with every number, which is
  exactly the conflation being fixed.

Result: per entity, a map of G-number → the set of names TIPNR attaches to it.
A parallel corpus-wide map (name → G-numbers attached to that name anywhere) gates the
two fallback lanes the same way.

## The match (normalization — NOT raw equality)
Slot name and TIPNR names are both normalized with the existing machinery:
- `entity_resolution.norm_name` (lowercase, trailing punctuation stripped), plus
  accent/diacritic folding on both sides.
- The existing variant table (`VARIANT_ALIASES` + `name_variants`) applied both
  directions — so a slot printed one way still matches a TIPNR spelling of the same
  name ("Elias"/"Elijah" via the `[ ]` head expansion and the variant table).
- Compact compare (hyphen/space-stripped) same as the binder's compound handling
  ("Ramathaimzophim" vs "Ramathaim-zophim").

MATCH = the slot's normalized name (or one of its variants) is in the G-number's name
set (or matches a variant of one of those names).

## Where the gate applies (all three tipnr-source lanes in build_pn_greek_identity)
1. **Bound lane** (pn_binding → entity with exactly one Greek number): inherit only on
   MATCH against that entity's map. Mizpah/Mizpeh/Ramah slots fail (G707 carries only
   "Arimathea") → they fall to the honest lemma/no-number states, same as today's
   multi-Greek entities. Elijah-class slots pass.
2. **Name-agreement lane** (unbound; all entities with the spelling agree on one G):
   the spelling itself must be attached to that G-number in the corpus-wide map.
3. **Lookup lane** (import_tipnr's name→G lookup): same corpus-wide check.

abp-tag rows (the word's own ABP G-number) are untouched — those numbers are ABP's, not
inherited. Hebrew side, gentilic handling, headword discipline: all untouched.

## Expected effect (pre-registered)
- The 52 flagged records stop stamping ~588 foreign-named OT slots; those slots serve
  the lemma-only/no-number card state (honest, per Q3 design).
- G707 in the words table on scratch: exactly 4, all NT, english_head arimathea.
- Elijah G2243 / Noah G3575 / Rehoboam G4497 keep their numbers (G2 gate; if the
  predicate drops these it is too strict — stop and report).
- Zero changes outside the flagged records (G5 diff gate; control word G3101
  byte-identical).

## Chain + gates (unchanged from the session charter)
Scratch copy only, journal DELETE. check_roster_regression CLEAN before import_tipnr.
Full chain in /rebuild-words order: import_tipnr → retire_hebrew_identity →
build_pn_greek_identity (patched) → build_entity_binding, then surface backfills +
translit if words moved. Every gate reads the scratch WORDS table (the served layer),
each detector fired on the known-bad live state first. Gates G1–G7 per the charter;
permanent regression test pinning G1+G2 added to both CI lists.
