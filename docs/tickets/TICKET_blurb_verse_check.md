# TICKET — AI reference-blurb verse-check certification (scoped, NOT started)

Opened 2026-07-30 (JP + reviewer, from the Stephen Acts 7:59 card discussion).
Interim fix SHIPPED same day: disclaimer reworded to "AI-written summary — claims
not verified against the verse text" (the old "not verse-checked" read as "we
didn't check which verse this is").

## The goal
Make "verse-checked" a state a blurb can EARN, not just a disclaimer. Today every
AI reference blurb (the `.detail-ai-caveat` population, served via
/api/metav/ai-description) is generated for the right verse by construction, but
nothing ever verifies that what the prose CLAIMS is true.

## Step 1 — scope (before designing anything)
Pin the exact serving population: how many cached blurbs exist, how many slots can
request one (the AI-only card population: Tier-3 name-path + fall-through slots).
Census with the standing read-only pattern.

## The check (borrows the Lexica-dictionary definition-engine tooling)
- **Claim decomposition:** each blurb makes discrete claims (Stephen is a deacon;
  he is being stoned; he calls on Jesus). Every claim needs a corroboration
  source or the blurb fails.
- **Evidence tiers, pre-registered:** verse-text-attested (strongest) →
  context-window-attested (pericope) → record-attested (TIPNR/metaV entity data)
  → uncorroborated (fail).
- **DESIGN QUESTION 1 (doctrine):** does cross-reference attestation count?
  The Stephen blurb's "deacon" claim isn't in Acts 7:59 — it comes from Acts 6.
  If it counts, how is it cited?
- **DESIGN QUESTION 2 (failure policy):** a failing blurb either (a) stays
  flagged with the honest label, (b) is regenerated under a constrained prompt,
  or (c) is suppressed. Pick one, reviewer-ruled.
- **Output:** pass → badge flips to a "verse-checked" state with the evidence
  class STORED AS DATA (survives rebuilds); fail → per the failure policy.

## Cert mechanics (standing template)
Frozen prompt if regeneration is involved · calibration batch first (~20 blurbs
hand-adjudicated to validate the checker before scale) · review-what-ships on
cached draws · detector control proving the checker can fail · checked-state
stored in the db, not derived.

## EXPANDED SCOPE (JP + reviewer 2026-07-30 — same lane, bigger deployment target)
JP wants the verse-specific AI summary on ALL PN cards (people/places/groups),
not just AI-only cards — it's the one layer no reference source provides
(narrative context: "this is the moment Stephen is being stoned"). Ruled valid.
Shape: **cert first** (this ticket's mechanism is the prerequisite — unverified
prose must not sit on certified cards without earning the verse-checked state),
then **generation-from-bound-facts** (feed the blurb generator the certified
entity: verse + TIPNR record + kind='ruled' identity — ground truth in, better
prose out; the rulings arcs are literally this feature's input layer), rolled
out by entity class with sampling like the definition batches. Cost model =
definition engine (pennies per blurb, one-time, rebuild-stamped).

## Sequencing
Behind the current Lexica-dictionary batch work (it borrows that tooling) AND
rulings batch 2. SCOPED-NOT-STARTED — no blurb generation until the cert
mechanism exists. Waits for a batch slot + JP raising it.
