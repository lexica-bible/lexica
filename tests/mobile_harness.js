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
//   * /api/news/meta          -> views_news.py `meta` return (:587) + `_reviewer` id shape
//   * /api/news/all           -> views_news.py `all_news` return (:570)
//   * a news card             -> views_news.py `_serialize` return + the `event`/`members`
//                                fields `_all_cards` attaches after it, + the `status`
//                                `all_news` re-attaches per reviewer
//   * thread keys/labels      -> views_news.py `THREAD_LABELS`
//   * the six Word-study endpoints + the three per-verse word routes -> the "Word study
//     (lexicon)" block below, each cited to its producer there (views_lexicon.py /
//     views_lexica.py + scripts/build_lexica_def.py / views_kjv.py / views_bsb.py / views_heb.py)
// The VALUES are illustrative; the SHAPES (field names, nesting, types) are the payload's.
// Two values are NOT free to be illustrative, because the code computes on them rather than
// printing them: a news thread KEY (it resolves through THREAD_LABELS) and any DATE (the feed's
// default window is a rolling 21 days off the clock — see the News block).
//
// NOTES is the one fixture with NO Python producer, on purpose — the notes store is
// browser-local (12-notes-store.jsx, localStorage "lexica.notes.v1"), so it is seeded into
// localStorage, not stubbed at /api/. Do NOT shape it from views_notes.py: `notes_sync`
// (views_notes.py:708) stores the client's blob OPAQUELY (`json.dumps(n)`) and hands the same
// blob back — it never authors a field, so the server is a round-tripper, not the producer.
// The producers are the CLIENT. Note there are TWO anchor writers, and they are not
// interchangeable — a note's shape depends on which one made it:
//   * a SINGLE-verse note     -> 12-notes-store.jsx `create()` (id/device/body/color/
//                                created/updated) merged over 60-library.jsx `verseAnchor()`
//                                (:1291-1295 — corpus/translation/book/bookName/chapter/
//                                start/end/snippet/refLabel). This is the VERSE-NUMBER MENU
//                                path: it stamps `start` and `end` to the SAME verse and
//                                `pos: null`, so it can only ever produce a single-verse note.
//   * a MULTI-verse note      -> the same `create()` over 60-library.jsx `resolveSelection()`
//                                (:1093-1102 — the DRAG-SELECT path). It resolves each edge of
//                                the selection to its own verse (:1057-1058), swaps them into
//                                order if the drag ran backwards (:1063-1066), and stores
//                                `start.verse` / `end.verse` SEPARATELY (:1098-1099) with real
//                                word positions in `pos`. `refLabel` comes out already a range
//                                — `book ch:startV–endV`, EN-DASH (:1073).
//                                Shape a range fixture from THIS, not from `verseAnchor()`:
//                                reading the single-verse writer and assuming it covers ranges
//                                is how you'd "confirm" that ranges aren't stored at all.
//   * `bookmark: true`        -> 60-library.jsx `vmBookmark` -> create({...a, bookmark: true})
//   * a journal page          -> 12-notes-store.jsx `createJournal()` (kind/title/body)
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

// /api/chapter/<book>/<ch> — views_library.py `chapter_text()` returns a BARE LIST of
// {verse, heading, prose, words} (views_library.py:268, `return jsonify([...])`). Keep it a
// list: the Library consumes it as one (60-library.jsx:444, `setVerses(data)`), and stubbing
// the shape a buggy caller *expects* would hide the bug instead of catching it.
// DESKTOP mounts LibraryView alongside whatever tab is active, so an empty object here crashed
// the whole app before any other surface could render (withMarks -> arr.forEach). Mobile never
// showed it because it mounts only the active view. Same story as /api/books.
//
// The chapter's LENGTH is load-bearing, not decoration: NoteVerseInspect derives the chapter's
// last verse from this reply to decide whether an "after" neighbour exists, so an invented
// length would decide a test's outcome. These are the REAL lengths, read out of the repo's own
// ABP source (abp_texts/ — pre-build, diagnosis-grade, which is all a verse COUNT needs):
//   grep -oE '^\(Joh 4:[0-9]+\)' abp_texts/abp_nt_texts/abp_john.txt | tail -1   -> 54
// Covered: every chapter this harness actually asks for (Gen/1 from the Library's boot, plus
// each chapter the NOTES seed anchors). An unknown chapter THROWS rather than inventing a
// length — a stand-in that quietly answers for a chapter it knows nothing about is how a
// fixture starts deciding results (the chronological.json lesson).
// The four extra chapters below (Exo/Isa/Mat/Rev) exist for the LEXICON fixture's occurrence
// spread — same rule, same source:
//   grep -oE '^\(Exo 1:[0-9]+\)'  abp_texts/abp_ot_texts/abp_exodus.txt     | tail -1  -> 22
//   grep -oE '^\(Isa 11:[0-9]+\)' abp_texts/abp_ot_texts/abp_isaiah.txt     | tail -1  -> 16
//   grep -oE '^\(Mat 3:[0-9]+\)'  abp_texts/abp_nt_texts/abp_matthew.txt    | tail -1  -> 17
//   grep -oE '^\(Rev 22:[0-9]+\)' abp_texts/abp_nt_texts/abp_revelation.txt | tail -1  -> 21
const CHAPTER_LEN = { "Gen/1": 31, "Exo/1": 22, "Joh/1": 51, "Joh/4": 54, "Rom/8": 39,
                      "Psa/104": 35, "Isa/11": 16, "Mat/3": 17, "Rev/22": 21 };

// One verse's worth of stand-in prose. The READER isn't under test here — what matters per row
// is that it carries the produced field names and that its verse number is real.
const chapterVerse = (v) => ({
  verse: v,
  heading: v === 1 ? "In the beginning" : null,
  prose: `Stand-in prose for verse ${v} — the harness measures layout, not the corpus.`,
  words: [word({ english: "word", strongs: "G3056", strongs_base: "G3056", lemma: "λόγος", translit: "logos" })],
});
const chapterFor = (book, ch) => {
  const n = CHAPTER_LEN[`${book}/${ch}`];
  if (!n) throw new Error(`mobile_harness: no real verse count for ${book} ${ch} — add it to ` +
    `CHAPTER_LEN from abp_texts/ rather than letting the fixture invent one.`);
  return Array.from({ length: n }, (_, i) => chapterVerse(i + 1));
};

// /api/verse-words/<book>/<ch>/<v> — views_library.py verse_words() returns {"words": [...]},
// NOT a bare list (that route and chapter_text() disagree ON PURPOSE; check the producer, don't
// pattern-match off its neighbour). VerseRow reads `d.words` and fetches per row, lazily.
// `{{v}}` is substituted with the requested verse on both sides. That marker earns its keep:
// each VerseRow fetches its OWN verse, so it proves in a measurement WHICH verses actually
// rendered — a range of identical rows can't tell you that.
// `italic: true` marks a TRANSLATOR-SUPPLIED word — views_library.py verse_words returns
// `"italic": bool(w["italic"])`, and every verse renderer turns it into `.lib-prose-italic`
// (the KJV/BSB branches in 50-corpus-results.jsx and the ABP prose path in
// 59c-library-render.jsx all use that one class). A supplied copula is the classic case: the
// Greek has no "is", so ABP prints it italic. Without one in the fixture, no verse rendered by
// this harness has any italics at all — and italic formatting can't be measured on a row that
// has none.
const VERSE_WORDS = { words: [
  word({ english: "God", strongs: "G2316", strongs_base: "G2316", lemma: "θεός", translit: "theos", gloss: "God" }),
  word({ english: "is", strongs: "G1510", strongs_base: "G1510", lemma: "εἰμί", translit: "eimi", is_function: true, italic: true }),
  word({ english: "spirit-v{{v}}", strongs: "G4151", strongs_base: "G4151", lemma: "πνεῦμα", translit: "pneuma", gloss: "spirit" }),
] };

