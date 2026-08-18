import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

// Fallback: show actual 2026 Wimbledon results when live odds unavailable
const FALLBACK_MEN = [
  { name: 'Jannik Sinner 🏆', odds: 0 },
  { name: 'Alexander Zverev', odds: 0 },
  { name: 'Novak Djokovic', odds: 0 },
  { name: 'Arthur Fery (wildcard)', odds: 0 },
];
const FALLBACK_WOMEN = [
  { name: 'Linda Noskova 🏆', odds: 0 },
  { name: 'Karolina Muchova', odds: 0 },
  { name: 'Coco Gauff', odds: 0 },
  { name: 'Marta Kostyuk', odds: 0 },
];

const TABS = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'tips', label: '💡 Tips' },
  { id: 'results', label: '🎾 Results' },
  { id: 'schedule', label: '📅 Schedule' },
];

function fmtFrac(decimalOdds) {
  if (!decimalOdds || decimalOdds <= 1) return '-';
  const n = Math.round((decimalOdds - 1) * 100);
  const d = 100;
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
  const g = gcd(n, d) || 1;
  return `${n / g}/${d / g}`;
}

function OutrightBoard({ title, contenders, flag }) {
  const isMobile = window.innerWidth < 640;
  return (
    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14, padding: isMobile ? 14 : 20, flex: 1, minWidth: 280 }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14 }}>
        {flag} {title} — Top 5 Winner
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
            <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{c.name}</span>
          </div>
          <span style={{ fontSize: 14, fontWeight: 900, color: '#34d399' }}>{fmtFrac(c.odds)}</span>
        </div>
      ))}
    </div>
  );
}

function MatchRow({ m }) {
  const flagEmoji = (country) => '';
  const completed = m.completed;
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '10px 14px', marginBottom: 6, borderRadius: 8,
      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>
          <span style={{ color: m.winner === m.player1 ? '#34d399' : 'inherit' }}>{m.player1}</span>
          {' vs '}
          <span style={{ color: m.winner === m.player2 ? '#34d399' : 'inherit' }}>{m.player2}</span>
        </div>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
          {m.tour === 'mens' ? "Men's" : "Women's"}
          {m.round && <> · <span style={{ color: '#a78bfa', fontWeight: 700 }}>{m.round}</span></>}
          {m.court && <> · {m.court}</>} · {completed ? m.result_text : m.status}
        </div>
        {completed && m.sets1 && m.sets1.length > 0 && (
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)', marginTop: 4, fontFamily: 'monospace' }}>
            Sets: {m.sets1.map((s1, i) => `${s1}-${m.sets2[i] ?? ''}`).join('  ')}
          </div>
        )}
      </div>
      <span style={{
        fontSize: 11, fontWeight: 800, padding: '3px 10px', borderRadius: 6,
        background: completed ? 'rgba(52,211,153,0.15)' : 'rgba(96,165,250,0.15)',
        color: completed ? '#34d399' : '#60a5fa',
      }}>
        {completed ? 'FT' : m.status}
      </span>
    </div>
  );
}

