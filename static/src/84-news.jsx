// ============================================================
// NEWS WATCH — admin-only end-times news review (from news.db)
// Gathered + AI-scored offline by scripts/news/; this tab reviews the result.
//
// Three-zone shell (desktop ≥1100px): LEFT navigate (inbox/kept + threads +
// filters) · CENTER read (the feed cards, Keep/Dismiss ON the card) · RIGHT
// inspect (why the selected story scored — the scorer's per-article reasoning).
// Mobile (<1100px) collapses to the original single stacked column with the why
// shown inline on each card.
// ============================================================
function _newsDaysAgo(n) {
  return new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
}

// Empty-state mark for the inspect zone (newspaper), sized to match Word study's.
const NEWS_INSPECT_ICON = (
  <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 5h13a1 1 0 0 1 1 1v12a2 2 0 0 0 2 2H6a2 2 0 0 1-2-2V5Z"/>
    <path d="M18 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2"/>
    <path d="M8 8h6M8 12h6M8 16h4"/>
  </svg>
);

function _scoreTier(score) {
  return score >= 8 ? "hi" : score >= 6 ? "mid" : "lo";
}

function NewsStory({ story, view, onMark, readOnly, selected, onSelect }) {
  const [open, setOpen] = useState(false);
  const top = story.sources[0] || {};
  const tier = _scoreTier(story.score);
  const mark = (status, e) => { if (e) e.stopPropagation(); if (!readOnly) onMark(story, status); };
  return (
    <div className={"news-story" + (selected ? " news-story-sel" : "")}
         onClick={() => onSelect && onSelect(story)}>
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
              <button className="news-srcmore"
                      onClick={(e) => { e.stopPropagation(); setOpen(o => !o); }}>
                +{story.count - 1} more {open ? "▲" : "▼"}
              </button>
            </>
          )}
        </div>
        {open && story.count > 1 && (
          <div className="news-sources">
            {story.sources.map((s, i) => (
              <a key={i} className="news-src" href={s.url} target="_blank" rel="noopener noreferrer"
                 onClick={(e) => e.stopPropagation()}>
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
                    onClick={(e) => mark("keep", e)}>Keep</button>
            <button className="news-btn news-dismiss" disabled={readOnly}
                    title={readOnly ? "Read-only" : "Hide it"}
                    onClick={(e) => mark("dismiss", e)}>Dismiss</button>
          </>
        ) : (
          <button className="news-btn" disabled={readOnly}
                  title={readOnly ? "Read-only" : "Back to the inbox"}
                  onClick={(e) => mark("new", e)}>Un-keep</button>
        )}
      </div>
    </div>
  );
}

// One article's reasoning row in the right inspect panel: its OWN score next to its
// OWN why sentence, so the number always matches the words.
function NewsRatRow({ m, label }) {
  const tier = _scoreTier(m.score);
  return (
    <div className="news-rat-row">
      <div className="news-rat-head">
        <span className={"news-rat-score news-score-" + tier}>{m.score}</span>
        <div className="news-rat-headtext">
          {label && <span className="news-rat-label">{label}</span>}
          <span className="news-rat-thread">{m.thread_label}</span>
        </div>
      </div>
      {m.why && <div className="news-rat-why">{m.why}</div>}
      <div className="news-rat-src">
        <a href={m.url || "#"} target="_blank" rel="noopener noreferrer">{m.source}</a>
        <span className="news-rat-date">{m.published || "—"}</span>
      </div>
    </div>
  );
}

// RIGHT zone: why the selected story scored. The card shows the cluster's PEAK
// score but the FACE article's headline — and those can be two different articles,
// so we surface both rows explicitly, plus the other sources by score.
function NewsRationale({ story }) {
  if (!story) return null;   // the unselected state is the shared <ZoneEmpty> in the inspect slot
  const members = story.members || [];
  const byId = (id) => members.find(m => m.id === id);
  const peak = byId(story.peak_id);
  const face = byId(story.face_id);
  const same = story.peak_id === story.face_id;
  const pinnedIds = new Set([story.peak_id, story.face_id]);
  const pinnedCount = same ? 1 : 2;
  const rest = members.filter(m => !pinnedIds.has(m.id)).slice(0, Math.max(0, 5 - pinnedCount));
  return (
    <div className="news-inspect-body">
      <div className="news-inspect-h">Why it scored</div>
      {peak && <NewsRatRow m={peak} label={same ? "Peak · headline" : "Peak score"} />}
      {!same && face && <NewsRatRow m={face} label="Headline shown" />}
      {rest.length > 0 && (
        <>
          <div className="news-inspect-sub">Other sources</div>
          {rest.map((m, i) => <NewsRatRow key={m.id || i} m={m} />)}
        </>
      )}
      {story.count > rest.length + pinnedCount && (
        <div className="news-inspect-more">+{story.count - rest.length - pinnedCount} more in this story</div>
      )}
    </div>
  );
}

function NewsView({ isMobile }) {
  const [meta, setMeta] = useState(null);
  const [stories, setStories] = useState(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("inbox");          // inbox | kept
  const [since, setSince] = useState(() => localStorage.getItem("lexica.news.since.v1") || _newsDaysAgo(21));
  const [minScore, setMinScore] = useState(() => Number(localStorage.getItem("lexica.news.min.v1") || 6));
  const [thread, setThread] = useState("");
  const [order, setOrder] = useState("score");        // score | date
  const [flash, setFlash] = useState("");
  const [selId, setSelId] = useState(null);           // ids[0] of the selected story (desktop inspect)

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
    if (selId === story.ids[0]) setSelId(null);
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

  const canReview = !!(meta && meta.can_write);
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
  const selected = (stories || []).find(s => s.ids[0] === selId) || null;

  // ---- shared bits used by both layouts ----
  const threadList = (
    <div className="news-rail-threads">
      <button className={"news-thread-item" + (thread === "" ? " on" : "")}
              onClick={() => setThread("")}>All threads</button>
      {Object.keys(labels).map(k => (
        <button key={k} className={"news-thread-item" + (thread === k ? " on" : "")}
                onClick={() => setThread(k)}>{labels[k]}</button>
      ))}
    </div>
  );

  const viewsToggle = (
    <div className="news-views">
      <button className={"seg-b" + (view === "inbox" ? " on" : "")} onClick={() => setView("inbox")}>Inbox</button>
      <button className={"seg-b" + (view === "kept" ? " on" : "")} onClick={() => setView("kept")}>
        Kept{counts.kept ? ` (${counts.kept})` : ""}
      </button>
    </div>
  );

  const inboxFilters = (
    <>
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
      <select className="news-thread-sel" value={order} onChange={e => setOrder(e.target.value)}>
        <option value="score">Top score</option>
        <option value="date">Newest</option>
      </select>
    </>
  );

  const feedInner = (
    loading || stories === null ? (
      // `stories === null` = no fetch has finished yet (load runs after meta arrives).
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
            <NewsStory key={s.ids[0] + "-" + i} story={s} view={view} onMark={mark}
                       readOnly={!canReview} selected={!isMobile && selected === s}
                       onSelect={isMobile ? null : setSel} />
          ))}
        </div>
      </>
    )
  );

  function setSel(story) { setSelId(story.ids[0]); }

  // ---------------- MOBILE: single stacked column (unchanged shape) -------------
  if (isMobile) {
    return (
      <div className="news-view">
        <div className="news-head">
          <h1 className="news-h1">News watch</h1>
          {meta.reviewer_name ? (
            <span className="news-asline" title="Keep/Dismiss are recorded under this reviewer">
              Reviewing as <strong>{meta.reviewer_name}</strong>
            </span>
          ) : null}
          {viewsToggle}
        </div>
        {view === "inbox" ? (
          <div className="news-filters">
            {inboxFilters}
            <select className="news-thread-sel" value={thread} onChange={e => setThread(e.target.value)}>
              <option value="">All threads</option>
              {Object.keys(labels).map(k => <option key={k} value={k}>{labels[k]}</option>)}
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
        {feedInner}
      </div>
    );
  }

  // ---------------- DESKTOP: the shared three-zone frame ------------------------
  const rail = (
    <div className="news-rail">
      {viewsToggle}
      {view === "inbox" && <div className="news-rail-filters">{inboxFilters}</div>}
      {view === "kept" && (
        <div className="news-rail-filters">
          <button className="news-btn news-keep" onClick={copyShortlist}
                  disabled={!stories || !stories.length}>Copy shortlist</button>
          {flash && <span className="news-flash">{flash}</span>}
        </div>
      )}
      <div className="news-rail-threadlabel">Threads</div>
      {threadList}
      {meta.reviewer_name ? (
        <div className="news-rail-asline" title="Keep/Dismiss are recorded under this reviewer">
          Reviewing as <strong>{meta.reviewer_name}</strong>
        </div>
      ) : null}
    </div>
  );

  return (
    <ThreeZone
      className="news-frame"
      rail={rail}
      center={<div className="news-feed">{feedInner}</div>}
      inspect={selected
        ? <NewsRationale story={selected} />
        : <ZoneEmpty icon={NEWS_INSPECT_ICON} title="No story selected"
            sub="Select a story to see why it scored against the two-beast framework." />}
    />
  );
}
