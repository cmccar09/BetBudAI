import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, QueryCommand, ScanCommand, GetCommand } from '@aws-sdk/lib-dynamodb';
import { SFNClient, ListExecutionsCommand, StartExecutionCommand, DescribeExecutionCommand, GetExecutionHistoryCommand } from '@aws-sdk/client-sfn';
import { CloudWatchLogsClient, FilterLogEventsCommand } from '@aws-sdk/client-cloudwatch-logs';
import { z } from 'zod';

const REGION = 'eu-west-1';
const API_BASE = 'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com';

const dynamo = DynamoDBDocumentClient.from(new DynamoDBClient({ region: REGION }));
const sfn    = new SFNClient({ region: REGION });
const cwl    = new CloudWatchLogsClient({ region: REGION });

let ACCOUNT_ID = null;
async function accountId() {
  if (ACCOUNT_ID) return ACCOUNT_ID;
  const r = await fetch('https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15', {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  // fall back to env or known value
  ACCOUNT_ID = process.env.AWS_ACCOUNT_ID || '813281204422';
  return ACCOUNT_ID;
}

function smArn(name) {
  return `arn:aws:states:${REGION}:813281204422:stateMachine:${name}`;
}

// ── helpers ────────────────────────────────────────────────────────────────

function today() {
  return new Date().toISOString().slice(0, 10);
}

function fmtPick(p) {
  const score = p.comprehensive_score ?? p.score ?? '?';
  const odds  = p.odds ? parseFloat(p.odds).toFixed(2) : '?';
  const outcome = p.outcome || p.result_emoji || 'pending';
  return `${p.horse || p.horse_name || '?'} | ${p.course || '?'} ${(p.race_time || '').substring(11,16)} | score=${score} odds=${odds} | ${outcome} | signals=${p.n_signals ?? p.signals ?? '?'}`;
}

// ── server ─────────────────────────────────────────────────────────────────

const server = new McpServer({
  name: 'betbudai',
  version: '1.0.0',
});

// ── TOOL: picks_today ──────────────────────────────────────────────────────
server.tool(
  'picks_today',
  'Get all picks from DynamoDB for today (or a given date). Shows horse, course, score, odds, outcome.',
  { date: z.string().optional().describe('YYYY-MM-DD, defaults to today') },
  async ({ date }) => {
    const d = date || today();
    const res = await dynamo.send(new QueryCommand({
      TableName: 'SureBetBets',
      KeyConditionExpression: 'bet_date = :d',
      ExpressionAttributeValues: { ':d': d },
    }));
    const items = res.Items || [];
    if (!items.length) return { content: [{ type: 'text', text: `No picks found for ${d}` }] };

    const ui   = items.filter(p => p.show_in_ui);
    const ext  = items.filter(p => p.pick_type === 'extended' && !p.is_dropped);
    const drop = items.filter(p => p.is_dropped);
    const lines = [
      `=== BetBudAI Picks — ${d} ===`,
      `Total: ${items.length} | UI picks: ${ui.length} | Extended: ${ext.length} | Dropped: ${drop.length}`,
      '',
      '── MORNING PICKS (show_in_ui) ──',
      ...ui.sort((a,b) => (b.comprehensive_score||b.score||0)-(a.comprehensive_score||a.score||0)).map(fmtPick),
      '',
      '── EXTENDED PICKS ──',
      ...ext.sort((a,b) => (b.comprehensive_score||b.score||0)-(a.comprehensive_score||a.score||0)).map(fmtPick),
    ];
    return { content: [{ type: 'text', text: lines.join('\n') }] };
  }
);

// ── TOOL: pick_detail ──────────────────────────────────────────────────────
server.tool(
  'pick_detail',
  'Get full detail for a specific pick including all signals, score breakdown, form data.',
  {
    date:   z.string().describe('YYYY-MM-DD'),
    horse:  z.string().describe('Horse name (partial match OK)'),
  },
  async ({ date, horse }) => {
    const res = await dynamo.send(new QueryCommand({
      TableName: 'SureBetBets',
      KeyConditionExpression: 'bet_date = :d',
      ExpressionAttributeValues: { ':d': date },
    }));
    const match = (res.Items || []).find(p =>
      (p.horse || p.horse_name || '').toLowerCase().includes(horse.toLowerCase())
    );
    if (!match) return { content: [{ type: 'text', text: `No pick matching "${horse}" on ${date}` }] };

    const exclude = ['all_horses', 'form_runs'];
    const detail = Object.fromEntries(
      Object.entries(match).filter(([k]) => !exclude.includes(k))
    );
    return { content: [{ type: 'text', text: JSON.stringify(detail, null, 2) }] };
  }
);

// ── TOOL: roi_stats ────────────────────────────────────────────────────────
server.tool(
  'roi_stats',
  'Get cumulative ROI stats and recent win/loss record from the BetBudAI API.',
  {},
  async () => {
    const [roiRes, todayRes] = await Promise.all([
      fetch(`${API_BASE}/api/results/cumulative-roi`).then(r => r.json()).catch(() => ({})),
      fetch(`${API_BASE}/api/results/today`).then(r => r.json()).catch(() => ({})),
    ]);
    const lines = [
      `=== ROI Stats ===`,
      `ROI: ${roiRes.roi != null ? roiRes.roi.toFixed(1) + '%' : 'n/a'}`,
      `Settled bets: ${roiRes.settled ?? 'n/a'}`,
      `Wins: ${roiRes.wins ?? 'n/a'} | Win rate: ${roiRes.win_rate != null ? roiRes.win_rate.toFixed(1) + '%' : 'n/a'}`,
      '',
      `=== Today's Picks ===`,
      ...(todayRes.picks || []).map(fmtPick),
    ];
    return { content: [{ type: 'text', text: lines.join('\n') }] };
  }
);

// ── TOOL: extended_picks ───────────────────────────────────────────────────
server.tool(
  'extended_picks',
  'Get the Top 4 extended picks for a date from the BetBudAI API (all courses, by score).',
  { date: z.string().optional().describe('YYYY-MM-DD, defaults to today') },
  async ({ date }) => {
    const d = date || today();
    const data = await fetch(`${API_BASE}/api/picks/extended?date=${d}`).then(r => r.json()).catch(() => ({}));
    const picks = (data.picks || []).sort((a,b) => (b.score||0)-(a.score||0));
    if (!picks.length) return { content: [{ type: 'text', text: `No extended picks for ${d}` }] };
    const lines = [
      `=== Extended Picks — ${d} (${picks.length} picks) ===`,
      ...picks.map((p, i) => `${i+1}. ${fmtPick(p)} | trainer=${p.trainer||'?'} jockey=${p.jockey||'?'}`),
    ];
    return { content: [{ type: 'text', text: lines.join('\n') }] };
  }
);

// ── TOOL: pipeline_status ──────────────────────────────────────────────────
server.tool(
  'pipeline_status',
  'Check recent Step Functions execution history for Morning and Refresh pipelines.',
  { count: z.number().optional().describe('Number of executions to show per pipeline (default 5)') },
  async ({ count = 5 }) => {
    const pipelines = ['SureBet-Morning', 'SureBet-Refresh'];
    const lines = [];
    for (const name of pipelines) {
      lines.push(`\n=== ${name} ===`);
      try {
        const res = await sfn.send(new ListExecutionsCommand({
          stateMachineArn: smArn(name),
          maxResults: count,
        }));
        for (const e of res.executions || []) {
          const start = new Date(e.startDate).toISOString().slice(0,19);
          const stop  = e.stopDate ? new Date(e.stopDate).toISOString().slice(0,19) : 'running';
          const dur   = e.stopDate ? Math.round((new Date(e.stopDate)-new Date(e.startDate))/1000) + 's' : '—';
          lines.push(`  ${e.status.padEnd(10)} ${start} → ${stop} (${dur})`);
        }
      } catch (err) {
        lines.push(`  ERROR: ${err.message}`);
      }
    }
    return { content: [{ type: 'text', text: lines.join('\n') }] };
  }
);

// ── TOOL: run_pipeline ─────────────────────────────────────────────────────
server.tool(
  'run_pipeline',
  'Trigger a pipeline run now. pipeline = "morning" or "refresh".',
  { pipeline: z.enum(['morning', 'refresh']).describe('"morning" = full pick selection, "refresh" = odds update only') },
  async ({ pipeline }) => {
    const name = pipeline === 'morning' ? 'SureBet-Morning' : 'SureBet-Refresh';
    const res = await sfn.send(new StartExecutionCommand({
      stateMachineArn: smArn(name),
      input: JSON.stringify({ source: 'mcp', mode: pipeline }),
    }));
    return { content: [{ type: 'text', text: `Started ${name}\nExecution: ${res.executionArn}\nStarted at: ${new Date(res.startDate).toISOString()}` }] };
  }
);

// ── TOOL: pipeline_last_error ──────────────────────────────────────────────
server.tool(
  'pipeline_last_error',
  'Get the failure reason from the most recent failed Refresh or Morning execution.',
  { pipeline: z.enum(['morning', 'refresh']).optional().default('refresh') },
  async ({ pipeline }) => {
    const name = pipeline === 'morning' ? 'SureBet-Morning' : 'SureBet-Refresh';
    const list = await sfn.send(new ListExecutionsCommand({
      stateMachineArn: smArn(name),
      statusFilter: 'FAILED',
      maxResults: 1,
    }));
    const exec = (list.executions || [])[0];
    if (!exec) return { content: [{ type: 'text', text: `No failed executions found for ${name}` }] };

    const hist = await sfn.send(new GetExecutionHistoryCommand({
      executionArn: exec.executionArn,
      reverseOrder: true,
      maxResults: 20,
    }));
    const errors = (hist.events || []).filter(e =>
      e.type?.includes('Failed') || e.type?.includes('failed')
    );
    const lines = [`=== Last ${name} failure — ${new Date(exec.startDate).toISOString().slice(0,19)} ===`];
    for (const e of errors) {
      const d = e.executionFailedEventDetails || e.taskFailedEventDetails || e.lambdaFunctionFailedEventDetails || {};
      lines.push(`Type: ${e.type}`);
      lines.push(`Error: ${d.error || '—'}`);
      lines.push(`Cause: ${(d.cause || '—').slice(0, 400)}`);
      lines.push('');
    }
    return { content: [{ type: 'text', text: lines.join('\n') }] };
  }
);

// ── TOOL: sports_data ─────────────────────────────────────────────────────
server.tool(
  'sports_data',
  'Query BetBudAI_Sports DynamoDB table. sport = worldcup | wimbledon | tourdefrance | rugby | golf',
  {
    sport:    z.enum(['worldcup','wimbledon','tourdefrance','rugby','golf']),
    data_key: z.string().optional().describe('e.g. MATCHES, RESULTS, OUTRIGHT — omit to list available keys'),
  },
  async ({ sport, data_key }) => {
    if (!data_key) {
      const res = await dynamo.send(new QueryCommand({
        TableName: 'BetBudAI_Sports',
        KeyConditionExpression: 'sport = :s',
        ExpressionAttributeValues: { ':s': sport },
        ProjectionExpression: 'data_key, updated_at',
      }));
      const keys = (res.Items || []).map(i => `${i.data_key} (updated: ${(i.updated_at||'?').slice(0,19)})`);
      return { content: [{ type: 'text', text: `Available keys for ${sport}:\n${keys.join('\n')}` }] };
    }
    const res = await dynamo.send(new GetCommand({
      TableName: 'BetBudAI_Sports',
      Key: { sport, data_key },
    }));
    if (!res.Item) return { content: [{ type: 'text', text: `No data for ${sport}/${data_key}` }] };
    const { sport: _s, data_key: _k, ...payload } = res.Item;
    return { content: [{ type: 'text', text: JSON.stringify(payload, null, 2).slice(0, 8000) }] };
  }
);

// ── TOOL: lambda_logs ─────────────────────────────────────────────────────
server.tool(
  'lambda_logs',
  'Get recent CloudWatch log output for a BetBudAI Lambda. Common names: surebet-analysis, surebet-betfair-fetch, surebet-validate, surebet-notify, surebet-sl-results',
  {
    lambda_name: z.string().describe('Lambda function name'),
    minutes:     z.number().optional().describe('How far back to look in minutes (default 30)'),
  },
  async ({ lambda_name, minutes = 30 }) => {
    const logGroup = `/aws/lambda/${lambda_name}`;
    const startTime = Date.now() - minutes * 60 * 1000;
    try {
      const res = await cwl.send(new FilterLogEventsCommand({
        logGroupName: logGroup,
        startTime,
        limit: 100,
      }));
      const msgs = (res.events || []).map(e => {
        const ts = new Date(e.timestamp).toISOString().slice(11,19);
        return `${ts} ${e.message.trimEnd()}`;
      });
      if (!msgs.length) return { content: [{ type: 'text', text: `No logs in the last ${minutes}m for ${lambda_name}` }] };
      return { content: [{ type: 'text', text: msgs.join('\n').slice(0, 10000) }] };
    } catch (err) {
      return { content: [{ type: 'text', text: `Error fetching logs: ${err.message}` }] };
    }
  }
);

// ── TOOL: results_by_date ──────────────────────────────────────────────────
server.tool(
  'results_by_date',
  'Get settled results (wins/losses) for a date range to analyse pick performance.',
  {
    from: z.string().describe('Start date YYYY-MM-DD'),
    to:   z.string().optional().describe('End date YYYY-MM-DD, defaults to today'),
  },
  async ({ from, to }) => {
    const end = to || today();
    // Scan for settled picks in range
    const res = await dynamo.send(new ScanCommand({
      TableName: 'SureBetBets',
      FilterExpression: 'bet_date >= :f AND bet_date <= :t AND show_in_ui = :ui',
      ExpressionAttributeValues: { ':f': from, ':t': end, ':ui': true },
      ProjectionExpression: 'bet_date, horse, horse_name, course, race_time, odds, outcome, comprehensive_score, score',
    }));
    const items = (res.Items || []).sort((a,b) => (a.bet_date||'').localeCompare(b.bet_date||''));
    const wins   = items.filter(p => ['win','won'].includes((p.outcome||'').toLowerCase()));
    const losses = items.filter(p => ['loss','lost'].includes((p.outcome||'').toLowerCase()));
    const pending = items.filter(p => !['win','won','loss','lost'].includes((p.outcome||'').toLowerCase()));
    const lines = [
      `=== Results ${from} → ${end} ===`,
      `Total: ${items.length} | Wins: ${wins.length} | Losses: ${losses.length} | Pending: ${pending.length}`,
      wins.length ? `Win rate: ${(wins.length/Math.max(1,wins.length+losses.length)*100).toFixed(0)}%` : '',
      '',
      '── WINS ──',
      ...wins.map(p => `✅ ${p.bet_date} ${fmtPick(p)}`),
      '',
      '── LOSSES ──',
      ...losses.map(p => `❌ ${p.bet_date} ${fmtPick(p)}`),
    ];
    return { content: [{ type: 'text', text: lines.filter(l => l !== null).join('\n') }] };
  }
);

// ── start ──────────────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
