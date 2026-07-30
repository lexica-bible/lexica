# DRILL SHEET — witness-divergence design pass (~370 slots)

Status: **REVIEWER VERDICT LANDED 2026-07-30** — (1) doctrine answered once on Lane A,
which ships FIRST and ALONE; lane order = doctrine → A → B-rulings-infrastructure →
B → C. (2) kind='witness' as a first-class bind type (not a flag) — keeps evidence
classes partitioned, wording keys off type, gate gains a free invariant (ruled and
witness rows can never silently trade places). (3) Lane-B spelling equivalences are
HAND RULINGS — they live in pn_hand_rulings.tsv with a new evidence-class tag
(spelling-equiv), NOT in the witness file; one file governs "JP ruled this."
CONDITION: the exact card sentence for witness binds is drafted in the Lane A ticket
and JP approves it BEFORE Lane A builds.

## LANE A SHIPPED 2026-07-30 — 9 binds live, after a caught-and-corrected wrong-referent ship
Final: kind='witness' binds at Job 1:13/16/17/18 (Job@Job.1.1-Jas) + Gen 36:20/24/29,
1Ch 1:38/40 (Zibeon@Gen.36.2-1Ch), each carrying the JP-approved card sentence.
**INCIDENT (owned):** the first Lane A ship (20 binds) used the sole-SPELLING test as if
it established the referent; 11 binds pointed at the WRONG person (sarah Num 26:46 =
Serah Asher's daughter, koz = Hakkoz, shuah = Shua/Shuhah, hadar = Hadad-son-of-Ishmael,
joanna = Joanan, sheva = Seraiah, job Gen 46:13 = Jashub, michal 2Sa 21:8 = contested
Merab reading). Caught by the post-swap curl (Sarah), confirmed by a full referent screen,
corrected same session (demoted lane X, gate extended: demoted keys FORBIDDEN as witness).
**STANDING RULE EARNED: lane-A eligibility requires the REFERENT screen — no other TIPNR
entity of ANY spelling may cover the verse. Sole-spelling proves candidacy, never identity.**
The 11 demoted slots are lane-B-shape spelling collisions; each needs a hand ruling
(spelling-equiv, TSV lane) to its TRUE referent. Malchiah Ezr 10:25 separately demoted
(two Malchiahs in the verse — word-position lane).

## PRODUCTION-MATCHER CENSUS (step 1, done 2026-07-30)
Re-run with the binder's own map (er.parse_tipnr + er.build_indexes on the pinned
TIPNR). Frozen artifact: `docs/tickets/witness_census_lanes.txt` (370 slots).
**Lane A: 10 names / 21 slots** (zibeon 5, job 5, shuah 3, koz 2, sheva/michal/
malchiah/hadar/joanna/sarah 1 each — the production map moved sheva + hadar IN vs
the proxy: hadar is an attested Hadad spelling; juda moved OUT to Lane B).
**Lane B: 16 names / 46 slots** (shechaniah 9, michaiah 7, bashemath 6, micha 4…).
**Lane C: 95 names / 303 slots** (jesus 38, judah 21, jacob 16, elijah 15…).

## LANE A TICKET (build-ready once JP approves the card sentence)
The 21 slots, each: the name has exactly ONE TIPNR entity anywhere in the corpus,
ABP's own Greek prints the name at the verse (italic=0, certified in the class-3
itemization), and that entity's reference list lacks the verse only because its
base text differs. Bind = the sole entity, kind='witness'.
- Evidence file: the frozen Lane-A rows of witness_census_lanes.txt (name/ref/
  entity), consumed by the binder like the rulings TSV; re-lands on rebuild.
- Gate: gate_pn_rulings pattern — delta pinned to the Lane-A rows, control first,
  entities/refs byte-stable, zero HOT replacements, served spot-checks incl. one
  unchanged ruled bind.
- **CARD SENTENCE — JP-APPROVED VERBATIM 2026-07-30 (both drafts REJECTED for
  asserting an unproven manuscript cause; approved wording claims only bound
  facts):** "ABP's Greek text reads {Name} here. The reference index does not
  list this name at this verse; the identification follows ABP's reading."
  Upgrade path: a per-name ruling with attested witness evidence (e.g. LXX-vs-MT)
  may carry a stronger sentence; the class default stays at what is proven.
  Placement: muted meta line on the .pnbound card above the badge, both variants
  (thin defers to full so the sentence always shows); no new visual treatment.
Parent: TICKET_supplied_subject_binds.md. Census: class3_witness_slots.txt minus the
22 batch-3 adjacency binds = 370 slots / 121 names.

