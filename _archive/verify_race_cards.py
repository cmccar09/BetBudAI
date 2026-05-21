"""
Complete Race Card Verification
Check all races have full runner cards saved
"""
import json
import boto3
from collections import defaultdict

print("\n" + "="*80)
print("RACE CARD COMPLETENESS VERIFICATION")
print("="*80 + "\n")

# Load race data from file
try:
    with open('response_horses.json', 'r') as f:
        data = json.load(f)
    
    races = data.get('races', [])
    print(f"Total races in response_horses.json: {len(races)}\n")
    
    print(f"{'Venue':<20} {'Time':<10} {'Market':<30} {'Runners':<8}")
    print("-" * 80)
    
    race_summary = []
    issues = []
    
    for race in races:
        venue = race.get('venue', 'Unknown')[:20]
        start_time = race.get('start_time', '')[:16].split('T')[-1]
        market_name = race.get('market_name', 'Unknown')[:30]
        runners = race.get('runners', [])
        runner_count = len(runners)
        
        print(f"{venue:<20} {start_time:<10} {market_name:<30} {runner_count:<8}")
        
        race_summary.append({
            'venue': venue,
            'time': start_time,
            'market': market_name,
            'runners': runner_count
        })
        
        # Flag suspicious races
        if runner_count < 4:
            issues.append({
                'race': f"{venue} {start_time}",
                'issue': f"Only {runner_count} runners (suspicious)",
                'market': market_name
            })
        elif runner_count > 30:
            issues.append({
                'race': f"{venue} {start_time}",
                'issue': f"{runner_count} runners (unusually high)",
                'market': market_name
            })
    
    print("\n" + "="*80)
    print("POTENTIAL ISSUES:")
    print("="*80 + "\n")
    
    if issues:
        for issue in issues:
            print(f"⚠️ {issue['race']}: {issue['issue']}")
            print(f"   Market: {issue['market']}\n")
    else:
        print("✓ No obvious runner count issues detected")
    
    # Check Carlisle races specifically
    print("\n" + "="*80)
    print("CARLISLE RACES DETAIL:")
    print("="*80 + "\n")
    
    carlisle_races = [r for r in races if 'Carlisle' in r.get('venue', '')]
    
    for race in carlisle_races:
        start_time = race.get('start_time', '')
        market_name = race.get('market_name', '')
        runners = race.get('runners', [])
        
        print(f"Race: {start_time}")
        print(f"Market: {market_name}")
        print(f"Runners: {len(runners)}")
        print("Horse names:")
        for i, runner in enumerate(runners, 1):
            name = runner.get('name', 'Unknown')
            odds = runner.get('odds', 0)
            form = runner.get('form', '')
            print(f"  {i:2d}. {name:<30} @ {odds:6.1f}  Form: {form}")
        print()
    
    # Check Fairyhouse races
    print("\n" + "="*80)
    print("FAIRYHOUSE RACES DETAIL:")
    print("="*80 + "\n")
    
    fairyhouse_races = [r for r in races if 'Fairyhouse' in r.get('venue', '')]
    
    for race in fairyhouse_races:
        start_time = race.get('start_time', '')
        market_name = race.get('market_name', '')
        runners = race.get('runners', [])
        
        print(f"Race: {start_time}")
        print(f"Market: {market_name}")
        print(f"Runners: {len(runners)}")
        print("Horse names:")
        for i, runner in enumerate(runners, 1):
            name = runner.get('name', 'Unknown')
            odds = runner.get('odds', 0)
            form = runner.get('form', '')
            print(f"  {i:2d}. {name:<30} @ {odds:6.1f}  Form: {form}")
        print()
        
except FileNotFoundError:
    print("❌ response_horses.json not found")
    exit(1)
except Exception as e:
    print(f"❌ Error reading file: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Check database
print("\n" + "="*80)
print("DATABASE VERIFICATION:")
print("="*80 + "\n")

try:
    db = boto3.resource('dynamodb', region_name='eu-west-1')
    table = db.Table('SureBetBets')
    
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        ExpressionAttributeValues={':date': '2026-02-03'}
    )
    
    items = response['Items']
    print(f"Total items in database for 2026-02-03: {len(items)}\n")
    
    # Group by venue and race time
    by_race = defaultdict(list)
    
    for item in items:
        venue = item.get('course', 'Unknown')
        race_time = item.get('race_time', 'Unknown')
        race_key = f"{venue} {race_time}"
        by_race[race_key].append(item)
    
    print(f"Unique races in database: {len(by_race)}\n")
    
    print(f"{'Race':<40} {'Horses in DB':<15}")
    print("-" * 60)
    
    for race_key in sorted(by_race.keys()):
        horses = by_race[race_key]
        print(f"{race_key:<40} {len(horses):<15}")
    
    # Check specific problem races
    print("\n" + "="*80)
    print("PROBLEM RACE INVESTIGATION:")
    print("="*80 + "\n")
    
    # Carlisle 14:00
    carlisle_14 = [item for item in items if 'Carlisle' in item.get('course', '') and '14:' in item.get('race_time', '')]
    
    print(f"Carlisle ~14:00 horses in database: {len(carlisle_14)}")
    if carlisle_14:
        print("Horses:")
        for item in sorted(carlisle_14, key=lambda x: float(x.get('confidence', 0)), reverse=True)[:10]:
            horse = item.get('horse', 'Unknown')
            odds = float(item.get('odds', 0))
            score = float(item.get('confidence', 0))
            ui = item.get('show_in_ui', False)
            status = "[UI]" if ui else "[Learning]"
            print(f"  {status} {horse:<30} @ {odds:6.1f}  Score: {score:5.1f}")
    
    # Fairyhouse 13:50
    fairyhouse_13 = [item for item in items if 'Fairyhouse' in item.get('course', '') and '13:' in item.get('race_time', '')]
    
    print(f"\nFairyhouse ~13:50 horses in database: {len(fairyhouse_13)}")
    if fairyhouse_13:
        print("Horses:")
        for item in sorted(fairyhouse_13, key=lambda x: float(x.get('confidence', 0)), reverse=True)[:10]:
            horse = item.get('horse', 'Unknown')
            odds = float(item.get('odds', 0))
            score = float(item.get('confidence', 0))
            ui = item.get('show_in_ui', False)
            status = "[UI]" if ui else "[Learning]"
            print(f"  {status} {horse:<30} @ {odds:6.1f}  Score: {score:5.1f}")
    
    print("\n" + "="*80)
    print("DIAGNOSIS:")
    print("="*80 + "\n")
    
    # Check if file data matches database
    print("Comparing response_horses.json with database...")
    
    file_horses = sum(len(r.get('runners', [])) for r in races)
    db_horses = len(items)
    
    print(f"\nHorses in response_horses.json: {file_horses}")
    print(f"Horses in database: {db_horses}")
    
    if file_horses == db_horses:
        print("\n✓ Database matches file - ALL horses were saved")
        print("\n🔴 CONCLUSION: The problem is in data CAPTURE, not storage")
        print("   betfair_odds_fetcher.py is not getting complete markets")
    elif db_horses < file_horses:
        print(f"\n⚠️ Database has FEWER horses ({db_horses}) than file ({file_horses})")
        print("   Some horses not being saved to database")
    else:
        print(f"\n⚠️ Database has MORE horses ({db_horses}) than file ({file_horses})")
        print("   Possible duplicate entries or old data")
        
except Exception as e:
    print(f"❌ Database error: {e}")
    import traceback
    traceback.print_exc()
