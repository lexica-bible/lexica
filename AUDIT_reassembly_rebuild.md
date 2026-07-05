# Reassembly-diff — findings + rebuild plan (2026-07-04)

READ-ONLY audit complete. No data writes yet. This memo is the decision doc; nothing
changes until it's approved.

## SESSION HANDOFF — next session is THE BUILD (decisions locked 2026-07-04)
Diagnosis done + committed (5 read-only tools, chip-lift fix live). Decisions locked:
- **Architecture A** — `verses.text` stays independently derived (the witness that caught
  this; B destroys the oracle). Do NOT derive it from the rows.
- **Fix target: `build_words` token slotting** — the word rows are mis-slotted (prose is
  the correct side on all 6 families). Prime suspect: `_split_compounds` article-fronting
  (build_words_from_abp.py ~386–470; see its own reverted "the LORD/their X" over-reach
  comment). CONFIRM by building Jer 48:1 in isolation and watching the split step before
  changing anything.
- **paren-edge:** extend the reorder float to include `)` (today `. , ; : ! ? ·`).
- **13 leaks:** run `python3 scripts/dump_family_source.py bible.db --scan-brackets` first.
  Malformed source (a `]` with no `[`) = **Van der Pool's source defect** → log as **Tier B
  `abp_corrections` entries** AND make `load_abp_prose` tolerate an unmatched bracket
  (don't leak digits).
- **punct-position (261): LEAVE**, but **re-count after the rebuild** (the slot fix may cure
  some free), THEN pin the survivors as a **frozen allowlist** in the v2 gate — any NEW
  punct hit still fires.
- **Both-store rebuild** from the pinned feed (`abp_texts/`); neither synced from the other.
- **Redraw only G1096 (Mat 21:19)** after the corpus is clean.
- **PASS CRITERION for the gate:** zero word-order + zero content-other + no NEW
  punct-position (allowlist only). Then wire v2 into `cert_invariants.py`.
- **Full gate block:** the 7 cert invariants + L9 lint + v1 AND v2 at criterion +
  `tests/test_reorder_port.py` green + row pins re-pinned in the rebuild commit.

Tools (all committed, READ-ONLY): `scripts/audit_reassembly_diff.py` (v1/v2 + `--controls`),
`scripts/reorder_english.py` (+ `tests/test_reorder_port.py`), `scripts/check_draw_citations.py`,
`scripts/dump_family_source.py` (+ `--scan-brackets`). Rebuild procedure: the `/rebuild-words` skill.

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

## Family adjudication (source-arbiter dump, 2026-07-04) — all self-adjudicated
Every word-order family: the ABP **source order is unambiguous, the PROSE side
(`load_abp_prose`) reproduces it, and the WORDS side (`build_words`) deviates.** For 5
of 6 there is NO bracket, so the reorder function is not even acting — the word ROWS
are mis-slotted at build time.

| family (exemplar) | source order | wrong side |
|---|---|---|
| forces (Jer 48:1, 19:15) | of the / forces, / the / God | words (2nd `the` pulled forward) |
| the-Christ (Mat 16:16) | the Christ, the son | words (same `the` pull) |
| same (Rom 9:17) | this same thing | words (→ `thing same`) |
| pronoun-fronting (Gen 7:1) | I beheld you | words (→ `beheld I you`) |
| verb-particle (Mat 26:16) | deliver him up | words (→ `up he him`) |
| paren-edge (Heb 10:8) | …the law) | words (`)` did not float past the reorder) |
| Mat 21:19 (leak) | `[…]` MISSING its opening `[` | prose (parser choked on a malformed source) |

**This INVERTS the canonical direction below.** The reliable order authority is
`load_abp_prose` (reads source order directly, correct on all six), NOT the reader
port. The port's reorder is fine; its *input rows* are the bad side.

## The fix: consolidate on the correct order authority (not a patch)
The divergence exists because two independent parsers reorder the same ABP source. The
fix is not to patch each — it is to make BOTH stores flow through a **single canonical
reorder implementation**, so they cannot diverge again by construction.
The order authority is `load_abp_prose`'s source reading (proven correct on every
family). The reader port's REORDER stays; the fix is upstream, in how `build_words`
slots tokens.
1. **Fix `build_words` token slotting** so the word rows sit in source order (the 6
   word-order families all trace here — non-bracket tokens placed out of order). Target
   the split / article-attach step, not the reorder.
2. **Verify by construction:** after the slot fix, `reassemble(word_rows)` via the port
   must equal `verses.text`. That is exactly what v2 measures → drive v2 to zero.
3. **paren-edge:** extend the canonical reorder float to include `)` (today only
   `. , ; : ! ? ·`). Small, shared by prose + reader.
4. **The 13 apparatus leaks:** `load_abp_prose` choked on malformed source brackets (a
   `]` with no `[`, Mat 21:19). FIRST scan all 13 to confirm the shape, then either fix
   the source lines or make the prose parser tolerate an unmatched bracket.
5. **Both stores rebuild from the pinned feed** (`abp_texts/`); neither synced from the
   other (standing rule).
6. **punct-position (261):** decide separately — likely leave (cosmetic). Not blocking.
7. **Redraw** only `G1096` (Mat 21:19), after the corpus is clean.
8. **v2 guards ingest permanently** — wired into `cert_invariants.py` at zero, so the
   words rows and `verses.text` can never silently drift again.

### Architecture choice for you
Two ways to make them un-divergeable:
- **(A) keep both builds, share the order decision + gate with v2** — `build_words` is
  fixed to match `load_abp_prose`'s source order; v2 stays as the independent cross-check.
  Keeps the independent oracle. Recommended.
- **(B) derive `verses.text` FROM the fixed word rows** (retire `load_abp_prose`) — they
  can't diverge, but v2 becomes trivial (same source) and you lose the independent oracle,
  so it's only safe AFTER the slot fix. Not recommended while the rows are the buggy side.

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
