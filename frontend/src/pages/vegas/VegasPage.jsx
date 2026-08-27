import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

const GRADE_CONFIG = {
  ELITE:  { label: 'ELITE',  bg: 'rgba(251,191,36,0.15)',  border: '#fbbf24', color: '#fbbf24' },
  STRONG: { label: 'STRONG', bg: 'rgba(52,211,153,0.12)',  border: '#34d399', color: '#34d399' },
  VALUE:  { label: 'VALUE',  bg: 'rgba(96,165,250,0.12)',  border: '#60a5fa', color: '#60a5fa' },
};

const STATUS_CONFIG = {
  won:    { label: 'WON',    bg: 'rgba(52,211,153,0.2)', border: '#34d399', color: '#34d399' },
  placed: { label: 'PLACED', bg: 'rgba(251,191,36,0.2)', border: '#fbbf24', color: '#fbbf24' },
  lost:   { label: 'LOST',   bg: 'rgba(248,113,113,0.2)', border: '#f87171', color: '#f87171' },
};

function formatTime(raceTime) {
  if (!raceTime) return '';
  try {
    const d = new Date(raceTime);
    if (isNaN(d)) return raceTime;
    return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/London' });
  } catch { return raceTime; }
}

function toFractional(decimal) {
  if (!decimal || decimal <= 1) return '';
  const frac = decimal - 1;
  const denom = 4;
  const num = Math.round(frac * denom);
  const g = (a, b) => b ? g(b, a % b) : a;
  const d = g(num, denom);
  return `${num/d}/${denom/d}`;
}

