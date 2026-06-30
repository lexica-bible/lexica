const { useState, useEffect, useLayoutEffect, useRef, useMemo } = React;

const _ARTICLE_RE = /^((?:the|a|an|his|her|its|of|my|your|their|our)\s+)+/i;
function stripArticles(s) {
  if (!s) return s;
  return s.replace(_ARTICLE_RE, "").trim() || s;
}

// A lemma's dictionary gloss from the lexicon KJV-rendering list (kjv_def) — a comma
// list, sometimes with parenthetical KJV-isms. Trim it to a short sense ("spirit, wind")
// to sit beside the headword lemma: drop the parentheticals, keep the first sense or two.
function shortLemmaGloss(s) {
  if (!s) return "";
  const t = s.replace(/\([^)]*\)/g, " ").replace(/\s+/g, " ").trim();
  const parts = t.split(/[,;]/).map(x => x.trim()).filter(Boolean);
  let out = parts.slice(0, 2).join(", ").replace(/[\s,;:.\-]+$/, "");
  if (out.length > 30 && parts[0]) out = parts[0].replace(/[\s,;:.\-]+$/, "");
  return out;
}

// The Haiku-written blurbs (cross-ref synthesis, book/chapter summaries, person/
// place descriptions, LSJ word study) routinely mark transliterated Greek/Hebrew in
// markdown — *italic* and occasionally **bold**. Rendered as plain text the markers
// leak as literal asterisks, so turn them into <em>/<strong> here. Asterisks only
// (the form the model actually emits); a lone/unpaired * is left as text.
// Require non-space hugging the markers (the real markdown rule), so a stray or
// unpaired "*" — or "2*3" arithmetic — is never mistaken for emphasis.
const _INLINE_MD_RE = /\*\*(\S(?:[^*]*\S)?)\*\*|\*(\S(?:[^*]*\S)?)\*/g;
function renderInlineMd(text) {
  if (!text || typeof text !== "string" || text.indexOf("*") === -1) return text;
  const nodes = [];
  let last = 0, m, key = 0;
  while ((m = _INLINE_MD_RE.exec(text)) !== null) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    if (m[1] != null) nodes.push(<strong key={key++}>{m[1]}</strong>);
    else nodes.push(<em key={key++}>{m[2]}</em>);
    last = _INLINE_MD_RE.lastIndex;
  }
  _INLINE_MD_RE.lastIndex = 0;
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

// ============================================================
// API LAYER
// ============================================================
// Attach the signed-in user's bearer token (if any). Used only by the ESV calls
// below — the server gate needs to know WHO is asking, since the ESV is the
// owner's personal text. Resolved at call time (NotesStore loads after this file).
function _authHeaders() {
  try {
    const a = (typeof NotesStore !== "undefined") && NotesStore.auth();
    return a && a.token ? { "Authorization": "Bearer " + a.token } : {};
  } catch (e) { return {}; }
}

// The no-login News share key (saved when someone opens /?news=<key>), if any.
function _newsKey() {
  // Prefer the saved key; fall back to the ?news= URL param so a freshly opened share
  // link works on its very first request, before the mount effect saves the key.
  try { const k = localStorage.getItem("lexica.news.key.v1"); if (k) return k; } catch (e) {}
  try { return new URLSearchParams(window.location.search).get("news") || ""; } catch (e) { return ""; }
}

