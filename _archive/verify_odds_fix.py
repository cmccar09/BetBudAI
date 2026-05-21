import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-20'),
    FilterExpression='show_in_ui = :ui AND horse = :h',
    ExpressionAttributeValues={
        ':ui': True,
        ':h': 'River Run Free'
    }
)

if resp['Items']:
    item = resp['Items'][0]
    print('\nRiver Run Free:')
    print(f'  odds: {item.get("odds")}')
    print(f'  decimal_odds: {item.get("decimal_odds")}')
    print(f'  p_win: {item.get("p_win")}')
    print(f'  p_place: {item.get("p_place")}')
    print(f'  comprehensive_score: {item.get("comprehensive_score")}')
else:
    print('River Run Free not found with show_in_ui=True')
