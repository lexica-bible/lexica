// 59b — Library nav/picker sub-components + the non-canon text list + the
//       restore-from-localStorage helpers, split out of 60-library.jsx.
//       Loads between 59a-library-helpers and 60-library.
//       Holds: LibNavPanel · MobileBookPicker · ModesSheet · _BOOK_DIV ·
//              NONCANON + nonCanonGroups · readLibSaved/readCachedBooks/readCachedChrono.
// ============================================================
// LIB NAV PANEL — desktop left sidebar (≥1100px)
// ============================================================

const _BOOK_DIV = {
  Gen:"Law",Exo:"Law",Lev:"Law",Num:"Law",Deu:"Law",
  Jos:"History",Jdg:"History",Rth:"History","1Sa":"History","2Sa":"History",
  "1Ki":"History","2Ki":"History","1Ch":"History","2Ch":"History",Ezr:"History",Neh:"History",Est:"History",
  Job:"Wisdom",Psa:"Wisdom",Pro:"Wisdom",Ecc:"Wisdom",Son:"Wisdom",
  Isa:"Major Prophets",Jer:"Major Prophets",Lam:"Major Prophets",Eze:"Major Prophets",Dan:"Major Prophets",
  Hos:"Minor Prophets",Joe:"Minor Prophets",Amo:"Minor Prophets",Oba:"Minor Prophets",
  Jon:"Minor Prophets",Mic:"Minor Prophets",Nah:"Minor Prophets",Hab:"Minor Prophets",
  Zep:"Minor Prophets",Hag:"Minor Prophets",Zec:"Minor Prophets",Mal:"Minor Prophets",
  Mat:"Gospels",Mar:"Gospels",Luk:"Gospels",Joh:"Gospels",
  Act:"History",
  Rom:"Pauline Epistles","1Co":"Pauline Epistles","2Co":"Pauline Epistles",
  Gal:"Pauline Epistles",Eph:"Pauline Epistles",Php:"Pauline Epistles",
  Col:"Pauline Epistles","1Th":"Pauline Epistles","2Th":"Pauline Epistles",
  "1Ti":"Pauline Epistles","2Ti":"Pauline Epistles",Tit:"Pauline Epistles",Phm:"Pauline Epistles",
  Heb:"General Epistles",Jas:"General Epistles",
  "1Pe":"General Epistles","2Pe":"General Epistles",
  "1Jn":"General Epistles","2Jn":"General Epistles","3Jn":"General Epistles",
  Jud:"General Epistles",Rev:"Apocalyptic",
};

// Group a testament's books by their _BOOK_DIV division, preserving canon order —
// quiet division waypoints inside the mobile picker's single testament grid.
function divisionsOf(bks) {
  const order = [], map = {};
  for (const b of bks) {
    const d = _BOOK_DIV[b.abbrev] || "";
    if (!map[d]) { map[d] = []; order.push(d); }
    map[d].push(b);
  }
  return order.map(d => ({ div: d, books: map[d] }));
}

