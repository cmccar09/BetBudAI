import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

// Seeded fallback outright odds for The Open (real research, used only if live Betfair scrape is empty)
const FALLBACK_OUTRIGHT = [
  { name: 'Scottie Scheffler', odds: 5.0 },
  { name: 'Rory McIlroy', odds: 8.0 },
  { name: 'Jon Rahm', odds: 15.0 },
  { name: 'Xander Schauffele', odds: 17.0 },
  { name: 'Matt Fitzpatrick', odds: 26.0 },
];

const TABS = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'tips', label: '💡 Tips' },
  { id: 'majors', label: '🏆 Majors' },
  { id: 'rydercup', label: '⛳ Ryder Cup' },
];

const STATUS_COLOR = {
  completed: '#34d399',
  live: '#f87171',
  upcoming: '#60a5fa',
  pending_result: '#fbbf24',
};

function fmtFrac(decimalOdds) {
  if (!decimalOdds || decimalOdds <= 1) return '-';
  const n = Math.round((decimalOdds - 1) * 100);
  const d = 100;
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
  const g = gcd(n, d) || 1;
  return `${n / g}/${d / g}`;
}

function OutrightBoard({ contenders, tournament }) {
  const isMobile = window.innerWidth < 640;
  return (
    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14, padding: isMobile ? 14 : 20, maxWidth: 420, margin: '0 auto' }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
        ⛳ {tournament || 'The Open Championship'}
      </div>
      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 14 }}>Top 5 Winner</div>
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
            <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{c.name}</span>
          </div>
          <span style={{ fontSize: 14, fontWeight: 900, color: '#34d399' }}>{fmtFrac(c.odds)}</span>
        </div>
      ))}
    </div>
  );
}

