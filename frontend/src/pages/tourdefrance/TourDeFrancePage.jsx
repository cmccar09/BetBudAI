import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

// Seeded fallback GC winner odds (real research, used only if live Betfair scrape is empty)
const FALLBACK_OUTRIGHT = [
  { name: 'Tadej Pogačar', odds: 1.286 },
  { name: 'Jonas Vingegaard', odds: 5.5 },
  { name: 'Paul Seixas', odds: 6.5 },
  { name: 'Remco Evenepoel', odds: 15.0 },
  { name: 'Florian Lipowitz', odds: 15.0 },
];

const TABS = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'tips', label: '💡 Tips' },
  { id: 'schedule', label: '📅 Stage Schedule' },
  { id: 'results', label: '🏁 Stage Results' },
  { id: 'teams', label: '🚴 Teams' },
];

function fmtFrac(decimalOdds) {
  if (!decimalOdds || decimalOdds <= 1) return '-';
  const n = Math.round((decimalOdds - 1) * 100);
  const d = 100;
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
  const g = gcd(n, d) || 1;
  return `${n / g}/${d / g}`;
}

function OutrightBoard({ contenders }) {
  const isMobile = window.innerWidth < 640;
  return (
    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14, padding: isMobile ? 14 : 20, maxWidth: 420, margin: '0 auto' }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14 }}>
        🚴 General Classification — Top 5 Winner
      </div>
      {contenders.map((c, i) => (
        <div key={c.name} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 12px', marginBottom: 6, borderRadius: 8,
          background: i === 0 ? 'rgba(251,191,36,0.1)' : 'rgba(255,255,255,0.03)',
          border: i === 0 ? '1px solid rgba(251,191,36,0.3)' : '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: i === 0 ? '#fbbf24' : 'rgba(255,255,255,0.4)', width: 18 }}>
              {i === 0 ? '🟡' : `#${i + 1}`}
            </span>
            <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{c.name}</span>
          </div>
          <span style={{ fontSize: 14, fontWeight: 900, color: '#34d399' }}>{fmtFrac(c.odds)}</span>
        </div>
      ))}
    </div>
  );
}

const STAGE_TYPE_COLOR = {
  'Flat': '#60a5fa',
  'Hilly': '#fbbf24',
  'Mountain': '#f87171',
  'Individual Time Trial': '#a78bfa',
  'Team Time Trial': '#a78bfa',
};

function StageRow({ s, result }) {
  const color = STAGE_TYPE_COLOR[s.type] || 'rgba(255,255,255,0.5)';
  const dateLabel = new Date(s.date).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '10px 14px', marginBottom: 6, borderRadius: 8,
      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>
          Stage {s.stage}: {s.route}
        </div>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
          {dateLabel} · {s.distance_km}km
          {result && <span style={{ color: '#34d399', fontWeight: 700 }}> · Winner: {result.winner}</span>}
        </div>
      </div>
      <span style={{
        fontSize: 11, fontWeight: 800, padding: '3px 10px', borderRadius: 6,
        background: `${color}22`, color,
      }}>
        {s.type}
      </span>
    </div>
  );
}

