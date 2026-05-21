import boto3
from datetime import date, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (date.today() - timedelta(days=1)).isoformat()
print(f'Yesterday: {yesterday}')

# Search for these horses in yesterday's data
all_items = []
last_key = None
while True:
    kwargs = {'KeyConditionExpression': boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)}
    if last_key:
        kwargs['ExclusiveStartKey'] = last_key
    r = table.query(**kwargs)
    all_items += r.get('Items', [])
    last_key = r.get('LastEvaluatedKey')
    if not last_key:
        break

targets = ['cargin bhui', 'say what you see']
for it in all_items:
    if any(t in (it.get('horse','') or '').lower() for t in targets):
        print(f"\nHorse: {it.get('horse')}")
        print(f"  bet_id: {it.get('bet_id')}")
        print(f"  bet_date: {it.get('bet_date')}")
        print(f"  course: {it.get('course')}")
        print(f"  race_time: {it.get('race_time')}")
        print(f"  show_in_ui: {it.get('show_in_ui')}")
        print(f"  outcome: {it.get('outcome')}")
        print(f"  stake: {it.get('stake')}")
        print(f"  profit_loss: {it.get('profit_loss')}")
