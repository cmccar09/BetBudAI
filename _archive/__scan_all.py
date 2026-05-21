import boto3, json
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Get all items and look at what race_times we have
resp = table.scan()
items = resp['Items']
while resp.get('LastEvaluatedKey'):
    resp = table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

print(f'Total records in DynamoDB: {len(items)}')
print()

# Group by race_time
from collections import defaultdict
by_race = defaultdict(list)
for i in items:
    rt = i.get('race_time', 'NO_RACE_TIME')
    by_race[rt].append(i)

print('Race times and horse counts:')
for rt in sorted(by_race.keys()):
    horses = by_race[rt]
    ui_picks = [h for h in horses if h.get('show_in_ui')]
    print(f'  {rt}  total={len(horses):3}  ui_picks={len(ui_picks)}')

print()
# Show all losses
losses = [i for i in items if i.get('outcome') == 'loss' and i.get('show_in_ui')]
print(f'UI losses: {len(losses)}')
for L in sorted(losses, key=lambda x: str(x.get('race_time',''))):
    rt = L.get('race_time','?')[:16]
    horse = L.get('horse','?')
    winner = L.get('result_winner_name','?')
    # check if winner is in our data
    race_items = by_race.get(L.get('race_time',''), [])
    winner_rec = next((h for h in race_items if (h.get('horse') or '').lower() == (winner or '').lower()), None)
    has_winner = 'OK' if winner_rec else 'MISSING'
    print(f'  {rt}  Our pick: {horse:28}  Winner: {winner:28}  Winner in DB: {has_winner}')
