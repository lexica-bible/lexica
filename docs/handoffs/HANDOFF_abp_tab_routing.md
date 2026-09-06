# HANDOFF — ABP-tab routing (the header arc's original goal, now unblocked)

Banked 2026-09-06 at arc close. The Greek header arc is CLOSED (landed live, served,
JP-signed; full record `HANDOFF_gateB_enumeration.md`, memory `project_greek_header_fold`).
Routing was ALWAYS the goal — the folding existed so this lane wouldn't lie.
**JP raises this lane on his timeline; do not start it unprompted.**

## The problem (why the tab is grey)
Word study's ABP tab greys on names like Galilee. It is honest about the NUMBER and
wrong about the TEXT: ABP prints Galilee 73 times, all starred with no dictionary
lemma, so `has_abp` (views_lexicon.py) finds nothing under G1056 and the tab dies.
[READ 8/9, re-verify at charter time.]

## What changed under it
`pn_greek_identity` is now the folded header layer, LIVE since 9/6: one disciplined
Greek header per resolvable name (galilee → Γαλιλαία covers all 73 rows; zion → Σιών;
hadad per-verse forms). The by-form door (`_pn_lemma_rows`) matches ONE stored form
exactly — routing through it pre-fold would have shown 13 of 73 as if that were the
total. THAT is the trap this lane exists to avoid. [Door behavior READ 8/9 —
re-verify the function before designing on it.]

## Pre-registrations for the charter (write these before code)
1. **The count shown must equal the fold**: Galilee's ABP tab shows 73, sourced from
   pn_greek_identity rows under the header — never from matching one form. Gate pin:
   galilee = 73 exactly (the arc's banked number, machine-verified 9/6).
2. **Unresolved names (875 of them, receipt class UNRESOLVED) stay honest**: they have
   no single header, so the tab must show whatever partial truth it can LABELED as
   such, or stay grey — never a one-form count presented as a total. The 875 list =
   `docs/tickets/greek_header_split.txt` on PA (regenerated every build run).
3. **KJV-vs-ABP counts differ by design** (galilee: KJV 63 via kjv_strongs G1056,
   ABP 73 rows — receipted 9/6). The UI must never present one as the other.
4. **Served check set is pre-named**: galilee (73), zion, hadad (1Ki 11 — 12 rows,
   per-verse forms, the hard case), one UNRESOLVED name (e.g. abishai — 3 forms).
5. Presentation is JP's call per the visual-approval rule; propose, don't ship.

## Housekeeping FIRST, next session (before or independent of routing)
- **Check the nightly landed** (first bible.db backup stamped after 9/6 15:56):
  `ls -l ~/db_backups/ | grep -a 'bible\.db\.'` — then, per the single-rollback rule,
  the scratch copies are deletable:
  `rm ~/bible-db/bible_hdrlane.db ~/bible-db/bible_formlane.db` (JP runs; they ride
  every nightly at ~860MB/day until deleted). Also deletable then: their backup
  copies in ~/db_backups if any remain.
- **TRIPWIRE (new, 9/6): bible.db retention is 3 copies — a MANUAL backup_db.py run
  IS a deletion of the oldest copy.** Check nothing in the window is load-bearing
  first. This ate the last old-form-table copy on 9/6 (871 retired unreproducible).
- Filed follow-ups live in TODO.md: the 20 glued-blanked rows (hand-table door
  candidates) · "midianitish" gap in `er.is_people_group` (gentilic follow-up — fix
  changes builder output, own charter) · 875 multi-form names (long-tail hand-table
  class, template = batch-2/3 records) · health_check abp_surface floor re-declare
  389,244 → 391,130 · audit_surface_coverage stored-vs-live control (permanent false
  alarm on backfilled tables).

## Standing law for this lane
`feedback_verdict_gate` · `feedback_audit_tools_must_fail` (routing display = a NEW
render mode: its oracle must model THIS mode, and every detector fires on a known
positive first) · `feedback_visual_changes_jp_approval` · CLAUDE.md routing table
(word-study.md is the routed doc for views_lexicon.py work — read it first).