// Precomputed so BOTH the server and the in-page stub resolve from ONE table (the page's stub
// is inlined JSON — it can't call these functions).
const CHAPTERS = {};
for (const k of Object.keys(CHAPTER_LEN)) { const [b, c] = k.split("/"); CHAPTERS[k] = chapterFor(b, c); }

// ── Word study (lexicon) ────────────────────────────────────────────────────
// Six endpoints, each shaped from its PRODUCER (sibling routes disagree on shape ON PURPOSE —
// /api/lexicon/lookup returns a bare list while /profile returns one object; read the producer,
// never the neighbour):
//   * /api/lexicon/lookup   -> views_lexicon.py lexicon_lookup (:465): BARE LIST of
//                              {strongs, lemma, translit, gloss} + `match` ("exact"/"contains")
//                              on the English/translit band (:524-531). Enrichment (*_glosses /
//                              *_totals) attaches ONLY when >1 rows survive (:478) — a lone
//                              exact hit skips it and the frontend auto-opens the word.
//   * /api/lexicon/english  -> views_lexicon.py lexicon_english (:630): BARE LIST, rows built by
//                              _emit (:1011-1022): {strongs, lemma, translit, count,
//                              abp_glosses, heb_glosses, kjv_glosses, bsb_glosses,
//                              abp_total, heb_total, kjv_total, bsb_total}. Each *_glosses is
//                              `_fold` output (:994-1008): [{gloss, count}] with `m: true` on
//                              the matched rendering and an optional trailing {trunc: true}
//                              marker; each *_total is a number or null (dict .get miss).
//   * /api/lexicon/profile  -> views_lexicon.py lexicon_profile return (:1256) — the 22 keys
//                              below, verbatim. Nested shapes: books rows {book, name,
//                              testament, count} (:1212-1214); gloss rows {gloss, count}
//                              (_fold_glosses, :246); related rows {strongs, lemma, translit,
//                              gloss} (_greek_cognates, :122 — [] for Hebrew, :1241);
//                              alias_note (contested_register.alias_note_for, :298 — null for
//                              an unaliased word); default_verses rows {book, chapter, verse}
//                              (_all_books_verses, :1375/:1409/:1445) + default_truncated bool.
//   * /api/lexicon/books    -> views_lexicon.py lexicon_books (:1339): {books: [same rows]}.
//   * /api/lexicon/verses   -> views_lexicon.py lexicon_verses — TWO SHAPES, ONE ENDPOINT:
//                              book=all (:1489) -> {verses: [{book, chapter, verse}],
//                              glosses: [], truncated}; a PICKED book has NO `truncated` key
//                              and rows that differ per corpus: ABP (:1631/:1641)
//                              {chapter, verse, words: [{w, h, i}], text}; KJV (:1608/:1618)
//                              {chapter, verse, words: [{w, h, i, punc}]}; HEB (:1518/:1521)
//                              and BSB (:1551/:1554) verse KEYS only {chapter, verse}.
//                              glosses = [{gloss, count}] sorted by -count.
//   * /api/lexica/<sid>     -> the STORED entry document. The producer is the WRITER,
//                              scripts/build_lexica_def.py `assemble` (:2229-2262) — the serve
//                              route (views_lexica.py:99) only pops `raw` (:157) and rides
//                              alias_note on top. Nested: audit = run_citation_gate (:993-997)
//                              + dangling/noncanon (lists of strings) + double_shelved /
//                              gloss_claims / hedged / subuse_overload / registry_verses
//                              (lists, [] when quiet); coverage_audit's empty-but-shaped block
//                              (:2220-2221); sense_prov rows {ot, nt, lxx} (:1241);
//                              fork = fork_field (:1708-1717) {core, frames: [{label,
//                              tradition, gloss}], graph_ref, gloss, divergence_type,
//                              lead_flip} (+ note); verses rows {ref, text} (build_verses,
//                              :1699). A word with NO entry serves {error: "not found"}
//                              (views_lexica.py:128/:143-144) — a REAL produced shape the card
//                              turns into the LSJ/BDB fallback.
// Plus the three per-verse word routes the occurrence list's rows fetch lazily:
//   * /api/kjv/verse_words + /api/bsb/verse_words -> views_kjv.py (:190-202) / views_bsb.py
//     (:174-186): BARE LIST of {word_id, word, italic:bool, punc, strongs_ids:[], lemma, xlit}.
//   * /api/hebrew/verse-words -> views_heb.py (:163-169): {words: [{hebrew, strongs, gloss,
//     translit}]}.
//
// THE COUNT AXIS rides the two seeded words, not a page flag: G4151 is the MANY word (60
// occurrences over 9 chapters in 8 books — past the occurrence list's 50-row "See more" page)
// and H7307 is the FEW word (4 occurrences, 2 books). The EMPTY state is the tab's own landing
// (no word loaded, no fetch) — reachable by just not searching.
// Every occurrence is minted inside a chapter CHAPTER_LEN knows, within its REAL verse count —
// the refs are computed ON (a row's tap navigates the Library to that chapter), so an invented
// chapter would decide a test's outcome. An unknown Strong's number / search / gloss / book
// THROWS (the CHAPTER_LEN rule): the fixture answers for its two words and nothing else.
const _LEX_RENDER_G4151 = (i) => (i % 9 === 0 ? "wind" : i % 7 === 3 ? "breath" : "spirit");
const _lexOccSpread = (spread, render) => {
  const out = [];
  let i = 0;
  for (const [book, chapter, n] of spread) {
    const len = CHAPTER_LEN[`${book}/${chapter}`];
    if (!len || n > len) throw new Error(`mobile_harness: lexicon spread wants ${n} verses of ` +
      `${book} ${chapter} (real length ${len || "unknown"}) — fix the spread, not CHAPTER_LEN.`);
    for (let v = 1; v <= n; v++) out.push({ book, chapter, verse: v, r: render(i++) });
  }
  return out;
};

