#!/usr/bin/env node
// MOBILE LAYOUT HARNESS — serves the REAL committed bundle against stubbed server
// payloads so a phone-width layout can be MEASURED, not eyeballed.
//
// Why this exists: tests/ has logic tests + a render smoke gate, but nothing that LAYS
// OUT. Claims like "the last row hides behind the bar" or "something overflows sideways"
// are measurements (scrollWidth/getBoundingClientRect), and a measurement needs a real
// engine with real CSS. This boots static/app.js + static/styles.css + the local React
// UMD (all served from static/, no CDN) and lets a headless Chrome drive it at an
// asserted viewport.
//
// This is a TOOL, not a gate — it is deliberately NOT in the CI test list. It renders a
// surface; it doesn't assert. The assertions live in the per-surface tests.
//
// FIXTURE PROVENANCE (the standing rule: fixtures are shaped from the real server
// payloads, never from memory). Every shape below is derived from the PRODUCING code in
// this repo, cited per fixture:
//   * /api/ai-search payload  -> ai.py `_assemble_payload` return (the six top-level keys)
//   * a result verse          -> ai.py `_assemble_payload` verse_index build + the
//                                is_primary/is_additional tagging pass
//   * a verse's words         -> core.py `_serialize_word_core` + ai.py `_fetch_verse_words`
//   * key_strongs entries     -> ai.py `_stamp_rail_fields` (contested + alias_note)
//   * quota                   -> views_notes.py `ai_quota_status` return
// The VALUES are illustrative; the SHAPES (field names, nesting, types) are the payload's.
//
// Run:  node tests/mobile_harness.js [port]      then drive http://127.0.0.1:<port>/
"use strict";
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const PORT = Number(process.argv[2] || 8099);

// ── Fixtures ────────────────────────────────────────────────────────────────
// Word shape: core.py _serialize_word_core (english, english_head, strongs, strongs_base,
// greek_pos, bracket_id, italic_words, lemma, translit, is_pn) + ai.py _fetch_verse_words
// extras (italic:bool, is_function:bool, gloss, strongs_def, kjv_def, derivation).
const word = (o) => Object.assign({
  english: "", english_head: null, strongs: "", strongs_base: "", greek_pos: "N-NSF",
  bracket_id: null, italic_words: "", lemma: "", translit: "", is_pn: 0,
  italic: false, is_function: false, gloss: "", strongs_def: "", kjv_def: "", derivation: "",
}, o);

// Verse shape: ai.py _assemble_payload — verse_index entries carry ref/book/chapter/verse/
// words (+ text on the SQL path), and the tagging pass stamps is_primary/is_additional/
// is_thematic on every result.
const verse = (book, chapter, v, text, words, primary) => ({
  ref: `${book} ${chapter}:${v}`, book, chapter, verse: v, text,
  words: words || [], is_primary: !!primary, is_additional: !primary, is_thematic: false,
});

const PNEUMA = word({ english: "spirit", strongs: "G4151", strongs_base: "G4151",
  lemma: "πνεῦμα", translit: "pneuma", gloss: "spirit", kjv_def: "spirit, breath, wind" });

