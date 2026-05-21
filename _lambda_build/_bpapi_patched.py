"""
AWS Lambda function to serve betting picks from DynamoDB
Provides REST API for frontend hosted on Amplify
"""
import json
import urllib.request
import urllib.parse
import secrets
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib, os, base64, re
try:
    import stripe
except ImportError:
    stripe = None  # Stripe layer not yet deployed; payment routes will fail gracefully

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
subscribers_table = dynamodb.Table('BetBudAI_Subscribers')
ses_client = boto3.client('ses', region_name='eu-west-1')

SENDER_EMAIL    = 'charles.mccarthy@gmail.com'
SITE_URL        = 'https://www.betbudai.com'

# ── Stripe configuration ────────────────────────────────────────────────────
if stripe:
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
STRIPE_PRICE_PREMIUM = os.environ.get('STRIPE_PRICE_PREMIUM', '')   # price_xxx for €19.99/mo
STRIPE_PRICE_VIP     = os.environ.get('STRIPE_PRICE_VIP', '')       # price_xxx for €99/mo

def _hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256, 32-byte random salt, 200k iterations."""
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return base64.b64encode(salt + key).decode('utf-8')

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

def _settlement_odds(p):
    """Return the best available odds for P&L calculations.
    Prefers sp_odds (set at settlement using Betfair SP/lastPriceTraded)
    over the pre-race exchange price stored at pick time."""
    return float(p.get('sp_odds') or p.get('odds', 0))

def lambda_handler(event, context):
    """Handle API Gateway requests"""
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-admin-token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS preflight — supports both REST API (httpMethod) and HTTP API v2 (requestContext.http.method)
    req_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', '')
    if req_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }

    # ── EventBridge scheduled trigger (no HTTP path) ─────────────────────────
    if event.get('source') == 'aws.events' or event.get('source') == 'scheduled-results':
        print('EventBridge scheduled trigger – running auto_record_pending_results')
        return auto_record_pending_results(headers)

    # Get path - handle both API Gateway and Lambda URL formats
    path = event.get('rawPath', event.get('path', ''))
    method = event.get('requestContext', {}).get('http', {}).get('method', event.get('httpMethod', 'GET'))
    
    print(f"Request: {method} {path}")
    print(f"Event keys: {event.keys()}")
    print(f"Path check - 'workflow/run' in path: {'workflow/run' in path}")
    
    try:
        # Route requests - check more specific paths first
        if 'cheltenham/picks/save' in path:
            return save_cheltenham_picks_lambda(headers)
        elif 'cheltenham/picks' in path:
            return get_cheltenham_picks_lambda(headers, event)
        elif 'cheltenham/races' in path:
            return get_cheltenham_races_lambda(headers)
        elif 'favs-run' in path:
            return get_favs_run_lambda(headers, event)
        elif 'learning/apply' in path:
            return apply_learning_lambda(headers, event)
        elif 'results/auto-record' in path:
            return auto_record_pending_results(headers)
        elif 'admin/config' in path and method == 'GET':
            return admin_get_config(headers, event)
        elif 'admin/config' in path and method == 'POST':
            return admin_save_config(headers, event)
        elif 'admin/subscribers' in path and method == 'GET':
            return admin_get_subscribers(headers, event)
        elif 'login' in path and method == 'POST':
            return login_subscriber(headers, event)
        elif 'verify-email' in path:
            return verify_email_token(headers, event)
        elif 'register' in path and method == 'POST':
            return register_subscriber(headers, event)
        elif 'create-checkout-session' in path and method == 'POST':
            return create_checkout_session(headers, event)
        elif 'stripe-webhook' in path and method == 'POST':
            return handle_stripe_webhook(headers, event)
        elif 'subscription-status' in path and method == 'POST':
            return get_subscription_status(headers, event)
        elif 'customer-portal' in path and method == 'POST':
            return create_customer_portal(headers, event)
        elif 'cancel-subscription' in path and method == 'POST':
            return cancel_subscription(headers, event)
        elif 'results/export-csv' in path:
            return export_roi_csv(headers)
        elif 'results/cumulative-roi' in path:
            return get_cumulative_roi(headers)
        elif 'results/yesterday' in path:
            return check_yesterday_results(headers)
        elif 'results/today' in path or path.endswith('/results'):
            return check_today_results(headers)
        elif 'picks/greyhounds' in path:
            return get_greyhound_picks(headers)
        elif 'picks/yesterday' in path:
            return get_yesterday_picks(headers)
        elif 'picks/today' in path:
            return get_today_picks(headers)
        elif 'major-race-analysis/run' in path and method == 'POST':
            return run_major_race_analysis(headers, event)
        elif 'major-race-analysis' in path and method == 'GET':
            return get_major_race_analysis(headers)
        elif 'workflow/run' in path or 'workflow' in path:
            return trigger_workflow(headers)
        elif 'picks' in path:
            return get_all_picks(headers)
        elif 'health' in path:
            return get_health(headers)
        elif path == '/':
            # Root path - return API info
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'service': 'Betting Picks API',
                    'endpoints': [
                        '/api/picks/today',
                        '/api/picks/yesterday',
                        '/api/picks',
                        '/api/results',
                        '/api/results/today',
                        '/api/workflow/run',
                        '/api/health'
                    ]
                })
            }
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': f'Endpoint not found: {path}'
                })
            }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def get_all_picks(headers):
    """Get all picks from DynamoDB"""
    response = table.scan()
    items = response.get('Items', [])
    
    # Convert Decimals to floats
    items = [decimal_to_float(item) for item in items]
    
    # Sort by timestamp descending
    items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'picks': items,
            'count': len(items)
        })
    }

def get_today_picks(headers):
    """Get today's picks only - filter to show only upcoming horse races"""
    from datetime import timezone as _tz
    today = datetime.now(_tz.utc).strftime('%Y-%m-%d')

    # ── 1PM BST GATE ─────────────────────────────────────────────────────────
    # Hold picks until 12:00 UTC (1:00pm BST) each day.
    # The morning analysis runs at ~10:00 UTC but may re-score horses as going /
    # flags update before racing.  Showing picks only after 1pm ensures the last
    # lunchtime re-check has settled and we're committed to the best version.
    _now_utc = datetime.now(_tz.utc)
    if _now_utc.hour < 12:
        _mins = (12 - _now_utc.hour) * 60 - _now_utc.minute
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success':          True,
                'picks':            [],
                'count':            0,
                'date':             today,
                'analysis_pending': True,
                'pending_reason':   f'Picks confirmed at 1:00pm — rechecking going & flags ({_mins} min)',
                'message':          'Picks locked until 1pm BST to allow full morning analysis to complete',
            })
        }

    # Use query with partition key for better performance
    try:
        response = table.query(
            KeyConditionExpression='bet_date = :today',
            ExpressionAttributeValues={':today': today}
        )
    except Exception as e:
        print(f"Query failed, falling back to scan: {e}")
        # Fallback to scan if query fails
        response = table.scan(
            FilterExpression='(#d = :today OR bet_date = :today)',
            ExpressionAttributeNames={'#d': 'date'},
            ExpressionAttributeValues={':today': today}
        )
    
    items = response.get('Items', [])
    items = [decimal_to_float(item) for item in items]
    
    # Filter out greyhounds - only show horses (accept both 'horses' and 'Horse Racing')
    horse_items = [item for item in items if item.get('sport', 'horses') in ['horses', 'Horse Racing', 'horse racing']]
    
    # CRITICAL: Only ranked UI picks OR dropped picks
    horse_items = [item for item in horse_items if (item.get('show_in_ui') == True and int(item.get('pick_rank', 0)) > 0) or item.get('is_dropped') == True]
    
    # Filter to System A only: picks with stake <= 10 (excludes learning_workflow picks)
    # System A = Comprehensive scoring system with £5-6 stakes (actual bets)
    # System B = Learning workflow with £12-30 stakes (data collection only)
    horse_items = [item for item in horse_items if float(item.get('stake', 0)) <= 10]
    
    # DEMO MODE: On Jan 20, 2026, show ALL picks regardless of time
    # This allows showing past races during the demo
    if today == '2026-01-20':
        print(f"DEMO MODE: Showing all {len(horse_items)} picks for {today}")
        future_picks = horse_items
    else:
        # Filter out races that have already started
        from datetime import timezone as _tz
        now_utc = datetime.now(_tz.utc)
        future_picks = []
        
        for item in horse_items:
            race_time_str = item.get('race_time', '')
            if race_time_str:
                try:
                    # Parse race time (ISO format with offset) and compare in UTC
                    race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
                    if race_time.astimezone(_tz.utc) > now_utc:
                        future_picks.append(item)
                except Exception as e:
                    print(f"Error parsing race time {race_time_str}: {e}")
                    # Include if we can't parse (safer than excluding)
                    future_picks.append(item)
            else:
                # Include if no race time (safer than excluding)
                future_picks.append(item)
    
    # ONE PICK PER RACE: keep only the highest-scoring pick per race
    seen_races = {}
    for pick in future_picks:
        race_key = (pick.get('course', ''), str(pick.get('race_time', ''))[:16])
        existing = seen_races.get(race_key)
        if not existing or float(pick.get('comprehensive_score', 0)) > float(existing.get('comprehensive_score', 0)):
            seen_races[race_key] = pick
    future_picks = list(seen_races.values())
    print(f"After dedup (1 pick per race): {len(future_picks)} picks")

    # Build full race card for each pick by scanning all items for the same (course, race_time)
    for pick in future_picks:
        pick_course    = pick.get('course', '')
        pick_race_time = pick.get('race_time', '')
        pick_score     = float(pick.get('comprehensive_score', 0) or 0)

        # Preserve the all_horses list saved by the workflow (full race card with all runners scored)
        # This is used as fallback if DynamoDB only has one record for this race (the pick itself)
        stored_all_horses = pick.get('all_horses', [])

        # All candidates for this race with a valid score
        race_candidates = [
            item for item in items
            if item.get('course') == pick_course
            and item.get('race_time') == pick_race_time
            and item.get('comprehensive_score') is not None
            and float(item.get('comprehensive_score', 0) or 0) != 0
        ]

        # Deduplicate by horse name — keep highest-scoring entry
        seen_runners = {}
        for h in race_candidates:
            hname  = (h.get('horse') or '').strip()
            hscore = float(h.get('comprehensive_score', 0) or 0)
            if hname not in seen_runners or hscore > seen_runners[hname]:
                seen_runners[hname] = hscore

        # Build sorted race card (best score first)
        race_card = sorted(
            [{'name': n, 'score': s} for n, s in seen_runners.items()],
            key=lambda x: x['score'], reverse=True
        )

        # Attach full all_horses list to pick (with jockey/trainer from item)
        horse_lookup = {}
        for h in race_candidates:
            hname  = (h.get('horse') or '').strip()
            hscore = float(h.get('comprehensive_score', 0) or 0)
            if hname not in horse_lookup or hscore > float(horse_lookup[hname].get('comprehensive_score', 0) or 0):
                horse_lookup[hname] = h

        pick['all_horses'] = [
            {
                'horse':   entry['name'],
                'jockey':  horse_lookup[entry['name']].get('jockey', '') if entry['name'] in horse_lookup else '',
                'trainer': horse_lookup[entry['name']].get('trainer', '') if entry['name'] in horse_lookup else '',
                'odds':    float(horse_lookup[entry['name']].get('odds', 0) or 0) if entry['name'] in horse_lookup else 0,
                'score':   round(entry['score'], 0),
            }
            for entry in race_card
        ]

        # If race_candidates only found our pick (1 entry), fall back to the full all_horses list
        # stored by the workflow in DynamoDB — this contains all scored runners in the race
        if len(pick['all_horses']) <= 1 and stored_all_horses and len(stored_all_horses) > 1:
            pick['all_horses'] = [
                {
                    'horse':   h.get('horse', ''),
                    'jockey':  h.get('jockey', ''),
                    'trainer': h.get('trainer', ''),
                    'odds':    float(h.get('odds', 0) or 0),
                    'score':   float(h.get('score', 0) or 0),
                }
                for h in stored_all_horses
            ]

        # next_best / score_gap from rivals (exclude our pick)
        rivals = [r for r in race_card if r['name'] != pick.get('horse', '')]
        if rivals:
            best_rival = rivals[0]
            pick['next_best_score'] = best_rival['score']
            pick['next_best_horse'] = best_rival['name']
            pick['score_gap'] = pick_score - best_rival['score']
        else:
            pick['next_best_score'] = 0
            pick['next_best_horse'] = ''
            pick['score_gap'] = 0

    # Sort by score and limit to top 5 picks per day
    future_picks.sort(key=lambda x: float(x.get('comprehensive_score') or x.get('analysis_score') or 0), reverse=True)
    future_picks = future_picks[:5]
    # Re-sort top 5 by race time for display
    future_picks.sort(key=lambda x: x.get('race_time', ''))

    # Map reasons -> selection_reasons for UI compatibility
    race_fields = {}
    for pick in future_picks:
        pick['selection_reasons'] = pick.get('reasons', [])

    print(f"Total picks: {len(items)}, Horse picks: {len(horse_items)}, Future picks: {len(future_picks)} (top 5 by score)")
    
    # Calculate workflow schedule (runs every 30 min at :15 and :45)
    now = datetime.utcnow()
    current_minute = now.minute
    
    # Determine last run time
    if current_minute >= 45:
        last_run_minute = 45
    elif current_minute >= 15:
        last_run_minute = 15
    else:
        # Last run was previous hour at :45
        last_run_minute = 45
        now = now - timedelta(hours=1)
    
    last_run = now.replace(minute=last_run_minute, second=0, microsecond=0)
    if current_minute < 15:
        last_run = last_run - timedelta(hours=1)
    
    # Determine next run time
    if current_minute < 15:
        next_run = now.replace(minute=15, second=0, microsecond=0)
    elif current_minute < 45:
        next_run = now.replace(minute=45, second=0, microsecond=0)
    else:
        # Next run is next hour at :15
        next_run = (now + timedelta(hours=1)).replace(minute=15, second=0, microsecond=0)
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'picks': future_picks,
            'count': len(future_picks),
            'date': today,
            'last_run': last_run.isoformat() + 'Z',
            'next_run': next_run.isoformat() + 'Z',
            'race_fields': race_fields,
            'message': 'No selections met the criteria' if len(future_picks) == 0 else f'{len(future_picks)} upcoming races'
        })
    }

def get_greyhound_picks(headers):
    """Get today's greyhound picks only - filter to show only upcoming races"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get today's picks and filter for greyhounds
    response = table.scan(
        FilterExpression='(#d = :today OR bet_date = :today) AND sport = :sport',
        ExpressionAttributeNames={'#d': 'date'},
        ExpressionAttributeValues={
            ':today': today,
            ':sport': 'greyhounds'
        }
    )
    
    items = response.get('Items', [])
    items = [decimal_to_float(item) for item in items]
    
    # DEMO MODE: On Jan 20, 2026, show ALL picks regardless of time
    if today == '2026-01-20':
        print(f"DEMO MODE: Showing all {len(items)} greyhound picks for {today}")
        future_picks = items
    else:
        # Filter out races that have already started
        now = datetime.utcnow()
        future_picks = []
        
        for item in items:
            race_time_str = item.get('race_time', '')
            if race_time_str:
                try:
                    # Parse race time (ISO format)
                    race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
                    # Only include if race is in the future
                    if race_time.replace(tzinfo=None) > now:
                        future_picks.append(item)
                except Exception as e:
                    print(f"Error parsing race time {race_time_str}: {e}")
                    # Include if we can't parse (safer than excluding)
                    future_picks.append(item)
            else:
                # Include if no race time (safer than excluding)
                future_picks.append(item)
    
    # Sort by race time (soonest first)
    future_picks.sort(key=lambda x: x.get('race_time', ''))
    
    print(f"Greyhound picks today: {len(items)}, Future greyhound picks: {len(future_picks)}")
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'picks': future_picks,
            'count': len(future_picks),
            'date': today,
            'sport': 'greyhounds'
        })
    }

def get_yesterday_picks(headers):
    """Get yesterday's picks with results (System A only - actual bets)"""
    from datetime import timedelta
    from boto3.dynamodb.conditions import Key
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"[DEBUG] Querying for yesterday: {yesterday}")
    
    # Use query with partition key for better performance (bet_date is the partition key)
    response = table.query(
        KeyConditionExpression=Key('bet_date').eq(yesterday)
    )
    
    items = response.get('Items', [])
    print(f"[DEBUG] Raw items from query: {len(items)}")
    items = [decimal_to_float(item) for item in items]
    
    # Filter to System A only: picks with stake <= 10 (excludes learning_workflow picks)
    # System A = Comprehensive scoring system with £5-6 stakes (actual bets)
    # System B = Learning workflow with £12-30 stakes (data collection only)
    before_filter = len(items)
    items = [item for item in items if float(item.get('stake', 0)) <= 10]
    print(f"[DEBUG] After stake filter (<= 10): {len(items)} (was {before_filter})")
    
    # Normalize outcome values for frontend compatibility
    # Database uses: 'won', 'WON', 'lost', 'LOST'
    # Frontend expects: 'win', 'loss', 'placed'
    for item in items:
        outcome = item.get('outcome', '').lower() if item.get('outcome') else None
        if outcome in ['won', 'win']:
            item['outcome'] = 'win'
        elif outcome in ['lost', 'loss']:
            item['outcome'] = 'loss'
        elif outcome in ['placed', 'place']:
            item['outcome'] = 'placed'
        # Keep None or other values as-is (for pending/voided)
    
    # Sort by race time
    items.sort(key=lambda x: x.get('race_time', ''))
    
    print(f"Yesterday's picks: {len(items)}")
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'picks': items,
            'count': len(items),
            'date': yesterday
        })
    }


