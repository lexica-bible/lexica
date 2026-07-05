#!/usr/bin/env node
// RENDER MARKUP GATE — chip mode must carry NO bracket marks and NO order digits
// (Phase 3 made chip read in English order, so ABP's "[" "]" + superscript digits
// are inert apparatus); interlinear mode (mode three) MUST carry both (the faithful
// as-printed view). The pure-logic order tests can't see rendered markup, so this
// renders the REAL LibRender output with react-dom/server and inspects the HTML.
//
// It loads the built bundle in a vm sandbox (like the smoke gate), captures the
// bundle's own LibRender via an appended one-liner, and renders a bracketed verse
// (2 Ki 23:29) through renderVerse (chip) and renderAbpInterlinear (mode three).
//
// Run:  node tests/test_render_markup.js
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

const code = fs.readFileSync(path.join(__dirname, "..", "static", "app.js"), "utf8")
  // Capture the bundle-internal LibRender so the test can drive its verse renderers.
  + "\n;globalThis.__LibRender = (typeof LibRender !== 'undefined') ? LibRender : null;";

function perm() {
  const f = function () { return perm(); };
  return new Proxy(f, { get(_t, p) { if (p === "length") return 0; if (p === Symbol.iterator) return function* () {}; if (typeof p === "symbol") return () => ""; return perm(); }, apply() { return perm(); }, construct() { return perm(); } });
}
const ReactDOM = { createRoot: () => ({ render() {}, unmount() {} }), render() {} };
const ls = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
const doc = new Proxy({ getElementById: () => ({}), addEventListener: () => {}, createElement: () => perm(), documentElement: perm(), body: perm(), head: perm() }, { get(t, p) { return p in t ? t[p] : perm(); } });
const win = new Proxy({ React, ReactDOM, document: doc, localStorage: ls, addEventListener: () => {}, matchMedia: () => ({ matches: false, addEventListener: () => {}, addListener: () => {} }), location: { search: "", href: "", pathname: "/" }, navigator: { userAgent: "node" }, innerWidth: 1280, fetch: () => new Promise(() => {}), IntersectionObserver: function () { return { observe() {}, disconnect() {} }; }, ResizeObserver: function () { return { observe() {}, disconnect() {} }; }, getComputedStyle: () => perm(), requestAnimationFrame: () => 0 }, { get(t, p) { return p in t ? t[p] : perm(); } });
const sb = { React, ReactDOM, window: win, document: doc, localStorage: ls, navigator: win.navigator, location: win.location, fetch: win.fetch, matchMedia: win.matchMedia, getComputedStyle: win.getComputedStyle, IntersectionObserver: win.IntersectionObserver, ResizeObserver: win.ResizeObserver, requestAnimationFrame: () => 0, cancelAnimationFrame: () => {}, setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0, clearInterval: () => {}, console };
sb.globalThis = sb; sb.self = win;
vm.runInNewContext(code, sb, { filename: "app.js", timeout: 20000 });

const LibRender = sb.__LibRender;
assert.ok(LibRender && LibRender.renderVerse && LibRender.renderAbpInterlinear, "captured LibRender with both renderers");

const ki = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", "order", "2ki_23_29.json"), "utf8"));
const v = { verse: 29, words: ki.words };
// Minimal ctx: interlinear/strongs ON so the Greek + Strong's lines render too.
const ctx = {
  selChapter: 23, selBook: { abbrev: "2Ki" }, nav: null,
  wordMode: true, showInterlinear: true, showStrongs: true,
  onWordClick: () => {}, handleVerseNum: null,
  hiClass: () => "", vnumEl: () => null, noteMarker: () => null,
  highlightRef: null,
};

let n = 0;
const test = (name, fn) => { fn(); n++; console.log("ok  " + name); };

test("chip mode output has NO bracket marks and NO order digits", () => {
  const html = renderToStaticMarkup(LibRender.renderVerse(ctx, v));
  assert.ok(!html.includes("lib-iw-brk"), "chip must not render bracket marks");
  assert.ok(!html.includes("lib-iw-pos\""), "chip must not render order-digit spans");
  assert.ok(!html.includes("["), "chip must not contain a literal '['");
  // sanity: it DID render the words (English order reaches 'God')
  assert.ok(html.includes("Josiah") && html.includes("king"), "chip rendered the bracket words");
});

test("interlinear: Greek base + brackets + digits survive ALL four toggle combos; companion lines follow the toggles", () => {
  for (const showInterlinear of [true, false]) {
    for (const showStrongs of [true, false]) {
      const html = renderToStaticMarkup(LibRender.renderAbpInterlinear({ ...ctx, showInterlinear, showStrongs }, v));
      const tag = `(interlinear=${showInterlinear}, strongs=${showStrongs})`;
      // base is ALWAYS present: Greek line + bracket marks + order digits
      assert.ok(html.includes("lib-abpil-greek"), "Greek line present " + tag);
      assert.ok(html.includes("lib-iw-brk") && html.includes("["), "bracket marks present " + tag);
      assert.ok(html.includes("lib-iw-pos"), "order digits present " + tag);
      // companion lines appear ONLY when their toggle is on (space collapses otherwise)
      assert.strictEqual(html.includes("lib-abpil-gloss"), showInterlinear, "gloss line matches toggle " + tag);
      assert.strictEqual(html.includes("lib-abpil-strongs"), showStrongs, "Strong's line matches toggle " + tag);
      // PN click target unaffected by toggle state: Pharaoh stays clickable + named
      assert.ok(html.includes("Pharaoh"), "PN name in Greek line " + tag);
      assert.ok(html.includes("lib-word-clickable"), "PN stays clickable " + tag);
    }
  }
});

// SCOPED CONTAINER CLASSES — each mode's verse container carries its own scope class
// so mode-specific CSS (e.g. the interlinear gap/align) can't leak into chip. A leak
// here is how the spacing regression happened.
test("verse containers are scoped per mode (chip has no interlinear class, and vice versa)", () => {
  const chipHtml = renderToStaticMarkup(LibRender.renderVerse(ctx, v));
  const ilHtml = renderToStaticMarkup(LibRender.renderAbpInterlinear(ctx, v));
  assert.ok(chipHtml.includes("lib-verse-chips"), "chip uses the shared chips container");
  assert.ok(!chipHtml.includes("lib-verse-abpil"), "chip must NOT carry the interlinear scope class");
  assert.ok(ilHtml.includes("lib-verse-abpil"), "interlinear carries its own scope class");
});

// PN click PAYLOAD is computed from the word alone (pnClickPayload), never from the
// toggle state — assert directly against the shared helper.
test("PN click payload is independent of toggle state", () => {
  const { pnClickPayload } = require(path.join(__dirname, "..", "static", "src", "56-library-order-logic.jsx"));
  const pharaoh = ki.words.find(w => w.english === "Pharaoh");
  const a = pnClickPayload(pharaoh, "Pharaoh");
  assert.deepStrictEqual(a, { isPN: true, pnName: "Pharaoh", gloss: "Pharaoh" });
});

console.log(`\n${n} tests passed.`);
