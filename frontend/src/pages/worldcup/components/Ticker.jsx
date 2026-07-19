// gameDate controls visibility — items older than yesterday are hidden.
// TIP items (no gameDate) are always shown.
const ALL_ITEMS = [
  // ── Round of 32 results ───────────────────────────────────────────────────
  { gameDate:'2026-06-28', label:'🇿🇦 South Africa vs 🇨🇦 Canada',      detail:'Jun 28 · R32 · FT', score:'0–1', status:'FT', pred:'✅' },
  { gameDate:'2026-06-29', label:'🇧🇷 Brazil vs 🇯🇵 Japan',             detail:'Jun 29 · R32 · FT', score:'2–1', status:'FT', pred:'✅' },
  { gameDate:'2026-06-29', label:'🇩🇪 Germany vs 🇵🇾 Paraguay',         detail:'Jun 29 · R32 · FT (3-4 pens)', score:'1–1', status:'FT', pred:'❌' },
  { gameDate:'2026-06-29', label:'🇳🇱 Netherlands vs 🇲🇦 Morocco',      detail:'Jun 29 · R32 · FT (2-3 pens)', score:'1–1', status:'FT', pred:'❌' },
  { gameDate:'2026-06-30', label:'🇨🇮 Ivory Coast vs 🇳🇴 Norway',       detail:'Jun 30 · R32 · FT', score:'1–2', status:'FT', pred:'✅' },
  { gameDate:'2026-06-30', label:'🇫🇷 France vs 🇸🇪 Sweden',            detail:'Jun 30 · R32 · FT (Mbappé ×2)', score:'3–0', status:'FT', pred:'✅' },
  { gameDate:'2026-06-30', label:'🇲🇽 Mexico vs 🇪🇨 Ecuador',           detail:'Jun 30 · R32 · FT', score:'2–0', status:'FT', pred:'✅' },
  { gameDate:'2026-07-01', label:'🏴󠁧󠁢󠁥󠁮󠁧󠁿 England vs 🇨🇩 DR Congo',        detail:'Jul 1 · R32 · FT', score:'3–0', status:'FT', pred:'✅' },
  { gameDate:'2026-07-01', label:'🇧🇪 Belgium vs 🇸🇳 Senegal',          detail:'Jul 1 · R32 · FT', score:'2–1', status:'FT', pred:'✅' },
  { gameDate:'2026-07-01', label:'🇺🇸 USA vs 🇧🇦 Bosnia',               detail:'Jul 1 · R32 · FT', score:'2–0', status:'FT', pred:'✅' },
  { gameDate:'2026-07-02', label:'🇪🇸 Spain vs 🇦🇹 Austria',            detail:'Jul 2 · R32 · FT', score:'2–0', status:'FT', pred:'✅' },
  { gameDate:'2026-07-02', label:'🇵🇹 Portugal vs 🇭🇷 Croatia',         detail:'Jul 2 · R32 · FT', score:'2–1', status:'FT', pred:'✅' },
  { gameDate:'2026-07-02', label:'🇨🇭 Switzerland vs 🇩🇿 Algeria',      detail:'Jul 2 · R32 · FT', score:'2–1', status:'FT', pred:'✅' },
  { gameDate:'2026-07-03', label:'🇦🇺 Australia vs 🇪🇬 Egypt',          detail:'Jul 3 · R32 · FT (pens)', score:'1–1', status:'FT', pred:'❌' },
  { gameDate:'2026-07-03', label:'🇦🇷 Argentina vs 🇨🇻 Cape Verde',     detail:'Jul 3 · R32 · FT (AET)', score:'3–2', status:'FT', pred:'✅' },
  { gameDate:'2026-07-03', label:'🇨🇴 Colombia vs 🇬🇭 Ghana',           detail:'Jul 3 · R32 · FT', score:'1–0', status:'FT', pred:'✅' },
  // ── Round of 16 results ───────────────────────────────────────────────────
  { gameDate:'2026-07-04', label:'🇨🇦 Canada vs 🇲🇦 Morocco',           detail:'Jul 4 · R16 · FT', score:'0–3', status:'FT', pred:'❌' },
  { gameDate:'2026-07-04', label:'🇵🇾 Paraguay vs 🇫🇷 France',          detail:'Jul 4 · R16 · FT', score:'0–1', status:'FT', pred:'✅' },
  { gameDate:'2026-07-05', label:'🇧🇷 Brazil vs 🇳🇴 Norway',            detail:'Jul 5 · R16 · FT ⚡UPSET', score:'1–2', status:'FT', pred:'❌' },
  { gameDate:'2026-07-05', label:'🇲🇽 Mexico vs 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England',          detail:'Jul 5 · R16 · FT', score:'2–3', status:'FT', pred:'✅' },
  { gameDate:'2026-07-06', label:'🇵🇹 Portugal vs 🇪🇸 Spain',           detail:'Jul 6 · R16 · FT', score:'0–1', status:'FT', pred:'✅' },
  { gameDate:'2026-07-06', label:'🇺🇸 USA vs 🇧🇪 Belgium',              detail:'Jul 6 · R16 · FT', score:'1–4', status:'FT', pred:'✅' },
  { gameDate:'2026-07-07', label:'🇦🇷 Argentina vs 🇪🇬 Egypt',          detail:'Jul 7 · R16 · FT', score:'3–2', status:'FT', pred:'✅' },
  { gameDate:'2026-07-07', label:'🇨🇭 Switzerland vs 🇨🇴 Colombia',     detail:'Jul 7 · R16 · FT (pens)', score:'0–0', status:'FT', pred:'❌' },
  // ── Quarter-finals ────────────────────────────────────────────────────────
  { gameDate:'2026-07-09', label:'🇫🇷 France vs 🇲🇦 Morocco',           detail:'Jul 9 · QF · FT',  score:'2–0', status:'FT', pred:'✅' },
  { gameDate:'2026-07-10', label:'🇪🇸 Spain vs 🇧🇪 Belgium',            detail:'Jul 10 · QF · FT', score:'2–1', status:'FT', pred:'✅' },
  { gameDate:'2026-07-11', label:'🇳🇴 Norway vs 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England',          detail:'Jul 11 · QF · FT', score:'1–2', status:'FT', pred:'✅' },
  { gameDate:'2026-07-12', label:'🇦🇷 Argentina vs 🇨🇭 Switzerland',    detail:'Jul 12 · QF · FT', score:'3–1', status:'FT', pred:'↗️' },
  // ── Semi-Finals ───────────────────────────────────────────────────────────
  { gameDate:'2026-07-14', label:'🇫🇷 France vs 🇪🇸 Spain',             detail:'Jul 14 · SF · FT ⚡UPSET', score:'0–2', status:'FT', pred:'❌' },
  { gameDate:'2026-07-15', label:'🏴󠁧󠁢󠁥󠁮󠁧󠁿 England vs 🇦🇷 Argentina',       detail:'Jul 15 · SF · FT (Messi ×2 assists)', score:'1–2', status:'FT', pred:'✅' },
  // ── 3rd Place + Final ─────────────────────────────────────────────────────
  { gameDate:'2026-07-18', label:'🏴󠁧󠁢󠁥󠁮󠁧󠁿 England vs 🇫🇷 France',              detail:'Jul 18 · 3rd Place · FT AET', score:'6–4', status:'FT', pred:'❌' },
  { gameDate:'2026-07-19', label:'🏆 FIFA World Cup Final',               detail:'TODAY · 3pm ET · MetLife Stadium', score:null, status:'TODAY', pred:'BetBud: Spain 🇪🇸 to win · ~2/1' },
  // ── Tip ──────────────────────────────────────────────────────────────────
  { label:'🏆 BetBud Final Bet', detail:'Spain to WIN World Cup 2026 · 37-match unbeaten · 6 clean sheets this tournament · odds ~2/1', score:null, status:'TIP', pred:'Spain vs Argentina · TODAY 3pm ET MetLife' },
]

