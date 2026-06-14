// ============================================================
// CROSS-REFERENCE PANEL
// ============================================================
function CrossRefPanel({ source, onClose, onNavigate, isMobile, translation, onAiSearch, overviewBack, backLabel = "Overview" }) {
  const [refs, setRefs] = useState([]);
  const [synthesis, setSynthesis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [abpTexts, setAbpTexts] = useState({});
  const showAbp = translation === "abp" || translation === "parallel";

  useEffect(() => {
    if (!source) return;
    let cancelled = false;
    setRefs([]);
    setSynthesis(null);
    setAbpTexts({});
    setLoading(true);
    api.crossRefsCurated(source.book, source.chapter, source.verse)
      .then(d => {
        if (cancelled) return;
        setRefs(d.refs || []);
        setSynthesis(d.synthesis || null);
        setLoading(false);
      })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [source && source.book, source && source.chapter, source && source.verse]);

  useEffect(() => {
    if (!showAbp || !refs.length) { setAbpTexts({}); return; }
    let cancelled = false;
    Promise.all(
      refs.map(ref =>
        api.verse(ref.book, ref.chapter, ref.verse)
          .then(d => [ref.ref, d.text || ""])
          .catch(() => [ref.ref, ""])
      )
    ).then(pairs => { if (!cancelled) setAbpTexts(Object.fromEntries(pairs)); });
    return () => { cancelled = true; };
  }, [refs, showAbp]);

  const verseText = (ref) => showAbp ? (abpTexts[ref.ref] || ref.kjv_text) : ref.kjv_text;

  const sourceRef = `${source.book} ${source.chapter}:${source.verse}`;
  const heroRef = `${BOOK_LABELS[source.book] || source.book} ${source.chapter}:${source.verse}`;
  const { sheetRef, scrollRef } = useSwipeToDismiss(onClose);

  // Body shares the word-study / Reading-intro rail: a .detail-hero block (the
  // source reference + a passage count) then .sec/.sec-head sections — the AI
  // synthesis as "The connection" (Sonnet-written, so it carries the AI badge),
  // and the curated list as "Related passages".
  const content = (
    <>
      {(loading || synthesis) && (
        <section className="sec">
          <h4 className="sec-head">
            <span className="sec-t">The connection</span>
            <span className="lsj-badge lsj-badge--accent">AI</span>
          </h4>
          {loading ? (
            <p className="xref-synthesis-loading">Selecting relevant passages…</p>
          ) : (
            <p className="detail-p">{renderInlineMd(synthesis)}</p>
          )}
          {!loading && onAiSearch && (
            <button className="xref-ai-btn" onClick={() => { onClose(); onAiSearch(sourceRef); }}>
              Explore in the corpus →
            </button>
          )}
        </section>
      )}
      <section className="sec">
        <h4 className="sec-head">
          <span className="sec-t">Related passages</span>
          <span className="lsj-badge">TSK</span>
        </h4>
        {loading ? (
          <div className="lib-loading">Loading…</div>
        ) : refs.length === 0 ? (
          <p className="detail-p">No cross-references found.</p>
        ) : (
          <div className="xref-list">
            {refs.map(ref => (
              <div key={ref.ref} className="xref-verse" onClick={() => onNavigate(ref.book, ref.chapter, ref.verse)}>
                <span className="xref-ref">{ref.ref}</span>
                <p className="xref-text">{verseText(ref)}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  );

  return (
    <aside ref={isMobile ? sheetRef : null} className={"xref-panel " + (isMobile ? "detail-sheet" : "detail-side")} role="dialog" aria-label="Related Passages">
      {isMobile && <div className="sheet-drag-zone" aria-hidden="true"><div className="sheet-handle"></div></div>}
      <div className="detail-head">
        <div className="detail-head-l">
          <span className="detail-pos summary-pos">{heroRef}</span>
        </div>
        {overviewBack && !isMobile ? (
          <button className="detail-back" onClick={onClose} aria-label={"Back to " + backLabel.toLowerCase()}>‹ {backLabel}</button>
        ) : (
          <button className="detail-close" onClick={onClose} aria-label="Close"><Icon.Close/></button>
        )}
      </div>
      <div className="detail-body" ref={isMobile ? scrollRef : null}>{content}</div>
    </aside>
  );
}