function MajorCard({ m }) {
  const [expanded, setExpanded] = useState(false);
  const isMobile = window.innerWidth < 640;
  const color = STATUS_COLOR[m.status] || 'rgba(255,255,255,0.5)';
  const dateRange = `${new Date(m.start).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })} – ${new Date(m.end).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}`;
  const hasLeaderboard = m.leaderboard && m.leaderboard.length > 0;
  const visibleRows = expanded ? m.leaderboard : (m.leaderboard || []).slice(0, 5);

  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: isMobile ? 14 : 16, marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
        <div style={{ fontSize: 15, fontWeight: 800, color: 'white' }}>{m.name}</div>
        <span style={{ fontSize: 11, fontWeight: 800, padding: '3px 10px', borderRadius: 6, background: `${color}22`, color, textTransform: 'capitalize' }}>
          {m.status === 'pending_result' ? 'Result pending' : m.status}
        </span>
      </div>
      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginBottom: m.winner ? 8 : 0 }}>
        {dateRange} · {m.venue}
      </div>
      {m.winner && (
        <div style={{ fontSize: 14, fontWeight: 800, color: '#fbbf24', marginTop: 8, marginBottom: 8 }}>
          🏆 Winner: {m.winner}
        </div>
      )}
      {m.win_story && (
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.65)', lineHeight: 1.6, background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: 12, marginBottom: 10 }}>
          {m.win_story}
        </div>
      )}
      {hasLeaderboard && (
        <div style={{ marginTop: 10 }}>
          <div style={{ display: 'flex', fontSize: 10, color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', letterSpacing: 0.5, padding: '0 0 4px', borderBottom: '1px solid rgba(255,255,255,0.06)', marginBottom: 4 }}>
            <span style={{ flex: 1 }}>Player</span>
            {visibleRows[0]?.rounds?.length > 0 && <span style={{ width: isMobile ? 100 : 160, textAlign: 'right' }}>R1 · R2 · R3 · R4</span>}
            <span style={{ width: 44, textAlign: 'right' }}>Total</span>
          </div>
          {visibleRows.map((p, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', fontSize: 12, color: i === 0 ? '#fbbf24' : 'rgba(255,255,255,0.7)', padding: '4px 0', fontWeight: i === 0 ? 700 : 400 }}>
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {i + 1}. {p.name} {p.country && <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)' }}>({p.country})</span>}
              </span>
              {p.rounds?.length > 0 && (
                <span style={{ width: isMobile ? 100 : 160, textAlign: 'right', fontFamily: 'monospace', fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>
                  {p.rounds.join(' · ')}
                </span>
              )}
              <span style={{ width: 44, textAlign: 'right', color: '#34d399', fontWeight: 700 }}>{p.score}</span>
            </div>
          ))}
          {m.leaderboard.length > 5 && (
            <button onClick={() => setExpanded(!expanded)} style={{
              background: 'none', border: 'none', color: '#60a5fa', fontSize: 11, fontWeight: 700,
              cursor: 'pointer', padding: '6px 0 0', textDecoration: 'underline',
            }}>
              {expanded ? 'Show top 5' : `Show full leaderboard (${m.leaderboard.length})`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function GolfPage() {
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
    fetch(`${API_BASE_URL}/api/sports/golf`)
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
    return <div style={{ textAlign: 'center', padding: 60, color: 'rgba(255,255,255,0.5)' }}>⛳ Loading golf majors data…</div>;
  }

  const majors = data?.majors || [];
  const outright = (data?.outright?.length > 0) ? data.outright : FALLBACK_OUTRIGHT;
  const outrightTournament = data?.outright_tournament || 'The Open Championship';
  const previousOpenChampions = data?.previous_open_champions || [];
  const ryderCupLast = data?.ryder_cup_last || {};
  const ryderCupNext = data?.ryder_cup_next || {};
  const tipsInForm = data?.tips_in_form || [];
  const courseForm = data?.course_form || {};
  const roundPredictions = data?.round_predictions || [];
  const yesterdayPerf = data?.yesterday_performance || {};
  const completed = majors.filter(m => m.status === 'completed');
  const nextMajor = majors.find(m => m.status !== 'completed');

  const today = new Date().toISOString().slice(0, 10);
  const daysToNext = nextMajor
    ? Math.ceil((new Date(nextMajor.start) - new Date(today)) / 86400000)
    : null;

  return (
    <div style={{ minHeight: '100vh', background: '#0a0f1e', margin: '-12px', padding: 0 }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,rgba(16,90,16,0.25),rgba(8,50,8,0.18))', borderBottom: '1px solid rgba(52,211,153,0.25)', padding: isMobile ? '20px 16px' : '28px 32px', textAlign: 'center' }}>
        <div style={{ fontSize: isMobile ? 26 : 36, fontWeight: 900, color: 'white' }}>⛳ BetBud Pro Golf</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', marginTop: 6 }}>
          AI predictions across the 4 men's majors · {completed.length}/{majors.length} completed in 2026
          {nextMajor && daysToNext > 0 && (
            <span style={{ marginLeft: 8, color: '#fbbf24', fontWeight: 800 }}>{nextMajor.name} in {daysToNext} days</span>
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
            <OutrightBoard contenders={outright} tournament={outrightTournament} />
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textAlign: 'center', margin: '12px 0 24px' }}>
              {data?.outright?.length > 0 ? 'Live Betfair Exchange odds' : 'Pre-tournament odds — live exchange odds update automatically once available'}
            </div>

            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>2026 Major Winners So Far</div>
            {completed.map(m => <MajorCard key={m.name} m={m} />)}

            {/* Yesterday's picks performance */}
            {yesterdayPerf.predicted && (
              <div style={{ background: yesterdayPerf.correct ? 'rgba(52,211,153,0.08)' : 'rgba(251,191,36,0.06)', border: `1px solid ${yesterdayPerf.correct ? 'rgba(52,211,153,0.3)' : 'rgba(251,191,36,0.2)'}`, borderRadius: 10, padding: '12px 16px', marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: yesterdayPerf.correct ? '#34d399' : '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>📊 Yesterday's Pick — {yesterdayPerf.date}</div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)' }}>
                  Predicted: <strong>{yesterdayPerf.predicted}</strong> · Actual leader: <strong>{yesterdayPerf.actual_leader}</strong> {yesterdayPerf.correct ? '✅' : '❌'}
                </div>
              </div>
            )}

            {nextMajor && (
              <>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, margin: '20px 0 10px' }}>Up Next</div>
                <MajorCard m={nextMajor} />
              </>
            )}

            {/* BetBud round predictions */}
            {roundPredictions.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, margin: '20px 0 10px' }}>⛳ BetBud Round Predictions</div>
                {roundPredictions.map((p, i) => (
                  <div key={i} style={{ background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{p.prediction}</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 4 }}>{p.reason}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Course form — Royal Birkdale */}
            {courseForm.course && (
              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16, marginBottom: 20 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>🏌️ Course Form — Royal Birkdale</div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)', lineHeight: 1.6, marginBottom: 12 }}>{courseForm.key_challenges}</div>
                {courseForm.player_course_notes && Object.entries(courseForm.player_course_notes).map(([player, note]) => (
                  <div key={player} style={{ padding: '6px 0', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'white', marginBottom: 2 }}>{player}</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)', lineHeight: 1.5 }}>{note}</div>
                  </div>
                ))}
              </div>
            )}

            {previousOpenChampions.length > 0 && (
              <>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, margin: '20px 0 10px' }}>
                  Previous {outrightTournament || 'Open'} Champions
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                  {previousOpenChampions.map(c => (
                    <div key={c.year} style={{ padding: '5px 0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'rgba(255,255,255,0.75)' }}>
                        <span style={{ color: 'rgba(255,255,255,0.4)', width: 44 }}>{c.year}</span>
                        <span style={{ flex: 1, fontWeight: 700 }}>{c.winner}</span>
                      </div>
                      {c.note && <div style={{ fontSize: 11, color: '#fbbf24', marginLeft: 44, marginTop: 2 }}>{c.note}</div>}
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}
        {tab === 'tips' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
              💡 BetBud Tips — In-Form Players
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 16 }}>
              Players with multiple top-10 finishes across 2026's majors so far — not betting advice.
            </div>
            {tipsInForm.length > 0 ? tipsInForm.map((p, i) => (
              <div key={i} style={{ background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{p.player}</span>
                  <span style={{ fontSize: 12, color: '#34d399', fontWeight: 700 }}>{p.top10_count} top-10s</span>
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 4 }}>
                  Best finish: #{p.best_finish} · {p.majors.join(', ')}
                </div>
              </div>
            )) : (
              <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                Need at least 2 completed majors to identify form trends.
              </div>
            )}
          </>
        )}
        {tab === 'majors' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              All 4 Majors — 2026
            </div>
            {majors.map(m => <MajorCard key={m.name} m={m} />)}
          </>
        )}
        {tab === 'rydercup' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 16 }}>
              ⛳ Ryder Cup
            </div>

            {ryderCupNext.name && (
              <div style={{ background: 'linear-gradient(135deg,rgba(52,211,153,0.12),rgba(16,185,129,0.08))', border: '1px solid rgba(52,211,153,0.3)', borderRadius: 12, padding: isMobile ? 14 : 18, marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Next Up — {ryderCupNext.name}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'white', marginBottom: 4 }}>{ryderCupNext.venue}</div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', marginBottom: 10 }}>{ryderCupNext.dates}</div>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 10 }}>
                  {ryderCupNext.captains && Object.entries(ryderCupNext.captains).map(([team, captain]) => (
                    <div key={team}>
                      <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>{team} Captain</span>
                      <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{captain}</div>
                    </div>
                  ))}
                  <div>
                    <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>Favourite</span>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#fbbf24' }}>{ryderCupNext.favourite}</div>
                  </div>
                </div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 8 }}>{ryderCupNext.format}</div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.65)', lineHeight: 1.6, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                  {ryderCupNext.note}
                </div>
              </div>
            )}

            {ryderCupLast.name && (
              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: isMobile ? 14 : 18 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Last Edition — {ryderCupLast.name}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'white', marginBottom: 4 }}>{ryderCupLast.venue}</div>
                <div style={{ fontSize: 16, fontWeight: 900, color: '#34d399', marginBottom: 10 }}>{ryderCupLast.result}</div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.65)', lineHeight: 1.6 }}>{ryderCupLast.note}</div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
