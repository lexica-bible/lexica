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
function DayPlanView({ chrono, curText, texts, progAll, chronoPos, onPickText, onPickPassage, onMarkComplete, onSetDay }) {
  const days = (chrono && chrono.days) || [];
  const total = days.length || 365;
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
  const todayRef = useRef(null);    // plan "Today" — target of the Jump button
  const focusRef = useRef(null);    // the day you're reading — auto-scrolled to

  // Follow the reading position: keep the day you're in open + scrolled into view as it
  // changes (switching into chrono, turning pages, or marking a day complete — all of
  // which move readingDay). Also re-centres when you switch reading text.
  useEffect(() => {
    setOpen(new Set([focusDay]));
    requestAnimationFrame(() => focusRef.current && focusRef.current.scrollIntoView({ block: "nearest" }));
  }, [curText, focusDay]);

  const toggle = (d) => setOpen(s => { const n = new Set(s); n.has(d) ? n.delete(d) : n.add(d); return n; });
  const jumpToday = () => {
    setOpen(s => new Set(s).add(curDay));
    requestAnimationFrame(() => todayRef.current && todayRef.current.scrollIntoView({ behavior: "smooth", block: "center" }));
  };
  const passagesOf = (day) => day.pos.map(q => chrono.passages[q - 1]).filter(Boolean);

  return (
    <div className="plan">
      <div className="plan-head">
        <div className="plan-sub">Each text keeps its own progress.</div>
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
        {days.map(day => {
          const state = day.day < curDay ? "done" : day.day === curDay ? "today" : "soon";
          // "Reading" highlight only when you're on a day OTHER than your plan Today, so
          // it never clashes with the gold Today bar (reading your Today keeps the gold).
          const isReading = readingDay != null && day.day === readingDay && readingDay !== curDay;
          const isOpen = open.has(day.day);
          return (
            <div key={day.day}
              ref={el => {
                if (day.day === focusDay) focusRef.current = el;
                if (day.day === curDay) todayRef.current = el;
              }}
              className={"plan-day plan-day--" + state + (isReading ? " plan-day--reading" : "") + (isOpen ? " open" : "")}>
              <button className="plan-day-head" onClick={() => toggle(day.day)} aria-expanded={isOpen}>
                <span className="plan-day-mark">
                  {state === "done" ? <Icon.Check/>
                    : state === "today" ? <span className="plan-dot" aria-hidden="true" />
                    : <span className="plan-caret" aria-hidden="true">▸</span>}
                </span>
                <span className="plan-day-n">Day {day.day}</span>
                {isReading && <span className="plan-reading-tag">Reading</span>}
                {state === "today" && <span className="plan-today-tag">Today</span>}
                <span className="plan-day-v">{day.verses}v</span>
              </button>
              {isOpen && (
                <div className="plan-day-body">
                  {passagesOf(day).map(p => (
                    <button key={p.pos} className="plan-passage" onClick={() => onPickPassage(p)}>{p.label}</button>
                  ))}
                  {state === "today" ? (
                    <button className="plan-complete" onClick={onMarkComplete}><Icon.Check/> Mark today complete</button>
                  ) : (
                    <button className="plan-setday" onClick={() => onSetDay(day.day)}>Set as today</button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
