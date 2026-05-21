import boto3
from datetime import datetime, timedelta

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = '2026-02-23'

print(f"\n{'='*80}")
print(f"Checking yesterday's data ({yesterday}) in DynamoDB")
print(f"{'='*80}\n")

# Query by partition key
response = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': yesterday}
)

items = response.get('Items', [])
print(f"Total items found: {len(items)}\n")

if items:
    # Check first item structure
    print("First item fields:")
    first = items[0]
    for key in sorted(first.keys()):
        value = first[key]
        if isinstance(value, str) and len(str(value)) > 50:
            print(f"  {key}: {str(value)[:50]}...")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n{'='*80}")
    print("STAKE DISTRIBUTION")
    print(f"{'='*80}\n")
    
    # Group by stake to understand the filter
    stake_groups = {}
    for item in items:
        stake = float(item.get('stake', 0))
        stake_key = f"{stake:.1f}"
        if stake_key not in stake_groups:
            stake_groups[stake_key] = []
        stake_groups[stake_key].append(item)
    
    for stake, group_items in sorted(stake_groups.items(), key=lambda x: float(x[0])):
        print(f"Stake £{stake}: {len(group_items)} items")
    
    # Check how many would pass the <= 10 filter
    filtered = [item for item in items if float(item.get('stake', 0)) <= 10]
    print(f"\nItems with stake <= 10: {len(filtered)}")
    print(f"Items with stake > 10: {len(items) - len(filtered)}")
    
    print(f"\n{'='*80}")
    print("OUTCOME DISTRIBUTION (all items)")
    print(f"{'='*80}\n")
    
    outcomes = {}
    for item in items:
        outcome = item.get('outcome', 'None/Missing')
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    
    for outcome, count in sorted(outcomes.items()):
        print(f"  {outcome}: {count}")
    
    print(f"\n{'='*80}")
    print("OUTCOME DISTRIBUTION (stake <= 10 only)")
    print(f"{'='*80}\n")
    
    outcomes_filtered = {}
    for item in filtered:
        outcome = item.get('outcome', 'None/Missing')
        outcomes_filtered[outcome] = outcomes_filtered.get(outcome, 0) + 1
    
    for outcome, count in sorted(outcomes_filtered.items()):
        print(f"  {outcome}: {count}")
    
    # Sample items with outcomes
    print(f"\n{'='*80}")
    print("SAMPLE ITEMS WITH OUTCOMES")
    print(f"{'='*80}\n")
    
    won_items = [i for i in filtered if i.get('outcome') in ['won', 'win', 'WON']]
    lost_items = [i for i in filtered if i.get('outcome') in ['lost', 'loss', 'LOST']]
    
    if won_items:
        print(f"Sample WON item:")
        w = won_items[0]
        print(f"  Horse: {w.get('horse', 'N/A')}")
        print(f"  Venue: {w.get('venue', 'N/A')}")
        print(f"  Course: {w.get('course', 'N/A')}")
        print(f"  Odds: {w.get('odds', 'N/A')}")
        print(f"  Outcome: {w.get('outcome', 'N/A')}")
        print(f"  Stake: {w.get('stake', 'N/A')}")
    
    if lost_items:
        print(f"\nSample LOST item:")
        l = lost_items[0]
        print(f"  Horse: {l.get('horse', 'N/A')}")
        print(f"  Venue: {l.get('venue', 'N/A')}")
        print(f"  Course: {l.get('course', 'N/A')}")
        print(f"  Odds: {l.get('odds', 'N/A')}")
        print(f"  Outcome: {l.get('outcome', 'N/A')}")
        print(f"  Stake: {l.get('stake', 'N/A')}")

else:
    print(f"No items found for {yesterday}")
