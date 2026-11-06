# HANDOFF — edition upgrade: reviewer-subagent setup (written 2026-11-06)

Successor to `HANDOFF_edition_upgrade_stageC_repin.md` (stage C CLOSED 11/6 at `7d815400`; record at the end of
`DRAFT_stageC_outline.md`). Stage D waits behind this task.

## Why the last session closed
CLAUDE.md stop rule. CC recorded a GUESSED cause for a false CR hit ("matched the letter r") in the DRAFT and memory;
testing showed otherwise (in local Git Bash, `$'\r'` inside `"$(…)"` becomes nothing → empty grep pattern → matches
every line). Both records corrected. The verified figure (0 CR bytes) never depended on it. Nothing on PA was affected.

## The task (ruling chat 11/6, paraphrased — the spec is theirs)
Draft `.claude/agents/reviewer.md`; **print the full draft in chat, do NOT write the file** until cleared. Under ~120
lines. Contents:
1. Scope: reviewer CLEARS only (a) read-only blocks and (b) re-runs of gates already ruled in `DESIGN_q2_build.md`
   §9.x, with the ruled expected figures. Anything else (any write, any REF move, any new ruling, any figure not
   traceable to a ruling or to code) → ESCALATE to the ruling chat; never ask JP.
2. Gate wrapper verbatim: GATE REF line · `git diff --quiet "$REF" HEAD -- scripts tests` · porcelain
   (`--untracked-files=no -- scripts tests`) empty · `git merge-base --is-ancestor "$REF" HEAD` · tee to a dated log ·
   expected figures stated before the run · exit code printed · the three untracked PA `scripts/*.txt` left alone.
3. Banked tripwires, all of them (ruling chat's list): no `!` in pasted blocks except `!=`; grep via `<<<`, not pipes,
   under pipefail; frozen-list Strong's = build-time `strongs_base` (compare both columns); charter descriptions of
   live rows are claims — read the rows; forecast patch counts from the last run's log, not entry counts; verify
   checklist figures against code before they go in a gate; count CR bytes with `tr -cd '\r' | wc -c`; a check that
   cannot fire is void (controls first); re-runs overwrite logs — paste once.
4. Stop rule: two wrong gate figures in one session = handoff (CLAUDE.md).
5. Output: `REVIEW: CLEAR` / `REVIEW: ESCALATE` + one-line reason, then the block or the escalation text.
Cite the DESIGN §§ for the wrapper and the stop rule by number.

## Findings — take to the ruling chat BEFORE drafting (each checked 11/6; re-check, don't trust)
1. **No DESIGN § covers the full wrapper.** `DESIGN_q2_build.md` §9 ends at §9.84. The only wrapper wording is inside
   §9.76 (line ~469): "gated blocks test that code is unchanged (`git diff --quiet <commit> HEAD -- scripts tests`),
   not an exact HEAD; no pushes while a gated block is waiting" (CC rules banked 11/2). The porcelain and
   merge-base pieces are "Standing rules" in `HANDOFF_edition_upgrade_stageC_repin.md` (lines 60–61) — not a DESIGN §
   (memory `feedback_conditional_clearance_chained` has only the `git diff --quiet` piece). Spec item 2 omits "no scripts/tests pushes while a
   gated block waits" (§9.76); recommend adding it.
2. **No DESIGN § for the stop rule.** CLAUDE.md's rule is stricter: ONE unverified claim or guess → stop + handoff.
   The "two" comes from 11/4 (`HANDOFF_edition_upgrade_stageC_tail.md` "Why this session closed": two unchecked
   gate pre-check figures → closed). Writing "two" alone into the reviewer would loosen CLAUDE.md — ask the ruling
   chat how to word it (e.g. one unverified figure = ESCALATE; a second wrong gate figure = stop + handoff).
3. **§9.85–§9.89 are NOT in DESIGN** — only in `DRAFT_stageC_outline.md` (§9.85 ~line 1512, §9.86/§9.87 ~1833,
   §9.86 withdrawn ~1965, §9.88 ~1968/2110/2147/2219, §9.89 ~2152). Under spec item 1(b) a gate 3 re-run ruled by
   §9.87 would not count as "ruled in DESIGN". Options: copy §9.85–§9.89 into DESIGN first (docs only), or widen
   scope to "DESIGN §9 + the DRAFT's recorded rulings".
4. **Two banked tripwires are missing from the spec's list** (both in the repin handoff's "Tripwires banked"): a
   `-journal` file beside a copy = stop, move it aside (never delete) before restoring; bracket groups read at their
   first member sorted by `greek_pos`, trailing punctuation floats to the last member — test a digit fix through
   `reorder_english` first. Spec says "all of them" → recommend adding.
5. **The CR tripwire's cause** is the Git Bash behavior above; PA's bash is untested. Word the tripwire as "count
   bytes with `tr`", not as a claim about grep.
6. `.claude/agents/` does not exist yet (only `.claude/commands/`). Recommend tools = Read, Grep, Glob only (the
   reviewer reads code to trace figures; it runs nothing).

## Then
Write the cleared file, commit (docs/config only), then stage D per the repin handoff's "Then" list
(`declared_deltas.json` before gate 2, pn_binding first; §9.85 member rulings; Gen 46:26 lane ③ repair at 8b.2a;
§9.87 punct re-freeze 607 at 9c).

## Standing rules
Unchanged from `HANDOFF_edition_upgrade_stageC_repin.md` "Standing rules".
