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
function Header({ activeView, onNavChange, owner, email, name, onLogin, onAccount }) {
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
