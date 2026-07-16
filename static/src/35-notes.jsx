// ============================================================
// NOTES UI — add popover, editor panel, browse view
// ------------------------------------------------------------
// Drag-select text in the Library reader → a small "Add note" bar pops by the
// selection → opens the editor panel (same right-sidebar / bottom-sheet slot
// the word-study and cross-ref panels use). The Notes tab lists & searches
// every saved note and jumps back to its verse.
// ============================================================

// "Add note" affordance for a text selection. On DESKTOP it floats just above
// the selection. On MOBILE the OS floats its own copy/share toolbar right there,
// so ours is pinned to the bottom of the screen (above the tab bar) to avoid the
// collision.
function NoteAddPopover({ rect, isMobile, onAdd, onColor, onCopy, onJournal }) {
  if (!rect) return null;
  let style;
  if (isMobile) {
    style = { position: "fixed", left: "50%", transform: "translateX(-50%)", bottom: 72, zIndex: 1000 };
  } else {
    const W = 360;
    style = {
      position: "fixed",
      top: Math.max(8, rect.top - 48),
      left: Math.min(window.innerWidth - W - 8, Math.max(8, rect.left + rect.width / 2 - W / 2)),
      zIndex: 1000,
    };
  }
  // preventDefault on mousedown so pressing a button doesn't clear the selection
  return (
    <div className={"note-popover" + (isMobile ? " note-popover-mobile" : "")} style={style} onMouseDown={(e) => e.preventDefault()}>
      <div className="note-swatches">
        {NOTE_COLORS.map(c => (
          <button key={c} className="note-swatch" style={{ background: NOTE_COLOR_CSS[c] }}
            title={"Highlight " + c} aria-label={"Highlight " + c} onClick={() => onColor(c)} />
        ))}
      </div>
      <button className="note-popover-btn" onClick={onAdd}><Icon.Note/><span className="note-btn-lbl">Note</span></button>
      {onJournal && <button className="note-popover-btn" onClick={onJournal}><Icon.Book/><span className="note-btn-lbl">Journal</span></button>}
      {onCopy && <button className="note-popover-btn" onClick={onCopy}><Icon.Copy/><span className="note-btn-lbl">Copy</span></button>}
    </div>
  );
}

// Menu shown when you right-click / long-press a verse number: Bookmark · Note · colors.
function VerseNoteMenu({ rect, isMobile, onBookmark, onNote, onColor, onCopy, onJournal, onClose }) {
  if (!rect) return null;
  let style;
  if (isMobile) {
    style = { position: "fixed", left: "50%", transform: "translateX(-50%)", bottom: 72, zIndex: 1000 };
  } else {
    const W = 270;
    style = {
      position: "fixed",
      top: Math.min(window.innerHeight - 56, rect.top + rect.height + 6),
      left: Math.min(window.innerWidth - W - 8, Math.max(8, rect.left)),
      zIndex: 1000,
    };
  }
  return (
    <>
      <div className="note-menu-scrim" onClick={onClose} />
      <div className={"note-popover" + (isMobile ? " note-popover-mobile" : "")} style={style} onMouseDown={(e) => e.preventDefault()}>
        <div className="note-swatches">
          {NOTE_COLORS.map(c => (
            <button key={c} className="note-swatch" style={{ background: NOTE_COLOR_CSS[c] }}
              title={"Highlight " + c} aria-label={"Highlight " + c} onClick={() => onColor(c)} />
          ))}
        </div>
        <button className="note-popover-btn" onClick={onNote}><Icon.Note/><span className="note-btn-lbl">Note</span></button>
        {onJournal && <button className="note-popover-btn" onClick={onJournal}><Icon.Book/><span className="note-btn-lbl">Journal</span></button>}
        {onCopy && <button className="note-popover-btn" onClick={onCopy}><Icon.Copy/><span className="note-btn-lbl">Copy</span></button>}
        <button className="note-popover-btn" onClick={onBookmark}><Icon.Bookmark/><span className="note-btn-lbl">Bookmark</span></button>
      </div>
    </>
  );
}

// A row of color swatches + a clear button, for the editor.
function NoteColorRow({ value, onPick }) {
  return (
    <div className="note-color-row">
      {NOTE_COLORS.map(c => (
        <button key={c}
          className={"note-swatch" + (value === c ? " on" : "")}
          style={{ background: NOTE_COLOR_CSS[c] }}
          title={"Highlight " + c} aria-label={"Highlight " + c}
          onClick={() => onPick(value === c ? null : c)} />
      ))}
      <button className={"note-swatch note-swatch-none" + (!value ? " on" : "")}
        title="No highlight" aria-label="No highlight" onClick={() => onPick(null)}>✕</button>
    </div>
  );
}

// Shared editor state for a single note — used by BOTH the Library rail panel
// (NotesPanel) AND the Notes-tab center editor (NoteCenterEditor), so the two
// can never drift. onClose is the caller's "done" (close the panel / deselect).
function useNoteEditor(noteId, isMobile, onClose) {
  const note = NotesStore.get(noteId);
  const [body, setBody] = useState(note ? (note.body || "") : "");
  const [color, setColor] = useState(note ? (note.color || null) : null);
  const [bookmark, setBookmark] = useState(note ? !!note.bookmark : false);
  const taRef = useRef(null);

  useEffect(() => {
    setBody(note ? (note.body || "") : "");
    setColor(note ? (note.color || null) : null);
    setBookmark(note ? !!note.bookmark : false);
    // Desktop: focus the box right away. Mobile: DON'T — auto-popping the
    // on-screen keyboard covers a freshly opened sheet. The user taps to type.
    if (!isMobile) requestAnimationFrame(() => taRef.current && taRef.current.focus());
  }, [noteId]);

  const save = () => { NotesStore.update(noteId, { body, color, bookmark }); onClose(); };
  const del = () => { NotesStore.remove(noteId); onClose(); };
  // Closing a record that's blank AND uncolored AND not bookmarked discards it
  // (id minted on create, so a thrown-away draft shouldn't linger).
  const close = () => {
    if (!body.trim() && !color && !bookmark) NotesStore.remove(noteId);
    else NotesStore.update(noteId, { body, color, bookmark });
    onClose();
  };

  return { note, body, setBody, color, setColor, bookmark, setBookmark, taRef, save, del, close };
}

