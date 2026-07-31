# TICKET — 509 article-slot re-sweep (content English riding the G3588 slot)

Opened 2026-07-31 (charter: `docs/handoffs/HANDOFF_2026-07-31_next_cc.md`).
**Status: CLOSED 2026-07-31** — count revised, no data written, no DB read.
The fix session now opens against the revised list below.
**Fix session opened 2026-07-31: both session-open rulings are recorded in §6a/§6b
(awaiting JP's confirm). Nothing built, nothing written until he confirms.**

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

## 6. DECIDE AT SESSION OPEN — the two questions, and the rulings

The questions as asked (JP, 2026-07-31):

**Q1 — one lane or two?** Bin D splits ~1,054 function-word rows vs ~585 content-word rows,
and the repair SOURCE differs: conjunction/copula/pronoun numbers for the first, nouns for
the second. Lumping them risks a pass tuned for one class silently mangling the other.
Rule this before writing a predicate, not after.

**Q2 — expect the shipped-row count to land well under 2,662, and do NOT read that as
shortfall.** Part of the population closes by RULING, not by writing — the 1Co 1:25 class
is ABP printing supplied English over the bare article, a display decision. Declare up
front how many rows are expected to close each way.

**Parked, deliberately not run now:** the row-by-row diff behind the 26-row gap in §4b.
Both readings leave the same ~2,662 rows in scope, so it buys nothing today. Run it only
if the session wants to know whether extending the lexicon path is worth it.

---

### 6a. RULING 1 — TWO lanes, split on ORIGIN, not on word class (recorded 2026-07-31)

**Two lanes, yes. But the fault line the charter named — function word vs content word —
is the WRONG axis, and splitting on it would cause the exact mangling it was written to
prevent.** The real question per row is: *is there an empty slot the English can go back
onto?* That is structural and decidable from the source; word class is not.

The word-class axis cuts straight across both repairs — four rows, source-verified:

```
  Act 20:15  'and'      FUNCTION  ... andG3588 G1161 another day ...   G1161 present, BLANK -> fill it
  1Co  4:20  'is the'   FUNCTION  ... 1is theG3588 2kingdomG932 ...    no Greek copula at all -> nothing to write
  Num  7:25  'brought'  CONTENT   brought G3588 his gift;G1435         verb number absent -> curated write
  Luk  6:15  'son of'   CONTENT   theG3588 son of G3588 Alphaeus,G*    'son of' supplied -> nothing to write
```

A word-class lane would put `'and'` (fill) and `'is the'` (no-op) through the same pass,
and separate `'and'` from `'brought'`, which take the same repair. The origin axis puts
each repair in exactly one lane.

**LANE A — mechanical redistribution. 1,325 source rows (bin D 276 · bin R 1,049).**
The carrier slot has an adjacent BLANK slot holding a real number (1,317) or a star (8).
The word's own number is already in the verse and its slot is empty, so the repair is
build-side redistribution onto that slot — the `_split_compounds` /
`_redistribute_pronoun_compounds` family, no lexicon needed. **All of bin R is in this
lane**, which is why the lexicon could touch R rows at all. Composition: 957
conjunction/pronoun · 289 content · 79 other.

**LANE B — per-row triage. 1,363 rows, all bin D.**
No blank neighbour anywhere. There is nothing to fill, so no automated pass runs here.
Each row closes either by RULING (ABP supplied English — no Greek word exists) or by a
curated data write (the number is genuinely absent from the source, e.g. `1Sa 2:25`
"against the LORD", where the parallel clause in the same verse numbers its `εἰς` as G1519
and this one does not). Composition:

```
  401  copula supplied      'is the' / 'was the' / 'are the'
  204  genealogy supplied   'son of' / 'the son of'   (Luk 3 / apostle-list class)
  141  possessive supplied  'his' / 'their' / 'her'
   94  preposition          'against the' / 'concerning'  — MIXED, needs eyes
  176  conjunction/pronoun  MIXED, needs eyes
  309  content word         'the borders' 33 · 'the places' 25 · 'brought' 10 · … — needs eyes
   38  mixed function words
```

The first three families (746 rows) are supplied-by-construction: the Greek has no copula,
no "son", no possessive pronoun to carry the English. **That is a structural expectation
plus a source spot-check on 6 rows, NOT a per-row proof** — no lane-B row is declared
closed until it has been looked at.

**Consequence for the fix session: lane A is written first and alone.** Lane B does not
get a predicate at all; it gets a reviewed list.

### 6b. RULING 2 — declared split: ~1,300 close by writing, ~1,360 by ruling

Declared before any predicate is written, so the end-of-session count is measured against
this and not against 2,662:

```
  close by WRITING (lane A build fix)   1,325 source rows
                                        1,299-1,325 live  (the §4b 26-row gap sits in bin R,
                                                            i.e. inside lane A, and is parked)
  close by RULING or curated write      1,363 rows (lane B)
     of which expected RULING, no write   ~746 supplied (copula/genealogy/possessive)
     of which needs eyes before a call    ~617
  ---------------------------------------------------------------
  TOTAL accounted                        2,688 source / ~2,662 live
```

**So the shipped-row count is expected to land near 1,300, not 2,662, and a lane-B row that
closes with no data written is a CORRECT outcome, not a miss.** Anything that ships beyond
~1,325 means lane B rows were written without the row-level review this ruling requires —
treat that as a red flag, not as progress.

Two things pinned with the ruling:

- **The 8 dotted rows are individual, never batched.** G3588.2 ×7 ('oboli', Exo 30:13 /
  Eze 45:12 …) and G3588.1 ×1 may be legitimate ABP dotted assignments carrying real
  content — the standing dotted-number rule applies. Inspect each; do not fold into either
  lane's pass.
- **Lane assignment is reproducible from the committed detector, not from scratch files.**
  First build step after these rulings are confirmed: land a `--lanes` reporting flag on
  `scripts/audit_article_slot_carrier.py` that prints the A/B split from the same predicate
  the counts come from, with all existing controls still green. Until that flag exists, the
  1,325 / 1,363 numbers above are this session's finding, not a re-runnable artifact.

### 6c. `--lanes` LANDED (JP confirmed both rulings 2026-07-31) — read-only, still green

The lane is now derived inside `sweep()`, off the **same token walk that produces the
bins**, and carried in a list index-aligned with them — never re-matched to rows afterwards,
so it cannot drift from the predicate. Every earlier number reproduced unchanged on the same
run: carriers 2,689 · S 4,654 · P 1 / R 1,049 / D 1,639 · D split 585/1,054 · containment
508/0/1/0 · old replay 951 raw / 509 filtered row-for-row MATCH.

```
  LANE A  blank slot adjacent - mechanical redistribution   1325   (D 276 · R 1049)
  LANE B  no blank slot - per-row triage, NO pass           1363   (D 1363 · R 0)
          bin P excluded from both (the build already fixed it): A 1 / B 0

  LANE B families - reporting only, nothing closes on them:
       401  copula supplied (is/was/are/be)
       309  content word (noun/verb) - needs eyes
       204  genealogy supplied (son/daughter of)
       176  conjunction/pronoun - MIXED, needs eyes
       141  possessive supplied (his/their/...)
        94  preposition - MIXED, needs eyes
        38  mixed function words - needs eyes
       746  supplied-by-construction  ·  617 need eyes on the row
```

**The lane classifier got its own controls** (certification rule — a classifier never fired
on a known positive certifies nothing), chosen to CROSS the word-class line in both
directions so the classifier breaks loudly if it ever drifts back onto word class:

```
  lane Act 20:15  'and'       want A  lane A  FIRED   function word, blank G1161 -> fill
  lane 1Co  4:20  'is the'    want B  lane B  FIRED   function word, no Greek copula
  lane Num  7:25  'brought'   want B  lane B  FIRED   content word, number absent
  lane Luk  6:15  'son of'    want B  lane B  FIRED   content word, supplied English
  lane Gen 22:21  'Huz'       want A  lane A  FIRED   the star sub-case (blank G*)
  lane 1Ki  9:26  'the city'  want B  lane B  FIRED   the archetype, no slot to fill
```

**Second halt path demonstrated live, not assumed.** `--prove-halt-lanes` re-declares
Act 20:15 'and' as lane B (its G1161 neighbour is blank and present, so a working
classifier must refuse):

```
  lane Act 20:15 'and'  want B  lane A  SILENT
  HALT: a control went silent - the predicate changed. Do not trust any count from this run.
  exit 1
```

Exit codes checked on every mode: `--prove-halt` 1 · `--prove-halt-lanes` 1 · `--controls` 0
· `--list D` 0 · `--old` 0. Still read-only, still no DB read, no data written.

### 6d. `--manifest` LANDED (2026-07-31) — lane A pinned by identity, not by count

A count has no identity. The fix reclassifies every row it repairs (lane A → bin P), so
lane A's membership exists **only before the write** and cannot be reconstructed after.
`--manifest A|B` prints the lane's full row list plus a SHA-256 over it, so the post-fix
check is set identity — "the build touched exactly these rows" — instead of arithmetic that
a compensating pair of errors could satisfy.

Reporting only: `lane_of` and the bin predicate untouched. `lane_of`'s own reason string is
now carried out of `sweep()` beside the lane letter (same index alignment, same rationale)
so the manifest separates numbered-slot rows from star rows without a second token walk —
a second walk would be a *copy* of the predicate, not the predicate.

```
  docs/audits/MANIFEST_lane_a_article_slot.txt
  sha256 e0ff71f85f8e3dbac22a674378125900ad8edf30049508377ea227e17dc62332
  1,325 rows = bin D 276 + bin R 1,049 = 1,317 numbered-slot + 8 star
```

Regression baseline identical across the change: lane A 1,325 · lane B 1,363 · P 1 · replay
951/509 row-for-row · all six bin controls, six lane controls and four red-first checks
FIRED · `--prove-halt` and `--prove-halt-lanes` both still exit 1.

### 6e. RULINGS 3–5 — the fix predicate (recorded 2026-07-31, before any predicate was written)

**Open call "direction" was NOT a ruling — it was already decided and only needed reading.**
`lane_of` tests both sides (`i-1` and `i+1`) and the lane controls prove both shapes are in
scope: `Act 20:15 'and'` on a numbered slot, `Gen 22:21 'Huz'` on a star. Read out, not ruled.

**RULING 3 — the move is decided by WORD CLASS, never by position.** The shape census over
all 1,325 lane-A rows:

```
   869  residue is a clean PREFIX     "But the"         XA
   373  whole slot is residue         "his own"         XX
    58  residue is a clean SUFFIX     "by his"          AX
    11  residue is a clean MIDDLE     "for indeed the"  AXA
    14  INTERLEAVED                   "is the whole,"   XAX
```

Prefix is not the rule, it is the rule's most common consequence — 456 rows sit off it. One
formulation covers all four clean shapes with no position logic: **move the words that are
not the article's own English, leave the ones that are, wherever they sit.**

**RULING 4 — the stays-set is ARTICLE_ENGLISH *plus* substantival, defined once.** 226
lane-A rows carry `one/ones/thing/things` (`"But the one"`, `"all things,"`,
`"but to the ones"`). The detector's own predicate already says those ARE the article's
English — that is what bin S is — but `residue()` strips only `ARTICLE_ENGLISH` and hands
back `['but', 'one']`. A pass built on the narrower set would drag `one` off the article and
leave a bare `"the"`: **226 new defects manufactured while fixing old ones.** The set must be
defined in ONE place and shared with the S-predicate, not duplicated, or the two drift apart
again exactly as they had here.

**RULING 5 — the STRADDLE rows go to curated handling, same as lane B. 25 rows, not 14 —
corrected below, and the build ruled this once already.**

First draft of this ruling excluded 14 rows on the test "is the residue contiguous". That
test is too loose, and `build_words_from_abp.py:868` already carries the right one, written
for the 2026-07-05 (P1) defect in `_redistribute_pronoun_compounds`: English moves between
two slots ONLY when the kept words sit **entirely before** or **entirely after** the moved
run. Kept words on BOTH sides of the moved run is a straddle — *"two slots can't hold both
positions"* — and the pass leaves the phrase whole.

`"the same things"` and `"for indeed the"` have perfectly contiguous residue and still fail:
the article's own words sit either side of it, so no two-slot arrangement reproduces the
source reading order. The contiguity test would have written 11 of those. **Same defect
class as (P1), caught before it shipped rather than after.**

The neighbour evidence stands and points the same way: of the rows the contiguity test did
catch, **12 of 14 have two residue blocks and one blank slot** — `Heb 2:10 "is the whole,"`
needs `is` one way and `whole` the other with only G3956 blank, so no correct mechanical
answer *exists*. `1Ki 3:23` and `Deu 8:11` have two blanks and still need a per-block
direction call, which is judgment, not mechanics.

**Use the build's test, not a new one.** 25 rows out: bin R 24, bin D 1 (`Jer 25:6`).

**RULING 7 — a slot whose English is ENTIRELY residue moves whole, and the article is left
with no English (373 rows).** The pronoun pass refuses this case (`if not keep_idx:
continue`) because a pronoun always renders in English. An article frequently does not —
untranslated G3588 slots are ordinary throughout the corpus — and if none of the English on
the slot is the article's own, all of it belongs to the neighbour. Flagged explicitly rather
than folded in silently: it is 29% of the pass, and it is the one rule here with no build
precedent to lean on.

**RULING 6 — the 8 star rows split 6 / 2, on semantics not scheduling.** Only two carry a
name: `Gen 22:21 'Huz'`, `Isa 46:13 'to Israel'`. The other six are possessives and function
words — `'his'`, `'so as'`, `'with his'`, `'even by the'`, `'Is'`, `'his'`. A star slot is a
PROPER-NOUN slot, so those six are wrong to write regardless of what the PN-star work does:
a permanent exclusion, not a scheduling hold. The named two are held for a post-PN-star
landing per §7's separate-landings rule. This is TODO ②'s pinned lesson holding: the
discriminator is **whether the carrier holds a name**, never adjacency.

**WRITE TARGET — 1,292.** Every exclusion is enforceable from the manifest's own fields (the
reason string for the star rows, the word classes for the straddles), so the pass's scope is
derivable and re-checkable, never a hand-carried list.

