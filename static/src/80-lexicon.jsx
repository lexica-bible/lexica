// ============================================================
// LEXICON VIEW
// ============================================================
const _STRONGS_RE = /^[GgHh]?\d+(\.\d+)?$/;
// A phrase or question (3+ words, or ending in "?") routes to the corpus AI
// instead of a word lookup. A single English word still does a lexicon lookup.
const _looksLikeQuestion = (s) => /\?\s*$/.test(s) || s.split(/\s+/).filter(Boolean).length >= 3;

// Which original languages live in a (corpus, testament) slice of the English
// search results. ABP is Greek throughout (the Septuagint in the OT, Greek NT);
// KJV's OT is Hebrew and its NT is Greek. Lets the Greek/Hebrew filter gray out
// combos that can't return anything (ABP has no Hebrew; KJV's OT has no Greek)
// while still allowing Greek in the OT via the Septuagint.
function _sliceHasGreek(corpus, testament) {
  if (corpus === "kjv" || corpus === "bsb") return testament !== "ot";   // KJV/BSB: Greek only in the NT
  if (corpus === "heb") return false;                                     // Hebrew OT: no Greek
  return true;                                                            // ABP / All: always some Greek
}
function _sliceHasHebrew(corpus, testament) {
  if (corpus === "abp") return false;                 // ABP is all Greek
  return testament !== "nt";                           // HEB / KJV / BSB / All: Hebrew only outside the NT
}
function _comboOK(corpus, testament, language) {
  if (language === "greek")  return _sliceHasGreek(corpus, testament);
  if (language === "hebrew") return _sliceHasHebrew(corpus, testament);
  return true;
}

// Mobile word-study glyphs (kept local; mirror the design handoff's WMI set).
const WsI = {
  Search: (p) => (<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>),
  Book: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19"/><path d="M19 16H7.5"/></svg>),
  Card: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/></svg>),
  Sliders: (p) => (<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 8h9M19 8h0M5 16h0M10 16h9"/><circle cx="16" cy="8" r="2.4"/><circle cx="7.5" cy="16" r="2.4"/></svg>),
  ChevR: (p) => (<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m9 6 6 6-6 6"/></svg>),
  Close: (p) => (<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M6 6l12 12M6 18 18 6"/></svg>),
};

// Bottom sheet for the mobile word-study tools — rises from the bottom, drag the
// grab-zone down past ~110px to dismiss (ported from the design handoff's Sheet).
function WsSheet({ title, tall, titleMono, hideClose, onClose, children }) {
  // Same swipe-down-to-dismiss as every other sheet: the shared hook arms on the
  // chrome (handle/header) OR on the body when it's scrolled to the top.
  const { sheetRef, scrollRef } = useSwipeToDismiss(onClose);
  const [kb, setKb] = useState(0);   // how far the on-screen keyboard eats into the screen
  // Lift the sheet above the keyboard. Done via `bottom` (not transform) so it never
  // fights the swipe hook, which drives the sheet's transform.
  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;
    const onResize = () => setKb(Math.max(0, window.innerHeight - vv.height - vv.offsetTop));
    vv.addEventListener("resize", onResize);
    vv.addEventListener("scroll", onResize);
    onResize();
    return () => { vv.removeEventListener("resize", onResize); vv.removeEventListener("scroll", onResize); };
  }, []);
  return (
    <>
      <div className="wm-scrim" onClick={onClose}/>
      <div ref={sheetRef} className={"wm-sheet" + (tall ? " tall" : "")} style={kb ? { bottom: kb } : undefined}>
        <div className="wm-grab">
          <div className="wm-handle" aria-hidden="true"/>
          <div className="wm-sheet-head">
            <span className={"wm-sheet-title" + (titleMono ? " wm-sheet-title--mono" : "")}>{title}</span>
          </div>
        </div>
        <div ref={scrollRef} className="wm-sheet-body">{children}</div>
      </div>
    </>
  );
}

