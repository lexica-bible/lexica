// ============================================================
// NOTES UI — add popover, editor panel, browse view
// ------------------------------------------------------------
// Drag-select text in the Library reader → a small "Add note" bar pops by the
// selection → opens the editor panel (same right-sidebar / bottom-sheet slot
// the word-study and cross-ref panels use). The Notes tab lists & searches
// every saved note and jumps back to its verse.
// ============================================================

// Small bar that appears above a text selection in the reader.
function NoteAddPopover({ rect, onAdd }) {
  if (!rect) return null;
  const W = 118;
  const style = {
    position: "fixed",
    top: Math.max(8, rect.top - 46),
    left: Math.min(window.innerWidth - W - 8, Math.max(8, rect.left + rect.width / 2 - W / 2)),
    zIndex: 1000,
  };
  // preventDefault on mousedown so pressing the button doesn't clear the selection
  return (
    <div className="note-popover" style={style} onMouseDown={(e) => e.preventDefault()}>
      <button className="note-popover-btn" onClick={onAdd}>
        <Icon.Bookmark/> Add note
      </button>
    </div>
  );
}

// Write / edit / delete a single note. Reuses the .detail shell.
function NotesPanel({ noteId, isMobile, onClose }) {
  const note = NotesStore.get(noteId);
  const [body, setBody] = useState(note ? (note.body || "") : "");
  const taRef = useRef(null);

  useEffect(() => {
    setBody(note ? (note.body || "") : "");
    requestAnimationFrame(() => taRef.current && taRef.current.focus());
  }, [noteId]);

  if (!note) return null;

  const save = () => { NotesStore.update(noteId, { body }); onClose(); };
  const del = () => { NotesStore.remove(noteId); onClose(); };
  // Closing without ever typing discards the empty draft (the id was minted on
  // "Add note" — id-at-creation — so a thrown-away draft shouldn't linger).
  const close = () => {
    if (!body.trim() && !(note.body || "").trim()) NotesStore.remove(noteId);
    else if (body !== note.body) NotesStore.update(noteId, { body });
    onClose();
  };

  const head = (
    <div className="detail-head">
      <div className="detail-head-l">
        <span className="detail-pos">{note.refLabel || (note.book + " " + note.chapter)}</span>
      </div>
      <button className="detail-close" onClick={close} aria-label="Close"><Icon.Close/></button>
    </div>
  );
  const content = (
    <div className="detail-body note-edit-body">
      {note.snippet && <blockquote className="note-snippet">“{note.snippet}”</blockquote>}
      <textarea
        ref={taRef}
        className="note-textarea"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Write your note…"
      />
      <div className="note-actions">
        <button className="note-save" onClick={save}>Save</button>
        <button className="note-del" onClick={del}>Delete</button>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <>
        <div className="sheet-scrim" onClick={close}/>
        <aside className="detail detail-sheet note-sheet" role="dialog" aria-label="Note">
          <div className="sheet-drag-zone" aria-hidden="true"><div className="sheet-handle"></div></div>
          {head}
          {content}
        </aside>
      </>
    );
  }
  return (
    <aside className="detail detail-side note-side" role="complementary" aria-label="Note">
      {head}
      {content}
    </aside>
  );
}

// The Notes tab — list + search of every saved note.
function NotesView({ onOpen }) {
  useNotesVersion();
  const [q, setQ] = useState("");
  const notes = NotesStore.search(q);
  return (
    <div className="notes-view">
      <div className="notes-view-head">
        <h2 className="notes-view-title">My Notes</h2>
        <input
          className="notes-search"
          type="text"
          placeholder="Search your notes…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      {notes.length === 0 ? (
        <div className="notes-empty">
          {q
            ? "No notes match that."
            : "No notes yet. In the Library, select some text in a verse and choose “Add note.”"}
        </div>
      ) : (
        <ul className="notes-list">
          {notes.map(n => (
            <li key={n.id} className="notes-item" onClick={() => onOpen(n)}>
              <div className="notes-item-ref">{n.refLabel || (n.book + " " + n.chapter)}</div>
              {n.snippet && <div className="notes-item-snippet">“{n.snippet}”</div>}
              <div className="notes-item-body">
                {n.body ? n.body : <span className="notes-item-empty">(empty)</span>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
