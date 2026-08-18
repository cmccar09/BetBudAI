import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

// Seeded fallback outright odds for World Matchplay (real research, used only if live Betfair scrape is empty)
const FALLBACK_OUTRIGHT = [
  { name: 'Luke Littler', odds_decimal: 1.91, odds_fractional: '10/11', note: 'Defending champion, outright favourite' },
  { name: 'Luke Humphries', odds_decimal: 5.5, odds_fractional: '9/2', note: 'World number one on the Order of Merit' },
  { name: 'Wessel Nijman', odds_decimal: 11.0, odds_fractional: '10/1', note: 'Rising Dutch star' },
  { name: 'Gerwyn Price', odds_decimal: 15.0, odds_fractional: '14/1', note: '2026 European Darts Grand Prix winner' },
  { name: 'Michael van Gerwen', odds_decimal: 15.0, odds_fractional: '14/1', note: 'Three-time champion' },
  { name: 'Gian van Veen', odds_decimal: 17.0, odds_fractional: '16/1', note: 'World Championship runner-up' },
];

const TABS = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'tips', label: '🎯 Tips' },
  { id: 'tournaments', label: '🏆 Tournaments' },
  { id: 'history', label: '📜 History' },
];

const STATUS_COLOR = {
  completed: '#34d399',
  live: '#f87171',
  upcoming: '#60a5fa',
};

function fmtFrac(decimalOdds) {
  if (!decimalOdds || decimalOdds <= 1) return '-';
  const n = Math.round((decimalOdds - 1) * 100);
  const d = 100;
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
  const g = gcd(n, d) || 1;
  return `${n / g}/${d / g}`;
}

function OutrightBoard({ contenders, tournament, meta }) {
  const isMobile = window.innerWidth < 640;
  const dateRange = meta?.start && meta?.end
    ? `${new Date(meta.start).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} – ${new Date(meta.end).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}`
    : null;
  return (
    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14, padding: isMobile ? 14 : 20, maxWidth: 460, margin: '0 auto' }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
        🎯 {tournament || 'World Matchplay'}
      </div>
      {meta && (dateRange || meta.venue) && (
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>
          {dateRange}{dateRange && meta.venue ? ' · ' : ''}{meta.venue}
        </div>
      )}
      {meta?.prize_fund && (
        <div style={{ fontSize: 11, color: 'rgba(251,191,36,0.8)', marginBottom: 10 }}>
          Prize fund {meta.prize_fund}{meta.winner_prize ? ` · Winner ${meta.winner_prize}` : ''}
        </div>
      )}
      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 14 }}>Outright Winner</div>
      {contenders.map((c, i) => (
        <div key={c.name} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 12px', marginBottom: 6, borderRadius: 8,
          background: i === 0 ? 'rgba(251,191,36,0.1)' : 'rgba(255,255,255,0.03)',
          border: i === 0 ? '1px solid rgba(251,191,36,0.3)' : '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: i === 0 ? '#fbbf24' : 'rgba(255,255,255,0.4)', width: 18, flexShrink: 0 }}>
              {i === 0 ? '🏆' : `#${i + 1}`}
            </span>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{c.name}</div>
              {c.note && <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>{c.note}</div>}
            </div>
          </div>
          <span style={{ fontSize: 14, fontWeight: 900, color: '#34d399', flexShrink: 0, marginLeft: 8 }}>{c.odds_fractional || fmtFrac(c.odds_decimal ?? c.odds)}</span>
        </div>
      ))}
    </div>
  );
}

function TournamentCard({ t }) {
  const isMobile = window.innerWidth < 640;
  const color = STATUS_COLOR[t.status] || 'rgba(255,255,255,0.5)';
  const dateRange = `${new Date(t.start).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} – ${new Date(t.end).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}`;

  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: isMobile ? 14 : 16, marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
        <div style={{ fontSize: 15, fontWeight: 800, color: 'white' }}>{t.name}</div>
        <span style={{ fontSize: 11, fontWeight: 800, padding: '3px 10px', borderRadius: 6, background: `${color}22`, color, textTransform: 'capitalize' }}>
          {t.status}
        </span>
      </div>
      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginBottom: t.winner ? 8 : 0 }}>
        {dateRange} · {t.venue}
      </div>
      {t.prize_fund && (
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 4 }}>
          Prize fund: {t.prize_fund}{t.winner_prize ? ` · Winner: ${t.winner_prize}` : ''} · Format: {t.format}
        </div>
      )}
      {t.winner && (
        <div style={{ fontSize: 14, fontWeight: 800, color: '#fbbf24', marginTop: 8 }}>
          🏆 Winner: {t.winner}
        </div>
      )}
      {t.note && (
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', fontStyle: 'italic', marginTop: 6 }}>{t.note}</div>
      )}
    </div>
  );
}

