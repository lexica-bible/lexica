// ============================================================
// useFitText — shrink a single-line element's font-size until it fits its slot.
// Used by the mobile reading-intro / overview card titles so a long title never
// wraps or runs off (and never collides with the corner toggle link) — it just
// steps the font down to fit. Pass {enabled:false} to leave the text untouched
// (e.g. on desktop, where the title sits inline and ellipsises instead).
// ============================================================
function useFitText(ref, text, opts) {
  const o = opts || {};
  const min = o.min || 13, max = o.max || 20, enabled = o.enabled !== false;
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || !enabled) return;
    const fit = () => {
      el.style.fontSize = max + "px";
      const avail = el.clientWidth;
      const full = el.scrollWidth;
      if (!avail || full <= avail) return;          // already fits at full size
      // One proportional jump gets us close (text width ~ linear in font size),
      // then nudge down in half-pixels until it clears.
      let size = Math.max(min, Math.floor((max * avail / full) * 2) / 2);
      el.style.fontSize = size + "px";
      while (size > min && el.scrollWidth > avail + 0.5) { size -= 0.5; el.style.fontSize = size + "px"; }
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, [text, enabled, min, max]);
}

// ============================================================
// HEADER
// ============================================================
function Header({ activeView, onNavChange, owner, showNews, email, name, onLogin, onAccount }) {
  return (
    <header className="hdr">
      <div className="hdr-inner">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M11 7v6M14 10h-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="brand-text">
            <div className="brand-name">Lexica</div>
            <div className="brand-sub">Greek &amp; Hebrew Word Study</div>
          </div>
        </div>
        <nav className="hdr-nav">
          <button className={"hdr-link " + (activeView === "library" ? "active" : "")} onClick={() => onNavChange("library")}>Library</button>
          <button className={"hdr-link " + (activeView === "lexicon" ? "active" : "")} onClick={() => onNavChange("lexicon")}>Word study</button>
          <button className={"hdr-link " + (activeView === "corpus" ? "active" : "")} onClick={() => onNavChange("corpus")}>Ask the corpus</button>
          <button className={"hdr-link " + (activeView === "notes" ? "active" : "")} onClick={() => onNavChange("notes")}>Notes</button>
          <button className={"hdr-link " + (activeView === "study" ? "active" : "")} onClick={() => onNavChange("study")}>Study</button>
          {showNews && <button className={"hdr-link " + (activeView === "news" ? "active" : "")} onClick={() => onNavChange("news")}>News</button>}
          <button className={"hdr-link " + (activeView === "about" ? "active" : "")} onClick={() => onNavChange("about")}>About</button>
        </nav>
        <div className="hdr-right">
          {email
            ? <button className="hdr-acct" onClick={onAccount} title="Your account">{name || email}</button>
            : <button className="hdr-login" onClick={onLogin}>Log in</button>}
        </div>
      </div>
    </header>
  );
}

// ============================================================
// LSJ SUMMARY DISPLAY
// ============================================================
function LsjSummary({ data, loading }) {
  if (loading)
    return <div className="lsj-def" style={{ color: "var(--muted)", fontStyle: "italic" }}>Summarizing…</div>;
  if (!data?.summary)
    return <div className="lsj-def" style={{ color: "var(--muted)" }}>No definition available.</div>;
  return <p className="lsj-synthesis">{renderInlineMd(data.summary)}</p>;
}

