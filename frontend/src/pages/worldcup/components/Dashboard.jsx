import { GROUPS } from '../data/groups'
import { useState, useEffect } from 'react'

function ConfBar({ pct, width = 160 }) {
  return (
    <div className="conf-bar" style={{ maxWidth: width, width: '100%' }}>
      <div className="conf-fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

function StatCard({ icon, title, name, sub, odds, liveCount, liveLabel, liveLeader, liveLeaderFlag }) {
  return (
    <div className="card" style={{ textAlign: 'center', position: 'relative' }}>
      <div className="card-title" style={{ justifyContent: 'center' }}>{icon} {title}</div>

      {/* Live leader highlight */}
      {liveLeader && (
        <div style={{ background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)', borderRadius: 8, padding: '8px 10px', margin: '6px 0 8px' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: '#6ee7b7', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
            LIVE LEADER
          </div>
          <div style={{ fontSize: 17, fontWeight: 900, color: '#4ade80' }}>
            {liveLeaderFlag} {liveLeader}
          </div>
          {liveCount !== undefined && (
            <div style={{ fontSize: 28, fontWeight: 900, color: 'white', lineHeight: 1, marginTop: 2 }}>
              {liveCount}
              <span style={{ fontSize: 13, color: '#6ee7b7', fontWeight: 600, marginLeft: 4 }}>{liveLabel}</span>
            </div>
          )}
        </div>
      )}

      <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
        <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 10 }}>Pred: </span>{name}
      </div>
      <div style={{ color: 'var(--muted)', fontSize: 11, marginTop: 2 }}>{sub}</div>
      {odds && <div style={{ fontSize: 11, marginTop: 6 }}>Odds: <span className="odds-pill">{odds}</span></div>}
    </div>
  )
}

function GroupWinnerCard({ letter, data }) {
  const won = data.predWon !== false  // default true unless explicitly false
  const winner = data.actualWinner || data.predWinner
  const runner = data.actualRunner || data.predRunner
  const winnerTeam = data.teams.find(t => t.name === winner) || data.teams[0]
  const predTeam = data.teams.find(t => t.name === data.predWinner)

  return (
    <div className="card-sm" style={{
      textAlign: 'center', padding: 14,
      border: `1px solid ${won ? 'rgba(74,222,128,0.3)' : 'rgba(248,113,113,0.3)'}`,
      background: won ? 'rgba(74,222,128,0.04)' : 'rgba(248,113,113,0.04)'
    }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--muted)', marginBottom: 4, letterSpacing: 1 }}>GROUP {letter}</div>
      <div style={{ fontSize: 24 }}>{winnerTeam.flag}</div>
      <div style={{ fontWeight: 700, fontSize: 14, marginTop: 4, color: won ? '#4ade80' : 'white' }}>{winner}</div>
      <div style={{ fontSize: 11, color: 'var(--muted)' }}>2nd: {runner}</div>
      {won ? (
        <span style={{ display: 'inline-block', marginTop: 6, fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 6, background: 'rgba(74,222,128,0.15)', color: '#4ade80' }}>
          ✅ CORRECT
        </span>
      ) : (
        <div style={{ marginTop: 6 }}>
          <span style={{ display: 'inline-block', fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 6, background: 'rgba(248,113,113,0.15)', color: '#f87171' }}>
            ❌ WRONG
          </span>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 3 }}>
            Pred: {predTeam?.flag} {data.predWinner}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 640)
  useEffect(() => {
    const fn = () => setIsMobile(window.innerWidth < 640)
    window.addEventListener('resize', fn)
    return () => window.removeEventListener('resize', fn)
  }, [])

  return (
    <div className="page-content">
      {/* Champion prediction — horizontal podium + live stats */}
      <div style={{
        background: 'linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%)',
        border: '1px solid rgba(139,92,246,0.4)', borderRadius: 16,
        padding: '18px 20px', marginBottom: 24, overflow: 'hidden', position: 'relative'
      }}>
        <div style={{ position:'absolute', top:'-40px', left:'50%', transform:'translateX(-50%)', width:300, height:300, background:'radial-gradient(circle,rgba(250,204,21,0.07) 0%,transparent 70%)', pointerEvents:'none' }} />

        <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(139,92,246,0.8)', textTransform: 'uppercase', letterSpacing: 2, textAlign: 'center', marginBottom: 14 }}>
          🤖 BetBud Predicts — 2026 FIFA World Cup
        </div>

        {/* Outer wrapper: stats left | podium centre | stats right — stacks on mobile */}
        <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 12, alignItems: isMobile ? 'stretch' : 'flex-end' }}>

          {/* LEFT STATS — Golden Boot + Assists */}
          <div style={{ flexShrink: 0, width: isMobile ? '100%' : 145, display: 'flex', flexDirection: isMobile ? 'row' : 'column', gap: 8, paddingBottom: isMobile ? 0 : 3 }}>
            <div style={{ background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.22)', borderRadius: 10, padding: '10px 12px' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>⚽ Golden Boot</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 22 }}>🇦🇷</span>
                <div>
                  <div style={{ fontWeight: 900, fontSize: 14, color: '#4ade80' }}>Messi</div>
                  <div style={{ fontSize: 11, color: '#fbbf24', fontWeight: 700 }}>8 goals 🥇</div>
                </div>
              </div>
              <div style={{ fontSize: 10, color: '#64748b', marginTop: 4 }}>Leads via assists · Mbappé (8, out)</div>
            </div>
            <div style={{ background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.2)', borderRadius: 10, padding: '10px 12px' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>👟 Most Assists</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 22 }}>🇦🇷</span>
                <div>
                  <div style={{ fontWeight: 900, fontSize: 14, color: '#4ade80' }}>Messi</div>
                  <div style={{ fontSize: 11, color: '#38bdf8', fontWeight: 700 }}>4 assists 🏆</div>
                </div>
              </div>
              <div style={{ fontSize: 10, color: '#64748b', marginTop: 4 }}>2 vs England · all-time WC record</div>
            </div>
          </div>

          {/* CENTRE PODIUM */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1.8fr 1fr' : '1fr 1.6fr 1fr 1fr', gap: 0, alignItems: 'flex-end' }}>
              <div style={{ textAlign: 'center', paddingBottom: 4 }}>
                <div style={{ fontSize: 26, marginBottom: 3 }}>🇫🇷</div>
                <div style={{ fontWeight: 800, fontSize: 13, color: '#9ca3af' }}>France</div>
                <div style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px 6px 0 0', marginTop: 6, padding: '7px 4px 4px', display: 'flex', flexDirection: 'column', alignItems: 'center', height: 50 }}>
                  <div style={{ fontSize: 17 }}>🥉</div>
                  <div style={{ fontSize: 9, color: '#6b7280', marginTop: 2 }}>3rd Place</div>
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 40, marginBottom: 3 }}>🇪🇸</div>
                <div style={{ fontWeight: 900, fontSize: 20, color: '#fbbf24' }}>Spain</div>
                <div style={{ fontSize: 11, color: '#4ade80', marginTop: 1, fontWeight: 700 }}>✅ BetBud Pick WON · ~2/1</div>
                <div style={{ background: 'linear-gradient(180deg,rgba(250,204,21,0.28),rgba(250,204,21,0.10))', border: '1px solid rgba(250,204,21,0.5)', borderRadius: '6px 6px 0 0', marginTop: 6, padding: '10px 4px 4px', display: 'flex', flexDirection: 'column', alignItems: 'center', height: 76 }}>
                  <div style={{ fontSize: 24 }}>🏆</div>
                  <div style={{ fontSize: 10, color: '#fbbf24', fontWeight: 800, marginTop: 2 }}>CHAMPIONS</div>
                </div>
              </div>
              <div style={{ textAlign: 'center', paddingBottom: 4 }}>
                <div style={{ fontSize: 26, marginBottom: 3 }}>🇦🇷</div>
                <div style={{ fontWeight: 800, fontSize: 13, color: '#e2e8f0' }}>Argentina</div>
                <div style={{ background: 'rgba(226,232,240,0.07)', border: '1px solid rgba(226,232,240,0.15)', borderRadius: '6px 6px 0 0', marginTop: 6, padding: '7px 4px 4px', display: 'flex', flexDirection: 'column', alignItems: 'center', height: 62 }}>
                  <div style={{ fontSize: 18 }}>🥈</div>
                  <div style={{ fontSize: 9, color: '#9ca3af', marginTop: 2 }}>Finalist</div>
                </div>
              </div>
              {!isMobile && (
              <div style={{ textAlign: 'center', paddingBottom: 4 }}>
                <div style={{ fontSize: 24, marginBottom: 3 }}>🏴󠁧󠁢󠁥󠁮󠁧󠁿</div>
                <div style={{ fontWeight: 700, fontSize: 12, color: '#6b7280' }}>England</div>
                <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px 6px 0 0', marginTop: 6, padding: '5px 4px 4px', display: 'flex', flexDirection: 'column', alignItems: 'center', height: 42 }}>
                  <div style={{ fontSize: 13 }}>4️⃣</div>
                  <div style={{ fontSize: 9, color: '#4b5563', marginTop: 1 }}>4th</div>
                </div>
              </div>
              )}
            </div>
            <div style={{ height: 3, background: 'linear-gradient(90deg,transparent,rgba(139,92,246,0.5),rgba(250,204,21,0.7),rgba(139,92,246,0.5),transparent)', borderRadius: 2 }} />
          </div>

          {/* RIGHT STATS — Clean Sheets + Top scorer race */}
          <div style={{ flexShrink: 0, width: isMobile ? '100%' : 145, display: 'flex', flexDirection: isMobile ? 'row' : 'column', gap: 8, paddingBottom: isMobile ? 0 : 3 }}>
            <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.22)', borderRadius: 10, padding: '10px 12px' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#6ee7b7', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>🧤 Clean Sheets</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 22 }}>🇪🇸</span>
                <div>
                  <div style={{ fontWeight: 900, fontSize: 14, color: '#4ade80' }}>Simón</div>
                  <div style={{ fontSize: 11, color: '#6ee7b7', fontWeight: 700 }}>4 CS 🏆 record</div>
                </div>
              </div>
              <div style={{ fontSize: 10, color: '#64748b', marginTop: 4 }}>Spain unbeaten · WC record</div>
            </div>
            <div style={{ background: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.22)', borderRadius: 10, padding: '10px 12px' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#c4b5fd', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>⚽ Semi-Finals → Final</div>
              <div style={{ fontSize: 12, fontWeight: 800, color: 'white', lineHeight: 1.4 }}>Spain 2-0 France · Arg 2-1 England</div>
              <div style={{ fontSize: 12, fontWeight: 800, color: '#4ade80', lineHeight: 1.4 }}>🏆 Final: Spain 1-0 Argentina (AET)</div>
              <div style={{ fontSize: 10, color: '#4ade80', marginTop: 3, fontWeight: 700 }}>Ferran Torres 106' · BetBud ✅</div>
            </div>
          </div>

        </div>

        <div style={{ textAlign: 'center', marginTop: 10, fontSize: 10, color: '#374151' }}>
          Model: Form · Squad depth · Bracket draw · Last 16 results · Updated daily
        </div>
      </div>


    </div>
  )
}
