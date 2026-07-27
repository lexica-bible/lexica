# TICKET — Lane #3: Word study opens by LEMMA (live links for numberless PN cards)

Opened 2026-07-27 (reviewer sequence #1 → #3 → #2; #1 closed same day). Scope only —
build awaits ruling.

## The gap (verified in code)

~14,850 PN identities are lemma-only: real Greek name-form, no Strong's number in any
scheme (Q3 honest state). Their card shows a static "N× in ABP (this form)" count —
30-detail-panel.jsx:1137-1143 renders the occ line as a BUTTON only when
`greekId.greek_strongs` exists, else a plain count — because every Word-study entry
point is number-keyed (`/api/lexicon/profile/<strongs>`, `/books/<strongs>`,
views_lexicon.py:1129/1372; view id `lexicon`, `/?lex=` URL key). The count itself
already exists server-side: views_metav.py:632-636 counts pn_greek_identity rows
sharing the stored `greek_lemma` where no number exists. R-2 residue note: "new
key/URL shape = own candidate" (held out of G2 by ruling — this is that candidate).

## Scope (app-side only, zero data writes)

1. **Server** — one new read-only route, e.g. `/api/lexicon/pn-lemma?lemma=<form>`:
   occurrences = pn_greek_identity rows with that greek_lemma (both numberless AND
   numbered rows sharing the form? NO — numberless only, matching the card's own
   count at views_metav.py:632, so the link's list length equals the count shown),
   joined to words/verses for the verse list, book breakdown, and per-verse English.
   Slim profile shape (form, translit if derivable, occurrence count, verse list) —
   NOT the full mega-profile; these are names, 1–50 occurrences typical.
2. **Frontend** — Word study accepts a lemma key alongside the number key: the
   card's occ line becomes a button when `greek_lemma` exists (number absent),
   navigating with the lemma; the Word study header shows the Greek form with an
   honest "name-form (no Strong's number)" state line — the same honest-state
   language the card already uses. URL persistence: extend the existing `/?lex=`
   key (e.g. `lex=lemma:<form>`) so refresh/back behave like number pages.
3. **No change** to numbered cards, no change to any table.

## Collision handling (the ruled question)

Same lemma spanning multiple identities (two people printed identically): show the
LEMMA-WIDE occurrence list. This is the established precedent — JP already ruled
occurrence controls are lemma-wide, not entity-scoped, when the bound-card
occurrences landed 2026-06-28 ("all Edens sharing the number", user's explicit
choice; memory project_entity_resolution_rebuild). Identity disambiguation stays on
the reader cards (TIPNR bind), where it belongs. The Word-study header's state line
says "every occurrence of this printed form" so the page never implies one person.

## Verify plan

- Locked test: route returns exactly the card's count for a seeded lemma-only pair;
  a numbered identity's form does NOT leak into the numberless list; empty lemma 404s.
- Live: pick a lemma-only card (dry: `SELECT greek_lemma, count(*) FROM
  pn_greek_identity WHERE greek_strongs IS NULL AND source='lemma-only' GROUP BY
  greek_lemma ORDER BY 2 DESC LIMIT 10`), click through, list length = card count.
- Chrome desktop check (standing rule) + mobile sheet unaffected (no new card).

Status: SCOPED — awaiting ruling on the collision recommendation + build go.