function EdgeBar({ edge, maxEdge = 40 }) {
  const pct = Math.min(100, (edge / maxEdge) * 100);
  return (
    <div style={{ height: 4, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden', marginTop: 4 }}>
      <div style={{ height: '100%', width: `${pct}%`, background: 'linear-gradient(90deg,#34d399,#059669)', borderRadius: 2, transition: 'width 0.5s ease' }} />
    </div>
  );
}

function ValueBetCard({ pick, isMobile }) {
  const grade = GRADE_CONFIG[pick.benter_grade] || GRADE_CONFIG.VALUE;
  const status = STATUS_CONFIG[pick.result_status];
  const kellyDisplay = pick.kelly_units > 0 ? `${pick.kelly_units}u` : '—';
  const frac = toFractional(pick.odds);
  const edgeColor = status ? status.border : grade.border;

  return (
    <div style={{
      background: 'rgba(30,41,69,0.9)',
      border: `1px solid ${edgeColor}33`,
      borderLeft: `3px solid ${edgeColor}`,
      borderRadius: 8,
      padding: isMobile ? '14px 16px' : '18px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      opacity: pick.result_status === 'lost' ? 0.75 : 1,
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div>
          <div style={{ fontSize: isMobile ? 16 : 18, fontWeight: 700, color: '#e2e8f0', fontFamily: 'monospace', lineHeight: 1.2 }}>
            {pick.horse}
          </div>
          <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.5)', marginTop: 3 }}>
            {pick.venue} · {formatTime(pick.race_time)}
            {pick.race_type ? ` · ${pick.race_type}` : ''}
          </div>
          {status && (
            <div style={{ fontSize: 11, color: status.color, marginTop: 4, fontFamily: 'monospace' }}>
              {pick.finish_position ? `Finished ${pick.finish_position === 1 ? '1st' : pick.finish_position === 2 ? '2nd' : pick.finish_position === 3 ? '3rd' : `${pick.finish_position}th`}` : status.label}
              {pick.result_status !== 'won' && pick.result_winner_name ? ` · winner: ${pick.result_winner_name}` : ''}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <div style={{ display: 'flex', gap: 6 }}>
            {status && (
              <span style={{ background: status.bg, border: `1px solid ${status.border}`, color: status.color, fontSize: 9, letterSpacing: '0.12em', padding: '3px 7px', borderRadius: 3, fontFamily: 'monospace', fontWeight: 700 }}>
                {status.label}
              </span>
            )}
            <span style={{ background: grade.bg, border: `1px solid ${grade.border}`, color: grade.color, fontSize: 9, letterSpacing: '0.12em', padding: '3px 7px', borderRadius: 3, fontFamily: 'monospace', fontWeight: 600 }}>
              {grade.label}
            </span>
          </div>
          <span style={{ fontSize: 18, fontWeight: 700, color: '#fbbf24', fontFamily: 'monospace' }}>
            {frac || pick.odds}
          </span>
        </div>
      </div>

      {/* Probability comparison */}
      <div style={{ background: 'rgba(0,0,0,0.25)', borderRadius: 6, padding: '10px 12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ fontSize: 10, letterSpacing: '0.1em', color: 'rgba(226,232,240,0.45)', fontFamily: 'monospace' }}>BENTER MODEL</span>
          <span style={{ fontSize: 10, letterSpacing: '0.1em', color: 'rgba(226,232,240,0.45)', fontFamily: 'monospace' }}>MARKET</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 20, fontWeight: 700, color: '#34d399', fontFamily: 'monospace' }}>{pick.combined_prob}%</span>
          <span style={{ fontSize: 12, color: 'rgba(226,232,240,0.5)', fontFamily: 'monospace' }}>vs</span>
          <span style={{ fontSize: 20, fontWeight: 700, color: 'rgba(226,232,240,0.6)', fontFamily: 'monospace' }}>{pick.market_prob}%</span>
        </div>
        <EdgeBar edge={pick.value_edge} />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 5 }}>
          <div style={{ fontSize: 10, color: '#34d399', fontFamily: 'monospace', fontWeight: 600 }}>
            +{pick.value_edge}% EDGE OVER MARKET
          </div>
          {pick.field_scored != null && (
            <div style={{ fontSize: 9, fontFamily: 'monospace', color: pick.coverage >= 70 ? 'rgba(52,211,153,0.6)' : pick.coverage >= 50 ? 'rgba(251,191,36,0.6)' : 'rgba(248,113,113,0.6)' }}>
              {pick.field_scored}/{pick.field_known} runners scored · {pick.coverage}% coverage
            </div>
          )}
        </div>
      </div>

      {/* Footer: score + Kelly */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <div>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>MODEL SCORE</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0', fontFamily: 'monospace' }}>{pick.score}</div>
          </div>
          <div>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>½-KELLY STAKE</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#fbbf24', fontFamily: 'monospace' }}>{kellyDisplay}</div>
          </div>
          <div>
            <div style={{ fontSize: 9, letterSpacing: '0.1em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>EV</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: pick.ev > 0 ? '#34d399' : '#f87171', fontFamily: 'monospace' }}>
              {pick.ev > 0 ? '+' : ''}{(pick.ev * 100).toFixed(1)}%
            </div>
          </div>
        </div>
        {pick.jockey && (
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', textAlign: 'right', maxWidth: 120 }}>
            {pick.jockey}
          </div>
        )}
      </div>

      {/* Benter advice */}
      {(pick.action || pick.benter_note) && (
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {pick.action && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <span style={{ fontSize: 9, letterSpacing: '0.1em', color: grade.color, fontFamily: 'monospace', flexShrink: 0, paddingTop: 2 }}>ACTION</span>
              <span style={{ fontSize: 12, color: '#e2e8f0', lineHeight: 1.5 }}>{pick.action}</span>
            </div>
          )}
          {pick.benter_note && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <span style={{ fontSize: 9, letterSpacing: '0.1em', color: 'rgba(251,191,36,0.7)', fontFamily: 'monospace', flexShrink: 0, paddingTop: 2 }}>BENTER</span>
              <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.55)', lineHeight: 1.5 }}>{pick.benter_note}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ExactaCard({ exacta, isMobile }) {
  return (
    <div style={{
      background: 'rgba(30,41,69,0.7)',
      border: '1px solid rgba(96,165,250,0.2)',
      borderRadius: 8,
      padding: isMobile ? '12px 14px' : '16px 18px',
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
    }}>
      <div style={{ fontSize: 9, letterSpacing: '0.14em', color: '#60a5fa', fontFamily: 'monospace', fontWeight: 600 }}>
        EXACTA · {exacta.venue} · {formatTime(exacta.race_time)}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', fontFamily: 'monospace' }}>{exacta.horse_win}</span>
        <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>→ 1st</span>
        <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.3)', fontFamily: 'monospace' }}>+</span>
        <span style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0', fontFamily: 'monospace' }}>{exacta.horse_place}</span>
        <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>→ 2nd</span>
      </div>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div>
          <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>HARVILLE PROB</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#60a5fa', fontFamily: 'monospace' }}>{exacta.exacta_prob}%</div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>FAIR PRICE</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#fbbf24', fontFamily: 'monospace' }}>{exacta.fair_price}×</div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>BETFAIR EST</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: exacta.value ? '#34d399' : 'rgba(226,232,240,0.5)', fontFamily: 'monospace' }}>{exacta.betfair_est}×</div>
        </div>
        <div>
          <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>WIN / PLACE ODDS</div>
          <div style={{ fontSize: 13, color: '#e2e8f0', fontFamily: 'monospace' }}>{exacta.odds_win} / {exacta.odds_place}</div>
        </div>
        {exacta.value && (
          <div style={{ background: 'rgba(52,211,153,0.15)', border: '1px solid #34d399', borderRadius: 6, padding: '3px 8px', fontSize: 10, fontWeight: 700, color: '#34d399', fontFamily: 'monospace', letterSpacing: '0.1em' }}>
            BET — mkt {exacta.betfair_est}× vs fair {exacta.fair_price}×
          </div>
        )}
        {!exacta.value && (
          <div style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace' }}>
            est. mkt below fair price — skip
          </div>
        )}
      </div>
    </div>
  );
}

const CALIB_COLOR = { 'GOOD': '#34d399', 'SLIGHT OVERCONFIDENCE': '#fbbf24', 'OVERCONFIDENT': '#f97316', 'POOR — check partial field coverage': '#f87171' };

export default function VegasPage() {
  const [data, setData]             = useState(null);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [showMethod, setShowMethod] = useState(false);
  const [learning, setLearning]     = useState(null);
  const [showLearn, setShowLearn]   = useState(false);
  const [results, setResults]       = useState(null);
  const isMobile = window.innerWidth < 640;

  const fetchPicks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/vegas`);
      const json = await res.json();
      if (json.success) {
        setData(json);
        setLastUpdate(new Date());
        setError(null);
      } else {
        setError(json.error || 'No Benter picks available today');
      }
    } catch (e) {
      setError('Failed to connect — check back shortly');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPicks();
    const iv = setInterval(fetchPicks, 60000);
    return () => clearInterval(iv);
  }, [fetchPicks]);

  useEffect(() => {
    fetch(`${API_BASE}/api/vegas/learning`)
      .then(r => r.json())
      .then(d => { if (d.success) setLearning(d); })
      .catch(() => {});
    fetch(`${API_BASE}/api/vegas/results`)
      .then(r => r.json())
      .then(d => { if (d.success) setResults(d); })
      .catch(() => {});
  }, []);

  const containerStyle = {
    maxWidth: 900,
    margin: '0 auto',
    padding: isMobile ? '16px 12px 60px' : '24px 24px 80px',
    fontFamily: 'system-ui, sans-serif',
    color: '#e2e8f0',
  };

  const sectionHead = (label) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, marginTop: 28 }}>
      <span style={{ fontSize: 9, letterSpacing: '0.16em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace', textTransform: 'uppercase' }}>{label}</span>
      <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.07)' }} />
    </div>
  );

  return (
    <div style={containerStyle}>

      {/* Header */}
      <div style={{ marginBottom: 24, paddingBottom: 20, borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
        <div style={{ fontSize: 10, letterSpacing: '0.16em', color: '#fbbf24', fontFamily: 'monospace', marginBottom: 6 }}>
          BETBUDAI · BENTER METHOD
        </div>
        <h1 style={{ fontSize: isMobile ? 24 : 30, fontWeight: 700, color: '#e2e8f0', margin: 0, fontFamily: 'monospace', lineHeight: 1.1 }}>
          Vegas
        </h1>
        <p style={{ fontSize: 13, color: 'rgba(226,232,240,0.5)', margin: '8px 0 0', lineHeight: 1.5 }}>
          Value picks where our model diverges from the market — inspired by Bill Benter's $1B horse racing system.
        </p>
        <div style={{ display: 'flex', gap: 12, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          {lastUpdate && (
            <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace' }}>
              Updated {lastUpdate.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          <button
            onClick={() => { setLoading(true); fetchPicks(); }}
            style={{ fontSize: 10, color: '#34d399', background: 'none', border: '1px solid rgba(52,211,153,0.3)', padding: '3px 10px', borderRadius: 4, cursor: 'pointer', fontFamily: 'monospace', letterSpacing: '0.1em' }}
          >
            REFRESH
          </button>
          <button
            onClick={() => setShowMethod(v => !v)}
            style={{ fontSize: 10, color: 'rgba(226,232,240,0.5)', background: 'none', border: '1px solid rgba(255,255,255,0.1)', padding: '3px 10px', borderRadius: 4, cursor: 'pointer', fontFamily: 'monospace', letterSpacing: '0.1em' }}
          >
            {showMethod ? 'HIDE METHOD' : 'HOW IT WORKS'}
          </button>
        </div>
      </div>

      {/* Yesterday's results summary + running ROI */}
      {results && (
        <div style={{ marginBottom: 20 }}>

          {/* Running ROI strip */}
          {results.running && results.running.settled > 0 && (
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
              {[
                { label: 'VEGAS ROI', value: `${results.running.roi > 0 ? '+' : ''}${results.running.roi}%`, color: results.running.roi > 0 ? '#34d399' : '#f87171' },
                { label: 'RECORD', value: `${results.running.won}W / ${results.running.lost}L`, color: '#e2e8f0' },
                { label: 'P&L (level stakes)', value: `${results.running.pnl > 0 ? '+' : ''}${results.running.pnl}u`, color: results.running.pnl > 0 ? '#34d399' : '#f87171' },
                { label: 'PICKS SETTLED', value: results.running.settled, color: 'rgba(226,232,240,0.6)' },
              ].map(s => (
                <div key={s.label} style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 6, padding: '8px 14px', display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ fontSize: 9, letterSpacing: '0.12em', color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace' }}>{s.label}</span>
                  <span style={{ fontSize: 14, fontWeight: 700, color: s.color, fontFamily: 'monospace' }}>{s.value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Grade ROI breakdown */}
          {results.running?.grade_roi && Object.keys(results.running.grade_roi).length > 0 && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {Object.entries(results.running.grade_roi).map(([g, s]) => {
                const gc = GRADE_CONFIG[g] || GRADE_CONFIG.VALUE;
                return (
                  <div key={g} style={{ background: gc.bg, border: `1px solid ${gc.border}44`, borderRadius: 5, padding: '6px 12px', display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span style={{ fontSize: 9, fontFamily: 'monospace', color: gc.color, letterSpacing: '0.1em' }}>{g}</span>
                    <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#e2e8f0' }}>{s.w}W/{s.l}L</span>
                    <span style={{ fontSize: 11, fontFamily: 'monospace', color: s.roi > 0 ? '#34d399' : '#f87171', fontWeight: 700 }}>{s.roi > 0 ? '+' : ''}{s.roi}%</span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Yesterday's picks card */}
          {results.yesterday && !results.yesterday.no_picks && (
            <div style={{ background: 'rgba(15,23,42,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, overflow: 'hidden' }}>
              {/* Card header */}
              <div style={{ background: 'rgba(30,41,69,0.8)', padding: '10px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 9, letterSpacing: '0.16em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace', textTransform: 'uppercase' }}>Yesterday · {results.yesterday.date}</span>
                  <span style={{ fontSize: 9, letterSpacing: '0.1em', color: '#fbbf24', fontFamily: 'monospace' }}>VEGAS SELECTIONS</span>
                </div>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  {results.yesterday.won > 0 && <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#34d399' }}>✓ {results.yesterday.won} WON</span>}
                  {results.yesterday.lost > 0 && <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#f87171' }}>✗ {results.yesterday.lost} LOST</span>}
                  {results.yesterday.pending > 0 && <span style={{ fontSize: 11, fontFamily: 'monospace', color: 'rgba(226,232,240,0.4)' }}>⧖ {results.yesterday.pending} PENDING</span>}
                  {results.yesterday.roi !== null && (
                    <span style={{ fontSize: 13, fontWeight: 700, fontFamily: 'monospace', color: results.yesterday.roi > 0 ? '#34d399' : '#f87171' }}>
                      {results.yesterday.roi > 0 ? '+' : ''}{results.yesterday.roi}% ROI
                    </span>
                  )}
                </div>
              </div>

              {/* Pick rows */}
              <div>
                {results.yesterday.picks.map((p, i) => {
                  const gc = GRADE_CONFIG[p.grade] || GRADE_CONFIG.VALUE;
                  const isWon  = p.result === 'WON';
                  const isLost = p.result === 'LOST';
                  const isPending = p.result === 'PENDING';
                  const frac = toFractional(p.odds) || `${p.odds}`;
                  return (
                    <div key={i} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: isMobile ? 8 : 14,
                      padding: isMobile ? '10px 12px' : '10px 16px',
                      borderTop: '1px solid rgba(255,255,255,0.05)',
                      background: isWon ? 'rgba(52,211,153,0.04)' : isLost ? 'rgba(248,113,113,0.04)' : 'transparent',
                      flexWrap: isMobile ? 'wrap' : 'nowrap',
                    }}>
                      {/* Result pill */}
                      <span style={{
                        fontSize: 9, fontFamily: 'monospace', fontWeight: 700, letterSpacing: '0.1em',
                        padding: '3px 8px', borderRadius: 3, flexShrink: 0,
                        background: isWon ? 'rgba(52,211,153,0.15)' : isLost ? 'rgba(248,113,113,0.12)' : 'rgba(255,255,255,0.06)',
                        color: isWon ? '#34d399' : isLost ? '#f87171' : 'rgba(226,232,240,0.4)',
                        border: `1px solid ${isWon ? 'rgba(52,211,153,0.3)' : isLost ? 'rgba(248,113,113,0.25)' : 'rgba(255,255,255,0.1)'}`,
                      }}>
                        {isWon ? '✓ WON' : isLost ? '✗ LOST' : '⧖ PENDING'}
                      </span>

                      {/* Horse name */}
                      <span style={{ fontSize: isMobile ? 13 : 14, fontWeight: 600, color: '#e2e8f0', fontFamily: 'monospace', flex: 1, minWidth: 100 }}>{p.horse}</span>

                      {/* Venue + time */}
                      {!isMobile && (
                        <span style={{ fontSize: 11, color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace', flexShrink: 0 }}>
                          {p.venue} {p.race_time ? `· ${formatTime(p.race_time)}` : ''}
                        </span>
                      )}

                      {/* Grade badge */}
                      <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 3, border: `1px solid ${gc.border}55`, color: gc.color, fontFamily: 'monospace', flexShrink: 0 }}>
                        {p.grade}
                      </span>

                      {/* Odds */}
                      <span style={{ fontSize: 13, fontWeight: 700, color: '#fbbf24', fontFamily: 'monospace', flexShrink: 0, minWidth: 40, textAlign: 'right' }}>{frac}</span>

                      {/* Edge */}
                      <span style={{ fontSize: 10, color: 'rgba(52,211,153,0.7)', fontFamily: 'monospace', flexShrink: 0 }}>+{p.value_edge}%</span>

                      {/* P&L for this pick */}
                      {(isWon || isLost) && (
                        <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'monospace', flexShrink: 0, minWidth: 50, textAlign: 'right', color: isWon ? '#34d399' : '#f87171' }}>
                          {isWon ? `+${(p.odds - 1).toFixed(1)}u` : '−1u'}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Card footer */}
              {results.yesterday.pnl !== undefined && results.yesterday.pnl !== null && (
                <div style={{ background: 'rgba(30,41,69,0.6)', padding: '8px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>Level stakes · 1u per pick</span>
                  <span style={{ fontSize: 13, fontWeight: 700, fontFamily: 'monospace', color: results.yesterday.pnl >= 0 ? '#34d399' : '#f87171' }}>
                    Day P&L: {results.yesterday.pnl >= 0 ? '+' : ''}{results.yesterday.pnl}u
                  </span>
                </div>
              )}
            </div>
          )}

          {results.yesterday && results.yesterday.no_picks && (
            <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace', padding: '8px 0' }}>
              No Vegas picks were recorded yesterday.
            </div>
          )}
        </div>
      )}

      {/* How to make money — always visible */}
      <div style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(251,191,36,0.15)', borderRadius: 10, padding: isMobile ? '16px' : '20px 24px', marginBottom: 20 }}>
        <div style={{ fontSize: 10, letterSpacing: '0.16em', color: '#fbbf24', fontFamily: 'monospace', marginBottom: 14 }}>HOW THIS IS SUPPOSED TO MAKE MONEY</div>

        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: isMobile ? 14 : 20 }}>

          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#e2e8f0', marginBottom: 6 }}>The core idea</div>
            <p style={{ fontSize: 12, color: 'rgba(226,232,240,0.65)', lineHeight: 1.7, margin: 0 }}>
              You are not trying to predict which horse wins. You are finding horses the market has <em>underpriced</em> — where the collective public opinion (the odds) is systematically wrong. Bet consistently on every mispricing. The edge compounds over hundreds of bets.
            </p>
          </div>

          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#e2e8f0', marginBottom: 6 }}>Why individual results don't matter</div>
            <p style={{ fontSize: 12, color: 'rgba(226,232,240,0.65)', lineHeight: 1.7, margin: 0 }}>
              A horse with a true 30% win chance loses 70% of the time. That is not a failure — it is correct. You will back losers. Many of them. What matters is that over 200+ bets, winners pay more than the average loss. That's what a positive ROI means.
            </p>
          </div>

          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#e2e8f0', marginBottom: 6 }}>Kelly sizing is not optional</div>
            <p style={{ fontSize: 12, color: 'rgba(226,232,240,0.65)', lineHeight: 1.7, margin: 0 }}>
              The ½-Kelly stake shown on each card is mathematically proven to grow a bankroll faster than any fixed-stake system — while avoiding ruin. Staking more than Kelly on any single bet risks losing the bank before the edge has time to show. Staking less just slows growth.
            </p>
          </div>

          <div>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#e2e8f0', marginBottom: 6 }}>The rules Benter followed</div>
            <ul style={{ fontSize: 12, color: 'rgba(226,232,240,0.65)', lineHeight: 1.9, margin: 0, paddingLeft: 16 }}>
              <li>Back <strong style={{ color: '#e2e8f0' }}>every ELITE and STRONG pick</strong> — never skip because you "don't fancy it"</li>
              <li>Never bet VALUE grade alone — wait for STRONG/ELITE confirmation</li>
              <li>Use the exact Kelly stake — don't round down out of nerves</li>
              <li>Track ROI after 50+ bets, not after 5</li>
              <li>If the edge disappears over time, the model needs recalibration — not more gut picks</li>
            </ul>
          </div>

        </div>

        <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.07)', display: 'flex', gap: isMobile ? 10 : 24, flexWrap: 'wrap' }}>
          {[
            { label: 'Minimum picks before judging', value: '50+' },
            { label: 'Expected win rate', value: '25–35%' },
            { label: 'Grades worth staking', value: 'ELITE · STRONG' },
            { label: 'Minimum coverage to trust', value: '≥ 70%' },
          ].map(s => (
            <div key={s.label}>
              <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace', letterSpacing: '0.1em', marginBottom: 2 }}>{s.label}</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#fbbf24', fontFamily: 'monospace' }}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Methodology box (technical detail) */}
      {showMethod && (
        <div style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(251,191,36,0.2)', borderRadius: 8, padding: '16px 18px', marginBottom: 20, fontSize: 12, color: 'rgba(226,232,240,0.7)', lineHeight: 1.7 }}>
          <div style={{ fontSize: 10, letterSpacing: '0.14em', color: '#fbbf24', fontFamily: 'monospace', marginBottom: 8 }}>BENTER COMBINED MODEL — TECHNICAL</div>
          <p style={{ margin: '0 0 8px' }}><strong style={{ color: '#e2e8f0' }}>Formula:</strong> c_i = softmax(α·log(model_prob) + β·log(market_prob)) where α=β=1. Combined probability is then scaled by field coverage (runners scored ÷ runners known) to correct for partial field inflation, then compared to market price to find edge.</p>
          <p style={{ margin: '0 0 8px' }}><strong style={{ color: '#e2e8f0' }}>Coverage correction:</strong> If we scored 6 of 14 runners, combined_prob × (6/14) = honest probability accounting for the 8 runners we didn't see. Without this, softmax inflates every probability.</p>
          <p style={{ margin: '0 0 8px' }}><strong style={{ color: '#e2e8f0' }}>Exactas (coverage-aware Harville):</strong> P(win) = combined_prob_i (coverage-discounted). P(j places | i wins) = combined_prob_j / (1.0 − combined_prob_i) — denominator is the full field minus the winner, including unseen runners. Only shown where 3% ≤ P(exacta) ≤ 35%. Betfair Est = win_odds × place_odds × 0.6 (rough exchange forecast price). BET flag appears when the estimated market price exceeds the fair price — meaning the exchange is paying more than the model says it should.</p>
          <p style={{ margin: 0 }}><strong style={{ color: '#e2e8f0' }}>Stakes:</strong> Half-Kelly — f* = (b·p − q) / b, halved, capped at 12% of bank.</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>
          <div style={{ fontSize: 11, letterSpacing: '0.14em' }}>COMPUTING BENTER SCORES...</div>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div style={{ background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.3)', borderRadius: 8, padding: '20px 24px', textAlign: 'center' }}>
          <div style={{ color: '#f87171', fontSize: 13, fontFamily: 'monospace' }}>{error}</div>
        </div>
      )}

      {/* No value bets */}
      {!loading && !error && data && data.value_bets?.length === 0 && (
        <div style={{ background: 'rgba(30,41,69,0.7)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, padding: '40px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: 28, marginBottom: 12 }}>🎰</div>
          <div style={{ fontSize: 14, color: '#e2e8f0', fontFamily: 'monospace', marginBottom: 6 }}>No Value Bets Today</div>
          <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.45)' }}>
            The market has already priced in today's picks — no meaningful edge found.
            {data.races_analysed > 0 && ` (${data.races_analysed} races analysed)`}
          </div>
        </div>
      )}

      {/* Value bets — split by grade */}
      {!loading && !error && data?.value_bets?.length > 0 && (() => {
        const backAll  = (data.value_bets || []).filter(p => p.benter_grade === 'ELITE' || p.benter_grade === 'STRONG');
        const watchOnly = (data.value_bets || []).filter(p => p.benter_grade === 'VALUE');
        const ts = data.today_summary || {};
        return (
          <>
            {/* Today's results summary */}
            <div style={{ background: 'rgba(30,41,69,0.6)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, padding: '14px 16px', marginBottom: 16 }}>
              <div style={{ fontSize: 10, letterSpacing: '0.12em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace', marginBottom: 10 }}>TODAY'S RESULTS</div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2,1fr)' : 'repeat(5,1fr)', gap: 10 }}>
                {[
                  { label: 'Won', value: ts.won ?? 0, color: '#34d399' },
                  { label: 'Placed', value: ts.placed ?? 0, color: '#fbbf24' },
                  { label: 'Lost', value: ts.lost ?? 0, color: '#f87171' },
                  { label: 'Pending', value: ts.pending ?? 0, color: 'rgba(226,232,240,0.5)' },
                  { label: 'P&L', value: `${(ts.pnl_units ?? 0) > 0 ? '+' : ''}${ts.pnl_units ?? 0}u`, color: (ts.pnl_units ?? 0) >= 0 ? '#34d399' : '#f87171' },
                ].map(s => (
                  <div key={s.label}>
                    <div style={{ fontSize: 9, letterSpacing: '0.1em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>{s.label.toUpperCase()}</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: s.color, fontFamily: 'monospace' }}>{s.value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Daily exposure cap warning */}
            {data.daily_exposure?.scaled && (
              <div style={{ background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.25)', borderRadius: 8, padding: '12px 16px', marginBottom: 16, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <span style={{ fontSize: 16, flexShrink: 0 }}>⚠️</span>
                <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.75)', lineHeight: 1.6 }}>
                  <strong style={{ color: '#fbbf24' }}>Stakes scaled down for today's card.</strong> {backAll.length} picks qualified at once — backing every one at its raw half-Kelly size would call for {data.daily_exposure.raw_total_before_scaling}u combined in a single day. Every stake below has been scaled proportionally so the day's total stays at {data.daily_exposure.total_stake_units}u — bigger-edge picks are still sized bigger relative to the rest, it's the day as a whole that's capped.
                </div>
              </div>
            )}

            {/* Back all — ELITE + STRONG */}
            {backAll.length > 0 && (
              <>
                {sectionHead(`Today's Bets · ${backAll.length} qualifying · ${data.races_analysed || 0} races analysed`)}
                <div style={{ background: 'rgba(52,211,153,0.04)', border: '1px solid rgba(52,211,153,0.15)', borderRadius: 8, padding: '10px 14px', marginBottom: 14, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <span style={{ fontSize: 16, flexShrink: 0 }}>✅</span>
                  <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.7)', lineHeight: 1.6 }}>
                    <strong style={{ color: '#34d399' }}>Back all of these.</strong> Benter's rule: never skip a qualifying pick because you "don't fancy it". The edge is statistical — it only works if you take every bet the model finds. Skipping winners and backing losers by gut feel will destroy the ROI faster than any losing streak.
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {backAll.map((pick, i) => (
                    <ValueBetCard key={`${pick.horse}-${pick.race_time}-${i}`} pick={pick} isMobile={isMobile} />
                  ))}
                </div>
              </>
            )}

            {/* VALUE grade is not shown — edge (ratio 1.0-1.5x) is within partial-field
                coverage noise and the site explicitly says not to stake on it, so
                surfacing it as a "pick" only confuses subscribers. Still computed and
                persisted to DynamoDB every run for background tracking — once 50+ have
                settled the model calibration can tell us if the grade threshold should
                move (see the vegas skill). */}

            {/* No backable picks today */}
            {backAll.length === 0 && watchOnly.length > 0 && (
              <div style={{ background: 'rgba(30,41,69,0.5)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, padding: '16px 20px', marginBottom: 12 }}>
                <div style={{ fontSize: 13, color: '#e2e8f0', fontFamily: 'monospace', marginBottom: 4 }}>No ELITE or STRONG picks today</div>
                <div style={{ fontSize: 12, color: 'rgba(226,232,240,0.45)' }}>Only VALUE-grade picks found — watch list only. This is the correct response: pass the day rather than force a bet.</div>
              </div>
            )}
          </>
        );
      })()}

      {/* Exacta Lab */}
      {!loading && !error && data?.exactas?.length > 0 && (
        <>
          {sectionHead('Exacta Lab · Harville Formula')}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {data.exactas.map((exacta, i) => (
              <ExactaCard key={`${exacta.venue}-${exacta.race_time}-${i}`} exacta={exacta} isMobile={isMobile} />
            ))}
          </div>
        </>
      )}

      {/* Stats strip */}
      {!loading && !error && data && (
        <>
          {sectionHead('Today\'s Model Stats')}
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4, 1fr)', gap: 10 }}>
            {[
              { label: 'Races Analysed', value: data.races_analysed ?? '—', color: '#34d399' },
              { label: 'Back All (ELITE+STRONG)', value: (data.value_bets || []).filter(p => p.benter_grade !== 'VALUE').length, color: '#34d399' },
              { label: 'Watch Only (VALUE)', value: (data.value_bets || []).filter(p => p.benter_grade === 'VALUE').length, color: 'rgba(226,232,240,0.5)' },
              { label: 'Min Edge Required', value: data.methodology?.min_edge ?? '10%', color: '#fbbf24' },
            ].map(stat => (
              <div key={stat.label} style={{ background: 'rgba(30,41,69,0.6)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, padding: '12px 14px' }}>
                <div style={{ fontSize: 9, letterSpacing: '0.12em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace', marginBottom: 4 }}>{stat.label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: stat.color || '#34d399', fontFamily: 'monospace' }}>{stat.value}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Model Learning */}
      {(learning || true) && (
        <>
          {sectionHead('Model Learning')}
          <button
            onClick={() => setShowLearn(v => !v)}
            style={{ fontSize: 10, color: learning?.settled_count > 0 ? '#a78bfa' : 'rgba(226,232,240,0.4)', background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.25)', padding: '6px 14px', borderRadius: 4, cursor: 'pointer', fontFamily: 'monospace', letterSpacing: '0.1em', marginBottom: 16 }}
          >
            {showLearn ? '▲ HIDE' : '▼ SHOW'} CALIBRATION STATS
            {learning?.settled_count > 0 ? ` · ${learning.settled_count} settled picks` : ' · no settled picks yet'}
          </button>

          {showLearn && learning && learning.settled_count > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

              {/* Summary row */}
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)', gap: 10 }}>
                {[
                  { label: 'Picks Settled', value: learning.settled_count, color: '#e2e8f0' },
                  { label: 'Win Rate', value: `${learning.overall_wr}%`, color: learning.overall_wr > 30 ? '#34d399' : '#f87171' },
                  { label: 'ROI', value: `${learning.overall_roi > 0 ? '+' : ''}${learning.overall_roi}%`, color: learning.overall_roi > 0 ? '#34d399' : '#f87171' },
                  { label: 'Brier Score', value: learning.brier_score, color: CALIB_COLOR[learning.calib_label] || '#fbbf24' },
                ].map(s => (
                  <div key={s.label} style={{ background: 'rgba(30,41,69,0.6)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 6, padding: '12px 14px' }}>
                    <div style={{ fontSize: 9, letterSpacing: '0.12em', color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace', marginBottom: 4 }}>{s.label}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: s.color, fontFamily: 'monospace' }}>{s.value}</div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 10, color: CALIB_COLOR[learning.calib_label] || '#fbbf24', fontFamily: 'monospace', letterSpacing: '0.1em' }}>
                CALIBRATION: {learning.calib_label}
              </div>

              {/* Grade breakdown */}
              {Object.keys(learning.grade_stats || {}).length > 0 && (
                <div>
                  <div style={{ fontSize: 9, letterSpacing: '0.14em', color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace', marginBottom: 8 }}>BY GRADE</div>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    {Object.entries(learning.grade_stats).map(([g, s]) => {
                      const gc = GRADE_CONFIG[g] || GRADE_CONFIG.VALUE;
                      return (
                        <div key={g} style={{ background: gc.bg, border: `1px solid ${gc.border}55`, borderRadius: 6, padding: '10px 14px', minWidth: 90 }}>
                          <div style={{ fontSize: 9, color: gc.color, fontFamily: 'monospace', marginBottom: 4 }}>{g}</div>
                          <div style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', fontFamily: 'monospace' }}>{s.wr}%</div>
                          <div style={{ fontSize: 10, color: s.roi > 0 ? '#34d399' : '#f87171', fontFamily: 'monospace' }}>{s.roi > 0 ? '+' : ''}{s.roi}% ROI</div>
                          <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace' }}>{s.n} picks</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Score band table */}
              {learning.score_bands?.length > 0 && (
                <div>
                  <div style={{ fontSize: 9, letterSpacing: '0.14em', color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace', marginBottom: 8 }}>BY SCORE BAND</div>
                  <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4,1fr)', gap: 8 }}>
                    {learning.score_bands.map(b => (
                      <div key={b.band} style={{ background: 'rgba(30,41,69,0.5)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, padding: '10px 12px' }}>
                        <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace', marginBottom: 3 }}>SCORE {b.band}</div>
                        <div style={{ fontSize: 16, fontWeight: 700, color: '#e2e8f0', fontFamily: 'monospace' }}>{b.wr}%</div>
                        <div style={{ fontSize: 10, color: b.roi > 0 ? '#34d399' : '#f87171', fontFamily: 'monospace' }}>{b.roi > 0 ? '+' : ''}{b.roi}% · {b.n}p</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Calibration chart */}
              {learning.calibration?.length > 0 && (
                <div>
                  <div style={{ fontSize: 9, letterSpacing: '0.14em', color: 'rgba(226,232,240,0.35)', fontFamily: 'monospace', marginBottom: 8 }}>CALIBRATION — PREDICTED vs ACTUAL WIN RATE</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {learning.calibration.map(c => {
                      const over = c.mean_pred > c.actual_wr * 1.5;
                      return (
                        <div key={c.range} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div style={{ width: 70, fontSize: 9, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace', flexShrink: 0 }}>{c.range}</div>
                          <div style={{ flex: 1, position: 'relative', height: 16, background: 'rgba(0,0,0,0.3)', borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{ position: 'absolute', height: '100%', width: `${Math.min(100, c.mean_pred)}%`, background: 'rgba(96,165,250,0.35)', borderRadius: 3 }} />
                            <div style={{ position: 'absolute', height: '100%', width: `${Math.min(100, c.actual_wr)}%`, background: over ? '#f97316' : '#34d399', opacity: 0.8, borderRadius: 3 }} />
                          </div>
                          <div style={{ fontSize: 9, fontFamily: 'monospace', color: over ? '#f97316' : '#34d399', width: 80, textAlign: 'right' }}>
                            pred {c.mean_pred}% → {c.actual_wr}%
                          </div>
                          <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.3)', fontFamily: 'monospace', width: 24, textAlign: 'right' }}>{c.n}p</div>
                        </div>
                      );
                    })}
                  </div>
                  <div style={{ fontSize: 9, color: 'rgba(226,232,240,0.3)', marginTop: 6, fontFamily: 'monospace' }}>Blue = predicted · Green/Orange = actual (orange = overconfident)</div>
                </div>
              )}

              {/* Parameter suggestions */}
              {learning.suggestions?.length > 0 && (
                <div style={{ background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.2)', borderRadius: 8, padding: '14px 16px' }}>
                  <div style={{ fontSize: 10, color: '#fbbf24', fontFamily: 'monospace', letterSpacing: '0.12em', marginBottom: 10 }}>⚡ MODEL TUNING SUGGESTIONS</div>
                  {learning.suggestions.map((s, i) => (
                    <div key={i} style={{ marginBottom: 8, paddingBottom: 8, borderBottom: i < learning.suggestions.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 3 }}>
                        <span style={{ fontSize: 10, fontWeight: 700, color: '#fbbf24', fontFamily: 'monospace' }}>{s.param}</span>
                        <span style={{ fontSize: 10, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace' }}>{s.current} → {s.suggested}</span>
                      </div>
                      <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.6)', lineHeight: 1.5 }}>{s.reason}</div>
                    </div>
                  ))}
                </div>
              )}

            </div>
          )}

          {showLearn && learning && learning.settled_count === 0 && (
            <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.4)', fontFamily: 'monospace', paddingBottom: 12 }}>
              Picks are saved each day after the pipeline runs. Results settle after races finish. Check back tomorrow for calibration data.
            </div>
          )}
        </>
      )}

      {/* Card glossary */}
      {sectionHead('What Each Figure Means')}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0, background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, overflow: 'hidden', marginBottom: 32 }}>
        {[
          {
            field: 'ELITE / STRONG / VALUE',
            color: '#fbbf24',
            what: 'The grade — how much our model diverges from the market.',
            why: 'ELITE = model rates the horse 2× or more than market odds imply. STRONG = 1.5–2×. VALUE = 1.0–1.5×. Lower grades are noisier — the edge may be within model error. Only STRONG and ELITE meet Benter\'s minimum threshold for real staking.',
          },
          {
            field: 'Fractional odds (e.g. 14/1)',
            color: '#fbbf24',
            what: 'The current Betfair exchange price for a win bet.',
            why: 'This is the price you\'d actually get. 14/1 means you profit €14 for every €1 staked if the horse wins. Betfair odds reflect the market\'s collective view of win probability — our model disagrees, which is the whole point.',
          },
          {
            field: 'BENTER MODEL %',
            color: '#34d399',
            what: 'The combined probability from the Benter formula — our model probability blended with the market price.',
            why: 'Formula: softmax(α·log(model_prob) + β·log(market_prob)). At 14/1, the market says 6.8%. Our score-based model says ~40%. The blend (24.9%) is the best estimate of true win probability given both sources of information. This is what you bet on.',
          },
          {
            field: 'MARKET %',
            color: 'rgba(226,232,240,0.6)',
            what: 'The market\'s implied win probability — derived from Betfair odds and adjusted for overround.',
            why: 'Raw: 1 ÷ decimal_odds. Normalised by dividing by the sum of all runners\' raw implied probs to remove bookmaker margin. 6.8% at 14/1 means the public collectively gives this horse a 1-in-15 chance. When our model disagrees sharply, that\'s the edge.',
          },
          {
            field: 'EDGE OVER MARKET',
            color: '#34d399',
            what: 'The gap: Benter model% minus market%. This is the value.',
            why: 'Benter\'s central insight — only bet when your model probability exceeds the market implied probability. +18.2% means our model is 18 percentage points more bullish than the market. The bar visualises this gap. Minimum threshold to show a card is 10%.',
          },
          {
            field: 'MODEL SCORE',
            color: '#e2e8f0',
            what: 'The BetBudAI 7-factor form score (0–150+).',
            why: 'Built from: course & distance form, going match, Timeform stars, jockey quality, trainer strike rate, market steam, and days-since-last-run. 80+ = enough signals to trust. 90+ = high confidence. Below 80 is filtered out — too much noise from partial data to produce a reliable Benter probability.',
          },
          {
            field: '½-KELLY STAKE',
            color: '#fbbf24',
            what: 'Recommended stake as a percentage of your betting bank, using half the Kelly criterion.',
            why: 'Kelly formula: f* = (b·p − q) ÷ b, where b = decimal odds − 1, p = combined win prob, q = 1 − p. Halved for safety (full Kelly is mathematically optimal but requires perfect probability estimates — we use half to account for model error). Capped at 12% of bank. 9.8u on a 100-unit bank = €9.80 stake.',
          },
          {
            field: 'EV (Expected Value)',
            color: '#34d399',
            what: 'The theoretical profit per €1 staked if the model probability is correct.',
            why: 'EV = (combined_prob × decimal_odds) − 1. At 24.9% and 15.0 (14/1 decimal): 0.249 × 15 − 1 = +2.74 = +274%. This means for every €1 staked you should profit €2.74 on average over many identical bets — IF the 24.9% is accurate. High EV from inflated model probs is misleading; this is why the score gate and grade filter matter.',
          },
          {
            field: 'Jockey name (bottom right)',
            color: 'rgba(226,232,240,0.4)',
            what: 'The declared jockey for this race.',
            why: 'Included because jockey quality is one of the 7 scoring signals. Top 5% strike-rate jockeys add +15 points to the model score. A big-name jockey on a value pick is a supporting signal; an unknown apprentice on a short-priced pick is a mild red flag.',
          },
        ].map((row, i, arr) => (
          <div key={row.field} style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : '200px 1fr',
            gap: isMobile ? 4 : 16,
            padding: isMobile ? '14px 16px' : '14px 20px',
            borderBottom: i < arr.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
          }}>
            <div style={{ fontFamily: 'monospace', fontSize: 11, fontWeight: 700, color: row.color, lineHeight: 1.4, paddingTop: 1 }}>
              {row.field}
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#e2e8f0', marginBottom: 4, lineHeight: 1.5 }}>{row.what}</div>
              <div style={{ fontSize: 11, color: 'rgba(226,232,240,0.45)', lineHeight: 1.6 }}>{row.why}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={{ marginTop: 16, paddingTop: 18, borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: 10, color: 'rgba(226,232,240,0.3)', fontFamily: 'monospace', lineHeight: 1.8 }}>
        Benter Combined Model · α=1.0 · β=1.0 · Temperature=20 · Half-Kelly sizing (cap 12%) · Harville γ=0.81 δ=0.65<br/>
        Value threshold: combined probability must exceed market by ≥10%. Score gate ≥80. Scores use BetBudAI 7-factor engine. Refreshes every 60s.
      </div>
    </div>
  );
}
