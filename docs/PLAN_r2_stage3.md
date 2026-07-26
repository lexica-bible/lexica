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

## G1 — CLEAR (receipt G1-R2, reviewer, 2026-07-24)

Build 16b4eac1, deployed OFF (OFF-PROOF: IDENTICAL on both feeds), flipped ON by
JP. Four live checks clean: Agag G9826 tag matches the card (1); real inline
G-numbers untouched (2); lemma-only positively shown hidden — Havilah/Shur @
1Sa 15:7 (3); KJV/BSB tags Hebrew-keyed unchanged (4, HEB covered by the same
untouched path). H7017/H6002 @ 1Sa 15:6 classified against the live identity
table: all four rows bucket 'none' → H-number print is the spec'd fallback, not
a defect. Receipt of record: G1-R2, evidence = four-check screenshots + the
15:6 classification paste. Reviewer scope note attached to the receipt:
never-scoped rows (gentilics etc.) still speaking Hebrew is a COVERAGE
BOUNDARY, not an inconsistency; earning them Greek identities = a new backfill
class, adjacent to the parked R-1 gentilic ticket (pile U), future candidate,
NOT stage-3 scope.

## G2 sizing — candidate #1: Word study ABP branch flip (sized 2026-07-24, build on go)

Evidence base: docs/R2_stage3_evidence.md §2; all line cites re-verified against
current views_lexicon.py before sizing.

**What flips, precisely.** Word study becomes able to answer for a
STEP-extended Greek identity (G9xxx), so the card's identity/count lines can
LINK there instead of showing a static count (30-detail-panel.jsx:1106–1112
"Word study can't key those yet" — that block is the target). Today a G9xxx
profile 404s at views_lexicon.py:1094–1098 (main lexicon has no row) and the
ABP occurrence predicate (`_abp_strongs_filter` :291–310) structurally matches
zero rows (words never carries G9xxx pre-rebuild).

**The ABP occurrence set under the flip (the core definition):** for a Greek
number, ABP occurrences = rows words carries natively (today's predicate,
unchanged) PLUS `pn_greek_identity` rows with source='tipnr' for that number
(verse_id+position → the words row). No double count by construction: an
abp-tag identity row IS a native words row; a tipnr row is Hebrew-keyed in
words, so it can only arrive via the identity table. Gated on
READER_GREEK_FLIPS + table present; switch OFF = today's behavior exactly.

**Backend edits (views_lexicon.py only):**
1. Profile :1094–1098 — on main-lexicon miss for a G-number, gated fallback to
   `step_lexicon` (join on `base` as a NUMBER — the receipt-2 lesson), serving
   lemma/translit/gloss + a `step: true` field for the card's provenance tag.
2. `_abp_book_counts` :1151, `_abp_gloss_rows` :1173, the occurrence verse
   lists (`lexicon_verses` + `_all_books_verses`) — each gains the gated
   tipnr-identity union defined above.
3. The ABP-empty corpus fallback :1138–1144 — must consult the union before
   demoting a G9xxx to KJV/BSB (which can never carry it), else the reader
   lands on the wrong tab.
4. NO change to: Hebrew branch, KJV/BSB/HEB branches, the English finder, the
   lookup/translit search bands.

**Frontend edits:**
5. 30-detail-panel.jsx :1106–1112 — STEP identity gets a real "Word study"
   link (G9xxx, source "abp") replacing the static count.
6. 80-lexicon.jsx — word-card head shows the quiet "STEP" source tag beside a
   G9xxx number (same S2-Q2 style as the reader card); scoped to `.wd`, never
   the shared classes.

**Held OUT of G2 (reviewer to confirm with the go):**
- Lemma-only identities: Word study is number-keyed; keying by a stored Greek
  form is a new key type (new machinery, new URL shape). Card keeps the static
  count. Park as its own candidate.
- Real-G native counts: unchanged. The known count seam (card greek_count =
  identity rows; Word study native rows may include non-PN uses of the same
  number) is handled by the G2 count gate below, not by changing native logic.

**G2 gate (stage-2 pattern, no trial-then-apply):** locked test on a fixture
mirroring the real builders' table shapes (extends the G1 fixture) on BOTH CI
lists; deploy OFF → OFF-proof (a G9xxx profile still 404s; a normal profile
byte-identical) → receipt → flip is already ON site-wide (same switch), so the
deploy itself is the flip → live checks: (a) Terah/Βουγαίου-class G9xxx card
link opens Word study with lemma from STEP + STEP tag; (b) its ABP total
EQUALS the card's greek_count, any diff itemized to native non-PN rows;
(c) a normal Greek word's Word study unchanged; (d) Hebrew cross-ref link
still opens the Hebrew-keyed page → receipt → clear.

