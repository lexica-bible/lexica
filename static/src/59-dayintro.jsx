// ============================================================
// DAY INTRO PANEL — the ESV-style "Reading" card for the chronological plan.
//
// Shows for whatever chronological day you're reading: the reading number, an
// AI-written title + Berean summary, the era's dated timeline with your spot marked,
// and the day's passages. Lives in the right detail panel (desktop) / a bottom sheet
// (mobile), the same shell the chapter overview uses.
//
// Dates: each ERA carries a span + a few dated milestones (curated below; LXX dates
// for the early eras). A reading's own date is APPROXIMATE — derived from its position
// in the era's day list and shown as a clearly-marked "c." — so the marker slides
// correctly without inventing a precise year for all 365 readings.
// ============================================================

// era id -> { start, end, marks:[{label, year}] }. Year: negative = BC, positive = AD.
const ERA_TIMELINE = {
  "primeval-history":        { start: -5500, end: -2100, marks: [{ label: "Creation", year: -5500 }, { label: "The Flood", year: -3300 }, { label: "Tower of Babel", year: -3000 }] },
  "the-patriarchs":          { start: -2166, end: -1805, marks: [{ label: "Abraham's call", year: -2091 }, { label: "Isaac & Jacob", year: -2006 }, { label: "Joseph in Egypt", year: -1876 }] },
  "the-exodus-wilderness":   { start: -1446, end: -1406, marks: [{ label: "The Exodus", year: -1446 }, { label: "Law at Sinai", year: -1445 }, { label: "Wilderness", year: -1420 }] },
  "the-conquest":            { start: -1406, end: -1380, marks: [{ label: "Jordan crossed", year: -1406 }, { label: "Jericho falls", year: -1406 }, { label: "Land divided", year: -1399 }] },
  "the-judges":              { start: -1380, end: -1050, marks: [{ label: "Deborah", year: -1209 }, { label: "Gideon", year: -1162 }, { label: "Samson", year: -1075 }] },
  "the-united-kingdom":      { start: -1100, end: -970,  marks: [{ label: "Samuel's ministry", year: -1060 }, { label: "Saul anointed", year: -1050 }, { label: "David is king", year: -1010 }] },
  "the-reign-of-solomon":    { start: -970,  end: -931,  marks: [{ label: "Solomon's reign", year: -969 }, { label: "Temple built", year: -966 }, { label: "Solomon dies", year: -931 }] },
  "the-divided-kingdom":     { start: -931,  end: -609,  marks: [{ label: "Kingdom divides", year: -931 }, { label: "Israel falls", year: -722 }, { label: "Josiah's reforms", year: -622 }] },
  "judah-s-fall-the-exile":  { start: -609,  end: -538,  marks: [{ label: "Babylon rises", year: -605 }, { label: "Jerusalem falls", year: -586 }, { label: "Exiles freed", year: -538 }] },
  "the-return":              { start: -538,  end: -430,  marks: [{ label: "Cyrus's decree", year: -538 }, { label: "Temple rebuilt", year: -516 }, { label: "Ezra & Nehemiah", year: -445 }] },
  "the-gospels":             { start: -5,    end: 33,    marks: [{ label: "Jesus born", year: -5 }, { label: "Public ministry", year: 27 }, { label: "Death & rising", year: 30 }] },
  "the-early-church":        { start: 30,    end: 68,    marks: [{ label: "Pentecost", year: 30 }, { label: "Paul's missions", year: 47 }, { label: "Paul in Rome", year: 60 }] },
  "revelation":              { start: 90,    end: 96,    marks: [{ label: "John's vision", year: 95 }] },
};

// "1060 BC" / "AD 30". Years are whole; there is no year 0 in the data.
function fmtYear(y) {
  y = Math.round(y);
  return y < 0 ? (-y) + " BC" : "AD " + y;
}

// A reading's approximate date window: interpolate its slot within its era's day list
// across the era's span. Sparse eras (few days over a long span) give a wide window;
// dense ones (the monarchy) give a near-point. Returns null if the era has no timeline.
function readingWindow(day, chrono) {
  const et = day && ERA_TIMELINE[day.era];
  if (!et || !chrono || !chrono.days) return null;
  const eraDays = chrono.days.filter(d => d.era === day.era);
  const idx = Math.max(0, eraDays.findIndex(d => d.day === day.day));
  const n = eraDays.length || 1;
  const span = et.end - et.start;
  const y0 = et.start + (idx / n) * span;
  const y1 = et.start + ((idx + 1) / n) * span;
  return { et, y0, y1 };
}

// "c. 968 BC" for a point, "c. 968–948 BC" / "c. AD 30–47" for a span.
function fmtReadingDate(y0, y1) {
  const a = Math.round(y0), b = Math.round(y1);
  if (b - a < 15) return "c. " + fmtYear((a + b) / 2);
  if (a < 0 && b < 0) return "c. " + (-a) + "–" + (-b) + " BC";
  if (a >= 0 && b >= 0) return "c. AD " + a + "–" + b;
  return "c. " + fmtYear(a) + " – " + fmtYear(b);
}