const api = {
  aiSearch: (q, context = "") =>
    fetch(`/api/ai-search?q=${encodeURIComponent(q)}${context ? `&context=${encodeURIComponent(context)}` : ""}`, { headers: _authHeaders() }).then(r => r.json()),
  // Streamed Ask-the-corpus: the panel arrives first, the synthesis prose streams in
  // word-by-word, the verse evidence lands at the tail. A cache hit (or a quota / login /
  // error reply) comes back as one-lump JSON instead — detected by content type — and is
  // handed straight to onDone, exactly like the old aiSearch.
  aiSearchStream: async (q, context, { onPanel, onDelta, onDone, onError }) => {
    const url = `/api/ai-search?q=${encodeURIComponent(q)}${context ? `&context=${encodeURIComponent(context)}` : ""}`;
    const resp = await fetch(url, { headers: _authHeaders() });
    if (!(resp.headers.get("content-type") || "").includes("text/event-stream")) {
      let data; try { data = await resp.json(); } catch (e) { data = { error: "Couldn't read the answer." }; }
      onDone(data);
      return;
    }
    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    const handle = (frame) => {
      let name = "", data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) name = line.slice(6).trim();
        else if (line.startsWith("data:")) data = line.slice(5).trim();
      }
      if (!name || !data) return;
      let obj; try { obj = JSON.parse(data); } catch (e) { return; }
      if (name === "panel") onPanel(obj);
      else if (name === "delta") onDelta(obj.t || "");
      else if (name === "done") onDone(obj);
      else if (name === "error") onError(obj);
    };
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n\n")) !== -1) {
        const frame = buf.slice(0, i); buf = buf.slice(i + 2);
        if (frame.trim()) handle(frame);
      }
    }
  },
  verse: (book, chapter, verse) =>
    fetch(`/api/verse/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.json()),
  verseWords: (book, chapter, verse) =>
    fetch(`/api/verse-words/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.json()),
  hebVerseWords: (book, chapter, verse) =>
    fetch(`/api/hebrew/verse-words/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.json()),
  hebStrongsCount: (strongs) =>
    fetch(`/api/hebrew/strongs-count/${encodeURIComponent(strongs)}`).then(r => r.json()),
  strongsCount: (strongs_base) =>
    fetch(`/api/strongs-count/${encodeURIComponent(strongs_base)}`).then(r => r.json()),
  lsj: (lemma, strongs) => {
    const path = lemma || strongs || '';
    if (!path) return Promise.resolve({ error: 'not found' });
    const qs = strongs ? `?strongs=${encodeURIComponent(strongs)}` : '';
    return fetch(`/api/lsj/${encodeURIComponent(path)}${qs}`).then(r => r.json());
  },
  lsjSummary: (key, strongs, book, chapter, verse) => {
    const hasDot = strongs && strongs.includes('.');
    const path = key || (hasDot ? strongs : '');
    if (!path) return Promise.resolve({ error: 'not found' });
    const p = new URLSearchParams();
    if (hasDot) p.set('strongs', strongs);
    if (book && chapter && verse) { p.set('book', book); p.set('chapter', chapter); p.set('verse', verse); }
    const qs = p.toString() ? `?${p}` : '';
    return fetch(`/api/lsj-summary/${encodeURIComponent(path)}${qs}`).then(r => r.json());
  },
  // Lexica dictionary entry (verse-grounded). PUBLIC since 2026-06-25; still sends the bearer token
  // (harmless when logged out). A word with no stored entry 404s and the card falls back to LSJ.
  lexica: (strongs) => {
    if (!strongs) return Promise.resolve({ error: 'not found' });
    return fetch(`/api/lexica/${encodeURIComponent(strongs)}`, { headers: _authHeaders() }).then(r => r.json());
  },
  books: () =>
    fetch("/api/books").then(r => r.json()),
  chronological: () =>
    fetch("/static/chronological.json").then(r => r.json()),
  chronoIntro: (day) =>
    fetch(`/api/chrono/intro/${day}`).then(r => r.json()),
  chapter: (book, ch) =>
    fetch(`/api/chapter/${encodeURIComponent(book)}/${ch}`).then(r => r.json()),
  extraChapter: (book, ch) =>
    fetch(`/api/extra/${encodeURIComponent(book)}/chapter/${ch}`).then(r => r.json()),
  extraStrongsCount: (book, strongs) =>
    fetch(`/api/extra/${encodeURIComponent(book)}/strongs-count/${encodeURIComponent(strongs)}`).then(r => r.json()),
  kjvChapter: (book, ch) =>
    fetch(`/api/kjv/chapter/${encodeURIComponent(book)}/${ch}`).then(r => r.json()),
  bsbChapter: (book, ch) =>
    fetch(`/api/bsb/chapter/${encodeURIComponent(book)}/${ch}`).then(r => r.json()),
  bsbAudio: (book, ch) =>
    fetch(`/api/bsb/audio/${encodeURIComponent(book)}/${ch}`)
      .then(r => r.ok ? r.json() : { url: null }).catch(() => ({ url: null })),
  // KJV public-domain narration (audiotreasure.com, music bg) — no key, public.
  kjvAudio: (book, ch) =>
    fetch(`/api/kjv/audio/${encodeURIComponent(book)}/${ch}`)
      .then(r => r.ok ? r.json() : { url: null }).catch(() => ({ url: null })),
  // ESV is the owner's personal text — every call carries the login token and the
  // server refuses anyone but the owner (404). esvStatus drives the toggle.
  esvStatus: () =>
    fetch(`/api/esv/status`, { headers: _authHeaders() })
      .then(r => r.json()).catch(() => ({ owner: false })),
  esvChapter: (book, ch) =>
    fetch(`/api/esv/chapter/${encodeURIComponent(book)}/${ch}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : []).catch(() => []),
  esvAudio: (book, ch) =>
    fetch(`/api/esv/audio/${encodeURIComponent(book)}/${ch}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : { url: null }).catch(() => ({ url: null })),
  // NIV is the owner's personal text too (same gate as ESV; text-only, no audio).
  nivStatus: () =>
    fetch(`/api/niv/status`, { headers: _authHeaders() })
      .then(r => r.json()).catch(() => ({ owner: false })),
  nivChapter: (book, ch) =>
    fetch(`/api/niv/chapter/${encodeURIComponent(book)}/${ch}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : []).catch(() => []),
  // Hebrew OT interlinear — PUBLIC text (public-domain WLC), no gate on the data.
  // hebStatus carries the token only to learn if the caller is the owner (the toggle
  // shows owner-only during rollout); the chapter fetch needs no auth.
  hebStatus: () =>
    fetch(`/api/hebrew/status`, { headers: _authHeaders() })
      .then(r => r.json()).catch(() => ({ available: false, owner: false })),
  hebChapter: (book, ch) =>
    fetch(`/api/hebrew/chapter/${encodeURIComponent(book)}/${ch}`)
      .then(r => r.ok ? r.json() : []).catch(() => []),
  // Visitor stats — count this visit (owner's own visits are skipped server-side),
  // ask if the logged-in user is the owner (drives the Stats tab), and fetch the
  // owner-only dashboard numbers.
  statsHit: () =>
    fetch(`/api/stats/hit`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ..._authHeaders() },
      body: JSON.stringify({ ref: document.referrer || "" }),
    }).catch(() => {}),
  statsOwner: () =>
    fetch(`/api/stats/owner`, { headers: _authHeaders() })
      .then(r => r.json()).catch(() => ({ owner: false })),
  stats: () =>
    fetch(`/api/stats`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : null).catch(() => null),
  // Admin-only: list accounts + set a role (admin page).
  adminUsers: () =>
    fetch(`/api/admin/users`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : null).catch(() => null),
  setRole: (userId, role) =>
    fetch(`/api/admin/role`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ..._authHeaders() },
      body: JSON.stringify({ user_id: userId, role }),
    }).then(r => r.ok ? r.json() : { ok: false }).catch(() => ({ ok: false })),
  // News watch (admin, or a no-login reader holding the share key) — scored news.db.
  newsMeta: () => {
    const k = _newsKey();
    return fetch(`/api/news/meta${k ? `?key=${encodeURIComponent(k)}` : ""}`, { headers: _authHeaders() })
      .then(r => r.json()).catch(() => ({ owner: false, reader: false, available: false }));
  },
  newsList: (params) => {
    const p = { ...(params || {}) };
    const k = _newsKey(); if (k) p.key = k;
    const qs = new URLSearchParams(p).toString();
    return fetch(`/api/news/list${qs ? "?" + qs : ""}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : { stories: [] }).catch(() => ({ stories: [] }));
  },
  newsCounts: (params) => {
    const p = { ...(params || {}) };
    const k = _newsKey(); if (k) p.key = k;
    const qs = new URLSearchParams(p).toString();
    return fetch(`/api/news/counts${qs ? "?" + qs : ""}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : null).catch(() => null);
  },
  newsShape: (params) => {
    const p = { ...(params || {}) };
    const k = _newsKey(); if (k) p.key = k;
    const qs = new URLSearchParams(p).toString();
    return fetch(`/api/news/shape${qs ? "?" + qs : ""}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : { available: false }).catch(() => ({ available: false }));
  },
  // The whole clustered feed in ONE fetch — the browser holds it and does every
  // sort/filter/score/date/thread/count locally (no server round-trip per interaction).
  newsAll: (params) => {
    const p = { ...(params || {}) };
    const k = _newsKey(); if (k) p.key = k;
    const qs = new URLSearchParams(p).toString();
    return fetch(`/api/news/all${qs ? "?" + qs : ""}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : { available: false, cards: [] })
      .catch(() => ({ available: false, cards: [] }));
  },
  newsStatus: (ids, status) => {
    const k = _newsKey();
    return fetch(`/api/news/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ..._authHeaders(), ...(k ? { "X-News-Key": k } : {}) },
      body: JSON.stringify({ ids, status }),
    }).then(r => r.ok ? r.json() : { ok: false }).catch(() => ({ ok: false }));
  },
  // Study modules (admin-only) — authored study content in study.db.
  studyEntries: (type) =>
    fetch(`/api/study/entries${type && type !== "all" ? `?type=${encodeURIComponent(type)}` : ""}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : null).catch(() => null),
  studyEntry: (id) =>
    fetch(`/api/study/entry/${encodeURIComponent(id)}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : null).catch(() => null),
  studySave: (entry) =>
    fetch(`/api/study/entry`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ..._authHeaders() },
      body: JSON.stringify(entry),
    }).then(r => r.ok ? r.json() : null).catch(() => null),
  studyDelete: (id) =>
    fetch(`/api/study/entry/${encodeURIComponent(id)}/delete`, { method: "POST", headers: _authHeaders() })
      .then(r => r.ok ? r.json() : { ok: false }).catch(() => ({ ok: false })),
  studyVerse: (ref) =>
    fetch(`/api/study/verse`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ..._authHeaders() },
      body: JSON.stringify({ ref }),
    }).then(r => r.ok ? r.json() : { verses: [] }).catch(() => ({ verses: [] })),
  // Nave's topical for a person/place name (subtopic headers + counts) on the metaV sidebar.
  studyForName: (name) =>
    fetch(`/api/study/for-name/${encodeURIComponent(name)}`, { headers: _authHeaders() })
      .then(r => r.ok ? r.json() : { sections: [] }).catch(() => ({ sections: [] })),
  // Which published concept studies cite this verse → the reader's "In studies:" line.
  studyForVerse: (book, chapter, verse) =>
    fetch(`/api/study/for-verse/${encodeURIComponent(book)}/${chapter}/${verse}`)
      .then(r => r.ok ? r.json() : { topics: [] }).catch(() => ({ topics: [] })),
  // Admin: draft a text-first intro for a topic (title + sections) → { intro }.
  studyDraftIntro: (payload) =>
    fetch(`/api/study/draft-intro`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ..._authHeaders() },
      body: JSON.stringify(payload),
    }).then(r => r.ok ? r.json() : { error: true }).catch(() => ({ error: true })),
  textSearch: (q, corpus, opts = {}) => {
    const p = new URLSearchParams({ q, corpus: corpus || "bsb", mode: opts.mode || "phrase" });
    p.set("partial", opts.partial === false ? "0" : "1");
    p.set("case", opts.caseSensitive ? "1" : "0");
    if (opts.exclude) p.set("exclude", opts.exclude);
    if (opts.from) p.set("from", opts.from);
    if (opts.to) p.set("to", opts.to);
    return fetch(`/api/text-search?${p.toString()}`).then(r => r.json());
  },
  summary: (book, ch) =>
    fetch(`/api/summary/${encodeURIComponent(book)}/${ch}`).then(r => r.json()),
  kjvVerse: (book, ch, v) =>
    fetch(`/api/kjv/verse/${encodeURIComponent(book)}/${ch}/${v}`).then(r => r.json()),
  kjvVerseWords: (book, ch, v) =>
    fetch(`/api/kjv/verse_words/${encodeURIComponent(book)}/${ch}/${v}`).then(r => r.json()),
  kjvVerseWordsBatch: (refs) =>
    fetch('/api/kjv/verse_words_batch', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(refs)}).then(r => r.json()),
  kjvStrongsCount: (strongs_id) =>
    fetch(`/api/kjv/strongs-count/${encodeURIComponent(strongs_id)}`).then(r => r.json()),
  kjvStrongsSearch: (strongs_id) =>
    fetch(`/api/kjv/strongs-search/${encodeURIComponent(strongs_id)}`).then(r => r.json()),
  bsbVerse: (book, ch, v) =>
    fetch(`/api/bsb/verse/${encodeURIComponent(book)}/${ch}/${v}`).then(r => r.json()),
  bsbVerseWords: (book, ch, v) =>
    fetch(`/api/bsb/verse_words/${encodeURIComponent(book)}/${ch}/${v}`).then(r => r.json()),
  bsbStrongsCount: (strongs_id) =>
    fetch(`/api/bsb/strongs-count/${encodeURIComponent(strongs_id)}`).then(r => r.json()),
  pnCount: (name) =>
    fetch(`/api/pn-count/${encodeURIComponent(name)}`).then(r => r.json()),
  // byBase=true counts ABP words on strongs_base (for a backfilled proper noun whose bare
  // strongs is '*' but whose base is a real H/G number — e.g. Eden -> H5731).
  strongsCountBase: (base) =>
    fetch(`/api/strongs-count/${encodeURIComponent(base)}?by=base`).then(r => r.json()),
  metavPerson: (name) =>
    fetch(`/api/metav/person/${encodeURIComponent(name)}`).then(r => r.json()),
  metavAiDescription: (name, book, chapter, verse) => {
    const q = (book && chapter && verse)
      ? `?book=${encodeURIComponent(book)}&chapter=${chapter}&verse=${verse}` : "";
    return fetch(`/api/metav/ai-description/${encodeURIComponent(name)}${q}`).then(r => r.json());
  },
  metavPlace: (name) =>
    fetch(`/api/metav/place/${encodeURIComponent(name)}`).then(r => r.json()),
  metavEntity: (name, book, chapter, verse) =>
    fetch(`/api/metav/entity/${encodeURIComponent(name)}?book=${encodeURIComponent(book)}&chapter=${chapter}&verse=${verse}`).then(r => r.json()),
  bdb: (sid) =>
    fetch(`/api/bdb/${encodeURIComponent(sid)}`).then(r => r.json()),
  crossRefsCurated: (book, chapter, verse) =>
    fetch(`/api/cross-references/curated/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.json()),
  lexiconLookup: (q) =>
    fetch(`/api/lexicon/lookup?q=${encodeURIComponent(q)}`).then(r => r.json()),
  lexiconProfile: (strongs, corpus) =>
    fetch(`/api/lexicon/profile/${encodeURIComponent(strongs)}${corpus ? `?corpus=${corpus}` : ""}`).then(r => r.json()),
  lexiconVerses: (strongs, book, corpus, gloss, testament) =>
    fetch(`/api/lexicon/verses/${encodeURIComponent(strongs)}/${encodeURIComponent(book)}?corpus=${corpus}${gloss ? `&gloss=${encodeURIComponent(gloss)}` : ""}${testament && testament !== "all" ? `&testament=${encodeURIComponent(testament)}` : ""}`).then(r => r.json()),
  lexiconBooks: (strongs, corpus, gloss) =>
    fetch(`/api/lexicon/books/${encodeURIComponent(strongs)}?corpus=${corpus}${gloss ? `&gloss=${encodeURIComponent(gloss)}` : ""}`).then(r => r.json()),
  lexiconEnglish: (q, corpus, testament) =>
    fetch(`/api/lexicon/english?q=${encodeURIComponent(q)}&corpus=${encodeURIComponent(corpus)}${testament && testament !== "all" ? `&testament=${encodeURIComponent(testament)}` : ""}`).then(r => r.json()),
};

