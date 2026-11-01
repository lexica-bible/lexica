// ============================================================
// STATS — owner-only visitor dashboard (in-house, from notes.db)
// Everything below the range control is scoped to it. Numbers come from
// /api/stats?range=… (views_stats.py → stats_rollup.summarize).
// ============================================================
const _STATS_RANGES = [["7d", "7d"], ["30d", "30d"], ["90d", "90d"], ["all", "All"]];
const _STATS_SURFACE = {
  library: "Library", lexicon: "Word study", corpus: "Ask corpus", notes: "Notes",
  study: "Study", news: "News", about: "About",
};

const _sFmt = n => (n == null ? "—" : Number(n).toLocaleString());
const _sPct = (a, b) => (b ? Math.round((a / b) * 100) : 0);
const _sPctTxt = (a, b) => (a > 0 && b && (a / b) < 0.005 ? "<1%" : _sPct(a, b) + "%");
const _sDate = (d, withDow) => {
  if (!d) return "—";
  try {
    return new Date(d + "T00:00:00Z").toLocaleDateString("en-US",
      withDow ? { weekday: "short", month: "short", day: "numeric", timeZone: "UTC" }
              : { month: "short", day: "numeric", timeZone: "UTC" });
  } catch (e) { return d; }
};
const _sYear = d => (d ? _sDate(d) + ", " + d.slice(0, 4) : "—");
const _sCompact = n => (n >= 1e6 ? (n / 1e6).toFixed(n >= 1e7 ? 0 : 1).replace(/\.0$/, "") + "M"
  : n >= 1000 ? (n / 1000).toFixed(n >= 1e4 ? 0 : 1).replace(/\.0$/, "") + "K" : String(n));
const _sMedian = xs => {
  const s = xs.slice().sort((a, b) => a - b), n = s.length;
  return !n ? 0 : n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2;
};

// "▲ 312% vs prior 7d". prior null = no comparison (the "all" range).
function StatsDelta({ v, prior, vs }) {
  if (prior == null || v == null) return null;
  let txt;
  if (!prior) txt = v ? "▲ from 0" : "no change";
  else {
    const p = Math.round(((v - prior) / prior) * 100);
    txt = p > 0 ? `▲ ${p.toLocaleString()}%` : p < 0 ? `▼ ${Math.abs(p)}%` : "no change";
  }
  return <div className="stats-delta">{txt} vs {vs}</div>;
}

function StatCard({ n, label, delta, sub }) {
  return (
    <div className="stats-card">
      <div className="stats-card-n">{typeof n === "string" ? n : _sFmt(n)}</div>
      <div className="stats-card-l">{label}</div>
      {delta}
      {sub && <div className="stats-delta">{sub}</div>}
    </div>
  );
}

// 14-day sparkline: muted line, today's end-dot in the accent.
function StatsSpark({ values }) {
  const w = 64, h = 18, n = values.length;
  const max = Math.max(1, ...values);
  const pts = values.map((v, i) => [n > 1 ? (i / (n - 1)) * (w - 4) + 2 : w / 2, h - 2 - (v / max) * (h - 4)]);
  const last = pts[pts.length - 1];
  return (
    <svg className="stats-spark" width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
      <polyline points={pts.map(p => p.join(",")).join(" ")} fill="none" stroke="var(--ink-4)"
                strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      {last && <circle cx={last[0]} cy={last[1]} r="2.5" fill="var(--accent)" />}
    </svg>
  );
}

// Clean y ticks: 0 + about four round steps up to (or past) max.
function _sNiceTicks(max) {
  if (max <= 0) return [0, 1];
  const raw = max / 4, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) || 10 * mag;
  const out = [];
  for (let t = 0; t <= max + step * 0.999; t += step) out.push(Math.round(t * 100) / 100);
  return out;
}

// Which x positions get a date label: every day at 7d, every 5th at 30d, weekly at
// 90d, monthly beyond — counted back from today so today is always labeled — and
// never closer than ~46px apart.
function _sLabelIdx(days, slot) {
  const n = days.length;
  if (n > 120) {
    const out = [];
    let lastX = -1e9;
    days.forEach((d, i) => { if (d.endsWith("-01") && (i - lastX) * slot >= 46) { out.push(i); lastX = i; } });
    return new Set(out);
  }
  let step = n <= 7 ? 1 : n <= 31 ? 5 : 7;
  while (step * slot < 46 && step < n) step += step < 7 ? 1 : 7;
  const out = new Set();
  for (let i = n - 1; i >= 0; i -= step) out.add(i);
  return out;
}

