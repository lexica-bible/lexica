# TICKET — STEP tag placement (cosmetic; reviewer follow-up from R-2 stage-2 receipt 2)

Status: LANDED (commit a570f9b, 2026-07-24) — awaiting JP's post-deploy C2 screenshot to close.
Fix: tag removed from the head band; now renders beside the G9xxx number in the body's
ABP Occurrences line (the static branch — STEP-keyed cards always take it). Guarded so a
lemma-only card never shows a stray tag. No CSS change; reuses `.detail-strong-alias`.

Opened 2026-07-24 at receipt-2 close.

The STEP source tag (ruling S2-Q2) renders in the card's top head band —
`static/src/30-detail-panel.jsx`, the `detail-strong-wrap` span (`· STEP` as a
`detail-strong-alias` beside `detail-strong-head`). On JP's C2 screenshot (Agag,
1Sa 15:8, G9826) it reads as part of the breadcrumb bar next to "Overview" rather
than sitting with the number the reader is studying.

Reviewer ruling: move the tag so it sits beside the headword number in the card
body, where C1/C2a display theirs. Information is correct and present — placement
only, not a gate item.

Constraints: quiet style per the design doctrine (no pill — CONTESTED is the only
pill); word-study card shares these classes, so any tweak scoped per the
`.wd`-scoping rule in docs/claude/word-study.md.
