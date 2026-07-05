// ============================================================
// LIBRARY WORD-ORDER LOGIC — the two pure functions that decide reading order,
// factored OUT of 59a-library-helpers.jsx so ONE copy serves both the app
// (prose reorder + chip grouping in 59c-library-render.jsx) and the Node unit
// test (tests/test_library_order.js). No React / no JSX / no external globals —
// plain array math over a verse's `words` list.
//
//   getEnglishOrderWords — prose + (from Phase 3) chip English order. Within each
//     bracket group sort by greek_pos ascending (ABP's superscript order digit:
//     "[2fruit 1good]" -> "good fruit"); non-bracket words keep source position.
//     Operates on FULL word objects, so every token keeps its Strong's tag and
//     click identity through the reorder.
//   groupForGreekMode — chip grouping: runs of same bracket_id, source order kept
//     (the faithful ABP / mode-three order).
//
// Loads at prefix 56 (before 57-chrono, 59a-helpers, 59c-render, 60-library) so
// the functions exist before any caller. The export guard at the tail is a no-op
// in the browser (`module` is undefined there) and hands the functions to Node.
// ============================================================

// THE REORDER CORE: order one bracket group's words by ABP's superscript digit
// (greek_pos) ascending. A missing digit sorts to the end (999). Array.sort is
// stable, so equal or missing digits keep their source order. This ONE function is
// the shared reorder both prose (getEnglishOrderWords, below) and chip mode
// (59c-library-render.jsx) run — chip keeps its OWN trailing-punctuation lift and
// duplicate-number suppression around it; only the ordering is shared.
function orderBracketGroupWords(words) {
  return [...words].sort((a, b) => (a.greek_pos ?? 999) - (b.greek_pos ?? 999));
}

// Reorder words for natural English reading:
// within each bracket group sort by greek_pos ascending; non-bracket words keep position order.
function getEnglishOrderWords(words) {
  const bracketMap = {};
  for (const w of words) {
    const bid = w.bracket_id;
    if (bid !== null && bid !== undefined) {
      if (!bracketMap[bid]) bracketMap[bid] = [];
      bracketMap[bid].push(w);
    }
  }
  // Trailing punctuation marks a clause boundary in the SOURCE order. After a
  // bracket group is reordered into English order, that punctuation must float
  // to the last word of the reordered group (Greek "were-completed ... earth,"
  // -> English "... earth were-completed,") instead of stranding on "earth".
  const TRAIL = /[.,;:!?·]+$/;
  for (const bid in bracketMap) {
    let trailing = "";
    let cleaned = [];
    for (const w of bracketMap[bid]) {
      const eng = (w.english || "").trim();
      if (eng && eng.replace(TRAIL, "") === "") {        // pure-punctuation token
        trailing += eng;
        continue;
      }
      const m = eng.match(TRAIL);
      if (m) {
        trailing += m[0];
        cleaned.push({ ...w, english: eng.slice(0, eng.length - m[0].length).trimEnd() });
      } else {
        cleaned.push(w);
      }
    }
    cleaned = orderBracketGroupWords(cleaned);   // shared reorder core (was an inline .sort)
    if (trailing && cleaned.length) {
      // Attach the floated punctuation to the last word that actually has English
      // text. Empty-gloss words (e.g. the σου/αὐτός pronouns folded into a
      // neighboring noun) would otherwise become a standalone "," token, which
      // renders with a stray leading space ("reprove , me") in prose mode.
      let li = cleaned.length - 1;
      while (li > 0 && !((cleaned[li].english || "").trim())) li--;
      cleaned[li] = { ...cleaned[li], english: (cleaned[li].english || "") + trailing };
    }
    bracketMap[bid] = cleaned;
  }
  const result = [];
  const seen = new Set();
  for (const w of words) {
    const bid = w.bracket_id;
    if (bid === null || bid === undefined) {
      result.push(w);
    } else if (!seen.has(bid)) {
      seen.add(bid);
      result.push(...bracketMap[bid]);
    }
  }
  return result;
}

// Group a position-sorted word list into runs by bracket_id for bracket notation rendering.
function groupForGreekMode(words) {
  const groups = [];
  let cur = null;
  for (const w of words) {
    const bid = (w.bracket_id !== null && w.bracket_id !== undefined) ? w.bracket_id : null;
    if (bid === null) {
      groups.push({ isBracket: false, word: w });
      cur = null;
    } else {
      if (!cur || cur.bid !== bid) {
        cur = { isBracket: true, bid, words: [] };
        groups.push(cur);
      }
      cur.words.push(w);
    }
  }
  return groups;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { getEnglishOrderWords, groupForGreekMode, orderBracketGroupWords };
}
