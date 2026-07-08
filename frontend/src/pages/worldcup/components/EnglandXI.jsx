import { useState } from 'react'
import { ENGLAND_SQUAD, BETBUD_XI } from '../data/specials'

const FORMATIONS = {
  '4-3-3': { GK: 1, DEF: 4, MID: 3, FWD: 3 },
  '4-2-3-1': { GK: 1, DEF: 4, MID: 5, FWD: 1 },
  '3-5-2': { GK: 1, DEF: 3, MID: 5, FWD: 2 },
  '4-4-2': { GK: 1, DEF: 4, MID: 4, FWD: 2 },
}

const PITCH_BG = 'linear-gradient(180deg, #0a3d1a 0%, #0d4d20 25%, #0a3d1a 50%, #0d4d20 75%, #0a3d1a 100%)'

function PitchPlayer({ name, flag, isBetBud }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', cursor: 'default' }}>
      <div style={{
        width: 44, height: 44, borderRadius: '50%',
        background: isBetBud ? 'linear-gradient(135deg,#b8970a,var(--gold))' : '#fff',
        border: `3px solid ${isBetBud ? 'var(--gold)' : '#c8e6c9'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 20, boxShadow: isBetBud ? '0 0 12px rgba(255,215,0,0.5)' : 'none'
      }}>
        {flag}
      </div>
      <div style={{
        marginTop: 4, fontSize: 10, fontWeight: 700, color: '#fff',
        textAlign: 'center', maxWidth: 70, lineHeight: 1.2,
        textShadow: '0 1px 2px rgba(0,0,0,0.8)',
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'
      }}>
        {name.split(' ').slice(-1)[0]}
      </div>
    </div>
  )
}

function PitchRow({ players, selectedNames, betbudNames }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-evenly', alignItems: 'center', padding: '8px 0' }}>
      {players.map((p, i) => (
        <PitchPlayer
          key={i}
          name={p.name}
          flag={p.flag}
          isBetBud={betbudNames.includes(p.name)}
        />
      ))}
    </div>
  )
}

export default function EnglandXI() {
  const [formation, setFormation] = useState('4-3-3')
  const [selected, setSelected] = useState({ GK: [], DEF: [], MID: [], FWD: [] })
  const [mode, setMode] = useState('user') // 'user' | 'betbud'

  const limits = FORMATIONS[formation]

  function togglePlayer(pos, player) {
    setSelected(prev => {
      const cur = prev[pos]
      const limit = limits[pos]
      if (cur.find(p => p.name === player.name)) {
        return { ...prev, [pos]: cur.filter(p => p.name !== player.name) }
      }
      if (cur.length >= limit) {
        return { ...prev, [pos]: [...cur.slice(1), player] }
      }
      return { ...prev, [pos]: [...cur, player] }
    })
  }

  function getBetBudSquad() {
    const all = [...ENGLAND_SQUAD.GK, ...ENGLAND_SQUAD.DEF, ...ENGLAND_SQUAD.MID, ...ENGLAND_SQUAD.FWD]
    const findP = name => all.find(p => p.name === name) || { name, flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' }
    return {
      GK: BETBUD_XI.GK.map(findP),
      DEF: BETBUD_XI.DEF.map(findP),
      MID: BETBUD_XI.MID.map(findP),
      FWD: BETBUD_XI.FWD.map(findP),
    }
  }

  const displayXI = mode === 'betbud' ? getBetBudSquad() : selected
  const betbudNames = [...BETBUD_XI.GK, ...BETBUD_XI.DEF, ...BETBUD_XI.MID, ...BETBUD_XI.FWD]

  const totalSelected = Object.values(selected).flat().length

  return (
    <div className="page-content">
      <div className="section-title">🏴󠁧󠁢󠁥󠁮󠁧󠁿 England Starting XI — vs 🇭🇷 Croatia (17 Jun 2026)</div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <select className="select" value={formation} onChange={e => setFormation(e.target.value)}>
          {Object.keys(FORMATIONS).map(f => <option key={f} value={f}>{f}</option>)}
        </select>
        <button className={`btn ${mode === 'user' ? 'btn-gold' : 'btn-ghost'}`} onClick={() => setMode('user')}>
          ✏️ Pick Your XI
        </button>
        <button className={`btn ${mode === 'betbud' ? 'btn-gold' : 'btn-ghost'}`} onClick={() => setMode('betbud')}>
          🤖 BetBud's XI
        </button>
        {mode === 'user' && (
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>
            Selected: {totalSelected}/11 · Formation: {formation}
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, alignItems: 'start' }}>
        {/* Pitch visualization */}
        <div>
          <div style={{ fontWeight: 700, marginBottom: 10, color: 'var(--gold)', fontSize: 13 }}>
            {mode === 'betbud' ? '🤖 BetBud Predicted XI' : '✏️ Your Selected XI'} ({formation})
          </div>
          <div style={{
            background: PITCH_BG, borderRadius: 12, padding: '16px 8px',
            border: '2px solid #2d6a35', position: 'relative', minHeight: 400
          }}>
            {/* Pitch markings */}
            <div style={{ position: 'absolute', top: '50%', left: '10%', right: '10%', height: 1, background: 'rgba(255,255,255,0.15)' }} />
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 60, height: 60, borderRadius: '50%', border: '1px solid rgba(255,255,255,0.15)' }} />

            {/* GK */}
            <div style={{ textAlign: 'center', fontSize: 10, color: 'rgba(255,255,255,0.4)', marginBottom: 4 }}>GK</div>
            {displayXI.GK.length > 0
              ? <PitchRow players={displayXI.GK} selectedNames={[]} betbudNames={betbudNames} />
              : <div style={{ height: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.2)', fontSize: 12 }}>Select GK →</div>
            }

            {/* DEF */}
            <div style={{ textAlign: 'center', fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>DEF</div>
            {displayXI.DEF.length > 0
              ? <PitchRow players={displayXI.DEF} selectedNames={[]} betbudNames={betbudNames} />
              : <div style={{ height: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.2)', fontSize: 12 }}>Select {limits.DEF} Defenders →</div>
            }

            {/* MID */}
            <div style={{ textAlign: 'center', fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>MID</div>
            {displayXI.MID.length > 0
              ? <PitchRow players={displayXI.MID} selectedNames={[]} betbudNames={betbudNames} />
              : <div style={{ height: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.2)', fontSize: 12 }}>Select {limits.MID} Midfielders →</div>
            }

            {/* FWD */}
            <div style={{ textAlign: 'center', fontSize: 10, color: 'rgba(255,255,255,0.4)', marginTop: 4 }}>FWD</div>
            {displayXI.FWD.length > 0
              ? <PitchRow players={displayXI.FWD} selectedNames={[]} betbudNames={betbudNames} />
              : <div style={{ height: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.2)', fontSize: 12 }}>Select {limits.FWD} Forwards →</div>
            }
          </div>
          {mode === 'betbud' && (
            <div style={{ marginTop: 10, fontSize: 12, color: 'var(--muted)', padding: '8px 12px', background: 'var(--card2)', borderRadius: 6 }}>
              🤖 BetBud picks: Pickford · James, Stones, Guehi, Quansah · Rice, Mainoo, Bellingham · Saka, Kane, Watkins
            </div>
          )}
        </div>

        {/* Squad selector */}
        {mode === 'user' && (
          <div>
            {[
              { pos: 'GK', label: '🧤 Goalkeepers', pool: ENGLAND_SQUAD.GK },
              { pos: 'DEF', label: '🛡️ Defenders', pool: ENGLAND_SQUAD.DEF },
              { pos: 'MID', label: '⚙️ Midfielders', pool: ENGLAND_SQUAD.MID },
              { pos: 'FWD', label: '⚽ Forwards', pool: ENGLAND_SQUAD.FWD },
            ].map(({ pos, label, pool }) => (
              <div key={pos} style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--gold)', marginBottom: 8 }}>
                  {label} — Pick {limits[pos]} ({selected[pos].length}/{limits[pos]})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {pool.map(p => {
                    const isSel = !!selected[pos].find(s => s.name === p.name)
                    const isBB = betbudNames.includes(p.name)
                    return (
                      <button
                        key={p.name}
                        onClick={() => togglePlayer(pos, p)}
                        style={{
                          background: isSel ? 'linear-gradient(135deg,#1a5a1a,var(--green))' : 'var(--card2)',
                          border: `1px solid ${isSel ? 'var(--accent)' : isBB ? 'var(--gold)' : 'var(--border)'}`,
                          color: isSel ? '#fff' : 'var(--text)',
                          padding: '5px 10px', borderRadius: 6, fontSize: 12, fontWeight: isSel ? 700 : 400,
                          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5
                        }}
                      >
                        {isBB && <span style={{ fontSize: 9, color: 'var(--gold)' }}>🤖</span>}
                        {p.name}
                        <span style={{ color: 'var(--muted)', fontSize: 10 }}>{p.rating}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
            <button
              className="btn btn-ghost"
              style={{ fontSize: 12, marginTop: 4 }}
              onClick={() => setSelected({ GK: [], DEF: [], MID: [], FWD: [] })}
            >
              Clear Selection
            </button>
          </div>
        )}

        {mode === 'betbud' && (
          <div>
            <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--gold)', marginBottom: 12 }}>🤖 BetBud Analysis — England vs Croatia</div>
            {[
              { pos: 'GK', players: BETBUD_XI.GK, note: 'Pickford undisputed No.1. Excellent shot-stopper, crucial in shootouts.' },
              { pos: 'DEF', players: BETBUD_XI.DEF, note: 'James right, Quansah left. Stones & Guehi central — best CB partnership in tournament.' },
              { pos: 'MID', players: BETBUD_XI.MID, note: 'Rice anchors. Mainoo box-to-box. Bellingham free role — expect him in the box constantly.' },
              { pos: 'FWD', players: BETBUD_XI.FWD, note: 'Saka right, Watkins left, Kane central. Croatia have no answer for Kane\'s movement.' },
            ].map(({ pos, players, note }) => (
              <div key={pos} style={{ marginBottom: 14, background: 'var(--card2)', borderRadius: 8, padding: '10px 12px' }}>
                <div style={{ fontWeight: 700, color: 'var(--muted)', fontSize: 11, marginBottom: 6, textTransform: 'uppercase' }}>{pos}</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                  {players.map(name => (
                    <span key={name} style={{ background: 'rgba(99,102,241,.15)', border: '1px solid rgba(99,102,241,.4)', padding: '3px 8px', borderRadius: 5, fontSize: 12, fontWeight: 700 }}>
                      {name}
                    </span>
                  ))}
                </div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>{note}</div>
              </div>
            ))}
            <div style={{ padding: '10px 12px', background: 'var(--card2)', borderRadius: 8, fontSize: 12, color: 'var(--muted)', borderLeft: '3px solid var(--purple)' }}>
              🤖 BetBud Prediction: England 2-0 Croatia · Kane & Bellingham scorers · Clean sheet likely
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
