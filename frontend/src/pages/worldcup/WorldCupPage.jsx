import { useState, useEffect, useCallback } from 'react'
import './worldcup.css'
import Header from './components/Header'
import Ticker from './components/Ticker'
import Dashboard from './components/Dashboard'
import Today from './components/Today'
import Groups from './components/Groups'
import Fixtures from './components/Fixtures'
import Bracket from './components/Bracket'
import { Scorers, Assisters, CleanSheets } from './components/PlayerStats'
import EnglandXI from './components/EnglandXI'
import Specials from './components/Specials'
import Bets from './components/Bets'
import { fetchStandings, fetchAllFixtures, parseStandings, parseFixtures, getApiKey } from './services/apiFootball'
import { GROUPS } from './data/groups'

function WcAnalysis({ data, hideBet = false }) {
  const golden = data?.golden_boot || []
  const bracket = data?.bracket || {}
  const analysis = bracket.analysis || {}
  const halves = bracket.halves || {}
  const topBet = analysis.betbud_top_bet || {}
  const updated = data?.meta?.updated_at ? new Date(data.meta.updated_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : null

  const cardStyle = { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: 18, marginBottom: 16 }
  const headStyle = { fontSize: 12, fontWeight: 800, color: '#34d399', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }

  if (!data) return (
    <div style={{ textAlign: 'center', padding: 40, color: 'rgba(255,255,255,0.4)' }}>
      Loading live analysis…
    </div>
  )

  return (
    <div style={{ padding: '16px 0' }}>
      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginBottom: 20, textAlign: 'right' }}>
        Updated {updated} · refreshes daily at 06:00 UTC
      </div>

      {/* ⭐ Argentina Top Bet card — shown first and most prominently */}
      {topBet.team && !hideBet && (
        <div style={{ background: 'linear-gradient(135deg,rgba(73,140,84,0.2),rgba(102,167,120,0.12))', border: '2px solid rgba(73,160,90,0.5)', borderRadius: 14, padding: 20, marginBottom: 20, position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: 12, right: 12, background: 'linear-gradient(135deg,#16a34a,#15803d)', borderRadius: 8, padding: '3px 10px', fontSize: 10, fontWeight: 800, color: 'white', textTransform: 'uppercase', letterSpacing: 1 }}>
            {topBet.confidence}
          </div>
          <div style={{ fontSize: 12, fontWeight: 800, color: '#4ade80', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
            ⭐ BetBud Top Bet
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12, flexWrap: 'wrap' }}>
            <div style={{ fontSize: 40 }}>🇦🇷</div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 900, color: 'white' }}>{topBet.team}</div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>{topBet.bet_type}</div>
            </div>
            <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
              <div style={{ fontSize: 28, fontWeight: 900, color: '#4ade80' }}>{topBet.odds_fractional}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>decimal {topBet.odds_decimal}</div>
            </div>
          </div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', lineHeight: 1.7, marginBottom: 14 }}>
            {topBet.reasoning}
          </div>
          {topBet.key_stats && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 6 }}>
              {topBet.key_stats.map((s, i) => (
                <div key={i} style={{ fontSize: 11, color: '#4ade80', background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)', borderRadius: 6, padding: '4px 10px' }}>
                  ✓ {s}
                </div>
              ))}
            </div>
          )}
          {topBet.forecast_final && (
            <div style={{ marginTop: 14, fontSize: 13, fontWeight: 800, color: '#fbbf24', textAlign: 'center', paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
              🏆 Forecast Final: {topBet.forecast_final}
            </div>
          )}
        </div>
      )}

      {analysis.headline && (
        <div style={{ ...cardStyle, background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.25)' }}>
          <div style={{ ...headStyle, color: '#fbbf24' }}>🤖 BetBud Bracket Analysis</div>
          <div style={{ fontSize: 16, fontWeight: 800, color: '#fbbf24', marginBottom: 10 }}>{analysis.headline}</div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', lineHeight: 1.7 }}>{analysis.detail}</div>
        </div>
      )}

      {analysis.mbappe_note && (
        <div style={{ ...cardStyle, background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.25)' }}>
          <div style={{ ...headStyle, color: '#34d399' }}>⚽ Mbappé Watch</div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', lineHeight: 1.7 }}>{analysis.mbappe_note}</div>
        </div>
      )}

      {golden.length > 0 && (
        <div style={cardStyle}>
          <div style={headStyle}>🥇 Live Golden Boot</div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 10 }}>All goals scraped from ESPN daily at 06:00 UTC</div>
          {golden.slice(0, 10).map((p, i) => (
            <div key={p.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: i < 9 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
              <span style={{ fontSize: 13, color: 'white', fontWeight: i < 3 ? 800 : 400 }}>
                {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`} {p.name}
                <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginLeft: 8 }}>{p.team}</span>
              </span>
              <span style={{ fontSize: 14, fontWeight: 800, color: '#34d399' }}>{p.goals} ⚽</span>
            </div>
          ))}
        </div>
      )}

      {Object.entries(halves).map(([key, half]) => (
        <div key={key} style={cardStyle}>
          <div style={headStyle}>{half.label}</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6, marginBottom: 10 }}>{half.description}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {(half.teams || []).map(t => (
              <span key={t} style={{ fontSize: 11, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 6, padding: '3px 8px', color: 'rgba(255,255,255,0.7)' }}>{t}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

const TABS = [
  { id: 'dashboard', label: '📊 Dashboard' },
  { id: 'today', label: '🔮 Daily Predictions' },
  { id: 'groups', label: '🏆 Groups' },
  { id: 'fixtures', label: '📅 Fixtures' },
  { id: 'bracket', label: '🏅 Knockout' },
  { id: 'scorers', label: '⚽ Scorers' },
  { id: 'assists', label: '👟 Assists' },
  { id: 'cleansheets', label: '🧤 Clean Sheets' },
  { id: 'england', label: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England XI' },
  { id: 'specials', label: '🎰 Specials' },
  { id: 'bets', label: '💰 BetBud Bets' },
]

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com'

export default function WorldCupPage() {
  const [tab, setTab] = useState('dashboard')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [liveGroups, setLiveGroups] = useState(null)
  const [liveFixtures, setLiveFixtures] = useState([])
  const [wcData, setWcData] = useState(null)

  const refresh = useCallback(async () => {
    if (!getApiKey()) return
    try {
      const [standingsData, fixturesData] = await Promise.all([
        fetchStandings(),
        fetchAllFixtures(),
      ])
      if (standingsData) {
        const parsed = parseStandings(standingsData, GROUPS)
        if (parsed) setLiveGroups(parsed)
      }
      if (fixturesData) {
        setLiveFixtures(parseFixtures(fixturesData))
      }
      setLastUpdated(new Date().toLocaleTimeString())
    } catch (e) {
      console.warn('API refresh failed:', e)
    }
  }, [])

  // Fetch live WC analysis data (bracket, golden boot) from BetBudAI Sports API
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/sports/worldcup`)
      .then(r => r.json())
      .then(d => { if (d.success) setWcData(d) })
      .catch(() => {})
    const interval = setInterval(() => {
      fetch(`${API_BASE_URL}/api/sports/worldcup`)
        .then(r => r.json())
        .then(d => { if (d.success) setWcData(d) })
        .catch(() => {})
    }, 15 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 15 * 60 * 1000)
    return () => clearInterval(interval)
  }, [refresh])

  return (
    <div className="wc-page" style={{ minHeight: '100vh', background: 'var(--dark)' }}>
      {/* Sticky header + nav unit — wrapping both keeps nav below header at all screen sizes */}
      <div style={{ position: 'sticky', top: 0, zIndex: 100 }}>
        <Header lastUpdated={lastUpdated} onRefresh={refresh} />
        <Ticker fixtures={liveFixtures.slice(0, 10)} />
        <nav style={{
          background: '#1e293b',
          borderBottom: '1px solid #334155',
          display: 'flex', overflowX: 'auto',
          scrollbarWidth: 'none',
          WebkitOverflowScrolling: 'touch',
          boxShadow: '0 2px 12px rgba(0,0,0,0.3)',
        }}>
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                background: 'none', border: 'none',
                color: tab === t.id ? '#f1f5f9' : '#64748b',
                padding: '10px 12px', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                whiteSpace: 'nowrap', minWidth: 0,
                borderBottom: `3px solid ${tab === t.id ? '#6366f1' : 'transparent'}`,
                transition: 'all .2s',
                flexShrink: 0,
              }}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Pages */}
      <main>
        {tab === 'dashboard' && (() => {
          const topBet = wcData?.bracket?.analysis?.betbud_top_bet
          return (
            <>
              {topBet?.team && (
                <div style={{ maxWidth: 900, margin: '0 auto', padding: '16px 16px 0' }}>
                  <div style={{ background: 'linear-gradient(135deg,rgba(22,163,74,0.2),rgba(16,185,129,0.1))', border: '2px solid rgba(22,163,74,0.45)', borderRadius: 14, padding: '18px 20px', position: 'relative', overflow: 'hidden' }}>
                    <div style={{ position: 'absolute', top: 12, right: 12, background: 'linear-gradient(135deg,#16a34a,#15803d)', borderRadius: 8, padding: '3px 10px', fontSize: 10, fontWeight: 800, color: 'white', textTransform: 'uppercase', letterSpacing: 1 }}>
                      {topBet.confidence}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 10, fontWeight: 800, color: '#4ade80', textTransform: 'uppercase', letterSpacing: 1 }}>⭐ BetBud Top Bet</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 10, flexWrap: 'wrap' }}>
                      <div style={{ fontSize: 36 }}>🇦🇷</div>
                      <div>
                        <div style={{ fontSize: 22, fontWeight: 900, color: 'white' }}>{topBet.team}</div>
                        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>{topBet.bet_type}</div>
                      </div>
                      <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                        <div style={{ fontSize: 30, fontWeight: 900, color: '#4ade80' }}>{topBet.odds_fractional}</div>
                        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>decimal {topBet.odds_decimal}</div>
                      </div>
                    </div>
                    <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', lineHeight: 1.65, marginBottom: 12 }}>
                      {topBet.reasoning}
                    </div>
                    {topBet.key_stats && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
                        {topBet.key_stats.map((s, i) => (
                          <span key={i} style={{ fontSize: 11, color: '#4ade80', background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)', borderRadius: 6, padding: '4px 10px' }}>✓ {s}</span>
                        ))}
                      </div>
                    )}
                    {topBet.forecast_final && (
                      <div style={{ fontSize: 13, fontWeight: 800, color: '#fbbf24', textAlign: 'center', paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                        🏆 Forecast Final: {topBet.forecast_final}
                      </div>
                    )}
                  </div>
                </div>
              )}
              <Dashboard />
              <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 16px 24px' }}>
                <WcAnalysis data={wcData} hideBet={true} />

                {/* ⚔️ Round of 32 — BetBud Predictions */}
                <div style={{ marginBottom: 24 }}>
                  <div className="section-title">⚔️ Round of 32 — BetBud Predictions</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: 8 }}>
                    {[
                      { date:'Jun 28', time:'15:30', h:'🇿🇦 S.Africa', a:'🇨🇦 Canada',      pred:'1–2', fav:'Canada',      pct:[32,25,43] },
                      { date:'Jun 29', time:'13:30', h:'🇧🇷 Brazil',   a:'🇯🇵 Japan',       pred:'3–1', fav:'Brazil',      pct:[70,18,12] },
                      { date:'Jun 29', time:'17:00', h:'🇩🇪 Germany',  a:'🇵🇾 Paraguay',    pred:'2–0', fav:'Germany',     pct:[72,18,10] },
                      { date:'Jun 29', time:'21:30', h:'🇳🇱 Neth.',    a:'🇲🇦 Morocco',     pred:'2–1', fav:'Netherlands', pct:[58,22,20] },
                      { date:'Jun 30', time:'13:30', h:'🇨🇮 Iv.Coast', a:'🇳🇴 Norway',      pred:'1–2', fav:'Norway',      pct:[32,25,43] },
                      { date:'Jun 30', time:'17:30', h:'🇫🇷 France',   a:'🇸🇪 Sweden',      pred:'2–0', fav:'France',      pct:[72,18,10] },
                      { date:'Jun 30', time:'21:30', h:'🇲🇽 Mexico',   a:'🇪🇨 Ecuador',     pred:'2–1', fav:'Mexico',      pct:[55,22,23] },
                      { date:'Jul 1',  time:'12:30', h:'🏴󠁧󠁢󠁥󠁮󠁧󠁿 England',  a:'🇨🇩 DR Congo',    pred:'3–0', fav:'England',     pct:[78,14,8]  },
                      { date:'Jul 1',  time:'16:30', h:'🇧🇪 Belgium',  a:'🇸🇳 Senegal',     pred:'2–1', fav:'Belgium',     pct:[58,22,20] },
                      { date:'Jul 1',  time:'20:30', h:'🇺🇸 USA',      a:'🇧🇦 Bosnia',      pred:'2–0', fav:'USA',         pct:[65,20,15] },
                      { date:'Jul 2',  time:'15:30', h:'🇪🇸 Spain',    a:'🇦🇹 Austria',     pred:'2–0', fav:'Spain',       pct:[68,20,12] },
                      { date:'Jul 2',  time:'19:30', h:'🇵🇹 Portugal', a:'🇭🇷 Croatia',     pred:'2–1', fav:'Portugal',    pct:[58,22,20] },
                      { date:'Jul 2',  time:'23:30', h:'🇨🇭 Switz.',   a:'🇩🇿 Algeria',     pred:'2–1', fav:'Switzerland', pct:[60,22,18] },
                      { date:'Jul 3',  time:'14:30', h:'🇦🇺 Australia',a:'🇪🇬 Egypt',       pred:'1–1', fav:'Draw',        pct:[35,30,35] },
                      { date:'Jul 3',  time:'18:30', h:'🇦🇷 Argentina',a:'🇨🇻 C.Verde',     pred:'4–0', fav:'Argentina',   pct:[88,9,3]   },
                      { date:'Jul 3',  time:'22:00', h:'🇨🇴 Colombia', a:'🇬🇭 Ghana',       pred:'2–1', fav:'Colombia',    pct:[60,22,18] },
                    ].map((m, i) => (
                      <div key={i} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, padding: '10px 12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: 12, fontWeight: 700, color: 'rgba(255,255,255,0.5)' }}>{m.date} · {m.time} GMT</span>
                          <span style={{ fontSize: 18, fontWeight: 900, color: '#fbbf24' }}>{m.pred}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                          <span style={{ fontSize: 13, fontWeight: 600, color: 'white' }}>{m.h}</span>
                          <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>vs</span>
                          <span style={{ fontSize: 13, fontWeight: 600, color: 'white' }}>{m.a}</span>
                        </div>
                        <div style={{ marginTop: 6, display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'rgba(255,255,255,0.5)' }}>
                          <span>W {m.pct[0]}%</span>
                          <span style={{ color: '#4ade80', fontWeight: 700, fontSize: 11 }}>🤖 {m.fav}</span>
                          <span>L {m.pct[2]}%</span>
                        </div>
                        <div style={{ marginTop: 4, height: 3, borderRadius: 2, background: 'rgba(255,255,255,0.08)', display: 'flex', overflow: 'hidden' }}>
                          <div style={{ width: `${m.pct[0]}%`, background: '#38bdf8' }} />
                          <div style={{ width: `${m.pct[1]}%`, background: '#64748b' }} />
                          <div style={{ width: `${m.pct[2]}%`, background: '#f87171' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* ⚡ BetBud Quick Picks */}
                <div style={{ marginBottom: 8 }}>
                  <div className="section-title">⚡ BetBud Quick Picks</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 10 }}>
                    {[
                      { icon:'⚽', title:'Golden Boot',      name:'Mbappé',     sub:'🇫🇷 France · 7 goals pred.',         odds:'+350', live:'Messi 6⚽ 🇦🇷' },
                      { icon:'👟', title:'Most Assists',     name:'Bellingham', sub:'🏴󠁧󠁢󠁥󠁮󠁧󠁿 England · 5 assists pred.',     odds:'+600', live:'Mbappé 2🎯 🇫🇷' },
                      { icon:'🧤', title:'Most Clean Sheets',name:'Maignan',    sub:'🇫🇷 France · 5 CS pred.',            odds:'+450', live:'Maignan 2🧤 🇫🇷' },
                      { icon:'🎯', title:'Total Goals',      name:'285 pred.',  sub:'Avg 2.74/game across 104 matches',  odds:'—',    live:'82 played so far' },
                    ].map(p => (
                      <div key={p.title} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, padding: '14px 14px' }}>
                        <div style={{ fontSize: 20, marginBottom: 6 }}>{p.icon}</div>
                        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: 1 }}>{p.title}</div>
                        <div style={{ fontSize: 15, fontWeight: 800, color: 'white', margin: '4px 0 2px' }}>{p.name}</div>
                        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 8 }}>{p.sub}</div>
                        <div style={{ fontSize: 10, color: '#4ade80', fontWeight: 700, background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)', borderRadius: 6, padding: '3px 8px', display: 'inline-block' }}>
                          Live: {p.live}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )
        })()}
        {tab === 'today' && <Today liveFixtures={liveFixtures} />}
        {tab === 'groups' && <Groups liveData={liveGroups} />}
        {tab === 'fixtures' && <Fixtures liveFixtures={liveFixtures} />}
        {tab === 'bracket' && <Bracket />}
        {tab === 'scorers' && <Scorers />}
        {tab === 'assists' && <Assisters />}
        {tab === 'cleansheets' && <CleanSheets />}
        {tab === 'england' && <EnglandXI />}
        {tab === 'specials' && <Specials />}
        {tab === 'bets' && <Bets />}
      </main>

      <footer style={{
        background: '#1e293b',
        borderTop: '1px solid #334155',
        padding: '20px 24px',
        textAlign: 'center',
        color: '#64748b',
        fontSize: 12,
        marginTop: 48,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
          <div style={{
            width: 22, height: 22, borderRadius: 6,
            background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12,
            flexShrink: 0,
          }}>⚽</div>
          <strong style={{ color: '#f1f5f9' }}>BetBudWorldCup</strong>
          <span>· 2026 FIFA World Cup Predictor · Powered by API-Football &amp; Betfair Exchange</span>
        </div>
        <div>🤖 AI predictions for entertainment purposes only · Please gamble responsibly · 18+ · BeGambleAware.org</div>
      </footer>
    </div>
  )
}
