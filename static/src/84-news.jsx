// ============================================================
// NEWS WATCH — admin-only end-times news review (from news.db)
// Gathered + AI-scored offline by scripts/news/; this tab reviews the result.
// ============================================================
function _newsDaysAgo(n) {
  return new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
}

function NewsStory({ story, view, onMark, readOnly }) {
  const [open, setOpen] = useState(false);
  const top = story.sources[0] || {};
  const tier = story.score >= 8 ? "hi" : story.score >= 6 ? "mid" : "lo";
  return (
    <div className="news-story">
      <div className={"news-score news-score-" + tier}>{story.score}</div>
      <div className="news-body">
        <div className="news-thread">{story.thread_label}</div>
        <a className="news-title" href={story.url || top.url || "#"} target="_blank" rel="noopener noreferrer">
          {story.title}
        </a>
        {story.why && <div className="news-why">{story.why}</div>}
        <div className="news-meta-line">
          <span>{top.source || "?"}</span>
          <span>·</span>
          <span>{story.published || "—"}</span>
          {story.count > 1 && (
            <>
              <span>·</span>
              <button className="news-srcmore" onClick={() => setOpen(o => !o)}>
                +{story.count - 1} more {open ? "▲" : "▼"}
              </button>
            </>
          )}
        </div>
        {open && story.count > 1 && (
          <div className="news-sources">
            {story.sources.map((s, i) => (
              <a key={i} className="news-src" href={s.url} target="_blank" rel="noopener noreferrer">
                {s.source} <span className="news-src-date">{s.published}</span>
              </a>
            ))}
          </div>
        )}
      </div>
      <div className="news-actions">
        {view === "inbox" ? (
          <>
            <button className="news-btn news-keep" disabled={readOnly}
                    title={readOnly ? "Read-only" : "Keep for the episode"}
                    onClick={() => !readOnly && onMark(story, "keep")}>Keep</button>
            <button className="news-btn news-dismiss" disabled={readOnly}
                    title={readOnly ? "Read-only" : "Hide it"}
                    onClick={() => !readOnly && onMark(story, "dismiss")}>Dismiss</button>
          </>
        ) : (
          <button className="news-btn" disabled={readOnly}
                  title={readOnly ? "Read-only" : "Back to the inbox"}
                  onClick={() => !readOnly && onMark(story, "new")}>Un-keep</button>
        )}
      </div>
    </div>
  );
}

