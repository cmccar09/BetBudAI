import { DEMO_FIXTURES, FixtureCard } from './Fixtures'

export default function Today({ liveFixtures }) {
  const fixtures = liveFixtures?.length ? liveFixtures : DEMO_FIXTURES

  // Use US Eastern time (UTC-4) — World Cup runs until ~midnight EDT so late
  // games that roll past midnight UTC should still count as "today"
  const usEastern = new Date(Date.now() - 4 * 60 * 60 * 1000)
  const todayStr = usEastern.toISOString().slice(0, 10)
  // Only consider non-finished fixtures from today onwards
  const upcoming = fixtures.filter(f => f.status !== 'FT' && f.date >= todayStr)
  const dates = [...new Set(upcoming.map(f => f.date).filter(Boolean))].sort()

  // Show today's matches if any, otherwise the next upcoming matchday
  let targetDate = dates.find(d => d === todayStr)
  if (!targetDate) targetDate = dates.find(d => d >= todayStr) || dates[0]

  const todaysFixtures = upcoming.filter(f => f.date === targetDate)
  const isToday = targetDate === todayStr

  return (
    <div className="page-content">
      <div className="section-title">🔮 Daily Predictions</div>
      <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>
        🤖 BetBud AI score, BTTS and Over/Under 2.5 predictions for {isToday ? "today's" : 'the next'} matches.
      </div>

      <div className="card">
        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--gold)', padding: '8px 0 4px', textTransform: 'uppercase', letterSpacing: 1 }}>
          📆 {isToday ? 'Today' : 'Next Matchday'} — {targetDate}
        </div>
        {todaysFixtures.length
          ? todaysFixtures.map(f => <FixtureCard key={f.id} f={f} detailed />)
          : <div style={{ textAlign: 'center', padding: 32, color: 'var(--muted)' }}>No matches scheduled.</div>
        }
      </div>
    </div>
  )
}
