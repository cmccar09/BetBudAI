import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response.get('Items', [])
print(f'\nTotal picks for {today}: {len(items)}')

if items:
    now = datetime.utcnow()
    future = []
    past = []
    
    for i in items:
        race_time_str = i.get('race_time', '')
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00')).replace(tzinfo=None)
            if race_time > now:
                future.append(i)
            else:
                past.append(i)
        except:
            print(f"Error parsing time for {i.get('horse')}: {race_time_str}")
    
    # Filter for show_in_ui=True
    ui_picks = [i for i in future if i.get('show_in_ui') == True]
    print(f'\nFuture picks (should show on UI): {len(future)}')
    print(f'UI picks (show_in_ui=True): {len(ui_picks)}')
    
    for item in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
        course = item.get('course', 'Unknown')
        print(f"  ✓ {item.get('horse'):25} @ {course:20} Score: {item.get('comprehensive_score')}/100 show_in_ui={item.get('show_in_ui')} recommended_bet={item.get('recommended_bet')}")
    
    print(f'\nPast picks (filtered out): {len(past)}')
    for item in sorted(past, key=lambda x: x.get('race_time', ''))[:5]:
        print(f"  ✗ {item.get('horse'):25} @ {item.get('course'):20} - {item.get('race_time')}")
else:
    print('No picks found in database for today')
