import boto3
from datetime import date

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = date.today().isoformat()

all_items = []
last_key = None
while True:
    kwargs = {'KeyConditionExpression': boto3.dynamodb.conditions.Key('bet_date').eq(today)}
    if last_key:
        kwargs['ExclusiveStartKey'] = last_key
    r = table.query(**kwargs)
    all_items += r.get('Items', [])
    last_key = r.get('LastEvaluatedKey')
    if not last_key:
        break

# Look at created_at times
created_times = [it.get('created_at','') for it in all_items if it.get('created_at')]
created_times.sort()
if created_times:
    print('Earliest created_at:', created_times[0])
    print('Latest created_at:  ', created_times[-1])
    print('Total items:', len(all_items))

# Show show_in_ui=True picks created_at
print('\nshow_in_ui=True created_at:')
for it in sorted(all_items, key=lambda x: x.get('race_time','') or ''):
    if it.get('show_in_ui') is True:
        print(f"  {it.get('horse')} | created_at={it.get('created_at','?')} | race={it.get('race_time','?')}")

# Check if races with 13:30, 13:40 times were created before their race time
print('\n13:30 and 13:40 picks — were they created before race time?')
for it in all_items:
    rt = it.get('race_time','')
    if '13:30' in str(rt) or '13:40' in str(rt):
        if it.get('show_in_ui') is True:
            print(f"  {it.get('horse')} | race={rt} | created={it.get('created_at','?')}")
