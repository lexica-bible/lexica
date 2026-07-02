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
  if (!panel || !panel.groups || !panel.groups.length) return null;
  const fmt = (n) => (n != null ? n.toLocaleString() : "");
  return (
    <div className="cpanel" role="note" aria-label="How often these words occur">
      <div className="cpanel-tag">How often these words occur</div>
      {panel.groups.map((g, gi) => {
        const fam = g.family || [];
        if (!fam.length) return null;
        const core = fam[0], rest = fam.slice(1);
        const heb = g.lang === "H";
        const aside = g.set_aside || 0;
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
            {rest.map((r) => row(r, false))}
            {aside > 0 && (
              <div className="cpanel-aside">
                {aside} related form{aside > 1 ? "s" : ""} set aside — spelling matches, meaning unconfirmed
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// The answer's PROVENANCE — what the synthesis actually rests on. Driven by the SAME
// payload as the answer (results / keyStrongs / grounded), never a second lookup, so the
// rail and the note can't disagree. Provenance LEADS; the lexical-shape frequency panel
// folds beneath it, collapsed and subordinate. Populates on the stream's `done` event
// (results + grounding land at the tail); the bare frequency panel fills the rail while
// the synthesis is still writing.
const _PROV_PASSAGE_CAP = 6;   // show this many key passages before the "show all" expander
function ProvenancePanel({ answer, panel, onOccInspect, onStrongs, contestedSet }) {
  const results = answer.results || [];
  const cited = _acCited(answer.keyStrongs);
  const grounded = answer.grounded !== false;
  const words = answer.keyStrongs || [];
  // Key passages = the primary passages the synthesis leaned on, then any thematic
  // ("additional") refs, each tagged so a theme-only link isn't misread as direct evidence.
  // If nothing was flagged primary (a small pool), every retrieved verse shows. Deduped by ref.
  const hasPrimary = results.some(e => e.is_primary);
  const passages = [];
  const seen = new Set();
  const push = (e, theme) => { if (!seen.has(e.ref)) { seen.add(e.ref); passages.push({ ...e, theme }); } };
  if (hasPrimary) {
    for (const e of results) if (e.is_primary) push(e, false);
    for (const e of results) if (e.is_additional) push(e, true);
  } else {
    for (const e of results) push(e, false);
  }
  const evidenceCount = passages.filter(p => !p.theme).length;

  // Snippet translation toggle — same four texts as the old inline section. The snippet
  // text is fetched per verse by VerseRow (the payload carries only the ref), so flipping
  // the toggle just re-renders in that text. Defaults to ABP (the corpus anchor). HEB is
  // heb.db (OT-only), so it's offered only when the answer cites OT verses, and in HEB mode
  // the list is trimmed to those OT verses (no blank rows for NT/Greek verses).
  const hasOtVerse = passages.some(p => !NT_BOOKS.has(p.book));
  const [textMode, setTextMode] = useState("abp");
  const [showAll, setShowAll] = useState(false);
  const shownPassages = textMode === "heb" ? passages.filter(p => !NT_BOOKS.has(p.book)) : passages;
  const visible = showAll ? shownPassages : shownPassages.slice(0, _PROV_PASSAGE_CAP);

  // Clicking a passage PEEKS it into the drill (occurrence → fork → word), same as a prose
  // chip. The drill's "Read in context" then leaves for the Library — the old inline jump.
  const peek = (e) => onOccInspect && onOccInspect({
    book: e.book, chapter: e.chapter, verse: e.verse,
    label: `${BOOK_LABELS[e.book] || e.book} ${e.chapter}:${e.verse}`,
    textMode, cited, keyStrongs: words,
  });
  const peekGuarded = (e) => {
    if (window.getSelection && String(window.getSelection())) return;   // don't hijack text selection
    peek(e);
  };
  return (
    <div className="ac-prov">
      {grounded ? (
        <div className="ac-prov-grounded" role="note">
          Backed by {evidenceCount} {evidenceCount === 1 ? "passage" : "passages"} in the corpus.
        </div>
      ) : (
        <div className="ac-prov-caution" role="note">
          <b>No direct occurrences.</b> The corpus turned up no verse that actually uses this
          word, so the note is general background — not verse evidence. Verify against the text.
        </div>
      )}

      {shownPassages.length > 0 && (
        <div className="ac-prov-sec">
          <div className="ac-prov-h ac-prov-h--split">
            <span>Key passages</span>
            <div className="ac-tm ac-tm--rail" role="group" aria-label="Snippet text">
              {[["abp", "ABP", "Show the ABP (Greek)"],
                ["bsb", "BSB", "Show the BSB (modern English)"],
                ["kjv", "KJV", "Show the KJV"]].map(([m, lbl, t]) => (
                <button key={m} className={"ac-tm-b" + (textMode === m ? " on" : "")}
                  onClick={() => setTextMode(m)} title={t}>{lbl}</button>
              ))}
              <button className={"ac-tm-b" + (textMode === "heb" ? " on" : "")}
                onClick={() => setTextMode("heb")} disabled={!hasOtVerse}
                title={hasOtVerse ? "Show the Hebrew OT (Old Testament verses only)" : "No Old Testament verses in this answer"}>HEB</button>
            </div>
          </div>
          <div className="ac-prov-verses">
            {visible.map((e) => (
              <div key={e.ref} className="ac-prov-verse" onClick={() => peekGuarded(e)} title="Inspect this passage">
                <div className="ac-prov-vhead">
                  <span className="ac-prov-ref">{BOOK_LABELS[e.book] || e.book} {e.chapter}:{e.verse}</span>
                  {e.theme && <span className="ac-prov-theme" title="Related by theme — may not contain the word">theme</span>}
                  <span className="ac-prov-chev">›</span>
                </div>
                <div className="ac-prov-snippet">
                  <VerseRow book={e.book} chapter={e.chapter} verse={e.verse} textMode={textMode}
                    citedStrongs={cited} hideRef={true} />
                </div>
              </div>
            ))}
          </div>
          {shownPassages.length > _PROV_PASSAGE_CAP && (
            <button className="ac-prov-more" onClick={() => setShowAll(s => !s)}>
              {showAll ? "Show fewer" : `Show all ${shownPassages.length}`}
            </button>
          )}
        </div>
      )}

      {words.length > 0 && (
        <div className="ac-prov-sec">
          <div className="ac-prov-h">Words in scope</div>
          <div className="ac-prov-words">
            {words.map((w) => {
              const heb = /^H/i.test(w.strongs || w.strongs_base || "");
              // Badge a fork word from the payload flag OR the served contested set — the set
              // covers reopened saved threads whose stored copy predates the server flag.
              const isContested = w.contested || (contestedSet && contestedSet.has(w.strongs));
              return (
                <button key={w.strongs} className="ac-prov-word" onClick={() => onStrongs && onStrongs(w.strongs)}
                  title={"Study " + (w.translit || w.lemma) + " in Word study"}>
                  <span className={"ac-prov-lemma" + (heb ? " heb" : "")} dir={heb ? "rtl" : undefined}>{w.lemma}</span>
                  {w.translit && <span className="ac-prov-tr">{w.translit}</span>}
                  <span className="ac-prov-s">{w.strongs}</span>
                  {isContested && <span className="ac-prov-contested" title="This word's reading is contested — open it to see the fork">contested</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {panel && panel.groups && panel.groups.length > 0 && (
        <details className="ac-prov-freq">
          <summary>Lexical shape — how often these words occur</summary>
          <CorpusPanel panel={panel} onStrongs={onStrongs}/>
        </details>
      )}
    </div>
  );
}

// One answered (or in-flight) question.
function AcTurn({ turn, onReadInContext, onLemma, onStrongs, onOccInspect, selected, onSelect, isMobile }) {
  const cited = useMemo(() => _acCited(turn.keyStrongs), [turn.keyStrongs]);
  // Verses the search actually surfaced — the only ones the synthesis prose may
  // link. Anything the AI names outside this set renders un-linked (seatbelt).
  const verifiedRefs = useMemo(() => {
    if (turn.verified) return new Set(turn.verified);
    const s = new Set();
    for (const e of (turn.results || [])) s.add(`${e.book}-${e.chapter}-${e.verse}`);
    return s;
  }, [turn.verified, turn.results]);
  // MOBILE ONLY: the inline Key Passages block (with its own text toggle) — desktop moved
  // this into the provenance rail (ProvenancePanel), but mobile has no rail yet.
  const [manualMode, setManualMode] = useState(null);
  const textMode = manualMode || "abp";
  const displayResults = useMemo(() => {
    if (textMode !== "heb") return turn.results || [];
    return (turn.results || []).filter(e => !NT_BOOKS.has(e.book));
  }, [textMode, turn.results]);
  const hasOtVerse = useMemo(() => (turn.results || []).some(e => !NT_BOOKS.has(e.book)), [turn.results]);
  const primaryCount = useMemo(() => {
    if (!displayResults.length) return 0;
    const seen = new Set();
    for (const e of displayResults) if (e.is_primary) seen.add(e.ref);
    return seen.size || new Set(displayResults.map(e => e.ref)).size;
  }, [displayResults]);

  // A verse-ref CHIP in the synthesis PEEKS into the inspect rail (stays in corpus), carrying
  // this turn's word context. The KEY PASSAGES list below keeps its own jump-to-Library. On
  // mobile there's no rail yet, so a chip falls back to the jump-to-reader.
  const peekVerse = (book, chapter, verse) => {
    if (onOccInspect) {
      onSelect && onSelect();   // engaging this answer pins the rail to it too
      onOccInspect({ book, chapter, verse,
        label: `${BOOK_LABELS[book] || book} ${chapter}:${verse}`,
        textMode, cited, keyStrongs: turn.keyStrongs || [] });
    } else onReadInContext(book, chapter, verse);
  };

  // Click anywhere on the answer to point the rail at THIS answer's provenance — but
  // don't hijack a control (verse chip, toggle) or an in-progress text selection.
  const blockSelect = (e) => {
    if (!onSelect) return;
    if (e.target.closest("button, a")) return;
    if (window.getSelection && String(window.getSelection())) return;
    onSelect();
  };

  return (
    <div className={"ac-turn" + (selected ? " selected" : "")} onClick={blockSelect}>
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
          <div className="ac-syn-tag"><Icon.Sparkle/> Synthesis</div>
          {turn.grounded === false && (
            <div className="ac-ungrounded" role="note">
              <b>No direct occurrences found.</b> The corpus search turned up no verse that actually
              uses this word, so the note below is general background from the AI — not verse evidence.
              Treat it with caution and verify against the text.
            </div>
          )}
          <AcProse text={turn.explanation} onVerse={peekVerse} onStrongs={onStrongs} verified={verifiedRefs}/>

          {isMobile && turn.results && turn.results.length > 0 && (
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
          {onSelect && (
            <button className={"ac-select-src" + (selected ? " on" : "")} onClick={onSelect}
              title="Show what this answer rests on in the inspect panel">
              {selected ? "✓ Sources shown in panel" : "Show this answer's sources ›"}
            </button>
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

// ── Right-rail inspect (RightStack layers): occurrence → fork → word ─────────────
// The verse-ref chip in the synthesis PEEKS here. Depth 1 = the occurrence (this verse +
// the word the search turns on). From it: Read in context (LEAVE → reader), Contested
// reading (PUSH the fork, only when the word is contested), Full word study (PUSH the card).

// Depth 2/3 — the full word card in-rail: the Lexica dictionary entry when the word has one
// (LexicaBody, reused), else a lean card with the gloss + a jump to the Word study tab.
function AcWordLayer({ target, onOpenStudy }) {
  const strongs = target.strongs;
  const heb = /^H/i.test(strongs);
  const [lexica, setLexica] = useState(undefined);   // undefined = loading, null = none
  useEffect(() => {
    let live = true;
    api.lexica(strongs).then(d => live && setLexica(d && !d.error && d.strongs ? d : null))
      .catch(() => live && setLexica(null));
    return () => { live = false; };
  }, [strongs]);
  return (
    <div className="ac-insp-card">
      <div className="ac-insp-hero">
        <span className={"ac-insp-lemma" + (heb ? " heb" : "")} dir={heb ? "rtl" : undefined}>{target.lemma}</span>
        {target.translit && <span className="ac-insp-tr">{target.translit}</span>}
        <span className="ac-insp-s">{strongs}</span>
      </div>
      {lexica === undefined ? (
        <div className="ac-insp-loading">Loading…</div>
      ) : lexica ? (
        <LexicaBody lexica={lexica} lsjEntry={null} />
      ) : (
        <>
          {target.definition && <p className="ac-insp-gloss">{target.definition}</p>}
          <p className="ac-insp-hint">The full distribution, senses, and every occurrence live in Word study.</p>
        </>
      )}
      <button className="ac-insp-open" onClick={onOpenStudy}>Open in Word study ↗</button>
    </div>
  );
}

// Drill ROOT — the clicked occurrence.
function AcOccurrenceCard({ occ, onClose, onReadInContext, onOpenStudy, ctl }) {
  const target = (occ.keyStrongs && occ.keyStrongs[0]) || null;
  const strongs = target && target.strongs;
  const heb = strongs && /^H/i.test(strongs);
  const [lexica, setLexica] = useState(undefined);
  useEffect(() => {
    if (!strongs) { setLexica(null); return; }
    let live = true;
    api.lexica(strongs).then(d => live && setLexica(d && !d.error && d.strongs ? d : null))
      .catch(() => live && setLexica(null));
    return () => { live = false; };
  }, [strongs]);
  const fork = lexica && lexica.fork;
  return (
    <div className="ac-insp-root">
      <div className="ac-insp-band ac-insp-band--split">
        <button className="detail-back" onClick={onClose}>‹ Overview</button>
        <span className="ac-insp-ref">{occ.label}</span>
      </div>
      <div className="ac-insp-rbody">
      <div className="ac-insp-verse">
        <VerseRow book={occ.book} chapter={occ.chapter} verse={occ.verse} label={occ.label}
          textMode={occ.textMode} citedStrongs={occ.cited} onReadInContext={onReadInContext} />
      </div>
      {target && (
        <div className="ac-insp-word-line">
          <span className={"ac-insp-lemma" + (heb ? " heb" : "")} dir={heb ? "rtl" : undefined}>{target.lemma}</span>
          {target.translit && <span className="ac-insp-tr">{target.translit}</span>}
          <span className="ac-insp-s">{strongs}</span>
          {target.definition && <div className="ac-insp-gloss">{target.definition}</div>}
        </div>
      )}
      <div className="ac-insp-acts">
        <button className="ac-insp-act" onClick={() => onReadInContext(occ.book, occ.chapter, occ.verse)}>Read in context ›</button>
        {fork && (
          <button className="ac-insp-act" onClick={() => ctl.push({
            backLabel: "Occurrence",
            render: () => (
              <div className="ac-insp-card">
                <div className="ac-insp-hero-sm">Contested — <span className={heb ? "heb" : undefined} dir={heb ? "rtl" : undefined}>{target.lemma}</span></div>
                <LexicaFork fork={fork} />
              </div>
            ),
          })}>Contested reading ›</button>
        )}
        {strongs && (
          <button className="ac-insp-act" onClick={() => ctl.push({
            backLabel: "Occurrence",
            render: () => <AcWordLayer target={target} onOpenStudy={() => onOpenStudy(strongs)} />,
          })}>Full word study ›</button>
        )}
      </div>
      </div>
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
  const rightCtl = useRightStack();   // inspect-panel push stack (occurrence → fork → word)
  const [selectedOcc, setSelectedOcc] = useState(null);   // the peeked occurrence (null = idle)
  const [selIdx, setSelIdx] = useState(null);   // which answer the rail is pinned to (null = follow the newest)
  const [contestedSet, setContestedSet] = useState(null);   // fork Strong's set from the server (one source of truth)
  useNotesVersion();   // re-render when the store changes (e.g. a cross-device sync pulls convos in)
  const convos = NotesStore.corpusConvos();
  const busy = thread.some(t => t && (t.loading || t.streaming));   // a search is in flight (or streaming) — lock the composer

  // Seed the "questions left today" counter on mount (signed-in only; ignored otherwise).
  useEffect(() => {
    let live = true;
    fetch("/api/auth/me", { headers: _authHeaders() })
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (live && d && d.ai_quota) setQuota(d.ai_quota); })
      .catch(() => {});
    return () => { live = false; };
  }, []);

  // Load the contested (fork) Strong's set once — badges fork words even in reopened saved
  // threads whose stored copy predates the server-side flag (the register is the one source).
  useEffect(() => {
    let live = true;
    api.contestedStrongs().then(s => { if (live) setContestedSet(s); });
    return () => { live = false; };
  }, []);

  // Save the live conversation to the store so the rail can REOPEN it later with no
  // re-run. The store keeps it browser-local AND (when signed in) syncs it across
  // devices. One entry per thread keyed by currentId; loading turns are never stored.
  useEffect(() => {
    if (currentId == null) return;
    // A streaming turn is incomplete — don't save it until the `done` payload lands.
    const answered = thread.filter(t => t && t.question && !t.loading && !t.streaming);
    if (!answered.length) return;
    NotesStore.upsertConvo({ id: currentId, title: answered[0].question,
                             turns: thread.filter(t => t && !t.loading && !t.streaming) });
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
    setSelIdx(null);   // a fresh question takes focus — rail follows the newest answer again
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
    // buildTurn maps a finished payload (streamed OR a one-lump cache hit) to a turn.
    const buildTurn = (data) => {
      if (data.login) return { question: q, error: "Sign in to ask the corpus." };
      if (data.capped) return { question: q, notice: data.error, capped: true };
      if (data.global_capped) return { question: q, notice: data.error };
      if (data.out_of_scope) return { question: q, notice: data.explanation || "This tool searches the Greek & Hebrew Bible corpus — try a question about a word, theme, or passage." };
      if (data.error) return { question: q, error: data.error };
      return {
        question: q,
        explanation: data.explanation || "",
        keyStrongs: data.key_strongs || [],
        results: acDisplayedResults(flattenAiResults(data.results || [])),
        verified: (data.results || []).map(v => `${v.book}-${v.chapter}-${v.verse}`),
        total: data.total || 0,
        grounded: data.grounded !== false,   // false only when the backend says so
        panel: data.panel || null,           // computed lexical-texture panel (may be absent)
      };
    };
    try {
      await api.aiSearchStream(q, context, {
        // Panel first: switch out of the "thinking" state and show it while the synthesis writes.
        onPanel: (d) => setThread(t => t.map((x, i) => i === idx
          ? { question: q, streaming: true, panel: d.panel || null, explanation: "" } : x)),
        // Prose streams in word-by-word; append to the live turn (guard on `streaming` so a
        // late delta can't clobber a turn the `done` payload has already finalized).
        onDelta: (text) => setThread(t => t.map((x, i) => (i === idx && x && x.streaming)
          ? { ...x, explanation: (x.explanation || "") + text } : x)),
        // Done (or a one-lump cache hit): the authoritative payload replaces the turn.
        onDone: (data) => {
          if (data.quota) setQuota(data.quota);     // refresh the "left today" counter
          setThread(t => t.map((x, i) => i === idx ? buildTurn(data) : x));
          setSelIdx(null);   // the completed answer steals focus (new answer = new focus)
        },
        onError: (data) => setThread(t => t.map((x, i) => i === idx
          ? { question: q, error: data.error || "Something went wrong on that one." } : x)),
      });
    } catch (e) {
      setThread(t => t.map((x, i) => i === idx ? { question: q, error: "Network error: " + e.message } : x));
    }
  };

  // Start a clean conversation — clears the thread (back to the landing) but keeps
  // any Word-study scope and the saved-conversations rail. The current thread is
  // already saved by the effect above, so there's nothing to flush here.
  const newThread = () => { setThread([]); setDraft(""); setCurrentId(null); setSelIdx(null); if (isMobile) setRailOpen(false); };

  // Reopen a saved conversation — restores its turns verbatim. NO model calls (the
  // whole point): the answers are already in hand, so nothing re-runs.
  const openConvo = (c) => {
    setThread(c.turns || []);
    setCurrentId(c.id);
    setDraft("");
    setSelIdx(null);
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
  // Right-rail inspect: a prose ref chip peeks here (occurrence → fork → word). Peer-select
  // (another chip) resets the drill to the new occurrence; closing returns to the idle card.
  const onOccInspect = (occ) => { setSelectedOcc(occ); rightCtl.reset(); };
  const closeOcc = () => { setSelectedOcc(null); rightCtl.reset(); };
  // Point the rail at a specific answer (click-to-select). Also drops any open drill so the
  // rail returns to the idle provenance view for the chosen answer.
  const selectTurn = (i) => { setSelIdx(i); setSelectedOcc(null); rightCtl.reset(); };
  // Idle rail = the latest answer's frequency panel (the result-shape summary). Never blank.
  const latestPanel = useMemo(() => {
    for (let i = thread.length - 1; i >= 0; i--) if (thread[i] && thread[i].panel) return thread[i].panel;
    return null;
  }, [thread]);
  const isFinishedAnswer = (t) => t && t.results && !t.loading && !t.streaming && !t.error && !t.notice;
  // The latest FINISHED answer's index. A loading/streaming turn has no results yet, so during
  // a stream this is the previous answer (or -1 for the very first search → frequency panel).
  const latestAnswerIdx = useMemo(() => {
    for (let i = thread.length - 1; i >= 0; i--) if (isFinishedAnswer(thread[i])) return i;
    return -1;
  }, [thread]);
  // Which answer the rail shows: a user-selected turn if it's a finished answer, else the
  // latest (the default "follow the newest" behavior — every completed answer retains its own
  // provenance in the thread, so selecting an older one just re-points, no re-fetch).
  const selectedIdx = (selIdx != null && isFinishedAnswer(thread[selIdx])) ? selIdx : latestAnswerIdx;
  const selectedAnswer = selectedIdx >= 0 ? thread[selectedIdx] : null;
  const started = thread.length > 0;
  const followCapped = thread.filter(t => t && t.question && !t.local).length > AC_MAX_FOLLOWUPS;
  const suggestions = acScopeSuggestions(scope);

  // Shared zone contents, composed differently per layout. Desktop puts the composer in a
  // top STRIP (the shared Shell); mobile keeps its own hero/pinned placement until the mobile
  // shell migration (step 5). The inspect zone is the RightStack — an empty state for now;
  // step 3 fills it with the occurrence → fork → word drill.
  // The left rail is threads-only: the recent-conversation list. New Thread moved to the
  // center STRIP (it's a control) on desktop; mobile keeps its own new-search button.
  const railInner = (
    <>
      <div className="ac-rail-top"><span className="ac-rail-eyebrow"><Icon.Clock/> Recent conversations</span></div>
      {convos.length === 0
        ? <div className="ac-rail-empty">Your conversations are saved here — reopen one anytime.</div>
        : <div className="ac-rail-list">{convos.map((c) => (
            <button key={c.id} className={"ac-rail-item" + (c.id === currentId ? " on" : "")}
              onClick={() => openConvo(c)} title="Reopen this conversation">{c.title}</button>
          ))}</div>}
      {convos.length > 0 && <button className="ac-rail-clear" onClick={() => NotesStore.clearConvos()}>Clear all</button>}
    </>
  );

  const construction = (
    <div className="ac-construction" role="note">
      <svg className="ac-construction-i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M10.3 3.2 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.2a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>
      </svg>
      <span><b>Under construction</b> — answers can be rough or incomplete while this tab is being tuned.</span>
    </div>
  );

  // DESKTOP strip: a one-line construction note (left) + the New Thread control (right). The
  // ask bar is NOT here anymore — it's centered on the landing, then pinned to the center bottom.
  const stripNote = (
    <span className="ac-strip-note">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M10.3 3.2 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.2a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>
      </svg>
      <span><b>Under construction</b> — answers can be rough while this tab is tuned.</span>
    </span>
  );

  const landingHead = (
    <>
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
    </>
  );

  const examplesRow = (
    <div className="ac-examples">
      {suggestions.map((ex, i) => (
        <button key={i} className="ac-example" onClick={() => ask(ex)}><span>{ex}</span><Icon.ArrowRight/></button>
      ))}
    </div>
  );

  const threadBody = (
    <div className="ac-thread" ref={threadRef}>
      <div className="ac-thread-col">
        {thread.map((turn, i) => (
          <AcTurn key={i} turn={turn} onReadInContext={onReadInContext} onLemma={onLemma}
            onStrongs={onStrongs} onOccInspect={isMobile ? null : onOccInspect} isMobile={isMobile}
            selected={!isMobile && i === selectedIdx}
            onSelect={isMobile ? null : () => selectTurn(i)}/>
        ))}
      </div>
    </div>
  );

  const composerFor = (pinned) => (
    <AcComposer pinned={pinned} value={draft} setValue={setDraft} onSubmit={() => ask(draft)}
      busy={busy} quota={quota}
      placeholder={started
        ? (followCapped ? "Follow-up limit reached — start a new thread" : "Ask a follow-up…")
        : (scope ? `Ask about ${scope.translit || scope.lemma}…` : "Ask anything across the Bible…")}/>
  );

  // Inspect rail: idle = the latest answer's PROVENANCE (what it rests on) — with the
  // frequency panel folded beneath; a peeked ref chip replaces it with the occurrence →
  // fork → word drill. While a search streams there's no finished answer yet, so it shows
  // the bare frequency panel; before the first question, an empty prompt. Never blank.
  const inspectIdle = (
    <div className="ac-insp-idle">
      <div className="ac-insp-band">{selectedAnswer ? "What this answer rests on" : (latestPanel ? "How often these words occur" : "Inspect")}</div>
      <div className="ac-insp-scroll">
        {selectedAnswer
          ? <ProvenancePanel key={selectedIdx} answer={selectedAnswer} panel={selectedAnswer.panel} onOccInspect={onOccInspect} onStrongs={onStrongs} contestedSet={contestedSet}/>
          : latestPanel
            ? <CorpusPanel panel={latestPanel} onStrongs={onStrongs}/>
            : <ZoneEmpty icon={<Icon.Sparkle/>} title="Nothing selected yet"
                sub="Ask a question — the passages it rests on and the words it turns on show here. Then click a passage to inspect it."/>}
      </div>
    </div>
  );
  const inspectRoot = selectedOcc ? {
    key: `${selectedOcc.book}-${selectedOcc.chapter}-${selectedOcc.verse}`,
    render: () => <AcOccurrenceCard occ={selectedOcc} onClose={closeOcc} onReadInContext={onReadInContext}
      onOpenStudy={(s) => onNavigateToLexicon?.(s, /^H/i.test(s) ? "heb" : "abp")} ctl={rightCtl}/>,
  } : null;

  // ── MOBILE: unchanged layout (own hero/pinned composer) until the mobile shell step ──
  if (isMobile) {
    return (
      <div className={"ac" + (railOpen ? " rail-open" : "")}>
        {railOpen && <div className="ac-rail-scrim" onClick={() => setRailOpen(false)}/>}
        <aside className={"ac-rail" + (!railOpen ? " hidden" : "")}>{railInner}</aside>
        <main className="ac-main">
          {construction}
          <div className="ac-mobi-actions">
            {started && (
              <button className="ac-mobi-new" onClick={newThread} title="Start a new conversation">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>
                New search
              </button>
            )}
            <button className="ac-mobi-hist" onClick={() => setRailOpen(true)} title="Recent conversations">
              <Icon.Clock/> Recent
            </button>
          </div>
          {!started ? (
            <div className="ac-landing"><div className="ac-landing-in">
              {landingHead}
              {composerFor(false)}
              {examplesRow}
            </div></div>
          ) : (<>{threadBody}{composerFor(true)}</>)}
        </main>
      </div>
    );
  }

  // ── DESKTOP: the shared three-zone Shell. Chat pattern — the ask bar is centered on the
  // empty landing, then drops to a PINNED bar at the bottom of the center column once a thread
  // exists (the thread scrolls above it). The top strip carries the note + New Thread only. ──
  return (
    <Shell
      isMobile={false}
      className="ac-frame"
      centerClass="ac-center"
      rail={railInner}
      center={
        <>
          <div className="ac-strip">
            {stripNote}
            <button className="ac-strip-new" onClick={newThread} disabled={!started}
              title="Start a new conversation">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>
              New thread
            </button>
          </div>
          <div className="ac-body">
            {!started
              ? <div className="ac-landing"><div className="ac-landing-in">{landingHead}{composerFor(false)}{examplesRow}</div></div>
              : <>{threadBody}{composerFor(true)}</>}
          </div>
        </>
      }
      inspect={<RightStack ctl={rightCtl} root={inspectRoot} empty={inspectIdle} className="ac-rstack" />}
    />
  );
}
