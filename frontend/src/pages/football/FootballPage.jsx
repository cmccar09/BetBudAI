import { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

const TABS = [
  { id: 'pl',       label: 'Premier League',   emoji: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  { id: 'fixtures', label: 'Fixtures',          emoji: '📅' },
  { id: 'ucl',      label: 'Champions League', emoji: '⭐' },
  { id: 'el',       label: 'Europa League',    emoji: '🟠' },
];

// ─── Fallback static data ─────────────────────────────────────────────────────
const FB_PL = {
  title: {
    team: 'Arsenal', odds: '3/1', confidence: 72,
    reasoning: 'Defending champions — Arsenal ended Man City\'s dominance in 2025/26 and have the squad depth and momentum to back up. Mikel Arteta\'s system is now at peak maturity.',
  },
  top_four: [
    { pos: 1, team: 'Arsenal',          odds: '3/1',  badge: '🔴', note: 'Defending champions — Arteta squad at peak maturity' },
    { pos: 2, team: 'Manchester City',  odds: '4/1',  badge: '🔵', note: 'Enzo Maresca takes over — Haaland the key, lost Rodri' },
    { pos: 3, team: 'Liverpool',        odds: '5/1',  badge: '❤️', note: 'Massive rebuild — Wirtz + Isak is a statement of intent' },
    { pos: 4, team: 'Chelsea',          odds: '10/1', badge: '🔵', note: 'Maresca left for City — new chapter at Stamford Bridge' },
  ],
  top_six: [
    { team: 'Manchester United', odds: '12/1' },
    { team: 'Tottenham Hotspur', odds: '14/1' },
    { team: 'Newcastle United',  odds: '16/1' },
    { team: 'Aston Villa',       odds: '20/1' },
  ],
  relegation: [
    { team: 'Coventry City',  odds: '4/9',  note: 'Promoted — first PL season, brutal early fixtures' },
    { team: 'Hull City',      odds: '1/2',  note: 'Promoted — squad thin at PL level' },
    { team: 'Sunderland',     odds: '4/7',  note: 'Back in top flight — punching at ceiling' },
    { team: 'Ipswich Town',   odds: '5/6',  note: 'Second season up — quality gap still apparent' },
  ],
  golden_boot: [
    { player: 'Erling Haaland',  team: 'Man City',  odds: '3/1'  },
    { player: 'Alexander Isak',  team: 'Liverpool', odds: '6/1'  },
    { player: 'Bukayo Saka',     team: 'Arsenal',   odds: '8/1'  },
    { player: 'Florian Wirtz',   team: 'Liverpool', odds: '8/1'  },
    { player: 'Cole Palmer',     team: 'Chelsea',   odds: '10/1' },
  ],
};

const FB_UCL = {
  english_clubs: [
    { team: 'Manchester City',  how: 'PL Champions'  },
    { team: 'Arsenal',          how: 'PL 2nd'        },
    { team: 'Liverpool',        how: 'PL 3rd'        },
    { team: 'Chelsea',          how: 'PL 4th'        },
  ],
  contenders: [
    { pos: 1, team: 'Real Madrid',     odds: '3/1'  },
    { pos: 2, team: 'Manchester City', odds: '9/2'  },
    { pos: 3, team: 'Bayern Munich',   odds: '5/1'  },
    { pos: 4, team: 'PSG',            odds: '7/1'  },
    { pos: 5, team: 'Arsenal',         odds: '12/1' },
    { pos: 6, team: 'Liverpool',       odds: '14/1' },
  ],
  final_date: '2027-05-31',
  group_draw: 'August 2026',
};

const FB_EL = {
  english_clubs: [
    { team: 'Manchester United', how: 'PL 5th / Cup winner' },
    { team: 'Tottenham Hotspur', how: 'PL 6th' },
  ],
  contenders: [
    { pos: 1, team: 'Bayer Leverkusen',  odds: '5/1'  },
    { pos: 2, team: 'Atletico Madrid',   odds: '6/1'  },
    { pos: 3, team: 'Roma',             odds: '8/1'  },
    { pos: 4, team: 'Manchester United', odds: '9/1'  },
    { pos: 5, team: 'Tottenham Hotspur', odds: '12/1' },
    { pos: 6, team: 'Lazio',            odds: '14/1' },
  ],
  final_date: '2027-05-21',
  group_draw: 'August 2026',
};

// ─── Helper components ────────────────────────────────────────────────────────
function SectionLabel({ children }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 800, color: '#34d399', textTransform: 'uppercase',
      letterSpacing: 1.5, marginBottom: 12 }}>
      {children}
    </div>
  );
}

