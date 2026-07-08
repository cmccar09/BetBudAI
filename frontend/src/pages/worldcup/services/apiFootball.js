const API_BASE = 'https://v3.football.api-sports.io'
const WC_LEAGUE = 1
const WC_SEASON = 2026

// BetBud AWS API — reads from DynamoDB, no key required
export const WC_API = 'https://q8ncph5i45.execute-api.eu-west-1.amazonaws.com'

export async function fetchWcGroups()    { try { const r = await fetch(WC_API+'/groups');    return r.ok ? r.json() : null } catch { return null } }
export async function fetchWcOutrights() { try { const r = await fetch(WC_API+'/outrights'); return r.ok ? r.json() : null } catch { return null } }
export async function fetchWcScorers()   { try { const r = await fetch(WC_API+'/scorers');   return r.ok ? r.json() : null } catch { return null } }
export async function fetchWcBracket()   { try { const r = await fetch(WC_API+'/bracket');   return r.ok ? r.json() : null } catch { return null } }
export async function fetchWcMeta()      { try { const r = await fetch(WC_API+'/meta');      return r.ok ? r.json() : null } catch { return null } }

let _apiKey = localStorage.getItem('betbud_apikey') || ''

export const setApiKey = (key) => {
  _apiKey = key
  localStorage.setItem('betbud_apikey', key)
}

export const getApiKey = () => _apiKey

const headers = () => ({ 'x-apisports-key': _apiKey })

async function apiFetch(endpoint) {
  if (!_apiKey) return null
  try {
    const res = await fetch(API_BASE + endpoint, { headers: headers() })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

export async function testConnection() {
  const data = await apiFetch(`/leagues?id=${WC_LEAGUE}&season=${WC_SEASON}`)
  return data?.response?.length > 0
}

export async function fetchStandings() {
  return apiFetch(`/standings?league=${WC_LEAGUE}&season=${WC_SEASON}`)
}

export async function fetchFixturesByDate(date) {
  return apiFetch(`/fixtures?league=${WC_LEAGUE}&season=${WC_SEASON}&date=${date}`)
}

export async function fetchAllFixtures() {
  return apiFetch(`/fixtures?league=${WC_LEAGUE}&season=${WC_SEASON}`)
}

export async function fetchTopScorers() {
  return apiFetch(`/players/topscorers?league=${WC_LEAGUE}&season=${WC_SEASON}`)
}

export async function fetchTopAssisters() {
  return apiFetch(`/players/topassists?league=${WC_LEAGUE}&season=${WC_SEASON}`)
}

export async function fetchFixtureStats(fixtureId) {
  return apiFetch(`/fixtures/statistics?fixture=${fixtureId}`)
}

export async function fetchFixturePlayerStats(fixtureId) {
  return apiFetch(`/fixtures/players?fixture=${fixtureId}`)
}

export async function fetchPredictions(fixtureId) {
  return apiFetch(`/predictions?fixture=${fixtureId}`)
}

export async function fetchOdds(fixtureId) {
  return apiFetch(`/odds?fixture=${fixtureId}&bookmaker=6`) // bookmaker 6 = Bet365
}

// Parse standings API response into our group format
export function parseStandings(apiData, existingGroups) {
  if (!apiData?.response?.[0]?.league?.standings) return null
  const result = {}
  apiData.response[0].league.standings.forEach(groupArr => {
    const grpName = groupArr[0]?.group?.replace('Group ', '')
    if (!grpName) return
    result[grpName] = {
      ...existingGroups[grpName],
      teams: groupArr.map(t => ({
        name: t.team.name,
        flag: existingGroups[grpName]?.teams?.find(x => x.name === t.team.name)?.flag || '🏳',
        p: t.all.played,
        w: t.all.win,
        d: t.all.draw,
        l: t.all.lose,
        gf: t.all.goals.for,
        ga: t.all.goals.against,
        pts: t.points,
        rating: existingGroups[grpName]?.teams?.find(x => x.name === t.team.name)?.rating || 7.0,
        form: t.form || 'NNNNN',
      }))
    }
  })
  return result
}

// Parse fixtures from API
export function parseFixtures(apiData) {
  if (!apiData?.response) return []
  return apiData.response.map(f => {
    const s = f.fixture.status.short
    const isLive = ['1H','HT','2H','ET','BT','P','SUSP','INT'].includes(s)
    const isFin = ['FT','AET','PEN'].includes(s)
    return {
      id: f.fixture.id,
      date: f.fixture.date?.split('T')[0],
      time: f.fixture.date?.split('T')[1]?.slice(0, 5) || '--:--',
      home: f.teams.home.name,
      homeFlag: '',
      away: f.teams.away.name,
      awayFlag: '',
      hScore: f.goals.home,
      aScore: f.goals.away,
      elapsed: f.fixture.status.elapsed,
      status: isLive ? 'LIVE' : isFin ? 'FT' : 'NS',
      round: f.league.round,
      venue: f.fixture.venue?.name || '',
    }
  })
}
