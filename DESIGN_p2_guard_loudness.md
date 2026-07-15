# DESIGN — probe-2 guard: make the silent degrade visible

**2026-07-14. Design note only, ZERO code, ZERO spend.** Reviewer-ordered before any build:
per #73, a detector-side change must answer *what is this for* before it exists. Follows the
#71 close-out (`3899ed2`), which found the guard's loader untested and its only exercise a
silent failure running green.

## The three questions, answered from the bytes

### 1. What should the loud path distinguish — guard-absent vs guard-error?

**THE DISTINCTION COLLAPSES AT THIS LAYER. There is only guard-ERROR.** This is the note's
main finding and it shrinks the ticket.

**Guard-absent is ALREADY loud, one layer up, and has been all along.** When there is no
connection, `validate_entry` prints *"V11 prose probes NOT RUN … verbatim-quote gate,
named-subject check, identity scanner all UNCHECKED"* (`build_lexica_def.py:2876-2879`) and
**the probes never run at all** — `_p2_corpus_names` is not reached. The guard-load call sits
inside the `elif raw:` branch (`:2880`, `:2892`), i.e. it only ever runs when a connection
exists.

**Therefore, in production, a `None` from `_p2_corpus_names` can ONLY mean the read failed
against a live connection** (`:2748-2749`, `except Exception → None`). There is no legitimate
production path to a `None` return. **One state to make loud, not two.**

**Keep the two `None`s separate — they are not the same fact:**
- `probe2_names(known_names=None)` — a **legitimate parameter contract**: *"None disables
  sentence-starter demotion entirely"* (`:2710-2711`). Tests 2a-2e rely on it. **Do not touch.**
- `_p2_corpus_names(conn) → None` — **always an error.** This is the one that must speak.

The bug is that the loader's error and the parameter's legitimate value are **the same byte**,
so the error arrives at `probe2_names` wearing the contract's clothes and is handled as if it
were a choice. **That is the whole defect in one line.**

### 2. What should it fail toward?

**Unchanged: toward the human — no demotion, therefore MORE warns.** This is already ruled
(*"the guard degrading must always fail toward the human, never silently widen demotion"*,
`:2736-2737`) and it is already correct. **This ticket adds VISIBILITY ONLY; it must not touch
the failure direction.**

**Why that boundary is load-bearing.** The safe direction is over-firing. The dangerous
direction is a guard that loads *partially* or *wrongly* and **eats real warns** — silent, and
in the direction that loses information. Any change that makes demotion more available in a
degraded state trades a visible nuisance for an invisible miss. **Do not.**