// The two seeded words. `occ` is the ONE occurrence table everything downstream derives from
// (distribution rows, totals, rendering breakdowns, verse lists, gloss filters) — one source,
// so the profile/books/verses replies can't disagree with each other. `r` is the occurrence's
// rendering, which is what the ?gloss= filter slices on (the producer compares normalized
// renderings; the fixture's are already normal). Definitions follow the plain-meaning rule:
// the RANGE, never a church-word (χάρις=favor not "grace"; πνεῦμα=spirit/breath/wind).
const LEX_WORDS = {
  G4151: {
    strongs: "G4151", lemma: "πνεῦμα", translit: "pneuma",
    definition: "spirit, breath, wind — moving air; the immaterial self",
    derivation: "from G4154 (pneō) — to blow",
    related: [{ strongs: "G4154", lemma: "πνέω", translit: "pneō", gloss: "to blow" }],
    has: { abp: true, heb: false, kjv: true, bsb: true },
    defaultCorpus: "abp",
    // 60 = past the 50-row "See more" page size on purpose. OT 15 / NT 45.
    occ: _lexOccSpread([
      ["Gen", 1, 2], ["Exo", 1, 3], ["Psa", 104, 6], ["Isa", 11, 4],
      ["Mat", 3, 5], ["Joh", 1, 6], ["Joh", 4, 10], ["Rom", 8, 21], ["Rev", 22, 3],
    ], _LEX_RENDER_G4151),
  },
  H7307: {
    strongs: "H7307", lemma: "רוּחַ", translit: "ruach",
    // Hebrew `definition` is the long BDB description paragraph (views_lexicon.py:1055) —
    // shaped long on purpose so the card's Hebrew fallback body has a paragraph to lay out.
    definition: "Stand-in BDB-style paragraph — wind; by resemblance breath, a sensible (violent) " +
                "exhalation; by resemblance spirit, the animating principle; the harness measures " +
                "layout, not the lexicon.",
    derivation: "",
    related: [],
    has: { abp: false, heb: true, kjv: true, bsb: true },
    defaultCorpus: "heb",
    occ: _lexOccSpread([["Gen", 1, 2], ["Psa", 104, 2]],
      (i) => (i === 1 ? "wind" : i === 3 ? "breath" : "spirit")),
  },
};

// Book display meta for the fixture's 8 books — name from the BOOKS slice above (one constant,
// both readers), testament by the NT membership the producer derives from its _NT set (:1128).
const LEX_NT = ["Mat", "Joh", "Rom", "Rev"];
const LEX_META = {};
for (const b of BOOKS) LEX_META[b.abbrev] = { name: b.name };

// /api/lexicon/lookup seeds — a Greek lemma and its transliteration, each ONE exact hit
// (match:"exact", no enrichment — the >1 branch never runs), which the frontend auto-opens
// (80-lexicon.jsx showLookup: a lone true exact goes straight to the profile).
const LEX_LOOKUP = {
  "πνεῦμα": [{ strongs: "G4151", lemma: "πνεῦμα", translit: "pneuma",
               gloss: "spirit, breath, wind", match: "exact" }],
  "pneuma": [{ strongs: "G4151", lemma: "πνεῦμα", translit: "pneuma",
               gloss: "spirit, breath, wind", match: "exact" }],
};

// /api/lexicon/english seed — q="spirit" finds both words. Derived fields (counts, gloss
// lists) are computed from LEX_WORDS' own occurrence tables below at module load, so the
// finder's numbers agree with each word's study page (the same invariant the producer keeps —
// its totals helpers count "the SAME way the Word-study profile does", :760-765). `m: true`
// bolds the matched rendering; the lone {trunc: true} marker on the BSB line is the
// truncation-"…" DISPLAY case (renderRend draws it; the producer emits it whenever a source
// has more rendering rows than the 8 shown).
const _lexFold = (occ) => {
  const counts = {}, order = [];
  for (const o of occ) { if (!(o.r in counts)) { counts[o.r] = 0; order.push(o.r); } counts[o.r]++; }
  return order.map(g => ({ gloss: g, count: counts[g] })).sort((a, b) => b.count - a.count);
};
const _lexEnglishRow = (w, extras) => {
  const g = _lexFold(w.occ).map(x => (x.gloss === "spirit" ? { ...x, m: true } : x));
  const total = w.occ.length;
  return Object.assign({
    strongs: w.strongs, lemma: w.lemma, translit: w.translit, count: total,
    abp_glosses: w.has.abp ? g : [], heb_glosses: w.has.heb ? g : [],
    kjv_glosses: w.has.kjv ? g : [], bsb_glosses: w.has.bsb ? g : [],
    abp_total: w.has.abp ? total : null, heb_total: w.has.heb ? total : null,
    kjv_total: w.has.kjv ? total : null, bsb_total: w.has.bsb ? total : null,
  }, extras);
};
const LEX_ENGLISH = {
  spirit: [
    _lexEnglishRow(LEX_WORDS.G4151, {
      bsb_glosses: _lexFold(LEX_WORDS.G4151.occ).map(x => (x.gloss === "spirit" ? { ...x, m: true } : x))
        .concat([{ trunc: true }]),
    }),
    _lexEnglishRow(LEX_WORDS.H7307, {}),
  ],
};

// /api/lexica/G4151 — the stored Lexica entry, per the writer's `assemble` shape minus `raw`
// (the serve route pops it). G4151 sits in the CONTESTED fixture set above, and the serve
// route REFUSES a contested word stored without a fork (views_lexica.py:153-156) — so this
// entry MUST carry one; a forkless G4151 here would model a reply the server never sends.
// The stand-in text says it's stand-in (same rule as the News headlines).
const LEX_LEXICA_G4151 = {
  strongs: "G4151", lemma: "πνεῦμα", translit: "pneuma",
  sense_headlines: [
    "**1. Breath, wind — moving air**",
    "**2. The animating breath of a living creature**",
    "**3. A spirit — an immaterial being**",
  ],
  senses_block:
    "**1. Breath, wind — moving air** — stand-in sense body; the harness measures layout, " +
    "not the dictionary (Gen 1:2; Psa 104:30).\n\n" +
    "**2. The animating breath of a living creature** — stand-in sense body (Psa 104:29; Joh 4:24).\n\n" +
    "**3. A spirit — an immaterial being** — stand-in sense body (Joh 4:24; Rom 8:16).",
  range: "Stand-in Range paragraph — from moving air to the immaterial self, the span a reader " +
         "should hold rather than one settled English word.",
  gloss_notes: "Stand-in gloss note — long enough to wrap at 375px, which is the thing under measurement.",
  coverage: "Stand-in coverage line.",
  sense_prov: [{ ot: 2, nt: 0, lxx: true }, { ot: 1, nt: 1, lxx: false }, { ot: 0, nt: 2, lxx: false }],
  coverage_audit: { collocations: [], renderings: [], senses: [], thin_senses: [],
                    contested: true, flags: [] },
  pinned_core: null,
  fork: {
    core: "Stand-in shared core — what every reading agrees the word denotes.",
    frames: [
      { label: "Stand-in frame A", tradition: "Stand-in tradition A", gloss: "stand-in gloss A" },
      { label: "Stand-in frame B", tradition: "Stand-in tradition B", gloss: "stand-in gloss B" },
    ],
    graph_ref: null, gloss: "spirit", divergence_type: "stand-in-axis", lead_flip: false,
    note: "Stand-in fork note — the both-priors card's footer line.",
  },
  verses: [
    { ref: "Gen 1:2", text: "Stand-in ABP prose for Genesis 1:2 — the cited-verse block under the entry." },
    { ref: "Psa 104:30", text: "Stand-in ABP prose for Psalms 104:30." },
    { ref: "Joh 4:24", text: "Stand-in ABP prose for John 4:24." },
  ],
  provenance: "verse-grounded · LEXICA",
  split_ver: "split3",
  audit: { pass: 5, total: 5, tagging: 0, real: 0, noverse: 0, misses: [],
           dangling: [], noncanon: [], double_shelved: [], gloss_claims: [], hedged: [],
           subuse_overload: [], registry_verses: [] },
};

