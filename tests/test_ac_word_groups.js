#!/usr/bin/env node
// Ask-corpus provenance rail — the "Words in scope" builder (_acWordGroups).
//
// This is the frontend logic behind fixture 1: for a scoped answer, the rail must show the
// right words with the right badges — in-scope vs lexical-family, contested, and the
// standard<->ABP alias note. _acWordGroups lives in static/src/51-corpus-logic.jsx (plain JS,
// bundled into app.js AND required here) so this test drives the SAME code the app runs.
//
// Run from repo root:  node tests/test_ac_word_groups.js
"use strict";
const assert = require("assert");
const path = require("path");

// The shared logic is a .jsx file (bundled by filename order) but contains no JSX — let Node
// load it with the plain-JS compiler so the test imports the exact production function.
require.extensions[".jsx"] = require.extensions[".js"];
const { _acWordGroups } = require(path.join(__dirname, "..", "static", "src", "51-corpus-logic.jsx"));

let n = 0;
const test = (name, fn) => { fn(); n++; console.log("ok  " + name); };

// A scoped answer: three in-scope words (Greek fire, Greek charis, Hebrew esh) + a computed
// panel whose Greek family adds one cognate (pyroo) the answer didn't itself use.
const words = [
  { strongs: "G4442", lemma: "πῦρ", translit: "pyr" },                          // fire — in panel too
  { strongs: "G5484", lemma: "χάρις", translit: "charis",
    alias_note: { standard: ["G5485"] } },                                                     // charis — carries a crosswalk
  { strongs: "G2316", lemma: "θεός", translit: "theos", contested: true }, // theos — contested via its own flag
  { strongs: "H784", lemma: "אֵשׁ", translit: "esh" },                      // Hebrew — panel didn't include it
];
const panel = { groups: [
  { lang: "G", label: "Greek (NT / Greek OT)", max: 1000, set_aside: 2, family: [
    { strongs: "G4442", lemma: "πῦρ", translit: "pyr", gloss: "fire", count: 1000, core: true },
    { strongs: "G4448", lemma: "πυρόω", translit: "pyroo", gloss: "to burn", count: 10 },
  ] },
] };
const contestedSet = new Set(["G5484"]);   // charis flagged by the server register set

const groups = _acWordGroups(words, panel, contestedSet);
const G = groups.find(g => g.lang === "G");
const H = groups.find(g => g.lang === "H");
const row = (g, s) => g.rows.find(r => r.strongs === s);

test("groups split by language, Greek before Hebrew", () => {
  assert.strictEqual(groups.length, 2);
  assert.strictEqual(groups[0].lang, "G");
  assert.strictEqual(groups[1].lang, "H");
});

test("in-scope answer words are flagged inScope; family-only cognate is not", () => {
  assert.strictEqual(row(G, "G4442").inScope, true);    // fire — answer used it
  assert.strictEqual(row(G, "G4448").inScope, false);   // pyroo — family only, not evidence
  assert.strictEqual(row(H, "H784").inScope, true);     // esh — answer scope word
});

test("contested badge comes from EITHER the server set OR the word's own flag", () => {
  assert.strictEqual(row(G, "G5484").contested, true);  // via contestedSet
  assert.strictEqual(row(G, "G2316").contested, true);  // via ks[s].contested
  assert.strictEqual(row(G, "G4442").contested, false); // plain fire — no badge
});

test("alias note passes through to the row (the standard<->ABP crosswalk)", () => {
  assert.deepStrictEqual(row(G, "G5484").aliasNote, { standard: ["G5485"] });
  assert.strictEqual(row(G, "G4442").aliasNote, null);  // fire has no crosswalk
});

test("panel rows carry counts/bars; appended scope words don't (hasCount)", () => {
  assert.strictEqual(row(G, "G4442").hasCount, true);
  assert.strictEqual(row(G, "G4442").count, 1000);
  assert.strictEqual(row(G, "G5484").hasCount, false);  // charis wasn't in the panel family
  assert.strictEqual(row(G, "G5484").count, null);
});

test("core head is marked; set-aside boundary is carried on the group", () => {
  assert.strictEqual(row(G, "G4442").core, true);
  assert.strictEqual(row(G, "G4448").core, false);
  assert.strictEqual(G.set_aside, 2);
});

test("no answer-scope word is dropped (Hebrew supplement the panel lacked)", () => {
  assert.ok(row(H, "H784"), "esh must appear even though the panel had no Hebrew group");
});

console.log("\n" + n + " passed");