// /api/ai-search: ai.py _assemble_payload returns exactly these six keys.
const AI_SEARCH = {
  results: [
    verse("Joh", 4, 24, "God is spirit, and the ones worshiping him in spirit and truth must worship.",
      [word({ english: "God", strongs: "G2316", strongs_base: "G2316", lemma: "θεός", translit: "theos", gloss: "God" }), PNEUMA], true),
    verse("Gen", 1, 2, "And the earth was unseen and unfinished, and darkness was upon the abyss, and spirit of God bore upon the water.",
      [word({ english: "spirit", strongs: "H7307", strongs_base: "H7307", lemma: "רוּחַ", translit: "ruach", gloss: "spirit" })], true),
    verse("Rom", 8, 16, "The spirit itself testifies together with our spirit that we are children of God.", [PNEUMA], false),
  ],
  total: 3,
  grounded: true,
  explanation: "Across both testaments the word carries the plain sense of breath or wind before it carries anything else. In John 4:24 it stands as a predicate of God himself; in Genesis 1:2 the Hebrew רוּחַ moves over the water. The range is what the corpus shows — not a single settled English word.",
  // key_strongs: ai.py _stamp_rail_fields stamps `contested` + `alias_note` on each entry.
  key_strongs: [
    { strongs: "G4151", lemma: "πνεῦμα", translit: "pneuma", gloss: "spirit, breath, wind",
      count: 385, contested: true, alias_note: null },
    { strongs: "H7307", lemma: "רוּחַ", translit: "ruach", gloss: "spirit, breath, wind",
      count: 378, contested: false, alias_note: null },
    { strongs: "G2316", lemma: "θεός", translit: "theos", gloss: "God",
      count: 1343, contested: true, alias_note: { standard: ["G2316"] } },
  ],
  // panel: the computed distribution/lemma-family block (frontend CorpusPanel / _acWordGroups).
  panel: { groups: [
    { lang: "G", label: "Greek (NT / Greek OT)", max: 385, set_aside: 0, family: [
      { strongs: "G4151", lemma: "πνεῦμα", translit: "pneuma", gloss: "spirit", count: 385, core: true },
      { strongs: "G4154", lemma: "πνέω", translit: "pneo", gloss: "to blow", count: 7 },
    ] },
    { lang: "H", label: "Hebrew (OT)", max: 378, set_aside: 0, family: [
      { strongs: "H7307", lemma: "רוּחַ", translit: "ruach", gloss: "spirit", count: 378, core: true },
    ] },
  ] },
  // quota rides the response per-account: views_notes.py ai_quota_status.
  quota: { used: 1, limit: 3, remaining: 2 },
};

// /api/auth/me — the boot call AskCorpusView reads `ai_quota` off (52-ask-corpus.jsx:627).
// The path is the one the app ACTUALLY asks for, confirmed from the harness's own request
// log (__LEX_HARNESS__.asked), not from the route name in the Python.
const ME = { user: null, role: "user", ai_quota: { used: 1, limit: 3, remaining: 2 } };

// /api/books — views_library.py books_list() returns a LIST of {abbrev, name, chapters} in
// canonical order. The DESKTOP shell reads it on boot and indexes into it; handed an empty
// object it read index 0 of nothing and the whole app failed to mount (blank at 1400px —
// which reproduced on the COMMITTED bundle too, so it was always this, never a regression).
// A short canonical slice is enough to boot; the reader isn't under test here.
const BOOKS = [
  { abbrev: "Gen", name: "Genesis", chapters: 50 },
  { abbrev: "Exo", name: "Exodus", chapters: 40 },
  { abbrev: "Psa", name: "Psalms", chapters: 150 },
  { abbrev: "Isa", name: "Isaiah", chapters: 66 },
  { abbrev: "Mat", name: "Matthew", chapters: 28 },
  { abbrev: "Joh", name: "John", chapters: 21 },
  { abbrev: "Rom", name: "Romans", chapters: 16 },
  { abbrev: "Rev", name: "Revelation", chapters: 22 },
];

// /api/lexica/contested — 00-core.jsx reads `d.strongs` and builds a Set from it.
const CONTESTED = { strongs: ["G2316", "G4151"] };

// /api/chapter/<book>/<ch> — views_library.py chapter_text() returns a LIST of
// {verse, heading, prose, words}. DESKTOP mounts LibraryView alongside whatever tab is
// active, so an empty object here crashed the whole app before any other surface could
// render (withMarks -> arr.forEach). Mobile never showed it because it mounts only the
// active view. Same story as /api/books: a fixture gap, not a product bug.
const CHAPTER = [
  { verse: 1, heading: "The Word became flesh", prose: "In the beginning was the word, and the word was with God, and God was the word.",
    words: [word({ english: "In the beginning", strongs: "G1722", strongs_base: "G1722", lemma: "ἐν", translit: "en", is_function: true }),
            word({ english: "was", strongs: "G1510", strongs_base: "G1510", lemma: "εἰμί", translit: "eimi" })] },
  { verse: 2, heading: null, prose: "This one was in the beginning with God.", words: [PNEUMA] },
];