// The LSJ card body: the AI sense-summary by default, with an underline toggle to show
// the FULL raw dictionary entry (lsjEntry.def_html — already fetched). Shared by the
// Library word card (30-detail-panel) and the Word study tab (80-lexicon) so the two
// can't drift. A Strong's-fallback entry has no synthesis — it's raw text, no toggle.
function LsjBody({ lsjEntry, lsjSummary, summaryLoading }) {
  const [showFull, setShowFull] = React.useState(false);
  React.useEffect(() => { setShowFull(false); }, [lsjEntry && lsjEntry.key]);
  if (!lsjEntry) return null;
  if (lsjEntry.source === "strongs")
    return <div className="lsj-def" dangerouslySetInnerHTML={{ __html: lsjEntry.def_html }} />;
  const hasFull = !!lsjEntry.def_html;
  const summaryEmpty = !summaryLoading && !(lsjSummary && lsjSummary.summary);
  // Summary view = the AI synthesis, falling back to the raw entry when the synthesis is
  // empty (the old word-study behavior). The toggle forces the full entry either way.
  const body = ((showFull || summaryEmpty) && hasFull)
    ? <div className="lsj-def" dangerouslySetInnerHTML={{ __html: lsjEntry.def_html }} />
    : <LsjSummary data={lsjSummary} loading={summaryLoading} />;
  return (
    <>
      {hasFull && (
        <div className="lsj-tg-row">
          <button className={"lsj-tg" + (!showFull ? " on" : "")} onClick={() => setShowFull(false)}>Summary</button>
          <button className={"lsj-tg" + (showFull ? " on" : "")} onClick={() => setShowFull(true)}>Full entry</button>
        </div>
      )}
      {body}
    </>
  );
}

// ============================================================
// LEXICA DICTIONARY CARD (verse-grounded definition)
// ============================================================
// Renders ONLY when a word has a Lexica entry (admin-only during rollout); every other word keeps
// the LsjBody path above untouched. Three depths via the shared toggle: Meaning (the glance) ·
// Full entry · LSJ (raw classical entry, display-only). The contested-word fork shows in BOTH
// Meaning and Full — it never folds away. All visuals use dedicated .lex-* classes so nothing
// leaks into the locked LSJ / Library word card.
function LexicaFork({ fork }) {
  if (!fork) return null;
  return (
    <div className="lex-fork">
      <div className="lex-fork-head">Contested — the meaning above doesn't settle this</div>
      {fork.core && <div className="lex-fork-core"><span className="lex-fork-corelbl">Core (all agree):</span> {fork.core}</div>}
      <div className="lex-fork-frames">
        {(fork.frames || []).map((f, i) => (
          <div key={i} className="lex-fork-frame">
            <span className="lex-fork-label">{f.label}</span>
            {f.tradition && f.tradition !== "—" && <span className="lex-fork-trad"> · {f.tradition}</span>}
            {f.gloss && <span className="lex-fork-gloss"> — {f.gloss}</span>}
          </div>
        ))}
      </div>
      {fork.note && <div className="lex-fork-note">{fork.note}</div>}
      {fork.graph_ref && <div className="lex-fork-map">Full argument map · Study › Graphs</div>}
    </div>
  );
}

function LexicaVerses({ verses }) {
  if (!verses || !verses.length) return null;
  return (
    <div className="lex-verses">
      {verses.map((v, i) => (
        <div key={i} className="lex-verse"><span className="lex-vref">{v.ref}</span> {v.text}</div>
      ))}
    </div>
  );
}

// Frame-leakers (dikaioō / charis / aionios) carry a hand-pinned neutral core: the model's own
// senses pre-pick a contested frame draw to draw, so the settled core leads the card and those
// senses drop below it as "Attested uses". Present only when build_lexica_def pinned it; every
// other word has no pinned_core and its senses lead as usual.
function LexicaPinnedCore({ core }) {
  if (!core) return null;
  return (
    <>
      <div className="lex-core">{core}</div>
      <div className="lex-uses-lbl">Attested uses</div>
    </>
  );
}

