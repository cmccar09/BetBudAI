#!/usr/bin/env python3
"""
Analyze why bets lost and whether we could have picked the actual winners
Compare our selections vs actual winners to improve future predictions
"""
import json
import requests
import boto3
from datetime import datetime, timedelta
from collections import defaultdict

# Load credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

# AWS DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("=" * 80)
print("LEARNING FROM LOSING BETS - Winner Analysis")
print("=" * 80)

# Step 1: Login to Betfair
print("\n[1/5] Logging in to Betfair...")
cert_url = "https://identitysso-cert.betfair.com/api/certlogin"

response = requests.post(
    cert_url,
    headers={
        'X-Application': creds['app_key'],
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    data={'username': creds['username'], 'password': creds['password']},
    cert=('betfair-client.crt', 'betfair-client.key'),
    timeout=10
)

if response.status_code == 200:
    result = response.json()
    login_status = result.get('loginStatus', result.get('status'))
    
    if login_status == 'SUCCESS':
        session_token = result.get('sessionToken')
        print(f"  [OK] Logged in")
    else:
        print(f"  [FAILED] {login_status}")
        exit(1)
else:
    print(f"  [FAILED] HTTP {response.status_code}")
    exit(1)

# Step 2: Get recent losing bets
print("\n[2/5] Loading recent losing bets...")
losing_bets = []

for days_ago in range(5):  # Last 5 days
    date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={':date': date}
    )
    
    items = response.get('Items', [])
    for item in items:
        if item.get('actual_result') == 'LOST' and item.get('market_id'):
            losing_bets.append(item)

print(f"  Found {len(losing_bets)} losing bets to analyze")

if not losing_bets:
    print("\n[OK] No losing bets to analyze")
    exit(0)

# Group by market to minimize API calls
markets_to_analyze = {}
for bet in losing_bets:
    market_id = bet.get('market_id')
    if market_id not in markets_to_analyze:
        markets_to_analyze[market_id] = {
            'our_bet': bet,
            'all_bets': [bet]
        }
    else:
        markets_to_analyze[market_id]['all_bets'].append(bet)

print(f"  Analyzing {len(markets_to_analyze)} unique races")

# Step 3: Fetch actual winners and full market data
print("\n[3/5] Fetching actual winners and market data...")

api_url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
headers = {
    'X-Application': creds['app_key'],
    'X-Authentication': session_token,
    'Content-Type': 'application/json'
}

learning_data = []

for i, (market_id, market_info) in enumerate(markets_to_analyze.items(), 1):
    our_bet = market_info['our_bet']
    venue = our_bet.get('course', 'Unknown')
    race_time = our_bet.get('race_time', '')[:16]
    race_type = our_bet.get('race_type', 'horse')
    
    print(f"\n  [{i}/{len(markets_to_analyze)}] {venue} - {race_time} ({race_type})")
    
    # Get market book with full data
    payload = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listMarketBook",
        "params": {
            "marketIds": [market_id],
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS", "EX_TRADED"],
                "virtualise": True
            }
        },
        "id": 1
    }
    
    try:
        api_response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        if api_response.status_code != 200:
            print(f"    [ERROR] HTTP {api_response.status_code}")
            continue
        
        api_result = api_response.json()
        
        if 'result' not in api_result or len(api_result['result']) == 0:
            print(f"    [NO DATA]")
            continue
        
        market_data = api_result['result'][0]
        runners = market_data.get('runners', [])
        
        if not runners:
            print(f"    [NO RUNNERS]")
            continue
        
        # Find the winner
        winner = None
        for runner in runners:
            if runner.get('status') == 'WINNER':
                winner = runner
                break
        
        if not winner:
            print(f"    [NO WINNER] Race might not be finished")
            continue
        
        winner_id = str(winner.get('selectionId'))
        
        # Get our selection
        our_selection_id = str(our_bet.get('selection_id'))
        our_horse = our_bet.get('horse', 'Unknown')
        our_confidence = float(our_bet.get('confidence', 0))
        our_odds = float(our_bet.get('odds', 0))
        our_p_win = float(our_bet.get('p_win', 0))
        
        # Find our runner in the market data
        our_runner = None
        for runner in runners:
            if str(runner.get('selectionId')) == our_selection_id:
                our_runner = runner
                break
        
        # Get winner's final odds
        winner_sp = winner.get('sp', {}).get('actualSP', 'N/A')
        winner_last_traded = winner.get('lastPriceTraded', 'N/A')
        
        # Get our horse's final position/odds
        our_sp = our_runner.get('sp', {}).get('actualSP', 'N/A') if our_runner else 'N/A'
        our_last_traded = our_runner.get('lastPriceTraded', 'N/A') if our_runner else 'N/A'
        
        print(f"    Winner: {winner_id} (SP: {winner_sp}, Last: {winner_last_traded})")
        print(f"    Our pick: {our_horse} (Conf: {our_confidence}%, Odds: {our_odds}, SP: {our_sp})")
        
        # Analyze: Could we have picked the winner?
        # Get all runners with their market data
        all_runners_data = []
        for runner in runners:
            runner_id = str(runner.get('selectionId'))
            runner_status = runner.get('status')
            runner_sp = runner.get('sp', {}).get('actualSP', 0)
            runner_last = runner.get('lastPriceTraded', 0)
            
            all_runners_data.append({
                'selection_id': runner_id,
                'status': runner_status,
                'sp': runner_sp,
                'last_traded': runner_last,
                'was_winner': runner_status == 'WINNER'
            })
        
        # Analysis: Compare winner's odds vs our selection
        analysis = {
            'market_id': market_id,
            'venue': venue,
            'race_time': race_time,
            'race_type': race_type,
            'our_selection': {
                'horse': our_horse,
                'selection_id': our_selection_id,
                'confidence': our_confidence,
                'odds': our_odds,
                'p_win': our_p_win,
                'final_sp': our_sp,
                'result': 'LOST'
            },
            'actual_winner': {
                'selection_id': winner_id,
                'final_sp': winner_sp,
                'last_traded': winner_last_traded
            },
            'all_runners': all_runners_data,
            'insights': []
        }
        
        # Key insight: Winner was better value than our pick?
        if isinstance(winner_sp, (int, float)) and isinstance(our_odds, (int, float)):
            if winner_sp < our_odds:
                analysis['insights'].append(
                    f"Winner was FAVORITE (SP {winner_sp}) vs our pick (odds {our_odds}). "
                    f"We picked outsider with {our_confidence}% confidence but favorite won."
                )
                print(f"    [INSIGHT] Favorite won, we picked outsider")
            else:
                analysis['insights'].append(
                    f"Winner was OUTSIDER (SP {winner_sp}) vs our pick (odds {our_odds}). "
                    f"Both were outsiders, winner had longer odds."
                )
                print(f"    [INSIGHT] Outsider won, hard to predict")
        
        # Check if we had high confidence but lost
        if our_confidence > 70:
            analysis['insights'].append(
                f"HIGH CONFIDENCE LOSS: We were {our_confidence}% confident but lost. "
                f"AI was overconfident."
            )
            print(f"    [INSIGHT] High confidence loss - AI overconfident")
        
        learning_data.append(analysis)
        
    except Exception as e:
        print(f"    [ERROR] {str(e)[:60]}")

