# TICKET (for JP's call) — PA-side drift check for the probe-2 guard fixture

**Written up, NOT designed and NOT built** — reviewer-ruled 2026-07-14: this one lives on PA,
touches `health_check.py`'s mail behavior, and JP runs all PA. **His decision, not delegated.**
Zero spend either way.

## The claim that is going stale

`tests/test_v11_probes.py:477-480` carries this, in its own comment:

> *"Guard fixture set mirrors the live control run on PA: korah/solomon/laban/jesus/peter ARE
> words-table name-marked heads; votive/active/applying are NOT (raw output in the session
> record)."*

```python
KNOWN = frozenset({"korah", "solomon", "laban", "jesus", "peter"})
```

**VERIFIED ONCE, AGAINST A LIVE CONTROL RUN ON PA, ON 2026-07-12.** *(Date cited so staleness is
computable later rather than remembered — reviewer condition. The same claim is also stated at
`build_lexica_def.py:2735-2736`, carrying the same date. Two copies, one verification.)*

**Nothing has re-checked it since, and nothing can.** The test cannot reach the corpus: CI runs
without `bible.db` by reviewer-ruled fixture condition (`test_v11_probes.py:6`). So this claim
about the live corpus can only ever be re-checked **on PA**.

## Why it matters — and why it is NOT urgent

**It is not a correctness bug today.** The fixture's job is to test the demotion boundary logic
with controlled input, which it does correctly regardless of what PA's corpus holds. **Nothing
is wrong right now.**

**What drift would cost:** if those eight words' name-marking changes on PA, the test keeps
passing on the frozen set while production's guard behaves differently. The test would be
asserting a world that no longer exists — **quietly**. The dangerous direction is a name losing
its marking: production's guard drops it, a real name at a sentence start gets demoted, and its
warn is **eaten** — while the test, holding the name hard-coded, still says green.

**Honest scale:** this is a slow, unlikely drift (a words rebuild or a TIPNR re-import would be
the mover), and its blast radius is one probe's demotion behavior. **It sits on the shelf for a
reason.** It is written up because #71's whole point is that a fixture string is a claim, and
this claim has one verification and no expiry.

## What a check would do (shape only — NOT a design)

Re-read the corpus on PA and compare against the eight words the fixture asserts: the five that
must be name-marked, and the three (`votive`, `active`, `applying`) that must not be. Report a
mismatch. Two plausible homes:

- **Fold into the nightly `health_check.py`** — it already has database access and already mails.
  Automatic, catches drift the day it happens. **Cost: it changes mail behavior, and a new
  nightly alert has to be worth waking up for.**
- **A hand-run script JP runs after any words rebuild.** No mail, no nightly noise, but it is a
  remembered step — and a remembered step is what this ticket is complaining about.

**No recommendation is made here.** Both have a real cost and the choice is JP's.

## JP's call

1. **Build the nightly check** (accepting one more thing that can mail you), or
2. **Hand-run script**, tied to the `/rebuild-words` procedure so it is a step, not a memory, or
3. **Leave it** — accept the fixture as a dated snapshot, and re-verify only if probe 2's
   demotion is ever suspected. **This is a legitimate answer**; the risk is small and slow.

**Do NOT let this be pitched as fixing `is_pn` incompleteness — that is CLOSED as #72.** A
current fixture and an incomplete name index are different problems; this check would only tell
us the fixture still matches the corpus, not that the corpus is right.

**Related:** `DESIGN_p2_guard_loudness.md` (the adjacent ticket — making the guard's *failure*
visible; different problem, same seam) · AUDIT "#71 KNOWN-SET TICKET" · ENGINE_LESSONS #71/#72.
