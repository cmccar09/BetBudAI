import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Hide The Dark Baron (19:00 race - already finished)
today = datetime.now().strftime('%Y-%m-%d')
race_time = "2026-02-02T19:00:00.000Z"

print(f"Hiding The Dark Baron (19:00 - race finished)...")
table.update_item(
    Key={
        'bet_date': today,
        'race_time': race_time
    },
    UpdateExpression='SET show_in_ui = :false',
    ExpressionAttributeValues={
        ':false': False
    }
)
print("✓ Updated - old race now hidden from UI")