# Step 4: Generate learning insights
print(f"\n[4/5] Generating learning insights from {len(learning_data)} races...")

insights_summary = {
    'timestamp': datetime.now().isoformat(),
    'races_analyzed': len(learning_data),
    'patterns': defaultdict(int),
    'recommendations': [],
    'detailed_analysis': learning_data
}

# Analyze patterns
favorites_won = 0
outsiders_won = 0
high_conf_losses = 0

for race in learning_data:
    for insight in race['insights']:
        if 'FAVORITE' in insight and 'favorite won' in insight.lower():
            favorites_won += 1
        if 'OUTSIDER' in insight and 'outsider won' in insight.lower():
            outsiders_won += 1
        if 'HIGH CONFIDENCE LOSS' in insight:
            high_conf_losses += 1

insights_summary['patterns']['favorites_won'] = favorites_won
insights_summary['patterns']['outsiders_won'] = outsiders_won
insights_summary['patterns']['high_confidence_losses'] = high_conf_losses

# Generate recommendations
if favorites_won > len(learning_data) * 0.6:
    insights_summary['recommendations'].append(
        "CRITICAL: Favorites winning more often than expected. "
        "Reduce outsider selections. Focus on horses with lower odds (favorites)."
    )

if high_conf_losses > len(learning_data) * 0.4:
    insights_summary['recommendations'].append(
        "CRITICAL: Too many high-confidence losses. "
        "AI is overconfident. Lower confidence scores by 20-30%."
    )

if outsiders_won > len(learning_data) * 0.5:
    insights_summary['recommendations'].append(
        "Pattern: Outsiders winning frequently. "
        "Market might be unpredictable. Increase required confidence threshold."
    )

# Step 5: Save insights
print("\n[5/5] Saving winner analysis...")

output_file = 'winner_analysis_insights.json'
with open(output_file, 'w') as f:
    json.dump(insights_summary, f, indent=2, default=str)

print(f"  [OK] Saved to: {output_file}")

# Print summary
print("\n" + "=" * 80)
print("WINNER ANALYSIS SUMMARY")
print("=" * 80)
print(f"Races analyzed: {len(learning_data)}")
print(f"Favorites won: {favorites_won} ({favorites_won/len(learning_data)*100:.1f}%)")
print(f"Outsiders won: {outsiders_won} ({outsiders_won/len(learning_data)*100:.1f}%)")
print(f"High confidence losses: {high_conf_losses} ({high_conf_losses/len(learning_data)*100:.1f}%)")
print("\nRECOMMENDATIONS:")
for i, rec in enumerate(insights_summary['recommendations'], 1):
    print(f"{i}. {rec}")
print("=" * 80)
