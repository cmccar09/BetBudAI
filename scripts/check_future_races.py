"""
Check races at 17:45 and 18:20 that are incorrectly marked as LOST
"""

import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*70)
print("CHECKING FUTURE RACES MARKED AS LOST")
print(f"Current Time: 17:37 (user reported)")
print("="*70 + "\n")

# Query today's picks
today = '2026-05-20'
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
print(f"Total picks today: {len(items)}")

# Find races at 17:45 and 18:20
target_times = ['17:45', '18:20']
problem_races = []

for item in items:
    race_time = item.get('race_time', '')
    if any(t in race_time for t in target_times):
        result = item.get('actual_result', 'PENDING')

        race_info = {
            'race_time': race_time,
            'course': item.get('course', 'Unknown'),
            'horse': item.get('horse', 'Unknown'),
            'bet_id': item.get('bet_id', 'Unknown'),
            'actual_result': result,
            'settled_date': item.get('settled_date', 'Not settled'),
            'odds': item.get('odds', 0),
            'score': item.get('comprehensive_score', 0)
        }

        print(f"\n{'='*70}")
        print(f"Race: {race_info['race_time']} - {race_info['course']}")
        print(f"Horse: {race_info['horse']}")
        print(f"Current Result: {race_info['actual_result']}")
        print(f"Settled Date: {race_info['settled_date']}")
        print(f"Odds: {race_info['odds']}")
        print(f"Score: {race_info['score']}")
        print(f"Bet ID: {race_info['bet_id']}")

        # Check if marked as LOST before race time
        if result == 'LOSS':
            print(f"\n[ERROR] This race is marked as LOST but hasn't run yet!")
            print(f"  Race time: {race_time}")
            print(f"  Current time: 17:37")
            print(f"  Time until race: {race_time} is in the future")
            problem_races.append(race_info)

print(f"\n{'='*70}")
print(f"SUMMARY")
print("="*70)
print(f"Races found at target times: {len([i for i in items if any(t in i.get('race_time', '') for t in target_times)])}")
print(f"Problem races (marked LOST before running): {len(problem_races)}")

if problem_races:
    print(f"\n[ACTION REQUIRED] Fix these races:")
    for race in problem_races:
        print(f"\n  Race: {race['race_time']} {race['course']}")
        print(f"  Horse: {race['horse']}")
        print(f"  Bet ID: {race['bet_id']}")
        print(f"  Current (wrong) result: {race['actual_result']}")
        print(f"  Should be: PENDING")

        print(f"\n  Fix command:")
        print(f"  aws dynamodb update-item \\")
        print(f"    --table-name SureBetBets \\")
        print(f"    --key '{{\"bet_date\":{{\"S\":\"2026-05-20\"}},\"bet_id\":{{\"S\":\"{race['bet_id']}\"}}}}' \\")
        print(f"    --update-expression \"REMOVE actual_result, settled_date\" \\")
        print(f"    --region eu-west-1")
else:
    print("\n[OK] No problem races found - all future races are correctly marked as PENDING")

print("\n" + "="*70 + "\n")
