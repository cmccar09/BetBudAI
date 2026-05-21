import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': '2026-01-18'}
)

items = response['Items']
print(f"Total bets: {len(items)}\n")

for item in items:
    horse = item.get('horse_name', item.get('horse', 'Unknown'))
    venue = item.get('course', 'Unknown')
    market_id = item.get('market_id', '')
    sport = item.get('sport_type', 'unknown')
    
    print(f"{horse} @ {venue} ({sport}): market_id = {'YES - ' + market_id if market_id else 'NO'}")
