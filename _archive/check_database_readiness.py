"""
Check all horses in eu-west-1 database and verify confidence scores
Focus on Carlisle 14:00 (next race)
Also analyze Fairyhouse 13:50 result (Harwa won at 10/3)
"""
import boto3
import json
from datetime import datetime

# Always use eu-west-1
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("=" * 100)
print("DATABASE READINESS CHECK - eu-west-1")
print("=" * 100)

# Get all today's data
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

items = response.get('Items', [])
print(f"\nTotal items for 2026-02-03: {len(items)}")

# Group by course and race_time
races = {}
for item in items:
    course = item.get('course', 'Unknown')
    race_time = item.get('race_time', 'Unknown')
    key = f"{course} {race_time}"
    
    if key not in races:
        races[key] = []
    races[key].append(item)

print(f"\nTotal races found: {len(races)}")

# Sort by time
sorted_races = sorted(races.items(), key=lambda x: x[0])

print("\n" + "=" * 100)
print("ALL RACES IN DATABASE")
print("=" * 100)

for race_key, horses in sorted_races:
    course, race_time = race_key.split(' ', 1)
    
    # Count horses with confidence scores (convert to float)
    with_scores = sum(1 for h in horses if float(h.get('confidence', 0)) > 0)
    avg_confidence = sum(float(h.get('confidence', 0)) for h in horses) / len(horses) if horses else 0
    
    print(f"\n{race_key}")
    print(f"  Runners: {len(horses)}")
    print(f"  With confidence scores: {with_scores}/{len(horses)}")
    print(f"  Average confidence: {avg_confidence:.1f}/100")
    
    # Show top 3 horses by confidence
    if horses:
        sorted_horses = sorted(horses, key=lambda x: float(x.get('confidence', 0)), reverse=True)
        print(f"  Top picks:")
        for i, h in enumerate(sorted_horses[:3], 1):
            horse_name = h.get('horse', 'Unknown')
            conf = float(h.get('confidence', 0))
            odds = float(h.get('odds', 0))
            print(f"    {i}. {horse_name:<30} Conf: {conf:3}/100  Odds: {odds:6.2f}")

# Focus on Carlisle 14:00
print("\n" + "=" * 100)
print("CARLISLE 14:00 - DETAILED CHECK")
print("=" * 100)

carlisle_1400 = [item for item in items if item.get('course') == 'Carlisle' and '14:00' in item.get('race_time', '')]

if carlisle_1400:
    print(f"\n✓ Found {len(carlisle_1400)} horses for Carlisle 14:00")
    
    print(f"\n{'Horse':<30} {'Confidence':<12} {'Odds':<8} {'Value':<7} {'Form':<15}")
    print("-" * 100)
    
    for item in sorted(carlisle_1400, key=lambda x: float(x.get('confidence', 0)), reverse=True):
        horse = item.get('horse', '')
        conf = float(item.get('confidence', 0))
        odds = float(item.get('odds', 0))
        form = item.get('form', '')[:15]
        
        # Get value score if available
        value_score = 0
        all_horses = item.get('all_horses_analyzed', {})
        if all_horses:
            value_analysis = all_horses.get('value_analysis', [])
            for runner in value_analysis:
                if runner.get('runner_name') == horse:
                    value_score = runner.get('value_score', 0)
                    break
        
        status = "✓" if conf > 0 else "✗"
        print(f"{status} {horse:<30} {conf:3}/100      {odds:6.2f}  {value_score}/10   {form:<15}")
    
    # Check if any horse meets our criteria
    print("\n" + "-" * 100)
    print("PICKS ANALYSIS:")
    
    high_conf = [h for h in carlisle_1400 if float(h.get('confidence', 0)) >= 45]
    if high_conf:
        print(f"\n✓ {len(high_conf)} horses meet threshold (>=45):")
        for h in high_conf:
            print(f"  - {h.get('horse')} ({float(h.get('confidence', 0))}/100)")
    else:
        print("\n⚠ No horses meet standard threshold (45/100)")
        
        # Check for high value recent winners
        print("\nChecking for HIGH VALUE RECENT WINNER candidates...")
        for item in carlisle_1400:
            tags = item.get('tags', [])
            all_horses = item.get('all_horses_analyzed', {})
            
            if all_horses:
                value_analysis = all_horses.get('value_analysis', [])
                for runner in value_analysis:
                    if runner.get('runner_name') == item.get('horse'):
                        value_score = int(runner.get('value_score', 0))
                        edge = float(runner.get('edge_percentage', 0))
                        
                        if value_score >= 9 and 'Recent winner' in tags and edge >= 25:
                            print(f"  ✓✓ {item.get('horse')} - Value: {value_score}/10, Edge: {edge}%")
                            print(f"     RECOMMEND PICK despite confidence {item.get('confidence')}/100")
                        elif value_score >= 8:
                            print(f"  ~ {item.get('horse')} - Value: {value_score}/10, Edge: {edge}%")