```
  1325  lane A
   -25  straddle           -> curated (the build's own (P1) test, not contiguity)
    -6  star, no name      -> excluded on their own terms, permanently
    -2  star, named        -> held for post-PN-star landing
  ----
  1292  the pass           = bin R 1,025 + bin D 267
```

Shape census under the build's test, all 1,325 rows — this replaces the earlier
prefix/suffix/middle/interleaved buckets, which split on the wrong question:

```
   869  OK - the moved run leads         "but to the ones"   -> move "but", keep "the ones"
   373  WHOLE slot moves (ruling 7)      "his own"           -> article left blank
    58  OK - article's own words lead    "with our own"      -> keep "with", move "our own"
    25  STRADDLE - skip (ruling 5)       "the same things"   -> keep either side of the move
```

**EXPECTED PICTURE — pre-registered.** The 33 excluded rows are NOT all proven defects:
24 of the 25 straddles are bin R, all 8 star rows are bin D.

```
                 before      after a correct fix
  bin P               1      ~1,293   (1 + the 1,292 written)
  bin R           1,049         ~24   (the straddle R rows - NOT ~0)
  bin D           1,639      ~1,372   (lane B 1,363 + Jer 25:6 + the 8 star)
  lane A          1,325          ~0
  lane B          1,363       1,363   UNCHANGED - if this moves, the pass overreached
                                      total 1,293 + 24 + 1,372 = 2,689 carriers
```

