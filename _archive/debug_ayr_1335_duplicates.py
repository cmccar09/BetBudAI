import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = '2026-02-10'

# Get ALL Ayr 13:35 entries
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

ayr_1335 = [
    item for item in response['Items'] 
    if item.get('course') == 'Ayr' and '13:35' in item.get('race_time', '')
]

print("ALL AYR 13:35 DATABASE ENTRIES")
print("="*80)
print(f"\nTotal entries: {len(ayr_1335)}")

# Group by horse name
from collections import defaultdict
by_horse = defaultdict(list)

for item in ayr_1335:
    horse = item.get('horse', 'Unknown')
    by_horse[horse].append(item)

print("\nEntries by horse:")
for horse, entries in sorted(by_horse.items()):
    print(f"\n{horse}: {len(entries)} entries")
    for i, entry in enumerate(entries, 1):
        score = float(entry.get('comprehensive_score', 0))
        bet_id = entry.get('bet_id', '')
        outcome = entry.get('outcome', 'pending')
        form = entry.get('form', '')[:20]
        
        print(f"  {i}. bet_id: {bet_id[:50]}")
        print(f"     Score: {score}/100, Outcome: {outcome}")
        print(f"     Form: {form}")
        print(f"     Has component_scores: {bool(entry.get('component_scores'))}")
        print(f"     Created_at: {entry.get('created_at', 'N/A')[:19]}")
