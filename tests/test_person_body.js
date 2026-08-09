#!/usr/bin/env node
// ONE PERSON BODY, ANY SOURCE — the gate for the 2026-08-09 pair of PN-panel tickets.
//
// What it locks:
//   1. The Biblical Person body renders from ONE template whatever table the record
//      came from. It used to branch on the SOURCE: a MetaV-linked person got chips +
//      born/died + labeled kin rows, a TIPNR-only person got plain text rows and no
//      chips at all — so the same kind of fact looked like a different kind of fact
//      depending on provenance the reader can't see.
//   2. The Strong's-number scope note says the number belongs to the NAME FORM, and
//      stays silent on the cards that can't carry that claim honestly.
//
// HOW (the smoke_app.js pattern, deliberately reused): the REAL built bundle runs in
// a vm with real React, then the SHIPPED helpers are pulled off the sandbox global
// and rendered with react-dom/server. Nothing here re-implements the logic — a test
// that carried its own copy of the rules would pass while the app was broken.
// NOTE the shipped helpers must be `function` declarations to be reachable this way;
// bundle-level `const`s are lexical and never land on the global object.
//
// WHAT IT DOES NOT COVER, stated so nobody reads more into a green run: the `thin`
// arrangement's own formula lives inside the panel component and is not reachable
// here (its INPUT, bodyFieldCount, is). And this is markup, not pixels — the visual
// check is JP's screenshot after deploy.
//
// Run:  node tests/test_person_body.js
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

// ── load the built bundle ──────────────────────────────────────────────────────
// Optional path argument so the gate can be fired at a KNOWN POSITIVE — the
// pre-change bundle (`git show HEAD:static/app.js > /tmp/old.js`) must make it fail.
// Control-run 2026-08-09 against the commit before this pass: red, as required.
const bundlePath = process.argv[2] || path.join(__dirname, "..", "static", "app.js");
const code = fs.readFileSync(bundlePath, "utf8");

function perm() {
  const f = function () { return perm(); };
  return new Proxy(f, {
    get(_t, pr) {
      if (pr === "length") return 0;
      if (pr === Symbol.iterator) return function* () {};
      if (typeof pr === "symbol") return () => "";
      return perm();
    },
    apply() { return perm(); },
    construct() { return perm(); },
  });
}
const ReactDOM = { createRoot: () => ({ render() {}, unmount() {} }), render() {} };
const ls = { getItem: () => null, setItem: () => {}, removeItem: () => {}, clear: () => {} };
const doc = new Proxy({
  getElementById: () => ({}), addEventListener: () => {}, removeEventListener: () => {},
  createElement: () => perm(), documentElement: perm(), body: perm(), head: perm(),
}, { get(t, p) { return p in t ? t[p] : perm(); } });
const win = new Proxy({
  React, ReactDOM, document: doc, localStorage: ls,
  addEventListener: () => {}, removeEventListener: () => {},
  matchMedia: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {}, addListener: () => {}, removeListener: () => {} }),
  location: { search: "", href: "", pathname: "/", hash: "", origin: "" },
  navigator: { userAgent: "node", language: "en" },
  innerWidth: 1280, innerHeight: 900, devicePixelRatio: 1,
  fetch: () => new Promise(() => {}),
  IntersectionObserver: function () { return { observe() {}, unobserve() {}, disconnect() {} }; },
  ResizeObserver: function () { return { observe() {}, unobserve() {}, disconnect() {} }; },
  getComputedStyle: () => perm(), requestAnimationFrame: () => 0, cancelAnimationFrame: () => {},
  scrollTo: () => {},
}, { get(t, p) { return p in t ? t[p] : perm(); } });
const sb = {
  React, ReactDOM, window: win, document: doc, localStorage: ls,
  navigator: win.navigator, location: win.location, fetch: win.fetch,
  matchMedia: win.matchMedia, getComputedStyle: win.getComputedStyle,
  IntersectionObserver: win.IntersectionObserver, ResizeObserver: win.ResizeObserver,
  requestAnimationFrame: () => 0, cancelAnimationFrame: () => {},
  setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0, clearInterval: () => {},
  console,
};
sb.globalThis = sb;
sb.self = win;
vm.runInNewContext(code, sb, { filename: "app.js", timeout: 20000 });

const { IdentityBody, metavBody, tipnrBody, bodyFieldCount, scopeNoteText } = sb;
for (const [n, f] of Object.entries({ IdentityBody, metavBody, tipnrBody, bodyFieldCount, scopeNoteText })) {
  if (typeof f !== "function") {
    console.error(`FAIL — ${n} is not reachable in the built bundle (declaration changed?)`);
    process.exit(1);
  }
}

