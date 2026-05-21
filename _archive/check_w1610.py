import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-02-26'))
items = resp['Items']

w1610 = [i for i in items if 'wetherby' in i.get('course','').lower() and '16:10' in str(i.get('race_time',''))]
w1610.sort(key=lambda x: float(x.get('comprehensive_score', 0) or 0), reverse=True)
print(f"Wetherby 16:10 - {len(w1610)} horses")
for h in w1610:
    bd = h.get('score_breakdown', {})
    components = [(k, int(v or 0)) for k, v in bd.items() if int(v or 0) > 0]
    components.sort(key=lambda x: x[1], reverse=True)
    comp_str = ', '.join(f"{k}={v}" for k,v in components)
    print(f"  [{h.get('horse','')}] score={h.get('comprehensive_score','')} odds={h.get('odds','')} ui={h.get('show_in_ui','')} | {comp_str}")
