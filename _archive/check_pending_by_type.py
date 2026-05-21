import boto3
from datetime import datetime, timedelta

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

print("Checking pending bets by race type...\n")

total = 0
for i in range(5):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    response = table.query(
        KeyConditionExpression='bet_date = :d',
        ExpressionAttributeValues={':d': date}
    )
    
    items = [x for x in response.get('Items', []) if not x.get('actual_result')]
    dogs = sum(1 for x in items if x.get('race_type') == 'greyhound')
    horses = sum(1 for x in items if x.get('race_type') == 'horse')
    
    total += len(items)
    print(f"{date}: {len(items)} pending ({dogs} dogs, {horses} horses)")

print(f"\nTotal pending: {total}")
