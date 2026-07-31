# TICKET — 509 article-slot re-sweep (content English riding the G3588 slot)

Opened 2026-07-31 (charter: `docs/handoffs/HANDOFF_2026-07-31_next_cc.md`).
**Status: CLOSED 2026-07-31** — count revised, no data written, no DB read.
The fix session now opens against the revised list below.

Detector: `scripts/audit_article_slot_carrier.py` — READ-ONLY, predicate stated in
full in its header, six controls + a red-first block + an old-predicate replay, HALTs
when any of them goes silent.

---

## 1. THE OLD PREDICATE IS RECOVERABLE — three corrections to the charter

The charter said the 509's predicate was unrecoverable and its exclusion inconsistent.
Neither holds. `reproduce_old()` rebuilds the old sweep from its own committed hit list
and matches it **951/951 row-for-row, zero difference in both directions**, and 509/509
after the doc's `thing(s)` filter. Asserted on every run, so it can never go
unrecoverable again.

**Correction 1 — the exclusion WAS applied consistently.** Its stated rule
("adjacent-empty-slot cases (the build redistribution class) are EXCLUDED") keys on a
blank slot holding a **real number**, either side. It drops exactly **3,564** slots —
the charter's own figure, reproduced to the row. A blank `G*` star never triggered it.
That is why `Act 19:4 "Jesus the"` survived: its only blank neighbour is a star. Rule
working, not rule broken.

**Correction 2 — `Gen 22:21 "Huz"` is NOT a miss.** It is row 669 of the committed
list and it is inside the 509. The charter named it a known miss; it is a known hit.
`Mat 20:22 "Jesus"` and `2Sa 12:9 "Uriah"` ARE genuine misses — both carry a blank
*numbered* neighbour, so the exclusion dropped them.

**Correction 3 — the 509's real defect is SCOPE, not consistency.** Three faults:

  a. the 3,564 exclusion rests on an unproven theory about what the build redistributes;
  b. English function words riding the article slot were stoplisted out, though they are
     the same click-defect;
  c. **it never checked the BUILD.** `Act 19:4` is in the 509, yet `_split_pn_article_lump`
     (build_words_from_abp.py:728) already repairs it — the built row reads "Jesus" on the
     star and "the" on G3588. A source-side hit is not a live defect.

## 2. THE 3,564, RESOLVED — taken in, and answered by the build itself

Not excluded, and not replaced with a second theory. `_split_compounds`
(build_words_from_abp.py:469) only looks AHEAD, only from a MULTI-WORD gloss, only on an
UNBRACKETED slot, never into a `G*` star and never into the copula (1510) — so backward
adjacency, single-word carriers, bracketed carriers and star-adjacency all sit outside it.
So the 3,564 are swept IN, and every carrier verse is re-assembled by the **production**
`build_verse_words` (not a copy of its rules) to see what the build really does with it.

Each carrier row lands in exactly one bin:

| bin | meaning |
|---|---|
| **P** | source hit, gone after the lexicon-free build → the build already fixes it |
| **R** | still there at `lex=None`, gone under MAXLEX → lexicon-dependent, needs a live check |
| **D** | still there under BOTH → **proven defect**, the build cannot reach it |

MAXLEX is the most generous lexicon that could move a word OFF the article slot (empty
definition for the article, universal definition for every other slot). No real lexicon
can move more, so **D is a floor, not an estimate**.

## 3. REVISED COUNT — 2,688 (SUPERSEDES 509)

```
SOURCE STAGE
  carrier rows (content English on G3588)   2,689
  bin S  substantival "the one/thing(s)"    4,654   legitimate, not a defect

BUILD STAGE (production build_verse_words, every carrier verse)
  bin P  already repaired by the build          1   (Act 19:4 — the only corpus case,
                                                     matching _split_pn_article_lump's
                                                     own docstring)
  bin R  lexicon-dependent, pending live    1,049
  bin D  PROVEN DEFECT                      1,639

  REVISED POPULATION (D + R)                2,688   SUPERSEDES 509
     proven                                 1,639
     pending the live check                 1,049

  D split (reporting only, nothing dropped):
     content word on the article slot         585   the old 509's target
     English function word on it            1,054   same click-defect, different repair
```

**Containment: all 509 old rows accounted for** — 508 in bin D, 1 in bin P (Act 19:4),
0 lost. So the revised list is a strict superset of the trustworthy part of the 509.

Numbers are reported in FULL DOTTED form per the standing dotted-number rule. The article
slot carries three dotted forms corpus-wide: G3588 (91,304), G3588.2 (7), G3588.1 (1) —
all in scope, none dropped.

## 4. CONTROLS — all fired, halt proven live

