#!/usr/bin/env node
// Outlet cap on the News Inbox top band — locks applyOutletCap (static/src/83-news-logic.jsx,
// bundled into app.js AND required here, so this guards the app, not a copy).
//
// Ruling 2026-10-24 (Item 2, layer 1): in the first `band` cards of the default Inbox sort, at
// most `cap` may share one headline outlet. Skipped cards are not dropped — they follow the
// band in their original order, then the rest unchanged. cap = null leaves the list as sorted.
//
// Run from repo root:  node tests/test_outlet_cap.js
"use strict";
const assert = require("assert");
const path = require("path");

require.extensions[".jsx"] = require.extensions[".js"];
const { applyOutletCap, newsFaceSource, newsOutletLayersApply } =
  require(path.join(__dirname, "..", "static", "src", "83-news-logic.jsx"));

let n = 0;
const test = (name, fn) => { fn(); n++; console.log("ok  " + name); };

// A card the way the server ships it: the headline outlet is the member whose url is the
// card's url (newsFaceSource), NOT sources[0]. `rank` is the position after the existing sort.
const card = (rank, outlet) => ({
  rank, url: `https://example.invalid/${rank}`,
  sources: [{ source: "Newest-dated other outlet" }],      // must NOT be read as the outlet
  members: [{ url: `https://example.invalid/${rank}`, src: outlet },
            { url: `https://example.invalid/${rank}-b`, src: "Sibling outlet" }],
});

// The pinned fixture: one outlet holds ranks 1-5, three others hold 6-10.
const FIXTURE = [
  card(1, "Dominant"), card(2, "Dominant"), card(3, "Dominant"), card(4, "Dominant"),
  card(5, "Dominant"), card(6, "Outlet B"), card(7, "Outlet C"), card(8, "Outlet D"),
  card(9, "Outlet B"), card(10, "Outlet C"),
];
const ranks = (list) => list.map(c => c.rank);

test("band=6, cap=2: band = 2 of the dominant outlet then ranks 6-9", () => {
  const out = applyOutletCap(FIXTURE, 6, 2);
  assert.deepStrictEqual(ranks(out.slice(0, 6)), [1, 2, 6, 7, 8, 9]);
  assert.strictEqual(out.slice(0, 6).filter(c => newsFaceSource(c) === "Dominant").length, 2);
});

test("ranks 3-5 follow the band immediately, in order; then the rest", () => {
  assert.deepStrictEqual(ranks(applyOutletCap(FIXTURE, 6, 2)), [1, 2, 6, 7, 8, 9, 3, 4, 5, 10]);
});

test("nothing dropped: same length, same cards", () => {
  const out = applyOutletCap(FIXTURE, 6, 2);
  assert.strictEqual(out.length, 10);
  assert.deepStrictEqual(ranks(out).sort((a, b) => a - b), ranks(FIXTURE));
});

test("cap = null returns the input order", () => {
  assert.deepStrictEqual(ranks(applyOutletCap(FIXTURE, 6, null)), ranks(FIXTURE));
});

test("input list is not changed in place", () => {
  const copy = FIXTURE.slice();
  applyOutletCap(FIXTURE, 6, 2);
  assert.deepStrictEqual(ranks(FIXTURE), ranks(copy));
});

test("a card with no known headline outlet is never capped", () => {
  const blank = [card(1, ""), card(2, ""), card(3, ""), card(4, "?"), card(5, "?"), card(6, "?")];
  blank.forEach(c => { c.sources = []; });                   // no fallback outlet either
  assert.deepStrictEqual(ranks(applyOutletCap(blank, 6, 2)), [1, 2, 3, 4, 5, 6]);
});

test("list shorter than the band: skipped cards still follow, nothing lost", () => {
  const short = FIXTURE.slice(0, 5);                         // all Dominant
  assert.deepStrictEqual(ranks(applyOutletCap(short, 20, 2)), [1, 2, 3, 4, 5]);
});

test("ruled defaults are band 20, cap 2", () => {
  const many = Array.from({ length: 30 }, (_, i) => card(i + 1, i < 10 ? "Dominant" : "Other " + i));
  const out = applyOutletCap(many);
  assert.strictEqual(out.slice(0, 20).filter(c => newsFaceSource(c) === "Dominant").length, 2);
  assert.strictEqual(out.length, 30);
});

// --- WHEN the layers run (rulings 2026-10-25: Inbox tab, Top stories sort, no thread, every
// date window; Kept / Dismissed plain under every sort) ---
// A window bypass would have switched the cap off for good: the picker remembers its choice,
// and the old opening preset (21d) had no button to return to. The opening preset is now 30d.
const inbox = { view: "inbox", order: "score", thread: "", minScore: 5 };

test("cap applies with a non-default date window (7d / 90d / 1y / Max / custom)", () => {
  for (const windowKey of ["7", "14", "90", "365", "max", "custom"]) {
    assert.strictEqual(newsOutletLayersApply({ ...inbox, windowKey }), true, "window " + windowKey);
  }
  assert.strictEqual(newsOutletLayersApply({ ...inbox, windowKey: "30" }), true);   // opening preset
});

test("a thread selection bypasses the cap", () => {
  assert.strictEqual(newsOutletLayersApply({ ...inbox, windowKey: "30", thread: "ecumenism" }), false);
  assert.strictEqual(newsOutletLayersApply({ ...inbox, windowKey: "max", thread: "ai_moralized" }), false);
});

test("the score floor never bypasses", () => {
  for (const minScore of [0, 5, 6, 9]) {
    assert.strictEqual(newsOutletLayersApply({ ...inbox, windowKey: "30", minScore }), true);
  }
});

test("Newest / Oldest sorts bypass the cap, under any window", () => {
  for (const windowKey of ["30", "7", "max", "custom"]) {
    assert.strictEqual(newsOutletLayersApply({ ...inbox, windowKey, order: "date" }), false);
    assert.strictEqual(newsOutletLayersApply({ ...inbox, windowKey, order: "oldest" }), false);
  }
});

test("Kept and Dismissed tabs are plain raw-score order under every sort and window", () => {
  for (const view of ["kept", "dismissed"]) {
    for (const order of ["score", "date", "oldest"]) {
      for (const windowKey of ["30", "7", "max"]) {
        assert.strictEqual(newsOutletLayersApply({ ...inbox, view, order, windowKey }), false,
                           `${view} / ${order} / ${windowKey}`);
      }
    }
  }
  assert.strictEqual(newsOutletLayersApply({ ...inbox, view: "inbox", windowKey: "90" }), true);
});

console.log(`\n${n} passed`);
