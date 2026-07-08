import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

// Seeded fallback outright odds (real research, used only if live Betfair scrape is empty)
const FALLBACK_OUTRIGHT = [
  { name: 'South Africa', odds: 3.4 },
  { name: 'France', odds: 5.0 },
  { name: 'New Zealand', odds: 5.0 },
  { name: 'England', odds: 6.0 },
  { name: 'Ireland', odds: 6.0 },
];

const TABS = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'tips', label: '💡 Tips' },
  { id: 'fixtures', label: '📅 Fixtures' },
  { id: 'results', label: '🏉 Results' },
  { id: 'rwc2027', label: '🏆 World Cup 2027' },
];

const COUNTRY_FLAG = {
  'New Zealand': '🇳🇿', 'France': '🇫🇷', 'Japan': '🇯🇵', 'Italy': '🇮🇹',
  'South Africa': '🇿🇦', 'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'Australia': '🇦🇺', 'Ireland': '🇮🇪',
  'Fiji': '🇫🇯', 'Wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'Argentina': '🇦🇷', 'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
};

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
      <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14 }}>
        🏉 Nations Championship — Top 5 Winner
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
              {i === 0 ? '🏆' : `#${i + 1}`}
            </span>
            <span style={{ fontSize: 16 }}>{COUNTRY_FLAG[c.name] || ''}</span>
            <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{c.name}</span>
          </div>
          <span style={{ fontSize: 14, fontWeight: 900, color: '#34d399' }}>{fmtFrac(c.odds)}</span>
        </div>
      ))}
    </div>
  );
}

