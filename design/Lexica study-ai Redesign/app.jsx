const { useState, useEffect, useRef, useMemo } = React;

// ============================================================
// SAMPLE DATA — Greek lexicon entries (original synthesis)
// ============================================================
const ENTRIES = [
  {
    id: "g3056-john-1-1",
    strongs: "G3056",
    greek: "λόγος",
    translit: "lógos",
    gloss: "word, reason, account",
    pos: "Noun, masculine",
    ref: "John 1:1",
    refLong: "John 1:1",
    verseKJV: "In the beginning was the Word, and the Word was with God, and the Word was God.",
    kjvGloss: "Word (218×), saying (50×), account (8×), speech (8×), thing (5×), misc. (32×)",
    derivation: "From the verb λέγω (légō, G3004) — \"to speak, lay forth, gather\". Originally signified the gathering or arrangement of thoughts into speech.",
    definition: "A word, uttered by a living voice; that which embodies a conception or idea. By extension: the divine expression — the rational principle by which the cosmos coheres. In Johannine theology, the pre-incarnate Christ understood as the self-disclosure of God.",
    occurrences: 330,
    related: ["G3004 λέγω", "G3050 λογικός", "G3053 λογισμός"],
  },
  {
    id: "g26-1cor-13-4",
    strongs: "G26",
    greek: "ἀγάπη",
    translit: "agápē",
    gloss: "love, charity, benevolence",
    pos: "Noun, feminine",
    ref: "1 Cor 13:4",
    refLong: "1 Corinthians 13:4",
    verseKJV: "Charity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up.",
    kjvGloss: "love (86×), charity (27×), dear (1×), charitably (1×), feast of charity (1×)",
    derivation: "From ἀγαπάω (agapáō, G25). Distinct from φιλία (philia, affection) and ἔρως (érōs, desire) — denotes volitional, principled benevolence.",
    definition: "Affection, good-will, love, benevolence; the love feasts. In NT usage: a self-giving, covenantal regard for the other — not contingent upon merit or reciprocation. Used of God's love toward humanity and the corresponding disposition demanded of believers.",
    occurrences: 116,
    related: ["G25 ἀγαπάω", "G27 ἀγαπητός"],
  },
  {
    id: "g4151-john-4-24",
    strongs: "G4151",
    greek: "πνεῦμα",
    translit: "pneûma",
    gloss: "spirit, breath, wind",
    pos: "Noun, neuter",
    ref: "John 4:24",
    refLong: "John 4:24",
    verseKJV: "God is a Spirit: and they that worship him must worship him in spirit and in truth.",
    kjvGloss: "Spirit (111×), Holy Ghost (89×), spirit (133×), wind (1×), life (1×), spiritual (1×)",
    derivation: "From πνέω (pnéō, G4154) — \"to breathe, blow\". The same root yields πνοή (breath) and πνευματικός (spiritual).",
    definition: "A movement of air, gentle blast; the wind; breath of mouth or nostrils; the spirit, i.e. the vital principle by which the body is animated. Of the Holy Spirit: the third person of the Godhead, the immanent presence of God acting upon and within creation.",
    occurrences: 385,
    related: ["G4154 πνέω", "G4152 πνευματικός", "G4157 πνοή"],
  },
  {
    id: "g3107-matt-5-3",
    strongs: "G3107",
    greek: "μακάριος",
    translit: "makários",
    gloss: "blessed, happy, fortunate",
    pos: "Adjective",
    ref: "Matt 5:3",
    refLong: "Matthew 5:3",
    verseKJV: "Blessed are the poor in spirit: for theirs is the kingdom of heaven.",
    kjvGloss: "blessed (44×), happy (5×), happier (1×)",
    derivation: "Prolonged form of an obsolete μάκαρ — of the same meaning. Originally applied to the gods, and to the dead who had attained the bliss of the next life.",
    definition: "Supremely blest; by extension, fortunate, well off. In the Beatitudes: not merely subjective happiness but an objective state of divine favor — a flourishing rooted in alignment with the kingdom of God, often paradoxically realized through apparent loss.",
    occurrences: 50,
    related: ["G3106 μακαρίζω", "G3108 μακαρισμός"],
  },
  {
    id: "g5485-eph-2-8",
    strongs: "G5485",
    greek: "χάρις",
    translit: "cháris",
    gloss: "grace, favor, kindness",
    pos: "Noun, feminine",
    ref: "Eph 2:8",
    refLong: "Ephesians 2:8",
    verseKJV: "For by grace are ye saved through faith; and that not of yourselves: it is the gift of God.",
    kjvGloss: "grace (130×), favour (6×), thanks (4×), thank (4×), pleasure (2×), misc. (10×)",
    derivation: "From χαίρω (chaírō, G5463) — \"to rejoice\". Cognate with χαρά (joy) — that which causes or produces gladness.",
    definition: "Graciousness of manner or act; abstractly, the divine influence upon the heart and its reflection in the life. In Pauline theology: unmerited divine favor as the operative cause of salvation, in contradistinction to works of the law.",
    occurrences: 156,
    related: ["G5463 χαίρω", "G5479 χαρά", "G5486 χάρισμα"],
  },
  {
    id: "g225-john-14-6",
    strongs: "G225",
    greek: "ἀλήθεια",
    translit: "alḗtheia",
    gloss: "truth, truthfulness, reality",
    pos: "Noun, feminine",
    ref: "John 14:6",
    refLong: "John 14:6",
    verseKJV: "Jesus saith unto him, I am the way, the truth, and the life: no man cometh unto the Father, but by me.",
    kjvGloss: "truth (107×), truly (1×), verity (1×)",
    derivation: "From ἀληθής (alēthḗs, G227); compounded of the alpha-privative (ἀ-) and λήθω/λανθάνω — \"to escape notice, be hidden\". Literally: that which is not concealed; un-hiddenness.",
    definition: "Objectively: what is true in any matter under consideration. Subjectively: truth as a personal excellence; that candor of mind which is free from affectation, pretense, or simulation. In Johannine usage, truth is not abstract but personal — embodied in Christ.",
    occurrences: 109,
    related: ["G227 ἀληθής", "G228 ἀληθινός", "G230 ἀληθῶς"],
  },
  {
    id: "g4102-heb-11-1",
    strongs: "G4102",
    greek: "πίστις",
    translit: "pístis",
    gloss: "faith, belief, trust",
    pos: "Noun, feminine",
    ref: "Heb 11:1",
    refLong: "Hebrews 11:1",
    verseKJV: "Now faith is the substance of things hoped for, the evidence of things not seen.",
    kjvGloss: "faith (239×), assurance (1×), believe (with G1537) (1×), belief (1×), them that believe (1×), fidelity (1×)",
    derivation: "From πείθω (peíthō, G3982) — \"to persuade, to be persuaded\". Faith, then, is the state of being persuaded.",
    definition: "Conviction of the truth of anything, belief; in the NT of a conviction or belief respecting man's relationship to God and divine things, generally with the included idea of trust and holy fervor born of faith and conjoined with it.",
    occurrences: 244,
    related: ["G3982 πείθω", "G4100 πιστεύω", "G4103 πιστός"],
  },
  {
    id: "g1680-rom-15-13",
    strongs: "G1680",
    greek: "ἐλπίς",
    translit: "elpís",
    gloss: "hope, expectation",
    pos: "Noun, feminine",
    ref: "Rom 15:13",
    refLong: "Romans 15:13",
    verseKJV: "Now the God of hope fill you with all joy and peace in believing, that ye may abound in hope, through the power of the Holy Ghost.",
    kjvGloss: "hope (53×), faith (1×)",
    derivation: "From a primary ἔλπω — \"to anticipate, usually with pleasure\".",
    definition: "Expectation of good, hope; in the Christian sense, joyful and confident expectation of eternal salvation. Distinct from mere wishfulness — grounded in the character and promises of God.",
    occurrences: 54,
    related: ["G1679 ἐλπίζω"],
  },
];