export default function DartsPage() {
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
    fetch(`${API_BASE_URL}/api/sports/darts`)
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
    return <div style={{ textAlign: 'center', padding: 60, color: 'rgba(255,255,255,0.5)' }}>🎯 Loading darts data…</div>;
  }

  const tournaments = data?.tournaments || [];
  const outright = (data?.outright?.length > 0) ? data.outright : FALLBACK_OUTRIGHT;
  const outrightTournament = data?.outright_tournament || 'World Matchplay';
  const recentWinners = data?.recent_winners || [];
  const liveFixtures = data?.live_fixtures || [];
  const predictions = data?.predictions || [];
  const isLive = data?.meta?.is_live || false;

  const completed = tournaments.filter(t => t.status === 'completed');
  const nextOrLive = tournaments.find(t => t.status !== 'completed');
  const today = new Date().toISOString().slice(0, 10);
  const daysToNext = nextOrLive && nextOrLive.status === 'upcoming'
    ? Math.ceil((new Date(nextOrLive.start) - new Date(today)) / 86400000)
    : null;

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', margin: '-12px', padding: 0 }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,rgba(16,90,90,0.25),rgba(8,50,50,0.18))', borderBottom: '1px solid rgba(52,211,153,0.25)', padding: isMobile ? '20px 16px' : '28px 32px', textAlign: 'center' }}>
        <div style={{ fontSize: isMobile ? 26 : 36, fontWeight: 900, color: 'white' }}>🎯 BetBud Darts</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', marginTop: 6 }}>
          AI predictions across the PDC major tournaments · {completed.length}/{tournaments.length} completed this season
          {nextOrLive && isLive && <span style={{ marginLeft: 8, color: '#f87171', fontWeight: 800 }}>🔴 {nextOrLive.name} LIVE now</span>}
          {nextOrLive && !isLive && daysToNext > 0 && (
            <span style={{ marginLeft: 8, color: '#fbbf24', fontWeight: 800 }}>{nextOrLive.name} in {daysToNext} days</span>
          )}
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
            <OutrightBoard contenders={outright} tournament={outrightTournament} meta={nextOrLive} />
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textAlign: 'center', margin: '12px 0 16px' }}>
              {data?.outright?.length > 0 ? 'Live Betfair Exchange odds' : 'Pre-tournament odds — live exchange odds update automatically once available'}
            </div>

            {predictions.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, margin: '0 0 10px' }}>
                  🎯 BetBud Match Predictions
                  <span style={{ fontSize: 10, fontWeight: 600, color: 'rgba(255,255,255,0.35)', marginLeft: 8, textTransform: 'none' }}>updates daily while live</span>
                </div>
                {predictions.map((p, i) => (
                  <div key={i} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(52,211,153,0.2)', borderLeft: '3px solid #34d399', borderRadius: 8, padding: '12px 14px', marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{p.match}</span>
                      <span style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24' }}>{p.predicted_score}</span>
                    </div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', lineHeight: 1.5 }}>{p.reason}</div>
                  </div>
                ))}
              </div>
            )}

            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Recent Major Winners</div>
            {recentWinners.slice(0, 2).map(w => (
              <div key={w.tournament} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 14, marginBottom: 10 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{w.tournament}</div>
                <div style={{ fontSize: 14, fontWeight: 800, color: '#fbbf24', marginTop: 4 }}>🏆 {w.winner}{w.score ? ` ${w.score} ${w.runner_up}` : ''}</div>
                {w.note && <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 6, lineHeight: 1.5 }}>{w.note}</div>}
              </div>
            ))}

            {nextOrLive && (
              <>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, margin: '20px 0 10px' }}>
                  {isLive ? 'Live Now' : 'Up Next'}
                </div>
                <TournamentCard t={nextOrLive} />
              </>
            )}
          </>
        )}

        {tab === 'tips' && (
          <>
            {liveFixtures.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#f87171', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
                  🔴 Live Fixtures
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 12 }}>
                  {liveFixtures[0]?.session || 'Today\'s session'}
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(248,113,113,0.25)', borderRadius: 10, padding: '12px 14px' }}>
                  {liveFixtures.map((f, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '6px 0', borderBottom: i < liveFixtures.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none', color: 'rgba(255,255,255,0.8)' }}>
                      <span>{f.players[0]} vs {f.players[1]}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
              🎯 Match Predictions
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 16 }}>
              Predicted leg/set scores for confirmed live-tournament fixtures, refreshed daily.
            </div>
            {predictions.length > 0 ? predictions.map((p, i) => (
              <div key={i} style={{ background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 8, padding: '12px 14px', marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{p.match}</span>
                  <span style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24' }}>{p.predicted_score}</span>
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 6, lineHeight: 1.5 }}>{p.reason}</div>
              </div>
            )) : (
              <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                No live tournament fixtures right now — check back once the next major's draw is confirmed.
              </div>
            )}
          </>
        )}

        {tab === 'tournaments' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              PDC Majors — 2026 Season
            </div>
            {tournaments.map(t => <TournamentCard key={t.name} t={t} />)}
          </>
        )}

        {tab === 'history' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              Recent Major Results
            </div>
            {recentWinners.map(w => (
              <div key={w.tournament} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16, marginBottom: 10 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{w.tournament}</div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginTop: 2 }}>{w.venue} · {w.date}</div>
                <div style={{ fontSize: 15, fontWeight: 800, color: '#fbbf24', marginTop: 8 }}>
                  🏆 {w.winner}{w.score ? ` beat ${w.runner_up} ${w.score}` : ''}
                </div>
                {w.note && <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', marginTop: 8, lineHeight: 1.6 }}>{w.note}</div>}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
