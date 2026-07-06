---
description: Deep-clean the living docs — merge, regroup, and collapse. Run deliberately, not every session.
---

You're consolidating the project's living docs. This is the periodic deep-clean `/wrap` flags but never does — a bigger, deliberate restructuring pass. It produces a large diff by design; that's why it's separate from the routine wrap. Talk to me in plain English and keep it tight.

Do this only for files `/wrap` flagged as due, unless I name a specific file. For each:

1. **Read the whole file first.** You can't consolidate what you haven't seen end to end. No partial-view edits.

2. **CLAUDE.md + `docs/claude/*.md`** — the core job now is checking that ROUTING held: nothing session-scoped or dated-narrative leaked into core, and nothing durable got stranded in a handoff / AUDIT / memory that belongs in a module. Move each rule to where it belongs (cross-project doctrine or a standing rule/invariant → core; per-area detail → its module: data-model / frontend / ai / word-study / ops), regroup related rules within a file so they sit together, merge rules that drifted into duplicates, and cut anything now false — verify each invariant against the actual code/schema before keeping it, don't trust the file's own claim. Same standing facts, better routed and shorter, never new facts invented during the tidy. Keep core LEAN (~200-line neighborhood); let the modules hold the domain detail.

3. **Memory** — merge files covering one topic into one. Collapse superseded notes (three sessions of "panel half-wired → wired → live" become one line: "panel live both directions"). Fix stale file/line/behavior references against the real repo. Keep the lessons (what-looked-true / was-true / tipped-it-off) — those are the point; consolidate their wording, don't delete them. Update every pointer in MEMORY.md to match the merged structure.

4. **TODO.md / TODO_ARCHIVE.md** — collapse near-duplicate items, move everything done/scrapped to the archive with its why+lesson, delete items that quietly went irrelevant (noting why in the archive). TODO.md should end holding only genuinely-open, genuinely-distinct work.

**Before saving anything, show me the plan:** for each file, what merges into what, what gets cut, and the rough before/after size. I approve the plan, THEN you write. This is a big diff — I want to see the shape before it lands, same as any large change.

Memory files live outside the repo — save them, no commit. For in-repo docs (CLAUDE.md, `docs/claude/*.md`, TODO.md, TODO_ARCHIVE.md), commit only on my explicit ok, since a consolidation diff is large and worth a deliberate commit message.
