// ============================================================
// STUDY MODULES
// One Study tab with a sub-switch: Topics · Graphs.
//   Topics — a BROWSE: a subject broken into subtopic SECTIONS, each with its verses
//            (mostly filled from MetaV; light editing). PUBLIC when published. Shape:
//            {title, intro, sections:[{heading, verses:[{ref,text}]}]}.
//   Graphs — an ARGUMENT MAP (admin-only): a pool of CLAIMS joined by per-tradition
//            LINKS, each claim tagged with provenance + each link with strength, so the
//            conclusion can be stress-tested (see argmap.py). Read-only here; authored
//            with scripts/add_study_graph.py.
// Backend: views_study.py (study.db). Graph routes are admin-gated (404 otherwise).
// ============================================================
const STUDY_MODULES = [
  { id: "topic", label: "Topics" },
  { id: "graph", label: "Graphs" },
];
// "name" = a person/place name-topic (MetaV), shown on the metaV sidebar, opened
// here read-only. Same shape as a topic, so it renders through TopicPage.
const isTopicLike = t => t === "topic" || t === "name";
// Subtopic headings arrive from Nave's as little sentences ("Father.") — drop a
// trailing period/comma so they read as headings, not sentences.
const cleanHeading = h => String(h || "").replace(/\s*[.,;:]+\s*$/, "");
// Split "Leviticus 10:8" -> book "Leviticus" + short ref "10:8", so a section's verses
// can be grouped (and collapsed) under book headers.
const _REF_SPLIT = /^(.*?)\s+(\d+:\d+(?:[-–—]\d+(?::\d+)?)?)\s*$/;
const bookOf = ref => { const m = _REF_SPLIT.exec(String(ref || "")); return m ? m[1] : String(ref || ""); };
const shortRef = ref => { const m = _REF_SPLIT.exec(String(ref || "")); return m ? m[2] : String(ref || ""); };
function groupByBook(verses) {
  const groups = [];
  (verses || []).forEach(v => {
    const book = bookOf(v.ref);
    const last = groups[groups.length - 1];
    if (last && last.book === book) last.verses.push(v);
    else groups.push({ book, verses: [v] });
  });
  return groups;
}
// A verse reference inside a READ view. When the verse carries book/chapter/verse (the
// server resolves them) and a nav handler is present, it's a button that jumps into the
// Library reader — same idea as a Search/Lexicon result reference. Otherwise a plain pill.
function StudyRef({ v, label, onNavigate }) {
  const go = onNavigate && v && v.book && v.chapter && v.verse;
  if (!go) return <span className="study-verse-ref">{label}</span>;
  return (
    <button className="study-verse-ref study-verse-ref--link" title="Open in the reader"
      onClick={() => onNavigate(v.book, v.chapter, v.verse)}>{label}</button>
  );
}
// Nave's titles are index-style — keyword first: "Accusation, False", "Trinity, The".
// Flip the SAFE ones to read naturally ("False Accusation", "The Trinity"); leave
// ambiguous multi-word tails alone (e.g. "God, the Father" shouldn't become "the
// Father God"). Display only — the stored title is untouched.
const _TITLE_STOP = new Set(["the", "a", "an", "of", "and", "or", "to", "in", "on", "for"]);
function displayTitle(t) {
  t = String(t || "").trim();
  const ci = t.indexOf(",");
  if (ci < 0 || t.indexOf(",", ci + 1) >= 0) return t;   // no comma, or more than one -> leave
  const head = t.slice(0, ci).trim();
  const tail = t.slice(ci + 1).trim();
  if (!head || !tail) return t;
  if (tail.toLowerCase() === "the") return "The " + head;
  const words = tail.split(/\s+/);
  if (words.length === 1 && !_TITLE_STOP.has(tail.toLowerCase()))
    return tail.charAt(0).toUpperCase() + tail.slice(1) + " " + head;
  return t;
}

function blankTopic() {
  return { id: "", type: "topic", title: "", intro: "", sections: [{ heading: "", verses: [] }], related: [], status: "draft", source: "" };
}
function moveItem(arr, i, dir) {
  const j = i + dir;
  if (j < 0 || j >= arr.length) return arr;
  const a = arr.slice();
  const t = a[i]; a[i] = a[j]; a[j] = t;
  return a;
}

// Add a reference: resolves it to ABP prose, then hands {ref, text} up.
function AddRef({ onAdd, placeholder }) {
  const [ref, setRef] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const add = () => {
    const r = ref.trim();
    if (!r || busy) return;
    setBusy(true); setErr("");
    api.studyVerse(r).then(d => {
      setBusy(false);
      if (d && d.verses && d.verses.length) {
        onAdd({ ref: d.canonical || r, text: d.verses.map(v => v.text).join(" ") });
        setRef("");
      } else {
        setErr((d && d.error) || "Couldn't find that reference.");
      }
    });
  };
  return (
    <>
      <div className="study-add-row">
        <input className="study-add-input" type="text" value={ref}
          placeholder={placeholder || "Add a reference — e.g. Romans 10:17 (text fills in)"}
          onChange={e => { setRef(e.target.value); if (err) setErr(""); }}
          onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); add(); } }} />
        <button className="study-add-btn" onClick={add} disabled={busy || !ref.trim()}>{busy ? "…" : "Add"}</button>
      </div>
      {err && <div className="study-add-err">{err}</div>}
    </>
  );
}

