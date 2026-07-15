#!/usr/bin/env node
// NOTES INSPECT — the anchored-verse panel's two pure decisions:
//   1. how many verses the chapter has (drives whether an "after" neighbour exists)
//   2. which verses render, and which of them are the note's OWN text vs context
//
// Both were shipped broken (fixed 2026-07-15):
//   * the chapter reply was read as `d.verses`, but /api/chapter returns a BARE LIST
//     (views_library.py:268) -> the after-neighbour never rendered.
//   * only `start.verse` was read -> a multi-verse note showed its first verse only, while
//     the label still said "John 4:21-23".
//
// CONTROL-TESTED (the standing rule: a detector must fire on a known positive before a zero
// from it means anything). The LEGACY section below transcribes the shipped-broken logic and
// asserts these expectations FAIL against it — so a green here is evidence the test can see
// the bug, not evidence that nothing is being checked.
"use strict";
require.extensions[".jsx"] = require.extensions[".js"];
const path = require("path");
const { noteInspLastVerse, noteInspRows } =
  require(path.join(__dirname, "..", "static", "src", "34-notes-logic.jsx"));

let failures = 0;
const eq = (actual, expected, name) => {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a === e) { console.log("ok  " + name); return true; }
  console.log("FAIL " + name + "\n  expected " + e + "\n  actual   " + a);
  failures++; return false;
};

// The shape views_library.py:268 actually produces: a bare list of {verse, heading, prose, words}.
const chapter = (n) => Array.from({ length: n }, (_, i) => ({ verse: i + 1, heading: null, prose: "", words: [] }));
const verses = (rows) => rows.map((r) => r.verse);
const kinds = (rows) => rows.map((r) => r.kind);

// ── 1. the chapter's last verse ──────────────────────────────────────────────
// John 4 really has 54 verses (abp_texts/abp_nt_texts/abp_john.txt).
eq(noteInspLastVerse(chapter(54), 24), 54, "last verse: reads a BARE LIST (the shipped bug)");
eq(noteInspLastVerse([], 24), 24, "last verse: empty chapter falls back to the anchor");
eq(noteInspLastVerse(null, 24), 24, "last verse: a failed fetch falls back to the anchor");
eq(noteInspLastVerse(undefined, 24), 24, "last verse: undefined falls back to the anchor");
// Guard the ACTUAL bug shape: an object with a .verses key must NOT be honoured, or a future
// endpoint change would silently resurrect the old reading.
eq(noteInspLastVerse({ verses: chapter(54) }, 24), 24, "last verse: {verses:[...]} is NOT the shape -> falls back");
eq(noteInspLastVerse(chapter(3), 2), 3, "last verse: short chapter");

// ── 2. which rows render ─────────────────────────────────────────────────────
// Single verse, mid-chapter: one neighbour each side.
eq(verses(noteInspRows(24, 24, 54)), [23, 24, 25], "single: neighbour each side");
eq(kinds(noteInspRows(24, 24, 54)), ["near", "anchor", "near"], "single: only the anchor is the note's text");

// Multi-verse: EVERY verse in the range is the note's own text; one neighbour each side of the
// WHOLE range, not per verse.
eq(verses(noteInspRows(21, 23, 54)), [20, 21, 22, 23, 24], "range: whole range + one neighbour each side");
eq(kinds(noteInspRows(21, 23, 54)), ["near", "anchor", "anchor", "anchor", "near"], "range: every verse in range is anchor");

// Edges: no phantom row before verse 1 or past the chapter's end.
eq(verses(noteInspRows(1, 1, 54)), [1, 2], "edge: verse 1 has no before-neighbour");
eq(verses(noteInspRows(54, 54, 54)), [53, 54], "edge: last verse has no after-neighbour");
eq(verses(noteInspRows(1, 54, 54)), Array.from({ length: 54 }, (_, i) => i + 1), "edge: whole chapter, no neighbours either side");
eq(verses(noteInspRows(30, 30, null)), [29, 30], "edge: unknown chapter length hides the after-neighbour");
// Defensive: a reversed pair (imported / hand-edited note) must not render an empty range.
eq(verses(noteInspRows(23, 21, 54)), [20, 21, 22, 23, 24], "defensive: reversed start/end still renders the range");
// A note whose end is missing entirely (older note, or the verse-number menu path) reads as single.
eq(verses(noteInspRows(24, 24, 54)), [23, 24, 25], "defensive: end === start reads as a single verse");

// ── CONTROL: the expectations must FAIL against the shipped-broken logic ─────
// Transcribed from 35-notes.jsx as it shipped (`d.verses`; rows off start.verse only).
const legacyLastVerse = (d, fallback) => {
  const vs = (d && d.verses) || [];
  return vs.length ? Math.max(...vs.map((x) => x.verse)) : fallback;
};
const legacyRows = (v, maxVerse) => {
  const rows = [];
  if (v > 1) rows.push({ verse: v - 1, kind: "near" });
  rows.push({ verse: v, kind: "anchor" });
  if (maxVerse != null && v < maxVerse) rows.push({ verse: v + 1, kind: "near" });
  return rows;
};
const control = (name, cond) => {
  if (cond) { console.log("ok  CONTROL " + name); return; }
  console.log("FAIL CONTROL " + name + " — the test would NOT have caught the bug it exists for");
  failures++;
};
// Defect 1: legacy reads a bare list as empty, so it falls back and the after-neighbour dies.
control("legacy misreads the bare list", legacyLastVerse(chapter(54), 24) === 24);
control("legacy therefore drops the after-neighbour",
  JSON.stringify(verses(legacyRows(24, legacyLastVerse(chapter(54), 24)))) === JSON.stringify([23, 24]));
// Defect 2: legacy truncates a 21-23 note to verse 21.
control("legacy truncates a range to its first verse",
  JSON.stringify(verses(legacyRows(21, 54))) === JSON.stringify([20, 21, 22]));
// ...and the verse it DOES show past the range is dimmed context, not the note's own text —
// which is why fixing defect 1 alone would have mislabelled the note's own verse 22 as "near".
control("legacy would mislabel the note's own next verse as context",
  legacyRows(21, 54).find((r) => r.verse === 22).kind === "near");

console.log(failures ? `\n${failures} failed` : "\nall passed");
process.exit(failures ? 1 : 0);
