// ============================================================
// ASK THE CORPUS — the single home for AI search.
// A question in plain language → a synthesis answer with cited Greek/Hebrew
// lemmas and the passages that carry it. Reuses /api/ai-search (login-gated)
// and CorpusResults for the verse evidence. Opened on its own ("corpus" tab)
// or handed a word from Word study ("✦ Ask AI about <word>"), which seeds the
// scope + contextual suggestions. (Phase 1 of the study/AI redesign — see
// design/README.md + memory project_ai_search_redesign.)
// ============================================================

// Saved conversations live in NotesStore (browser-local for everyone; synced across
// devices when signed in) — see corpusConvos()/upsertConvo()/clearConvos() there.

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
  // Linkify one paragraph: turn the refs / Strong's the AI wrote into clickable chips.
  // A verse the search actually surfaced gets the solid evidence chip; a verse the AI
  // named that we never retrieved still jumps, but in a quieter style (the seatbelt) so
  // it doesn't imply it's part of the evidence.
  const linkify = (block, pi) => {
    const out = []; let last = 0, m, k = 0;
    _CITE_RE.lastIndex = 0;
    while ((m = _CITE_RE.exec(block)) !== null) {
      if (m[1]) {   // verse ref
        const key = _BOOK_LOOKUP[m[1].toLowerCase().replace(/\s+/g, "")];
        if (!key) continue;   // unknown book → leave as plain text
        const ok = !verified || verified.has(`${key}-${+m[2]}-${+m[3]}`);
        if (m.index > last) out.push(block.slice(last, m.index));
        out.push(<button key={"r" + pi + "-" + k++} className={"ac-ref" + (ok ? "" : " ac-ref-soft")}
          onClick={() => onVerse(key, +m[2], +m[3])}>{m[0]}</button>);
        last = _CITE_RE.lastIndex;
      } else if (m[4]) {   // Strong's number
        if (m.index > last) out.push(block.slice(last, m.index));
        const tag = m[4].toUpperCase() + m[5];
        out.push(<button key={"s" + pi + "-" + k++} className="ac-instrongs" onClick={() => onStrongs(tag)}>{m[0]}</button>);
        last = _CITE_RE.lastIndex;
      }
    }
    if (last < block.length) out.push(block.slice(last));
    return out;
  };
  // Pass-2 breaks the synthesis into paragraphs at sense shifts (blank lines); render
  // one <p> per paragraph so the prose breathes. A single-sense note is one paragraph —
  // visually identical to before.
  const paras = String(text).split(/\n\s*\n/).map(s => s.trim()).filter(Boolean);
  return <div className="ac-prose">{paras.map((p, pi) => <p key={pi}>{linkify(p, pi)}</p>)}</div>;
}