**bin R landing at ~0 is a FAILURE, not a success** — it means the pass ate straddle rows it
was told to leave alone.

**TWO SUPERSEDED DRAFTS OF THIS PICTURE, both recorded so the error class stays visible:**
the first said R → ~0 / D → ~1,385, wrong because it assumed every excluded row was already a
proven defect; the second said 1,303 written / R → ~13, wrong because it excluded on residue
contiguity instead of the build's straddle test and would have written 11 (P1)-class rows.
Neither was caught by arithmetic — the totals balanced both times. The first was caught by
reading which bin each excluded row actually sits in, the second by reading the build's
existing pass before writing a new one.

### 6f. THE PASS LANDED — and the gate fired first, on the MEASUREMENT

`_redistribute_article_slot` (build_words_from_abp.py) implements rulings 3–7. The first run
with it in place read as a **lane-B breach: 1,363 → 1,360**, three rows the pass was forbidden
to touch sitting in bin P. Under the charter that is halt-and-do-not-ship.

**It was the detector, not the pass.** `sweep()` matched built rows back to source rows by
ENGLISH TEXT, and (verse, English) is not a row identity:

```
  Mar 14:24  'the blood'   on TWO article slots - token 8 (blank G1473 beside it -> lane A)
                           and token 12 (no blank neighbour -> lane B)
  Rom  3:1   'is the'      tokens 2 and 8
  Psa 40:5   'concerning'  tokens 7 and 11
```

