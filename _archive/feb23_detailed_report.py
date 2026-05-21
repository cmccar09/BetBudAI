import boto3
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = '2026-02-23'

response = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': yesterday}
)

bets = response.get('Items', [])
won_bets = [b for b in bets if b.get('outcome', '').lower() == 'won']

print("\n=== WINNING BETS WITH FULL DETAILS ===\n")
for bet in won_bets:
    print(f"\nHorse fields available: {list(bet.keys())}")
    print(f"Horse name attempts:")
    print(f"  horse_name: {bet.get('horse_name', 'N/A')}")
    print(f"  horse: {bet.get('horse', 'N/A')}")
    print(f"  selection_name: {bet.get('selection_name', 'N/A')}")
    print(f"  runner_name: {bet.get('runner_name', 'N/A')}")
    print(f"Venue attempts:")
    print(f"  venue: {bet.get('venue', 'N/A')}")
    print(f"  course: {bet.get('course', 'N/A')}")
    print(f"  event: {bet.get('event', 'N/A')}")
    print(f"Odds: {bet.get('odds', 'N/A')}")
    print(f"Confidence: {bet.get('combined_confidence', 'N/A')}")
    break  # Just show first one
