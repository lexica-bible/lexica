// ============================================================
// NEWS WATCH — admin-only end-times news review (from news.db)
// Gathered + AI-scored offline by scripts/news/; this tab reviews the result.
//
// Three-zone shell (desktop ≥1100px): LEFT navigate (inbox/kept/dismissed + threads +
// filters) · CENTER read (the feed cards, Keep/Dismiss ON the card) · RIGHT inspect
// (the feed-shape readout — "why the watch is pointed here today", FeedShape). Mobile
// (<1100px) collapses to the original single stacked column with the why shown inline.
// ============================================================
function _newsDaysAgo(n) {
  return new Date(Date.now() - n * 86400000).toISOString().slice(0, 10);
}

// How a triage action moves the three tab counts. The card LEAVES the current view and
// ENTERS the bucket its new status maps to ("clear" sends it back to inbox). Every card
// shown is in-window (the lists are window-scoped), so these in-window deltas are exact —
// and since the out-of-window set never moves, the all-time tallies shift by the SAME
// kept/dismissed deltas, leaving the "+N outside this window" footer steady.
function _countDeltas(view, status) {
  const dest = status === "keep" ? "kept"
             : status === "dismiss" ? "dismissed"
             : "inbox";   // "clear" / "new" => back to inbox
  const d = { inbox: 0, kept: 0, dismissed: 0 };
  if (view !== dest) {
    if (view in d) d[view] -= 1;
    if (dest in d) d[dest] += 1;
  }
  return d;
}

function _scoreTier(score) {
  return score >= 8 ? "hi" : score >= 6 ? "mid" : "lo";
}

// Drop a trailing " - Outlet" / " — Outlet" suffix (the source already shows in the
// peak/headline rows below, so the panel header needn't repeat it). Mirrors the
// grouping's _sig_tokens strip. Only peels a single trailing segment.
function _stripOutlet(title) {
  return (title || "").replace(/\s+[-–—]\s+[^-–—]+$/, "").trim() || (title || "");
}

