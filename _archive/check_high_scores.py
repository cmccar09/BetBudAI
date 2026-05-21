"""Check why scores are so high"""
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='show_in_ui = :ui',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':ui': True
    }
)

print("UI PICKS WITH HIGH SCORES:\n")
for item in sorted(response['Items'], key=lambda x: -(x.get('comprehensive_score') or x.get('combined_confidence', 0))):
    horse = item.get('horse', 'Unknown')
    score = item.get('comprehensive_score') or item.get('combined_confidence', 0)
    odds = item.get('odds', 0)
    form = item.get('form', '')[:20]
    
    print(f"{horse:25} {score:3}/100  Odds: {odds:5}  Form: {form}")
