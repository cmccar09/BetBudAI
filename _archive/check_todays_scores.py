import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = resp.get('Items', [])

print(f'Today ({today}): {len(items)} horses analyzed\n')

for i in sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
    score = float(i.get('comprehensive_score', 0))
    print(f'{i.get("horse"):30} {score:3.0f}/100  Odds: {i.get("odds"):5}  {i.get("course")}  {i.get("race_time")[11:16]}')
    print(f'  Form: {i.get("form", "N/A")}')
    print(f'  Reasons: {i.get("score_reasons", [])}')
    print()
