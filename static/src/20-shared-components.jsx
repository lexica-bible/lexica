// ============================================================
// ZONE EMPTY — the shared inspect/rail empty-state (icon + bold title + helper line).
// The three-zone FRAME component (Shell) + the RightStack inspect stack now live in
// 22-shell.jsx; News, Word study and Library all render through it (the old ThreeZone
// was retired once all three migrated). This file keeps ZoneEmpty, which those frames
// drop into an empty slot. Widths / spacing / over-header behavior live once in the
// .zshell* / .zinspect CSS.
// ============================================================
function ZoneEmpty({ icon, title, sub }) {
  return (
    <div className="zempty">
      {icon ? <div className="zempty-mark">{icon}</div> : null}
      {title ? <div className="zempty-t">{title}</div> : null}
      {sub ? <div className="zempty-s">{sub}</div> : null}
    </div>
  );
}

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
  // Below the Shell's nav-overflow breakpoint (styles.css, 1500px) the inline nav is
  // hidden and these same links move into this hamburger menu — the row never reflows.
  const [menuOpen, setMenuOpen] = React.useState(false);
  const wrapRef = React.useRef(null);
  React.useEffect(() => {
    if (!menuOpen) return;
    const onDoc = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setMenuOpen(false); };
    const onKey = (e) => { if (e.key === "Escape") setMenuOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  }, [menuOpen]);

  const links = [
    ["library", "Library"],
    ["lexicon", "Word study"],
    ["corpus", "Ask the corpus"],
    ["notes", "Notes"],
    ...(owner ? [["study", "Study"]] : []),
    ...(showNews ? [["news", "News"]] : []),
    ["about", "About"],
  ];

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
          {links.map(([v, label]) => (
            <button key={v} className={"hdr-link " + (activeView === v ? "active" : "")} onClick={() => onNavChange(v)}>{label}</button>
          ))}
        </nav>
        <div className="hdr-right">
          <div className="hdr-burger-wrap" ref={wrapRef}>
            <button className="hdr-burger" aria-label="Menu" aria-expanded={menuOpen} onClick={() => setMenuOpen(o => !o)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/>
              </svg>
            </button>
            {menuOpen && (
              <div className="hdr-menu">
                {links.map(([v, label]) => (
                  <button key={v} className={"hdr-menu-link " + (activeView === v ? "active" : "")} onClick={() => { onNavChange(v); setMenuOpen(false); }}>{label}</button>
                ))}
              </div>
            )}
          </div>
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
        // Checkmark ONLY when every citation verified; a partial pass shows a warning glyph.
        // The build gate now blocks failed citations, so live entries should always be N == N —
        // this is the defensive belt if one ever slips through (or was gate-bypassed).
        <div className="lex-verified">{audit.pass === audit.total ? "✓" : "⚠"} {audit.pass}/{audit.total} cited verses verified</div>
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
          {lexica.alias_note && (
            <div className="lex-block">
              <span className="lex-lbl">Strong's numbering</span>
              <div className="lex-notes">
                {lexica.alias_note.direction === "to_abp"
                  ? `ABP tags this word under ${lexica.alias_note.abp}.`
                  : `Standard Strong's ${lexica.alias_note.standard.join(", ")}.`}
                {lexica.alias_note.caveat ? " " + lexica.alias_note.caveat : ""}
              </div>
            </div>
          )}
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
  // GLANCE / FULL split — the SAME view-state + .lsj-tg toggle LexicaBody uses (Meaning / Full
  // entry). "Function" is the glance: just the finding (data.function). A card splits ONLY when
  // it carries a deeper narrative layer below the finding — a use-boundary scope, the
  // contested-case flag, an underspecified note, or a sense typology (data.glance). A lone
  // cross-ref is NOT a deep layer: it does not trigger a split, so a flat card (οὐ) can carry a
  // one-line cross-ref pointer in its single view without sprouting a Full tab; on a card that
  // already splits (eimi, μή) the cross-ref rides along in Full. A preposition is just the
  // finding + a short case-row table + the straddle note, already glance-sized — no Full tab, the
  // single view shows everything (collapse-to-one). hasMore drives both the tab and each view.
  const hasMore = !!(data.scope || data.scope_contested || data.underspecified || data.glance);
  const showDetail = !hasMore || view === "full";
  return (
    <>
      <div className="lsj-tg-row">
        <button className={"lsj-tg" + (view === "fn" ? " on" : "")} onClick={() => setView("fn")}>Function</button>
        {hasMore && <button className={"lsj-tg" + (view === "full" ? " on" : "")} onClick={() => setView("full")}>Full entry</button>}
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
          {/* GLANCE boundary pointer: the finding describes the LINKING use only, but the same
             lemma also carries the existential "I am" (Exo 3:14, John 8:58). Without this line the
             glance would speak for the whole word while covering one use — the existential
             overclaim. The full scope paragraph + the 8:58 flag stay in Full; glance just points
             to the boundary. Gated on data.scope, so only a card with a use-boundary (eimi) shows
             it; prepositions never do.
             NOTE — this line is AUTHORED per card, not a template: its wording names εἰμί's "I am".
             A future deep card whose deeper layer is a sense typology rather than a separate-use
             scope (a conjunction like ὅτι / ὡς / εἰ) would point to a DIFFERENT boundary and needs
             its own gate + its own sentence — same as the verse exemplars are per-card, not
             find-replace. */}
          {!showDetail && data.scope && (
            <div className="gram-bound">This covers the linking use; the absolute “I am” (asserting existence) is a separate use — <button type="button" className="gram-bound-link" onClick={() => setView("full")}>see Full entry</button>.</div>
          )}
          {/* GLANCE pointer for a TYPOLOGY card (a conjunction like ὅτι). This differs from eimi's
             pointer above in WHERE it points. Eimi points OUT — to the existential “I am”, a
             DIFFERENT function the copula card scopes itself away from. A typology pointer points
             IN — it flags the easy-to-miss member of THIS card's own sense list (ὅτι's recitative),
             which the finding already covers. Keep that distinction: the in/out-of-scope line is
             exactly the eimi/existential line, and blurring it misframes the word. Gated on
             data.glance (typology cards); eimi has only data.scope, never glance, so the two are
             disjoint — eimi shows ONE pointer, not two. Authored per card in structural.py, ending
             just before the link. */}
          {!showDetail && data.glance && (
            <div className="gram-bound">{data.glance} <button type="button" className="gram-bound-link" onClick={() => setView("full")}>see Full entry</button>.</div>
          )}
          {showDetail && <>
            {data.scope && (
              <div className="lex-block">
                <span className="lex-lbl">Linking use only — the absolute “I am” is separate</span>
                <div className="lex-notes">{data.scope}</div>
              </div>
            )}
            {data.scope_contested && <div className="gram-xref">{data.scope_contested}</div>}
            {/* contest_graph: the doctrinal-application pointer to the Study argument graph. Shows on
               every ἵνα card but NAMES its loaded verses, so it never paints a mundane purpose-ἵνα as
               contested. Breadcrumb to Study › Graphs (not click-through yet — matches the dikaioō fork
               pointer; a shared click-through is a later upgrade for both). See structural.py G2443. */}
            {data.contest_graph && (
              <div className="gram-contest">
                <div className="gram-contest-lead">{data.contest_graph.lead}</div>
                <div className="gram-contest-at">
                  <span className="gram-contest-lbl">At:</span> {(data.contest_graph.verses || []).join(" · ")}
                </div>
                <div className="gram-contest-map">Argument map · Study › Graphs</div>
              </div>
            )}
            {data.underspecified && (
              <div className="lex-block">
                {/* Label is authored per card (data.underspecified_label) — eimi's copula finding
                   is "...the relation"; ἄν's particle finding is "...the contingency". Default
                   keeps eimi byte-identical. */}
                <span className="lex-lbl">{data.underspecified_label || "The verb doesn’t settle the relation"}</span>
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
          </>}
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