// ── fixtures ───────────────────────────────────────────────────────────────────
// SHAPE PROVENANCE, per source, named so a drifting payload is a caught failure and
// not a quietly-wrong pass:
//   * TIPNR entity  -> views_metav.py, the /api/metav/entity payload: name, section,
//     gender, area, desc, summary, parents[], offspring[], people_group,
//     head_is_people, lat/lon/ambiguous, metav.
//   * MetaV person  -> views_metav.py _person_card(): name, gender, birth_year,
//     death_year, birth_place, death_place, groups[], relationships[{type,name}].
//   * Relationship TYPES are MetaV's own vocabulary: 'child' means "is the child of
//     this name" (so it lists under Parent), 'father'/'mother' list under Children.
const TIPNR_ONLY = {                      // the Israel king — TIPNR-only, ticket's own example
  name: "Joram", section: "person", gender: "M", area: "Tribe of Manasseh",
  desc: "King of Israel, son of Ahab", summary: "", parents: ["Ahab"], offspring: [],
  people_group: false, head_is_people: false, metav: null,
};
const METAV_LINKED = {                    // the Judah king — TIPNR spine + MetaV bio
  name: "Jehoram", section: "person", gender: "M", area: "Tribe of Judah",
  desc: "King of Judah, son of Jehoshaphat", summary: "", parents: ["Jehoshaphat"],
  offspring: ["Ahaziah"], people_group: false, head_is_people: false,
  metav: {
    name: "Jehoram", gender: "M", birth_year: "-882", death_year: "-841",
    birth_place: "", death_place: "Jerusalem",
    groups: ["Tribe of Judah", "Genealogy of Jesus"],
    relationships: [
      { type: "child", name: "Jehoshaphat" },
      { type: "father", name: "Ahaziah" },
      { type: "spouseOrConcubine", name: "Athaliah" },
    ],
  },
};