function Card({ children, style = {} }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 14,
      padding: 18,
      ...style,
    }}>
      {children}
    </div>
  );
}

function PredictionBadge({ result }) {
  const map = {
    home_win: { label: 'Home Win', color: '#34d399' },
    away_win: { label: 'Away Win', color: '#60a5fa' },
    draw:     { label: 'Draw',     color: '#fbbf24' },
  };
  const cfg = map[result] || { label: result, color: 'rgba(255,255,255,0.5)' };
  return (
    <span style={{ fontSize: 10, fontWeight: 800, padding: '2px 8px', borderRadius: 6,
      background: `${cfg.color}22`, color: cfg.color, textTransform: 'uppercase', letterSpacing: 0.5 }}>
      {cfg.label}
    </span>
  );
}

function FixtureCard({ fx, isMobile }) {
  const pred = fx.prediction;
  const completed = fx.completed;
  const dateStr = fx.date ? new Date(fx.date).toLocaleDateString('en-GB',
    { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';

  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: 10, padding: isMobile ? '12px 14px' : '14px 18px', marginBottom: 8 }}>

      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 8 }}>{dateStr}</div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 }}>
          <span style={{ fontSize: 14, fontWeight: 800, color: 'white', flexShrink: 0 }}>{fx.home}</span>
          <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.3)', flexShrink: 0 }}>vs</span>
          <span style={{ fontSize: 14, fontWeight: 700, color: 'rgba(255,255,255,0.8)', flexShrink: 0 }}>{fx.away}</span>
        </div>
        {completed
          ? <span style={{ fontSize: 18, fontWeight: 900, color: '#fbbf24', flexShrink: 0 }}>
              {fx.home_score}–{fx.away_score}
            </span>
          : pred && <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
              <PredictionBadge result={pred.result} />
              <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>
                {pred.score} · {pred.confidence}% conf
              </span>
            </div>
        }
      </div>
    </div>
  );
}