function StatsChart({ byDay, spikes, today }) {
  const boxRef = useRef(null);
  const [w, setW] = useState(720);
  const [hover, setHover] = useState(null);
  const [scale, setScale] = useState(null);   // null = auto; "linear" | "log" once chosen
  useLayoutEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    const measure = () => setW(Math.max(280, Math.round(el.clientWidth)));
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const n = byDay.length;
  const views = byDay.map(d => d.views);
  const max = Math.max(0, ...views, ...byDay.map(d => d.uniques));
  const med = _sMedian(views);
  const autoLog = max > 20 * Math.max(med, 1);
  const isLog = scale ? scale === "log" : autoLog;

  const H = 210, mL = 40, mR = 8, mT = 18, mB = 24;
  const pw = w - mL - mR, ph = H - mT - mB;
  const slot = pw / Math.max(1, n);
  const barW = Math.max(1, Math.min(24, slot - 2));
  let ticks, top, yOf;
  if (isLog) {
    top = Math.pow(10, Math.max(1, Math.ceil(Math.log10(Math.max(1, max)))));
    ticks = [0];
    for (let t = 1; t <= top; t *= 10) ticks.push(t);
    yOf = v => mT + ph - (Math.log10(1 + v) / Math.log10(1 + top)) * ph;
  } else {
    ticks = _sNiceTicks(max);
    top = ticks[ticks.length - 1] || 1;
    yOf = v => mT + ph - (v / top) * ph;
  }
  const base = mT + ph;
  const xc = i => mL + slot * i + slot / 2;
  const yday = byDay.length > 1 ? byDay[byDay.length - 2].day : null;
  const spikeDays = new Set(spikes.map(s => s.day));
  const labels = _sLabelIdx(byDay.map(d => d.day), slot);

  const barPath = (i, v) => {
    const x = xc(i) - barW / 2, y = yOf(v), hgt = base - y;
    if (hgt <= 0) return null;
    const r = Math.min(4, barW / 2, hgt);
    return `M${x},${base}V${y + r}Q${x},${y} ${x + r},${y}H${x + barW - r}Q${x + barW},${y} ${x + barW},${y + r}V${base}Z`;
  };
  const line = byDay.map((d, i) => `${i ? "L" : "M"}${xc(i)},${yOf(d.uniques)}`).join("");
  const hv = hover != null ? byDay[hover] : null;
  const onKey = e => {
    if (e.key === "ArrowLeft") { e.preventDefault(); setHover(h => Math.max(0, (h == null ? n : h) - 1)); }
    else if (e.key === "ArrowRight") { e.preventDefault(); setHover(h => Math.min(n - 1, (h == null ? -1 : h) + 1)); }
    else if (e.key === "Escape") setHover(null);
  };

  return (
    <div className="stats-chart">
      <div className="stats-chart-head">
        <div className="stats-legend">
          <span className="stats-key"><i className="stats-key-bar" />Views</span>
          <span className="stats-key"><i className="stats-key-line" />Unique visitors</span>
          <span className="stats-key"><i className="stats-key-bar stats-key-bar--now" />Today &amp; yesterday</span>
        </div>
        <div className="seg seg--line stats-scale-seg" role="group" aria-label="Y scale">
          <button className={"seg-b" + (!isLog ? " on" : "")} onClick={() => setScale("linear")}>Linear</button>
          <button className={"seg-b" + (isLog ? " on" : "")} onClick={() => setScale("log")}>
            Log{!scale && autoLog ? " (auto)" : ""}
          </button>
        </div>
      </div>
      <div className="stats-chart-box" ref={boxRef}>
        <svg width={w} height={H} viewBox={`0 0 ${w} ${H}`} tabIndex="0" onKeyDown={onKey}
             onMouseLeave={() => setHover(null)} onBlur={() => setHover(null)}
             role="img" aria-label="Views and unique visitors per day">
          {ticks.map(t => (
            <g key={t}>
              <line x1={mL} x2={w - mR} y1={yOf(t)} y2={yOf(t)} className={t === 0 ? "stats-axis" : "stats-grid"} />
              <text x={mL - 6} y={yOf(t)} className="stats-tick" textAnchor="end" dominantBaseline="middle">{_sCompact(t)}</text>
            </g>
          ))}
          {byDay.map((d, i) => {
            const p = barPath(i, d.views);
            const now = d.day === today || d.day === yday;
            return p && <path key={d.day} d={p}
              className={"stats-bar" + (now ? " stats-bar--now" : "") + (hover === i ? " stats-bar--hover" : "")} />;
          })}
          <path d={line} className="stats-line" />
          {hv && <circle cx={xc(hover)} cy={yOf(hv.uniques)} r="4" className="stats-dot" />}
          {byDay.map((d, i) => spikeDays.has(d.day) && (
            <path key={"s" + d.day} className="stats-spike"
                  d={`M${xc(i) - 4},${mT - 12}h8l-4,6z`} />
          ))}
          {byDay.map((d, i) => labels.has(i) && (
            <text key={"x" + d.day} x={xc(i)} y={H - 6} className="stats-tick" textAnchor="middle">
              {n > 120 ? new Date(d.day + "T00:00:00Z").toLocaleDateString("en-US", { month: "short", timeZone: "UTC" }) : _sDate(d.day)}
            </text>
          ))}
          {byDay.map((d, i) => (
            <rect key={"h" + d.day} x={mL + slot * i} y={0} width={slot} height={base}
                  fill="transparent" onMouseEnter={() => setHover(i)} />
          ))}
        </svg>
        {hv && (
          <div className="stats-tip" style={{ left: Math.min(Math.max(xc(hover), 70), w - 70), top: 0 }}>
            <div className="stats-tip-d">{_sDate(hv.day, true)}</div>
            <div className="stats-tip-r"><i className="stats-key-bar" /><b>{_sFmt(hv.views)}</b> views</div>
            <div className="stats-tip-r"><i className="stats-key-line" /><b>{_sFmt(hv.uniques)}</b> unique</div>
          </div>
        )}
      </div>
      {spikes.length > 0 && (
        <div className="stats-spikes">
          {spikes.map(s => (
            <div key={s.day} className="stats-spike-line">
              <span className="stats-spike-mark" aria-hidden="true">▼</span>
              {_sDate(s.day)}: {_sFmt(s.views)} views — top referrer that day: {s.top_ref || "none recorded"}
            </div>
          ))}
        </div>
      )}
      <details className="stats-daily">
        <summary>Daily numbers</summary>
        <div className="stats-daily-rows">
          {byDay.slice().reverse().map(d => (
            <div key={d.day} className="stats-daily-row">
              <span>{_sDate(d.day, true)}</span><span>{_sFmt(d.views)}</span><span>{_sFmt(d.uniques)}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

const _sPathLabel = p => (p === "/" ? "/ (start page)" : p);

function StatsPages({ pages, total }) {
  const [open, setOpen] = useState({});      // surface -> how many paths shown (0 = closed)
  if (!pages.length) return <div className="stats-empty">No page data in this range yet.</div>;
  return (
    <div className="stats-tbl stats-tbl--pages">
      <div className="stats-tr stats-th">
        <span>Page</span><span>Views</span><span>Uniques</span><span>%</span><span>14 days</span>
      </div>
      {pages.map(g => {
        const shown = open[g.surface] || 0;
        return (
          <React.Fragment key={g.surface}>
            <button className="stats-tr stats-tr--group" aria-expanded={shown > 0}
                    onClick={() => setOpen(o => ({ ...o, [g.surface]: shown ? 0 : 15 }))}>
              <span className="stats-tname"><span className="stats-caret">{shown ? "▾" : "▸"}</span>{_STATS_SURFACE[g.surface] || g.surface}</span>
              <span>{_sFmt(g.views)}</span><span>{_sFmt(g.uniques)}</span>
              <span>{_sPctTxt(g.views, total)}</span><span><StatsSpark values={g.spark} /></span>
            </button>
            {shown > 0 && g.paths.slice(0, shown).map(p => (
              <div key={p.path} className="stats-tr stats-tr--sub">
                <span className="stats-tname refmark" title={p.path}>{_sPathLabel(p.path)}</span>
                <span>{_sFmt(p.views)}</span><span>{_sFmt(p.uniques)}</span>
                <span>{_sPctTxt(p.views, total)}</span><span><StatsSpark values={p.spark} /></span>
              </div>
            ))}
            {shown > 0 && g.paths.length > shown && (
              <button className="stats-more" onClick={() => setOpen(o => ({ ...o, [g.surface]: shown + 15 }))}>
                Show more ({g.paths.length - shown} left)
              </button>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function StatsRefTable({ rows, nonDirect, hasPrior, vs, kind }) {
  if (!rows.length) return <div className="stats-empty">None in this range.</div>;
  return (
    <div className={"stats-tbl stats-tbl--refs" + (hasPrior ? "" : " stats-tbl--noprior")}>
      <div className="stats-tr stats-th">
        <span>{kind}</span><span>Views</span><span>%</span>{hasPrior && <span>vs {vs}</span>}
      </div>
      {rows.map(r => {
        let d = null;
        if (hasPrior) {
          d = !r.prior ? "new" : (() => {
            const p = Math.round(((r.n - r.prior) / r.prior) * 100);
            return p > 0 ? `▲ ${p}%` : p < 0 ? `▼ ${Math.abs(p)}%` : "no change";
          })();
        }
        return (
          <div key={r.name} className="stats-tr" title={r.hosts.join(", ")}>
            <span className="stats-tname">{r.name}</span>
            <span>{_sFmt(r.n)}</span>
            <span>{_sPctTxt(r.n, nonDirect)}</span>
            {hasPrior && <span className="stats-tdelta" title={`${_sFmt(r.prior)} in ${vs}`}>{d}</span>}
          </div>
        );
      })}
    </div>
  );
}

function StatsAccounts({ a }) {
  const [shown, setShown] = useState({});
  const mask = e => {
    const at = e.indexOf("@");
    return at < 0 ? e.slice(0, 3) + "…" : e.slice(0, Math.min(3, at)) + "…" + e.slice(at);
  };
  return (
    <>
      <div className="stats-line">
        {_sFmt(a.total)} total · {_sFmt(a.new)} new in range · {_sFmt(a.active)} active in range
      </div>
      {a.list.length === 0 ? <div className="stats-empty">No accounts yet.</div> : (
        <div className="stats-tbl stats-tbl--accts">
          <div className="stats-tr stats-th"><span>Account</span><span>Signed up</span><span>Last seen</span></div>
          {a.list.map(x => (
            <div key={x.email} className="stats-tr">
              <button className="stats-tname stats-email" title={shown[x.email] ? "Hide" : "Click to show the full email"}
                      onClick={() => setShown(s => ({ ...s, [x.email]: !s[x.email] }))}>
                {shown[x.email] ? x.email : mask(x.email)}{x.owner ? " · you" : ""}
              </button>
              <span>{_sYear(x.created)}</span>
              <span>{x.last_seen ? _sYear(x.last_seen) : "—"}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function StatsView() {
  const [range, setRange] = useState(() => {
    try { const r = localStorage.getItem("lexica.stats.range.v1"); return _STATS_RANGES.some(x => x[0] === r) ? r : "30d"; }
    catch (e) { return "30d"; }
  });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    try { localStorage.setItem("lexica.stats.range.v1", range); } catch (e) {}
    api.stats(range).then(d => {
      if (cancelled) return;
      setLoading(false);
      if (d && d.kpi) { setData(d); setErr(false); } else setErr(true);
    });
    return () => { cancelled = true; };
  }, [range]);

  const head = (
    <>
      <h1 className="stats-title">Visitors</h1>
      <div className="stats-sub">Your own visits aren't counted. No cookies, no IPs stored. Days are UTC.</div>
      <div className="seg seg--line stats-range-seg" role="group" aria-label="Date range">
        {_STATS_RANGES.map(([k, lbl]) => (
          <button key={k} className={"seg-b" + (range === k ? " on" : "")} onClick={() => setRange(k)}>{lbl}</button>
        ))}
      </div>
    </>
  );
  if (!data) {
    return (
      <div className="stats-view">{head}
        <div className="stats-empty">{err ? "Couldn't load stats." : "Loading…"}</div>
      </div>
    );
  }

  const k = data.kpi;
  const vs = data.range === "all" ? null : `prior ${data.range}`;
  const ret = k.returning;
  const dev = data.devices;
  const devTotal = dev.mobile + dev.desktop;
  const since = d => (d && d > data.start ? `since ${_sDate(d)}` : null);
  const refs = data.refs;
  return (
    <div className={"stats-view" + (loading ? " stats-view--loading" : "")}>
      {head}
      {err && <div className="stats-empty">Couldn't refresh — showing the last numbers.</div>}

      <div className="stats-cards">
        <StatCard n={k.uniques.v} label="Unique visitors" delta={<StatsDelta {...k.uniques} vs={vs} />} />
        <StatCard n={k.views.v} label="Total views" delta={<StatsDelta {...k.views} vs={vs} />} />
        <StatCard n={k.today.v} label="Today" delta={<StatsDelta {...k.today} vs="yesterday" />} />
        <StatCard n={k.last7.v} label="Last 7 days" delta={<StatsDelta {...k.last7} vs="prior 7d" />} />
        <StatCard n={k.last30.v} label="Last 30 days" delta={<StatsDelta {...k.last30} vs="prior 30d" />} />
        <StatCard n={k.accounts.v} label="Accounts" delta={<StatsDelta {...k.accounts} vs={vs} />} />
        <StatCard n={ret.since ? ret.v : "—"} label="Returning"
                  delta={<StatsDelta v={ret.v} prior={ret.prior} vs={vs} />}
                  sub={!ret.since ? "no data yet"
                    : [`${_sPct(ret.v, ret.known)}% of visitors`, since(ret.since)].filter(Boolean).join(" · ")} />
      </div>
      <div className="stats-cards stats-cards--pair">
        <StatCard n={devTotal ? _sPct(dev.mobile, devTotal) + "%" : "—"} label="Mobile (phones + tablets)"
                  sub={devTotal ? [`${_sFmt(dev.mobile)} views`, since(dev.since)].filter(Boolean).join(" · ") : "no data yet"} />
        <StatCard n={devTotal ? _sPct(dev.desktop, devTotal) + "%" : "—"} label="Desktop"
                  sub={devTotal ? [`${_sFmt(dev.desktop)} views`, since(dev.since)].filter(Boolean).join(" · ") : "no data yet"} />
      </div>
      <div className="stats-note">
        Unique visitors are counted per day (a person back on 3 days counts 3 times). Returning = this
        browser had already visited earlier in the range.
      </div>

      <div className="stats-section-title">Views</div>
      {data.by_day.every(d => !d.views) ? <div className="stats-empty">No visits in this range.</div>
        : <StatsChart byDay={data.by_day} spikes={data.spikes} today={data.today} />}

      <div className="stats-section-title">Top pages</div>
      <div className="stats-note">
        Where each visit landed. One view = one page load; moving between tabs isn't counted.
        {since(data.pages_since) && ` Page data starts ${_sYear(data.pages_since)}; earlier visits are in the totals only.`}
      </div>
      <StatsPages pages={data.pages} total={data.pages_total} />

      <div className="stats-section-title">Referrers</div>
      <div className="stats-line">
        Direct (no referrer): <b>{_sFmt(refs.direct)}</b> · {_sPct(refs.direct, refs.views)}% of views
      </div>
      <div className="stats-subhead">Search engines</div>
      <StatsRefTable rows={refs.search} nonDirect={refs.non_direct} hasPrior={refs.has_prior} vs={vs} kind="Engine" />
      <div className="stats-subhead">Other sites</div>
      <StatsRefTable rows={refs.other} nonDirect={refs.non_direct} hasPrior={refs.has_prior} vs={vs} kind="Site" />
      <div className="stats-note">% is out of views that came from another site{refs.has_prior ? `; change is vs ${vs}` : ""}.</div>

      <div className="stats-section-title">Accounts</div>
      <StatsAccounts a={data.accounts} />
    </div>
  );
}

// ============================================================
// ADMIN — accounts & roles (admin-only; set who's a berean)
// ============================================================
function AdminView() {
  const [users, setUsers] = useState(null);
  const [err, setErr] = useState(false);
  const [busy, setBusy] = useState(null);
  const load = () => {
    api.adminUsers().then(d => { if (d && d.users) { setUsers(d.users); setErr(false); } else setErr(true); });
  };
  useEffect(() => { load(); }, []);
  const change = (u, role) => {
    if (role === u.role) return;
    setBusy(u.id);
    api.setRole(u.id, role).then(r => {
      setBusy(null);
      if (r && r.ok) setUsers(us => us.map(x => (x.id === u.id ? { ...x, role } : x)));
      else load();
    });
  };
  if (err) return <div className="stats-view"><div className="stats-empty">Couldn't load accounts.</div></div>;
  if (!users) return <div className="stats-view"><div className="stats-empty">Loading…</div></div>;
  return (
    <div className="stats-view">
      <h1 className="stats-title">Accounts &amp; roles</h1>
      <div className="stats-sub"><b>user</b> = signed in · <b>berean</b> = ESV/NIV access · <b>admin</b> = everything</div>
      {users.length === 0 ? (
        <div className="stats-empty">No accounts yet.</div>
      ) : (
        <div className="admin-users">
          {users.map(u => (
            <div key={u.id} className="admin-user-row">
              <span className="admin-user-email">{u.email}{u.owner ? " · you" : ""}</span>
              {u.owner ? (
                <span className="admin-user-locked">admin</span>
              ) : (
                <select className="admin-role-sel" value={u.role} disabled={busy === u.id}
                        onChange={e => change(u, e.target.value)}>
                  <option value="user">user</option>
                  <option value="berean">berean</option>
                  <option value="admin">admin</option>
                </select>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