def get_health(headers):
    """Health check endpoint"""
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'status': 'ok',
            'service': 'betting-picks-api',
            'timestamp': datetime.now().isoformat()
        })
    }

def get_cumulative_roi(headers):
    """Cumulative level-stakes ROI since 2026-03-22, deduped by race identity."""
    from boto3.dynamodb.conditions import Key, Attr
    from datetime import timedelta, date as _date
    CUMULATIVE_ROI_START = '2026-03-22'
    try:
        # Query day-by-day using the bet_date partition key (avoids expensive full-table scan)
        all_items = []
        start_d = _date.fromisoformat(CUMULATIVE_ROI_START)
        today_d = _date.today()
        cur = start_d
        while cur <= today_d:
            day_kwargs = {
                'KeyConditionExpression': Key('bet_date').eq(str(cur)),
                'ProjectionExpression': 'bet_date, bet_id, horse, course, race_time, show_in_ui, is_learning_pick, outcome, sp_odds, odds, ew_fraction, bet_type',
            }
            while True:
                resp = table.query(**day_kwargs)
                all_items.extend(resp.get('Items', []))
                lek = resp.get('LastEvaluatedKey')
                if not lek:
                    break
                day_kwargs['ExclusiveStartKey'] = lek
            cur += timedelta(days=1)

        picks = [decimal_to_float(i) for i in all_items]
        picks = [
            p for p in picks
            if p.get('course') and p.get('course') != 'Unknown'
            and p.get('horse') and p.get('horse') != 'Unknown'
            and p.get('show_in_ui') is True
            and not p.get('is_learning_pick', False)
            and not p.get('is_dropped', False)
        ]

        # Deduplicate by race identity (course + race_time), keep most-recently dated record
        # so outcome corrections always win over the original pick record.
        seen = {}
        for p in picks:
            k = (p.get('course', ''), p.get('race_time', ''))
            if k not in seen or p.get('bet_date', '') > seen[k].get('bet_date', ''):
                seen[k] = p
        picks = list(seen.values())

        # Normalise outcome spellings
        for p in picks:
            oc = (p.get('outcome') or '').lower()
            if oc in ('won',):    p['outcome'] = 'win'
            elif oc in ('lost',): p['outcome'] = 'loss'

        # Level-stakes ROI (1 unit per pick — standard tipster ROI)
        UNIT = 1.0
        total_stake = total_return = 0.0
        wins = places = losses = pending = 0
        for p in picks:
            outcome = (p.get('outcome') or '').lower()
            odds = _settlement_odds(p)
            ef   = float(p.get('ew_fraction') or 0.25)
            if outcome == 'win':
                wins += 1; total_stake += UNIT; total_return += UNIT * odds
            elif outcome == 'placed':
                places += 1; total_stake += UNIT
                total_return += (UNIT/2) * (1 + (odds-1) * ef)
            elif outcome == 'loss':
                losses += 1; total_stake += UNIT
            else:
                pending += 1

        profit  = total_return - total_stake
        roi     = round((profit / total_stake * 100) if total_stake > 0 else 0, 1)
        settled = wins + places + losses
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success':      True,
                'start_date':   CUMULATIVE_ROI_START,
                'roi':          roi,
                'profit':       round(profit, 2),
                'total_stake':  round(total_stake, 2),
                'total_return': round(total_return, 2),
                'wins':         wins,
                'places':       places,
                'losses':       losses,
                'pending':      pending,
                'settled':      settled,
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': str(e)})
        }


def export_roi_csv(headers):
    """Export all settled UI picks as CSV for ROI verification."""
    from boto3.dynamodb.conditions import Key, Attr
    from datetime import date as _date, timedelta
    from concurrent.futures import ThreadPoolExecutor
    CUMULATIVE_ROI_START = '2026-03-22'
    try:
        start_d = _date.fromisoformat(CUMULATIVE_ROI_START)
        today_d = _date.today()
        dates = [(start_d + timedelta(days=i)).isoformat()
                 for i in range((today_d - start_d).days + 1)]

        def _query_date(d):
            items = []
            kwargs = {
                'KeyConditionExpression': Key('bet_date').eq(d),
                'FilterExpression': Attr('show_in_ui').eq(True),
                'ProjectionExpression': 'bet_date, bet_id, horse, course, race_time, show_in_ui, is_learning_pick, outcome, sp_odds, odds, ew_fraction, bet_type, comprehensive_score, finish_position, winner_horse, number_of_places, confidence_grade, jockey, trainer',
            }
            while True:
                resp = table.query(**kwargs)
                items.extend(resp.get('Items', []))
                if 'LastEvaluatedKey' not in resp:
                    break
                kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']
            return items

        all_items = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            for batch in ex.map(_query_date, dates):
                all_items.extend(batch)

        picks = [decimal_to_float(i) for i in all_items]
        picks = [p for p in picks
                 if p.get('horse') and p.get('horse') != 'Unknown'
                 and p.get('course') and p.get('course') != 'Unknown'
                 and not p.get('is_learning_pick', False)]

        # Deduplicate by race identity (course + race_time)
        seen = {}
        for p in picks:
            k = (p.get('course', ''), p.get('race_time', ''))
            if k not in seen or p.get('bet_date', '') > seen[k].get('bet_date', ''):
                seen[k] = p
        picks = sorted(seen.values(), key=lambda x: x.get('race_time', '') or x.get('bet_date', ''))

        # Build CSV
        csv_lines = ['Date,Race Time,Course,Horse,Trainer,Jockey,Odds,SP Odds,EW Fraction,Bet Type,Score,Grade,Outcome,Finish Position,Winner,Places Paid']
        UNIT = 1.0
        total_stake = total_return = 0.0
        settled_count = 0

        for p in picks:
            oc = (p.get('outcome') or '').lower()
            if oc in ('won',): oc = 'win'
            elif oc in ('lost',): oc = 'loss'

            odds = _settlement_odds(p)
            sp_odds = float(p.get('sp_odds') or 0)
            pre_odds = float(p.get('odds') or 0)
            ef = float(p.get('ew_fraction') or 0.25)

            if oc == 'win':
                settled_count += 1; total_stake += UNIT; total_return += UNIT * odds
            elif oc in ('placed', 'place'):
                oc = 'placed'
                settled_count += 1; total_stake += UNIT
                total_return += (UNIT / 2) * (1 + (odds - 1) * ef)
            elif oc == 'loss':
                settled_count += 1; total_stake += UNIT

            race_time = (p.get('race_time') or '')[:16].replace('T', ' ')
            row = ','.join([
                p.get('bet_date', ''),
                race_time,
                '"' + (p.get('course') or '').replace('"', '""') + '"',
                '"' + (p.get('horse') or '').replace('"', '""') + '"',
                '"' + (p.get('trainer') or '').replace('"', '""') + '"',
                '"' + (p.get('jockey') or '').replace('"', '""') + '"',
                str(pre_odds),
                str(sp_odds),
                str(ef),
                p.get('bet_type', 'Each Way'),
                str(float(p.get('comprehensive_score', 0))),
                p.get('confidence_grade', ''),
                oc or 'pending',
                str(p.get('finish_position', '')),
                '"' + (p.get('winner_horse') or '').replace('"', '""') + '"',
                str(p.get('number_of_places', '')),
            ])
            csv_lines.append(row)

        profit = total_return - total_stake
        roi_pct = round((profit / total_stake * 100) if total_stake > 0 else 0, 1)
        csv_lines.append('')
        csv_lines.append(f'SUMMARY,Settled: {settled_count},Stake: {total_stake:.2f},Return: {total_return:.2f},Profit: {profit:.2f},ROI: {roi_pct}%')

        csv_headers = dict(headers)
        csv_headers['Content-Type'] = 'text/csv'
        csv_headers['Content-Disposition'] = 'attachment; filename="BetBudAI_ROI_Data.csv"'
        return {
            'statusCode': 200,
            'headers': csv_headers,
            'body': '\n'.join(csv_lines)
        }
    except Exception as e:
        print(f'export_roi_csv error: {e}')
        import traceback; traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': str(e)})
        }


