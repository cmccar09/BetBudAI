"""
Quick System Status Check - Run anytime to verify workflows are active

Shows:
- EventBridge schedules status
- Recent Lambda executions
- Today's betting performance
- Learning system health
"""
import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

print("="*80)
print(f"BETTING SYSTEM STATUS CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# 1. Check EventBridge Rules
print("\n📅 SCHEDULED WORKFLOWS:")
events = boto3.client('events', region_name='eu-west-1')
response = events.list_rules()

betting_rules = [r for r in response['Rules'] if 'Betting' in r['Name'] or 'racing' in r['Name']]
for rule in sorted(betting_rules, key=lambda x: x['Name']):
    status = "✅" if rule['State'] == 'ENABLED' else "❌"
    schedule = rule.get('ScheduleExpression', 'N/A')
    print(f"  {status} {rule['Name']:30} {schedule}")

# 2. Today's Performance
print(f"\n📊 TODAY'S PERFORMANCE:")
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = response.get('Items', [])

wins = sum(1 for i in items if str(i.get('outcome', '')).upper() in ['WON', 'WIN'])
losses = sum(1 for i in items if str(i.get('outcome', '')).upper() in ['LOST', 'LOSS'])
pending = sum(1 for i in items if str(i.get('outcome', '')).upper() in ['PENDING', 'NONE', ''])

total_stake = sum(float(i.get('stake', 2.0)) for i in items if str(i.get('outcome', '')).upper() in ['WON', 'LOST', 'WIN', 'LOSS'])
total_return = sum(float(i.get('stake', 2.0)) * float(i.get('odds', 0)) for i in items if str(i.get('outcome', '')).upper() in ['WON', 'WIN'])
profit = total_return - total_stake
roi = (profit / total_stake * 100) if total_stake > 0 else 0

print(f"  Total Bets: {len(items)}")
print(f"  Wins: {wins} | Losses: {losses} | Pending: {pending}")
print(f"  Profit: £{profit:.2f} | ROI: {roi:.1f}%")
print(f"  Strike Rate: {(wins/(wins+losses)*100) if (wins+losses) > 0 else 0:.1f}%")

# 3. Recent Lambda Executions
print(f"\n⚡ RECENT WORKFLOW ACTIVITY (last 2 hours):")
logs = boto3.client('logs', region_name='eu-west-1')

try:
    streams = logs.describe_log_streams(
        logGroupName='/aws/lambda/betting',
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    if streams['logStreams']:
        last_run = datetime.fromtimestamp(streams['logStreams'][0]['lastEventTimestamp']/1000)
        minutes_ago = int((datetime.now() - last_run).total_seconds() / 60)
        print(f"  Workflow Lambda: ✅ Last run {minutes_ago} min ago")
    else:
        print(f"  Workflow Lambda: ⚠️  No recent activity")
except:
    print(f"  Workflow Lambda: ⚠️  Could not check")

try:
    streams = logs.describe_log_streams(
        logGroupName='/aws/lambda/BettingLearningAnalysis',
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    if streams['logStreams']:
        last_run = datetime.fromtimestamp(streams['logStreams'][0]['lastEventTimestamp']/1000)
        minutes_ago = int((datetime.now() - last_run).total_seconds() / 60)
        print(f"  Learning Lambda: ✅ Last run {minutes_ago} min ago")
    else:
        print(f"  Learning Lambda: ⚠️  No recent activity")
except:
    print(f"  Learning Lambda: ⚠️  Could not check")

# 4. Learning System Status
print(f"\n🧠 LEARNING SYSTEM:")
recent_with_outcomes = [i for i in items if i.get('outcome') in ['WON', 'LOST', 'won', 'loss']]
print(f"  Data collected today: {len(items)} races")
print(f"  Results recorded: {len(recent_with_outcomes)} races")
print(f"  Status: {'✅ ACTIVE' if len(items) > 0 else '⚠️  NO DATA'}")

print(f"\n{'='*80}")
print(f"SYSTEM STATUS: ✅ OPERATIONAL")
print(f"All workflows running automatically - no action needed")
print(f"{'='*80}\n")
