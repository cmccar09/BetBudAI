import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

const FALLBACK_FUTURES = [
  { name: 'Philadelphia Eagles',     odds: 7.0 },
  { name: 'San Francisco 49ers',     odds: 7.5 },
  { name: 'Kansas City Chiefs',      odds: 8.0 },
  { name: 'Detroit Lions',           odds: 9.0 },
  { name: 'Baltimore Ravens',        odds: 10.0 },
  { name: 'Dallas Cowboys',          odds: 14.0 },
  { name: 'Miami Dolphins',          odds: 16.0 },
  { name: 'Buffalo Bills',           odds: 18.0 },
];

const TABS = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'superbowl', label: '🏈 Super Bowl' },
  { id: 'scores',    label: '📺 Scores' },
  { id: 'standings', label: '📋 Standings' },
  { id: 'history',   label: '🏅 History' },
];

function fmtFrac(dec) {
  if (!dec || dec <= 1) return '-';
  const n = Math.round((dec - 1) * 100);
  const d = 100;
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
  const g = gcd(n, d) || 1;
  return `${n / g}/${d / g}`;
}

function SuperBowlBoard({ futures }) {
  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14 }}>
        🏈 Super Bowl LXI Futures
      </div>
      {(futures || FALLBACK_FUTURES).map((c, i) => (
        <div key={c.name} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 14px', marginBottom: 8, borderRadius: 10,
          background: i === 0 ? 'rgba(251,191,36,0.1)' : 'rgba(255,255,255,0.04)',
          border: i === 0 ? '1px solid rgba(251,191,36,0.3)' : '1px solid rgba(255,255,255,0.08)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: i === 0 ? '#fbbf24' : 'rgba(255,255,255,0.35)', width: 24 }}>
              {i === 0 ? '🏆' : `#${i + 1}`}
            </span>
            <span style={{ fontSize: 15, fontWeight: 700, color: 'white' }}>{c.name}</span>
          </div>
          <span style={{ fontSize: 16, fontWeight: 900, color: '#34d399' }}>{fmtFrac(c.odds)}</span>
        </div>
      ))}
      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 8 }}>
        Betfair Exchange odds · updated daily
      </div>
    </div>
  );
}

function Scoreboard({ games }) {
  if (!games || games.length === 0) {
    return (
      <div style={{ padding: '32px 0', color: 'rgba(255,255,255,0.5)', textAlign: 'center' }}>
        <div style={{ fontSize: 36, marginBottom: 8 }}>🏈</div>
        <div style={{ fontSize: 15, fontWeight: 600 }}>No games today</div>
        <div style={{ fontSize: 13, marginTop: 4 }}>
          NFL pre-season begins early August · Regular season kicks off in September
        </div>
      </div>
    );
  }
  return (
    <div style={{ marginTop: 16 }}>
      {games.map((g, i) => (
        <div key={g.id || i} style={{
          background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 10, padding: '12px 16px', marginBottom: 8,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>{g.week}</span>
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>{g.status}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>{g.away?.team}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>{g.away?.record}</div>
            </div>
            <div style={{ fontSize: 20, fontWeight: 900, color: '#34d399', textAlign: 'center' }}>
              {g.away?.score} — {g.home?.score}
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>{g.home?.team}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>{g.home?.record}</div>
            </div>
          </div>
          {g.venue && <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 6 }}>📍 {g.venue}</div>}
        </div>
      ))}
    </div>
  );
}

