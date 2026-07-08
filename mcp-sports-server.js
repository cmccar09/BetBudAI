#!/usr/bin/env node
/**
 * BetBudAI Sports MCP Server
 *
 * Exposes BetBudAI's DynamoDB data to Claude via the Model Context Protocol.
 * Covers: horse racing picks, World Cup, Tennis, Cycling, Rugby, Golf.
 *
 * Register with: claude mcp add sports-api -- node ./mcp-sports-server.js
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, QueryCommand, GetCommand, ScanCommand } from '@aws-sdk/lib-dynamodb';

// ── AWS setup ────────────────────────────────────────────────────────────────

const REGION = 'eu-west-1';
const dynamo = DynamoDBDocumentClient.from(
  new DynamoDBClient({ region: REGION }),
  { marshallOptions: { removeUndefinedValues: true } }
);

const RACING_TABLE = 'SureBetBets';
const SPORTS_TABLE = 'BetBudAI_Sports';

function today() {
  return new Date().toISOString().slice(0, 10);
}

// ── Tool implementations ──────────────────────────────────────────────────────

async function getRacingPicks({ date }) {
  const d = date || today();
  try {
    const res = await dynamo.send(new QueryCommand({
      TableName: RACING_TABLE,
      IndexName: 'date-index',
      KeyConditionExpression: '#d = :d',
      ExpressionAttributeNames: { '#d': 'date' },
      ExpressionAttributeValues: { ':d': d },
    }));
    const items = res.Items || [];
    if (!items.length) {
      return { date: d, status: 'no_picks', message: 'Pipeline not yet run or no picks for this date. Picks appear after 11:00 UTC.' };
    }
    return {
      date: d,
      count: items.length,
      picks: items.map(p => ({
        horse: p.horse_name,
        meeting: p.meeting,
        race_time: p.race_time,
        score: p.score,
        odds: p.odds,
        odds_morning: p.odds_morning,
        signals: p.signals,
        signal_count: (p.signals || []).length,
        form_enriched: p.form_enriched,
        going: p.going,
        result_won: p.result_won ?? null,
        our_pick: p.our_pick ?? false,
        watchlist: p.watchlist ?? false,
      })).sort((a, b) => (b.score || 0) - (a.score || 0)),
    };
  } catch (err) {
    return { error: err.message };
  }
}

async function getSportData({ sport, data_key }) {
  const validSports = ['worldcup', 'wimbledon', 'tourdefrance', 'rugby', 'golf'];
  if (!validSports.includes(sport)) {
    return { error: `Unknown sport "${sport}". Valid: ${validSports.join(', ')}` };
  }
  try {
    const res = await dynamo.send(new GetCommand({
      TableName: SPORTS_TABLE,
      Key: { sport, data_key },
    }));
    if (!res.Item) {
      return { sport, data_key, status: 'not_found', message: 'No data found. Scraper may not have run yet.' };
    }
    return res.Item;
  } catch (err) {
    return { error: err.message };
  }
}

async function getGoldenBoot() {
  const res = await getSportData({ sport: 'worldcup', data_key: 'GOLDEN_BOOT' });
  if (res.error || res.status === 'not_found') return res;
  return {
    updated_at: res.updated_at,
    leaderboard: (res.leaderboard || []).slice(0, 10),
  };
}

async function getWorldCupFixtures() {
  const [results, bracket, meta] = await Promise.all([
    getSportData({ sport: 'worldcup', data_key: 'RESULTS' }),
    getSportData({ sport: 'worldcup', data_key: 'BRACKET' }),
    getSportData({ sport: 'worldcup', data_key: 'META' }),
  ]);
  const todayStr = today();
  const todayMatches = (results.results || []).filter(r => r.date?.startsWith(todayStr) || !r.completed);
  const recent = (results.results || []).filter(r => r.completed).slice(-8);
  return {
    updated_at: meta.updated_at,
    is_live: meta.is_live,
    matches_completed: meta.matches_completed,
    todays_fixtures: todayMatches,
    recent_results: recent,
    bracket_analysis: bracket.analysis || null,
  };
}

async function getRacingHistory({ days = 7 }) {
  const results = [];
  for (let i = 0; i < days; i++) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().slice(0, 10);
    const res = await dynamo.send(new QueryCommand({
      TableName: RACING_TABLE,
      IndexName: 'date-index',
      KeyConditionExpression: '#d = :d',
      ExpressionAttributeNames: { '#d': 'date' },
      ExpressionAttributeValues: { ':d': dateStr },
      FilterExpression: 'our_pick = :t',
      ExpressionAttributeValues: { ':d': dateStr, ':t': true },
    }));
    for (const item of res.Items || []) {
      results.push({
        date: dateStr,
        horse: item.horse_name,
        meeting: item.meeting,
        score: item.score,
        odds: item.odds,
        signals: (item.signals || []).length,
        result_won: item.result_won ?? null,
        form_enriched: item.form_enriched,
      });
    }
  }
  const withResults = results.filter(r => r.result_won !== null);
  const wins = withResults.filter(r => r.result_won === true).length;
  return {
    period_days: days,
    total_picks: results.length,
    results_available: withResults.length,
    wins,
    losses: withResults.length - wins,
    win_rate: withResults.length ? `${Math.round((wins / withResults.length) * 100)}%` : 'insufficient data',
    picks: results,
  };
}

async function checkDataFreshness({ sport }) {
  if (sport === 'racing') {
    const picks = await getRacingPicks({ date: today() });
    return {
      sport: 'racing',
      has_todays_picks: (picks.count || 0) > 0,
      pick_count: picks.count || 0,
      status: picks.status || 'ok',
    };
  }
  const meta = await getSportData({ sport, data_key: 'META' });
  if (meta.error || meta.status === 'not_found') return { sport, fresh: false, error: meta.error || 'not found' };
  const updatedAt = meta.updated_at ? new Date(meta.updated_at) : null;
  const ageHours = updatedAt ? Math.round((Date.now() - updatedAt.getTime()) / 3600000) : null;
  return {
    sport,
    updated_at: meta.updated_at,
    age_hours: ageHours,
    fresh: ageHours !== null && ageHours < 25,
    is_live: meta.is_live ?? null,
  };
}

async function getTodaysBriefing() {
  const [racing, wc, tennis, cycling, rugby, golf] = await Promise.all([
    getRacingPicks({ date: today() }),
    checkDataFreshness({ sport: 'worldcup' }),
    checkDataFreshness({ sport: 'wimbledon' }),
    checkDataFreshness({ sport: 'tourdefrance' }),
    checkDataFreshness({ sport: 'rugby' }),
    checkDataFreshness({ sport: 'golf' }),
  ]);

  const bestBet = (racing.picks || []).find(p => p.our_pick && p.score >= 90);

  return {
    date: today(),
    racing: {
      pick_count: racing.count || 0,
      best_bet: bestBet ? { horse: bestBet.horse, score: bestBet.score, odds: bestBet.odds, signals: bestBet.signal_count } : null,
      pipeline_run: (racing.count || 0) > 0,
    },
    sports_freshness: {
      worldcup: { fresh: wc.fresh, age_hours: wc.age_hours },
      tennis: { fresh: tennis.fresh, age_hours: tennis.age_hours },
      cycling: { fresh: cycling.fresh, age_hours: cycling.age_hours },
      rugby: { fresh: rugby.fresh, age_hours: rugby.age_hours },
      golf: { fresh: golf.fresh, age_hours: golf.age_hours },
    },
    stale_sports: ['worldcup', 'wimbledon', 'tourdefrance', 'rugby', 'golf']
      .filter((_, i) => ![wc, tennis, cycling, rugby, golf][i].fresh),
  };
}

// ── Tool definitions ──────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: 'get_racing_picks',
    description: 'Get today\'s (or any date\'s) horse racing picks from DynamoDB SureBetBets. Returns score, signals, odds, going, form_enriched, and result_won for each pick. Sorted by score descending.',
    inputSchema: {
      type: 'object',
      properties: {
        date: { type: 'string', description: 'Date in YYYY-MM-DD format. Defaults to today.' },
      },
    },
  },
  {
    name: 'get_sport_data',
    description: 'Get any sports page data from DynamoDB BetBudAI_Sports. Use this for World Cup results/bracket/golden boot, Wimbledon matches/tips/outright, Tour de France schedule/results, Rugby fixtures/tips, Golf majors/outright.',
    inputSchema: {
      type: 'object',
      properties: {
        sport: { type: 'string', enum: ['worldcup', 'wimbledon', 'tourdefrance', 'rugby', 'golf'], description: 'Sport identifier' },
        data_key: { type: 'string', description: 'Data key e.g. RESULTS, MATCHES, TIPS, OUTRIGHT, SCHEDULE, FIXTURES, GOLDEN_BOOT, BRACKET, META, OUTRIGHT_MEN, OUTRIGHT_WOMEN' },
      },
      required: ['sport', 'data_key'],
    },
  },
  {
    name: 'get_world_cup_fixtures',
    description: 'Get today\'s World Cup fixtures, recent completed results (last 8), and bracket analysis in one call. Includes updated_at freshness check.',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'get_golden_boot',
    description: 'Get the current World Cup Golden Boot leaderboard (top 10 scorers with goal counts and teams).',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'get_racing_history',
    description: 'Get horse racing pick history with win/loss results for the last N days. Returns win rate, ROI data, and per-pick breakdown.',
    inputSchema: {
      type: 'object',
      properties: {
        days: { type: 'number', description: 'Number of days of history to fetch (default 7, max 30)', default: 7 },
      },
    },
  },
  {
    name: 'check_data_freshness',
    description: 'Check when a sport\'s data was last updated. Returns age in hours and whether it is considered fresh (< 25 hours). Use "racing" to check if today\'s pipeline has run.',
    inputSchema: {
      type: 'object',
      properties: {
        sport: { type: 'string', enum: ['racing', 'worldcup', 'wimbledon', 'tourdefrance', 'rugby', 'golf'] },
      },
      required: ['sport'],
    },
  },
  {
    name: 'get_todays_briefing',
    description: 'Get a full today\'s status snapshot: racing pipeline state + best bet + freshness for all 5 sport pages. Use this as the starting point for /picks-today or /betting-picks all.',
    inputSchema: { type: 'object', properties: {} },
  },
];

// ── MCP server ────────────────────────────────────────────────────────────────

const server = new Server(
  { name: 'betbudai-sports-api', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  let result;
  switch (name) {
    case 'get_racing_picks':       result = await getRacingPicks(args || {}); break;
    case 'get_sport_data':         result = await getSportData(args); break;
    case 'get_world_cup_fixtures': result = await getWorldCupFixtures(); break;
    case 'get_golden_boot':        result = await getGoldenBoot(); break;
    case 'get_racing_history':     result = await getRacingHistory(args || {}); break;
    case 'check_data_freshness':   result = await checkDataFreshness(args); break;
    case 'get_todays_briefing':    result = await getTodaysBriefing(); break;
    default:
      return { content: [{ type: 'text', text: `Unknown tool: ${name}` }], isError: true };
  }

  return {
    content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
  };
});

// ── Start ─────────────────────────────────────────────────────────────────────

const transport = new StdioServerTransport();
await server.connect(transport);