In all three the pass repaired the lane-A copy and left the lane-B copy alone — verified on
the built rows, not sampled. But with one copy surviving, a text match cannot tell WHICH, so
the repair was credited to the first and the survivor booked as the other. **A correct pass
read as over-reach.**

**Fixed by keying on the slot, certified before it was believed.** `built_carriers` now
returns `{slot position -> english}` and `sweep()` matches slot by slot. Two things had to be
proven first, and both were:

```
  row k IS source token k   0 row-count mismatches over all 27,266 verses holding
                            an article slot (the build returns one row per source token)
  the NUMBER is not usable  10,046 index mismatches, all the pronoun retag G1473 -> 846
                            doing its job - so the key must be position, not the number
```

**PASS-DISABLED REPLAY — the only thing that could make any of this trustworthy.** With the
new attribution and the one pass switched off, the pre-fix picture reproduces exactly:

```
  carriers 2,689 · S 4,654 · bin P 1 / R 1,049 / D 1,639
  LANE A 1,325 · LANE B 1,363 · bin P: A 1 / B 0 · all pre-fix controls FIRED
  lane-A row set re-derived in the ORIGINAL line format hashes to
  e0ff71f85f8e...dc62332 — IDENTICAL to the pin. The rewrite changed how rows are
  MATCHED, not which rows exist.
```