def check_yesterday_results(headers):
    """Check results for yesterday's UI picks only (show_in_ui=True)"""
    from boto3.dynamodb.conditions import Key
    from datetime import timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get ALL yesterday's picks using partition key query (paginated)
    response = table.query(
        KeyConditionExpression=Key('bet_date').eq(yesterday)
    )
    all_picks = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression=Key('bet_date').eq(yesterday),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        all_picks.extend(response.get('Items', []))

    all_picks = [decimal_to_float(item) for item in all_picks]
    
    # Filter for UI picks only — exclude dropped picks
    picks = [item for item in all_picks if item.get('show_in_ui') == True and not item.get('is_dropped', False)]
    
    # Normalize outcome values for frontend compatibility
    # Database uses: 'won', 'WON', 'lost', 'LOST'
    # Frontend expects: 'win', 'loss', 'placed'
    for item in picks:
        outcome = item.get('outcome', '').lower() if item.get('outcome') else None
        if outcome in ['won', 'win']:
            item['outcome'] = 'win'
        elif outcome in ['lost', 'loss']:
            item['outcome'] = 'loss'
        elif outcome in ['placed', 'place']:
            item['outcome'] = 'placed'
        # Keep None or other values as-is (for pending/voided)
    
    print(f"Yesterday ({yesterday}) - Total picks: {len(all_picks)}, UI picks: {len(picks)}")

    # Exclude retrospective picks (created >30 min after race started, accounting for BST)
    def _is_retro_yest(pick):
        import calendar as _cal
        from datetime import timezone as _tz, timedelta as _td
        def _uk_off(d):
            def _last_sun(y, m):
                last = _cal.monthrange(y, m)[1]
                return next(day for day in range(last, last - 7, -1)
                            if datetime(y, m, day).weekday() == 6)
            bst_start = datetime(d.year, 3, _last_sun(d.year, 3), 1, tzinfo=_tz.utc)
            bst_end   = datetime(d.year, 10, _last_sun(d.year, 10), 1, tzinfo=_tz.utc)
            return 1 if bst_start <= datetime(d.year, d.month, d.day, tzinfo=_tz.utc) < bst_end else 0
        created_s = str(pick.get('created_at', '') or '')
        race_rt_s = str(pick.get('race_time', '') or '')
        if len(created_s) < 16 or len(race_rt_s) < 16 or created_s[:10] != race_rt_s[:10]:
            return False
        try:
            race_utc    = datetime.fromisoformat(race_rt_s).astimezone(_tz.utc)
            uk_off      = _uk_off(race_utc.date())
            created_utc = datetime.fromisoformat(created_s[:16]) - _td(hours=uk_off)
            return (created_utc - race_utc).total_seconds() > 30 * 60
        except Exception:
            return False

    picks = [p for p in picks if not _is_retro_yest(p)]

    # ONE PICK PER RACE: keep highest-scoring pick, normalise race_time to strip tz offset
    def _norm_rt_y(rt):
        return str(rt or '')[:16]

    seen_races = {}
    for pick in picks:
        race_key = (pick.get('course', ''), _norm_rt_y(pick.get('race_time', '')))
        existing = seen_races.get(race_key)
        score = float(pick.get('comprehensive_score') or pick.get('analysis_score') or 0)
        existing_score = float(existing.get('comprehensive_score') or existing.get('analysis_score') or 0) if existing else 0
        if not existing or score > existing_score:
            seen_races[race_key] = pick
    picks = list(seen_races.values())
    picks.sort(key=lambda x: x.get('race_time', ''))
    print(f"After retro-filter + dedup: {len(picks)} picks")

    if not picks:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': f'No picks for yesterday',
                'date': yesterday,
                'summary': {'total_picks': 0, 'wins': 0, 'losses': 0, 'pending': 0},
                'horses': {'summary': None, 'picks': []},
                'greyhounds': {'summary': None, 'picks': []},
                'picks': []
            })
        }
    
    # Calculate stats from existing outcomes (case-insensitive)
    wins = sum(1 for p in picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON'])
    places = sum(1 for p in picks if str(p.get('outcome', '')).upper() == 'PLACED')
    losses = sum(1 for p in picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST'])
    pending = sum(1 for p in picks if str(p.get('outcome', '')).upper() in ['PENDING', ''] or p.get('outcome') is None)
    
    # EXCLUDE PENDING from stake/return calculations - only count resolved bets
    resolved_picks = [p for p in picks if str(p.get('outcome', '')).upper() not in ['PENDING', ''] and p.get('outcome') is not None]
    
    total_stake = sum(float(p.get('stake', 1.0)) for p in resolved_picks)

    # Calculate total_return from first principles (don't trust stored profit field)
    total_return = 0.0
    for p in resolved_picks:
        outcome = str(p.get('outcome', '')).upper()
        if outcome in ['WIN', 'WON']:
            stake = float(p.get('stake', 1.0))
            odds = _settlement_odds(p)
            bet_type = p.get('bet_type', 'WIN').upper()
            if bet_type == 'WIN':
                total_return += stake * odds
            else:  # EW
                ew_fraction = float(p.get('ew_fraction', 0.2) or 0.2)
                total_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
        elif outcome == 'PLACED':
            stake = float(p.get('stake', 1.0))
            odds = _settlement_odds(p)
            ew_fraction = float(p.get('ew_fraction', 0.2) or 0.2)
            total_return += (stake/2) * (1 + (odds-1) * ew_fraction)

    profit = total_return - total_stake
    roi = (profit / total_stake * 100) if total_stake > 0 else 0
    
    # Build race_fields: all runners for yesterday grouped by race (for full race card display)
    race_fields = {}
    for item in all_picks:
        if item.get('sport') != 'horses':
            continue
        course    = item.get('course', '') or item.get('venue', '')
        race_time = item.get('race_time', '')
        if not course or not race_time:
            continue
        key = f"{course}|{race_time}"
        if key not in race_fields:
            race_fields[key] = []
        score = float(item.get('comprehensive_score') or item.get('analysis_score') or 0)
        race_fields[key].append({
            'horse':     item.get('horse', ''),
            'jockey':    item.get('jockey', ''),
            'trainer':   item.get('trainer', ''),
            'odds':      float(item.get('odds', 0) or 0),
            'score':     score,
            'pick_rank': 1 if item.get('show_in_ui') else 0,
        })
    for key in race_fields:
        race_fields[key].sort(key=lambda r: float(r.get('score', 0)), reverse=True)

    # Separate by sport
    horse_picks = [p for p in picks if p.get('sport') == 'horses']
    greyhound_picks = [p for p in picks if p.get('sport') == 'greyhounds']
    
    def calculate_sport_summary(sport_picks):
        if not sport_picks:
            return None
        
        sport_wins = sum(1 for p in sport_picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON'])
        sport_places = sum(1 for p in sport_picks if str(p.get('outcome', '')).upper() == 'PLACED')
        sport_losses = sum(1 for p in sport_picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST'])
        sport_pending = sum(1 for p in sport_picks if str(p.get('outcome', '')).upper() in ['PENDING', ''] or p.get('outcome') is None)
        
        # EXCLUDE PENDING from stake/return calculations - only count resolved bets
        sport_resolved = [p for p in sport_picks if str(p.get('outcome', '')).upper() not in ['PENDING', ''] and p.get('outcome') is not None]
        sport_stake = sum(float(p.get('stake', 1.0)) for p in sport_resolved)
        sport_return = 0.0
        for p in sport_resolved:
            outcome = str(p.get('outcome', '')).upper()
            if outcome in ['WIN', 'WON']:
                s = float(p.get('stake', 1.0))
                o = _settlement_odds(p)
                bt = p.get('bet_type', 'WIN').upper()
                if bt == 'WIN':
                    sport_return += s * o
                else:  # EW
                    ewf = float(p.get('ew_fraction', 0.2) or 0.2)
                    sport_return += (s/2) * o + (s/2) * (1 + (o-1) * ewf)
            elif outcome == 'PLACED':
                s = float(p.get('stake', 1.0))
                o = _settlement_odds(p)
                ewf = float(p.get('ew_fraction', 0.2) or 0.2)
                sport_return += (s/2) * (1 + (o-1) * ewf)
        sport_profit = sport_return - sport_stake
        sport_roi = (sport_profit / sport_stake * 100) if sport_stake > 0 else 0
        
        return {
            'total_picks': len(sport_picks),
            'wins': sport_wins,
            'places': sport_places,
            'losses': sport_losses,
            'pending': sport_pending,
            'total_stake': round(sport_stake, 2),
            'total_return': round(sport_return, 2),
            'profit': round(sport_profit, 2),
            'roi': round(sport_roi, 1),
            'strike_rate': round((sport_wins / (sport_wins + sport_losses) * 100) if (sport_wins + sport_losses) > 0 else 0, 1)
        }
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'date': yesterday,
            'summary': {
                'total_picks': len(picks),
                'wins': wins,
                'places': places,
                'losses': losses,
                'pending': pending,
                'total_stake': round(total_stake, 2),
                'total_return': round(total_return, 2),
                'profit': round(profit, 2),
                'roi': round(roi, 1),
                'strike_rate': round((wins / (wins + losses) * 100) if (wins + losses) > 0 else 0, 1)
            },
            'horses': {
                'summary': calculate_sport_summary(horse_picks),
                'picks': horse_picks
            },
            'greyhounds': {
                'summary': calculate_sport_summary(greyhound_picks),
                'picks': greyhound_picks
            },
            'picks': picks,
            'race_fields': race_fields,
            'debug_timestamp': datetime.now().isoformat()
        })
    }

def check_today_results(headers):
    """Check results for today's UI picks only (show_in_ui=True, plus dropped picks)"""
    from boto3.dynamodb.conditions import Key
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get ALL today's picks using partition key query - WITH PAGINATION
    all_picks = []
    response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
    all_picks.extend(response.get('Items', []))
    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression=Key('bet_date').eq(today),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        all_picks.extend(response.get('Items', []))

    all_picks = [decimal_to_float(item) for item in all_picks]
    print(f"Total picks retrieved (paginated): {len(all_picks)}")

    # Filter for ranked UI picks AND dropped picks — keep others for learning
    # pick_rank > 0 is the authoritative filter: ensures rank-0 records with
    # show_in_ui=True (from legacy/buggy refreshes) are excluded.
    picks = [item for item in all_picks
             if (item.get('show_in_ui') == True and int(item.get('pick_rank', 0)) > 0)
             or item.get('is_dropped') == True]

    # Filter: race must be TODAY (excludes yesterday's races stored with today's bet_date)
    picks = [item for item in picks if str(item.get('race_time', '')).startswith(today)]

    # Exclude retrospective picks: created more than 30 min after the race started.
    # race_time has an explicit UTC offset (+00:00 or +01:00); created_at is UK
    # local time (no suffix). Compare both in UTC so BST offsets don't confuse things.
    def _is_retrospective(pick):
        import calendar as _cal
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        def _uk_off(d):
            def _last_sun(y, m):
                last = _cal.monthrange(y, m)[1]
                return next(day for day in range(last, last - 7, -1)
                            if _dt(y, m, day).weekday() == 6)
            bst_start = _dt(d.year, 3, _last_sun(d.year, 3), 1, tzinfo=_tz.utc)
            bst_end   = _dt(d.year, 10, _last_sun(d.year, 10), 1, tzinfo=_tz.utc)
            return 1 if bst_start <= _dt(d.year, d.month, d.day, tzinfo=_tz.utc) < bst_end else 0
        created_s = str(pick.get('created_at', '') or '')
        race_rt_s = str(pick.get('race_time', '') or '')
        if len(created_s) < 16 or len(race_rt_s) < 16 or created_s[:10] != race_rt_s[:10]:
            return False
        try:
            race_utc    = _dt.fromisoformat(race_rt_s).astimezone(_tz.utc)
            uk_off      = _uk_off(race_utc.date())
            created_utc = _dt.fromisoformat(created_s[:16]) - _td(hours=uk_off)
            return (created_utc - race_utc).total_seconds() > 30 * 60
        except Exception:
            return False

    picks = [p for p in picks if not _is_retrospective(p)]

    # ONE PICK PER RACE: keep only the highest-scoring pick per (course, race_time)
    # Normalise race_time to YYYY-MM-DDTHH:MM (strip timezone offset) so that
    # records stored as +00:00 and +01:00 for the same local UK race are deduped.
    def _norm_rt(rt):
        s = str(rt or '')
        return s[:16]  # e.g. "2026-03-31T14:15" from any offset variant

    seen_races = {}
    for pick in picks:
        race_key = (pick.get('course', ''), _norm_rt(pick.get('race_time', '')))
        existing = seen_races.get(race_key)
        score = float(pick.get('comprehensive_score') or pick.get('analysis_score') or 0)
        existing_score = float(existing.get('comprehensive_score') or existing.get('analysis_score') or 0) if existing else 0
        if not existing or score > existing_score:
            seen_races[race_key] = pick
    picks = list(seen_races.values())
    # Sort by race_time for display (top-N cap applied at pick selection time, not here)
    picks.sort(key=lambda x: x.get('race_time', ''))
    print(f"After dedup: {len(picks)} picks")

    # Normalize outcome values for frontend compatibility
    # Database uses: 'won', 'WON', 'lost', 'LOST'
    # Frontend expects: 'win', 'loss', 'placed'
    for item in picks:
        outcome = item.get('outcome', '').lower() if item.get('outcome') else None
        if outcome in ['won', 'win']:
            item['outcome'] = 'win'
        elif outcome in ['lost', 'loss']:
            item['outcome'] = 'loss'
        elif outcome in ['placed', 'place']:
            item['outcome'] = 'placed'
        # Keep None or other values as-is (for pending/voided)
    
    if not picks:
        print("NO PICKS for today - returning empty")
        # Calculate next run time (every 2 hours, on the hour)
        now = datetime.now()
        current_hour = now.hour
        # Round up to next 2-hour boundary
        next_hour = ((current_hour // 2) + 1) * 2
        if next_hour >= 24:
            next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            next_run = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': f'No selections met the criteria',
                'date': today,
                'last_run': now.strftime('%Y-%m-%d %H:%M:%S'),
                'next_run': next_run.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': {'total_picks': 0, 'wins': 0, 'losses': 0, 'pending': 0},
                'horses': {'summary': None, 'picks': []},
                'greyhounds': {'summary': None, 'picks': []},
                'picks': []
            })
        }
    
    # Use all picks for results checking
    print(f"Proceeding with {len(picks)} picks from today")
    
    # Use existing outcomes from database (already fetched by fetch_today_results.py)
    # No need to call Betfair API - outcomes are already in the picks
    picks_with_results = picks
    
    # Calculate overall stats from existing outcomes (case-insensitive)
    wins = sum(1 for p in picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON'])
    places = sum(1 for p in picks if str(p.get('outcome', '')).upper() == 'PLACED')
    losses = sum(1 for p in picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST'])
    pending = sum(1 for p in picks if str(p.get('outcome', '')).upper() in ['PENDING', ''] or p.get('outcome') is None)
    
    # EXCLUDE PENDING from stake/return calculations - only count resolved bets
    resolved_picks = [p for p in picks if str(p.get('outcome', '')).upper() not in ['PENDING', ''] and p.get('outcome') is not None]
    
    total_stake = sum(float(p.get('stake', 2.0)) for p in resolved_picks)
    
    # Calculate returns based on outcomes (only resolved bets)
    total_return = 0
    for p in resolved_picks:
        outcome = str(p.get('outcome', '')).upper()
        if outcome in ['WIN', 'WON']:
            stake = float(p.get('stake', 2.0))
            odds = _settlement_odds(p)
            bet_type = p.get('bet_type', 'WIN').upper()
            if bet_type == 'WIN':
                total_return += stake * odds
            else:  # EW
                ew_fraction = float(p.get('ew_fraction', 0.2))
                total_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
        elif outcome == 'PLACED':
            stake = float(p.get('stake', 2.0))
            odds = _settlement_odds(p)
            ew_fraction = float(p.get('ew_fraction', 0.2))
            total_return += (stake/2) * (1 + (odds-1) * ew_fraction)
    
    profit = total_return - total_stake
    roi = (profit / total_stake * 100) if total_stake > 0 else 0
    
    # Separate picks by sport
    horse_picks = [p for p in picks_with_results if p.get('sport') == 'horses']
    greyhound_picks = [p for p in picks_with_results if p.get('sport') == 'greyhounds']
    
    # Calculate sport-specific summaries
    def calculate_sport_summary(sport_picks):
        if not sport_picks:
            return None
        
        sport_wins = sum(1 for p in sport_picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON'])
        sport_places = sum(1 for p in sport_picks if str(p.get('outcome', '')).upper() == 'PLACED')
        sport_losses = sum(1 for p in sport_picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST'])
        sport_pending = sum(1 for p in sport_picks if str(p.get('outcome', '')).upper() in ['PENDING', ''] or p.get('outcome') is None)
        
        # EXCLUDE PENDING from stake/return calculations - only count resolved bets
        sport_resolved = [p for p in sport_picks if str(p.get('outcome', '')).upper() not in ['PENDING', ''] and p.get('outcome') is not None]
        sport_stake = sum(float(p.get('stake', 2.0)) for p in sport_resolved)
        
        # Calculate returns for this sport (only resolved bets)
        sport_return = 0
        for p in sport_resolved:
            outcome = str(p.get('outcome', '')).upper()
            if outcome in ['WIN', 'WON']:
                stake = float(p.get('stake', 2.0))
                odds = _settlement_odds(p)
                bet_type = p.get('bet_type', 'WIN').upper()
                if bet_type == 'WIN':
                    sport_return += stake * odds
                else:  # EW
                    ew_fraction = float(p.get('ew_fraction', 0.2))
                    sport_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
            elif outcome == 'PLACED':
                stake = float(p.get('stake', 2.0))
                odds = _settlement_odds(p)
                ew_fraction = float(p.get('ew_fraction', 0.2))
                sport_return += (stake/2) * (1 + (odds-1) * ew_fraction)
        
        sport_profit = sport_return - sport_stake
        sport_roi = (sport_profit / sport_stake * 100) if sport_stake > 0 else 0
        
        return {
            'total_picks': len(sport_picks),
            'wins': sport_wins,
            'places': sport_places,
            'losses': sport_losses,
            'pending': sport_pending,
            'total_stake': round(sport_stake, 2),
            'total_return': round(sport_return, 2),
            'profit': round(sport_profit, 2),
            'roi': round(sport_roi, 1),
            'strike_rate': round((sport_wins / (sport_wins + sport_losses) * 100) if (sport_wins + sport_losses) > 0 else 0, 1)
        }
    
    summary = {
        'total_picks': len(picks),
        'wins': wins,
        'places': places,
        'losses': losses,
        'pending': pending,
        'total_stake': round(total_stake, 2),
        'total_return': round(total_return, 2),
        'profit': round(profit, 2),
        'roi': round(roi, 1),
        'strike_rate': round((wins / (wins + losses) * 100) if (wins + losses) > 0 else 0, 1)
    }
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'date': today,
            'summary': summary,
            'horses': {
                'summary': calculate_sport_summary(horse_picks),
                'picks': horse_picks
            },
            'greyhounds': {
                'summary': calculate_sport_summary(greyhound_picks),
                'picks': greyhound_picks
            },
            'picks': picks_with_results,
            'debug_timestamp': datetime.now().isoformat()
        })
    }

def get_cheltenham_picks_lambda(headers, event):
    """Return today's Cheltenham picks from CheltenhamPicks DynamoDB table."""
    from boto3.dynamodb.conditions import Attr
    from datetime import timedelta

    db_chelt = dynamodb.Table('CheltenhamPicks')
    qp = event.get('queryStringParameters') or {}
    target_date = qp.get('date', datetime.now().strftime('%Y-%m-%d'))

    # Collect items across a 5-day lookback window so that older full-field
    # saves (e.g. with 12 all_horses) are not dropped in favour of newer
    # lighter refreshes that only stored 6.
    base = datetime.strptime(target_date, '%Y-%m-%d')
    date_window = [(base - timedelta(days=n)).strftime('%Y-%m-%d') for n in range(5)]

    def scan_date(dt):
        resp = db_chelt.scan(
            FilterExpression=Attr('pick_date').eq(dt)
        )
        return [decimal_to_float(item) for item in resp.get('Items', [])]

    # Flat list of all items across the window (newest dates first so the
    # (day, race_time) dedup below prefers today's horse/score fields while
    # also picking up full all_horses lists from older saves).
    all_items_by_date: dict = {}   # race_name → best item (most all_horses wins)
    for dt in date_window:   # newest first — dt=today, yesterday, …
        for item in scan_date(dt):
            rn = item.get('race_name', '')
            existing = all_items_by_date.get(rn)
            # Keep today's fields by default, but upgrade all_horses if an
            # older date has a fuller field list.
            if existing is None:
                all_items_by_date[rn] = item
            elif len(item.get('all_horses', [])) > len(existing.get('all_horses', [])):
                # Preserve today's scalar fields; only replace all_horses from older richer item
                merged_item = dict(existing)
                merged_item['all_horses'] = item['all_horses']
                # Fix is_surebet_pick flags — old all_horses may mark a stale pick as PICK
                # (e.g. Day 1 save had Horse A as pick; today's save has Horse B; old all_horses
                # still has Horse A flagged is_surebet_pick=True, causing wrong PICK badge in UI)
                current_horse = merged_item.get('horse', '')
                if current_horse:
                    for h in merged_item['all_horses']:
                        h['is_surebet_pick'] = (h.get('name', '') == current_horse)
                all_items_by_date[rn] = merged_item
    all_picks = list(all_items_by_date.values())

    # Deduplicate by (day, race_time) — keep the record with the most all_horses
    # Prevents duplicate panels when race was saved under two different name variants
    seen_slots: dict = {}
    for item in all_picks:
        slot = (item.get('day', ''), item.get('race_time', ''))
        existing = seen_slots.get(slot)
        if not existing or len(item.get('all_horses', [])) > len(existing.get('all_horses', [])):
            seen_slots[slot] = item
    all_picks = list(seen_slots.values())

    DAY_ORDER = ['Tuesday_10_March', 'Wednesday_11_March', 'Thursday_12_March', 'Friday_13_March']
    days = {}
    for item in all_picks:
        day = item.get('day', 'Unknown')
        if day not in days:
            days[day] = []
        days[day].append({
            'race_name':        item.get('race_name', ''),
            'day':              item.get('day', ''),
            'race_time':        item.get('race_time', ''),
            'grade':            item.get('grade', ''),
            'distance':         item.get('distance', ''),
            'horse':            item.get('horse', ''),
            'trainer':          item.get('trainer', ''),
            'jockey':           item.get('jockey', ''),
            'odds':             item.get('odds', ''),
            'score':            item.get('score', 0),
            'tier':             item.get('tier', ''),
            'value_rating':     item.get('value_rating', 0),
            'second_score':     item.get('second_score', 0),
            'score_gap':        item.get('score_gap', 0),
            'confidence':       item.get('confidence', ''),
            # ── Strategy fields ──────────────────────────────────────────────
            'is_grade1':        item.get('is_grade1', False),
            'is_skip_race':     item.get('is_skip_race', False),
            'bet_tier':         item.get('bet_tier', 'OPINION_ONLY'),
            'bet_recommendation': item.get('bet_recommendation', False),
            # ─────────────────────────────────────────────────────────────────
            'reasons':          item.get('reasons', []),
            'warnings':         item.get('warnings', []),
            'pick_changed':     item.get('pick_changed', False),
            'previous_horse':   item.get('previous_horse', ''),
            'previous_odds':    item.get('previous_odds', ''),
            'change_reason':    item.get('change_reason', ''),
            'pick_date':        item.get('pick_date', target_date),
            'all_horses':       item.get('all_horses', []),
        })

    ordered = {d: days[d] for d in DAY_ORDER if d in days}
    for d in days:
        if d not in ordered:
            ordered[d] = days[d]

    total_changes = sum(1 for p in all_picks if p.get('pick_changed'))
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success':       True,
            'pick_date':     target_date,
            'days':          ordered,
            'total_picks':   len(all_picks),
            'total_changes': total_changes,
        })
    }


