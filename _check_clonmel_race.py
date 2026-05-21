import boto3
from boto3.dynamodb.conditions import Key

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'))
items = [dict(it) for it in resp['Items']]
clonmel_1537 = [it for it in items if 'clonmel' in str(it.get('course', '')).lower() and '15:37' in str(it.get('race_time', ''))]
print(f'Clonmel 15:37 runners: {len(clonmel_1537)}')
for it in sorted(clonmel_1537, key=lambda x: float(x.get('odds', 99))):
    print(f"  {it.get('horse', '?'):25s} odds={str(it.get('odds', '?')):>6s} fav_outcome={str(it.get('fav_outcome', 'N/A')):>6s} score={it.get('score', '?')} rwn={it.get('race_winner_name', '')}")
