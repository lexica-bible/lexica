const { useState, useEffect, useMemo, useRef } = React;

// ============================================================
// ICONS
// ============================================================
const I = {
  Search:  (p) => (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>),
  Arrow:   (p) => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 12h14M13 6l6 6-6 6"/></svg>),
  ArrowSm: (p) => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 12h14M13 6l6 6-6 6"/></svg>),
  Chevron: (p) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m6 9 6 6 6-6"/></svg>),
  Left:    (p) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m15 18-6-6 6-6"/></svg>),
  Close:   (p) => (<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M6 6l12 12M6 18 18 6"/></svg>),
  Book:    (p) => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19"/><path d="M19 16H7.5"/></svg>),
  Menu:    (p) => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M4 6h16M4 12h16M4 18h16"/></svg>),
  Card:    (p) => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/></svg>),
  Spark:   (p) => (<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" {...p}><path d="M12 2.4c.3 3.4 1.6 5.3 3.4 6.4 1.1.7 2.6 1 4.9 1.2-2.3.2-3.8.5-4.9 1.2-1.8 1.1-3.1 3-3.4 6.4-.3-3.4-1.6-5.3-3.4-6.4-1.1-.7-2.6-1-4.9-1.2 2.3-.2 3.8-.5 4.9-1.2C10.4 7.7 11.7 5.8 12 2.4Z"/></svg>),
};

// ============================================================
// HEADER
// ============================================================
function Header({ onToggleRail, onToggleDetail }) {
  return (
    <header className="hdr">
      <div className="hdr-inner">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M11 7v6M14 10h-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="brand-text">
            <div className="brand-name">Lexica</div>
            <div className="brand-sub">Greek &amp; Hebrew Word Study</div>
          </div>
        </div>
        <nav className="hdr-nav">
          <a className="hdr-link" href="Library.html">Library</a>
          <a className="hdr-link active" href="#">Word study</a>
          <a className="hdr-link" href="Ask the Corpus.html">Ask the corpus</a>
          <a className="hdr-link" href="#">Notes</a>
          <a className="hdr-link" href="#">About</a>
        </nav>
        <div className="hdr-right">
          <button className="hdr-icon-btn pane-toggle" onClick={onToggleRail} aria-label="Distribution"><I.Menu/></button>
          <button className="hdr-icon-btn pane-toggle" onClick={onToggleDetail} aria-label="Word detail"><I.Card/></button>
          <div className="hdr-avatar">JM</div>
        </div>
      </div>
    </header>
  );
}

// ============================================================
// VERSE RENDERING (shared markup)
// ============================================================
function parseVerse(str) {
  const out = []; const re = /(\[)|(\])|\^(\d+)|\*([^*]+)\*|\{([^}]+)\}/g;
  let last = 0, m;
  while ((m = re.exec(str)) !== null) {
    if (m.index > last) out.push({ t: "text", v: str.slice(last, m.index) });
    if (m[1]) out.push({ t: "open" });
    else if (m[2]) out.push({ t: "close" });
    else if (m[3]) out.push({ t: "ord", n: m[3] });
    else if (m[4]) out.push({ t: "it", v: m[4] });
    else if (m[5]) { const p = m[5].split("|"); out.push({ t: "word", v: p[0], s: p[1] }); }
    last = re.lastIndex;
  }
  if (last < str.length) out.push({ t: "text", v: str.slice(last) });
  return out;
}
function highlightGloss(text, words) {
  if (!words || !words.length) return text;
  const esc = words.filter((w) => w && w.length > 2).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  if (!esc.length) return text;
  const re = new RegExp("\\b(" + esc.join("|") + ")\\b", "gi");
  const out = []; let last = 0, m, k = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index));
    out.push(<mark key={k++} className="w-hit">{m[0]}</mark>);
    last = re.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}
