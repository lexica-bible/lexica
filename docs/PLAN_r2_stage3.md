# PLAN — R-2 stage 3 charter (reviewer-ruled 2026-07-24)

Charter recorded verbatim from the reviewer's ruling (receipt basis: evidence pass
docs/R2_stage3_evidence.md, accepted at 76f4abb). Delegation note: ruled by
reviewer under the pre-stated intersection rule; applied as delegated, no
decisions routed to JP.

## The ruling (pasted reviewer text — the record)

> Evidence accepted — verified against current source, read-only, receipt 76f4abb
> noted. Applying the pre-stated ruling logic.
>
> **Dependency ruling** — Intersection is non-empty. The rebuild rewrites
> `words.strongs_base` and the side tables; candidate 1 counts by `strongs_base`
> (or reads stage-1 side tables pre-rebuild), and candidate 2's fallback prints
> `strongs_base`. The prior from last session — "rebuild trails because 1–2 read
> tables it doesn't rewrite" — is refuted on its stated reason but upheld on
> sequence: rebuild still goes last, now because 1–2 are flag-only only if built
> pre-rebuild (per §4), and because the rebuild rewrites their read paths, which
> mandates a re-receipt gate on both flips after it lands. Delegation note: ruled
> by reviewer under the pre-stated intersection rule; the non-empty branch selects
> "flips land before rebuild, re-receipt after."
>
> **Sequence ruling** — 2 → 1 → 3.
> * #2 first. Only user-visible seam (Agag viewport), smallest surface (5 tag
>   sites, one frontend file), flag-only.
> * #1 second. Flag-only pre-rebuild; accepts the side-table read as the cost of
>   landing before the rebuild. That read gets repointed to `strongs_base` inside
>   candidate 3's scope (it becomes a serving-site touch of the rebuild, same
>   class as the cross-ref count repoint).
> * #3 last. Changed builder: trial-then-apply binds, roster gate fires, own
>   rollback point per the stage-1 precedent, backup retention rule rides.
>
> **Rollback grouping** — Two switches, not one. Stage-2 cards stay on
> `READER_GREEK_IDENTITY`. Both flips share one new switch (working name
> `READER_GREEK_FLIPS`) — grouped rollback for #1+#2, independent of the live card
> flip. Rationale accepted from §5: sharing the existing switch would make
> rollback of a new flip also roll back shipped, receipted work. The rebuild sits
> behind no switch; its rollback is the backup restore.
>
> **Gates**
> 1. G1 — #2 build+flip: OFF-proof, receipt, clear. Flag-only, no
>    trial-then-apply.
> 2. G2 — #1 build+flip: same class, same gate shape. Side-table read verified
>    against stage-1 receipts.
> 3. G3 — rebuild pre-charter gate (blocking): the 14,850 lemma-only number-cell
>    question must be ruled before candidate 3 is sized. This is a design gap,
>    not a build task — CC drafts the options (leave null / carry lemma key /
>    STEP-extend), reviewer rules, ruling recorded in the rebuild charter.
> 4. G4 — rebuild run: trial-then-apply, roster gate, must-touch list includes
>    (a) card Hebrew cross-ref count repoint (the silent-zero collision from §6),
>    (b) #1's side-table read repoint. Own backup, keep the pre-rebuild
>    known-good.
> 5. G5 — post-rebuild re-receipt: both flips re-receipted against rewritten
>    tables. Also record the switch-semantics change: post-rebuild,
>    `READER_GREEK_FLIPS` OFF no longer means Hebrew-everywhere — documented in
>    the handoff as expected behavior, not a defect.
>
> **Charter emission** — That's the full stage-3 charter: sequence 2→1→3, five
> gates, two-switch rollback grouping, G3 blocking candidate-3 sizing. CC's next
> actions in order: (1) scope #2's 5-site change against the new switch, (2)
> draft the G3 options memo. Send when CC confirms the charter is recorded in
> the plan doc.

## Candidate #2 scope — the 5-site tag flip against READER_GREEK_FLIPS (sized, not built)

Evidence base: docs/R2_stage3_evidence.md §3. Grep-before-you-size done there:
5 ABP tag sites, all in `static/src/59c-library-render.jsx`; Heb/KJV/BSB tag
sites are Q4-out-of-scope and untouched.

**Backend (2 blocks + 1 switch line):**
- `core.py` — add `READER_GREEK_FLIPS` beside `READER_GREEK_IDENTITY` (:39),
  same env pattern, default OFF. ON = one line in the WSGI file; rollback =
  delete the line + reload.
