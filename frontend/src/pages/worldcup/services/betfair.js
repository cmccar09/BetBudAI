/**
 * Betfair Exchange — proxied through BetBud Lambda (no CORS issue).
 *
 * All calls go to the BetBud API Gateway which authenticates with
 * Betfair server-side using the registered certificate + app key.
 *
 * Endpoints added to the Lambda:
 *   GET  /betfair/events      — upcoming WC events
 *   GET  /betfair/outrights   — outright markets with best prices
 *   POST /betfair/catalogue   — { eventId } → market list
 *   POST /betfair/book        — { marketIds } → current prices
 */

import { WC_API } from './apiFootball'

const BF = `${WC_API}/betfair`

async function bfGet(path) {
  try {
    const r = await fetch(BF + path)
    if (!r.ok) return null
    return r.json()
  } catch { return null }
}

async function bfPost(path, body) {
  try {
    const r = await fetch(BF + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!r.ok) return null
    return r.json()
  } catch { return null }
}

/** List upcoming World Cup events from the Betfair Exchange */
export async function fetchBfEvents() {
  return bfGet('/events')
}

/** List outright markets (winner, top scorer) with best prices */
export async function fetchBfOutrights() {
  return bfGet('/outrights')
}

/** Get all markets for a specific event */
export async function fetchBfCatalogue(eventId) {
  return bfPost('/catalogue', { eventId })
}

/** Get current best-offer prices for one or more markets */
export async function fetchBfBook(marketIds) {
  return bfPost('/book', { marketIds })
}

// ── Legacy key helpers (kept for backward compat, no-op now) ───────────────
export const getBetfairKey  = () => ''
export const setBetfairKey  = () => {}

// ── Utility ─────────────────────────────────────────────────────────────────
export function decimalToAmerican(dec) {
  if (!dec || dec <= 1) return '-'
  if (dec >= 2) return `+${Math.round((dec - 1) * 100)}`
  return `-${Math.round(100 / (dec - 1))}`
}

export function formatDecimalOdds(dec) {
  if (!dec || dec <= 1) return '-'
  return `${dec.toFixed(2)} (${((1 / dec) * 100).toFixed(0)}%)`
}

// ── Static fallback mock data (shown if Lambda/Betfair unavailable) ─────────
export const BETFAIR_MOCK_MARKETS = {
  'England vs Croatia (17 Jun)': [
    {
      marketName: 'Match Odds',
      runners: [
        { name: 'England',  back: 1.75, lay: 1.76, tag: 'value' },
        { name: 'Draw',     back: 3.80, lay: 3.90 },
        { name: 'Croatia',  back: 5.00, lay: 5.20 },
      ]
    },
    {
      marketName: 'Both Teams To Score',
      runners: [
        { name: 'Yes', back: 1.85, lay: 1.88, tag: 'tip' },
        { name: 'No',  back: 2.02, lay: 2.06 },
      ]
    },
    {
      marketName: 'Over/Under 2.5 Goals',
      runners: [
        { name: 'Over 2.5',  back: 2.10, lay: 2.14, tag: 'tip' },
        { name: 'Under 2.5', back: 1.80, lay: 1.83 },
      ]
    },
    {
      marketName: 'Total Corners (Over/Under 9.5)',
      runners: [
        { name: 'Over 9.5',  back: 1.88, lay: 1.92, tag: 'value' },
        { name: 'Under 9.5', back: 1.98, lay: 2.02 },
      ]
    },
    {
      marketName: 'Total Bookings (Over/Under 3.5)',
      runners: [
        { name: 'Over 3.5',  back: 1.92, lay: 1.96, tag: 'tip' },
        { name: 'Under 3.5', back: 1.94, lay: 1.98 },
      ]
    },
    {
      marketName: 'Asian Handicap',
      runners: [
        { name: 'England -0.5', back: 1.90, lay: 1.94, tag: 'value' },
        { name: 'Croatia +0.5', back: 2.00, lay: 2.04 },
      ]
    },
    {
      marketName: 'Harry Kane Anytime Scorer',
      runners: [
        { name: 'Yes', back: 2.00, lay: 2.10, tag: 'hot' },
        { name: 'No',  back: 1.85, lay: 1.90 },
      ]
    },
    {
      marketName: '1st Goal Scorer',
      runners: [
        { name: 'H. Kane',       back: 6.00,  lay: 6.40,  tag: 'hot' },
        { name: 'B. Saka',       back: 8.00,  lay: 8.60  },
        { name: 'J. Bellingham', back: 9.00,  lay: 9.80  },
        { name: 'O. Watkins',    back: 11.00, lay: 12.00 },
        { name: 'L. Modrić',     back: 17.00, lay: 19.00 },
      ]
    },
    {
      marketName: 'Correct Score',
      runners: [
        { name: '2-0 England', back: 6.50,  lay: 7.00,  tag: 'tip' },
        { name: '1-0 England', back: 7.00,  lay: 7.50  },
        { name: '2-1 England', back: 9.00,  lay: 9.80  },
        { name: '3-0 England', back: 11.00, lay: 12.00 },
        { name: '1-1 Draw',    back: 8.00,  lay: 8.60  },
        { name: '0-1 Croatia', back: 22.00, lay: 24.00 },
      ]
    },
  ],
}
