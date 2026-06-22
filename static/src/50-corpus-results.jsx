// ============================================================
// SHARED VERSE ROW — used by both Search (CorpusGroup) and the Lexicon tab.
// Lazy-loads its own words; highlights any word whose Strong's is in citedStrongs.
// ============================================================
function VerseRow({ book, chapter, verse, label, allResults, onWordClick, onReadInContext, textMode, primaryStrongs, citedStrongs, kjvCache }) {
  const [words, setWords] = useState(null);
  const [kjvText, setKjvText] = useState(null);
  const [visible, setVisible] = useState(false);
  const rowRef = useRef(null);
  const downRef = useRef(null);   // pointer-down spot, to tell a clean tap from a select-drag

  useEffect(() => {
    const el = rowRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { rootMargin: "300px" }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!visible) return;
    let cancelled = false;
    setWords(null);
    api.verseWords(book, chapter, verse)
      .then(d => { if (!cancelled) setWords(d.words || []); })
      .catch(() => { if (!cancelled) setWords([]); });
    return () => { cancelled = true; };
  }, [visible, book, chapter, verse]);

  useEffect(() => {
    if (!visible || textMode !== "kjv") return;
    const cacheKey = `${book}:${chapter}:${verse}`;
    if (kjvCache && kjvCache[cacheKey]) {
      setKjvText(kjvCache[cacheKey]);
      return;
    }
    let cancelled = false;
    setKjvText(null);
    api.kjvVerseWords(book, chapter, verse)
      .then(d => { if (!cancelled) setKjvText(Array.isArray(d) ? d : []); })
      .catch(() => { if (!cancelled) setKjvText([]); });
    return () => { cancelled = true; };
  }, [visible, book, chapter, verse, textMode, kjvCache]);

  // citedStrongs is passed in from App level; the matched word(s) are highlighted in
  // the prose below. No per-word entry map — clicking a word is the reader's job now.

  // The WHOLE ROW is the tap target (touch has no hover, and the ref is a tiny target): a
  // clean tap/click jumps to the verse. A drag-to-select or an active text selection does
  // NOT jump (reuse the Study-graph "did they move?" guard). The ref stays a real <button>
  // so keyboard / screen-reader users still have a focusable control.
  const clickable = !!onReadInContext;
  const jump = () => onReadInContext?.(book, chapter, verse);
  const onRowDown = (e) => { downRef.current = { x: e.clientX, y: e.clientY }; };
  const onRowClick = (e) => {
    const sel = (typeof window !== "undefined" && window.getSelection) ? window.getSelection() : null;
    if (sel && String(sel).length > 0) return;          // user was selecting text → don't jump
    const d = downRef.current;
    if (d && (Math.abs(e.clientX - d.x) > 5 || Math.abs(e.clientY - d.y) > 5)) return;  // a drag
    jump();
  };

  return (
    <div className={"corpus-verse" + (clickable ? " corpus-verse--click" : "")} ref={rowRef}
      onMouseDown={clickable ? onRowDown : undefined} onClick={clickable ? onRowClick : undefined}>
      <button className="corpus-ref" onClick={(e) => { e.stopPropagation(); jump(); }}>{label}</button>
      <span className="corpus-text">
        {textMode === "kjv" ? (
          kjvText === null
            ? <span style={{ color: "var(--ink-4)", fontSize: "13px" }}>Loading…</span>
            : kjvText.map((w, i) => {
                // Prose: plain readable text, the matched word gold-highlighted. No
                // per-word click — the reference jumps into the reader for word study.
                const sid = w.strongs_ids && w.strongs_ids.length ? w.strongs_ids[0] : null;
                const sidBare = sid ? sid.replace(/^[GH]/i, "") : null;
                const isCited = sid && citedStrongs != null && citedStrongs.size > 0 &&
                  (citedStrongs.has(sid) || citedStrongs.has(sidBare));
                const cls = (w.italic ? "lib-prose-italic " : "") + (isCited ? "corpus-hit" : "");
                // space OUTSIDE the span so a highlighted match hugs just the word
                return <React.Fragment key={i}><span className={cls.trim() || undefined}>{w.word}{w.punc || ""}</span>{" "}</React.Fragment>;
              })
        ) : words === null ? (
          <span style={{ color: "var(--ink-4)", fontSize: "13px" }}>Loading…</span>
        ) : (() => {
          // Prose: readable english in reading order — identical to the reader's prose
          // mode (reuse LibRender.renderProseWords). The matched word(s) — those whose
          // Strong's is in citedStrongs — get the gold "corpus-hit" highlight via a
          // hiClass that lights up their position. No per-word click / brackets /
          // numbers; the reference button jumps into the reader to study any word.
          const citedPositions = new Set(
            (citedStrongs && citedStrongs.size)
              ? words.filter(w => citedStrongs.has(w.strongs_base) || citedStrongs.has(strongsBare(w.strongs_base))
                                || citedStrongs.has(w.strongs) || citedStrongs.has(strongsBare(w.strongs))).map(w => w.position)
              : []
          );
          const proseCtx = {
            selChapter: chapter,
            hiClass: (vs, pos) => citedPositions.has(pos) ? " corpus-hit" : "",
          };
          return LibRender.renderProseWords(proseCtx, { verse, words, _ch: chapter }, { tightSpace: true });
        })()}
      </span>
    </div>
  );
}