// Editable verse list (with remove).
function VerseRows({ items, onRemove }) {
  if (!items.length) return null;
  return (
    <div className="study-verse-list">
      {items.map((it, i) => (
        <div className="study-verse-row" key={i}>
          <span className="study-verse-ref">{it.ref}</span>
          <span className="study-verse-text">{it.text || <em className="study-verse-missing">not found — saved as a reference</em>}</span>
          <button className="study-x" onClick={() => onRemove(i)} aria-label="Remove verse" title="Remove">×</button>
        </div>
      ))}
    </div>
  );
}

// ---- Topics ---------------------------------------------------------------
function TopicSectionEdit({ section, idx, count, onChange, onRemove, onMove }) {
  return (
    <div className="study-section study-section--edit">
      <div className="study-section-bar">
        <input className="study-section-head-input" type="text" value={section.heading}
          placeholder="Section heading (optional)" onChange={e => onChange({ ...section, heading: e.target.value })} />
        <div className="study-section-tools">
          <button className="study-sec-tool" disabled={idx === 0} onClick={() => onMove(-1)} aria-label="Move up" title="Move up">↑</button>
          <button className="study-sec-tool" disabled={idx === count - 1} onClick={() => onMove(1)} aria-label="Move down" title="Move down">↓</button>
          <button className="study-sec-tool study-sec-tool--del" onClick={onRemove} aria-label="Remove section" title="Remove section">✕</button>
        </div>
      </div>
      <VerseRows items={section.verses} onRemove={i => onChange({ ...section, verses: section.verses.filter((_, j) => j !== i) })} />
      <AddRef onAdd={v => onChange({ ...section, verses: [...section.verses, v] })} placeholder="Add a reference to this section" />
    </div>
  );
}

// Which subtopic sections start open on the read page: a 1-section topic opens; a
// multi-section topic starts collapsed (you see the structure first, expand on demand).
function defaultOpenSecs(entry) {
  const secs = (entry && entry.sections) || [];
  return new Set(secs.length <= 1 ? secs.map((_, i) => i) : []);
}