export default function Ticker({ fixtures = [] }) {
  // Show: yesterday's results + all future fixtures + TIP (no date = always)
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  const cutoffStr = yesterday.toISOString().slice(0, 10)

  const items = ALL_ITEMS.filter(f => {
    if (f.status === 'TIP') return true         // tips always show
    if (!f.gameDate) return true                // no date = always show
    return f.gameDate >= cutoffStr              // yesterday + future only
  })

  const doubled = [...items, ...items]

  return (
    <div className="ticker">
      <div className="ticker-track">
        {doubled.map((f, i) => (
          <span key={i} className="ticker-item">
            <span>{f.label}</span>
            {f.score !== null
              ? <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{f.score}</span>
              : f.status === 'LIVE'
                ? <span style={{ color: 'var(--red)', fontWeight: 700 }}>LIVE</span>
                : f.status === 'TODAY'
                  ? <span style={{ color: 'var(--gold)', fontWeight: 700 }}>TODAY</span>
                  : f.status === 'TIP'
                    ? <span style={{ color: 'var(--gold)', fontWeight: 700 }}>💡</span>
                    : null
            }
            <span style={{ color: 'var(--muted)', fontSize: 11 }}>{f.detail}</span>
            {f.pred && f.score === null && (
              <span style={{ color: '#7dd3fc', fontSize: 11 }}>🤖 {f.pred}</span>
            )}
            {f.pred && f.score !== null && (
              <span style={{ fontSize: 11 }}>{f.pred === '✅' ? '✅' : f.pred === '❌' ? '❌' : ''}</span>
            )}
          </span>
        ))}
      </div>
    </div>
  )
}