**Switch note:** the card link (5) must only render when the Word study side
can answer — both are behind READER_GREEK_FLIPS, deployed together in one
commit, so no window where the link 404s.

## STANDING RULE (JP, 2026-07-25) — visual changes need JP's explicit approval

All visual/style changes — colors, link treatments, typography, spacing — require
JP's explicit approval on the SPECIFIC change before build. The reviewer may
propose; nothing visual ships without JP's yes. Same shelf as "JP runs all PA
commands." (Origin: the reviewer ruled an ink-colored link treatment; JP's actual
ask was format alignment, and the color change shipped without his OK.)

**FINAL identity-line state (JP, 2026-07-25 — SETTLED, do not restyle):**
`9× G9826` / `9× H90` — no dot, no bold, no underline; whole line a plain blue
link with hover-underline, the panel's one link voice ("Read in context /
Interlinear"). STEP tag lives in the card HEADER with a hover explanation.
**Anti-design-creep rule:** this line went through five styling passes in one
night; the settled state wins over any future "improvement" unless JP asks.

## G2 — CLEAR (receipt G2-R1, reviewer, 2026-07-25)

Receipt basis: five-check bundle screenshots + JP live eyeball on the final card
state. Three JP flags fixed and verified inside the gate: occurrence-list
highlight (gold via g_id), arrow dropped, perf split resolved (G2 regression
fixed twice — index-friendly union 2eb2d710 + zero-tipnr peek 0c22ecba, flip
path 0.3s live; residual mega-word slowness pre-existing, ticketed in TODO.md).
Invariance deviation + substitute evidence on file below.

