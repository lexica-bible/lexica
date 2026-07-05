#!/usr/bin/env node
// Library word-order — parity + anchor lock for the chip/mode-three split.
//
// Guards the two pure order helpers in static/src/56-library-order-logic.jsx
// (bundled into app.js AND required here — the app calls the SAME copy, so this
// tests the app, not a duplicate):
//   getEnglishOrderWords — prose (and, from Phase 3, chip) English reading order
//   groupForGreekMode     — chip grouping in faithful ABP / mode-three order
//
// PARITY GATE (mandatory before the Phase-3 chip flip): a committed baseline
// (tests/fixtures/order/expected.json) pins the order output for real chapter
// data — John 1, Genesis 1, 1 Chronicles 1 (OT LXX, bracket-heavy), plus the
// 2 Ki 23:29 anchor fixture. Phase 2 = extract only, so the baseline captures
// CURRENT behavior; prose must stay byte-identical through Phase 3, and any chip
// change must be a bracket reorder and nothing else.
//
// 2 Ki 23:29 is an ANCHOR in every phase's test set: it exercises the PN Strong's
// path (strongs_base kept verbatim — H6547, not synthesized 'G...'), the name-only
// fallback (Pharaoh/Necho/Egypt/Josiah/Megiddo have no Greek), and two bracket
// groups that reorder with Hebrew-numbered names inside.
//
// Run:            node tests/test_library_order.js
// Regenerate:     node tests/test_library_order.js --write   (after an INTENDED change)
"use strict";
const assert = require("assert");
const fs = require("fs");
const path = require("path");

require.extensions[".jsx"] = require.extensions[".js"];
const { getEnglishOrderWords, groupForGreekMode, orderBracketGroupWords, greekLineForWord } =
  require(path.join(__dirname, "..", "static", "src", "56-library-order-logic.jsx"));

const SNAP = path.join(__dirname, "snapshots");
const FIX  = path.join(__dirname, "fixtures", "order");
const readJson = (p) => JSON.parse(fs.readFileSync(p, "utf8"));

// Fixture verses: real chapter payloads (as the /api/chapter endpoint returns) +
// the hand-captured 2 Ki 23:29 anchor. Each entry -> a list of {verse, words}.
function fixtureVerses() {
  const out = [];
  for (const f of ["api__chapter__Joh__1.json", "api__chapter__Gen__1.json", "api__chapter__1Ch__1.json"]) {
    const chap = readJson(path.join(SNAP, f));
    for (const v of chap) out.push({ src: f, verse: v.verse, words: v.words });
  }
  const ki = readJson(path.join(FIX, "2ki_23_29.json"));
  out.push({ src: "2ki_23_29.json", verse: 29, words: ki.words });
  return out;
}

// Compact, stable signature of the order output for one verse. Prose = the english
// reading sequence (drop empty-gloss tokens, as the renderer does). Chip = each
// group's positions in RENDER order: Phase 3 reorders each bracket group by the
// shared reorder core (orderBracketGroupWords), exactly as 59c-library-render.jsx
// now does; non-bracket words keep source position.
function signature(words) {
  const prose = getEnglishOrderWords(words)
    .map(w => (w.english || "").trim())
    .filter(Boolean);
  const chip = groupForGreekMode(words).map(g =>
    g.isBracket
      ? { b: g.bid, pos: orderBracketGroupWords(g.words).map(w => w.position) }
      : { pos: g.word.position });
  return { prose, chip };
}

function buildBaseline() {
  const map = {};
  for (const v of fixtureVerses()) map[`${v.src}#${v.verse}`] = signature(v.words);
  return map;
}

const EXPECTED = path.join(FIX, "expected.json");

if (process.argv.includes("--write")) {
  fs.writeFileSync(EXPECTED, JSON.stringify(buildBaseline(), null, 1) + "\n");
  console.log("wrote " + EXPECTED);
  process.exit(0);
}

