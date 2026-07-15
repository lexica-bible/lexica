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

// WsI — Word study's PRIVATE icon set — is gone (2026-07-15). It was a FORK, not drift:
// its Sliders was character-for-character identical to Icon.Modes, and its Search redrew
// Icon.Search's exact two shapes at a different stroke. Same function, two definitions, and
// the sliders glyph was serving "Views" here while meaning "Reading options" in Library —
// one glyph, two jobs, which is what the app-wide pass exists to stop. Card + ChevR had no
// shared twin, so they were PROMOTED into Icon rather than deleted.
// Sizes: the bottom bar sizes its own glyphs (.wm-tab svg -> 22px), so the bar takes the
// shared components bare. The NON-bar uses (the search box's leading icon, its clear button,
// the context chevron) were 20/19/15px by the old set's own width attrs and the CSS only
// sets the flex slot, not the glyph — so they pass their size explicitly. Consolidating the
// definition must not resize a shipped surface.

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
  const [allTruncated, setAllTruncated] = useState(false);  // "All books" list hit the render cap
  const [visibleCount, setVisibleCount] = useState(50);     // occurrences shown so far; "See more" adds 50
  const [filteredBooks, setFilteredBooks] = useState(null);
  const [groupings, setGroupings] = useState(null);
  const [pendingGloss, setPendingGloss] = useState(null);
  // Signature of the occurrence-list state the profile already SEEDED (default all-books view),
  // so the all-books effect below skips the redundant re-fetch for exactly that one state and
  // still fires for any real filter change. Cleared once consumed.
  const seededVersesSig = useRef(null);
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

  // Verse-grounded Lexica entry, keyed by the FULL Strong's number (profile.strongs keeps the
  // dotted ".N"). Same fetch the Library word card makes (30-detail-panel); when present it
  // REPLACES the LSJ/BDB body with the shared LexicaBody / StructuralBody / idiom note so the two
  // surfaces can't drift. Quiet by design (JP's call): NO loading gate — the LSJ/gloss body shows
  // immediately and the Lexica body swaps in when this lands, no spinner container. A word with no
  // entry 404s → null → the card is exactly as before. The numbering crosswalk (alias_note) rides
  // this same response but its header badge is a separate queue item, not wired here.
  const [lexica, setLexica] = useState(null);
  useEffect(() => {
    setLexica(null);
    const sn = profile && profile.strongs;
    if (!sn || sn === "*") return;
    let cancelled = false;
    api.lexica(sn)
      .then(d => { if (!cancelled) setLexica(d && !d.error ? d : null); })
      .catch(() => { if (!cancelled) setLexica(null); });
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
      const data = await api.lexiconProfile(strongs, c, testament);
      if (data.error) setError(data.error);
      // Honor the source the backend actually used — a Hebrew number heb.db lacks
      // (a byform/Aramaic/name) falls back to KJV, so reflect that in the toggle.
      else {
        setProfile(data);
        const rc = (data.corpus && data.corpus !== c) ? data.corpus : c;
        if (rc !== c) setProfileCorpus(rc);
        // Seed the occurrence list from the profile's baked default page so it renders
        // WITH the rest of the card — no second round-trip. The all-books effect skips
        // exactly this seeded state (matched by signature) and re-fetches on any filter change.
        if (data.default_verses) {
          setVerseList(data.default_verses);
          setAllTruncated(!!data.default_truncated);
          seededVersesSig.current = JSON.stringify([data.strongs, rc, null, null, testament || "all"]);
        }
      }
    } catch (e) { setError("Failed to load word profile: " + e); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (profile && pendingGloss) {
      selectGloss(pendingGloss);
      setPendingGloss(null);
    }
  }, [profile, pendingGloss]);

  // The default "All books" view: with a word in focus and no specific book picked,
  // the occurrences pane lists EVERY occurrence across the Bible. The book rail, the
  // OT/NT tabs, and the rendering chips just narrow this list — so re-fetch whenever
  // any of those filters change (a picked book is handled imperatively by selectBook).
  // Gated on !loading so a profile/corpus reload in flight fires this exactly once.
  useEffect(() => {
    if (!profile || selectedBook || loading) return;
    // The profile already baked this exact default view (all books, no gloss, current
    // testament) — use the seeded list instead of re-fetching it. Consume the signature so a
    // later real filter change (different sig) fetches normally.
    const sig = JSON.stringify([profile.strongs, profileCorpus, selectedBook, selectedGloss, testament || "all"]);
    if (seededVersesSig.current === sig) { seededVersesSig.current = null; return; }
    let cancelled = false;
    setVerseLoading(true);
    setVerseList(null);
    setAllTruncated(false);
    api.lexiconVerses(profile.strongs, "all", profileCorpus, selectedGloss, testament)
      .then(d => {
        if (cancelled) return;
        if (d.error) setVerseList([{ error: d.error }]);
        else { setVerseList(d.verses || []); setAllTruncated(!!d.truncated); }
      })
      .catch(e => { if (!cancelled) setVerseList([{ error: String(e) }]); })
      .finally(() => { if (!cancelled) setVerseLoading(false); });
    return () => { cancelled = true; };
  }, [profile, profileCorpus, selectedBook, selectedGloss, testament, loading]);

  // Any change of word / source / book / rendering / testament means a fresh
  // occurrence list — start back at the first 50 (the "See more" page size).
  useEffect(() => { setVisibleCount(50); }, [profile, profileCorpus, selectedBook, selectedGloss, testament]);

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

  // A "renders as" chip click: set the top translation filter to that chip's Bible
  // AND apply its gloss together, in one click. On the tab that's already active
  // this is just the gloss toggle (selectGloss). On a different tab it reloads the
  // word in that corpus (like switchProfileCorpus) but KEEPS the picked gloss rather
  // than clearing it — using lineCorpus explicitly since profileCorpus updates async.
  const pickRender = async (lineCorpus, gloss) => {
    if (loading || !profile) return;
    if (lineCorpus === profileCorpus) { selectGloss(gloss); return; }
    setProfileCorpus(lineCorpus);
    setLoading(true);
    setSelectedBook(null);
    setVerseList(null);
    setTestament("all");
    setSelectedGloss(gloss);
    setBookGlosses(null);
    try {
      const data = await api.lexiconProfile(profile.strongs, lineCorpus);
      if (!data.error) setProfile(data);
      const bk = await api.lexiconBooks(profile.strongs, lineCorpus, gloss);
      setFilteredBooks(bk.books && bk.books.length ? bk.books : null);
    } catch { setFilteredBooks(null); }
    finally { setLoading(false); }
  };

  const _isGreekHebrew = (s) => /[Ͱ-Ͽἀ-῿֐-׿]/.test(s);

  // One "<Bible> renders this as" line. EVERY chip is clickable: it jumps the top
  // translation filter to that chip's Bible AND applies its gloss in one click (see
  // pickRender), so you skip the move-tab-then-filter two-step. The chip on the tab
  // that's already active still toggles its gloss the same way.
  const renderGlossLine = (lineCorpus, label, list) => {
    if (!list || !list.length) return null;
    return (
      <div className="lexicon-glosses">
        {label && <div className="lexicon-gloss-label">{label}</div>}
        <div className="lexicon-dist-list">
          {list.map((g, i) => (
            <React.Fragment key={g.gloss}>
              {i > 0 && <span className="lexicon-dist-sep"> · </span>}
              <button
                className={"lexicon-dist-item" + (profileCorpus === lineCorpus && selectedGloss === g.gloss ? " selected" : "")}
                onClick={() => pickRender(lineCorpus, g.gloss)}
              >
                {g.gloss}<span className="lexicon-dist-count">{g.count}</span>
              </button>
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

  // Handle a /lexicon/lookup result (Greek/Hebrew/transliteration). Auto-open ONLY a
  // lone true hit (one exact, nothing else); if ANY "contains" rows exist, always show
  // the ranked list so the Exact / Also-contains divider does its discovery job.
  const showLookup = (data, q) => {
    if (!data.length) { setError("No matches found for \"" + q + "\"."); return; }
    const exact = data.filter(d => d.match === "exact");
    if (exact.length === 1 && exact.length === data.length) loadProfile(exact[0].strongs);
    else { setMatches(data); setGlOpen(true); }
  };

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
        showLookup(await api.lexiconLookup(q), q);
      } else {
        const data = await api.lexiconEnglish(q, corpus, testament);
        if (data.length) { setGroupings(data); setGlOpen(true); }
        else {
          // No English meaning matched — the input may be a Greek/Hebrew word
          // typed in Latin letters (e.g. "pneuma"). Fall back to the lookup,
          // which matches transliterations accent-insensitively.
          showLookup(await api.lexiconLookup(q), q);
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
  const _topRender = !profile ? "" : (
    (((profileCorpus === "heb" ? profile.heb_glosses : profileCorpus === "bsb" ? profile.bsb_glosses : profileCorpus === "kjv" ? profile.kjv_glosses : profile.abp_glosses) || [])[0] || {}).gloss
    || ((profile.heb_glosses || profile.abp_glosses || profile.kjv_glosses || profile.bsb_glosses || [])[0] || {}).gloss || "");
  // Header gloss = the plain dictionary meaning (word_gloss), trimmed exactly like the Library
  // word card (shortLemmaGloss), so the two surfaces match. GREEK: profile.definition leads with
  // word_gloss; for Hebrew that field is the long BDB paragraph, so keep the top in-verse rendering
  // there until the profile carries the Hebrew word_gloss (its own checkpoint).
  const firstGloss = !profile ? "" : (
    (/^G/i.test(profile.strongs) ? shortLemmaGloss(profile.definition) : "") || _topRender);
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

  // One source's rendering line. The backend caps it to 8 and (for an English
  // search) flags the matched rendering `m` for bolding — surfacing it in place if
  // it sorted below the cap, so the summary always shows the typed word. A trailing
  // {trunc:true} marker means the source has more rows than shown → render a "…".
  const renderRend = (list) => {
    const items = list.filter(x => !x.trunc);
    const trunc = list.some(x => x.trunc);
    return (
      <>
        {items.map((x, i) => (
          <React.Fragment key={x.gloss + i}>
            {i > 0 && ", "}
            <span className={x.m ? "glrow-match" : undefined}>{x.gloss}</span>
          </React.Fragment>
        ))}
        {trunc && " …"}
      </>
    );
  };

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
                  <span className="glrow-s refmark">{g.strongs}</span>
                  <span className="glrow-main">
                    <span className="glrow-top">
                      {g.lemma && <span className={"glrow-gk" + (gh ? " heb" : "")} dir={gh ? "rtl" : undefined}>{g.lemma}</span>}
                      {g.translit && <span className="glrow-tr">{g.translit}</span>}
                    </span>
                    {/* Each source line carries that Bible's TOTAL count for the number — matches
                        the count on the word's own study page. ABP spans OT+NT (LXX), KJV/BSB are
                        NT-only for a Greek word; for a Hebrew number HEB is the real Hebrew OT. */}
                    {g.abp_glosses && g.abp_glosses.length > 0 && (
                      <span className="glrow-rend"><span className="glrow-k">ABP</span><span>{renderRend(g.abp_glosses)}</span>{g.abp_total != null && <span className="glrow-n">{g.abp_total}</span>}</span>
                    )}
                    {g.heb_glosses && g.heb_glosses.length > 0 && (
                      <span className="glrow-rend"><span className="glrow-k">HEB</span><span>{renderRend(g.heb_glosses)}</span>{g.heb_total != null && <span className="glrow-n">{g.heb_total}</span>}</span>
                    )}
                    {g.kjv_glosses && g.kjv_glosses.length > 0 && (
                      <span className="glrow-rend"><span className="glrow-k">KJV</span><span>{renderRend(g.kjv_glosses)}</span>{g.kjv_total != null && <span className="glrow-n">{g.kjv_total}</span>}</span>
                    )}
                    {g.bsb_glosses && g.bsb_glosses.length > 0 && (
                      <span className="glrow-rend"><span className="glrow-k">BSB</span><span>{renderRend(g.bsb_glosses)}</span>{g.bsb_total != null && <span className="glrow-n">{g.bsb_total}</span>}</span>
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

  // Split a lookup list into its two bands. Exact = a real dictionary/transliteration
  // hit; contains = a plain substring match, labeled as such so a letter-accident
  // (euthéōs under "theos") can't masquerade as a relative.
  const matchBands = (arr) => ({
    exact: arr.filter(m => m.match === "exact"),
    contains: arr.filter(m => m.match !== "exact"),
  });
  const containsLabel = (exactCount, q) => exactCount
    ? "Other words containing “" + q + "”"
    : "No exact match — showing words containing “" + q + "”";

  // One rich match row (mobile glsenses list). Shared by both bands.
  const renderMatchRow = (m) => {
    const mh = m.strongs[0] === "H";
    return (
      <button key={m.strongs}
        className={"glrow" + (profile && profile.strongs === m.strongs ? " on" : "")}
        onClick={() => { loadProfile(m.strongs); setGlOpen(false); }}>
        <span className="glrow-s refmark">{m.strongs}</span>
        <span className="glrow-main">
          <span className="glrow-top">
            {m.lemma && <span className={"glrow-gk" + (mh ? " heb" : "")} dir={mh ? "rtl" : undefined}>{m.lemma}</span>}
            {m.translit && <span className="glrow-tr">{m.translit}</span>}
          </span>
          {/* "used as" renderings per source — same lines as the English finder.
              Falls back to the plain gloss for a row with no renderings. */}
          {m.abp_glosses && m.abp_glosses.length > 0 && (
            <span className="glrow-rend"><span className="glrow-k">ABP</span><span>{renderRend(m.abp_glosses)}</span>{m.abp_total != null && <span className="glrow-n">{m.abp_total}</span>}</span>
          )}
          {m.heb_glosses && m.heb_glosses.length > 0 && (
            <span className="glrow-rend"><span className="glrow-k">HEB</span><span>{renderRend(m.heb_glosses)}</span>{m.heb_total != null && <span className="glrow-n">{m.heb_total}</span>}</span>
          )}
          {m.kjv_glosses && m.kjv_glosses.length > 0 && (
            <span className="glrow-rend"><span className="glrow-k">KJV</span><span>{renderRend(m.kjv_glosses)}</span>{m.kjv_total != null && <span className="glrow-n">{m.kjv_total}</span>}</span>
          )}
          {m.bsb_glosses && m.bsb_glosses.length > 0 && (
            <span className="glrow-rend"><span className="glrow-k">BSB</span><span>{renderRend(m.bsb_glosses)}</span>{m.bsb_total != null && <span className="glrow-n">{m.bsb_total}</span>}</span>
          )}
          {!(m.abp_glosses && m.abp_glosses.length) && !(m.heb_glosses && m.heb_glosses.length)
            && !(m.kjv_glosses && m.kjv_glosses.length) && !(m.bsb_glosses && m.bsb_glosses.length)
            && m.gloss && <span className="glrow-rend"><span>{m.gloss}</span></span>}
        </span>
        <span className="glrow-occ" title="Open word study">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
        </span>
      </button>
    );
  };

  // Greek/Hebrew word-match list (from /api/lexicon/lookup). Same collapsible card
  // shell as the English renderSenses() so picking a result COLLAPSES the list (shows
  // the chosen word in the header) instead of making it vanish — they share .glsenses.
  const renderMatches = () => (
    <div className={"glsenses" + (glOpen ? " open" : "")}>
      <button className="glsenses-head" aria-expanded={glOpen} onClick={() => setGlOpen(o => !o)}>
        <span className="glsenses-l">
          <b>{matches.length}</b> {matches.length === 1 ? "match" : "matches"} for “{query.trim()}”
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
      {glOpen && (() => {
        const { exact, contains } = matchBands(matches);
        const q = query.trim();
        return (
          <div className="glsenses-rows">
            {exact.length > 0 && <div className="glmatch-div">Exact match</div>}
            {exact.map(renderMatchRow)}
            {contains.length > 0 && <div className="glmatch-div glmatch-div--contains">{containsLabel(exact.length, q)}</div>}
            {contains.map(renderMatchRow)}
          </div>
        );
      })()}
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

      {(profile.definition || /^G/i.test(profile.strongs)) && (() => {
        // When a Lexica entry exists it leads, exactly like the Library word card: an idiom note,
        // the structural/function card, or the verse-grounded sense list — each via the SAME shared
        // component (LexicaBody / StructuralBody), so the two surfaces stay in step by construction.
        // No lexica → the original LSJ/BDB path, untouched. The card keeps its own top plain-gloss
        // line (in the hero) regardless — orientation above the detail.
        // GREEK ONLY: Library never renders LexicaBody for a Hebrew word (it gets the BDB section
        // instead — 30-detail-panel pushes "bdb", never "lsj", for Hebrew). Gate the same way so a
        // Hebrew number with an entry keeps its BDB definition and the two surfaces don't diverge.
        const lex = /^G/i.test(profile.strongs) ? lexica : null;
        const idiom = !!(lex && lex.kind === "idiom");
        const structural = !!(lex && lex.kind === "structural");
        return (
        <section className="sec">
          <h4 className="sec-head">
            <span className="sec-t">{structural ? "Function" : idiom ? "Phrase" : "Definition"}</span>
            {idiom
              ? <span className="lsj-badge" title="A fixed phrase (idiom) — its plain meaning, not a grammatical relation">Idiom</span>
              : structural
              ? <span className="lsj-badge" title="Structural word — its grammatical function, not a sense list">Grammar</span>
              : lex
              ? <span className="lsj-badge" title="Lexica dictionary — defined from the Bible's own usage">Lexica</span>
              : !/^G/i.test(profile.strongs)
              ? <span className="bdb-badge">Strong's</span>
              : (!lsjLoading && lsjEntry)
                ? <span className="lsj-badge" title={lsjSummary && lsjSummary.override ? "Lexica editorial gloss — plain biblical sense foregrounded" : undefined}>{(lsjSummary && lsjSummary.override) ? "Lexica" : lsjEntry.source === "strongs" ? "Strong's" : lsjEntry.source === "abp_ext" ? "ABP" : "LSJ"}</span>
                : null}
          </h4>
          {idiom
            ? <div className="gram"><p className="gram-fn"><b>{lex.phrase}</b> — {lex.note}</p></div>
            : structural
            ? <StructuralBody data={lex} lsjEntry={lsjEntry} />
            : lex
            ? <LexicaBody lexica={lex} lsjEntry={lsjEntry} />
            : !/^G/i.test(profile.strongs)
            ? <p className="lsj">{profile.definition}</p>
            : lsjLoading
              ? <div className="lsj-def lsj-def--loading">Loading…</div>
              : !lsjEntry
                ? <p className="lsj">{profile.definition}</p>
                : <LsjBody lsjEntry={lsjEntry} lsjSummary={lsjSummary} summaryLoading={lsjSummaryLoading} />}
        </section>
        );
      })()}

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
                <span className="rel-gloss">{r.gloss}<span className="rel-s refmark">{r.strongs}</span></span>
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
      verseLoading || !verseList ? <div className="occ-empty">Loading…</div>
      : (verseList[0] && verseList[0].error) ? <div className="occ-empty" style={{ color: "var(--danger, #b91c1c)" }}>{verseList[0].error}</div>
      : (verseList.length) ? (
        <div className="vlist">
          {!selectedBook && allTruncated && (
            <div className="occ-trunc">First {verseList.length.toLocaleString()} — pick a book or rendering to see the rest.</div>
          )}
          {verseList.slice(0, visibleCount).map(v => {
            const vb = v.book || selectedBook;
            return (
            <VerseRow key={`${vb}-${v.chapter}-${v.verse}`}
              book={vb} chapter={v.chapter} verse={v.verse}
              label={`${vb} ${v.chapter}:${v.verse}`}
              allResults={[]} onWordClick={onWordClick}
              onReadInContext={onNavigateToLibrary ? (b, c, vv) => onNavigateToLibrary(b, c, vv, profileCorpus) : undefined}
              textMode={profileCorpus === "kjv" ? "kjv" : profileCorpus === "heb" ? "heb" : profileCorpus === "bsb" ? "bsb" : "greek"}
              primaryStrongs={null} citedStrongs={citedStrongs} kjvCache={{}}/>
            );
          })}
          {verseList.length > visibleCount && (
            <button className="occ-more" onClick={() => setVisibleCount(c => c + 50)}>
              See more <span className="occ-more-n">({Math.min(visibleCount, verseList.length).toLocaleString()} of {verseList.length.toLocaleString()})</span>
            </button>
          )}
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
            <span className="wm-ctx-go"><Icon.ChevR/></span>
          </button>
        )}

        <div className="wm-main">
          {error && <p className="lexicon-error">{error}</p>}
          {groupings && renderSenses()}
          {matches && renderMatches()}
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
                <Icon.Search className="wm-search-i" width="20" height="20"/>
                <input className="wm-search-input" type="text" value={query}
                  onChange={e => setQuery(e.target.value)} enterKeyHint="search"
                  placeholder="Word, transliteration, Strong's…"/>
                {query && <button type="button" className="wm-search-clear" onClick={() => setQuery("")} aria-label="Clear"><Icon.Close width="19" height="19"/></button>}
              </form>
              <div className="occ-welcome-s">Search a word, transliteration, or Strong's number — or tap a sample.</div>
              <div className="occ-welcome-chips">
                {["πνεῦμα", "pistis", "G26", "spirit"].map(q => (
                  <button key={q} className="welcome-chip suggest-link" onClick={() => handleSubmit(null, q)}>{q}</button>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <nav className="wm-tabs" aria-label="Word study tools">
          <button className={"wm-tab" + (sheet === "search" ? " on" : "")} onClick={() => setSheet("search")} title="Search" aria-label="Search">
            <Icon.Search/>
          </button>
          <button className={"wm-tab" + (sheet === "dist" ? " on" : "")} disabled={!profile} onClick={() => setSheet("dist")} title="Distribution" aria-label="Distribution">
            <Icon.Book/>
          </button>
          {/* The word's detail panel = every other surface's inspect. Same glyph as News's
              Watch and Ask-corpus's Inspect (2026-07-15). */}
          <button className={"wm-tab" + (sheet === "card" ? " on" : "")} disabled={!profile} onClick={() => setSheet("card")} title="Word card" aria-label="Word card">
            <Icon.Panel/>
          </button>
          {/* "Views" is a FILTER sheet, whatever its label says: Edition (ABP/HEB/KJV/BSB),
              Testament (All/Old/New), Go deeper — it narrows WHICH occurrences you see. Same
              function as News's Options, so it takes the same glyph. It briefly wore Icon.Grid
              on the guess that "Views" meant layout; nobody had opened the sheet, and Grid
              already means CHIP VIEW in the reader. Read the sheet, not the label. */}
          <button className={"wm-tab" + (sheet === "views" ? " on" : "")} disabled={!profile} onClick={() => setSheet("views")} title="Views" aria-label="Views">
            <Icon.Filter/>
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
                <Icon.Search className="wm-search-i" width="20" height="20"/>
                <input className="wm-search-input" type="text" value={query} autoFocus
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Word, transliteration, Strong's…"/>
                {query && <button type="button" className="wm-search-clear" onClick={() => setQuery("")} aria-label="Clear"><Icon.Close width="19" height="19"/></button>}
              </form>
              <div className="wm-search-hint">Greek, Hebrew, a transliteration, an English gloss, or a Strong's number.</div>
              <div className="wm-search-chips">
                {["πνεῦμα", "pistis", "G26", "spirit", "ἀγάπη", "H7307"].map(q => (
                  <button key={q} className="welcome-chip suggest-link" onClick={() => { setSheet(null); handleSubmit(null, q); }}>{q}</button>
                ))}
              </div>
            </div>
          </WsSheet>
        )}
      </div>
    );
  }

  // Desktop frame migrated onto the shared <Shell> (Phase 2). PARITY ONLY — same emitted DOM:
  // Shell renders <div class="zshell ws"><aside class="zrail brail">…</aside><main class="zcenter
  // center">…</main>{inspect}</div>, and the inspect is a plain .zinspect wd (top:0 float — a
  // shipped surface keeps its float, NOT the new-surface below-nav). Mobile is the separate
  // `if (isMobile)` branch above, untouched. isMobile is hard-false here (the mobile branch
  // already returned), so the old mobile-only scrims/hidden classes were dead and are dropped.
  return (
    <Shell
      className="ws"
      isMobile={false}
      railClass="brail"
      centerClass="center"
      rail={
        profile ? (
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
        )
      }
      center={<>
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

            {/* search-results toolbar (no word in focus). ONLY for the English-rendering
                search — source/testament/language actually re-query there. Over a
                transliteration/lemma `matches` set they can't filter anything (a word
                exists independent of which text renders it), so the bar is hidden rather
                than shown-but-inert. */}
            {!profile && groupings && (
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

            {matches && !profile && (() => {
              const { exact, contains } = matchBands(matches);
              const q = query.trim();
              const row = (m) => (
                <button key={m.strongs} className="lexicon-match-row listrow" onClick={() => loadProfile(m.strongs)}>
                  <span className="lexicon-match-strongs refmark">{m.strongs}</span>
                  <span className={"lexicon-match-lemma" + (m.strongs[0] === "H" ? " heb" : "")}
                        dir={m.strongs[0] === "H" ? "rtl" : undefined}>{m.lemma}</span>
                  <span className="lexicon-match-translit">{m.translit}</span>
                  <span className="lexicon-match-gloss">{m.gloss}</span>
                </button>
              );
              return (
                <div className="lexicon-matches">
                  {exact.length > 0 && <div className="glmatch-div">Exact match</div>}
                  {exact.map(row)}
                  {contains.length > 0 && <div className="glmatch-div glmatch-div--contains">{containsLabel(exact.length, q)}</div>}
                  {contains.map(row)}
                </div>
              );
            })()}

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
                ) : allTruncated && verseList && verseList.length ? (
                  <div className="occ-filter">
                    <span>Only the first {verseList.length.toLocaleString()} occurrences are listed — pick a book or rendering at left to reach the rest.</span>
                  </div>
                ) : null}

                {verseLoading || !verseList ? (
                  <div className="occ-empty">Loading…</div>
                ) : (verseList[0] && verseList[0].error) ? (
                  <div className="occ-empty" style={{ color: "var(--danger, #b91c1c)" }}>{verseList[0].error}</div>
                ) : (verseList.length) ? (
                  <div className="vlist">
                    {verseList.slice(0, visibleCount).map(v => {
                      const vb = v.book || selectedBook;
                      return (
                      <VerseRow
                        key={`${vb}-${v.chapter}-${v.verse}`}
                        book={vb} chapter={v.chapter} verse={v.verse}
                        label={`${vb} ${v.chapter}:${v.verse}`}
                        allResults={[]}
                        onWordClick={onWordClick}
                        onReadInContext={onNavigateToLibrary ? (b, c, vv) => onNavigateToLibrary(b, c, vv, profileCorpus) : undefined}
                        textMode={profileCorpus === "kjv" ? "kjv" : profileCorpus === "heb" ? "heb" : profileCorpus === "bsb" ? "bsb" : "greek"}
                        primaryStrongs={null}
                        citedStrongs={citedStrongs}
                        kjvCache={{}}
                      />
                      );
                    })}
                    {verseList.length > visibleCount && (
                      <button className="occ-more" onClick={() => setVisibleCount(c => c + 50)}>
                        See more <span className="occ-more-n">({Math.min(visibleCount, verseList.length).toLocaleString()} of {verseList.length.toLocaleString()})</span>
                      </button>
                    )}
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
                    <button key={q} className="welcome-chip suggest-link" onClick={() => handleSubmit(null, q)}>{q}</button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </>}
      inspect={
        <aside className="zinspect wd">
        {profile ? (
          <>
          <div className="detail-head">
            {/* Badge + numbering crosswalk glued as one unit — same treatment as the Library card. */}
            <span className="detail-strong-wrap">
              <span className="detail-strong-head">{profile.strongs}</span>
              {profile.alias_note && (
                <span className="detail-strong-alias">
                  {profile.alias_note.direction === "to_abp"
                    ? `· ABP ${profile.alias_note.abp}`
                    : `· standard ${profile.alias_note.standard.join(", ")}`}
                </span>
              )}
            </span>
            {(groupings || matches) && (
              <button className="detail-back" onClick={backToResults}>‹ Results</button>
            )}
          </div>
          <div className="detail-body">{renderWordCardInner()}</div>
          </>
        ) : (
          <ZoneEmpty icon={<Icon.Book width="30" height="30"/>}
            title="No word selected"
            sub="Search a Greek or Hebrew word, a transliteration, or a Strong's number to study it here."/>
        )}
        </aside>
      }
    />
  );
}
