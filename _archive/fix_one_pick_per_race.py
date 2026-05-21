#!/usr/bin/env python3
"""
Ensure only the BEST pick per race is shown on UI
If multiple picks exist for the same race, keep only the highest-scoring one
"""

import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

bet_date = datetime.now().strftime('%Y-%m-%d')
print(f"Processing date: {bet_date}")

# Get all items for today
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(bet_date)
)

items = response.get('Items', [])

print("="*80)
print("FIXING UI PICKS - ONE BEST PICK PER RACE")
print("="*80)

# Group by race (course + time)
races = {}
for item in items:
    race_key = f"{item.get('race_time')}_{item.get('course')}"
    if race_key not in races:
        races[race_key] = []
    races[race_key].append(item)

print(f"\nTotal horses: {len(items)}")
print(f"Total races: {len(races)}\n")

# For each race, find the best pick and ensure only it shows on UI
updated_count = 0
races_with_multiple = 0

for race_key, race_horses in races.items():
    if len(race_horses) > 1:
        # Sort by score
        sorted_horses = sorted(race_horses, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)
        
        best_horse = sorted_horses[0]
        others = sorted_horses[1:]
        
        course = best_horse.get('course', 'Unknown')
        time = best_horse.get('race_time', '')[:16]
        
        print(f"\n{time} {course} - {len(race_horses)} horses:")
        races_with_multiple += 1
        
        # Ensure best horse is on UI
        if not best_horse.get('show_in_ui'):
            print(f"  + ENABLING:  {best_horse.get('horse'):25} {float(best_horse.get('comprehensive_score', 0)):3.0f}/100")
            table.update_item(
                Key={'bet_date': bet_date, 'bet_id': best_horse['bet_id']},
                UpdateExpression='SET show_in_ui = :true',
                ExpressionAttributeValues={':true': True}
            )
            updated_count += 1
        else:
            print(f"  + KEEP:      {best_horse.get('horse'):25} {float(best_horse.get('comprehensive_score', 0)):3.0f}/100")
        
        # Hide all others
        for horse in others:
            if horse.get('show_in_ui'):
                print(f"  - HIDING:    {horse.get('horse'):25} {float(horse.get('comprehensive_score', 0)):3.0f}/100")
                table.update_item(
                    Key={'bet_date': bet_date, 'bet_id': horse['bet_id']},
                    UpdateExpression='SET show_in_ui = :false, recommended_bet = :false',
                    ExpressionAttributeValues={':false': False}
                )
                updated_count += 1

print(f"\n{'='*80}")
print(f"Races with multiple picks: {races_with_multiple}")
print(f"Updates made: {updated_count}")
print(f"{'='*80}\n")

# Verify - show final UI picks
print("FINAL UI PICKS (one per race):\n")

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(bet_date)
)

items = response.get('Items', [])
ui_picks = [i for i in items if i.get('show_in_ui')]

# Group by race again to verify
races_check = {}
for pick in ui_picks:
    race_key = f"{pick.get('race_time')}_{pick.get('course')}"
    if race_key not in races_check:
        races_check[race_key] = []
    races_check[race_key].append(pick)

errors = []
for race_key, picks in sorted(races_check.items()):
    if len(picks) > 1:
        errors.append(f"ERROR: {race_key} still has {len(picks)} picks!")

if errors:
    print("ERRORS FOUND:")
    for err in errors:
        print(f"  {err}")
else:
    print("+ All races have exactly 1 pick\n")

print(f"Total UI picks: {len(ui_picks)}\n")

for i, pick in enumerate(sorted(ui_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:15], 1):
    horse = pick.get('horse')
    score = float(pick.get('comprehensive_score', 0))
    course = pick.get('course')
    time = pick.get('race_time', '')[:16]
    rec = '*' if pick.get('recommended_bet') else ' '
    
    print(f"{i:2}. {rec} {horse:25} {score:3.0f}/100 @ {course:15} {time}")

print(f"\n{'='*80}\n")