// The editor fields (quoted snippet + color row + textarea + Save/Delete). scrollRef
// = the mobile swipe-to-dismiss scroll container (desktop leaves it undefined).
// hideSnippet drops the quoted-selection block — the Notes-tab center passes it so the
// anchored verse lives ONLY in the right rail (inspect covenant); the Library rail keeps it.
function NoteEditFields({ ed, scrollRef, hideSnippet }) {
  return (
    <div className="detail-body note-edit-body" ref={scrollRef}>
      {!hideSnippet && ed.note.snippet && <blockquote className="note-snippet">“{ed.note.snippet}”</blockquote>}
      <NoteColorRow value={ed.color} onPick={ed.setColor} />
      <textarea
        ref={ed.taRef}
        className="note-textarea"
        value={ed.body}
        onChange={(e) => ed.setBody(e.target.value)}
        placeholder="Write your note…"
      />
      <div className="note-actions">
        <button className="note-save" onClick={ed.save}>Save</button>
        <button className="note-del" onClick={ed.del}>Delete</button>
      </div>
    </div>
  );
}

// Write / edit / delete a single note in the Library rail (desktop aside / mobile sheet).
function NotesPanel({ noteId, isMobile, onClose }) {
  const ed = useNoteEditor(noteId, isMobile, onClose);
  // Swipe-down-to-close on mobile (same hook the word / xref / summary sheets use).
  const { sheetRef, scrollRef } = useSwipeToDismiss(ed.close);

  if (!ed.note) return null;
  const note = ed.note;

  const head = (
    <div className="detail-head">
      <div className="detail-head-l">
        <span className="detail-pos summary-pos">{note.refLabel || (note.book + " " + note.chapter)}</span>
      </div>
      <button className={"note-bm-toggle" + (ed.bookmark ? " on" : "")} onClick={() => ed.setBookmark(b => !b)}
        title={ed.bookmark ? "Bookmarked" : "Bookmark this"} aria-label="Toggle bookmark" aria-pressed={ed.bookmark}>
        <Icon.Bookmark/>
      </button>
      {!isMobile && <button className="detail-close" onClick={ed.close} aria-label="Close"><Icon.Close/></button>}
    </div>
  );

  if (isMobile) {
    return (
      <>
        <div className="sheet-scrim" onClick={ed.close}/>
        <aside ref={sheetRef} className="detail detail-sheet note-sheet" role="dialog" aria-label="Note">
          <div className="sheet-drag-zone" aria-hidden="true"><div className="sheet-handle"></div></div>
          {head}
          <NoteEditFields ed={ed} scrollRef={scrollRef} />
        </aside>
      </>
    );
  }
  return (
    <aside className="detail zinspect detail-side note-side" role="complementary" aria-label="Note">
      {head}
      <NoteEditFields ed={ed} />
    </aside>
  );
}

// DESKTOP Notes tab — the selected note open in the center column (edit in place;
// the anchored verse rides along in the right rail). Reuses the same editor fields
// as the Library rail, so they can't drift.
function NoteCenterEditor({ noteId, onClose, onReadInContext }) {
  const ed = useNoteEditor(noteId, false, onClose);
  if (!ed.note) return null;
  const note = ed.note;
  const canRead = note.corpus === "bible" && note.start;
  return (
    <div className="note-center">
      <div className="note-center-head">
        <span className="note-center-ref">{note.refLabel || (note.book + " " + note.chapter)}</span>
        <div className="note-center-tools">
          {canRead && (
            <button className="note-read-link" onClick={() => onReadInContext(note.book, note.chapter, note.start.verse)}>
              Read in context ›
            </button>
          )}
          <button className={"note-bm-toggle" + (ed.bookmark ? " on" : "")} onClick={() => ed.setBookmark(b => !b)}
            title={ed.bookmark ? "Bookmarked" : "Bookmark this"} aria-label="Toggle bookmark" aria-pressed={ed.bookmark}>
            <Icon.Bookmark/>
          </button>
          <button className="detail-close" onClick={ed.close} aria-label="Close"><Icon.Close/></button>
        </div>
      </div>
      <NoteEditFields ed={ed} hideSnippet />
    </div>
  );
}

