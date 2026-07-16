# TICKET — Gentilic mis-binding: "Canaanitess" binds to the PLACE Canaan

Status: **SHIPPED + LIVE-VERIFIED 2026-07-16.** Guard in `entity_resolution.py`
(commits `d087375` + `c4210d9`, the second adding the SAME-NAME EXEMPTION — the place's
own name is never blocked; Midian/Beth-shean/Rephaim false positives caught by dry-run
accounting: 478 flagged − 58 exempt = 420 blocked, ~6 converted to person binds, render
rows 14,803 → 14,389). Side tables rebuilt on PA (`--apply` 2026-07-16). Live checks
passed: 1Ch 2:3 Canaanitess → honest fallback (AI-tagged blurb + Strong's), no place
card; Exo 2:15 Midian → place card + map + "Matched to this verse" intact. The LOOKUP
side of gentilic names (double-star Strong's rows) still rides the head-word rebuild —
see `TICKET_headword_class.md`.

## Symptom
"Canaanitess" in 1Ch 2 (Bath-shua, Judah's wife — a woman) opens an entity card for the
PLACE Canaan.

## Where it lives
Engine: `entity_resolution.py`. `_GENTILIC_SUFFIXES` includes `itess`/`itesses` (~line 252),
so canaanitess → root "canaan"; `VARIANT_ALIASES` also folds canaanite/canaanites → canaan
(~211). From there `bind_occurrence` picks a Canaan entity. TIPNR holds BOTH a Canaan person
(Ham's son, the eponymous ancestor) and a Canaan place — `tipnr.entity_types` was widened to a
set for exactly this class. The bug: nothing checks that a gentilic surface form (a PERSON
descriptor) should not land on a place-type node, so the binder can confidently bind to the
place.

## Root cause hypothesis
Entity resolution treats the gentilic root purely as a name key. The surface form's own class
(person descriptor: -ite, -ites, -itess, -ian, -ean …) is never compared against the candidate
node's `section`. A suffix-form/type mismatch should never produce a confident bind.

## Fix spec — the gentilic guard
Add a guard to the binding tier in `bind_occurrence`:

1. Classify the surface form: if it matches the gentilic suffix set (or `is_people_group`),
   it is a person-descriptor / people-group surface.
2. Candidate typing — three possible targets, per the contract's §7 scope note:
   - **Correct target (the established design): the eponymous-ancestor PERSON entity**, rendered
     as "People / Clan" with the "Descended from X" line — that's how TIPNR models peoples and
     how ~819 existing binds (Hittites→Heth) already work. Canaanitess should bind to Canaan
     the person (section='person'), People/Clan render.
   - A true people-group node does not exist in the data (display-time classification only);
     creating one is contract open item OI-3, out of scope here.
   - **Descriptor-of-individual vs. standalone group reference (JP flag, 2026-07-16).** A
     gentilic appears in two distinct uses: standalone, naming the people ("the Canaanites
     dwelt in the land") — bind to the ancestor person, People/Clan render, as above — and as
     a DESCRIPTOR of a specific individual in-verse ("Shua's daughter, the Canaanitess",
     1Ch 2:3). In the descriptor use the word is about the person's origin, not the group as
     the subject; binding it to the individual (Bath-shua) is not achievable from the gentilic
     itself, and a confident People/Clan bind there over-asserts. Ruling: the descriptor use
     still MAY carry the ancestor-person People/Clan card (the origin info is true and
     useful), but only where the verse-corroboration tier genuinely supports it; where it
     doesn't, no-bind (Fix A floor) beats a confident bind — the guard must not fix
     gentilic→place by creating wrong confident gentilic→group binds in the other direction.
     Distinguishing the two uses automatically (apposition to a named person vs. standalone
     subject) is NOT required of the binder; the tier discipline covers it.
3. Guard rule: gentilic surface + candidate `section='place'` → **block the confident bind**:
   demote to a lower tier or no-bind (Fix A floor takes over), per the existing three-tier
   verse-corroborated design. If a person-type entity with the same root exists and is
   verse-corroborated, prefer it.
4. Re-run `scripts/build_entity_binding.py` (dry-run first, `--apply` after review) — the
   guard changes stored binds, not just render.

## Sweep — the whole class, not the one instance
The bug class is every gentilic-suffixed surface bound to a place-type node (Moabitess,
Shunammite, Jebusite, Ammonitess, …).

Detection (JP runs on PA — CC cannot query the db; read-only):

```
sqlite3 ~/bible-db/bible.db "SELECT b.name, b.book, b.chapter, b.verse, b.entity_uniq, b.kind, b.tier
  FROM pn_binding b JOIN tipnr_entities e ON e.uniq = b.entity_uniq
  WHERE b.render=1 AND e.section='place'
    AND (b.name LIKE '%ite' OR b.name LIKE '%ites' OR b.name LIKE '%itess' OR b.name LIKE '%itesses'
         OR b.name LIKE '%ians' OR b.name LIKE '%eans')
  ORDER BY b.name, b.book LIMIT 200;"

sqlite3 ~/bible-db/bible.db "SELECT b.name, count(*) FROM pn_binding b
  JOIN tipnr_entities e ON e.uniq = b.entity_uniq
  WHERE b.render=1 AND e.section='place'
    AND (b.name LIKE '%ite' OR b.name LIKE '%ites' OR b.name LIKE '%itess' OR b.name LIKE '%itesses'
         OR b.name LIKE '%ians' OR b.name LIKE '%eans')
  GROUP BY b.name ORDER BY 2 DESC;"
```

Caveats for reading the results: the LIKE-suffix net will catch a few non-gentilics (real
place names ending in -ite etc.) — every hit gets eyeballed before it counts as a bug
(dotted-number-blindness-style rule: a raw count is not a finding). The real fix reuses the
production `_GENTILIC_SUFFIXES` / `is_people_group` classifier, not this SQL approximation,
and the detector must fire on the known positive (Canaanitess, 1Ch 2) before any zero is
trusted.

## Acceptance
- Canaanitess @ 1Ch 2 no longer opens the place card. Correct outcome: Canaan-the-person
  People/Clan card IF the verse-corroboration tier supports it, otherwise no-bind (Fix A) —
  never the place, never an unsupported confident group bind.
- The sweep query returns zero true gentilic→place binds after rebuild (each residual hit
  individually justified).
- Dry-run diff reviewed by JP before `--apply` (standing rule).
