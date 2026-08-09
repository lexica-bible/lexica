// ============================================================
// SUMMARY PANEL — Library right-pane DEFAULT (desktop) / bottom sheet (mobile)
// ------------------------------------------------------------
// A short Berean book blurb + a pericope-aware chapter summary for whatever the
// reader is on. On DESKTOP it's the resting content of the right sidebar (reuses
// the .detail-side shell); a word/verse click replaces it and closing returns
// here. On MOBILE it opens on demand as a bottom sheet from the reading cockpit's
// ⓘ button (isMobile + onClose), riding the same shared Sheet as the
// word-study sheet.
// ============================================================
// Rich MetaV person body — the tags / born-died / relationships block, WITHOUT the
// section header. Shared by the name-path card (case "metav") and the verse-bound
// linked card (the .pnbound rich branch), so the two renders can't drift. The header
// + badge stay the caller's: metaV badge on the name path, the TIPNR spine on the
// bound card (TIPNR binds it, MetaV enriches it).
// TRIBAL EPONYMS (JP ruling 2026-07-11): TIPNR/MetaV file tribe/kingdom references
// under the founding patriarch, so "king of Judah" lands on Jacob's son. The data is
// faithful; the card must not lead with claims false of the kingdom. Static
// both-senses opener for the founder names, patriarch bio demoted under a "The man"
// break. Rendered by BOTH person cards — the verse-bound TIPNR card (case
// "boundEntity", guarded there by the bio text so namesakes stay plain) and the
// name-path MetaV card (via MetavPersonBody withEponym, guarded by parentage).
// Joseph is deliberately absent: his mentions are overwhelmingly the man.
const EPONYM_LINES = {
  "Israel":   "Jacob, renamed Israel — most later mentions name the nation or the northern kingdom, not the man.",
  "Judah":    "Jacob's son — most later mentions name the tribe or the southern kingdom called after him.",
  "Ephraim":  "Joseph's son — later mentions often name the tribe, its territory, or the northern kingdom.",
  "Manasseh": "Joseph's son — later mentions often name the tribe and its territory.",
  "Levi":     "Jacob's son — later mentions often name the tribe of priests descended from him.",
  "Benjamin": "Jacob's son — later mentions often name the tribe and its territory.",
  "Reuben":   "Jacob's son — later mentions often name the tribe and its territory.",
  "Simeon":   "Jacob's son — later mentions often name the tribe and its territory.",
  "Dan":      "Jacob's son — later mentions often name the tribe, its territory, or the city of Dan.",
  "Naphtali": "Jacob's son — later mentions often name the tribe and its territory.",
  "Gad":      "Jacob's son — later mentions often name the tribe and its territory.",
  "Asher":    "Jacob's son — later mentions often name the tribe and its territory.",
  "Issachar": "Jacob's son — later mentions often name the tribe and its territory.",
  "Zebulun":  "Jacob's son — later mentions often name the tribe and its territory.",
};

