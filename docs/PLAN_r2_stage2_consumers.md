# R-2 stage 2 — consumer enumeration (goes to the reviewer BEFORE any edit is sized)

Walked 2026-07-24 per PLAN_r2_stage2.md step 2: TICKET_headword_class's contamination
map + docs/claude/word-study.md + a code sweep (pn_binding / pn_greek_identity /
step_lexicon / strongs_base / english_head / PN-click paths). Every site below was read
at the cited lines, not inferred. NO code has been changed; nothing is sized yet.

## A. Sites the flip helper must feed (serve an ABP PN identity or count today)

Backend:
1. **views_metav.py:542 `strongs_count_route`** (`/api/strongs-count/<base>?by=base`) —
   THE ABP occurrence count for a backfilled PN (Hebrew base over `words.strongs_base`).
   This is the count that changes under S2-Q4; feeds card line "×N in ABP".
2. **views_metav.py:110 `pn_count`** — name-path count (`english_head` where
   `strongs_base='*'`). Under the flip this is the lemma-only card's count-by-stored-form
   anchor (S2-Q4).
3. **views_metav.py:429 `metav_entity`** — the verse-bound PN card payload (identity
   spine, ref_count, kin, metav). The BINDER does not flip (ruled); listed because the
   card built from this response is where the Greek identity header + Hebrew cross-ref
   line will render, so its payload (or a sibling lookup) must carry the
   pn_greek_identity row for the clicked (verse, word).
4. **views_library.py:64 + :229** (verse/chapter word feeds) — serve each ABP word's
   `strongs`, `strongs_base`, `is_pn`, `lemma` (lexicon join on strongs_base). The card
   header number (`entry.strongs`, rendered at 30-detail-panel.jsx:1224) originates
   here. The Greek identity either joins in here or is fetched per click — a sizing
   decision, not made yet.
5. **views_lexicon.py — Word study, ABP source branch for a Hebrew-numbered PN**:
   `_sid_pred` :297–310 (base predicate), profile ABP branch ~:921, `_abp_book_counts`
   :1151, renders-as :1179, occurrence list :1604. Reached from the PN card via
   30-detail-panel.jsx:1083 (`onNavigateToLexicon(entry.strongs, "abp")` — Hebrew
   number, ABP source). If the card's ABP line flips to Greek, this link and the branch
   it lands on must agree with the new count or the card contradicts Word study.
6. **core.py:422 `word_gloss_cols` / :445 `word_gloss_join`** — number-keyed gloss the
   card head shows; step_lexicon COALESCE (S2 lemma/translit resolution) sits beside
   this pattern.

Frontend (all in the committed bundle; rebuild required):
7. **30-detail-panel.jsx** — the ABP PN card itself: PN detection :328, Hebrew-word
   branching :334–341, pnCount :342–353, heb/kjv/bsb counts :355–391, abpBaseCount
   :393–407 (consumes site 1), metavEntity :457, section list :744–764, "×N in ABP"
   :1076/:1083, identity header :1224 (`entry.strongs`), "Strong's Hebrew" BDB section
   :977 (the H-identity block that becomes the quiet cross-ref line).
8. **56-library-order-logic.jsx** — `greekLineForWord` :134 (name-fallback Greek line)
   and `pnClickPayload` :149 (`is_pn || strongs_base==='*'`; the click payload the card
   keys off). Click ROUTING itself doesn't flip; payload may need to carry the identity.
9. **80-lexicon.jsx / Word study card** — shares the Library card classes; receives the
   Hebrew-keyed navigation from site 7's links (frontend counterpart of site 5).
10. **00-core.jsx api helpers** :362–388 (`strongsCountBase`, `pnCount`,
    `metavEntity` etc.) — plumbing for the above.

## B. Checked and proposed OUT of scope (unchanged by the flip — reviewer to confirm)

- **views_kjv.py / views_bsb.py / views_heb.py counts** — stay Hebrew-keyed (Q4 ruled);
  the card keeps their lines as-is.
- **views_search.py** in-text search — highlights by re-matching prose, never touches
  identity (per TICKET_headword_class).
- **ai.py Ask-corpus** — evidence highlights by Strong's position; search-side, not a
  card identity surface.
- **views_seo.py:601 `/word/<sid>` pages + :580 ABP ref sampling** — number-keyed SEO
  pages, not the ABP PN card; an H-number page keeps listing its ABP refs by base.
  FLAGGED for the reviewer: these pages will still describe a Hebrew number's ABP
  presence Hebrew-keyed after the flip — consistent with Q4 (findability preserved) but
  it is a surface a purist could call mixed. Proposal: out of scope for stage 2.
- **views_lexica.py (Lexica dictionary)** — number-keyed, no '*' PN rows in lexica_def.
- **'none'-bucket words (3,380)** — C4: no code path change; they never enter the helper.
- **Build/audit scripts** (build_entity_binding, build_pn_greek_identity,
  audit_two_derivations, reconcile_binder_delta, etc.) — build-side, not serving.

## C. Open sizing questions carried to the reviewer with this list

- Where the Greek identity joins in: per-word in the chapter feed (site 4) vs a
  per-click lookup beside metav_entity (site 3). Not sized; helper design follows the
  reviewer's read of this list.
- Whether site 5 (Word study ABP branch for an H-number) flips inside stage 2 or is
  explicitly held Hebrew-keyed with the card link labeled accordingly — the plan's
  "every surface, one switch" ruling (S2-Q1) vs the plan text scoping the flip to card
  surfaces. Reviewer call requested.
