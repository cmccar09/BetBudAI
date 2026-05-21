import boto3
from datetime import datetime, timedelta

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get yesterday's date
yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

print(f"\n{'='*80}")
print(f"YESTERDAY'S TIPS ({yesterday})")
print(f"{'='*80}\n")

# Query for yesterday's picks - filter by date field not SK
response = table.scan(
    FilterExpression='#dt = :date',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':date': yesterday}
)

items = response.get('Items', [])

if not items:
    print(f"No picks found for {yesterday}")
else:
    print(f"Total picks: {len(items)}\n")
    
    wins = 0
    losses = 0
    pending = 0
    
    for item in items:
        horse_name = item.get('horse', item.get('horse_name', 'Unknown'))
        racecourse = item.get('course', item.get('racecourse', 'Unknown'))
        race_time = item.get('race_time', 'Unknown')
        result = item.get('actual_result', item.get('result', 'PENDING'))
        combined_conf = item.get('combined_confidence', 'N/A')
        bet_type = item.get('bet_type', 'Unknown')
        race_type = item.get('sport', item.get('race_type', 'Unknown'))
        
        if result == 'WON':
            wins += 1
            status_icon = "✓ WIN"
        elif result == 'LOST':
            losses += 1
            status_icon = "✗ LOST"
        else:
            pending += 1
            status_icon = "⏳ PENDING"
        
        print(f"{status_icon:12} | {horse_name:25} | {racecourse:20} | {race_time:8} | {race_type:10} | {bet_type:5} | Conf: {combined_conf}%")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Pending: {pending}")
    if wins + losses > 0:
        win_rate = (wins / (wins + losses)) * 100
        print(f"  Win Rate: {win_rate:.1f}%")
    print(f"{'='*80}\n")
