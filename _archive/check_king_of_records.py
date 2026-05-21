import boto3

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Query for King Of Records
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-09')
)

# Find King Of Records
for item in response['Items']:
    if item.get('horse') == 'King Of Records':
        print(f"King Of Records found:")
        print(f"  Score: {item.get('comprehensive_score')}")
        print(f"  Show in UI: {item.get('show_in_ui')}")
        print(f"  Course: {item.get('course')}")
        print(f"  Race time: {item.get('race_time')}")
        print(f"  Finish position: {item.get('finish_position', 'Not set')}")
        print(f"  Outcome: {item.get('outcome', 'Not set')}")
        break
