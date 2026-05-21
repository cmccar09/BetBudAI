import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Scan for recent items (get more)
response = table.scan(Limit=500)
items = response['Items']

print(f"Total items scanned: {len(items)}")

# Check outcomes
with_outcomes = [i for i in items if i.get('outcome') in ['WON', 'LOST', 'PLACED', 'won', 'loss', 'WIN', 'LOSS']]
print(f"Items with outcomes: {len(with_outcomes)}")

# Show all bet_date formats
bet_dates = set([i.get('bet_date', 'MISSING') for i in items])
print(f"\nAll bet_date values found: {sorted(bet_dates)}")

# Show today's items
today_items = [i for i in items if i.get('bet_date') == '2026-02-14']
print(f"\nToday's items (2026-02-14): {len(today_items)}")

for item in today_items[:10]:
    print(f"  {item.get('horse', '?'):25} outcome={item.get('outcome', 'None'):10} show_in_ui={item.get('show_in_ui', '?')}")

# Show items with outcomes
print(f"\nAll items with outcomes:")
for item in [i for i in items if i.get('outcome')][:10]:
    print(f"  {item.get('horse', '?'):25} date={item.get('bet_date', '?'):12} outcome={item.get('outcome', '?')}")

# Check learning Lambda criteria
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=7)
print(f"\nLearning Lambda looks for:")
print(f"  - timestamp > {cutoff.isoformat()}")
print(f"  - outcome field exists")

recent_with_outcome = [i for i in items if i.get('outcome') and i.get('timestamp')]
print(f"\nItems matching criteria: {len(recent_with_outcome)}")