function TopicPage({ entry, editing, onChange, onSave, onDelete, onClose, onToggleEdit, previewReader, saving, savedAt, onNavigate }) {
  const up = patch => onChange({ ...entry, ...patch });
  const verseCount = entry.sections.reduce((n, s) => n + s.verses.length, 0);
  const [drafting, setDrafting] = useState(false);
  const [draftErr, setDraftErr] = useState(false);
  const draftIntro = () => {
    if (drafting) return;
    setDrafting(true); setDraftErr(false);
    const slim = (entry.sections || []).map(s => ({ heading: s.heading, verses: (s.verses || []).slice(0, 2).map(v => ({ ref: v.ref, text: v.text })) }));
    api.studyDraftIntro({ title: entry.title, sections: slim }).then(d => {
      setDrafting(false);
      if (d && d.intro) up({ intro: d.intro }); else setDraftErr(true);
    });
  };
  const [openSecs, setOpenSecs] = useState(() => defaultOpenSecs(entry));
  useEffect(() => { setOpenSecs(defaultOpenSecs(entry)); }, [entry.id]);
  const allOpen = entry.sections.length > 0 && openSecs.size === entry.sections.length;
  const toggleAll = () => setOpenSecs(allOpen ? new Set() : new Set(entry.sections.map((_, i) => i)));
  const toggleSec = i => setOpenSecs(prev => { const n = new Set(prev); n.has(i) ? n.delete(i) : n.add(i); return n; });
  const [closedBooks, setClosedBooks] = useState(() => new Set());   // big sections group verses by book; this tracks collapsed books
  useEffect(() => { setClosedBooks(new Set()); }, [entry.id]);
  const toggleBook = key => setClosedBooks(prev => { const n = new Set(prev); n.has(key) ? n.delete(key) : n.add(key); return n; });

  if (!editing) {
    return (
      <div className="study-topic">
        <div className="study-editor-bar">
          <button className="study-back" onClick={onClose}>‹ {previewReader ? "Back" : "All topics"}</button>
          {!previewReader && <button className="study-edit-btn" onClick={onToggleEdit}>Edit</button>}
        </div>
        <div className="study-eyebrow">Topic</div>
        <h1 className="study-topic-title">{displayTitle(entry.title)}</h1>
        <div className="study-topic-meta">{entry.source === "metav" ? "from Nave's · " : ""}{entry.sections.length} sections · {verseCount} verses</div>
        {entry.intro && <p className="study-topic-intro">{entry.intro}</p>}
        {entry.sections.length === 0 ? (
          <div className="stats-empty">No verses yet — click Edit to add some.</div>
        ) : (
          <>
            {entry.sections.length > 1 && (
              <button className="study-collapse-all" onClick={toggleAll}>{allOpen ? "Collapse all" : "Expand all"}</button>
            )}
            {entry.sections.map((s, i) => {
              const isOpen = openSecs.has(i);
              return (
                <div className={"study-section study-section--collapsible" + (isOpen ? " open" : "")} key={i}>
                  <button className="study-section-toggle" onClick={() => toggleSec(i)} aria-expanded={isOpen}>
                    <span className="study-section-chevron">{isOpen ? "▾" : "▸"}</span>
                    <span className="study-section-head-text">{cleanHeading(s.heading) || "General references"}</span>
                    <span className="study-section-count">{s.verses.length}</span>
                  </button>
                  {isOpen && (s.verses.length > 4 ? (
                    <div className="study-books">
                      {groupByBook(s.verses).map((g, gi) => {
                        const bkey = i + "|" + gi + "|" + g.book;
                        const bopen = !closedBooks.has(bkey);
                        return (
                          <div className="study-book" key={gi}>
                            <button className="study-book-toggle" onClick={() => toggleBook(bkey)} aria-expanded={bopen}>
                              <span className="study-book-chevron">{bopen ? "▾" : "▸"}</span>
                              <span className="study-book-name">{g.book}</span>
                              <span className="study-book-count">{g.verses.length}</span>
                            </button>
                            {bopen && (
                              <div className="study-book-verses">
                                {g.verses.map((v, j) => (
                                  <div className="study-read-verse" key={j}>
                                    <StudyRef v={v} label={shortRef(v.ref)} onNavigate={onNavigate} />
                                    <span className="study-read-text">{v.text || <em className="study-verse-missing">(text not found)</em>}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="study-read-verses">
                      {s.verses.map((v, j) => (
                        <div className="study-read-verse" key={j}>
                          <StudyRef v={v} label={v.ref} onNavigate={onNavigate} />
                          <span className="study-read-text">{v.text || <em className="study-verse-missing">(text not found)</em>}</span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              );
            })}
          </>
        )}
      </div>
    );
  }

  return (
    <div className="study-editor">
      <div className="study-editor-bar">
        <button className="study-back" onClick={() => entry.id ? onToggleEdit() : onClose()}>‹ {entry.id ? "Done editing" : "Cancel"}</button>
        <div className="study-editor-actions">
          {savedAt && !saving && <span className="study-saved">Saved ✓</span>}
          {entry.id && <button className="study-del" onClick={onDelete}>Delete</button>}
          <button className="study-save" onClick={onSave} disabled={saving || !entry.title.trim()}>{saving ? "Saving…" : "Save"}</button>
        </div>
      </div>
      <div className="study-field">
        <label className="study-label">Topic</label>
        <input className="study-input" type="text" value={entry.title} placeholder="Subject — e.g. Faith" onChange={e => up({ title: e.target.value })} />
      </div>
      <div className="study-field">
        <label className="study-label">Intro <span className="study-label-hint">(optional)</span>
          <button type="button" className="study-ai-btn" disabled={drafting || !entry.title.trim()} onClick={draftIntro}>{drafting ? "Drafting…" : "✦ Draft with AI"}</button>
          {draftErr && <span className="study-ai-err">couldn't draft — try again</span>}
        </label>
        <textarea className="study-textarea study-textarea--sm" value={entry.intro} placeholder="A short, plain-English lead-in (or use Draft with AI)." onChange={e => up({ intro: e.target.value })} />
      </div>
      {entry.sections.map((s, i) => (
        <TopicSectionEdit key={i} section={s} idx={i} count={entry.sections.length}
          onChange={ns => up({ sections: entry.sections.map((x, j) => j === i ? ns : x) })}
          onRemove={() => up({ sections: entry.sections.filter((_, j) => j !== i) })}
          onMove={dir => up({ sections: moveItem(entry.sections, i, dir) })} />
      ))}
      <button className="study-add-section" onClick={() => up({ sections: [...entry.sections, { heading: "", verses: [] }] })}>+ Add section</button>
      <div className="study-field study-status-row">
        <span className="study-label">Visibility</span>
        <div className="seg">
          <button className={"seg-b" + (entry.status === "draft" ? " on" : "")} onClick={() => up({ status: "draft" })}>Draft</button>
          <button className={"seg-b" + (entry.status === "published" ? " on" : "")} onClick={() => up({ status: "published" })}>Published</button>
        </div>
        <span className="study-label-hint">Draft = only you. Published = visible to everyone.</span>
      </div>
    </div>
  );
}

// ---- Graph (argument map) -------------------------------------------------
// Provenance says whether a claim stands on the source: text/lexicon = grounded (navy),
// everything else leans on something added (amber). A conclusion gets no badge.
const PROV_GROUNDED = new Set(["text", "lexicon"]);
const PROV_LABEL = { text: "Text", lexicon: "Lexicon", tradition: "Tradition", conjecture: "Conjecture", inference: "Inference", observation: "Observation", conclusion: "" };
function ProvBadge({ prov }) {
  const label = PROV_LABEL[prov] != null ? PROV_LABEL[prov] : prov;
  if (!label) return null;
  return <span className={"study-prov " + (PROV_GROUNDED.has(prov) ? "study-prov--grounded" : "study-prov--added")}>{label}</span>;
}

// One claim, compact: its statement + provenance badge, and (for a verse claim) a
// reference button that jumps into the reader plus the verse text.
function ClaimChip({ claim, onNavigate }) {
  if (!claim) return <div className="study-claim study-claim--missing">(missing claim)</div>;
  return (
    <div className={"study-claim" + (PROV_GROUNDED.has(claim.provenance) ? " study-claim--grounded" : "")}>
      <div className="study-claim-head">
        <ProvBadge prov={claim.provenance} />
        {claim.ref && <StudyRef v={claim} label={claim.ref} onNavigate={onNavigate} />}
      </div>
      <div className="study-claim-text">{claim.text}</div>
      {claim.ref && claim.verse_text && <div className="study-claim-verse">{claim.verse_text}</div>}
    </div>
  );
}

const linkKey = l => l.from + "→" + l.to + "·" + l.relation;

// ---- The chart (per-overlay SVG: verses converge into claims into the thesis) ----
const CH = { W: 168, H: 60, COLGAP: 206, ROWGAP: 90, PAD: 16 };
const shortLabel = c => (c && (c.label || c.ref)) || (c && c.text ? (c.text.length > 32 ? c.text.slice(0, 30) + "…" : c.text) : "");

// Longest-path column for each node from the grounded verses (verses = column 0).
function chartColumns(claims, carry, ids) {
  const preds = {};
  carry.forEach(l => { (preds[l.to] = preds[l.to] || []).push(l.from); });
  const col = {}, busy = {};
  const walk = id => {
    if (id in col) return col[id];
    if (busy[id]) return 0;                       // cycle guard
    busy[id] = true;
    // A SOURCE (a verse, or anything with no feeder) sits in column 0; everything else — incl. a
    // grounded LEXICON claim that's derived from a verse — sits one past whatever feeds it.
    const c = (preds[id] && preds[id].length) ? 1 + Math.max(...preds[id].map(walk)) : 0;
    busy[id] = false;
    return (col[id] = c);
  };
  ids.forEach(walk);
  return col;
}

// One overlay drawn left-to-right. Shared verses are pinned to the top rows in the same
// order on every overlay, so flipping traditions holds them in place while the arrows and
// the conclusion change — the verse back-reference, made visual.
function GraphSvg({ claims, overlay, verdict, shared, onNavigate }) {
  const carry = (overlay.links || []).filter(l => l.relation !== "undercuts");
  const ids = [], seen = new Set();
  const add = id => { if (id && !seen.has(id)) { seen.add(id); ids.push(id); } };
  carry.forEach(l => { add(l.from); add(l.to); });
  add(overlay.thesis);
  const col = chartColumns(claims, carry, ids);
  let maxCol = Math.max(0, ...ids.map(id => col[id] || 0));
  if (overlay.thesis && !carry.some(l => l.to === overlay.thesis)) {
    col[overlay.thesis] = maxCol + 1;                        // gap: nothing points at the conclusion — float it out alone, with a visible space before it
    maxCol += 1;
  }
  // A link spanning more than one column gets invisible WAYPOINTS at each column it crosses, so
  // the layout reserves a clear row for the line there and the line bends around the boxes instead
  // of slicing over them. Waypoints join the ordering like thin nodes; the link is drawn through them.
  const wpOf = {}, dcol = {};
  const segPre = {}, segSucc = {};                  // chain-segment links that drive the ordering
  const seg = (a, b) => { (segPre[b] = segPre[b] || []).push(a); (segSucc[a] = segSucc[a] || []).push(b); };
  carry.forEach(l => {
    const wps = [];
    for (let c = (col[l.from] || 0) + 1; c < (col[l.to] || 0); c++) {
      const d = "~wp:" + linkKey(l) + ":" + c;
      dcol[d] = c; wps.push(d);
    }
    wpOf[linkKey(l)] = wps;
    const chain = [l.from, ...wps, l.to];
    for (let j = 0; j < chain.length - 1; j++) seg(chain[j], chain[j + 1]);
  });
  const nodes = ids.concat(Object.keys(dcol));
  const colOf = id => (id in dcol) ? dcol[id] : col[id];
  const byCol = {};
  nodes.forEach(id => { (byCol[colOf(id)] = byCol[colOf(id)] || []).push(id); });
  const rank = id => { const i = shared.indexOf(id); return i < 0 ? 1e6 : i; };   // tiebreak only
  const cols = Object.keys(byCol).map(Number).sort((a, b) => a - b);
  const yy = {};
  // Pull every node toward the average row of its chain-neighbours, re-sort, then push siblings
  // apart so nothing overlaps. Waypoints take part, so each line reserves its own clear row.
  const relax = (c, neigh) => {
    byCol[c].forEach(id => {
      const ns = (neigh[id] || []).filter(n => n in yy);
      if (ns.length) yy[id] = ns.reduce((s, n) => s + yy[n], 0) / ns.length;
    });
    byCol[c].sort((a, b) => (yy[a] - yy[b]) || (rank(a) - rank(b)));
    for (let k = 1; k < byCol[c].length; k++) {
      const a = byCol[c][k - 1], b = byCol[c][k];
      if (yy[b] - yy[a] < CH.ROWGAP) yy[b] = yy[a] + CH.ROWGAP;
    }
  };
  if (byCol[0]) byCol[0].sort((a, b) => rank(a) - rank(b));        // a stable starting order
  (byCol[0] || []).forEach((id, r) => { yy[id] = r * CH.ROWGAP; });
  cols.forEach(c => { if (c > 0) relax(c, segPre); });            // seed everyone with one forward pass
  // Sweep both directions a few times — the standard untangle. Right→left reorders verses to sit
  // beside what they feed; left→right re-centres the claims (and waypoints) on their feeders.
  for (let pass = 0; pass < 4; pass++) {
    for (let i = cols.length - 1; i >= 0; i--) relax(cols[i], segSucc);
    for (let i = 0; i < cols.length; i++) if (cols[i] > 0) relax(cols[i], segPre);
  }
  const minY = Math.min(...nodes.map(id => yy[id] || 0));          // shift the topmost node to y=0 (no dead space above)
  if (minY) nodes.forEach(id => { yy[id] = (yy[id] || 0) - minY; });
  const pos = {};
  nodes.forEach(id => { pos[id] = { c: colOf(id), y: yy[id] || 0 }; });
  const maxY = Math.max(0, ...nodes.map(id => pos[id].y));
  const W = CH.PAD * 2 + maxCol * CH.COLGAP + CH.W;
  const H = CH.PAD * 2 + maxY + CH.H;
  const X = id => CH.PAD + pos[id].c * CH.COLGAP;
  const Y = id => CH.PAD + pos[id].y;
  const cxc = id => X(id) + CH.W / 2;                              // column-centre x (a waypoint's x)
  const joints = new Set(((verdict && verdict.load_bearing) || []).map(linkKey));
  const defeated = new Set(((verdict && verdict.defeated) || []));        // knocked out by a grounded, solid objection
  const edgeKind = l => joints.has(linkKey(l)) ? "joint" : l.strength;   // solid | contested | weak
  const nodeKind = id => {
    const p = (claims[id] || {}).provenance;
    return p === "conclusion" ? "concl" : (PROV_GROUNDED.has(p) ? "verse" : "added");
  };
  // Smooth path through a list of points (each [x, y, column]). The vertical move always happens in
  // the GAP between two columns — never inside a box's column — so a line that changes rows can't cut
  // across a box. Horizontal runs sit on de-overlapped rows, so they're clear too. Boxes can't be hit.
  const pathThrough = pts => {
    let d = "M" + pts[0][0] + "," + pts[0][1];
    for (let i = 1; i < pts.length; i++) {
      const y1 = pts[i - 1][1], x2 = pts[i][0], y2 = pts[i][1];
      const c = Math.min(pts[i - 1][2], pts[i][2]);
      const cx = CH.PAD + c * CH.COLGAP + CH.W + (CH.COLGAP - CH.W) / 2;   // mid of the gap after column c
      d += " C" + cx + "," + y1 + " " + cx + "," + y2 + " " + x2 + "," + y2;
    }
    return d;
  };
  return (
    <svg className="study-svg" viewBox={"0 0 " + W + " " + H} width={W} height={H} role="img">
      <defs>
        {["solid", "contested", "weak", "joint"].map(k => (
          <marker key={k} id={"ah-" + k} className={"study-arrow study-arrow--" + k}
            markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto" markerUnits="userSpaceOnUse">
            <path d="M0,0 L7,3 L0,6 Z" />
          </marker>
        ))}
      </defs>
      {carry.map((l, i) => {
        if (!pos[l.from] || !pos[l.to]) return null;
        const k = edgeKind(l);
        const pts = [[X(l.from) + CH.W, Y(l.from) + CH.H / 2, pos[l.from].c]];               // right edge of the from box
        (wpOf[linkKey(l)] || []).forEach(d => { pts.push([cxc(d), Y(d) + CH.H / 2, pos[d].c]); });   // through each reserved row
        pts.push([X(l.to) - 8, Y(l.to) + CH.H / 2, pos[l.to].c]);                            // left edge of the to box (room for the arrow)
        return <path key={i} className={"study-edge study-edge--" + k}
          d={pathThrough(pts)} markerEnd={"url(#ah-" + k + ")"} />;
      })}
      {ids.map(id => {
        const c = claims[id] || {};
        const k = nodeKind(id);
        const go = onNavigate && c.book && c.chapter && c.verse;
        return (
          <g key={id} transform={"translate(" + X(id) + "," + Y(id) + ")"}
            className={"study-node study-node--" + k + (go ? " study-node--link" : "") + (defeated.has(id) ? " study-node--defeated" : "")}
            onClick={go ? () => onNavigate(c.book, c.chapter, c.verse) : undefined}>
            <title>{c.text || id}</title>
            {/* a foreignObject box so the label WRAPS to the box (SVG <text> can't wrap → it spilled) */}
            <foreignObject width={CH.W} height={CH.H}>
              <div className="study-node-box">
                {k === "verse" && c.ref ? (
                  <>
                    <div className="study-node-ref">{c.ref}</div>
                    {c.label ? <div className="study-node-sub">{c.label}</div> : null}
                  </>
                ) : (
                  <div className="study-node-main">{shortLabel(c)}</div>
                )}
              </div>
            </foreignObject>
          </g>
        );
      })}
    </svg>
  );
}

// Tabs to flip traditions, the SVG, a legend, and — for the selected side — the verdict,
// why each non-solid link is rated as it is, and the open objections.
function GraphChart({ claims, overlays, analysis, onNavigate }) {
  const [sel, setSel] = useState(0);
  if (!overlays.length) return null;
  const i = Math.min(sel, overlays.length - 1);
  const overlay = overlays[i];
  const verdict = (analysis.verdicts || [])[i] || { grounded: false, gap: false, load_bearing: [], defeated: [] };
  const shared = (analysis.diff || {}).shared_verses || [];
  const cls = verdict.overturned ? "overturned" : verdict.grounded ? "stands" : verdict.gap ? "gap" : "depends";
  const label = verdict.overturned ? "Overturned — a grounded objection knocks out the conclusion"
    : verdict.grounded ? "Stands on the text"
    : verdict.gap ? "Incomplete — a step is missing"
    : (verdict.load_bearing && verdict.load_bearing.length) ? "Depends on a non-solid joint"
    : "Depends on contested steps";
  const why = (overlay.links || []).filter(l => l.relation !== "undercuts" && l.strength !== "solid" && l.why);
  const objections = (overlay.links || []).filter(l => l.relation === "undercuts");
  const defeatedSet = new Set(verdict.defeated || []);
  const objDecisive = l => l.strength === "solid" && defeatedSet.has(l.to);   // cleared the knock-down bar
  return (
    <div className="study-chart">
      <div className="study-chart-tabs">
        {overlays.map((ov, j) => (
          <button key={j} className={"study-chart-tab" + (j === i ? " on" : "")} onClick={() => setSel(j)}>{ov.tradition}</button>
        ))}
      </div>
      <div className={"study-verdict study-verdict--" + cls}>{label}</div>
      <div className="study-chart-scroll">
        <GraphSvg claims={claims} overlay={overlay} verdict={verdict} shared={shared} onNavigate={onNavigate} />
      </div>
      <div className="study-chart-legend">
        <span><i className="study-key study-key--verse" /> verse (grounded)</span>
        <span><i className="study-key study-key--added" /> inference / tradition</span>
        <span><i className="study-key study-key--concl" /> conclusion</span>
        <span><i className="study-key-line study-key-line--solid" /> established</span>
        <span><i className="study-key-line study-key-line--contested" /> contested</span>
        <span><i className="study-key-line study-key-line--weak" /> weak</span>
        <span><i className="study-key-line study-key-line--joint" /> load-bearing joint</span>
        {verdict.defeated && verdict.defeated.length > 0 && (
          <span><i className="study-key study-key--defeated" /> overturned by an objection</span>
        )}
      </div>
      {why.length > 0 && (
        <div className="study-chart-why">
          <div className="study-objections-label">Why the dashed links are rated that way</div>
          {why.map((l, j) => (
            <div className="study-link-why" key={j}>
              <b>{shortLabel(claims[l.from])} → {shortLabel(claims[l.to])}</b> ({l.strength}): {l.why}
              <span className="study-link-by"> — {overlay.tradition}'s call</span>
            </div>
          ))}
        </div>
      )}
      {objections.length > 0 && (
        <div className="study-objections">
          <div className="study-objections-label">Objections {objections.some(objDecisive) ? "(a grounded, solid one knocks out its target)" : "(raised, none decisive)"}</div>
          {objections.map((l, j) => (
            <div className={"study-objection" + (objDecisive(l) ? " study-objection--decisive" : "")} key={j}>
              {objDecisive(l) && <span className="study-objection-tag">knocks out {shortLabel(claims[l.to])}</span>}
              {l.why || ((claims[l.from] || {}).text + " — attacks the conclusion")}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Read-only argument-map page (the in-app editor + React Flow canvas come in a later cut).
function GraphPage({ entry, onClose, previewReader, onNavigate }) {
  const claims = entry.claims || {};
  const overlays = entry.overlays || [];
  const analysis = entry.analysis || { verdicts: [], diff: {} };
  const diff = analysis.diff || {};
  const sharedVerses = diff.shared_verses || [];
  const privates = diff.private || {};
  const seams = diff.seams || [];
  const hasPart = sharedVerses.length > 0 || seams.length > 0 || Object.keys(privates).some(k => (privates[k] || []).length);
  return (
    <div className="study-topic study-graph">
      <div className="study-editor-bar">
        <button className="study-back" onClick={onClose}>‹ {previewReader ? "Back" : "All graphs"}</button>
      </div>
      <div className="study-eyebrow">Argument graph</div>
      <h1 className="study-topic-title">{entry.title}</h1>
      <div className="study-topic-meta">{Object.keys(claims).length} claims · {overlays.length} {overlays.length === 1 ? "tradition" : "traditions"}</div>
      <div className="study-graph-caution">Maps reasoning, does not settle truth.</div>
      {entry.intro && <p className="study-topic-intro">{entry.intro}</p>}
      <GraphChart claims={claims} overlays={overlays} analysis={analysis} onNavigate={onNavigate} />
      {hasPart && (
        <div className="study-part">
          <div className="study-part-label">Where they part</div>
          <div className="study-part-row">
            <span className="study-part-key">Verses leaned on by more than one side:</span>{" "}
            {sharedVerses.length
              ? sharedVerses.map((cid, i) => <span key={i} className="study-part-chip">{(claims[cid] || {}).ref || cid}</span>)
              : <em className="study-verse-missing">they cite different verses</em>}
          </div>
          {seams.length > 0 && (
            <div className="study-part-row">
              <span className="study-part-key">Contested claims (one side leans on, another rejects):</span>
              <div className="study-part-privs">
                {seams.map((s, i) => (
                  <div className="study-part-priv" key={i}>
                    <ProvBadge prov={s.provenance} /> {s.body}
                    <span className="study-seam-who"> — held by {s.used_by.join(", ")}; rejected by {s.rejected_by.join(", ")}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {overlays.map((ov, i) => {
            const priv = privates[i] || [];
            if (!priv.length) return null;
            return (
              <div className="study-part-row" key={i}>
                <span className="study-part-key">{ov.tradition} adds:</span>
                <div className="study-part-privs">
                  {priv.map((cid, j) => (
                    <div className="study-part-priv" key={j}><ProvBadge prov={(claims[cid] || {}).provenance} /> {(claims[cid] || {}).text}</div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---- The Study tab --------------------------------------------------------
function StudyView({ admin, pending, onConsumed, onNavigateToLibrary }) {
  const adminUser = !!admin;
  const [module, setModule] = useState(() => {
    // Restore unconditionally: only an admin can ever set "graph" (the switch is admin-only), and
    // `admin` often isn't resolved yet on this first render — gating on it here fell back to Topics.
    try { return localStorage.getItem("lexica.study.module.v1") === "graph" ? "graph" : "topic"; } catch (e) { return "topic"; }
  });
  const [entries, setEntries] = useState(null);
  const [err, setErr] = useState(false);
  const [editing, setEditing] = useState(null);
  const [editMode, setEditMode] = useState(false);   // read vs edit (read-first for all types)
  const [previewReader, setPreviewReader] = useState(false);  // admin: preview the clean reader view
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [q, setQ] = useState("");
  // Capture the saved open-entry id ONCE at first render, BEFORE any effect runs — the persist
  // effect below clears the stored key on mount (nothing open yet), so reading it later in the
  // restore effect found it already gone. Holding it in a var dodges that ordering trap.
  const [initialOpen] = useState(() => { try { return localStorage.getItem("lexica.study.open.v1") || ""; } catch (e) { return ""; } });
  // A non-admin visitor IS the reader: published-only, no editing, no module switch
  // (only Topics are public). An admin can also opt into this view via "Preview as reader".
  const readerView = !adminUser || previewReader;

  const load = mod => {
    setEntries(null);
    api.studyEntries(mod).then(d => {
      if (d && d.entries) { setEntries(d.entries); setErr(false); }
      else setErr(true);
    });
  };
  useEffect(() => { load(module); }, [module]);

  const pickModule = m => { if (m === module) return; setEditing(null); setSavedAt(null); setQ(""); setModule(m); };

  const openEntry = id => {
    setSavedAt(null);
    api.studyEntry(id).then(d => {
      if (!d) return;
      if (isTopicLike(d.type)) {
        setEditing({ id: d.id, type: d.type, title: d.title || "", intro: d.intro || "",
          sections: (d.sections || []).map(s => ({ heading: s.heading || "", verses: s.verses || [] })),
          related: d.related || [], status: d.status || "draft", source: d.source || "" });
      } else {   // graph — read-only in this cut
        setEditing({ id: d.id, type: "graph", title: d.title || "", intro: d.intro || "",
          claims: d.claims || {}, overlays: d.overlays || [],
          analysis: d.analysis || { verdicts: [], diff: {} }, status: d.status || "draft" });
      }
      setEditMode(false);
    });
  };
  const newEntry = () => { setSavedAt(null); setEditMode(true); setEditing(blankTopic()); };   // only topics are authored in-app; graphs come from the script

  // Opened from the metaV sidebar: jump straight into a name-topic's page.
  useEffect(() => {
    if (pending) { openEntry(pending); if (onConsumed) onConsumed(); }
  }, [pending]);

  // Refresh-persistence: remember the sub-tab (Topics/Graphs) and the open entry, so a reload
  // lands you right back instead of resetting to Topics. Restored on mount; the sidebar
  // `pending` open wins if both are set. (StudyView mounts once — kept alive via display:none.)
  useEffect(() => { try { localStorage.setItem("lexica.study.module.v1", module); } catch (e) {} }, [module]);
  useEffect(() => {
    try {
      if (editing && editing.id) localStorage.setItem("lexica.study.open.v1", editing.id);
      else localStorage.removeItem("lexica.study.open.v1");
    } catch (e) {}
  }, [editing && editing.id]);
  useEffect(() => {
    if (pending) return;                        // a sidebar open wins over the restore
    if (initialOpen) openEntry(initialOpen);    // captured at first render, before the persist effect could clear it
  }, []);

  const save = () => {
    if (!editing || !editing.title.trim() || saving) return;   // only topic-like entries have an in-app editor
    setSaving(true);
    const payload = { ...editing, sections: editing.sections.map(s => ({ heading: s.heading, verses: s.verses.map(v => ({ ref: v.ref })) })) };
    api.studySave(payload).then(d => {
      setSaving(false);
      if (d && d.id) { setEditing(e => ({ ...e, id: d.id })); setSavedAt(Date.now()); load(module); }
    });
  };
  const del = () => {
    if (!editing || !editing.id) { setEditing(null); return; }
    if (!window.confirm("Delete this entry?")) return;
    api.studyDelete(editing.id).then(() => { setEditing(null); load(module); });
  };

  if (err) return <div className="stats-view"><div className="stats-empty">Couldn't load study content.{adminUser ? " (Admin sign-in required.)" : ""}</div></div>;

  if (editing) {
    const ro = readerView || !editMode;   // read-only: a reader/preview, or not actively editing
    const close = () => { setEditing(null); setSavedAt(null); };
    if (isTopicLike(editing.type))
      return <div className="study-view"><TopicPage entry={editing} editing={!ro} onChange={setEditing} onSave={save} onDelete={del} onClose={close} onToggleEdit={() => setEditMode(m => !m)} previewReader={readerView} saving={saving} savedAt={savedAt} onNavigate={onNavigateToLibrary} /></div>;
    return <div className="study-view"><GraphPage entry={editing} onClose={close} previewReader={readerView} onNavigate={onNavigateToLibrary} /></div>;
  }

  const isTopic = module === "topic";
  const moduleName = isTopic ? "Topics" : "Graphs";
  const qs = q.trim().toLowerCase();
  const pool = (entries || []).filter(e => !readerView || e.status === "published");   // a reader only sees published
  const sortKey = e => displayTitle(e.title || "").toLowerCase().replace(/^(?:the|a|an)\s+/, "");
  const shown = pool
    .filter(e => !qs || (e.title || "").toLowerCase().includes(qs) || displayTitle(e.title).toLowerCase().includes(qs) || (e.heldBy || "").toLowerCase().includes(qs))
    .sort((a, b) => sortKey(a).localeCompare(sortKey(b)));
  return (
    <div className="study-view">
      {adminUser && (
        <div className="study-sub">
          {STUDY_MODULES.map(m => (
            <button key={m.id} className={"study-sub-b" + (module === m.id ? " on" : "")} onClick={() => pickModule(m.id)}>{m.label}</button>
          ))}
          <button className={"study-preview-toggle" + (previewReader ? " on" : "")} onClick={() => setPreviewReader(p => !p)}
            title="See exactly what a reader sees — editing off, drafts hidden">
            {previewReader ? "✓ Previewing as reader" : "Preview as reader"}
          </button>
        </div>
      )}
      {previewReader && (
        <div className="study-preview-note">
          You're seeing what a reader sees — editing is off and drafts are hidden.
          <button className="study-preview-exit" onClick={() => setPreviewReader(false)}>Exit preview</button>
        </div>
      )}
      <div className="study-list-head">
        <h1 className="stats-title">{moduleName}</h1>
        {!readerView && isTopic && <button className="study-new" onClick={newEntry}>+ New topic</button>}
      </div>
      <div className="stats-sub">{isTopic
        ? "Browse a subject and its verses, grouped by subtopic. Mostly filled from MetaV — light edits only."
        : "Arguments as claims and links — each side's chain stress-tested to show where it actually load-bears."}</div>

      {pool.length > 0 && (
        <input className="study-search-input" type="text" value={q}
          placeholder={"Search " + moduleName.toLowerCase() + "…"} onChange={e => setQ(e.target.value)} />
      )}

      {entries === null ? (
        <div className="stats-empty">Loading…</div>
      ) : shown.length === 0 ? (
        <div className="stats-empty">{qs
          ? "No matches for “" + q + "”."
          : !adminUser
          ? "No study topics yet — check back soon."
          : previewReader
          ? "Nothing published yet — mark an entry Published to show it here."
          : isTopic
          ? "Nothing here yet — start with “+ New topic”. (Or import from MetaV.)"
          : "No graphs yet — add one with scripts/add_study_graph.py."}</div>
      ) : (
        <div className="study-rows">
          {shown.map(e => (
            <button className="study-row" key={e.id} onClick={() => openEntry(e.id)}>
              {!isTopic && <span className="study-badge study-badge--graph">Graph</span>}
              <span className="study-row-title">{isTopic ? displayTitle(e.title) : e.title}</span>
              <span className="study-row-n">{e.n || 0} {isTopic ? "verses" : "claims"}</span>
              {!readerView && e.status === "draft" && <span className="study-row-draft">draft</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