// Extract proper noun name from a multi-word gloss, skipping function words
const _PN_STOP = new Set(["And","But","Or","The","A","An","In","Of","To","For","With","From","By","At","His","Her","Its","Their","My","Your","Our"]);
function extractProperName(gloss) {
  if (!gloss) return "";
  const clean = gloss.replace(/[^a-zA-Z\s'-]/g, "").trim();
  const proper = clean.split(/\s+/).find(w => /^[A-Z]/.test(w) && !_PN_STOP.has(w));
  return proper || "";
}

// ============================================================
// DATA SHAPING
// ============================================================
// ---- Canonical Strong's-number handling (single source of truth) --------
// strongsBare: drop any G/H prefix, keep dotted variants. "G4151"->"4151",
//   "1510.7.3"->"1510.7.3", "H7307"->"7307".
// strongsTag: display form. "*"/empty -> "PN"; preserves an explicit H prefix;
//   bare numbers above the Greek max (5624) read as Hebrew.
function strongsBare(snum) {
  return String(snum || "").replace(/^[GH]/i, "");
}
function strongsTag(snum) {
  if (!snum || snum === "*") return "PN";
  const s = String(snum);
  const hasH = /^H/i.test(s);
  const bare = strongsBare(s);
  const n = parseInt(bare, 10);
  if (hasH) return `H${bare}`;
  return `${!isNaN(n) && n > 5624 ? "H" : "G"}${bare}`;
}

// ---- Morphology decoder (words.morph) -----------------------------------
// OT = CATSS dotted (V.AAI3S, N.GSM, RP.GS, bare C/P/D/X); NT = Robinson
// hyphen (V-PAI-3S, N-ASF, P-1GS, PRT-N, CONJ). Verbs start V in both, but
// the rest CONFLICTS by scheme (CATSS perfect=X/imperative=D; Robinson
// perfect=R/imperative=M) → separate tables. Returns e.g.
// "Verb · Aorist · Active · Indicative · 3rd person · Singular", or "" when
// morph is null/unmappable (caller hides the line — never shows "unknown").
const _CASE = { N:"Nominative", V:"Vocative", G:"Genitive", D:"Dative", A:"Accusative" };
const _NUM  = { S:"Singular", P:"Plural", D:"Dual" };
const _GEN  = { M:"Masculine", F:"Feminine", N:"Neuter" };
const _PERS = { "1":"1st person", "2":"2nd person", "3":"3rd person" };

const _CATSS_POS = { N:"Noun", A:"Adjective", RA:"Article", RP:"Pronoun",
  RD:"Demonstrative pronoun", RR:"Relative pronoun", RI:"Interrogative pronoun",
  RX:"Indefinite pronoun", V:"Verb", C:"Conjunction", P:"Preposition",
  D:"Adverb", X:"Particle", M:"Numeral", I:"Interjection" };
const _CATSS_TENSE = { P:"Present", I:"Imperfect", F:"Future", A:"Aorist", X:"Perfect", Y:"Pluperfect" };
const _CATSS_VOICE = { A:"Active", M:"Middle", P:"Passive" };
const _CATSS_MOOD  = { I:"Indicative", D:"Imperative", S:"Subjunctive", O:"Optative", N:"Infinitive", P:"Participle" };
// CATSS lumps several pronoun sub-classes under RD; disambiguate by lemma so
// αὐτός (3rd-person personal, = Robinson P) and the reflexives/reciprocal don't
// all read "Demonstrative". Anything not listed (οὗτος/ἐκεῖνος/ὅδε/τοιοῦτος…)
// keeps the demonstrative default.
const _CATSS_RD_LEMMA = {
  "αὐτός":"Pronoun", "ἑαυτοῦ":"Reflexive pronoun", "σεαυτοῦ":"Reflexive pronoun",
  "ἐμαυτοῦ":"Reflexive pronoun", "ἀλλήλων":"Reciprocal pronoun",
};

const _ROB_POS = { N:"Noun", A:"Adjective", T:"Article", P:"Pronoun",
  R:"Relative pronoun", D:"Demonstrative pronoun", K:"Correlative pronoun",
  I:"Interrogative pronoun", X:"Indefinite pronoun", Q:"Correlative pronoun",
  F:"Reflexive pronoun", S:"Possessive pronoun", C:"Reciprocal pronoun",
  V:"Verb", CONJ:"Conjunction", PREP:"Preposition", ADV:"Adverb",
  PRT:"Particle", COND:"Conditional", INJ:"Interjection", HEB:"Hebrew", ARAM:"Aramaic" };
const _ROB_TENSE = { P:"Present", I:"Imperfect", F:"Future", A:"Aorist", R:"Perfect", L:"Pluperfect" };
const _ROB_VOICE = { A:"Active", M:"Middle", P:"Passive", E:"Middle/Passive",
  D:"Middle deponent", O:"Passive deponent", N:"Middle/Passive deponent" };
const _ROB_MOOD  = { I:"Indicative", S:"Subjunctive", O:"Optative", M:"Imperative", N:"Infinitive", P:"Participle" };

function _decodeCNG(s) {            // case + number + (optional) gender, by position
  const out = [];
  if (s[0] && _CASE[s[0]]) out.push(_CASE[s[0]]);
  if (s[1] && _NUM[s[1]])  out.push(_NUM[s[1]]);
  if (s[2] && _GEN[s[2]])  out.push(_GEN[s[2]]);
  return out;
}

function decodeMorph(morph, lemma, snum) {
  if (!morph) return "";
  const m = morph.trim();
  let parts = [];
  try {
    if (m.indexOf(".") >= 0) {                         // ---- CATSS (OT) ----
      const dot = m.indexOf(".");
      const pos = m.slice(0, dot), p = m.slice(dot + 1);
      if (pos === "V") {
        parts = ["Verb"];
        if (_CATSS_TENSE[p[0]]) parts.push(_CATSS_TENSE[p[0]]);
        if (_CATSS_VOICE[p[1]]) parts.push(_CATSS_VOICE[p[1]]);
        if (_CATSS_MOOD[p[2]])  parts.push(_CATSS_MOOD[p[2]]);
        const rest = p.slice(3);
        if (p[2] === "P")      parts.push(..._decodeCNG(rest));      // participle
        else if (p[2] !== "N" && rest) {                            // finite (N = infinitive)
          if (_PERS[rest[0]]) parts.push(_PERS[rest[0]]);
          if (_NUM[rest[1]])  parts.push(_NUM[rest[1]]);
        }
      } else {
        let label = _CATSS_POS[pos];
        if (!label) return "";
        if (pos === "RD") label = _CATSS_RD_LEMMA[(lemma || "").normalize("NFC")] || "Demonstrative pronoun";
        parts = [label, ..._decodeCNG(p)];
      }
    } else if (m.indexOf("-") >= 0) {                  // ---- Robinson (NT) ----
      const seg = m.split("-");
      const pos = seg[0];
      if (pos === "V") {
        let tvm = seg[1] || "";
        if (/^[23]/.test(tvm)) tvm = tvm.slice(1);     // 2nd aorist/perfect
        parts = ["Verb"];
        if (_ROB_TENSE[tvm[0]]) parts.push(_ROB_TENSE[tvm[0]]);
        if (_ROB_VOICE[tvm[1]]) parts.push(_ROB_VOICE[tvm[1]]);
        if (_ROB_MOOD[tvm[2]])  parts.push(_ROB_MOOD[tvm[2]]);
        const rest = seg[2] || "";
        if (rest) {
          if (tvm[2] === "P") parts.push(..._decodeCNG(rest));      // participle
          else {
            if (_PERS[rest[0]]) parts.push(_PERS[rest[0]]);
            if (_NUM[rest[1]])  parts.push(_NUM[rest[1]]);
          }
        }
      } else if (pos === "PRT") {
        parts = ["Particle"];
        if (seg[1] === "N") parts.push("Negative");
        else if (seg[1] === "I") parts.push("Interrogative");
      } else {
        const label = _ROB_POS[pos];
        if (!label) return "";
        const p = seg[1] || "";
        if (p === "PRI") return "Proper noun (indeclinable)";
        if (p === "NUI") return "Numeral (indeclinable)";
        parts = [label];
        if (pos === "P" && /^[123]/.test(p)) {         // personal pron: person·case·number
          if (_PERS[p[0]]) parts.push(_PERS[p[0]]);
          if (_CASE[p[1]]) parts.push(_CASE[p[1]]);
          if (_NUM[p[2]])  parts.push(_NUM[p[2]]);
        } else {
          parts.push(..._decodeCNG(p));                // incl. αὐτός P-GSM, drops trailing -T
        }
      }
    } else {                                           // ---- bare POS token ----
      const label = (m.length === 1 ? _CATSS_POS[m] : _ROB_POS[m]);
      if (!label) return "";
      parts = [label];
    }
  } catch (e) { return ""; }
  // Two-ending adjectives (masculine & feminine are one form): the OT (CATSS) /
  // NT (Robinson) morph source often just defaults such a word to Masculine. For
  // the words it never resolves (never tags Feminine — see scripts/build_two_ending.py)
  // show "Masculine/Feminine" rather than assert a gender the form can't carry;
  // Feminine/Neuter tags are trusted as-is. snum = strongs_base ("G517").
  if (snum && parts[0] === "Adjective") {
    const soft = (m.indexOf(".") >= 0)
      ? (typeof TWO_END_SOFT_OT !== "undefined" && TWO_END_SOFT_OT)
      : (typeof TWO_END_SOFT_NT !== "undefined" && TWO_END_SOFT_NT);
    if (soft && soft.has(snum)) {
      const gi = parts.indexOf("Masculine");
      if (gi >= 0) parts[gi] = "Masculine/Feminine";
    }
  }
  return parts.filter(Boolean).join(" · ");
}

// Which Strong's number a detail entry shows: a proper-noun slot ('*') stays '*';
// otherwise prefer the bare `strongs`, falling back to `strongs_base`.
function entrySnum(s) {
  return s.strongs_base === "*" ? "*" : (s.strongs && s.strongs !== "*" ? s.strongs : s.strongs_base);
}

// Shared core of a detail-panel word entry. Callers add their own `id`, `gloss`
// source, and any extra fields (gloss_head, morph, is_primary, …).
function wordEntryCore(src, { ref, book, chapter, verse, gloss }) {
  return {
    strongs: strongsTag(entrySnum(src)),
    strongs_base: src.strongs_base,
    strongs_raw: entrySnum(src),
    greek: src.lemma || "",
    translit: src.translit || "",
    gloss: gloss || "",
    ref,
    book,
    chapter,
    verse,
    definition: src.strongs_def || "",
    derivation: src.derivation || "",
    is_function: src.is_function || false,
    is_pn: src.is_pn || false,
  };
}

function makeEntry(r, idx) {
  return {
    id: `${entrySnum(r)}-${r.book}-${r.chapter}-${r.verse}-${idx}`,
    ...wordEntryCore(r, { ref: r.ref, book: r.book, chapter: r.chapter, verse: r.verse, gloss: r.gloss }),
    gloss_head: r.gloss_head || "",
  };
}

function flattenAiResults(verses) {
  const entries = [];
  let idx = 0;
  for (const v of verses) {
    for (const w of (v.words || [])) {
      entries.push({
        id: `ai-${v.book}-${v.chapter}-${v.verse}-${entrySnum(w)}-${idx++}`,
        ...wordEntryCore(w, { ref: v.ref, book: v.book, chapter: v.chapter, verse: v.verse, gloss: w.gloss }),
        is_primary: v.is_primary || false,
        is_additional: v.is_additional || false,
      });
    }
  }
  return entries;
}

// ============================================================
// BOOK LABELS
// ============================================================
const NT_BOOKS = new Set([
  "Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph",
  "Php","Col","1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas",
  "1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev",
]);

const BOOK_ORDER = {};
[
  "Gen","Exo","Lev","Num","Deu","Jos","Jdg","Rth","1Sa","2Sa",
  "1Ki","2Ki","1Ch","2Ch","Ezr","Neh","Est","Job","Psa","Pro",
  "Ecc","Son","Isa","Jer","Lam","Eze","Dan","Hos","Joe","Amo",
  "Oba","Jon","Mic","Nah","Hab","Zep","Hag","Zec","Mal",
  "Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph",
  "Php","Col","1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas",
  "1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev",
].forEach((b, i) => { BOOK_ORDER[b] = i; });

const BOOK_LABELS = {
  Gen: "Genesis",      Exo: "Exodus",       Lev: "Leviticus",    Num: "Numbers",
  Deu: "Deuteronomy",  Jos: "Joshua",        Jdg: "Judges",       Rth: "Ruth",
  "1Sa": "1 Samuel",   "2Sa": "2 Samuel",    "1Ki": "1 Kings",    "2Ki": "2 Kings",
  "1Ch": "1 Chronicles", "2Ch": "2 Chronicles", Ezr: "Ezra",      Neh: "Nehemiah",
  Est: "Esther",       Job: "Job",           Psa: "Psalms",       Pro: "Proverbs",
  Ecc: "Ecclesiastes", Son: "Song of Solomon", Isa: "Isaiah",     Jer: "Jeremiah",
  Lam: "Lamentations", Eze: "Ezekiel",       Dan: "Daniel",       Hos: "Hosea",
  Joe: "Joel",         Amo: "Amos",          Oba: "Obadiah",      Jon: "Jonah",
  Mic: "Micah",        Nah: "Nahum",         Hab: "Habakkuk",     Zep: "Zephaniah",
  Hag: "Haggai",       Zec: "Zechariah",     Mal: "Malachi",
  Mat: "Matthew",      Mar: "Mark",          Luk: "Luke",         Joh: "John",
  Act: "Acts",         Rom: "Romans",        "1Co": "1 Corinthians", "2Co": "2 Corinthians",
  Gal: "Galatians",    Eph: "Ephesians",     Php: "Philippians",  Col: "Colossians",
  "1Th": "1 Thessalonians", "2Th": "2 Thessalonians", "1Ti": "1 Timothy", "2Ti": "2 Timothy",
  Tit: "Titus",        Phm: "Philemon",      Heb: "Hebrews",      Jas: "James",
  "1Pe": "1 Peter",    "2Pe": "2 Peter",     "1Jn": "1 John",     "2Jn": "2 John",
  "3Jn": "3 John",     Jud: "Jude",          Rev: "Revelation",
};