```
  1Ki  9:26  'the city'    -> D   the old sweep's own control positive
  Mat 20:22  'Jesus'       -> D   known MISS from the 509 (live-confirmed on PA)
  2Sa 12:9   'Uriah'       -> D   known MISS from the 509
  Gen 22:21  'Huz'         -> D   IN the 509 (charter called it a miss — it is not)
  Act 19:4   'Jesus the'   -> P   in the 509, but the BUILD repairs it — the
                                  discriminating control: it proves stage 2 really does
                                  separate source hits from live ones
  1Co  1:28  'the things'  -> S   NEGATIVE control: legitimate substantival article
                                  English, must never count as a defect
  old-predicate replay     -> 951 raw / 509 filtered, row-for-row MATCH
```

**Red-first, both directions** — asserted on every run, not left as a claim in a doc:

```
  red-first Mat  20:22 'Jesus'      old-509 SILENT  new FIRES   OK
  red-first 2Sa  12:9  'Uriah'      old-509 SILENT  new FIRES   OK
  red-first Gen  22:21 'Huz'        old-509 IN      new FIRES   OK
  red-first Act  19:4  'Jesus the'  old-509 IN      new FIRES   OK
```

**HALT path demonstrated, not assumed.** `--prove-halt` re-declares the Act 19:4 control
as bin D (the build repairs it, so a working detector must refuse):

```
  control Act  19:4  'Jesus the'  want D  bin P   SILENT
  HALT: a control went silent - the predicate changed. Do not trust any count from this run.
  exit 1
```

## 4b. LIVE CHECK — RUN AND LANDED (JP, 2026-07-31): **2,662**

```
sizing count on the live words table   2,662
   floor  (real lexicon repairs every R row)   1,639
   ceiling(real lexicon repairs none)          2,688
```

**Bin R is essentially all real.** The live figure sits 26 below the ceiling, so the
lexicon repairs ~26 of the 1,049 — not a thousand. **The fix session's list is ~2,662**,
and bin D (1,639) is inside it by construction.

Caveat on record: the 26-row gap is the best reading of the difference, not a row-by-row
proof — a few could be rows the built table renders slightly differently rather than rows
the lexicon actually repaired. It does not move the fix list either way.

Archetype row check, `1Ki 9:26`, live:

```
9|3588|G3588|the city        <- the defect, still live
14|3588|G3588|the            <- legitimate article carrier, correctly NOT counted
17|3588|G3588|of the         <- likewise
```

So the sizing query is not over-matching legitimate article carriers.

**GATE MET.** Revised count declared, controls green, halt proven, live state confirmed.
The fix session may open.

## 5. NOT DONE, DELIBERATELY

No data written, no fix, no DB read by CC (CC cannot query bible.db — the live check in
§4b was JP's step). The detector prints the read-only `sqlite3` lines, including the
sizing query whose `NOT IN` list is generated from the run's own predicate so it cannot
drift from it.

That list is collected from the source tokens **and** the built rows under both lexicon
settings, not source alone: the build's repair passes mint three article-own renderings
the source never shows (`'things,'`, `'things.'`, `'the one in'` — 11 rows corpus-wide),
and each one missing would have been miscounted as a defect, reading the live number up
to 11 high. 89 → 92 strings, over-count risk 11 → 0.

Four per-control row checks (1Ki 9:26, Mat 20:22, 2Sa 12:9, Gen 22:21) print with the
run — `python3 scripts/audit_article_slot_carrier.py`.

## 6. STANDING WARNINGS FOR THE FIX SESSION

- **The article-slot class MIXES origins.** Some rows are ABP-attested *supplied* English
  printed over the bare article (1Co 1:25 "the wisdom"/"the strength" — the Greek has no
  noun there), NOT number drops. The fix is not uniformly "add a number"; sort display
  treatment from data fix per spot.
- **Bin S is not a residue to drop.** 4,654 rows where the article legitimately renders as
  "the one/ones/thing(s)" — τό/τά/ὁ standing alone as a substantive.
- **Bin D's function-word half (1,054) is the same click-defect but a different repair** —
  a missing conjunction/copula/pronoun number, not a missing noun.
- **Never re-derive the old predicate by hand.** It is pinned in `OLD_STOP` +
  `reproduce_old()` and asserted every run.

## Pointers
- `scripts/audit_article_slot_carrier.py` — the detector; predicate in the header.
- `docs/audits/AUDIT_pn_star_verb_merge.md` "Subpattern B" — the superseded 951/509 list.
- `docs/tickets/TICKET_detector_gap.md` — the star-verb close-out that chartered this.
- `TODO.md` "① 509 ARTICLE-SLOT RE-SWEEP" (closed) → "② PN-STAR MERGED-VERB FIX SESSION".
