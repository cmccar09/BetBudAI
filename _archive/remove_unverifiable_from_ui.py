"""
Remove unverifiable yesterday UI picks from display
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

print(f'Removing {len(pending)} unverifiable picks from UI for {yesterday}')
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
            UpdateExpression='SET show_in_ui = :ui, updated_at = :ts',
            ExpressionAttributeValues={
                ':ui': False,
                ':ts': datetime.now().isoformat()
            }
        )
        print(f'✓ {horse} @ {course} - removed from UI')
        updated += 1
    except Exception as e:
        print(f'✗ {horse} @ {course} - Error: {e}')

print('=' * 80)
print(f'Updated {updated}/{len(pending)} picks')
print(f'\nResults page will now show only verified picks')
