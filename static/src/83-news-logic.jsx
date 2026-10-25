// ============================================================
// NEWS FEED — pure ordering logic, factored OUT of NewsView so ONE copy is used by both the
// app (84-news.jsx) and the Node unit test (tests/test_outlet_cap.js). No React here.
//
// Plain JS (no JSX): the browser bundle picks it up in filename order (83 < 84, so these exist
// before NewsView uses them); the export guard at the tail is a no-op in the browser (`module`
// is undefined there) and hands the functions to Node.
// ============================================================

// The FACE article's own outlet, matched in members by url — NOT sources[0] (the newest-dated
// outlet, a different article). Shared by the card meta line, copy/export AND the outlet cap
// below, so "whose card is this" can't drift between what the card says and how it's capped.
function newsFaceSource(s) {
  const face = (s.members || []).find(m => m.url === s.url) || {};
  return face.src || ((s.sources || [])[0] || {}).source || "";
}

// Outlet cap on the Inbox TOP BAND (ruling 2026-10-24, Item 2 layer 1). One outlet that scores
// itself high on stories nobody else covers (Advent Messenger: 28 of 31 recent articles on cards
// no other outlet shares) shouldn't fill the top of the feed. Walk the already-sorted list and
// fill the first `band` slots in order, skipping any card whose headline outlet already holds
// `cap` slots in the band. Skipped cards are NOT dropped: they come straight after the band in
// their original relative order, then the rest of the list unchanged. Same cards, same count —
// only the top band's order moves. A card with no known headline outlet ("" or the server's "?")
// is its own bucket and never capped. cap == null (or band <= 0) returns the input order.
function applyOutletCap(cards, band = 20, cap = 2, outletOf = newsFaceSource) {
  if (cap == null || !(band > 0) || !cards) return cards;
  const inBand = [], skipped = [], per = new Map();
  let i = 0;
  for (; i < cards.length && inBand.length < band; i++) {
    const c = cards[i];
    const o = outletOf(c) || "";
    if (o && o !== "?") {
      const n = per.get(o) || 0;
      if (n >= cap) { skipped.push(c); continue; }
      per.set(o, n + 1);
    }
    inBand.push(c);
  }
  return inBand.concat(skipped, cards.slice(i));
}

// WHEN the two outlet layers run (the rank_score sort, then applyOutletCap). Rulings 2026-10-25:
// the INBOX tab, sorted by Top stories, with no thread picked — under EVERY date window
// (7d / 14d / 30d / 90d / 1y / Max / custom). Kept and Dismissed are plain raw-score order under
// every sort; Newest / Oldest and a thread other than "All threads" switch them off too. The
// score floor never does. The window and floor are accepted and deliberately ignored, so a
// caller can pass its whole filter state.
function newsOutletLayersApply({ view, order, thread }) {
  return view === "inbox" && order === "score" && !thread;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { newsFaceSource, applyOutletCap, newsOutletLayersApply };
}