- `views_library.py` verse feed (:61–74) and chapter feed (:229–239): when the
  switch is ON **and** `pn_greek_identity` exists, LEFT-join it on
  `verse_id + position` and add one field per word, e.g.
  `"g_id": {"strongs": greek_strongs or null, "src": source}` — only for rows
  with a served identity (source != 'none'). With the switch OFF: no join, no
  field, payload byte-identical (the G1 OFF-proof surface). Deploy-safe: table
  missing → behave as OFF.

**Frontend (1 helper + 5 call sites, one file):**
- One shared tag helper in `59c-library-render.jsx` (kills the 4-copy
  duplication the evidence pass counted) used at :208/:226/:267/:291 and the
  ABP-interlinear site :787–789:
  - word carries a real inline G-number (`strongs` != '*') → unchanged
    ('G'+strongs), the flip never re-derives what the text carries (C2a
    precedent).
  - backfilled PN with a served NUMBERED identity → print `g_id.strongs`
    (G1138 / G9xxx). Bare refmark text, no STEP tag in the tag line — the
    provenance tag lives on the card (S2-Q2); tags are number-only by design.
  - lemma-only identity (no number in any scheme) → tag HIDDEN (the same
    hidden-placeholder span the sites already use) — no fabricated number (Q3).
  - no identity served / 'none' bucket / switch OFF → today's fallback
    (`strongs_base`) unchanged.
- `npm run build`; commit source + app.js together.

**Tests / gates (G1):**
- Locked test: feed payload with switch OFF is byte-identical (fixture mirrors
  the real builders' table shapes — the receipt-2 lesson); switch ON serves the
  identity field for a known backfilled PN (Agag-class fixture) and hides the
  number for a lemma-only row. Added to BOTH CI lists.
- Deploy OFF → OFF-proof (chapter feed diffed before/after, identical) →
  receipt → flip ON → live checks (Agag @ 1Sa 15 tag shows the card's G9826;
  a real-G NT name unchanged; a lemma-only PN tag hidden; KJV/BSB/Heb tags
  unchanged) → receipt → clear.

**Known consequences to declare at receipt time (not defects):**
- Chip/prose/interlinear tags for backfilled PNs stop matching the Hebrew
  number KJV/BSB tags show for the same name — expected: each text keys its
  own scheme (the provenance rule stage 2 already applied to counts).
- Feed payload grows slightly when ON (one small field on PN words only).

## Next after G1: candidate #1 (G2)

Not sized yet — sized after G1 clears, against the same switch. Read surface and
the pre-rebuild side-table dependency are already recorded in
docs/R2_stage3_evidence.md §2.

## G3 — RULED (reviewer, 2026-07-24): Option B. G3 CLEAR.

Memo: docs/R2_stage3_G3_memo.md. Ruling (pasted reviewer text):

> G3 ruling: Option B. Delegation note: ruled by reviewer on CC's
> recommendation, applied as delegated.
> Reasons of record:
> * Only option consistent with the ruled Q3 card state — a missing identity is
>   data; the column means one thing everywhere after the retirement, which is
>   the retirement's purpose.
> * A is refused because it permanently re-opens the Agag-class seam for this
>   bucket and makes every future consumer carry the exception.
> * C is dispositioned as unavailable, not merely rejected: lemma-only is
>   defined post-STEP-check, so minting numbers is a provenance-contract
>   violation. Record it as closed, no revisit.
> Conditions bound into the rebuild charter with the ruling:
> 1. Unfindability gate (mandatory): the count gate CC proposed — 14,850 rows
>    enumerated before (Hebrew-keyed) and after (Q2 home + lemma), zero
>    findable-before/unfindable-after. S2-Q4 bar applies.
> 2. Must-touch enlargement recorded, not appended: all H-number-keyed reads
>    over these rows repoint to the Q2 home — same G4 item as the cross-ref
>    count, enlarged in scope, not a new class. CC greps for H-number-keyed
>    serving sites at rebuild-sizing time so the must-touch list is enumerated
>    from code, not assumed complete.
> 3. No #2 rework: the tag helper's lemma-only branch already renders the B
>    state correctly — note in the charter that G1's live checks double as a
>    preview of post-rebuild B behavior for this bucket.

Candidate-3 sizing UNBLOCKED but waits its sequence turn (after G1, G2).
Option C is CLOSED — no revisit.
