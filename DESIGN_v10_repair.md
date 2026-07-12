# V10 DESIGN — the coverage REPAIR PASS

Drafted at the batch-5 run-session-2 pivot (2026-07-12, commit 169ac3a). Rulings applied
under JP's standing delegation (2026-07-12); reviewer verification per section is the
gate before any code lands. **Nothing here touches the frozen V9 verse prompt
(`lexica:f27027b50754`). The repair prompt is a SEPARATE, versioned instruction block.**

## The problem (evidence base, all banked)
Three one-or-two-verse-margin parks in one session, every kill coverage-alone at the
machine, no other defect surviving adjudication:
- G227 ἀληθής: 34 → 38 → 38 of 39 (final absentee Joh 21:24, convergent 2/3)
- G162 αἰχμαλωτεύω: 36 → 33 → 35 of 36 (final absentee Job 1:15, twin cited beside it)
- G1390 δόμα: 36 → 37 → 37 of 38 (2Sa 19:42 ×2 then cited in d3 while Deu 23:23 dropped)
The squeeze RELOCATES, never resolves: 10 distinct absentees across the nine draws, one
convergence pair per word at most. Hints cannot fix it (no nameable trap); re-rolls do
not converge (each draw rolls fresh victims). The gate already NAMES the absentees at
refusal and we throw that information away.

## The mechanism
On a coverage-gate failure at dry-run/apply, ONE bounded repair call:
1. Input: the draw's own raw card text + the gate's named absentee refs + each
   absentee's verse text (same feed shape as the original occurrences).
2. Repair prompt (draft wording, JP-ruled under delegation before landing):
   > The definition below is complete except that these fed occurrences are not yet
   > cited under a sense: {refs, with verse texts}. Integrate each into the sense where
   > its text belongs — add citations (and the minimum prose needed to house them)
   > WITHOUT changing the sense structure, removing any existing citation, or altering
   > any existing quotation. Return the full corrected definition.
3. The repaired raw REPLACES the cached draw's raw and re-runs EVERYTHING fresh:
   splitter, citation gate, coverage gate, #30 floor-diff, checker warns. No gate sees
   it as anything but a new card.
4. Cap: TWO repair rounds per draw, then the draw is dead (a card that can't integrate
   its absentees in two tries has a real problem).
5. Draw record stamps: `repaired: [refs]`, `repair_rounds: N`, `repair_prompt_ver`
   (hash, same scheme as the hint signature). Console prints a LOUD
   "REPAIR PASS round N — integrating: {refs}" line. The card's audit stores the same.
   A repaired ship is visibly repaired everywhere the draw record is read.

## Gate story (why this is NOT the edited-draw class)
- fix_lexica_raw = a HUMAN writes bytes into a stored entry (allowed only inside the
  τόπος/ἔργον artifact boundary).
- The edited-draw refusal = a human hand-editing a CACHED DRAW, which skips
  review-what-ships. Still refused; nothing changes there.
- The repair pass = the MODEL writes, every machine gate re-runs from zero, and the
  human adjudication + hand-checks (quotes, echo scan) happen on the FINAL card before
  apply, exactly as today. Review-what-ships intact; the only change is that the
  re-roll is targeted instead of blind.

## Adjudication rules for repaired draws (pre-set, so reads are against stated criteria)
- The full hand-check battery runs on the REPAIRED card (quotes crux-weight where the
  word's history says so; hint-echo scan; REPAIR-echo scan — "as noted above, these
  references..."-style machinery language is the G2805 leak class).
- A repair that changes anything beyond housing the absentees (sense count moved,
  existing citation dropped, existing quote reworded) = the draw is DEAD, not
  re-repaired. The splitter diff makes this checkable: sense_headlines and the
  pre-repair citation set must be preserved superset-style.
- 3-defect budget: a repaired-then-shipped draw counts as ONE draw. A draw dead after
  cap-out counts as one defect draw.
- Scoreboard: a repaired hinted ship stays superscript-h; the record shows the repair
  stamp. No separate marker tier (the draw record carries the detail).

## Controls (audit-tools-must-fail)
- Must-fail: a fixture from G1390 d3's cached raw (Deu 23:23 absent) — the repair path
  must FIRE, produce a card that cites Deu 23:23, and the re-run gates must PASS it,
  with the repair stamp present. Plus a no-op control: a full-coverage card must NOT
  trigger repair. Plus a structure-guard control: a mock repair output that drops a
  sense must be REFUSED. All in BOTH CI lists.
- The structure guard is the detector that proves rule 2 above works; red-first on the
  mock before any zero is trusted.

## What V10 adoption means
- The parked words' retry-trigger ("next engine/prompt change") FIRES on the repair
  pass landing + acceptance: G227, G162, G1390 re-enter on fresh unhinted floors is NOT
  required (mechanism change, not prompt change — their V9 floors + banked pre-clears
  stay valid; the draw signature moves only when repair fires). Reviewer to verify this
  reading against the floor-staleness rule before the first retry; if the signature
  math says otherwise, fresh floors, no argument.
- G236 does NOT retry on V10 (its kills were quote/placement, on the record).
- The stamp: repaired cards keep `lexica:f27027b50754` (the verse prompt is unchanged);
  the repair prompt version lives in the draw record + entry audit. "V10" names the
  MECHANISM version, not a new verse-prompt stamp.

## Build order
1. This doc → reviewer full read.
2. Repair-prompt wording ruled (delegation; wording above is the draft).
3. Code: build_lexica_def.py repair hook (shown in full before commit) + the three
   controls red-first.
4. CI lists both updated; neighbor tests green.
5. Retry session: G1390 first (freshest evidence, its d3 was one verse out), then G227,
   then G162 — each through the full per-word gate order.
