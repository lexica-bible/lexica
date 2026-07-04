// ============================================================
// CHRONOLOGICAL RECONCILE — pure passage-lookup logic, factored OUT of LibraryView so ONE
// copy is used by both the app (60-library.jsx: passageForRef + the reader-position
// reconcile) and the Node unit test (tests/test_chrono_reconcile.js). No React here —
// plain array math over chrono.passages.
//
// The bug this file exists to lock: opening a reading-plan day whose FIRST passage starts
// mid-chapter, in a chapter the PREVIOUS day's last passage also touches (e.g. Zephaniah 2
// split 2:1-7 in one passage / 2:8-3:20 in the next — day 219's tail vs day 220's head).
// The reader lands on the right chapter, then reports its position back as a bare
// (book, chapter) with NO verse. Resolving that to "the first passage covering the chapter"
// snaps you back to the PREVIOUS day's passage, so the clicked day never opens. 141 of the
// 365 days had this shape. The fix: if the passage you're ALREADY on still covers the
// reported chapter, the reader just moved within it — keep it.
//
// Plain JS (no JSX): the browser bundle picks it up in filename order (57 < 60, so the
// helpers exist before LibraryView uses them); the export guard at the tail is a no-op in
// the browser (`module` is undefined there) and hands the functions to Node.
// ============================================================

// Does passage p span this book + chapter?
function chronoCovers(p, book, ch) {
  return p.book === book && ch >= p.start_ch && ch <= p.end_ch;
}

// Which passage holds (book, ch[, v])? With a verse, narrow a split chapter to the passage
// whose window actually contains that verse; without a verse, fall back to the FIRST
// passage covering the chapter. Returns the passage object or null. (This is the original
// LibraryView.passageForRef, unchanged — now shared.)
function chronoPassageForRef(passages, book, ch, v) {
  if (!passages || !book) return null;
  if (v != null) {
    const exact = passages.find(p => chronoCovers(p, book, ch)
      && !(ch === p.start_ch && v < p.start_v)
      && !(ch === p.end_ch && v > p.end_v));
    if (exact) return exact;
  }
  return passages.find(p => chronoCovers(p, book, ch)) || null;
}

// Reconcile the chronological position when the reader reports its spot. The report carries
// only (book, chapter) with no verse (highlight === null). If the passage we're already on
// (curPos) still covers that chapter, the reader moved WITHIN it — keep curPos so a
// mid-chapter day head isn't dragged back to the previous day's passage. Otherwise resolve
// normally (verse-narrowed when a highlight verse IS present). Returns the passage object
// to land on, or null.
function chronoReconcile(passages, curPos, book, ch, v) {
  const cur = passages && passages[curPos - 1];
  if (v == null && cur && chronoCovers(cur, book, ch)) return cur;
  return chronoPassageForRef(passages, book, ch, v);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { chronoCovers, chronoPassageForRef, chronoReconcile };
}
