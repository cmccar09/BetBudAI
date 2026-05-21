"""
AWS Lambda function to serve betting picks from DynamoDB
Provides REST API for frontend hosted on Amplify
"""
import json
import boto3
from datetime import datetime
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
    
    # Get path - handle both API Gateway and Lambda URL formats
    path = event.get('rawPath', event.get('path', ''))
    method = event.get('requestContext', {}).get('http', {}).get('method', event.get('httpMethod', 'GET'))
    
    print(f"Request: {method} {path}")
    print(f"Event keys: {event.keys()}")
    print(f"Path check - 'workflow/run' in path: {'workflow/run' in path}")
    
    try:
        # Route requests - check more specific paths first
        if 'results/today' in path or path.endswith('/results'):
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
    
    # Filter out greyhounds - only show horses
    horse_items = [item for item in items if item.get('sport', 'horses') == 'horses']
    
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
    
    # Sort by race time ascending (earliest races first)
    future_picks.sort(key=lambda x: x.get('race_time', ''))
    
    print(f"Total picks: {len(items)}, Horse picks: {len(horse_items)}, Future picks: {len(future_picks)}")
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'success': True,
            'picks': future_picks,
            'count': len(future_picks),
            'date': today
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
    """Get yesterday's picks with results"""
    from datetime import timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Check both 'date' and 'bet_date' fields (schema evolved)
    response = table.scan(
        FilterExpression='#d = :yesterday OR bet_date = :yesterday',
        ExpressionAttributeNames={'#d': 'date'},
        ExpressionAttributeValues={':yesterday': yesterday}
    )
    
    items = response.get('Items', [])
    items = [decimal_to_float(item) for item in items]
    
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

def check_today_results(headers):
    """Check results for today's picks - ALL picks separated by sport"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get ALL today's picks
    response = table.scan(
        FilterExpression='#d = :today',
        ExpressionAttributeNames={'#d': 'date'},
        ExpressionAttributeValues={':today': today}
    )
    
    all_picks = response.get('Items', [])
    all_picks = [decimal_to_float(item) for item in all_picks]
    
    # No filtering - use ALL picks
    picks = all_picks
    
    # Debug logging
    print(f"Total picks retrieved: {len(picks)}")
    
    if not picks:
        print("NO PICKS for today - returning empty")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': f'No picks for today',
                'date': today,
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
    
    # Calculate overall stats from existing outcomes
    wins = sum(1 for p in picks if p.get('outcome') == 'win')
    places = sum(1 for p in picks if p.get('outcome') == 'placed')
    losses = sum(1 for p in picks if p.get('outcome') == 'loss')
    pending = sum(1 for p in picks if p.get('outcome') in ['pending', None])
    
    total_stake = sum(float(p.get('stake', 2.0)) for p in picks)
    
    # Calculate returns based on outcomes
    total_return = 0
    for p in picks:
        outcome = p.get('outcome')
        if outcome == 'win':
            stake = float(p.get('stake', 2.0))
            odds = float(p.get('odds', 0))
            bet_type = p.get('bet_type', 'WIN').upper()
            if bet_type == 'WIN':
                total_return += stake * odds
            else:  # EW
                ew_fraction = float(p.get('ew_fraction', 0.2))
                total_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
        elif outcome == 'placed':
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
        
        sport_wins = sum(1 for p in sport_picks if p.get('outcome') == 'win')
        sport_places = sum(1 for p in sport_picks if p.get('outcome') == 'placed')
        sport_losses = sum(1 for p in sport_picks if p.get('outcome') == 'loss')
        sport_pending = sum(1 for p in sport_picks if p.get('outcome') in ['pending', None])
        sport_stake = sum(float(p.get('stake', 2.0)) for p in sport_picks)
        
        # Calculate returns for this sport
        sport_return = 0
        for p in sport_picks:
            if p.get('outcome') == 'win':
                stake = float(p.get('stake', 2.0))
                odds = float(p.get('odds', 0))
                bet_type = p.get('bet_type', 'WIN').upper()
                if bet_type == 'WIN':
                    sport_return += stake * odds
                else:  # EW
                    ew_fraction = float(p.get('ew_fraction', 0.2))
                    sport_return += (stake/2) * odds + (stake/2) * (1 + (odds-1) * ew_fraction)
            elif p.get('outcome') == 'placed':
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

def trigger_workflow(headers):
    """Trigger the betting workflow Lambda to generate new picks"""
    import boto3
    
    lambda_client = boto3.client('lambda', region_name='eu-west-1')
    
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

