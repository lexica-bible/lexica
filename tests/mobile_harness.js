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
const CHAPTER_LEN = { "Gen/1": 31, "Joh/1": 51, "Joh/4": 54, "Rom/8": 39, "Psa/104": 35 };

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

// Routes that carry ids in the PATH (chapter, verse) rather than a query string. Exact-match
// FIXTURES wins; these catch the parameterised families. The two regexes and the resolver body
// are shared verbatim with the in-page stub (RESOLVER_SRC below) so the server and the browser
// can't answer differently — a fixture that disagrees with itself is worse than none.
const RE_CHAPTER = /^\/api\/(?:chapter|kjv\/chapter|bsb\/chapter)\/([^/]+)\/(\d+)$/;
const RE_VERSE_WORDS = /^\/api\/(?:verse-words|heb\/verse-words)\/([^/]+)\/(\d+)\/(\d+)$/;

// Kept as SOURCE TEXT because the in-page stub must run the same resolver the server does, and
// a function can't ride there as JSON. Reads _F / _CH / _VW from the page's scope.
const RESOLVER_SRC = `
  function _resolve(u) {
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
    return undefined;
  }`;

const fixtureFor = (pathname) => {
  if (Object.prototype.hasOwnProperty.call(FIXTURES, pathname)) return FIXTURES[pathname];
  let m = pathname.match(RE_CHAPTER);
  if (m) {
    const hit = CHAPTERS[`${m[1]}/${m[2]}`];
    if (!hit) throw new Error(`mobile_harness: no real verse count for ${m[1]} ${m[2]} — add it ` +
      `to CHAPTER_LEN from abp_texts/ rather than letting the fixture invent one.`);
    return hit;
  }
  m = pathname.match(RE_VERSE_WORDS);
  if (m) return JSON.parse(JSON.stringify(VERSE_WORDS).split("{{v}}").join(m[3]));
  return undefined;
};

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
  const _F = ${JSON.stringify(FIXTURES)};
  const _CH = ${JSON.stringify(CHAPTERS)};
  const _VW = ${JSON.stringify(VERSE_WORDS)};
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
    const hit = _resolve(u);
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
});
