import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
)

picks = response['Items']
print(f"\nYESTERDAY ({yesterday}): {len(picks)} bets\n")
print("="*100)

for pick in picks:
    horse = pick.get('horse', 'Unknown')
    venue = pick.get('course', 'Unknown')
    outcome = pick.get('outcome', None)
    position = pick.get('actual_position', None)
    market_id = pick.get('market_id', None)
    
    status = "NO OUTCOME" if not outcome else outcome
    
    print(f"{horse:25} @ {venue:20} | Outcome: {status:10} | Position: {str(position):5} | Market: {market_id}")

print("\n" + "="*100)
print(f"\nNeed to fetch results from Betfair for these {len(picks)} races.")
