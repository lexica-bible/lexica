#!/usr/bin/env node
// Chronological reading-plan reconcile — regression lock for the "day fails to open" bug.
//
// Opening a plan day loads its FIRST passage, then the reader reports its spot back as a
// bare (book, chapter) with no verse. If that report resolves to a DIFFERENT passage than
// the one just opened, the reader snaps away and the day never opens. This happens whenever
// a day's first passage starts mid-chapter in a chapter an earlier passage also covers
// (141 of 365 days — day 220 = Zephaniah 2:8 is the one that surfaced the bug).
//
// The contract: for EVERY day, reconciling the reader's (book, chapter, no-verse) report
// while sitting on that day's first passage must KEEP that passage. Logic lives in
// static/src/57-chrono-logic.jsx (bundled into app.js AND required here) — LibraryView
// calls the SAME chronoReconcile, so this test guards the app, not a copy.
//
// Run from repo root:  node tests/test_chrono_reconcile.js
"use strict";
const assert = require("assert");
const fs = require("fs");
const path = require("path");

require.extensions[".jsx"] = require.extensions[".js"];
const { chronoReconcile, chronoPassageForRef } =
  require(path.join(__dirname, "..", "static", "src", "57-chrono-logic.jsx"));

const chrono = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "static", "chronological.json"), "utf8"));
const P = chrono.passages, days = chrono.days;

let n = 0;
const test = (name, fn) => { fn(); n++; console.log("ok  " + name); };

// The core invariant, across the WHOLE plan: click day D -> land on its first passage F ->
// reader reports (F.book, F.start_ch) with no verse -> reconcile must return F (not an
// earlier passage covering that chapter).
test("every day's first passage survives the no-verse reader-position reconcile", () => {
  const broken = [];
  for (const d of days) {
    const first = (d.pos || []).map(q => P[q - 1]).filter(Boolean)[0];
    if (!first) continue;
    const landed = chronoReconcile(P, first.pos, first.book, first.start_ch, null);
    if (!landed || landed.pos !== first.pos) {
      broken.push(`Day ${d.day} (${first.label}) -> ` +
        (landed ? `${landed.label} [pos ${landed.pos}]` : "null"));
    }
  }
  assert.deepStrictEqual(broken, [],
    "days dragged off their first passage by the reconcile:\n  " + broken.join("\n  "));
});

// Day 220's actual data — the reported case, pinned explicitly.
test("day 220 (Zephaniah 2:8-3:20) opens and is NOT snapped back to day 219", () => {
  const day220 = days.find(d => d.day === 220);
  const first = P[day220.pos[0] - 1];
  assert.strictEqual(first.label, "Zephaniah 2:8–3:20");
  const landed = chronoReconcile(P, first.pos, "Zep", 2, null);   // reader reports Zep ch2
  assert.strictEqual(landed.pos, first.pos);                       // stays on day 220's head
  // Without the guard this is what went wrong — the bare lookup finds day 219's tail:
  const bare = chronoPassageForRef(P, "Zep", 2, null);
  assert.strictEqual(bare.label, "Zephaniah 1:1–2:7");        // passage 565, day 219
});

// A real verse jump (highlight set) must still narrow a split chapter precisely, even when
// the current passage also covers that chapter.
test("a verse jump within a split chapter still resolves by verse (guard doesn't hijack it)", () => {
  // Sitting on day 220's head (Zep 2:8-3:20), jump to Zep 2:3 (in day 219's part of ch2).
  const day220 = days.find(d => d.day === 220);
  const head = P[day220.pos[0] - 1];
  const landed = chronoReconcile(P, head.pos, "Zep", 2, 3);
  assert.strictEqual(landed.label, "Zephaniah 1:1–2:7");      // verse 3 lives in 565
});

console.log(`\n${n} tests passed`);
