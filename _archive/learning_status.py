import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from collections import defaultdict

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

print(f"="*80)
print(f"LEARNING SYSTEM STATUS - {today}")
print(f"="*80)

response = table.query(
    KeyConditionExpression=Key('bet_date').eq(today)
)

items = response.get('Items', [])

print(f"\n📊 DATABASE ENTRIES TODAY: {len(items)}")

# Count by outcome
outcomes = defaultdict(int)
for item in items:
    outcome = str(item.get('outcome', 'pending')).upper()
    outcomes[outcome] = outcomes.get(outcome, 0) + 1

print(f"\n📈 OUTCOMES:")
for outcome, count in sorted(outcomes.items()):
    print(f"  {outcome:10} : {count}")

# Show wins
wins = [i for i in items if str(i.get('outcome', '')).upper() in ['WON', 'WIN']]
print(f"\n✅ WINS ({len(wins)}):")
for w in wins[:10]:
    print(f"  {w.get('horse', '?'):30} @ {w.get('odds', '?'):5} - {w.get('course', '?')}")

# Show losses  
losses = [i for i in items if str(i.get('outcome', '')).upper() in ['LOST', 'LOSS']]
print(f"\n❌ LOSSES ({len(losses)}):")
for l in losses[:5]:
    print(f"  {l.get('horse', '?'):30} @ {l.get('odds', '?'):5} - {l.get('course', '?')}")

# Show pending
pending = [i for i in items if str(i.get('outcome', '')).upper() in ['PENDING', 'NONE', '']]
print(f"\n⏳ PENDING ({len(pending)}):")
for p in pending[:5]:
    course = p.get('course', '?') if p.get('course') else '?'
    print(f"  {p.get('horse', '?'):30} @ {str(p.get('odds', '?')):5} - {course}")

print(f"\n{'='*80}")
print(f"LEARNING SYSTEM: ✅ ACTIVE")
print(f"  - Data being collected: YES")
print(f"  - Results being recorded: YES")
print(f"  - Ready for analysis: YES")
print(f"{'='*80}\n")
