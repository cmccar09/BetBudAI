#!/usr/bin/env python3
"""Revert the 5 wins that were artificially set, keeping only EW place wins"""
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime('%Y-%m-%d')

# Get today's bets
response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = response.get('Items', [])

# Find wins that have actual_result = 'WIN' (real wins)
# vs those that have actual_result = 'PLACED' (EW places we want to keep)
wins = [b for b in items if b.get('outcome') == 'WON']

print(f"Current wins: {len(wins)}")
print("\nAnalyzing wins:")

real_wins = []
ew_place_wins = []
fake_wins = []

for bet in wins:
    actual_result = bet.get('actual_result', '')
    bet_type = bet.get('bet_type', 'WIN')
    horse_name = bet.get('horse_name', bet.get('horse', 'Unknown'))
    
    if actual_result == 'PLACED' and bet_type.upper() == 'EW':
        ew_place_wins.append(bet)
        print(f"  ✓ EW Place: {horse_name} (KEEP)")
    elif actual_result == 'WIN':
        real_wins.append(bet)
        print(f"  ✓ Real Win: {horse_name} (KEEP)")
    else:
        fake_wins.append(bet)
        print(f"  ✗ Fake Win: {horse_name} (REVERT TO LOSS)")

print(f"\nReal wins: {len(real_wins)}")
print(f"EW place wins: {len(ew_place_wins)}")
print(f"Fake wins to revert: {len(fake_wins)}")

if len(fake_wins) > 0:
    print(f"\nReverting {len(fake_wins)} fake wins back to losses:\n")
    
    for bet in fake_wins:
        horse_name = bet.get('horse_name', bet.get('horse', 'Unknown'))
        racecourse = bet.get('racecourse', bet.get('course', 'Unknown'))
        stake = float(bet.get('stake', 0))
        
        # Loss profit = -stake
        loss_profit = -stake
        
        print(f"❌ {horse_name} @ {racecourse}")
        print(f"   Stake: £{stake:.2f}")
        print(f"   Reverting to LOST, Profit: £{loss_profit:.2f}")
        
        try:
            table.update_item(
                Key={
                    'bet_date': bet['bet_date'],
                    'bet_id': bet['bet_id']
                },
                UpdateExpression='SET outcome = :outcome, actual_result = :result, profit = :profit',
                ExpressionAttributeValues={
                    ':outcome': 'LOST',
                    ':result': 'LOSS',
                    ':profit': Decimal(str(loss_profit))
                }
            )
            print(f"   ✓ Reverted successfully\n")
        except Exception as e:
            print(f"   ✗ Error: {e}\n")

# Show final summary
response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = response.get('Items', [])
settled = len([b for b in items if b.get('status') == 'settled'])
wins = len([b for b in items if b.get('outcome') == 'WON'])
losses = len([b for b in items if b.get('outcome') == 'LOST'])

print(f"\n=== FINAL SUMMARY ===")
print(f"Total picks: {len(items)}")
print(f"Settled: {settled}")
print(f"Wins: {wins} (Real: {len(real_wins)}, EW Places: {len(ew_place_wins)})")
print(f"Losses: {losses}")
print(f"Win rate: {wins/settled*100 if settled > 0 else 0:.1f}%")
