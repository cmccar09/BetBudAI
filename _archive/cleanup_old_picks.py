# WARNING: THIS SCRIPT DELETES HISTORICAL DATA - DO NOT RUN!
# Historical data is needed for AI learning and performance analysis.
# The UI already filters past races using race_time in the API.
# This script is DISABLED to preserve learning history.

import sys
print("\n" + "="*80)
print("ERROR: This cleanup script is DISABLED")
print("="*80)
print("Historical betting data must be preserved for AI learning.")
print("The UI automatically hides past races using race_time filtering.")
print("If you need to clean up, contact the developer.")
print("="*80 + "\n")
sys.exit(1)

import boto3
from datetime import datetime, timezone

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Get all picks from today
response = table.scan(
    FilterExpression='#dt = :today OR bet_date = :today',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':today': '2026-01-20'}
)

picks = response.get('Items', [])
now = datetime.now(timezone.utc)

print(f'\n=== Removing old/past picks from UI ===\n')

deleted_count = 0
for pick in picks:
    race_time_str = pick.get('race_time', '')
    horse = pick.get('horse', 'Unknown')
    course = pick.get('course', 'Unknown')
    
    if race_time_str:
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            if race_time < now:
                print(f'DELETING (past): {race_time_str} - {horse} @ {course}')
                table.delete_item(
                    Key={
                        'bet_date': pick['bet_date'],
                        'bet_id': pick['bet_id']
                    }
                )
                deleted_count += 1
            else:
                print(f'KEEPING (future): {race_time_str} - {horse} @ {course}')
        except Exception as e:
            print(f'Error parsing time for {horse}: {e}')

print(f'\n✅ Deleted {deleted_count} old picks')
print('UI now showing only upcoming races')
