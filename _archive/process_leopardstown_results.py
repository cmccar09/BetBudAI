"""
Leopardstown Results Learning Script
Compares actual race results with our pre-race analysis to identify patterns
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

# Initialize DynamoDB
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

def process_race_result(race_time, winner_name, placed_horses=None, all_finishers=None):
    """
    Process a single race result and compare with our analysis
    
    Args:
        race_time: str - Race time like "14:25" or "2026-02-02T14:25:00.000Z"
        winner_name: str - Name of winning horse
        placed_horses: list - Names of horses that placed (2nd, 3rd, etc.)
        all_finishers: dict - Complete finishing order {position: horse_name}
    """
    
    print(f"\n{'='*80}")
    print(f"PROCESSING RACE RESULT: {race_time}")
    print(f"{'='*80}")
    
    # Normalize race time
    if 'T' not in race_time:
        race_time = f"2026-02-02T{race_time}:00.000Z"
    
    # Query database for our pre-race analysis
    response = table.scan(
        FilterExpression='analysis_type = :type AND race_time = :time',
        ExpressionAttributeValues={
            ':type': 'PRE_RACE_COMPLETE',
            ':time': race_time
        }
    )
    
    analyses = response.get('Items', [])
    
    if not analyses:
        print(f"⚠️  No pre-race analysis found for {race_time}")
        return None
    
    print(f"✓ Found {len(analyses)} horses in our pre-race analysis\n")
    
    # Find winner's analysis
    winner_analysis = None
    for a in analyses:
        if a['horse'].lower() == winner_name.lower():
            winner_analysis = a
            break
    
    if not winner_analysis:
        print(f"❌ Winner '{winner_name}' not found in our analysis!")
        print(f"Available horses: {[a['horse'] for a in analyses]}")
        return None
    
    # Analyze what we got right/wrong
    learning = {
        'bet_id': f'LEARNING_{race_time.replace(":", "").replace(".", "").replace("Z", "").replace("T", "_")}',
        'bet_date': '2026-02-02',
        'learning_type': 'RACE_RESULT_ANALYSIS',
        'venue': 'Leopardstown',
        'race_time': race_time,
        'analyzed_at': datetime.now().isoformat(),
        
        # Winner details
        'winner': winner_name,
        'winner_odds': winner_analysis['odds'],
        'winner_form': winner_analysis.get('form', 'Unknown'),
        'winner_trainer': winner_analysis.get('trainer', 'Unknown'),
        'winner_position_in_odds': 0,  # Will calculate
        
        # Analysis insights
        'total_runners': len(analyses),
        'favorite_won': False,
        'insights': []
    }
    
    # Sort by odds to find favorite
    sorted_by_odds = sorted(analyses, key=lambda x: float(x['odds']) if x['odds'] else 999)
    
    # Calculate winner's position in betting
    for idx, horse in enumerate(sorted_by_odds, 1):
        if horse['horse'] == winner_name:
            learning['winner_position_in_odds'] = idx
            break
    
    learning['favorite_won'] = (learning['winner_position_in_odds'] == 1)
    
    print(f"🏆 WINNER: {winner_name}")
    print(f"   Odds: {winner_analysis['odds']}")
    print(f"   Form: {winner_analysis.get('form', 'Unknown')}")
    print(f"   Trainer: {winner_analysis.get('trainer', 'Unknown')}")
    print(f"   Position in betting: {learning['winner_position_in_odds']} of {len(analyses)}")
    print(f"   Favorite won: {'YES' if learning['favorite_won'] else 'NO'}")
    
    # Analyze form patterns
    winner_form = winner_analysis.get('form', '')
    if winner_form and winner_form != 'Unknown':
        if '1' in winner_form[:3]:  # Win in last 3 runs
            learning['insights'].append('Winner had recent win in form (1 in last 3)')
        if winner_form[0] == '1':
            learning['insights'].append('Winner won last race (LTO winner)')
        if winner_form.count('1') >= 2:
            learning['insights'].append(f'Winner had {winner_form.count("1")} wins in recent form')
    
    # Odds analysis
    winner_odds = float(winner_analysis['odds'])
    if winner_odds >= 3.0 and winner_odds <= 9.0:
        learning['insights'].append('Winner was in SWEET SPOT odds (3.0-9.0)')
    elif winner_odds < 3.0:
        learning['insights'].append('Winner was favorite/short-priced (< 3.0 odds)')
    elif winner_odds > 15.0:
        learning['insights'].append(f'Winner was LONGSHOT ({winner_odds} odds)')
    else:
        learning['insights'].append(f'Winner was outside sweet spot ({winner_odds} odds)')
    
    # Compare with placed horses if provided
    if placed_horses:
        learning['placed_horses'] = []
        for place_num, horse_name in enumerate(placed_horses, 2):
            for a in analyses:
                if a['horse'].lower() == horse_name.lower():
                    learning['placed_horses'].append({
                        'position': place_num,
                        'name': horse_name,
                        'odds': a['odds'],
                        'form': a.get('form', 'Unknown')
                    })
                    break
    
    # Generate specific learnings
    print(f"\n📚 KEY LEARNINGS:")
    for idx, insight in enumerate(learning['insights'], 1):
        print(f"   {idx}. {insight}")
    
    # Save learning to database
    learning_decimal = convert_to_decimal(learning)
    table.put_item(Item=learning_decimal)
    print(f"\n✅ Learning saved to database")
    
    return learning

def convert_to_decimal(obj):
    """Recursively convert floats to Decimal for DynamoDB"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_decimal(item) for item in obj]
    else:
        return obj

