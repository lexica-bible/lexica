# Handoff — /consolidate pass on the memory index

Status at handoff: MEMORY.md is over its read limit and the harness hook has nagged about it for
three sessions. Each of those sessions correctly DECLINED to do it mid-flight — a whole-index
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
  MEMORY.md   20,865 bytes / 120 lines / 99 entries      target: under 17,100
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

Success = under 17.1KB, one hook per entry, every pointer in MEMORY.md resolving to a real file,
nothing in the must-survive list weakened, and no fact invented during the tidy.
