const { useState, useEffect, useRef } = React;

// ============================================================
// ICONS
// ============================================================
const I = {
  Spark:  (p) => (<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" {...p}><path d="M12 2.4c.3 3.4 1.6 5.3 3.4 6.4 1.1.7 2.6 1 4.9 1.2-2.3.2-3.8.5-4.9 1.2-1.8 1.1-3.1 3-3.4 6.4-.3-3.4-1.6-5.3-3.4-6.4-1.1-.7-2.6-1-4.9-1.2 2.3-.2 3.8-.5 4.9-1.2C10.4 7.7 11.7 5.8 12 2.4Z"/></svg>),
  Arrow:  (p) => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 12h14M13 6l6 6-6 6"/></svg>),
  ArrowSm:(p) => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 12h14M13 6l6 6-6 6"/></svg>),
  Book:   (p) => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19"/><path d="M19 16H7.5"/></svg>),
  Clock:  (p) => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>),
  Menu:   (p) => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M4 6h16M4 12h16M4 18h16"/></svg>),
};

// ============================================================
// HEADER  (shared chrome)
// ============================================================
function Header({ onToggleRail }) {
  return (
    <header className="hdr">
      <div className="hdr-inner">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
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
          <a className="hdr-link" href="Library.html">Library</a>
          <a className="hdr-link" href="Word Study.html">Word study</a>
          <a className="hdr-link active" href="#">Ask the corpus</a>
          <a className="hdr-link" href="#">Notes</a>
          <a className="hdr-link" href="#">About</a>
        </nav>
        <div className="hdr-right">
          <button className="hdr-icon-btn pane-toggle" onClick={onToggleRail} aria-label="History"><I.Menu/></button>
          <div className="hdr-avatar">JM</div>
        </div>
      </div>
    </header>
  );
}

// ============================================================
// ANSWER PROSE — inline clickable refs + lemmas
// ============================================================
function parseAns(str) {
  const out = []; const re = /\[\[(v|l):([^\]]+)\]\]/g; let last = 0, m;
  while ((m = re.exec(str)) !== null) {
    if (m.index > last) out.push({ t: "text", v: str.slice(last, m.index) });
    out.push({ t: m[1], v: m[2] });
    last = re.lastIndex;
  }
  if (last < str.length) out.push({ t: "text", v: str.slice(last) });
  return out;
}
function Prose({ text, onVerse, onLemma }) {
  return (
    <p className="ac-prose">
      {parseAns(text).map((tk, i) => {
        if (tk.t === "text") return <span key={i}>{tk.v}</span>;
        if (tk.t === "v") {
          const v = AC_VERSES[tk.v]; if (!v) return null;
          return <button key={i} className="ac-ref" onClick={() => onVerse(tk.v)}>{v.ref}</button>;
        }
        if (tk.t === "l") {
          const l = AC_LEMMAS[tk.v];
          return <button key={i} className={"ac-inlem " + (l && l.script === "hebrew" ? "heb" : "")} onClick={() => onLemma(tk.v)}>{l ? l.gk : tk.v}</button>;
        }
        return null;
      })}
    </p>
  );
}

