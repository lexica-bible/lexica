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
// Today, ISO YYYY-MM-DD — the export filename + Markdown header date.
function _newsToday() {
  return new Date().toISOString().slice(0, 10);
}

// The feed-shape "surfaced vs buried" line. FIXED analytic threshold — the scorer's
// over-catch boundary (noise sits below 6), ported verbatim from the server's shape().
// It is NOT the score floor (minScore, default 5) and must NEVER be coupled to it.
const _SURFACE_SCORE = 6;

// Is a single date inside the window? Used per-MEMBER now (not per-card): an active window
// is judged against each article's own publish day, so a card is pulled in by the coverage
// that actually overlaps the window — never by the cluster's old busy day. Empty since/until
// = open on that side (since="" is the Max preset).
function _inWindow(d0, since, until) {
  const d = (d0 || "").slice(0, 10);
  if (!since && !until) return true;
  if (!d) return false;
  if (since && d < since) return false;
  if (until && d > until) return false;
  return true;
}

// Busiest day among the given members (most coverage; same-count tie broken by summed score,
// then toward the EARLIER day) — the client port of the server's _peak_date, but run over an
// arbitrary subset so a windowed card ages from its IN-WINDOW burst, not a global one.
function _peakDay(members) {
  const byDay = {};
  for (const m of members) {
    const d = (m.d || "").slice(0, 10);
    if (!d) continue;
    const cur = byDay[d] || [0, 0];
    byDay[d] = [cur[0] + 1, cur[1] + (m.s || 0)];
  }
  let best = null;
  for (const d of Object.keys(byDay).sort()) {     // ascending -> earliest wins a tie
    const [cnt, ssum] = byDay[d];
    if (!best || cnt > best[1] || (cnt === best[1] && ssum > best[2])) best = [d, cnt, ssum];
  }
  return best ? best[0] : "";
}

// Recompute a card for the active date window over ONLY its in-window members. Returns the
// windowed card, or null if it doesn't belong in this window. One date stops doing two jobs:
//   - the GATE is per-member and floor-aware — the card is in only if some in-window article
//     CLEARS THE FLOOR itself (so an old-loud card with one fresh WEAK straggler can't leak
//     back in and sit there with its loud old face — the reverse-staleness bug);
//   - everything DISPLAYED (face, score, date, sources) is taken from the in-window members,
//     so a card included on fresh strength also SHOWS its fresh face, never the stale one.
// No active window (Max preset) -> the global card, floored on its all-time peak (unchanged).
function _windowCard(c, since, until, minScore, thread, labels) {
  if (thread && c.thread !== thread) return null;
  if (!since && !until) {
    if (c.score < minScore) return null;
    // Max preset: the server _pick_face already applied the free-first penalty, so the
    // face is paywalled ONLY when every member is (the wholly-paywalled fallback). Derive
    // face_pw from the member flags — no domain check, no url join.
    const all = c.members || [];
    return { ...c, face_pw: all.length > 0 && all.every(m => !!m.pw) };
  }
  const mem = (c.members || []).filter(m => _inWindow(m.d, since, until));
  if (!mem.some(m => m.s >= minScore)) return null;          // floor judged in-window
  // free-first (m.pw = server paywall flag), then score, then recency — mirrors the
  // server _pick_face penalty so a windowed card never fronts a dead-end paywalled link
  // when a free sibling covers the same story. The check itself stays server-side.
  const _faceBetter = (m, b) => {
    if (!!m.pw !== !!b.pw) return !m.pw;                 // free beats paywalled
    if (m.s !== b.s) return m.s > b.s;                   // then strongest
    return (m.d || "") > (b.d || "");                    // then newer
  };
  const face = mem.reduce((b, m) => _faceBetter(m, b) ? m : b, mem[0]);
  const score = mem.reduce((mx, m) => Math.max(mx, m.s), 0);
  const dates = mem.map(m => (m.d || "").slice(0, 10)).filter(Boolean).sort();
  const seen = new Set(), sources = [];
  for (const m of mem.slice().sort((a, b) => (b.d || "").localeCompare(a.d || ""))) {
    const s = m.src || "?";
    if (seen.has(s)) continue;
    seen.add(s);
    sources.push({ source: s, url: m.url, published: (m.d || "").slice(0, 10) });
  }
  return {
    ...c,
    title: face.title, url: face.url, resolved_url: face.resolved || "", why: face.why, summary: face.summary || "",
    thread: face.t, thread_label: labels[face.t] || face.t || "?",
    face_pw: !!face.pw,                                 // the CURRENTLY selected face's paywall flag
    score, peak_date: _peakDay(mem),
    published: dates.length ? dates[dates.length - 1] : (c.published || ""),
    count: mem.length, sources: sources.slice(0, 12),
  };
}

// Recency dock, ported from the server's _staleness_penalty (GRACE=2, RATE=0.1, CAP=2.0),
// keyed off the cluster's PEAK day so a stale event with a fresh straggler can't dodge it.
function _stale(peak) {
  const d = (peak || "").slice(0, 10);
  if (!d) return 0;
  const pd = Date.parse(d + "T00:00:00Z");
  if (isNaN(pd)) return 0;
  const t = new Date();
  const today = Date.UTC(t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate());
  const age = Math.round((today - pd) / 86400000);
  return Math.min(2.0, Math.max(0, (age - 2) * 0.1));
}

function _scoreTier(score) {
  return score >= 8 ? "hi" : score >= 6 ? "mid" : "lo";
}

// The ONE 🔒 marker for a hard-paywalled article (a dead-end link for a reader). Driven
// PURELY by the server `pw` flag — the frontend never checks a domain. A missing/false flag
// renders nothing (unknown is never treated as paywalled). Shared by the card headline, the
// rail headline, and the rail sibling rows so their markup can't drift.
function _lock(pw) {
  if (!pw) return null;
  return <span className="news-lock" title="Paywalled — this link may not open the full article"
               aria-label="Paywalled">🔒</span>;
}

// Drop a trailing " - Outlet" / " — Outlet" suffix (the source already shows in the
// peak/headline rows below, so the panel header needn't repeat it). Mirrors the
// grouping's _sig_tokens strip. Only peels a single trailing segment.
function _stripOutlet(title) {
  return (title || "").replace(/\s+[-–—]\s+[^-–—]+$/, "").trim() || (title || "");
}

