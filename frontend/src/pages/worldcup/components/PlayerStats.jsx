import { SCORERS, ASSISTS, CLEANSHEETS, GOLDEN_BOOT_LIVE, GOLDEN_ASSIST_LIVE } from '../data/players'

function ConfDots({ pct, n = 5 }) {
  const filled = Math.round(pct / 100 * n)
  return (
    <span style={{ display: 'inline-flex', gap: 3 }}>
      {Array.from({ length: n }, (_, i) => (
        <span key={i} style={{ width: 8, height: 8, borderRadius: '50%', background: i < filled ? 'var(--gold)' : 'var(--border)' }} />
      ))}
    </span>
  )
}

function LiveTable({ data, valueKey, valueLabel, secondKey, secondLabel, title, icon }) {
  return (
    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, padding: '12px 14px', marginBottom: 20 }}>
      <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--gold)', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444', boxShadow: '0 0 6px #ef4444', display: 'inline-block', animation: 'pulse 2s infinite' }} />
        {icon} LIVE — {title}
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <th style={{ textAlign: 'left', padding: '4px 6px', color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 600 }}>#</th>
            <th style={{ textAlign: 'left', padding: '4px 6px', color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 600 }}>Player</th>
            <th style={{ textAlign: 'center', padding: '4px 6px', color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 600 }}>{valueLabel}</th>
            <th style={{ textAlign: 'center', padding: '4px 6px', color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 600 }}>{secondLabel}</th>
            <th style={{ textAlign: 'center', padding: '4px 6px', color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 600 }}>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((p, i) => (
            <tr key={p.name} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: i < 3 ? 'rgba(251,191,36,0.04)' : 'transparent' }}>
              <td style={{ padding: '7px 6px', color: i === 0 ? '#fbbf24' : i === 1 ? '#d1d5db' : i === 2 ? '#92400e' : 'rgba(255,255,255,0.5)', fontWeight: 700, fontSize: 14 }}>
                {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}`}
              </td>
              <td style={{ padding: '7px 6px' }}>
                <span style={{ marginRight: 6 }}>{p.flag}</span>
                <span style={{ fontWeight: 600, color: 'white' }}>{p.name}</span>
                <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginLeft: 6 }}>{p.team}</span>
              </td>
              <td style={{ padding: '7px 6px', textAlign: 'center', fontWeight: 900, fontSize: 16, color: 'var(--accent)' }}>{p[valueKey]}</td>
              <td style={{ padding: '7px 6px', textAlign: 'center', color: 'rgba(255,255,255,0.6)', fontSize: 13 }}>{p[secondKey]}</td>
              <td style={{ padding: '7px 6px', textAlign: 'center' }}>
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 6,
                  background: p.status === 'OUT' ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)',
                  color: p.status === 'OUT' ? '#f87171' : '#6ee7b7'
                }}>
                  {p.status === 'OUT' ? '❌ Out' : '✅ R32'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 8, textAlign: 'right' }}>Updated: 28 Jun 2026 · Source: FIFA / Yahoo Sports</div>
    </div>
  )
}

function PlayerCard({ p, statKey, statLabel, actualKey, actualAssistKey }) {
  const tagColors = { hot: { bg: '#7f1d1d', fg: '#fca5a5' }, value: { bg: '#14532d', fg: '#86efac' }, tip: { bg: '#1e3a5f', fg: '#93c5fd' } }
  const tc = tagColors[p.tag] || tagColors.tip
  const actual = p[actualKey] ?? null
  const actualAssists = p[actualAssistKey] ?? null
  const predicted = p[statKey]
  const pct = actual !== null ? Math.min(100, Math.round(actual / predicted * 100)) : null

  return (
    <div className="card" style={{ textAlign: 'center', position: 'relative' }}>
      {p.tag && (
        <span style={{ position: 'absolute', top: 10, right: 10, background: tc.bg, color: tc.fg, fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 8 }}>
          {p.tag.toUpperCase()}
        </span>
      )}
      <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--gold)' }}>#{p.rank}</div>
      <div style={{ fontSize: 40, marginTop: 4 }}>{p.flag}</div>
      <div style={{ fontSize: 16, fontWeight: 700, marginTop: 6 }}>{p.name}</div>
      <div style={{ color: 'var(--muted)', fontSize: 12 }}>{p.club}</div>

      {/* Actual vs Predicted */}
      <div style={{ margin: '12px 0 4px', display: 'flex', justifyContent: 'center', gap: 20, alignItems: 'flex-end' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: actual !== null ? 38 : 30, fontWeight: 900, color: actual !== null ? '#4ade80' : 'var(--accent)', lineHeight: 1 }}>
            {actual !== null ? actual : predicted}
          </div>
          <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>{actual !== null ? `Actual ${statLabel}` : `Pred. ${statLabel}`}</div>
        </div>
        {actual !== null && (
          <div style={{ textAlign: 'center', opacity: 0.6 }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--muted)', lineHeight: 1 }}>{predicted}</div>
            <div style={{ fontSize: 10, color: 'var(--muted)', marginTop: 2 }}>Predicted</div>
          </div>
        )}
      </div>

      {/* Assists counter */}
      {actualAssists !== null && (
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>
          {actualAssists} assist{actualAssists !== 1 ? 's' : ''} so far
        </div>
      )}

      {/* Progress vs prediction */}
      {pct !== null && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ height: 4, background: 'rgba(255,255,255,0.1)', borderRadius: 2, overflow: 'hidden', margin: '4px 0' }}>
            <div style={{ height: '100%', width: `${pct}%`, background: pct >= 100 ? '#4ade80' : pct >= 60 ? '#fbbf24' : '#94a3b8', borderRadius: 2, transition: 'width 0.6s' }} />
          </div>
          <div style={{ fontSize: 10, color: 'var(--muted)' }}>{pct}% of prediction reached</div>
        </div>
      )}

      <div className="rating-pill" style={{ display: 'inline-flex', margin: '6px auto' }}>⭐ {p.rating} Rating</div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 12, padding: '0 4px', alignItems: 'center' }}>
        <span style={{ color: 'var(--muted)' }}>Confidence:</span>
        <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{p.confidence}%</span>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
        <ConfDots pct={p.confidence} />
      </div>
      <div className="conf-bar" style={{ marginTop: 8 }}>
        <div className="conf-fill" style={{ width: `${p.confidence}%` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontSize: 12, padding: '0 4px', alignItems: 'center' }}>
        <span style={{ color: 'var(--muted)' }}>Betfair odds:</span>
        <span className="odds-pill">{p.odds}</span>
      </div>
      {p.analysis && (
        <div style={{ marginTop: 12, fontSize: 11, color: 'var(--muted)', textAlign: 'left', background: 'var(--dark)', borderRadius: 6, padding: '8px 10px', lineHeight: 1.5 }}>
          {p.analysis}
        </div>
      )}
    </div>
  )
}

export function Scorers() {
  return (
    <div className="page-content">
      <div className="section-title">⚽ Golden Boot — Top Goalscorers</div>
      <LiveTable
        data={GOLDEN_BOOT_LIVE}
        valueKey="goals" valueLabel="Goals"
        secondKey="assists" secondLabel="Assists"
        title="Golden Boot Race" icon="⚽"
      />
      <div style={{ fontSize: 13, fontWeight: 700, color: 'rgba(255,255,255,0.7)', margin: '20px 0 10px', textTransform: 'uppercase', letterSpacing: 1 }}>
        BetBud Pre-Tournament Predictions vs Actual
      </div>
      <div className="grid-3">
        {SCORERS.map(p => (
          <PlayerCard key={p.name} p={p} statKey="predGoals" statLabel="Goals" actualKey="actualGoals" actualAssistKey="actualAssists" />
        ))}
      </div>
    </div>
  )
}

export function Assisters() {
  return (
    <div className="page-content">
      <div className="section-title">👟 Golden Assist — Top Playmakers</div>
      <LiveTable
        data={GOLDEN_ASSIST_LIVE}
        valueKey="assists" valueLabel="Assists"
        secondKey="goals" secondLabel="Goals"
        title="Golden Assist Race" icon="👟"
      />
      <div style={{ fontSize: 13, fontWeight: 700, color: 'rgba(255,255,255,0.7)', margin: '20px 0 10px', textTransform: 'uppercase', letterSpacing: 1 }}>
        BetBud Pre-Tournament Predictions vs Actual
      </div>
      <div className="grid-3">
        {ASSISTS.map(p => (
          <PlayerCard key={p.name} p={p} statKey="predAssists" statLabel="Assists" actualKey="actualAssists" actualAssistKey="actualGoals" />
        ))}
      </div>
    </div>
  )
}

export function CleanSheets() {
  return (
    <div className="page-content">
      <div className="section-title">🧤 Clean Sheets — Goalkeeper Rankings</div>
      <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, padding: '12px 14px', marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--gold)', marginBottom: 10 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444', display: 'inline-block', marginRight: 6 }} />
          🧤 LIVE — Clean Sheet Leaders
        </div>
        {CLEANSHEETS.map((p, i) => (
          <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <span style={{ fontWeight: 700, color: i === 0 ? '#fbbf24' : 'rgba(255,255,255,0.5)', width: 24, textAlign: 'center' }}>
              {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i+1}`}
            </span>
            <span style={{ fontSize: 18 }}>{p.flag}</span>
            <span style={{ flex: 1, fontWeight: 600 }}>{p.name}</span>
            <span style={{ fontSize: 22, fontWeight: 900, color: 'var(--accent)', minWidth: 30, textAlign: 'center' }}>{p.actualCS}</span>
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>/{p.predCS} pred</span>
          </div>
        ))}
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 8, textAlign: 'right' }}>Updated: 28 Jun 2026</div>
      </div>
      <div style={{ fontSize: 13, fontWeight: 700, color: 'rgba(255,255,255,0.7)', margin: '20px 0 10px', textTransform: 'uppercase', letterSpacing: 1 }}>
        BetBud Pre-Tournament Predictions vs Actual
      </div>
      <div className="grid-3">
        {CLEANSHEETS.map(p => (
          <PlayerCard key={p.name} p={p} statKey="predCS" statLabel="Clean Sheets" actualKey="actualCS" actualAssistKey={null} />
        ))}
      </div>
    </div>
  )
}
