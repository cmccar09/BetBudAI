import { useState, useEffect } from 'react'
import { OUTRIGHTS, GROUP_BETS, GOLDEN_BOOT_BETS } from '../data/bets'
import { BETFAIR_MOCK_MARKETS, decimalToAmerican, fetchBfEvents, fetchBfOutrights, fetchBfCatalogue } from '../services/betfair'

function TagBadge({ tag }) {
  const map = { hot: 'badge-hot', value: 'badge-val', tip: 'badge-tip' }
  const labels = { hot: '🔥 HOT', value: '💎 VALUE', tip: '💡 TIP' }
  return <span className={`badge ${map[tag] || 'badge-tip'}`}>{labels[tag] || tag}</span>
}

function ConfBar({ conf, width = 80 }) {
  const pct = typeof conf === 'string' ? parseInt(conf) : conf
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--accent)', fontWeight: 700 }}>{pct}%</div>
      <div className="conf-bar" style={{ width }}>
        <div className="conf-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function WeightPill({ weight }) {
  const colors = { high: '#4caf50', medium: '#ff9800', low: '#9e9e9e' }
  return (
    <span style={{
      fontSize: 9, fontWeight: 800, padding: '1px 6px', borderRadius: 4,
      background: colors[weight] + '22', color: colors[weight],
      textTransform: 'uppercase', letterSpacing: 0.5
    }}>
      {weight}
    </span>
  )
}

function DrillDown({ d }) {
  if (!d) return null
  return (
    <div style={{
      margin: '10px 0 4px', padding: '14px 16px',
      background: '#0f172a', border: '1px solid #334155',
      borderRadius: 8, borderLeft: '3px solid var(--purple)',
    }}>
      {/* Methodology chips */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>
          🔍 Analysis Methodology
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
          {d.methodology.map((m, i) => (
            <span key={i} style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 10,
              background: '#2d3748', color: 'var(--accent)', border: '1px solid #334155',
              fontWeight: 600
            }}>{m}</span>
          ))}
        </div>
      </div>

      {/* Key factors */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>
          📊 Key Factors
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {d.factors.map((f, i) => (
            <div key={i} style={{
              display: 'flex', gap: 8, alignItems: 'flex-start',
              padding: '5px 8px', background: '#1e293b', borderRadius: 5
            }}>
              <WeightPill weight={f.weight} />
              <div>
                <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)', marginRight: 6 }}>{f.name}:</span>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>{f.detail}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Risk factors */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, color: '#ef9a9a', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>
          ⚠ Risk Factors
        </div>
        <ul style={{ margin: 0, paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 3 }}>
          {d.risks.map((r, i) => (
            <li key={i} style={{ fontSize: 12, color: '#ef9a9a99' }}>{r}</li>
          ))}
        </ul>
      </div>

      {/* AI verdict */}
      <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 10px', border: '1px solid #334155' }}>
        <div style={{ fontSize: 10, color: 'var(--gold)', fontWeight: 800, marginBottom: 4 }}>
          🤖 BETBUD AI VERDICT — {d.verdict}
        </div>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>{d.aiNote}</div>
      </div>
    </div>
  )
}

function OutrightRow({ o }) {
  const [open, setOpen] = useState(false)
  const pct = typeof o.prob === 'string' ? parseInt(o.prob) : o.prob
  return (
    <>
      <tr
        onClick={() => setOpen(!open)}
        style={{ cursor: 'pointer', background: open ? '#1e2a3b' : undefined }}
      >
        <td style={{ fontWeight: 700, fontSize: 14 }}>
          <span style={{ marginRight: 6, fontSize: 11, color: 'var(--muted)' }}>{open ? '▲' : '▼'}</span>
          {o.team}
        </td>
        <td className="odds-pill">{o.odds}</td>
        <td style={{ color: 'var(--muted)', fontSize: 12 }}>{o.decOdds}</td>
        <td>
          <div style={{ color: 'var(--accent)', fontWeight: 700 }}>{o.prob}</div>
          <div className="conf-bar" style={{ width: 60, marginTop: 2 }}>
            <div className="conf-fill" style={{ width: `${pct}%` }} />
          </div>
        </td>
        <td>
          <span style={{ display: 'inline-flex', gap: 2 }}>
            {o.form.split('').map((c, i) => <span key={i} className={`form-dot form-${c}`} />)}
          </span>
        </td>
        <td><TagBadge tag={o.tag} /></td>
        <td style={{ color: 'var(--muted)', fontSize: 12, maxWidth: 220 }}>{o.reason}</td>
      </tr>
      {open && (
        <tr>
          <td colSpan={7} style={{ padding: '0 8px 8px', background: '#0f172a' }}>
            <DrillDown d={o.drilldown} />
          </td>
        </tr>
      )}
    </>
  )
}

function GroupBetRow({ b }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <tr
        onClick={() => setOpen(!open)}
        style={{ cursor: 'pointer', background: open ? '#1e2a3b' : undefined }}
      >
        <td style={{ fontWeight: 600, fontSize: 12 }}>
          <span style={{ marginRight: 6, fontSize: 11, color: 'var(--muted)' }}>{open ? '▲' : '▼'}</span>
          {b.match}
        </td>
        <td style={{ color: 'var(--gold)', fontWeight: 700 }}>{b.bet}</td>
        <td className="odds-pill">{b.odds}</td>
        <td style={{ color: 'var(--muted)', fontSize: 12 }}>{b.decOdds}</td>
        <td><ConfBar conf={b.conf} /></td>
        <td><TagBadge tag={b.tag} /></td>
        <td style={{ color: 'var(--muted)', fontSize: 12, maxWidth: 220 }}>{b.reason}</td>
      </tr>
      {open && (
        <tr>
          <td colSpan={7} style={{ padding: '0 8px 8px', background: '#0f172a' }}>
            <DrillDown d={b.drilldown} />
          </td>
        </tr>
      )}
    </>
  )
}

function GoldenBootCard({ p }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="card-sm" style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => setOpen(!open)}>
      <div style={{ fontSize: 32 }}>{p.flag}</div>
      <div style={{ fontWeight: 700, fontSize: 15, marginTop: 6 }}>{p.player}</div>
      <div style={{ fontSize: 26, fontWeight: 900, color: 'var(--gold)', margin: '10px 0 2px' }}>{p.odds}</div>
      <div style={{ fontSize: 11, color: 'var(--muted)' }}>Decimal: {p.decOdds}</div>
      <div className="conf-bar" style={{ margin: '10px auto', width: 100 }}>
        <div className="conf-fill" style={{ width: `${p.conf}%` }} />
      </div>
      <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4, textAlign: 'left' }}>{p.analysis}</div>
      <div style={{ marginTop: 8, fontSize: 11, color: 'var(--accent)', fontWeight: 600 }}>
        {open ? '▲ Hide analysis' : '▼ Full analysis'}
      </div>
      {open && (
        <div style={{ textAlign: 'left', marginTop: 4 }}>
          <DrillDown d={p.drilldown} />
        </div>
      )}
    </div>
  )
}

