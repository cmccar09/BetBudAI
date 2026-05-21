"""Check why Harbour Vision and No Return aren't showing in results"""
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='horse IN (:h1, :h2)',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':h1': 'Harbour Vision',
        ':h2': 'No Return'
    }
)

for item in response['Items']:
    print(f"\nHorse: {item.get('horse')}")
    print(f"  outcome: {item.get('outcome')}")
    print(f"  show_in_ui: {item.get('show_in_ui')}")
    print(f"  comprehensive_score: {item.get('comprehensive_score')}")
    print(f"  combined_confidence: {item.get('combined_confidence')}")
    print(f"  race_time: {item.get('race_time')}")
    print(f"  course: {item.get('course')}")