function FixtureRow({ f, result }) {
  const dateLabel = new Date(f.date).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
  const completed = !!result;
  return (
    <div style={{
      padding: '10px 14px', marginBottom: 6, borderRadius: 8,
      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>
            {COUNTRY_FLAG[f.home] || ''} {f.home}
            {completed ? <span style={{ color: '#fbbf24', fontWeight: 900 }}> {result.home_score} - {result.away_score} </span> : ' vs '}
            {f.away} {COUNTRY_FLAG[f.away] || ''}
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
            Round {f.round} · {dateLabel}
            {(result?.venue || f.venue) && <> · {result?.venue || f.venue}</>}
            {completed && <span style={{ color: '#34d399', fontWeight: 700 }}> · Winner: {result.winner}</span>}
          </div>
        </div>
        <span style={{
          fontSize: 11, fontWeight: 800, padding: '3px 10px', borderRadius: 6,
          background: completed ? 'rgba(52,211,153,0.15)' : 'rgba(96,165,250,0.15)',
          color: completed ? '#34d399' : '#60a5fa',
        }}>
          {completed ? 'FT' : 'Scheduled'}
        </span>
      </div>
      {completed && ((result.home_tries?.length > 0) || (result.away_tries?.length > 0)) && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {result.home_tries?.length > 0 && (
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)' }}>
              <span style={{ color: '#60a5fa', fontWeight: 700 }}>{f.home} tries:</span> {result.home_tries.join(', ')}
            </div>
          )}
          {result.away_tries?.length > 0 && (
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)' }}>
              <span style={{ color: '#60a5fa', fontWeight: 700 }}>{f.away} tries:</span> {result.away_tries.join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function RugbyPage() {
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
    fetch(`${API_BASE_URL}/api/sports/rugby`)
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
    return <div style={{ textAlign: 'center', padding: 60, color: 'rgba(255,255,255,0.5)' }}>🏉 Loading Nations Championship data…</div>;
  }

  const fixtures = data?.fixtures || [];
  const results = data?.results || [];
  const meta = data?.meta || {};
  const outright = (data?.outright?.length > 0) ? data.outright : FALLBACK_OUTRIGHT;
  const sixNations = data?.six_nations_2026 || {};
  const rugbyChamp = data?.rugby_championship_2025 || {};
  const tipsPredictions = data?.tips_predictions || [];
  const rwc2027 = data?.rwc_2027 || {};
  const rwcPools = rwc2027.pools || {};
  const rwcDates = rwc2027.dates || {};
  const rwcPoolPredictions = rwc2027.pool_predictions || {};
  const rwcOutright = rwc2027.outright || [];
  const rwcHistory = rwc2027.history || [];
  const rwcTitleCounts = rwc2027.title_counts || [];

  const resultsByMatch = {};
  results.forEach(r => { resultsByMatch[`${r.home}|${r.away}`] = r; });

  const today = new Date().toISOString().slice(0, 10);
  const daysToStart = meta.tournament_start
    ? Math.ceil((new Date(meta.tournament_start) - new Date(today)) / 86400000)
    : null;
  const nextFixtures = fixtures.filter(f => f.date >= today).slice(0, 6);

  return (
    <div style={{ minHeight: '100vh', background: '#0a0f1e', margin: '-12px', padding: 0 }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,rgba(16,90,16,0.25),rgba(8,50,8,0.18))', borderBottom: '1px solid rgba(52,211,153,0.25)', padding: isMobile ? '20px 16px' : '28px 32px', textAlign: 'center' }}>
        <div style={{ fontSize: isMobile ? 26 : 36, fontWeight: 900, color: 'white' }}>🏉 BetBud Nations Championship</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', marginTop: 6 }}>
          Rugby's new global competition — Six Nations vs SANZAAR · July &amp; November 2026
          {meta.is_live
            ? <span style={{ marginLeft: 8, color: '#34d399', fontWeight: 800 }}>● LIVE</span>
            : (daysToStart > 0 && <span style={{ marginLeft: 8, color: '#fbbf24', fontWeight: 800 }}>Starts in {daysToStart} days</span>)
          }
        </div>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 4 }}>
          {meta.matches_completed}/{meta.matches_total} July matches played · updated {meta.updated_at ? new Date(meta.updated_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '—'}
        </div>
      </div>

      {/* Nav */}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', padding: '16px 12px', flexWrap: 'wrap', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            background: tab === t.id ? 'linear-gradient(135deg,#059669,#047857)' : 'rgba(255,255,255,0.06)',
            border: tab === t.id ? '1px solid #10b981' : '1px solid rgba(255,255,255,0.15)',
            borderRadius: 8, color: 'white', fontSize: 13, fontWeight: 700, padding: '8px 16px', cursor: 'pointer',
          }}>{t.label}</button>
        ))}
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: isMobile ? 16 : 24 }}>
        {tab === 'dashboard' && (
          <>
            <OutrightBoard contenders={outright} />
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textAlign: 'center', margin: '12px 0 24px' }}>
              {data?.outright?.length > 0 ? 'Live Betfair Exchange odds' : 'Pre-tournament odds — live exchange odds update automatically once available'}
            </div>

            <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              {results.length > 0 ? 'Latest Results' : 'Round 1 — Super Saturday, 4 July'}
            </div>
            {(results.length > 0 ? results.slice(-6) : nextFixtures).map((item, i) => (
              <FixtureRow key={i}
                f={results.length > 0 ? fixtures.find(f => f.home === item.home && f.away === item.away) || item : item}
                result={results.length > 0 ? item : resultsByMatch[`${item.home}|${item.away}`]} />
            ))}

            {(sixNations.winner || rugbyChamp.winner) && (
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', margin: '20px 0' }}>
                {sixNations.winner && (
                  <div style={{ flex: 1, minWidth: 260, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                    <div style={{ fontSize: 11, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>{sixNations.name}</div>
                    <div style={{ fontSize: 16, fontWeight: 900, color: '#fbbf24' }}>🏆 {COUNTRY_FLAG[sixNations.winner] || ''} {sixNations.winner}</div>
                    <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)', marginTop: 6, lineHeight: 1.5 }}>{sixNations.note}</div>
                  </div>
                )}
                {rugbyChamp.winner && (
                  <div style={{ flex: 1, minWidth: 260, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                    <div style={{ fontSize: 11, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>{rugbyChamp.name}</div>
                    <div style={{ fontSize: 16, fontWeight: 900, color: '#fbbf24' }}>🏆 {COUNTRY_FLAG[rugbyChamp.winner] || ''} {rugbyChamp.winner}</div>
                    <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)', marginTop: 6, lineHeight: 1.5 }}>{rugbyChamp.note}</div>
                  </div>
                )}
              </div>
            )}

            <div style={{ fontSize: 13, fontWeight: 800, color: 'rgba(255,255,255,0.7)', textTransform: 'uppercase', letterSpacing: 1, margin: '20px 0 10px' }}>About the Competition</div>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', lineHeight: 1.7, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
              🆕 Inaugural Nations Championship — replaces the old summer tour format<br/>
              🌍 12 teams: Six Nations (England, France, Ireland, Italy, Scotland, Wales) vs SANZAAR + invitees (New Zealand, South Africa, Australia, Argentina, Fiji, Japan)<br/>
              📅 6 rounds total: 3 in July (Southern Series), 3 in November (Northern Series), plus Finals Weekend<br/>
              🏆 World champions South Africa start as favourites to lift the inaugural trophy
            </div>
          </>
        )}
        {tab === 'tips' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
              💡 BetBud Tips — Match Predictions
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 16 }}>
              Winner, margin band &amp; key try-scorer — based on outright market odds, Six Nations/Rugby Championship form and verified 2026 stats. Not betting advice.
            </div>
            {tipsPredictions.length > 0 ? tipsPredictions.map((p, i) => (
              <div key={i} style={{ background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>
                  {COUNTRY_FLAG[p.home] || ''} {p.home} vs {p.away} {COUNTRY_FLAG[p.away] || ''}
                  <span style={{ fontSize: 11, color: '#a78bfa', fontWeight: 700, marginLeft: 8 }}>Round {p.round}</span>
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>
                  {new Date(p.date).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })}
                  {p.venue && <> · {p.venue}</>}
                </div>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 6 }}>
                  <div>
                    <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>Winner</span>
                    <div style={{ fontSize: 12, color: '#34d399', fontWeight: 700 }}>{COUNTRY_FLAG[p.predicted_winner] || ''} {p.predicted_winner}</div>
                  </div>
                  {p.predicted_margin && (
                    <div>
                      <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>Margin</span>
                      <div style={{ fontSize: 12, color: '#60a5fa', fontWeight: 700 }}>{p.predicted_margin}</div>
                    </div>
                  )}
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 4 }}>{p.reason}</div>
                {p.key_try_scorer && (
                  <div style={{ fontSize: 11, color: '#fbbf24', marginTop: 6, paddingTop: 6, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                    🎯 Key try-scorer to watch: <strong>{p.key_try_scorer.player}</strong> — {p.key_try_scorer.note}
                  </div>
                )}
              </div>
            )) : (
              <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                Predictions will appear closer to kickoff.
              </div>
            )}
          </>
        )}
        {tab === 'fixtures' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              All Fixtures — July Rounds
            </div>
            {fixtures.map((f, i) => (
              <FixtureRow key={i} f={f} result={resultsByMatch[`${f.home}|${f.away}`]} />
            ))}
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textAlign: 'center', marginTop: 16 }}>
              November round (Northern Series) fixtures confirmed closer to the date.
            </div>
          </>
        )}
        {tab === 'results' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              Results ({results.length})
            </div>
            {results.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                🏉 Competition hasn't started yet — Round 1 "Super Saturday" kicks off {meta.tournament_start ? new Date(meta.tournament_start).toLocaleDateString('en-GB', { day: 'numeric', month: 'long' }) : 'soon'}.
              </div>
            ) : (
              results.slice().reverse().map((r, i) => (
                <FixtureRow key={i} f={fixtures.find(f => f.home === r.home && f.away === r.away) || r} result={r} />
              ))
            )}
          </>
        )}
        {tab === 'rwc2027' && (
          <>
            <div style={{ background: 'linear-gradient(135deg,rgba(251,191,36,0.12),rgba(217,119,6,0.08))', border: '1px solid rgba(251,191,36,0.3)', borderRadius: 12, padding: isMobile ? 14 : 18, marginBottom: 20, textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 900, color: 'white' }}>🏆 Rugby World Cup 2027</div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', marginTop: 4 }}>
                {rwcDates.host} · {rwcDates.start && new Date(rwcDates.start).toLocaleDateString('en-GB', { day: 'numeric', month: 'long' })} – {rwcDates.end && new Date(rwcDates.end).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
              </div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>Ante-post / futures betting — pools confirmed at the December 2025 draw</div>
            </div>

            {rwcOutright.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>Outright Winner — Top 5</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 10 }}>
                  {rwc2027.outright_is_live ? 'Live Betfair Exchange odds' : 'Pre-tournament odds — live exchange odds update automatically once available'}
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16, maxWidth: 420 }}>
                  {rwcOutright.map((c, i) => (
                    <div key={c.name} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '8px 10px', marginBottom: 6, borderRadius: 8,
                      background: i === 0 ? 'rgba(251,191,36,0.1)' : 'rgba(255,255,255,0.03)',
                      border: i === 0 ? '1px solid rgba(251,191,36,0.3)' : '1px solid rgba(255,255,255,0.06)',
                    }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>
                        {i === 0 ? '🏆' : `#${i + 1}`} {COUNTRY_FLAG[c.name] || ''} {c.name}
                      </span>
                      <span style={{ fontSize: 13, fontWeight: 900, color: '#34d399' }}>{fmtFrac(c.odds)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(rwcHistory.length > 0 || rwcTitleCounts.length > 0) && (
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
                {rwcTitleCounts.length > 0 && (
                  <div style={{ flex: 1, minWidth: 260, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                    <div style={{ fontSize: 12, fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Most Titles All-Time</div>
                    {rwcTitleCounts.map(t => (
                      <div key={t.team} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 0' }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{COUNTRY_FLAG[t.team] || ''} {t.team}</span>
                        <span style={{ fontSize: 12, color: '#fbbf24', fontWeight: 800 }}>{t.titles}× ({t.years.join(', ')})</span>
                      </div>
                    ))}
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                      South Africa go for an unprecedented 3rd straight title in 2027.
                    </div>
                  </div>
                )}
                {rwcHistory.length > 0 && (
                  <div style={{ flex: 1, minWidth: 260, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                    <div style={{ fontSize: 12, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Tournament History</div>
                    {rwcHistory.slice().reverse().map(h => (
                      <div key={h.year} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', color: 'rgba(255,255,255,0.7)' }}>
                        <span style={{ color: 'rgba(255,255,255,0.4)', width: 38 }}>{h.year}</span>
                        <span style={{ flex: 1, fontWeight: 700 }}>{COUNTRY_FLAG[h.winner] || ''} {h.winner}</span>
                        <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11 }}>bt {h.runner_up}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div>
              <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>Pools &amp; BetBud Group Winner Tips</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 12 }}>6 pools of 4 — top 2 plus best 4 third-place teams advance to the Round of 16</div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
                {Object.entries(rwcPools).map(([poolName, teams]) => {
                  const pred = rwcPoolPredictions[poolName] || {};
                  return (
                    <div key={poolName} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 14 }}>
                      <div style={{ fontSize: 12, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>{poolName}</div>
                      {teams.map(t => (
                        <div key={t} style={{
                          fontSize: 13, padding: '4px 0',
                          color: t === pred.predicted_winner ? '#fbbf24' : 'rgba(255,255,255,0.7)',
                          fontWeight: t === pred.predicted_winner ? 800 : 400,
                        }}>
                          {t === pred.predicted_winner ? '🏆 ' : '· '}{COUNTRY_FLAG[t] || ''} {t}
                        </div>
                      ))}
                      {pred.note && (
                        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.08)', lineHeight: 1.5 }}>
                          {pred.note}
                        </div>
                      )}
                      {pred.storyline && (
                        <div style={{ fontSize: 11, color: '#7dd3fc', marginTop: 8, lineHeight: 1.5 }}>
                          📰 {pred.storyline}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
