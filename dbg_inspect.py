import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
import json

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')
now_minus_30 = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S')

response = table.query(IndexName='bet_date-index', KeyConditionExpression=Key('bet_date').eq(today))
items = response.get('Items', [])

fields = ['bet_id', 'bet_date', 'horse', 'course', 'race_time', 'outcome', 'market_id', 'selection_id', 'result_recorded_at', 'sp_odds', 'finish_position', 'winner_horse', 'is_dropped', 'show_in_ui', 'created_at', 'updated_at']

def fmt(i): return {f: str(i.get(f)) for f in fields}

print('--- DAMYSUS TODAY ---')
for i in [x for x in items if 'Damysus' in str(x.get('horse'))]: print(json.dumps(fmt(i), indent=2))

print('\n--- PENDING & DELAYED ---')
for i in [x for x in items if x.get('outcome') == 'pending' and x.get('race_time', 'Z') < now_minus_30]: print(json.dumps(fmt(i), indent=2))
