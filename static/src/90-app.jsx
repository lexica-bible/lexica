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
  const [corpusFilter, setCorpusFilter] = useState("all"); // "all" | "ot" | "nt"
  const [corpusSort, setCorpusSort] = useState("curated"); // "curated" | "canonical"
  const [corpusTextMode, setCorpusTextMode] = useState("abp"); // "abp" | "kjv"
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 1100);
  // Remember the active tab across refreshes (guard against a stale/removed value).
  const _VIEWS = ["library", "lexicon", "search", "notes", "study", "about"];
  const [mainView, setMainView] = useState(() => {
    try { const v = localStorage.getItem("lexica.view.v1"); return _VIEWS.includes(v) ? v : "library"; }
    catch (e) { return "library"; }
  });
  useEffect(() => { try { localStorage.setItem("lexica.view.v1", mainView); } catch (e) {} }, [mainView]);
  const [libNav, setLibNav] = useState(null);
  const [libCrossRef, setLibCrossRef] = useState(null);
  const [lexiconPendingStrongs, setLexiconPendingStrongs] = useState(null);
  const [studyPending, setStudyPending] = useState(null);   // open this name-topic in Study (from the metaV sidebar)
  const [libTranslation, setLibTranslation] = useState("abp");
  // Which panel is the base of the detail rail ("overview" = chapter summary, "intro" =
  // chrono day intro) — so a word/xref panel labels its back link to match.
  const [libDetailBase, setLibDetailBase] = useState("overview");
  const [activeNote, setActiveNote] = useState(null);   // note id being edited
  const [focusMode, setFocusMode] = useState(false);    // distraction-free reading: chrome hidden (library only, not remembered)

  // Open a note's editor — closes the word / cross-ref panels so one panel owns the slot.
  const openNote = (id) => { setActiveEntry(null); setLibCrossRef(null); setActiveNote(id); };
  // From the Notes tab: jump to the verse in the Library, then open the editor.
  const openNoteFromList = (n) => {
    if (n.corpus === "bible") {
      searchScrollRef.current = window.scrollY;
      setLibEverVisited(true);
      setMainView("library");
      setLibNav({ book: n.book, chapter: n.chapter, highlight: n.start.verse, scroll: true, extern: true, translation: n.translation === "kjv" ? "kjv" : "abp" });
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
    const onWheel = (e) => {
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
            if (!((dir < 0 && atTop) || (dir > 0 && atBottom))) return;  // inner list can still scroll
          }
        }
        node = node.parentElement;
      }
      e.preventDefault();   // nothing left to scroll in the chrome → don't scroll the page
    };
    document.addEventListener("wheel", onWheel, { passive: false });
    return () => document.removeEventListener("wheel", onWheel);
  }, []);


  const handleVerseNumberClick = (book, chapter, verse, translation) => {
    setActiveEntry(null);
    setActiveNote(null);
    setLibCrossRef({ book, chapter, verse, translation: translation || "abp" });
    setLibNav(prev => ({ ...(prev || {}), book, chapter, highlight: verse }));
  };

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
    if (mode === "ai" && aiMeta && aiMeta.keyStrongs && aiMeta.keyStrongs.length > 0)
      return aiMeta.keyStrongs;
    return null;
  }, [mode, aiMeta]);

  // Compute citedStrongs at App level — single source of truth, no prop-threading issues
  const citedStrongsApp = useMemo(() => {
    if (!primaryStrongs || !primaryStrongs.length) return null;
    const s = new Set();
    for (const p of primaryStrongs) {
      if (p.strongs_base) {
        const bare = strongsBare(p.strongs_base);
        s.add(p.strongs_base);   // as-is (e.g. "4151" or "G4151")
        s.add(bare);             // bare (e.g. "4151")
        s.add(`G${bare}`);       // G-prefixed
        s.add(`H${bare}`);       // H-prefixed
      }
    }
    return s.size > 0 ? s : null;
  }, [primaryStrongs]);

  // Count of distinct primary verses (AI mode only)
  const primaryVerseCount = useMemo(() => {
    if (mode !== "ai") return null;
    const seen = new Set();
    for (const e of allResults) { if (e.is_primary) seen.add(e.ref); }
    return seen.size;
  }, [allResults, mode]);

  const [showTour, setShowTour] = useState(() => {
    try { return !localStorage.getItem("lexica_tour_seen"); } catch { return false; }
  });
  const handleTourDone = () => {
    try { localStorage.setItem("lexica_tour_seen", "1"); } catch {}
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
    try { p = new URLSearchParams(window.location.search); } catch (e) { return; }
    const lex = p.get("lex");
    if (lex) {   // word page → open the Lexicon tab on that Strong's number
      setMainView("lexicon");
      setLexiconPendingStrongs(lex);
      try { window.history.replaceState(null, "", window.location.pathname); } catch (e) {}
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
    setLibNav({ book: b, chapter, highlight: null, scroll: false, extern: true, translation });
    try { window.history.replaceState(null, "", window.location.pathname); } catch (e) {}
    requestAnimationFrame(() => window.scrollTo(0, 0));
  }, []);

  // Visitor stats: count this page load once (the server skips the owner's own
  // visits), and figure out whether the logged-in user is the owner so we can show
  // the private Stats tab. Re-check only when the signed-in email actually changes.
  const [owner, setOwner] = useState(false);
  useEffect(() => { api.statsHit(); }, []);
  useEffect(() => {
    let last;
    const check = () => {
      let email = null;
      try { email = (NotesStore.authInfo() || {}).email || null; } catch (e) {}
      if (email === last) return;
      last = email;
      api.statsOwner().then(d => setOwner(!!(d && d.owner)));
    };
    check();
    return NotesStore.subscribe(check);   // setAuth notifies on login/logout
  }, []);

  const handleReadInContext = (book, chapter, verse) => {
    searchScrollRef.current = window.scrollY;
    // `extern` (jump came from OUTSIDE the reader — Search results, or a word panel opened over them)
    // flips chrono→canonical so the verse shows in its chapter. A word panel opened IN the library
    // (mainView already "library") is an in-reader control, so it stays chronological.
    setLibNav({ book, chapter, highlight: verse, scroll: true, extern: mainView !== "library" });
    setLibEverVisited(true);
    setMainView("library");
    // Desktop: queue the verse's cross-references for the rail. If it's resting on the summary
    // the xref shows right away; if a word-study / note panel is up, the xref sits UNDER it (its
    // render is gated on those) and surfaces when that panel is closed — instead of the summary.
    // Mobile keeps the reader unobstructed (xref is a full bottom sheet there).
    if (!isMobile) setLibCrossRef({ book, chapter, verse, translation: "abp" });
  };

  const handleNavChange = (view) => {
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
    setActiveEntry(null);   // close the word panel (bottom sheet on mobile) before showing the lexicon
    setLibCrossRef(null);
    setLexiconPendingStrongs({ strongs, corpus });   // corpus: "abp" | "kjv" | undefined (default by language)
    handleNavChange("lexicon");
  };

  const handleOpenStudyName = (id) => {
    if (!id) return;
    setActiveEntry(null);     // close the person/place panel before jumping to Study
    setLibCrossRef(null);
    setStudyPending(id);
    handleNavChange("study");
  };

  const handleAiSearch = async (overrideQ) => {
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
        setAiMeta({ query: q, explanation: data.explanation || "", total: data.total || 0, keyStrongs: data.key_strongs || [] });
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

  // Desktop Library: when nothing is selected, the right panel rests on the
  // book/chapter overview (SummaryPanel). It fills the same slot the word-study
  // and xref panels use, so `has-detail` stays on and the reading column keeps
  // its condensed (three-column) measure. Mobile never shows the summary.
  const showLibSummary = !isMobile && mainView === "library" && !activeEntry && !libCrossRef && !activeNote;

  return (
    <div className={"app view-" + mainView + " " + ((activeEntry || libCrossRef || activeNote || showLibSummary) ? "has-detail " : "") + (focusMode && mainView === "library" ? "focus-mode" : "")}>
      <Header activeView={mainView} onNavChange={handleNavChange} owner={owner}/>
      {isMobile && mainView !== "library" && (
        <div className="mobile-brand-bar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M11 7v6M14 10h-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
          </svg>
          <span className="mobile-brand-name">Lexica</span>
          <span className="mobile-brand-sub">Greek &amp; Hebrew Word Study</span>
        </div>
      )}
      <main className="main">
        {libEverVisited && (
          <div style={{ display: mainView === "library" ? undefined : "none" }}>
            <LibraryView nav={libNav} onNavChange={setLibNav} onWordClick={(e) => { setLibCrossRef(null); setActiveNote(null); setActiveEntry(e); }} onVerseNumberClick={handleVerseNumberClick} onOpenNote={openNote} onTranslationChange={setLibTranslation} isMobile={isMobile} showSummary={showLibSummary} focusMode={focusMode} onToggleFocus={() => setFocusMode(f => !f)} onDetailBaseChange={setLibDetailBase} />
          </div>
        )}
        {mainView === "about" && <AboutView owner={owner} />}
        {mainView === "notes" && <NotesView onOpen={openNoteFromList} />}
        {mainView === "study" && owner && <StudyView pending={studyPending} onConsumed={() => setStudyPending(null)} />}
        <div style={{ display: mainView === "lexicon" ? undefined : "none" }}>
          <LexiconView
            onNavigateToSearch={(q) => { handleNavChange("search"); setQ2(q); }}
            onNavigateToLibrary={(book, chapter, verse, corpus) => {
              searchScrollRef.current = window.scrollY;
              setLibNav({ book, chapter, highlight: verse, scroll: true, extern: true, translation: corpus === "kjv" ? "kjv" : "abp" });
              setLibEverVisited(true);
              setMainView("library");
              // Same as Read-in-context: desktop queues the xref (shows now if resting on the
              // summary, else tucks under the open panel and surfaces when it closes).
              if (!isMobile) setLibCrossRef({ book, chapter, verse, translation: corpus === "kjv" ? "kjv" : "abp" });
            }}
            onWordClick={(e) => setActiveEntry(e)}
            pendingStrongs={lexiconPendingStrongs}
            onPendingStrongsConsumed={() => setLexiconPendingStrongs(null)}
            isMobile={isMobile}
          />
        </div>
        <div className="main-inner" style={{ display: (mainView === "library" || mainView === "about" || mainView === "lexicon" || mainView === "notes" || mainView === "study") ? "none" : undefined }}>
          <><SearchBar
            q2={q2} setQ2={setQ2}
            onAiSearch={handleAiSearch}
            aiLoading={aiLoading}
          />

          {aiNotice && (
            <div style={{
              marginTop: "14px",
              padding: "12px 16px",
              background: "var(--accent-soft, #f0f4ff)",
              border: "1px solid var(--accent, #b0bfff)",
              borderRadius: "10px",
              color: "var(--ink-2, #444)",
              fontSize: "14px",
            }}>
              {aiNotice}
            </div>
          )}

          {error && (
            <div style={{
              marginTop: "14px",
              padding: "12px 16px",
              background: "#fef2f2",
              border: "1px solid #fecaca",
              borderRadius: "10px",
              color: "#b91c1c",
              fontSize: "14px",
            }}>
              {error}
            </div>
          )}

          {aiMeta && (
            <AIAnswer
              query={aiMeta.query}
              explanation={aiMeta.explanation}
              keyStrongs={aiMeta.keyStrongs || []}
              onPick={(e) => setActiveEntry(e)}
            />
          )}

          {mode === "ai" && (
            <>
              <div className="results-head">
                <div className="results-meta">
                  <span className="results-count">{(loading || aiLoading) ? "…" : primaryVerseCount}</span>
                  <span className="results-label">primary {primaryVerseCount === 1 ? "verse" : "verses"}</span>
                  {!loading && aiMeta && aiMeta.total > primaryVerseCount && (
                    <button className="see-all-link" onClick={() => setShowAllAi(v => !v)}>
                      {showAllAi ? "Show less" : `See all ${aiMeta.total} occurrences`}
                    </button>
                  )}
                  {searchLabel && !aiLoading && <span className="results-for">for "<b>{searchLabel}</b>"</span>}
                </div>
                <div className="results-controls" style={{marginLeft:"auto"}}>
                  <div className="results-sort">
                    <button className={"sort-btn " + (corpusFilter === "all" ? "on" : "")} onClick={() => setCorpusFilter("all")}>All</button>
                    <button className={"sort-btn " + (corpusFilter === "ot"  ? "on" : "")} onClick={() => setCorpusFilter("ot")}>OT</button>
                    <button className={"sort-btn " + (corpusFilter === "nt"  ? "on" : "")} onClick={() => setCorpusFilter("nt")}>NT</button>
                    <span style={{margin:"0 4px",color:"var(--rule-2)"}}>|</span>
                    <button className={"sort-btn " + (corpusSort === "curated"   ? "on" : "")} onClick={() => setCorpusSort("curated")}>Curated</button>
                    <button className={"sort-btn " + (corpusSort === "canonical" ? "on" : "")} onClick={() => setCorpusSort("canonical")}>Canonical</button>
                    <span style={{margin:"0 4px",color:"var(--rule-2)"}}>|</span>
                    <button className={"sort-btn " + (corpusTextMode === "abp" ? "on" : "")} onClick={() => setCorpusTextMode("abp")}>ABP</button>
                    <button className={"sort-btn " + (corpusTextMode === "kjv" ? "on" : "")} onClick={() => setCorpusTextMode("kjv")}>KJV</button>
                  </div>
                </div>
              </div>
              {(loading || aiLoading) ? (
                <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--ink-3)", fontSize: "14px" }}>
                  Searching…
                </div>
              ) : (
                <CorpusResults allResults={corpusFilteredResults} primaryStrongs={primaryStrongs} citedStrongs={citedStrongsApp} showAll={showAllAi} onWordClick={(e) => setActiveEntry(e)} onReadInContext={handleReadInContext} corpusSort={corpusSort} textMode={corpusTextMode} />
              )}
            </>
          )}

          <footer className="foot">
            <span>Lexica · Greek Septuagint (LXX) · Apostolic Bible Polyglot Interlinear · Strong's Greek</span>
          </footer>
          </>
        </div>
      </main>

      {activeEntry && !isMobile && (
        <DetailPanel
          entry={activeEntry}
          isMobile={false}
          onClose={() => setActiveEntry(null)}
          occurrences={countMap[activeEntry.strongs_raw] || 0}
          totalResults={allResults.length}
                    onNavigateToLexicon={handleNavigateToLexicon}
          onReadInContext={handleReadInContext}
          onOpenStudyName={handleOpenStudyName}
          overviewBack={mainView === "library"}
          backLabel={libCrossRef ? "Cross-references" : (libDetailBase === "intro" ? "Intro" : "Overview")}
        />
      )}

      {activeEntry && isMobile && (
        <>
          <div className="sheet-scrim" onClick={() => setActiveEntry(null)}/>
          <DetailPanel
            entry={activeEntry}
            isMobile={true}
            onClose={() => setActiveEntry(null)}
            occurrences={countMap[activeEntry.strongs_raw] || 0}
            totalResults={allResults.length}
                        onNavigateToLexicon={handleNavigateToLexicon}
            onReadInContext={handleReadInContext}
            onOpenStudyName={handleOpenStudyName}
          />
        </>
      )}
      {activeNote && (
        <NotesPanel
          noteId={activeNote}
          isMobile={isMobile}
          onClose={() => setActiveNote(null)}
        />
      )}
      {libCrossRef && !isMobile && !activeEntry && !activeNote && (
        <CrossRefPanel
          source={libCrossRef}
          translation={libTranslation === "kjv" ? "kjv" : "abp"}
          onClose={() => { setLibCrossRef(null); setLibNav(prev => prev ? { ...prev, highlight: null } : prev); }}
          onNavigate={(book, chapter, verse) => {
            setMainView("library");
            setLibCrossRef(null);
            setLibNav({ book, chapter, scroll: true, highlight: verse });
          }}
          onAiSearch={(q) => { setLibCrossRef(null); handleAiSearch(q); }}
          isMobile={false}
          overviewBack={true}
          backLabel={libDetailBase === "intro" ? "Intro" : "Overview"}
        />
      )}
      {libCrossRef && isMobile && (
        <>
          <div className="sheet-scrim" onClick={() => { setLibCrossRef(null); setLibNav(prev => prev ? { ...prev, highlight: null } : prev); }} />
          <CrossRefPanel
            source={libCrossRef}
            translation={libTranslation === "kjv" ? "kjv" : "abp"}
            onClose={() => { setLibCrossRef(null); setLibNav(prev => prev ? { ...prev, highlight: null } : prev); }}
            onNavigate={(book, chapter, verse) => {
              setMainView("library");
              setLibCrossRef(null);
              setLibNav({ book, chapter, scroll: true, highlight: verse });
            }}
            onAiSearch={(q) => { setLibCrossRef(null); handleAiSearch(q); }}
            isMobile={true}
          />
        </>
      )}
      {showTour && <GuidedTour onDone={handleTourDone} />}

      {isMobile && (
        <nav className="mobile-tabs">
          <button className={"mobile-tab" + (mainView === "library" ? " active" : "")} onClick={() => handleNavChange("library")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3"/></svg>
            Library
          </button>
          <button className={"mobile-tab" + (mainView === "lexicon" ? " active" : "")} onClick={() => handleNavChange("lexicon")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M4 19V6a2 2 0 0 1 2-2h13"/><path d="M4 19a2 2 0 0 0 2 2h13V8H6a2 2 0 0 0-2 2"/></svg>
            Lexicon
          </button>
          <button className={"mobile-tab" + (mainView === "search" ? " active" : "")} onClick={() => handleNavChange("search")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><circle cx="11" cy="11" r="7"/><line x1="16.5" y1="16.5" x2="21" y2="21"/></svg>
            Search
          </button>
          <button className={"mobile-tab" + (mainView === "notes" ? " active" : "")} onClick={() => handleNavChange("notes")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M6 3h12v18l-6-4-6 4z"/></svg>
            Notes
          </button>
          {owner && (
            <button className={"mobile-tab" + (mainView === "study" ? " active" : "")} onClick={() => handleNavChange("study")}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M9 7h7M9 11h7"/></svg>
              Study
            </button>
          )}
          <button className={"mobile-tab" + (mainView === "about" ? " active" : "")} onClick={() => handleNavChange("about")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="8.5"/><line x1="12" y1="12" x2="12" y2="16"/></svg>
            About
          </button>
        </nav>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