def get_cheltenham_races_lambda(headers):
    """
    Return Cheltenham race structure derived from CheltenhamPicks DynamoDB table.
    Grouped by day with race metadata (name, time, grade, horses count).
    """
    from boto3.dynamodb.conditions import Attr
    today = datetime.now().strftime('%Y-%m-%d')
    db_chelt = dynamodb.Table('CheltenhamPicks')
    resp = db_chelt.scan(FilterExpression=Attr('pick_date').eq(today))
    raw_items = [decimal_to_float(i) for i in resp.get('Items', [])]

    # Deduplicate by (day, race_time) — keep item with the most all_horses
    seen_slots: dict = {}
    for item in raw_items:
        slot = (item.get('day', ''), item.get('race_time', ''))
        existing = seen_slots.get(slot)
        if not existing or len(item.get('all_horses', [])) > len(existing.get('all_horses', [])):
            seen_slots[slot] = item
    items = list(seen_slots.values())

    DAY_ORDER = ['Tuesday_10_March', 'Wednesday_11_March', 'Thursday_12_March', 'Friday_13_March']
    days = {}
    for idx, item in enumerate(items):
        day = item.get('day', 'Unknown')
        if day not in days:
            days[day] = []
        days[day].append({
            'raceId':       f"{day}_{idx}",
            'raceName':     item.get('race_name', ''),
            'raceTime':     item.get('race_time', ''),
            'raceGrade':    item.get('grade', ''),
            'raceDistance': item.get('distance', ''),
            'festivalDay':  day,
            'totalHorses':  len(item.get('all_horses', [])),
        })

    ordered = {d: sorted(days.get(d, []), key=lambda x: x.get('raceTime', '')) for d in DAY_ORDER}
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'success': True, 'races': ordered, 'totalRaces': len(items)})
    }


def save_cheltenham_picks_lambda(headers):
    """
    Run cheltenham picks save inline (imports and calls save_picks directly).
    Falls back to async Lambda invoke if import fails.
    """
    try:
        import sys
        sys.path.insert(0, '/var/task')
        from save_cheltenham_picks import save_picks
        picks, changes = save_picks(dry_run=False)
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': f'Saved {len(picks)} picks. {len(changes)} changed.',
                'picks_count': len(picks),
                'changes_count': len(changes),
            })
        }
    except ImportError:
        # Fall back to async Lambda invoke if module not found
        import boto3 as _boto3
        try:
            lc = _boto3.client('lambda', region_name='eu-west-1')
            lc.invoke(
                FunctionName='cheltenham-picks-save',
                InvocationType='Event',
                Payload=json.dumps({'source': 'api-trigger'})
            )
            return {
                'statusCode': 202,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'message': 'Save triggered — picks will update in ~60s. Refresh to see changes.',
                })
            }
        except Exception as e2:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': f'Could not trigger pick save: {e2}',
                    'message': 'Run: python save_cheltenham_picks.py locally to refresh picks.',
                })
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': f'Pick save failed: {e}',
            })
        }


def trigger_workflow(headers):
    """Trigger the betting workflow Lambda to generate new picks"""
    import boto3 as _boto3

    lambda_client = _boto3.client('lambda', region_name='eu-west-1')

    try:
        # Invoke the workflow Lambda asynchronously
        response = lambda_client.invoke(
            FunctionName='betting-workflow',
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({
                'source': 'api-trigger',
                'trigger': 'manual-refresh'
            })
        )
        
        return {
            'statusCode': 202,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Workflow triggered successfully',
                'status': 'processing',
                'info': 'New picks will be generated in ~60-90 seconds. Refresh picks to see updates.'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to trigger workflow. Make sure betting-workflow Lambda exists and API has invoke permissions.'
            })
        }


def register_subscriber(headers, event):
    """Register a new subscriber. POST /api/register"""
    try:
        body = event.get('body') or '{}'
        if isinstance(body, str):
            data = json.loads(body)
        else:
            data = body

        full_name = (data.get('full_name') or '').strip()
        email     = (data.get('email') or '').strip().lower()
        address   = (data.get('address') or '').strip()
        age       = data.get('age')
        username  = (data.get('username') or '').strip().lower()
        password  = data.get('password') or ''

        if not full_name or len(full_name) < 3:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Full name is required.'})}

        email_re = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
        if not email_re.match(email):
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'A valid email address is required (e.g. jane@example.com).'})}
        if '..' in email:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Email address contains invalid consecutive dots.'})}
        email_domain = email.split('@')[1] if '@' in email else ''
        email_local  = email.split('@')[0] if '@' in email else ''
        if len(email_domain.split('.')[-1]) < 2:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Email domain extension looks invalid.'})}
        if re.match(r'^(test|asdf|qwerty|aaaaa|zzzzz|abcde|12345|noreply|fake|spam|none|null|xxx)', email_local):
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Please use a real email address.'})}
        _fake_domains = {'test.com','fake.com','example.com','mailinator.com','guerrillamail.com',
                         'throwam.com','trashmail.com','yopmail.com','sharklasers.com'}
        if email_domain in _fake_domains:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Disposable or test email addresses are not accepted.'})}

        if len(address) < 10:
            pass  # Address is optional — no longer required for registration
        addr_words = [w for w in address.split() if len(w) > 1]
        if len(addr_words) < 3:
            pass  # Address is optional
        addr_clean = address.replace(' ', '')
        if addr_clean:
            pass  # Address is optional
        if re.match(r'^(asdf|qwerty|zxcv|abcd|1234|test|fake|none|null|xxx)', address, re.IGNORECASE):
            pass  # Address is optional
        try:
            age = int(age)
            if age < 18 or age > 120:
                raise ValueError
        except (TypeError, ValueError):
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'You must be 18 or over to register.'})}
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Username must be 3-30 characters (letters, numbers, underscores).'})}
        if len(password) < 8:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Password must be at least 8 characters.'})}

        # Check email uniqueness
        if subscribers_table.get_item(Key={'email': email}).get('Item'):
            return {'statusCode': 409, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'An account with this email already exists.'})}
        # Check username uniqueness
        if subscribers_table.get_item(Key={'email': f'u#{username}'}).get('Item'):
            return {'statusCode': 409, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'That username is already taken.'})}

        pw_hash   = _hash_password(password)
        joined_at = datetime.utcnow().isoformat() + 'Z'
        subscribers_table.put_item(Item={
            'email': email, 'full_name': full_name, 'address': address,
            'age': Decimal(str(age)), 'username': username,
            'password_hash': pw_hash, 'joined_at': joined_at, 'active': True,
        })
        subscribers_table.put_item(Item={
            'email': f'u#{username}', 'username': username,
            'ref_email': email, 'joined_at': joined_at,
        })

        # Mark verified immediately; attempt to send welcome email (non-blocking)
        subscribers_table.update_item(
            Key={'email': email},
            UpdateExpression='SET email_verified = :v',
            ExpressionAttributeValues={':v': True},
        )
        try:
            token = secrets.token_urlsafe(32)
            _send_verification_email(email, full_name, token)
        except Exception as mail_err:
            print(f'Welcome email failed (non-fatal): {mail_err}')

        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'success': True, 'message': 'Registration successful. Welcome to BetBudAI!'})}
    except Exception as e:
        print(f'register_subscriber error: {e}')
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Registration failed. Please try again.'})}


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a PBKDF2 hash created by _hash_password()."""
    try:
        raw        = base64.b64decode(stored.encode('utf-8'))
        salt       = raw[:32]
        stored_key = raw[32:]
        key        = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
        return key == stored_key
    except Exception:
        return False


def _send_verification_email(email: str, full_name: str, token: str):
    """Send an account verification email via SES."""
    verify_url = f'{SITE_URL}/?verify={token}'
    first_name = full_name.split()[0] if full_name else 'there'
    html = f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#0f172a;color:white;padding:40px;">
<div style="max-width:560px;margin:0 auto;background:#1e293b;border-radius:16px;padding:40px;">
  <h1 style="color:#34d399;margin:0 0 8px;">BetBudAI</h1>
  <p style="color:rgba(255,255,255,0.5);margin:0 0 32px;font-size:13px;">AI-powered horse racing picks</p>
  <h2 style="color:white;font-size:22px;margin:0 0 16px;">Hi {first_name}, verify your email</h2>
  <p style="color:rgba(255,255,255,0.7);line-height:1.6;">Thanks for registering with BetBudAI. Click the button below to verify your email address and activate your account.</p>
  <a href="{verify_url}" style="display:inline-block;margin:24px 0;padding:14px 32px;background:linear-gradient(135deg,#059669,#047857);color:white;text-decoration:none;border-radius:10px;font-weight:700;font-size:16px;">✓ Verify My Email</a>
  <p style="color:rgba(255,255,255,0.4);font-size:12px;">This link expires in 24 hours. If you didn't create an account, you can ignore this email.</p>
  <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:24px 0;"/>
  <p style="color:rgba(255,255,255,0.3);font-size:11px;">BetBudAI &middot; <a href="{SITE_URL}" style="color:#34d399;">{SITE_URL}</a></p>
</div></body></html>"""
    ses_client.send_email(
        Source=f'BetBudAI <{SENDER_EMAIL}>',
        Destination={'ToAddresses': [email]},
        Message={
            'Subject': {'Data': 'Verify your BetBudAI account', 'Charset': 'UTF-8'},
            'Body': {
                'Html': {'Data': html, 'Charset': 'UTF-8'},
                'Text': {'Data': f'Hi {first_name},\n\nVerify your BetBudAI account by visiting:\n{verify_url}\n\nThis link expires in 24 hours.', 'Charset': 'UTF-8'},
            },
        },
    )


def verify_email_token(headers, event):
    """GET /api/verify-email?token=xxx — mark account as verified."""
    try:
        qs = event.get('queryStringParameters') or {}
        token = (qs.get('token') or '').strip()
        if not token:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Verification token is missing.'})}

        # Look up token reservation
        reservation = subscribers_table.get_item(Key={'email': f'vt#{token}'}).get('Item')
        if not reservation:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Invalid or expired verification link. Please register again or contact support.'})}

        # Check expiry
        expires_at = reservation.get('expires_at', '')
        if expires_at and datetime.utcnow().isoformat() + 'Z' > expires_at:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Verification link has expired. Please register again.'})}

        ref_email = reservation['ref_email']

        # Mark account verified
        subscribers_table.update_item(
            Key={'email': ref_email},
            UpdateExpression='SET email_verified = :v REMOVE verify_token, token_expires',
            ExpressionAttributeValues={':v': True},
        )
        # Delete token reservation
        subscribers_table.delete_item(Key={'email': f'vt#{token}'})

        # Return user info so frontend can log them in immediately
        item = subscribers_table.get_item(Key={'email': ref_email}).get('Item', {})
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({
            'success': True,
            'message': 'Email verified! Welcome to BetBudAI.',
            'user': {'email': ref_email, 'username': item.get('username', ''), 'full_name': item.get('full_name', '')},
        })}
    except Exception as e:
        print(f'verify_email_token error: {e}')
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Verification failed. Please try again.'})}


# ═══════════════════════════════════════════════════════════════════════════════
# STRIPE PAYMENT HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

def create_checkout_session(headers, event):
    """Create a Stripe Checkout session for Premium (€19.99/mo) or VIP (€99/mo).
    POST /api/create-checkout-session  { "email": "...", "tier": "premium"|"vip" }
    """
    try:
        if not stripe or 'NOT_CONFIGURED' in (os.environ.get('STRIPE_SECRET_KEY') or ''):
            return {'statusCode': 503, 'headers': headers,
                    'body': json.dumps({'error': 'Payments coming soon! Stripe is not yet configured.'})}

        body = json.loads(event.get('body') or '{}')
        email = (body.get('email') or '').strip().lower()
        tier  = (body.get('tier') or '').strip().lower()

        if not email or tier not in ('premium', 'vip'):
            return {'statusCode': 400, 'headers': headers,
                    'body': json.dumps({'error': 'email and tier (premium/vip) required'})}

        # Look up subscriber
        sub = subscribers_table.get_item(Key={'email': email}).get('Item')
        if not sub:
            return {'statusCode': 404, 'headers': headers,
                    'body': json.dumps({'error': 'User not found'})}

        price_id = STRIPE_PRICE_PREMIUM if tier == 'premium' else STRIPE_PRICE_VIP

        # Reuse or create Stripe customer
        stripe_customer_id = sub.get('stripe_customer_id')
        if not stripe_customer_id:
            customer = stripe.Customer.create(
                email=email,
                name=sub.get('full_name', ''),
                metadata={'betbudai_email': email}
            )
            stripe_customer_id = customer.id
            subscribers_table.update_item(
                Key={'email': email},
                UpdateExpression='SET stripe_customer_id = :cid',
                ExpressionAttributeValues={':cid': stripe_customer_id}
            )

        # Create Checkout Session
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=f'{SITE_URL}?payment=success&tier={tier}',
            cancel_url=f'{SITE_URL}?payment=cancelled',
            metadata={'betbudai_email': email, 'tier': tier},
            subscription_data={'metadata': {'betbudai_email': email, 'tier': tier}},
        )

        return {'statusCode': 200, 'headers': headers,
                'body': json.dumps({'url': session.url, 'session_id': session.id})}

    except stripe.error.StripeError as e:
        print(f'Stripe error in create_checkout_session: {e}')
        return {'statusCode': 500, 'headers': headers,
                'body': json.dumps({'error': str(e)})}
    except Exception as e:
        print(f'create_checkout_session error: {e}')
        import traceback; traceback.print_exc()
        return {'statusCode': 500, 'headers': headers,
                'body': json.dumps({'error': 'Failed to create checkout session'})}


def handle_stripe_webhook(headers, event):
    """Handle Stripe webhook events — subscription lifecycle.
    POST /api/stripe-webhook
    """
    try:
        payload = event.get('body', '')
        sig_header = (event.get('headers') or {}).get('Stripe-Signature') or \
                     (event.get('headers') or {}).get('stripe-signature', '')

        # Verify webhook signature
        try:
            webhook_event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return {'statusCode': 400, 'headers': headers, 'body': 'Invalid payload'}
        except stripe.error.SignatureVerificationError:
            return {'statusCode': 400, 'headers': headers, 'body': 'Invalid signature'}

        event_type = webhook_event['type']
        data = webhook_event['data']['object']
        print(f'Stripe webhook: {event_type}')

        if event_type == 'checkout.session.completed':
            _handle_checkout_completed(data)

        elif event_type in ('customer.subscription.updated', 'customer.subscription.created'):
            _handle_subscription_updated(data)

        elif event_type == 'customer.subscription.deleted':
            _handle_subscription_deleted(data)

        elif event_type == 'invoice.payment_failed':
            _handle_payment_failed(data)

        return {'statusCode': 200, 'headers': headers,
                'body': json.dumps({'received': True})}

    except Exception as e:
        print(f'stripe webhook error: {e}')
        import traceback; traceback.print_exc()
        return {'statusCode': 500, 'headers': headers,
                'body': json.dumps({'error': str(e)})}


def _find_email_from_stripe(data):
    """Extract betbudai_email from Stripe object metadata or customer."""
    email = (data.get('metadata') or {}).get('betbudai_email')
    if email:
        return email
    # Fallback: look up customer
    customer_id = data.get('customer')
    if customer_id:
        from boto3.dynamodb.conditions import Attr
        resp = subscribers_table.scan(
            FilterExpression=Attr('stripe_customer_id').eq(customer_id),
            ProjectionExpression='email'
        )
        if resp.get('Items'):
            return resp['Items'][0]['email']
    return None