function LexicaBody({ lexica, lsjEntry }) {
  const [view, setView] = React.useState("meaning");
  React.useEffect(() => { setView("meaning"); }, [lexica && lexica.strongs]);
  if (!lexica) return null;
  const audit = lexica.audit || {};
  const fork = lexica.fork;
  const hasLsj = !!(lsjEntry && lsjEntry.def_html);
  const glanceVerses = (lexica.verses || []).slice(0, 2);
  // Per-sense LXX provenance (Option B). prov[i].lxx marks a sense resting heavily on Greek-OT
  // (Septuagint) citations; provSenses is the 1-based list for the full-view summary block.
  const prov = lexica.sense_prov || [];
  const provSenses = prov.map((p, i) => (p && p.lxx ? i + 1 : 0)).filter(Boolean);
  return (
    <>
      {audit.total ? (
        <div className="lex-verified">{"✓"} {audit.pass}/{audit.total} cited verses verified</div>
      ) : null}
      <div className="lsj-tg-row">
        <button className={"lsj-tg" + (view === "meaning" ? " on" : "")} onClick={() => setView("meaning")}>Meaning</button>
        <button className={"lsj-tg" + (view === "full" ? " on" : "")} onClick={() => setView("full")}>Full entry</button>
        {hasLsj && <button className={"lsj-tg" + (view === "lsj" ? " on" : "")} onClick={() => setView("lsj")}>LSJ</button>}
      </div>
      {view === "lsj" && hasLsj ? (
        <div className="lsj-def" dangerouslySetInnerHTML={{ __html: lsjEntry.def_html }} />
      ) : view === "full" ? (
        <div className="lex-full">
          <LexicaPinnedCore core={lexica.pinned_core} />
          <div className="lex-prose">{renderInlineMd(lexica.senses_block || "")}</div>
          {provSenses.length > 0 && (
            <div className="lex-block">
              <span className="lex-lbl">Septuagint provenance</span>
              <div className="lex-notes">
                {provSenses.length > 1 ? "Senses " : "Sense "}{provSenses.join(", ")}
                {provSenses.length > 1 ? " rest" : " rests"} largely on Septuagint (Greek-OT)
                usage — their citations are mostly Old Testament, where the Greek renders Hebrew.
              </div>
            </div>
          )}
          {fork && <LexicaFork fork={fork} />}
          {lexica.range && <div className="lex-block"><span className="lex-lbl">Range</span> {lexica.range}</div>}
          {lexica.gloss_notes && <div className="lex-block"><span className="lex-lbl">Gloss notes</span><div className="lex-prose lex-notes">{renderInlineMd(lexica.gloss_notes)}</div></div>}
          {lexica.coverage && <div className="lex-block"><span className="lex-lbl">Coverage</span> {lexica.coverage}</div>}
          <LexicaVerses verses={lexica.verses} />
        </div>
      ) : (
        <div className="lex-glance">
          <LexicaPinnedCore core={lexica.pinned_core} />
          <ol className="lex-senses">
            {(lexica.sense_headlines || []).map((h, i) => (
              <li key={i}>
                {h}
                {prov[i] && prov[i].lxx && (
                  <span className="lex-prov">rests on Septuagint (Greek-OT) usage</span>
                )}
              </li>
            ))}
          </ol>
          {fork && <LexicaFork fork={fork} />}
          <LexicaVerses verses={glanceVerses} />
        </div>
      )}
    </>
  );
}

