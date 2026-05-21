import boto3
from decimal import Decimal

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Query today's picks
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-10'}
)

# Find Lingfield 16:xx picks
picks = [p for p in response['Items'] if 'Lingfield' in p.get('course', '') and p.get('race_time', '').startswith('16:')]

print(f"Lingfield 16:xx picks: {len(picks)}")
for p in picks:
    print(f"{p['horse']} - {p.get('race_time')} - Score: {p.get('confidence_score', 0)} - UI: {p.get('show_in_ui', False)}")
