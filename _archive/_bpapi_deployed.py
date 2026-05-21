"""
AWS Lambda function to serve betting picks from DynamoDB
Provides REST API for frontend hosted on Amplify
"""
import json
import urllib.request
import urllib.parse
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

def lambda_handler(event, context):
    """Handle API Gateway requests"""
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
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
        elif 'results/auto-record' in path:
            return auto_record_pending_results(headers)
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
    today = datetime.now().strftime('%Y-%m-%d')
    
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
    
    # CRITICAL: Only show items explicitly marked for UI display
    horse_items = [item for item in horse_items if item.get('show_in_ui') == True]
    
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
        now = datetime.utcnow()
        future_picks = []
        
        for item in horse_items:
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
    
    # ONE PICK PER RACE: keep only the highest-scoring pick per race
    seen_races = {}
    for pick in future_picks:
        race_key = (pick.get('course', ''), pick.get('race_time', ''))
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
    from boto3.dynamodb.conditions import Attr
    CUMULATIVE_ROI_START = '2026-03-22'
    try:
        all_items = []
        scan_kwargs = {'FilterExpression': Attr('bet_date').gte(CUMULATIVE_ROI_START)}
        while True:
            resp = table.scan(**scan_kwargs)
            all_items.extend(resp.get('Items', []))
            if 'LastEvaluatedKey' not in resp:
                break
            scan_kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

        picks = [decimal_to_float(i) for i in all_items]
        picks = [
            p for p in picks
            if p.get('course') and p.get('course') != 'Unknown'
            and p.get('horse') and p.get('horse') != 'Unknown'
            and p.get('show_in_ui') is True
            and not p.get('is_learning_pick', False)
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
            odds = float(p.get('odds', 0))
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


def check_yesterday_results(headers):
    """Check results for yesterday's UI picks only (show_in_ui=True)"""
    from boto3.dynamodb.conditions import Key
    from datetime import timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get ALL yesterday's picks using partition key query
    response = table.query(
        KeyConditionExpression=Key('bet_date').eq(yesterday)
    )
    
    all_picks = response.get('Items', [])
    all_picks = [decimal_to_float(item) for item in all_picks]
    
    # Filter for UI picks only - keep others in database for learning
    picks = [item for item in all_picks if item.get('show_in_ui') == True]
    
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
            odds = float(p.get('odds', 0))
            bet_type = p.get('bet_type', 'WIN').upper()
            if bet_type == 'WIN':
                total_return += stake * odds
            else:  # EW
                ew_fraction = float(p.get('ew_fraction', 0.2) or 0.2)
                total_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
        elif outcome == 'PLACED':
            stake = float(p.get('stake', 1.0))
            odds = float(p.get('odds', 0))
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
                o = float(p.get('odds', 0))
                bt = p.get('bet_type', 'WIN').upper()
                if bt == 'WIN':
                    sport_return += s * o
                else:  # EW
                    ewf = float(p.get('ew_fraction', 0.2) or 0.2)
                    sport_return += (s/2) * o + (s/2) * (1 + (o-1) * ewf)
            elif outcome == 'PLACED':
                s = float(p.get('stake', 1.0))
                o = float(p.get('odds', 0))
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
    """Check results for today's UI picks only (show_in_ui=True)"""
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

    # Filter for UI picks only - keep others in database for learning
    picks = [item for item in all_picks if item.get('show_in_ui') == True]

    # Filter: race must be TODAY (excludes yesterday's races stored with today's bet_date)
    picks = [item for item in picks if str(item.get('race_time', '')).startswith(today)]

    # ONE PICK PER RACE: keep only the highest-scoring pick per (course, race_time)
    # Eliminates multiple runners saved by learning workflow for skipped/close-call races
    seen_races = {}
    for pick in picks:
        race_key = (pick.get('course', ''), pick.get('race_time', ''))
        existing = seen_races.get(race_key)
        score = float(pick.get('comprehensive_score') or pick.get('analysis_score') or 0)
        existing_score = float(existing.get('comprehensive_score') or existing.get('analysis_score') or 0) if existing else 0
        if not existing or score > existing_score:
            seen_races[race_key] = pick
    picks = list(seen_races.values())
    # Sort by score and keep top 5
    picks.sort(key=lambda x: float(x.get('comprehensive_score') or x.get('analysis_score') or 0), reverse=True)
    picks = picks[:5]
    print(f"After dedup + top-5 filter: {len(picks)} picks")

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
            odds = float(p.get('odds', 0))
            bet_type = p.get('bet_type', 'WIN').upper()
            if bet_type == 'WIN':
                total_return += stake * odds
            else:  # EW
                ew_fraction = float(p.get('ew_fraction', 0.2))
                total_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
        elif outcome == 'PLACED':
            stake = float(p.get('stake', 2.0))
            odds = float(p.get('odds', 0))
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
                odds = float(p.get('odds', 0))
                bet_type = p.get('bet_type', 'WIN').upper()
                if bet_type == 'WIN':
                    sport_return += stake * odds
                else:  # EW
                    ew_fraction = float(p.get('ew_fraction', 0.2))
                    sport_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
            elif outcome == 'PLACED':
                stake = float(p.get('stake', 2.0))
                odds = float(p.get('odds', 0))
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
            # ── listMarketBook: statuses + sort priority (= finish position) ──
            book_resp = bf_post('listMarketBook', {
                'marketIds': [market_id],
                'priceProjection': {'priceData': []},
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

                if sel_status == 'WINNER' or finish == 1:
                    outcome = 'win'
                elif finish in (2, 3):
                    outcome = 'placed'
                elif sel_status in ('LOSER', 'REMOVED') or finish > 3:
                    outcome = 'loss'
                else:
                    print(f"  {pick.get('horse')}: sel_id={pick_sel} not found in book (may have been a non-runner)")
                    continue

                dynamo_table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
                dynamo_table.update_item(
                    Key={'bet_id': pick['bet_id'], 'bet_date': pick['bet_date']},
                    UpdateExpression='SET outcome = :o, finish_position = :f, winner_horse = :w, result_recorded_at = :t',
                    ExpressionAttributeValues={
                        ':o': outcome,
                        ':f': finish,
                        ':w': winner_name,
                        ':t': now_utc.isoformat() + 'Z',
                    }
                )
                updated += 1
                results_summary.append({
                    'horse':   pick.get('horse'),
                    'course':  pick.get('course'),
                    'outcome': outcome,
                    'finish':  finish,
                    'winner':  winner_name,
                })
                print(f"  Recorded: {pick.get('horse')} @ {pick.get('course')} → {outcome} pos={finish} winner={winner_name}")

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

    score_gap = float(fav.get('score_gap') or 0)
    if 0 < score_gap < 10:
        flags['drift'] = True
        details.append(f'Low score gap ({score_gap:.0f}) — field competitive')
    elif score_gap == 0 and fav_score > 0:
        flags['drift'] = True
        details.append('Score gap = 0 — model does not separate favourite clearly')

    total = sum(_SCORE_WEIGHTS[f] for f in flags)
    return total, flags, details


def _verdict(score):
    if score >= 9:
        return 'STRONG LAY'
    elif score >= 4:
        return 'CAUTION'
    return 'LEAVE ALONE'


def _analyse_date_lambda(target_date_str, tbl):
    from boto3.dynamodb.conditions import Key as DKey
    resp = tbl.query(KeyConditionExpression=DKey('bet_date').eq(target_date_str))
    all_items = [_dec(it) for it in resp.get('Items', [])]
    if not all_items:
        return []

    races = {}
    for it in all_items:
        rt = str(it.get('race_time', ''))[:16]
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

        results.append({
            'date':          target_date_str,
            'race_time':     rt,
            'course':        course,
            'race_name':     race_name,
            'favourite':     fav.get('horse', '?'),
            'fav_odds':      fav_odds_dec,
            'fav_sys_score': float(fav.get('comprehensive_score') or fav.get('score', 0)),
            'score_gap':     float(fav.get('score_gap') or 0),
            'runners':       len(runners),
            'lay_score':     lay_score,
            'flags':         list(flags.keys()),
            'details':       details,
            'verdict':       verd,
            'form':          fav.get('form', ''),
            'trainer':       fav.get('trainer', ''),
            'jockey':        fav.get('jockey', ''),
            'our_pick':      fav.get('show_in_ui', False),
        })
    return results


def get_favs_run_lambda(headers, event):
    """GET /api/favs-run?days=N&date=YYYY-MM-DD"""
    try:
        qp = event.get('queryStringParameters') or {}
        today = datetime.now().strftime('%Y-%m-%d')
        target_date = qp.get('date', today)
        days = int(qp.get('days', 1))

        tbl = dynamodb.Table('SureBetBets')
        all_results = []
        for i in range(days):
            d = (datetime.strptime(target_date, '%Y-%m-%d') + timedelta(days=i)).strftime('%Y-%m-%d')
            all_results.extend(_analyse_date_lambda(d, tbl))

        caution = [r for r in all_results if r['lay_score'] >= 4]
        strong  = [r for r in all_results if r['lay_score'] >= 9]

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success':   True,
                'generated': datetime.now().isoformat(),
                'summary':   {'total': len(all_results), 'caution': len(caution), 'strong': len(strong)},
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