export default function TourDeFrancePage() {
  const [tab, setTab] = useState('dashboard');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 640);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 640);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const loadData = () => {
    fetch(`${API_BASE_URL}/api/sports/tourdefrance`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 60, color: 'rgba(255,255,255,0.5)' }}>🚴 Loading Tour de France data…</div>;
  }

  const schedule = data?.schedule || [];
  const results = data?.results || [];
  const meta = data?.meta || {};
  const outright = (data?.outright?.length > 0) ? data.outright : FALLBACK_OUTRIGHT;
  const previousWinners = data?.previous_winners || [];
  const giro2026 = data?.giro_2026 || null;
  const allTimeRecord = data?.all_time_record || {};
  const teams = data?.teams || {};
  const sprinters = data?.sprinters || [];
  const ttSpecialists = data?.tt_specialists || [];
  const tipsStoryline = data?.tips_storyline || '';
  const tipsGcWatch = data?.tips_gc_watch || '';
  const stagePredictions = data?.stage_predictions || [];
  const yesterdayPerf = data?.yesterday_performance || {};

  const resultsByStage = {};
  results.forEach(r => { resultsByStage[r.stage] = r; });

  const today = new Date().toISOString().slice(0, 10);
  const daysToStart = meta.tournament_start
    ? Math.ceil((new Date(meta.tournament_start) - new Date(today)) / 86400000)
    : null;
  const latestResult = results.length ? results[results.length - 1] : null;
  const nextStage = schedule.find(s => s.date >= today);

  return (
    <div style={{ minHeight: '100vh', background: '#0a0f1e', margin: '-12px', padding: 0 }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,rgba(251,191,36,0.2),rgba(180,83,9,0.15))', borderBottom: '1px solid rgba(251,191,36,0.25)', padding: isMobile ? '20px 16px' : '28px 32px', textAlign: 'center' }}>
        <div style={{ fontSize: isMobile ? 28 : 36, fontWeight: 900, color: 'white' }}>🚴 BetBud Pro Cycling</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', marginTop: 6 }}>
          AI predictions & live stage results · {meta.tournament_start} – {meta.tournament_end}
          {meta.is_live
            ? <span style={{ marginLeft: 8, color: '#34d399', fontWeight: 800 }}>● LIVE</span>
            : (daysToStart > 0 && <span style={{ marginLeft: 8, color: '#fbbf24', fontWeight: 800 }}>Starts in {daysToStart} days</span>)
          }
        </div>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 4 }}>
          {meta.stages_completed}/{meta.stages_total} stages raced · updated {meta.updated_at ? new Date(meta.updated_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '—'}
        </div>
      </div>

      {/* Nav */}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', padding: '16px 12px', flexWrap: 'wrap', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            background: tab === t.id ? 'linear-gradient(135deg,#d97706,#b45309)' : 'rgba(255,255,255,0.06)',
            border: tab === t.id ? '1px solid #f59e0b' : '1px solid rgba(255,255,255,0.15)',
            borderRadius: 8, color: 'white', fontSize: 13, fontWeight: 700, padding: '8px 16px', cursor: 'pointer',
          }}>{t.label}</button>
        ))}
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: isMobile ? 16 : 24 }}>
        {tab === 'dashboard' && (
          <>
            <OutrightBoard contenders={outright} />
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textAlign: 'center', margin: '12px 0 24px' }}>
              {data?.outright?.length > 0 ? 'Live Betfair Exchange odds' : 'Pre-race odds — live exchange odds update automatically once available'}
            </div>

            {/* Yesterday's picks performance */}
            {yesterdayPerf.total > 0 && (
              <div style={{ background: yesterdayPerf.win_pct >= 60 ? 'rgba(52,211,153,0.08)' : 'rgba(251,191,36,0.06)', border: `1px solid ${yesterdayPerf.win_pct >= 60 ? 'rgba(52,211,153,0.3)' : 'rgba(251,191,36,0.2)'}`, borderRadius: 10, padding: '12px 16px', marginBottom: 20 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: yesterdayPerf.win_pct >= 60 ? '#34d399' : '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
                  📊 Yesterday's Stage Picks — {yesterdayPerf.date}
                </div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)' }}>
                  {yesterdayPerf.correct}/{yesterdayPerf.total} correct
                  {yesterdayPerf.win_pct !== null && <span style={{ color: yesterdayPerf.win_pct >= 60 ? '#34d399' : '#f87171', fontWeight: 700, marginLeft: 8 }}>{yesterdayPerf.win_pct}% strike rate</span>}
                </div>
                {yesterdayPerf.picks?.map((p, i) => (
                  <div key={i} style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 4 }}>
                    Stage {p.stage}: picked {p.predicted} → actual {p.actual} {p.correct ? '✅' : '❌'}
                  </div>
                ))}
              </div>
            )}

            {latestResult ? (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Latest Stage Result</div>
                <StageRow s={schedule.find(s => s.stage === latestResult.stage) || latestResult} result={latestResult} />
              </div>
            ) : null}

            {/* Stage predictions for upcoming stages */}
            {stagePredictions.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                  🚴 BetBud Stage Predictions
                </div>
                {stagePredictions.map(s => (
                  <div key={s.stage} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 12, color: '#a78bfa', fontWeight: 700 }}>Stage {s.stage} · {s.date && new Date(s.date).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })} · {s.type}</div>
                        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', marginTop: 2 }}>{s.route}</div>
                        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 4 }}>{s.reason}</div>
                      </div>
                      <div style={{ textAlign: 'right', marginLeft: 12, flexShrink: 0 }}>
                        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>BetBud Pick</div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: '#34d399' }}>{s.pick}</div>
                        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)' }}>bk: {s.backup}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!stagePredictions.length && nextStage && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Next Stage</div>
                <StageRow s={nextStage} result={null} />
              </div>
            )}

            {giro2026 && giro2026.winner && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                  🩷 Other Grand Tours in 2026 — Giro d'Italia
                </div>
                <div style={{ background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.25)', borderRadius: 10, padding: 16 }}>
                  <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginBottom: 8 }}>{giro2026.dates}</div>
                  {giro2026.podium.map(p => (
                    <div key={p.pos} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '4px 0', color: p.pos === 1 ? '#fbbf24' : 'rgba(255,255,255,0.7)', fontWeight: p.pos === 1 ? 800 : 400 }}>
                      <span>{p.pos === 1 ? '🏆' : `#${p.pos}`} {p.name}</span>
                      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>{p.note}</span>
                    </div>
                  ))}
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)', marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)', lineHeight: 1.5 }}>
                    {giro2026.note}
                  </div>
                </div>
              </div>
            )}

            {allTimeRecord.record_holders && (
              <div style={{ background: 'linear-gradient(135deg,rgba(251,191,36,0.12),rgba(217,119,6,0.08))', border: '1px solid rgba(251,191,36,0.3)', borderRadius: 10, padding: 16, marginBottom: 20 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>🏆 All-Time Wins Record</div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', marginBottom: 6 }}>
                  <strong>{allTimeRecord.record_wins}× wins</strong> — {allTimeRecord.record_holders.join(', ')}
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginBottom: 10 }}>{allTimeRecord.note}</div>
                <div style={{ fontSize: 13, color: '#fbbf24', fontWeight: 700, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                  Pogačar: {allTimeRecord.pogacar_wins}× wins ({allTimeRecord.pogacar_years?.join(', ')})
                </div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.65)', marginTop: 4 }}>{allTimeRecord.pogacar_note}</div>
              </div>
            )}

            {previousWinners.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Previous Tour de France Winners</div>
                <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                  {previousWinners.map(w => (
                    <div key={w.year} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '5px 0', color: 'rgba(255,255,255,0.75)' }}>
                      <span style={{ color: 'rgba(255,255,255,0.4)', width: 50 }}>{w.year}</span>
                      <span style={{ flex: 1, fontWeight: 700 }}>{w.winner}</span>
                      <span style={{ color: 'rgba(255,255,255,0.4)' }}>{w.country}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ fontSize: 13, fontWeight: 800, color: 'rgba(255,255,255,0.7)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Race Highlights</div>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', lineHeight: 1.7, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
              🇪🇸 Grand Départ from Barcelona, Spain — 3rd time the Tour has started in Spain<br/>
              🏔️ All 5 of France's mountain ranges featured: Pyrénées, Massif Central, Vosges, Jura, Alps<br/>
              ⛰️ Stages 19 &amp; 20 both finish atop Alpe d'Huez — first consecutive Alpe summit finishes in Tour history<br/>
              🏁 Finishes in Paris with revamped Champs-Élysées finale featuring the Montmartre cobbled climb
            </div>
          </>
        )}
        {tab === 'tips' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
              💡 BetBud Tips
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 16 }}>
              Analysis from real results — not betting advice.
            </div>
            {tipsGcWatch && (
              <div style={{ background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.25)', borderRadius: 10, padding: 14, marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#34d399', marginBottom: 4 }}>GC Watch</div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)' }}>{tipsGcWatch}</div>
              </div>
            )}
            {tipsStoryline && (
              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 18, marginBottom: 20 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Key Battle to Watch</div>
                <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.8)', lineHeight: 1.7 }}>{tipsStoryline}</div>
              </div>
            )}

            {sprinters.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>🟢 Green Jersey / Stage Winner Favourites</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 10 }}>Top sprinters for flat-stage wins</div>
                {sprinters.map(s => (
                  <div key={s.name} style={{ background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{s.name}</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 1 }}>{s.team}</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginTop: 4 }}>{s.note}</div>
                  </div>
                ))}
              </div>
            )}

            {ttSpecialists.length > 0 && (
              <div>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>⏱️ Time Trial Specialists</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 10 }}>Stage 1 (Team TT, Barcelona) &amp; Stage 16 (Individual TT, Évian–Thonon)</div>
                {ttSpecialists.map(s => (
                  <div key={s.name} style={{ background: 'rgba(167,139,250,0.06)', border: '1px solid rgba(167,139,250,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{s.name}</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 1 }}>{s.team}</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginTop: 4 }}>{s.note}</div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
        {tab === 'schedule' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              Full Route — 21 Stages
            </div>
            {schedule.map(s => <StageRow key={s.stage} s={s} result={resultsByStage[s.stage]} />)}
          </>
        )}
        {tab === 'results' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              Stage Results ({results.length})
            </div>
            {results.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                🚴 Race hasn't started yet — first stage results land {meta.tournament_start ? new Date(meta.tournament_start).toLocaleDateString('en-GB', { day: 'numeric', month: 'long' }) : 'soon'}.
              </div>
            ) : (
              results.slice().reverse().map(r => (
                <StageRow key={r.stage} s={schedule.find(s => s.stage === r.stage) || r} result={r} />
              ))
            )}
          </>
        )}
        {tab === 'teams' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
              🚴 2026 Teams — {teams.riders_total || 184} Riders, {(teams.worldteams?.length || 0) + (teams.proteams?.length || 0) || 23} Teams
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 16 }}>18 UCI WorldTeams (automatic) + 5 UCI ProTeams (wildcards)</div>

            {teams.key_teams && Object.keys(teams.key_teams).length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Teams to Watch</div>
                {Object.entries(teams.key_teams).map(([team, note]) => (
                  <div key={team} style={{ background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{team}</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', marginTop: 2 }}>{note}</div>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              {teams.worldteams?.length > 0 && (
                <div style={{ flex: 1, minWidth: 260, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>UCI WorldTeams (18)</div>
                  {teams.worldteams.map(t => (
                    <div key={t} style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)', padding: '3px 0' }}>{t}</div>
                  ))}
                </div>
              )}
              {teams.proteams?.length > 0 && (
                <div style={{ flex: 1, minWidth: 260, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>UCI ProTeams — Wildcards (5)</div>
                  {teams.proteams.map(t => (
                    <div key={t} style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)', padding: '3px 0' }}>{t}</div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
