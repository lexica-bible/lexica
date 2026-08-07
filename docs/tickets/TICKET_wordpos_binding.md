# TICKET — word-position binding lane (same-verse same-name multi slots)

Opened 2026-08-07 at lane unpark (JP's ordering — next in the card-work queue,
TODO.md). **Census-first charter: nothing is designed and no data is written
until the re-derived census is confirmed and the reviewer has ruled on the
open questions below.**

## Charter (assembled — no prior ticket existed for this lane)
This lane never had its own ticket or a frozen member list. The charter is the
sum of:
- TODO.md open-lanes block: ~118 same-verse same-name multi slots + malchiah
  Ezr 10:25 + the mary class (8 verses / 16 slots); un-partitionable at the
  (book,ch,vs,name) bind key BY CONSTRUCTION; needs word-position-level binding.
- TODO_ARCHIVE 2026-07-30 census close: ≈118 slots = mary 16 + 102 across 22
  tail names (genealogy lists genuinely naming two like-named people in one
  verse — the Dishon pattern). The census certificate (banked verbatim there)
  identifies this class as one of the two things the automatic binder can't do.
- DRILL_lane_c.md named residue: the 5 multi-in-chapter slots (azariah 1Ch 6
  genealogy, joash 2Ch 25:20 both kings, benaiah, harim) — related shape,
  chapter grain not verse grain; NOT auto-folded here (ruling R3 below).
- DRILL_witness_divergence.md: malchiah Ezr 10:25 demoted from lane A to this
  lane (two Malchiahs in the verse).

## STALE-CENSUS status (binding)
The ~118 was derived 2026-07-30. Since then: the PN-star rebuild ride shipped
2026-08-05 and 17 lane-③ hand repairs landed 2026-08-07 — positions, brackets,
and identity assignments have all moved. The live-vs-source rule (55/71
phantoms in lane ③) applies: **the figure is a hypothesis until re-derived
against the live table.**

## Census tool (this session's build)
`scripts/census_wordpos_multi.py` — READ-ONLY, mirror functions copied from
`scripts/audit_pn_lanes.py` (the census pipeline's production mirrors; read in
full before writing this). Predicate: identity slot with a words row, chip-order
clicked name multi-referent (metaV+TIPNR test), UNBOUND (exact or unique-compact
bind test, same as the lanes script), same normalized name on ≥2 slots in the
same verse. Reports separately (not in the lane figure):
- **bound-PAINTED bucket**: same-name multi verses where a render bind EXISTS —
  the one (book,ch,vs,name) bind paints every same-name slot, possibly wrong
  for one of them. New sizing input, was invisible to the unbound-only census.
- Excluded by construction: the 340 no-words-row identity slots (own deferred
  lane, TODO) — the census inner-joins words.
Controls: known positive malchiah Ezr 10:25 must appear; known negative jesus
Mat 8:5 must be absent (this one only proves the ≥2-slots threshold, not the
bind test — the positive control is the load-bearing one). Either failing →
exit 2.

Run on PA:
```
cd ~/bible-db && PYTHONIOENCODING=utf-8 python3 scripts/census_wordpos_multi.py bible.db
```

## Diff frame (what the fresh census is checked against)
No frozen member-by-member list exists, so the diff runs against the charter's
NAMED members + aggregates; the fresh output then becomes the frozen list:
- total ≈118 slots (drift expected and must be explained by the 8/5 rebuild /
  8/7 repairs, not waved through)
- mary: 16 slots / 8 verses expected
- malchiah Ezr 10:25 present (also the control)
- ~22 tail names besides mary, genealogy-heavy
- azariah/joash/benaiah/harim should NOT appear at verse grain (they are
  chapter-grain residue) — if one does, that's a finding to walk down
CENSUS OUTPUT + DIFF VERDICT: (pending JP's PA run — paste below)

## DECIDE AT SESSION OPEN — open questions for the reviewer
The charter carries no explicit banked rulings (no prior ticket), so these are
the open questions, with recommendations (standing delegation: CC+reviewer
recommendation applies as the ruling):
- **R1 — class predicate.** Confirm the census predicate above (unbound
  Jacob-class slot, same normalized name ≥2 slots per verse, chip-order names)
  as THE lane membership definition. Recommendation: yes — it is the 07-30
  census's own frame re-run, not a new definition.
- **R2 — bound-painted bucket scope.** Does the painted bucket (bind exists,
  2+ same-name slots, one bind paints all) belong to this lane? It shares the
  mechanism (word-position grain) but was outside the ~118. Recommendation:
  census it now (done — separate bucket), rule on scope AFTER the numbers are
  on the table; do not fold into the lane figure silently.
- **R3 — chapter-grain residue.** The 5 multi-in-chapter slots (azariah, joash,
  benaiah, harim) are the same disease at chapter grain. Recommendation: keep
  OUT of this lane's verse-grain census; revisit only if the mechanism design
  turns out to cover them for free.
- **R4 — mary class + malchiah fold-in.** TODO.md already folds them in.
  Recommendation: confirm — same predicate catches both, no special-casing.

## Status
OPEN — census command handed to JP; verdict owed on the paste before any
predicate or design work. Design pass (the actual word-position binding
mechanism + card wording) is gated behind the confirmed census + rulings.
