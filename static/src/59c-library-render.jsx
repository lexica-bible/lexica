// ============================================================
// LIBRARY RENDER HELPERS — the verse renderers lifted out of LibraryView
// (60-library.jsx) to keep that file manageable. Each function takes a `ctx`
// bundle of the live values it needs from LibraryView (current book/chapter,
// the note/highlight helpers, the chip/Strong's/interlinear toggles,
// onWordClick, the highlight/press refs...). LibraryView builds `ctx` once per
// render and binds thin wrappers around these, so its call sites read unchanged.
// Pure relocation — no behavior change. Globals used here (React, Icon,
// getEnglishOrderWords, groupForGreekMode, wordEntryCore,
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

  const renderProseWords = (ctx, v, opts = {}) => {
    const { selChapter, hiClass } = ctx;
    // tightSpace: emit the inter-word space OUTSIDE the word's span. The reader leaves it
    // INSIDE (default) so a multi-word highlight paints as one continuous bar; the
    // Search/Lexicon result lists set it so a single-word match highlight hugs just the
    // word — a trailing space caught inside the gold makes the highlight look off-centre.
    const tight = !!opts.tightSpace;
    const ch = v._ch ?? selChapter;
    const englishWords = getEnglishOrderWords(v.words);
    const sp = tight ? "" : " ";
    const emit = (key, span) => tight ? <React.Fragment key={key}>{span}{" "}</React.Fragment> : span;
    return englishWords.map((w, i) => {
      const text = w.english || "";
      if (!text) return null;
      const hc = hiClass(v.verse, w.position, ch);   // highlight paint for this word
      const isPunct = /^[.,;:?!—)]/.test(text);
      if (isPunct) return <span key={i} data-note-pos={w.position} className={hc || undefined}>{text}</span>;
      if (text.includes(' ')) {
        // RESULT LIST (tight) + this slot matched (hc set): the gold hugs ONLY the
        // matched head word (w.english_head) and NEVER a glued helper — whether the
        // helper is a supplied italic article ("the love"), a relocated copula
        // ("is love") or a possessive ("his love"). Italic helpers still render italic.
        // The reader (non-tight) keeps the whole-phrase bar via the branches below.
        // (Subsumes the old plain-gloss head-hug AND the italic cases that used to paint
        // the whole span gold — the leak the user spotted on an italic "the".)
        if (tight && hc) {
          const headBare = w.english_head ? w.english_head.replace(/[^\w]/g,'').toLowerCase() : null;
          const iset = w.italic_words ? new Set(w.italic_words.split(',')) : null;
          const parts = text.split(' ').filter(Boolean);
          const bares = parts.map(word => word.replace(/[^\w]/g,'').toLowerCase());
          const italicOf = (pi) => iset ? iset.has(bares[pi]) : (!!w.italic && (!headBare || bares[pi] !== headBare));
          const headFound = !!headBare && bares.some((b, pi) => b === headBare && !italicOf(pi));
          const anyGold = bares.some((b, pi) => !italicOf(pi));
          return emit(i,
            <span key={i} data-note-pos={w.position}>
              {parts.map((word, pi) => {
                const isItalic = italicOf(pi);
                // gold the head; with no locatable head, gold every non-helper word
                // (and if every word is a helper, gold all so a match never goes dark)
                const isHead = headFound ? (bares[pi] === headBare) : anyGold ? !isItalic : true;
                const inner = isItalic ? <span className="lib-prose-italic">{word}</span> : word;
                return <React.Fragment key={pi}>{isHead ? <span className={hc.trim()}>{inner}</span> : inner}{pi < parts.length - 1 ? " " : ""}</React.Fragment>;
              })}
            </span>
          );
        }
        if (w.italic_words) {
          const iset = new Set(w.italic_words.split(','));
          const parts = text.split(' ').filter(Boolean);
          return emit(i,
            <span key={i} data-note-pos={w.position} className={hc || undefined}>
              {parts.map((word, pi) => {
                const bare = word.replace(/[^\w]/g,'').toLowerCase();
                return <span key={pi} className={iset.has(bare) ? "lib-prose-italic" : undefined}>{word}{(pi < parts.length - 1 || !tight) ? " " : ""}</span>;
              })}
            </span>
          );
        }
        if (w.italic) {
          const headBare = w.english_head ? w.english_head.replace(/[^\w]/g,'').toLowerCase() : null;
          const parts = text.split(' ').filter(Boolean);
          return emit(i,
            <span key={i} data-note-pos={w.position} className={hc || undefined}>
              {parts.map((word, pi) => {
                const bare = word.replace(/[^\w]/g,'').toLowerCase();
                const isItalic = !headBare || bare === headBare;
                return <span key={pi} className={isItalic ? "lib-prose-italic" : undefined}>{word}{(pi < parts.length - 1 || !tight) ? " " : ""}</span>;
              })}
            </span>
          );
        }
        return emit(i, <span key={i} data-note-pos={w.position} className={hc || undefined}>{text + sp}</span>);
      }
      return emit(i, <span key={i} data-note-pos={w.position} className={(!!w.italic ? "lib-prose-italic" : "") + hc}>{text + sp}</span>);
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
      inflected: w.hebrew || "",            // pointed word as it appears → big side-card headword
      inflectedTranslit: w.translit || "",
      gloss: w.gloss || "",
      lemmaGloss: w.lemma_gloss || "",      // plain-meaning dictionary sense (word_gloss) beside the lemma
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
      lemmaGloss: w.kjv_def || "",          // lexicon KJV gloss → dictionary sense beside the lemma
      morph: w.morph || "",
      inflected: w.inflected || "",         // printed Greek form → side-card "in this verse" line
      inflectedTranslit: w.inflected_translit || "",   // its romanization (build_abp_translit.py)
      pn_type: w.pn_type || null,
      pn_types: w.pn_types || null,
    });

    const chipLabel = (w) => {
      return (w.english_head && w.english?.includes(' ')) ? w.english_head : (w.english || w.english_head || "");
    };

    // Render a multi-word English gloss as inline sub-spans inside ONE chip's english
    // cell: italic translator-helper words are muted, smcap words small-capped. Lets a
    // gloss like "of the second" (all one Greek word, δευτέρῳ) stay a SINGLE chip — the
    // Greek lemma + Strong's then centre over the whole phrase — instead of splitting
    // into one chip per word, where a non-italic helper ("of") became its own blank,
    // clickable box that just reopened the same word.
    const englishParts = (w) => {
      const italicSet = w.italic_words ? new Set(w.italic_words.split(',')) : new Set();
      const smcapSet  = w.smcap_words ? new Set(w.smcap_words.split(',')) : new Set();
      const parts = w.english.split(' ');
      return parts.map((word, pi) => {
        const bare = word.replace(/[^\w]/g, '').toLowerCase();
        const cls = (italicSet.has(bare) ? "lib-prose-italic" : "") + (smcapSet.has(bare) ? " lib-iw-smcap" : "");
        return <span key={pi} className={cls.trim() || undefined}>{word}{pi < parts.length - 1 ? " " : ""}</span>;
      });
    };

    // Plain chip (English mode or non-bracketed word in Greek mode)
    const chip = (w, key) => {
      const isPN = !!(w.is_pn || w.strongs_base === "*");
      const clickable = !!(onWordClick && w.strongs_base && (w.strongs_base !== "*" || w.english || w.english_head) && (w.english || w.english_head));

      // Multi-word gloss for one Greek word → ONE chip (Greek lemma + Strong's centred
      // over the whole phrase), not one chip per word. See englishParts above.
      if (w.italic_words && w.english && w.english.includes(' ')) {
        return (
          <span key={key} data-note-pos={w.position}
            className={"lib-word" + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch)}
            onClick={clickable ? () => onWordClick(isPN ? { ...makeEntry(w), isPN: true, pnName: w.english_head || w.english } : makeEntry(w)) : undefined}>
            {showInterlinear && (w.lemma ? <span className="lib-iw-greek">{w.lemma}</span> : <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>)}
            <span className="lib-iw-english">{englishParts(w)}</span>
            {showStrongs && (w.strongs_base && w.strongs_base !== "*"
              ? <span className="lib-iw-strongs">{(w.strongs && w.strongs !== '*') ? 'G' + w.strongs : w.strongs_base}</span>
              : <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>)}
          </span>
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

    // Bracket chip (bracketed word in Greek mode). The "[" / "]" marks ride INSIDE the
    // english cell of the group's first / last word (brk.open / brk.close), so they hug
    // the english text and the greek still centres over each word — the same inline
    // treatment the detail-panel interlinear uses. (A separate bracket COLUMN, still used
    // by the search/lexicon result rows that carry no greek line, drifts off a short
    // english word once a wider greek lemma sits above it.) brk.trail is the clause
    // punctuation lifted outside the "]".
    const bracketChip = (w, key, brk = {}) => {
      const isPN = !!(w.is_pn || w.strongs_base === "*");
      const clickable = !!(onWordClick && w.strongs_base && (w.strongs_base !== "*" || w.english));
      const brkOpen = (pi) => (brk.open && pi === 0) ? <span className="lib-iw-brk">[</span> : null;
      const brkClose = (pi, lastPi) => (brk.close && pi === lastPi)
        ? <React.Fragment><span className="lib-iw-brk">]</span>{brk.trail ? <span className="lib-iw-english">{brk.trail}</span> : null}</React.Fragment>
        : null;

      // Multi-word gloss within a bracket word → ONE chip (same merge as the plain
      // chip): bracket marks + position number + the whole phrase in the english cell,
      // Greek lemma + Strong's centred over it. See englishParts above.
      if (w.italic_words && w.english && w.english.includes(' ')) {
        return (
          <span key={key} data-note-pos={w.position}
            className={"lib-word lib-word-bracketed" + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch)}
            onClick={clickable ? () => onWordClick(isPN ? { ...makeEntry(w), isPN: true, pnName: w.english_head || w.english } : makeEntry(w)) : undefined}>
            {showInterlinear && (w.lemma ? <span className="lib-iw-greek">{w.lemma}</span> : <span className="lib-iw-greek" style={{visibility:"hidden"}}>x</span>)}
            <span className="lib-iw-pos-english">
              {brkOpen(0)}
              {w.greek_pos !== null && w.greek_pos !== undefined && <span className="lib-iw-pos">{w.greek_pos}</span>}
              <span className="lib-iw-english">{englishParts(w)}</span>
              {brkClose(0, 0)}
            </span>
            {showStrongs && (w.strongs_base && w.strongs_base !== "*"
              ? <span className="lib-iw-strongs">{(w.strongs && w.strongs !== '*') ? 'G' + w.strongs : w.strongs_base}</span>
              : <span className="lib-iw-strongs" style={{visibility:"hidden"}}>G0</span>)}
          </span>
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
            {brkOpen(0)}
            {w.greek_pos !== null && w.greek_pos !== undefined &&
              <span className="lib-iw-pos">{w.greek_pos}</span>}
            <span className="lib-iw-english">{label}</span>
            {brkClose(0, 0)}
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
        // English order (Phase 3): reorder the group by ABP's superscript digit
        // (greek_pos) ascending via the SHARED reorder core — the same ordering
        // prose uses — so "[²God ³was ¹the ⁴word]" reads "the word was God" with
        // the digits running 1·2·3·4. Chip keeps its OWN number-suppression + trail
        // lift below (reorder core only, no prose punctuation floating).
        const ordered = orderBracketGroupWords(g.words);
        // Suppress a duplicate position number on continuation words: when a word
        // shares the greek_pos of the previous numbered member (e.g. the source
        // token "2God did" split into God + did, both pos 2), hide the second
        // number so it renders "²God did", not "²God ²did". After the reorder,
        // equal digits are adjacent (stable sort), so this still targets the pair.
        let lastGp = null;
        const gw = ordered.map((w) => {
          if (w.greek_pos != null && w.greek_pos === lastGp) return { ...w, greek_pos: null };
          if (w.greek_pos != null) lastGp = w.greek_pos;
          return w;
        });
        // Lift the bracket's trailing clause punctuation OUTSIDE the "]". ABP
        // writes "...many]," (mark after the bracket), but clean_english glued it
        // onto the word ("many,") so it renders inside. fix_bracket_punct already
        // parks the mark on the bracket's LAST word, so we snip it off here and
        // re-emit it just after the "]" — "[...dominate]." not "[...dominate.]".
        // Also lift a trailing clause DASH (ABP's "--") outside the "]". ABP writes
        // "...to me] -- above", but clean_english glued it onto the last word's gloss
        // ("to me --") so it renders inside the bracket. Ordinary marks (",.;:") keep
        // hugging the "]"; a dash gets a leading space so it reads "] --", not "]--".
        // (2 Sam 1:26 class.) Kept as "--" to match the un-bracketed dashes elsewhere.
        const TRAIL = /\s*(?:--|—|–|[.,;:!?·])+$/;
        let bracketTrail = "";
        let gwR = gw;
        {
          const li = gw.length - 1;
          const lastEng = (gw[li] && gw[li].english) || "";
          const m = lastEng.match(TRAIL);
          if (m && m.index > 0) {                 // keep at least one real word before the mark
            const lifted = m[0].trim();
            bracketTrail = /^(?:--|—|–)+$/.test(lifted) ? " " + lifted : lifted;
            gwR = gw.map((w, i) => i === li ? { ...w, english: lastEng.slice(0, m.index).trimEnd() } : w);
          }
        }
        // The "[" / "]" ride the first / last word's english cell (see bracketChip), so
        // the chips just flow in greek order and a verse highlight paints straight
        // through — no separate bracket columns sitting between the chips to break it.
        return (
          <span key={`bg${gi}`} className="lib-bracket-group">
            {gwR.map((w, wi) => bracketChip(w, `bg${gi}w${wi}`, {
              open: wi === 0,
              close: wi === gwR.length - 1,
              trail: wi === gwR.length - 1 ? bracketTrail : "",
            }))}
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
      lemmaGloss: w.lemma_gloss || "",      // plain-meaning dictionary sense (word_gloss) beside the lemma
      ref: `${selBook.abbrev} ${ch}:${v.verse}`,
      book: selBook.abbrev,
      chapter: ch,
      verse: v.verse,
      definition: "", derivation: "", is_function: false,
      isKjv: true,
      isHebrew: sid ? sid.startsWith("H") : false,
      hebName: w.heb_name,                  // heb.db: Hebrew word is a name → allow metaV name lookup
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

  // BSB word chips — same shape as renderKjvVerse (standard Strong's, both H and
  // G), but the word entry is flagged isBsb so the detail panel pulls BSB's own
  // verse breakdown / quote / occurrence count.
  const renderBsbVerse = (ctx, v, showVerseNum = true, skipHeading = false) => {
    const { selChapter, nav, selBook, highlightRef, vnumEl, noteMarker, onWordClick, showInterlinear, showStrongs, hiClass } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);
    const makeBsbEntry = (w, sid) => ({
      id: `bsb-${selBook.abbrev}-${ch}-${v.verse}-${w.word_id}`,
      strongs: sid || "",
      strongs_base: sid ? sid.slice(1) : "",
      strongs_raw: sid ? sid.slice(1) : "",
      greek: w.lemma || "",
      translit: w.xlit || "",
      inflected: w.form || "",              // original word as printed (Berean tables) → big side-card headword
      inflectedTranslit: w.form_translit || "",
      gloss: w.word,
      lemmaGloss: w.lemma_gloss || "",      // plain-meaning dictionary sense (word_gloss) beside the lemma
      ref: `${selBook.abbrev} ${ch}:${v.verse}`,
      book: selBook.abbrev,
      chapter: ch,
      verse: v.verse,
      definition: "", derivation: "", is_function: false,
      isBsb: true,
      isHebrew: sid ? sid.startsWith("H") : false,
      hebName: w.heb_name,                  // heb.db: Hebrew word is a name → allow metaV name lookup
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
              <span key={i} data-note-pos={w.verse_pos}
                className={"lib-word lib-bsb-word" + (w.italic ? " lib-bsb-italic" : "") + (clickable ? " lib-word-clickable" : "") + hiClass(v.verse, w.verse_pos, ch)}
                onClick={clickable ? () => onWordClick(makeBsbEntry(w, sid)) : undefined}>
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

  // MODE THREE — faithful ABP interlinear. Greek is the MAIN reading line (source
  // order, NO English reorder), English gloss muted ABOVE, Strong's BELOW. Its own
  // renderer so chip/prose are untouched (parity). Greek line = greekLineForWord
  // (inflected -> lemma -> capitalized English name). Strong's line prints
  // strongs_base VERBATIM (H6547 stays H6547) — never synthesizes 'G'+strongs;
  // a bare '*' (numberless PN) shows no number, like chip. Empty-English article
  // tokens are KEPT (they carry a Greek line), rendered with a blank gloss slot so
  // the three lines stay column-aligned; the ~477 truly-empty '*' tokens (no Greek,
  // no English) drop out and stay invisible.
  const renderAbpInterlinear = (ctx, v, skipHeading = false) => {
    const { selChapter, nav, selBook, onWordClick, hiClass, vnumEl, noteMarker, highlightRef } = ctx;
    const ch = v._ch ?? selChapter;
    const isHighlight = nav && nav.highlight === v.verse && (nav.chapter == null || nav.chapter === ch);

    const makeEntry = (w) => ({
      id: `libil-${selBook.abbrev}-${ch}-${v.verse}-${w.position}`,
      ...wordEntryCore(w, { ref: `${selBook.abbrev} ${ch}:${v.verse}`, book: selBook.abbrev, chapter: ch, verse: v.verse, gloss: w.english }),
      english_head: w.english_head || "",
      lemmaGloss: w.kjv_def || "",
      morph: w.morph || "",
      inflected: w.inflected || "",
      inflectedTranslit: w.inflected_translit || "",
      pn_type: w.pn_type || null,
      pn_types: w.pn_types || null,
    });

    // One three-line word. brk carries the bracket "[" / "]" marks for this slot.
    const abpWord = (w, key, brk = {}) => {
      const isPN = !!(w.is_pn || w.strongs_base === "*");
      const g = greekLineForWord(w);
      // keep a token only if it can show SOMETHING (a Greek line or an English gloss);
      // the empty '*' tokens (neither) return null and stay invisible.
      if (!g.text && !(w.english || w.english_head)) return null;
      const clickable = !!(onWordClick && w.strongs_base
        && (w.strongs_base !== "*" || w.english || w.english_head)
        && (w.english || w.english_head || g.text));
      const gloss = w.english || "";
      // PN click payload built the SAME way chip mode does (shared pnClickPayload):
      // capitalized name in pnName/gloss so the detail panel's verse-bound TIPNR/metaV
      // lookup matches (a lowercase english_head misses the bind -> lexeme card).
      const pnPayload = pnClickPayload(w, g.text);
      // Strong's VERBATIM: strongs_base as stored (H#### or G####); '*' -> hidden.
      const strongsShown = w.strongs_base && w.strongs_base !== "*";
      const openBrk = brk.open ? <span className="lib-iw-brk">[</span> : null;
      const closeBrk = brk.close
        ? <React.Fragment><span className="lib-iw-brk">]</span>{brk.trail ? <span className="lib-abpil-trail">{brk.trail}</span> : null}</React.Fragment>
        : null;
      return (
        <span key={key} data-note-pos={w.position}
          className={"lib-word lib-abpil-word" + (w.italic ? " lib-abp-italic" : "") + (clickable ? " lib-word-clickable" : "") + (isPN ? " lib-word-pn" : "") + hiClass(v.verse, w.position, ch)}
          onClick={clickable ? () => onWordClick(pnPayload ? { ...makeEntry(w), ...pnPayload } : makeEntry(w)) : undefined}>
          <span className="lib-abpil-gloss">{gloss || " "}</span>
          <span className="lib-abpil-greek" dir={g.kind === "name" ? undefined : "ltr"}>
            {openBrk}{g.text || " "}{closeBrk}
          </span>
          {strongsShown
            ? <span className="lib-abpil-strongs">{w.strongs_base}</span>
            : <span className="lib-abpil-strongs" style={{ visibility: "hidden" }}>G0</span>}
        </span>
      );
    };

    const sortedWords = [...v.words].sort((a, b) => a.position - b.position);
    const groups = groupForGreekMode(sortedWords);   // source order, NO reorder
    const content = groups.map((g, gi) => {
      if (!g.isBracket) return abpWord(g.word, `g${gi}`);
      const gw = g.words;
      return (
        <span key={`bg${gi}`} className="lib-bracket-group">
          {gw.map((w, wi) => abpWord(w, `bg${gi}w${wi}`, { open: wi === 0, close: wi === gw.length - 1 }))}
        </span>
      );
    });

    return (
      <React.Fragment key={`${ch}-${v.verse}`}>
        {!skipHeading && v.heading && <div className="lib-verse-row pericope-row"><span className="lib-vnum" aria-hidden="true"/><div className="pericope-heading">{v.heading}</div></div>}
        <div ref={isHighlight ? highlightRef : null} data-note-verse={v.verse} data-note-chapter={ch}
          className={"lib-verse-row" + (isHighlight ? " lib-highlight" : "")}>
          {vnumEl(v.verse, ch)}
          <span className="lib-verse-content lib-verse-chips lib-verse-abpil">{noteMarker(v.verse, ch)}{content}</span>
        </div>
      </React.Fragment>
    );
  };

  return {
    joinProse, renderProseWords, renderHebVerse, renderVerse, renderAbpInterlinear,
    renderKjvVerse, renderKjvProse, renderBsbVerse, renderPlainVerse, renderFlowVerse,
    plainFlowInner, kjvFlowInner, didChips, renderDidacheVerse,
    renderDidacheProse, renderExtraLines, renderDidacheParallelVerse,
  };
})();