let n = 0;
const test = (name, fn) => { fn(); n++; console.log("ok  " + name); };

// 1. PARITY: order output matches the committed baseline for every fixture verse.
test("order helpers reproduce the committed baseline (prose + chip)", () => {
  const expected = readJson(EXPECTED);
  const actual = buildBaseline();
  assert.deepStrictEqual(actual, expected);
});

// 2. ANCHOR — 2 Ki 23:29 bracket reorders resolve to natural English.
test("2Ki 23:29 bracket groups reorder to English (Josiah the king went / Necho killed him)", () => {
  const ki = readJson(path.join(FIX, "2ki_23_29.json"));
  const ordered = getEnglishOrderWords(ki.words).map(w => (w.english || "").trim()).filter(Boolean);
  const joined = ordered.join(" ");
  assert.ok(joined.includes("Josiah the king went"), "bracket 1 -> 'Josiah the king went': " + joined);
  assert.ok(joined.includes("Necho killed him"),     "bracket 2 -> 'Necho killed him': " + joined);
});

// 3. ANCHOR — proper-noun tokens keep strongs_base VERBATIM through the reorder
//    (never synthesized to 'G'+strongs). Josiah = H2977, Necho = H5224.
test("2Ki 23:29 PN tokens keep Hebrew strongs_base verbatim through reorder", () => {
  const ki = readJson(path.join(FIX, "2ki_23_29.json"));
  const ordered = getEnglishOrderWords(ki.words);
  const josiah = ordered.find(w => w.english === "Josiah");
  const necho  = ordered.find(w => w.english === "Necho" && w.bracket_id === 2);
  assert.strictEqual(josiah.strongs_base, "H2977");
  assert.strictEqual(necho.strongs_base,  "H5224");
  // and the reorder preserves token identity — the '*' bare strongs rides along untouched
  assert.strictEqual(josiah.strongs, "*");
});

// 4. ANCHOR — the name-only Greek fallback source is present: every PN in the verse
//    has NO lemma and NO translit (so mode three must fall back to the English name).
test("2Ki 23:29 proper nouns carry no Greek (lemma+translit blank) — name-only fallback", () => {
  const ki = readJson(path.join(FIX, "2ki_23_29.json"));
  const pns = ki.words.filter(w => w.is_pn);
  assert.ok(pns.length >= 7, "expected the roster of PNs, got " + pns.length);
  for (const p of pns) {
    assert.ok(!p.lemma,    p.english + " unexpectedly has a lemma");
    assert.ok(!p.translit, p.english + " unexpectedly has a translit");
  }
});

// 5. Reorder never drops or duplicates a token (count in == count out), all fixtures.
test("getEnglishOrderWords is a permutation (no tokens lost or duplicated)", () => {
  for (const v of fixtureVerses()) {
    const out = getEnglishOrderWords(v.words);
    assert.strictEqual(out.length, v.words.length, `${v.src}#${v.verse} token count`);
    const inPos = v.words.map(w => w.position).sort((a,b)=>a-b);
    const outPos = out.map(w => w.position).sort((a,b)=>a-b);
    assert.deepStrictEqual(outPos, inPos, `${v.src}#${v.verse} same positions`);
  }
});

// ---- Phase 4: mode three (faithful ABP interlinear) --------------------------

