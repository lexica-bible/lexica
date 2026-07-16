// ============================================================
// ASK-CORPUS PURE LOGIC — the provenance-rail word grouping, factored OUT of
// 52-ask-corpus.jsx so ONE copy is shared by the app (ProvenancePanel) and the Node unit
// test (tests/test_ac_word_groups.js). No React here — plain data shaping only.
//
// _acWordGroups is the rail's "Words in scope" builder: it merges the answer-scope words
// (key_strongs — carry the contested flag + are what the answer USED) with the lexical
// FAMILY (the computed panel — each head + its gloss-confirmed cognates, with corpus
// counts/bars), into ONE list grouped by language. The flags it stamps on each row
// (inScope / contested / aliasNote) drive the badges the reader sees, which is exactly why
// it deserves a lock. Filename order 51 < 52, so the app has it before the panel calls it;
// the export tail is a no-op in the browser and hands it to Node.
// ============================================================

// Merge the answer-scope words with the lexical family. A row is `inScope` when the answer
// used that exact word; family-only rows (a cognate the answer didn't pick, e.g. πύρωσις
// under πῦρ) are kept but marked so they don't read as evidence. Answer-scope words the
// panel didn't include (e.g. Hebrew supplements on a Greek answer) are appended so none are
// dropped.
function _acWordGroups(words, panel, contestedSet) {
  const ks = {};
  (words || []).forEach(w => { if (w && w.strongs) ks[w.strongs] = w; });
  const inScope = new Set(Object.keys(ks));
  const isContested = (s) => (contestedSet && contestedSet.has(s)) || !!(ks[s] && ks[s].contested);
  const order = [], byLang = {};
  const ensure = (lang) => {
    if (!byLang[lang]) {
      byLang[lang] = { lang, label: lang === "H" ? "Hebrew (OT)" : "Greek (NT / Greek OT)",
                       max: 0, set_aside: 0, rows: [], seen: new Set() };
      order.push(byLang[lang]);
    }
    return byLang[lang];
  };
  // 1) family rows from the panel — counts, glosses, bars, the set-aside boundary.
  ((panel && panel.groups) || []).forEach(pg => {
    const g = ensure(pg.lang);
    g.label = pg.label || g.label;
    g.set_aside += pg.set_aside || 0;
    g.max = Math.max(g.max, pg.max || 0);
    (pg.family || []).forEach(r => {
      if (g.seen.has(r.strongs)) return;
      g.seen.add(r.strongs);
      g.rows.push({ strongs: r.strongs, lemma: r.lemma, translit: r.translit, gloss: r.gloss || "",
                    count: r.count, core: !!r.core, hasCount: true,
                    inScope: inScope.has(r.strongs), contested: isContested(r.strongs),
                    aliasNote: (ks[r.strongs] && ks[r.strongs].alias_note) || null });
    });
  });
  // 2) answer-scope words the panel didn't include — keep them (never drop scope words).
  (words || []).forEach(w => {
    if (!w || !w.strongs) return;
    const lang = /^H/i.test(w.strongs) ? "H" : "G";
    const g = ensure(lang);
    if (g.seen.has(w.strongs)) return;
    g.seen.add(w.strongs);
    g.rows.push({ strongs: w.strongs, lemma: w.lemma, translit: w.translit, gloss: "",
                  count: null, core: false, hasCount: false, inScope: true, contested: isContested(w.strongs),
                  aliasNote: w.alias_note || null });
  });
  return order;
}

// _acCitedSet — the highlight cited-set builder, ONE copy (was two drifting copies:
// 52-ask-corpus._acCited + 90-app.citedStrongsApp). Emits ONLY language-prefixed
// numbers: every word row's number is fully prefixed (the strongs_base invariant),
// so bare forms in the set bought nothing except cross-language collisions — the
// old builder manufactured a G-twin AND H-twin for every key, so a Hebrew key
// H3588 (ki) lit every Greek article (G3588) in the evidence verses (Door 2 of
// docs/tickets/TICKET_highlight_cited_set.md). A bare key number is Greek by the
// SQL-gen prompt contract ("H prefix for Hebrew, G prefix or bare digits for Greek").
// Canonical prefixed form of one key-word entry ("G746"), or null when the entry
// carries no usable number. Bare digits are Greek by the SQL-gen prompt contract.
function _acNormTag(p) {
  const tag = String((p && (p.strongs || p.strongs_base)) || "").trim();
  const m = /^([GHgh]?)(\d+(?:\.\d+)*)$/.exec(tag);
  return m ? (m[1] ? m[1].toUpperCase() : "G") + m[2] : null;
}

function _acCitedSet(keyStrongs, excludeSet) {
  if (!keyStrongs || !keyStrongs.length) return null;
  const s = new Set();
  for (const p of keyStrongs) {
    const canon = _acNormTag(p);
    if (!canon) continue;
    if (excludeSet && excludeSet.has(canon)) continue;
    s.add(canon);
  }
  return s.size ? s : null;
}

// Drop function-word entries (articles, particles) from a saved key list. Saved
// Ask-corpus threads replay their browser-stored copy and never re-hit the answer
// endpoint, so a key list stored BEFORE the backend Door-1 filter (G3588 on the
// Gen 1:1 arche thread) can only be cleaned here, at display time — same pattern
// as the contested-register re-stamp. funcSet comes from /api/lexicon/function-
// strongs (prefixed forms, the ONE server-side source); null/empty = no-op, so a
// network miss can only under-filter, never hide real key words.
function _acDropFunctionKeys(keyStrongs, funcSet) {
  if (!keyStrongs || !funcSet || !funcSet.size) return keyStrongs || [];
  return keyStrongs.filter((p) => {
    const canon = _acNormTag(p);
    return !(canon && funcSet.has(canon));
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { _acWordGroups, _acCitedSet, _acDropFunctionKeys };
}
