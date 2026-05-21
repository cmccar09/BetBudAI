import boto3
from datetime import datetime

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get today's date
today = datetime.utcnow().strftime('%Y-%m-%d')

print(f"\n{'='*80}")
print(f"TODAY'S PICKS ({today})")
print(f"{'='*80}\n")

# Query for today's picks
response = table.scan(
    FilterExpression='#dt = :date',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':date': today}
)

items = response.get('Items', [])

if not items:
    print(f"No picks found for {today}")
else:
    print(f"Total picks: {len(items)}\n")
    
    for item in items:
        horse_name = item.get('horse', item.get('horse_name', 'Unknown'))
        racecourse = item.get('course', item.get('racecourse', 'Unknown'))
        race_time = item.get('race_time', 'Unknown')
        result = item.get('actual_result', item.get('result', 'PENDING'))
        combined_conf = item.get('combined_confidence', 'N/A')
        bet_type = item.get('bet_type', 'Unknown')
        race_type = item.get('sport', item.get('race_type', 'Unknown'))
        roi = item.get('roi', 'N/A')
        
        if result == 'WON':
            status_icon = "WIN"
        elif result == 'LOST':
            status_icon = "LOST"
        else:
            status_icon = "PENDING"
        
        print(f"{status_icon:10} | {horse_name:25} | {racecourse:20} | {race_type:10} | {bet_type:5} | Conf: {combined_conf}% | ROI: {roi}%")
    
    print(f"\n{'='*80}\n")
