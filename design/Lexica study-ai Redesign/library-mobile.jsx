const { useState, useEffect, useMemo, useRef } = React;

// ============================================================
// ICONS
// ============================================================
const I = {
  Menu: (p) => (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" {...p}><path d="M4 7h16M4 12h16M4 17h16"/></svg>),
  Modes: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" {...p}><path d="M5 8h9M19 8h0M5 16h0M10 16h9"/><circle cx="16" cy="8" r="2.4"/><circle cx="7.5" cy="16" r="2.4"/></svg>),
  Chevron: (p) => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m9 6 6 6-6 6"/></svg>),
  ChevDown: (p) => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m6 9 6 6 6-6"/></svg>),
  Back: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M19 12H5M11 6l-6 6 6 6"/></svg>),
  Close: (p) => (<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M6 6l12 12M6 18 18 6"/></svg>),
  Arrow: (p) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 12h14M13 6l6 6-6 6"/></svg>),
  Plus: (p) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" {...p}><path d="M12 5v14M5 12h14"/></svg>),
  Minus: (p) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" {...p}><path d="M5 12h14"/></svg>),
  Pin: (p) => (<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" {...p}><path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>),
  Search: (p) => (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>),
  SearchSm: (p) => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>),
  Book: (p) => (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5a2.5 2.5 0 0 0 0 5H20"/><path d="M20 16H6.5"/></svg>),
  Info: (p) => (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="12" r="9.2"/><path d="M12 11v5M12 7.6h0"/></svg>),
};

// ============================================================
// VERSE RENDERER  (shared markup vocabulary)
// ============================================================
function parseVerse(str) {
  const tokens = [];
  const re = /(\[)|(\])|\^(\d+)|\*([^*]+)\*|\{([^}]+)\}/g;
  let last = 0, m;
  while ((m = re.exec(str)) !== null) {
    if (m.index > last) tokens.push({ t: "text", v: str.slice(last, m.index) });
    if (m[1]) tokens.push({ t: "open" });
    else if (m[2]) tokens.push({ t: "close" });
    else if (m[3]) tokens.push({ t: "ord", n: m[3] });
    else if (m[4]) tokens.push({ t: "it", v: m[4] });
    else if (m[5]) { const p = m[5].split("|"); tokens.push({ t: "word", v: p[0], s: p[1], active: p[2] === "active" }); }
    last = re.lastIndex;
  }
  if (last < str.length) tokens.push({ t: "text", v: str.slice(last) });
  return tokens;
}

function Word({ tok, strongsOn, interlinear, script, activeStrong, onPick }) {
  const lex = WORDS[tok.s];
  const isActive = activeStrong === tok.s;
  const showGreek = script === "greek" && lex && lex.greek;
  const cls = "w" + (strongsOn ? " w-link" : "") + (isActive ? " w-active" : "");
  const handle = () => onPick(tok.s);
  if (interlinear && lex) {
    return (
      <button className={"il " + (isActive ? "il-active" : "")} onClick={handle}>
        <span className="il-gk">{lex.greek}</span>
        <span className="il-tr">{lex.translit}</span>
        <span className="il-en">{tok.v}</span>
      </button>
    );
  }
  return (
    <button className={cls} onClick={handle}>
      {showGreek ? lex.greek : tok.v}
      {strongsOn && tok.s && <sup className="w-s">{tok.s.replace(/^([GH])/, "$1·")}</sup>}
    </button>
  );
}

function Verse({ n, abp, kjv, edition, strongsOn, interlinear, script, activeStrong, onPick }) {
  if (edition === "kjv") {
    return (<p className="verse-line"><span className="vn">{n}</span><span className="vt">{kjv}</span></p>);
  }
  const tokens = parseVerse(abp);
  return (
    <p className={"verse-line" + (interlinear ? " il-line" : "")}>
      <span className="vn">{n}</span>
      <span className="vt">
        {tokens.map((tk, i) => {
          if (tk.t === "text") return <span key={i}>{tk.v}</span>;
          if (tk.t === "it") return <em key={i} className="sup">{tk.v}</em>;
          if (tk.t === "open") return strongsOn ? <span key={i} className="brk">[</span> : null;
          if (tk.t === "close") return strongsOn ? <span key={i} className="brk">]</span> : null;
          if (tk.t === "ord") return strongsOn ? <sup key={i} className="ord">{tk.n}</sup> : null;
          if (tk.t === "word") return <Word key={i} tok={tk} strongsOn={strongsOn} interlinear={interlinear} script={script} activeStrong={activeStrong} onPick={onPick}/>;
          return null;
        })}
      </span>
    </p>
  );
}

// ============================================================
// MINI MAP + WORD-STUDY DETAIL (reused, mobile bottom sheet)
// ============================================================
function MiniMap({ place, label }) {
  return (
    <div className="map">
      <div className="map-terrain"></div>
      <div className="map-grid" aria-hidden="true"></div>
      <div className="map-zoom">
        <button aria-label="Zoom in"><I.Plus/></button>
        <button aria-label="Zoom out"><I.Minus/></button>
      </div>
      {place.labels && place.labels.slice(0, 4).map((l, i) => (<span key={l} className={"map-lbl map-lbl-" + i}>{l}</span>))}
      <div className="map-pin"><I.Pin/></div>
      <div className="map-callout"><span>{label}</span><I.Close/></div>
    </div>
  );
}

function Detail({ strong, refLabel, verseText, onClose, lsjFull, setLsjFull }) {
  const lex = WORDS[strong];
  if (!lex) return null;
  const isPlace = lex.cat === "place";
  return (
    <aside className="detail detail-sheet" role="dialog" aria-label="Word study">
      <div className="sheet-handle" aria-hidden="true"></div>
      <div className="detail-head">
        <div className="detail-head-l">
          <span className="morph">{lex.morph}</span>
          <span className="detail-crumb">{refLabel}</span>
        </div>
        <button className="detail-x" onClick={onClose} aria-label="Close"><I.Close/></button>
      </div>
      <div className="detail-body">
        <h2 className="lemma">{lex.en}</h2>
        <div className="lemma-gk">{lex.greek} · <em>{lex.translit}</em></div>
        <div className="sec">
          <div className="sec-head">
            <span className="sec-t">{isPlace ? "Biblical Place" : lex.cat === "person" ? "Biblical Person" : "Lemma"}</span>
            <span className="tag">{lex.tag}</span>
          </div>
          {isPlace ? (<MiniMap place={lex.place} label={lex.en}/>) : (
            <div className="fact">
              <div className="fact-row"><span className="fact-k">Type</span><span className="fact-v">{lex.type}</span></div>
              <div className="fact-row"><span className="fact-k">Strong's</span><span className="fact-v mono">{strong}</span></div>
              <div className="fact-row"><span className="fact-k">Occurrences</span><span className="fact-v">{lex.occ}</span></div>
            </div>
          )}
        </div>
        <div className="sec">
          <div className="sec-head">
            <span className="sec-t">Liddell-Scott-Jones <span className="lsj-badge">LSJ</span></span>
            <div className="seg seg-sm">
              <button className={"seg-b " + (!lsjFull ? "on" : "")} onClick={() => setLsjFull(false)}>Definition</button>
              <button className={"seg-b " + (lsjFull ? "on" : "")} onClick={() => setLsjFull(true)}>Full LSJ</button>
            </div>
          </div>
          <p className="lsj-text">{lsjFull ? lex.lsjFull : lex.lsj}</p>
        </div>
        <div className="sec">
          <div className="sec-head"><span className="sec-t">ABP Occurrences</span></div>
          <button className="occ-link">{lex.occ} <I.Arrow/></button>
        </div>
        <div className="sec">
          <div className="sec-head">
            <span className="sec-t">Verse — {refLabel}</span>
            <span className="sec-meta">LXX (ABP English)</span>
          </div>
          <blockquote className="dverse">
            <span className="dverse-n">{refLabel.split(":").pop()}</span>
            {verseText}
          </blockquote>
          <div className="dverse-tools">
            <button className="link-btn">Read in context <I.Arrow/></button>
            <span className="dot">·</span>
            <button className="link-btn">Interlinear</button>
          </div>
        </div>
      </div>
    </aside>
  );
}

// ============================================================
// TOP BAR (slim, ~44px)
// ============================================================
function TopBar({ book, chapter, onOpenBooks, onOpenModes }) {
  return (
    <div className="mbar">
      <button className="mbar-btn" onClick={onOpenBooks} aria-label="Books"><I.Menu/></button>
      <button className="mbar-loc" onClick={onOpenBooks}>
        <span className="mbar-loc-name">{book.name}</span>
        <span className="mbar-loc-ch">{chapter}</span>
        <I.ChevDown className="mbar-loc-cv"/>
      </button>
      <button className="mbar-btn" onClick={onOpenModes} aria-label="Reading options"><I.Modes/></button>
    </div>
  );
}

// ============================================================
// OVERLAY 1 — BOOK / CHAPTER SELECTOR
// ============================================================
function BookSelector({ book, chapter, onPick, onClose }) {
  const [stage, setStage] = useState("books"); // "books" | "chapters"
  const [draftBook, setDraftBook] = useState(book);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return BOOKS;
    return BOOKS.filter((b) => b.name.toLowerCase().includes(q) || b.ab.toLowerCase().includes(q));
  }, [query]);

  // group: testament → division → books (preserve canon order)
  const testaments = useMemo(() => {
    const tOrder = [];
    const tMap = {};
    for (const b of filtered) {
      if (!tMap[b.t]) { tMap[b.t] = { t: b.t, divs: [], divMap: {} }; tOrder.push(tMap[b.t]); }
      const T = tMap[b.t];
      if (!T.divMap[b.div]) { T.divMap[b.div] = { div: b.div, books: [] }; T.divs.push(T.divMap[b.div]); }
      T.divMap[b.div].books.push(b);
    }
    return tOrder;
  }, [filtered]);

  const tName = { OT: "Old Testament", NT: "New Testament" };

  const openChapters = (b) => { setDraftBook(b); setStage("chapters"); };
  const chooseChapter = (n) => { onPick(draftBook, n); };

  return (
    <div className="bsel" role="dialog" aria-label="Select book and chapter">
      <div className="bsel-head">
        {stage === "chapters" ? (
          <button className="bsel-head-btn" onClick={() => setStage("books")} aria-label="Back to books"><I.Back/></button>
        ) : (
          <button className="bsel-head-btn" onClick={onClose} aria-label="Close"><I.Close/></button>
        )}
        <span className="bsel-title">
          {stage === "books"
            ? "Books"
            : <><span className="bsel-title-pre">Chapter · </span>{draftBook.name}</>}
        </span>
      </div>

      {stage === "books" ? (
        <>
          <div className="bsel-search">
            <I.SearchSm/>
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find a book" autoFocus/>
          </div>
          <div className="bsel-body">
            {testaments.map((T) => (
              <div key={T.t}>
                <div className="bsel-test">
                  <span className="bsel-test-t">{tName[T.t] || T.t}</span>
                  <span className="bsel-test-line"></span>
                  <span className="bsel-test-n">{T.divs.reduce((a, d) => a + d.books.length, 0)} books</span>
                </div>
                {T.divs.map((D) => (
                  <div key={D.div}>
                    <span className="bsel-div">{D.div}</span>
                    <div className="bgrid">
                      {D.books.map((b) => (
                        <button key={b.ab} className={"btile " + (b.ab === book.ab ? "on" : "")} onClick={() => openChapters(b)}>
                          <span className="btile-ab">{b.ab.toUpperCase()}</span>
                          <span className="btile-ch">{b.ch} ch</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="bsel-body">
          <div className="chsel-cur">{draftBook.name} · <b>{draftBook.ch} chapters</b></div>
          <div className="chgrid">
            {Array.from({ length: draftBook.ch }, (_, i) => i + 1).map((n) => {
              const isCur = draftBook.ab === book.ab && n === chapter;
              return (
                <button key={n} className={"chtile " + (isCur ? "on" : "")} onClick={() => chooseChapter(n)}>{n}</button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// OVERLAY 2 — READING MODES (bottom sheet)
// ============================================================
function ModesSheet({ edition, setEdition, strongsOn, setStrongsOn, interlinear, setInterlinear, script, setScript, onClose }) {
  return (
    <>
      <div className="msheet-scrim" onClick={onClose}></div>
      <div className="msheet" role="dialog" aria-label="Reading options">
        <div className="msheet-handle" aria-hidden="true"></div>
        <div className="msheet-head">
          <span className="msheet-title">Reading</span>
          <button className="msheet-x" onClick={onClose} aria-label="Close"><I.Close/></button>
        </div>

        <div className="mode-sec">
          <div className="mode-lbl">Edition</div>
          <div className="mseg">
            {["abp", "kjv", "parallel"].map((e) => (
              <button key={e} className={"mseg-b " + (edition === e ? "on" : "")} onClick={() => setEdition(e)}>
                {e === "abp" ? "ABP" : e === "kjv" ? "KJV" : "Parallel"}
              </button>
            ))}
          </div>
        </div>

        <div className="mode-sec">
          <div className="mode-lbl">Study layer</div>
          <div className="mtog">
            <div className="mtog-row">
              <div className="mtog-txt">
                <div className="mtog-name">Strong's numbers</div>
                <div className="mtog-sub">Tap a word for its lexicon entry</div>
              </div>
              <button className={"switch " + (strongsOn ? "on" : "")} onClick={() => setStrongsOn(!strongsOn)} aria-label="Toggle Strong's" aria-pressed={strongsOn}></button>
            </div>
            <div className="mtog-row">
              <div className="mtog-txt">
                <div className="mtog-name">Interlinear</div>
                <div className="mtog-sub">Stack Greek, transliteration & gloss</div>
              </div>
              <button className={"switch " + (interlinear ? "on" : "")} onClick={() => setInterlinear(!interlinear)} aria-label="Toggle Interlinear" aria-pressed={interlinear}></button>
            </div>
          </div>
        </div>

        <div className="mode-sec">
          <div className="mode-lbl">Script</div>
          <div className="mseg">
            <button className={"mseg-b " + (script === "english" ? "on" : "")} onClick={() => setScript("english")}>English</button>
            <button className={"mseg-b " + (script === "greek" ? "on" : "")} onClick={() => setScript("greek")}>Greek</button>
          </div>
        </div>
      </div>
    </>
  );
}

// ============================================================
// BOTTOM TAB BAR (Search / Library / About)
// ============================================================
function BottomTabs() {
  return (
    <nav className="mtabs" aria-label="Primary">
      <a className="mtab" href="Bible Word Study.html"><I.Search/><span className="mtab-l">Search</span></a>
      <button className="mtab on" aria-current="page"><I.Book/><span className="mtab-l">Library</span></button>
      <button className="mtab"><I.Info/><span className="mtab-l">About</span></button>
    </nav>
  );
}

// ============================================================
// READER
// ============================================================
function Reader({ book, chapter, edition, strongsOn, interlinear, script, active, onPick, setChapter, onOpenBooks }) {
  const scrollRef = useRef(null);
  useEffect(() => { if (scrollRef.current) scrollRef.current.scrollTop = 0; }, [book, chapter, edition, interlinear, script]);

  const hasText = !!book.text;
  const versesAbp = hasText ? book.text.abp : [];
  const versesKjv = hasText ? book.text.kjv : [];
  const verses = hasText ? book.text[edition === "parallel" ? "abp" : edition] : [];
  const greekTitle = script === "greek" && book.ab === "Amo" ? "Ἀμώς" : book.name;

  return (
    <div className="mread" ref={scrollRef}>
      <div className="mread-col">
        <h1 className="mch-title">{greekTitle} <span className="mch-title-n">{chapter}</span></h1>
        <div className="mch-sub">
          {edition === "abp" ? "ABP · Apostolic Bible Polyglot" : edition === "kjv" ? "KJV · King James Version" : "ABP / KJV Parallel"}
        </div>

        {!hasText ? (
          <div className="mempty">
            <div className="mempty-mark"><I.Book/></div>
            <h2 className="mempty-t">{book.name} {chapter}</h2>
            <p className="mempty-s">This preview ships the study text for <b>Amos&nbsp;1</b> — the fully tagged sample chapter with Strong's, interlinear and parallel views.</p>
            <button className="mempty-btn" onClick={onOpenBooks}>Browse books <I.Arrow/></button>
          </div>
        ) : edition === "parallel" ? (
          <div className="parallel">
            <div className="par-col">
              <div className="par-head">ABP — Apostolic Bible Polyglot</div>
              {versesAbp.map((v, i) => (
                <Verse key={i} n={i + 1} abp={v} kjv={versesKjv[i]} edition="abp" strongsOn={strongsOn} interlinear={false} script={script} activeStrong={active} onPick={onPick}/>
              ))}
            </div>
            <div className="par-col">
              <div className="par-head">KJV — King James Version</div>
              {versesKjv.map((v, i) => (
                <Verse key={i} n={i + 1} abp="" kjv={v} edition="kjv" strongsOn={false} interlinear={false} script="english" activeStrong={active} onPick={onPick}/>
              ))}
            </div>
          </div>
        ) : (
          <div className="chapter">
            {verses.map((v, i) => (
              <Verse key={i} n={i + 1} abp={versesAbp[i]} kjv={versesKjv[i]} edition={edition} strongsOn={strongsOn} interlinear={interlinear} script={script} activeStrong={active} onPick={onPick}/>
            ))}
          </div>
        )}

        <div className="mread-foot">
          <button className="mfoot-nav" disabled={chapter <= 1} onClick={() => setChapter(chapter - 1)}>
            <I.Chevron style={{ transform: "rotate(180deg)" }}/> Ch {chapter - 1}
          </button>
          <span className="mfoot-ref">{book.name} {chapter} / {book.ch}</span>
          <button className="mfoot-nav" disabled={chapter >= book.ch} onClick={() => setChapter(chapter + 1)}>
            Ch {chapter + 1} <I.Chevron/>
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// APP  (lives inside the phone screen)
// ============================================================
function LibraryApp() {
  const [book, setBook] = useState(AMOS);
  const [chapter, setChapter] = useState(1);
  const [edition, setEdition] = useState("abp");
  const [strongsOn, setStrongsOn] = useState(true);
  const [interlinear, setInterlinear] = useState(false);
  const [script, setScript] = useState("english");
  const [active, setActive] = useState(null);
  const [activeRef, setActiveRef] = useState("");
  const [lsjFull, setLsjFull] = useState(false);
  const [booksOpen, setBooksOpen] = useState(false);
  const [modesOpen, setModesOpen] = useState(false);

  const versesAbp = book.text ? book.text.abp : [];
  const versesKjv = book.text ? book.text.kjv : [];

  const pickWord = (s) => {
    if (!WORDS[s]) return;
    setActive(s);
    setLsjFull(false);
    const vIdx = versesAbp.findIndex((v) => v.includes("{" + s + "|"));
    setActiveRef(`${book.name} ${chapter}:${vIdx >= 0 ? vIdx + 1 : 1}`);
  };

  const detailVerseText = useMemo(() => {
    const vIdx = versesAbp.findIndex((v) => v.includes("{" + active + "|"));
    if (vIdx < 0) return versesKjv[2] || "";
    return versesKjv[vIdx] || "";
  }, [active, versesAbp, versesKjv]);

  const handlePickBookChapter = (b, n) => {
    // BOOKS entries carry no bundled text; remap to the rich content constant when available
    setBook(b.ab === AMOS.ab ? AMOS : b);
    setChapter(n);
    setActive(null);
    setBooksOpen(false);
  };

  return (
    <div className="mlib">
      <TopBar book={book} chapter={chapter} onOpenBooks={() => setBooksOpen(true)} onOpenModes={() => setModesOpen(true)}/>

      <Reader
        book={book} chapter={chapter} edition={edition}
        strongsOn={strongsOn} interlinear={interlinear} script={script}
        active={active} onPick={pickWord} setChapter={(n) => { setChapter(n); setActive(null); }}
        onOpenBooks={() => setBooksOpen(true)}
      />

      <BottomTabs/>

      {booksOpen && (
        <BookSelector book={book} chapter={chapter} onPick={handlePickBookChapter} onClose={() => setBooksOpen(false)}/>
      )}

      {modesOpen && (
        <ModesSheet
          edition={edition} setEdition={setEdition}
          strongsOn={strongsOn} setStrongsOn={setStrongsOn}
          interlinear={interlinear} setInterlinear={setInterlinear}
          script={script} setScript={setScript}
          onClose={() => setModesOpen(false)}
        />
      )}

      {active && (
        <>
          <div className="sheet-scrim" onClick={() => setActive(null)}></div>
          <Detail strong={active} refLabel={activeRef} verseText={detailVerseText} onClose={() => setActive(null)} lsjFull={lsjFull} setLsjFull={setLsjFull}/>
        </>
      )}
    </div>
  );
}

// ============================================================
// STAGE — scale the phone to fit any viewport
// ============================================================
function Stage() {
  const W = 412, H = 892;
  const [scale, setScale] = useState(1);
  useEffect(() => {
    const fit = () => {
      const s = Math.min((window.innerWidth - 24) / W, (window.innerHeight - 24) / H, 1);
      setScale(s > 0 ? s : 1);
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);
  return (
    <div className="stage">
      <div className="stage-scale" style={{ transform: `scale(${scale})` }}>
        <AndroidDevice width={W} height={H}>
          <LibraryApp/>
        </AndroidDevice>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<Stage/>);
