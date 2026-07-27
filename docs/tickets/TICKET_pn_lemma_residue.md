# TICKET — the 5,030 PN words the scrape pairing refused (lemma residue)

Status: OPEN, sized 2026-07-24 (R-2 stage-1 dry-run). RE-SIZED same day: 5,030 → 3,380
after the G1 fix (unbound name-path words gained the name's agreed Greek number, which
absorbed 1,650 of the refused rows into 'tipnr' — the meter moved for a named reason). Pull, not push — pick up after
stage 1 lands, or alongside Pile P (possessive/plural cells), which likely shares causes.

**LANE #2 CLOSED 2026-07-28 — scrape-based recovery COMPLETE, residue FINAL: 2,358.**
Opening number was 3,387 (census 2026-07-27). Three recovery passes, each
trial-then-apply with closing arithmetic, all locked in tests/test_pn_surface_backfill.py:
  cause A (name numbered on the scrape page + hyphen-blind compare): +744
  cause B (fold class: '*' in the compound tag ↔ label-less slot, order-paired): +285
  (the compound-cell guard and the dual-role precedence rule — lesson 87 — landed
  along the way; the Mat-1 spot list and the already-present counter each caught one
  would-be defect pre-apply)
Final residue classification: 2,298 scrape-side dead ends (the page has no Greek for
the name in that verse — honest end of THIS source; a different source is a separate
decision, not this lane), 57 blank-label slots with no/unmatched star row, 6 ambiguous
(same-token count mismatch), minus 3 slots already written under the earlier stricter
rule. Defining query verbatim (must only shrink for a named reason):

    SELECT COUNT(*) AS total_pn, SUM(s.verse_id IS NULL) AS still_missing
    FROM words w
    LEFT JOIN abp_surface s ON s.verse_id = w.verse_id AND s.position = w.position
    WHERE w.is_pn = 1;
    -- live 2026-07-28 (FINAL): 32479 | 2358   (30,121 = 92.7% reading Greek)

## What it is

`build_pn_greek_identity.py` pairs a proper-noun word to its printed Greek in
`bh_scrape.db` by NAME within the verse, refusing anything that isn't a clean
one-to-one match. On the 2026-07-24 dry-run (bible_test.db): 18,828 matched,
**5,030 refused** — those rows sit in the `pn_greek_identity` `source='none'` bucket:
honest (no number, no lemma, nothing guessed), but recoverable in principle since the
scrape HAS Greek for most of them.

## Likely causes (hypotheses — characterize before fixing; none verified yet)

- Same name appearing twice in one verse (pairing sees two candidates → refuses).
- Mangled word cells ("Aaron's," / "Hezekiah said," / "son of Simon") whose name token
  doesn't equal the scrape row's token — the same word-cell class as the 745
  import-unmatched residue and the audit's Pile-P/word-cell diagnosis.
- Split name cells ("En-" + "gedi") where the label is half a name.
- ABP/scrape English wording differences on the name itself.

## Fix shape (when picked up)

Characterize the 5,030 by cause first (a read-only PA dump: refused rows + the verse's
scrape name-slots side by side). Then per-cause rules, each refuse-on-doubt, never a
looser global match. The `none` bucket count in the identity build report is the
regression meter — it only goes down for a reason.
