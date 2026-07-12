# V9 DESIGN — the two candidate lines (coverage/trimming + verbatim-quote)

Drafted at the V9 design pass (2026-07-12, post batch-5 s1 close, commit caa2ca8).
**Status: DRAFT — nothing here touches the live prompt. V8 stays frozen (stamp
`lexica:7ef8620328a9`) until JP promotes V9. Hard gate this session: NO word runs —
no floors, no draws, no applies, no re-entries (charter amendment 6).**

Everything below is for JP ruling. The RULINGS block at the bottom is empty until he rules.

---

## LINE (a) — CITATION COVERAGE (the trimming attractor)

### Evidence (all banked; pointers, not re-argument)
- Cross-word attractor record: six draws, two hinted re-entry words, EVERY rejection
  coverage alone — G227 37/34/38 of 39, G2805 34/30/31 of 39, six distinct absentee
  sets, zero convergence. Hints cured every original park defect each time. Record:
  G2805 RE-PARKED entry (audit doc) + V9_PILE close entry.
- Correlation table (reviewer-ordered, existing data): NO length trade — G227's longest
  card cited worst (7,015 chars → 34/39), G2805's longest cited best (4,181 → 34/39).
  Opposite signs kill the "card ran out of room" hypothesis. Reading: exemplar-sampling
  habit — the model treats the occurrence list as a pool to illustrate from, not a
  roster to account for.
- JP clarification already on the record (G2805 pre-clears): "citation-trimming is
  floor-legal only, NEVER ship license — a ship cites every fed occurrence." The line
  moves that ruling INTO the drafter's instructions.

### Drafted prompt line (discipline-shaped, no structural redesign)
> **COVERAGE IS TOTAL.** Every occurrence in the list above must appear as a citation
> under one of your senses. Do not choose representative examples — an occurrence you
> leave uncited is a defect, exactly like a fabricated one, even when the sense analysis
> is otherwise right. Before you finish, re-scan the occurrence list top to bottom and
> confirm every reference appears in your senses.

Shape notes (per the no-regress rule, memory `project_ai_synthesis_quality`):
- Reframes (roster to account for), doesn't blacklist ("never trim" alone would name the
  failure without giving the behavior). The final self-check sentence gives the model a
  concrete closing action instead of a prohibition.
- One block, injected with the other standing instruction blocks; exact placement decided
  at the build session (after JP promotes), shown to JP before landing, like every prompt
  change.

### Where it does NOT reach (stated so nobody over-claims later)
- It cannot make coverage *verified* — that is the gate's job (below). History says a
  prompt line reduces a failure mode without eliminating it (the hint-limits exhibit is
  exactly that shape, same session).

---

## LINE (b) — VERBATIM QUOTES

### Evidence (three words + the hint-limits exhibit)
- G2805: refrain misquoted three park draws running, three different corruptions; then
  at re-entry d2 WITH the verbatim hint live, the hybrid splice ("there shall be the
  weeping…" — the shall-verses' verb on the of-teeth ending, matching NO member) — the
  family's 4th corruption and THE HINT-LIMITS EXHIBIT: a per-word hint reduces
  (d1 clean, d2 one-of-two, d3 clean) but does not eliminate. V9_PILE hint-limits entry.
- G236: draws misquoted stored text (V9_PILE 2026-07-12 G236 lines).
- G162 d2: Eph 4:8 quote dropped "into the height" mid-quote with no ellipsis — banked
  in the G162 PARKED audit entry (d2 bullet) + the V9_PILE batch-wide "THIRD word" line.
- Member-list addendum evidence: the seven refrain verses differ by articles; d1's
  "structurally identical across all six" was true of structure, not wording (ledger:
  a quote against a member list names its member). G2805 RE-PARKED entry.

### Drafted prompt line
> **QUOTES ARE VERBATIM.** Any wording you place inside quotation marks and attribute
> to a verse must match that verse's stored text word for word; mark any omission with
> an ellipsis (…). When several verses share a refrain or formula, quote ONE verse and
> name it — never write a blended wording, and never claim the members are worded
> identically unless they are.

Shape notes: same discipline shape as line (a) — a positive procedure (quote one, name
it) replacing the failure (splice/blend), not a bare prohibition. This GENERALIZES the
per-word G2805 verbatim hint; the hint stays in the register regardless (hints and
prompt lines are different layers — the register entry is per-word evidence-specific).

---

## THE ENFORCEMENT QUESTION (answered, per the opener's requirement)

**Question:** prompt line alone, or prompt line + a coverage gate in `validate_entry`
(fed-occurrences-cited check)?

**Recommendation: BOTH — line (a) plus the gate.** Grounds:
1. **Audit-tools-must-fail** (standing rule): a line without a detector can't be proven
   working; the streak would be the only evidence, and streaks aren't proof.
2. **The session's own data:** hints (a prompt-adjacent mechanism) went 6-for-6 on their
   registered content and STILL couldn't stop an adjacent failure. Expect the coverage
   line to move the rate, not zero it. The gate catches the residue.
3. **Trimming is uniquely machine-checkable** — unlike carve-invention or misattribution,
   both sides of the comparison already exist at build time: the fed sample (`ctx`, in
   scope in `build_lexica_def.py` at validate time) and the card's citations (the #28
   `ref_spans` scanner over the senses block, ranges + tails now expanded). No model
   call, no new data.
