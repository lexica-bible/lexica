# Handoff — /consolidate pass on the memory index

> **SPENT — this opener RAN (2026-07-15). Do not paste it again.** The pass landed: index routed to
> hooks, two-lines-one-file merges folded, `feedback_workflow` split, orphans indexed, one retired
> file deleted (only after its forwarding address was made real). All pointers resolve, zero orphans.
> **It did NOT hit 17.1KB and that target is now RETIRED** — see the ruling below. Two premises in
> this doc turned out to be wrong and are corrected in place; a future consolidation measures its own
> starting state anyway (this doc says so itself), so re-running these numbers would be re-running a
> memory. Kept for the record and for its method, not for reuse.

> **⚠ TARGET RAISED TO 24KB — JP ruling 2026-07-15.** The guards-stay-in-the-index rule (a hook keeps
> the TRIPWIRE; narrative routes down) sets a floor ABOVE 17.1KB, and post-wrap additions breached the
> old number every session — it had stopped telling bloat apart from normal accumulation. Consolidation
> now triggers on APPROACHING 24KB. Routing discipline is unchanged. The threshold of record lives in
> **`.claude/commands/wrap.md`** step 4; this line is the reasoning behind it.

Status at handoff: MEMORY.md is over its read limit and the harness hook has nagged about it for
three sessions.
**BOTH HALVES OF THAT SENTENCE WERE FALSE — corrected 2026-07-15, and the correction is the lesson.**
There is no read limit being breached: MEMORY.md loaded FULLY into context at 20,865 bytes; the only
real cap observed is ~25,000 tokens per read, and the index is ~6,000. And there is no hook: the only
one configured is the communication-style prompt hook. The "nag" is `/wrap`'s own step-4 check, run by
whoever reads `wrap.md` — where the number actually lived, and where a session that only updated THIS
doc would have left it firing forever. Two invented mechanisms, both plausible, both propagated
unchecked into a handoff that then told the next session to trust them. Each of those sessions correctly DECLINED to do it mid-flight — a whole-index
rewrite is not a side quest. This is the deliberate pass, on JP's call, with nothing else in it.

Runs whenever JP calls it. No dependency on the other two handoffs.

Session opener follows. Paste it whole.

---

Lexica — /consolidate pass on the memory index. Deliberate, whole-index, no other work.

New session. JP has called this one — it's the deliberate pass the hook has been nagging about
for three sessions and that every session so far correctly declined to do mid-flight.

Run the /consolidate skill (.claude/commands/consolidate.md). It already defines the procedure —
FOLLOW IT, don't re-derive it here. Scope: MEMORY.md and the memory topic files. In-repo docs are
out of scope this session unless the routing check turns up something stranded, which the skill
covers.

Measured starting state (verify it yourself — don't trust this line):
  MEMORY.md   20,865 bytes / 120 lines / 99 entries      target: RETIRED (was: under 17,100)
  [2026-07-15: the size/line/entry counts here all VERIFIED correct against the real files.
   The TARGET is what didn't hold — see the ruling at the top. Landed at 19,627 with every
   guard kept; the number and the guards ruling could not both be satisfied.]
  topic files 115
  The fat is concentrated, not spread: the ten longest index lines hold ~6,000 chars.
  The worst three — Lexica Dictionary (~1,540), Verify Before You Claim (~837), and the
  settled build-folded-fixes line (~661) — are ~3,000 chars between them. Cutting those to
  one-hook lines gets most of the way to target without touching 96 other entries.

The index's own rule is "one hook per memory; detail in each topic file" — the fat lines broke it
by accreting detail that belongs in their files. So the job is mostly ROUTING, not deletion: move
the detail down, leave a hook.

MUST SURVIVE VERBATIM — these are load-bearing and a consolidation must not "tidy" them:
  · the standing rules in the "Working with the user" block (they're hard rules JP has repeated;
    wording matters)
  · every hard lock and key of record — the grounded-naming stamp lexica:f8c77bf889f6, the
    scoreboard 3/10ʰ · 7/15 (JP-ruled FINAL and UNTOUCHABLE), the live-card count, ENGINE
    LESSONS numbering (#63–#84)
  · every "don't re-pitch / don't re-open / closed" verdict — those exist to stop rework
  · the what-looked-true / was-true / here's-the-tell lessons. Consolidate their WORDING;
    deleting one is deleting the point of the file.
  · commit hashes cited as state (7c9dd93, e9089c9, 63b550e, 1a35822, dba2edb)

Verify before you cut: the skill says fix stale file/line/behaviour references against the real
repo, not against the file's own claim. Chips and counts go stale — a recent session saw a chip
say "5 call sites" when the truth was 6, because a later session had added one. Check, don't
inherit.

Deliverable and gate: per the skill, show JP the PLAN before writing — for each file, what merges
into what, what gets cut, rough before/after sizes. Then post a diff-style before/after for
review. Memory lives outside the repo: save, no commit. If the routing check moves anything into
an in-repo doc, that's a separate commit with its own receipt.

Success = ~~under 17.1KB~~ **approaching-24KB is the trigger, not a success bar (JP 2026-07-15)**,
one hook per entry, every pointer in MEMORY.md resolving to a real file, nothing in the must-survive
list weakened, and no fact invented during the tidy.

**WHAT THIS PASS ACTUALLY TAUGHT (2026-07-15), worth more than its numbers:**
- **The must-survive list and the target were incompatible, and nobody noticed until it was run.**
  This doc's own plan ("cut the worst three to one-hook lines gets MOST of the way") lands at ~18KB
  by its own arithmetic — it never reached 17.1 either. The remaining fat IS the guards. Hence the
  raise: when a bar and a rule collide, the rule wins and the bar moves.
- **"Verify it yourself" earned its keep in the one place nobody would look — the doc's own premises.**
  The counts were right; the two *mechanisms* cited for urgency (a read limit, a hook) were both
  invented. A number is easy to check and gets checked; a mechanism sounds like background and rides
  along free. **Check the WHY, not just the WHAT.**
- **A cut is only safe once its forwarding address is real.** `project_word_study_merge` declared
  itself history — but its successor didn't carry the view-id invariant (`/?lex=` deep links key off
  it) and two files linked to it. Route the durable fact UP and repoint the links FIRST, then delete.
  A self-declared-historical file is a claim like any other.
- **A pointer that lives ONLY in the index dies when you trim the index.** `tests/mobile_harness.js`
  was one line from being lost that way. Grep each fact you're about to drop against its own file
  before dropping it.
