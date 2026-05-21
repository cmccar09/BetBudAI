import boto3

table = boto3.resource('dynamodb', region_name='us-east-1').Table('SureBetBets')
response = table.scan(
    FilterExpression='horse = :horse',
    ExpressionAttributeValues={':horse': 'Magna'}
)

print("\nMagna picks:")
for item in sorted(response['Items'], key=lambda x: x.get('timestamp', ''), reverse=True)[:2]:
    print(f"\nTimestamp: {item.get('timestamp')}")
    print(f"Odds: {item.get('odds')}")
    print(f"p_win: {item.get('p_win')}")
    print(f"p_place: {item.get('p_place')}")
    print(f"ew_fraction: {item.get('ew_fraction')}")
    print(f"ROI: {item.get('roi')}%")
