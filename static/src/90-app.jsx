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
  const [entryView, setEntryView] = useState(null);   // which tab opened the word card (library|lexicon) — scopes the rail to that tab
  const [corpusFilter, setCorpusFilter] = useState("all"); // "all" | "ot" | "nt"
  const [corpusSort, setCorpusSort] = useState("curated"); // "curated" | "canonical"
  const [corpusTextMode, setCorpusTextMode] = useState("abp"); // "abp" | "kjv"
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 1100);
  // Remember the active tab across refreshes (guard against a stale/removed value).
  const _VIEWS = ["library", "lexicon", "corpus", "notes", "study", "news", "about"];
  const [mainView, setMainView] = useState(() => {
    // A /?news=<key> share link (Tudor's read-only News) opens straight on the News tab —
    // decided here, synchronously, so the default Library view never flashes first.
    try { if (new URLSearchParams(window.location.search).get("news")) return "news"; } catch (e) {}
    try { const v = localStorage.getItem("lexica.view.v1"); return _VIEWS.includes(v) ? v : "library"; }
    catch (e) { return "library"; }
  });
  useEffect(() => { try { localStorage.setItem("lexica.view.v1", mainView); } catch (e) {} }, [mainView]);
  const [libNav, setLibNav] = useState(null);
  const [libCrossRef, setLibCrossRef] = useState(null);
  const [lexiconPendingStrongs, setLexiconPendingStrongs] = useState(null);
  const [corpusPending, setCorpusPending] = useState(null);   // {ask} or {scope:{strongs,lemma,translit}} handed to the Ask-the-corpus tab
  const [studyPending, setStudyPending] = useState(null);   // open this name-topic in Study (from the metaV sidebar)
  const [libTranslation, setLibTranslation] = useState("abp");
  // Which panel is the base of the detail rail ("overview" = chapter summary, "intro" =
  // chrono day intro) — so a word/xref panel labels its back link to match.
  const [libDetailBase, setLibDetailBase] = useState("overview");
  const [activeNote, setActiveNote] = useState(null);   // note id being edited
  const [resetToken, setResetToken] = useState(null);   // ?reset=<token> from a password-reset email
  // No-login News reader: true once someone has opened a /?news=<key> share link (the key
  // is saved in localStorage). Lets them see the read-only News tab without an account.
  const [newsReader, setNewsReader] = useState(() => {
    try { if (new URLSearchParams(window.location.search).get("news")) return true; } catch (e) {}
    try { return !!localStorage.getItem("lexica.news.key.v1"); } catch (e) { return false; }
  });
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

  // The reader's true position lives in LibraryView; the rail cards + the gold jump
  // marker (libNav) live here. When the reader MOVES (book click, chapter pick, page
  // turn, chrono step) LibraryView reports the new spot so we can drop anything left
  // over from the old one — a cross-ref / word / note card, or a stale highlight from
  // a previous verse. An EXTERNAL jump (read-in-context, lexicon, verse-number click)
  // sets these to the SAME spot it lands on, so they MATCH and are kept. This single
  // reconcile is what keeps the rail + marker in step with the text (desktop + mobile).
  const handleReaderPos = (book, chapter) => {
    // Re-sync the marker to the reader and clear a stale highlight; an external jump
    // already matches (book+chapter), so its highlight survives. A restored spot has
    // no book yet (null) but the right chapter — treat that as a match too.
    setLibNav(prev => (prev && (prev.book == null || prev.book === book) && (prev.chapter || 1) === chapter) ? prev : { book, chapter, highlight: null });
    setLibCrossRef(cur => (cur && (cur.book !== book || cur.chapter !== chapter)) ? null : cur);
    setActiveEntry(cur => (cur && entryView === "library" && (cur.book !== book || cur.chapter !== chapter)) ? null : cur);
    setActiveNote(cur => {
      if (!cur) return cur;
      const n = NotesStore.get(cur);
      return (n && (n.book !== book || n.chapter !== chapter)) ? null : cur;
    });
  };

  // Returning to the Library tab re-scrolls to the placeholder verse (the last verse
  // you clicked / jumped to), so it survives a tab switch like a version switch does.
  useEffect(() => {
    if (mainView === "library") setLibNav(n => (n && n.highlight != null) ? { ...n, scroll: true, instant: true } : n);
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
    // A /?news=<key> share link (Tudor's read-only News) skips the full-site welcome tour.
    try { if (new URLSearchParams(window.location.search).get("news")) return false; } catch (e) {}
    try { return !localStorage.getItem("lexica_tour_seen"); } catch { return false; }
  });
  const handleTourDone = () => {
    try { localStorage.setItem("lexica_tour_seen", "1"); } catch {}
    setShowTour(false);
  };

  const [libEverVisited, setLibEverVisited] = useState(true);
  // News mounts on first visit, then STAYS mounted (display:none when away) — like the
  // Library above. Without this the tab was conditionally rendered, so leaving it unmounted
  // NewsView and returning re-ran its initial fetch (and lost filters/scroll/selection).
  const [newsEverVisited, setNewsEverVisited] = useState(false);
  useEffect(() => { if (mainView === "news") setNewsEverVisited(true); }, [mainView]);
  const searchScrollRef = useRef(0);

  // Deep link from the crawlable /read/ pages ("Open in interactive reader" →
  // /?b=<abbrev>&c=<chapter>&t=<text>). Jump to that WHOLE chapter the same way a
  // Search/Notes jump does — book selected, left nav follows, reader at top — but
  // with NO verse highlight (it's a chapter, not a verse). Then strip the query so a
  // refresh doesn't re-jump; the spot is saved to localStorage like any reading position.
  useEffect(() => {
    let p;
    try { p = new URLSearchParams(window.location.search); } catch (e) { return; }
    const reset = p.get("reset");
    if (reset) {   // arrived from a password-reset email → open the reset dialog
      setResetToken(reset);
      try { window.history.replaceState(null, "", window.location.pathname); } catch (e) {}
      return;
    }
    const newsKey = p.get("news");
    if (newsKey) {   // a News share link → save the key, open the read-only News tab
      try { localStorage.setItem("lexica.news.key.v1", newsKey); } catch (e) {}
      setNewsReader(true);
      setMainView("news");
      try { window.history.replaceState(null, "", window.location.pathname); } catch (e) {}
      return;
    }
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
  // Seed owner SYNCHRONOUSLY from the last-known value (like newsReader above) so the first
  // painted frame already has the right News nav visibility. Without this, owner starts false
  // and only flips true after the async /api/stats/owner fetch below — Firefox paints that
  // first newsless frame, so the News nav flashed in ~500ms late on refresh. The fetch still
  // runs and corrects the cache (e.g. after a logout).
  const [owner, setOwner] = useState(() => { try { return localStorage.getItem("lexica.owner.v1") === "1"; } catch (e) { return false; } });
  const [authEmail, setAuthEmail] = useState(() => { try { return (NotesStore.authInfo() || {}).email || null; } catch (e) { return null; } });
  const [authName, setAuthName] = useState(() => { try { return (NotesStore.authInfo() || {}).name || null; } catch (e) { return null; } });
  const [authOpen, setAuthOpen] = useState(null);   // header "Log in" → sign-in popup
  const [accountOpen, setAccountOpen] = useState(false);   // header account → dropdown in place
  useEffect(() => { api.statsHit(); }, []);
  useEffect(() => {
    let last;
    const check = () => {
      let email = null;
      try {
        const ai = NotesStore.authInfo() || {};
        email = ai.email || null;
        setAuthName(ai.name || null);
      } catch (e) {}
      setAuthEmail(email);
      if (email === last) return;
      last = email;
      api.statsOwner().then(d => {
        const o = !!(d && d.owner);
        setOwner(o);
        try { localStorage.setItem("lexica.owner.v1", o ? "1" : "0"); } catch (e) {}
      });
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

  // AI lives in its own "Ask the corpus" tab now — a question hands off there.
  const handleAiSearch = (overrideQ) => {
    const q = (overrideQ !== undefined ? overrideQ : q2).trim();
    if (!q) return;
    setActiveEntry(null);
    setLibCrossRef(null);
    setCorpusPending({ ask: q });
    handleNavChange("corpus");
  };
  // From Word study's "✦ Ask AI about <word>": seed the corpus tab's scope +
  // contextual suggestions (no question fired yet).
  const handleAskWord = (strongs, lemma, translit) => {
    if (!strongs) return;
    setActiveEntry(null);
    setLibCrossRef(null);
    setCorpusPending({ scope: { strongs, lemma, translit } });
    handleNavChange("corpus");
  };

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

  return (
    <div className={"app view-" + mainView + " " + ((showWord || showXref || showNote || showLibSummary) ? "has-detail " : "") + (focusMode && mainView === "library" ? "focus-mode" : "")}>
      <Header activeView={mainView} onNavChange={handleNavChange} owner={owner} showNews={owner || newsReader}
        email={authEmail} name={authName} onLogin={() => setAuthOpen("login")} onAccount={() => setAccountOpen(true)}/>
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
            <LibraryView nav={libNav} onNavChange={setLibNav} onReaderPos={handleReaderPos} onWordClick={(e) => { if (isMobile) setLibCrossRef(null); setActiveNote(null); setActiveEntry(e); setEntryView("library"); }} onVerseNumberClick={handleVerseNumberClick} onOpenNote={openNote} onTranslationChange={setLibTranslation} isMobile={isMobile} showSummary={showLibSummary} focusMode={focusMode} onToggleFocus={() => setFocusMode(f => !f)} onDetailBaseChange={setLibDetailBase} />
          </div>
        )}
        {mainView === "about" && <AboutView owner={owner} />}
        {(owner || newsReader) && newsEverVisited && (
          <div style={{ display: mainView === "news" ? undefined : "none" }}>
            <NewsView isMobile={isMobile} />
          </div>
        )}
        {mainView === "notes" && <NotesView onOpen={openNoteFromList} isMobile={isMobile} onReadInContext={handleReadInContext} />}
        <div style={{ display: mainView === "study" ? undefined : "none" }}>
          <StudyView admin={owner} pending={studyPending} onConsumed={() => setStudyPending(null)} onNavigateToLibrary={handleReadInContext} isMobile={isMobile} />
        </div>
        <div style={{ display: mainView === "corpus" ? undefined : "none" }}>
          <AskCorpusView
            pending={corpusPending}
            onConsumed={() => setCorpusPending(null)}
            onReadInContext={handleReadInContext}
            onNavigateToLexicon={handleNavigateToLexicon}
            isMobile={isMobile}
          />
        </div>
        <div style={{ display: mainView === "lexicon" ? undefined : "none" }}>
          <LexiconView
            onAiSearch={handleAiSearch}
            onAskWord={handleAskWord}
            onNavigateToLibrary={(book, chapter, verse, corpus) => {
              searchScrollRef.current = window.scrollY;
              setLibNav({ book, chapter, highlight: verse, scroll: true, extern: true, translation: corpus === "kjv" ? "kjv" : corpus === "heb" ? "heb" : corpus === "bsb" ? "bsb" : "abp" });
              setLibEverVisited(true);
              setMainView("library");
              // Same as Read-in-context: desktop queues the xref (shows now if resting on the
              // summary, else tucks under the open panel and surfaces when it closes).
              if (!isMobile) setLibCrossRef({ book, chapter, verse, translation: corpus === "kjv" ? "kjv" : "abp" });
            }}
            onWordClick={(e) => { setActiveEntry(e); setEntryView("lexicon"); }}
            pendingStrongs={lexiconPendingStrongs}
            onPendingStrongsConsumed={() => setLexiconPendingStrongs(null)}
            isMobile={isMobile}
          />
        </div>
      </main>

      {/* key={id} remounts the panel for every distinct word so referent-specific state
          (the verse-bound entity, metaV person/place, AI blurb) starts fresh — without it
          the reused panel paints the PREVIOUS word's identity on the first frame, then
          swaps once the bind resolves (the Eden "garden → Mesopotamia" flip). */}
      {showWord && !isMobile && (
        <DetailPanel
          key={activeEntry.id}
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

      {showWord && isMobile && (
        <>
          <div className="sheet-scrim" onClick={() => setActiveEntry(null)}/>
          <DetailPanel
            key={activeEntry.id}
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
      {showNote && (
        <NotesPanel
          noteId={activeNote}
          isMobile={isMobile}
          onClose={() => setActiveNote(null)}
        />
      )}
      {showXref && !isMobile && !showWord && !showNote && (
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
          onOpenStudy={handleOpenStudyName}
          isMobile={false}
          overviewBack={true}
          backLabel={libDetailBase === "intro" ? "Intro" : "Overview"}
        />
      )}
      {showXref && isMobile && (
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
            onOpenStudy={handleOpenStudyName}
            isMobile={true}
          />
        </>
      )}
      {showTour && <GuidedTour onDone={handleTourDone} />}

      {isMobile && (
        <nav className="mobile-tabs">
          <button className={"mobile-tab" + (mainView === "library" ? " active" : "")} onClick={() => handleNavChange("library")} title="Library" aria-label="Library">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3"/></svg>
          </button>
          <button className={"mobile-tab" + (mainView === "lexicon" ? " active" : "")} onClick={() => handleNavChange("lexicon")} title="Words" aria-label="Words">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M4 19V6a2 2 0 0 1 2-2h13"/><path d="M4 19a2 2 0 0 0 2 2h13V8H6a2 2 0 0 0-2 2"/></svg>
          </button>
          <button className={"mobile-tab" + (mainView === "corpus" ? " active" : "")} onClick={() => handleNavChange("corpus")} title="Ask the corpus" aria-label="Ask the corpus">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.4c.3 3.4 1.6 5.3 3.4 6.4 1.1.7 2.6 1 4.9 1.2-2.3.2-3.8.5-4.9 1.2-1.8 1.1-3.1 3-3.4 6.4-.3-3.4-1.6-5.3-3.4-6.4-1.1-.7-2.6-1-4.9-1.2 2.3-.2 3.8-.5 4.9-1.2C10.4 7.7 11.7 5.8 12 2.4Z"/></svg>
          </button>
          <button className={"mobile-tab" + (mainView === "notes" ? " active" : "")} onClick={() => handleNavChange("notes")} title="Notes" aria-label="Notes">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M6 3h12v18l-6-4-6 4z"/></svg>
          </button>
          {owner && (
            <button className={"mobile-tab" + (mainView === "study" ? " active" : "")} onClick={() => handleNavChange("study")} title="Study" aria-label="Study">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M9 7h7M9 11h7"/></svg>
            </button>
          )}
          {(owner || newsReader) && (
            <button className={"mobile-tab" + (mainView === "news" ? " active" : "")} onClick={() => handleNavChange("news")} title="News" aria-label="News">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 5h13a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a2 2 0 0 1-2-2V7"/><path d="M18 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2"/><path d="M7 8h7M7 12h7M7 16h4"/></svg>
            </button>
          )}
          <button className={"mobile-tab" + (mainView === "about" ? " active" : "")} onClick={() => handleNavChange("about")} title="About" aria-label="About">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="8.5"/><line x1="12" y1="12" x2="12" y2="16"/></svg>
          </button>
        </nav>
      )}
      {resetToken && <AuthModal mode="reset" resetToken={resetToken} onClose={() => setResetToken(null)} />}
      {authOpen && <AuthModal mode={authOpen} onClose={() => setAuthOpen(null)} />}
      {accountOpen && <AccountModal anchored onClose={() => setAccountOpen(false)} />}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
