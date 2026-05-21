import boto3
from datetime import datetime, timedelta
from collections import Counter

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
print(f'Investigating picks for {yesterday}')
print('=' * 80)

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
)

items = response.get('Items', [])

# Group by outcome
outcome_counts = Counter()
for item in items:
    outcome = item.get('outcome')
    if outcome:
        outcome_counts[outcome] += 1
    else:
        outcome_counts['None'] += 1

print(f'Total picks: {len(items)}')
print(f'\nOutcome breakdown:')
for outcome, count in outcome_counts.most_common():
    print(f'  {outcome:20}: {count}')

# Check if picks have market_id
with_market = sum(1 for i in items if i.get('market_id'))
without_market = len(items) - with_market

print(f'\nMarket ID coverage:')
print(f'  With market_id:    {with_market}')
print(f'  Without market_id: {without_market}')

# Sample some picks without results
no_result = [i for i in items if not i.get('outcome')]
if no_result:
    print(f'\nSample picks without outcome (showing first 5):')
    for pick in no_result[:5]:
        horse = pick.get('horse', 'Unknown')
        course = pick.get('course', 'Unknown')
        time = pick.get('race_time', 'Unknown')
        market = pick.get('market_id', 'None')
        print(f'  {horse:30} @ {course:20} {time} MarketID: {market}')
