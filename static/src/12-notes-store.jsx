// ============================================================
// NOTES STORE — browser-local, migration-ready
// ------------------------------------------------------------
// v1 keeps study notes in the browser only (no login, no bible.db write).
// The shape here is the EXACT shape a future server/account will use, so
// moving notes up later is a straight copy, not a rewrite:
//   - each note gets its OWN id the moment it's created (clean device-merge
//     / re-upload later)
//   - the anchor is a word-position range (corpus, which text, book, chapter,
//     start verse+word-spot, end verse+word-spot) so a future highlight layer
//     can paint the exact words
// Highlighting (color + painting the marks) is the NEXT phase; `color` is
// stored blank now so it's already there when that lands.
// ============================================================
// Highlight palette — ids map to CSS classes (.lib-hi-<id>) + swatch colors.
const NOTE_COLORS = ["yellow", "green", "blue", "pink", "orange"];
const NOTE_COLOR_CSS = {
  yellow: "#ffe89e", green: "#bdeec0", blue: "#bfe0ff", pink: "#ffcfe1", orange: "#ffd6a6",
};

const NotesStore = (function () {
  const KEY = "lexica.notes.v1";
  const DEVKEY = "lexica.device.v1";
  const AUTHKEY = "lexica.auth.v1";   // { token, email } when signed in
  const JKEY = "lexica.journal.active.v1";   // id of the journal page you last opened
  const listeners = new Set();
  let cache = null;

  // --- sync state ---
  let syncTimer = null;
  let applyingRemote = false;   // suppress re-scheduling while folding in the server's copy
  let syncing = false;
  let lastSync = 0;             // ms epoch of last successful sync

  function load() {
    if (cache) return cache;
    try { cache = JSON.parse(localStorage.getItem(KEY)) || []; }
    catch (e) { cache = []; }
    if (!Array.isArray(cache)) cache = [];
    return cache;
  }
  const live = (n) => !n.deleted;   // tombstones stay in the store (for sync) but hide everywhere else
  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(cache)); } catch (e) { /* storage full / blocked */ }
    listeners.forEach(fn => { try { fn(); } catch (e) {} });
    scheduleSync();
  }
  function newId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "n_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 10);
  }
  // A stable per-browser id, made once — harmless now, helps a future account
  // merge tell this device's notes apart.
  function deviceId() {
    let d = null;
    try { d = localStorage.getItem(DEVKEY); } catch (e) {}
    if (!d) {
      d = newId();
      try { localStorage.setItem(DEVKEY, d); } catch (e) {}
    }
    return d;
  }

  // Fold a list of notes into the store by id: newer `updated` wins, tombstones
  // (deleted:true) included. Shared by Import (backup file) and Sync (server).
  function merge(incoming) {
    if (!Array.isArray(incoming)) return { added: 0, updated: 0, skipped: 0 };
    const cur = load();
    const byId = new Map(cur.map(n => [n.id, n]));
    let added = 0, updated = 0, skipped = 0;
    for (const n of incoming) {
      // journal pages have no verse anchor (no .start) — let them through too
      if (!n || !n.id || (n.kind !== "journal" && !n.start)) { skipped++; continue; }
      const ex = byId.get(n.id);
      if (!ex) { cur.push(n); byId.set(n.id, n); added++; }
      else if ((n.updated || "") > (ex.updated || "")) { Object.assign(ex, n); updated++; }
      else skipped++;
    }
    persist();
    return { added, updated, skipped };
  }

  // --- account (email + password) ---
  function getAuth() { try { return JSON.parse(localStorage.getItem(AUTHKEY)) || null; } catch (e) { return null; } }
  function setAuth(a) {
    try { a ? localStorage.setItem(AUTHKEY, JSON.stringify(a)) : localStorage.removeItem(AUTHKEY); } catch (e) {}
    listeners.forEach(fn => { try { fn(); } catch (e) {} });
  }
  function notify() { listeners.forEach(fn => { try { fn(); } catch (e) {} }); }

  function scheduleSync() {
    const a = getAuth();
    if (applyingRemote || !a || !a.token) return;
    clearTimeout(syncTimer);
    syncTimer = setTimeout(() => { syncNow(); }, 2500);
  }
  async function syncNow() {
    const a = getAuth();
    if (!a || !a.token) return { ok: false, reason: "off" };
    syncing = true; notify();
    try {
      const res = await fetch("/api/notes/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + a.token },
        body: JSON.stringify({ notes: load() }),
      });
      if (res.status === 401) { setAuth(null); return { ok: false, reason: "signed-out" }; }
      if (!res.ok) return { ok: false, status: res.status };
      const data = await res.json();
      applyingRemote = true;
      merge(data.notes || []);     // fold the account's copy back in (no re-schedule)
      applyingRemote = false;
      lastSync = Date.now();
      syncPlanNow();               // push/pull the reading-plan progress at the same moment
      return { ok: true };
    } catch (e) {
      return { ok: false, error: String(e) };
    } finally {
      syncing = false; notify();
    }
  }
  // --- reading-plan (chrono Days) progress sync ---
  // The plan blob lives in the SAME localStorage key the Library reads/writes
  // ("lexica.plan.v1"); we just push/pull it for signed-in users. The server unions
  // the completed-day sets, so two devices never clobber each other's checkmarks.
  const PLANKEY = "lexica.plan.v1";
  function planLoadLocal() { try { return JSON.parse(localStorage.getItem(PLANKEY) || "{}") || {}; } catch (e) { return {}; } }
  function planSaveLocal(o) { try { localStorage.setItem(PLANKEY, JSON.stringify(o)); } catch (e) {} }
  let planTimer = null;
  async function syncPlanNow() {
    const a = getAuth();
    if (!a || !a.token) return { ok: false, reason: "off" };
    try {
      const res = await fetch("/api/plan/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + a.token },
        body: JSON.stringify({ plan: planLoadLocal() }),
      });
      if (res.status === 401) { setAuth(null); return { ok: false, reason: "signed-out" }; }
      if (!res.ok) return { ok: false, status: res.status };
      const data = await res.json();
      if (data && data.plan) { planSaveLocal(data.plan); notify(); }  // let the Library re-read
      return { ok: true };
    } catch (e) {
      return { ok: false, error: String(e) };
    }
  }
  function schedulePlanSync() {
    const a = getAuth();
    if (applyingRemote || !a || !a.token) return;
    clearTimeout(planTimer);
    planTimer = setTimeout(() => { syncPlanNow(); }, 2500);
  }

  // POST to an auth endpoint; on success store {token,email} and push/pull notes.
  async function authPost(path, email, password) {
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return { ok: false, error: data.error || "Something went wrong." };
      setAuth({ token: data.token, email: data.email });
      syncNow();   // push local notes up + pull the account's down
      return { ok: true, email: data.email };
    } catch (e) {
      return { ok: false, error: "Network error." };
    }
  }

  return {
    // newest-edited first (tombstones hidden). Journal pages are a separate
    // free-form mode — they live in journals(), not the anchored-note list.
    all() {
      return load().filter(n => live(n) && n.kind !== "journal").sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
    },
    // Free-form journal pages (kind:"journal"), newest-edited first.
    journals() {
      return load().filter(n => live(n) && n.kind === "journal")
        .sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
    },
    createJournal() {
      const now = new Date().toISOString();
      const page = { id: newId(), device: deviceId(), kind: "journal", title: "", body: "", created: now, updated: now };
      load().push(page);
      persist();
      return page;
    },
    // The journal page you last opened — what "send verse to journal" targets.
    // Validated: returns null if the page was since deleted.
    getActiveJournal() {
      let id = null;
      try { id = localStorage.getItem(JKEY); } catch (e) {}
      if (!id) return null;
      const n = load().find(x => x.id === id);
      return (n && live(n) && n.kind === "journal") ? id : null;
    },
    setActiveJournal(id) {
      try { id ? localStorage.setItem(JKEY, id) : localStorage.removeItem(JKEY); } catch (e) {}
    },
    // Append text to a journal page (blank line between blocks). Returns the page.
    appendToJournal(id, text) {
      const n = this.get(id);
      if (!n || n.kind !== "journal") return null;
      const sep = (n.body && n.body.trim()) ? "\n\n" : "";
      return this.update(id, { body: (n.body || "") + sep + text });
    },
    get(id) { const n = load().find(x => x.id === id); return n && live(n) ? n : null; },
    // An existing (non-deleted) record on the exact same words, so we reuse it
    // instead of stacking duplicates.
    findAnchor(a) {
      const sp = a.start.pos ?? null, ep = (a.end && a.end.pos) ?? null;
      const ev = (a.end && a.end.verse) || a.start.verse;
      return load().find(n => live(n) &&
        n.corpus === a.corpus && n.book === a.book && n.chapter === a.chapter &&
        n.start.verse === a.start.verse && ((n.end && n.end.verse) || n.start.verse) === ev &&
        (n.start.pos ?? null) === sp && ((n.end && n.end.pos) ?? null) === ep
      ) || null;
    },
    forChapter(corpus, book, chapter) {
      return load().filter(n => live(n) && n.corpus === corpus && n.book === book && n.chapter === chapter);
    },
    create(anchor) {
      const now = new Date().toISOString();
      const note = { id: newId(), device: deviceId(), body: "", color: null, created: now, updated: now, ...anchor };
      load().push(note);
      persist();
      return note;
    },
    update(id, fields) {
      const n = this.get(id);
      if (!n) return null;
      Object.assign(n, fields, { updated: new Date().toISOString() });
      persist();
      return n;
    },
    // SOFT delete — keep a tombstone so the delete propagates through sync/import
    // instead of the note re-appearing from another device.
    remove(id) {
      const n = load().find(x => x.id === id);
      if (!n) return;
      Object.assign(n, { deleted: true, title: "", body: "", color: null, bookmark: false, updated: new Date().toISOString() });
      persist();
    },
    search(text) {
      const t = (text || "").toLowerCase().trim();
      const list = this.all();
      if (!t) return list;
      return list.filter(n =>
        (n.body || "").toLowerCase().includes(t) ||
        (n.snippet || "").toLowerCase().includes(t) ||
        (n.refLabel || "").toLowerCase().includes(t)
      );
    },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    exportData() {
      return { app: "lexica-notes", version: 1, exported: new Date().toISOString(), notes: load() };
    },
    importMerge(incoming) { return merge(incoming); },

    // --- account API ---
    auth: getAuth,
    authInfo() { const a = getAuth(); return { email: a && a.email, token: a && a.token, syncing, last: lastSync }; },
    signup(email, password) { return authPost("/api/auth/signup", email, password); },
    login(email, password) { return authPost("/api/auth/login", email, password); },
    // Sign in with the signed token Google handed the browser.
    async googleLogin(credential) {
      try {
        const res = await fetch("/api/auth/google", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ credential }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) return { ok: false, error: data.error || "Google sign-in failed." };
        setAuth({ token: data.token, email: data.email });
        syncNow();
        return { ok: true, email: data.email };
      } catch (e) {
        return { ok: false, error: "Network error." };
      }
    },
    logout() {
      const a = getAuth();
      if (a && a.token) {
        fetch("/api/auth/logout", { method: "POST", headers: { "Authorization": "Bearer " + a.token } }).catch(() => {});
      }
      clearTimeout(syncTimer);
      setAuth(null);
    },
    syncNow,
    syncPlanNow, schedulePlanSync,
  };
})();

// On load, if signed in, pull once so this device catches up.
if (NotesStore.auth()) { setTimeout(() => NotesStore.syncNow(), 400); }

// Re-render a component whenever the note store changes.
function useNotesVersion() {
  const [, force] = useState(0);
  useEffect(() => NotesStore.subscribe(() => force(v => v + 1)), []);
}