// ============================================================
// ICONS — minimal line set
// ============================================================
const Icon = {
  Search: (p) => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
    </svg>
  ),
  Sparkle: (p) => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>
    </svg>
  ),
  Close: (p) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M6 6l12 12M6 18 18 6"/>
    </svg>
  ),
  ArrowRight: (p) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M5 12h14M13 6l6 6-6 6"/>
    </svg>
  ),
  Book: (p) => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v18H6.5a2.5 2.5 0 0 0 0 5H20"/><path d="M8 6h8M8 10h6"/>
    </svg>
  ),
  Filter: (p) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M3 6h18M6 12h12M10 18h4"/>
    </svg>
  ),
  Bookmark: (p) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M6 3h12v18l-6-4-6 4z"/>
    </svg>
  ),
  Copy: (p) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>
    </svg>
  ),
  Share: (p) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7M16 6l-4-4-4 4M12 2v13"/>
    </svg>
  ),
};

// ============================================================
// HEADER
// ============================================================
function Header() {
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
          <a className="hdr-link active" href="#">Search</a>
          <a className="hdr-link" href="#">Concordance</a>
          <a className="hdr-link" href="#">Library</a>
          <a className="hdr-link" href="#">Notes</a>
        </nav>
        <div className="hdr-right">
          <button className="hdr-icon-btn" aria-label="Saved">
            <Icon.Bookmark/>
          </button>
          <div className="hdr-avatar">JM</div>
        </div>
      </div>
    </header>
  );
}

