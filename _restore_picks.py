"""Restore incorrectly demoted picks for today."""
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

demoted = [
    "2026-04-15T123000+0000_Haydock_Le_Beau_Madrik",
    "2026-04-15T155200+0000_Leopardstown_Vega's_Muse",
    "2026-04-15T152500+0000_Haydock_Smokeringinthedark",
    "2026-04-15T160000+0000_Haydock_Grand_Geste",
]

for bid in demoted:
    table.update_item(
        Key={'bet_date': '2026-04-15', 'bet_id': bid},
        UpdateExpression='SET show_in_ui = :t, is_learning_pick = :f, pick_type = :pt',
        ExpressionAttributeValues={':t': True, ':f': False, ':pt': 'intraday'},
    )
    short = bid.rsplit('_', 2)[-2] + ' ' + bid.rsplit('_', 1)[-1]
    print(f'  Restored: {short}')

print('Done - all picks restored')
