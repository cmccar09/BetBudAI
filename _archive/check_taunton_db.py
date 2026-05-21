import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.scan(
    FilterExpression='#dt = :date',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':date': '2026-02-03'}
)

items = response['Items']
tracks = set(item.get('track') for item in items)

print(f'Total items for 2026-02-03: {len(items)}')
print(f'Tracks: {sorted(tracks)}')

# Check for Taunton specifically
taunton_items = [i for i in items if i.get('track') == 'Taunton']
print(f'\nTaunton items: {len(taunton_items)}')

if taunton_items:
    race_times = set(i.get('race_time') for i in taunton_items)
    print(f'Taunton race times: {sorted(race_times)}')
    
    # Check for 13:40 specifically
    taunton_1340 = [i for i in taunton_items if i.get('race_time') == '13:40']
    print(f'\nTaunton 13:40 horses: {len(taunton_1340)}')
    
    if taunton_1340:
        for horse in sorted(taunton_1340, key=lambda x: x.get('confidence_score', 0), reverse=True):
            print(f"  {horse.get('horse_name'):30s} Score: {horse.get('confidence_score', 0):3}/100  Odds: {float(horse.get('odds', 0)):5.1f}")
