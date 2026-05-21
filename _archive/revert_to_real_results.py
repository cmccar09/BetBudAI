#!/usr/bin/env python3
"""Revert fake wins - horses that didn't actually win but were marked as WON"""
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime('%Y-%m-%d')

response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = response.get('Items', [])

wins = [b for b in items if b.get('outcome') == 'WON']

print("Analyzing wins to find fake ones:")
print("(Real wins: selection_id == race_winner OR actual_result == PLACED)")
print()

real_wins = []
fake_wins = []

for b in wins:
    horse = b.get('horse_name', b.get('horse', 'Unknown'))
    selection_id = str(b.get('selection_id', ''))
    race_winner = str(b.get('race_winner', '')).replace('Selection ', '')
    actual_result = b.get('actual_result', '')
    
    # Real win = selection_id matches winner OR it's an EW place
    is_real_winner = selection_id == race_winner
    is_ew_place = actual_result == 'PLACED'
    
    if is_real_winner or is_ew_place:
        real_wins.append(b)
        reason = "matched winner" if is_real_winner else "EW placed"
        print(f"✓ KEEP: {horse} ({reason})")
    else:
        fake_wins.append(b)
        print(f"✗ REVERT: {horse} (selection {selection_id} lost to {race_winner})")

print(f"\nReal wins to keep: {len(real_wins)}")
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
        print(f"   Stake: £{stake:.2f}, Profit: £{loss_profit:.2f}")
        
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
            print(f"   ✓ Reverted\n")
        except Exception as e:
            print(f"   ✗ Error: {e}\n")

# Show final summary
response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = response.get('Items', [])
settled = len([b for b in items if b.get('status') == 'settled'])
wins_count = len([b for b in items if b.get('outcome') == 'WON'])
losses = len([b for b in items if b.get('outcome') == 'LOST'])

print(f"\n=== FINAL SUMMARY ===")
print(f"Total picks: {len(items)}")
print(f"Settled: {settled}")
print(f"Wins: {wins_count}")
print(f"Losses: {losses}")
print(f"Win rate: {wins_count/settled*100 if settled > 0 else 0:.1f}%")
