const BRACKET = {
  r32: [
    { home: '🇫🇷 France', away: '🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland', pred: '3-0', winner: 'France' },
    { home: '🇧🇷 Brazil', away: '🇲🇦 Morocco', pred: '2-0', winner: 'Brazil' },
    { home: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', away: '🇭🇷 Croatia', pred: '2-0', winner: 'England' },
    { home: '🇦🇷 Argentina', away: '🇦🇹 Austria', pred: '2-0', winner: 'Argentina' },
    { home: '🇪🇸 Spain', away: '🇺🇾 Uruguay', pred: '2-0', winner: 'Spain' },
    { home: '🇩🇪 Germany', away: '🇪🇨 Ecuador', pred: '3-1', winner: 'Germany' },
    { home: '🇵🇹 Portugal', away: '🇨🇴 Colombia', pred: '2-1', winner: 'Portugal' },
    { home: '🇳🇱 Netherlands', away: '🇯🇵 Japan', pred: '2-0', winner: 'Netherlands' },
    { home: '🇲🇽 Mexico', away: '🇰🇷 S. Korea', pred: '2-1', winner: 'Mexico' },
    { home: '🇨🇭 Switzerland', away: '🇨🇦 Canada', pred: '1-0', winner: 'Switzerland' },
    { home: '🇺🇸 USA', away: '🇹🇷 Türkiye', pred: '2-1', winner: 'USA' },
    { home: '🇳🇴 Norway', away: '🇸🇳 Senegal', pred: '2-0', winner: 'Norway' },
    { home: '🇧🇪 Belgium', away: '🇪🇬 Egypt', pred: '2-0', winner: 'Belgium' },
    { home: '🇨🇮 Ivory Coast', away: '🇮🇷 Iran', pred: '2-0', winner: 'Ivory Coast' },
    { home: '🇦🇺 Australia', away: '🇧🇦 Bosnia', pred: '1-0', winner: 'Australia' },
    { home: '🇺🇾 Uruguay', away: '🇸🇪 Sweden', pred: '1-1 (4-3p)', winner: 'Uruguay' },
  ],
  r16: [
    { home: '🇫🇷 France', away: '🇲🇽 Mexico', pred: '3-0', winner: 'France' },
    { home: '🇧🇷 Brazil', away: '🇺🇸 USA', pred: '2-1', winner: 'Brazil' },
    { home: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', away: '🇧🇪 Belgium', pred: '2-0', winner: 'England' },
    { home: '🇦🇷 Argentina', away: '🇨🇭 Switzerland', pred: '2-0', winner: 'Argentina' },
    { home: '🇪🇸 Spain', away: '🇦🇺 Australia', pred: '3-0', winner: 'Spain' },
    { home: '🇩🇪 Germany', away: '🇳🇴 Norway', pred: '2-1', winner: 'Germany' },
    { home: '🇵🇹 Portugal', away: '🇺🇾 Uruguay', pred: '2-1', winner: 'Portugal' },
    { home: '🇳🇱 Netherlands', away: '🇨🇮 Ivory Coast', pred: '2-0', winner: 'Netherlands' },
  ],
  qf: [
    { home: '🇫🇷 France', away: '🇧🇷 Brazil', pred: '2-1', winner: 'France' },
    { home: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', away: '🇦🇷 Argentina', pred: '1-0', winner: 'England' },
    { home: '🇪🇸 Spain', away: '🇩🇪 Germany', pred: '2-1', winner: 'Spain' },
    { home: '🇵🇹 Portugal', away: '🇳🇱 Netherlands', pred: '2-0', winner: 'Portugal' },
  ],
  sf: [
    { home: '🇫🇷 France', away: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', pred: '2-1 AET', winner: 'France' },
    { home: '🇪🇸 Spain', away: '🇵🇹 Portugal', pred: '1-1 (4-3p)', winner: 'Spain' },
  ],
  third: [
    { home: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', away: '🇵🇹 Portugal', pred: '2-1', winner: 'England' },
  ],
  final: [
    { home: '🇫🇷 France', away: '🇪🇸 Spain', pred: '2-1', winner: 'France' },
  ],
}

function MatchBox({ m, isWinner }) {
  const winTeam = m.winner
  return (
    <div style={{
      background: 'var(--card2)', border: `1px solid ${isWinner ? 'var(--gold)' : 'var(--border)'}`,
      borderRadius: 8, padding: '8px 10px', margin: '4px 2px', fontSize: 12, minWidth: 160,
    }}>
      <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 4 }}>🤖 {m.pred}</div>
      {[m.home, m.away].map((team, ti) => {
        const isW = team.includes(winTeam) || winTeam === team.split(' ').slice(-1)[0]
        return (
          <div key={ti} style={{
            display: 'flex', justifyContent: 'space-between',
            color: isW ? 'var(--gold)' : 'var(--muted)',
            fontWeight: isW ? 700 : 400, padding: '2px 0'
          }}>
            <span>{team}</span>
            {isW && <span style={{ color: 'var(--accent)', fontSize: 10 }}>✓</span>}
          </div>
        )
      })}
    </div>
  )
}

function Round({ title, matches, highlight }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minWidth: 175, flex: '0 0 auto' }}>
      <div style={{
        textAlign: 'center', color: highlight ? 'var(--gold)' : 'var(--muted)',
        fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1,
        padding: '8px 4px', borderBottom: '1px solid var(--border)', marginBottom: 8
      }}>
        {title}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, justifyContent: 'space-around', flex: 1 }}>
        {matches.map((m, i) => (
          <MatchBox key={i} m={m} isWinner={title === '🏆 FINAL'} />
        ))}
      </div>
    </div>
  )
}