// ============================================================
// STRUCTURAL / FUNCTION-WORD CARD (grammatical function, not a sense list)
// ============================================================
// For words whose meaning resolves OUTSIDE the lexeme — the copula εἰμί first. Verse-grounding
// would mislocate the context's meaning onto the verb; instead this states the verb's FUNCTION,
// flags that it's underspecified, and shows the construction TYPES it appears in (patterns, not
// senses). The entry is written once on the lemma; a clicked conjugate inherits it and shows its
// own parse (data.form). Reuses .lex-block/.lex-lbl/.lex-verse so it can't drift; the
// function-card-only bits are .gram-*. Provenance = GRAMMAR (a grammatical claim, not an attested
// sense — see structural.py).
function StructuralBody({ data, lsjEntry }) {
  const [view, setView] = React.useState("fn");
  React.useEffect(() => { setView("fn"); }, [data && data.strongs]);
  if (!data) return null;
  const hasLsj = !!(lsjEntry && lsjEntry.def_html);
  const form = data.form;
  return (
    <>
      <div className="lsj-tg-row">
        <button className={"lsj-tg" + (view === "fn" ? " on" : "")} onClick={() => setView("fn")}>Function</button>
        {hasLsj && <button className={"lsj-tg" + (view === "lsj" ? " on" : "")} onClick={() => setView("lsj")}>LSJ</button>}
      </div>
      {view === "lsj" && hasLsj ? (
        <div className="lsj-def" dangerouslySetInnerHTML={{ __html: lsjEntry.def_html }} />
      ) : (
        <div className="gram">
          {form && form.parse && (
            <div className="gram-form">This form: <b>{form.parse}</b>{form.gloss ? " — “" + form.gloss + "”" : ""}</div>
          )}
          {data.function && <div className="gram-fn">{data.function}</div>}
          {data.scope && (
            <div className="lex-block">
              <span className="lex-lbl">Linking use only — the absolute “I am” is separate</span>
              <div className="lex-notes">{data.scope}</div>
            </div>
          )}
          {data.scope_contested && <div className="gram-xref">{data.scope_contested}</div>}
          {data.underspecified && (
            <div className="lex-block">
              <span className="lex-lbl">The verb doesn’t settle the relation</span>
              <div className="lex-notes">{data.underspecified}</div>
            </div>
          )}
          {(data.relations || []).length > 0 && (
            <div className="lex-block">
              <span className="lex-lbl">{data.relation_label || "What the predicate supplies — relation, not sense"}</span>
              {data.relation_lead && <div className="lex-notes gram-rlead">{data.relation_lead}</div>}
              <ul className="gram-clist">
                {data.relations.map((c, i) => (
                  <li key={i} className="gram-citem">
                    <div><span className="gram-ctype">{c.type}</span>{c.note ? <span className="gram-cnote"> — {c.note}</span> : null}</div>
                    {c.ref && <div className="lex-verse"><span className="lex-vref">{c.ref}</span> {c.text}</div>}
                  </li>
                ))}
              </ul>
              {data.relation_tail && <div className="lex-notes gram-rtail">{data.relation_tail}</div>}
            </div>
          )}
          {data.crossref && data.crossref.note && <div className="gram-xref">{data.crossref.note}</div>}
          {data.straddle && <div className="gram-straddle">{data.straddle}</div>}
          {data.provenance && <div className="gram-prov">{data.provenance}</div>}
        </div>
      )}
    </>
  );
}

