#!/usr/bin/env python3
import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='us-east-1').Table('SureBetBets')
today = '2026-01-10'

response = table.scan(
    FilterExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

picks = response['Items']
print(f"\nPicks in DynamoDB for {today}: {len(picks)}\n")

if picks:
    for p in picks:
        print(f"  - {p['horse']} @ {p['course']}")
        print(f"    Race Time: {p.get('race_time', 'No time')}")
        print(f"    Bet Type: {p.get('bet_type', 'Unknown')}")
        print(f"    Odds: {p.get('odds', 0)}")
        print()
else:
    print("❌ NO PICKS FOR TODAY IN DATABASE")
    print("\nYou need to run: .\\generate_todays_picks.ps1")
