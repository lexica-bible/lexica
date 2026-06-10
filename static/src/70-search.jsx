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
// GUIDED TOUR
// ============================================================
const TOUR_STEPS = [
  { icon: "Book",    label: "Welcome to Lexica", body: "Lexica is a Greek and Hebrew word study tool built for the diligent Berean. No prior training required. Every word traces back to its Greek or Hebrew source so you can read what the text actually says — before any theological framework is applied. You won't be a scholar overnight, but you'll immediately be a Berean." },
  { icon: "Search",  label: "The Lexicon",       body: "Search by English, Greek, Hebrew, transliteration, or Strong's number. Results span both Greek (LSJ) and Hebrew (BDB) — click any word for its full lexicon entry and a context-aware AI summary anchored in the source text." },
  { icon: "Book",    label: "The Library",       body: "Read in ABP Greek, KJV, or the Berean Standard Bible — on their own, in parallel, or compare them side by side. Switch between plain reading and a full interlinear (Hebrew over OT words, Greek over NT), follow the text in chronological order, or listen with read-along audio. Click any word for its lexicon entry; click any verse number for cross-references. Beyond the canon you'll also find the Apocrypha, 1 Enoch, and the Apostolic Fathers." },
  { icon: "Panel",   label: "Cross-References",  body: "Every verse connects to Torrey's Treasury of Scripture Knowledge — AI-curated to the strongest matches and synthesized into a thematic overview anchored in ABP vocabulary." },
  { icon: "Sparkle", label: "Ask the Corpus",    body: "Ask in plain language: 'Where does pneuma appear in Genesis?' or 'Differences in how KJV and ABP render spirit in the OT.' The AI searches Greek and Hebrew simultaneously and cites specific passages." },
  { icon: "Note",    label: "Notes & Highlights", body: "Highlight verses in five colors, write notes on any word or verse, drop bookmarks, and keep a free-form journal. It all saves in your browser automatically — no account required. Sign in with email or Google to sync everything across your devices." },
  { icon: "Book",    label: "Support Lexica",    body: "Lexica is free, independent, and has no ads. It's maintained by one person who thinks serious Bible study tools shouldn't cost hundreds of dollars. If it's been useful to your studies, a small contribution keeps it running.", donate: true },
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
            <a className="donate-btn kofi" href="https://ko-fi.com/lexica" target="_blank" rel="noopener noreferrer">☕ Ko-fi</a>
            <a className="donate-btn github" href="https://github.com/sponsors/jonathan-pernice" target="_blank" rel="noopener noreferrer">♥ GitHub Sponsors</a>
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
          </div>
        )}
        {owner && tab === "stats" ? <StatsView /> : (
        <>
        <h1 className="about-title">About Lexica</h1>
        <p className="about-lead">A Greek and Hebrew word study tool for the diligent Berean. No seminary required.</p>

        <h2 className="about-h2">What Lexica does</h2>
        <p className="about-p">Lexica lets you trace any English word in the Bible back to its Greek or Hebrew source and explore its full meaning — not just the translation choice made by one committee. Every word links to the Liddell-Scott-Jones Greek lexicon (LSJ) or Brown-Driver-Briggs Hebrew lexicon (BDB), the two most comprehensive scholarly references available.</p>
        <p className="about-p">The primary text is the <b>Apostolic Bible Polyglot (ABP)</b> — a word-for-word Greek interlinear covering both the Septuagint (OT) and New Testament. The <b>King James Version</b> and the <b>Berean Standard Bible</b> read alongside it — on their own, in parallel, or compared side by side — with read-along audio and an optional chronological reading order. Cross-references come from Torrey's Treasury of Scripture Knowledge.</p>
        <p className="about-p">Beyond the canon, Lexica includes a library of related texts: the Septuagint Apocrypha, the Pseudepigrapha (1 Enoch, Jubilees, and more), and the Apostolic Fathers with full Greek interlinear.</p>

        <h2 className="about-h2">Your study, saved</h2>
        <p className="about-p">Highlight verses, write notes on any word or verse, set bookmarks, and keep a free-form journal. Everything saves in your browser automatically — no account needed. Create a free account (email or Google) and your notes sync across every device. The app stays fully usable with no sign-in at all.</p>

        <h2 className="about-h2">The Berean approach</h2>
        <p className="about-p">The Bereans "received the word with all readiness of mind, and searched the scriptures daily" (Acts 17:11). Lexica is built on that same posture: let the Greek and Hebrew speak first, before any theological system is imported. No commentary, no denominational lens, no conclusions pre-loaded. The text speaks — you decide what it means.</p>
        <p className="about-p">Every AI-generated summary is anchored in the source vocabulary of the ABP. The system prompt explicitly forbids importing theology from outside the text.</p>

        <h2 className="about-h2">Methodology</h2>
        <ul className="about-ul">
          <li>Strong's numbers are the bridge between English, Greek, and Hebrew</li>
          <li>Greek definitions draw from LSJ — the standard classical Greek reference</li>
          <li>Hebrew definitions draw from BDB — the standard OT Hebrew reference</li>
          <li>AI search generates SQL against the full lexicon corpus — not a summary or paraphrase</li>
          <li>Translation comparisons surface where ABP, KJV, and the BSB make different rendering choices for the same source word</li>
        </ul>

        <h2 className="about-h2">Support Lexica</h2>
        <p className="about-p">Lexica is free, independent, and has no ads. It's maintained by one person who thinks serious Bible study tools shouldn't cost hundreds of dollars or require a seminary login. If it's been useful to you, a small contribution keeps the lights on.</p>
        <div className="about-donate">
          <a className="donate-btn kofi" href="https://ko-fi.com/lexica" target="_blank" rel="noopener noreferrer">☕ Ko-fi</a>
          <a className="donate-btn github" href="https://github.com/sponsors/jonathan-pernice" target="_blank" rel="noopener noreferrer">♥ GitHub Sponsors</a>
        </div>
        </>
        )}
      </div>
    </div>
  );
}
