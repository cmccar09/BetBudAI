import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-10'))
items = [it for it in resp.get('Items', []) if it.get('bet_id') != 'WORKFLOW_RUN_LOCK']

print(f"\n{'Time':<10} {'Course':<15} {'Horse':<28} {'Score':>6}  {'Odds':>6}  {'UI':>4}  Outcome")
print("-" * 90)
for it in sorted(items, key=lambda x: x.get('race_time', '')):
    print(f"{str(it.get('race_time','?')):<10} {str(it.get('course','?')):<15} "
          f"{str(it.get('horse_name','?')):<28} {str(it.get('comprehensive_score','?')):>6}  "
          f"{str(it.get('odds','?')):>6}  {str(it.get('show_in_ui','?')):>4}  "
          f"{str(it.get('outcome','pending'))}")
print(f"\nTotal: {len(items)} picks")