// ONE IDENTITY BODY FOR EVERY PERSON/PLACE CARD, WHATEVER THE SOURCE (ticket
// "one renderer for Biblical Person regardless of source", 2026-08-09).
// The body used to branch on WHICH TABLE held the record: a MetaV-linked person got
// chips + born/died + labeled kin rows, while a TIPNR-only person (Joram, the Israel
// king) got plain text rows and no chips at all — so the same kind of fact looked like
// two different kinds of fact depending on provenance the reader can't see. Now every
// card fills this one shape and a field the source doesn't carry is simply ABSENT —
// no placeholder, no second layout. Field order is fixed everywhere:
//   chips -> born/died -> labeled rows.
// The source badge (TIPNR / MetaV+TIPNR) is untouched: provenance is the badge's job,
// never the layout's.
function IdentityBody({ chips, born, rows }) {
  chips = chips || []; rows = rows || [];
  if (!chips.length && !born && !rows.length) return null;
  return (
    <>
      {chips.length > 0 && (
        <div className="metav-meta">
          {chips.map(c => (
            <span key={c.text} className={"metav-tag" + (c.gold ? " metav-tag-gold" : "")}>{c.text}</span>
          ))}
        </div>
      )}
      {born && (
        <p className="detail-p detail-p--meta" style={{fontSize:"13px"}}>
          {born.birth_year && <span>Born: {born.birth_year}{born.birth_place ? `, ${born.birth_place}` : ""}</span>}
          {born.birth_year && born.death_year && " · "}
          {born.death_year && <span>Died: {born.death_year}{born.death_place ? `, ${born.death_place}` : ""}</span>}
        </p>
      )}
      {rows.length > 0 && (
        <div className="metav-rels">
          {rows.map(r => (
            <div key={r.label} className="metav-rel-row">
              <span className="metav-rel-label">{r.label}</span>
              <span className="metav-rel-names">{r.value}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

// The kin-row label set — MetaV's wording, and now the ONE set. The bound card's own
// rows used to say "Parents" beside MetaV's "Parent" for the same relation.
const REL_ROWS = [
  { types: ["child"],                    label: "Parent"   },
  { types: ["father","mother"],          label: "Children" },
  { types: ["spouseOrConcubine"],        label: "Spouse"   },
  { types: ["sibling","halfSiblingSameFather","halfSiblingSameMother"], label: "Siblings" },
];

// MetaV person record -> the shared body shape. Relationship rows list every name, no
// truncation: names are the point of the panel, and the corpus-wide worst case (David,
// 21 children) is ~8 lines — not enough to earn a collapse (measured on PA 2026-07-11).
function metavBody(d) {
  const groups = d.groups || [];
  return {
    chips: [
      ...(d.gender ? [{ text: d.gender === "M" ? "Male" : "Female" }] : []),
      ...groups.filter(g => g.startsWith("Tribe")).map(g => ({ text: g })),
      ...(groups.includes("Genealogy of Jesus") ? [{ text: "Genealogy of Jesus", gold: true }] : []),
    ],
    born: (d.birth_year || d.death_year) ? d : null,
    rows: REL_ROWS.map(({ types, label }) => {
      const matching = (d.relationships || []).filter(r => types.includes(r.type));
      return matching.length ? { label, value: matching.map(r => r.name).join(", ") } : null;
    }).filter(Boolean),
  };
}

// TIPNR text carries a "(?)" uncertainty marker; strip it for display. ONE copy,
// shared by the card and by tipnrBody below — the value is read in four places.
const cleanTipnr = s => (s || "").replace(/\s*\(\?\)/g, "").trim();
// The clicked word is a people-group (gentilic) bound to its eponymous ancestor (a
// PERSON entity) — TIPNR models peoples that way.
const isPeopleClan = be => be.section === "person" && !!be.people_group;

// TIPNR entity -> the SAME body shape metavBody returns. This is the half of the
// unification that used to be a second layout: these facts rendered as plain text
// rows with no chips while a MetaV-linked person got the chip treatment.
//
// GENDER is not new data — the entity payload has always carried it (views_metav.py);
// this card just never rendered it, so a TIPNR-only person lost a fact we already
// held. Surfacing it is DISPLAY of the existing payload, not entity enrichment
// (which stays out of scope by ruling).
//
// ⚠ AREA IS NOT A TRIBE FIELD — measured on PA 2026-08-09 across tipnr_entities'
// person rows: ~1,150 read "Tribe of X", but ~400 read a REGION or a PERIOD instead
// (Early Patriarch 142, Edom 72, Israel 29, Canaan 19, Egypt 18, Sinai, Arabia,
// Ammon, Syria, Moab, Mesopotamia, Persia, Assyria, Midian …). The card labeled
// every one of them "Tribe", which was simply wrong for those; fixed here, since
// unifying the body forced the label to be decided anyway.
// The split is by VALUE, never by source: only a value that literally says "Tribe of
// X" is promoted to a CHIP, everything else stays a labeled ROW — rows state, chips
// assert (reviewer ruling, pre-approved 2026-08-09). A "(?)" value stays a row for
// that same reason: cleanTipnr drops the marker for display, so an uncertain tribe
// must not then be asserted as a chip. A PLACE never chips its area — a place's
// Geo-area is the territory it sits in, and a bare "Tribe of Simeon" chip there
// would read as identity.
// `line` is the descriptor already rendered above the body: an area the description
// already names isn't repeated (Eden: "…in Mesopotamia").
function tipnrBody(be, line) {
  const peopleClan = isPeopleClan(be);
  // often just TIPNR's empty-breadcrumb ">" — strip stray > and blanks so an empty
  // geo-area shows NO row at all.
  const area = cleanTipnr(be.area).replace(/^[>\s]+|[>\s]+$/g, "");
  const showArea = !!area && !(line && line.toLowerCase().includes(area.toLowerCase()));
  const areaIsTribe = be.section === "person" && !peopleClan
    && /^tribe of\b/i.test(area) && !/\(\?\)/.test(be.area || "");
  return {
    chips: [
      ...(be.section === "person" && !peopleClan && (be.gender === "M" || be.gender === "F")
          ? [{ text: be.gender === "M" ? "Male" : "Female" }] : []),
      ...(showArea && areaIsTribe ? [{ text: area }] : []),
    ],
    born: null,
    rows: [
      // A group card drops the ancestor's individual kin and his tribe — they assert
      // links the collective may not carry; Lineage is the honest ancestry instead.
      // It now wears a label like every other row: an unlabeled row was itself a
      // second layout, which is what this unification deletes.
      ...(peopleClan && !be.head_is_people
          ? [{ label: "Lineage", value: `Descended from ${be.name}` }] : []),
      ...(be.section === "person" && !peopleClan && be.parents && be.parents.length > 0
          ? [{ label: "Parent", value: be.parents.join(", ") }] : []),
      ...(be.section === "person" && !peopleClan && be.offspring && be.offspring.length > 0
          ? [{ label: "Children", value: be.offspring.join(", ") }] : []),
      ...(showArea && !peopleClan && !areaIsTribe
          ? [{ label: be.section === "place" ? "Region" : "Area", value: area }] : []),
    ],
  };
}

// How many elements a body will actually render — the input to the sparse-card test.
// A `function` declaration on purpose: the bundle's consts are lexical and invisible
// to tests/test_person_body.js, which must exercise the SHIPPED helper, never a copy.
function bodyFieldCount(b) { return b.chips.length + (b.born ? 1 : 0) + b.rows.length; }

// ── WHAT THE NUMBER IS ATTACHED TO ──────────────────────────────────────────────
// The card leads with the Strong's number, the hero prints the Greek/Hebrew form,
// and the person block sits under both — so a reader can reasonably take the number
// as identifying the PERSON. It doesn't: G2496 is the number for the written name
// Ἰωράμ, which BOTH kings Jehoram carry because both are spelled that way, and the
// occurrence line under it ("51× G2496") counts that FORM across everyone bearing it.
// WORDING APPROVED VERBATIM (JP, 2026-08-09): it states the positive rather than a
// denial — "not the person" read as though the two were unrelated. Don't reword it.
// Returns "" when the card can't carry the claim honestly:
//   * no identity block under it (nothing for "below" to point at),
//   * no real number — a header reading "PN" has nothing to clarify. RULED a
//     deliberate omission, not a coverage hole (reviewer, 2026-08-09),
//   * no script form in the hero (it falls back to the English name, and that is
//     not what a Strong's number numbers).
function scopeNoteText(strongs, form, kind) {
  if (!kind || !form || !/^[GH]\d/.test(strongs || "")) return "";
  return `${strongs} numbers the name form ${form} — the ${kind} this verse names is below.`;
}

function MetavPersonBody({ data, withEponym }) {
  if (!data) return null;
  // Eponym opener on the name-path card. Parentage guard keeps namesakes plain:
  // only the record whose parents are Israel/Jacob (the 12 sons) or Joseph
  // (Ephraim/Manasseh) is the founder; Israel himself passes by name.
  const parents = (data.relationships || []).filter(r => r.type === "child").map(r => r.name);
  const eponym = withEponym && EPONYM_LINES[data.name]
    && (data.name === "Israel" || parents.some(p => /^(Israel|Jacob|Joseph)$/.test(p)))
    ? EPONYM_LINES[data.name] : null;
  return (
    <>
      {eponym && <p className="pnbound-desc">{eponym}</p>}
      {eponym && <div className="detail-h">The man</div>}
      <IdentityBody {...metavBody(data)} />
    </>
  );
}

function SummaryPanel({ book, chapter, bookLabel, isMobile, onClose, onBack }) {
  // Remembers fetched summaries across remounts (the panel unmounts whenever a
  // word/verse takes over the slot) so re-opening the same chapter is instant
  // instead of flashing the loading line again.
  const key = book + "/" + chapter;
  const [data, setData] = useState(() => SummaryPanel._cache[key] || null);
  // FRAME-0 (audit site 5): start loading ON when a fetch is certain, so the first
  // frame shows the loading line — never a premature "No overview available".
  const [loading, setLoading] = useState(() => !!(book && chapter) && !SummaryPanel._cache[key]);

  useEffect(() => {
    if (!book || !chapter) return;
    const cached = SummaryPanel._cache[key];
    if (cached) { setData(cached); setLoading(false); return; }
    let cancelled = false;
    setLoading(true);
    setData(null);
    api.summary(book, chapter)
      .then(d => { if (!cancelled) { SummaryPanel._cache[key] = d || {}; setData(d || {}); setLoading(false); } })
      .catch(() => { if (!cancelled) { setData({}); setLoading(false); } });
    return () => { cancelled = true; };
  }, [book, chapter]);

  // Swipe-to-dismiss for the mobile sheet (same hook the word-study / xref sheets
  const titleRef = useRef(null);

  const bookText = data && data.book_summary;
  const chapText = data && data.chapter_summary;
  const nothing = !loading && !bookText && !chapText;
  const title = (bookLabel || book) + (chapter ? " " + chapter : "");
  // Mobile: shrink the title to fit one line beside the corner "Intro" link.
  useFitText(titleRef, title, { enabled: isMobile });

  const content = (
    <>
      {loading && <div className="summary-loading">Reading the chapter…</div>}
      {/* Provenance contract §3: every synthesized block carries the AI tag (JP ruling —
          the summary panel had NO source label at all; audit 2026-07-16 check A+F). */}
      {!loading && bookText && (
        <div className="detail-section">
          <div className="detail-h">About<WarrantTag cls="lsj-badge lsj-badge--accent" warrant="AI-written summary — claims not verified against the verse text.">AI</WarrantTag></div>
          <p className="detail-p">{renderInlineMd(bookText)}</p>
        </div>
      )}
      {!loading && chapText && (
        <div className="detail-section last">
          <div className="detail-h">This chapter<WarrantTag cls="lsj-badge lsj-badge--accent" warrant="AI-written summary — claims not verified against the verse text.">AI</WarrantTag></div>
          <p className="detail-p">{renderInlineMd(chapText)}</p>
        </div>
      )}
      {nothing && (
        <div className="summary-loading">No overview available for this passage.</div>
      )}
    </>
  );

  // Mobile: bottom sheet opened from the reading cockpit. Swipe down (drag
  // anywhere) or tap the scrim to close — matches the other sheets.
  if (isMobile) {
    // A bare child of the shared Sheet: the card owns its .detail-head band + .detail-body
    // scroll box, so the sheet supplies only chrome (scrim, handle, height, the gesture).
    return (
      <Sheet bare onClose={onClose}>
        <aside className="detail detail-card summary-sheet" role="dialog" aria-label="Reading overview">
          {/* Same header as desktop: title on the left (wraps), the "‹ Intro" toggle on
              the right pinned to the top. No ✕ — the drag handle + tap-outside close it. */}
          <div className="detail-head">
            <div className="detail-head-l">
              <span ref={titleRef} className="detail-pos summary-pos">{title}</span>
            </div>
            {onBack && <button className="detail-back" onClick={onBack} aria-label="Back to reading intro" title="Intro">‹</button>}
          </div>
          <div className="detail-body">{content}</div>
        </aside>
      </Sheet>
    );
  }

  // Desktop: resting content of the right sidebar. The "‹ Intro" toggle sits in the
  // .detail-back slot (right), matching the word-study / xref / day-intro headers.
  return (
    <aside className="detail zinspect detail-side summary-side" role="complementary" aria-label="Reading overview">
      <div className="detail-head">
        <div className="detail-head-l">
          <span className="detail-pos summary-pos">{title}</span>
        </div>
        {onBack && <button className="detail-back" onClick={onBack} aria-label="Back to reading intro">‹ Intro</button>}
      </div>
      <div className="detail-body">{content}</div>
    </aside>
  );
}

SummaryPanel._cache = {};

// ============================================================
// DETAIL PANEL — SIDEBAR / BOTTOM SHEET
// ============================================================
// metaV place comments carry a bare URL (almost always Wikipedia) tacked on the end —
// it was never meant to show. Strip the URL (and any dangling "; "/", " separator) so the
// card shows just the prose gloss, e.g. "river: now Wadi al Arish".
function cleanPlaceComment(text) {
  return String(text || "").replace(/\s*[;,]?\s*https?:\/\/\S+/g, "").trim().replace(/[;,]\s*$/, "");
}

function DetailPanel({ entry, isMobile, onClose, occurrences, totalResults, onStrongsSearch, onReadInContext, onNameSearch, onNavigateToLexicon, overviewBack, backLabel = "Overview" }) {
  const [verseText, setVerseText] = useState("");
  // FRAME-0 (audit site 7): start loading ON when the verse fetch will run at mount
  // (same condition as the fetch effect), so the quote never paints "—" first.
  const [verseLoading, setVerseLoading] = useState(() => !!(entry && !entry.isExtra));
  const [abpCount, setAbpCount] = useState(null);
  const [extraCount, setExtraCount] = useState(null);
  const [showInterlinear, setShowInterlinear] = useState(false);
  const [interlinearWords, setInterlinearWords] = useState(null);
  const heroRef = useRef(null);

  useEffect(() => {
    setShowInterlinear(false);
    setInterlinearWords(null);
  }, [entry && entry.id]);

  // Auto-shrink the big headword so a long word (e.g. a proper name like
  // "Nebuchadnezzar") scales down to fit the panel on one line instead of
  // overflowing. Measure the natural width at the CSS base size against the
  // panel's content width, then drop the size proportionally if it's too wide.
  // Re-runs per word and when the layout swaps (mobile sheet <-> desktop side)
  // or the window resizes.
  useLayoutEffect(() => {
    const el = heroRef.current;
    if (!el) return;
    let cancelled = false;
    const fit = () => {
      if (cancelled || !el.isConnected) return;
      el.style.fontSize = "";                       // reset to the CSS base, then measure
      const box = el.closest(".detail-body");
      if (!box) return;
      const cs = getComputedStyle(box);
      const avail = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      const natural = el.scrollWidth;
      if (avail > 0 && natural > avail) {
        const base = parseFloat(getComputedStyle(el).fontSize);
        el.style.fontSize = Math.max(22, Math.floor(base * avail / natural)) + "px";
      }
    };
    fit();
    // The reader fonts load with display=optional, so a first-open measure can
    // land on the fallback font — re-measure once the real font settles.
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
    window.addEventListener("resize", fit);
    return () => { cancelled = true; window.removeEventListener("resize", fit); };
  }, [entry && entry.id, isMobile]);

  // The side-card interlinear follows the TEXT you're reading, same as the reading
  // pane: KJV -> KJV words, Hebrew (HEB reader) -> Hebrew words, otherwise ABP Greek.
  // Each feed is normalised to one shape {top, translit, english, strongs, he} so the
  // render below stays a single dumb loop. (Before, it always pulled ABP Greek — so a
  // KJV verse showed the LXX Greek underneath it.)
  useEffect(() => {
    if (!showInterlinear || !entry || interlinearWords) return;
    let cancelled = false;
    const done = (rows) => { if (!cancelled) setInterlinearWords(rows); };
    const tag = (s) => (s && s !== "*") ? strongsTag(s) : "";
    if (entry.isKjv) {
      api.kjvVerseWords(entry.book, entry.chapter, entry.verse)
        .then(rows => done((rows || []).map(w => {
          const sid = (w.strongs_ids && w.strongs_ids[0]) || "";
          return { top: w.lemma || "", translit: w.xlit || "", english: w.word || "",
                   strongs: tag(sid), he: /^H/i.test(sid) };
        })))
        .catch(() => done([]));
    } else if (entry.isBsb) {
      api.bsbVerseWords(entry.book, entry.chapter, entry.verse)
        .then(rows => done((rows || []).map(w => {
          const sid = (w.strongs_ids && w.strongs_ids[0]) || "";
          return { top: w.lemma || "", translit: w.xlit || "", english: w.word || "",
                   strongs: tag(sid), he: /^H/i.test(sid) };
        })))
        .catch(() => done([]));
    } else if (entry.isHeb) {
      api.hebVerseWords(entry.book, entry.chapter, entry.verse)
        .then(d => done((d.words || []).map(w => ({
          top: w.hebrew || "", translit: w.translit || "", english: w.gloss || "",
          strongs: tag(w.strongs), he: true,
        }))))
        .catch(() => done([]));
    } else {
      api.verseWords(entry.book, entry.chapter, entry.verse)
        .then(d => done((d.words || []).map(w => ({
          top: w.lemma || "", translit: w.translit || "", english: w.english || "",
          strongs: (w.strongs_base === "*") ? "" : tag((w.strongs && w.strongs !== "*") ? w.strongs : w.strongs_base),
          he: false,
          bracket_id: w.bracket_id,   // ABP translator-supplied words -> [ ] in the render (KJV/Hebrew leave this undefined)
          pos: w.greek_pos,           // Greek word-order number, shown inside brackets like the reading pane
        }))))
        .catch(() => done([]));
    }
    return () => { cancelled = true; };
  }, [showInterlinear, entry && entry.id]);

  useEffect(() => {
    if (!entry || entry.isExtra) return;   // non-canonical words have no Bible verse to load
    let cancelled = false;
    setVerseText("");
    setVerseLoading(true);
    api.verse(entry.book, entry.chapter, entry.verse)
      .then((data) => {
        if (!cancelled) setVerseText(data.text || "");
      })
      .catch(() => {
        if (!cancelled) setVerseText("");
      })
      .finally(() => {
        if (!cancelled) setVerseLoading(false);
      });
    return () => { cancelled = true; };
  }, [entry && entry.id]);

  useEffect(() => {
    if (!entry || entry.strongs_base === "*") { setAbpCount(null); return; }
    let cancelled = false;
    api.strongsCount(entry.strongs_raw)
      .then(d => { if (!cancelled) setAbpCount(d.count ?? null); })
      .catch(() => { if (!cancelled) setAbpCount(null); });
    return () => { cancelled = true; };
  }, [entry && entry.strongs_raw]);

  // Count within the non-canonical text itself (e.g. the Didache).
  useEffect(() => {
    if (!entry || !entry.isExtra || !entry.extraBook || !entry.strongs_base || entry.strongs_base === "*") {
      setExtraCount(null); return;
    }
    let cancelled = false;
    api.extraStrongsCount(entry.extraBook, entry.strongs_base)
      .then(d => { if (!cancelled) setExtraCount(d.count ?? null); })
      .catch(() => { if (!cancelled) setExtraCount(null); });
    return () => { cancelled = true; };
  }, [entry && entry.id]);

  const isPN = entry && (entry.is_pn || entry.isPN || entry.strongs === "PN" || entry.strongs_base === "*");
  // A word carrying an H-number. For Hebrew PROPER NOUNS we want metaV (person/
  // place) on top with the BDB lexical entry stacked BELOW (like KJV mode):
  //  - isHebrewWord drives the BDB fetch + section (shown for ALL Hebrew words, incl. PNs)
  //  - isHebrew (excludes PNs) drives the Hebrew HERO styling + LSJ suppression, so a
  //    PN's hero shows its NAME and metaV stays the primary card.
  const isHebrewWord = entry && entry.strongs && entry.strongs.startsWith("H");
  const isHebrew = isHebrewWord && !isPN;
  // Gentilics (-ite/-ites: Hivite, Sinite, Amorite…) are eponymous people-groups
  // from the Table of Nations — labelled "People / Clan", but still shown as a
  // metaV person so the genealogy (parent/sibling clans) is preserved.
  const isGentilic = !!(isPN && entry && /ites?$/i.test(extractProperName(entry.pnName || entry.gloss || "")));

  // R-2 stage 2: the ABP proper-noun card's GREEK identity (pn_greek_identity via
  // /api/pn/greek-identity). The server-side switch READER_GREEK_IDENTITY gates the
  // endpoint — with it OFF, or for a 'none'-bucket word (control C4), this stays
  // null and the card renders exactly as before. ABP reader only: KJV/BSB/Hebrew
  // clicks stay Hebrew-keyed (ruling S2-Q4 / Q4).
  const [greekId, setGreekId] = useState(null);
  // FRAME-0 rule (Hebrew-flash fix, 2026-07-25): the identity fetch gets a pending
  // flag that starts TRUE whenever the fetch WILL run, so the card holds its
  // identity-dependent parts neutral instead of painting the stored Hebrew state
  // and swapping when the Greek identity lands (the flash JP reported). Same
  // pattern as bdbLoading/lexicaLoading. Resolves fast either way: identity,
  // 'none', or a 404 when the switch is off — then the old card paints once.
  const giWillFetch = !!(entry && isPN && !entry.isKjv && !entry.isBsb && !entry.isHeb && !entry.isExtra
    && entry.position !== null && entry.position !== undefined && entry.book);
  const [greekIdPending, setGreekIdPending] = useState(giWillFetch);
  useEffect(() => {
    setGreekId(null);
    if (!giWillFetch) { setGreekIdPending(false); return; }
    setGreekIdPending(true);
    let cancelled = false;
    // Merged compound chip (pnMergePos): fetch BOTH slots' identities and join the
    // DISPLAYED headword/translit ("Γασιών Γαβέρ"), so the card's hero matches the
    // one-chip pair (JP 2026-07-31). Counts/source stay the FIRST word's — the
    // lookup key and payload are unchanged; join fails soft to the first identity.
    const p1 = api.pnGreekIdentity(entry.book, entry.chapter, entry.verse, entry.position);
    const p2 = entry.pnMergePos != null
      ? api.pnGreekIdentity(entry.book, entry.chapter, entry.verse, entry.pnMergePos).catch(() => null)
      : Promise.resolve(null);
    Promise.all([p1, p2])
      .then(([d, d2]) => {
        if (cancelled) return;
        if (d && !d.error) {
          if (d2 && !d2.error && d2.lemma && d.lemma) {
            // Translit joins ONLY when both halves have one — a half-translit
            // ("Gád" under Δαιβών Γάδ) is the frankenstein row (JP 2026-07-31).
            d = { ...d, lemma: d.lemma + " " + d2.lemma,
                  translit: (d.translit && d2.translit) ? d.translit + " " + d2.translit : "" };
          }
          setGreekId(d);
        }
        setGreekIdPending(false);
      })
      .catch(() => { if (!cancelled) setGreekIdPending(false); });
    return () => { cancelled = true; };
  }, [entry && entry.id]);

  // PN occurrence count (by name, for strongs='*' entries)
  const [pnCount, setPnCount] = useState(null);
  useEffect(() => {
    setPnCount(null);
    if (!entry.pnName && !entry.gloss) return;
    const name = extractProperName(entry.pnName || entry.gloss);   // Part-3: same precedence as the lookups
    if (!name || name.length < 2) return;
    let cancelled = false;
    api.pnCount(name)
      .then(d => { if (!cancelled) setPnCount(d.count ?? null); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [entry && entry.id]);

  // KJV occurrence count for Hebrew words
  const [kjvCount, setKjvCount] = useState(null);
  useEffect(() => {
    setKjvCount(null);
    if (!entry.strongs || (!isHebrewWord && !entry.isKjv)) return;   // KJV cross-link: KJV words + ANY Hebrew word (incl. proper nouns)
    let cancelled = false;
    api.kjvStrongsCount(entry.strongs)
      .then(d => { if (!cancelled) setKjvCount(d.count ?? null); })
      .catch(() => { if (!cancelled) setKjvCount(null); });
    return () => { cancelled = true; };
  }, [entry && entry.strongs]);

  // BSB occurrence count (BSB word study) — its own count; the Lexicon tab has no
  // BSB corpus, so this shows as a plain "N× in BSB" tally, not a click-through.
  const [bsbCount, setBsbCount] = useState(null);
  useEffect(() => {
    setBsbCount(null);
    if (!entry || !entry.strongs || (!entry.isBsb && !isHebrewWord)) return;   // BSB words + ANY Hebrew word (incl. proper nouns)
    let cancelled = false;
    api.bsbStrongsCount(entry.strongs)
      .then(d => { if (!cancelled) setBsbCount(d.count ?? null); })
      .catch(() => { if (!cancelled) setBsbCount(null); });
    return () => { cancelled = true; };
  }, [entry && entry.strongs]);

  // Hebrew OT occurrence count (heb.db) for ANY Hebrew word — the source-text tally,
  // shown whichever reader the word was clicked from (KJV, BSB, or the Hebrew reader).
  const [hebCount, setHebCount] = useState(null);
  useEffect(() => {
    setHebCount(null);
    if (!isHebrewWord || !entry.strongs) return;   // ANY Hebrew word, incl. proper nouns (bound-entity cards)
    let cancelled = false;
    api.hebStrongsCount(entry.strongs)
      .then(d => { if (!cancelled) setHebCount(d.count ?? null); })
      .catch(() => { if (!cancelled) setHebCount(null); });
    return () => { cancelled = true; };
  }, [entry && entry.strongs]);

  // ABP (Greek/LXX) occurrences of a backfilled proper noun, counted on its strongs_base
  // (the bare strongs is '*'). Shown only on the bound-entity card: the name DOES appear in
  // the ABP text, individuated from παράδεισος — this surfaces those Greek occurrences from
  // the Hebrew number we already carry (no Greek re-key; TIPNR's Greek form is an unusable
  // STEP-extended number our lexicon doesn't have and ABP never uses).
  const [abpBaseCount, setAbpBaseCount] = useState(null);
  useEffect(() => {
    setAbpBaseCount(null);
    if (!isHebrewWord || !entry.strongs_base || entry.strongs_base === "*") return;
    let cancelled = false;
    api.strongsCountBase(entry.strongs_base)
      .then(d => { if (!cancelled) setAbpBaseCount(d.count ?? null); })
      .catch(() => { if (!cancelled) setAbpBaseCount(null); });
    return () => { cancelled = true; };
  }, [entry && entry.strongs_base]);

  // metaV person/place lookup — runs on any word click where gloss may be a name
  const [metavPersonData, setMetavPersonData] = useState(null);
  const [metavPlaceData, setMetavPlaceData] = useState(null);
  const [metavTab, setMetavTab] = useState("person"); // "person" | "place"
  const [metavLoading, setMetavLoading] = useState(false);

  // Nave's topical card REMOVED 2026-07-16 — the data was deleted from PA (JP), so the
  // section could never render again; dead code stripped under the render charter.
  // Derived — all downstream code uses these unchanged.
  // If the word's OWN proper-noun type (tipnr pn_types) is a clean SINGLE type and
  // we have that card, the word IS that entity — the other metaV card is a
  // name-coincidence (loose name-based lookup), so PIN to the single entity and
  // suppress the Person/Place toggle. When pn_types is ambiguous ('person,place':
  // a strongs shared by a genuine person AND place — Adam, Dan) or absent (a
  // non-Library entry, or no tipnr row), keep the toggle so the user can see both.
  const pnList = ((entry && entry.pn_types) || "").toLowerCase().split(",").map(s => s.trim()).filter(Boolean);
  const pnSingle = (pnList.length === 1 && (pnList[0] === "person" || pnList[0] === "place")) ? pnList[0] : null;
  const metavPinned = (pnSingle === "person" && metavPersonData) ? "person"
                    : (pnSingle === "place"  && metavPlaceData)  ? "place"
                    : null;
  const metavHasBoth = !!(metavPersonData && metavPlaceData) && !metavPinned;
  const metavType = metavPinned
    ? metavPinned
    : (metavHasBoth ? metavTab : (metavPersonData ? "person" : metavPlaceData ? "place" : null));
  const metavData = metavType === "person" ? metavPersonData : metavType === "place" ? metavPlaceData : null;

  // Verse-bound TIPNR entity (Issue 2): the VERIFIED person/place for THIS click, from
  // the pn_binding tables. When present it replaces the name-guess metaV card AND the
  // AI blurb with a sourced identity. 404 -> null -> the old name-path shows. Declared
  // BEFORE the metaV effect because that effect gates on it (deps + body).
  const [boundEntity, setBoundEntity] = useState(null);
  const [boundLoading, setBoundLoading] = useState(false);
  // Synchronous "a bind is being checked for this entry" flag. The metaV effect runs
  // right after this one in the SAME commit and reads it to skip firing a name lookup
  // before the async boundLoading state flips — without it the metaV fetch races ahead
  // on the first render and strands a "Looking up…" loader.
  const bindPendingRef = useRef(false);
  useEffect(() => {
    setBoundEntity(null);
    const bn = extractProperName(entry.pnName || entry.gloss || "");
    if (!bn || bn.length < 2 || !entry.book || !entry.chapter || !entry.verse) {
      bindPendingRef.current = false;
      setBoundLoading(false);
      return;
    }
    bindPendingRef.current = true;
    let cancelled = false;
    setBoundLoading(true);
    api.metavEntity(bn, entry.book, entry.chapter, entry.verse, entry.position)
      .then(d => { if (!cancelled) setBoundEntity(d && d.bound ? d : null); })
      .catch(() => {})
      .finally(() => { bindPendingRef.current = false; if (!cancelled) setBoundLoading(false); });
    return () => { cancelled = true; };
  }, [entry && entry.id]);

  useEffect(() => {
    setMetavPersonData(null);
    setMetavPlaceData(null);
    setMetavTab("person");
    setMetavLoading(false);   // cleared each run; the proceed-path re-sets it true below
    // A verified verse-bind (Issue 2) OWNS the card: skip the name-based metaV lookup
    // entirely. This is the single gate that kills EVERY downstream name-based section
    // at once — the person/place card, its Groups, Nave's topical (needs metaV data),
    // and the place-LSJ definition all derive from this fetch. The ref is set
    // synchronously by the bind effect above; boundEntity catches the resolved bind.
    if (bindPendingRef.current || boundEntity) return;
    // Skip metaV for words with a real Greek lemma — those belong to LSJ
    // Exception: KJV/BSB words that are proper nouns still go through metaV. For Hebrew (OT)
    // words we KNOW name-vs-common from heb.db's own grammar (entry.hebName, built at startup) —
    // so a common word capitalized mid-verse ("Wilderness of Sinai") never pops a place card,
    // while real names AND gentilic clans (Philistines) still do. Greek/NT words, or a missing
    // heb.db, carry no hebName and fall back to the capital-letter heuristic.
    const kjvIsPN = (entry.isKjv || entry.isBsb) && (
      entry.hebName !== undefined ? entry.hebName
                                  : extractProperName(entry.pnName || entry.gloss || "") !== ""
    );
    if (!isPN && !kjvIsPN && entry.greek && entry.translit) return;
    const name = extractProperName(entry.pnName || entry.gloss || "");
    if (!name || name.length < 2) return;
    const _DIVINE_SKIP = new Set(["LORD","Lord","YHWH","Yahweh","Jehovah","Holy"]);
    if (_DIVINE_SKIP.has(name)) return;
    let cancelled = false;
    setMetavLoading(true);
    Promise.all([
      api.metavPerson(name).catch(() => ({ error: true })),
      api.metavPlace(name).catch(() => ({ error: true })),
    ]).then(([pd, ld]) => {
      if (cancelled) return;
      const personOk = !pd.error && (pd.birth_year || pd.death_year || pd.relationships?.length >= 2);
      // SLIM person card (Paul-class, JP option A 2026-07-29): an exact single-owner
      // match that fails the bio bar used to serve NOTHING (Paul, Pilate, Esther —
      // 2,218 slots). Serve a reduced card instead. Guards: sole_referent (exact-tier
      // only — the Archite fuzzy rejection is certified and must survive), and NO
      // place row (so every slot that shows a place card today keeps it — the slim
      // card fills true no-card slots only).
      const slimOk = !personOk && !pd.error && !pd.ambiguous && pd.sole_referent === true && ld.error;
      if (personOk) setMetavPersonData(pd);
      else if (slimOk) setMetavPersonData({ ...pd, _slim: true });
      if (!ld.error) setMetavPlaceData(ld);
      // Default tab (only matters when BOTH person+place exist). Prefer the
      // word's OWN proper-noun type from tipnr — pn_types is a SET ('person',
      // 'place', or 'person,place'; backlog #5 fix). A clean SINGLE type is
      // authoritative. When tipnr is ambiguous (a strongs shared by a person AND
      // a place → 'person,place', which strongs alone can't disambiguate) or
      // absent (pn_types null: pre-reimport, or a non-Library entry), fall back to
      // the strongs_g heuristic — flip to Place only when the place's own (G-)
      // strongs matches the clicked word's strongs_base. (Legacy pn_type is NOT
      // used: tipnr.strongs was a PK so it stored whichever type imported last.)
      const pnTypes = (entry.pn_types || "").toLowerCase().split(",").map(s => s.trim()).filter(Boolean);
      let tab;
      if (pnTypes.length === 1 && pnTypes[0] === "person") tab = "person";
      else if (pnTypes.length === 1 && pnTypes[0] === "place") tab = "place";
      else {
        const placeStrongsMatch = !ld.error && !!ld.strongs_g && !!entry.strongs_base &&
          ld.strongs_g.split(/[^GH0-9.]+/i).map(s => s.toUpperCase()).includes(entry.strongs_base.toUpperCase());
        tab = placeStrongsMatch ? "place" : "person";
      }
      setMetavTab(tab);
      setMetavLoading(false);
    }).catch(() => { if (!cancelled) setMetavLoading(false); });
    return () => { cancelled = true; };
  }, [entry && entry.id, boundLoading, boundEntity]);

  // AI description fallback for PN entries with no metaV data
  const [aiDescription, setAiDescription] = useState(null);
  const [aiDescLoading, setAiDescLoading] = useState(false);
  useEffect(() => {
    setAiDescription(null);
    setAiDescLoading(false);
    if (boundLoading || boundEntity) return;   // a verified bind replaces the AI blurb
    if (metavLoading) return;
    if (metavData && metavType === "person" && !isGentilic && !metavData._slim) return; // rich person bio replaces AI; groups + SLIM cards still get the summary
    if (metavData && metavType === "place" && metavData.strongs_g?.length > 0) return; // place has LSJ via strongs_g
    if (isHebrew) return; // BDB covers Hebrew words
    if (!isPN) return; // only for proper nouns
    const name = extractProperName(entry.pnName || entry.gloss || "");
    if (!name || name.length < 2) return;
    let cancelled = false;
    setAiDescLoading(true);
    const curText = entry.isKjv ? "kjv" : entry.isBsb ? "bsb" : entry.isHeb ? "heb" : "abp";
    api.metavAiDescription(name, entry.book, entry.chapter, entry.verse, curText)
      .then(d => { if (!cancelled && !d.error) setAiDescription(d.description || null); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setAiDescLoading(false); });
    return () => { cancelled = true; };
  }, [entry && entry.id, metavData, metavLoading, boundLoading, boundEntity]);

  // Hebrew BDB lookup. Start loading=true for a Hebrew word so a fresh mount's first
  // frame shows "Loading…", never a premature "Not found in BDB" before the lookup runs
  // (only Hebrew words render the BDB block, so this is inert for everything else).
  const [bdbEntry, setBdbEntry] = useState(null);
  const [bdbLoading, setBdbLoading] = useState(!!isHebrewWord);
  useEffect(() => {
    setBdbEntry(null);
    // FRAME-0 (audit site 1): clear the flag on the no-fetch path — a stuck
    // loading hold would blank the hero forever, worse than the flash it fixes.
    if (!isHebrewWord || !entry.strongs) { setBdbLoading(false); return; }
    let cancelled = false;
    setBdbLoading(true);
    api.bdb(entry.strongs)
      .then(d => { if (!cancelled) { setBdbEntry(d.error ? null : d); setBdbLoading(false); } })
      .catch(() => { if (!cancelled) { setBdbEntry(null); setBdbLoading(false); } });
    return () => { cancelled = true; };
  }, [entry && entry.id]);

  // English verse text for the quote — BSB for BSB words, else KJV (KJV mode, a
  // Hebrew word, or a place card). Held in kjvVerseText; the source is picked here.
  // FRAME-0 (audit site 7): undefined = still loading (the 52-ask-corpus sentinel
  // pattern); "" = resolved-empty. The quote line shows "Loading…" while undefined
  // instead of painting "—" and swapping.
  const [kjvVerseText, setKjvVerseText] = useState(undefined);
  useEffect(() => {
    if (!entry || (!entry.isKjv && !entry.isBsb && !isHebrew && !(metavType === "place" && !isPN))) { setKjvVerseText(""); return; }
    setKjvVerseText(undefined);
    let cancelled = false;
    const fetchVerse = entry.isBsb ? api.bsbVerse : api.kjvVerse;
    fetchVerse(entry.book, entry.chapter, entry.verse)
      .then(d => { if (!cancelled) setKjvVerseText(d.text || ""); })
      .catch(() => { if (!cancelled) setKjvVerseText(""); });
    return () => { cancelled = true; };
  }, [entry && entry.id]);

  const [lsjEntry, setLsjEntry] = useState(null);
  // Same frame-0 rule as BDB: start loading=true when a lookup will run at mount, so a
  // fresh mount shows "Loading…" rather than a premature "Not found." before the LSJ
  // lookup has even started (placeStrongs is null at mount, so it's not in the condition).
  const [lsjLoading, setLsjLoading] = useState(() => !isHebrew && !!(entry && (entry.greek || entry.strongs_raw)));
  const [lsjSummary, setLsjSummary] = useState(null);
  const [lsjSummaryLoading, setLsjSummaryLoading] = useState(false);
  const [lexica, setLexica] = useState(null);
  // The numbering crosswalk (alias_note) rides the /api/lexica response — on a REAL entry AND on
  // its not-found 404 — so it survives whichever card body renders (Lexica, LSJ, bare). Held in
  // its OWN state, separate from `lexica`, so it can show even when the word has no Lexica entry
  // and falls to LSJ. Rendered ONCE at the shared Definition-section layer, never per-body.
  const [aliasNote, setAliasNote] = useState(null);
  // The Lexica fork lookup needs its OWN loading flag (init true when a lookup runs at mount)
  // so the Definition block can wait for it before drawing the LSJ fallback — without it a
  // fork word (θεός) paints the LSJ card first, then swaps to the Lexica card when this lands.
  const [lexicaLoading, setLexicaLoading] = useState(() => {
    const sn = entry && (entry.strongs_raw || entry.strongs_base);
    return !!(sn && sn !== "*");
  });

  useEffect(() => {
    setLsjEntry(null);
    setLsjSummary(null);
    // For PN place entries with a mapped strongs_g, use that for LSJ lookup
    const placeStrongs = (isPN && metavType === "place" && metavData?.strongs_g?.length > 0)
      ? metavData.strongs_g.replace(/^G/i, "") : null;
    const canLookup = !isHebrew && entry && (entry.greek || entry.strongs_raw || placeStrongs);
    if (!canLookup) { setLsjLoading(false); return; }
    let cancelled = false;
    setLsjLoading(true);
    api.lsj(entry.greek || "", placeStrongs || entry.strongs_raw)
      .then(d => {
        if (!cancelled) { setLsjEntry(d.error ? null : d); setLsjLoading(false); }
      })
      .catch(() => {
        if (!cancelled) { setLsjEntry(null); setLsjLoading(false); }
      });
    return () => { cancelled = true; };
  }, [entry && entry.id, metavType, metavData?.strongs_g]);

  useEffect(() => {
    if (!lsjEntry || lsjEntry.source === "strongs") { setLsjSummary(null); setLsjSummaryLoading(false); return; }
    let cancelled = false;
    setLsjSummaryLoading(true);
    const summaryStrongs = lsjEntry.source === "abp_ext" ? lsjEntry.key : "";
    // Always request the verse-agnostic ("general") summary. A word's LSJ summary
    // is cached/shown universally, so it must not name the verse it was first clicked in.
    api.lsjSummary(lsjEntry.key, summaryStrongs)
      .then(d => { if (!cancelled) setLsjSummary(d); })
      .catch(() => { if (!cancelled) setLsjSummary(null); })
      .finally(() => { if (!cancelled) setLsjSummaryLoading(false); });
    return () => { cancelled = true; };
  }, [lsjEntry && lsjEntry.key, entry && entry.id]);

  // Lexica dictionary entry (verse-grounded), keyed by Strong's. Admin-only during rollout — the
  // server 404s for everyone else, so only fetch when signed in (skips the call for the logged-out
  // public). When present it REPLACES the LSJ card body + the up-top plain gloss; when absent the
  // card is exactly as before.
  useEffect(() => {
    setLexica(null);
    setAliasNote(null);
    // Look the entry up by the FULL number (strongs_raw keeps the dotted ".N"), NOT strongs_base
    // (which drops it). A dotted cognate — ekklesiazo G1577.1 / ekklesiastes G1577.2 sitting under
    // ekklesia G1577 — must fetch its OWN number so it 404s and falls through to its own LSJ card,
    // instead of borrowing the base word's definition. Keyed by strongs_base, every one of the
    // ~3619 dotted words would inherit its base's entry once that base is built.
    const sn = entry && (entry.strongs_raw || entry.strongs_base);
    if (!sn || sn === "*") { setLexicaLoading(false); return; }
    let cancelled = false;
    setLexicaLoading(true);
    api.lexica(sn)
      .then(d => {
        if (cancelled) return;
        setLexica(d && !d.error ? d : null);
        setAliasNote(d ? (d.alias_note || null) : null);   // rides both the real entry and the 404
      })
      .catch(() => { if (!cancelled) { setLexica(null); setAliasNote(null); } })
      .finally(() => { if (!cancelled) setLexicaLoading(false); });
    return () => { cancelled = true; };
  }, [entry && entry.id]);

  if (!entry) return null;

  const barWidth = Math.min(100, (occurrences / Math.max(1, totalResults)) * 100);
  const morphLine = (entry.greek && !isHebrew) ? decodeMorph(entry.morph, entry.greek, entry.strongs_base)
    : (isHebrew ? (entry.grammar || "") : "");   // Hebrew: the decoded TAHOT grammar, same card slot as Greek
  // --------------------------------------------------------------------------
  // Panel descriptor — resolve the isPN / isHebrew / metavType tangle into ONE
  // place: a `hero` block and an ordered `sections` list. The return below is
  // dumb: it renders `hero`, then `sections.map(renderSection)` — no decisions.
  // --------------------------------------------------------------------------
  // pnName FIRST (Part-3 fix 2026-07-29, Mat 23:26 "Blind"): the lookups were unified
  // on the resolved name in lane 1 but the TITLE still read the raw gloss, whose first
  // capital can be a stray sentence word ("Blind Pharisee," -> "Blind"). One precedence
  // everywhere: the word the bind resolved on is the word the header shows.
  const properName = extractProperName(entry.pnName || entry.gloss);
  const nameOrGloss = (isPN || metavData) ? properName : entry.gloss;
  // trimPunct: tail punctuation only. trimTail (punct + leading-article strip) is for
  // NAME displays; the in-verse gloss must stay VERBATIM — stripArticles was eating
  // real wording ("His disciples" → "disciples", Mat 28:13, JP sighting 2026-07-31).
  const trimPunct = (s) => (s)?.replace(/[.,;:!?—-]+$/, "").trim();
  const trimTail = (s) => stripArticles(trimPunct(s));
  // The clicked word's INFLECTED form — the surface form as it appears in THIS verse —
  // when the reading text carries one: the Hebrew OT reader (entry.inflected = the
  // pointed word) and BSB (entry.inflected = the Berean-tables original word) set it at
  // the click. The dictionary form (lemma) stays the BIG headword for EVERY text, so the
  // card's headline word means the same thing everywhere (ABP/KJV have no surface form);
  // the inflected form shows on a small "in this verse" line just beneath it.
  const heroInflected = (entry.inflected || "").trim();
  const heroInflectedTranslit = (entry.inflectedTranslit || "").trim();
  // Dotted frozen idiom (ἀνὰ μέσον, G303.1): the header is HAND-AUTHORED in structural.py and shown
  // VERBATIM — the dotted_lexicon row's base-neighbour lemma + the ABP romanizer mangle a two-word
  // phrase ("ἀνάμέσος / anámésos"). Use the authored phrase/translit, never entry.greek/entry.translit.
  const idiomHdr = (lexica && lexica.kind === "idiom") ? lexica : null;
  // R-2 flip: with a Greek identity served, the hero shows the GREEK form (control
  // C1 — Δαυίδ up top, the name on the gloss line) and lemma-only cards add the
  // honest state line below. greekId null (switch OFF / none-bucket) leaves every
  // value exactly as before.
  const giLemma = (greekId && greekId.lemma) || "";
  // Hebrew-flash fix, hero leg: while the identity fetch is pending the HEADLINE
  // holds blank (nbsp keeps the line height) instead of painting the English
  // name and swapping to the Greek form a beat later. Paints once on resolve.
  // FRAME-0 (audit site 1): the Hebrew hero used to paint the English gloss in the
  // big headword slot while the BDB lookup ran, then swap to Hebrew (the "sons of
  // Noah" instance). Same hold as greekIdPending: blank until the real data lands.
  const hero = (greekIdPending || (isHebrewWord && bdbLoading)) ? {
    he: false, noGloss: true, script: " ", translit: "", standaloneGloss: "", morph: "",
  } : {
    he: isHebrew,
    noGloss: isPN && !entry.greek && !isHebrew && !giLemma,
    // MERGED compound card (JP sweep verdict 2026-07-31): the IDENTITY JOIN is
    // the ONLY hero source — per-slot word fields (entry.greek/translit, joined
    // naively at the chip) produced half-names ("Γάδ" hero, "Gád · Dibon" row).
    script: idiomHdr ? idiomHdr.phrase : (isHebrew ? (bdbEntry?.lemma || entry.gloss)
      : (entry.pnMergePos != null ? (giLemma || nameOrGloss) : (entry.greek || giLemma || nameOrGloss))),
    translit: idiomHdr ? idiomHdr.translit : (isHebrew ? bdbEntry?.xlit
      : (entry.pnMergePos != null ? (giLemma ? greekId.translit : "")
        : (entry.translit || (giLemma ? greekId.translit : "")))),
    standaloneGloss: (isPN || metavData) ? trimTail(entry.pnDisplay || properName)
      : trimPunct(entry.greek && (entry.gloss || "").trim().split(/\s+/).length > 2 ? (entry.english_head || entry.gloss) : entry.gloss),
    morph: morphLine,
  };
  // The small "in this verse" line shows the inflected form — only when we have one AND
  // it differs from the headword lemma (indeclinable words can coincide → skip it). For an
  // idiom the abp_surface form is the same phrase in bh's accent-only spelling (αναμέσον) —
  // redundant + mangled-looking next to the authored lemma, so drop it.
  // FRAME-0: joins the greekIdPending hold — since Phase-6 name slots carry a
  // printed form, this line painted during the pending window and then deduped
  // away when the identity landed with form == lemma (the Canaan flash, JP
  // report 2026-07-28). Settled behavior unchanged: a differing inflected form
  // still shows; an identical one is still (correctly) not repeated.
  // Accent-divergence fix (JP sighting Νῶε/Νώε 1Ch 1:4, 2026-07-29): the surface form and
  // the lemma come from two sources whose accents/breathings/case legitimately differ
  // (abp_surface is stripped-down Greek). Compare FOLDED (greekFold, compare-only) so the
  // section fires only when the LETTERS differ — real inflection, never editorial noise.
  // What renders is still the raw forms, real accents and all.
  const heroForm = (!greekIdPending && !idiomHdr && heroInflected && greekFold(heroInflected) !== greekFold(hero.script)) ? heroInflected : "";
  // The clicked word's CONTEXTUAL english (its sense IN THIS VERSE). When the card shows
  // an inflected "in this verse" line, that english belongs next to the FORM it actually
  // translates — not glued to the dictionary lemma above. Relocate it down whenever there's
  // a form to attach it to (normal words only; for a proper noun the "gloss" is a name and
  // stays as the headword).
  const relocateGloss = !!(heroForm && hero.standaloneGloss && !hero.noGloss && !isPN && !metavData);
  // The plain-meaning `word_gloss` dictionary sense ("spirit, breath"), threaded for ABP,
  // KJV, BSB, and Hebrew alike (each text's chapter endpoint joins word_gloss).
  const heroLemmaGloss = entry.lemmaGloss ? shortLemmaGloss(entry.lemmaGloss) : "";
  // Show that dictionary gloss up top for EVERY word that has one and isn't a name/place.
  // When there's an "in this verse" form line, the contextual english drops onto it
  // (relocateGloss); when there isn't (KJV, an ABP word with no printed form), the meaning
  // simply replaces the in-verse word up top. A form word with NO gloss keeps the old
  // behavior: empty up top, contextual english on the form line (don't duplicate it).
  const showLemmaGloss = !!(heroLemmaGloss && !hero.noGloss && !isPN && !metavData);
  const heroTopGloss = showLemmaGloss ? heroLemmaGloss : (relocateGloss ? "" : hero.standaloneGloss);
  // Show "translit · gloss" on one line whenever there's both — same for Greek and
  // Hebrew so the two cards match. Falls back to a standalone gloss line only when
  // there's no transliteration.
  const heroInlineGloss = !!(hero.translit && heroTopGloss && !hero.noGloss);

  // The form-vs-person scope note (sentence + its guards: scopeNoteText, top of this
  // file). It renders in the hero's existing status slot — the same slot and muted
  // style as the "ABP-only form" line — so it costs no new structure and no layout
  // change. `headerStrongs` is SHARED with the header badge below, so the note can
  // never name a different number than the one printed on screen.
  const headerStrongs = greekId ? (greekId.greek_strongs || "PN") : (greekIdPending ? "PN" : entry.strongs);
  // The noun the sentence ends on: the bound card's own kind, else the name-path
  // card's. TIPNR 'other' records (deities, months, constellations) have no natural
  // noun here — "the one this verse names" is true of every kind, so they get that
  // rather than being dropped. Shows on EVERY name card with a real number and an
  // identity block, not only the shared-form ones: the distinction is always true.
  const scopeKind = boundEntity
    ? (boundEntity.section === "place" ? "place"
       : boundEntity.people_group ? "group"
       : boundEntity.section === "person" ? "person" : "one")
    : (metavType === "person" && metavData) ? (isGentilic ? "group" : "person")
    : (metavType === "place" && metavData) ? "place" : "";
  // The sentence calls the hero a "name form", so the hero must actually be printing
  // a script form — never the English-name fallback `nameOrGloss`.
  const heroIsScriptForm = !!(idiomHdr || (isHebrew ? bdbEntry?.lemma : (entry.greek || giLemma)));
  const scopeNote = scopeNoteText(headerStrongs, heroIsScriptForm ? hero.script : "", scopeKind);

  // Verse + place sections show an English reading text (not ABP) for Hebrew /
  // KJV-mode / BSB-mode / place words. BSB pulls BSB text; the rest pull KJV.
  const useKjvText = entry.isKjv || entry.isBsb || isHebrew || (metavType === "place" && !isPN);

  // Ordered list of stacked sections. BDB and LSJ are mutually exclusive (Hebrew
  // gets BDB; everything else may get LSJ) — same either/or as the old ternary.
  const sections = [];
  // A verified verse-bind (Issue 2) leads the card. metaV/aidesc data is only fetched
  // when there is NO bind (the fetches above wait on the bind), so their own push
  // conditions already evaluate false under a bind — nothing name-based leaks through.
  if (boundEntity) sections.push("boundEntity");
  if (metavLoading || metavPersonData || metavPlaceData) sections.push("metav");
  if (aiDescription || aiDescLoading) sections.push("aidesc");
  // R-2 flip: under a served Greek identity the Hebrew number is a CROSS-REFERENCE,
  // not the identity — the BDB block (the Hebrew identity presentation) gives way to
  // the quiet cross-ref section below; Word study by the Hebrew number stays one
  // click away there (nothing findable before becomes unfindable).
  if (isHebrewWord && !greekId && !greekIdPending) sections.push("bdb");
  // metavType "person" suppresses the definition (a real proper-noun person has no useful
  // lexical entry). θεός (G2316) is no longer special-cased here: it now skips metaV entirely
  // (see the lookup gate above), so its Lexica entry leads as the definition like any word.
  else if ((!isPN || (metavType === "place" && metavData?.strongs_g?.length > 0))
           && metavType !== "person"
           && !aiDescription && !aiDescLoading
           && (entry.greek || entry.strongs_raw || metavData?.strongs_g?.length > 0)) sections.push("lsj");
  // A verse-bound entity carries a real Strong's number (TIPNR mapped these people/places
  // onto H/G numbers), so it gets the SAME occurrence controls every other word has — the
  // real word-occurrence list, where each verse shows the surface form.
  const boundOcc = !!boundEntity;
  // Every word shows occurrences for the ONE text being read, not all Bibles at once — the
  // cross-Bible breakdown lives in Word study. activeText is read off the entry (a Hebrew word,
  // incl. a backfilled proper noun whose ABP form keys on its Hebrew base, shows the matching
  // line below).
  const activeText = entry.isKjv ? "kjv" : entry.isBsb ? "bsb" : entry.isHeb ? "heb" : "abp";
  // R-2 flip: a served Greek identity replaces the three ABP-count shapes below
  // (abpOcc / pnOcc / hebrewAbpOcc) with ONE Greek-keyed count section + the
  // Hebrew cross-ref section. greekId null -> the old lines, unchanged.
  if (greekId && activeText === "abp") {
    sections.push("greekIdOcc");
    if (greekId.hebrew_base) sections.push("hebCrossRef");
  }
  if (!greekId && !greekIdPending && !isHebrewWord && (!isPN || boundOcc) && !entry.isKjv && !entry.isBsb && !entry.isExtra && abpCount !== null && abpCount > 0) sections.push("abpOcc");
  // Non-canon "other" books (Apostolic Fathers chip mode): suppress the occurrence
  // links/counts (the LXX cross-link above + this in-book count) until Lexicon search is
  // wired. Re-enable: drop `!entry.isExtra` above + uncomment extraOcc.
  // if (entry.isExtra && extraCount !== null && extraCount > 0) sections.push("extraOcc");
  if (entry.isKjv && !isHebrew && !isPN && kjvCount !== null && kjvCount > 0) sections.push("kjvOcc");
  if (entry.isBsb && !isPN && !isHebrew && bsbCount !== null && bsbCount > 0) sections.push("bsbOcc");
  if (!greekId && !greekIdPending && !entry.isKjv && !entry.isBsb && isPN && pnCount !== null && pnCount > 0 && onNameSearch) sections.push("pnOcc");
  // A Hebrew word shows occurrences only for the text being read (Hebrew OT / KJV / BSB, or ABP
  // via its Hebrew base for a backfilled proper noun); each opens that source in Word study,
  // where the full cross-Bible breakdown lives.
  if (!greekId && !greekIdPending && isHebrewWord && activeText === "abp" && abpBaseCount !== null && abpBaseCount > 0) sections.push("hebrewAbpOcc");
  if (isHebrewWord && activeText === "heb" && hebCount !== null && hebCount > 0) sections.push("hebrewOtOcc");
  if (isHebrewWord && activeText === "kjv" && kjvCount !== null && kjvCount > 0) sections.push("hebrewKjvOcc");
  if (isHebrewWord && activeText === "bsb" && bsbCount !== null && bsbCount > 0) sections.push("hebrewBsbOcc");
  if (entry.derivation) sections.push("derivation");
  if (entry.book && !entry.isExtra) sections.push("verse");
  if (occurrences > 0 || totalResults > 0) sections.push("frequency");

  const renderSection = (id) => {
    switch (id) {
    case "boundEntity": {
      if (boundLoading && !boundEntity)
        return <section key="boundEntity" className="sec pnbound"><div className="lsj-def lsj-def--loading">Looking up…</div></section>;
      if (!boundEntity) return null;
      const be = boundEntity;
      // C: a people-group click renders "People / Clan" and drops the ancestor's
      // individual kin, so "the Jews" never shows Judah's own parents. (Predicate
      // shared with tipnrBody — one definition, top of this file.)
      const peopleClan = isPeopleClan(be);
      // A bound person cross-linked to its rich MetaV record (David-style badges /
      // born-died / kin) — served on be.metav only when it clears the bio bar AND the
      // People/Clan gate (the server nulls it for a gentilic; !peopleClan double-guards
      // here). When present it fills the card body IN PLACE OF the thin TIPNR facts;
      // TIPNR stays the spine (header + "Matched to this verse"). No link / below-bio /
      // gentilic -> falls back to the thin facts below.
      const richPerson = !!be.metav && !peopleClan;
      // When the group treatment fires, title the card with the PEOPLE term (the clicked
      // gloss, e.g. "Jews") and leave the ancestor to the Lineage line — the card is about
      // the people, not the individual.
      const clickName = extractProperName(entry.pnName || entry.gloss || "");
      const heroName = (peopleClan && clickName) ? clickName : be.name;
      // TIPNR 'other'-section records (34: deities, groups, months, constellations, the
      // temple pillars, Satan, Leviathan) used to all read "Identity". JP+reviewer ruling
      // 2026-07-16 (render charter R1–R4): type the heading from TIPNR's OWN description
      // words — no imported category (no "pagan"), the descr line carries the detail.
      const otherLabel = /deity/i.test(be.desc || "") ? "Deity"
                       : /group/i.test(be.desc || "") ? "Group"
                       : /\b(angel|monster)\b/i.test(be.desc || "") ? "Being"
                       : "Reference";
      // Header unification (JP ruling 2026-07-29): ONE card family, so the bound card
      // titles match the name-path card ("Biblical Person"/"Biblical Place", not the
      // bare "Person"/"Place" this path grew on its own). Densities and badges differ;
      // the family name doesn't.
      const label = peopleClan ? "People / Clan"
                  : be.section === "place" ? "Biblical Place" : be.section === "person" ? "Biblical Person" : otherLabel;
      const clean = cleanTipnr;   // drops TIPNR's "(?)" uncertainty marker
      // TIPNR's descr is a genuine description for PERSONS ("Man living at the time of …")
      // but for PLACES it's often just the name, a bare id ("Bethel_1"), or a cross-ref
      // string ("Mount Paran= in Paran (…)"). Cut the cross-ref tail at '=', drop a trailing
      // "_N" id; the "same as the name" test then hides whatever is left when it's just the
      // name, so only a real description survives as the subtitle.
      const descText = clean((be.desc || "").split("=")[0]).replace(/_\d+$/, "").trim();
      // a clean one-liner: the person 'desc' is short; for a place fall to the
      // summary's first clause (before "first/only mentioned").
      let line = (descText && descText.toLowerCase() !== be.name.toLowerCase() && descText.length > 4) ? descText : "";
      if (!line && be.summary)
        line = be.summary.split(/,?\s*(?:first mentioned|only mentioned|referred to)/i)[0].replace(/\(+$/, "");
      line = clean(line);
      // TIPNR's summary opens "A location …" for nearly every place — a generic placeholder,
      // not a real description. Drop it; real descriptions still show.
      if (/^(a location|a place|location|place)\.?$/i.test(line)) line = "";
      // For a People/Clan, the ancestor's own bio ("Man living at the time of …") misframes
      // the collective — drop it; the lineage line below carries the honest link instead.
      if (peopleClan) line = "";
      // TRIBAL EPONYMS: see EPONYM_LINES at the top of this file. Guarded by the
      // TIPNR bio text so namesakes (Judah@Neh, King Manasseh) keep their plain card.
      const eponym = be.section === "person" && !peopleClan && EPONYM_LINES[be.name]
        && /jacob's son|joseph's son|patriarchs|renamed/i.test(descText || "")
        ? EPONYM_LINES[be.name] : null;
      if (eponym) line = eponym;
      // The entity's verses are no longer listed here — the standard occurrence controls
      // below ("× in ABP / Hebrew OT / KJV / BSB") show the real word in each verse, which
      // supersedes the old TIPNR ref-list (it listed verse pointers, some without the word).
      const hasMap = be.section === "place" && be.lat && be.lon;
      const placeNote = be.section === "place" && !hasMap && be.ambiguous;
      // THE CARD BODY — one shape, either source (both builders + IdentityBody are at
      // the top of this file). Built as DATA so it can be COUNTED: a card whose whole
      // body is <=1 element reads as a floating name echo + orphan row + stranded
      // badge (the Levites / Pharaoh-at-Exo-3 shape); see `thin` below.
      const body = richPerson ? metavBody(be.metav) : tipnrBody(be, line);
      const bodyCount = bodyFieldCount(body);
      // THIN = a sparse non-rich card with no map / note to anchor the badge. One shared
      // arrangement (not a per-branch fix): drop the name echo (the hero above carries
      // it), promote the single body line, tuck the badge inline on its baseline. Covers
      // PERSON-thin, PEOPLE/CLAN, and a coordinate-less place alike.
      // kind='witness' (Lane A, 2026-07-30): the bind rests on ABP's own text, not a
      // TIPNR verse listing — the card must SAY so. Sentence JP-approved verbatim
      // 2026-07-30 (claims only bound facts; no manuscript-cause assertion).
      // rule='context-run' (Lane C, 2026-07-30): multi-candidate name, identity fixed
      // by the per-name run audit. DISTINCT sentence, reviewer-proposed + JP-approved
      // verbatim ({person/place} filled from the entity's own section).
      // The sentence claims what ABP PRINTS, so it must show the CLICKED word — never
      // the bound entity's display name, which can differ (jacob -> Israel record;
      // "ABP reads Israel here" was false — caught served, 2026-07-30).
      const witnessName = clickName || be.name;
      const witnessNote = be.kind === "witness"
        ? (be.rule === "context-run"
          ? <p className="detail-p detail-p--meta" style={{color:"var(--ink-4)", fontStyle:"italic"}}>
              ABP's Greek text reads {witnessName} here. Several people share this name; the
              identification follows the surrounding passage, where only this{" "}
              {be.section === "place" ? "place" : "person"} appears.
            </p>
          : be.rule === "verse-offset"
          // rule='verse-offset' (pile-3 closure, 2026-07-30): same entity one verse
          // seam over — the Greek and Hebrew split the list differently. Sentence
          // JP-approved verbatim 2026-07-30.
          ? <p className="detail-p detail-p--meta" style={{color:"var(--ink-4)", fontStyle:"italic"}}>
              ABP's Greek text reads {witnessName} here. The Greek and Hebrew texts divide this
              list at different verse breaks; the reference index lists this name at the
              neighboring verse.
            </p>
          : <p className="detail-p detail-p--meta" style={{color:"var(--ink-4)", fontStyle:"italic"}}>
              ABP's Greek text reads {witnessName} here. The reference index does not list this
              name at this verse; the identification follows ABP's reading.
            </p>)
        : null;
      // The test counts RENDERED FIELDS and never the source (reviewer ruling
      // 2026-08-09). It used to carry `!richPerson`, so a sparse card could only ever
      // be detected as sparse on ONE source — the same source-branching this ticket
      // deletes, relocated into the detector.
      const thin = !hasMap && !placeNote && !witnessNote && ((line ? 1 : 0) + bodyCount) <= 1;
      // Match-state placement (JP amendment 2026-07-30, third pass — supersedes the
      // under-description slot): "Matched to this verse" is the LAST element of the
      // person/place section — below tags, dates and relation rows — reading as the
      // provenance seal on the whole block. It's a claim about the card's bind, not
      // a modifier of the description. TIPNR badge stays in the section header.
      // Warrant wording (JP-approved 2026-07-30): "bound to this specific verse" —
      // NOT "explicitly": binds are MIXED (binder tiers + hand rulings + witness),
      // verified before wording shipped.
      // Entity-type aware (issue-log 2026-07-31): a PEOPLE/CLAN card said "This
      // person is bound…" (G2455 Jews). peopleClan → "group"; sentence unchanged.
      const kindWord = be.section === "place" ? "place"
        : peopleClan ? "group"
        : be.section === "person" ? "person" : "name";
      const matchState = (
        <div><WarrantTag cls="pnbound-badge"
          warrant={`This ${kindWord} is bound to this specific verse in our records.`}>
          Matched to this verse</WarrantTag></div>
      );
      const tipnrWarrant = `TIPNR — Tyndale Individualised Proper Names with all References; source of this card's ${kindWord} data.`;
      const bothWarrant = `TIPNR (Tyndale proper-name reference) + MetaV verse data — sources of this card's ${kindWord} data.`;
      // NAME ALWAYS SHOWS (JP ruling 2026-07-30, reversing the 2026-07-16 differs-only
      // rule): every person/place section opens with the ENTITY's name in bold. The
      // old rule suppressed it when it matched the clicked word ("stutter"), but on
      // Greek-headed cards that left no prominent English name at all, and the
      // conditional read as randomness. Header = the clicked FORM, this line = the
      // REFERENT; when they coincide that's information, not noise.
      if (thin) {
        // Sparse ARRANGEMENT, same template: promote the one element we have onto a
        // single row under the name. `thin` caps the count at 1, so `line` and the
        // body can never both be present here.
        const opener = line ? <span>{line}</span> : <IdentityBody {...body} />;
        return (
          <section key="boundEntity" className="sec pnbound">
            <h4 className="sec-head"><span className="sec-t">{label}</span><WarrantTag cls="bdb-badge" warrant={tipnrWarrant}>TIPNR</WarrantTag></h4>
            <div className="pnbound-name">{heroName}</div>
            {(line || bodyCount > 0) && <div className="pnbound-thinrow">{opener}</div>}
            {matchState}
          </section>
        );
      }
      return (
        <section key="boundEntity" className="sec pnbound">
          {/* Contract §1 (audit B): when the rich MetaV body renders, the card blends two
              sources — the badge credits both. CONDITIONAL on the data actually shown
              (richPerson), never on the card variant: a TIPNR-only card stays "TIPNR". */}
          <h4 className="sec-head"><span className="sec-t">{label}</span><WarrantTag cls="bdb-badge" warrant={richPerson ? bothWarrant : tipnrWarrant}>{richPerson ? "MetaV/TIPNR" : "TIPNR"}</WarrantTag></h4>
          <div className="pnbound-name">{heroName}</div>
          {line && <p className="pnbound-desc">{line}</p>}
          {eponym && bodyCount > 0 && <div className="detail-h">The man</div>}
          <IdentityBody {...body} />
          {be.section === "place" && (be.lat && be.lon
            ? <LeafletMap lat={be.lat} lon={be.lon} name={be.name} />
            : be.ambiguous
              ? <p className="detail-p detail-p--meta" style={{color:"var(--ink-4)", fontStyle:"italic"}}>Several places share this name — map hidden to avoid a wrong location.</p>
              : null)}
          {witnessNote}
          {matchState}
        </section>
      );
    }
    case "metav": return (
      <section key="metav" className="sec">
        {metavLoading ? (
          <div className="lsj-def lsj-def--loading">Looking up…</div>
        ) : <>
          {metavType === "person" && metavData ? (
          <div className="metav-person">
            <h4 className="sec-head">
              {metavHasBoth ? (
                <span className="metav-titleswitch">
                  Biblical{" "}
                  <button className={"metav-ts-b"+(metavTab==="person"?" on":"")} onClick={()=>setMetavTab("person")}>Person</button>
                  <span className="metav-ts-sep">/</span>
                  <button className={"metav-ts-b"+(metavTab==="place"?" on":"")} onClick={()=>setMetavTab("place")}>Place</button>
                </span>
              ) : <span className="sec-t">{isGentilic ? "People / Clan" : "Biblical Person"}</span>}
              <WarrantTag cls="lsj-badge" warrant="MetaV — verse-level Bible reference data; source of this card's data.">metaV</WarrantTag>
            </h4>
            {/* NAME ALWAYS SHOWS (JP ruling 2026-07-30) — same line as the bound card. */}
            {metavData.name && <div className="pnbound-name">{metavData.name}</div>}
            {metavData._slim ? (
              /* SLIM body (Paul-class): only what metaV/TIPNR actually hold — gender
                 tag, the lone family link if any, a TIPNR one-liner when the server
                 attaches one. The AI note renders as its own section (gate above),
                 and the shared caveat below carries the confident sole-referent
                 label. Deliberately sparser than the full card — it must not imply
                 completeness. */
              <div className="metav-person--slim">
                {metavData.gender && (
                  <div className="metav-meta">
                    <span className="metav-tag">{metavData.gender === "M" ? "Male" : "Female"}</span>
                  </div>
                )}
                {metavData.tipnr_desc && <p className="detail-p detail-p--meta">{metavData.tipnr_desc}</p>}
                {(metavData.relationships || []).slice(0, 1).map(r => (
                  <div key={r.id} className="metav-rel-row">
                    <span className="metav-rel-label">{
                      r.type === "father" ? "Father" : r.type === "mother" ? "Mother"
                      : r.type === "spouseOrConcubine" ? "Spouse" : r.type === "child" ? "Child"
                      : r.type === "sibling" ? "Sibling" : "Kin"}</span>
                    <span className="metav-rel-names">{r.name}</span>
                  </div>
                ))}
              </div>
            ) : <MetavPersonBody data={metavData} withEponym={!isGentilic} />}
          </div>
        ) : metavType === "place" && metavData ? (
          <div className="metav-place">
            <h4 className="sec-head">
              {metavHasBoth ? (
                <span className="metav-titleswitch">
                  Biblical{" "}
                  <button className={"metav-ts-b"+(metavTab==="person"?" on":"")} onClick={()=>setMetavTab("person")}>Person</button>
                  <span className="metav-ts-sep">/</span>
                  <button className={"metav-ts-b"+(metavTab==="place"?" on":"")} onClick={()=>setMetavTab("place")}>Place</button>
                </span>
              ) : <span className="sec-t">{isGentilic ? "Homeland" : "Biblical Place"}</span>}
              <WarrantTag cls="lsj-badge" warrant="MetaV — verse-level Bible reference data; source of this card's data.">metaV</WarrantTag>
            </h4>
            {/* NAME ALWAYS SHOWS (JP ruling 2026-07-30) — same line as the bound card. */}
            {metavData.name && <div className="pnbound-name">{metavData.name}</div>}
            {cleanPlaceComment(metavData.comment) && <p className="detail-p detail-p--meta">{cleanPlaceComment(metavData.comment)}</p>}
            {metavData.lat && metavData.lon
              ? <LeafletMap lat={metavData.lat} lon={metavData.lon} name={metavData.name} />
              : <p className="detail-p detail-p--meta" style={{color:"var(--ink-4)", fontStyle:"italic"}}>
                  {metavData.ambiguous
                    ? "Several places share this name — map hidden to avoid a wrong location."
                    : "Location unknown"}
                </p>
            }
          </div>
        ) : null}
        {/* Contract §4 state 2: this card is a NAME lookup (it only renders when no
            verse-bind exists) — say so, in the same voice as the AI block's caveat.
            TICKET_pn_label_confidence (JP-ruled copy, 2026-07-29): when the server says
            the name has exactly ONE referent in our records (sole_referent — exact-match
            only, fuzzy never earns it), the label carries that confidence instead of
            reading like a guess. Gentilic person cards ("People / Clan") keep the hedge —
            "only person of this name" misdescribes a people-group. */}
        {/* Match-state unification (JP amendment 2026-07-30, Seth card): the CONFIDENT
            name-match renders as the same pill as "Matched to this verse" — one
            element, one treatment, text "Matched by name"; the full disambiguation
            sentence survives as hover text. The HEDGED state ("not checked against
            this verse") deliberately stays prose: a pill would make the weak claim
            look as strong as the checked one — converting it is JP's call. */}
        {metavData && (
          metavData.sole_referent && (metavType === "place" || !isGentilic)
            ? <div><WarrantTag cls="pnbound-badge"
                warrant={`Matched by name — the only ${metavType === "place" ? "place" : "person"} of this name in our records.`}>
                Matched by name</WarrantTag></div>
            : <p className="detail-ai-caveat">Matched by name — not checked against this verse.</p>
        )}
        </>}
      </section>
    );
    case "aidesc": return (
      <section key="aidesc" className="sec">
        <h4 className="sec-head"><span className="sec-t">{metavType === "place" ? "Biblical Place" : "Biblical Reference"}</span><WarrantTag cls="lsj-badge lsj-badge--accent" warrant="AI-written summary — claims not verified against the verse text.">AI</WarrantTag></h4>
        {aiDescLoading
          ? <div className="lsj-def lsj-def--loading">Looking up…</div>
          : <>
              <p className="detail-p detail-p--meta">{renderInlineMd(aiDescription)}</p>
              <p className="detail-ai-caveat">AI-written summary — claims not verified against the verse text.</p>
            </>
        }
      </section>
    );
    case "bdb": return (
      <section key="bdb" className="sec">
        {/* The table is named `bdb` but holds STRONG'S HEBREW, not Brown-Driver-Briggs —
            the warrant must say Strong's (standing trap, data-model.md). */}
        <h4 className="sec-head"><span className="sec-t">Strong's Hebrew</span><WarrantTag cls="bdb-badge" warrant="Strong's Hebrew dictionary.">Strong's</WarrantTag></h4>
        {bdbLoading ? (
          <div className="lsj-def lsj-def--loading">Loading…</div>
        ) : bdbEntry ? (
          <div className="bdb-body">
            {bdbEntry.pronounce && <div className="bdb-xlit"><span className="bdb-pronounce">{bdbEntry.pronounce}</span></div>}
            {bdbEntry.part_of_speech && <span className="bdb-pos-badge">{bdbEntry.part_of_speech}</span>}
            {bdbEntry.description && <p className="detail-p detail-p--meta">{bdbEntry.description}</p>}
            {/* Under a verse-bound entity the BDB entry is the dictionary's, keyed by the
                shared word — it covers every sense, so it can describe a different referent
                than the one this verse names (the "Adam's home" gloss under the Assyrian
                Eden). Fixed line, makes no per-referent claim, no detection logic. */}
            {boundEntity && (
              <p className="detail-ai-caveat">Dictionary entry for the word — all its meanings, not only {boundEntity.section === "place" ? "this place" : boundEntity.section === "person" ? "this person" : "this name"}.</p>
            )}
          </div>
        ) : (
          <div className="lsj-def lsj-def--loading">Not found in Strong's Hebrew.</div>
        )}
      </section>
    );
    case "lsj": {
      const structural = !!(lexica && lexica.kind === "structural");
      const idiom = !!(lexica && lexica.kind === "idiom");   // dotted frozen phrase (ἀνὰ μέσον) — a content note, not the structural card
      // The Definition block draws from TWO lookups: the Lexica fork entry (the intended card
      // when it exists) and LSJ (the fallback). Until the Lexica lookup resolves we don't know
      // WHICH card this is, so hold the whole block neutral ("Definition · Loading…") instead of
      // painting the LSJ card first and swapping to the Lexica card (the θεός fork flash). Same
      // rule as the frame-0 fix: a block stays neutral until its own lookup resolves.
      const defnLoading = (lexicaLoading || lsjLoading) && !lexica;
      return (
      <section key="lsj" className="sec">
        <h4 className="sec-head">
          {defnLoading
            ? <span className="sec-t">Definition</span>
            : idiom
            ? <><span className="sec-t">Phrase</span><WarrantTag cls="lsj-badge" warrant="A fixed phrase (idiom) — its plain meaning, not a grammatical relation">Idiom</WarrantTag></>
            : structural
            ? <><span className="sec-t">Function</span><WarrantTag cls="lsj-badge" warrant="Structural word — its grammatical function, not a sense list">Grammar</WarrantTag></>
            : lexica
            ? <><span className="sec-t">Definition</span><WarrantTag cls="lsj-badge" warrant="Lexica dictionary — defined from the Bible's own usage">Lexica</WarrantTag></>
            : lsjSummary && lsjSummary.override
            ? <><span className="sec-t">Definition</span><WarrantTag cls="lsj-badge" warrant="Lexica editorial gloss — plain biblical sense foregrounded">Lexica</WarrantTag></>
            : lsjEntry && lsjEntry.source === "abp_ext"
              ? <><span className="sec-t">ABP Extended</span><WarrantTag cls="abp-badge" warrant="Apostolic Bible Polyglot extended lexicon entry.">ABP EXT</WarrantTag></>
            : lsjEntry && lsjEntry.source === "strongs"
              /* Strong's fallback (views_lsj.py serves it when no LSJ/abp_ext entry
                 exists) must NOT wear the LSJ header — mislabeled source + the
                 silent-fallback rule. Label JP-approved 2026-07-30. */
              ? <><span className="sec-t">Strong's Dictionary</span><WarrantTag cls="lsj-badge" warrant="No LSJ entry for this word — this is the Strong's dictionary definition">Strong's</WarrantTag></>
              : <><span className="sec-t">Liddell-Scott-Jones</span><WarrantTag cls="lsj-badge" warrant="Liddell-Scott-Jones — classical Greek lexicon.">LSJ</WarrantTag></>}
        </h4>
        {defnLoading ? (
          <div className="lsj-def lsj-def--loading">Loading…</div>
        ) : idiom ? (
          <div className="gram"><p className="gram-fn"><b>{lexica.phrase}</b> — {lexica.note}</p></div>
        ) : structural ? (
          <StructuralBody data={lexica} lsjEntry={lsjEntry} />
        ) : lexica ? (
          <LexicaBody lexica={lexica} lsjEntry={lsjEntry} />
        ) : lsjLoading ? (
          <div className="lsj-def lsj-def--loading">Loading…</div>
        ) : lsjEntry ? (
          <LsjBody lsjEntry={lsjEntry} lsjSummary={lsjSummary} summaryLoading={lsjSummaryLoading} />
        ) : (
          <div className="lsj-def lsj-def--loading">Not found.</div>
        )}
      </section>
      );
    }
    case "abpOcc": return (
      <section key="abpOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">{entry.isExtra ? "Occurrences in Scripture" : "ABP Occurrences"}</span></h4>
        <button className="occ-link" onClick={() => onNavigateToLexicon && onNavigateToLexicon(entry.strongs_raw, "abp")}>
          {/* Every count line renders via the shared CountLine (20-shared-components.jsx)
              — the one owner of the JP-approved format. */}
          <CountLine n={abpCount} label="in ABP"/><Icon.ArrowRight/>
        </button>
      </section>
    );
    case "extraOcc": return (
      <section key="extraOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">In the {entry.extraBookName || "text"}</span></h4>
        <div className="occ-link occ-link--static"><CountLine n={extraCount} label={"in " + (entry.extraBookName || "this text")}/></div>
      </section>
    );
    case "kjvOcc": return (
      <section key="kjvOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">KJV Occurrences</span></h4>
        <button className="occ-link" onClick={() => onNavigateToLexicon && onNavigateToLexicon(entry.strongs, "kjv")}>
          <CountLine n={kjvCount} label="in KJV"/><Icon.ArrowRight/>
        </button>
      </section>
    );
    case "bsbOcc": return (
      <section key="bsbOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">BSB Occurrences</span></h4>
        <button className="occ-link" onClick={() => onNavigateToLexicon && onNavigateToLexicon(entry.strongs, "bsb")}>
          <CountLine n={bsbCount} label="in BSB"/><Icon.ArrowRight/>
        </button>
      </section>
    );
    // R-2 flip: the one ABP count under the Greek identity (S2-Q4). Any NUMBERED
    // identity links into Word study by that Greek number — STEP-extended included
    // (G2 flip: Word study answers for G9xxx via step_lexicon + the identity
    // union, behind the same READER_GREEK_FLIPS switch, deployed together so the
    // link never lands on a 404). Lemma-only links via the PN:<form> key
    // (lane #3, 2026-07-28 — the old static-count G2 holdout is retired).
    // No trailing arrow on the link: standalone card link (JP flag at G2-R1,
    // per the standing arrow ruling — list links keep arrows, card links don't).
    case "greekIdOcc":
      // Merged compound card (JP verdict 2026-07-31, count option c): DROP the
      // occurrence line — it counts the FIRST slot's form only, and a precise-
      // looking wrong number is worse than none. (Also keeps the PN:<joined-lemma>
      // link from minting a key no page answers.) Banked end state: the pair's
      // co-occurrence count, to land with the next touch of this server code.
      if (entry.pnMergePos != null) return null;
      return (
      <section key="greekIdOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">ABP Occurrences</span></h4>
        {/* SETTLED STATE, amended by JP 2026-07-26: the COUNT is bold to match
            the unified count-line standard (`{count}× …`, bold count) — the
            rest of the 2026-07-25 ruling stands: no dot, no underline, plain
            blue link, hover-underline only. Identity emphasis stays in the
            card header (G9826 (STEP)). */}
        {greekId.greek_strongs ? (
          <button className="occ-link occ-link--id" onClick={() => onNavigateToLexicon && onNavigateToLexicon(greekId.greek_strongs, "abp")}>
            <CountLine n={greekId.greek_count} label={greekId.greek_strongs}/>
          </button>
        ) : greekId.lemma && onNavigateToLexicon ? (
          /* Lemma-only identity (Q3): Word study now opens by the stored form
             via the PN: key (lane #3, TICKET_lemma_word_study.md) — the list is
             the SAME derivation as this count, so the numbers must match. */
          <button className="occ-link occ-link--id" onClick={() => onNavigateToLexicon("PN:" + greekId.lemma, "abp")}>
            <CountLine n={greekId.greek_count} label="in ABP (this form)"/>
          </button>
        ) : (
          <div className="occ-link occ-link--static">
            <CountLine n={greekId.greek_count} label="in ABP (this form)"/>
          </div>
        )}
      </section>
    );
    // R-2 flip: the Hebrew number, demoted to a quiet cross-reference with its own
    // count — the OT-number path stays findable (Word study by the Hebrew number;
    // the link says so explicitly per receipt-0's site-5 ruling).
    case "hebCrossRef": return (
      <section key="hebCrossRef" className="sec">
        <h4 className="sec-head"><span className="sec-t">Hebrew Cross-Reference</span></h4>
        <button className="occ-link occ-link--id" onClick={() => onNavigateToLexicon && onNavigateToLexicon(greekId.hebrew_base, "abp")}>
          {/* SETTLED STATE, amended by JP 2026-07-26 — twin of the ABP line
              above: count bold per the unified count-line standard; the rest
              of the 2026-07-25 ruling stands (plain blue link, no dot, no
              underline). */}
          {greekId.hebrew_count
            ? <CountLine n={greekId.hebrew_count} label={greekId.hebrew_base}/>
            : greekId.hebrew_base}
        </button>
      </section>
    );
    case "pnOcc": return (
      <section key="pnOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">ABP Occurrences</span></h4>
        <button className="occ-link" onClick={() => onNameSearch(extractProperName(entry.pnName || entry.gloss))}>
          <CountLine n={pnCount} label="in ABP"/><Icon.ArrowRight/>
        </button>
      </section>
    );
    case "hebrewAbpOcc": return (
      <section key="hebrewAbpOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">ABP Occurrences</span></h4>
        <button className="occ-link" onClick={() => onNavigateToLexicon && onNavigateToLexicon(entry.strongs, "abp")}>
          <CountLine n={abpBaseCount} label="in ABP"/><Icon.ArrowRight/>
        </button>
      </section>
    );
    case "hebrewOtOcc": return (
      <section key="hebrewOtOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">Hebrew OT Occurrences</span></h4>
        <button className="occ-link" onClick={() => onNavigateToLexicon && onNavigateToLexicon(entry.strongs, "heb")}>
          <CountLine n={hebCount} label="in Hebrew OT"/><Icon.ArrowRight/>
        </button>
      </section>
    );
    case "hebrewKjvOcc": return (
      <section key="hebrewKjvOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">KJV Occurrences</span></h4>
        <button className="occ-link" onClick={() => onNavigateToLexicon && onNavigateToLexicon(entry.strongs, "kjv")}>
          <CountLine n={kjvCount} label="in KJV"/><Icon.ArrowRight/>
        </button>
      </section>
    );
    case "hebrewBsbOcc": return (
      <section key="hebrewBsbOcc" className="sec">
        <h4 className="sec-head"><span className="sec-t">BSB Occurrences</span></h4>
        <button className="occ-link" onClick={() => onNavigateToLexicon && onNavigateToLexicon(entry.strongs, "bsb")}>
          <CountLine n={bsbCount} label="in BSB"/><Icon.ArrowRight/>
        </button>
      </section>
    );
    case "derivation": return (
      <section key="derivation" className="sec">
        <h4 className="sec-head"><span className="sec-t">Derivation</span></h4>
        <p className="detail-p">
          {entry.derivation.split(/\b(G\d[\d.]*)/i).map((part, i) =>
            /^G\d[\d.]*/i.test(part)
              ? <button key={i} className="link-btn link-btn--strong" onClick={() => onNavigateToLexicon?.(part)}>{part}</button>
              : part
          )}
        </p>
      </section>
    );
    case "verse": return (
      <section key="verse" className="sec">
        <h4 className="sec-head">
          <span className="sec-t">Verse — {entry.ref}</span>
          <WarrantTag cls="lsj-badge"
            warrant={entry.isBsb ? "BSB — Berean Standard Bible, the translation shown."
              : useKjvText ? "KJV — King James Version, the translation shown."
              : "ABP — Apostolic Bible Polyglot, the translation shown."}>
            {entry.isBsb ? "BSB" : useKjvText ? "KJV" : "ABP"}</WarrantTag>
        </h4>
        <blockquote className="dverse">
          <span className="dverse-n">{entry.verse}</span>
          {useKjvText ? (kjvVerseText === undefined ? "Loading…" : (kjvVerseText || "—")) : (verseLoading ? "Loading…" : verseText || "—")}
        </blockquote>
        {showInterlinear && (
          <div className="interlinear">
            {!interlinearWords ? (
              <span style={{ color: "var(--ink-4)", fontSize: "13px" }}>Loading…</span>
            ) : interlinearWords.length === 0 ? (
              <span style={{ color: "var(--ink-4)", fontSize: "13px" }}>No interlinear for this verse.</span>
            ) : (() => {
              // Uniform column structure so the english rows line up: reserve the
              // translit / strongs rows (hidden when a word lacks them) whenever the
              // verse uses them. ABP brackets render INLINE on the english word
              // ("[day" … "second].") — a separate bracket column sits at the column's
              // EDGE, which drifts away from a short english word (its column is as
              // wide as the greek/translit above it) while hugging a long one; on the
              // english text itself the bracket is always tight, on the reading line.
              const hasTranslit = interlinearWords.some(w => w.translit);
              const hasStrongs = interlinearWords.some(w => w.strongs);
              return interlinearWords.map((w, i) => {
                // A bracket group = consecutive words sharing bracket_id (same rule as
                // the reading pane). KJV/Hebrew carry no bracket_id, so they get none.
                const bid = (w.bracket_id != null) ? w.bracket_id : null;
                const prev = interlinearWords[i - 1], next = interlinearWords[i + 1];
                const open = bid != null && (!prev || prev.bracket_id !== bid);
                const close = bid != null && (!next || next.bracket_id !== bid);
                // On the group's last word, lift trailing clause punctuation outside
                // the "]" (mirror the reading pane: "second.]" -> "second].", and a
                // trailing dash "to me --]" -> "to me] --").
                let eng = w.english || "—", trail = "";
                if (close) {
                  const m = (w.english || "").match(/\s*(?:--|—|–|[.,;:!?·)])+$/);
                  if (m && m.index > 0) {
                    const lifted = m[0].trim();
                    trail = /^(?:--|—|–)+$/.test(lifted) ? " " + lifted : lifted;
                    eng = (w.english || "").slice(0, m.index).trimEnd() || "—";
                  }
                }
                return (
                  <div className="iword" key={i}>
                    <span className={"iw-greek" + (w.he ? " iw-heb" : "")}>{w.top || "—"}</span>
                    {hasTranslit && <span className="iw-translit" style={w.translit ? undefined : { visibility: "hidden" }}>{w.translit || "x"}</span>}
                    <span className="iw-english">
                      {open && <span className="iw-brk">[</span>}{bid != null && w.pos != null && <span className="iw-pos">{w.pos}</span>}{eng}{close && <span className="iw-brk">]</span>}{trail}
                    </span>
                    {hasStrongs && <span className="iw-strongs" style={w.strongs ? undefined : { visibility: "hidden" }}>{w.strongs || "G0"}</span>}
                  </div>
                );
              });
            })()}
          </div>
        )}
        <div className="dverse-tools">
          <button className="link-btn" onClick={() => onReadInContext && onReadInContext(entry.book, entry.chapter, entry.verse)}>
            Read in context
          </button>
          <span className="dot">·</span>
          <button
            className={"link-btn" + (showInterlinear ? " link-btn-on" : "")}
            onClick={() => setShowInterlinear(v => !v)}
          >Interlinear</button>
        </div>
      </section>
    );
    case "frequency": return (
      <section key="frequency" className="sec">
        <h4 className="sec-head"><span className="sec-t">Frequency</span></h4>
        <div className="freq">
          <div className="freq-bar">
            <div className="freq-fill" style={{ width: barWidth + "%" }}></div>
          </div>
          <div className="freq-meta">
            <CountLine n={occurrences} label="in current results"/>
          </div>
        </div>
      </section>
    );
    default: return null;
    }
  };

  // The card is the SAME element in both homes — a bare child of the shared Sheet on mobile,
  // the desktop rail aside otherwise. Its .detail-head band + .detail-body scroll box are its
  // own (and shared with desktop, so they do NOT move); the sheet supplies only the chrome.
  const card = (
    <aside className={"detail " + (isMobile ? "detail-card" : "zinspect detail-side")} role="dialog" aria-label="Lexicon detail">
      <div className="detail-head">
        <div className="detail-head-l">
          {/* Numbering crosswalk glued to the badge as one unit (.detail-strong-wrap) — the one
              element present in every card state (Lexica/LSJ/bare), beside the badge where the
              reader's eye already is. Worded by the door they came in; the pool caveat (if any)
              stays in the LexicaBody provenance block, served side. */}
          <span className="detail-strong-wrap">
            {/* R-2 flip: a served Greek identity is the header number (C1/C2/C2a);
                lemma-only keeps the neutral PN tag — never the Hebrew number (that
                moved to the cross-ref section). STEP tag per ruling S2-Q2. */}
            <span className="detail-strong-head">{headerStrongs}</span>
            {/* JP-ruled 2026-07-25 (supersedes TICKET_step_tag_placement's body
                placement): STEP tag lives HERE beside the header number,
                hoverable explanation; the occurrence line below stays bare
                (NUMBER · COUNT×). */}
            {greekId && greekId.step && greekId.greek_strongs && (
              <span className="detail-strong-alias"
                title="Extended number from the STEP Bible project — beyond standard Strong's numbering"> (STEP)</span>
            )}
            {aliasNote && (
              <span className="detail-strong-alias">
                {aliasNote.direction === "to_abp"
                  ? `· ABP ${aliasNote.abp}`
                  : `· standard ${aliasNote.standard.join(", ")}`}
              </span>
            )}
          </span>
        </div>
        {overviewBack && !isMobile ? (
          <button className="detail-back" onClick={onClose} aria-label={"Back to " + backLabel.toLowerCase()}>‹ {backLabel}</button>
        ) : !isMobile ? (
          <button className="detail-close" onClick={onClose} aria-label="Close">
            <Icon.Close/>
          </button>
        ) : null}
      </div>

      <div className="detail-body">
        <div className={"detail-hero" + (hero.noGloss ? " no-gloss" : "")}>
          <div className="detail-hero-id">
            <div ref={heroRef}
                 className={"detail-greek" + (hero.he ? " detail-greek--he" : (!entry.greek ? " detail-greek--latin" : ""))}
                 dir={hero.he ? "rtl" : undefined}>
              {hero.script}
            </div>
            {(hero.translit || heroInlineGloss) && (
              <div className={"detail-translit-row" + (hero.he ? " detail-translit-row-he" : "")}>
                <span className="detail-translit">{hero.translit}</span>
                {heroInlineGloss && (
                  <><span className="detail-sep">·</span><span className="detail-gloss">{heroTopGloss}</span></>
                )}
              </div>
            )}
            {!hero.noGloss && !heroInlineGloss && heroTopGloss && (
              <div className="detail-gloss">{heroTopGloss}</div>
            )}
            {/* R-2 flip, ruling S2-Q3: a lemma-only identity states its status
                honestly — the printed form has no GREEK number (a Hebrew cross-ref may
                still exist below; wording per JP 2026-07-30). */}
            {greekId && !greekId.greek_strongs && (
              <div className="detail-morph">ABP-only form — no Greek Strong's number</div>
            )}
            {/* Form-vs-person scope note — see `scopeNote` above. Same slot and same
                muted style as the line above it; the two are mutually exclusive (that
                one needs NO number, this one needs a real one). */}
            {scopeNote && <div className="detail-morph detail-scopenote">{scopeNote}</div>}
          </div>
          {(heroForm || hero.morph) && (
            <div className={"detail-hero-occ" + (heroForm ? "" : " detail-hero-occ--tight")}>
              {heroForm && <span className="detail-form-label">in this verse</span>}
              {heroForm && (
                <span className={"detail-form-w" + (hero.he ? " detail-form-w--he" : "")}
                      dir={hero.he ? "rtl" : undefined}>{heroForm}</span>
              )}
              {heroForm && ((heroInflectedTranslit && heroInflectedTranslit !== hero.translit) || relocateGloss) && (
                <div className="detail-form-trrow">
                  {heroInflectedTranslit && heroInflectedTranslit !== hero.translit && (
                    <span className="detail-form-tr">{heroInflectedTranslit}</span>
                  )}
                  {heroInflectedTranslit && heroInflectedTranslit !== hero.translit && relocateGloss && (
                    <span className="detail-sep">·</span>
                  )}
                  {relocateGloss && <span className="detail-form-gloss">{hero.standaloneGloss}</span>}
                </div>
              )}
              {hero.morph && <div className="detail-morph">{hero.morph}</div>}
            </div>
          )}
        </div>

        {sections.map(renderSection)}
      </div>
    </aside>
  );
  if (!isMobile) return card;
  return <Sheet bare onClose={onClose}>{card}</Sheet>;
}
