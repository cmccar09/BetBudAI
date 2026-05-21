import boto3
from datetime import datetime

# Delete the duplicate Doncaster bets (keep only the best one - Deep Cave with higher p_win)
table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

# Delete Josh The Boss (lower p_win)
bet_id_to_delete = f"{today}T14:05:00.000Z_Doncaster_Josh The Boss"

try:
    response = table.delete_item(
        Key={
            'bet_date': today,
            'bet_id': bet_id_to_delete
        }
    )
    print(f"✓ Deleted duplicate: Josh The Boss")
except Exception as e:
    print(f"Error deleting: {e}")

# Verify
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
doncaster = [i for i in items if 'Doncaster' in i.get('course', '') and '14:05' in i.get('race_time', '')]

print(f"\nRemaining Doncaster 14:05 bets: {len(doncaster)}")
for i in doncaster:
    print(f"  - {i['horse']} ({i.get('bet_type', '?')}) - p_win: {i.get('p_win', 0)}")
