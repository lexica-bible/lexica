#!/usr/bin/env node
// Ask-corpus highlight cited-set builder (_acCitedSet) — the Door-2 lock
// (docs/tickets/TICKET_highlight_cited_set.md).
//
// The OLD builders (52-ask-corpus._acCited + 90-app.citedStrongsApp, two drifting
// copies) added the bare digits PLUS a manufactured G-twin AND H-twin for every key
// number — so a legitimate Hebrew key (H3588 "ki") lit every Greek article (G3588)
// in the evidence verses: the stopword-highlight bug's Door 2. The shared builder
// emits ONLY language-prefixed numbers: every word row's number is fully prefixed
// (the strongs_base invariant), so bare forms in the set bought nothing except
// cross-language collisions. A bare key number is Greek by the prompt contract
// ("H prefix for Hebrew, G prefix or bare digits for Greek").
//
// Run from repo root:  node tests/test_ac_cited_set.js
"use strict";
const assert = require("assert");
const path = require("path");

require.extensions[".jsx"] = require.extensions[".js"];
const { _acCitedSet, _acDropFunctionKeys } = require(path.join(__dirname, "..", "static", "src", "51-corpus-logic.jsx"));

let n = 0;
const test = (name, fn) => { fn(); n++; console.log("ok  " + name); };

test("Door-2 control: H3588 must NOT manufacture the Greek article G3588", () => {
  const s = _acCitedSet([{ strongs: "H3588" }]);
  assert(s.has("H3588"), "the Hebrew key itself must be in the set");
  assert(!s.has("G3588"), "the Greek twin must NOT be manufactured");
  assert(!s.has("3588"), "the bare form must NOT be in the set (matchers bare both sides)");
});

test("Greek key stays Greek-only", () => {
  const s = _acCitedSet([{ strongs: "G746" }]);
  assert(s.has("G746"));
  assert(!s.has("H746") && !s.has("746"));
});

test("bare digits are Greek by the prompt contract", () => {
  const s = _acCitedSet([{ strongs: "746" }]);
  assert(s.has("G746"));
  assert(!s.has("H746") && !s.has("746"));
});

test("falls back to strongs_base (the 90-app payload shape)", () => {
  const s = _acCitedSet([{ strongs_base: "G4151" }, { strongs_base: "H7307" }]);
  assert(s.has("G4151") && s.has("H7307"));
  assert(!s.has("H4151") && !s.has("G7307"));
});

test("dotted numbers keep their dot", () => {
  const s = _acCitedSet([{ strongs: "G303.1" }]);
  assert(s.has("G303.1"));
});

test("empty / junk input returns null", () => {
  assert.strictEqual(_acCitedSet(null), null);
  assert.strictEqual(_acCitedSet([]), null);
  assert.strictEqual(_acCitedSet([{ lemma: "no number" }]), null);
  assert.strictEqual(_acCitedSet([{ strongs: "not-a-number" }]), null);
});

test("mixed list keeps each key in its own language", () => {
  const s = _acCitedSet([{ strongs: "G746" }, { strongs: "H7225" }]);
  assert(s.has("G746") && s.has("H7225"));
  assert(!s.has("H746") && !s.has("G7225"));
});

// ── the display-time function-word drop (saved threads replay stored key lists
// that predate the backend Door-1 filter; the Gen 1:1 arche thread stored G3588) ──

test("stored-thread control: G3588 dropped from a saved key list", () => {
  const funcSet = new Set(["G3588", "G2532"]);
  const keys = [{ strongs: "G746" }, { strongs: "G3588", lemma: "ὁ" }, { strongs: "G2316" }];
  const kept = _acDropFunctionKeys(keys, funcSet);
  assert.deepStrictEqual(kept.map(k => k.strongs), ["G746", "G2316"]);
  const s = _acCitedSet(kept);
  assert(!s.has("G3588") && s.has("G746") && s.has("G2316"));
});

test("no funcSet (network miss) = no-op, never hides real key words", () => {
  const keys = [{ strongs: "G746" }, { strongs: "G3588" }];
  assert.strictEqual(_acDropFunctionKeys(keys, null), keys);
  assert.strictEqual(_acDropFunctionKeys(keys, new Set()), keys);
});

test("drop is language-aware: H853 drops, G853 survives", () => {
  const funcSet = new Set(["H853"]);
  const kept = _acDropFunctionKeys([{ strongs: "H853" }, { strongs: "G853" }], funcSet);
  assert.deepStrictEqual(kept.map(k => k.strongs), ["G853"]);
});

test("_acCitedSet excludeSet drops directly too", () => {
  const s = _acCitedSet([{ strongs: "G746" }, { strongs: "G3588" }], new Set(["G3588"]));
  assert(s.has("G746") && !s.has("G3588"));
});

console.log(`\n${n} cited-set tests passed`);
