# HANDOFF — Provenance contract / entity arc (session of 2026-07-16)

Session closed clean; wrap ran (living docs + memory updated). This is the pick-up sheet.

## 1. Shipped and LIVE-VERIFIED today
- **Provenance contract** — `docs/PROVENANCE_CONTRACT.md` committed + JP-gated: source-of-record
  labeling, three-state verse-corroboration, one tooltip registry, name-display rule, entity
  taxonomy (grounded by PA inventory; TIPNR "other" bucket = 34 entries, open items OI-1/2).
- **Gentilic guard** (through `2a88176`): a gentilic never confidently binds a place entity,
  EXCEPT the place's own name (same-name exemption — Midian class, caught by pre-apply
  accounting). -itess(es) added to the people classifier. Live checks passed both directions
  (Canaanitess 1Ch 2:3 → honest fallback; Midian Exo 2:15 → place card + map).
- **Binding re-apply**: pn_binding render rows **14,389** (was 14,803; 420 blocked − ~6
  converted = 414 net, predicted 14,390 — arithmetic CLOSED before apply). tipnr_entities 2,164.
- **Highlight cited-set fix, all three legs** (`d948a4d` + `d925983`, ticket closed `bce0aa3`):
  acceptance filter on fresh answers · unified prefixed-only frontend builder · read-time
  cleaning (server cache + browser-stored threads via `/api/lexicon/function-strongs`).
  Live-verified on the Gen 1:1 arche thread (articles dark, content words gold, "ho" chip gone).
  Ticket: `docs/tickets/TICKET_highlight_cited_set.md` (claim-failure lesson logged inside).

## 2. Open fronts — nine items, each with pointer + gate
1. **Rebuild session (NEXT UP)** — charter `docs/REBUILD_SCOPE_headword.md`. Gate zero = JP's
   disk-space paste at run time (his PA quota, NOT the NFS df). Big pre-run lift: the alias map,
   ~1,690 hand-checked variant rows (`docs/tickets/TICKET_missing_strongs_pn.md`). Also in the
   run: RC-2 emit fix (477 blank rows), RC-1 scoped head pick, backup keep-count 7→3, owed
   finish_rebuild.sh acceptance check. Fresh session, HIGH effort, /rebuild-words procedure.
2. **Synthesis Greek script** — `docs/tickets/TICKET_synthesis_greek_script.md`. Parked, nothing
   built. Direction: render the lemma from the DB keyed on the cited number, not prompt changes.
3. **Greek-name migration** — `docs/DESIGN_greek_name_identity.md`. Gate: JP's five rulings
   (Q1–Q5, incl. the LXX-only render wording = Q3). Sequenced AFTER the rebuild — its audit diff
   needs clean heads.
4. **Provenance audit sweep** — contract §8 checklist, chartered as AUDIT ONLY (a follow-up
   session; the contract defines "correct", the sweep measures).
5. **Contract RENDER build work — chartered NOWHERE (the gap JP caught)**: §6 name-echo fix
   (Midian card, known failure E), §5 tappable tags + one tooltip registry, §4 name-path state
   line, AI tag back on summaries. TODO.md entry exists; needs a charter before build.
6. **pn_binding hand-check rows** — 65 HOT + 798 number-only suspects in
   `scripts/pn_binding_hot.txt` / `pn_binding_numonly.txt` on PA ("step 5"). Never scheduled;
   candidate to fold into the audit session. All floor safely meanwhile.
7. **Descriptor-of-individual gentilics** — can "Canaanitess" (Bath-shua) earn a real bind
   (tier-gated People/Clan, or the individual via apposition)? Ruling record in
   `docs/tickets/TICKET_gentilic_binding.md`; explicit audit-session line item per JP.
8. **5 known-red tests** — tests/test_lexica_draw_cache.py fails without the live DB on any
   clean checkout. Not in the curated gate lists (no gate lies), but unticketed red rots —
   TODO.md entry; fix = skip-without-DB guard or fixture.
9. **Ask-corpus counts + zero-bars** — chips show total-Bible counts, should be search-pool
   counts (needs backend payload work, do NOT approximate); `hasCount:false` rows render like
   tiny counts (silent-fallback violation). TODO.md entry; JP's timeline.

## 3. Standing rulings (today)
- **R-1**: words rebuild approved; batch everything pending into ONE run (the charter's list).
- **R-2**: Greek-name identity approved as direction — SUPERSEDES the old "Hebrew-key, don't
  re-pitch a pure Greek re-key" rule (data-model.md + memory updated). Honest "ABP-only form,
  no Strong's mapping" state where nothing maps; never fabricate.
- **Backup retention**: never delete the only pre-rebuild backup; keep most-recent known-good,
  drop older. Keep-count 7→3 rides the rebuild. (~540 MB of old bible.db dailies trimmed today;
  July 13/14/15 kept.)
- **Scoped head-pick**: RC-1 name-preference applies ONLY to star/PN-tagged slots — the 14,938
  measurement proved a blanket rule rewrites correct heads ("the LORD said" tags the verb).

## 4. Lessons (filed in memory; one line each)
- **A coverage claim is verified against the LOAD PATH** — "cached answers self-heal" ignored
  that reopened threads replay a browser-stored copy; cost one deploy cycle.
  (feedback_verify_before_claiming, part 9 + index tripwire.)
- **Close the arithmetic before any --apply** — dry-run 470 vs predicted ~350 didn't reconcile;
  the gap WAS the Midian false-positive class. (project_provenance_contract.)
- **df on shared NFS ≠ the account's quota** — 1.4 TB "free" vs JP's real 0.7 GB.
- **Measure before designing a rule** — one count query killed the "obvious" blanket head fix.

Memory authorities: `project_provenance_contract` (today's arc + ledger),
`project_entity_resolution_rebuild` (guard section), MEMORY.md hooks updated.
