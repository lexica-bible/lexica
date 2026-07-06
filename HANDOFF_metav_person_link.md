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

## SERIALIZER PASS DONE (2026-07-05) — shipped + a title-rule CORRECTION
The rich-card serializer + frontend are built (`views_metav._person_card` shared by the name path
and the bound path; `metav_entity` adds a `metav` field via one join to `tipnr_metav_link`; frontend
`MetavPersonBody` in 30-detail-panel fills the bound card body under the TIPNR-spine frame). Ship
decision on titles = **A, ship as-is** — which CORRECTS flag #2 above. Read this before "fixing" the
title check in any rebuild:

- **The `TITLES` exclusion in build_person_metav_link.py did NOT fire on the pharaohs, and that was
  RIGHT, not a bug to fix.** (It missed because entity heads are longer than the bare word "Pharaoh",
  so `key(disp) != "pharaoh"`.) TIPNR has SEVEN per-referent pharaoh entities — Abraham's / Joseph's /
  Exodus / Solomon's / Hezekiah's / Jer / 1Ch — each verse-overlap-linked to its OWN metaV Pharaoh
  record (2328–2335). Those seven links are CORRECT: the verse-bind already fixes WHICH pharaoh, so
  each link is a specific-man claim — exactly what the join guarantees. Had the title check fired it
  would have DELETED seven good links.
- **The title rule's real target is a title COLLAPSE** — an unbound/composite title matched to one bio
  for many men. That case IS handled: the broad-span `Pharaoh@Exo.1.11-Heb` entity failed overlap
  (best 0.55 / split) and is correctly UNLINKED (residual `title(unlinkable)`). Verified end-to-end
  2026-07-05: the seven specific pharaohs `linked->`, the composite one UNLINKED.
- **So the rebuild fix (if any) is NARROWER, not wider:** the title check should catch unbound/composite
  title entities, never per-referent title entities that verse-overlap resolved cleanly. Do NOT widen it
  to catch `Pharaoh@Exo.3.10` — that deletes correct links.
- **This is the pattern the PLACES edition will hit too** (Zion, Rabbah, the several Antiochs): specific
  referents link, the composite/ambiguous one quarantines. The system got title-vs-referent right here;
  the place builder should aim for the same shape, not a blanket name-based title block.
- Serializer safety that made A clean: `_person_has_bio` gate (born/died OR ≥2 kin) sends the bio-empty
  pharaoh records to the thin TIPNR card anyway — the fallback chain (rich → TIPNR → Strong's) doing its
  designed job, no title special-case in the view. **People/Clan precedence** ships as required, keyed on
  the SAME `is_people_group` predicate (no copied set). David is NOT bound (absent from pn_binding), so it
  keeps the name-path card unchanged — the `_person_card` refactor is what keeps those two in step.

## Live-smoke found a PRE-EXISTING name-path bug — FIXED this pass (2026-07-05)
Gen 36:37 "Saul" (the EDOMITE king) clicked in an unbound spot — Genesis has ZERO Saul binds, so it
fell through to the bare-name metaV lookup, which matched "Saul" → served metav 2478 = KING Saul
(Kish/Jonathan/died Mt. Gilboa) on an Edomite king list. Wrong man's family as fact — the
wrong-referent analog of the loaded-gloss freight problem. Not a serving-pass regression and not a
link-table error (the link `Saul@1Sa.9.2-Act → 2478, strongs, 1.0` is correct — that entity IS King
Saul). MetaV even has the right man (2562/2563 "Shaul") but the name path can't reach him: ABP spells
the Edomite "Saul", MetaV spells him "Shaul".

**Fix (name path only, `views_metav._name_is_multi_referent` + a guard in `metav_person`):** before
serving a bio from a bare name, test referent multiplicity — several metav_people candidates (name OR
alias) OR several TIPNR person entities under the surface name. If multi-referent → return
`{"ambiguous": true}`, no bio; the frontend then shows Strong's + occurrences (+ its verse-scoped AI
note), the honest card. Single-referent names (David) unaffected — still rich. The verse-BOUND path is
untouched: a bind already fixes which man, so King Saul at 1Sa 9 and the seven pharaohs still serve.

## Binding coverage (David absent from pn_binding) — PRIORITY RAISED, now user-visible cost
Before this fix, an unbound click still fabricated a specific bio, so the coverage gap was invisible.
AFTER it, unbound = a thin card. So every major figure missing from `pn_binding` — David (absent
entirely), and any occurrence outside a bound range — now visibly LOSES its rich card until it binds.
Binding is what EARNS the rich card back. So the entity-resolution binding-coverage task is no longer
housekeeping — raise it. Same class for every multi-man name clicked outside bound ranges (Zechariah,
Shallum, Azariah, Joseph). Note David may be TIPNR-absent too (earlier `head='David'` / `uniq LIKE
'David%'` both returned nothing) — worth confirming as part of that task.

## Next task (its own reviewed pass) — serializer + frontend  [DONE — see the correction block above]
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