// The lazily-fetched verse-words rows the occurrence list renders per corpus. `{{v}}` is the
// same per-verse identity marker VERSE_WORDS uses. Both a G and an H token ride the KJV/BSB
// list so EITHER seeded word's rows carry a highlightable match (citedStrongs lights only its
// own number). The lone `italic: true` keeps translator-supplied styling measurable here too.
const LEX_KJVISH_WORDS = [
  { word_id: 1, word: "God", italic: false, punc: "", strongs_ids: ["G2316"], lemma: "θεός", xlit: "theos" },
  { word_id: 2, word: "is", italic: true, punc: "", strongs_ids: [], lemma: "", xlit: "" },
  { word_id: 3, word: "spirit-v{{v}}", italic: false, punc: ",", strongs_ids: ["G4151"], lemma: "πνεῦμα", xlit: "pneuma" },
  { word_id: 4, word: "spirit", italic: false, punc: ".", strongs_ids: ["H7307"], lemma: "רוּחַ", xlit: "ruach" },
];
const LEX_HEB_WORDS = { words: [
  { hebrew: "ר֫וּחַ", strongs: "H7307", gloss: "spirit-v{{v}}", translit: "ruach" },
  { hebrew: "אֱלֹהִים", strongs: "H430", gloss: "God", translit: "elohim" },
] };

// ONE bundle for the shared resolver (server + in-page stub read the same object).
const LEX = { words: LEX_WORDS, nt: LEX_NT, meta: LEX_META, lookup: LEX_LOOKUP,
              english: LEX_ENGLISH, lexica: { G4151: LEX_LEXICA_G4151 },
              kjvish: LEX_KJVISH_WORDS, heb: LEX_HEB_WORDS };

// The notes store's localStorage seed (&notes=1). Anchored notes carry the anchor builder's
// fields; `updated` drives the default newest-first sort, so these are ordered on purpose.
// The set is shaped to make every branch of NotesView reachable: one note WITH a body (the
// "Notes" filter + the center editor), one bookmark-only and one highlight-only (the
// "Bookmarks"/"Highlights" filters, and the list's two marker glyphs), four distinct books
// (Group-by-book + the canonical-order sort), and one journal page (the Journal mode + the
// inspect's no-anchor empty state). Gen/Psa/Joh/Rom are all in the BOOKS slice above, so the
// inspect's api.chapter() lookup resolves.
const NOTES = [
  { id: "h-note-1", device: "harness", body: "Predicate of God himself — not a thing he has.",
    color: "yellow", created: "2026-07-10T09:00:00.000Z", updated: "2026-07-14T09:00:00.000Z",
    corpus: "bible", translation: "abp", book: "Joh", bookName: "John", chapter: 4,
    start: { verse: 24, pos: null }, end: { verse: 24, pos: null },
    snippet: "God is spirit", refLabel: "John 4:24" },
  { id: "h-note-2", device: "harness", body: "", color: null, bookmark: true,
    created: "2026-07-09T09:00:00.000Z", updated: "2026-07-13T09:00:00.000Z",
    corpus: "bible", translation: "abp", book: "Gen", bookName: "Genesis", chapter: 1,
    start: { verse: 2, pos: null }, end: { verse: 2, pos: null },
    snippet: "and spirit of God bore upon the water", refLabel: "Genesis 1:2" },
  { id: "h-note-3", device: "harness", body: "", color: "blue",
    created: "2026-07-08T09:00:00.000Z", updated: "2026-07-12T09:00:00.000Z",
    corpus: "bible", translation: "bsb", book: "Rom", bookName: "Romans", chapter: 8,
    start: { verse: 16, pos: null }, end: { verse: 16, pos: null },
    snippet: "The spirit itself testifies together with our spirit", refLabel: "Romans 8:16" },
  { id: "h-note-4", device: "harness",
    body: "Ruach here is breath/wind before it is anything else — worth holding the range.",
    color: null, created: "2026-07-07T09:00:00.000Z", updated: "2026-07-11T09:00:00.000Z",
    corpus: "bible", translation: "abp", book: "Psa", bookName: "Psalms", chapter: 104,
    start: { verse: 30, pos: null }, end: { verse: 30, pos: null },
    snippet: "You shall send forth your spirit and they shall be created", refLabel: "Psalms 104:30" },
  // A MULTI-VERSE note. Shape traced from the WRITE path, not from memory: 60-library.jsx
  // `resolveSelection()` resolves each selection edge to its own verse (:1057-1058), swaps them
  // into order if you dragged backwards (:1063-1066), and stores start/end separately
  // (:1098-1099) with a range refLabel built as `book ch:startV–endV` (:1073, EN-DASH). So a
  // range genuinely survives to storage — `end.verse` is real data, not a copy of `start.verse`.
  // `pos` is a word-position within the verse and is only non-null on a drag-select, which is
  // exactly what this note is.
  { id: "h-note-5", device: "harness",
    body: "The whole exchange, not just the punchline — she asks about the mountain, he answers about spirit.",
    color: "green", created: "2026-07-05T09:00:00.000Z", updated: "2026-07-09T09:00:00.000Z",
    corpus: "bible", translation: "abp", book: "Joh", bookName: "John", chapter: 4,
    start: { verse: 21, pos: 3 }, end: { verse: 23, pos: 7 },
    snippet: "Believe me woman that an hour comes when neither on this mountain nor in Jerusalem shall you worship the father",
    refLabel: "John 4:21–23" },
  { id: "h-page-1", device: "harness", kind: "journal", title: "Spirit — working notes",
    body: "Start from the plain sense and let the corpus argue.\n\nNo verse anchor here on purpose.",
    created: "2026-07-06T09:00:00.000Z", updated: "2026-07-10T09:00:00.000Z" },
  // A SECOND page, because one row can't show a list's rhythm. The journal list is a
  // .listrow family now (dividers between rows, no card), and a single row renders neither a
  // divider (`.listrow:last-child` drops it) nor a neighbour to be separated FROM — so a
  // one-page fixture would have "proved" the row styling while showing none of it.
  // Untitled on purpose: JournalList falls back to "Untitled page" for a page with no title
  // (35-notes.jsx), and that fallback is a real row a reader sees.
  { id: "h-page-2", device: "harness", kind: "journal", title: "",
    body: "Draft with no title yet — this row renders the “Untitled page” fallback.",
    created: "2026-07-04T09:00:00.000Z", updated: "2026-07-08T09:00:00.000Z" },
];

