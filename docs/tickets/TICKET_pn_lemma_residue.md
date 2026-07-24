# TICKET — the 5,030 PN words the scrape pairing refused (lemma residue)

Status: OPEN, sized 2026-07-24 (R-2 stage-1 dry-run). Pull, not push — pick up after
stage 1 lands, or alongside Pile P (possessive/plural cells), which likely shares causes.

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