function CornersRow({ r, i }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <tr
        onClick={() => setOpen(!open)}
        style={{ cursor: 'pointer', background: open ? '#1e2a3b' : undefined }}
      >
        <td style={{ fontSize: 12, fontWeight: 600 }}>
          <span style={{ marginRight: 6, fontSize: 11, color: 'var(--muted)' }}>{open ? '▲' : '▼'}</span>
          {r.match}
        </td>
        <td style={{ fontSize: 12 }}>{r.market}</td>
        <td className="odds-pill">{typeof r.betfairOdds === 'number' ? r.betfairOdds.toFixed(2) : r.betfairOdds}</td>
        <td><span className={`badge ${r.pred === 'YES' ? 'badge-yes' : 'badge-maybe'}`}>{r.pred}</span></td>
        <td><ConfBar conf={r.conf} /></td>
        <td style={{ color: 'var(--muted)', fontSize: 12, maxWidth: 220 }}>{r.reason}</td>
      </tr>
      {open && (
        <tr>
          <td colSpan={6} style={{ padding: '0 8px 8px', background: '#0f172a' }}>
            <DrillDown d={r.drilldown} />
          </td>
        </tr>
      )}
    </>
  )
}

function BetfairMarketCard({ match, markets }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div
        className="card-title"
        style={{ cursor: 'pointer', justifyContent: 'space-between' }}
        onClick={() => setExpanded(!expanded)}
      >
        <span>{match}</span>
        <span style={{ color: 'var(--muted)', fontSize: 14 }}>{expanded ? '▲' : '▼'}</span>
      </div>
      {expanded && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {markets.map((mkt, mi) => (
            <div key={mi}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: .5, marginBottom: 6 }}>
                {mkt.marketName}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {mkt.runners.map((r, ri) => (
                  <div key={ri} style={{
                    background: 'var(--dark)', border: `1px solid ${r.tag ? 'var(--gold)' : 'var(--border)'}`,
                    borderRadius: 8, padding: '8px 12px', minWidth: 130, position: 'relative'
                  }}>
                    {r.tag && (
                      <span style={{ position: 'absolute', top: -8, right: 6, fontSize: 9, background: '#7c4a00', color: 'var(--gold)', padding: '1px 6px', borderRadius: 8, fontWeight: 700 }}>
                        BETBUD
                      </span>
                    )}
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{r.name}</div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 6, fontSize: 12 }}>
                      <div>
                        <div style={{ color: 'var(--muted)', fontSize: 10 }}>BACK</div>
                        <div style={{ color: '#64b5f6', fontWeight: 700, fontSize: 14 }}>{r.back}</div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--muted)', fontSize: 10 }}>LAY</div>
                        <div style={{ color: '#ef9a9a', fontWeight: 700, fontSize: 14 }}>{r.lay}</div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--muted)', fontSize: 10 }}>US</div>
                        <div style={{ color: 'var(--gold)', fontWeight: 700, fontSize: 13 }}>{decimalToAmerican(r.back)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const CORNERS_DATA = [
  ...(() => {
    const engCro = BETFAIR_MOCK_MARKETS['England vs Croatia (17 Jun)']
    return engCro
      .filter(m => ['Total Corners (Over/Under 9.5)', 'Total Bookings (Over/Under 3.5)'].includes(m.marketName))
      .flatMap(m => m.runners.slice(0, 1).map(r => ({
        match: 'England vs Croatia', market: `${m.marketName} — ${r.name}`,
        betfairOdds: r.back, pred: r.tag ? 'YES' : 'CHECK', conf: r.tag ? 72 : 50,
        reason: `Betfair Exchange line. ${r.tag ? 'BetBud supports this side.' : 'Marginal — review closer to kick-off.'}`,
        drilldown: {
          methodology: ['Betfair Exchange Line', 'Team Style Analysis', 'H2H Corner Data'],
          factors: [
            { name: 'Exchange Price', detail: `Market line: ${m.marketName}. Back price ${r.back} — exchange consensus`, weight: 'high' },
            { name: 'England Wide Play', detail: 'Saka right, Bellingham attacking, full-backs push on — high corner generation team', weight: 'high' },
            { name: 'Croatia Deep Block', detail: 'Croatia sit deep vs England, forcing crosses and corners from England\'s wide players', weight: 'high' },
          ],
          risks: ['Injury/suspension changes team shape', 'Neutral venue affects crowd-driven pressure'],
          verdict: r.tag ? 'BACK' : 'MONITOR',
          aiNote: r.tag ? 'BetBud supports this Betfair Exchange line. The market price reflects sharp money on this outcome.' : 'Marginal — monitor closer to kick-off for late movement.',
        }
      })))
  })(),
  {
    match: 'France vs Iraq', market: 'Total Corners Over 8.5', betfairOdds: 1.70, pred: 'YES', conf: 80,
    reason: 'France dominate possession vs deep-sitting Iraq, generating crosses and corners.',
    drilldown: {
      methodology: ['France Possession Stats', 'Iraq Defensive Block Analysis', 'Corner Generation Rate', 'Similar Match Precedents'],
      factors: [
        { name: 'France Possession', detail: 'France average 68% possession in competitive games — forcing opposition into defensive shape', weight: 'high' },
        { name: 'Iraq Deep Block', detail: 'Iraq sat with 9 men behind the ball in Asian qualifying — generating massive corner opportunities', weight: 'high' },
        { name: 'France Corner Rate', detail: 'France averaged 7.8 corners/game in Euro 2024 qualifying. vs deep teams: 10.2/game', weight: 'high' },
        { name: 'Mbappé + Dembélé Crossers', detail: 'Both attack the byline regularly. Iraq will concede 10-13 corners expected', weight: 'medium' },
      ],
      risks: ['France score early and ease off — reduced intensity late in game', 'Iraq surprisingly attack — less possession for France'],
      verdict: 'BACK',
      aiNote: 'BetBud 80% confidence. France vs a 9-man Iraq defensive block will generate corners relentlessly. Over 8.5 at 1.70 is well-priced — expect 10-13 corners from France alone.',
    }
  },
  {
    match: 'England vs Croatia', market: 'England Corners Over 5.5', betfairOdds: 2.00, pred: 'YES', conf: 68,
    reason: 'England\'s wide play via Saka and Bellingham generates corners. Croatia sit deep.',
    drilldown: {
      methodology: ['England Corner Rate', 'Croatia Defensive System', 'Saka/Bellingham Wide Threat', 'Historic England vs Croatia WC Data'],
      factors: [
        { name: 'England Corner Rate', detail: 'England average 6.1 corners/game under Tuchel — wide play central to system', weight: 'high' },
        { name: 'Croatia Defensive Setup', detail: 'Croatia sit in 4-5-1/4-4-2 deep block vs big nations — pushes England wide', weight: 'high' },
        { name: 'Saka Right Side', detail: 'Saka drives to the byline repeatedly. Croatia will block — corners inevitable', weight: 'high' },
        { name: 'Set-Piece Focus', detail: 'Tuchel has worked extensively on set-pieces. England use corners as primary attacking weapon', weight: 'medium' },
      ],
      risks: ['Saka or Trippier injury reduces right-side threat', 'England score 2-0 early and stop pressing — corners decline'],
      verdict: 'BACK',
      aiNote: 'BetBud 68% confidence. England\'s wide-play system and Tuchel\'s set-piece focus means 6+ England corners is a realistic expectation vs Croatia\'s deep defensive block. Over 5.5 at 2.00 is fair value.',
    }
  },
  {
    match: 'Germany vs Curaçao', market: 'Total Corners Over 10.5', betfairOdds: 1.90, pred: 'YES', conf: 82,
    reason: 'Germany bombard Curaçao. Expected 12-15 corners as Germany dominate from all areas.',
    drilldown: {
      methodology: ['Germany vs Weak Teams Corner Data', 'Curaçao Defensive Setup', 'Musiala-Wirtz Wide Threat', 'Expected Total Corners Model'],
      factors: [
        { name: 'Germany vs Lower Ranked', detail: 'Germany averaged 12.4 total corners/game vs teams ranked 70+ in 2025/26', weight: 'high' },
        { name: 'Curaçao Defensive Approach', detail: 'Curaçao will sit in a compact 4-5-1 — German wingers will attack the byline repeatedly', weight: 'high' },
        { name: 'Musiala + Wirtz Width', detail: 'Both attack wide areas instinctively. Two world-class dribblers generating corner after corner', weight: 'high' },
        { name: 'Gnabry Crossing', detail: 'Gnabry on the right side adds another corner-generation threat — 3 wide attackers creating opportunities', weight: 'medium' },
      ],
      risks: ['Germany score 5-0 and take it easy late — corners in final 20 minutes dry up', 'Curaçao play attacking football in desperation — fewer German corner opportunities'],
      verdict: 'BACK',
      aiNote: 'BetBud 82% confidence. Germany dominating Curaçao will generate a record number of corners — the match is the tournament\'s most lopsided in expected corner count. Over 10.5 at 1.90 is strong value.',
    }
  },
  {
    match: 'Argentina vs Algeria', market: 'Total Cards Over 3.5', betfairOdds: 1.88, pred: 'YES', conf: 70,
    reason: 'Algeria likely to foul frequently to disrupt Argentina\'s play. 4+ yellow cards expected.',
    drilldown: {
      methodology: ['Algeria Foul Rate', 'Argentina vs Physical Teams', 'WC Card Rate Statistics', 'Referee Analysis', 'H2H Physical Data'],
      factors: [
        { name: 'Algeria Foul Rate', detail: 'Algeria averaged 18.2 fouls/game in AFCON qualifying — highest of all African qualifiers', weight: 'high' },
        { name: 'Argentina vs Pressure', detail: 'Argentina draw fouls: Messi, Álvarez and Di María all targeted heavily by physical teams', weight: 'high' },
        { name: 'WC Cards Rate', detail: 'WC matches with a 20+ FIFA ranking gap average 4.8 yellow cards/game historically', weight: 'high' },
        { name: 'Algeria Tactical Disruption', detail: 'Algeria\'s only chance to stop Argentina is physical disruption — expect deliberate tactical fouling', weight: 'high' },
        { name: 'Group Stage Intensity', detail: 'Group stage games without card-consequence pressure (yellow cards reset) tend to see more bookings', weight: 'medium' },
      ],
      risks: ['Lenient referee reduces card frequency', 'Algeria approach the game openly — fewer defensive fouls', 'Early red card changes dynamics entirely'],
      verdict: 'BACK',
      aiNote: 'BetBud 70% confidence. Algeria will be physically aggressive against Argentina — it is their only viable strategy. 4+ yellow cards is the baseline expectation. At 1.88 this is well-priced value.',
    }
  },
  {
    match: 'Brazil vs Haiti', market: 'Total Corners Over 9.5', betfairOdds: 1.80, pred: 'YES', conf: 85,
    reason: 'Brazil dominate, Haiti sit deep. Vini Jr and Rodrygo generate corners constantly.',
    drilldown: {
      methodology: ['Brazil Corner Generation Rate', 'Haiti Defensive Block', 'Vini Jr Byline Threat', 'Copa America Corner Data'],
      factors: [
        { name: 'Brazil Corner Rate', detail: 'Brazil averaged 9.8 total corners/game in Copa America 2024 — among highest in tournament', weight: 'high' },
        { name: 'Haiti Defensive Setup', detail: 'Haiti will sit in a 5-4-1 deep block. Every Brazil attack hits the byline — corners follow', weight: 'high' },
        { name: 'Vini Jr Width', detail: 'Vini Jr attacks the left channel relentlessly. Will generate 4-5 corners himself in 90 minutes', weight: 'high' },
        { name: 'Brazil Crossing Game', detail: 'Raphinha right, Vini Jr left — Brazil\'s wide play is their primary attacking weapon vs deep blocks', weight: 'high' },
      ],
      risks: ['Brazil score 5 early and coast — reduced intensity reduces corners in final 30 minutes', 'Haiti surprisingly counterattack — disrupts Brazil\'s possession rhythm'],
      verdict: 'STRONG BACK',
      aiNote: 'BetBud 85% confidence. Brazil vs Haiti is a corner-generation machine — similar to Copa America 2016 (7-1, 14 corners). Over 9.5 at 1.80 is excellent value. Second-highest confidence corners bet.',
    }
  },
  {
    match: 'Spain vs Cape Verde', market: 'Spain Corners Over 7.5', betfairOdds: 1.95, pred: 'YES', conf: 78,
    reason: 'Spain\'s patient build-up forces Cape Verde wide, generating corners regularly.',
    drilldown: {
      methodology: ['Spain Corner Rate Euro 2024', 'Cape Verde Defensive Analysis', 'Yamal Right Side Threat', 'Spain vs Africa H2H Corners'],
      factors: [
        { name: 'Spain Euro 2024 Corners', detail: 'Spain averaged 8.3 corners/game in Euro 2024 — most of any team in the tournament', weight: 'high' },
        { name: 'Cape Verde Defensive Compact', detail: 'Cape Verde will defend with 10 men behind the ball — Spain\'s patient build-up generates corner after corner', weight: 'high' },
        { name: 'Yamal Right-Side Attack', detail: 'Yamal drives the right side relentlessly. Cape Verde left-back will be overwhelmed — multiple corners', weight: 'high' },
        { name: 'Spain Build-Up System', detail: 'De la Fuente\'s Spain recycle possession through full-backs then attack wide — systematic corner generation', weight: 'medium' },
      ],
      risks: ['Spain score three quick goals — may play conservatively in the second half', 'Cape Verde surprisingly attack — disrupting Spain\'s possession-based corner generation'],
      verdict: 'BACK',
      aiNote: 'BetBud 78% confidence. Spain\'s wide-play system vs Cape Verde\'s defensive block will generate 8-10+ Spain corners. Over 7.5 at 1.95 is solid value — Spain are the most systematic corner-generating team at this World Cup.',
    }
  },
  {
    match: 'England vs Croatia', market: 'Kane First Scorer & England Win', betfairOdds: 5.50, pred: 'YES', conf: 55,
    reason: 'Kane historically scores first. Croatia vulnerable to set pieces. Good each-way value.',
    drilldown: {
      methodology: ['Kane First Scorer History', 'Croatia Set-Piece Vulnerability', 'England Opening Game Mentality', 'Anytime + First Scorer Probability Model'],
      factors: [
        { name: 'Kane First Scorer Record', detail: 'Kane has been first scorer in 31% of England games where he scored (2021-2026). Above market rate', weight: 'high' },
        { name: 'England vs Croatia 2018', detail: 'In 2018 WC England 2-1 Croatia (AET) — Kieran Trippier scored first. Kane missed penalty. Different this time', weight: 'medium' },
        { name: 'Croatia Set-Piece', detail: 'Croatia conceded 4 set-piece goals in 2025/26 UEFA Nations League. Kane is the set-piece striker', weight: 'high' },
        { name: 'England Opener Motivation', detail: 'Tuchel wants to make a statement in the first game. Kane will be unleashed on Croatia from the start', weight: 'medium' },
        { name: 'Odds Value', detail: '5.50 decimal (implied 18.2%) vs BetBud model 55% × 60% (Kane scores) × 60% (first) = ~20% — roughly fair', weight: 'medium' },
      ],
      risks: ['Bellingham could score first from midfield', 'Saka or Watkins may be more aggressive in the final third', 'If England go behind early, game dynamics change entirely'],
      verdict: 'SPECULATIVE TIP',
      aiNote: 'BetBud 55% overall England win confidence × Kane first scorer probability ≈ 20% — the 5.50 price is roughly fair. This is a speculative narrative bet rather than a strong value play. Include as a fun single rather than a serious investment. Watch team news for Kane starting confirmation.',
    }
  },
]

const TOP5 = [
  {
    rank: 1,
    emoji: '💎',
    label: 'OUTRIGHT VALUE',
    title: 'England Each-Way — Best Value Outright',
    subtitle: 'Outright — Best market value among the top-5 favourites (BetBud champion pick: 🇫🇷 France, 68%)',
    odds: '+700',
    decOdds: '8.00',
    conf: 56,
    tag: 'value',
    stakeAdvice: '1–2% bankroll',
    verdict: 'EACH-WAY BACK — BEST VALUE OF THE FAVOURITES',
    summary: 'Kane + Bellingham at peak, Tuchel\'s defensive organisation transformed England. Group L is the easiest path of any top-5 nation. At +700 the market underprices them vs our 56% model — the biggest value edge of all outright picks. Note: BetBud\'s outright champion pick remains 🇫🇷 France (68%) — this is a value/each-way play on England reaching the latter stages, not a change to the title prediction.',
    keyFactors: [
      { name: 'Kane 2025/26', detail: '61 goals in 51 Bayern games — the world\'s most prolific striker', weight: 'high' },
      { name: 'Bellingham', detail: '18 La Liga goals + 14 assists — orchestrating world-class creativity', weight: 'high' },
      { name: 'Tuchel Defence', detail: '6 clean sheets in first 8 games — England defensive record transformed', weight: 'high' },
      { name: 'Group L Draw', detail: 'Panama, Ghana, Croatia — the clearest path to the knockout rounds', weight: 'high' },
      { name: 'Market Edge', detail: '+700 implies 12.5% prob. BetBud model: 56%. Largest model/market gap of all favourites', weight: 'high' },
    ],
    risks: ['Kane\'s tournament record for England below his club form', 'Croatia opener is not a formality', 'England\'s historic pressure-situation tendency', 'France (68%) and Spain (62%) remain BetBud\'s higher-probability outright picks'],
    aiNote: 'England at +700/8.00 is BetBud\'s single highest-value outright bet — the model/market discrepancy is the largest of all top-8 teams. This is an each-way value play, separate from BetBud\'s outright champion prediction (France, 68%). Bet each-way for a deep run rather than to win outright.',
  },
  {
    rank: 2,
    emoji: '⚽',
    label: 'GROUP STAGE BET',
    title: 'Germany Win & Over 3.5 Goals vs Curaçao',
    subtitle: 'Group E opener — Germany vs Curaçao',
    odds: '-115',
    decOdds: '1.87',
    conf: 90,
    tag: 'hot',
    stakeAdvice: '2–3% bankroll',
    verdict: 'STRONG BACK — HIGHEST CONFIDENCE',
    summary: 'The most lopsided match-up in the entire group stage. Curaçao ranked 83rd, Germany ranked 6th with the most exciting young midfield in world football. Germany averaged 4.2 goals vs nations ranked 80+ (2021–2026). BetBud\'s highest-confidence single of the tournament.',
    keyFactors: [
      { name: 'FIFA Rank Gap', detail: 'Germany #6 vs Curaçao #83 — 77-place differential. Historic mismatch', weight: 'high' },
      { name: 'Germany Scoring Rate', detail: 'Germany avg 4.2 goals/game vs nations ranked 80+ in recent competitive fixtures', weight: 'high' },
      { name: 'Musiala + Wirtz', detail: 'Most exciting young midfield duo in world football — will carve Curaçao apart', weight: 'high' },
      { name: 'Curaçao Defensive Record', detail: 'Conceded 18 goals in CONCACAF qualifying — avg 3.0/game', weight: 'high' },
      { name: 'Tournament Opener', detail: 'Germany go all-out in openers. Motivated after 2018/2022 group stage exits', weight: 'high' },
    ],
    risks: ['Germany go 4-0 early and ease off — final goal count may not reach 4', 'Injury risk in a comfortable win'],
    aiNote: '90% confidence — BetBud\'s highest-rated single bet of the entire World Cup. This is as close to a certainty as the tournament offers. Strongest candidate for a banker in accumulator bets.',
  },
  {
    rank: 3,
    emoji: '🥇',
    label: 'GOLDEN BOOT',
    title: 'Kylian Mbappé — Top Scorer',
    subtitle: 'Golden Boot — Tournament Top Scorer',
    odds: '+350',
    decOdds: '4.50',
    conf: 78,
    tag: 'hot',
    stakeAdvice: '1–2% bankroll',
    verdict: 'BACK — CLEAR FAVOURITE',
    summary: 'Mbappé is at his absolute peak (27 years old, 28 La Liga goals in 2025/26). France face Iraq (#82) and Senegal (#23) in the group stage — Mbappé should score in both comfortably. BetBud predicts France reach the final (7 games), giving him 7 opportunities. His 2022 WC had 5 goals. This campaign is projected at 7.',
    keyFactors: [
      { name: 'La Liga 2025/26', detail: '28 goals — 2nd in Europe. At the absolute peak of his career aged 27', weight: 'high' },
      { name: 'WC History', detail: '4 goals in 2018, 5 goals & Golden Boot in 2022 — proven tournament scorer', weight: 'high' },
      { name: 'France Group I', detail: 'Iraq (#82), Senegal (#23), Norway — 3 games where Mbappé should score', weight: 'high' },
      { name: 'France to Final', detail: 'BetBud: France reach the final = 7 games = 7 Mbappé scoring opportunities', weight: 'high' },
      { name: 'Goals per Game', detail: '0.82 goals/game internationally 2025/26. Projected 5.7 goals in 7 WC games', weight: 'high' },
    ],
    risks: ['Minor knee concern March 2026 — monitor fitness news', 'France rotate if comfortably ahead in group', 'Haaland or Kane on comparable form'],
    aiNote: 'At +350/4.50 with 78% model confidence, Mbappé is the clearest value Golden Boot pick. Both the probability and the implied value make this the #3 bet overall. Combine with France to win outright for maximum return.',
  },
  {
    rank: 4,
    emoji: '⚽',
    label: 'GROUP STAGE BET',
    title: 'Brazil Over 3.5 Goals vs Haiti',
    subtitle: 'Group C — Brazil vs Haiti',
    odds: '-130',
    decOdds: '1.77',
    conf: 88,
    tag: 'hot',
    stakeAdvice: '2% bankroll',
    verdict: 'BACK',
    summary: 'Haiti conceded 12 goals in 4 CONCACAF qualifying final-round games — an average of 3.0 per game. Brazil have Vini Jr (22 La Liga goals), Rodrygo (14 goals) and the emerging Endrick (19 years old). Historical precedent: Brazil beat Haiti 7-1 in Copa America 2016. The Over 3.5 in this fixture is the second-safest bet in the group stage.',
    keyFactors: [
      { name: 'Haiti Defensive Record', detail: 'Conceded 12 goals in 4 qualifying games — avg 3.0/game. Catastrophic', weight: 'high' },
      { name: 'Brazil Attack Power', detail: 'Vini Jr + Rodrygo + Endrick — three world-class forwards all in form', weight: 'high' },
      { name: '2016 Precedent', detail: 'Brazil beat Haiti 7-1 in Copa America. Historical data strongly supports 4+ goals', weight: 'high' },
      { name: 'Brazil Wide Threats', detail: 'Raphinha + Vini Jr on both wings generate enormous chance volume — 20+ shots expected', weight: 'high' },
    ],
    risks: ['Brazil score 4 early and coast — reduced intensity may cap goals late', 'Haiti sit very deep — can slow tempo'],
    aiNote: '88% confidence — second highest group stage bet. Over 3.5 at -130/1.77 is the most appropriate market. Use as banker in accas alongside Germany vs Curaçao.',
  },
  {
    rank: 5,
    emoji: '🏆',
    label: 'OUTRIGHT WINNER',
    title: 'Germany Each-Way — World Cup Winner',
    subtitle: 'Outright — Each-way to win or top 4',
    odds: '+1200',
    decOdds: '13.00',
    conf: 38,
    tag: 'value',
    stakeAdvice: '0.5–1% bankroll',
    verdict: 'EACH-WAY BACK — BEST OUTSIDER VALUE',
    summary: 'Germany at +1200/13.00 is the biggest model vs market discrepancy of any team outside the top 4 favourites. BetBud model gives them 38% probability — the market implies 7.7%. Musiala + Wirtz is the most exciting midfield pairing in world football. Germany reach WC semis in 70% of tournaments historically. The North America venues have large German-descended communities — quasi-home advantage.',
    keyFactors: [
      { name: 'Musiala + Wirtz Form', detail: 'Musiala 24 goals (Bayern), Wirtz 21 goals (Leverkusen) — peak of their powers at 22', weight: 'high' },
      { name: 'Market Discrepancy', detail: 'Market implies 7.7% probability. BetBud model: 38%. Largest gap of any team at this price', weight: 'high' },
      { name: 'Historical Depth', detail: 'Germany reach WC semis in 70% of tournaments since 1966. Most reliable deep runners', weight: 'high' },
      { name: 'Group E', detail: 'Curaçao, Ivory Coast, Ecuador — the easiest group of any top-8 team', weight: 'high' },
      { name: 'Atmosphere Boost', detail: 'German diaspora across USA/Canada is enormous — effectively home support in several venues', weight: 'medium' },
    ],
    risks: ['Nagelsmann\'s first WC — experience gap vs elite coaches', 'No world-class No.9 — goals may dry up vs elite defences', 'Germany\'s recent WC record (2018 group exit, 2022 group exit)'],
    aiNote: 'Germany at +1200 is BetBud\'s top outsider value pick. The combination of Musiala-Wirtz, favourable draw, and historical depth makes the 13.00 price extraordinary value. Back each-way for a top-4 finish. Highest expected value of any bet in the top 5.',
  },
]

function RankBadge({ n }) {
  const styles = [
    { bg: 'linear-gradient(135deg,#f59e0b,#f97316)', color: '#fff' },
    { bg: 'linear-gradient(135deg,#94a3b8,#cbd5e1)', color: '#0f172a' },
    { bg: 'linear-gradient(135deg,#f97316,#ea580c)',  color: '#fff' },
    { bg: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff' },
    { bg: 'linear-gradient(135deg,#10b981,#059669)', color: '#fff' },
  ]
  const s = styles[n - 1] || styles[4]
  return (
    <div style={{
      width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
      background: s.bg, color: s.color,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 15, fontWeight: 900,
      boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
    }}>{n}</div>
  )
}

function Top5Card({ bet, expanded, onToggle }) {
  const tagMap  = { hot: 'badge-hot', value: 'badge-val', tip: 'badge-tip' }
  const tagLabel = { hot: '🔥 HOT', value: '💎 VALUE', tip: '💡 TIP' }
  const weightColors = { high: '#10b981', medium: '#f97316', low: '#94a3b8' }

  return (
    <div style={{
      background: 'var(--card)', border: '1px solid var(--border)',
      borderLeft: '4px solid var(--purple)', borderRadius: 12,
      overflow: 'hidden', transition: 'box-shadow .2s',
      boxShadow: expanded ? '0 4px 24px rgba(99,102,241,.25)' : '0 2px 8px rgba(0,0,0,.3)',
    }}>
      {/* Card header — always visible */}
      <div
        onClick={onToggle}
        style={{ padding: '16px 20px', cursor: 'pointer', display: 'flex', gap: 14, alignItems: 'flex-start' }}
      >
        <RankBadge n={bet.rank} />

        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Label row */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 4 }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: .8 }}>
              {bet.emoji} {bet.label}
            </span>
            <span className={`badge ${tagMap[bet.tag]}`}>{tagLabel[bet.tag]}</span>
          </div>

          {/* Title */}
          <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text)', marginBottom: 2 }}>{bet.title}</div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>{bet.subtitle}</div>
        </div>

        {/* Odds + conf (right side) */}
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontSize: 26, fontWeight: 900, color: 'var(--gold)', lineHeight: 1 }}>{bet.odds}</div>
          <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 6 }}>Dec: {bet.decOdds}</div>
          <div style={{ fontSize: 10, color: 'var(--accent2)', fontWeight: 700 }}>{bet.conf}% confidence</div>
          <div className="conf-bar" style={{ width: 80, marginTop: 4 }}>
            <div className="conf-fill" style={{ width: `${bet.conf}%` }} />
          </div>
        </div>

        <div style={{ color: 'var(--muted)', fontSize: 14, alignSelf: 'center', marginLeft: 4 }}>
          {expanded ? '▲' : '▼'}
        </div>
      </div>

      {/* Summary always-visible strip */}
      <div style={{ padding: '0 20px 14px', borderTop: '1px solid var(--border2)' }}>
        <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6, paddingTop: 10 }}>
          {bet.summary}
        </div>
        <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 11, background: 'rgba(99,102,241,.12)', color: 'var(--accent2)', padding: '2px 10px', borderRadius: 20, fontWeight: 600, border: '1px solid rgba(99,102,241,.25)' }}>
            {bet.verdict}
          </span>
          <span style={{ fontSize: 11, color: 'var(--muted)' }}>Stake: {bet.stakeAdvice}</span>
        </div>
      </div>

      {/* Expandable drilldown */}
      {expanded && (
        <div style={{ padding: '0 20px 20px', borderTop: '1px solid var(--border)' }}>
          {/* Key factors */}
          <div style={{ marginTop: 14, marginBottom: 12 }}>
            <div style={{ fontSize: 10, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: .5, marginBottom: 8 }}>
              📊 Key Factors
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              {bet.keyFactors.map((f, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', padding: '6px 10px', background: 'var(--card2)', borderRadius: 6 }}>
                  <span style={{
                    fontSize: 9, fontWeight: 800, padding: '2px 6px', borderRadius: 4, flexShrink: 0,
                    background: weightColors[f.weight] + '22', color: weightColors[f.weight],
                    textTransform: 'uppercase', letterSpacing: .5, marginTop: 1,
                  }}>{f.weight}</span>
                  <div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)', marginRight: 6 }}>{f.name}:</span>
                    <span style={{ fontSize: 12, color: 'var(--muted)' }}>{f.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Risks */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 10, color: '#ef9a9a', fontWeight: 700, textTransform: 'uppercase', letterSpacing: .5, marginBottom: 6 }}>
              ⚠ Risk Factors
            </div>
            <ul style={{ margin: 0, paddingLeft: 16 }}>
              {bet.risks.map((r, i) => (
                <li key={i} style={{ fontSize: 12, color: '#ef9a9a99', marginBottom: 3 }}>{r}</li>
              ))}
            </ul>
          </div>

          {/* AI verdict */}
          <div style={{ background: 'var(--card2)', borderRadius: 8, padding: '10px 12px', border: '1px solid var(--border2)', borderLeft: '3px solid var(--purple)' }}>
            <div style={{ fontSize: 10, color: 'var(--accent2)', fontWeight: 800, marginBottom: 4 }}>🤖 BETBUD AI VERDICT</div>
            <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>{bet.aiNote}</div>
          </div>
        </div>
      )}
    </div>
  )
}

