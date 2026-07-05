# Reassembly-diff — findings + rebuild plan (2026-07-04)

READ-ONLY audit complete. No data writes yet. This memo is the decision doc; nothing
changes until it's approved.

## What the tool does
`scripts/audit_reassembly_diff.py` rebuilds each verse from its word rows and diffs
against `verses.text`. v1 = bag-of-words (reorder-immune). v2 = order-aware, using a
Python port of the reader's own `getEnglishOrderWords` (proven byte-equal to the JS on
137 fixture verses — `tests/test_reorder_port.py`; quiet on 135/136 clean snapshot
verses). v2 supersedes v1 and is the count below.

## The count (31,237 verses)
| class | count | meaning |
|---|---:|---|
| word-order | 364 | a real word sits in the wrong slot |
| punct-position | 261 | a comma / em-dash landed on a neighbor (cosmetic) |
| content-other | 13 | `verses.text` carries baked apparatus (`1let`, `AndG.`) |
| dup-gloss | 0 | — |

Spread tracks **book size**, not LXX-renumbered books — the renumbering hypothesis is
dead. The real defects come in **phrase-family recurrences**: "LORD of the forces" (~24
in Jeremiah), "the Christ," (~8 gospels), "same" (~5), subject pronouns (I/it/he/they),
verb-particle "up X". One root cause per family, not 364 unique bugs.

## Root cause (verified)
`verses.text` and the word rows come from the **same** ABP source (`abp_texts/`) but
through **two independent bracket-reorder parsers**:
- `load_abp_prose.py` `reorder_bracket()` → `verses.text`
- `build_words_from_abp.py` tokenizer + the reader's `getEnglishOrderWords` → word rows

Where the two reorders diverge, they disagree. **The tool finds the disagreement; it
does NOT prove which side is right.** Two directions, confirmed by sampling:
- **word-order (364):** on Jer 48:1 the WORD side is wrong — the split step put the
  second `the` on the `forces` slot instead of before `God` ("of the the forces … God"
  vs the clean prose "of the forces … the God"). This is the split-step slotting family
  (same neighborhood as the earlier split-flip / split-compounds fixes).
- **content-other (13):** here the PROSE side is wrong — `load_abp_prose` left order
  digits (`1let`, `3in 4multitude`, `4dried`) or a stray Strong's `G` (`AndG.`,
  `biddingG.`, `viewG.`, `buttocks.G`, Mal 3:6 `G`) unstripped. Word rows are clean.

So "trust `verses.text`" is NOT universal — the 13 prove it can be the wrong side.
**Before any fix, each word-order family is checked against the ABP source** (confirm-
source rule) to pin which side is authoritative. Jer 48:1 is confirmed (words wrong);
the Christ / same / pronoun families are NOT yet confirmed and must be, per family.

## User-facing blast radius (draw-citation collision check)
`scripts/check_draw_citations.py` — 36 shipped citations quote a flagged verse:
- **1 content-other** — Mat 21:19, cited by the `G1096` (γίνομαι) entry. Highest concern:
  could show baked apparatus.
- 21 word-order, 14 punct-position — all `lexica_def` rows; the draw cache has only 1 file.

Most cards render verse text **live** from `verses.text`, so once the corpus is fixed
they self-heal on the next load — a redraw is needed ONLY for entries that froze the
verse text into stored fields. The redraw subset is ≤36, likely far fewer. To be
determined once the fix side is settled.

## Proposed plan (for approval — no writes yet)
1. **Reconcile the two reorders to ONE.** The divergence exists because there are two
   parsers. Fix = make `load_abp_prose` and the word build share a single reorder
   decision, adjudicated against the ABP source per phrase-family.
   - word-order families → fix the `build_words` split-step slotting (words side).
   - the 13 apparatus leaks → fix `load_abp_prose` stripping (prose side).
2. **Both stores rebuild from the pinned source.** Words table AND `verses.text`
   regenerate from `abp_texts/` (the cert-pinned feed). **Neither store is synced from
   the other** — a broken store is never copied over a good one (standing rule).
3. **punct-position (261):** decide separately — likely leave (cosmetic) or a light
   float-alignment pass. Not blocking.
4. **Redraw** only the citation entries whose text is frozen (from the collision list),
   after the corpus is clean.

## Gate block (must all pass before the rebuild swaps in)
- `compare_words.py` diff reviewed (pinned live-stale cells only)
- `cert_invariants.py` 7/7 green + `--controls` all fire
- L9 split lint = 0
- **v1 AND v2 reassembly-diff = 0** (`--controls` + `--controls --v2` fire first;
  `tests/test_reorder_port.py` green)
- row pins re-pinned in the same rebuild commit (never hand-edited to force green)
- then, and only then, wire v2 into `cert_invariants.py` as a standing invariant

## Open decisions for you
1. Confirm the fix side per family against the ABP source (Christ / same / pronoun /
   verb-particle) — I'll prep the source-vs-both-reorder dumps; you adjudicate.
2. punct-position: leave, or align?
3. Rebuild is a rare high-stakes job (`/rebuild-words`). Green-light the reconcile-and-
   rebuild only after 1 is settled.
