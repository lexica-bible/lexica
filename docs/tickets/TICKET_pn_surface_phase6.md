# TICKET — Phase-6: printed Greek for proper-noun slots (interlinear Greek line)

Opened 2026-07-27, JP-raised ("ABP Greek first reading reads full Greek front to
back"), reviewer-sequenced #1 → #3 → #2 in the Greek-coverage lane:
  #1 THIS — abp_surface backfill for name slots (the visible reading win)
  #2 the 3,380 'none'-class hold-outs (TICKET_pn_lemma_residue.md) — after #1
  #3 lemma-open Word study (the inactive ABP-occurrences links on numberless
     identities — confirmed by-design refusal, not breakage; own app change)

## Census (read-only, live PA, 2026-07-27) — defining queries verbatim

    SELECT v.book, COUNT(*) AS pn_words, SUM(s.verse_id IS NULL) AS missing_greek
    FROM words w JOIN verses v ON v.id = w.verse_id
    LEFT JOIN abp_surface s ON s.verse_id = w.verse_id AND s.position = w.position
    WHERE w.is_pn = 1 GROUP BY v.book ORDER BY missing_greek DESC;

    SELECT COUNT(*) AS total_pn, SUM(s.verse_id IS NULL) AS total_missing
    FROM words w
    LEFT JOIN abp_surface s ON s.verse_id = w.verse_id AND s.position = w.position
    WHERE w.is_pn = 1;

Result: **32,479 name slots / 32,479 missing — the gap is the entire class**, and
the total equals pn_greek_identity's row count exactly (the two systems agree on
what a name slot is). Top books: 1Ch 3,076 · Gen 2,546 · Num 1,936 · Jos 1,777.
Matthew-1 detail dump (same joins, book='Mat' chapter=1) confirmed the hard
shapes: same name twice in a verse (both Isaacs, Mat 1:2), punctuation/prefix
cells ("of David,"), '*' numberless slots, and Emmanuel carrying Jesus' G2424 —
proof the pairing must go by NAME, never by number.

## Build: scripts/backfill_pn_surface.py

Pairs each is_pn word to the scrape's NAME rows (bh_words, blank Strong's +
Greek form) by name token within the verse — the pairing
build_pn_greek_identity.py proved — extended with two safe rules for the
genealogy shape:
  1 candidate → take · N candidates all same form → take · N candidates =
  N same-name slots → pair in printed order · anything else → REFUSE, counted.
Writes NEW rows only into abp_surface (never overwrites; non-PN rows untouched);
serving is the existing greekLineForWord chain step 1 — zero UI change. Undo =
delete the added rows. Locked test tests/test_pn_surface_backfill.py (real-shape
fixtures; ambiguity + no-match refusal controls must FIRE; never-overwrite +
arithmetic-closes checks) — green locally, wired into pre-commit + CI.

## Gate (reviewer shape, ruled 2026-07-27)

1. Dry-run on PA: arithmetic must close on 32,479 exactly (new + refused +
   already = total), already-present = 0, Matthew-1 spot list eyeballed against
   the ABP page (torture test: split/repeated/possessive names).
2. Refusal count sets the honest remainder — it only shrinks for a named reason.
3. --apply, then build_abp_translit.py for the new rows, then standard reload +
   sweep. Post-apply re-run of the census must show missing = the refusal count.

Status: **APPLIED + LIVE 2026-07-27.** Dry-run and apply matched exactly:
359,288 → 388,380 (delta 29,092; refused 3,387 = 3,381 no-match + 6 ambiguous;
arithmetic closed on 32,479; already-present 0; edge-trim cleaned 243 forms —
the '΄ Αχαζ' class — letterless 0). Matthew-1 spot list clean both runs.
Translit re-run filled all 388,380; deploy.sh reload. Live verification:
/api/chapter/Mat/1 serves inflected "Αβραάμ" + translit on the Abraham name
slot — the interlinear Greek line reads Greek with zero UI change.
Post-apply census expectation: missing = 3,387 (the lane-#2 remainder).