const FIXTURES = {
  "/api/auth/me": ME,
  "/api/ai-search": AI_SEARCH,
  "/api/books": BOOKS,
  "/api/lexica/contested": CONTESTED,
};

// Prefix-matched fixtures: routes that carry ids in the PATH (chapter, verse) rather than
// a query string. Exact-match FIXTURES wins; these catch the parameterised families.
const FIXTURE_PREFIXES = [
  ["/api/chapter/", CHAPTER],
  ["/api/kjv/chapter/", CHAPTER],
  ["/api/bsb/chapter/", CHAPTER],
];
const fixtureFor = (pathname) => {
  if (Object.prototype.hasOwnProperty.call(FIXTURES, pathname)) return FIXTURES[pathname];
  for (const [pre, val] of FIXTURE_PREFIXES) if (pathname.startsWith(pre)) return val;
  return undefined;
};

// ── The page ────────────────────────────────────────────────────────────────
// Loads the real bundle. `fetch` is stubbed BEFORE app.js so no call escapes to a server
// that isn't here; anything unfixtured resolves empty rather than hanging (a hang would
// leave the surface mid-render and every measurement would be of a half-drawn page).
// __LEX_HARNESS__ records what was asked for, so a read can prove the surface got its data.
const PAGE = (view, admin, bundle) => `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>
<title>Lexica mobile harness — ${view}${admin ? " (admin)" : ""}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,500;0,8..60,600;1,8..60,400&family=JetBrains+Mono:wght@400;500&display=block" rel="stylesheet"/>
<link rel="stylesheet" href="/static/styles.css"/>
</head>
<body>
<div id="root"></div>
<script>
  window.__LEX_HARNESS__ = { asked: [], fixtures: ${JSON.stringify(Object.keys(FIXTURES))} };
  try {
    localStorage.setItem("lexica.view.v1", ${JSON.stringify(view)});
    // The first-run tour (90-app.jsx: lexica_tour_seen) opens a CENTERED modal over the
    // whole surface. Left unseeded, every measurement is of the tour's scrim, not the
    // surface under it — a measured zero that means nothing. Seed it seen.
    localStorage.setItem("lexica_tour_seen", "1");
    // ?admin=1 — the ADMIN's chrome, which is not the plain reader's. 90-app.jsx gates two
    // extra mobile nav tabs on these two keys (owner -> Study, news key -> News), so an
    // admin's .mobile-tabs carries 7 tabs where a reader's carries 5. JP reviews as admin;
    // measuring a reader's nav and calling it his is measuring the wrong page.
    if (${admin ? "true" : "false"}) {
      localStorage.setItem("lexica.owner.v1", "1");
      localStorage.setItem("lexica.news.key.v1", "harness-key");
    } else {
      localStorage.removeItem("lexica.owner.v1");
      localStorage.removeItem("lexica.news.key.v1");
    }
  } catch (e) {}
  const _F = ${JSON.stringify(FIXTURES)};
  const _FP = ${JSON.stringify(FIXTURE_PREFIXES)};
  const _realFetch = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    const u = String(url).split("?")[0];
    window.__LEX_HARNESS__.asked.push(u);
    // Only the API is stubbed. Anything under /static/ is a REAL file on disk and must be
    // fetched for real — chronological.json is a 255KB shipped asset the Library nav indexes
    // into (chrono.passages[...]), and standing in an empty object for it crashed the whole
    // desktop app before any surface rendered. A stub that answers for files it has no
    // business answering for is not a fixture, it's a fault injector.
    if (u.indexOf("/api/") !== 0) return _realFetch(url, opts);
    let hit = Object.prototype.hasOwnProperty.call(_F, u) ? _F[u] : undefined;
    if (hit === undefined) { for (const [pre, val] of _FP) if (u.indexOf(pre) === 0) { hit = val; break; } }
    const body = hit !== undefined ? hit : {};
    // 00-core.jsx aiSearchStream BRANCHES on the content-type header: anything that isn't
    // text/event-stream takes the one-lump cache-hit path. Ask-search is served as a real
    // stream, so the stub must say so — otherwise the harness silently exercises a
    // different code path than production and the layout under test isn't the live one.
    const isStream = u === "/api/ai-search";
    return Promise.resolve({
      ok: true, status: 200,
      headers: { get: (h) => (String(h).toLowerCase() === "content-type"
        ? (isStream ? "text/event-stream" : "application/json") : null) },
      json: () => Promise.resolve(body),
      text: () => Promise.resolve(JSON.stringify(body)),
      // ai.py's generator yields _sse("panel"|"delta"|"done"). Replay that order so the
      // surface passes through the SAME states the reader sees: panel first, prose
      // streaming, then the authoritative done payload.
      body: { getReader: () => {
        const frames = [
          "event: panel\\ndata: " + JSON.stringify({ panel: body.panel || null }) + "\\n\\n",
          "event: delta\\ndata: " + JSON.stringify({ t: String(body.explanation || "") }) + "\\n\\n",
          "event: done\\ndata: " + JSON.stringify(body) + "\\n\\n",
        ];
        let i = 0;
        return { read: () => (i >= frames.length
          ? Promise.resolve({ done: true, value: undefined })
          : Promise.resolve({ done: false, value: new TextEncoder().encode(frames[i++]) })) };
      } },
    });
  };
</script>
<script src="/static/react.production.min.js"></script>
<script src="/static/react-dom.production.min.js"></script>
<script src="${bundle === "head" ? "/head-bundle.js" : "/static/app.js"}"></script>
</body>
</html>`;

