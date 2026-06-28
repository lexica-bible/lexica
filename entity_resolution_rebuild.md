# Entity Resolution Rebuild — Final Design Brief (Issue 2)

Status: **design only, no code.** Fix A (verse-scoped AI blurb + map-pin guard) is already
live and serves as the permanent floor. This brief is the rebuild design, with every number
confirmed by the read-only probes (`scripts/audit_entity_resolution.py`,
`scripts/probe_tipnr_fullset.py`).

## Objective
Metric = **percent rendered-and-correct, with zero confident-wrong** — not percent-bound.
- A **floor-miss** (correct-verse blurb, no pin) is honest: it looks like a model description,
  asserts nothing false with authority, the reader knows what they're getting.
- A **wrong bind** renders TIPNR's real bio for the *wrong* entity — confident, sourced-looking,
  indistinguishable from a correct card, uncatchable by the reader. It is the project's core
  disease (the LSJ bundled freight, the blurb that fabricated Acts verses). It is weighted as a
  **loss**, not a smaller win.
- We **accept a lower bind rate to eliminate confident-wrong.** Rendered-correct dropping below
  raw bind rate is the system working.

## Spine — the global render rule
A bind **renders only when the clicked verse corroborates it** (the verse is in the bound
entity's reference list, after the versification map). Otherwise it **floors** (Fix A). Applies
everywhere, every tier. The count proves the rule is a sniper, not a flood-wall: ~25
confident-wrong cases exist corpus-wide (2,167 number-only binds × 1.1% measured pollution).

## The binder — verse-primary, name-first
For an occurrence `(surface name N, clicked verse V, stored number B)`:
1. **Exact name + verse** — N matches an entity's headword/recorded spelling and that entity
   lists V → bind & render. The number is metadata here (the 304 / 1.1% disagreements are harmless).
2. **Fuzzy name + verse** — N matches by normalization (gentilic stem, KJV/LXX spelling variant)
   and the entity lists V → bind **only if B also sits in the entity's number cluster** (fuzzy can
   over-match, so it needs the second key).
3. **Multi-corroboration** — if ≥2 entities of name N list V: word-position tiebreak (verse slots
   in reading order ↔ entities by first appearance, when the counts match); otherwise **floor**.
   Never guess. These binds are tagged **HOT** for hand-check (the order is a heuristic).
4. **Everything else → floor.** A number-only link (no name match) does **not** render — that is
   the confident-wrong path.

Number is metadata behind a name link; it is load-bearing only on the 2,167 number-only binds,
which WS2/WS3 normalization shrinks toward zero.

## Scope — three tiers (bind where broken, leave where working)
"Working today" = unambiguous AND has a metaV row.

- **Tier 1 — Ambiguous set** (724 names, 15,203 occ). Bind, verse-primary, floor on any
  non-corroborated bind. Measured: **95.2% bound, 2.5% soft, 2.3% hard.**
- **Tier 2 — Unambiguous, no metaV row** (2,823 occ). Bind — the non-homonym Cushi class, bare
  AI blurbs today, nothing working to regress. The gate is **load-bearing** here: pollution is
  4.5% (vs 1.1% corpus-wide) and 1,259 binds are number-reliant vs only 626 real name+verse. Most
  upside (blurb → real bio) coincides with most confident-wrong risk; the gate is the only thing
  separating them. **32.3% hard stays on the floor.**
- **Tier 3 — Unambiguous, with metaV row** (13,970 occ). **Leave on the working name-path.**
  Binder is fallback only, never primary. Do NOT blanket-bind — name resolution already works;
  binding would introduce 3.5% (~488) as new wrong-or-floor where there was none. No upside under
  a correctness objective, only regression risk.
- **Re-tier on every data load** (requirement, not note). Tier assignment is derived at load,
  never cached; a name that later gains a twin auto-routes to the bound path. This is the standing
  maintenance cost — the accepted price of not regressing Tier 3.

## WS1 — Versification map (confirmed)
Derived from documented Hebrew/Greek-vs-English differences **only**; the deltas merely validate
(a documented remap must land on a same-name entity to count). **117 recovered:**
- **Psalms superscription (+1): 116.** The per-chapter pass correctly floored the few that were
  not real superscription shifts (book-average had over-counted them).
