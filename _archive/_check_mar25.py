import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

# Get all items for 2026-03-25
resp = tbl.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-03-25'))
items = resp.get('Items', [])
while resp.get('LastEvaluatedKey'):
    resp = tbl.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-03-25'),
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    items += resp.get('Items', [])

print(f"Total items for 2026-03-25: {len(items)}")

target_horses = {
    'Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted',
    'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan'
}

print("\n--- All horses (sorted by time/course) ---")
for it in sorted(items, key=lambda x: (str(x.get('race_time', x.get('time',''))), str(x.get('course','')))):
    horse = str(it.get('horse', '?'))
    course = str(it.get('course', '?'))
    rtime = str(it.get('race_time', it.get('time', '?')))
    outcome = it.get('outcome', '-')
    pos = it.get('finish_position', it.get('position', '-'))
    odds = it.get('odds', it.get('decimal_odds', '-'))
    marker = ' <-- FAV' if horse in target_horses else ''
    if it.get('show_in_ui') or horse in target_horses:
        print(f"  {rtime[-5:]} | {course:<15} | {horse:<25} | odds={odds} | outcome={outcome} | pos={pos}{marker}")
