# DESIGN PASTE — word-position binding lane (2026-08-07)

Charter: TICKET_wordpos_binding.md (frozen baseline wordpos_census_20260807.txt =
96 slots / 47 groups / 28 names; R1–R4 banked; three census riders). This paste is
built to the reviewer's four-point design bar quoted in the ticket. NO data has
been written; nothing here runs before the reviewer rules on this design.

---

## 1. Partition mechanism — how a slot maps to its referent, and where it lives

### The seam that already exists
- Every reader click carries the word's `position` (the words-table slot number).
  The chip already sends it to `/api/pn/greek-identity?...&pos=` — position is IN
  the click payload today; only the entity lookup ignores it.
- `pn_binding` is keyed `(book_num, chapter, verse, name)` — one row per name per
  verse. On all 47 groups the binder correctly DECLINED (`rule='multi'`,
  `render=0`): the key cannot say which slot is which. That is the whole disease.

### The mechanism: a per-slot bind table beside pn_binding, never inside it
New side table **`pn_slot_binding`**, PA-only, written ONLY by
`build_entity_binding.py --apply` (same run that writes pn_binding, so a words
rebuild re-lands it automatically):

```
pn_slot_binding(book INT, chapter INT, verse INT, position INT,
                name TEXT,          -- normalized printed head AT THIS SLOT
                entity_uniq TEXT,   -- TIPNR entity (person OR place — see §2)
                kind TEXT,          -- 'slot-ruled'
                evidence_class TEXT,
                render INT, tier TEXT,
                PRIMARY KEY (book, chapter, verse, position))
```

Deliberately NOT a `position` column on pn_binding: every existing pn_binding
read assumes the (book,ch,vs,name) key is unique (`LIMIT 1` lookups, the
chip-merge derivation, the gates). Slot rows in the same table would let a
verse-grain read pick up a slot row and paint every same-name slot with it —
manufacturing exactly the bound-painted disease R2 just ruled out of this lane.
Separate table = the 96 stay in their own risk class (unbound today; a fix can
only add), and pn_binding's frozen behavior is untouched byte-for-byte.

### Source of truth: a per-slot rulings file, mirroring pn_hand_rulings.tsv
Repo-versioned **`scripts/pn_slot_rulings.tsv`** — the slot analog of the proven
hand-rulings pipeline (one row = one slot, citable forever):

```
name  book  chapter  verse  position  entity_uniq  referent_kind  evidence_class  evidence_quote  rationale  flags
```

- `name` = the printed head AT that slot, stored per-row. This is the staleness
  tripwire: at every `--apply`, the builder reads the live words row at
  (verse_id, position) and compact-compares its `english_head` to the TSV name.
  Mismatch (a rebuild moved positions, an edit changed the head) → that row is
  REFUSED and reported, never landed — the slot falls back to today's honest
  Fix-A floor instead of serving a wrong identity. Same expect-stale → catch-up
  pattern as the retirement chain.
- The Ezr 10:25 appendix pair rides this format natively: two rows, names
  `malchiah` (p10) and `malchijah` (p16), `flags=variant-spelling` — no
  predicate widening, exactly per the R1 codicil.
- Precedence guard at build: a slot row may land ONLY where the verse-grain
  binder still declines that name (`rule='multi'`/no render bind). If a future
  binder run flips the name to a verse-grain render bind, the builder stops and
  reports the collision (the gate_pn_rulings hot-row rule, applied here) —
  slot and verse grain can never both paint one verse's name.

### Serve path (one added lookup, byte-same fallback)
`/api/metav/entity/<name>` gains an optional `pos` param (frontend `metavEntity`
sends `w.position`; `pnClickPayload` stays the ONE payload producer — it only
passes through what the word already carries). Lookup order:

1. `pn_slot_binding` at (book, chapter, verse, pos) with render=1 AND
   compact(name) match → serve that entity through the EXISTING card path
   (tipnr_entities → section/kin/coords/metav enrichment — the place branch and
   person branch already exist, §2).
