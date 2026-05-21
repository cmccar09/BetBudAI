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

# Find Three On Thursday
picks = [p for p in response['Items'] if 'Three On Thursday' in p.get('horse', '')]

print(f"Three On Thursday picks: {len(picks)}")
for p in picks:
    print(f"\nHorse: {p['horse']}")
    print(f"Course: {p.get('course', 'N/A')}")
    print(f"Race Time: {p.get('race_time', 'N/A')}")
    print(f"Score: {p.get('confidence_score', 0)}")
    print(f"Show in UI: {p.get('show_in_ui', False)}")
    print(f"Outcome: {p.get('outcome', 'pending')}")
