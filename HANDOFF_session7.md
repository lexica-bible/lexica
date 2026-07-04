# ABP Corpus Certification — Session 7 handoff

**Model seat:** low/medium is correct for this session's shape (source readings + maybe the
twin-bug rebuild) — everything is pre-registered, surprises resolve by enumeration. Bump only on
the stop-conditions below.

## Frame (unchanged, governs all audit sessions)
Two-tier standard. **Tier A** = ingest-faithfulness. **Tier B** = source defects as a versioned
overlay (`abp_corrections`). Certification has been COMPLETE since Session 3; every session since
extends the perimeter, never re-opens it.

## Standing rules (inherited + one promoted this session)
- **Checkpoint rule:** new data structures, schema fields, correction-table writes, manifest
  additions, binder-logic changes → JP's explicit go before landing.
- **CC cannot query bible.db.** JP runs every query on PA and pastes results.
- **Control-test rule:** every detector fires on a known positive before its zero is trusted;
  reuse the production detector, never a second copy; controls are durable (permanent seeded fixture).
- **New-finding rule:** a defect claim lands with its evidence pasted at first mention.
- **Verify-before-sizing:** a ledger entry is a pointer, not a spec — inspect the real cells before
  sizing any correction.
- **[PROMOTED Session 6] Query-preservation:** *any count or claim that lands in a ledger, audit
  doc, or handoff carries its defining query verbatim.* Earned by four unsaved ad-hoc probes → four
  wrong claims this arc (37/39 prose · ×4/14 Greek · L5's regen-found-0 · L5's "never committed").
- **Loud-fails are the guard working, NOT bugs to patch around:** (a) `parse_tipnr` now RAISES on an
  unrecognized entity type under a `PERSON+PLACE` header — a future TIPNR re-ingest can stop the build
  by design; extend the type map, don't suppress the raise. (b) check 7's mirror leg is live.
- Accepted limits, do not re-open: `HEAD_WORD_TAIL_CAVEAT`, `SPLIT_FUNCWORD_SLOT_CAVEAT`.

## Closed + certified — DO NOT re-open
L9 · the flip class · em-dash class · Cushi corpus rows · Jer 49:13 · Hab 3:6 · the Session-3 swap ·
Session-4 Cushi binding fix · Session-5 TIPNR pin · L2 · L10 · **[Session 6] the 97-card
section-label defect · the mirror census (P1=0, valid) · L5 (two errors explained, no drift) ·
check-7 both-directions.**

## State entering Session 7
- `cert_invariants.py` **7/7 green** live, correction pin 16, manifest 75 files.
- Entity binding rebuilt + live: parsed 4,247, `tipnr_entities` 2,186, `pn_binding` render 14,803 +
  HOT 72. Parser fix in `entity_resolution.parse_tipnr` (F1 row-type over header, F2 skip EXCLUDED,
  F3 skip prose, loud-fail raise). Durable control in `tests/test_versification.py`.
- Standing source witness: the official ABP app (apostolicbibleapp.com).

## Carry-forward (each already doored)
1. **L5 — 9 source readings (async, JP).** Re-derived authoritative list (query saved verbatim in
   `AUDIT_abp_certification.md` L5 entry). The 9 CANDIDATES: 2Ki 18:9 p9 · 2Ki 18:10 p12 · 2Ki 25:8 p9
   (G846 "this is") · 1Ch 27:6 p0 · Ezr 7:6 p0 (G846 "This") · Dan 4:33 p1 · Eze 36:32 p4
   (G1473) · 1Co 1:24 p1 (G846 "to these") · Mat 3:15 p9 (G3779 "for to this"). Each: read vs the
   ABP app — αὐτός/ἐγώ can legitimately render "this/same"; real mistags → correction rows via the
   L2/L10 door (dry-run → JP go → guarded apply → check 4 green).
2. **Luke 23:38 Tier B candidate.** The word "Hebrew" now renders the Hebrews-PEOPLE card (was a
   floor) — a source-reading question (does TIPNR rightly file a language verse under the people).
   Rides the ABP-app pass; gates nothing. Full note in `AUDIT_entity_seam.md`.
3. **`import_tipnr.py` twin bug.** Its own separate parser has the same header-first defect (line 97),
   so the `tipnr` table also types the 10 mixed places as person. MASKED for all 97 bound cards (a
   bind gates the metaV path off), so no urgency. Fix = same 3 classes in that parser; needs a words
   rebuild / `import_tipnr` re-run = its own checkpoint.
4. **The 7 uncertified build-reorder passes.** L9 certified `_split_compounds` only. Still open:
   `_split_numbered`, `_redistribute_pronoun_compounds`, `_fix_backwards_pairing`,
   `_split_pn_article_lump`, `_funcword_noun_relocate`, `_lord_subject_split`, `_lord_oath_fix`.
   Same census+control approach. JP's timing call.

## Out of scope
Re-opening anything certified in Sessions 1–6; schema changes to `abp_corrections`; new binder
guards beyond evidence-justified proposals.

## Output discipline
Every gate/rebuild presented with its pre-registered expectation BEFORE JP runs it; parser/correction
changes as checkpointed proposals with dry-runs pasted; enumerate deltas, never count; close with a
perimeter statement.