// Clean a LOCAL copy of an article's RSS summary for the "Title + description + link" copy
// format ONLY — never mutates the stored summary. RSS summaries are unreliable: many feeds
// echo the headline (sometimes + the source name), and some append boilerplate ("The post
// <title> first appeared on <source>."). Strip those tails, then drop the line entirely when
// what's left is just the title again.
function cleanDescription(title, summary) {
  if (!summary) return "";
  let s = summary
    .replace(/\s*The post .*? first appeared on .*?\.?\s*$/i, "")
    .replace(/\s*This (post|article|entry) (first )?appeared on .*?\.?\s*$/i, "")
    .trim();
  if (!s) return "";
  const norm = (x) => x.toLowerCase().normalize("NFKC")
    .replace(/[^\p{L}\p{N}\s]/gu, "")   // drop punctuation, keep Unicode letters (Cyrillic/Greek)
    .replace(/\s+/g, " ").trim();
  const nt = norm(title), nd = norm(s);
  if (nd === nt) return "";                              // exact echo
  if (nt && nd.startsWith(nt)) {                         // title + a short source-name echo
    const tail = nd.slice(nt.length).trim();
    if (tail.length <= 60) return "";
  }
  return s;
}

// ============================================================
// Shortlist assembly — the ONE layer both clipboard copy AND file export route through.
// Face-field resolution + cleanDescription live HERE and nowhere else; every format below
// draws from _shortlistFace, so changing the format logic changes it in one place.
// ============================================================

// The FACE article's own outlet, matched in members by url — NOT sources[0] (the newest-dated
// outlet, a different article). Shared by the card meta line + copy/export so they can't drift.
function _faceSource(s) {
  const face = (s.members || []).find(m => m.url === s.url) || {};
  return face.src || ((s.sources || [])[0] || {}).source || "";
}

// The link a card/article opens on click: the REAL decoded article when known (resolved_url,
// same field copy reads), else the stored `url` — which is a Google News wrapper for the
// not-yet-resolved faces and still lands the reader on the article via Google's redirect.
// So the click is always direct-when-known, never dead. Matches copy's face-URL resolution.
function _faceLink(s) {
  return s.resolved_url || s.url || "";
}

// The values every format reads, resolved from ONE article per card (the FACE — the headline
// the card shows). `date` matches the card (peak, else latest).
function _shortlistFace(s) {
  return {
    title: s.title || "",
    url: s.url || "",
    summary: s.summary || "",                              // RAW (CSV keeps it; text formats clean it)
    date: (s.peak_date || s.published || "").slice(0, 10),
    score: Number.isFinite(s.score) ? s.score : "",
    thread: s.thread_label || "",
    source: _faceSource(s),
  };
}

// The three clipboard TEXT formats (behavior unchanged — copy still routes through these).
// `url` is already the resolved link. A blank date/description drops its own line.
function _plainFormat(fmt, f, url) {
  if (fmt === "titlelink") return [f.title, f.date, url].filter(Boolean).join("\n");
  const desc = cleanDescription(f.title, f.summary);       // titledesc
  return [f.title, ...(desc ? ["— " + desc] : []), f.date, url].filter(Boolean).join("\n");
}

// Markdown — the richest, human-readable "keep it" form. H1 + count header, then one H2 entry
// per item: title (plain, not linked), a "·"-joined meta line, the cleaned description, the url.
function _markdownFormat(faces, rurl, today) {
  const entries = faces.map(f => {
    const meta = [f.date, f.thread, f.score !== "" ? "score " + f.score : "", f.source]
      .filter(Boolean).join("  ·  ");
    const desc = cleanDescription(f.title, f.summary);
    return ["## " + f.title, meta, ...(desc ? ["— " + desc] : []), rurl(f.url)]
      .filter(Boolean).join("\n");
  });
  const n = faces.length;
  return `# Lexica news shortlist — ${today}\n${n} ${n === 1 ? "article" : "articles"}\n\n`
    + entries.join("\n\n") + "\n";
}

// CSV — archival/data view. RFC-4180 (quote every field, double embedded quotes), \r\n lines,
// UTF-8 BOM so Excel renders Cyrillic/Greek. description = RAW summary (NOT cleaned — data truth).
function _csvFormat(faces, rurl) {
  const q = (v) => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
  const rows = [["date", "thread", "score", "title", "source", "url", "description"]];
  for (const f of faces)
    rows.push([f.date, f.thread, f.score, f.title, f.source, rurl(f.url), f.summary]);
  const BOM = String.fromCharCode(0xFEFF);
  return BOM + rows.map(r => r.map(q).join(",")).join("\r\n") + "\r\n";
}

// Trigger a browser download of `text` as `filename`.
function _downloadFile(filename, text, mime) {
  const blob = new Blob([text], { type: mime });
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
}

// The card date shows the PEAK day only (rank + window both key on it). A single-date
// event already collapses to that one date, so this is just "{peak}" — the old
// "· latest Y" half is dropped (it added a second date that rarely earned the room).
function _dateRange(story) {
  const peak = (story.peak_date || "").slice(0, 10);
  const latest = (story.published || "").slice(0, 10);
  return peak || latest || "—";
}

// Collapse member articles to ONE row per outlet, keeping each outlet's NEWEST article (its
// date + link) so a fresh follow-up beats the old burst instance, then sort the survivors
// newest-first. Undated articles lose to any dated one for their outlet and sort last (no
// date shown, never faked). The ≤~12-row deduped view, not the full per-article wall.
function _dedupByOutlet(members) {
  const best = new Map();
  for (const m of members || []) {
    const k = m.src || "?";
    const cur = best.get(k);
    if (!cur || (m.d || "") > (cur.d || "")) best.set(k, m);
  }
  return [...best.values()].sort((a, b) => {
    const da = a.d || "", db = b.d || "";
    if (da && db) return db < da ? -1 : db > da ? 1 : 0;   // descending = newest first
    return da ? -1 : db ? 1 : 0;                            // dated before undated
  });
}

// Default depth of the in-window citation list before the "show more sources" fold — even
// after dedup-by-outlet a mega-cluster has 100+ distinct outlets (genuine breadth, not dupes),
// so cap the visible rows and tuck the rest behind a fold like the out-of-window coverage.
const _SRC_DEPTH = 15;

