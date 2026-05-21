"""
Mark unverifiable yesterday UI picks as void
"""
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
)

items = response.get('Items', [])
ui_picks = [i for i in items if i.get('show_in_ui') == True]
pending = [i for i in ui_picks if not i.get('outcome') or i.get('outcome') == 'pending']

print(f'Marking {len(pending)} unverifiable picks as void for {yesterday}')
print('=' * 80)

updated = 0
for pick in pending:
    horse = pick.get('horse', '')
    course = pick.get('course', '')
    
    try:
        table.update_item(
            Key={
                'bet_date': yesterday,
                'bet_id': pick['bet_id']
            },
            UpdateExpression='SET outcome = :outcome, updated_at = :ts, #note = :note',
            ExpressionAttributeNames={
                '#note': 'note'
            },
            ExpressionAttributeValues={
                ':outcome': 'void',
                ':ts': datetime.now().isoformat(),
                ':note': 'Results unavailable - void race'
            }
        )
        print(f'✓ {horse} @ {course} - marked as VOID')
        updated += 1
    except Exception as e:
        print(f'✗ {horse} @ {course} - Error: {e}')

print('=' * 80)
print(f'Updated {updated}/{len(pending)} picks')
