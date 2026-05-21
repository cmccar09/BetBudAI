import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.scan(
    FilterExpression='contains(horse, :h) AND bet_date = :d',
    ExpressionAttributeValues={
        ':h': 'Many A Star',
        ':d': '2026-02-03'
    }
)

items = response['Items']
print(f'\nFound {len(items)} items for Many A Star')

for item in items:
    print(f'\nScore: {item.get("comprehensive_score")}')
    print(f'Grade: {item.get("confidence_grade")}')
    print(f'Odds: {item.get("odds")}')
    print(f'Form: {item.get("form")}')
    print(f'Show UI: {item.get("show_in_ui")}')
    print(f'Race Time: {item.get("race_time")}')
    print(f'Venue: {item.get("venue")}')