// ============================================================
// CORPUS SEARCH — PASSAGE GROUP (collapsible book+chapter section)
// ============================================================
function CorpusGroup({ label, verses, allResults, onWordClick, onReadInContext, textMode, primaryStrongs, citedStrongs, kjvCache }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="corpus-group">
      <button
        className={"corpus-group-head " + (open ? "open" : "")}
        onClick={() => setOpen(o => !o)}
      >
        <Icon.Book style={{ opacity: 0.5, flexShrink: 0 }}/>
        <span className="corpus-group-label">{label}</span>
        <span className="corpus-group-count">{verses.length} verse{verses.length !== 1 ? "s" : ""}</span>
        <span className={"corpus-chevron " + (open ? "open" : "")}/>
      </button>
      {open && (
        <div className="corpus-group-body">
          {verses.map(v => (
            <VerseRow
              key={`${v.book}-${v.chapter}-${v.verse}`}
              book={v.book}
              chapter={v.chapter}
              verse={v.verse}
              label={v.ref}
              allResults={allResults}
              onWordClick={onWordClick}
              onReadInContext={onReadInContext}
              textMode={textMode}
              primaryStrongs={primaryStrongs}
              citedStrongs={citedStrongs}
              kjvCache={kjvCache}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================
// CORPUS SEARCH — OUTER CONTAINER
// ============================================================
function CorpusResults({ allResults, primaryStrongs, citedStrongs, showAll, onWordClick, onReadInContext, corpusSort, textMode }) {
  const [kjvCache, setKjvCache] = useState({}); // pre-fetched KJV verse words

  // Pre-fetch all KJV verse words in one batch when switching to KJV mode
  React.useEffect(() => {
    if (textMode !== "kjv" || !allResults.length) return;
    const seen = new Set();
    const refs = [];
    for (const e of allResults) {
      const key = `${e.book}:${e.chapter}:${e.verse}`;
      if (!seen.has(key)) { seen.add(key); refs.push({book: e.book, chapter: e.chapter, verse: e.verse}); }
    }
    if (!refs.length) return;
    let cancelled = false;
    api.kjvVerseWordsBatch(refs)
      .then(data => { if (!cancelled) setKjvCache(data); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [textMode, allResults]);

  const groups = useMemo(() => {
    const gMap = {};
    const gOrder = [];
    for (const entry of allResults) {
      const gk = `${entry.book}-${entry.chapter}`;
      if (!gMap[gk]) {
        gMap[gk] = {
          label: `${BOOK_LABELS[entry.book] || entry.book} · Chapter ${entry.chapter}`,
          verseMap: {},
          verseOrder: [],
        };
        gOrder.push(gk);
      }
      const vk = `${entry.book}-${entry.chapter}-${entry.verse}`;
      if (!gMap[gk].verseMap[vk]) {
        gMap[gk].verseMap[vk] = {
          book: entry.book, chapter: entry.chapter, verse: entry.verse, ref: entry.ref,
          is_primary: entry.is_primary,
          is_additional: entry.is_additional,
        };
        gMap[gk].verseOrder.push(vk);
      }
    }
    return gOrder
      .map(gk => ({
        label:  gMap[gk].label,
        verses: gMap[gk].verseOrder.map(vk => gMap[gk].verseMap[vk]),
      }))
      .sort((a, b) => {
        if (corpusSort === "canonical") {
          const bookDiff = (BOOK_ORDER[a.verses[0]?.book] ?? 99) - (BOOK_ORDER[b.verses[0]?.book] ?? 99);
          return bookDiff || (a.verses[0]?.chapter ?? 0) - (b.verses[0]?.chapter ?? 0);
        }
        const aPrimary = a.verses.filter(v => v.is_primary).length;
        const bPrimary = b.verses.filter(v => v.is_primary).length;
        return bPrimary - aPrimary || b.verses.length - a.verses.length;
      });
  }, [allResults, corpusSort]);

  const hasPrimary = allResults.some(e => e.is_primary);
  const hasAdditional = allResults.some(e => e.is_additional);

  const primaryGroups = hasPrimary
    ? groups.map(g => ({ ...g, verses: g.verses.filter(v => v.is_primary) })).filter(g => g.verses.length > 0)
    : groups;

  const additionalGroups = hasAdditional
    ? groups.map(g => ({ ...g, verses: g.verses.filter(v => v.is_additional) })).filter(g => g.verses.length > 0)
    : [];

  const otherGroups = (hasPrimary || hasAdditional)
    ? groups.map(g => ({ ...g, verses: g.verses.filter(v => !v.is_primary && !v.is_additional) })).filter(g => g.verses.length > 0)
    : [];

  const passageGroupProps = { allResults, onWordClick, onReadInContext, textMode, primaryStrongs, citedStrongs, kjvCache };

  return (
    <div className="corpus-groups">

      {primaryGroups.map(g => (
        <CorpusGroup key={g.label} label={g.label} verses={g.verses} {...passageGroupProps} />
      ))}
      {additionalGroups.length > 0 && (
        <div className="additional-refs-section">
          <div className="additional-refs-label">
            Additional references
            <span style={{ fontWeight: 400, color: "var(--ink-4)" }}> · related by theme — may not contain the word</span>
          </div>
          {additionalGroups.map(g => (
            <CorpusGroup key={g.label} label={g.label} verses={g.verses} {...passageGroupProps} />
          ))}
        </div>
      )}
      {showAll && otherGroups.map(g => (
        <CorpusGroup key={g.label} label={g.label} verses={g.verses} {...passageGroupProps} />
      ))}
    </div>
  );
}
