# DESIGN — G236 part 2: does a mechanism exist?

**2026-07-14. Zero spend, zero code. Enumeration + pre-registered criterion.**
Reviewer-directed (three asks answered, ruling pasted by JP). Nothing here proposes a
mechanism — this note establishes whether one *can* exist, and commits the test to disk
BEFORE the deciding evidence is opened.

## The task

Move G236's five confirmed sense-1 misfiles — **Ezr 6:11 · Ezr 6:12 · Neh 9:26 · Isa 24:5 ·
Act 6:14** — into the ruled narrow third home (*"alter/violate a standing norm"*), inside
four constraints:

1. A floor is **ten model draws voting** (`lexica_agreement.py:733`, `--runs` default 10).
2. The **V9 prompt is FROZEN** — it is the prompt of record for the JP-ruled-FINAL 7/15.
3. **Floors draw UNHINTED** by design.
4. **No roster hand-carve.**

## The enumeration — 12 levers, 11 dead

**Dead on the machinery:**

1. **Re-run the floor on V9.** Same prompt, same verses, same vote. The handoff's own logic
   and it holds: V9 adds only coverage + verbatim-quote discipline (`lexica_agreement.py:369`)
   and does not dictate the sense inventory. Ten calls to buy the misfile back.
2. **Raise the draw count.** Same, dearer.
3. **Change the prompt.** V9 frozen (constraint 2). Un-freezing puts the untouchable 7/15's
   basis in play.
4. **Hint the floor.** Blocked twice: floors draw unhinted, AND hints may never name a
   preferred sense wording, sense count, or carve (`draw_hints.py:8-11`). A third home is a
   carve.
5. **Stable-jobs hint (`--structure-hint`).** G236's `jobs` list is empty. Inventing one is
   hand-carving renamed. The channel names jobs, not carves.
6. **V10 coverage repair.** **Structurally barred.** Its own instruction reads: integrate the
   absentees *"WITHOUT changing the sense structure or the sense headlines"*
   (`build_lexica_def.py:1779`). It cannot create a third home. **This is why "a repair" was
   the wrong word for part 2** — now verified against the instruction text, not assumed.
7. **V11.2 quote repair.** Touches only wording inside quotation marks. Further still.
8. **Roster `excluded` channel.** Would drop the five from every sense — a coverage defect
   against V9's own *"COVERAGE IS TOTAL"* (`lexica_agreement.py:370`). Illegal.
9. **Roster `float` channel.** *"may sit in either group; do not force a split"* — moves a
   verse between **existing** groups. Cannot create a third. Doesn't reach.
10. **Change the fed verses (`--force-verse`).** Evidence-shopping to move a vote. Rejected on
    principle; the 23 are already fed.

**11. Roster revision — STANDING (see below).**

**12. Re-aggregate the existing floor under a non-modal counting rule — DEAD, and it is the
most instructive death on the list.** Reviewer-raised; disposed of explicitly rather than left
unlisted.

- **In form it is a duplicate.** The roster *is* the aggregation output. Re-scoring the floor
  and writing the result into the roster is lever 11 reached by a different road.
- **In substance it is worse than any of the ten.** Lever 11's entire legal defense is *"I read
  what the floor already settled."* Lever 12 changes the counting rule until the floor returns
  the answer the ruled direction wants, then claims the roster's defense for the result. That
  is not reading a consensus; it is manufacturing one, and it retro-fits the floor's meaning
  after the fact.
- **Consequence for lever 11 — this is the load-bearing point.** If the third home is visible
  ONLY by counting the vote differently than the roster's own rule counts it, then reading it
  back **is lever 12** and is dead. Lever 11 survives only if the third home is visible under
  the roster's **existing** rule. The criterion below enforces exactly that line.

## Lever 11 — roster revision — and where the reasoning was wrong

The roster clears all four constraints, each leg byte-checked:

- **Prompt frozen?** Survives. The roster rides in the **user message**, not the prompt —
  *"frozen V9 prompt untouched"* (`build_lexica_def.py:511-517`), injection at `594-597`.
- **Floors unhinted?** Doesn't bite. `--roster` anchors the **ship draw**
  (`build_lexica_def.py:3125`), not the floor. The floor is never re-run. Cost is **one draw**,
  not ten.
- **Hand-carve banned?** The handoff compressed this into an inversion. The real rule: the
  hand-carve ban *"governs hints/jobs ONLY"*; a roster **is** allowed to fix how many senses
  and which verses group, *"because it is not hand-invented — it is the floor's OWN
  repeated-review consensus"* (`draw_hints.py:15-26`).

**The gap in CC's first reading (reviewer-caught, material).** CC framed the deciding question
as *"is the third home in the floor?"* — i.e. **floor-derived**. That is not the roster's
defense. The roster's defense is **floor-CONSENSUS**. A placement appearing in 1 of 10 draws is
in the floor and is not consensus by any reading; reading it back would be minority-shopping in
the roster's clothes — hand-carving one layer removed. The question as CC first put it was
under-specified in the direction of convenience.

## THE CRITERION — pre-registered, banked BEFORE the floor is opened

Red-first analog for an evidence read. A criterion written after seeing the data is no
criterion. All four legs must hold.

### C1 — COUNT. The floor's modal per-draw sense count must be ≥ 3.

The roster class fixes count as *"the modal per-draw sense count"* (`draw_hints.py:20`). That is
the rule the roster's legality rests on and it is not CC's to re-pick — re-picking it **is lever
12**. If the modal count is 2, then no legal roster off this floor carries a third group, no
matter what any minority draw shows, and the mechanism does not exist.

