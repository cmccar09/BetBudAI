"""
Betfair Results Fetcher
Fetches race results from Betfair API and updates picks in database
"""
import boto3
import json
import requests
from datetime import datetime, timedelta
from decimal import Decimal
import os

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Betfair API credentials
BETFAIR_USERNAME = os.getenv('BETFAIR_USERNAME', 'charlieobrien1981')
BETFAIR_APP_KEY = os.getenv('BETFAIR_APP_KEY', 'your_app_key')
BETFAIR_CERT_PATH = os.getenv('BETFAIR_CERT_PATH', 'client-2048.crt')
BETFAIR_KEY_PATH = os.getenv('BETFAIR_KEY_PATH', 'client-2048.key')

def get_session_token():
    """Login to Betfair and get session token"""
    try:
        # Read password from environment or config
        password = os.getenv('BETFAIR_PASSWORD')
        if not password:
            print("⚠️  BETFAIR_PASSWORD not set in environment")
            return None
        
        login_url = 'https://identitysso-cert.betfair.com/api/certlogin'
        
        headers = {
            'X-Application': BETFAIR_APP_KEY,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'username': BETFAIR_USERNAME,
            'password': password
        }
        
        # Check if cert files exist
        if not os.path.exists(BETFAIR_CERT_PATH) or not os.path.exists(BETFAIR_KEY_PATH):
            print(f"⚠️  Cert files not found: {BETFAIR_CERT_PATH}, {BETFAIR_KEY_PATH}")
            return None
        
        response = requests.post(
            login_url,
            data=data,
            headers=headers,
            cert=(BETFAIR_CERT_PATH, BETFAIR_KEY_PATH)
        )
        
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get('loginStatus') == 'SUCCESS':
                return resp_json.get('sessionToken')
        
        print(f"❌ Login failed: {response.text}")
        return None
    
    except Exception as e:
        print(f"❌ Error getting session token: {e}")
        return None