function NFLStandings({ standings }) {
  if (!standings || standings.length === 0) {
    return <div style={{ color: 'rgba(255,255,255,0.4)', padding: '24px 0', textAlign: 'center' }}>Standings available once season begins</div>;
  }
  return (
    <div style={{ marginTop: 16 }}>
      {standings.map((conf, ci) => (
        <div key={ci} style={{ marginBottom: 28 }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
            {conf.conference}
          </div>
          {(conf.divisions || []).map((div, di) => (
            <div key={di} style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.5)', letterSpacing: 0.5, marginBottom: 6 }}>
                {div.division}
              </div>
              {(div.teams || []).map((t, i) => (
                <div key={t.team} style={{
                  display: 'flex', justifyContent: 'space-between', padding: '6px 10px',
                  background: i % 2 === 0 ? 'rgba(255,255,255,0.03)' : 'transparent',
                  borderRadius: 6, fontSize: 13,
                }}>
                  <span style={{ color: 'rgba(255,255,255,0.85)', fontWeight: 600 }}>{t.team}</span>
                  <span style={{ color: '#34d399', fontWeight: 700 }}>{t.wins}–{t.losses}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function SuperBowlHistory({ history }) {
  const records = history || [
    { year: 2025, sb: 'LIX',   winner: 'Philadelphia Eagles', defeated: 'Kansas City Chiefs', score: '40-22' },
    { year: 2024, sb: 'LVIII', winner: 'Kansas City Chiefs',  defeated: 'San Francisco 49ers', score: '25-22 OT' },
    { year: 2023, sb: 'LVII',  winner: 'Kansas City Chiefs',  defeated: 'Philadelphia Eagles', score: '38-35' },
    { year: 2022, sb: 'LVI',   winner: 'Los Angeles Rams',    defeated: 'Cincinnati Bengals',  score: '23-20' },
    { year: 2021, sb: 'LV',    winner: 'Tampa Bay Buccaneers','defeated': 'Kansas City Chiefs', score: '31-9' },
  ];
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
        Super Bowl History — Last 5 Years
      </div>
      {records.map((c, i) => (
        <div key={c.year} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '12px 16px', marginBottom: 8, borderRadius: 10,
          background: i === 0 ? 'rgba(251,191,36,0.08)' : 'rgba(255,255,255,0.04)',
          border: i === 0 ? '1px solid rgba(251,191,36,0.2)' : '1px solid rgba(255,255,255,0.07)',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 800, color: i === 0 ? '#fbbf24' : 'white' }}>
              {i === 0 ? '🏆 ' : ''}Super Bowl {c.sb} — {c.winner}
            </div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
              def. {c.defeated} {c.score}
            </div>
          </div>
          <div style={{ fontSize: 20, fontWeight: 900, color: 'rgba(255,255,255,0.18)' }}>{c.year}</div>
        </div>
      ))}
    </div>
  );
}

export default function NFLPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const isMobile = window.innerWidth < 640;

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/sports/nfl`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const futures = data?.superbowl_futures || FALLBACK_FUTURES;
  const tip = data?.tip || {};

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: 'white', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1a2e1a 0%, #0f172a 100%)',
        padding: isMobile ? '20px 16px 16px' : '28px 32px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <span style={{ fontSize: isMobile ? 28 : 36 }}>🏈</span>
            <div>
              <div style={{ fontSize: isMobile ? 20 : 26, fontWeight: 900, color: 'white', letterSpacing: -0.5 }}>
                BetBud NFL
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
                NFL · Super Bowl LXI Futures · Season Preview
              </div>
            </div>
          </div>
          {tip.championship_pick && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.3)',
              borderRadius: 8, padding: '6px 12px', marginTop: 8,
            }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1 }}>
                BetBud Pick
              </span>
              <span style={{ fontSize: 14, fontWeight: 800, color: 'white' }}>
                {tip.championship_pick} @ {fmtFrac(tip.championship_odds)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        maxWidth: 960, margin: '0 auto', padding: '0 16px',
        display: 'flex', gap: 6, overflowX: 'auto', paddingTop: 14, paddingBottom: 4,
      }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            flex: '0 0 auto', padding: '7px 14px', borderRadius: 8, cursor: 'pointer',
            fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap',
            background: activeTab === t.id ? 'linear-gradient(135deg,#059669 0%,#047857 100%)' : 'rgba(255,255,255,0.07)',
            border: activeTab === t.id ? '1.5px solid #10b981' : '1.5px solid rgba(255,255,255,0.12)',
            color: 'white', transition: 'all 0.15s',
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ maxWidth: 960, margin: '0 auto', padding: isMobile ? '12px 16px 32px' : '16px 32px 48px' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'rgba(255,255,255,0.4)' }}>
            Loading NFL data…
          </div>
        )}

        {!loading && activeTab === 'dashboard' && (
          <div>
            {tip.note && (
              <div style={{
                background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.2)',
                borderRadius: 10, padding: '12px 16px', marginBottom: 16, fontSize: 13,
                color: 'rgba(255,255,255,0.7)', lineHeight: 1.5,
              }}>
                💡 {tip.note}
              </div>
            )}
            <SuperBowlBoard futures={futures} />
            {(tip.value_picks || []).length > 0 && (
              <div style={{ marginTop: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                  Value Picks (14/1+)
                </div>
                {tip.value_picks.map(v => (
                  <div key={v.name} style={{
                    display: 'flex', justifyContent: 'space-between', padding: '10px 14px',
                    background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.15)',
                    borderRadius: 8, marginBottom: 6,
                  }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{v.name}</span>
                    <span style={{ fontSize: 14, fontWeight: 900, color: '#fbbf24' }}>{fmtFrac(v.odds)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {!loading && activeTab === 'superbowl' && <SuperBowlBoard futures={futures} />}
        {!loading && activeTab === 'scores' && <Scoreboard games={data?.games_today} />}
        {!loading && activeTab === 'standings' && <NFLStandings standings={data?.standings} />}
        {!loading && activeTab === 'history' && <SuperBowlHistory history={data?.superbowl_history} />}
      </div>
    </div>
  );
}
