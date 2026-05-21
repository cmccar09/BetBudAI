from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime('%Y-%m-%d')
response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = [i for i in response['Items'] if i.get('sport') == 'horses']

print(f'\n📅 TODAY ({today}): {len(items)} picks found')

if items:
    print('\n✅ System is running - picks generated:')
    for i in sorted(items, key=lambda x: x.get('race_time', '')):
        race_time = i.get('race_time', '')
        horse = i.get('horse', 'Unknown')
        course = i.get('course', 'Unknown')
        bet_type = i.get('bet_type', 'WIN')
        stake = i.get('stake', 0)
        confidence = i.get('combined_confidence', i.get('confidence', 0))
        print(f'  {race_time[:16] if race_time else "?"} - {horse} @ {course} - {bet_type} €{float(stake):.2f} ({confidence}% conf)')
else:
    print('\n❌ No picks for today yet')
    print('\nChecking if workflow is scheduled to run...')
    # Could check CloudWatch Events here
