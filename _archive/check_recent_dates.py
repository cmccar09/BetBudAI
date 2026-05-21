import boto3
from collections import Counter
db = boto3.resource('dynamodb', region_name='eu-west-1')
t = db.Table('SureBetBets')

# Check last few days
dates = ['2026-02-08', '2026-02-07', '2026-02-06']

for date in dates:
    r = t.query(KeyConditionExpression='bet_date = :d', ExpressionAttributeValues={':d': date})
    count = r['Count']
    print(f'{date}: {count} picks')
    
    if count > 0 and count < 50:
        for item in r['Items']:
            print(f'  - {item.get("horse")} @ {item.get("course")}')