// COMPUTED lexical-texture panel — sits ABOVE the AI note (not under the "Synthesis"
// tag: it is fact, not generated prose). Per word-family: the head word + its
// gloss-confirmed relatives, each with its full corpus occurrence count and a bar.
// Bars scale WITHIN a group's own language (the OT dwarfs the NT). Borderline words
// (spelling matches, meaning unconfirmed) are never listed to the reader — only
// counted, and that line shows only when there are any. The backend (corpus_panel.py)
// already decided membership + never manufactures structure; this only draws it.
function CorpusPanel({ panel, onStrongs }) {
  const [open, setOpen] = useState({});
  if (!panel || !panel.groups || !panel.groups.length) return null;
  const fmt = (n) => (n != null ? n.toLocaleString() : "");
  return (
    <div className="cpanel" role="note" aria-label="How often these words occur">
      <div className="cpanel-tag">How often these words occur</div>
      {panel.groups.map((g, gi) => {
        const fam = g.family || [];
        if (!fam.length) return null;
        const core = fam[0], rest = fam.slice(1);
        const expanded = !!open[gi];
        const heb = g.lang === "H";
        const aside = g.set_aside || 0;
        const hasMore = rest.length > 0 || aside > 0;
        const barW = (n) => Math.max(4, Math.round((100 * n) / (g.max || n || 1)));
        // Each row jumps to Word study (replaces the old lemma chips below the note).
        const row = (r, isCore) => (
          <button className={"cpanel-row" + (isCore ? " core" : "")} key={r.strongs}
            onClick={() => onStrongs && onStrongs(r.strongs)}
            title={"Study " + (r.translit || r.lemma) + " in Word study"}>
            <span className="cpanel-word">
              <span className={"cpanel-lemma" + (heb ? " heb" : "")} dir={heb ? "rtl" : undefined}>{r.lemma}</span>
              {r.translit && <span className="cpanel-tr">{r.translit}</span>}
            </span>
            <span className="cpanel-gloss">{r.gloss || "—"}</span>
            <span className="cpanel-bar"><span style={{ width: barW(r.count) + "%" }}/></span>
            <span className="cpanel-n">{fmt(r.count)}</span>
          </button>
        );
        // Don't repeat the language header on a second same-language group (e.g. two
        // Greek heads on "kingdom of God") — the dashed divider already separates them.
        const showLabel = gi === 0 || panel.groups[gi - 1].lang !== g.lang;
        return (
          <div className="cpanel-grp" key={gi}>
            {showLabel && <div className="cpanel-grp-h">{g.label}</div>}
            {row(core, true)}
            {expanded && rest.map((r) => row(r, false))}
            {expanded && aside > 0 && (
              <div className="cpanel-aside">
                {aside} related form{aside > 1 ? "s" : ""} set aside — spelling matches, meaning unconfirmed
              </div>
            )}
            {hasMore && (
              <button className="cpanel-more" onClick={() => setOpen((o) => ({ ...o, [gi]: !expanded }))}>
                {expanded ? "Show less ▴" : (rest.length > 0 ? `+${rest.length} more ▾` : "Show note ▾")}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

// One answered (or in-flight) question.
function AcTurn({ turn, onReadInContext, onLemma, onStrongs }) {
  const cited = useMemo(() => _acCited(turn.keyStrongs), [turn.keyStrongs]);
  // Display-text toggle (ABP · BSB · KJV · HEB) for THIS answer's verse evidence. The
  // evidence is found by Strong's number, but the text shown can be the ABP (Greek
  // LXX), the BSB or KJV in English, or the real Hebrew OT (heb.db). It always
  // defaults to ABP (the corpus anchor); the reader flips it manually. heb.db is
  // OT-only, so HEB is offered only when the answer actually cites OT verses, and in
  // HEB mode the verse list is trimmed to those OT verses (a mixed Greek+Hebrew
  // answer would otherwise show blank rows for its NT/Greek verses).
  const hasOtVerse = useMemo(() =>
    (turn.results || []).some(e => !NT_BOOKS.has(e.book)),
    [turn.results]);
  const [manualMode, setManualMode] = useState(null);   // null = default (ABP)
  const textMode = manualMode || "abp";
  // HEB shows only OT verses (heb.db is OT-only) so the list never has blank rows.
  const displayResults = useMemo(() => {
    if (textMode !== "heb") return turn.results || [];
    return (turn.results || []).filter(e => !NT_BOOKS.has(e.book));
  }, [textMode, turn.results]);
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
    if (!displayResults.length) return 0;
    const seen = new Set();
    for (const e of displayResults) if (e.is_primary) seen.add(e.ref);
    return seen.size || new Set(displayResults.map(e => e.ref)).size;
  }, [displayResults]);

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
        <div className="ac-answer">
          <p className="ac-notice">{turn.notice}</p>
          {turn.capped && (
            <a className="ac-upsell" href="https://ko-fi.com/lexica" target="_blank" rel="noopener noreferrer">
              Become a Berean — more searches a day + ESV &amp; NIV. Subscribe on Ko-fi ↗
            </a>
          )}
        </div>
      ) : turn.error ? (
        <div className="ac-answer"><p className="ac-error">{turn.error}</p></div>
      ) : (
        <div className="ac-answer">
          <CorpusPanel panel={turn.panel} onStrongs={onStrongs}/>
          <div className="ac-syn-tag"><Icon.Sparkle/> Synthesis</div>
          {turn.grounded === false && (
            <div className="ac-ungrounded" role="note">
              <b>No direct occurrences found.</b> The corpus search turned up no verse that actually
              uses this word, so the note below is general background from the AI — not verse evidence.
              Treat it with caution and verify against the text.
            </div>
          )}
          <AcProse text={turn.explanation} onVerse={onReadInContext} onStrongs={onStrongs} verified={verifiedRefs}/>

          {turn.results && turn.results.length > 0 && (
            <div className="ac-evidence">
              <div className="ac-evidence-head">
                <span className="ac-evidence-n">{primaryCount}</span>
                <span className="ac-evidence-l">key {primaryCount === 1 ? "passage" : "passages"}</span>
                <div className="ac-tm" role="group" aria-label="Display text">
                  <button className={"ac-tm-b" + (textMode === "abp" ? " on" : "")}
                    onClick={() => setManualMode("abp")} title="Show the ABP (Greek)">ABP</button>
                  <button className={"ac-tm-b" + (textMode === "bsb" ? " on" : "")}
                    onClick={() => setManualMode("bsb")} title="Show the BSB (modern English)">BSB</button>
                  <button className={"ac-tm-b" + (textMode === "kjv" ? " on" : "")}
                    onClick={() => setManualMode("kjv")} title="Show the KJV">KJV</button>
                  <button className={"ac-tm-b" + (textMode === "heb" ? " on" : "")}
                    onClick={() => setManualMode("heb")} disabled={!hasOtVerse}
                    title={hasOtVerse ? "Show the Hebrew OT (Old Testament verses only)" : "No Old Testament verses in this answer"}>HEB</button>
                </div>
              </div>
              <CorpusResults
                allResults={displayResults}
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

// Follow-up questions allowed after the opening one, per conversation (cost control).
const AC_MAX_FOLLOWUPS = 3;

function AcComposer({ pinned, value, setValue, onSubmit, placeholder, busy, quota }) {
  const go = () => { if (!busy) onSubmit(); };
  const left = quota && !quota.unlimited ? quota.remaining : null;
  return (
    <div className={"ac-composer " + (pinned ? "pinned" : "hero")}>
      <div className="ac-field">
        <Icon.Sparkle className="ac-field-i"/>
        <input className="ac-input" value={value} onChange={e => setValue(e.target.value)}
          onKeyDown={e => e.key === "Enter" && go()} placeholder={placeholder} />
        <button className="ac-send" onClick={go} aria-label="Ask" disabled={busy}>
          {busy ? <span className="spinner"/> : <Icon.ArrowRight/>}
        </button>
      </div>
      {left != null && (
        <div className="ac-quota">{left > 0
          ? `${left} of ${quota.limit} question${quota.limit === 1 ? "" : "s"} left today`
          : <>Out of searches today — resets tomorrow. <a className="ac-quota-link" href="https://ko-fi.com/lexica" target="_blank" rel="noopener noreferrer">Become a Berean on Ko-fi ↗</a></>}</div>
      )}
    </div>
  );
}

function AskCorpusView({ pending, onConsumed, onReadInContext, onNavigateToLexicon, isMobile }) {
  const [thread, setThread] = useState([]);
  const [draft, setDraft] = useState("");
  const [railOpen, setRailOpen] = useState(false);
  const [scope, setScope] = useState(null);   // { strongs, lemma, translit } from a Word study handoff
  const [currentId, setCurrentId] = useState(null);   // the conversation being viewed/built (null = landing)
  const [quota, setQuota] = useState(null);   // {used, limit, remaining} | {unlimited} — daily AI cap, from the server
  const threadRef = useRef(null);
  useNotesVersion();   // re-render when the store changes (e.g. a cross-device sync pulls convos in)
  const convos = NotesStore.corpusConvos();
  const busy = thread.some(t => t && t.loading);   // a search is in flight — lock the composer

  // Seed the "questions left today" counter on mount (signed-in only; ignored otherwise).
  useEffect(() => {
    let live = true;
    fetch("/api/auth/me", { headers: _authHeaders() })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (live && d && d.ai_quota) setQuota(d.ai_quota); })
      .catch(() => {});
    return () => { live = false; };
  }, []);

  // Save the live conversation to the store so the rail can REOPEN it later with no
  // re-run. The store keeps it browser-local AND (when signed in) syncs it across
  // devices. One entry per thread keyed by currentId; loading turns are never stored.
  useEffect(() => {
    if (currentId == null) return;
    const answered = thread.filter(t => t && t.question && !t.loading);
    if (!answered.length) return;
    NotesStore.upsertConvo({ id: currentId, title: answered[0].question,
                             turns: thread.filter(t => t && !t.loading) });
  }, [thread, currentId]);

  const ask = async (question) => {
    const q = (question || "").trim();
    if (!q || busy) return;                       // ignore empty, and don't double-fire
    const isFollow = thread.length > 0;
    const norm = s => (s || "").trim().toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").replace(/\s+/g, " ").trim();
    // No repeat questions inside a conversation — don't pay to re-ask the same thing.
    if (isFollow && thread.some(t => t && t.question && !t.local && norm(t.question) === norm(q))) {
      setThread(t => [...t, { question: q, local: true,
        notice: "You already asked that in this conversation — scroll up for the answer." }]);
      setDraft("");
      return;
    }
    // Follow-up cap: the opening question + up to AC_MAX_FOLLOWUPS follow-ups per thread.
    const asked = thread.filter(t => t && t.question && !t.local).length;
    if (isFollow && asked > AC_MAX_FOLLOWUPS) {
      setThread(t => [...t, { question: q, local: true,
        notice: "Follow-up limit reached for this conversation — start a new thread to keep going." }]);
      setDraft("");
      return;
    }
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
      if (data.quota) setQuota(data.quota);       // refresh the "left today" counter
      let turn;
      if (data.login) turn = { question: q, error: "Sign in to ask the corpus." };
      else if (data.capped) turn = { question: q, notice: data.error, capped: true };
      else if (data.global_capped) turn = { question: q, notice: data.error };
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
        panel: data.panel || null,           // computed lexical-texture panel (may be absent)
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

  const onLemma = (l) => { const tag = l.strongs || l.strongs_base; onNavigateToLexicon?.(tag, /^H/i.test(tag) ? "heb" : "abp"); };
  const onStrongs = (tag) => onNavigateToLexicon?.(tag, /^H/i.test(tag) ? "heb" : "abp");
  const started = thread.length > 0;
  const followCapped = thread.filter(t => t && t.question && !t.local).length > AC_MAX_FOLLOWUPS;
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
        {convos.length > 0 && <button className="ac-rail-clear" onClick={() => NotesStore.clearConvos()}>Clear all</button>}
      </aside>

      <main className="ac-main">
        <div className="ac-construction" role="note">
          <svg className="ac-construction-i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M10.3 3.2 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.2a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>
          </svg>
          <span><b>Under construction</b> — answers can be rough or incomplete while this tab is being tuned.</span>
        </div>
        {isMobile && (
          <div className="ac-mobi-actions">
            {started && (
              <button className="ac-mobi-new" onClick={newThread}
                title="Start a new conversation">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>
                New search
              </button>
            )}
            <button className="ac-mobi-hist" onClick={() => setRailOpen(true)}
              title="Recent conversations">
              <Icon.Clock/> Recent
            </button>
          </div>
        )}
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
                busy={busy} quota={quota}
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
                  <AcTurn key={i} turn={turn} onReadInContext={onReadInContext} onLemma={onLemma} onStrongs={onStrongs}/>
                ))}
              </div>
            </div>
            <AcComposer pinned={true} value={draft} setValue={setDraft} onSubmit={() => ask(draft)}
              busy={busy} quota={quota}
              placeholder={followCapped ? "Follow-up limit reached — start a new thread" : "Ask a follow-up…"}/>
          </>
        )}
      </main>
    </div>
  );
}