export default function WimbledonPage() {
  const [tab, setTab] = useState('dashboard');
  const [roundFilter, setRoundFilter] = useState('all');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 640);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 640);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const loadData = () => {
    fetch(`${API_BASE_URL}/api/sports/wimbledon`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15 * 60 * 1000); // refresh every 15 min
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 60, color: 'rgba(255,255,255,0.5)' }}>🎾 Loading Wimbledon data…</div>;
  }

  const matches = data?.matches || [];
  const meta = data?.meta || {};
  const outrightMen = (data?.outright_men?.length > 0) ? data.outright_men : FALLBACK_MEN;
  const outrightWomen = (data?.outright_women?.length > 0) ? data.outright_women : FALLBACK_WOMEN;
  const prevChampsMen = data?.previous_champions_men || [];
  const prevChampsWomen = data?.previous_champions_women || [];
  const tipsInForm = data?.tips_in_form || [];
  const tipsPredictions = data?.tips_predictions || [];
  const yesterdayPerf = data?.yesterday_performance || {};

  const isComplete = meta.is_complete === true;
  const completed = matches.filter(m => m.completed).sort((a, b) => new Date(b.date) - new Date(a.date));
  const scheduled = matches.filter(m => !m.completed);
  const recentResults = completed.slice(0, 20);

  // Build prediction lookup by match_id for inline display on scheduled matches
  const predMap = {};
  tipsPredictions.forEach(p => { predMap[p.match_id] = p; });

  return (
    <div style={{ minHeight: '100vh', background: '#0a0f1e', margin: '-12px', padding: 0 }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,rgba(34,139,34,0.25),rgba(16,90,16,0.18))', borderBottom: '1px solid rgba(52,211,153,0.25)', padding: isMobile ? '20px 16px' : '28px 32px', textAlign: 'center' }}>
        <div style={{ fontSize: isMobile ? 28 : 36, fontWeight: 900, color: 'white' }}>🎾 BetBud Pro Tennis</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', marginTop: 6 }}>
          AI predictions & live results · {meta.tournament_start} – {meta.tournament_end}
          {meta.is_live && <span style={{ marginLeft: 8, color: '#34d399', fontWeight: 800 }}>● LIVE</span>}
          {meta.is_complete && <span style={{ marginLeft: 8, color: '#fbbf24', fontWeight: 800 }}>✅ COMPLETED</span>}
        </div>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 4 }}>
          {meta.matches_completed}/{meta.matches_total} matches played · updated {meta.updated_at ? new Date(meta.updated_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '—'}
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
            {/* Champion card — shows when tournament is complete */}
            {isComplete && (
              <div style={{ background: 'linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%)', border: '1px solid rgba(251,191,36,0.4)', borderRadius: 16, padding: '20px 24px', marginBottom: 20 }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(251,191,36,0.8)', textTransform: 'uppercase', letterSpacing: 2, textAlign: 'center', marginBottom: 14 }}>
                  🏆 2026 Wimbledon Champions
                </div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 220, background: 'rgba(251,191,36,0.07)', border: '1px solid rgba(251,191,36,0.25)', borderRadius: 12, padding: '14px 16px', textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: '#fbbf24', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>🎾 Men's Singles</div>
                    <div style={{ fontSize: 26, fontWeight: 900, color: 'white' }}>Jannik Sinner</div>
                    <div style={{ fontSize: 12, color: '#fbbf24', marginTop: 4 }}>🇮🇹 Italy · 5th Grand Slam</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 6 }}>def. Zverev 6-7 7-6 6-3 6-4</div>
                    <div style={{ fontSize: 10, color: '#34d399', marginTop: 4 }}>✅ BetBud picked Sinner</div>
                  </div>
                  <div style={{ flex: 1, minWidth: 220, background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.25)', borderRadius: 12, padding: '14px 16px', textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: '#a78bfa', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>🎾 Women's Singles</div>
                    <div style={{ fontSize: 26, fontWeight: 900, color: 'white' }}>Linda Noskova</div>
                    <div style={{ fontSize: 12, color: '#a78bfa', marginTop: 4 }}>🇨🇿 Czech Republic · First slam</div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 6 }}>def. Muchova 6-2 5-7 6-3</div>
                    <div style={{ fontSize: 10, color: '#fbbf24', marginTop: 4 }}>⚡ Upset — beat 5 seeds en route</div>
                  </div>
                </div>
                {/* US Open preview teaser */}
                <div style={{ marginTop: 14, padding: '10px 14px', background: 'rgba(96,165,250,0.08)', border: '1px solid rgba(96,165,250,0.2)', borderRadius: 10, textAlign: 'center' }}>
                  <span style={{ fontSize: 12, color: '#60a5fa', fontWeight: 700 }}>⛳ Next up: US Open</span>
                  <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginLeft: 8 }}>~25 Aug · Flushing Meadows · BetBud picks in Tips tab</span>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 20 }}>
              <OutrightBoard title="Men's Singles" contenders={outrightMen} flag="🎾" />
              <OutrightBoard title="Women's Singles" contenders={outrightWomen} flag="🎾" />
            </div>
            {!isComplete && (
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', textAlign: 'center', marginBottom: 24 }}>
              {data?.outright_men?.length > 0 ? 'Live Betfair Exchange odds' : 'Pre-tournament odds — live exchange odds update automatically once available'}
            </div>
            )}
            {/* Yesterday's picks performance */}
            {yesterdayPerf.total > 0 && (
              <div style={{ background: yesterdayPerf.win_pct >= 60 ? 'rgba(52,211,153,0.08)' : 'rgba(251,191,36,0.06)', border: `1px solid ${yesterdayPerf.win_pct >= 60 ? 'rgba(52,211,153,0.3)' : 'rgba(251,191,36,0.2)'}`, borderRadius: 10, padding: '12px 16px', marginBottom: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 800, color: yesterdayPerf.win_pct >= 60 ? '#34d399' : '#fbbf24', textTransform: 'uppercase', letterSpacing: 1 }}>📊 Yesterday's Picks — {yesterdayPerf.date}</div>
                    <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', marginTop: 4 }}>
                      {yesterdayPerf.correct}/{yesterdayPerf.total} correct
                      {yesterdayPerf.win_pct !== null && <span style={{ color: yesterdayPerf.win_pct >= 60 ? '#34d399' : '#f87171', fontWeight: 700, marginLeft: 8 }}>{yesterdayPerf.win_pct}% strike rate</span>}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {yesterdayPerf.picks?.map((p, i) => (
                      <span key={i} title={`${p.player1} vs ${p.player2} — picked ${p.predicted}, actual ${p.actual}`}
                        style={{ width: 24, height: 24, borderRadius: '50%', background: p.correct ? '#34d399' : '#f87171', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12 }}>
                        {p.correct ? '✓' : '✗'}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Up Next with inline BetBud pick */}
            {scheduled.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
                  🔴 Up Next — BetBud Picks
                </div>
                {scheduled.slice(0, 8).map(m => {
                  const pred = predMap[m.match_id];
                  return (
                    <div key={m.match_id} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>
                            <span style={{ color: pred?.predicted_winner === m.player1 ? '#34d399' : 'inherit' }}>{m.player1}</span>
                            {' vs '}
                            <span style={{ color: pred?.predicted_winner === m.player2 ? '#34d399' : 'inherit' }}>{m.player2}</span>
                          </div>
                          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>
                            {m.tour === 'mens' ? "Men's" : "Women's"}
                            {m.round && <> · <span style={{ color: '#a78bfa' }}>{m.round}</span></>}
                            {m.court && <> · {m.court}</>}
                          </div>
                        </div>
                        {pred && (
                          <div style={{ textAlign: 'right', marginLeft: 12, flexShrink: 0 }}>
                            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>BetBud Pick</div>
                            <div style={{ fontSize: 12, fontWeight: 700, color: '#34d399' }}>{pred.predicted_winner}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Latest Results</div>
            {recentResults.slice(0, 8).map(m => <MatchRow key={m.match_id} m={m} />)}

            {(prevChampsMen.length > 0 || prevChampsWomen.length > 0) && (
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 24 }}>
                {prevChampsMen.length > 0 && (
                  <div style={{ flex: 1, minWidth: 260 }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Previous Champions — Men's</div>
                    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                      {prevChampsMen.map(c => (
                        <div key={c.year} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '5px 0', color: 'rgba(255,255,255,0.75)' }}>
                          <span style={{ color: 'rgba(255,255,255,0.4)', width: 44 }}>{c.year}</span>
                          <span style={{ flex: 1, fontWeight: 700 }}>{c.winner}</span>
                          <span style={{ color: 'rgba(255,255,255,0.4)' }}>{c.country}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {prevChampsWomen.length > 0 && (
                  <div style={{ flex: 1, minWidth: 260 }}>
                    <div style={{ fontSize: 13, fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Previous Champions — Women's</div>
                    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                      {prevChampsWomen.map(c => (
                        <div key={c.year} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '5px 0', color: 'rgba(255,255,255,0.75)' }}>
                          <span style={{ color: 'rgba(255,255,255,0.4)', width: 44 }}>{c.year}</span>
                          <span style={{ flex: 1, fontWeight: 700 }}>{c.winner}</span>
                          <span style={{ color: 'rgba(255,255,255,0.4)' }}>{c.country}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
        {tab === 'tips' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
              💡 BetBud Tips {isComplete ? '— US Open Preview' : ''}
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 16 }}>
              {isComplete ? 'Wimbledon complete. US Open starts ~25 Aug at Flushing Meadows.' : 'Based on real match data scraped this run — not betting advice, just analysis.'}
            </div>

            {tipsPredictions.length > 0 && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>{isComplete ? 'US Open BetBud Picks' : 'Predictions — Next Matches'}</div>
                {tipsPredictions.map(p => (
                  <div key={p.match_id} style={{ background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.2)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>
                      {p.player1} vs {p.player2}
                      <span style={{ fontSize: 11, color: '#a78bfa', fontWeight: 700, marginLeft: 8 }}>{p.round}</span>
                    </div>
                    <div style={{ fontSize: 12, color: '#34d399', marginTop: 4, fontWeight: 700 }}>
                      Pick: {p.predicted_winner}
                    </div>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 2 }}>{p.reason}</div>
                  </div>
                ))}
              </div>
            )}

            {tipsInForm.length > 0 && (
              <div>
                <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>In-Form Players</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 10 }}>Won their last match without dropping a set</div>
                {tipsInForm.map((p, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, padding: '10px 14px', marginBottom: 6 }}>
                    <div>
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'white' }}>{p.player}</span>
                      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginLeft: 8 }}>{p.tour === 'mens' ? "Men's" : "Women's"} · {p.round}</span>
                    </div>
                    <span style={{ fontSize: 11, color: '#34d399' }}>🔥 Straight sets</span>
                  </div>
                ))}
              </div>
            )}

            {tipsPredictions.length === 0 && tipsInForm.length === 0 && (
              <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
                Tips will appear once matches start generating form data.
              </div>
            )}
          </>
        )}
        {tab === 'results' && (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1 }}>
                All Results ({completed.filter(m => roundFilter === 'all' || m.round === roundFilter).length})
              </div>
              <select value={roundFilter} onChange={e => setRoundFilter(e.target.value)} style={{
                background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6,
                color: 'white', fontSize: 12, padding: '6px 10px',
              }}>
                <option value="all">All Rounds</option>
                {[...new Set(completed.map(m => m.round).filter(Boolean))]
                  .sort((a, b) => (completed.find(m => m.round === a)?.round_id || 0) - (completed.find(m => m.round === b)?.round_id || 0))
                  .map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            {completed.filter(m => roundFilter === 'all' || m.round === roundFilter).map(m => <MatchRow key={m.match_id} m={m} />)}
          </>
        )}
        {tab === 'schedule' && (
          <>
            <div style={{ fontSize: 13, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
              Upcoming / In Progress ({scheduled.length})
            </div>
            {scheduled.map(m => <MatchRow key={m.match_id} m={m} />)}
          </>
        )}
      </div>
    </div>
  );
}
