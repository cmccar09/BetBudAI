"""Quick check of race_time fields for target horses"""
import boto3
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

resp = tbl.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-03-25'))
items = resp.get('Items', [])

targets = ['Falls Of Acharn', 'Shadowfax Of Rohan', 'Peckforton Hills', 'Hillberry Hill', 'Montevetro']

for item in items:
    horse = str(item.get('horse',''))
    if horse in targets:
        race_time = item.get('race_time', item.get('race_date', item.get('time', '?')))
        race_date = item.get('race_date', '?')
        course = item.get('course','?')
        all_keys = [k for k in item.keys() if 'time' in k.lower() or 'date' in k.lower()]
        print(f"{horse}: course={course}")
        for k in all_keys:
            print(f"  {k} = {item.get(k)}")
        print()
