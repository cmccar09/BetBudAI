import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

# Get all picks for today
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']

print(f"\n╔═══════════════════════════════════════════════╗")
print(f"║  PICKS HISTORY - {datetime.now().strftime('%H:%M:%S')}               ║")
print(f"╚═══════════════════════════════════════════════╝\n")

if items:
    print(f"Total picks for {today}: {len(items)}")
    print(f"\nAll picks (sorted by timestamp):\n")
    
    # Sort by timestamp
    items_sorted = sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    for item in items_sorted:
        timestamp = item.get('timestamp', 'Unknown')
        created_time = timestamp.split('T')[1][:8] if 'T' in timestamp else 'Unknown'
        race_time = item.get('race_time', 'Unknown')
        race_time_short = race_time.split('T')[1][:5] if 'T' in race_time else race_time
        
        print(f"  {item['horse']:<20} @ {item['course']:<12}")
        print(f"    Race time: {race_time_short}")
        print(f"    Created: {created_time}")
        print(f"    Timestamp: {timestamp}")
        print()
else:
    print(f"⚠ NO PICKS found in DynamoDB for {today}")
    print(f"\nChecking if workflow has run today...")
    
# Check workflow log
import os
import glob

log_pattern = f"logs/run_{today.replace('-', '')}*.log"
log_files = glob.glob(log_pattern)

if log_files:
    latest_log = max(log_files, key=os.path.getmtime)
    print(f"\nLatest workflow log: {os.path.basename(latest_log)}")
    
    # Check if it completed
    with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        last_lines = lines[-10:] if len(lines) > 10 else lines
        
        for line in last_lines:
            if 'saved to DynamoDB' in line or 'Final pick count' in line or 'timed out' in line:
                print(f"  Status line: {line.strip()}")
else:
    print(f"\n⚠ No workflow logs found for today")
