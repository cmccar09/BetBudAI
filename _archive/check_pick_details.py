import boto3
db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('SureBetBets')
resp = table.scan(FilterExpression='begins_with(bet_date, :d)', ExpressionAttributeValues={':d': '2026-01-10'})
for p in resp['Items'][:5]:
    print(f"{p['horse']} - market: {p.get('market_id')}, selection: {p.get('selection_id')}, outcome: {p.get('outcome')}")