export default function Bracket() {
  return (
    <div className="page-content">
      <div className="section-title">🏅 BetBud Knockout Bracket Prediction</div>

      <div style={{ padding: '10px 14px', background: 'var(--card2)', border: '1px solid var(--border)', borderRadius: 8, marginBottom: 20, fontSize: 13, color: 'var(--muted)' }}>
        🤖 BetBud predicted path based on squad ratings, form, draw bracket analysis, and historical head-to-head data.
        Predictions update automatically as tournament progresses.
      </div>

      {/* Winner highlight */}
      <div style={{
        display: 'flex', justifyContent: 'center', marginBottom: 24
      }}>
        <div style={{
          background: 'linear-gradient(135deg,#1e293b,#312e81)',
          border: '2px solid var(--purple)', borderRadius: 12, padding: '16px 32px',
          textAlign: 'center', maxWidth: 280
        }}>
          <div style={{ fontSize: 40 }}>🏆</div>
          <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>BetBud Champion</div>
          <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--gold)' }}>🇫🇷 France</div>
          <div style={{ fontSize: 13, color: 'var(--muted)' }}>Pred. score: 2-1 vs 🇪🇸 Spain</div>
        </div>
      </div>

      <div style={{ overflowX: 'auto', paddingBottom: 16 }}>
        <div style={{ display: 'flex', gap: 0, minWidth: 1100, alignItems: 'flex-start' }}>
          <Round title="Round of 32" matches={BRACKET.r32} />
          <Round title="Round of 16" matches={BRACKET.r16} />
          <Round title="Quarter-Finals" matches={BRACKET.qf} />
          <Round title="Semi-Finals" matches={BRACKET.sf} />
          <Round title="🏆 Final" matches={BRACKET.final} highlight />
          <Round title="3rd Place" matches={BRACKET.third} />
        </div>
      </div>

      {/* Bracket analysis */}
      <div className="section" style={{ marginTop: 24 }}>
        <div className="section-title">📊 Bracket Analysis</div>
        <div className="grid-2">
          {[
            { team: '🇫🇷 France', path: 'Iraq → Scotland → Mexico → Brazil → England → Spain', difficulty: 'Medium', conf: 68 },
            { team: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', path: 'Panama → Ghana → Croatia → Belgium → Argentina → France', difficulty: 'Hard', conf: 56 },
            { team: '🇪🇸 Spain', path: 'Cape Verde → Saudi Arabia → Uruguay → Australia → Germany → Portugal', difficulty: 'Medium', conf: 62 },
            { team: '🇦🇷 Argentina', path: 'Algeria → Jordan → Austria → Switzerland → England (SF loss)', difficulty: 'Medium', conf: 45 },
          ].map(a => (
            <div key={a.team} className="card-sm">
              <div style={{ fontWeight: 700, fontSize: 15 }}>{a.team}</div>
              <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>Path: {a.path}</div>
              <div style={{ display: 'flex', gap: 12, marginTop: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 12 }}>Bracket difficulty: <strong style={{ color: a.difficulty === 'Hard' ? 'var(--red)' : a.difficulty === 'Medium' ? 'var(--gold)' : 'var(--accent)' }}>{a.difficulty}</strong></span>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>Win conf: <strong style={{ color: 'var(--accent)' }}>{a.conf}%</strong></span>
              </div>
              <div className="conf-bar" style={{ marginTop: 6 }}>
                <div className="conf-fill" style={{ width: `${a.conf}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
