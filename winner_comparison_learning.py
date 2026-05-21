#!/usr/bin/env python3
"""
Enhanced Winner Comparison Learning
For every race with a pick, analyze WHY the winner won and HOW to pick it next time
"""

import boto3
import json
import requests
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

def get_betfair_session():
    """Get Betfair session token"""
    try:
        with open('./betfair-creds.json', 'r') as f:
            creds = json.load(f)
        return creds.get('session_token'), creds.get('app_key')
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None, None

def fetch_race_winner(market_id, session_token, app_key):
    """Fetch the actual winner of a race from Betfair"""
    
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "marketIds": [market_id],
        "priceProjection": {
            "priceData": ["EX_BEST_OFFERS"]
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            markets = response.json()
            if markets and len(markets) > 0:
                market = markets[0]
                if market.get('status') == 'CLOSED':
                    # Find the winner
                    for runner in market.get('runners', []):
                        if runner.get('status') == 'WINNER':
                            return {
                                'selection_id': runner.get('selectionId'),
                                'sp': runner.get('sp', {}).get('nearPrice'),
                                'status': 'WINNER'
                            }
                    # Check for placed runners (for each-way analysis)
                    placed_runners = []
                    for runner in market.get('runners', []):
                        if runner.get('status') in ['WINNER', 'PLACED']:
                            placed_runners.append({
                                'selection_id': runner.get('selectionId'),
                                'sp': runner.get('sp', {}).get('nearPrice'),
                                'status': runner.get('status')
                            })
                    return {
                        'winner': [r for r in placed_runners if r['status'] == 'WINNER'][0] if placed_runners else None,
                        'placed': placed_runners
                    }
    except Exception as e:
        print(f"Error fetching winner for {market_id}: {e}")
    
    return None

def compare_pick_vs_winner(pick, winner_data, race_odds_snapshot):
    """
    Analyze what the winner had that our pick didn't
    Returns specific learnings about what to look for next time
    """
    
    learnings = []
    
    if not winner_data or not winner_data.get('winner'):
        return learnings
    
    winner_id = str(winner_data['winner']['selection_id'])
    our_id = str(pick.get('selection_id'))
    
    if winner_id == our_id:
        learnings.append({
            'type': 'SUCCESS',
            'lesson': f"Our pick WON! {pick['horse']} - analysis was correct"
        })
        return learnings
    
    # Find winner's details in odds snapshot
    winner_horse = None
    our_horse_data = None
    
    for horse in race_odds_snapshot.get('runners', []):
        if str(horse.get('selection_id')) == winner_id:
            winner_horse = horse
        if str(horse.get('selection_id')) == our_id:
            our_horse_data = horse
    
    if not winner_horse:
        return learnings
    
    # Compare odds
    winner_odds = winner_horse.get('odds', 0)
    our_odds = pick.get('odds', 0)
    
    if winner_odds < our_odds:
        diff = our_odds - winner_odds
        learnings.append({
            'type': 'ODDS_PREFERENCE',
            'lesson': f"Winner {winner_horse['name']} was {diff:.1f} points shorter ({winner_odds:.1f} vs {our_odds:.1f}). Market was right - should trust shorter prices more.",
            'action': f"When choosing between similar horses, favor the one {diff:.1f}+ points shorter if form is close"
        })
    elif winner_odds > our_odds * 1.5:
        learnings.append({
            'type': 'UPSET_RESULT',
            'lesson': f"Winner {winner_horse['name']} at {winner_odds:.1f} beat our pick at {our_odds:.1f}. Check what we missed.",
            'action': f"Review: {winner_horse.get('trainer', '')}, {winner_horse.get('jockey', '')}, course form, recent form"
        })
    
    # Compare form indicators
    winner_tags = winner_horse.get('form_tags', '').lower()
    our_tags = pick.get('tags', '').lower()
    
    # Check course form
    if 'c&d winner' in winner_tags and 'c&d winner' not in our_tags:
        learnings.append({
            'type': 'COURSE_FORM',
            'lesson': f"{winner_horse['name']} had course & distance form that we undervalued",
            'action': "BOOST weight for C&D winners - this is a proven edge"
        })
    elif 'course winner' in winner_tags and 'course winner' not in our_tags:
        learnings.append({
            'type': 'COURSE_FORM',
            'lesson': f"{winner_horse['name']} had course winning form",
            'action': "Course form is critical - don't overlook horses with track wins"
        })
    
    # Check trainer/jockey
    winner_trainer = winner_horse.get('trainer', '')
    winner_jockey = winner_horse.get('jockey', '')
    
    if winner_trainer and 'top trainer' in winner_tags:
        learnings.append({
            'type': 'TRAINER_EDGE',
            'lesson': f"Trainer {winner_trainer} won - may have better course record",
            'action': f"Check {winner_trainer}'s course strike rate for future races here"
        })
    
    # Check recent form
    if 'last time out winner' in winner_tags:
        learnings.append({
            'type': 'RECENT_FORM',
            'lesson': f"{winner_horse['name']} won last time out - strong current form",
            'action': "Last-time-out winners have momentum - weight this more heavily"
        })
    
    # Check ground suitability
    if 'ground specialist' in winner_tags:
        learnings.append({
            'type': 'GROUND',
            'lesson': f"{winner_horse['name']} had proven going preference",
            'action': "Ground suitability is non-negotiable - horses without it should be excluded"
        })
    
    # Class comparison
    our_confidence = pick.get('confidence', 0)
    if our_confidence > 70:
        learnings.append({
            'type': 'OVERCONFIDENCE',
            'lesson': f"We were {our_confidence}% confident but wrong",
            'action': "Calibration needed - reduce confidence when multiple viable contenders"
        })
    
    return learnings

def analyze_all_races_with_picks():
    """
    For every race where we made a pick:
    1. Get the actual winner
    2. Compare winner vs our pick
    3. Generate specific learnings
    4. Save to insights
    """
    
    print("="*70)
    print("WINNER COMPARISON LEARNING SYSTEM")
    print("="*70)
    
    # Get session
    session_token, app_key = get_betfair_session()
    if not session_token:
        print("❌ Failed to get Betfair session")
        return
    
    # Load picks without results
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    
    # Scan for picks from last 2 days without winner_analysis
    response = table.scan(
        FilterExpression='attribute_not_exists(winner_comparison) OR winner_comparison = :empty',
        ExpressionAttributeValues={':empty': ''}
    )
    
    picks = response.get('Items', [])
    print(f"\n Found {len(picks)} picks to analyze")
    
    all_learnings = []
    races_analyzed = 0
    
    # Group by market_id
    by_market = defaultdict(list)
    for pick in picks:
        market_id = pick.get('market_id')
        if market_id:
            by_market[market_id].append(pick)
    
    print(f"\nAnalyzing {len(by_market)} unique races...\n")
    
    for market_id, market_picks in by_market.items():
        print(f"Race: {market_picks[0].get('course', 'Unknown')} - {market_picks[0].get('race_time', '')}")
        
        # Fetch actual winner
        winner_data = fetch_race_winner(market_id, session_token, app_key)
        
        if not winner_data:
            print("  [PENDING] Race not complete yet or data unavailable")
            continue
        
        races_analyzed += 1
        
        # For each pick in this race, compare with winner
        for pick in market_picks:
            horse_name = pick.get('horse', 'Unknown')
            
            # Get race snapshot (would need to load from stored data)
            # For now, use pick data
            race_snapshot = {
                'runners': []  # Would load full field data here
            }
            
            learnings = compare_pick_vs_winner(pick, winner_data, race_snapshot)
            
            if learnings:
                print(f"  [ANALYSIS] {horse_name}:")
                for learning in learnings:
                    print(f"     → {learning['lesson']}")
                    if 'action' in learning:
                        print(f"       Action: {learning['action']}")
                
                all_learnings.extend(learnings)
                
                # Save winner comparison to DynamoDB
                try:
                    table.update_item(
                        Key={
                            'bet_date': pick['bet_date'],
                            'bet_id': pick['bet_id']
                        },
                        UpdateExpression='SET winner_comparison = :analysis, winner_id = :wid',
                        ExpressionAttributeValues={
                            ':analysis': json.dumps([l for l in learnings], default=str),
                            ':wid': str(winner_data.get('winner', {}).get('selection_id', ''))
                        }
                    )
                except Exception as e:
                    print(f"     ⚠️  Error saving analysis: {e}")
        
        print()
    
    # Generate consolidated insights
    print("="*70)
    print(f"ANALYSIS COMPLETE: {races_analyzed} races analyzed")
    print("="*70)
    
    # Categorize learnings
    insights = {
        'total_races': races_analyzed,
        'total_learnings': len(all_learnings),
        'by_type': defaultdict(list),
        'top_actions': [],
        'updated': datetime.utcnow().isoformat()
    }
    
    for learning in all_learnings:
        insights['by_type'][learning['type']].append(learning)
    
    # Print summary
    print("\nKey Insights:")
    for category, items in insights['by_type'].items():
        print(f"\n{category} ({len(items)} instances):")
        for item in items[:3]:  # Top 3 per category
            print(f"  • {item['lesson']}")
            if 'action' in item:
                print(f"    → {item['action']}")
    
    # Save to S3
    try:
        s3 = boto3.client('s3', region_name='eu-west-1')
        s3.put_object(
            Bucket='surebet-betting-data',
            Key='betting-insights/winner_comparison_learnings.json',
            Body=json.dumps(insights, indent=2, default=str),
            ContentType='application/json'
        )
        print(f"\n[OK] Saved insights to S3: surebet-betting-data/betting-insights/winner_comparison_learnings.json")
    except Exception as e:
        print(f"\n[X] Error saving to S3: {e}")
    
    print("="*70)
    
    return insights

if __name__ == "__main__":
    analyze_all_races_with_picks()
