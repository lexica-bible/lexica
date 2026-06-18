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

// One tradition's card: its conclusion, the verdict, the load-bearing joint, then the chain.
function OverlayCard({ overlay, verdict, claims, onNavigate }) {
  const v = verdict || { grounded: false, gap: false, load_bearing: [], soft_steps: [], objections: [] };
  const joints = new Set((v.load_bearing || []).map(linkKey));
  const cls = v.grounded ? "stands" : v.gap ? "gap" : "depends";
  const label = v.grounded ? "Stands on the text" : v.gap ? "Incomplete — a step is missing" : "Depends on non-solid joints";
  const chain = (overlay.links || []).filter(l => l.relation !== "undercuts");
  const objections = (overlay.links || []).filter(l => l.relation === "undercuts");
  return (
    <div className="study-overlay">
      <div className="study-overlay-head">{overlay.tradition}</div>
      <div className="study-overlay-thesis">{(claims[overlay.thesis] || {}).text || "(no conclusion set)"}</div>
      <div className={"study-verdict study-verdict--" + cls}>{label}</div>
      {(v.load_bearing || []).length > 0 && (
        <div className="study-joint-callout">
          <div className="study-joint-label">Load-bearing joint — cut this and the conclusion falls</div>
          {(v.load_bearing || []).map((l, i) => (
            <div className="study-joint" key={i}>
              <ClaimChip claim={claims[l.from]} onNavigate={onNavigate} />
              <div className="study-link-rel study-link-rel--weak">{l.relation} · {l.strength}</div>
              <ClaimChip claim={claims[l.to]} onNavigate={onNavigate} />
            </div>
          ))}
        </div>
      )}
      <div className="study-chain">
        {chain.map((l, i) => (
          <div className={"study-link study-link--" + l.strength + (joints.has(linkKey(l)) ? " study-link--joint" : "")} key={i}>
            <ClaimChip claim={claims[l.from]} onNavigate={onNavigate} />
            <div className={"study-link-rel study-link-rel--" + l.strength}>{l.relation} · {l.strength}</div>
            <ClaimChip claim={claims[l.to]} onNavigate={onNavigate} />
          </div>
        ))}
      </div>
      {objections.length > 0 && (
        <div className="study-objections">
          <div className="study-objections-label">Open objections (noted, not scored)</div>
          {objections.map((l, i) => (
            <div className="study-objection" key={i}>{l.note || ((claims[l.from] || {}).text + " — attacks the conclusion")}</div>
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
  const hasPart = sharedVerses.length > 0 || Object.keys(privates).some(k => (privates[k] || []).length);
  return (
    <div className="study-topic study-graph">
      <div className="study-editor-bar">
        <button className="study-back" onClick={onClose}>‹ {previewReader ? "Back" : "All graphs"}</button>
      </div>
      <div className="study-eyebrow">Argument graph</div>
      <h1 className="study-topic-title">{entry.title}</h1>
      <div className="study-topic-meta">{Object.keys(claims).length} claims · {overlays.length} {overlays.length === 1 ? "tradition" : "traditions"}</div>
      {entry.intro && <p className="study-topic-intro">{entry.intro}</p>}
      <div className="study-prov-key">
        <span className="study-prov study-prov--grounded">Grounded</span> stands on the text ·
        <span className="study-prov study-prov--added">Added</span> leans on tradition, inference or conjecture
      </div>
      {overlays.map((ov, i) => (
        <OverlayCard key={i} overlay={ov} verdict={(analysis.verdicts || [])[i]} claims={claims} onNavigate={onNavigate} />
      ))}
      {hasPart && (
        <div className="study-part">
          <div className="study-part-label">Where they part</div>
          <div className="study-part-row">
            <span className="study-part-key">Verses both lean on:</span>{" "}
            {sharedVerses.length
              ? sharedVerses.map((cid, i) => <span key={i} className="study-part-chip">{(claims[cid] || {}).ref || cid}</span>)
              : <em className="study-verse-missing">they cite different verses</em>}
          </div>
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
  const [module, setModule] = useState("topic");
  const [entries, setEntries] = useState(null);
  const [err, setErr] = useState(false);
  const [editing, setEditing] = useState(null);
  const [editMode, setEditMode] = useState(false);   // read vs edit (read-first for all types)
  const [previewReader, setPreviewReader] = useState(false);  // admin: preview the clean reader view
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const [q, setQ] = useState("");
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
