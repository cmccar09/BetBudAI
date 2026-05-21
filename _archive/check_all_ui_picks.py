import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

ui_picks = [i for i in response['Items'] if i.get('show_in_ui') == True]

print(f'Total UI picks: {len(ui_picks)}\n')
print('All picks with scores:\n')

for pick in sorted(ui_picks, key=lambda x: float(x.get('confidence', 0)), reverse=True):
    horse = pick.get('horse', 'Unknown')
    score = pick.get('confidence', 0)
    source = pick.get('source', 'unknown')
    print(f'{horse:30} Score: {score:5}  Source: {source}')
