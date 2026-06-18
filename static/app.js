function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  useState,
  useEffect,
  useLayoutEffect,
  useRef,
  useMemo
} = React;
const _ARTICLE_RE = /^((?:the|a|an|his|her|its|of|my|your|their|our)\s+)+/i;
function stripArticles(s) {
  if (!s) return s;
  return s.replace(_ARTICLE_RE, "").trim() || s;
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
  let last = 0,
    m,
    key = 0;
  while ((m = _INLINE_MD_RE.exec(text)) !== null) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    if (m[1] != null) nodes.push(/*#__PURE__*/React.createElement("strong", {
      key: key++
    }, m[1]));else nodes.push(/*#__PURE__*/React.createElement("em", {
      key: key++
    }, m[2]));
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
    const a = typeof NotesStore !== "undefined" && NotesStore.auth();
    return a && a.token ? {
      "Authorization": "Bearer " + a.token
    } : {};
  } catch (e) {
    return {};
  }
}
const api = {
  search: (q, phrase = false) => fetch(`/api/search?q=${encodeURIComponent(q)}&phrase=${phrase ? 1 : 0}`).then(r => r.json()),
  aiSearch: q => fetch(`/api/ai-search?q=${encodeURIComponent(q)}`, {
    headers: _authHeaders()
  }).then(r => r.json()),
  verse: (book, chapter, verse) => fetch(`/api/verse/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.json()),
  verseWords: (book, chapter, verse) => fetch(`/api/verse-words/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.json()),
  hebVerseWords: (book, chapter, verse) => fetch(`/api/hebrew/verse-words/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.json()),
  strongsCount: strongs_base => fetch(`/api/strongs-count/${encodeURIComponent(strongs_base)}`).then(r => r.json()),
  lsj: (lemma, strongs) => {
    const path = lemma || strongs || '';
    if (!path) return Promise.resolve({
      error: 'not found'
    });
    const qs = strongs ? `?strongs=${encodeURIComponent(strongs)}` : '';
    return fetch(`/api/lsj/${encodeURIComponent(path)}${qs}`).then(r => r.json());
  },
  lsjSummary: (key, strongs, book, chapter, verse) => {
    const hasDot = strongs && strongs.includes('.');
    const path = key || (hasDot ? strongs : '');
    if (!path) return Promise.resolve({
      error: 'not found'
    });
    const p = new URLSearchParams();
    if (hasDot) p.set('strongs', strongs);
    if (book && chapter && verse) {
      p.set('book', book);
      p.set('chapter', chapter);
      p.set('verse', verse);
    }
    const qs = p.toString() ? `?${p}` : '';
    return fetch(`/api/lsj-summary/${encodeURIComponent(path)}${qs}`).then(r => r.json());
  },
  books: () => fetch("/api/books").then(r => r.json()),
  chronological: () => fetch("/static/chronological.json").then(r => r.json()),
  chronoIntro: day => fetch(`/api/chrono/intro/${day}`).then(r => r.json()),
  chapter: (book, ch) => fetch(`/api/chapter/${encodeURIComponent(book)}/${ch}`).then(r => r.json()),
  extraChapter: (book, ch) => fetch(`/api/extra/${encodeURIComponent(book)}/chapter/${ch}`).then(r => r.json()),
  extraStrongsCount: (book, strongs) => fetch(`/api/extra/${encodeURIComponent(book)}/strongs-count/${encodeURIComponent(strongs)}`).then(r => r.json()),
  kjvChapter: (book, ch) => fetch(`/api/kjv/chapter/${encodeURIComponent(book)}/${ch}`).then(r => r.json()),
  bsbChapter: (book, ch) => fetch(`/api/bsb/chapter/${encodeURIComponent(book)}/${ch}`).then(r => r.json()),
  bsbAudio: (book, ch) => fetch(`/api/bsb/audio/${encodeURIComponent(book)}/${ch}`).then(r => r.ok ? r.json() : {
    url: null
  }).catch(() => ({
    url: null
  })),
  // KJV public-domain narration (audiotreasure.com, music bg) — no key, public.
  kjvAudio: (book, ch) => fetch(`/api/kjv/audio/${encodeURIComponent(book)}/${ch}`).then(r => r.ok ? r.json() : {
    url: null
  }).catch(() => ({
    url: null
  })),
  // ESV is the owner's personal text — every call carries the login token and the
  // server refuses anyone but the owner (404). esvStatus drives the toggle.
  esvStatus: () => fetch(`/api/esv/status`, {
    headers: _authHeaders()
  }).then(r => r.json()).catch(() => ({
    owner: false
  })),
  esvChapter: (book, ch) => fetch(`/api/esv/chapter/${encodeURIComponent(book)}/${ch}`, {
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : []).catch(() => []),
  esvAudio: (book, ch) => fetch(`/api/esv/audio/${encodeURIComponent(book)}/${ch}`, {
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : {
    url: null
  }).catch(() => ({
    url: null
  })),
  // NIV is the owner's personal text too (same gate as ESV; text-only, no audio).
  nivStatus: () => fetch(`/api/niv/status`, {
    headers: _authHeaders()
  }).then(r => r.json()).catch(() => ({
    owner: false
  })),
  nivChapter: (book, ch) => fetch(`/api/niv/chapter/${encodeURIComponent(book)}/${ch}`, {
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : []).catch(() => []),
  // Hebrew OT interlinear — PUBLIC text (public-domain WLC), no gate on the data.
  // hebStatus carries the token only to learn if the caller is the owner (the toggle
  // shows owner-only during rollout); the chapter fetch needs no auth.
  hebStatus: () => fetch(`/api/hebrew/status`, {
    headers: _authHeaders()
  }).then(r => r.json()).catch(() => ({
    available: false,
    owner: false
  })),
  hebChapter: (book, ch) => fetch(`/api/hebrew/chapter/${encodeURIComponent(book)}/${ch}`).then(r => r.ok ? r.json() : []).catch(() => []),
  // Visitor stats — count this visit (owner's own visits are skipped server-side),
  // ask if the logged-in user is the owner (drives the Stats tab), and fetch the
  // owner-only dashboard numbers.
  statsHit: () => fetch(`/api/stats/hit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ..._authHeaders()
    },
    body: JSON.stringify({
      ref: document.referrer || ""
    })
  }).catch(() => {}),
  statsOwner: () => fetch(`/api/stats/owner`, {
    headers: _authHeaders()
  }).then(r => r.json()).catch(() => ({
    owner: false
  })),
  stats: () => fetch(`/api/stats`, {
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : null).catch(() => null),
  // Admin-only: list accounts + set a role (admin page).
  adminUsers: () => fetch(`/api/admin/users`, {
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : null).catch(() => null),
  setRole: (userId, role) => fetch(`/api/admin/role`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ..._authHeaders()
    },
    body: JSON.stringify({
      user_id: userId,
      role
    })
  }).then(r => r.ok ? r.json() : {
    ok: false
  }).catch(() => ({
    ok: false
  })),
  // Study modules (admin-only) — authored study content in study.db.
  studyEntries: type => fetch(`/api/study/entries${type && type !== "all" ? `?type=${encodeURIComponent(type)}` : ""}`, {
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : null).catch(() => null),
  studyEntry: id => fetch(`/api/study/entry/${encodeURIComponent(id)}`, {
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : null).catch(() => null),
  studySave: entry => fetch(`/api/study/entry`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ..._authHeaders()
    },
    body: JSON.stringify(entry)
  }).then(r => r.ok ? r.json() : null).catch(() => null),
  studyDelete: id => fetch(`/api/study/entry/${encodeURIComponent(id)}/delete`, {
    method: "POST",
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : {
    ok: false
  }).catch(() => ({
    ok: false
  })),
  studyVerse: ref => fetch(`/api/study/verse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ..._authHeaders()
    },
    body: JSON.stringify({
      ref
    })
  }).then(r => r.ok ? r.json() : {
    verses: []
  }).catch(() => ({
    verses: []
  })),
  // Nave's topical for a person/place name (subtopic headers + counts) on the metaV sidebar.
  studyForName: name => fetch(`/api/study/for-name/${encodeURIComponent(name)}`, {
    headers: _authHeaders()
  }).then(r => r.ok ? r.json() : {
    sections: []
  }).catch(() => ({
    sections: []
  })),
  // Which published concept studies cite this verse → the reader's "In studies:" line.
  studyForVerse: (book, chapter, verse) => fetch(`/api/study/for-verse/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.ok ? r.json() : {
    topics: []
  }).catch(() => ({
    topics: []
  })),
  // Admin: draft a text-first intro for a topic (title + sections) → { intro }.
  studyDraftIntro: payload => fetch(`/api/study/draft-intro`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ..._authHeaders()
    },
    body: JSON.stringify(payload)
  }).then(r => r.ok ? r.json() : {
    error: true
  }).catch(() => ({
    error: true
  })),
  textSearch: (q, corpus, opts = {}) => {
    const p = new URLSearchParams({
      q,
      corpus: corpus || "bsb",
      mode: opts.mode || "phrase"
    });
    p.set("partial", opts.partial === false ? "0" : "1");
    p.set("case", opts.caseSensitive ? "1" : "0");
    if (opts.exclude) p.set("exclude", opts.exclude);
    if (opts.from) p.set("from", opts.from);
    if (opts.to) p.set("to", opts.to);
    return fetch(`/api/text-search?${p.toString()}`).then(r => r.json());
  },
  summary: (book, ch) => fetch(`/api/summary/${encodeURIComponent(book)}/${ch}`).then(r => r.json()),
  kjvVerse: (book, ch, v) => fetch(`/api/kjv/verse/${encodeURIComponent(book)}/${ch}/${v}`).then(r => r.json()),
  kjvVerseWords: (book, ch, v) => fetch(`/api/kjv/verse_words/${encodeURIComponent(book)}/${ch}/${v}`).then(r => r.json()),
  kjvVerseWordsBatch: refs => fetch('/api/kjv/verse_words_batch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(refs)
  }).then(r => r.json()),
  kjvStrongsCount: strongs_id => fetch(`/api/kjv/strongs-count/${encodeURIComponent(strongs_id)}`).then(r => r.json()),
  kjvStrongsSearch: strongs_id => fetch(`/api/kjv/strongs-search/${encodeURIComponent(strongs_id)}`).then(r => r.json()),
  bsbVerse: (book, ch, v) => fetch(`/api/bsb/verse/${encodeURIComponent(book)}/${ch}/${v}`).then(r => r.json()),
  bsbVerseWords: (book, ch, v) => fetch(`/api/bsb/verse_words/${encodeURIComponent(book)}/${ch}/${v}`).then(r => r.json()),
  bsbStrongsCount: strongs_id => fetch(`/api/bsb/strongs-count/${encodeURIComponent(strongs_id)}`).then(r => r.json()),
  pnCount: name => fetch(`/api/pn-count/${encodeURIComponent(name)}`).then(r => r.json()),
  metavPerson: name => fetch(`/api/metav/person/${encodeURIComponent(name)}`).then(r => r.json()),
  metavAiDescription: name => fetch(`/api/metav/ai-description/${encodeURIComponent(name)}`).then(r => r.json()),
  metavPlace: name => fetch(`/api/metav/place/${encodeURIComponent(name)}`).then(r => r.json()),
  bdb: sid => fetch(`/api/bdb/${encodeURIComponent(sid)}`).then(r => r.json()),
  crossRefsCurated: (book, chapter, verse) => fetch(`/api/cross-references/curated/${encodeURIComponent(book)}/${chapter}/${verse}`).then(r => r.json()),
  lexiconLookup: q => fetch(`/api/lexicon/lookup?q=${encodeURIComponent(q)}`).then(r => r.json()),
  lexiconProfile: (strongs, corpus) => fetch(`/api/lexicon/profile/${encodeURIComponent(strongs)}${corpus ? `?corpus=${corpus}` : ""}`).then(r => r.json()),
  lexiconVerses: (strongs, book, corpus, gloss) => fetch(`/api/lexicon/verses/${encodeURIComponent(strongs)}/${encodeURIComponent(book)}?corpus=${corpus}${gloss ? `&gloss=${encodeURIComponent(gloss)}` : ""}`).then(r => r.json()),
  lexiconBooks: (strongs, corpus, gloss) => fetch(`/api/lexicon/books/${encodeURIComponent(strongs)}?corpus=${corpus}${gloss ? `&gloss=${encodeURIComponent(gloss)}` : ""}`).then(r => r.json()),
  lexiconEnglish: (q, corpus, testament) => fetch(`/api/lexicon/english?q=${encodeURIComponent(q)}&corpus=${encodeURIComponent(corpus)}${testament && testament !== "all" ? `&testament=${encodeURIComponent(testament)}` : ""}`).then(r => r.json())
};

// Extract proper noun name from a multi-word gloss, skipping function words
const _PN_STOP = new Set(["And", "But", "Or", "The", "A", "An", "In", "Of", "To", "For", "With", "From", "By", "At", "His", "Her", "Its", "Their", "My", "Your", "Our"]);
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
const _CASE = {
  N: "Nominative",
  V: "Vocative",
  G: "Genitive",
  D: "Dative",
  A: "Accusative"
};
const _NUM = {
  S: "Singular",
  P: "Plural",
  D: "Dual"
};
const _GEN = {
  M: "Masculine",
  F: "Feminine",
  N: "Neuter"
};
const _PERS = {
  "1": "1st person",
  "2": "2nd person",
  "3": "3rd person"
};
const _CATSS_POS = {
  N: "Noun",
  A: "Adjective",
  RA: "Article",
  RP: "Pronoun",
  RD: "Demonstrative pronoun",
  RR: "Relative pronoun",
  RI: "Interrogative pronoun",
  RX: "Indefinite pronoun",
  V: "Verb",
  C: "Conjunction",
  P: "Preposition",
  D: "Adverb",
  X: "Particle",
  M: "Numeral",
  I: "Interjection"
};
const _CATSS_TENSE = {
  P: "Present",
  I: "Imperfect",
  F: "Future",
  A: "Aorist",
  X: "Perfect",
  Y: "Pluperfect"
};
const _CATSS_VOICE = {
  A: "Active",
  M: "Middle",
  P: "Passive"
};
const _CATSS_MOOD = {
  I: "Indicative",
  D: "Imperative",
  S: "Subjunctive",
  O: "Optative",
  N: "Infinitive",
  P: "Participle"
};
// CATSS lumps several pronoun sub-classes under RD; disambiguate by lemma so
// αὐτός (3rd-person personal, = Robinson P) and the reflexives/reciprocal don't
// all read "Demonstrative". Anything not listed (οὗτος/ἐκεῖνος/ὅδε/τοιοῦτος…)
// keeps the demonstrative default.
const _CATSS_RD_LEMMA = {
  "αὐτός": "Pronoun",
  "ἑαυτοῦ": "Reflexive pronoun",
  "σεαυτοῦ": "Reflexive pronoun",
  "ἐμαυτοῦ": "Reflexive pronoun",
  "ἀλλήλων": "Reciprocal pronoun"
};
const _ROB_POS = {
  N: "Noun",
  A: "Adjective",
  T: "Article",
  P: "Pronoun",
  R: "Relative pronoun",
  D: "Demonstrative pronoun",
  K: "Correlative pronoun",
  I: "Interrogative pronoun",
  X: "Indefinite pronoun",
  Q: "Correlative pronoun",
  F: "Reflexive pronoun",
  S: "Possessive pronoun",
  C: "Reciprocal pronoun",
  V: "Verb",
  CONJ: "Conjunction",
  PREP: "Preposition",
  ADV: "Adverb",
  PRT: "Particle",
  COND: "Conditional",
  INJ: "Interjection",
  HEB: "Hebrew",
  ARAM: "Aramaic"
};
const _ROB_TENSE = {
  P: "Present",
  I: "Imperfect",
  F: "Future",
  A: "Aorist",
  R: "Perfect",
  L: "Pluperfect"
};
const _ROB_VOICE = {
  A: "Active",
  M: "Middle",
  P: "Passive",
  E: "Middle/Passive",
  D: "Middle deponent",
  O: "Passive deponent",
  N: "Middle/Passive deponent"
};
const _ROB_MOOD = {
  I: "Indicative",
  S: "Subjunctive",
  O: "Optative",
  M: "Imperative",
  N: "Infinitive",
  P: "Participle"
};
function _decodeCNG(s) {
  // case + number + (optional) gender, by position
  const out = [];
  if (s[0] && _CASE[s[0]]) out.push(_CASE[s[0]]);
  if (s[1] && _NUM[s[1]]) out.push(_NUM[s[1]]);
  if (s[2] && _GEN[s[2]]) out.push(_GEN[s[2]]);
  return out;
}
function decodeMorph(morph, lemma, snum) {
  if (!morph) return "";
  const m = morph.trim();
  let parts = [];
  try {
    if (m.indexOf(".") >= 0) {
      // ---- CATSS (OT) ----
      const dot = m.indexOf(".");
      const pos = m.slice(0, dot),
        p = m.slice(dot + 1);
      if (pos === "V") {
        parts = ["Verb"];
        if (_CATSS_TENSE[p[0]]) parts.push(_CATSS_TENSE[p[0]]);
        if (_CATSS_VOICE[p[1]]) parts.push(_CATSS_VOICE[p[1]]);
        if (_CATSS_MOOD[p[2]]) parts.push(_CATSS_MOOD[p[2]]);
        const rest = p.slice(3);
        if (p[2] === "P") parts.push(..._decodeCNG(rest)); // participle
        else if (p[2] !== "N" && rest) {
          // finite (N = infinitive)
          if (_PERS[rest[0]]) parts.push(_PERS[rest[0]]);
          if (_NUM[rest[1]]) parts.push(_NUM[rest[1]]);
        }
      } else {
        let label = _CATSS_POS[pos];
        if (!label) return "";
        if (pos === "RD") label = _CATSS_RD_LEMMA[(lemma || "").normalize("NFC")] || "Demonstrative pronoun";
        parts = [label, ..._decodeCNG(p)];
      }
    } else if (m.indexOf("-") >= 0) {
      // ---- Robinson (NT) ----
      const seg = m.split("-");
      const pos = seg[0];
      if (pos === "V") {
        let tvm = seg[1] || "";
        if (/^[23]/.test(tvm)) tvm = tvm.slice(1); // 2nd aorist/perfect
        parts = ["Verb"];
        if (_ROB_TENSE[tvm[0]]) parts.push(_ROB_TENSE[tvm[0]]);
        if (_ROB_VOICE[tvm[1]]) parts.push(_ROB_VOICE[tvm[1]]);
        if (_ROB_MOOD[tvm[2]]) parts.push(_ROB_MOOD[tvm[2]]);
        const rest = seg[2] || "";
        if (rest) {
          if (tvm[2] === "P") parts.push(..._decodeCNG(rest)); // participle
          else {
            if (_PERS[rest[0]]) parts.push(_PERS[rest[0]]);
            if (_NUM[rest[1]]) parts.push(_NUM[rest[1]]);
          }
        }
      } else if (pos === "PRT") {
        parts = ["Particle"];
        if (seg[1] === "N") parts.push("Negative");else if (seg[1] === "I") parts.push("Interrogative");
      } else {
        const label = _ROB_POS[pos];
        if (!label) return "";
        const p = seg[1] || "";
        if (p === "PRI") return "Proper noun (indeclinable)";
        if (p === "NUI") return "Numeral (indeclinable)";
        parts = [label];
        if (pos === "P" && /^[123]/.test(p)) {
          // personal pron: person·case·number
          if (_PERS[p[0]]) parts.push(_PERS[p[0]]);
          if (_CASE[p[1]]) parts.push(_CASE[p[1]]);
          if (_NUM[p[2]]) parts.push(_NUM[p[2]]);
        } else {
          parts.push(..._decodeCNG(p)); // incl. αὐτός P-GSM, drops trailing -T
        }
      }
    } else {
      // ---- bare POS token ----
      const label = m.length === 1 ? _CATSS_POS[m] : _ROB_POS[m];
      if (!label) return "";
      parts = [label];
    }
  } catch (e) {
    return "";
  }
  // Two-ending adjectives (masculine & feminine are one form): the OT (CATSS) /
  // NT (Robinson) morph source often just defaults such a word to Masculine. For
  // the words it never resolves (never tags Feminine — see scripts/build_two_ending.py)
  // show "Masculine/Feminine" rather than assert a gender the form can't carry;
  // Feminine/Neuter tags are trusted as-is. snum = strongs_base ("G517").
  if (snum && parts[0] === "Adjective") {
    const soft = m.indexOf(".") >= 0 ? typeof TWO_END_SOFT_OT !== "undefined" && TWO_END_SOFT_OT : typeof TWO_END_SOFT_NT !== "undefined" && TWO_END_SOFT_NT;
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
  return s.strongs_base === "*" ? "*" : s.strongs && s.strongs !== "*" ? s.strongs : s.strongs_base;
}

// Shared core of a detail-panel word entry. Callers add their own `id`, `gloss`
// source, and any extra fields (gloss_head, morph, is_primary, …).
function wordEntryCore(src, {
  ref,
  book,
  chapter,
  verse,
  gloss
}) {
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
    is_pn: src.is_pn || false
  };
}
function makeEntry(r, idx) {
  return {
    id: `${entrySnum(r)}-${r.book}-${r.chapter}-${r.verse}-${idx}`,
    ...wordEntryCore(r, {
      ref: r.ref,
      book: r.book,
      chapter: r.chapter,
      verse: r.verse,
      gloss: r.gloss
    }),
    gloss_head: r.gloss_head || ""
  };
}
function flattenAiResults(verses) {
  const entries = [];
  let idx = 0;
  for (const v of verses) {
    for (const w of v.words || []) {
      entries.push({
        id: `ai-${v.book}-${v.chapter}-${v.verse}-${entrySnum(w)}-${idx++}`,
        ...wordEntryCore(w, {
          ref: v.ref,
          book: v.book,
          chapter: v.chapter,
          verse: v.verse,
          gloss: w.gloss
        }),
        is_primary: v.is_primary || false,
        is_additional: v.is_additional || false
      });
    }
  }
  return entries;
}

// ============================================================
// BOOK LABELS
// ============================================================
const NT_BOOKS = new Set(["Mat", "Mar", "Luk", "Joh", "Act", "Rom", "1Co", "2Co", "Gal", "Eph", "Php", "Col", "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm", "Heb", "Jas", "1Pe", "2Pe", "1Jn", "2Jn", "3Jn", "Jud", "Rev"]);
const BOOK_ORDER = {};
["Gen", "Exo", "Lev", "Num", "Deu", "Jos", "Jdg", "Rth", "1Sa", "2Sa", "1Ki", "2Ki", "1Ch", "2Ch", "Ezr", "Neh", "Est", "Job", "Psa", "Pro", "Ecc", "Son", "Isa", "Jer", "Lam", "Eze", "Dan", "Hos", "Joe", "Amo", "Oba", "Jon", "Mic", "Nah", "Hab", "Zep", "Hag", "Zec", "Mal", "Mat", "Mar", "Luk", "Joh", "Act", "Rom", "1Co", "2Co", "Gal", "Eph", "Php", "Col", "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm", "Heb", "Jas", "1Pe", "2Pe", "1Jn", "2Jn", "3Jn", "Jud", "Rev"].forEach((b, i) => {
  BOOK_ORDER[b] = i;
});
const BOOK_LABELS = {
  Gen: "Genesis",
  Exo: "Exodus",
  Lev: "Leviticus",
  Num: "Numbers",
  Deu: "Deuteronomy",
  Jos: "Joshua",
  Jdg: "Judges",
  Rth: "Ruth",
  "1Sa": "1 Samuel",
  "2Sa": "2 Samuel",
  "1Ki": "1 Kings",
  "2Ki": "2 Kings",
  "1Ch": "1 Chronicles",
  "2Ch": "2 Chronicles",
  Ezr: "Ezra",
  Neh: "Nehemiah",
  Est: "Esther",
  Job: "Job",
  Psa: "Psalms",
  Pro: "Proverbs",
  Ecc: "Ecclesiastes",
  Son: "Song of Solomon",
  Isa: "Isaiah",
  Jer: "Jeremiah",
  Lam: "Lamentations",
  Eze: "Ezekiel",
  Dan: "Daniel",
  Hos: "Hosea",
  Joe: "Joel",
  Amo: "Amos",
  Oba: "Obadiah",
  Jon: "Jonah",
  Mic: "Micah",
  Nah: "Nahum",
  Hab: "Habakkuk",
  Zep: "Zephaniah",
  Hag: "Haggai",
  Zec: "Zechariah",
  Mal: "Malachi",
  Mat: "Matthew",
  Mar: "Mark",
  Luk: "Luke",
  Joh: "John",
  Act: "Acts",
  Rom: "Romans",
  "1Co": "1 Corinthians",
  "2Co": "2 Corinthians",
  Gal: "Galatians",
  Eph: "Ephesians",
  Php: "Philippians",
  Col: "Colossians",
  "1Th": "1 Thessalonians",
  "2Th": "2 Thessalonians",
  "1Ti": "1 Timothy",
  "2Ti": "2 Timothy",
  Tit: "Titus",
  Phm: "Philemon",
  Heb: "Hebrews",
  Jas: "James",
  "1Pe": "1 Peter",
  "2Pe": "2 Peter",
  "1Jn": "1 John",
  "2Jn": "2 John",
  "3Jn": "3 John",
  Jud: "Jude",
  Rev: "Revelation"
};

// AUTO-GENERATED by scripts/build_two_ending.py — do not hand-edit.
// Two-ending adjectives whose morph source never tags them Feminine, so their
// "Masculine" reads as "Masculine/Feminine" (see decodeMorph in 00-core.jsx).
// Regenerate on PythonAnywhere after a words rebuild; paste the output here.
const TWO_END_SOFT_OT = new Set(["G96", "G102", "G172", "G183", "G241", "G249", "G268", "G273", "G370", "G415", "G453", "G514", "G517", "G521", "G562", "G571", "G614", "G732", "G761", "G801", "G804", "G820", "G824", "G829", "G852", "G880", "G888", "G915", "G989", "G1198", "G1313", "G1384", "G1455", "G1541", "G1542", "G1630", "G1640", "G1655", "G1717", "G1741", "G1777", "G1784", "G1933", "G1954", "G1965", "G1990", "G2111", "G2121", "G2126", "G2149", "G2152", "G2158", "G2176", "G2272", "G2310", "G2318", "G2557", "G2645", "G3038", "G3118", "G3169", "G3353", "G3835", "G3927", "G3941", "G4036", "G4041", "G4108", "G4158", "G4289", "G4312", "G4644", "G4702", "G4854", "G5068", "G5199", "G5244", "G5246", "G5255", "G5499"]);
const TWO_END_SOFT_NT = new Set(["G4", "G35", "G57", "G62", "G94", "G102", "G106", "G112", "G113", "G121", "G146", "G160", "G169", "G172", "G175", "G176", "G178", "G180", "G182", "G185", "G193", "G194", "G215", "G216", "G241", "G246", "G261", "G267", "G269", "G275", "G277", "G298", "G338", "G361", "G370", "G376", "G379", "G410", "G413", "G415", "G420", "G422", "G428", "G434", "G459", "G462", "G506", "G517", "G532", "G545", "G551", "G552", "G564", "G590", "G614", "G656", "G679", "G729", "G732", "G765", "G777", "G781", "G786", "G794", "G800", "G802", "G813", "G815", "G820", "G824", "G829", "G830", "G842", "G843", "G855", "G865", "G866", "G878", "G880", "G884", "G888", "G890", "G893", "G915", "G1126", "G1332", "G1337", "G1351", "G1374", "G1384", "G1421", "G1450", "G1455", "G1468", "G1541", "G1542", "G1558", "G1560", "G1569", "G1630", "G1640", "G1655", "G1717", "G1721", "G1729", "G1777", "G1784", "G1786", "G1790", "G1853", "G1935", "G1944", "G1965", "G1967", "G1973", "G1978", "G1990", "G2000", "G2084", "G2104", "G2115", "G2126", "G2130", "G2152", "G2154", "G2155", "G2170", "G2173", "G2253", "G2263", "G2272", "G2287", "G2306", "G2312", "G2314", "G2318", "G2319", "G2357", "G2465", "G2473", "G2557", "G2593", "G2645", "G2709", "G2755", "G3038", "G3118", "G3151", "G3202", "G3424", "G3442", "G3504", "G3629", "G3637", "G3640", "G3642", "G3648", "G3651", "G3663", "G3673", "G3797", "G3835", "G3920", "G3927", "G3941", "G3943", "G4031", "G4040", "G4041", "G4108", "G4158", "G4184", "G4235", "G4312", "G4361", "G4406", "G4416", "G4644", "G4659", "G4662", "G4691", "G4773", "G4789", "G4805", "G4830", "G4832", "G4835", "G4854", "G4861", "G4904", "G4939", "G5005", "G5063", "G5244", "G5255", "G5267", "G5358", "G5361", "G5366", "G5367", "G5369", "G5377", "G5382", "G5387", "G5459", "G5554", "G5571", "G5573"]);

// ============================================================
// ICONS — minimal line set
// ============================================================
const Icon = {
  Search: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("circle", {
    cx: "11",
    cy: "11",
    r: "7"
  }), /*#__PURE__*/React.createElement("path", {
    d: "m20 20-3.5-3.5"
  })),
  Sparkle: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"
  })),
  Close: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M6 6l12 12M6 18 18 6"
  })),
  ArrowRight: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M5 12h14M13 6l6 6-6 6"
  })),
  Book: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5a2.5 2.5 0 0 0 0 5H20"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M8 6h8M8 10h6"
  })),
  Filter: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M3 6h18M6 12h12M10 18h4"
  })),
  Bookmark: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M6 3h12v18l-6-4-6 4z"
  })),
  // Note / highlight marker — a pencil (annotation)
  Note: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M4 20h4L18.5 9.5l-4-4L4 16z"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M13 7l4 4"
  })),
  // Reading-plan: a completed day
  Check: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M5 12l5 5L20 6"
  })),
  // Reading-plan: streak
  Flame: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M12 3c2.4 3 3.8 5 3.8 7.8A3.8 3.8 0 0 1 8.2 11C8.2 9.6 8.8 8.5 9.7 7.7 9.9 9.3 11 9.6 11 8c0-1.6.4-3.3 1-5z"
  })),
  Copy: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("rect", {
    x: "8",
    y: "8",
    width: "13",
    height: "13",
    rx: "2"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"
  })),
  Share: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "14",
    height: "14",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7M16 6l-4-4-4 4M12 2v13"
  })),
  Grid: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "15",
    height: "15",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "3",
    width: "7",
    height: "7",
    rx: "1"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "3",
    width: "7",
    height: "7",
    rx: "1"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "14",
    width: "7",
    height: "7",
    rx: "1"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "14",
    width: "7",
    height: "7",
    rx: "1"
  })),
  Lines: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "15",
    height: "15",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M3 6h18M3 11h18M3 16h12"
  })),
  Panel: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "3",
    width: "18",
    height: "18",
    rx: "2"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M15 3v18"
  })),
  // Strong's numbers → hash
  Hash: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M10 3 8 21M16 3l-2 18M4 8.5h16M3 15.5h16"
  })),
  // Interlinear → Greek stacked over English (two rows)
  Interlinear: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M4 6h16M4 9.5h11"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M4 15h16M4 18.5h11"
  })),
  // Parallel → two side-by-side columns
  Columns: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "4",
    width: "7.5",
    height: "16",
    rx: "1"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "13.5",
    y: "4",
    width: "7.5",
    height: "16",
    rx: "1"
  })),
  // Chronological order → clock
  Clock: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M12 7v5l3.5 2"
  })),
  // Overview / summary → info circle
  Info: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "20",
    height: "20",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.75",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, p), /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "9"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M12 11v5"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M12 8h.01"
  })),
  // Audio play (filled triangle, reads as a media control)
  Play: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "currentColor"
  }, p), /*#__PURE__*/React.createElement("path", {
    d: "M7 4.5v15l12-7.5z"
  })),
  // Audio pause (two filled bars)
  Pause: p => /*#__PURE__*/React.createElement("svg", _extends({
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "currentColor"
  }, p), /*#__PURE__*/React.createElement("rect", {
    x: "6.5",
    y: "5",
    width: "4",
    height: "14",
    rx: "1"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "13.5",
    y: "5",
    width: "4",
    height: "14",
    rx: "1"
  }))
};

// ============================================================
// NOTES STORE — browser-local, migration-ready
// ------------------------------------------------------------
// v1 keeps study notes in the browser only (no login, no bible.db write).
// The shape here is the EXACT shape a future server/account will use, so
// moving notes up later is a straight copy, not a rewrite:
//   - each note gets its OWN id the moment it's created (clean device-merge
//     / re-upload later)
//   - the anchor is a word-position range (corpus, which text, book, chapter,
//     start verse+word-spot, end verse+word-spot) so a future highlight layer
//     can paint the exact words
// Highlighting (color + painting the marks) is the NEXT phase; `color` is
// stored blank now so it's already there when that lands.
// ============================================================
// Highlight palette — ids map to CSS classes (.lib-hi-<id>) + swatch colors.
const NOTE_COLORS = ["yellow", "green", "blue", "pink", "orange"];
const NOTE_COLOR_CSS = {
  yellow: "#ffe89e",
  green: "#bdeec0",
  blue: "#bfe0ff",
  pink: "#ffcfe1",
  orange: "#ffd6a6"
};
const NotesStore = function () {
  const KEY = "lexica.notes.v1";
  const DEVKEY = "lexica.device.v1";
  const AUTHKEY = "lexica.auth.v1"; // { token, email } when signed in
  const JKEY = "lexica.journal.active.v1"; // id of the journal page you last opened
  const listeners = new Set();
  let cache = null;

  // --- sync state ---
  let syncTimer = null;
  let applyingRemote = false; // suppress re-scheduling while folding in the server's copy
  let syncing = false;
  let lastSync = 0; // ms epoch of last successful sync

  function load() {
    if (cache) return cache;
    try {
      cache = JSON.parse(localStorage.getItem(KEY)) || [];
    } catch (e) {
      cache = [];
    }
    if (!Array.isArray(cache)) cache = [];
    return cache;
  }
  const live = n => !n.deleted; // tombstones stay in the store (for sync) but hide everywhere else
  function persist() {
    try {
      localStorage.setItem(KEY, JSON.stringify(cache));
    } catch (e) {/* storage full / blocked */}
    listeners.forEach(fn => {
      try {
        fn();
      } catch (e) {}
    });
    scheduleSync();
  }
  function newId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "n_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 10);
  }
  // A stable per-browser id, made once — harmless now, helps a future account
  // merge tell this device's notes apart.
  function deviceId() {
    let d = null;
    try {
      d = localStorage.getItem(DEVKEY);
    } catch (e) {}
    if (!d) {
      d = newId();
      try {
        localStorage.setItem(DEVKEY, d);
      } catch (e) {}
    }
    return d;
  }

  // Fold a list of notes into the store by id: newer `updated` wins, tombstones
  // (deleted:true) included. Shared by Import (backup file) and Sync (server).
  function merge(incoming) {
    if (!Array.isArray(incoming)) return {
      added: 0,
      updated: 0,
      skipped: 0
    };
    const cur = load();
    const byId = new Map(cur.map(n => [n.id, n]));
    let added = 0,
      updated = 0,
      skipped = 0;
    for (const n of incoming) {
      // journal pages have no verse anchor (no .start) — let them through too
      if (!n || !n.id || n.kind !== "journal" && !n.start) {
        skipped++;
        continue;
      }
      const ex = byId.get(n.id);
      if (!ex) {
        cur.push(n);
        byId.set(n.id, n);
        added++;
      } else if ((n.updated || "") > (ex.updated || "")) {
        Object.assign(ex, n);
        updated++;
      } else skipped++;
    }
    persist();
    return {
      added,
      updated,
      skipped
    };
  }

  // --- account (email + password) ---
  function getAuth() {
    try {
      return JSON.parse(localStorage.getItem(AUTHKEY)) || null;
    } catch (e) {
      return null;
    }
  }
  function setAuth(a) {
    try {
      a ? localStorage.setItem(AUTHKEY, JSON.stringify(a)) : localStorage.removeItem(AUTHKEY);
    } catch (e) {}
    listeners.forEach(fn => {
      try {
        fn();
      } catch (e) {}
    });
  }
  function notify() {
    listeners.forEach(fn => {
      try {
        fn();
      } catch (e) {}
    });
  }
  function scheduleSync() {
    const a = getAuth();
    if (applyingRemote || !a || !a.token) return;
    clearTimeout(syncTimer);
    syncTimer = setTimeout(() => {
      syncNow();
    }, 2500);
  }
  async function syncNow() {
    const a = getAuth();
    if (!a || !a.token) return {
      ok: false,
      reason: "off"
    };
    syncing = true;
    notify();
    try {
      const res = await fetch("/api/notes/sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + a.token
        },
        body: JSON.stringify({
          notes: load()
        })
      });
      if (res.status === 401) {
        setAuth(null);
        return {
          ok: false,
          reason: "signed-out"
        };
      }
      if (!res.ok) return {
        ok: false,
        status: res.status
      };
      const data = await res.json();
      applyingRemote = true;
      merge(data.notes || []); // fold the account's copy back in (no re-schedule)
      applyingRemote = false;
      lastSync = Date.now();
      syncPlanNow(); // push/pull the reading-plan progress at the same moment
      return {
        ok: true
      };
    } catch (e) {
      return {
        ok: false,
        error: String(e)
      };
    } finally {
      syncing = false;
      notify();
    }
  }
  // --- reading-plan (chrono Days) progress sync ---
  // The plan blob lives in the SAME localStorage key the Library reads/writes
  // ("lexica.plan.v1"); we just push/pull it for signed-in users. The server unions
  // the completed-day sets, so two devices never clobber each other's checkmarks.
  const PLANKEY = "lexica.plan.v1";
  function planLoadLocal() {
    try {
      return JSON.parse(localStorage.getItem(PLANKEY) || "{}") || {};
    } catch (e) {
      return {};
    }
  }
  function planSaveLocal(o) {
    try {
      localStorage.setItem(PLANKEY, JSON.stringify(o));
    } catch (e) {}
  }
  let planTimer = null;
  async function syncPlanNow() {
    const a = getAuth();
    if (!a || !a.token) return {
      ok: false,
      reason: "off"
    };
    try {
      const res = await fetch("/api/plan/sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + a.token
        },
        body: JSON.stringify({
          plan: planLoadLocal()
        })
      });
      if (res.status === 401) {
        setAuth(null);
        return {
          ok: false,
          reason: "signed-out"
        };
      }
      if (!res.ok) return {
        ok: false,
        status: res.status
      };
      const data = await res.json();
      if (data && data.plan) {
        planSaveLocal(data.plan);
        notify();
      } // let the Library re-read
      return {
        ok: true
      };
    } catch (e) {
      return {
        ok: false,
        error: String(e)
      };
    }
  }
  function schedulePlanSync() {
    const a = getAuth();
    if (applyingRemote || !a || !a.token) return;
    clearTimeout(planTimer);
    planTimer = setTimeout(() => {
      syncPlanNow();
    }, 2500);
  }
  // Clear reading-plan progress: one text (e.g. "abp") or all ("*"). Clears locally AND
  // on the server (a hard delete there), so the union merge can't bring it back.
  async function clearPlan(text) {
    const all = !text || text === "*";
    const p = planLoadLocal();
    if (all) Object.keys(p).forEach(k => delete p[k]);else delete p[text];
    planSaveLocal(p);
    notify();
    const a = getAuth();
    if (a && a.token) {
      try {
        await fetch("/api/plan/clear", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + a.token
          },
          body: JSON.stringify(all ? {
            all: true
          } : {
            text
          })
        });
      } catch (e) {}
    }
  }

  // POST a JSON body to an auth endpoint; on success store {token,email} and
  // push/pull notes. Shared by signup/login AND password-reset (the reset endpoint
  // also returns {token,email}, signing the user in once the new password is set).
  async function authPostBody(path, payload) {
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return {
        ok: false,
        error: data.error || "Something went wrong."
      };
      setAuth({
        token: data.token,
        email: data.email
      });
      syncNow(); // push local notes up + pull the account's down
      return {
        ok: true,
        email: data.email
      };
    } catch (e) {
      return {
        ok: false,
        error: "Network error."
      };
    }
  }
  function authPost(path, email, password) {
    return authPostBody(path, {
      email,
      password
    });
  }
  return {
    // newest-edited first (tombstones hidden). Journal pages are a separate
    // free-form mode — they live in journals(), not the anchored-note list.
    all() {
      return load().filter(n => live(n) && n.kind !== "journal").sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
    },
    // Free-form journal pages (kind:"journal"), newest-edited first.
    journals() {
      return load().filter(n => live(n) && n.kind === "journal").sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
    },
    createJournal() {
      const now = new Date().toISOString();
      const page = {
        id: newId(),
        device: deviceId(),
        kind: "journal",
        title: "",
        body: "",
        created: now,
        updated: now
      };
      load().push(page);
      persist();
      return page;
    },
    // The journal page you last opened — what "send verse to journal" targets.
    // Validated: returns null if the page was since deleted.
    getActiveJournal() {
      let id = null;
      try {
        id = localStorage.getItem(JKEY);
      } catch (e) {}
      if (!id) return null;
      const n = load().find(x => x.id === id);
      return n && live(n) && n.kind === "journal" ? id : null;
    },
    setActiveJournal(id) {
      try {
        id ? localStorage.setItem(JKEY, id) : localStorage.removeItem(JKEY);
      } catch (e) {}
    },
    // Append text to a journal page (blank line between blocks). Returns the page.
    appendToJournal(id, text) {
      const n = this.get(id);
      if (!n || n.kind !== "journal") return null;
      const sep = n.body && n.body.trim() ? "\n\n" : "";
      return this.update(id, {
        body: (n.body || "") + sep + text
      });
    },
    get(id) {
      const n = load().find(x => x.id === id);
      return n && live(n) ? n : null;
    },
    // An existing (non-deleted) record on the exact same words, so we reuse it
    // instead of stacking duplicates.
    findAnchor(a) {
      const sp = a.start.pos ?? null,
        ep = (a.end && a.end.pos) ?? null;
      const ev = a.end && a.end.verse || a.start.verse;
      return load().find(n => live(n) && n.corpus === a.corpus && n.book === a.book && n.chapter === a.chapter && n.start.verse === a.start.verse && (n.end && n.end.verse || n.start.verse) === ev && (n.start.pos ?? null) === sp && ((n.end && n.end.pos) ?? null) === ep) || null;
    },
    forChapter(corpus, book, chapter) {
      return load().filter(n => live(n) && n.corpus === corpus && n.book === book && n.chapter === chapter);
    },
    create(anchor) {
      const now = new Date().toISOString();
      const note = {
        id: newId(),
        device: deviceId(),
        body: "",
        color: null,
        created: now,
        updated: now,
        ...anchor
      };
      load().push(note);
      persist();
      return note;
    },
    update(id, fields) {
      const n = this.get(id);
      if (!n) return null;
      Object.assign(n, fields, {
        updated: new Date().toISOString()
      });
      persist();
      return n;
    },
    // SOFT delete — keep a tombstone so the delete propagates through sync/import
    // instead of the note re-appearing from another device.
    remove(id) {
      const n = load().find(x => x.id === id);
      if (!n) return;
      Object.assign(n, {
        deleted: true,
        title: "",
        body: "",
        color: null,
        bookmark: false,
        updated: new Date().toISOString()
      });
      persist();
    },
    search(text) {
      const t = (text || "").toLowerCase().trim();
      const list = this.all();
      if (!t) return list;
      return list.filter(n => (n.body || "").toLowerCase().includes(t) || (n.snippet || "").toLowerCase().includes(t) || (n.refLabel || "").toLowerCase().includes(t));
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
    exportData() {
      return {
        app: "lexica-notes",
        version: 1,
        exported: new Date().toISOString(),
        notes: load()
      };
    },
    importMerge(incoming) {
      return merge(incoming);
    },
    // --- account API ---
    auth: getAuth,
    authInfo() {
      const a = getAuth();
      return {
        email: a && a.email,
        token: a && a.token,
        syncing,
        last: lastSync
      };
    },
    signup(email, password) {
      return authPost("/api/auth/signup", email, password);
    },
    login(email, password) {
      return authPost("/api/auth/login", email, password);
    },
    // Ask the server to email a reset link. Always resolves ok (the server never
    // reveals whether the address has an account); the UI just says "check email".
    async requestReset(email) {
      try {
        const res = await fetch("/api/auth/request-reset", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            email
          })
        });
        await res.json().catch(() => ({}));
        return {
          ok: res.ok
        };
      } catch (e) {
        return {
          ok: false,
          error: "Network error."
        };
      }
    },
    // Consume a reset link's token + new password; on success the server signs the
    // user in (returns {token,email}), so reuse the shared sign-in path.
    resetPassword(token, password) {
      return authPostBody("/api/auth/reset", {
        token,
        password
      });
    },
    // Set/change the password for the signed-in account (lets a Google-only account
    // add one). Needs a bearer token.
    async setPassword(password) {
      const a = getAuth();
      if (!a || !a.token) return {
        ok: false,
        error: "Not signed in."
      };
      try {
        const res = await fetch("/api/auth/set-password", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + a.token
          },
          body: JSON.stringify({
            password
          })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) return {
          ok: false,
          error: data.error || "Could not set password."
        };
        return {
          ok: true
        };
      } catch (e) {
        return {
          ok: false,
          error: "Network error."
        };
      }
    },
    // Sign in with the signed token Google handed the browser.
    async googleLogin(credential) {
      try {
        const res = await fetch("/api/auth/google", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            credential
          })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) return {
          ok: false,
          error: data.error || "Google sign-in failed."
        };
        setAuth({
          token: data.token,
          email: data.email
        });
        syncNow();
        return {
          ok: true,
          email: data.email
        };
      } catch (e) {
        return {
          ok: false,
          error: "Network error."
        };
      }
    },
    logout() {
      const a = getAuth();
      if (a && a.token) {
        fetch("/api/auth/logout", {
          method: "POST",
          headers: {
            "Authorization": "Bearer " + a.token
          }
        }).catch(() => {});
      }
      clearTimeout(syncTimer);
      setAuth(null);
    },
    syncNow,
    syncPlanNow,
    schedulePlanSync,
    clearPlan
  };
}();

// On load, if signed in, pull once so this device catches up.
if (NotesStore.auth()) {
  setTimeout(() => NotesStore.syncNow(), 400);
}

// Re-render a component whenever the note store changes.
function useNotesVersion() {
  const [, force] = useState(0);
  useEffect(() => NotesStore.subscribe(() => force(v => v + 1)), []);
}

// ============================================================
// useFitText — shrink a single-line element's font-size until it fits its slot.
// Used by the mobile reading-intro / overview card titles so a long title never
// wraps or runs off (and never collides with the corner toggle link) — it just
// steps the font down to fit. Pass {enabled:false} to leave the text untouched
// (e.g. on desktop, where the title sits inline and ellipsises instead).
// ============================================================
function useFitText(ref, text, opts) {
  const o = opts || {};
  const min = o.min || 13,
    max = o.max || 20,
    enabled = o.enabled !== false;
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return;
    const fit = () => {
      el.style.fontSize = max + "px";
      const avail = el.clientWidth;
      const full = el.scrollWidth;
      if (!avail || full <= avail) return; // already fits at full size
      // One proportional jump gets us close (text width ~ linear in font size),
      // then nudge down in half-pixels until it clears.
      let size = Math.max(min, Math.floor(max * avail / full * 2) / 2);
      el.style.fontSize = size + "px";
      while (size > min && el.scrollWidth > avail + 0.5) {
        size -= 0.5;
        el.style.fontSize = size + "px";
      }
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, [text, enabled, min, max]);
}

// ============================================================
// HEADER
// ============================================================
function Header({
  activeView,
  onNavChange,
  owner
}) {
  return /*#__PURE__*/React.createElement("header", {
    className: "hdr"
  }, /*#__PURE__*/React.createElement("div", {
    className: "hdr-inner"
  }, /*#__PURE__*/React.createElement("div", {
    className: "brand"
  }, /*#__PURE__*/React.createElement("div", {
    className: "brand-mark",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("svg", {
    width: "22",
    height: "22",
    viewBox: "0 0 24 24",
    fill: "none"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3",
    stroke: "currentColor",
    strokeWidth: "1.6",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M11 7v6M14 10h-6",
    stroke: "currentColor",
    strokeWidth: "1.6",
    strokeLinecap: "round"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "brand-text"
  }, /*#__PURE__*/React.createElement("div", {
    className: "brand-name"
  }, "Lexica"), /*#__PURE__*/React.createElement("div", {
    className: "brand-sub"
  }, "Greek & Hebrew Word Study"))), /*#__PURE__*/React.createElement("nav", {
    className: "hdr-nav"
  }, /*#__PURE__*/React.createElement("button", {
    className: "hdr-link " + (activeView === "library" ? "active" : ""),
    onClick: () => onNavChange("library")
  }, "Library"), /*#__PURE__*/React.createElement("button", {
    className: "hdr-link " + (activeView === "lexicon" ? "active" : ""),
    onClick: () => onNavChange("lexicon")
  }, "Lexicon"), /*#__PURE__*/React.createElement("button", {
    className: "hdr-link " + (activeView === "search" ? "active" : ""),
    onClick: () => onNavChange("search")
  }, "Search"), /*#__PURE__*/React.createElement("button", {
    className: "hdr-link " + (activeView === "notes" ? "active" : ""),
    onClick: () => onNavChange("notes")
  }, "Notes"), /*#__PURE__*/React.createElement("button", {
    className: "hdr-link " + (activeView === "study" ? "active" : ""),
    onClick: () => onNavChange("study")
  }, "Study"), /*#__PURE__*/React.createElement("button", {
    className: "hdr-link " + (activeView === "about" ? "active" : ""),
    onClick: () => onNavChange("about")
  }, "About"))));
}

// ============================================================
// SEARCH BAR
// ============================================================
function SearchBar({
  q2,
  setQ2,
  onAiSearch,
  aiLoading
}) {
  return /*#__PURE__*/React.createElement("section", {
    className: "search"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-cell"
  }, /*#__PURE__*/React.createElement("label", {
    className: "search-label"
  }, /*#__PURE__*/React.createElement("span", {
    className: "search-eyebrow ai"
  }, /*#__PURE__*/React.createElement("span", {
    className: "ai-dot"
  }), "Ask the corpus")), /*#__PURE__*/React.createElement("form", {
    className: "search-field ai-field",
    onSubmit: e => {
      e.preventDefault();
      onAiSearch();
    }
  }, /*#__PURE__*/React.createElement(Icon.Sparkle, {
    className: "search-icon"
  }), /*#__PURE__*/React.createElement("input", {
    type: "text",
    className: "search-input",
    placeholder: "Ask the corpus\u2026 Where does the divine council appear?",
    value: q2,
    onChange: e => setQ2(e.target.value)
  }), /*#__PURE__*/React.createElement("button", {
    type: "submit",
    className: "search-go",
    "aria-label": "Submit"
  }, aiLoading ? /*#__PURE__*/React.createElement("span", {
    className: "spinner"
  }) : /*#__PURE__*/React.createElement(Icon.ArrowRight, null)))));
}

// ============================================================
// LSJ SUMMARY DISPLAY
// ============================================================
function LsjSummary({
  data,
  loading
}) {
  if (loading) return /*#__PURE__*/React.createElement("div", {
    className: "lsj-def",
    style: {
      color: "var(--muted)",
      fontStyle: "italic"
    }
  }, "Summarizing\u2026");
  if (!data?.summary) return /*#__PURE__*/React.createElement("div", {
    className: "lsj-def",
    style: {
      color: "var(--muted)"
    }
  }, "No definition available.");
  return /*#__PURE__*/React.createElement("p", {
    className: "lsj-synthesis"
  }, renderInlineMd(data.summary));
}

// Google-Maps-style bottom-sheet dismissal: drag the WHOLE card down to close.
// Grabbing the card's top chrome (the handle/header — anything outside the
// scrolling body) ALWAYS arms the drag, no matter where the body is scrolled.
// Starting inside the body only arms when it's already scrolled to the top
// (otherwise the body scrolls normally). Uses native non-passive listeners so we
// can block page scroll / pull-to-refresh while dragging (React's touch props
// are passive and can't).
function useSwipeToDismiss(onClose) {
  const sheetRef = React.useRef(null);
  const scrollRef = React.useRef(null);
  const closeRef = React.useRef(onClose);
  closeRef.current = onClose;
  React.useEffect(() => {
    const el = sheetRef.current;
    if (!el) return;
    let startY = 0,
      dragY = 0,
      active = false,
      fromChrome = false;
    const SNAP = 'transform 0.25s cubic-bezier(0.2,0.8,0.2,1)';
    const atTop = () => {
      const sc = scrollRef.current;
      return !sc || sc.scrollTop <= 0;
    };
    const onStart = e => {
      const sc = scrollRef.current;
      fromChrome = !(sc && sc.contains(e.target)); // touch began on the handle/header, not the scroll body
      active = fromChrome || atTop(); // chrome always arms; body only when scrolled to top
      startY = e.touches[0].clientY;
      dragY = 0;
    };
    const onMove = e => {
      if (!active) return;
      const d = e.touches[0].clientY - startY;
      if (d <= 0 || !fromChrome && !atTop()) {
        // pulling up, or body-drag that got scrolled → hand back
        if (dragY) {
          el.style.transition = '';
          el.style.transform = '';
          dragY = 0;
        }
        active = false;
        return;
      }
      dragY = d;
      el.style.transition = 'none';
      el.style.transform = `translateY(${d}px)`;
      if (e.cancelable) e.preventDefault(); // stop the page scrolling / pull-to-refresh
    };
    const onEnd = () => {
      if (!active) return;
      active = false;
      if (dragY > 90) {
        // committed: slide the card fully down, THEN dismiss
        el.style.transition = SNAP;
        el.style.transform = 'translateY(100%)';
        let done = false;
        const finish = () => {
          if (done) return;
          done = true;
          el.removeEventListener('transitionend', finish);
          closeRef.current?.();
        };
        el.addEventListener('transitionend', finish);
        setTimeout(finish, 320); // fallback if transitionend doesn't fire
        dragY = 0;
        return;
      }
      if (dragY) {
        el.style.transition = SNAP;
        el.style.transform = '';
      } // not far enough: snap back up
      dragY = 0;
    };
    el.addEventListener('touchstart', onStart, {
      passive: true
    });
    el.addEventListener('touchmove', onMove, {
      passive: false
    });
    el.addEventListener('touchend', onEnd, {
      passive: true
    });
    el.addEventListener('touchcancel', onEnd, {
      passive: true
    });
    return () => {
      el.removeEventListener('touchstart', onStart);
      el.removeEventListener('touchmove', onMove);
      el.removeEventListener('touchend', onEnd);
      el.removeEventListener('touchcancel', onEnd);
    };
  }, []);
  return {
    sheetRef,
    scrollRef
  };
}

// ============================================================
// LEAFLET MINI-MAP
// ============================================================
// Leaflet (CSS+JS) is loaded ON DEMAND — the map only ever appears inside the
// metaV place card, so keeping it out of index.html keeps it off the critical
// path for every page load. Loaded once, cached on window.L for later opens.
let _leafletPromise = null;
function loadLeaflet() {
  if (window.L) return Promise.resolve(window.L);
  if (_leafletPromise) return _leafletPromise;
  _leafletPromise = new Promise((resolve, reject) => {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    css.crossOrigin = "";
    document.head.appendChild(css);
    const js = document.createElement("script");
    js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    js.crossOrigin = "";
    js.onload = () => resolve(window.L);
    js.onerror = reject;
    document.head.appendChild(js);
  });
  return _leafletPromise;
}
function LeafletMap({
  lat,
  lon,
  name
}) {
  const mapRef = React.useRef(null);
  const instanceRef = React.useRef(null);
  const [ready, setReady] = React.useState(!!window.L);

  // Kick off the lazy load on first mount (no-op if Leaflet is already present).
  React.useEffect(() => {
    if (window.L) return;
    let cancelled = false;
    loadLeaflet().then(() => {
      if (!cancelled) setReady(true);
    }).catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);
  React.useEffect(() => {
    if (!ready || !mapRef.current || !window.L) return;
    if (instanceRef.current) {
      instanceRef.current.remove();
      instanceRef.current = null;
    }
    const map = window.L.map(mapRef.current, {
      center: [lat, lon],
      zoom: 7,
      zoomControl: true,
      scrollWheelZoom: false,
      attributionControl: false
    });
    window.L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);
    window.L.marker([lat, lon]).addTo(map).bindPopup(name).openPopup();
    instanceRef.current = map;
    return () => {
      if (instanceRef.current) {
        instanceRef.current.remove();
        instanceRef.current = null;
      }
    };
  }, [ready, lat, lon, name]);
  return /*#__PURE__*/React.createElement("div", {
    ref: mapRef,
    className: "metav-leaflet-map"
  });
}

// ============================================================
// SUMMARY PANEL — Library right-pane DEFAULT (desktop) / bottom sheet (mobile)
// ------------------------------------------------------------
// A short Berean book blurb + a pericope-aware chapter summary for whatever the
// reader is on. On DESKTOP it's the resting content of the right sidebar (reuses
// the .detail-side shell); a word/verse click replaces it and closing returns
// here. On MOBILE it opens on demand as a bottom sheet from the reading cockpit's
// ⓘ button (isMobile + onClose), riding the same .detail-sheet rails as the
// word-study sheet.
// ============================================================
function SummaryPanel({
  book,
  chapter,
  bookLabel,
  isMobile,
  onClose,
  onBack
}) {
  // Remembers fetched summaries across remounts (the panel unmounts whenever a
  // word/verse takes over the slot) so re-opening the same chapter is instant
  // instead of flashing the loading line again.
  const key = book + "/" + chapter;
  const [data, setData] = useState(() => SummaryPanel._cache[key] || null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!book || !chapter) return;
    const cached = SummaryPanel._cache[key];
    if (cached) {
      setData(cached);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setData(null);
    api.summary(book, chapter).then(d => {
      if (!cancelled) {
        SummaryPanel._cache[key] = d || {};
        setData(d || {});
        setLoading(false);
      }
    }).catch(() => {
      if (!cancelled) {
        setData({});
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [book, chapter]);

  // Swipe-to-dismiss for the mobile sheet (same hook the word-study / xref sheets
  // use). Harmlessly no-ops on desktop, where sheetRef is never attached.
  const {
    sheetRef,
    scrollRef
  } = useSwipeToDismiss(onClose);
  const titleRef = useRef(null);
  const bookText = data && data.book_summary;
  const chapText = data && data.chapter_summary;
  const nothing = !loading && !bookText && !chapText;
  const title = (bookLabel || book) + (chapter ? " " + chapter : "");
  // Mobile: shrink the title to fit one line beside the corner "Intro" link.
  useFitText(titleRef, title, {
    enabled: isMobile
  });
  const content = /*#__PURE__*/React.createElement(React.Fragment, null, loading && /*#__PURE__*/React.createElement("div", {
    className: "summary-loading"
  }, "Reading the chapter\u2026"), !loading && bookText && /*#__PURE__*/React.createElement("div", {
    className: "detail-section"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-h"
  }, "About"), /*#__PURE__*/React.createElement("p", {
    className: "detail-p"
  }, renderInlineMd(bookText))), !loading && chapText && /*#__PURE__*/React.createElement("div", {
    className: "detail-section last"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-h"
  }, "This chapter"), /*#__PURE__*/React.createElement("p", {
    className: "detail-p"
  }, renderInlineMd(chapText))), nothing && /*#__PURE__*/React.createElement("div", {
    className: "summary-loading"
  }, "No overview available for this passage."));

  // Mobile: bottom sheet opened from the reading cockpit. Swipe down (drag
  // anywhere) or tap the scrim to close — matches the other sheets.
  if (isMobile) {
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      className: "sheet-scrim",
      onClick: onClose
    }), /*#__PURE__*/React.createElement("aside", {
      ref: sheetRef,
      className: "detail detail-sheet summary-sheet",
      role: "dialog",
      "aria-label": "Reading overview"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sheet-drag-zone",
      "aria-hidden": "true"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sheet-handle"
    })), /*#__PURE__*/React.createElement("div", {
      className: "detail-head"
    }, /*#__PURE__*/React.createElement("div", {
      className: "detail-head-l"
    }, /*#__PURE__*/React.createElement("span", {
      ref: titleRef,
      className: "detail-pos summary-pos"
    }, title)), onBack && /*#__PURE__*/React.createElement("button", {
      className: "detail-back",
      onClick: onBack,
      "aria-label": "Back to reading intro",
      title: "Intro"
    }, "\u2039")), /*#__PURE__*/React.createElement("div", {
      className: "detail-body",
      ref: scrollRef
    }, content)));
  }

  // Desktop: resting content of the right sidebar. The "‹ Intro" toggle sits in the
  // .detail-back slot (right), matching the word-study / xref / day-intro headers.
  return /*#__PURE__*/React.createElement("aside", {
    className: "detail detail-side summary-side",
    role: "complementary",
    "aria-label": "Reading overview"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-head-l"
  }, /*#__PURE__*/React.createElement("span", {
    className: "detail-pos summary-pos"
  }, title)), onBack && /*#__PURE__*/React.createElement("button", {
    className: "detail-back",
    onClick: onBack,
    "aria-label": "Back to reading intro"
  }, "\u2039 Intro")), /*#__PURE__*/React.createElement("div", {
    className: "detail-body"
  }, content));
}
SummaryPanel._cache = {};

// ============================================================
// DETAIL PANEL — SIDEBAR / BOTTOM SHEET
// ============================================================
function DetailPanel({
  entry,
  isMobile,
  onClose,
  occurrences,
  totalResults,
  onStrongsSearch,
  onReadInContext,
  onNameSearch,
  onNavigateToLexicon,
  onOpenStudyName,
  overviewBack,
  backLabel = "Overview"
}) {
  const [verseText, setVerseText] = useState("");
  const [verseLoading, setVerseLoading] = useState(false);
  const [abpCount, setAbpCount] = useState(null);
  const [extraCount, setExtraCount] = useState(null);
  const [showInterlinear, setShowInterlinear] = useState(false);
  const [interlinearWords, setInterlinearWords] = useState(null);
  const heroRef = useRef(null);
  useEffect(() => {
    setShowInterlinear(false);
    setInterlinearWords(null);
  }, [entry && entry.id]);

  // Auto-shrink the big headword so a long word (e.g. a proper name like
  // "Nebuchadnezzar") scales down to fit the panel on one line instead of
  // overflowing. Measure the natural width at the CSS base size against the
  // panel's content width, then drop the size proportionally if it's too wide.
  // Re-runs per word and when the layout swaps (mobile sheet <-> desktop side)
  // or the window resizes.
  useLayoutEffect(() => {
    const el = heroRef.current;
    if (!el) return;
    let cancelled = false;
    const fit = () => {
      if (cancelled || !el.isConnected) return;
      el.style.fontSize = ""; // reset to the CSS base, then measure
      const box = el.closest(".detail-body");
      if (!box) return;
      const cs = getComputedStyle(box);
      const avail = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      const natural = el.scrollWidth;
      if (avail > 0 && natural > avail) {
        const base = parseFloat(getComputedStyle(el).fontSize);
        el.style.fontSize = Math.max(22, Math.floor(base * avail / natural)) + "px";
      }
    };
    fit();
    // The reader fonts load with display=optional, so a first-open measure can
    // land on the fallback font — re-measure once the real font settles.
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
    window.addEventListener("resize", fit);
    return () => {
      cancelled = true;
      window.removeEventListener("resize", fit);
    };
  }, [entry && entry.id, isMobile]);

  // The side-card interlinear follows the TEXT you're reading, same as the reading
  // pane: KJV -> KJV words, Hebrew (HEB reader) -> Hebrew words, otherwise ABP Greek.
  // Each feed is normalised to one shape {top, translit, english, strongs, he} so the
  // render below stays a single dumb loop. (Before, it always pulled ABP Greek — so a
  // KJV verse showed the LXX Greek underneath it.)
  useEffect(() => {
    if (!showInterlinear || !entry || interlinearWords) return;
    let cancelled = false;
    const done = rows => {
      if (!cancelled) setInterlinearWords(rows);
    };
    const tag = s => s && s !== "*" ? strongsTag(s) : "";
    if (entry.isKjv) {
      api.kjvVerseWords(entry.book, entry.chapter, entry.verse).then(rows => done((rows || []).map(w => {
        const sid = w.strongs_ids && w.strongs_ids[0] || "";
        return {
          top: w.lemma || "",
          translit: w.xlit || "",
          english: w.word || "",
          strongs: tag(sid),
          he: /^H/i.test(sid)
        };
      }))).catch(() => done([]));
    } else if (entry.isBsb) {
      api.bsbVerseWords(entry.book, entry.chapter, entry.verse).then(rows => done((rows || []).map(w => {
        const sid = w.strongs_ids && w.strongs_ids[0] || "";
        return {
          top: w.lemma || "",
          translit: w.xlit || "",
          english: w.word || "",
          strongs: tag(sid),
          he: /^H/i.test(sid)
        };
      }))).catch(() => done([]));
    } else if (entry.isHeb) {
      api.hebVerseWords(entry.book, entry.chapter, entry.verse).then(d => done((d.words || []).map(w => ({
        top: w.hebrew || "",
        translit: w.translit || "",
        english: w.gloss || "",
        strongs: tag(w.strongs),
        he: true
      })))).catch(() => done([]));
    } else {
      api.verseWords(entry.book, entry.chapter, entry.verse).then(d => done((d.words || []).map(w => ({
        top: w.lemma || "",
        translit: w.translit || "",
        english: w.english || "",
        strongs: w.strongs_base === "*" ? "" : tag(w.strongs && w.strongs !== "*" ? w.strongs : w.strongs_base),
        he: false,
        bracket_id: w.bracket_id,
        // ABP translator-supplied words -> [ ] in the render (KJV/Hebrew leave this undefined)
        pos: w.greek_pos // Greek word-order number, shown inside brackets like the reading pane
      })))).catch(() => done([]));
    }
    return () => {
      cancelled = true;
    };
  }, [showInterlinear, entry && entry.id]);
  useEffect(() => {
    if (!entry || entry.isExtra) return; // non-canonical words have no Bible verse to load
    let cancelled = false;
    setVerseText("");
    setVerseLoading(true);
    api.verse(entry.book, entry.chapter, entry.verse).then(data => {
      if (!cancelled) setVerseText(data.text || "");
    }).catch(() => {
      if (!cancelled) setVerseText("");
    }).finally(() => {
      if (!cancelled) setVerseLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.id]);
  useEffect(() => {
    if (!entry || entry.strongs_base === "*") {
      setAbpCount(null);
      return;
    }
    let cancelled = false;
    api.strongsCount(entry.strongs_raw).then(d => {
      if (!cancelled) setAbpCount(d.count ?? null);
    }).catch(() => {
      if (!cancelled) setAbpCount(null);
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.strongs_raw]);

  // Count within the non-canonical text itself (e.g. the Didache).
  useEffect(() => {
    if (!entry || !entry.isExtra || !entry.extraBook || !entry.strongs_base || entry.strongs_base === "*") {
      setExtraCount(null);
      return;
    }
    let cancelled = false;
    api.extraStrongsCount(entry.extraBook, entry.strongs_base).then(d => {
      if (!cancelled) setExtraCount(d.count ?? null);
    }).catch(() => {
      if (!cancelled) setExtraCount(null);
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.id]);
  const isPN = entry && (entry.is_pn || entry.isPN || entry.strongs === "PN" || entry.strongs_base === "*");
  // A word carrying an H-number. For Hebrew PROPER NOUNS we want metaV (person/
  // place) on top with the BDB lexical entry stacked BELOW (like KJV mode):
  //  - isHebrewWord drives the BDB fetch + section (shown for ALL Hebrew words, incl. PNs)
  //  - isHebrew (excludes PNs) drives the Hebrew HERO styling + LSJ suppression, so a
  //    PN's hero shows its NAME and metaV stays the primary card.
  const isHebrewWord = entry && entry.strongs && entry.strongs.startsWith("H");
  const isHebrew = isHebrewWord && !isPN;
  // Gentilics (-ite/-ites: Hivite, Sinite, Amorite…) are eponymous people-groups
  // from the Table of Nations — labelled "People / Clan", but still shown as a
  // metaV person so the genealogy (parent/sibling clans) is preserved.
  const isGentilic = !!(isPN && entry && /ites?$/i.test(extractProperName(entry.pnName || entry.gloss || "")));

  // PN occurrence count (by name, for strongs='*' entries)
  const [pnCount, setPnCount] = useState(null);
  useEffect(() => {
    setPnCount(null);
    if (!entry.gloss) return;
    const name = extractProperName(entry.gloss);
    if (!name || name.length < 2) return;
    let cancelled = false;
    api.pnCount(name).then(d => {
      if (!cancelled) setPnCount(d.count ?? null);
    }).catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [entry && entry.id]);

  // KJV occurrence count for Hebrew words
  const [kjvCount, setKjvCount] = useState(null);
  useEffect(() => {
    setKjvCount(null);
    if (!isHebrew && !entry.isKjv || !entry.strongs || entry.isHeb || entry.isBsb) return; // Hebrew OT reader / BSB: no KJV cross-link
    let cancelled = false;
    api.kjvStrongsCount(entry.strongs).then(d => {
      if (!cancelled) setKjvCount(d.count ?? null);
    }).catch(() => {
      if (!cancelled) setKjvCount(null);
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.strongs]);

  // BSB occurrence count (BSB word study) — its own count; the Lexicon tab has no
  // BSB corpus, so this shows as a plain "N× in BSB" tally, not a click-through.
  const [bsbCount, setBsbCount] = useState(null);
  useEffect(() => {
    setBsbCount(null);
    if (!entry || !entry.isBsb || !entry.strongs) return;
    let cancelled = false;
    api.bsbStrongsCount(entry.strongs).then(d => {
      if (!cancelled) setBsbCount(d.count ?? null);
    }).catch(() => {
      if (!cancelled) setBsbCount(null);
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.strongs]);

  // metaV person/place lookup — runs on any word click where gloss may be a name
  const [metavPersonData, setMetavPersonData] = useState(null);
  const [metavPlaceData, setMetavPlaceData] = useState(null);
  const [metavTab, setMetavTab] = useState("person"); // "person" | "place"
  const [metavLoading, setMetavLoading] = useState(false);

  // Nave's topical study for this person/place (subtopic headers + counts), shown
  // under the metaV card. PUBLIC for published name-topics; drafts stay admin-only
  // (the endpoint returns no sections otherwise → stays null).
  const [naveData, setNaveData] = useState(null);
  useEffect(() => {
    setNaveData(null);
    if (!metavPersonData && !metavPlaceData) return;
    const nm = extractProperName(entry.pnName || entry.gloss || "");
    if (!nm || nm.length < 2) return;
    let cancelled = false;
    api.studyForName(nm).then(d => {
      if (!cancelled && d && d.sections && d.sections.length) setNaveData(d);
    });
    return () => {
      cancelled = true;
    };
  }, [metavPersonData, metavPlaceData, entry]);
  // Derived — all downstream code uses these unchanged.
  // If the word's OWN proper-noun type (tipnr pn_types) is a clean SINGLE type and
  // we have that card, the word IS that entity — the other metaV card is a
  // name-coincidence (loose name-based lookup), so PIN to the single entity and
  // suppress the Person/Place toggle. When pn_types is ambiguous ('person,place':
  // a strongs shared by a genuine person AND place — Adam, Dan) or absent (a
  // non-Library entry, or no tipnr row), keep the toggle so the user can see both.
  const pnList = (entry && entry.pn_types || "").toLowerCase().split(",").map(s => s.trim()).filter(Boolean);
  const pnSingle = pnList.length === 1 && (pnList[0] === "person" || pnList[0] === "place") ? pnList[0] : null;
  const metavPinned = pnSingle === "person" && metavPersonData ? "person" : pnSingle === "place" && metavPlaceData ? "place" : null;
  const metavHasBoth = !!(metavPersonData && metavPlaceData) && !metavPinned;
  const metavType = metavPinned ? metavPinned : metavHasBoth ? metavTab : metavPersonData ? "person" : metavPlaceData ? "place" : null;
  const metavData = metavType === "person" ? metavPersonData : metavType === "place" ? metavPlaceData : null;
  useEffect(() => {
    setMetavPersonData(null);
    setMetavPlaceData(null);
    setMetavTab("person");
    // Skip metaV for words with a real Greek lemma — those belong to LSJ
    // Exception: KJV/BSB words that look like proper nouns (capitalized) still go through metaV
    const kjvIsPN = (entry.isKjv || entry.isBsb) && extractProperName(entry.pnName || entry.gloss || "") !== "";
    if (!isPN && !kjvIsPN && entry.greek && entry.translit && entry.strongs_raw !== "2316") return;
    const name = extractProperName(entry.pnName || entry.gloss || "");
    if (!name || name.length < 2) return;
    const _DIVINE_SKIP = new Set(["LORD", "Lord", "YHWH", "Yahweh", "Jehovah", "Holy"]);
    if (_DIVINE_SKIP.has(name)) return;
    let cancelled = false;
    setMetavLoading(true);
    Promise.all([api.metavPerson(name).catch(() => ({
      error: true
    })), api.metavPlace(name).catch(() => ({
      error: true
    }))]).then(([pd, ld]) => {
      if (cancelled) return;
      const personOk = !pd.error && (pd.birth_year || pd.death_year || pd.relationships?.length >= 2);
      if (personOk) setMetavPersonData(pd);
      if (!ld.error) setMetavPlaceData(ld);
      // Default tab (only matters when BOTH person+place exist). Prefer the
      // word's OWN proper-noun type from tipnr — pn_types is a SET ('person',
      // 'place', or 'person,place'; backlog #5 fix). A clean SINGLE type is
      // authoritative. When tipnr is ambiguous (a strongs shared by a person AND
      // a place → 'person,place', which strongs alone can't disambiguate) or
      // absent (pn_types null: pre-reimport, or a non-Library entry), fall back to
      // the strongs_g heuristic — flip to Place only when the place's own (G-)
      // strongs matches the clicked word's strongs_base. (Legacy pn_type is NOT
      // used: tipnr.strongs was a PK so it stored whichever type imported last.)
      const pnTypes = (entry.pn_types || "").toLowerCase().split(",").map(s => s.trim()).filter(Boolean);
      let tab;
      if (pnTypes.length === 1 && pnTypes[0] === "person") tab = "person";else if (pnTypes.length === 1 && pnTypes[0] === "place") tab = "place";else {
        const placeStrongsMatch = !ld.error && !!ld.strongs_g && !!entry.strongs_base && ld.strongs_g.split(/[^GH0-9.]+/i).map(s => s.toUpperCase()).includes(entry.strongs_base.toUpperCase());
        tab = placeStrongsMatch ? "place" : "person";
      }
      setMetavTab(tab);
      setMetavLoading(false);
    }).catch(() => {
      if (!cancelled) setMetavLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.id]);

  // AI description fallback for PN entries with no metaV data
  const [aiDescription, setAiDescription] = useState(null);
  const [aiDescLoading, setAiDescLoading] = useState(false);
  useEffect(() => {
    setAiDescription(null);
    setAiDescLoading(false);
    if (metavLoading) return;
    if (metavData && metavType === "person" && !isGentilic) return; // rich person bio replaces AI; groups still get the summary
    if (metavData && metavType === "place" && metavData.strongs_g?.length > 0) return; // place has LSJ via strongs_g
    if (isHebrew) return; // BDB covers Hebrew words
    if (!isPN) return; // only for proper nouns
    const name = extractProperName(entry.pnName || entry.gloss || "");
    if (!name || name.length < 2) return;
    let cancelled = false;
    setAiDescLoading(true);
    api.metavAiDescription(name).then(d => {
      if (!cancelled && !d.error) setAiDescription(d.description || null);
    }).catch(() => {}).finally(() => {
      if (!cancelled) setAiDescLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.id, metavData, metavLoading]);

  // Hebrew BDB lookup
  const [bdbEntry, setBdbEntry] = useState(null);
  const [bdbLoading, setBdbLoading] = useState(false);
  useEffect(() => {
    setBdbEntry(null);
    if (!isHebrewWord || !entry.strongs) return;
    let cancelled = false;
    setBdbLoading(true);
    api.bdb(entry.strongs).then(d => {
      if (!cancelled) {
        setBdbEntry(d.error ? null : d);
        setBdbLoading(false);
      }
    }).catch(() => {
      if (!cancelled) {
        setBdbEntry(null);
        setBdbLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.id]);

  // English verse text for the quote — BSB for BSB words, else KJV (KJV mode, a
  // Hebrew word, or a place card). Held in kjvVerseText; the source is picked here.
  const [kjvVerseText, setKjvVerseText] = useState("");
  useEffect(() => {
    setKjvVerseText("");
    if (!entry || !entry.isKjv && !entry.isBsb && !isHebrew && !(metavType === "place" && !isPN)) return;
    let cancelled = false;
    const fetchVerse = entry.isBsb ? api.bsbVerse : api.kjvVerse;
    fetchVerse(entry.book, entry.chapter, entry.verse).then(d => {
      if (!cancelled) setKjvVerseText(d.text || "");
    }).catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [entry && entry.id]);
  const [lsjEntry, setLsjEntry] = useState(null);
  const [lsjLoading, setLsjLoading] = useState(false);
  const [lsjSummary, setLsjSummary] = useState(null);
  const [lsjSummaryLoading, setLsjSummaryLoading] = useState(false);
  useEffect(() => {
    setLsjEntry(null);
    setLsjSummary(null);
    // For PN place entries with a mapped strongs_g, use that for LSJ lookup
    const placeStrongs = isPN && metavType === "place" && metavData?.strongs_g?.length > 0 ? metavData.strongs_g.replace(/^G/i, "") : null;
    const canLookup = !isHebrew && entry && (entry.greek || entry.strongs_raw || placeStrongs);
    if (!canLookup) {
      setLsjLoading(false);
      return;
    }
    let cancelled = false;
    setLsjLoading(true);
    api.lsj(entry.greek || "", placeStrongs || entry.strongs_raw).then(d => {
      if (!cancelled) {
        setLsjEntry(d.error ? null : d);
        setLsjLoading(false);
      }
    }).catch(() => {
      if (!cancelled) {
        setLsjEntry(null);
        setLsjLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [entry && entry.id, metavType, metavData?.strongs_g]);
  useEffect(() => {
    if (!lsjEntry || lsjEntry.source === "strongs") {
      setLsjSummary(null);
      setLsjSummaryLoading(false);
      return;
    }
    let cancelled = false;
    setLsjSummaryLoading(true);
    const summaryStrongs = lsjEntry.source === "abp_ext" ? lsjEntry.key : "";
    // Always request the verse-agnostic ("general") summary. A word's LSJ summary
    // is cached/shown universally, so it must not name the verse it was first clicked in.
    api.lsjSummary(lsjEntry.key, summaryStrongs).then(d => {
      if (!cancelled) setLsjSummary(d);
    }).catch(() => {
      if (!cancelled) setLsjSummary(null);
    }).finally(() => {
      if (!cancelled) setLsjSummaryLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [lsjEntry && lsjEntry.key, entry && entry.id]);
  if (!entry) return null;
  const barWidth = Math.min(100, occurrences / Math.max(1, totalResults) * 100);
  const morphLine = entry.greek && !isHebrew ? decodeMorph(entry.morph, entry.greek, entry.strongs_base) : isHebrew ? entry.grammar || "" : ""; // Hebrew: the decoded TAHOT grammar, same card slot as Greek
  const {
    sheetRef,
    scrollRef
  } = useSwipeToDismiss(onClose);

  // --------------------------------------------------------------------------
  // Panel descriptor — resolve the isPN / isHebrew / metavType tangle into ONE
  // place: a `hero` block and an ordered `sections` list. The return below is
  // dumb: it renders `hero`, then `sections.map(renderSection)` — no decisions.
  // --------------------------------------------------------------------------
  const properName = extractProperName(entry.gloss);
  const nameOrGloss = isPN || metavData ? properName : entry.gloss;
  const trimTail = s => stripArticles(s?.replace(/[.,;:!?—-]+$/, "").trim());
  // The clicked word's INFLECTED form — the surface form as it appears in THIS verse —
  // when the reading text carries one: the Hebrew OT reader (entry.inflected = the
  // pointed word) and BSB (entry.inflected = the Berean-tables original word) set it at
  // the click. The dictionary form (lemma) stays the BIG headword for EVERY text, so the
  // card's headline word means the same thing everywhere (ABP/KJV have no surface form);
  // the inflected form shows on a small "in this verse" line just beneath it.
  const heroInflected = (entry.inflected || "").trim();
  const heroInflectedTranslit = (entry.inflectedTranslit || "").trim();
  const hero = {
    he: isHebrew,
    noGloss: isPN && !entry.greek && !isHebrew,
    script: isHebrew ? bdbEntry?.lemma || entry.gloss : entry.greek || nameOrGloss,
    translit: isHebrew ? bdbEntry?.xlit : entry.translit,
    standaloneGloss: trimTail(isPN || metavData ? properName : entry.greek && (entry.gloss || "").trim().split(/\s+/).length > 2 ? entry.english_head || entry.gloss : entry.gloss),
    morph: morphLine
  };
  // The small "in this verse" line shows the inflected form — only when we have one AND
  // it differs from the headword lemma (indeclinable words can coincide → skip it).
  const heroForm = heroInflected && heroInflected !== hero.script ? heroInflected : "";
  // Show "translit · gloss" on one line whenever there's both — same for Greek and
  // Hebrew so the two cards match. Falls back to a standalone gloss line only when
  // there's no transliteration.
  const heroInlineGloss = !!(hero.translit && hero.standaloneGloss && !hero.noGloss);

  // Verse + place sections show an English reading text (not ABP) for Hebrew /
  // KJV-mode / BSB-mode / place words. BSB pulls BSB text; the rest pull KJV.
  const useKjvText = entry.isKjv || entry.isBsb || isHebrew || metavType === "place" && !isPN;

  // Ordered list of stacked sections. BDB and LSJ are mutually exclusive (Hebrew
  // gets BDB; everything else may get LSJ) — same either/or as the old ternary.
  const sections = [];
  if (metavLoading || metavPersonData || metavPlaceData) sections.push("metav");
  if (aiDescription || aiDescLoading) sections.push("aidesc");
  if (isHebrewWord) sections.push("bdb");else if ((!isPN || metavType === "place" && metavData?.strongs_g?.length > 0) && metavType !== "person" && !aiDescription && !aiDescLoading && (entry.greek || entry.strongs_raw || metavData?.strongs_g?.length > 0)) sections.push("lsj");
  if (!isHebrew && !isPN && !entry.isKjv && !entry.isBsb && !entry.isExtra && abpCount !== null && abpCount > 0) sections.push("abpOcc");
  // Non-canon "other" books (Apostolic Fathers chip mode): suppress the occurrence
  // links/counts (the LXX cross-link above + this in-book count) until Lexicon search is
  // wired. Re-enable: drop `!entry.isExtra` above + uncomment extraOcc.
  // if (entry.isExtra && extraCount !== null && extraCount > 0) sections.push("extraOcc");
  if (entry.isKjv && !isHebrew && !isPN && kjvCount !== null && kjvCount > 0) sections.push("kjvOcc");
  if (entry.isBsb && !isPN && bsbCount !== null && bsbCount > 0) sections.push("bsbOcc");
  if (!entry.isKjv && !entry.isBsb && isPN && pnCount !== null && pnCount > 0 && onNameSearch) sections.push("pnOcc");
  if (isHebrew && !entry.isHeb && !entry.isBsb && kjvCount !== null && kjvCount > 0) sections.push("hebrewKjvOcc");
  // Nave's topical sits BELOW the lexicon/place cards (metaV, AI, BDB/LSJ) — it's a
  // study cross-link, not a definition, so it reads last among the reference blocks.
  if (naveData && naveData.sections.length) sections.push("naveTopical");
  if (entry.derivation) sections.push("derivation");
  if (entry.book && !entry.isExtra) sections.push("verse");
  if (occurrences > 0 || totalResults > 0) sections.push("frequency");
  const renderSection = id => {
    switch (id) {
      case "metav":
        return /*#__PURE__*/React.createElement("section", {
          key: "metav",
          className: "sec"
        }, metavLoading ? /*#__PURE__*/React.createElement("div", {
          className: "lsj-def lsj-def--loading"
        }, "Looking up\u2026") : /*#__PURE__*/React.createElement(React.Fragment, null, metavType === "person" && metavData ? /*#__PURE__*/React.createElement("div", {
          className: "metav-person"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, metavHasBoth ? /*#__PURE__*/React.createElement("span", {
          className: "metav-titleswitch"
        }, "Biblical", " ", /*#__PURE__*/React.createElement("button", {
          className: "metav-ts-b" + (metavTab === "person" ? " on" : ""),
          onClick: () => setMetavTab("person")
        }, "Person"), /*#__PURE__*/React.createElement("span", {
          className: "metav-ts-sep"
        }, "/"), /*#__PURE__*/React.createElement("button", {
          className: "metav-ts-b" + (metavTab === "place" ? " on" : ""),
          onClick: () => setMetavTab("place")
        }, "Place")) : /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, isGentilic ? "People / Clan" : "Biblical Person"), /*#__PURE__*/React.createElement("span", {
          className: "lsj-badge"
        }, "metaV")), /*#__PURE__*/React.createElement("div", {
          className: "metav-meta"
        }, metavData.gender && /*#__PURE__*/React.createElement("span", {
          className: "metav-tag"
        }, metavData.gender === "M" ? "Male" : "Female"), metavData.groups.filter(g => g.startsWith("Tribe")).map(g => /*#__PURE__*/React.createElement("span", {
          key: g,
          className: "metav-tag"
        }, g)), metavData.groups.includes("Genealogy of Jesus") && /*#__PURE__*/React.createElement("span", {
          className: "metav-tag metav-tag-gold"
        }, "Genealogy of Jesus")), (metavData.birth_year || metavData.death_year) && /*#__PURE__*/React.createElement("p", {
          className: "detail-p detail-p--meta",
          style: {
            fontSize: "13px"
          }
        }, metavData.birth_year && /*#__PURE__*/React.createElement("span", null, "Born: ", metavData.birth_year, metavData.birth_place ? `, ${metavData.birth_place}` : ""), metavData.birth_year && metavData.death_year && " · ", metavData.death_year && /*#__PURE__*/React.createElement("span", null, "Died: ", metavData.death_year, metavData.death_place ? `, ${metavData.death_place}` : "")), metavData.relationships.length > 0 && /*#__PURE__*/React.createElement("div", {
          className: "metav-rels"
        }, [{
          types: ["child"],
          label: "Parent"
        }, {
          types: ["father", "mother"],
          label: "Children"
        }, {
          types: ["spouseOrConcubine"],
          label: "Spouse"
        }, {
          types: ["sibling", "halfSiblingSameFather", "halfSiblingSameMother"],
          label: "Siblings"
        }].map(({
          types,
          label
        }) => {
          const matching = metavData.relationships.filter(r => types.includes(r.type));
          if (!matching.length) return null;
          return /*#__PURE__*/React.createElement("div", {
            key: label,
            className: "metav-rel-row"
          }, /*#__PURE__*/React.createElement("span", {
            className: "metav-rel-label"
          }, label), /*#__PURE__*/React.createElement("span", {
            className: "metav-rel-names"
          }, matching.slice(0, 5).map(r => r.name).join(", "), matching.length > 5 ? ` +${matching.length - 5}` : ""));
        }))) : metavType === "place" && metavData ? /*#__PURE__*/React.createElement("div", {
          className: "metav-place"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, metavHasBoth ? /*#__PURE__*/React.createElement("span", {
          className: "metav-titleswitch"
        }, "Biblical", " ", /*#__PURE__*/React.createElement("button", {
          className: "metav-ts-b" + (metavTab === "person" ? " on" : ""),
          onClick: () => setMetavTab("person")
        }, "Person"), /*#__PURE__*/React.createElement("span", {
          className: "metav-ts-sep"
        }, "/"), /*#__PURE__*/React.createElement("button", {
          className: "metav-ts-b" + (metavTab === "place" ? " on" : ""),
          onClick: () => setMetavTab("place")
        }, "Place")) : /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, isGentilic ? "Homeland" : "Biblical Place"), /*#__PURE__*/React.createElement("span", {
          className: "lsj-badge"
        }, "metaV")), metavData.comment && /*#__PURE__*/React.createElement("p", {
          className: "detail-p detail-p--meta"
        }, metavData.comment), metavData.lat && metavData.lon ? /*#__PURE__*/React.createElement(LeafletMap, {
          lat: metavData.lat,
          lon: metavData.lon,
          name: metavData.name
        }) : /*#__PURE__*/React.createElement("p", {
          className: "detail-p detail-p--meta",
          style: {
            color: "var(--ink-4)",
            fontStyle: "italic"
          }
        }, "Location unknown")) : null));
      case "naveTopical":
        {
          // Sidebar-only: cap at 5 so the side card stays short, and strip the leading
          // "N. " that Nave's bakes into each heading (so it reads "A name of Christ",
          // not "2. A name of Christ"). The full, un-stripped list lives on the Study page.
          const NAVE_CAP = 5;
          const shown = naveData.sections.slice(0, NAVE_CAP);
          const extra = naveData.sections.length - shown.length;
          const openFull = () => onOpenStudyName && onOpenStudyName(naveData.id);
          return /*#__PURE__*/React.createElement("section", {
            key: "naveTopical",
            className: "sec"
          }, /*#__PURE__*/React.createElement("h4", {
            className: "sec-head"
          }, /*#__PURE__*/React.createElement("span", {
            className: "sec-t"
          }, "Nave's Topical"), /*#__PURE__*/React.createElement("span", {
            className: "lsj-badge"
          }, "Nave's")), /*#__PURE__*/React.createElement("div", {
            className: "nave-secs"
          }, shown.map((s, i) => /*#__PURE__*/React.createElement("button", {
            key: i,
            className: "nave-sec",
            onClick: openFull
          }, /*#__PURE__*/React.createElement("span", {
            className: "nave-sec-h"
          }, (s.heading || "").replace(/^\s*\d+\.\s*/, "").trim() || "General"), /*#__PURE__*/React.createElement("span", {
            className: "nave-sec-n"
          }, s.n))), extra > 0 && /*#__PURE__*/React.createElement("button", {
            className: "nave-sec nave-sec--more",
            onClick: openFull
          }, /*#__PURE__*/React.createElement("span", {
            className: "nave-sec-h"
          }, "+ ", extra, " more in Study"))));
        }
      case "aidesc":
        return /*#__PURE__*/React.createElement("section", {
          key: "aidesc",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, metavType === "place" ? "Biblical Place" : "Biblical Reference"), /*#__PURE__*/React.createElement("span", {
          className: "lsj-badge lsj-badge--accent"
        }, "AI")), aiDescLoading ? /*#__PURE__*/React.createElement("div", {
          className: "lsj-def lsj-def--loading"
        }, "Looking up\u2026") : /*#__PURE__*/React.createElement("p", {
          className: "detail-p detail-p--meta"
        }, renderInlineMd(aiDescription)));
      case "bdb":
        return /*#__PURE__*/React.createElement("section", {
          key: "bdb",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "Brown-Driver-Briggs"), /*#__PURE__*/React.createElement("span", {
          className: "bdb-badge"
        }, "BDB")), bdbLoading ? /*#__PURE__*/React.createElement("div", {
          className: "lsj-def lsj-def--loading"
        }, "Loading\u2026") : bdbEntry ? /*#__PURE__*/React.createElement("div", {
          className: "bdb-body"
        }, bdbEntry.pronounce && /*#__PURE__*/React.createElement("div", {
          className: "bdb-xlit"
        }, /*#__PURE__*/React.createElement("span", {
          className: "bdb-pronounce"
        }, bdbEntry.pronounce)), bdbEntry.part_of_speech && /*#__PURE__*/React.createElement("span", {
          className: "bdb-pos-badge"
        }, bdbEntry.part_of_speech), bdbEntry.description && /*#__PURE__*/React.createElement("p", {
          className: "detail-p detail-p--meta"
        }, bdbEntry.description)) : /*#__PURE__*/React.createElement("div", {
          className: "lsj-def lsj-def--loading"
        }, "Not found in BDB."));
      case "lsj":
        return /*#__PURE__*/React.createElement("section", {
          key: "lsj",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, lsjEntry && lsjEntry.source === "abp_ext" ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "ABP Extended"), /*#__PURE__*/React.createElement("span", {
          className: "abp-badge"
        }, "ABP EXT")) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "Liddell-Scott-Jones"), /*#__PURE__*/React.createElement("span", {
          className: "lsj-badge"
        }, "LSJ"))), lsjLoading ? /*#__PURE__*/React.createElement("div", {
          className: "lsj-def lsj-def--loading"
        }, "Loading\u2026") : lsjEntry ? lsjEntry.source === "strongs" ? /*#__PURE__*/React.createElement("div", {
          className: "lsj-def",
          dangerouslySetInnerHTML: {
            __html: lsjEntry.def_html
          }
        }) : /*#__PURE__*/React.createElement(LsjSummary, {
          data: lsjSummary,
          loading: lsjSummaryLoading
        }) : /*#__PURE__*/React.createElement("div", {
          className: "lsj-def lsj-def--loading"
        }, "Not found."));
      case "abpOcc":
        return /*#__PURE__*/React.createElement("section", {
          key: "abpOcc",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, entry.isExtra ? "Occurrences in Scripture" : "ABP Occurrences")), /*#__PURE__*/React.createElement("button", {
          className: "occ-link",
          onClick: () => onNavigateToLexicon && onNavigateToLexicon(entry.strongs_raw, "abp")
        }, /*#__PURE__*/React.createElement("b", null, abpCount), "\xD7 in LXX ", /*#__PURE__*/React.createElement(Icon.ArrowRight, null)));
      case "extraOcc":
        return /*#__PURE__*/React.createElement("section", {
          key: "extraOcc",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "In the ", entry.extraBookName || "text")), /*#__PURE__*/React.createElement("div", {
          className: "occ-link occ-link--static"
        }, /*#__PURE__*/React.createElement("b", null, extraCount), "\xD7 in ", entry.extraBookName || "this text"));
      case "kjvOcc":
        return /*#__PURE__*/React.createElement("section", {
          key: "kjvOcc",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "KJV Occurrences")), /*#__PURE__*/React.createElement("button", {
          className: "occ-link",
          onClick: () => onNavigateToLexicon && onNavigateToLexicon(entry.strongs, "kjv")
        }, /*#__PURE__*/React.createElement("b", null, kjvCount), "\xD7 in KJV ", /*#__PURE__*/React.createElement(Icon.ArrowRight, null)));
      case "bsbOcc":
        return /*#__PURE__*/React.createElement("section", {
          key: "bsbOcc",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "BSB Occurrences")), /*#__PURE__*/React.createElement("div", {
          className: "occ-link occ-link--static"
        }, /*#__PURE__*/React.createElement("b", null, bsbCount), "\xD7 in BSB"));
      case "pnOcc":
        return /*#__PURE__*/React.createElement("section", {
          key: "pnOcc",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "ABP Occurrences")), /*#__PURE__*/React.createElement("button", {
          className: "occ-link",
          onClick: () => onNameSearch(extractProperName(entry.gloss))
        }, /*#__PURE__*/React.createElement("b", null, pnCount), "\xD7 in LXX ", /*#__PURE__*/React.createElement(Icon.ArrowRight, null)));
      case "hebrewKjvOcc":
        return /*#__PURE__*/React.createElement("section", {
          key: "hebrewKjvOcc",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "KJV Occurrences")), /*#__PURE__*/React.createElement("button", {
          className: "occ-link",
          onClick: () => onNavigateToLexicon && onNavigateToLexicon(entry.strongs, "kjv")
        }, /*#__PURE__*/React.createElement("b", null, kjvCount), "\xD7 in KJV ", /*#__PURE__*/React.createElement(Icon.ArrowRight, null)));
      case "derivation":
        return /*#__PURE__*/React.createElement("section", {
          key: "derivation",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "Derivation")), /*#__PURE__*/React.createElement("p", {
          className: "detail-p"
        }, entry.derivation.split(/\b(G\d[\d.]*)/i).map((part, i) => /^G\d[\d.]*/i.test(part) ? /*#__PURE__*/React.createElement("button", {
          key: i,
          className: "link-btn link-btn--strong",
          onClick: () => onNavigateToLexicon?.(part)
        }, part) : part)));
      case "verse":
        return /*#__PURE__*/React.createElement("section", {
          key: "verse",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "Verse \u2014 ", entry.ref), /*#__PURE__*/React.createElement("span", {
          className: "lsj-badge"
        }, entry.isBsb ? "BSB" : useKjvText ? "KJV" : "ABP")), /*#__PURE__*/React.createElement("blockquote", {
          className: "dverse"
        }, /*#__PURE__*/React.createElement("span", {
          className: "dverse-n"
        }, entry.verse), useKjvText ? kjvVerseText || "—" : verseLoading ? "Loading…" : verseText || "—"), showInterlinear && /*#__PURE__*/React.createElement("div", {
          className: "interlinear"
        }, !interlinearWords ? /*#__PURE__*/React.createElement("span", {
          style: {
            color: "var(--ink-4)",
            fontSize: "13px"
          }
        }, "Loading\u2026") : interlinearWords.length === 0 ? /*#__PURE__*/React.createElement("span", {
          style: {
            color: "var(--ink-4)",
            fontSize: "13px"
          }
        }, "No interlinear for this verse.") : (() => {
          // Uniform column structure so the english rows line up: reserve the
          // translit / strongs rows (hidden when a word lacks them) whenever the
          // verse uses them. ABP brackets render INLINE on the english word
          // ("[day" … "second].") — a separate bracket column sits at the column's
          // EDGE, which drifts away from a short english word (its column is as
          // wide as the greek/translit above it) while hugging a long one; on the
          // english text itself the bracket is always tight, on the reading line.
          const hasTranslit = interlinearWords.some(w => w.translit);
          const hasStrongs = interlinearWords.some(w => w.strongs);
          return interlinearWords.map((w, i) => {
            // A bracket group = consecutive words sharing bracket_id (same rule as
            // the reading pane). KJV/Hebrew carry no bracket_id, so they get none.
            const bid = w.bracket_id != null ? w.bracket_id : null;
            const prev = interlinearWords[i - 1],
              next = interlinearWords[i + 1];
            const open = bid != null && (!prev || prev.bracket_id !== bid);
            const close = bid != null && (!next || next.bracket_id !== bid);
            // On the group's last word, lift trailing clause punctuation outside
            // the "]" (mirror the reading pane: "second.]" -> "second].").
            let eng = w.english || "—",
              trail = "";
            if (close) {
              const m = (w.english || "").match(/[.,;:!?·]+$/);
              if (m) {
                trail = m[0];
                eng = (w.english || "").slice(0, m.index) || "—";
              }
            }
            return /*#__PURE__*/React.createElement("div", {
              className: "iword",
              key: i
            }, /*#__PURE__*/React.createElement("span", {
              className: "iw-greek" + (w.he ? " iw-heb" : "")
            }, w.top || "—"), hasTranslit && /*#__PURE__*/React.createElement("span", {
              className: "iw-translit",
              style: w.translit ? undefined : {
                visibility: "hidden"
              }
            }, w.translit || "x"), /*#__PURE__*/React.createElement("span", {
              className: "iw-english"
            }, open && /*#__PURE__*/React.createElement("span", {
              className: "iw-brk"
            }, "["), bid != null && w.pos != null && /*#__PURE__*/React.createElement("span", {
              className: "iw-pos"
            }, w.pos), eng, close && /*#__PURE__*/React.createElement("span", {
              className: "iw-brk"
            }, "]"), trail), hasStrongs && /*#__PURE__*/React.createElement("span", {
              className: "iw-strongs",
              style: w.strongs ? undefined : {
                visibility: "hidden"
              }
            }, w.strongs || "G0"));
          });
        })()), /*#__PURE__*/React.createElement("div", {
          className: "dverse-tools"
        }, /*#__PURE__*/React.createElement("button", {
          className: "link-btn",
          onClick: () => onReadInContext && onReadInContext(entry.book, entry.chapter, entry.verse)
        }, "Read in context ", /*#__PURE__*/React.createElement(Icon.ArrowRight, null)), /*#__PURE__*/React.createElement("span", {
          className: "dot"
        }, "\xB7"), /*#__PURE__*/React.createElement("button", {
          className: "link-btn" + (showInterlinear ? " link-btn-on" : ""),
          onClick: () => setShowInterlinear(v => !v)
        }, "Interlinear")));
      case "frequency":
        return /*#__PURE__*/React.createElement("section", {
          key: "frequency",
          className: "sec"
        }, /*#__PURE__*/React.createElement("h4", {
          className: "sec-head"
        }, /*#__PURE__*/React.createElement("span", {
          className: "sec-t"
        }, "Frequency")), /*#__PURE__*/React.createElement("div", {
          className: "freq"
        }, /*#__PURE__*/React.createElement("div", {
          className: "freq-bar"
        }, /*#__PURE__*/React.createElement("div", {
          className: "freq-fill",
          style: {
            width: barWidth + "%"
          }
        })), /*#__PURE__*/React.createElement("div", {
          className: "freq-meta"
        }, /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("b", null, occurrences), "\xD7 in current results"))));
      default:
        return null;
    }
  };
  return /*#__PURE__*/React.createElement("aside", {
    ref: isMobile ? sheetRef : null,
    className: "detail " + (isMobile ? "detail-sheet" : "detail-side"),
    role: "dialog",
    "aria-label": "Lexicon detail"
  }, isMobile && /*#__PURE__*/React.createElement("div", {
    className: "sheet-drag-zone",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet-handle"
  })), /*#__PURE__*/React.createElement("div", {
    className: "detail-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-head-l"
  }, /*#__PURE__*/React.createElement("span", {
    className: "detail-strong-head"
  }, entry.strongs)), overviewBack && !isMobile ? /*#__PURE__*/React.createElement("button", {
    className: "detail-back",
    onClick: onClose,
    "aria-label": "Back to " + backLabel.toLowerCase()
  }, "\u2039 ", backLabel) : /*#__PURE__*/React.createElement("button", {
    className: "detail-close",
    onClick: onClose,
    "aria-label": "Close"
  }, /*#__PURE__*/React.createElement(Icon.Close, null))), /*#__PURE__*/React.createElement("div", {
    className: "detail-body",
    ref: isMobile ? scrollRef : null
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-hero" + (hero.noGloss ? " no-gloss" : "")
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-hero-id"
  }, /*#__PURE__*/React.createElement("div", {
    ref: heroRef,
    className: "detail-greek" + (hero.he ? " detail-greek--he" : !entry.greek ? " detail-greek--latin" : ""),
    dir: hero.he ? "rtl" : undefined
  }, hero.script), (hero.translit || heroInlineGloss) && /*#__PURE__*/React.createElement("div", {
    className: "detail-translit-row" + (hero.he ? " detail-translit-row-he" : "")
  }, /*#__PURE__*/React.createElement("span", {
    className: "detail-translit"
  }, hero.translit), heroInlineGloss && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "detail-sep"
  }, "\xB7"), /*#__PURE__*/React.createElement("span", {
    className: "detail-gloss"
  }, hero.standaloneGloss))), !hero.noGloss && !heroInlineGloss && /*#__PURE__*/React.createElement("div", {
    className: "detail-gloss"
  }, hero.standaloneGloss)), (heroForm || hero.morph) && /*#__PURE__*/React.createElement("div", {
    className: "detail-hero-occ" + (heroForm ? "" : " detail-hero-occ--tight")
  }, heroForm && /*#__PURE__*/React.createElement("span", {
    className: "detail-form-label"
  }, "in this verse"), heroForm && /*#__PURE__*/React.createElement("span", {
    className: "detail-form-w" + (hero.he ? " detail-form-w--he" : ""),
    dir: hero.he ? "rtl" : undefined
  }, heroForm), heroForm && heroInflectedTranslit && heroInflectedTranslit !== hero.translit && /*#__PURE__*/React.createElement("span", {
    className: "detail-form-tr"
  }, heroInflectedTranslit), hero.morph && /*#__PURE__*/React.createElement("div", {
    className: "detail-morph"
  }, hero.morph))), sections.map(renderSection)));
}

// ============================================================
// NOTES UI — add popover, editor panel, browse view
// ------------------------------------------------------------
// Drag-select text in the Library reader → a small "Add note" bar pops by the
// selection → opens the editor panel (same right-sidebar / bottom-sheet slot
// the word-study and cross-ref panels use). The Notes tab lists & searches
// every saved note and jumps back to its verse.
// ============================================================

// "Add note" affordance for a text selection. On DESKTOP it floats just above
// the selection. On MOBILE the OS floats its own copy/share toolbar right there,
// so ours is pinned to the bottom of the screen (above the tab bar) to avoid the
// collision.
function NoteAddPopover({
  rect,
  isMobile,
  onAdd,
  onColor,
  onCopy,
  onJournal
}) {
  if (!rect) return null;
  let style;
  if (isMobile) {
    style = {
      position: "fixed",
      left: "50%",
      transform: "translateX(-50%)",
      bottom: 72,
      zIndex: 1000
    };
  } else {
    const W = 360;
    style = {
      position: "fixed",
      top: Math.max(8, rect.top - 48),
      left: Math.min(window.innerWidth - W - 8, Math.max(8, rect.left + rect.width / 2 - W / 2)),
      zIndex: 1000
    };
  }
  // preventDefault on mousedown so pressing a button doesn't clear the selection
  return /*#__PURE__*/React.createElement("div", {
    className: "note-popover" + (isMobile ? " note-popover-mobile" : ""),
    style: style,
    onMouseDown: e => e.preventDefault()
  }, /*#__PURE__*/React.createElement("div", {
    className: "note-swatches"
  }, NOTE_COLORS.map(c => /*#__PURE__*/React.createElement("button", {
    key: c,
    className: "note-swatch",
    style: {
      background: NOTE_COLOR_CSS[c]
    },
    title: "Highlight " + c,
    "aria-label": "Highlight " + c,
    onClick: () => onColor(c)
  }))), /*#__PURE__*/React.createElement("button", {
    className: "note-popover-btn",
    onClick: onAdd
  }, /*#__PURE__*/React.createElement(Icon.Note, null), /*#__PURE__*/React.createElement("span", {
    className: "note-btn-lbl"
  }, "Note")), onJournal && /*#__PURE__*/React.createElement("button", {
    className: "note-popover-btn",
    onClick: onJournal
  }, /*#__PURE__*/React.createElement(Icon.Book, null), /*#__PURE__*/React.createElement("span", {
    className: "note-btn-lbl"
  }, "Journal")), onCopy && /*#__PURE__*/React.createElement("button", {
    className: "note-popover-btn",
    onClick: onCopy
  }, /*#__PURE__*/React.createElement(Icon.Copy, null), /*#__PURE__*/React.createElement("span", {
    className: "note-btn-lbl"
  }, "Copy")));
}

// Menu shown when you right-click / long-press a verse number: Bookmark · Note · colors.
function VerseNoteMenu({
  rect,
  isMobile,
  onBookmark,
  onNote,
  onColor,
  onCopy,
  onJournal,
  onClose
}) {
  if (!rect) return null;
  let style;
  if (isMobile) {
    style = {
      position: "fixed",
      left: "50%",
      transform: "translateX(-50%)",
      bottom: 72,
      zIndex: 1000
    };
  } else {
    const W = 270;
    style = {
      position: "fixed",
      top: Math.min(window.innerHeight - 56, rect.top + rect.height + 6),
      left: Math.min(window.innerWidth - W - 8, Math.max(8, rect.left)),
      zIndex: 1000
    };
  }
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "note-menu-scrim",
    onClick: onClose
  }), /*#__PURE__*/React.createElement("div", {
    className: "note-popover" + (isMobile ? " note-popover-mobile" : ""),
    style: style,
    onMouseDown: e => e.preventDefault()
  }, /*#__PURE__*/React.createElement("div", {
    className: "note-swatches"
  }, NOTE_COLORS.map(c => /*#__PURE__*/React.createElement("button", {
    key: c,
    className: "note-swatch",
    style: {
      background: NOTE_COLOR_CSS[c]
    },
    title: "Highlight " + c,
    "aria-label": "Highlight " + c,
    onClick: () => onColor(c)
  }))), /*#__PURE__*/React.createElement("button", {
    className: "note-popover-btn",
    onClick: onNote
  }, /*#__PURE__*/React.createElement(Icon.Note, null), /*#__PURE__*/React.createElement("span", {
    className: "note-btn-lbl"
  }, "Note")), onJournal && /*#__PURE__*/React.createElement("button", {
    className: "note-popover-btn",
    onClick: onJournal
  }, /*#__PURE__*/React.createElement(Icon.Book, null), /*#__PURE__*/React.createElement("span", {
    className: "note-btn-lbl"
  }, "Journal")), onCopy && /*#__PURE__*/React.createElement("button", {
    className: "note-popover-btn",
    onClick: onCopy
  }, /*#__PURE__*/React.createElement(Icon.Copy, null), /*#__PURE__*/React.createElement("span", {
    className: "note-btn-lbl"
  }, "Copy")), /*#__PURE__*/React.createElement("button", {
    className: "note-popover-btn",
    onClick: onBookmark
  }, /*#__PURE__*/React.createElement(Icon.Bookmark, null), /*#__PURE__*/React.createElement("span", {
    className: "note-btn-lbl"
  }, "Bookmark"))));
}

// A row of color swatches + a clear button, for the editor.
function NoteColorRow({
  value,
  onPick
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "note-color-row"
  }, NOTE_COLORS.map(c => /*#__PURE__*/React.createElement("button", {
    key: c,
    className: "note-swatch" + (value === c ? " on" : ""),
    style: {
      background: NOTE_COLOR_CSS[c]
    },
    title: "Highlight " + c,
    "aria-label": "Highlight " + c,
    onClick: () => onPick(value === c ? null : c)
  })), /*#__PURE__*/React.createElement("button", {
    className: "note-swatch note-swatch-none" + (!value ? " on" : ""),
    title: "No highlight",
    "aria-label": "No highlight",
    onClick: () => onPick(null)
  }, "\u2715"));
}

// Write / edit / delete a single note. Reuses the .detail shell.
function NotesPanel({
  noteId,
  isMobile,
  onClose
}) {
  const note = NotesStore.get(noteId);
  const [body, setBody] = useState(note ? note.body || "" : "");
  const [color, setColor] = useState(note ? note.color || null : null);
  const [bookmark, setBookmark] = useState(note ? !!note.bookmark : false);
  const taRef = useRef(null);
  useEffect(() => {
    setBody(note ? note.body || "" : "");
    setColor(note ? note.color || null : null);
    setBookmark(note ? !!note.bookmark : false);
    // Desktop: focus the box right away. Mobile: DON'T — auto-popping the
    // on-screen keyboard covers a freshly opened sheet. The user taps to type.
    if (!isMobile) requestAnimationFrame(() => taRef.current && taRef.current.focus());
  }, [noteId]);
  const save = () => {
    NotesStore.update(noteId, {
      body,
      color,
      bookmark
    });
    onClose();
  };
  const del = () => {
    NotesStore.remove(noteId);
    onClose();
  };
  // Closing a record that's blank AND uncolored AND not bookmarked discards it
  // (id minted on create, so a thrown-away draft shouldn't linger).
  const close = () => {
    if (!body.trim() && !color && !bookmark) NotesStore.remove(noteId);else NotesStore.update(noteId, {
      body,
      color,
      bookmark
    });
    onClose();
  };
  // Swipe-down-to-close on mobile (same hook the word / xref / summary sheets use).
  const {
    sheetRef,
    scrollRef
  } = useSwipeToDismiss(close);
  if (!note) return null;
  const head = /*#__PURE__*/React.createElement("div", {
    className: "detail-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-head-l"
  }, /*#__PURE__*/React.createElement("span", {
    className: "detail-pos summary-pos"
  }, note.refLabel || note.book + " " + note.chapter)), /*#__PURE__*/React.createElement("button", {
    className: "note-bm-toggle" + (bookmark ? " on" : ""),
    onClick: () => setBookmark(b => !b),
    title: bookmark ? "Bookmarked" : "Bookmark this",
    "aria-label": "Toggle bookmark",
    "aria-pressed": bookmark
  }, /*#__PURE__*/React.createElement(Icon.Bookmark, null)), /*#__PURE__*/React.createElement("button", {
    className: "detail-close",
    onClick: close,
    "aria-label": "Close"
  }, /*#__PURE__*/React.createElement(Icon.Close, null)));
  const content = /*#__PURE__*/React.createElement("div", {
    className: "detail-body note-edit-body",
    ref: isMobile ? scrollRef : undefined
  }, note.snippet && /*#__PURE__*/React.createElement("blockquote", {
    className: "note-snippet"
  }, "\u201C", note.snippet, "\u201D"), /*#__PURE__*/React.createElement(NoteColorRow, {
    value: color,
    onPick: setColor
  }), /*#__PURE__*/React.createElement("textarea", {
    ref: taRef,
    className: "note-textarea",
    value: body,
    onChange: e => setBody(e.target.value),
    placeholder: "Write your note\u2026"
  }), /*#__PURE__*/React.createElement("div", {
    className: "note-actions"
  }, /*#__PURE__*/React.createElement("button", {
    className: "note-save",
    onClick: save
  }, "Save"), /*#__PURE__*/React.createElement("button", {
    className: "note-del",
    onClick: del
  }, "Delete")));
  if (isMobile) {
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      className: "sheet-scrim",
      onClick: close
    }), /*#__PURE__*/React.createElement("aside", {
      ref: sheetRef,
      className: "detail detail-sheet note-sheet",
      role: "dialog",
      "aria-label": "Note"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sheet-drag-zone",
      "aria-hidden": "true"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sheet-handle"
    })), head, content));
  }
  return /*#__PURE__*/React.createElement("aside", {
    className: "detail detail-side note-side",
    role: "complementary",
    "aria-label": "Note"
  }, head, content);
}

// One free-form journal page (plain text). No verse anchor — a title + a big
// box you type into. Autosaves as you write; rides the same store/sync as notes.
const JOURNAL_MAX = 60000; // chars; stays safely under the server's 64KB page cap
function JournalEditor({
  pageId,
  onBack
}) {
  const page = NotesStore.get(pageId);
  const [title, setTitle] = useState(page ? page.title || "" : "");
  const [body, setBody] = useState(page ? page.body || "" : "");
  const saveTimer = useRef(null);
  const first = useRef(true);

  // This is now the page that "send verse to journal" (in the reader) targets.
  useEffect(() => {
    NotesStore.setActiveJournal(pageId);
  }, [pageId]);

  // Autosave ~0.8s after you stop typing. Skip the very first run so just
  // opening a page doesn't re-stamp it as edited.
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      NotesStore.update(pageId, {
        title,
        body
      });
    }, 800);
    return () => clearTimeout(saveTimer.current);
  }, [title, body]);
  const back = () => {
    clearTimeout(saveTimer.current);
    // A page never given a title or any text is a thrown-away draft — discard it.
    if (!title.trim() && !body.trim()) NotesStore.remove(pageId);else NotesStore.update(pageId, {
      title,
      body
    });
    onBack();
  };
  const del = () => {
    clearTimeout(saveTimer.current);
    NotesStore.remove(pageId);
    onBack();
  };
  if (!page) {
    onBack();
    return null;
  }
  const near = body.length > JOURNAL_MAX - 2000;
  return /*#__PURE__*/React.createElement("div", {
    className: "journal-editor"
  }, /*#__PURE__*/React.createElement("div", {
    className: "journal-editor-bar"
  }, /*#__PURE__*/React.createElement("button", {
    className: "notes-tool-btn",
    onClick: back
  }, "\u2039 Back"), /*#__PURE__*/React.createElement("button", {
    className: "note-del",
    onClick: del
  }, "Delete")), /*#__PURE__*/React.createElement("input", {
    className: "journal-title-input",
    type: "text",
    value: title,
    maxLength: 200,
    onChange: e => setTitle(e.target.value),
    placeholder: "Page title"
  }), /*#__PURE__*/React.createElement("textarea", {
    className: "journal-textarea",
    value: body,
    maxLength: JOURNAL_MAX,
    onChange: e => setBody(e.target.value),
    placeholder: "Write freely \u2014 thoughts, questions, an outline, a study\u2026"
  }), /*#__PURE__*/React.createElement("div", {
    className: "journal-count" + (near ? " warn" : "")
  }, body.length.toLocaleString(), " characters", near ? " — near the page limit; start a new page for more" : ""));
}

// The Journal side of the Notes tab — a list of free-form pages + an editor.
function JournalView() {
  useNotesVersion();
  const [editing, setEditing] = useState(null);
  const pages = NotesStore.journals();
  if (editing) return /*#__PURE__*/React.createElement(JournalEditor, {
    pageId: editing,
    onBack: () => setEditing(null)
  });
  const fmtDate = iso => {
    try {
      return new Date(iso).toLocaleDateString();
    } catch (e) {
      return "";
    }
  };
  const newPage = () => {
    const p = NotesStore.createJournal();
    setEditing(p.id);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "journal-view"
  }, /*#__PURE__*/React.createElement("div", {
    className: "journal-toolbar"
  }, /*#__PURE__*/React.createElement("button", {
    className: "notes-tool-btn on",
    onClick: newPage
  }, "+ New page")), pages.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "notes-empty"
  }, "No journal pages yet. Tap \u201CNew page\u201D to start writing \u2014 free-form, not tied to any verse.") : /*#__PURE__*/React.createElement("ul", {
    className: "journal-list"
  }, pages.map(p => /*#__PURE__*/React.createElement("li", {
    key: p.id,
    className: "journal-item",
    onClick: () => setEditing(p.id)
  }, /*#__PURE__*/React.createElement("div", {
    className: "journal-item-title"
  }, (p.title || "").trim() || "Untitled page"), (p.body || "").trim() && /*#__PURE__*/React.createElement("div", {
    className: "journal-item-preview"
  }, p.body.trim().slice(0, 160)), /*#__PURE__*/React.createElement("div", {
    className: "journal-item-date"
  }, fmtDate(p.updated))))));
}

// The Notes tab — list + search of every saved note.
function NotesView({
  onOpen
}) {
  useNotesVersion();
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("all"); // all | bookmark | highlight | note
  const [sort, setSort] = useState("recent"); // recent | ref
  const [group, setGroup] = useState(false); // group by book
  const [collapsed, setCollapsed] = useState(() => new Set()); // collapsed book keys
  const toggleSection = key => setCollapsed(s => {
    const n = new Set(s);
    n.has(key) ? n.delete(key) : n.add(key);
    return n;
  });
  const [authOpen, setAuthOpen] = useState(null); // null | "login" | "signup"
  const [acctOpen, setAcctOpen] = useState(false); // account / options panel
  const [mode, setMode] = useState("notes"); // notes | journal
  const acct = NotesStore.authInfo();
  let notes = NotesStore.search(q); // already newest-first
  if (filter === "bookmark") notes = notes.filter(n => n.bookmark);else if (filter === "highlight") notes = notes.filter(n => n.color);else if (filter === "note") notes = notes.filter(n => n.body && n.body.trim());

  // Canonical order: Bible books by BOOK_ORDER, non-canon after, by name.
  const bookRank = n => BOOK_ORDER[n.book] != null ? BOOK_ORDER[n.book] : 1000;
  const byRef = (a, b) => {
    const ra = bookRank(a),
      rb = bookRank(b);
    if (ra !== rb) return ra - rb;
    const na = a.bookName || a.book,
      nb = b.bookName || b.book;
    if (ra === 1000 && na !== nb) return na.localeCompare(nb);
    if (a.chapter !== b.chapter) return a.chapter - b.chapter;
    return a.start.verse - b.start.verse;
  };
  if (sort === "ref") notes = [...notes].sort(byRef);

  // Optional grouping by book (sections in canonical order, items by reference).
  let sections = null;
  if (group) {
    const map = new Map();
    for (const n of notes) {
      if (!map.has(n.book)) map.set(n.book, {
        key: n.book,
        label: BOOK_LABELS[n.book] || n.bookName || n.book,
        rank: bookRank(n),
        items: []
      });
      map.get(n.book).items.push(n);
    }
    sections = [...map.values()].sort((a, b) => a.rank - b.rank || a.label.localeCompare(b.label));
    sections.forEach(s => s.items.sort(byRef));
  }
  const renderItem = n => /*#__PURE__*/React.createElement("li", {
    key: n.id,
    className: "notes-item",
    onClick: () => onOpen(n)
  }, /*#__PURE__*/React.createElement("div", {
    className: "notes-item-ref"
  }, (n.body || n.bookmark) && /*#__PURE__*/React.createElement("span", {
    className: "notes-item-type",
    "aria-hidden": "true"
  }, n.body ? /*#__PURE__*/React.createElement(Icon.Note, null) : /*#__PURE__*/React.createElement(Icon.Bookmark, null)), n.color && /*#__PURE__*/React.createElement("span", {
    className: "notes-item-dot",
    style: {
      background: NOTE_COLOR_CSS[n.color]
    }
  }), n.refLabel || n.book + " " + n.chapter), n.snippet && /*#__PURE__*/React.createElement("div", {
    className: "notes-item-snippet"
  }, "\u201C", n.snippet, "\u201D"), n.body && /*#__PURE__*/React.createElement("div", {
    className: "notes-item-body"
  }, n.body));
  return /*#__PURE__*/React.createElement("div", {
    className: "notes-view"
  }, /*#__PURE__*/React.createElement("div", {
    className: "notes-view-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "notes-view-titlerow"
  }, /*#__PURE__*/React.createElement("h2", {
    className: "notes-view-title"
  }, "My Notes"), /*#__PURE__*/React.createElement("div", {
    className: "notes-acct"
  }, acct.email ? /*#__PURE__*/React.createElement("button", {
    className: "notes-acct-email",
    title: "Account & options",
    onClick: () => setAcctOpen(true)
  }, /*#__PURE__*/React.createElement("span", {
    className: "notes-acct-addr"
  }, acct.email), /*#__PURE__*/React.createElement("span", {
    className: "notes-acct-caret",
    "aria-hidden": "true"
  }, "\u25BE")) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    className: "notes-tool-btn",
    onClick: () => setAuthOpen("login")
  }, "Log in"), /*#__PURE__*/React.createElement("button", {
    className: "notes-tool-btn",
    onClick: () => setAuthOpen("signup")
  }, "Sign up")))), /*#__PURE__*/React.createElement("div", {
    className: "notes-mode seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (mode === "notes" ? " on" : ""),
    onClick: () => setMode("notes")
  }, "Verse notes"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (mode === "journal" ? " on" : ""),
    onClick: () => setMode("journal")
  }, "Journal")), mode === "notes" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("input", {
    className: "notes-search",
    type: "text",
    placeholder: "Search your notes\u2026",
    value: q,
    onChange: e => setQ(e.target.value)
  }), /*#__PURE__*/React.createElement("div", {
    className: "notes-controls"
  }, /*#__PURE__*/React.createElement("div", {
    className: "notes-filter seg"
  }, [["all", "All"], ["bookmark", "★ Bookmarks"], ["highlight", "🎨 Highlights"], ["note", "✎ Notes"]].map(([k, lbl]) => /*#__PURE__*/React.createElement("button", {
    key: k,
    className: "seg-b" + (filter === k ? " on" : ""),
    onClick: () => setFilter(k)
  }, lbl))), /*#__PURE__*/React.createElement("div", {
    className: "seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (sort === "recent" ? " on" : ""),
    onClick: () => setSort("recent")
  }, "Recent"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (sort === "ref" ? " on" : ""),
    onClick: () => setSort("ref")
  }, "Reference")), /*#__PURE__*/React.createElement("button", {
    className: "notes-tool-btn" + (group ? " on" : ""),
    onClick: () => setGroup(g => !g)
  }, "Group by book")))), mode === "journal" ? /*#__PURE__*/React.createElement(JournalView, null) : notes.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "notes-empty"
  }, q || filter !== "all" ? "Nothing matches that." : "No notes yet. In the Library, select some text in a verse and choose “Add note.”") : group ? sections.map(s => {
    const open = !collapsed.has(s.key);
    return /*#__PURE__*/React.createElement("div", {
      key: s.key,
      className: "notes-group"
    }, /*#__PURE__*/React.createElement("button", {
      className: "notes-group-head" + (open ? " open" : ""),
      onClick: () => toggleSection(s.key),
      "aria-expanded": open
    }, /*#__PURE__*/React.createElement("span", {
      className: "notes-group-caret"
    }, "\u25B8"), /*#__PURE__*/React.createElement("span", {
      className: "notes-group-label"
    }, s.label), /*#__PURE__*/React.createElement("span", {
      className: "notes-group-count"
    }, s.items.length)), open && /*#__PURE__*/React.createElement("ul", {
      className: "notes-list"
    }, s.items.map(renderItem)));
  }) : /*#__PURE__*/React.createElement("ul", {
    className: "notes-list"
  }, notes.map(renderItem)), authOpen && /*#__PURE__*/React.createElement(AuthModal, {
    mode: authOpen,
    onClose: () => setAuthOpen(null)
  }), acctOpen && /*#__PURE__*/React.createElement(AccountModal, {
    onClose: () => setAcctOpen(false)
  }));
}

// Account / options panel — opened from the signed-in email in the Notes header.
// Holds account actions (log out) + reading-plan progress management. Built to grow:
// new account-level options drop in as more .acct-sec blocks.
const PLAN_TEXT_LABELS = {
  abp: "ABP",
  kjv: "KJV",
  bsb: "BSB",
  esv: "ESV",
  niv: "NIV"
};
function AccountModal({
  onClose
}) {
  useNotesVersion(); // re-render after a clear (NotesStore.clearPlan notifies)
  const acct = NotesStore.authInfo();
  const plan = planLoadAll();
  const rows = Object.keys(plan).map(k => ({
    text: k,
    done: plan[k] && Array.isArray(plan[k].done) ? plan[k].done.length : 0
  })).filter(r => r.done > 0).sort((a, b) => a.text.localeCompare(b.text));
  const label = t => PLAN_TEXT_LABELS[t] || t.toUpperCase();
  const clearOne = t => {
    if (window.confirm(`Clear your ${label(t)} reading-plan progress?`)) NotesStore.clearPlan(t);
  };
  const clearAll = () => {
    if (window.confirm("Clear ALL reading-plan progress (every text)?")) NotesStore.clearPlan("*");
  };
  const [pw, setPw] = useState("");
  const [pwMsg, setPwMsg] = useState("");
  const [pwBusy, setPwBusy] = useState(false);
  const savePw = async () => {
    if (pwBusy) return;
    if (!pw || pw.length < 8) {
      setPwMsg("At least 8 characters.");
      return;
    }
    setPwBusy(true);
    setPwMsg("");
    const r = await NotesStore.setPassword(pw);
    setPwBusy(false);
    setPwMsg(r.ok ? "Password updated." : r.error || "Couldn't update.");
    if (r.ok) setPw("");
  };
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "auth-scrim",
    onClick: onClose
  }), /*#__PURE__*/React.createElement("div", {
    className: "auth-modal",
    role: "dialog",
    "aria-modal": "true",
    "aria-label": "Account and options"
  }, /*#__PURE__*/React.createElement("div", {
    className: "auth-modal-head"
  }, /*#__PURE__*/React.createElement("h3", {
    className: "auth-modal-title"
  }, "Account"), /*#__PURE__*/React.createElement("button", {
    className: "detail-close",
    onClick: onClose,
    "aria-label": "Close"
  }, /*#__PURE__*/React.createElement(Icon.Close, null))), /*#__PURE__*/React.createElement("p", {
    className: "auth-modal-sub"
  }, acct.email), /*#__PURE__*/React.createElement("div", {
    className: "acct-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acct-sec-h"
  }, "Reading plan progress"), rows.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "acct-empty"
  }, "No reading-plan progress yet.") : /*#__PURE__*/React.createElement("ul", {
    className: "acct-plan-list"
  }, rows.map(r => /*#__PURE__*/React.createElement("li", {
    key: r.text,
    className: "acct-plan-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "acct-plan-name"
  }, label(r.text)), /*#__PURE__*/React.createElement("span", {
    className: "acct-plan-count"
  }, r.done, " ", r.done === 1 ? "day" : "days", " read"), /*#__PURE__*/React.createElement("button", {
    className: "acct-plan-clear",
    onClick: () => clearOne(r.text)
  }, "Clear")))), rows.length > 1 && /*#__PURE__*/React.createElement("button", {
    className: "acct-plan-clearall",
    onClick: clearAll
  }, "Clear all progress")), /*#__PURE__*/React.createElement("div", {
    className: "acct-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "acct-sec-h"
  }, "Password"), /*#__PURE__*/React.createElement("div", {
    className: "acct-pw-row"
  }, /*#__PURE__*/React.createElement("input", {
    className: "auth-input",
    type: "password",
    placeholder: "New password",
    autoComplete: "new-password",
    value: pw,
    onChange: e => setPw(e.target.value),
    onKeyDown: e => {
      if (e.key === "Enter") savePw();
    }
  }), /*#__PURE__*/React.createElement("button", {
    className: "acct-plan-clear",
    onClick: savePw,
    disabled: pwBusy
  }, pwBusy ? "…" : "Set")), pwMsg && /*#__PURE__*/React.createElement("div", {
    className: "auth-fine"
  }, pwMsg), /*#__PURE__*/React.createElement("div", {
    className: "acct-empty"
  }, "Set a password to also sign in without Google.")), /*#__PURE__*/React.createElement("button", {
    className: "auth-submit acct-logout",
    onClick: () => {
      NotesStore.logout();
      onClose();
    }
  }, "Log out")));
}

// Centered login / sign-up dialog.
// modes: "login" | "signup" | "forgot" (email me a reset link) | "reset" (set a new
// password from a link's token, passed in resetToken).
function AuthModal({
  mode,
  onClose,
  resetToken
}) {
  const [m, setM] = useState(mode);
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [err, setErr] = useState("");
  const [sent, setSent] = useState(false); // forgot-password confirmation shown
  const [busy, setBusy] = useState(false);
  const [gid, setGid] = useState(null); // Google Client ID, if configured
  const emailRef = useRef(null);
  const passRef = useRef(null);
  const gbtnRef = useRef(null);
  const isPw = m === "login" || m === "signup"; // email + password / Google modes
  useEffect(() => {
    requestAnimationFrame(() => {
      const el = m === "reset" ? passRef.current : emailRef.current;
      el && el.focus();
    });
  }, []);

  // Is "Sign in with Google" turned on for this site? (login/signup only)
  useEffect(() => {
    if (!isPw) return;
    fetch("/api/auth/config").then(r => r.json()).then(d => setGid(d.google_client_id || null)).catch(() => {});
  }, [isPw]);

  // Load Google's button + wire the callback (only when configured + a pw mode).
  useEffect(() => {
    if (!gid || !isPw) return;
    let cancelled = false;
    const init = () => {
      if (cancelled || !window.google || !window.google.accounts || !gbtnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: gid,
        callback: resp => {
          NotesStore.googleLogin(resp.credential).then(r => {
            if (r.ok) onClose();else setErr(r.error);
          });
        }
      });
      gbtnRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(gbtnRef.current, {
        theme: "outline",
        size: "large",
        width: 300,
        text: m === "signup" ? "signup_with" : "signin_with"
      });
    };
    if (window.google && window.google.accounts) {
      init();
      return () => {
        cancelled = true;
      };
    }
    let s = document.getElementById("gsi-script");
    if (!s) {
      s = document.createElement("script");
      s.src = "https://accounts.google.com/gsi/client";
      s.async = true;
      s.defer = true;
      s.id = "gsi-script";
      document.head.appendChild(s);
    }
    s.addEventListener("load", init);
    return () => {
      cancelled = true;
      s && s.removeEventListener("load", init);
    };
  }, [gid, m, isPw]);
  const submit = async () => {
    if (busy) return;
    setBusy(true);
    setErr("");
    if (m === "forgot") {
      await NotesStore.requestReset(email);
      setBusy(false);
      setSent(true); // never reveal whether the email exists
      return;
    }
    if (m === "reset") {
      const r = await NotesStore.resetPassword(resetToken, pass);
      setBusy(false);
      if (r.ok) onClose();else setErr(r.error || "That reset link is invalid or has expired.");
      return;
    }
    const r = m === "signup" ? await NotesStore.signup(email, pass) : await NotesStore.login(email, pass);
    setBusy(false);
    if (r.ok) onClose();else setErr(r.error || "Something went wrong.");
  };
  const title = m === "signup" ? "Create account" : m === "forgot" ? "Reset password" : m === "reset" ? "Choose a new password" : "Log in";
  const cta = m === "signup" ? "Create account" : m === "forgot" ? "Send reset link" : m === "reset" ? "Set new password" : "Log in";
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "auth-scrim",
    onClick: onClose
  }), /*#__PURE__*/React.createElement("div", {
    className: "auth-modal",
    role: "dialog",
    "aria-modal": "true",
    "aria-label": title
  }, /*#__PURE__*/React.createElement("div", {
    className: "auth-modal-head"
  }, /*#__PURE__*/React.createElement("h3", {
    className: "auth-modal-title"
  }, title), /*#__PURE__*/React.createElement("button", {
    className: "detail-close",
    onClick: onClose,
    "aria-label": "Close"
  }, /*#__PURE__*/React.createElement(Icon.Close, null))), m === "reset" ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("p", {
    className: "auth-modal-sub"
  }, "Pick a new password for your account."), /*#__PURE__*/React.createElement("input", {
    ref: passRef,
    className: "auth-input",
    type: "password",
    placeholder: "New password",
    autoComplete: "new-password",
    value: pass,
    onChange: e => setPass(e.target.value),
    onKeyDown: e => {
      if (e.key === "Enter") submit();
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "auth-fine"
  }, "At least 8 characters.")) : m === "forgot" ? sent ? /*#__PURE__*/React.createElement("p", {
    className: "auth-modal-sub"
  }, "If that email has an account, a reset link is on its way. The link expires in 1 hour \u2014 check your inbox (and spam folder).") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("p", {
    className: "auth-modal-sub"
  }, "Enter your email and we'll send a link to set a new password."), /*#__PURE__*/React.createElement("input", {
    ref: emailRef,
    className: "auth-input",
    type: "email",
    placeholder: "Email",
    autoComplete: "username",
    value: email,
    onChange: e => setEmail(e.target.value),
    onKeyDown: e => {
      if (e.key === "Enter") submit();
    }
  })) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("p", {
    className: "auth-modal-sub"
  }, "Sync your notes across devices."), gid && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "auth-google",
    ref: gbtnRef
  }), /*#__PURE__*/React.createElement("div", {
    className: "auth-or"
  }, /*#__PURE__*/React.createElement("span", null, "or"))), /*#__PURE__*/React.createElement("input", {
    ref: emailRef,
    className: "auth-input",
    type: "email",
    placeholder: "Email",
    autoComplete: "username",
    value: email,
    onChange: e => setEmail(e.target.value),
    onKeyDown: e => {
      if (e.key === "Enter") submit();
    }
  }), /*#__PURE__*/React.createElement("input", {
    className: "auth-input",
    type: "password",
    placeholder: "Password",
    autoComplete: m === "signup" ? "new-password" : "current-password",
    value: pass,
    onChange: e => setPass(e.target.value),
    onKeyDown: e => {
      if (e.key === "Enter") submit();
    }
  }), m === "signup" && /*#__PURE__*/React.createElement("div", {
    className: "auth-fine"
  }, "At least 8 characters."), m === "login" && /*#__PURE__*/React.createElement("div", {
    className: "auth-forgot"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      setM("forgot");
      setErr("");
      setSent(false);
    }
  }, "Forgot password?"))), err && /*#__PURE__*/React.createElement("div", {
    className: "auth-err"
  }, err), !(m === "forgot" && sent) && /*#__PURE__*/React.createElement("button", {
    className: "auth-submit",
    onClick: submit,
    disabled: busy
  }, busy ? "…" : cta), /*#__PURE__*/React.createElement("div", {
    className: "auth-switch"
  }, m === "signup" && /*#__PURE__*/React.createElement(React.Fragment, null, "Already have an account? ", /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      setM("login");
      setErr("");
    }
  }, "Log in")), m === "login" && /*#__PURE__*/React.createElement(React.Fragment, null, "New here? ", /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      setM("signup");
      setErr("");
    }
  }, "Sign up")), m === "forgot" && /*#__PURE__*/React.createElement(React.Fragment, null, "Remembered it? ", /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      setM("login");
      setErr("");
      setSent(false);
    }
  }, "Back to log in")), m === "reset" && /*#__PURE__*/React.createElement(React.Fragment, null, "Changed your mind? ", /*#__PURE__*/React.createElement("button", {
    onClick: onClose
  }, "Cancel")))));
}

// ============================================================
// CROSS-REFERENCE PANEL
// ============================================================
function CrossRefPanel({
  source,
  onClose,
  onNavigate,
  isMobile,
  translation,
  onAiSearch,
  overviewBack,
  backLabel = "Overview",
  onOpenStudy
}) {
  const [refs, setRefs] = useState([]);
  const [synthesis, setSynthesis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [abpTexts, setAbpTexts] = useState({});
  const [studies, setStudies] = useState([]); // published concept studies that cite this verse
  const showAbp = translation === "abp" || translation === "parallel";
  useEffect(() => {
    if (!source) return;
    let cancelled = false;
    setRefs([]);
    setSynthesis(null);
    setAbpTexts({});
    setLoading(true);
    api.crossRefsCurated(source.book, source.chapter, source.verse).then(d => {
      if (cancelled) return;
      setRefs(d.refs || []);
      setSynthesis(d.synthesis || null);
      setLoading(false);
    }).catch(() => {
      if (!cancelled) setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [source && source.book, source && source.chapter, source && source.verse]);

  // Which published concept studies cite this verse (the "In studies:" line). Cheap, public.
  useEffect(() => {
    if (!source || !onOpenStudy) {
      setStudies([]);
      return;
    }
    let cancelled = false;
    setStudies([]);
    api.studyForVerse(source.book, source.chapter, source.verse).then(d => {
      if (!cancelled) setStudies(d && d.topics || []);
    }).catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [source && source.book, source && source.chapter, source && source.verse, !!onOpenStudy]);
  useEffect(() => {
    if (!showAbp || !refs.length) {
      setAbpTexts({});
      return;
    }
    let cancelled = false;
    Promise.all(refs.map(ref => api.verse(ref.book, ref.chapter, ref.verse).then(d => [ref.ref, d.text || ""]).catch(() => [ref.ref, ""]))).then(pairs => {
      if (!cancelled) setAbpTexts(Object.fromEntries(pairs));
    });
    return () => {
      cancelled = true;
    };
  }, [refs, showAbp]);
  const verseText = ref => showAbp ? abpTexts[ref.ref] || ref.kjv_text : ref.kjv_text;
  const sourceRef = `${source.book} ${source.chapter}:${source.verse}`;
  const heroRef = `${BOOK_LABELS[source.book] || source.book} ${source.chapter}:${source.verse}`;
  const {
    sheetRef,
    scrollRef
  } = useSwipeToDismiss(onClose);

  // Body shares the word-study / Reading-intro rail: a .detail-hero block (the
  // source reference + a passage count) then .sec/.sec-head sections — the AI
  // synthesis as "The connection" (Sonnet-written, so it carries the AI badge),
  // and the curated list as "Related passages".
  const content = /*#__PURE__*/React.createElement(React.Fragment, null, onOpenStudy && studies.length > 0 && /*#__PURE__*/React.createElement("section", {
    className: "sec"
  }, /*#__PURE__*/React.createElement("h4", {
    className: "sec-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "sec-t"
  }, "In studies")), /*#__PURE__*/React.createElement("div", {
    className: "xref-studies"
  }, studies.map(t => /*#__PURE__*/React.createElement("button", {
    key: t.id,
    className: "xref-study-link",
    onClick: () => {
      onClose();
      onOpenStudy(t.id);
    }
  }, t.title, " \u2192")))), (loading || synthesis) && /*#__PURE__*/React.createElement("section", {
    className: "sec"
  }, /*#__PURE__*/React.createElement("h4", {
    className: "sec-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "sec-t"
  }, "The connection"), /*#__PURE__*/React.createElement("span", {
    className: "lsj-badge lsj-badge--accent"
  }, "AI")), loading ? /*#__PURE__*/React.createElement("p", {
    className: "xref-synthesis-loading"
  }, "Selecting relevant passages\u2026") : /*#__PURE__*/React.createElement("p", {
    className: "detail-p"
  }, renderInlineMd(synthesis)), !loading && onAiSearch && /*#__PURE__*/React.createElement("button", {
    className: "xref-ai-btn",
    onClick: () => {
      onClose();
      onAiSearch(sourceRef);
    }
  }, "Explore in the corpus \u2192")), /*#__PURE__*/React.createElement("section", {
    className: "sec"
  }, /*#__PURE__*/React.createElement("h4", {
    className: "sec-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "sec-t"
  }, "Related passages"), /*#__PURE__*/React.createElement("span", {
    className: "lsj-badge"
  }, "TSK")), loading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-loading"
  }, "Loading\u2026") : refs.length === 0 ? /*#__PURE__*/React.createElement("p", {
    className: "detail-p"
  }, "No cross-references found.") : /*#__PURE__*/React.createElement("div", {
    className: "xref-list"
  }, refs.map(ref => /*#__PURE__*/React.createElement("div", {
    key: ref.ref,
    className: "xref-verse",
    onClick: () => onNavigate(ref.book, ref.chapter, ref.verse)
  }, /*#__PURE__*/React.createElement("span", {
    className: "xref-ref"
  }, ref.ref), /*#__PURE__*/React.createElement("p", {
    className: "xref-text"
  }, verseText(ref)))))));
  return /*#__PURE__*/React.createElement("aside", {
    ref: isMobile ? sheetRef : null,
    className: "xref-panel " + (isMobile ? "detail-sheet" : "detail-side"),
    role: "dialog",
    "aria-label": "Related Passages"
  }, isMobile && /*#__PURE__*/React.createElement("div", {
    className: "sheet-drag-zone",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet-handle"
  })), /*#__PURE__*/React.createElement("div", {
    className: "detail-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-head-l"
  }, /*#__PURE__*/React.createElement("span", {
    className: "detail-pos summary-pos"
  }, heroRef)), overviewBack && !isMobile ? /*#__PURE__*/React.createElement("button", {
    className: "detail-back",
    onClick: onClose,
    "aria-label": "Back to " + backLabel.toLowerCase()
  }, "\u2039 ", backLabel) : /*#__PURE__*/React.createElement("button", {
    className: "detail-close",
    onClick: onClose,
    "aria-label": "Close"
  }, /*#__PURE__*/React.createElement(Icon.Close, null))), /*#__PURE__*/React.createElement("div", {
    className: "detail-body",
    ref: isMobile ? scrollRef : null
  }, content));
}

// ============================================================
// SHARED VERSE ROW — used by both Search (CorpusGroup) and the Lexicon tab.
// Lazy-loads its own words; highlights any word whose Strong's is in citedStrongs.
// ============================================================
function VerseRow({
  book,
  chapter,
  verse,
  label,
  allResults,
  onWordClick,
  onReadInContext,
  textMode,
  primaryStrongs,
  citedStrongs,
  kjvCache
}) {
  const [words, setWords] = useState(null);
  const [kjvText, setKjvText] = useState(null);
  const [visible, setVisible] = useState(false);
  const rowRef = useRef(null);
  useEffect(() => {
    const el = rowRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true);
        obs.disconnect();
      }
    }, {
      rootMargin: "300px"
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  useEffect(() => {
    if (!visible) return;
    let cancelled = false;
    setWords(null);
    api.verseWords(book, chapter, verse).then(d => {
      if (!cancelled) setWords(d.words || []);
    }).catch(() => {
      if (!cancelled) setWords([]);
    });
    return () => {
      cancelled = true;
    };
  }, [visible, book, chapter, verse]);
  useEffect(() => {
    if (!visible || textMode !== "kjv") return;
    const cacheKey = `${book}:${chapter}:${verse}`;
    if (kjvCache && kjvCache[cacheKey]) {
      setKjvText(kjvCache[cacheKey]);
      return;
    }
    let cancelled = false;
    setKjvText(null);
    api.kjvVerseWords(book, chapter, verse).then(d => {
      if (!cancelled) setKjvText(Array.isArray(d) ? d : []);
    }).catch(() => {
      if (!cancelled) setKjvText([]);
    });
    return () => {
      cancelled = true;
    };
  }, [visible, book, chapter, verse, textMode, kjvCache]);

  // citedStrongs is passed in from App level; the matched word(s) are highlighted in
  // the prose below. No per-word entry map — clicking a word is the reader's job now.

  return /*#__PURE__*/React.createElement("div", {
    className: "corpus-verse",
    ref: rowRef
  }, /*#__PURE__*/React.createElement("button", {
    className: "corpus-ref",
    onClick: () => onReadInContext?.(book, chapter, verse)
  }, label), /*#__PURE__*/React.createElement("span", {
    className: "corpus-text"
  }, textMode === "kjv" ? kjvText === null ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-4)",
      fontSize: "13px"
    }
  }, "Loading\u2026") : kjvText.map((w, i) => {
    // Prose: plain readable text, the matched word gold-highlighted. No
    // per-word click — the reference jumps into the reader for word study.
    const sid = w.strongs_ids && w.strongs_ids.length ? w.strongs_ids[0] : null;
    const sidBare = sid ? sid.replace(/^[GH]/i, "") : null;
    const isCited = sid && citedStrongs != null && citedStrongs.size > 0 && (citedStrongs.has(sid) || citedStrongs.has(sidBare));
    const cls = (w.italic ? "lib-prose-italic " : "") + (isCited ? "corpus-hit" : "");
    // space OUTSIDE the span so a highlighted match hugs just the word
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: i
    }, /*#__PURE__*/React.createElement("span", {
      className: cls.trim() || undefined
    }, w.word, w.punc || ""), " ");
  }) : words === null ? /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--ink-4)",
      fontSize: "13px"
    }
  }, "Loading\u2026") : (() => {
    // Prose: readable english in reading order — identical to the reader's prose
    // mode (reuse LibRender.renderProseWords). The matched word(s) — those whose
    // Strong's is in citedStrongs — get the gold "corpus-hit" highlight via a
    // hiClass that lights up their position. No per-word click / brackets /
    // numbers; the reference button jumps into the reader to study any word.
    const citedPositions = new Set(citedStrongs && citedStrongs.size ? words.filter(w => citedStrongs.has(w.strongs_base) || citedStrongs.has(strongsBare(w.strongs_base))).map(w => w.position) : []);
    const proseCtx = {
      selChapter: chapter,
      hiClass: (vs, pos) => citedPositions.has(pos) ? " corpus-hit" : ""
    };
    return LibRender.renderProseWords(proseCtx, {
      verse,
      words,
      _ch: chapter
    }, {
      tightSpace: true
    });
  })()));
}

// ============================================================
// CORPUS SEARCH — PASSAGE GROUP (collapsible book+chapter section)
// ============================================================
function CorpusGroup({
  label,
  verses,
  allResults,
  onWordClick,
  onReadInContext,
  textMode,
  primaryStrongs,
  citedStrongs,
  kjvCache
}) {
  const [open, setOpen] = useState(true);
  return /*#__PURE__*/React.createElement("div", {
    className: "corpus-group"
  }, /*#__PURE__*/React.createElement("button", {
    className: "corpus-group-head " + (open ? "open" : ""),
    onClick: () => setOpen(o => !o)
  }, /*#__PURE__*/React.createElement(Icon.Book, {
    style: {
      opacity: 0.5,
      flexShrink: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "corpus-group-label"
  }, label), /*#__PURE__*/React.createElement("span", {
    className: "corpus-group-count"
  }, verses.length, " verse", verses.length !== 1 ? "s" : ""), /*#__PURE__*/React.createElement("span", {
    className: "corpus-chevron " + (open ? "open" : "")
  })), open && /*#__PURE__*/React.createElement("div", {
    className: "corpus-group-body"
  }, verses.map(v => /*#__PURE__*/React.createElement(VerseRow, {
    key: `${v.book}-${v.chapter}-${v.verse}`,
    book: v.book,
    chapter: v.chapter,
    verse: v.verse,
    label: v.ref,
    allResults: allResults,
    onWordClick: onWordClick,
    onReadInContext: onReadInContext,
    textMode: textMode,
    primaryStrongs: primaryStrongs,
    citedStrongs: citedStrongs,
    kjvCache: kjvCache
  }))));
}

// ============================================================
// CORPUS SEARCH — OUTER CONTAINER
// ============================================================
function CorpusResults({
  allResults,
  primaryStrongs,
  citedStrongs,
  showAll,
  onWordClick,
  onReadInContext,
  corpusSort,
  textMode
}) {
  const [kjvCache, setKjvCache] = useState({}); // pre-fetched KJV verse words

  // Pre-fetch all KJV verse words in one batch when switching to KJV mode
  React.useEffect(() => {
    if (textMode !== "kjv" || !allResults.length) return;
    const seen = new Set();
    const refs = [];
    for (const e of allResults) {
      const key = `${e.book}:${e.chapter}:${e.verse}`;
      if (!seen.has(key)) {
        seen.add(key);
        refs.push({
          book: e.book,
          chapter: e.chapter,
          verse: e.verse
        });
      }
    }
    if (!refs.length) return;
    let cancelled = false;
    api.kjvVerseWordsBatch(refs).then(data => {
      if (!cancelled) setKjvCache(data);
    }).catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [textMode, allResults]);
  const groups = useMemo(() => {
    const gMap = {};
    const gOrder = [];
    for (const entry of allResults) {
      const gk = `${entry.book}-${entry.chapter}`;
      if (!gMap[gk]) {
        gMap[gk] = {
          label: `${BOOK_LABELS[entry.book] || entry.book} · Chapter ${entry.chapter}`,
          verseMap: {},
          verseOrder: []
        };
        gOrder.push(gk);
      }
      const vk = `${entry.book}-${entry.chapter}-${entry.verse}`;
      if (!gMap[gk].verseMap[vk]) {
        gMap[gk].verseMap[vk] = {
          book: entry.book,
          chapter: entry.chapter,
          verse: entry.verse,
          ref: entry.ref,
          is_primary: entry.is_primary,
          is_additional: entry.is_additional
        };
        gMap[gk].verseOrder.push(vk);
      }
    }
    return gOrder.map(gk => ({
      label: gMap[gk].label,
      verses: gMap[gk].verseOrder.map(vk => gMap[gk].verseMap[vk])
    })).sort((a, b) => {
      if (corpusSort === "canonical") {
        const bookDiff = (BOOK_ORDER[a.verses[0]?.book] ?? 99) - (BOOK_ORDER[b.verses[0]?.book] ?? 99);
        return bookDiff || (a.verses[0]?.chapter ?? 0) - (b.verses[0]?.chapter ?? 0);
      }
      const aPrimary = a.verses.filter(v => v.is_primary).length;
      const bPrimary = b.verses.filter(v => v.is_primary).length;
      return bPrimary - aPrimary || b.verses.length - a.verses.length;
    });
  }, [allResults, corpusSort]);
  const hasPrimary = allResults.some(e => e.is_primary);
  const hasAdditional = allResults.some(e => e.is_additional);
  const primaryGroups = hasPrimary ? groups.map(g => ({
    ...g,
    verses: g.verses.filter(v => v.is_primary)
  })).filter(g => g.verses.length > 0) : groups;
  const additionalGroups = hasAdditional ? groups.map(g => ({
    ...g,
    verses: g.verses.filter(v => v.is_additional)
  })).filter(g => g.verses.length > 0) : [];
  const otherGroups = hasPrimary || hasAdditional ? groups.map(g => ({
    ...g,
    verses: g.verses.filter(v => !v.is_primary && !v.is_additional)
  })).filter(g => g.verses.length > 0) : [];
  const passageGroupProps = {
    allResults,
    onWordClick,
    onReadInContext,
    textMode,
    primaryStrongs,
    citedStrongs,
    kjvCache
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "corpus-groups"
  }, primaryGroups.map(g => /*#__PURE__*/React.createElement(CorpusGroup, _extends({
    key: g.label,
    label: g.label,
    verses: g.verses
  }, passageGroupProps))), additionalGroups.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "additional-refs-section"
  }, /*#__PURE__*/React.createElement("div", {
    className: "additional-refs-label"
  }, "Additional references"), additionalGroups.map(g => /*#__PURE__*/React.createElement(CorpusGroup, _extends({
    key: g.label,
    label: g.label,
    verses: g.verses
  }, passageGroupProps)))), showAll && otherGroups.map(g => /*#__PURE__*/React.createElement(CorpusGroup, _extends({
    key: g.label,
    label: g.label,
    verses: g.verses
  }, passageGroupProps))));
}

// ============================================================
// STUDY MODULES
// One Study tab with a sub-switch: Topics · Graphs.
//   Topics — a BROWSE: a subject broken into subtopic SECTIONS, each with its verses
//            (mostly filled from MetaV; light editing). PUBLIC when published. Shape:
//            {title, intro, sections:[{heading, verses:[{ref,text}]}]}.
//   Graphs — an ARGUMENT MAP (admin-only): a pool of CLAIMS joined by per-tradition
//            LINKS, each claim tagged with provenance + each link with strength, so the
//            conclusion can be stress-tested (see argmap.py). Read-only here; authored
//            with scripts/add_study_graph.py.
// Backend: views_study.py (study.db). Graph routes are admin-gated (404 otherwise).
// ============================================================
const STUDY_MODULES = [{
  id: "topic",
  label: "Topics"
}, {
  id: "graph",
  label: "Graphs"
}];
// "name" = a person/place name-topic (MetaV), shown on the metaV sidebar, opened
// here read-only. Same shape as a topic, so it renders through TopicPage.
const isTopicLike = t => t === "topic" || t === "name";
// Subtopic headings arrive from Nave's as little sentences ("Father.") — drop a
// trailing period/comma so they read as headings, not sentences.
const cleanHeading = h => String(h || "").replace(/\s*[.,;:]+\s*$/, "");
// Split "Leviticus 10:8" -> book "Leviticus" + short ref "10:8", so a section's verses
// can be grouped (and collapsed) under book headers.
const _REF_SPLIT = /^(.*?)\s+(\d+:\d+(?:[-–—]\d+(?::\d+)?)?)\s*$/;
const bookOf = ref => {
  const m = _REF_SPLIT.exec(String(ref || ""));
  return m ? m[1] : String(ref || "");
};
const shortRef = ref => {
  const m = _REF_SPLIT.exec(String(ref || ""));
  return m ? m[2] : String(ref || "");
};
function groupByBook(verses) {
  const groups = [];
  (verses || []).forEach(v => {
    const book = bookOf(v.ref);
    const last = groups[groups.length - 1];
    if (last && last.book === book) last.verses.push(v);else groups.push({
      book,
      verses: [v]
    });
  });
  return groups;
}
// A verse reference inside a READ view. When the verse carries book/chapter/verse (the
// server resolves them) and a nav handler is present, it's a button that jumps into the
// Library reader — same idea as a Search/Lexicon result reference. Otherwise a plain pill.
function StudyRef({
  v,
  label,
  onNavigate
}) {
  const go = onNavigate && v && v.book && v.chapter && v.verse;
  if (!go) return /*#__PURE__*/React.createElement("span", {
    className: "study-verse-ref"
  }, label);
  return /*#__PURE__*/React.createElement("button", {
    className: "study-verse-ref study-verse-ref--link",
    title: "Open in the reader",
    onClick: () => onNavigate(v.book, v.chapter, v.verse)
  }, label);
}
// Nave's titles are index-style — keyword first: "Accusation, False", "Trinity, The".
// Flip the SAFE ones to read naturally ("False Accusation", "The Trinity"); leave
// ambiguous multi-word tails alone (e.g. "God, the Father" shouldn't become "the
// Father God"). Display only — the stored title is untouched.
const _TITLE_STOP = new Set(["the", "a", "an", "of", "and", "or", "to", "in", "on", "for"]);
function displayTitle(t) {
  t = String(t || "").trim();
  const ci = t.indexOf(",");
  if (ci < 0 || t.indexOf(",", ci + 1) >= 0) return t; // no comma, or more than one -> leave
  const head = t.slice(0, ci).trim();
  const tail = t.slice(ci + 1).trim();
  if (!head || !tail) return t;
  if (tail.toLowerCase() === "the") return "The " + head;
  const words = tail.split(/\s+/);
  if (words.length === 1 && !_TITLE_STOP.has(tail.toLowerCase())) return tail.charAt(0).toUpperCase() + tail.slice(1) + " " + head;
  return t;
}
function blankTopic() {
  return {
    id: "",
    type: "topic",
    title: "",
    intro: "",
    sections: [{
      heading: "",
      verses: []
    }],
    related: [],
    status: "draft",
    source: ""
  };
}
function moveItem(arr, i, dir) {
  const j = i + dir;
  if (j < 0 || j >= arr.length) return arr;
  const a = arr.slice();
  const t = a[i];
  a[i] = a[j];
  a[j] = t;
  return a;
}

// Add a reference: resolves it to ABP prose, then hands {ref, text} up.
function AddRef({
  onAdd,
  placeholder
}) {
  const [ref, setRef] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const add = () => {
    const r = ref.trim();
    if (!r || busy) return;
    setBusy(true);
    setErr("");
    api.studyVerse(r).then(d => {
      setBusy(false);
      if (d && d.verses && d.verses.length) {
        onAdd({
          ref: d.canonical || r,
          text: d.verses.map(v => v.text).join(" ")
        });
        setRef("");
      } else {
        setErr(d && d.error || "Couldn't find that reference.");
      }
    });
  };
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "study-add-row"
  }, /*#__PURE__*/React.createElement("input", {
    className: "study-add-input",
    type: "text",
    value: ref,
    placeholder: placeholder || "Add a reference — e.g. Romans 10:17 (text fills in)",
    onChange: e => {
      setRef(e.target.value);
      if (err) setErr("");
    },
    onKeyDown: e => {
      if (e.key === "Enter") {
        e.preventDefault();
        add();
      }
    }
  }), /*#__PURE__*/React.createElement("button", {
    className: "study-add-btn",
    onClick: add,
    disabled: busy || !ref.trim()
  }, busy ? "…" : "Add")), err && /*#__PURE__*/React.createElement("div", {
    className: "study-add-err"
  }, err));
}

// Editable verse list (with remove).
function VerseRows({
  items,
  onRemove
}) {
  if (!items.length) return null;
  return /*#__PURE__*/React.createElement("div", {
    className: "study-verse-list"
  }, items.map((it, i) => /*#__PURE__*/React.createElement("div", {
    className: "study-verse-row",
    key: i
  }, /*#__PURE__*/React.createElement("span", {
    className: "study-verse-ref"
  }, it.ref), /*#__PURE__*/React.createElement("span", {
    className: "study-verse-text"
  }, it.text || /*#__PURE__*/React.createElement("em", {
    className: "study-verse-missing"
  }, "not found \u2014 saved as a reference")), /*#__PURE__*/React.createElement("button", {
    className: "study-x",
    onClick: () => onRemove(i),
    "aria-label": "Remove verse",
    title: "Remove"
  }, "\xD7"))));
}

// ---- Topics ---------------------------------------------------------------
function TopicSectionEdit({
  section,
  idx,
  count,
  onChange,
  onRemove,
  onMove
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "study-section study-section--edit"
  }, /*#__PURE__*/React.createElement("div", {
    className: "study-section-bar"
  }, /*#__PURE__*/React.createElement("input", {
    className: "study-section-head-input",
    type: "text",
    value: section.heading,
    placeholder: "Section heading (optional)",
    onChange: e => onChange({
      ...section,
      heading: e.target.value
    })
  }), /*#__PURE__*/React.createElement("div", {
    className: "study-section-tools"
  }, /*#__PURE__*/React.createElement("button", {
    className: "study-sec-tool",
    disabled: idx === 0,
    onClick: () => onMove(-1),
    "aria-label": "Move up",
    title: "Move up"
  }, "\u2191"), /*#__PURE__*/React.createElement("button", {
    className: "study-sec-tool",
    disabled: idx === count - 1,
    onClick: () => onMove(1),
    "aria-label": "Move down",
    title: "Move down"
  }, "\u2193"), /*#__PURE__*/React.createElement("button", {
    className: "study-sec-tool study-sec-tool--del",
    onClick: onRemove,
    "aria-label": "Remove section",
    title: "Remove section"
  }, "\u2715"))), /*#__PURE__*/React.createElement(VerseRows, {
    items: section.verses,
    onRemove: i => onChange({
      ...section,
      verses: section.verses.filter((_, j) => j !== i)
    })
  }), /*#__PURE__*/React.createElement(AddRef, {
    onAdd: v => onChange({
      ...section,
      verses: [...section.verses, v]
    }),
    placeholder: "Add a reference to this section"
  }));
}

// Which subtopic sections start open on the read page: a 1-section topic opens; a
// multi-section topic starts collapsed (you see the structure first, expand on demand).
function defaultOpenSecs(entry) {
  const secs = entry && entry.sections || [];
  return new Set(secs.length <= 1 ? secs.map((_, i) => i) : []);
}
function TopicPage({
  entry,
  editing,
  onChange,
  onSave,
  onDelete,
  onClose,
  onToggleEdit,
  previewReader,
  saving,
  savedAt,
  onNavigate
}) {
  const up = patch => onChange({
    ...entry,
    ...patch
  });
  const verseCount = entry.sections.reduce((n, s) => n + s.verses.length, 0);
  const [drafting, setDrafting] = useState(false);
  const [draftErr, setDraftErr] = useState(false);
  const draftIntro = () => {
    if (drafting) return;
    setDrafting(true);
    setDraftErr(false);
    const slim = (entry.sections || []).map(s => ({
      heading: s.heading,
      verses: (s.verses || []).slice(0, 2).map(v => ({
        ref: v.ref,
        text: v.text
      }))
    }));
    api.studyDraftIntro({
      title: entry.title,
      sections: slim
    }).then(d => {
      setDrafting(false);
      if (d && d.intro) up({
        intro: d.intro
      });else setDraftErr(true);
    });
  };
  const [openSecs, setOpenSecs] = useState(() => defaultOpenSecs(entry));
  useEffect(() => {
    setOpenSecs(defaultOpenSecs(entry));
  }, [entry.id]);
  const allOpen = entry.sections.length > 0 && openSecs.size === entry.sections.length;
  const toggleAll = () => setOpenSecs(allOpen ? new Set() : new Set(entry.sections.map((_, i) => i)));
  const toggleSec = i => setOpenSecs(prev => {
    const n = new Set(prev);
    n.has(i) ? n.delete(i) : n.add(i);
    return n;
  });
  const [closedBooks, setClosedBooks] = useState(() => new Set()); // big sections group verses by book; this tracks collapsed books
  useEffect(() => {
    setClosedBooks(new Set());
  }, [entry.id]);
  const toggleBook = key => setClosedBooks(prev => {
    const n = new Set(prev);
    n.has(key) ? n.delete(key) : n.add(key);
    return n;
  });
  if (!editing) {
    return /*#__PURE__*/React.createElement("div", {
      className: "study-topic"
    }, /*#__PURE__*/React.createElement("div", {
      className: "study-editor-bar"
    }, /*#__PURE__*/React.createElement("button", {
      className: "study-back",
      onClick: onClose
    }, "\u2039 ", previewReader ? "Back" : "All topics"), !previewReader && /*#__PURE__*/React.createElement("button", {
      className: "study-edit-btn",
      onClick: onToggleEdit
    }, "Edit")), /*#__PURE__*/React.createElement("div", {
      className: "study-eyebrow"
    }, "Topic"), /*#__PURE__*/React.createElement("h1", {
      className: "study-topic-title"
    }, displayTitle(entry.title)), /*#__PURE__*/React.createElement("div", {
      className: "study-topic-meta"
    }, entry.source === "metav" ? "from Nave's · " : "", entry.sections.length, " sections \xB7 ", verseCount, " verses"), entry.intro && /*#__PURE__*/React.createElement("p", {
      className: "study-topic-intro"
    }, entry.intro), entry.sections.length === 0 ? /*#__PURE__*/React.createElement("div", {
      className: "stats-empty"
    }, "No verses yet \u2014 click Edit to add some.") : /*#__PURE__*/React.createElement(React.Fragment, null, entry.sections.length > 1 && /*#__PURE__*/React.createElement("button", {
      className: "study-collapse-all",
      onClick: toggleAll
    }, allOpen ? "Collapse all" : "Expand all"), entry.sections.map((s, i) => {
      const isOpen = openSecs.has(i);
      return /*#__PURE__*/React.createElement("div", {
        className: "study-section study-section--collapsible" + (isOpen ? " open" : ""),
        key: i
      }, /*#__PURE__*/React.createElement("button", {
        className: "study-section-toggle",
        onClick: () => toggleSec(i),
        "aria-expanded": isOpen
      }, /*#__PURE__*/React.createElement("span", {
        className: "study-section-chevron"
      }, isOpen ? "▾" : "▸"), /*#__PURE__*/React.createElement("span", {
        className: "study-section-head-text"
      }, cleanHeading(s.heading) || "General references"), /*#__PURE__*/React.createElement("span", {
        className: "study-section-count"
      }, s.verses.length)), isOpen && (s.verses.length > 4 ? /*#__PURE__*/React.createElement("div", {
        className: "study-books"
      }, groupByBook(s.verses).map((g, gi) => {
        const bkey = i + "|" + gi + "|" + g.book;
        const bopen = !closedBooks.has(bkey);
        return /*#__PURE__*/React.createElement("div", {
          className: "study-book",
          key: gi
        }, /*#__PURE__*/React.createElement("button", {
          className: "study-book-toggle",
          onClick: () => toggleBook(bkey),
          "aria-expanded": bopen
        }, /*#__PURE__*/React.createElement("span", {
          className: "study-book-chevron"
        }, bopen ? "▾" : "▸"), /*#__PURE__*/React.createElement("span", {
          className: "study-book-name"
        }, g.book), /*#__PURE__*/React.createElement("span", {
          className: "study-book-count"
        }, g.verses.length)), bopen && /*#__PURE__*/React.createElement("div", {
          className: "study-book-verses"
        }, g.verses.map((v, j) => /*#__PURE__*/React.createElement("div", {
          className: "study-read-verse",
          key: j
        }, /*#__PURE__*/React.createElement(StudyRef, {
          v: v,
          label: shortRef(v.ref),
          onNavigate: onNavigate
        }), /*#__PURE__*/React.createElement("span", {
          className: "study-read-text"
        }, v.text || /*#__PURE__*/React.createElement("em", {
          className: "study-verse-missing"
        }, "(text not found)"))))));
      })) : /*#__PURE__*/React.createElement("div", {
        className: "study-read-verses"
      }, s.verses.map((v, j) => /*#__PURE__*/React.createElement("div", {
        className: "study-read-verse",
        key: j
      }, /*#__PURE__*/React.createElement(StudyRef, {
        v: v,
        label: v.ref,
        onNavigate: onNavigate
      }), /*#__PURE__*/React.createElement("span", {
        className: "study-read-text"
      }, v.text || /*#__PURE__*/React.createElement("em", {
        className: "study-verse-missing"
      }, "(text not found)")))))));
    })));
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "study-editor"
  }, /*#__PURE__*/React.createElement("div", {
    className: "study-editor-bar"
  }, /*#__PURE__*/React.createElement("button", {
    className: "study-back",
    onClick: () => entry.id ? onToggleEdit() : onClose()
  }, "\u2039 ", entry.id ? "Done editing" : "Cancel"), /*#__PURE__*/React.createElement("div", {
    className: "study-editor-actions"
  }, savedAt && !saving && /*#__PURE__*/React.createElement("span", {
    className: "study-saved"
  }, "Saved \u2713"), entry.id && /*#__PURE__*/React.createElement("button", {
    className: "study-del",
    onClick: onDelete
  }, "Delete"), /*#__PURE__*/React.createElement("button", {
    className: "study-save",
    onClick: onSave,
    disabled: saving || !entry.title.trim()
  }, saving ? "Saving…" : "Save"))), /*#__PURE__*/React.createElement("div", {
    className: "study-field"
  }, /*#__PURE__*/React.createElement("label", {
    className: "study-label"
  }, "Topic"), /*#__PURE__*/React.createElement("input", {
    className: "study-input",
    type: "text",
    value: entry.title,
    placeholder: "Subject \u2014 e.g. Faith",
    onChange: e => up({
      title: e.target.value
    })
  })), /*#__PURE__*/React.createElement("div", {
    className: "study-field"
  }, /*#__PURE__*/React.createElement("label", {
    className: "study-label"
  }, "Intro ", /*#__PURE__*/React.createElement("span", {
    className: "study-label-hint"
  }, "(optional)"), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "study-ai-btn",
    disabled: drafting || !entry.title.trim(),
    onClick: draftIntro
  }, drafting ? "Drafting…" : "✦ Draft with AI"), draftErr && /*#__PURE__*/React.createElement("span", {
    className: "study-ai-err"
  }, "couldn't draft \u2014 try again")), /*#__PURE__*/React.createElement("textarea", {
    className: "study-textarea study-textarea--sm",
    value: entry.intro,
    placeholder: "A short, plain-English lead-in (or use Draft with AI).",
    onChange: e => up({
      intro: e.target.value
    })
  })), entry.sections.map((s, i) => /*#__PURE__*/React.createElement(TopicSectionEdit, {
    key: i,
    section: s,
    idx: i,
    count: entry.sections.length,
    onChange: ns => up({
      sections: entry.sections.map((x, j) => j === i ? ns : x)
    }),
    onRemove: () => up({
      sections: entry.sections.filter((_, j) => j !== i)
    }),
    onMove: dir => up({
      sections: moveItem(entry.sections, i, dir)
    })
  })), /*#__PURE__*/React.createElement("button", {
    className: "study-add-section",
    onClick: () => up({
      sections: [...entry.sections, {
        heading: "",
        verses: []
      }]
    })
  }, "+ Add section"), /*#__PURE__*/React.createElement("div", {
    className: "study-field study-status-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "study-label"
  }, "Visibility"), /*#__PURE__*/React.createElement("div", {
    className: "seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (entry.status === "draft" ? " on" : ""),
    onClick: () => up({
      status: "draft"
    })
  }, "Draft"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (entry.status === "published" ? " on" : ""),
    onClick: () => up({
      status: "published"
    })
  }, "Published")), /*#__PURE__*/React.createElement("span", {
    className: "study-label-hint"
  }, "Draft = only you. Published = visible to everyone.")));
}

// ---- Graph (argument map) -------------------------------------------------
// Provenance says whether a claim stands on the source: text/lexicon = grounded (navy),
// everything else leans on something added (amber). A conclusion gets no badge.
const PROV_GROUNDED = new Set(["text", "lexicon"]);
const PROV_LABEL = {
  text: "Text",
  lexicon: "Lexicon",
  tradition: "Tradition",
  conjecture: "Conjecture",
  inference: "Inference",
  observation: "Observation",
  conclusion: ""
};
function ProvBadge({
  prov
}) {
  const label = PROV_LABEL[prov] != null ? PROV_LABEL[prov] : prov;
  if (!label) return null;
  return /*#__PURE__*/React.createElement("span", {
    className: "study-prov " + (PROV_GROUNDED.has(prov) ? "study-prov--grounded" : "study-prov--added")
  }, label);
}

// One claim, compact: its statement + provenance badge, and (for a verse claim) a
// reference button that jumps into the reader plus the verse text.
function ClaimChip({
  claim,
  onNavigate
}) {
  if (!claim) return /*#__PURE__*/React.createElement("div", {
    className: "study-claim study-claim--missing"
  }, "(missing claim)");
  return /*#__PURE__*/React.createElement("div", {
    className: "study-claim" + (PROV_GROUNDED.has(claim.provenance) ? " study-claim--grounded" : "")
  }, /*#__PURE__*/React.createElement("div", {
    className: "study-claim-head"
  }, /*#__PURE__*/React.createElement(ProvBadge, {
    prov: claim.provenance
  }), claim.ref && /*#__PURE__*/React.createElement(StudyRef, {
    v: claim,
    label: claim.ref,
    onNavigate: onNavigate
  })), /*#__PURE__*/React.createElement("div", {
    className: "study-claim-text"
  }, claim.text), claim.ref && claim.verse_text && /*#__PURE__*/React.createElement("div", {
    className: "study-claim-verse"
  }, claim.verse_text));
}
const linkKey = l => l.from + "→" + l.to + "·" + l.relation;

// ---- The chart (per-overlay SVG: verses converge into claims into the thesis) ----
const CH = {
  W: 176,
  H: 58,
  COLGAP: 232,
  ROWGAP: 94,
  PAD: 18
};
const shortLabel = c => c && (c.label || c.ref) || (c && c.text ? c.text.length > 32 ? c.text.slice(0, 30) + "…" : c.text : "");

// Longest-path column for each node from the grounded verses (verses = column 0).
function chartColumns(claims, carry, ids) {
  const isVerse = id => PROV_GROUNDED.has((claims[id] || {}).provenance);
  const preds = {};
  carry.forEach(l => {
    (preds[l.to] = preds[l.to] || []).push(l.from);
  });
  const col = {},
    busy = {};
  const walk = id => {
    if (id in col) return col[id];
    if (busy[id]) return 0; // cycle guard
    busy[id] = true;
    const c = !isVerse(id) && preds[id] ? 1 + Math.max(...preds[id].map(walk)) : 0;
    busy[id] = false;
    return col[id] = c;
  };
  ids.forEach(walk);
  return col;
}

// One overlay drawn left-to-right. Shared verses are pinned to the top rows in the same
// order on every overlay, so flipping traditions holds them in place while the arrows and
// the conclusion change — the verse back-reference, made visual.
function GraphSvg({
  claims,
  overlay,
  verdict,
  shared,
  onNavigate
}) {
  const carry = (overlay.links || []).filter(l => l.relation !== "undercuts");
  const ids = [],
    seen = new Set();
  const add = id => {
    if (id && !seen.has(id)) {
      seen.add(id);
      ids.push(id);
    }
  };
  carry.forEach(l => {
    add(l.from);
    add(l.to);
  });
  add(overlay.thesis);
  const col = chartColumns(claims, carry, ids);
  let maxCol = Math.max(0, ...ids.map(id => col[id] || 0));
  if (overlay.thesis && !carry.some(l => l.to === overlay.thesis)) {
    col[overlay.thesis] = maxCol + 1; // gap: nothing points at the conclusion — float it out alone, with a visible space before it
    maxCol += 1;
  }
  const byCol = {};
  ids.forEach(id => {
    (byCol[col[id]] = byCol[col[id]] || []).push(id);
  });
  if (byCol[0]) {
    // pin shared verses to the top rows
    const rank = id => {
      const i = shared.indexOf(id);
      return i < 0 ? 1e6 : i;
    };
    byCol[0].sort((a, b) => rank(a) - rank(b));
  }
  // y: column 0 on a fixed row grid (shared pinned); each later column centers a node on the
  // verses/claims that feed it (barycenter), then nudges siblings apart so boxes don't overlap.
  // This keeps feeders grouped under their target, so the support lines stop crossing.
  const preds = {};
  carry.forEach(l => {
    (preds[l.to] = preds[l.to] || []).push(l.from);
  });
  const yy = {};
  (byCol[0] || []).forEach((id, r) => {
    yy[id] = r * CH.ROWGAP;
  });
  const mid = Math.max(0, (byCol[0] || []).length - 1) / 2 * CH.ROWGAP;
  Object.keys(byCol).map(Number).sort((a, b) => a - b).forEach(c => {
    if (c === 0) return;
    byCol[c].forEach(id => {
      const ps = (preds[id] || []).filter(p => p in yy);
      yy[id] = ps.length ? ps.reduce((s, p) => s + yy[p], 0) / ps.length : mid;
    });
    byCol[c].sort((a, b) => yy[a] - yy[b]);
    for (let k = 1; k < byCol[c].length; k++) {
      const a = byCol[c][k - 1],
        b = byCol[c][k];
      if (yy[b] - yy[a] < CH.ROWGAP) yy[b] = yy[a] + CH.ROWGAP;
    }
  });
  const pos = {};
  ids.forEach(id => {
    pos[id] = {
      c: col[id],
      y: yy[id] || 0
    };
  });
  const maxY = Math.max(0, ...ids.map(id => pos[id].y));
  const W = CH.PAD * 2 + maxCol * CH.COLGAP + CH.W;
  const H = CH.PAD * 2 + maxY + CH.H;
  const X = id => CH.PAD + pos[id].c * CH.COLGAP;
  const Y = id => CH.PAD + pos[id].y;
  const joints = new Set((verdict && verdict.load_bearing || []).map(linkKey));
  const edgeKind = l => joints.has(linkKey(l)) ? "joint" : l.strength === "solid" ? "solid" : "soft";
  const nodeKind = id => {
    const p = (claims[id] || {}).provenance;
    return p === "conclusion" ? "concl" : PROV_GROUNDED.has(p) ? "verse" : "added";
  };
  return /*#__PURE__*/React.createElement("svg", {
    className: "study-svg",
    viewBox: "0 0 " + W + " " + H,
    width: W,
    height: H,
    role: "img"
  }, /*#__PURE__*/React.createElement("defs", null, ["solid", "soft", "joint"].map(k => /*#__PURE__*/React.createElement("marker", {
    key: k,
    id: "ah-" + k,
    className: "study-arrow study-arrow--" + k,
    markerWidth: "9",
    markerHeight: "9",
    refX: "7",
    refY: "3",
    orient: "auto",
    markerUnits: "userSpaceOnUse"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M0,0 L7,3 L0,6 Z"
  })))), carry.map((l, i) => {
    if (!pos[l.from] || !pos[l.to]) return null;
    const k = edgeKind(l);
    const x1 = X(l.from) + CH.W,
      y1 = Y(l.from) + CH.H / 2;
    const x2 = X(l.to),
      y2 = Y(l.to) + CH.H / 2,
      mx = (x1 + x2) / 2;
    return /*#__PURE__*/React.createElement("path", {
      key: i,
      className: "study-edge study-edge--" + k,
      d: "M" + x1 + "," + y1 + " C" + mx + "," + y1 + " " + mx + "," + y2 + " " + (x2 - 8) + "," + y2,
      markerEnd: "url(#ah-" + k + ")"
    });
  }), ids.map(id => {
    const c = claims[id] || {};
    const k = nodeKind(id);
    const go = onNavigate && c.book && c.chapter && c.verse;
    return /*#__PURE__*/React.createElement("g", {
      key: id,
      transform: "translate(" + X(id) + "," + Y(id) + ")",
      className: "study-node study-node--" + k + (go ? " study-node--link" : ""),
      onClick: go ? () => onNavigate(c.book, c.chapter, c.verse) : undefined
    }, /*#__PURE__*/React.createElement("title", null, c.text || id), /*#__PURE__*/React.createElement("rect", {
      width: CH.W,
      height: CH.H,
      rx: "9"
    }), /*#__PURE__*/React.createElement("text", {
      className: "study-node-t1",
      x: CH.W / 2,
      y: k === "verse" ? 24 : 34,
      textAnchor: "middle"
    }, c.ref || shortLabel(c)), k === "verse" && /*#__PURE__*/React.createElement("text", {
      className: "study-node-t2",
      x: CH.W / 2,
      y: 40,
      textAnchor: "middle"
    }, c.label || ""));
  }));
}

// Tabs to flip traditions, the SVG, a legend, and — for the selected side — the verdict,
// why each non-solid link is rated as it is, and the open objections.
function GraphChart({
  claims,
  overlays,
  analysis,
  onNavigate
}) {
  const [sel, setSel] = useState(0);
  if (!overlays.length) return null;
  const i = Math.min(sel, overlays.length - 1);
  const overlay = overlays[i];
  const verdict = (analysis.verdicts || [])[i] || {
    grounded: false,
    gap: false,
    load_bearing: []
  };
  const shared = (analysis.diff || {}).shared_verses || [];
  const cls = verdict.grounded ? "stands" : verdict.gap ? "gap" : "depends";
  const label = verdict.grounded ? "Stands on the text" : verdict.gap ? "Incomplete — a step is missing" : verdict.load_bearing && verdict.load_bearing.length ? "Depends on a non-solid joint" : "Depends on contested steps";
  const why = (overlay.links || []).filter(l => l.relation !== "undercuts" && l.strength !== "solid" && l.why);
  const objections = (overlay.links || []).filter(l => l.relation === "undercuts");
  return /*#__PURE__*/React.createElement("div", {
    className: "study-chart"
  }, /*#__PURE__*/React.createElement("div", {
    className: "study-chart-tabs"
  }, overlays.map((ov, j) => /*#__PURE__*/React.createElement("button", {
    key: j,
    className: "study-chart-tab" + (j === i ? " on" : ""),
    onClick: () => setSel(j)
  }, ov.tradition))), /*#__PURE__*/React.createElement("div", {
    className: "study-verdict study-verdict--" + cls
  }, label), /*#__PURE__*/React.createElement("div", {
    className: "study-chart-scroll"
  }, /*#__PURE__*/React.createElement(GraphSvg, {
    claims: claims,
    overlay: overlay,
    verdict: verdict,
    shared: shared,
    onNavigate: onNavigate
  })), /*#__PURE__*/React.createElement("div", {
    className: "study-chart-legend"
  }, /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("i", {
    className: "study-key study-key--verse"
  }), " verse (grounded)"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("i", {
    className: "study-key study-key--added"
  }), " inference / tradition"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("i", {
    className: "study-key study-key--concl"
  }), " conclusion"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("i", {
    className: "study-key-line study-key-line--solid"
  }), " established"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("i", {
    className: "study-key-line study-key-line--soft"
  }), " contested"), /*#__PURE__*/React.createElement("span", null, /*#__PURE__*/React.createElement("i", {
    className: "study-key-line study-key-line--joint"
  }), " load-bearing joint")), why.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "study-chart-why"
  }, /*#__PURE__*/React.createElement("div", {
    className: "study-objections-label"
  }, "Why the dashed links are rated that way"), why.map((l, j) => /*#__PURE__*/React.createElement("div", {
    className: "study-link-why",
    key: j
  }, /*#__PURE__*/React.createElement("b", null, shortLabel(claims[l.from]), " \u2192 ", shortLabel(claims[l.to])), " (", l.strength, "): ", l.why, /*#__PURE__*/React.createElement("span", {
    className: "study-link-by"
  }, " \u2014 ", overlay.tradition, "'s call")))), objections.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "study-objections"
  }, /*#__PURE__*/React.createElement("div", {
    className: "study-objections-label"
  }, "Open objections (noted, not scored)"), objections.map((l, j) => /*#__PURE__*/React.createElement("div", {
    className: "study-objection",
    key: j
  }, l.why || (claims[l.from] || {}).text + " — attacks the conclusion"))));
}

// Read-only argument-map page (the in-app editor + React Flow canvas come in a later cut).
function GraphPage({
  entry,
  onClose,
  previewReader,
  onNavigate
}) {
  const claims = entry.claims || {};
  const overlays = entry.overlays || [];
  const analysis = entry.analysis || {
    verdicts: [],
    diff: {}
  };
  const diff = analysis.diff || {};
  const sharedVerses = diff.shared_verses || [];
  const privates = diff.private || {};
  const seams = diff.seams || [];
  const hasPart = sharedVerses.length > 0 || seams.length > 0 || Object.keys(privates).some(k => (privates[k] || []).length);
  return /*#__PURE__*/React.createElement("div", {
    className: "study-topic study-graph"
  }, /*#__PURE__*/React.createElement("div", {
    className: "study-editor-bar"
  }, /*#__PURE__*/React.createElement("button", {
    className: "study-back",
    onClick: onClose
  }, "\u2039 ", previewReader ? "Back" : "All graphs")), /*#__PURE__*/React.createElement("div", {
    className: "study-eyebrow"
  }, "Argument graph"), /*#__PURE__*/React.createElement("h1", {
    className: "study-topic-title"
  }, entry.title), /*#__PURE__*/React.createElement("div", {
    className: "study-topic-meta"
  }, Object.keys(claims).length, " claims \xB7 ", overlays.length, " ", overlays.length === 1 ? "tradition" : "traditions"), /*#__PURE__*/React.createElement("div", {
    className: "study-graph-caution"
  }, "Maps reasoning, does not settle truth."), entry.intro && /*#__PURE__*/React.createElement("p", {
    className: "study-topic-intro"
  }, entry.intro), /*#__PURE__*/React.createElement(GraphChart, {
    claims: claims,
    overlays: overlays,
    analysis: analysis,
    onNavigate: onNavigate
  }), hasPart && /*#__PURE__*/React.createElement("div", {
    className: "study-part"
  }, /*#__PURE__*/React.createElement("div", {
    className: "study-part-label"
  }, "Where they part"), /*#__PURE__*/React.createElement("div", {
    className: "study-part-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "study-part-key"
  }, "Verses leaned on by more than one side:"), " ", sharedVerses.length ? sharedVerses.map((cid, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    className: "study-part-chip"
  }, (claims[cid] || {}).ref || cid)) : /*#__PURE__*/React.createElement("em", {
    className: "study-verse-missing"
  }, "they cite different verses")), seams.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "study-part-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "study-part-key"
  }, "Contested claims (one side leans on, another rejects):"), /*#__PURE__*/React.createElement("div", {
    className: "study-part-privs"
  }, seams.map((s, i) => /*#__PURE__*/React.createElement("div", {
    className: "study-part-priv",
    key: i
  }, /*#__PURE__*/React.createElement(ProvBadge, {
    prov: s.provenance
  }), " ", s.body, /*#__PURE__*/React.createElement("span", {
    className: "study-seam-who"
  }, " \u2014 held by ", s.used_by.join(", "), "; rejected by ", s.rejected_by.join(", ")))))), overlays.map((ov, i) => {
    const priv = privates[i] || [];
    if (!priv.length) return null;
    return /*#__PURE__*/React.createElement("div", {
      className: "study-part-row",
      key: i
    }, /*#__PURE__*/React.createElement("span", {
      className: "study-part-key"
    }, ov.tradition, " adds:"), /*#__PURE__*/React.createElement("div", {
      className: "study-part-privs"
    }, priv.map((cid, j) => /*#__PURE__*/React.createElement("div", {
      className: "study-part-priv",
      key: j
    }, /*#__PURE__*/React.createElement(ProvBadge, {
      prov: (claims[cid] || {}).provenance
    }), " ", (claims[cid] || {}).text))));
  })));
}

// ---- The Study tab --------------------------------------------------------
function StudyView({
  admin,
  pending,
  onConsumed,
  onNavigateToLibrary
}) {
  const adminUser = !!admin;
  const [module, setModule] = useState("topic");
  const [entries, setEntries] = useState(null);
  const [err, setErr] = useState(false);
  const [editing, setEditing] = useState(null);
  const [editMode, setEditMode] = useState(false); // read vs edit (read-first for all types)
  const [previewReader, setPreviewReader] = useState(false); // admin: preview the clean reader view
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [q, setQ] = useState("");
  // A non-admin visitor IS the reader: published-only, no editing, no module switch
  // (only Topics are public). An admin can also opt into this view via "Preview as reader".
  const readerView = !adminUser || previewReader;
  const load = mod => {
    setEntries(null);
    api.studyEntries(mod).then(d => {
      if (d && d.entries) {
        setEntries(d.entries);
        setErr(false);
      } else setErr(true);
    });
  };
  useEffect(() => {
    load(module);
  }, [module]);
  const pickModule = m => {
    if (m === module) return;
    setEditing(null);
    setSavedAt(null);
    setQ("");
    setModule(m);
  };
  const openEntry = id => {
    setSavedAt(null);
    api.studyEntry(id).then(d => {
      if (!d) return;
      if (isTopicLike(d.type)) {
        setEditing({
          id: d.id,
          type: d.type,
          title: d.title || "",
          intro: d.intro || "",
          sections: (d.sections || []).map(s => ({
            heading: s.heading || "",
            verses: s.verses || []
          })),
          related: d.related || [],
          status: d.status || "draft",
          source: d.source || ""
        });
      } else {
        // graph — read-only in this cut
        setEditing({
          id: d.id,
          type: "graph",
          title: d.title || "",
          intro: d.intro || "",
          claims: d.claims || {},
          overlays: d.overlays || [],
          analysis: d.analysis || {
            verdicts: [],
            diff: {}
          },
          status: d.status || "draft"
        });
      }
      setEditMode(false);
    });
  };
  const newEntry = () => {
    setSavedAt(null);
    setEditMode(true);
    setEditing(blankTopic());
  }; // only topics are authored in-app; graphs come from the script

  // Opened from the metaV sidebar: jump straight into a name-topic's page.
  useEffect(() => {
    if (pending) {
      openEntry(pending);
      if (onConsumed) onConsumed();
    }
  }, [pending]);
  const save = () => {
    if (!editing || !editing.title.trim() || saving) return; // only topic-like entries have an in-app editor
    setSaving(true);
    const payload = {
      ...editing,
      sections: editing.sections.map(s => ({
        heading: s.heading,
        verses: s.verses.map(v => ({
          ref: v.ref
        }))
      }))
    };
    api.studySave(payload).then(d => {
      setSaving(false);
      if (d && d.id) {
        setEditing(e => ({
          ...e,
          id: d.id
        }));
        setSavedAt(Date.now());
        load(module);
      }
    });
  };
  const del = () => {
    if (!editing || !editing.id) {
      setEditing(null);
      return;
    }
    if (!window.confirm("Delete this entry?")) return;
    api.studyDelete(editing.id).then(() => {
      setEditing(null);
      load(module);
    });
  };
  if (err) return /*#__PURE__*/React.createElement("div", {
    className: "stats-view"
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "Couldn't load study content.", adminUser ? " (Admin sign-in required.)" : ""));
  if (editing) {
    const ro = readerView || !editMode; // read-only: a reader/preview, or not actively editing
    const close = () => {
      setEditing(null);
      setSavedAt(null);
    };
    if (isTopicLike(editing.type)) return /*#__PURE__*/React.createElement("div", {
      className: "study-view"
    }, /*#__PURE__*/React.createElement(TopicPage, {
      entry: editing,
      editing: !ro,
      onChange: setEditing,
      onSave: save,
      onDelete: del,
      onClose: close,
      onToggleEdit: () => setEditMode(m => !m),
      previewReader: readerView,
      saving: saving,
      savedAt: savedAt,
      onNavigate: onNavigateToLibrary
    }));
    return /*#__PURE__*/React.createElement("div", {
      className: "study-view"
    }, /*#__PURE__*/React.createElement(GraphPage, {
      entry: editing,
      onClose: close,
      previewReader: readerView,
      onNavigate: onNavigateToLibrary
    }));
  }
  const isTopic = module === "topic";
  const moduleName = isTopic ? "Topics" : "Graphs";
  const qs = q.trim().toLowerCase();
  const pool = (entries || []).filter(e => !readerView || e.status === "published"); // a reader only sees published
  const sortKey = e => displayTitle(e.title || "").toLowerCase().replace(/^(?:the|a|an)\s+/, "");
  const shown = pool.filter(e => !qs || (e.title || "").toLowerCase().includes(qs) || displayTitle(e.title).toLowerCase().includes(qs) || (e.heldBy || "").toLowerCase().includes(qs)).sort((a, b) => sortKey(a).localeCompare(sortKey(b)));
  return /*#__PURE__*/React.createElement("div", {
    className: "study-view"
  }, adminUser && /*#__PURE__*/React.createElement("div", {
    className: "study-sub"
  }, STUDY_MODULES.map(m => /*#__PURE__*/React.createElement("button", {
    key: m.id,
    className: "study-sub-b" + (module === m.id ? " on" : ""),
    onClick: () => pickModule(m.id)
  }, m.label)), /*#__PURE__*/React.createElement("button", {
    className: "study-preview-toggle" + (previewReader ? " on" : ""),
    onClick: () => setPreviewReader(p => !p),
    title: "See exactly what a reader sees \u2014 editing off, drafts hidden"
  }, previewReader ? "✓ Previewing as reader" : "Preview as reader")), previewReader && /*#__PURE__*/React.createElement("div", {
    className: "study-preview-note"
  }, "You're seeing what a reader sees \u2014 editing is off and drafts are hidden.", /*#__PURE__*/React.createElement("button", {
    className: "study-preview-exit",
    onClick: () => setPreviewReader(false)
  }, "Exit preview")), /*#__PURE__*/React.createElement("div", {
    className: "study-list-head"
  }, /*#__PURE__*/React.createElement("h1", {
    className: "stats-title"
  }, moduleName), !readerView && isTopic && /*#__PURE__*/React.createElement("button", {
    className: "study-new",
    onClick: newEntry
  }, "+ New topic")), /*#__PURE__*/React.createElement("div", {
    className: "stats-sub"
  }, isTopic ? "Browse a subject and its verses, grouped by subtopic. Mostly filled from MetaV — light edits only." : "Arguments as claims and links — each side's chain stress-tested to show where it actually load-bears."), pool.length > 0 && /*#__PURE__*/React.createElement("input", {
    className: "study-search-input",
    type: "text",
    value: q,
    placeholder: "Search " + moduleName.toLowerCase() + "…",
    onChange: e => setQ(e.target.value)
  }), entries === null ? /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "Loading\u2026") : shown.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, qs ? "No matches for “" + q + "”." : !adminUser ? "No study topics yet — check back soon." : previewReader ? "Nothing published yet — mark an entry Published to show it here." : isTopic ? "Nothing here yet — start with “+ New topic”. (Or import from MetaV.)" : "No graphs yet — add one with scripts/add_study_graph.py.") : /*#__PURE__*/React.createElement("div", {
    className: "study-rows"
  }, shown.map(e => /*#__PURE__*/React.createElement("button", {
    className: "study-row",
    key: e.id,
    onClick: () => openEntry(e.id)
  }, !isTopic && /*#__PURE__*/React.createElement("span", {
    className: "study-badge study-badge--graph"
  }, "Graph"), /*#__PURE__*/React.createElement("span", {
    className: "study-row-title"
  }, isTopic ? displayTitle(e.title) : e.title), /*#__PURE__*/React.createElement("span", {
    className: "study-row-n"
  }, e.n || 0, " ", isTopic ? "verses" : "claims"), !readerView && e.status === "draft" && /*#__PURE__*/React.createElement("span", {
    className: "study-row-draft"
  }, "draft")))));
}

// ============================================================
// READING PLAN — the "Days" view of the chronological picker.
//
// A 365-day plan is baked into chronological.json (chrono.days: each entry is a day
// with its passage positions + verse total). Progress is tracked PER READING TEXT —
// your ABP day is independent of your KJV day — and lives in the browser
// (localStorage "lexica.plan.v1"; account sync can layer on later).
//
// Reading itself reuses the existing chronological passage reader: tapping a day's
// passage jumps the reader there; "Mark today complete" advances THIS text's progress
// to the next day (and continues reading into it).
// ============================================================
const PLAN_KEY = "lexica.plan.v1";
function planLoadAll() {
  try {
    return JSON.parse(localStorage.getItem(PLAN_KEY) || "{}") || {};
  } catch (e) {
    return {};
  }
}
function planSaveAll(obj) {
  try {
    localStorage.setItem(PLAN_KEY, JSON.stringify(obj));
  } catch (e) {}
}
// One text's progress, with sane defaults for a text never started. `done` is the set
// of completed day numbers (independent — you can skip around). Old saves stored only a
// linear `day` pointer (everything before it = done); migrate that into the done list so
// existing progress carries over.
function planFor(all, text) {
  const p = all && all[text] || {};
  let done = p.done;
  if (!Array.isArray(done)) {
    done = [];
    for (let i = 1; i < (p.day || 1); i++) done.push(i); // migrate the old pointer
  }
  return {
    day: p.day || 1,
    streak: p.streak || 0,
    last: p.last || null,
    done
  };
}
function planYmd(d) {
  d = d || new Date();
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
}
function planDayDiff(a, b) {
  // whole days from ymd a -> ymd b
  const pa = new Date(a + "T00:00:00"),
    pb = new Date(b + "T00:00:00");
  return Math.round((pb - pa) / 86400000);
}

// Hebrew months (spring-first) paired with their zodiac constellation. `days` = roughly
// how long the sun takes to cross that constellation (IAU boundaries) — Virgo the longest
// stretch, Scorpius the shortest. The Days plan sizes each "month" block by these, scaled
// to fill the whole plan, so the blocks are deliberately uneven (the themed calendar).
const ZODIAC = [{
  heb: "Nisan",
  sign: "Aries",
  glyph: "♈",
  days: 25
}, {
  heb: "Iyar",
  sign: "Taurus",
  glyph: "♉",
  days: 38
}, {
  heb: "Sivan",
  sign: "Gemini",
  glyph: "♊",
  days: 30
}, {
  heb: "Tammuz",
  sign: "Cancer",
  glyph: "♋",
  days: 20
}, {
  heb: "Av",
  sign: "Leo",
  glyph: "♌",
  days: 37
}, {
  heb: "Elul",
  sign: "Virgo",
  glyph: "♍",
  days: 45
}, {
  heb: "Tishrei",
  sign: "Libra",
  glyph: "♎",
  days: 23
}, {
  heb: "Cheshvan",
  sign: "Scorpius",
  glyph: "♏",
  days: 8
}, {
  heb: "Kislev",
  sign: "Sagittarius",
  glyph: "♐",
  days: 33
}, {
  heb: "Tevet",
  sign: "Capricorn",
  glyph: "♑",
  days: 28
}, {
  heb: "Shevat",
  sign: "Aquarius",
  glyph: "♒",
  days: 24
}, {
  heb: "Adar",
  sign: "Pisces",
  glyph: "♓",
  days: 38
}];

// The plan body — shared by the desktop left nav and the mobile picker.
function DayPlanView({
  chrono,
  curText,
  texts,
  progAll,
  chronoPos,
  onPickText,
  onPickPassage,
  onToggleDone,
  isMobile
}) {
  const days = chrono && chrono.days || [];
  const total = days.length || 365;
  // Chunk the plan into 12 "month" blocks (accordion, one open at a time), themed to the
  // Hebrew months / zodiac: each block is as long, proportionally, as the sun spends
  // crossing that constellation, scaled to fill the whole plan. So the blocks are uneven.
  const zSum = ZODIAC.reduce((s, z) => s + z.days, 0);
  let _acc = 0;
  const zBounds = ZODIAC.map(z => {
    _acc += z.days;
    return Math.round(_acc / zSum * total);
  });
  zBounds[zBounds.length - 1] = total; // last block always reaches the end
  const monthOf = d => {
    for (let i = 0; i < zBounds.length; i++) if (d <= zBounds[i]) return i + 1;
    return zBounds.length;
  };
  const prog = planFor(progAll, curText);
  // Completed days are an independent set now — mark/un-mark any day, skip around freely.
  const doneSet = new Set(prog.done || []);
  const doneCount = doneSet.size;
  // "Next to read" = the first day NOT yet done (used for focus + Jump-to-today + header).
  let curDay = 1;
  while (curDay <= total && doneSet.has(curDay)) curDay++;
  if (curDay > total) curDay = total;
  // The day that holds the passage you're currently reading. The list FOLLOWS this —
  // opening, highlighting, and scrolling to it as you switch into chronological or turn
  // pages — separately from curDay (the next unread day, what Jump-to-today targets).
  const readingDay = (() => {
    if (chronoPos == null) return null;
    const d = days.find(dd => dd.pos && dd.pos.includes(chronoPos));
    return d ? d.day : null;
  })();
  const focusDay = readingDay || curDay;
  const pct = Math.round(doneCount / total * 100); // share of all days marked done
  const [open, setOpen] = useState(() => new Set([focusDay]));
  const [openMonth, setOpenMonth] = useState(() => monthOf(focusDay)); // which month block is expanded
  const todayRef = useRef(null); // plan "Today" — target of the Jump button
  const focusRef = useRef(null); // the day you're reading — auto-scrolled to
  const monthRefs = useRef({}); // each month block — to scroll the opened one to the top

  // Follow the reading position: keep the day you're in open + scrolled into view as it
  // changes (switching into chrono, turning pages, or marking a day complete — all of
  // which move readingDay). Also re-centres when you switch reading text.
  useEffect(() => {
    setOpen(new Set([focusDay]));
    setOpenMonth(monthOf(focusDay));
    requestAnimationFrame(() => focusRef.current && focusRef.current.scrollIntoView({
      block: "nearest"
    }));
  }, [curText, focusDay]);
  const jumpToday = () => {
    const td = days.find(d => d.day === curDay);
    if (td) selectDay(td); // open today, move the dot there, load its first reading
    else setOpen(new Set([curDay]));
    requestAnimationFrame(() => todayRef.current && todayRef.current.scrollIntoView({
      behavior: "smooth",
      block: "center"
    }));
  };
  const passagesOf = day => day.pos.map(q => chrono.passages[q - 1]).filter(Boolean);
  // One click on a day does the lot: open ONLY that day (accordion — the one you were
  // on closes), move the reading dot to it, and load its first reading in the pane.
  const selectDay = day => {
    setOpen(new Set([day.day]));
    setOpenMonth(monthOf(day.day));
    const ps = passagesOf(day);
    if (ps[0]) onPickPassage(ps[0]);
  };
  // A day tap behaves the same on desktop and mobile: collapse the day you had open,
  // open this one, and move the reading dot to it. On mobile the sheet stays open (the
  // parent passes a non-closing onPickPassage) so you can keep browsing.
  const onDayTap = day => selectDay(day);

  // Bin the days into month blocks (contiguous runs of the same monthOf()).
  const months = [];
  days.forEach(d => {
    const m = monthOf(d.day);
    let g = months[months.length - 1];
    if (!g || g.n !== m) {
      g = {
        n: m,
        days: [],
        first: d.day,
        last: d.day
      };
      months.push(g);
    }
    g.days.push(d);
    g.last = d.day;
  });
  // Open/collapse a month. When opening, scroll the DAY LIST so the month lands at the
  // top — but ONLY that inner list, never the page/reading (set scrollTop directly
  // instead of scrollIntoView, which would yank every scroll parent around). Mobile
  // offsets for the sticky progress bar; desktop's header is static, so no offset.
  const toggleMonth = n => setOpenMonth(cur => {
    const next = cur === n ? null : n;
    if (next != null) {
      requestAnimationFrame(() => {
        const el = monthRefs.current[next];
        const scroller = el && el.closest(".plan-days, .mpick-scroll");
        if (!el || !scroller) return;
        const offset = scroller.classList.contains("mpick-scroll") ? 84 : 0;
        const delta = el.getBoundingClientRect().top - scroller.getBoundingClientRect().top;
        scroller.scrollTo({
          top: scroller.scrollTop + delta - offset,
          behavior: "smooth"
        });
      });
    }
    return next;
  });

  // One day row — rendered only when its month block is open.
  const renderDay = day => {
    const done = doneSet.has(day.day);
    const isReading = readingDay != null && day.day === readingDay;
    const isOpen = open.has(day.day);
    const markClick = e => {
      e.stopPropagation();
      onToggleDone(day.day);
    };
    // Every day's marker is its own toggle now — done shows a ✓ (click to undo), the day
    // you're reading shows a dot, anything else a faint ring you can tap to mark done.
    const mark = /*#__PURE__*/React.createElement("button", {
      className: "plan-day-mark" + (done ? " plan-day-mark--done" : isReading ? " plan-day-mark--reading" : ""),
      onClick: markClick,
      "aria-label": "Mark Day " + day.day + (done ? " unread" : " read"),
      title: done ? "Read — click to undo" : "Mark as read"
    }, done ? /*#__PURE__*/React.createElement(Icon.Check, null) : isReading ? /*#__PURE__*/React.createElement("span", {
      className: "plan-day-dot",
      "aria-hidden": "true"
    }) : /*#__PURE__*/React.createElement("span", {
      className: "plan-day-hollow",
      "aria-hidden": "true"
    }));
    return /*#__PURE__*/React.createElement("div", {
      key: day.day,
      ref: el => {
        if (day.day === focusDay) focusRef.current = el;
        if (day.day === curDay) todayRef.current = el;
      },
      className: "plan-day" + (done ? " plan-day--done" : "") + (isReading ? " plan-day--reading" : "") + (isOpen ? " open" : "")
    }, /*#__PURE__*/React.createElement("div", {
      className: "plan-day-head",
      role: "button",
      tabIndex: 0,
      "aria-expanded": isOpen,
      onClick: () => onDayTap(day),
      onKeyDown: e => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onDayTap(day);
        }
      }
    }, /*#__PURE__*/React.createElement("span", {
      className: "plan-day-n"
    }, "Day ", day.day), /*#__PURE__*/React.createElement("span", {
      className: "plan-day-v"
    }, day.verses, "v"), mark), isOpen && /*#__PURE__*/React.createElement("div", {
      className: "plan-day-body"
    }, passagesOf(day).map(p => /*#__PURE__*/React.createElement("button", {
      key: p.pos,
      className: "plan-passage" + (p.pos === chronoPos ? " on" : ""),
      onClick: () => onPickPassage(p)
    }, p.label))));
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "plan"
  }, /*#__PURE__*/React.createElement("div", {
    className: "plan-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "plan-prog"
  }, /*#__PURE__*/React.createElement("span", {
    className: "plan-dayno"
  }, "Day ", curDay, " of ", total), /*#__PURE__*/React.createElement("span", {
    className: "plan-pct"
  }, pct, "%")), /*#__PURE__*/React.createElement("div", {
    className: "plan-bar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "plan-bar-fill",
    style: {
      width: pct + "%"
    }
  })), /*#__PURE__*/React.createElement("div", {
    className: "plan-meta"
  }, /*#__PURE__*/React.createElement("span", {
    className: "plan-streak"
  }, prog.streak > 0 ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Icon.Flame, null), " ", prog.streak, "-day streak") : /*#__PURE__*/React.createElement(React.Fragment, null, "Just getting started")), /*#__PURE__*/React.createElement("button", {
    className: "plan-jump",
    onClick: jumpToday
  }, "Jump to today"))), /*#__PURE__*/React.createElement("div", {
    className: "plan-days"
  }, /*#__PURE__*/React.createElement("div", {
    className: "plan-days-inner"
  }, months.map(m => {
    const mOpen = openMonth === m.n;
    const doneInMonth = m.days.filter(d => doneSet.has(d.day)).length;
    const hasReading = readingDay != null && readingDay >= m.first && readingDay <= m.last;
    return /*#__PURE__*/React.createElement("div", {
      key: m.n,
      ref: el => {
        if (el) monthRefs.current[m.n] = el;
      },
      className: "plan-month" + (mOpen ? " open" : "") + (hasReading ? " plan-month--reading" : "")
    }, /*#__PURE__*/React.createElement("button", {
      className: "plan-month-head",
      onClick: () => toggleMonth(m.n),
      "aria-expanded": mOpen
    }, /*#__PURE__*/React.createElement("span", {
      className: "plan-month-name",
      title: ZODIAC[m.n - 1].sign
    }, ZODIAC[m.n - 1].glyph, " ", ZODIAC[m.n - 1].heb), /*#__PURE__*/React.createElement("span", {
      className: "plan-month-range"
    }, "Days ", m.first, "\u2013", m.last), /*#__PURE__*/React.createElement("span", {
      className: "plan-month-done"
    }, doneInMonth, "/", m.days.length)), mOpen && /*#__PURE__*/React.createElement("div", {
      className: "plan-month-days"
    }, m.days.map(renderDay)));
  }))));
}

// ============================================================
// DAY INTRO PANEL — the ESV-style "Reading" card for the chronological plan.
//
// Shows for whatever chronological day you're reading: the reading number, an
// AI-written title + Berean summary, the era's dated timeline with your spot marked,
// and the day's passages. Lives in the right detail panel (desktop) / a bottom sheet
// (mobile), the same shell the chapter overview uses.
//
// Dates: each ERA carries a span + a few dated milestones (curated below; LXX dates
// for the early eras). A reading's own date is APPROXIMATE — derived from its position
// in the era's day list and shown as a clearly-marked "c." — so the marker slides
// correctly without inventing a precise year for all 365 readings.
// ============================================================

// era id -> { start, end, marks:[{label, year}] }. Year: negative = BC, positive = AD.
const ERA_TIMELINE = {
  "primeval-history": {
    start: -5500,
    end: -2100,
    marks: [{
      label: "Creation",
      year: -5500
    }, {
      label: "The Flood",
      year: -3300
    }, {
      label: "Tower of Babel",
      year: -3000
    }]
  },
  "the-patriarchs": {
    start: -2166,
    end: -1805,
    marks: [{
      label: "Abraham's call",
      year: -2091
    }, {
      label: "Isaac & Jacob",
      year: -2006
    }, {
      label: "Joseph in Egypt",
      year: -1876
    }]
  },
  "the-exodus-wilderness": {
    start: -1446,
    end: -1406,
    marks: [{
      label: "The Exodus",
      year: -1446
    }, {
      label: "Law at Sinai",
      year: -1445
    }, {
      label: "Wilderness",
      year: -1420
    }]
  },
  "the-conquest": {
    start: -1406,
    end: -1380,
    marks: [{
      label: "Jordan crossed",
      year: -1406
    }, {
      label: "Jericho falls",
      year: -1406
    }, {
      label: "Land divided",
      year: -1399
    }]
  },
  "the-judges": {
    start: -1380,
    end: -1050,
    marks: [{
      label: "Deborah",
      year: -1209
    }, {
      label: "Gideon",
      year: -1162
    }, {
      label: "Samson",
      year: -1075
    }]
  },
  "the-united-kingdom": {
    start: -1100,
    end: -970,
    marks: [{
      label: "Samuel's ministry",
      year: -1060
    }, {
      label: "Saul anointed",
      year: -1050
    }, {
      label: "David is king",
      year: -1010
    }]
  },
  "the-reign-of-solomon": {
    start: -970,
    end: -931,
    marks: [{
      label: "Solomon's reign",
      year: -969
    }, {
      label: "Temple built",
      year: -966
    }, {
      label: "Solomon dies",
      year: -931
    }]
  },
  "the-divided-kingdom": {
    start: -931,
    end: -609,
    marks: [{
      label: "Kingdom divides",
      year: -931
    }, {
      label: "Israel falls",
      year: -722
    }, {
      label: "Josiah's reforms",
      year: -622
    }]
  },
  "judah-s-fall-the-exile": {
    start: -609,
    end: -538,
    marks: [{
      label: "Babylon rises",
      year: -605
    }, {
      label: "Jerusalem falls",
      year: -586
    }, {
      label: "Exiles freed",
      year: -538
    }]
  },
  "the-return": {
    start: -538,
    end: -430,
    marks: [{
      label: "Cyrus's decree",
      year: -538
    }, {
      label: "Temple rebuilt",
      year: -516
    }, {
      label: "Ezra & Nehemiah",
      year: -445
    }]
  },
  "the-gospels": {
    start: -5,
    end: 33,
    marks: [{
      label: "Jesus born",
      year: -5
    }, {
      label: "Public ministry",
      year: 27
    }, {
      label: "Death & rising",
      year: 30
    }]
  },
  "the-early-church": {
    start: 30,
    end: 68,
    marks: [{
      label: "Pentecost",
      year: 30
    }, {
      label: "Paul's missions",
      year: 47
    }, {
      label: "Paul in Rome",
      year: 60
    }]
  },
  "revelation": {
    start: 90,
    end: 96,
    marks: [{
      label: "John's vision",
      year: 95
    }]
  }
};

// "1060 BC" / "AD 30". Years are whole; there is no year 0 in the data.
function fmtYear(y) {
  y = Math.round(y);
  return y < 0 ? -y + " BC" : "AD " + y;
}

// A reading's approximate date window: interpolate its slot within its era's day list
// across the era's span. Sparse eras (few days over a long span) give a wide window;
// dense ones (the monarchy) give a near-point. Returns null if the era has no timeline.
function readingWindow(day, chrono) {
  const et = day && ERA_TIMELINE[day.era];
  if (!et || !chrono || !chrono.days) return null;
  const eraDays = chrono.days.filter(d => d.era === day.era);
  const idx = Math.max(0, eraDays.findIndex(d => d.day === day.day));
  const n = eraDays.length || 1;
  const span = et.end - et.start;
  const y0 = et.start + idx / n * span;
  const y1 = et.start + (idx + 1) / n * span;
  return {
    et,
    y0,
    y1
  };
}

// "c. 968 BC" for a point, "c. 968–948 BC" / "c. AD 30–47" for a span.
function fmtReadingDate(y0, y1) {
  const a = Math.round(y0),
    b = Math.round(y1);
  if (b - a < 15) return "c. " + fmtYear((a + b) / 2);
  if (a < 0 && b < 0) return "c. " + -a + "–" + -b + " BC";
  if (a >= 0 && b >= 0) return "c. AD " + a + "–" + b;
  return "c. " + fmtYear(a) + " – " + fmtYear(b);
}

// The dated strip: a thin track for the era span, a filled "you are here" bar showing
// how much time this reading covers, and the milestone dots. The bar sits ON the track,
// but the dots are drawn AFTER it with a thick paper ring, so every checkpoint is carved
// cleanly out of the bar — the bar can never swallow one. The first dot (era start) sits
// flush-left so the year list below can line its bullets up under it. Milestone labels
// live in that list (each tied to its own dot), not floating over the track.
// The first dot is at viewBox x=0; the .dintro-tl-svg CSS insets the strip by half a
// list-bullet (3.5px) and lets the end dots overflow, so that first dot's CENTRE lands
// exactly on the year-list bullet centre (both 3.5px in) at any panel width.
function TimelineStrip({
  win
}) {
  if (!win) return null;
  const {
    et,
    y0,
    y1
  } = win;
  const W = 320;
  const span = et.end - et.start || 1;
  const xOf = yr => (yr - et.start) / span * W;
  const mx0 = Math.max(0, xOf(y0)),
    mx1 = Math.min(W, xOf(y1));
  const nowX = Math.min(mx0, mx1),
    nowW = Math.max(10, Math.abs(mx1 - mx0));
  return /*#__PURE__*/React.createElement("div", {
    className: "dintro-tl"
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: `0 0 ${W} 14`,
    className: "dintro-tl-svg",
    role: "img",
    "aria-label": "Era timeline"
  }, /*#__PURE__*/React.createElement("rect", {
    x: 0,
    y: 5,
    width: W,
    height: 4,
    rx: 2,
    className: "dintro-tl-track"
  }), /*#__PURE__*/React.createElement("rect", {
    x: nowX,
    y: 3,
    width: nowW,
    height: 8,
    rx: 4,
    className: "dintro-tl-now"
  }), et.marks.map((m, i) => {
    // Every milestone is the SAME round dot. A dark dot sitting under the navy
    // "now" bar would vanish, so there we just invert its COLOUR (white fill, dark
    // ring) — same shape, stays visible. No shape change as the bar moves over it.
    const mxx = xOf(m.year);
    const onBar = mxx >= nowX - 1 && mxx <= nowX + nowW + 1;
    return /*#__PURE__*/React.createElement("circle", {
      key: i,
      cx: mxx,
      cy: 7,
      r: 3.5,
      className: "dintro-tl-dot" + (onBar ? " dintro-tl-dot--on" : "")
    });
  })), /*#__PURE__*/React.createElement("div", {
    className: "dintro-tl-legend"
  }, et.marks.map((m, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "dintro-tl-ev"
  }, /*#__PURE__*/React.createElement("span", {
    className: "dintro-tl-ev-dot",
    "aria-hidden": "true"
  }), /*#__PURE__*/React.createElement("span", {
    className: "dintro-tl-ev-yr"
  }, fmtYear(m.year)), /*#__PURE__*/React.createElement("span", {
    className: "dintro-tl-ev-lbl"
  }, m.label)))));
}
function DayIntroPanel({
  day,
  chrono,
  isMobile,
  onClose,
  onPickPassage,
  onOverview
}) {
  const dayNo = day ? day.day : null;
  const [data, setData] = useState(() => dayNo != null && DayIntroPanel._cache[dayNo] || null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (dayNo == null) return;
    const cached = DayIntroPanel._cache[dayNo];
    if (cached) {
      setData(cached);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setData(null);
    api.chronoIntro(dayNo).then(d => {
      if (!cancelled) {
        DayIntroPanel._cache[dayNo] = d || {};
        setData(d || {});
        setLoading(false);
      }
    }).catch(() => {
      if (!cancelled) {
        setData({});
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [dayNo]);
  const {
    sheetRef,
    scrollRef
  } = useSwipeToDismiss(onClose);
  const titleRef = useRef(null);
  const era = chrono && chrono.eras && day ? chrono.eras.find(e => e.id === day.era) : null;
  const win = day ? readingWindow(day, chrono) : null;
  const passages = day && chrono && chrono.passages ? day.pos.map(q => chrono.passages[q - 1]).filter(Boolean) : [];
  const title = data && data.title || (era ? era.name : "Today's reading");
  const dateLine = win ? fmtReadingDate(win.y0, win.y1) : null;
  // Shrink the title to fit one line beside the corner toggle link — same on desktop
  // and mobile (no ellipsis; it scales down to a floor instead).
  useFitText(titleRef, title);
  const content = /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "detail-hero dintro-hero"
  }, /*#__PURE__*/React.createElement("div", {
    className: "dintro-meta"
  }, "Reading ", dayNo, era ? " · " + era.name : ""), dateLine && /*#__PURE__*/React.createElement("div", {
    className: "dintro-date"
  }, dateLine)), win && /*#__PURE__*/React.createElement("section", {
    className: "sec"
  }, /*#__PURE__*/React.createElement("h4", {
    className: "sec-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "sec-t"
  }, "Timeline")), /*#__PURE__*/React.createElement(TimelineStrip, {
    win: win
  })), /*#__PURE__*/React.createElement("section", {
    className: "sec"
  }, /*#__PURE__*/React.createElement("h4", {
    className: "sec-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "sec-t"
  }, "About this reading")), loading ? /*#__PURE__*/React.createElement("div", {
    className: "summary-loading"
  }, "Writing today's intro\u2026") : data && data.summary ? /*#__PURE__*/React.createElement("p", {
    className: "detail-p"
  }, renderInlineMd(data.summary)) : /*#__PURE__*/React.createElement("div", {
    className: "summary-loading"
  }, "No intro available for this reading.")), passages.length > 0 && /*#__PURE__*/React.createElement("section", {
    className: "sec"
  }, /*#__PURE__*/React.createElement("h4", {
    className: "sec-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "sec-t"
  }, "Today's passages")), /*#__PURE__*/React.createElement("div", {
    className: "dintro-passages"
  }, passages.map(p => /*#__PURE__*/React.createElement("button", {
    key: p.pos,
    className: "dintro-passage",
    onClick: () => onPickPassage && onPickPassage(p)
  }, /*#__PURE__*/React.createElement("span", {
    className: "dintro-passage-ref"
  }, p.label), /*#__PURE__*/React.createElement("span", {
    className: "dintro-passage-go",
    "aria-hidden": "true"
  }, "\u203A"))))));

  // Header is just the subject — the day's serif title (the contents make it
  // obvious it's a reading intro, so no panel-type label). "Reading N" + era move
  // down into the hero meta line. The "‹ Overview" toggle keeps the .detail-back slot.
  const headTitle = /*#__PURE__*/React.createElement("span", {
    ref: titleRef,
    className: "detail-pos summary-pos dintro-era-head"
  }, title);
  if (isMobile) {
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      className: "sheet-scrim",
      onClick: onClose
    }), /*#__PURE__*/React.createElement("aside", {
      ref: sheetRef,
      className: "detail detail-sheet summary-sheet dintro-sheet",
      role: "dialog",
      "aria-label": "Reading intro"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sheet-drag-zone",
      "aria-hidden": "true"
    }, /*#__PURE__*/React.createElement("div", {
      className: "sheet-handle"
    })), /*#__PURE__*/React.createElement("div", {
      className: "detail-head"
    }, /*#__PURE__*/React.createElement("div", {
      className: "detail-head-l"
    }, /*#__PURE__*/React.createElement("span", {
      ref: titleRef,
      className: "detail-pos summary-pos dintro-era-head"
    }, title)), onOverview && /*#__PURE__*/React.createElement("button", {
      className: "detail-back",
      onClick: onOverview,
      "aria-label": "Chapter overview",
      title: "Overview"
    }, "\u2039")), /*#__PURE__*/React.createElement("div", {
      className: "detail-body",
      ref: scrollRef
    }, content)));
  }
  return /*#__PURE__*/React.createElement("aside", {
    className: "detail detail-side summary-side dintro-side",
    role: "complementary",
    "aria-label": "Reading intro"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "detail-head-l"
  }, headTitle), onOverview && /*#__PURE__*/React.createElement("button", {
    className: "detail-back",
    onClick: onOverview,
    "aria-label": "Chapter overview"
  }, "\u2039 Overview")), /*#__PURE__*/React.createElement("div", {
    className: "detail-body"
  }, content));
}
DayIntroPanel._cache = {};

// 59a — Library helpers, split out of 60-library.jsx so that file holds only the
//       LibraryView component. Loads just before 59b-library-nav + 60-library.
// ============================================================
// LIBRARY HELPERS
// ============================================================

// Wrap every occurrence of any term in `terms` with a highlight mark (for the
// in-text search result list). `partial` false = whole-word only; `caseSensitive`
// matches case. Mirrors the backend matcher so the paint lines up with the hits.
function highlightTerms(text, terms, partial, caseSensitive) {
  if (!text || !terms || !terms.length) return text;
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const body = terms.filter(Boolean).map(t => {
    const e = esc(t);
    return partial ? e : `(?<!\\w)${e}(?!\\w)`;
  }).join("|");
  if (!body) return text;
  let re;
  try {
    re = new RegExp(body, caseSensitive ? "g" : "gi");
  } catch (e) {
    return text;
  }
  const parts = [];
  let last = 0,
    key = 0,
    m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(/*#__PURE__*/React.createElement("mark", {
      key: key++,
      className: "lib-search-mark"
    }, m[0]));
    last = m.index + m[0].length;
    if (m.index === re.lastIndex) re.lastIndex++; // guard against a zero-length match
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

// Search-range presets for the in-text search (mirrors eSword's range groups).
// Each is [fromAbbrev, toAbbrev] over the canonical 66 books.
const SEARCH_RANGES = [{
  id: "all",
  label: "Whole Bible",
  from: "Gen",
  to: "Rev"
}, {
  id: "ot",
  label: "Old Testament",
  from: "Gen",
  to: "Mal"
}, {
  id: "nt",
  label: "New Testament",
  from: "Mat",
  to: "Rev"
}, {
  id: "pent",
  label: "Pentateuch (Gen–Deu)",
  from: "Gen",
  to: "Deu"
}, {
  id: "hist",
  label: "History (Jos–Est)",
  from: "Jos",
  to: "Est"
}, {
  id: "wis",
  label: "Wisdom (Job–Son)",
  from: "Job",
  to: "Son"
}, {
  id: "maj",
  label: "Major Prophets (Isa–Dan)",
  from: "Isa",
  to: "Dan"
}, {
  id: "min",
  label: "Minor Prophets (Hos–Mal)",
  from: "Hos",
  to: "Mal"
}, {
  id: "gos",
  label: "Gospels & Acts (Mat–Act)",
  from: "Mat",
  to: "Act"
}, {
  id: "paul",
  label: "Paul's Letters (Rom–Heb)",
  from: "Rom",
  to: "Heb"
}, {
  id: "gen",
  label: "General Letters (Jas–Jud)",
  from: "Jas",
  to: "Jud"
}, {
  id: "apoc",
  label: "Apocalypse (Rev)",
  from: "Rev",
  to: "Rev"
}];
// Canonical book list (abbrev order) for the from/to pickers.
const SEARCH_BOOK_LIST = Object.keys(BOOK_ORDER);

// Reorder words for natural English reading:
// within each bracket group sort by greek_pos ascending; non-bracket words keep position order.
function getEnglishOrderWords(words) {
  const bracketMap = {};
  for (const w of words) {
    const bid = w.bracket_id;
    if (bid !== null && bid !== undefined) {
      if (!bracketMap[bid]) bracketMap[bid] = [];
      bracketMap[bid].push(w);
    }
  }
  // Trailing punctuation marks a clause boundary in the SOURCE order. After a
  // bracket group is reordered into English order, that punctuation must float
  // to the last word of the reordered group (Greek "were-completed ... earth,"
  // -> English "... earth were-completed,") instead of stranding on "earth".
  const TRAIL = /[.,;:!?·]+$/;
  for (const bid in bracketMap) {
    let trailing = "";
    const cleaned = [];
    for (const w of bracketMap[bid]) {
      const eng = (w.english || "").trim();
      if (eng && eng.replace(TRAIL, "") === "") {
        // pure-punctuation token
        trailing += eng;
        continue;
      }
      const m = eng.match(TRAIL);
      if (m) {
        trailing += m[0];
        cleaned.push({
          ...w,
          english: eng.slice(0, eng.length - m[0].length).trimEnd()
        });
      } else {
        cleaned.push(w);
      }
    }
    cleaned.sort((a, b) => (a.greek_pos ?? 999) - (b.greek_pos ?? 999));
    if (trailing && cleaned.length) {
      // Attach the floated punctuation to the last word that actually has English
      // text. Empty-gloss words (e.g. the σου/αὐτός pronouns folded into a
      // neighboring noun) would otherwise become a standalone "," token, which
      // renders with a stray leading space ("reprove , me") in prose mode.
      let li = cleaned.length - 1;
      while (li > 0 && !(cleaned[li].english || "").trim()) li--;
      cleaned[li] = {
        ...cleaned[li],
        english: (cleaned[li].english || "") + trailing
      };
    }
    bracketMap[bid] = cleaned;
  }
  const result = [];
  const seen = new Set();
  for (const w of words) {
    const bid = w.bracket_id;
    if (bid === null || bid === undefined) {
      result.push(w);
    } else if (!seen.has(bid)) {
      seen.add(bid);
      result.push(...bracketMap[bid]);
    }
  }
  return result;
}

// Group a position-sorted word list into runs by bracket_id for bracket notation rendering.
function groupForGreekMode(words) {
  const groups = [];
  let cur = null;
  for (const w of words) {
    const bid = w.bracket_id !== null && w.bracket_id !== undefined ? w.bracket_id : null;
    if (bid === null) {
      groups.push({
        isBracket: false,
        word: w
      });
      cur = null;
    } else {
      if (!cur || cur.bid !== bid) {
        cur = {
          isBracket: true,
          bid,
          words: []
        };
        groups.push(cur);
      }
      cur.words.push(w);
    }
  }
  return groups;
}

// 59b — Library nav/picker sub-components + the non-canon text list + the
//       restore-from-localStorage helpers, split out of 60-library.jsx.
//       Loads between 59a-library-helpers and 60-library.
//       Holds: LibNavPanel · MobileBookPicker · ModesSheet · _BOOK_DIV ·
//              NONCANON + nonCanonGroups · readLibSaved/readCachedBooks/readCachedChrono.
// ============================================================
// LIB NAV PANEL — desktop left sidebar (≥1100px)
// ============================================================

const _BOOK_DIV = {
  Gen: "Law",
  Exo: "Law",
  Lev: "Law",
  Num: "Law",
  Deu: "Law",
  Jos: "History",
  Jdg: "History",
  Rth: "History",
  "1Sa": "History",
  "2Sa": "History",
  "1Ki": "History",
  "2Ki": "History",
  "1Ch": "History",
  "2Ch": "History",
  Ezr: "History",
  Neh: "History",
  Est: "History",
  Job: "Wisdom",
  Psa: "Wisdom",
  Pro: "Wisdom",
  Ecc: "Wisdom",
  Son: "Wisdom",
  Isa: "Major Prophets",
  Jer: "Major Prophets",
  Lam: "Major Prophets",
  Eze: "Major Prophets",
  Dan: "Major Prophets",
  Hos: "Minor Prophets",
  Joe: "Minor Prophets",
  Amo: "Minor Prophets",
  Oba: "Minor Prophets",
  Jon: "Minor Prophets",
  Mic: "Minor Prophets",
  Nah: "Minor Prophets",
  Hab: "Minor Prophets",
  Zep: "Minor Prophets",
  Hag: "Minor Prophets",
  Zec: "Minor Prophets",
  Mal: "Minor Prophets",
  Mat: "Gospels",
  Mar: "Gospels",
  Luk: "Gospels",
  Joh: "Gospels",
  Act: "History",
  Rom: "Pauline Epistles",
  "1Co": "Pauline Epistles",
  "2Co": "Pauline Epistles",
  Gal: "Pauline Epistles",
  Eph: "Pauline Epistles",
  Php: "Pauline Epistles",
  Col: "Pauline Epistles",
  "1Th": "Pauline Epistles",
  "2Th": "Pauline Epistles",
  "1Ti": "Pauline Epistles",
  "2Ti": "Pauline Epistles",
  Tit: "Pauline Epistles",
  Phm: "Pauline Epistles",
  Heb: "General Epistles",
  Jas: "General Epistles",
  "1Pe": "General Epistles",
  "2Pe": "General Epistles",
  "1Jn": "General Epistles",
  "2Jn": "General Epistles",
  "3Jn": "General Epistles",
  Jud: "General Epistles",
  Rev: "Apocalyptic"
};
function LibNavPanel({
  books,
  selBook,
  setSelBook,
  selChapter,
  setSelChapter,
  isOverlay,
  onClose,
  navBookRef,
  nonCanon,
  nonCanonList,
  onPickNonCanon,
  translation,
  corpus,
  pickBible,
  esvOwner,
  nivOwner,
  hebShown,
  hebPickable,
  otherOpen,
  setOtherOpen,
  chrono,
  orderMode,
  setOrder,
  chronoPos,
  onPickPassage,
  plan
}) {
  const [query, setQuery] = useState("");
  const chronoMode = orderMode === "chronological" && chrono && !nonCanon;
  // The era a passage belongs to, so the active passage's era starts expanded.
  const curEraId = chrono && chrono.passages[chronoPos - 1] ? chrono.passages[chronoPos - 1].era : null;
  const [openEras, setOpenEras] = useState(() => new Set(curEraId ? [curEraId] : []));
  const eraRefs = useRef({});
  const toggleEra = id => setOpenEras(s => {
    const n = new Set(s);
    const opening = !n.has(id);
    opening ? n.add(id) : n.delete(id);
    // On open, scroll the era to the top of the list — only the inner list, never the
    // page (set scrollTop directly, like the Days month scroll).
    if (opening) requestAnimationFrame(() => {
      const el = eraRefs.current[id];
      const sc = el && el.closest(".nav-scroll, .mpick-scroll");
      if (el && sc) sc.scrollTo({
        top: sc.scrollTop + el.getBoundingClientRect().top - sc.getBoundingClientRect().top,
        behavior: "smooth"
      });
    });
    return n;
  });
  const navActiveRef = useRef(null); // the active passage button (scroll into view)
  // Keep the active passage's era open and scroll it into view as you step through.
  useEffect(() => {
    if (!chronoMode || !curEraId) return;
    setOpenEras(s => s.has(curEraId) ? s : new Set(s).add(curEraId));
    requestAnimationFrame(() => navActiveRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest"
    }));
  }, [chronoMode, chronoPos, curEraId]);
  // "Other" menu groups start collapsed (the list is long) — except the group of the
  // text that's currently open, so the active pick stays visible.
  const [openGroups, setOpenGroups] = useState(() => new Set(["Bibles", ...(nonCanon ? [nonCanon.group] : [])]));
  const toggleGroup = g => setOpenGroups(s => {
    const n = new Set(s);
    n.has(g) ? n.delete(g) : n.add(g);
    return n;
  });

  // The "More" popout closes on a click outside it (or Esc) — proper menu behaviour
  // now it floats over the book list instead of sitting inline.
  const sourceWrapRef = useRef(null);
  useEffect(() => {
    if (!otherOpen) return;
    const onDown = e => {
      if (sourceWrapRef.current && !sourceWrapRef.current.contains(e.target)) {
        setOtherOpen(false);
        // Swallow the dismiss click so it doesn't also land on a word chip behind the menu.
        const swallow = ev => {
          ev.stopPropagation();
          ev.preventDefault();
        };
        document.addEventListener("click", swallow, {
          capture: true,
          once: true
        });
        setTimeout(() => document.removeEventListener("click", swallow, {
          capture: true
        }), 350);
      }
    };
    const onKey = e => {
      if (e.key === "Escape") setOtherOpen(false);
    };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [otherOpen, setOtherOpen]);

  // Book accordion: which book's chapter grid is expanded. Starts collapsed (null)
  // — the current chapter shows next to the book name until you open it. Click the
  // open book to collapse it again; click another book to switch + open that one.
  const [navOpenBook, setNavOpenBook] = useState(null);
  const onBookClick = b => {
    if (navOpenBook === b.abbrev) {
      setNavOpenBook(null);
      return;
    } // tap the open book to collapse
    if (!(selBook && b.abbrev === selBook.abbrev)) {
      setSelBook(b);
      setSelChapter(1);
    }
    setNavOpenBook(b.abbrev);
  };
  const filtered = useMemo(() => {
    // Hebrew is OT-only (no Hebrew NT), so drop the NT books from the list in HEB mode.
    const base = translation === "heb" ? books.filter(b => !NT_BOOKS.has(b.abbrev)) : books;
    const q = query.trim().toLowerCase();
    if (!q) return base;
    return base.filter(b => b.name.toLowerCase().includes(q) || b.abbrev.toLowerCase().includes(q));
  }, [books, query, translation]);
  const groups = useMemo(() => {
    const out = [];
    let cur = null;
    for (const b of filtered) {
      const t = NT_BOOKS.has(b.abbrev) ? "NT" : "OT";
      const div = _BOOK_DIV[b.abbrev] || "";
      const key = t + " · " + div;
      if (!cur || cur.key !== key) {
        cur = {
          key,
          t,
          div,
          books: []
        };
        out.push(cur);
      }
      cur.books.push(b);
    }
    return out;
  }, [filtered]);

  // When a non-canonical text is active, the nav shows that text's chapter chips
  // (picking WHICH non-canon text happens via the "Other" menu in the source bar).
  const nonCanonActive = nonCanon ? /*#__PURE__*/React.createElement("div", {
    className: "nav-group"
  }, /*#__PURE__*/React.createElement("div", {
    className: "nav-div"
  }, /*#__PURE__*/React.createElement("span", {
    className: "nav-div-t"
  }, "Other"), /*#__PURE__*/React.createElement("span", {
    className: "nav-div-n"
  }, nonCanon.name)), /*#__PURE__*/React.createElement("div", {
    ref: navBookRef
  }, /*#__PURE__*/React.createElement("button", {
    className: "nav-book on"
  }, /*#__PURE__*/React.createElement("span", {
    className: "nav-book-name"
  }, nonCanon.name)), /*#__PURE__*/React.createElement("div", {
    className: "nav-chips"
  }, Array.from({
    length: nonCanon.chapters
  }, (_, i) => i + 1).map(n => /*#__PURE__*/React.createElement("button", {
    key: n,
    className: "ch-chip" + (n === selChapter ? " on" : ""),
    onClick: () => setSelChapter(n)
  }, n))))) : null;

  // "More" button: ABP/KJV/BSB stay one-click; ESV/NIV/HEB + the non-canon books live
  // in this menu, so the row stays at four buttons no matter how many texts exist.
  const extraActive = !nonCanon && (translation === "esv" || translation === "niv" || translation === "heb");
  const moreActive = !!nonCanon || extraActive;
  const moreLabel = nonCanon ? nonCanon.abbr || nonCanon.name : translation === "esv" ? "ESV" : translation === "niv" ? "NIV" : translation === "heb" ? "HEB" : "More";
  return /*#__PURE__*/React.createElement("nav", {
    className: "nav" + (isOverlay ? " nav-overlay" : ""),
    "aria-label": "Books"
  }, /*#__PURE__*/React.createElement("div", {
    className: "nav-top"
  }, isOverlay && /*#__PURE__*/React.createElement("button", {
    className: "nav-x",
    onClick: onClose,
    "aria-label": "Close"
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    className: "nav-source-wrap",
    ref: sourceWrapRef
  }, /*#__PURE__*/React.createElement("div", {
    className: "nav-source"
  }, /*#__PURE__*/React.createElement("div", {
    className: "seg nav-source-seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (!nonCanon && translation === "abp" ? " on" : ""),
    onClick: () => pickBible("abp")
  }, "ABP"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (!nonCanon && translation === "kjv" ? " on" : ""),
    onClick: () => pickBible("kjv")
  }, "KJV"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (!nonCanon && translation === "bsb" ? " on" : ""),
    onClick: () => pickBible("bsb")
  }, "BSB"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b nav-other-seg" + (moreActive ? " on" : ""),
    onClick: () => setOtherOpen(o => !o),
    "aria-expanded": otherOpen
  }, /*#__PURE__*/React.createElement("span", {
    className: "nav-other-lbl"
  }, moreLabel), /*#__PURE__*/React.createElement("span", {
    className: "nav-other-caret" + (otherOpen ? " open" : "")
  }, "\u25BE")))), otherOpen && /*#__PURE__*/React.createElement("div", {
    className: "nav-other-inline"
  }, (esvOwner || nivOwner || hebShown) && (() => {
    const bibles = [esvOwner && {
      id: "esv",
      name: "ESV"
    }, nivOwner && {
      id: "niv",
      name: "NIV"
    }, hebShown && {
      id: "heb",
      name: "Hebrew OT (interlinear)",
      disabled: !hebPickable,
      title: !hebPickable ? "Old Testament books only" : undefined
    }].filter(Boolean);
    const open = openGroups.has("Bibles");
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
      className: "lib-other-head lib-other-head-btn" + (open ? " open" : ""),
      onClick: () => toggleGroup("Bibles"),
      "aria-expanded": open
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-other-head-caret"
    }, "\u25B8"), /*#__PURE__*/React.createElement("span", {
      className: "lib-other-head-lbl"
    }, "Bibles"), /*#__PURE__*/React.createElement("span", {
      className: "lib-other-head-count"
    }, bibles.length)), open && bibles.map(b => /*#__PURE__*/React.createElement("button", {
      key: b.id,
      className: "lib-other-item" + (!nonCanon && translation === b.id ? " on" : ""),
      disabled: b.disabled,
      title: b.title,
      onClick: () => {
        pickBible(b.id);
        setOtherOpen(false);
        if (isOverlay) onClose();
      }
    }, b.name)));
  })(), nonCanonList && nonCanonList.length > 0 && nonCanonGroups(nonCanonList).map(grp => {
    const open = openGroups.has(grp.group);
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: grp.group
    }, /*#__PURE__*/React.createElement("button", {
      className: "lib-other-head lib-other-head-btn" + (open ? " open" : ""),
      onClick: () => toggleGroup(grp.group),
      "aria-expanded": open
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-other-head-caret"
    }, "\u25B8"), /*#__PURE__*/React.createElement("span", {
      className: "lib-other-head-lbl"
    }, grp.group), /*#__PURE__*/React.createElement("span", {
      className: "lib-other-head-count"
    }, grp.items.length)), open && grp.items.map(t => /*#__PURE__*/React.createElement("button", {
      key: t.id,
      className: "lib-other-item" + (nonCanon && nonCanon.id === t.id ? " on" : ""),
      onClick: () => {
        onPickNonCanon(t);
        setOtherOpen(false);
        if (isOverlay) onClose();
      }
    }, t.name)));
  }))), chronoMode && plan ? /*#__PURE__*/React.createElement("div", {
    className: "nav-plan"
  }, /*#__PURE__*/React.createElement("div", {
    className: "plan-toggle"
  }, /*#__PURE__*/React.createElement("button", {
    className: "plan-toggle-b" + (plan.view !== "days" ? " on" : ""),
    onClick: () => plan.setView("eras")
  }, "Eras"), /*#__PURE__*/React.createElement("button", {
    className: "plan-toggle-b" + (plan.view === "days" ? " on" : ""),
    onClick: () => plan.setView("days")
  }, "Days")), plan.view === "days" ? /*#__PURE__*/React.createElement(DayPlanView, {
    chrono: chrono,
    curText: plan.curText,
    texts: plan.texts,
    progAll: plan.progAll,
    chronoPos: chronoPos,
    onPickText: plan.onPickText,
    onToggleDone: plan.onToggleDone,
    onPickPassage: p => {
      onPickPassage(p);
      if (isOverlay) onClose();
    }
  }) : /*#__PURE__*/React.createElement("div", {
    className: "nav-scroll nav-plan-scroll"
  }, /*#__PURE__*/React.createElement("div", {
    className: "nav-eras-inner"
  }, chrono.eras.map(era => {
    const open = openEras.has(era.id);
    const eraPassages = chrono.passages.filter(p => p.era === era.id);
    return /*#__PURE__*/React.createElement("div", {
      className: "nav-group",
      key: era.id,
      ref: el => {
        if (el) eraRefs.current[era.id] = el;
      }
    }, /*#__PURE__*/React.createElement("button", {
      className: "nav-era" + (open ? " open" : ""),
      onClick: () => toggleEra(era.id),
      "aria-expanded": open,
      title: era.blurb
    }, /*#__PURE__*/React.createElement("span", {
      className: "nav-era-name"
    }, era.name), /*#__PURE__*/React.createElement("span", {
      className: "nav-era-count"
    }, eraPassages.length)), open && /*#__PURE__*/React.createElement("div", {
      className: "nav-passages"
    }, eraPassages.map(p => {
      const active = p.pos === chronoPos;
      return /*#__PURE__*/React.createElement("button", {
        key: p.pos,
        ref: active ? navActiveRef : null,
        className: "nav-passage" + (active ? " on" : ""),
        onClick: () => {
          onPickPassage(p);
          if (isOverlay) onClose();
        }
      }, p.label);
    })));
  })))) : /*#__PURE__*/React.createElement("div", {
    className: "nav-scroll"
  }, nonCanon && nonCanonActive, !nonCanon && groups.map((g, gi) => {
    // Show the OT/NT tag only when the testament changes (once at the top,
    // once at the OT→NT boundary) — repeating it on every group was noise.
    const newTestament = gi === 0 || groups[gi - 1].t !== g.t;
    const tClass = g.t === "OT" ? " nav-group--ot" : g.t === "NT" ? " nav-group--nt" : "";
    return /*#__PURE__*/React.createElement("div", {
      className: "nav-group" + (newTestament ? " nav-group--tnew" : "") + tClass,
      key: g.key
    }, newTestament && /*#__PURE__*/React.createElement("div", {
      className: "nav-testament"
    }, g.t === "OT" ? "Old Testament" : "New Testament"), /*#__PURE__*/React.createElement("div", {
      className: "nav-div"
    }, /*#__PURE__*/React.createElement("span", {
      className: "nav-div-n"
    }, g.div)), g.books.map(b => {
      const active = !nonCanon && selBook && b.abbrev === selBook.abbrev;
      const open = navOpenBook === b.abbrev;
      return /*#__PURE__*/React.createElement("div", {
        key: b.abbrev,
        ref: active ? navBookRef : null
      }, /*#__PURE__*/React.createElement("button", {
        className: "nav-book" + (active ? " on" : "") + (open ? " open" : ""),
        onClick: () => onBookClick(b),
        "aria-expanded": open
      }, /*#__PURE__*/React.createElement("span", {
        className: "nav-book-name"
      }, b.name), active && !open && /*#__PURE__*/React.createElement("span", {
        className: "nav-book-ch"
      }, selChapter), !open && /*#__PURE__*/React.createElement("span", {
        className: "nav-book-count"
      }, b.chapters)), open && /*#__PURE__*/React.createElement("div", {
        className: "nav-chips"
      }, Array.from({
        length: b.chapters
      }, (_, i) => i + 1).map(n => /*#__PURE__*/React.createElement("button", {
        key: n,
        className: "ch-chip" + (n === selChapter ? " on" : ""),
        onClick: () => {
          setSelChapter(n);
          if (isOverlay) onClose();
        }
      }, n))));
    }));
  })));
}

// ============================================================
// MOBILE BOOK PICKER — full-screen, two-screen (book grid → chapter grid)
// ============================================================
function MobileBookPicker({
  books,
  selBook,
  selChapter,
  nonCanon,
  nonCanonList,
  onDone,
  onClose,
  chronoOn,
  chrono,
  chronoPos,
  onPickPassage,
  onPickPassageNoClose,
  translation,
  plan
}) {
  // A non-canonical book is identified by its `id`; a Bible book by its `abbrev`.
  const isNC = b => !!(b && b.id);
  // Chronological: the picker shows eras → passages instead of books → chapters.
  const curEraId = chrono && chrono.passages[chronoPos - 1] ? chrono.passages[chronoPos - 1].era : null;
  const [openEras, setOpenEras] = useState(() => new Set(curEraId ? [curEraId] : []));
  const eraRefs = useRef({});
  const toggleEra = id => setOpenEras(s => {
    const n = new Set(s);
    const opening = !n.has(id);
    opening ? n.add(id) : n.delete(id);
    // On open, scroll the era to the top of the list — only the inner list, never the
    // page (set scrollTop directly, like the Days month scroll).
    if (opening) requestAnimationFrame(() => {
      const el = eraRefs.current[id];
      const sc = el && el.closest(".nav-scroll, .mpick-scroll");
      if (el && sc) sc.scrollTo({
        top: sc.scrollTop + el.getBoundingClientRect().top - sc.getBoundingClientRect().top,
        behavior: "smooth"
      });
    });
    return n;
  });
  // Open straight to the chapter grid of whatever you're currently reading — an open
  // non-canonical text OR the current Bible book — so you can change chapter right away
  // instead of landing on the generic book list. "‹ Books" steps back to switch books.
  const startBook = nonCanon || selBook || null;
  // Open to the book list, not the chapter grid — picking a book steps into chapters.
  const [screen, setScreen] = useState("book");
  const [pickedBook, setPickedBook] = useState(startBook);
  // Every section (OT, NT, and each non-canonical group) starts collapsed EXCEPT the
  // one you're currently reading: the testament of the open Bible book, or the active
  // non-canonical text's group.
  const [openGroups, setOpenGroups] = useState(() => new Set([nonCanon ? nonCanon.group : selBook && NT_BOOKS.has(selBook.abbrev) ? "NT" : "OT"]));
  const toggleGroup = g => setOpenGroups(s => {
    const n = new Set(s);
    n.has(g) ? n.delete(g) : n.add(g);
    return n;
  });
  // Same swipe-down-to-close + at-top scroll arming as the hero / xref sheets.
  // ONE stable root so the refs survive the book→chapter screen switch.
  const {
    sheetRef,
    scrollRef
  } = useSwipeToDismiss(onClose);

  // Hebrew is OT-only (no Hebrew NT), so drop the NT section in HEB mode — mirrors the
  // desktop nav's `filtered` useMemo.
  const otBooks = books.filter(b => !NT_BOOKS.has(b.abbrev));
  const ntBooks = translation === "heb" ? [] : books.filter(b => NT_BOOKS.has(b.abbrev));
  const onChapter = screen === "chapter";
  const isActive = b => isNC(b) ? nonCanon && nonCanon.id === b.id : selBook && b.abbrev === selBook.abbrev;
  return /*#__PURE__*/React.createElement("div", {
    className: "mpick",
    ref: sheetRef
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet-drag-zone",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet-handle"
  })), /*#__PURE__*/React.createElement("div", {
    className: "mpick-head"
  }, !chronoOn && onChapter ? /*#__PURE__*/React.createElement("button", {
    className: "mpick-back",
    onClick: () => setScreen("book")
  }, "\u2039 Books") : /*#__PURE__*/React.createElement("span", {
    className: "mpick-head-spacer"
  }), /*#__PURE__*/React.createElement("span", {
    className: "mpick-title"
  }, chronoOn ? "Chronological" : onChapter ? pickedBook.name : "Books"), /*#__PURE__*/React.createElement("button", {
    className: "mpick-x",
    onClick: onClose
  }, "\u2715")), chronoOn && plan && /*#__PURE__*/React.createElement("div", {
    className: "plan-toggle mpick-toggle"
  }, /*#__PURE__*/React.createElement("button", {
    className: "plan-toggle-b" + (plan.view !== "days" ? " on" : ""),
    onClick: () => plan.setView("eras")
  }, "Eras"), /*#__PURE__*/React.createElement("button", {
    className: "plan-toggle-b" + (plan.view === "days" ? " on" : ""),
    onClick: () => plan.setView("days")
  }, "Days")), /*#__PURE__*/React.createElement("div", {
    className: "mpick-scroll" + (chronoOn && plan && plan.view === "days" ? " mpick-scroll--plan" : ""),
    ref: scrollRef
  }, chronoOn ? plan && plan.view === "days" ? /*#__PURE__*/React.createElement(DayPlanView, {
    isMobile: true,
    chrono: chrono,
    curText: plan.curText,
    texts: plan.texts,
    progAll: plan.progAll,
    chronoPos: chronoPos,
    onPickText: plan.onPickText,
    onToggleDone: plan.onToggleDone,
    onPickPassage: onPickPassageNoClose || onPickPassage
  }) : chrono.eras.map(era => {
    const open = openEras.has(era.id);
    const eraPassages = chrono.passages.filter(p => p.era === era.id);
    return /*#__PURE__*/React.createElement("div", {
      key: era.id,
      className: "mpick-section",
      ref: el => {
        if (el) eraRefs.current[era.id] = el;
      }
    }, /*#__PURE__*/React.createElement("button", {
      className: "mpick-sec-label mpick-sec-btn" + (open ? " open" : ""),
      onClick: () => toggleEra(era.id),
      "aria-expanded": open
    }, /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-caret"
    }, "\u25B8"), /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-name"
    }, era.name), /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-count"
    }, eraPassages.length)), open && /*#__PURE__*/React.createElement("div", {
      className: "mpick-passages"
    }, eraPassages.map(p => /*#__PURE__*/React.createElement("button", {
      key: p.pos,
      className: "mpick-passage" + (p.pos === chronoPos ? " on" : ""),
      onClick: () => onPickPassage(p)
    }, p.label))));
  }) : onChapter ? /*#__PURE__*/React.createElement("div", {
    className: "mpick-grid"
  }, Array.from({
    length: pickedBook.chapters
  }, (_, i) => i + 1).map(n => {
    const active = isActive(pickedBook) && n === selChapter;
    return /*#__PURE__*/React.createElement("button", {
      key: n,
      className: "mpick-btn" + (active ? " on" : ""),
      onClick: () => onDone(pickedBook, n)
    }, n);
  })) : [["OT", otBooks], ["NT", ntBooks]].filter(([, bks]) => bks.length).map(([label, bks]) => {
    const open = openGroups.has(label);
    return /*#__PURE__*/React.createElement("div", {
      key: label,
      className: "mpick-section"
    }, /*#__PURE__*/React.createElement("button", {
      className: "mpick-sec-label mpick-sec-btn" + (open ? " open" : ""),
      onClick: () => toggleGroup(label),
      "aria-expanded": open
    }, /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-caret"
    }, "\u25B8"), /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-name"
    }, label), /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-count"
    }, bks.length)), open && /*#__PURE__*/React.createElement("div", {
      className: "mpick-grid"
    }, bks.map(b => /*#__PURE__*/React.createElement("button", {
      key: b.abbrev,
      className: "mpick-btn" + (isActive(b) ? " on" : ""),
      onClick: () => {
        setPickedBook(b);
        setScreen("chapter");
      }
    }, b.abbrev.toUpperCase()))));
  }).concat((nonCanonList || []).length ? nonCanonGroups(nonCanonList).map(grp => {
    const open = openGroups.has(grp.group);
    return /*#__PURE__*/React.createElement("div", {
      key: grp.group,
      className: "mpick-section"
    }, /*#__PURE__*/React.createElement("button", {
      className: "mpick-sec-label mpick-sec-btn" + (open ? " open" : ""),
      onClick: () => toggleGroup(grp.group),
      "aria-expanded": open
    }, /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-caret"
    }, "\u25B8"), /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-name"
    }, grp.group), /*#__PURE__*/React.createElement("span", {
      className: "mpick-sec-count"
    }, grp.items.length)), open && /*#__PURE__*/React.createElement("div", {
      className: "mpick-grid"
    }, grp.items.map(t => /*#__PURE__*/React.createElement("button", {
      key: t.id,
      className: "mpick-btn mpick-btn-nc" + (isActive(t) ? " on" : ""),
      onClick: () => {
        setPickedBook(t);
        setScreen("chapter");
      }
    }, t.name))));
  }) : [])));
}

// ============================================================
// MOBILE READING OPTIONS — bottom sheet (swipe-to-dismiss, scrollable).
// Compacted to three groups: Text · Study layer · Display.
// ============================================================
function ModesSheet({
  corpus,
  translation,
  pickBible,
  esvOwner,
  nivOwner,
  hebShown,
  hebPickable,
  toggleParallel,
  nonCanonList,
  compareAvail,
  compareActive,
  toggleCompare,
  showStrongs,
  showInterlinear,
  setOpt,
  chipMode,
  viewMode,
  libFontSize,
  changeFontSize,
  onClose,
  chrono,
  orderMode,
  setOrder,
  theme,
  setTheme
}) {
  const {
    sheetRef,
    scrollRef
  } = useSwipeToDismiss(onClose);
  const activeNonCanon = nonCanonList.find(t => t.id === corpus) || null;
  const proseLocked = !!(activeNonCanon && activeNonCanon.englishOnly) || translation === "esv" || translation === "niv"; // English-only / ESV / NIV: no Greek toggles (BSB has its own per-word Strong's data)
  const hebMode = translation === "heb"; // Hebrew interlinear: always chips, no prose option
  const gray = proseLocked ? {
    opacity: 0.35,
    cursor: "default"
  } : undefined;
  // English-only "other books": Greek toggles stay locked, but line-vs-flow is allowed.
  const extraEnglish = !!(activeNonCanon && activeNonCanon.englishOnly);
  const layoutLocked = proseLocked && !extraEnglish;
  const viewChipOn = hebMode ? true : extraEnglish ? viewMode === "chip" : chipMode;
  // Text picker gestures: a TAP swaps to that single Bible; a LONG-PRESS (or right-click)
  // ticks it into / out of the side-by-side compare set. One shared timer is fine (touches
  // happen one at a time); the `fired` flag stops a long-press from also firing the tap.
  const pressRef = useRef({
    timer: null,
    fired: false
  });
  const pickHandlers = id => ({
    onClick: () => {
      if (pressRef.current.fired) {
        pressRef.current.fired = false;
        return;
      }
      pickBible(id);
    },
    onContextMenu: e => {
      e.preventDefault();
      toggleCompare(id);
    },
    onTouchStart: () => {
      const st = pressRef.current;
      st.fired = false;
      clearTimeout(st.timer);
      st.timer = setTimeout(() => {
        st.fired = true;
        toggleCompare(id);
        if (navigator.vibrate) navigator.vibrate(12);
      }, 500);
    },
    onTouchMove: () => clearTimeout(pressRef.current.timer),
    onTouchEnd: () => clearTimeout(pressRef.current.timer)
  });
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "sheet-scrim",
    onClick: onClose
  }), /*#__PURE__*/React.createElement("div", {
    className: "msheet",
    ref: sheetRef
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet-drag-zone",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("div", {
    className: "sheet-handle"
  })), /*#__PURE__*/React.createElement("div", {
    className: "msheet-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "msheet-title"
  }, "Reading"), /*#__PURE__*/React.createElement("button", {
    className: "msheet-x",
    onClick: onClose,
    "aria-label": "Close"
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    className: "msheet-body",
    ref: scrollRef
  }, /*#__PURE__*/React.createElement("div", {
    className: "mode-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mode-lbl"
  }, "Text"), activeNonCanon ?
  /*#__PURE__*/
  /* Reading a non-canonical text: ABP/KJV/etc just jump back to the Bible. */
  React.createElement("div", {
    className: "mseg text-ed"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (corpus === "bible" && translation === "abp" ? " on" : ""),
    onClick: () => pickBible("abp")
  }, "ABP"), /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (corpus === "bible" && translation === "kjv" ? " on" : ""),
    onClick: () => pickBible("kjv")
  }, "KJV"), /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (corpus === "bible" && translation === "bsb" ? " on" : ""),
    onClick: () => pickBible("bsb")
  }, "BSB"), esvOwner && /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (corpus === "bible" && translation === "esv" ? " on" : ""),
    onClick: () => pickBible("esv")
  }, "ESV"), nivOwner && /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (corpus === "bible" && translation === "niv" ? " on" : ""),
    onClick: () => pickBible("niv")
  }, "NIV")) :
  /*#__PURE__*/
  /* Bible: one checkable row — tick 1 to read it, 2-4 to compare side by side.
     compareActive + toggleCompare already do the read/compare switching. HEB
     rides in the same row but is single-read only (no compare gesture); the
     row wraps to a 2nd line when there are enough texts. When HEB is the read,
     none of the compare buttons are "on" (compareActive falls back to abp). */
  React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "mode-hint"
  }, "Tap to read \xB7 long-press to compare"), /*#__PURE__*/React.createElement("div", {
    className: "mseg text-ed text-pick"
  }, compareAvail.map(id => {
    const on = translation !== "heb" && compareActive.includes(id);
    return /*#__PURE__*/React.createElement("button", _extends({
      key: id,
      className: "mseg-b" + (on ? " on" : ""),
      "aria-pressed": on
    }, pickHandlers(id)), on && /*#__PURE__*/React.createElement("span", {
      className: "mseg-chk",
      "aria-hidden": "true"
    }, "\u2713"), id.toUpperCase());
  }), hebShown && /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (translation === "heb" ? " on" : ""),
    "aria-pressed": translation === "heb",
    disabled: !hebPickable,
    style: !hebPickable ? {
      opacity: 0.35,
      cursor: "default"
    } : undefined,
    "aria-label": "Hebrew OT interlinear",
    onContextMenu: e => e.preventDefault(),
    onClick: () => {
      if (hebPickable) pickBible("heb");
    }
  }, translation === "heb" && /*#__PURE__*/React.createElement("span", {
    className: "mseg-chk",
    "aria-hidden": "true"
  }, "\u2713"), "HEB")))), chrono && !activeNonCanon && /*#__PURE__*/React.createElement("div", {
    className: "mode-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mode-lbl"
  }, "Order"), /*#__PURE__*/React.createElement("div", {
    className: "mseg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (orderMode !== "chronological" ? " on" : ""),
    "aria-pressed": orderMode !== "chronological",
    onClick: () => setOrder("canonical")
  }, "Canonical"), /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (orderMode === "chronological" ? " on" : ""),
    disabled: translation === "heb",
    "aria-pressed": orderMode === "chronological",
    style: translation === "heb" ? {
      opacity: 0.4,
      cursor: "default"
    } : undefined,
    onClick: () => translation !== "heb" && setOrder("chronological")
  }, "Chronological"))), /*#__PURE__*/React.createElement("div", {
    className: "mode-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mode-lbl"
  }, "Study layer"), /*#__PURE__*/React.createElement("div", {
    className: "mseg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (showStrongs ? " on" : ""),
    disabled: proseLocked,
    style: gray,
    "aria-pressed": showStrongs,
    onClick: () => !proseLocked && setOpt("showStrongs", !showStrongs)
  }, "Strong's"), /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (showInterlinear ? " on" : ""),
    disabled: proseLocked,
    style: gray,
    "aria-pressed": showInterlinear,
    onClick: () => !proseLocked && setOpt("showInterlinear", !showInterlinear)
  }, "Interlinear"))), /*#__PURE__*/React.createElement("div", {
    className: "mode-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mode-lbl"
  }, "Display"), /*#__PURE__*/React.createElement("div", {
    className: "display-row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mseg mseg-view"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (viewChipOn ? " on" : ""),
    disabled: layoutLocked,
    style: layoutLocked ? {
      opacity: 0.35,
      cursor: "default"
    } : undefined,
    title: extraEnglish ? "Line-by-line view" : "Chip view",
    "aria-label": extraEnglish ? "Line-by-line view" : "Chip view",
    "aria-pressed": viewChipOn,
    onClick: () => !layoutLocked && setOpt("viewMode", "chip")
  }, /*#__PURE__*/React.createElement(Icon.Grid, null)), /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (!viewChipOn ? " on" : ""),
    disabled: hebMode || !extraEnglish && !proseLocked && (showStrongs || showInterlinear),
    style: hebMode || !extraEnglish && !proseLocked && (showStrongs || showInterlinear) ? {
      opacity: 0.35
    } : undefined,
    title: "Prose view",
    "aria-label": "Prose view",
    "aria-pressed": !viewChipOn,
    onClick: () => {
      if (hebMode) return;
      if (extraEnglish) {
        setOpt("viewMode", "prose");
        return;
      }
      if (!showStrongs && !showInterlinear) setOpt("viewMode", "prose");
    }
  }, /*#__PURE__*/React.createElement(Icon.Lines, null))), /*#__PURE__*/React.createElement("div", {
    className: "mseg font-picker"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mseg-b",
    onClick: () => changeFontSize(-1)
  }, "A\u2212"), /*#__PURE__*/React.createElement("span", {
    className: "font-size-lbl"
  }, libFontSize), /*#__PURE__*/React.createElement("button", {
    className: "mseg-b",
    onClick: () => changeFontSize(+1)
  }, "A+")))), /*#__PURE__*/React.createElement("div", {
    className: "mode-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mode-lbl"
  }, "Theme"), /*#__PURE__*/React.createElement("div", {
    className: "mseg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (theme === "light" ? " on" : ""),
    "aria-pressed": theme === "light",
    onClick: () => setTheme("light")
  }, "Light"), /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (theme === "sepia" ? " on" : ""),
    "aria-pressed": theme === "sepia",
    onClick: () => setTheme("sepia")
  }, "Sepia"), /*#__PURE__*/React.createElement("button", {
    className: "mseg-b" + (theme === "dark" ? " on" : ""),
    "aria-pressed": theme === "dark",
    onClick: () => setTheme("dark")
  }, "Dark"))))));
}

// Non-canonical texts — reached via the "Other" pick, walled off from the Bible
// book list, search, and lexicon counts. Each rides its own backend route + tables.
// Add future early-church / apocryphal texts here.
const NONCANON = [
// abbr = short label for the mobile toolbar pill (standard scholarly short forms).
// group = section heading in the "Other" menus (kept in array order).
// englishOnly: no Greek interlinear in our pipeline, so the reader stays in Prose
// (chip / parallel-Greek views would be blank). Drop the flag once a tagged Greek
// file is added (e.g. 1 Enoch ch 1–32 from the Akhmim papyrus).
// Group order = nearness to the canon / era: Septuagint Apocrypha (inside the Greek
// OT world) -> Pseudepigrapha -> Testaments -> Apostolic Fathers (early Christian).

// Septuagint Apocrypha — Brenton's 1851 public-domain English LXX (ebible.org USFM),
// verse-perfect. English-only; the Greek isn't Strong's-tagged so no interlinear.
{
  id: "esdras1",
  name: "1 Esdras",
  abbr: "1Esd",
  chapters: 9,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "tobit",
  name: "Tobit",
  abbr: "Tob",
  chapters: 14,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "judith",
  name: "Judith",
  abbr: "Jdt",
  chapters: 16,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "esther_gk",
  name: "Esther (Greek)",
  abbr: "EsG",
  chapters: 10,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "maccabees1",
  name: "1 Maccabees",
  abbr: "1Mac",
  chapters: 16,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "maccabees2",
  name: "2 Maccabees",
  abbr: "2Mac",
  chapters: 15,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "maccabees3",
  name: "3 Maccabees",
  abbr: "3Mac",
  chapters: 7,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "maccabees4",
  name: "4 Maccabees",
  abbr: "4Mac",
  chapters: 18,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "wisdom",
  name: "Wisdom of Solomon",
  abbr: "Wis",
  chapters: 19,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "sirach",
  name: "Sirach",
  abbr: "Sir",
  chapters: 51,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "baruch",
  name: "Baruch",
  abbr: "Bar",
  chapters: 5,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "epjeremiah",
  name: "Letter of Jeremiah",
  abbr: "EpJer",
  chapters: 1,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "susanna",
  name: "Susanna",
  abbr: "Sus",
  chapters: 1,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "bel",
  name: "Bel and the Dragon",
  abbr: "Bel",
  chapters: 1,
  englishOnly: true,
  group: "Septuagint Apocrypha"
}, {
  id: "manasseh",
  name: "Prayer of Manasseh",
  abbr: "PrMan",
  chapters: 1,
  englishOnly: true,
  group: "Septuagint Apocrypha"
},
// Pseudepigrapha — Second Temple Jewish texts (R.H. Charles et al., public domain).
// 2 Esdras (= 4 Ezra) is the great Jewish apocalypse; not in the Greek LXX, so it sits
// here rather than with the Septuagint Apocrypha. WEB Apocrypha (public domain) English.
{
  id: "esdras2",
  name: "2 Esdras (4 Ezra)",
  abbr: "2Esd",
  chapters: 16,
  englishOnly: true,
  group: "Pseudepigrapha"
}, {
  id: "enoch",
  name: "1 Enoch",
  abbr: "1En",
  chapters: 108,
  englishOnly: true,
  group: "Pseudepigrapha"
}, {
  id: "enoch2",
  name: "2 Enoch",
  abbr: "2En",
  chapters: 68,
  englishOnly: true,
  group: "Pseudepigrapha"
}, {
  id: "jubilees",
  name: "Jubilees",
  abbr: "Jub",
  chapters: 50,
  englishOnly: true,
  group: "Pseudepigrapha"
}, {
  id: "baruch2",
  name: "2 Baruch",
  abbr: "2Bar",
  chapters: 85,
  englishOnly: true,
  group: "Pseudepigrapha"
},
// 3 Baruch / Greek Apocalypse of Baruch (Charles APOT, public domain) -- 17 ch + Prologue (ch 0).
{
  id: "baruch3",
  name: "3 Baruch",
  abbr: "3Bar",
  chapters: 17,
  englishOnly: true,
  group: "Pseudepigrapha"
}, {
  id: "apocabr",
  name: "Apocalypse of Abraham",
  abbr: "ApAb",
  chapters: 32,
  englishOnly: true,
  group: "Pseudepigrapha"
},
// chapter-level only: no freely-reachable copy is versified (see parse_assummoses.py)
{
  id: "assummoses",
  name: "Assumption of Moses",
  abbr: "AsMos",
  chapters: 12,
  englishOnly: true,
  group: "Pseudepigrapha"
},
// Latin Vita Adae et Evae (Charles APOT, public domain) -- 51 chapters.
{
  id: "adameve",
  name: "Life of Adam and Eve",
  abbr: "LAE",
  chapters: 51,
  englishOnly: true,
  group: "Pseudepigrapha"
},
// Psalms of Solomon (G.B. Gray, Charles APOT, public domain) -- 18 psalms.
{
  id: "psolomon",
  name: "Psalms of Solomon",
  abbr: "PsSol",
  chapters: 18,
  englishOnly: true,
  group: "Pseudepigrapha"
},
// Letter of Aristeas (H.T. Andrews, Charles APOT, public domain) -- one letter, cited by
// section 1-322 (loaded as a single chapter whose verses are the section numbers).
{
  id: "aristeas",
  name: "Letter of Aristeas",
  abbr: "Arist",
  chapters: 1,
  englishOnly: true,
  group: "Pseudepigrapha"
},
// Ascension of Isaiah (R.H. Charles, public domain) -- Martyrdom (1-5) + Vision (6-11).
{
  id: "ascisaiah",
  name: "Ascension of Isaiah",
  abbr: "AscIsa",
  chapters: 11,
  englishOnly: true,
  group: "Pseudepigrapha"
},
// Sibylline Oracles (Milton Terry, public domain) -- chapter = book, verse = line. The
// collection numbers its books 1-8 and 11-14 (chapters 9 & 10 carry a "no such book" note).
{
  id: "sibylline",
  name: "Sibylline Oracles",
  abbr: "SibOr",
  chapters: 14,
  englishOnly: true,
  group: "Pseudepigrapha"
},
// Testaments of the Twelve Patriarchs (R.H. Charles, APOT) -- twelve short books,
// each cited on its own (T. Reuben 1:1 ...), so each is a separate entry.
{
  id: "treuben",
  name: "Testament of Reuben",
  abbr: "TReu",
  chapters: 7,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tsimeon",
  name: "Testament of Simeon",
  abbr: "TSim",
  chapters: 9,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tlevi",
  name: "Testament of Levi",
  abbr: "TLevi",
  chapters: 19,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tjudah",
  name: "Testament of Judah",
  abbr: "TJud",
  chapters: 26,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tissachar",
  name: "Testament of Issachar",
  abbr: "TIss",
  chapters: 7,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tzebulun",
  name: "Testament of Zebulun",
  abbr: "TZeb",
  chapters: 10,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tdan",
  name: "Testament of Dan",
  abbr: "TDan",
  chapters: 7,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tnaphtali",
  name: "Testament of Naphtali",
  abbr: "TNaph",
  chapters: 9,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tgad",
  name: "Testament of Gad",
  abbr: "TGad",
  chapters: 8,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tasher",
  name: "Testament of Asher",
  abbr: "TAsh",
  chapters: 8,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tjoseph",
  name: "Testament of Joseph",
  abbr: "TJos",
  chapters: 20,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
}, {
  id: "tbenjamin",
  name: "Testament of Benjamin",
  abbr: "TBen",
  chapters: 12,
  englishOnly: true,
  group: "Testaments (12 Patriarchs)"
},
// Apostolic Fathers — Greek-tagged interlinear (Brannan/Lake Greek + Lightfoot English).
// NOT englishOnly: these have the full Greek word-study layer like the Bible text.
// Traditional reading order. (Polycarp ch 10-14 survive only in Latin -> English
// shows there, no Greek chips.)
{
  id: "clement1",
  name: "1 Clement",
  abbr: "1Clem",
  chapters: 65,
  group: "Apostolic Fathers"
}, {
  id: "clement2",
  name: "2 Clement",
  abbr: "2Clem",
  chapters: 20,
  group: "Apostolic Fathers"
}, {
  id: "ign_eph",
  name: "Ignatius to the Ephesians",
  abbr: "IgEph",
  chapters: 21,
  group: "Apostolic Fathers"
}, {
  id: "ign_mag",
  name: "Ignatius to the Magnesians",
  abbr: "IgMag",
  chapters: 15,
  group: "Apostolic Fathers"
}, {
  id: "ign_tral",
  name: "Ignatius to the Trallians",
  abbr: "IgTra",
  chapters: 13,
  group: "Apostolic Fathers"
}, {
  id: "ign_rom",
  name: "Ignatius to the Romans",
  abbr: "IgRom",
  chapters: 10,
  group: "Apostolic Fathers"
}, {
  id: "ign_phld",
  name: "Ignatius to the Philadelphians",
  abbr: "IgPhl",
  chapters: 11,
  group: "Apostolic Fathers"
}, {
  id: "ign_smyrn",
  name: "Ignatius to the Smyrnaeans",
  abbr: "IgSmy",
  chapters: 13,
  group: "Apostolic Fathers"
}, {
  id: "ign_pol",
  name: "Ignatius to Polycarp",
  abbr: "IgPol",
  chapters: 8,
  group: "Apostolic Fathers"
}, {
  id: "polycarp",
  name: "Polycarp to the Philippians",
  abbr: "Pol",
  chapters: 14,
  group: "Apostolic Fathers"
}, {
  id: "mpolycarp",
  name: "Martyrdom of Polycarp",
  abbr: "MPol",
  chapters: 22,
  group: "Apostolic Fathers"
}, {
  id: "barnabas",
  name: "Epistle of Barnabas",
  abbr: "Barn",
  chapters: 21,
  group: "Apostolic Fathers"
}, {
  id: "didache",
  name: "Didache",
  abbr: "Did",
  chapters: 16,
  group: "Apostolic Fathers"
}, {
  id: "diognetus",
  name: "Epistle to Diognetus",
  abbr: "Diog",
  chapters: 12,
  group: "Apostolic Fathers"
}, {
  id: "shepherd",
  name: "Shepherd of Hermas",
  abbr: "Herm",
  chapters: 110,
  group: "Apostolic Fathers"
}];

// Group NONCANON entries by their `group` label, preserving array order, for the
// section-headed "Other" menus (nav source-picker dropdown + mobile sheet).
function nonCanonGroups(list) {
  const out = [];
  let cur = null;
  for (const t of list) {
    const g = t.group || "Other";
    if (!cur || cur.group !== g) {
      cur = {
        group: g,
        items: []
      };
      out.push(cur);
    }
    cur.items.push(t);
  }
  return out;
}

// ============================================================
// LIBRARY VIEW
// ============================================================
// The saved library spot (lexica.lib.v1), read once. Used by the state initializers so the
// reading order / text / compare / book-chapter / corpus all restore at the FIRST paint — no
// default→saved flicker (e.g. the mobile bottom selector flashing chapter "1" before the real one).
function readLibSaved() {
  try {
    return JSON.parse(localStorage.getItem("lexica.lib.v1") || "null");
  } catch (e) {
    return null;
  }
}
// The book list is tiny + stable (the canon), so we cache it. Reading it back at init lets the book
// NAME render on the FIRST paint instead of popping in after api.books() returns; the fetch still
// runs and refreshes the cache.
function readCachedBooks() {
  try {
    const c = JSON.parse(localStorage.getItem("lexica.books.v1") || "null");
    return Array.isArray(c) ? c : [];
  } catch (e) {
    return [];
  }
}
// Same idea for the chronological list (a ~255KB static file). Caching it lets the
// chrono passage label paint on the FIRST frame after a refresh — without it, `chrono`
// is null until the fetch lands, so chronoOn is briefly false and the mobile toolbar
// flashes the canonical book/chapter before flipping to the passage label.
function readCachedChrono() {
  try {
    const c = JSON.parse(localStorage.getItem("lexica.chrono.v1") || "null");
    return c && Array.isArray(c.passages) ? c : null;
  } catch (e) {
    return null;
  }
}

// ============================================================
// LIBRARY RENDER HELPERS — the verse renderers lifted out of LibraryView
// (60-library.jsx) to keep that file manageable. Each function takes a `ctx`
// bundle of the live values it needs from LibraryView (current book/chapter,
// the note/highlight helpers, the chip/Strong's/interlinear toggles,
// onWordClick, the highlight/press refs...). LibraryView builds `ctx` once per
// render and binds thin wrappers around these, so its call sites read unchanged.
// Pure relocation — no behavior change. Globals used here (React, Icon,
// getEnglishOrderWords, groupForGreekMode, wordEntryCore,
// strongsTag) all live in earlier files (00/10/59a).
// ============================================================
const LibRender = function () {
  const joinProse = words => {
    const tokens = words.map(w => w.english).filter(Boolean);
    return tokens.reduce((acc, tok, i) => {
      if (i === 0) return tok;
      return /^[.,;:?!—)]/.test(tok) ? acc + tok : acc + " " + tok;
    }, "");
  };
  const renderProseWords = (ctx, v, opts = {}) => {
    const {
      selChapter,
      hiClass
    } = ctx;
    // tightSpace: emit the inter-word space OUTSIDE the word's span. The reader leaves it
    // INSIDE (default) so a multi-word highlight paints as one continuous bar; the
    // Search/Lexicon result lists set it so a single-word match highlight hugs just the
    // word — a trailing space caught inside the gold makes the highlight look off-centre.
    const tight = !!opts.tightSpace;
    const ch = v._ch ?? selChapter;
    const englishWords = getEnglishOrderWords(v.words);
    const sp = tight ? "" : " ";
    const emit = (key, span) => tight ? /*#__PURE__*/React.createElement(React.Fragment, {
      key: key
    }, span, " ") : span;
    return englishWords.map((w, i) => {
      const text = w.english || "";
      if (!text) return null;
      const hc = hiClass(v.verse, w.position, ch); // highlight paint for this word
      const isPunct = /^[.,;:?!—)]/.test(text);
      if (isPunct) return /*#__PURE__*/React.createElement("span", {
        key: i,
        "data-note-pos": w.position,
        className: hc || undefined
      }, text);
      if (text.includes(' ')) {
        if (w.italic_words) {
          const iset = new Set(w.italic_words.split(','));
          const parts = text.split(' ').filter(Boolean);
          return emit(i, /*#__PURE__*/React.createElement("span", {
            key: i,
            "data-note-pos": w.position,
            className: hc || undefined
          }, parts.map((word, pi) => {
            const bare = word.replace(/[^\w]/g, '').toLowerCase();
            return /*#__PURE__*/React.createElement("span", {
              key: pi,
              className: iset.has(bare) ? "lib-prose-italic" : undefined
            }, word, pi < parts.length - 1 || !tight ? " " : "");
          })));
        }
        if (w.italic) {
          const headBare = w.english_head ? w.english_head.replace(/[^\w]/g, '').toLowerCase() : null;
          const parts = text.split(' ').filter(Boolean);
          return emit(i, /*#__PURE__*/React.createElement("span", {
            key: i,
            "data-note-pos": w.position,
            className: hc || undefined
          }, parts.map((word, pi) => {
            const bare = word.replace(/[^\w]/g, '').toLowerCase();
            const isItalic = !headBare || bare === headBare;
            return /*#__PURE__*/React.createElement("span", {
              key: pi,
              className: isItalic ? "lib-prose-italic" : undefined
            }, word, pi < parts.length - 1 || !tight ? " " : "");
          })));
        }
        return emit(i, /*#__PURE__*/React.createElement("span", {
          key: i,
          "data-note-pos": w.position,
          className: hc || undefined
        }, text + sp));
      }
      return emit(i, /*#__PURE__*/React.createElement("span", {
        key: i,
        "data-note-pos": w.position,
        className: (!!w.italic ? "lib-prose-italic" : "") + hc
      }, text + sp));
    });
  };

  // Hebrew OT interlinear verse — right-to-left chips (Hebrew over gloss over H-number).
  // Its own simple renderer (morphhb is one word = one chip; none of the ABP bracket /
  // italic / proper-noun machinery applies). Word-click hands a Hebrew entry (strongs
  // "H####") to the detail panel, which already routes H-numbers to the BDB sidebar.
  const renderHebVerse = (ctx, v) => {
    const {
      selChapter,
      nav,
      selBook,
      highlightRef,
      vnumEl,
      noteMarker,
      onWordClick,
      showInterlinear,
      showStrongs,
      hiClass
    } = ctx;
    const ch = selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    const hebEntry = w => ({
      id: `heb-${selBook.abbrev}-${ch}-${v.verse}-${w.pos}`,
      strongs: w.strongs,
      // "H7307" -> isHebrewWord -> BDB fetch
      strongs_base: w.strongs,
      strongs_raw: (w.strongs || "").replace(/^H/, ""),
      greek: "",
      translit: w.translit || "",
      inflected: w.hebrew || "",
      // pointed word as it appears → big side-card headword
      inflectedTranslit: w.translit || "",
      gloss: w.gloss || "",
      hebrew: w.hebrew,
      morph: w.morph || "",
      grammar: w.grammar || "",
      ref: `${selBook.abbrev} ${ch}:${v.verse}`,
      book: selBook.abbrev,
      chapter: ch,
      verse: v.verse,
      is_pn: false,
      isHeb: true // from the Hebrew OT reader — suppress the KJV-occurrences link
    });
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: `heb-${ch}-${v.verse}`
    }, v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row pericope-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-vnum",
      "aria-hidden": "true"
    }), /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      ref: isHighlight ? highlightRef : null,
      "data-note-verse": v.verse,
      "data-note-chapter": ch,
      className: "lib-verse-row lib-heb-row" + (isHighlight ? " lib-highlight" : "")
    }, vnumEl(v.verse, ch), /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-content lib-heb-content"
    }, noteMarker(v.verse, ch), (v.words || []).map(w => {
      const clickable = !!(onWordClick && w.strongs);
      return /*#__PURE__*/React.createElement("span", {
        key: w.pos,
        "data-note-pos": w.pos,
        className: "lib-word lib-heb-word" + (clickable ? " lib-word-clickable" : "") + hiClass(v.verse, w.pos, ch),
        onClick: clickable ? () => onWordClick(hebEntry(w)) : undefined
      }, /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-heb"
      }, w.hebrew), showInterlinear && w.translit && /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-translit"
      }, w.translit), /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-english"
      }, w.gloss), showStrongs && (w.strongs ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs"
      }, w.strongs) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs",
        style: {
          visibility: "hidden"
        }
      }, "H0")));
    }))));
  };
  const renderVerse = (ctx, v, skipHeading = false) => {
    const {
      selChapter,
      nav,
      selBook,
      wordMode,
      showInterlinear,
      showStrongs,
      onWordClick,
      hiClass,
      vnumEl,
      noteMarker,
      highlightRef
    } = ctx;
    const ch = v._ch ?? selChapter; // chronological rides the chapter on the verse
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    const makeEntry = w => ({
      id: `lib-${selBook.abbrev}-${ch}-${v.verse}-${w.position}`,
      ...wordEntryCore(w, {
        ref: `${selBook.abbrev} ${ch}:${v.verse}`,
        book: selBook.abbrev,
        chapter: ch,
        verse: v.verse,
        gloss: w.english
      }),
      english_head: w.english_head || "",
      // hero shows the head word for a long gloss
      morph: w.morph || "",
      inflected: w.inflected || "",
      // printed Greek form → side-card "in this verse" line
      inflectedTranslit: w.inflected_translit || "",
      // its romanization (build_abp_translit.py)
      pn_type: w.pn_type || null,
      pn_types: w.pn_types || null
    });
    const chipLabel = w => {
      return w.english_head && w.english?.includes(' ') ? w.english_head : w.english || w.english_head || "";
    };

    // Render a multi-word English gloss as inline sub-spans inside ONE chip's english
    // cell: italic translator-helper words are muted, smcap words small-capped. Lets a
    // gloss like "of the second" (all one Greek word, δευτέρῳ) stay a SINGLE chip — the
    // Greek lemma + Strong's then centre over the whole phrase — instead of splitting
    // into one chip per word, where a non-italic helper ("of") became its own blank,
    // clickable box that just reopened the same word.
    const englishParts = w => {
      const italicSet = w.italic_words ? new Set(w.italic_words.split(',')) : new Set();
      const smcapSet = w.smcap_words ? new Set(w.smcap_words.split(',')) : new Set();
      const parts = w.english.split(' ');
      return parts.map((word, pi) => {
        const bare = word.replace(/[^\w]/g, '').toLowerCase();
        const cls = (italicSet.has(bare) ? "lib-prose-italic" : "") + (smcapSet.has(bare) ? " lib-iw-smcap" : "");
        return /*#__PURE__*/React.createElement("span", {
          key: pi,
          className: cls.trim() || undefined
        }, word, pi < parts.length - 1 ? " " : "");
      });
    };

    // Plain chip (English mode or non-bracketed word in Greek mode)
    const chip = (w, key) => {
      const isPN = !!(w.is_pn || w.strongs_base === "*");
      const clickable = !!(onWordClick && w.strongs_base && (w.strongs_base !== "*" || w.english || w.english_head) && (w.english || w.english_head));

      // Multi-word gloss for one Greek word → ONE chip (Greek lemma + Strong's centred
      // over the whole phrase), not one chip per word. See englishParts above.
      if (w.italic_words && w.english && w.english.includes(' ')) {
        return /*#__PURE__*/React.createElement("span", {
          key: key,
          "data-note-pos": w.position,
          className: "lib-word" + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch),
          onClick: clickable ? () => onWordClick(isPN ? {
            ...makeEntry(w),
            isPN: true,
            pnName: w.english_head || w.english
          } : makeEntry(w)) : undefined
        }, showInterlinear && (w.lemma ? /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-greek"
        }, w.lemma) : /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-greek",
          style: {
            visibility: "hidden"
          }
        }, "x")), /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-english"
        }, englishParts(w)), showStrongs && (w.strongs_base && w.strongs_base !== "*" ? /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-strongs"
        }, w.strongs && w.strongs !== '*' ? 'G' + w.strongs : w.strongs_base) : /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-strongs",
          style: {
            visibility: "hidden"
          }
        }, "G0")));
      }
      const rawLabel = w.english || chipLabel(w);
      if (!rawLabel) return null;
      const label = isPN && rawLabel && !rawLabel.includes(' ') ? rawLabel[0].toUpperCase() + rawLabel.slice(1) : rawLabel;
      const isSmcap = w.smcap_words ? new Set(w.smcap_words.split(',')).has(label.replace(/[^\w]/g, '').toLowerCase()) : false;
      return /*#__PURE__*/React.createElement("span", {
        key: key,
        "data-note-pos": w.position,
        className: "lib-word" + (w.italic ? " lib-abp-italic" : "") + (isSmcap ? " lib-smcap" : "") + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch),
        onClick: clickable ? () => onWordClick(isPN ? {
          ...makeEntry(w),
          isPN: true,
          pnName: label,
          gloss: label
        } : makeEntry(w)) : undefined
      }, showInterlinear && (w.lemma ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek"
      }, w.lemma) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek",
        style: {
          visibility: "hidden"
        }
      }, "x")), /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-english"
      }, label), showStrongs && (w.strongs_base && w.strongs_base !== "*" ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs"
      }, w.strongs && w.strongs !== '*' ? 'G' + w.strongs : w.strongs_base) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs",
        style: {
          visibility: "hidden"
        }
      }, "G0")));
    };

    // Bracket chip (bracketed word in Greek mode). The "[" / "]" marks ride INSIDE the
    // english cell of the group's first / last word (brk.open / brk.close), so they hug
    // the english text and the greek still centres over each word — the same inline
    // treatment the detail-panel interlinear uses. (A separate bracket COLUMN, still used
    // by the search/lexicon result rows that carry no greek line, drifts off a short
    // english word once a wider greek lemma sits above it.) brk.trail is the clause
    // punctuation lifted outside the "]".
    const bracketChip = (w, key, brk = {}) => {
      const isPN = !!(w.is_pn || w.strongs_base === "*");
      const clickable = !!(onWordClick && w.strongs_base && (w.strongs_base !== "*" || w.english));
      const brkOpen = pi => brk.open && pi === 0 ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-brk"
      }, "[") : null;
      const brkClose = (pi, lastPi) => brk.close && pi === lastPi ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-brk"
      }, "]"), brk.trail ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-english"
      }, brk.trail) : null) : null;

      // Multi-word gloss within a bracket word → ONE chip (same merge as the plain
      // chip): bracket marks + position number + the whole phrase in the english cell,
      // Greek lemma + Strong's centred over it. See englishParts above.
      if (w.italic_words && w.english && w.english.includes(' ')) {
        return /*#__PURE__*/React.createElement("span", {
          key: key,
          "data-note-pos": w.position,
          className: "lib-word lib-word-bracketed" + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch),
          onClick: clickable ? () => onWordClick(isPN ? {
            ...makeEntry(w),
            isPN: true,
            pnName: w.english_head || w.english
          } : makeEntry(w)) : undefined
        }, showInterlinear && (w.lemma ? /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-greek"
        }, w.lemma) : /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-greek",
          style: {
            visibility: "hidden"
          }
        }, "x")), /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-pos-english"
        }, brkOpen(0), w.greek_pos !== null && w.greek_pos !== undefined && /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-pos"
        }, w.greek_pos), /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-english"
        }, englishParts(w)), brkClose(0, 0)), showStrongs && (w.strongs_base && w.strongs_base !== "*" ? /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-strongs"
        }, w.strongs && w.strongs !== '*' ? 'G' + w.strongs : w.strongs_base) : /*#__PURE__*/React.createElement("span", {
          className: "lib-iw-strongs",
          style: {
            visibility: "hidden"
          }
        }, "G0")));
      }
      const rawLabel = w.english || chipLabel(w);
      if (!rawLabel) return null;
      const label = isPN && rawLabel && !rawLabel.includes(' ') ? rawLabel[0].toUpperCase() + rawLabel.slice(1) : rawLabel;
      const isSmcap = w.smcap_words ? new Set(w.smcap_words.split(',')).has(label.replace(/[^\w]/g, '').toLowerCase()) : false;
      return /*#__PURE__*/React.createElement("span", {
        key: key,
        "data-note-pos": w.position,
        className: "lib-word lib-word-bracketed" + (w.italic ? " lib-abp-italic" : "") + (isSmcap ? " lib-smcap" : "") + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch),
        onClick: clickable ? () => onWordClick(isPN ? {
          ...makeEntry(w),
          isPN: true,
          pnName: label,
          gloss: label
        } : makeEntry(w)) : undefined
      }, showInterlinear && (w.lemma ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek"
      }, w.lemma) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek",
        style: {
          visibility: "hidden"
        }
      }, "x")), /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-pos-english"
      }, brkOpen(0), w.greek_pos !== null && w.greek_pos !== undefined && /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-pos"
      }, w.greek_pos), /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-english"
      }, label), brkClose(0, 0)), showStrongs && (w.strongs_base && w.strongs_base !== "*" ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs"
      }, w.strongs && w.strongs !== '*' ? 'G' + w.strongs : w.strongs_base) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs",
        style: {
          visibility: "hidden"
        }
      }, "G0")));
    };
    if (!wordMode) {
      return /*#__PURE__*/React.createElement(React.Fragment, {
        key: `${ch}-${v.verse}`
      }, !skipHeading && v.heading && /*#__PURE__*/React.createElement("div", {
        className: "lib-verse-row pericope-row"
      }, /*#__PURE__*/React.createElement("span", {
        className: "lib-vnum",
        "aria-hidden": "true"
      }), /*#__PURE__*/React.createElement("div", {
        className: "pericope-heading"
      }, v.heading)), /*#__PURE__*/React.createElement("div", {
        ref: isHighlight ? highlightRef : null,
        "data-note-verse": v.verse,
        "data-note-chapter": ch,
        className: "lib-verse-row" + (isHighlight ? " lib-highlight" : "")
      }, vnumEl(v.verse, ch), /*#__PURE__*/React.createElement("span", {
        className: "lib-verse-content"
      }, noteMarker(v.verse, ch), renderProseWords(ctx, v))));
    }

    // Chip mode — always Greek syntactic order with bracket notation
    let content;
    {
      const sortedWords = [...v.words].filter(w => w.english || w.kjv_def || w.strongs_base === "*").sort((a, b) => a.position - b.position);
      const groups = groupForGreekMode(sortedWords);
      content = groups.map((g, gi) => {
        if (!g.isBracket) {
          return chip(g.word, `g${gi}`);
        }
        // Suppress a duplicate position number on continuation words: when a word
        // shares the greek_pos of the previous numbered member (e.g. the source
        // token "2God did" split into God + did, both pos 2), hide the second
        // number so it renders "²God did", not "²God ²did".
        let lastGp = null;
        const gw = g.words.map(w => {
          if (w.greek_pos != null && w.greek_pos === lastGp) return {
            ...w,
            greek_pos: null
          };
          if (w.greek_pos != null) lastGp = w.greek_pos;
          return w;
        });
        // Lift the bracket's trailing clause punctuation OUTSIDE the "]". ABP
        // writes "...many]," (mark after the bracket), but clean_english glued it
        // onto the word ("many,") so it renders inside. fix_bracket_punct already
        // parks the mark on the bracket's LAST word, so we snip it off here and
        // re-emit it just after the "]" — "[...dominate]." not "[...dominate.]".
        const TRAIL = /[.,;:!?·]+$/;
        let bracketTrail = "";
        let gwR = gw;
        {
          const li = gw.length - 1;
          const lastEng = gw[li] && gw[li].english || "";
          const m = lastEng.match(TRAIL);
          if (m) {
            bracketTrail = m[0];
            gwR = gw.map((w, i) => i === li ? {
              ...w,
              english: lastEng.slice(0, m.index)
            } : w);
          }
        }
        // The "[" / "]" ride the first / last word's english cell (see bracketChip), so
        // the chips just flow in greek order and a verse highlight paints straight
        // through — no separate bracket columns sitting between the chips to break it.
        return /*#__PURE__*/React.createElement("span", {
          key: `bg${gi}`,
          className: "lib-bracket-group"
        }, gwR.map((w, wi) => bracketChip(w, `bg${gi}w${wi}`, {
          open: wi === 0,
          close: wi === gwR.length - 1,
          trail: wi === gwR.length - 1 ? bracketTrail : ""
        })));
      });
    }
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: `${ch}-${v.verse}`
    }, !skipHeading && v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row pericope-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-vnum",
      "aria-hidden": "true"
    }), /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      ref: isHighlight ? highlightRef : null,
      "data-note-verse": v.verse,
      "data-note-chapter": ch,
      className: "lib-verse-row" + (isHighlight ? " lib-highlight" : "")
    }, vnumEl(v.verse, ch), /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-content lib-verse-chips"
    }, noteMarker(v.verse, ch), content)));
  };
  const renderKjvVerse = (ctx, v, showVerseNum = true, skipHeading = false) => {
    const {
      selChapter,
      nav,
      selBook,
      highlightRef,
      vnumEl,
      noteMarker,
      onWordClick,
      showInterlinear,
      showStrongs,
      hiClass
    } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    const makeKjvEntry = (w, sid) => ({
      id: `kjv-${selBook.abbrev}-${ch}-${v.verse}-${w.word_id}`,
      strongs: sid || "",
      strongs_base: sid ? sid.slice(1) : "",
      strongs_raw: sid ? sid.slice(1) : "",
      greek: w.lemma || "",
      translit: w.xlit || "",
      gloss: w.word,
      ref: `${selBook.abbrev} ${ch}:${v.verse}`,
      book: selBook.abbrev,
      chapter: ch,
      verse: v.verse,
      definition: "",
      derivation: "",
      is_function: false,
      isKjv: true,
      isHebrew: sid ? sid.startsWith("H") : false
    });
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: `${ch}-${v.verse}`
    }, !skipHeading && v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row pericope-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-vnum",
      "aria-hidden": "true"
    }), /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      ref: isHighlight ? highlightRef : null,
      "data-note-verse": v.verse,
      "data-note-chapter": ch,
      className: "lib-verse-row" + (isHighlight ? " lib-highlight" : "")
    }, showVerseNum && vnumEl(v.verse, ch), /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-content lib-verse-chips"
    }, showVerseNum && noteMarker(v.verse, ch), v.words.map((w, i) => {
      const sid = w.strongs_ids && w.strongs_ids.length ? w.strongs_ids[0] : null;
      const clickable = !!(onWordClick && sid);
      const isHebrew = sid ? sid.startsWith("H") : false;
      return /*#__PURE__*/React.createElement("span", {
        key: i,
        className: "lib-word lib-kjv-word" + (w.italic ? " lib-kjv-italic" : "") + (clickable ? " lib-word-clickable" : "") + hiClass(v.verse, null, ch),
        onClick: clickable ? () => onWordClick(makeKjvEntry(w, sid)) : undefined
      }, showInterlinear && (w.lemma ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek",
        dir: isHebrew ? "rtl" : undefined,
        style: isHebrew ? {
          fontFamily: "var(--f-serif)"
        } : undefined
      }, w.lemma) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek",
        style: {
          visibility: "hidden"
        }
      }, "x")), /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-english"
      }, w.word, w.punc || ""), showStrongs && (sid ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs"
      }, sid) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs",
        style: {
          visibility: "hidden"
        }
      }, "G0")));
    }))));
  };

  // BSB word chips — same shape as renderKjvVerse (standard Strong's, both H and
  // G), but the word entry is flagged isBsb so the detail panel pulls BSB's own
  // verse breakdown / quote / occurrence count.
  const renderBsbVerse = (ctx, v, showVerseNum = true, skipHeading = false) => {
    const {
      selChapter,
      nav,
      selBook,
      highlightRef,
      vnumEl,
      noteMarker,
      onWordClick,
      showInterlinear,
      showStrongs,
      hiClass
    } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    const makeBsbEntry = (w, sid) => ({
      id: `bsb-${selBook.abbrev}-${ch}-${v.verse}-${w.word_id}`,
      strongs: sid || "",
      strongs_base: sid ? sid.slice(1) : "",
      strongs_raw: sid ? sid.slice(1) : "",
      greek: w.lemma || "",
      translit: w.xlit || "",
      inflected: w.form || "",
      // original word as printed (Berean tables) → big side-card headword
      inflectedTranslit: w.form_translit || "",
      gloss: w.word,
      ref: `${selBook.abbrev} ${ch}:${v.verse}`,
      book: selBook.abbrev,
      chapter: ch,
      verse: v.verse,
      definition: "",
      derivation: "",
      is_function: false,
      isBsb: true,
      isHebrew: sid ? sid.startsWith("H") : false
    });
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: `${ch}-${v.verse}`
    }, !skipHeading && v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row pericope-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-vnum",
      "aria-hidden": "true"
    }), /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      ref: isHighlight ? highlightRef : null,
      "data-note-verse": v.verse,
      "data-note-chapter": ch,
      className: "lib-verse-row" + (isHighlight ? " lib-highlight" : "")
    }, showVerseNum && vnumEl(v.verse, ch), /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-content lib-verse-chips"
    }, showVerseNum && noteMarker(v.verse, ch), v.words.map((w, i) => {
      const sid = w.strongs_ids && w.strongs_ids.length ? w.strongs_ids[0] : null;
      const clickable = !!(onWordClick && sid);
      const isHebrew = sid ? sid.startsWith("H") : false;
      return /*#__PURE__*/React.createElement("span", {
        key: i,
        "data-note-pos": w.verse_pos,
        className: "lib-word lib-bsb-word" + (w.italic ? " lib-bsb-italic" : "") + (clickable ? " lib-word-clickable" : "") + hiClass(v.verse, w.verse_pos, ch),
        onClick: clickable ? () => onWordClick(makeBsbEntry(w, sid)) : undefined
      }, showInterlinear && (w.lemma ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek",
        dir: isHebrew ? "rtl" : undefined,
        style: isHebrew ? {
          fontFamily: "var(--f-serif)"
        } : undefined
      }, w.lemma) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek",
        style: {
          visibility: "hidden"
        }
      }, "x")), /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-english"
      }, w.word, w.punc || ""), showStrongs && (sid ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs"
      }, sid) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs",
        style: {
          visibility: "hidden"
        }
      }, "G0")));
    }))));
  };
  const renderKjvProse = (ctx, v, showVerseNum = true, skipHeading = false) => {
    const {
      selChapter,
      nav,
      highlightRef,
      vnumEl,
      noteMarker,
      hiClass
    } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: `${ch}-${v.verse}`
    }, !skipHeading && v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row pericope-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-vnum",
      "aria-hidden": "true"
    }), /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      ref: isHighlight ? highlightRef : null,
      "data-note-verse": v.verse,
      "data-note-chapter": ch,
      className: "lib-verse-row" + (isHighlight ? " lib-highlight" : "")
    }, showVerseNum && vnumEl(v.verse, ch), /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-content"
    }, showVerseNum && noteMarker(v.verse, ch), v.words.map((w, i) => /*#__PURE__*/React.createElement("span", {
      key: i,
      className: (w.italic ? "lib-prose-italic" : "") + hiClass(v.verse, null, ch)
    }, w.word, w.punc || "", " ")))));
  };

  // Plain-text verse-per-line (BSB/ESV/NIV) — the same one-block-per-verse layout
  // renderKjvProse gives KJV, used for poetry books so every text lines its verses
  // up the way ABP poetry does (not run together as flowing prose).
  const renderPlainVerse = (ctx, v, showVerseNum = true, skipHeading = false) => {
    const {
      selChapter,
      nav,
      highlightRef,
      vnumEl,
      noteMarker,
      hiClass
    } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: `${ch}-${v.verse}`
    }, !skipHeading && v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row pericope-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-vnum",
      "aria-hidden": "true"
    }), /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      ref: isHighlight ? highlightRef : null,
      "data-note-verse": v.verse,
      "data-note-chapter": ch,
      className: "lib-verse-row" + (isHighlight ? " lib-highlight" : "")
    }, showVerseNum && vnumEl(v.verse, ch), /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-content"
    }, showVerseNum && noteMarker(v.verse, ch), /*#__PURE__*/React.createElement("span", {
      className: "lib-bsb-text" + hiClass(v.verse, null, ch)
    }, v.verse_text))));
  };

  // KJV / BSB / ESV read as continuous prose (paragraphs), the same flow ABP prose
  // uses — NOT one block per verse. Each verse is an inline run with a superscript
  // number; `inner` is that verse's text/words.
  const renderFlowVerse = (ctx, v, inner) => {
    const {
      selChapter,
      nav,
      highlightRef,
      handleVerseNum,
      vnumPressRef,
      vnumNoteHandlers,
      noteDotInline
    } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: `${ch}-${v.verse}`
    }, v.heading && /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading), /*#__PURE__*/React.createElement("span", {
      ref: isHighlight ? highlightRef : null,
      className: "lib-flow-verse",
      "data-note-verse": v.verse,
      "data-note-chapter": ch
    }, /*#__PURE__*/React.createElement("sup", _extends({
      className: "lib-flow-vnum",
      title: handleVerseNum ? "Click: cross-references · Right-click / long-press: add a note" : undefined,
      onClick: handleVerseNum ? () => {
        if (vnumPressRef.current.fired) {
          vnumPressRef.current.fired = false;
          return;
        }
        handleVerseNum(v.verse, ch);
      } : undefined
    }, vnumNoteHandlers(v.verse, ch)), v.verse), noteDotInline(v.verse, ch), inner));
  };
  // Plain-text verse (BSB + ESV).
  const plainFlowInner = (ctx, v) => {
    const {
      selChapter,
      hiClass
    } = ctx;
    const ch = v._ch ?? selChapter;
    return /*#__PURE__*/React.createElement("span", {
      className: "lib-bsb-text" + hiClass(v.verse, null, ch)
    }, v.verse_text, " ");
  };
  // KJV word list (keeps italic-addition styling), run together as prose.
  const kjvFlowInner = (ctx, v) => {
    const {
      selChapter,
      hiClass
    } = ctx;
    const ch = v._ch ?? selChapter;
    return v.words.map((w, i) => /*#__PURE__*/React.createElement("span", {
      key: i,
      className: (w.italic ? "lib-prose-italic" : "") + hiClass(v.verse, null, ch)
    }, w.word, w.punc || "", " "));
  };

  // Non-canonical reader (Didache, etc.). The Greek interlinear is the normal reading,
  // exactly like Bible ABP. The readable English appears ONLY in Parallel — same
  // two-column layout as Bible parallel (Greek interlinear | English). No bracket /
  // ordering machinery; chips stay in natural Greek order. Word click → word-study.
  let _didCapNext = true; // reset per verse below; capitalize sentence-initial glosses
  const didChips = (ctx, v) => {
    const {
      onWordClick,
      corpus,
      selChapter,
      nonCanon,
      showInterlinear,
      showStrongs,
      hiClass
    } = ctx;
    _didCapNext = true;
    return v.words.map((w, i) => {
      const raw = w.english || "";
      if (!raw) return null;
      const label = _didCapNext ? raw.charAt(0).toUpperCase() + raw.slice(1) : raw;
      _didCapNext = /[.!?][")'\]]*$/.test(raw); // next gloss starts a new sentence?
      const clickable = !!(onWordClick && w.strongs_base);
      const entry = {
        id: `extra-${corpus}-${selChapter}-${v.verse}-${w.position}`,
        strongs: w.strongs ? strongsTag(w.strongs) : "",
        strongs_base: w.strongs_base || "",
        strongs_raw: w.strongs || "",
        greek: w.lemma || w.greek || "",
        translit: w.translit || "",
        morph: "",
        gloss: label,
        english_head: label,
        // hero shows the gloss even when it's a short phrase
        ref: `${nonCanon ? nonCanon.name : "Extra"} ${selChapter}:${v.verse}`,
        book: corpus,
        chapter: selChapter,
        verse: v.verse,
        definition: "",
        derivation: "",
        is_function: false,
        is_pn: false,
        pn_type: null,
        pn_types: null,
        isExtra: true,
        extraBook: corpus,
        extraBookName: nonCanon ? nonCanon.name : ""
      };
      return /*#__PURE__*/React.createElement("span", {
        key: `d${i}`,
        className: "lib-word" + (clickable ? " lib-word-clickable" : "") + hiClass(v.verse, null),
        onClick: clickable ? () => onWordClick(entry) : undefined
      }, showInterlinear && (w.lemma ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek"
      }, w.lemma) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-greek",
        style: {
          visibility: "hidden"
        }
      }, "x")), /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-english"
      }, label), showStrongs && (w.strongs ? /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs"
      }, "G" + w.strongs) : /*#__PURE__*/React.createElement("span", {
        className: "lib-iw-strongs",
        style: {
          visibility: "hidden"
        }
      }, "G0")));
    });
  };

  // Single view: Greek interlinear only (mirrors Bible ABP).
  const renderDidacheVerse = (ctx, v) => {
    const {
      noteVnum,
      noteMarker
    } = ctx;
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: v.verse
    }, v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row pericope-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-vnum",
      "aria-hidden": "true"
    }), /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row lib-did-row",
      "data-note-verse": v.verse
    }, noteVnum(v.verse), /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-content lib-verse-chips"
    }, noteMarker(v.verse), didChips(ctx, v))));
  };

  // Prose view: our readable English as flowing text with verse numbers.
  const renderDidacheProse = ctx => {
    const {
      didVerses,
      vnumPressRef,
      vnumNoteHandlers,
      noteDotInline,
      hiClass
    } = ctx;
    return /*#__PURE__*/React.createElement("div", {
      className: "lib-text-words lib-prose-flow"
    }, didVerses.map(v => /*#__PURE__*/React.createElement(React.Fragment, {
      key: v.verse
    }, v.heading && /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading), /*#__PURE__*/React.createElement("span", {
      className: "lib-flow-verse",
      "data-note-verse": v.verse
    }, /*#__PURE__*/React.createElement("sup", _extends({
      className: "lib-flow-vnum",
      title: "Right-click / long-press: add a note",
      onClick: () => {
        if (vnumPressRef.current.fired) vnumPressRef.current.fired = false;
      }
    }, vnumNoteHandlers(v.verse)), v.verse), noteDotInline(v.verse), /*#__PURE__*/React.createElement("span", {
      className: hiClass(v.verse, null) || undefined
    }, (v.english || "") + " ")))));
  };

  // Verse-per-line view for English-only "other books": each verse on its own row
  // with its number, like the Bible's verse layout — but plain reading text, no
  // clickable word chips (these texts have no Greek interlinear). Notes + highlights
  // ride the whole verse, same as the flowing-prose view.
  const renderExtraLines = ctx => {
    const {
      didVerses,
      noteVnum,
      noteMarker,
      hiClass
    } = ctx;
    return /*#__PURE__*/React.createElement("div", {
      className: "lib-text-words"
    }, didVerses.map(v => /*#__PURE__*/React.createElement(React.Fragment, {
      key: v.verse
    }, v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row pericope-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-vnum",
      "aria-hidden": "true"
    }), /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      className: "lib-verse-row",
      "data-note-verse": v.verse
    }, noteVnum(v.verse), /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-content"
    }, noteMarker(v.verse), /*#__PURE__*/React.createElement("span", {
      className: hiClass(v.verse, null) || undefined
    }, v.english || ""))))));
  };

  // Parallel view: Greek interlinear | readable English (same shape as Bible parallel).
  const renderDidacheParallelVerse = (ctx, v) => {
    const {
      noteVnum,
      noteMarker,
      hiClass
    } = ctx;
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: v.verse
    }, v.heading && /*#__PURE__*/React.createElement("div", {
      className: "lib-parallel-section-heading"
    }, /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading)), /*#__PURE__*/React.createElement("div", {
      className: "lib-parallel-verse",
      "data-note-verse": v.verse
    }, /*#__PURE__*/React.createElement("div", {
      className: "lib-parallel-vnum"
    }, noteVnum(v.verse), noteMarker(v.verse)), /*#__PURE__*/React.createElement("div", {
      className: "lib-parallel-col"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lib-verse-chips"
    }, didChips(ctx, v))), /*#__PURE__*/React.createElement("div", {
      className: "lib-parallel-col"
    }, /*#__PURE__*/React.createElement("p", {
      className: "lib-did-eng" + hiClass(v.verse, null)
    }, v.english))));
  };
  return {
    joinProse,
    renderProseWords,
    renderHebVerse,
    renderVerse,
    renderKjvVerse,
    renderKjvProse,
    renderBsbVerse,
    renderPlainVerse,
    renderFlowVerse,
    plainFlowInner,
    kjvFlowInner,
    didChips,
    renderDidacheVerse,
    renderDidacheProse,
    renderExtraLines,
    renderDidacheParallelVerse
  };
}();

// ============================================================
// LIBRARY VIEW — the reader (the big component). Its helpers and nav/picker
// sub-components live in 59a-library-helpers.jsx + 59b-library-nav.jsx.
// ============================================================
function LibraryView({
  nav,
  onNavChange,
  onWordClick,
  onVerseNumberClick,
  onOpenNote,
  onTranslationChange,
  isMobile,
  showSummary,
  focusMode,
  onToggleFocus,
  onDetailBaseChange
}) {
  const [books, setBooks] = useState(() => readCachedBooks());
  const [selBook, setSelBook] = useState(() => {
    const c = readCachedBooks(),
      s = readLibSaved();
    if (!c.length) return null;
    return s && s.book && c.find(b => b.abbrev === s.book) || c[0];
  });
  const [selChapter, setSelChapter] = useState(() => {
    const s = readLibSaved();
    return s && s.chapter > 0 ? s.chapter : 1;
  });
  const [verses, setVerses] = useState([]);
  const [kjvVerses, setKjvVerses] = useState([]);
  const [bsbVerses, setBsbVerses] = useState([]);
  const [esvVerses, setEsvVerses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [kjvLoading, setKjvLoading] = useState(false);
  const [bsbLoading, setBsbLoading] = useState(false);
  const [esvLoading, setEsvLoading] = useState(false);
  // ESV is the owner's personal text: esvOwner (set by the server) gates the toggle.
  const [esvOwner, setEsvOwner] = useState(false);
  // NIV — same owner gate as ESV, text-only (no audio).
  const [nivVerses, setNivVerses] = useState([]);
  const [nivLoading, setNivLoading] = useState(false);
  const [nivOwner, setNivOwner] = useState(false);
  // Hebrew OT interlinear (PUBLIC, public-domain). Now open to everyone: the toggle
  // shows whenever hebAvail (heb.db is loaded) — no login needed. Single-read mode for
  // now (not in compare/chronological yet).
  const [hebVerses, setHebVerses] = useState([]);
  const [hebLoading, setHebLoading] = useState(false);
  const [hebAvail, setHebAvail] = useState(false);
  // Have the owner-status checks come back yet? Until they do, don't bounce a restored
  // ESV/NIV/HEB reading to ABP (a refresh would otherwise drop you off the gated text).
  const [gatedReady, setGatedReady] = useState(false);
  // Chapter audio (BSB = public-domain openbible; ESV = owner-only FCBH), once "Listen" is pressed.
  // audioKey = the "book-chapter" currently loaded (so the right Listen button highlights in chrono,
  // where a passage can span chapters and each chapter is its own file).
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioKey, setAudioKey] = useState(null);
  const [audioBusy, setAudioBusy] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [audioCur, setAudioCur] = useState(0);
  const [audioDur, setAudioDur] = useState(0);
  const [dockClosing, setDockClosing] = useState(false); // mobile dock: keep it mounted briefly so it can slide OUT
  const dockWasShown = useRef(false);
  const audioRef = useRef(null);
  const resumeAudioRef = useRef(false); // page-turn while playing → keep the read-along going on the next page
  const [viewCh, setViewCh] = useState(null); // chrono: chapter currently scrolled into view (drives the toolbar play target)
  const [libOptions, setLibOptions] = useState(() => {
    try {
      const s = JSON.parse(localStorage.getItem("lexica.opts.v1") || "null");
      if (s) return {
        viewMode: s.viewMode || "chip",
        showStrongs: !!s.showStrongs,
        showInterlinear: !!s.showInterlinear
      };
    } catch (e) {}
    return {
      viewMode: "chip",
      showStrongs: false,
      showInterlinear: false
    };
  });
  const [libFontSize, setLibFontSize] = useState(() => {
    const stored = localStorage.getItem("libFontSize");
    if (stored) return parseInt(stored, 10);
    return isMobile ? 15 : 18;
  });
  // Reading theme: "light" (default) | "sepia" | "dark". Applied to <html data-theme>
  // so it re-skins the whole app, and remembered across reloads.
  const [theme, setTheme] = useState(() => localStorage.getItem("lexica.theme.v1") || "light");
  useEffect(() => {
    if (theme === "light") document.documentElement.removeAttribute("data-theme");else document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("lexica.theme.v1", theme);
  }, [theme]);
  const [translation, setTranslation] = useState(() => {
    // "abp"|"kjv"|"bsb"|"esv"|"niv"|"parallel"
    const s = readLibSaved(),
      t = s && s.translation;
    return ["abp", "kjv", "bsb", "esv", "niv", "heb", "parallel"].includes(t) ? t : "abp";
  });
  // Compare (parallel): translation === "parallel" is the mode; compareSel is WHICH
  // texts (2-4) sit side by side. ESV/NIV only offered to the owner.
  const [compareSel, setCompareSel] = useState(() => {
    const s = readLibSaved();
    return s && Array.isArray(s.compareSel) && s.compareSel.length >= 2 ? s.compareSel : ["abp", "kjv"];
  });
  const [compareOpen, setCompareOpen] = useState(false);
  // Close the Compare popout on any click outside it (or Esc) — same as the More menu.
  const compareWrapRef = useRef(null);
  useEffect(() => {
    if (!compareOpen) return;
    const onDown = e => {
      if (compareWrapRef.current && !compareWrapRef.current.contains(e.target)) {
        setCompareOpen(false);
        // Swallow the dismiss click so it doesn't also land on a word chip behind the menu.
        const swallow = ev => {
          ev.stopPropagation();
          ev.preventDefault();
        };
        document.addEventListener("click", swallow, {
          capture: true,
          once: true
        });
        setTimeout(() => document.removeEventListener("click", swallow, {
          capture: true
        }), 350);
      }
    };
    const onKey = e => {
      if (e.key === "Escape") setCompareOpen(false);
    };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [compareOpen]);
  const [corpus, setCorpus] = useState(() => {
    // "bible" | a non-canonical id (e.g. "didache")
    const s = readLibSaved();
    return s && s.corpus && s.corpus !== "bible" && NONCANON.some(x => x.id === s.corpus) ? s.corpus : "bible";
  });
  const [didVerses, setDidVerses] = useState([]);
  const [didLoading, setDidLoading] = useState(false);
  const [otherOpen, setOtherOpen] = useState(false);
  const [fontOpen, setFontOpen] = useState(false);
  const fontWrapRef = useRef(null); // the Aa menu wrapper — for click-outside-to-close
  // Close the Aa (size/theme) menu on any click outside it — robust against the
  // toolbar sitting above the scrim. Clicks inside keep it open so A−/A+ still work.
  // The outside click that closes it is SWALLOWED so it doesn't also select a word
  // or open something behind the menu (the dismiss click should only dismiss).
  useEffect(() => {
    if (!fontOpen) return;
    const onDoc = e => {
      if (fontWrapRef.current && fontWrapRef.current.contains(e.target)) return; // inside: keep open
      setFontOpen(false);
      const swallow = ev => {
        ev.stopPropagation();
        ev.preventDefault();
      };
      document.addEventListener("click", swallow, {
        capture: true,
        once: true
      });
      // If this press never becomes a click (e.g. a drag), drop the swallower.
      setTimeout(() => document.removeEventListener("click", swallow, {
        capture: true
      }), 350);
    };
    document.addEventListener("pointerdown", onDoc);
    return () => document.removeEventListener("pointerdown", onDoc);
  }, [fontOpen]);
  const [summaryOpen, setSummaryOpen] = useState(false); // mobile: overview sheet
  const [chronoPanel, setChronoPanel] = useState("intro"); // chrono right panel: "intro" | "overview"
  // Chronological reading: the same reader, fed passages in event order. The list
  // is a static file (book + verse range pointers, no Bible text). "canonical" =
  // normal book/chapter order; "chronological" = walk `chrono.passages` in order.
  const [orderMode, setOrderMode] = useState(() => {
    // "canonical" | "chronological"
    const s = readLibSaved();
    return s && s.orderMode === "chronological" ? "chronological" : "canonical";
  });
  const [chrono, setChrono] = useState(() => readCachedChrono()); // { eras, passages } | null (cached for instant first paint)
  const [chronoPos, setChronoPos] = useState(() => {
    // current passage position (1-based)
    const s = readLibSaved();
    return s && s.chronoPos > 0 ? s.chronoPos : 1;
  });
  const [chronoData, setChronoData] = useState(null); // loaded span: { pos, byCh:{ch:{abp,kjv,bsb}} }
  const [chronoLoading, setChronoLoading] = useState(false);
  // Chrono picker view: "eras" (the era→passage browse) or "days" (the 365-day plan).
  const [chronoView, setChronoView] = useState(() => {
    try {
      return localStorage.getItem("lexica.chronoview.v1") === "eras" ? "eras" : "days";
    } catch (e) {
      return "days";
    }
  });
  // Per-text reading-plan progress ({ abp:{day,streak,last}, kjv:{...}, ... }).
  const [planProg, setPlanProg] = useState(() => planLoadAll());
  const nonCanon = NONCANON.find(t => t.id === corpus) || null;
  const chronoOn = orderMode === "chronological" && !nonCanon && !!chrono && translation !== "heb";
  // Hebrew OT has no chronological order — keep order canonical whenever Hebrew is the text
  // (covers both switching to Hebrew from chrono AND restoring an old heb+chrono spot).
  useEffect(() => {
    if (translation === "heb" && orderMode === "chronological") setOrderMode("canonical");
  }, [translation, orderMode]);
  const curPassage = chronoOn ? chrono.passages[chronoPos - 1] || null : null;
  const highlightRef = useRef(null);
  const navBookRef = useRef(null);
  const readingRef = useRef(null);
  // Drag-select-to-note: the floating "Add note" bar + the captured anchor.
  const [noteSel, setNoteSel] = useState(null); // { rect, anchor } | null
  const justSelectedRef = useRef(false); // suppress the click that follows a drag
  const swallowClickRef = useRef(false); // a press that closed the popup → eat its click (survives the re-render)
  const [flashMsg, setFlashMsg] = useState(""); // tiny confirmation toast ("Copied", etc.)
  const flashT = useRef(null);
  const flash = m => {
    setFlashMsg(m);
    clearTimeout(flashT.current);
    flashT.current = setTimeout(() => setFlashMsg(""), 1600);
  };
  // The line a verse becomes when sent to the journal: "Genesis 1:8 (ABP) — text".
  // No translation tag for non-canon texts (their book name already says it all).
  const journalLine = a => {
    const tag = nonCanon ? "" : translation === "parallel" ? compareSel.map(s => s.toUpperCase()).join("/") : (translation || "").toUpperCase();
    return a.refLabel + (tag ? " (" + tag + ")" : "") + " — " + a.snippet;
  };
  useNotesVersion(); // re-render markers when notes change
  // Who's signed in (re-read every render; setAuth notifies, so login/logout
  // re-renders us). The ESV toggle only ever shows when the server says "owner".
  const authEmail = (() => {
    try {
      return (NotesStore.authInfo() || {}).email || null;
    } catch (e) {
      return null;
    }
  })();
  useEffect(() => {
    let cancelled = false;
    Promise.all([api.esvStatus().then(d => {
      if (!cancelled) setEsvOwner(!!(d && d.owner));
    }), api.nivStatus().then(d => {
      if (!cancelled) setNivOwner(!!(d && d.owner));
    }), api.hebStatus().then(d => {
      if (!cancelled) setHebAvail(!!(d && d.available));
    })]).finally(() => {
      if (!cancelled) setGatedReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, [authEmail]);
  // If the owner signs out (or it's revoked) while reading ESV/NIV, fall back to ABP
  // so they're never stuck on a now-forbidden text showing blank.
  useEffect(() => {
    if (!gatedReady) return; // owner status still loading — don't bounce a just-restored gated text
    if (!esvOwner && translation === "esv") {
      setTranslation("abp");
      onTranslationChange?.("abp");
    }
    if (!nivOwner && translation === "niv") {
      setTranslation("abp");
      onTranslationChange?.("abp");
    }
    // HEB is OT-only — bounce back to ABP if it's unavailable, or you moved to an NT
    // book while reading Hebrew.
    if (translation === "heb" && (!hebAvail || selBook && NT_BOOKS.has(selBook.abbrev))) {
      setTranslation("abp");
      onTranslationChange?.("abp");
    }
  }, [esvOwner, nivOwner, hebAvail, translation, selBook, gatedReady]);
  useEffect(() => {
    if (!nav?.book || !navBookRef.current || nav.book !== selBook?.abbrev) return;
    requestAnimationFrame(() => {
      const el = navBookRef.current;
      const sc = el && el.closest(".nav-scroll");
      if (!sc) return;
      // Scroll ONLY the nav's own book list so the active book rides near the top —
      // never the whole window (that dragged the verse you jumped to off-screen).
      const top = el.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop;
      sc.scrollTo({
        top: Math.max(0, top - 8),
        behavior: "smooth"
      });
    });
  }, [nav?.book, selBook?.abbrev]);

  // When a non-canonical text is opened, its nav group moves to the top — bring it into view.
  useEffect(() => {
    if (!nonCanon || !navBookRef.current) return;
    requestAnimationFrame(() => {
      navBookRef.current?.scrollIntoView({
        behavior: "auto",
        block: "start"
      });
    });
  }, [nonCanon?.id]);
  const navVisible = !isMobile;
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [modesOpen, setModesOpen] = useState(false);
  // In-text search ("find in the text you're reading")
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQ, setSearchQ] = useState("");
  const [searchResults, setSearchResults] = useState(null); // null = no search run yet
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchCounts, setSearchCounts] = useState(null); // {verses, matches, capped}
  const [searchHi, setSearchHi] = useState(null); // {terms, partial, caseSensitive} for result highlighting
  const didSearchRef = useRef(false); // true once a search has run (gates the auto-rerun on setting changes)
  const [searchOptsOpen, setSearchOptsOpen] = useState(false); // the collapsible options/range block
  // eSword-style options
  const [searchMode, setSearchMode] = useState("any"); // "any" | "all" | "phrase"
  const [searchPartial, setSearchPartial] = useState(true); // true = substring, false = whole word
  const [searchCase, setSearchCase] = useState(false); // case-sensitive
  const [searchExclude, setSearchExclude] = useState(""); // words to exclude
  const [searchFrom, setSearchFrom] = useState("Gen"); // range start (book abbrev)
  const [searchTo, setSearchTo] = useState("Rev"); // range end (book abbrev)

  useEffect(() => {
    api.books().then(data => {
      setBooks(data);
      if (!data.length) return;
      try {
        localStorage.setItem("lexica.books.v1", JSON.stringify(data));
      } catch (e) {}
      // Restore the last reading spot from a previous visit (book/chapter/translation, or an
      // open non-canonical text); fall back to Genesis. An explicit verse jump (nav.book — a
      // click from Search/cross-refs) runs in its own effect and overrides this afterward.
      let saved = null;
      try {
        saved = JSON.parse(localStorage.getItem("lexica.lib.v1") || "null");
      } catch (e) {}
      const savedBook = saved && saved.book ? data.find(b => b.abbrev === saved.book) : null;
      // Everything else — chapter, text, order, chrono position, compare, corpus — restores
      // synchronously in the state initializers above, so nothing flickers (no chapter "1"
      // flash on mobile). Only selBook waits here: it must be resolved against the just-loaded
      // books list. The gated-text bounce (owner status) still drops ESV/NIV/HEB afterward.
      setSelBook(savedBook || data[0]);
      // Restore the placeholder verse (the verse you last clicked) so a refresh lands
      // back on it — set the highlight + scroll. No book in the nav, so the chapter-load
      // effect leaves it alone (selBook/selChapter are already restored above).
      if (savedBook && saved.highlight != null) {
        onNavChange?.({
          chapter: saved.chapter,
          highlight: saved.highlight,
          scroll: true,
          instant: true
        });
      }
    });
  }, []);
  // Remember the reading spot so a refresh returns you here instead of Genesis 1.
  useEffect(() => {
    if (!selBook && corpus === "bible") return; // nothing settled yet
    try {
      localStorage.setItem("lexica.lib.v1", JSON.stringify({
        corpus,
        book: selBook ? selBook.abbrev : null,
        chapter: selChapter,
        translation,
        orderMode,
        chronoPos,
        compareSel,
        highlight: nav?.highlight ?? null
      }));
    } catch (e) {}
  }, [corpus, selBook, selChapter, translation, orderMode, chronoPos, compareSel, nav?.highlight]);
  // Re-scroll to the placeholder verse when you switch Bible version, so you land back
  // on the verse you marked instead of the top of the chapter. Skip the first render
  // (the version is just being restored); only real switches re-arm the scroll.
  const firstTransRef = useRef(true);
  useEffect(() => {
    if (firstTransRef.current) {
      firstTransRef.current = false;
      return;
    }
    onNavChange?.(n => n && n.highlight != null ? {
      ...n,
      scroll: true,
      instant: true
    } : n);
  }, [translation]);
  // Persist reading-plan progress + the Eras/Days choice.
  useEffect(() => {
    planSaveAll(planProg);
    NotesStore.schedulePlanSync();
  }, [planProg]);
  // Pull account-synced plan progress back in: when a sync folds the server's copy into
  // localStorage, NotesStore notifies — re-read it, but only swap state if it actually
  // changed (so a no-op notify doesn't loop back into another push).
  useEffect(() => NotesStore.subscribe(() => setPlanProg(prev => {
    const next = planLoadAll();
    return JSON.stringify(next) === JSON.stringify(prev) ? prev : next;
  })), []);
  useEffect(() => {
    try {
      localStorage.setItem("lexica.chronoview.v1", chronoView);
    } catch (e) {}
  }, [chronoView]);
  // Reading-display toggles (chip/prose, Strong's, interlinear) stick across reloads.
  useEffect(() => {
    try {
      localStorage.setItem("lexica.opts.v1", JSON.stringify(libOptions));
    } catch (e) {}
  }, [libOptions]);

  // Load the chronological passage list once (a small static file). If it fails,
  // chronoOn stays false and the Order toggle simply never appears.
  useEffect(() => {
    api.chronological().then(data => {
      setChrono(data);
      try {
        localStorage.setItem("lexica.chrono.v1", JSON.stringify(data));
      } catch (e) {}
    }).catch(() => {});
  }, []);

  // Where you were reading in canonical order, so flipping back restores it
  // (instead of stranding you on the chronological passage's book/chapter).
  const canonReturnRef = useRef(null);
  // Jump the reader to a chronological passage: select its book and land on its
  // START chapter. (Stage 2 trims to the exact verse window and spans chapters.)
  // No manual verse-clearing here — the chapter loader clears + reloads itself when
  // the book/chapter actually changes; clearing when they DON'T change just blanks
  // the page (e.g. switching to chrono while already on Genesis 1).
  const pickPassage = p => {
    if (!p) return;
    const b = books.find(bk => bk.abbrev === p.book);
    if (!b) return;
    setChronoPos(p.pos);
    if (corpus !== "bible") setCorpus("bible");
    setSelBook(b);
    setSelChapter(p.start_ch);
  };
  // Step forward/back through the whole passage list (flows across era edges).
  const stepPassage = delta => {
    if (!chrono) return;
    const next = chronoPos + delta;
    if (next < 1 || next > chrono.passages.length) return;
    pickPassage(chrono.passages[next - 1]);
  };
  // Which chronological passage contains a given book + chapter (and verse, if known)?
  // Used when flipping INTO chronological so you land on the passage holding the spot
  // you were just reading. A chapter can sit in several passages (e.g. 1 Chronicles 1
  // is split across days), so prefer the one whose verse window actually covers the
  // verse; otherwise fall back to the first passage that covers the chapter.
  const passageForRef = (book, ch, v) => {
    if (!chrono || !book) return null;
    const coversCh = p => p.book === book && ch >= p.start_ch && ch <= p.end_ch;
    if (v != null) {
      const exact = chrono.passages.find(p => coversCh(p) && !(ch === p.start_ch && v < p.start_v) && !(ch === p.end_ch && v > p.end_v));
      if (exact) return exact;
    }
    return chrono.passages.find(coversCh) || null;
  };
  // Reading-plan ("Days") wiring. Progress is per reading text; the chips switch text.
  const planTexts = [{
    id: "abp",
    label: "ABP"
  }, {
    id: "kjv",
    label: "KJV"
  }, {
    id: "bsb",
    label: "BSB"
  }, ...(esvOwner ? [{
    id: "esv",
    label: "ESV"
  }] : []), ...(nivOwner ? [{
    id: "niv",
    label: "NIV"
  }] : [])];
  // The little check on each day IS the control. Each day is INDEPENDENT — checking a
  // day marks just that one done, unchecking clears just that one, so you can skip around
  // and still keep an accurate count. Marking bumps the daily streak (once per calendar
  // day). Marking does NOT yank you to another passage — tap a passage to read.
  const toggleDayDone = dayNum => {
    if (!chrono || !chrono.days) return;
    setPlanProg(prev => {
      const cur = planFor(prev, translation);
      const done = new Set(cur.done || []);
      let {
        streak,
        last
      } = cur;
      if (done.has(dayNum)) {
        done.delete(dayNum); // un-mark just this day
      } else {
        done.add(dayNum); // mark just this day
        const today = planYmd();
        if (cur.last === today) {/* already counted a day today — keep streak */} else if (cur.last && planDayDiff(cur.last, today) === 1) streak = (streak || 0) + 1;else streak = 1;
        last = today;
      }
      const next = {
        ...cur,
        done: Array.from(done).sort((a, b) => a - b),
        streak,
        last
      };
      return {
        ...prev,
        [translation]: next
      };
    });
  };
  const planBundle = {
    view: chronoView,
    setView: setChronoView,
    progAll: planProg,
    texts: planTexts,
    curText: translation,
    onPickText: id => pickBible(id),
    onToggleDone: toggleDayDone
  };
  // Flip reading order. Entering chronological stashes the canonical spot and jumps
  // to the current passage; leaving restores the stashed canonical spot.
  const setOrder = mode => {
    if (mode === orderMode) return;
    if (mode === "chronological") {
      canonReturnRef.current = selBook ? {
        book: selBook,
        chapter: selChapter
      } : null;
      setOrderMode("chronological");
      if (chrono) {
        if (corpus !== "bible") setCorpus("bible");
        // Land on the passage that holds the spot you were just reading; only fall back
        // to the last-remembered chronological position if that lookup comes up empty.
        const match = selBook && passageForRef(selBook.abbrev, selChapter) || chrono.passages[chronoPos - 1] || chrono.passages[0];
        pickPassage(match);
      }
    } else {
      setOrderMode("canonical");
      const r = canonReturnRef.current;
      if (r && r.book) {
        if (corpus !== "bible") setCorpus("bible");
        setSelBook(r.book);
        setSelChapter(r.chapter);
      }
    }
  };
  useEffect(() => {
    if (!nav || !nav.book || !books.length) return;
    const b = books.find(b => b.abbrev === nav.book);
    if (!b) return;
    // A verse jump can carry a translation (e.g. a KJV cross-ref) — honor it in either order.
    if (nav.translation) {
      setTranslation(nav.translation);
      onTranslationChange?.(nav.translation);
    }
    if (chronoOn) {
      // EXTERNAL jump (from Search / Lexicon / a note list — flagged `nav.extern`) → drop to
      // canonical so the reference shows in its NORMAL chapter, not dumped mid-passage. But the
      // IN-READER controls (a verse-number cross-ref, a word panel, chasing a cross-ref — all
      // triggered while reading chronologically) STAY in chrono: move to the passage that holds the
      // target verse (passageForRef, narrowed by the verse for a split chapter). If it's already the
      // current passage (e.g. just opening the xref on a verse you're reading) this is a no-op — and
      // the `p.pos !== chronoPos` guard also stops the scroll:false self-update from re-firing it.
      if (nav.extern) {
        setOrderMode("canonical"); // fall through to the canonical reset below
      } else {
        const p = passageForRef(b.abbrev, nav.chapter || 1, nav.highlight);
        if (p && p.pos !== chronoPos) {
          if (corpus !== "bible") setCorpus("bible");
          setOtherOpen(false);
          setChronoPos(p.pos);
          setSelBook(b);
          setSelChapter(p.start_ch);
        }
        return;
      }
    }

    // Only react to a REAL destination change. The scroll-to-highlight step writes a `scroll: false`
    // self-update back to nav (same book + chapter); without this guard that re-fires the reset
    // below, wiping the just-loaded verses → blank chapter. Skip the guard when we just left chrono:
    // order flipped, so we must load even if the chapter number happens to match.
    if (!chronoOn && corpus === "bible" && selBook?.abbrev === b.abbrev && selChapter === (nav.chapter || 1)) return;
    setCorpus("bible"); // a verse reference is a Bible verse — leave any open non-canonical text
    setOtherOpen(false); // close the "Other" picker if it was open
    // clear the old chapter's verses so the scroll-to-highlight waits for the NEW
    // chapter (otherwise it can fire on a stale same-numbered verse and burn its flag)
    setVerses([]);
    setKjvVerses([]);
    setBsbVerses([]);
    setSelBook(b);
    setSelChapter(nav.chapter || 1);
  }, [nav, books]);
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn) return; // non-canon + chronological load via their own effects below
    let cancelled = false;
    setLoading(true);
    setVerses([]);
    api.chapter(selBook.abbrev, selChapter).then(data => {
      if (!cancelled) {
        setVerses(data);
        setLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [selBook && selBook.abbrev, selChapter, corpus, chronoOn]);

  // Chronological span loader: fetch every chapter the current passage covers, for
  // the active text(s). One state object keyed by chapter; the render trims each
  // chapter to the passage's verse window and stitches them with chapter markers.
  useEffect(() => {
    if (!chronoOn || !curPassage || !selBook) return;
    let cancelled = false;
    setChronoLoading(true);
    const {
      book,
      start_ch,
      end_ch
    } = curPassage;
    const chs = [];
    for (let c = start_ch; c <= end_ch; c++) chs.push(c);
    const need = translation === "parallel" ? compareSel : [translation];
    const fetchChapter = c => {
      const jobs = [];
      if (need.includes("abp")) jobs.push(api.chapter(book, c).then(d => ["abp", d]));
      if (need.includes("kjv")) jobs.push(api.kjvChapter(book, c).then(d => ["kjv", d]));
      if (need.includes("bsb")) jobs.push(api.bsbChapter(book, c).then(d => ["bsb", d]));
      if (need.includes("esv")) jobs.push(api.esvChapter(book, c).then(d => ["esv", d]));
      if (need.includes("niv")) jobs.push(api.nivChapter(book, c).then(d => ["niv", d]));
      return Promise.all(jobs).then(pairs => [c, Object.fromEntries(pairs)]);
    };
    Promise.all(chs.map(fetchChapter)).then(entries => {
      if (cancelled) return;
      setChronoData({
        pos: curPassage.pos,
        byCh: Object.fromEntries(entries)
      });
      setChronoLoading(false);
    }).catch(() => {
      if (!cancelled) setChronoLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [chronoOn, chronoPos, translation, corpus, compareSel]);

  // Non-canonical text loader (Didache, etc.) — keyed on the active text id + chapter.
  useEffect(() => {
    if (!nonCanon) return;
    let cancelled = false;
    setDidLoading(true);
    setDidVerses([]);
    api.extraChapter(nonCanon.id, selChapter).then(data => {
      if (!cancelled) {
        setDidVerses(data);
        setDidLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setDidLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [corpus, selChapter]);
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn) return;
    if (translation !== "kjv" && !(translation === "parallel" && compareSel.includes("kjv"))) return;
    let cancelled = false;
    setKjvLoading(true);
    setKjvVerses([]);
    api.kjvChapter(selBook.abbrev, selChapter).then(data => {
      if (!cancelled) {
        setKjvVerses(data);
        setKjvLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setKjvLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn, compareSel]);

  // BSB chapter loader — when BSB is the reading text OR a selected compare column.
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn) return;
    if (translation !== "bsb" && !(translation === "parallel" && compareSel.includes("bsb"))) return;
    let cancelled = false;
    setBsbLoading(true);
    setBsbVerses([]);
    api.bsbChapter(selBook.abbrev, selChapter).then(data => {
      if (!cancelled) {
        setBsbVerses(data);
        setBsbLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setBsbLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn, compareSel]);

  // ESV chapter loader — owner-only reading text. Each fetch carries the login
  // token; the server returns 404 (and api.esvChapter yields []) for non-owners.
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn || !esvOwner) return;
    if (translation !== "esv" && !(translation === "parallel" && compareSel.includes("esv"))) return;
    let cancelled = false;
    setEsvLoading(true);
    setEsvVerses([]);
    api.esvChapter(selBook.abbrev, selChapter).then(data => {
      if (!cancelled) {
        setEsvVerses(data);
        setEsvLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setEsvLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn, esvOwner, compareSel]);

  // NIV chapter loader — owner-only reading text (same as ESV, text only).
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn || !nivOwner) return;
    if (translation !== "niv" && !(translation === "parallel" && compareSel.includes("niv"))) return;
    let cancelled = false;
    setNivLoading(true);
    setNivVerses([]);
    api.nivChapter(selBook.abbrev, selChapter).then(data => {
      if (!cancelled) {
        setNivVerses(data);
        setNivLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setNivLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn, nivOwner, compareSel]);

  // Hebrew OT interlinear loader — PUBLIC text, OT books only, single-read mode
  // (not wired into compare / chronological yet).
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn) return;
    if (translation !== "heb" || NT_BOOKS.has(selBook.abbrev)) return;
    let cancelled = false;
    setHebLoading(true);
    setHebVerses([]);
    api.hebChapter(selBook.abbrev, selChapter).then(data => {
      if (!cancelled) {
        setHebVerses(data);
        setHebLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setHebLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn]);

  // Reset the chapter audio when the reading changes — the old mp3 is for the
  // previous chapter/passage. Press Listen to fetch the new one. (chronoPos covers
  // moving between chronological passages, which doesn't change selChapter.)
  useEffect(() => {
    setAudioUrl(null);
    setAudioKey(null);
    setAudioBusy(false);
    setAudioPlaying(false);
    setAudioCur(0);
    setAudioDur(0);
    // If the change was a page-turn while audio was playing, keep listening: load the
    // new chapter/passage and let the audioUrl effect auto-play it (no need to leave
    // reading mode to press play again).
    if (resumeAudioRef.current) {
      resumeAudioRef.current = false;
      const b = chronoOn ? curPassage && curPassage.book : selBook && selBook.abbrev;
      const c = chronoOn ? curPassage && curPassage.start_ch : selChapter;
      if (b && c) loadAudio(b, c);
    }
  }, [selBook && selBook.abbrev, selChapter, translation, chronoPos]);
  // New mp3 loaded: start playing (the user already pressed Listen).
  useEffect(() => {
    const a = audioRef.current;
    if (!a || !audioUrl) return;
    a.load();
    a.play().catch(() => {});
  }, [audioUrl]);
  const loadAudio = (book, ch) => {
    if (!book) return;
    setAudioBusy(true);
    const fetchUrl = translation === "esv" ? api.esvAudio : translation === "kjv" ? api.kjvAudio : api.bsbAudio;
    fetchUrl(book, ch).then(d => {
      setAudioBusy(false);
      if (d && d.url) {
        setAudioUrl(d.url);
        setAudioKey(book + "-" + ch);
      } else flash("No audio for this chapter");
    }).catch(() => {
      setAudioBusy(false);
      flash("Audio unavailable");
    });
  };
  const seekAudio = e => {
    const a = audioRef.current;
    if (!a) return;
    const v = Number(e.target.value);
    a.currentTime = v;
    setAudioCur(v);
  };
  useEffect(() => {
    if (!nav?.scroll || loading) return;
    if (chronoOn) {
      // An EXTERNAL jump is mid-flip to canonical — wait for that render so we don't briefly scroll
      // (and burn the scroll flag on) the chrono passage. An INTERNAL jump (xref chase / read-in-
      // context) stays chronological: the nav effect moved chronoPos to the verse's passage, so wait
      // for that span to load, then the retry loop finds the highlighted row.
      if (nav.extern) return;
      if (!chronoData || chronoData.pos !== chronoPos) return;
    } else {
      if (!verses.length) return;
      // Don't scroll while the requested chapter's verses are still the OLD chapter's —
      // otherwise we scroll to (and burn the scroll flag on) a wrong same-numbered verse.
      if (nav.chapter != null && nav.chapter !== selChapter) return;
    }
    let raf,
      tries = 0;
    const tryScroll = () => {
      if (highlightRef.current) {
        // Land the verse in the UPPER THIRD (context above, room to read forward) —
        // not dead center. The row carries scroll-margin-top: 30vh (styles.css), so
        // block:"start" stops 30% down. scrollIntoView finds the right scroller on its
        // own (the window, or the fixed focus-mode page), so this works in every mode.
        highlightRef.current.scrollIntoView({
          behavior: nav.instant ? "auto" : "smooth",
          block: "start"
        });
        onNavChange?.({
          ...nav,
          scroll: false
        });
      } else if (tries++ < 30) {
        raf = requestAnimationFrame(tryScroll); // highlight row not rendered yet — keep waiting
      }
    };
    raf = requestAnimationFrame(tryScroll);
    return () => cancelAnimationFrame(raf);
    // kjvVerses is in the deps so a KJV-mode jump re-runs once the KJV rows render (the highlight
    // ref lives on those rows, which load separately from the ABP set). chronoData/chronoOn re-run it
    // once an internal chrono jump's passage loads, or after an external jump flips to canonical.
  }, [nav?.scroll, nav?.highlight, nav?.chapter, verses, kjvVerses, bsbVerses, loading, selChapter, chronoOn, chronoData, chronoPos]);
  const maxChap = nonCanon ? nonCanon.chapters : selBook ? selBook.chapters : 1;

  // Pick a non-canonical text (from the "Other" menu / nav): switch the reader to it and
  // start at chapter 1. Parallel/KJV/BSB have no meaning for a non-canonical text,
  // so any of those falls back to the Greek interlinear (ABP single view).
  const pickNonCanon = t => {
    setCorpus(t.id);
    setSelChapter(1);
    setOtherOpen(false);
    if (translation === "kjv" || translation === "bsb" || translation === "esv" || translation === "niv" || translation === "parallel") {
      setTranslation("abp");
      onTranslationChange?.("abp");
    }
  };
  // Picking a Bible book from the nav returns to the Bible text.
  const selectBook = b => {
    setSelBook(b);
    setCorpus("bible");
  };
  // ABP / KJV always select a Bible edition — and clicking either while a
  // non-canonical text is open is the quick way back to the Bible.
  const pickBible = edition => {
    setCorpus("bible");
    setTranslation(edition);
    onTranslationChange?.(edition);
    setOtherOpen(false); // picking a row text collapses the "More" menu if it was open
    if (selBook && selChapter > selBook.chapters) setSelChapter(selBook.chapters);
  };
  // Compare (parallel): pick 2-4 texts to show side by side. The picker's "active"
  // set is the parallel selection when on, else just the current single edition (so
  // opening the menu pre-checks what you're reading). Checking a 2nd text turns
  // compare ON; dropping below 2 falls back to a single view. Bible only.
  const COMPARE_ORDER = ["abp", "kjv", "bsb", "esv", "niv"];
  const compareAvail = COMPARE_ORDER.filter(id => id === "esv" ? esvOwner : id === "niv" ? nivOwner : true);
  const compareActive = translation === "parallel" ? compareSel.filter(id => compareAvail.includes(id)) : COMPARE_ORDER.includes(translation) ? [translation] : ["abp"];
  const toggleCompare = id => {
    const set = compareActive.includes(id) ? compareActive.filter(x => x !== id) : [...compareActive, id];
    const ordered = COMPARE_ORDER.filter(x => set.includes(x) && compareAvail.includes(x));
    setCompareSel(ordered);
    if (ordered.length >= 2) {
      setTranslation("parallel");
      onTranslationChange?.("parallel");
    } else {
      const fb = ordered[0] || "abp";
      setTranslation(fb);
      onTranslationChange?.(fb);
    }
  };
  // Plain on/off toggle (used by the mobile sheet header + as a quick flip). Turning
  // on keeps the current compareSel if it already has 2+, else defaults to ABP|KJV.
  const toggleParallel = () => {
    if (translation === "parallel") {
      setTranslation("abp");
      onTranslationChange?.("abp");
    } else {
      setCompareSel(prev => prev.filter(id => compareAvail.includes(id)).length >= 2 ? prev : ["abp", "kjv"]);
      setTranslation("parallel");
      onTranslationChange?.("parallel");
    }
  };
  // In-text search: which text to search. Bible → the active edition (Parallel
  // searches the English/KJV column); a non-canonical reader → that text's id.
  const readCorpus = corpus === "bible" ? translation === "parallel" ? "kjv" : translation : corpus;
  // ESV has no plain-text search route (owner-only reading text), so the reader's
  // in-text find is off for it — every other text supports it.
  const canSearch = !!readCorpus && translation !== "esv" && translation !== "niv";
  const searchName = corpus === "bible" ? readCorpus.toUpperCase() : nonCanon ? nonCanon.name : "";
  const runTextSearch = () => {
    const q = searchQ.trim();
    if (!q || !readCorpus) return;
    didSearchRef.current = true;
    const terms = searchMode === "phrase" ? [q] : q.split(/\s+/);
    setSearchHi({
      terms,
      partial: searchPartial,
      caseSensitive: searchCase
    });
    setSearchLoading(true);
    setSearchResults(null);
    setSearchCounts(null);
    const opts = {
      mode: searchMode,
      partial: searchPartial,
      caseSensitive: searchCase,
      exclude: searchExclude.trim()
    };
    // Range only applies to the Bible texts (non-canon is a single book).
    if (corpus === "bible") {
      opts.from = searchFrom;
      opts.to = searchTo;
    }
    api.textSearch(q, readCorpus, opts).then(d => {
      setSearchResults(d.results || []);
      setSearchCounts({
        verses: d.verse_count || 0,
        matches: d.match_count || 0,
        capped: !!d.capped
      });
      setSearchLoading(false);
    }).catch(() => {
      setSearchResults([]);
      setSearchCounts(null);
      setSearchLoading(false);
    });
  };
  // Apply a range preset (sets the from/to book pickers).
  const applyRangePreset = id => {
    const r = SEARCH_RANGES.find(x => x.id === id);
    if (r) {
      setSearchFrom(r.from);
      setSearchTo(r.to);
    }
  };
  // Which preset (if any) the current from/to pair matches — for the dropdown's value.
  const activeRangeId = (SEARCH_RANGES.find(r => r.from === searchFrom && r.to === searchTo) || {}).id || "custom";
  // Once a search has run, changing mode / range / whole-word / case re-runs it
  // automatically so the list never sits stale against the controls. (Exclude
  // re-runs on Enter — it's typed, so we don't fire on every keystroke.)
  useEffect(() => {
    if (!didSearchRef.current || !searchQ.trim() || !readCorpus) return;
    runTextSearch();
  }, [searchMode, searchPartial, searchCase, searchFrom, searchTo]);
  // Jump to a hit. Bible → the shared nav path (loads chapter, highlights +
  // scrolls). Non-canonical → same text, just switch to that chapter.
  const jumpToResult = r => {
    setSearchOpen(false);
    if (corpus === "bible") {
      onNavChange?.({
        book: r.book,
        chapter: r.chapter,
        highlight: r.verse,
        scroll: true,
        translation
      });
    } else {
      setSelChapter(r.chapter);
    }
  };
  const showStrongs = libOptions.showStrongs || false;
  const showInterlinear = libOptions.showInterlinear || false;
  const viewMode = libOptions.viewMode || "chip";
  const setOpt = (key, val) => setLibOptions(prev => ({
    ...prev,
    [key]: val
  }));

  // English-only non-canonical texts (e.g. 1 Enoch) and ESV/NIV (no per-word data)
  // are locked to Prose and the Greek/Strong's toggles (Strong's / Interlinear /
  // Chip) are disabled and grayed out. BSB now has its own per-word Strong's data
  // (bsb_words), so it is NOT prose-locked — it gets chip mode like KJV.
  const bsbMode = translation === "bsb";
  const esvMode = translation === "esv";
  const nivMode = translation === "niv";
  const kjvMode = translation === "kjv"; // KJV has public-domain audio (no key)
  const hebMode = translation === "heb"; // Hebrew interlinear: always chips, no prose option
  const proseLocked = !!(nonCanon && nonCanon.englishOnly) || esvMode || nivMode;
  const chipMode = !proseLocked && (viewMode === "chip" || showStrongs || showInterlinear);
  const wordMode = chipMode;
  const kjvWordMode = chipMode;
  // English-only "other books" have no Greek interlinear, so the Strong's / Interlinear
  // toggles stay locked — but they CAN switch between a verse-per-line layout (the
  // "chip" slot) and flowing prose. layoutLocked = can't even pick line vs flow.
  const extraEnglish = !!(nonCanon && nonCanon.englishOnly);
  const extraLineMode = extraEnglish && viewMode === "chip";
  const layoutLocked = proseLocked && !extraEnglish;
  const viewChipOn = hebMode ? true : extraEnglish ? viewMode === "chip" : chipMode;
  const POETRY_BOOKS = new Set(["Psa", "Pro", "Job", "Son", "Lam", "Ecc"]);
  const isPoetry = POETRY_BOOKS.has(selBook?.abbrev);

  // HEB toggle: public (shows whenever the Hebrew data is loaded), OT books only (no
  // Hebrew NT), and not while a non-canon text is open.
  // hebShown = the OT-only Hebrew text exists as an option (heb.db loaded, reading the Bible).
  // hebPickable = and it's usable on the CURRENT book (an OT book). On NT books we keep the
  // selector VISIBLE but disabled/grayed, so it doesn't vanish out from under you.
  const hebShown = hebAvail && !nonCanon && !!selBook;
  const hebPickable = hebShown && !NT_BOOKS.has(selBook.abbrev);

  // ---- Chronological span assembly --------------------------------------
  // Pull the active text(s) for the current passage out of the loaded span,
  // trim each chapter to the passage's verse window, and tag every verse with
  // its chapter (_ch). The renderers read _ch (defaulting to selChapter), so
  // canonical reading is unchanged — _ch is simply absent there.
  const chronoReady = chronoOn && chronoData && chronoData.pos === chronoPos;
  const flattenSpan = key => {
    if (!chronoReady || !curPassage) return [];
    const {
      start_ch,
      end_ch,
      start_v,
      end_v
    } = curPassage;
    const out = [];
    for (let c = start_ch; c <= end_ch; c++) {
      const arr = chronoData.byCh[c] && chronoData.byCh[c][key] || [];
      const lo = c === start_ch ? start_v : 1;
      const hi = c === end_ch ? end_v : Infinity;
      arr.forEach(v => {
        if (v.verse >= lo && v.verse <= hi) out.push({
          ...v,
          _ch: c
        });
      });
    }
    return out;
  };
  const abpView = chronoOn ? flattenSpan("abp") : verses;
  const kjvView = chronoOn ? flattenSpan("kjv") : kjvVerses;
  const bsbView = chronoOn ? flattenSpan("bsb") : bsbVerses;
  const esvView = chronoOn ? flattenSpan("esv") : esvVerses;
  const nivView = chronoOn ? flattenSpan("niv") : nivVerses;
  // BSB chips need the per-word data (bsb_words). If it isn't loaded yet, the
  // chapter feed has empty `words`, so fall back to prose even in chip mode —
  // safe to ship the frontend before the data load.
  const bsbHasWords = bsbView.some(v => v.words && v.words.length);
  const bsbWordMode = chipMode && bsbHasWords;
  // A heading each time the chapter changes within a passage. EVERY chrono passage gets
  // one now — single-chapter ones too (they were skipped before, which is why Genesis 6
  // and the like showed no book/chapter label at all). When a passage only covers part of
  // a chapter, the heading shows the verse range so partial readings are obvious
  // (e.g. "1 Chronicles 1:1–4", "Genesis 10:1–5").
  const chronoChapLabel = c => {
    const name = selBook ? selBook.name : "";
    if (!curPassage) return `${name} ${c}`;
    const {
      start_ch,
      end_ch,
      start_v,
      end_v
    } = curPassage;
    const primaryKey = translation === "parallel" ? compareSel[0] || "abp" : translation;
    const full = chronoData && chronoData.byCh[c] && chronoData.byCh[c][primaryKey] || [];
    const maxV = full.length ? full[full.length - 1].verse : null; // whole chapter is loaded → last verse = its length
    const lo = c === start_ch ? start_v : 1;
    const hi = c === end_ch ? end_v : maxV;
    const partial = lo > 1 || maxV != null && hi != null && hi < maxV;
    return partial && hi != null ? `${name} ${c}:${lo}–${hi}` : `${name} ${c}`;
  };
  const withMarks = (arr, renderFn) => {
    const out = [];
    let lastCh = null;
    arr.forEach(v => {
      if (v._ch != null && v._ch !== lastCh) {
        out.push(/*#__PURE__*/React.createElement("div", {
          key: `cm-${v._ch}`,
          "data-ch": v._ch,
          className: "lib-chrono-chapmark"
        }, chronoChapLabel(v._ch)));
        lastCh = v._ch;
      }
      out.push(renderFn(v));
    });
    return out;
  };
  const abpShowLoading = chronoOn ? chronoLoading || !chronoReady : loading;
  const kjvShowLoading = chronoOn ? chronoLoading || !chronoReady : kjvLoading;
  const bsbShowLoading = chronoOn ? chronoLoading || !chronoReady : bsbLoading;
  const esvShowLoading = chronoOn ? chronoLoading || !chronoReady : esvLoading;
  const nivShowLoading = chronoOn ? chronoLoading || !chronoReady : nivLoading;
  // Chapter audio (BSB + ESV only). Audio is one file per WHOLE chapter. ONE play/pause
  // icon in the toolbar + a progress bar under the toolbar (desktop AND mobile, same
  // spot). The button targets the chapter you're reading: canonical = the open chapter;
  // chrono = whichever chapter is scrolled into view (viewCh). Press play and you get
  // that chapter; it auto-advances to the next when one ends.
  const audioCapable = bsbMode || esvMode || kjvMode;
  const audioTarget = audioCapable ? {
    book: chronoOn ? curPassage && curPassage.book : selBook && selBook.abbrev,
    ch: chronoOn ? viewCh || curPassage && curPassage.start_ch : selChapter
  } : null;
  const targetKey = audioTarget && audioTarget.book ? audioTarget.book + "-" + audioTarget.ch : null;
  const onTargetNow = !!targetKey && audioKey === targetKey; // the chapter in view IS the loaded one
  // The icon follows ONLY whether sound is playing, so scrolling never desyncs it.
  const showPause = audioPlaying;
  const onToolbarAudio = () => {
    if (!audioTarget || !audioTarget.book || !audioTarget.ch) return;
    const a = audioRef.current;
    if (a && !a.paused) {
      a.pause();
      return;
    } // playing → pause
    if (a && onTargetNow) {
      a.play().catch(() => {});
      return;
    } // paused on the chapter in view → resume
    loadAudio(audioTarget.book, audioTarget.ch); // else start / switch to the chapter in view
  };
  const onAudioEnded = () => {
    setAudioPlaying(false);
    if (chronoOn && curPassage && audioKey) {
      const cur = parseInt(audioKey.split("-")[1], 10); // chrono: roll into the next chapter of the passage
      if (cur < curPassage.end_ch) {
        loadAudio(curPassage.book, cur + 1);
        return;
      }
    }
    setAudioUrl(null);
    setAudioKey(null); // canonical end, or chrono passage finished → scrubber goes away
  };
  // The (invisible) audio element renders once while a chapter is loaded so it can play.
  const audioEl = audioCapable && audioUrl ? /*#__PURE__*/React.createElement("audio", {
    ref: audioRef,
    src: audioUrl,
    preload: "metadata",
    onLoadedMetadata: e => setAudioDur(e.target.duration || 0),
    onTimeUpdate: e => setAudioCur(e.target.currentTime || 0),
    onPlay: () => setAudioPlaying(true),
    onPause: () => setAudioPlaying(false),
    onEnded: onAudioEnded
  }) : null;
  const audioProgress = /*#__PURE__*/React.createElement("input", {
    className: "lib-audio-bar",
    type: "range",
    min: "0",
    max: audioDur || 0,
    step: "0.1",
    value: Math.min(audioCur, audioDur || 0),
    onChange: seekAudio,
    "aria-label": "Audio position"
  });
  // The bottom player only mounts once audio is loaded, so its button just plays/pauses
  // the current track (nothing to "start" — that's the toolbar/cockpit button's job).
  const onDockAudio = () => {
    const a = audioRef.current;
    if (!a) return;
    if (a.paused) a.play().catch(() => {});else a.pause();
  };
  // ONE self-contained player — play/pause + scrubber — docked at the bottom in every
  // mode, desktop AND mobile. It floats ABOVE the focus-mode wash so audio stays
  // controllable in reading mode (where the toolbar play/pause is hidden). Mobile
  // repositions it just above the bottom cockpit (CSS).
  const dockShown = !!audioEl;
  // When the dock disappears (chapter/passage ended), keep it mounted one beat so it can
  // slide OUT instead of vanishing. A re-open cancels the pending close.
  useEffect(() => {
    if (dockShown) {
      dockWasShown.current = true;
      if (dockClosing) setDockClosing(false);
    } else if (dockWasShown.current) {
      dockWasShown.current = false;
      setDockClosing(true);
      const t = setTimeout(() => setDockClosing(false), 240);
      return () => clearTimeout(t);
    }
  }, [dockShown]);
  const dockPlayer = /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    className: "lib-audio-dock-btn",
    onClick: onDockAudio,
    disabled: audioBusy,
    title: audioPlaying ? "Pause audio" : "Play audio",
    "aria-label": audioPlaying ? "Pause audio" : "Play audio",
    "aria-pressed": audioPlaying
  }, audioPlaying ? /*#__PURE__*/React.createElement(Icon.Pause, null) : /*#__PURE__*/React.createElement(Icon.Play, null)), audioProgress);
  const audioBar = audioEl ? /*#__PURE__*/React.createElement("div", {
    className: "lib-audio-dock"
  }, dockPlayer, audioEl) : dockClosing ? /*#__PURE__*/React.createElement("div", {
    className: "lib-audio-dock lib-audio-dock--out"
  }, dockPlayer) : null;
  const audioDockOn = !!audioEl; // drives the reading-list bottom clearance (desktop + mobile)
  const audioBtn = audioCapable ? /*#__PURE__*/React.createElement("button", {
    className: "lib-toggle lib-toggle-icon" + (showPause ? " on" : ""),
    disabled: audioBusy,
    title: showPause ? "Pause audio" : "Play chapter audio",
    "aria-label": showPause ? "Pause audio" : "Play chapter audio",
    "aria-pressed": showPause,
    onClick: onToolbarAudio
  }, showPause ? /*#__PURE__*/React.createElement(Icon.Pause, null) : /*#__PURE__*/React.createElement(Icon.Play, null)) : null;
  // Chrono: track which chapter is scrolled into view (~just above mid-screen), so the
  // toolbar play button AND the chapter overview both follow the chapter you're reading.
  useEffect(() => {
    if (!chronoOn) {
      setViewCh(null);
      return;
    }
    const compute = () => {
      const root = readingRef.current;
      if (!root) return;
      const marks = root.querySelectorAll(".lib-chrono-chapmark[data-ch]");
      // A single-chapter passage (e.g. Genesis 6, 1 Chronicles 1:1–4) renders no chapter
      // headings, so there's nothing to measure — pin to the passage's own chapter instead
      // of leaving viewCh stuck on the previous passage's chapter (which made the audio +
      // chapter overview load the wrong chapter, e.g. Genesis 4 while reading Genesis 6).
      if (!marks.length) {
        setViewCh(curPassage ? curPassage.start_ch : null);
        return;
      }
      // Switch when a chapter heading passes ~just-above the middle of the screen
      // (not the very top), so the "current" chapter matches what you're reading.
      const threshold = (window.innerHeight || 800) * 0.45;
      let cur = parseInt(marks[0].dataset.ch, 10);
      marks.forEach(m => {
        if (m.getBoundingClientRect().top <= threshold) cur = parseInt(m.dataset.ch, 10);
      });
      setViewCh(cur);
    };
    let raf = null;
    const onScroll = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = null;
        compute();
      });
    };
    compute();
    window.addEventListener("scroll", onScroll, true); // capture: also catches a nested scroll panel
    return () => {
      window.removeEventListener("scroll", onScroll, true);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [chronoOn, audioCapable, chronoPos, translation, chronoReady, curPassage && curPassage.start_ch]);

  // Chapter overview target — in chrono it follows the chapter scrolled into view
  // (same cutoff as the audio); otherwise the open chapter.
  const sumBook = nonCanon ? nonCanon.id : chronoOn && curPassage ? curPassage.book : selBook && selBook.abbrev;
  const sumChapter = chronoOn && curPassage ? viewCh || curPassage.start_ch : selChapter;
  const sumLabel = nonCanon ? nonCanon.name : BOOK_LABELS[sumBook] || sumBook;
  // The chronological reading "day" you're in — drives the Reading-intro panel. In
  // chrono the right panel shows that day's intro instead of the per-chapter overview.
  const currentDay = chronoOn && chrono && chrono.days ? chrono.days.find(d => d.pos && d.pos.includes(chronoPos)) : null;

  // Tell the app which panel is the current BASE of the detail rail, so a word/xref
  // panel opened on top of it labels its back link correctly ("‹ Intro" vs "‹ Overview").
  const detailBase = chronoOn && currentDay && chronoPanel === "intro" ? "intro" : "overview";
  useEffect(() => {
    onDetailBaseChange?.(detailBase);
  }, [detailBase]);

  // Turn one page: chronological steps a passage, everything else steps a chapter.
  // Shared by the mobile swipe and the desktop arrow keys (focus mode).
  const turnPage = dir => {
    // dir: +1 next, -1 prev
    if (chronoOn) {
      const can = dir > 0 ? chrono && chronoPos < chrono.passages.length : chronoPos > 1;
      if (!can) return;
      if (audioPlaying) resumeAudioRef.current = true; // carry the read-along onto the next passage
      stepPassage(dir);
      return;
    }
    const c = selChapter + dir;
    if (c < 1 || c > maxChap) return;
    if (audioPlaying) resumeAudioRef.current = true; // carry the read-along onto the next chapter
    setSelChapter(c);
    if (!nonCanon) onNavChange?.({
      ...nav,
      book: selBook?.abbrev,
      chapter: c,
      highlight: null
    });
  };
  const swipeRef = React.useRef(null);
  const tapMovedRef = React.useRef(false);
  const swipeHandlers = isMobile ? {
    onTouchStart: e => {
      tapMovedRef.current = false;
      swipeRef.current = {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY
      };
    },
    onTouchMove: e => {
      if (!swipeRef.current) return;
      const dx = e.touches[0].clientX - swipeRef.current.x;
      const dy = e.touches[0].clientY - swipeRef.current.y;
      if (Math.abs(dx) > 10 || Math.abs(dy) > 10) tapMovedRef.current = true;
    },
    // A swipe/scroll that ends over a word must NOT open its panel — only a real tap should.
    onClickCapture: e => {
      if (tapMovedRef.current) {
        e.stopPropagation();
        e.preventDefault();
      }
    },
    onTouchEnd: e => {
      if (!swipeRef.current) return;
      // If the touch produced a text selection (note-making), don't turn the page.
      if (window.getSelection && String(window.getSelection()).trim()) {
        swipeRef.current = null;
        return;
      }
      const dx = e.changedTouches[0].clientX - swipeRef.current.x;
      const dy = e.changedTouches[0].clientY - swipeRef.current.y;
      swipeRef.current = null;
      if (Math.abs(dx) < 50) return; // too short
      if (Math.abs(dy) > Math.abs(dx) * 0.6) return; // too vertical
      turnPage(dx < 0 ? 1 : -1); // left swipe = next, right swipe = prev
    }
  } : {};

  // --- Drag-select → note ---------------------------------------------------
  // Walk up from a selection edge to the nearest tagged verse row / word span.
  const _attrUp = (node, attr) => {
    let el = node && node.nodeType === 1 ? node : node ? node.parentElement : null;
    while (el && el !== readingRef.current && !(el.getAttribute && el.hasAttribute(attr))) el = el.parentElement;
    return el && el.getAttribute ? el.getAttribute(attr) : null;
  };
  const resolveSelection = () => {
    const sel = window.getSelection && window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) {
      setNoteSel(null);
      return;
    }
    const text = sel.toString().trim();
    if (!text) {
      setNoteSel(null);
      return;
    }
    const range = sel.getRangeAt(0);
    if (!readingRef.current || !readingRef.current.contains(range.commonAncestorContainer)) {
      setNoteSel(null);
      return;
    }
    const aV = _attrUp(range.startContainer, "data-note-verse");
    const bV = _attrUp(range.endContainer, "data-note-verse");
    if (aV == null && bV == null) {
      setNoteSel(null);
      return;
    }
    let startV = parseInt(aV != null ? aV : bV, 10);
    let endV = parseInt(bV != null ? bV : aV, 10);
    const aP = _attrUp(range.startContainer, "data-note-pos");
    const bP = _attrUp(range.endContainer, "data-note-pos");
    let startP = aP != null ? parseInt(aP, 10) : null;
    let endP = bP != null ? parseInt(bP, 10) : null;
    if (startV > endV || startV === endV && (startP || 0) > (endP || 0)) {
      [startV, endV] = [endV, startV];
      [startP, endP] = [endP, startP];
    }
    const bookId = nonCanon ? nonCanon.id : selBook ? selBook.abbrev : null;
    const bookName = nonCanon ? nonCanon.name : selBook ? selBook.name : "";
    if (!bookId) {
      setNoteSel(null);
      return;
    }
    // The chapter the selection sits in — from the row (chronological spans several
    // chapters), falling back to the single canonical chapter.
    const selCh = parseInt(_attrUp(range.startContainer, "data-note-chapter") || selChapter, 10);
    const refLabel = bookName + " " + selCh + ":" + startV + (endV !== startV ? "–" + endV : "");
    // In chip mode each word is its own chip with no space characters between
    // them, so the raw selected text runs together ("Inthebeginning"). Rebuild
    // the snippet from the visible English of the touched word chips instead;
    // that also drops the verse number. Prose/BSB keep real spaces, so fall back.
    let snippet = text;
    if (sel.containsNode) {
      const parts = [];
      readingRef.current.querySelectorAll(".lib-word, .lib-kjv-word").forEach(el => {
        if (sel.containsNode(el, true)) {
          const eng = el.querySelector(".lib-iw-english");
          const t = (eng ? eng.textContent : el.textContent).trim();
          if (t) parts.push(t);
        }
      });
      if (parts.length) snippet = parts.join(" ");
    }
    const r = range.getBoundingClientRect();
    justSelectedRef.current = true;
    swallowClickRef.current = false; // a real selection isn't a dismiss-click
    setNoteSel({
      rect: {
        top: r.top,
        left: r.left,
        width: r.width,
        height: r.height
      },
      anchor: {
        corpus,
        translation,
        book: bookId,
        bookName,
        chapter: selCh,
        start: {
          verse: startV,
          pos: startP
        },
        end: {
          verse: endV,
          pos: endP
        },
        snippet: snippet.slice(0, 300),
        refLabel
      }
    });
  };
  const addNoteFromSelection = () => {
    if (!noteSel) return;
    // Reuse a note already on this exact text instead of making a duplicate.
    const existing = NotesStore.findAnchor(noteSel.anchor);
    const note = existing || NotesStore.create(noteSel.anchor);
    setNoteSel(null);
    if (window.getSelection) window.getSelection().removeAllRanges(); // dismiss the OS selection toolbar
    onOpenNote && onOpenNote(note.id);
  };
  // A color swatch in the popover → make a highlight (no editor; the paint is it).
  // If this exact text already has a record, just recolor it.
  const addHighlightFromSelection = color => {
    if (!noteSel) return;
    const existing = NotesStore.findAnchor(noteSel.anchor);
    if (existing) NotesStore.update(existing.id, {
      color
    });else NotesStore.create({
      ...noteSel.anchor,
      color
    });
    setNoteSel(null);
    if (window.getSelection) window.getSelection().removeAllRanges();
  };
  // Copy the selected verse text to the clipboard (also clears the OS bar on mobile).
  const copySelection = () => {
    if (!noteSel) return;
    const txt = noteSel.anchor.snippet || "";
    try {
      if (navigator.clipboard) navigator.clipboard.writeText(txt);
    } catch (e) {}
    setNoteSel(null);
    if (window.getSelection) window.getSelection().removeAllRanges();
    flash("Copied");
  };
  // Drop "reference — verse text" into the journal page currently open in the Notes tab.
  const journalFromSelection = () => {
    if (!noteSel) return;
    const id = NotesStore.getActiveJournal();
    const a = noteSel.anchor;
    setNoteSel(null);
    if (window.getSelection) window.getSelection().removeAllRanges();
    if (!id) {
      flash("Open a journal page first");
      return;
    }
    NotesStore.appendToJournal(id, journalLine(a));
    flash("Added to journal");
  };
  // Mobile: the browser owns the touch-select gesture, so our touch handlers may
  // not fire. Watch for a settled selection and show the bottom "Add note" bar.
  const resolveRef = useRef(resolveSelection);
  resolveRef.current = resolveSelection;
  useEffect(() => {
    if (!isMobile) return;
    let t;
    const onSel = () => {
      clearTimeout(t);
      t = setTimeout(() => resolveRef.current(), 200);
    };
    document.addEventListener("selectionchange", onSel);
    return () => {
      document.removeEventListener("selectionchange", onSel);
      clearTimeout(t);
    };
  }, [isMobile]);
  // Focus mode: blank-space tap strips the chrome (header/nav/toolbar/tabs/audio)
  // for distraction-free reading. A one-time hint shows the way back out.
  const toggleFocus = () => {
    if (!focusMode) flash(isMobile ? "Tap anywhere to show the menus" : "Reading mode — tap the text or press Esc to exit");
    onToggleFocus && onToggleFocus();
  };
  // While focus is on: Esc brings the chrome back; arrow keys turn the page
  // (the toolbar's hidden, so this is the desktop page-turn). Ignore keys typed
  // into an input so search/notes fields aren't hijacked.
  useEffect(() => {
    if (!focusMode) return;
    const onKey = e => {
      if (e.target && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
      if (e.key === "Escape") {
        onToggleFocus && onToggleFocus();
      } else if (e.key === "ArrowRight") turnPage(1);else if (e.key === "ArrowLeft") turnPage(-1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusMode, chronoOn, selChapter, maxChap, nonCanon, chronoPos]);

  // One handler set on the reading area: swipe (mobile) + selection (all).
  const readingHandlers = {
    ...swipeHandlers,
    // A fresh press starts a new interaction: drop any open popover + the suppress flag.
    onMouseDown: () => {
      if (noteSel) {
        setNoteSel(null);
        swallowClickRef.current = true;
      }
      justSelectedRef.current = false;
    },
    onMouseUp: () => resolveSelection(),
    onTouchEnd: e => {
      if (swipeHandlers.onTouchEnd) swipeHandlers.onTouchEnd(e);
      setTimeout(resolveSelection, 0); // let the browser settle the selection first
    },
    onClickCapture: e => {
      // The click that ENDS a selection must keep the popover showing — swallow it
      // (so it doesn't also hit a chip / verse number / focus) but leave noteSel set.
      if (justSelectedRef.current) {
        justSelectedRef.current = false;
        e.stopPropagation();
        e.preventDefault();
        return;
      }
      // A press that closed the popover flagged this click to be eaten — so dismissing
      // the popover doesn't also hit a chip / verse number / focus. (Popover buttons sit
      // outside the reading area, so they're unaffected.)
      if (swallowClickRef.current) {
        swallowClickRef.current = false;
        e.stopPropagation();
        e.preventDefault();
        return;
      }
      if (swipeHandlers.onClickCapture) swipeHandlers.onClickCapture(e);
    },
    // Tap on blank space (not a word / verse number / control, and not mid-selection)
    // toggles focus mode. A swipe or a finished selection sets defaultPrevented above.
    onClick: e => {
      if (e.defaultPrevented) return;
      if (window.getSelection && String(window.getSelection())) return;
      if (e.target.closest && e.target.closest(".lib-word, .lib-vnum, .lib-flow-vnum, button, a, input, textarea, [contenteditable]")) return;
      toggleFocus();
    }
  };

  // Notes/highlights are looked up per chapter. Canonical reading is one chapter
  // (ch defaults to selChapter); chronological spans several, so every note helper
  // takes the verse's chapter. A small per-render cache avoids re-querying the
  // store for each verse in a chapter.
  const noteBookId = nonCanon ? nonCanon.id : selBook ? selBook.abbrev : null;
  const _chNoteCache = {};
  const chapterNotesFor = ch => {
    if (!(ch in _chNoteCache)) _chNoteCache[ch] = NotesStore.forChapter(corpus, noteBookId, ch);
    return _chNoteCache[ch];
  };
  const noteForVerse = (verse, ch = selChapter) => chapterNotesFor(ch).find(n => verse >= n.start.verse && verse <= (n.end && n.end.verse || n.start.verse));
  // Highlight paint: the color (if any) for a given word. Highlights show in
  // EVERY translation (verses always line up). In the text where the highlight
  // was made we paint the exact words; in a DIFFERENT translation we can't line
  // up word-for-word, so a partial highlight rounds up to the whole verse.
  const hiForWord = (verse, pos, ch = selChapter) => {
    for (const n of chapterNotesFor(ch)) {
      if (!n.color) continue;
      const sv = n.start.verse,
        ev = n.end && n.end.verse || sv;
      if (verse < sv || verse > ev) continue;
      const sameText = !n.translation || !translation || n.translation === translation;
      const sp = n.start.pos,
        ep = n.end ? n.end.pos : null;
      if (!sameText || sp == null || pos == null) return n.color; // whole-verse paint
      if (verse === sv && pos < sp) continue;
      if (verse === ev && ep != null && pos > ep) continue;
      return n.color;
    }
    return null;
  };
  const hiClass = (verse, pos, ch = selChapter) => {
    const c = hiForWord(verse, pos, ch);
    return c ? " lib-hi lib-hi-" + c : "";
  };
  // A record is shown with a bookmark icon only when it's a PLAIN bookmark; once it
  // carries a note or a highlight color it shows the note (pencil) icon instead.
  const isBookmarkOnly = n => !!(n && n.bookmark && !n.body && !n.color);
  const markerIcon = n => isBookmarkOnly(n) ? /*#__PURE__*/React.createElement(Icon.Bookmark, null) : /*#__PURE__*/React.createElement(Icon.Note, null);
  const markerLabel = n => isBookmarkOnly(n) ? "Open bookmark" : "Open note";
  const noteMarker = (verse, ch = selChapter) => {
    const n = noteForVerse(verse, ch);
    if (!n) return null;
    return /*#__PURE__*/React.createElement("button", {
      className: "lib-note-dot",
      title: markerLabel(n),
      "aria-label": markerLabel(n),
      onClick: e => {
        e.stopPropagation();
        onOpenNote && onOpenNote(n.id);
      }
    }, markerIcon(n));
  };
  // Inline variant (prose flow / non-canon) — same icon logic, inline placement.
  const noteDotInline = (verse, ch = selChapter) => {
    const n = noteForVerse(verse, ch);
    if (!n) return null;
    return /*#__PURE__*/React.createElement("button", {
      className: "lib-note-dot lib-note-dot-inline",
      title: markerLabel(n),
      "aria-label": markerLabel(n),
      onClick: e => {
        e.stopPropagation();
        onOpenNote && onOpenNote(n.id);
      }
    }, markerIcon(n));
  };
  // Build the whole-verse anchor (incl. a readable snippet) for a verse number.
  const verseAnchor = (verse, fromEl, ch = selChapter) => {
    const bookId = nonCanon ? nonCanon.id : selBook ? selBook.abbrev : null;
    const bookName = nonCanon ? nonCanon.name : selBook ? selBook.name : "";
    if (!bookId) return null;
    // Snippet = the verse's words. Chip rows pack words with no spaces, so pull
    // the visible English of each chip; otherwise read the verse text (works for
    // both the verse-row layout and the running-prose flow span, after dropping
    // the verse number + note marker).
    let snippet = "";
    const row = fromEl && fromEl.closest("[data-note-verse]");
    if (row) {
      const chips = row.querySelectorAll(".lib-word, .lib-kjv-word");
      if (chips.length) {
        const parts = [];
        chips.forEach(el => {
          const eng = el.querySelector(".lib-iw-english");
          const t = (eng ? eng.textContent : el.textContent).trim();
          if (t) parts.push(t);
        });
        snippet = parts.join(" ");
      } else {
        const clone = row.cloneNode(true);
        clone.querySelectorAll(".lib-vnum, .lib-flow-vnum, .lib-note-dot").forEach(el => el.remove());
        snippet = (clone.textContent || "").trim();
      }
    }
    return {
      corpus,
      translation,
      book: bookId,
      bookName,
      chapter: ch,
      start: {
        verse,
        pos: null
      },
      end: {
        verse,
        pos: null
      },
      snippet: snippet.slice(0, 300),
      refLabel: bookName + " " + ch + ":" + verse
    };
  };
  // Right-click / long-press a verse number opens a small menu (Bookmark · Note ·
  // colors). Left-click / tap stays cross-references.
  const [verseMenu, setVerseMenu] = useState(null); // { rect, verse, el } | null
  const openVerseMenu = (verse, el, ch = selChapter) => {
    const r = el.getBoundingClientRect();
    setVerseMenu({
      rect: {
        top: r.top,
        left: r.left,
        width: r.width,
        height: r.height
      },
      verse,
      el,
      ch
    });
  };
  const vmBookmark = () => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch);
    if (!a) return setVerseMenu(null);
    const ex = NotesStore.findAnchor(a);
    if (ex) NotesStore.update(ex.id, {
      bookmark: true
    });else NotesStore.create({
      ...a,
      bookmark: true
    });
    setVerseMenu(null);
  };
  const vmNote = () => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch);
    if (!a) return setVerseMenu(null);
    const ex = NotesStore.findAnchor(a);
    const note = ex || NotesStore.create(a);
    setVerseMenu(null);
    onOpenNote && onOpenNote(note.id);
  };
  const vmColor = color => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch);
    if (!a) return setVerseMenu(null);
    const ex = NotesStore.findAnchor(a);
    if (ex) NotesStore.update(ex.id, {
      color
    });else NotesStore.create({
      ...a,
      color
    });
    setVerseMenu(null);
  };
  // Copy the whole verse text to the clipboard.
  const vmCopy = () => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch);
    if (!a) return setVerseMenu(null);
    setVerseMenu(null);
    try {
      if (navigator.clipboard) navigator.clipboard.writeText(a.snippet || "");
    } catch (e) {}
    flash("Copied");
  };
  // Send the whole verse to the journal page currently open in the Notes tab.
  const vmJournal = () => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch);
    if (!a) return setVerseMenu(null);
    setVerseMenu(null);
    const id = NotesStore.getActiveJournal();
    if (!id) {
      flash("Open a journal page first");
      return;
    }
    NotesStore.appendToJournal(id, journalLine(a));
    flash("Added to journal");
  };
  // Shared press handlers for a verse number: right-click + mobile long-press.
  const vnumPressRef = useRef({
    timer: null,
    fired: false
  });
  const vnumNoteHandlers = (verse, ch = selChapter) => ({
    onContextMenu: e => {
      e.preventDefault();
      openVerseMenu(verse, e.currentTarget, ch);
    },
    onTouchStart: e => {
      const el = e.currentTarget;
      const st = vnumPressRef.current;
      st.fired = false;
      clearTimeout(st.timer);
      st.timer = setTimeout(() => {
        st.fired = true;
        openVerseMenu(verse, el, ch);
        if (navigator.vibrate) navigator.vibrate(12);
      }, 500);
    },
    onTouchMove: () => clearTimeout(vnumPressRef.current.timer),
    onTouchEnd: () => clearTimeout(vnumPressRef.current.timer)
  });
  const changeFontSize = delta => {
    setLibFontSize(prev => {
      const next = Math.min(24, Math.max(13, prev + delta));
      localStorage.setItem("libFontSize", String(next));
      return next;
    });
  };
  const handleVerseNum = onVerseNumberClick && selBook ? (verse, ch = selChapter) => onVerseNumberClick(selBook.abbrev, ch, verse, translation) : null;

  // Outer span = the alignment gutter (fixed width, not interactive). Inner span =
  // the actual hit target, sized to the digits, so clicking the empty space beside
  // the number does nothing (and can't start a verse-wide text selection).
  const vnumEl = (verse, ch = selChapter) => /*#__PURE__*/React.createElement("span", {
    className: "lib-vnum"
  }, /*#__PURE__*/React.createElement("span", _extends({
    className: "lib-vnum-num" + (handleVerseNum ? " lib-vnum-click" : ""),
    title: handleVerseNum ? "Click: cross-references · Right-click / long-press: add a note" : undefined,
    onClick: handleVerseNum ? () => {
      if (vnumPressRef.current.fired) {
        vnumPressRef.current.fired = false;
        return;
      }
      handleVerseNum(verse, ch);
    } : undefined
  }, vnumNoteHandlers(verse, ch)), verse));

  // Verse number for non-canonical texts: opens the note menu on right-click /
  // long-press, but no cross-references (those texts have none). Left-click is a no-op
  // (just swallows the click that follows a long-press).
  const noteVnum = (verse, cls = "lib-vnum") => /*#__PURE__*/React.createElement("span", {
    className: cls
  }, /*#__PURE__*/React.createElement("span", _extends({
    className: "lib-vnum-num lib-vnum-click",
    title: "Right-click / long-press: add a note",
    onClick: () => {
      if (vnumPressRef.current.fired) vnumPressRef.current.fired = false;
    }
  }, vnumNoteHandlers(verse)), verse));

  // The verse renderers moved to 59c-library-render.jsx (LibRender). Build the
  // context bundle they need from our live state + helpers, then bind thin
  // wrappers so the call sites below read exactly as before.
  const _renderCtx = {
    selChapter,
    selBook,
    nav,
    corpus,
    nonCanon,
    didVerses,
    wordMode,
    showInterlinear,
    showStrongs,
    onWordClick,
    handleVerseNum,
    hiClass,
    vnumEl,
    noteMarker,
    noteVnum,
    noteDotInline,
    vnumNoteHandlers,
    highlightRef,
    vnumPressRef
  };
  const renderProseWords = v => LibRender.renderProseWords(_renderCtx, v);
  const renderHebVerse = v => LibRender.renderHebVerse(_renderCtx, v);
  const renderVerse = (v, sh) => LibRender.renderVerse(_renderCtx, v, sh);
  const renderKjvVerse = (v, svn, sh) => LibRender.renderKjvVerse(_renderCtx, v, svn, sh);
  const renderKjvProse = (v, svn, sh) => LibRender.renderKjvProse(_renderCtx, v, svn, sh);
  const renderBsbVerse = (v, svn, sh) => LibRender.renderBsbVerse(_renderCtx, v, svn, sh);
  const renderPlainVerse = (v, svn, sh) => LibRender.renderPlainVerse(_renderCtx, v, svn, sh);
  const renderFlowVerse = (v, inner) => LibRender.renderFlowVerse(_renderCtx, v, inner);
  const plainFlowInner = v => LibRender.plainFlowInner(_renderCtx, v);
  const kjvFlowInner = v => LibRender.kjvFlowInner(_renderCtx, v);
  const renderDidacheVerse = v => LibRender.renderDidacheVerse(_renderCtx, v);
  const renderDidacheProse = () => LibRender.renderDidacheProse(_renderCtx);
  const renderExtraLines = () => LibRender.renderExtraLines(_renderCtx);
  const renderDidacheParallelVerse = v => LibRender.renderDidacheParallelVerse(_renderCtx, v);
  return /*#__PURE__*/React.createElement("div", {
    className: "library"
  }, navVisible && /*#__PURE__*/React.createElement(LibNavPanel, {
    books: books,
    selBook: selBook,
    setSelBook: selectBook,
    selChapter: selChapter,
    setSelChapter: setSelChapter,
    navBookRef: navBookRef,
    nonCanon: nonCanon,
    nonCanonList: NONCANON,
    onPickNonCanon: pickNonCanon,
    translation: translation,
    corpus: corpus,
    pickBible: pickBible,
    esvOwner: esvOwner,
    nivOwner: nivOwner,
    hebShown: hebShown,
    hebPickable: hebPickable,
    otherOpen: otherOpen,
    setOtherOpen: setOtherOpen,
    chrono: chrono,
    orderMode: orderMode,
    setOrder: setOrder,
    chronoPos: chronoPos,
    onPickPassage: pickPassage,
    plan: planBundle
  }), !navVisible && mobileNavOpen && /*#__PURE__*/React.createElement(MobileBookPicker, {
    books: books,
    translation: translation,
    selBook: selBook,
    selChapter: selChapter,
    nonCanon: nonCanon,
    nonCanonList: NONCANON,
    chronoOn: chronoOn,
    chrono: chrono,
    chronoPos: chronoPos,
    onPickPassage: p => {
      pickPassage(p);
      setMobileNavOpen(false);
    },
    onPickPassageNoClose: p => pickPassage(p),
    plan: planBundle,
    onDone: (b, n) => {
      // Clear any lingering jump-highlight (a verse reached via Search/cross-ref) —
      // a manual book/chapter pick shouldn't leave an old verse lit. Point nav at the
      // newly picked Bible book/chapter so the jump effect sees no change and no-ops.
      if (b.id) pickNonCanon(b);else {
        selectBook(b);
        onNavChange?.({
          ...(nav || {}),
          book: b.abbrev,
          chapter: n,
          highlight: null,
          scroll: false
        });
      }
      setSelChapter(n);
      setMobileNavOpen(false);
    },
    onClose: () => setMobileNavOpen(false)
  }), !navVisible && modesOpen && /*#__PURE__*/React.createElement(ModesSheet, {
    corpus: corpus,
    translation: translation,
    pickBible: pickBible,
    esvOwner: esvOwner,
    nivOwner: nivOwner,
    hebShown: hebShown,
    hebPickable: hebPickable,
    toggleParallel: toggleParallel,
    compareAvail: compareAvail,
    compareActive: compareActive,
    toggleCompare: toggleCompare,
    nonCanonList: NONCANON,
    showStrongs: showStrongs,
    showInterlinear: showInterlinear,
    setOpt: setOpt,
    chipMode: chipMode,
    viewMode: viewMode,
    libFontSize: libFontSize,
    changeFontSize: changeFontSize,
    chrono: chrono,
    orderMode: orderMode,
    setOrder: setOrder,
    theme: theme,
    setTheme: setTheme,
    onClose: () => setModesOpen(false)
  }), /*#__PURE__*/React.createElement("div", null, navVisible ? /*#__PURE__*/React.createElement("div", {
    className: "lib-bar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lib-bar-l"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bar-ch" + (chronoOn ? " bar-ch-chrono" : "")
  }, /*#__PURE__*/React.createElement("button", {
    className: "ch-nav",
    disabled: chronoOn ? chronoPos <= 1 : selChapter <= 1,
    onClick: () => turnPage(-1),
    "aria-label": chronoOn ? "Previous passage" : "Previous chapter"
  }, "\u2039"), /*#__PURE__*/React.createElement("button", {
    className: "ch-nav",
    disabled: chronoOn ? chrono && chronoPos >= chrono.passages.length : selChapter >= maxChap,
    onClick: () => turnPage(1),
    "aria-label": chronoOn ? "Next passage" : "Next chapter"
  }, "\u203A")), chrono && !nonCanon && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "lib-bar-sep",
    "aria-hidden": "true"
  }), /*#__PURE__*/React.createElement("div", {
    className: "seg lib-order-seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (orderMode !== "chronological" ? " on" : ""),
    title: "Canonical order (books in order)",
    "aria-label": "Canonical order",
    onClick: () => setOrder("canonical")
  }, /*#__PURE__*/React.createElement(Icon.Book, null)), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (orderMode === "chronological" ? " on" : ""),
    disabled: translation === "heb",
    title: translation === "heb" ? "Chronological isn't available for the Hebrew OT" : "Chronological order (events in sequence)",
    "aria-label": "Chronological order",
    style: translation === "heb" ? {
      opacity: 0.35,
      cursor: "default"
    } : undefined,
    onClick: () => translation !== "heb" && setOrder("chronological")
  }, /*#__PURE__*/React.createElement(Icon.Clock, null)))), /*#__PURE__*/React.createElement("span", {
    className: "lib-bar-sep",
    "aria-hidden": "true"
  }), /*#__PURE__*/React.createElement("button", {
    className: "lib-toggle lib-toggle-icon" + (showStrongs ? " on" : ""),
    disabled: proseLocked,
    title: "Strong's numbers",
    "aria-label": "Strong's numbers",
    "aria-pressed": showStrongs,
    style: proseLocked ? {
      opacity: 0.35,
      cursor: "default"
    } : undefined,
    onClick: () => !proseLocked && setOpt("showStrongs", !showStrongs)
  }, /*#__PURE__*/React.createElement(Icon.Hash, null)), /*#__PURE__*/React.createElement("button", {
    className: "lib-toggle lib-toggle-icon" + (showInterlinear ? " on" : ""),
    disabled: proseLocked,
    title: "Interlinear",
    "aria-label": "Interlinear",
    "aria-pressed": showInterlinear,
    style: proseLocked ? {
      opacity: 0.35,
      cursor: "default"
    } : undefined,
    onClick: () => !proseLocked && setOpt("showInterlinear", !showInterlinear)
  }, /*#__PURE__*/React.createElement(Icon.Interlinear, null)), !nonCanon && /*#__PURE__*/React.createElement("div", {
    className: "lib-other-wrap",
    ref: compareWrapRef
  }, /*#__PURE__*/React.createElement("button", {
    className: "lib-toggle lib-toggle-icon" + (translation === "parallel" ? " on" : ""),
    title: "Compare translations",
    "aria-label": "Compare translations",
    "aria-pressed": translation === "parallel",
    "aria-expanded": compareOpen,
    onClick: () => setCompareOpen(o => !o)
  }, /*#__PURE__*/React.createElement(Icon.Columns, null)), compareOpen && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "lib-other-menu lib-compare-menu"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lib-compare-title"
  }, "Compare (pick 2\u20134)"), compareAvail.map(id => /*#__PURE__*/React.createElement("label", {
    key: id,
    className: "lib-compare-opt"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: compareActive.includes(id),
    onChange: () => toggleCompare(id)
  }), /*#__PURE__*/React.createElement("span", null, id.toUpperCase())))))), /*#__PURE__*/React.createElement("span", {
    className: "lib-bar-sep",
    "aria-hidden": "true"
  }), /*#__PURE__*/React.createElement("div", {
    className: "seg lib-view-seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (viewChipOn ? " on" : ""),
    disabled: layoutLocked,
    title: extraEnglish ? "Line-by-line view" : "Chip view",
    "aria-label": extraEnglish ? "Line-by-line view" : "Chip view",
    "aria-pressed": viewChipOn,
    style: layoutLocked ? {
      opacity: 0.35,
      cursor: "default"
    } : undefined,
    onClick: () => !layoutLocked && setOpt("viewMode", "chip")
  }, /*#__PURE__*/React.createElement(Icon.Grid, null)), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (!viewChipOn ? " on" : ""),
    disabled: hebMode || !extraEnglish && !proseLocked && (showStrongs || showInterlinear),
    title: "Prose view",
    "aria-label": "Prose view",
    "aria-pressed": !viewChipOn,
    style: hebMode || !extraEnglish && !proseLocked && (showStrongs || showInterlinear) ? {
      opacity: 0.35,
      cursor: "default"
    } : undefined,
    onClick: () => {
      if (hebMode) return;
      if (extraEnglish) {
        setOpt("viewMode", "prose");
        return;
      }
      if (!showStrongs && !showInterlinear) setOpt("viewMode", "prose");
    }
  }, /*#__PURE__*/React.createElement(Icon.Lines, null))), /*#__PURE__*/React.createElement("span", {
    className: "lib-bar-sep",
    "aria-hidden": "true"
  }), audioBtn, /*#__PURE__*/React.createElement("button", {
    className: "lib-toggle lib-toggle-icon" + (searchOpen ? " on" : ""),
    disabled: !canSearch,
    style: !canSearch ? {
      opacity: 0.35,
      cursor: "default"
    } : undefined,
    title: canSearch ? "Search this text" : "Search isn't available for this text",
    "aria-label": "Search this text",
    "aria-pressed": searchOpen,
    onClick: () => {
      if (canSearch) setSearchOpen(o => !o);
    }
  }, /*#__PURE__*/React.createElement(Icon.Search, null)), /*#__PURE__*/React.createElement("div", {
    className: "lib-other-wrap",
    ref: fontWrapRef
  }, /*#__PURE__*/React.createElement("button", {
    className: "lib-toggle lib-font-btn",
    onClick: () => setFontOpen(o => !o),
    title: "Text size",
    "aria-label": "Text size"
  }, "Aa \u25BE"), fontOpen && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "lib-other-scrim",
    onClick: () => setFontOpen(false)
  }), /*#__PURE__*/React.createElement("div", {
    className: "lib-other-menu lib-font-menu"
  }, /*#__PURE__*/React.createElement("div", {
    className: "seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b",
    onClick: () => changeFontSize(-1)
  }, "A\u2212"), /*#__PURE__*/React.createElement("span", {
    className: "font-size-lbl"
  }, libFontSize), /*#__PURE__*/React.createElement("button", {
    className: "seg-b",
    onClick: () => changeFontSize(+1)
  }, "A+")), /*#__PURE__*/React.createElement("div", {
    className: "seg lib-theme-seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (theme === "light" ? " on" : ""),
    onClick: () => setTheme("light")
  }, "Light"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (theme === "sepia" ? " on" : ""),
    onClick: () => setTheme("sepia")
  }, "Sepia"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (theme === "dark" ? " on" : ""),
    onClick: () => setTheme("dark")
  }, "Dark"))))))) : /*#__PURE__*/React.createElement("div", {
    className: "lib-toolbar"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mbar-overview",
    onClick: () => setSummaryOpen(true),
    "aria-label": chronoOn ? "Reading intro" : "Chapter overview"
  }, /*#__PURE__*/React.createElement(Icon.Info, null)), /*#__PURE__*/React.createElement("button", {
    className: "mbar-overview mbar-search",
    disabled: !canSearch,
    style: !canSearch ? {
      opacity: 0.35
    } : undefined,
    onClick: () => {
      if (canSearch) setSearchOpen(o => !o);
    },
    "aria-label": "Search this text"
  }, /*#__PURE__*/React.createElement(Icon.Search, null)), /*#__PURE__*/React.createElement("div", {
    className: "mbar-center"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mbar-loc",
    onClick: () => setMobileNavOpen(true)
  }, chronoOn ? /*#__PURE__*/React.createElement("span", {
    className: "mbar-loc-name mbar-loc-chrono"
  }, curPassage ? curPassage.label : "—") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "mbar-loc-name"
  }, nonCanon ? nonCanon.name : selBook ? selBook.name : ""), /*#__PURE__*/React.createElement("span", {
    className: "mbar-loc-ch"
  }, selChapter)))), /*#__PURE__*/React.createElement("button", {
    className: "mbar-overview mbar-audio" + (showPause ? " on" : ""),
    disabled: !audioCapable || audioBusy,
    style: !audioCapable ? {
      opacity: 0.35
    } : undefined,
    onClick: () => {
      if (audioCapable) onToolbarAudio();
    },
    "aria-label": !audioCapable ? "Audio not available for this text" : showPause ? "Pause audio" : "Play chapter audio"
  }, showPause ? /*#__PURE__*/React.createElement(Icon.Pause, null) : /*#__PURE__*/React.createElement(Icon.Play, null)), /*#__PURE__*/React.createElement("button", {
    className: "mbar-trans",
    onClick: () => setModesOpen(true),
    "aria-label": "Reading options"
  }, nonCanon ? nonCanon.abbr || nonCanon.name : translation === "parallel" ? "Par" : translation.toUpperCase())), audioBar, searchOpen && canSearch && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "lib-search-scrim",
    onClick: () => setSearchOpen(false)
  }), /*#__PURE__*/React.createElement("div", {
    className: "lib-search-panel"
  }, /*#__PURE__*/React.createElement("form", {
    className: "lib-search-row",
    onSubmit: e => {
      e.preventDefault();
      runTextSearch();
      document.activeElement?.blur?.();
    }
  }, /*#__PURE__*/React.createElement("input", {
    className: "lib-search-input",
    type: "text",
    autoFocus: true,
    enterKeyHint: "search",
    placeholder: `Search ${searchName}…`,
    value: searchQ,
    onChange: e => setSearchQ(e.target.value),
    onKeyDown: e => {
      if (e.key === "Escape") setSearchOpen(false);
    }
  }), /*#__PURE__*/React.createElement("button", {
    type: "submit",
    className: "lib-search-go",
    "aria-label": "Search"
  }, "Go"), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "lib-search-x",
    onClick: () => setSearchOpen(false),
    "aria-label": "Close search"
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    className: "lib-search-modes"
  }, /*#__PURE__*/React.createElement("div", {
    className: "seg lib-search-mode-seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (searchMode === "any" ? " on" : ""),
    onClick: () => setSearchMode("any")
  }, "Any word"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (searchMode === "all" ? " on" : ""),
    onClick: () => setSearchMode("all")
  }, "All words"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (searchMode === "phrase" ? " on" : ""),
    onClick: () => setSearchMode("phrase")
  }, "Phrase")), /*#__PURE__*/React.createElement("button", {
    className: "lib-search-opts-btn" + (searchOptsOpen ? " on" : ""),
    onClick: () => setSearchOptsOpen(o => !o)
  }, "Options ", searchOptsOpen ? "▴" : "▾")), searchOptsOpen && /*#__PURE__*/React.createElement("div", {
    className: "lib-search-opts"
  }, corpus === "bible" && /*#__PURE__*/React.createElement("div", {
    className: "lib-search-range"
  }, /*#__PURE__*/React.createElement("select", {
    className: "lib-search-sel",
    value: activeRangeId,
    onChange: e => applyRangePreset(e.target.value)
  }, SEARCH_RANGES.map(r => /*#__PURE__*/React.createElement("option", {
    key: r.id,
    value: r.id
  }, r.label)), activeRangeId === "custom" && /*#__PURE__*/React.createElement("option", {
    value: "custom"
  }, "Custom range")), /*#__PURE__*/React.createElement("div", {
    className: "lib-search-range-books"
  }, /*#__PURE__*/React.createElement("select", {
    className: "lib-search-sel",
    value: searchFrom,
    onChange: e => setSearchFrom(e.target.value)
  }, SEARCH_BOOK_LIST.map(b => /*#__PURE__*/React.createElement("option", {
    key: b,
    value: b
  }, BOOK_LABELS[b] || b))), /*#__PURE__*/React.createElement("span", {
    className: "lib-search-range-dash"
  }, "to"), /*#__PURE__*/React.createElement("select", {
    className: "lib-search-sel",
    value: searchTo,
    onChange: e => setSearchTo(e.target.value)
  }, SEARCH_BOOK_LIST.map(b => /*#__PURE__*/React.createElement("option", {
    key: b,
    value: b
  }, BOOK_LABELS[b] || b))))), /*#__PURE__*/React.createElement("label", {
    className: "lib-search-check"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: !searchPartial,
    onChange: e => setSearchPartial(!e.target.checked)
  }), " Whole words only"), /*#__PURE__*/React.createElement("label", {
    className: "lib-search-check"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: searchCase,
    onChange: e => setSearchCase(e.target.checked)
  }), " Case-sensitive"), /*#__PURE__*/React.createElement("form", {
    style: {
      display: "contents"
    },
    onSubmit: e => {
      e.preventDefault();
      runTextSearch();
      document.activeElement?.blur?.();
    }
  }, /*#__PURE__*/React.createElement("input", {
    className: "lib-search-input lib-search-excl-input",
    type: "text",
    enterKeyHint: "search",
    placeholder: "Exclude verses with\u2026",
    value: searchExclude,
    onChange: e => setSearchExclude(e.target.value),
    onBlur: () => {
      if (didSearchRef.current && searchQ.trim()) runTextSearch();
    }
  }))), /*#__PURE__*/React.createElement("div", {
    className: "lib-search-results"
  }, searchLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-search-status"
  }, "Searching\u2026") : searchResults == null ? null : searchResults.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "lib-search-status"
  }, "No matches.") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "lib-search-status"
  }, searchCounts ? `${searchCounts.verses}${searchCounts.capped ? "+" : ""} verse${searchCounts.verses === 1 ? "" : "s"} found, ${searchCounts.matches}${searchCounts.capped ? "+" : ""} match${searchCounts.matches === 1 ? "" : "es"}` : `${searchResults.length} results`), searchResults.map((r, i) => /*#__PURE__*/React.createElement("button", {
    key: i,
    className: "lib-search-hit",
    onClick: () => jumpToResult(r)
  }, /*#__PURE__*/React.createElement("span", {
    className: "lib-search-hit-ref"
  }, corpus === "bible" ? BOOK_LABELS[r.book] || r.book : searchName, " ", r.chapter, ":", r.verse), /*#__PURE__*/React.createElement("span", {
    className: "lib-search-hit-text"
  }, searchHi ? highlightTerms(r.text, searchHi.terms, searchHi.partial, searchHi.caseSensitive) : r.text))))))), /*#__PURE__*/React.createElement("div", _extends({
    ref: readingRef,
    className: "lib-reading" + (showInterlinear ? " lib-interlinear-on" : "") + (audioDockOn ? " lib-reading--audio" : ""),
    style: {
      ...(translation === "parallel" ? {
        paddingTop: 0
      } : {}),
      "--lib-font-size": libFontSize + "px"
    }
  }, readingHandlers), nonCanon ? didLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-loading"
  }, "Loading\u2026") : nonCanon.englishOnly ? extraLineMode ? renderExtraLines() : renderDidacheProse() : translation === "parallel" ? /*#__PURE__*/React.createElement("div", {
    className: "lib-parallel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lib-parallel-header"
  }, /*#__PURE__*/React.createElement("span", {
    className: "lib-parallel-label"
  }, nonCanon.name, " \xB7 Greek"), /*#__PURE__*/React.createElement("span", {
    className: "lib-parallel-label"
  }, "English")), didVerses.map(renderDidacheParallelVerse)) : chipMode ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words lib-did-text"
  }, didVerses.map(renderDidacheVerse)) : renderDidacheProse() : translation === "parallel" ? (() => {
    // Compare: render the selected texts (2-4) side by side. Each column
    // knows how to draw its own verse + its own number (shown on desktop,
    // hidden on mobile where the shared number sits above the stack).
    // Plain English columns (BSB/ESV/NIV) carry their own verse number too
    // (the shared one is mobile-only), so every desktop column shows it.
    // They also get the note anchor + highlight paint + note marker so notes
    // and highlights are SHARED across the compare columns: a highlight made
    // in any text paints the whole verse here, the pencil shows, and you can
    // drag-select inside the column to add a new one.
    const plainCol = v => {
      const pch = v._ch ?? selChapter;
      return /*#__PURE__*/React.createElement("span", {
        className: "lib-parallel-plain",
        "data-note-verse": v.verse,
        "data-note-chapter": pch
      }, vnumEl(v.verse, pch), noteDotInline(v.verse, pch), /*#__PURE__*/React.createElement("span", {
        className: "lib-bsb-text" + hiClass(v.verse, null, pch)
      }, v.verse_text));
    };
    const colDefs = {
      abp: {
        label: "ABP",
        view: abpView,
        loading: abpShowLoading,
        render: v => renderVerse(v, true)
      },
      kjv: {
        label: "KJV",
        view: kjvView,
        loading: kjvShowLoading,
        render: v => kjvWordMode ? renderKjvVerse(v, true, true) : renderKjvProse(v, true, true)
      },
      bsb: {
        label: "BSB",
        view: bsbView,
        loading: bsbShowLoading,
        render: v => bsbWordMode ? renderBsbVerse(v, true, true) : plainCol(v)
      },
      esv: {
        label: "ESV",
        view: esvView,
        loading: esvShowLoading,
        render: plainCol
      },
      niv: {
        label: "NIV",
        view: nivView,
        loading: nivShowLoading,
        render: plainCol
      }
    };
    const cols = compareSel.filter(id => colDefs[id] && compareAvail.includes(id)).map(id => ({
      id,
      ...colDefs[id]
    }));
    const n = Math.max(cols.length, 1);
    return /*#__PURE__*/React.createElement("div", {
      className: "lib-parallel lib-cmp-" + n
    }, /*#__PURE__*/React.createElement("div", {
      className: "lib-parallel-header"
    }, cols.map(c => /*#__PURE__*/React.createElement("span", {
      key: c.id,
      className: "lib-parallel-label"
    }, c.label))), cols.some(c => c.loading) ? /*#__PURE__*/React.createElement("div", {
      className: "lib-loading"
    }, "Loading\u2026") : (() => {
      // Key by chapter+verse so a chronological span (verse numbers repeat
      // across chapters) lines the texts up; canonical has one chapter.
      const cv = v => `${v._ch ?? selChapter}-${v.verse}`;
      const maps = {};
      cols.forEach(c => {
        maps[c.id] = Object.fromEntries(c.view.map(v => [cv(v), v]));
      });
      // Ordered union of every verse present in any selected text.
      const seen = new Set();
      const order = [];
      cols.forEach(c => c.view.forEach(v => {
        const k = cv(v);
        if (!seen.has(k)) {
          seen.add(k);
          order.push({
            k,
            ch: v._ch ?? selChapter,
            verse: v.verse
          });
        }
      }));
      order.sort((a, b) => a.ch - b.ch || a.verse - b.verse);
      const items = [];
      let lastCh = null;
      order.forEach(o => {
        if (chronoOn && o.ch !== lastCh) {
          items.push({
            type: 'chap',
            ch: o.ch
          });
          lastCh = o.ch;
        }
        let heading = null;
        for (const c of cols) {
          const vv = maps[c.id][o.k];
          if (vv && vv.heading) {
            heading = vv.heading;
            break;
          }
        }
        if (heading) items.push({
          type: 'heading',
          heading,
          key: `h-${o.k}`
        });
        items.push({
          type: 'verse',
          o
        });
      });
      return items.map(item => {
        if (item.type === 'chap') return /*#__PURE__*/React.createElement("div", {
          key: `cm-${item.ch}`,
          className: "lib-chrono-chapmark"
        }, selBook ? selBook.name : "", " ", item.ch);
        if (item.type === 'heading') return /*#__PURE__*/React.createElement("div", {
          key: item.key,
          className: "lib-parallel-section-heading"
        }, /*#__PURE__*/React.createElement("div", {
          className: "pericope-heading"
        }, item.heading));
        const o = item.o;
        return /*#__PURE__*/React.createElement("div", {
          key: o.k,
          className: "lib-parallel-verse"
        }, /*#__PURE__*/React.createElement("div", {
          className: "lib-parallel-vnum"
        }, vnumEl(o.verse, o.ch)), cols.map(c => {
          const vv = maps[c.id][o.k];
          return /*#__PURE__*/React.createElement("div", {
            key: c.id,
            className: "lib-parallel-col"
          }, /*#__PURE__*/React.createElement("span", {
            className: "lib-parallel-col-lbl"
          }, c.label), vv ? c.render(vv) : null);
        }));
      });
    })());
  })() : translation === "kjv" ? kjvShowLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-loading"
  }, "Loading\u2026") : kjvWordMode ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words"
  }, withMarks(kjvView, v => renderKjvVerse(v))) : isPoetry ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words"
  }, withMarks(kjvView, v => renderKjvProse(v))) : /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words lib-prose-flow"
  }, withMarks(kjvView, v => renderFlowVerse(v, kjvFlowInner(v)))) : translation === "bsb" ? bsbShowLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-loading"
  }, "Loading\u2026") : bsbWordMode ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words"
  }, withMarks(bsbView, v => renderBsbVerse(v))) : isPoetry ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words"
  }, withMarks(bsbView, v => renderPlainVerse(v))) : /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words lib-prose-flow"
  }, withMarks(bsbView, v => renderFlowVerse(v, plainFlowInner(v)))) : translation === "esv" ? esvShowLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-loading"
  }, "Loading\u2026") : isPoetry ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words"
  }, withMarks(esvView, v => renderPlainVerse(v))) : /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words lib-prose-flow"
  }, withMarks(esvView, v => renderFlowVerse(v, plainFlowInner(v)))) : translation === "niv" ? nivShowLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-loading"
  }, "Loading\u2026") : isPoetry ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words"
  }, withMarks(nivView, v => renderPlainVerse(v))) : /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words lib-prose-flow"
  }, withMarks(nivView, v => renderFlowVerse(v, plainFlowInner(v)))) : translation === "heb" ? hebLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-loading"
  }, "Loading\u2026") : /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words lib-heb-text"
  }, hebVerses.map(renderHebVerse)) : abpShowLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lib-loading"
  }, "Loading\u2026") : wordMode ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words"
  }, withMarks(abpView, v => renderVerse(v))) : isPoetry ? /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words"
  }, withMarks(abpView, v => renderVerse(v))) : /*#__PURE__*/React.createElement("div", {
    className: "lib-text-words lib-prose-flow"
  }, withMarks(abpView, v => {
    const ch = v._ch ?? selChapter;
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: `${ch}-${v.verse}`
    }, v.heading && /*#__PURE__*/React.createElement("div", {
      className: "pericope-heading"
    }, v.heading), /*#__PURE__*/React.createElement("span", {
      className: "lib-flow-verse",
      "data-note-verse": v.verse,
      "data-note-chapter": ch
    }, /*#__PURE__*/React.createElement("sup", _extends({
      className: "lib-flow-vnum",
      title: handleVerseNum ? "Click: cross-references · Right-click / long-press: add a note" : undefined,
      onClick: handleVerseNum ? () => {
        if (vnumPressRef.current.fired) {
          vnumPressRef.current.fired = false;
          return;
        }
        handleVerseNum(v.verse, ch);
      } : undefined
    }, vnumNoteHandlers(v.verse, ch)), v.verse), noteDotInline(v.verse, ch), renderProseWords(v)));
  })))), focusMode && !isMobile && (() => {
    const canPrev = chronoOn ? chronoPos > 1 : selChapter > 1;
    const canNext = chronoOn ? chrono && chronoPos < chrono.passages.length : selChapter < maxChap;
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
      className: "lib-focus-arrow lib-focus-arrow-prev" + (audioDockOn ? " lib-focus-arrow--audio" : ""),
      "aria-label": "Previous",
      disabled: !canPrev,
      onClick: () => turnPage(-1)
    }, "\u2039"), /*#__PURE__*/React.createElement("button", {
      className: "lib-focus-arrow lib-focus-arrow-next" + (audioDockOn ? " lib-focus-arrow--audio" : ""),
      "aria-label": "Next",
      disabled: !canNext,
      onClick: () => turnPage(1)
    }, "\u203A"));
  })(), noteSel && /*#__PURE__*/React.createElement(NoteAddPopover, {
    rect: noteSel.rect,
    isMobile: isMobile,
    onAdd: addNoteFromSelection,
    onColor: addHighlightFromSelection,
    onCopy: copySelection,
    onJournal: journalFromSelection
  }), flashMsg && /*#__PURE__*/React.createElement("div", {
    className: "lib-flash"
  }, flashMsg), verseMenu && /*#__PURE__*/React.createElement(VerseNoteMenu, {
    rect: verseMenu.rect,
    isMobile: isMobile,
    onColor: vmColor,
    onNote: vmNote,
    onBookmark: vmBookmark,
    onCopy: vmCopy,
    onJournal: vmJournal,
    onClose: () => setVerseMenu(null)
  }), showSummary && chronoOn && currentDay ? chronoPanel === "overview" ? /*#__PURE__*/React.createElement(SummaryPanel, {
    book: sumBook,
    chapter: sumChapter,
    bookLabel: sumLabel,
    onBack: () => setChronoPanel("intro")
  }) : /*#__PURE__*/React.createElement(DayIntroPanel, {
    day: currentDay,
    chrono: chrono,
    onPickPassage: pickPassage,
    onOverview: () => setChronoPanel("overview")
  }) : showSummary && (selBook || nonCanon) ? /*#__PURE__*/React.createElement(SummaryPanel, {
    book: sumBook,
    chapter: sumChapter,
    bookLabel: sumLabel
  }) : null, isMobile && summaryOpen && chronoOn && currentDay ? chronoPanel === "overview" ? /*#__PURE__*/React.createElement(SummaryPanel, {
    isMobile: true,
    book: sumBook,
    chapter: sumChapter,
    bookLabel: sumLabel,
    onClose: () => setSummaryOpen(false),
    onBack: () => setChronoPanel("intro")
  }) : /*#__PURE__*/React.createElement(DayIntroPanel, {
    isMobile: true,
    day: currentDay,
    chrono: chrono,
    onClose: () => setSummaryOpen(false),
    onPickPassage: p => {
      pickPassage(p);
      setSummaryOpen(false);
    },
    onOverview: () => setChronoPanel("overview")
  }) : isMobile && summaryOpen && (selBook || nonCanon) ? /*#__PURE__*/React.createElement(SummaryPanel, {
    isMobile: true,
    onClose: () => setSummaryOpen(false),
    book: sumBook,
    chapter: sumChapter,
    bookLabel: sumLabel
  }) : null);
}

// ============================================================
// GLOSS GROUPINGS
// ============================================================
// ============================================================
// AI ANSWER STRIP
// ============================================================
function AIAnswer({
  query,
  explanation,
  keyStrongs,
  onPick
}) {
  return /*#__PURE__*/React.createElement("section", {
    className: "ai-answer"
  }, /*#__PURE__*/React.createElement("div", {
    className: "ai-answer-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "ai-tag"
  }, /*#__PURE__*/React.createElement("span", {
    className: "ai-dot"
  }), "Synthesis"), /*#__PURE__*/React.createElement("span", {
    className: "ai-q"
  }, "\"", query, "\"")), /*#__PURE__*/React.createElement("p", {
    className: "ai-answer-body"
  }, explanation), keyStrongs && keyStrongs.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "ai-cites"
  }, /*#__PURE__*/React.createElement("span", {
    className: "ai-cites-label"
  }, "Cited:"), keyStrongs.map(ks => /*#__PURE__*/React.createElement("button", {
    key: ks.strongs,
    className: "ai-cite",
    onClick: () => onPick({
      id: `ks-${ks.strongs_base}`,
      strongs: ks.strongs,
      strongs_base: ks.strongs_base,
      strongs_raw: ks.strongs_base,
      greek: ks.lemma,
      translit: ks.translit,
      gloss: "",
      ref: "",
      book: "",
      chapter: 0,
      verse: 0,
      definition: ks.definition || "",
      derivation: ks.derivation || ""
    })
  }, ks.strongs, " ", ks.translit || ks.lemma))));
}

// ============================================================
// GUIDED TOUR
// ============================================================
const TOUR_STEPS = [{
  icon: "Book",
  label: "Welcome to Lexica",
  body: "Lexica is a Greek and Hebrew word study tool built for the diligent Berean. No prior training required. Every word traces back to its Greek or Hebrew source so you can read what the text actually says — before any theological framework is applied. You won't be a scholar overnight, but you'll immediately be a Berean."
}, {
  icon: "Search",
  label: "The Lexicon",
  body: "Search by English, Greek, Hebrew, transliteration, or Strong's number. Results span both Greek (LSJ) and Hebrew (BDB) — click any word for its full lexicon entry and a context-aware AI summary anchored in the source text."
}, {
  icon: "Book",
  label: "The Library",
  body: "Read in ABP Greek, KJV, or the Berean Standard Bible — on their own, in parallel, or compare them side by side. Switch between plain reading and a full interlinear (Hebrew over OT words, Greek over NT), follow the text in chronological order, or listen with read-along audio. Click any word for its lexicon entry; click any verse number for cross-references. Beyond the canon you'll also find the Apocrypha, 1 Enoch, and the Apostolic Fathers."
}, {
  icon: "Panel",
  label: "Cross-References",
  body: "Every verse connects to Torrey's Treasury of Scripture Knowledge — AI-curated to the strongest matches and synthesized into a thematic overview anchored in ABP vocabulary."
}, {
  icon: "Sparkle",
  label: "Ask the Corpus",
  body: "Ask in plain language: 'Where does pneuma appear in Genesis?' or 'Differences in how KJV and ABP render spirit in the OT.' The AI searches Greek and Hebrew simultaneously and cites specific passages."
}, {
  icon: "Note",
  label: "Notes & Highlights",
  body: "Highlight verses in five colors, write notes on any word or verse, drop bookmarks, and keep a free-form journal. It all saves in your browser automatically — no account required. Sign in with email or Google to sync everything across your devices."
}, {
  icon: "Book",
  label: "Support Lexica",
  body: "Lexica is free, independent, and has no ads. It's maintained by one person who thinks serious Bible study tools shouldn't cost hundreds of dollars. If it's been useful to your studies, a small contribution keeps it running.",
  donate: true
}];
function GuidedTour({
  onDone
}) {
  const [step, setStep] = useState(0);
  const cur = TOUR_STEPS[step];
  const StepIcon = Icon[cur.icon];
  const isLast = step === TOUR_STEPS.length - 1;
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "tour-scrim",
    onClick: onDone
  }), /*#__PURE__*/React.createElement("div", {
    className: "tour-modal",
    role: "dialog",
    "aria-modal": "true",
    "aria-label": "Welcome to Lexica"
  }, /*#__PURE__*/React.createElement("button", {
    className: "tour-skip",
    onClick: onDone
  }, "Skip"), /*#__PURE__*/React.createElement("div", {
    className: "tour-icon-wrap"
  }, /*#__PURE__*/React.createElement(StepIcon, {
    width: "20",
    height: "20"
  })), /*#__PURE__*/React.createElement("div", {
    className: "tour-step-num"
  }, step + 1, " of ", TOUR_STEPS.length), /*#__PURE__*/React.createElement("h2", {
    className: "tour-title"
  }, cur.label), /*#__PURE__*/React.createElement("p", {
    className: "tour-body"
  }, cur.body), cur.donate && /*#__PURE__*/React.createElement("div", {
    className: "tour-donate-btns"
  }, /*#__PURE__*/React.createElement("a", {
    className: "donate-btn kofi",
    href: "https://ko-fi.com/lexica",
    target: "_blank",
    rel: "noopener noreferrer"
  }, "\u2615 Ko-fi"), /*#__PURE__*/React.createElement("a", {
    className: "donate-btn github",
    href: "https://github.com/sponsors/jonathan-pernice",
    target: "_blank",
    rel: "noopener noreferrer"
  }, "\u2665 GitHub Sponsors")), /*#__PURE__*/React.createElement("div", {
    className: "tour-dots"
  }, TOUR_STEPS.map((_, i) => /*#__PURE__*/React.createElement("button", {
    key: i,
    className: "tour-dot" + (i === step ? " active" : ""),
    onClick: () => setStep(i),
    "aria-label": `Step ${i + 1}`
  }))), /*#__PURE__*/React.createElement("div", {
    className: "tour-nav"
  }, step > 0 && /*#__PURE__*/React.createElement("button", {
    className: "tour-btn tour-btn-prev",
    onClick: () => setStep(s => s - 1)
  }, "Previous"), isLast ? /*#__PURE__*/React.createElement("button", {
    className: "tour-btn tour-btn-done",
    onClick: onDone
  }, "Get started") : /*#__PURE__*/React.createElement("button", {
    className: "tour-btn tour-btn-next",
    onClick: () => setStep(s => s + 1)
  }, "Next"))));
}

// ============================================================
// ABOUT VIEW
// ============================================================
function AboutView({
  owner
}) {
  // The owner gets a private "Stats" view tucked behind a toggle here (no extra tab).
  const [tab, setTab] = useState("about");
  return /*#__PURE__*/React.createElement("div", {
    className: "about-view"
  }, /*#__PURE__*/React.createElement("div", {
    className: "about-inner"
  }, owner && /*#__PURE__*/React.createElement("div", {
    className: "seg about-owner-seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (tab === "about" ? " on" : ""),
    onClick: () => setTab("about")
  }, "About"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (tab === "stats" ? " on" : ""),
    onClick: () => setTab("stats")
  }, "Stats"), /*#__PURE__*/React.createElement("button", {
    className: "seg-b" + (tab === "admin" ? " on" : ""),
    onClick: () => setTab("admin")
  }, "Admin")), owner && tab === "stats" ? /*#__PURE__*/React.createElement(StatsView, null) : owner && tab === "admin" ? /*#__PURE__*/React.createElement(AdminView, null) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("h1", {
    className: "about-title"
  }, "About Lexica"), /*#__PURE__*/React.createElement("p", {
    className: "about-lead"
  }, "A Greek and Hebrew word study tool for the diligent Berean. No seminary required."), /*#__PURE__*/React.createElement("h2", {
    className: "about-h2"
  }, "What Lexica does"), /*#__PURE__*/React.createElement("p", {
    className: "about-p"
  }, "Lexica lets you trace any English word in the Bible back to its Greek or Hebrew source and explore its full meaning \u2014 not just the translation choice made by one committee. Every word links to the Liddell-Scott-Jones Greek lexicon (LSJ) or Brown-Driver-Briggs Hebrew lexicon (BDB), the two most comprehensive scholarly references available."), /*#__PURE__*/React.createElement("p", {
    className: "about-p"
  }, "The primary text is the ", /*#__PURE__*/React.createElement("b", null, "Apostolic Bible Polyglot (ABP)"), " \u2014 a word-for-word Greek interlinear covering both the Septuagint (OT) and New Testament. The ", /*#__PURE__*/React.createElement("b", null, "King James Version"), " and the ", /*#__PURE__*/React.createElement("b", null, "Berean Standard Bible"), " read alongside it \u2014 on their own, in parallel, or compared side by side \u2014 with read-along audio and an optional chronological reading order. Cross-references come from Torrey's Treasury of Scripture Knowledge."), /*#__PURE__*/React.createElement("p", {
    className: "about-p"
  }, "Beyond the canon, Lexica includes a library of related texts: the Septuagint Apocrypha, the Pseudepigrapha (1 Enoch, Jubilees, and more), and the Apostolic Fathers with full Greek interlinear."), /*#__PURE__*/React.createElement("h2", {
    className: "about-h2"
  }, "Your study, saved"), /*#__PURE__*/React.createElement("p", {
    className: "about-p"
  }, "Highlight verses, write notes on any word or verse, set bookmarks, and keep a free-form journal. Everything saves in your browser automatically \u2014 no account needed. Create a free account (email or Google) and your notes sync across every device. The app stays fully usable with no sign-in at all."), /*#__PURE__*/React.createElement("h2", {
    className: "about-h2"
  }, "The Berean approach"), /*#__PURE__*/React.createElement("p", {
    className: "about-p"
  }, "The Bereans \"received the word with all readiness of mind, and searched the scriptures daily\" (Acts 17:11). Lexica is built on that same posture: let the Greek and Hebrew speak first, before any theological system is imported. No commentary, no denominational lens, no conclusions pre-loaded. The text speaks \u2014 you decide what it means."), /*#__PURE__*/React.createElement("p", {
    className: "about-p"
  }, "Every AI-generated summary is anchored in the source vocabulary of the ABP. The system prompt explicitly forbids importing theology from outside the text."), /*#__PURE__*/React.createElement("h2", {
    className: "about-h2"
  }, "Methodology"), /*#__PURE__*/React.createElement("ul", {
    className: "about-ul"
  }, /*#__PURE__*/React.createElement("li", null, "Strong's numbers are the bridge between English, Greek, and Hebrew"), /*#__PURE__*/React.createElement("li", null, "Greek definitions draw from LSJ \u2014 the standard classical Greek reference"), /*#__PURE__*/React.createElement("li", null, "Hebrew definitions draw from BDB \u2014 the standard OT Hebrew reference"), /*#__PURE__*/React.createElement("li", null, "AI search generates SQL against the full lexicon corpus \u2014 not a summary or paraphrase"), /*#__PURE__*/React.createElement("li", null, "Translation comparisons surface where ABP, KJV, and the BSB make different rendering choices for the same source word")), /*#__PURE__*/React.createElement("h2", {
    className: "about-h2"
  }, "Support Lexica"), /*#__PURE__*/React.createElement("p", {
    className: "about-p"
  }, "Lexica is free, independent, and has no ads. It's maintained by one person who thinks serious Bible study tools shouldn't cost hundreds of dollars or require a seminary login. If it's been useful to you, a small contribution keeps the lights on."), /*#__PURE__*/React.createElement("div", {
    className: "about-donate"
  }, /*#__PURE__*/React.createElement("a", {
    className: "donate-btn kofi",
    href: "https://ko-fi.com/lexica",
    target: "_blank",
    rel: "noopener noreferrer"
  }, "\u2615 Ko-fi"), /*#__PURE__*/React.createElement("a", {
    className: "donate-btn github",
    href: "https://github.com/sponsors/jonathan-pernice",
    target: "_blank",
    rel: "noopener noreferrer"
  }, "\u2665 GitHub Sponsors")))));
}

// ============================================================
// LEXICON VIEW
// ============================================================
const _STRONGS_RE = /^[GgHh]?\d+(\.\d+)?$/;

// Which original languages live in a (corpus, testament) slice of the English
// search results. ABP is Greek throughout (the Septuagint in the OT, Greek NT);
// KJV's OT is Hebrew and its NT is Greek. Lets the Greek/Hebrew filter gray out
// combos that can't return anything (ABP has no Hebrew; KJV's OT has no Greek)
// while still allowing Greek in the OT via the Septuagint.
function _sliceHasGreek(corpus, testament) {
  if (corpus === "kjv") return testament !== "ot"; // KJV: Greek only in the NT
  return true; // ABP / All: always some Greek
}
function _sliceHasHebrew(corpus, testament) {
  if (corpus === "abp") return false; // ABP is all Greek
  return testament !== "nt"; // KJV / All: Hebrew only outside the NT
}
function _comboOK(corpus, testament, language) {
  if (language === "greek") return _sliceHasGreek(corpus, testament);
  if (language === "hebrew") return _sliceHasHebrew(corpus, testament);
  return true;
}
function LexiconView({
  onNavigateToSearch,
  onNavigateToLibrary,
  onWordClick,
  pendingStrongs,
  onPendingStrongsConsumed,
  isMobile
}) {
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState(null);
  const [profile, setProfile] = useState(null);
  const [corpus, setCorpus] = useState("all"); // search-results scope: all | abp | kjv
  const [profileCorpus, setProfileCorpus] = useState("abp"); // drilled-in word view: abp | kjv (never "all")
  const [language, setLanguage] = useState("all"); // results filter: all | greek | hebrew
  const [testament, setTestament] = useState("all");
  const [selectedBook, setSelectedBook] = useState(null);
  const [verseList, setVerseList] = useState(null);
  const [verseLoading, setVerseLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedGloss, setSelectedGloss] = useState(null);
  const [bookGlosses, setBookGlosses] = useState(null);
  const [filteredBooks, setFilteredBooks] = useState(null);
  const [groupings, setGroupings] = useState(null);
  const [pendingGloss, setPendingGloss] = useState(null);
  const [showDef, setShowDef] = useState(false);
  const [lsjEntry, setLsjEntry] = useState(null);
  const [lsjSummary, setLsjSummary] = useState(null);
  const [lsjLoading, setLsjLoading] = useState(false);
  const [lsjSummaryLoading, setLsjSummaryLoading] = useState(false);

  // Reset the curated LSJ definition whenever the focused word changes.
  useEffect(() => {
    setLsjEntry(null);
    setLsjSummary(null);
  }, [profile?.strongs]);

  // Lazily fetch the LSJ entry + AI-curated summary when the Greek definition is
  // opened (Haiku, cached). Hebrew keeps its BDB definition. The /api/lsj endpoint
  // auto-falls back to strongs_def when there's no LSJ match.
  useEffect(() => {
    if (!showDef || !profile || !/^G/i.test(profile.strongs) || lsjEntry || lsjLoading) return;
    let cancelled = false;
    setLsjLoading(true);
    api.lsj(profile.lemma || "", profile.strongs.replace(/^[GH]/i, "")).then(d => {
      if (cancelled) return;
      const entry = d && !d.error ? d : null;
      setLsjEntry(entry);
      setLsjLoading(false);
      if (entry && entry.source !== "strongs") {
        setLsjSummaryLoading(true);
        api.lsjSummary(entry.key).then(s => {
          if (!cancelled) setLsjSummary(s);
        }).catch(() => {}).finally(() => {
          if (!cancelled) setLsjSummaryLoading(false);
        });
      }
    }).catch(() => {
      if (!cancelled) {
        setLsjEntry(null);
        setLsjLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [showDef, profile?.strongs]);
  useEffect(() => {
    if (!pendingStrongs) return;
    onPendingStrongsConsumed?.();
    setGroupings(null);
    setMatches(null);
    // pendingStrongs may be a bare Strong's or { strongs, corpus } (from an
    // ABP/KJV "occurrences" link) — drill in to the corpus the link named.
    const s = typeof pendingStrongs === "string" ? pendingStrongs : pendingStrongs.strongs;
    const c = typeof pendingStrongs === "string" ? undefined : pendingStrongs.corpus;
    loadProfile(s, c);
  }, [pendingStrongs]);
  const loadProfile = async (strongs, corpusOverride) => {
    setLoading(true);
    setError(null);
    // NOTE: keep `matches`/`groupings` alive so the profile's back button can
    // return to whichever result list we drilled in from. handleSubmit clears
    // both before every new search, so a stale list can't linger.
    setSelectedBook(null);
    setSelectedGloss(null);
    setBookGlosses(null);
    setFilteredBooks(null);
    setShowDef(false);
    const isHeb = /^H/i.test(strongs) || !/^[GgHh]/.test(strongs) && parseInt(strongs) > 5624;
    const c = corpusOverride ?? (isHeb ? "kjv" : "abp"); // drilling in always lands in a single corpus
    setProfileCorpus(c);
    try {
      const data = await api.lexiconProfile(strongs, c);
      if (data.error) setError(data.error);else setProfile(data);
    } catch (e) {
      setError("Failed to load word profile: " + e);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    if (profile && pendingGloss) {
      selectGloss(pendingGloss);
      setPendingGloss(null);
    }
  }, [profile, pendingGloss]);

  // Search-results scope toggle (All / ABP / KJV). Only shown when no word is
  // in focus; re-runs the English search in that corpus.
  const switchCorpus = async c => {
    if (loading || c === corpus) return;
    if (c !== "all" && !_comboOK(c, testament, language)) return; // grayed combo
    setCorpus(c);
    const q = query.trim();
    const isEnglishQuery = !!q && !_STRONGS_RE.test(q) && !_isGreekHebrew(q);
    if (groupings && isEnglishQuery) {
      setLoading(true);
      try {
        const data = await api.lexiconEnglish(q, c, testament);
        setGroupings(data.length ? data : null);
        setError(data.length ? null : "No matches found.");
      } catch {
        setError("Search failed.");
      } finally {
        setLoading(false);
      }
    }
  };

  // Profile corpus toggle (ABP / KJV). Reloads the focused word in that corpus.
  const switchProfileCorpus = async c => {
    if (loading || c === profileCorpus || !profile) return;
    setProfileCorpus(c);
    setLoading(true);
    setSelectedBook(null);
    setVerseList(null);
    setTestament("all");
    setSelectedGloss(null);
    setBookGlosses(null);
    setFilteredBooks(null);
    setShowDef(false);
    try {
      const data = await api.lexiconProfile(profile.strongs, c);
      if (!data.error) setProfile(data);
    } catch {} finally {
      setLoading(false);
    }
  };
  const switchTestament = async t => {
    if (loading) return;
    if (!profile && t !== "all" && !_comboOK(corpus, t, language)) return; // grayed combo (results view only)
    setTestament(t);
    setSelectedBook(null);
    setVerseList(null);
    // Profile view filters its distribution + count on `testament` client-side.
    if (profile) return;
    // Results view: re-run the English search scoped to the testament.
    const q = query.trim();
    if (groupings && q && !_STRONGS_RE.test(q) && !_isGreekHebrew(q)) {
      setLoading(true);
      try {
        const data = await api.lexiconEnglish(q, corpus, t);
        setGroupings(data.length ? data : null);
        setError(data.length ? null : "No matches found.");
      } catch {
        setError("Search failed.");
      } finally {
        setLoading(false);
      }
    }
  };

  // Greek/Hebrew filter for the results grid — a pure client-side row filter, no
  // refetch. Graying (via _comboOK) keeps it from clashing with corpus/testament.
  const switchLanguage = l => {
    if (l === language || !_comboOK(corpus, testament, l)) return;
    setLanguage(l);
  };
  const fetchVerses = async (book, gloss) => {
    setVerseList(null);
    setVerseLoading(true);
    try {
      const data = await api.lexiconVerses(profile.strongs, book, profileCorpus, gloss);
      if (data.error) {
        setVerseList([{
          error: data.error
        }]);
      } else {
        setVerseList(data.verses || []);
        setBookGlosses(data.glosses && data.glosses.length ? data.glosses : null);
      }
    } catch (e) {
      setVerseList([{
        error: String(e)
      }]);
    } finally {
      setVerseLoading(false);
    }
  };
  const selectBook = async book => {
    if (selectedBook === book) {
      setSelectedBook(null);
      setVerseList(null);
      setBookGlosses(null);
      return;
    }
    setSelectedBook(book);
    await fetchVerses(book, selectedGloss);
  };
  const selectGloss = async gloss => {
    const next = selectedGloss === gloss ? null : gloss;
    setSelectedGloss(next);
    if (next) {
      const data = await api.lexiconBooks(profile.strongs, profileCorpus, next);
      setFilteredBooks(data.books && data.books.length ? data.books : null);
    } else {
      setFilteredBooks(null);
    }
    if (selectedBook) await fetchVerses(selectedBook, next);
  };
  const _isGreekHebrew = s => /[Ͱ-Ͽἀ-῿֐-׿]/.test(s);

  // One "<Bible> renders this as" line. The active toggle's line is the
  // interactive one (click a rendering to filter the books/verses below); the
  // other Bible's line is shown read-only, just so you can see both at once.
  const renderGlossLine = (lineCorpus, label, list) => {
    if (!list || !list.length) return null;
    const interactive = profileCorpus === lineCorpus;
    return /*#__PURE__*/React.createElement("div", {
      className: "lexicon-glosses"
    }, /*#__PURE__*/React.createElement("div", {
      className: "lexicon-gloss-label"
    }, label), /*#__PURE__*/React.createElement("div", {
      className: "lexicon-dist-list"
    }, list.map((g, i) => /*#__PURE__*/React.createElement(React.Fragment, {
      key: g.gloss
    }, i > 0 && /*#__PURE__*/React.createElement("span", {
      className: "lexicon-dist-sep"
    }, " \xB7 "), interactive ? /*#__PURE__*/React.createElement("button", {
      className: "lexicon-dist-item" + (selectedGloss === g.gloss ? " selected" : ""),
      onClick: () => selectGloss(g.gloss)
    }, g.gloss, /*#__PURE__*/React.createElement("span", {
      className: "lexicon-dist-count"
    }, g.count)) : /*#__PURE__*/React.createElement("span", {
      className: "lexicon-dist-item lexicon-dist-item--ref"
    }, g.gloss, /*#__PURE__*/React.createElement("span", {
      className: "lexicon-dist-count"
    }, g.count))))));
  };

  // A result row's rendering preview: an ABP line and/or a KJV line, each
  // labeled with its ABP/KJV tag (so a single-Bible word still says which one).
  // Desktop caps each line at 6 renderings; mobile shows all (wraps).
  const renderRowPreview = g => {
    const line = (list, tag) => !list || list.length === 0 ? null : /*#__PURE__*/React.createElement("span", {
      className: "lex-prev-line",
      key: tag
    }, /*#__PURE__*/React.createElement("span", {
      className: "lex-prev-tag"
    }, tag), (isMobile ? list : list.slice(0, 6)).map(x => x.gloss).join(", "));
    return [line(g.abp_glosses, "ABP"), line(g.kjv_glosses, "KJV")];
  };

  // Light up every form of the focused word's Strong's in the verse list.
  const citedStrongs = useMemo(() => {
    if (!profile?.strongs) return new Set();
    const tag = profile.strongs;
    const base = tag.split(".")[0];
    return new Set([tag, base, base.replace(/^[GH]/i, "")]);
  }, [profile?.strongs]);
  const handleSubmit = async e => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setProfile(null);
    setMatches(null);
    setGroupings(null);
    setError(null);
    if (_STRONGS_RE.test(q)) {
      const normalized = /^[GgHh]/i.test(q) ? q.toUpperCase() : q;
      loadProfile(normalized);
      return;
    }
    setLoading(true);
    try {
      if (_isGreekHebrew(q)) {
        const data = await api.lexiconLookup(q);
        if (!data.length) setError("No matches found.");else if (data.length === 1) loadProfile(data[0].strongs);else setMatches(data);
      } else {
        const data = await api.lexiconEnglish(q, corpus, testament);
        if (data.length) {
          setGroupings(data);
        } else {
          // No English meaning matched — the input may be a Greek/Hebrew word
          // typed in Latin letters (e.g. "pneuma"). Fall back to the lookup,
          // which matches transliterations accent-insensitively.
          const alt = await api.lexiconLookup(q);
          if (!alt.length) setError("No matches found for \"" + q + "\".");else if (alt.length === 1) loadProfile(alt[0].strongs);else setMatches(alt);
        }
      }
    } catch {
      setError("Search failed.");
    } finally {
      setLoading(false);
    }
  };

  // Apply the Greek/Hebrew filter to the results grid (client-side row hide).
  const visibleGroupings = !groupings ? null : language === "all" ? groupings : groupings.filter(g => language === "greek" ? g.strongs[0] === "G" : g.strongs[0] === "H");
  return /*#__PURE__*/React.createElement("div", {
    className: "lexicon-view"
  }, /*#__PURE__*/React.createElement("section", {
    className: "search"
  }, /*#__PURE__*/React.createElement("div", {
    className: "search-cell"
  }, /*#__PURE__*/React.createElement("label", {
    className: "search-label"
  }, /*#__PURE__*/React.createElement("span", {
    className: "search-eyebrow"
  }, "Word lookup")), /*#__PURE__*/React.createElement("form", {
    className: "search-field",
    onSubmit: handleSubmit
  }, /*#__PURE__*/React.createElement(Icon.Search, {
    className: "search-icon"
  }), /*#__PURE__*/React.createElement("input", {
    className: "search-input",
    type: "text",
    value: query,
    onChange: e => setQuery(e.target.value),
    placeholder: "Greek, Hebrew, English, or Strong's (G4151, H7307)\u2026",
    autoFocus: true
  }), /*#__PURE__*/React.createElement("button", {
    type: "submit",
    className: "search-go",
    "aria-label": "Search",
    disabled: loading
  }, loading ? /*#__PURE__*/React.createElement("span", {
    className: "spinner"
  }) : /*#__PURE__*/React.createElement(Icon.ArrowRight, null))))), /*#__PURE__*/React.createElement("div", {
    className: "lexicon-toolbar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lexicon-corpus-toggle"
  }, profile ?
  /*#__PURE__*/
  /* Drilled into a word: All is N/A (search-only); gray a corpus the
     word isn't in — but ABP stays live for backfilled proper nouns. */
  React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    className: "lct-btn",
    disabled: true,
    title: "Pick ABP or KJV to study this word"
  }, "All"), /*#__PURE__*/React.createElement("button", {
    className: "lct-btn" + (profileCorpus === "abp" ? " on" : ""),
    disabled: !profile.has_abp,
    onClick: () => switchProfileCorpus("abp")
  }, "ABP"), /*#__PURE__*/React.createElement("button", {
    className: "lct-btn" + (profileCorpus === "kjv" ? " on" : ""),
    disabled: !profile.has_kjv,
    onClick: () => switchProfileCorpus("kjv")
  }, "KJV")) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    className: "lct-btn" + (corpus === "all" ? " on" : ""),
    onClick: () => switchCorpus("all")
  }, "All"), /*#__PURE__*/React.createElement("button", {
    className: "lct-btn" + (corpus === "abp" ? " on" : ""),
    disabled: !_comboOK("abp", testament, language),
    onClick: () => switchCorpus("abp")
  }, "ABP"), /*#__PURE__*/React.createElement("button", {
    className: "lct-btn" + (corpus === "kjv" ? " on" : ""),
    disabled: !_comboOK("kjv", testament, language),
    onClick: () => switchCorpus("kjv")
  }, "KJV"))), /*#__PURE__*/React.createElement("div", {
    className: "lexicon-corpus-toggle"
  }, ["all", "ot", "nt"].map(t => /*#__PURE__*/React.createElement("button", {
    key: t,
    className: "lct-btn" + (testament === t ? " on" : ""),
    disabled: !profile && t !== "all" && !_comboOK(corpus, t, language),
    onClick: () => switchTestament(t)
  }, t === "all" ? "All" : t.toUpperCase()))), !profile && /*#__PURE__*/React.createElement("div", {
    className: "lexicon-corpus-toggle"
  }, /*#__PURE__*/React.createElement("button", {
    className: "lct-btn" + (language === "all" ? " on" : ""),
    onClick: () => switchLanguage("all")
  }, "All"), /*#__PURE__*/React.createElement("button", {
    className: "lct-btn" + (language === "greek" ? " on" : ""),
    disabled: !_comboOK(corpus, testament, "greek"),
    onClick: () => switchLanguage("greek")
  }, "Greek"), /*#__PURE__*/React.createElement("button", {
    className: "lct-btn" + (language === "hebrew" ? " on" : ""),
    disabled: !_comboOK(corpus, testament, "hebrew"),
    onClick: () => switchLanguage("hebrew")
  }, "Hebrew"))), error && /*#__PURE__*/React.createElement("p", {
    className: "lexicon-error"
  }, error), matches && !profile && /*#__PURE__*/React.createElement("div", {
    className: "lexicon-matches"
  }, matches.map(m => /*#__PURE__*/React.createElement("button", {
    key: m.strongs,
    className: "lexicon-match-row",
    onClick: () => loadProfile(m.strongs)
  }, /*#__PURE__*/React.createElement("span", {
    className: "lexicon-match-strongs"
  }, m.strongs), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-match-lemma"
  }, m.lemma), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-match-translit"
  }, m.translit), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-match-gloss"
  }, m.gloss)))), groupings && !profile && /*#__PURE__*/React.createElement("div", {
    className: "lexicon-results"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lexicon-dist-label"
  }, "rendered as \"", query.trim(), "\" \xB7 ", visibleGroupings.length, " ", visibleGroupings.length === 1 ? "word" : "words"), visibleGroupings.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "lexicon-dist-label"
  }, "No ", language === "greek" ? "Greek" : "Hebrew", " words rendered \"", query.trim(), "\".") : visibleGroupings.map(g => /*#__PURE__*/React.createElement("button", {
    key: g.strongs,
    className: "lexicon-result-row",
    onClick: () => loadProfile(g.strongs, corpus === "all" ? undefined : corpus)
  }, /*#__PURE__*/React.createElement("span", {
    className: "lexicon-result-topbar"
  }, /*#__PURE__*/React.createElement("span", {
    className: "lexicon-result-head"
  }, /*#__PURE__*/React.createElement("span", {
    className: "lexicon-match-strongs"
  }, g.strongs), g.lemma && /*#__PURE__*/React.createElement("span", {
    className: "lexicon-match-lemma",
    dir: g.strongs[0] === "H" ? "rtl" : undefined
  }, g.lemma), g.translit && /*#__PURE__*/React.createElement("span", {
    className: "lexicon-match-translit"
  }, g.translit)), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-result-end"
  }, /*#__PURE__*/React.createElement("span", {
    className: "lexicon-result-count"
  }, g.count), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-result-chev"
  }, "\u203A"))), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-result-preview"
  }, renderRowPreview(g))))), profile && /*#__PURE__*/React.createElement("div", {
    className: "lexicon-profile"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lexicon-profile-header"
  }, (groupings || matches) && /*#__PURE__*/React.createElement("button", {
    className: "lexicon-back-btn",
    title: `Back to "${query.trim()}" results`,
    onClick: () => {
      setProfile(null);
      setSelectedBook(null);
      setVerseList(null);
    }
  }, "\u2190"), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-lemma",
    dir: profile.strongs[0] === "H" ? "rtl" : undefined
  }, profile.lemma), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-translit"
  }, profile.translit), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-strongs-tag"
  }, profile.strongs), /*#__PURE__*/React.createElement("span", {
    className: "lexicon-total"
  }, testament === "all" ? profile.total : (filteredBooks || profile.books).filter(b => (b.testament || "").toLowerCase() === testament).reduce((s, b) => s + b.count, 0), " occurrences")), (profile.definition || /^G/i.test(profile.strongs)) && /*#__PURE__*/React.createElement("div", {
    className: "lexicon-def-section"
  }, /*#__PURE__*/React.createElement("button", {
    className: "lexicon-def-toggle",
    onClick: () => setShowDef(v => !v)
  }, "Definition", showDef && (!/^G/i.test(profile.strongs) ? /*#__PURE__*/React.createElement("span", {
    className: "lexicon-def-src"
  }, "BDB") : !lsjLoading && lsjEntry ? /*#__PURE__*/React.createElement("span", {
    className: "lexicon-def-src"
  }, lsjEntry.source === "strongs" ? "Strong's" : lsjEntry.source === "abp_ext" ? "ABP" : "LSJ") : null), " ", showDef ? "▲" : "▼"), showDef && (!/^G/i.test(profile.strongs) ? /*#__PURE__*/React.createElement("p", {
    className: "lexicon-definition"
  }, profile.definition) /* Hebrew: BDB */ : lsjLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lsj-def lsj-def--loading"
  }, "Loading\u2026") : !lsjEntry ? /*#__PURE__*/React.createElement("p", {
    className: "lexicon-definition"
  }, profile.definition) /* no LSJ: strongs_def */ : lsjEntry.source === "strongs" ? /*#__PURE__*/React.createElement("div", {
    className: "lsj-def",
    dangerouslySetInnerHTML: {
      __html: lsjEntry.def_html
    }
  }) : lsjSummaryLoading ? /*#__PURE__*/React.createElement(LsjSummary, {
    data: null,
    loading: true
  }) : lsjSummary && lsjSummary.summary ? /*#__PURE__*/React.createElement(LsjSummary, {
    data: lsjSummary,
    loading: false
  }) : /*#__PURE__*/React.createElement("div", {
    className: "lsj-def",
    dangerouslySetInnerHTML: {
      __html: lsjEntry.def_html
    }
  }) /* AI down: raw LSJ */)), selectedBook ? (bookGlosses || profile.glosses) && (bookGlosses || profile.glosses).length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "lexicon-glosses"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lexicon-gloss-label"
  }, "In this book"), /*#__PURE__*/React.createElement("div", {
    className: "lexicon-dist-list"
  }, (bookGlosses || profile.glosses).map((g, i) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: g.gloss
  }, i > 0 && /*#__PURE__*/React.createElement("span", {
    className: "lexicon-dist-sep"
  }, " \xB7 "), /*#__PURE__*/React.createElement("button", {
    className: "lexicon-dist-item" + (selectedGloss === g.gloss ? " selected" : ""),
    onClick: () => selectGloss(g.gloss)
  }, g.gloss, /*#__PURE__*/React.createElement("span", {
    className: "lexicon-dist-count"
  }, g.count)))))) : /*#__PURE__*/React.createElement(React.Fragment, null, renderGlossLine("abp", "ABP renders this as", profile.abp_glosses), renderGlossLine("kjv", "KJV renders this as", profile.kjv_glosses)), /*#__PURE__*/React.createElement("div", {
    className: "lexicon-distribution"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lexicon-dist-header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "lexicon-dist-label"
  }, "Distribution by book")), /*#__PURE__*/React.createElement("div", {
    className: "lexicon-dist-list"
  }, (filteredBooks || profile.books).filter(b => testament === "all" || (b.testament || "").toLowerCase() === testament).map((b, i) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: b.book
  }, i > 0 && /*#__PURE__*/React.createElement("span", {
    className: "lexicon-dist-sep"
  }, " \xB7 "), /*#__PURE__*/React.createElement("button", {
    className: "lexicon-dist-item" + (selectedBook === b.book ? " selected" : ""),
    onClick: () => selectBook(b.book)
  }, b.name, /*#__PURE__*/React.createElement("span", {
    className: "lexicon-dist-count"
  }, b.count)))))), selectedBook && /*#__PURE__*/React.createElement("div", {
    className: "corpus-groups"
  }, verseLoading ? /*#__PURE__*/React.createElement("div", {
    className: "lexicon-verse-loading"
  }, "Loading\u2026") : verseList && verseList[0] && verseList[0].error ? /*#__PURE__*/React.createElement("div", {
    className: "lexicon-verse-loading",
    style: {
      color: "red"
    }
  }, verseList[0].error) : verseList && verseList.length ? /*#__PURE__*/React.createElement(CorpusGroup, {
    label: profile.books.find(b => b.book === selectedBook)?.name || selectedBook,
    verses: verseList.map(v => ({
      book: selectedBook,
      chapter: v.chapter,
      verse: v.verse,
      ref: `${selectedBook} ${v.chapter}:${v.verse}`
    })),
    allResults: [],
    onWordClick: onWordClick,
    onReadInContext: onNavigateToLibrary ? (b, c, vv) => onNavigateToLibrary(b, c, vv, profileCorpus) : undefined,
    textMode: profileCorpus === "kjv" ? "kjv" : "greek",
    primaryStrongs: null,
    citedStrongs: citedStrongs,
    kjvCache: {}
  }) : /*#__PURE__*/React.createElement("div", {
    className: "lexicon-verse-loading"
  }, "No verses."))));
}

// ============================================================
// STATS — owner-only visitor dashboard (in-house, from notes.db)
// ============================================================
function StatCard({
  n,
  label
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "stats-card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-card-n"
  }, n != null ? n.toLocaleString() : "—"), /*#__PURE__*/React.createElement("div", {
    className: "stats-card-l"
  }, label));
}
function StatsView() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let cancelled = false;
    api.stats().then(d => {
      if (cancelled) return;
      if (d) setData(d);else setErr(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);
  if (err) return /*#__PURE__*/React.createElement("div", {
    className: "stats-view"
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "Couldn't load stats."));
  if (!data) return /*#__PURE__*/React.createElement("div", {
    className: "stats-view"
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "Loading\u2026"));
  const maxV = Math.max(1, ...data.by_day.map(d => d.views));
  const accounts = data.accounts || [];
  const fmtDate = s => s ? String(s).slice(0, 10) : "—";
  return /*#__PURE__*/React.createElement("div", {
    className: "stats-view"
  }, /*#__PURE__*/React.createElement("h1", {
    className: "stats-title"
  }, "Visitors"), /*#__PURE__*/React.createElement("div", {
    className: "stats-sub"
  }, "Your own visits aren't counted. No cookies, no IPs stored."), /*#__PURE__*/React.createElement("div", {
    className: "stats-cards"
  }, /*#__PURE__*/React.createElement(StatCard, {
    n: data.unique_visitors,
    label: "Unique visitors"
  }), /*#__PURE__*/React.createElement(StatCard, {
    n: data.total_views,
    label: "Total views"
  }), /*#__PURE__*/React.createElement(StatCard, {
    n: data.today,
    label: "Today"
  }), /*#__PURE__*/React.createElement(StatCard, {
    n: data.last7,
    label: "Last 7 days"
  }), /*#__PURE__*/React.createElement(StatCard, {
    n: data.last30,
    label: "Last 30 days"
  }), /*#__PURE__*/React.createElement(StatCard, {
    n: accounts.length,
    label: "Accounts"
  })), /*#__PURE__*/React.createElement("div", {
    className: "stats-section-title"
  }, "Views \u2014 last 30 days"), data.by_day.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "No visits yet.") : /*#__PURE__*/React.createElement("div", {
    className: "stats-bars"
  }, data.by_day.map(d => /*#__PURE__*/React.createElement("div", {
    key: d.day,
    className: "stats-bar-col",
    title: `${d.day} · ${d.views} views · ${d.uniques} unique`
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-bar",
    style: {
      height: Math.max(2, Math.round(d.views / maxV * 100)) + "%"
    }
  })))), /*#__PURE__*/React.createElement("div", {
    className: "stats-section-title"
  }, "Top referrers"), data.top_ref.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "None yet.") : /*#__PURE__*/React.createElement("div", {
    className: "stats-refs"
  }, data.top_ref.map(r => /*#__PURE__*/React.createElement("div", {
    key: r.ref,
    className: "stats-ref-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "stats-ref-name"
  }, r.ref), /*#__PURE__*/React.createElement("span", {
    className: "stats-ref-n"
  }, r.n.toLocaleString())))), /*#__PURE__*/React.createElement("div", {
    className: "stats-section-title"
  }, "Accounts"), accounts.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "No accounts yet.") : /*#__PURE__*/React.createElement("div", {
    className: "stats-refs"
  }, accounts.map(a => /*#__PURE__*/React.createElement("div", {
    key: a.email,
    className: "stats-ref-row",
    title: `Last sign-in: ${fmtDate(a.last_seen)}`
  }, /*#__PURE__*/React.createElement("span", {
    className: "stats-ref-name"
  }, a.email), /*#__PURE__*/React.createElement("span", {
    className: "stats-ref-n"
  }, fmtDate(a.created))))));
}

// ============================================================
// ADMIN — accounts & roles (admin-only; set who's a berean)
// ============================================================
function AdminView() {
  const [users, setUsers] = useState(null);
  const [err, setErr] = useState(false);
  const [busy, setBusy] = useState(null);
  const load = () => {
    api.adminUsers().then(d => {
      if (d && d.users) {
        setUsers(d.users);
        setErr(false);
      } else setErr(true);
    });
  };
  useEffect(() => {
    load();
  }, []);
  const change = (u, role) => {
    if (role === u.role) return;
    setBusy(u.id);
    api.setRole(u.id, role).then(r => {
      setBusy(null);
      if (r && r.ok) setUsers(us => us.map(x => x.id === u.id ? {
        ...x,
        role
      } : x));else load();
    });
  };
  if (err) return /*#__PURE__*/React.createElement("div", {
    className: "stats-view"
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "Couldn't load accounts."));
  if (!users) return /*#__PURE__*/React.createElement("div", {
    className: "stats-view"
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "Loading\u2026"));
  return /*#__PURE__*/React.createElement("div", {
    className: "stats-view"
  }, /*#__PURE__*/React.createElement("h1", {
    className: "stats-title"
  }, "Accounts & roles"), /*#__PURE__*/React.createElement("div", {
    className: "stats-sub"
  }, /*#__PURE__*/React.createElement("b", null, "user"), " = signed in \xB7 ", /*#__PURE__*/React.createElement("b", null, "berean"), " = ESV/NIV access \xB7 ", /*#__PURE__*/React.createElement("b", null, "admin"), " = everything"), users.length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "stats-empty"
  }, "No accounts yet.") : /*#__PURE__*/React.createElement("div", {
    className: "admin-users"
  }, users.map(u => /*#__PURE__*/React.createElement("div", {
    key: u.id,
    className: "admin-user-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "admin-user-email"
  }, u.email, u.owner ? " · you" : ""), u.owner ? /*#__PURE__*/React.createElement("span", {
    className: "admin-user-locked"
  }, "admin") : /*#__PURE__*/React.createElement("select", {
    className: "admin-role-sel",
    value: u.role,
    disabled: busy === u.id,
    onChange: e => change(u, e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: "user"
  }, "user"), /*#__PURE__*/React.createElement("option", {
    value: "berean"
  }, "berean"), /*#__PURE__*/React.createElement("option", {
    value: "admin"
  }, "admin"))))));
}

// ============================================================
// APP
// ============================================================
function App() {
  const [q2, setQ2] = useState("");
  const [allResults, setAllResults] = useState([]);
  const [aiMeta, setAiMeta] = useState(null);
  const [showAllAi, setShowAllAi] = useState(false);
  const [mode, setMode] = useState("idle");
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState("");
  const [aiNotice, setAiNotice] = useState("");
  const [activeEntry, setActiveEntry] = useState(null);
  const [entryView, setEntryView] = useState(null); // which tab opened the word card (library|search|lexicon) — scopes the rail to that tab
  const [corpusFilter, setCorpusFilter] = useState("all"); // "all" | "ot" | "nt"
  const [corpusSort, setCorpusSort] = useState("curated"); // "curated" | "canonical"
  const [corpusTextMode, setCorpusTextMode] = useState("abp"); // "abp" | "kjv"
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 1100);
  // Remember the active tab across refreshes (guard against a stale/removed value).
  const _VIEWS = ["library", "lexicon", "search", "notes", "study", "about"];
  const [mainView, setMainView] = useState(() => {
    try {
      const v = localStorage.getItem("lexica.view.v1");
      return _VIEWS.includes(v) ? v : "library";
    } catch (e) {
      return "library";
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem("lexica.view.v1", mainView);
    } catch (e) {}
  }, [mainView]);
  const [libNav, setLibNav] = useState(null);
  const [libCrossRef, setLibCrossRef] = useState(null);
  const [lexiconPendingStrongs, setLexiconPendingStrongs] = useState(null);
  const [studyPending, setStudyPending] = useState(null); // open this name-topic in Study (from the metaV sidebar)
  const [libTranslation, setLibTranslation] = useState("abp");
  // Which panel is the base of the detail rail ("overview" = chapter summary, "intro" =
  // chrono day intro) — so a word/xref panel labels its back link to match.
  const [libDetailBase, setLibDetailBase] = useState("overview");
  const [activeNote, setActiveNote] = useState(null); // note id being edited
  const [resetToken, setResetToken] = useState(null); // ?reset=<token> from a password-reset email
  const [focusMode, setFocusMode] = useState(false); // distraction-free reading: chrome hidden (library only, not remembered)

  // Open a note's editor — closes the word / cross-ref panels so one panel owns the slot.
  const openNote = id => {
    setActiveEntry(null);
    setLibCrossRef(null);
    setActiveNote(id);
  };
  // From the Notes tab: jump to the verse in the Library, then open the editor.
  const openNoteFromList = n => {
    if (n.corpus === "bible") {
      searchScrollRef.current = window.scrollY;
      setLibEverVisited(true);
      setMainView("library");
      setLibNav({
        book: n.book,
        chapter: n.chapter,
        highlight: n.start.verse,
        scroll: true,
        extern: true,
        translation: n.translation === "kjv" ? "kjv" : "abp"
      });
    }
    openNote(n.id);
  };
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 1100);
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // A wheel over the fixed chrome (header banner, toolbar, left nav / chrono panel)
  // shouldn't scroll the reading pane (which rides the window). Block the page scroll
  // there — but first let an inner list (the book / day / era list) consume the wheel
  // if it still has room to scroll. The reading area and detail panel are untouched.
  useEffect(() => {
    const onWheel = e => {
      const chrome = e.target.closest && e.target.closest(".hdr, .lib-bar, .lib-toolbar, .nav, .detail-side");
      if (!chrome) return;
      const dir = Math.sign(e.deltaY);
      let node = e.target;
      while (node && node !== chrome.parentElement) {
        if (node.nodeType === 1) {
          const oy = getComputedStyle(node).overflowY;
          if ((oy === "auto" || oy === "scroll") && node.scrollHeight > node.clientHeight) {
            const atTop = node.scrollTop <= 0;
            const atBottom = node.scrollTop + node.clientHeight >= node.scrollHeight - 1;
            if (!(dir < 0 && atTop || dir > 0 && atBottom)) return; // inner list can still scroll
          }
        }
        node = node.parentElement;
      }
      e.preventDefault(); // nothing left to scroll in the chrome → don't scroll the page
    };
    document.addEventListener("wheel", onWheel, {
      passive: false
    });
    return () => document.removeEventListener("wheel", onWheel);
  }, []);
  const handleVerseNumberClick = (book, chapter, verse, translation) => {
    setActiveEntry(null);
    setActiveNote(null);
    setLibCrossRef({
      book,
      chapter,
      verse,
      translation: translation || "abp"
    });
    setLibNav(prev => ({
      ...(prev || {}),
      book,
      chapter,
      highlight: verse
    }));
  };

  // Returning to the Library tab re-scrolls to the placeholder verse (the last verse
  // you clicked / jumped to), so it survives a tab switch like a version switch does.
  useEffect(() => {
    if (mainView === "library") setLibNav(n => n && n.highlight != null ? {
      ...n,
      scroll: true,
      instant: true
    } : n);
  }, [mainView]);

  // Corpus-filtered AI results (OT/NT filter)
  const corpusFilteredResults = useMemo(() => {
    let r = allResults;
    if (corpusFilter === "ot") r = r.filter(e => !NT_BOOKS.has(e.book));
    if (corpusFilter === "nt") r = r.filter(e => NT_BOOKS.has(e.book));
    return r;
  }, [allResults, corpusFilter]);

  // Count occurrences per strongs across AI results
  const countMap = useMemo(() => {
    const map = {};
    for (const e of corpusFilteredResults) {
      const key = e.strongs_raw || e.strongs_base;
      if (key) map[key] = (map[key] || 0) + 1;
    }
    return map;
  }, [corpusFilteredResults]);

  // Key strongs from AI search
  const primaryStrongs = useMemo(() => {
    if (mode === "ai" && aiMeta && aiMeta.keyStrongs && aiMeta.keyStrongs.length > 0) return aiMeta.keyStrongs;
    return null;
  }, [mode, aiMeta]);

  // Compute citedStrongs at App level — single source of truth, no prop-threading issues
  const citedStrongsApp = useMemo(() => {
    if (!primaryStrongs || !primaryStrongs.length) return null;
    const s = new Set();
    for (const p of primaryStrongs) {
      if (p.strongs_base) {
        const bare = strongsBare(p.strongs_base);
        s.add(p.strongs_base); // as-is (e.g. "4151" or "G4151")
        s.add(bare); // bare (e.g. "4151")
        s.add(`G${bare}`); // G-prefixed
        s.add(`H${bare}`); // H-prefixed
      }
    }
    return s.size > 0 ? s : null;
  }, [primaryStrongs]);

  // Count of distinct primary verses (AI mode only)
  const primaryVerseCount = useMemo(() => {
    if (mode !== "ai") return null;
    const seen = new Set();
    for (const e of allResults) {
      if (e.is_primary) seen.add(e.ref);
    }
    return seen.size;
  }, [allResults, mode]);
  const [showTour, setShowTour] = useState(() => {
    try {
      return !localStorage.getItem("lexica_tour_seen");
    } catch {
      return false;
    }
  });
  const handleTourDone = () => {
    try {
      localStorage.setItem("lexica_tour_seen", "1");
    } catch {}
    setShowTour(false);
  };
  const [libEverVisited, setLibEverVisited] = useState(true);
  const searchScrollRef = useRef(0);

  // Deep link from the crawlable /read/ pages ("Open in interactive reader" →
  // /?b=<abbrev>&c=<chapter>&t=<text>). Jump to that WHOLE chapter the same way a
  // Search/Notes jump does — book selected, left nav follows, reader at top — but
  // with NO verse highlight (it's a chapter, not a verse). Then strip the query so a
  // refresh doesn't re-jump; the spot is saved to localStorage like any reading position.
  useEffect(() => {
    let p;
    try {
      p = new URLSearchParams(window.location.search);
    } catch (e) {
      return;
    }
    const reset = p.get("reset");
    if (reset) {
      // arrived from a password-reset email → open the reset dialog
      setResetToken(reset);
      try {
        window.history.replaceState(null, "", window.location.pathname);
      } catch (e) {}
      return;
    }
    const lex = p.get("lex");
    if (lex) {
      // word page → open the Lexicon tab on that Strong's number
      setMainView("lexicon");
      setLexiconPendingStrongs(lex);
      try {
        window.history.replaceState(null, "", window.location.pathname);
      } catch (e) {}
      return;
    }
    const b = p.get("b");
    if (!b) return;
    const t = p.get("t");
    const translation = ["abp", "kjv", "bsb", "heb"].includes(t) ? t : "abp";
    const chapter = Math.max(1, parseInt(p.get("c"), 10) || 1);
    setLibEverVisited(true);
    setMainView("library");
    setLibTranslation(translation);
    setLibNav({
      book: b,
      chapter,
      highlight: null,
      scroll: false,
      extern: true,
      translation
    });
    try {
      window.history.replaceState(null, "", window.location.pathname);
    } catch (e) {}
    requestAnimationFrame(() => window.scrollTo(0, 0));
  }, []);

  // Visitor stats: count this page load once (the server skips the owner's own
  // visits), and figure out whether the logged-in user is the owner so we can show
  // the private Stats tab. Re-check only when the signed-in email actually changes.
  const [owner, setOwner] = useState(false);
  useEffect(() => {
    api.statsHit();
  }, []);
  useEffect(() => {
    let last;
    const check = () => {
      let email = null;
      try {
        email = (NotesStore.authInfo() || {}).email || null;
      } catch (e) {}
      if (email === last) return;
      last = email;
      api.statsOwner().then(d => setOwner(!!(d && d.owner)));
    };
    check();
    return NotesStore.subscribe(check); // setAuth notifies on login/logout
  }, []);
  const handleReadInContext = (book, chapter, verse) => {
    searchScrollRef.current = window.scrollY;
    // `extern` (jump came from OUTSIDE the reader — Search results, or a word panel opened over them)
    // flips chrono→canonical so the verse shows in its chapter. A word panel opened IN the library
    // (mainView already "library") is an in-reader control, so it stays chronological.
    setLibNav({
      book,
      chapter,
      highlight: verse,
      scroll: true,
      extern: mainView !== "library"
    });
    setLibEverVisited(true);
    setMainView("library");
    // Desktop: queue the verse's cross-references for the rail. If it's resting on the summary
    // the xref shows right away; if a word-study / note panel is up, the xref sits UNDER it (its
    // render is gated on those) and surfaces when that panel is closed — instead of the summary.
    // Mobile keeps the reader unobstructed (xref is a full bottom sheet there).
    if (!isMobile) setLibCrossRef({
      book,
      chapter,
      verse,
      translation: "abp"
    });
  };
  const handleNavChange = view => {
    if (view === "library") {
      searchScrollRef.current = window.scrollY;
      setLibEverVisited(true);
      if (!libNav) setLibNav({});
    } else {
      const saved = searchScrollRef.current;
      requestAnimationFrame(() => window.scrollTo(0, saved));
    }
    setMainView(view);
  };
  const handleNavigateToLexicon = (strongs, corpus) => {
    if (!strongs) return;
    setActiveEntry(null); // close the word panel (bottom sheet on mobile) before showing the lexicon
    setLibCrossRef(null);
    setLexiconPendingStrongs({
      strongs,
      corpus
    }); // corpus: "abp" | "kjv" | undefined (default by language)
    handleNavChange("lexicon");
  };
  const handleOpenStudyName = id => {
    if (!id) return;
    setActiveEntry(null); // close the person/place panel before jumping to Study
    setLibCrossRef(null);
    setStudyPending(id);
    handleNavChange("study");
  };
  const handleAiSearch = async overrideQ => {
    const q = (overrideQ !== undefined ? overrideQ : q2).trim();
    if (!q) return;
    if (overrideQ !== undefined) setQ2(overrideQ);
    setMainView("search");
    setAiLoading(true);
    setError("");
    setAiNotice("");
    setMode("ai");
    setShowAllAi(false);
    setActiveEntry(null);
    try {
      const data = await api.aiSearch(q);
      if (data.out_of_scope) {
        setAiNotice(data.explanation || "This tool searches the Greek Bible corpus — try a question about a word, theme, or passage.");
        setAllResults([]);
        setAiMeta(null);
      } else if (data.error) {
        setError(data.error);
        setAllResults([]);
        setAiMeta(null);
      } else {
        setAllResults(flattenAiResults(data.results || []));
        setAiMeta({
          query: q,
          explanation: data.explanation || "",
          total: data.total || 0,
          keyStrongs: data.key_strongs || []
        });
      }
    } catch (e) {
      setError("Network error: " + e.message);
      setAllResults([]);
      setAiMeta(null);
    } finally {
      setAiLoading(false);
    }
  };
  const searchLabel = q2.trim();

  // The right rail belongs to the tab that opened a card: a word card scopes to
  // where it was opened (Library, Search, or Lexicon), xref + note are Library-only.
  // Leaving that tab hides the card (the state is kept), and returning shows it again
  // — so a card never bleeds onto a tab it wasn't opened in.
  const showWord = !!activeEntry && mainView === entryView;
  const showXref = !!libCrossRef && mainView === "library";
  const showNote = !!activeNote && mainView === "library";
  // Desktop Library: when nothing is selected, the right panel rests on the
  // book/chapter overview (SummaryPanel) — same slot the word/xref panels use, so
  // `has-detail` stays on and the reading column keeps its condensed measure. Mobile
  // never shows the summary.
  const showLibSummary = !isMobile && mainView === "library" && !showWord && !showXref && !showNote;
  return /*#__PURE__*/React.createElement("div", {
    className: "app view-" + mainView + " " + (showWord || showXref || showNote || showLibSummary ? "has-detail " : "") + (focusMode && mainView === "library" ? "focus-mode" : "")
  }, /*#__PURE__*/React.createElement(Header, {
    activeView: mainView,
    onNavChange: handleNavChange,
    owner: owner
  }), isMobile && mainView !== "library" && /*#__PURE__*/React.createElement("div", {
    className: "mobile-brand-bar"
  }, /*#__PURE__*/React.createElement("svg", {
    width: "16",
    height: "16",
    viewBox: "0 0 24 24",
    fill: "none"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3",
    stroke: "currentColor",
    strokeWidth: "1.6",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M11 7v6M14 10h-6",
    stroke: "currentColor",
    strokeWidth: "1.6",
    strokeLinecap: "round"
  })), /*#__PURE__*/React.createElement("span", {
    className: "mobile-brand-name"
  }, "Lexica"), /*#__PURE__*/React.createElement("span", {
    className: "mobile-brand-sub"
  }, "Greek & Hebrew Word Study")), /*#__PURE__*/React.createElement("main", {
    className: "main"
  }, libEverVisited && /*#__PURE__*/React.createElement("div", {
    style: {
      display: mainView === "library" ? undefined : "none"
    }
  }, /*#__PURE__*/React.createElement(LibraryView, {
    nav: libNav,
    onNavChange: setLibNav,
    onWordClick: e => {
      setLibCrossRef(null);
      setActiveNote(null);
      setActiveEntry(e);
      setEntryView("library");
    },
    onVerseNumberClick: handleVerseNumberClick,
    onOpenNote: openNote,
    onTranslationChange: setLibTranslation,
    isMobile: isMobile,
    showSummary: showLibSummary,
    focusMode: focusMode,
    onToggleFocus: () => setFocusMode(f => !f),
    onDetailBaseChange: setLibDetailBase
  })), mainView === "about" && /*#__PURE__*/React.createElement(AboutView, {
    owner: owner
  }), mainView === "notes" && /*#__PURE__*/React.createElement(NotesView, {
    onOpen: openNoteFromList
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: mainView === "study" ? undefined : "none"
    }
  }, /*#__PURE__*/React.createElement(StudyView, {
    admin: owner,
    pending: studyPending,
    onConsumed: () => setStudyPending(null),
    onNavigateToLibrary: handleReadInContext
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: mainView === "lexicon" ? undefined : "none"
    }
  }, /*#__PURE__*/React.createElement(LexiconView, {
    onNavigateToSearch: q => {
      handleNavChange("search");
      setQ2(q);
    },
    onNavigateToLibrary: (book, chapter, verse, corpus) => {
      searchScrollRef.current = window.scrollY;
      setLibNav({
        book,
        chapter,
        highlight: verse,
        scroll: true,
        extern: true,
        translation: corpus === "kjv" ? "kjv" : "abp"
      });
      setLibEverVisited(true);
      setMainView("library");
      // Same as Read-in-context: desktop queues the xref (shows now if resting on the
      // summary, else tucks under the open panel and surfaces when it closes).
      if (!isMobile) setLibCrossRef({
        book,
        chapter,
        verse,
        translation: corpus === "kjv" ? "kjv" : "abp"
      });
    },
    onWordClick: e => {
      setActiveEntry(e);
      setEntryView("lexicon");
    },
    pendingStrongs: lexiconPendingStrongs,
    onPendingStrongsConsumed: () => setLexiconPendingStrongs(null),
    isMobile: isMobile
  })), /*#__PURE__*/React.createElement("div", {
    className: "main-inner",
    style: {
      display: mainView === "library" || mainView === "about" || mainView === "lexicon" || mainView === "notes" || mainView === "study" ? "none" : undefined
    }
  }, /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(SearchBar, {
    q2: q2,
    setQ2: setQ2,
    onAiSearch: handleAiSearch,
    aiLoading: aiLoading
  }), aiNotice && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "14px",
      padding: "12px 16px",
      background: "var(--accent-soft, #f0f4ff)",
      border: "1px solid var(--accent, #b0bfff)",
      borderRadius: "10px",
      color: "var(--ink-2, #444)",
      fontSize: "14px"
    }
  }, aiNotice), error && /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "14px",
      padding: "12px 16px",
      background: "#fef2f2",
      border: "1px solid #fecaca",
      borderRadius: "10px",
      color: "#b91c1c",
      fontSize: "14px"
    }
  }, error), aiMeta && /*#__PURE__*/React.createElement(AIAnswer, {
    query: aiMeta.query,
    explanation: aiMeta.explanation,
    keyStrongs: aiMeta.keyStrongs || [],
    onPick: e => {
      setActiveEntry(e);
      setEntryView("search");
    }
  }), mode === "ai" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "results-head"
  }, /*#__PURE__*/React.createElement("div", {
    className: "results-meta"
  }, /*#__PURE__*/React.createElement("span", {
    className: "results-count"
  }, loading || aiLoading ? "…" : primaryVerseCount), /*#__PURE__*/React.createElement("span", {
    className: "results-label"
  }, "primary ", primaryVerseCount === 1 ? "verse" : "verses"), !loading && aiMeta && aiMeta.total > primaryVerseCount && /*#__PURE__*/React.createElement("button", {
    className: "see-all-link",
    onClick: () => setShowAllAi(v => !v)
  }, showAllAi ? "Show less" : `See all ${aiMeta.total} occurrences`), searchLabel && !aiLoading && /*#__PURE__*/React.createElement("span", {
    className: "results-for"
  }, "for \"", /*#__PURE__*/React.createElement("b", null, searchLabel), "\"")), /*#__PURE__*/React.createElement("div", {
    className: "results-controls",
    style: {
      marginLeft: "auto"
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "results-sort"
  }, /*#__PURE__*/React.createElement("button", {
    className: "sort-btn " + (corpusFilter === "all" ? "on" : ""),
    onClick: () => setCorpusFilter("all")
  }, "All"), /*#__PURE__*/React.createElement("button", {
    className: "sort-btn " + (corpusFilter === "ot" ? "on" : ""),
    onClick: () => setCorpusFilter("ot")
  }, "OT"), /*#__PURE__*/React.createElement("button", {
    className: "sort-btn " + (corpusFilter === "nt" ? "on" : ""),
    onClick: () => setCorpusFilter("nt")
  }, "NT"), /*#__PURE__*/React.createElement("span", {
    style: {
      margin: "0 4px",
      color: "var(--rule-2)"
    }
  }, "|"), /*#__PURE__*/React.createElement("button", {
    className: "sort-btn " + (corpusSort === "curated" ? "on" : ""),
    onClick: () => setCorpusSort("curated")
  }, "Curated"), /*#__PURE__*/React.createElement("button", {
    className: "sort-btn " + (corpusSort === "canonical" ? "on" : ""),
    onClick: () => setCorpusSort("canonical")
  }, "Canonical"), /*#__PURE__*/React.createElement("span", {
    style: {
      margin: "0 4px",
      color: "var(--rule-2)"
    }
  }, "|"), /*#__PURE__*/React.createElement("button", {
    className: "sort-btn " + (corpusTextMode === "abp" ? "on" : ""),
    onClick: () => setCorpusTextMode("abp")
  }, "ABP"), /*#__PURE__*/React.createElement("button", {
    className: "sort-btn " + (corpusTextMode === "kjv" ? "on" : ""),
    onClick: () => setCorpusTextMode("kjv")
  }, "KJV")))), loading || aiLoading ? /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "center",
      padding: "60px 20px",
      color: "var(--ink-3)",
      fontSize: "14px"
    }
  }, "Searching\u2026") : /*#__PURE__*/React.createElement(CorpusResults, {
    allResults: corpusFilteredResults,
    primaryStrongs: primaryStrongs,
    citedStrongs: citedStrongsApp,
    showAll: showAllAi,
    onWordClick: e => {
      setActiveEntry(e);
      setEntryView("search");
    },
    onReadInContext: handleReadInContext,
    corpusSort: corpusSort,
    textMode: corpusTextMode
  })), /*#__PURE__*/React.createElement("footer", {
    className: "foot"
  }, /*#__PURE__*/React.createElement("span", null, "Lexica \xB7 Greek Septuagint (LXX) \xB7 Apostolic Bible Polyglot Interlinear \xB7 Strong's Greek"))))), showWord && !isMobile && /*#__PURE__*/React.createElement(DetailPanel, {
    entry: activeEntry,
    isMobile: false,
    onClose: () => setActiveEntry(null),
    occurrences: countMap[activeEntry.strongs_raw] || 0,
    totalResults: allResults.length,
    onNavigateToLexicon: handleNavigateToLexicon,
    onReadInContext: handleReadInContext,
    onOpenStudyName: handleOpenStudyName,
    overviewBack: mainView === "library",
    backLabel: libCrossRef ? "Cross-references" : libDetailBase === "intro" ? "Intro" : "Overview"
  }), showWord && isMobile && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "sheet-scrim",
    onClick: () => setActiveEntry(null)
  }), /*#__PURE__*/React.createElement(DetailPanel, {
    entry: activeEntry,
    isMobile: true,
    onClose: () => setActiveEntry(null),
    occurrences: countMap[activeEntry.strongs_raw] || 0,
    totalResults: allResults.length,
    onNavigateToLexicon: handleNavigateToLexicon,
    onReadInContext: handleReadInContext,
    onOpenStudyName: handleOpenStudyName
  })), showNote && /*#__PURE__*/React.createElement(NotesPanel, {
    noteId: activeNote,
    isMobile: isMobile,
    onClose: () => setActiveNote(null)
  }), showXref && !isMobile && !showWord && !showNote && /*#__PURE__*/React.createElement(CrossRefPanel, {
    source: libCrossRef,
    translation: libTranslation === "kjv" ? "kjv" : "abp",
    onClose: () => {
      setLibCrossRef(null);
      setLibNav(prev => prev ? {
        ...prev,
        highlight: null
      } : prev);
    },
    onNavigate: (book, chapter, verse) => {
      setMainView("library");
      setLibCrossRef(null);
      setLibNav({
        book,
        chapter,
        scroll: true,
        highlight: verse
      });
    },
    onAiSearch: q => {
      setLibCrossRef(null);
      handleAiSearch(q);
    },
    onOpenStudy: handleOpenStudyName,
    isMobile: false,
    overviewBack: true,
    backLabel: libDetailBase === "intro" ? "Intro" : "Overview"
  }), showXref && isMobile && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "sheet-scrim",
    onClick: () => {
      setLibCrossRef(null);
      setLibNav(prev => prev ? {
        ...prev,
        highlight: null
      } : prev);
    }
  }), /*#__PURE__*/React.createElement(CrossRefPanel, {
    source: libCrossRef,
    translation: libTranslation === "kjv" ? "kjv" : "abp",
    onClose: () => {
      setLibCrossRef(null);
      setLibNav(prev => prev ? {
        ...prev,
        highlight: null
      } : prev);
    },
    onNavigate: (book, chapter, verse) => {
      setMainView("library");
      setLibCrossRef(null);
      setLibNav({
        book,
        chapter,
        scroll: true,
        highlight: verse
      });
    },
    onAiSearch: q => {
      setLibCrossRef(null);
      handleAiSearch(q);
    },
    onOpenStudy: handleOpenStudyName,
    isMobile: true
  })), showTour && /*#__PURE__*/React.createElement(GuidedTour, {
    onDone: handleTourDone
  }), isMobile && /*#__PURE__*/React.createElement("nav", {
    className: "mobile-tabs"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mobile-tab" + (mainView === "library" ? " active" : ""),
    onClick: () => handleNavChange("library")
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3"
  })), "Library"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-tab" + (mainView === "lexicon" ? " active" : ""),
    onClick: () => handleNavChange("lexicon")
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M4 19V6a2 2 0 0 1 2-2h13"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M4 19a2 2 0 0 0 2 2h13V8H6a2 2 0 0 0-2 2"
  })), "Lexicon"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-tab" + (mainView === "search" ? " active" : ""),
    onClick: () => handleNavChange("search")
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "11",
    cy: "11",
    r: "7"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "16.5",
    y1: "16.5",
    x2: "21",
    y2: "21"
  })), "Search"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-tab" + (mainView === "notes" ? " active" : ""),
    onClick: () => handleNavChange("notes")
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M6 3h12v18l-6-4-6 4z"
  })), "Notes"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-tab" + (mainView === "study" ? " active" : ""),
    onClick: () => handleNavChange("study")
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M4 19.5A2.5 2.5 0 0 1 6.5 17H20"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M9 7h7M9 11h7"
  })), "Study"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-tab" + (mainView === "about" ? " active" : ""),
    onClick: () => handleNavChange("about")
  }, /*#__PURE__*/React.createElement("svg", {
    width: "18",
    height: "18",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "10"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "8",
    x2: "12",
    y2: "8.5"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "12",
    x2: "12",
    y2: "16"
  })), "About")), resetToken && /*#__PURE__*/React.createElement(AuthModal, {
    mode: "reset",
    resetToken: resetToken,
    onClose: () => setResetToken(null)
  }));
}
ReactDOM.createRoot(document.getElementById("root")).render(/*#__PURE__*/React.createElement(App, null));
