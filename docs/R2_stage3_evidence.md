# R-2 stage 3 — pre-scoping evidence pass (read-only; goes to the reviewer)

Written 2026-07-24 per docs/handoffs/HANDOFF_r2_greek_names.md "Stage 3 — opening context" work
item 5. Every code claim below was read at the cited file/line TODAY (not carried
from the stage-2 consumer doc — lines re-verified against current source). No code
changed; no sequence recommendation anywhere in this doc — sequencing is the
reviewer's ruling.

Candidates (from the handoff): **C1** = Word study ABP branch flip · **C2** = reader
interlinear tags Greek-keyed for backfilled PNs · **C3** = Hebrew retirement rebuild.

---

## 1. Rebuild (C3) table footprint

C3 has no dedicated plan doc; its shape comes from DESIGN_greek_name_identity.md
("stage 3: retire the stopgap as identity, keep as cross-ref", layers 2/5) plus the
stage-1 run as builder precedent. Per that, the rebuild would touch:

| Table | What C3 does to it | Does C1 read it? | Does C2 read it? |
|---|---|---|---|
| `words.strongs_base` | REWRITTEN for ABP PN rows — `import_tipnr.py:719` (`UPDATE words SET strongs_base=…`) stops writing the Hebrew number, writes the Greek identity (design layer 2). Value change, not schema change. | **YES** — the ABP branch's only occurrence key: `views_lexicon.py:291–310` (`_abp_strongs_filter`), `:1151` (`_abp_book_counts`), profile `:1053`. | **YES** — the feed serves it (`views_library.py:64`, `:229`) and the tag falls back to it (see §3). |
| Hebrew cross-ref home (Q2: side table or `words` column — **new-field checkpoint, JP OK required**) | CREATED by C3. Doesn't exist yet; today's cross-ref is served from `pn_greek_identity.hebrew_base` (`views_metav.py:583`). | Only if implemented against it. | Only if implemented against it. |
| `tipnr` | REBUILT every import run (`import_tipnr.py:357`). Keys HEBREW numbers today. | No. | **YES** — the feed joins `t.strongs = w.strongs_base` (`views_library.py:70`, `:239`) for `pn_type`/`pn_types` badges. After retirement that pairing (Hebrew tipnr key × Greek strongs_base) matches nothing unless both sides move together. |
| `pn_greek_identity` | DROP/CREATE if re-run (`build_pn_greek_identity.py:201`). Its `hebrew_base` column SNAPSHOTS `words.strongs_base` at build time (PLAN_r2_stage1.md item 4) — a post-retirement re-run reads a rewritten column, so the snapshot's meaning changes; it must instead read the Q2 cross-ref home. | **YES if C1 is built pre-retirement** — the only Greek-keyed ABP occurrence source that exists before the rebuild (see §2). | **YES if C2 joins it into the feed** — it is keyed `verse_id + position`, exactly the feed's shape. |
| `pn_binding` / `tipnr_entities` / `tipnr_entity_refs` | Rebuilt by the required `build_entity_binding --apply` re-run; design layer 5: `tipnr_entities.bases` must gain the Greek keys or the fuzzy number-guard floors ABP-side binds. | No (bound-card path, not Word study). | No. |
| `step_lexicon` | Untouched (read-only input). | **YES** (lemma/translit for G9xxx under a flip). | No (tags print numbers, not lemmas). |

Design gap surfaced while walking this (evidence, not a proposal): the design says
lemma-only words (14,850) get "lemma identity without a number" — what C3 writes
into their `strongs_base` cell (blank? `'*'`? left Hebrew?) is not specified
anywhere. It determines whether those rows keep working under §2/§3's fallbacks.

Standing gates that fire on C3 regardless of sequence: roster-freeze tripwire
(`import_tipnr.py` changes ⇒ `check_roster_regression.py` CLEAN before import),
`/rebuild-words` copy-then-swap discipline, strongs_base GLOB invariant, and the
new-field checkpoint for the Q2 home.

## 2. C1 read surface — Word study ABP branch, today

- Entry links from the live card (`static/src/30-detail-panel.jsx`): a REAL
  G-number identity already links Word study by the Greek number (`:1112`); a
  STEP-extended or lemma-only identity shows a **static count only** — the code
  comment at `:1106–1107` says it plainly: "Word study can't key those yet". The
  Hebrew cross-ref line links Word study by `hebrew_base` (`:1129–1132`).
- The branch itself (`views_lexicon.py`): every ABP occurrence/count/verse query
  keys `words.strongs_base` (or full dotted `words.strongs`) via `_abp_strongs_filter`
  `:291–310`; book counts `_abp_book_counts` `:1151`; profile `:1053`. Lemma/translit
  come from `lexicon` / `dotted_lexicon`; there is **no step_lexicon read and no
  pn_greek_identity read anywhere in views_lexicon.py** (grepped: zero hits).
- What flips: Word study answering for a G9xxx or lemma-only identity. Pre-
  retirement, `words.strongs_base` contains **zero** G9xxx rows (stage-1 proved ABP
  never uses STEP numbers), so the existing predicate structurally returns empty —
  the only pre-retirement Greek-keyed occurrence source is `pn_greek_identity`
  (`greek_strongs` / `greek_lemma`, the same derivation the card counts at
  `views_metav.py:615–623`), plus `step_lexicon` for the headword. Post-retirement,
  the existing strongs_base predicate would serve real-G and G9xxx keys natively.
  That is the dependency fact for the reviewer: **C1 built pre-C3 reads side
  tables; C1 built post-C3 can reuse today's predicate.**
- Frontend counterpart: `80-lexicon.jsx` (shares the Library card classes; receives
  whatever number the card links pass).

## 3. C2 read surface — reader interlinear tags for backfilled PNs, today