function AbpClean({ abp, targets, onPick }) {
  return parseVerse(abp).map((tk, i) => {
    if (tk.t === "text") return <span key={i}>{tk.v}</span>;
    if (tk.t === "it") return <span key={i}>{tk.v}</span>;
    if (tk.t === "word") {
      const hit = targets && targets.includes(tk.s);
      return <button key={i} className={"wv" + (hit ? " w-hit" : "")} onClick={() => onPick(tk.s)}>{tk.v}</button>;
    }
    return null;
  });
}
function VerseRow({ id, edition, targets, glossWords, onPick }) {
  const vs = VERSES[id];
  if (!vs) return null;
  return (
    <div className="vrow" data-vid={id}>
      <span className="vrow-ref">{vs.ab} {vs.ch}:{vs.v}</span>
      <span className="vrow-text">
        {edition === "kjv" ? highlightGloss(vs.kjv, glossWords) : <AbpClean abp={vs.abp} targets={targets} onPick={onPick}/>}
      </span>
    </div>
  );
}

// ============================================================
// LEFT — DISTRIBUTION-BY-BOOK RAIL  (mirrors Library canon nav)
// ============================================================
function BookRail({ lex, bookFilter, onSelect, hiddenCls = "" }) {
  if (!lex) {
    return <aside className={"brail " + hiddenCls}><div className="brail-empty">Distribution appears here once a word is selected.</div></aside>;
  }
  const sorted = [...lex.distribution].sort((a, b) => b[1] - a[1]);
  const max = sorted[0][1];
  const total = lex.occ;
  return (
    <aside className={"brail " + hiddenCls}>
      <div className="brail-top">
        <div className="brail-eyebrow">Distribution by book</div>
        <div className="brail-sub"><span className="brail-gk">{lex.word}</span> · {lex.distribution.length} books</div>
      </div>
      <div className="brail-scroll">
        <button className={"brow brow-all " + (!bookFilter ? "on" : "")} onClick={() => onSelect(null)}>
          <span className="brow-name">All books</span>
          <span className="brow-n">{total}</span>
        </button>
        {sorted.map(([book, n], i) => (
          <button key={i} className={"brow " + (bookFilter === book ? "on" : "")} onClick={() => onSelect(book)}>
            <span className="brow-name">{book}</span>
            <span className="brow-bar"><span className={"brow-fill " + (TESTAMENT(book) === "OT" ? "ot" : "")} style={{ width: Math.max(7, (n / max) * 100) + "%" }}></span></span>
            <span className="brow-n">{n}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}

// ============================================================
// RIGHT — WORD DETAIL  (matches Library detail card)
// ============================================================
function WordDetail({ lex, onPick, onOverview, hiddenCls = "" }) {
  const [lsjFull, setLsjFull] = useState(false);
  useEffect(() => { setLsjFull(false); }, [lex && lex.strongs]);
  if (!lex) {
    return (
      <aside className={"wd " + hiddenCls}>
        <div className="empty-pane">
          <div className="empty-mark"><I.Book width="32" height="32"/></div>
          <div className="empty-t">No word selected</div>
          <div className="empty-s">Search a Greek or Hebrew word, a Strong's number, or tap any lemma in a passage to study it here.</div>
        </div>
      </aside>
    );
  }
  const isHeb = lex.script === "hebrew";
  const gloss = lex.abp[0] ? lex.abp[0][0] : "";
  return (
    <aside className={"wd " + hiddenCls}>
      <div className="wd-head">
        <span className="wd-strongs">{lex.strongs}</span>
        <button className="wd-overview" onClick={onOverview}><I.Left/> Overview</button>
      </div>
      <div className="wd-body">
        <div className="wd-hero">
          <div className={"wd-greek " + (isHeb ? "heb" : "")}>{lex.word}</div>
          <div className="wd-sub"><span className="wd-tr">{lex.translit}</span> · <span className="wd-gloss">{gloss}</span></div>
          <div className="wd-morph">{lex.morph} · {lex.type}</div>
          <a className="wd-askai" href={"Ask the Corpus.html?w=" + lex.strongs + "&tr=" + encodeURIComponent(lex.translit) + "&gk=" + encodeURIComponent(lex.word)}>
            <I.Spark/> Ask AI about <span className={"wd-askai-w " + (isHeb ? "heb" : "")}>{lex.word}</span> <I.ArrowSm/>
          </a>
        </div>

        <div className="wd-sec">
          <div className="wd-sec-h"><span className="wd-sec-t">Liddell-Scott-Jones</span><span className="wd-badge">LSJ</span></div>
          <p className="lsj">{lsjFull ? lex.lsjFull : lex.lsjShort}</p>
          <button className="lsj-toggle" onClick={() => setLsjFull(!lsjFull)}>{lsjFull ? "Show less" : "Full entry"} <I.Chevron style={{ transform: lsjFull ? "rotate(180deg)" : "none" }}/></button>
        </div>

        <div className="wd-sec">
          <div className="wd-sec-h"><span className="wd-sec-t">ABP renders as</span><span className="wd-sec-meta">{lex.abp.length} senses</span></div>
          <div className="senses">
            {lex.abp.map((s, i) => (<span key={i} className={"sense " + (i === 0 ? "lead" : "")}><span className="sense-w">{s[0]}</span><span className="sense-n">{s[1]}</span></span>))}
          </div>
        </div>

        <div className="wd-sec">
          <div className="wd-sec-h"><span className="wd-sec-t">KJV renders as</span><span className="wd-sec-meta">{lex.kjv.length} senses</span></div>
          <div className="senses">
            {lex.kjv.map((s, i) => (<span key={i} className={"sense " + (i === 0 ? "lead" : "")}><span className="sense-w">{s[0]}</span><span className="sense-n">{s[1]}</span></span>))}
          </div>
        </div>

        <div className="wd-sec">
          <div className="wd-sec-h"><span className="wd-sec-t">Derivation</span></div>
          <p className="root-note">{lex.root}</p>
        </div>

        <div className="wd-sec last">
          <div className="wd-sec-h"><span className="wd-sec-t">Cognates &amp; related lemmas</span></div>
          <div className="related">
            {lex.related.map((r, i) => (
              <button key={i} className="rel" onClick={() => LEMMAS[r.s] && onPick(r.s)}>
                <span className="rel-gk">{r.word}</span>
                <span className="rel-tr">{r.translit}</span>
                <span className="rel-gloss">{r.gloss} <span className="rel-s">{r.s}</span></span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}

// ============================================================
// CENTER — SEARCH + OCCURRENCES
// ============================================================
function SearchBar({ value, setValue, onSubmit }) {
  return (
    <div className="searchbar">
      <div className="searchbar-in">
        <div className="search-field">
          <I.Search className="search-i"/>
          <input className="search-input" value={value} onChange={(e) => setValue(e.target.value)} onKeyDown={(e) => e.key === "Enter" && onSubmit()} placeholder="A word, transliteration, or Strong's №…"/>
          <button className="search-go" onClick={onSubmit} aria-label="Search"><I.Arrow/></button>
        </div>
      </div>
    </div>
  );
}

function GlossList({ label, matches, onPick }) {
  return (
    <>
      <div className="occ-head">
        <span className="occ-count">{matches.length}</span>
        <span className="occ-label">words rendered “{label}”</span>
      </div>
      <div className="wordlist">
        {matches.map((s) => {
          const t = LEMMAS[s]; if (!t) return null;
          return (
            <button key={s} className="wl-row" onClick={() => onPick(s)}>
              <span className="wl-s">{t.strongs}</span>
              <span className="wl-main">
                <span className="wl-top"><span className="wl-gk">{t.word}</span><span className="wl-tr">{t.translit}</span></span>
                <span className="wl-renders">
                  <span className="wl-rend"><span className="wl-rend-k">ABP</span> {t.abp.map((a) => a[0]).join(", ")}</span>
                  <span className="wl-rend"><span className="wl-rend-k">KJV</span> {t.kjv.map((a) => a[0]).join(", ")}</span>
                </span>
              </span>
              <span className="wl-occ">{t.occ} <I.ArrowSm/></span>
            </button>
          );
        })}
      </div>
    </>
  );
}

// ============================================================
// APP
// ============================================================
function findLemmas(q) {
  const t = q.trim().toLowerCase();
  if (!t) return [];
  const up = t.toUpperCase().replace(/\s+/g, "");
  if (LEMMAS[up]) return [up];
  return Object.keys(LEMMAS).filter((s) => {
    const l = LEMMAS[s];
    return l.translit.toLowerCase().includes(t) || l.word.includes(q.trim()) || l.strongs.toLowerCase().includes(t);
  });
}

function App() {
  const [query, setQuery] = useState("");
  const [view, setView] = useState("lemma");        // "lemma" | "glosslist" | "overview"
  const [activeStrong, setActiveStrong] = useState("G4151");
  const [edition, setEdition] = useState("kjv");
  const [testament, setTestament] = useState("all");
  const [bookFilter, setBookFilter] = useState(null);
  const [glossMatches, setGlossMatches] = useState([]);
  const [glossLabel, setGlossLabel] = useState("");

  const [railOpen, setRailOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [vw, setVw] = useState(typeof window !== "undefined" ? window.innerWidth : 1400);
  useEffect(() => { const r = () => setVw(window.innerWidth); window.addEventListener("resize", r); return () => window.removeEventListener("resize", r); }, []);

  const lex = (view === "overview" || view === "glosslist") ? null : LEMMAS[activeStrong];

  // deep-link: ?w=G4151 from the corpus tab
  useEffect(() => {
    const w = new URLSearchParams(window.location.search).get("w");
    if (w && LEMMAS[w]) { setActiveStrong(w); setView("lemma"); }
  }, []);

  const studyLemma = (s) => {
    if (!LEMMAS[s]) return;
    setActiveStrong(s); setView("lemma"); setBookFilter(null);
    if (vw <= 1040) setDetailOpen(true);
  };

  const onSubmit = (term) => {
    const t = (typeof term === "string" ? term : query).trim();
    if (!t) return;
    setQuery(t);
    const gloss = t.toLowerCase();
    const ls = findLemmas(t);
    if (GLOSS_INDEX[gloss] && (ls.length !== 1)) {
      setGlossMatches(GLOSS_INDEX[gloss].filter((s) => LEMMAS[s])); setGlossLabel(t); setView("glosslist"); return;
    }
    if (ls.length === 1) { studyLemma(ls[0]); return; }
    if (ls.length > 1) { setGlossMatches(ls); setGlossLabel(t); setView("glosslist"); return; }
    if (GLOSS_INDEX[gloss]) { setGlossMatches(GLOSS_INDEX[gloss].filter((s) => LEMMAS[s])); setGlossLabel(t); setView("glosslist"); return; }
  };

  const targets = lex ? [lex.strongs] : [];
  const glossWords = useMemo(() => {
    if (!lex) return [];
    const ws = new Set();
    (lex.kjv || []).slice(0, 3).forEach((g) => ws.add(g[0]));
    (lex.abp || []).slice(0, 3).forEach((g) => ws.add(g[0]));
    return [...ws];
  }, [lex]);

  // occurrences filtered by testament + book
  const occ = useMemo(() => {
    if (!lex) return [];
    return lex.verses.filter((id) => {
      const v = VERSES[id]; if (!v) return false;
      if (testament !== "all" && TESTAMENT(v.book) !== testament.toUpperCase()) return false;
      if (bookFilter && v.book !== bookFilter) return false;
      return true;
    });
  }, [lex, testament, bookFilter]);

  const bookCount = useMemo(() => {
    if (!lex || !bookFilter) return null;
    const d = lex.distribution.find((d) => d[0] === bookFilter);
    return d ? d[1] : null;
  }, [lex, bookFilter]);

  const narrowDetail = vw <= 1040;
  const narrowRail = vw <= 760;
  const shellCls = "ws" + (narrowRail ? " rail-collapsed" : "") + (narrowDetail ? " detail-collapsed" : "");

  return (
    <div className="app">
      <Header onToggleRail={() => setRailOpen(!railOpen)} onToggleDetail={() => setDetailOpen(!detailOpen)}/>
      <div className={shellCls}>
        {/* LEFT — distribution rail */}
        {narrowRail && railOpen && <div className="rail-scrim" onClick={() => setRailOpen(false)}></div>}
        <BookRail lex={lex} bookFilter={bookFilter} onSelect={(b) => { setBookFilter(b); if (narrowRail) setRailOpen(false); }}
          hiddenCls={narrowRail && !railOpen ? "hidden" : ""}/>

        {/* CENTER — search + occurrences */}
        <main className="center">
          <SearchBar value={query} setValue={setQuery} onSubmit={onSubmit}/>
          <div className="results-scroll">
            <div className="results-col">
              {view === "glosslist" ? (
                <GlossList label={glossLabel} matches={glossMatches} onPick={studyLemma}/>
              ) : lex ? (
                <>
                  {bookFilter && (
                    <div className="occ-filter">
                      <span>Filtered to <b>{bookFilter}</b> · {bookCount} occurrence{bookCount === 1 ? "" : "s"}</span>
                      <button className="occ-reset" onClick={() => setBookFilter(null)}>Clear</button>
                    </div>
                  )}

                  <div className="filters">
                    <div className="tgroup">
                      {[["all", "All"], ["ot", "OT"], ["nt", "NT"]].map(([k, l]) => (
                        <button key={k} className={"tg " + (testament === k ? "on" : "")} onClick={() => setTestament(k)}>{l}</button>
                      ))}
                    </div>
                    <span className="filters-sep"></span>
                    <div className="tgroup">
                      {[["abp", "ABP"], ["kjv", "KJV"]].map(([k, l]) => (
                        <button key={k} className={"tg " + (edition === k ? "on" : "")} onClick={() => setEdition(k)}>{l}</button>
                      ))}
                    </div>
                  </div>

                  {occ.length ? (
                    <div className="vlist">
                      {occ.map((id) => (<VerseRow key={id} id={id} edition={edition} targets={targets} glossWords={glossWords} onPick={studyLemma}/>))}
                    </div>
                  ) : (
                    <div className="occ-empty">
                      {bookFilter
                        ? `${bookCount} occurrence${bookCount === 1 ? "" : "s"} recorded in ${bookFilter} — sample passages not loaded in this prototype.`
                        : "No passages match the current filters."}
                    </div>
                  )}
                </>
              ) : (
                <div className="occ-welcome">
                  <div className="occ-welcome-t">Greek &amp; Hebrew word study</div>
                  <div className="occ-welcome-s">Search a word, transliteration, or Strong's number to study its senses, derivation, and every place it occurs.</div>
                  <div className="occ-welcome-chips">
                    {["πνεῦμα", "pistis", "G26", "spirit"].map((q) => (
                      <button key={q} className="welcome-chip" onClick={() => onSubmit(q)}>{q}</button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>

        {/* RIGHT — word detail */}
        {narrowDetail && detailOpen && <div className="wd-scrim" onClick={() => setDetailOpen(false)}></div>}
        <WordDetail lex={lex} onPick={studyLemma} onOverview={() => { setView("overview"); }}
          hiddenCls={narrowDetail && !detailOpen ? "hidden" : ""}/>
      </div>
    </div>
  );
}

// welcome chips need onSubmit after query set — wire via effect-free direct call
ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