function StandingsTable({ standings, isMobile }) {
  if (!standings || standings.length === 0) return null;
  const cols = isMobile
    ? ['pos','team','played','pts']
    : ['pos','team','played','won','drawn','lost','gd','pts'];
  const hdrs = { pos:'#', team:'Club', played:'P', won:'W', drawn:'D', lost:'L', gd:'GD', pts:'Pts' };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr>
            {cols.map(c => (
              <th key={c} style={{ textAlign: c === 'team' ? 'left' : 'center', padding: '6px 8px',
                fontSize: 11, color: 'rgba(255,255,255,0.4)', fontWeight: 700, borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                {hdrs[c]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {standings.map((row, i) => {
            const inUCL = i < 4;
            const inEL  = i >= 4 && i < 6;
            const releg = i >= 17;
            const rowColor = inUCL ? '#34d39922' : inEL ? '#60a5fa22' : releg ? '#f8717122' : 'transparent';
            return (
              <tr key={row.team} style={{ background: rowColor }}>
                {cols.map(c => (
                  <td key={c} style={{
                    textAlign: c === 'team' ? 'left' : 'center',
                    padding: '8px 8px',
                    color: c === 'pts' ? '#fbbf24' : c === 'team' ? 'white' : 'rgba(255,255,255,0.7)',
                    fontWeight: c === 'pts' ? 900 : c === 'team' ? 700 : 400,
                    borderBottom: '1px solid rgba(255,255,255,0.04)',
                  }}>
                    {row[c]}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 11, color: 'rgba(255,255,255,0.4)', flexWrap: 'wrap' }}>
        <span><span style={{ color: '#34d399' }}>■</span> UCL</span>
        <span><span style={{ color: '#60a5fa' }}>■</span> Europa League</span>
        <span><span style={{ color: '#f87171' }}>■</span> Relegation zone</span>
      </div>
    </div>
  );
}

function OutrightBoard({ contenders, title, isMobile }) {
  return (
    <div>
      <SectionLabel>{title}</SectionLabel>
      {contenders.map((c, i) => (
        <div key={c.team} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 14px', marginBottom: 6, borderRadius: 8,
          background: i === 0 ? 'rgba(251,191,36,0.1)' : 'rgba(255,255,255,0.03)',
          border: i === 0 ? '1px solid rgba(251,191,36,0.3)' : '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 800, color: i === 0 ? '#fbbf24' : 'rgba(255,255,255,0.35)', width: 20 }}>
              {i === 0 ? '🏆' : `${i + 1}`}
            </span>
            <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{c.team}</span>
          </div>
          <span style={{ fontSize: 14, fontWeight: 900, color: '#34d399' }}>{c.odds}</span>
        </div>
      ))}
    </div>
  );
}

function EnglishClubsBadge({ clubs }) {
  return (
    <div>
      <SectionLabel>🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Clubs</SectionLabel>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {clubs.map(c => (
          <div key={c.team} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 14px', borderRadius: 8, background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)' }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{c.team}</span>
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>{c.how}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Match bet cards ──────────────────────────────────────────────────────────
function MatchBetCard({ fx, isMobile }) {
  const bets = fx.bets || {};
  const dateStr = fx.date ? new Date(fx.date).toLocaleDateString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  }) : '';

  const bttsLabel = bets.value?.pct != null ? `BTTS · ${bets.value.pct}% likely` : 'BTTS';
  // generate_match_bets() falls back from 'First Goalscorer' to 'Correct Score' when
  // the tipped scorer's team confidence is below its gate — read the actual market
  // name back rather than hardcoding "1st Goalscorer", or the label lies about what's
  // actually being shown (found 2026-08-28: a Correct Score fallback pick displayed
  // under a "1st Goalscorer" header).
  const isCorrectScore = bets.longshot?.market === 'Correct Score';
  const picks = [
    { key: 'safe',     emoji: '🛡️', label: 'Match Result',    color: '#34d399', bg: 'rgba(52,211,153,0.1)',  border: 'rgba(52,211,153,0.25)',  data: bets.safe     },
    { key: 'value',    emoji: '💰', label: bttsLabel,          color: '#fbbf24', bg: 'rgba(251,191,36,0.1)',  border: 'rgba(251,191,36,0.25)',  data: bets.value    },
    { key: 'longshot', emoji: isCorrectScore ? '🔢' : '🎯', label: bets.longshot?.market || '1st Goalscorer', color: '#a78bfa', bg: 'rgba(167,139,250,0.1)', border: 'rgba(167,139,250,0.25)', data: bets.longshot },
  ];

  return (
    <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 14, overflow: 'hidden', marginBottom: 14 }}>
      {/* Fixture header */}
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.08)', background: 'rgba(0,0,0,0.2)' }}>
        {dateStr && <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginBottom: 5 }}>{dateStr}</div>}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: isMobile ? 14 : 16, fontWeight: 900, color: 'white' }}>{fx.home}</span>
          {fx.prediction?.score ? (
            <span style={{ fontSize: 16, fontWeight: 900, color: '#fbbf24', padding: '2px 10px',
              background: 'rgba(251,191,36,0.12)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: 7, letterSpacing: 1 }}>
              {fx.prediction.score}
            </span>
          ) : (
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', padding: '1px 7px',
              background: 'rgba(255,255,255,0.06)', borderRadius: 5 }}>vs</span>
          )}
          <span style={{ fontSize: isMobile ? 14 : 15, fontWeight: 700, color: 'rgba(255,255,255,0.8)' }}>{fx.away}</span>
          {fx.prediction && <PredictionBadge result={fx.prediction.result} />}
        </div>
        {fx.prediction?.score && (
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 4 }}>
            AI predicted score · {fx.prediction.confidence}% confidence
          </div>
        )}
      </div>
      {/* 3 picks */}
      <div style={{ padding: isMobile ? '10px 12px' : '12px 18px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {picks.map(p => p.data ? (
          <div key={p.key} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '10px 12px',
            background: p.bg, border: `1px solid ${p.border}`, borderRadius: 10 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 10, fontWeight: 800, color: p.color, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  {p.emoji} {p.label}
                </span>
                <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)' }}>· {p.data.market}</span>
              </div>
              <div style={{ fontSize: isMobile ? 13 : 14, fontWeight: 900, color: 'white', marginBottom: 3 }}>
                {p.data.pick}
                {p.data.team && <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginLeft: 6 }}>({p.data.team})</span>}
              </div>
              {p.data.reason && (
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', lineHeight: 1.4 }}>{p.data.reason}</div>
              )}
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: 15, fontWeight: 900, color: p.color }}>{p.data.odds}</div>
              {p.data.pct != null && (
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 2 }}>{p.data.pct}% prob</div>
              )}
            </div>
          </div>
        ) : null)}
      </div>
    </div>
  );
}

