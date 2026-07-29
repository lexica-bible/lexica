# TICKET — Split "Matched by name" label by name-ownership confidence

Filed 2026-07-29 (JP handover, post-census verdict). Status: OPEN, unstarted.

## Context
PN-card census (scripts/audit_pn_card_census.py, commit 8bdda27d, reviewer verdict
accepted 2026-07-29) proved the unverified half of PN slots splits ~25:1:
15,590 unbound slots carry a name with exactly one known referent, 624 carry a
multi-referent name (156 distinct names). The current "Matched by name — not
checked against this verse" label (30-detail-panel.jsx, provenance contract §4
state 2) covers both and reads like a guess. For single-referent names it isn't
a guess — the lookup has no other candidate. Reader-trust fix is wording, not
data.

## Change (app-side only, no db writes)
1. When the card path lands in bin (a) (name-matched, not verse-bound), check
   whether the extracted name has exactly one referent — the SAME referent-count
   logic the census script uses for its multi/single split (mirrors
   views_metav._name_is_multi_referent: metav people+aliases count, TIPNR person
   count). Reuse or mirror that logic; do not invent a new count.
2. Single referent → new confident label. HONESTY CONSTRAINT: the claim is
   scoped to OUR records (metaV + TIPNR), not the Bible absolutely — wording
   must say "in our records" or equivalent, and the name-lookup provenance
   (not verse-bound) must stay visible per the provenance contract.
   Final copy = JP's call; 2–3 options proposed in chat at filing time
   (person + place variants).
3. Multiple referents that somehow reach a card (should be ~zero given the
   decline path — VERIFY) → keep the current hedged label.
4. Both click paths (chip and prose) must show the same label for the same
   slot. Census found 87 slots where classification differs by click path
   (separate ticket) — do not fix that here, but don't make it worse; log if
   the label change surfaces it.

## Not in scope
Verse-verification of any slot · the parked Greek-name identity lane · the
Jacob-class 624 · any database writes.

## Acceptance (all checked LIVE)
- Seth @ 1Ch 1:1 (bin a:person, single-referent) shows the confident label.
- Jerusalem @ Jer 15:5 (bin a:place) shows the confident place variant.
- Zibeon / Cainan / Dishon still show NO person card (decline path untouched).
- Adam @ 1Ch 1:1 (bound) unchanged.
- Label identical chip vs prose on all four checks.

## Standing gates that apply
Visual/wording change → JP explicit yes on the SPECIFIC copy before ship.
Frontend edit → npm run build, commit source + app.js together.
