"""Check show_in_ui flags"""
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

picks = [i for i in response['Items'] if not i.get('analysis_type') and not i.get('learning_type')]

print("\nAll picks with show_in_ui flag status:\n")
for p in sorted(picks, key=lambda x: x.get('race_time', '')):
    show_flag = p.get('show_in_ui', 'NOT SET')
    print(f"  {p.get('horse')}: show_in_ui={show_flag}")
