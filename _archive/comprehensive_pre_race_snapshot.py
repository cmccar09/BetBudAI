"""
COMPREHENSIVE PRE-RACE ANALYSIS SNAPSHOT
Captures complete state of all horses before races run
For later comparison with actual results
"""

import boto3
import json
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

def generate_comprehensive_snapshot():
    """Generate detailed pre-race snapshot for all horses"""
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n{'='*100}")
    print(f"COMPREHENSIVE PRE-RACE ANALYSIS SNAPSHOT - {today} at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*100}\n")
    
    # Get all analyzed horses for today
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={':date': today}
    )
    
    items = response.get('Items', [])
    
    # Filter only PRE_RACE_COMPLETE analyses
    pre_race_items = [i for i in items if i.get('analysis_type') == 'PRE_RACE_COMPLETE']
    
    print(f"Total horses with pre-race analysis: {len(pre_race_items)}")
    
    if not pre_race_items:
        print("\n⚠️  No pre-race analyses found. Run analyze_all_races_comprehensive.py first.")
        return
    
    # Sample one item to show what data we have
    sample = pre_race_items[0]
    print(f"\n{'='*100}")
    print("DATA FIELDS CAPTURED PER HORSE:")
    print(f"{'='*100}\n")
    
    fields = sorted(sample.keys())
    for field in fields:
        value = sample.get(field)
        if isinstance(value, dict):
            print(f"  {field}: [dict with {len(value)} keys]")
        elif isinstance(value, list):
            print(f"  {field}: [list with {len(value)} items]")
        else:
            print(f"  {field}: {type(value).__name__}")
    
    # Group by venue and race
    races = defaultdict(list)
    for item in pre_race_items:
        venue = item.get('venue', item.get('course', 'Unknown'))
        race_time = item.get('race_time', 'Unknown')
        race_key = f"{venue}_{race_time}"
        races[race_key].append(item)
    
    print(f"\n{'='*100}")
    print(f"RACES ANALYZED: {len(races)} races")
    print(f"{'='*100}\n")
    
    # Summary by venue
    venue_summary = defaultdict(lambda: {'races': 0, 'horses': 0})
    for race_key, horses in races.items():
        venue = race_key.split('_')[0]
        venue_summary[venue]['races'] += 1
        venue_summary[venue]['horses'] += len(horses)
    
    print("Breakdown by Venue:")
    for venue in sorted(venue_summary.keys()):
        stats = venue_summary[venue]
        print(f"  {venue:<20} {stats['races']} races, {stats['horses']} horses")
    
    # Detailed race breakdown
    print(f"\n{'='*100}")
    print("DETAILED RACE BREAKDOWN:")
    print(f"{'='*100}\n")
    
    sorted_races = sorted(races.items(), key=lambda x: x[1][0].get('race_time', ''))
    
    for race_key, horses in sorted_races:
        first_horse = horses[0]
        venue = first_horse.get('venue', first_horse.get('course', 'Unknown'))
        race_time = first_horse.get('race_time', 'Unknown')
        market_name = first_horse.get('market_name', 'Unknown')
        market_id = first_horse.get('market_id', 'Unknown')
        
        print(f"\n{venue} - {race_time}")
        print(f"  {market_name} | Market ID: {market_id}")
        print(f"  {len(horses)} runners analyzed\n")
        
        # Show top horses by odds (favorites)
        sorted_horses = sorted(horses, key=lambda x: float(x.get('odds', 999)))
        
        print("  Top 5 by odds (favorites):")
        for i, horse in enumerate(sorted_horses[:5], 1):
            name = horse.get('horse', 'Unknown')
            odds = float(horse.get('odds', 0))
            form = horse.get('form', 'N/A')
            trainer = horse.get('trainer', 'N/A')
            jockey = horse.get('jockey', 'N/A')
            
            print(f"    {i}. {name:<25} @ {odds:6.2f} | Form: {form:<8} | {trainer} / {jockey}")
    
    # Generate exportable snapshot
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'date': today,
        'total_horses': len(pre_race_items),
        'total_races': len(races),
        'venues': list(venue_summary.keys()),
        'races': []
    }
    
    for race_key, horses in sorted_races:
        race_data = {
            'venue': horses[0].get('venue', horses[0].get('course', 'Unknown')),
            'race_time': horses[0].get('race_time', 'Unknown'),
            'market_id': horses[0].get('market_id', 'Unknown'),
            'market_name': horses[0].get('market_name', 'Unknown'),
            'distance': horses[0].get('distance', 'Unknown'),
            'going': horses[0].get('going', 'Unknown'),
            'race_type': horses[0].get('race_type', 'Unknown'),
            'runners': []
        }
        
        for horse in sorted(horses, key=lambda x: float(x.get('odds', 999))):
            runner_data = {
                'name': horse.get('horse', 'Unknown'),
                'selection_id': horse.get('selection_id', 'Unknown'),
                'odds': float(horse.get('odds', 0)),
                'form': horse.get('form', ''),
                'trainer': horse.get('trainer', ''),
                'jockey': horse.get('jockey', ''),
                'weight': horse.get('weight', ''),
                'age': horse.get('age', ''),
                'days_since_run': horse.get('days_since_run', ''),
                'implied_probability': float(horse.get('implied_probability', 0)),
                'has_history': horse.get('has_history', False),
                'history_win_rate': float(horse.get('history_win_rate', 0)) if horse.get('history_win_rate') else 0,
            }
            race_data['runners'].append(runner_data)
        
        snapshot['races'].append(race_data)
    
    # Save snapshot to file
    snapshot_file = f'pre_race_snapshot_{today}_{datetime.now().strftime("%H%M")}.json'
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2, default=str)
    
    print(f"\n{'='*100}")
    print(f"✅ SNAPSHOT SAVED: {snapshot_file}")
    print(f"{'='*100}")
    print(f"\nThis snapshot captures the complete pre-race state of all {len(pre_race_items)} horses.")
    print("After races complete, compare with actual results to learn:")
    print("  • Which favorites won vs. upset winners")
    print("  • Form patterns that predicted winners")
    print("  • Trainer/jockey combinations that succeeded")
    print("  • Optimal odds ranges for value")
    print("  • Historical patterns that mattered")
    print(f"\n{'='*100}\n")
    
    return snapshot


if __name__ == "__main__":
    generate_comprehensive_snapshot()
