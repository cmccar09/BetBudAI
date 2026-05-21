import boto3
db = boto3.resource('dynamodb', region_name='eu-west-1')
t = db.Table('SureBetBets')
r = t.scan(FilterExpression='bet_date = :d', ExpressionAttributeValues={':d': '2026-02-08'})
print(f'Total for 2026-02-08: {r["Count"]}')
for i in r.get('Items', [])[:10]:
    print(f'  {i.get("horse")} @ {i.get("course")}')