// ── Server ──────────────────────────────────────────────────────────────────
const TYPES = { ".js": "application/javascript", ".css": "text/css", ".json": "application/json",
                ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon" };

http.createServer((req, res) => {
  const url = new URL(req.url, "http://127.0.0.1");
  if (url.pathname.startsWith("/static/")) {
    const file = path.join(ROOT, url.pathname.replace(/^\/+/, ""));
    if (!file.startsWith(path.join(ROOT, "static"))) { res.writeHead(403).end(); return; }
    fs.readFile(file, (err, buf) => {
      if (err) { res.writeHead(404).end("no " + url.pathname); return; }
      res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
      res.end(buf);
    });
    return;
  }
  if (url.pathname.startsWith("/api/")) {
    const hit = fixtureFor(url.pathname);
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(hit !== undefined ? hit : {}));
    return;
  }
  // ?bundle=head — serve the COMMITTED bundle instead of the working one. This is the A/B:
  // when a surface breaks, it separates "my change broke it" from "the harness never ran it"
  // (a desktop blank once read as a regression when the same blank happened without the
  // change at all). Same page, same fixtures, only the bundle swaps.
  if (url.pathname === "/head-bundle.js") {
    require("child_process").execFile("git", ["show", "HEAD:static/app.js"],
      { cwd: ROOT, maxBuffer: 64 * 1024 * 1024 }, (err, stdout) => {
        if (err) { res.writeHead(500).end("// git show failed: " + err.message); return; }
        res.writeHead(200, { "Content-Type": "application/javascript" });
        res.end(stdout);
      });
    return;
  }
  const view = url.searchParams.get("view") || "corpus";
  const admin = url.searchParams.get("admin") === "1";
  const bundle = url.searchParams.get("bundle") || "working";
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(PAGE(view, admin, bundle));
}).listen(PORT, "127.0.0.1", () => {
  console.log("mobile harness on http://127.0.0.1:" + PORT + "/?view=corpus");
  console.log("views: library | lexicon | corpus | notes | study | news | about");
  console.log("add &admin=1 for the admin's chrome (7 mobile nav tabs, not 5)");
});