// ── The COUNT axis (&notes=1 | &notes=many) ─────────────────────────────────────
// Height stability is a per-COUNT claim, so "empty / few / many" is a required axis on every
// Panel card (reviewer ruling, 2026-07-15): a card that sizes to its content looks correct at
// one row count and wrong at another, and a single-count fixture would pass a card that jumps.
//   * empty -> omit &notes    (store cleared; NotesView's own empty state)
//   * few   -> &notes=1       (the curated set above: 5 notes + 2 journal pages)
//   * many  -> &notes=many    (the curated set + MANY_EXTRA generated verse notes)
// The generated rows are NOT a new shape. Each is the traced SINGLE-VERSE note shape — the one
// 60-library.jsx `verseAnchor()` (:1291-1295) writes from the verse-number menu: `start` and
// `end` stamped to the SAME verse with `pos: null`, which is all that anchor writer can ever
// produce. Only book/chapter/verse/updated/flags vary. They stay inside the four chapters
// CHAPTER_LEN knows and inside each one's REAL verse count — an unknown chapter throws by
// design (:179), and an out-of-range verse would be inventing corpus.
// The bookmark/color/body cycle is load-bearing, not decoration: the list's four filters
// (35-notes.jsx:412-414) each slice on one of those fields, so a "many" seed that varied none
// of them would leave three of the four filters showing the curated set's handful — i.e. it
// would claim to measure "many" while measuring "few" on every filter but All.
const MANY_ANCHORS = [
  { book: "Joh", bookName: "John", chapter: 4 },
  { book: "Gen", bookName: "Genesis", chapter: 1 },
  { book: "Rom", bookName: "Romans", chapter: 8 },
  { book: "Psa", bookName: "Psalms", chapter: 104 },
];
const MANY_EXTRA = 40;
const manyNotes = () => {
  const out = NOTES.slice();
  for (let i = 0; i < MANY_EXTRA; i++) {
    const a = MANY_ANCHORS[i % MANY_ANCHORS.length];
    const verse = (i % CHAPTER_LEN[`${a.book}/${a.chapter}`]) + 1;
    const day = String(1 + (i % 28)).padStart(2, "0");
    out.push({
      id: `h-many-${i}`, device: "harness",
      body: i % 3 === 0 ? `Generated row ${i} — carries a body, so the "Notes" filter sees it.` : "",
      color: i % 2 === 0 ? "yellow" : null,
      bookmark: i % 4 === 1,
      created: `2026-06-${day}T09:00:00.000Z`, updated: `2026-06-${day}T09:00:00.000Z`,
      corpus: "bible", translation: "abp", book: a.book, bookName: a.bookName, chapter: a.chapter,
      start: { verse, pos: null }, end: { verse, pos: null },
      snippet: `Stand-in snippet for ${a.bookName} ${a.chapter}:${verse}.`,
      refLabel: `${a.bookName} ${a.chapter}:${verse}`,
    });
  }
  return out;
};

// ── News ────────────────────────────────────────────────────────────────────
// news.db is PA-only, so every shape below is traced to the PRODUCING Python in this repo,
// per field. NewsView's mobile branch never reaches its <Shell> without this: it returns a
// bare `.news-view` early three times over (84-news.jsx:737 no meta / :738 !canRead /
// :739 !available), so the bar can only be MEASURED once meta clears all three.
//
// WHAT NEWS ACTUALLY CALLS — verified by call site, not from the route list. 00-core.jsx
// defines SEVEN news helpers (:233-286) but NewsView calls only FOUR: newsMeta (:512),
// newsAll (:538), newsStatus (:668), newsResolve (:695). `newsList`/`newsCounts`/`newsShape`
// have ZERO call sites app-wide — /all carries the whole clustered feed and the browser
// derives every count/shape locally (the `shape` memo, :629). Only the first two run at
// MOUNT; the other two are POSTs on a tap. So the boot fixture is /meta + /all, and stubbing
// /counts or /shape would be answering for calls that never come.
//
// THE GATE, checked not assumed: `?admin=1` seeds `lexica.news.key.v1` (which is also what
// gates the News tab into the nav at all, 90-app.jsx:130) and `_newsKey()` (00-core.jsx:58)
// puts it on the query string. The SERVER gate (_can_read / _shared_key_ok) never runs here
// — fetch is stubbed above the network — so what actually decides is the CLIENT gate reading
// this reply: owner|reader, then available. Hence owner+available+can_write below.
//
// DATES ARE RELATIVE TO TODAY, ON PURPOSE. The default window is `windowKey` "21"
// (84-news.jsx:489) and `since` is recomputed FRESH every render from the clock
// (`_newsDaysAgo`, :10 + :494), with the floor at score >= 5 (:496). A hardcoded date would
// drift out of the window and this fixture would quietly render "No stories match" — a bar
// measured over an empty feed, passing vacuously, some weeks after anyone last looked.
const _newsDay = (n) => new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);

// views_news.py THREAD_LABELS (:44-59) — the gatherer's 13 threads + "new". Keys are the
// vocabulary `card.thread` / `member.t` must speak: the rail, the shape readout and the card
// meta line all resolve a label through this map (`labels[face.t] || face.t || "?"`,
// :96), so an invented key would render as a bare "?" and look like a data bug.
const THREAD_LABELS = {
  papacy_moral_authority: "Papacy as moral authority",
  american_pope: "Vatican–US relations",
  encyclical_political: "Encyclicals / doctrine going political",
  ai_moralized: "Economic/tech control",
  legislating_morality: "Legislating worship/morality",
  ecumenism: "Ecumenism (Protestant–Catholic)",
  ecumenism_orthodox: "Catholic–Orthodox reunion",
  protestant_collapse: "Protestant / Evangelical collapse",
  alien_agenda: "Alien / UFO disclosure",
  culture_shaping: "Culture shaping",
  signs_wonders: "Signs & wonders / miracles",
  political_realignment: "Political realignment",
  sabbath_sunday: "Sabbath / Sunday law",
  new: "New angle",
};

// /api/news/meta — views_news.py meta() (:574). The available+permitted return is :587-589
// (owner, reader, available, labels, can_write, reviewer, reviewer_name). `reviewer` is the
// STABLE id shape 'u<user_id>' for an admin (_reviewer, :113-126) — never a human name; the
// display alias is resolved separately by _reviewer_label (:129) off the notes.db users row,
// which is why the two fields disagree here rather than echoing each other.
const NEWS_META = { owner: true, reader: false, available: true, labels: THREAD_LABELS,
                    can_write: true, reviewer: "u1", reviewer_name: "Harness reviewer" };

// A member of a card's `members` list — views_news.py _all_cards (:522-534). The short keys
// are the producer's own (s=score, t=thread, nf=new-flag, d=date, pw=paywalled). `via` is
// provenance and is exactly one of two produced strings: "RSS" when the ingest query started
// "rss:", else "Google News" (:533).
const member = (o) => Object.assign({
  s: 5, t: "culture_shaping", nf: 0, d: _newsDay(3), title: "", url: "", resolved: "",
  pw: false, summary: "", why: "", src: "?", via: "Google News",
}, o);

// A card — views_news.py _serialize (:361-378) + the two fields _all_cards attaches after it
// (`event` :518, `members` :522), + `status`, which _all_cards deliberately POPS (:516) and
// all_news() re-attaches per request from the reviewer's own rows (:562-564). So `status`
// belongs on the card here even though _serialize doesn't emit it.
const card = (o) => Object.assign({
  ids: [], title: "", url: "", resolved_url: "", summary: "", score: 5, thread: "culture_shaping",
  thread_label: "", why: "", published: "", peak_date: "", count: 1, sources: [], status: "new",
  event: "", members: [],
}, o);

// The stand-in text says it's stand-in — a fixture that reads like real reporting is one
// screenshot away from being quoted as real. What must be realistic is LENGTH, because that
// is the thing under measurement: the long headline exists so wrapping can be measured at
// 375px (the admin Keep/Dismiss squeeze in TODO.md is a ~148px/5-line headline claim), and
// the short one so the two-line case is present to compare against.
const LONG_TITLE = "Stand-in headline, long on purpose — the harness measures layout, not the feed, " +
                   "and a headline that never wraps cannot prove a row's height at 375px";
const SHORT_TITLE = "Stand-in headline — short";