def get_market_results(market_ids, session_token):
    """Get results for specific markets from Betfair"""
    
    url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/'
    
    headers = {
        'X-Application': BETFAIR_APP_KEY,
        'X-Authentication': session_token,
        'Content-Type': 'application/json'
    }
    
    data = {
        'marketIds': market_ids,
        'priceProjection': {
            'priceData': ['EX_BEST_OFFERS', 'SP_TRADED']
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API error: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error fetching market results: {e}")
        return None

def update_results_from_betfair(date_str=None):
    """Fetch results from Betfair and update picks"""
    
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n{'='*70}")
    print(f"BETFAIR RESULTS UPDATER - {date_str}")
    print(f"{'='*70}\n")
    
    # Get session token
    print("1. Logging in to Betfair...")
    session_token = get_session_token()
    
    if not session_token:
        print("   ❌ Failed to login - check credentials")
        return 0
    
    print("   ✅ Logged in successfully\n")
    
    # Get all picks for today that have market_id
    print("2. Fetching picks with Betfair market IDs...")
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='attribute_exists(market_id) AND attribute_not_exists(outcome)',
        ExpressionAttributeValues={':date': date_str}
    )
    
    picks = response.get('Items', [])
    print(f"   Found {len(picks)} picks without results\n")
    
    if not picks:
        print("   No picks need updating")
        return 0
    
    # Group picks by market_id
    market_picks = {}
    for pick in picks:
        market_id = pick.get('market_id')
        if market_id:
            if market_id not in market_picks:
                market_picks[market_id] = []
            market_picks[market_id].append(pick)
    
    print(f"3. Fetching results for {len(market_picks)} markets...\n")
    
    # Fetch results in batches (max 25 markets per request)
    market_ids = list(market_picks.keys())
    updated_count = 0
    
    for i in range(0, len(market_ids), 25):
        batch = market_ids[i:i+25]
        
        results = get_market_results(batch, session_token)
        
        if not results:
            continue
        
        # Process each market
        for market_data in results:
            market_id = market_data.get('marketId')
            status = market_data.get('status')
            
            # Only process closed/settled markets
            if status not in ['CLOSED', 'SETTLED']:
                continue
            
            runners = market_data.get('runners', [])
            
            # Find winner(s)
            winners = [r for r in runners if r.get('status') == 'WINNER']
            placed = [r for r in runners if r.get('status') == 'PLACED']
            
            # Update picks for this market
            for pick in market_picks.get(market_id, []):
                selection_id = pick.get('selection_id')
                
                if not selection_id:
                    continue
                
                # Find this selection's result
                outcome = None
                finishing_position = None
                
                for idx, runner in enumerate(runners, 1):
                    if str(runner.get('selectionId')) == str(selection_id):
                        if runner.get('status') == 'WINNER':
                            outcome = 'win'
                            finishing_position = 1
                        elif runner.get('status') == 'PLACED':
                            outcome = 'placed'
                            finishing_position = idx
                        elif runner.get('status') == 'LOSER':
                            outcome = 'loss'
                            finishing_position = idx
                        # Extract SP: prefer sp.actualSP, fall back to lastPriceTraded
                        sp_data = runner.get('sp', {})
                        sp_actual = sp_data.get('actualSP') if sp_data else None
                        sp_odds = sp_actual or runner.get('lastPriceTraded')
                        break
                
                if outcome:
                    stake = float(pick.get('stake', 6.0))
                    # Use SP for P&L if we have it, fall back to stored pick odds
                    settlement_odds = float(sp_odds) if sp_odds else float(pick.get('odds', 0))
                    if outcome == 'win':
                        profit = round(stake * (settlement_odds - 1), 2)
                    elif outcome == 'placed':
                        ef = float(pick.get('ew_fraction', 0.25))
                        profit = round((stake / 2) * (1 + (settlement_odds - 1) * ef) - stake, 2)
                    else:
                        profit = round(-stake, 2)

                    # Update the database
                    try:
                        update_expr = 'SET outcome = :outcome, finishing_position = :pos, result_source = :source, result_updated = :updated, profit = :profit'
                        expr_vals = {
                            ':outcome': outcome,
                            ':pos': Decimal(finishing_position) if finishing_position else None,
                            ':source': 'betfair',
                            ':updated': datetime.now().isoformat(),
                            ':profit': Decimal(str(profit)),
                        }
                        if sp_odds:
                            update_expr += ', sp_odds = :sp'
                            expr_vals[':sp'] = Decimal(str(round(float(sp_odds), 2)))
                            # CLV (Closing Line Value) — compare our morning price to SP.
                            # Positive CLV = we got better odds than the market settled at.
                            # This is the gold standard long-term edge indicator:
                            # consistent +CLV means we are genuinely finding value, not luck.
                            # Source: Sharp Sports Betting, Betfair Exchange pricing research.
                            _opening = float(pick.get('opening_price') or pick.get('odds') or 0)
                            _sp_f    = float(sp_odds)
                            if _opening > 0 and _sp_f > 0:
                                _clv_delta = round(_opening - _sp_f, 3)
                                update_expr += ', clv_delta = :clv, clv_positive = :clvp'
                                expr_vals[':clv']  = Decimal(str(_clv_delta))
                                expr_vals[':clvp'] = _clv_delta > 0

                        table.update_item(
                            Key={'bet_date': date_str, 'bet_id': pick['bet_id']},
                            UpdateExpression=update_expr,
                            ExpressionAttributeValues=expr_vals
                        )
                        
                        horse = pick.get('horse', 'Unknown')
                        course = pick.get('course', 'Unknown')
                        result_icon = "✅" if outcome == 'win' else "🔶" if outcome == 'placed' else "❌"
                        sp_display = f" SP={settlement_odds}" if sp_odds else " (no SP, used pick odds)"
                        _clv_display = ''
                        if sp_odds:
                            _op = float(pick.get('opening_price') or pick.get('odds') or 0)
                            if _op > 0:
                                _clv = round(_op - float(sp_odds), 3)
                                _clv_display = f"  CLV={_clv:+.2f}({'✓' if _clv > 0 else '✗'})"
                        print(f"{result_icon} {horse:25} @ {course:15} | Pos: {finishing_position} | {outcome.upper()} | profit={profit:+.2f}{sp_display}{_clv_display}")
                        updated_count += 1
                    
                    except Exception as e:
                        print(f"❌ Error updating {pick.get('horse')}: {e}")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Results updated: {updated_count}")
    print(f"Source: Betfair API")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    return updated_count

if __name__ == '__main__':
    import sys
    
    date = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        updated = update_results_from_betfair(date)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