function Top5Bets() {
  const [openIdx, setOpenIdx] = useState(null)

  return (
    <div className="section">
      {/* Header banner */}
      <div style={{
        background: 'linear-gradient(135deg,#1e293b,#312e81)',
        border: '2px solid var(--purple)', borderRadius: 14,
        padding: '20px 24px', marginBottom: 24,
        display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap',
      }}>
        <div style={{ fontSize: 48 }}>🎯</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
            BetBud AI — 2026 FIFA World Cup
          </div>
          <div style={{ fontSize: 26, fontWeight: 900, color: 'var(--text)', lineHeight: 1.1 }}>
            Top 5 Bets of the Tournament
          </div>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 6 }}>
            Ranked by AI confidence, value edge, and expected return. Tap any card to expand full analysis.
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11, color: 'var(--muted)' }}>Combined acc odds</div>
          <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--gold)' }}>+3,900</div>
          <div style={{ fontSize: 11, color: 'var(--muted)' }}>if all 5 win</div>
        </div>
      </div>

      {/* Quick-stats row */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        {[
          { label: 'Highest Confidence', value: '90%', sub: 'Germany vs Curaçao', color: 'var(--green)' },
          { label: 'Best Value Odds', value: '+1200', sub: 'Germany Outright', color: 'var(--gold)' },
          { label: 'Avg Confidence', value: '70%', sub: 'Across top 5 picks', color: 'var(--accent2)' },
          { label: 'Recommended Stake', value: '≤2%', sub: 'Bankroll per bet', color: 'var(--orange)' },
        ].map(s => (
          <div key={s.label} className="card-sm" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 22, fontWeight: 900, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text)', marginTop: 2 }}>{s.label}</div>
            <div style={{ fontSize: 10, color: 'var(--muted)' }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Bet cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {TOP5.map((bet, i) => (
          <Top5Card
            key={bet.rank}
            bet={bet}
            expanded={openIdx === i}
            onToggle={() => setOpenIdx(openIdx === i ? null : i)}
          />
        ))}
      </div>

      {/* Disclaimer */}
      <div style={{ marginTop: 20, fontSize: 11, color: 'var(--muted)', textAlign: 'center', lineHeight: 1.7 }}>
        🤖 BetBud AI picks are for entertainment purposes only. All selections are model-generated — never a guarantee.
        Please gamble responsibly. Never bet more than you can afford to lose. 18+ · BeGambleAware.org
      </div>
    </div>
  )
}

function LiveRunner({ r }) {
  return (
    <div style={{
      background: 'var(--dark2)', border: `1px solid ${r.tag ? 'var(--purple)' : 'var(--border2)'}`,
      borderRadius: 8, padding: '8px 12px', minWidth: 130, position: 'relative',
    }}>
      {r.tag && (
        <span style={{
          position: 'absolute', top: -8, right: 6, fontSize: 9,
          background: 'rgba(99,102,241,.3)', color: 'var(--accent2)',
          padding: '1px 6px', borderRadius: 8, fontWeight: 700, border: '1px solid var(--purple)',
        }}>BETBUD</span>
      )}
      <div style={{ fontWeight: 600, fontSize: 13 }}>{r.name}</div>
      <div style={{ display: 'flex', gap: 8, marginTop: 6, fontSize: 12 }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 10 }}>BACK</div>
          <div style={{ color: '#93c5fd', fontWeight: 700, fontSize: 14 }}>{r.back?.toFixed(2) ?? '-'}</div>
        </div>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 10 }}>LAY</div>
          <div style={{ color: '#fca5a5', fontWeight: 700, fontSize: 14 }}>{r.lay?.toFixed(2) ?? '-'}</div>
        </div>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 10 }}>US</div>
          <div style={{ color: 'var(--gold)', fontWeight: 700, fontSize: 13 }}>{decimalToAmerican(r.back)}</div>
        </div>
      </div>
    </div>
  )
}