def quick_result_entry():
    """Interactive mode for entering results"""
    
    print(f"\n{'='*80}")
    print("LEOPARDSTOWN RESULTS ENTRY")
    print(f"{'='*80}\n")
    
    races = [
        ("14:25", "21 runners"),
        ("14:55", "3 runners"),
        ("15:30", "12 runners - Feature race"),
        ("16:05", "14 runners"),
        ("16:40", "7 runners")
    ]
    
    print("Today's Leopardstown races:")
    for i, (time, info) in enumerate(races, 1):
        print(f"  {i}. {time} - {info}")
    
    print(f"\n{'='*80}")
    print("EXAMPLE USAGE:")
    print("  process_race_result('14:25', 'County Final')")
    print("  process_race_result('14:55', 'Romeo Coolio', placed_horses=['Kargese', 'Downmexicoway'])")
    print(f"{'='*80}\n")

def analyze_all_results(results):
    """
    Batch process multiple race results
    
    Args:
        results: list of dicts with keys 'race_time', 'winner', 'placed' (optional)
    """
    
    all_learnings = []
    
    for result in results:
        learning = process_race_result(
            result['race_time'],
            result['winner'],
            result.get('placed', [])
        )
        if learning:
            all_learnings.append(learning)
    
    # Generate summary report
    print(f"\n{'='*80}")
    print("SUMMARY OF ALL RESULTS")
    print(f"{'='*80}\n")
    
    favorites_won = sum(1 for l in all_learnings if l.get('favorite_won', False))
    sweet_spot_wins = sum(1 for l in all_learnings 
                          if any('SWEET SPOT' in i for i in l.get('insights', [])))
    longshot_wins = sum(1 for l in all_learnings 
                       if any('LONGSHOT' in i for i in l.get('insights', [])))
    
    print(f"Total races analyzed: {len(all_learnings)}")
    print(f"Favorites won: {favorites_won}/{len(all_learnings)} ({100*favorites_won/len(all_learnings):.1f}%)")
    print(f"Sweet spot winners (3-9 odds): {sweet_spot_wins}/{len(all_learnings)}")
    print(f"Longshot winners (15+ odds): {longshot_wins}/{len(all_learnings)}")
    
    print(f"\n{'='*80}\n")
    
    return all_learnings

if __name__ == "__main__":
    quick_result_entry()
    
    # Example: Uncomment and modify with actual results
    # process_race_result('14:25', 'County Final')
