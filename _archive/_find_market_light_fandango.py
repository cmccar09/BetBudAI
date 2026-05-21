import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-03-20'),
    FilterExpression=Attr('course').eq('Musselburgh')
)
items = resp.get('Items', [])
print(f'Musselburgh items today: {len(items)}')

by_market = {}
for it in sorted(items, key=lambda x: str(x.get('race_time', ''))):
    rt = str(it.get('race_time', ''))[:16]
    mid = str(it.get('market_id', '') or '')
    sid = str(it.get('selection_id', '') or '')
    horse = it.get('horse', '?')
    ui = it.get('show_in_ui')
    print(f"  {horse:30} rt={rt} mid={mid} sid={sid} ui={ui}")
    if mid:
        by_market[mid] = by_market.get(mid, [])
        by_market[mid].append(horse)

print("\nMarkets found:", list(by_market.keys()))
