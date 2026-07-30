# TICKET — witness-divergence name slots (class 3, scoping only — NO build)

Opened 2026-07-30 as "supplied-subject binds"; **RENAMED after the itemization
falsified the founding assumption** (correction owned in the record, reviewer-
accepted): the original description said "ABP names the subject where the
underlying text has a pronoun." Measurement says otherwise — see below.

## What the class actually is (itemization + Greek-token check, 2026-07-30)
**392 slots, census in `docs/tickets/class3_witness_slots.txt`.** For every one:
- the clicked name is PRINTED in ABP's own text (392/392, full scan of the
  pre-build source), and
- the word row is **italic=0 — a real word of ABP's Greek base, NOT a translator
  addition** (392/392, `scripts/audit_witness_italic.py` on the live table;
  spot sample also showed the Greek directly: Ιακώβ Gen 29:32, Ιησούς Mat 14:14,
  Γωγ Amo 7:1), and
- no TIPNR candidate's reference list covers the verse — because TIPNR's refs
  follow a different base text (Hebrew MT / critical NT) that lacks the name
  there (LXX and TR-family witnesses genuinely read these names).

So the class is **witness-divergence**: ABP's primary text attests a name that
TIPNR's reference base doesn't list at that verse. The "translator-supplied
pronoun" class has ZERO members.

## The doctrine question for the design pass (restated with true size)
**When ABP's own Greek attests a name that TIPNR's base text lacks, does the
primary text's reading suffice to bind, given the referent is contextually
unambiguous?** The Cainan rulings (5 rows) and the batch-2 abimelech row already
answered yes at small scale with the LXX-only flag. At ~392 slots the right shape
is a per-slot witness-flag MECHANISM, not hand rulings — that is the design
pass's actual subject. Card wording for witness-dependent binds is part of the
design (provenance contract territory).

## Resolved out of this ticket (2026-07-30)
- 59 strict compound-fragment slots (Ben-hadad, Obed-edom, Ezion-geber…) →
  **rulings batch 2** with abimelech→Achish (see pn_hand_rulings.tsv).
- 9 Psalm-superscription slots → part of this class (LXX title attributions);
  abimelech ruled, the rest await the design pass.
- Adjacency compounds (~41: "Ramoth Gilead" / "Jabish Gilead" printed as two
  words, entity keyed under the FIRST word — Ramoth@Gen.31.47-Hos covers the
  sample 6/6): **own evidence pass required before ruling** (bar: adjacent token
  forms the attested compound AND the first-word entity's refs cover the verse;
  per-slot evidence; near-misses named). Batch 3 candidate.
  **DISPLAY HALF (JP + reviewer 2026-07-30, from the Ezion-Geber screenshot):
  adjacent PN tokens that bind to the SAME entity should render as ONE clickable
  chip — today "Ezion" + "Geber" are two chips serving one card. One entity =
  one clickable thing. Belongs to this lane (same shape as the batch-3 slots);
  fold into the evidence pass's design.**

## Status
PARKED — design pass waits for JP to raise it. Related-but-separate:
same-verse same-name multi (~118 slots) = word-position binding lane.
