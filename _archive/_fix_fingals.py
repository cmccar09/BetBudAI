import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# 1. Hide the retrospective +01:00 record (created 17:01, well after race)
table.update_item(
    Key={'bet_date': '2026-03-31', 'bet_id': "2026-03-31T150000+0100_Newcastle_Fingal's_Hill"},
    UpdateExpression='SET show_in_ui = :f',
    ExpressionAttributeValues={':f': False}
)
print('Hid +01:00 retrospective record')

# 2. Fix the +00:00 record: horse placed 2nd (winner: Smokeringinthedark)
table.update_item(
    Key={'bet_date': '2026-03-31', 'bet_id': "2026-03-31T150000+0000_Newcastle_Fingal's_Hill"},
    UpdateExpression='SET outcome = :o, result_emoji = :e, actual_result = :a, result_analysis = :ra, result_winner_name = :w',
    ExpressionAttributeValues={
        ':o': 'placed',
        ':e': 'PLACED',
        ':a': 'PLACED',
        ':ra': '2nd of 2, winner: Smokeringinthedark',
        ':w': 'Smokeringinthedark',
    }
)
print('Fixed +00:00 record to PLACED')
