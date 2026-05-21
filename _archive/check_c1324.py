import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-02-26'))
items = resp['Items']

c1324 = [i for i in items if 'clonmel' in i.get('course','').lower() and '13:24' in str(i.get('race_time',''))]
c1324.sort(key=lambda x: float(x.get('comprehensive_score', 0) or 0), reverse=True)
print(f"Clonmel 13:24 - {len(c1324)} horses")
for h in c1324:
    print(f"  {h.get('horse','')} | score={h.get('comprehensive_score','')} | ui={h.get('show_in_ui','')} | outcome={h.get('outcome','')} | odds={h.get('odds','')} | bet_id={h.get('bet_id','')}")
