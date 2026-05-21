import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime("%Y-%m-%d")
response = table.scan(
    FilterExpression='#d = :date',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
print(f"\nToday's picks ({today}):")
print("=" * 80)
for item in sorted(items, key=lambda x: x['timestamp'], reverse=True):
    print(f"\n{item['horse']}")
    print(f"  ROI: {item.get('roi', 'N/A')}%")
    print(f"  Odds: {item.get('odds', 'N/A')}")
    print(f"  Type: {item.get('bet_type', 'N/A')}")
    print(f"  Combined Confidence: {item.get('combined_confidence', 'N/A')}")
    print(f"  Win Prob: {item.get('p_win', 'N/A')}")
