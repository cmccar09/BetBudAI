"""Test parallel DynamoDB query speed locally"""
import boto3, time
from boto3.dynamodb.conditions import Key
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

CUMULATIVE_ROI_START = '2026-03-22'
start_d = date.fromisoformat(CUMULATIVE_ROI_START)
today_d = date.today()
dates = [(start_d + timedelta(days=i)).isoformat() for i in range((today_d - start_d).days + 1)]
print(f"Querying {len(dates)} dates: {dates}")

def _query_date(d):
    items = []
    kwargs = {'KeyConditionExpression': Key('bet_date').eq(d)}
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get('Items', []))
        if 'LastEvaluatedKey' not in resp:
            break
        kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']
    return d, len(items)

t0 = time.time()
with ThreadPoolExecutor(max_workers=10) as ex:
    for d, count in ex.map(lambda d: _query_date(d), dates):
        print(f"  {d}: {count} items")
print(f"Total time: {round(time.time()-t0, 2)}s")
