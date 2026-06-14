// ============================================================
// READING PLAN — the "Days" view of the chronological picker.
//
// A 365-day plan is baked into chronological.json (chrono.days: each entry is a day
// with its passage positions + verse total). Progress is tracked PER READING TEXT —
// your ABP day is independent of your KJV day — and lives in the browser
// (localStorage "lexica.plan.v1"; account sync can layer on later).
//
// Reading itself reuses the existing chronological passage reader: tapping a day's
// passage jumps the reader there; "Mark today complete" advances THIS text's progress
// to the next day (and continues reading into it).
// ============================================================
const PLAN_KEY = "lexica.plan.v1";

function planLoadAll() {
  try { return JSON.parse(localStorage.getItem(PLAN_KEY) || "{}") || {}; }
  catch (e) { return {}; }
}
function planSaveAll(obj) {
  try { localStorage.setItem(PLAN_KEY, JSON.stringify(obj)); } catch (e) {}
}
// One text's progress, with sane defaults for a text never started.
function planFor(all, text) {
  const p = all && all[text];
  return { day: (p && p.day) || 1, streak: (p && p.streak) || 0, last: (p && p.last) || null };
}
function planYmd(d) {
  d = d || new Date();
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
}
function planDayDiff(a, b) {            // whole days from ymd a -> ymd b
  const pa = new Date(a + "T00:00:00"), pb = new Date(b + "T00:00:00");
  return Math.round((pb - pa) / 86400000);
}
// Mark the current day done: bump the streak if it's a fresh calendar day kept up from
// yesterday (reading several days in one sitting doesn't inflate it), then move the
// pointer to the next day, capped at the plan length.
function planAdvance(cur, totalDays) {
  const today = planYmd();
  let streak = cur.streak || 0;
  if (cur.last === today) {
    // already marked a day today — keep the streak, just move the pointer on
  } else if (cur.last && planDayDiff(cur.last, today) === 1) {
    streak += 1;
  } else {
    streak = 1;
  }
  return { day: Math.min(totalDays, (cur.day || 1) + 1), streak, last: today };
}