**The live cost of the current silence is NOT the extra warns — it is that the human
adjudicates them blind.** With the guard dead, probe 2 over-fires; a reviewer sees junk warns,
recognises them as the known `is_pn`-incompleteness class (#72), and waves them through — never
learning the guard was not running. **The wrong explanation is already sitting on the shelf,
which is what makes the silence expensive.**

### 3. Gate output or a log line?

**Recommendation: reuse the ruled NOT-RUN convention. Do not invent a fourth loudness tier.**

A guard-load failure means *the demotion check did not run*. The project already has a ruled,
built convention for exactly that shape — **loud on stderr + stored on the audit record +
BLOCKS apply**:
- NOT-RUN items print per line (`:2903-2904`) and are stored (`a["probe2_notrun"]`, `:2898`).
- *"open warns AND probe NOT-RUNs BLOCK apply until adjudicated"* — the V11 ruled gate condition.
- The comment at `:2874` already names the rule: *"No connection = loud NOT RUN, the
  coverage-gate convention."*

So: **a guard-load failure becomes a probe-2 NOT-RUN item.** It reuses production's own
convention, invents no mechanism, and is maximally distinct from a healthy run — which is what
JP's silent-fallback rule demands (*"fallbacks must be visibly distinct from the real thing or
eliminated"*).

**A log line alone is REJECTED.** It dies with the terminal. The draw record would still show
probe-2 results with no trace that demotion was off, so a later reader — the exact reader this
project keeps getting burned by — cannot tell a healthy run from a blind one. **That is
`offline_gate_check.py`'s own ruled output contract: *"a reader of this REPORT must see what
the report does not cover. Silence reads as covered — #69(i)"* (`:139-141`).** The same
argument applies to the audit record, which is the durable report.

**Blocking is right, not aggressive.** A guard-load failure against a real `bible.db` should be
impossible; if it happens, something is badly wrong and stopping is the correct response. It
also cannot bite in normal use — a healthy corpus never takes this path.

**The second caller must not be forgotten:** `offline_gate_check.py:134` passes
`B._p2_corpus_names(conn)` too, and its report enumerates what ran. A guard failure must surface
in **its** output as well, or that report claims coverage it does not have — #69(i) again.

## Where the red-first control already sits, free

**The must-fail fixture exists and is currently passing green.** The `validate_entry` wiring
block (`test_v11_probes.py:605`) runs against an in-memory db with a `verses` table and **no
`words` table** — the exact guard-error state. Today it degrades silently and the test passes.
**When this ships, that block MUST start reporting a NOT-RUN.** If it does not, the change did
not work. **The existing test is the control; it needs no new fixture — it needs to stop being
quiet.** (Its assertions will need updating to acknowledge the NOT-RUN. That update IS the
red-first proof, not a chore.)

## The `id(conn)` cache key — disposed, NOT folded in, NOT dropped

**Verdict: FLAGGED, NO CLAIM. It does not fold in — the loudness fix does not touch the key —
so it stays a separate flag rather than riding along.**

**The mechanism, stated precisely:** `_P2_PN_CACHE` is a module-level dict keyed on `id(conn)`
(`:2738-2743`) that **never evicts**. Python reuses an object's id once that object is freed.
A closed connection's entry therefore stays in the dict forever, and a *new* connection
allocated at the same address would hit the **stale** entry — receiving a guard set built from
a different database. The never-evicting dict does not merely permit the collision; it is what
makes the stale entry survive to be hit.

**Reachability — assessed, not assumed, and NO live bug is claimed.** Both production callers
open ONE connection and are short-lived scripts: `build_lexica_def.py` (per-run) and
`offline_gate_check.py` (opens, uses, `conn.close()` at `:137`). I did **not** trace every
path, and I am not asserting this has ever fired.

**Named revival trigger** (so this is a condition, not a memory): **the day any long-running
process opens and closes multiple connections while calling `validate_entry` or
`_p2_corpus_names` — the Flask app being the obvious candidate — this key becomes a real
hazard and must be re-opened.** At that point the cheap fix is a key that cannot be recycled,
or no cache at all (the read is one indexed pass, not a hot path).

**Why it is not folded in:** bundling an untraced hazard into a ticket that has a clean,
provable scope is how a small fix grows a tail nobody reviews. The loudness change stands on
its own evidence; this does not yet stand on any.

## Scope + checkpoints, named before the build

- **NEW AUDIT FIELD = JP CHECKPOINT.** If the failure is recorded on the audit record under its
  own key rather than folded into the existing `probe2_notrun` list, that is a **new field** and
  pauses for JP's OK before landing (`feedback_new_fields_checkpoint`). **Recommendation: fold
  it into `probe2_notrun`** — it IS a not-run item, the class already blocks apply, and it needs
  no new field, so no checkpoint. Naming it here so the choice is deliberate rather than
  discovered mid-build.
- **RED-FIRST MANDATORY** (reviewer-ruled; it touches gate behavior): the wiring block must be
  shown going from silent-green to reporting the NOT-RUN, and the loader's failure path
  control-broken, before the change is trusted.
- **OUT OF SCOPE, stated so silence does not read as covered:** the failure DIRECTION (stays
  toward the human) · `probe2_names`' `known_names=None` contract (untouched) · the `is_pn`
  incompleteness root (**CLOSED as #72 — this ticket does not re-open it; a loud guard does not
  make `is_pn` complete, and must not be pitched as if it did**).

## What this ticket is NOT for

**It does not improve probe 2's accuracy by one warn.** A loud guard finds no misattribution a
quiet one misses. **Its entire value is that a future reader can tell whether the check ran** —
and, per #73, that is a detector-side change that raises kill probability, not conversion
probability. **It is worth building for exactly one reason: this session watched the silent
path run green and call itself healthy** (`test_v11_probes.py:605`), which is the certification
rule's own failure case wearing a passing test.
