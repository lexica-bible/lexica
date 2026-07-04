# The two-source entity seam — MetaV × TIPNR (Session 5 write-up)

**Status:** documentation of a known seam, not a defect report. Written Session 5
(2026-07-04), after the Session 4 Cushi fix locked the first shape-guard in.

The proper-noun sidebar is fed by two independent sources. They fail in
different ways, and the system leans on each exactly where the other is weak.
This doc records each source's known failure shape, why there is **no
precedence rule**, and an evidence-based assessment of whether more
shape-guards are warranted.

## The seam

| | MetaV | TIPNR |
|---|---|---|
| Role | Enrichment: person/place cards, aliases, relationships, map coords | Identity spine: verse-correct entity binding (`pn_binding`), PN Strong's numbers in `words` |
| Known failure shape | **Factual accuracy** — entries can be wrong or stale; this is why TIPNR backfills identity and why a bind GATES the whole name-based MetaV fetch | **Mis-filing across sections** — verses of a *person* can sit in a *place* entity's reference list (the Cushi shape, Session 4) |
| What guards it | The bind gate: a verse-correct TIPNR bind suppresses the name-guess MetaV card entirely; Fix A floors the rest | The render rule (verse must corroborate), the number-agreement requirement on fuzzy matches, and the Session 4 person-as-place guard |

**No precedence rule.** Neither source is the gold standard. TIPNR wins on
*identity* (which entity is this verse about) because its reference lists are
verse-granular; MetaV wins on *content* (what to show about it) because its
cards are richer. A "TIPNR always beats MetaV" rule would import TIPNR's
mis-filing shape into content; the reverse would import MetaV's accuracy shape
into identity. The seam is managed by construction — bind gates card — not by
ranking the sources.

## The Session 4 shape, precisely

Cushi (2Sa 18, a man): the surface name stems (gentilic normalization) to the
*region* Cush; the region's TIPNR entry both **lists the verse** and **carries
the gentilic number H3569** — so the fuzzy path's two guards (verse
corroboration + number agreement) both pass, and a PLACE card renders for a
person. The tell: an exact-spelling PERSON entity (Cushi@Zep.1.1) carries the
*same* number.

Guard (in `entity_resolution.py`, fuzzy step): skip a PLACE fuzzy-candidate
when an exact-spelling PERSON entity carries the same stored number. Floor,
never mis-bind. Locked by cert check 7: **no name renders both a fuzzy-place
and an exact-person.**

## Assessment: are other shape-guards warranted?

"Assess" here = enumerate candidates with evidence from the live tables, not
implement. Any new guard is its own checkpointed proposal.

### Candidate shapes

1. **Place-as-person (the mirror).** A place's verse fuzzy-binds to a PERSON
   entity that lists the verse and shares the number, while an exact-spelling
   PLACE entity carries the same number. Structurally possible — the fuzzy
   path is symmetric and the Session 4 guard only covers one direction.
   Probe: the check-7 mirror census (P1 below).
2. **Fuzzy to the wrong same-section entity.** Two persons (or two places)
   share a base number (family clusters do); a fuzzy variant single-hits the
   wrong one. The multi guard only fires when *both* survive as candidates —
   a spelling variant reaching exactly one of them renders. No verse-level
   tell exists in the stored rows (both are persons), so the census can only
   bound the risk pool (P2/P3), not detect instances.
3. **Compact-index collision.** Hyphen/space-stripped matching can collide
   ('baal-peor' the place vs 'baal' the god). Already number-guarded at
   build; enumerated here for completeness. Same observable as shape 1/2
   depending on sections involved.

### Probe results (live pn_binding + tipnr_entities, 2026-07-04)

