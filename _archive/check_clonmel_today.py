import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-02-26'))
items = resp['Items']
clonmel = [i for i in items if 'clonmel' in i.get('course', '').lower()]
clonmel.sort(key=lambda x: str(x.get('race_time', '')))
print(f"Total today: {len(items)}, Clonmel: {len(clonmel)}")
for h in clonmel:
    print(f"  {h.get('race_time','')} | {h.get('horse_name','')} | score={h.get('comprehensive_score','')} | ui={h.get('show_in_ui','')} | outcome={h.get('outcome','')}")