// 6. FALLBACK CHAIN ORDER — the Greek line precedence is pinned explicitly:
//    inflected -> lemma -> English name (capitalized) -> none. This guards the
//    order so the future PN surface-form backfill slots into step 1 without drift.
test("greekLineForWord follows inflected -> lemma -> name -> none", () => {
  assert.deepStrictEqual(
    greekLineForWord({ inflected: "θεόν", lemma: "θεός", english: "God" }),
    { text: "θεόν", kind: "inflected" }, "inflected wins when present");
  assert.deepStrictEqual(
    greekLineForWord({ inflected: "", lemma: "θεός", english: "God" }),
    { text: "θεός", kind: "lemma" }, "lemma when no inflected");
  assert.deepStrictEqual(
    greekLineForWord({ inflected: "", lemma: "", english_head: "pharaoh" }),
    { text: "Pharaoh", kind: "name" }, "capitalized English name when no Greek");
  assert.deepStrictEqual(
    greekLineForWord({ inflected: "", lemma: "", english: "" }),
    { text: "", kind: "none" }, "nothing to show -> none (stays invisible)");
  // precedence holds even if a later source is 'better' — order is fixed, not best-of
  assert.strictEqual(greekLineForWord({ inflected: "ταις", lemma: "ὁ" }).kind, "inflected");
});

// 7. ANCHOR (2 Ki 23:29) — the Greek line each PN resolves to is the capitalized
//    English name, and the Strong's line is strongs_base VERBATIM (never 'G'+num).
test("2Ki 23:29 PN Greek line = capitalized name; Strong's stays Hebrew verbatim", () => {
  const ki = readJson(path.join(FIX, "2ki_23_29.json"));
  const byEng = (e) => ki.words.find(w => w.english === e);
  const pharaoh = byEng("Pharaoh");
  assert.deepStrictEqual(greekLineForWord(pharaoh), { text: "Pharaoh", kind: "name" });
  assert.strictEqual(pharaoh.strongs_base, "H6547");              // printed verbatim by the renderer
  assert.ok(!/^G/.test(pharaoh.strongs_base), "PN must never carry a G-prefix");
  // a Greek-bearing word still leads with its Greek, not the gloss
  const river = byEng("river");
  assert.deepStrictEqual(greekLineForWord(river), { text: "ποταμόν", kind: "inflected" });
});

// 8. EMPTY-ENGLISH ARTICLE — kept and continuous: it carries a Greek line (so it is
//    NOT dropped), while its English gloss is blank (the renderer holds the slot).
//    Gen 1 is full of these folded articles.
test("empty-English article tokens keep a Greek line (un-hidden, continuous)", () => {
  const gen = readJson(path.join(SNAP, "api__chapter__Gen__1.json"));
  const articles = [];
  for (const v of gen)
    for (const w of v.words)
      if (!(w.english || "").trim() && (w.lemma || w.inflected)) articles.push(w);
  assert.ok(articles.length >= 5, "expected folded articles in Gen 1, got " + articles.length);
  for (const w of articles) {
    const g = greekLineForWord(w);
    assert.ok(g.text, "folded article must show a Greek line");
    assert.notStrictEqual(g.kind, "none");
  }
  // a truly-empty '*' token (no Greek, no English) DOES drop out -> none
  assert.deepStrictEqual(
    greekLineForWord({ english: "", english_head: "", lemma: "", inflected: "", strongs_base: "*" }),
    { text: "", kind: "none" });
});

// 9. ANCHOR — mode three does NOT reorder brackets: the grouper yields source order,
//    which is what the interlinear renders (distinct from chip's English reorder).
test("2Ki 23:29 mode three keeps bracket source order (no reorder)", () => {
  const ki = readJson(path.join(FIX, "2ki_23_29.json"));
  const sorted = [...ki.words].sort((a, b) => a.position - b.position);
  const groups = groupForGreekMode(sorted).filter(g => g.isBracket);
  const b1 = groups.find(g => g.bid === 1);
  // source order is went(18) Josiah(19) the(20) king(21) — NOT reordered to "Josiah the king went"
  assert.deepStrictEqual(b1.words.map(w => w.english), ["went", "Josiah", "the", "king"]);
  // and the chip-mode reorder of the SAME group WOULD differ (proves the two modes diverge)
  assert.deepStrictEqual(orderBracketGroupWords(b1.words).map(w => w.english),
    ["Josiah", "the", "king", "went"]);
});

console.log(`\n${n} tests passed.`);
