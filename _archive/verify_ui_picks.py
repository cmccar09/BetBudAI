#!/usr/bin/env python3
"""
Verify today's picks in DynamoDB match the UI
"""

import boto3
from datetime import datetime

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SureBetBets')

# Scan for today's picks (can't query without both keys)
today = datetime.utcnow().strftime('%Y-%m-%d')
response = table.scan(
    FilterExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

picks = response['Items']

print("=" * 70)
print(f"DynamoDB Picks for {today}")
print("=" * 70)
print(f"\nTotal picks: {len(picks)}\n")

# Filter Dundalk picks
dundalk_picks = [p for p in picks if p.get('course') == 'Dundalk']
print(f"Dundalk picks: {len(dundalk_picks)}\n")

# Check for the 3 specific horses shown in UI
ui_horses = ['Blanc De Blanc', 'Beat The Devil', 'Diamond Exchange']

print("Checking UI horses in database:")
for horse_name in ui_horses:
    found = [p for p in dundalk_picks if p.get('horse') == horse_name]
    if found:
        pick = found[0]
        print(f"  ✅ {pick['horse']} @ {pick['course']}")
        print(f"     Bet Type: {pick.get('bet_type')}")
        print(f"     ROI: {pick.get('roi', 0):.1f}%")
        print(f"     Confidence: {pick.get('confidence', 0)}")
        print(f"     Odds: {pick.get('odds', 0)}")
        print(f"     Race Time: {pick.get('race_time')}")
        print()
    else:
        print(f"  ❌ {horse_name} - NOT FOUND")
        print()

print("=" * 70)
print("\nAll Dundalk picks in database:")
for p in dundalk_picks:
    print(f"  - {p['horse']} @ {p['course']} - {p['bet_type']} (ROI: {p.get('roi', 0):.1f}%)")

print("=" * 70)