// The plan body — shared by the desktop left nav and the mobile picker.
function DayPlanView({ chrono, curText, texts, progAll, chronoPos, onPickText, onPickPassage, onToggleDone, isMobile }) {
  const days = (chrono && chrono.days) || [];
  const total = days.length || 365;
  // 365 days is too long to scroll as one list, so chunk it into ~12 "month" blocks
  // (≈31 days each) shown as an accordion — one month open at a time.
  const monthSize = Math.ceil(total / 12);
  const monthOf = (d) => Math.floor((d - 1) / monthSize) + 1;
  const prog = planFor(progAll, curText);
  const curDay = prog.day;
  // The day that holds the passage you're currently reading. The list FOLLOWS this —
  // opening, highlighting, and scrolling to it as you switch into chronological or turn
  // pages — separately from your plan "Today" (curDay), which still owns the streak +
  // Mark-complete button.
  const readingDay = (() => {
    if (chronoPos == null) return null;
    const d = days.find(dd => dd.pos && dd.pos.includes(chronoPos));
    return d ? d.day : null;
  })();
  const focusDay = readingDay || curDay;
  const pct = Math.round((curDay - 1) / total * 100);     // days COMPLETED / total
  const [open, setOpen] = useState(() => new Set([focusDay]));
  const [openMonth, setOpenMonth] = useState(() => monthOf(focusDay));   // which month block is expanded
  const todayRef = useRef(null);    // plan "Today" — target of the Jump button
  const focusRef = useRef(null);    // the day you're reading — auto-scrolled to

  // Follow the reading position: keep the day you're in open + scrolled into view as it
  // changes (switching into chrono, turning pages, or marking a day complete — all of
  // which move readingDay). Also re-centres when you switch reading text.
  useEffect(() => {
    setOpen(new Set([focusDay]));
    setOpenMonth(monthOf(focusDay));
    requestAnimationFrame(() => focusRef.current && focusRef.current.scrollIntoView({ block: "nearest" }));
  }, [curText, focusDay]);

  const jumpToday = () => {
    const td = days.find(d => d.day === curDay);
    if (td) selectDay(td);        // open today, move the dot there, load its first reading
    else setOpen(new Set([curDay]));
    requestAnimationFrame(() => todayRef.current && todayRef.current.scrollIntoView({ behavior: "smooth", block: "center" }));
  };
  const passagesOf = (day) => day.pos.map(q => chrono.passages[q - 1]).filter(Boolean);
  // One click on a day does the lot: open ONLY that day (accordion — the one you were
  // on closes), move the reading dot to it, and load its first reading in the pane.
  const selectDay = (day) => {
    setOpen(new Set([day.day]));
    setOpenMonth(monthOf(day.day));
    const ps = passagesOf(day);
    if (ps[0]) onPickPassage(ps[0]);
  };
  // A day tap behaves the same on desktop and mobile: collapse the day you had open,
  // open this one, and move the reading dot to it. On mobile the sheet stays open (the
  // parent passes a non-closing onPickPassage) so you can keep browsing.
  const onDayTap = (day) => selectDay(day);

  // Bin the days into month blocks (contiguous runs of the same monthOf()).
  const months = [];
  days.forEach(d => {
    const m = monthOf(d.day);
    let g = months[months.length - 1];
    if (!g || g.n !== m) { g = { n: m, days: [], first: d.day, last: d.day }; months.push(g); }
    g.days.push(d); g.last = d.day;
  });
  const toggleMonth = (n) => setOpenMonth(cur => (cur === n ? null : n));

  // One day row — rendered only when its month block is open.
  const renderDay = (day) => {
    const done = day.day < curDay;
    const isReading = readingDay != null && day.day === readingDay;
    const isOpen = open.has(day.day);
    const markClick = (e) => { e.stopPropagation(); onToggleDone(day.day); };
    const mark = isReading
      ? (done
          ? <button className="plan-day-mark plan-day-mark--done" onClick={markClick}
              aria-label={"Mark Day " + day.day + " unread"} title="Read — click to undo"><Icon.Check/></button>
          : <button className="plan-day-mark plan-day-mark--reading" onClick={markClick}
              aria-label={"Mark Day " + day.day + " read"} title="Mark as read"><span className="plan-day-dot" aria-hidden="true"></span></button>)
      : done
        ? <span className="plan-day-mark plan-day-mark--done" aria-hidden="true"><Icon.Check/></span>
        : <span className="plan-day-mark" aria-hidden="true"></span>;
    return (
      <div key={day.day}
        ref={el => {
          if (day.day === focusDay) focusRef.current = el;
          if (day.day === curDay) todayRef.current = el;
        }}
        className={"plan-day" + (done ? " plan-day--done" : "") + (isReading ? " plan-day--reading" : "") + (isOpen ? " open" : "")}>
        <div className="plan-day-head" role="button" tabIndex={0} aria-expanded={isOpen}
          onClick={() => onDayTap(day)}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onDayTap(day); } }}>
          <span className="plan-day-n">Day {day.day}</span>
          <span className="plan-day-v">{day.verses}v</span>
          {mark}
        </div>
        {isOpen && (
          <div className="plan-day-body">
            {passagesOf(day).map(p => (
              <button key={p.pos} className={"plan-passage" + (p.pos === chronoPos ? " on" : "")}
                onClick={() => onPickPassage(p)}>{p.label}</button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="plan">
      <div className="plan-head">
        <div className="plan-prog">
          <span className="plan-dayno">Day {curDay} of {total}</span>
          <span className="plan-pct">{pct}%</span>
        </div>
        <div className="plan-bar"><div className="plan-bar-fill" style={{ width: pct + "%" }} /></div>
        <div className="plan-meta">
          <span className="plan-streak">
            {prog.streak > 0
              ? <><Icon.Flame/> {prog.streak}-day streak</>
              : <>Just getting started</>}
          </span>
          <button className="plan-jump" onClick={jumpToday}>Jump to today</button>
        </div>
      </div>

      <div className="plan-days">
        <div className="plan-days-inner">
        {months.map(m => {
          const mOpen = openMonth === m.n;
          const doneInMonth = m.days.filter(d => d.day < curDay).length;
          const hasReading = readingDay != null && readingDay >= m.first && readingDay <= m.last;
          return (
            <div key={m.n} className={"plan-month" + (mOpen ? " open" : "") + (hasReading ? " plan-month--reading" : "")}>
              <button className="plan-month-head" onClick={() => toggleMonth(m.n)} aria-expanded={mOpen}>
                <span className="plan-month-name">Month {m.n}</span>
                <span className="plan-month-range">Days {m.first}–{m.last}</span>
                <span className="plan-month-done">{doneInMonth}/{m.days.length}</span>
              </button>
              {mOpen && <div className="plan-month-days">{m.days.map(renderDay)}</div>}
            </div>
          );
        })}
        </div>
      </div>
    </div>
  );
}
