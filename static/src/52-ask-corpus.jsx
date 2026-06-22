// ============================================================
// ASK THE CORPUS — the single home for AI search.
// A question in plain language → a synthesis answer with cited Greek/Hebrew
// lemmas and the passages that carry it. Reuses /api/ai-search (login-gated)
// and CorpusResults for the verse evidence. Opened on its own ("corpus" tab)
// or handed a word from Word study ("✦ Ask AI about <word>"), which seeds the
// scope + contextual suggestions. (Phase 1 of the study/AI redesign — see
// design/README.md + memory project_ai_search_redesign.)
// ============================================================

const _AC_CONVOS_KEY = "lexica.corpus.convos.v1";
const _AC_CONVO_MAX = 15;   // keep the most recent N conversations (browser-local)

// Only the curated key passages are shown now (the old "see all 156" dump is gone),
// so keep just those in a turn — this also keeps saved conversations small. Mirrors
// CorpusResults' showAll=false render: when nothing was tagged primary it falls back
// to showing everything, so in that one case keep them all (don't drop the evidence).
function acDisplayedResults(entries) {
  if (!entries.some(e => e.is_primary)) return entries;
  return entries.filter(e => e.is_primary || e.is_additional);
}

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
function AcProse({ text, onVerse, onStrongs, verified }) {
  if (!text) return null;
  const out = []; let last = 0, m, k = 0;
  _CITE_RE.lastIndex = 0;
  while ((m = _CITE_RE.exec(text)) !== null) {
    if (m[1]) {   // verse ref
      const key = _BOOK_LOOKUP[m[1].toLowerCase().replace(/\s+/g, "")];
      if (!key) continue;   // unknown book → leave as plain text
      // SEATBELT: only vouch for (linkify) a verse the search actually surfaced.
      // If the AI named a verse we never retrieved, render it as plain text — we
      // can't verify it, so we don't link it or imply it's evidence.
      if (verified && !verified.has(`${key}-${+m[2]}-${+m[3]}`)) continue;
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
  const firstLem = turn.keyStrongs && turn.keyStrongs[0];   // anchor for the "see in Word study" link
  const cited = useMemo(() => _acCited(turn.keyStrongs), [turn.keyStrongs]);
  // Verses the search actually surfaced — the only ones the synthesis prose may
  // link. Anything the AI names outside this set renders un-linked (seatbelt).
  // `turn.verified` (full retrieved ref list) is kept separate from the displayed
  // results so trimming the verse cards never un-links a verse the answer cited.
  const verifiedRefs = useMemo(() => {
    if (turn.verified) return new Set(turn.verified);
    const s = new Set();
    for (const e of (turn.results || [])) s.add(`${e.book}-${e.chapter}-${e.verse}`);
    return s;
  }, [turn.verified, turn.results]);
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
          {turn.grounded === false && (
            <div className="ac-ungrounded" role="note">
              <b>No direct occurrences found.</b> The corpus search turned up no verse that actually
              uses this word, so the note below is general background from the AI — not verse evidence.
              Treat it with caution and verify against the text.
            </div>
          )}
          <AcProse text={turn.explanation} onVerse={onReadInContext} onStrongs={onStrongs} verified={verifiedRefs}/>

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
                {turn.total > primaryCount && firstLem && (
                  <button className="ac-seeall" onClick={() => onLemma(firstLem)}
                    title={"Browse every occurrence of " + (firstLem.translit || firstLem.lemma) + " in Word study"}>
                    {turn.total} occurrences · see in Word study
                  </button>
                )}
              </div>
              <CorpusResults
                allResults={turn.results}
                primaryStrongs={turn.keyStrongs}
                citedStrongs={cited}
                showAll={false}
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
  const [convos, setConvos] = useState(() => {
    try { return JSON.parse(localStorage.getItem(_AC_CONVOS_KEY) || "[]"); } catch (e) { return []; }
  });
  const [currentId, setCurrentId] = useState(null);   // the conversation being viewed/built (null = landing)
  const threadRef = useRef(null);
  useEffect(() => { try { localStorage.setItem(_AC_CONVOS_KEY, JSON.stringify(convos.slice(0, _AC_CONVO_MAX))); } catch (e) {} }, [convos]);

  // Save the live conversation locally so the rail can REOPEN it later with no
  // re-run. One entry per thread keyed by currentId; title = first question; most
  // recent first; last _AC_CONVO_MAX kept. Loading turns are never stored.
  useEffect(() => {
    if (currentId == null) return;
    const answered = thread.filter(t => t && t.question && !t.loading);
    if (!answered.length) return;
    setConvos(cs => {
      const entry = { id: currentId, title: answered[0].question,
                      turns: thread.filter(t => t && !t.loading), updated: Date.now() };
      return [entry, ...cs.filter(c => c.id !== currentId)].slice(0, _AC_CONVO_MAX);
    });
  }, [thread, currentId]);

  const ask = async (question) => {
    const q = (question || "").trim();
    if (!q) return;
    setDraft("");
    if (isMobile) setRailOpen(false);
    // A question from the landing (empty thread) starts a NEW conversation; a
    // follow-up keeps the current one. The auto-save effect persists it by id.
    if (thread.length === 0) setCurrentId("c" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6));
    const idx = thread.length;
    // Follow-up context: hand the recent thread (capped) to the backend so references
    // like "it" / "this word" / "the same word" resolve across the conversation —
    // each ask is otherwise standalone. Last 6 real turns, total trimmed to ~1500 chars.
    const ctxTurns = thread.filter(t => t && t.question && !t.loading && !t.error).slice(-6);
    let context = "";
    if (ctxTurns.length) {
      context = ctxTurns.map(t => {
        const lem = (t.keyStrongs || []).slice(0, 4)
          .map(k => [k.lemma, k.translit, k.strongs].filter(Boolean).join(" "))
          .filter(Boolean).join("; ");
        return `Asked: "${(t.question || "").slice(0, 160)}".` + (lem ? ` Key words: ${lem}.` : "");
      }).join("\n").slice(0, 1500);
    }
    setThread(t => [...t, { question: q, loading: true }]);
    try {
      const data = await api.aiSearch(q, context);
      let turn;
      if (data.login) turn = { question: q, error: "Sign in to ask the corpus." };
      else if (data.out_of_scope) turn = { question: q, notice: data.explanation || "This tool searches the Greek & Hebrew Bible corpus — try a question about a word, theme, or passage." };
      else if (data.error) turn = { question: q, error: data.error };
      else turn = {
        question: q,
        explanation: data.explanation || "",
        keyStrongs: data.key_strongs || [],
        results: acDisplayedResults(flattenAiResults(data.results || [])),
        verified: (data.results || []).map(v => `${v.book}-${v.chapter}-${v.verse}`),
        total: data.total || 0,
        grounded: data.grounded !== false,   // false only when the backend says so
      };
      setThread(t => t.map((x, i) => i === idx ? turn : x));
    } catch (e) {
      setThread(t => t.map((x, i) => i === idx ? { question: q, error: "Network error: " + e.message } : x));
    }
  };

  // Start a clean conversation — clears the thread (back to the landing) but keeps
  // any Word-study scope and the saved-conversations rail. The current thread is
  // already saved by the effect above, so there's nothing to flush here.
  const newThread = () => { setThread([]); setDraft(""); setCurrentId(null); if (isMobile) setRailOpen(false); };

  // Reopen a saved conversation — restores its turns verbatim. NO model calls (the
  // whole point): the answers are already in hand, so nothing re-runs.
  const openConvo = (c) => {
    setThread(c.turns || []);
    setCurrentId(c.id);
    setDraft("");
    if (isMobile) setRailOpen(false);
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
        <button className="ac-rail-new" onClick={newThread} disabled={!started}
          title="Start a new conversation">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>
          New thread
        </button>
        <div className="ac-rail-top"><span className="ac-rail-eyebrow"><Icon.Clock/> Recent conversations</span></div>
        {convos.length === 0
          ? <div className="ac-rail-empty">Your conversations are saved here — reopen one anytime.</div>
          : <div className="ac-rail-list">{convos.map((c) => (
              <button key={c.id} className={"ac-rail-item" + (c.id === currentId ? " on" : "")}
                onClick={() => openConvo(c)} title="Reopen this conversation">{c.title}</button>
            ))}</div>}
        {convos.length > 0 && <button className="ac-rail-clear" onClick={() => setConvos([])}>Clear all</button>}
      </aside>

      <main className="ac-main">
        <div className="ac-construction" role="note">
          <svg className="ac-construction-i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M10.3 3.2 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.2a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>
          </svg>
          <span><b>Under construction</b> — answers can be rough or incomplete while this tab is being tuned.</span>
        </div>
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