*P1 — mirror tell: names that render fuzzy→person somewhere AND exact→place
elsewhere (the exact symmetric of check 7's Cushi tell):*

> **NONE (0).** No name in the live tables shows the mirror shape.

*P2 — render binds by match-kind × section (sizes the fuzzy risk pools):*

> exact person 9,880 · exact place 3,580 · fuzzy person 647 · fuzzy place 438 ·
> fuzzy other 125 · exact other 105 · versification person 39 · place 2.
> The fuzzy pools total ~1,210 of 14,816 renders (~8%).

*P3 — the fuzzy→person pool by name (top 30, 2026-07-04):*

> Dominated by two benign classes: (1) alternate spellings/transliterations
> (Melchisedek→Melchizedek, Baldad→Bildad, Nabuzaradan→Nebuzaradan, hyphen
> variants like Baalhanan→Baal-hanan); (2) the *deliberate* gentilic design —
> tribe/people names bound to the founding ancestor (Levites→Levi 229,
> Jews→Judah 213, Israelites→Israel, Ishmaelites→Ishmael, Hittites→Heth),
> the documented Table-of-Nations value, not a defect. Drill-down on the two
> non-obvious rows: `cherethite` binds to `Cherethites@2Sa.8.18` — "A military
> group", a people-GROUP entity TIPNR files in its person section (correct
> referent); `gibeonites` binds to `Gibeon@Jos.9.3` — see below.

### Follow-on finding (Session 5): the section-label defect — 3 parser faults

The Gibeon drill-down answered its own question and opened a bigger one:
`Gibeon@Jos.9.3` is typed **Place** in TIPNR's own row (the Gibeonite group's
verses are filed inside it by TIPNR's design — the bind is correct), but our
stored section says **person**. Traced to `parse_tipnr` in
`entity_resolution.py`, verified by running the production parser on the
pinned TIPNR file:

- **F1 — mixed-block sections.** Sections come from the file's
  `$==========` block headers, and the rule checks the word "person" first —
  so all 10 entities under `$========== PERSON+PLACE` headers get stamped
  person. All 10 are typed Place in their own rows: Gibeon, Shechem, Tekoa,
  Keilah, Eshtemoa, Gedor, Etam, Zanoah, Beth-gader, Ir-nahash.
  **Live impact: 97 render binds wear the wrong label** (Shechem 42,
  Gibeon 38, Eshtemoa 5, Gedor 4, Zanoah 4, Etam 2, Beth-gader 1,
  Ir-nahash 1; Keilah + Tekoa never bound). The card also stored
  person-kin fields for these places (`person = section=="person"` in the
  build's write step).
- **F2 — EXCLUDED blocks ingested.** TIPNR fences off languages, titles,
  groups, and supernatural terms under `$========== EXCLUDED OTHER`
  (Sheol, Abaddon, Gentiles, Rabbi, Greek/Hebrew/Latin…); the parser takes
  them in as bindable "other"-section entities. Live impact: 4 renders
  (`Greek@Isa.66.19`); the rest never bound.
- **F3 — documentation prose parsed as entities.** 37 footnote/legend lines
  from the file become pseudo-entities whose names are sentences. Live
  impact: **zero** — none ever bound (confirmed against `tipnr_entities`).

No wrong-identity bind was found in any of this: the verse-corroboration
rule kept the *referent* right even where the *label* is wrong.

### Verdict

1. **No new bind-level shape-guard is warranted on today's evidence** — the
   census found zero mirror-shape instances and zero wrong-referent binds.
2. **But the mirror-shape question stays OPEN**, because the P1 census keys
   on stored section labels now known wrong for 10 entities. Deciding it on
   known-bad labels would be a void zero (the audit-tools-must-fail rule).
3. **Session 6 opener (checkpointed proposal, not implemented here):** fix
   `parse_tipnr` — take each entity's own row type over the block header for
   mixed blocks, skip EXCLUDED blocks, skip prose lines — then re-run the
   binder, re-run the P1 census on trustworthy labels, and consider whether
   check 7 should assert on row-types rather than block-sections.

## Standing consequences

- The Session 4 guard and check 7 stay as-is (certified, closed).
- TIPNR is now hash-pinned (Session 5): `tipnr/TIPNR.txt`, entry 75 in
  `cert_manifest.json`; both consumers (`import_tipnr.py`,
  `build_entity_binding.py`) read the pin by default.
- Any future mis-bind report should first be classified against the two
  shapes above; a third shape is a new finding with its own evidence.
