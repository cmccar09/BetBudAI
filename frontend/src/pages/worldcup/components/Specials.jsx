import { useState } from 'react'
import {
  GROUP_STAGE_SPECIALS, GOAL_SPECIALS,
  MESSI_RONALDO_SPECIALS, NOVELTY_SPECIALS
} from '../data/specials'

function SpecialRow({ s }) {
  const [expanded, setExpanded] = useState(false)
  const isYes = s.betbudPred === 'YES'

  return (
    <div style={{
      borderBottom: '1px solid var(--border2)', padding: '10px 4px',
      cursor: 'pointer',
    }} onClick={() => setExpanded(!expanded)}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        {/* BetBud verdict */}
        <span className={`badge ${isYes ? 'badge-yes' : 'badge-no'}`} style={{ minWidth: 38 }}>
          {s.betbudPred}
        </span>

        {/* Market name */}
        <span style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{s.market}</span>

        {/* Betfair odds */}
        <span style={{ color: 'var(--gold)', fontWeight: 700, fontSize: 13, minWidth: 45, textAlign: 'right' }}>
          {s.betfairOdds}
        </span>

        {/* Confidence bar */}
        <div style={{ minWidth: 80 }}>
          <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 2 }}>{s.confidence}% conf</div>
          <div className="conf-bar" style={{ width: 80 }}>
            <div className="conf-fill" style={{ width: `${s.confidence}%` }} />
          </div>
        </div>

        <span style={{ color: 'var(--muted)', fontSize: 14 }}>{expanded ? '▲' : '▼'}</span>
      </div>

      {expanded && (
        <div style={{
          marginTop: 8, fontSize: 12, color: 'var(--muted)', padding: '8px 10px',
          background: 'var(--card2)', borderRadius: 6, lineHeight: 1.6, borderLeft: `3px solid ${isYes ? 'var(--purple)' : 'var(--red)'}`
        }}>
          🤖 {s.reasoning}
        </div>
      )}
    </div>
  )
}

function Section({ title, icon, items, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const yesCount = items.filter(i => i.betbudPred === 'YES').length
  const noCount = items.filter(i => i.betbudPred === 'NO').length

  return (
    <div className="card section">
      <div
        className="card-title"
        style={{ cursor: 'pointer', justifyContent: 'space-between', marginBottom: open ? 12 : 0 }}
        onClick={() => setOpen(!open)}
      >
        <span>{icon} {title}</span>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge badge-yes">YES ×{yesCount}</span>
          <span className="badge badge-no">NO ×{noCount}</span>
          <span style={{ fontSize: 16, color: 'var(--muted)' }}>{open ? '▲' : '▼'}</span>
        </div>
      </div>

      {open && (
        <>
          <div style={{ display: 'flex', gap: 8, fontSize: 11, color: 'var(--muted)', marginBottom: 10, flexWrap: 'wrap' }}>
            <span>Market</span>
            <span style={{ marginLeft: 'auto' }}>Betfair Odds (decimal) · BetBud YES/NO · Confidence</span>
            <span style={{ color: 'var(--muted)', fontSize: 10 }}>Click any row to expand reasoning</span>
          </div>
          {items.map(s => <SpecialRow key={s.id} s={s} />)}
        </>
      )}
    </div>
  )
}

export default function Specials() {
  const [activeTab, setActiveTab] = useState('all')

  const tabs = [
    { id: 'all', label: 'All Specials' },
    { id: 'group', label: '📋 Group Stage' },
    { id: 'goals', label: '⚽ Goals' },
    { id: 'mr', label: '🐐 Messi & Ronaldo' },
    { id: 'novelty', label: '🎭 Novelty' },
  ]

  return (
    <div className="page-content">
      <div className="section-title">🎰 FIFA World Cup 2026 Specials — BetBud Predictions</div>

      <div style={{ padding: '10px 14px', background: 'var(--card2)', border: '1px solid var(--border)', borderRadius: 8, marginBottom: 20, fontSize: 13, color: 'var(--muted)' }}>
        ⚠️ Specials markets sourced from Paddy Power & Betfair Exchange. Decimal odds = Betfair Exchange.
        YES/NO = BetBud AI prediction. Click any market for BetBud's full reasoning. Gamble responsibly.
      </div>

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

      {(activeTab === 'all' || activeTab === 'group') && (
        <Section
          title="Group Stage Specials"
          icon="📋"
          items={GROUP_STAGE_SPECIALS}
          defaultOpen={activeTab === 'group'}
        />
      )}

      {(activeTab === 'all' || activeTab === 'goals') && (
        <Section
          title="#WhatOddsPaddy — Goals Specials (Excl. Shootouts)"
          icon="⚽"
          items={GOAL_SPECIALS}
          defaultOpen={activeTab === 'goals'}
        />
      )}

      {(activeTab === 'all' || activeTab === 'mr') && (
        <Section
          title="Messi & Ronaldo Specials — The Last Dance?"
          icon="🐐"
          items={MESSI_RONALDO_SPECIALS}
          defaultOpen={activeTab === 'mr'}
        />
      )}

      {(activeTab === 'all' || activeTab === 'novelty') && (
        <Section
          title="Novelty Specials"
          icon="🎭"
          items={NOVELTY_SPECIALS}
          defaultOpen={activeTab === 'novelty'}
        />
      )}

      {/* Summary stats */}
      <div className="section">
        <div className="section-title">📊 BetBud Special Picks Summary</div>
        <div className="grid-4">
          {[
            { label: 'Group Stage Specials', yes: GROUP_STAGE_SPECIALS.filter(x=>x.betbudPred==='YES').length, no: GROUP_STAGE_SPECIALS.filter(x=>x.betbudPred==='NO').length, total: GROUP_STAGE_SPECIALS.length },
            { label: 'Goals Specials', yes: GOAL_SPECIALS.filter(x=>x.betbudPred==='YES').length, no: GOAL_SPECIALS.filter(x=>x.betbudPred==='NO').length, total: GOAL_SPECIALS.length },
            { label: 'Messi & Ronaldo', yes: MESSI_RONALDO_SPECIALS.filter(x=>x.betbudPred==='YES').length, no: MESSI_RONALDO_SPECIALS.filter(x=>x.betbudPred==='NO').length, total: MESSI_RONALDO_SPECIALS.length },
            { label: 'Novelty Specials', yes: NOVELTY_SPECIALS.filter(x=>x.betbudPred==='YES').length, no: NOVELTY_SPECIALS.filter(x=>x.betbudPred==='NO').length, total: NOVELTY_SPECIALS.length },
          ].map(s => (
            <div key={s.label} className="card-sm" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>{s.label}</div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: 'var(--accent)' }}>{s.yes}</div>
                  <div style={{ fontSize: 10, color: 'var(--muted)' }}>YES picks</div>
                </div>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: 'var(--red)' }}>{s.no}</div>
                  <div style={{ fontSize: 10, color: 'var(--muted)' }}>NO picks</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