**Live and genuinely unresolved.** G236's roster carries `"count": 2` (`draw_hints.py:149`), but
**its provenance says "modal homes" and never says "modal count"** (`draw_hints.py:157`) —
whereas G1390's says *"+ modal count; count-anchored"* (`:75`) and G227's says *"+ modal count;
membership-anchored"* (`:127`). G236 is the one roster of the three that does not record its
count as modal. So whether 2 is this floor's modal count is **not established by any byte CC has
read.** That is what the read must settle first.

**The erasure case this leg exists to catch:** if a substantial share of draws produced a
3-sense structure with a coherent third home, and the modal *count* collapsed to 2, that third
home was **rounded away by the count collapse, not outvoted per verse.** That is the only route
by which the third home could be floor-consensus and still be absent from the roster. If the
modal count is 2, that route is closed.

### C2 — SHARED HOME. The non-group-1 placements must converge on ONE home.

Not five verses scattered into five idiosyncratic homes. The reviewer's argument, and the
machinery agrees: homes are set by the floor's *"per-verse company"* (`draw_hints.py:20-21`).
Company means the verses that travel together. **Scatter has no company, so it cannot produce a
home** — it is noise, not an unread consensus.

### C3 — STRENGTH. The shared third home must carry the verse in ≥ 5 of 10 draws.

Justified from bands the machinery itself names, not from what would be convenient:

| Band | The machinery's own words | Source |
|---|---|---|
| ~2/10 | *"poles blur ~2/10 even under clean anchors"* — the named **noise** band | `draw_hints.py:65` |
| 5/5 | *"floor 5/5 true seam"* — the named line for a **genuine split** | `draw_hints.py:155` |
| 7-8/10 | what *"the floor homes X"* means (Gal 4:20 substitution 7-8/10; Isa 42:3 *"cond 7/10 + own company … at 7-8/10"*) | `draw_hints.py:166`, `:123` |

**5/10 is the machinery's own boundary between noise and a real split** — G236's own Jer 13:23
seam is banked at exactly 5/5. At or under ~2/10 a placement is indistinguishable from the
residual wobble the rig exists to measure (*"the residual wobble is the MEDIUM, not a tuning
bug"*). Below the seam line, reading a placement back is minority-shopping. **The number is
fixed here, before the data, and does not move afterward.**

### C4 — PER-VERSE, not the set.

The roster's homes are per-verse (`draw_hints.py:20-21`). A set-level test would let a strong
verse drag a weak one across — which is hand-carving. If the criterion passes for 3 of the 5 and
fails for 2, **only 3 move; the other 2 stay parked as a named open gap.** Part 1 established
sense 1 stays coherent once the misfiles come out; it did not establish that they travel
together.

## Predicted outcome — stated before the read

**C1 probably kills it.** `"count": 2` in the roster suggests the modal count is 2, which would
close the only route to a legal third home off this floor. It is not proven — G236's provenance
uniquely omits "modal count" — which is precisely why the read is worth its (zero) cost rather
than being settled by assumption in either direction.

**Both branches are bankable:**

- **Criterion met** → the roster revision is floor-consensus, legal under the existing rule,
  prompt untouched, floor untouched. Cost: **one ship draw.** Part 3's red-first fixture follows.
- **Criterion not met** → **the mechanism does not exist at current floor evidence.** G236 stays
  parked. That is an answer to the open question, not a failure, and it closes the standing gate
  on every G236 spend.

## The deciding read

`agreement_G236_v9_20260712-165959.json` — named in the roster, **PA-only, not in the repo**
(CC confirmed by search this session). **CC has not read it. No claim is made about its
contents.**

Cost: **zero.** `--from-json` re-renders a saved run free, no model call
(`lexica_agreement.py:738`). Gate order per the reviewer's ruling: **(a) this note lands →
(b) the command is drafted paste-ready for JP.** JP runs it; the command gate is his.

The read must answer, in this order: **the modal per-draw sense count** (C1) → **whether the
non-group-1 placements share a home** (C2) → **the per-verse strength of that home** (C3, C4).

## Citations — verified by CC this session, on CC's own repo reads

Repo reads are CC's job; the receipt rule governs receipts, not evidence. Recorded so a future
session knows whose eyes. Every line below was opened and read, not recalled.

- `lexica_agreement.py:733` — `--runs` default 10. **Confirmed verbatim.**
- `lexica_agreement.py:369` — V9's two added lines are coverage + verbatim quotes, with **no
  sense-inventory language.** **Confirmed** — the handoff is byte-true here.
- `draw_hints.py:15-26` — **FALSIFIES** the handoff's *"hand-carve the roster ⇒ BANNED"*.
- `draw_hints.py:157` vs `:75` / `:127` — G236's provenance says "modal homes", **never "modal
  count"**; the other two rosters say "modal count". The C1 gap.
- `build_lexica_def.py:511-539, 594-597, 3125, 3190` — roster rides the user message, anchors
  the **ship** draw. **FALSIFIES** the *"~10× a redraw"* pricing.
- `build_lexica_def.py:1779` — repair instruction forbids structure/headline change. Confirms
  repair is structurally barred from creating a home.

## Errors logged this session

- **CC:** framed the deciding question as "floor-derived" when the roster's defense is
  "floor-consensus" — under-specified toward convenience, reviewer-caught before any read.
  Banked as the reason the criterion is pre-registered rather than written after the data.
- **The handoff:** two SPEND BOARD lines falsified by the files they cite (corrected in place,
  same commit). Neither rescues a spend; both change what part 2 **is**.