2. No slot table / no `pos` / no row → today's verse-grain lookup, unchanged.

Table-existence-gated like every side table (absent → pre-build behavior, deploy
safe). Chip-merge, occurrence line, Fix-A floor all follow the served entity
exactly as they do for a verse bind — no second card path.

### Chapter grain (R3)
The key (verse, position) mechanically extends to the 5 chapter-grain cases —
but per R3 that is a scope-extension question that RETURNS TO THE REVIEWER after
the 96 are done. Nothing in this design pre-commits it.

---

## 2. Per-slot identity evidence — and referents that are not people

### The model never says "person"
`entity_uniq` points into `tipnr_entities`, which holds persons AND places
(`section` column) — the card already branches on it (place → coords/map path,
person → kin/metav path). The TSV's `referent_kind` (person|place|group) is a
declared expectation checked against the entity's own `section` at build time
(mismatch → refuse). So gilead Jos 17:1 / Num 26:29, jezreel Hos 1:4, penuel,
haran Gen 11:31 are two SLOTS pointing at two ENTITIES that happen to differ in
kind — nowhere does the schema, the TSV, or the card assume two people. (Rider
2 satisfied structurally, not by a special case.)

### Evidence classes — pre-registered here, PINNED once ratified
Per the standing rule (evidence classes pinned, never loosened), the per-slot
adjudication may use ONLY these, each with a mandatory `evidence_quote` (the
printed ABP text or TIPNR record line that carries the discrimination):

- **epithet-in-verse** — the discriminating epithet is printed beside the slot
  ("Mary the Magdalene" vs "Mary the mother of James", Mar 15:40). Covers most
  of the mary 16.
- **kin-in-verse** — a parent/child/office printed with the slot matches the
  entity's TIPNR kin ("Amaziah son of Joash king of Judah … Joash son of
  Joahaz", 2Ki 14:1/13/17/23).
- **list-structure** — genealogy grammar fixes roles: in "X begat Y" with one
  name twice (1Ch 6:9 azariah p4/p6), slot order IS the father/son partition,
  each side then matched to the TIPNR entity whose own parent/offspring line
  agrees. The quote must show BOTH the structure and the TIPNR agreement.