// DESKTOP Notes tab — the right inspect rail: the note's anchored verse(s) + one verse of
// context each side, kept in view while you write. The anchor is emphasized, the neighbors
// dimmed. Reuses the reader's shared VerseRow. Depth-1, no drill. Journal / non-Bible notes
// have no anchor, so it shows an empty state.
// A note anchors a RANGE (60-library.jsx resolveSelection stores start.verse + end.verse from
// the two edges of a drag-select), so "the anchor" is every verse from start to end — all of it
// the note's own text — and the neighbors sit outside the WHOLE range. The two decisions here
// are pure and live in 34-notes-logic.jsx, under test in tests/test_note_inspect.js.
function NoteVerseInspect({ note, onReadInContext }) {
  const anchored = note && note.corpus === "bible" && note.start;
  const lo = anchored ? note.start.verse : 0;
  // An older note, or one from the verse-number menu, has end === start; a note with no `end`
  // at all reads as single rather than blowing up.
  const hi = anchored ? Math.max(lo, (note.end && note.end.verse) || lo) : 0;
  const multi = hi > lo;
  // A full header-height band clears the navy header (the inspect floats top:0, unified
  // with News / Word study). Band title = the verse ref when anchored, else a caption.
  // The refLabel the write path stores is ALREADY a range ("John 4:21–23", :1073); the fallback
  // matches it, en-dash and all, for a note that somehow lacks one.
  const label = anchored
    ? (note.refLabel || `${note.book} ${note.chapter}:${lo}${multi ? `–${hi}` : ""}`)
    : "Anchored verse";
  // heb/bsb/kjv notes show in their own text; everything else is ABP.
  const tm = anchored && ["kjv", "bsb", "heb"].includes(note.translation) ? note.translation : "abp";

  // Learn the chapter's last verse so we never render an empty out-of-range "next" row.
  // On any miss we fall back to the range's LAST verse → the next neighbor simply stays hidden.
  const [lastVerse, setLastVerse] = useState(null);
  useEffect(() => {
    if (!anchored) { setLastVerse(null); return; }
    let cancelled = false;
    setLastVerse(null);
    api.chapter(note.book, note.chapter)
      .then(d => { if (!cancelled) setLastVerse(noteInspLastVerse(d, hi)); })
      .catch(() => { if (!cancelled) setLastVerse(hi); });
    return () => { cancelled = true; };
  }, [anchored, note && note.book, note && note.chapter, hi]);

  // Each anchor row is labelled with its OWN ref once there's more than one — the band already
  // carries the range, and stamping "John 4:21–23" on the row that is only verse 21 is what the
  // panel used to do. A single-verse note keeps the stored refLabel exactly as it shipped.
  const anchorLabel = (vs) => (multi ? `${note.bookName || note.book} ${note.chapter}:${vs}` : label);
  const row = (vs, kind) => (
    <div className={"note-insp-v note-insp-" + kind} key={vs}>
      <VerseRow book={note.book} chapter={note.chapter} verse={vs}
        label={kind === "anchor" ? anchorLabel(vs) : `${note.book} ${note.chapter}:${vs}`}
        textMode={tm}
        onReadInContext={kind === "anchor" && vs === lo ? onReadInContext : undefined} />
    </div>
  );

  // A truly-empty state renders the BARE ZoneEmpty — no band, and no wrapper either. The shared
  // `.zinspect .zempty::before` ALREADY draws the header-continuation line at var(--hdr-h), so a
  // band above it paints a SECOND rule with a dead gap between (measured: band border y=66,
  // cross-line y=148, 82px of nothing). Ask-corpus's `inspectIdle` solved it the same way.
  // The ZoneEmpty must be the DIRECT child of `.zinspect`: that `::before` is positioned against
  // the .zempty box, so wrapping it in `.note-insp-scroll` (padding: 16px …) slides the one
  // divider 16px below the header line it exists to continue. The band earns its place only when
  // it has something to say — the verse ref.
  if (!anchored) {
    return (
      <ZoneEmpty icon={<Icon.Note width="30" height="30"/>} title="No verse anchored"
        sub="Journal pages and imported notes aren’t tied to a verse, so nothing shows here." />
    );
  }
  return (
    <div className="note-insp">
      <div className="note-insp-band sh-band">{label}</div>
      <div className="note-insp-scroll">
        <div className="note-insp-ctx">
          {noteInspRows(lo, hi, lastVerse).map(r => row(r.verse, r.kind))}
        </div>
      </div>
    </div>
  );
}

// One free-form journal page (plain text). No verse anchor — a title + a big
// box you type into. Autosaves as you write; rides the same store/sync as notes.
const JOURNAL_MAX = 60000;   // chars; stays safely under the server's 64KB page cap
function JournalEditor({ pageId, onBack }) {
  const page = NotesStore.get(pageId);
  const [title, setTitle] = useState(page ? (page.title || "") : "");
  const [body, setBody] = useState(page ? (page.body || "") : "");
  const saveTimer = useRef(null);
  const first = useRef(true);

  // This is now the page that "send verse to journal" (in the reader) targets.
  useEffect(() => { NotesStore.setActiveJournal(pageId); }, [pageId]);

  // Autosave ~0.8s after you stop typing. Skip the very first run so just
  // opening a page doesn't re-stamp it as edited.
  useEffect(() => {
    if (first.current) { first.current = false; return; }
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => { NotesStore.update(pageId, { title, body }); }, 800);
    return () => clearTimeout(saveTimer.current);
  }, [title, body]);

  const back = () => {
    clearTimeout(saveTimer.current);
    // A page never given a title or any text is a thrown-away draft — discard it.
    if (!title.trim() && !body.trim()) NotesStore.remove(pageId);
    else NotesStore.update(pageId, { title, body });
    onBack();
  };
  const del = () => { clearTimeout(saveTimer.current); NotesStore.remove(pageId); onBack(); };

  if (!page) { onBack(); return null; }
  const near = body.length > JOURNAL_MAX - 2000;

  return (
    <div className="journal-editor">
      <div className="journal-editor-bar">
        <button className="notes-tool-btn" onClick={back}>‹ Back</button>
        <button className="note-del" onClick={del}>Delete</button>
      </div>
      <input
        className="journal-title-input"
        type="text"
        value={title}
        maxLength={200}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Page title"
      />
      <textarea
        className="journal-textarea"
        value={body}
        maxLength={JOURNAL_MAX}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Write freely — thoughts, questions, an outline, a study…"
      />
      <div className={"journal-count" + (near ? " warn" : "")}>
        {body.length.toLocaleString()} characters{near ? " — near the page limit; start a new page for more" : ""}
      </div>
    </div>
  );
}

