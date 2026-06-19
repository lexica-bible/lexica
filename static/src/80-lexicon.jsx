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

// The book with the most occurrences — auto-opened on profile load so the
// center column shows verses immediately instead of an empty "pick a book".
function _topBook(books) {
  if (!books || !books.length) return null;
  return books.reduce((a, b) => (b.count > a.count ? b : a)).book;
}

function LexiconView({ onNavigateToLibrary, onWordClick, pendingStrongs, onPendingStrongsConsumed, isMobile, onAiSearch, onAskWord }) {
  const [railOpen, setRailOpen] = useState(false);     // mobile: distribution drawer
  const [detailOpen, setDetailOpen] = useState(false); // mobile: word-card drawer
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
      else { setProfile(data); await _openTopBook(data, c); }
    } catch (e) { setError("Failed to load word profile: " + e); }
    finally { setLoading(false); }
  };

  // Load the busiest book's verses straight into the center (used on profile
  // load + corpus switch, where `profile`/`profileCorpus` state is still stale).
  const _openTopBook = async (data, c) => {
    const tb = _topBook(data.books);
    if (!tb) { setSelectedBook(null); setVerseList(null); return; }
    setSelectedBook(tb);
    setVerseLoading(true);
    try {
      const vd = await api.lexiconVerses(data.strongs, tb, c, null);
      if (vd.error) setVerseList([{ error: vd.error }]);
      else { setVerseList(vd.verses || []); setBookGlosses(vd.glosses && vd.glosses.length ? vd.glosses : null); }
    } catch (e) { setVerseList([{ error: String(e) }]); }
    finally { setVerseLoading(false); }
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
    setShowDef(false);
    try {
      const data = await api.lexiconProfile(profile.strongs, c);
      if (!data.error) { setProfile(data); await _openTopBook(data, c); }
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
    const tag = profile.strongs;
    const base = tag.split(".")[0];
    return new Set([tag, base, base.replace(/^[GH]/i, "")]);
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

  const isHeb = profile && profile.strongs[0] === "H";
  const occCount = !profile ? 0 : (testament === "all"
    ? profile.total
    : (filteredBooks || profile.books).filter(b => (b.testament || "").toLowerCase() === testament).reduce((s, b) => s + b.count, 0));
  const distBooks = !profile ? [] : (filteredBooks || profile.books)
    .filter(b => testament === "all" || (b.testament || "").toLowerCase() === testament)
    .slice().sort((a, b) => b.count - a.count);
  const maxCount = distBooks.length ? distBooks[0].count : 1;
  const firstGloss = !profile ? "" : (
    (((profileCorpus === "kjv" ? profile.kjv_glosses : profile.abp_glosses) || [])[0] || {}).gloss
    || ((profile.abp_glosses || profile.kjv_glosses || [])[0] || {}).gloss || "");
  const selBookName = profile && selectedBook ? (profile.books.find(b => b.book === selectedBook)?.name || selectedBook) : "";
  const selBookCount = profile && selectedBook ? (profile.books.find(b => b.book === selectedBook)?.count ?? null) : null;
  const backToResults = () => { setProfile(null); setSelectedBook(null); setVerseList(null); };

  return (
    <div className={"ws" + (profile ? "" : " center-only") + (isMobile ? " is-mobile" : "")}>

      {/* LEFT — distribution rail (only with a word in focus) */}
      {isMobile && railOpen && profile && <div className="rail-scrim" onClick={() => setRailOpen(false)}/>}
      {profile && (
        <aside className={"brail" + (isMobile && !railOpen ? " hidden" : "")}>
          <div className="brail-top">
            <div className="brail-eyebrow">Distribution by book</div>
            <div className="brail-sub"><span className="brail-gk" dir={isHeb ? "rtl" : undefined}>{profile.lemma}</span> · {profile.books.length} {profile.books.length === 1 ? "book" : "books"}</div>
          </div>
          <div className="brail-scroll">
            <button className={"brow brow-all" + (!selectedBook ? " on" : "")}
              onClick={() => { setSelectedBook(null); setVerseList(null); setBookGlosses(null); setSelectedGloss(null); setFilteredBooks(null); if (isMobile) setRailOpen(false); }}>
              <span className="brow-name">All books</span>
              <span className="brow-n">{occCount}</span>
            </button>
            {distBooks.map(b => (
              <button key={b.book} className={"brow" + (selectedBook === b.book ? " on" : "")}
                onClick={() => { selectBook(b.book); if (isMobile) setRailOpen(false); }}>
                <span className="brow-name">{b.name}</span>
                <span className="brow-bar"><span className="brow-fill" style={{ width: Math.max(7, (b.count / maxCount) * 100) + "%" }}/></span>
                <span className="brow-n">{b.count}</span>
              </button>
            ))}
          </div>
        </aside>
      )}

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
            <div className="search-hint">One word looks it up · a question opens Ask the corpus</div>
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
                      onClick={() => switchTestament(t)}>{t === "all" ? "All" : t.toUpperCase()}</button>
                  ))}
                </div>
                <div className="lexicon-corpus-toggle">
                  <button className={"lct-btn" + (language === "all" ? " on" : "")} onClick={() => switchLanguage("all")}>All</button>
                  <button className={"lct-btn" + (language === "greek" ? " on" : "")} disabled={!_comboOK(corpus, testament, "greek")} onClick={() => switchLanguage("greek")}>Greek</button>
                  <button className={"lct-btn" + (language === "hebrew" ? " on" : "")} disabled={!_comboOK(corpus, testament, "hebrew")} onClick={() => switchLanguage("hebrew")}>Hebrew</button>
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

            {groupings && !profile && (
              <div className="lexicon-results">
                <div className="lexicon-dist-label">
                  rendered as "{query.trim()}" · {visibleGroupings.length} {visibleGroupings.length === 1 ? "word" : "words"}
                </div>
                {onAiSearch && (
                  <button className="lexicon-ask-instead" onClick={() => onAiSearch(query.trim())}>
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
                    <button className={"tg" + (profileCorpus === "kjv" ? " on" : "")} disabled={!profile.has_kjv} onClick={() => switchProfileCorpus("kjv")}>KJV</button>
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
                  <div className="corpus-groups">
                    <CorpusGroup
                      label={selBookName}
                      verses={verseList.map(v => ({ book: selectedBook, chapter: v.chapter, verse: v.verse, ref: `${selectedBook} ${v.chapter}:${v.verse}` }))}
                      allResults={[]}
                      onWordClick={onWordClick}
                      onReadInContext={onNavigateToLibrary ? (b, c, vv) => onNavigateToLibrary(b, c, vv, profileCorpus) : undefined}
                      textMode={profileCorpus === "kjv" ? "kjv" : "greek"}
                      primaryStrongs={null}
                      citedStrongs={citedStrongs}
                      kjvCache={{}}
                    />
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

      {/* RIGHT — word detail card (only with a word in focus) */}
      {isMobile && detailOpen && profile && <div className="wd-scrim" onClick={() => setDetailOpen(false)}/>}
      {profile && (
        <aside className={"wd" + (isMobile && !detailOpen ? " hidden" : "")}>
          <div className="wd-head">
            <span className="wd-strongs">{profile.strongs}</span>
            <span className="wd-head-r">
              {(groupings || matches) && (
                <button className="wd-overview" onClick={backToResults}>‹ Results</button>
              )}
              {isMobile && <button className="wd-overview" onClick={() => setDetailOpen(false)} aria-label="Close">✕</button>}
            </span>
          </div>
          <div className="wd-body">
            <div className="wd-hero">
              <div className={"wd-greek" + (isHeb ? " heb" : "")} dir={isHeb ? "rtl" : undefined}>{profile.lemma}</div>
              <div className="wd-sub"><span className="wd-tr">{profile.translit}</span>{firstGloss ? <> · <span className="wd-gloss">{firstGloss}</span></> : null}</div>
              <div className="wd-morph">{occCount} {occCount === 1 ? "occurrence" : "occurrences"}</div>
              {onAskWord && (
                <button className="wd-askai" onClick={() => onAskWord(profile.strongs, profile.lemma, profile.translit)}>
                  <Icon.Sparkle/> Ask AI about <span className={"wd-askai-w" + (isHeb ? " heb" : "")} dir={isHeb ? "rtl" : undefined}>{profile.lemma}</span> <Icon.ArrowRight/>
                </button>
              )}
            </div>

            {(profile.definition || /^G/i.test(profile.strongs)) && (
              <div className="wd-sec">
                <div className="wd-sec-h">
                  <span className="wd-sec-t">Definition</span>
                  {showDef && (!/^G/i.test(profile.strongs)
                    ? <span className="wd-badge">BDB</span>
                    : (!lsjLoading && lsjEntry)
                      ? <span className="wd-badge">{lsjEntry.source === "strongs" ? "Strong's" : lsjEntry.source === "abp_ext" ? "ABP" : "LSJ"}</span>
                      : null)}
                </div>
                {showDef ? (
                  !/^G/i.test(profile.strongs)
                    ? <p className="lsj">{profile.definition}</p>
                    : lsjLoading
                      ? <div className="lsj-def lsj-def--loading">Loading…</div>
                      : !lsjEntry
                        ? <p className="lsj">{profile.definition}</p>
                        : lsjEntry.source === "strongs"
                          ? <div className="lsj-def" dangerouslySetInnerHTML={{ __html: lsjEntry.def_html }} />
                          : lsjSummaryLoading
                            ? <LsjSummary data={null} loading={true} />
                            : (lsjSummary && lsjSummary.summary)
                              ? <LsjSummary data={lsjSummary} loading={false} />
                              : <div className="lsj-def" dangerouslySetInnerHTML={{ __html: lsjEntry.def_html }} />
                ) : (
                  <button className="lsj-toggle" onClick={() => setShowDef(true)}>Full entry ▾</button>
                )}
                {showDef && <button className="lsj-toggle" onClick={() => setShowDef(false)}>Show less ▴</button>}
              </div>
            )}

            {profile.abp_glosses && profile.abp_glosses.length > 0 && (
              <div className="wd-sec">
                <div className="wd-sec-h"><span className="wd-sec-t">ABP renders as</span><span className="wd-sec-meta">{profile.abp_glosses.length} senses</span></div>
                {renderGlossLine("abp", null, profile.abp_glosses)}
              </div>
            )}
            {profile.kjv_glosses && profile.kjv_glosses.length > 0 && (
              <div className="wd-sec">
                <div className="wd-sec-h"><span className="wd-sec-t">KJV renders as</span><span className="wd-sec-meta">{profile.kjv_glosses.length} senses</span></div>
                {renderGlossLine("kjv", null, profile.kjv_glosses)}
              </div>
            )}
            {profile.derivation && (
              <div className="wd-sec">
                <div className="wd-sec-h"><span className="wd-sec-t">Derivation</span></div>
                <p className="root-note">{profile.derivation}</p>
              </div>
            )}
          </div>
        </aside>
      )}
    </div>
  );
}