- Data: the verse feed (`views_library.py:61–92`) and chapter feed (`:229+`) serve
  each ABP word's `strongs`, `strongs_base` (+ `lexicon` and `tipnr` joins). The
  chapter feed carries **no Greek identity** — receipt-0 ruled it out of stage-2
  scope on purpose (per-click endpoint only; the feed is the OFF-proof surface,
  restated at `views_metav.py:568–569`).
- Render (grep-before-you-size — every copy counted): the ABP Strong's tag is
  emitted at **5 sites**, all in `static/src/59c-library-render.jsx`:
  - chip/prose modes ×4 — `:208`, `:226`, `:267`, `:291`, identical expression
    `(w.strongs && w.strongs !== '*') ? 'G'+w.strongs : w.strongs_base`. A
    backfilled PN has `strongs='*'`, so the tag falls back to the Hebrew
    `strongs_base` — this is exactly the H90-under-Agag seam JP flagged.
  - ABP interlinear ×1 — `:787–789`, prints `strongs_base` VERBATIM by documented
    rule (`:734`).
  - The other tag sites in the file (`:143`, `:446`, `:510`, `:647`) are the
    Heb/KJV/BSB corpora — Q4-ruled untouched.
- What flips: those 5 sites need a per-word Greek key the feed doesn't carry.
  Two possible sources (sizing, not ruled): join `pn_greek_identity` into the feed
  (it is keyed `verse_id + position` — the feed's own shape), or read the rewritten
  `strongs_base` after C3. Pre-C3 the first is the only option.

## 4. Builder classification per candidate

- **C1 — flag-only** if built pre-retirement: serving-code + frontend only; every
  input (`pn_greek_identity`, `step_lexicon`) is already live; git-revertible; the
  stage-2 pattern (OFF-proof deploy → receipt → flip) applies, trial-then-apply
  does not bind. If instead built ON TOP of C3's rewritten `strongs_base`:
  **mixed** — the code edit is small but it inherits the rebuild's trial-then-apply.
- **C2 — flag-only**, same split as C1. One boundary note: a feed join moves the
  OFF-proof line — with the switch OFF the chapter feed must still be
  byte-identical (gate the join on the switch); with it ON the feed payload
  changes, which stage 2's OFF-proof never did.
- **C3 — changed-builder, unambiguously**: edits `import_tipnr.py` (roster gate
  fires), changes `build_pn_greek_identity` snapshot semantics, re-runs
  `build_entity_binding` with extended entity bases. **Trial-then-apply binds**,
  plus the copy/swap rebuild discipline and the Q2 new-field checkpoint.

## 5. Shared-switch feasibility (C1 + C2)

- The mechanism: `READER_GREEK_IDENTITY` is a single boolean read from the env at
  import (`core.py:39`), consumed by the identity endpoint gate
  (`views_metav.py:647`). Any new backend site can gate on the same
  `_core.READER_GREEK_IDENTITY`; the frontend keys off endpoint behavior.
- Both candidates CAN sit behind the existing switch: technically trivial, one-line
  rollback preserved. Consequence to weigh (fact, not a recommendation): the switch
  already runs the LIVE stage-2 card — turning it off to roll back C1/C2 also rolls
  back the receipted card flip. One switch = one blast radius.
- A second analogous env switch is the same one-line pattern and gives independent
  rollback. Nothing in the code prevents either shape.
- C3 can sit behind NO switch — it is data; its rollback is the db-swap file. And
  post-retirement the switch's OFF state stops meaning "Hebrew everywhere": the §3
  tag fallback prints whatever `strongs_base` holds, so tags would show Greek with
  the switch OFF. Any switch design must account for that inversion.

## 6. Collision list (touched by more than one candidate)

- **`words.strongs_base`** — rewritten by C3; the occurrence key for C1
  (`views_lexicon.py:291–310`, `:1151`) and served + fallback-rendered by C2
  (`views_library.py:64/:229`; `59c-library-render.jsx:208/226/267/291/788`).
- **`pn_greek_identity`** — the natural pre-C3 data source for BOTH C1 and C2; its
  `hebrew_base` snapshot is invalidated/re-derived by any C3 re-run.
- **`views_library.py` feed queries (`:61–74`, `:229–239`)** — C2 edits these
  blocks (identity join); C3 changes what their `tipnr` join (`:70`, `:239`) can
  match (Hebrew-keyed `tipnr.strongs` × rewritten `strongs_base` → PN badges lost
  unless C3 also moves the join). Same lines, two candidates.
- **`30-detail-panel.jsx:1106–1132`** — C1 changes where the identity/count links
  land (the ":1106 can't-key-those-yet" block is C1's target); C3 changes the
  cross-ref count's meaning (next bullet). Two candidates, one block.
- **`views_metav.py:628–631` (`hebrew_count`)** — counts `words WHERE strongs_base
  = <H-number>`. After C3 that column no longer carries Hebrew, so the LIVE
  stage-2 card's cross-ref count silently drops to 0 unless C3's scope includes
  repointing this query at the Q2 cross-ref home. A C3-must-touch serving site
  beyond the rebuild itself.
- **`static/app.js`** — C1 (30-detail-panel.jsx, 80-lexicon.jsx) and C2
  (59c-library-render.jsx) both rebuild the same committed bundle; different
  source files, no line collision, but parallel sessions on the bundle are the
  known clobber risk.
- C3-only (no collision): `pn_binding`/`tipnr_entities`/`tipnr_entity_refs`
  rebuild, `import_tipnr.py` + roster gate, the Q2 new table.

---

*Verification note: file/line cites checked against the working tree at commit
0f7155c. Read-only pass — no DB access needed or used; all table-shape claims come
from the builders' own CREATE/UPDATE statements in the repo.*
