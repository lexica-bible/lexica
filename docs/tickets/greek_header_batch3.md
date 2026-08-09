# Greek-header hand-table — batch 3 record (DRAFTED 2026-08-09, apply chain HELD)

One name: **galilee → Γαλιλαία**. Admitted under the batch-1/2 rule (every printed
form the SAME stem declined; the headword printed on ABP's own pages). Drafted from
JP-run read-only checks + the bh_scrape per-verse census, both pasted in-session.
**Nothing has been built or swapped — the scratch rebuild waits at checkpoint.**

## Why this name came up
Word study's ABP tab greys on Galilee. It is honest about the NUMBER and wrong about
the TEXT: ABP prints Galilee 73 times, every one carrying a star and no lemma, so
`has_abp` (views_lexicon.py) correctly finds nothing under G1056 and the tab dies.
The by-form door (`_pn_lemma_rows`) matches ONE stored form exactly, and the forms
are stored per inflected form — so routing the tab there without folding would have
shown 13 of 73 as if that were the total. Folding first, routing second.
Full ticket: TODO.md → "Word Study's greyed ABP tab" + the merged-ticket entry.

## The admission

| name | headword | headword's own verses (page receipts) | other forms (same stem) |
|---|---|---|---|
| galilee | Γαλιλαία | **Isa 33:9** "will be Galilee" (subject position — no preposition ambiguity) · **Mat 4:15** + **Isa 9:1** "Galilee of the nations" (the same quote, both testaments) · **Joel 3:4** "all Galilee of the Philistines?" (address) | Γαλιλαίας ×37 ("of Galilee") · Γαλιλαίαν ×20 (after into/unto) · plus the three slips below |

Nine further Γαλιλαία rows are "in Galilee" (Luk 24:6, Mar 15:41, Joh 7:1, 7:9,
Jos 20:7, 21:32, 1Ch 6:76, 1Ki 9:11, Mat 17:22). Those forms are ambiguous once the
iota subscript drops, so they carry NO weight in the admission — the four receipts
above stand on their own. (Reviewer ruling 2026-08-09: one clean receipt suffices;
adjudicate FOR a receipt, do not certify all 13.)

## The three one-letter slips (typo class — they fold under the admission)
Each is one letter off a form ABP prints repeatedly in the SAME book, and each
prints "Galilee" in English:

| verse | printed | attested form it slips from |
|---|---|---|
| Joh 4:45 | Γαλιλαάν | Γαλιλαίαν — Joh 4:3, 4:43, 4:47, 4:54 |
| Mar 14:28 | Γαλιλίαν | Γαλιλαίαν — Mar 1:14, 1:39, 16:7 |
| Mat 21:11 | Γαλιλαίς | Γαλιλαίας — Mat 2:22, 4:18, 15:29 … |

**Γαλιλίαν was NOT in the earlier record** (the diagnosis banked 5 forms / 72 rows).
It is a real row, Mar 14:28. See the count section below.

## The egypt blocker is ABSENT (checked on the page, not in the table)
Every gentilic row prints "Galilean(s)" in its own slot — Γαλιλαίοι, Γαλιλαίος,
Γαλιλαίων, Γαλιλαίους, Γαλιλαίου. **Joh 4:45 carries BOTH in one verse**, Γαλιλαάν
"Galilee," and Γαλιλαίοι "Galileans," as separate slots — the cleanest possible proof
that no gentilic is printed under a Galilee label. Egypt was held in batch 2 because
its page DID print gentilics under an "Egypt" label; that condition does not occur here.

## The 73-vs-72 gap: CLOSED, and it was not a hole
The banked diagnosis carried an unexplained one-row gap (73 word rows vs 72 identity
rows). Resolved: **the 72 was a short count — it missed Γαλιλίαν (Mar 14:28).** Proven
twice over, JP-run 2026-08-09:
- No Galilee word row is missing an identity row (the check returned empty).
- Membership, not just totals: 0 Galilee word rows point at a non-Galil form, 73 point
  at one. Same list, not merely the same size.
- The bh_scrape page census reproduces **73** independently — 13 + 20 + 37 + 3, form
  for form, from a different source than the first count.

**EXCLUSION, so no later sweep re-counts it: Γαλιλώθ (Jos 18:18) is Geliloth, a
different place.** It only appeared because the check used a "Γαλιλ" prefix. It is
already headed (source=surface) and is not part of this fold.

## Why the hand table is the only door here
The morph is **blank on all 73 rows**. The builder's automatic picker needs populated
morph agreeing on one nominative, so it can never resolve this name, in any re-run.
Confirmed by read, not assumed.

## ADJACENT LANE — logged, deliberately not chased
Some Galilean slots ride a COMPOUND slot with a star instead of G1057: **Luk 13:2**
(Γαλιλαίοι ούτοι, *-3778), **Luk 22:59** and **Luk 23:6** (Γαλιλαίός εστιν,
*-1510.2.3), **Mar 14:70** (Γαλιλαίος ει, *-1510.2.2). Nothing to do with this fold.
Flagged here so the compound-slot lane — or the 871-name follow-on below — picks it
up instead of it evaporating with this session.

## ACCEPTANCE TEST for the rebuild (reviewer-set, 2026-08-09)
1. Gate control FIRST: the batch-3 pin must **FAIL** on live-vs-live (nothing folded
   yet) and **PASS** on the scratch build. Batch-1/2 pins now pass on live and can no
   longer fire.
2. Scope proof before any swap: **exactly 73 rows flip**, all to Γαλιλαία, all
   source=surface. Every one is numberless, so the batch-2 sizing refinement predicts
   the full 73 rather than fewer.
3. **Anything other than 73 is a STOP, not a shrug.**
4. Identity delta must be zero — this lane touches pn_greek_identity only (drill
   pre-ruling 6). Any pn_binding / tipnr_entities / words / verses change is an
   automatic stop.

Apply chain is the standing one (batch 2 § "Apply chain"): rows in git → scratch
rebuild on a copy → gate control → scope proof → **JP checkpoint** → swap (single
rollback rule) → deploy reload → served check on Word study.

## Scope note
This batch is Galilee only. **871 names** are scattered across more than one form
(JP-run count, numberless lemma-only rows). That is the real size of the class and it
is a scoped FOLLOW-ON, not this ticket — Galilee plus κύριε ship as the merged
ticket's proof pair, with this record as the template. Routing the ABP tab stays held
until the pair is folded and re-counted.
