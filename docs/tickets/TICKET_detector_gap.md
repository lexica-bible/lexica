# TICKET — PN-star merged-verb detector gap (Mat 26:1 class)

Opened 2026-07-31 (G707 session close). **Status: CLOSED 2026-07-31** — count revised, no
data written. The 145+509 fix session now opens against the revised list below.

## CLOSE-OUT (2026-07-31)

**1. Why Mat 26:1 was skipped.** Not recoverable from code — *the sweep script was never
committed* (commit 5dc96a50 landed only the test + the hit list; no script exists in the
repo, working tree, or stash). What IS provable is the gap, from the doc's own output
shape and the ABP source:

    Mat 26:4   they should seize JesusG* G2902    <- English on the STAR, number slot blank
    Mat 27:26  scourging Jesus,G* G5417           <- same
    Mat 27:47  calls ElijahG* G5455               <- same
    Mat 26:1   Jesus finishedG5055 G3588 G*       <- English on the NUMBER, STAR slot blank

The list's own column header is "star-slot English". Mat 26:1's star slot has NO English,
so no shape of that verse is expressible in the tuple — it could not be reported whatever
the predicate was. The hypothesis in the original ticket (ordering / intervening G3588) is
CORRECT as to the symptom but the cause is one layer up: the sweep is anchored on the slot
that CARRIES the English, and this class mirrors which slot that is. Same mechanism, name
and content word sharing one cell, one slot left blank — just reflected.

**2. Patched detector + controls.** `scripts/audit_pn_star_verb_merge.py` (READ-ONLY,
source-side). Predicate stated in full in its header. Controls, all three FIRED:

    Mat 26:1   class B  'Jesus finished'   -> blanks G5055,G3588   (the gap case)
    Mat 27:26  class A  'scourging Jesus,' -> blanks G5417         (original positive)
    Mat 27:47  class A  'calls Elijah'     -> blanks G5455         (original positive)

Red-first proof, both directions: class A alone returns **0** hits at Mat 26:1 (the old
orientation was blind, not merely unlucky), and re-declaring Mat 26:1 as class A makes the
run HALT instead of printing a count — the HALT path is demonstrated, not assumed.

**3. Revised count — 4,996 (SUPERSEDES 145).**

    Class A   star carries the merged English         2,237
    Class B   number carries, star left empty         2,759
       B1     carrier holds a pinned-TIPNR name       2,668
       B2     roster-silent residue, needs eyeball       91
    TOTAL                                             4,996

Containment checked: **all 145 documented rows are inside class A, 145/145.** The 145 is
superseded rather than adjusted — its predicate is unrecoverable and demonstrably ad hoc:
the structural core reproduces ~247 rows, and the ~100 it silently dropped are
structurally identical to rows it kept (`'this Moses'` out, `'these Galileans'` in;
`'O Israel,'` out, `'of Israel, no.'` in). Do not treat 145 as a baseline to diff against.

B2 is reported, not dropped: it mixes real merges the pinned roster misses (Bath-sheba,
Bezaleel, gentilics like Sadducees/Romans) with bracket-position artifacts that are NOT
defects (`1Sa 25:42 "rose upG450 G* 1Abigail],G*"` — the name IS printed, on its own star).
Two false-positive guards were tried and one was REVERTED after source check: excluding an
empty star whose neighbour is a printed star kills genuine merges
(`Gen 23:19 "Abraham entombedG2290 G* SarahG*"` is directly adjacent and IS a merge).
Adjacency is not the discriminator; whether the carrier holds a name is.

**4. The 509 article-slot set has the SAME blind spot — demonstrated, control-backed.**
That sweep is anchored the same way ("a content noun rides the G3588 slot"), so the
mirrored ordering — the noun's English on the article slot while the word's OWN slot sits
blank — falls outside it. Control positive proving the probe reaches the right population:
`Act 19:4 'Jesus the'` IS in the 509 list. The miss, same shape, absent from it:

    Mat 20:22  And answeringG611 G1161 JesusG3588 G* said,G2036

"Jesus" rides the article slot; the name's star slot is blank. The user-visible defect is
identical to the one the 509 exists to catalogue — the card heads with the article ὁ
instead of the word clicked. Also absent: `2Sa 12:9 'Uriah'`, `Gen 22:21 'Huz'`. Sizing:
**3,564** article slots carrying English have an adjacent blank numbered slot and were
excluded from the 509 wholesale by its stated "adjacent-empty-slot cases are EXCLUDED"
rule — and that exclusion was not even applied consistently, since Act 19:4 has an
adjacent blank star and survived. **The 509 needs its own re-sweep before the fix session
touches it; it is not a trustworthy population either.**

**Not done, deliberately (charter = count revision only):** no data written, no fix, no
DB read. The served state still needs confirming on PA — a source-side scan is not live
state. Read-only checks for JP in the session hand-off.

## The finding
JP spotted Mat 26:1 ("Jesus finished") as a PN-star merged-verb case. It is NOT in
docs/audits/AUDIT_pn_star_verb_merge.md's catalogued 145 — the doc's only Matthew-26 entry is 26:4.
So the sweep's list is INCOMPLETE and must not be treated as the full population: fixing
off the 145 (or the 509 article-slot set) as-is would close the ticket with the same
class still live at every slot the detector never saw.

## Evidence (checked at source, 2026-07-31)
abp_texts/abp_nt_texts/abp_matthew.txt line 911:

    (Mat 26:1)  AndG2532 it came to passG1096 whenG3753 Jesus finishedG5055 G3588 G*
    allG3956 ... he saidG2036 to G3588 his disciples,G3101 G1473

The verb English ("finished", G5055 τελέω) is glued to the "Jesus" star chunk — same
mechanism as the catalogued class. BUT the shape differs from the audit's known
positives: here the content number comes FIRST and the star LAST, with an article number
between (`...finishedG5055 G3588 G*`), whereas the fired controls look like
"scourging Jesus,G* G5417" (star first, content number after). HYPOTHESIS (unverified —
verify against the detector's actual predicate before patching): the sweep matched only
the star-first ordering / no-intervening-number shape. Do not patch from this hypothesis;
read the detector, name the exact predicate miss, then patch.

## Required for close
1. Read the sweep's predicate in the audit tooling; name the exact reason Mat 26:1 was
   skipped (ordering, intervening G3588, or something else).
2. Patch the detector; CONTROL-FIRE it on Mat 26:1 AND on the original positives
   (Mat 27:26 G5417, Mat 27:47 G5455) before trusting any new count.
3. Re-run the full sweep → a REVISED count supersedes 145 (and check whether the 509
   article-slot set has the same blind spot). The fix session opens only against the
   revised list.

## Method lesson (bake into the re-sweep)
The first grep for this finding returned a FALSE EMPTY: the pattern didn't match the
doc's own reference notation. The zero was only trusted after re-deriving the notation
from the doc's lines and getting a control hit (Mat 26:4). Every "not found" in the
re-sweep needs the same control-hit proof — a zero without a fired control is not a zero.

## Pointers
- docs/audits/AUDIT_pn_star_verb_merge.md — mechanism, the 145 list, detector control history.
- tests/test_pn_star_verb_merge.py — regression pin (flips to the split shape when fixed).
- TODO.md "PN-STAR MERGED-VERB CLASS" — the held fix-session ticket this gates.