function LibNavPanel({ books, selBook, setSelBook, selChapter, setSelChapter, isOverlay, onClose, navBookRef, nonCanon, nonCanonList, onPickNonCanon, translation, corpus, pickBible, esvOwner, nivOwner, hebShown, hebPickable, otherOpen, setOtherOpen, chrono, orderMode, setOrder, chronoPos, onPickPassage, plan }) {
  const [query, setQuery] = useState("");
  const chronoMode = orderMode === "chronological" && chrono && !nonCanon;
  // The era a passage belongs to, so the active passage's era starts expanded.
  const curEraId = chrono && chrono.passages[chronoPos - 1] ? chrono.passages[chronoPos - 1].era : null;
  const [openEras, setOpenEras] = useState(() => new Set(curEraId ? [curEraId] : []));
  const eraRefs = useRef({});
  const toggleEra = (id) => setOpenEras(s => {
    const n = new Set(s);
    const opening = !n.has(id);
    opening ? n.add(id) : n.delete(id);
    // On open, scroll the era to the top of the list — only the inner list, never the
    // page (set scrollTop directly, like the Days month scroll).
    if (opening) requestAnimationFrame(() => {
      const el = eraRefs.current[id];
      const sc = el && el.closest(".nav-scroll, .mpick-scroll");
      if (el && sc) sc.scrollTo({ top: sc.scrollTop + el.getBoundingClientRect().top - sc.getBoundingClientRect().top, behavior: "smooth" });
    });
    return n;
  });
  const navActiveRef = useRef(null);   // the active passage button (scroll into view)
  // Keep the active passage's era open and scroll it into view as you step through.
  useEffect(() => {
    if (!chronoMode || !curEraId) return;
    setOpenEras(s => s.has(curEraId) ? s : new Set(s).add(curEraId));
    requestAnimationFrame(() => navActiveRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
  }, [chronoMode, chronoPos, curEraId]);
  // "Other" menu groups start collapsed (the list is long) — except the group of the
  // text that's currently open, so the active pick stays visible.
  const [openGroups, setOpenGroups] = useState(() => new Set(["Bibles", ...(nonCanon ? [nonCanon.group] : [])]));
  const toggleGroup = (g) => setOpenGroups(s => {
    const n = new Set(s);
    n.has(g) ? n.delete(g) : n.add(g);
    return n;
  });

  // The "More" popout closes on a click outside it (or Esc) — proper menu behaviour
  // now it floats over the book list instead of sitting inline.
  const sourceWrapRef = useRef(null);
  useEffect(() => {
    if (!otherOpen) return;
    const onDown = (e) => {
      if (sourceWrapRef.current && !sourceWrapRef.current.contains(e.target)) {
        setOtherOpen(false);
        // Swallow the dismiss click so it doesn't also land on a word chip behind the menu.
        const swallow = (ev) => { ev.stopPropagation(); ev.preventDefault(); };
        document.addEventListener("click", swallow, { capture: true, once: true });
        setTimeout(() => document.removeEventListener("click", swallow, { capture: true }), 350);
      }
    };
    const onKey = (e) => { if (e.key === "Escape") setOtherOpen(false); };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("pointerdown", onDown); document.removeEventListener("keydown", onKey); };
  }, [otherOpen, setOtherOpen]);

  // Book accordion: which book's chapter grid is expanded. Starts collapsed (null)
  // — the current chapter shows next to the book name until you open it. Click the
  // open book to collapse it again; click another book to switch + open that one.
  const [navOpenBook, setNavOpenBook] = useState(null);
  const onBookClick = (b) => {
    if (navOpenBook === b.abbrev) { setNavOpenBook(null); return; }   // tap the open book to collapse
    if (!(selBook && b.abbrev === selBook.abbrev)) { setSelBook(b); setSelChapter(1); }
    setNavOpenBook(b.abbrev);
  };

  const filtered = useMemo(() => {
    // Hebrew is OT-only (no Hebrew NT), so drop the NT books from the list in HEB mode.
    const base = translation === "heb" ? books.filter(b => !NT_BOOKS.has(b.abbrev)) : books;
    const q = query.trim().toLowerCase();
    if (!q) return base;
    return base.filter(b => b.name.toLowerCase().includes(q) || b.abbrev.toLowerCase().includes(q));
  }, [books, query, translation]);

  const groups = useMemo(() => {
    const out = [];
    let cur = null;
    for (const b of filtered) {
      const t = NT_BOOKS.has(b.abbrev) ? "NT" : "OT";
      const div = _BOOK_DIV[b.abbrev] || "";
      const key = t + " · " + div;
      if (!cur || cur.key !== key) { cur = { key, t, div, books: [] }; out.push(cur); }
      cur.books.push(b);
    }
    return out;
  }, [filtered]);

  // When a non-canonical text is active, the nav shows that text's chapter chips
  // (picking WHICH non-canon text happens via the "Other" menu in the source bar).
  const nonCanonActive = nonCanon ? (
    <div className="nav-group">
      <div className="nav-div">
        <span className="nav-div-t">Other</span>
        <span className="nav-div-n">{nonCanon.name}</span>
      </div>
      <div ref={navBookRef}>
        <button className="nav-book on"><span className="nav-book-name">{nonCanon.name}</span></button>
        <div className="nav-chips">
          {Array.from({ length: nonCanon.chapters }, (_, i) => i + 1).map(n => (
            <button
              key={n}
              className={"ch-chip" + (n === selChapter ? " on" : "")}
              onClick={() => setSelChapter(n)}
            >{n}</button>
          ))}
        </div>
      </div>
    </div>
  ) : null;

  // "More" button: ABP/BSB stay one-click and HEB takes the third top slot; KJV is
  // demoted INTO this menu beside ESV/NIV (BSB is the default English now). ESV/NIV +
  // the non-canon books also live here, so the row stays at four buttons. Deploy-safe:
  // if heb.db isn't loaded (hebShown false) HEB can't fill the slot, so KJV stays up
  // top and is NOT listed in More.
  const kjvInMore = hebShown;
  const extraActive = !nonCanon && (
    translation === "esv" || translation === "niv" || (kjvInMore && translation === "kjv")
  );
  const moreActive = !!nonCanon || extraActive;
  const moreLabel = nonCanon ? (nonCanon.abbr || nonCanon.name)
    : translation === "esv" ? "ESV"
    : translation === "niv" ? "NIV"
    : (kjvInMore && translation === "kjv") ? "KJV" : "More";

  return (
    <nav className={"nav" + (isOverlay ? " nav-overlay" : "")} aria-label="Books">
      <div className="nav-top">
        {isOverlay && <button className="nav-x" onClick={onClose} aria-label="Close">✕</button>}
      </div>
      {/* Text-source picker — ABP/BSB one-click, HEB the third top slot; KJV/ESV/NIV +
          non-canon in "More". Wrapper is the anchor for the floating "More" popout below. */}
      <div className="nav-source-wrap" ref={sourceWrapRef}>
      <div className="nav-source">
        <div className="seg nav-source-seg">
          <button className={"seg-b" + (!nonCanon && translation === "abp" ? " on" : "")} onClick={() => pickBible("abp")}>ABP</button>
          <button className={"seg-b" + (!nonCanon && translation === "bsb" ? " on" : "")} onClick={() => pickBible("bsb")}>BSB</button>
          {/* Third slot = HEB (grayed on NT books — OT-only). Falls back to KJV only if
              heb.db isn't loaded, so the row never loses its third Bible. */}
          {hebShown ? (
            <button className={"seg-b" + (!nonCanon && translation === "heb" ? " on" : "")}
              disabled={!hebPickable} style={!hebPickable ? { opacity: 0.35, cursor: "default" } : undefined}
              title={!hebPickable ? "Old Testament books only" : undefined}
              onClick={() => { if (hebPickable) pickBible("heb"); }}>HEB</button>
          ) : (
            <button className={"seg-b" + (!nonCanon && translation === "kjv" ? " on" : "")} onClick={() => pickBible("kjv")}>KJV</button>
          )}
          <button className={"seg-b nav-other-seg" + (moreActive ? " on" : "")} onClick={() => setOtherOpen(o => !o)} aria-expanded={otherOpen}>
            <span className="nav-other-lbl">{moreLabel}</span>
            <span className={"nav-other-caret" + (otherOpen ? " open" : "")}>▾</span>
          </button>
        </div>
      </div>
      {/* Reading-order toggle (Canonical | Chronological) lives in the top toolbar.
          The nav just reflects orderMode: era→passage list when chronological. */}
      {/* "Other" books (KJV/ESV/NIV + non-canon) open in a floating panel anchored under the
          source picker; a faint dim sits behind it over the book list (design 2026-06-19). */}
      {otherOpen && <div className="nav-other-dim" onClick={() => setOtherOpen(false)} />}
      {otherOpen && (
        <div className="nav-other-inline">
          {(esvOwner || nivOwner || hebShown) && (() => {
            const bibles = [
              // KJV is demoted here only when HEB holds the top slot; if heb.db is
              // absent (kjvInMore false) KJV stays up top and is left out of this list.
              kjvInMore && { id: "kjv", name: "KJV" },
              esvOwner && { id: "esv", name: "ESV" },
              nivOwner && { id: "niv", name: "NIV" },
            ].filter(Boolean);
            const open = openGroups.has("Bibles");
            return (
              <React.Fragment>
                <button className={"lib-other-head lib-other-head-btn" + (open ? " open" : "")}
                  onClick={() => toggleGroup("Bibles")} aria-expanded={open}>
                  <span className="lib-other-head-caret">▸</span>
                  <span className="lib-other-head-lbl">Bibles</span>
                  <span className="lib-other-head-count">{bibles.length}</span>
                </button>
                {open && bibles.map(b => (
                  <button key={b.id}
                    className={"lib-other-item" + (!nonCanon && translation === b.id ? " on" : "")}
                    disabled={b.disabled} title={b.title}
                    onClick={() => { pickBible(b.id); setOtherOpen(false); if (isOverlay) onClose(); }}>{b.name}</button>
                ))}
              </React.Fragment>
            );
          })()}
          {nonCanonList && nonCanonList.length > 0 && nonCanonGroups(nonCanonList).map(grp => {
            const open = openGroups.has(grp.group);
            return (
              <React.Fragment key={grp.group}>
                <button className={"lib-other-head lib-other-head-btn" + (open ? " open" : "")}
                  onClick={() => toggleGroup(grp.group)} aria-expanded={open}>
                  <span className="lib-other-head-caret">▸</span>
                  <span className="lib-other-head-lbl">{grp.group}</span>
                  <span className="lib-other-head-count">{grp.items.length}</span>
                </button>
                {open && grp.items.map(t => (
                  <button key={t.id}
                    className={"lib-other-item" + (nonCanon && nonCanon.id === t.id ? " on" : "")}
                    onClick={() => { onPickNonCanon(t); setOtherOpen(false); if (isOverlay) onClose(); }}>{t.name}</button>
                ))}
              </React.Fragment>
            );
          })}
        </div>
      )}
      </div>
      {chronoMode && plan ? (
        <div className="nav-plan">
          <div className="plan-toggle">
            <button className={"plan-toggle-b" + (plan.view !== "days" ? " on" : "")} onClick={() => plan.setView("eras")}>Eras</button>
            <button className={"plan-toggle-b" + (plan.view === "days" ? " on" : "")} onClick={() => plan.setView("days")}>Days</button>
          </div>
          {plan.view === "days" ? (
            <DayPlanView chrono={chrono} curText={plan.curText} texts={plan.texts} progAll={plan.progAll}
              chronoPos={chronoPos}
              onPickText={plan.onPickText} onToggleDone={plan.onToggleDone}
              onPickPassage={(p) => { onPickPassage(p); if (isOverlay) onClose(); }} />
          ) : (
            <div className="nav-scroll nav-plan-scroll">
              <div className="nav-eras-inner">
              {chrono.eras.map(era => {
          const open = openEras.has(era.id);
          const eraPassages = chrono.passages.filter(p => p.era === era.id);
          return (
            <div className="nav-group" key={era.id} ref={el => { if (el) eraRefs.current[era.id] = el; }}>
              <button className={"nav-era" + (open ? " open" : "")} onClick={() => toggleEra(era.id)}
                aria-expanded={open} title={era.blurb}>
                <span className="nav-era-name">{era.name}</span>
                <span className="nav-era-count">{eraPassages.length}</span>
              </button>
              {open && (
                <div className="nav-passages">
                  {eraPassages.map(p => {
                    const active = p.pos === chronoPos;
                    return (
                      <button key={p.pos} ref={active ? navActiveRef : null}
                        className={"nav-passage" + (active ? " on" : "")}
                        onClick={() => { onPickPassage(p); if (isOverlay) onClose(); }}>{p.label}</button>
                    );
                  })}
                </div>
              )}
            </div>
          );
              })}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="nav-scroll">
        {nonCanon && nonCanonActive}
        {!nonCanon && groups.map((g, gi) => {
          // Show the OT/NT tag only when the testament changes (once at the top,
          // once at the OT→NT boundary) — repeating it on every group was noise.
          const newTestament = gi === 0 || groups[gi - 1].t !== g.t;
          const tClass = g.t === "OT" ? " nav-group--ot" : g.t === "NT" ? " nav-group--nt" : "";
          return (
          <div className={"nav-group" + (newTestament ? " nav-group--tnew" : "") + tClass} key={g.key}>
            {newTestament && (
              <div className="nav-testament">{g.t === "OT" ? "Old Testament" : "New Testament"}</div>
            )}
            <div className="nav-div">
              <span className="nav-div-n">{g.div}</span>
            </div>
            {g.books.map(b => {
              const active = !nonCanon && selBook && b.abbrev === selBook.abbrev;
              const open = navOpenBook === b.abbrev;
              return (
                <div key={b.abbrev} ref={active ? navBookRef : null}>
                  <button
                    className={"nav-book" + (active ? " on" : "") + (open ? " open" : "")}
                    onClick={() => onBookClick(b)}
                    aria-expanded={open}
                  >
                    <span className="nav-book-name">{b.name}</span>
                    {active && !open && <span className="nav-book-ch">{selChapter}</span>}
                    {!open && <span className="nav-book-count">{b.chapters}</span>}
                  </button>
                  {open && (
                    <div className="nav-chips">
                      {Array.from({ length: b.chapters }, (_, i) => i + 1).map(n => (
                        <button
                          key={n}
                          className={"ch-chip" + (n === selChapter ? " on" : "")}
                          onClick={() => { setSelChapter(n); if (isOverlay) onClose(); }}
                        >{n}</button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          );
        })}
      </div>
      )}
    </nav>
  );
}

// ============================================================
// MOBILE BOOK PICKER — full-screen, two-screen (book grid → chapter grid)
// ============================================================
function MobileBookPicker({ books, selBook, selChapter, nonCanon, nonCanonList, onDone, onClose, chronoOn, chrono, chronoPos, onPickPassage, onPickPassageNoClose, translation, plan }) {
  // A non-canonical book is identified by its `id`; a Bible book by its `abbrev`.
  const isNC = b => !!(b && b.id);
  // Chronological: the picker shows eras → passages instead of books → chapters.
  const curEraId = chrono && chrono.passages[chronoPos - 1] ? chrono.passages[chronoPos - 1].era : null;
  const [openEras, setOpenEras] = useState(() => new Set(curEraId ? [curEraId] : []));
  const eraRefs = useRef({});
  const toggleEra = (id) => setOpenEras(s => {
    const n = new Set(s);
    const opening = !n.has(id);
    opening ? n.add(id) : n.delete(id);
    // On open, scroll the era to the top of the list — only the inner list, never the
    // page (set scrollTop directly, like the Days month scroll).
    if (opening) requestAnimationFrame(() => {
      const el = eraRefs.current[id];
      const sc = el && el.closest(".nav-scroll, .mpick-scroll");
      if (el && sc) sc.scrollTo({ top: sc.scrollTop + el.getBoundingClientRect().top - sc.getBoundingClientRect().top, behavior: "smooth" });
    });
    return n;
  });
  // Open straight to the chapter grid of whatever you're currently reading — an open
  // non-canonical text OR the current Bible book — so you can change chapter right away
  // instead of landing on the generic book list. "‹ Books" steps back to switch books.
  const startBook = nonCanon || selBook || null;
  // Open to the book list, not the chapter grid — picking a book steps into chapters.
  const [screen, setScreen] = useState("book");
  const [pickedBook, setPickedBook] = useState(startBook);
  // Every section (OT, NT, and each non-canonical group) starts collapsed EXCEPT the
  // one you're currently reading: the testament of the open Bible book, or the active
  // non-canonical text's group.
  const [openGroups, setOpenGroups] = useState(() => new Set([
    nonCanon ? nonCanon.group
             : (selBook && NT_BOOKS.has(selBook.abbrev) ? "NT" : "OT"),
  ]));
  const toggleGroup = (g) => setOpenGroups(s => {
    const n = new Set(s);
    n.has(g) ? n.delete(g) : n.add(g);
    return n;
  });
  // Same swipe-down-to-close + at-top scroll arming as the hero / xref sheets.
  // ONE stable root so the refs survive the book→chapter screen switch.
  const { sheetRef, scrollRef } = useSwipeToDismiss(onClose);

  // Hebrew is OT-only (no Hebrew NT), so drop the NT section in HEB mode — mirrors the
  // desktop nav's `filtered` useMemo.
  const otBooks = books.filter(b => !NT_BOOKS.has(b.abbrev));
  const ntBooks = translation === "heb" ? [] : books.filter(b => NT_BOOKS.has(b.abbrev));
  const onChapter = screen === "chapter";
  const isActive = b => isNC(b) ? (nonCanon && nonCanon.id === b.id)
                                : (selBook && b.abbrev === selBook.abbrev);

  return (
    <div className="mpick" ref={sheetRef}>
      <div className="sheet-drag-zone" aria-hidden="true"><div className="sheet-handle"></div></div>
      <div className="mpick-head">
        {!chronoOn && onChapter
          ? <button className="mpick-back" onClick={() => setScreen("book")}>‹ Books</button>
          : <span className="mpick-head-spacer" />}
        <span className="mpick-title">{chronoOn ? "Chronological" : (onChapter ? pickedBook.name : "Books")}</span>
        <button className="mpick-x" onClick={onClose}>✕</button>
      </div>
      {chronoOn && plan && (
        <div className="plan-toggle mpick-toggle">
          <button className={"plan-toggle-b" + (plan.view !== "days" ? " on" : "")} onClick={() => plan.setView("eras")}>Eras</button>
          <button className={"plan-toggle-b" + (plan.view === "days" ? " on" : "")} onClick={() => plan.setView("days")}>Days</button>
        </div>
      )}
      <div className={"mpick-scroll" + (chronoOn && plan && plan.view === "days" ? " mpick-scroll--plan" : "")} ref={scrollRef}>
        {chronoOn ? (
          plan && plan.view === "days" ? (
            <DayPlanView isMobile chrono={chrono} curText={plan.curText} texts={plan.texts} progAll={plan.progAll}
              chronoPos={chronoPos}
              onPickText={plan.onPickText} onToggleDone={plan.onToggleDone} onPickPassage={onPickPassageNoClose || onPickPassage} />
          ) : chrono.eras.map(era => {
            const open = openEras.has(era.id);
            const eraPassages = chrono.passages.filter(p => p.era === era.id);
            return (
              <div key={era.id} className="mpick-section" ref={el => { if (el) eraRefs.current[era.id] = el; }}>
                <button className={"mpick-sec-label mpick-sec-btn" + (open ? " open" : "")} onClick={() => toggleEra(era.id)} aria-expanded={open}>
                  <span className="mpick-sec-caret">▸</span>
                  <span className="mpick-sec-name">{era.name}</span>
                  <span className="mpick-sec-count">{eraPassages.length}</span>
                </button>
                {open && (
                  <div className="mpick-passages">
                    {eraPassages.map(p => (
                      <button key={p.pos} className={"mpick-passage" + (p.pos === chronoPos ? " on" : "")} onClick={() => onPickPassage(p)}>{p.label}</button>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        ) : onChapter ? (
          <div className="mpick-grid">
            {Array.from({ length: pickedBook.chapters }, (_, i) => i + 1).map(n => {
              const active = isActive(pickedBook) && n === selChapter;
              return <button key={n} className={"mpick-btn" + (active ? " on" : "")} onClick={() => onDone(pickedBook, n)}>{n}</button>;
            })}
          </div>
        ) : (
          [["OT", otBooks], ["NT", ntBooks]].filter(([, bks]) => bks.length).map(([label, bks]) => {
            const open = openGroups.has(label);
            return (
              <div key={label} className="mpick-section">
                <button className={"mpick-sec-label mpick-sec-btn" + (open ? " open" : "")} onClick={() => toggleGroup(label)} aria-expanded={open}>
                  <span className="mpick-sec-caret">▸</span>
                  <span className="mpick-sec-name">{label}</span>
                  <span className="mpick-sec-count">{bks.length}</span>
                </button>
                {open && (
                  <div className="mpick-grid">
                    {divisionsOf(bks).map(d => (
                      <React.Fragment key={d.div}>
                        <div className="mpick-div">{d.div}</div>
                        {d.books.map(b => (
                          <button key={b.abbrev} className={"mpick-btn" + (isActive(b) ? " on" : "")} onClick={() => { setPickedBook(b); setScreen("chapter"); }}>
                            {b.abbrev.toUpperCase()}
                          </button>
                        ))}
                      </React.Fragment>
                    ))}
                  </div>
                )}
              </div>
            );
          }).concat((nonCanonList || []).length ? nonCanonGroups(nonCanonList).map(grp => {
            const open = openGroups.has(grp.group);
            return (
              <div key={grp.group} className="mpick-section">
                <button className={"mpick-sec-label mpick-sec-btn" + (open ? " open" : "")} onClick={() => toggleGroup(grp.group)} aria-expanded={open}>
                  <span className="mpick-sec-caret">▸</span>
                  <span className="mpick-sec-name">{grp.group}</span>
                  <span className="mpick-sec-count">{grp.items.length}</span>
                </button>
                {open && (
                  <div className="mpick-grid">
                    {grp.items.map(t => (
                      <button key={t.id} className={"mpick-btn mpick-btn-nc" + (isActive(t) ? " on" : "")} onClick={() => { setPickedBook(t); setScreen("chapter"); }}>
                        {t.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          }) : [])
        )}
      </div>
    </div>
  );
}

// ============================================================
// MOBILE READING OPTIONS — bottom sheet (swipe-to-dismiss, scrollable).
// Compacted to three groups: Text · Study layer · Display.
// ============================================================
function ModesSheet({
  corpus, translation, pickBible, esvOwner, nivOwner, hebShown, hebPickable, toggleParallel, nonCanonList,
  compareAvail, compareActive, toggleCompare,
  showStrongs, showInterlinear, setOpt, pickView, toggleStudy, chipMode, viewMode, libFontSize, changeFontSize, onClose,
  chrono, orderMode, setOrder, theme, setTheme,
}) {
  const { sheetRef, scrollRef } = useSwipeToDismiss(onClose);
  const activeNonCanon = nonCanonList.find(t => t.id === corpus) || null;
  const proseLocked = !!(activeNonCanon && activeNonCanon.englishOnly) || translation === "esv" || translation === "niv";   // English-only / ESV / NIV: no Greek toggles (BSB has its own per-word Strong's data)
  const hebMode = translation === "heb";   // Hebrew interlinear chips; "prose" flips them left-to-right
  const hebProse = hebMode && viewMode === "prose";
  const gray = proseLocked ? { opacity: 0.35, cursor: "default" } : undefined;
  // English-only "other books": Greek toggles stay locked, but line-vs-flow is allowed.
  const extraEnglish = !!(activeNonCanon && activeNonCanon.englishOnly);
  const layoutLocked = proseLocked && !extraEnglish;
  const viewChipOn   = hebMode ? !hebProse : (extraEnglish ? viewMode === "chip" : chipMode);
  // Mode three (faithful ABP interlinear) — ABP Bible only; mirrors LibraryView.
  const abpMode      = translation === "abp" && !activeNonCanon && viewMode === "interlinear";
  const ilApplicable = translation === "abp" && !activeNonCanon;
  const ilActive     = abpMode;
  const chipActive   = !abpMode && viewChipOn;
  const proseActive  = !abpMode && !viewChipOn;
  // Text picker gestures: a TAP swaps to that single Bible; a LONG-PRESS (or right-click)
  // ticks it into / out of the side-by-side compare set. One shared timer is fine (touches
  // happen one at a time); the `fired` flag stops a long-press from also firing the tap.
  const pressRef = useRef({ timer: null, fired: false });
  const pickHandlers = (id) => ({
    onClick: () => { if (pressRef.current.fired) { pressRef.current.fired = false; return; } pickBible(id); },
    onContextMenu: (e) => { e.preventDefault(); toggleCompare(id); },
    onTouchStart: () => {
      const st = pressRef.current;
      st.fired = false;
      clearTimeout(st.timer);
      st.timer = setTimeout(() => { st.fired = true; toggleCompare(id); if (navigator.vibrate) navigator.vibrate(12); }, 500);
    },
    onTouchMove: () => clearTimeout(pressRef.current.timer),
    onTouchEnd: () => clearTimeout(pressRef.current.timer),
  });
  // One read-picker button (tap = read, long-press = compare). KJV is rendered LAST in
  // the row now that BSB is the default English, so it shares this helper.
  const renderPick = (id) => {
    const on = translation !== "heb" && compareActive.includes(id);
    return (
      <button key={id} className={"mseg-b"+(on?" on":"")} aria-pressed={on} {...pickHandlers(id)}>
        {on && <span className="mseg-chk" aria-hidden="true">✓</span>}{id.toUpperCase()}
      </button>
    );
  };
  return (
    <>
      <div className="sheet-scrim" onClick={onClose} />
      <div className="msheet" ref={sheetRef}>
        <div className="sheet-drag-zone" aria-hidden="true"><div className="sheet-handle"></div></div>
        <div className="msheet-head">
          <span className="msheet-title">Reading</span>
        </div>
        <div className="msheet-body" ref={scrollRef}>
          <div className="mode-sec">
            <div className="mode-lbl">Text</div>
            {activeNonCanon ? (
              /* Reading a non-canonical text: ABP/KJV/etc just jump back to the Bible. */
              <div className="mseg text-ed">
                <button className={"mseg-b"+(corpus==="bible"&&translation==="abp"?" on":"")} onClick={()=>pickBible("abp")}>ABP</button>
                <button className={"mseg-b"+(corpus==="bible"&&translation==="kjv"?" on":"")} onClick={()=>pickBible("kjv")}>KJV</button>
                <button className={"mseg-b"+(corpus==="bible"&&translation==="bsb"?" on":"")} onClick={()=>pickBible("bsb")}>BSB</button>
                {esvOwner && <button className={"mseg-b"+(corpus==="bible"&&translation==="esv"?" on":"")} onClick={()=>pickBible("esv")}>ESV</button>}
                {nivOwner && <button className={"mseg-b"+(corpus==="bible"&&translation==="niv"?" on":"")} onClick={()=>pickBible("niv")}>NIV</button>}
              </div>
            ) : (
              /* Bible: one checkable row — tick 1 to read it, 2-4 to compare side by side.
                 compareActive + toggleCompare already do the read/compare switching. HEB
                 rides in the same row but is single-read only (no compare gesture); the
                 row wraps to a 2nd line when there are enough texts. When HEB is the read,
                 none of the compare buttons are "on" (compareActive falls back to abp). */
              <>
                <div className="mode-hint">Tap to read · long-press to compare</div>
                <div className="mseg text-ed text-pick">
                  {/* BSB is the default English now, so KJV sinks to the END of the row
                      (after BSB/HEB) — still a one-tap peer, just last. */}
                  {compareAvail.filter(id => id !== "kjv").map(renderPick)}
                  {hebShown && (
                    <button className={"mseg-b"+(translation === "heb" ? " on" : "")} aria-pressed={translation === "heb"}
                      disabled={!hebPickable} style={!hebPickable ? {opacity:0.35,cursor:"default"} : undefined}
                      aria-label="Hebrew OT interlinear"
                      onContextMenu={(e) => e.preventDefault()}
                      onClick={() => { if (hebPickable) pickBible("heb"); }}>
                      {translation === "heb" && <span className="mseg-chk" aria-hidden="true">✓</span>}HEB
                    </button>
                  )}
                  {compareAvail.includes("kjv") && renderPick("kjv")}
                </div>
              </>
            )}
          </div>
          {chrono && !activeNonCanon && (
            <div className="mode-sec">
              <div className="mode-lbl">Order</div>
              <div className="mseg">
                <button className={"mseg-b"+(orderMode!=="chronological"?" on":"")} aria-pressed={orderMode!=="chronological"} onClick={()=>setOrder("canonical")}>Canonical</button>
                <button className={"mseg-b"+(orderMode==="chronological"?" on":"")} disabled={translation==="heb"} aria-pressed={orderMode==="chronological"} style={translation==="heb"?{opacity:0.4,cursor:"default"}:undefined} onClick={()=>translation!=="heb"&&setOrder("chronological")}>Chronological</button>
              </div>
            </div>
          )}
          <div className="mode-sec">
            <div className="mode-lbl">Study layer</div>
            <div className="mseg">
              <button className={"mseg-b"+(showStrongs?" on":"")} disabled={proseLocked} style={gray} aria-pressed={showStrongs} onClick={()=>!proseLocked&&toggleStudy("showStrongs")}>Strong's</button>
              <button className={"mseg-b"+(showInterlinear?" on":"")} disabled={proseLocked} style={gray} aria-pressed={showInterlinear} onClick={()=>!proseLocked&&toggleStudy("showInterlinear")}>Interlinear</button>
            </div>
          </div>
          <div className="mode-sec">
            <div className="mode-lbl">Display</div>
            <div className="display-row">
              <div className="mseg mseg-view">
                <button className={"mseg-b"+(chipActive?" on":"")} disabled={layoutLocked} style={layoutLocked?{opacity:0.35,cursor:"default"}:undefined} title={extraEnglish?"Line-by-line view":"Chip view"} aria-label={extraEnglish?"Line-by-line view":"Chip view"} aria-pressed={chipActive} onClick={()=>!layoutLocked&&pickView("chip")}><Icon.Grid/></button>
                {ilApplicable && (
                  <button className={"mseg-b"+(ilActive?" on":"")} title="Interlinear — Greek reading line (faithful ABP)" aria-label="Faithful ABP interlinear" aria-pressed={ilActive} onClick={()=>pickView("interlinear")}><Icon.Interlinear/></button>
                )}
                <button className={"mseg-b"+(proseActive?" on":"")} title={hebMode?"Left-to-right view":"Prose view"} aria-label={hebMode?"Left-to-right view":"Prose view"} aria-pressed={proseActive} onClick={()=>pickView("prose")}><Icon.Lines/></button>
              </div>
              <div className="mseg font-picker">
                <button className="mseg-b" onClick={() => changeFontSize(-1)}>A−</button>
                <span className="font-size-lbl">{libFontSize}</span>
                <button className="mseg-b" onClick={() => changeFontSize(+1)}>A+</button>
              </div>
            </div>
          </div>
          <div className="mode-sec">
            <div className="mode-lbl">Theme</div>
            <div className="mseg">
              <button className={"mseg-b"+(theme==="light"?" on":"")} aria-pressed={theme==="light"} onClick={()=>setTheme("light")}>Light</button>
              <button className={"mseg-b"+(theme==="sepia"?" on":"")} aria-pressed={theme==="sepia"} onClick={()=>setTheme("sepia")}>Sepia</button>
              <button className={"mseg-b"+(theme==="dark"?" on":"")} aria-pressed={theme==="dark"} onClick={()=>setTheme("dark")}>Dark</button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// Non-canonical texts — reached via the "Other" pick, walled off from the Bible
// book list, search, and lexicon counts. Each rides its own backend route + tables.
// Add future early-church / apocryphal texts here.
const NONCANON = [
  // abbr = short label for the mobile toolbar pill (standard scholarly short forms).
  // group = section heading in the "Other" menus (kept in array order).
  // englishOnly: no Greek interlinear in our pipeline, so the reader stays in Prose
  // (chip / parallel-Greek views would be blank). Drop the flag once a tagged Greek
  // file is added (e.g. 1 Enoch ch 1–32 from the Akhmim papyrus).
  // Group order = nearness to the canon / era: Septuagint Apocrypha (inside the Greek
  // OT world) -> Pseudepigrapha -> Testaments -> Apostolic Fathers (early Christian).

  // Septuagint Apocrypha — Brenton's 1851 public-domain English LXX (ebible.org USFM),
  // verse-perfect. English-only; the Greek isn't Strong's-tagged so no interlinear.
  { id: "esdras1",    name: "1 Esdras",            abbr: "1Esd",  chapters: 9,  englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "tobit",      name: "Tobit",               abbr: "Tob",   chapters: 14, englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "judith",     name: "Judith",              abbr: "Jdt",   chapters: 16, englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "esther_gk",  name: "Esther (Greek)",      abbr: "EsG",   chapters: 10, englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "maccabees1", name: "1 Maccabees",         abbr: "1Mac",  chapters: 16, englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "maccabees2", name: "2 Maccabees",         abbr: "2Mac",  chapters: 15, englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "maccabees3", name: "3 Maccabees",         abbr: "3Mac",  chapters: 7,  englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "maccabees4", name: "4 Maccabees",         abbr: "4Mac",  chapters: 18, englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "wisdom",     name: "Wisdom of Solomon",   abbr: "Wis",   chapters: 19, englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "sirach",     name: "Sirach",              abbr: "Sir",   chapters: 51, englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "baruch",     name: "Baruch",              abbr: "Bar",   chapters: 5,  englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "epjeremiah", name: "Letter of Jeremiah",  abbr: "EpJer", chapters: 1,  englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "susanna",    name: "Susanna",             abbr: "Sus",   chapters: 1,  englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "bel",        name: "Bel and the Dragon",  abbr: "Bel",   chapters: 1,  englishOnly: true, group: "Septuagint Apocrypha" },
  { id: "manasseh",   name: "Prayer of Manasseh",  abbr: "PrMan", chapters: 1,  englishOnly: true, group: "Septuagint Apocrypha" },

  // Pseudepigrapha — Second Temple Jewish texts (R.H. Charles et al., public domain).
  // 2 Esdras (= 4 Ezra) is the great Jewish apocalypse; not in the Greek LXX, so it sits
  // here rather than with the Septuagint Apocrypha. WEB Apocrypha (public domain) English.
  { id: "esdras2", name: "2 Esdras (4 Ezra)", abbr: "2Esd", chapters: 16, englishOnly: true, group: "Pseudepigrapha" },
  { id: "enoch", name: "1 Enoch", abbr: "1En", chapters: 108, englishOnly: true, group: "Pseudepigrapha" },
  { id: "enoch2", name: "2 Enoch", abbr: "2En", chapters: 68, englishOnly: true, group: "Pseudepigrapha" },
  { id: "jubilees", name: "Jubilees", abbr: "Jub", chapters: 50, englishOnly: true, group: "Pseudepigrapha" },
  { id: "baruch2", name: "2 Baruch", abbr: "2Bar", chapters: 85, englishOnly: true, group: "Pseudepigrapha" },
  // 3 Baruch / Greek Apocalypse of Baruch (Charles APOT, public domain) -- 17 ch + Prologue (ch 0).
  { id: "baruch3", name: "3 Baruch", abbr: "3Bar", chapters: 17, englishOnly: true, group: "Pseudepigrapha" },
  { id: "apocabr", name: "Apocalypse of Abraham", abbr: "ApAb", chapters: 32, englishOnly: true, group: "Pseudepigrapha" },
  // chapter-level only: no freely-reachable copy is versified (see parse_assummoses.py)
  { id: "assummoses", name: "Assumption of Moses", abbr: "AsMos", chapters: 12, englishOnly: true, group: "Pseudepigrapha" },
  // Latin Vita Adae et Evae (Charles APOT, public domain) -- 51 chapters.
  { id: "adameve", name: "Life of Adam and Eve", abbr: "LAE", chapters: 51, englishOnly: true, group: "Pseudepigrapha" },
  // Psalms of Solomon (G.B. Gray, Charles APOT, public domain) -- 18 psalms.
  { id: "psolomon", name: "Psalms of Solomon", abbr: "PsSol", chapters: 18, englishOnly: true, group: "Pseudepigrapha" },
  // Letter of Aristeas (H.T. Andrews, Charles APOT, public domain) -- one letter, cited by
  // section 1-322 (loaded as a single chapter whose verses are the section numbers).
  { id: "aristeas", name: "Letter of Aristeas", abbr: "Arist", chapters: 1, englishOnly: true, group: "Pseudepigrapha" },
  // Ascension of Isaiah (R.H. Charles, public domain) -- Martyrdom (1-5) + Vision (6-11).
  { id: "ascisaiah", name: "Ascension of Isaiah", abbr: "AscIsa", chapters: 11, englishOnly: true, group: "Pseudepigrapha" },
  // Sibylline Oracles (Milton Terry, public domain) -- chapter = book, verse = line. The
  // collection numbers its books 1-8 and 11-14 (chapters 9 & 10 carry a "no such book" note).
  { id: "sibylline", name: "Sibylline Oracles", abbr: "SibOr", chapters: 14, englishOnly: true, group: "Pseudepigrapha" },

  // Testaments of the Twelve Patriarchs (R.H. Charles, APOT) -- twelve short books,
  // each cited on its own (T. Reuben 1:1 ...), so each is a separate entry.
  { id: "treuben",   name: "Testament of Reuben",   abbr: "TReu",  chapters: 7,  englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tsimeon",   name: "Testament of Simeon",   abbr: "TSim",  chapters: 9,  englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tlevi",     name: "Testament of Levi",     abbr: "TLevi", chapters: 19, englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tjudah",    name: "Testament of Judah",    abbr: "TJud",  chapters: 26, englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tissachar", name: "Testament of Issachar", abbr: "TIss",  chapters: 7,  englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tzebulun",  name: "Testament of Zebulun",  abbr: "TZeb",  chapters: 10, englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tdan",      name: "Testament of Dan",      abbr: "TDan",  chapters: 7,  englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tnaphtali", name: "Testament of Naphtali", abbr: "TNaph", chapters: 9,  englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tgad",      name: "Testament of Gad",      abbr: "TGad",  chapters: 8,  englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tasher",    name: "Testament of Asher",    abbr: "TAsh",  chapters: 8,  englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tjoseph",   name: "Testament of Joseph",   abbr: "TJos",  chapters: 20, englishOnly: true, group: "Testaments (12 Patriarchs)" },
  { id: "tbenjamin", name: "Testament of Benjamin", abbr: "TBen",  chapters: 12, englishOnly: true, group: "Testaments (12 Patriarchs)" },

  // Apostolic Fathers — Greek-tagged interlinear (Brannan/Lake Greek + Lightfoot English).
  // NOT englishOnly: these have the full Greek word-study layer like the Bible text.
  // Traditional reading order. (Polycarp ch 10-14 survive only in Latin -> English
  // shows there, no Greek chips.)
  { id: "clement1",  name: "1 Clement",                      abbr: "1Clem", chapters: 65, group: "Apostolic Fathers" },
  { id: "clement2",  name: "2 Clement",                      abbr: "2Clem", chapters: 20, group: "Apostolic Fathers" },
  { id: "ign_eph",   name: "Ignatius to the Ephesians",      abbr: "IgEph", chapters: 21, group: "Apostolic Fathers" },
  { id: "ign_mag",   name: "Ignatius to the Magnesians",     abbr: "IgMag", chapters: 15, group: "Apostolic Fathers" },
  { id: "ign_tral",  name: "Ignatius to the Trallians",      abbr: "IgTra", chapters: 13, group: "Apostolic Fathers" },
  { id: "ign_rom",   name: "Ignatius to the Romans",         abbr: "IgRom", chapters: 10, group: "Apostolic Fathers" },
  { id: "ign_phld",  name: "Ignatius to the Philadelphians", abbr: "IgPhl", chapters: 11, group: "Apostolic Fathers" },
  { id: "ign_smyrn", name: "Ignatius to the Smyrnaeans",     abbr: "IgSmy", chapters: 13, group: "Apostolic Fathers" },
  { id: "ign_pol",   name: "Ignatius to Polycarp",           abbr: "IgPol", chapters: 8,  group: "Apostolic Fathers" },
  { id: "polycarp",  name: "Polycarp to the Philippians",    abbr: "Pol",   chapters: 14, group: "Apostolic Fathers" },
  { id: "mpolycarp", name: "Martyrdom of Polycarp",          abbr: "MPol",  chapters: 22, group: "Apostolic Fathers" },
  { id: "barnabas",  name: "Epistle of Barnabas",            abbr: "Barn",  chapters: 21, group: "Apostolic Fathers" },
  { id: "didache",   name: "Didache",                        abbr: "Did",   chapters: 16, group: "Apostolic Fathers" },
  { id: "diognetus", name: "Epistle to Diognetus",           abbr: "Diog",  chapters: 12, group: "Apostolic Fathers" },
  { id: "shepherd",  name: "Shepherd of Hermas",             abbr: "Herm",  chapters: 110, group: "Apostolic Fathers" },
];

// Group NONCANON entries by their `group` label, preserving array order, for the
// section-headed "Other" menus (nav source-picker dropdown + mobile sheet).
function nonCanonGroups(list) {
  const out = [];
  let cur = null;
  for (const t of list) {
    const g = t.group || "Other";
    if (!cur || cur.group !== g) { cur = { group: g, items: [] }; out.push(cur); }
    cur.items.push(t);
  }
  return out;
}

// ============================================================
// LIBRARY VIEW
// ============================================================
// The saved library spot (lexica.lib.v1), read once. Used by the state initializers so the
// reading order / text / compare / book-chapter / corpus all restore at the FIRST paint — no
// default→saved flicker (e.g. the mobile bottom selector flashing chapter "1" before the real one).
function readLibSaved() {
  try { return JSON.parse(localStorage.getItem("lexica.lib.v1") || "null"); } catch (e) { return null; }
}
// The book list is tiny + stable (the canon), so we cache it. Reading it back at init lets the book
// NAME render on the FIRST paint instead of popping in after api.books() returns; the fetch still
// runs and refreshes the cache.
function readCachedBooks() {
  try { const c = JSON.parse(localStorage.getItem("lexica.books.v1") || "null"); return Array.isArray(c) ? c : []; } catch (e) { return []; }
}
// Same idea for the chronological list (a ~255KB static file). Caching it lets the
// chrono passage label paint on the FIRST frame after a refresh — without it, `chrono`
// is null until the fetch lands, so chronoOn is briefly false and the mobile toolbar
// flashes the canonical book/chapter before flipping to the passage label.
function readCachedChrono() {
  try { const c = JSON.parse(localStorage.getItem("lexica.chrono.v1") || "null"); return (c && Array.isArray(c.passages)) ? c : null; } catch (e) { return null; }
}