// The list of free-form journal pages + a "New page" button. The shell's rail on desktop,
// the list sheet on mobile.
function JournalList({ editingId, onOpen, onNew }) {
  useNotesVersion();
  const pages = NotesStore.journals();
  const fmtDate = (iso) => { try { return new Date(iso).toLocaleDateString(); } catch (e) { return ""; } };
  return (
    <div className="journal-view">
      <div className="journal-toolbar">
        <button className="notes-tool-btn on" onClick={onNew}>+ New page</button>
      </div>
      {pages.length === 0 ? (
        <div className="notes-empty">No journal pages yet. Tap “New page” to start writing — free-form, not tied to any verse.</div>
      ) : (
        <ul className="journal-list">
          {pages.map(p => (
            <li key={p.id} className={"journal-item listrow" + (p.id === editingId ? " on" : "")} onClick={() => onOpen(p.id)}>
              <div className="journal-item-title">{(p.title || "").trim() || "Untitled page"}</div>
              {(p.body || "").trim() && <div className="journal-item-preview">{p.body.trim().slice(0, 160)}</div>}
              <div className="journal-item-date">{fmtDate(p.updated)}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// (There was a self-contained JournalView here — the mobile journal's list-swaps-to-editor
// page, from when mobile Notes had no center of its own. The shell gives it one, so mobile
// composes JournalList + JournalEditor across the zones exactly like desktop, and the
// separate mobile-only journal is gone rather than left to drift from the desktop one.)

// The Notes tab, on the shared three-zone Shell (rail = note index · strip = search/filter ·
// center = editor · right = the anchored verse). Mobile collapses the rail + inspect behind
// the bottom toolbar as sheets; the center (the editor) stays inline. News + Ask-corpus are
// the reference consumers — docs/claude/frontend.md, "Shell's MOBILE collapse".
function NotesView({ isMobile, onReadInContext }) {
  useNotesVersion();
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("all");   // all | bookmark | highlight | note
  const [sort, setSort] = useState("recent");     // recent | ref
  const [group, setGroup] = useState(false);      // group by book
  const [collapsed, setCollapsed] = useState(() => new Set());   // collapsed book keys
  const toggleSection = (key) => setCollapsed(s => { const n = new Set(s); n.has(key) ? n.delete(key) : n.add(key); return n; });
  const [mode, setMode] = useState("notes");        // notes | journal
  const [selectedId, setSelectedId] = useState(null);   // note open in the center editor
  const [journalEditing, setJournalEditing] = useState(null);   // journal page in the center
  const [mSheet, setMSheet] = useState(null);       // mobile: which zone is open — list | inspect
  let notes = NotesStore.search(q);               // already newest-first
  if (filter === "bookmark") notes = notes.filter(n => n.bookmark);
  else if (filter === "highlight") notes = notes.filter(n => n.color);
  else if (filter === "note") notes = notes.filter(n => n.body && n.body.trim());

  // Canonical order: Bible books by BOOK_ORDER, non-canon after, by name.
  const bookRank = (n) => (BOOK_ORDER[n.book] != null ? BOOK_ORDER[n.book] : 1000);
  const byRef = (a, b) => {
    const ra = bookRank(a), rb = bookRank(b);
    if (ra !== rb) return ra - rb;
    const na = a.bookName || a.book, nb = b.bookName || b.book;
    if (ra === 1000 && na !== nb) return na.localeCompare(nb);
    if (a.chapter !== b.chapter) return a.chapter - b.chapter;
    return a.start.verse - b.start.verse;
  };
  if (sort === "ref") notes = [...notes].sort(byRef);

  // Optional grouping by book (sections in canonical order, items by reference).
  let sections = null;
  if (group) {
    const map = new Map();
    for (const n of notes) {
      if (!map.has(n.book)) map.set(n.book, { key: n.book, label: BOOK_LABELS[n.book] || n.bookName || n.book, rank: bookRank(n), items: [] });
      map.get(n.book).items.push(n);
    }
    sections = [...map.values()].sort((a, b) => (a.rank - b.rank) || a.label.localeCompare(b.label));
    sections.forEach(s => s.items.sort(byRef));
  }

  // A note opens in the CENTER editor on both. Mobile used to jump to the Library's editor
  // instead — that was the workaround for having no center of its own; the shell gives it one,
  // and the jump survives as the editor's explicit "Read in context ›". Picking one closes the
  // list sheet, so the tap lands you on what you picked.
  const openItem = (n) => { setSelectedId(n.id); setMSheet(null); };

  const renderItem = (n) => (
    <li key={n.id} className={"notes-item listrow" + (n.id === selectedId ? " on" : "")} onClick={() => openItem(n)}>
      <div className="notes-item-ref">
        {(n.body || n.bookmark) && (
          <span className="notes-item-type" aria-hidden="true">{n.body ? <Icon.Note/> : <Icon.Bookmark/>}</span>
        )}
        {n.color && <span className="notes-item-dot" style={{ background: NOTE_COLOR_CSS[n.color] }} />}
        {n.refLabel || (n.book + " " + n.chapter)}
      </div>
      {/* The row previews the NOTE, not the verse — this list holds notes, so the row names
          its own content (JP, shape 2). It used to print the full verse quote AND the body,
          so a row could run five or six lines and the thing you actually wrote came last.
          A bare highlight or bookmark has no body, so it falls back to the verse snippet —
          one line of it, not the whole quote, or the fallback grows back into the problem. */}
      {n.body && n.body.trim()
        ? <div className="notes-item-body">{n.body}</div>
        : n.snippet ? <div className="notes-item-snippet">“{n.snippet}”</div> : null}
    </li>
  );

  // ── Shared fragments ──────────────────────────────────────────────────────
  const modeSeg = (
    <div className="notes-mode seg seg--line">
      <button className={"seg-b" + (mode === "notes" ? " on" : "")} onClick={() => setMode("notes")}>Verse notes</button>
      <button className={"seg-b" + (mode === "journal" ? " on" : "")} onClick={() => setMode("journal")}>Journal</button>
    </div>
  );

  const notesControls = (
    <>
      <input className="notes-search" type="text" placeholder="Search your notes…" value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="notes-controls">
        <div className="notes-filter seg seg--line">
          {[["all", "All"], ["bookmark", "★ Bookmarks"], ["highlight", "🎨 Highlights"], ["note", "✎ Notes"]].map(([k, lbl]) => (
            <button key={k} className={"seg-b" + (filter === k ? " on" : "")} onClick={() => setFilter(k)}>{lbl}</button>
          ))}
        </div>
        {/* Two different jobs run together here — WHICH notes (filter) and IN WHAT ORDER
            (sort). Word study's strip already separates its groups this way, so reuse its
            divider rather than mint a second one. */}
        <span className="filters-sep"/>
        <div className="seg seg--line">
          <button className={"seg-b" + (sort === "recent" ? " on" : "")} onClick={() => setSort("recent")}>Recent</button>
          <button className={"seg-b" + (sort === "ref" ? " on" : "")} onClick={() => setSort("ref")}>Reference</button>
        </div>
        <button className={"notes-tool-btn" + (group ? " on" : "")} onClick={() => setGroup(g => !g)}>Group by book</button>
      </div>
    </>
  );

  const notesListContent = notes.length === 0 ? (
    <div className="notes-empty">
      {q || filter !== "all"
        ? "Nothing matches that."
        : "No notes yet. In the Library, select some text in a verse and choose “Add note.”"}
    </div>
  ) : group ? (
    sections.map(s => {
      const open = !collapsed.has(s.key);
      return (
        <div key={s.key} className="notes-group">
          <button className={"notes-group-head" + (open ? " open" : "")} onClick={() => toggleSection(s.key)} aria-expanded={open}>
            <span className="notes-group-caret">▸</span>
            <span className="notes-group-label">{s.label}</span>
            <span className="notes-group-count">{s.items.length}</span>
          </button>
          {open && <ul className="notes-list">{s.items.map(renderItem)}</ul>}
        </div>
      );
    })
  ) : (
    <ul className="notes-list">{notes.map(renderItem)}</ul>
  );

  // ── The zone contents, shared by BOTH branches ────────────────────────────
  const selNote = selectedId ? NotesStore.get(selectedId) : null;
  const newJournalPage = () => { const p = NotesStore.createJournal(); setJournalEditing(p.id); setMSheet(null); };
  const openPage = (id) => { setJournalEditing(id); setMSheet(null); };

  const railBody = mode === "journal"
    ? <JournalList editingId={journalEditing} onOpen={openPage} onNew={newJournalPage} />
    : notesListContent;

  // "Pick a note from the list" is true on DESKTOP, where the list is open beside the center —
  // an empty one saying "No notes yet. In the Library, select some text…" right there. The
  // mobile collapse puts the list behind a button, so for a reader with NOTHING saved that
  // line points at an empty room and buries the only real first step one tap away. Same room,
  // different reachability: the phone's center has to carry the first step itself.
  const anyNotes = NotesStore.all().length > 0;
  const noteEmpty = (isMobile && !anyNotes)
    ? <ZoneEmpty icon={<Icon.Note width="30" height="30"/>} title="No notes yet"
        sub="In the Library, select some text in a verse and choose “Add note.” Everything you save collects here." />
    : <ZoneEmpty icon={<Icon.Note width="30" height="30"/>} title="No note open" sub="Pick a note from the list to read and edit it here." />;

  const centerContent = mode === "journal"
    ? (journalEditing
        ? <JournalEditor key={journalEditing} pageId={journalEditing} onBack={() => setJournalEditing(null)} />
        : <ZoneEmpty icon={<Icon.Book width="30" height="30"/>} title="No page open" sub="Pick a page from the list, or start a new one." />)
    : (selectedId
        ? <NoteCenterEditor key={selectedId} noteId={selectedId} onClose={() => setSelectedId(null)} onReadInContext={onReadInContext} />
        : noteEmpty);

  // Journal mode's inspect is empty BY DESIGN (pages have no verse anchor, ever), so it takes
  // the same bare-ZoneEmpty shape as NoteVerseInspect's empty state — no band, one divider.
  // The band said "Journal" directly above a ZoneEmpty titled "Journal": a second rule, a dead
  // gap, and the panel's name printed twice.
  const inspectContent = mode === "journal"
    ? <ZoneEmpty icon={<Icon.Book width="30" height="30"/>} title="Journal" sub="Journal pages aren’t tied to a verse, so nothing shows here." />
    : <NoteVerseInspect note={selNote} onReadInContext={onReadInContext} />;

  // ── MOBILE: the shared Shell's collapse (News + Ask-corpus are the pattern) ─
  if (isMobile) {
    // TWO zones collapse: the list and the anchored-verse inspect. The mode seg is NOT one —
    // it's a mode switch, and it decides what the list button below even means, so it has to
    // stay visible while the bar is. It rides the center strip.
    //
    // The list's search + filters come WITH the list into its sheet. Desktop can leave them in
    // the center strip because the rail sits open beside them; here the list is behind a bar
    // button, so a filter in the center would drive a list you can't see.
    const listSheet = mode === "journal" ? railBody : <>{notesControls}{railBody}</>;
    // The list button is content-named — the last row of the icon matrix, per-tab BY RULING
    // (docs/claude/frontend.md). What this list holds changes with the mode, so the name and
    // the glyph change with it: verse notes are notes (the pencil), journal pages are pages
    // (the book — the tab's OWN journal vocabulary, cf. the journal ZoneEmpty above). One
    // fixed glyph would have to be wrong in one of the two modes.
    const listLabel = mode === "journal" ? "Journal pages" : "Verse notes";
    // The inspect GRAYS, never hides — a real zone that doesn't apply right now. Three ways it
    // doesn't apply: no note picked yet, the picked note has no verse anchor (imported /
    // journal), or Journal mode, where the zone is empty BY DESIGN and not just "empty yet".
    const inspectApplies = mode === "notes" && !!(selNote && selNote.corpus === "bible" && selNote.start);
    const tools = [
      { key: "list", label: listLabel, icon: mode === "journal" ? <Icon.Book/> : <Icon.Note/>,
        on: mSheet === "list", onTap: () => setMSheet(s => (s === "list" ? null : "list")) },
      { key: "inspect", label: "Anchored verse", icon: <Icon.Panel/>, disabled: !inspectApplies,
        on: mSheet === "inspect", onTap: () => setMSheet(s => (s === "inspect" ? null : "inspect")) },
    ];
    return (
      <Shell
        isMobile={true}
        className="notes-frame notes-m"
        center={
          <>
            <div className="notes-mstrip">{modeSeg}</div>
            <div className="notes-center-body">{centerContent}</div>
          </>
        }
        mobile={{
          tools,
          // Inspect goes in BARE: .note-insp carries its own header band + its own scroll box,
          // so the padded .zsheet-body would nest a second scroll box and collapse the fill.
          // Its band already names the panel (the verse ref), so it takes no sheetTitle — the
          // band IS the header, and adding one would print the name twice. The list is plain
          // content -> normal body. (frontend.md, the bare-sheet + doubled-header rules.)
          sheet: mSheet === "list" ? listSheet
               : mSheet === "inspect" ? inspectContent : null,
          sheetBare: mSheet === "inspect",
          sheetTitle: mSheet === "list" ? listLabel : null,
          onCloseSheet: () => setMSheet(null),
        }}
      />
    );
  }

  // ── DESKTOP: the shared three-zone Shell ──────────────────────────────────
  return (
    <>
      <Shell
        isMobile={false}
        className="notes-frame"
        centerClass="notes-center"
        rail={
          <>
            <div className="notes-rail-top">{modeSeg}</div>
            <div className="notes-rail-scroll">{railBody}</div>
          </>
        }
        center={
          <>
            {mode === "notes" && <div className="notes-strip">{notesControls}</div>}
            <div className="notes-center-body">{centerContent}</div>
          </>
        }
        inspect={<aside className="zinspect notes-inspect">{inspectContent}</aside>}
      />
    </>
  );
}

// Account / options panel — opened from the signed-in email in the Notes header.
// Holds account actions (log out) + reading-plan progress management. Built to grow:
// new account-level options drop in as more .acct-sec blocks.
const PLAN_TEXT_LABELS = { abp: "ABP", kjv: "KJV", bsb: "BSB", esv: "ESV", niv: "NIV" };
function AccountModal({ onClose, anchored }) {
  useNotesVersion();   // re-render after a clear (NotesStore.clearPlan notifies)
  const acct = NotesStore.authInfo();
  const plan = planLoadAll();
  const rows = Object.keys(plan)
    .map(k => ({ text: k, done: (plan[k] && Array.isArray(plan[k].done)) ? plan[k].done.length : 0 }))
    .filter(r => r.done > 0)
    .sort((a, b) => a.text.localeCompare(b.text));
  const label = (t) => PLAN_TEXT_LABELS[t] || t.toUpperCase();
  const clearOne = (t) => { if (window.confirm(`Clear your ${label(t)} reading-plan progress?`)) NotesStore.clearPlan(t); };
  const clearAll = () => { if (window.confirm("Clear ALL reading-plan progress (every text)?")) NotesStore.clearPlan("*"); };
  const [pw, setPw] = useState("");
  const [pwMsg, setPwMsg] = useState("");
  const [pwBusy, setPwBusy] = useState(false);
  const savePw = async () => {
    if (pwBusy) return;
    if (!pw || pw.length < 8) { setPwMsg("At least 8 characters."); return; }
    setPwBusy(true); setPwMsg("");
    const r = await NotesStore.setPassword(pw);
    setPwBusy(false);
    setPwMsg(r.ok ? "Password updated." : (r.error || "Couldn't update."));
    if (r.ok) setPw("");
  };
  const [nm, setNm] = useState(acct.name || "");
  const [nmMsg, setNmMsg] = useState("");
  const [nmBusy, setNmBusy] = useState(false);
  const saveNm = async () => {
    if (nmBusy) return;
    setNmBusy(true); setNmMsg("");
    const r = await NotesStore.setName(nm);
    setNmBusy(false);
    setNmMsg(r.ok ? (nm.trim() ? "Saved." : "Name cleared.") : (r.error || "Couldn't save."));
  };
  const [pwOpen, setPwOpen] = useState(false);     // password section collapsed behind a muted link too
  const [delOpen, setDelOpen] = useState(false);   // collapsed by default — a muted link expands the section
  const [delArm, setDelArm] = useState(false);
  const [delText, setDelText] = useState("");
  const [delBusy, setDelBusy] = useState(false);
  const [delMsg, setDelMsg] = useState("");
  const deleteAcct = async () => {
    if (delBusy) return;
    if (delText.trim().toLowerCase() !== "delete") { setDelMsg('Type "delete" to confirm.'); return; }
    setDelBusy(true); setDelMsg("");
    const r = await NotesStore.deleteAccount();
    setDelBusy(false);
    if (r.ok) onClose();
    else setDelMsg(r.error || "Couldn't delete the account.");
  };
  return (
    <>
      <div className={anchored ? "acct-pop-scrim" : "auth-scrim"} onClick={onClose} />
      <div className={"auth-modal" + (anchored ? " acct-pop" : "")} role="dialog" aria-modal={anchored ? undefined : "true"} aria-label="Account and options">
        <div className="auth-modal-head">
          <h3 className="auth-modal-title">Account</h3>
          <button className="detail-close" onClick={onClose} aria-label="Close"><Icon.Close/></button>
        </div>
        <p className="auth-modal-sub">{acct.name ? <>{acct.name} · {acct.email}</> : acct.email}</p>

        <div className="acct-sec">
          <div className="acct-sec-h">Display name</div>
          <div className="acct-pw-row">
            <input className="auth-input" type="text" placeholder="Optional — shown instead of your email"
              value={nm} maxLength={40} onChange={(e) => setNm(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") saveNm(); }} />
            <button className="acct-plan-clear" onClick={saveNm} disabled={nmBusy || nm.trim() === (acct.name || "").trim()}>{nmBusy ? "…" : "Save"}</button>
          </div>
          {nmMsg && <div className="auth-fine">{nmMsg}</div>}
          <div className="acct-empty">Leave blank to show your email instead.</div>
        </div>

        <div className="acct-sec">
          <div className="acct-sec-h">Reading plan progress</div>
          {rows.length === 0 ? (
            <div className="acct-empty">No reading-plan progress yet.</div>
          ) : (
            <ul className="acct-plan-list">
              {rows.map(r => (
                <li key={r.text} className="acct-plan-row">
                  <span className="acct-plan-name">{label(r.text)}</span>
                  <span className="acct-plan-count">{r.done} {r.done === 1 ? "day" : "days"} read</span>
                </li>
              ))}
            </ul>
          )}
          {rows.length >= 1 && (
            <button className="acct-plan-clearall" onClick={clearAll}>{rows.length > 1 ? "Clear all progress" : "Clear progress"}</button>
          )}
        </div>

        <div className="acct-sec">
          {!pwOpen ? (
            <button className="acct-plan-clearall" onClick={() => { setPwOpen(true); setPwMsg(""); }}>Set or change password…</button>
          ) : (
            <>
              <div className="acct-sec-h">Password</div>
              <div className="acct-pw-row">
                <input className="auth-input" type="password" placeholder="New password" autoComplete="new-password" autoFocus
                  value={pw} onChange={(e) => setPw(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") savePw(); }} />
                <button className="acct-plan-clear" onClick={savePw} disabled={pwBusy || !pw.trim()}>{pwBusy ? "…" : "Set"}</button>
              </div>
              {pwMsg && <div className="auth-fine">{pwMsg}</div>}
              <div className="acct-empty">Set a password to also sign in without Google.</div>
              <button className="acct-plan-clearall" onClick={() => { setPwOpen(false); setPw(""); setPwMsg(""); }}>Cancel</button>
            </>
          )}
        </div>

        {acct.role === "user" && (
          <div className="acct-sec">
            <div className="acct-sec-h">Support Lexica</div>
            <div className="acct-empty">Lexica is free and built by one person. If it's useful to you, a small tip on Ko-fi helps keep it running.</div>
            <a className="donate-btn kofi acct-kofi" href="https://ko-fi.com/lexica" target="_blank" rel="noopener noreferrer">☕ Support on Ko-fi</a>
          </div>
        )}

        <button className="notes-tool-btn acct-logout-btn" onClick={() => { NotesStore.logout(); onClose(); }}>Log out</button>

        <div className="acct-sec acct-danger-sec">
          {!delOpen ? (
            <button className="acct-danger-link" onClick={() => { setDelOpen(true); setDelArm(false); setDelText(""); setDelMsg(""); }}>Delete account…</button>
          ) : (
            <>
              <div className="acct-sec-h">Delete account</div>
              <div className="acct-empty">Permanently removes your account and everything saved to it — notes, highlights, bookmarks and reading-plan progress. No undo.</div>
              {!delArm ? (
                <button className="acct-delete" onClick={() => { setDelArm(true); setDelMsg(""); setDelText(""); }}>Delete my account</button>
              ) : (
                <div className="acct-del-confirm">
                  <div className="acct-empty">Type <b>delete</b> to confirm:</div>
                  <div className="acct-pw-row">
                    <input className="auth-input" type="text" autoFocus placeholder="delete" autoComplete="off"
                      value={delText} onChange={(e) => setDelText(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") deleteAcct(); }} />
                    <button className="acct-delete" onClick={deleteAcct}
                      disabled={delBusy || delText.trim().toLowerCase() !== "delete"}>
                      {delBusy ? "Deleting…" : "Delete"}
                    </button>
                  </div>
                </div>
              )}
              {delMsg && <div className="auth-fine">{delMsg}</div>}
              <button className="acct-plan-clearall" onClick={() => { setDelOpen(false); setDelArm(false); setDelText(""); setDelMsg(""); }}>Cancel</button>
            </>
          )}
        </div>
      </div>
    </>
  );
}

// Centered login / sign-up dialog.
// modes: "login" | "signup" | "forgot" (email me a reset link) | "reset" (set a new
// password from a link's token, passed in resetToken).
function AuthModal({ mode, onClose, resetToken }) {
  const [m, setM] = useState(mode);
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [err, setErr] = useState("");
  const [sent, setSent] = useState(false);   // forgot-password confirmation shown
  const [busy, setBusy] = useState(false);
  const [gid, setGid] = useState(null);     // Google Client ID, if configured
  const emailRef = useRef(null);
  const passRef = useRef(null);
  const gbtnRef = useRef(null);
  const isPw = m === "login" || m === "signup";   // email + password / Google modes
  useEffect(() => {
    requestAnimationFrame(() => {
      const el = m === "reset" ? passRef.current : emailRef.current;
      el && el.focus();
    });
  }, []);

  // Is "Sign in with Google" turned on for this site? (login/signup only)
  useEffect(() => {
    if (!isPw) return;
    fetch("/api/auth/config").then(r => r.json()).then(d => setGid(d.google_client_id || null)).catch(() => {});
  }, [isPw]);

  // Load Google's button + wire the callback (only when configured + a pw mode).
  useEffect(() => {
    if (!gid || !isPw) return;
    let cancelled = false;
    const init = () => {
      if (cancelled || !window.google || !window.google.accounts || !gbtnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: gid,
        callback: (resp) => {
          NotesStore.googleLogin(resp.credential).then(r => { if (r.ok) onClose(); else setErr(r.error); });
        },
      });
      gbtnRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(gbtnRef.current, { theme: "outline", size: "large", width: 300, text: m === "signup" ? "signup_with" : "signin_with" });
    };
    if (window.google && window.google.accounts) { init(); return () => { cancelled = true; }; }
    let s = document.getElementById("gsi-script");
    if (!s) {
      s = document.createElement("script");
      s.src = "https://accounts.google.com/gsi/client";
      s.async = true; s.defer = true; s.id = "gsi-script";
      document.head.appendChild(s);
    }
    s.addEventListener("load", init);
    return () => { cancelled = true; s && s.removeEventListener("load", init); };
  }, [gid, m, isPw]);

  const submit = async () => {
    if (busy) return;
    setBusy(true); setErr("");
    if (m === "forgot") {
      await NotesStore.requestReset(email);
      setBusy(false); setSent(true);   // never reveal whether the email exists
      return;
    }
    if (m === "reset") {
      const r = await NotesStore.resetPassword(resetToken, pass);
      setBusy(false);
      if (r.ok) onClose(); else setErr(r.error || "That reset link is invalid or has expired.");
      return;
    }
    const r = m === "signup" ? await NotesStore.signup(email, pass) : await NotesStore.login(email, pass);
    setBusy(false);
    if (r.ok) onClose(); else setErr(r.error || "Something went wrong.");
  };

  const title = m === "signup" ? "Create account"
    : m === "forgot" ? "Reset password"
    : m === "reset" ? "Choose a new password" : "Log in";
  const cta = m === "signup" ? "Create account"
    : m === "forgot" ? "Send reset link"
    : m === "reset" ? "Set new password" : "Log in";

  return (
    <>
      <div className="auth-scrim" onClick={onClose} />
      <div className="auth-modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className="auth-modal-head">
          <h3 className="auth-modal-title">{title}</h3>
          <button className="detail-close" onClick={onClose} aria-label="Close"><Icon.Close/></button>
        </div>

        {m === "reset" ? (
          <>
            <p className="auth-modal-sub">Pick a new password for your account.</p>
            <input ref={passRef} className="auth-input" type="password" placeholder="New password" autoComplete="new-password"
              value={pass} onChange={(e) => setPass(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") submit(); }} />
            <div className="auth-fine">At least 8 characters.</div>
          </>
        ) : m === "forgot" ? (
          sent ? (
            <p className="auth-modal-sub">If that email has an account, a reset link is on its way. The link expires in 1 hour — check your inbox (and spam folder).</p>
          ) : (
            <>
              <p className="auth-modal-sub">Enter your email and we'll send a link to set a new password.</p>
              <input ref={emailRef} className="auth-input" type="email" placeholder="Email" autoComplete="username"
                value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") submit(); }} />
            </>
          )
        ) : (
          <>
            <p className="auth-modal-sub">Sync your notes across devices.</p>
            {gid && (
              <>
                <div className="auth-google" ref={gbtnRef} />
                <div className="auth-or"><span>or</span></div>
              </>
            )}
            <input ref={emailRef} className="auth-input" type="email" placeholder="Email" autoComplete="username"
              value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") submit(); }} />
            <input className="auth-input" type="password" placeholder="Password"
              autoComplete={m === "signup" ? "new-password" : "current-password"}
              value={pass} onChange={(e) => setPass(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") submit(); }} />
            {m === "signup" && <div className="auth-fine">At least 8 characters.</div>}
            {m === "login" && (
              <div className="auth-forgot">
                <button onClick={() => { setM("forgot"); setErr(""); setSent(false); }}>Forgot password?</button>
              </div>
            )}
          </>
        )}

        {err && <div className="auth-err">{err}</div>}
        {!(m === "forgot" && sent) && (
          <button className="auth-submit" onClick={submit} disabled={busy}>{busy ? "…" : cta}</button>
        )}

        <div className="auth-switch">
          {m === "signup" && <>Already have an account? <button onClick={() => { setM("login"); setErr(""); }}>Log in</button></>}
          {m === "login" && <>New here? <button onClick={() => { setM("signup"); setErr(""); }}>Sign up</button></>}
          {m === "forgot" && <>Remembered it? <button onClick={() => { setM("login"); setErr(""); setSent(false); }}>Back to log in</button></>}
          {m === "reset" && <>Changed your mind? <button onClick={onClose}>Cancel</button></>}
        </div>
      </div>
    </>
  );
}