function LexiconView({ onNavigateToLibrary, onWordClick, pendingStrongs, onPendingStrongsConsumed, isMobile, onAiSearch, onAskWord }) {
  const [railOpen, setRailOpen] = useState(false);     // mobile: distribution drawer
  const [detailOpen, setDetailOpen] = useState(false); // mobile: word-card drawer
  const [glOpen, setGlOpen] = useState(true);          // English results card: expanded/collapsed
  const [sheet, setSheet] = useState(null);            // mobile bottom sheet: "search"|"dist"|"card"|"views"|null
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState(null);
  const [profile, setProfile] = useState(null);
  const [corpus, setCorpus] = useState("all");          // search-results scope: all | abp | kjv
  const [profileCorpus, setProfileCorpus] = useState("abp"); // drilled-in word view: abp | kjv (never "all")
  const [language, setLanguage] = useState("all");      // results filter: all | greek | hebrew
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
  const [lsjEntry, setLsjEntry] = useState(null);
  const [lsjSummary, setLsjSummary] = useState(null);
  const [lsjLoading, setLsjLoading] = useState(false);
  const [lsjSummaryLoading, setLsjSummaryLoading] = useState(false);

  // Reset the curated LSJ definition whenever the focused word changes.
  useEffect(() => { setLsjEntry(null); setLsjSummary(null); }, [profile?.strongs]);

  // Fetch the LSJ entry + AI-curated summary for the focused Greek word (Haiku,
  // cached). Hebrew keeps its BDB definition. The /api/lsj endpoint auto-falls
  // back to strongs_def when there's no LSJ match.
  useEffect(() => {
    if (!profile || !/^G/i.test(profile.strongs) || lsjEntry || lsjLoading) return;
    let cancelled = false;
    setLsjLoading(true);
    api.lsj(profile.lemma || "", profile.strongs.replace(/^[GH]/i, ""))
      .then(d => {
        if (cancelled) return;
        const entry = d && !d.error ? d : null;
        setLsjEntry(entry);
        setLsjLoading(false);
        if (entry && entry.source !== "strongs") {
          setLsjSummaryLoading(true);
          api.lsjSummary(entry.key)
            .then(s => { if (!cancelled) setLsjSummary(s); })
            .catch(() => {})
            .finally(() => { if (!cancelled) setLsjSummaryLoading(false); });
        }
      })
      .catch(() => { if (!cancelled) { setLsjEntry(null); setLsjLoading(false); } });
    return () => { cancelled = true; };
  }, [profile?.strongs]);

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
    // Land on "All books" (selectedBook=null), NOT the busiest book — auto-opening
    // a book buried the reader in one book's verses the moment you searched.
    setSelectedBook(null);
    setVerseList(null);
    setSelectedGloss(null);
    setBookGlosses(null);
    setFilteredBooks(null);
    const isHeb = /^H/i.test(strongs) || (!(/^[GgHh]/.test(strongs)) && parseInt(strongs) > 5624);
    const c = corpusOverride ?? (isHeb ? "heb" : "abp");  // Hebrew lands on the real Hebrew OT (heb.db)
    setProfileCorpus(c);
    try {
      const data = await api.lexiconProfile(strongs, c);
      if (data.error) setError(data.error);
      // Honor the source the backend actually used — a Hebrew number heb.db lacks
      // (a byform/Aramaic/name) falls back to KJV, so reflect that in the toggle.
      else { setProfile(data); if (data.corpus && data.corpus !== c) setProfileCorpus(data.corpus); }
    } catch (e) { setError("Failed to load word profile: " + e); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (profile && pendingGloss) {
      selectGloss(pendingGloss);
      setPendingGloss(null);
    }
  }, [profile, pendingGloss]);

  // Search-results scope toggle (All / ABP / KJV). Only shown when no word is
  // in focus; re-runs the English search in that corpus.
  const switchCorpus = async (c) => {
    if (loading || c === corpus) return;
    if (c !== "all" && !_comboOK(c, testament, language)) return;  // grayed combo
    setCorpus(c);
    const q = query.trim();
    const isEnglishQuery = !!q && !_STRONGS_RE.test(q) && !_isGreekHebrew(q);
    if (groupings && isEnglishQuery) {
      setLoading(true);
      try {
        const data = await api.lexiconEnglish(q, c, testament);
        setGroupings(data.length ? data : null);
        setError(data.length ? null : "No matches found.");
      } catch { setError("Search failed."); }
      finally { setLoading(false); }
    }
  };

  // Profile corpus toggle (ABP / KJV). Reloads the focused word in that corpus.
  const switchProfileCorpus = async (c) => {
    if (loading || c === profileCorpus || !profile) return;
    setProfileCorpus(c);
    setLoading(true);
    setSelectedBook(null);
    setVerseList(null);
    setTestament("all");
    setSelectedGloss(null);
    setBookGlosses(null);
    setFilteredBooks(null);
    try {
      const data = await api.lexiconProfile(profile.strongs, c);
      if (!data.error) setProfile(data);   // stays on "All books" (selectedBook cleared above)
    } catch {}
    finally { setLoading(false); }
  };

  const switchTestament = async (t) => {
    if (loading) return;
    if (!profile && t !== "all" && !_comboOK(corpus, t, language)) return;  // grayed combo (results view only)
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
      } catch { setError("Search failed."); }
      finally { setLoading(false); }
    }
  };

  // Greek/Hebrew filter for the results grid — a pure client-side row filter, no
  // refetch. Graying (via _comboOK) keeps it from clashing with corpus/testament.
  const switchLanguage = (l) => {
    if (l === language || !_comboOK(corpus, testament, l)) return;
    setLanguage(l);
  };

  const fetchVerses = async (book, gloss) => {
    setVerseList(null);
    setVerseLoading(true);
    try {
      const data = await api.lexiconVerses(profile.strongs, book, profileCorpus, gloss);
      if (data.error) {
        setVerseList([{ error: data.error }]);
      } else {
        setVerseList(data.verses || []);
        setBookGlosses(data.glosses && data.glosses.length ? data.glosses : null);
      }
    } catch (e) { setVerseList([{ error: String(e) }]); }
    finally { setVerseLoading(false); }
  };

  const selectBook = async (book) => {
    if (selectedBook === book) { setSelectedBook(null); setVerseList(null); setBookGlosses(null); return; }
    setSelectedBook(book);
    await fetchVerses(book, selectedGloss);
  };

  const selectGloss = async (gloss) => {
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

  const _isGreekHebrew = (s) => /[Ͱ-Ͽἀ-῿֐-׿]/.test(s);

  // One "<Bible> renders this as" line. The active toggle's line is the
  // interactive one (click a rendering to filter the books/verses below); the
  // other Bible's line is shown read-only, just so you can see both at once.
  const renderGlossLine = (lineCorpus, label, list) => {
    if (!list || !list.length) return null;
    const interactive = profileCorpus === lineCorpus;
    return (
      <div className="lexicon-glosses">
        {label && <div className="lexicon-gloss-label">{label}</div>}
        <div className="lexicon-dist-list">
          {list.map((g, i) => (
            <React.Fragment key={g.gloss}>
              {i > 0 && <span className="lexicon-dist-sep"> · </span>}
              {interactive ? (
                <button
                  className={"lexicon-dist-item" + (selectedGloss === g.gloss ? " selected" : "")}
                  onClick={() => selectGloss(g.gloss)}
                >
                  {g.gloss}<span className="lexicon-dist-count">{g.count}</span>
                </button>
              ) : (
                <span className="lexicon-dist-item lexicon-dist-item--ref">
                  {g.gloss}<span className="lexicon-dist-count">{g.count}</span>
                </span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    );
  };

  // A result row's rendering preview: an ABP line and/or a KJV line, each
  // labeled with its ABP/KJV tag (so a single-Bible word still says which one).
  // Desktop caps each line at 6 renderings; mobile shows all (wraps).
  const renderRowPreview = (g) => {
    const line = (list, tag) => !list || list.length === 0 ? null : (
      <span className="lex-prev-line" key={tag}>
        <span className="lex-prev-tag">{tag}</span>
        {(isMobile ? list : list.slice(0, 6)).map(x => x.gloss).join(", ")}
      </span>
    );
    return [line(g.abp_glosses, "ABP"), line(g.kjv_glosses, "KJV")];
  };

  // Light up every form of the focused word's Strong's in the verse list.
  const citedStrongs = useMemo(() => {
    if (!profile?.strongs) return new Set();
    const tag = profile.strongs;              // "G4521" or, for an ABP dotted different-word, "G4521.2"
    return new Set([tag, strongsBare(tag)]);  // match the FULL number — a dotted word lights up itself, not its base
  }, [profile?.strongs]);

  const handleSubmit = async (e, override) => {
    e?.preventDefault?.();
    const q = (override !== undefined ? override : query).trim();
    if (!q) return;
    setQuery(q);
    setProfile(null);
    setMatches(null);
    setGroupings(null);
    setError(null);
    // Plain-language question / phrase → hand the box over to the corpus AI.
    if (onAiSearch && !_STRONGS_RE.test(q) && !_isGreekHebrew(q) && _looksLikeQuestion(q)) {
      onAiSearch(q);
      return;
    }
    if (_STRONGS_RE.test(q)) {
      const normalized = /^[GgHh]/i.test(q) ? q.toUpperCase() : q;
      loadProfile(normalized);
      return;
    }
    setLoading(true);
    try {
      if (_isGreekHebrew(q)) {
        const data = await api.lexiconLookup(q);
        if (!data.length) setError("No matches found.");
        else if (data.length === 1) loadProfile(data[0].strongs);
        else setMatches(data);
      } else {
        const data = await api.lexiconEnglish(q, corpus, testament);
        if (data.length) { setGroupings(data); setGlOpen(true); }
        else {
          // No English meaning matched — the input may be a Greek/Hebrew word
          // typed in Latin letters (e.g. "pneuma"). Fall back to the lookup,
          // which matches transliterations accent-insensitively.
          const alt = await api.lexiconLookup(q);
          if (!alt.length) setError("No matches found for \"" + q + "\".");
          else if (alt.length === 1) loadProfile(alt[0].strongs);
          else setMatches(alt);
        }
      }
    } catch { setError("Search failed."); }
    finally { setLoading(false); }
  };

  // Apply the Greek/Hebrew filter to the results grid (client-side row hide).
  const visibleGroupings = !groupings ? null
    : language === "all" ? groupings
    : groupings.filter(g => language === "greek" ? g.strongs[0] === "G" : g.strongs[0] === "H");

  const isHeb = profile && profile.strongs[0] === "H";
  const occCount = !profile ? 0 : (testament === "all"
    ? profile.total
    : (filteredBooks || profile.books).filter(b => (b.testament || "").toLowerCase() === testament).reduce((s, b) => s + b.count, 0));
  const distBooks = !profile ? [] : (filteredBooks || profile.books)
    .filter(b => testament === "all" || (b.testament || "").toLowerCase() === testament)
    .slice().sort((a, b) => b.count - a.count);
  const maxCount = distBooks.length ? distBooks[0].count : 1;
  const firstGloss = !profile ? "" : (
    (((profileCorpus === "heb" ? profile.heb_glosses : profileCorpus === "bsb" ? profile.bsb_glosses : profileCorpus === "kjv" ? profile.kjv_glosses : profile.abp_glosses) || [])[0] || {}).gloss
    || ((profile.heb_glosses || profile.abp_glosses || profile.kjv_glosses || profile.bsb_glosses || [])[0] || {}).gloss || "");
  const selBookName = profile && selectedBook ? (profile.books.find(b => b.book === selectedBook)?.name || selectedBook) : "";
  const selBookCount = profile && selectedBook ? (profile.books.find(b => b.book === selectedBook)?.count ?? null) : null;
  const backToResults = () => { setProfile(null); setSelectedBook(null); setVerseList(null); };

  // ---- shared render helpers (used by the desktop panes AND the mobile sheets) ----
  const renderDistRows = (afterPick) => (
    <>
      <button className={"brow brow-all" + (!selectedBook ? " on" : "")}
        onClick={() => { setSelectedBook(null); setVerseList(null); setBookGlosses(null); setSelectedGloss(null); setFilteredBooks(null); afterPick && afterPick(); }}>
        <span className="brow-name">All books</span>
        <span className="brow-n">{occCount}</span>
      </button>
      {distBooks.map(b => (
        <button key={b.book} className={"brow" + (selectedBook === b.book ? " on" : "")}
          onClick={() => { selectBook(b.book); afterPick && afterPick(); }}>
          <span className="brow-name">{b.name}</span>
          <span className="brow-bar"><span className="brow-fill" style={{ width: Math.max(7, (b.count / maxCount) * 100) + "%" }}/></span>
          <span className="brow-n">{b.count}</span>
        </button>
      ))}
    </>
  );

  // The collapsible "words rendered" card (English-gloss search → several lemmas).
  const renderSenses = () => (
    <div className={"glsenses" + (glOpen ? " open" : "")}>
      <button className="glsenses-head" aria-expanded={glOpen} onClick={() => setGlOpen(o => !o)}>
        <span className="glsenses-l">
          <b>{visibleGroupings.length}</b> {visibleGroupings.length === 1 ? "word" : "words"} rendered “{query.trim()}”
        </span>
        {!glOpen && profile && (
          <span className="glsenses-cur">
            <span className={"glsenses-cur-gk" + (isHeb ? " heb" : "")} dir={isHeb ? "rtl" : undefined}>{profile.lemma}</span>
            <span className="glsenses-cur-tr">{profile.translit}{occCount ? ` · ${occCount}` : ""}</span>
          </span>
        )}
        <span className="glsenses-tog">
          {glOpen ? "Collapse" : "Expand"}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </span>
      </button>
      {glOpen && (
        visibleGroupings.length === 0 ? (
          <div className="glsenses-empty">No {language === "greek" ? "Greek" : "Hebrew"} words rendered “{query.trim()}”.</div>
        ) : (
          <div className="glsenses-rows">
            {visibleGroupings.map(g => {
              const gh = g.strongs[0] === "H";
              return (
                <button key={g.strongs}
                  className={"glrow" + (profile && profile.strongs === g.strongs ? " on" : "")}
                  onClick={() => { loadProfile(g.strongs, corpus === "all" ? undefined : corpus); setGlOpen(false); }}>
                  <span className="glrow-s">{g.strongs}</span>
                  <span className="glrow-main">
                    <span className="glrow-top">
                      {g.lemma && <span className={"glrow-gk" + (gh ? " heb" : "")} dir={gh ? "rtl" : undefined}>{g.lemma}</span>}
                      {g.translit && <span className="glrow-tr">{g.translit}</span>}
                    </span>
                    {/* Each source line carries that Bible's TOTAL count for the number — matches
                        the count on the word's own study page. ABP spans OT+NT (LXX), KJV/BSB are
                        NT-only for a Greek word; for a Hebrew number HEB is the real Hebrew OT. */}
                    {g.abp_glosses && g.abp_glosses.length > 0 && (
                      <span className="glrow-rend"><span className="glrow-k">ABP</span><span>{g.abp_glosses.slice(0, 8).map(x => x.gloss).join(", ")}</span>{g.abp_total != null && <span className="glrow-n">{g.abp_total}</span>}</span>
                    )}
                    {g.heb_glosses && g.heb_glosses.length > 0 && (
                      <span className="glrow-rend"><span className="glrow-k">HEB</span><span>{g.heb_glosses.slice(0, 8).map(x => x.gloss).join(", ")}</span>{g.heb_total != null && <span className="glrow-n">{g.heb_total}</span>}</span>
                    )}
                    {g.kjv_glosses && g.kjv_glosses.length > 0 && (
                      <span className="glrow-rend"><span className="glrow-k">KJV</span><span>{g.kjv_glosses.slice(0, 8).map(x => x.gloss).join(", ")}</span>{g.kjv_total != null && <span className="glrow-n">{g.kjv_total}</span>}</span>
                    )}
                    {g.bsb_glosses && g.bsb_glosses.length > 0 && (
                      <span className="glrow-rend"><span className="glrow-k">BSB</span><span>{g.bsb_glosses.slice(0, 8).map(x => x.gloss).join(", ")}</span>{g.bsb_total != null && <span className="glrow-n">{g.bsb_total}</span>}</span>
                    )}
                  </span>
                  <span className="glrow-occ" title="Open word study">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
                  </span>
                </button>
              );
            })}
          </div>
        )
      )}
    </div>
  );

  // The word card body (hero + LSJ/BDB + ABP/KJV renderings + derivation + cognates).
  const renderWordCardInner = () => !profile ? null : (
    <>
      <div className="detail-hero">
        <div className="detail-hero-id">
          <div className={"detail-greek" + (isHeb ? " detail-greek--he" : "")} dir={isHeb ? "rtl" : undefined}>{profile.lemma}</div>
          {(profile.translit || firstGloss) && (
            <div className="detail-translit-row">
              {profile.translit && <span className="detail-translit">{profile.translit}</span>}
              {profile.translit && firstGloss && <span className="detail-sep">·</span>}
              {firstGloss && <span className="detail-gloss">{firstGloss}</span>}
            </div>
          )}
          <div className="detail-morph">{occCount} {occCount === 1 ? "occurrence" : "occurrences"}</div>
        </div>
      </div>

      {(profile.definition || /^G/i.test(profile.strongs)) && (
        <section className="sec">
          <h4 className="sec-head">
            <span className="sec-t">Definition</span>
            {!/^G/i.test(profile.strongs)
              ? <span className="bdb-badge">BDB</span>
              : (!lsjLoading && lsjEntry)
                ? <span className="lsj-badge">{lsjEntry.source === "strongs" ? "Strong's" : lsjEntry.source === "abp_ext" ? "ABP" : "LSJ"}</span>
                : null}
          </h4>
          {!/^G/i.test(profile.strongs)
            ? <p className="lsj">{profile.definition}</p>
            : lsjLoading
              ? <div className="lsj-def lsj-def--loading">Loading…</div>
              : !lsjEntry
                ? <p className="lsj">{profile.definition}</p>
                : <LsjBody lsjEntry={lsjEntry} lsjSummary={lsjSummary} summaryLoading={lsjSummaryLoading} />}
        </section>
      )}

      {profile.heb_glosses && profile.heb_glosses.length > 0 && (
        <section className="sec">
          <h4 className="sec-head"><span className="sec-t">Hebrew renders as</span></h4>
          {renderGlossLine("heb", null, profile.heb_glosses)}
        </section>
      )}
      {profile.abp_glosses && profile.abp_glosses.length > 0 && (
        <section className="sec">
          <h4 className="sec-head"><span className="sec-t">ABP renders as</span></h4>
          {renderGlossLine("abp", null, profile.abp_glosses)}
        </section>
      )}
      {profile.kjv_glosses && profile.kjv_glosses.length > 0 && (
        <section className="sec">
          <h4 className="sec-head"><span className="sec-t">KJV renders as</span></h4>
          {renderGlossLine("kjv", null, profile.kjv_glosses)}
        </section>
      )}
      {profile.bsb_glosses && profile.bsb_glosses.length > 0 && (
        <section className="sec">
          <h4 className="sec-head"><span className="sec-t">BSB renders as</span></h4>
          {renderGlossLine("bsb", null, profile.bsb_glosses)}
        </section>
      )}
      {profile.derivation && (
        <section className="sec">
          <h4 className="sec-head"><span className="sec-t">Derivation</span></h4>
          {/* Strong's zero-pads its cross-ref numbers (H07676); show them clean (H7676). */}
          <p className="root-note">{profile.derivation.replace(/\b([GH])0+(\d)/g, "$1$2")}</p>
        </section>
      )}
      {profile.related && profile.related.length > 0 && (
        <section className="sec">
          <h4 className="sec-head"><span className="sec-t">Cognates &amp; related lemmas</span></h4>
          <div className="related">
            {profile.related.map(r => (
              <button key={r.strongs} className="rel" onClick={() => loadProfile(r.strongs, "abp")}>
                <span className="rel-gk">{r.lemma}</span>
                <span className="rel-tr">{r.translit}</span>
                <span className="rel-gloss">{r.gloss}<span className="rel-s">{r.strongs}</span></span>
                <span className="rel-go" aria-hidden="true">›</span>
              </button>
            ))}
          </div>
        </section>
      )}
    </>
  );

  // ============================================================
  // MOBILE — context strip · reading area · bottom tools bar · sheets
  // (global nav stays at the top of the app; this is just the tab body)
  // ============================================================
  if (isMobile) {
    const tLabel = testament === "all" ? "All" : testament.toUpperCase();
    const occList = (
      !selectedBook ? <div className="occ-empty">Open <b>Distribution</b> below to pick a book.</div>
      : verseLoading ? <div className="occ-empty">Loading…</div>
      : (verseList && verseList[0] && verseList[0].error) ? <div className="occ-empty" style={{ color: "var(--danger, #b91c1c)" }}>{verseList[0].error}</div>
      : (verseList && verseList.length) ? (
        <div className="vlist">
          {verseList.map(v => (
            <VerseRow key={`${selectedBook}-${v.chapter}-${v.verse}`}
              book={selectedBook} chapter={v.chapter} verse={v.verse}
              label={`${selectedBook} ${v.chapter}:${v.verse}`}
              allResults={[]} onWordClick={onWordClick}
              onReadInContext={onNavigateToLibrary ? (b, c, vv) => onNavigateToLibrary(b, c, vv, profileCorpus) : undefined}
              textMode={profileCorpus === "kjv" ? "kjv" : profileCorpus === "heb" ? "heb" : profileCorpus === "bsb" ? "bsb" : "greek"}
              primaryStrongs={null} citedStrongs={citedStrongs} kjvCache={{}}/>
          ))}
        </div>
      ) : <div className="occ-empty">No verses.</div>
    );
    return (
      <div className="wm">
        {profile && (
          <button className="wm-ctx" onClick={() => setSheet("card")} aria-label="Open word card">
            <span className={"wm-ctx-gk" + (isHeb ? " heb" : "")} dir={isHeb ? "rtl" : undefined}>{profile.lemma}</span>
            <span className="wm-ctx-meta">
              <span className="wm-ctx-tr">{profile.translit}</span>
              {firstGloss && <><span className="wm-ctx-dot">·</span><span className="wm-ctx-gloss">{firstGloss}</span></>}
            </span>
            <span className="wm-ctx-go"><WsI.ChevR/></span>
          </button>
        )}

        <div className="wm-main">
          {error && <p className="lexicon-error">{error}</p>}
          {groupings && renderSenses()}
          {matches && !profile && (
            <div className="lexicon-matches">
              {matches.map(m => (
                <button key={m.strongs} className="lexicon-match-row" onClick={() => loadProfile(m.strongs)}>
                  <span className="lexicon-match-strongs">{m.strongs}</span>
                  <span className="lexicon-match-lemma">{m.lemma}</span>
                  <span className="lexicon-match-translit">{m.translit}</span>
                  <span className="lexicon-match-gloss">{m.gloss}</span>
                </button>
              ))}
            </div>
          )}
          {profile ? (
            <>
              <div className="wm-occhead">
                <span className="wm-occ-count">{selectedBook && selBookCount != null ? selBookCount : occCount}</span>
                <span className="wm-occ-lbl">{selectedBook ? "in " + selBookName : (occCount === 1 ? "occurrence" : "occurrences")}</span>
                <span className="wm-occ-meta">{tLabel} · {profileCorpus.toUpperCase()}</span>
              </div>
              {occList}
            </>
          ) : (loading && !groupings && !matches) ? (
            <div className="wm-searching"><span className="wm-searching-spin"/>Searching…</div>
          ) : (!groupings && !matches && !error) ? (
            <div className="occ-welcome">
              <div className="occ-welcome-t">Greek &amp; Hebrew word study</div>
              <form className="wm-search wm-welcome-search" onSubmit={handleSubmit}>
                <WsI.Search className="wm-search-i"/>
                <input className="wm-search-input" type="text" value={query}
                  onChange={e => setQuery(e.target.value)} enterKeyHint="search"
                  placeholder="Word, transliteration, Strong's…"/>
                {query && <button type="button" className="wm-search-clear" onClick={() => setQuery("")} aria-label="Clear"><WsI.Close/></button>}
              </form>
              <div className="occ-welcome-s">Search a word, transliteration, or Strong's number — or tap a sample.</div>
              <div className="occ-welcome-chips">
                {["πνεῦμα", "pistis", "G26", "spirit"].map(q => (
                  <button key={q} className="welcome-chip" onClick={() => handleSubmit(null, q)}>{q}</button>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <nav className="wm-tabs" aria-label="Word study tools">
          <button className={"wm-tab" + (sheet === "search" ? " on" : "")} onClick={() => setSheet("search")} title="Search" aria-label="Search">
            <WsI.Search/>
          </button>
          <button className={"wm-tab" + (sheet === "dist" ? " on" : "")} disabled={!profile} onClick={() => setSheet("dist")} title="Distribution" aria-label="Distribution">
            <WsI.Book/>
          </button>
          <button className={"wm-tab" + (sheet === "card" ? " on" : "")} disabled={!profile} onClick={() => setSheet("card")} title="Word card" aria-label="Word card">
            <WsI.Card/>
          </button>
          <button className={"wm-tab" + (sheet === "views" ? " on" : "")} disabled={!profile} onClick={() => setSheet("views")} title="Views" aria-label="Views">
            <WsI.Sliders/>
          </button>
        </nav>

        {sheet === "dist" && (
          <WsSheet tall title={profile ? "Distribution · " + profile.translit : "Distribution"} onClose={() => setSheet(null)}>
            <div className="wm-rail">{renderDistRows(() => setSheet(null))}</div>
          </WsSheet>
        )}
        {sheet === "card" && (
          <WsSheet tall title={profile ? profile.strongs : "Word card"} titleMono hideClose onClose={() => setSheet(null)}>
            <div className="wm-card">{renderWordCardInner()}</div>
          </WsSheet>
        )}
        {sheet === "views" && (
          <WsSheet title="Views" onClose={() => setSheet(null)}>
            <div className="mode-sec">
              <div className="mode-lbl">Edition</div>
              <div className="mseg">
                <button className={"mseg-b" + (profileCorpus === "abp" ? " on" : "")} disabled={!profile?.has_abp} onClick={() => switchProfileCorpus("abp")}>ABP</button>
                {isHeb && <button className={"mseg-b" + (profileCorpus === "heb" ? " on" : "")} disabled={!profile?.has_heb} onClick={() => switchProfileCorpus("heb")}>HEB</button>}
                <button className={"mseg-b" + (profileCorpus === "kjv" ? " on" : "")} disabled={!profile?.has_kjv} onClick={() => switchProfileCorpus("kjv")}>KJV</button>
                <button className={"mseg-b" + (profileCorpus === "bsb" ? " on" : "")} disabled={!profile?.has_bsb} onClick={() => switchProfileCorpus("bsb")}>BSB</button>
              </div>
            </div>
            <div className="mode-sec">
              <div className="mode-lbl">Testament</div>
              <div className="mseg">
                {[["all", "All"], ["ot", "Old"], ["nt", "New"]].map(([k, l]) => (
                  <button key={k} className={"mseg-b" + (testament === k ? " on" : "")} onClick={() => switchTestament(k)}>{l}</button>
                ))}
              </div>
            </div>
            {profile && onAskWord && (
              <div className="mode-sec">
                <div className="mode-lbl">Go deeper</div>
                <button className="wm-jump" onClick={() => { setSheet(null); onAskWord(profile.strongs, profile.lemma, profile.translit); }}>
                  <Icon.Sparkle/> Ask the corpus about <span className={"wm-jump-w" + (isHeb ? " heb" : "")} dir={isHeb ? "rtl" : undefined}>{profile.lemma}</span> <Icon.ArrowRight/>
                </button>
              </div>
            )}
          </WsSheet>
        )}
        {sheet === "search" && (
          <WsSheet title="Search" onClose={() => setSheet(null)}>
            <div className="wm-searchsheet">
              <form className="wm-search" onSubmit={(e) => { setSheet(null); handleSubmit(e); }}>
                <WsI.Search className="wm-search-i"/>
                <input className="wm-search-input" type="text" value={query} autoFocus
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Word, transliteration, Strong's…"/>
                {query && <button type="button" className="wm-search-clear" onClick={() => setQuery("")} aria-label="Clear"><WsI.Close/></button>}
              </form>
              <div className="wm-search-hint">Greek, Hebrew, a transliteration, an English gloss, or a Strong's number.</div>
              <div className="wm-search-chips">
                {["πνεῦμα", "pistis", "G26", "spirit", "ἀγάπη", "H7307"].map(q => (
                  <button key={q} className="welcome-chip" onClick={() => { setSheet(null); handleSubmit(null, q); }}>{q}</button>
                ))}
              </div>
            </div>
          </WsSheet>
        )}
      </div>
    );
  }

  return (
    <div className={"ws" + (isMobile ? " is-mobile" : "")}>

      {/* LEFT — distribution rail (empty state before a word is studied) */}
      {isMobile && railOpen && <div className="rail-scrim" onClick={() => setRailOpen(false)}/>}
      <aside className={"brail" + (isMobile && !railOpen ? " hidden" : "")}>
        {profile ? (
          <>
            <div className="brail-top">
              <div className="brail-eyebrow">Distribution by book</div>
              <div className="brail-sub"><span className="brail-gk" dir={isHeb ? "rtl" : undefined}>{profile.lemma}</span> · {profile.books.length} {profile.books.length === 1 ? "book" : "books"}</div>
            </div>
            <div className="brail-scroll">{renderDistRows()}</div>
          </>
        ) : (
          <>
            <div className="brail-top"><div className="brail-eyebrow">Distribution by book</div></div>
            <div className="brail-empty">The books a word appears in show here once you study it.</div>
          </>
        )}
      </aside>

      {/* CENTER — search + occurrences / results */}
      <main className="center">
        <div className="searchbar">
          <div className="searchbar-in">
            <form className="search-field" onSubmit={handleSubmit}>
              <Icon.Search className="search-i"/>
              <input className="search-input" type="text" value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="A word, transliteration, or Strong's №…" autoFocus/>
              <button type="submit" className="search-go" aria-label="Search" disabled={loading}>
                {loading ? <span className="spinner"/> : <Icon.ArrowRight/>}
              </button>
            </form>
            {profile && onAskWord && (
              <button type="button" className="searchbar-ask" onClick={() => onAskWord(profile.strongs, profile.lemma, profile.translit)}>
                <Icon.Sparkle/><span>Ask AI about <span dir={isHeb ? "rtl" : undefined}>{profile.lemma}</span></span><Icon.ArrowRight/>
              </button>
            )}
          </div>
        </div>

        <div className="results-scroll">
          <div className="results-col">
            {isMobile && profile && (
              <div className="ws-mobi">
                <button className="ws-mobi-b" onClick={() => setRailOpen(true)}>≣ Distribution</button>
                <button className="ws-mobi-b" onClick={() => setDetailOpen(true)}>▭ Word card</button>
              </div>
            )}

            {error && <p className="lexicon-error">{error}</p>}

            {/* search-results toolbar (no word in focus) */}
            {!profile && (groupings || matches) && (
              <div className="filters">
                <div className="tgroup">
                  <button className={"tg" + (corpus === "all" ? " on" : "")} onClick={() => switchCorpus("all")}>All</button>
                  <button className={"tg" + (corpus === "abp" ? " on" : "")} disabled={!_comboOK("abp", testament, language)} onClick={() => switchCorpus("abp")}>ABP</button>
                  <button className={"tg" + (corpus === "heb" ? " on" : "")} disabled={!_comboOK("heb", testament, language)} onClick={() => switchCorpus("heb")}>HEB</button>
                  <button className={"tg" + (corpus === "kjv" ? " on" : "")} disabled={!_comboOK("kjv", testament, language)} onClick={() => switchCorpus("kjv")}>KJV</button>
                  <button className={"tg" + (corpus === "bsb" ? " on" : "")} disabled={!_comboOK("bsb", testament, language)} onClick={() => switchCorpus("bsb")}>BSB</button>
                </div>
                <span className="filters-sep"/>
                <div className="tgroup">
                  {["all","ot","nt"].map(t => (
                    <button key={t} className={"tg" + (testament === t ? " on" : "")}
                      disabled={t !== "all" && !_comboOK(corpus, t, language)}
                      onClick={() => switchTestament(t)}>{t === "all" ? "All" : t.toUpperCase()}</button>
                  ))}
                </div>
                <span className="filters-sep"/>
                <div className="tgroup">
                  <button className={"tg" + (language === "all" ? " on" : "")} onClick={() => switchLanguage("all")}>All</button>
                  <button className={"tg" + (language === "greek" ? " on" : "")} disabled={!_comboOK(corpus, testament, "greek")} onClick={() => switchLanguage("greek")}>Greek</button>
                  <button className={"tg" + (language === "hebrew" ? " on" : "")} disabled={!_comboOK(corpus, testament, "hebrew")} onClick={() => switchLanguage("hebrew")}>Hebrew</button>
                </div>
              </div>
            )}

            {matches && !profile && (
              <div className="lexicon-matches">
                {matches.map(m => (
                  <button key={m.strongs} className="lexicon-match-row" onClick={() => loadProfile(m.strongs)}>
                    <span className="lexicon-match-strongs">{m.strongs}</span>
                    <span className="lexicon-match-lemma">{m.lemma}</span>
                    <span className="lexicon-match-translit">{m.translit}</span>
                    <span className="lexicon-match-gloss">{m.gloss}</span>
                  </button>
                ))}
              </div>
            )}

            {/* English "words rendered" results — a collapsible card that stays
                pinned above the occurrences once a word is picked. */}
            {groupings && renderSenses()}
            {groupings && !profile && onAiSearch && (
              <button className="lexicon-ask-instead" onClick={() => onAiSearch(query.trim())}>
                Or ask the corpus about “{query.trim()}” →
              </button>
            )}

            {/* occurrences (word in focus) */}
            {profile && (
              <>
                <div className="filters">
                  <div className="tgroup">
                    {[["all","All"],["ot","OT"],["nt","NT"]].map(([k, l]) => (
                      <button key={k} className={"tg" + (testament === k ? " on" : "")} onClick={() => switchTestament(k)}>{l}</button>
                    ))}
                  </div>
                  <span className="filters-sep"/>
                  <div className="tgroup">
                    <button className={"tg" + (profileCorpus === "abp" ? " on" : "")} disabled={!profile.has_abp} onClick={() => switchProfileCorpus("abp")}>ABP</button>
                    {isHeb && <button className={"tg" + (profileCorpus === "heb" ? " on" : "")} disabled={!profile.has_heb} onClick={() => switchProfileCorpus("heb")}>HEB</button>}
                    <button className={"tg" + (profileCorpus === "kjv" ? " on" : "")} disabled={!profile.has_kjv} onClick={() => switchProfileCorpus("kjv")}>KJV</button>
                    <button className={"tg" + (profileCorpus === "bsb" ? " on" : "")} disabled={!profile.has_bsb} onClick={() => switchProfileCorpus("bsb")}>BSB</button>
                  </div>
                </div>

                {selectedBook ? (
                  <div className="occ-filter">
                    <span>Showing <b>{selBookName}</b>{selBookCount != null ? ` · ${selBookCount} occurrence${selBookCount === 1 ? "" : "s"}` : ""}{selectedGloss ? ` · rendered “${selectedGloss}”` : ""}</span>
                    <button className="occ-reset" onClick={() => { setSelectedBook(null); setVerseList(null); setBookGlosses(null); }}>All books</button>
                  </div>
                ) : null}

                {!selectedBook ? (
                  <div className="occ-empty">Pick a book at left to read its occurrences.</div>
                ) : verseLoading ? (
                  <div className="occ-empty">Loading…</div>
                ) : (verseList && verseList[0] && verseList[0].error) ? (
                  <div className="occ-empty" style={{ color: "var(--danger, #b91c1c)" }}>{verseList[0].error}</div>
                ) : (verseList && verseList.length) ? (
                  <div className="vlist">
                    {verseList.map(v => (
                      <VerseRow
                        key={`${selectedBook}-${v.chapter}-${v.verse}`}
                        book={selectedBook} chapter={v.chapter} verse={v.verse}
                        label={`${selectedBook} ${v.chapter}:${v.verse}`}
                        allResults={[]}
                        onWordClick={onWordClick}
                        onReadInContext={onNavigateToLibrary ? (b, c, vv) => onNavigateToLibrary(b, c, vv, profileCorpus) : undefined}
                        textMode={profileCorpus === "kjv" ? "kjv" : profileCorpus === "heb" ? "heb" : profileCorpus === "bsb" ? "bsb" : "greek"}
                        primaryStrongs={null}
                        citedStrongs={citedStrongs}
                        kjvCache={{}}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="occ-empty">No verses.</div>
                )}
              </>
            )}

            {/* welcome (nothing yet) */}
            {!profile && !groupings && !matches && !error && (
              <div className="occ-welcome">
                <div className="occ-welcome-t">Greek &amp; Hebrew word study</div>
                <div className="occ-welcome-s">Search a word, transliteration, or Strong's number to study its senses, derivation, and every place it occurs.</div>
                <div className="occ-welcome-chips">
                  {["πνεῦμα", "pistis", "G26", "spirit"].map(q => (
                    <button key={q} className="welcome-chip" onClick={() => handleSubmit(null, q)}>{q}</button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* RIGHT — word detail card (empty state before a word is studied) */}
      {isMobile && detailOpen && <div className="wd-scrim" onClick={() => setDetailOpen(false)}/>}
      <aside className={"wd" + (isMobile && !detailOpen ? " hidden" : "")}>
        {profile ? (
          <>
          <div className="detail-head">
            <span className="detail-strong-head">{profile.strongs}</span>
            {(groupings || matches) && (
              <button className="detail-back" onClick={backToResults}>‹ Results</button>
            )}
          </div>
          <div className="detail-body">{renderWordCardInner()}</div>
          </>
        ) : (
          <div className="empty-pane">
            <div className="empty-mark"><Icon.Book width="30" height="30"/></div>
            <div className="empty-t">No word selected</div>
            <div className="empty-s">Search a Greek or Hebrew word, a transliteration, or a Strong's number to study it here.</div>
          </div>
        )}
      </aside>
    </div>
  );
}