// Google-Maps-style bottom-sheet dismissal: drag the WHOLE card down to close.
// Grabbing the card's top chrome (the handle/header — anything outside the
// scrolling body) ALWAYS arms the drag, no matter where the body is scrolled.
// Starting inside the body only arms when it's already scrolled to the top
// (otherwise the body scrolls normally). Uses native non-passive listeners so we
// can block page scroll / pull-to-refresh while dragging (React's touch props
// are passive and can't).
function useSwipeToDismiss(onClose) {
  const sheetRef = React.useRef(null);
  const scrollRef = React.useRef(null);
  const closeRef = React.useRef(onClose);
  closeRef.current = onClose;

  React.useEffect(() => {
    const el = sheetRef.current;
    if (!el) return;
    let startY = 0, dragY = 0, active = false, fromChrome = false;
    const SNAP = 'transform 0.25s cubic-bezier(0.2,0.8,0.2,1)';

    const atTop = () => { const sc = scrollRef.current; return !sc || sc.scrollTop <= 0; };
    const onStart = (e) => {
      const sc = scrollRef.current;
      fromChrome = !(sc && sc.contains(e.target));  // touch began on the handle/header, not the scroll body
      active = fromChrome || atTop();               // chrome always arms; body only when scrolled to top
      startY = e.touches[0].clientY;
      dragY = 0;
    };
    const onMove = (e) => {
      if (!active) return;
      const d = e.touches[0].clientY - startY;
      if (d <= 0 || (!fromChrome && !atTop())) {  // pulling up, or body-drag that got scrolled → hand back
        if (dragY) { el.style.transition = ''; el.style.transform = ''; dragY = 0; }
        active = false;
        return;
      }
      dragY = d;
      el.style.transition = 'none';
      el.style.transform = `translateY(${d}px)`;
      if (e.cancelable) e.preventDefault();   // stop the page scrolling / pull-to-refresh
    };
    const onEnd = () => {
      if (!active) return;
      active = false;
      if (dragY > 90) {                     // committed: slide the card fully down, THEN dismiss
        el.style.transition = SNAP;
        el.style.transform = 'translateY(100%)';
        let done = false;
        const finish = () => {
          if (done) return; done = true;
          el.removeEventListener('transitionend', finish);
          closeRef.current?.();
        };
        el.addEventListener('transitionend', finish);
        setTimeout(finish, 320);            // fallback if transitionend doesn't fire
        dragY = 0;
        return;
      }
      if (dragY) { el.style.transition = SNAP; el.style.transform = ''; }   // not far enough: snap back up
      dragY = 0;
    };

    el.addEventListener('touchstart', onStart, { passive: true });
    el.addEventListener('touchmove', onMove, { passive: false });
    el.addEventListener('touchend', onEnd, { passive: true });
    el.addEventListener('touchcancel', onEnd, { passive: true });
    return () => {
      el.removeEventListener('touchstart', onStart);
      el.removeEventListener('touchmove', onMove);
      el.removeEventListener('touchend', onEnd);
      el.removeEventListener('touchcancel', onEnd);
    };
  }, []);

  return { sheetRef, scrollRef };
}

// ============================================================
// LEAFLET MINI-MAP
// ============================================================
// Leaflet (CSS+JS) is loaded ON DEMAND — the map only ever appears inside the
// metaV place card, so keeping it out of index.html keeps it off the critical
// path for every page load. Loaded once, cached on window.L for later opens.
let _leafletPromise = null;
function loadLeaflet() {
  if (window.L) return Promise.resolve(window.L);
  if (_leafletPromise) return _leafletPromise;
  _leafletPromise = new Promise((resolve, reject) => {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    css.crossOrigin = "";
    document.head.appendChild(css);
    const js = document.createElement("script");
    js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    js.crossOrigin = "";
    js.onload = () => resolve(window.L);
    js.onerror = reject;
    document.head.appendChild(js);
  });
  return _leafletPromise;
}

function LeafletMap({ lat, lon, name }) {
  const mapRef = React.useRef(null);
  const instanceRef = React.useRef(null);
  const [ready, setReady] = React.useState(!!window.L);

  // Kick off the lazy load on first mount (no-op if Leaflet is already present).
  React.useEffect(() => {
    if (window.L) return;
    let cancelled = false;
    loadLeaflet().then(() => { if (!cancelled) setReady(true); }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  React.useEffect(() => {
    if (!ready || !mapRef.current || !window.L) return;
    if (instanceRef.current) {
      instanceRef.current.remove();
      instanceRef.current = null;
    }
    const map = window.L.map(mapRef.current, {
      center: [lat, lon],
      zoom: 7,
      zoomControl: true,
      scrollWheelZoom: false,
      attributionControl: false,
    });
    window.L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
    }).addTo(map);
    window.L.marker([lat, lon]).addTo(map).bindPopup(name).openPopup();
    instanceRef.current = map;
    return () => { if (instanceRef.current) { instanceRef.current.remove(); instanceRef.current = null; } };
  }, [ready, lat, lon, name]);

  return <div ref={mapRef} className="metav-leaflet-map" />;
}
