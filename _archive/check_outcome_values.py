import boto3
from datetime import datetime, timedelta

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
print(f"\n🔍 Checking outcomes for {yesterday}...\n")

resp = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': yesterday}
)

items = resp.get('Items', [])
print(f"Total picks: {len(items)}\n")

# Count outcomes
outcomes = {}
for item in items:
    outcome = item.get('outcome', 'None')
    outcomes[outcome] = outcomes.get(outcome, 0) + 1

print("Outcome values in DB:")
for k, v in outcomes.items():
    print(f"  '{k}': {v}")

print("\nSample items:")
for i, item in enumerate(items[:5], 1):
    print(f"  {i}. {item.get('horse_name', 'Unknown')}: outcome='{item.get('outcome')}' | P/L: {item.get('profit_loss', 0)}")