Manifest re-pinned slot-keyed: **`8737a6f222cd03e26affe63d3dfe57635d50478b86fd854ee84a80870ecbbec2`**,
same 1,325 rows. The old hash stays in the file and here as superseded.

**RE-READ OF THE FIX RUN, with attribution that works — the gate PASSES:**

```
                 before      after      expected      verdict
  bin P               1      1,241        ~1,293      52 short - all refusals, counted below
  bin R           1,049         24           ~24      EXACT
  bin D           1,639      1,424        ~1,372      the same 52
  lane B          1,363      1,363         1,363      HELD - bin P: A 1,241 / B 0
  lane A          1,325         85            ~0      = 25 straddle + 8 star + 52 refused
```

All 12 controls fired. Mat 20:22 'Jesus' and 2Sa 12:9 'Uriah' flipped D → P; **Gen 22:21
'Huz' did NOT**, because it is star-adjacent and ruling 6 refuses stars. The charter predicted
all three would flip — ruling 6 is now proven by a control that predates it.

**THE 52 REFUSALS, keyed by slot** (the earlier 39/12/5 was itself measured by the broken
matcher; "neighbour filled" was really 1, not 5):

```
    39  the article slot is already inside a bracket        1Co 3:8 slot 10 'his own'
    12  the blank neighbour is ANOTHER ARTICLE              1Ti 6:3 slot 7 'the words'
     1  the neighbour is no longer empty at build time      Pro 15:19 slot 6 'ways of the'
```

* **The 12 — correct refusal, permanent.** A blank `G3588` is not the word's own number.
  Writing "words" onto a second article slot is not repair, it is relocating the defect.
  The lane-A predicate is source-side and counts any real number, so lane A was mildly
  over-broad here; these rows are lane B in substance.
* **The 1 — correct refusal, and it fixes this pass's ORDER permanently.** An earlier pass
  fills that slot, so this pass must run after it, always.
* **The 39 — OPEN, not defaulted either way.** `1Co 3:8` carries `'his own'` twice: the
  unbracketed one is repaired onto `G2398`, the bracketed one is left. That is inconsistent
  WITHIN a verse, which is an argument for extending — but moving English inside an existing
  bracket means reassigning `greek_pos` across a group that already has an order, which is a
  different and larger question. Ruled separately, with the bracket semantics in front of us.

### 6g. LANE FOLD + THE ORDERING CONSTRAINT — both landed, both controlled

**RULING 8 — a blank neighbour that is ITSELF a G3588 does not make a row lane A.** Those
rows were MIS-LANED, not correctly-laned-then-refused: handing "words" from one article to
the next article relocates the defect — the reader still gets the article's card. `lane_of`
now requires a non-article number, so the lane definition tells the truth instead of leaving
the pass to decline what the split should never have offered.

