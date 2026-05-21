import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from collections import defaultdict

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

print("="*80)
print(f"TODAY'S RESULTS SUMMARY - {today}")
print("="*80)

# Get all today's entries
response = table.query(
    KeyConditionExpression=Key('bet_date').eq(today)
)

items = response.get('Items', [])

print(f"\nTotal picks today: {len(items)}")

# Group by outcome
by_outcome = defaultdict(list)
for item in items:
    outcome = str(item.get('outcome', 'pending')).upper()
    if outcome in ['', 'NONE']:
        outcome = 'PENDING'
    by_outcome[outcome].append(item)

# Calculate stats
wins = by_outcome.get('WON', []) + by_outcome.get('WIN', [])
losses = by_outcome.get('LOST', []) + by_outcome.get('LOSS', [])
pending = by_outcome.get('PENDING', [])

total_resolved = len(wins) + len(losses)
strike_rate = (len(wins) / total_resolved * 100) if total_resolved > 0 else 0

# Calculate profit
total_profit = 0
for item in wins + losses:
    profit = item.get('profit')
    if profit is not None:
        total_profit += float(profit)

print(f"\nWINS: {len(wins)}")
print(f"LOSSES: {len(losses)}")
print(f"PENDING: {len(pending)}")
print(f"\nStrike Rate: {strike_rate:.1f}%")
print(f"Total Profit: GBP {total_profit:.2f}")

print(f"\n{'='*80}")
print(f"WINS ({len(wins)}):")
print(f"{'='*80}")
for item in sorted(wins, key=lambda x: x.get('race_time', '')):
    horse = item.get('horse', '?')
    course = item.get('course', '?')
    odds = item.get('odds', 0)
    score = item.get('comprehensive_score', 0)
    profit = item.get('profit', 0)
    race_time = item.get('race_time', '')[:16] if item.get('race_time') else '?'
    
    score_val = float(score) if score else 0
    profit_val = float(profit) if profit else 0
    
    print(f"  {race_time:16} {course:15} {horse:25} @{float(odds):5.1f} Score:{score_val:3.0f} Profit:GBP{profit_val:6.2f}")

print(f"\n{'='*80}")
print(f"LOSSES ({len(losses)}):")
print(f"{'='*80}")
for item in sorted(losses, key=lambda x: x.get('race_time', ''))[:10]:
    horse = item.get('horse', '?')
    course = item.get('course', '?')
    odds = item.get('odds', 0)
    score = item.get('comprehensive_score', 0)
    race_time = item.get('race_time', '')[:16] if item.get('race_time') else '?'
    notes = item.get('race_notes', '')
    
    score_val = float(score) if score else 0
    note_str = f" ({notes})" if notes else ""
    
    print(f"  {race_time:16} {course:15} {horse:25} @{float(odds):5.1f} Score:{score_val:3.0f}{note_str}")

print(f"\n{'='*80}")
print(f"PENDING ({len(pending)}) - Next races to finish:")
print(f"{'='*80}")
for item in sorted(pending, key=lambda x: x.get('race_time', ''))[:10]:
    horse = item.get('horse', '?')
    course = item.get('course', '?')
    odds = item.get('odds', 0)
    score = item.get('comprehensive_score', 0)
    race_time = item.get('race_time', '')[:16] if item.get('race_time') else '?'
    
    score_val = float(score) if score else 0
    
    print(f"  {race_time:16} {course:15} {horse:25} @{float(odds):5.1f} Score:{score_val:3.0f}")

print(f"\n{'='*80}\n")
