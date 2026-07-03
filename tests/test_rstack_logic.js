#!/usr/bin/env node
// RightStack reducer — the inspect-panel stack transforms (fixture 4).
//
// The contract: PUSH-UNIQUE keys (two cards of the same type can coexist without a React key
// collision), pop UNCOVERS the layer beneath, and a center peer-select RESETS to depth 1 on
// the newly-selected item. These transforms live in static/src/21-shell-logic.jsx (plain JS,
// bundled into app.js AND required here); useRightStack + RightStack call the SAME functions.
//
// Run from repo root:  node tests/test_rstack_logic.js
"use strict";
const assert = require("assert");
const path = require("path");

require.extensions[".jsx"] = require.extensions[".js"];
const { rsNextId, rsPush, rsPop, rsReset, rsLayers } =
  require(path.join(__dirname, "..", "static", "src", "21-shell-logic.jsx"));

let n = 0;
const test = (name, fn) => { fn(); n++; console.log("ok  " + name); };

const layerA = { backLabel: "Occurrence", render: () => "A" };

test("PUSH-UNIQUE: pushing the SAME entry twice gives two layers with distinct ids", () => {
  // The hook mints an ever-rising id per push (rsNextId(++seq)); simulate two pushes.
  let s = rsPush([], layerA, rsNextId(1));
  s = rsPush(s, layerA, rsNextId(2));
  assert.strictEqual(s.length, 2);              // both kept — not collapsed
  assert.notStrictEqual(s[0]._id, s[1]._id);    // distinct keys, no React collision
  assert.deepStrictEqual([s[0]._id, s[1]._id], ["L1", "L2"]);
});

test("push does not mutate the input stack (new array each time)", () => {
  const s0 = [];
  const s1 = rsPush(s0, layerA, rsNextId(1));
  assert.strictEqual(s0.length, 0);
  assert.strictEqual(s1.length, 1);
});

test("pop uncovers the layer beneath (drops only the top)", () => {
  let s = rsPush(rsPush([], layerA, rsNextId(1)), layerA, rsNextId(2));
  s = rsPop(s);
  assert.strictEqual(s.length, 1);
  assert.strictEqual(s[0]._id, "L1");           // the first layer is still there, uncovered
});

test("center peer-select RESETS to depth 1 on the new item", () => {
  const root = { key: "Gen-1-1", render: () => "root" };
  // Drill two deep, then a peer-select resets the pushed stack; the layer list is just the root.
  let s = rsPush(rsPush([], layerA, rsNextId(1)), layerA, rsNextId(2));
  const afterReset = rsLayers(root.render, root.key, rsReset());
  assert.strictEqual(afterReset.length, 1);     // depth 1
  assert.strictEqual(afterReset[0]._id, "Gen-1-1");
  assert.strictEqual(afterReset[0].root, true);
});

test("rsLayers puts the root first, keyed by its own key (or the literal 'root')", () => {
  const withKey = rsLayers(() => "x", "Gen-1-1", []);
  assert.strictEqual(withKey[0]._id, "Gen-1-1");
  const noKey = rsLayers(() => "x", undefined, []);
  assert.strictEqual(noKey[0]._id, "root");     // fallback when a root has no stable key
});

test("rsLayers stacks pushed layers ABOVE the root; depth = layers.length", () => {
  let s = rsPush(rsPush([], layerA, rsNextId(1)), layerA, rsNextId(2));
  const layers = rsLayers(() => "root", "Gen-1-1", s);
  assert.strictEqual(layers.length, 3);         // root + 2 pushed = depth 3
  assert.strictEqual(layers[0].root, true);
  assert.strictEqual(layers[2]._id, "L2");      // the top layer is last (visible)
});

console.log("\n" + n + " passed");