// The dated strip: a thin track for the era span, a filled "you are here" bar showing
// how much time this reading covers, and the milestone dots. The bar sits ON the track,
// but the dots are drawn AFTER it with a thick paper ring, so every checkpoint is carved
// cleanly out of the bar — the bar can never swallow one. The first dot (era start) sits
// flush-left so the year list below can line its bullets up under it. Milestone labels
// live in that list (each tied to its own dot), not floating over the track.
// The first dot is at viewBox x=0; the .dintro-tl-svg CSS insets the strip by half a
// list-bullet (3.5px) and lets the end dots overflow, so that first dot's CENTRE lands
// exactly on the year-list bullet centre (both 3.5px in) at any panel width.
function TimelineStrip({ win }) {
  if (!win) return null;
  const { et, y0, y1 } = win;
  const W = 320;
  const span = et.end - et.start || 1;
  const xOf = (yr) => ((yr - et.start) / span) * W;
  const mx0 = Math.max(0, xOf(y0)), mx1 = Math.min(W, xOf(y1));
  const nowX = Math.min(mx0, mx1), nowW = Math.max(10, Math.abs(mx1 - mx0));
  return (
    <div className="dintro-tl">
      <svg viewBox={`0 0 ${W} 14`} className="dintro-tl-svg" role="img" aria-label="Era timeline">
        <rect x={0} y={5} width={W} height={4} rx={2} className="dintro-tl-track" />
        <rect x={nowX} y={3} width={nowW} height={8} rx={4} className="dintro-tl-now" />
        {et.marks.map((m, i) => (
          <circle key={i} cx={xOf(m.year)} cy={7} r={3.5} className="dintro-tl-dot" />
        ))}
      </svg>
      <div className="dintro-tl-legend">
        {et.marks.map((m, i) => (
          <div key={i} className="dintro-tl-ev">
            <span className="dintro-tl-ev-dot" aria-hidden="true"></span>
            <span className="dintro-tl-ev-yr">{fmtYear(m.year)}</span>
            <span className="dintro-tl-ev-lbl">{m.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DayIntroPanel({ day, chrono, isMobile, onClose, onPickPassage, onOverview }) {
  const dayNo = day ? day.day : null;
  const [data, setData] = useState(() => (dayNo != null && DayIntroPanel._cache[dayNo]) || null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (dayNo == null) return;
    const cached = DayIntroPanel._cache[dayNo];
    if (cached) { setData(cached); setLoading(false); return; }
    let cancelled = false;
    setLoading(true); setData(null);
    api.chronoIntro(dayNo)
      .then(d => { if (!cancelled) { DayIntroPanel._cache[dayNo] = d || {}; setData(d || {}); setLoading(false); } })
      .catch(() => { if (!cancelled) { setData({}); setLoading(false); } });
    return () => { cancelled = true; };
  }, [dayNo]);

  const { sheetRef, scrollRef } = useSwipeToDismiss(onClose);
  const era = chrono && chrono.eras && day ? chrono.eras.find(e => e.id === day.era) : null;
  const win = day ? readingWindow(day, chrono) : null;
  const passages = (day && chrono && chrono.passages)
    ? day.pos.map(q => chrono.passages[q - 1]).filter(Boolean) : [];
  const title = (data && data.title) || (era ? era.name : "Today's reading");
  const dateLine = win ? fmtReadingDate(win.y0, win.y1) : null;

  const content = (
    <>
      <div className="detail-hero dintro-hero">
        <div className="dintro-meta">Reading {dayNo}{era ? " · " + era.name : ""}</div>
        {dateLine && <div className="dintro-date">{dateLine}</div>}
      </div>
      {win && (
        <section className="sec">
          <h4 className="sec-head"><span className="sec-t">Timeline</span></h4>
          <TimelineStrip win={win} />
        </section>
      )}
      <section className="sec">
        <h4 className="sec-head">
          <span className="sec-t">About this reading</span>
          <span className="lsj-badge lsj-badge--accent">AI</span>
        </h4>
        {loading
          ? <div className="summary-loading">Writing today's intro…</div>
          : (data && data.summary)
            ? <p className="detail-p">{renderInlineMd(data.summary)}</p>
            : <div className="summary-loading">No intro available for this reading.</div>}
      </section>
      {passages.length > 0 && (
        <section className="sec">
          <h4 className="sec-head"><span className="sec-t">Today's passages</span></h4>
          <div className="dintro-passages">
            {passages.map(p => (
              <button key={p.pos} className="dintro-passage" onClick={() => onPickPassage && onPickPassage(p)}>
                <span className="dintro-passage-ref">{p.label}</span>
                <span className="dintro-passage-go" aria-hidden="true">›</span>
              </button>
            ))}
          </div>
        </section>
      )}
    </>
  );

  // Header is just the subject — the day's serif title (the contents make it
  // obvious it's a reading intro, so no panel-type label). "Reading N" + era move
  // down into the hero meta line. The "‹ Overview" toggle keeps the .detail-back slot.
  const headTitle = (
    <span className="detail-pos summary-pos dintro-era-head">{title}</span>
  );

  if (isMobile) {
    return (
      <>
        <div className="sheet-scrim" onClick={onClose} />
        <aside ref={sheetRef} className="detail detail-sheet summary-sheet dintro-sheet" role="dialog" aria-label="Reading intro">
          <div className="sheet-drag-zone" aria-hidden="true"><div className="sheet-handle"></div></div>
          <div className="detail-head">
            <div className="detail-head-l">
              {onOverview && <button className="detail-back" onClick={onOverview} aria-label="Chapter overview">‹ Overview</button>}
              {headTitle}
            </div>
            <button className="detail-close" onClick={onClose} aria-label="Close"><Icon.Close/></button>
          </div>
          <div className="detail-body" ref={scrollRef}>{content}</div>
        </aside>
      </>
    );
  }

  return (
    <aside className="detail detail-side summary-side dintro-side" role="complementary" aria-label="Reading intro">
      <div className="detail-head">
        <div className="detail-head-l">{headTitle}</div>
        {onOverview && <button className="detail-back" onClick={onOverview} aria-label="Chapter overview">‹ Overview</button>}
      </div>
      <div className="detail-body">{content}</div>
    </aside>
  );
}

DayIntroPanel._cache = {};
