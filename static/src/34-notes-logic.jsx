// ============================================================
// NOTES — pure logic for the anchored-verse inspect (no JSX in this file on purpose).
// Lifted so the Node tests exercise the SAME code the app runs, not a second copy that
// drifts — the repo's standing pattern for testing frontend logic (see 21-shell-logic.jsx).
// Numbered before 35-notes.jsx so it's a global by the time NoteVerseInspect calls it.
// ============================================================

// The chapter's last verse, out of /api/chapter's reply.
//
// The reply is a BARE LIST — views_library.py:268 `return jsonify([...])` — and the Library
// consumes it as one (60-library.jsx:444, `setVerses(data)`). This used to read `d.verses`,
// which is undefined on a list, so it ALWAYS fell back and the "after" neighbour could never
// render. Sibling routes disagree on shape by design (/api/verse-words returns {words:[...]}),
// so read the producer, don't pattern-match off a neighbour.
//
// `fallback` is the anchor's LAST verse: on a genuine miss (empty chapter, network error) we
// want the after-neighbour hidden rather than a row pointing past the end of the chapter.
function noteInspLastVerse(reply, fallback) {
  const vs = Array.isArray(reply) ? reply : [];
  if (!vs.length) return fallback;
  return Math.max(...vs.map((x) => x.verse));
}

// Which verses the inspect renders, and what each one IS.
//
// A note anchors a RANGE: 60-library.jsx `resolveSelection()` stores start.verse and end.verse
// separately (:1098-1099) from the two edges of a drag-select. Every verse from start to end is
// the note's OWN text and reads as "anchor"; one neighbour each side of the WHOLE range is
// context and reads as "near". Reading only start.verse was the bug — it truncated a range note
// to its first verse while the label still promised the range.
//
// lo/hi are ordered defensively: the write path already swaps a backwards drag (:1063-1066),
// but imported or hand-edited notes make no such promise, and a reversed pair would otherwise
// render an empty range.
function noteInspRows(startVerse, endVerse, lastVerse) {
  const lo = Math.min(startVerse, endVerse);
  const hi = Math.max(startVerse, endVerse);
  const rows = [];
  if (lo > 1) rows.push({ verse: lo - 1, kind: "near" });
  for (let v = lo; v <= hi; v++) rows.push({ verse: v, kind: "anchor" });
  if (lastVerse != null && hi < lastVerse) rows.push({ verse: hi + 1, kind: "near" });
  return rows;
}

// A no-op in the browser (`module` is undefined there); the handoff to the Node tests.
if (typeof module !== "undefined" && module.exports) {
  module.exports = { noteInspLastVerse, noteInspRows };
}
