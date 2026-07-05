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

## User-facing blast radius (draw-citation collision check + render trace)
`scripts/check_draw_citations.py` — 36 shipped citations quote a flagged verse
(1 content-other, 21 word-order, 14 punct-position; all `lexica_def`, the draw cache
has only 1 file).

**Render trace (verified, corrects the earlier "self-heal" guess):** the Lexica card
renders the verse text **frozen** from `def_json` (`LexicaBody` → `v.text`,
20-shared-components.jsx:195), NOT a live fetch. That frozen text was copied from
`verses.text` at build time (`build_lexica_def.py:295/684). So:
- word-order collisions (35) draw from `verses.text`, which is the **correct** side for
  that class — the card shows good prose. NOT user-facing.
- only the content-other case makes `verses.text` itself dirty, and exactly one is
  cited: **Mat 21:19 in the `G1096` entry.** That is the ONLY redraw.

The main **reader** (chip/prose) DOES render the 364 word-order defects — it reassembles
from the word rows via `getEnglishOrderWords`. That surface is fixed by the words
rebuild, not a redraw.

## The fix: ONE canonical reorder (consolidation, not a patch)
The divergence exists because two independent parsers reorder the same ABP source. The
fix is not to patch each — it is to make BOTH stores flow through a **single canonical
reorder implementation**, so they cannot diverge again by construction.
1. **Canonical reorder = the proven Python port** (`scripts/reorder_english.py`, already
   byte-equal to the reader's JS `getEnglishOrderWords`). It becomes the one arbiter of
   English order for the corpus build.
2. **Both stores built through it.** `build_words_from_abp` and the `verses.text` build
   both call the canonical reorder; the old `load_abp_prose.reorder_bracket` is **retired
   or delegates** to it. No second reorder survives.
3. **Adjudicate fix-side per family against the ABP source FIRST** (`dump_family_source.py`
   — the source line is the arbiter). Jer 48:1 confirmed: words side wrong. The other
   families self-adjudicate from the source unless flagged AMBIGUOUS (duplicate digit /
   nesting → printed-ABP tiebreak).
4. **The 13 apparatus leaks** are `load_abp_prose` strip bugs (order digit / stray `G`);
   they fall out once `verses.text` is built through the canonical path with proper
   G-number + digit stripping.
5. **Both stores rebuild from the pinned feed** (`abp_texts/`); neither is synced from
   the other (standing rule).
6. **punct-position (261):** decide separately — likely leave (cosmetic) or fold into the
   canonical float. Not blocking.
7. **Redraw** only `G1096` (Mat 21:19), after the corpus is clean.
8. **v2 guards ingest permanently** — wired into `cert_invariants.py` at zero, so the two
   paths can never silently drift again.

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