function WeeklyBetsSection({ weeklyBets, isMobile }) {
  if (!weeklyBets || weeklyBets.length === 0) return null;
  return (
    <Card style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.28)' }}>
      <SectionLabel>🎯 This Week's Best Bets</SectionLabel>
      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginBottom: 14 }}>
        3-pick cards per fixture — Safe Pick · Value (with BTTS %) · Longshot
      </div>
      {weeklyBets.map(fx => (
        <MatchBetCard key={fx.id || `${fx.home}-${fx.away}`} fx={fx} isMobile={isMobile} />
      ))}
    </Card>
  );
}

// ─── Premier League Tab ───────────────────────────────────────────────────────
function PremierLeagueTab({ apiData, isMobile }) {
  const pl = apiData?.pl_predictions || {};
  const title     = pl.title     || FB_PL.title;
  const topFour   = pl.top_four  || FB_PL.top_four;
  const topSix    = pl.top_six   || FB_PL.top_six;
  const relegate  = pl.relegation || FB_PL.relegation;
  const gBoot     = pl.golden_boot || FB_PL.golden_boot;
  const fixtures    = apiData?.pl_fixtures || [];
  const weeklyBets  = apiData?.pl_weekly_bets || [];
  const standings   = apiData?.pl_standings || [];
  const isLive      = standings.length > 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

      {/* Season banner */}
      <Card style={{ background: 'linear-gradient(135deg,rgba(52,211,153,0.12),rgba(251,191,36,0.08))',
        border: '1px solid rgba(52,211,153,0.3)', textAlign: 'center', padding: '20px 18px' }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#34d399', textTransform: 'uppercase',
          letterSpacing: 2, marginBottom: 6 }}>🏆 Premier League 2026/27</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>
          {isLive ? 'Live season — predictions updated weekly' : 'Season starts August 2026 · Pre-season predictions'}
        </div>
      </Card>

      {/* Weekly best bets */}
      <WeeklyBetsSection weeklyBets={weeklyBets} isMobile={isMobile} />

      {/* Fixtures (when live) */}
      {fixtures.length > 0 && (
        <Card>
          <SectionLabel>📅 This Week's Fixtures</SectionLabel>
          {fixtures.map(fx => (
            <FixtureCard key={fx.id || `${fx.home}-${fx.away}`} fx={fx} isMobile={isMobile} />
          ))}
        </Card>
      )}

      {/* Live standings */}
      {isLive && (
        <Card>
          <SectionLabel>📊 League Table</SectionLabel>
          <StandingsTable standings={standings} isMobile={isMobile} />
        </Card>
      )}

      {/* Relegation */}
      <Card>
        <SectionLabel>⬇️ Relegation Danger Zone</SectionLabel>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {relegate.map((t, i) => (
            <div key={t.team} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '10px 14px', borderRadius: 8,
              background: i === 0 ? 'rgba(248,113,113,0.1)' : 'rgba(255,255,255,0.03)',
              border: i === 0 ? '1px solid rgba(248,113,113,0.3)' : '1px solid rgba(255,255,255,0.06)',
            }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>⬇️ {t.team}</div>
                {t.note && <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>{t.note}</div>}
              </div>
              <span style={{ fontSize: 13, fontWeight: 800, color: '#f87171' }}>{t.odds}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Golden Boot */}
      <Card>
        <SectionLabel>⚽ Golden Boot</SectionLabel>
        {gBoot.map((g, i) => (
          <div key={g.player} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '9px 14px', marginBottom: 6, borderRadius: 8,
            background: i === 0 ? 'rgba(251,191,36,0.08)' : 'rgba(255,255,255,0.03)',
            border: i === 0 ? '1px solid rgba(251,191,36,0.2)' : '1px solid rgba(255,255,255,0.05)',
          }}>
            <div>
              <span style={{ fontSize: 14, fontWeight: 700, color: 'white' }}>{g.player}</span>
              <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginLeft: 8 }}>{g.team}</span>
            </div>
            <span style={{ fontSize: 14, fontWeight: 900, color: '#34d399' }}>{g.odds}</span>
          </div>
        ))}
      </Card>

      {/* Title prediction — moved to the end: season-long forecast, not this week's action */}
      <Card style={{ background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.25)' }}>
        <SectionLabel>🏆 BetBud Title Pick</SectionLabel>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 900, color: '#fbbf24' }}>{title.team}</div>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)', marginTop: 4, maxWidth: 380 }}>
              {title.reasoning}
            </div>
          </div>
          <div style={{ textAlign: 'center', padding: '10px 20px', borderRadius: 10,
            background: 'rgba(251,191,36,0.15)', border: '1px solid rgba(251,191,36,0.3)' }}>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 2 }}>ODDS</div>
            <div style={{ fontSize: 26, fontWeight: 900, color: '#fbbf24' }}>{title.odds}</div>
            <div style={{ fontSize: 11, color: '#34d399', marginTop: 2 }}>{title.confidence}% confidence</div>
          </div>
        </div>
      </Card>

      {/* Top 4 predictions */}
      <Card>
        <SectionLabel>Top 4 Predictions</SectionLabel>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {topFour.map(t => (
            <div key={t.team} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '11px 14px', borderRadius: 8,
              background: t.pos === 1 ? 'rgba(251,191,36,0.08)' : 'rgba(255,255,255,0.03)',
              border: t.pos === 1 ? '1px solid rgba(251,191,36,0.2)' : '1px solid rgba(255,255,255,0.06)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 14, fontWeight: 900, color: t.pos === 1 ? '#fbbf24' : 'rgba(255,255,255,0.35)', width: 22 }}>
                  {t.pos === 1 ? '🥇' : t.pos === 2 ? '🥈' : t.pos === 3 ? '🥉' : `${t.pos}`}
                </span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 800, color: 'white' }}>{t.badge} {t.team}</div>
                  {t.note && <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)', marginTop: 2 }}>{t.note}</div>}
                </div>
              </div>
              <span style={{ fontSize: 14, fontWeight: 900, color: '#34d399' }}>{t.odds}</span>
            </div>
          ))}
        </div>

        {topSix && topSix.length > 0 && (
          <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', marginBottom: 8, fontWeight: 700 }}>ALSO WORTH WATCHING</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {topSix.map(t => (
                <div key={t.team} style={{ fontSize: 13, padding: '5px 12px', borderRadius: 8,
                  background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <span style={{ color: 'white', fontWeight: 700 }}>{t.team}</span>
                  <span style={{ color: '#34d399', marginLeft: 8, fontWeight: 800 }}>{t.odds}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

// ─── Champions League Tab ─────────────────────────────────────────────────────
function ChampionsLeagueTab({ apiData, isMobile }) {
  const ucl = apiData?.ucl_data || {};
  const contenders = ucl.contenders || FB_UCL.contenders;
  const englishClubs = ucl.english_clubs || FB_UCL.english_clubs;
  const fixtures = ucl.fixtures || [];
  const finalDate = ucl.final_date || FB_UCL.final_date;
  const groupDraw = ucl.group_draw || FB_UCL.group_draw;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

      {/* UCL banner */}
      <Card style={{ background: 'linear-gradient(135deg,rgba(96,165,250,0.12),rgba(52,211,153,0.06))',
        border: '1px solid rgba(96,165,250,0.3)', textAlign: 'center', padding: '20px 18px' }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#60a5fa', textTransform: 'uppercase',
          letterSpacing: 2, marginBottom: 6 }}>⭐ UEFA Champions League 2026/27</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>
          Group stage draw: {groupDraw} · Final: {new Date(finalDate).toLocaleDateString('en-GB',
            { day: 'numeric', month: 'long', year: 'numeric' })}
        </div>
      </Card>

      {/* Winner prediction */}
      <Card>
        <OutrightBoard contenders={contenders} title="🏆 UCL Winner Odds" isMobile={isMobile} />
      </Card>

      {/* English clubs */}
      <Card>
        <EnglishClubsBadge clubs={englishClubs} />
      </Card>

      {/* Live fixtures */}
      {fixtures.length > 0 && (
        <Card>
          <SectionLabel>📅 UCL Fixtures</SectionLabel>
          {fixtures.map(fx => (
            <FixtureCard key={fx.id || `${fx.home}-${fx.away}`} fx={fx} isMobile={isMobile} />
          ))}
        </Card>
      )}

      {fixtures.length === 0 && (
        <Card>
          <div style={{ textAlign: 'center', padding: '24px 0', color: 'rgba(255,255,255,0.4)', fontSize: 14 }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>⭐</div>
            <div>UCL group stage begins September 2026</div>
            <div style={{ fontSize: 12, marginTop: 6 }}>Fixtures will appear here once the group draw is complete</div>
          </div>
        </Card>
      )}
    </div>
  );
}

// ─── Europa League Tab ────────────────────────────────────────────────────────
function EuropaLeagueTab({ apiData, isMobile }) {
  const el = apiData?.el_data || {};
  const contenders = el.contenders || FB_EL.contenders;
  const englishClubs = el.english_clubs || FB_EL.english_clubs;
  const fixtures = el.fixtures || [];
  const finalDate = el.final_date || FB_EL.final_date;
  const groupDraw = el.group_draw || FB_EL.group_draw;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

      {/* EL banner */}
      <Card style={{ background: 'linear-gradient(135deg,rgba(251,146,60,0.12),rgba(52,211,153,0.06))',
        border: '1px solid rgba(251,146,60,0.3)', textAlign: 'center', padding: '20px 18px' }}>
        <div style={{ fontSize: 12, fontWeight: 800, color: '#fb923c', textTransform: 'uppercase',
          letterSpacing: 2, marginBottom: 6 }}>🟠 UEFA Europa League 2026/27</div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.6)' }}>
          Group stage draw: {groupDraw} · Final: {new Date(finalDate).toLocaleDateString('en-GB',
            { day: 'numeric', month: 'long', year: 'numeric' })}
        </div>
      </Card>

      {/* Winner odds */}
      <Card>
        <OutrightBoard contenders={contenders} title="🏆 EL Winner Odds" isMobile={isMobile} />
      </Card>

      {/* English clubs */}
      <Card>
        <EnglishClubsBadge clubs={englishClubs} />
      </Card>

      {/* Live fixtures */}
      {fixtures.length > 0 && (
        <Card>
          <SectionLabel>📅 EL Fixtures</SectionLabel>
          {fixtures.map(fx => (
            <FixtureCard key={fx.id || `${fx.home}-${fx.away}`} fx={fx} isMobile={isMobile} />
          ))}
        </Card>
      )}

      {fixtures.length === 0 && (
        <Card>
          <div style={{ textAlign: 'center', padding: '24px 0', color: 'rgba(255,255,255,0.4)', fontSize: 14 }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🟠</div>
            <div>EL group stage begins September 2026</div>
            <div style={{ fontSize: 12, marginTop: 6 }}>Fixtures will appear here once the group draw is complete</div>
          </div>
        </Card>
      )}
    </div>
  );
}

// ─── Fixtures + Table Tab ─────────────────────────────────────────────────────
function FixturesTab({ apiData, isMobile }) {
  // pl_weekly_bets has predictions + bets from static fallback (ESPN blocked from Lambda)
  // pl_fixtures is from ESPN live feed (usually empty); merge both, weekly_bets takes priority
  const weeklyBets   = apiData?.pl_weekly_bets || [];
  const espnFixtures = apiData?.pl_fixtures || [];
  const standings    = apiData?.pl_standings || [];

  // Build a unified fixture list: weekly_bets first (they have predictions/bets),
  // then any ESPN fixtures not already covered
  const weeklyIds = new Set(weeklyBets.map(f => f.id));
  const extraEspn = espnFixtures.filter(f => !weeklyIds.has(f.id));
  const allFixtures = [...weeklyBets, ...extraEspn];

  // Split into completed and upcoming
  const completed = [...allFixtures].filter(f => f.completed)
    .sort((a, b) => b.date.localeCompare(a.date));
  const upcoming  = [...allFixtures].filter(f => !f.completed)
    .sort((a, b) => a.date.localeCompare(b.date));

  const fmtDate = d => d ? new Date(d).toLocaleDateString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  }) : '';

  const ResultRow = ({ fx }) => (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: isMobile ? '10px 12px' : '12px 16px', marginBottom: 6,
      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10,
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginBottom: 4 }}>{fmtDate(fx.date)}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 14, fontWeight: 800, color: 'white' }}>{fx.home}</span>
          <span style={{ fontSize: 18, fontWeight: 900, color: '#fbbf24', padding: '0 6px' }}>
            {fx.home_score} – {fx.away_score}
          </span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'rgba(255,255,255,0.7)' }}>{fx.away}</span>
        </div>
      </div>
    </div>
  );

  const UpcomingRow = ({ fx }) => {
    const bets = fx.bets;
    const pred = fx.prediction || {};
    const resultMap = { home_win: { lbl: `${fx.home} Win`, c: '#34d399' }, away_win: { lbl: `${fx.away} Win`, c: '#60a5fa' }, draw: { lbl: 'Draw', c: '#fbbf24' } };
    const r = resultMap[pred.result] || {};
    return (
      <div style={{
        padding: isMobile ? '10px 12px' : '12px 16px', marginBottom: 8,
        background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10,
      }}>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginBottom: 4 }}>{fmtDate(fx.date)}</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
          {/* Teams + predicted score */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 14, fontWeight: 800, color: 'white' }}>{fx.home}</span>
            {pred.score ? (
              <span style={{ fontSize: 16, fontWeight: 900, color: '#fbbf24', padding: '2px 10px',
                background: 'rgba(251,191,36,0.12)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: 7, letterSpacing: 1 }}>
                {pred.score}
              </span>
            ) : (
              <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', padding: '1px 6px',
                background: 'rgba(255,255,255,0.06)', borderRadius: 5 }}>vs</span>
            )}
            <span style={{ fontSize: 14, fontWeight: 700, color: 'rgba(255,255,255,0.8)' }}>{fx.away}</span>
          </div>
          {/* Result label + confidence */}
          {r.lbl && (
            <span style={{ fontSize: 11, fontWeight: 800, padding: '3px 9px', borderRadius: 6,
              background: `${r.c}22`, color: r.c, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {r.lbl} · {pred.confidence}%
            </span>
          )}
        </div>
        {pred.score && (
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginTop: 3 }}>
            AI predicted score · model confidence {pred.confidence}%
          </div>
        )}
        {bets && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 10 }}>
            {[
              { label: '🛡️ Match Result', pick: bets.safe?.pick,     odds: bets.safe?.odds,     c: '#34d399' },
              { label: `💰 BTTS${bets.value?.pct != null ? ` (${bets.value?.pct}% likely)` : ''}`, pick: bets.value?.pick, odds: bets.value?.odds, c: '#fbbf24' },
              { label: `${bets.longshot?.market === 'Correct Score' ? '🔢' : '🎯'} ${bets.longshot?.market || '1st Goalscorer'}`, pick: bets.longshot?.pick, odds: bets.longshot?.odds, c: '#a78bfa' },
            ].filter(b => b.pick).map(b => (
              <div key={b.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '7px 12px', borderRadius: 8,
                background: `${b.c}10`, border: `1px solid ${b.c}30` }}>
                <div>
                  <span style={{ fontSize: 11, color: b.c, fontWeight: 700, display: 'block', marginBottom: 1 }}>{b.label}</span>
                  <span style={{ fontSize: 13, color: 'white', fontWeight: 800 }}>{b.pick}</span>
                </div>
                {b.odds && <span style={{ fontSize: 15, color: b.c, fontWeight: 900, marginLeft: 12 }}>{b.odds}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

      {/* Upcoming */}
      <Card>
        <SectionLabel>📅 Upcoming Fixtures</SectionLabel>
        {upcoming.length === 0
          ? <div style={{ textAlign: 'center', padding: '20px 0', color: 'rgba(255,255,255,0.35)', fontSize: 13 }}>No upcoming fixtures yet</div>
          : upcoming.map(fx => <UpcomingRow key={fx.id || `${fx.home}-${fx.away}`} fx={fx} />)
        }
      </Card>

      {/* Results */}
      {completed.length > 0 && (
        <Card>
          <SectionLabel>✅ Recent Results</SectionLabel>
          {completed.map(fx => <ResultRow key={fx.id || `${fx.home}-${fx.away}`} fx={fx} />)}
        </Card>
      )}

      {/* League table */}
      {standings.length > 0 && (
        <Card>
          <SectionLabel>📊 League Table</SectionLabel>
          <StandingsTable standings={standings} isMobile={isMobile} />
        </Card>
      )}

      {standings.length === 0 && (
        <Card>
          <SectionLabel>📊 League Table</SectionLabel>
          <div style={{ textAlign: 'center', padding: '20px 0', color: 'rgba(255,255,255,0.35)', fontSize: 13 }}>
            League table will appear once matches have been played
          </div>
        </Card>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function FootballPage() {
  const [activeTab, setActiveTab] = useState('pl');
  const [apiData, setApiData]     = useState(null);
  const [loading, setLoading]     = useState(true);
  const isMobile = window.innerWidth < 640;

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/sports/football`)
      .then(r => r.json())
      .then(d => { setApiData(d.success ? d : null); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ background: '#0f172a', minHeight: '100vh', padding: isMobile ? '16px 12px' : '24px 20px', maxWidth: 960, margin: '0 auto' }}>

      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: isMobile ? 24 : 32, fontWeight: 900, color: 'white', marginBottom: 6 }}>
          ⚽ Football
        </div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)' }}>
          Premier League · Champions League · Europa League · Weekly predictions
        </div>
        {apiData?.meta?.last_updated && (
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 4 }}>
            Updated: {new Date(apiData.meta.last_updated).toLocaleString('en-GB')}
          </div>
        )}
      </div>

      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20, overflowX: 'auto', paddingBottom: 2 }}>
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
            padding: isMobile ? '8px 14px' : '9px 18px',
            borderRadius: 10, border: 'none', cursor: 'pointer', whiteSpace: 'nowrap',
            fontSize: isMobile ? 12 : 13, fontWeight: 700,
            background: activeTab === tab.id ? '#34d399' : 'rgba(255,255,255,0.07)',
            color: activeTab === tab.id ? '#0f172a' : 'rgba(255,255,255,0.7)',
            transition: 'all 0.15s',
          }}>
            {tab.emoji} {isMobile ? tab.label.split(' ')[0] : tab.label}
          </button>
        ))}
      </div>

      {/* Loading state */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'rgba(255,255,255,0.4)' }}>
          Loading football data…
        </div>
      )}

      {/* Tab content */}
      {!loading && activeTab === 'pl'       && <PremierLeagueTab   apiData={apiData} isMobile={isMobile} />}
      {!loading && activeTab === 'fixtures' && <FixturesTab         apiData={apiData} isMobile={isMobile} />}
      {!loading && activeTab === 'ucl'      && <ChampionsLeagueTab  apiData={apiData} isMobile={isMobile} />}
      {!loading && activeTab === 'el'       && <EuropaLeagueTab     apiData={apiData} isMobile={isMobile} />}
    </div>
  );
}
