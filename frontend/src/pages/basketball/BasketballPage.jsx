import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

const FALLBACK_OUTRIGHT = [
  { name: 'Boston Celtics',        odds: 4.0 },
  { name: 'Oklahoma City Thunder', odds: 5.0 },
  { name: 'Denver Nuggets',        odds: 7.0 },
  { name: 'Golden State Warriors', odds: 9.0 },
  { name: 'Cleveland Cavaliers',   odds: 10.0 },
];

const TABS = [
  { id: 'dashboard',    label: '📊 Dashboard' },
  { id: 'futures',      label: '🏆 Futures' },
  { id: 'summer',       label: '☀️ Summer League' },
  { id: 'standings',    label: '📋 Standings' },
  { id: 'history',      label: '🏅 Champions' },
];

function fmtFrac(dec) {
  if (!dec || dec <= 1) return '-';
  const n = Math.round((dec - 1) * 100);
  const d = 100;
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
  const g = gcd(n, d) || 1;
  return `${n / g}/${d / g}`;
}

function OutrightBoard({ contenders }) {
  const isMobile = window.innerWidth < 640;
  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14 }}>
        🏀 NBA Championship Futures
      </div>
      {(contenders || FALLBACK_OUTRIGHT).map((c, i) => (
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

function SummerLeague({ games }) {
  if (!games || games.length === 0) {
    return (
      <div style={{ padding: '24px 0', color: 'rgba(255,255,255,0.5)', textAlign: 'center' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>☀️</div>
        <div style={{ fontSize: 15, fontWeight: 600 }}>Summer League</div>
        <div style={{ fontSize: 13, marginTop: 4 }}>Games typically run 5–19 July. Check back during Las Vegas Summer League.</div>
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
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 4 }}>{g.status}</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{g.away?.team}</span>
            <span style={{ fontSize: 18, fontWeight: 900, color: '#34d399' }}>
              {g.away?.score} — {g.home?.score}
            </span>
            <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{g.home?.team}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function StandingsTable({ standings }) {
  if (!standings || standings.length === 0) {
    return <div style={{ color: 'rgba(255,255,255,0.4)', padding: '16px 0', textAlign: 'center' }}>Standings unavailable — pre-season</div>;
  }
  return (
    <div style={{ marginTop: 16 }}>
      {standings.map((conf, ci) => (
        <div key={ci} style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
            {conf.conference}
          </div>
          {(conf.teams || []).slice(0, 8).map((t, i) => (
            <div key={t.team} style={{
              display: 'flex', justifyContent: 'space-between', padding: '7px 12px',
              background: i % 2 === 0 ? 'rgba(255,255,255,0.03)' : 'transparent',
              borderRadius: 6, fontSize: 13, color: 'rgba(255,255,255,0.85)',
            }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <span style={{ color: 'rgba(255,255,255,0.35)', width: 18 }}>{i + 1}</span>
                <span style={{ fontWeight: 600 }}>{t.team}</span>
              </div>
              <span style={{ color: '#34d399', fontWeight: 700 }}>{t.wins}–{t.losses}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function ChampionsHistory({ history }) {
  const champs = history || [
    { year: 2024, winner: 'Boston Celtics',    defeated: 'Dallas Mavericks', series: '4-1' },
    { year: 2023, winner: 'Denver Nuggets',    defeated: 'Miami Heat',       series: '4-1' },
    { year: 2022, winner: 'Golden State Warriors', defeated: 'Boston Celtics', series: '4-2' },
    { year: 2021, winner: 'Milwaukee Bucks',   defeated: 'Phoenix Suns',     series: '4-2' },
    { year: 2020, winner: 'Los Angeles Lakers','defeated': 'Miami Heat',      series: '4-2' },
  ];
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
        NBA Champions — Last 5 Seasons
      </div>
      {champs.map((c, i) => (
        <div key={c.year} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '12px 16px', marginBottom: 8, borderRadius: 10,
          background: i === 0 ? 'rgba(251,191,36,0.08)' : 'rgba(255,255,255,0.04)',
          border: i === 0 ? '1px solid rgba(251,191,36,0.2)' : '1px solid rgba(255,255,255,0.07)',
        }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 800, color: i === 0 ? '#fbbf24' : 'white' }}>
              {i === 0 ? '🏆 ' : ''}{c.winner}
            </div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
              def. {c.defeated} {c.series}
            </div>
          </div>
          <div style={{ fontSize: 22, fontWeight: 900, color: 'rgba(255,255,255,0.2)' }}>{c.year}</div>
        </div>
      ))}
    </div>
  );
}

export default function BasketballPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const isMobile = window.innerWidth < 640;

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/sports/basketball`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const outright = data?.outright || FALLBACK_OUTRIGHT;
  const tip = data?.tip || {};

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: 'white', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
        padding: isMobile ? '20px 16px 16px' : '28px 32px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
            <span style={{ fontSize: isMobile ? 28 : 36 }}>🏀</span>
            <div>
              <div style={{ fontSize: isMobile ? 20 : 26, fontWeight: 900, color: 'white', letterSpacing: -0.5 }}>
                BetBud Basketball
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
                NBA · Championship Futures · Summer League
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
            Loading NBA data…
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
            <OutrightBoard contenders={outright} />
            {(tip.value_picks || []).length > 0 && (
              <div style={{ marginTop: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                  Value Picks (10/1+)
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

        {!loading && activeTab === 'futures' && <OutrightBoard contenders={outright} />}
        {!loading && activeTab === 'summer' && <SummerLeague games={data?.summer_league_games} />}
        {!loading && activeTab === 'standings' && <StandingsTable standings={data?.standings} />}
        {!loading && activeTab === 'history' && <ChampionsHistory history={data?.previous_champions} />}
      </div>
    </div>
  );
}
