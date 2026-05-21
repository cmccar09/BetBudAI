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

        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',

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

        elif 'results/auto-record' in path:

            return auto_record_pending_results(headers)

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

        elif 'learning/apply' in path:

            return apply_learning_lambda(headers, event)

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



def _day_pick_cap(date_str):

    """Return 5 for Sat/Sun, 3 for Mon-Fri"""

    try:

        dow = datetime.strptime(date_str, '%Y-%m-%d').weekday()  # 0=Mon, 6=Sun

        return 5 if dow >= 5 else 3

    except Exception:

        return 5



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



    # Sort by score and limit by day-of-week cap (3 weekdays, 5 weekend)

    future_picks.sort(key=lambda x: float(x.get('comprehensive_score') or x.get('analysis_score') or 0), reverse=True)

    future_picks = future_picks[:_day_pick_cap(today)]

    # Re-sort capped picks by race time for display

    future_picks.sort(key=lambda x: x.get('race_time', ''))



    # Map reasons -> selection_reasons and analysis_breakdown -> score_breakdown for UI compatibility

    race_fields = {}

    for pick in future_picks:

        pick['selection_reasons'] = pick.get('reasons', [])
        pick['score_breakdown']   = pick.get('analysis_breakdown', pick.get('score_breakdown', {}))
        pick['score']             = float(pick.get('comprehensive_score') or pick.get('analysis_score') or pick.get('confidence') or 0)



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

    # Apply day-of-week cap: top 3 weekdays, top 5 weekend

    picks.sort(key=lambda x: float(x.get('comprehensive_score') or x.get('analysis_score') or 0), reverse=True)

    picks = picks[:_day_pick_cap(yesterday)]

    

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

    

    # £50 each-way per pick = £100 total stake per pick

    EW_LEG = 50.0

    def _ew_profit(p):

        win_odds = float(p.get('odds') or 0)

        oc = str(p.get('outcome', '')).upper()

        if win_odds <= 0:

            return 0.0

        place_div = (win_odds - 1) / 4.0 + 1  # 1/4 odds place terms

        if oc in ('WIN', 'WON'):

            return EW_LEG * win_odds + EW_LEG * place_div - EW_LEG * 2

        elif oc == 'PLACED':

            return EW_LEG * place_div - EW_LEG * 2

        elif oc in ('LOSS', 'LOST'):

            return -(EW_LEG * 2)

        return 0.0

    total_stake = len(resolved_picks) * EW_LEG * 2  # £1 per pick

    total_profit = sum(_ew_profit(p) for p in resolved_picks)

    total_return = round(total_stake + total_profit, 2)

    roi = round((total_profit / total_stake * 100), 1) if total_stake > 0 else 0

    

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

        _ew = 50.0

        def _sport_ew_profit(p):

            wo = float(p.get('odds') or 0)

            oc = str(p.get('outcome', '')).upper()

            if wo <= 0: return 0.0

            pd = (wo - 1) / 4.0 + 1

            if oc in ('WIN', 'WON'): return _ew * wo + _ew * pd - _ew * 2

            elif oc == 'PLACED': return _ew * pd - _ew * 2

            elif oc in ('LOSS', 'LOST'): return -(_ew * 2)

            return 0.0

        sport_stake = len(sport_resolved) * _ew * 2

        sport_profit = sum(_sport_ew_profit(p) for p in sport_resolved)

        sport_roi = round((sport_profit / sport_stake * 100), 1) if sport_stake > 0 else 0

        

        return {

            'total_picks': len(sport_picks),

            'wins': sport_wins,

            'places': sport_places,

            'losses': sport_losses,

            'pending': sport_pending,

            'total_stake': round(sport_stake, 2),

            'total_return': round(sport_stake + sport_profit, 2),

            'profit': round(sport_profit, 2),

            'roi': round(sport_roi, 1),

            'strike_rate': round((sport_wins / (sport_wins + sport_losses) * 100) if (sport_wins + sport_losses) > 0 else 0, 1)

        }

    


    # Attach winner_analysis to non-winning picks
    for pick in picks:
        oc = (pick.get('outcome') or '').lower()
        if oc in ('loss', 'placed'):
            pick['winner_analysis'] = compute_winner_analysis(pick)

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

                'total_return': round(total_stake + total_profit, 2),

                'profit': round(total_profit, 2),

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

    picks = picks[:_day_pick_cap(today)]

    print(f"After dedup + day-cap filter: {len(picks)} picks")



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