def _handle_checkout_completed(session):
    """After successful Checkout, activate subscription."""
    email = (session.get('metadata') or {}).get('betbudai_email')
    tier  = (session.get('metadata') or {}).get('tier', 'premium')
    subscription_id = session.get('subscription')

    if not email:
        print('checkout.session.completed: no betbudai_email in metadata')
        return

    update_expr = 'SET subscription_tier = :tier, subscription_status = :status'
    expr_vals = {':tier': tier, ':status': 'active'}

    if subscription_id:
        update_expr += ', stripe_subscription_id = :sid'
        expr_vals[':sid'] = subscription_id

    subscribers_table.update_item(
        Key={'email': email},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_vals
    )
    print(f'Activated {tier} for {email}')


def _handle_subscription_updated(subscription):
    """Handle subscription status changes (renewals, payment method updates, etc.)."""
    email = _find_email_from_stripe(subscription)
    if not email:
        print(f'subscription.updated: cannot find user for sub {subscription["id"]}')
        return

    status = subscription.get('status', 'active')
    tier = (subscription.get('metadata') or {}).get('tier', 'premium')

    subscribers_table.update_item(
        Key={'email': email},
        UpdateExpression='SET subscription_status = :s, subscription_tier = :t, stripe_subscription_id = :sid, subscription_current_period_end = :end',
        ExpressionAttributeValues={
            ':s': status,
            ':t': tier,
            ':sid': subscription['id'],
            ':end': subscription.get('current_period_end', 0),
        }
    )
    print(f'Subscription updated: {email} → {tier}/{status}')


def _handle_subscription_deleted(subscription):
    """Handle subscription cancellation — downgrade to free."""
    email = _find_email_from_stripe(subscription)
    if not email:
        print(f'subscription.deleted: cannot find user for sub {subscription["id"]}')
        return

    subscribers_table.update_item(
        Key={'email': email},
        UpdateExpression='SET subscription_tier = :t, subscription_status = :s',
        ExpressionAttributeValues={':t': 'free', ':s': 'canceled'}
    )
    print(f'Subscription canceled: {email} → free')


def _handle_payment_failed(invoice):
    """Mark subscription as past_due on payment failure."""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    # Find user by subscription ID
    from boto3.dynamodb.conditions import Attr
    resp = subscribers_table.scan(
        FilterExpression=Attr('stripe_subscription_id').eq(subscription_id),
        ProjectionExpression='email'
    )
    if resp.get('Items'):
        email = resp['Items'][0]['email']
        subscribers_table.update_item(
            Key={'email': email},
            UpdateExpression='SET subscription_status = :s',
            ExpressionAttributeValues={':s': 'past_due'}
        )
        print(f'Payment failed: {email} → past_due')


def get_subscription_status(headers, event):
    """Get current subscription status for a user.
    POST /api/subscription-status  { "email": "..." }
    """
    try:
        body = json.loads(event.get('body') or '{}')
        email = (body.get('email') or '').strip().lower()
        if not email:
            return {'statusCode': 400, 'headers': headers,
                    'body': json.dumps({'error': 'email required'})}

        sub = subscribers_table.get_item(Key={'email': email}).get('Item')
        if not sub:
            return {'statusCode': 404, 'headers': headers,
                    'body': json.dumps({'error': 'User not found'})}

        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({
            'subscription_tier': sub.get('subscription_tier', 'free'),
            'subscription_status': sub.get('subscription_status', ''),
            'subscription_current_period_end': int(sub.get('subscription_current_period_end', 0)),
        })}
    except Exception as e:
        print(f'get_subscription_status error: {e}')
        return {'statusCode': 500, 'headers': headers,
                'body': json.dumps({'error': 'Failed to get subscription status'})}


def create_customer_portal(headers, event):
    """Create a Stripe Customer Portal session for managing subscription.
    POST /api/customer-portal  { "email": "..." }
    """
    try:
        if not stripe or 'NOT_CONFIGURED' in (os.environ.get('STRIPE_SECRET_KEY') or ''):
            return {'statusCode': 503, 'headers': headers,
                    'body': json.dumps({'error': 'Payments coming soon! Stripe is not yet configured.'})}

        body = json.loads(event.get('body') or '{}')
        email = (body.get('email') or '').strip().lower()
        if not email:
            return {'statusCode': 400, 'headers': headers,
                    'body': json.dumps({'error': 'email required'})}

        sub = subscribers_table.get_item(Key={'email': email}).get('Item')
        if not sub or not sub.get('stripe_customer_id'):
            return {'statusCode': 404, 'headers': headers,
                    'body': json.dumps({'error': 'No active subscription found'})}

        session = stripe.billing_portal.Session.create(
            customer=sub['stripe_customer_id'],
            return_url=SITE_URL,
        )
        return {'statusCode': 200, 'headers': headers,
                'body': json.dumps({'url': session.url})}
    except Exception as e:
        print(f'create_customer_portal error: {e}')
        return {'statusCode': 500, 'headers': headers,
                'body': json.dumps({'error': 'Failed to create portal session'})}


def cancel_subscription(headers, event):
    """Cancel a subscription (at period end).
    POST /api/cancel-subscription  { "email": "..." }
    """
    try:
        body = json.loads(event.get('body') or '{}')
        email = (body.get('email') or '').strip().lower()
        if not email:
            return {'statusCode': 400, 'headers': headers,
                    'body': json.dumps({'error': 'email required'})}

        sub = subscribers_table.get_item(Key={'email': email}).get('Item')
        if not sub or not sub.get('stripe_subscription_id'):
            return {'statusCode': 404, 'headers': headers,
                    'body': json.dumps({'error': 'No active subscription found'})}

        # Cancel at end of billing period (not immediately)
        stripe.Subscription.modify(
            sub['stripe_subscription_id'],
            cancel_at_period_end=True
        )

        subscribers_table.update_item(
            Key={'email': email},
            UpdateExpression='SET subscription_status = :s',
            ExpressionAttributeValues={':s': 'canceling'}
        )

        return {'statusCode': 200, 'headers': headers,
                'body': json.dumps({'success': True, 'message': 'Subscription will cancel at end of billing period'})}
    except Exception as e:
        print(f'cancel_subscription error: {e}')
        return {'statusCode': 500, 'headers': headers,
                'body': json.dumps({'error': 'Failed to cancel subscription'})}


def login_subscriber(headers, event):
    """Authenticate a subscriber. Accepts email or username + password."""
    try:
        body = json.loads(event.get('body') or '{}')
        identifier = (body.get('email') or '').strip().lower()
        password   = body.get('password') or ''

        if not identifier or not password:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Email/username and password are required.'})}

        # Resolve username → email if no '@'
        if '@' not in identifier:
            reservation = subscribers_table.get_item(Key={'email': f'u#{identifier}'}).get('Item')
            if not reservation:
                return {'statusCode': 401, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Invalid email/username or password.'})}
            identifier = reservation['ref_email']

        item = subscribers_table.get_item(Key={'email': identifier}).get('Item')
        if not item or not _verify_password(password, item.get('password_hash', '')):
            return {'statusCode': 401, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Invalid email/username or password.'})}

        # Track login activity
        try:
            source_ip = (event.get('requestContext', {}).get('identity', {}).get('sourceIp')
                         or event.get('headers', {}).get('X-Forwarded-For', '').split(',')[0].strip()
                         or 'unknown')
            subscribers_table.update_item(
                Key={'email': identifier},
                UpdateExpression='SET last_login = :now, last_ip = :ip ADD login_count :one',
                ExpressionAttributeValues={
                    ':now': datetime.utcnow().isoformat() + 'Z',
                    ':ip':  source_ip,
                    ':one': 1,
                }
            )
        except Exception as track_err:
            print(f'login tracking error: {track_err}')

        role = item.get('role', 'free')
        subscription_tier = item.get('subscription_tier', 'free')
        # If user has an active paid subscription, reflect that in role
        if subscription_tier in ('premium', 'vip') and item.get('subscription_status') == 'active':
            role = subscription_tier
        user_payload = {
            'email':     identifier,
            'username':  item.get('username', ''),
            'full_name': item.get('full_name', ''),
            'role':      role,
            'subscription_tier': subscription_tier,
            'subscription_status': item.get('subscription_status', ''),
        }

        # Generate admin session token if user is admin
        admin_token = None
        if role == 'admin':
            admin_token = secrets.token_hex(32)
            # Store session (24h TTL)
            expires = (datetime.utcnow() + timedelta(hours=24)).isoformat() + 'Z'
            subscribers_table.put_item(Item={
                'email':      f'__session__{admin_token}',
                'user_email': identifier,
                'expires_at': expires,
                'created_at': datetime.utcnow().isoformat() + 'Z',
            })
            user_payload['admin_token'] = admin_token

        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({
            'success': True,
            'user': user_payload,
        })}
    except Exception as e:
        print(f'login_subscriber error: {e}')
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Login failed. Please try again.'})}


def auto_record_pending_results(headers):
    """
    Fetch Betfair results for any pending picks whose race finished >30 min ago.
    Triggered by EventBridge every 15 minutes, or manually via /api/results/auto-record.
    """
    now_utc = datetime.utcnow()
    today     = now_utc.strftime('%Y-%m-%d')
    yesterday = (now_utc - timedelta(days=1)).strftime('%Y-%m-%d')

    # ── 1. Scan DynamoDB for pending picks (today + yesterday) ────────────────
    from boto3.dynamodb.conditions import Attr
    pending = []
    for date in [today, yesterday]:
        resp = table.scan(
            FilterExpression=Attr('bet_date').eq(date) & Attr('outcome').eq('pending') & Attr('show_in_ui').eq(True)
        )
        pending.extend(decimal_to_float(item) for item in resp.get('Items', []))

    # Keep only races that finished >30 minutes ago and have a market_id
    to_check = []
    for pick in pending:
        rt_str    = pick.get('race_time', '')
        market_id = str(pick.get('market_id', '')).strip()
        if not market_id or not rt_str:
            continue
        try:
            rt = datetime.fromisoformat(rt_str.replace('Z', '+00:00')).replace(tzinfo=None)
            if rt + timedelta(minutes=30) < now_utc:
                to_check.append(pick)
        except Exception:
            continue

    if not to_check:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True, 'message': 'No pending results ready to check', 'checked': 0})
        }

    print(f'auto_record: checking {len(to_check)} pending picks')

    # ── 2. Authenticate to Betfair ────────────────────────────────────────────
    sm = boto3.client('secretsmanager', region_name='eu-west-1')
    creds = json.loads(sm.get_secret_value(SecretId='betfair-credentials')['SecretString'])
    app_key = creds['app_key']
    BF_BASE = 'https://api.betfair.com/exchange/betting/rest/v1.0'

    session_token = None
    try:
        login_data = urllib.parse.urlencode(
            {'username': creds['username'], 'password': creds['password']}
        ).encode('utf-8')
        login_req = urllib.request.Request(
            'https://identitysso.betfair.com/api/login',
            data=login_data,
            headers={'X-Application': app_key, 'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        with urllib.request.urlopen(login_req, timeout=10) as r:
            result = json.loads(r.read())
            session_token = result.get('sessionToken') or result.get('token')
    except Exception as e:
        print(f'Betfair login error: {e}')
        session_token = creds.get('session_token', '')

    if not session_token:
        return {
            'statusCode': 500, 'headers': headers,
            'body': json.dumps({'success': False, 'error': 'Could not authenticate to Betfair'})
        }

    bf_hdrs = {
        'X-Application':  app_key,
        'X-Authentication': session_token,
        'Content-Type':   'application/json',
        'Accept':         'application/json',
    }

    def bf_post(endpoint, payload):
        data = json.dumps(payload).encode('utf-8')
        req  = urllib.request.Request(f'{BF_BASE}/{endpoint}/', data=data, headers=bf_hdrs, method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    # ── 3. Group picks by market_id ───────────────────────────────────────────
    by_market = {}
    for pick in to_check:
        mid = str(pick['market_id']).strip()
        by_market.setdefault(mid, []).append(pick)

    updated = 0
    errors  = []
    results_summary = []

    for market_id, picks in by_market.items():
        try:
            # ── listMarketBook: statuses + SP ─────────────────────────────
            book_resp = bf_post('listMarketBook', {
                'marketIds': [market_id],
                'priceProjection': {'priceData': ['SP_TRADED']},
                'orderProjection': 'EXECUTABLE',
                'matchProjection': 'NO_ROLLUP',
            })
            if not book_resp:
                errors.append(f'{market_id}: empty book response')
                continue

            market_book  = book_resp[0] if isinstance(book_resp, list) else book_resp
            market_status = market_book.get('status', '')
            runners_book  = market_book.get('runners', [])

            # If market not CLOSED yet, skip — check again next cycle
            if market_status not in ('CLOSED',):
                print(f'{market_id}: status={market_status} – not settled yet, will retry')
                continue

            # ── listMarketCatalogue: horse names by selectionId ───────────────
            runner_names = {}
            try:
                cat_resp = bf_post('listMarketCatalogue', {
                    'filter': {'marketIds': [market_id]},
                    'marketProjection': ['RUNNER_DESCRIPTION'],
                })
                cat_market = (cat_resp[0] if isinstance(cat_resp, list) else cat_resp) or {}
                for r in cat_market.get('runners', []):
                    runner_names[str(r.get('selectionId'))] = r.get('runnerName', '')
            except Exception as ce:
                print(f'Catalogue fetch failed for {market_id}: {ce}')

            # Build lookup dicts from book
            sort_by_sel   = {str(r.get('selectionId')): r.get('sortPriority', 99) for r in runners_book}
            status_by_sel = {str(r.get('selectionId')): r.get('status', '')      for r in runners_book}
            # SP lookup: prefer sp.actualSP, fall back to lastPriceTraded
            sp_by_sel = {}
            for r in runners_book:
                sp_data = r.get('sp', {})
                sp_val  = (sp_data.get('actualSP') if sp_data else None) or r.get('lastPriceTraded')
                if sp_val:
                    sp_by_sel[str(r.get('selectionId'))] = float(sp_val)

            # Winner = runner with sortPriority==1 (or status==WINNER)
            winner_sel_id = None
            winner_name   = 'Unknown'
            for r in runners_book:
                if r.get('sortPriority') == 1 or r.get('status') == 'WINNER':
                    winner_sel_id = str(r.get('selectionId'))
                    winner_name   = runner_names.get(winner_sel_id, 'Unknown')
                    break

            # ── Update each pick in this market ───────────────────────────────
            for pick in picks:
                pick_sel   = str(pick.get('selection_id', '')).strip()
                sel_status = status_by_sel.get(pick_sel, '')
                finish     = int(sort_by_sel.get(pick_sel, 99))
                sp_odds    = sp_by_sel.get(pick_sel)  # None if not traded

                if sel_status == 'WINNER' or finish == 1:
                    outcome = 'win'
                elif finish in (2, 3):
                    outcome = 'placed'
                elif sel_status in ('LOSER', 'REMOVED') or finish > 3:
                    outcome = 'loss'
                else:
                    print(f"  {pick.get('horse')}: sel_id={pick_sel} not found in book (may have been a non-runner)")
                    continue

                # Calculate P&L using SP when available, else stored pick odds
                stake = float(pick.get('stake', 6.0))
                settlement_odds = sp_odds if sp_odds else float(pick.get('odds', 0))
                if outcome == 'win':
                    profit = round(stake * (settlement_odds - 1), 2)
                elif outcome == 'placed':
                    ef = float(pick.get('ew_fraction', 0.25) or 0.25)
                    profit = round((stake / 2) * (1 + (settlement_odds - 1) * ef) - stake, 2)
                else:
                    profit = round(-stake, 2)

                dynamo_table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
                update_expr = 'SET outcome = :o, finish_position = :f, winner_horse = :w, result_recorded_at = :t, profit = :p'
                expr_vals = {
                    ':o': outcome,
                    ':f': finish,
                    ':w': winner_name,
                    ':t': now_utc.isoformat() + 'Z',
                    ':p': Decimal(str(profit)),
                }
                if sp_odds:
                    update_expr += ', sp_odds = :sp'
                    expr_vals[':sp'] = Decimal(str(round(sp_odds, 2)))

                dynamo_table.update_item(
                    Key={'bet_id': pick['bet_id'], 'bet_date': pick['bet_date']},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_vals
                )
                updated += 1
                results_summary.append({
                    'horse':   pick.get('horse'),
                    'course':  pick.get('course'),
                    'outcome': outcome,
                    'finish':  finish,
                    'winner':  winner_name,
                    'sp_odds': sp_odds,
                    'profit':  profit,
                })
                sp_note = f" SP={sp_odds}" if sp_odds else " (no SP)"
                print(f"  Recorded: {pick.get('horse')} @ {pick.get('course')} → {outcome} pos={finish} profit={profit:+.2f}{sp_note}")

        except Exception as e:
            errors.append(f'{market_id}: {str(e)}')
            print(f'Error processing market {market_id}: {e}')

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success':  True,
            'checked':  len(to_check),
            'updated':  updated,
            'results':  results_summary,
            'errors':   errors,
        })
    }