**13 rows move, not the 12 the built-row count suggested** — that count was measured on the
built rows and merged two causes; the source-side test is the lane's own question and finds
one more.

```
             before fold    after fold
  LANE A          1,325         1,312   (bin D 263 + bin R 1,049)
  LANE B          1,363         1,376
  bins            UNCHANGED — P 1 / R 1,049 / D 1,639. The fold re-labels lanes, never bins.
```

New lane control, because a new rule with no control certifies nothing:
`1Ti 6:3 'the words' -> lane B`. It would have FAILED before this change and passes after —
red-first on its own rule. All 13 controls fire.

**The pass still refuses these too.** Belt and braces: `_redistribute_article_slot` is not
allowed to depend on the lane split being right.

**RULING 9 — the pass's ORDER in the chain is load-bearing, and is now recorded in the build
itself, not only here.** `_redistribute_article_slot` writes only into a slot that is still
empty, so it must run AFTER every pass that fills one. `Pro 15:19` slot 6 `'ways of the'` is
the pinned witness: blank neighbour in the SOURCE, filled by build time, correctly declined.
Move the call earlier and rows like it start being written into occupied slots silently.

**MANIFEST RE-PINNED — third and current:**

```
  dd0f35a5edc4fb99c9b240efbb8d960e4d18476ec04cb2c135d478fa225ee4bf   1,312 rows, slot-keyed
  8737a6f2...0ecbbec2   superseded — 1,325 rows, slot-keyed, before the fold
  e0ff71f8...dc62332    superseded — 1,325 rows, keyed by (verse, English), not a row identity
```

**LIVE-PROOF FIGURE RESTATED — §4b's expected drop is NOT ~1,363.** That figure assumed every
lane-A row would be written. 72 remain by ruling (25 straddle + 8 star + 39 bracketed), so
the source-side D+R after the fix is **1,448**, and the live sizing count should land near
that rather than at 1,363. Pinned here BEFORE the scratch build, per the verdict gate.

```
  live now (JP, §4b)   2,662
  live after rebuild   ~1,448      D 1,424 + R 24
```

**ONE OPEN RULING REMAINS: the 39 bracketed rows**, with `1Co 3:8` as the exhibit — one
`'his own'` repaired onto G2398, its bracketed twin left. Inconsistent within a verse, but
the repair means reassigning `greek_pos` across a group that already carries an order. The
39 stay refused whichever way it goes, so the scratch build does not wait on it — unless the
ruling lands first, in which case one rebuild serves both.

### 6h. THE BRACKETED CLASS SIZED — NOT contained, and it is 38, not 39

**Decision rule stated BEFORE the sizing, so the outcome could not be argued into whichever
answer was convenient:** contained → folds into this rebuild; real work → the rebuild goes
now with the class refused, and the ruling lands in its own cycle.

**Count correction first: the class is 38.** The lane fold moved one of the original 39 to
lane B (it carried an article neighbour as well as a bracket). Refusals are now
**38 bracketed + 1 neighbour-filled = 39**, and 25 straddle + 8 star + 39 = 72 remaining.

```
   20  whole slot moves    the word takes the emptied slot's OWN position - order untouched
   18  PARTIAL moves       need a NEW position inside an ordering that already exists
        of which 13 target a slot INSIDE the same bracket, 5 outside it
```

**The second decision exists, so it is not contained.** `1Pe 4:2` is the deciding shape: an
11-slot bracket group whose positions run to 9. Moving part of `'the remaining'` into it
requires choosing where in that sequence the word sits — a ruling about bracket ordering
semantics, stacked on top of the ruling about which words move. `1Co 15:28 'all things,'` has
the same problem in a 3-slot group. Code-diff size is irrelevant to this: the question is a
second ruling, and second rulings do not ride along inside a pass.

The 20 whole-slot rows genuinely ARE cheap. **Not split off anyway** — shipping the easy half
produces a rule that fires on 20 rows for a reason nobody can restate afterwards, which is
the failure mode this ticket exists to avoid.

**CALL: the scratch rebuild proceeds with all 39 refused.** 1,240 written rows do not wait on
39. The bracket class becomes its own ruling with its own controls.

## 7. STANDING WARNINGS FOR THE FIX SESSION

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
