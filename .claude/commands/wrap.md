---
description: Update the living docs (CLAUDE.md, memory, TODO/archive) to close out a chunk of work
---

You're wrapping up a chunk of work. Bring the project's living docs up to date so the next
session starts clean. Do each item that applies; skip anything with no real change. Talk to me
in plain English (see the communication style rule) and keep it tight.

1. **CLAUDE.md** — if any *durable* fact changed (architecture, database tables, invariants,
   file/module layout, deploy steps, design decisions), update the right section. Standing facts
   only — no session narrative.

2. **Memory** (`C:\Users\JP\.claude\projects\C--Users-JP-projects-bible-db\memory\`) —
   create or update the relevant memory file(s) for anything non-obvious worth carrying forward,
   and FIX any claims this session made stale (don't leave wrong file/line/behavior notes). Add or
   update the one-line pointer in `MEMORY.md`. Don't save what code/git already records.

3. **TODO.md / TODO_ARCHIVE.md** — tick off finished items; MOVE anything completed or scrapped
   (with the why + any lesson learned) out of `TODO.md` into `TODO_ARCHIVE.md`; add any new
   follow-ups that surfaced this session.

Then: show me a short bullet summary of what you changed in each file. Memory files live OUTSIDE
the repo — just save them, no commit. Commit the in-repo docs (CLAUDE.md, TODO.md,
TODO_ARCHIVE.md) only if I've been committing this session / it makes sense; otherwise leave them
staged and tell me.
