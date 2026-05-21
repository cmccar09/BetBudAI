import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-20'),
    FilterExpression='show_in_ui = :ui',
    ExpressionAttributeValues={':ui': True}
)

picks = sorted(resp['Items'], key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)

print(f'\nTotal picks today: {len(picks)}\n')

sure = [p for p in picks if float(p.get('comprehensive_score', 0)) >= 85]
high = [p for p in picks if 75 <= float(p.get('comprehensive_score', 0)) < 85]
good = [p for p in picks if 70 <= float(p.get('comprehensive_score', 0)) < 75]

print(f'SURE BETS (85+): {len(sure)}')
for p in sure:
    print(f'  - {p.get("horse")} @ {p.get("course")} ({float(p.get("comprehensive_score", 0)):.0f}/100)')

print(f'\nHIGH CONFIDENCE (75-84): {len(high)}')
for p in high:
    print(f'  - {p.get("horse")} @ {p.get("course")} ({float(p.get("comprehensive_score", 0)):.0f}/100)')

print(f'\nGOOD (70-74): {len(good)}')
for p in good[:5]:
    print(f'  - {p.get("horse")} @ {p.get("course")} ({float(p.get("comprehensive_score", 0)):.0f}/100)')
if len(good) > 5:
    print(f'  ... and {len(good) - 5} more')