## The doctrine question (carried from the ticket, now to be answered at scale)
When ABP's own Greek attests a name at a verse that TIPNR's reference base (Hebrew MT /
critical NT) doesn't list there, does the primary text's reading suffice to bind,
given the referent is contextually unambiguous? Precedents already answered YES at
small scale, witness-flagged: Cainan (5 rows), abimelech Psa 34:0, and batch-1's
17 artaxerxes rows (lxx-naming class). The design pass decides the MECHANISM that
says yes ~300 more times without ~300 hand rulings.

## Lane sizing (LOCAL PROXY — pre-registered caveat)
Sized 2026-07-30 by tokenizing pinned-TIPNR aliases; this splits compound aliases
into tokens, so multi-owner counts are INFLATED (joseph "14 owners" includes any
compound alias containing the token). **Drill step 1 re-runs this census with the
production binder's own spelling map (build_entity_binding), not this proxy — the
proxy orders the lanes, it does not adjudicate any slot.**

- **Lane A — sole-owner names: 9 names / 21 slots** (job 5, zibeon 5, shuah 3,
  juda 2, koz 2, joanna/malchiah/michal/sarah 1 each). Exactly one TIPNR entity
  bears the name; if the doctrine says yes, the bind is mechanical. Confidence-arc
  tripwire honored: sole-referent = exact/compact matching only, never fuzzy.
- **Lane B — spelling-gap names: 15 names / 44 slots** (shechaniah 9, michaiah 7,
  bashemath 6, micha 4, jonas 3, maachah 3, …). ZERO TIPNR entity carries the ABP
  spelling — same class as jabish/jabesh: KJV-style spelling variance, the entity
  exists under another spelling. Needs a per-name spelling equivalence ruling
  BEFORE any bind; each equivalence is citable (both spellings of one Hebrew name).
- **Lane C — multi-owner names: 97 names / 305 slots** (jesus 38, judah 21,
  jacob 16, elijah 15, gilead 13, joseph 11, pharaoh 9, …). Witness question AND
  referent question stack. Sub-shape worth splitting in step 1: names where all
  slots sit in ONE narrative run (elijah = 1Ki 17–19, jacob = Gen 29–48 arc,
  cushi = 2Sa 18 only) vs genuinely scattered. Narrative-run slots have the same
  contextual-unambiguity argument as batch 1's ref-partition class.

## Proposed mechanism (the design-pass subject — for verdict, then JP checkpoint)
A per-slot witness evidence file, consumed by the binder — NOT ~300 TSV hand rows:
1. New repo-versioned evidence file (name/ref/entity/witness-flag/lane/evidence
   line per slot), built by the drill, frozen before apply — same role the TSV
   plays for rulings, but its rows are PRODUCED by the lane rules above and
   audited per-lane rather than hand-written one at a time.
2. Binder consumes it as a new bind kind (proposal: kind='witness') so these rows
   are distinguishable from 'ruled' forever — gate can pin the delta exactly like
   gate_pn_rulings does (control-first inherits).
3. **Card wording (provenance-contract territory, JP approves wording + any visual
   treatment):** a witness-dependent bind must SAY what it rests on — the name is
   read here by the Greek text ABP translates; TIPNR's base text lacks it at this
   verse. Wording proposal drafted in the design pass, not improvised at build.
4. A future Hebrew-parallel view reads the same flag (the TSV's LXX-only flag
   generalized).

## Pre-registered checks (inherit the batch-3 discipline)
- Step-1 census re-run uses production matching; the proxy above is never cited as
  evidence. Full-population, no sampling.
- Every lane's rule gets a control case that must FAIL before its pass counts.
- Gate: new-kind delta pinned to the frozen evidence file; entities/refs tables
  byte-stable; zero HOT replacements without stop-and-look.
- Served spot-checks per lane after reload, plus one unchanged batch-1/2/3 bind.

## Explicitly out of scope
Same-verse same-name multi (~118, word-position lane) · chip-merge display half
(has its own 22-slot candidate list) · jabish consistency fix (recorded in the
ticket) · any prompt/AI change.

## Open for the reviewer
1. Does the doctrine answer generalize to lane C, or does lane C wait for
   per-name evidence (narrative-run argument) while A/B ship first?
2. Is kind='witness' the right shape vs a flag column on existing kinds?
   (New field either way = JP checkpoint before landing.)
3. Lane B: is a per-name spelling-equivalence ruling sufficient evidence, and
   where does it live so a rebuild re-lands it?
