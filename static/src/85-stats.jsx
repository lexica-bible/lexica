// ============================================================
// STATS — owner-only visitor dashboard (in-house, from notes.db)
// ============================================================
function StatCard({ n, label }) {
  return (
    <div className="stats-card">
      <div className="stats-card-n">{n != null ? n.toLocaleString() : "—"}</div>
      <div className="stats-card-l">{label}</div>
    </div>
  );
}

function StatsView() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let cancelled = false;
    api.stats().then(d => {
      if (cancelled) return;
      if (d) setData(d); else setErr(true);
    });
    return () => { cancelled = true; };
  }, []);

  if (err) return <div className="stats-view"><div className="stats-empty">Couldn't load stats.</div></div>;
  if (!data) return <div className="stats-view"><div className="stats-empty">Loading…</div></div>;

  const maxV = Math.max(1, ...data.by_day.map(d => d.views));
  const accounts = data.accounts || [];
  const fmtDate = s => (s ? String(s).slice(0, 10) : "—");
  return (
    <div className="stats-view">
      <h1 className="stats-title">Visitors</h1>
      <div className="stats-sub">Your own visits aren't counted. No cookies, no IPs stored.</div>

      <div className="stats-cards">
        <StatCard n={data.unique_visitors} label="Unique visitors" />
        <StatCard n={data.total_views} label="Total views" />
        <StatCard n={data.today} label="Today" />
        <StatCard n={data.last7} label="Last 7 days" />
        <StatCard n={data.last30} label="Last 30 days" />
        <StatCard n={accounts.length} label="Accounts" />
      </div>

      <div className="stats-section-title">Views — last 30 days</div>
      {data.by_day.length === 0 ? (
        <div className="stats-empty">No visits yet.</div>
      ) : (
        <div className="stats-bars">
          {data.by_day.map(d => (
            <div key={d.day} className="stats-bar-col"
                 title={`${d.day} · ${d.views} views · ${d.uniques} unique`}>
              <div className="stats-bar" style={{ height: Math.max(2, Math.round(d.views / maxV * 100)) + "%" }} />
            </div>
          ))}
        </div>
      )}

      <div className="stats-section-title">Top referrers</div>
      {data.top_ref.length === 0 ? (
        <div className="stats-empty">None yet.</div>
      ) : (
        <div className="stats-refs">
          {data.top_ref.map(r => (
            <div key={r.ref} className="stats-ref-row">
              <span className="stats-ref-name">{r.ref}</span>
              <span className="stats-ref-n">{r.n.toLocaleString()}</span>
            </div>
          ))}
        </div>
      )}

      <div className="stats-section-title">Accounts</div>
      {accounts.length === 0 ? (
        <div className="stats-empty">No accounts yet.</div>
      ) : (
        <div className="stats-refs">
          {accounts.map(a => (
            <div key={a.email} className="stats-ref-row" title={`Last sign-in: ${fmtDate(a.last_seen)}`}>
              <span className="stats-ref-name">{a.email}</span>
              <span className="stats-ref-n">{fmtDate(a.created)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
