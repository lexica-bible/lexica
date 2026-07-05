# Handoff — MetaV↔TIPNR person cross-link

## Status: link table BUILT + LIVE in bible.db (data only). Not yet served.
Applied 2026-07-05 after a checkpoint backup. **1,625 person links** written to
`tipnr_metav_link` (kind='person'), covering **85.4% of person-card view traffic**
(render-count proxy). Serializer + frontend NOT done — clicking a bound person still
renders the thin TIPNR card until the next task ships.

## What it does
A bound TIPNR person entity (thin card: one line + kin) is cross-linked to its rich
MetaV person record (David: badges, born/died, kin +N, Nave's) so the panel can render
the rich card while TIPNR stays the identity spine.

MetaV's verse anchoring is NOT in `metav_people` (bio columns only) — it's in
`MainIndex.csv` (unloaded), which tags every KJV word with a PersonID + verse + WordID,
and `StrongsIndex.csv` (WordID→StrongsID). We distill those into two slim staging tables
rather than loading 790K rows into bible.db.

## Scripts (both PA, dry-run by default)
- `scripts/build_metav_person_index.py` — reads MetaV CSVs, writes a standalone
  `metav_index.db` (staging, PA-only, `*.db`-gitignored): `metav_person_strongs`,
  `metav_person_verses`. Never touches bible.db.
- `scripts/build_person_metav_link.py` — reads bible.db + metav_index.db read-only,
  three-tier match, `--apply` writes kind='person' rows into `tipnr_metav_link`
  (columns: uniq, kind, metav_id, **rule, score, margin** — every link auditable to its rule).
  Re-run after any words rebuild (re-tiers from live pn_binding), same as build_entity_binding.

## The match (rules that survived review)
- **Tier 1 — Strong's-direct (202):** among same-name MetaV people, the one whose Strong's
  set (from the distill) contains the entity's own base. Deterministic, exact key. score=1.0.
- **Tier 2 — verse-overlap (1,423):** tiebreaker for Strong's collisions (26 Zechariahs, all
  H2148). CONTAINMENT of the entity's refs in the MetaV person's verse set (asymmetric — TIPNR
  refs ⊆ MetaV's fuller list). Must clear **floor 0.5 AND beat the runner-up by ≥0.30**.
  1,362 of 1,423 land at containment 1.0.
  - **Key lesson: the safety signal is MARGIN, not score.** A low score with runner-up ~0 is
    safe (partial MetaV coverage, unambiguous winner). A decent score with a runner-up carrying
    a real share of the refs = the refs are SPLIT across two same-name records = ambiguous → residual.
- **name-only DEMOTED (7):** a lone name-match Strong's couldn't confirm. Retired rule, not linked.
  Shelah@Gen.10.24 proved why — 8 MetaV verses, 0 overlap = the *other* Shelah.
- **residual (56):** hand-list, ranked by traffic, tagged with why overlap failed.

## Two things flagged during review (log — not blockers)
1. **Simon Magus double-record.** `Simon@Act.8.9 → 2752` and `Simon@Act.8.13 → 2753` are two
   TIPNR entities landing on two different MetaV records inside one Acts 8 story. Likely one man
   split (TIPNR at a chapter boundary, or MetaV double-recorded). Both links individually
   defensible and above the margin line — but a **candidate future merge**. If a rich card shows
   on 8.9 but not 8.13, or shows different bios, this is why — not a mystery.
2. **Titles are unlinkable BY DESIGN.** Pharaoh (and Caesar/Tetrarch/Augustus/Candace) are borne
   by many different men — never one bio. The script now forces them to residual tagged
   `title(unlinkable)` so the top-N hand pass skips them. Their real end-state is a **title card**
   (People/Clan-style), not a hand-curated single link — the serializer's job below.

## Next task (its own reviewed pass) — serializer + frontend
- Resolver: bound person → `tipnr_metav_link` (kind='person') → render the rich MetaV card
  (reuse David's existing component, no new styles per design.md); fall back TIPNR card →
  Strong's-only. No new lookups — one join.
- **People/Clan precedence MUST win:** a group-gloss click (Hittites→Heth, the eponymous-ancestor
  binds) keeps the People/Clan card from tonight's classifier — NEVER the ancestor's rich MetaV
  card with kin rows. `is_people_group` in entity_resolution.py already gates this at serve time;
  make the rich-card branch sit *behind* it.
- Title entities (residual `title(unlinkable)`) → the title-card treatment, not a bio.
- Licensing unchanged: MetaV is share-alike — in-app display only (already live), stays OUT of any
  dictionary-export path. The link table adds no new leak route.

## Queued behind that — reopen E's parked PLACE cross-link (no OpenBibleInfo needed)
MainIndex carries **PlaceID and YearNum** per word too. ONE extraction pass (persons + places +
time) yields four derived tables — `metav_person_{strongs,verses}` (built) plus
`metav_place_{strongs,verses}`. That gives place→verse and place→Strong's the identical way,
which is the per-referent key `metav_places` lacked — so E's "park it for OpenBibleInfo" decision
should be revisited with this in hand (person panels + a time-scoped map fall out of the same distill).