// Shaped so every branch the mobile bar opens onto is reachable, since a bar measured over a
// feed with nothing in it proves only that the bar draws:
//   * threads sheet  -> four DISTINCT threads, so the rail has rows to be a list
//   * watch sheet    -> scores straddling _SURFACE_SCORE (6, :21) so the shape readout has a
//                       real surfaced/buried split, not an all-or-nothing line; one nf:1 for
//                       the "new angle" tally
//   * options sheet  -> nothing needed; it's the top bar's own knobs
//   * the view tabs  -> one card per status (new / keep / dismiss)
//   * the 🔒 marker  -> one wholly-paywalled card (every member pw), the only way `face_pw`
//                       comes out true on the Max preset (:71)
//   * "+N outside"   -> the last card is KEPT but dated 40d back, outside the default 21d
//                       window, which is the only way `keptOutside` (:899) is non-zero
const NEWS_CARDS = [
  card({
    ids: [101, 102, 103], title: LONG_TITLE, url: "https://example.invalid/news/101",
    resolved_url: "https://example.invalid/real/101",
    summary: "Stand-in summary — three articles clustered into one card so the article→card collapse line has a real numerator.",
    score: 9, thread: "papacy_moral_authority", thread_label: THREAD_LABELS.papacy_moral_authority,
    why: "Stand-in scorer rationale — this is the text the Watch sheet shows for a selected card.",
    published: _newsDay(1), peak_date: _newsDay(3), count: 3, status: "new",
    event: "Stand-in event name",
    sources: [{ source: "Stand-in Wire", url: "https://example.invalid/news/101", published: _newsDay(1) },
              { source: "Stand-in Post", url: "https://example.invalid/news/102", published: _newsDay(3) }],
    members: [
      member({ s: 9, t: "papacy_moral_authority", nf: 1, d: _newsDay(3), title: LONG_TITLE,
               url: "https://example.invalid/news/101", resolved: "https://example.invalid/real/101",
               summary: "Stand-in summary — the face article.", why: "Stand-in scorer rationale — the face article's why.",
               src: "Stand-in Wire", via: "RSS" }),
      member({ s: 7, t: "papacy_moral_authority", d: _newsDay(3), title: SHORT_TITLE,
               url: "https://example.invalid/news/102", src: "Stand-in Post" }),
      member({ s: 5, t: "papacy_moral_authority", d: _newsDay(1), title: "Stand-in headline — the straggler",
               url: "https://example.invalid/news/103", src: "Stand-in Review" }),
    ],
  }),
  card({
    ids: [201], title: "Stand-in headline — a paywalled card, the one that renders the lock marker",
    url: "https://example.invalid/news/201",
    summary: "Stand-in summary — every member paywalled, so the face is paywalled on the Max preset too.",
    score: 8, thread: "ecumenism", thread_label: THREAD_LABELS.ecumenism,
    why: "Stand-in scorer rationale — paywalled card.",
    published: _newsDay(5), peak_date: _newsDay(5), count: 1, status: "new",
    sources: [{ source: "Stand-in Journal", url: "https://example.invalid/news/201", published: _newsDay(5) }],
    members: [member({ s: 8, t: "ecumenism", d: _newsDay(5), pw: true,
                       title: "Stand-in headline — a paywalled card, the one that renders the lock marker",
                       url: "https://example.invalid/news/201", src: "Stand-in Journal" })],
  }),
  card({
    ids: [301], title: "Stand-in headline — scored below the surface line, so it counts as buried",
    url: "https://example.invalid/news/301",
    summary: "Stand-in summary — score 5 sits under _SURFACE_SCORE (6) but on the default floor (5), so it shows AND counts buried.",
    score: 5, thread: "ai_moralized", thread_label: THREAD_LABELS.ai_moralized,
    why: "Stand-in scorer rationale — buried card.",
    published: _newsDay(8), peak_date: _newsDay(8), count: 1, status: "new",
    sources: [{ source: "Stand-in Wire", url: "https://example.invalid/news/301", published: _newsDay(8) }],
    members: [member({ s: 5, t: "ai_moralized", d: _newsDay(8), title: "Stand-in headline — scored below the surface line, so it counts as buried",
                       url: "https://example.invalid/news/301", src: "Stand-in Wire", via: "RSS" })],
  }),
  card({
    ids: [401], title: "Stand-in headline — this one is kept, inside the window",
    url: "https://example.invalid/news/401",
    summary: "Stand-in summary — the Kept tab's in-window row.",
    score: 7, thread: "sabbath_sunday", thread_label: THREAD_LABELS.sabbath_sunday,
    why: "Stand-in scorer rationale — kept card.",
    published: _newsDay(12), peak_date: _newsDay(12), count: 1, status: "keep",
    sources: [{ source: "Stand-in Post", url: "https://example.invalid/news/401", published: _newsDay(12) }],
    members: [member({ s: 7, t: "sabbath_sunday", d: _newsDay(12), title: "Stand-in headline — this one is kept, inside the window",
                       url: "https://example.invalid/news/401", src: "Stand-in Post" })],
  }),
  card({
    ids: [501], title: "Stand-in headline — dismissed",
    url: "https://example.invalid/news/501",
    summary: "Stand-in summary — the Dismissed tab's row.",
    score: 6, thread: "culture_shaping", thread_label: THREAD_LABELS.culture_shaping,
    why: "Stand-in scorer rationale — dismissed card.",
    published: _newsDay(19), peak_date: _newsDay(19), count: 1, status: "dismiss",
    sources: [{ source: "Stand-in Review", url: "https://example.invalid/news/501", published: _newsDay(19) }],
    members: [member({ s: 6, t: "culture_shaping", d: _newsDay(19), title: "Stand-in headline — dismissed",
                       url: "https://example.invalid/news/501", src: "Stand-in Review" })],
  }),
  card({
    ids: [601], title: "Stand-in headline — kept, but OUTSIDE the default 21d window",
    url: "https://example.invalid/news/601",
    summary: "Stand-in summary — dated 40d back so the Kept tab's \"+N outside this window\" line has something to count.",
    score: 8, thread: "protestant_collapse", thread_label: THREAD_LABELS.protestant_collapse,
    why: "Stand-in scorer rationale — out-of-window kept card.",
    published: _newsDay(40), peak_date: _newsDay(40), count: 1, status: "keep",
    sources: [{ source: "Stand-in Wire", url: "https://example.invalid/news/601", published: _newsDay(40) }],
    members: [member({ s: 8, t: "protestant_collapse", d: _newsDay(40), title: "Stand-in headline — kept, but OUTSIDE the default 21d window",
                       url: "https://example.invalid/news/601", src: "Stand-in Wire" })],
  }),
];

// /api/news/all — views_news.py all_news() (:543). Exactly three keys on the success return
// (:570). `labels` rides BOTH this and /meta from the same server constant; NewsView reads it
// off meta (:555), so they must agree — one constant above, both readers.
const NEWS_ALL = { available: true, cards: NEWS_CARDS, labels: THREAD_LABELS };

const FIXTURES = {
  "/api/auth/me": ME,
  "/api/ai-search": AI_SEARCH,
  "/api/books": BOOKS,
  "/api/lexica/contested": CONTESTED,
  "/api/news/meta": NEWS_META,
  "/api/news/all": NEWS_ALL,
};

