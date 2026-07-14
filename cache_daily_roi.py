"""
Lambda: betbudai-cache-roi  (handler: cache_daily_roi.lambda_handler)
======================================================================
Calculates cumulative level-stakes ROI and caches to BetBudAICache.
Runs: 06:00 UTC daily via EventBridge rule 'betbudai-daily-roi-cache'.

Reads from: SureBetBets (ranked daily picks, pick_type='morning'/'official')
Writes to:  BetBudAICache  cache_key='cumulative_roi'  (32-day TTL)

The /api/results/cumulative-roi endpoint reads this cache on every request.
Cache miss falls back to a slow live recalculation — this Lambda keeps it fresh.

Fix history:
  2026-06-06: Was writing to wrong table (SureBetBets CONFIG row) with wrong filter
              (show_in_ui=True broken by stale-pick cleanup). Now uses pick_type
              filter and writes to BetBudAICache correctly.
"""

import boto3
from datetime import date, datetime, timezone as tz, timedelta
from decimal import Decimal

REGION = 'eu-west-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
picks_table = dynamodb.Table('SureBetBets')
cache_table = dynamodb.Table('BetBudAICache')

CUMULATIVE_ROI_START = '2026-03-22'
UNIT = 1.0   # level-stakes: 1 unit per pick


def _dec(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, dict):
        return {k: _dec(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_dec(v) for v in o]
    return o


def _is_ranked_pick(item):
    """Identify official ranked picks for ROI calculation.
    Uses pick_type instead of show_in_ui — show_in_ui is cleared after races
    settle but pick_type='morning'/'official'/'extended' remains set permanently.
    Extended picks (Live Opportunities) are included because subscribers back them.
    """
    pt = str(item.get('pick_type') or '').strip().lower()
    if pt in ('morning', 'official', 'extended'):
        return True
    # Fallback: show_in_ui + pick_rank for picks predating pick_type field
    raw = item.get('show_in_ui', False)
    show = raw is True or str(raw).strip().lower() == 'true'
    try:
        rank = int(item.get('pick_rank', 0) or 0)
    except Exception:
        rank = 0
    return show and rank > 0


def _parse_odds(raw):
    """Parse odds from decimal float or fractional string (e.g. '7/5' → 2.4)."""
    if not raw:
        return 0.0
    s = str(raw).strip()
    if '/' in s:
        try:
            num, den = s.split('/', 1)
            return float(num) / float(den) + 1.0
        except Exception:
            return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def _settlement_odds(p):
    """Best available odds for settlement (SP > live odds)."""
    sp = _parse_odds(p.get('sp_odds'))
    live = _parse_odds(p.get('odds'))
    return sp if sp > 1.0 else (live if live > 1.0 else 1.0)


def lambda_handler(event, context):
    today = str(date.today())
    print(f"[cache_roi] Building cumulative ROI from {CUMULATIVE_ROI_START} to {today}...")

    # ── Query day-by-day (avoids expensive full-table scan) ───────────────────
    all_picks = []
    start_d = date.fromisoformat(CUMULATIVE_ROI_START)
    cur = start_d
    today_d = date.today()
    while cur <= today_d:
        day_str = str(cur)
        kwargs = {
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('bet_date').eq(day_str),
            'ProjectionExpression': (
                'bet_date, bet_id, horse, course, race_time, show_in_ui, pick_rank, '
                'is_learning_pick, is_dropped, outcome, sp_odds, odds, ew_fraction, '
                'bet_type, pick_type'
            ),
        }
        while True:
            resp = picks_table.query(**kwargs)
            all_picks.extend([_dec(it) for it in resp.get('Items', [])])
            lek = resp.get('LastEvaluatedKey')
            if not lek:
                break
            kwargs['ExclusiveStartKey'] = lek
        cur += timedelta(days=1)

    print(f"  Total DynamoDB rows: {len(all_picks)}")

    # ── Filter to ranked official picks only ──────────────────────────────────
    picks = [
        p for p in all_picks
        if p.get('course') and p.get('horse')
        and _is_ranked_pick(p)
        and not p.get('is_learning_pick', False)
        and not p.get('is_dropped', False)
    ]

    # Deduplicate: one pick per race (course + race_time), most recent date wins
    seen = {}
    for p in picks:
        k = (p.get('course', ''), p.get('race_time', ''))
        if k not in seen or p.get('bet_date', '') > seen[k].get('bet_date', ''):
            seen[k] = p
    picks = list(seen.values())
    print(f"  Ranked picks after dedup: {len(picks)}")

    # Normalise outcome spellings
    for p in picks:
        oc = (p.get('outcome') or '').lower()
        if oc == 'won':    p['outcome'] = 'win'
        elif oc == 'lost': p['outcome'] = 'loss'

    # ── Level-stakes ROI ──────────────────────────────────────────────────────
    # Placed = 0.5 × odds return (half the win price — matches original system formula).
    # Non-runners excluded from settled count (bet never placed).
    total_stake = total_return = 0.0
    wins = places = losses = pending = 0
    for p in picks:
        outcome = (p.get('outcome') or '').lower()
        odds = _settlement_odds(p)
        if outcome in ('win', 'won'):
            wins += 1;    total_stake += UNIT; total_return += UNIT * odds
        elif outcome == 'placed':
            places += 1;  total_stake += UNIT; total_return += UNIT * odds * 0.5
        elif outcome in ('loss', 'lost'):
            losses += 1;  total_stake += UNIT
        elif outcome in ('non_runner', 'nr', 'void'):
            pass   # no bet placed — exclude entirely
        else:
            pending += 1

    settled = wins + places + losses
    profit  = round(total_return - total_stake, 2)
    roi     = round((profit / total_stake * 100) if total_stake > 0 else 0, 1)
    sr      = round((wins / settled * 100) if settled > 0 else 0, 1)

    print(f"  Settled: {settled}  Wins: {wins}  Places: {places}  Losses: {losses}  Pending: {pending}")
    print(f"  Profit: {profit:+.2f}u  ROI: {roi:+.1f}%  Strike: {sr:.1f}%")

    # ── Write to BetBudAICache ─────────────────────────────────────────────────
    now_iso = datetime.now(tz.utc).isoformat()
    ttl_ts  = int((datetime.now(tz.utc) + timedelta(days=32)).timestamp())

    payload = {
        'success':          True,
        'roi':              roi,
        'profit':           profit,
        'total_stake':      float(total_stake),
        'total_return':     round(total_return, 2),
        'wins':             wins,
        'places':           places,
        'losses':           losses,
        'settled':          settled,
        'pending':          pending,
        'strike_rate':      sr,
        'since':            CUMULATIVE_ROI_START,
        'cached_at':        now_iso,
        'methodology_note': 'ROI: level-stakes 1u/pick, all published picks (morning + Live Opportunities), SP used where available.',
    }

    cache_table.put_item(Item={
        'cache_key':  'cumulative_roi',
        'data':       {k: Decimal(str(round(v, 6))) if isinstance(v, float) else v for k, v in payload.items()},
        'cached_at':  now_iso,
        'ttl':        ttl_ts,
        'cache_type': 'daily_roi',
        'updated_at': now_iso,
    })
    print(f"  Wrote to BetBudAICache  roi={roi}%  settled={settled}  TTL={ttl_ts}")

    return {
        'statusCode': 200,
        'success':    True,
        'date':       today,
        'roi':        roi,
        'settled':    settled,
        'wins':       wins,
        'profit':     profit,
    }