# ── Lay the Favourite analysis ─────────────────────────────────────────────

def _dec(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, dict):
        return {k: _dec(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_dec(v) for v in o]
    return o


def _odds_dec(odds):
    if odds is None:
        return None
    try:
        return float(odds)
    except (TypeError, ValueError):
        pass
    try:
        s = str(odds).strip()
        if '/' in s:
            n, d = s.split('/')
            return float(n) / float(d) + 1.0
    except Exception:
        pass
    return None


_SCORE_WEIGHTS = {
    'class_up': 4, 'trip_new': 2, 'going_unproven': 2, 'draw_poor': 1,
    'layoff': 1, 'pace_doubt': 1, 'rivals_close': 2, 'drift': 1, 'short_price': 1,
    'trainer_track': 1, 'trainer_cold': 1, 'trainer_multiple': 1, 'current_form_no_wins': 1,
}


def _score_fav(fav, all_horses_sorted):
    sb = fav.get('score_breakdown') or {}
    flags = {}
    details = []
    fav_score = float(fav.get('comprehensive_score') or fav.get('score', 0))
    fav_odds = _odds_dec(fav.get('odds') or fav.get('decimal_odds'))

    if fav_odds is not None and fav_odds <= 2.25:
        flags['short_price'] = True
        details.append('Short price (5/4 or less)')

    rivals = [h for h in all_horses_sorted if h.get('horse') != fav.get('horse')]
    if rivals:
        r2 = float(rivals[0].get('score', 0)) if len(rivals) >= 1 else 0
        r3 = float(rivals[1].get('score', 0)) if len(rivals) >= 2 else 0
        if fav_score > 0 and (r2 / fav_score) >= 0.75:
            flags['rivals_close'] = True
            details.append(f'Rivals close: {rivals[0].get("horse","")} scored {r2:.0f} vs fav {fav_score:.0f}')
        elif fav_score > 0 and len(rivals) >= 2 and (r3 / fav_score) >= 0.70:
            flags['rivals_close'] = True
            details.append(f'3rd fav competitive at {r3:.0f}')

    going_pts = float(sb.get('going_suitability', 0))
    heavy_pts = float(sb.get('heavy_going_penalty', 0))
    if going_pts == 0 and heavy_pts == 0:
        flags['going_unproven'] = True
        details.append('Going suitability = 0')

    dist_pts = float(sb.get('distance_suitability', 0))
    cd_pts = float(sb.get('cd_bonus', 0))
    if dist_pts == 0 and cd_pts == 0:
        flags['trip_new'] = True
        details.append('Distance suitability = 0 & no CD bonus')

    or_pts = float(sb.get('official_rating_bonus', 0))
    db_pts = float(sb.get('database_history', 0))
    course_pts = float(sb.get('course_performance', 0))
    if or_pts > 0 and cd_pts == 0 and course_pts == 0 and db_pts == 0:
        flags['class_up'] = True
        details.append('No prior wins at course/class — stepping up')

    form_str = str(fav.get('form') or '')
    reasons_text = ' '.join(str(r) for r in (fav.get('selection_reasons') or fav.get('reasons') or []))
    if 'days off' in reasons_text.lower() or 'days since' in reasons_text.lower():
        flags['layoff'] = True
        details.append('Significant layoff flagged')
    elif '--' in form_str or form_str.count('-') >= 2:
        flags['layoff'] = True
        details.append(f'Form suggests layoff: {form_str}')

    draw = fav.get('draw')
    total_runners = float(fav.get('race_total_count') or fav.get('total_runners') or 0)
    if draw and total_runners > 0:
        draw_n = float(draw)
        if total_runners >= 10 and draw_n >= total_runners * 0.7:
            flags['draw_poor'] = True
            details.append(f'High draw ({draw_n:.0f}/{total_runners:.0f})')

    recent_win_pts = float(sb.get('recent_win', 0))
    if going_pts == 0 and recent_win_pts == 0:
        flags['pace_doubt'] = True
        details.append('No going suitability or recent win — pace uncertain')

    # --- Trainer at track win rate (+1) ---
    fav_trainer = str(fav.get('trainer') or '').strip()
    trainer_rep_pts = float(sb.get('trainer_reputation', 0))
    if fav_trainer and trainer_rep_pts == 0:
        flags['trainer_track'] = True
        details.append(f'Trainer ({fav_trainer}) — no tier status at this track')

    # --- Trainer cold last 14 days (+1) ---
    meeting_pts = float(sb.get('meeting_focus', 0))
    form_str = str(fav.get('form') or '')
    recent_form = form_str[-4:] if len(form_str) >= 4 else form_str
    recent_wins_in_form = sum(1 for c in recent_form if c == '1')
    if fav_trainer and meeting_pts == 0 and recent_wins_in_form == 0:
        flags['trainer_cold'] = True
        details.append(f'Trainer ({fav_trainer}) — no meeting focus & no win in recent form')

    # --- Trainer with multiple runners (+1) ---
    if fav_trainer and all_horses_sorted:
        multi_count = sum(
            1 for h in all_horses_sorted
            if (str(h.get('trainer') or '').strip().lower() == fav_trainer.lower()
                and (h.get('horse') or '') != (fav.get('horse') or ''))
        )
        if multi_count >= 1:
            flags['trainer_multiple'] = True
            details.append(f'Trainer ({fav_trainer}) has {multi_count + 1} runners in race')

    # --- Drift (+1) ---
    score_gap = float(fav.get('score_gap') or 0)
    if 0 < score_gap < 10:
        flags['drift'] = True
        details.append(f'Low score gap ({score_gap:.0f}) — field competitive, possible drift')
    elif score_gap == 0 and fav_score > 0:
        flags['drift'] = True
        details.append('Score gap = 0 — model does not separate the favourite clearly')

    # --- Current form – no wins (+1) ---
    form_digits = []
    for ch in str(form_str).replace('-', '').replace('/', ''):
        if ch.isdigit():
            form_digits.append(int(ch))
        elif ch.upper() in ('U', 'F', 'P', 'R'):
            form_digits.append(99)
    last_4 = form_digits[-4:] if len(form_digits) >= 4 else form_digits
    if last_4 and all(pos >= 2 for pos in last_4):
        flags['current_form_no_wins'] = True
        details.append(f'No wins in last 4 races (form: {form_str[-8:]}) — 2nd or worse throughout')

    total = sum(_SCORE_WEIGHTS[f] for f in flags if f in _SCORE_WEIGHTS)
    return total, flags, details


# ── Learning / Apply route ────────────────────────────────────────────────────

def toFractional_py(decimal):
    """Convert decimal odds to fractional string."""
    if not decimal or float(decimal) <= 1.0:
        return 'SP'
    d = float(decimal)
    tbl = [
        (1.1,'1/10'),(1.13,'1/9'),(1.2,'1/5'),(1.25,'1/4'),(1.33,'1/3'),
        (1.4,'2/5'),(1.5,'1/2'),(1.6,'3/5'),(1.67,'4/6'),(1.8,'4/5'),
        (1.9,'9/10'),(2.0,'1/1'),(2.1,'11/10'),(2.2,'6/5'),(2.25,'5/4'),
        (2.5,'6/4'),(2.62,'13/8'),(2.75,'7/4'),(3.0,'2/1'),(3.25,'9/4'),
        (3.5,'5/2'),(3.75,'11/4'),(4.0,'3/1'),(4.5,'7/2'),(5.0,'4/1'),
        (5.5,'9/2'),(6.0,'5/1'),(7.0,'6/1'),(8.0,'7/1'),(9.0,'8/1'),
        (10.0,'9/1'),(11.0,'10/1'),(13.0,'12/1'),(16.0,'15/1'),(21.0,'20/1'),
        (26.0,'25/1'),(34.0,'33/1'),(51.0,'50/1'),(101.0,'100/1'),
    ]
    for threshold, label in tbl:
        if d <= threshold:
            return label
    return f'{int(d-1)}/1'


def compute_winner_analysis(pick):
    """
    Compare our selection against the actual winner.
    Returns winner_found, scores, why_missed list, weight_nudges dict.
    """
    our_score   = float(pick.get('comprehensive_score') or pick.get('analysis_score') or 0)
    our_odds    = float(pick.get('odds') or 0)
    our_horse   = (pick.get('horse') or '').strip().lower()
    winner_name = (pick.get('result_winner_name') or '').strip()
    all_horses  = pick.get('all_horses') or []
    sb          = pick.get('score_breakdown') or {}

    if not winner_name:
        return {'winner_found': False, 'why_missed': ['Winner not yet recorded']}

    sorted_field = sorted(
        [h for h in all_horses if h.get('horse')],
        key=lambda h: float(h.get('score', 0)), reverse=True
    )
    winner_horse = next(
        (h for h in sorted_field if h.get('horse', '').strip().lower() == winner_name.lower()),
        None
    )
    winner_score = float(winner_horse.get('score', 0)) if winner_horse else 0
    winner_odds  = float(winner_horse.get('odds', 0)) if winner_horse else 0
    winner_rank  = next(
        (i + 1 for i, h in enumerate(sorted_field)
         if h.get('horse', '').strip().lower() == winner_name.lower()),
        0
    )
    score_gap     = our_score - winner_score
    why_missed    = []
    weight_nudges = {}

    if not winner_horse:
        why_missed.append(f'Winner "{winner_name}" was not in our scored Betfair field')
        return {'winner_found': False, 'winner_score': 0, 'winner_rank': 0,
                'winner_odds': 0, 'score_gap': score_gap,
                'why_missed': why_missed, 'weight_nudges': weight_nudges}

    if winner_odds > 0 and our_odds > 0 and winner_odds < our_odds * 0.80:
        why_missed.append(
            f'Market disagreed: winner at {toFractional_py(winner_odds)} vs our pick at {toFractional_py(our_odds)}'
        )
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 1.0

    if score_gap > 15:
        why_missed.append(
            f'Model over-confidence: {our_horse.title()} scored {our_score:.0f} vs {winner_name} {winner_score:.0f} — {score_gap:.0f}pt gap'
        )

    if 0 < winner_rank <= 3 and score_gap <= 10:
        why_missed.append(
            f'{winner_name} ranked {winner_rank} in our model at {winner_score:.0f}/100 — narrow margin, defensible pick'
        )

    if winner_rank > 5:
        why_missed.append(
            f'{winner_name} ranked {winner_rank} of {len(sorted_field)} in our model ({winner_score:.0f}/100) — model blind spot'
        )

    going_pts = float(sb.get('going_suitability', 0))
    if going_pts > 0 and our_score > 0 and (going_pts / our_score) > 0.25:
        why_missed.append(f'Going suitability over-weighted ({going_pts:.0f}pts = {going_pts/our_score*100:.0f}% of score)')
        weight_nudges['going_suitability'] = weight_nudges.get('going_suitability', 0) - 0.5

    cd_pts = float(sb.get('cd_bonus', 0)) + float(sb.get('course_performance', 0))
    if cd_pts > 20:
        why_missed.append(f'C&D bonus inflated score ({cd_pts:.0f}pts)')
        weight_nudges['cd_bonus'] = weight_nudges.get('cd_bonus', 0) - 0.3

    if winner_score < our_score * 0.85:
        weight_nudges['recent_win'] = weight_nudges.get('recent_win', 0) + 0.5

    if len(sorted_field) <= 5 and winner_odds > 0 and winner_odds < 2.5:
        why_missed.append(f'Small field ({len(sorted_field)} runners) with well-backed winner — market highly predictive')
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 0.5

    if not why_missed:
        why_missed.append(f'{winner_name} scored {winner_score:.0f}/100 rank {winner_rank} — within normal variance')

    return {
        'winner_found':   True,
        'winner_name':    winner_name,
        'winner_score':   int(winner_score),
        'winner_rank':    winner_rank,
        'winner_rank_of': len(sorted_field),
        'winner_odds':    winner_odds,
        'score_gap':      round(score_gap, 1),
        'why_missed':     why_missed,
        'weight_nudges':  weight_nudges,
    }


def apply_learning_lambda(headers, event):
    """POST /api/learning/apply — analyse missed winners, nudge SYSTEM_WEIGHTS in DynamoDB."""
    from decimal import Decimal
    from boto3.dynamodb.conditions import Key
    from datetime import timedelta

    method = (event.get('requestContext') or {}).get('http', {}).get('method',
              event.get('httpMethod', 'GET'))
    if method == 'OPTIONS':
        return {'statusCode': 204, 'headers': headers, 'body': ''}

    try:
        body = event.get('body') or '{}'
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        data = json.loads(body) if body else {}
        # Support date passed directly in payload (Step Functions) or in body (API Gateway)
        target_date = data.get('date') or event.get('date') or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Fetch all records for the date
        resp = table.query(KeyConditionExpression=Key('bet_date').eq(target_date))
        all_items = [decimal_to_float(i) for i in resp.get('Items', [])]

        picks = [p for p in all_items
                 if p.get('show_in_ui') is True
                 and p.get('result_winner_name')
                 and (p.get('outcome') or '').lower() in ('loss', 'placed')]

        if not picks:
            return {'statusCode': 200, 'headers': headers,
                    'body': json.dumps({'success': True,
                                        'message': 'No settled losses found — nothing to learn from',
                                        'changes': {}})}

        WEIGHT_MIN, WEIGHT_MAX, MAX_NUDGE = 2.0, 40.0, 1.5
        try:
            wt_resp = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
            raw_wt  = wt_resp.get('Item', {}).get('weights', {}) if 'Item' in wt_resp else {}
            weights = {k: float(v) for k, v in raw_wt.items()} if raw_wt else {}
        except Exception:
            weights = {}

        all_nudges, race_summaries = [], []
        for pick in picks:
            wa     = compute_winner_analysis(pick)
            nudges = wa.get('weight_nudges', {})
            if nudges:
                all_nudges.append(nudges)
            race_summaries.append({
                'horse':  pick.get('horse'),
                'winner': wa.get('winner_name', pick.get('result_winner_name', '?')),
                'why':    wa.get('why_missed', []),
            })

        changes = {}
        if all_nudges and weights:
            totals = {}
            for nd in all_nudges:
                for k, v in nd.items():
                    totals[k] = totals.get(k, 0) + v
            n = len(all_nudges)
            for factor, total in totals.items():
                if factor not in weights:
                    continue
                nudge = max(-MAX_NUDGE, min(MAX_NUDGE, total / n))
                old_v = weights[factor]
                new_v = round(max(WEIGHT_MIN, min(WEIGHT_MAX, old_v + nudge)), 2)
                if abs(new_v - old_v) > 0.01:
                    weights[factor] = new_v
                    changes[factor] = {'from': old_v, 'to': new_v, 'nudge': round(nudge, 2)}
            if changes:
                table.put_item(Item={
                    'bet_id':        'SYSTEM_WEIGHTS',
                    'bet_date':      'CONFIG',
                    'weights':       {k: Decimal(str(v)) for k, v in weights.items()},
                    'updated_at':    datetime.now().isoformat(),
                    'source':        'lambda_learning_apply',
                    'learning_date': target_date,
                })

        msg = (f"Applied {len(changes)} weight update(s) from {len(picks)} missed winner(s)"
               if changes else "No weight changes needed")
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({
            'success': True, 'date': target_date, 'picks_analysed': len(picks),
            'changes': changes, 'races': race_summaries, 'message': msg,
        })}
    except Exception as e:
        return {'statusCode': 500, 'headers': headers,
                'body': json.dumps({'success': False, 'error': str(e)})}

def _verdict(score):
    if score >= 13:
        return 'STRONG LAY CANDIDATE'
    elif score >= 9:
        return 'STRONG LAY'
    elif score >= 4:
        return 'CAUTION'
    return 'DO NOT SHOW'


def _verdict_colour(score):
    if score >= 13:
        return 'RED'
    elif score >= 9:
        return 'AMBER'
    elif score >= 4:
        return 'YELLOW'
    return 'GREEN'


