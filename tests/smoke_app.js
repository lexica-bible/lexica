#!/usr/bin/env node
// SMOKE GATE — render the built bundle with REAL React to catch blank-site
// reference errors (use-before-declare / TDZ, undefined globals) that the pure
// Node logic tests never see because they don't evaluate the components.
//
// Why this exists: a Phase-4 edit put `abpMode` (which reads `extraEnglish`)
// ABOVE `extraEnglish`'s declaration in LibraryView. Every unit test passed, but
// the live site was blank — LibraryView threw "can't access 'extraEnglish' before
// initialization" the instant React rendered it. Logic tests can't catch that.
//
// How (robust, not stub-fragile): the bundle gets the REAL React + real hooks.
// Browser globals are permissively stubbed only so the module can LOAD (top-level
// code + the mount line). The bundle's own mount —
//   ReactDOM.createRoot(document.getElementById("root")).render(<App/>)
// — is redirected to react-dom/server renderToStaticMarkup, which synchronously
// runs every component body (App -> Header -> LibraryView -> ...) with real hooks.
// Because the hooks are real, only GENUINE bugs surface — a small change in the
// stubs can't flip the result the way a fake shallow renderer could. A component's
// variable declarations run at the TOP of its body, so a TDZ throws before any
// data access. We FAIL on a ReferenceError; other errors (missing data under the
// stubs) are reported as a non-fatal note.
//
// Run:  node tests/smoke_app.js            (uses static/app.js)
//       node tests/smoke_app.js <path>     (check a specific bundle)
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

const bundle = process.argv[2] || path.join(__dirname, "..", "static", "app.js");
const code = fs.readFileSync(bundle, "utf8");

// Permissive stub: any property/call returns another permissive stub, so top-level
// browser access (window.location.search.split(...), etc.) never throws while the
// module loads. Real rendering is done by React, not these.
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

let renderError = null;
// ReactDOM stub: createRoot(...).render(el) does a real server render of el, which
// executes the whole component tree synchronously. Capture whatever it throws.
const ReactDOM = {
  createRoot: () => ({
    render(el) {
      try { renderToStaticMarkup(el); }
      catch (e) { renderError = e; }
    },
    unmount() {},
  }),
  render(el) {
    try { renderToStaticMarkup(el); } catch (e) { renderError = e; }
  },
};

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

let loadError = null;
try {
  vm.runInNewContext(code, sb, { filename: "app.js", timeout: 20000 });
} catch (e) {
  loadError = e;
}

// A ReferenceError from EITHER the module load or the render is the blank-site
// class. NOTE: the error is thrown inside the vm sandbox, so its constructor is a
// DIFFERENT realm's ReferenceError — `instanceof ReferenceError` (host) is false.
// Match on the error NAME, which is realm-agnostic.
const isRef = (e) => !!e && e.name === "ReferenceError";
const refError = (isRef(loadError) && loadError) || (isRef(renderError) && renderError) || null;

if (refError) {
  console.error("SMOKE FAIL — reference error while rendering the bundle (blank-site class):");
  console.error("  " + refError.message);
  process.exit(1);
}
if (loadError) {                       // a non-Reference load error is a real problem too
  console.error("SMOKE FAIL — bundle threw while loading:");
  console.error("  " + (loadError && loadError.message));
  process.exit(1);
}
if (renderError) {
  // Non-Reference render error: the tree executed but hit a data/DOM gap under the
  // stubs. Not the blank-site class — report it so it's visible, but don't fail.
  console.log("ok  smoke: no reference/TDZ error (render stopped on a non-fatal stub gap: "
    + String(renderError && renderError.message).slice(0, 80) + ")");
  process.exit(0);
}
console.log("ok  smoke: bundle renders with no reference/TDZ errors");
