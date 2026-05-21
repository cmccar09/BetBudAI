#!/usr/bin/env python3
"""Check pending bets for today"""
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime('%Y-%m-%d')
response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = response.get('Items', [])

pending = [b for b in items if b.get('status') != 'settled']
print(f"Pending bets today: {len(pending)}")
print()
for b in pending:
    print(f"{b.get('horse_name')} @ {b.get('racecourse')} - {b.get('race_time')}")
    print(f"  Market ID: {b.get('market_id', 'NO MARKET')}")
    print(f"  Status: {b.get('status', 'unknown')}")
    print()
