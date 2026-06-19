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
  if (corpus === "kjv") return testament !== "ot";   // KJV: Greek only in the NT
  return true;                                         // ABP / All: always some Greek
}
function _sliceHasHebrew(corpus, testament) {
  if (corpus === "abp") return false;                 // ABP is all Greek
  return testament !== "nt";                           // KJV / All: Hebrew only outside the NT
}
function _comboOK(corpus, testament, language) {
  if (language === "greek")  return _sliceHasGreek(corpus, testament);
  if (language === "hebrew") return _sliceHasHebrew(corpus, testament);
  return true;
}

// ============================================================
// WORD STUDY — MOBILE BOTTOM COCKPIT + SHEETS
// ============================================================
// Mirrors the library's mobile chrome: the verses ARE the page, and a fixed
// bottom cockpit (thumb zone) opens the side content as bottom sheets. Left
// button = Analysis (the desktop RIGHT rail), middle = Word (the desktop LEFT
// rail), right = Options (filters / settings).
function WsCockpit({ open, setOpen }) {
  const btn = (id, icon, label) => (
    <button className={"ws-cockpit-btn" + (open === id ? " on" : "")}
      aria-label={label} aria-pressed={open === id}
      onClick={() => setOpen(open === id ? null : id)}>
      {icon}<span className="ws-cockpit-lbl">{label}</span>
    </button>
  );
  return (
    <div className="ws-cockpit">
      {btn("analysis", <Icon.Panel/>, "Analysis")}
      {btn("word", <Icon.Book/>, "Word")}
      {btn("options", <Icon.Filter/>, "Options")}
    </div>
  );
}

// One library-style bottom sheet (scrim + swipe-to-dismiss), reusing the
// reading-options sheet styling (.msheet / .msheet-head / .msheet-body).
function WsSheet({ title, onClose, children }) {
  const { sheetRef, scrollRef } = useSwipeToDismiss(onClose);
  return (
    <>
      <div className="sheet-scrim" onClick={onClose} />
      <div className="msheet ws-sheet" ref={sheetRef}>
        <div className="sheet-drag-zone" aria-hidden="true"><div className="sheet-handle"></div></div>
        <div className="msheet-head">
          <span className="msheet-title">{title}</span>
          <button className="msheet-x" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="msheet-body" ref={scrollRef}>{children}</div>
      </div>
    </>
  );
}