// `isMobile` is here for ONE reason: a control that does nothing doesn't earn a 375px row.
// Below the mobile breakpoint a read-only viewer's Keep/Dismiss aren't rendered at all;
// above it they gray exactly as before (JP's desktop ruling — a grayed control + its
// tooltip teaches a reader what the feed is, and on a wide row that costs nothing).
// Same control, different cost, different answer. It's a breakpoint, not a new mode:
// readOnly is unchanged and still drives the desktop gray.
function NewsStory({ story, view, onMark, readOnly, since, until, onSelect, selected, isMobile }) {
  const top = story.sources[0] || {};
  const tier = _scoreTier(story.score);
  // A plain, non-interactive cluster-size signal (distinct outlets). The why + the full
  // per-outlet article list now live in the right rail on selection, not a card expander.
  const srcCount = new Set((story.members || []).map(m => m.src || "?")).size;
  // Meta line = date · face outlet · (N sources only when >1). Same face source as the inspect
  // panel / copy / export. If the face source is missing, fall back to date · N sources (no bare
  // dangling separator). Built as segments so the "·" gaps stay identical to the card-spacing pass.
  const faceSource = _faceSource(story);
  const metaSegs = [_dateRange(story)];
  if (faceSource) metaSegs.push(faceSource);
  if (srcCount > 1) metaSegs.push(srcCount + " sources");
  const mark = (status, e) => { if (e) e.stopPropagation(); if (!readOnly) onMark(story, status); };
  // Click the card BODY to inspect why it scored (the rail); the headline link and the
  // Keep/Dismiss buttons stop the bubble, so they keep their own action.
  const pick = onSelect ? () => onSelect(story) : undefined;
  // Dead controls on a phone row: the reader can't act, so the pair is pure cost — it
  // squeezes the headline column and buys nothing. The read-only signal moves to one
  // line at the top of the feed (see the mobile branch), where it costs no row width.
  const hideActions = readOnly && isMobile;
  return (
    <div className={"news-story listrow" + (onSelect ? " news-story--click" : "") + (selected ? " on" : "")}
         onClick={pick}>
      <div className={"news-score news-score-" + tier}>{story.score}</div>
      <div className="news-body">
        <div className="news-thread">{story.thread_label}</div>
        <a className="news-title" href={_faceLink(story) || top.url || "#"} target="_blank" rel="noopener noreferrer"
           onClick={(e) => e.stopPropagation()}>
          {_lock(story.face_pw)}{_stripOutlet(story.title)}
        </a>
        {/* Body = headline + thread + a date · outlet · source-count meta line. The why and the
            full per-outlet article list now render in the right rail on selection. */}
        <div className="news-meta-line">
          {metaSegs.map((seg, i) => (
            <React.Fragment key={i}>
              {i > 0 && <span>·</span>}
              <span>{seg}</span>
            </React.Fragment>
          ))}
        </div>
      </div>
      {hideActions ? null : (
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
      )}
    </div>
  );
}

