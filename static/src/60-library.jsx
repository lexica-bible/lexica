// ============================================================
// LIBRARY VIEW — the reader (the big component). Its helpers and nav/picker
// sub-components live in 59a-library-helpers.jsx + 59b-library-nav.jsx.
// ============================================================
function LibraryView({ nav, onNavChange, onWordClick, onVerseNumberClick, onOpenNote, onTranslationChange, isMobile, showSummary, focusMode, onToggleFocus, onDetailBaseChange }) {
  const [books, setBooks] = useState(() => readCachedBooks());
  const [selBook, setSelBook] = useState(() => {
    const c = readCachedBooks(), s = readLibSaved();
    if (!c.length) return null;
    return (s && s.book && c.find(b => b.abbrev === s.book)) || c[0];
  });
  const [selChapter, setSelChapter] = useState(() => { const s = readLibSaved(); return s && s.chapter > 0 ? s.chapter : 1; });
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
  const [dockClosing, setDockClosing] = useState(false);  // mobile dock: keep it mounted briefly so it can slide OUT
  const dockWasShown = useRef(false);
  const audioRef = useRef(null);
  const resumeAudioRef = useRef(false);   // page-turn while playing → keep the read-along going on the next page
  const [viewCh, setViewCh] = useState(null);   // chrono: chapter currently scrolled into view (drives the toolbar play target)
  const [libOptions, setLibOptions] = useState(() => {
    try {
      const s = JSON.parse(localStorage.getItem("lexica.opts.v1") || "null");
      if (s) return { viewMode: s.viewMode || "chip", showStrongs: !!s.showStrongs, showInterlinear: !!s.showInterlinear };
    } catch (e) {}
    return { viewMode: "chip", showStrongs: false, showInterlinear: false };
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
    if (theme === "light") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("lexica.theme.v1", theme);
  }, [theme]);
  const [translation, setTranslation] = useState(() => {       // "abp"|"kjv"|"bsb"|"esv"|"niv"|"parallel"
    const s = readLibSaved(), t = s && s.translation;
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
    const onDown = (e) => {
      if (compareWrapRef.current && !compareWrapRef.current.contains(e.target)) {
        setCompareOpen(false);
        // Swallow the dismiss click so it doesn't also land on a word chip behind the menu.
        const swallow = (ev) => { ev.stopPropagation(); ev.preventDefault(); };
        document.addEventListener("click", swallow, { capture: true, once: true });
        setTimeout(() => document.removeEventListener("click", swallow, { capture: true }), 350);
      }
    };
    const onKey = (e) => { if (e.key === "Escape") setCompareOpen(false); };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("pointerdown", onDown); document.removeEventListener("keydown", onKey); };
  }, [compareOpen]);
  const [corpus, setCorpus] = useState(() => {            // "bible" | a non-canonical id (e.g. "didache")
    const s = readLibSaved();
    return s && s.corpus && s.corpus !== "bible" && NONCANON.some(x => x.id === s.corpus) ? s.corpus : "bible";
  });
  const [didVerses, setDidVerses] = useState([]);
  const [didLoading, setDidLoading] = useState(false);
  const [otherOpen, setOtherOpen] = useState(false);
  const [fontOpen, setFontOpen] = useState(false);
  const fontWrapRef = useRef(null);   // the Aa menu wrapper — for click-outside-to-close
  // Close the Aa (size/theme) menu on any click outside it — robust against the
  // toolbar sitting above the scrim. Clicks inside keep it open so A−/A+ still work.
  // The outside click that closes it is SWALLOWED so it doesn't also select a word
  // or open something behind the menu (the dismiss click should only dismiss).
  useEffect(() => {
    if (!fontOpen) return;
    const onDoc = (e) => {
      if (fontWrapRef.current && fontWrapRef.current.contains(e.target)) return;   // inside: keep open
      setFontOpen(false);
      const swallow = (ev) => { ev.stopPropagation(); ev.preventDefault(); };
      document.addEventListener("click", swallow, { capture: true, once: true });
      // If this press never becomes a click (e.g. a drag), drop the swallower.
      setTimeout(() => document.removeEventListener("click", swallow, { capture: true }), 350);
    };
    document.addEventListener("pointerdown", onDoc);
    return () => document.removeEventListener("pointerdown", onDoc);
  }, [fontOpen]);
  const [summaryOpen, setSummaryOpen] = useState(false);   // mobile: overview sheet
  const [chronoPanel, setChronoPanel] = useState("intro"); // chrono right panel: "intro" | "overview"
  // Chronological reading: the same reader, fed passages in event order. The list
  // is a static file (book + verse range pointers, no Bible text). "canonical" =
  // normal book/chapter order; "chronological" = walk `chrono.passages` in order.
  const [orderMode, setOrderMode] = useState(() => {       // "canonical" | "chronological"
    const s = readLibSaved();
    return s && s.orderMode === "chronological" ? "chronological" : "canonical";
  });
  const [chrono, setChrono] = useState(() => readCachedChrono());  // { eras, passages } | null (cached for instant first paint)
  const [chronoPos, setChronoPos] = useState(() => {       // current passage position (1-based)
    const s = readLibSaved();
    return s && s.chronoPos > 0 ? s.chronoPos : 1;
  });
  const [chronoData, setChronoData] = useState(null);      // loaded span: { pos, byCh:{ch:{abp,kjv,bsb}} }
  const [chronoLoading, setChronoLoading] = useState(false);
  // Chrono picker view: "eras" (the era→passage browse) or "days" (the 365-day plan).
  const [chronoView, setChronoView] = useState(() => {
    try { return localStorage.getItem("lexica.chronoview.v1") === "eras" ? "eras" : "days"; } catch (e) { return "days"; }
  });
  // Per-text reading-plan progress ({ abp:{day,streak,last}, kjv:{...}, ... }).
  const [planProg, setPlanProg] = useState(() => planLoadAll());
  const nonCanon = NONCANON.find(t => t.id === corpus) || null;
  const chronoOn = orderMode === "chronological" && !nonCanon && !!chrono && translation !== "heb";
  // Hebrew OT has no chronological order — keep order canonical whenever Hebrew is the text
  // (covers both switching to Hebrew from chrono AND restoring an old heb+chrono spot).
  useEffect(() => { if (translation === "heb" && orderMode === "chronological") setOrderMode("canonical"); }, [translation, orderMode]);
  const curPassage = chronoOn ? (chrono.passages[chronoPos - 1] || null) : null;
  const highlightRef = useRef(null);
  const navBookRef = useRef(null);
  const readingRef = useRef(null);
  // Drag-select-to-note: the floating "Add note" bar + the captured anchor.
  const [noteSel, setNoteSel] = useState(null);   // { rect, anchor } | null
  const justSelectedRef = useRef(false);            // suppress the click that follows a drag
  const swallowClickRef = useRef(false);            // a press that closed the popup → eat its click (survives the re-render)
  const [flashMsg, setFlashMsg] = useState("");     // tiny confirmation toast ("Copied", etc.)
  const flashT = useRef(null);
  const flash = (m) => { setFlashMsg(m); clearTimeout(flashT.current); flashT.current = setTimeout(() => setFlashMsg(""), 1600); };
  // The line a verse becomes when sent to the journal: "Genesis 1:8 (ABP) — text".
  // No translation tag for non-canon texts (their book name already says it all).
  const journalLine = (a) => {
    const tag = nonCanon ? "" : (translation === "parallel" ? compareSel.map(s => s.toUpperCase()).join("/") : (translation || "").toUpperCase());
    return a.refLabel + (tag ? " (" + tag + ")" : "") + " — " + a.snippet;
  };
  useNotesVersion();                                // re-render markers when notes change
  // Who's signed in (re-read every render; setAuth notifies, so login/logout
  // re-renders us). The ESV toggle only ever shows when the server says "owner".
  const authEmail = (() => { try { return (NotesStore.authInfo() || {}).email || null; } catch (e) { return null; } })();
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.esvStatus().then(d => { if (!cancelled) setEsvOwner(!!(d && d.owner)); }),
      api.nivStatus().then(d => { if (!cancelled) setNivOwner(!!(d && d.owner)); }),
      api.hebStatus().then(d => { if (!cancelled) setHebAvail(!!(d && d.available)); }),
    ]).finally(() => { if (!cancelled) setGatedReady(true); });
    return () => { cancelled = true; };
  }, [authEmail]);
  // If the owner signs out (or it's revoked) while reading ESV/NIV, fall back to ABP
  // so they're never stuck on a now-forbidden text showing blank.
  useEffect(() => {
    if (!gatedReady) return;   // owner status still loading — don't bounce a just-restored gated text
    if (!esvOwner && translation === "esv") { setTranslation("abp"); onTranslationChange?.("abp"); }
    if (!nivOwner && translation === "niv") { setTranslation("abp"); onTranslationChange?.("abp"); }
    // HEB is OT-only — bounce back to ABP if it's unavailable, or you moved to an NT
    // book while reading Hebrew.
    if (translation === "heb" && (!hebAvail || (selBook && NT_BOOKS.has(selBook.abbrev)))) { setTranslation("abp"); onTranslationChange?.("abp"); }
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
      sc.scrollTo({ top: Math.max(0, top - 8), behavior: "smooth" });
    });
  }, [nav?.book, selBook?.abbrev]);

  // When a non-canonical text is opened, its nav group moves to the top — bring it into view.
  useEffect(() => {
    if (!nonCanon || !navBookRef.current) return;
    requestAnimationFrame(() => {
      navBookRef.current?.scrollIntoView({ behavior: "auto", block: "start" });
    });
  }, [nonCanon?.id]);
  const navVisible = !isMobile;
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [modesOpen, setModesOpen] = useState(false);
  // In-text search ("find in the text you're reading")
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQ, setSearchQ] = useState("");
  const [searchResults, setSearchResults] = useState(null);   // null = no search run yet
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchCounts, setSearchCounts] = useState(null);     // {verses, matches, capped}
  const [searchHi, setSearchHi] = useState(null);             // {terms, partial, caseSensitive} for result highlighting
  const didSearchRef = useRef(false);                         // true once a search has run (gates the auto-rerun on setting changes)
  const [searchOptsOpen, setSearchOptsOpen] = useState(false);// the collapsible options/range block
  // eSword-style options
  const [searchMode, setSearchMode] = useState("any");        // "any" | "all" | "phrase"
  const [searchPartial, setSearchPartial] = useState(true);   // true = substring, false = whole word
  const [searchCase, setSearchCase] = useState(false);        // case-sensitive
  const [searchExclude, setSearchExclude] = useState("");     // words to exclude
  const [searchFrom, setSearchFrom] = useState("Gen");        // range start (book abbrev)
  const [searchTo, setSearchTo] = useState("Rev");            // range end (book abbrev)

  useEffect(() => {
    api.books().then(data => {
      setBooks(data);
      if (!data.length) return;
      try { localStorage.setItem("lexica.books.v1", JSON.stringify(data)); } catch (e) {}
      // Restore the last reading spot from a previous visit (book/chapter/translation, or an
      // open non-canonical text); fall back to Genesis. An explicit verse jump (nav.book — a
      // click from Search/cross-refs) runs in its own effect and overrides this afterward.
      let saved = null;
      try { saved = JSON.parse(localStorage.getItem("lexica.lib.v1") || "null"); } catch (e) {}
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
        onNavChange?.({ chapter: saved.chapter, highlight: saved.highlight, scroll: true, instant: true });
      }
    });
  }, []);
  // Remember the reading spot so a refresh returns you here instead of Genesis 1.
  useEffect(() => {
    if (!selBook && corpus === "bible") return;   // nothing settled yet
    try {
      localStorage.setItem("lexica.lib.v1", JSON.stringify({
        corpus, book: selBook ? selBook.abbrev : null, chapter: selChapter, translation,
        orderMode, chronoPos, compareSel, highlight: nav?.highlight ?? null,
      }));
    } catch (e) {}
  }, [corpus, selBook, selChapter, translation, orderMode, chronoPos, compareSel, nav?.highlight]);
  // Re-scroll to the placeholder verse when you switch Bible version, so you land back
  // on the verse you marked instead of the top of the chapter. Skip the first render
  // (the version is just being restored); only real switches re-arm the scroll.
  const firstTransRef = useRef(true);
  useEffect(() => {
    if (firstTransRef.current) { firstTransRef.current = false; return; }
    onNavChange?.(n => (n && n.highlight != null) ? { ...n, scroll: true, instant: true } : n);
  }, [translation]);
  // Persist reading-plan progress + the Eras/Days choice.
  useEffect(() => { planSaveAll(planProg); NotesStore.schedulePlanSync(); }, [planProg]);
  // Pull account-synced plan progress back in: when a sync folds the server's copy into
  // localStorage, NotesStore notifies — re-read it, but only swap state if it actually
  // changed (so a no-op notify doesn't loop back into another push).
  useEffect(() => NotesStore.subscribe(() => setPlanProg(prev => {
    const next = planLoadAll();
    return JSON.stringify(next) === JSON.stringify(prev) ? prev : next;
  })), []);
  useEffect(() => { try { localStorage.setItem("lexica.chronoview.v1", chronoView); } catch (e) {} }, [chronoView]);
  // Reading-display toggles (chip/prose, Strong's, interlinear) stick across reloads.
  useEffect(() => { try { localStorage.setItem("lexica.opts.v1", JSON.stringify(libOptions)); } catch (e) {} }, [libOptions]);

  // Load the chronological passage list once (a small static file). If it fails,
  // chronoOn stays false and the Order toggle simply never appears.
  useEffect(() => {
    api.chronological().then(data => {
      setChrono(data);
      try { localStorage.setItem("lexica.chrono.v1", JSON.stringify(data)); } catch (e) {}
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
  const pickPassage = (p) => {
    if (!p) return;
    const b = books.find(bk => bk.abbrev === p.book);
    if (!b) return;
    setChronoPos(p.pos);
    if (corpus !== "bible") setCorpus("bible");
    setSelBook(b);
    setSelChapter(p.start_ch);
  };
  // Step forward/back through the whole passage list (flows across era edges).
  const stepPassage = (delta) => {
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
    const coversCh = (p) => p.book === book && ch >= p.start_ch && ch <= p.end_ch;
    if (v != null) {
      const exact = chrono.passages.find(p => coversCh(p)
        && !(ch === p.start_ch && v < p.start_v)
        && !(ch === p.end_ch && v > p.end_v));
      if (exact) return exact;
    }
    return chrono.passages.find(coversCh) || null;
  };
  // Reading-plan ("Days") wiring. Progress is per reading text; the chips switch text.
  const planTexts = [
    { id: "abp", label: "ABP" }, { id: "kjv", label: "KJV" }, { id: "bsb", label: "BSB" },
    ...(esvOwner ? [{ id: "esv", label: "ESV" }] : []),
    ...(nivOwner ? [{ id: "niv", label: "NIV" }] : []),
  ];
  // The little check on each day IS the control. Each day is INDEPENDENT — checking a
  // day marks just that one done, unchecking clears just that one, so you can skip around
  // and still keep an accurate count. Marking bumps the daily streak (once per calendar
  // day). Marking does NOT yank you to another passage — tap a passage to read.
  const toggleDayDone = (dayNum) => {
    if (!chrono || !chrono.days) return;
    setPlanProg(prev => {
      const cur = planFor(prev, translation);
      const done = new Set(cur.done || []);
      let { streak, last } = cur;
      if (done.has(dayNum)) {
        done.delete(dayNum);                                     // un-mark just this day
      } else {
        done.add(dayNum);                                        // mark just this day
        const today = planYmd();
        if (cur.last === today) { /* already counted a day today — keep streak */ }
        else if (cur.last && planDayDiff(cur.last, today) === 1) streak = (streak || 0) + 1;
        else streak = 1;
        last = today;
      }
      const next = { ...cur, done: Array.from(done).sort((a, b) => a - b), streak, last };
      return { ...prev, [translation]: next };
    });
  };
  const planBundle = {
    view: chronoView, setView: setChronoView,
    progAll: planProg, texts: planTexts, curText: translation,
    onPickText: (id) => pickBible(id),
    onToggleDone: toggleDayDone,
  };
  // Flip reading order. Entering chronological stashes the canonical spot and jumps
  // to the current passage; leaving restores the stashed canonical spot.
  const setOrder = (mode) => {
    if (mode === orderMode) return;
    if (mode === "chronological") {
      canonReturnRef.current = selBook ? { book: selBook, chapter: selChapter } : null;
      setOrderMode("chronological");
      if (chrono) {
        if (corpus !== "bible") setCorpus("bible");
        // Land on the passage that holds the spot you were just reading; only fall back
        // to the last-remembered chronological position if that lookup comes up empty.
        const match = (selBook && passageForRef(selBook.abbrev, selChapter))
          || chrono.passages[chronoPos - 1] || chrono.passages[0];
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
    if (nav.translation) { setTranslation(nav.translation); onTranslationChange?.(nav.translation); }

    if (chronoOn) {
      // EXTERNAL jump (from Search / Lexicon / a note list — flagged `nav.extern`) → drop to
      // canonical so the reference shows in its NORMAL chapter, not dumped mid-passage. But the
      // IN-READER controls (a verse-number cross-ref, a word panel, chasing a cross-ref — all
      // triggered while reading chronologically) STAY in chrono: move to the passage that holds the
      // target verse (passageForRef, narrowed by the verse for a split chapter). If it's already the
      // current passage (e.g. just opening the xref on a verse you're reading) this is a no-op — and
      // the `p.pos !== chronoPos` guard also stops the scroll:false self-update from re-firing it.
      if (nav.extern) {
        setOrderMode("canonical");   // fall through to the canonical reset below
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
    setCorpus("bible");   // a verse reference is a Bible verse — leave any open non-canonical text
    setOtherOpen(false);  // close the "Other" picker if it was open
    // clear the old chapter's verses so the scroll-to-highlight waits for the NEW
    // chapter (otherwise it can fire on a stale same-numbered verse and burn its flag)
    setVerses([]);
    setKjvVerses([]);
    setBsbVerses([]);
    setSelBook(b);
    setSelChapter(nav.chapter || 1);
  }, [nav, books]);

  useEffect(() => {
    if (!selBook || nonCanon || chronoOn) return;   // non-canon + chronological load via their own effects below
    let cancelled = false;
    setLoading(true);
    setVerses([]);
    api.chapter(selBook.abbrev, selChapter)
      .then(data => { if (!cancelled) { setVerses(data); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [selBook && selBook.abbrev, selChapter, corpus, chronoOn]);

  // Chronological span loader: fetch every chapter the current passage covers, for
  // the active text(s). One state object keyed by chapter; the render trims each
  // chapter to the passage's verse window and stitches them with chapter markers.
  useEffect(() => {
    if (!chronoOn || !curPassage || !selBook) return;
    let cancelled = false;
    setChronoLoading(true);
    const { book, start_ch, end_ch } = curPassage;
    const chs = [];
    for (let c = start_ch; c <= end_ch; c++) chs.push(c);
    const need = translation === "parallel" ? compareSel : [translation];
    const fetchChapter = (c) => {
      const jobs = [];
      if (need.includes("abp")) jobs.push(api.chapter(book, c).then(d => ["abp", d]));
      if (need.includes("kjv")) jobs.push(api.kjvChapter(book, c).then(d => ["kjv", d]));
      if (need.includes("bsb")) jobs.push(api.bsbChapter(book, c).then(d => ["bsb", d]));
      if (need.includes("esv")) jobs.push(api.esvChapter(book, c).then(d => ["esv", d]));
      if (need.includes("niv")) jobs.push(api.nivChapter(book, c).then(d => ["niv", d]));
      return Promise.all(jobs).then(pairs => [c, Object.fromEntries(pairs)]);
    };
    Promise.all(chs.map(fetchChapter))
      .then(entries => {
        if (cancelled) return;
        setChronoData({ pos: curPassage.pos, byCh: Object.fromEntries(entries) });
        setChronoLoading(false);
      })
      .catch(() => { if (!cancelled) setChronoLoading(false); });
    return () => { cancelled = true; };
  }, [chronoOn, chronoPos, translation, corpus, compareSel]);

  // Non-canonical text loader (Didache, etc.) — keyed on the active text id + chapter.
  useEffect(() => {
    if (!nonCanon) return;
    let cancelled = false;
    setDidLoading(true);
    setDidVerses([]);
    api.extraChapter(nonCanon.id, selChapter)
      .then(data => { if (!cancelled) { setDidVerses(data); setDidLoading(false); } })
      .catch(() => { if (!cancelled) setDidLoading(false); });
    return () => { cancelled = true; };
  }, [corpus, selChapter]);

  useEffect(() => {
    if (!selBook || nonCanon || chronoOn) return;
    if (translation !== "kjv" && !(translation === "parallel" && compareSel.includes("kjv"))) return;
    let cancelled = false;
    setKjvLoading(true);
    setKjvVerses([]);
    api.kjvChapter(selBook.abbrev, selChapter)
      .then(data => { if (!cancelled) { setKjvVerses(data); setKjvLoading(false); } })
      .catch(() => { if (!cancelled) setKjvLoading(false); });
    return () => { cancelled = true; };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn, compareSel]);

  // BSB chapter loader — when BSB is the reading text OR a selected compare column.
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn) return;
    if (translation !== "bsb" && !(translation === "parallel" && compareSel.includes("bsb"))) return;
    let cancelled = false;
    setBsbLoading(true);
    setBsbVerses([]);
    api.bsbChapter(selBook.abbrev, selChapter)
      .then(data => { if (!cancelled) { setBsbVerses(data); setBsbLoading(false); } })
      .catch(() => { if (!cancelled) setBsbLoading(false); });
    return () => { cancelled = true; };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn, compareSel]);

  // ESV chapter loader — owner-only reading text. Each fetch carries the login
  // token; the server returns 404 (and api.esvChapter yields []) for non-owners.
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn || !esvOwner) return;
    if (translation !== "esv" && !(translation === "parallel" && compareSel.includes("esv"))) return;
    let cancelled = false;
    setEsvLoading(true);
    setEsvVerses([]);
    api.esvChapter(selBook.abbrev, selChapter)
      .then(data => { if (!cancelled) { setEsvVerses(data); setEsvLoading(false); } })
      .catch(() => { if (!cancelled) setEsvLoading(false); });
    return () => { cancelled = true; };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn, esvOwner, compareSel]);

  // NIV chapter loader — owner-only reading text (same as ESV, text only).
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn || !nivOwner) return;
    if (translation !== "niv" && !(translation === "parallel" && compareSel.includes("niv"))) return;
    let cancelled = false;
    setNivLoading(true);
    setNivVerses([]);
    api.nivChapter(selBook.abbrev, selChapter)
      .then(data => { if (!cancelled) { setNivVerses(data); setNivLoading(false); } })
      .catch(() => { if (!cancelled) setNivLoading(false); });
    return () => { cancelled = true; };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn, nivOwner, compareSel]);

  // Hebrew OT interlinear loader — PUBLIC text, OT books only, single-read mode
  // (not wired into compare / chronological yet).
  useEffect(() => {
    if (!selBook || nonCanon || chronoOn) return;
    if (translation !== "heb" || NT_BOOKS.has(selBook.abbrev)) return;
    let cancelled = false;
    setHebLoading(true);
    setHebVerses([]);
    api.hebChapter(selBook.abbrev, selChapter)
      .then(data => { if (!cancelled) { setHebVerses(data); setHebLoading(false); } })
      .catch(() => { if (!cancelled) setHebLoading(false); });
    return () => { cancelled = true; };
  }, [selBook && selBook.abbrev, selChapter, translation, corpus, chronoOn]);

  // Reset the chapter audio when the reading changes — the old mp3 is for the
  // previous chapter/passage. Press Listen to fetch the new one. (chronoPos covers
  // moving between chronological passages, which doesn't change selChapter.)
  useEffect(() => {
    setAudioUrl(null); setAudioKey(null); setAudioBusy(false);
    setAudioPlaying(false); setAudioCur(0); setAudioDur(0);
    // If the change was a page-turn while audio was playing, keep listening: load the
    // new chapter/passage and let the audioUrl effect auto-play it (no need to leave
    // reading mode to press play again).
    if (resumeAudioRef.current) {
      resumeAudioRef.current = false;
      const b = chronoOn ? (curPassage && curPassage.book) : (selBook && selBook.abbrev);
      const c = chronoOn ? (curPassage && curPassage.start_ch) : selChapter;
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
    const fetchUrl = translation === "esv" ? api.esvAudio
                   : translation === "kjv" ? api.kjvAudio
                   : api.bsbAudio;
    fetchUrl(book, ch)
      .then(d => {
        setAudioBusy(false);
        if (d && d.url) { setAudioUrl(d.url); setAudioKey(book + "-" + ch); }
        else flash("No audio for this chapter");
      })
      .catch(() => { setAudioBusy(false); flash("Audio unavailable"); });
  };
  const seekAudio = (e) => {
    const a = audioRef.current; if (!a) return;
    const v = Number(e.target.value);
    a.currentTime = v; setAudioCur(v);
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
    let raf;
    // Wait on a WALL-CLOCK deadline, not a frame count: leaving a heavy view (e.g. the
    // Study argument-graph SVG) drops frames, so a fixed ~30-frame budget could expire
    // before the target chapter finishes loading/painting → verse highlighted but never
    // scrolled to. ~3s of retries outlasts any normal load+paint.
    const deadline = Date.now() + 3000;
    const tryScroll = () => {
      if (highlightRef.current) {
        // Land the verse in the UPPER THIRD (context above, room to read forward) —
        // not dead center. The row carries scroll-margin-top: 30vh (styles.css), so
        // block:"start" stops 30% down. scrollIntoView finds the right scroller on its
        // own (the window, or the fixed focus-mode page), so this works in every mode.
        highlightRef.current.scrollIntoView({ behavior: nav.instant ? "auto" : "smooth", block: "start" });
        onNavChange?.({ ...nav, scroll: false });
      } else if (Date.now() < deadline) {
        raf = requestAnimationFrame(tryScroll); // highlight row not rendered yet — keep waiting
      }
    };
    raf = requestAnimationFrame(tryScroll);
    return () => cancelAnimationFrame(raf);
    // kjvVerses is in the deps so a KJV-mode jump re-runs once the KJV rows render (the highlight
    // ref lives on those rows, which load separately from the ABP set). chronoData/chronoOn re-run it
    // once an internal chrono jump's passage loads, or after an external jump flips to canonical.
  }, [nav?.scroll, nav?.highlight, nav?.chapter, verses, kjvVerses, bsbVerses, loading, selChapter, chronoOn, chronoData, chronoPos]);

  const maxChap = nonCanon ? nonCanon.chapters : (selBook ? selBook.chapters : 1);

  // Pick a non-canonical text (from the "Other" menu / nav): switch the reader to it and
  // start at chapter 1. Parallel/KJV/BSB have no meaning for a non-canonical text,
  // so any of those falls back to the Greek interlinear (ABP single view).
  const pickNonCanon = (t) => {
    setCorpus(t.id);
    setSelChapter(1);
    setOtherOpen(false);
    if (translation === "kjv" || translation === "bsb" || translation === "esv" || translation === "niv" || translation === "parallel") { setTranslation("abp"); onTranslationChange?.("abp"); }
  };
  // Picking a Bible book from the nav returns to the Bible text.
  const selectBook = (b) => {
    setSelBook(b);
    setCorpus("bible");
  };
  // ABP / KJV always select a Bible edition — and clicking either while a
  // non-canonical text is open is the quick way back to the Bible.
  const pickBible = (edition) => {
    setCorpus("bible");
    setTranslation(edition);
    onTranslationChange?.(edition);
    setOtherOpen(false);   // picking a row text collapses the "More" menu if it was open
    if (selBook && selChapter > selBook.chapters) setSelChapter(selBook.chapters);
  };
  // Compare (parallel): pick 2-4 texts to show side by side. The picker's "active"
  // set is the parallel selection when on, else just the current single edition (so
  // opening the menu pre-checks what you're reading). Checking a 2nd text turns
  // compare ON; dropping below 2 falls back to a single view. Bible only.
  const COMPARE_ORDER = ["abp", "kjv", "bsb", "esv", "niv"];
  const compareAvail = COMPARE_ORDER.filter(id => (id === "esv" ? esvOwner : id === "niv" ? nivOwner : true));
  const compareActive = translation === "parallel"
    ? compareSel.filter(id => compareAvail.includes(id))
    : (COMPARE_ORDER.includes(translation) ? [translation] : ["abp"]);
  const toggleCompare = (id) => {
    const set = compareActive.includes(id) ? compareActive.filter(x => x !== id) : [...compareActive, id];
    const ordered = COMPARE_ORDER.filter(x => set.includes(x) && compareAvail.includes(x));
    setCompareSel(ordered);
    if (ordered.length >= 2) { setTranslation("parallel"); onTranslationChange?.("parallel"); }
    else { const fb = ordered[0] || "abp"; setTranslation(fb); onTranslationChange?.(fb); }
  };
  // Plain on/off toggle (used by the mobile sheet header + as a quick flip). Turning
  // on keeps the current compareSel if it already has 2+, else defaults to ABP|KJV.
  const toggleParallel = () => {
    if (translation === "parallel") { setTranslation("abp"); onTranslationChange?.("abp"); }
    else {
      setCompareSel(prev => (prev.filter(id => compareAvail.includes(id)).length >= 2 ? prev : ["abp", "kjv"]));
      setTranslation("parallel"); onTranslationChange?.("parallel");
    }
  };
  // In-text search: which text to search. Bible → the active edition (Parallel
  // searches the English/KJV column); a non-canonical reader → that text's id.
  const readCorpus = corpus === "bible" ? (translation === "parallel" ? "kjv" : translation) : corpus;
  // ESV has no plain-text search route (owner-only reading text), so the reader's
  // in-text find is off for it — every other text supports it.
  const canSearch = !!readCorpus && translation !== "esv" && translation !== "niv";
  const searchName = corpus === "bible" ? readCorpus.toUpperCase() : (nonCanon ? nonCanon.name : "");
  const runTextSearch = () => {
    const q = searchQ.trim();
    if (!q || !readCorpus) return;
    didSearchRef.current = true;
    const terms = searchMode === "phrase" ? [q] : q.split(/\s+/);
    setSearchHi({ terms, partial: searchPartial, caseSensitive: searchCase });
    setSearchLoading(true);
    setSearchResults(null);
    setSearchCounts(null);
    const opts = { mode: searchMode, partial: searchPartial, caseSensitive: searchCase, exclude: searchExclude.trim() };
    // Range only applies to the Bible texts (non-canon is a single book).
    if (corpus === "bible") { opts.from = searchFrom; opts.to = searchTo; }
    api.textSearch(q, readCorpus, opts)
      .then(d => {
        setSearchResults(d.results || []);
        setSearchCounts({ verses: d.verse_count || 0, matches: d.match_count || 0, capped: !!d.capped });
        setSearchLoading(false);
      })
      .catch(() => { setSearchResults([]); setSearchCounts(null); setSearchLoading(false); });
  };
  // Apply a range preset (sets the from/to book pickers).
  const applyRangePreset = (id) => {
    const r = SEARCH_RANGES.find(x => x.id === id);
    if (r) { setSearchFrom(r.from); setSearchTo(r.to); }
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
  const jumpToResult = (r) => {
    setSearchOpen(false);
    if (corpus === "bible") {
      onNavChange?.({ book: r.book, chapter: r.chapter, highlight: r.verse, scroll: true, translation });
    } else {
      setSelChapter(r.chapter);
    }
  };
  const showStrongs     = libOptions.showStrongs     || false;
  const showInterlinear = libOptions.showInterlinear || false;
  const viewMode        = libOptions.viewMode        || "chip";
  const setOpt = (key, val) => setLibOptions(prev => ({ ...prev, [key]: val }));

  // English-only non-canonical texts (e.g. 1 Enoch) and ESV/NIV (no per-word data)
  // are locked to Prose and the Greek/Strong's toggles (Strong's / Interlinear /
  // Chip) are disabled and grayed out. BSB now has its own per-word Strong's data
  // (bsb_words), so it is NOT prose-locked — it gets chip mode like KJV.
  const bsbMode     = translation === "bsb";
  const esvMode     = translation === "esv";
  const nivMode     = translation === "niv";
  const kjvMode     = translation === "kjv";   // KJV has public-domain audio (no key)
  const hebMode     = translation === "heb";   // Hebrew interlinear chips; "prose" flips them left-to-right
  const hebProse    = hebMode && viewMode === "prose";   // L→R word order (each word stays RTL); see .lib-heb-ltr
  const proseLocked = !!(nonCanon && nonCanon.englishOnly) || esvMode || nivMode;
  const chipMode    = !proseLocked && (viewMode === "chip" || showStrongs || showInterlinear);
  const wordMode    = chipMode;
  const kjvWordMode = chipMode;
  // English-only "other books" have no Greek interlinear, so the Strong's / Interlinear
  // toggles stay locked — but they CAN switch between a verse-per-line layout (the
  // "chip" slot) and flowing prose. layoutLocked = can't even pick line vs flow.
  const extraEnglish  = !!(nonCanon && nonCanon.englishOnly);
  const extraLineMode = extraEnglish && viewMode === "chip";
  const layoutLocked  = proseLocked && !extraEnglish;
  const viewChipOn    = hebMode ? !hebProse : (extraEnglish ? viewMode === "chip" : chipMode);

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
  const flattenSpan = (key) => {
    if (!chronoReady || !curPassage) return [];
    const { start_ch, end_ch, start_v, end_v } = curPassage;
    const out = [];
    for (let c = start_ch; c <= end_ch; c++) {
      const arr = (chronoData.byCh[c] && chronoData.byCh[c][key]) || [];
      const lo = c === start_ch ? start_v : 1;
      const hi = c === end_ch ? end_v : Infinity;
      arr.forEach(v => { if (v.verse >= lo && v.verse <= hi) out.push({ ...v, _ch: c }); });
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
  const chronoChapLabel = (c) => {
    const name = selBook ? selBook.name : "";
    if (!curPassage) return `${name} ${c}`;
    const { start_ch, end_ch, start_v, end_v } = curPassage;
    const primaryKey = translation === "parallel" ? (compareSel[0] || "abp") : translation;
    const full = (chronoData && chronoData.byCh[c] && chronoData.byCh[c][primaryKey]) || [];
    const maxV = full.length ? full[full.length - 1].verse : null;   // whole chapter is loaded → last verse = its length
    const lo = c === start_ch ? start_v : 1;
    const hi = c === end_ch ? end_v : maxV;
    const partial = lo > 1 || (maxV != null && hi != null && hi < maxV);
    return partial && hi != null ? `${name} ${c}:${lo}–${hi}` : `${name} ${c}`;
  };
  const withMarks = (arr, renderFn) => {
    const out = []; let lastCh = null;
    arr.forEach(v => {
      if (v._ch != null && v._ch !== lastCh) {
        out.push(<div key={`cm-${v._ch}`} data-ch={v._ch} className="lib-chrono-chapmark">{chronoChapLabel(v._ch)}</div>);
        lastCh = v._ch;
      }
      out.push(renderFn(v));
    });
    return out;
  };
  const abpShowLoading = chronoOn ? (chronoLoading || !chronoReady) : loading;
  const kjvShowLoading = chronoOn ? (chronoLoading || !chronoReady) : kjvLoading;
  const bsbShowLoading = chronoOn ? (chronoLoading || !chronoReady) : bsbLoading;
  const esvShowLoading = chronoOn ? (chronoLoading || !chronoReady) : esvLoading;
  const nivShowLoading = chronoOn ? (chronoLoading || !chronoReady) : nivLoading;
  // Chapter audio (BSB + ESV only). Audio is one file per WHOLE chapter. ONE play/pause
  // icon in the toolbar + a progress bar under the toolbar (desktop AND mobile, same
  // spot). The button targets the chapter you're reading: canonical = the open chapter;
  // chrono = whichever chapter is scrolled into view (viewCh). Press play and you get
  // that chapter; it auto-advances to the next when one ends.
  const audioCapable = bsbMode || esvMode || kjvMode;
  const audioTarget = audioCapable ? {
    book: chronoOn ? (curPassage && curPassage.book) : (selBook && selBook.abbrev),
    ch:   chronoOn ? (viewCh || (curPassage && curPassage.start_ch)) : selChapter,
  } : null;
  const targetKey = audioTarget && audioTarget.book ? (audioTarget.book + "-" + audioTarget.ch) : null;
  const onTargetNow = !!targetKey && audioKey === targetKey;   // the chapter in view IS the loaded one
  // The icon follows ONLY whether sound is playing, so scrolling never desyncs it.
  const showPause = audioPlaying;
  const onToolbarAudio = () => {
    if (!audioTarget || !audioTarget.book || !audioTarget.ch) return;
    const a = audioRef.current;
    if (a && !a.paused) { a.pause(); return; }                 // playing → pause
    if (a && onTargetNow) { a.play().catch(() => {}); return; } // paused on the chapter in view → resume
    loadAudio(audioTarget.book, audioTarget.ch);               // else start / switch to the chapter in view
  };
  const onAudioEnded = () => {
    setAudioPlaying(false);
    if (chronoOn && curPassage && audioKey) {
      const cur = parseInt(audioKey.split("-")[1], 10);               // chrono: roll into the next chapter of the passage
      if (cur < curPassage.end_ch) { loadAudio(curPassage.book, cur + 1); return; }
    }
    setAudioUrl(null); setAudioKey(null);   // canonical end, or chrono passage finished → scrubber goes away
  };
  // The (invisible) audio element renders once while a chapter is loaded so it can play.
  const audioEl = (audioCapable && audioUrl) ? (
    <audio ref={audioRef} src={audioUrl} preload="metadata"
      onLoadedMetadata={e => setAudioDur(e.target.duration || 0)}
      onTimeUpdate={e => setAudioCur(e.target.currentTime || 0)}
      onPlay={() => setAudioPlaying(true)} onPause={() => setAudioPlaying(false)}
      onEnded={onAudioEnded} />
  ) : null;
  const audioProgress = (
    <input className="lib-audio-bar" type="range" min="0" max={audioDur || 0} step="0.1"
      value={Math.min(audioCur, audioDur || 0)} onChange={seekAudio} aria-label="Audio position" />
  );
  // The bottom player only mounts once audio is loaded, so its button just plays/pauses
  // the current track (nothing to "start" — that's the toolbar/cockpit button's job).
  const onDockAudio = () => {
    const a = audioRef.current; if (!a) return;
    if (a.paused) a.play().catch(() => {}); else a.pause();
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
  const dockPlayer = (
    <>
      <button className="lib-audio-dock-btn" onClick={onDockAudio} disabled={audioBusy}
        title={audioPlaying ? "Pause audio" : "Play audio"}
        aria-label={audioPlaying ? "Pause audio" : "Play audio"} aria-pressed={audioPlaying}>
        {audioPlaying ? <Icon.Pause/> : <Icon.Play/>}
      </button>
      {audioProgress}
    </>
  );
  const audioBar = audioEl
    ? <div className="lib-audio-dock">{dockPlayer}{audioEl}</div>
    : (dockClosing ? <div className="lib-audio-dock lib-audio-dock--out">{dockPlayer}</div> : null);
  const audioDockOn = !!audioEl;   // drives the reading-list bottom clearance (desktop + mobile)
  const audioBtn = audioCapable ? (
    <button className={"lib-toggle lib-toggle-icon" + (showPause ? " on" : "")}
      disabled={audioBusy}
      title={showPause ? "Pause audio" : "Play chapter audio"}
      aria-label={showPause ? "Pause audio" : "Play chapter audio"} aria-pressed={showPause}
      onClick={onToolbarAudio}>
      {showPause ? <Icon.Pause/> : <Icon.Play/>}
    </button>
  ) : null;
  // Chrono: track which chapter is scrolled into view (~just above mid-screen), so the
  // toolbar play button AND the chapter overview both follow the chapter you're reading.
  useEffect(() => {
    if (!chronoOn) { setViewCh(null); return; }
    const compute = () => {
      const root = readingRef.current; if (!root) return;
      const marks = root.querySelectorAll(".lib-chrono-chapmark[data-ch]");
      // A single-chapter passage (e.g. Genesis 6, 1 Chronicles 1:1–4) renders no chapter
      // headings, so there's nothing to measure — pin to the passage's own chapter instead
      // of leaving viewCh stuck on the previous passage's chapter (which made the audio +
      // chapter overview load the wrong chapter, e.g. Genesis 4 while reading Genesis 6).
      if (!marks.length) { setViewCh(curPassage ? curPassage.start_ch : null); return; }
      // Switch when a chapter heading passes ~just-above the middle of the screen
      // (not the very top), so the "current" chapter matches what you're reading.
      const threshold = (window.innerHeight || 800) * 0.45;
      let cur = parseInt(marks[0].dataset.ch, 10);
      marks.forEach(m => { if (m.getBoundingClientRect().top <= threshold) cur = parseInt(m.dataset.ch, 10); });
      setViewCh(cur);
    };
    let raf = null;
    const onScroll = () => { if (raf) return; raf = requestAnimationFrame(() => { raf = null; compute(); }); };
    compute();
    window.addEventListener("scroll", onScroll, true);   // capture: also catches a nested scroll panel
    return () => { window.removeEventListener("scroll", onScroll, true); if (raf) cancelAnimationFrame(raf); };
  }, [chronoOn, audioCapable, chronoPos, translation, chronoReady, curPassage && curPassage.start_ch]);

  // Chapter overview target — in chrono it follows the chapter scrolled into view
  // (same cutoff as the audio); otherwise the open chapter.
  const sumBook = nonCanon ? nonCanon.id : (chronoOn && curPassage ? curPassage.book : (selBook && selBook.abbrev));
  const sumChapter = (chronoOn && curPassage) ? (viewCh || curPassage.start_ch) : selChapter;
  const sumLabel = nonCanon ? nonCanon.name : (BOOK_LABELS[sumBook] || sumBook);
  // The chronological reading "day" you're in — drives the Reading-intro panel. In
  // chrono the right panel shows that day's intro instead of the per-chapter overview.
  const currentDay = (chronoOn && chrono && chrono.days)
    ? chrono.days.find(d => d.pos && d.pos.includes(chronoPos)) : null;

  // Tell the app which panel is the current BASE of the detail rail, so a word/xref
  // panel opened on top of it labels its back link correctly ("‹ Intro" vs "‹ Overview").
  const detailBase = (chronoOn && currentDay && chronoPanel === "intro") ? "intro" : "overview";
  useEffect(() => { onDetailBaseChange?.(detailBase); }, [detailBase]);

  // Turn one page: chronological steps a passage, everything else steps a chapter.
  // Shared by the mobile swipe and the desktop arrow keys (focus mode).
  const turnPage = (dir) => {                 // dir: +1 next, -1 prev
    if (chronoOn) {
      const can = dir > 0 ? (chrono && chronoPos < chrono.passages.length) : chronoPos > 1;
      if (!can) return;
      if (audioPlaying) resumeAudioRef.current = true;   // carry the read-along onto the next passage
      stepPassage(dir);
      return;
    }
    const c = selChapter + dir;
    if (c < 1 || c > maxChap) return;
    if (audioPlaying) resumeAudioRef.current = true;     // carry the read-along onto the next chapter
    setSelChapter(c);
    if (!nonCanon) onNavChange?.({ ...nav, book: selBook?.abbrev, chapter: c, highlight: null });
  };

  const swipeRef = React.useRef(null);
  const tapMovedRef = React.useRef(false);
  const swipeHandlers = isMobile ? {
    onTouchStart: (e) => {
      tapMovedRef.current = false;
      swipeRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    },
    onTouchMove: (e) => {
      if (!swipeRef.current) return;
      const dx = e.touches[0].clientX - swipeRef.current.x;
      const dy = e.touches[0].clientY - swipeRef.current.y;
      if (Math.abs(dx) > 10 || Math.abs(dy) > 10) tapMovedRef.current = true;
    },
    // A swipe/scroll that ends over a word must NOT open its panel — only a real tap should.
    onClickCapture: (e) => {
      if (tapMovedRef.current) { e.stopPropagation(); e.preventDefault(); }
    },
    onTouchEnd: (e) => {
      if (!swipeRef.current) return;
      // If the touch produced a text selection (note-making), don't turn the page.
      if (window.getSelection && String(window.getSelection()).trim()) { swipeRef.current = null; return; }
      const dx = e.changedTouches[0].clientX - swipeRef.current.x;
      const dy = e.changedTouches[0].clientY - swipeRef.current.y;
      swipeRef.current = null;
      if (Math.abs(dx) < 50) return;           // too short
      if (Math.abs(dy) > Math.abs(dx) * 0.6) return; // too vertical
      turnPage(dx < 0 ? 1 : -1);               // left swipe = next, right swipe = prev
    },
  } : {};

  // --- Drag-select → note ---------------------------------------------------
  // Walk up from a selection edge to the nearest tagged verse row / word span.
  const _attrUp = (node, attr) => {
    let el = node && node.nodeType === 1 ? node : (node ? node.parentElement : null);
    while (el && el !== readingRef.current && !(el.getAttribute && el.hasAttribute(attr))) el = el.parentElement;
    return el && el.getAttribute ? el.getAttribute(attr) : null;
  };
  const resolveSelection = () => {
    const sel = window.getSelection && window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) { setNoteSel(null); return; }
    const text = sel.toString().trim();
    if (!text) { setNoteSel(null); return; }
    const range = sel.getRangeAt(0);
    if (!readingRef.current || !readingRef.current.contains(range.commonAncestorContainer)) { setNoteSel(null); return; }
    const aV = _attrUp(range.startContainer, "data-note-verse");
    const bV = _attrUp(range.endContainer, "data-note-verse");
    if (aV == null && bV == null) { setNoteSel(null); return; }
    let startV = parseInt(aV != null ? aV : bV, 10);
    let endV = parseInt(bV != null ? bV : aV, 10);
    const aP = _attrUp(range.startContainer, "data-note-pos");
    const bP = _attrUp(range.endContainer, "data-note-pos");
    let startP = aP != null ? parseInt(aP, 10) : null;
    let endP = bP != null ? parseInt(bP, 10) : null;
    if (startV > endV || (startV === endV && (startP || 0) > (endP || 0))) {
      [startV, endV] = [endV, startV];
      [startP, endP] = [endP, startP];
    }
    const bookId = nonCanon ? nonCanon.id : (selBook ? selBook.abbrev : null);
    const bookName = nonCanon ? nonCanon.name : (selBook ? selBook.name : "");
    if (!bookId) { setNoteSel(null); return; }
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
    swallowClickRef.current = false;   // a real selection isn't a dismiss-click
    setNoteSel({
      rect: { top: r.top, left: r.left, width: r.width, height: r.height },
      anchor: {
        corpus, translation,
        book: bookId, bookName, chapter: selCh,
        start: { verse: startV, pos: startP },
        end: { verse: endV, pos: endP },
        snippet: snippet.slice(0, 300), refLabel,
      },
    });
  };
  const addNoteFromSelection = () => {
    if (!noteSel) return;
    // Reuse a note already on this exact text instead of making a duplicate.
    const existing = NotesStore.findAnchor(noteSel.anchor);
    const note = existing || NotesStore.create(noteSel.anchor);
    setNoteSel(null);
    if (window.getSelection) window.getSelection().removeAllRanges();   // dismiss the OS selection toolbar
    onOpenNote && onOpenNote(note.id);
  };
  // A color swatch in the popover → make a highlight (no editor; the paint is it).
  // If this exact text already has a record, just recolor it.
  const addHighlightFromSelection = (color) => {
    if (!noteSel) return;
    const existing = NotesStore.findAnchor(noteSel.anchor);
    if (existing) NotesStore.update(existing.id, { color });
    else NotesStore.create({ ...noteSel.anchor, color });
    setNoteSel(null);
    if (window.getSelection) window.getSelection().removeAllRanges();
  };
  // Copy the selected verse text to the clipboard (also clears the OS bar on mobile).
  const copySelection = () => {
    if (!noteSel) return;
    const txt = noteSel.anchor.snippet || "";
    try { if (navigator.clipboard) navigator.clipboard.writeText(txt); } catch (e) {}
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
    if (!id) { flash("Open a journal page first"); return; }
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
    const onSel = () => { clearTimeout(t); t = setTimeout(() => resolveRef.current(), 200); };
    document.addEventListener("selectionchange", onSel);
    return () => { document.removeEventListener("selectionchange", onSel); clearTimeout(t); };
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
    const onKey = (e) => {
      if (e.target && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
      if (e.key === "Escape") { onToggleFocus && onToggleFocus(); }
      else if (e.key === "ArrowRight") turnPage(1);
      else if (e.key === "ArrowLeft") turnPage(-1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusMode, chronoOn, selChapter, maxChap, nonCanon, chronoPos]);

  // One handler set on the reading area: swipe (mobile) + selection (all).
  const readingHandlers = {
    ...swipeHandlers,
    // A fresh press starts a new interaction: drop any open popover + the suppress flag.
    onMouseDown: () => { if (noteSel) { setNoteSel(null); swallowClickRef.current = true; } justSelectedRef.current = false; },
    onMouseUp: () => resolveSelection(),
    onTouchEnd: (e) => {
      if (swipeHandlers.onTouchEnd) swipeHandlers.onTouchEnd(e);
      setTimeout(resolveSelection, 0);   // let the browser settle the selection first
    },
    onClickCapture: (e) => {
      // The click that ENDS a selection must keep the popover showing — swallow it
      // (so it doesn't also hit a chip / verse number / focus) but leave noteSel set.
      if (justSelectedRef.current) { justSelectedRef.current = false; e.stopPropagation(); e.preventDefault(); return; }
      // A press that closed the popover flagged this click to be eaten — so dismissing
      // the popover doesn't also hit a chip / verse number / focus. (Popover buttons sit
      // outside the reading area, so they're unaffected.)
      if (swallowClickRef.current) { swallowClickRef.current = false; e.stopPropagation(); e.preventDefault(); return; }
      // Desktop focus mode = a read-only page: any tap inside the reader exits focus instead of
      // opening a word/xref panel (those sit behind the non-interactive wash now). Mobile focus
      // KEEPS chips + verse numbers tappable. Skip while the user is selecting text.
      if (focusMode && !isMobile && !(window.getSelection && String(window.getSelection()))) {
        e.stopPropagation(); e.preventDefault(); toggleFocus(); return;
      }
      if (swipeHandlers.onClickCapture) swipeHandlers.onClickCapture(e);
    },
    // Tap on blank space (not a word / verse number / control, and not mid-selection)
    // toggles focus mode. A swipe or a finished selection sets defaultPrevented above.
    onClick: (e) => {
      if (e.defaultPrevented) return;
      if (window.getSelection && String(window.getSelection())) return;
      if (e.target.closest && e.target.closest(".lib-word, .lib-vnum, .lib-flow-vnum, button, a, input, textarea, [contenteditable]")) return;
      toggleFocus();
    },
  };

  // Notes/highlights are looked up per chapter. Canonical reading is one chapter
  // (ch defaults to selChapter); chronological spans several, so every note helper
  // takes the verse's chapter. A small per-render cache avoids re-querying the
  // store for each verse in a chapter.
  const noteBookId = nonCanon ? nonCanon.id : (selBook ? selBook.abbrev : null);
  const _chNoteCache = {};
  const chapterNotesFor = (ch) => {
    if (!(ch in _chNoteCache)) _chNoteCache[ch] = NotesStore.forChapter(corpus, noteBookId, ch);
    return _chNoteCache[ch];
  };
  const noteForVerse = (verse, ch = selChapter) =>
    chapterNotesFor(ch).find(n => verse >= n.start.verse && verse <= ((n.end && n.end.verse) || n.start.verse));
  // Highlight paint: the color (if any) for a given word. Highlights show in
  // EVERY translation (verses always line up). In the text where the highlight
  // was made we paint the exact words; in a DIFFERENT translation we can't line
  // up word-for-word, so a partial highlight rounds up to the whole verse.
  const hiForWord = (verse, pos, ch = selChapter) => {
    for (const n of chapterNotesFor(ch)) {
      if (!n.color) continue;
      const sv = n.start.verse, ev = (n.end && n.end.verse) || sv;
      if (verse < sv || verse > ev) continue;
      const sameText = !n.translation || !translation || n.translation === translation;
      const sp = n.start.pos, ep = n.end ? n.end.pos : null;
      if (!sameText || sp == null || pos == null) return n.color;   // whole-verse paint
      if (verse === sv && pos < sp) continue;
      if (verse === ev && ep != null && pos > ep) continue;
      return n.color;
    }
    return null;
  };
  const hiClass = (verse, pos, ch = selChapter) => { const c = hiForWord(verse, pos, ch); return c ? " lib-hi lib-hi-" + c : ""; };
  // A record is shown with a bookmark icon only when it's a PLAIN bookmark; once it
  // carries a note or a highlight color it shows the note (pencil) icon instead.
  const isBookmarkOnly = (n) => !!(n && n.bookmark && !n.body && !n.color);
  const markerIcon = (n) => isBookmarkOnly(n) ? <Icon.Bookmark/> : <Icon.Note/>;
  const markerLabel = (n) => isBookmarkOnly(n) ? "Open bookmark" : "Open note";
  const noteMarker = (verse, ch = selChapter) => {
    const n = noteForVerse(verse, ch);
    if (!n) return null;
    return (
      <button className="lib-note-dot" title={markerLabel(n)} aria-label={markerLabel(n)}
        onClick={(e) => { e.stopPropagation(); onOpenNote && onOpenNote(n.id); }}>
        {markerIcon(n)}
      </button>
    );
  };
  // Inline variant (prose flow / non-canon) — same icon logic, inline placement.
  const noteDotInline = (verse, ch = selChapter) => {
    const n = noteForVerse(verse, ch);
    if (!n) return null;
    return (
      <button className="lib-note-dot lib-note-dot-inline" title={markerLabel(n)} aria-label={markerLabel(n)}
        onClick={(e) => { e.stopPropagation(); onOpenNote && onOpenNote(n.id); }}>
        {markerIcon(n)}
      </button>
    );
  };
  // Build the whole-verse anchor (incl. a readable snippet) for a verse number.
  const verseAnchor = (verse, fromEl, ch = selChapter) => {
    const bookId = nonCanon ? nonCanon.id : (selBook ? selBook.abbrev : null);
    const bookName = nonCanon ? nonCanon.name : (selBook ? selBook.name : "");
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
        chips.forEach(el => { const eng = el.querySelector(".lib-iw-english"); const t = (eng ? eng.textContent : el.textContent).trim(); if (t) parts.push(t); });
        snippet = parts.join(" ");
      } else {
        const clone = row.cloneNode(true);
        clone.querySelectorAll(".lib-vnum, .lib-flow-vnum, .lib-note-dot").forEach(el => el.remove());
        snippet = (clone.textContent || "").trim();
      }
    }
    return {
      corpus, translation, book: bookId, bookName, chapter: ch,
      start: { verse, pos: null }, end: { verse, pos: null },
      snippet: snippet.slice(0, 300), refLabel: bookName + " " + ch + ":" + verse,
    };
  };
  // Right-click / long-press a verse number opens a small menu (Bookmark · Note ·
  // colors). Left-click / tap stays cross-references.
  const [verseMenu, setVerseMenu] = useState(null);   // { rect, verse, el } | null
  const openVerseMenu = (verse, el, ch = selChapter) => {
    const r = el.getBoundingClientRect();
    setVerseMenu({ rect: { top: r.top, left: r.left, width: r.width, height: r.height }, verse, el, ch });
  };
  const vmBookmark = () => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch); if (!a) return setVerseMenu(null);
    const ex = NotesStore.findAnchor(a);
    if (ex) NotesStore.update(ex.id, { bookmark: true }); else NotesStore.create({ ...a, bookmark: true });
    setVerseMenu(null);
  };
  const vmNote = () => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch); if (!a) return setVerseMenu(null);
    const ex = NotesStore.findAnchor(a);
    const note = ex || NotesStore.create(a);
    setVerseMenu(null);
    onOpenNote && onOpenNote(note.id);
  };
  const vmColor = (color) => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch); if (!a) return setVerseMenu(null);
    const ex = NotesStore.findAnchor(a);
    if (ex) NotesStore.update(ex.id, { color }); else NotesStore.create({ ...a, color });
    setVerseMenu(null);
  };
  // Copy the whole verse text to the clipboard.
  const vmCopy = () => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch); if (!a) return setVerseMenu(null);
    setVerseMenu(null);
    try { if (navigator.clipboard) navigator.clipboard.writeText(a.snippet || ""); } catch (e) {}
    flash("Copied");
  };
  // Send the whole verse to the journal page currently open in the Notes tab.
  const vmJournal = () => {
    const a = verseAnchor(verseMenu.verse, verseMenu.el, verseMenu.ch); if (!a) return setVerseMenu(null);
    setVerseMenu(null);
    const id = NotesStore.getActiveJournal();
    if (!id) { flash("Open a journal page first"); return; }
    NotesStore.appendToJournal(id, journalLine(a));
    flash("Added to journal");
  };
  // Shared press handlers for a verse number: right-click + mobile long-press.
  const vnumPressRef = useRef({ timer: null, fired: false });
  const vnumNoteHandlers = (verse, ch = selChapter) => ({
    onContextMenu: (e) => { e.preventDefault(); openVerseMenu(verse, e.currentTarget, ch); },
    onTouchStart: (e) => {
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
    onTouchEnd: () => clearTimeout(vnumPressRef.current.timer),
  });

  const changeFontSize = (delta) => {
    setLibFontSize(prev => {
      const next = Math.min(24, Math.max(13, prev + delta));
      localStorage.setItem("libFontSize", String(next));
      return next;
    });
  };

  const handleVerseNum = onVerseNumberClick && selBook
    ? (verse, ch = selChapter) => onVerseNumberClick(selBook.abbrev, ch, verse, translation)
    : null;

  // Outer span = the alignment gutter (fixed width, not interactive). Inner span =
  // the actual hit target, sized to the digits, so clicking the empty space beside
  // the number does nothing (and can't start a verse-wide text selection).
  const vnumEl = (verse, ch = selChapter) => (
    <span className="lib-vnum">
      <span
        className={"lib-vnum-num" + (handleVerseNum ? " lib-vnum-click" : "")}
        title={handleVerseNum ? "Click: cross-references · Right-click / long-press: add a note" : undefined}
        onClick={handleVerseNum ? () => {
          if (vnumPressRef.current.fired) { vnumPressRef.current.fired = false; return; }
          handleVerseNum(verse, ch);
        } : undefined}
        {...vnumNoteHandlers(verse, ch)}
      >{verse}</span>
    </span>
  );

  // Verse number for non-canonical texts: opens the note menu on right-click /
  // long-press, but no cross-references (those texts have none). Left-click is a no-op
  // (just swallows the click that follows a long-press).
  const noteVnum = (verse, cls = "lib-vnum") => (
    <span className={cls}>
      <span className="lib-vnum-num lib-vnum-click"
        title="Right-click / long-press: add a note"
        onClick={() => { if (vnumPressRef.current.fired) vnumPressRef.current.fired = false; }}
        {...vnumNoteHandlers(verse)}>{verse}</span>
    </span>
  );

  // The verse renderers moved to 59c-library-render.jsx (LibRender). Build the
  // context bundle they need from our live state + helpers, then bind thin
  // wrappers so the call sites below read exactly as before.
  const _renderCtx = {
    selChapter, selBook, nav, corpus, nonCanon, didVerses,
    wordMode, showInterlinear, showStrongs,
    onWordClick, handleVerseNum,
    hiClass, vnumEl, noteMarker, noteVnum, noteDotInline, vnumNoteHandlers,
    highlightRef, vnumPressRef,
  };
  const renderProseWords = (v) => LibRender.renderProseWords(_renderCtx, v);
  const renderHebVerse = (v) => LibRender.renderHebVerse(_renderCtx, v);
  const renderVerse = (v, sh) => LibRender.renderVerse(_renderCtx, v, sh);
  const renderKjvVerse = (v, svn, sh) => LibRender.renderKjvVerse(_renderCtx, v, svn, sh);
  const renderKjvProse = (v, svn, sh) => LibRender.renderKjvProse(_renderCtx, v, svn, sh);
  const renderBsbVerse = (v, svn, sh) => LibRender.renderBsbVerse(_renderCtx, v, svn, sh);
  const renderPlainVerse = (v, svn, sh) => LibRender.renderPlainVerse(_renderCtx, v, svn, sh);
  const renderFlowVerse = (v, inner) => LibRender.renderFlowVerse(_renderCtx, v, inner);
  const plainFlowInner = (v) => LibRender.plainFlowInner(_renderCtx, v);
  const kjvFlowInner = (v) => LibRender.kjvFlowInner(_renderCtx, v);
  const renderDidacheVerse = (v) => LibRender.renderDidacheVerse(_renderCtx, v);
  const renderDidacheProse = () => LibRender.renderDidacheProse(_renderCtx);
  const renderExtraLines = () => LibRender.renderExtraLines(_renderCtx);
  const renderDidacheParallelVerse = (v) => LibRender.renderDidacheParallelVerse(_renderCtx, v);

  return (
    <div className="library">
      {navVisible && (
        <LibNavPanel
          books={books}
          selBook={selBook}
          setSelBook={selectBook}
          selChapter={selChapter}
          setSelChapter={setSelChapter}
          navBookRef={navBookRef}
          nonCanon={nonCanon}
          nonCanonList={NONCANON}
          onPickNonCanon={pickNonCanon}
          translation={translation}
          corpus={corpus}
          pickBible={pickBible}
          esvOwner={esvOwner}
          nivOwner={nivOwner}
          hebShown={hebShown}
          hebPickable={hebPickable}
          otherOpen={otherOpen}
          setOtherOpen={setOtherOpen}
          chrono={chrono}
          orderMode={orderMode}
          setOrder={setOrder}
          chronoPos={chronoPos}
          onPickPassage={pickPassage}
          plan={planBundle}
        />
      )}
      {!navVisible && mobileNavOpen && (
        <MobileBookPicker
          books={books}
          translation={translation}
          selBook={selBook}
          selChapter={selChapter}
          nonCanon={nonCanon}
          nonCanonList={NONCANON}
          chronoOn={chronoOn}
          chrono={chrono}
          chronoPos={chronoPos}
          onPickPassage={(p) => { pickPassage(p); setMobileNavOpen(false); }}
          onPickPassageNoClose={(p) => pickPassage(p)}
          plan={planBundle}
          onDone={(b, n) => {
            // Clear any lingering jump-highlight (a verse reached via Search/cross-ref) —
            // a manual book/chapter pick shouldn't leave an old verse lit. Point nav at the
            // newly picked Bible book/chapter so the jump effect sees no change and no-ops.
            if (b.id) pickNonCanon(b);
            else { selectBook(b); onNavChange?.({ ...(nav || {}), book: b.abbrev, chapter: n, highlight: null, scroll: false }); }
            setSelChapter(n);
            setMobileNavOpen(false);
          }}
          onClose={() => setMobileNavOpen(false)}
        />
      )}
      {!navVisible && modesOpen && (
        <ModesSheet
          corpus={corpus}
          translation={translation}
          pickBible={pickBible}
          esvOwner={esvOwner}
          nivOwner={nivOwner}
          hebShown={hebShown}
          hebPickable={hebPickable}
          toggleParallel={toggleParallel}
          compareAvail={compareAvail}
          compareActive={compareActive}
          toggleCompare={toggleCompare}
          nonCanonList={NONCANON}
          showStrongs={showStrongs}
          showInterlinear={showInterlinear}
          setOpt={setOpt}
          chipMode={chipMode}
          viewMode={viewMode}
          libFontSize={libFontSize}
          changeFontSize={changeFontSize}
          chrono={chrono}
          orderMode={orderMode}
          setOrder={setOrder}
          theme={theme}
          setTheme={setTheme}
          onClose={() => setModesOpen(false)}
        />
      )}
      <div>
      {navVisible ? (
        <div className="lib-bar">
          <div className="lib-bar-l">
            <div className={"bar-ch" + (chronoOn ? " bar-ch-chrono" : "")}>
              <button
                className="ch-nav"
                disabled={chronoOn ? chronoPos <= 1 : selChapter <= 1}
                onClick={() => turnPage(-1)}
                aria-label={chronoOn ? "Previous passage" : "Previous chapter"}
              >‹</button>
              <button
                className="ch-nav"
                disabled={chronoOn ? (chrono && chronoPos >= chrono.passages.length) : selChapter >= maxChap}
                onClick={() => turnPage(1)}
                aria-label={chronoOn ? "Next passage" : "Next chapter"}
              >›</button>
            </div>
            {chrono && !nonCanon && (
              <>
                <span className="lib-bar-sep" aria-hidden="true"/>
                <div className="seg lib-order-seg">
                  <button className={"seg-b" + (orderMode !== "chronological" ? " on" : "")} title="Canonical order (books in order)" aria-label="Canonical order" onClick={() => setOrder("canonical")}><Icon.Book/></button>
                  <button className={"seg-b" + (orderMode === "chronological" ? " on" : "")} disabled={translation === "heb"} title={translation === "heb" ? "Chronological isn't available for the Hebrew OT" : "Chronological order (events in sequence)"} aria-label="Chronological order" style={translation === "heb" ? { opacity: 0.35, cursor: "default" } : undefined} onClick={() => translation !== "heb" && setOrder("chronological")}><Icon.Clock/></button>
                </div>
              </>
            )}
            <span className="lib-bar-sep" aria-hidden="true"/>
            <button className={"lib-toggle lib-toggle-icon" + (showStrongs ? " on" : "")} disabled={proseLocked} title="Strong's numbers" aria-label="Strong's numbers" aria-pressed={showStrongs} style={proseLocked ? { opacity: 0.35, cursor: "default" } : undefined} onClick={() => !proseLocked && setOpt("showStrongs", !showStrongs)}><Icon.Hash/></button>
            <button className={"lib-toggle lib-toggle-icon" + (showInterlinear ? " on" : "")} disabled={proseLocked} title="Interlinear" aria-label="Interlinear" aria-pressed={showInterlinear} style={proseLocked ? { opacity: 0.35, cursor: "default" } : undefined} onClick={() => !proseLocked && setOpt("showInterlinear", !showInterlinear)}><Icon.Interlinear/></button>
            {!nonCanon && (
              <div className="lib-other-wrap" ref={compareWrapRef}>
                <button className={"lib-toggle lib-toggle-icon" + (translation === "parallel" ? " on" : "")} title="Compare translations" aria-label="Compare translations" aria-pressed={translation === "parallel"} aria-expanded={compareOpen} onClick={() => setCompareOpen(o => !o)}><Icon.Columns/></button>
                {compareOpen && (
                  <>
                    <div className="lib-other-menu lib-compare-menu">
                      <div className="lib-compare-title">Compare (pick 2–4)</div>
                      {compareAvail.map(id => (
                        <label key={id} className="lib-compare-opt">
                          <input type="checkbox" checked={compareActive.includes(id)} onChange={() => toggleCompare(id)} />
                          <span>{id.toUpperCase()}</span>
                        </label>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
            <span className="lib-bar-sep" aria-hidden="true"/>
            <div className="seg lib-view-seg">
              <button
                className={"seg-b" + (viewChipOn ? " on" : "")}
                disabled={layoutLocked}
                title={extraEnglish ? "Line-by-line view" : "Chip view"}
                aria-label={extraEnglish ? "Line-by-line view" : "Chip view"}
                aria-pressed={viewChipOn}
                style={layoutLocked ? { opacity: 0.35, cursor: "default" } : undefined}
                onClick={() => !layoutLocked && setOpt("viewMode", "chip")}
              ><Icon.Grid/></button>
              <button
                className={"seg-b" + (!viewChipOn ? " on" : "")}
                disabled={!hebMode && !extraEnglish && !proseLocked && (showStrongs || showInterlinear)}
                title={hebMode ? "Left-to-right view" : "Prose view"}
                aria-label={hebMode ? "Left-to-right view" : "Prose view"}
                aria-pressed={!viewChipOn}
                style={!hebMode && !extraEnglish && !proseLocked && (showStrongs || showInterlinear) ? { opacity: 0.35, cursor: "default" } : undefined}
                onClick={() => { if (hebMode || extraEnglish) { setOpt("viewMode", "prose"); return; } if (!showStrongs && !showInterlinear) setOpt("viewMode", "prose"); }}
              ><Icon.Lines/></button>
            </div>
            <span className="lib-bar-sep" aria-hidden="true"/>
            {audioBtn}
            <button className={"lib-toggle lib-toggle-icon" + (searchOpen ? " on" : "")} disabled={!canSearch} style={!canSearch ? { opacity: 0.35, cursor: "default" } : undefined} title={canSearch ? "Search this text" : "Search isn't available for this text"} aria-label="Search this text" aria-pressed={searchOpen} onClick={() => { if (canSearch) setSearchOpen(o => !o); }}><Icon.Search/></button>
            <div className="lib-other-wrap" ref={fontWrapRef}>
              <button className="lib-toggle lib-font-btn" onClick={() => setFontOpen(o => !o)} title="Text size" aria-label="Text size">Aa ▾</button>
              {fontOpen && (
                <>
                  <div className="lib-other-scrim" onClick={() => setFontOpen(false)} />
                  <div className="lib-other-menu lib-font-menu">
                    <div className="seg">
                      <button className="seg-b" onClick={() => changeFontSize(-1)}>A−</button>
                      <span className="font-size-lbl">{libFontSize}</span>
                      <button className="seg-b" onClick={() => changeFontSize(+1)}>A+</button>
                    </div>
                    <div className="seg lib-theme-seg">
                      <button className={"seg-b"+(theme==="light"?" on":"")} onClick={() => setTheme("light")}>Light</button>
                      <button className={"seg-b"+(theme==="sepia"?" on":"")} onClick={() => setTheme("sepia")}>Sepia</button>
                      <button className={"seg-b"+(theme==="dark"?" on":"")} onClick={() => setTheme("dark")}>Dark</button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="lib-toolbar">
          <button className="mbar-overview mbar-search" disabled={!canSearch} style={!canSearch ? { opacity: 0.35 } : undefined} onClick={() => { if (canSearch) setSearchOpen(o => !o); }} aria-label="Search this text">
            <Icon.Search/>
          </button>
          <button className={"mbar-overview mbar-audio" + (showPause ? " on" : "")}
            disabled={!audioCapable || audioBusy}
            style={!audioCapable ? { opacity: 0.35 } : undefined}
            onClick={() => { if (audioCapable) onToolbarAudio(); }}
            aria-label={!audioCapable ? "Audio not available for this text" : (showPause ? "Pause audio" : "Play chapter audio")}>
            {showPause ? <Icon.Pause/> : <Icon.Play/>}
          </button>
          <div className="mbar-center">
            <button className="mbar-loc" onClick={() => setMobileNavOpen(true)}>
              {chronoOn ? (
                <span className="mbar-loc-name mbar-loc-chrono">{curPassage
                  ? curPassage.book + " " + curPassage.start_ch + (curPassage.end_ch && curPassage.end_ch !== curPassage.start_ch ? "–" + curPassage.end_ch : "")
                  : "—"}</span>
              ) : (
                <>
                  <span className="mbar-loc-name">{nonCanon ? (nonCanon.abbr || nonCanon.name) : (selBook ? selBook.abbrev : "")}</span>
                  <span className="mbar-loc-ch">{selChapter}</span>
                </>
              )}
            </button>
          </div>
          <button className="mbar-overview" onClick={() => setSummaryOpen(true)} aria-label={chronoOn ? "Reading intro" : "Chapter overview"}>
            <Icon.Info/>
          </button>
          <button className={"mbar-trans" + (modesOpen ? " on" : "")} onClick={() => setModesOpen(true)} aria-label="Reading options">
            <Icon.Modes/>
          </button>
        </div>
      )}

      {audioBar}

      {searchOpen && canSearch && (
        <>
          <div className="lib-search-scrim" onClick={() => setSearchOpen(false)} />
          <div className="lib-search-panel">
            <form className="lib-search-row" onSubmit={(e) => { e.preventDefault(); runTextSearch(); document.activeElement?.blur?.(); }}>
              <input
                className="lib-search-input"
                type="text"
                autoFocus
                enterKeyHint="search"
                placeholder={`Search ${searchName}…`}
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Escape") setSearchOpen(false); }}
              />
              <button type="submit" className="lib-search-go" aria-label="Search">Go</button>
              <button type="button" className="lib-search-x" onClick={() => setSearchOpen(false)} aria-label="Close search">✕</button>
            </form>
            <div className="lib-search-modes">
              <div className="seg lib-search-mode-seg">
                <button className={"seg-b" + (searchMode === "any" ? " on" : "")} onClick={() => setSearchMode("any")}>Any word</button>
                <button className={"seg-b" + (searchMode === "all" ? " on" : "")} onClick={() => setSearchMode("all")}>All words</button>
                <button className={"seg-b" + (searchMode === "phrase" ? " on" : "")} onClick={() => setSearchMode("phrase")}>Phrase</button>
              </div>
              <button className={"lib-search-opts-btn" + (searchOptsOpen ? " on" : "")} onClick={() => setSearchOptsOpen(o => !o)}>Options {searchOptsOpen ? "▴" : "▾"}</button>
            </div>
            {searchOptsOpen && (
              <div className="lib-search-opts">
                {corpus === "bible" && (
                  <div className="lib-search-range">
                    <select className="lib-search-sel" value={activeRangeId} onChange={(e) => applyRangePreset(e.target.value)}>
                      {SEARCH_RANGES.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
                      {activeRangeId === "custom" && <option value="custom">Custom range</option>}
                    </select>
                    <div className="lib-search-range-books">
                      <select className="lib-search-sel" value={searchFrom} onChange={(e) => setSearchFrom(e.target.value)}>
                        {SEARCH_BOOK_LIST.map(b => <option key={b} value={b}>{BOOK_LABELS[b] || b}</option>)}
                      </select>
                      <span className="lib-search-range-dash">to</span>
                      <select className="lib-search-sel" value={searchTo} onChange={(e) => setSearchTo(e.target.value)}>
                        {SEARCH_BOOK_LIST.map(b => <option key={b} value={b}>{BOOK_LABELS[b] || b}</option>)}
                      </select>
                    </div>
                  </div>
                )}
                <label className="lib-search-check"><input type="checkbox" checked={!searchPartial} onChange={(e) => setSearchPartial(!e.target.checked)} /> Whole words only</label>
                <label className="lib-search-check"><input type="checkbox" checked={searchCase} onChange={(e) => setSearchCase(e.target.checked)} /> Case-sensitive</label>
                <form style={{ display: "contents" }} onSubmit={(e) => { e.preventDefault(); runTextSearch(); document.activeElement?.blur?.(); }}>
                  <input
                    className="lib-search-input lib-search-excl-input"
                    type="text"
                    enterKeyHint="search"
                    placeholder="Exclude verses with…"
                    value={searchExclude}
                    onChange={(e) => setSearchExclude(e.target.value)}
                    onBlur={() => { if (didSearchRef.current && searchQ.trim()) runTextSearch(); }}
                  />
                </form>
              </div>
            )}
            <div className="lib-search-results">
              {searchLoading ? (
                <div className="lib-search-status">Searching…</div>
              ) : searchResults == null ? (
                null
              ) : searchResults.length === 0 ? (
                <div className="lib-search-status">No matches.</div>
              ) : (
                <>
                  <div className="lib-search-status">
                    {searchCounts
                      ? `${searchCounts.verses}${searchCounts.capped ? "+" : ""} verse${searchCounts.verses === 1 ? "" : "s"} found, ${searchCounts.matches}${searchCounts.capped ? "+" : ""} match${searchCounts.matches === 1 ? "" : "es"}`
                      : `${searchResults.length} results`}
                  </div>
                  {searchResults.map((r, i) => (
                    <button key={i} className="lib-search-hit" onClick={() => jumpToResult(r)}>
                      <span className="lib-search-hit-ref">{(corpus === "bible" ? (BOOK_LABELS[r.book] || r.book) : searchName)} {r.chapter}:{r.verse}</span>
                      <span className="lib-search-hit-text">{searchHi ? highlightTerms(r.text, searchHi.terms, searchHi.partial, searchHi.caseSensitive) : r.text}</span>
                    </button>
                  ))}
                </>
              )}
            </div>
          </div>
        </>
      )}

      <div ref={readingRef} className={"lib-reading" + (showInterlinear ? " lib-interlinear-on" : "") + (audioDockOn ? " lib-reading--audio" : "")} style={{...(translation === "parallel" ? {paddingTop: 0} : {}), "--lib-font-size": libFontSize + "px"}} {...readingHandlers}>

        {nonCanon ? (
          didLoading ? (
            <div className="lib-loading">Loading…</div>
          ) : nonCanon.englishOnly ? (
            extraLineMode ? renderExtraLines() : renderDidacheProse()
          ) : translation === "parallel" ? (
            <div className="lib-parallel">
              <div className="lib-parallel-header">
                <span className="lib-parallel-label">{nonCanon.name} · Greek</span>
                <span className="lib-parallel-label">English</span>
              </div>
              {didVerses.map(renderDidacheParallelVerse)}
            </div>
          ) : chipMode ? (
            <div className="lib-text-words lib-did-text">
              {didVerses.map(renderDidacheVerse)}
            </div>
          ) : (
            renderDidacheProse()
          )
        ) : translation === "parallel" ? (
          (() => {
            // Compare: render the selected texts (2-4) side by side. Each column
            // knows how to draw its own verse + its own number (shown on desktop,
            // hidden on mobile where the shared number sits above the stack).
            // Plain English columns (BSB/ESV/NIV) carry their own verse number too
            // (the shared one is mobile-only), so every desktop column shows it.
            // They also get the note anchor + highlight paint + note marker so notes
            // and highlights are SHARED across the compare columns: a highlight made
            // in any text paints the whole verse here, the pencil shows, and you can
            // drag-select inside the column to add a new one.
            const plainCol = (v) => {
              const pch = v._ch ?? selChapter;
              return (
                <span className="lib-parallel-plain" data-note-verse={v.verse} data-note-chapter={pch}>
                  {vnumEl(v.verse, pch)}
                  {noteDotInline(v.verse, pch)}
                  <span className={"lib-bsb-text" + hiClass(v.verse, null, pch)}>{v.verse_text}</span>
                </span>
              );
            };
            const colDefs = {
              abp: { label: "ABP", view: abpView, loading: abpShowLoading, render: (v) => renderVerse(v, true) },
              kjv: { label: "KJV", view: kjvView, loading: kjvShowLoading, render: (v) => (kjvWordMode ? renderKjvVerse(v, true, true) : renderKjvProse(v, true, true)) },
              bsb: { label: "BSB", view: bsbView, loading: bsbShowLoading, render: (v) => (bsbWordMode ? renderBsbVerse(v, true, true) : plainCol(v)) },
              esv: { label: "ESV", view: esvView, loading: esvShowLoading, render: plainCol },
              niv: { label: "NIV", view: nivView, loading: nivShowLoading, render: plainCol },
            };
            const cols = compareSel.filter(id => colDefs[id] && compareAvail.includes(id)).map(id => ({ id, ...colDefs[id] }));
            const n = Math.max(cols.length, 1);
            return (
              <div className={"lib-parallel lib-cmp-" + n}>
                <div className="lib-parallel-header">
                  {cols.map(c => <span key={c.id} className="lib-parallel-label">{c.label}</span>)}
                </div>
                {cols.some(c => c.loading) ? (
                  <div className="lib-loading">Loading…</div>
                ) : (() => {
                  // Key by chapter+verse so a chronological span (verse numbers repeat
                  // across chapters) lines the texts up; canonical has one chapter.
                  const cv = (v) => `${v._ch ?? selChapter}-${v.verse}`;
                  const maps = {};
                  cols.forEach(c => { maps[c.id] = Object.fromEntries(c.view.map(v => [cv(v), v])); });
                  // Ordered union of every verse present in any selected text.
                  const seen = new Set(); const order = [];
                  cols.forEach(c => c.view.forEach(v => {
                    const k = cv(v);
                    if (!seen.has(k)) { seen.add(k); order.push({ k, ch: v._ch ?? selChapter, verse: v.verse }); }
                  }));
                  order.sort((a, b) => a.ch - b.ch || a.verse - b.verse);
                  const items = []; let lastCh = null;
                  order.forEach(o => {
                    if (chronoOn && o.ch !== lastCh) { items.push({ type: 'chap', ch: o.ch }); lastCh = o.ch; }
                    let heading = null;
                    for (const c of cols) { const vv = maps[c.id][o.k]; if (vv && vv.heading) { heading = vv.heading; break; } }
                    if (heading) items.push({ type: 'heading', heading, key: `h-${o.k}` });
                    items.push({ type: 'verse', o });
                  });
                  return items.map(item => {
                    if (item.type === 'chap') return <div key={`cm-${item.ch}`} className="lib-chrono-chapmark">{selBook ? selBook.name : ""} {item.ch}</div>;
                    if (item.type === 'heading') return <div key={item.key} className="lib-parallel-section-heading"><div className="pericope-heading">{item.heading}</div></div>;
                    const o = item.o;
                    return (
                      <div key={o.k} className="lib-parallel-verse">
                        <div className="lib-parallel-vnum">{vnumEl(o.verse, o.ch)}</div>
                        {cols.map(c => {
                          const vv = maps[c.id][o.k];
                          return (
                            <div key={c.id} className="lib-parallel-col">
                              <span className="lib-parallel-col-lbl">{c.label}</span>
                              {vv ? c.render(vv) : null}
                            </div>
                          );
                        })}
                      </div>
                    );
                  });
                })()}
              </div>
            );
          })()
        ) : translation === "kjv" ? (
          kjvShowLoading ? (
            <div className="lib-loading">Loading…</div>
          ) : kjvWordMode ? (
            <div className="lib-text-words">
              {withMarks(kjvView, v => renderKjvVerse(v))}
            </div>
          ) : isPoetry ? (
            <div className="lib-text-words">
              {withMarks(kjvView, v => renderKjvProse(v))}
            </div>
          ) : (
            <div className="lib-text-words lib-prose-flow">
              {withMarks(kjvView, v => renderFlowVerse(v, kjvFlowInner(v)))}
            </div>
          )
        ) : translation === "bsb" ? (
          bsbShowLoading ? (
            <div className="lib-loading">Loading…</div>
          ) : bsbWordMode ? (
            <div className="lib-text-words">
              {withMarks(bsbView, v => renderBsbVerse(v))}
            </div>
          ) : isPoetry ? (
            <div className="lib-text-words">
              {withMarks(bsbView, v => renderPlainVerse(v))}
            </div>
          ) : (
            <div className="lib-text-words lib-prose-flow">
              {withMarks(bsbView, v => renderFlowVerse(v, plainFlowInner(v)))}
            </div>
          )
        ) : translation === "esv" ? (
          esvShowLoading ? (
            <div className="lib-loading">Loading…</div>
          ) : isPoetry ? (
            <div className="lib-text-words">
              {withMarks(esvView, v => renderPlainVerse(v))}
            </div>
          ) : (
            <div className="lib-text-words lib-prose-flow">
              {withMarks(esvView, v => renderFlowVerse(v, plainFlowInner(v)))}
            </div>
          )
        ) : translation === "niv" ? (
          nivShowLoading ? (
            <div className="lib-loading">Loading…</div>
          ) : isPoetry ? (
            <div className="lib-text-words">
              {withMarks(nivView, v => renderPlainVerse(v))}
            </div>
          ) : (
            <div className="lib-text-words lib-prose-flow">
              {withMarks(nivView, v => renderFlowVerse(v, plainFlowInner(v)))}
            </div>
          )
        ) : translation === "heb" ? (
          hebLoading ? (
            <div className="lib-loading">Loading…</div>
          ) : (
            <div className={"lib-text-words lib-heb-text" + (hebProse ? " lib-heb-ltr" : "")}>
              {hebVerses.map(renderHebVerse)}
            </div>
          )
        ) : abpShowLoading ? (
          <div className="lib-loading">Loading…</div>
        ) : wordMode ? (
          <div className="lib-text-words">
            {withMarks(abpView, v => renderVerse(v))}
          </div>
        ) : isPoetry ? (
          <div className="lib-text-words">
            {withMarks(abpView, v => renderVerse(v))}
          </div>
        ) : (
          <div className="lib-text-words lib-prose-flow">
            {withMarks(abpView, v => {
              const ch = v._ch ?? selChapter;
              return (
              <React.Fragment key={`${ch}-${v.verse}`}>
                {v.heading && <div className="pericope-heading">{v.heading}</div>}
                <span className="lib-flow-verse" data-note-verse={v.verse} data-note-chapter={ch}>
                  <sup className="lib-flow-vnum"
                       title={handleVerseNum ? "Click: cross-references · Right-click / long-press: add a note" : undefined}
                       onClick={handleVerseNum ? () => {
                         if (vnumPressRef.current.fired) { vnumPressRef.current.fired = false; return; }
                         handleVerseNum(v.verse, ch);
                       } : undefined}
                       {...vnumNoteHandlers(v.verse, ch)}>
                    {v.verse}
                  </sup>
                  {noteDotInline(v.verse, ch)}
                  {renderProseWords(v)}
                </span>
              </React.Fragment>
              );
            })}
          </div>
        )}
      </div>
      </div>
      {focusMode && !isMobile && (() => {
        const canPrev = chronoOn ? chronoPos > 1 : selChapter > 1;
        const canNext = chronoOn ? (chrono && chronoPos < chrono.passages.length) : selChapter < maxChap;
        return (
          <>
            {/* Real wash element (not a ::before) so it CAPTURES clicks: the dimmed chrome is
                non-interactive, and clicking the wash leaves focus mode. */}
            <div className="lib-focus-wash" onClick={toggleFocus} aria-hidden="true" />
            <button className={"lib-focus-arrow lib-focus-arrow-prev" + (audioDockOn ? " lib-focus-arrow--audio" : "")} aria-label="Previous" disabled={!canPrev} onClick={() => turnPage(-1)}>‹</button>
            <button className={"lib-focus-arrow lib-focus-arrow-next" + (audioDockOn ? " lib-focus-arrow--audio" : "")} aria-label="Next" disabled={!canNext} onClick={() => turnPage(1)}>›</button>
          </>
        );
      })()}
      {noteSel && <NoteAddPopover rect={noteSel.rect} isMobile={isMobile} onAdd={addNoteFromSelection} onColor={addHighlightFromSelection} onCopy={copySelection} onJournal={journalFromSelection} />}
      {flashMsg && <div className="lib-flash">{flashMsg}</div>}
      {verseMenu && <VerseNoteMenu rect={verseMenu.rect} isMobile={isMobile} onColor={vmColor} onNote={vmNote} onBookmark={vmBookmark} onCopy={vmCopy} onJournal={vmJournal} onClose={() => setVerseMenu(null)} />}
      {/* Desktop right panel: in chronological it rests on the day's Reading intro
          (with a link to the per-chapter overview, and back); otherwise the overview. */}
      {showSummary && chronoOn && currentDay ? (
        chronoPanel === "overview" ? (
          <SummaryPanel book={sumBook} chapter={sumChapter} bookLabel={sumLabel}
            onBack={() => setChronoPanel("intro")} />
        ) : (
          <DayIntroPanel day={currentDay} chrono={chrono} onPickPassage={pickPassage}
            onOverview={() => setChronoPanel("overview")} />
        )
      ) : showSummary && (selBook || nonCanon) ? (
        <SummaryPanel book={sumBook} chapter={sumChapter} bookLabel={sumLabel} />
      ) : null}
      {/* Mobile overview sheet (ⓘ): chrono shows the Reading intro (toggle to the chapter overview). */}
      {isMobile && summaryOpen && chronoOn && currentDay ? (
        chronoPanel === "overview" ? (
          <SummaryPanel isMobile book={sumBook} chapter={sumChapter} bookLabel={sumLabel}
            onClose={() => setSummaryOpen(false)} onBack={() => setChronoPanel("intro")} />
        ) : (
          <DayIntroPanel isMobile day={currentDay} chrono={chrono}
            onClose={() => setSummaryOpen(false)}
            onPickPassage={(p) => { pickPassage(p); setSummaryOpen(false); }}
            onOverview={() => setChronoPanel("overview")} />
        )
      ) : isMobile && summaryOpen && (selBook || nonCanon) ? (
        <SummaryPanel isMobile onClose={() => setSummaryOpen(false)}
          book={sumBook} chapter={sumChapter} bookLabel={sumLabel} />
      ) : null}
    </div>
  );
}
