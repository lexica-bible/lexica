---
description: Update the living docs (CLAUDE.md, memory, TODO/archive) to close out a chunk of work
---

You're wrapping up a chunk of work. Bring the project's living docs up to date so the next session starts clean. Do each item that applies; skip anything with no real change. Talk to me in plain English (see the communication style rule) and keep it tight.

**The test for every entry:** if a fact is discoverable by reading the code or `git log` in under a minute, it does NOT belong in these docs. These docs exist only for what a fresh session cannot reconstruct from the repo — the *why*, the invariants, the lessons. Bias toward pruning over adding.

**Before adding anything to a file, delete what's now false.** Living docs decay by accumulation, not omission. A wrong standing rule is worse than a missing one — it actively misleads the next session. Each section below is a delete-then-add pass, in that order.

1. **CLAUDE.md** — first remove any standing fact this session made false (dead invariant, renamed module, changed deploy step). Then, if a durable fact changed (architecture, database tables, invariants, file/module layout, deploy steps, design decisions), update the right section. Standing facts only — no session narrative. **Size rule:** CLAUDE.md is always-loaded, so every line taxes every future session. It's already a large, dense standing-rules file (~1,200 lines) — so the bar to ADD a line is high: only a standing rule that genuinely can't live in a linked memory doc earns a spot here. When in doubt, the *story* goes to memory, only the *rule* stays here. If it grows past ~1,300 lines, a `/consolidate` trim is due.

2. **Memory** (`C:\Users\JP\.claude\projects\C--Users-JP-projects-bible-db\memory\`) — first fix any claim this session made stale (don't leave wrong file/line/behavior notes). Then create or update the relevant memory file(s) for anything non-obvious worth carrying forward. Don't save what code/git already records. Add or update the one-line pointer in `MEMORY.md`.
   **Lesson capture (do this explicitly):** for each thing that went wrong this session and got fixed, write one line — *what looked true, what was actually true, what tipped it off.* These are the entries that vanish if not forced; an open-ended "worth carrying forward" skips them.

3. **TODO.md / TODO_ARCHIVE.md** — tick off finished items; MOVE anything completed or scrapped (with the why + any lesson learned) out of `TODO.md` into `TODO_ARCHIVE.md`; add any new follow-ups that surfaced this session. Delete TODOs that quietly became irrelevant — note why in the archive rather than leaving them to rot.

4. **Consolidation check (flag only — do NOT consolidate here).** After updating, check each living doc for consolidation debt and flag it in the summary if tripped — but don't restructure now; that's `/consolidate`, run deliberately.
   - CLAUDE.md over ~1,300 lines (it sits around 1,200 — flag only real growth past that, not its normal size)
   - MEMORY.md index over ~17KB (the hook threshold), or any single memory file over ~200 lines, or 3+ memory files covering one topic
   - TODO.md over ~20 open items
   If any trips, say so plainly — e.g. "MEMORY.md is at 18KB, `/consolidate` is due" — and stop there. Never silently consolidate inside a wrap; a routine close-out must stay light and predictable.

**Verify before you record.** This command exists partly to fix notes past sessions got wrong, so don't trust this session's own account blindly. Before writing a durable fact (a new table, an invariant, a deploy step), confirm it against the actual code or schema — not against what the conversation claimed shipped. Record what's true in the repo, not what was intended.

Then: show me a short bullet summary of what you changed in each file. Memory files live OUTSIDE the repo — just save them, no commit. Commit the in-repo docs (CLAUDE.md, TODO.md, TODO_ARCHIVE.md) only if I've been committing this session / it makes sense; otherwise leave them staged and tell me.
