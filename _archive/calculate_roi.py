#!/usr/bin/env python3
"""Calculate ROI for today's bets"""
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(KeyConditionExpression=Key('bet_date').eq('2026-01-19'))
items = response.get('Items', [])

# Only count settled bets
settled = [b for b in items if b.get('outcome') in ['WON', 'LOST']]

total_stake = 0
total_profit = 0

print("=== TODAY'S SETTLED BETS ===\n")

for b in settled:
    horse = b.get('horse_name', b.get('horse', 'Unknown'))
    stake = float(b.get('stake', 0))
    profit = float(b.get('profit', 0))
    outcome = b.get('outcome', 'PENDING')
    
    total_stake += stake
    total_profit += profit
    
    print(f"{outcome:4s} | {horse:20s} | Stake: £{stake:6.2f} | Profit: £{profit:7.2f}")

print(f"\n{'='*70}")
print(f"TOTAL STAKE:  £{total_stake:.2f}")
print(f"TOTAL PROFIT: £{total_profit:.2f}")
print(f"TOTAL RETURN: £{total_stake + total_profit:.2f}")

if total_stake > 0:
    roi = (total_profit / total_stake) * 100
    print(f"ROI:          {roi:.2f}%")
else:
    print("ROI:          N/A (no stake)")

print(f"\nSettled: {len(settled)}")
print(f"Wins: {len([b for b in settled if b.get('outcome') == 'WON'])}")
print(f"Losses: {len([b for b in settled if b.get('outcome') == 'LOST'])}")
print(f"Win Rate: {len([b for b in settled if b.get('outcome') == 'WON'])/len(settled)*100:.1f}%")
