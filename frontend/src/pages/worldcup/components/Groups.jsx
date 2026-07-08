import { GROUPS } from '../data/groups'

function FormDots({ form = '' }) {
  return (
    <span style={{ display: 'inline-flex', gap: 1 }}>
      {form.split('').map((c, i) => (
        <span key={i} className={`form-dot form-${c}`} style={{ width: 6, height: 6 }} />
      ))}
    </span>
  )
}

function GroupTable({ letter, data }) {
  const sorted = [...data.teams].sort((a, b) => {
    if (b.pts !== a.pts) return b.pts - a.pts
    return (b.gf - b.ga) - (a.gf - a.ga)
  })

  return (
    <div className="card" style={{ padding: 10 }}>
      <div className="card-title" style={{ justifyContent: 'space-between', marginBottom: 6, fontSize: 12 }}>
        <span>Group {letter}</span>
        <span className="badge badge-pred" style={{ fontSize: 10, padding: '2px 6px' }}>Winner: {data.predWinner}</span>
      </div>

      <table className="table" style={{ fontSize: 11, width: '100%' }}>
        <thead>
          <tr>
            <th style={{ width: 18, padding: '4px 4px' }}>#</th>
            <th style={{ padding: '4px 4px' }}>Team</th>
            <th style={{ padding: '4px 4px', textAlign: 'center' }}>P</th>
            <th style={{ padding: '4px 4px', textAlign: 'center' }}>W</th>
            <th style={{ padding: '4px 4px', textAlign: 'center' }}>D</th>
            <th style={{ padding: '4px 4px', textAlign: 'center' }}>L</th>
            <th style={{ padding: '4px 4px', textAlign: 'center' }}>GD</th>
            <th style={{ padding: '4px 4px', textAlign: 'center' }}>Pts</th>
            <th style={{ padding: '4px 4px' }}>Form</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((t, i) => (
            <tr key={t.name} style={{
              borderLeft: i < 2 ? `3px solid ${i === 0 ? 'var(--accent)' : 'var(--gold)'}` : 'none',
            }}>
              <td style={{
                padding: '4px 4px',
                color: i === 0 ? 'var(--accent)' : i === 1 ? 'var(--gold)' : 'var(--muted)',
                fontWeight: 700
              }}>{i + 1}</td>
              <td style={{ padding: '4px 4px', whiteSpace: 'nowrap' }}>
                <span style={{ marginRight: 4 }}>{t.flag}</span>
                <span style={{ fontWeight: i < 2 ? 700 : 400 }}>{t.name}</span>
              </td>
              <td style={{ padding: '4px 4px', textAlign: 'center' }}>{t.p}</td>
              <td style={{ padding: '4px 4px', textAlign: 'center' }}>{t.w}</td>
              <td style={{ padding: '4px 4px', textAlign: 'center' }}>{t.d}</td>
              <td style={{ padding: '4px 4px', textAlign: 'center' }}>{t.l}</td>
              <td style={{ padding: '4px 4px', textAlign: 'center', color: t.gf - t.ga > 0 ? 'var(--accent)' : t.gf - t.ga < 0 ? 'var(--red)' : 'var(--muted)' }}>
                {t.gf - t.ga > 0 ? '+' : ''}{t.gf - t.ga}
              </td>
              <td style={{ padding: '4px 4px', textAlign: 'center', fontWeight: 700, color: 'var(--gold)' }}>{t.pts}</td>
              <td style={{ padding: '4px 4px' }}><FormDots form={t.form} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Groups({ liveData }) {
  const groups = liveData || GROUPS

  // Group winners summary banner
  const winners = Object.entries(groups).map(([letter, data]) => {
    const sorted = [...data.teams].sort((a, b) => b.pts !== a.pts ? b.pts - a.pts : (b.gf-b.ga)-(a.gf-a.ga))
    return { letter, team: sorted[0] }
  })

  return (
    <div className="page-content">
      <div className="section-title">📊 Final Group Stage Standings</div>

      {/* Group winners strip */}
      <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 10, padding: '12px 14px', marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#6ee7b7', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
          GROUP WINNERS — ROUND OF 32
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {winners.map(({ letter, team }) => (
            <div key={letter} style={{ display: 'flex', alignItems: 'center', gap: 5, background: 'rgba(255,255,255,0.06)', borderRadius: 6, padding: '4px 8px', fontSize: 12 }}>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', fontWeight: 700 }}>G{letter}</span>
              <span>{team.flag}</span>
              <span style={{ fontWeight: 700 }}>{team.name}</span>
              <span style={{ color: '#fbbf24', fontWeight: 700, fontSize: 11 }}>{team.pts}pts</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12, padding: '6px 10px', background: 'var(--card2)', borderRadius: 6 }}>
        ✅ Group stage complete · All 32 teams qualified · Round of 32 starts 28 Jun 2026
      </div>
      <div className="grid-3">
        {Object.entries(groups).map(([letter, data]) => (
          <GroupTable key={letter} letter={letter} data={data} />
        ))}
      </div>
    </div>
  )
}