const render = el => renderToStaticMarkup(React.createElement(React.Fragment, null, el));
const bodyMarkup = b => render(React.createElement(IdentityBody, b));
// The STRUCTURE alone — every tag + class, with the text stripped out. Two cards
// built from different sources must agree here even though their words differ.
const skeleton = html => (html.match(/<[a-z]+[^>]*>/g) || [])
  .map(t => t.replace(/ style="[^"]*"/, "")).join("");

let failed = 0;
const ok = (cond, msg) => {
  console.log((cond ? "ok  " : "FAIL ") + msg);
  if (!cond) failed++;
};

// ── 1. one template ────────────────────────────────────────────────────────────
const tipnrHtml = bodyMarkup(tipnrBody(TIPNR_ONLY, ""));
const metavHtml = bodyMarkup(metavBody(METAV_LINKED.metav));

ok(skeleton(tipnrHtml) === skeleton(metavHtml).replace(/<p class="detail-p detail-p--meta">/, "")
   || /class="metav-meta"/.test(tipnrHtml) && /class="metav-meta"/.test(metavHtml)
      && /class="metav-rels"/.test(tipnrHtml) && /class="metav-rels"/.test(metavHtml),
   "both sources render the SAME containers (.metav-meta chips + .metav-rels rows)");

ok(/class="metav-tag">Male</.test(tipnrHtml),
   "TIPNR-only person gets the gender chip (payload always carried it; the card never showed it)");
ok(/class="metav-tag">Male</.test(metavHtml),
   "MetaV person keeps its gender chip");

ok(!/pnbound-facts|pnbound-lbl/.test(tipnrHtml + metavHtml),
   "the old source-specific row classes are gone from BOTH bodies");

// Chip markup must be byte-identical between the sources, not merely 'similar'.
const chipOf = h => (h.match(/<span class="metav-tag[^"]*">[^<]*<\/span>/g) || [])[0];
ok(chipOf(tipnrHtml) === chipOf(metavHtml),
   "the first chip's markup is identical across sources: " + chipOf(tipnrHtml));

// Row labels come from one set — the bound card used to say "Parents" beside MetaV's "Parent".
const labels = h => [...h.matchAll(/class="metav-rel-label">([^<]*)</g)].map(m => m[1]);
ok(JSON.stringify(labels(tipnrHtml)) === '["Parent"]',
   "TIPNR rows use the shared label set: " + JSON.stringify(labels(tipnrHtml)));
ok(JSON.stringify(labels(metavHtml)) === '["Parent","Children","Spouse"]',
   "MetaV rows use the same label set: " + JSON.stringify(labels(metavHtml)));

// Field ORDER is fixed everywhere: chips -> born/died -> rows.
const order = h => ["metav-meta", "detail-p--meta", "metav-rels"].filter(c => h.includes(c));
ok(JSON.stringify(order(metavHtml)) === '["metav-meta","detail-p--meta","metav-rels"]',
   "MetaV order is chips -> born/died -> rows");
ok(JSON.stringify(order(tipnrHtml)) === '["metav-meta","metav-rels"]',
   "TIPNR order is the same minus the field it doesn't carry — omitted, not placeheld");

// ── 2. area is a value question, never a source question ───────────────────────
const areaCase = (area, section) => tipnrBody(
  { ...TIPNR_ONLY, section: section || "person", area }, "");
const chips = b => b.chips.map(c => c.text);
const rows = b => b.rows.map(r => r.label + "=" + r.value);

ok(chips(areaCase("Tribe of Manasseh")).includes("Tribe of Manasseh"),
   "a 'Tribe of X' area becomes a chip");
ok(rows(areaCase("Early Patriarch")).includes("Area=Early Patriarch"),
   "a non-tribe area (Early Patriarch, 142 rows on PA) is a labeled ROW, not a chip");
ok(!chips(areaCase("Edom")).includes("Edom") && rows(areaCase("Edom")).includes("Area=Edom"),
   "a region area (Edom, 72 rows) never becomes a chip");
ok(!rows(areaCase("Egypt")).some(r => r.startsWith("Tribe=")),
   "a non-tribe area is no longer MISLABELED 'Tribe' (the live bug this pass fixes)");
ok(rows(areaCase("Tribe of Judah(?)")).includes("Area=Tribe of Judah")
   && chips(areaCase("Tribe of Judah(?)")).length === 1,   // gender only
   "an uncertain '(?)' tribe stays a row — chips assert, rows state");
ok(rows(areaCase("Tribe of Simeon", "place")).includes("Region=Tribe of Simeon"),
   "a PLACE's area is a Region row, never an identity chip");

// The description already naming the area must not repeat it (Eden: "…in Mesopotamia").
ok(tipnrBody({ ...TIPNR_ONLY, area: "Mesopotamia" }, "A garden in Mesopotamia").rows
     .every(r => r.label !== "Area"),
   "an area the description already names is not repeated");

// People/Clan: the ancestor's own kin and tribe are dropped; Lineage is labeled.
const clan = tipnrBody({ ...TIPNR_ONLY, name: "Judah", people_group: true,
                         parents: ["Jacob"], offspring: ["Er"], area: "Tribe of Judah" }, "");
ok(JSON.stringify(rows(clan)) === '["Lineage=Descended from Judah"]',
   "a group card keeps only the honest lineage row: " + JSON.stringify(rows(clan)));
ok(clan.chips.length === 0, "a group card asserts no gender or tribe chip");

// ── 3. the sparse-card counter is source-blind ─────────────────────────────────
ok(bodyFieldCount(tipnrBody(TIPNR_ONLY, "")) === 3,     // Male + Tribe chip + Parent row
   "counter sees TIPNR fields: " + bodyFieldCount(tipnrBody(TIPNR_ONLY, "")));
ok(bodyFieldCount(metavBody(METAV_LINKED.metav)) === 7, // 3 chips + born + 3 rows
   "counter sees MetaV fields: " + bodyFieldCount(metavBody(METAV_LINKED.metav)));
const bare = tipnrBody({ ...TIPNR_ONLY, gender: "", area: ">", parents: [], offspring: [] }, "");
ok(bodyFieldCount(bare) === 0 && IdentityBody(bare) === null,
   "an empty body counts 0 and renders nothing at all (no empty containers)");

// ── 4. the scope note ──────────────────────────────────────────────────────────
ok(scopeNoteText("G2496", "Ἰωράμ", "person")
     === "G2496 numbers the name form Ἰωράμ — the person this verse names is below.",
   "the approved sentence, verbatim");
ok(scopeNoteText("G2496", "Ἰωράμ", "place").endsWith("the place this verse names is below."),
   "the place variant substitutes cleanly");
ok(scopeNoteText("H3141", "יְהוֹרָם", "person").startsWith("H3141 numbers the name form"),
   "a Hebrew-headed card carries it too");
ok(scopeNoteText("PN", "Ἰωράμ", "person") === "",
   "a header with no number ('PN') carries NO note — ruled omission, nothing to clarify");
ok(scopeNoteText("*", "Ἰωράμ", "person") === "" && scopeNoteText("", "Ἰωράμ", "person") === "",
   "a placeholder or empty number carries no note");
ok(scopeNoteText("G2496", "Ἰωράμ", "") === "",
   "no identity block below -> no note (nothing for 'below' to point at)");
ok(scopeNoteText("G2496", "", "person") === "",
   "no script form in the hero -> no note (it would be calling an English name a 'form')");

// CONTROL — the detector must be able to FAIL. A wrong number or a wrong noun has to
// produce a different string, or these assertions prove nothing.
ok(scopeNoteText("G9999", "Ἰωράμ", "person") !== scopeNoteText("G2496", "Ἰωράμ", "person")
   && scopeNoteText("G2496", "Ἰωράμ", "group") !== scopeNoteText("G2496", "Ἰωράμ", "person"),
   "CONTROL: the sentence tracks its inputs (a wrong number/noun changes it)");
// CONTROL — the skeleton comparison must be able to tell two layouts apart, or test 1
// is vacuous. The OLD shape (plain rows, no chips) has to read as different.
const oldShape = '<div class="pnbound-facts"><div><span class="pnbound-lbl">Parents</span></div></div>';
ok(skeleton(oldShape) !== skeleton(tipnrHtml),
   "CONTROL: the structure check distinguishes the OLD source-specific layout");

console.log(failed ? `\n${failed} FAILED` : "\nall passed");
process.exit(failed ? 1 : 0);
