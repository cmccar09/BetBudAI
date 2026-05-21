import boto3
db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('SureBetBets')
resp = table.scan(FilterExpression='begins_with(bet_date, :d) AND outcome = :o', ExpressionAttributeValues={':d': '2026-01-10', ':o': 'WON'})
for p in resp['Items']:
    print(f"{p['horse']} @ {p['course']} - WON - P/L: {float(p.get('profit_loss', 0)):+.2f} units")
