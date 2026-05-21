#!/usr/bin/env python3
"""
Display all UI picks properly, showing recommended bets prominently
"""

import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

# Get all picks for today
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response.get('Items', [])

# Filter UI picks
ui_picks = [i for i in items if i.get('show_in_ui')]
recommended = [i for i in items if i.get('recommended_bet')]

print("="*80)
print(f"TODAY'S BETTING PICKS - {today}")
print("="*80)
print(f"\nTotal horses analyzed: {len(items)}")
print(f"UI picks (70+): {len(ui_picks)}")
print(f"Recommended bets (85+): {len(recommended)}")

print("\n" + "="*80)
print("★ RECOMMENDED BETS (Score 85+)")
print("="*80)

for i, pick in enumerate(sorted(recommended, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True), 1):
    score = float(pick.get('comprehensive_score', 0))
    horse = pick.get('horse', 'Unknown')
    course = pick.get('course', 'Unknown')
    race_time = pick.get('race_time', '')
    odds = pick.get('odds', 'N/A')
    form = pick.get('form', 'N/A')
    trainer = pick.get('trainer', 'N/A')
    
    # Extract time
    time_str = race_time[11:16] if len(race_time) > 16 else 'N/A'
    
    # Tier
    if score >= 110:
        tier = "⭐⭐⭐ EXCEPTIONAL"
    elif score >= 95:
        tier = "⭐⭐ STRONG"
    else:
        tier = "⭐ SOLID"
    
    print(f"\n{i}. {horse} @ {course}")
    print(f"   Time: {time_str}  Score: {score:.0f}/100  {tier}")
    print(f"   Odds: {odds}  Trainer: {trainer}")
    print(f"   Form: {form}")

print("\n" + "="*80)
print("OTHER UI PICKS (Score 70-84)")
print("="*80)

other_ui = [i for i in ui_picks if not i.get('recommended_bet')]
for i, pick in enumerate(sorted(other_ui, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True), 1):
    score = float(pick.get('comprehensive_score', 0))
    horse = pick.get('horse', 'Unknown')
    course = pick.get('course', 'Unknown')
    race_time = pick.get('race_time', '')
    
    time_str = race_time[11:16] if len(race_time) > 16 else 'N/A'
    
    print(f"{i:2}. {time_str} {horse:25} {score:3.0f}/100 @ {course}")

print("\n" + "="*80)
print("RACES WITH PICKS (Chronological)")
print("="*80)

# Group by race time
races = {}
for pick in ui_picks:
    race_key = pick.get('race_time', 'Unknown')
    if race_key not in races:
        races[race_key] = []
    races[race_key].append(pick)

for race_time in sorted(races.keys()):
    race_picks = races[race_time]
    course = race_picks[0].get('course', 'Unknown')
    time_str = race_time[11:16] if len(race_time) > 16 else race_time
    
    print(f"\n{time_str} - {course} ({len(race_picks)} pick{'s' if len(race_picks) > 1 else ''})")
    
    for pick in sorted(race_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
        horse = pick.get('horse', 'Unknown')
        score = float(pick.get('comprehensive_score', 0))
        is_rec = '★' if pick.get('recommended_bet') else ' '
        
        print(f"  {is_rec} {horse:25} {score:3.0f}/100")

print("\n" + "="*80)