// Routes that carry ids in the PATH (chapter, verse, Strong's) or the QUERY STRING rather than
// an exact path. Exact-match FIXTURES wins; these catch the parameterised families.
// NOTE the verse-words regex used to also accept "/api/heb/verse-words/…" — a route that does
// not exist (the real Hebrew route is /api/hebrew/verse-words, 00-core.jsx:114); the dead
// alternative answered for nothing and is dropped now that the real one is fixtured.
const RE_CHAPTER = /^\/api\/(?:chapter|kjv\/chapter|bsb\/chapter)\/([^/]+)\/(\d+)$/;
const RE_VERSE_WORDS = /^\/api\/verse-words\/([^/]+)\/(\d+)\/(\d+)$/;
const RE_KB_VERSE_WORDS = /^\/api\/(?:kjv|bsb)\/verse_words\/([^/]+)\/(\d+)\/(\d+)$/;
const RE_HEB_VERSE_WORDS = /^\/api\/hebrew\/verse-words\/([^/]+)\/(\d+)\/(\d+)$/;
const RE_LEX_PROFILE = /^\/api\/lexicon\/profile\/([^/]+)$/;
const RE_LEX_BOOKS = /^\/api\/lexicon\/books\/([^/]+)$/;
const RE_LEX_VERSES = /^\/api\/lexicon\/verses\/([^/]+)\/([^/]+)$/;
const RE_LEXICA = /^\/api\/lexica\/([GH]\d+(?:\.\d+)?)$/;

// Kept as SOURCE TEXT because the in-page stub must run the same resolver the server does, and
// a function can't ride there as JSON. Reads _F / _CH / _VW / _LX from scope. The SERVER now
// evaluates this SAME text (new Function below) instead of keeping a hand-mirrored copy — the
// old duplicate was two bodies that had to be edited in lockstep, and a fixture that disagrees
// with itself is worse than none.
// Takes the FULL url (query string included): the lexicon family branches on ?q/?corpus/
// ?gloss/?testament. Unknown seeds THROW, loudly, on both sides (the CHAPTER_LEN rule).
const RESOLVER_SRC = `
  function _lexWord(sid) {
    if (!Object.prototype.hasOwnProperty.call(_LX.words, sid))
      throw new Error("mobile_harness: no lexicon fixture for " + sid +
        " — G4151 and H7307 are the seeded words; add one rather than inventing a reply.");
    return _LX.words[sid];
  }
  function _lexIsNT(b) { return _LX.nt.indexOf(b) >= 0; }
  function _lexOccOf(w, testament, gloss) {
    return w.occ.filter(function (o) {
      if (testament === "ot" && _lexIsNT(o.book)) return false;
      if (testament === "nt" && !_lexIsNT(o.book)) return false;
      if (gloss && o.r !== gloss) return false;
      return true;
    });
  }
  function _lexGlossCheck(w, gloss) {
    if (gloss && !w.occ.some(function (o) { return o.r === gloss; }))
      throw new Error("mobile_harness: '" + gloss + "' is not a rendering the " + w.strongs +
        " fixture ever serves — a silent empty here would decide a filter test.");
  }
  function _lexFoldJs(occ) {
    var counts = {}, order = [];
    occ.forEach(function (o) { if (!(o.r in counts)) { counts[o.r] = 0; order.push(o.r); } counts[o.r]++; });
    return order.map(function (g) { return { gloss: g, count: counts[g] }; })
      .sort(function (a, b) { return b.count - a.count; });
  }
  function _lexBooksFor(w, gloss) {
    var counts = {}, order = [];
    w.occ.forEach(function (o) {
      if (gloss && o.r !== gloss) return;
      if (!(o.book in counts)) { counts[o.book] = 0; order.push(o.book); }
      counts[o.book]++;
    });
    return order.map(function (b) {
      return { book: b, name: _LX.meta[b].name, testament: _lexIsNT(b) ? "NT" : "OT", count: counts[b] };
    }).sort(function (a, b) { return b.count - a.count; });
  }
  // The resolved corpus, per the producer's fallbacks (:1107-1127 profile; :1472/:1478 verses):
  // default = the word's native text; "all" folds to it; heb without heb data folds to kjv.
  function _lexCorpus(w, asked) {
    var c = asked || w.defaultCorpus;
    if (c === "all") c = w.defaultCorpus;
    if (c === "heb" && !w.has.heb) c = "kjv";
    return c;
  }
  function _lexProfile(w, asked, testament) {
    var c = _lexCorpus(w, asked);
    var books = _lexBooksFor(w, "");
    var total = 0;
    books.forEach(function (b) { total += b.count; });
    var g = _lexFoldJs(w.occ);
    return {
      strongs: w.strongs, lemma: w.lemma, translit: w.translit,
      definition: w.definition, derivation: w.derivation, related: w.related,
      total: total, books: books, corpus: c,
      glosses: g.slice(),
      abp_glosses: w.has.abp ? g : [], heb_glosses: w.has.heb ? g : [],
      kjv_glosses: w.has.kjv ? g : [], bsb_glosses: w.has.bsb ? g : [],
      has_abp: w.has.abp, has_kjv: w.has.kjv, has_heb: w.has.heb, has_bsb: w.has.bsb,
      alias_note: null,
      default_verses: _lexOccOf(w, testament || "all", "").map(function (o) {
        return { book: o.book, chapter: o.chapter, verse: o.verse };
      }),
      default_truncated: false,
    };
  }
  function _lexVerses(w, book, asked, gloss, testament) {
    _lexGlossCheck(w, gloss);
    var c = _lexCorpus(w, asked);
    if (book === "all") {
      return { verses: _lexOccOf(w, testament || "all", gloss).map(function (o) {
                 return { book: o.book, chapter: o.chapter, verse: o.verse };
               }), glosses: [], truncated: false };
    }
    var occ = w.occ.filter(function (o) { return o.book === book; });
    if (!occ.length)
      throw new Error("mobile_harness: the " + w.strongs + " fixture has no occurrences in '" +
        book + "' — the UI can only ask for books its own distribution listed.");
    // Rendering breakdown counts BEFORE the gloss filter, exactly like the producer (:1509-1521:
    // gloss_counts accumulates over every occurrence; the filter only prunes the verse rows).
    var glosses = _lexFoldJs(occ);
    var rows = occ.filter(function (o) { return !gloss || o.r === gloss; });
    var verses;
    if (c === "kjv") {
      verses = rows.map(function (o) { return { chapter: o.chapter, verse: o.verse, words: [
        { w: "Stand-in", h: 0, i: 0, punc: "" }, { w: "prose", h: 0, i: 1, punc: "," },
        { w: o.r + "-v" + o.verse, h: 1, i: 0, punc: "." },
      ] }; });
    } else if (c === "heb" || c === "bsb") {
      verses = rows.map(function (o) { return { chapter: o.chapter, verse: o.verse }; });
    } else {
      verses = rows.map(function (o) { return { chapter: o.chapter, verse: o.verse, words: [
        { w: "Stand-in", h: 0, i: 0 }, { w: "prose", h: 0, i: 1 },
        { w: o.r + "-v" + o.verse, h: 1, i: 0 },
      ], text: "Stand-in ABP prose for " + book + " " + o.chapter + ":" + o.verse + "." }; });
    }
    return { verses: verses, glosses: glosses };
  }
  function _resolve(full) {
    var qi = String(full).indexOf("?");
    var u = qi >= 0 ? String(full).slice(0, qi) : String(full);
    var P = new URLSearchParams(qi >= 0 ? String(full).slice(qi + 1) : "");
    if (Object.prototype.hasOwnProperty.call(_F, u)) return _F[u];
    var m = u.match(${RE_CHAPTER});
    if (m) {
      var hit = _CH[m[1] + "/" + m[2]];
      if (!hit) throw new Error("mobile_harness: no real verse count for " + m[1] + " " + m[2] +
        " — add it to CHAPTER_LEN from abp_texts/ rather than letting the fixture invent one.");
      return hit;
    }
    m = u.match(${RE_VERSE_WORDS});
    if (m) return JSON.parse(JSON.stringify(_VW).split("{{v}}").join(m[3]));
    m = u.match(${RE_KB_VERSE_WORDS});
    if (m) return JSON.parse(JSON.stringify(_LX.kjvish).split("{{v}}").join(m[3]));
    m = u.match(${RE_HEB_VERSE_WORDS});
    if (m) return JSON.parse(JSON.stringify(_LX.heb).split("{{v}}").join(m[3]));
    if (u === "/api/lexicon/lookup") {
      var q = P.get("q") || "";
      if (!Object.prototype.hasOwnProperty.call(_LX.lookup, q))
        throw new Error("mobile_harness: no lookup fixture for '" + q + "'.");
      return _LX.lookup[q];
    }
    if (u === "/api/lexicon/english") {
      var qe = P.get("q") || "";
      if (!Object.prototype.hasOwnProperty.call(_LX.english, qe))
        throw new Error("mobile_harness: no english-finder fixture for '" + qe + "'.");
      // corpus/testament re-queries serve the same rows — the SHAPE is what's fixtured.
      return _LX.english[qe];
    }
    m = u.match(${RE_LEX_PROFILE});
    if (m) return _lexProfile(_lexWord(m[1]), P.get("corpus"), P.get("testament"));
    m = u.match(${RE_LEX_BOOKS});
    if (m) {
      var wb = _lexWord(m[1]);
      _lexGlossCheck(wb, P.get("gloss") || "");
      return { books: _lexBooksFor(wb, P.get("gloss") || "") };
    }
    m = u.match(${RE_LEX_VERSES});
    if (m) return _lexVerses(_lexWord(m[1]), m[2], P.get("corpus"), P.get("gloss") || "", P.get("testament"));
    m = u.match(${RE_LEXICA});
    if (m) {
      if (Object.prototype.hasOwnProperty.call(_LX.lexica, m[1])) return _LX.lexica[m[1]];
      if (Object.prototype.hasOwnProperty.call(_LX.words, m[1])) return { error: "not found" };
      throw new Error("mobile_harness: no lexica fixture for " + m[1] + ".");
    }
    return undefined;
  }`;