else:
    print("\n✗✗ NO HORSES FOUND FOR CARLISLE 14:00")
    print("   This race may not be in the database yet")
    print("\n   Searching for any Carlisle races...")
    
    carlisle_all = [item for item in items if item.get('course') == 'Carlisle']
    if carlisle_all:
        carlisle_times = set(item.get('race_time', '') for item in carlisle_all)
        print(f"   Found Carlisle races at: {sorted(carlisle_times)}")
    else:
        print("   No Carlisle races found at all")

# Analyze Fairyhouse 13:50 result
print("\n" + "=" * 100)
print("FAIRYHOUSE 13:50 RESULT ANALYSIS")
print("=" * 100)

print("\nACTUAL RESULT:")
print("  1st: Harwa (FR) - 10/3 (4.33 odds)")
print("  2nd: Springhill Warrior (IRE) - 2/5 (1.40 odds - FAVORITE)")
print("  3rd: Lincoln Du Seuil (FR) - 6/1 (7.0 odds)")

fairyhouse_1350 = [item for item in items if item.get('course') == 'Fairyhouse' and '13:50' in item.get('race_time', '')]

if fairyhouse_1350:
    print(f"\n✓ Found {len(fairyhouse_1350)} horses for Fairyhouse 13:50")
    
    # Find the winner and key horses
    harwa = None
    springhill = None
    lincoln = None
    
    for item in fairyhouse_1350:
        horse = item.get('horse', '')
        if 'Harwa' in horse:
            harwa = item
        elif 'Springhill Warrior' in horse:
            springhill = item
        elif 'Lincoln Du Seuil' in horse:
            lincoln = item
    
    if harwa:
        print("\n1. HARWA (WINNER)")
        print(f"   Our confidence: {float(harwa.get('confidence', 0))}/100")
        print(f"   Our odds: {float(harwa.get('odds', 0))} (actual: 4.33)")
        print(f"   Tags: {harwa.get('tags', [])}")
        
        # Get value analysis
        all_horses = harwa.get('all_horses_analyzed', {})
        if all_horses:
            value_analysis = all_horses.get('value_analysis', [])
            for runner in value_analysis:
                if 'Harwa' in runner.get('runner_name', ''):
                    print(f"   Value score: {runner.get('value_score')}/10")
                    print(f"   Edge: {runner.get('edge_percentage')}%")
                    print(f"   Reasoning: {runner.get('reasoning')}")
        
        if float(harwa.get('confidence', 0)) >= 45:
            print("   [YES] WOULD HAVE BEEN PICKED")
        else:
            print(f"   [NO] Below threshold ({float(harwa.get('confidence', 0))}/100 < 45)")
    else:
        print("\n✗ Harwa not found in database")
    
    if springhill:
        print("\n2. SPRINGHILL WARRIOR (2ND - FAVORITE)")
        print(f"   Our confidence: {float(springhill.get('confidence', 0))}/100")
        print(f"   Our odds: {float(springhill.get('odds', 0))} (actual: 1.40)")
        
        # Check if quality favorite
        odds = float(springhill.get('odds', 0))
        if 1.5 <= odds <= 3.0:
            print(f"   ⚠ Odds {odds} just outside quality favorite range (1.5-3.0)")
        else:
            print(f"   ✗ Odds {odds} not in quality favorite range")
    
    # Show all horses by confidence
    print(f"\n{'Pos':<4} {'Horse':<30} {'Conf':<6} {'Odds':<8} {'Result':<10}")
    print("-" * 100)
    
    for i, item in enumerate(sorted(fairyhouse_1350, key=lambda x: float(x.get('confidence', 0)), reverse=True), 1):
        horse = item.get('horse', '')
        conf = float(item.get('confidence', 0))
        odds = float(item.get('odds', 0))
        
        result = ""
        if 'Harwa' in horse:
            result = "✓ WON"
        elif 'Springhill' in horse:
            result = "2nd"
        elif 'Lincoln' in horse:
            result = "3rd"
        
        print(f"{i:<4} {horse:<30} {conf:3}/100 {odds:6.2f}  {result:<10}")

else:
    print("\n✗ Fairyhouse 13:50 not found in database")

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

print(f"\n✓ Total races analyzed: {len(races)}")
print(f"✓ Total horses: {len(items)}")
print(f"✓ All using eu-west-1 region")

# Count readiness
ready_races = sum(1 for horses in races.values() if any(float(h.get('confidence', 0)) > 0 for h in horses))
print(f"\n[OK] Races with confidence scores: {ready_races}/{len(races)}")

# Check if Carlisle 14:00 is ready
if carlisle_1400 and any(float(h.get('confidence', 0)) > 0 for h in carlisle_1400):
    print("\n[READY] CARLISLE 14:00 IS READY FOR ANALYSIS")
else:
    print("\n[NOT READY] CARLISLE 14:00 - May need to wait for next workflow cycle")

print("\n" + "=" * 100)
