// 59a — Library helpers, split out of 60-library.jsx so that file holds only the
//       LibraryView component. Loads just before 59b-library-nav + 60-library.
// ============================================================
// LIBRARY HELPERS
// ============================================================

// Wrap every occurrence of any term in `terms` with a highlight mark (for the
// in-text search result list). `partial` false = whole-word only; `caseSensitive`
// matches case. Mirrors the backend matcher so the paint lines up with the hits.
function highlightTerms(text, terms, partial, caseSensitive) {
  if (!text || !terms || !terms.length) return text;
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const body = terms.filter(Boolean).map(t => {
    const e = esc(t);
    return partial ? e : `(?<!\\w)${e}(?!\\w)`;
  }).join("|");
  if (!body) return text;
  let re;
  try { re = new RegExp(body, caseSensitive ? "g" : "gi"); } catch (e) { return text; }
  const parts = [];
  let last = 0, key = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(<mark key={key++} className="lib-search-mark">{m[0]}</mark>);
    last = m.index + m[0].length;
    if (m.index === re.lastIndex) re.lastIndex++;   // guard against a zero-length match
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

// Search-range presets for the in-text search (mirrors eSword's range groups).
// Each is [fromAbbrev, toAbbrev] over the canonical 66 books.
const SEARCH_RANGES = [
  { id: "all", label: "Whole Bible",            from: "Gen", to: "Rev" },
  { id: "ot",  label: "Old Testament",          from: "Gen", to: "Mal" },
  { id: "nt",  label: "New Testament",          from: "Mat", to: "Rev" },
  { id: "pent",label: "Pentateuch (Gen–Deu)",   from: "Gen", to: "Deu" },
  { id: "hist",label: "History (Jos–Est)",      from: "Jos", to: "Est" },
  { id: "wis", label: "Wisdom (Job–Son)",       from: "Job", to: "Son" },
  { id: "maj", label: "Major Prophets (Isa–Dan)", from: "Isa", to: "Dan" },
  { id: "min", label: "Minor Prophets (Hos–Mal)", from: "Hos", to: "Mal" },
  { id: "gos", label: "Gospels & Acts (Mat–Act)", from: "Mat", to: "Act" },
  { id: "paul",label: "Paul's Letters (Rom–Heb)", from: "Rom", to: "Heb" },
  { id: "gen", label: "General Letters (Jas–Jud)", from: "Jas", to: "Jud" },
  { id: "apoc",label: "Apocalypse (Rev)",       from: "Rev", to: "Rev" },
];
// Canonical book list (abbrev order) for the from/to pickers.
const SEARCH_BOOK_LIST = Object.keys(BOOK_ORDER);

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
    const cleaned = [];
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
    cleaned.sort((a, b) => (a.greek_pos ?? 999) - (b.greek_pos ?? 999));
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

// Which sub-word of a split multi-word gloss carries the Strong's number + Greek
// lemma superscript in chip mode. For a CONTENT-word slot (verb/noun/adjective per
// the morph POS) the number belongs to the head content word — english_head, e.g.
// "put" in "you shall put it" — not the leading "you". For a FUNCTION-word slot
// (article/preposition/pronoun/conjunction/particle), and whenever morph is absent,
// it stays on the first non-italic token (prior behavior), which IS the function
// word itself ("of", "the"). Only ever returns a non-italic (visible) token so the
// superscript actually renders. morph schemes: OT CATSS (V./N./A.) + NT Robinson
// (V-/N-/A-) — content words start V/N/A in both.
function strongsAnchorIndex(parts, italicSet, w) {
  const bare = s => s.replace(/[^\w]/g, "").toLowerCase();
  const firstNonItalic = parts.findIndex(word => !italicSet.has(bare(word)));
  // Anchor the Strong's on the gloss's head word whenever it's present — even when
  // the row has no morph. The old morph gate dropped the Strong's onto the FIRST word
  // for null-morph rows ("of the LORD" → shown on "of", not "LORD"); the head is the
  // Strong's-bearing word, so anchoring on it is always at least as good (recovers ~552
  // κύριος/G2962 displays — see scripts/audit_lord_strongs.py ANCHOR-MORPH bucket).
  if (w.english_head) {
    const hb = bare(w.english_head);
    const hi = parts.findIndex(word => bare(word) === hb && !italicSet.has(bare(word)));
    if (hi >= 0) return hi;
  }
  return firstNonItalic;
}
