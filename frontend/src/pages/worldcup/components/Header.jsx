import { useState } from 'react'
import { getApiKey, setApiKey, testConnection } from '../services/apiFootball'

export default function Header({ lastUpdated, onRefresh }) {
  const [key, setKey]           = useState(getApiKey())
  const [status, setStatus]     = useState(getApiKey() ? '✓ Connected' : 'Demo mode')
  const [isOk, setIsOk]         = useState(!!getApiKey())
  const [showKey]   = useState(false)
  const [showPanel, setShowPanel] = useState(false)

  async function save() {
    setApiKey(key)
    setStatus('Testing…')
    const ok = await testConnection()
    setIsOk(ok)
    setStatus(ok ? '✓ Connected' : '✗ Invalid key')
    if (ok && onRefresh) onRefresh()
  }

  return (
    <header style={{
      background: '#1e293b',
      borderBottom: '2px solid #6366f1',
      padding: '10px 16px',
      position: 'relative',
      boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 8, flexShrink: 0,
            background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18, boxShadow: '0 2px 12px rgba(99,102,241,.5)',
          }}>⚽</div>

          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 20, fontWeight: 900, lineHeight: 1.1, letterSpacing: .5, whiteSpace: 'nowrap' }}>
              <span style={{ color: '#f1f5f9' }}>BetBud</span>
              <span style={{ color: '#f97316' }}>WorldCup</span>
            </div>
            <div className="header-subtitle" style={{ fontSize: 10, color: '#64748b', marginTop: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              2026 FIFA World Cup · USA, Canada, Mexico · 11 Jun – 19 Jul 2026
            </div>
          </div>
        </div>

        {/* Right side — desktop: inline, mobile: toggle panel */}
        <div className="header-controls-desktop" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 5 }}>
          {/* Status row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              background: '#ef4444', color: '#fff', fontSize: 9, fontWeight: 800,
              padding: '2px 8px', borderRadius: 20, letterSpacing: 1,
              animation: 'wc-pulse 1.5s infinite', flexShrink: 0,
            }}>LIVE</span>
            <span style={{ fontSize: 11, color: '#64748b', whiteSpace: 'nowrap' }}>
              {lastUpdated ? `Updated: ${lastUpdated}` : 'Auto-refresh 15 min'}
            </span>
          </div>
          {/* API key row */}
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <span style={{ fontSize: 11, color: '#818cf8', fontWeight: 700 }}>🔑</span>
            <input
              type={showKey ? 'text' : 'password'}
              placeholder="API-Sports key"
              value={key}
              onChange={e => setKey(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && save()}
              style={{
                background: '#0f172a', border: '1px solid #334155',
                color: '#f1f5f9', padding: '4px 10px',
                borderRadius: 50, fontSize: 11, width: 160, outline: 'none',
              }}
            />
            <button
              onClick={save}
              style={{
                background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
                color: '#fff', border: 'none',
                padding: '4px 12px', borderRadius: 50,
                fontSize: 11, fontWeight: 700, cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(99,102,241,.4)',
                whiteSpace: 'nowrap',
              }}
            >Connect</button>
            <span style={{ fontSize: 10, color: isOk ? '#10b981' : '#94a3b8', whiteSpace: 'nowrap' }}>{status}</span>
          </div>
        </div>

        {/* Mobile: compact right side */}
        <div className="header-controls-mobile" style={{ display: 'none', alignItems: 'center', gap: 8 }}>
          <span style={{
            background: '#ef4444', color: '#fff', fontSize: 8, fontWeight: 800,
            padding: '2px 7px', borderRadius: 20, letterSpacing: 1,
            animation: 'wc-pulse 1.5s infinite', flexShrink: 0,
          }}>LIVE</span>
          <button
            onClick={() => setShowPanel(!showPanel)}
            style={{
              background: showPanel ? 'rgba(99,102,241,.3)' : 'rgba(99,102,241,.1)',
              border: '1px solid rgba(99,102,241,.4)',
              color: '#818cf8', borderRadius: 8,
              padding: '5px 10px', fontSize: 11, fontWeight: 700, cursor: 'pointer',
            }}
          >🔑 API</button>
        </div>
      </div>

      {/* Mobile API panel — slides in */}
      {showPanel && (
        <div style={{
          marginTop: 10, padding: '10px 12px',
          background: '#0f172a', border: '1px solid #334155', borderRadius: 8,
        }}>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              type={showKey ? 'text' : 'password'}
              placeholder="Paste your API-Sports key here"
              value={key}
              onChange={e => setKey(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && save()}
              style={{
                background: '#1e293b', border: '1px solid #334155',
                color: '#f1f5f9', padding: '6px 12px',
                borderRadius: 50, fontSize: 12, flex: 1, minWidth: 160, outline: 'none',
              }}
            />
            <button
              onClick={save}
              style={{
                background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
                color: '#fff', border: 'none',
                padding: '6px 14px', borderRadius: 50,
                fontSize: 12, fontWeight: 700, cursor: 'pointer',
              }}
            >Connect</button>
          </div>
          <div style={{ fontSize: 11, color: isOk ? '#10b981' : '#94a3b8', marginTop: 6 }}>{status}</div>
        </div>
      )}
    </header>
  )
}
