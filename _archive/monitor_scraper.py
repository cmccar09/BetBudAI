import boto3
import time

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

print("\n=== MONITORING SCRAPER PROGRESS ===\n")

for i in range(5):
    resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-06'))
    items = resp.get('Items', [])
    
    # Count outcomes
    outcomes = {}
    for item in items:
        outcome = item.get('outcome', 'UNKNOWN')
        if outcome is None:
            outcome = 'None'
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    
    print(f"Check #{i+1}:")
    for status, count in sorted(outcomes.items(), key=lambda x: (x[0] is None, x[0])):
        print(f"  {status:20} - {count} horses")
    
    results = len([i for i in items if i.get('outcome') not in ['UNKNOWN', None, 'Pending']])
    print(f"  Results recorded: {results}/{len(items)}")
    print()
    
    if i < 4:
        print("Waiting 30 seconds...")
        time.sleep(30)
