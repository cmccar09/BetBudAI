import boto3
import json
from datetime import datetime
from collections import defaultdict

# Check Betfair data
print("="*80)
print("BETFAIR DATA (All Races & Horses Today)")
print("="*80)

with open('response_horses.json', 'r') as f:
    betfair_data = json.load(f)

races = betfair_data.get('races', [])
total_races = len(races)
total_horses = sum(len(race['runners']) for race in races)

print(f"\nTotal Races: {total_races}")
print(f"Total Horses: {total_horses}")
print(f"\nRaces by Venue:")

by_venue = defaultdict(list)
for race in races:
    by_venue[race['course']].append({
        'time': race['start_time'],
        'name': race['market_name'],
        'runners': len(race['runners'])
    })

for venue, races in sorted(by_venue.items()):
    print(f"\n{venue}: {len(races)} races, {sum(r['runners'] for r in races)} horses")
    for r in races[:3]:  # Show first 3
        print(f"  - {r['time'][:5]} {r['name'][:40]} ({r['runners']} runners)")
    if len(races) > 3:
        print(f"  ... and {len(races)-3} more races")

# Check DynamoDB picks
print("\n" + "="*80)
print("DATABASE PICKS (Analyzed & Scored)")
print("="*80)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

picks = response.get('Items', [])
print(f"\nTotal Picks Stored: {len(picks)}")

picks_by_course = defaultdict(list)
for pick in picks:
    picks_by_course[pick['course']].append({
        'horse': pick['horse'],
        'score': float(pick.get('comprehensive_score', 0)),
        'race_time': pick['race_time']
    })

print(f"\nPicks by Venue:")
for venue, horses in sorted(picks_by_course.items()):
    print(f"\n{venue}: {len(horses)} picks")
    for h in sorted(horses, key=lambda x: x['score'], reverse=True):
        print(f"  - {h['horse'][:30]:30} {h['score']:.0f}/100")

# Gap Analysis
print("\n" + "="*80)
print("LEARNING READINESS")
print("="*80)

print(f"\n📊 Coverage Statistics:")
print(f"  Races Available: {total_races}")
print(f"  Horses Available: {total_horses}")
print(f"  Picks Made: {len(picks)}")
print(f"  Coverage Rate: {len(picks)/total_horses*100:.1f}% of all horses analyzed")

print(f"\n⚠️  Learning Limitation:")
print(f"  - Only {len(picks)} horses stored in SureBetBets table")
print(f"  - {total_horses - len(picks)} horses NOT in database")
print(f"  - Cannot learn from non-picked horses (false negatives)")
print(f"  - Can only track performance of our picks (true/false positives)")

print(f"\n✓ What We CAN Learn:")
print(f"  - Which of our {len(picks)} picks won/lost")
print(f"  - Accuracy of our scoring system")
print(f"  - Which factors correlate with wins")

print(f"\n✗ What We CANNOT Learn:")
print(f"  - Which non-picked horses won (missed winners)")
print(f"  - Why we rejected {total_horses - len(picks)} horses")
print(f"  - Whether our filters are too strict")

print(f"\n💡 Recommendation:")
print(f"  Store ALL analyzed horses (scored + rejected) to enable:")
print(f"  1. Missed winner analysis")
print(f"  2. Filter calibration")
print(f"  3. Comprehensive learning feedback")