- **locative-syntax** — the slot sits in place-grammar ("he had Gilead and
  Bashan") while the other is a person; carries the person/place pairs.
- **tipnr-ref-partition** — the two entities' own reference lists split cleanly
  and this slot's role sits in exactly one (the zerubbabel class, per-slot).
- **variant-spelling** (appendix only) — Ezr 10:25; spelling itself is part of
  the evidence and is quoted.

A slot no class can carry gets outcome **floor** — it stays unbound, honestly,
with the group still pre-registered (that IS an allowed verdict; forcing 96/96
binds would be the accuracy-bar violation). New classes require a reviewer
ruling before use.

### Where evidence lives
`evidence_quote` + `rationale` in the TSV row (repo-versioned, citable), the
class name in BOTH the TSV and the landed `pn_slot_binding.evidence_class` —
so the served row can always be walked back to its quoted evidence.

---

## 3. Red-first controls and must-fail cases

All dry-runs JP-run; verdicts per row, expected-beside-actual; display evidence
comes from the render-modeling lister only (the ②-ride rule).

**(a) Wrong-referent row MUST FAIL (the reviewer's named minimum).** The control
TSV includes a deliberately wrong row: mary Mat 27:61 p3 assigned the
mother-of-James entity WITH the Magdalene epithet quote. Two independent gates
must each catch it red-first:
- the build-time duplicate check — after landing a group, no two slots in one
  verse may carry the SAME entity_uniq unless flagged `same-referent` (none of
  the 96 currently are); and
- the adjudication re-derivation — a checker script re-reads the printed verse
  and refuses any row whose evidence_quote does not appear adjacent to the
  ruled slot's position. The wrong row must be REFUSED with the reason printed.

**(b) Stale-name row MUST FAIL.** A control row keying position p with a name
the live words row does not carry (e.g. `joash` at a position whose stored head
is `amaziah`, 2Ki 14:1) — the landing guard must refuse it. This is the
rebuild-moves-positions tripwire proven red before it is trusted.

**(c) Bracket-contiguity case (required by the bar).** Positions are DATA-layer
slot numbers; brackets reorder DISPLAY. The trap from lane ③: chip/interlinear
group only consecutive same-bracket runs, so a mis-marked interior blank
re-orders those modes while prose stays correct. Controls:
- Selection: run the render-modeling lister over the 46 lane verses and list
  every group whose slot positions fall inside or adjacent to a bracket span;
  each such group's adjudication evidence must show the CHIP-ORDER rendering in
  all three modes, proving the click at that chip sends the position the ruling
  keyed (per-mode display oracles — the standing lesson that prose passing
  proves nothing about chip mode).
- Red-first: on a COPY row, deliberately un-mark one interior blank of such a
  bracket and show the shared contiguity classifier (the same check
  `fix_lane3_star_merges.py`'s dry-run uses — imported, never re-implemented,
  per the counter-and-fix-share-the-classifier rule) FAILS it; restore, it
  passes. If the lister shows NO lane group touches a bracket, that finding is
  itself reported with the lister output attached, and the red-first control
  runs on the nearest bracket-adjacent painted-bucket verse as a read-only
  display control instead — the case is exercised either way.

**(d) Verse-grain no-regression control.** With the slot table live, a bound
single-referent verse (e.g. a David click) fetched WITH `pos` must serve
byte-identical to today; and one of the 96 fetched with NO slot row must still
404 → Fix A floor exactly as now.

**(e) Discovery-time carve-out (rider 3).** Any wrongly-painted NEIGHBOR found
while adjudicating a group is recorded in the bound-painted follow-on ticket at
that moment, in the group's verdict row — never re-derived later.

---

## 4. Pre-registration format for the 47 groups

One frozen file, written and reviewer-ratified BEFORE any adjudication verdict:
**`docs/tickets/wordpos_prereg_20260807.txt`** — the 47 groups verbatim from the
frozen census (plus the Ezr 10:25 appendix block), each group a block:

```
GROUP 07  2Ki 14:1  joash  slots p3, p12
  expected partition: two entities (referent_kind person / person)
  p3   proposed: <entity_uniq>   class: kin-in-verse
       quote: "<printed ABP text adjacent to p3>"
  p12  proposed: <entity_uniq>   class: kin-in-verse
       quote: "<printed ABP text adjacent to p12>"
  fallback outcome if evidence fails: floor (both slots stay unbound)
```

Rules of the format:
- Every slot pre-registers its proposed entity, referent_kind, evidence class,
  and quote BEFORE the dry-run — the dry-run then confirms or refuses per row;
  a refused row's outcome flips to floor, never to a second guess in-flight.
- Person/place groups declare mixed kinds up front (gilead: p16 person /
  p23 place) so a two-people assumption can't creep in at adjudication.
- Three-slot groups (1Ch 1:41 dishon, Act 1:13 james) list all three; partial
  outcomes are legal (two bound + one floored) and recorded as such.
- The appendix pair is in the file, flagged, adjudicated with the rest, never
  counted in the 96 (R4).
- The file is frozen at ratification; any change after that is a new reviewer
  round, not an edit.

## Build/ship order (for scale, after design ratification)
prereg file → reviewer ratifies → adjudication fills the TSV group-by-group
(evidence quotes from JP-run dumps of live rows/prose) → controls (a)–(e)
red-first → JP-run dry-run of the full TSV, per-row verdicts → `--apply` →
serve-path change ships (frontend `pos` param + endpoint lookup) → live spot
verification on named groups in all three render modes.
