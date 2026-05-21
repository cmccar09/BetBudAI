import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get today's date
today = datetime.now().strftime('%Y-%m-%d')

# Query for actual picks (not analysis, just bets)
response = table.scan(
    FilterExpression='bet_date = :date AND is_learning_pick = :learning',
    ExpressionAttributeValues={
        ':date': today,
        ':learning': True
    }
)

picks = response['Items']

print("\n" + "="*100)
print(f"TODAY'S VALUE PICKS - {today}")
print("="*100)

if not picks:
    print("\nNo value picks identified yet today.")
    print("\nThe system is analyzing all races but only picks horses that meet strict criteria:")
    print("  • Positive edge (value vs market)")
    print("  • Odds in sweet spot or near it")
    print("  • Recent winning form")
    print("  • Score 40+ points across all factors")
    print("\nContinue monitoring - picks will appear here when criteria are met.")
else:
    print(f"\n{len(picks)} VALUE BET(S) IDENTIFIED:\n")
    
    # Group by race
    by_race = {}
    for pick in picks:
        race_key = f"{pick.get('venue')} {pick.get('race_time')}"
        if race_key not in by_race:
            by_race[race_key] = []
        by_race[race_key].append(pick)
    
    # Display each race
    for race_key in sorted(by_race.keys()):
        race_picks = by_race[race_key]
        print(f"📍 {race_key}")
        print("-" * 100)
        
        for pick in race_picks:
            horse = pick.get('horse', 'Unknown')
            odds = pick.get('odds', 'N/A')
            confidence = pick.get('confidence', 'N/A')
            bet_type = pick.get('bet_type', 'N/A')
            edge = pick.get('edge_percentage', 0)
            form = pick.get('form', 'N/A')
            status = pick.get('status', 'PENDING')
            
            print(f"  🐴 {horse}")
            print(f"     Odds: {odds} | Edge: {edge}% | Confidence: {confidence}")
            print(f"     Bet Type: {bet_type} | Status: {status}")
            print(f"     Form: {form}")
            print()
        
        print()

print("="*100)

# Also show CSV file status
import os
csv_file = 'today_picks.csv'
if os.path.exists(csv_file):
    print(f"\n✓ Picks also saved to: {csv_file}")
    print(f"  Open this file to see picks in spreadsheet format")
else:
    print(f"\n(No CSV file yet - will be created when first pick is identified)")

print("\n" + "="*100)
print("Background: Continuous learning system analyzing ALL races for pattern detection")
print("Display: Only showing VALUE PICKS that meet betting criteria")
print("="*100 + "\n")