function LexiconView({ onNavigateToLibrary, onWordClick, pendingStrongs, onPendingStrongsConsumed, isMobile, onAiSearch, onExitAi, aiActive, ai }) {
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
  const [showDef, setShowDef] = useState(false);
  const [lsjEntry, setLsjEntry] = useState(null);
  const [lsjSummary, setLsjSummary] = useState(null);
  const [lsjLoading, setLsjLoading] = useState(false);
  const [lsjSummaryLoading, setLsjSummaryLoading] = useState(false);
  const [sheet, setSheet] = useState(null);   // mobile bottom sheet open: null | "word" | "analysis" | "options"

  // Reset the curated LSJ definition whenever the focused word changes.
  useEffect(() => { setLsjEntry(null); setLsjSummary(null); }, [profile?.strongs]);

  // Lazily fetch the LSJ entry + AI-curated summary when the Greek definition is
  // opened (Haiku, cached). Hebrew keeps its BDB definition. The /api/lsj endpoint
  // auto-falls back to strongs_def when there's no LSJ match.
  useEffect(() => {
    if (!showDef || !profile || !/^G/i.test(profile.strongs) || lsjEntry || lsjLoading) return;
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
    onExitAi?.();   // drilling into a word leaves any AI answer behind
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
    const isHeb = /^H/i.test(strongs) || (!(/^[GgHh]/.test(strongs)) && parseInt(strongs) > 5624);
    const c = corpusOverride ?? (isHeb ? "kjv" : "abp");  // drilling in always lands in a single corpus
    setProfileCorpus(c);
    try {
      const data = await api.lexiconProfile(strongs, c);
      if (data.error) setError(data.error);
      else setProfile(data);
    } catch (e) { setError("Failed to load word profile: " + e); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (profile && pendingGloss) {
      selectGloss(pendingGloss);
      setPendingGloss(null);
    }
  }, [profile, pendingGloss]);

  // Lead with the verses: when a word loads (or the testament filter changes) and
  // no book is chosen yet, auto-open the book with the most occurrences so the
  // center fills with verses immediately instead of sitting blank. Everything else
  // stays user-driven (the distribution list re-picks the book).
  useEffect(() => {
    if (!profile || loading || selectedBook) return;
    const books = (filteredBooks || profile.books || [])
      .filter(b => testament === "all" || (b.testament || "").toLowerCase() === testament);
    if (!books.length) return;
    const top = books.reduce((a, b) => (b.count > a.count ? b : a));
    selectBook(top.book);
  }, [profile, loading, selectedBook, testament, filteredBooks]);

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
    setShowDef(false);
    try {
      const data = await api.lexiconProfile(profile.strongs, c);
      if (!data.error) setProfile(data);
    } catch {}
    finally { setLoading(false); }
  };

  const switchTestament = async (t) => {
    if (loading) return;
    if (!profile && t !== "all" && !_comboOK(corpus, t, language)) return;  // grayed combo (results view only)
    setTestament(t);
    setSelectedBook(null);
    setVerseList(null);
    // Profile view filters its distribution + count on `testament` client-side
    // (the auto-select effect then re-opens the top book within that testament).
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
        <div className="lexicon-gloss-label">{label}</div>
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
    const tag = profile.strongs;
    const base = tag.split(".")[0];
    return new Set([tag, base, base.replace(/^[GH]/i, "")]);
  }, [profile?.strongs]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setProfile(null);
    setMatches(null);
    setGroupings(null);
    setError(null);
    setSheet(null);
    // Plain-language question / phrase → hand the box over to the corpus AI.
    if (onAiSearch && !_STRONGS_RE.test(q) && !_isGreekHebrew(q) && _looksLikeQuestion(q)) {
      onAiSearch(q);
      return;
    }
    onExitAi?.();   // any other route is a word lookup — leave AI mode
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
        if (data.length) { setGroupings(data); }
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

  // ----------------------------------------------------------------
  // Focused-word pieces — defined once, placed in the desktop rails OR
  // the mobile sheets (only one branch renders, so no element reuse).
  // ----------------------------------------------------------------
  const displayCount = !profile ? 0 : (
    testament === "all"
      ? profile.total
      : (filteredBooks || profile.books).filter(b => (b.testament || "").toLowerCase() === testament).reduce((s, b) => s + b.count, 0)
  );
  const hasResultsToReturn = !!(groupings || matches);
  const curBookName = profile && selectedBook
    ? (profile.books.find(b => b.book === selectedBook)?.name || selectedBook)
    : null;
  const backToResults = () => { setProfile(null); setSelectedBook(null); setVerseList(null); setSheet(null); };

  const idHead = () => (
    <div className="ws-id-head">
      <span className="lexicon-lemma" dir={profile.strongs[0] === "H" ? "rtl" : undefined}>{profile.lemma}</span>
      <span className="lexicon-translit">{profile.translit}</span>
      <div className="ws-id-meta">
        <span className="lexicon-strongs-tag">{profile.strongs}</span>
        <span className="lexicon-total">{displayCount} occurrences</span>
      </div>
    </div>
  );

  const askBtn = () => onAiSearch ? (
    <button className="lexicon-ask-corpus" onClick={() => { const aq = `How is ${profile.translit || profile.lemma} (${profile.strongs}) used in scripture?`; setQuery(aq); setSheet(null); onAiSearch(aq); }}>
      <Icon.Sparkle/> Ask the corpus about {profile.lemma}
    </button>
  ) : null;

  const defSection = () => (profile.definition || /^G/i.test(profile.strongs)) ? (
    <div className="lexicon-def-section">
      <button className="lexicon-def-toggle" onClick={() => setShowDef(v => !v)}>
        Definition
        {showDef && (!/^G/i.test(profile.strongs)
          ? <span className="lexicon-def-src">BDB</span>
          : (!lsjLoading && lsjEntry)
            ? <span className="lexicon-def-src">{lsjEntry.source === "strongs" ? "Strong's" : lsjEntry.source === "abp_ext" ? "ABP" : "LSJ"}</span>
            : null)}
        {" "}{showDef ? "▲" : "▼"}
      </button>
      {showDef && (
        !/^G/i.test(profile.strongs)
          ? <p className="lexicon-definition">{profile.definition}</p>     /* Hebrew: BDB */
          : lsjLoading
            ? <div className="lsj-def lsj-def--loading">Loading…</div>
            : !lsjEntry
              ? <p className="lexicon-definition">{profile.definition}</p>  /* no LSJ: strongs_def */
              : lsjEntry.source === "strongs"
                ? <div className="lsj-def" dangerouslySetInnerHTML={{ __html: lsjEntry.def_html }} />
                : lsjSummaryLoading
                  ? <LsjSummary data={null} loading={true} />
                  : (lsjSummary && lsjSummary.summary)
                    ? <LsjSummary data={lsjSummary} loading={false} />
                    : <div className="lsj-def" dangerouslySetInnerHTML={{ __html: lsjEntry.def_html }} />  /* AI down: raw LSJ */
      )}
    </div>
  ) : null;

  const inThisBook = () => (selectedBook && (bookGlosses || profile.glosses) && (bookGlosses || profile.glosses).length > 0) ? (
    <div className="lexicon-glosses">
      <div className="lexicon-gloss-label">In this book</div>
      <div className="lexicon-dist-list">
        {(bookGlosses || profile.glosses).map((g, i) => (
          <React.Fragment key={g.gloss}>
            {i > 0 && <span className="lexicon-dist-sep"> · </span>}
            <button
              className={"lexicon-dist-item" + (selectedGloss === g.gloss ? " selected" : "")}
              onClick={() => selectGloss(g.gloss)}
            >
              {g.gloss}<span className="lexicon-dist-count">{g.count}</span>
            </button>
          </React.Fragment>
        ))}
      </div>
    </div>
  ) : null;

  // RIGHT-rail analysis: the whole-corpus renderings + the book distribution.
  const rendersAnalysis = () => (
    <>
      {renderGlossLine("abp", "ABP renders this as", profile.abp_glosses)}
      {renderGlossLine("kjv", "KJV renders this as", profile.kjv_glosses)}
    </>
  );

  const distribution = (afterPick) => (
    <div className="lexicon-distribution">
      <div className="lexicon-dist-header">
        <div className="lexicon-dist-label">Distribution by book</div>
      </div>
      <div className="lexicon-dist-list">
        {(filteredBooks || profile.books)
          .filter(b => testament === "all" || (b.testament || "").toLowerCase() === testament)
          .map((b, i) => (
            <React.Fragment key={b.book}>
              {i > 0 && <span className="lexicon-dist-sep"> · </span>}
              <button
                className={"lexicon-dist-item" + (selectedBook === b.book ? " selected" : "")}
                onClick={() => { selectBook(b.book); afterPick && afterPick(); }}
              >
                {b.name}<span className="lexicon-dist-count">{b.count}</span>
              </button>
            </React.Fragment>
          ))}
      </div>
    </div>
  );

  // ABP|KJV corpus toggle for a focused word (segmented; matches the sheet look
  // when `seg` is true, the desktop pill look otherwise).
  const corpusToggle = (seg, afterPick) => {
    const cls = seg ? "mseg-b" : "lct-btn";
    return (
      <div className={seg ? "mseg" : "lexicon-corpus-toggle"}>
        <button className={cls + (profileCorpus === "abp" ? " on" : "")} disabled={!profile.has_abp} onClick={() => { switchProfileCorpus("abp"); afterPick && afterPick(); }}>ABP</button>
        <button className={cls + (profileCorpus === "kjv" ? " on" : "")} disabled={!profile.has_kjv} onClick={() => { switchProfileCorpus("kjv"); afterPick && afterPick(); }}>KJV</button>
      </div>
    );
  };

  const testamentToggle = (seg, afterPick) => {
    const cls = seg ? "mseg-b" : "lct-btn";
    return (
      <div className={seg ? "mseg" : "lexicon-corpus-toggle"}>
        {["all", "ot", "nt"].map(t => (
          <button key={t} className={cls + (testament === t ? " on" : "")} onClick={() => { switchTestament(t); afterPick && afterPick(); }}>
            {t === "all" ? "All" : t.toUpperCase()}
          </button>
        ))}
      </div>
    );
  };

  // CENTER: the verse occurrences for the open book, in the reader's cards.
  const versesBody = () => (
    !selectedBook ? (
      <div className="lexicon-verse-loading">Pick a book to see its verses.</div>
    ) : verseLoading ? (
      <div className="lexicon-verse-loading">Loading…</div>
    ) : (verseList && verseList[0] && verseList[0].error) ? (
      <div className="lexicon-verse-loading" style={{ color: "red" }}>{verseList[0].error}</div>
    ) : (verseList && verseList.length) ? (
      <CorpusGroup
        label={curBookName}
        verses={verseList.map(v => ({ book: selectedBook, chapter: v.chapter, verse: v.verse, ref: `${selectedBook} ${v.chapter}:${v.verse}` }))}
        allResults={[]}
        onWordClick={onWordClick}
        onReadInContext={onNavigateToLibrary ? (b, c, vv) => onNavigateToLibrary(b, c, vv, profileCorpus) : undefined}
        textMode={profileCorpus === "kjv" ? "kjv" : "greek"}
        primaryStrongs={null}
        citedStrongs={citedStrongs}
        kjvCache={{}}
      />
    ) : (
      <div className="lexicon-verse-loading">No verses.</div>
    )
  );

  const searchHeader = (
    <section className="search ws-search">
      <div className="search-cell">
        <label className="search-label">
          <span className="search-eyebrow">Search</span>
        </label>
        <form className="search-field" onSubmit={handleSubmit}>
          <Icon.Search className="search-icon"/>
          <input
            className="search-input"
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="A word, a Strong's number, or a question…"
            autoFocus
          />
          <button type="submit" className="search-go" aria-label="Search" disabled={loading}>
            {loading ? <span className="spinner"/> : <Icon.ArrowRight/>}
          </button>
        </form>
        <div className="lexicon-search-hint">One word looks it up · a question asks the corpus</div>
      </div>
    </section>
  );

  return (
    <div className={"lexicon-view" + (profile && !aiActive ? " ws-profile" : "")}>
      {searchHeader}

      {aiActive ? (
        <AiResults {...ai} />
      ) : profile ? (
        isMobile ? (
          /* ---------- MOBILE: verses are the page; cockpit opens the rest ---------- */
          <>
            <div className="ws-mini-head">
              {hasResultsToReturn && (
                <button className="ws-mini-back" onClick={backToResults} aria-label={`Back to "${query.trim()}" results`}>←</button>
              )}
              <span className="ws-mini-lemma" dir={profile.strongs[0] === "H" ? "rtl" : undefined}>{profile.lemma}</span>
              {profile.translit && <span className="ws-mini-translit">{profile.translit}</span>}
              <span className="lexicon-strongs-tag">{profile.strongs}</span>
              {curBookName && <span className="ws-mini-book">{curBookName}</span>}
            </div>

            <div className="ws-verses ws-verses-mobile">{versesBody()}</div>

            <WsCockpit open={sheet} setOpen={setSheet} />

            {sheet === "word" && (
              <WsSheet title="Word" onClose={() => setSheet(null)}>
                <div className="ws-sheet-pad">
                  {idHead()}
                  {askBtn()}
                  {defSection()}
                  {inThisBook()}
                </div>
              </WsSheet>
            )}
            {sheet === "analysis" && (
              <WsSheet title="Analysis" onClose={() => setSheet(null)}>
                <div className="ws-sheet-pad">
                  {rendersAnalysis()}
                  {distribution(() => setSheet(null))}
                </div>
              </WsSheet>
            )}
            {sheet === "options" && (
              <WsSheet title="Options" onClose={() => setSheet(null)}>
                <div className="mode-sec"><div className="mode-lbl">Text</div>{corpusToggle(true, () => setSheet(null))}</div>
                <div className="mode-sec"><div className="mode-lbl">Testament</div>{testamentToggle(true, () => setSheet(null))}</div>
              </WsSheet>
            )}
          </>
        ) : (
          /* ---------- DESKTOP: three columns (identity / verses / analysis) ---------- */
          <div className="ws-grid">
            <aside className="ws-rail ws-identity">
              {hasResultsToReturn && (
                <button className="ws-back" onClick={backToResults} title={`Back to "${query.trim()}" results`}>← results</button>
              )}
              {idHead()}
              {corpusToggle(false)}
              {askBtn()}
              {defSection()}
              {inThisBook()}
            </aside>

            <div className="ws-verses">
              <div className="ws-verses-head">
                <span className="ws-verses-title">{curBookName || "Verses"}</span>
                {testamentToggle(false)}
              </div>
              {versesBody()}
            </div>

            <aside className="ws-rail ws-analysis">
              {rendersAnalysis()}
              {distribution()}
            </aside>
          </div>
        )
      ) : (
        /* ---------- EMPTY / RESULTS LIST / DISAMBIGUATION — single column ---------- */
        <>
          <div className="lexicon-toolbar">
            <div className="lexicon-corpus-toggle">
              <button className={"lct-btn" + (corpus === "all" ? " on" : "")} onClick={() => switchCorpus("all")}>All</button>
              <button className={"lct-btn" + (corpus === "abp" ? " on" : "")} disabled={!_comboOK("abp", testament, language)} onClick={() => switchCorpus("abp")}>ABP</button>
              <button className={"lct-btn" + (corpus === "kjv" ? " on" : "")} disabled={!_comboOK("kjv", testament, language)} onClick={() => switchCorpus("kjv")}>KJV</button>
            </div>
            <div className="lexicon-corpus-toggle">
              {["all","ot","nt"].map(t => (
                <button key={t} className={"lct-btn" + (testament === t ? " on" : "")}
                  disabled={t !== "all" && !_comboOK(corpus, t, language)}
                  onClick={() => switchTestament(t)}>
                  {t === "all" ? "All" : t.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="lexicon-corpus-toggle">
              <button className={"lct-btn" + (language === "all" ? " on" : "")} onClick={() => switchLanguage("all")}>All</button>
              <button className={"lct-btn" + (language === "greek" ? " on" : "")} disabled={!_comboOK(corpus, testament, "greek")} onClick={() => switchLanguage("greek")}>Greek</button>
              <button className={"lct-btn" + (language === "hebrew" ? " on" : "")} disabled={!_comboOK(corpus, testament, "hebrew")} onClick={() => switchLanguage("hebrew")}>Hebrew</button>
            </div>
          </div>

          {error && <p className="lexicon-error">{error}</p>}

          {matches && (
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

          {groupings && (
            <div className="lexicon-results">
              <div className="lexicon-dist-label">
                rendered as "{query.trim()}" · {visibleGroupings.length} {visibleGroupings.length === 1 ? "word" : "words"}
              </div>
              {onAiSearch && (
                <button className="lexicon-ask-instead" onClick={() => { setQuery(query.trim()); onAiSearch(query.trim()); }}>
                  Or ask the corpus about "{query.trim()}" →
                </button>
              )}
              {visibleGroupings.length === 0 ? (
                <div className="lexicon-dist-label">No {language === "greek" ? "Greek" : "Hebrew"} words rendered "{query.trim()}".</div>
              ) : visibleGroupings.map(g => (
                <button key={g.strongs} className="lexicon-result-row"
                  onClick={() => loadProfile(g.strongs, corpus === "all" ? undefined : corpus)}>
                  <span className="lexicon-result-topbar">
                    <span className="lexicon-result-head">
                      <span className="lexicon-match-strongs">{g.strongs}</span>
                      {g.lemma && <span className="lexicon-match-lemma" dir={g.strongs[0] === "H" ? "rtl" : undefined}>{g.lemma}</span>}
                      {g.translit && <span className="lexicon-match-translit">{g.translit}</span>}
                    </span>
                    <span className="lexicon-result-end">
                      <span className="lexicon-result-count">{g.count}</span>
                      <span className="lexicon-result-chev">›</span>
                    </span>
                  </span>
                  <span className="lexicon-result-preview">{renderRowPreview(g)}</span>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
