#!/usr/bin/env python3
"""Check Jan 18 data"""
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(KeyConditionExpression=Key('bet_date').eq('2026-01-18'))
items = response.get('Items', [])

settled = [b for b in items if b.get('outcome') in ['WON', 'LOST']]
total_stake = sum(float(b.get('stake', 0)) for b in settled)
total_profit = sum(float(b.get('profit', 0)) for b in settled)

print(f'Jan 18 Data:')
print(f'  Total Stake: £{total_stake:.2f}')
print(f'  Total Profit: £{total_profit:.2f}')
print(f'  ROI: {(total_profit/total_stake*100) if total_stake > 0 else 0:.2f}%')
print(f'  Settled: {len(settled)} / {len(items)} total')
print()
print('Settled bets:')
for b in settled:
    horse = b.get('horse_name', b.get('horse', 'Unknown'))
    stake = float(b.get('stake', 0))
    profit = float(b.get('profit', 0))
    outcome = b.get('outcome', 'PENDING')
    print(f"  {outcome:4s} | {horse:20s} | Stake: £{stake:6.2f} | Profit: £{profit:7.2f}")