// The server runs the SAME resolver text the page embeds — one body, two hosts.
const fixtureFor = new Function("_F", "_CH", "_VW", "_LX",
  RESOLVER_SRC + "\n  return _resolve;")(FIXTURES, CHAPTERS, VERSE_WORDS, LEX);

// ── The page ────────────────────────────────────────────────────────────────
// Loads the real bundle. `fetch` is stubbed BEFORE app.js so no call escapes to a server
// that isn't here; anything unfixtured resolves empty rather than hanging (a hang would
// leave the surface mid-render and every measurement would be of a half-drawn page).
// __LEX_HARNESS__ records what was asked for, so a read can prove the surface got its data.
const PAGE = (view, admin, bundle, notesSeed) => `<!DOCTYPE html>
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
    // ?notes=1 (few) | ?notes=many — seed the notes store. It is NOT stubbed at /api/ because
    // it isn't served from there: NotesStore reads localStorage on first load() and caches, so
    // the seed has to be in place BEFORE app.js runs. Unseeded, every Notes read is of the
    // empty state — which is a real state worth measuring, so this stays opt-in rather than
    // always-on (and the notes/highlights also paint marks in the Library reader, which would
    // quietly move every OTHER surface's measurements).
    ${notesSeed
      ? `localStorage.setItem("lexica.notes.v1", ${JSON.stringify(JSON.stringify(notesSeed))});`
      : `localStorage.removeItem("lexica.notes.v1");`}
  } catch (e) {}
  // The measuring pane runs this page as a HIDDEN tab (document.hidden === true), where the
  // engine suspends rAF and IntersectionObserver callbacks entirely — control-proved 2026-07-15:
  // an observer on an on-screen element stayed silent for 3s and rAF never ran. (Same mechanism
  // as the frozen-CSS-animations trap.) Left alone, every IO-lazy row (VerseRow, the ONLY IO
  // consumer — 50-corpus-results.jsx:17) sits at "Loading…" forever and a list measurement is
  // of placeholders. So the harness makes lazy EAGER: observe() fires once, immediately, as
  // intersecting. Laziness is not under test here — layout is.
  window.IntersectionObserver = function (cb) {
    const self = { observe: (el) => { try { cb([{ isIntersecting: true, target: el, intersectionRatio: 1 }], self); } catch (e) {} },
                   disconnect: () => {}, unobserve: () => {}, takeRecords: () => [] };
    return self;
  };
  const _F = ${JSON.stringify(FIXTURES)};
  const _CH = ${JSON.stringify(CHAPTERS)};
  const _VW = ${JSON.stringify(VERSE_WORDS)};
  const _LX = ${JSON.stringify(LEX)};
  ${RESOLVER_SRC}
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
    const hit = _resolve(String(url));   // FULL url — the lexicon family branches on the query string
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
    // An unknown seed REJECTS LOUDLY (the notes=… 400 rule) instead of crashing the process —
    // a probe's typo must fail its own request, not kill every parallel probe's server.
    // The in-page stub keeps the raw throw (it fails only the page that made the call).
    let hit;
    try { hit = fixtureFor(url.pathname + url.search); }
    catch (e) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(String(e.message || e));
      return;
    }
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
  // empty (omitted) / few (=1) / many (=many) — the required count axis. An unrecognised value
  // is a typo in a probe, not a request for the empty state: fail loudly rather than silently
  // measuring an empty card and calling it "many".
  const notesArg = url.searchParams.get("notes");
  if (notesArg !== null && notesArg !== "1" && notesArg !== "many") {
    res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
    res.end(`mobile_harness: notes=${notesArg} is not a seed. Use notes=1 (few), notes=many, or omit it (empty).`);
    return;
  }
  const notesSeed = notesArg === "many" ? manyNotes() : notesArg === "1" ? NOTES : null;
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(PAGE(view, admin, bundle, notesSeed));
}).listen(PORT, "127.0.0.1", () => {
  console.log("mobile harness on http://127.0.0.1:" + PORT + "/?view=corpus");
  console.log("views: library | lexicon | corpus | notes | study | news | about");
  console.log("add &admin=1 for the admin's chrome (7 mobile nav tabs, not 5) — also the News tab's gate");
  console.log("add &notes=1 to seed the notes store (5 notes + 2 journal pages)");
  console.log("add &notes=many for the same set + " + MANY_EXTRA + " generated notes (the count axis; omit &notes for empty)");
  console.log("lexicon (view=lexicon): seeded words G4151 (many: 60 occ) / H7307 (few: 4 occ);");
  console.log("  searches that answer: '\\u03c0\\u03bd\\u03b5\\u03c5\\u03bc\\u03b1(accented)'/'pneuma' (lookup), 'spirit' (english), G4151/H7307 (direct).");
  console.log("  anything else THROWS on purpose — landing = the empty state.");
});
