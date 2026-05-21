import boto3
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

for date in ['2026-04-10', '2026-04-09']:
    resp = table.query(
        KeyConditionExpression='bet_date = :d',
        FilterExpression='contains(course, :c)',
        ExpressionAttributeValues={':d': date, ':c': 'undalk'}
    )
    for item in resp.get('Items', []):
        print(f"{item.get('race_time','?')} | {item.get('horse','?')} | score={item.get('comprehensive_score','?')} | show_in_ui={item.get('show_in_ui','?')} | outcome={item.get('outcome','?')} | rank={item.get('pick_rank','?')} | ml={item.get('market_leader','?')}")
