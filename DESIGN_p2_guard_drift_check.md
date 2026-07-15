# DESIGN — probe-2 guard fixture drift check, chained into the rebuild

**2026-07-14. Design note only, ZERO code, ZERO spend.** JP ruling: **option (b), MODIFIED —
no hand-run step, no memory dependency. Chained into the `/rebuild-words` flow so it runs
automatically at the rebuild event.** *"JP will not run a separate command from memory; if the
check is not automatic at the rebuild event, it does not exist."*

## The claim being protected

`tests/test_v11_probes.py:480` hard-codes the guard fixture, and its comment (`:477-479`)
states the claim:

> *"korah/solomon/laban/jesus/peter ARE words-table name-marked heads; votive/active/applying
> are NOT"*

**VERIFIED ONCE, against a live control run on PA, on 2026-07-12.** Never re-checked. The same
claim sits in a comment at `build_lexica_def.py:2735-2736`, same date — **two copies, one
verification.** The test cannot re-check it: CI runs without `bible.db` by reviewer-ruled
fixture condition (`test_v11_probes.py:6`). **So the check can only live PA-side.**

## Where it hooks — `import_tipnr.py`, and this is verified, not chosen by taste

**`import_tipnr.py` is the ONLY writer of `is_pn=1`** — verified this session:
- `:610` — `UPDATE words SET strongs_base=?, is_pn=1 WHERE rowid=?`
- `:615` — `UPDATE words SET is_pn=1 WHERE strongs_base='*'`
- The build **CLEARS** `is_pn` (`build_words_from_abp.py:1635`: *"This rebuild CLEARED is_pn /
  proper-noun Strong's, so import_tipnr is required"*). Everything else in `scripts/` only READS
  `is_pn`.

**So the single writer of the marking is the single hook.** A check at the end of `import_tipnr`
fires at exactly the event that can move the claim — and it fires whether import_tipnr is reached
via `finish_rebuild.sh` step 3 **or run standalone**, which CLAUDE.md mandates after ANY words
rebuild. **Hooking `finish_rebuild.sh` instead would MISS the standalone run.** No new command,
nothing for JP to remember: the ruling is satisfied structurally.

## ⚠ THE BLOCKER — `finish_rebuild.sh` SWALLOWS EVERY STEP'S FAILURE TODAY

**This is the note's main finding, and JP's own ruling cannot be met without facing it.**

`scripts/finish_rebuild.sh:15` reads `set -uo pipefail` — **no `-e`** — and its `run()` helper
(`:19`) never checks an exit code:

```bash
set -uo pipefail
run() { echo; echo "── $* ──"; "$@"; }
```

**Consequence: if ANY step in the tail chain fails — including `import_tipnr` itself, TODAY,
before this ticket exists — the chain continues and prints `== finish_rebuild done ==`.** A
failure scrolls past under ten more steps.

**That is log-and-continue, which JP's ruling forbids** (*"Failure must block or visibly flag,
not log-and-continue — silent-fallback rule applies"*). **So a check that merely exits non-zero
inside `import_tipnr` would be swallowed and would NOT satisfy the ruling.** Loudness at the
check is necessary and not sufficient.

**It is also the same defect class this session just closed one layer down** — a failure
degrading into a green-looking finish. The probe-2 guard failed silently; `finish_rebuild.sh`
lets *any* step fail silently. **Bigger than this ticket, and load-bearing for it.**

**RECOMMENDATION (needs JP's gate — it changes a rebuild script's control flow):** do **not**
add `set -e`. The no-`-e` design looks deliberate — each patch is independently targeted and
re-runnable, and aborting mid-chain could leave a half-patched copy that is harder to reason
about than a fully-patched one with a named failure. Instead: **`run()` records failed steps,
and the closing banner REFUSES to say "done"** — it names every failed step and exits non-zero.
The chain still completes; the *verdict* stops lying. This fixes the whole chain, not just this
check, and preserves the deliberate design.

**If JP prefers the minimal change**, the fallback is a check whose banner is the LAST thing
`finish_rebuild.sh` prints — but that is weaker (it only covers this one check, and leaves every
other step's failure still swallowed), and it does not survive a standalone `import_tipnr` run.

## What it compares

Two halves, both from the fixture's own claim:

- **MUST be name-marked:** `korah`, `solomon`, `laban`, `jesus`, `peter` — present in
  `SELECT DISTINCT lower(english_head) FROM words WHERE is_pn=1 AND english_head != ''`, i.e.
  **the production guard's own read** (`build_lexica_def.py:2745-2746`), reused, never a copy.
- **MUST NOT be name-marked:** `votive`, `active`, `applying`. **Note: this half is currently
  comment-only** — the test uses those tokens as demotion candidates but never asserts the corpus
  lacks them. The check would make the claim testable for the first time.

**Cite the verification date (2026-07-12) in the check's own output**, so a reader sees how old
the baseline is rather than remembering it — the reviewer's condition, and the reason staleness
becomes computable.

## The single-source problem — REAL, and it needs a ruling

**`KNOWN` is a local variable inside `main()` (`test_v11_probes.py:480`) — it is NOT importable.**
So a PA check cannot read it. Writing the eight words into the check script as well would create
a **third** copy of a claim that already has two and one verification — **the exact #71 class this
ticket exists to close.** Fixing drift by adding a copy would be self-defeating.

**RECOMMENDATION: the claim moves to a module-level constant in the new check script
(`scripts/check_p2_guard_fixture.py`), and `test_v11_probes.py` IMPORTS it.** One copy, two
readers. Direction is right: the test already does `sys.path.insert(0, …/scripts)` (`:25`), so a
test importing from `scripts/` is the established pattern — whereas a production script importing
from `tests/` would be backwards. The comment at `build_lexica_def.py:2735-2736` then points at
the constant instead of restating the words.

**CHECKPOINT FLAGGED:** a module-level constant holding the claim is arguably a **new structure**
→ `feedback_new_fields_checkpoint` (*"New dict/field/table pauses for OK BEFORE landing"*). It is
a test-fixture hoist rather than a new production field, so it may fall under *"editing an
existing structure = fine"*. **Named here so it is JP's call, not discovered mid-build.**

## What LOUD looks like — reusing a ruled convention

**No new tier.** The rebuild checklist already has the convention: a named gate with an expected
value and a **don't-swap** consequence — e.g. `audit_split_flip.py` *"MUST be 0 … if non-zero the
`_split_compounds` source-phrase-order fix regressed, **don't swap**"* (`/rebuild-words` step 6).

The check speaks the same way: **a named, expected-value gate whose failure says DON'T SWAP.**

**It must NOT fail the rebuild.** A mismatch does **not** mean the rebuild is broken — it may
mean the corpus legitimately changed and **the test fixture is now lying**. Blocking the *swap*
is right; failing the *build* is disproportionate. The message should say what to do: **the words
rebuild changed the name-marking the probe-2 test fixture depends on — decide whether the change
is legitimate, update the fixture from THIS run's output, and re-verify before swapping.** (That
"update from the emitted output" wording is the #71 rule itself: a fixture string is pasted from
emitted output, never retyped.)

**Silence on success.** A healthy run says one quiet confirmation line at most — a loud banner on
every good rebuild trains the eye to skip it, which is how the next real one gets missed.

## Build order (when its gate clears)

1. **Red-first**, and it must fire ALONE (**#75** — a first-firing assert can mask a ruled
   control): prove the check catches a name that lost its marking AND a non-name that gained one.
   Both directions; the losing-a-marking direction is the dangerous one (production demotes the
   name, its warn is eaten, the test still says green).
2. The check script + the constant hoist + the test importing it.
3. The `import_tipnr` hook.
4. `finish_rebuild.sh`'s verdict fix — **its own gate; show the code first.**
5. `/rebuild-words` doc updated to name the new gate in step 3's description.
6. **Paste-ready command for JP only after the gate clears.** JP runs all PA commands.

## Out of scope — stated so silence does not read as covered

The `is_pn` **incompleteness** root stays **CLOSED (#72)**. This check asks only *"does the corpus
still match what the fixture claims?"* — **not** *"is the corpus right?"* A green check does not
make `is_pn` a complete name index and must never be pitched as if it did.
