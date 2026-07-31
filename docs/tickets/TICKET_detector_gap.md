# TICKET — PN-star merged-verb detector gap (Mat 26:1 class)

Opened 2026-07-31 (G707 session close). Status: OPEN — this is the SESSION OPENER for the
next PN-star arc; it comes BEFORE the 145+509 fix session.

## The finding
JP spotted Mat 26:1 ("Jesus finished") as a PN-star merged-verb case. It is NOT in
AUDIT_pn_star_verb_merge.md's catalogued 145 — the doc's only Matthew-26 entry is 26:4.
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
- AUDIT_pn_star_verb_merge.md — mechanism, the 145 list, detector control history.
- tests/test_pn_star_verb_merge.py — regression pin (flips to the split shape when fixed).
- TODO.md "PN-STAR MERGED-VERB CLASS" — the held fix-session ticket this gates.