// ============================================================
// SEARCH BAR — two equal inputs side by side
// ============================================================
function SearchBar({ q1, setQ1, q2, setQ2, onSubmit, aiThinking }) {
  return (
    <section className="search">
      <div className="search-grid">
        <div className="search-cell">
          <label className="search-label">
            <span className="search-eyebrow">Lexicon</span>
            <span className="search-hint">Word, transliteration, or Strong's №</span>
          </label>
          <div className="search-field">
            <Icon.Search className="search-icon"/>
            <input
              type="text"
              className="search-input"
              placeholder="λόγος   ·   agape   ·   G5485"
              value={q1}
              onChange={(e) => setQ1(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSubmit()}
            />
            <kbd className="search-kbd">⌘ K</kbd>
          </div>
          <div className="search-chips">
            <button className="chip">Greek</button>
            <button className="chip">Hebrew</button>
            <button className="chip chip-active">All</button>
            <span className="chip-sep">·</span>
            <button className="chip ghost"><Icon.Filter/> Filters</button>
          </div>
        </div>
        <div className="search-divider" aria-hidden="true"></div>
        <div className="search-cell">
          <label className="search-label">
            <span className="search-eyebrow ai">
              <span className="ai-dot"></span>
              Ask the corpus
            </span>
            <span className="search-hint">Natural language across the lexicon</span>
          </label>
          <div className="search-field ai-field">
            <Icon.Sparkle className="search-icon"/>
            <input
              type="text"
              className="search-input"
              placeholder="What does Paul mean by ‘grace’ in Ephesians?"
              value={q2}
              onChange={(e) => setQ2(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSubmit()}
            />
            <button className="search-go" onClick={onSubmit} aria-label="Submit">
              {aiThinking ? <span className="spinner"/> : <Icon.ArrowRight/>}
            </button>
          </div>
          <div className="search-chips">
            <button className="chip suggest">"compare ἀγάπη and φιλία"</button>
            <button className="chip suggest">"Pauline use of πίστις"</button>
          </div>
        </div>
      </div>
    </section>
  );
}

// ============================================================
// RESULT CARD
// ============================================================
function ResultCard({ entry, active, onClick }) {
  return (
    <article
      className={"card " + (active ? "card-active" : "")}
      onClick={onClick}
      tabIndex="0"
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onClick()}
    >
      <div className="card-top">
        <span className="card-ref">{entry.ref}</span>
        <span className="card-badge">{entry.strongs}</span>
      </div>
      <div className="card-greek">{entry.greek}</div>
      <div className="card-translit">{entry.translit}</div>
      <div className="card-gloss">{entry.gloss}</div>
      <div className="card-foot">
        <span className="card-pos">{entry.pos}</span>
        <span className="card-occ">{entry.occurrences}× NT</span>
      </div>
    </article>
  );
}

// ============================================================
// SIDEBAR / BOTTOM SHEET
// ============================================================
function DetailPanel({ entry, isMobile, onClose }) {
  if (!entry) return null;
  return (
    <aside className={"detail " + (isMobile ? "detail-sheet" : "detail-side")} role="dialog" aria-label="Lexicon detail">
      {isMobile && <div className="sheet-handle" aria-hidden="true"></div>}
      <div className="detail-head">
        <div className="detail-head-l">
          <span className="card-badge solid">{entry.strongs}</span>
          <span className="detail-pos">{entry.pos}</span>
        </div>
        <button className="detail-close" onClick={onClose} aria-label="Close">
          <Icon.Close/>
        </button>
      </div>

      <div className="detail-body">
        <div className="detail-hero">
          <div className="detail-greek">{entry.greek}</div>
          <div className="detail-translit-row">
            <span className="detail-translit">{entry.translit}</span>
            <button className="tool-btn" title="Copy"><Icon.Copy/></button>
            <button className="tool-btn" title="Save"><Icon.Bookmark/></button>
            <button className="tool-btn" title="Share"><Icon.Share/></button>
          </div>
          <div className="detail-gloss">{entry.gloss}</div>
        </div>

        <section className="detail-section">
          <h4 className="detail-h">Definition</h4>
          <p className="detail-p">{entry.definition}</p>
        </section>

        <section className="detail-section">
          <h4 className="detail-h">KJV Translation Count</h4>
          <p className="detail-p mono">{entry.kjvGloss}</p>
        </section>

        <section className="detail-section">
          <h4 className="detail-h">Derivation</h4>
          <p className="detail-p">{entry.derivation}</p>
        </section>

        <section className="detail-section">
          <h4 className="detail-h">
            Verse — {entry.refLong}
            <span className="detail-h-sub">King James Version</span>
          </h4>
          <blockquote className="verse">
            <span className="verse-num">{entry.refLong.split(/[:\s]/).pop()}</span>
            {entry.verseKJV}
          </blockquote>
          <div className="verse-tools">
            <button className="link-btn">Read in context <Icon.ArrowRight/></button>
            <span className="dot">·</span>
            <button className="link-btn">Interlinear</button>
            <span className="dot">·</span>
            <button className="link-btn">Parallel</button>
          </div>
        </section>

        <section className="detail-section">
          <h4 className="detail-h">Related Lemmas</h4>
          <div className="related">
            {entry.related.map((r, i) => (
              <button key={i} className="related-pill">{r}</button>
            ))}
          </div>
        </section>

        <section className="detail-section last">
          <h4 className="detail-h">Frequency</h4>
          <div className="freq">
            <div className="freq-bar">
              <div className="freq-fill" style={{ width: Math.min(100, (entry.occurrences / 400) * 100) + "%" }}></div>
            </div>
            <div className="freq-meta">
              <span><b>{entry.occurrences}</b> occurrences in the Greek New Testament</span>
            </div>
          </div>
        </section>
      </div>
    </aside>
  );
}

// ============================================================
// AI ANSWER STRIP (appears when AI query submitted)
// ============================================================
function AIAnswer({ query, onPick }) {
  return (
    <section className="ai-answer">
      <div className="ai-answer-head">
        <span className="ai-tag">
          <span className="ai-dot"></span>
          Synthesis
        </span>
        <span className="ai-q">"{query}"</span>
      </div>
      <p className="ai-answer-body">
        Across the Pauline corpus, <em>χάρις</em> (cháris, G5485) denotes God's unmerited favor as the
        active cause of salvation — set in deliberate contrast to ἔργα νόμου (works of law). The locus
        classicus is Ephesians 2:8, where grace is paired with πίστις (faith) and gifted (δῶρον). See
        also 4 supporting entries below.
      </p>
      <div className="ai-cites">
        <span className="ai-cites-label">Cited:</span>
        <button className="ai-cite" onClick={() => onPick("g5485-eph-2-8")}>G5485 χάρις</button>
        <button className="ai-cite" onClick={() => onPick("g4102-heb-11-1")}>G4102 πίστις</button>
        <button className="ai-cite" onClick={() => onPick("g26-1cor-13-4")}>G26 ἀγάπη</button>
      </div>
    </section>
  );
}

// ============================================================
// APP
// ============================================================
function App() {
  const [q1, setQ1] = useState("");
  const [q2, setQ2] = useState("");
  const [activeId, setActiveId] = useState(null);
  const [isMobile, setIsMobile] = useState(false);
  const [aiSubmitted, setAiSubmitted] = useState(false);
  const [aiQuery, setAiQuery] = useState("");
  const [aiThinking, setAiThinking] = useState(false);
  const [sortBy, setSortBy] = useState("relevance");

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 860);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  const filtered = useMemo(() => {
    const q = q1.trim().toLowerCase();
    let list = ENTRIES;
    if (q) {
      list = list.filter((e) =>
        e.greek.toLowerCase().includes(q) ||
        e.translit.toLowerCase().includes(q) ||
        e.strongs.toLowerCase().includes(q) ||
        e.gloss.toLowerCase().includes(q)
      );
    }
    if (sortBy === "alpha") list = [...list].sort((a, b) => a.translit.localeCompare(b.translit));
    if (sortBy === "freq") list = [...list].sort((a, b) => b.occurrences - a.occurrences);
    return list;
  }, [q1, sortBy]);

  const active = ENTRIES.find((e) => e.id === activeId);

  const handleSubmit = () => {
    if (q2.trim()) {
      setAiThinking(true);
      setTimeout(() => {
        setAiSubmitted(true);
        setAiQuery(q2.trim());
        setAiThinking(false);
      }, 700);
    }
  };

  return (
    <div className={"app " + (active ? "has-detail" : "")}>
      <Header/>
      <main className="main">
        <div className="main-inner">
          <SearchBar
            q1={q1} setQ1={setQ1}
            q2={q2} setQ2={setQ2}
            onSubmit={handleSubmit}
            aiThinking={aiThinking}
          />

          {aiSubmitted && (
            <AIAnswer query={aiQuery} onPick={(id) => setActiveId(id)}/>
          )}

          <div className="results-head">
            <div className="results-meta">
              <span className="results-count">{filtered.length}</span>
              <span className="results-label">results</span>
              {q1.trim() && <span className="results-for">for "<b>{q1.trim()}</b>"</span>}
            </div>
            <div className="results-sort">
              <span className="sort-label">Sort</span>
              <button className={"sort-btn " + (sortBy === "relevance" ? "on" : "")} onClick={() => setSortBy("relevance")}>Relevance</button>
              <button className={"sort-btn " + (sortBy === "alpha" ? "on" : "")} onClick={() => setSortBy("alpha")}>A–Z</button>
              <button className={"sort-btn " + (sortBy === "freq" ? "on" : "")} onClick={() => setSortBy("freq")}>Frequency</button>
            </div>
          </div>

          <div className="results">
            {filtered.length === 0 ? (
              <div className="empty">
                <div className="empty-title">No matches</div>
                <div className="empty-sub">Try a different lemma, gloss, or Strong's number.</div>
              </div>
            ) : (
              filtered.map((entry) => (
                <ResultCard
                  key={entry.id}
                  entry={entry}
                  active={entry.id === activeId}
                  onClick={() => setActiveId(entry.id)}
                />
              ))
            )}
          </div>

          <footer className="foot">
            <span>Lemmas drawn from the Strong's enumeration of the Textus Receptus. Definitions paraphrased; not authoritative.</span>
          </footer>
        </div>
      </main>

      {active && !isMobile && (
        <DetailPanel entry={active} isMobile={false} onClose={() => setActiveId(null)}/>
      )}
      {active && isMobile && (
        <>
          <div className="sheet-scrim" onClick={() => setActiveId(null)}/>
          <DetailPanel entry={active} isMobile={true} onClose={() => setActiveId(null)}/>
        </>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
