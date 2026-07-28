# AUDIT — FRAME-0 first-paint enumeration (step 1+2 of the lane)

Ruled 2026-07-27 (reviewer), run 2026-07-28. Code-reading only, zero spend. Question per
render site: what paints on the FIRST frame, before its data resolves? Classes: BLANK/SKELETON
(fine) · STALE-BUT-CORRECT (fine) · WRONG/FALLBACK-FIRST (flash bug).

## Verdict

**8 WRONG/FALLBACK-FIRST sites — the class is 8 wide, not 3.** The three known instances
(Hebrew-flash, Canaan line, sons-of-Noah headline) were members of one mechanical family, and
5 more were sitting unfound. **One common root cause across all 8:** a loading flag that starts
OFF and only turns on when the fetch begins — so the single frame between "component appears"
and "fetch starts" is unguarded, and whatever fallback expression sits in the slot paints first.

**The repo already owns the fix vocabulary** (no new invention needed):
- seed the loading flag ON at creation when a fetch is certain — `useState(giWillFetch)`
  30-detail-panel.jsx:355, `useState(!!isHebrewWord)` :578, lazy `useState(() => …)` :608/:620
- or the `undefined`-means-loading sentinel (52-ask-corpus.jsx:514, exemplary).

## The 8, ranked by user visibility (all file:line receipts from the sweep)

1. **Hebrew word-card hero paints the English gloss in the big Hebrew headword slot** —
   30-detail-panel.jsx:724 (`bdbEntry?.lemma || entry.gloss`), JSX :1360-1366. THE
   "sons of Noah" instance. `bdbLoading` (:578) is already seeded correctly — the hero just
   never consults it (only `greekIdPending`). Cheapest fix of the set.
2. **Word study definition double-swap** — 80-lexicon.jsx:709-713 (`lsjLoading` init false :80)
   + :111-128/:673-716 (`lexica` has NO gate — comment at :114 says quiet-by-design, JP's call:
   re-confirm that ruling before touching). Plain Strong's def → LSJ body → Lexica body, two
   full-paragraph replacements. The Library card fixed exactly this (30-detail-panel.jsx:1058);
   Word study diverged. Badge flips too (:687-699).
3. **Word study hero shows the PREVIOUS word** during cognate clicks / reader handoffs —
   80-lexicon.jsx:142-178 (profile never cleared, deliberate per :145-147), hero :652-671,
   collapsed header :625-629, mobile strip :803-811. Wrong WORD, not just wrong field.
4. **Cross-ref panel says "No cross-references found." before the fetch starts** —
   40-crossref-panel.jsx:7 + :101-104. Definitive negative on frame 0.
5. **Summary panel says "No overview available for this passage." before the fetch starts** —
   30-detail-panel.jsx:99-101, :120, :142-144. Hit on every cache-miss chapter change.
6. **Cross-ref verse text serves KJV then swaps to ABP** (ABP/parallel mode) —
   40-crossref-panel.jsx:54 (`abpTexts[ref.ref] || ref.text`).
7. **Word-card verse blockquote paints "—"** — 30-detail-panel.jsx:1237; `verseLoading` false
   at mount (:199) and `kjvVerseText` has no loading flag at all (:592-602).
8. **Library reading pane blank (not "Loading…") on frame 0** — 60-library.jsx:13-32 flags all
   init false vs :1735-1920. Blank not wrong — lowest priority, same root cause.

## Clean bill (patterns to copy, not touch)
- `greekIdPending` hold (30-detail-panel.jsx:346-365, 719-739) — the reference fix.
- 52-ask-corpus.jsx `undefined` sentinel (:514) · 84-news.jsx top gate (:483) — best in repo.
- 90-app.jsx synchronous seeds for view/owner (:105-111, :310-315) — each carries a comment
  naming the flash it fixed.
- 60-library.jsx localStorage-seeded state (:6-11, :50-69) + `gatedReady` (:33-35) — correct.
- 59c-library-render.jsx: pure, zero async — all `||` are field preferences, not stand-ins.
- 59b-library-nav.jsx: no fetches, no frame-0 sites.

## Notes / adjacent (not flash bugs)
- 80-lexicon.jsx:440 `isHeb = profile.strongs[0]==="H"` misreads a `PN:<form>` key — hazard,
  separate ticket class.
- 90-app.jsx deep-links (:270-305): one frame of the restored view before the jump — tab
  flash, low visibility.
- 90-app.jsx:118 `libTranslation` not restored at app level (Library restores its own) — a
  brief wrong value flows upward, no visible text swap found.

## Step 3 (next): one shared hold pattern applied to the flagged sites — smallest edit per
site, using the existing vocabulary above; NO refactor of card rendering (ruled). #2's
quiet-by-design comment needs JP's re-confirmation first. Receipts stay frame-capture
(element boxes when captures won't paint).

## Meta-lesson consequence
The parked candidate ("two fixes of the same class is the ceiling; the third instance triggers
enumeration") is now STRONG by its own pre-registered test: the audit found 8, not 3. Bank at
lane close per the parked TODO condition.
