import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get all today's items
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

# Find Unknown items
unknown = [item for item in response['Items'] if not item.get('course') or item.get('course') == 'Unknown']

print('Unknown items analysis:')
print(f'Total: {len(unknown)}\n')

for i, item in enumerate(unknown[:5]):
    bet_id = item.get('bet_id', 'NO_ID')
    print(f'{i+1}. bet_id: {bet_id[:70]}')
    print(f'   learning_type: {item.get("learning_type", "NOT SET")}')
    print(f'   analysis_type: {item.get("analysis_type", "NOT SET")}')
    print(f'   is_learning_pick: {item.get("is_learning_pick", "NOT SET")}')
    print(f'   course: {item.get("course", "NOT SET")}')
    print(f'   horse: {item.get("horse", "NOT SET")}')
    print(f'   race_time: {item.get("race_time", "NOT SET")}')
    print()