4. Precedent: the citation gate went report-only → blocking (2026-07-01) because a
   silent defect wrote exactly like a clean row. Trimming is the same silence today —
   34/39 ships would have LOOKED clean without the hand count.

### Gate spec (design only — build happens after JP promotes, with code shown first)
- **Hook:** `validate_entry` gains a coverage check; the build passes it the fed refs
  (from `ctx`). Floor/dry-run output prints the same count so a gap is visible before
  a ship attempt.
- **What counts as covered:** the fed ref appears as a citation in the SENSES block
  (scanned by the production `ref_spans` — never a copy), matched exact-or-dotted, BOTH
  clauses. Range-interior and tail refs count (that's what #28 bought). Named-dual =
  cited, once, per the convention.
- **What does NOT count:** a prose mention, a Range/gloss-note appearance, or an
  "cannot be assigned securely" sentence (the Isa 42:3 ruling: not a disposal).
- **Doubles:** coverage is ref-level — a verse fed twice (Amo 5:5 ×2 class) is covered
  by one citation of that verse.
- **Failure = blocks the write** like the citation gate, listing the absentee refs by
  name (counts are names). Bypass rides the existing `--force-gate-bypass "reason"`
  path — reason stamped, self-documenting; no new bypass surface.
- **Control test (must-fail):** a fixture from a banked trimmed draw — e.g. G2805 d1's
  cached raw with Jdg 21:2 absent — must FIRE the gate before any zero is trusted; plus
  a clean-card control that passes. Both tests go in BOTH CI lists.

### Enforcement for line (b) — separate, smaller answer
A verbatim-quote checker is mechanizable (the citation gate already holds verse text at
gate time: extract quoted spans near a ref, compare to `verses.text` allowing ellipses).
**Recommendation: do NOT bundle it into this pass.** It's a harder parse (which quote
belongs to which ref; member lists), and the evidence base is 3 words vs the coverage
attractor's every-draw signature. Bank it as its own ticket (V9_PILE already carries the
"mechanizable check" note); line (b) ships as prompt-line-only with the armed hand-read
+ the existing per-word hint as the interim detectors. JP rules.

---

## CORRELATION TABLE — batch-4 ship rows (offered, optional)
The table (in the s1 session record) can take the seven shipped batch-4 cards as
control rows: per card, def_json length vs fed-occurrences-cited count. The counter
doesn't exist yet as a standalone read (`check_draw_citations.py` is a collision check,
not coverage) — if JP wants the rows, CC writes a small READ-ONLY PA script (fed refs
from the draw record, citations via `ref_spans`) and JP runs it. Value: if shipped
(accepted) cards also show trimming pressure that adjudication caught, the attractor's
rate on PASSING work gets sized too. Not required for the ruling above.

---

## WHAT JP IS BEING ASKED TO RULE
1. Line (a) wording — adopt / amend.
2. Line (b) wording — adopt / amend.
3. Enforcement: prompt line + coverage gate (recommended) vs line alone.
4. Gate details if adopted: senses-block-only coverage · ref-level doubles · existing
   bypass path · must-fail fixture from G2805 d1 — adopt as specced / amend.
5. Verbatim-quote checker: separate ticket (recommended) vs bundle now.
6. Batch-4 correlation rows: want them (CC builds the read, JP runs) or skip.

## RULINGS (JP, 2026-07-12 — relayed via the reviewer chat; all six adopted on the
## CC+reviewer recommendations)
1. Line (a) wording — **ADOPTED as drafted.**
2. Line (b) wording — **ADOPTED as drafted.**
3. Enforcement — **line + coverage gate in `validate_entry`.**
4. Gate details — **adopted as specced:** senses-block-only coverage via the production
   `ref_spans`, exact-or-dotted both clauses, tails count, ref-level doubles, existing
   `--force-gate-bypass` path only, must-fail fixture from G2805 d1 (Jdg 21:2 absent)
   + clean-card control, both tests in BOTH CI lists.
5. Verbatim-quote checker — **separate ticket;** line (b) ships prompt-only with the
   hand-read + per-word hint as interim detectors.
6. Batch-4 correlation rows — **adopted:** CC builds the read-only PA script, JP runs
   it; gated on the PA-currency check first (JP reposts PA's raw `git log --oneline -1`
   before the script is handed over).

**Boundaries banked with the ruling (so nobody over-reads it):** ruling ≠ promotion —
V8 stays frozen (`lexica:7ef8620328a9`), the lines land only when JP promotes V9,
placement shown first · amendment 6 holds — no floors/draws/applies/re-entries; the
gate build is in scope per this doc's own terms and is not a word run · show code
before changing it — validate_entry diff + both CI fixtures posted for review before
commit · zero isn't trusted until the must-fail fixture fires.
