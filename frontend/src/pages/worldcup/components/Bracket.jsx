const BRACKET = {
  r16: [
    { home: '🇫🇷 France',    away: '🇵🇾 Paraguay',    pred: '1-0',       winner: 'France',    hS:1, aS:0 },
    { home: '🇲🇦 Morocco',   away: '🇨🇦 Canada',      pred: '3-0',       winner: 'Morocco',   hS:3, aS:0 },
    { home: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England',  away: '🇲🇽 Mexico',     pred: '3-2',       winner: 'England',   hS:3, aS:2 },
    { home: '🇳🇴 Norway',    away: '🇧🇷 Brazil',      pred: '2-1 ⚡',    winner: 'Norway',    hS:2, aS:1 },
    { home: '🇪🇸 Spain',     away: '🇵🇹 Portugal',    pred: '1-0',       winner: 'Spain',     hS:1, aS:0 },
    { home: '🇧🇪 Belgium',   away: '🇺🇸 USA',         pred: '4-1',       winner: 'Belgium',   hS:4, aS:1 },
    { home: '🇦🇷 Argentina', away: '🇪🇬 Egypt',       pred: '3-2',       winner: 'Argentina', hS:3, aS:2 },
    { home: '🇨🇭 Switzerland',away: '🇨🇴 Colombia',   pred: '0-0 (pens)',winner: 'Switzerland',hS:0,aS:0 },
  ],
  qf: [
    { home: '🇫🇷 France',    away: '🇲🇦 Morocco',    pred: '2-0', winner: 'France',    hS:2, aS:0 },
    { home: '🇪🇸 Spain',     away: '🇧🇪 Belgium',    pred: '2-1', winner: 'Spain',     hS:2, aS:1 },
    { home: '🇳🇴 Norway',    away: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', pred: '1-2', winner: 'England',   hS:1, aS:2 },
    { home: '🇦🇷 Argentina', away: '🇨🇭 Switzerland',pred: '3-1', winner: 'Argentina', hS:3, aS:1 },
  ],
  sf: [
    { home: '🇫🇷 France',   away: '🇪🇸 Spain',     pred: '0-2 ❌', winner: 'Spain',     hS:0, aS:2 },
    { home: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', away: '🇦🇷 Argentina', pred: '1-2 ✅', winner: 'Argentina', hS:1, aS:2 },
  ],
  third: [
    { home: '🇫🇷 France',   away: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', pred: '6-4 AET', winner: 'England', hS: 4, aS: 6 },
  ],
  final: [
    { home: '🇪🇸 Spain', away: '🇦🇷 Argentina', pred: 'Spain to win · TODAY 3pm ET', winner: 'Spain' },
  ],
}

function MatchBox({ m, isWinner }) {
  const winTeam = m.winner
  const hasResult = m.hS !== undefined && m.hS !== null
  return (
    <div style={{
      background: 'var(--card2)', border: `1px solid ${isWinner ? 'var(--gold)' : 'var(--border)'}`,
      borderRadius: 8, padding: '8px 10px', margin: '4px 2px', fontSize: 12, minWidth: 160,
    }}>
      {hasResult
        ? <div style={{ fontSize: 10, color: 'var(--accent)', marginBottom: 4, fontWeight: 700 }}>
            FT {m.hS}–{m.aS}
          </div>
        : <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 4 }}>🤖 {m.pred}</div>
      }
      {[m.home, m.away].map((team, ti) => {
        const isW = hasResult && (team.includes(winTeam) || winTeam === team.split(' ').slice(-1)[0])
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
      <div className="section-title">🏅 BetBud Knockout Bracket</div>

      <div style={{ padding: '10px 14px', background: 'var(--card2)', border: '1px solid var(--border)', borderRadius: 8, marginBottom: 20, fontSize: 13, color: 'var(--muted)' }}>
        🤖 BetBud path — SF1: Spain 2-0 France ❌ · SF2: Argentina 2-1 England ✅ · 3rd: England 6-4 France (AET) ❌ · <span style={{ color: '#fbbf24', fontWeight: 700 }}>FINAL TODAY · Spain vs Argentina · 3pm ET</span>
      </div>

      {/* Winner highlight */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
        <div style={{
          background: 'linear-gradient(135deg,#1e293b,#312e81)',
          border: '2px solid var(--purple)', borderRadius: 12, padding: '16px 32px',
          textAlign: 'center', maxWidth: 280
        }}>
          <div style={{ fontSize: 40 }}>🏆</div>
          <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>BetBud Champion</div>
          <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--gold)' }}>🇪🇸 Spain</div>
          <div style={{ fontSize: 13, color: '#fbbf24', fontWeight: 700 }}>FINAL TODAY · vs 🇦🇷 Argentina · 3pm ET</div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 4 }}>SF1: Spain 2-0 France ❌ · SF2: Argentina 2-1 England ✅ · 3rd: England 6-4 France ❌</div>
        </div>
      </div>

      <div style={{ overflowX: 'auto', paddingBottom: 16 }}>
        <div style={{ display: 'flex', gap: 0, minWidth: 900, alignItems: 'flex-start' }}>
          <Round title="Last 16" matches={BRACKET.r16} />
          <Round title="Quarter-Finals" matches={BRACKET.qf} />
          <Round title="Semi-Finals" matches={BRACKET.sf} />
          <Round title="🏆 Final" matches={BRACKET.final} highlight />
          <Round title="3rd Place" matches={BRACKET.third} />
        </div>
      </div>

      {/* Bracket analysis */}
      <div className="section" style={{ marginTop: 24 }}>
        <div className="section-title">📊 Final & Semi-Final 2 Analysis</div>
        <div className="grid-2">
          {[
            { team: '🇪🇸 Spain', path: 'Portugal → Belgium → France 2-0 (SF ✅) → Final Jul 19', difficulty: 'Medium', conf: 72, note: 'SF: 2-0 France. Oyarzabal pen + Porro. Yamal unstoppable.' },
            { team: '🇦🇷 Argentina', path: 'Egypt → Switzerland → England 2-1 (SF ✅) → Final Jul 19', difficulty: 'Hard', conf: 58, note: 'SF: 2-1 England. Enzo 85\' + Lautaro 92\'. Messi 2 assists.' },
            { team: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 England', path: 'Mexico → Norway → Argentina 1-2 (SF ❌) → 3rd Place WON 6-4 AET', difficulty: 'Hard', conf: 0, note: '3rd place ✅. Came back from SF defeat. Kane 6 goals. Brilliant 6-4 AET win.' },
            { team: '🇫🇷 France', path: 'Paraguay → Morocco → Spain 0-2 (SF ❌) → 3rd Place LOST 4-6 AET', difficulty: 'Hard', conf: 0, note: 'Finished 4th. Lost 3rd place 4-6 AET to England. Mbappé 8 goals, tournament over.' },
          ].map(a => (
            <div key={a.team} className="card-sm">
              <div style={{ fontWeight: 700, fontSize: 15 }}>{a.team}</div>
              <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>Path: {a.path}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 3 }}>{a.note}</div>
              <div style={{ display: 'flex', gap: 12, marginTop: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 12 }}>Difficulty: <strong style={{ color: a.difficulty === 'Hard' ? 'var(--red)' : 'var(--gold)' }}>{a.difficulty}</strong></span>
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
