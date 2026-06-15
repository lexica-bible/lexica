// ============================================================
// LIBRARY RENDER HELPERS — the verse renderers lifted out of LibraryView
// (60-library.jsx) to keep that file manageable. Each function takes a `ctx`
// bundle of the live values it needs from LibraryView (current book/chapter,
// the note/highlight helpers, the chip/Strong's/interlinear toggles,
// onWordClick, the highlight/press refs...). LibraryView builds `ctx` once per
// render and binds thin wrappers around these, so its call sites read unchanged.
// Pure relocation — no behavior change. Globals used here (React, Icon,
// getEnglishOrderWords, groupForGreekMode, strongsAnchorIndex, wordEntryCore,
// strongsTag) all live in earlier files (00/10/59a).
// ============================================================
const LibRender = (function () {

  const joinProse = (words) => {
    const tokens = words.map(w => w.english).filter(Boolean);
    return tokens.reduce((acc, tok, i) => {
      if (i === 0) return tok;
      return /^[.,;:?!—)]/.test(tok) ? acc + tok : acc + " " + tok;
    }, "");
  };

  const renderProseWords = (ctx, v) => {
    const { selChapter, hiClass } = ctx;
    const ch = v._ch ?? selChapter;
    const englishWords = getEnglishOrderWords(v.words);
    return englishWords.map((w, i) => {
      const text = w.english || "";
      if (!text) return null;
      const hc = hiClass(v.verse, w.position, ch);   // highlight paint for this word
      const isPunct = /^[.,;:?!—)]/.test(text);
      if (isPunct) return <span key={i} data-note-pos={w.position} className={hc || undefined}>{text}</span>;
      if (text.includes(' ')) {
        if (w.italic_words) {
          const iset = new Set(w.italic_words.split(','));
          return (
            <span key={i} data-note-pos={w.position} className={hc || undefined}>
              {text.split(' ').filter(Boolean).map((word, pi) => {
                const bare = word.replace(/[^\w]/g,'').toLowerCase();
                return <span key={pi} className={iset.has(bare) ? "lib-prose-italic" : undefined}>{word}{" "}</span>;
              })}
            </span>
          );
        }
        if (w.italic) {
          const headBare = w.english_head ? w.english_head.replace(/[^\w]/g,'').toLowerCase() : null;
          return (
            <span key={i} data-note-pos={w.position} className={hc || undefined}>
              {text.split(' ').filter(Boolean).map((word, pi) => {
                const bare = word.replace(/[^\w]/g,'').toLowerCase();
                const isItalic = !headBare || bare === headBare;
                return <span key={pi} className={isItalic ? "lib-prose-italic" : undefined}>{word}{" "}</span>;
              })}
            </span>
          );
        }
        return <span key={i} data-note-pos={w.position} className={hc || undefined}>{text + " "}</span>;
      }
      return <span key={i} data-note-pos={w.position} className={(!!w.italic ? "lib-prose-italic" : "") + hc}>{text + " "}</span>;
    });
  };

  // Hebrew OT interlinear verse — right-to-left chips (Hebrew over gloss over H-number).
  // Its own simple renderer (morphhb is one word = one chip; none of the ABP bracket /
  // italic / proper-noun machinery applies). Word-click hands a Hebrew entry (strongs
  // "H####") to the detail panel, which already routes H-numbers to the BDB sidebar.
  const renderHebVerse = (ctx, v) => {
    const { selChapter, nav, selBook, highlightRef, vnumEl, noteMarker, onWordClick, showInterlinear, showStrongs, hiClass } = ctx;
    const ch = selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    const hebEntry = (w) => ({
      id: `heb-${selBook.abbrev}-${ch}-${v.verse}-${w.pos}`,
      strongs: w.strongs,             // "H7307" -> isHebrewWord -> BDB fetch
      strongs_base: w.strongs,
      strongs_raw: (w.strongs || "").replace(/^H/, ""),
      greek: "",
      translit: w.translit || "",
      gloss: w.gloss || "",
      hebrew: w.hebrew,
      morph: w.morph || "",
      grammar: w.grammar || "",
      ref: `${selBook.abbrev} ${ch}:${v.verse}`,
      book: selBook.abbrev, chapter: ch, verse: v.verse,
      is_pn: false,
      isHeb: true,   // from the Hebrew OT reader — suppress the KJV-occurrences link
    });
    return (
      <React.Fragment key={`heb-${ch}-${v.verse}`}>
        {v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
        <div ref={isHighlight ? highlightRef : null} data-note-verse={v.verse} data-note-chapter={ch}
          className={"lib-verse-row lib-heb-row" + (isHighlight ? " lib-highlight" : "")}>
          {vnumEl(v.verse, ch)}
          <span className="lib-verse-content lib-heb-content">
            {noteMarker(v.verse, ch)}
            {(v.words || []).map(w => {
              const clickable = !!(onWordClick && w.strongs);
              return (
                <span key={w.pos} data-note-pos={w.pos}
                  className={"lib-word lib-heb-word" + (clickable ? " lib-word-clickable" : "") + hiClass(v.verse, w.pos, ch)}
                  onClick={clickable ? () => onWordClick(hebEntry(w)) : undefined}>
                  <span className="lib-iw-heb">{w.hebrew}</span>
                  {showInterlinear && w.translit && <span className="lib-iw-translit">{w.translit}</span>}
                  <span className="lib-iw-english">{w.gloss}</span>
                  {showStrongs && (w.strongs
                    ? <span className="lib-iw-strongs">{w.strongs}</span>
                    : <span className="lib-iw-strongs" style={{visibility:"hidden"}}>H0</span>)}
                </span>
              );
            })}
          </span>
        </div>
      </React.Fragment>
    );
  };

  const renderVerse = (ctx, v, skipHeading = false) => {
    const { selChapter, nav, selBook, wordMode, showInterlinear, showStrongs, onWordClick, hiClass, vnumEl, noteMarker, highlightRef } = ctx;
    const ch = v._ch ?? selChapter;   // chronological rides the chapter on the verse
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);

    const makeEntry = (w) => ({
      id: `lib-${selBook.abbrev}-${ch}-${v.verse}-${w.position}`,
      ...wordEntryCore(w, { ref: `${selBook.abbrev} ${ch}:${v.verse}`, book: selBook.abbrev, chapter: ch, verse: v.verse, gloss: w.english }),
      english_head: w.english_head || "",   // hero shows the head word for a long gloss
      morph: w.morph || "",
      pn_type: w.pn_type || null,
      pn_types: w.pn_types || null,
    });

    const chipLabel = (w) => {
      return (w.english_head && w.english?.includes(' ')) ? w.english_head : (w.english || w.english_head || "");
    };

    // Plain chip (English mode or non-bracketed word in Greek mode)
    const chip = (w, key) => {
      const isPN = !!(w.is_pn || w.strongs_base === "*");
      const clickable = !!(onWordClick && w.strongs_base && (w.strongs_base !== "*" || w.english || w.english_head) && (w.english || w.english_head));

      // Split multi-word gloss: mute italic sub-words, style smcap sub-words, chip the rest
      if (w.italic_words && w.english && w.english.includes(' ')) {
        const italicSet = new Set(w.italic_words.split(','));
        const smcapSet  = w.smcap_words ? new Set(w.smcap_words.split(',')) : new Set();
        const parts = w.english.split(' ');
        const hc = hiClass(v.verse, w.position, ch);
        return (
          <React.Fragment key={key}>
            {(() => {
              const anchorIdx = strongsAnchorIndex(parts, italicSet, w);
              return parts.map((word, pi) => {
                const bare = word.replace(/[^\w]/g, '').toLowerCase();
                if (italicSet.has(bare)) {
                  return <span key={`${key}-p${pi}`} className={"lib-word lib-abp-italic" + (smcapSet.has(bare) ? " lib-smcap" : "") + hc}>
                    {showInterlinear && <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>}
                    <span className="lib-iw-english">{word}</span>
                    {showStrongs && <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>}
                  </span>;
                }
                const isSmcap = smcapSet.has(bare);
                return (
                  <span key={`${key}-p${pi}`}
                    className={"lib-word" + (isSmcap ? " lib-smcap" : "") + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hc}
                    onClick={clickable ? () => onWordClick(isPN ? { ...makeEntry(w), isPN: true, pnName: w.english || w.english_head } : makeEntry(w)) : undefined}>
                    {showInterlinear && (pi === anchorIdx && w.lemma
                      ? <span className="lib-iw-greek">{w.lemma}</span>
                      : <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>)}
                    <span className="lib-iw-english">{word}</span>
                    {showStrongs && (pi === anchorIdx && w.strongs_base && w.strongs_base !== "*"
                      ? <span className="lib-iw-strongs">{(w.strongs && w.strongs !== '*') ? 'G' + w.strongs : w.strongs_base}</span>
                      : <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>)}
                  </span>
                );
              });
            })()}
          </React.Fragment>
        );
      }

      const rawLabel = w.english || chipLabel(w);
      if (!rawLabel) return null;
      const label = (isPN && rawLabel && !rawLabel.includes(' ')) ? rawLabel[0].toUpperCase() + rawLabel.slice(1) : rawLabel;
      const isSmcap = w.smcap_words ? new Set(w.smcap_words.split(',')).has(label.replace(/[^\w]/g, '').toLowerCase()) : false;
      return (
        <span key={key} data-note-pos={w.position}
          className={"lib-word" + (w.italic ? " lib-abp-italic" : "") + (isSmcap ? " lib-smcap" : "") + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch)}
          onClick={clickable ? () => onWordClick(isPN ? { ...makeEntry(w), isPN: true, pnName: label, gloss: label } : makeEntry(w)) : undefined}>
          {showInterlinear && (w.lemma ? <span className="lib-iw-greek">{w.lemma}</span> : <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>)}
          <span className="lib-iw-english">{label}</span>
          {showStrongs && (
            w.strongs_base && w.strongs_base !== "*"
              ? <span className="lib-iw-strongs">{(w.strongs && w.strongs !== '*') ? 'G' + w.strongs : w.strongs_base}</span>
              : <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>
          )}
        </span>
      );
    };

    // Bracket chip (bracketed word in Greek mode — shows inline position number)
    const bracketChip = (w, key) => {
      const isPN = !!(w.is_pn || w.strongs_base === "*");
      const clickable = !!(onWordClick && w.strongs_base && (w.strongs_base !== "*" || w.english));

      // Split multi-word gloss within a bracket word
      if (w.italic_words && w.english && w.english.includes(' ')) {
        const italicSet = new Set(w.italic_words.split(','));
        const smcapSet  = w.smcap_words ? new Set(w.smcap_words.split(',')) : new Set();
        const parts = w.english.split(' ');
        const anchorIdx = strongsAnchorIndex(parts, italicSet, w);
        const hc = hiClass(v.verse, w.position, ch);
        return (
          <React.Fragment key={key}>
            {parts.map((word, pi) => {
              const bare = word.replace(/[^\w]/g, '').toLowerCase();
              if (italicSet.has(bare)) {
                return <span key={`${key}-p${pi}`} className={"lib-word lib-word-bracketed lib-abp-italic" + (smcapSet.has(bare) ? " lib-smcap" : "") + hc}>
                  {showInterlinear && <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>}
                  <span className="lib-iw-pos-english">
                    {pi === 0 && w.greek_pos !== null && w.greek_pos !== undefined &&
                      <span className="lib-iw-pos">{w.greek_pos}</span>}
                    <span className="lib-iw-english">{word}</span>
                  </span>
                  {showStrongs && <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>}
                </span>;
              }
              const isSmcap = smcapSet.has(bare);
              return (
                <span key={`${key}-p${pi}`}
                  className={"lib-word lib-word-bracketed" + (isSmcap ? " lib-smcap" : "") + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hc}
                  onClick={clickable ? () => onWordClick(isPN ? { ...makeEntry(w), isPN: true, pnName: w.english || w.english_head } : makeEntry(w)) : undefined}>
                  {showInterlinear && (pi === anchorIdx && w.lemma
                    ? <span className="lib-iw-greek">{w.lemma}</span>
                    : <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>)}
                  <span className="lib-iw-pos-english">
                    {pi === 0 && w.greek_pos !== null && w.greek_pos !== undefined &&
                      <span className="lib-iw-pos">{w.greek_pos}</span>}
                    <span className="lib-iw-english">{word}</span>
                  </span>
                  {showStrongs && (pi === anchorIdx && w.strongs_base && w.strongs_base !== "*"
                    ? <span className="lib-iw-strongs">{(w.strongs && w.strongs !== '*') ? 'G' + w.strongs : w.strongs_base}</span>
                    : <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>)}
                </span>
              );
            })}
          </React.Fragment>
        );
      }

      const rawLabel = w.english || chipLabel(w);
      if (!rawLabel) return null;
      const label = (isPN && rawLabel && !rawLabel.includes(' ')) ? rawLabel[0].toUpperCase() + rawLabel.slice(1) : rawLabel;
      const isSmcap = w.smcap_words ? new Set(w.smcap_words.split(',')).has(label.replace(/[^\w]/g, '').toLowerCase()) : false;
      return (
        <span key={key} data-note-pos={w.position}
          className={"lib-word lib-word-bracketed" + (w.italic ? " lib-abp-italic" : "") + (isSmcap ? " lib-smcap" : "") + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch)}
          onClick={clickable ? () => onWordClick(isPN ? { ...makeEntry(w), isPN: true, pnName: label, gloss: label } : makeEntry(w)) : undefined}>
          {showInterlinear && (w.lemma
            ? <span className="lib-iw-greek">{w.lemma}</span>
            : <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>)}
          <span className="lib-iw-pos-english">
            {w.greek_pos !== null && w.greek_pos !== undefined &&
              <span className="lib-iw-pos">{w.greek_pos}</span>}
            <span className="lib-iw-english">{label}</span>
          </span>
          {showStrongs && (
            w.strongs_base && w.strongs_base !== "*"
              ? <span className="lib-iw-strongs">{(w.strongs && w.strongs !== '*') ? 'G' + w.strongs : w.strongs_base}</span>
              : <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>
          )}
        </span>
      );
    };

    if (!wordMode) {
      return (
        <React.Fragment key={`${ch}-${v.verse}`}>
          {!skipHeading && v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
          <div ref={isHighlight ? highlightRef : null} data-note-verse={v.verse} data-note-chapter={ch}
            className={"lib-verse-row" + (isHighlight ? " lib-highlight" : "")}>
            {vnumEl(v.verse, ch)}
            <span className="lib-verse-content">
              {noteMarker(v.verse, ch)}
              {renderProseWords(ctx, v)}
            </span>
          </div>
        </React.Fragment>
      );
    }

    // Chip mode — always Greek syntactic order with bracket notation
    let content;
    {
      const sortedWords = [...v.words].filter(w => w.english || w.kjv_def || w.strongs_base === "*").sort((a, b) => a.position - b.position);
      const groups = groupForGreekMode(sortedWords);
      content = groups.map((g, gi) => {
        if (!g.isBracket) {
          return chip(g.word, `g${gi}`);
        }
        // Suppress a duplicate position number on continuation words: when a word
        // shares the greek_pos of the previous numbered member (e.g. the source
        // token "2God did" split into God + did, both pos 2), hide the second
        // number so it renders "²God did", not "²God ²did".
        let lastGp = null;
        const gw = g.words.map((w) => {
          if (w.greek_pos != null && w.greek_pos === lastGp) return { ...w, greek_pos: null };
          if (w.greek_pos != null) lastGp = w.greek_pos;
          return w;
        });
        // Lift the bracket's trailing clause punctuation OUTSIDE the "]". ABP
        // writes "...many]," (mark after the bracket), but clean_english glued it
        // onto the word ("many,") so it renders inside. fix_bracket_punct already
        // parks the mark on the bracket's LAST word, so we snip it off here and
        // re-emit it just after the "]" — "[...dominate]." not "[...dominate.]".
        const TRAIL = /[.,;:!?·]+$/;
        let bracketTrail = "";
        let gwR = gw;
        {
          const li = gw.length - 1;
          const lastEng = (gw[li] && gw[li].english) || "";
          const m = lastEng.match(TRAIL);
          if (m) {
            bracketTrail = m[0];
            gwR = gw.map((w, i) => i === li ? { ...w, english: lastEng.slice(0, m.index) } : w);
          }
        }
        // `hc` carries the highlight paint so the "[", "]" and trailing punctuation
        // pick up the same color as the word they hug — otherwise the highlight bar
        // breaks at every bracket (those glyphs sit between the painted word chips).
        const trailChar = (txt, k, hc = "") => (
          <span key={k} className={"lib-bracket-trail" + hc}>
            {showInterlinear && <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>}
            <span className="lib-iw-english">{txt}</span>
            {showStrongs && <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>}
          </span>
        );
        const bracketChar = (glyph, k, hc = "") => (
          <span key={k} className={"lib-bracket" + hc}>
            {showInterlinear && <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>}
            <span className="lib-bracket-glyph">{glyph}</span>
            {showStrongs && <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>}
          </span>
        );
        // Highlight state of the bracket's edge words drives the bracket-glyph paint.
        const hcOpen = hiClass(v.verse, gwR[0].position, ch);
        const hcClose = hiClass(v.verse, gwR[gwR.length - 1].position, ch);
        return (
          <span key={`bg${gi}`} className="lib-bracket-group">
            {gwR.length === 1 ? (
              <span className={"lib-bracket-unit" + hcOpen}>
                {bracketChar("[", "bl", hcOpen)}
                {bracketChip(gwR[0], `bg${gi}w0`)}
                {bracketChar("]", "br", hcClose)}
                {bracketTrail && trailChar(bracketTrail, "bt", hcClose)}
              </span>
            ) : (<>
              <span className={"lib-bracket-unit" + hcOpen}>
                {bracketChar("[", "bl", hcOpen)}
                {bracketChip(gwR[0], `bg${gi}w0`)}
              </span>
              {gwR.slice(1, -1).map((w, wi) => bracketChip(w, `bg${gi}w${wi + 1}`))}
              <span className={"lib-bracket-unit" + hcClose}>
                {bracketChip(gwR[gwR.length - 1], `bg${gi}w${gwR.length - 1}`)}
                {bracketChar("]", "br", hcClose)}
                {bracketTrail && trailChar(bracketTrail, "bt", hcClose)}
              </span>
            </>)}
          </span>
        );
      });
    }

    return (
      <React.Fragment key={`${ch}-${v.verse}`}>
        {!skipHeading && v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
        <div ref={isHighlight ? highlightRef : null} data-note-verse={v.verse} data-note-chapter={ch}
          className={"lib-verse-row" + (isHighlight ? " lib-highlight" : "")}>
          {vnumEl(v.verse, ch)}
          <span className="lib-verse-content lib-verse-chips">{noteMarker(v.verse, ch)}{content}</span>
        </div>
      </React.Fragment>
    );
  };

  const renderKjvVerse = (ctx, v, showVerseNum = true, skipHeading = false) => {
    const { selChapter, nav, selBook, highlightRef, vnumEl, noteMarker, onWordClick, showInterlinear, showStrongs, hiClass } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    const makeKjvEntry = (w, sid) => ({
      id: `kjv-${selBook.abbrev}-${ch}-${v.verse}-${w.word_id}`,
      strongs: sid || "",
      strongs_base: sid ? sid.slice(1) : "",
      strongs_raw: sid ? sid.slice(1) : "",
      greek: w.lemma || "",
      translit: w.xlit || "",
      gloss: w.word,
      ref: `${selBook.abbrev} ${ch}:${v.verse}`,
      book: selBook.abbrev,
      chapter: ch,
      verse: v.verse,
      definition: "", derivation: "", is_function: false,
      isKjv: true,
      isHebrew: sid ? sid.startsWith("H") : false,
    });
    return (
      <React.Fragment key={`${ch}-${v.verse}`}>
        {!skipHeading && v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
        <div ref={isHighlight ? highlightRef : null} data-note-verse={v.verse} data-note-chapter={ch}
          className={"lib-verse-row" + (isHighlight ? " lib-highlight" : "")}>
        {showVerseNum && vnumEl(v.verse, ch)}
        <span className="lib-verse-content lib-verse-chips">
          {showVerseNum && noteMarker(v.verse, ch)}
          {v.words.map((w, i) => {
            const sid = w.strongs_ids && w.strongs_ids.length ? w.strongs_ids[0] : null;
            const clickable = !!(onWordClick && sid);
            const isHebrew = sid ? sid.startsWith("H") : false;
            return (
              <span key={i}
                className={"lib-word lib-kjv-word" + (w.italic ? " lib-kjv-italic" : "") + (clickable ? " lib-word-clickable" : "") + hiClass(v.verse, null, ch)}
                onClick={clickable ? () => onWordClick(makeKjvEntry(w, sid)) : undefined}>
                {showInterlinear && (w.lemma
                  ? <span className="lib-iw-greek" dir={isHebrew ? "rtl" : undefined}
                      style={isHebrew ? {fontFamily: "var(--f-serif)"} : undefined}>
                      {w.lemma}
                    </span>
                  : <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>
                )}
                <span className="lib-iw-english">{w.word}{w.punc || ""}</span>
                {showStrongs && (sid
                  ? <span className="lib-iw-strongs">{sid}</span>
                  : <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>
                )}
              </span>
            );
          })}
        </span>
      </div>
      </React.Fragment>
    );
  };

  const renderKjvProse = (ctx, v, showVerseNum = true, skipHeading = false) => {
    const { selChapter, nav, highlightRef, vnumEl, noteMarker, hiClass } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    return (
      <React.Fragment key={`${ch}-${v.verse}`}>
        {!skipHeading && v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
        <div ref={isHighlight ? highlightRef : null} data-note-verse={v.verse} data-note-chapter={ch}
          className={"lib-verse-row" + (isHighlight ? " lib-highlight" : "")}>
          {showVerseNum && vnumEl(v.verse, ch)}
          <span className="lib-verse-content">
            {showVerseNum && noteMarker(v.verse, ch)}
            {v.words.map((w, i) => (
              <span key={i} className={(w.italic ? "lib-prose-italic" : "") + hiClass(v.verse, null, ch)}>
                {w.word}{w.punc || ""}{" "}
              </span>
            ))}
          </span>
        </div>
      </React.Fragment>
    );
  };

  // Plain-text verse-per-line (BSB/ESV/NIV) — the same one-block-per-verse layout
  // renderKjvProse gives KJV, used for poetry books so every text lines its verses
  // up the way ABP poetry does (not run together as flowing prose).
  const renderPlainVerse = (ctx, v, showVerseNum = true, skipHeading = false) => {
    const { selChapter, nav, highlightRef, vnumEl, noteMarker, hiClass } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    return (
      <React.Fragment key={`${ch}-${v.verse}`}>
        {!skipHeading && v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
        <div ref={isHighlight ? highlightRef : null} data-note-verse={v.verse} data-note-chapter={ch}
          className={"lib-verse-row" + (isHighlight ? " lib-highlight" : "")}>
          {showVerseNum && vnumEl(v.verse, ch)}
          <span className="lib-verse-content">
            {showVerseNum && noteMarker(v.verse, ch)}
            <span className={"lib-bsb-text" + hiClass(v.verse, null, ch)}>{v.verse_text}</span>
          </span>
        </div>
      </React.Fragment>
    );
  };

  // KJV / BSB / ESV read as continuous prose (paragraphs), the same flow ABP prose
  // uses — NOT one block per verse. Each verse is an inline run with a superscript
  // number; `inner` is that verse's text/words.
  const renderFlowVerse = (ctx, v, inner) => {
    const { selChapter, nav, highlightRef, handleVerseNum, vnumPressRef, vnumNoteHandlers, noteDotInline } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    return (
      <React.Fragment key={`${ch}-${v.verse}`}>
        {v.heading && <div className="pericope-heading">{v.heading}</div>}
        <span ref={isHighlight ? highlightRef : null} className="lib-flow-verse"
          data-note-verse={v.verse} data-note-chapter={ch}>
          <sup className="lib-flow-vnum"
               title={handleVerseNum ? "Click: cross-references · Right-click / long-press: add a note" : undefined}
               onClick={handleVerseNum ? () => {
                 if (vnumPressRef.current.fired) { vnumPressRef.current.fired = false; return; }
                 handleVerseNum(v.verse, ch);
               } : undefined}
               {...vnumNoteHandlers(v.verse, ch)}>
            {v.verse}
          </sup>
          {noteDotInline(v.verse, ch)}
          {inner}
        </span>
      </React.Fragment>
    );
  };
  // Plain-text verse (BSB + ESV).
  const plainFlowInner = (ctx, v) => {
    const { selChapter, hiClass } = ctx;
    const ch = v._ch ?? selChapter;
    return <span className={"lib-bsb-text" + hiClass(v.verse, null, ch)}>{v.verse_text}{" "}</span>;
  };
  // KJV word list (keeps italic-addition styling), run together as prose.
  const kjvFlowInner = (ctx, v) => {
    const { selChapter, hiClass } = ctx;
    const ch = v._ch ?? selChapter;
    return v.words.map((w, i) => (
      <span key={i} className={(w.italic ? "lib-prose-italic" : "") + hiClass(v.verse, null, ch)}>{w.word}{w.punc || ""}{" "}</span>
    ));
  };

  // Non-canonical reader (Didache, etc.). The Greek interlinear is the normal reading,
  // exactly like Bible ABP. The readable English appears ONLY in Parallel — same
  // two-column layout as Bible parallel (Greek interlinear | English). No bracket /
  // ordering machinery; chips stay in natural Greek order. Word click → word-study.
  let _didCapNext = true;   // reset per verse below; capitalize sentence-initial glosses
  const didChips = (ctx, v) => {
    const { onWordClick, corpus, selChapter, nonCanon, showInterlinear, showStrongs, hiClass } = ctx;
    _didCapNext = true;
    return v.words.map((w, i) => {
    const raw = w.english || "";
    if (!raw) return null;
    const label = _didCapNext ? raw.charAt(0).toUpperCase() + raw.slice(1) : raw;
    _didCapNext = /[.!?][")'\]]*$/.test(raw);   // next gloss starts a new sentence?
    const clickable = !!(onWordClick && w.strongs_base);
    const entry = {
      id: `extra-${corpus}-${selChapter}-${v.verse}-${w.position}`,
      strongs: w.strongs ? strongsTag(w.strongs) : "",
      strongs_base: w.strongs_base || "",
      strongs_raw: w.strongs || "",
      greek: w.lemma || w.greek || "",
      translit: w.translit || "", morph: "",
      gloss: label,
      english_head: label,   // hero shows the gloss even when it's a short phrase
      ref: `${nonCanon ? nonCanon.name : "Extra"} ${selChapter}:${v.verse}`,
      book: corpus, chapter: selChapter, verse: v.verse,
      definition: "", derivation: "", is_function: false,
      is_pn: false, pn_type: null, pn_types: null,
      isExtra: true, extraBook: corpus, extraBookName: nonCanon ? nonCanon.name : "",
    };
    return (
      <span key={`d${i}`}
        className={"lib-word" + (clickable ? " lib-word-clickable" : "") + hiClass(v.verse, null)}
        onClick={clickable ? () => onWordClick(entry) : undefined}>
        {showInterlinear && (w.lemma
          ? <span className="lib-iw-greek">{w.lemma}</span>
          : <span className="lib-iw-greek" style={{ visibility: "hidden" }}>x</span>)}
        <span className="lib-iw-english">{label}</span>
        {showStrongs && (w.strongs
          ? <span className="lib-iw-strongs">{"G" + w.strongs}</span>
          : <span className="lib-iw-strongs" style={{ visibility: "hidden" }}>G0</span>)}
      </span>
    );
    });
  };

  // Single view: Greek interlinear only (mirrors Bible ABP).
  const renderDidacheVerse = (ctx, v) => {
    const { noteVnum, noteMarker } = ctx;
    return (
    <React.Fragment key={v.verse}>
      {v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
      <div className="lib-verse-row lib-did-row" data-note-verse={v.verse}>
        {noteVnum(v.verse)}
        <span className="lib-verse-content lib-verse-chips">{noteMarker(v.verse)}{didChips(ctx, v)}</span>
      </div>
    </React.Fragment>
    );
  };

  // Prose view: our readable English as flowing text with verse numbers.
  const renderDidacheProse = (ctx) => {
    const { didVerses, vnumPressRef, vnumNoteHandlers, noteDotInline, hiClass } = ctx;
    return (
    <div className="lib-text-words lib-prose-flow">
      {didVerses.map(v => (
        <React.Fragment key={v.verse}>
          {v.heading && <div className="pericope-heading">{v.heading}</div>}
          <span className="lib-flow-verse" data-note-verse={v.verse}>
            <sup className="lib-flow-vnum"
                 title="Right-click / long-press: add a note"
                 onClick={() => { if (vnumPressRef.current.fired) vnumPressRef.current.fired = false; }}
                 {...vnumNoteHandlers(v.verse)}>{v.verse}</sup>
            {noteDotInline(v.verse)}
            <span className={hiClass(v.verse, null) || undefined}>{(v.english || "") + " "}</span>
          </span>
        </React.Fragment>
      ))}
    </div>
    );
  };

  // Verse-per-line view for English-only "other books": each verse on its own row
  // with its number, like the Bible's verse layout — but plain reading text, no
  // clickable word chips (these texts have no Greek interlinear). Notes + highlights
  // ride the whole verse, same as the flowing-prose view.
  const renderExtraLines = (ctx) => {
    const { didVerses, noteVnum, noteMarker, hiClass } = ctx;
    return (
    <div className="lib-text-words">
      {didVerses.map(v => (
        <React.Fragment key={v.verse}>
          {v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
          <div className="lib-verse-row" data-note-verse={v.verse}>
            {noteVnum(v.verse)}
            <span className="lib-verse-content">
              {noteMarker(v.verse)}
              <span className={hiClass(v.verse, null) || undefined}>{v.english || ""}</span>
            </span>
          </div>
        </React.Fragment>
      ))}
    </div>
    );
  };

  // Parallel view: Greek interlinear | readable English (same shape as Bible parallel).
  const renderDidacheParallelVerse = (ctx, v) => {
    const { noteVnum, noteMarker, hiClass } = ctx;
    return (
    <React.Fragment key={v.verse}>
      {v.heading && <div className="lib-parallel-section-heading"><div className="pericope-heading">{v.heading}</div></div>}
      <div className="lib-parallel-verse" data-note-verse={v.verse}>
        <div className="lib-parallel-vnum">{noteVnum(v.verse)}{noteMarker(v.verse)}</div>
        <div className="lib-parallel-col"><span className="lib-verse-chips">{didChips(ctx, v)}</span></div>
        <div className="lib-parallel-col"><p className={"lib-did-eng" + hiClass(v.verse, null)}>{v.english}</p></div>
      </div>
    </React.Fragment>
    );
  };

  return {
    joinProse, renderProseWords, renderHebVerse, renderVerse,
    renderKjvVerse, renderKjvProse, renderPlainVerse, renderFlowVerse,
    plainFlowInner, kjvFlowInner, didChips, renderDidacheVerse,
    renderDidacheProse, renderExtraLines, renderDidacheParallelVerse,
  };
})();