function NewsView() {
  const [meta, setMeta] = useState(null);
  const [stories, setStories] = useState(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("inbox");          // inbox | kept
  const [since, setSince] = useState(() => localStorage.getItem("lexica.news.since.v1") || _newsDaysAgo(21));
  const [minScore, setMinScore] = useState(() => Number(localStorage.getItem("lexica.news.min.v1") || 6));
  const [thread, setThread] = useState("");
  const [order, setOrder] = useState("score");        // score | date
  const [flash, setFlash] = useState("");

  useEffect(() => { api.newsMeta().then(setMeta); }, []);
  useEffect(() => { localStorage.setItem("lexica.news.since.v1", since); }, [since]);
  useEffect(() => { localStorage.setItem("lexica.news.min.v1", String(minScore)); }, [minScore]);

  // Reload whenever a filter changes (kept queries ignore the date/score floor so the
  // shortlist always shows everything you've kept).
  useEffect(() => {
    if (!meta || !meta.available) return;
    let cancelled = false;
    setLoading(true);
    const params = { view, order };
    if (view === "inbox") {
      params.min = minScore;
      if (since) params.since = since;
    }
    if (thread) params.thread = thread;
    api.newsList(params).then(d => {
      if (cancelled) return;
      setStories(d.stories || []);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [meta, view, minScore, thread, order, since]);

  const mark = (story, status) => {
    api.newsStatus(story.ids, status);
    setStories(ss => (ss || []).filter(s => s !== story));   // drop it from the current list
  };

  const copyShortlist = () => {
    const lines = (stories || []).map(s => {
      const src = s.sources[0] || {};
      return `${s.title}\n  ${src.source || ""} · ${s.published} · score ${s.score} · ${s.thread_label}\n  ${s.why}\n  ${src.url || ""}`;
    });
    navigator.clipboard.writeText(lines.join("\n\n")).then(
      () => { setFlash("Copied " + (stories || []).length + " stories"); setTimeout(() => setFlash(""), 2000); },
      () => { setFlash("Copy failed"); setTimeout(() => setFlash(""), 2000); }
    );
  };

  const isAdmin = !!(meta && meta.owner);
  const canRead = !!(meta && (meta.owner || meta.reader));
  if (!meta) return <div className="news-view"><div className="news-empty">Loading…</div></div>;
  if (!canRead) return <div className="news-view"><div className="news-empty">Not available.</div></div>;
  if (!meta.available) return (
    <div className="news-view">
      <h1 className="news-h1">News watch</h1>
      <div className="news-empty">No <code>news.db</code> yet. Run the gatherer + scorer on the server first.</div>
    </div>
  );

  const labels = meta.labels || {};
  const counts = meta.counts || {};
  const scoreOpts = [["", "All"], ["6", "6+"], ["7", "7+"], ["8", "8+"], ["9", "9+"]];

  return (
    <div className="news-view">
      <div className="news-head">
        <h1 className="news-h1">News watch</h1>
        <div className="news-views">
          <button className={"seg-b" + (view === "inbox" ? " on" : "")} onClick={() => setView("inbox")}>Inbox</button>
          <button className={"seg-b" + (view === "kept" ? " on" : "")} onClick={() => setView("kept")}>
            Kept{counts.kept ? ` (${counts.kept})` : ""}
          </button>
        </div>
      </div>

      {view === "inbox" ? (
        <div className="news-filters">
          <label className="news-f">
            <span>Since</span>
            <input type="date" value={since} onChange={e => setSince(e.target.value)} />
          </label>
          <div className="news-presets">
            <button onClick={() => setSince(_newsDaysAgo(7))}>7d</button>
            <button onClick={() => setSince(_newsDaysAgo(14))}>14d</button>
            <button onClick={() => setSince(_newsDaysAgo(30))}>30d</button>
          </div>
          <div className="news-seg news-score-seg">
            {scoreOpts.map(([v, lbl]) => (
              <button key={v} className={"seg-b" + (String(minScore || "") === v ? " on" : "")}
                      onClick={() => setMinScore(Number(v || 0))}>{lbl}</button>
            ))}
          </div>
          <select className="news-thread-sel" value={thread} onChange={e => setThread(e.target.value)}>
            <option value="">All threads</option>
            {Object.keys(labels).map(k => <option key={k} value={k}>{labels[k]}</option>)}
          </select>
          <select className="news-thread-sel" value={order} onChange={e => setOrder(e.target.value)}>
            <option value="score">Top score</option>
            <option value="date">Newest</option>
          </select>
        </div>
      ) : (
        <div className="news-filters">
          <button className="news-btn news-keep" onClick={copyShortlist}
                  disabled={!stories || !stories.length}>Copy shortlist</button>
          <select className="news-thread-sel" value={thread} onChange={e => setThread(e.target.value)}>
            <option value="">All threads</option>
            {Object.keys(labels).map(k => <option key={k} value={k}>{labels[k]}</option>)}
          </select>
          {flash && <span className="news-flash">{flash}</span>}
        </div>
      )}

      {loading || stories === null ? (
        // `stories === null` = no fetch has finished yet. The stories load runs in an
        // effect AFTER meta arrives, so the first render with meta has loading=false +
        // stories=null — without this guard it flashed "No stories match" before the
        // list arrived (paint-before-ready). Treat not-yet-loaded as still loading.
        <div className="news-empty">Loading…</div>
      ) : !stories.length ? (
        <div className="news-empty">
          {view === "kept" ? "Nothing kept yet." : "No stories match — try an earlier date or a lower score."}
        </div>
      ) : (
        <>
          <div className="news-count">{stories.length} stories</div>
          <div className="news-list">
            {stories.map((s, i) => (
              <NewsStory key={s.ids[0] + "-" + i} story={s} view={view} onMark={mark} readOnly={!isAdmin} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
