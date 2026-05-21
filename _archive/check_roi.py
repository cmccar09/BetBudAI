import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='us-east-1').Table('SureBetBets')
response = table.scan(
    FilterExpression='#d = :today',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':today': datetime.utcnow().strftime('%Y-%m-%d')}
)

print("\nRecent picks with ROI (sorted by timestamp):")
print("-" * 70)
items = sorted(response['Items'], key=lambda x: x.get('timestamp', ''), reverse=True)
for item in items[:10]:
    print(f"{item['horse']:20} | {item['bet_type']:3} | ROI: {item.get('roi', 0):6.1f}% | p_win: {item.get('p_win', 0):.3f} | odds: {item.get('odds', 0):.2f}")