def _utc_to_local_hhmm(utc_hhmm, date_str):
    """Convert UTC HH:MM to UK local time (BST = UTC+1, late Mar – late Oct)."""
    try:
        from datetime import date as _d
        d = _d.fromisoformat(date_str[:10])
        bst_start = _d(d.year, 3, 31)
        while bst_start.weekday() != 6:
            bst_start = _d(bst_start.year, bst_start.month, bst_start.day - 1)
        bst_end = _d(d.year, 10, 31)
        while bst_end.weekday() != 6:
            bst_end = _d(bst_end.year, bst_end.month, bst_end.day - 1)
        if not (bst_start <= d < bst_end):
            return utc_hhmm
        h, mn = map(int, utc_hhmm.split(':'))
        total = h * 60 + mn + 60
        return f'{(total // 60) % 24:02d}:{total % 60:02d}'
    except Exception:
        return utc_hhmm


def _fetch_sl_winner_map():
    """
    Fetch SL fast-results and return {(course_lower, local_hhmm): winner_name}.
    Returns empty dict on any error.
    """
    import re as _re
    try:
        import urllib.request as _ur
        req = _ur.Request(
            'https://www.sportinglife.com/racing/fast-results/all',
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/122.0.0.0 Safari/537.36'
                ),
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-GB,en;q=0.5',
                'Referer': 'https://www.sportinglife.com/',
            },
        )
        with _ur.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'[favs_run] SL fetch error: {e}')
        return {}
    m = _re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, _re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group(1))
    except Exception:
        return {}
    fast = data.get('props', {}).get('pageProps', {}).get('fastResults', [])
    winner_map = {}
    for fr in fast:
        top_horses = fr.get('top_horses')
        if not top_horses:
            continue
        course = fr.get('courseName', '')
        off_time = fr.get('time', '')
        if not course or not off_time:
            continue
        sorted_h = sorted(top_horses, key=lambda h: h.get('position', 99))
        winner = sorted_h[0].get('horse_name', '') if sorted_h else ''
        winner = _re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', winner).strip()
        if winner:
            winner_map[(course.lower().replace('-', ' ').strip(), off_time)] = winner
    print(f'[favs_run] SL winner_map: {len(winner_map)} races')
    return winner_map


def _analyse_date_lambda(target_date_str, tbl, winner_map=None):
    from boto3.dynamodb.conditions import Key as DKey
    resp = tbl.query(KeyConditionExpression=DKey('bet_date').eq(target_date_str))
    all_items = [_dec(it) for it in resp.get('Items', [])]
    if not all_items:
        return []

    races = {}
    for it in all_items:
        rt = str(it.get('race_time', ''))[:19]  # keep HH:MM:SS for UTC display
        course = it.get('course', '') or it.get('race_course', '')
        key = f'{rt}|{course}'
        races.setdefault(key, []).append(it)

    results = []
    for race_key, runners in sorted(races.items()):
        rt, course = race_key.split('|', 1)

        def sort_odds(h):
            o = _odds_dec(h.get('odds') or h.get('decimal_odds'))
            return o if o else 99.0

        runners_sorted = sorted(runners, key=sort_odds)
        fav = runners_sorted[0]
        fav_odds_dec = sort_odds(fav)

        if fav_odds_dec > 2.25:
            continue

        all_horses_raw = fav.get('all_horses') or []
        if all_horses_raw:
            all_horses_sorted = sorted(all_horses_raw, key=lambda h: float(h.get('odds') or 99))
        else:
            all_horses_sorted = [
                {'horse': h.get('horse', ''), 'score': h.get('comprehensive_score', 0), 'odds': sort_odds(h)}
                for h in runners_sorted
            ]

        lay_score, flags, details = _score_fav(fav, all_horses_sorted)
        verd = _verdict(lay_score)
        race_name = fav.get('race_name') or f'{course} {rt[11:16]}'
        fav_name = fav.get('horse', '') or ''

        # Determine outcome: SL winner_map first, then DynamoDB runner scan, then fav's own field
        fav_outcome = None
        if winner_map:
            import re as _re2
            race_hhmm = rt[11:16] if len(rt) >= 16 else ''
            course_key = course.lower().replace('-', ' ').strip()
            try:
                lh, lm = map(int, race_hhmm.split(':'))
                local_mins = lh * 60 + lm
                best_diff = 999
                best_winner = None
                for (c_key, t_key), w_name in winner_map.items():
                    if c_key != course_key:
                        continue
                    wh, wm = map(int, t_key.split(':'))
                    diff = abs((wh * 60 + wm) - local_mins)
                    if diff < best_diff:
                        best_diff = diff
                        best_winner = w_name.strip()
                if best_winner and best_diff <= 10:
                    fav_outcome = (
                        'win' if best_winner.lower() == fav_name.strip().lower()
                        else 'loss'
                    )
            except Exception:
                pass
        if fav_outcome is None:
            winner_name = None
            for h in runners:
                if (h.get('outcome') or '').lower() == 'win':
                    winner_name = h.get('horse', '')
                    break
            if winner_name:
                fav_outcome = (
                    'win' if winner_name.strip().lower() == fav_name.strip().lower()
                    else 'loss'
                )
            # else: leave fav_outcome as None — race hasn't been settled yet

        results.append({
            'date':          target_date_str,
            'race_time':     rt,
            'course':        course,
            'race_name':     race_name,
            'favourite':     fav_name or '?',
            'fav_odds':      fav_odds_dec,
            'fav_sys_score': float(fav.get('comprehensive_score') or fav.get('score', 0)),
            'score_gap':     float(fav.get('score_gap') or 0),
            'runners':       len(runners),
            'lay_score':     lay_score,
            'flags':         list(flags.keys()),
            'details':       details,
            'verdict':       verd,
            'verdict_colour': _verdict_colour(lay_score),
            'form':          fav.get('form', ''),
            'trainer':       fav.get('trainer', ''),
            'jockey':        fav.get('jockey', ''),
            'our_pick':      fav.get('show_in_ui', False),
            'outcome':       fav_outcome,
        })
    return results


def get_major_race_analysis(headers):
    """GET /api/major-race-analysis — return all stored early-bird predictions."""
    try:
        from boto3.dynamodb.conditions import Key as DKey
        resp = table.query(
            KeyConditionExpression=DKey('bet_date').eq('MAJOR_ANALYSIS')
        )
        items = [decimal_to_float(it) for it in resp.get('Items', [])]
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True, 'analyses': items}, default=str)
        }
    except Exception as e:
        print(f'get_major_race_analysis error: {e}')
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'success': False, 'error': str(e)})}


def run_major_race_analysis(headers, event):
    """POST /api/major-race-analysis/run — fetch Betfair ante-post odds & score horses for upcoming major races.
    Admin-only. Designed to run weekly via EventBridge or manual trigger."""
    import urllib.parse as _up
    import urllib.request as _ur

    # Admin auth check
    raw_headers = event.get('headers', {})
    admin_token = raw_headers.get('x-admin-token', '')
    if admin_token:
        sess_key = f'__session__{admin_token}'
        sess = subscribers_table.get_item(Key={'email': sess_key}).get('Item')
        if not sess or sess.get('role') != 'admin':
            return {'statusCode': 403, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Admin auth required'})}
    else:
        source = event.get('source', '')
        if source not in ('aws.events', 'scheduled-major-analysis'):
            return {'statusCode': 403, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Admin auth required'})}

    # Major races calendar (same as frontend)
    MAJOR_RACES = [
        {'date': '2026-04-18', 'meeting': 'Ayr', 'name': 'Scottish Grand National', 'type': 'NH', 'grade': 'G3'},
        {'date': '2026-04-29', 'meeting': 'Punchestown', 'name': 'Punchestown Champion Chase', 'type': 'NH', 'grade': 'G1'},
        {'date': '2026-04-30', 'meeting': 'Punchestown', 'name': 'Punchestown Gold Cup', 'type': 'NH', 'grade': 'G1'},
        {'date': '2026-05-01', 'meeting': 'Punchestown', 'name': 'Punchestown Champion Hurdle', 'type': 'NH', 'grade': 'G1'},
        {'date': '2026-05-01', 'meeting': 'Punchestown', 'name': 'World Series Hurdle', 'type': 'NH', 'grade': 'G1'},
        {'date': '2026-05-02', 'meeting': 'Newmarket', 'name': '2000 Guineas', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-05-03', 'meeting': 'Newmarket', 'name': '1000 Guineas', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-05-08', 'meeting': 'Chester', 'name': 'Chester Vase', 'type': 'Flat', 'grade': 'G3'},
        {'date': '2026-05-14', 'meeting': 'York', 'name': 'Dante Stakes', 'type': 'Flat', 'grade': 'G2'},
        {'date': '2026-05-15', 'meeting': 'York', 'name': 'Musidora Stakes', 'type': 'Flat', 'grade': 'G3'},
        {'date': '2026-06-05', 'meeting': 'Epsom', 'name': 'Coronation Cup', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-06-05', 'meeting': 'Epsom', 'name': 'The Oaks', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-06-06', 'meeting': 'Epsom', 'name': 'The Derby', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-06-16', 'meeting': 'Royal Ascot', 'name': 'Queen Anne Stakes', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-06-17', 'meeting': 'Royal Ascot', 'name': "Prince of Wales's Stakes", 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-06-18', 'meeting': 'Royal Ascot', 'name': 'Ascot Gold Cup', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-07-09', 'meeting': 'Sandown', 'name': 'Eclipse Stakes', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-07-25', 'meeting': 'Ascot', 'name': 'King George VI & Queen Elizabeth Stakes', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-07-29', 'meeting': 'Goodwood', 'name': 'Sussex Stakes', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-08-20', 'meeting': 'York', 'name': 'Juddmonte International', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-09-12', 'meeting': 'Doncaster', 'name': 'St Leger', 'type': 'Flat', 'grade': 'G1'},
        {'date': '2026-10-17', 'meeting': 'Ascot', 'name': 'QIPCO Champion Stakes', 'type': 'Flat', 'grade': 'G1'},
    ]

    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    upcoming = [r for r in MAJOR_RACES if r['date'] >= today_str]

    # ── Authenticate to Betfair ───────────────────────────────────────────────
    sm = boto3.client('secretsmanager', region_name='eu-west-1')
    creds = json.loads(sm.get_secret_value(SecretId='betfair-credentials')['SecretString'])
    app_key = creds['app_key']
    BF_BASE = 'https://api.betfair.com/exchange/betting/rest/v1.0'

    session_token = None
    try:
        login_data = _up.urlencode(
            {'username': creds['username'], 'password': creds['password']}
        ).encode('utf-8')
        login_req = _ur.Request(
            'https://identitysso.betfair.com/api/login',
            data=login_data,
            headers={'X-Application': app_key, 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'},
            method='POST'
        )
        with _ur.urlopen(login_req, timeout=10) as r:
            result = json.loads(r.read())
            session_token = result.get('sessionToken') or result.get('token')
    except Exception as e:
        print(f'[major-analysis] Betfair login error: {e}')
        session_token = creds.get('session_token', '')

    if not session_token:
        return {
            'statusCode': 500, 'headers': headers,
            'body': json.dumps({'success': False, 'error': 'Could not authenticate to Betfair'})
        }

    bf_hdrs = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    def bf_post(endpoint, payload):
        data = json.dumps(payload).encode('utf-8')
        req = _ur.Request(f'{BF_BASE}/{endpoint}/', data=data, headers=bf_hdrs, method='POST')
        with _ur.urlopen(req, timeout=20) as r:
            return json.loads(r.read())

    print(f'[major-analysis] Betfair authenticated, fetching ante-post markets...')

    # ── Fetch ante-post + regular WIN markets ─────────────────────────────────
    # Betfair uses "ANTEPOST_WIN" for ante-post markets (no venue set).
    # Regular "WIN" markets appear closer to race day (1-2 days out) with full venue/runner metadata.
    all_bf_markets = []
    for mtype in ['ANTEPOST_WIN', 'WIN']:
        try:
            markets = bf_post('listMarketCatalogue', {
                'filter': {
                    'eventTypeIds': ['7'],
                    'marketTypeCodes': [mtype],
                    'marketStartTime': {
                        'from': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'to': (datetime.utcnow() + timedelta(days=200)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    },
                },
                'maxResults': 1000,
                'marketProjection': ['RUNNER_METADATA', 'EVENT', 'MARKET_START_TIME', 'COMPETITION', 'MARKET_DESCRIPTION'],
            })
            print(f'[major-analysis] Betfair {mtype}: {len(markets)} markets found')
            all_bf_markets.extend(markets)
        except Exception as e:
            print(f'[major-analysis] Betfair {mtype} fetch error: {e}')

    # ── Match Betfair markets to our major races ──────────────────────────────
    def _norm(s):
        return s.lower().strip().replace("'", '').replace('.', '').replace('-', ' ')

    # Build keyword aliases for matching (Betfair uses shortened names)
    RACE_ALIASES = {
        'scottish grand national': ['scottish grand national'],
        'punchestown champion chase': ['champion chase'],
        'punchestown gold cup': ['gold cup'],
        'punchestown champion hurdle': ['champion hurdle'],
        'world series hurdle': ['champion stayers hurdle', 'world series hurdle', 'stayers hurdle'],
        '2000 guineas': ['2000 guineas'],
        '1000 guineas': ['1000 guineas'],
        'chester vase': ['chester vase', 'chester cup'],
        'dante stakes': ['dante stakes', 'dante'],
        'musidora stakes': ['musidora stakes', 'musidora'],
        'coronation cup': ['coronation cup'],
        'the oaks': ['the oaks', 'oaks'],
        'the derby': ['the derby', 'derby'],
        'queen anne stakes': ['queen anne'],
        "prince of wales's stakes": ['prince of wales'],
        'ascot gold cup': ['gold cup', 'royal ascot gold cup'],
        'eclipse stakes': ['eclipse stakes', 'eclipse'],
        'king george vi & queen elizabeth stakes': ['king george'],
        'sussex stakes': ['sussex stakes', 'sussex'],
        'juddmonte international': ['juddmonte international', 'juddmonte'],
        'st leger': ['st leger'],
        'qipco champion stakes': ['champion stakes', 'qipco champion'],
        'lockinge stakes': ['lockinge'],
    }

    def _match_market(race, market):
        """Check if a Betfair market matches our major race."""
        market_name = _norm(market.get('marketName', ''))
        market_start = market.get('marketStartTime', '')
        race_name_lower = _norm(race['name'])

        # For ANTEPOST_WIN: no venue, match by name keywords + approximate date (±3 days)
        desc = market.get('description', {})
        is_antepost = desc.get('marketType') == 'ANTEPOST_WIN' if desc else 'antepost' in market.get('marketId', '').lower()

        # Get aliases for this race
        aliases = RACE_ALIASES.get(race_name_lower, [race_name_lower])

        # Check if market name matches any alias
        name_match = False
        for alias in aliases:
            alias_words = [w for w in alias.split() if len(w) > 2]
            hits = sum(1 for w in alias_words if w in market_name)
            # Require ALL key words to match to avoid cross-contamination
            # e.g. "1000 guineas" must not match "2000 guineas"
            if alias_words and hits >= len(alias_words):
                name_match = True
                break

        if not name_match:
            return False

        # Date match: for ante-post, allow ±3 day margin (Betfair dates may differ)
        if market_start:
            try:
                market_date = datetime.strptime(market_start[:10], '%Y-%m-%d')
                race_date = datetime.strptime(race['date'], '%Y-%m-%d')
                if abs((market_date - race_date).days) > 3:
                    # But for ambiguous names like "Gold Cup" or "Champion Chase",
                    # reject if date is far off to avoid mixing up different festivals
                    return False
            except Exception:
                pass

        return True

    # ── Score a horse ─────────────────────────────────────────────────────────
    def _score_horse(horse, all_horses, race):
        score = 0
        factors = []
        odds = horse.get('odds')

        # 1. Market position (30pts max)
        if odds and odds > 0:
            if odds <= 3.0:
                score += 30; factors.append(f'Market favourite @ {odds:.2f} — strong support')
            elif odds <= 5.0:
                score += 24; factors.append(f'Well-backed @ {odds:.2f}')
            elif odds <= 8.0:
                score += 18; factors.append(f'Solid market position @ {odds:.2f}')
            elif odds <= 15.0:
                score += 12; factors.append(f'Mid-market @ {odds:.2f} — each-way contender')
            elif odds <= 25.0:
                score += 6; factors.append(f'Outsider @ {odds:.2f}')
            else:
                score += 2; factors.append(f'Big price @ {odds:.2f}')

        # 2. Betfair market liquidity signal (totalMatched)
        matched = horse.get('totalMatched', 0)
        if matched > 10000:
            score += 10; factors.append(f'Heavy market interest (£{matched:,.0f} matched)')
        elif matched > 2000:
            score += 6; factors.append(f'Good market liquidity (£{matched:,.0f} matched)')
        elif matched > 500:
            score += 3; factors.append(f'Some market activity (£{matched:,.0f} matched)')

        # 3. Trainer quality (10pts)
        trainer = _norm(horse.get('trainer', ''))
        top_flat = ['aidan o brien', 'charlie appleby', 'john gosden', 'william haggas', 'andrew balding', 'roger varian', 'karl burke']
        top_nh = ['willie mullins', 'gordon elliott', 'henry de bromhead', 'nicky henderson', 'paul nicholls', 'dan skelton', 'olly murphy']
        top_trainers = top_flat if race.get('type') == 'Flat' else top_nh
        if any(t in trainer for t in top_trainers):
            score += 10; factors.append(f'Elite trainer: {horse.get("trainer", "")}')

        # 4. Grade bonus (10pts)
        grade = race.get('grade', '')
        if grade == 'G1':
            score += 5; factors.append('Group 1 — highest level')
        elif grade == 'G2':
            score += 3; factors.append('Group 2')

        # 5. Market rank bonus (8pts)
        sorted_by_odds = sorted([h for h in all_horses if h.get('odds')], key=lambda h: h['odds'])
        for i, h in enumerate(sorted_by_odds):
            if h['name'] == horse['name']:
                if i == 0:
                    score += 8; factors.append('Shortest price in the market')
                elif i == 1:
                    score += 5; factors.append('Second favourite')
                elif i == 2:
                    score += 3; factors.append('Third in the betting')
                break

        # 6. Lay/back spread tightness (good indicator of certainty)
        spread = horse.get('spread')
        if spread is not None and spread < 0.5:
            score += 5; factors.append('Tight spread — market confident')

        return min(score, 100), factors

    # ── Process each upcoming major race ──────────────────────────────────────
    analysed = []
    used_market_ids = set()  # prevent same market being used for multiple races
    for race in upcoming[:15]:
        race_key = f"{race['date']}__{race['name'].replace(' ', '_')}"

        # Find matching Betfair market(s), preferring unused ones
        matched_markets = [m for m in all_bf_markets if _match_market(race, m) and m['marketId'] not in used_market_ids]
        print(f'[major-analysis] {race["name"]} ({race["meeting"]}) -> {len(matched_markets)} Betfair market(s) matched')

        horses = []
        if matched_markets:
            # Use only the first (best) matched market
            best_market = matched_markets[0]
            market_ids = [best_market['marketId']]
            used_market_ids.add(best_market['marketId'])
            try:
                books = bf_post('listMarketBook', {
                    'marketIds': market_ids,
                    'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
                })
            except Exception as e:
                print(f'[major-analysis] Betfair odds fetch error for {race["name"]}: {e}')
                books = []

            # Build runner map from catalogue
            runner_map = {}
            for runner in best_market.get('runners', []):
                    sid = runner['selectionId']
                    meta = runner.get('metadata', {})
                    runner_map[sid] = {
                        'name': runner['runnerName'],
                        'trainer': meta.get('TRAINER_NAME', ''),
                        'jockey': meta.get('JOCKEY_NAME', ''),
                        'form': meta.get('FORM', ''),
                    }

            # Merge with live odds
            for book in books:
                for runner in book.get('runners', []):
                    sid = runner['selectionId']
                    if runner.get('status') != 'ACTIVE':
                        continue
                    info = runner_map.get(sid, {'name': f'Selection {sid}'})
                    back = runner.get('ex', {}).get('availableToBack', [])
                    lay = runner.get('ex', {}).get('availableToLay', [])
                    best_back = back[0]['price'] if back else None
                    best_lay = lay[0]['price'] if lay else None
                    spread = round(best_lay - best_back, 2) if best_back and best_lay else None

                    # Fractional odds display
                    frac = ''
                    if best_back:
                        dec_minus = best_back - 1
                        # Common fractions lookup
                        common = {0.5:'1/2', 1.0:'1/1', 2.0:'2/1', 3.0:'3/1', 4.0:'4/1', 5.0:'5/1',
                                  6.0:'6/1', 7.0:'7/1', 8.0:'8/1', 9.0:'9/1', 10.0:'10/1', 11.0:'11/1',
                                  12.0:'12/1', 14.0:'14/1', 16.0:'16/1', 20.0:'20/1', 25.0:'25/1',
                                  33.0:'33/1', 40.0:'40/1', 50.0:'50/1', 66.0:'66/1', 100.0:'100/1',
                                  0.25:'1/4', 0.33:'1/3', 1.5:'3/2', 2.5:'5/2', 3.5:'7/2', 4.5:'9/2',
                                  5.5:'11/2', 6.5:'13/2', 7.5:'15/2'}
                        frac = common.get(dec_minus, f'{dec_minus:.1f}/1')

                    horses.append({
                        'name': info['name'],
                        'odds': best_back,
                        'odds_display': frac,
                        'trainer': info.get('trainer', ''),
                        'jockey': info.get('jockey', ''),
                        'form': info.get('form', ''),
                        'totalMatched': runner.get('totalMatched', 0),
                        'spread': spread,
                    })

        # Score all horses
        scored_horses = []
        for h in horses:
            score, factors = _score_horse(h, horses, race)
            scored_horses.append({
                'name': h['name'],
                'odds': h.get('odds'),
                'odds_display': h.get('odds_display', ''),
                'trainer': h.get('trainer', ''),
                'jockey': h.get('jockey', ''),
                'form': h.get('form', ''),
                'score': score,
                'factors': factors,
                'totalMatched': h.get('totalMatched', 0),
            })

        scored_horses.sort(key=lambda h: h['score'], reverse=True)

        top3 = scored_horses[:3]
        pick = scored_horses[0] if scored_horses else None

        days_to_race = max(0, (datetime.strptime(race['date'], '%Y-%m-%d') - datetime.utcnow()).days)

        analysis = {
            'bet_date': 'MAJOR_ANALYSIS',
            'bet_id': race_key,
            'race_name': race['name'],
            'race_date': race['date'],
            'meeting': race['meeting'],
            'grade': race.get('grade', ''),
            'type': race.get('type', ''),
            'days_to_race': days_to_race,
            'analysed_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'total_horses': len(scored_horses),
            'top_pick': pick['name'] if pick else None,
            'top_pick_score': pick['score'] if pick else 0,
            'top_pick_odds': pick.get('odds_display', '') if pick else '',
            'top_pick_odds_decimal': pick.get('odds') if pick else None,
            'top_pick_factors': pick['factors'] if pick else [],
            'top3': top3,
            'all_runners': scored_horses[:10],
            'confidence': 'HIGH' if pick and pick['score'] >= 50 else 'MEDIUM' if pick and pick['score'] >= 30 else 'LOW' if pick else 'NO DATA',
        }

        # Store in DynamoDB
        try:
            table.put_item(Item=json.loads(json.dumps(analysis), parse_float=Decimal))
            print(f"[major-analysis] Stored: {race['name']} -> {pick['name'] if pick else 'NO PICK'} @ {pick.get('odds') if pick else 'N/A'} (score: {pick['score'] if pick else 0})")
        except Exception as e:
            print(f"[major-analysis] DynamoDB error for {race['name']}: {e}")

        analysed.append(analysis)

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'message': f'Analysed {len(analysed)} major races',
            'analysed': analysed,
        }, default=str)
    }


def get_favs_run_lambda(headers, event):
    """GET /api/favs-run?days=N&date=YYYY-MM-DD"""
    try:
        qp = event.get('queryStringParameters') or {}
        today = datetime.now().strftime('%Y-%m-%d')
        target_date = qp.get('date', today)
        days = int(qp.get('days', 1))

        tbl = dynamodb.Table('SureBetBets')

        # Fetch SL fast-results once to annotate finished races with win/loss
        winner_map = _fetch_sl_winner_map()

        all_results = []
        for i in range(days):
            d = (datetime.strptime(target_date, '%Y-%m-%d') + timedelta(days=i)).strftime('%Y-%m-%d')
            all_results.extend(_analyse_date_lambda(d, tbl, winner_map))

        caution   = [r for r in all_results if r['lay_score'] >= 4]
        strong    = [r for r in all_results if r['lay_score'] >= 9]
        red_flag  = [r for r in all_results if r['lay_score'] >= 13]

        # Lay win % — how often the favourite lost (settled races only)
        settled   = [r for r in all_results if r.get('outcome') and r['outcome'].lower() in ('win','won','loss','lost')]
        fav_lost  = [r for r in settled if r['outcome'].lower() in ('loss','lost')]
        lay_win_pct = round(len(fav_lost) / len(settled) * 100, 1) if settled else None

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success':   True,
                'generated': datetime.now().isoformat(),
                'summary':   {'total': len(all_results), 'caution': len(caution), 'strong': len(strong), 'red_flag': len(red_flag),
                              'settled': len(settled), 'fav_lost': len(fav_lost), 'lay_win_pct': lay_win_pct},
                'races':     all_results,
            }, default=str)
        }
    except Exception as e:
        print(f'get_favs_run_lambda error: {e}')
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': str(e)})
        }


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN API
# ─────────────────────────────────────────────────────────────────────────────