function NewsStory({ story, view, onMark, readOnly }) {
  const [open, setOpen] = useState(false);
  const top = story.sources[0] || {};
  const tier = _scoreTier(story.score);
  const mark = (status, e) => { if (e) e.stopPropagation(); if (!readOnly) onMark(story, status); };
  return (
    <div className="news-story">
      <div className={"news-score news-score-" + tier}>{story.score}</div>
      <div className="news-body">
        <div className="news-thread">{story.thread_label}</div>
        <a className="news-title" href={story.url || top.url || "#"} target="_blank" rel="noopener noreferrer">
          {_stripOutlet(story.title)}
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
          // Kept/Dismissed: clear back to inbox (recover a misclick) + flip to the other
          // state. "clear" deletes the row so the card re-surfaces in inbox at its normal
          // score/recency spot — it's just unreviewed again.
          <>
            <button className="news-btn" disabled={readOnly}
                    title={readOnly ? "Read-only" : "Back to the inbox"}
                    onClick={(e) => mark("clear", e)}>Back to Inbox</button>
            {view === "kept" ? (
              <button className="news-btn news-fill" disabled={readOnly}
                      title={readOnly ? "Read-only" : "Move to dismissed"}
                      onClick={(e) => mark("dismiss", e)}>Dismiss</button>
            ) : (
              <button className="news-btn news-keep" disabled={readOnly}
                      title={readOnly ? "Read-only" : "Move to kept"}
                      onClick={(e) => mark("keep", e)}>Keep</button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// RIGHT zone: "why the watch is pointed here today" — a feed-level readout computed
// from the already-scored rows (no model call, served by /api/news/shape). Replaces the
// old per-card rationale (which just echoed the card). Shows by default, no selection.
// The BURIED count is the hero: the stories the scorer looked at and held back — the one
// thing here you can't get by scrolling the feed.
function FeedShape({ shape }) {
  if (!shape) return <div className="news-shape news-shape-loading">Reading the feed…</div>;
  const threads = (shape.threads || []).filter(t => t.surfaced > 0).slice(0, 6);
  const maxSurf = Math.max(1, ...threads.map(t => t.surfaced));
  const clusters = shape.clusters || [];
  return (
    <div className="news-shape">
      <div className="news-shape-head">Today's watch</div>
      <div className="news-shape-body">
        <div className="news-shape-tally">
          <div className="news-shape-buried">
            <span className="news-shape-bignum">{shape.buried}</span>
            <span className="news-shape-biglbl">buried by the scorer</span>
          </div>
          <div className="news-shape-sub">
            {shape.surfaced} surfaced · {shape.total} scored
            {shape.new_angles ? <> · {shape.new_angles} new {shape.new_angles === 1 ? "angle" : "angles"}</> : null}
          </div>
        </div>

        {threads.length > 0 && (
          <div className="news-shape-sec">
            <div className="news-shape-h">Hot threads</div>
            {threads.map(t => (
              <div key={t.thread || "?"} className="news-shape-row">
                <span className="news-shape-tlabel" title={t.label}>{t.label}</span>
                <span className="news-shape-bar">
                  <span className="news-shape-fill" style={{ width: (100 * t.surfaced / maxSurf) + "%" }} />
                </span>
                <span className="news-shape-n">{t.surfaced}</span>
              </div>
            ))}
          </div>
        )}

        {clusters.length > 0 && (
          <div className="news-shape-sec">
            <div className="news-shape-h">Biggest stories</div>
            {clusters.map((c, i) => (
              <div key={i} className="news-shape-crow">
                <span className="news-shape-cev">{c.event}</span>
                <span className="news-shape-cn">{c.n}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function NewsView({ isMobile }) {
  const [meta, setMeta] = useState(null);
  const [stories, setStories] = useState(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("inbox");          // inbox | kept
  const [since, setSince] = useState(() => localStorage.getItem("lexica.news.since.v1") || _newsDaysAgo(21));
  const [minScore, setMinScore] = useState(() => Number(localStorage.getItem("lexica.news.min.v1") || 5));
  const [thread, setThread] = useState("");
  const [order, setOrder] = useState("score");        // score | date
  const [flash, setFlash] = useState("");
  const [shape, setShape] = useState(null);           // feed-shape readout for the right zone
  const [counts, setCounts] = useState({});           // Kept badge — server-seeded, then owned locally

  useEffect(() => { api.newsMeta().then(setMeta); }, []);
  // Reseed the three tab counts from the server for the CURRENT window (date + score +
  // thread) whenever any of those change; between reseeds, triage owns them locally (no
  // refetch, so the feed never tears down — see `mark`). Keyed on thread too so the badges
  // stay equal to the feed when a thread is picked. Deliberately NOT keyed on `order` — a
  // sort change must never recount (it only reorders the already-loaded list).
  useEffect(() => {
    if (!meta || !meta.available) return;
    let cancelled = false;
    const p = { min: minScore }; if (since) p.since = since; if (thread) p.thread = thread;
    api.newsCounts(p).then(d => { if (!cancelled && d && d.available) setCounts(d); });
    return () => { cancelled = true; };
  }, [meta, since, minScore, thread]);
  useEffect(() => { localStorage.setItem("lexica.news.since.v1", since); }, [since]);
  useEffect(() => { localStorage.setItem("lexica.news.min.v1", String(minScore)); }, [minScore]);

  // Feed-shape (right zone). Honors the Since window only — ignores score floor + thread,
  // so it's the whole-feed "why it's pointed here" readout, not the filtered view.
  useEffect(() => {
    if (!meta || !meta.available) { setShape(null); return; }
    let cancelled = false;
    const p = {}; if (since) p.since = since;
    api.newsShape(p).then(d => { if (!cancelled) setShape(d && d.available ? d : null); });
    return () => { cancelled = true; };
  }, [meta, since]);

  // Reload whenever a filter changes (kept queries ignore the date/score floor so the
  // shortlist always shows everything you've kept).
  useEffect(() => {
    if (!meta || !meta.available) return;
    let cancelled = false;
    setLoading(true);
    // Option 1: every view honors the date+score window, so a list always matches its tab
    // badge. (Kept/Dismissed used to ignore the window; the "+N outside this window" footer
    // keeps the rest discoverable.)
    const params = { view, order, min: minScore };
    if (since) params.since = since;
    if (thread) params.thread = thread;
    api.newsList(params).then(d => {
      if (cancelled) return;
      setStories(d.stories || []);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [meta, view, minScore, thread, order, since]);

  // Apply (sign +1) or undo (sign -1) a triage move's deltas to all the tab counts. The
  // all-time kept/dismissed tallies move by the SAME kept/dismissed deltas (the card is
  // in-window), so the "+N outside" footer stays put.
  const applyCounts = (dd, sign) => setCounts(c => ({
    ...c,
    inbox: Math.max(0, (c.inbox || 0) + sign * dd.inbox),
    kept: Math.max(0, (c.kept || 0) + sign * dd.kept),
    dismissed: Math.max(0, (c.dismissed || 0) + sign * dd.dismissed),
    kept_all: Math.max(0, (c.kept_all || 0) + sign * dd.kept),
    dismissed_all: Math.max(0, (c.dismissed_all || 0) + sign * dd.dismissed),
  }));

  const mark = (story, status) => {
    // Optimistic: the card is leaving this view regardless, so drop it NOW and adjust the
    // tab counts locally — no refetch, so the feed never reloads/flashes.
    const idx = (stories || []).indexOf(story);
    const dd = _countDeltas(view, status);
    setStories(ss => (ss || []).filter(s => s !== story));
    applyCounts(dd, 1);
    // Fire the write in the background. newsStatus never rejects — it resolves
    // {ok:false} on failure. On failure, roll the card back to its spot + undo the
    // counts + flash; on success do nothing (the UI already matches).
    api.newsStatus(story.ids, status).then(d => {
      if (d && d.ok !== false) return;
      setStories(ss => {
        const a = (ss || []).slice();
        a.splice(Math.min(idx < 0 ? a.length : idx, a.length), 0, story);
        return a;
      });
      applyCounts(dd, -1);
      setFlash("Couldn't save — put it back. Try again.");
      setTimeout(() => setFlash(""), 3000);
    });
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
  const scoreOpts = [["", "All"], ["5", "5+"], ["6", "6+"], ["7", "7+"], ["8", "8+"], ["9", "9+"]];

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

  // Live count for a tab — shown once the counts have loaded (so even "(0)" reads, which
  // is the point: Inbox is one slice of a triaged whole). All three are window-scoped.
  const cnt = (k) => Number.isFinite(counts[k]) ? ` (${counts[k]})` : "";
  const viewsToggle = (
    <div className="news-views">
      <button className={"seg-b" + (view === "inbox" ? " on" : "")} onClick={() => setView("inbox")}>
        Inbox{cnt("inbox")}
      </button>
      <button className={"seg-b" + (view === "kept" ? " on" : "")} onClick={() => setView("kept")}>
        Kept{cnt("kept")}
      </button>
      <button className={"seg-b" + (view === "dismissed" ? " on" : "")} onClick={() => setView("dismissed")}>
        Dismissed{cnt("dismissed")}
      </button>
    </div>
  );

  // Inbox filter controls, split so the desktop rail can group + label them while
  // the mobile strip keeps them in one flat row.
  const dateInput = <input type="date" value={since} onChange={e => setSince(e.target.value)} />;
  // Each preset is just another view of `since` — tapping one sets the field, and the
  // one whose date equals the current field renders active. A custom date matches none
  // (then nothing shows active — correct, the user is on their own window).
  const datePresets = [[7, "7d"], [14, "14d"], [30, "30d"], [90, "90d"], [365, "1y"]];
  const presets = (
    <div className="news-presets">
      {datePresets.map(([n, lbl]) => {
        const d = _newsDaysAgo(n);
        return (
          <button key={n} className={since === d ? "on" : ""}
                  onClick={() => setSince(d)}>{lbl}</button>
        );
      })}
    </div>
  );
  const scoreSeg = (
    <div className="news-seg news-score-seg">
      {scoreOpts.map(([v, lbl]) => (
        <button key={v} className={"seg-b" + (String(minScore || "") === v ? " on" : "")}
                onClick={() => setMinScore(Number(v || 0))}>{lbl}</button>
      ))}
    </div>
  );
  const sortSel = (
    <select className="news-thread-sel" value={order} onChange={e => setOrder(e.target.value)}>
      <option value="score">Top stories</option>
      <option value="date">Newest</option>
    </select>
  );
  const inboxFilters = (   // mobile: one flat strip (keeps the inline "Since" word)
    <>
      <label className="news-f"><span>Since</span>{dateInput}</label>
      {presets}
      {scoreSeg}
      {sortSel}
    </>
  );

  // "+N outside this window" — all-time kept/dismissed minus what's in the current window.
  // Both halves come from /api/news/counts, so it's cheap; only the active view's number
  // is shown (the lists are window-scoped now, so this keeps the all-time set discoverable).
  const keptOutside = Math.max(0, (counts.kept_all || 0) - (counts.kept || 0));
  const dismissedOutside = Math.max(0, (counts.dismissed_all || 0) - (counts.dismissed || 0));
  const outsideN = view === "kept" ? keptOutside : view === "dismissed" ? dismissedOutside : 0;

  const feedInner = (
    loading || stories === null ? (
      // `stories === null` = no fetch has finished yet (load runs after meta arrives).
      <div className="news-empty">Loading…</div>
    ) : !stories.length ? (
      <div className="news-empty">
        {view === "kept"
          ? (keptOutside > 0
              ? `Nothing kept in this window — +${keptOutside} outside. Widen the date to see them.`
              : "Nothing kept yet.")
          : view === "dismissed"
          ? (dismissedOutside > 0
              ? `Nothing dismissed in this window — +${dismissedOutside} outside. Widen the date to see them.`
              : "Nothing dismissed yet.")
          : "No stories match — try an earlier date or a lower score."}
      </div>
    ) : (
      <>
        <div className="news-count">
          {view === "inbox"
            ? `${stories.length} to review`
            : `${stories.length} ${stories.length === 1 ? "story" : "stories"}`}
        </div>
        <div className="news-list">
          {stories.map((s, i) => (
            <NewsStory key={s.ids[0] + "-" + i} story={s} view={view} onMark={mark}
                       readOnly={!canReview} />
          ))}
        </div>
        {outsideN > 0 && (
          <div className="news-outside">
            +{outsideN} {view === "kept" ? "kept" : "dismissed"} outside this window — widen the date to see all.
          </div>
        )}
      </>
    )
  );

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
            {view === "kept" && (   // shortlist-copy belongs with Kept, not Dismissed
              <button className="news-btn news-keep" onClick={copyShortlist}
                      disabled={!stories || !stories.length}>Copy shortlist</button>
            )}
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
      <div className="news-rail-sec">
        <div className="news-rail-label">View</div>
        {viewsToggle}
      </div>
      {view === "inbox" ? (
        <>
          <div className="news-rail-sec">
            <div className="news-rail-label">Since</div>
            <label className="news-f">{dateInput}</label>
            {presets}
          </div>
          <div className="news-rail-sec">
            <div className="news-rail-label">Score</div>
            {scoreSeg}
          </div>
          <div className="news-rail-sec">
            <div className="news-rail-label">Sort</div>
            {sortSel}
          </div>
        </>
      ) : view === "kept" ? (   // shortlist-copy belongs with Kept, not Dismissed
        <div className="news-rail-sec">
          <button className="news-btn news-keep" onClick={copyShortlist}
                  disabled={!stories || !stories.length}>Copy shortlist</button>
          {flash && <span className="news-flash">{flash}</span>}
        </div>
      ) : null}
      <div className="news-rail-sec">
        <div className="news-rail-label">Threads</div>
        {threadList}
      </div>
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
      inspect={<FeedShape shape={shape} />}
    />
  );
}