function LiveMarketCard({ mkt }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div
        className="card-title"
        style={{ cursor: 'pointer', justifyContent: 'space-between', marginBottom: open ? 12 : 0 }}
        onClick={() => setOpen(!open)}
      >
        <span>{mkt.marketName || mkt.description?.marketName || 'Market'}</span>
        <span style={{ color: 'var(--muted)', fontSize: 14 }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {(mkt.runners || []).map((r, i) => (
            <LiveRunner key={i} r={r} />
          ))}
        </div>
      )}
    </div>
  )
}

function LiveEventCard({ event, onSelect, selected }) {
  const name = event.event?.name || 'Event'
  const date = event.event?.openDate ? new Date(event.event.openDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''
  return (
    <div
      onClick={() => onSelect(event.event?.id)}
      style={{
        background: selected ? 'rgba(99,102,241,.15)' : 'var(--card2)',
        border: `1px solid ${selected ? 'var(--purple)' : 'var(--border2)'}`,
        borderRadius: 8, padding: '10px 14px', cursor: 'pointer',
        transition: 'all .15s',
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 13 }}>{name}</div>
      <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>{date}</div>
    </div>
  )
}

function BetfairLiveTab() {
  const [loading, setLoading]   = useState(true)
  const [events, setEvents]     = useState([])
  const [outrights, setOutrights] = useState([])
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [catalogue, setCatalogue] = useState([])
  const [catLoading, setCatLoading] = useState(false)
  const [view, setView] = useState('events') // 'events' | 'outrights'
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([fetchBfEvents(), fetchBfOutrights()])
      .then(([evts, outs]) => {
        setEvents(evts || [])
        setOutrights(outs || [])
        setLoading(false)
      })
      .catch(e => {
        setError('Could not connect to Betfair Exchange')
        setLoading(false)
      })
  }, [])

  async function selectEvent(eventId) {
    if (selectedEvent === eventId) { setSelectedEvent(null); setCatalogue([]); return }
    setSelectedEvent(eventId)
    setCatLoading(true)
    const cats = await fetchBfCatalogue(eventId)
    setCatalogue(cats || [])
    setCatLoading(false)
  }

  const useMock = !loading && events.length === 0 && !error

  return (
    <div className="section">
      {/* Header */}
      <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 10, padding: '12px 16px', marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#93c5fd' }}>
              📈 Betfair Exchange — Live World Cup Markets
            </div>
            <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>
              Connected via BetBud server proxy · App key: XDDM8EHzaw8tokvQ ·
              <strong style={{ color: '#93c5fd' }}> Back</strong> = bet to win ·
              <strong style={{ color: '#fca5a5' }}> Lay</strong> = act as bookmaker
            </div>
          </div>
          <span style={{
            fontSize: 10, fontWeight: 800, padding: '3px 10px', borderRadius: 20,
            background: loading ? 'rgba(245,158,11,.2)' : error ? 'rgba(239,68,68,.2)' : 'rgba(16,185,129,.2)',
            color: loading ? '#fcd34d' : error ? '#fca5a5' : '#6ee7b7',
            border: `1px solid ${loading ? '#f59e0b' : error ? '#ef4444' : '#10b981'}`,
          }}>
            {loading ? '⟳ CONNECTING' : error ? '✗ FALLBACK' : `✓ LIVE`}
          </span>
        </div>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--muted)' }}>
          <div className="spinner" />
          <div style={{ marginTop: 12, fontSize: 13 }}>Connecting to Betfair Exchange…</div>
        </div>
      )}

      {!loading && (error || useMock) && (
        <>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 16 }}>
            {error ? `⚠ ${error} — showing reference odds below.` : '⚠ No live markets found — showing reference odds.'}
          </div>
          {Object.entries(BETFAIR_MOCK_MARKETS).map(([match, markets]) => (
            <BetfairMarketCard key={match} match={match} markets={markets} />
          ))}
        </>
      )}

      {!loading && !error && (events.length > 0 || outrights.length > 0) && (
        <>
          {/* Sub-tab */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
            <button className={`btn ${view === 'events' ? 'btn-gold' : 'btn-ghost'}`} style={{ fontSize: 12 }} onClick={() => setView('events')}>
              ⚽ Match Events ({events.length})
            </button>
            <button className={`btn ${view === 'outrights' ? 'btn-gold' : 'btn-ghost'}`} style={{ fontSize: 12 }} onClick={() => setView('outrights')}>
              🏆 Outright Markets ({outrights.length})
            </button>
          </div>

          {view === 'events' && (
            <>
              <div className="grid-3" style={{ marginBottom: 16 }}>
                {events.map((e, i) => (
                  <LiveEventCard
                    key={i} event={e}
                    selected={selectedEvent === e.event?.id}
                    onSelect={selectEvent}
                  />
                ))}
              </div>

              {catLoading && <div className="spinner" />}

              {!catLoading && catalogue.length > 0 && (
                <div>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 10 }}>
                    {catalogue.length} markets found — click to expand prices
                  </div>
                  {catalogue.map((mkt, i) => (
                    <LiveMarketCard key={i} mkt={mkt} />
                  ))}
                </div>
              )}

              {events.length === 0 && (
                <div style={{ color: 'var(--muted)', fontSize: 13, padding: 20, textAlign: 'center' }}>
                  No upcoming World Cup events found on the exchange yet.
                  Markets will appear once fixtures are listed closer to kick-off.
                </div>
              )}
            </>
          )}

          {view === 'outrights' && (
            <div>
              {outrights.length === 0
                ? <div style={{ color: 'var(--muted)', fontSize: 13, padding: 20, textAlign: 'center' }}>No outright markets found.</div>
                : outrights.map((mkt, i) => <LiveMarketCard key={i} mkt={{ ...mkt, runners: mkt.runners || mkt.book?.runners || [] }} />)
              }
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default function Bets() {
  const [activeTab, setActiveTab] = useState('top5')

  const tabs = [
    { id: 'top5',      label: '🎯 Top 5 Bets' },
    { id: 'outrights', label: '🏆 Outrights' },
    { id: 'group',     label: '📋 Group Bets' },
    { id: 'golden',    label: '⚽ Golden Boot' },
    { id: 'betfair',   label: '📈 Betfair Exchange' },
    { id: 'corners',   label: '⚽ Corners & Cards' },
  ]

  return (
    <div className="page-content">
      <div className="section-title">💰 BetBud Smart Picks & Betfair Markets</div>

      <div style={{ background: '#1e2a3b', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 13, color: 'var(--muted)' }}>
        ⚠️ BetBud picks are AI predictions. Betfair odds in decimal format.
        <strong style={{ color: 'var(--gold)' }}> Back</strong> = bet on outcome to happen.
        <strong style={{ color: '#ef9a9a' }}> Lay</strong> = bet against outcome.
        <span style={{ color: 'var(--accent2)', fontWeight: 600 }}> Click any row to expand full analysis, methodology &amp; risk factors.</span>
        {' '}Always gamble responsibly. 18+
      </div>

      {/* Tab nav */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            className={`btn ${activeTab === t.id ? 'btn-gold' : 'btn-ghost'}`}
            style={{ fontSize: 12, padding: '6px 12px' }}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Top 5 Bets */}
      {activeTab === 'top5' && <Top5Bets />}

      {/* Outrights */}
      {activeTab === 'outrights' && (
        <div className="section">
          <div className="card">
            <div className="card-title">🏆 World Cup Winner — Outright Bets</div>
            <div style={{ fontSize: 12, color: 'var(--accent)', marginBottom: 10 }}>
              Click any team row to see full AI analysis, methodology breakdown and risk factors ▼
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="table" style={{ minWidth: 560 }}>
                <thead>
                  <tr>
                    <th>Team</th><th>US Odds</th><th>Dec Odds</th><th>BetBud Prob</th>
                    <th>Form</th><th>Verdict</th><th>Summary</th>
                  </tr>
                </thead>
                <tbody>
                  {OUTRIGHTS.map(o => <OutrightRow key={o.team} o={o} />)}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Group bets */}
      {activeTab === 'group' && (
        <div className="section">
          <div className="card">
            <div className="card-title">📋 Group Stage Value Bets</div>
            <div style={{ fontSize: 12, color: 'var(--accent)', marginBottom: 10 }}>
              Click any bet row to expand full analysis, key factors and risk assessment ▼
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="table" style={{ minWidth: 560 }}>
                <thead>
                  <tr><th>Match</th><th>Bet</th><th>US Odds</th><th>Dec</th><th>Conf</th><th>Tag</th><th>Summary</th></tr>
                </thead>
                <tbody>
                  {GROUP_BETS.map((b, i) => <GroupBetRow key={i} b={b} />)}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Golden Boot bets */}
      {activeTab === 'golden' && (
        <div className="section">
          <div className="card">
            <div className="card-title">⚽ Golden Boot Betting — Top 5 Picks</div>
            <div style={{ fontSize: 12, color: 'var(--accent)', marginBottom: 10 }}>
              Click any player card to see full AI analysis and scoring prediction breakdown ▼
            </div>
            <div className="grid-3" style={{ marginTop: 12 }}>
              {GOLDEN_BOOT_BETS.map(p => <GoldenBootCard key={p.player} p={p} />)}
            </div>
          </div>
        </div>
      )}

      {/* Betfair Exchange markets */}
      {activeTab === 'betfair' && <BetfairLiveTab />}

      {/* Corners & Cards */}
      {activeTab === 'corners' && (
        <div className="section">
          <div className="card">
            <div className="card-title">⚽ Corners & Cards Markets</div>
            <div style={{ fontSize: 12, color: 'var(--accent)', marginBottom: 10 }}>
              Click any row to expand full analysis, corner generation methodology and risks ▼
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="table" style={{ minWidth: 500 }}>
                <thead>
                  <tr><th>Match</th><th>Market</th><th>Betfair Odds</th><th>BetBud</th><th>Confidence</th><th>Summary</th></tr>
                </thead>
                <tbody>
                  {CORNERS_DATA.map((r, i) => <CornersRow key={i} r={r} i={i} />)}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
