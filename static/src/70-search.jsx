// ============================================================
// GLOSS GROUPINGS
// ============================================================
// ============================================================
// AI ANSWER STRIP
// ============================================================
function AIAnswer({ query, explanation, keyStrongs, onPick }) {
  return (
    <section className="ai-answer">
      <div className="ai-answer-head">
        <span className="ai-tag">
          <span className="ai-dot"></span>
          Synthesis
        </span>
        <span className="ai-q">"{query}"</span>
      </div>
      <p className="ai-answer-body">{explanation}</p>
      {keyStrongs && keyStrongs.length > 0 && (
        <div className="ai-cites">
          <span className="ai-cites-label">Cited:</span>
          {keyStrongs.map((ks) => (
            <button key={ks.strongs} className="ai-cite" onClick={() => onPick({
              id: `ks-${ks.strongs_base}`,
              strongs: ks.strongs,
              strongs_base: ks.strongs_base,
              strongs_raw: ks.strongs_base,
              greek: ks.lemma,
              translit: ks.translit,
              gloss: "",
              ref: "",
              book: "", chapter: 0, verse: 0,
              definition: ks.definition || "", derivation: ks.derivation || "",
            })}>
              {ks.strongs} {ks.translit || ks.lemma}
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

// ============================================================
// ASK-THE-CORPUS RESULTS
// ============================================================
// The AI answer + verse results, shown inside the Word study tab when a
// plain-language question is asked. (This was the standalone Search tab; the
// state still lives in App and is passed down as one bundle.)
function AiResults({
  notice, error, meta, mode, loading, aiLoading,
  primaryVerseCount, showAll, setShowAll,
  filter, setFilter, sort, setSort, textMode, setTextMode,
  results, primaryStrongs, citedStrongs, searchLabel,
  onWordClick, onReadInContext, onPick,
}) {
  return (
    <>
      {notice && (
        <div style={{ marginTop: "14px", padding: "12px 16px", background: "var(--accent-soft, #f0f4ff)", border: "1px solid var(--accent, #b0bfff)", borderRadius: "10px", color: "var(--ink-2, #444)", fontSize: "14px" }}>
          {notice}
        </div>
      )}
      {error && (
        <div style={{ marginTop: "14px", padding: "12px 16px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "10px", color: "#b91c1c", fontSize: "14px" }}>
          {error}
        </div>
      )}
      {meta && (
        <AIAnswer query={meta.query} explanation={meta.explanation} keyStrongs={meta.keyStrongs || []} onPick={onPick} />
      )}
      {mode === "ai" && (
        <>
          <div className="results-head">
            <div className="results-meta">
              <span className="results-count">{(loading || aiLoading) ? "…" : primaryVerseCount}</span>
              <span className="results-label">primary {primaryVerseCount === 1 ? "verse" : "verses"}</span>
              {!loading && meta && meta.total > primaryVerseCount && (
                <button className="see-all-link" onClick={() => setShowAll(v => !v)}>
                  {showAll ? "Show less" : `See all ${meta.total} occurrences`}
                </button>
              )}
              {searchLabel && !aiLoading && <span className="results-for">for "<b>{searchLabel}</b>"</span>}
            </div>
            <div className="results-controls" style={{ marginLeft: "auto" }}>
              <div className="results-sort">
                <button className={"sort-btn " + (filter === "all" ? "on" : "")} onClick={() => setFilter("all")}>All</button>
                <button className={"sort-btn " + (filter === "ot"  ? "on" : "")} onClick={() => setFilter("ot")}>OT</button>
                <button className={"sort-btn " + (filter === "nt"  ? "on" : "")} onClick={() => setFilter("nt")}>NT</button>
                <span style={{ margin: "0 4px", color: "var(--rule-2)" }}>|</span>
                <button className={"sort-btn " + (sort === "curated"   ? "on" : "")} onClick={() => setSort("curated")}>Curated</button>
                <button className={"sort-btn " + (sort === "canonical" ? "on" : "")} onClick={() => setSort("canonical")}>Canonical</button>
                <span style={{ margin: "0 4px", color: "var(--rule-2)" }}>|</span>
                <button className={"sort-btn " + (textMode === "abp" ? "on" : "")} onClick={() => setTextMode("abp")}>ABP</button>
                <button className={"sort-btn " + (textMode === "kjv" ? "on" : "")} onClick={() => setTextMode("kjv")}>KJV</button>
              </div>
            </div>
          </div>
          {(loading || aiLoading) ? (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--ink-3)", fontSize: "14px" }}>
              Searching…
            </div>
          ) : (
            <CorpusResults allResults={results} primaryStrongs={primaryStrongs} citedStrongs={citedStrongs} showAll={showAll} onWordClick={onWordClick} onReadInContext={onReadInContext} corpusSort={sort} textMode={textMode} />
          )}
        </>
      )}
    </>
  );
}

// ============================================================
// GUIDED TOUR
// ============================================================
const TOUR_STEPS = [
  { icon: "Book",    label: "Welcome to Lexica", body: "Lexica is a Greek and Hebrew word study tool built for the diligent Berean. No prior training required. Every word traces back to its Greek or Hebrew source so you can read what the text actually says — before any theological framework is applied. You won't be a scholar overnight, but you'll immediately be a Berean." },
  { icon: "Search",  label: "Word study",        body: "Search by English, Greek, Hebrew, transliteration, or Strong's number — or just ask a question in plain language like 'Where does pneuma appear in Genesis?' One word looks it up; a question searches the whole corpus and cites the passages. Results span both Greek (LSJ) and Hebrew (BDB) — click any word for its full lexicon entry and a context-aware AI summary anchored in the source text." },
  { icon: "Book",    label: "The Library",       body: "Read in ABP Greek, KJV, or the Berean Standard Bible — on their own, in parallel, or compare them side by side. Switch between plain reading and a full interlinear (Hebrew over OT words, Greek over NT), follow the text in chronological order, or listen with read-along audio. Click any word for its lexicon entry; click any verse number for cross-references. Beyond the canon you'll also find the Apocrypha, 1 Enoch, and the Apostolic Fathers." },
  { icon: "Panel",   label: "Cross-References",  body: "Every verse connects to Torrey's Treasury of Scripture Knowledge — AI-curated to the strongest matches and synthesized into a thematic overview anchored in ABP vocabulary." },
  { icon: "Note",    label: "Notes & Highlights", body: "Highlight verses in five colors, write notes on any word or verse, drop bookmarks, and keep a free-form journal. It all saves in your browser automatically — no account required. Sign in with email or Google to sync everything across your devices." },
  { icon: "Book",    label: "Get in touch",      body: "Lexica is free, independent, and has no ads — built and maintained by one person. Questions, corrections, or feedback on your studies? I'd genuinely love to hear from you.", donate: true },
];

function GuidedTour({ onDone }) {
  const [step, setStep] = useState(0);
  const cur = TOUR_STEPS[step];
  const StepIcon = Icon[cur.icon];
  const isLast = step === TOUR_STEPS.length - 1;

  return (
    <>
      <div className="tour-scrim" onClick={onDone} />
      <div className="tour-modal" role="dialog" aria-modal="true" aria-label="Welcome to Lexica">
        <button className="tour-skip" onClick={onDone}>Skip</button>
        <div className="tour-icon-wrap">
          <StepIcon width="20" height="20" />
        </div>
        <div className="tour-step-num">{step + 1} of {TOUR_STEPS.length}</div>
        <h2 className="tour-title">{cur.label}</h2>
        <p className="tour-body">{cur.body}</p>
        {cur.donate && (
          <div className="tour-donate-btns">
            <a className="donate-btn contact" href="mailto:hello@lexica.bible">✉ hello@lexica.bible</a>
            <a className="donate-btn kofi" href="https://ko-fi.com/lexica" target="_blank" rel="noopener noreferrer">☕ Support on Ko-fi</a>
          </div>
        )}
        <div className="tour-dots">
          {TOUR_STEPS.map((_, i) => (
            <button key={i} className={"tour-dot" + (i === step ? " active" : "")} onClick={() => setStep(i)} aria-label={`Step ${i + 1}`} />
          ))}
        </div>
        <div className="tour-nav">
          {step > 0 && (
            <button className="tour-btn tour-btn-prev" onClick={() => setStep(s => s - 1)}>Previous</button>
          )}
          {isLast ? (
            <button className="tour-btn tour-btn-done" onClick={onDone}>Get started</button>
          ) : (
            <button className="tour-btn tour-btn-next" onClick={() => setStep(s => s + 1)}>Next</button>
          )}
        </div>
      </div>
    </>
  );
}

// ============================================================
// ABOUT VIEW
// ============================================================
function AboutView({ owner }) {
  // The owner gets a private "Stats" view tucked behind a toggle here (no extra tab).
  const [tab, setTab] = useState("about");
  return (
    <div className="about-view">
      <div className="about-inner">
        {owner && (
          <div className="seg about-owner-seg">
            <button className={"seg-b" + (tab === "about" ? " on" : "")} onClick={() => setTab("about")}>About</button>
            <button className={"seg-b" + (tab === "stats" ? " on" : "")} onClick={() => setTab("stats")}>Stats</button>
            <button className={"seg-b" + (tab === "admin" ? " on" : "")} onClick={() => setTab("admin")}>Admin</button>
          </div>
        )}
        {owner && tab === "stats" ? <StatsView /> : owner && tab === "admin" ? <AdminView /> : (
        <>
        <h1 className="about-title">About Lexica</h1>
        <p className="about-lead">A Greek and Hebrew word study tool for the diligent Berean. No seminary required.</p>

        <h2 className="about-h2">The Berean approach</h2>
        <p className="about-p">The Bereans "received the word with all readiness of mind, and searched the scriptures daily" (Acts 17:11). Lexica is built on that posture: let the Greek and Hebrew speak before any theological system does. No commentary, no denominational lens, no conclusions pre-loaded — and where the tradition disagrees with itself, both readings on the table.</p>
        <p className="about-p">The text speaks. You decide what it means.</p>

        <h2 className="about-h2">What Lexica does</h2>
        <p className="about-p">Lexica lets you trace any English word in the Bible back to its Greek or Hebrew source and see what that word actually means — not just the rendering one translation committee chose. Search in English, Greek, Hebrew, or transliteration; land on the word; see every place it occurs.</p>
        <p className="about-p">The primary text is the <b>Apostolic Bible Polyglot (ABP)</b> — a word-for-word Greek interlinear covering both the Septuagint and the New Testament. The Hebrew Old Testament stands alongside it, so every Old Testament word can be traced in both its Hebrew original and its Greek rendering. The <b>King James Version</b> and the <b>Berean Standard Bible</b> read alongside as well — on their own, in parallel, or side by side — with read-along audio and an optional chronological reading order. Cross-references come from Torrey's Treasury of Scripture Knowledge.</p>
        <p className="about-p">Beyond the canon, the library includes the Septuagint Apocrypha, the Pseudepigrapha (1 Enoch, Jubilees, and more), and the Apostolic Fathers with full Greek interlinear.</p>

        <h2 className="about-h2">Where definitions come from</h2>
        <p className="about-p">This is what makes Lexica different, so it's worth being precise.</p>
        <p className="about-p">Most study tools hand you a lexicon entry and call it a definition. The problem is that lexicons carry history: centuries of classical usage, church tradition, and theological assumption baked into the glosses. Read one uncritically and you're importing someone else's conclusions without knowing it.</p>
        <p className="about-p">Lexica is building its definitions from the text itself: every sense of a word derived from its actual occurrences in the corpus, cited to the verses that support it. If a definition claims a word means something, you can click through to the passages where it means that — and judge for yourself. No sense ships without evidence.</p>
        <p className="about-p">This is a work in progress, and honesty about that is part of the method. Corpus-grounded definitions are live today for the most contested words in the New Testament, and are rolling out across the full vocabulary — highest-frequency words first. Where a word's entry hasn't been built yet, you'll see the raw materials instead: every occurrence in context, the interlinear rendering, and the scholarly lexicons (Liddell-Scott-Jones for Greek, Brown-Driver-Briggs for Hebrew) as reference. The lexicons inform; they don't dictate. The text speaks first — and where the tool can't yet meet its own standard, it shows you the evidence rather than a shortcut.</p>

        <h2 className="about-h2">When meaning is contested</h2>
        <p className="about-p">Some words carry two thousand years of argument — dikaioō, charis, sarx, ekklesia, and others. Most tools quietly pick a side and present it as the definition.</p>
        <p className="about-p">Lexica doesn't. Where a word's meaning is genuinely contested, it says so, and shows you the competing readings side by side — each grounded in the same verses, so you can see exactly where the interpretations divide. The tool's job is to surface the fork in the road, not to walk you down one branch.</p>

        <h2 className="about-h2">Ask the corpus</h2>
        <p className="about-p">Ask a question in plain English — "is baptizō immersion?", "what does Sheol mean in the O.T.?" — and Lexica answers from the corpus: senses synthesized from actual occurrences, every claim cited to verses you can open and check. The system is explicitly forbidden from importing theology from outside the text. Answers that can't be grounded in the vocabulary don't ship.</p>
        <p className="about-p">Corpus search requires a free account, and supporters get a higher usage tier — these searches cost real money to run, and this keeps the tool free of ads.</p>

        <h2 className="about-h2">Your study, saved</h2>
        <p className="about-p">Highlight verses, write notes on any word or verse, set bookmarks, keep a free-form journal. Everything saves in your browser automatically — no account needed. Create a free account (email or Google) and it syncs across your devices, and unlocks corpus search. Reading, word study, and all your notes work with no sign-in at all.</p>

        <h2 className="about-h2">Methodology</h2>
        <ul className="about-ul">
          <li>Strong's numbers are the bridge between English, Greek, and Hebrew</li>
          <li>Definitions are built from the corpus — every sense derived from and cited to actual occurrences (rolling out across the full vocabulary, contested words first)</li>
          <li>LSJ (Greek) and BDB (Hebrew) are provided as scholarly reference — display, not source</li>
          <li>Contested words show competing readings rather than a resolved answer</li>
          <li>Translation comparisons surface where ABP, KJV, and BSB render the same source word differently</li>
          <li>AI answers are corpus-grounded and citation-gated; unsupported claims are blocked, not softened</li>
        </ul>

        <h2 className="about-h2">Get in touch</h2>
        <p className="about-p">Lexica is free, independent, and has no ads. It's maintained by one person who thinks serious Bible study shouldn't cost hundreds of dollars or require a seminary login. Questions, corrections, feedback? I'd love to hear from you.</p>
        <div className="about-donate">
          <a className="donate-btn contact" href="mailto:hello@lexica.bible">✉ hello@lexica.bible</a>
          <a className="donate-btn kofi" href="https://ko-fi.com/lexica" target="_blank" rel="noopener noreferrer">☕ Support on Ko-fi</a>
        </div>
        <p className="about-credit"><a href="/credits">Credits &amp; attributions</a></p>
        </>
        )}
      </div>
    </div>
  );
}