def to_fractional(decimal_odds):
    if not decimal_odds or float(decimal_odds) <= 1.0:
        return 'SP'
    d = float(decimal_odds)
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
    score_gap    = our_score - winner_score
    why_missed   = []
    weight_nudges = {}

    if not winner_horse:
        why_missed.append(f'Winner "{winner_name}" was not in our scored Betfair field — model could not see them')
        return {'winner_found': False, 'winner_score': 0, 'winner_rank': 0,
                'winner_odds': 0, 'score_gap': score_gap,
                'why_missed': why_missed, 'weight_nudges': weight_nudges}

    if winner_odds > 0 and our_odds > 0 and winner_odds < our_odds * 0.80:
        why_missed.append(
            f'Market disagreed: winner went off at {to_fractional(winner_odds)} '
            f'vs our pick at {to_fractional(our_odds)} — odds signal should have flagged this'
        )
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 1.0

    if score_gap > 15:
        why_missed.append(
            f'Model over-confidence: we scored {our_horse.title()} {our_score:.0f}/100 '
            f'vs {winner_name} {winner_score:.0f}/100 — {score_gap:.0f}pt gap too large'
        )

    if 0 < winner_rank <= 3 and score_gap <= 10:
        ord_suffix = 'st' if winner_rank == 1 else 'nd' if winner_rank == 2 else 'rd'
        why_missed.append(
            f'{winner_name} ranked {winner_rank}{ord_suffix} '
            f'in our model at {winner_score:.0f}/100 — narrow margin, pick was defensible'
        )

    if winner_rank > 5:
        why_missed.append(
            f'{winner_name} ranked {winner_rank}th of {len(sorted_field)} in our model '
            f'({winner_score:.0f}/100) — significant model blind spot'
        )

    going_pts = float(sb.get('going_suitability', 0))
    if going_pts > 0 and our_score > 0 and (going_pts / our_score) > 0.25:
        why_missed.append(
            f'Going suitability dominated our score ({going_pts:.0f}pts = '
            f'{going_pts/our_score*100:.0f}% of total) — may have been misleading'
        )
        weight_nudges['going_suitability'] = weight_nudges.get('going_suitability', 0) - 0.5

    cd_pts = float(sb.get('cd_bonus', 0)) + float(sb.get('course_performance', 0))
    if cd_pts > 20:
        why_missed.append(
            f'Course & distance bonus inflated score ({cd_pts:.0f}pts) — '
            f'winner may have had stronger recent form on the day'
        )
        weight_nudges['cd_bonus'] = weight_nudges.get('cd_bonus', 0) - 0.3

    if winner_score < our_score * 0.85:
        weight_nudges['recent_win'] = weight_nudges.get('recent_win', 0) + 0.5

    field_size = len(sorted_field)
    if field_size <= 5 and winner_odds > 0 and winner_odds < 2.5:
        why_missed.append(
            f'Small field ({field_size} runners) with a well-backed winner — '
            f'in small fields the market price is highly predictive'
        )
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 0.5

    # Why the winner won
    winner_sb = winner_horse.get('score_breakdown') or {}
    winner_reasons = []
    if winner_odds > 0 and our_odds > 0 and winner_odds < our_odds:
        winner_reasons.append(
            f'better market confidence ({to_fractional(winner_odds)} vs our pick at {to_fractional(our_odds)})'
        )
    w_form = float(winner_sb.get('form', 0) or winner_sb.get('form_score', 0) or winner_sb.get('recent_win', 0))
    o_form = float(sb.get('form', 0) or sb.get('form_score', 0) or sb.get('recent_win', 0))
    if w_form > o_form + 3:
        winner_reasons.append(f"stronger recent form score ({w_form:.0f}pts vs our pick's {o_form:.0f}pts)")
    w_cd = float(winner_sb.get('cd_bonus', 0) or winner_sb.get('course_performance', 0))
    o_cd = float(sb.get('cd_bonus', 0) or sb.get('course_performance', 0))
    if w_cd > o_cd + 5:
        winner_reasons.append(f"superior C&D record ({w_cd:.0f}pts vs our pick's {o_cd:.0f}pts)")
    w_going = float(winner_sb.get('going_suitability', 0))
    o_going = float(sb.get('going_suitability', 0))
    if w_going > o_going + 5:
        winner_reasons.append(f'better going suitability ({w_going:.0f}pts vs {o_going:.0f}pts)')
    w_tr = float(winner_sb.get('trainer_strike_rate', 0) or winner_sb.get('meeting_focus_trainer', 0))
    o_tr = float(sb.get('trainer_strike_rate', 0) or sb.get('meeting_focus_trainer', 0))
    if w_tr > o_tr + 5:
        winner_reasons.append(f"trainer in better form ({w_tr:.0f}pts vs our pick's {o_tr:.0f}pts)")

    if winner_reasons:
        why_missed.append(f'{winner_name} won on: {"; ".join(winner_reasons)}')
    elif winner_score > 0:
        why_missed.append(
            f'{winner_name} (scored {winner_score:.0f}/100, rank {winner_rank}) outperformed expectations on the day'
        )

    if not why_missed:
        why_missed.append(
            f'{winner_name} scored {winner_score:.0f}/100 (rank {winner_rank}) — result within normal variance'
        )

    return {
        'winner_found':   True,
        'winner_name':    winner_name,
        'winner_score':   int(winner_score),
        'winner_rank':    winner_rank,
        'winner_rank_of': len(sorted_field),
        'winner_odds':    winner_odds,
        'winner_odds_fractional': to_fractional(winner_odds) if winner_odds > 0 else '?',
        'score_gap':      round(score_gap, 1),
        'why_missed':     why_missed,
        'weight_nudges':  weight_nudges,
    }


