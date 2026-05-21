#!/usr/bin/env python3
"""Check which wins should be reverted"""
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(KeyConditionExpression=Key('bet_date').eq('2026-01-19'))
items = response.get('Items', [])

wins = [b for b in items if b.get('outcome') == 'WON']
losses = [b for b in items if b.get('outcome') == 'LOST']

print("=== WINS ===")
for b in wins:
    horse = b.get('horse_name', b.get('horse', 'Unknown'))
    actual = b.get('actual_result', 'None')
    race_time = b.get('race_time', '')[:16]
    bet_type = b.get('bet_type', 'WIN')
    race_winner = b.get('race_winner', 'Unknown')
    selection_id = b.get('selection_id', 'Unknown')
    
    print(f"\n{horse} ({bet_type}) @ {race_time}")
    print(f"  outcome: WON, actual_result: {actual}")
    print(f"  race_winner: {race_winner}")
    print(f"  selection_id: {selection_id}")

print("\n\n=== LOSSES ===")
for b in losses[:3]:
    horse = b.get('horse_name', b.get('horse', 'Unknown'))
    actual = b.get('actual_result', 'None')
    race_time = b.get('race_time', '')[:16]
    
    print(f"{horse} @ {race_time}: outcome=LOST, actual_result={actual}")
