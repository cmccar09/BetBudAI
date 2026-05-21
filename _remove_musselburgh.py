import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

picks_to_remove = [
    {'bet_date': '2026-04-12', 'bet_id': '2026-04-12T164500+0000_Musselburgh_Say_What_You_See'},
    {'bet_date': '2026-04-12', 'bet_id': '2026-04-12T171500+0000_Musselburgh_Cargin_Bhui'},
]

for key in picks_to_remove:
    table.update_item(
        Key=key,
        UpdateExpression='SET show_in_ui = :f, removed_reason = :r',
        ExpressionAttributeValues={':f': False, ':r': 'Manually removed by admin - April 13 2026'}
    )
    bid = key['bet_id']
    print(f'Removed: {bid}')

print('Done.')