# Default config thresholds (mirrors complete_daily_analysis.py constants)
ADMIN_DEFAULT_CONFIG = {
    'min_confidence':        78,
    'min_confidence_hcap':   85,
    'min_confidence_norace': 75,
    'target_picks':           3,
    'picks_gate_hour_utc':   12,   # 1pm BST = 12 UTC
    'elite_threshold':       95,
    'strong_threshold':      90,
    'good_threshold':        80,
    'fair_threshold':        65,
    'risky_threshold':       50,
}

# Default scoring weights — mirrors comprehensive_pick_logic.py DEFAULT_WEIGHTS
ADMIN_DEFAULT_WEIGHTS = {
    'sweet_spot':                 12,
    'optimal_odds':               10,
    'recent_win':                 16,
    'total_wins':                  8,
    'consistency':                 6,
    'course_bonus':               12,
    'database_history':           15,
    'going_suitability':          16,
    'track_pattern_bonus':         8,
    'trainer_reputation':         15,
    'trainer_tier2':               8,
    'trainer_tier3':               4,
    'favorite_correction':         7,
    'jockey_quality':             12,
    'jockey_tier2':                6,
    'weight_penalty':             10,
    'age_bonus':                   7,
    'distance_suitability':       18,
    'novice_race_penalty':        15,
    'bounce_back_bonus':           8,
    'short_form_improvement':      8,
    'aw_low_class_penalty':       50,
    'heavy_going_penalty':        12,
    'cd_bonus':                   18,
    'graded_race_cd_bonus':        8,
    'official_rating_bonus':       8,
    'jockey_course_bonus':         8,
    'relative_weight_bonus':       8,
    'meeting_focus_trainer':      10,
    'meeting_focus_jockey':       10,
    'meeting_focus_combo':        10,
    'new_trainer_debut':           5,
    'form_exact_course_win':      20,
    'form_exact_distance_win':    20,
    'form_going_win':             16,
    'form_going_place':            6,
    'form_fresh_optimal':         10,
    'form_close_2nd':             14,
    'form_or_rising':             10,
    'form_big_field_win':          8,
    'unexposed_bonus':            12,
    'aw_evening_penalty':         12,
    'unknown_trainer_penalty':     8,
    'large_field_penalty':        10,
    'class_drop_bonus':           12,
    'same_trainer_rival_penalty': 10,
    'irish_handicap_penalty':     10,
}


def _check_admin_token(event):
    """Validate X-Admin-Token header. Returns user_email if valid, else None."""
    req_headers = event.get('headers') or {}
    token = req_headers.get('x-admin-token') or req_headers.get('X-Admin-Token') or ''
    if not token:
        return None
    try:
        item = subscribers_table.get_item(Key={'email': f'__session__{token}'}).get('Item')
        if not item:
            return None
        expires = item.get('expires_at', '')
        if expires and datetime.utcnow() > datetime.fromisoformat(expires.replace('Z', '')):
            return None
        return item.get('user_email')
    except Exception as e:
        print(f'_check_admin_token error: {e}')
        return None


def admin_get_config(headers, event):
    """GET /api/admin/config — returns current weights + thresholds."""
    user_email = _check_admin_token(event)
    if not user_email:
        return {'statusCode': 403, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Forbidden'})}

    try:
        # Load current scoring weights
        wt_resp = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
        raw_weights = wt_resp.get('Item', {}).get('weights', {})
        current_weights = {k: float(v) for k, v in raw_weights.items()} if raw_weights else ADMIN_DEFAULT_WEIGHTS.copy()

        # Load current config thresholds
        cfg_resp = table.get_item(Key={'bet_id': 'SYSTEM_CONFIG', 'bet_date': 'CONFIG'})
        raw_cfg = cfg_resp.get('Item', {}).get('config', {})
        current_config = {k: float(v) for k, v in raw_cfg.items()} if raw_cfg else ADMIN_DEFAULT_CONFIG.copy()

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success':          True,
                'weights':          current_weights,
                'config':           current_config,
                'default_weights':  ADMIN_DEFAULT_WEIGHTS,
                'default_config':   ADMIN_DEFAULT_CONFIG,
                'weights_saved_at': wt_resp.get('Item', {}).get('updated_at', None),
                'config_saved_at':  cfg_resp.get('Item', {}).get('updated_at', None),
            })
        }
    except Exception as e:
        print(f'admin_get_config error: {e}')
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'success': False, 'error': str(e)})}


def admin_save_config(headers, event):
    """POST /api/admin/config — saves weights and/or thresholds to DynamoDB."""
    user_email = _check_admin_token(event)
    if not user_email:
        return {'statusCode': 403, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Forbidden'})}

    try:
        data = json.loads(event.get('body') or '{}')
        weights = data.get('weights')
        config  = data.get('config')
        now_iso = datetime.utcnow().isoformat() + 'Z'

        if weights:
            # Validate all values are numbers
            for k, v in weights.items():
                try:
                    float(v)
                except (TypeError, ValueError):
                    return {'statusCode': 400, 'headers': headers,
                            'body': json.dumps({'success': False, 'error': f'Invalid value for weight "{k}": {v}'})}
            table.put_item(Item={
                'bet_id':     'SYSTEM_WEIGHTS',
                'bet_date':   'CONFIG',
                'weights':    {k: Decimal(str(float(v))) for k, v in weights.items()},
                'updated_at': now_iso,
                'updated_by': user_email,
            })

        if config:
            for k, v in config.items():
                try:
                    float(v)
                except (TypeError, ValueError):
                    return {'statusCode': 400, 'headers': headers,
                            'body': json.dumps({'success': False, 'error': f'Invalid value for config "{k}": {v}'})}
            table.put_item(Item={
                'bet_id':     'SYSTEM_CONFIG',
                'bet_date':   'CONFIG',
                'config':     {k: Decimal(str(float(v))) for k, v in config.items()},
                'updated_at': now_iso,
                'updated_by': user_email,
            })

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True, 'message': 'Configuration saved successfully', 'saved_by': user_email, 'saved_at': now_iso})
        }
    except Exception as e:
        print(f'admin_save_config error: {e}')
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'success': False, 'error': str(e)})}


def admin_get_subscribers(headers, event):
    """GET /api/admin/subscribers — returns all subscriber records."""
    user_email = _check_admin_token(event)
    if not user_email:
        return {'statusCode': 403, 'headers': headers, 'body': json.dumps({'success': False, 'error': 'Forbidden'})}

    try:
        resp = subscribers_table.scan()
        items = resp.get('Items', [])
        # Filter out internal session records
        users = [
            {k: v for k, v in i.items() if k != 'password_hash'}
            for i in items
            if not str(i.get('email', '')).startswith('__session__')
        ]
        # Split into real accounts (email key) vs username shadow rows
        email_rows    = [u for u in users if '@' in str(u.get('email', '')) and not str(u.get('email', '')).startswith('u#')]
        username_rows = [u for u in users if str(u.get('email', '')).startswith('u#')]
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success':  True,
                'total':    len(email_rows),
                'users':    decimal_to_float(sorted(email_rows, key=lambda x: x.get('joined_at', ''))),
            }, default=str)
        }
    except Exception as e:
        print(f'admin_get_subscribers error: {e}')
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'success': False, 'error': str(e)})}