def apply_learning_lambda(headers, event):
    import json as _json
    from datetime import timedelta
    from decimal import Decimal
    from boto3.dynamodb.conditions import Key

    method = (event.get('requestContext') or {}).get('http', {}).get('method', event.get('httpMethod', 'GET'))
    if method == 'OPTIONS':
        return {'statusCode': 204, 'headers': headers, 'body': ''}

    try:
        body = event.get('body') or '{}'
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        data = _json.loads(body) if body else {}
        target_date = data.get('date') or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        resp = table.query(KeyConditionExpression=Key('bet_date').eq(target_date))
        all_items = [decimal_to_float(i) for i in resp.get('Items', [])]

        picks = [p for p in all_items
                 if p.get('show_in_ui') == True
                 and p.get('result_winner_name')
                 and (p.get('outcome') or '').lower() in ('loss', 'placed')]

        if not picks:
            return {'statusCode': 200, 'headers': headers,
                    'body': _json.dumps({'success': True,
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
                'winner': wa.get('winner_name', '?'),
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
        return {'statusCode': 200, 'headers': headers, 'body': _json.dumps({
            'success': True, 'date': target_date, 'picks_analysed': len(picks),
            'changes': changes, 'races': race_summaries, 'message': msg,
        })}
    except Exception as e:
        return {'statusCode': 500, 'headers': headers,
                'body': _json.dumps({'success': False, 'error': str(e)})}
