"""Check Team Player and Saladins Son records, then fix both."""
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

resp  = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-04'))
items = [x for x in resp.get('Items', []) if x.get('show_in_ui')]

for item in items:
    horse = item.get('horse', '')
    if 'Team Player' in horse or 'Saladins' in horse:
        print(f"\n--- {horse} ---")
        for k in ['bet_id', 'odds', 'stake', 'result', 'outcome', 'profit_loss', 'bet_type', 'course']:
            print(f"  {k}: {item.get(k)}")