- **Numbers 16/17 (English 16:36-50 = Hebrew 17:1-15): 1.** The land-test confirms ABP follows
  Hebrew numbering there, so the documented offset binds.
- **Lev, Est, Lam 1, and every hidden-offset flag: floored.** No named documented difference
  (Lamentations 1 is 22 verses in both Hebrew and LXX — the prologue is an added line, not a
  renumber; the −3 was pronoun-gap geometry, the same clean-looking-but-sourceless trap as Lev
  d−1). **A flag enters the map only if its documented difference can be named.**
- **~2,405 floored = the floor class by design:** mostly pronoun-gaps (ABP names the person where
  English wrote "him") tagged **"referent-known, not-named"** + genuine no-entity misses.
  Strict-floor — binding an unnamed word is the fabrication we kill. Recoverable later by a real
  resolver, never by a chapter-ownership guess.

Standalone lookup table, serves all tiers. Pure correct-bind recovery, zero wrong-bind risk
(entity is already right, only the verse number moves).

## WS2 — Name normalization (the Cushi class)
**One lever:** gentilic stems + KJV/LXX transliteration variants expand the name index, so
surfaces like "Cushi" → Cush ("Cushite") and "Pharez" → Perez bind by **name+verse (robust)**
instead of falling onto the polluted number path. Same lever as WS3 below — it shrinks the 2,167
number-only population.
- **The Cushi runner (canary): two keys, both required.** The gentilic index makes "cushi" reach
  Cush, but stored H3570 ∉ Cush's cluster, so the fuzzy guard fails → still floored. So WS2 also
  needs a **by-verse number correction** of the proven mis-tag: the 6 occurrences in 2 Samuel 18
  → H3569 (the verse-identified Cushite form). Curated, scoped to the 6, reversible.
- **By-verse only — never a global H3570 swap.** Footprint: H3570 also lives at Jer 36:14 (the
  real Cushi, correctly H3570) and Zep 1:1 (mis-stored H3570 but binds right by name+verse —
  harmless). Leave both.
- **Acceptance:** (a) the 6 runners render Cush/Cushite; (b) **no word outside 2 Samuel 18 changes
  binding** — prove the fix is inert elsewhere.

## WS3 — Residual verification (a step, not a build)
After the gate + normalization, hand-verify the residual; at this size we get certainty, not an
estimate.
- **Number-only binds: 2,167; flagged (shared-number OR no-stem): 1,396** — but **transliteration
  normalization runs first**, folding the spelling variants (pharez/perez, jeconiah/jehoiachin,
  salathiel/shealtiel, mizraim=Egypt) into correct name+verse binds. **Hand-check only what
  survives normalization** — the true referent mismatches, which look very few.
- **Ordered-multi (positional): 83, HOT** — stay hand-checked. `gibeon → [abiel, gibeon]` and the
  double-Gazez verse are the real positional cases where order can mis-assign and still pass the gate.

## Bridges — metaV is enrichment only, never identity
- **People → dates: 51.5% relationship-keyed** (Rate 2). Decoration; the misses are date-less
  obscure people. Identity + content come from TIPNR.
- **Places → coords: 99.5% is coverage, not correctness** (Rate 3). Name-only reach can't pick the
  right row among same-named places, so **ambiguous pins stay hidden — Fix A's guard stays** (no
  pin when the place match is ambiguous or lacks its own coords). The rebuild does not change the
  map story.

## Architecture
**TIPNR is the identity/content spine** — its own bio, references, and descriptions render the
card, which is why binding kills the fabrication class without needing metaV. **metaV is
opportunistic enrichment only** (coords/dates), reached by relationship for people and name-only
for places.

## Build order (when greenlit)
1. WS1 versification table (standalone, zero risk) — +117 corroborations.
2. WS2/WS3 name normalization (gentilic + transliteration) — moves the bulk of the 2,167
   number-only binds onto the robust name+verse path.
3. The binder + global render rule, Tiers 1 & 2 only (Tier 3 stays on the name-path).
4. Cushi by-verse number correction (the 6) + its two acceptance tests.
5. WS3 hand-verification of the post-normalization residual + the 83 ordered-multi.
6. Re-tier-on-load wired in.