// ============================================================
// ONE ANSWERED TURN
// ============================================================
function Turn({ turn, onVerse, onLemma }) {
  const { question, answer, thinking } = turn;
  return (
    <div className="ac-turn">
      <div className="ac-ask"><span className="ac-ask-q">{question}</span></div>
      {thinking ? (
        <div className="ac-answer thinking">
          <div className="ac-syn-tag"><I.Spark/> Synthesis</div>
          <div className="ac-dots"><span></span><span></span><span></span></div>
          <div className="ac-thinking-l">Reading across the canon…</div>
        </div>
      ) : (
        <div className="ac-answer">
          <div className="ac-syn-tag"><I.Spark/> Synthesis</div>
          <Prose text={answer.text} onVerse={onVerse} onLemma={onLemma}/>

          {answer.cited && answer.cited.length > 0 && (
            <div className="ac-lemmas">
              {answer.cited.map((s) => {
                const l = AC_LEMMAS[s]; if (!l) return null;
                return (
                  <button key={s} className="ac-lem" onClick={() => onLemma(s)} title={"Study " + l.tr + " in Word study"}>
                    <span className={"ac-lem-gk " + (l.script === "hebrew" ? "heb" : "")}>{l.gk}</span>
                    <span className="ac-lem-tr">{l.tr}</span>
                    <span className="ac-lem-s">{s}</span>
                  </button>
                );
              })}
            </div>
          )}

          {answer.verses && answer.verses.length > 0 && (
            <div className="ac-evidence">
              {answer.verses.map((id) => {
                const v = AC_VERSES[id]; if (!v) return null;
                return (
                  <blockquote key={id} className="ac-verse">
                    <button className="ac-verse-ref" onClick={() => onVerse(id)}>{v.ref} <I.ArrowSm/></button>
                    <span className="ac-verse-text">{v.text}</span>
                  </blockquote>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================
// COMPOSER
// ============================================================
function Composer({ pinned, value, setValue, onSubmit, placeholder }) {
  return (
    <div className={"ac-composer " + (pinned ? "pinned" : "hero")}>
      <div className="ac-field">
        <I.Spark className="ac-field-i"/>
        <input className="ac-input" value={value} onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSubmit()} placeholder={placeholder} autoFocus/>
        <button className="ac-send" onClick={onSubmit} aria-label="Ask"><I.Arrow/></button>
      </div>
    </div>
  );
}

// ============================================================
// APP
// ============================================================
const HIST_KEY = "lexica-corpus-history";

function App() {
  const [thread, setThread] = useState([]);
  const [draft, setDraft] = useState("");
  const [vw, setVw] = useState(typeof window !== "undefined" ? window.innerWidth : 1400);
  const [railOpen, setRailOpen] = useState(false);
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem(HIST_KEY) || "[]"); } catch (e) { return []; }
  });
  const threadRef = useRef(null);
  const timers = useRef([]);

  // word scope carried in from a Word study link (?w=…&tr=…&gk=…)
  const scope = useRef(null);
  if (scope.current === null) {
    const p = new URLSearchParams(window.location.search);
    const w = p.get("w");
    scope.current = w ? { strongs: w, tr: p.get("tr") || "", gk: p.get("gk") || "" } : false;
  }
  const sc = scope.current || null;
  const suggestions = acScopeSuggestions(sc);

  useEffect(() => { const r = () => setVw(window.innerWidth); window.addEventListener("resize", r); return () => window.removeEventListener("resize", r); }, []);
  useEffect(() => { try { sessionStorage.setItem(HIST_KEY, JSON.stringify(history.slice(0, 24))); } catch (e) {} }, [history]);
  useEffect(() => {
    const cont = threadRef.current;
    if (!cont) return;
    const turns = cont.querySelectorAll(".ac-turn");
    const last = turns[turns.length - 1];
    if (last) {
      const r = last.getBoundingClientRect(), c = cont.getBoundingClientRect();
      cont.scrollTop += (r.top - c.top) - 22;
    }
  }, [thread.length]);

  const narrowRail = vw <= 980;

  const ask = (question) => {
    const q = (question || "").trim();
    if (!q) return;
    setDraft("");
    if (narrowRail) setRailOpen(false);
    setHistory((h) => [q, ...h.filter((x) => x !== q)].slice(0, 24));
    const idx = thread.length;
    setThread((t) => [...t, { question: q, thinking: true, answer: null }]);
    const tm = setTimeout(() => {
      setThread((t) => t.map((turn, i) => i === idx ? { ...turn, thinking: false, answer: acAnswer(q) } : turn));
    }, 700);
    timers.current.push(tm);
  };

  // links out
  const onVerse = (id) => {
    const v = AC_VERSES[id];
    window.location.href = "Library.html" + (v ? "?ref=" + encodeURIComponent(v.ref) : "");
  };
  const onLemma = (s) => { window.location.href = "Word Study.html?w=" + encodeURIComponent(s); };

  const started = thread.length > 0;

  return (
    <div className="app ac">
      <Header onToggleRail={() => setRailOpen(!railOpen)}/>
      <div className={"ac-shell" + (narrowRail ? " rail-collapsed" : "")}>

        {/* LEFT — recent questions (session history) */}
        {narrowRail && railOpen && <div className="ac-rail-scrim" onClick={() => setRailOpen(false)}></div>}
        <aside className={"ac-rail" + (narrowRail && !railOpen ? " hidden" : "")}>
          <div className="ac-rail-top">
            <span className="ac-rail-eyebrow"><I.Clock/> Recent questions</span>
          </div>
          {history.length === 0 ? (
            <div className="ac-rail-empty">Your session's questions collect here.</div>
          ) : (
            <div className="ac-rail-list">
              {history.map((h, i) => (
                <button key={i} className="ac-rail-item" onClick={() => ask(h)}>{h}</button>
              ))}
            </div>
          )}
          {history.length > 0 && (
            <button className="ac-rail-clear" onClick={() => setHistory([])}>Clear history</button>
          )}
        </aside>

        {/* CENTER — landing / thread */}
        <main className="ac-main">
          {!started ? (
            <div className="ac-landing">
              <div className="ac-landing-in">
                <div className="ac-mark"><I.Spark/></div>
                <h1 className="ac-title">Ask the corpus</h1>
                {sc ? (
                  <p className="ac-scope">Asking about <span className={"ac-scope-gk " + (/[\u0590-\u05FF]/.test(sc.gk) ? "heb" : "")}>{sc.gk}</span><span className="ac-scope-s">{sc.strongs}</span></p>
                ) : null}
                <p className="ac-lede">{sc
                  ? <>Ask anything about <span className="ac-lede-gk">{sc.gk}</span> across the whole of Scripture — its synonyms, its spread, the passages that carry it. Or ask a broader question.</>
                  : "A question in plain language, answered across the whole of Scripture — with the Greek and Hebrew it turns on, and the passages that carry it."}</p>
                <Composer pinned={false} value={draft} setValue={setDraft} onSubmit={() => ask(draft)}
                  placeholder={sc ? `Ask about ${sc.tr || sc.gk}…` : "Ask anything across the Bible…"}/>
                <div className="ac-examples">
                  {suggestions.map((ex, i) => (
                    <button key={i} className="ac-example" onClick={() => ask(ex)}>
                      <span>{ex}</span><I.ArrowSm/>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="ac-thread" ref={threadRef}>
                <div className="ac-thread-col">
                  {thread.map((turn, i) => (
                    <Turn key={i} turn={turn} onVerse={onVerse} onLemma={onLemma}/>
                  ))}
                </div>
              </div>
              <Composer pinned={true} value={draft} setValue={setDraft} onSubmit={() => ask(draft)}
                placeholder="Ask a follow-up…"/>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