// RIGHT zone: "why the watch is pointed here today" — a feed-level readout computed
// from the already-scored rows (no model call, served by /api/news/shape). Replaces the
// old per-card rationale (which just echoed the card). Shows by default, no selection.
// The BURIED count is the hero: the stories the scorer looked at and held back — the one
// thing here you can't get by scrolling the feed.
function FeedShape({ shape, onPick }) {
  if (!shape) return <div className="news-shape news-shape-loading">Reading the feed…</div>;
  const threads = (shape.threads || []).filter(t => t.surfaced > 0).slice(0, 6);
  const maxSurf = Math.max(1, ...threads.map(t => t.surfaced));
  const clusters = shape.clusters || [];
  return (
    <div className="news-shape">
      <div className="news-shape-head sh-band">Today's watch</div>
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
            {/* A real <button> (not a div+onClick) so it's keyboard- and screen-reader-reachable;
                it's styled to stay the same quiet row — the hover wash is the only affordance,
                per the no-decorative-containers rule. */}
            {clusters.map((c, i) => (
              <button key={i} className="news-shape-crow news-shape-crow--click"
                      onClick={() => onPick && onPick(c.id)}
                      title={"Why it surfaced: " + c.event}>
                <span className="news-shape-cev">{c.event}</span>
                <span className="news-shape-cn">{c.n}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// The watch's lens, verbatim from scripts/news/queries.py — the one storyline every
// article is scored against. It's GLOBAL (identical for every card), so it's stated ONCE in the
// ⓘ "How the feed works" popover, NOT repeated per card. Single source of truth for the string.
const _NEWS_LENS = "Manufactured crisis → a public cry for moral order → all authority (states, denominations, even tech and AI) consolidating under Rome, with America as the enforcer — the two-beasts endgame.";

// RIGHT zone, SELECTED state: click a story card → this replaces the feed-shape dashboard.
// Everything here is stored or authored, nothing generated at view time: the score + thread,
// the scorer's own one-line reason (ai_why, genuinely per-article), the sources + how each was
// pulled (Google News / RSS), and the cluster's article list. "‹ Watch" is the depth-1 reset
// back to the dashboard. (A per-thread beast-arm badge is a separate, authored follow-up.)
function NewsWhy({ story, onBack }) {
  const tier = _scoreTier(story.score);
  const members = story.members || [];
  // ONE deduped list: each outlet's newest article (title · outlet · date · via), newest-first.
  const arts = _dedupByOutlet(members);
  const peak = (story.peak_date || "").slice(0, 10);
  return (
    <div className="news-shape news-why">
      <div className="news-shape-head news-why-head sh-band">
        <span className="news-why-headt">Why it surfaced</span>
        <button className="detail-back" onClick={onBack}>‹ Watch</button>
      </div>
      <div className="news-shape-body">
        <div className="news-why-top">
          <div className={"news-score news-score-" + tier}>{story.score}</div>
          <div className="news-why-thread">{story.thread_label}</div>
        </div>
        <a className="news-why-title" href={_faceLink(story) || "#"} target="_blank" rel="noopener noreferrer">
          {_lock(story.face_pw)}{_stripOutlet(story.title)}
        </a>

        {story.why && (
          <div className="news-shape-sec">
            <div className="news-shape-h">Why it scored</div>
            <p className="news-why-reason">{story.why}</p>
          </div>
        )}

        {arts.length > 0 && (
          <div className="news-shape-sec">
            <div className="news-shape-h">
              {arts.length} {arts.length === 1 ? "source" : "sources"}{arts.length > 1 && peak ? " · peaked " + peak : ""}
            </div>
            {arts.map((m, i) => (
              <div key={i} className="news-why-art">
                <a className="news-why-artt" href={m.resolved || m.url || "#"} target="_blank" rel="noopener noreferrer"
                   onClick={(e) => e.stopPropagation()}>
                  {_lock(m.pw)}{_stripOutlet(m.title)}
                </a>
                <div className="news-why-artmeta">{m.src}{m.d ? " · " + m.d : ""}{m.via ? " · " + m.via : ""}</div>
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
  const [allCards, setAllCards] = useState(null);     // the full held set (one fetch)
  const [overrides, setOverrides] = useState({});     // local triage: cardKey -> status
  const [refreshN, setRefreshN] = useState(0);        // bump = re-pull (Refresh / new pull)
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("inbox");          // inbox | kept | dismissed
  // The date window's IDENTITY is a day COUNT (or a named key), NEVER a stored anchor date — an
  // anchor goes stale as the clock rolls (the "Last 7d → Last 8d" drift). windowKey is one of the
  // preset day-counts ("7".."365"), "max" (no bounds), or "custom" (the Since/Until fields). The
  // actual from/to bounds are computed FRESH every render from windowKey + today (see `since`/
  // `until` below), so the label AND the window stay correct across a refresh + the nightly tick.
  const [windowKey, setWindowKey] = useState(() => localStorage.getItem("lexica.news.wkey.v1") || "21");
  const [customSince, setCustomSince] = useState(() => localStorage.getItem("lexica.news.csince.v1") || "");
  const [customUntil, setCustomUntil] = useState(() => localStorage.getItem("lexica.news.cuntil.v1") || "");
  // Bounds derived at query time — never persisted. A preset = "last N days through now"; custom =
  // the two fields; max = no bounds. `_newsDaysAgo` reads the current date, so this can't go stale.
  const since = windowKey === "max" ? "" : windowKey === "custom" ? customSince : _newsDaysAgo(Number(windowKey));
  const until = windowKey === "custom" ? customUntil : "";   // presets + max have no upper bound
  const [minScore, setMinScore] = useState(() => Number(localStorage.getItem("lexica.news.min.v1") || 5));
  const [thread, setThread] = useState("");
  const [order, setOrder] = useState("score");        // score | date | oldest
  const [flash, setFlash] = useState("");
  const [copying, setCopying] = useState(false);      // Copy shortlist: resolving wrapper URLs
  const [copyOpen, setCopyOpen] = useState(false);    // Copy-shortlist format dropdown
  const [copiedN, setCopiedN] = useState(0);          // >0 = show "Copied n ✓" for ~1.5s
  const copyTimer = useRef(null);
  const [exportOpen, setExportOpen] = useState(false); // Export (file) format dropdown
  const [exported, setExported] = useState(false);     // show "Exported ✓" for ~1.5s
  const exportTimer = useRef(null);
  const [dateOpen, setDateOpen] = useState(false);    // desktop top-bar date popover
  const [helpOpen, setHelpOpen] = useState(false);    // top-bar "how the feed works" popover
  const [selStory, setSelStory] = useState(null);     // card selected into the why-rail (desktop) / Watch sheet (mobile)
  const [mSheet, setMSheet] = useState(null);         // mobile shell: null | "threads" | "watch" | "options"

  useEffect(() => { api.newsMeta().then(setMeta); }, []);
  useEffect(() => { localStorage.setItem("lexica.news.wkey.v1", windowKey); }, [windowKey]);
  useEffect(() => { localStorage.setItem("lexica.news.csince.v1", customSince); }, [customSince]);
  useEffect(() => { localStorage.setItem("lexica.news.cuntil.v1", customUntil); }, [customUntil]);
  useEffect(() => { localStorage.setItem("lexica.news.min.v1", String(minScore)); }, [minScore]);
  // Esc closes whichever export/copy menu is open (outside-click is the scrim). Clear the
  // done-flash timers on unmount.
  useEffect(() => {
    if (!copyOpen && !exportOpen) return;
    const onKey = (e) => { if (e.key === "Escape") { setCopyOpen(false); setExportOpen(false); } };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [copyOpen, exportOpen]);
  useEffect(() => () => {
    if (copyTimer.current) clearTimeout(copyTimer.current);
    if (exportTimer.current) clearTimeout(exportTimer.current);
  }, []);

  // The ONLY data fetch: pull the whole clustered feed once (and on an explicit Refresh or
  // reload). Every sort/filter/score/date/thread/count below is derived from it locally,
  // with no further server calls. `refreshN` is the manual force-refresh (also the way to
  // pick up a hand re-score — see the cache-boundary note in views_news.py).
  useEffect(() => {
    if (!meta || !meta.available) return;
    let cancelled = false;
    setLoading(true);
    api.newsAll().then(d => {
      if (cancelled) return;
      setAllCards(d && d.available ? (d.cards || []) : []);
      setOverrides({});           // a fresh pull = the server's status is the truth
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [meta, refreshN]);

  // Apply local triage overrides over the held set, so a Keep/Dismiss shows instantly
  // without a refetch (the card simply changes status and the filters below re-bucket it).
  const cards = useMemo(() => (allCards || []).map(c => {
    const k = c.ids[0];
    const st = (k in overrides) ? overrides[k] : c.status;
    return st === c.status ? c : { ...c, status: st };
  }), [allCards, overrides]);

  const labels = (meta && meta.labels) || {};

  // Every card recomputed for the active window — membership (gate + floor), face, score,
  // date and sources all over the in-window members (see _windowCard). The counts AND the
  // feed both read THIS one windowed view, so "why a card is in" and "what it shows" agree.
  const windowed = useMemo(() => cards
    .map(c => _windowCard(c, since, until, minScore, thread, labels))
    .filter(Boolean),
    [cards, since, until, minScore, thread, meta]);

  // Tab tallies — all derived, no server round-trip. Inbox = anything not kept/dismissed.
  // The all-time kept/dismissed totals stay thread-scoped but ignore the date window (so
  // "+N outside this window" means outside the DATE window, within the same thread).
  const counts = useMemo(() => {
    const o = { inbox: 0, kept: 0, dismissed: 0, kept_all: 0, dismissed_all: 0 };
    for (const c of cards) {            // all-time totals: thread-scoped, ignore window + floor
      const tOk = !thread || c.thread === thread;
      if (tOk && c.status === "keep") o.kept_all++;
      if (tOk && c.status === "dismiss") o.dismissed_all++;
    }
    for (const c of windowed) {         // in-window + floored + thread-scoped
      if (c.status === "keep") o.kept++;
      else if (c.status === "dismiss") o.dismissed++;
      else o.inbox++;
    }
    return o;
  }, [cards, windowed, thread]);

  // Article -> card collapse for the header label, in ONE pass over the SAME set the feed
  // shows: the active view's in-window floored cards, and the in-window articles AT THE FLOOR
  // that cluster into them. Both halves are window- and floor-scoped together, so the header
  // never pairs a no-floor article dump with a floored card count (the misread this fixes).
  // No floor (minScore 0) => every in-window article counts. Display only — reuses windowed.
  const collapse = useMemo(() => {
    const want = { inbox: "new", kept: "keep", dismissed: "dismiss" }[view];
    let articles = 0, cards = 0;
    for (const c of windowed) {
      const isInbox = c.status !== "keep" && c.status !== "dismiss";
      if (!(want === "new" ? isInbox : c.status === want)) continue;
      cards++;
      for (const m of (c.members || [])) {
        if (!_inWindow(m.d, since, until)) continue;
        if (minScore && m.s < minScore) continue;
        articles++;
      }
    }
    return { articles, cards };
  }, [windowed, view, since, until, minScore]);

  // The visible feed — filter the windowed view to the active tab, then sort. All client-side.
  const stories = useMemo(() => {
    const want = { inbox: "new", kept: "keep", dismissed: "dismiss" }[view];
    const list = windowed.filter(c => {
      const isInbox = c.status !== "keep" && c.status !== "dismiss";
      return want === "new" ? isInbox : c.status === want;
    });
    if (order === "date")
      // Newest by the event's PEAK day (not its latest straggler); stronger card wins a tie.
      list.sort((a, b) => (b.peak_date + "").localeCompare(a.peak_date + "") || b.score - a.score);
    else if (order === "oldest")
      list.sort((a, b) => (a.peak_date + "").localeCompare(b.peak_date + "") || b.score - a.score);
    else
      // Default: recency-weighted score (the dock keys off the peak day). Newest published
      // is the tie-break so equal effective scores still favor the fresher card.
      list.sort((a, b) => (b.score - _stale(b.peak_date)) - (a.score - _stale(a.peak_date))
                       || (b.published + "").localeCompare(a.published + ""));
    return list.slice(0, 300);
  }, [windowed, view, order]);

  // Feed-shape readout (right zone) — also derived. Honors the date window only (ignores
  // the score floor + thread, by design: the BURIED count is the whole point). Counts
  // ARTICLES by each member's OWN date in the window (not the card's peak day) — so the
  // recent strong articles parked under old-dated cards now show up in the surfaced count
  // instead of being swallowed. The surfaced line uses the FIXED _SURFACE_SCORE.
  const shape = useMemo(() => {
    if (!allCards || !cards.length) return null;
    let surfaced = 0, buried = 0, total = 0, newAngles = 0;
    const byT = {};
    const events = [];
    for (const c of cards) {
      const mem = (c.members || []).filter(m => _inWindow(m.d, since, until));
      if (!mem.length) continue;
      for (const m of mem) {
        total++;
        const hi = m.s >= _SURFACE_SCORE;
        hi ? surfaced++ : buried++;
        if (m.nf === 1) newAngles++;
        const k = m.t || "";
        const cur = byT[k] || { s: 0, sc: 0 };
        cur.s += hi ? 1 : 0; cur.sc++; byT[k] = cur;
      }
      // `id` carries the cluster back to its card so the row can be opened (see
      // openShapeCluster). The readout is built from `cards`, NOT `windowed` — deliberately,
      // since the buried count is the whole point — so an id here can name a card the feed's
      // own floor/thread filter is hiding. That's handled at the click, not by trimming here.
      events.push({ id: c.ids[0], event: c.event || c.title, n: mem.length,
                    hi: mem.reduce((mx, m) => Math.max(mx, m.s), 0) });
    }
    const threads = Object.keys(byT).map(t => ({
      thread: t, label: labels[t] || t || "?", surfaced: byT[t].s, scored: byT[t].sc
    })).sort((a, b) => b.surfaced - a.surfaced || b.scored - a.scored);
    const clusters = events.sort((a, b) => b.n - a.n).slice(0, 5);
    return { available: true, surfaced, buried, total, new_angles: newAngles, threads, clusters };
  }, [cards, since, until, meta]);

  const mark = (story, status) => {
    // Optimistic + local: flip the card's status, which drops it out of the current view via
    // the filter above — no refetch, so the feed never reloads/flashes. Fire the write in
    // the background; newsStatus resolves {ok:false} on failure → roll the override back.
    const k = story.ids[0];
    const prev = (k in overrides) ? overrides[k] : story.status;
    const next = status === "keep" ? "keep" : status === "dismiss" ? "dismiss" : "new";
    setOverrides(o => ({ ...o, [k]: next }));
    api.newsStatus(story.ids, status).then(d => {
      if (d && d.ok !== false) return;
      setOverrides(o => ({ ...o, [k]: prev }));
      setFlash("Couldn't save — put it back. Try again.");
      setTimeout(() => setFlash(""), 3000);
    });
  };

  // Swap a button label to its "done" state for ~1.5s; reset the timer on a repeat click.
  const flashCopied = (n) => {
    setCopiedN(n);
    if (copyTimer.current) clearTimeout(copyTimer.current);
    copyTimer.current = setTimeout(() => { setCopiedN(0); copyTimer.current = null; }, 1500);
  };
  const flashExported = () => {
    setExported(true);
    if (exportTimer.current) clearTimeout(exportTimer.current);
    exportTimer.current = setTimeout(() => { setExported(false); exportTimer.current = null; }, 1500);
  };

  // Resolve any Google News wrapper URLs (direct links need no round-trip), then hand the
  // {wrapper -> real} map to `done`. Shared by BOTH copy and export so neither emits a wrapper.
  const withResolvedUrls = (done) => {
    const wrappers = [...new Set((stories || []).map(s => s.url)
      .filter(u => u && u.includes("news.google.com/rss/articles/")))];
    if (!wrappers.length) { done(null); return; }
    setCopying(true);
    api.newsResolve(wrappers)
      .then(res => { setCopying(false); done(res && res.ok ? res.urls : null); })
      .catch(() => { setCopying(false); done(null); });   // fail-soft: raw wrappers
  };

  // The ONE assembler. Given a format key + the resolved-url map, builds the whole output from
  // the current shortlist. Every format (3 clipboard + md + csv) routes through here.
  const buildShortlist = (fmt, urlMap) => {
    const rurl = (u) => (urlMap && urlMap[u]) || u;
    const faces = (stories || []).filter(s => s.url).map(_shortlistFace);
    // Link only = bare URLs, one per line, single \n, no dates/titles, no trailing newline.
    if (fmt === "link") return faces.map(f => rurl(f.url)).join("\n");
    if (fmt === "md") return _markdownFormat(faces, rurl, _newsToday());
    if (fmt === "csv") return _csvFormat(faces, rurl);
    return faces.map(f => _plainFormat(fmt, f, rurl(f.url))).join("\n\n");   // titlelink|titledesc
  };

  // Copy the current shortlist in one of the three text formats (assembly shared with export).
  const doCopy = (fmt) => {
    setCopyOpen(false);
    if (copying || !(stories || []).some(s => s.url)) return;
    const n = (stories || []).filter(s => s.url).length;
    withResolvedUrls((map) => {
      navigator.clipboard.writeText(buildShortlist(fmt, map)).then(
        () => flashCopied(n),
        () => { setFlash("Copy failed"); setTimeout(() => setFlash(""), 2000); }
      );
    });
  };

  // Export the current shortlist to a downloaded .txt — the SAME string the "Link only"
  // copy puts on the clipboard (buildShortlist("link", …), byte-for-byte).
  const doExport = () => {
    if (copying || !(stories || []).some(s => s.url)) return;
    withResolvedUrls((map) => {
      _downloadFile(`lexica-news-${_newsToday()}.txt`, buildShortlist("link", map), "text/plain;charset=utf-8");
      flashExported();
    });
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

  // Live count for a tab — shown once the counts have loaded (so even "0" reads, which is
  // the point: Inbox is one slice of a triaged whole). No parens (thinner, fits the rail);
  // all three are window-scoped.
  const cnt = (k) => Number.isFinite(counts[k]) ? ` ${counts[k]}` : "";
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
  // Editing either field switches the window to "custom" and seeds BOTH bounds from the current
  // derived values, so tweaking one edge doesn't drop the other (e.g. narrowing a 7d preset).
  const enterCustom = (ns, nu) => { setCustomSince(ns); setCustomUntil(nu); setWindowKey("custom"); };
  const dateInput = <input type="date" value={since} onChange={e => enterCustom(e.target.value, until)} />;
  const untilInput = <input type="date" value={until} onChange={e => enterCustom(since, e.target.value)} />;
  // Each preset is a day-COUNT ("last N days through now"); windowKey stores the count as identity,
  // so the label never drifts and the bounds recompute from today. A preset highlights when its
  // count is the active windowKey (custom / max are their own keys).
  const datePresets = [[7, "7d"], [14, "14d"], [30, "30d"], [90, "90d"], [365, "1y"]];
  const presets = (
    <div className="news-presets">
      {datePresets.map(([n, lbl]) => (
        <button key={n} className={(windowKey === String(n)) ? "on" : ""}
                onClick={() => setWindowKey(String(n))}>{lbl}</button>
      ))}
      {/* Max = drop the date bounds entirely (windowKey "max" → since="" + until=""). */}
      <button key="max" className={(windowKey === "max") ? "on" : ""}
              onClick={() => setWindowKey("max")}>Max</button>
    </div>
  );
  // Score chips REUSE the date presets' style (`.news-presets`), they don't imitate it: same
  // base chip, same `.on` accent fill, one rule for both. They were `.seg-b`, whose selected
  // state is a WHITE pill (`--ctl-on`) — so on the Options sheet the selected score read white
  // while the 7d/14d chip right above it read accent, two different answers to "this one is
  // picked" in one sheet (JP, 2026-07-15). `.seg-b` is shared with Notes/Study/Library/the view
  // tabs, so its white pill is NOT ours to restyle — the fix is that score was wearing the
  // wrong class, not that the class is wrong. Mobile-only: the desktop strip uses `scoreSel`,
  // a plain dropdown, so it never had this divergence (checked).
  const scoreSeg = (
    <div className="news-presets news-score-seg">
      {scoreOpts.map(([v, lbl]) => (
        <button key={v} className={String(minScore || "") === v ? "on" : ""}
                onClick={() => setMinScore(Number(v || 0))}>{lbl}</button>
      ))}
    </div>
  );
  const sortSel = (
    <select className="news-thread-sel" value={order} onChange={e => setOrder(e.target.value)}>
      <option value="score">Top stories</option>
      <option value="date">Newest</option>
      <option value="oldest">Oldest</option>
    </select>
  );
  // Desktop top-bar compact controls: score as a plain dropdown (the 6-button segment is
  // mobile-only now), and a short label summarising the active date window for its popover
  // button ("Last 21d" / "All dates" / "Custom range").
  const scoreSel = (
    <select className="news-thread-sel" value={String(minScore || "")}
            onChange={e => setMinScore(Number(e.target.value || 0))}>
      {scoreOpts.map(([v, lbl]) => (
        <option key={v} value={v}>{v ? lbl + " score" : "Any score"}</option>
      ))}
    </select>
  );
  // Rendered straight from the count (the source of truth), so it CAN'T drift as the clock rolls.
  const dateLabel = windowKey === "max" ? "All dates"
    : windowKey === "custom" ? "Custom range"
    : "Last " + windowKey + "d";

  // Copy-shortlist: a dropdown (Link only / Title + link / Title + description + link). One
  // definition, dropped into both the desktop top bar and the mobile filter strip. Closes on
  // outside-click (the scrim) or Esc (effect above). Label flips to "Copied n ✓" after a copy.
  const copyLabel = copiedN ? "Copied " + copiedN + " ✓"
    : copying ? <><span className="news-spin" /> Resolving…</>
    : "Copy shortlist ▾";
  const copyMenu = (
    <div className="news-bar-pop news-copy-pop">
      <button className={"news-btn news-keep" + (copyOpen ? " on" : "")}
              disabled={copying || !stories.length} aria-expanded={copyOpen}
              onClick={() => setCopyOpen(o => !o)}>{copyLabel}</button>
      {copyOpen && (
        <>
          <div className="news-bar-scrim" onClick={() => setCopyOpen(false)} />
          <div className="news-bar-menu news-copy-menu">
            <button className="news-copy-item" onClick={() => doCopy("link")}>Link only</button>
            <button className="news-copy-item" onClick={() => doCopy("titlelink")}>Title + link</button>
            <button className="news-copy-item" onClick={() => doCopy("titledesc")}>Title + description + link</button>
          </div>
        </>
      )}
    </div>
  );
  // Export: same dropdown chrome as Copy, but writes a downloaded file (Markdown / CSV) through
  // the SAME assembly layer. Label flips to "Exported ✓" after a download.
  const exportLabel = exported ? "Exported ✓"
    : copying ? <><span className="news-spin" /> Resolving…</>
    : "Export ▾";
  const exportMenu = (
    <div className="news-bar-pop news-copy-pop">
      <button className="news-btn"
              disabled={copying || !stories.length}
              onClick={doExport}>{exported ? "Exported ✓" : "Export .txt"}</button>
    </div>
  );
  // "+N outside this window" — all-time kept/dismissed minus what's in the current window.
  // Both halves come from /api/news/counts, so it's cheap; only the active view's number
  // is shown (the lists are window-scoped now, so this keeps the all-time set discoverable).
  // Selecting a card fills the inspect zone. Desktop = the right rail (in place). Mobile =
  // the Watch sheet — the SAME sheet the toolbar's middle button opens, just entered by a
  // different door (a tap pre-selects the story; the button opens whatever's already there).
  // Before this, mobile passed no onSelect at all and the whole why/feed-shape zone was
  // simply unreachable on a phone.
  const pickStory = (s) => { setSelStory(s); if (isMobile) setMSheet("watch"); };

  // "Biggest stories" row -> that story's why-view. The THIRD door into the same room (desktop
  // fills the rail, mobile opens the Watch sheet — pickStory already routes both).
  // The filter question, decided on what the data does: the readout counts every in-window
  // story, ignoring the score floor and the thread filter ON PURPOSE (buried is the point), so
  // a row here CAN name a card the feed is hiding. Rebuilding it with floor 0 / no thread means
  // such a row still opens and shows its real why. The alternative — clearing JP's filters to
  // reveal it — silently rearranges the feed he set up, as a side effect of a click that only
  // asked to read one story. A row you can see should open; it should not redecorate the room.
  const openShapeCluster = (id) => {
    const c = (cards || []).find(x => x.ids && x.ids[0] === id);
    if (!c) return;
    const s = _windowCard(c, since, until, 0, "", labels);   // date window only
    if (s) pickStory(s);
  };

  const keptOutside = Math.max(0, (counts.kept_all || 0) - (counts.kept || 0));
  const dismissedOutside = Math.max(0, (counts.dismissed_all || 0) - (counts.dismissed || 0));
  const outsideN = view === "kept" ? keptOutside : view === "dismissed" ? dismissedOutside : 0;

  const feedInner = (
    loading || allCards === null ? (
      // `allCards === null` = the one fetch hasn't finished yet (it runs after meta arrives).
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
        {/* Name the article->card collapse so the article total can't read as the numerator
            of the card count. Both halves are window+floor scoped (see the `collapse` memo). */}
        <div className="news-count">
          {collapse.articles} {collapse.articles === 1 ? "article" : "articles"}
          {" → "}
          {collapse.cards} {collapse.cards === 1 ? "card" : "cards"}
          {view === "inbox" ? " to review" : ""}
        </div>
        <div className="news-list">
          {stories.map((s, i) => (
            <NewsStory key={s.ids[0] + "-" + i} story={s} view={view} onMark={mark}
                       readOnly={!canReview} since={since} until={until} isMobile={isMobile}
                       onSelect={pickStory}
                       selected={!!(selStory && selStory.ids && s.ids && selStory.ids[0] === s.ids[0])} />
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

  // ---------------- MOBILE: the shared Shell, zones collapsed behind the toolbar ------
  // News is the FIRST surface to consume Shell's mobile collapse (Ask-corpus + Study are
  // still on their old single-column branches). The mapping is the desktop's own zones, not
  // a new information architecture:
  //   LEFT rail (threads)                                  -> the "Threads" sheet   [left button]
  //   CENTER (feed cards)                                  -> stays inline, the whole screen
  //   RIGHT inspect (FeedShape, or NewsWhy on a selection)  -> the "Watch" sheet    [middle button]
  //   the top bar's date / score / sort                     -> the "Options" sheet  [right button]
  // Three buttons, JP's ruling. The bar reads left-to-right the way the desktop does: the
  // navigate zone on the left, the inspect zone in the middle (it's the thing you look AT),
  // the knobs on the right. "Options" and not "Filters" on the right BECAUSE Threads is
  // itself a filter — labelling one of two filtering sheets "Filters" would say the other
  // one isn't.
  // Why this replaces the old stacked column: that column pushed a 205px filter strip above
  // the feed (first headline started 404px down — half a phone screen of controls before one
  // story), AND it dropped the inspect zone entirely, so a phone reader could never see why a
  // story surfaced. The toolbar buys both back for one 48px bar.
  // NOTE the bar is at the BOTTOM and the app's own .mobile-tabs is fixed at the TOP, so the
  // two never collide (checked, not assumed — styles.css .mobile-tabs is `top: 0`).
  if (isMobile) {
    const mHead = (
      <div className="news-head">
        <h1 className="news-h1">News watch</h1>
        {meta.reviewer_name ? (
          <span className="news-asline" title="Keep/Dismiss are recorded under this reviewer">
            Reviewing as <strong>{meta.reviewer_name}</strong>
          </span>
        ) : !canReview ? (
          // The read-only signal, stated ONCE where it costs no row width. On mobile the
          // grayed Keep/Dismiss aren't rendered (see hideActions), and a plain reader gets
          // no "Reviewing as" line from the server (_reviewer() -> no id), so without this
          // there'd be nothing left telling a reader what the tab is. Says the same thing
          // the desktop tooltip says: you're reading someone's curated watch.
          <span className="news-asline">Read-only — a curated watch</span>
        ) : null}
        {/* Tabs lead, refresh sits at the far right of the same row — the desktop top bar's
            order (views on the left, icon controls right), and an icon rather than the old
            labelled 66px button.
            WHY IT STAYS VISIBLE rather than moving into the Options sheet (measured at 375px,
            not assumed): it rides the tabs row's spare width (129.7px spare vs a 32px icon)
            and costs 6.4px of header — the icon is 32px against the tabs' 26.8px. That 6.4px
            is 1.7% of the 214px this pass reclaimed. Against it: a tap, and filing under
            "Options" a control that changes what the feed CONTAINS rather than how it's
            filtered. Shrinking it to 27px would zero the 6.4px but trade away a real touch
            target for noise. So: visible, full size. */}
        {viewsToggle}
        <button className="news-bar-icon" disabled={loading} title="Refresh the scored feed"
                aria-label="Refresh the scored feed" onClick={() => setRefreshN(n => n + 1)}>
          <Icon.Refresh className={loading ? "spin" : undefined} />
        </button>
        {/* Shortlist copy + export stay Kept-only, and stay in the CENTER: they act on the
            visible shortlist, so they belong with it, not behind a filters sheet. */}
        {view === "kept" && <div className="news-mkept">{copyMenu}{exportMenu}</div>}
        {flash && <span className="news-flash">{flash}</span>}
      </div>
    );
    // LEFT sheet = the desktop rail, verbatim: the same threadList element the desktop
    // renders. Same state, same handlers — only its home moved.
    const mThreads = <div className="news-msheet">{threadList}</div>;
    // RIGHT sheet = the desktop top bar's knobs (date window / score / sort), grouped under
    // the rail's own small-caps section rhythm.
    const mOptions = (
      <div className="news-msheet">
        <div className="news-msec">
          <div className="news-mlabel">Date window</div>
          <div className="news-filters news-mfilters">
            <label className="news-f"><span>Since</span>{dateInput}</label>
            <label className="news-f"><span>Until</span>{untilInput}</label>
            {presets}
          </div>
        </div>
        <div className="news-msec">
          <div className="news-mlabel">Score</div>
          {scoreSeg}
        </div>
        <div className="news-msec">
          <div className="news-mlabel">Sort</div>
          {sortSel}
        </div>
      </div>
    );
    // MIDDLE = the inspect zone. The toolbar button and a card tap are two doors into the
    // SAME room: both land on this one expression — a selected card shows its why, otherwise
    // the feed-shape readout. "‹ Watch" still clears the selection back to the readout, so
    // the sheet's own depth works whichever door you came through.
    const mWatch = selStory
      ? <NewsWhy story={selStory} onBack={() => setSelStory(null)} />
      : <FeedShape shape={shape} onPick={openShapeCluster} />;
    const sheet = mSheet === "threads" ? mThreads
      : mSheet === "options" ? mOptions
      : mSheet === "watch" ? mWatch
      : null;
    const flip = (k) => () => setMSheet(m => (m === k ? null : k));
    // The Watch BUTTON always means "today's watch" — it drops any card selection on the way
    // in, so it can't reopen the last card's why-view days later (JP, 2026-07-15). Cleared
    // HERE at the door rather than when the sheet closes: closing keeps the selection, which
    // is what leaves the card highlighted in the feed and matches the desktop rail holding its
    // selection. "‹ Watch" is untouched — it lives inside the sheet and clears the same state.
    // So: button = readout, card tap = that card's why, back link = readout. Three paths, one
    // room, no stale door.
    const openWatch = () => {
      if (mSheet === "watch") { setMSheet(null); return; }
      setSelStory(null);
      setMSheet("watch");
    };
    const tools = [
      { key: "threads", label: "Threads", icon: <Icon.Hash />, on: mSheet === "threads", onTap: flip("threads") },
      { key: "watch", label: "Watch", icon: <Icon.Panel />, on: mSheet === "watch", onTap: openWatch },
      { key: "options", label: "Options", icon: <Icon.Filter />, on: mSheet === "options", onTap: flip("options") },
    ];
    return (
      <Shell
        className="news-frame news-m"
        isMobile={true}
        center={<div className="news-view">{mHead}{feedInner}</div>}
        mobile={{
          tools,
          sheet,
          // The Watch sheet carries its own header band + its own scroll box (.news-shape is a
          // flex column), so it goes BARE — the padded .zsheet-body would nest a second scroll
          // box and collapse the stack's flex-fill. Filters is plain content -> normal body.
          sheetBare: mSheet === "watch",
          // Options is CONTROLS ONLY (date window / score / sort — nothing conditionally
          // mounted, verified against mOptions above), so it's a MENU under the contract's
          // classification line; it was swept in as a panel with the rest of the News cards
          // and opened as a near-full card with one control-strip's worth of content (JP,
          // 2026-07-15). Threads and Watch hold data -> panels, untouched.
          sheetVariant: mSheet === "options" ? "menu" : undefined,
          sheetTitle: mSheet === "threads" ? "Threads" : mSheet === "options" ? "Options" : null,
          onCloseSheet: () => setMSheet(null),
        }}
      />
    );
  }

  // ---------------- DESKTOP: the shared three-zone frame ------------------------
  // LEFT rail is now JUST the thread list (the navigate zone) — every other control
  // moved up into the center's horizontal top bar (below). Threads get the full height.
  // The THREADS header rides Word study's .brail-top band (59px + bottom border), so its
  // border meets the top bar's at the same height and reads as one unbroken line across.
  const rail = (
    <div className="news-rail news-rail-threads-only">
      <div className="brail-top"><div className="brail-eyebrow">Threads</div></div>
      <div className="news-rail-body">
        {threadList}
        {meta.reviewer_name ? (
          <div className="news-rail-asline" title="Keep/Dismiss are recorded under this reviewer">
            Reviewing as <strong>{meta.reviewer_name}</strong>
          </div>
        ) : null}
      </div>
    </div>
  );

  // CENTER top bar — one horizontal row (Library's .lib-bar pattern): view pills · date
  // window (popover) · score · sort · refresh. Date is a dropdown so its two fields +
  // presets don't eat the row; score/sort are plain dropdowns. All apply to every view.
  const topBar = (
    <div className="news-bar">
      <div className="news-bar-l">
        {viewsToggle}
        <span className="news-bar-sep" aria-hidden="true" />
        <div className="news-bar-pop">
          <button className={"news-bar-btn" + (dateOpen ? " on" : "")}
                  title="Date window" aria-expanded={dateOpen}
                  onClick={() => setDateOpen(o => !o)}>{dateLabel} ▾</button>
          {dateOpen && (
            <>
              <div className="news-bar-scrim" onClick={() => setDateOpen(false)} />
              <div className="news-bar-menu">
                <label className="news-f"><span>Since</span>{dateInput}</label>
                <label className="news-f"><span>Until</span>{untilInput}</label>
                {presets}
              </div>
            </>
          )}
        </div>
        <label className="news-bar-f"><span>Score</span>{scoreSel}</label>
        <label className="news-bar-f"><span>Sort</span>{sortSel}</label>
        <span className="news-bar-sep" aria-hidden="true" />
        {/* Re-pull the scored set without a full reload (also the force-refresh for a hand
            re-score — the held set's cache busts on a new pull, not an in-place re-score). */}
        <button className="news-bar-icon" disabled={loading} title="Refresh the scored feed"
                aria-label="Refresh the scored feed"
                onClick={() => setRefreshN(n => n + 1)}>
          <Icon.Refresh className={loading ? "spin" : undefined} />
        </button>
        {/* First-timer key to what the score / dates / views mean. Reuses the date
            popover's scrim+menu styling; opens right-aligned so it can't run off the bar. */}
        <div className="news-bar-pop">
          <button className={"news-bar-icon" + (helpOpen ? " on" : "")} title="How the feed works"
                  aria-label="How the feed works" aria-expanded={helpOpen}
                  onClick={() => setHelpOpen(o => !o)}>
            <Icon.Info />
          </button>
          {helpOpen && (
            <>
              <div className="news-bar-scrim" onClick={() => setHelpOpen(false)} />
              <div className="news-bar-menu news-help-menu">
                <div className="news-help-head">
                  <span>How the feed works</span>
                  <button className="news-help-x" aria-label="Close" onClick={() => setHelpOpen(false)}>
                    <Icon.Close />
                  </button>
                </div>
                <div className="news-help-sec">
                  <div className="news-help-t">The lens every story is scored against</div>
                  <p>{_NEWS_LENS}</p>
                </div>
                <div className="news-help-sec">
                  <div className="news-help-t">Score</div>
                  <p>It's not a quality rating — it's how closely a story sits to the themes being
                     watched. A high score means right on theme; a low one is further out, not junk.
                     Set the score filter to “Any score” to see everything.</p>
                </div>
                <div className="news-help-sec">
                  <div className="news-help-t">Dates</div>
                  <p>A story can run for several days. <strong>Peaked</strong> is the day it drew the
                     most coverage — the day the story is filed under; <strong>latest</strong> is its
                     most recent article. The date window filters on the peaked day.</p>
                </div>
                <div className="news-help-sec">
                  <div className="news-help-t">Views</div>
                  <p><strong>Inbox</strong> is everything you haven't sorted yet. <strong>Keep</strong> and
                     <strong> Dismiss</strong> move a story out of the inbox — that's your own label, it
                     doesn't change the scoring.</p>
                </div>
              </div>
            </>
          )}
        </div>
        {view === "kept" && <>{copyMenu}{exportMenu}</> /* shortlist copy + export: Kept only */}
        {flash && <span className="news-flash">{flash}</span>}
      </div>
    </div>
  );

  // Phase 2: migrated from the old <ThreeZone> onto the shared <Shell>. PARITY ONLY — the
  // emitted DOM is byte-identical (ThreeZone wrapped `inspect` in <aside className="zinspect">;
  // Shell renders `inspect` raw, so News supplies that same aside). Crucially the inspect stays a
  // PLAIN .zinspect (NOT .rstack), so it keeps News's float-behind-the-nav (top:0) — a migrated
  // shipped surface reproduces the old float; only NEW surfaces start below the nav. isMobile is
  // hard-false here because News's own `if (isMobile)` branch above owns the mobile layout
  // (untouched = mobile parity for free) and never reaches this desktop return.
  return (
    <Shell
      className="news-frame"
      isMobile={false}
      rail={rail}
      center={<>{topBar}<div className="news-feed">{feedInner}</div></>}
      inspect={<aside className="zinspect">
        {selStory ? <NewsWhy story={selStory} onBack={() => setSelStory(null)} />
                  : <FeedShape shape={shape} onPick={openShapeCluster} />}
      </aside>}
    />
  );
}
