// ============================================================
// ASK THE CORPUS — the single home for AI search.
// A question in plain language → a synthesis answer with cited Greek/Hebrew
// lemmas and the passages that carry it. Reuses /api/ai-search (login-gated)
// and CorpusResults for the verse evidence. Opened on its own ("corpus" tab)
// or handed a word from Word study ("✦ Ask AI about <word>"), which seeds the
// scope + contextual suggestions. (Phase 1 of the study/AI redesign — see
// design/README.md + memory project_ai_search_redesign.)
// ============================================================

const _AC_HIST_KEY = "lexica.corpus.history.v1";

// Broad starter questions (no word in scope).
const _AC_BROAD = [
  "Where does Scripture link blood and covenant?",
  "Compare the OT and NT view of the Sabbath",
  "What does fire symbolize across the prophets?",
  "How is the temple reimagined in the New Testament?",
];

// Contextual questions seeded from the word handed in from Word study.
function acScopeSuggestions(scope) {
  if (!scope) return _AC_BROAD;
  const w = scope.translit || scope.lemma || "this word";
  return [
    `How does ${w} differ from its synonyms?`,
    `Trace ${w} from the OT to the NT`,
    `Where is ${w} most concentrated?`,
    `When does ${w} mean one thing versus another?`,
  ];
}

// The set of Strong's strings that mark a turn's key words in its verse list
// (so the matched word lights up gold). Mirrors App.citedStrongsApp.
function _acCited(keyStrongs) {
  if (!keyStrongs || !keyStrongs.length) return null;
  const s = new Set();
  for (const p of keyStrongs) {
    const tag = p.strongs || p.strongs_base;   // p.strongs is H/G-prefixed
    if (!tag) continue;
    const bare = strongsBare(tag);
    s.add(tag); s.add(bare); s.add(`G${bare}`); s.add(`H${bare}`);
  }
  return s.size ? s : null;
}

// Resolve a book name/abbrev the AI wrote in prose ("Matthew", "Exo",
// "1 Corinthians", "1Co") to the app's book key. Built from BOOK_LABELS, so it
// accepts both the 3-letter key and the full name; spaces/case are ignored.
const _BOOK_LOOKUP = (() => {
  const m = {};
  const add = (s, key) => { if (s) m[String(s).toLowerCase().replace(/\s+/g, "")] = key; };
  for (const key in BOOK_LABELS) { add(key, key); add(BOOK_LABELS[key], key); }
  // a few abbreviations the model favours that aren't the app's key
  Object.entries({ matt: "Mat", mk: "Mar", lk: "Luk", jn: "Joh", ps: "Psa", psalm: "Psa", song: "Son", phil: "Php", rev: "Rev" })
    .forEach(([k, v]) => add(k, v));
  return m;
})();

// Make the citations the AI already wrote in its prose clickable: verse refs
// ("Exo 24:8", "Hebrews 9:12-22") jump to the reader; Strong's ("G129", "H1818")
// open Word study. No prompt/caching change — purely a render of existing text.
const _CITE_RE = /\b((?:[1-3]\s?)?[A-Za-z][A-Za-z]+)\.?\s+(\d+):(\d+)(?:[-–]\d+)?\b|\b([GH])(\d+(?:\.\d+)?)\b/g;
function AcProse({ text, onVerse, onStrongs }) {
  if (!text) return null;
  const out = []; let last = 0, m, k = 0;
  _CITE_RE.lastIndex = 0;
  while ((m = _CITE_RE.exec(text)) !== null) {
    if (m[1]) {   // verse ref
      const key = _BOOK_LOOKUP[m[1].toLowerCase().replace(/\s+/g, "")];
      if (!key) continue;   // unknown book → leave as plain text
      if (m.index > last) out.push(text.slice(last, m.index));
      out.push(<button key={k++} className="ac-ref" onClick={() => onVerse(key, +m[2], +m[3])}>{m[0]}</button>);
      last = _CITE_RE.lastIndex;
    } else if (m[4]) {   // Strong's number
      if (m.index > last) out.push(text.slice(last, m.index));
      const tag = m[4].toUpperCase() + m[5];
      out.push(<button key={k++} className="ac-instrongs" onClick={() => onStrongs(tag)}>{m[0]}</button>);
      last = _CITE_RE.lastIndex;
    }
  }
  if (last < text.length) out.push(text.slice(last));
  return <p className="ac-prose">{out}</p>;
}