**CARD SETTLED STATE (JP visual rulings, final — reopen ONLY on JP's word):**
- Header: `G9826 (STEP)` — STEP tag beside the header number, hover explains
  ("Extended number from the STEP Bible project — beyond standard Strong's").
- Identity lines: `9× G9826` / `9× H90` — count first, no dot, no underline,
  no arrows, no destination labels; whole line a plain blue link, weight 500
  (the panel's one link voice, same as Read in context), hover-underline only.
  **AMENDED BY JP 2026-07-26 (unified count-line standard): the COUNT is bold**
  — matches every other occurrence-count line; rest of the ruling stands.
  Anti-design-creep rule still applies.

Standing rules confirmed in force (both in this doc): visual changes = JP
explicit approval (block above); deploys of serving code = dashboard Reload +
5× curl sweep (G2 deploy record below).

**NEXT (queue):** 1. Hebrew-flash trace (CC, ticketed-or-worse classification).
2. Candidate-3 sizing under the G3 ruling (Option B state, unfindability gate,
must-touch grep from code).

## CANDIDATE-3 CHARTER — Hebrew retirement rebuild (FROZEN 2026-07-25, reviewer-ruled)

The rebuild section of record. Sizing evidence: docs/R2_stage3_c3_sizing.md
(A–H must-touch list, enumerated from code — the edit-sizing basis; grep-before-
you-size satisfied there).

**Write set (per the sizing's row-class table):**
- abp-tag 3,518: unchanged — proven by the diff gate, not assumed.
- tipnr 10,731: strongs_base ← the served Greek number (real G or STEP G9xxx).
- lemma-only 14,850: strongs_base ← `'*'` (**C3-Q2 ruled**: the existing
  no-number convention; every click/tag/count gate already handles it; G3-B by
  construction).
- none 3,380: **KEEP Hebrew (C3-Q1 ruled, documented exception)** with two bound
  conditions: (a) the exception is MACHINE-VISIBLE — a scope marker consumers can
  query directly ("which rows are the retained-Hebrew exception"), via a
  source/class column on the Q2 home or the identity table's bucket; (b) the
  named end state is the **gentilic/people-class Greek backfill candidate**
  (adjacent to parked pile U) — that candidate retires this exception when it
  lands. **Expectation correction (reviewer's own record):** the post-G1 note
  that the rebuild would stop the Hebrew fallback for these words was WRONG —
  they keep printing Hebrew until the backfill candidate lands; that is the
  stated user-visible expectation.
- ALL classes: the Hebrew number moves to the Q2 cross-ref home (NEW TABLE = JP
  checkpoint before it lands).

**C3-Q3 (ruled): SEO follows serving truth, no special casing.** G9xxx pages
join the /word list (STEP-fallback lemma resolution); H-number pages persist
(the Hebrew corpus is untouched, H-numbers stay legitimate identities there);
no removals, no redirects; any H-page content previously fed by a now-cleared
ABP row draws from the Q2 home like every consumer.

**Run shape (ruled): code first, dormant.** ALL serving-code repoints (sizing
classes A–F + the STEP-fallback class below) ship BEFORE the swap, gated on the
Q2 table's existence (the G1 table-existence guard pattern). No gap where
Hebrew-keyed pages serve zeros; the swap activates already-deployed code.

**STEP-fallback generalization (its own must-touch class, ruled in scope):**
every lemma-displaying feed gets the card's step_lexicon COALESCE (the sizing's
new-fact finding — post-retirement strongs_base carries G9xxx the main lexicon
join can't see). Rides the code-first wave.

**Gates and constraints (all standing):**
- Changed builder → trial-then-apply BINDS (rewrite site AMENDED 2026-07-25 by
  reviewer ruling, docs/PLAN_r2_c3_rebuild.md deviation block: the rewrite
  lives in the dedicated `scripts/retire_hebrew_identity.py`, NOT
  import_tipnr.py:719 — import_tipnr untouched and not run; roster gate fires
  unconditionally on trial AND apply; the script consumes the stage-1 identity
  table's classification as the one write set of record, any disagreement
  halts. build_pn_greek_identity snapshot re-sourced from the Q2 home;
  binder AMENDED 2026-07-25 by reviewer ruling (docs/PLAN_r2_c3_rebuild.md
  drift block): the charter's "bases extended to Greek keys or fuzzy binds
  floor" alternatives are BOTH set aside for a ruled third path —
  build_entity_binding sources each word's guard number from the Q2 home
  (frozen Hebrew, byte-for-byte the pre-retirement guard value; NULL-hebrew
  tipnr rows reconstruct their old '*'), pass bar = line-for-line identity
  with the pre-copy dry-run incl. both hand-check text files. The Greek-key
  bases extension is PARKED BY RULING as its own future candidate (capability
  change — would fire novel binds mid-rebuild), adjacent to the gentilic
  backfill; recorded, not dropped.)
- JP TABLE CHECKPOINT CLEARED 2026-07-25: DDL approved on plain-English intent
  (technical shape reviewer-vetted) — cite in the rebuild receipt.
- Roster-freeze gate: check_roster_regression.py CLEAN before import.
- Copy-first into a test db; own backup; the pre-rebuild known-good file kept.
- **Unfindability gate (G3 condition 1, mandatory):** the 14,850 enumerated
  before (Hebrew-keyed) and after (Q2 home + lemma); zero
  findable-before/unfindable-after. S2-Q4 bar.
- compare_words itemized to zero unexplained; strongs_base GLOB invariant
  (G9xxx passes — verified in sizing); health_check; cert_invariants;
  two-derivations re-run.
- G5 rides after: both flips (G1 reader tags, G2 Word study) re-receipted
  against the rewritten tables + the switch-semantics change recorded
  (READER_GREEK_FLIPS OFF no longer means Hebrew-everywhere — expected, not a
  defect).

## CANDIDATE-3 CODE-FIRST WAVE — BUILT (2026-07-25), dormant, pre-deploy

**Q2 table shape RULED (reviewer, 2026-07-25, this session):** per-word table
`pn_hebrew_xref(verse_id, position, hebrew_base, class)` — hebrew_base NULL
(declared, never '') for always-Greek abp-tag rows; `class` ∈ abp-tag | tipnr |
lemma-only | none, with 'none' doubling as the machine-visible kept-Hebrew
exception marker (C3-Q1 condition a); the gentilic/people-class Greek backfill
candidate is the named consumer that retires those rows (condition b) — both
recorded in the reference DDL comment (tests/test_c3_dormant.py `_retire`,
which the rebuild lane must land byte-for-shape). Greek number deliberately NOT
copied in (one fact, one home). Reviewer reversed the older Greek-keyed
side-table recommendation on the record, reason: consumer access is per-word or
per-H-number, both served directly. **OUTSTANDING GATE: NEW TABLE = JP
checkpoint — the table lands in NO database (test copies of the rebuild run
included) until JP's checkpoint clears; the rebuild receipt must cite it.**

**What shipped (all gated on `core.pn_xref_ready` — table absent = today's
exact SQL, proven byte-level in the locked test):**
- core.py: `pn_xref_ready` + `step_lemma_cols` (STEP G9xxx lemma/translit/gloss
  COALESCE, MIN(estrong) pick, join can't duplicate rows) + `h_abp_predicate`
  (H-keyed ABP reads union the xref home; rowid-IN + peek, the G2 perf shape)
  + `pn_xref_parts` (tipnr type-badge join through the xref home).
- views_library.py (A): both feeds get step COALESCE + xref'd tipnr key.
- views_lexicon.py (B): `_abp_strongs_filter` H-union (serves every profile/
  count/gloss/verse-list/corpus-fallback path — all 8 call sites); the old
  G-side pn_greek_identity union retires when xref exists (repoint per the
  G4-MUST-TOUCH marker, no double count); `_step_lexicon_row` answers
  post-retirement regardless of READER_GREEK_FLIPS (G5 semantics); English
  finder band gets the step COALESCE (G9xxx bases enter via LIKE 'G%').
- views_metav.py (C): /api/strongs-count?by=base + the card's hebrew_count
  repointed via h_abp_predicate (kills the §6 silent zero).
- views_seo.py (D): chapter feed step COALESCE; /word/G9xxx serves from
  step_lexicon (C3-Q3, not switch-gated — serving truth). H pages confirmed to
  read heb.db/KJV, not ABP words — no repoint needed (checked, not assumed).
- ai.py (E): cited-verse fetch step COALESCE; `_AI_PN_RETIREMENT_ADDENDUM`
  appended to the built prompt ONLY when xref exists, with matching `pnx=1`
  cache-fingerprint tag — today's prompt AND fingerprint byte-identical; the
  search cache refreshes once, exactly at the swap.
- core.py word_gloss_cols (F): no-op with reason — a retired row's Hebrew gloss
  key correctly stops resolving (identity is Greek now); step gloss arrives via
  the feed COALESCE.
- Frontend (G): zero edits — behavior flips by data; G5 re-receipt covers.
- Locked test tests/test_c3_dormant.py (25 checks: phase-1 dormancy byte-level,
  phase-2 simulated retirement fires every repoint; 'none' rows reachable both
  ways count once) — added to BOTH CI lists.

**W1-C3 RECEIPT ISSUED (reviewer, 2026-07-25): code-first dormant wave, commit
4dac41c7, CLEAR.** Evidence: chapter-feed diff IDENTICAL + 5× sweep on the
ruled dashboard Reload (first pass rode deploy.sh's `touch` — deviation caught
pre-receipt, cured by re-running on the standard, recorded not waived;
deploy.sh:63 fix queued as its own task); second surface H90 count = the
receipted 9; /word/G9826 dark at 404 (STEP path table-gated inert); locked
test 25/25 on both CI lists; class-D H-page sizing item STRUCK as
wrong-at-sizing with code cites (views_seo.py :537/:568/:602 under the
:515/:550/:581 Greek-branch guards); completeness claim on record (complete
A–G + STEP-fallback; only at-swap change = AI prompt + cache tag, by design).
**Rebuild lane OPEN under G4** — run plan: docs/PLAN_r2_c3_rebuild.md
(declared expectations + the one deviation for ruling: rewrite site as a new
dedicated builder, import_tipnr untouched). JP's table checkpoint still open,
clears at his word on the DDL in that plan; rebuild receipt cites it.

## G2 deploy record (2026-07-24) — deviation + lesson, reviewer-ruled

**Invariance-proof DEVIATION (accepted, recorded, not waived):** the deploy
landed onto an app with the switch already ON, a stale-worker mix served
errors mid-deploy, and no before/after capture of an existing surface was
taken — the original proof form is gone. Substitute evidence accepted by the
reviewer: (a) the locked test's OFF-invariance assertions
(tests/test_ws_greek_flips.py, both CI lists); (b) live checks θεός-unchanged +
H90 cross-ref resolves; (c) ADDED: a normal numbered-name Word study page
(G1138 David class) verified unchanged — nearest neighbor to the changed path.

**STALE-WORKER LESSON (standing, deploy notes):** the `touch`-reload left a
half-refreshed worker mix live — old code answering 404, then a mixed state
answering 500, while a fresh console process ran the same code+data clean.
Ruling: for ANY deploy that changes serving code, (1) the PythonAnywhere
dashboard Reload button is the STANDARD reload, not `touch`; (2) the 5×
repeated-curl worker sweep on a changed endpoint is part of DEPLOY
VERIFICATION, not incident response. (This is G2's lesson the way the fixture
lesson was stage 2's.)

**Chapter-feed g_id classification (pre-receipt question, answered):** the
"1" from the live probe was `grep -c` counting LINES — the whole chapter JSON
is one line. Counted properly, 1Sa 15 carries **83** g_id marks: 51 numbered
(tipnr; G9826 ×8, matching Word study's 1Sa count exactly) + 32 lemma-only
(empty number, tag hidden). No G1 regression.

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
