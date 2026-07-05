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

// getEnglishOrderWords + groupForGreekMode moved to 56-library-order-logic.jsx
// (loads earlier in the bundle) so the SAME copy serves the app and the Node
// unit test tests/test_library_order.js. They remain plain globals here.