// One answered (or in-flight) question.
function AcTurn({ turn, textMode, onReadInContext, onLemma, onStrongs }) {
  const [showAll, setShowAll] = useState(false);
  const cited = useMemo(() => _acCited(turn.keyStrongs), [turn.keyStrongs]);
  const primaryCount = useMemo(() => {
    if (!turn.results) return 0;
    const seen = new Set();
    for (const e of turn.results) if (e.is_primary) seen.add(e.ref);
    return seen.size || new Set(turn.results.map(e => e.ref)).size;
  }, [turn.results]);

  return (
    <div className="ac-turn">
      <div className="ac-ask"><span className="ac-ask-q">{turn.question}</span></div>

      {turn.loading ? (
        <div className="ac-answer thinking">
          <div className="ac-syn-tag"><Icon.Sparkle/> Synthesis</div>
          <div className="ac-dots"><span></span><span></span><span></span></div>
          <div className="ac-thinking-l">Reading across the canon…</div>
        </div>
      ) : turn.notice ? (
        <div className="ac-answer"><p className="ac-notice">{turn.notice}</p></div>
      ) : turn.error ? (
        <div className="ac-answer"><p className="ac-error">{turn.error}</p></div>
      ) : (
        <div className="ac-answer">
          <div className="ac-syn-tag"><Icon.Sparkle/> Synthesis</div>
          <AcProse text={turn.explanation} onVerse={onReadInContext} onStrongs={onStrongs}/>

          {turn.keyStrongs && turn.keyStrongs.length > 0 && (
            <div className="ac-lemmas">
              {turn.keyStrongs.map((l) => {
                const tag = l.strongs || l.strongs_base;   // H/G-prefixed
                const heb = /^H/i.test(tag);
                return (
                  <button key={tag} className="ac-lem" onClick={() => onLemma(l)}
                    title={"Study " + (l.translit || l.lemma) + " in Word study"}>
                    <span className={"ac-lem-gk" + (heb ? " heb" : "")} dir={heb ? "rtl" : undefined}>{l.lemma}</span>
                    {l.translit && <span className="ac-lem-tr">{l.translit}</span>}
                    <span className="ac-lem-s">{tag}</span>
                  </button>
                );
              })}
            </div>
          )}

          {turn.results && turn.results.length > 0 && (
            <div className="ac-evidence">
              <div className="ac-evidence-head">
                <span className="ac-evidence-n">{primaryCount}</span>
                <span className="ac-evidence-l">key {primaryCount === 1 ? "passage" : "passages"}</span>
                {turn.total > primaryCount && (
                  <button className="ac-seeall" onClick={() => setShowAll(v => !v)}>
                    {showAll ? "Show less" : `See all ${turn.total}`}
                  </button>
                )}
              </div>
              <CorpusResults
                allResults={turn.results}
                primaryStrongs={turn.keyStrongs}
                citedStrongs={cited}
                showAll={showAll}
                onWordClick={() => {}}
                onReadInContext={onReadInContext}
                corpusSort="curated"
                textMode={textMode}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AcComposer({ pinned, value, setValue, onSubmit, placeholder, busy }) {
  return (
    <div className={"ac-composer " + (pinned ? "pinned" : "hero")}>
      <div className="ac-field">
        <Icon.Sparkle className="ac-field-i"/>
        <input className="ac-input" value={value} onChange={e => setValue(e.target.value)}
          onKeyDown={e => e.key === "Enter" && onSubmit()} placeholder={placeholder} />
        <button className="ac-send" onClick={onSubmit} aria-label="Ask" disabled={busy}>
          {busy ? <span className="spinner"/> : <Icon.ArrowRight/>}
        </button>
      </div>
    </div>
  );
}

function AskCorpusView({ pending, onConsumed, onReadInContext, onNavigateToLexicon, isMobile }) {
  const [thread, setThread] = useState([]);
  const [draft, setDraft] = useState("");
  const [textMode, setTextMode] = useState("abp");
  const [railOpen, setRailOpen] = useState(false);
  const [scope, setScope] = useState(null);   // { strongs, lemma, translit } from a Word study handoff
  const [history, setHistory] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem(_AC_HIST_KEY) || "[]"); } catch (e) { return []; }
  });
  const threadRef = useRef(null);
  useEffect(() => { try { sessionStorage.setItem(_AC_HIST_KEY, JSON.stringify(history.slice(0, 24))); } catch (e) {} }, [history]);

  const ask = async (question) => {
    const q = (question || "").trim();
    if (!q) return;
    setDraft("");
    if (isMobile) setRailOpen(false);
    setHistory(h => [q, ...h.filter(x => x !== q)].slice(0, 24));
    const idx = thread.length;
    setThread(t => [...t, { question: q, loading: true }]);
    try {
      const data = await api.aiSearch(q);
      let turn;
      if (data.login) turn = { question: q, error: "Sign in to ask the corpus." };
      else if (data.out_of_scope) turn = { question: q, notice: data.explanation || "This tool searches the Greek & Hebrew Bible corpus — try a question about a word, theme, or passage." };
      else if (data.error) turn = { question: q, error: data.error };
      else turn = {
        question: q,
        explanation: data.explanation || "",
        keyStrongs: data.key_strongs || [],
        results: flattenAiResults(data.results || []),
        total: data.total || 0,
      };
      setThread(t => t.map((x, i) => i === idx ? turn : x));
    } catch (e) {
      setThread(t => t.map((x, i) => i === idx ? { question: q, error: "Network error: " + e.message } : x));
    }
  };

  // Handoff from Word study (scope) or a pushed question (ask) — consumed once.
  useEffect(() => {
    if (!pending) return;
    if (pending.scope) setScope(pending.scope);
    if (pending.ask) ask(pending.ask);
    onConsumed?.();
  }, [pending]);

  // Keep the latest turn in view.
  useEffect(() => {
    const c = threadRef.current; if (!c) return;
    const turns = c.querySelectorAll(".ac-turn");
    const last = turns[turns.length - 1];
    if (last) { const r = last.getBoundingClientRect(), cr = c.getBoundingClientRect(); c.scrollTop += (r.top - cr.top) - 22; }
  }, [thread.length]);

  const onLemma = (l) => { const tag = l.strongs || l.strongs_base; onNavigateToLexicon?.(tag, /^H/i.test(tag) ? "kjv" : "abp"); };
  const onStrongs = (tag) => onNavigateToLexicon?.(tag, /^H/i.test(tag) ? "kjv" : "abp");
  const started = thread.length > 0;
  const suggestions = acScopeSuggestions(scope);

  return (
    <div className={"ac" + (railOpen ? " rail-open" : "")}>
      {isMobile && railOpen && <div className="ac-rail-scrim" onClick={() => setRailOpen(false)}/>}
      <aside className={"ac-rail" + (isMobile && !railOpen ? " hidden" : "")}>
        <div className="ac-rail-top"><span className="ac-rail-eyebrow"><Icon.Clock/> Recent questions</span></div>
        {history.length === 0
          ? <div className="ac-rail-empty">Your session's questions collect here.</div>
          : <div className="ac-rail-list">{history.map((h, i) => (
              <button key={i} className="ac-rail-item" onClick={() => ask(h)}>{h}</button>
            ))}</div>}
        {history.length > 0 && <button className="ac-rail-clear" onClick={() => setHistory([])}>Clear history</button>}
      </aside>

      <main className="ac-main">
        {!started ? (
          <div className="ac-landing">
            <div className="ac-landing-in">
              <div className="ac-mark"><Icon.Sparkle/></div>
              <h1 className="ac-title">Ask the corpus</h1>
              {scope && (
                <p className="ac-scope">Asking about{" "}
                  <span className={"ac-scope-gk" + (/^H/i.test(scope.strongs) ? " heb" : "")}
                    dir={/^H/i.test(scope.strongs) ? "rtl" : undefined}>{scope.lemma}</span>
                  <span className="ac-scope-s">{scope.strongs}</span>
                </p>
              )}
              <p className="ac-lede">{scope
                ? <>Ask anything about <b>{scope.translit || scope.lemma}</b> across the whole of Scripture — its synonyms, its spread, the passages that carry it. Or ask a broader question.</>
                : "A question in plain language, answered across the whole of Scripture — with the Greek and Hebrew it turns on, and the passages that carry it."}</p>
              <AcComposer pinned={false} value={draft} setValue={setDraft} onSubmit={() => ask(draft)}
                placeholder={scope ? `Ask about ${scope.translit || scope.lemma}…` : "Ask anything across the Bible…"}/>
              <div className="ac-examples">
                {suggestions.map((ex, i) => (
                  <button key={i} className="ac-example" onClick={() => ask(ex)}><span>{ex}</span><Icon.ArrowRight/></button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="ac-thread" ref={threadRef}>
              <div className="ac-thread-col">
                {thread.map((turn, i) => (
                  <AcTurn key={i} turn={turn} textMode={textMode} onReadInContext={onReadInContext} onLemma={onLemma} onStrongs={onStrongs}/>
                ))}
              </div>
            </div>
            <AcComposer pinned={true} value={draft} setValue={setDraft} onSubmit={() => ask(draft)} placeholder="Ask a follow-up…"/>
          </>
        )}
      </main>
    </div>
  );
}
