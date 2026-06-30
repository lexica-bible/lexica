const { useState, useEffect, useMemo, useRef } = React;

// ============================================================
// ICONS  (WMI — kept unique; shares global scope with the data file)
// ============================================================
const WMI = {
  Search:  (p) => (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>),
  Arrow:   (p) => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 12h14M13 6l6 6-6 6"/></svg>),
  ArrowSm: (p) => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 12h14M13 6l6 6-6 6"/></svg>),
  Chevron: (p) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m6 9 6 6 6-6"/></svg>),
  ChevR:   (p) => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m9 6 6 6-6 6"/></svg>),
  Close:   (p) => (<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M6 6l12 12M6 18 18 6"/></svg>),
  Book:    (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19"/><path d="M19 16H7.5"/></svg>),
  Card:    (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/></svg>),
  Sliders: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 8h9M19 8h0M5 16h0M10 16h9"/><circle cx="16" cy="8" r="2.4"/><circle cx="7.5" cy="16" r="2.4"/></svg>),
  Menu:    (p) => (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" {...p}><path d="M4 7h16M4 12h16M4 17h16"/></svg>),
  Spark:   (p) => (<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" {...p}><path d="M12 2.4c.3 3.4 1.6 5.3 3.4 6.4 1.1.7 2.6 1 4.9 1.2-2.3.2-3.8.5-4.9 1.2-1.8 1.1-3.1 3-3.4 6.4-.3-3.4-1.6-5.3-3.4-6.4-1.1-.7-2.6-1-4.9-1.2 2.3-.2 3.8-.5 4.9-1.2C10.4 7.7 11.7 5.8 12 2.4Z"/></svg>),
  // module-nav glyphs
  ModLib:   (p) => (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M12 6.6C10.3 5.6 7.9 5 5.6 5 4 5 2.5 5.3 2.5 5.3v12.3s1.5-.3 3.1-.3c2.3 0 4.7.6 6.4 1.6 1.7-1 4.1-1.6 6.4-1.6 1.6 0 3.1.3 3.1.3V5.3S20 5 18.4 5c-2.3 0-4.7.6-6.4 1.6z"/><path d="M12 6.6v11"/></svg>),
  ModWord:  (p) => (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M6.5 4.5A2.5 2.5 0 0 1 9 2H19v17H9a2.5 2.5 0 0 0 0 5H19"/><path d="M12.5 8v5M15 10.5h-5"/></svg>),
  ModAsk:   (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="currentColor" {...p}><path d="M12 2.6c.28 3.2 1.5 5 3.2 6 1 .65 2.45.95 4.6 1.15-2.15.2-3.6.5-4.6 1.15-1.7 1-2.92 2.8-3.2 6-.28-3.2-1.5-5-3.2-6-1-.65-2.45-.95-4.6-1.15 2.15-.2 3.6-.5 4.6-1.15C10.5 7.6 11.72 5.8 12 2.6Z"/></svg>),
  ModNotes: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 3.6h9l5 5v11.8H5z"/><path d="M14 3.6V9h5M8.5 13h7M8.5 16.4h5"/></svg>),
  ModStudy: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="6" cy="6" r="2.4"/><circle cx="18" cy="9" r="2.4"/><circle cx="9" cy="18" r="2.4"/><path d="M8.1 6.9l7.8 1.4M9.2 15.7 8.6 8.4"/></svg>),
  ModAbout: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="12" r="9.2"/><path d="M12 11v5M12 7.6h0"/></svg>),
};

// ============================================================
// VERSE RENDERING  (shared markup vocabulary)
// ============================================================
function wmParseVerse(str) {
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
function wmHighlight(text, words) {
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
function AbpCleanM({ abp, targets, onPick }) {
  return wmParseVerse(abp).map((tk, i) => {
    if (tk.t === "text") return <span key={i}>{tk.v}</span>;
    if (tk.t === "it") return <span key={i}>{tk.v}</span>;
    if (tk.t === "word") {
      const hit = targets && targets.includes(tk.s);
      return <button key={i} className={"wv" + (hit ? " w-hit" : "")} onClick={() => onPick(tk.s)}>{tk.v}</button>;
    }
    return null;
  });
}
function VerseRowM({ id, edition, targets, glossWords, onPick }) {
  const vs = VERSES[id];
  if (!vs) return null;
  return (
    <div className="vrow" data-vid={id}>
      <span className="vrow-ref">{vs.ab} {vs.ch}:{vs.v}</span>
      <span className="vrow-text">
        {edition === "kjv" ? wmHighlight(vs.kjv, glossWords) : <AbpCleanM abp={vs.abp} targets={targets} onPick={onPick}/>}
      </span>
    </div>
  );
}

function wmFindLemmas(q) {
  const t = q.trim().toLowerCase();
  if (!t) return [];
  const up = t.toUpperCase().replace(/\s+/g, "");
  if (LEMMAS[up]) return [up];
  return Object.keys(LEMMAS).filter((s) => {
    const l = LEMMAS[s];
    return l.translit.toLowerCase().includes(t) || l.word.includes(q.trim()) || l.strongs.toLowerCase().includes(t);
  });
}

// ============================================================
// BOTTOM SHEET  (rises from bottom, drag the grab-zone down to dismiss)
// ============================================================
function Sheet({ title, onClose, tall, children }) {
  const [dy, setDy] = useState(0);
  const [dragging, setDragging] = useState(false);
  const drag = useRef({ active: false, startY: 0 });

  const grab = {
    onPointerDown: (e) => { drag.current = { active: true, startY: e.clientY }; setDragging(true); try { e.currentTarget.setPointerCapture(e.pointerId); } catch (_) {} },
    onPointerMove: (e) => { if (!drag.current.active) return; setDy(Math.max(0, e.clientY - drag.current.startY)); },
    onPointerUp: () => {
      if (!drag.current.active) return;
      drag.current.active = false; setDragging(false);
      setDy((d) => { if (d > 110) { onClose(); return 0; } return 0; });
    },
  };

  return (
    <>
      <div className="wm-scrim" onClick={onClose}></div>
      <div className={"wm-sheet" + (tall ? " tall" : "")}
        style={{ transform: `translateY(${dy}px)`, transition: dragging ? "none" : "transform 0.26s cubic-bezier(0.2,0.8,0.2,1)" }}>
        <div className="wm-grab" {...grab}>
          <div className="wm-handle" aria-hidden="true"></div>
          <div className="wm-sheet-head">
            <span className="wm-sheet-title">{title}</span>
            <button className="wm-sheet-x" onClick={onClose} aria-label="Close"><WMI.Close/></button>
          </div>
        </div>
        <div className="wm-sheet-body">{children}</div>
      </div>
    </>
  );
}

// ============================================================
// WORD CARD  (the desktop right hero panel, as sheet content)
// ============================================================
function CardBody({ lex, onPick }) {
  const [lsjFull, setLsjFull] = useState(false);
  useEffect(() => { setLsjFull(false); }, [lex && lex.strongs]);
  if (!lex) {
    return (
      <div className="empty-pane">
        <div className="empty-mark"><WMI.Book width="32" height="32"/></div>
        <div className="empty-t">No word selected</div>
        <div className="empty-s">Search a Greek or Hebrew word, a Strong's number, or tap any lemma in a passage to study it here.</div>
      </div>
    );
  }
  const isHeb = lex.script === "hebrew";
  const gloss = lex.abp[0] ? lex.abp[0][0] : "";
  return (
    <div className="wd-body wm-card">
      <div className="wd-hero">
        <div className={"wd-greek " + (isHeb ? "heb" : "")}>{lex.word}</div>
        <div className="wd-sub"><span className="wd-tr">{lex.translit}</span> · <span className="wd-gloss">{gloss}</span></div>
        <div className="wd-morph">{lex.morph} · {lex.type} · <span className="wm-card-s">{lex.strongs}</span></div>
        <a className="wd-askai" href={"Ask the Corpus.html?w=" + lex.strongs + "&tr=" + encodeURIComponent(lex.translit) + "&gk=" + encodeURIComponent(lex.word)}>
          <WMI.Spark/> Ask AI about <span className={"wd-askai-w " + (isHeb ? "heb" : "")}>{lex.word}</span> <WMI.ArrowSm/>
        </a>
      </div>

      <div className="wd-sec">
        <div className="wd-sec-h"><span className="wd-sec-t">Liddell-Scott-Jones</span><span className="wd-badge">LSJ</span></div>
        <p className="lsj">{lsjFull ? lex.lsjFull : lex.lsjShort}</p>
        <button className="lsj-toggle" onClick={() => setLsjFull(!lsjFull)}>{lsjFull ? "Show less" : "Full entry"} <WMI.Chevron style={{ transform: lsjFull ? "rotate(180deg)" : "none" }}/></button>
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
  );
}

// ============================================================
// DISTRIBUTION  (the desktop left rail, as sheet content)
// ============================================================
function RailBody({ lex, bookFilter, onSelect }) {
  if (!lex) return <div className="brail-empty">Distribution appears here once a word is selected.</div>;
  const sorted = [...lex.distribution].sort((a, b) => b[1] - a[1]);
  const max = sorted[0][1];
  return (
    <div className="wm-rail">
      <button className={"brow brow-all " + (!bookFilter ? "on" : "")} onClick={() => onSelect(null)}>
        <span className="brow-name">All books</span>
        <span className="brow-n">{lex.occ}</span>
      </button>
      {sorted.map(([book, n], i) => (
        <button key={i} className={"brow " + (bookFilter === book ? "on" : "")} onClick={() => onSelect(book)}>
          <span className="brow-name">{book}</span>
          <span className="brow-bar"><span className={"brow-fill " + (TESTAMENT(book) === "OT" ? "ot" : "")} style={{ width: Math.max(7, (n / max) * 100) + "%" }}></span></span>
          <span className="brow-n">{n}</span>
        </button>
      ))}
    </div>
  );
}

// ============================================================
// VIEWS  (edition + testament + jumps)
// ============================================================
function ViewsBody({ edition, setEdition, testament, setTestament, lex }) {
  return (
    <>
      <div className="mode-sec">
        <div className="mode-lbl">Edition</div>
        <div className="mseg">
          {[["abp", "ABP"], ["kjv", "KJV"]].map(([k, l]) => (
            <button key={k} className={"mseg-b " + (edition === k ? "on" : "")} onClick={() => setEdition(k)}>{l}</button>
          ))}
        </div>
      </div>
      <div className="mode-sec">
        <div className="mode-lbl">Testament</div>
        <div className="mseg">
          {[["all", "All"], ["ot", "Old"], ["nt", "New"]].map(([k, l]) => (
            <button key={k} className={"mseg-b " + (testament === k ? "on" : "")} onClick={() => setTestament(k)}>{l}</button>
          ))}
        </div>
      </div>
      {lex && (
        <div className="mode-sec">
          <div className="mode-lbl">Go deeper</div>
          <a className="wm-jump" href={"Ask the Corpus.html?w=" + lex.strongs + "&tr=" + encodeURIComponent(lex.translit) + "&gk=" + encodeURIComponent(lex.word)}>
            <WMI.Spark/> Ask the corpus about <span className={"wm-jump-w " + (lex.script === "hebrew" ? "heb" : "")}>{lex.word}</span> <WMI.ArrowSm/>
          </a>
        </div>
      )}
    </>
  );
}

// ============================================================
// NAVY MODULE BAR  (global nav — same tabs as desktop, top of screen)
// ============================================================
const WM_MODULES = [
  ["Library", "Library.html", "lib", (p) => <WMI.ModLib {...p}/>],
  ["Word study", "Word Study.html", "word", (p) => <WMI.ModWord {...p}/>],
  ["Ask the corpus", "Ask the Corpus.html", "ask", (p) => <WMI.ModAsk {...p}/>],
  ["Notes", "#", "notes", (p) => <WMI.ModNotes {...p}/>],
  ["Study", "Study.html", "study", (p) => <WMI.ModStudy {...p}/>],
  ["About", "#", "about", (p) => <WMI.ModAbout {...p}/>],
];
function NavBar() {
  return (
    <nav className="wm-nav" aria-label="Modules">
      <div className="wm-nav-brand" aria-hidden="true">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
          <path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M11 7v6M14 10h-6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/>
        </svg>
      </div>
      {WM_MODULES.map(([label, href, key, Icon]) => (
        key === "word"
          ? <span key={key} className="wm-navtab on" aria-current="page" title={label}><Icon/></span>
          : <a key={key} className="wm-navtab" href={href} title={label} aria-label={label}><Icon/></a>
      ))}
    </nav>
  );
}

// ============================================================
// SEARCH SHEET  (find a new lemma — invoked from the toolbar)
// ============================================================
function SearchSheet({ query, setQuery, onSubmit, onClose }) {
  const ref = useRef(null);
  useEffect(() => { if (ref.current) ref.current.focus(); }, []);
  return (
    <Sheet title="Search" onClose={onClose}>
      <div className="wm-searchsheet">
        <div className="wm-search">
          <WMI.Search className="wm-search-i"/>
          <input ref={ref} className="wm-search-input" value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { onSubmit(); onClose(); } }}
            placeholder="Word, transliteration, Strong's…" />
          {query && <button className="wm-search-clear" onClick={() => setQuery("")} aria-label="Clear"><WMI.Close/></button>}
        </div>
        <div className="wm-search-hint">Greek, Hebrew, transliteration, an English gloss, or a Strong's number.</div>
        <div className="wm-search-chips">
          {["πνεῦμα", "pistis", "G26", "spirit", "ἀγάπη", "H7307"].map((q) => (
            <button key={q} className="welcome-chip" onClick={() => { onSubmit(q); onClose(); }}>{q}</button>
          ))}
        </div>
      </div>
    </Sheet>
  );
}

// ============================================================
// SENSES PIVOT  (English gloss → several lemmas)
// ============================================================
function SensesBarM({ label, senses, active, onPick }) {
  const [open, setOpen] = useState(true);
  const cur = LEMMAS[active];
  return (
    <div className={"glsenses" + (open ? " open" : "")}>
      <button className="glsenses-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="glsenses-l"><b>{senses.length}</b> rendered “{label}”</span>
        {!open && cur && (
          <span className="glsenses-cur">
            <span className={"glsenses-cur-gk" + (cur.script === "hebrew" ? " heb" : "")}>{cur.word}</span>
            <span className="glsenses-cur-tr">{cur.translit}</span>
          </span>
        )}
        <span className="glsenses-tog">{open ? "Collapse" : "Expand"} <WMI.Chevron/></span>
      </button>
      {open && (
        <div className="glsenses-rows">
          {senses.map((s) => {
            const l = LEMMAS[s]; if (!l) return null;
            return (
              <button key={s} className={"glrow" + (s === active ? " on" : "")} onClick={() => onPick(s)}>
                <span className="glrow-s">{l.strongs}</span>
                <span className="glrow-main">
                  <span className="glrow-top">
                    <span className={"glrow-gk" + (l.script === "hebrew" ? " heb" : "")}>{l.word}</span>
                    <span className="glrow-tr">{l.translit}</span>
                  </span>
                  {l.abp && l.abp.length > 0 && <span className="glrow-rend"><span className="glrow-k">ABP</span><span>{l.abp.map((a) => a[0]).join(", ")}</span></span>}
                  {l.kjv && l.kjv.length > 0 && <span className="glrow-rend"><span className="glrow-k">KJV</span><span>{l.kjv.map((a) => a[0]).join(", ")}</span></span>}
                </span>
                <span className="glrow-occ">{l.occ} <WMI.ArrowSm/></span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============================================================
// APP  (inside the phone screen)
// ============================================================
function WordStudyApp() {
  const [query, setQuery] = useState("");
  const [activeStrong, setActiveStrong] = useState("G4151");
  const [edition, setEdition] = useState("kjv");
  const [testament, setTestament] = useState("all");
  const [bookFilter, setBookFilter] = useState(null);
  const [glossSenses, setGlossSenses] = useState([]);
  const [glossLabel, setGlossLabel] = useState("");
  const [welcome, setWelcome] = useState(false);
  const [sheet, setSheet] = useState(null); // "dist" | "card" | "views" | "nav" | null

  const lex = welcome ? null : LEMMAS[activeStrong];

  useEffect(() => {
    const w = new URLSearchParams(window.location.search).get("w");
    if (w && LEMMAS[w]) { setActiveStrong(w); setWelcome(false); }
  }, []);

  const studyLemma = (s) => {
    if (!LEMMAS[s]) return;
    setActiveStrong(s); setWelcome(false); setBookFilter(null); setGlossSenses([]);
    setSheet(null);
  };
  const pickSense = (s) => { if (!LEMMAS[s]) return; setActiveStrong(s); setWelcome(false); setBookFilter(null); };

  const onSubmit = (term) => {
    const t = (typeof term === "string" ? term : query).trim();
    if (!t) return;
    setQuery(t);
    const gloss = t.toLowerCase();
    const ls = wmFindLemmas(t);
    const glossHit = GLOSS_INDEX[gloss] ? GLOSS_INDEX[gloss].filter((s) => LEMMAS[s]) : [];
    let senses = null;
    if (glossHit.length && ls.length !== 1) senses = glossHit;
    else if (ls.length === 1) { studyLemma(ls[0]); return; }
    else if (ls.length > 1) senses = ls;
    else if (glossHit.length) senses = glossHit;
    if (senses && senses.length) {
      senses = senses.slice().sort((a, b) => (LEMMAS[b].occ || 0) - (LEMMAS[a].occ || 0));
      setGlossLabel(t); setGlossSenses(senses);
      setActiveStrong(senses[0]); setWelcome(false); setBookFilter(null);
    }
  };

  const targets = lex ? [lex.strongs] : [];
  const glossWords = useMemo(() => {
    if (!lex) return [];
    const ws = new Set();
    (lex.kjv || []).slice(0, 3).forEach((g) => ws.add(g[0]));
    (lex.abp || []).slice(0, 3).forEach((g) => ws.add(g[0]));
    return [...ws];
  }, [lex]);

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

  const gloss = lex && lex.abp[0] ? lex.abp[0][0] : "";
  const isHeb = lex && lex.script === "hebrew";
  const tLabel = testament === "all" ? "All" : testament === "ot" ? "OT" : "NT";

  return (
    <div className="wm">
      {/* TOP — navy module bar (same nav as desktop) */}
      <NavBar/>

      {/* CONTEXT — current lemma, taps open the word card */}
      {lex && (
        <button className="wm-ctx" onClick={() => setSheet("card")} aria-label="Open word card">
          <span className={"wm-ctx-gk" + (isHeb ? " heb" : "")}>{lex.word}</span>
          <span className="wm-ctx-meta">
            <span className="wm-ctx-tr">{lex.translit}</span>
            <span className="wm-ctx-dot">·</span>
            <span className="wm-ctx-gloss">{gloss}</span>
          </span>
          <span className="wm-ctx-go"><WMI.ChevR/></span>
        </button>
      )}

      {/* MAIN — senses pivot + occurrences (the reading area) */}
      <div className="wm-main">
        {lex ? (
          <>
            {glossSenses.length > 1 && glossSenses.includes(activeStrong) && (
              <SensesBarM label={glossLabel} senses={glossSenses} active={activeStrong} onPick={pickSense}/>
            )}

            <div className="wm-occhead">
              <span className="wm-occ-count">{occ.length ? occ.length : (bookFilter ? bookCount : lex.occ)}</span>
              <span className="wm-occ-lbl">{bookFilter ? "in " + bookFilter : "occurrences"}</span>
              <span className="wm-occ-meta">{tLabel} · {edition.toUpperCase()}</span>
            </div>
            {bookFilter && (
              <div className="wm-filterchip">
                <span>Filtered to <b>{bookFilter}</b></span>
                <button onClick={() => setBookFilter(null)}>Clear</button>
              </div>
            )}

            {occ.length ? (
              <div className="vlist">
                {occ.map((id) => (<VerseRowM key={id} id={id} edition={edition} targets={targets} glossWords={glossWords} onPick={studyLemma}/>))}
              </div>
            ) : (
              <div className="occ-empty">
                {bookFilter
                  ? `${bookCount} occurrence${bookCount === 1 ? "" : "s"} recorded in ${bookFilter} — sample passages not loaded in this prototype.`
                  : "No passages match the current view."}
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

      {/* BOTTOM — per-screen working toolbar */}
      <nav className="wm-tabs" aria-label="Word study tools">
        <button className={"wm-tab" + (sheet === "search" ? " on" : "")} onClick={() => setSheet("search")}>
          <WMI.Search/><span className="wm-tab-l">Search</span>
        </button>
        <button className={"wm-tab" + (sheet === "dist" ? " on" : "")} onClick={() => setSheet("dist")}>
          <WMI.Book/><span className="wm-tab-l">Distribution</span>
        </button>
        <button className={"wm-tab" + (sheet === "card" ? " on" : "")} onClick={() => setSheet("card")}>
          <WMI.Card/><span className="wm-tab-l">Word card</span>
        </button>
        <button className={"wm-tab" + (sheet === "views" ? " on" : "")} onClick={() => setSheet("views")}>
          <WMI.Sliders/><span className="wm-tab-l">Views</span>
        </button>
      </nav>

      {/* SHEETS */}
      {sheet === "dist" && (
        <Sheet tall title={lex ? "Distribution · " + lex.translit : "Distribution"} onClose={() => setSheet(null)}>
          <RailBody lex={lex} bookFilter={bookFilter} onSelect={(b) => { setBookFilter(b); setSheet(null); }}/>
        </Sheet>
      )}
      {sheet === "card" && (
        <Sheet tall title="Word card" onClose={() => setSheet(null)}>
          <CardBody lex={lex} onPick={studyLemma}/>
        </Sheet>
      )}
      {sheet === "views" && (
        <Sheet title="Views" onClose={() => setSheet(null)}>
          <ViewsBody edition={edition} setEdition={setEdition} testament={testament} setTestament={setTestament} lex={lex}/>
        </Sheet>
      )}
      {sheet === "search" && (
        <SearchSheet query={query} setQuery={setQuery} onSubmit={onSubmit} onClose={() => setSheet(null)}/>
      )}
    </div>
  );
}

// ============================================================
// STAGE — scale the phone to fit any viewport
// ============================================================
function Stage() {
  const W = 412, H = 892;
  const wrapRef = useRef(null);
  const [scale, setScale] = useState(1);
  useEffect(() => {
    const fit = () => {
      const vv = window.visualViewport;
      const aw = Math.min(window.innerWidth, document.documentElement.clientWidth || Infinity, (vv && vv.width) || Infinity);
      const ah = Math.min(window.innerHeight, document.documentElement.clientHeight || Infinity, (vv && vv.height) || Infinity);
      const s = Math.min((aw - 20) / W, (ah - 20) / H, 1);
      setScale(s > 0 ? s : 1);
    };
    fit();
    const t1 = setTimeout(fit, 120);
    const t2 = setTimeout(fit, 400);
    window.addEventListener("resize", fit);
    if (window.visualViewport) window.visualViewport.addEventListener("resize", fit);
    return () => { clearTimeout(t1); clearTimeout(t2); window.removeEventListener("resize", fit); if (window.visualViewport) window.visualViewport.removeEventListener("resize", fit); };
  }, []);
  return (
    <div className="stage" ref={wrapRef}>
      <div className="stage-scale" style={{ transform: `scale(${scale})` }}>
        <AndroidDevice width={W} height={H}>
          <WordStudyApp/>
        </AndroidDevice>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<Stage/>);
