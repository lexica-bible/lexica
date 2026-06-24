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
      syncCorpusNow();             // …and the saved Ask-the-corpus conversations
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
  // Clear reading-plan progress: one text (e.g. "abp") or all ("*"). Clears locally AND
  // on the server (a hard delete there), so the union merge can't bring it back.
  async function clearPlan(text) {
    const all = !text || text === "*";
    const p = planLoadLocal();
    if (all) Object.keys(p).forEach(k => delete p[k]); else delete p[text];
    planSaveLocal(p); notify();
    const a = getAuth();
    if (a && a.token) {
      try {
        await fetch("/api/plan/clear", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": "Bearer " + a.token },
          body: JSON.stringify(all ? { all: true } : { text }),
        });
      } catch (e) {}
    }
  }

  // --- saved Ask-the-corpus conversations (cross-device) ---
  // Each entry: { id, title, turns:[...], updated (ISO string), deleted? }. Browser-local
  // for everyone; for a signed-in reader they ALSO push/pull through /api/corpus/sync, so a
  // conversation started on the desktop is there on the phone. Newer `updated` wins by id; a
  // deleted:true tombstone propagates a "Clear all" instead of resurrecting from another device.
  const CORPUSKEY = "lexica.corpus.convos.v1";
  const _CONVO_KEEP = 60;   // cap stored locally (matches the server cap)
  function corpusLoadRaw() {
    let a = [];
    try { a = JSON.parse(localStorage.getItem(CORPUSKEY) || "[]"); } catch (e) {}
    if (!Array.isArray(a)) a = [];
    // older rows stored `updated` as a number (ms epoch) — coerce to an ISO string so it
    // string-compares chronologically and passes the server's type check.
    let changed = false;
    for (const c of a) {
      if (c && typeof c.updated === "number") { c.updated = new Date(c.updated).toISOString(); changed = true; }
      else if (c && c.updated == null) { c.updated = new Date(0).toISOString(); changed = true; }
    }
    if (changed) corpusSaveRaw(a);
    return a;
  }
  function corpusSaveRaw(a) { try { localStorage.setItem(CORPUSKEY, JSON.stringify(a)); } catch (e) {} }
  function corpusMerge(incoming) {
    if (!Array.isArray(incoming)) return;
    const cur = corpusLoadRaw();
    const byId = new Map(cur.map(c => [c.id, c]));
    for (const c of incoming) {
      if (!c || !c.id || typeof c.updated !== "string") continue;
      const ex = byId.get(c.id);
      if (!ex) { cur.push(c); byId.set(c.id, c); }
      else if (c.updated > (ex.updated || "")) Object.assign(ex, c);
    }
    corpusSaveRaw(cur);
  }
  let corpusTimer = null;
  async function syncCorpusNow() {
    const a = getAuth();
    if (!a || !a.token) return { ok: false, reason: "off" };
    try {
      const res = await fetch("/api/corpus/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + a.token },
        body: JSON.stringify({ convos: corpusLoadRaw() }),
      });
      if (res.status === 401) { setAuth(null); return { ok: false, reason: "signed-out" }; }
      if (!res.ok) return { ok: false, status: res.status };
      const data = await res.json();
      corpusMerge(data.convos || []);
      notify();
      return { ok: true };
    } catch (e) { return { ok: false, error: String(e) }; }
  }
  function scheduleCorpusSync() {
    const a = getAuth();
    if (applyingRemote || !a || !a.token) return;
    clearTimeout(corpusTimer);
    corpusTimer = setTimeout(() => { syncCorpusNow(); }, 2500);
  }

  // POST a JSON body to an auth endpoint; on success store {token,email} and
  // push/pull notes. Shared by signup/login AND password-reset (the reset endpoint
  // also returns {token,email}, signing the user in once the new password is set).
  async function authPostBody(path, payload) {
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return { ok: false, error: data.error || "Something went wrong." };
      setAuth({ token: data.token, email: data.email, name: data.name || null });
      syncNow();   // push local notes up + pull the account's down
      return { ok: true, email: data.email };
    } catch (e) {
      return { ok: false, error: "Network error." };
    }
  }
  function authPost(path, email, password) { return authPostBody(path, { email, password }); }

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
    authInfo() { const a = getAuth(); return { email: a && a.email, name: a && a.name, role: a && a.role, token: a && a.token, syncing, last: lastSync }; },
    signup(email, password) { return authPost("/api/auth/signup", email, password); },
    login(email, password) { return authPost("/api/auth/login", email, password); },
    // Ask the server to email a reset link. Always resolves ok (the server never
    // reveals whether the address has an account); the UI just says "check email".
    async requestReset(email) {
      try {
        const res = await fetch("/api/auth/request-reset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        await res.json().catch(() => ({}));
        return { ok: res.ok };
      } catch (e) {
        return { ok: false, error: "Network error." };
      }
    },
    // Consume a reset link's token + new password; on success the server signs the
    // user in (returns {token,email}), so reuse the shared sign-in path.
    resetPassword(token, password) { return authPostBody("/api/auth/reset", { token, password }); },
    // Set/change the password for the signed-in account (lets a Google-only account
    // add one). Needs a bearer token.
    async setPassword(password) {
      const a = getAuth();
      if (!a || !a.token) return { ok: false, error: "Not signed in." };
      try {
        const res = await fetch("/api/auth/set-password", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": "Bearer " + a.token },
          body: JSON.stringify({ password }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) return { ok: false, error: data.error || "Could not set password." };
        return { ok: true };
      } catch (e) {
        return { ok: false, error: "Network error." };
      }
    },
    // Set/clear the optional display name for the signed-in account. Empty clears it.
    async setName(name) {
      const a = getAuth();
      if (!a || !a.token) return { ok: false, error: "Not signed in." };
      try {
        const res = await fetch("/api/auth/set-name", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": "Bearer " + a.token },
          body: JSON.stringify({ name }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) return { ok: false, error: data.error || "Could not save." };
        setAuth({ ...a, name: data.name || null });
        return { ok: true, name: data.name || null };
      } catch (e) {
        return { ok: false, error: "Network error." };
      }
    },
    // Pull the account's email/name fresh from the server (keeps the name in sync
    // across devices and fills it in for sessions that signed in before the feature).
    async refreshAccount() {
      const a = getAuth();
      if (!a || !a.token) return;
      try {
        const res = await fetch("/api/auth/me", { headers: { "Authorization": "Bearer " + a.token } });
        if (!res.ok) return;
        const data = await res.json().catch(() => ({}));
        if (data && data.email) setAuth({ ...a, email: data.email, name: data.name || null, role: data.role || "user" });
      } catch (e) {}
    },
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
        setAuth({ token: data.token, email: data.email, name: data.name || null });
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
    // Permanently delete the account + all its server data, then log out locally.
    // Browser-local notes on THIS device are left as-is (the account is gone, but the
    // device's own copy stays usable and can seed a fresh account later).
    async deleteAccount() {
      const a = getAuth();
      if (!a || !a.token) return { ok: false, error: "Not signed in." };
      try {
        const res = await fetch("/api/auth/delete-account", {
          method: "POST",
          headers: { "Authorization": "Bearer " + a.token },
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) return { ok: false, error: data.error || "Could not delete the account." };
        clearTimeout(syncTimer);
        setAuth(null);
        return { ok: true };
      } catch (e) {
        return { ok: false, error: "Network error." };
      }
    },
    syncNow,
    syncPlanNow, schedulePlanSync, clearPlan,

    // --- saved Ask-the-corpus conversations ---
    // Live (non-tombstoned) conversations, newest-edited first.
    corpusConvos() {
      return corpusLoadRaw().filter(c => c && !c.deleted)
        .sort((a, b) => (b.updated || "").localeCompare(a.updated || ""));
    },
    // Insert or replace a conversation by id, then persist + schedule a sync. Stamps a
    // fresh `updated` so the newest edit wins the cross-device merge; tombstones the
    // oldest live ones past the cap so local storage stays bounded.
    upsertConvo(entry) {
      if (!entry || !entry.id) return;
      const a = corpusLoadRaw();
      const i = a.findIndex(c => c.id === entry.id);
      const row = { ...entry, updated: new Date().toISOString(), deleted: false };
      if (i >= 0) a[i] = { ...a[i], ...row }; else a.push(row);
      const live = a.filter(c => !c.deleted)
        .sort((x, y) => (y.updated || "").localeCompare(x.updated || ""));
      if (live.length > _CONVO_KEEP) {
        const keep = new Set(live.slice(0, _CONVO_KEEP).map(c => c.id));
        for (const c of a) if (!c.deleted && !keep.has(c.id)) { c.deleted = true; c.turns = []; }
      }
      corpusSaveRaw(a);
      notify();
      scheduleCorpusSync();
    },
    // Drop one conversation (soft delete → propagates through sync).
    removeConvo(id) {
      const a = corpusLoadRaw();
      const c = a.find(x => x.id === id);
      if (!c) return;
      Object.assign(c, { deleted: true, title: "", turns: [], updated: new Date().toISOString() });
      corpusSaveRaw(a);
      notify();
      scheduleCorpusSync();
    },
    // Clear them all (each becomes a tombstone so the clear propagates across devices).
    clearConvos() {
      const a = corpusLoadRaw();
      const now = new Date().toISOString();
      for (const c of a) Object.assign(c, { deleted: true, title: "", turns: [], updated: now });
      corpusSaveRaw(a);
      notify();
      scheduleCorpusSync();
    },
    syncCorpusNow, scheduleCorpusSync,
  };
})();

// On load, if signed in, pull once so this device catches up.
if (NotesStore.auth()) { setTimeout(() => NotesStore.syncNow(), 400); NotesStore.refreshAccount(); }

// Re-render a component whenever the note store changes.
function useNotesVersion() {
  const [, force] = useState(0);
  useEffect(() => NotesStore.subscribe(() => force(v => v + 1)), []);
}
